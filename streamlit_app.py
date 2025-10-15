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

# Import from our modules
from src.config import (
    SUGGESTIONS,
    MIN_TIME_BETWEEN_REQUESTS,
    CV_SCHEMA
)
from src.llm_client import (
    get_openai_client,
    build_question_prompt,
    get_response,
    generator_to_string,
    generate_personalized_examples
)
from src.cv_generator import json_to_cv_pdf, generate_word_docx
from src.data_utils import (
    save_json_str_to_dict,
    extract_personalia_from_json,
    extract_cv_from_pdf
)
from src.metrics import (
    initialize_session_metrics,
    log_event,
    log_error,
    track_first_user_input,
    track_cv_generation_attempt,
    get_session_duration
)

# Initialize OpenAI client
client = get_openai_client(api_key=st.secrets["OPENAI_API_KEY"])

# Page configuration
st.set_page_config(page_title="Ungt Steg AI Assistent", page_icon="✨")

# Debug mode
DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"


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


# -----------------------------------------------------------------------------
# UI Setup

st.html(div(style=styles(font_size=rem(5), line_height=1))["❉"])

title_row = st.container(horizontal=True, vertical_alignment="bottom")

with title_row:
    st.title("Ungt Steg AI assistent", anchor=False, width="stretch")

# Check user interaction state
user_just_asked_initial_question = (
    "initial_question" in st.session_state and st.session_state.initial_question
)

user_just_clicked_suggestion = (
    "selected_suggestion" in st.session_state and st.session_state.selected_suggestion
)

user_first_interaction = (
    user_just_asked_initial_question or user_just_clicked_suggestion
)

has_message_history = (
    "messages" in st.session_state and len(st.session_state.messages) > 0
)

# Initialize session state
if "prev_question_timestamp" not in st.session_state:
    st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

# Initialize metrics tracking
initialize_session_metrics()

# Track entry source from query params
if "entry_source_tracked" not in st.session_state:
    source = st.query_params.get("source", "direct")
    st.session_state.metrics["entry_source"] = source
    st.session_state.entry_source_tracked = True
    log_event("session_started", {"entry_source": source})

# Show initial UI when no question asked yet
if not user_first_interaction and not has_message_history:
    st.session_state.messages = []
    st.session_state.is_pdf_ready = False
    st.session_state.initial_stream_done = False

    with st.container():
        st.chat_input("Ask a question...", key="initial_question")

        selected_suggestion = st.pills(
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

# Show chat input at bottom
user_message = st.chat_input("Ask a follow-up...")

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

        # Initial question from the chatbot
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Hei! Jeg er her for å hjelpe deg med å lage en CV. "
                    "For å komme i gang, last opp din CV (pdf) eller skriv ditt fulle navn og fødselsdato (DD.MM.ÅÅ)"
                ),
            }
        )
        st.session_state.initial_CV_questions = True

# Add restart button
with title_row:
    def clear_conversation():
        st.session_state.messages = []
        st.session_state.initial_question = None
        st.session_state.selected_suggestion = None

    st.button(
        "Restart",
        icon=":material/refresh:",
        on_click=clear_conversation,
    )

# PDF uploader
uploaded_cv = st.file_uploader("Last opp eksisterende CV (pdf)", type=["pdf"])

if uploaded_cv is not None and not st.session_state.get("CV_uploaded", False):
    st.session_state.messages = []

# Display chat history
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "pdf_uploaded":
        continue

    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container()  # Fix ghost message bug

        if not st.session_state.initial_stream_done:
            def generator_initial_question(text, delay=0.01):
                for ch in text:
                    yield ch
                    time.sleep(delay)
                st.session_state.initial_stream_done = True

            response = st.write_stream(generator_initial_question(st.session_state.messages[-1]["content"]))
            continue

        st.markdown(message["content"])

        # Show examples expander for historical messages if available
        if message["role"] == "assistant" and message.get("examples"):
            with st.expander("💡 Se eksempler", expanded=False):
                st.markdown(message["examples"])

