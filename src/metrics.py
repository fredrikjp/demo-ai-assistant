"""Metrics and observability module for CV Generator."""

import datetime
import uuid
import json
from typing import Optional, Dict, Any
import streamlit as st

# Lazy imports to avoid requiring these packages if not configured
def get_supabase_client():
    """Get Supabase client with lazy import."""
    try:
        from supabase import create_client
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            return create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"]
            )
    except Exception as e:
        print(f"Supabase not configured: {e}")
    return None


def get_posthog_client():
    """Get PostHog client with lazy import."""
    try:
        import posthog
        if "POSTHOG_KEY" in st.secrets:
            # PostHog 3.0+ uses api_key instead of project_api_key
            posthog.api_key = st.secrets["POSTHOG_KEY"]
            posthog.host = st.secrets.get("POSTHOG_HOST", "https://app.posthog.com")
            return posthog
    except Exception as e:
        print(f"PostHog not configured: {e}")
    return None


def initialize_session_metrics():
    """Initialize metrics tracking in session state."""
    if "metrics" not in st.session_state:
        st.session_state.metrics = {
            "session_id": str(uuid.uuid4()),
            "session_start": datetime.datetime.now(),
            "first_user_input": None,
            "cv_generation_attempts": [],
            "events": [],
            "errors": [],
            "total_tokens": 0,
            "response_times": [],
            "stages_completed": [],
            "device_info": get_device_info(),
            "entry_source": "direct"  # Can be updated based on query params
        }


def get_device_info() -> Dict[str, str]:
    """Extract device information from user agent."""
    try:
        # Streamlit doesn't expose user agent directly, but we can infer from context
        # This is a placeholder - in production you'd use request headers
        return {
            "type": "unknown",
            "browser": "unknown",
            "os": "unknown"
        }
    except Exception:
        return {"type": "unknown"}


def log_event(event_name: str, properties: Optional[Dict[str, Any]] = None):
    """
    Log an event to both local state and external services.

    Args:
        event_name: Name of the event (e.g., 'cv_generated', 'error_occurred')
        properties: Additional event metadata
    """
    if "metrics" not in st.session_state:
        initialize_session_metrics()

    timestamp = datetime.datetime.now()
    event = {
        "timestamp": timestamp.isoformat(),
        "event": event_name,
        "properties": properties or {}
    }

    # Log to session state
    st.session_state.metrics["events"].append(event)

    # Log to PostHog
    posthog = get_posthog_client()
    if posthog:
        try:
            posthog.capture(
                distinct_id=st.session_state.metrics["session_id"],
                event=event_name,
                properties={
                    **event["properties"],
                    "session_duration": get_session_duration(),
                    "message_count": len(st.session_state.get("messages", []))
                }
            )
        except Exception as e:
            print(f"PostHog logging failed: {e}")


def log_error(error_type: str, error_message: str, context: Optional[Dict] = None):
    """Log an error with context."""
    if "metrics" not in st.session_state:
        initialize_session_metrics()

    error = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": error_type,
        "message": error_message,
        "context": context or {}
    }

    st.session_state.metrics["errors"].append(error)
    log_event("error_occurred", {
        "error_type": error_type,
        "error_message": error_message
    })


def track_first_user_input():
    """Track the timestamp of the first user input."""
    if "metrics" not in st.session_state:
        initialize_session_metrics()

    if st.session_state.metrics["first_user_input"] is None:
        st.session_state.metrics["first_user_input"] = datetime.datetime.now()
        log_event("first_user_input")


def track_cv_generation_attempt():
    """Track a CV generation attempt with timing."""
    if "metrics" not in st.session_state:
        initialize_session_metrics()

    first_input = st.session_state.metrics["first_user_input"]
    if first_input:
        time_to_generate = (datetime.datetime.now() - first_input).total_seconds()
    else:
        time_to_generate = None

    attempt = {
        "timestamp": datetime.datetime.now().isoformat(),
        "time_from_start": time_to_generate,
        "message_count": len(st.session_state.get("messages", []))
    }

    st.session_state.metrics["cv_generation_attempts"].append(attempt)

    log_event("cv_generation_clicked", {
        "attempt_number": len(st.session_state.metrics["cv_generation_attempts"]),
        "time_from_start_seconds": time_to_generate,
        "message_count": attempt["message_count"]
    })


def get_session_duration() -> float:
    """Get current session duration in seconds."""
    if "metrics" not in st.session_state:
        return 0

    start = st.session_state.metrics["session_start"]
    return (datetime.datetime.now() - start).total_seconds()


