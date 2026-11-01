from datetime import date, datetime
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


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    __table_args__ = (
        CheckConstraint(
            "ledger_entry_id ~ '^LED-[0-9]{4}-[0-9]{8}$'",
            name="ck_ledger_entries_id_format",
        ),
        CheckConstraint(
            "transaction_date <= posting_date",
            name="ck_ledger_entries_date_order",
        ),
        CheckConstraint(
            "transaction_type IN ('INFLOW', 'OUTFLOW')",
            name="ck_ledger_entries_transaction_type",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_ledger_entries_positive_amount",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_ledger_entries_currency_format",
        ),
    )

    ledger_entry_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    bank_account_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("bank_accounts.bank_account_id"),
        nullable=False,
        index=True,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    posting_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
