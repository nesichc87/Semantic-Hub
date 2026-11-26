"""Database model of the source catalog (ADR-001).

The catalog holds configuration, status and load results of the sources,
never their triples (ADR-003).
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


SOURCE_STATUSES = (
    "proposed",
    "approved",
    "loading",
    "active",
    "error",
    "rejected",
    "disabled",
)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    type: Mapped[str] = mapped_column(String(20))
    config: Mapped[dict] = mapped_column(JSON)
    prefixes: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
    status_reason: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceLoad(Base):
    __tablename__ = "source_loads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(10))
    message: Mapped[str | None] = mapped_column(Text)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())