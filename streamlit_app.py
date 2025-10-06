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

from streamlit.runtime.state import session_state
from htbuilder.units import rem
from htbuilder import div, styles
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import datetime
import textwrap
import time

import streamlit as st
from openai import OpenAI
import json
import os
import subprocess
import base64
import sys, os



client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Streamlit AI assistant", page_icon="✨")

# -----------------------------------------------------------------------------
# Set things up.



executor = ThreadPoolExecutor(max_workers=5)

MODEL = "gpt-4.1"

DB = "ST_ASSISTANT"
SCHEMA = "PUBLIC"
DOCSTRINGS_SEARCH_SERVICE = "STREAMLIT_DOCSTRINGS_SEARCH_SERVICE"
PAGES_SEARCH_SERVICE = "STREAMLIT_DOCS_PAGES_SEARCH_SERVICE"
HISTORY_LENGTH = 5
SUMMARIZE_OLD_HISTORY = True
DOCSTRINGS_CONTEXT_LEN = 10
PAGES_CONTEXT_LEN = 10
MIN_TIME_BETWEEN_REQUESTS = datetime.timedelta(seconds=3)

GITHUB_URL = "https://github.com/streamlit/streamlit-assistant"

DEBUG_MODE = st.query_params.get("debug", "false").lower() == "true"

LATEX_TEMPLATE = textwrap.dedent(r"""
    \documentclass[10pt, letterpaper]{article}

    % ========== Packages ==========
    \usepackage[
        ignoreheadfoot,
        top=2 cm,
        bottom=2 cm,
        left=2 cm,
        right=2 cm,
        headsep=1.0 cm,
        footskip=1.0 cm
    ]{geometry}
    \usepackage[explicit]{titlesec}
    \usepackage{tabularx}
    \usepackage{array}
    \usepackage[dvipsnames]{xcolor}
    \definecolor{primaryColor}{RGB}{0, 79, 144}
    \usepackage{enumitem}
    \usepackage{fontawesome5}
    \usepackage{amsmath}
    \usepackage[
        pdftitle={CV},
        pdfauthor={},
        pdfcreator={LaTeX},
        colorlinks=true,
        urlcolor=primaryColor
    ]{hyperref}
    \usepackage{paracol}
    \usepackage{changepage}
    \usepackage{ifthen}
    \usepackage{needspace}
    \usepackage{lastpage}
    \usepackage{bookmark}

    % Ensure ATS readability
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}

    \usepackage[default]{sourcesanspro} % clean sans-serif font


    % ========== Styling ==========
    \pagestyle{empty}
    \setcounter{secnumdepth}{0}
    \setlength{\parindent}{0pt}
    \setlength{\columnsep}{0.15cm}

    \titleformat{\section}{
        \needspace{4\baselineskip}
        \Large\color{primaryColor}
    }{}{
    }{
        \textbf{#1}\hspace{0.15cm}\titlerule[0.8pt]\hspace{-0.1cm}
    }[]

    \titlespacing{\section}{-1pt}{0.3cm}{0.2cm}

    \newenvironment{highlights}{
        \begin{itemize}[
            topsep=0.10cm,
            parsep=0.10cm,
            itemsep=0pt,
            leftmargin=0.5cm
        ]
    }{
        \end{itemize}
    }

    \newenvironment{onecolentry}{
        \begin{adjustwidth}{0.2cm}{0.2cm}
    }{
        \end{adjustwidth}
    }

    \newenvironment{twocolentry}[2][]{
        \onecolentry
        \def\secondColumn{#2}
        \setcolumnwidth{\fill, 4.5cm}
        \begin{paracol}{2}
    }{
        \switchcolumn \raggedleft \secondColumn
        \end{paracol}
        \endonecolentry
    }

    % ========== Document ==========
    \begin{document}

    % ---------- Header ----------
    \begin{center}
        {\fontsize{28pt}{30pt}\selectfont \textbf{Navn}} \\[12pt]
        \small
        \faBirthdayCake \ Fødselsdato \quad | \quad
        \faEnvelope[regular] \ Epost \quad | \quad
        \faPhone* \ Telefonnummer \quad | \quad
        \faMapMarker* \ Adresse
    \end{center}

    \vspace{0.8cm}


    % ---------- Summary ----------
    \section{Sammendrag}
    \begin{onecolentry}
    Sammendrag\_tekst
    \end{onecolentry}

    % ---------- Education ----------
    \section{Utdanning}
    \begin{twocolentry}{Trinn/Ferdig\_år}
        \textbf{Grad} – Skole
        \begin{highlights}
            \item Ytterligere\_informasjon
        \end{highlights}
    \end{twocolentry}

    % ---------- Experience ----------
    \section{Arbeidserfaring}
    \subsection*{Stillinger}
    \begin{twocolentry}{Periode}
        \textbf{Tittel}, Firma
        \begin{highlights}
            \item Beskrivelse
        \end{highlights}
    \end{twocolentry}

    \vspace{0.3cm}

    \subsection*{Dugnad}
    \begin{twocolentry}{Periode}
        \textbf{Oppdrag}
        \begin{highlights}
            \item Beskrivelse
        \end{highlights}
    \end{twocolentry}

    % ---------- Skills ----------
    \section{Ferdigheter}
    \begin{onecolentry}
        \textbf{Ferdigheter og kompetanser:}
        \begin{highlights}
            \item Ferdighet (Nivå): Beskrivelse
        \end{highlights}
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Språk:} Språk (Nivå)
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Sertifikater:} \\
        Sertifikater
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Annet:} \\
        Annet
    \end{onecolentry}

    % ---------- Interests ----------
    \section{Interesser og hobbyer}
    \begin{onecolentry}
        \textbf{Interesse/Hobby} – Beskrivelse
    \end{onecolentry}

    % ---------- Future Goals ----------
    \section{Fremtidige mål}
    \begin{onecolentry}
        \textbf{Fremtidsutsikter og mål:} Fremtidsutsikter\_og\_mål
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Jobbønsker:}
        \begin{highlights}
            \item Jobbønske – Begrunnelse
        \end{highlights}
    \end{onecolentry}

    \end{document}
""")

