from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    __table_args__ = (
        UniqueConstraint(
            "account_reference",
            name="uq_bank_accounts_account_reference",
        ),
        CheckConstraint(
            "bank_account_id ~ '^BANKACC-ENT-[0-9]{6}-[0-9]{3}$'",
            name="ck_bank_accounts_id_format",
        ),
        CheckConstraint(
            "length(trim(bank_name)) > 0",
            name="ck_bank_accounts_bank_name",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_bank_accounts_currency_format",
        ),
        CheckConstraint(
            "opening_balance >= 0",
            name="ck_bank_accounts_opening_balance",
        ),
        CheckConstraint(
            "account_status IN ('ACTIVE', 'INACTIVE', 'CLOSED')",
            name="ck_bank_accounts_status",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_bank_accounts_timestamps",
        ),
    )

    bank_account_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )

    entity_id: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("legal_entities.entity_id"),
        nullable=False,
        index=True,
    )

    bank_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    account_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    opening_balance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    account_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
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
