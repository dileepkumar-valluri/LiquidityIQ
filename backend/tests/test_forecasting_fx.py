
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.app.services.forecasting import (
    get_fx_rate,
    convert_to_reporting_currency,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.order_by.return_value = query
    return session


def test_same_currency_returns_one_without_database_query(mock_session):
    result = get_fx_rate(
        mock_session, "INR", "INR", date(2026, 11, 1)
    )

    assert result == Decimal("1")
    mock_session.query.assert_not_called()


def test_direct_fx_rate_is_returned(mock_session):
    mock_session.query.return_value.first.return_value = (
        SimpleNamespace(exchange_rate=Decimal("83.50000000"))
    )

    result = get_fx_rate(
        mock_session, "USD", "INR", date(2026, 11, 1)
    )

    assert result == Decimal("83.50000000")


def test_latest_available_rate_query_is_used(mock_session):
    mock_session.query.return_value.first.return_value = (
        SimpleNamespace(exchange_rate=Decimal("84.50000000"))
    )

    result = get_fx_rate(
        mock_session, "USD", "INR", date(2026, 11, 1)
    )

    query = mock_session.query.return_value
    query.order_by.assert_called_once()

    assert result == Decimal("84.50000000")


def test_missing_fx_rate_raises_value_error(mock_session):
    mock_session.query.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Missing FX rate"):
        get_fx_rate(
            mock_session, "JPY", "INR", date(2026, 11, 1)
        )


def test_reporting_currency_conversion_rounds_to_two_decimals(
    mock_session,
):
    mock_session.query.return_value.first.return_value = (
        SimpleNamespace(exchange_rate=Decimal("83.12345678"))
    )

    result = convert_to_reporting_currency(
        mock_session,
        Decimal("100"),
        "USD",
        "INR",
        date(2026, 11, 1),
    )

    assert result == Decimal("8312.35")


def test_same_currency_conversion_preserves_amount(mock_session):
    result = convert_to_reporting_currency(
        mock_session,
        Decimal("125.50"),
        "INR",
        "INR",
        date(2026, 11, 1),
    )

    assert result == Decimal("125.50")
    mock_session.query.assert_not_called()
