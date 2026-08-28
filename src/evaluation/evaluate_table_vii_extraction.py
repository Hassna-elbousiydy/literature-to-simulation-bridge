from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "ground_truth"
    / "chen2020"
    / "table_vii_numeric_parameters.csv"
)

EXTRACTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
    / "table_vii_extracted_rows.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
)

DETAIL_PATH = OUTPUT_DIR / "table_vii_extraction_evaluation.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_vii_extraction_metrics.json"


PARAMETER_TO_ROW = {
    "Current collector thickness": 2,
    "Electrode thickness": 3,
    "Electrode length": 4,
    "Electrode width": 5,
    "Mean particle radius": 6,
    "Electrolyte volume fraction": 7,
    "Active material volume fraction": 8,
    "Bruggeman exponent": 9,
    "Solid phase lithium diffusivity": 10,
    "Solid phase electronic conductivity": 11,
    "Maximum concentration": 12,
    "Stoichiometry at 0% SOC": 13,
    "Stoichiometry at 100% SOC": 14,
    "Transference number": 17,
    "Initial electrolyte concentration": 18,
    "Activation energy": 20,
    "Reaction rate": 21,
}


COMPONENT_TO_COLUMN = {
    "positive_current_collector": "positive_electrode_raw",
    "negative_current_collector": "negative_electrode_raw",
    "positive_electrode": "positive_electrode_raw",
    "separator": "separator_raw",
    "negative_electrode": "negative_electrode_raw",
    "cell": "positive_electrode_raw",
    "electrolyte": "separator_raw",
}


def parse_numeric_value(
    raw_value: object,
    unit_raw: str,
) -> float | None:
    if pd.isna(raw_value):
        return None

    text = str(raw_value).strip()

    if not text or text in {"\u2014", "-", "\u2013"}:
        return None

    text = (
        text.replace("\u2212", "-")
        .replace("\u00a0", "")
        .replace(" ", "")
    )

    scientific_pattern = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
        r"(?:\u00b7|\u00d7)10\^?([+-]?\d+)",
        text,
    )

    if scientific_pattern:
        coefficient = float(scientific_pattern.group(1))
        exponent = int(scientific_pattern.group(2))
        value = coefficient * (10 ** exponent)
    else:
        decimal_pattern = re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
            text,
        )

        if not decimal_pattern:
            return None

        value = float(text)

    if "%" in str(unit_raw):
        value = value / 100

    return value


def values_match(
    expected: float,
    predicted: float,
) -> bool:
    return math.isclose(
        expected,
        predicted,
        rel_tol=1e-10,
        abs_tol=1e-18,
    )


