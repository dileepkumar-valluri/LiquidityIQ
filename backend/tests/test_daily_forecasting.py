
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.forecasting import (
    calculate_daily_cash_positions,
)


@pytest.fixture
def mock_forecasting_data():
    entity = SimpleNamespace(entity_id="ENT-TEST-001")

    account = SimpleNamespace(
        bank_account_id="BANK-TEST-001",
        entity_id="ENT-TEST-001",
        opening_balance=Decimal("1000.00"),
        currency="INR",
        opening_balance_date=date(2026, 10, 1),
    )

    ledger_entries = [
        SimpleNamespace(
            posting_date=date(2026, 10, 15),
            transaction_type="INFLOW",
            amount=Decimal("500.00"),
            currency="INR",
        ),
        SimpleNamespace(
            posting_date=date(2026, 10, 20),
            transaction_type="OUTFLOW",
            amount=Decimal("200.00"),
            currency="INR",
        ),
    ]

    forecast_run = SimpleNamespace(
        forecast_run_id="FCAST-TEST-001",
        forecast_cutoff_date=date(2026, 10, 31),
        reporting_currency="INR",
        scenario_id="SCENARIO-TEST-001",
    )

    receivable = SimpleNamespace(
        receivable_id="REC-TEST-001",
        entity_id="ENT-TEST-001",
    )

    payable = SimpleNamespace(
        payable_id="PAY-TEST-001",
        entity_id="ENT-TEST-001",
    )

    return {
        "entity": entity,
        "account": account,
        "ledger_entries": ledger_entries,
        "forecast_run": forecast_run,
        "receivable": receivable,
        "payable": payable,
    }


def run_forecast_with_mocks(data, forecast_items):
    session = MagicMock()

    def query_side_effect(model):
        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query

        if model.__name__ == "ForecastRun":
            query.one_or_none.return_value = data["forecast_run"]

        elif model.__name__ == "LegalEntity":
            query.all.return_value = [data["entity"]]

        elif model.__name__ == "BankAccount":
            query.all.return_value = [data["account"]]

        elif model.__name__ == "Receivable":
            query.all.return_value = [data["receivable"]]

        elif model.__name__ == "Payable":
            query.all.return_value = [data["payable"]]

        elif model.__name__ == "LedgerEntry":
            query.all.return_value = data["ledger_entries"]

        elif model.__name__ == "CashFlowForecast":
            # Simulate the database excluding cancelled items.
            query.all.return_value = [
                item
                for item in forecast_items
                if item.forecast_status != "CANCELLED"
            ]

        return query

    session.query.side_effect = query_side_effect

    with patch(
        "backend.app.services.forecasting.SessionLocal",
        return_value=session,
    ), patch(
        "backend.app.services.forecasting.convert_to_reporting_currency",
        side_effect=lambda session, amount, source, target, effective_date:
            Decimal(amount).quantize(Decimal("0.01")),
    ):
        result = calculate_daily_cash_positions("FCAST-TEST-001")

    session.close.assert_called_once()
    return result


def test_opening_balance_includes_posted_ledger_activity(
    mock_forecasting_data,
):
    results = run_forecast_with_mocks(mock_forecasting_data, [])

    first_day = results[0]

    # 1000 + 500 inflow - 200 outflow = 1300
    assert first_day["opening_balance"] == Decimal("1300.00")
    assert first_day["closing_balance"] == Decimal("1300.00")


def test_daily_inflows_and_outflows_are_calculated(
    mock_forecasting_data,
):
    forecast_items = [
        SimpleNamespace(
            forecast_item_id="CF-TEST-001",
            receivable_id="REC-TEST-001",
            payable_id=None,
            bank_account_id=None,
            expected_date=date(2026, 11, 1),
            amount=Decimal("300.00"),
            currency="INR",
            flow_type="INFLOW",
            forecast_status="PENDING",
        ),
        SimpleNamespace(
            forecast_item_id="CF-TEST-002",
            receivable_id=None,
            payable_id="PAY-TEST-001",
            bank_account_id=None,
            expected_date=date(2026, 11, 1),
            amount=Decimal("100.00"),
            currency="INR",
            flow_type="OUTFLOW",
            forecast_status="PENDING",
        ),
    ]

    results = run_forecast_with_mocks(
        mock_forecasting_data, forecast_items
    )

    first_day = results[0]

    assert first_day["inflows"] == Decimal("300.00")
    assert first_day["outflows"] == Decimal("100.00")
    assert first_day["closing_balance"] == Decimal("1500.00")


def test_next_day_opening_matches_previous_closing(
    mock_forecasting_data,
):
    forecast_items = [
        SimpleNamespace(
            forecast_item_id="CF-TEST-003",
            receivable_id="REC-TEST-001",
            payable_id=None,
            bank_account_id=None,
            expected_date=date(2026, 11, 1),
            amount=Decimal("300.00"),
            currency="INR",
            flow_type="INFLOW",
            forecast_status="PENDING",
        ),
        SimpleNamespace(
            forecast_item_id="CF-TEST-004",
            receivable_id="REC-TEST-001",
            payable_id=None,
            bank_account_id=None,
            expected_date=date(2026, 11, 2),
            amount=Decimal("200.00"),
            currency="INR",
            flow_type="INFLOW",
            forecast_status="PENDING",
        ),
    ]

    results = run_forecast_with_mocks(
        mock_forecasting_data, forecast_items
    )

    assert results[1]["opening_balance"] == (
        results[0]["closing_balance"]
    )


def test_cancelled_forecast_items_are_ignored(
    mock_forecasting_data,
):
    forecast_items = [
        SimpleNamespace(
            forecast_item_id="CF-TEST-005",
            receivable_id="REC-TEST-001",
            payable_id=None,
            bank_account_id=None,
            expected_date=date(2026, 11, 1),
            amount=Decimal("500.00"),
            currency="INR",
            flow_type="INFLOW",
            forecast_status="CANCELLED",
        ),
    ]

    results = run_forecast_with_mocks(
        mock_forecasting_data, forecast_items
    )

    assert results[0]["inflows"] == Decimal("0.00")
    assert results[0]["closing_balance"] == Decimal("1300.00")


def test_forecast_before_cutoff_is_rejected(
    mock_forecasting_data,
):
    forecast_items = [
        SimpleNamespace(
            forecast_item_id="CF-TEST-006",
            receivable_id="REC-TEST-001",
            payable_id=None,
            bank_account_id=None,
            expected_date=date(2026, 10, 31),
            amount=Decimal("100.00"),
            currency="INR",
            flow_type="INFLOW",
            forecast_status="PENDING",
        ),
    ]

    with pytest.raises(ValueError, match="before the forecast cutoff"):
        run_forecast_with_mocks(
            mock_forecasting_data, forecast_items
        )


def test_invalid_ledger_transaction_type_is_rejected(
    mock_forecasting_data,
):
    mock_forecasting_data["ledger_entries"] = [
        SimpleNamespace(
            posting_date=date(2026, 10, 15),
            transaction_type="UNKNOWN",
            amount=Decimal("100.00"),
            currency="INR",
        )
    ]

    with pytest.raises(ValueError, match="Invalid ledger transaction type"):
        run_forecast_with_mocks(
            mock_forecasting_data, []
        )
