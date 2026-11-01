
from backend.app.database import SessionLocal
from sqlalchemy import func, case
from datetime import date
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
    StatusHistory,
)


def validate_dataset():
    session = SessionLocal()
    results = []

    def check(name, passed, details):
        results.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "details": details,
        })

    try:
        # 1. Primary key uniqueness
        models = [
            (LegalEntity, "entity_id"),
            (BankAccount, "bank_account_id"),
            (LedgerEntry, "ledger_entry_id"),
            (Receivable, "receivable_id"),
            (Payable, "payable_id"),
            (CurrencyRate, "currency_rate_id"),
            (LiquidityScenario, "scenario_id"),
            (ForecastRun, "forecast_run_id"),
            (CashFlowForecast, "forecast_item_id"),
        ]

        for model, field in models:
            column = getattr(model, field)
            total = session.query(model).count()
            unique = session.query(column).distinct().count()

            check(
                f"PK uniqueness: {model.__name__}",
                total == unique,
                f"Total={total}, Unique={unique}",
            )

        # 2. Foreign key integrity
        invalid_accounts = (
            session.query(BankAccount)
            .outerjoin(
                LegalEntity,
                BankAccount.entity_id == LegalEntity.entity_id,
            )
            .filter(LegalEntity.entity_id.is_(None))
            .count()
        )

        check(
            "BankAccount -> LegalEntity FK",
            invalid_accounts == 0,
            f"Invalid references={invalid_accounts}",
        )

        invalid_ledger = (
            session.query(LedgerEntry)
            .outerjoin(
                BankAccount,
                LedgerEntry.bank_account_id
                == BankAccount.bank_account_id,
            )
            .filter(BankAccount.bank_account_id.is_(None))
            .count()
        )

        check(
            "LedgerEntry -> BankAccount FK",
            invalid_ledger == 0,
            f"Invalid references={invalid_ledger}",
        )

        invalid_receivables = (
            session.query(Receivable)
            .outerjoin(
                LegalEntity,
                Receivable.entity_id == LegalEntity.entity_id,
            )
            .filter(LegalEntity.entity_id.is_(None))
            .count()
        )

        check(
            "Receivable -> LegalEntity FK",
            invalid_receivables == 0,
            f"Invalid references={invalid_receivables}",
        )

        invalid_payables = (
            session.query(Payable)
            .outerjoin(
                LegalEntity,
                Payable.entity_id == LegalEntity.entity_id,
            )
            .filter(LegalEntity.entity_id.is_(None))
            .count()
        )

        check(
            "Payable -> LegalEntity FK",
            invalid_payables == 0,
            f"Invalid references={invalid_payables}",
        )

        invalid_forecasts = (
            session.query(CashFlowForecast)
            .outerjoin(
                ForecastRun,
                CashFlowForecast.forecast_run_id
                == ForecastRun.forecast_run_id,
            )
            .filter(ForecastRun.forecast_run_id.is_(None))
            .count()
        )

        check(
            "CashFlowForecast -> ForecastRun FK",
            invalid_forecasts == 0,
            f"Invalid references={invalid_forecasts}",
        )
        # Additional foreign key integrity checks

        invalid_scenarios = (
            session.query(ForecastRun)
            .outerjoin(
                LiquidityScenario,
                ForecastRun.scenario_id == LiquidityScenario.scenario_id,
            )
            .filter(LiquidityScenario.scenario_id.is_(None))
            .count()
        )

        check(
            "ForecastRun -> LiquidityScenario FK",
            invalid_scenarios == 0,
            f"Invalid references={invalid_scenarios}",
        )

        optional_fk_checks = [
            (
                "CashFlowForecast -> BankAccount FK",
                CashFlowForecast.bank_account_id,
                BankAccount,
                BankAccount.bank_account_id,
            ),
            (
                "CashFlowForecast -> Receivable FK",
                CashFlowForecast.receivable_id,
                Receivable,
                Receivable.receivable_id,
            ),
            (
                "CashFlowForecast -> Payable FK",
                CashFlowForecast.payable_id,
                Payable,
                Payable.payable_id,
            ),
            (
                "CashFlowForecast -> CurrencyRate FK",
                CashFlowForecast.currency_rate_id,
                CurrencyRate,
                CurrencyRate.currency_rate_id,
            ),
        ]

        for check_name, foreign_key, parent_model, parent_key in optional_fk_checks:
            invalid_references = (
                session.query(CashFlowForecast)
                .outerjoin(
                    parent_model,
                    foreign_key == parent_key,
                )
                .filter(
                    foreign_key.isnot(None),
                    parent_key.is_(None),
                )
                .count()
            )

            check(
                check_name,
                invalid_references == 0,
                f"Invalid references={invalid_references}",
            )
        # 3. Bank account and ledger currency consistency
        currency_mismatches = (
            session.query(LedgerEntry)
            .join(
                BankAccount,
                LedgerEntry.bank_account_id
                == BankAccount.bank_account_id,
            )
            .filter(
                LedgerEntry.currency != BankAccount.currency
            )
            .count()
        )

        check(
            "Ledger and bank account currency consistency",
            currency_mismatches == 0,
            f"Currency mismatches={currency_mismatches}",
        )

        # 4. Calculate closing balances from opening balances and ledger activity
        negative_closing_balances = 0
        accounts_checked = 0

        for account in session.query(BankAccount).all():
            ledger_totals = (
                session.query(
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    LedgerEntry.transaction_type == "INFLOW",
                                    LedgerEntry.amount,
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    LedgerEntry.transaction_type == "OUTFLOW",
                                    LedgerEntry.amount,
                                ),
                                else_=0,
                            )
                        ),
                        0,
                    ),
                )
                .filter(
                    LedgerEntry.bank_account_id == account.bank_account_id,
                    LedgerEntry.posting_date <= date(2026, 10, 31),
                    LedgerEntry.posting_date >= account.opening_balance_date,
                )
                .one()
            )

            inflows, outflows = ledger_totals

            calculated_closing = (
                account.opening_balance + inflows - outflows
            )

            accounts_checked += 1

            if calculated_closing < 0:
                negative_closing_balances += 1
                print(
                    f"NEGATIVE BALANCE: {account.bank_account_id} | "
                    f"Opening={account.opening_balance} | "
                    f"Inflows={inflows} | "
                    f"Outflows={outflows} | "
                    f"Closing={calculated_closing}"
                )
        check(
            "Closing balance calculation",
            True,
            (
                f"Accounts checked={accounts_checked}, "
                f"Negative balances flagged={negative_closing_balances}"
            ),
        )

        if negative_closing_balances > 0:
            print(
                f"\nWARNING: {negative_closing_balances} accounts "
                "have negative calculated closing balances."
            )
            print(
                "These are liquidity warnings, not automatic validation failures."
            )
        # 4. Amount and date validation
        invalid_ledger_dates = (
            session.query(LedgerEntry)
            .filter(
                LedgerEntry.transaction_date > LedgerEntry.posting_date
            )
            .count()
        )

        check(
            "Ledger transaction/posting dates",
            invalid_ledger_dates == 0,
            f"Invalid records={invalid_ledger_dates}",
        )

        invalid_ledger_amounts = (
            session.query(LedgerEntry)
            .filter(LedgerEntry.amount <= 0)
            .count()
        )

        check(
            "Ledger positive amounts",
            invalid_ledger_amounts == 0,
            f"Invalid records={invalid_ledger_amounts}",
        )

        invalid_fx = (
            session.query(CurrencyRate)
            .filter(CurrencyRate.exchange_rate <= 0)
            .count()
        )

        check(
            "Positive FX rates",
            invalid_fx == 0,
            f"Invalid records={invalid_fx}",
        )
        # 5. FX rate availability for forecast conversion
        missing_fx_rates = 0

        forecast_items = (
            session.query(CashFlowForecast, ForecastRun)
            .join(
                ForecastRun,
                CashFlowForecast.forecast_run_id
                == ForecastRun.forecast_run_id,
            )
            .all()
        )

        for item, run in forecast_items:
            if item.currency == run.reporting_currency:
                continue

            fx_rate = (
                session.query(CurrencyRate)
                .filter(
                    CurrencyRate.base_currency == item.currency,
                    CurrencyRate.quote_currency == run.reporting_currency,
                    CurrencyRate.effective_date
                    <= run.forecast_cutoff_date,
                )
                .order_by(CurrencyRate.effective_date.desc())
                .first()
            )

            if fx_rate is None:
                missing_fx_rates += 1

        check(
            "FX rate availability",
            missing_fx_rates == 0,
            f"Forecast items missing FX rates={missing_fx_rates}",
        )
        # 6. Duplicate source cash flows within the same forecast run
        duplicate_forecasts = (
            session.query(
                CashFlowForecast.forecast_run_id,
                CashFlowForecast.receivable_id,
                CashFlowForecast.payable_id,
                func.count(CashFlowForecast.forecast_item_id),
            )
            .filter(
                (
                    CashFlowForecast.receivable_id.isnot(None)
                )
                | (
                    CashFlowForecast.payable_id.isnot(None)
                )
            )
            .group_by(
                CashFlowForecast.forecast_run_id,
                CashFlowForecast.receivable_id,
                CashFlowForecast.payable_id,
            )
            .having(
                func.count(CashFlowForecast.forecast_item_id) > 1
            )
            .all()
        )

        check(
            "Duplicate source forecasts within a run",
            len(duplicate_forecasts) == 0,
            f"Duplicate source groups={len(duplicate_forecasts)}",
        )

        # 5. Forecast validation
        forecast_runs = session.query(ForecastRun).all()

        invalid_cutoff = 0
        invalid_forecast_dates = 0

        for run in forecast_runs:
            if run.forecast_cutoff_date > run.run_date:
                invalid_cutoff += 1

            invalid_forecast_dates += (
                session.query(CashFlowForecast)
                .filter(
                    CashFlowForecast.forecast_run_id
                    == run.forecast_run_id,
                    CashFlowForecast.expected_date
                    <= run.forecast_cutoff_date,
                )
                .count()
            )

        check(
            "Forecast cutoff validation",
            invalid_cutoff == 0,
            f"Invalid runs={invalid_cutoff}",
        )

        check(
            "Forecast dates after cutoff",
            invalid_forecast_dates == 0,
            f"Invalid forecast records={invalid_forecast_dates}",
        )

        invalid_forecast_amounts = (
            session.query(CashFlowForecast)
            .filter(CashFlowForecast.amount <= 0)
            .count()
        )

        check(
            "Positive forecast amounts",
            invalid_forecast_amounts == 0,
            f"Invalid records={invalid_forecast_amounts}",
        )

        # 6. Receivable/payable flow direction
        invalid_receivable_flows = (
            session.query(CashFlowForecast)
            .filter(
                CashFlowForecast.receivable_id.isnot(None),
                CashFlowForecast.flow_type != "INFLOW",
            )
            .count()
        )

        invalid_payable_flows = (
            session.query(CashFlowForecast)
            .filter(
                CashFlowForecast.payable_id.isnot(None),
                CashFlowForecast.flow_type != "OUTFLOW",
            )
            .count()
        )

        check(
            "Receivable forecast direction",
            invalid_receivable_flows == 0,
            f"Invalid records={invalid_receivable_flows}",
        )

        check(
            "Payable forecast direction",
            invalid_payable_flows == 0,
            f"Invalid records={invalid_payable_flows}",
        )

        # 7. Forecast scenario count
        check(
            "Three forecast scenarios",
            session.query(LiquidityScenario).count() == 3,
            f"Scenarios={session.query(LiquidityScenario).count()}",
        )

        check(
            "Three forecast runs",
            session.query(ForecastRun).count() == 3,
            f"Runs={session.query(ForecastRun).count()}",
        )

        # 8. Dataset record counts
        counts = {
            "LegalEntity": session.query(LegalEntity).count(),
            "BankAccount": session.query(BankAccount).count(),
            "LedgerEntry": session.query(LedgerEntry).count(),
            "Receivable": session.query(Receivable).count(),
            "Payable": session.query(Payable).count(),
            "CurrencyRate": session.query(CurrencyRate).count(),
            "LiquidityScenario": session.query(LiquidityScenario).count(),
            "ForecastRun": session.query(ForecastRun).count(),
            "CashFlowForecast": session.query(CashFlowForecast).count(),
        }

        print("\nLIQUIDITYIQ DATA VALIDATION")
        print("=" * 55)

        for name, count in counts.items():
            print(f"{name:25} {count:>10}")

        print("\nVALIDATION RESULTS")
        print("=" * 55)

        for result in results:
            print(
                f"[{result['status']}] "
                f"{result['check']} - {result['details']}"
            )

        passed = sum(
            1 for result in results
            if result["status"] == "PASS"
        )

        failed = len(results) - passed

        print("\nSUMMARY")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total checks: {len(results)}")

        return {
            "counts": counts,
            "results": results,
            "passed": passed,
            "failed": failed,
        }

    finally:
        session.close()


if __name__ == "__main__":
    validate_dataset()
