from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String


class Base(DeclarativeBase):
    pass


class RawTicket(Base):
    __tablename__ = "raw_tickets"

    id: Mapped[str] = mapped_column(
        primary_key=True
    )

    raw_text: Mapped[str] = mapped_column(
        String,
        nullable=False
    )