INSTRUCTIONS = textwrap.dedent("""
    - Du er en hjelpfull AI assistent som skal samle informasjon fra brukeren som er nødvendig for å generere en god CV.
    - Du vil få ekstra informasjon gitt inni tagger som dette
      <foo></foo>.
    - Bruk context og historikk for å gi en kort sammenhengende respons og nytt spørsmål for å samle gjenstående manglende informasjon eller utdyping.
    - Bruk markdown.
    - Anta at brukeren er nybegynner.
    - Vær klar og presis. Unngå lange svar. Still spørsmål som krever svar på maksimalt ett avsnitt. Hvis du trenger mer informasjon, still et nytt spørsmål.
    - Dersom du trenger ett ords informasjon som navn, epost, telefonnummer osv. lag en liste med rimelig antall punkter.
    - Minimer cognitive load. Still et spørsmål av gangen dersom det krever setninger fra brukeren.
    - Tilpass spørsmålene dine basert på tidligere svar og hva du lærer om brukeren (f.eks. alder vil være veldig relevant for en ung søker).
    - Gi eksempler tilpasset brukeren.
    - Still spørsmål i en logisk rekkefølge (f.eks. personalia først, deretter utdanning, arbeidserfaring, ferdigheter, interesser og fremtidige mål).
""")

