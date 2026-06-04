import json

from ai_ticket_classifier import prompt_builder
from ai_ticket_classifier.validator import validate_classification

def call_llm_api(prompt: str) -> str:
    """
    Placeholder for LLM API call. Replace with your actual LLM integration.
    Should return a JSON string matching the TicketClassification schema.
    """
    return json.dumps({
        "category": "TECHNICAL",
        "priority": "HIGH",
        "sentiment": "NEGATIVE",
        "summary": "The user is reporting a technical issue affecting their experience.",
        "suggested_team": "Engineering",
        "confidence": 0.91
    })

def classify_ticket(redacted_text: str, prompt_version: str) -> tuple:
    """
    Classify a support ticket using the LLM.
    Args:
        redacted_text (str): The ticket text (PII redacted).
        prompt_version (str): The prompt template version (e.g., 'v1', 'v2').
    Returns:
        tuple: (category, priority, sentiment, confidence)
    """
    prompt = prompt_builder.build_prompt(redacted_text, prompt_version)

    llm_response = call_llm_api(prompt)

    classification = validate_classification(llm_response)
    if classification is None:
        raise RuntimeError(f"Failed to parse LLM response:\nResponse: {llm_response}")

    return (
        classification.category.value,
        classification.priority.value,
        classification.sentiment.value,
        classification.confidence,
    )