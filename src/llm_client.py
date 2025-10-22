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


def generate_adaptive_suggestions(client, question, user_data, request_variation=False):
    """
    Generate context-aware suggestions based on question type and user's CV data.

    Args:
        client: OpenAI client instance
        question: The question the assistant just asked
        user_data: Dictionary containing user's CV data so far
        request_variation: If True, generate alternative/different suggestions

    Returns:
        str: Adaptive suggestions in markdown format, or None if no suggestions needed
    """
    import json

    variation_instruction = ""
    if request_variation:
        variation_instruction = "\n\n**VIKTIG: Generer ALTERNATIVE og FORSKJELLIGE forslag fra tidligere. Vær kreativ og kom med nye ideer som brukeren kanskje ikke har tenkt på. Unngå å gjenta eksempler som har blitt vist før.**\n"

    prompt = f"""
Du er en intelligent CV-assistent som tilpasser forslag basert på spørsmålstype og brukerens profil.

Spørsmål assistenten stilte: {question}

Brukerens CV-data så langt:
{json.dumps(user_data, ensure_ascii=False, indent=2)}
{variation_instruction}
Analyser spørsmålet og generer passende forslag basert på disse retningslinjene:

**TYPE 1 - Spesifikk informasjon (e-post, telefon, adresse, fødselsdato etc.):**
- Generer KUN 1 komplett eksempel som mal
- Eksempel: 
    * "navn@outlook.com"
    * "+47 923 45 678"
    * "gate 23, 0846 Oslo"

**TYPE 2 - Erfaringer/Utdanning (jobberfaring, utdanning, dugnadsarbeid):**
- Generer 2-4 veiledende eksempler som maler
- Tilpass til brukerens alder og erfaring (ung = junior/student-eksempler)
- Hver linje skal være et komplett, konkret eksempel
- Eksempel: "- Butikkmedarbeider, Coop Extra (2022-2023) - Kundeservice og kassearbeid"

**TYPE 3 - Forslag basert på tidligere data (ferdigheter, interesser, jobbønsker):**
- Analyser brukerens utdanning og erfaring
- Generer passende CV mengde, personlige forslag som faktisk passer deres profil
- Hvis de har jobbet i butikk -> foreslå kundeservice-ferdigheter
- Eksempel: "- Kommunikasjon og kundeservice\n- Samarbeid i team\n- Microsoft Office"

**Viktige regler:**
- Bruk ALLTID bullet points (-)
- Være KORT og KONSIST (1-2 linjer per punkt)
- Returner "NONE" hvis spørsmålet ikke trenger forslag
- KUN returner forslagene, ingen forklaring eller overskrift
- Tilpass språknivå og eksempler til brukerens situasjon
- Produser alltid mest sannsynlig forslag for brukeren f.eks. bosted samt alder svært relevant for nåværende skole forslag
- Få med alle sannsynlige forslag: 
    - Språk: Norsk morsmål, Engelsk flytende muntlig utmerked skriftlig, Tysk grunnleggende muntlig og skriftlig, Spansk flytende muntlig og grunnleggende skriftlig, Fransk ... burde være standard og andre språk kan legges til basert på brukerens profil.


Kun returner forslagslisten.
"""

    try:
        # Use higher temperature for variation to get more diverse suggestions
        temperature = 1.0 if request_variation else 0.7

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an intelligent CV suggestion assistant that adapts to question context."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )

        suggestions = response.choices[0].message.content.strip()

        # Don't return suggestions if the LLM says they're not needed
        if suggestions.upper() == "NONE" or len(suggestions) < 10:
            return None

        return suggestions

    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return None
