
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models import (
    LegalEntity,
    BankAccount,
    LedgerEntry,
    Receivable,
    Payable,
    CurrencyRate,
    ForecastRun,
    CashFlowForecast,
)


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def get_fx_rate(session, source_currency, target_currency, effective_date):
    """
    Get the latest available FX rate on or before effective_date.
    Rate convention: 1 unit of source currency = rate units of target.
    """

    if source_currency == target_currency:
        return Decimal("1")

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

    if rate is None:
        raise ValueError(
            f"Missing FX rate: {source_currency} to {target_currency} "
            f"on or before {effective_date}"
        )

    return Decimal(rate.exchange_rate)


def convert_to_reporting_currency(
    session,
    amount,
    source_currency,
    reporting_currency,
    effective_date,
):
    """Convert a monetary amount into the reporting currency."""

    rate = get_fx_rate(
        session,
        source_currency,
        reporting_currency,
        effective_date,
    )

    return (Decimal(amount) * rate).quantize(CENT)


def calculate_daily_cash_positions(forecast_run_id):
    """
    Calculate daily cash positions for every legal entity
    in a particular forecast run.

    Opening position:
        Opening bank balances + posted ledger activity
        through the forecast cutoff date.

    Daily closing position:
        Opening position + inflows - outflows.

    Returns calculated positions in memory.
    """

    session = SessionLocal()

    try:
        forecast_run = (
            session.query(ForecastRun)
            .filter(
                ForecastRun.forecast_run_id == forecast_run_id
            )
            .one_or_none()
        )

        if forecast_run is None:
            raise ValueError(
                f"Forecast run not found: {forecast_run_id}"
            )

        cutoff_date = forecast_run.forecast_cutoff_date
        reporting_currency = forecast_run.reporting_currency
        first_forecast_day = cutoff_date + timedelta(days=1)

        entities = (
            session.query(LegalEntity)
            .order_by(LegalEntity.entity_id)
            .all()
        )

        accounts = (
            session.query(BankAccount)
            .order_by(BankAccount.bank_account_id)
            .all()
        )

        receivables = {
            item.receivable_id: item
            for item in session.query(Receivable).all()
        }

        payables = {
            item.payable_id: item
            for item in session.query(Payable).all()
        }

        # -------------------------------------------------
        # 1. Calculate actual cash balance at cutoff date.
        # -------------------------------------------------

        entity_opening_balances = defaultdict(lambda: ZERO)

        for account in accounts:
            opening_balance = convert_to_reporting_currency(
                session,
                account.opening_balance,
                account.currency,
                reporting_currency,
                account.opening_balance_date,
            )

            entity_opening_balances[account.entity_id] += opening_balance

            ledger_entries = (
                session.query(LedgerEntry)
                .filter(
                    LedgerEntry.bank_account_id
                    == account.bank_account_id,
                    LedgerEntry.posting_date
                    >= account.opening_balance_date,
                    LedgerEntry.posting_date <= cutoff_date,
                )
                .order_by(LedgerEntry.posting_date)
                .all()
            )

            for entry in ledger_entries:
                converted_amount = convert_to_reporting_currency(
                    session,
                    entry.amount,
                    entry.currency,
                    reporting_currency,
                    entry.posting_date,
                )

                if entry.transaction_type == "INFLOW":
                    entity_opening_balances[account.entity_id] += (
                        converted_amount
                    )
                elif entry.transaction_type == "OUTFLOW":
                    entity_opening_balances[account.entity_id] -= (
                        converted_amount
                    )
                else:
                    raise ValueError(
                        f"Invalid ledger transaction type: "
                        f"{entry.transaction_type}"
                    )

        # -------------------------------------------------
        # 2. Read forecast cash flows for this run.
        # -------------------------------------------------

        forecast_items = (
            session.query(CashFlowForecast)
            .filter(
                CashFlowForecast.forecast_run_id
                == forecast_run_id,
                CashFlowForecast.forecast_status != "CANCELLED",
            )
            .order_by(CashFlowForecast.expected_date)
            .all()
        )

        daily_flows = defaultdict(
            lambda: {"inflows": ZERO, "outflows": ZERO}
        )

        latest_forecast_date = first_forecast_day

        for item in forecast_items:

            if item.expected_date < first_forecast_day:
                raise ValueError(
                    f"Forecast item {item.forecast_item_id} "
                    "is before the forecast cutoff."
                )

            if item.receivable_id:
                source = receivables.get(item.receivable_id)

                if source is None:
                    raise ValueError(
                        f"Receivable not found: {item.receivable_id}"
                    )

                entity_id = source.entity_id

                if item.flow_type != "INFLOW":
                    raise ValueError(
                        "Receivable forecast must be an INFLOW."
                    )

            elif item.payable_id:
                source = payables.get(item.payable_id)

                if source is None:
                    raise ValueError(
                        f"Payable not found: {item.payable_id}"
                    )

                entity_id = source.entity_id

                if item.flow_type != "OUTFLOW":
                    raise ValueError(
                        "Payable forecast must be an OUTFLOW."
                    )

            elif item.bank_account_id:
                account = next(
                    (
                        account
                        for account in accounts
                        if account.bank_account_id
                        == item.bank_account_id
                    ),
                    None,
                )

                if account is None:
                    raise ValueError(
                        f"Bank account not found: {item.bank_account_id}"
                    )

                entity_id = account.entity_id

            else:
                raise ValueError(
                    f"Forecast item {item.forecast_item_id} "
                    "has no identifiable source entity."
                )

            # Projected amounts use the latest FX rate available
            # at the forecast cutoff, not a future exchange rate.
            converted_amount = convert_to_reporting_currency(
                session,
                item.amount,
                item.currency,
                reporting_currency,
                cutoff_date,
            )

            flow_key = (entity_id, item.expected_date)

            if item.flow_type == "INFLOW":
                daily_flows[flow_key]["inflows"] += converted_amount

            elif item.flow_type == "OUTFLOW":
                daily_flows[flow_key]["outflows"] += converted_amount

            else:
                raise ValueError(
                    f"Invalid forecast flow type: {item.flow_type}"
                )

            latest_forecast_date = max(
                latest_forecast_date,
                item.expected_date,
            )

        # -------------------------------------------------
        # 3. Calculate daily opening and closing positions.
        # -------------------------------------------------

        results = []

        for entity in entities:
            running_balance = entity_opening_balances[entity.entity_id]

            current_date = first_forecast_day

            while current_date <= latest_forecast_date:
                opening_balance = running_balance

                flows = daily_flows[
                    (entity.entity_id, current_date)
                ]

                inflows = flows["inflows"]
                outflows = flows["outflows"]

                closing_balance = (
                    opening_balance + inflows - outflows
                ).quantize(CENT)

                results.append({
                    "forecast_run_id": forecast_run_id,
                    "scenario_id": forecast_run.scenario_id,
                    "entity_id": entity.entity_id,
                    "date": current_date,
                    "currency": reporting_currency,
                    "opening_balance": opening_balance.quantize(CENT),
                    "inflows": inflows.quantize(CENT),
                    "outflows": outflows.quantize(CENT),
                    "closing_balance": closing_balance,
                })

                running_balance = closing_balance
                current_date += timedelta(days=1)

        return results

    finally:
        session.close()
