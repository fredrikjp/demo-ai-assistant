"""Configuration and constants for the CV Generator application."""

import datetime

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

# Output directory for generated files
OUTPUT_DIR = "outputs"
