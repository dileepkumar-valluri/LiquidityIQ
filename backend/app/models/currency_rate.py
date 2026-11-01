from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class CurrencyRate(Base):
    __tablename__ = "currency_rates"

    __table_args__ = (
        UniqueConstraint(
            "base_currency",
            "quote_currency",
            "effective_date",
            name="uq_currency_rates_pair_effective_date",
        ),
        CheckConstraint(
            "currency_rate_id ~ '^FX-[0-9]{4}-[0-9]{6}$'",
            name="ck_currency_rates_id_format",
        ),
        CheckConstraint(
            "base_currency ~ '^[A-Z]{3}$' "
            "AND quote_currency ~ '^[A-Z]{3}$'",
            name="ck_currency_rates_currency_format",
        ),
        CheckConstraint(
            "base_currency <> quote_currency",
            name="ck_currency_rates_different_currencies",
        ),
        CheckConstraint(
            "exchange_rate > 0",
            name="ck_currency_rates_positive_rate",
        ),
        CheckConstraint(
            "length(trim(source)) > 0",
            name="ck_currency_rates_source",
        ),
    )

    currency_rate_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    base_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    quote_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
