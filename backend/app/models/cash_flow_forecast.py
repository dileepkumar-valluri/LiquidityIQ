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


class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"

    __table_args__ = (
        CheckConstraint(
            "forecast_item_id ~ '^CF-[0-9]{4}-[0-9]{6}$'",
            name="ck_cash_flow_forecasts_id_format",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_cash_flow_forecasts_amount",
        ),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_cash_flow_forecasts_currency",
        ),
        CheckConstraint(
            "flow_type IN ('INFLOW', 'OUTFLOW')",
            name="ck_cash_flow_forecasts_flow_type",
        ),
        CheckConstraint(
            "forecast_status IN ('EXPECTED', 'DELAYED', 'CANCELLED')",
            name="ck_cash_flow_forecasts_status",
        ),
        CheckConstraint(
            "NOT (receivable_id IS NOT NULL AND payable_id IS NOT NULL)",
            name="ck_cash_flow_forecasts_source_reference",
        ),
    )

    forecast_item_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    forecast_run_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("forecast_runs.forecast_run_id"),
        nullable=False,
        index=True,
    )

    bank_account_id: Mapped[str | None] = mapped_column(
        String(30),
        ForeignKey("bank_accounts.bank_account_id"),
        nullable=True,
    )

    receivable_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("receivables.receivable_id"),
        nullable=True,
    )

    payable_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("payables.payable_id"),
        nullable=True,
    )

    currency_rate_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("currency_rates.currency_rate_id"),
        nullable=True,
    )

    expected_date: Mapped[date] = mapped_column(
        Date,
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

    flow_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    forecast_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EXPECTED",
        server_default=text("'EXPECTED'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
