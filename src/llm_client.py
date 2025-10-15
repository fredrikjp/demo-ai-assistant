"""LLM interaction functions for the CV Generator."""

from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple
from openai import OpenAI

from src.config import MODEL, HISTORY_LENGTH, SUMMARIZE_OLD_HISTORY


# Thread pool for parallel tasks
executor = ThreadPoolExecutor(max_workers=5)

# Task objects for better readability
TaskInfo = namedtuple("TaskInfo", ["name", "function", "args"])
TaskResult = namedtuple("TaskResult", ["name", "result"])


def get_openai_client(api_key):
    """Initialize and return OpenAI client."""
    return OpenAI(api_key=api_key)


def build_prompt(**kwargs):
    """Builds a prompt string with the kwargs as HTML-like tags.

    For example:
        build_prompt(foo="1\n2\n3", bar="4\n5\n6")

    Returns:
        '''
        <foo>
        1
        2
        3
        </foo>
        <bar>
        4
        5
        6
        </bar>
        '''
    """
    prompt = []

    for name, contents in kwargs.items():
        if contents:
            prompt.append(f"<{name}>\n{contents}\n</{name}>")

    prompt_str = "\n".join(prompt)
    return prompt_str


def history_to_text(chat_history):
    """Converts chat history into a string."""
    return "\n".join(f"[{h['role']}]: {h['content']}" for h in chat_history)


def generate_chat_summary(client, messages):
    """
    Summarize a conversation history using the OpenAI API.

    Args:
        client: OpenAI client instance
        messages (list[dict]): Chat history with {"role": "user"|"assistant", "content": str}

    Returns:
        str: A concise summary of the conversation
    """
    prompt = build_prompt(
        instructions="Summarize this conversation as concisely as possible.",
        conversation=history_to_text(messages),
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def build_question_prompt(messages, question, json_generator=False):
    """Fetches info from different services and creates the prompt string.

    Args:
        messages: Session state messages list
        question: Current user question
        json_generator: Whether this is for JSON data extraction

    Returns:
        str: Formatted prompt for the LLM
    """
    from src.config import get_instructions, INSTRUCTIONS_GENERATE_DATA_FROM_RESPONSE

    old_history = messages[:-HISTORY_LENGTH] if len(messages) > HISTORY_LENGTH else []
    recent_history = messages[-HISTORY_LENGTH:] if len(messages) > 0 else []

    recent_history_str = history_to_text(recent_history) if recent_history else None

    # Fetch information from different services in parallel
    task_infos = []

    if SUMMARIZE_OLD_HISTORY and old_history:
        # Note: This would need the client, but we'll skip for now to avoid circular dependencies
        pass

    context = {}

    # Import here to avoid circular dependency
    import streamlit as st
    instructions = INSTRUCTIONS_GENERATE_DATA_FROM_RESPONSE if json_generator else get_instructions(st.session_state)

    return build_prompt(
        instructions=instructions,
        **context,
        recent_messages=recent_history_str,
        question=question,
    )


def get_response(client, prompt):
    """
    Stream a response from the OpenAI API for a given prompt.

    Args:
        client: OpenAI client instance
        prompt (str): The user prompt or full conversation context

    Yields:
        str: Chunks of the model's generated text streamed as they arrive
    """
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    for chunk in stream:
        content = getattr(chunk.choices[0].delta, "content", None)
        if content:
            yield content


def generator_to_string(gen):
    """Converts a generator (such as openai stream) to a string."""
    return "".join(chunk for chunk in gen if isinstance(chunk, str))


def generate_personalized_examples(client, question, user_data):
    """
    Generate personalized examples based on the question and user's previous data.

    Args:
        client: OpenAI client instance
        question: The question the assistant just asked
        user_data: Dictionary containing user's CV data so far

    Returns:
        str: Personalized examples in markdown format, or None if no examples needed
    """
    import json

    prompt = f"""
Du er en hjelpfull assistent som genererer personlige eksempler for CV-spørsmål.
Du skal generere eksempler av informasjon assistenten spørr etter

Spørsmål assistenten stilte: {question}

Brukerens informasjon så langt:
{json.dumps(user_data, ensure_ascii=False, indent=2)}

Basert på spørsmålet og brukerens tidligere svar, generer 2-3 konkrete, relevante eksempler som passer brukerens profil (alder, erfaring, utdanningsnivå etc.).

Regler:
- Eksemplene skal være KORTE og KONSISE (1-2 linjer hver)
- Tilpass eksemplene til brukerens situasjon (f.eks. hvis de er ung, gi junior-relaterte eksempler)
- Bruk markdown format med bullet points
- Hvis spørsmålet ikke krever eksempler (f.eks. "ja/nei" spørsmål), returner "NONE"
- Kun returner eksemplene, ingen forklaring

Eksempel output:
- Software Engineer, TechCorp (2020-2023) - Utviklet webapplikasjoner med Python og React
- Junior Developer, StartupAS (2018-2020) - Jobbet med backend-utvikling
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful CV example generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        examples = response.choices[0].message.content.strip()

        # Don't return examples if the LLM says they're not needed
        if examples.upper() == "NONE" or len(examples) < 10:
            return None

        return examples

    except Exception as e:
        print(f"Error generating examples: {e}")
        return None
