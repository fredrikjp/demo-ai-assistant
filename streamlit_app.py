# Copyright 2025 Snowflake Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Streamlit CV Generator Application - Main Entry Point"""

import datetime
import time
import streamlit as st
from htbuilder.units import rem
from htbuilder import div, styles

# Import configuration
from src.config import SUGGESTIONS, MIN_TIME_BETWEEN_REQUESTS

# Import LLM functions
from src.llm_client import (
    get_openai_client,
    build_question_prompt,
    get_response,
    generate_adaptive_suggestions
)

# Import data functions
from src.cv_generator import json_to_cv_pdf
from src.data_utils import extract_cv_from_pdf

# Import metrics
from src.metrics import (
    log_event,
    log_error,
    track_first_user_input,
    get_session_duration
)

# Import UI and session helpers
from src.ui_helpers import (
    display_suggestions_and_cv_button,
    display_draft_preview,
    stream_initial_message,
    combine_pills_with_user_input
)
from src.session_helpers import (
    initialize_app_session_state,
    extract_and_save_json_data
)

# -----------------------------------------------------------------------------
# App Initialization
# -----------------------------------------------------------------------------

# Initialize OpenAI client
client = get_openai_client(api_key=st.secrets["OPENAI_API_KEY"])

# Page configuration
st.set_page_config(page_title="Ungt Steg AI Assistent", page_icon="✨")

# Debug mode
DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"

# Initialize session state
initialize_app_session_state()


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def show_disclaimer_dialog():
    """Show legal disclaimer dialog."""
    st.caption("""
        This AI chatbot is powered by OpenAI. Answers may be inaccurate, inefficient, or biased.
        Any use or decisions based on such answers should include reasonable
        practices including human oversight to ensure they are safe,
        accurate, and suitable for your intended purpose. Do not enter any private, sensitive, personal, or
        regulated data. By using this chatbot, you acknowledge and agree
        that input you provide and answers you receive (collectively,
        "Content") may be used by the service provider to improve their offerings.
    """)


def clear_conversation():
    """Reset conversation state."""
    st.session_state.messages = []
    st.session_state.initial_question = None
    st.session_state.selected_suggestion = None


def check_user_interaction():
    """Check user interaction state for initial UI."""
    user_just_asked = "initial_question" in st.session_state and st.session_state.initial_question
    user_clicked_suggestion = "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
    user_first_interaction = user_just_asked or user_clicked_suggestion
    has_history = "messages" in st.session_state and len(st.session_state.messages) > 0

    return user_just_asked, user_clicked_suggestion, user_first_interaction, has_history


# -----------------------------------------------------------------------------
# UI Setup
# -----------------------------------------------------------------------------

st.html(div(style=styles(font_size=rem(5), line_height=1))["❉"])

title_row = st.container(horizontal=True, vertical_alignment="bottom")
with title_row:
    st.title("Ungt Steg AI assistent", anchor=False, width="stretch")

# Check user interaction state
user_just_asked_initial_question, user_just_clicked_suggestion, user_first_interaction, has_message_history = check_user_interaction()

# Show initial UI when no interaction yet
if not user_first_interaction and not has_message_history:
    st.session_state.messages = []
    st.session_state.is_pdf_ready = False
    st.session_state.initial_stream_done = False

    with st.container():
        st.chat_input("Ask a question...", key="initial_question")
        st.pills(
            label="Examples",
            label_visibility="collapsed",
            options=SUGGESTIONS.keys(),
            key="selected_suggestion",
        )

    st.button(
        "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
        type="tertiary",
        on_click=show_disclaimer_dialog,
    )
    st.stop()

# Show chat input and restart button
user_message = st.chat_input("Ask a follow-up...")

with title_row:
    st.button("Restart", icon=":material/refresh:", on_click=clear_conversation)

