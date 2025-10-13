# CV Generator - AI-Powered Resume Builder

An AI-powered CV (resume) generator built with Streamlit and OpenAI. This application uses conversational AI to collect information from users in Norwegian and generates professional CVs in PDF format using LaTeX.

## Features

- **Conversational Data Collection**: Interactive AI assistant that asks questions in Norwegian to gather CV information
- **Smart Data Extraction**: Dual LLM pipeline that extracts structured data from conversations
- **PDF Upload**: Can parse existing CVs (PDF format) to pre-populate data
- **Professional PDF Generation**: Creates clean, ATS-friendly CVs using LaTeX templates
- **Norwegian Language**: All interactions and CV output in Norwegian (bokmål)

## Project Structure

```
demo-ai-assistant/
├── streamlit_app.py          # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration, constants, and CV schema
│   ├── llm_client.py         # OpenAI client and LLM interaction functions
│   ├── cv_generator.py       # PDF/LaTeX generation logic
│   └── data_utils.py         # Data processing and PDF parsing utilities
├── .streamlit/
│   ├── config.toml           # Streamlit theme configuration
│   └── secrets.toml          # API keys (not in git)
└── pyproject.toml            # Python dependencies
```

## Running it yourself

### Prerequisites

- Python 3.12+
- `pdflatex` (for PDF generation)
  - On Ubuntu/Debian: `sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-latex-extra`
  - On macOS: `brew install --cask mactex-no-gui`
  - On Windows: Install [MiKTeX](https://miktex.org/)
- OpenAI API key

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/streamlit/demo-ai-assistant
   cd demo-ai-assistant
   ```

2. Create a virtual environment and install dependencies:
   ```sh
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync

   # Or using pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. Configure your OpenAI API key in `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key-here"
   ```

4. Run the application:
   ```sh
   # Make sure to activate the virtual environment first
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Then run the app
   streamlit run streamlit_app.py
   ```

## How It Works

1. **User Interaction**: The application presents a conversational interface where users can either:
   - Upload an existing CV (PDF) for parsing
   - Start from scratch by providing basic information

2. **Data Collection**: The AI assistant asks targeted questions to gather:
   - Personal information (Personalia)
   - Education (Utdanning)
   - Work experience (Arbeidserfaring)
   - Skills and competencies (Ferdigheter)
   - Interests and hobbies (Interesser og hobbyer)
   - Future goals (Fremtidige mål)

3. **Data Extraction**: A second LLM analyzes each conversation turn and extracts structured JSON data that matches the CV schema

4. **CV Generation**: When data collection is complete, the application:
   - Uses an LLM to clean and optimize the CV data
   - Generates LaTeX code from a professional template
   - Compiles the LaTeX to PDF using `pdflatex`

5. **Download**: Users can download their generated CV as a PDF

## Configuration

### Debug Mode

Enable debug mode to see the prompts being sent to the LLM:
```
http://localhost:8501/?debug=true
```

### Customization

- **CV Template**: Edit the `LATEX_TEMPLATE` in `src/config.py`
- **Questions/Prompts**: Modify `get_instructions()` in `src/config.py`
- **Model**: Change `MODEL` constant in `src/config.py` (default: `gpt-4.1`)
- **Rate Limiting**: Adjust `MIN_TIME_BETWEEN_REQUESTS` in `src/config.py`

## License

Copyright 2025 Snowflake Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
