from ai_ticket_classifier.models import TicketClassification
from ai_ticket_classifier.validator import validate_classification


class TestValidateClassification:
    def test_valid_json_returns_model(self):
        result = validate_classification(
            """
            {
                "category": "TECHNICAL",
                "priority": "HIGH",
                "sentiment": "NEGATIVE",
                "summary": "The app crashes on launch.",
                "suggested_team": "Engineering",
                "confidence": 0.91
            }
            """
        )

        assert isinstance(result, TicketClassification)

    def test_invalid_json_returns_none(self):
        assert validate_classification("not json") is None

    def test_invalid_enum_returns_none(self):
        result = validate_classification(
            """
            {
                "category": "UNKNOWN",
                "priority": "HIGH",
                "sentiment": "NEGATIVE",
                "summary": "The app crashes on launch.",
                "suggested_team": "Engineering",
                "confidence": 0.91
            }
            """
        )

        assert result is None

    def test_out_of_range_confidence_returns_none(self):
        result = validate_classification(
            """
            {
                "category": "TECHNICAL",
                "priority": "HIGH",
                "sentiment": "NEGATIVE",
                "summary": "The app crashes on launch.",
                "suggested_team": "Engineering",
                "confidence": 1.5
            }
            """
        )

        assert result is None

    def test_summary_too_long_returns_none(self):
        result = validate_classification(
            """
            {
                "category": "TECHNICAL",
                "priority": "HIGH",
                "sentiment": "NEGATIVE",
                "summary": "This summary is deliberately made longer than one hundred characters to trigger validation failure in Pydantic.",
                "suggested_team": "Engineering",
                "confidence": 0.91
            }
            """
        )

        assert result is None