import os
import datetime
import json
from difflib import SequenceMatcher
from config import OPENAI_API_KEY
from chains.job_fit_chain import run_job_fit_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import re

print('Welcome to the LangChain-powered Applygorithminator!')

# Prompt for file paths
resume_path = input("Enter the path to your resume file (or press Enter to use default): ").strip()
job_description_path = input("Enter the path to the job description file (or press Enter to use default): ").strip()

# Use default paths if none provided
if not resume_path:
    resume_path = "resources/resumes/original_resume.txt"
if not job_description_path:
    job_description_path = "resources/job_descriptions/job_description.txt"

# Read file contents
try:
    with open(resume_path, "r") as f:
        resume_text = f.read()
    with open(job_description_path, "r") as f:
        job_description = f.read()
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit(1)

# Load all stories
stories_dir = "resources/stories"
stories_file = os.path.join(stories_dir, "stories.json")
stories_context = ""
all_stories = []
relevant_stories = []
if os.path.exists(stories_file):
    with open(stories_file, "r") as sf:
        stories_data = json.load(sf)
    all_stories = stories_data.get("stories", [])
    relevant_stories = [s for s in all_stories if s.get("has_experience")]
    if relevant_stories:
        stories_context = "\nAdditional Experience Stories:\n"
        for story in relevant_stories:
            stories_context += f"\nSkill: {story['skill']}\nStory: {story['story']}\n"
    else:
        stories_context = "\nAdditional Experience Stories:\n(None)\n"
else:
    stories_context = "\nAdditional Experience Stories:\n(None)\n"

# Prepare session logging
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
sessions_dir = "sessions"
os.makedirs(sessions_dir, exist_ok=True)
session_file = os.path.join(sessions_dir, f"session_{timestamp}.txt")

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
    except Exception:
        return []

def cleanse_llm_response(result):
    if isinstance(result, dict):
        output = result.get('content') or result.get('text') or str(result)
    else:
        output = str(result)
    output = output.replace('\\n', '\n').replace('\r\n', '\n').replace('\n', '\n')
    return output

