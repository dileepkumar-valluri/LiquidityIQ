
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.app.services.actual_vs_forecast import convert_amount


@pytest.fixture
def mock_session():
    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.order_by.return_value = query
    return session


def test_same_currency_returns_original_amount(mock_session):
    result = convert_amount(
        mock_session,
        Decimal("150.50"),
        "INR",
        "INR",
        date(2026, 11, 1),
    )

    assert result == Decimal("150.50")
    mock_session.query.assert_not_called()


def test_direct_fx_conversion(mock_session):
    mock_session.query.return_value.first.return_value = (
        SimpleNamespace(exchange_rate=Decimal("83.50"))
    )

    result = convert_amount(
        mock_session,
        Decimal("100"),
        "USD",
        "INR",
        date(2026, 11, 1),
    )

    assert result == Decimal("8350")


def test_inverse_fx_conversion(mock_session):
    query = mock_session.query.return_value
    query.first.side_effect = [
        None,
        SimpleNamespace(exchange_rate=Decimal("0.0125")),
    ]

    result = convert_amount(
        mock_session,
        Decimal("100"),
        "USD",
        "INR",
        date(2026, 11, 1),
    )

    assert result == Decimal("8000")
    assert query.first.call_count == 2


def test_missing_direct_and_inverse_rates_raise_error(mock_session):
    mock_session.query.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Missing FX rate"):
        convert_amount(
            mock_session,
            Decimal("100"),
            "JPY",
            "INR",
            date(2026, 11, 1),
        )

    assert mock_session.query.return_value.first.call_count == 2


def test_amount_is_converted_using_decimal_arithmetic(mock_session):
    mock_session.query.return_value.first.return_value = (
        SimpleNamespace(exchange_rate=Decimal("1.25"))
    )

    result = convert_amount(
        mock_session,
        "10.50",
        "USD",
        "EUR",
        date(2026, 11, 1),
    )

    assert isinstance(result, Decimal)
    assert result == Decimal("13.1250")
