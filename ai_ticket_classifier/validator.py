import json

from pydantic import ValidationError

from ai_ticket_classifier.models import TicketClassification


def validate_classification(json_str: str) -> TicketClassification | None:
    try:
        parsed = json.loads(json_str)
        return TicketClassification.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        return None