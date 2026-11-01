
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    changed_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="SYSTEM",
    )

    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('LegalEntity', 'BankAccount', "
            "'Receivable', 'Payable', 'ForecastRun', "
            "'LiquidityScenario')",
            name="ck_status_history_entity_type",
        ),
        Index(
            "ix_status_history_record",
            "entity_type",
            "record_id",
        ),
        Index(
            "ix_status_history_changed_at",
            "changed_at",
        ),
    )
