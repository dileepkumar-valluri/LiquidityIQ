
import argparse
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models import (
    LegalEntity,
    BankAccount,
    LedgerEntry,
    Receivable,
    Payable,
    CurrencyRate,
    LiquidityScenario,
    ForecastRun,
    CashFlowForecast,
)


DEFAULT_SEED = 20261022
RUN_DATE = date(2026, 11, 1)
CUTOFF_DATE = date(2026, 10, 31)
SUPPORTED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "SGD"]

COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Germany",
    "Singapore",
]

BANK_NAMES = [
    "Synthetic National Bank",
    "Global Trust Bank",
    "First Commercial Bank",
    "United Finance Bank",
    "International Business Bank",
]


@dataclass
class DatasetConfig:
    legal_entities: int
    bank_accounts: int
    ledger_entries: int
    forecast_items: int


STARTER_CONFIG = DatasetConfig(3, 15, 1000, 200)
BASELINE_CONFIG = DatasetConfig(30, 150, 100000, 20000)


def create_random_generator(seed=DEFAULT_SEED):
    return random.Random(seed)


def generate_entity_id(number):
    return f"ENT-{number:06d}"


def generate_bank_account_id(entity_number, account_number):
    return f"BANKACC-ENT-{entity_number:06d}-{account_number:03d}"


def generate_ledger_entry_id(number):
    return f"LED-2026-{number:08d}"


def generate_receivable_id(number):
    return f"REC-2026-{number:06d}"


def generate_payable_id(number):
    return f"PAY-2026-{number:06d}"


def generate_currency_rate_id(number):
    return f"FX-2026-{number:06d}"


def generate_scenario_id(number):
    return f"SCN-{number:06d}"


def generate_forecast_run_id(run_date, number):
    return f"FCAST-{run_date}-{number:03d}"


def generate_forecast_item_id(number):
    return f"CF-2026-{number:06d}"


# ---------------------------------------------------------
# 1. MASTER DATA
# ---------------------------------------------------------

def build_master_records(config, rng):
    entities = []
    accounts = []

    opening_date = date(2026, 1, 1)

    accounts_per_entity = config.bank_accounts // config.legal_entities
    extra_accounts = config.bank_accounts % config.legal_entities

    for entity_number in range(1, config.legal_entities + 1):
        entity_id = generate_entity_id(entity_number)

        entity = LegalEntity(
            entity_id=entity_id,
            entity_name=f"Synthetic Corporation {entity_number:03d}",
            registration_number=f"SYN-REG-{entity_number:06d}",
            country=rng.choice(COUNTRIES),
            base_currency=rng.choice(SUPPORTED_CURRENCIES),
            status="ACTIVE",
        )

        entities.append(entity)

        account_count = accounts_per_entity

        if entity_number <= extra_accounts:
            account_count += 1

        for account_number in range(1, account_count + 1):
            account = BankAccount(
                bank_account_id=generate_bank_account_id(
                    entity_number,
                    account_number,
                ),
                entity_id=entity_id,
                bank_name=rng.choice(BANK_NAMES),
                account_reference=(
                    f"SYN-ACCOUNT-{entity_number:06d}-{account_number:03d}"
                ),
                currency=rng.choice(SUPPORTED_CURRENCIES),
                opening_balance=(
                    Decimal(rng.randint(100000, 10000000))
                    / Decimal("100")
                ),
                opening_balance_date=opening_date,
                account_status="ACTIVE",
            )

            accounts.append(account)

    return entities, accounts


