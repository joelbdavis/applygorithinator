import pytest
from utils.text_parsing import (
    format_dict_list,
    extract_alignment_section,
    extract_gaps_json,
    cleanse_llm_response,
    extract_llm_content,
    read_file_or_exit,
    FileReadError,
    extract_json_from_llm_result,
    LLMJsonParseError,
    extract_json_from_string,
    GapsJsonParseError,
)
import tempfile
import os
import json

def test_format_dict_list_basic():
    items = [
        {"skill": "Python", "story": "Wrote a script."},
        {"skill": "Leadership", "story": "Led a team."}
    ]
    result = format_dict_list(items, ["skill", "story"], section_title="Stories")
    assert "Skill: Python" in result
    assert "Story: Wrote a script." in result
    assert "Skill: Leadership" in result
    assert "Story: Led a team." in result
    assert "Stories" in result

def test_format_dict_list_empty():
    result = format_dict_list([], ["skill", "story"], section_title="Stories")
    assert "(None)" in result
    assert "Stories" in result

def test_format_dict_list_missing_keys():
    items = [{"skill": "Python"}, {"story": "Wrote a script."}]
    result = format_dict_list(items, ["skill", "story"], section_title="Stories")
    assert "Skill: Python" in result
    assert "Story: Wrote a script." in result

def test_format_dict_list_extra_keys():
    items = [{"skill": "Python", "story": "Wrote a script.", "extra": 123}]
    result = format_dict_list(items, ["skill", "story"], section_title="Stories")
    assert "Skill: Python" in result
    assert "Story: Wrote a script." in result
    assert "extra" not in result

def test_format_dict_list_non_dict():
    items = ["not a dict", {"skill": "Python"}]
    result = format_dict_list(items, ["skill"], section_title="Stories")
    assert "Skill: Python" in result

def test_format_dict_list_non_list():
    result = format_dict_list(None, ["skill"], section_title="Stories")
    assert "(None)" in result

def test_extract_alignment_section_no_alignment():
    text = "No alignment section here."
    alignment = extract_alignment_section(text)
    assert alignment == []

def test_extract_gaps_json_no_gaps():
    text = "No GAPS section here."
    gaps = extract_gaps_json(text)
    assert gaps == []

def test_extract_gaps_json_malformed():
    text = "GAPS: not a json array"
    gaps = extract_gaps_json(text)
    assert gaps == []

def test_extract_gaps_json_invalid_json():
    text = "GAPS: not a json array"
    result = extract_gaps_json(text)
    assert result == []

def test_cleanse_llm_response_missing_keys():
    result = {"foo": "bar"}
    output = cleanse_llm_response(result)
    assert isinstance(output, str)

def test_cleanse_llm_response_empty():
    result = ""
    output = cleanse_llm_response(result)
    assert output == ""

def test_extract_llm_content_empty_dict():
    result = {}
    assert extract_llm_content(result) == "{}"

def test_extract_llm_content_empty_str():
    result = ""
    assert extract_llm_content(result) == ""

def test_read_file_or_exit_empty_file():
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tf:
        tf.flush()
        tf.close()
        content = read_file_or_exit(tf.name, "test file")
        assert content == ""
    os.unlink(tf.name)

def test_read_file_or_exit_file_not_found():
    path = tempfile.mktemp()  # Path that does not exist
    if os.path.exists(path):
        os.unlink(path)
    try:
        read_file_or_exit(path, "test file")
    except FileReadError as e:
        assert "Could not find test file" in str(e)
    else:
        assert False, "FileReadError not raised"

def test_extract_json_from_llm_result_number():
    result = {"content": "123"}
    parsed = extract_json_from_llm_result(result)
    assert parsed == 123

def test_extract_json_from_llm_result_empty():
    result = {"content": ''}
    with pytest.raises(LLMJsonParseError):
        extract_json_from_llm_result(result)

def test_extract_alignment_section_with_alignment():
    text = """ALIGNMENT:
- Skill 1
- Skill 2
GAPS: []
"""
    result = extract_alignment_section(text)
    assert result == ['Skill 1', 'Skill 2']

def test_extract_json_from_string_with_escaped_newlines():
    s = "content='value with newline\\nmore text'"
    result = extract_json_from_string(s)
    assert result == 'value with newline more text'

def test_extract_gaps_json_raises_custom_exception():
    text = "GAPS: [not valid json]"
    try:
        extract_gaps_json(text)
    except GapsJsonParseError as e:
        assert "Failed to parse GAPS JSON" in str(e)
        assert "[not valid json]" in str(e)
    else:
        assert False, "GapsJsonParseError not raised"
