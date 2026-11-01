from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class LegalEntity(Base):
    __tablename__ = "legal_entities"

    __table_args__ = (
        UniqueConstraint(
            "registration_number",
            name="uq_legal_entities_registration_number",
        ),
        CheckConstraint(
            "entity_id ~ '^ENT-[0-9]{6}$'",
            name="ck_legal_entities_id_format",
        ),
        CheckConstraint(
            "length(trim(entity_name)) > 0",
            name="ck_legal_entities_name_not_empty",
        ),
        CheckConstraint(
            "length(trim(country)) > 0",
            name="ck_legal_entities_country_not_empty",
        ),
        CheckConstraint(
            "base_currency ~ '^[A-Z]{3}$'",
            name="ck_legal_entities_currency_format",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="ck_legal_entities_status",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_legal_entities_timestamps",
        ),
    )

    entity_id: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
    )

    entity_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    registration_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    base_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
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
