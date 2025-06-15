import re
import json
import logging

class FileReadError(Exception):
    pass

class LLMJsonParseError(Exception):
    pass

class GapsJsonParseError(Exception):
    pass

def extract_llm_content(result):
    """Extracts the main content from an LLM result, handling both dict and string."""
    if isinstance(result, dict):
        return result.get('content') or result.get('text') or str(result)
    return str(result)

def extract_alignment_section(output):
    """Extracts the ALIGNMENT section as a list of strings using regex."""
    match = re.search(r'ALIGNMENT:\s*(.*?)(?:GAPS:|$)', output, re.DOTALL | re.IGNORECASE)
    alignment = []
    if match:
        align_text = match.group(1).strip()
        for line in align_text.splitlines():
            line = line.strip().lstrip('-').strip()
            if line:
                alignment.append(line)
    return alignment

def extract_gaps_json(output):
    """Extracts the GAPS section as a JSON array using regex."""
    match = re.search(r'GAPS:\s*(\[.*?\])', output, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    json_str = match.group(1)
    try:
        return json.loads(json_str)
    except Exception as e:
        raise GapsJsonParseError(f"Failed to parse GAPS JSON: {e}\nRaw: {json_str}")

def cleanse_llm_response(result):
    """Cleanses the LLM response, handling dict or string and normalizing newlines."""
    output = extract_llm_content(result)
    output = output.replace('\\n', '\n').replace('\r\n', '\n').replace('\n', '\n')
    return output

def extract_json_from_string(s):
    """Extracts the JSON part from an LLM output string, handling escaped newlines and whitespace."""
    match = re.search(r"content='((?:[^'\\]|\\.)*)'", s)
    if match:
        content = match.group(1).replace("\\'", "'")
        # Replace escaped newlines with spaces
        content = content.replace("\\n", " ")
        # Remove any remaining extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        return content
    return s

def extract_json_from_llm_result(result):
    """
    Given an LLM result (dict or string), extract and parse the JSON object/array from the content.
    Returns the parsed JSON (dict or list), or raises LLMJsonParseError if parsing fails.
    """
    content = extract_llm_content(result)
    json_str = extract_json_from_string(content)
    try:
        return json.loads(json_str)
    except Exception as e:
        raise LLMJsonParseError(f"Failed to parse JSON from LLM result: {e}\nRaw string: {json_str}")

def read_file_or_exit(path, description="file"):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        raise FileReadError(f"Could not find {description} at {path}: {e}")

def format_dict_list(items, keys, section_title="Items", empty_message="(None)"):
    if not items:
        return f"\n{section_title}:\n{empty_message}\n"
    context = f"\n{section_title}:\n"
    for item in items:
        for key in keys:
            if key in item:
                context += f"\n{key.capitalize()}: {item[key]}"
        context += "\n"
    return context 