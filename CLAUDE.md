# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Norwegian CV (resume) generator application built with Streamlit and OpenAI. The app collects user information through an AI-driven conversational interface in Norwegian and generates professional CVs in PDF format using LaTeX.

## Architecture

The codebase has been refactored into a modular structure:

### Module Structure

- **`src/config.py`** - Configuration, constants, and CV data schema
  - `CV_SCHEMA`: Defines the nested structure for all CV data
  - `LATEX_TEMPLATE`: Professional Norwegian CV LaTeX template
  - `get_instructions()`: Dynamic prompt generation based on session state
  - Model settings, rate limits, and UI configuration

- **`src/llm_client.py`** - OpenAI client and LLM interaction functions
  - `get_openai_client()`: Initialize OpenAI client
  - `build_question_prompt()`: Creates prompts for conversational assistant
  - `get_response()`: Streams LLM responses
  - `generator_to_string()`: Converts streaming responses to strings

- **`src/cv_generator.py`** - PDF/LaTeX and Word document generation
  - `json_to_cv_pdf()`: Generates PDF via LaTeX compilation
  - `generate_word_docx()`: Creates Word documents (optional, uses lazy imports)

- **`src/data_utils.py`** - Data processing and PDF parsing
  - `deep_update()`: Recursively merges new CV data into existing structure
  - `save_json_str_to_dict()`: Parses LLM JSON responses and updates session state
  - `extract_cv_from_pdf()`: Uses PyMuPDF and LLM to parse uploaded CVs

- **`streamlit_app.py`** - Main application entry point
  - UI layout and interaction flow
  - Chat interface management
  - Session state handling

### Main Application Flow

1. **User Interaction** - User clicks "Generate CV" suggestion or asks questions
2. **Conversational Data Collection** - Assistant asks structured questions in Norwegian
3. **Dual LLM Pipeline**:
   - **Primary LLM**: Generates conversational responses and follow-up questions
   - **Data Extraction LLM**: Parses user responses into structured JSON matching CV schema
4. **Data Aggregation** - `deep_update()` merges incremental JSON updates into session state
5. **CV Generation** - LLM generates LaTeX code from JSON, then compiles with pdflatex

## Development Commands

### Running the Application

**IMPORTANT:** Always activate the virtual environment before running:

```sh
# Activate the virtual environment first
source .venv/bin/activate

# Then run the app
streamlit run streamlit_app.py
```

Or in one command:
```sh
source .venv/bin/activate && streamlit run streamlit_app.py
```

### Testing Module Imports

```sh
python -c "from src.config import CV_SCHEMA; from src.llm_client import get_openai_client; print('Imports OK')"
```

## Configuration

### Required Secrets

Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-key-here"
```

### Model Configuration

- Model: GPT-4.1 (defined as `MODEL` in `src/config.py`)
- Debug mode: Add `?debug=true` query parameter to URL

## Important Implementation Details

### Session State Management

All CV data is stored in `st.session_state.CV_dict` following the schema defined in `src/config.py`. Key session state variables:
- `messages`: Chat history
- `CV_dict`: Accumulated CV data
- `CV_mode`: Boolean for CV generation mode
- `CV_uploaded`: Boolean tracking if PDF was uploaded
- `initial_CV_questions`: Boolean for first-time personalia collection

### List Management in deep_update()

The `deep_update()` function in `src/data_utils.py` has complex logic for merging list items. It attempts to detect whether to update existing list items or append new ones by comparing keys and values. This can have edge cases when dealing with similar entries.

### PDF Generation Dependencies

The `json_to_cv_pdf()` function requires:
1. System installation of `pdflatex` and LaTeX packages (geometry, titlesec, fontawesome5, etc.)
2. Write permissions in working directory for intermediate .tex and .pdf files
3. The function creates `CV.tex` and `CV.pdf` files in the current directory

### Lazy Imports

`generate_word_docx()` uses lazy imports for the `docx` library to avoid requiring it unless Word generation is explicitly used.

## Language

All user-facing content, prompts, and CV output are in **Norwegian** (bokmål). System instructions to LLMs are also in Norwegian.

## Testing

To test the application without full deployment:
1. Ensure all dependencies are installed: `uv sync` or `pip install -e .`
2. Verify pdflatex is available: `which pdflatex`
3. Check imports: `python -m py_compile streamlit_app.py`
4. Run with debug mode: `streamlit run streamlit_app.py` then navigate to `?debug=true`