def calculate_completion_time() -> Optional[float]:
    """Calculate time from first input to CV generation (last attempt)."""
    if "metrics" not in st.session_state:
        return None

    attempts = st.session_state.metrics.get("cv_generation_attempts", [])
    if not attempts:
        return None

    return attempts[-1]["time_from_start"]


async def score_cv_quality(cv_dict: Dict, client) -> Dict[str, Any]:
    """
    Use AI to score CV quality on multiple dimensions.

    Args:
        cv_dict: The CV data dictionary
        client: OpenAI client

    Returns:
        Dictionary with scores and overall quality assessment
    """
    from src.llm_client import get_response, generator_to_string

    cv_text = json.dumps(cv_dict, ensure_ascii=False, indent=2)

    prompt = f"""
Du er en profesjonell CV-evaluator. Vurder følgende CV på disse dimensjonene (0-5 poeng hver):

1. **Structure** (0-5): Hvor godt organisert og strukturert er CV-en?
2. **Clarity** (0-5): Hvor tydelig og lett å forstå er innholdet?
3. **Grammar** (0-5): Språklig kvalitet og grammatikk
4. **Relevance** (0-5): Hvor relevant er informasjonen for jobbsøking?
5. **Impact** (0-5): Hvor godt viser CV-en kandidatens prestasjoner og verdi?

CV data:
{cv_text}

Returner BARE et JSON-objekt i dette formatet:
{{
    "structure": <score 0-5>,
    "clarity": <score 0-5>,
    "grammar": <score 0-5>,
    "relevance": <score 0-5>,
    "impact": <score 0-5>,
    "feedback": "<kort forklaring på scores>",
    "suggestions": ["<forbedringforslag 1>", "<forbedringsforslag 2>"]
}}
"""

    try:
        response_gen = get_response(client, prompt)
        response = generator_to_string(response_gen)

        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())

            # Calculate weighted score (out of 100)
            # Each dimension weighted equally = 20 points max each
            total_score = sum([
                scores.get("structure", 0) * 4,
                scores.get("clarity", 0) * 4,
                scores.get("grammar", 0) * 4,
                scores.get("relevance", 0) * 4,
                scores.get("impact", 0) * 4
            ])

            scores["total_score"] = total_score

            # Determine quality level
            if total_score < 20:
                scores["quality_level"] = "needs_work"
            elif total_score < 70:
                scores["quality_level"] = "good"
            elif total_score < 85:
                scores["quality_level"] = "very_good"
            else:
                scores["quality_level"] = "excellent"

            return scores
        else:
            raise ValueError("Could not parse JSON from AI response")

    except Exception as e:
        log_error("cv_quality_scoring_failed", str(e))
        return {
            "error": str(e),
            "total_score": 0,
            "quality_level": "error"
        }


def save_session_metrics():
    """Save session metrics to Supabase at session end."""
    if "metrics" not in st.session_state:
        return

    supabase = get_supabase_client()
    if not supabase:
        return

    try:
        metrics = st.session_state.metrics

        # Prepare data for database
        session_data = {
            "session_id": metrics["session_id"],
            "session_start": metrics["session_start"].isoformat(),
            "session_duration": get_session_duration(),
            "first_user_input": metrics["first_user_input"].isoformat() if metrics["first_user_input"] else None,
            "cv_generated": len(metrics["cv_generation_attempts"]) > 0,
            "cv_downloaded": any(e["event"] == "cv_downloaded" for e in metrics["events"]),
            "generation_attempts": len(metrics["cv_generation_attempts"]),
            "message_count": len(st.session_state.get("messages", [])),
            "total_tokens": metrics["total_tokens"],
            "errors_count": len(metrics["errors"]),
            "device_type": metrics["device_info"].get("type"),
            "entry_source": metrics["entry_source"],
            "events": json.dumps(metrics["events"]),
            "errors": json.dumps(metrics["errors"]),
            "completion_times": json.dumps([a["time_from_start"] for a in metrics["cv_generation_attempts"]])
        }

        # Insert into Supabase
        supabase.table('sessions').insert(session_data).execute()

    except Exception as e:
        print(f"Failed to save metrics to Supabase: {e}")


def get_metrics_summary() -> Dict[str, Any]:
    """Get a summary of current session metrics."""
    if "metrics" not in st.session_state:
        return {}

    metrics = st.session_state.metrics

    return {
        "session_id": metrics["session_id"],
        "duration_seconds": get_session_duration(),
        "cv_generated": len(metrics["cv_generation_attempts"]) > 0,
        "generation_attempts": len(metrics["cv_generation_attempts"]),
        "message_count": len(st.session_state.get("messages", [])),
        "error_count": len(metrics["errors"]),
        "completion_time": calculate_completion_time()
    }
