
import re
import pytest
from unittest.mock import MagicMock, patch

from ai_ticket_classifier.models import RedactionResult


def _redact(text: str):
    """Import-fresh call so module-level state changes (analyzer mock) take effect."""
    from ai_ticket_classifier import pii_redactor
    return pii_redactor.redact_pii(text)


class TestReturnType:
    def test_returns_redaction_result_instance(self):
        result = _redact("Hello, no PII here.")
        assert isinstance(result, RedactionResult)

    def test_clean_text_has_empty_pii_list(self):
        result = _redact("Hello, no PII here.")
        assert result.pii_types_found == []

    def test_clean_text_is_unchanged(self):
        text = "Hello, no PII here."
        result = _redact(text)
        assert result.redacted_text == text

    def test_empty_string(self):
        result = _redact("")
        assert result.redacted_text == ""
        assert result.pii_types_found == []


class TestEmailRedaction:
    def test_simple_email(self):
        result = _redact("Contact me at user@example.com please.")
        assert "[EMAIL]" in result.redacted_text
        assert "user@example.com" not in result.redacted_text
        assert "EMAIL" in result.pii_types_found

    def test_email_with_plus_tag(self):
        result = _redact("Send to user+tag@sub.domain.org")
        assert "[EMAIL]" in result.redacted_text
        assert "EMAIL" in result.pii_types_found

    def test_email_with_dots_in_local(self):
        result = _redact("Email: first.last@company.co.uk")
        assert "[EMAIL]" in result.redacted_text
        assert "EMAIL" in result.pii_types_found

    def test_multiple_emails(self):
        result = _redact("a@a.com and b@b.com")
        assert result.redacted_text.count("[EMAIL]") == 2
        assert "EMAIL" in result.pii_types_found

    def test_no_email(self):
        result = _redact("No contact info here.")
        assert "EMAIL" not in result.pii_types_found



class TestPhoneRedaction:
    @pytest.mark.parametrize("phone", [
        "555-123-4567",
        "555.123.4567",
        "555 123 4567",
        "(555) 123-4567",
        "+1-555-123-4567",
        "+1 555 123 4567",
        "5551234567",
    ])
    def test_common_phone_formats(self, phone):
        result = _redact(f"Call me at {phone} anytime.")
        assert "[PHONE]" in result.redacted_text
        assert "PHONE" in result.pii_types_found

    def test_phone_not_in_result(self):
        result = _redact("There is no phone number here.")
        assert "PHONE" not in result.pii_types_found


class TestCardRedaction:
    @pytest.mark.parametrize("card", [
        "4111111111111111",          # no separator
        "4111 1111 1111 1111",       # spaces
        "4111-1111-1111-1111",       # hyphens
    ])
    def test_card_number_formats(self, card):
        result = _redact(f"My card is {card}.")
        assert "[CARD]" in result.redacted_text
        assert "CARD" in result.pii_types_found

    def test_no_card(self):
        result = _redact("I did not include a card number.")
        assert "CARD" not in result.pii_types_found



class TestIPRedaction:
    @pytest.mark.parametrize("ip", [
        "192.168.1.1",
        "10.0.0.255",
        "8.8.8.8",
        "172.16.254.1",
    ])
    def test_valid_ip_formats(self, ip):
        result = _redact(f"Server at {ip} is down.")
        assert "[IP]" in result.redacted_text
        assert "IP" in result.pii_types_found

    def test_no_ip(self):
        result = _redact("No server address mentioned.")
        assert "IP" not in result.pii_types_found


class TestMultiplePIITypes:
    def test_email_and_phone(self):
        result = _redact("Reach me at alice@example.com or 555-000-1234.")
        assert "EMAIL" in result.pii_types_found
        assert "PHONE" in result.pii_types_found
        assert "alice@example.com" not in result.redacted_text

    def test_all_four_regex_types(self):
        text = (
            "Email: x@x.com | Phone: 555-000-1234 | "
            "Card: 4111-1111-1111-1111 | IP: 192.168.0.1"
        )
        result = _redact(text)
        for label in ("EMAIL", "PHONE", "CARD", "IP"):
            assert label in result.pii_types_found, f"{label} should be detected"

    def test_pii_types_found_no_duplicates(self):
        # Two emails → only one "EMAIL" entry in pii_types_found
        result = _redact("a@a.com and b@b.com")
        assert result.pii_types_found.count("EMAIL") == 1


class TestPresidioLayer:
    """
    We always mock the module-level `analyzer` so tests are hermetic and fast,
    regardless of whether spaCy / Presidio is actually installed.
    """

    def _make_fake_result(self, start: int, end: int):
        r = MagicMock()
        r.start = start
        r.end = end
        return r

    def test_person_name_is_replaced_when_presidio_available(self):
        fake_result = self._make_fake_result(0, 10)  # "John Smith"
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [fake_result]

        with patch("ai_ticket_classifier.pii_redactor.analyzer", mock_analyzer):
            result = _redact("John Smith called us.")

        assert "[NAME]" in result.redacted_text
        assert "NAME" in result.pii_types_found

    def test_no_person_result_does_not_add_name(self):
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = []  # Presidio found nothing

        with patch("ai_ticket_classifier.pii_redactor.analyzer", mock_analyzer):
            result = _redact("The server is down.")

        assert "NAME" not in result.pii_types_found

    def test_presidio_unavailable_skips_layer2(self):
        with patch("ai_ticket_classifier.pii_redactor.analyzer", None):
            result = _redact("John Smith called us.")

        # No NAME redaction should have occurred
        assert "NAME" not in result.pii_types_found
        assert "John Smith" in result.redacted_text  # text left as-is by layer 2

    def test_multiple_persons_replaced_back_to_front(self):
        """
        Two names at different positions; back-to-front replacement must keep
        character positions valid for the second (earlier) substitution.
        """
        # "Alice" at 0-5, "Bob" at 10-13  → sorted by start desc: Bob first
        alice = self._make_fake_result(0, 5)
        bob = self._make_fake_result(10, 13)
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [alice, bob]

        with patch("ai_ticket_classifier.pii_redactor.analyzer", mock_analyzer):
            result = _redact("Alice and Bob called.")

        assert result.redacted_text.count("[NAME]") == 2
        assert "NAME" in result.pii_types_found


class TestRealWorldTickets:
    def test_typical_support_ticket(self):
        ticket = (
            "Hi, I'm John Smith. My account email is john.smith@company.com "
            "and my phone is +1-800-555-0199. "
            "My card 4111 1111 1111 1111 was charged incorrectly. "
            "I'm connecting from 203.0.113.42."
        )
        result = _redact(ticket)

        assert "john.smith@company.com" not in result.redacted_text
        assert "4111 1111 1111 1111" not in result.redacted_text
        assert "203.0.113.42" not in result.redacted_text
        assert "[EMAIL]" in result.redacted_text
        assert "[CARD]" in result.redacted_text
        assert "[IP]" in result.redacted_text

    def test_ticket_with_no_pii(self):
        ticket = "The login button does not respond after clicking it twice."
        result = _redact(ticket)
        assert result.redacted_text == ticket
        assert result.pii_types_found == []

    def test_redacted_text_is_string(self):
        result = _redact("My email is test@test.com")
        assert isinstance(result.redacted_text, str)

    def test_pii_types_found_is_list(self):
        result = _redact("My email is test@test.com")
        assert isinstance(result.pii_types_found, list)
