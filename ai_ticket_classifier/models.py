from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    BILLING = "BILLING"
    TECHNICAL = "TECHNICAL"
    ACCOUNT = "ACCOUNT"
    SHIPPING = "SHIPPING"
    GENERAL = "GENERAL"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketSentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    FRUSTRATED = "FRUSTRATED"

class TicketClassification(BaseModel):
    category: TicketCategory = Field(description="The category of the ticket")
    priority: TicketPriority = Field(description="The priority of the ticket")
    sentiment: TicketSentiment = Field(description="The sentiment of the user")
    summary: str = Field(description="A brief summary of the issue", max_length=100)
    suggested_team: str = Field(description="The team best suited to handle this ticket")
    confidence: float = Field(description="Confidence score of the classification", ge=0, le=1)

class RedactionResult(BaseModel):
    redacted_text: str = Field(description="The text with PII redacted")
    pii_types_found: List[str] = Field(description="List of PII types found in the text")

class PipelineOutput(BaseModel):
    original_ticket: str = Field(description="The original user ticket text")
    redaction: RedactionResult = Field(description="Redaction process results")
    classification: TicketClassification = Field(description="Classification results")
