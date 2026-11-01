
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.app.services.status_history import (
    change_status,
    get_status_history,
)


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def receivable():
    return SimpleNamespace(
        receivable_id="REC-TEST-000001",
        status="SCHEDULED",
    )


def test_valid_receivable_status_transition(
    mock_session, receivable
):
    mock_session.execute.return_value.scalar_one_or_none.return_value = (
        receivable
    )

    history = change_status(
        mock_session,
        "Receivable",
        receivable.receivable_id,
        "PARTIALLY_PAID",
        changed_by="TEST",
        reason="Automated test",
    )

    assert receivable.status == "PARTIALLY_PAID"
    assert history.previous_status == "SCHEDULED"
    assert history.new_status == "PARTIALLY_PAID"
    assert history.changed_by == "TEST"

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(history)


def test_invalid_receivable_transition_is_rejected(
    mock_session, receivable
):
    mock_session.execute.return_value.scalar_one_or_none.return_value = (
        receivable
    )

    with pytest.raises(ValueError, match="Invalid Receivable transition"):
        change_status(
            mock_session,
            "Receivable",
            receivable.receivable_id,
            "SCHEDULED",
        )

    assert receivable.status == "SCHEDULED"
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


def test_unknown_entity_type_is_rejected(mock_session):
    with pytest.raises(ValueError, match="Unsupported entity type"):
        change_status(
            mock_session,
            "UnknownEntity",
            "REC-TEST-000001",
            "PAID",
        )

    mock_session.execute.assert_not_called()


def test_missing_record_is_rejected(mock_session):
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(ValueError, match="record not found"):
        change_status(
            mock_session,
            "Receivable",
            "REC-DOES-NOT-EXIST",
            "PAID",
        )

    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()


def test_status_history_can_be_retrieved(mock_session):
    expected_history = [
        SimpleNamespace(
            previous_status="SCHEDULED",
            new_status="PARTIALLY_PAID",
        ),
        SimpleNamespace(
            previous_status="PARTIALLY_PAID",
            new_status="PAID",
        ),
    ]

    mock_session.execute.return_value.scalars.return_value.all.return_value = (
        expected_history
    )

    history = get_status_history(
        mock_session,
        "Receivable",
        "REC-TEST-000001",
    )

    assert len(history) == 2
    assert history[0].new_status == "PARTIALLY_PAID"
    assert history[1].new_status == "PAID"


def test_database_error_rolls_back_status_change(
    mock_session, receivable
):
    mock_session.execute.return_value.scalar_one_or_none.return_value = (
        receivable
    )
    mock_session.commit.side_effect = RuntimeError("Database error")

    with pytest.raises(RuntimeError, match="Database error"):
        change_status(
            mock_session,
            "Receivable",
            receivable.receivable_id,
            "PARTIALLY_PAID",
        )

    assert receivable.status == "PARTIALLY_PAID"
    mock_session.rollback.assert_called_once()
