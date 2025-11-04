"""CV data schema definitions."""

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
    },
    "Referanser": [
        {
            "Navn": "",
            "Stilling": "",
            "Firma": "",
            "Kontaktinformasjon": ""
        }
    ]
}
