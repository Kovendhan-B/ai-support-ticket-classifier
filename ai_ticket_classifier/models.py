from pydantic import BaseModel, Field
from typing import List

class TicketClassification(BaseModel):
    category: str = Field(description="The category of the ticket")
    priority: str = Field(description="The priority of the ticket")
    sentiment: str = Field(description="The sentiment of the user")
    summary: str = Field(description="A brief summary of the issue")
    suggested_team: str = Field(description="The team best suited to handle this ticket")
    confidence: float = Field(description="Confidence score of the classification")

class RedactionResult(BaseModel):
    redacted_text: str = Field(description="The text with PII redacted")
    pii_types_found: List[str] = Field(description="List of PII types found in the text")

class PipelineOutput(BaseModel):
    original_ticket: str = Field(description="The original user ticket text")
    redaction: RedactionResult = Field(description="Redaction process results")
    classification: TicketClassification = Field(description="Classification results")
