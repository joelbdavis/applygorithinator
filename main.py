from utils.config import OPENAI_API_KEY
from chains.job_fit_chain import run_job_fit_chain
from chains.story_gap_chain import story_answers_gap_llm, format_stories_context
from utils.text_parsing import (
    extract_alignment_section,
    extract_gaps_json,
    cleanse_llm_response,
    extract_llm_content,
    read_file_or_exit,
    FileReadError,
    LLMJsonParseError,
    format_dict_list,
    GapsJsonParseError,
)
from utils.story_manager import StoryManager
from utils.session_logger import SessionLogger
import cli

def get_resume_and_job_description(cli):
    resume_path = cli.prompt_for_resume_path("resources/resumes/original_resume.txt")
    job_description_path = cli.prompt_for_job_description_path("resources/job_descriptions/job_description.txt")
    return resume_path, job_description_path

def read_inputs(resume_path, job_description_path):
    resume_text = read_file_or_exit(resume_path, "resume")
    job_description = read_file_or_exit(job_description_path, "job description")
    return resume_text, job_description

def run_job_fit_analysis(resume_text, job_description, api_key):
    combined_experience = f"Resume:\n{resume_text}"
    result = run_job_fit_chain(combined_experience, job_description, api_key)
    return cleanse_llm_response(result)

def parse_job_fit_output(output):
    alignment = extract_alignment_section(output)
    gaps = extract_gaps_json(output)
    return alignment, gaps

def analyze_gaps_with_llm(gaps, relevant_stories, api_key):
    answered = []
    unanswered = []
    for gap in gaps:
        skill = gap.get('skill', '(unknown skill)')
        question = gap.get('question', '(no question)')
        is_answered, summary, confidence = story_answers_gap_llm(skill, question, relevant_stories, api_key)
        if is_answered:
            answered.append({'gap': gap, 'summary': summary, 'confidence': confidence})
        else:
            unanswered.append(gap)
    return answered, unanswered

def process_unanswered_gaps(unanswered_gaps, story_manager, logger, cli):
    for gap in unanswered_gaps:
        skill = gap.get('skill', '(unknown skill)')
        question = gap.get('question', '(no question)')
        response = cli.prompt_for_story(skill, question)
        logger.log_story_prompt(skill, question)
        if response.lower() != 'skip':
            story_manager.save_story(skill, response, has_experience=True)
            cli.display_story_saved()
            logger.log_story_response(skill, question, response)
        else:
            story_manager.save_story(skill, "No relevant experience", has_experience=False)
            cli.display_no_experience()
            logger.log_no_experience(skill, question)

def finalize_session(logger, cli):
    logger.save()
    cli.display_session_log_path(logger.session_file)

def run_workflow(api_key, cli, story_manager, logger):
    resume_path, job_description_path = get_resume_and_job_description(cli)
    try:
        resume_text, job_description = read_inputs(resume_path, job_description_path)
    except FileReadError as e:
        cli.display_error(e)
        exit(1)
    logger.log_session_header(resume_path, job_description_path, resume_text, job_description)
    job_fit_analysis = run_job_fit_analysis(resume_text, job_description, api_key)
    try:
        alignment, gaps = parse_job_fit_output(job_fit_analysis)
    except GapsJsonParseError as e:
        cli.display_error(e)
        exit(1)
    cli.display_alignment(alignment)
    cli.display_gaps(gaps)
    logger.log_output(job_fit_analysis)
    if gaps:
        cli.display_collect_stories_intro()
        relevant_stories = story_manager.get_relevant_stories()
        try:
            answered, unanswered = analyze_gaps_with_llm(gaps, relevant_stories, api_key)
        except LLMJsonParseError as e:
            cli.display_error(e)
            exit(1)
        for item in answered:
            cli.display_story_already_answered(item['gap'].get('skill', '(unknown skill)'), item['summary'])
        process_unanswered_gaps(unanswered, story_manager, logger, cli)
    finalize_session(logger, cli)

if __name__ == '__main__':  # pragma: no cover
    cli.display_banner()  # pragma: no cover
    story_manager = StoryManager()  # pragma: no cover
    logger = SessionLogger()  # pragma: no cover
    run_workflow(OPENAI_API_KEY, cli, story_manager, logger)  # pragma: no cover