def insert_master_records(config, rng):
    session = SessionLocal()

    try:
        entities, accounts = build_master_records(config, rng)

        existing_entity_ids = {
            row[0]
            for row in session.query(LegalEntity.entity_id).all()
        }

        existing_account_ids = {
            row[0]
            for row in session.query(BankAccount.bank_account_id).all()
        }

        expected_entity_ids = {item.entity_id for item in entities}
        expected_account_ids = {item.bank_account_id for item in accounts}

        if (
            existing_entity_ids == expected_entity_ids
            and existing_account_ids == expected_account_ids
        ):
            print("Master records already exist. No duplicates inserted.")
            return

        if existing_entity_ids or existing_account_ids:
            raise RuntimeError(
                "Existing master data does not match the requested scale."
            )

        session.add_all(entities)
        session.flush()
        session.add_all(accounts)
        session.commit()

        print("Master data inserted successfully!")
        print(f"Legal entities inserted: {len(entities)}")
        print(f"Bank accounts inserted: {len(accounts)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 2. LEDGER ENTRIES
# ---------------------------------------------------------

def insert_ledger_entries(config, rng):
    session = SessionLocal()

    try:
        existing_count = session.query(LedgerEntry).count()

        if existing_count == config.ledger_entries:
            print("Ledger entries already exist. No duplicates inserted.")
            return

        if existing_count > 0:
            raise RuntimeError(
                "Existing ledger dataset has a different size."
            )

        accounts = (
            session.query(BankAccount)
            .order_by(BankAccount.bank_account_id)
            .all()
        )

        if not accounts:
            raise RuntimeError("Bank accounts must exist first.")

        batch = []

        for number in range(1, config.ledger_entries + 1):
            account = rng.choice(accounts)

            transaction_date = date(2026, 1, 2) + timedelta(
                days=rng.randint(0, 300)
            )

            posting_date = transaction_date + timedelta(
                days=rng.randint(0, 3)
            )

            entry = LedgerEntry(
                ledger_entry_id=generate_ledger_entry_id(number),
                bank_account_id=account.bank_account_id,
                transaction_date=transaction_date,
                posting_date=posting_date,
                transaction_type=rng.choice(["INFLOW", "OUTFLOW"]),
                amount=(
                    Decimal(rng.randint(100, 1000000))
                    / Decimal("100")
                ),
                currency=account.currency,
                description=f"Synthetic transaction {number:08d}",
            )

            batch.append(entry)

            if len(batch) >= 5000:
                session.add_all(batch)
                session.flush()
                batch.clear()

        if batch:
            session.add_all(batch)

        session.commit()

        print("Ledger entries generated successfully!")
        print(f"Ledger entries inserted: {config.ledger_entries}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 3. RECEIVABLES AND PAYABLES
# ---------------------------------------------------------

def insert_receivables_and_payables(config, rng):
    session = SessionLocal()

    try:
        entities = (
            session.query(LegalEntity)
            .order_by(LegalEntity.entity_id)
            .all()
        )

        if not entities:
            raise RuntimeError("Legal entities must exist first.")

        receivable_count = session.query(Receivable).count()
        payable_count = session.query(Payable).count()

        if (
            receivable_count == config.forecast_items
            and payable_count == config.forecast_items
        ):
            print("Receivables and payables already exist. No duplicates inserted.")
            return

        if receivable_count > 0 or payable_count > 0:
            raise RuntimeError(
                "Existing receivable/payable dataset has a different size."
            )

        receivables = []
        payables = []

        for number in range(1, config.forecast_items + 1):
            entity = rng.choice(entities)

            invoice_date = date(2026, 1, 1) + timedelta(
                days=rng.randint(0, 300)
            )
            due_date = invoice_date + timedelta(
                days=rng.randint(7, 60)
            )

            receivables.append(
                Receivable(
                    receivable_id=generate_receivable_id(number),
                    entity_id=entity.entity_id,
                    customer_reference=f"CUST-{number:06d}",
                    invoice_date=invoice_date,
                    due_date=due_date,
                    expected_amount=(
                        Decimal(rng.randint(5000, 50000000))
                        / Decimal("100")
                    ),
                    currency=entity.base_currency,
                    status=(
                        "OVERDUE"
                        if due_date < RUN_DATE
                        else "SCHEDULED"
                    ),
                )
            )

            invoice_date = date(2026, 1, 1) + timedelta(
                days=rng.randint(0, 300)
            )
            due_date = invoice_date + timedelta(
                days=rng.randint(7, 60)
            )

            payables.append(
                Payable(
                    payable_id=generate_payable_id(number),
                    entity_id=entity.entity_id,
                    supplier_reference=f"SUP-{number:06d}",
                    invoice_date=invoice_date,
                    due_date=due_date,
                    expected_amount=(
                        Decimal(rng.randint(5000, 50000000))
                        / Decimal("100")
                    ),
                    currency=entity.base_currency,
                    status=(
                        "OVERDUE"
                        if due_date < RUN_DATE
                        else "SCHEDULED"
                    ),
                )
            )

        session.add_all(receivables)
        session.add_all(payables)
        session.commit()

        print("Receivables and payables generated successfully!")
        print(f"Receivables inserted: {len(receivables)}")
        print(f"Payables inserted: {len(payables)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 4. CURRENCY RATES
# ---------------------------------------------------------

def insert_currency_rates():
    session = SessionLocal()

    try:
        effective_dates = [
            date(2026, 1, 1),
            date(2026, 4, 1),
            date(2026, 7, 1),
            date(2026, 10, 1),
        ]

        expected_count = (
            len(SUPPORTED_CURRENCIES)
            * (len(SUPPORTED_CURRENCIES) - 1)
            * len(effective_dates)
        )

        existing_count = session.query(CurrencyRate).count()

        if existing_count == expected_count:
            print("Currency rates already exist. No duplicates inserted.")
            return

        if existing_count > 0:
            raise RuntimeError("Existing FX dataset is incomplete.")

        rates_to_usd = {
            "INR": Decimal("0.01130"),
            "USD": Decimal("1.00000"),
            "EUR": Decimal("1.08000"),
            "GBP": Decimal("1.27000"),
            "SGD": Decimal("0.74000"),
        }

        records = []
        number = 1

        for date_index, effective_date in enumerate(effective_dates):
            for base_currency in SUPPORTED_CURRENCIES:
                for quote_currency in SUPPORTED_CURRENCIES:
                    if base_currency == quote_currency:
                        continue

                    exchange_rate = (
                        rates_to_usd[base_currency]
                        / rates_to_usd[quote_currency]
                    )

                    exchange_rate *= (
                        Decimal("1") + Decimal(date_index) * Decimal("0.002")
                    )

                    records.append(
                        CurrencyRate(
                            currency_rate_id=generate_currency_rate_id(number),
                            base_currency=base_currency,
                            quote_currency=quote_currency,
                            exchange_rate=exchange_rate.quantize(
                                Decimal("0.00000001")
                            ),
                            effective_date=effective_date,
                            source="SYNTHETIC_REFERENCE_DATA",
                        )
                    )

                    number += 1

        session.add_all(records)
        session.commit()

        print("Currency rates generated successfully!")
        print(f"Currency rates inserted: {len(records)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 5. LIQUIDITY SCENARIOS
# ---------------------------------------------------------

def insert_liquidity_scenarios():
    session = SessionLocal()

    try:
        existing_count = session.query(LiquidityScenario).count()

        if existing_count == 3:
            print("Liquidity scenarios already exist. No duplicates inserted.")
            return

        if existing_count > 0:
            raise RuntimeError("Existing scenario records are incomplete.")

        scenarios = [
            LiquidityScenario(
                scenario_id=generate_scenario_id(1),
                scenario_name="BASE",
                description="Baseline expected cash flow.",
                scenario_type="BASELINE",
                assumptions={
                    "receipt_delay_days": 0,
                    "outflow_multiplier": 1.0,
                },
            ),
            LiquidityScenario(
                scenario_id=generate_scenario_id(2),
                scenario_name="DELAYED_RECEIPT",
                description="Customer receipts delayed by seven days.",
                scenario_type="DELAYED_RECEIPT",
                assumptions={
                    "receipt_delay_days": 7,
                    "outflow_multiplier": 1.0,
                },
            ),
            LiquidityScenario(
                scenario_id=generate_scenario_id(3),
                scenario_name="STRESS",
                description="Receipts delayed by fourteen days and outflows increased by ten percent.",
                scenario_type="STRESS",
                assumptions={
                    "receipt_delay_days": 14,
                    "outflow_multiplier": 1.10,
                },
            ),
        ]

        session.add_all(scenarios)
        session.commit()

        print("Liquidity scenarios generated successfully!")
        print(f"Scenarios inserted: {len(scenarios)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 6. FORECAST RUNS
# ---------------------------------------------------------

def insert_forecast_runs(seed):
    session = SessionLocal()

    try:
        scenarios = (
            session.query(LiquidityScenario)
            .order_by(LiquidityScenario.scenario_id)
            .all()
        )

        if len(scenarios) != 3:
            raise RuntimeError("All three scenarios must exist first.")

        existing_count = session.query(ForecastRun).count()

        if existing_count == 3:
            print("Forecast runs already exist. No duplicates inserted.")
            return

        if existing_count > 0:
            raise RuntimeError("Existing forecast runs are incomplete.")

        records = []

        for number, scenario in enumerate(scenarios, start=1):
            records.append(
                ForecastRun(
                    forecast_run_id=generate_forecast_run_id(
                        RUN_DATE,
                        number,
                    ),
                    scenario_id=scenario.scenario_id,
                    run_date=RUN_DATE,
                    forecast_cutoff_date=CUTOFF_DATE,
                    reporting_currency="INR",
                    run_status="PENDING",
                    random_seed=seed,
                )
            )

        session.add_all(records)
        session.commit()

        print("Forecast runs generated successfully!")
        print(f"Forecast runs inserted: {len(records)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 7. FX RATE LOOKUP
# ---------------------------------------------------------

def find_fx_rate(session, source_currency, reporting_currency, cutoff_date):
    if source_currency == reporting_currency:
        return None

    rate = (
        session.query(CurrencyRate)
        .filter(
            CurrencyRate.base_currency == source_currency,
            CurrencyRate.quote_currency == reporting_currency,
            CurrencyRate.effective_date <= cutoff_date,
        )
        .order_by(CurrencyRate.effective_date.desc())
        .first()
    )

    if rate is None:
        raise RuntimeError(
            f"Missing FX rate: {source_currency} to {reporting_currency} "
            f"on or before {cutoff_date}"
        )

    return rate


# ---------------------------------------------------------
# 8. CASH FLOW FORECAST GENERATION
# ---------------------------------------------------------


def insert_cash_flow_forecasts(config):
    session = SessionLocal()

    try:
        existing_count = session.query(CashFlowForecast).count()

        active_receivable_count = (
            session.query(Receivable)
            .filter(Receivable.status.in_(("SCHEDULED", "OVERDUE")))
            .count()
        )

        active_payable_count = (
            session.query(Payable)
            .filter(Payable.status.in_(("SCHEDULED", "OVERDUE")))
            .count()
        )

        expected_count = (
            active_receivable_count + active_payable_count
        ) * 3

        if existing_count == expected_count:
            print("Cash flow forecasts already exist. No duplicates inserted.")
            return

        if existing_count > 0:
            raise RuntimeError(
                f"Existing forecast count is {existing_count}; "
                f"expected {expected_count}. Clear old forecast records first."
            )

        forecast_runs = (
            session.query(ForecastRun)
            .order_by(ForecastRun.forecast_run_id)
            .all()
        )

        receivables = (
            session.query(Receivable)
            .filter(Receivable.status.in_(("SCHEDULED", "OVERDUE")))
            .order_by(Receivable.receivable_id)
            .all()
        )

        payables = (
            session.query(Payable)
            .filter(Payable.status.in_(("SCHEDULED", "OVERDUE")))
            .order_by(Payable.payable_id)
            .all()
        )

        if len(forecast_runs) != 3:
            raise RuntimeError("Exactly three forecast runs are required.")

        if len(receivables) != active_receivable_count:
            raise RuntimeError("Receivable count validation failed.")

        if len(payables) != active_payable_count:
            raise RuntimeError("Payable count validation failed.")

        records = []
        item_number = 1

        for forecast_run in forecast_runs:

            scenario = (
                session.query(LiquidityScenario)
                .filter(
                    LiquidityScenario.scenario_id
                    == forecast_run.scenario_id
                )
                .one()
            )

            assumptions = scenario.assumptions or {}

            receipt_delay_days = int(
                assumptions.get("receipt_delay_days", 0)
            )

            outflow_multiplier = Decimal(
                str(assumptions.get("outflow_multiplier", 1.0))
            )

            first_forecast_day = (
                forecast_run.forecast_cutoff_date
                + timedelta(days=1)
            )

            # -----------------------------------------
            # FORECAST INFLOWS
            # -----------------------------------------

            for receivable in receivables:

                expected_date = max(
                    receivable.due_date,
                    first_forecast_day,
                ) + timedelta(days=receipt_delay_days)

                fx_rate = find_fx_rate(
                    session,
                    receivable.currency,
                    forecast_run.reporting_currency,
                    forecast_run.forecast_cutoff_date,
                )

                records.append(
                    CashFlowForecast(
                        forecast_item_id=generate_forecast_item_id(
                            item_number
                        ),
                        forecast_run_id=forecast_run.forecast_run_id,
                        receivable_id=receivable.receivable_id,
                        currency_rate_id=(
                            fx_rate.currency_rate_id if fx_rate else None
                        ),
                        expected_date=expected_date,
                        amount=receivable.expected_amount,
                        currency=receivable.currency,
                        flow_type="INFLOW",
                        forecast_status=(
                            "DELAYED"
                            if receipt_delay_days > 0
                            else "EXPECTED"
                        ),
                    )
                )

                item_number += 1

            # -----------------------------------------
            # FORECAST OUTFLOWS
            # -----------------------------------------

            for payable in payables:

                expected_date = max(
                    payable.due_date,
                    first_forecast_day,
                )

                adjusted_amount = (
                    payable.expected_amount * outflow_multiplier
                ).quantize(Decimal("0.01"))

                fx_rate = find_fx_rate(
                    session,
                    payable.currency,
                    forecast_run.reporting_currency,
                    forecast_run.forecast_cutoff_date,
                )

                records.append(
                    CashFlowForecast(
                        forecast_item_id=generate_forecast_item_id(
                            item_number
                        ),
                        forecast_run_id=forecast_run.forecast_run_id,
                        payable_id=payable.payable_id,
                        currency_rate_id=(
                            fx_rate.currency_rate_id if fx_rate else None
                        ),
                        expected_date=expected_date,
                        amount=adjusted_amount,
                        currency=payable.currency,
                        flow_type="OUTFLOW",
                        forecast_status="EXPECTED",
                    )
                )

                item_number += 1

        if len(records) != expected_count:
            raise RuntimeError(
                f"Generated {len(records)} records; "
                f"expected {expected_count}."
            )

        session.add_all(records)
        session.commit()

        print("Cash flow forecasts generated successfully!")
        print(f"Forecast items inserted: {len(records)}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


# ---------------------------------------------------------
# 9. COMMAND LINE
# ---------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="LiquidityIQ deterministic synthetic data generator"
    )

    parser.add_argument(
        "--scale",
        choices=["starter", "baseline"],
        default="starter",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    config = (
        STARTER_CONFIG
        if args.scale == "starter"
        else BASELINE_CONFIG
    )

    rng = create_random_generator(args.seed)

    print("LiquidityIQ Synthetic Data Generator")
    print("------------------------------------")
    print(f"Scale: {args.scale}")
    print(f"Seed: {args.seed}")

    insert_master_records(config, rng)
    insert_ledger_entries(config, rng)
    insert_receivables_and_payables(config, rng)
    insert_currency_rates()
    insert_liquidity_scenarios()
    insert_forecast_runs(args.seed)
    insert_cash_flow_forecasts(config)