# Handle initial interaction
if not user_message:
    st.session_state.json_response = "{}"
    if user_just_asked_initial_question:
        user_message = st.session_state.initial_question
        st.session_state.CV_mode = False
        track_first_user_input()
        log_event("initial_question_asked", {"question_length": len(user_message)})

    if user_just_clicked_suggestion:
        st.session_state.CV_mode = True
        st.session_state.CV_uploaded = False
        track_first_user_input()
        log_event("cv_mode_selected")
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Hei! Jeg er her for å hjelpe deg med å lage en CV. "
                "For å komme i gang, last opp din CV (pdf) eller skriv ditt fulle navn og fødselsdato (DD.MM.ÅÅ)"
            ),
        })
        st.session_state.initial_CV_questions = True

# PDF uploader
uploaded_cv = st.file_uploader("Last opp eksisterende CV (pdf)", type=["pdf"])
if uploaded_cv is not None and not st.session_state.get("CV_uploaded", False):
    st.session_state.messages = []


# -----------------------------------------------------------------------------
# Display Chat History
# -----------------------------------------------------------------------------

# Check if we're about to create a new message inline
creating_new_message = (
    (uploaded_cv is not None and not st.session_state.get("CV_uploaded", False)) or
    (user_message is not None)
)

for i, message in enumerate(st.session_state.messages):
    if message["role"] == "pdf_uploaded":
        continue

    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container()  # Fix ghost message bug

        # Stream initial message
        if not st.session_state.initial_stream_done:
            st.write_stream(stream_initial_message(st.session_state.messages[-1]["content"]))
            continue

        st.markdown(message["content"])

        # Show suggestions only for the most recent assistant message
        # Don't show if we're about to create a new message inline (to avoid duplication)
        if message["role"] == "assistant" and message.get("suggestions"):
            is_last_message = (i == len(st.session_state.messages) - 1)
            if is_last_message and not creating_new_message:
                display_suggestions_and_cv_button(message["suggestions"], f"history_{i}")


# Show draft message preview (only when not sending)
if user_message is None:
    display_draft_preview()


# -----------------------------------------------------------------------------
# Handle PDF Upload
# -----------------------------------------------------------------------------

if uploaded_cv is not None and not st.session_state.get("CV_uploaded", False):
    log_event("cv_pdf_uploaded", {"file_name": uploaded_cv.name, "file_size": uploaded_cv.size})

    with st.spinner("Leser og tolker CV..."):
        try:
            cv_dict = extract_cv_from_pdf(client, uploaded_cv)
        except Exception as e:
            log_error("cv_pdf_extraction_failed", str(e), {"file_name": uploaded_cv.name})
            raise

    if cv_dict:
        st.session_state.CV_dict = cv_dict
        st.success("CV data lastet inn!")
        log_event("cv_pdf_parsed_success")

        # Prepare message for assistant
        pdf_message_content = f"Bruker har lastet opp en CV med følgende informasjon: {cv_dict}. Bekreft at du har mottatt informasjonen og still et nytt spørsmål for å samle mer eller manglende informasjon"
        st.session_state.messages.append({"role": "pdf_uploaded", "content": pdf_message_content})

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyserer CV..."):
                full_prompt = build_question_prompt(st.session_state.messages, pdf_message_content)
                response_gen = get_response(client, full_prompt)

            response = st.write_stream(response_gen)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "suggestions": None
            })

            # Mark that we just created a new message
            st.session_state.new_message_created = True

        st.session_state.CV_uploaded = True
    else:
        st.error("Kunne ikke tolke CVen. Vennligst prøv en annen CV.")


# -----------------------------------------------------------------------------
# Handle User Message
# -----------------------------------------------------------------------------

def process_user_message(message):
    """Process and sanitize user message."""
    # Combine pill selections with user input
    message = combine_pills_with_user_input(message)
    # Escape markdown special characters
    message = message.replace("$", r"\$")
    message = message.replace("'", "")
    return message


def apply_rate_limiting():
    """Apply rate limiting between requests."""
    question_timestamp = datetime.datetime.now()
    time_diff = question_timestamp - st.session_state.prev_question_timestamp
    st.session_state.prev_question_timestamp = question_timestamp

    if time_diff < MIN_TIME_BETWEEN_REQUESTS:
        time.sleep(time_diff.seconds + time_diff.microseconds * 0.001)


