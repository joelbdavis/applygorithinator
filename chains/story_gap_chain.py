from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.text_parsing import extract_json_from_llm_result, extract_llm_content, LLMJsonParseError, format_dict_list
import json
import logging

def format_stories_context(stories):
    return format_dict_list(stories, ["skill", "story"], section_title="Additional Experience Stories")

def story_answers_gap_llm(gap_skill, question, relevant_stories, openai_api_key):
    if not relevant_stories:
        return False, None, None
    # Format stories context for the LLM prompt
    stories_context = format_stories_context(relevant_stories)
    prompt = PromptTemplate(
        input_variables=["gap_skill", "question", "stories_context"],
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
{stories_context}
"""
    )
    llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo", temperature=0.0, max_tokens=300)
    chain = prompt | llm
    result = chain.invoke({
        "gap_skill": gap_skill,
        "question": question,
        "stories_context": stories_context
    })
    try:
        response_json = extract_json_from_llm_result(result)
        answered = response_json.get('answered', False)
        summary = response_json.get('summary', '')
        confidence = response_json.get('confidence', None)
        # Sanity check: if summary contains phrases indicating no match, treat as not answered
        if answered and any(phrase in summary.lower() for phrase in ["not directly addressed", "no relevant story", "not covered"]):
            answered = False
        return answered, summary, confidence
    except LLMJsonParseError as e:
        logging.error("Failed to parse LLM JSON response", exc_info=True)
        raise 