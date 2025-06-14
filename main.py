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
)
from utils.story_manager import StoryManager
from utils.session_logger import SessionLogger
import cli

cli.display_banner()

# Prompt for file paths
resume_path = cli.prompt_for_resume_path("resources/resumes/original_resume.txt")
job_description_path = cli.prompt_for_job_description_path("resources/job_descriptions/job_description.txt")

# Read file contents
try:
    resume_text = read_file_or_exit(resume_path, "resume")
    job_description = read_file_or_exit(job_description_path, "job description")
except FileReadError as e:
    cli.display_error(e)
    exit(1)

# Initialize StoryManager
story_manager = StoryManager()

# Load all stories
all_stories = story_manager.get_all_stories()
relevant_stories = story_manager.get_relevant_stories()

# Prepare session logging
logger = SessionLogger()
logger.log_session_header(resume_path, job_description_path, resume_text, stories_context, job_description)

cli.display_analyzing_job_fit()
# PASS 1: Run job fit analysis with only resume and job description
combined_experience = f"Resume:\n{resume_text}"
result = run_job_fit_chain(combined_experience, job_description, OPENAI_API_KEY)
output = cleanse_llm_response(result)

alignment = extract_alignment_section(output)
cli.display_alignment(alignment)

gaps = extract_gaps_json(output)
cli.display_gaps(gaps)

logger.log_output(output)

# --- PASS 2: For each gap, check stories with LLM ---
if gaps:
    cli.display_collect_stories_intro()
    for gap in gaps:
        skill = gap.get('skill', '(unknown skill)')
        question = gap.get('question', '(no question)')
        try:
            # Use LLM to check if any story answers the gap
            answered, summary, confidence = story_answers_gap_llm(skill, question, relevant_stories, OPENAI_API_KEY)
        except LLMJsonParseError as e:
            cli.display_error(e)
            exit(1)
        if answered:
            cli.display_story_already_answered(skill, summary)
            logger.log_story_already_answered(skill, summary)
            continue
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

logger.save()
cli.display_session_log_path(logger.session_file)



