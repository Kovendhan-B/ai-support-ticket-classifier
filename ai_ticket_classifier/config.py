from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

ACTIVE_PROMPT_VERSION = os.getenv(
    "ACTIVE_PROMPT_VERSION",
    "v1"
)

TEMPERATURE = float(
    os.getenv("TEMPERATURE", 0)
)

SEED = int(
    os.getenv("SEED", 42)
)

CHROMA_COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION_NAME",
    "support_tickets"
)