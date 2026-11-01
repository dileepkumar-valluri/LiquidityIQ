
import pytest

from backend.app.services.validation import validate_dataset


@pytest.fixture(scope="module")
def validation_result():
    return validate_dataset()


def test_dataset_validation_has_no_failed_checks(validation_result):
    assert validation_result["failed"] == 0


def test_dataset_validation_has_expected_check_count(validation_result):
    assert len(validation_result["results"]) == 33


def test_all_primary_keys_are_unique(validation_result):
    pk_checks = [
        item for item in validation_result["results"]
        if item["check"].startswith("PK uniqueness:")
    ]

    assert len(pk_checks) == 9
    assert all(item["status"] == "PASS" for item in pk_checks)


def test_all_foreign_key_checks_pass(validation_result):
    fk_checks = [
        item for item in validation_result["results"]
        if " FK" in item["check"]
    ]

    assert len(fk_checks) == 10
    assert all(item["status"] == "PASS" for item in fk_checks)


def test_dataset_has_expected_starter_scale_counts(validation_result):
    expected_counts = {
        "LegalEntity": 3,
        "BankAccount": 15,
        "LedgerEntry": 1000,
        "Receivable": 200,
        "Payable": 200,
        "CurrencyRate": 80,
        "LiquidityScenario": 3,
        "ForecastRun": 3,
        "CashFlowForecast": 1200,
    }

    assert validation_result["counts"] == expected_counts


def test_negative_balances_are_reported_as_warnings(validation_result):
    balance_check = next(
        item for item in validation_result["results"]
        if item["check"] == "Closing balance calculation"
    )

    assert balance_check["status"] == "PASS"
    assert "Negative balances flagged=3" in balance_check["details"]