with open(session_file, "w") as log:
    log.write("=== Applygorithminator Session Log ===\n")
    log.write(f"Timestamp: {timestamp}\n")
    log.write(f"Resume file: {resume_path}\n")
    log.write(f"Job description file: {job_description_path}\n\n")
    log.write("--- Resume ---\n")
    log.write(resume_text + "\n\n")
    log.write("--- Additional Experience Stories ---\n")
    log.write(stories_context.strip() + "\n\n")
    log.write("--- Job Description ---\n")
    log.write(job_description + "\n\n")
    log.write("--- Job Fit Analysis ---\n")

    print("\nAnalyzing job fit...\n")
    # PASS 1: Run job fit analysis with only resume and job description
    combined_experience = f"Resume:\n{resume_text}"
    result = run_job_fit_chain(combined_experience, job_description, OPENAI_API_KEY)
    # Extract the main content (handle dict or string)
    output = cleanse_llm_response(result)
    # Extract and print Alignment and Gaps in human-readable format
    alignment = extract_alignment_section(output)
    gaps = extract_gaps_json(output)

    print("\n=== Alignment ===")
    for item in alignment:
        print(f"✅ {item}")
    print("\n=== Gaps ===")
    if gaps:
        for gap in gaps:
            skill = gap.get('skill', '(unknown skill)')
            question = gap.get('question', '(no question)')
            print(f"❓ {skill}")
    else:
        print("(No gaps found)")

    log.write(output + "\n")

    # --- PASS 2: For each gap, check stories with LLM ---
    def extract_json_from_string(s):
        match = re.search(r"content='((?:[^'\\]|\\.)*)'", s)
        if match:
            content = match.group(1).replace("\\'", "'")
            # Replace escaped newlines with spaces
            content = content.replace("\\n", " ")
            # Remove any remaining extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            return content
        return s

    def story_answers_gap_llm(gap_skill, question, stories, openai_api_key):
        if not stories:
            return False, None, None
        # Prepare prompt
        stories_text = "\n".join([f"Skill: {s['skill']}\nStory: {s['story']}" for s in stories])
        prompt = PromptTemplate(
            input_variables=["gap_skill", "question", "stories_text"],
            template="""
You are helping a user prepare for a job application. For the following skill gap and behavioral question, review the user's provided stories. If any story answers the question, respond with a JSON object: {{"answered": true, "summary": "[summary of how the story answers the question]", "confidence": [confidence score between 0 and 1]}}.
If none of the stories are relevant, respond with {{"answered": false, "summary": "", "confidence": [confidence score between 0 and 1]}}.

Guidelines for confidence scores:
- 1.0: Perfect match - the story directly addresses the exact scenario described in the question
- 0.8-0.9: Strong match - the story clearly demonstrates the skill/experience but might be in a slightly different context
- 0.6-0.7: Partial match - the story shows some relevant experience but doesn't fully address the question
- 0.4-0.5: Weak match - the story has some tangential relevance but doesn't really answer the question
- 0.0-0.3: No match - the story is not relevant to the question

- If you set "answered" to true, the summary must clearly explain which story answers the question.
- If no story matches, set "answered" to false and summary to an empty string.
- Do not say 'not directly addressed' or similar in the summary if answered is true.
- Respond ONLY with a valid JSON object as described above.

Skill Gap: {gap_skill}
Behavioral Question: {question}

User's Stories:
{stories_text}
"""
        )
        llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo", temperature=0.0, max_tokens=300)
        chain = prompt | llm
        result = chain.invoke({
            "gap_skill": gap_skill,
            "question": question,
            "stories_text": stories_text
        })
        if isinstance(result, dict):
            content = result.get('content', '').strip()
        else:
            content = str(result).strip()
        #print(f"[DEBUG] content: {content}")  # Debug print
        # Extract the JSON part if the string contains more than just the JSON
        json_str = extract_json_from_string(content)
        #print(f"[DEBUG] json_str: {json_str}")  # Debug print
        try:
            response_json = json.loads(json_str)
            answered = response_json.get('answered', False)
            summary = response_json.get('summary', '')
            confidence = response_json.get('confidence', None)
            # Sanity check: if summary contains phrases indicating no match, treat as not answered
            if answered and any(phrase in summary.lower() for phrase in ["not directly addressed", "no relevant story", "not covered"]):
                answered = False
            #print(f"[DEBUG] confidence: {confidence}")  # Print confidence for review
            return answered, summary, confidence
        except Exception as e:
            #print(f"[DEBUG] Failed to parse LLM JSON response: {e}\nRaw content: {content}")
            return False, content, None

    gaps = extract_gaps_json(output)
    #print(f"[DEBUG] Parsed {len(gaps)} gaps: {gaps}")  # Debug print
    if gaps:
        print("\nLet's collect some stories to help strengthen your resume:")
        os.makedirs(stories_dir, exist_ok=True)
        # Load existing stories
        if os.path.exists(stories_file):
            with open(stories_file, "r") as sf:
                stories_data = json.load(sf)
        else:
            stories_data = {"stories": []}
        for skill, question in gaps:
            # Use LLM to check if any story answers the gap
            answered, summary, confidence = story_answers_gap_llm(skill, question, all_stories, OPENAI_API_KEY)
            #print(f"[DEBUG] LLM response for skill '{skill}': {summary}")  # Debug print
            #print(f"[DEBUG] Confidence score: {confidence}")  # Show confidence
            if answered:
                print(f"\n[Story already answers: {skill}]\n{summary}")
                log.write(f"\n[Story already answers: {skill}]\n{summary}\n")
                continue
            #print(f"[DEBUG] Prompting user for story for skill: {skill}")  # Debug print
            print(f"\nSkill/Experience: {skill}")
            print(f"Question: {question}")
            response = input("\nPlease share your story (or type 'skip' if you don't have relevant experience): ").strip()
            if response.lower() != 'skip':
                stories_data["stories"].append({
                    "skill": skill,
                    "story": response,
                    "has_experience": True,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                print("Story saved for future use!")
                log.write(f"\nSkill/Experience: {skill}\nQuestion: {question}\nStory: {response}\n")
            else:
                stories_data["stories"].append({
                    "skill": skill,
                    "story": "No relevant experience",
                    "has_experience": False,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                print("Noted that you don't have this experience.")
                log.write(f"\nSkill/Experience: {skill}\nQuestion: {question}\nStory: No relevant experience\n")
        # Save updated stories
        with open(stories_file, "w") as sf:
            json.dump(stories_data, sf, indent=2)

print(f"\nSession log saved to: {session_file}")

