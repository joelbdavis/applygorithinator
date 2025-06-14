# Resume Customizer

A Python script that uses ChatGPT to customize your resume for specific job descriptions, optimizing it for ATS systems.

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Place your resume text in a file
2. Place the job description in a file
3. Run the script:
   ```bash
   python resume_customizer.py
   ```

## Features

- Analyzes resume against job description
- Suggests ATS-friendly modifications
- Optimizes keywords and formatting
