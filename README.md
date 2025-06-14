# Applygorithminator

A Python tool that uses OpenAI and LangChain to analyze, customize, and optimize your resume for specific job descriptions. It identifies skill gaps, prompts you for behavioral stories, and helps you iteratively improve your job fit—all in a conversational, chat-like CLI.

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your OpenAI API key (and optionally model/max tokens):
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-3.5-turbo  # optional, default is gpt-3.5-turbo
   OPENAI_MAX_TOKENS=1500      # optional, default is 1500
   ```

## Usage

1. Place your resume text in a file (e.g., `resources/resumes/original_resume.txt`)
2. Place the job description in a file (e.g., `resources/job_descriptions/job_description.txt`)
3. Run the main script:
   ```bash
   python main.py
   ```
4. Follow the prompts to:
   - Analyze your resume vs. the job description
   - Review alignment and skill gaps
   - Provide behavioral stories for missing skills
   - Iteratively refine your resume for better job fit

## Features

- **Conversational CLI:** Chat-like flow for user input and refinement
- **Job Fit Analysis:** Uses OpenAI and LangChain to compare your resume and stories to the job description
- **Skill Gap Detection:** Identifies true gaps not covered by your resume or stories
- **Behavioral Story Collection:** Prompts you for stories to fill gaps, and remembers them for future runs
- **Confidence Scoring:** LLM rates how well your stories match each gap
- **Session Logging:** All analysis, inputs, and outputs are logged for review
- **Configurable Model/Token Limit:** Set via environment variables for cost control
- **Cleanup Command:** Remove temporary/session files easily

## Project Structure

- `main.py` — Main CLI workflow
- `chains/` — LangChain chains (e.g., job fit analysis)
- `resources/` — Resumes, job descriptions, and user stories (gitignored)
- `sessions/` — Session logs (gitignored)
- `config.py` — Environment/config management
- `requirements.txt` — Python dependencies

---

**Note:** This project is under active development. Contributions and feedback are welcome!
