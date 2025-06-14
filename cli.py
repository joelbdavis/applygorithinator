from utils.text_parsing import format_dict_list

def prompt_for_resume_path(default_path):
    path = input(f"Enter the path to your resume file (or press Enter to use default: {default_path}): ").strip()
    return path or default_path

def prompt_for_job_description_path(default_path):
    path = input(f"Enter the path to your job description file (or press Enter to use default: {default_path}): ").strip()
    return path or default_path

def display_alignment(alignment):
    print("\n=== Alignment ===")
    for item in alignment:
        print(f"✅ {item}")

def display_gaps(gaps):
    print(format_dict_list(gaps, ["skill", "question"], section_title="Gaps"))

def prompt_for_story(skill, question):
    print(f"\nSkill/Experience: {skill}")
    print(f"Question: {question}")
    return input("\nPlease share your story (or type 'skip' if you don't have relevant experience): ").strip()

def display_story_already_answered(skill, summary):
    print(f"\n[Story already answers: {skill}]\n{summary}")

def display_story_saved():
    print("Story saved for future use!")

def display_no_experience():
    print("Noted that you don't have this experience.")

def display_session_log_path(session_file):
    print(f"\nSession log saved to: {session_file}")

def display_collect_stories_intro():
    print("\nLet's collect some stories to help strengthen your resume:")

def display_error(message):
    print(f"Error: {message}")

def display_analyzing_job_fit():
    print("\nAnalyzing job fit...\n")

def display_banner():
    print('Welcome to the LangChain-powered Applygorithminator!') 