# Instruct a second LLM to analyze the response and output data for the CV in JSON format.
INSTRUCTIONS_GENERATE_DATA_FROM_RESPONSE = textwrap.dedent("""
    - Du er en hjelpfull AI assistent som skal trekke ut informasjon fra en samtale med en bruker for å generere en JSON strukturert datafil som kan brukes til å lage en god CV.
    - Du vil få spørsmål fra assistenten og svar fra brukeren, og ditt mål er å trekke ut relevant informasjon og forstå hvilke spørsmål infromasjonen svarer på.
    - Du skal returnere elementer i en JSON struktur som følger denne malen:
        {
            "Personalia": {
                "Navn": "",
                "Fødselsdato": "",
                "Epost": "",
                "Telefonnummer": "",
                "Adresse": ""
            },
            "Utdanning": [
                {
                    "Grad": "",
                    "Trinn/Ferdig_år": "",
                    "Skole": "",
                    "Ytterligere_informasjon": ""
                }
            ],
            "Arbeidserfaring": {
                "Stillinger": [
                    {
                        "Tittel": "",
                        "Firma": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }
                ],
                "Dugnad": [
                    {
                        "Oppdrag": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }
                ]
            },
            "Ferdigheter": {
                "Ferdigheter_og_kompetanser": [
                    {
                        "Ferdighet": "",
                        "Nivå": "",
                        "Beskrivelse": ""
                    }
                ],
                "Språk": [
                    {
                        "Språk": "",
                        "Nivå": ""
                    }
                ],
                "Sertifikater": [],
                "Annet": []
            },
            "Interesser_og_hobbyer": [
                {
                    "Interesse/Hobby": "",
                    "Beskrivelse": ""
                }
            ],
            "Fremtidige_mål": {
                "Fremtidsutsikter_og_mål": "",
                "Jobbønsker": [
                    {
                        "Jobbønske": "",
                        "Begrunnelse": ""
                    }
                ]
            }
        }
    - Returner KUN informasjonen brukeren nettopp ga (ikke informasjon fra samtale historien) f.ks.: "Personalia": {"Navn": "Ola Nordmann", "Fødseldato": "01.01.2000"}
    - Ellers legg til ny informasjon i lister (f.eks. utdanning, arbeidserfaring, ferdigheter osv.).
    - Dersom du ikke har fått informasjon om et felt, la det være tomt.
""")

SUGGESTIONS = {
    ":blue[:material/local_library:] Hjelp til å generere en proffesjonell clean CV": (
        ""
    ),
    ":orange[:material/call:] AI assistert jobb intervju": (
        ""
    ),
    ":green[:material/database:] Lag et skreddersydd søknadsbrev": (
        ""
    ),
    ":red[:material/multiline_chart:] Foreslå jobbalternativer": (
        ""
    ),
}


def build_prompt(**kwargs):
    """Builds a prompt string with the kwargs as HTML-like tags.

    For example, this:

        build_prompt(foo="1\n2\n3", bar="4\n5\n6")

    ...returns:

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


# Just some little objects to make tasks more readable.
TaskInfo = namedtuple("TaskInfo", ["name", "function", "args"])
TaskResult = namedtuple("TaskResult", ["name", "result"])


def build_question_prompt(question, JSON_GENERATOR=False):
    """Fetches info from different services and creates the prompt string."""
    old_history = st.session_state.messages[:-HISTORY_LENGTH]
    recent_history = st.session_state.messages[-HISTORY_LENGTH:]

    if recent_history:
        recent_history_str = history_to_text(recent_history)
    else:
        recent_history_str = None

    # Fetch information from different services in parallel.
    task_infos = []

    if SUMMARIZE_OLD_HISTORY and old_history:
        task_infos.append(
            TaskInfo(
                name="old_message_summary",
                function=generate_chat_summary,
                args=(old_history,),
            )
        )

    results = executor.map(
        lambda task_info: TaskResult(
            name=task_info.name,
            result=task_info.function(*task_info.args),
        ),
        task_infos,
    )

    context = {name: result for name, result in results}

    return build_prompt(
        instructions=INSTRUCTIONS if not JSON_GENERATOR else INSTRUCTIONS_GENERATE_DATA_FROM_RESPONSE,
        **context,
        recent_messages=recent_history_str,
        question=question,
    )


def generate_chat_summary(messages):
    """
    Summarize a conversation history using the OpenAI API.

    Args:
        messages (list[dict]): Chat history, where each entry has
            {"role": "user"|"Assistant", "content": str}.

    Returns:
        str: A concise summary of the conversation.
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

