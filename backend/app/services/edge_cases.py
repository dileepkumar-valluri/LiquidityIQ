
import json
import csv
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path("data/ground_truth")

GROUND_TRUTH = [
    {
        "case_id": "EDGE-001",
        "issue_type": "OPENING_BALANCE_MISMATCH",
        "description": "Opening balance plus ledger activity does not equal closing balance.",
        "expected_decision": "FLAG_RECONCILIATION_FAILURE",
    },
    {
        "case_id": "EDGE-002",
        "issue_type": "MISSING_FX_RATE",
        "description": "A foreign currency cash flow has no applicable FX rate.",
        "expected_decision": "FLAG_MISSING_FX_RATE",
    },
    {
        "case_id": "EDGE-003",
        "issue_type": "DUPLICATE_CASH_FLOW",
        "description": "The same cash flow is counted twice.",
        "expected_decision": "FLAG_DUPLICATE",
    },
    {
        "case_id": "EDGE-004",
        "issue_type": "ACTUAL_AFTER_CUTOFF",
        "description": "An actual transaction posted after the forecast cutoff must not affect the original forecast.",
        "expected_decision": "EXCLUDE_FROM_ORIGINAL_FORECAST",
    },
    {
        "case_id": "EDGE-005",
        "issue_type": "UNCONVERTED_CURRENCY",
        "description": "Cash flows in different currencies are added without conversion.",
        "expected_decision": "FLAG_CURRENCY_MISMATCH",
    },
]


# Synthetic anomaly records.
# These records are isolated from the clean production dataset.
EDGE_CASE_RECORDS = [
    {
        "case_id": "EDGE-001",
        "record_id": "ANOM-001",
        "record_type": "BALANCE_RECONCILIATION",
        "opening_balance": 10000.00,
        "total_inflows": 2500.00,
        "total_outflows": 1000.00,
        "reported_closing_balance": 12000.00,
        "calculated_closing_balance": 11500.00,
        "currency": "INR",
    },
    {
        "case_id": "EDGE-002",
        "record_id": "ANOM-002",
        "record_type": "FX_CONVERSION",
        "source_currency": "JPY",
        "target_currency": "INR",
        "amount": 50000.00,
        "effective_date": "2026-11-01",
        "fx_rate_available": False,
    },
    {
        "case_id": "EDGE-003",
        "record_id": "ANOM-003",
        "record_type": "DUPLICATE_CASH_FLOW",
        "cash_flow_id": "CF-EDGE-003",
        "expected_date": "2026-11-05",
        "amount": 25000.00,
        "currency": "INR",
        "flow_type": "INFLOW",
        "duplicate_occurrence": 1,
    },
    {
        "case_id": "EDGE-003",
        "record_id": "ANOM-004",
        "record_type": "DUPLICATE_CASH_FLOW",
        "cash_flow_id": "CF-EDGE-003",
        "expected_date": "2026-11-05",
        "amount": 25000.00,
        "currency": "INR",
        "flow_type": "INFLOW",
        "duplicate_occurrence": 2,
    },
    {
        "case_id": "EDGE-004",
        "record_id": "ANOM-005",
        "record_type": "ACTUAL_AFTER_CUTOFF",
        "transaction_id": "LED-EDGE-004",
        "transaction_date": "2026-11-01",
        "posting_date": "2026-11-02",
        "forecast_cutoff_date": "2026-10-31",
        "amount": 18000.00,
        "currency": "INR",
        "flow_type": "INFLOW",
    },
    {
        "case_id": "EDGE-005",
        "record_id": "ANOM-006",
        "record_type": "UNCONVERTED_CURRENCY",
        "cash_flow_a": {
            "amount": 1000.00,
            "currency": "USD",
        },
        "cash_flow_b": {
            "amount": 1000.00,
            "currency": "EUR",
        },
        "incorrect_total": 2000.00,
        "reporting_currency": "INR",
    },
]


def generate_edge_cases():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ground_truth_path = OUTPUT_DIR / "ground_truth.json"
    records_json_path = OUTPUT_DIR / "edge_case_records.json"
    records_csv_path = OUTPUT_DIR / "edge_case_records.csv"

    # Export expected labels separately.
    with open(ground_truth_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "dataset": "LiquidityIQ",
                "generated_on": str(date.today()),
                "edge_cases": GROUND_TRUTH,
            },
            file,
            indent=4,
        )

    # Export synthetic anomaly records separately.
    with open(records_json_path, "w", encoding="utf-8") as file:
        json.dump(EDGE_CASE_RECORDS, file, indent=4)

    # CSV stores nested values as JSON strings.
    with open(records_csv_path, "w", newline="", encoding="utf-8") as file:
        fieldnames = sorted({
            key
            for record in EDGE_CASE_RECORDS
            for key in record.keys()
        })

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )
        writer.writeheader()

        for record in EDGE_CASE_RECORDS:
            writer.writerow({
                key: json.dumps(value) if isinstance(value, dict) else value
                for key, value in record.items()
            })

    print("Ground truth generated:", ground_truth_path)
    print("Anomaly records generated:", records_json_path)
    print("Anomaly CSV generated:", records_csv_path)
    print("Ground-truth labels:", len(GROUND_TRUTH))
    print("Synthetic anomaly records:", len(EDGE_CASE_RECORDS))

    return GROUND_TRUTH, EDGE_CASE_RECORDS


if __name__ == "__main__":
    generate_edge_cases()
