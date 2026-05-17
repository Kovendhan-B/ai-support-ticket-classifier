import re
import logging
from ai_ticket_classifier.models import RedactionResult

#layer 1
PATTERNS = {
    "CARD": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
    "IP": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}

#layer 2
try:
    from presidio_analyzer import AnalyzerEngine
    analyzer = AnalyzerEngine()
    logging.info("Presidio AnalyzerEngine loaded successfully.")
except Exception:
    analyzer = None
    logging.warning(
        "Presidio not available — Layer 2 (NER name detection) will be skipped. "
        "Ensure presidio-analyzer and en_core_web_lg are installed."
    )


def redact_pii(text: str) -> RedactionResult:
    pii_types_found = set()

    # --- Layer 1: Regex ---
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            pii_types_found.add(label)
            text = pattern.sub(f"[{label}]", text)

    # --- Layer 2: Presidio (PERSON → [NAME]) ---
    if analyzer is not None:
        results = analyzer.analyze(text=text, language="en", entities=["PERSON"])
        if results:
            pii_types_found.add("NAME")
            # Replace from back to front so character positions stay valid
            for result in sorted(results, key=lambda r: r.start, reverse=True):
                text = text[:result.start] + "[NAME]" + text[result.end:]

    return RedactionResult(
        redacted_text=text,
        pii_types_found=list(pii_types_found)
    )


if __name__ == "__main__":
    sample = "John Smith emailed me at john@example.com or call 555-123-4567. Server IP: 192.168.1.1"
    result = redact_pii(sample)
    print("Redacted :", result.redacted_text)
    print("PII Found:", result.pii_types_found)