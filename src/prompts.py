"""Prompt generation and instructions for LLM interactions."""

import textwrap

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


def get_instructions(session_state):
    """Generate dynamic instructions based on current session state.

    Args:
        session_state: Streamlit session state object

    Returns:
        str: Dynamic instructions for the conversational assistant
    """
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
    - IKKE svar med informajonen du nettopp fikk fra brukeren. Bare bekreft mottakelsen kort og still neste spørsmål.
    - Still spørsmål i en logisk rekkefølge (f.eks. personalia først, deretter utdanning, arbeidserfaring, ferdigheter, interesser og fremtidige mål).
    - Data samlet inn så langt:
    {cv_dict}
    Data/instruks bruker nettop oppga: {user_message}
    - Dersom alle nødvendige data er samlet inn, bekreft dette og si at brukeren kan trykke på knappen 'Generer CV' for å lage en proffesjonell CV i pdf format.
    """)