def get_llm_response(user_message):
    """Build prompt and get LLM response."""
    if DEBUG_MODE:
        with st.status("Computing prompt...") as status:
            full_prompt = build_question_prompt(st.session_state.messages, user_message)
            st.code(full_prompt)
            status.update(label="Prompt computed")
    else:
        with st.spinner("Researching..."):
            full_prompt = build_question_prompt(st.session_state.messages, user_message)

    with st.spinner("Thinking..."):
        response_gen = get_response(client, full_prompt)

    return st.write_stream(response_gen)


if user_message is not None:
    # Process user message
    user_message = process_user_message(user_message)

    # Update session state
    st.session_state.user_message = user_message
    st.session_state.generate_CV_button_clicked = False
    st.session_state.trigger_cv_generation = False

    # Display user message
    with st.chat_message("user"):
        st.text(user_message)

    # Display assistant response
    with st.chat_message("assistant"):
        # Rate limiting
        with st.spinner("Waiting..."):
            apply_rate_limiting()

        # Get LLM response
        response = get_llm_response(user_message)

        # Add to chat history
        st.session_state.messages.append({"role": "user", "content": user_message})
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "suggestions": None
        })

        # Mark that we just created a new message
        st.session_state.new_message_created = True


# -----------------------------------------------------------------------------
# Post-Message Processing (for both user messages and PDF uploads)
# -----------------------------------------------------------------------------

if st.session_state.get("new_message_created", False):
    # Get the most recent assistant message
    last_message = st.session_state.messages[-1]

    # Generate suggestions if in CV mode
    if st.session_state.get("CV_mode", False) and last_message["role"] == "assistant":
        user_data = st.session_state.get("CV_dict", {})
        suggestions = generate_adaptive_suggestions(client, last_message["content"], user_data)
        st.session_state.messages[-1]["suggestions"] = suggestions

        # Display suggestions and CV button inline
        if not st.session_state.get("trigger_cv_generation", False):
            display_suggestions_and_cv_button(suggestions, f"user_{len(st.session_state.messages)}")

    # Extract JSON data from conversation
    extract_and_save_json_data(client)

    # Reset the flag
    st.session_state.new_message_created = False


# -----------------------------------------------------------------------------
# Handle CV Generation
# -----------------------------------------------------------------------------

if st.session_state.get("trigger_cv_generation", False):
    st.session_state.trigger_cv_generation = False

    if "CV_dict" in st.session_state:
        with st.spinner("Genererer CV..."):
            try:
                json_to_cv_pdf(client, st.session_state.CV_dict)
                with open("CV.pdf", "rb") as f:
                    st.session_state["CV_pdf"] = f.read()
                st.success("CV generert!")
                st.session_state.generate_CV_button_clicked = True
                log_event("cv_generated_success", {
                    "message_count": len(st.session_state.get("messages", [])),
                    "session_duration": get_session_duration()
                })
            except FileNotFoundError as e:
                log_error("cv_generation_pdf_not_found", str(e))
                st.error("PDF ikke funnet. Vennligst prøv å generere CVen på nytt.")
            except Exception as e:
                log_error("cv_generation_failed", str(e))
                st.error(f"Feil under generering av CV: {str(e)}")
    else:
        log_error("cv_generation_no_data", "CV_dict not in session state")
        st.error("Ingen CV data funnet. Vennligst samle inn data først.")


# -----------------------------------------------------------------------------
# Show Download Button
# -----------------------------------------------------------------------------

if "CV_pdf" in st.session_state and st.session_state.get("generate_CV_button_clicked", False) and not user_message:
    download_clicked = st.download_button(
        type="primary",
        label="📥 Last ned CV",
        data=st.session_state["CV_pdf"],
        file_name="CV.pdf",
        mime='application/pdf',
        use_container_width=True
    )
    if download_clicked:
        log_event("cv_downloaded", {
            "session_duration": get_session_duration(),
            "message_count": len(st.session_state.get("messages", []))
        })
