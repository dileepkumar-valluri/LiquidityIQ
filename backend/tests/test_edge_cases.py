
import json
from pathlib import Path

import pytest

from backend.app.services.edge_case_validation import detect_edge_cases


@pytest.fixture
def edge_case_file(tmp_path):
    """Create an isolated copy of the edge-case dataset."""
    source = Path("data/ground_truth/edge_case_records.json")

    records = json.loads(source.read_text(encoding="utf-8"))

    test_file = tmp_path / "edge_case_records.json"
    test_file.write_text(
        json.dumps(records),
        encoding="utf-8"
    )

    return test_file


def test_all_five_edge_cases_are_detected(edge_case_file):
    results = detect_edge_cases(str(edge_case_file))

    assert len(results) == 5
    assert all(result["detected"] for result in results)


@pytest.mark.parametrize(
    ("case_id", "expected_decision"),
    [
        ("EDGE-001", "FLAG_RECONCILIATION_FAILURE"),
        ("EDGE-002", "FLAG_MISSING_FX_RATE"),
        ("EDGE-003", "FLAG_DUPLICATE"),
        ("EDGE-004", "EXCLUDE_FROM_ORIGINAL_FORECAST"),
        ("EDGE-005", "FLAG_CURRENCY_MISMATCH"),
    ],
)
def test_edge_case_decisions(edge_case_file, case_id, expected_decision):
    results = detect_edge_cases(str(edge_case_file))

    result = next(item for item in results if item["case_id"] == case_id)

    assert result["detected"] is True
    assert result["decision"] == expected_decision


def test_missing_dataset_file_raises_error(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        detect_edge_cases(str(missing_file))
