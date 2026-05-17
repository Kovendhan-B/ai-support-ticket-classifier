import uuid
from sqlalchemy.orm import Session
from ai_ticket_classifier.db.models import (
    RawTicket, Ticket, Classification, RedactionLog, CostRecord, TicketEmbedding
)
from ai_ticket_classifier.config import CHROMA_COLLECTION_NAME


def insert_raw_ticket(db: Session, text: str, source: str = "manual") -> uuid.UUID:
    raw = RawTicket(raw_text=text, source=source)
    db.add(raw)
    db.commit()
    db.refresh(raw)
    return raw.id

def insert_ticket(
    db: Session,
    raw_ticket_id: uuid.UUID,
    redacted_text: str,
    pii_types: list[str],
    injection_detected: bool = False,
    status: str = "processing"
) -> uuid.UUID:
    ticket = Ticket(
        raw_ticket_id=raw_ticket_id,
        redacted_text=redacted_text,
        pii_types_found=pii_types,
        injection_detected=injection_detected,
        status=status
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket.id

def insert_classification(
    db: Session,
    ticket_id: uuid.UUID,
    classification_dict: dict,
    prompt_version: str
) -> uuid.UUID:
    cl = Classification(
        ticket_id=ticket_id,
        category=classification_dict["category"],
        priority=classification_dict["priority"],
        sentiment=classification_dict["sentiment"],
        summary=classification_dict["summary"],
        suggested_team=classification_dict["suggested_team"],
        confidence=classification_dict["confidence"],
        is_fallback=classification_dict.get("is_fallback", False),
        low_confidence_flagged=classification_dict.get("low_confidence_flagged", False),
        prompt_version=prompt_version
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl.id

def insert_redaction_logs(
    db: Session,
    ticket_id: uuid.UUID,
    pii_types: list[str]
) -> None:
    for pii_type in pii_types:
        log = RedactionLog(ticket_id=ticket_id, pii_type=pii_type)
        db.add(log)
    db.commit()

def insert_cost_record(
    db: Session,
    ticket_id: uuid.UUID,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost_usd: float,
    model: str
) -> None:
    record = CostRecord(
        ticket_id=ticket_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost_usd=estimated_cost_usd,
        model=model
    )
    db.add(record)
    db.commit()

def insert_embedding(
    db: Session,
    ticket_id: uuid.UUID,
    chroma_doc_id: str
) -> None:
    embedding = TicketEmbedding(
        ticket_id=ticket_id,
        chroma_doc_id=chroma_doc_id,
        collection_name=CHROMA_COLLECTION_NAME
    )
    db.add(embedding)
    db.commit()
