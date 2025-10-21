"""UI helper functions for Streamlit CV Generator."""

import time
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, Future
from src.data_utils import parse_examples_to_list, calculate_cv_completion
from src.metrics import track_cv_generation_attempt


def render_vertical_progress_bar(completion_percentage):
    """Render a vertical progress bar using HTML/CSS.

    Args:
        completion_percentage: Float between 0.0 and 1.0 representing completion
    """
    percentage = int(completion_percentage * 100)

    # Create vertical progress bar with HTML/CSS
    progress_html = f"""
    <style>
        .vertical-progress {{
            width: 20px;
            height: 513px;
            background-color: #e0e0e0;
            border-radius: 10px;
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        .vertical-progress-fill {{
            width: 100%;
            background: linear-gradient(to top, #4CAF50, #8BC34A);
            position: absolute;
            bottom: 0;
            transition: height 0.3s ease;
            border-radius: 10px;
            height: {percentage}%;
        }}
        .progress-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-90deg);
            font-size: 10px;
            font-weight: bold;
            color: #333;
            white-space: nowrap;
        }}
    </style>
    <div class="vertical-progress">
        <div class="vertical-progress-fill"></div>
        <div class="progress-text">{percentage}%</div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)


def display_message_with_suggestions(message_content, suggestions, key_suffix):
    """Display assistant message with clickable suggestion examples in sidebar.

    Args:
        message_content: The assistant's message text
        suggestions: Markdown string with bullet-point suggestions
        key_suffix: Unique suffix for widget keys (e.g., "pdf_1", "user_2")
    """
    # Main message content
    st.markdown(message_content)

    # Suggestions in actual sidebar
    with st.sidebar:
        # Header above columns, center-aligned and positioned with col2
        st.markdown('<h2 style="margin-left: 7%; margin-top: 0; text-align: center;">💡 Klikkbare forslag/eksempler</h2>', unsafe_allow_html=True)

        col1, col2 = st.columns([0.07,0.93], vertical_alignment="bottom")

        # Add vertical progress bar in col1 (left side)
        with col1:
            cv_dict = st.session_state.get("CV_dict", {})
            completion = calculate_cv_completion(cv_dict)
            render_vertical_progress_bar(completion)

        with col2:
            if suggestions:
                suggestion_items = parse_examples_to_list(suggestions)
                if suggestion_items:

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

            # Add spacing to push button to bottom
            st.container(height=10, border=False)

            # CV generation button at bottom of sidebar
            if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
                st.button(
                    "📄 Generer CV",
                    key=f"generate_cv_button_{key_suffix}",
                    on_click=lambda: trigger_cv_generation(),
                    use_container_width=True,
                    type="primary"
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
    """Stream assistant message and display suggestions in sidebar with real-time updates.

    Args:
        response_generator: Generator yielding response chunks
        client: OpenAI client for generating suggestions
        key_suffix: Unique suffix for widget keys

    Returns:
        tuple: (response_text, suggestions_text)
    """
    from src.llm_client import generate_adaptive_suggestions

    # Main message container
    message_container = st.empty()

    # Stream the main response
    response_text = ""
    for chunk in response_generator:
        response_text += chunk
        message_container.markdown(response_text)

    # Now that response is complete, generate suggestions
    suggestions = None

    # Display suggestions in sidebar
    with st.sidebar:
        # Header above columns, center-aligned and positioned with col2
        st.markdown('<h2 style="margin-left: 7%; margin-top: 0; text-align: center;">💡 Klikkbare forslag/eksempler</h2>', unsafe_allow_html=True)

        col1, col2 = st.columns([0.07,0.93], vertical_alignment="bottom")

        # Add vertical progress bar in col1 (left side)
        with col1:
            cv_dict = st.session_state.get("CV_dict", {})
            completion = calculate_cv_completion(cv_dict)
            render_vertical_progress_bar(completion)

        with col2:
            # Generate suggestions inside sidebar so spinner appears there
            if st.session_state.get("CV_mode", False):
                user_data = st.session_state.get("CV_dict", {})
                with st.spinner("Genererer forslag..."):
                    suggestions = generate_adaptive_suggestions(client, response_text, user_data)

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

            # Add spacing to push button to bottom
            st.container(height=10, border=False)

            # CV generation button at bottom of sidebar
            if st.session_state.get("CV_mode", False) and "CV_dict" in st.session_state:
                st.button(
                    "📄 Generer CV",
                    key=f"generate_cv_button_{key_suffix}",
                    on_click=lambda: trigger_cv_generation(),
                    use_container_width=True,
                    type="primary"
                )

    return response_text, suggestions
