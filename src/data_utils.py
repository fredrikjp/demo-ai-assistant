"""Data processing utilities for CV data management."""

import json
import textwrap
import pymupdf

from src.schemas import CV_SCHEMA


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

            # If original list is empty, just append the new item
            if len(original) == 0:
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


def parse_examples_to_list(examples_markdown):
    """Parse markdown bullet points into a list of example strings.

    Args:
        examples_markdown: String containing markdown bullet points (e.g., "- Item 1\n- Item 2")

    Returns:
        list: List of example strings without the "- " prefix
    """
    if not examples_markdown:
        return []

    lines = examples_markdown.strip().split('\n')
    examples = []
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            examples.append(line[2:].strip())
        elif line.startswith('* '):
            examples.append(line[2:].strip())

    return examples


def calculate_cv_completion(cv_dict):
    """Calculate completion percentage of CV data.

    Args:
        cv_dict: Current CV data dictionary

    Returns:
        float: Completion percentage (0.0 to 1.0)
    """
    def count_fields(data, is_required=True):
        """Recursively count total and filled fields."""
        total = 0
        filled = 0

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    # Nested dict
                    t, f = count_fields(value, is_required)
                    total += t
                    filled += f
                elif isinstance(value, list):
                    # List - count based on schema expectations
                    if len(value) > 0:
                        # Count fields in list items
                        for item in value:
                            if isinstance(item, dict):
                                t, f = count_fields(item, is_required)
                                total += t
                                filled += f
                            elif isinstance(item, str) and item.strip():
                                total += 1
                                filled += 1
                            elif isinstance(item, str):
                                total += 1
                    else:
                        # Empty list - count as 1 unfilled field for required sections
                        if is_required and key not in ["Sertifikater", "Annet"]:
                            total += 1
                else:
                    # Primitive field
                    total += 1
                    if value and str(value).strip():
                        filled += 1
        elif isinstance(data, list):
            for item in data:
                t, f = count_fields(item, is_required)
                total += t
                filled += f

        return total, filled

    if not cv_dict:
        return 0.0

    total_fields, filled_fields = count_fields(cv_dict)

    if total_fields == 0:
        return 0.0

    return filled_fields / total_fields


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
