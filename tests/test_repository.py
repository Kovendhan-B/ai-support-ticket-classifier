

import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from ai_ticket_classifier.config import DATABASE_URL
from ai_ticket_classifier.db.models import Base
from ai_ticket_classifier.db.repository import (
    insert_raw_ticket,
    insert_ticket,
    insert_classification,
    insert_redaction_logs,
    insert_cost_record,
    insert_embedding,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """
    Create one engine for the whole test session.
    scope="session" means this runs once, not once per test.
    """
    return create_engine(DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def create_tables(engine):
    """
    Ensure all tables exist before any test runs.
    autouse=True means it runs automatically without needing to be called.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Nothing to teardown — we keep the schema in place


@pytest.fixture()
def db(engine) -> Session:
    """
    Provide a database session that is ROLLED BACK after every test.

    How it works:
    1. Start a top-level connection and BEGIN a transaction.
    2. Bind the session to that connection (so it joins the same transaction).
    3. Yield the session to the test.
    4. After the test finishes, ROLLBACK the transaction — all inserts vanish.

    This is the standard pattern for fast, clean database tests.
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSession = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestingSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helper: shared classification dict used across tests
# ---------------------------------------------------------------------------

SAMPLE_CLASSIFICATION = {
    "category": "billing",
    "priority": "high",
    "sentiment": "negative",
    "summary": "User cannot download their invoice.",
    "suggested_team": "billing-team",
    "confidence": 0.95,
    "is_fallback": False,
    "low_confidence_flagged": False,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInsertRawTicket:
    def test_returns_uuid(self, db):
        """insert_raw_ticket should return a valid UUID."""
        raw_id = insert_raw_ticket(db, "My laptop is broken!")
        assert isinstance(raw_id, uuid.UUID)

    def test_default_source_is_manual(self, db):
        """When no source is provided, source should default to 'manual'."""
        from ai_ticket_classifier.db.models import RawTicket
        raw_id = insert_raw_ticket(db, "Test ticket")
        row = db.get(RawTicket, raw_id)
        assert row.source == "manual"

    def test_custom_source(self, db):
        """Custom source should be stored correctly."""
        from ai_ticket_classifier.db.models import RawTicket
        raw_id = insert_raw_ticket(db, "Test ticket", source="email")
        row = db.get(RawTicket, raw_id)
        assert row.source == "email"

    def test_text_is_stored(self, db):
        """The raw text should be saved as-is."""
        from ai_ticket_classifier.db.models import RawTicket
        text = "User cannot log in to the portal."
        raw_id = insert_raw_ticket(db, text)
        row = db.get(RawTicket, raw_id)
        assert row.raw_text == text


class TestInsertTicket:
    def test_returns_uuid(self, db):
        """insert_ticket should return a valid UUID."""
        raw_id = insert_raw_ticket(db, "Raw ticket text")
        ticket_id = insert_ticket(db, raw_id, "Redacted text", ["EMAIL"])
        assert isinstance(ticket_id, uuid.UUID)

    def test_links_to_raw_ticket(self, db):
        """Ticket's raw_ticket_id FK should point to the correct raw ticket."""
        from ai_ticket_classifier.db.models import Ticket
        raw_id = insert_raw_ticket(db, "Original text")
        ticket_id = insert_ticket(db, raw_id, "Clean text", [])
        row = db.get(Ticket, ticket_id)
        assert row.raw_ticket_id == raw_id

    def test_pii_types_stored(self, db):
        """pii_types_found list should be stored correctly."""
        from ai_ticket_classifier.db.models import Ticket
        raw_id = insert_raw_ticket(db, "Contains PII")
        pii_types = ["EMAIL", "PHONE_NUMBER"]
        ticket_id = insert_ticket(db, raw_id, "Redacted", pii_types)
        row = db.get(Ticket, ticket_id)
        assert row.pii_types_found == pii_types

    def test_default_status_is_processing(self, db):
        """Default status should be 'processing'."""
        from ai_ticket_classifier.db.models import Ticket
        raw_id = insert_raw_ticket(db, "Ticket")
        ticket_id = insert_ticket(db, raw_id, "Clean", [])
        row = db.get(Ticket, ticket_id)
        assert row.status == "processing"

    def test_injection_detected_flag(self, db):
        """injection_detected flag should be stored correctly."""
        from ai_ticket_classifier.db.models import Ticket
        raw_id = insert_raw_ticket(db, "Suspicious ticket")
        ticket_id = insert_ticket(db, raw_id, "Redacted", [], injection_detected=True)
        row = db.get(Ticket, ticket_id)
        assert row.injection_detected is True


class TestInsertClassification:
    def test_returns_uuid(self, db):
        """insert_classification should return a valid UUID."""
        raw_id = insert_raw_ticket(db, "Ticket")
        ticket_id = insert_ticket(db, raw_id, "Redacted", [])
        cl_id = insert_classification(db, ticket_id, SAMPLE_CLASSIFICATION, "v1")
        assert isinstance(cl_id, uuid.UUID)

    def test_fields_are_stored_correctly(self, db):
        """All fields from the classification dict should be saved correctly."""
        from ai_ticket_classifier.db.models import Classification
        raw_id = insert_raw_ticket(db, "Billing issue")
        ticket_id = insert_ticket(db, raw_id, "Billing issue", [])
        cl_id = insert_classification(db, ticket_id, SAMPLE_CLASSIFICATION, "v1")
        row = db.get(Classification, cl_id)

        assert row.category == "billing"
        assert row.priority == "high"
        assert row.sentiment == "negative"
        assert row.confidence == 0.95
        assert row.prompt_version == "v1"
        assert row.is_fallback is False
        assert row.low_confidence_flagged is False


class TestInsertRedactionLogs:
    def test_creates_one_row_per_pii_type(self, db):
        """One RedactionLog row should be created for each PII type."""
        from ai_ticket_classifier.db.models import RedactionLog
        from sqlalchemy import select

        raw_id = insert_raw_ticket(db, "Contains PII")
        ticket_id = insert_ticket(db, raw_id, "Redacted", ["EMAIL", "PHONE_NUMBER"])
        insert_redaction_logs(db, ticket_id, ["EMAIL", "PHONE_NUMBER"])

        rows = db.execute(
            select(RedactionLog).where(RedactionLog.ticket_id == ticket_id)
        ).scalars().all()

        assert len(rows) == 2
        pii_types_stored = {r.pii_type for r in rows}
        assert pii_types_stored == {"EMAIL", "PHONE_NUMBER"}

    def test_no_logs_for_empty_pii(self, db):
        """No RedactionLog rows should be created if pii_types is empty."""
        from ai_ticket_classifier.db.models import RedactionLog
        from sqlalchemy import select

        raw_id = insert_raw_ticket(db, "Clean ticket")
        ticket_id = insert_ticket(db, raw_id, "Clean ticket", [])
        insert_redaction_logs(db, ticket_id, [])

        rows = db.execute(
            select(RedactionLog).where(RedactionLog.ticket_id == ticket_id)
        ).scalars().all()

        assert len(rows) == 0


class TestInsertCostRecord:
    def test_cost_record_fields(self, db):
        """Cost record should store tokens and calculated total correctly."""
        from ai_ticket_classifier.db.models import CostRecord
        from sqlalchemy import select

        raw_id = insert_raw_ticket(db, "Ticket")
        ticket_id = insert_ticket(db, raw_id, "Redacted", [])
        insert_cost_record(db, ticket_id, prompt_tokens=100, completion_tokens=50,
                           estimated_cost_usd=0.00025, model="gpt-4o-mini")

        row = db.execute(
            select(CostRecord).where(CostRecord.ticket_id == ticket_id)
        ).scalar_one()

        assert row.prompt_tokens == 100
        assert row.completion_tokens == 50
        assert row.total_tokens == 150  # auto-calculated in repository
        assert row.estimated_cost_usd == 0.00025
        assert row.model == "gpt-4o-mini"


class TestInsertEmbedding:
    def test_embedding_fields(self, db):
        """Embedding should store chroma_doc_id and collection_name."""
        from ai_ticket_classifier.db.models import TicketEmbedding
        from sqlalchemy import select
        from ai_ticket_classifier.config import CHROMA_COLLECTION_NAME

        raw_id = insert_raw_ticket(db, "Ticket")
        ticket_id = insert_ticket(db, raw_id, "Redacted", [])
        chroma_doc_id = str(uuid.uuid4())
        insert_embedding(db, ticket_id, chroma_doc_id)

        row = db.execute(
            select(TicketEmbedding).where(TicketEmbedding.ticket_id == ticket_id)
        ).scalar_one()

        assert row.chroma_doc_id == chroma_doc_id
        assert row.collection_name == CHROMA_COLLECTION_NAME
