from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    BigInteger,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    __table_args__ = (
        CheckConstraint(
            "forecast_run_id ~ '^FCAST-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$'",
            name="ck_forecast_runs_id_format",
        ),
        CheckConstraint(
            "forecast_cutoff_date <= run_date",
            name="ck_forecast_runs_cutoff_date",
        ),
        CheckConstraint(
            "reporting_currency ~ '^[A-Z]{3}$'",
            name="ck_forecast_runs_currency",
        ),
        CheckConstraint(
            "run_status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="ck_forecast_runs_status",
        ),
    )

    forecast_run_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )

    scenario_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("liquidity_scenarios.scenario_id"),
        nullable=False,
        index=True,
    )

    run_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    forecast_cutoff_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reporting_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    run_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )

    random_seed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
