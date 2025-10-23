"""Configuration and constants for the CV Generator application."""

import datetime
import textwrap

# Model Configuration
MODEL = "gpt-4.1"

# Application Settings
HISTORY_LENGTH = 5
SUMMARIZE_OLD_HISTORY = True
MIN_TIME_BETWEEN_REQUESTS = datetime.timedelta(seconds=3)

# UI Configuration
GITHUB_URL = "https://github.com/streamlit/streamlit-assistant"

# Suggestions for the initial screen
SUGGESTIONS = {
    ":blue[:material/local_library:] Hjelp til å generere en proffesjonell clean CV": "",
    ":orange[:material/call:] AI assistert jobb intervju (kommer snart!)": "",
    ":green[:material/database:] Lag et skreddersydd søknadsbrev (kommer snart!)": "",
    ":red[:material/multiline_chart:] Foreslå jobbalternativer (kommer snart!)": "",
}

# CV Data Schema
CV_SCHEMA = {
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

# LaTeX Template for CV Generation
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


def get_instructions(session_state):
    """Generate dynamic instructions based on current session state."""
    cv_dict = session_state.get('CV_dict', {})
    user_message = session_state.get('user_message', {})

    return textwrap.dedent(f"""
    - Du er en hjelpfull AI assistent som skal samle informasjon fra brukeren som er nødvendig for å generere en god CV.
    - Du vil få ekstra informasjon gitt inni tagger som dette
      <foo></foo>.
    - Bruk context og historikk for å gi en KORT sammenhengende respons og nytt spørsmål for å samle gjenstående manglende informasjon eller utdyping.
    - Bruk markdown.
    - Anta at brukeren er nybegynner.
    - Vær klar og presis. Unngå lange svar. Still spørsmål som krever svar på maksimalt ett avsnitt. Hvis du trenger mer informasjon, still et nytt spørsmål.
    - Dersom du trenger ett ords informasjon som navn, epost, telefonnummer osv. lag en liste med rimelig antall punkter.
    - Minimer cognitive load. Still ETT spørsmål av gangen dersom det krever potensielt setninger/flere data punkter fra brukeren (f.eks språk, dugnadserfaring og sertifikater).
    - Ta alltid en av gangen dersom brukeren muligens har flere instanser av data som blir forespurt (f.eks Utdanninger).
    - Tilpass spørsmålene dine basert på tidligere svar og hva du lærer om brukeren (f.eks. alder vil være veldig relevant for en ung søker).
    - IKKE inkluder eksempler i ditt svar. Eksempler vil bli generert automatisk og vist separat.
    - Bruk bullet points hvis mulig for å minimere antall ord og kognitiv belastning.
    - Still spørsmål i en logisk rekkefølge (f.eks. personalia først, deretter utdanning, arbeidserfaring, ferdigheter, interesser og fremtidige mål).
    - Data samlet inn så langt:
    {cv_dict}
    Data/instruks bruker nettop oppga: {user_message}
    - Dersom alle nødvendige data er samlet inn, bekreft dette og si at brukeren kan trykke på knappen 'Generer CV' for å lage en proffesjonell CV i pdf format.
    """)


# Instructions for JSON data extraction from conversation
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
