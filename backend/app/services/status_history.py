
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    LegalEntity,
    BankAccount,
    Receivable,
    Payable,
    ForecastRun,
    LiquidityScenario,
    StatusHistory,
)


STATUS_MODELS = {
    "LegalEntity": LegalEntity,
    "BankAccount": BankAccount,
    "Receivable": Receivable,
    "Payable": Payable,
    "ForecastRun": ForecastRun,
    "LiquidityScenario": LiquidityScenario,
}


STATUS_FIELDS = {
    "LegalEntity": ("entity_id", "status"),
    "BankAccount": ("bank_account_id", "account_status"),
    "Receivable": ("receivable_id", "status"),
    "Payable": ("payable_id", "status"),
    "ForecastRun": ("forecast_run_id", "status"),
}


VALID_TRANSITIONS = {
    "LegalEntity": {
        "ACTIVE": {"INACTIVE", "SUSPENDED"},
        "INACTIVE": {"ACTIVE"},
        "SUSPENDED": {"ACTIVE", "INACTIVE"},
    },
    "BankAccount": {
        "ACTIVE": {"INACTIVE", "SUSPENDED"},
        "INACTIVE": {"ACTIVE"},
        "SUSPENDED": {"ACTIVE", "INACTIVE"},
    },
    "Receivable": {
        "SCHEDULED": {"PARTIALLY_PAID", "PAID", "OVERDUE", "CANCELLED"},
        "PARTIALLY_PAID": {"PAID", "OVERDUE", "CANCELLED"},
        "OVERDUE": {"PARTIALLY_PAID", "PAID", "CANCELLED"},
        "PAID": set(),
        "CANCELLED": set(),
    },
    "Payable": {
        "SCHEDULED": {"PARTIALLY_PAID", "PAID", "OVERDUE", "CANCELLED"},
        "PARTIALLY_PAID": {"PAID", "OVERDUE", "CANCELLED"},
        "OVERDUE": {"PARTIALLY_PAID", "PAID", "CANCELLED"},
        "PAID": set(),
        "CANCELLED": set(),
    },
    "ForecastRun": {
        "PENDING": {"RUNNING", "FAILED"},
        "RUNNING": {"COMPLETED", "FAILED"},
        "COMPLETED": set(),
        "FAILED": {"RUNNING"},
    },
}


def change_status(
    session: Session,
    entity_type: str,
    record_id: str,
    new_status: str,
    changed_by: str = "SYSTEM",
    reason: str | None = None,
):
    if entity_type not in STATUS_MODELS:
        raise ValueError(f"Unsupported entity type: {entity_type}")

    model = STATUS_MODELS[entity_type]
    id_field, status_field = STATUS_FIELDS[entity_type]

    record = session.execute(
        select(model).where(getattr(model, id_field) == record_id)
    ).scalar_one_or_none()

    if record is None:
        raise ValueError(f"{entity_type} record not found: {record_id}")

    previous_status = getattr(record, status_field)

    allowed = VALID_TRANSITIONS[entity_type].get(previous_status, set())

    if new_status not in allowed:
        raise ValueError(
            f"Invalid {entity_type} transition: "
            f"{previous_status} -> {new_status}"
        )

    history = StatusHistory(
        entity_type=entity_type,
        record_id=record_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=changed_by,
        change_reason=reason,
        changed_at=datetime.now(timezone.utc),
    )

    try:
        setattr(record, status_field, new_status)
        session.add(history)
        session.commit()
        session.refresh(history)
    except Exception:
        session.rollback()
        raise

    return history


def get_status_history(
    session: Session,
    entity_type: str,
    record_id: str,
):
    statement = (
        select(StatusHistory)
        .where(
            StatusHistory.entity_type == entity_type,
            StatusHistory.record_id == record_id,
        )
        .order_by(StatusHistory.changed_at, StatusHistory.id)
    )

    return list(session.execute(statement).scalars().all())
