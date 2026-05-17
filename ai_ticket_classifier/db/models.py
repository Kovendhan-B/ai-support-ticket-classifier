import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY

class Base(DeclarativeBase):
    pass

class RawTicket(Base):
    __tablename__ = "raw_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="raw_ticket", uselist=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_tickets.id"), nullable=False)
    redacted_text: Mapped[str] = mapped_column(Text, nullable=False)
    injection_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    pii_types_found: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    raw_ticket: Mapped["RawTicket"] = relationship("RawTicket", back_populates="ticket")
    classification: Mapped["Classification"] = relationship("Classification", back_populates="ticket", uselist=False)
    redaction_logs: Mapped[list["RedactionLog"]] = relationship("RedactionLog", back_populates="ticket")
    cost_records: Mapped[list["CostRecord"]] = relationship("CostRecord", back_populates="ticket")
    embeddings: Mapped[list["TicketEmbedding"]] = relationship("TicketEmbedding", back_populates="ticket")


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    sentiment: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_team: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    low_confidence_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="classification")


class RedactionLog(Base):
    __tablename__ = "redaction_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    pii_type: Mapped[str] = mapped_column(String, nullable=False)
    redacted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="redaction_logs")


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="cost_records")


class TicketEmbedding(Base):
    __tablename__ = "ticket_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    chroma_doc_id: Mapped[str] = mapped_column(String, nullable=False)
    collection_name: Mapped[str] = mapped_column(String, nullable=False)
    embedded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="embeddings")