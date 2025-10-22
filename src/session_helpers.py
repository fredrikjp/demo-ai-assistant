"""Session state and data extraction helpers for Streamlit CV Generator."""

import datetime
import streamlit as st
from src.llm_client import build_question_prompt, get_response, generator_to_string
from src.data_utils import save_json_str_to_dict, extract_personalia_from_json
from src.metrics import initialize_session_metrics, log_event


def initialize_app_session_state():
    """Initialize all session state variables for the application."""
    # Initialize metrics tracking
    initialize_session_metrics()

    # Initialize timestamp for rate limiting
    if "prev_question_timestamp" not in st.session_state:
        st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

    # Initialize pill selection tracking
    if "selected_pill_suggestions" not in st.session_state:
        st.session_state.selected_pill_suggestions = []

    # Initialize draft message text (editable version of selected pills)
    if "draft_message_text" not in st.session_state:
        st.session_state.draft_message_text = ""

    # Track entry source from query params
    if "entry_source_tracked" not in st.session_state:
        source = st.query_params.get("source", "direct")
        st.session_state.metrics["entry_source"] = source
        st.session_state.entry_source_tracked = True
        log_event("session_started", {"entry_source": source})


def extract_and_save_json_data(client):
    """Extract JSON data from conversation and save to session state.

    Args:
        client: OpenAI client instance
    """
    if not st.session_state.get("CV_mode", False) or len(st.session_state.messages) < 3:
        return

    assistant_question = st.session_state.messages[-3]["content"]
    user_answer = st.session_state.messages[-2]["content"]

    # Build JSON extraction prompt
    json_prompt = build_question_prompt(
        st.session_state.messages,
        f"Spørsmål: {assistant_question}\nSvar: {user_answer}",
        json_generator=True
    )

    # Get JSON response from LLM
    json_response_gen = get_response(client, json_prompt)
    json_str = generator_to_string(json_response_gen)

    # Handle personalia extraction on initial questions
    if st.session_state.get("initial_CV_questions", False) and not st.session_state.get("CV_uploaded", False):
        try:
            name, dob = extract_personalia_from_json(json_str)
            st.session_state.personalia_name = name
            st.session_state.personalia_dob = dob
            st.session_state.initial_CV_questions = False
        except:
            st.write("\nKunne ikke hente personalia. Vennligst skriv inn navn og fødselsdato (DD.MM.ÅÅ) på nytt.")
            st.session_state.initial_CV_questions = True

    # Save extracted data to session state
    save_json_str_to_dict(st.session_state, json_str)
