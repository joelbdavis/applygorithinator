from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from config import OPENAI_MODEL, OPENAI_MAX_TOKENS

job_fit_prompt = PromptTemplate(
    input_variables=["combined_experience", "job_description"],
    template="""
Compare my combined experience (resume plus additional stories) to this job description and identify:
1. Key skills and experiences that are well-aligned
2. Important skills or experiences from the job description that are missing or could be strengthened (i.e., not covered by either the resume or the stories)
3. For each gap, generate a specific behavioral question in the format 'Tell me about a time when you [specific scenario related to the missing skill/experience]'

IMPORTANT: Before listing a skill or experience as a gap, carefully check both the resume and all provided stories. If any story clearly addresses a required skill or experience, do NOT list it as a gap, even if it is not in the resume. Only list true gaps that are not covered by either the resume or any of the stories.

Format your response as follows:
ALIGNMENT:
[List aligned skills/experiences]

GAPS:
Return the GAPS section as a JSON array, where each item is an object with "skill" and "question" fields. For example:
GAPS:
[
  {{"skill": "Hands-on Leadership", "question": "Tell me about a time when you had to take on a player/coach role in leading a team."}},
  {{"skill": "Technologist", "question": "Can you share a specific scenario where you embraced technology to up-level your team's productivity and impact?"}}
]
"""
)

def run_job_fit_chain(combined_experience, job_description, openai_api_key):
    llm = ChatOpenAI(api_key=openai_api_key, model=OPENAI_MODEL, temperature=0.2, max_tokens=OPENAI_MAX_TOKENS)
    chain = job_fit_prompt | llm
    result = chain.invoke({
        "combined_experience": combined_experience,
        "job_description": job_description
    })
    return result 