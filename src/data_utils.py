"""Data processing utilities for CV data management."""

import json
import textwrap
import pymupdf

from src.config import CV_SCHEMA


def deep_update(original, new_data):
    """
    Recursively update a nested dict or list with new values.
    Dicts are merged, lists are updated element by element.

    Args:
        original: Original data structure (dict or list)
        new_data: New data to merge in

    Returns:
        Updated data structure
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

            # Catch primitive types in lists
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


def save_json_str_to_dict(session_state, json_str):
    """Saves LLM json string output to predefined dictionary storing CV data.

    Args:
        session_state: Streamlit session state
        json_str: JSON string from LLM
    """
    if "CV_dict" not in session_state:
        session_state.CV_dict = CV_SCHEMA.copy()

    try:
        data_dict = json.loads(json_str)
        session_state.CV_dict = deep_update(session_state.CV_dict, data_dict)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


def extract_personalia_from_json(json_str):
    """Extracts name and date of birth from JSON string.

    Args:
        json_str: JSON string containing personalia

    Returns:
        tuple: (name, date_of_birth)

    Raises:
        ValueError: If name or DOB is empty
    """
    personalia_dict = json.loads(json_str)
    name = personalia_dict["Personalia"]["Navn"]
    dob = personalia_dict["Personalia"]["Fødselsdato"]

    # If name and dob not given, or empty, raise error
    if name == "" or dob == "":
        raise ValueError("Name or date of birth is empty.")

    return name, dob


def extract_cv_from_pdf(client, uploaded_file):
    """Extract CV data from uploaded PDF file.

    Args:
        client: OpenAI client instance
        uploaded_file: Streamlit uploaded file object

    Returns:
        dict: Extracted CV data in JSON format, or None if extraction fails
    """
    from src.config import MODEL

    # Extract text from PDF
    pdf_text = ""
    with pymupdf.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            pdf_text += page.get_text()

    # Use LLM to extract relevant info from the CV text
    extraction_prompt = textwrap.dedent(f"""
        - Trekk ut relevant informasjon fra denne CVen og strukturer den i JSON format.
        - CV tekst: {pdf_text}
        - Returner informasjonen i JSON format etter denne malen:
        {json.dumps(CV_SCHEMA, indent=2, ensure_ascii=False)}
        """)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a CV data extractor."},
            {"role": "user", "content": extraction_prompt}
        ],
    )

    try:
        json_data = response.choices[0].message.content
        cv_dict = json.loads(json_data)
        return cv_dict
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from PDF extraction: {e}")
        return None