# Handle PDF upload
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

        # Get next question from assistant
        pdf_message_content = f"Bruker har lastet opp en CV med følgende informasjon: {cv_dict}. Bekreft at du har mottatt informasjonen og still et nytt spørsmål for å samle mer eller manglende informasjon"

        st.session_state.messages.append(
            {
                "role": "pdf_uploaded",
                "content": pdf_message_content,
            }
        )

        with st.spinner("Analyserer CV..."):
            full_prompt = build_question_prompt(
                st.session_state.messages,
                pdf_message_content
            )
            response_gen = get_response(client, full_prompt)
            response = generator_to_string(response_gen)
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.session_state.CV_uploaded = True
        st.rerun()
    else:
        st.error("Kunne ikke tolke CVen. Vennligst prøv en annen CV.")

# Handle user message
if user_message:
    st.session_state.user_message = user_message
    st.session_state.generate_CV_button_clicked = False
    # Clear CV generation trigger when user sends a message
    st.session_state.trigger_cv_generation = False

    # Escape markdown special characters
    user_message = user_message.replace("$", r"\$")

    # Display user message
    try:
        if not st.session_state.messages[-2]["role"] == "pdf_uploaded":
            with st.chat_message("user"):
                st.text(user_message)
    except:
        with st.chat_message("user"):
            st.text(user_message)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Waiting..."):
            # Rate limiting
            question_timestamp = datetime.datetime.now()
            time_diff = question_timestamp - st.session_state.prev_question_timestamp
            st.session_state.prev_question_timestamp = question_timestamp

            if time_diff < MIN_TIME_BETWEEN_REQUESTS:
                time.sleep(time_diff.seconds + time_diff.microseconds * 0.001)

            user_message = user_message.replace("'", "")

        # Build prompt
        if DEBUG_MODE:
            with st.status("Computing prompt...") as status:
                full_prompt = build_question_prompt(st.session_state.messages, user_message)
                st.code(full_prompt)
                status.update(label="Prompt computed")
        else:
            with st.spinner("Researching..."):
                full_prompt = build_question_prompt(st.session_state.messages, user_message)

        # Get LLM response
        with st.spinner("Thinking..."):
            response_gen = get_response(client, full_prompt)

        # Stream response
        with st.container():
            response = st.write_stream(response_gen)

            # Generate personalized examples after streaming
            examples = None
            if st.session_state.get("CV_mode", False):
                user_data = st.session_state.get("CV_dict", {})
                examples = generate_personalized_examples(client, response, user_data)

            # Add to chat history
            st.session_state.messages.append({"role": "user", "content": user_message})
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "examples": examples
            })

            # Show examples expander and CV button if available
            # Don't show during CV generation to prevent duplicate display
            if not st.session_state.get("trigger_cv_generation", False):
                if examples or (st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        if examples:
                            with st.expander("💡 Se eksempler", expanded=False):
                                st.markdown(examples)

                    with col2:
                        if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
                            def trigger_generation():
                                st.session_state.trigger_cv_generation = True
                                track_cv_generation_attempt()

                            st.button(
                                "📄 Generer CV",
                                key=f"generate_cv_button_{len(st.session_state.messages)}",
                                on_click=trigger_generation
                            )

            # Extract JSON data if in CV mode
            if st.session_state.get("CV_mode", False) and len(st.session_state.messages) > 1:
                assistant_question = st.session_state.messages[-3]["content"]
                user_answer = st.session_state.messages[-2]["content"]

                json_prompt = build_question_prompt(
                    st.session_state.messages,
                    f"Spørsmål: {assistant_question}\nSvar: {user_answer}",
                    json_generator=True
                )
                json_response_gen = get_response(client, json_prompt)
                json_str = generator_to_string(json_response_gen)

                # Save personalia on initial questions
                if st.session_state.get("initial_CV_questions", False) and not st.session_state.get("CV_uploaded", False):
                    try:
                        name, dob = extract_personalia_from_json(json_str)
                        st.session_state.personalia_name = name
                        st.session_state.personalia_dob = dob
                        st.session_state.initial_CV_questions = False
                    except:
                        st.write("\nKunne ikke hente personalia. Vennligst skriv inn navn og fødselsdato (DD.MM.ÅÅ) på nytt.")
                        st.session_state.initial_CV_questions = True

                save_json_str_to_dict(st.session_state, json_str)

# Handle CV generation trigger (after all chat processing, shows spinner below chat)
if st.session_state.get("trigger_cv_generation", False):
    st.session_state.trigger_cv_generation = False

    # Verify CV_dict exists before generating
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

# Show download button if PDF exists and not currently processing a message
# (placed below chat history, above chat_input)
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



