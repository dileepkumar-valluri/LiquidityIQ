from datetime import datetime
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class LiquidityScenario(Base):
    __tablename__ = "liquidity_scenarios"

    __table_args__ = (
        CheckConstraint(
            "scenario_id ~ '^SCN-[0-9]{6}$'",
            name="ck_liquidity_scenarios_id_format",
        ),
        CheckConstraint(
            "scenario_name IN ('BASE', 'DELAYED_RECEIPT', 'STRESS')",
            name="ck_liquidity_scenarios_name",
        ),
        CheckConstraint(
            "scenario_type IN ('BASELINE', 'DELAYED_RECEIPT', 'STRESS')",
            name="ck_liquidity_scenarios_type",
        ),
        CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_liquidity_scenarios_description",
        ),
        UniqueConstraint(
            "scenario_name",
            name="uq_liquidity_scenarios_name",
        ),
    )

    scenario_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    scenario_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    scenario_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    assumptions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
