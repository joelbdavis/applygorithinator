import pytest
from unittest.mock import patch, MagicMock
import chains.story_gap_chain as story_gap_chain
from chains.story_gap_chain import format_stories_context, story_answers_gap_llm
from utils.text_parsing import LLMJsonParseError

def test_format_stories_context_basic():
    stories = [
        {"skill": "Python", "story": "Wrote a script."},
        {"skill": "Leadership", "story": "Led a team."}
    ]
    result = format_stories_context(stories)
    assert "Skill: Python" in result
    assert "Story: Wrote a script." in result
    assert "Skill: Leadership" in result
    assert "Story: Led a team." in result
    assert "Additional Experience Stories" in result

def test_format_stories_context_empty():
    result = format_stories_context([])
    assert "(None)" in result
    assert "Additional Experience Stories" in result

def test_format_stories_context_missing_keys():
    stories = [{"skill": "Python"}, {"story": "Led a team."}]
    result = format_stories_context(stories)
    assert "Skill: Python" in result
    assert "Story: Led a team." in result

@patch('chains.story_gap_chain.ChatOpenAI')
def test_story_answers_gap_llm_answered(mock_chat_openai):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {'content': '{"answered": true, "summary": "Story matches", "confidence": 0.9}'}
    with patch.object(story_gap_chain, 'PromptTemplate', create=True) as mock_prompt:
        mock_prompt.return_value.__or__.return_value = mock_chain
        answered, summary, confidence = story_gap_chain.story_answers_gap_llm("Python", "Tell me about Python", [{"skill": "Python", "story": "Wrote a script."}], "fake-key")
        assert answered is True
        assert summary == "Story matches"
        assert confidence == 0.9

@patch('chains.story_gap_chain.ChatOpenAI')
def test_story_answers_gap_llm_not_answered(mock_chat_openai):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {'content': '{"answered": false, "summary": "", "confidence": 0.1}'}
    with patch.object(story_gap_chain, 'PromptTemplate', create=True) as mock_prompt:
        mock_prompt.return_value.__or__.return_value = mock_chain
        answered, summary, confidence = story_gap_chain.story_answers_gap_llm("Python", "Tell me about Python", [{"skill": "Java", "story": "Wrote a script."}], "fake-key")
        assert answered is False
        assert summary == ""
        assert confidence == 0.1

@patch('chains.story_gap_chain.ChatOpenAI')
def test_story_answers_gap_llm_invalid_json(mock_chat_openai):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {'content': 'not a json'}
    with patch.object(story_gap_chain, 'PromptTemplate', create=True) as mock_prompt:
        mock_prompt.return_value.__or__.return_value = mock_chain
        with pytest.raises(LLMJsonParseError):
            story_gap_chain.story_answers_gap_llm("Python", "Tell me about Python", [{"skill": "Python", "story": "Wrote a script."}], "fake-key")

def test_story_answers_gap_llm_empty_stories():
    answered, summary, confidence = story_gap_chain.story_answers_gap_llm("Python", "Tell me about Python", [], "fake-key")
    assert answered is False
    assert summary is None
    assert confidence is None

def test_story_answers_gap_llm_summary_indicates_no_match():
    # Patch ChatOpenAI and PromptTemplate to avoid real LLM calls
    with patch('chains.story_gap_chain.ChatOpenAI') as mock_chat_openai:
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        mock_chain = MagicMock()
        # LLM returns answered=True but summary indicates no match
        mock_chain.invoke.return_value = {'content': '{"answered": true, "summary": "Not directly addressed", "confidence": 0.5}'}
        with patch('chains.story_gap_chain.PromptTemplate', create=True) as mock_prompt:
            mock_prompt.return_value.__or__.return_value = mock_chain
            with patch('chains.story_gap_chain.extract_json_from_llm_result') as mock_extract_json:
                mock_extract_json.return_value = {
                    'answered': True,
                    'summary': 'Not directly addressed',
                    'confidence': 0.5
                }
                answered, summary, confidence = story_answers_gap_llm(
                    'Python', 'Tell me about Python', [{'skill': 'Python', 'story': 'Did Python stuff.'}], 'fake-key')
                assert answered is False
                assert summary == 'Not directly addressed'
                assert confidence == 0.5 