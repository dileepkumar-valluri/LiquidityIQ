from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class Receivable(Base):
    __tablename__ = "receivables"

    __table_args__ = (
        CheckConstraint(
            "receivable_id ~ '^REC-[0-9]{4}-[0-9]{6}$'",
            name="ck_receivables_id_format",
        ),
        CheckConstraint(
            "length(trim(customer_reference)) > 0",
            name="ck_receivables_customer_reference",
        ),
        CheckConstraint(
            "due_date >= invoice_date",
            name="ck_receivables_date_order",
        ),
        CheckConstraint(
            "expected_amount > 0",
            name="ck_receivables_positive_amount",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_receivables_currency_format",
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'CANCELLED')",
            name="ck_receivables_status",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_receivables_timestamps",
        ),
    )

    receivable_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("legal_entities.entity_id"),
        nullable=False,
        index=True,
    )

    customer_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    expected_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'SCHEDULED'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
