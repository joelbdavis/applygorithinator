import os
import datetime
import logging

class SessionLogger:
    def __init__(self, session_file=None, sessions_dir="sessions"):
        if session_file is None:
            self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(sessions_dir, exist_ok=True)
            self.session_file = os.path.join(sessions_dir, f"session_{self.timestamp}.txt")
        else:
            self.session_file = session_file
            self.timestamp = None  # Could extract from filename if needed
        self.entries = []

    def log(self, message):
        self.entries.append(message)

    def log_story_prompt(self, skill, question):
        self.entries.append(f"\nSkill/Experience: {skill}\nQuestion: {question}")

    def log_story_response(self, skill, question, response):
        self.entries.append(f"\nSkill/Experience: {skill}\nQuestion: {question}\nStory: {response}")

    def log_story_already_answered(self, skill, summary):
        self.entries.append(f"\n[Story already answers: {skill}]\n{summary}")

    def log_no_experience(self, skill, question):
        self.entries.append(f"\nSkill/Experience: {skill}\nQuestion: {question}\nStory: No relevant experience")

    def log_output(self, output):
        self.entries.append(output + "\n")

    def log_session_header(self, resume_path, job_description_path, resume_text, job_description):
        self.log("=== Applygorithminator Session Log ===")
        self.log(f"Timestamp: {self.timestamp}")
        self.log("--- Resume ---")
        self.log(f"file: {resume_path}")
        self.log(resume_text + "\n")
        self.log("\n--- Job Description ---")
        self.log(f"file: {job_description_path}\n")
        self.log(job_description + "\n")
        self.log("\n--- Job Fit Analysis ---")

    def save(self):
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        with open(self.session_file, "w") as f:
            for entry in self.entries:
                f.write(entry + "\n") 