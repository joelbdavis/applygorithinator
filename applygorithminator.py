import openai
import os
import sys
import time
import json
import argparse
import re
from datetime import datetime
from config import OPENAI_API_KEY

def show_thinking(message="Processing", thinking_messages=None):
    """Show a thinking indicator with rotating messages"""
    if thinking_messages is None:
        thinking_messages = [
            "Analyzing resume content...",
            "Reviewing job requirements...",
            "Identifying key skills...",
            "Evaluating experience match...",
            "Considering ATS optimization...",
            "Looking for improvement opportunities...",
            "Checking for keyword alignment...",
            "Assessing overall fit..."
        ]
    
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    message_index = 0
    last_message_time = time.time()
    
    while True:
        current_time = time.time()
        # Change message every 3 seconds
        if current_time - last_message_time >= 3:
            message_index = (message_index + 1) % len(thinking_messages)
            last_message_time = current_time
        
        sys.stdout.write(f"\r{message} {spinner[i]} {thinking_messages[message_index]}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(spinner)
        yield

class Applygorithminator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.resumes_dir = "resources/resumes"
        self.job_descriptions_dir = "resources/job_descriptions"
        self.stories_dir = "resources/stories"
        self.prompts = self._load_prompts()
        
    def _load_prompts(self):
        """Load prompts from prompts.txt"""
        prompts = {}
        try:
            with open("prompts.txt", "r") as f:
                current_prompt = None
                current_content = []
                
                for line in f:
                    line = line.strip()
                    if line.startswith("Prompt #"):
                        if current_prompt is not None:
                            prompts[current_prompt] = "\n".join(current_content)
                        current_prompt = line.split(":")[0].strip()
                        current_content = []
                    elif line and not line.startswith("Why?"):
                        current_content.append(line)
                
                if current_prompt is not None:
                    prompts[current_prompt] = "\n".join(current_content)
                    
            return prompts
        except FileNotFoundError:
            print("Warning: prompts.txt not found. Using default prompts.")
            return {}

    def _load_stories(self):
        """Load existing stories from JSON file"""
        stories_file = os.path.join(self.stories_dir, "stories.json")
        if os.path.exists(stories_file):
            with open(stories_file, "r") as f:
                return json.load(f)
        return {"stories": []}

    def _save_stories(self, stories):
        """Save stories to JSON file"""
        stories_file = os.path.join(self.stories_dir, "stories.json")
        with open(stories_file, "w") as f:
            json.dump(stories, f, indent=2)

    def _save_story(self, skill, story, has_experience=True):
        """Save a new story to the stories collection"""
        stories = self._load_stories()
        stories["stories"].append({
            "skill": skill,
            "story": story,
            "has_experience": has_experience,
            "timestamp": datetime.now().isoformat()
        })
        self._save_stories(stories)
    
    def save_resume(self, resume_text, is_original=True):
        """Save resume text to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "original" if is_original else "customized"
        filename = f"{prefix}_resume_{timestamp}.txt"
        filepath = os.path.join(self.resumes_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(resume_text)
        return filepath
    
    def save_job_description(self, job_description):
        """Save job description to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_description_{timestamp}.txt"
        filepath = os.path.join(self.job_descriptions_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(job_description)
        return filepath
    
    def read_file(self, filepath):
        """Read content from a file"""
        with open(filepath, "r") as f:
            return f.read()
    
    def test_api_connection(self):
        """
        Test the OpenAI API connection with a simple prompt
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'API connection successful!' if you can read this."}
                ]
            )
            print("✅ API Connection Test:")
            print(response.choices[0].message.content)
            return True
        except Exception as e:
            print("❌ API Connection Test Failed:")
            print(f"Error: {str(e)}")
            return False

    def analyze_fit(self, resume_text, job_description):
        """
        Analyze if the combined resume and stories are a good fit for the job description and generate behavioral questions for true gaps only.
        """
        try:
            # Load all existing stories with has_experience=True
            stories = self._load_stories()
            relevant_stories = [s for s in stories["stories"] if s["has_experience"]]
            
            # Combine resume and stories as the candidate's total experience
            stories_context = ""
            if relevant_stories:
                stories_context = "\nAdditional Experience Stories:\n"
                for story in relevant_stories:
                    stories_context += f"\nSkill: {story['skill']}\nStory: {story['story']}\n"
            
            combined_experience = f"Resume:\n{resume_text}\n{stories_context}"
            
            # Prompt for analysis
            analysis_prompt = f"""
            Compare my combined experience (resume plus additional stories) to this job description and identify:
            1. Key skills and experiences that are well-aligned
            2. Important skills or experiences from the job description that are missing or could be strengthened (i.e., not covered by either the resume or the stories)
            3. For each gap, generate a specific behavioral question in the format "Tell me about a time when you [specific scenario related to the missing skill/experience]"
            
            Combined Experience:
            {combined_experience}
            
            Job Description:
            {job_description}
            
            Format your response as follows:
            ALIGNMENT:
            [List aligned skills/experiences]
            
            GAPS:
            [List gaps with corresponding behavioral questions]
            """
            
            print("\nAnalyzing job fit and generating questions...")
            print("Response:")
            
            # Use streaming API for analysis
            stream = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional career advisor and job matching expert."},
                    {"role": "user", "content": analysis_prompt}
                ],
                stream=True
            )
            
            # Collect the full response while showing it in real-time
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n")  # Add a newline after the response
            
            # Extract gaps and questions from the response
            gaps_section = full_response.split("GAPS:")[1] if "GAPS:" in full_response else ""
            gaps = []
            current_gap = None
            
            for line in gaps_section.split("\n"):
                line = line.strip()
                if line and not line.startswith("["):
                    if "Tell me about a time" in line:
                        if current_gap:
                            gaps.append((current_gap, line))
                    else:
                        current_gap = line
            
            # Only prompt for new stories for gaps not already covered by stories
            existing_skills = set(s["skill"].strip().lower() for s in relevant_stories)
            if gaps:
                print("\nLet's collect some stories to help strengthen your resume:")
                for skill, question in gaps:
                    skill_key = skill.strip().lower()
                    if skill_key in existing_skills:
                        print(f"\n[Already have a story for: {skill}] Skipping.")
                        continue
                    print(f"\nSkill/Experience: {skill}")
                    print(f"Question: {question}")
                    response = input("\nPlease share your story (or type 'skip' if you don't have relevant experience): ").strip()
                    
                    if response.lower() != 'skip':
                        self._save_story(skill, response, has_experience=True)
                        print("Story saved for future use!")
                    else:
                        self._save_story(skill, "No relevant experience", has_experience=False)
                        print("Noted that you don't have this experience.")
            
            return full_response
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            return None

    def apply_prompt(self, resume_text, job_description, prompt_number):
        """
        Apply a specific prompt to customize the resume
        """
        try:
            prompt = self.prompts.get(f"Prompt #{prompt_number}")
            if not prompt:
                return None, "Prompt not found"
            
            # Load existing stories
            stories = self._load_stories()
            relevant_stories = [s for s in stories["stories"] if s["has_experience"]]
            
            # Add stories to the prompt if available
            stories_context = ""
            if relevant_stories:
                stories_context = "\nAdditional Experience Stories:\n"
                for story in relevant_stories:
                    stories_context += f"\nSkill: {story['skill']}\nStory: {story['story']}\n"
            
            full_prompt = f"""
            {prompt}
            
            Resume:
            {resume_text}
            
            Job Description:
            {job_description}
            {stories_context}
            """
            
            print("\nApplying customization...")
            print("Response:")
            
            # Use streaming API
            stream = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer and ATS optimization expert."},
                    {"role": "user", "content": full_prompt}
                ],
                stream=True
            )
            
            # Collect the full response while showing it in real-time
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print("\n")  # Add a newline after the response
            return full_response, None
            
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            return None, str(e)

    def cleanup_files(self):
        """
        Remove temporary files (timestamped files) while preserving original files
        """
        print("\nCleaning up temporary files...")
        
        # Clean up resumes
        if os.path.exists(self.resumes_dir):
            for filename in os.listdir(self.resumes_dir):
                # Keep original_resume.txt and skip non-timestamped files
                if filename == "original_resume.txt" or not re.match(r'.*_\d{8}_\d{6}\.txt$', filename):
                    continue
                filepath = os.path.join(self.resumes_dir, filename)
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except Exception as e:
                    print(f"Error removing {filepath}: {str(e)}")
        
        # Clean up job descriptions
        if os.path.exists(self.job_descriptions_dir):
            for filename in os.listdir(self.job_descriptions_dir):
                # Skip non-timestamped files
                if not re.match(r'.*_\d{8}_\d{6}\.txt$', filename):
                    continue
                filepath = os.path.join(self.job_descriptions_dir, filename)
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except Exception as e:
                    print(f"Error removing {filepath}: {str(e)}")
        
        print("Cleanup complete!")

    def interpret_user_intent(self, user_message, last_result, next_prompt_summary=None):
        """
        Use OpenAI to interpret the user's intent: refine, move on, or clarify.
        Returns a dict: {"action": "refine"/"move_on"/"clarify", "refinement": str or None}
        """
        system_prompt = (
            "You are an assistant helping a user customize their resume. "
            "Given the user's message, determine if they want to refine the previous result, move on to the next section, or if their intent is unclear. "
            "If they want to refine, extract their refinement instruction. "
            "If they want to move on, return a signal to continue. "
            "If unclear, ask for clarification. "
            "Respond in JSON format: {\"action\": \"refine\"/\"move_on\"/\"clarify\", \"refinement\": <refinement or null>}"
        )
        user_prompt = f"Previous result:\n{last_result[:1000]}\n\nUser message:\n{user_message}"
        if next_prompt_summary:
            user_prompt += f"\n\nThe next section is: {next_prompt_summary[:200]}"
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        import json as pyjson
        try:
            content = response.choices[0].message.content
            result = pyjson.loads(content)
            return result
        except Exception:
            # Fallback: if parsing fails, ask for clarification
            return {"action": "clarify", "refinement": None}

def main():
    # Print banner
    print("Welcome to the Applygorithminator - Your AI-Powered Resume Customization Tool!")
    print("=" * 80 + "\n")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Applygorithminator - AI-Powered Resume Customization Tool')
    parser.add_argument('--cleanup', action='store_true', help='Clean up temporary files (timestamped files)')
    args = parser.parse_args()

    # Create customizer instance
    customizer = Applygorithminator()
    
    # Handle cleanup if requested
    if args.cleanup:
        customizer.cleanup_files()
        return
    
    # Test API connection first
    if customizer.test_api_connection():
        print("\nAPI key is working correctly! You can now use the Applygorithminator.")
        
        # Example usage with file paths
        resume_path = input("\nEnter the path to your resume file (or press Enter to use default): ").strip()
        job_description_path = input("Enter the path to the job description file (or press Enter to use default): ").strip()
        
        # Use default paths if none provided
        if not resume_path:
            resume_path = os.path.join(customizer.resumes_dir, "original_resume.txt")
        if not job_description_path:
            job_description_path = os.path.join(customizer.job_descriptions_dir, "job_description.txt")
        
        try:
            resume_text = customizer.read_file(resume_path)
            job_description = customizer.read_file(job_description_path)
            
            # First, analyze the fit
            fit_analysis = customizer.analyze_fit(resume_text, job_description)
            if fit_analysis:
                proceed = input("\nWould you like to proceed with resume customization? (y/n): ").strip().lower()
                if proceed == 'y':
                    current_resume = resume_text
                    prompt_keys = [f"Prompt #{i}" for i in range(1, 9) if f"Prompt #{i}" in customizer.prompts]
                    for idx, prompt_key in enumerate(prompt_keys):
                        prompt_num = int(prompt_key.split('#')[1])
                        next_prompt = customizer.prompts[prompt_keys[idx + 1]] if idx + 1 < len(prompt_keys) else None
                        while True:
                            print(f"\n\n=== Applying {prompt_key} ===")
                            print(f"Prompt: {customizer.prompts[prompt_key][:100]}...")
                            result, error = customizer.apply_prompt(current_resume, job_description, prompt_num)
                            if result:
                                result_path = customizer.save_resume(result, is_original=False)
                                print(f"\nSaved to: {result_path}")
                                # Conversational user prompt
                                print("\nHow would you like to proceed?\nYou can ask for a refinement (e.g., 'Can you add...'), or say 'That looks good, let's move on.'")
                                user_message = input("Your input: ").strip()
                                intent = customizer.interpret_user_intent(user_message, result, next_prompt)
                                if intent["action"] == "refine" and intent["refinement"]:
                                    # Re-run the same prompt with the user's refinement as extra context
                                    result, error = customizer.apply_prompt(
                                        current_resume + "\n\n[User refinement/additional info:]\n" + intent["refinement"],
                                        job_description,
                                        prompt_num
                                    )
                                    if result:
                                        result_path = customizer.save_resume(result, is_original=False)
                                        print(f"\nRefined result saved to: {result_path}")
                                        current_resume = result
                                    else:
                                        print(f"\nError during refinement: {error}")
                                    # Loop again for further user input
                                    continue
                                elif intent["action"] == "move_on":
                                    current_resume = result
                                    if next_prompt:
                                        print(f"\nMoving on to the next section, which is:\n{next_prompt[:100]}...")
                                    else:
                                        print("\nCustomization complete!")
                                    break
                                else:
                                    print("\nSorry, I didn't understand. Please clarify your instruction.")
                                    continue
                            else:
                                print(f"\nError applying prompt: {error}")
                                return
                else:
                    print("\nResume customization skipped.")
        except FileNotFoundError as e:
            print(f"\nError: {str(e)}")
            print("Please make sure the files exist and try again.")
    else:
        print("\nPlease check your API key and try again.")

if __name__ == "__main__":
    main() 