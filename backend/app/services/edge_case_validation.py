
import json
from pathlib import Path
from collections import Counter


def detect_edge_cases(file_path="data/ground_truth/edge_case_records.json"):
    with open(file_path, "r", encoding="utf-8") as file:
        records = json.load(file)

    results = []

    # EDGE-001: Opening balance reconciliation
    record = next(r for r in records if r["case_id"] == "EDGE-001")
    calculated = (
        record["opening_balance"]
        + record["total_inflows"]
        - record["total_outflows"]
    )

    results.append({
        "case_id": "EDGE-001",
        "detected": calculated != record["reported_closing_balance"],
        "decision": "FLAG_RECONCILIATION_FAILURE",
    })

    # EDGE-002: Missing FX rate
    record = next(r for r in records if r["case_id"] == "EDGE-002")

    results.append({
        "case_id": "EDGE-002",
        "detected": record["fx_rate_available"] is False,
        "decision": "FLAG_MISSING_FX_RATE",
    })

    # EDGE-003: Duplicate cash flow
    duplicate_records = [
        r for r in records if r["case_id"] == "EDGE-003"
    ]

    cash_flow_counts = Counter(
        r["cash_flow_id"] for r in duplicate_records
    )

    duplicate_found = any(
        count > 1 for count in cash_flow_counts.values()
    )

    results.append({
        "case_id": "EDGE-003",
        "detected": duplicate_found,
        "decision": "FLAG_DUPLICATE",
    })

    # EDGE-004: Actual posted after forecast cutoff
    record = next(r for r in records if r["case_id"] == "EDGE-004")

    results.append({
        "case_id": "EDGE-004",
        "detected": record["posting_date"] > record["forecast_cutoff_date"],
        "decision": "EXCLUDE_FROM_ORIGINAL_FORECAST",
    })

    # EDGE-005: Mixed currencies without conversion
    record = next(r for r in records if r["case_id"] == "EDGE-005")

    mixed_currency = (
        record["cash_flow_a"]["currency"]
        != record["cash_flow_b"]["currency"]
    )

    results.append({
        "case_id": "EDGE-005",
        "detected": mixed_currency,
        "decision": "FLAG_CURRENCY_MISMATCH",
    })

    print("\nLIQUIDITYIQ EDGE-CASE DETECTION")
    print("--------------------------------")

    for result in results:
        status = "PASS" if result["detected"] else "FAIL"
        print(
            f'{result["case_id"]}: {status} | '
            f'{result["decision"]}'
        )

    passed = sum(result["detected"] for result in results)

    print("--------------------------------")
    print(f"Detected: {passed}/{len(results)}")

    return results


if __name__ == "__main__":
    detect_edge_cases()
