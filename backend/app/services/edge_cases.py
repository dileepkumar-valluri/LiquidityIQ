
import json
from pathlib import Path
from datetime import date


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


def generate_edge_cases():
    output_dir = Path("data/ground_truth")
    output_dir.mkdir(parents=True, exist_ok=True)

    ground_truth_path = output_dir / "ground_truth.json"

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

    print("Ground truth generated:", ground_truth_path)
    print("Labelled edge cases:", len(GROUND_TRUTH))

    return GROUND_TRUTH


if __name__ == "__main__":
    generate_edge_cases()
