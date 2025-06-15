import pytest
from unittest.mock import MagicMock, patch
from main import run_workflow, analyze_gaps_with_llm, process_unanswered_gaps, FileReadError, LLMJsonParseError, read_inputs, run_job_fit_analysis, parse_job_fit_output, finalize_session

# Helper: create a fake gap
def make_gap(skill, question):
    return {'skill': skill, 'question': question}

def test_analyze_gaps_with_llm_basic():
    gaps = [make_gap('Python', 'Tell me about Python')]
    relevant_stories = [{'skill': 'Python', 'story': 'Did Python stuff.'}]
    with patch('main.story_answers_gap_llm') as mock_llm:
        mock_llm.return_value = (True, 'Matched story', 0.9)
        answered, unanswered = analyze_gaps_with_llm(gaps, relevant_stories, 'fake-key')
        assert len(answered) == 1
        assert answered[0]['gap']['skill'] == 'Python'
        assert answered[0]['summary'] == 'Matched story'
        assert answered[0]['confidence'] == 0.9
        assert unanswered == []

    with patch('main.story_answers_gap_llm') as mock_llm:
        mock_llm.return_value = (False, '', 0.1)
        answered, unanswered = analyze_gaps_with_llm(gaps, relevant_stories, 'fake-key')
        assert answered == []
        assert len(unanswered) == 1
        assert unanswered[0]['skill'] == 'Python'

def test_analyze_gaps_with_llm_raises():
    gaps = [make_gap('Python', 'Tell me about Python')]
    relevant_stories = []
    with patch('main.story_answers_gap_llm', side_effect=LLMJsonParseError('fail')):
        with pytest.raises(LLMJsonParseError):
            analyze_gaps_with_llm(gaps, relevant_stories, 'fake-key')

def test_process_unanswered_gaps():
    cli = MagicMock()
    logger = MagicMock()
    story_manager = MagicMock()
    gaps = [make_gap('Python', 'Tell me about Python')]
    # Simulate user provides a story
    cli.prompt_for_story.return_value = 'A Python story'
    process_unanswered_gaps(gaps, story_manager, logger, cli)
    story_manager.save_story.assert_called_with('Python', 'A Python story', has_experience=True)
    cli.display_story_saved.assert_called_once()
    logger.log_story_response.assert_called_with('Python', 'Tell me about Python', 'A Python story')
    # Simulate user skips
    cli.reset_mock(); logger.reset_mock(); story_manager.reset_mock()
    cli.prompt_for_story.return_value = 'skip'
    process_unanswered_gaps(gaps, story_manager, logger, cli)
    story_manager.save_story.assert_called_with('Python', 'No relevant experience', has_experience=False)
    cli.display_no_experience.assert_called_once()
    logger.log_no_experience.assert_called_with('Python', 'Tell me about Python')

def test_run_workflow_file_read_error():
    cli = MagicMock()
    story_manager = MagicMock()
    logger = MagicMock()
    cli.prompt_for_resume_path.return_value = 'resume.txt'
    cli.prompt_for_job_description_path.return_value = 'job.txt'
    with patch('main.read_inputs', side_effect=FileReadError('fail')):
        with pytest.raises(SystemExit):
            run_workflow('fake-key', cli, story_manager, logger)
    cli.display_error.assert_called_once()

def test_run_workflow_llm_json_parse_error():
    cli = MagicMock()
    story_manager = MagicMock()
    logger = MagicMock()
    cli.prompt_for_resume_path.return_value = 'resume.txt'
    cli.prompt_for_job_description_path.return_value = 'job.txt'
    with patch('main.read_inputs', return_value=('resume', 'job')):
        with patch('main.run_job_fit_analysis', return_value='output'):
            with patch('main.parse_job_fit_output', return_value=('alignment', [make_gap('Python', 'Tell me about Python')])):
                story_manager.get_relevant_stories.return_value = []
                with patch('main.analyze_gaps_with_llm', side_effect=LLMJsonParseError('fail')):
                    with pytest.raises(SystemExit):
                        run_workflow('fake-key', cli, story_manager, logger)
    cli.display_error.assert_called_once()

# --- Tests for read_inputs ---
def test_read_inputs_success():
    with patch('main.read_file_or_exit') as mock_read:
        mock_read.side_effect = ['resume content', 'job description content']
        resume, jd = read_inputs('resume.txt', 'job.txt')
        assert resume == 'resume content'
        assert jd == 'job description content'
        assert mock_read.call_count == 2
        mock_read.assert_any_call('resume.txt', 'resume')
        mock_read.assert_any_call('job.txt', 'job description')

