"""UI helper functions for Streamlit CV Generator."""

import time
import streamlit as st
from src.data_utils import parse_examples_to_list
from src.metrics import track_cv_generation_attempt


def display_suggestions_and_cv_button(suggestions, key_suffix):
    """Display suggestion pills and CV generation button side by side.

    Args:
        suggestions: Markdown string with bullet-point suggestions
        key_suffix: Unique suffix for widget keys (e.g., "pdf_1", "user_2")
    """
    col1, col2 = st.columns([4, 1])

    with col1:
        if suggestions:
            suggestion_items = parse_examples_to_list(suggestions)
            if suggestion_items:
                with st.expander("💡 Klikk for å velge forslag", expanded=False):
                    # Let the widget manage its own state via the key
                    st.pills(
                        label="Velg forslag (kan velge flere)",
                        options=suggestion_items,
                        selection_mode="multi",
                        key=f"pills_{key_suffix}"
                    )

                    # Read the widget's value from session state (not a circular assignment)
                    st.session_state.selected_pill_suggestions = st.session_state.get(f"pills_{key_suffix}", [])

    with col2:
        if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
            st.button(
                "📄 Generer CV",
                key=f"generate_cv_button_{key_suffix}",
                on_click=lambda: trigger_cv_generation()
            )


def trigger_cv_generation():
    """Trigger CV generation and track the attempt."""
    st.session_state.trigger_cv_generation = True
    track_cv_generation_attempt()


def display_draft_preview():
    """Display draft message preview with editable text area if pills are selected."""
    if st.session_state.selected_pill_suggestions:
        with st.chat_message("user"):
            # Initialize draft message in session state if not exists
            if "draft_message_text" not in st.session_state:
                st.session_state.draft_message_text = ""

            # Update draft text when pills change
            current_draft = "\n".join(st.session_state.selected_pill_suggestions)
            if current_draft != st.session_state.draft_message_text:
                st.session_state.draft_message_text = current_draft

            # Editable text area for draft message
            st.session_state.draft_message_text = st.text_area(
                label="Rediger utkast",
                value=st.session_state.draft_message_text,
                height=150,
                key="draft_text_area",
                help="Du kan redigere forslagene før du sender"
            )
            st.caption("👆 Utkast fra valgte forslag (ikke sendt ennå) - kan redigeres")


def stream_initial_message(text, delay=0.01):
    """Generator for streaming initial message character by character.

    Args:
        text: Text to stream
        delay: Delay between characters in seconds

    Yields:
        str: Single characters from text
    """
    for ch in text:
        yield ch
        time.sleep(delay)
    st.session_state.initial_stream_done = True


def combine_pills_with_user_input(user_message):
    """Combine selected pill suggestions (or edited draft) with user message.

    Args:
        user_message: User's input message (can be empty string or text)

    Returns:
        str: Combined message with draft/pills first, then user input
    """
    if st.session_state.selected_pill_suggestions:
        # Use edited draft text if available, otherwise use pills directly
        draft_text = st.session_state.get("draft_message_text", "")
        if draft_text:
            combined = draft_text + ("\n" + user_message if user_message else "")
        else:
            pill_text = "\n".join(st.session_state.selected_pill_suggestions)
            combined = pill_text + ("\n" + user_message if user_message else "")

        # Clear after combining
        st.session_state.selected_pill_suggestions = []
        st.session_state.draft_message_text = ""
        return combined
    return user_message
