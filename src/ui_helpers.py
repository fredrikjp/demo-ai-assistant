"""UI helper functions for Streamlit CV Generator."""

import time
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, Future
from src.data_utils import parse_examples_to_list
from src.metrics import track_cv_generation_attempt


def display_message_with_suggestions(message_content, suggestions, key_suffix):
    """Display assistant message with clickable suggestion examples sidebar layout.

    Args:
        message_content: The assistant's message text
        suggestions: Markdown string with bullet-point suggestions
        key_suffix: Unique suffix for widget keys (e.g., "pdf_1", "user_2")
    """
    # Create sidebar layout: message content on left, suggestions on right
    col_main, col_suggestions = st.columns([2.5, 1])

    # Main message content (left side)
    with col_main:
        st.markdown(message_content)

    # Suggestions sidebar (right side) - clickable examples
    with col_suggestions:
        if suggestions:
            suggestion_items = parse_examples_to_list(suggestions)
            if suggestion_items:
                st.markdown("**💡 Eksempler:**")

                # Initialize selected suggestions in session state
                if "selected_suggestions" not in st.session_state:
                    st.session_state.selected_suggestions = []

                # Display each suggestion as a clickable button with markdown style
                for idx, suggestion in enumerate(suggestion_items):
                    # Create unique key for each suggestion button
                    button_key = f"suggestion_{key_suffix}_{idx}"

                    # Check if this suggestion is already selected
                    is_selected = suggestion in st.session_state.selected_suggestions

                    # Display as a button that looks like text
                    button_label = f"{'✓ ' if is_selected else ''}{suggestion}"
                    button_type = "primary" if is_selected else "secondary"

                    if st.button(
                        button_label,
                        key=button_key,
                        use_container_width=True,
                        type=button_type
                    ):
                        # Toggle selection
                        if is_selected:
                            st.session_state.selected_suggestions.remove(suggestion)
                        else:
                            st.session_state.selected_suggestions.append(suggestion)
                        st.rerun()

                # Store for backwards compatibility
                st.session_state.selected_pill_suggestions = st.session_state.selected_suggestions

        # CV generation button (right below suggestions)
        if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
            st.button(
                "📄 Generer CV",
                key=f"generate_cv_button_{key_suffix}",
                on_click=lambda: trigger_cv_generation(),
                use_container_width=True
            )


def display_suggestions_and_cv_button(suggestions, key_suffix):
    """Display suggestion pills and CV generation button (legacy - for inline display).

    Args:
        suggestions: Markdown string with bullet-point suggestions
        key_suffix: Unique suffix for widget keys (e.g., "pdf_1", "user_2")
    """
    if suggestions:
        suggestion_items = parse_examples_to_list(suggestions)
        if suggestion_items:
            st.markdown("**💡 Forslag:**")

            # Let the widget manage its own state via the key
            st.pills(
                label="Velg forslag",
                label_visibility="collapsed",
                options=suggestion_items,
                selection_mode="multi",
                key=f"pills_{key_suffix}"
            )

            # Read the widget's value from session state (not a circular assignment)
            st.session_state.selected_pill_suggestions = st.session_state.get(f"pills_{key_suffix}", [])

    # CV generation button
    if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
        st.button(
            "📄 Generer CV",
            key=f"generate_cv_button_{key_suffix}",
            on_click=lambda: trigger_cv_generation(),
            use_container_width=True
        )


def trigger_cv_generation():
    """Trigger CV generation and track the attempt."""
    st.session_state.trigger_cv_generation = True
    track_cv_generation_attempt()


def display_draft_preview():
    """Display draft message preview with editable text area if suggestions are selected."""
    # Check both old and new selection state keys for backwards compatibility
    selected_items = st.session_state.get("selected_pill_suggestions", []) or st.session_state.get("selected_suggestions", [])
    if selected_items:
        with st.chat_message("user"):
            # Initialize draft message in session state if not exists
            if "draft_message_text" not in st.session_state:
                st.session_state.draft_message_text = ""

            # Update draft text when suggestions change
            current_draft = "\n".join(selected_items)
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
        st.session_state.selected_suggestions = []
        st.session_state.draft_message_text = ""
        return combined
    return user_message


def stream_message_with_suggestions(response_generator, client, key_suffix):
    """Stream assistant message and suggestions side-by-side with real-time updates.

    Args:
        response_generator: Generator yielding response chunks
        client: OpenAI client for generating suggestions
        key_suffix: Unique suffix for widget keys

    Returns:
        tuple: (response_text, suggestions_text)
    """
    from src.llm_client import generate_adaptive_suggestions

    # Create two-column layout
    col_main, col_suggestions = st.columns([2.5, 1])

    # Containers for streaming content
    with col_main:
        message_container = st.empty()

    with col_suggestions:
        suggestions_container = st.container()
        suggestions_placeholder = suggestions_container.empty()

    # Stream the main response
    response_text = ""
    for chunk in response_generator:
        response_text += chunk
        message_container.markdown(response_text)

    # Now that response is complete, generate suggestions in parallel
    # Show a loading indicator while generating
    with suggestions_placeholder:
        with st.spinner("Genererer forslag..."):
            suggestions = None
            if st.session_state.get("CV_mode", False):
                user_data = st.session_state.get("CV_dict", {})
                suggestions = generate_adaptive_suggestions(client, response_text, user_data)

    # Clear the spinner and display suggestions
    suggestions_placeholder.empty()

    # Display suggestions as clickable buttons
    with suggestions_container:
        if suggestions:
            suggestion_items = parse_examples_to_list(suggestions)
            if suggestion_items:
                st.markdown("**💡 Eksempler:**")

                # Initialize selected suggestions in session state
                if "selected_suggestions" not in st.session_state:
                    st.session_state.selected_suggestions = []

                # Display each suggestion as a clickable button
                for idx, suggestion in enumerate(suggestion_items):
                    button_key = f"suggestion_{key_suffix}_{idx}"
                    is_selected = suggestion in st.session_state.selected_suggestions
                    button_label = f"{'✓ ' if is_selected else ''}{suggestion}"
                    button_type = "primary" if is_selected else "secondary"

                    if st.button(
                        button_label,
                        key=button_key,
                        use_container_width=True,
                        type=button_type
                    ):
                        if is_selected:
                            st.session_state.selected_suggestions.remove(suggestion)
                        else:
                            st.session_state.selected_suggestions.append(suggestion)
                        st.rerun()

                st.session_state.selected_pill_suggestions = st.session_state.selected_suggestions

        # CV generation button
        if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
            st.button(
                "📄 Generer CV",
                key=f"generate_cv_button_{key_suffix}",
                on_click=lambda: trigger_cv_generation(),
                use_container_width=True
            )

    return response_text, suggestions
