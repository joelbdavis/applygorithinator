import pytest
from unittest.mock import patch, MagicMock
from chains import job_fit_chain

@patch('chains.job_fit_chain.ChatOpenAI')
def test_run_job_fit_chain_basic(mock_chat_openai):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {'content': 'Test output'}
    with patch.object(job_fit_chain, 'job_fit_prompt', create=True) as mock_prompt:
        mock_prompt.__or__.return_value = mock_chain
        result = job_fit_chain.run_job_fit_chain('resume text', 'job description', 'fake-key')
        assert result == {'content': 'Test output'}
        mock_chain.invoke.assert_called_once()
        args, kwargs = mock_chain.invoke.call_args
        assert args[0]['combined_experience'] == 'resume text'
        assert args[0]['job_description'] == 'job description'

@patch('chains.job_fit_chain.ChatOpenAI')
def test_run_job_fit_chain_empty_inputs(mock_chat_openai):
    mock_llm = MagicMock()
    mock_chat_openai.return_value = mock_llm
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {'content': ''}
    with patch.object(job_fit_chain, 'job_fit_prompt', create=True) as mock_prompt:
        mock_prompt.__or__.return_value = mock_chain
        result = job_fit_chain.run_job_fit_chain('', '', 'fake-key')
        assert result == {'content': ''}
        mock_chain.invoke.assert_called_once()
        args, kwargs = mock_chain.invoke.call_args
        assert args[0]['combined_experience'] == ''
        assert args[0]['job_description'] == '' 