def test_read_inputs_file_error():
    with patch('main.read_file_or_exit', side_effect=FileReadError('fail')):
        with pytest.raises(FileReadError):
            read_inputs('resume.txt', 'job.txt')

# --- Tests for run_job_fit_analysis ---
def test_run_job_fit_analysis():
    with patch('main.run_job_fit_chain') as mock_chain, \
         patch('main.cleanse_llm_response') as mock_cleanse:
        mock_chain.return_value = 'llm raw result'
        mock_cleanse.return_value = 'cleaned result'
        result = run_job_fit_analysis('resume text', 'job desc', 'api-key')
        mock_chain.assert_called_once_with('Resume:\nresume text', 'job desc', 'api-key')
        mock_cleanse.assert_called_once_with('llm raw result')
        assert result == 'cleaned result'

# --- Tests for parse_job_fit_output ---
def test_parse_job_fit_output():
    with patch('main.extract_alignment_section') as mock_align, \
         patch('main.extract_gaps_json') as mock_gaps:
        mock_align.return_value = 'alignment section'
        mock_gaps.return_value = [{'skill': 'Python'}]
        alignment, gaps = parse_job_fit_output('llm output')
        mock_align.assert_called_once_with('llm output')
        mock_gaps.assert_called_once_with('llm output')
        assert alignment == 'alignment section'
        assert gaps == [{'skill': 'Python'}]

# --- Test for finalize_session ---
def test_finalize_session():
    logger = MagicMock()
    cli = MagicMock()
    logger.session_file = 'session.log'
    finalize_session(logger, cli)
    logger.save.assert_called_once()
    cli.display_session_log_path.assert_called_once_with('session.log')

def test_run_workflow_with_answered_and_unanswered(monkeypatch):
    cli = MagicMock()
    story_manager = MagicMock()
    logger = MagicMock()
    cli.prompt_for_resume_path.return_value = 'resume.txt'
    cli.prompt_for_job_description_path.return_value = 'job.txt'
    # Setup parse_job_fit_output to return gaps
    gaps = ['gap1']
    # Setup analyze_gaps_with_llm to return one answered and one unanswered
    answered = [{'gap': {'skill': 'Python'}, 'summary': 'summary', 'confidence': 0.9}]
    unanswered = [{'skill': 'Java'}]
    monkeypatch.setattr('main.read_inputs', lambda *a, **kw: ('resume', 'job'))
    monkeypatch.setattr('main.run_job_fit_analysis', lambda *a, **kw: 'output')
    monkeypatch.setattr('main.parse_job_fit_output', lambda *a, **kw: ('alignment', gaps))
    story_manager.get_relevant_stories.return_value = []
    monkeypatch.setattr('main.analyze_gaps_with_llm', lambda *a, **kw: (answered, unanswered))
    monkeypatch.setattr('main.process_unanswered_gaps', MagicMock())
    monkeypatch.setattr('main.finalize_session', MagicMock())
    from main import run_workflow, process_unanswered_gaps, finalize_session
    run_workflow('fake-key', cli, story_manager, logger)
    cli.display_story_already_answered.assert_called_once_with('Python', 'summary')
    process_unanswered_gaps.assert_called_once_with(unanswered, story_manager, logger, cli)
    finalize_session.assert_called_once_with(logger, cli)

def test_run_workflow_gaps_json_parse_error(monkeypatch):
    cli = MagicMock()
    story_manager = MagicMock()
    logger = MagicMock()
    cli.prompt_for_resume_path.return_value = 'resume.txt'
    cli.prompt_for_job_description_path.return_value = 'job.txt'
    monkeypatch.setattr('main.read_inputs', lambda *a, **kw: ('resume', 'job'))
    monkeypatch.setattr('main.run_job_fit_analysis', lambda *a, **kw: 'output')
    from utils.text_parsing import GapsJsonParseError
    def raise_gaps_json(*a, **kw):
        raise GapsJsonParseError('bad gaps')
    monkeypatch.setattr('main.parse_job_fit_output', raise_gaps_json)
    from main import run_workflow
    with pytest.raises(SystemExit):
        run_workflow('fake-key', cli, story_manager, logger)
    cli.display_error.assert_called_once() 