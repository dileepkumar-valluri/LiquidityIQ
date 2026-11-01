
from collections import defaultdict
from datetime import date
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models import (
    BankAccount,
    CashFlowForecast,
    CurrencyRate,
    ForecastRun,
    LedgerEntry,
    Payable,
    Receivable,
)


def convert_amount(session, amount, source_currency, target_currency, effective_date):
    """Convert an amount using the latest available FX rate."""

    amount = Decimal(str(amount))

    if source_currency == target_currency:
        return amount

    rate = (
        session.query(CurrencyRate)
        .filter(
            CurrencyRate.base_currency == source_currency,
            CurrencyRate.quote_currency == target_currency,
            CurrencyRate.effective_date <= effective_date,
        )
        .order_by(CurrencyRate.effective_date.desc())
        .first()
    )

    if rate:
        return amount * Decimal(str(rate.exchange_rate))

    inverse_rate = (
        session.query(CurrencyRate)
        .filter(
            CurrencyRate.base_currency == target_currency,
            CurrencyRate.quote_currency == source_currency,
            CurrencyRate.effective_date <= effective_date,
        )
        .order_by(CurrencyRate.effective_date.desc())
        .first()
    )

    if inverse_rate:
        return amount / Decimal(str(inverse_rate.exchange_rate))

    raise ValueError(
        f"Missing FX rate: {source_currency} to {target_currency} "
        f"on or before {effective_date}"
    )


def compare_forecast_to_actual(forecast_run_id):
    """
    Compare forecasted cash flows with actual posted ledger transactions.

    Matching level:
    Legal entity + date + flow type.

    Actual transactions posted on or before the forecast cutoff
    are excluded from the comparison.
    """

    session = SessionLocal()

    try:
        forecast_run = (
            session.query(ForecastRun)
            .filter(ForecastRun.forecast_run_id == forecast_run_id)
            .first()
        )

        if not forecast_run:
            raise ValueError(f"Forecast run not found: {forecast_run_id}")

        cutoff_date = forecast_run.forecast_cutoff_date
        reporting_currency = forecast_run.reporting_currency

        forecast_items = (
            session.query(CashFlowForecast)
            .filter(
                CashFlowForecast.forecast_run_id == forecast_run_id,
                CashFlowForecast.forecast_status != "CANCELLED",
                CashFlowForecast.expected_date > cutoff_date,
            )
            .all()
        )

        # Store expected and actual amounts by entity, date and flow type.
        forecast_totals = defaultdict(Decimal)
        actual_totals = defaultdict(Decimal)

        # Track currencies used in each aggregate.
        forecast_count = defaultdict(int)
        actual_count = defaultdict(int)

        # Aggregate forecasted cash flows.
        for item in forecast_items:

            entity_id = None

            if item.receivable_id:
                receivable = (
                    session.query(Receivable)
                    .filter(
                        Receivable.receivable_id == item.receivable_id
                    )
                    .first()
                )

                if receivable:
                    entity_id = receivable.entity_id

            elif item.payable_id:
                payable = (
                    session.query(Payable)
                    .filter(
                        Payable.payable_id == item.payable_id
                    )
                    .first()
                )

                if payable:
                    entity_id = payable.entity_id

            elif item.bank_account_id:
                account = (
                    session.query(BankAccount)
                    .filter(
                        BankAccount.bank_account_id == item.bank_account_id
                    )
                    .first()
                )

                if account:
                    entity_id = account.entity_id

            if not entity_id:
                raise ValueError(
                    f"Cannot identify legal entity for forecast item "
                    f"{item.forecast_item_id}"
                )

            converted_amount = convert_amount(
                session,
                item.amount,
                item.currency,
                reporting_currency,
                cutoff_date,
            )

            key = (
                entity_id,
                item.expected_date,
                item.flow_type,
            )

            forecast_totals[key] += converted_amount
            forecast_count[key] += 1

        # Get the forecast horizon.
        forecast_dates = [key[1] for key in forecast_totals]

        if not forecast_dates:
            return {
                "forecast_run_id": forecast_run_id,
                "cutoff_date": str(cutoff_date),
                "reporting_currency": reporting_currency,
                "actual_transactions_found": 0,
                "comparison_level": "ENTITY_DATE_FLOW_TYPE",
                "comparisons": [],
            }

        last_forecast_date = max(forecast_dates)

        # Fetch actual ledger entries posted after cutoff.
        actual_entries = (
            session.query(LedgerEntry, BankAccount)
            .join(
                BankAccount,
                LedgerEntry.bank_account_id == BankAccount.bank_account_id,
            )
            .filter(
                LedgerEntry.posting_date > cutoff_date,
                LedgerEntry.posting_date <= last_forecast_date,
            )
            .all()
        )

        # Aggregate actual posted cash flows.
        for entry, account in actual_entries:

            converted_amount = convert_amount(
                session,
                entry.amount,
                entry.currency,
                reporting_currency,
                entry.posting_date,
            )

            key = (
                account.entity_id,
                entry.posting_date,
                entry.transaction_type,
            )

            actual_totals[key] += converted_amount
            actual_count[key] += 1

        # Compare all forecast and actual aggregate buckets.
        all_keys = set(forecast_totals) | set(actual_totals)

        comparisons = []

        for key in sorted(all_keys, key=lambda x: (x[1], x[0], x[2])):

            entity_id, comparison_date, flow_type = key

            expected = forecast_totals.get(key, Decimal("0"))
            actual = actual_totals.get(key, Decimal("0"))

            variance = actual - expected

            if key not in actual_totals:
                status = "NO_ACTUAL_RECORDED"
                explanation = (
                    "No actual transaction was posted for this "
                    "entity, date and flow type."
                )

            elif key not in forecast_totals:
                status = "UNFORECASTED_ACTUAL"
                explanation = (
                    "An actual transaction was posted without a "
                    "matching forecast aggregate."
                )

            elif variance == 0:
                status = "MATCHED"
                explanation = "Actual amount matches forecast amount."

            else:
                status = "VARIANCE"
                explanation = (
                    "Actual and forecast aggregate amounts differ. "
                    "Further investigation is required."
                )

            variance_percentage = (
                (variance / expected) * Decimal("100")
                if expected != 0
                else None
            )

            comparisons.append({
                "entity_id": entity_id,
                "date": str(comparison_date),
                "flow_type": flow_type,
                "expected_amount": round(float(expected), 2),
                "actual_amount": round(float(actual), 2),
                "variance": round(float(variance), 2),
                "variance_percentage": (
                    round(float(variance_percentage), 2)
                    if variance_percentage is not None
                    else None
                ),
                "forecast_item_count": forecast_count.get(key, 0),
                "actual_transaction_count": actual_count.get(key, 0),
                "status": status,
                "explanation": explanation,
                "currency": reporting_currency,
            })

        return {
            "forecast_run_id": forecast_run_id,
            "cutoff_date": str(cutoff_date),
            "reporting_currency": reporting_currency,
            "actual_transactions_found": len(actual_entries),
            "comparison_level": "ENTITY_DATE_FLOW_TYPE",
            "comparisons": comparisons,
        }

    finally:
        session.close()