def main() -> None:
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(GROUND_TRUTH_PATH)

    if not EXTRACTION_PATH.exists():
        raise FileNotFoundError(EXTRACTION_PATH)

    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)

    extraction = pd.read_csv(
        EXTRACTION_PATH,
        keep_default_na=False,
    )

    if len(ground_truth) != 33:
        raise ValueError(
            f"Expected 33 ground-truth records, "
            f"obtained {len(ground_truth)}."
        )

    if len(extraction) != 21:
        raise ValueError(
            f"Expected 21 extracted rows, "
            f"obtained {len(extraction)}."
        )

    extraction_lookup = extraction.set_index(
        "row_number"
    ).to_dict("index")

    expected_cells: dict[tuple[int, str], float] = {}
    predicted_cells: dict[tuple[int, str], float] = {}

    value_columns = [
        "positive_electrode_raw",
        "separator_raw",
        "negative_electrode_raw",
    ]

    for _, extracted_row in extraction.iterrows():
        row_number = int(extracted_row["row_number"])
        unit_raw = str(extracted_row["unit_raw"])

        for column_name in value_columns:
            parsed_value = parse_numeric_value(
                extracted_row[column_name],
                unit_raw,
            )

            if parsed_value is not None:
                predicted_cells[
                    (row_number, column_name)
                ] = parsed_value

    evaluation_records = []

    for _, truth_row in ground_truth.iterrows():
        parameter_name = str(truth_row["parameter_raw"])
        component = str(truth_row["component"])

        if parameter_name not in PARAMETER_TO_ROW:
            raise KeyError(
                f"No extracted-row mapping for: {parameter_name}"
            )

        if component not in COMPONENT_TO_COLUMN:
            raise KeyError(
                f"No extracted-column mapping for: {component}"
            )

        row_number = PARAMETER_TO_ROW[parameter_name]
        column_name = COMPONENT_TO_COLUMN[component]
        cell_key = (row_number, column_name)

        expected_value = float(
            truth_row["normalized_value"]
        )

        expected_cells[cell_key] = expected_value

        extracted_row = extraction_lookup[row_number]
        extracted_raw_value = extracted_row[column_name]

        predicted_value = predicted_cells.get(cell_key)

        if predicted_value is None:
            status = "missing_numeric_value"
            exact_match = False
            absolute_error = None
            relative_error_percent = None
        else:
            exact_match = values_match(
                expected_value,
                predicted_value,
            )

            absolute_error = abs(
                predicted_value - expected_value
            )

            if expected_value == 0:
                relative_error_percent = (
                    0.0
                    if predicted_value == 0
                    else None
                )
            else:
                relative_error_percent = (
                    absolute_error
                    / abs(expected_value)
                    * 100
                )

            status = (
                "exact_match"
                if exact_match
                else "value_mismatch"
            )

        evaluation_records.append(
            {
                "record_id": truth_row["record_id"],
                "parameter_raw": parameter_name,
                "component": component,
                "row_number": row_number,
                "extracted_column": column_name,
                "extracted_raw_value": extracted_raw_value,
                "expected_normalized_value": expected_value,
                "predicted_normalized_value":
                    predicted_value,
                "absolute_error": absolute_error,
                "relative_error_percent":
                    relative_error_percent,
                "evaluation_status": status,
            }
        )

    expected_keys = set(expected_cells)
    predicted_keys = set(predicted_cells)

    matched_keys = {
        key
        for key in expected_keys & predicted_keys
        if values_match(
            expected_cells[key],
            predicted_cells[key],
        )
    }

    mismatched_keys = (
        expected_keys & predicted_keys
    ) - matched_keys

    false_positive_keys = (
        predicted_keys - expected_keys
    ) | mismatched_keys

    false_negative_keys = (
        expected_keys - predicted_keys
    ) | mismatched_keys

    true_positive_count = len(matched_keys)
    false_positive_count = len(false_positive_keys)
    false_negative_count = len(false_negative_keys)

    precision = (
        true_positive_count
        / (true_positive_count + false_positive_count)
        if true_positive_count + false_positive_count
        else 0.0
    )

    recall = (
        true_positive_count
        / (true_positive_count + false_negative_count)
        if true_positive_count + false_negative_count
        else 0.0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    detail = pd.DataFrame(evaluation_records)

    status_counts = {
        str(status): int(count)
        for status, count in detail[
            "evaluation_status"
        ].value_counts().items()
    }

    validation_passed = (
        len(expected_cells) == 33
        and len(predicted_cells) == 33
        and true_positive_count == 33
        and false_positive_count == 0
        and false_negative_count == 0
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail.to_csv(DETAIL_PATH, index=False)

    summary = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "table_id": "Table VII",
        "ground_truth_record_count": int(
            len(ground_truth)
        ),
        "extracted_table_row_count": int(
            len(extraction)
        ),
        "expected_numeric_cell_count": int(
            len(expected_cells)
        ),
        "predicted_numeric_cell_count": int(
            len(predicted_cells)
        ),
        "true_positive_count": true_positive_count,
        "false_positive_count": false_positive_count,
        "false_negative_count": false_negative_count,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(f1_score, 6),
        "status_counts": status_counts,
        "validation_passed": validation_passed,
        "detail_file": str(
            DETAIL_PATH.relative_to(PROJECT_ROOT)
        ),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== TABLE VII EXTRACTION EVALUATION ===")
    print(
        "Ground-truth numeric cells:",
        len(expected_cells),
    )
    print(
        "Predicted numeric cells:",
        len(predicted_cells),
    )
    print("True positives:", true_positive_count)
    print("False positives:", false_positive_count)
    print("False negatives:", false_negative_count)
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1_score:.4f}")
    print(f"Status counts: {status_counts}")
    print(f"Validation passed: {validation_passed}")
    print(f"Details: {DETAIL_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    if not validation_passed:
        print()
        print("=== NON-MATCHING RECORDS ===")

        problems = detail[
            detail["evaluation_status"] != "exact_match"
        ]

        if problems.empty:
            print("No value mismatch in expected records.")
            print(
                "Check unexpected additional numeric cells."
            )
        else:
            print(
                problems[
                    [
                        "record_id",
                        "parameter_raw",
                        "component",
                        "extracted_raw_value",
                        "expected_normalized_value",
                        "predicted_normalized_value",
                        "evaluation_status",
                    ]
                ].to_string(index=False)
            )

        raise RuntimeError(
            "Table VII extraction evaluation failed."
        )


if __name__ == "__main__":
    main()