def history_to_text(chat_history):
    """Converts chat history into a string."""
    return "\n".join(f"[{h['role']}]: {h['content']}" for h in chat_history)


def get_response(prompt):
    """
    Stream a response from the OpenAI API for a given prompt.

    Args:
        prompt (str): The user prompt or full conversation context.

    Yields:
        str: Chunks of the model’s generated text streamed as they arrive.
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
#   return complete(
#       MODEL,
#       prompt,
#       stream=True,
#       session=get_session(),
#   )
#

def deep_update(original, new_data):
    """
    Recursively update a nested dict or list with new values.
    Dicts are merged, lists are updated element by element.
    """
    if isinstance(original, dict) and isinstance(new_data, dict):
        for k, v in new_data.items():
            if k in original:
                original[k] = deep_update(original[k], v)
            else:
                original[k] = v
        return original

    elif isinstance(original, list) and isinstance(new_data, list):
        # Update existing items by index
        for i, v in enumerate(new_data):
            print("new data item:")
            print(i)
            print(new_data)

            #Catch primitive types in lists
            if isinstance(v, (str, int, float)) or v is None:
                print("primitive in list")
                if v not in original:
                    original.append(v)
                continue

            for key, value in v.items():
                if key in original[-1] and original[-1][key] == "" or original[-1][key] == value:
                    original[-1] = deep_update(original[-1], v)
                elif key not in original[-1]:
                    original[-1][key] = v[key]
                else:
                    original.append(new_data[i])
                    print("appending")
                    print(new_data[i])
        return original

    else:
        # Primitive (str, int, etc.) → overwrite
        return new_data

def save_JSONstr_to_dict(json_str):
    """Saves LLM json string output to predefined dictionary storing CV data."""
    if "CV_dict" not in st.session_state:

        st.session_state.CV_dict = {
            "Personalia": {
                "Navn": "",
                "Fødselsdato": "",
                "Epost": "",
                "Telefonnummer": "",
                "Adresse": ""
            },
            "Utdanning": [
                {
                    "Grad": "",
                    "Trinn/Ferdig_år": "",
                    "Skole": "",
                    "Ytterligere_informasjon": ""
                }
            ],
            "Arbeidserfaring": {
                "Stillinger": [
                    {
                        "Tittel": "",
                        "Firma": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }
                ],
                "Dugnad": [
                    {
                        "Oppdrag": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }
                ]
            },
            "Ferdigheter": {
                "Ferdigheter_og_kompetanser": [
                    {
                        "Ferdighet": "",
                        "Nivå": "",
                        "Beskrivelse": ""
                    }
                ],
                "Språk": [
                    {
                        "Språk": "",
                        "Nivå": ""
                    }
                ],
                "Sertifikater": [],
                "Annet": []
            },
            "Interesser_og_hobbyer": [
                {
                    "Interesse/Hobby": "",
                    "Beskrivelse": ""
                }
            ],
            "Fremtidige_mål": {
                "Fremtidsutsikter_og_mål": "",
                "Jobbønsker": [
                    {
                        "Jobbønske": "",
                        "Begrunnelse": ""
                    }
                ]
            }
        }
    try:
        data_dict = json.loads(json_str)
        st.session_state.CV_dict = deep_update(st.session_state.CV_dict, data_dict)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

def json_to_CVpdf():
    """Generates a CV PDF from the JSON data."""
    if "CV_dict" in st.session_state:
        promt = textwrap.dedent(f""" 
            - Lag en proffesjonell CV i latex format basert på JSON data.
            - Bruk informasjon som alder og erfaringer til å tilpasse CVen.
            - JSON data: {st.session_state.CV_dict}
            - Bruk denne latex malen: {LATEX_TEMPLATE}
            """)

        latex_response_gen = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a LaTeX generator."},
                {"role": "user", "content": promt}
            ],
        )
        latex_CVcode = latex_response_gen.choices[0].message.content

        # Save to file named with user's name and day of birth
        #try:
        #extract_personalia_from_json(json.dumps(st.session_state.CV_dict))
        #filename = base64.urlsafe_b64encode(f"{st.session_state.personalia_name}_{st.session_state.personalia_dob}".encode()).decode() + ".tex"
        #st.write(filename)
        #print(filename)
        filename = "CV.tex"
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(latex_CVcode)
        # Compile to PDF using pdflatex
        subprocess.run(["pdflatex", "-interaction=nonstopmode", filename])
        st.session_state.is_pdf_ready = True
        #except:
        #    st.write("Kunne ikke hente personalia. Vennligst skriv inn navn og fødselsdato (DD.MM.ÅÅ) på nytt.")
        #    return
    else: 
        st.write("Ingen data fra brukeren funnet.")

def generator_to_string(gen):
    """Converts a generator (such as openai stream) to a string."""
    return "".join(chunk for chunk in gen if isinstance(chunk, str))

def extract_personalia_from_json(json_str):
    """Extracts name and date of birth from JSON string and saves to session state."""
    personalia_dict = json.loads(json_str)
    st.session_state.personalia_name = personalia_dict["Personalia"]["Navn"]
    st.session_state.personalia_dob = personalia_dict["Personalia"]["Fødselsdato"]
    # If name and dob not given, or empty, ask again.
    if st.session_state.personalia_name == "" or st.session_state.personalia_dob == "":
        raise ValueError("Name or date of birth is empty.")

def send_telemetry(**kwargs):
    """Records some telemetry about questions being asked."""
    # TODO: Implement this.
    pass


def show_feedback_controls(message_index):
    """Shows the "How did I do?" control."""
    st.write("")

    with st.popover("How did I do?"):
        with st.form(key=f"feedback-{message_index}", border=False):
            with st.container(gap=None):
                st.markdown(":small[Rating]")
                rating = st.feedback(options="stars")

            details = st.text_area("More information (optional)")

            if st.checkbox("Include chat history with my feedback", True):
                relevant_history = st.session_state.messages[:message_index]
            else:
                relevant_history = []

            ""  # Add some space

            if st.form_submit_button("Send feedback"):
                # TODO: Submit feedback here!
                pass


@st.dialog("Legal disclaimer")
def show_disclaimer_dialog():
    st.caption("""
            This AI chatbot is powered by OpenAI. Answers may be inaccurate, inefficient, or biased.
            Any use or decisions based on such answers should include reasonable
            practices including human oversight to ensure they are safe,
            accurate, and suitable for your intended purpose. Streamlit is not
            liable for any actions, losses, or damages resulting from the use
            of the chatbot. Do not enter any private, sensitive, personal, or
            regulated data. By using this chatbot, you acknowledge and agree
            that input you provide and answers you receive (collectively,
            “Content”) may be used by Snowflake to provide, maintain, develop,
            and improve their respective offerings. For more
            information on how Snowflake may use your Content, see
            https://streamlit.io/terms-of-service.
        """)


# -----------------------------------------------------------------------------
# Draw the UI.


st.html(div(style=styles(font_size=rem(5), line_height=1))["❉"])

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom",
)

with title_row:
    st.title(
        "Ungt Steg AI assistent",
        anchor=False,
        width="stretch",
    )

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


# Show a different UI when the user hasn't asked a question yet.
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

# Show chat input at the bottom when a question has been asked.
user_message = st.chat_input("Ask a follow-up...")



if not user_message:
    st.session_state.json_response = "{}"  # Initialize empty JSON response
    if user_just_asked_initial_question:
        user_message = st.session_state.initial_question
        st.session_state.CV_mode = False
    if user_just_clicked_suggestion:
        #user_message = SUGGESTIONS[st.session_state.selected_suggestion]
        st.session_state.CV_mode = True
        st.session_state.CV_uploaded = False

        # Initial quesstion from the chatbot
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Hei! Jeg er her for å hjelpe deg med å lage en CV. "
                        "For å komme i gang, skriv ditt fulle navn og fødselsdato (DD.MM.ÅÅ)"
                ),
            }
        )
        st.session_state.initial_CV_questions = True


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

if "prev_question_timestamp" not in st.session_state:
    st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

# PDF uploader
uploaded_cv = st.file_uploader("Last opp eksisterende CV (pdf)", type=["pdf"])

# Display chat messages from history as speech bubbles.
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "pdf_uploaded":
        continue
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.container()  # Fix ghost message bug.

        if not st.session_state.initial_stream_done:
            def generator_initial_question(text, delay=0.01):
                for ch in text:
                    yield ch
                    time.sleep(delay)
                # Streaming done boolean
                st.session_state.initial_stream_done = True

            response = st.write_stream(generator_initial_question(st.session_state.messages[-1]["content"]))
            continue

        st.markdown(message["content"])
        #if message["role"] == "assistant":
        #    show_feedback_controls(i)

# If a CV has been uploaded, extract text and use LLM to parse it.
if uploaded_cv is not None and not st.session_state.CV_uploaded:
    import pymupdf
    pdf_text = ""
    with pymupdf.open(stream=uploaded_cv.read(), filetype="pdf") as doc:
        for page in doc:
            pdf_text += page.get_text()

    # Use LLM to extract relevant info from the CV text.
    extraction_prompt = textwrap.dedent(f"""
        - Trekk ut relevant informasjon fra denne CVen og strukturer den i JSON format.
        - CV tekst: {pdf_text}
        - Returner informasjonen i JSON format etter denne malen:
        {{
            "Personalia": {{
                "Navn": "",
                "Fødselsdato": "",
                "Epost": "",
                "Telefonnummer": "",
                "Adresse": ""
            }},
            "Utdanning": [
                {{
                    "Grad": "",
                    "Trinn/Ferdig_år": "",
                    "Skole": "",
                    "Ytterligere_informasjon": ""
                }}
            ],
            "Arbeidserfaring": {{
                "Stillinger": [
                    {{
                        "Tittel": "",
                        "Firma": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }}
                ],
                "Dugnad": [
                    {{
                        "Oppdrag": "",
                        "Periode": "",
                        "Beskrivelse": ""
                    }}
                ]
            }},
            "Ferdigheter": {{
                "Ferdigheter_og_kompetanser": [
                    {{
                        "Ferdighet": "",
                        "Nivå": "",
                        "Beskrivelse": ""
                    }}
                ],
                "Språk": [
                    {{
                        "Språk": "",
                        "Nivå": ""
                    }}
                ],
                "Sertifikater": [],
                "Annet": []
            }},
            "Interesser_og_hobbyer": [
                {{
                    "Interesse/Hobby": "",
                    "Beskrivelse": ""
                }}
            ],
            "Fremtidige_mål": {{
                "Fremtidsutsikter_og_mål": "",
                "Jobbønsker": [
                    {{
                        "Jobbønske": "",
                        "Begrunnelse": ""
                    }}
                ]
            }}
        }}
        """)
    with st.spinner("Leser og tolker CV..."):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a CV data extractor."},
                {"role": "user", "content": extraction_prompt}
            ],
        )
    try:
        json_data = response.choices[0].message.content
        st.session_state.CV_dict = json.loads(json_data)
        st.success("CV data lastet inn!")
        # Get next question from the assistant based on the extracted data.
        st.session_state.messages.append(
                {
                    "role": "pdf_uploaded",
                    "content": f"Bruker har lastet opp en CV med følgende informasjon: {json_data}. Bekreft at du har mottatt informasjonen og still et nytt spørsmål for å samle mer eller manglende informasjon",
                }
        )
        user_message = st.session_state.messages[-1]["content"]
        with st.spinner("Analyserer CV..."):
            full_prompt = build_question_prompt(st.session_state.messages[-1]["content"])
            response_gen = get_response(full_prompt)
            response = generator_to_string(response_gen)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.CV_uploaded = True # Prevent re-processing the same CV


    except json.JSONDecodeError as e:
        st.write("Kunne ikke tolke CVen. Vennligst prøv en annen CV.")




if user_message:
    # When the user posts a message...

    st.session_state.generate_CV_button_clicked = False
    # Streamlit's Markdown engine interprets "$" as LaTeX code (used to
    # display math). The line below fixes it.
    user_message = user_message.replace("$", r"\$")

    # Display message as a speech bubble.
    with st.chat_message("user"):
        st.text(user_message)

    # Display assistant response as a speech bubble.
    with st.chat_message("assistant"):
        with st.spinner("Waiting..."):
            # Rate-limit the input if needed.
            question_timestamp = datetime.datetime.now()
            time_diff = question_timestamp - st.session_state.prev_question_timestamp
            st.session_state.prev_question_timestamp = question_timestamp

            if time_diff < MIN_TIME_BETWEEN_REQUESTS:
                time.sleep(time_diff.seconds + time_diff.microseconds * 0.001)

            user_message = user_message.replace("'", "")

        # Build a detailed prompt.
        if DEBUG_MODE:
            with st.status("Computing prompt...") as status:
                full_prompt = build_question_prompt(user_message)
                st.code(full_prompt)
                status.update(label="Prompt computed")
        else:
            with st.spinner("Researching..."):
                full_prompt = build_question_prompt(user_message)

        # Send prompt to LLM.
        with st.spinner("Thinking..."):
            response_gen = get_response(full_prompt)

        # Put everything after the spinners in a container to fix the
        # ghost message bug.
        with st.container():
            # Stream the LLM response.
            response = st.write_stream(response_gen)

            # Add messages to chat history.
            st.session_state.messages.append({"role": "user", "content": user_message})
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Get the previous user and assistant message.
            if st.session_state.CV_mode and len(st.session_state.messages) > 1: # Length 1 means only the initial question from the assistant
                assistant_question = st.session_state.messages[-3]["content"] # The last message is the question from the assistant yet to be answered
                user_answer = st.session_state.messages[-2]["content"]
                json_prompt = build_question_prompt(f"Spørsmål: {assistant_question}\nSvar: {user_answer}", JSON_GENERATOR=True)
                json_response_gen = get_response(json_prompt)
                json_str = generator_to_string(json_response_gen)

                # Save personalia name and dob (from initial question) to session state.
                if st.session_state.initial_CV_questions:
                    try:
                        extract_personalia_from_json(json_str)
                        st.session_state.initial_CV_questions = False
                    except:
                        st.write("\nKunne ikke hente personalia. Vennligst skriv inn navn og fødselsdato (DD.MM.ÅÅ) på nytt.")
                        st.session_state.initial_CV_questions = True

                save_JSONstr_to_dict(json_str)

if "CV_dict" in st.session_state:
    if st.button("Generer CV", key="generate_CV_button"):
        with st.spinner("Genererer CV..."):
            json_to_CVpdf()
            try:
                with open("CV.pdf", "rb") as f:
                    st.session_state["CV_pdf"] = f.read()
            except FileNotFoundError as e:
                st.write(e)
                st.write("PDF ikke funnet. Vennligst prøv å generere CVen på nytt.")

    if "CV_pdf" in st.session_state:
        st.download_button(
            type="primary",
            label="Last ned pdf",
            data=st.session_state["CV_pdf"],
            file_name="CV.pdf",
            mime='application/pdf'
        )

            #TODO: Create genereate CV button



            # Other stuff.
            #show_feedback_controls(len(st.session_state.messages) - 1)
            #send_telemetry(question=user_message, response=response)

