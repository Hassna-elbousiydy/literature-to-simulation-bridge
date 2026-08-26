from __future__ import annotations

import json
import math
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

REGISTRY_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "pybamm"
    / "chen2020_parameter_registry.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "ground_truth"
    / "chen2020"
)

COMPARISON_PATH = OUTPUT_DIR / "table_vii_pybamm_comparison.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_vii_pybamm_comparison_summary.json"


def main() -> None:
    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
    registry = pd.read_csv(REGISTRY_PATH)

    if len(ground_truth) != 33:
        raise ValueError(
            f"Expected 33 Table VII records, obtained {len(ground_truth)}."
        )

    registry_lookup = registry.set_index("parameter_name").to_dict("index")

    comparison = ground_truth.copy()
    comparison["pybamm_value"] = pd.NA
    comparison["absolute_difference"] = pd.NA
    comparison["relative_difference_percent"] = pd.NA
    comparison["comparison_status"] = ""
    comparison["comparison_notes"] = ""

    for index, row in comparison.iterrows():
        candidate = row.get("candidate_pybamm_parameter_name")
        expected_relation = str(row["expected_pybamm_relation"])
        paper_value = float(row["normalized_value"])

        candidate_is_missing = (
            pd.isna(candidate) or not str(candidate).strip()
        )

        if candidate_is_missing:
            if expected_relation == "not_directly_comparable":
                comparison.at[
                    index, "comparison_status"
                ] = "not_directly_comparable"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "The paper value requires conversion or inspection "
                    "inside a PyBaMM function."
                )
            else:
                comparison.at[
                    index, "comparison_status"
                ] = "missing_mapping"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "A direct or candidate PyBaMM mapping was expected."
                )

            continue

        candidate = str(candidate).strip()

        if candidate not in registry_lookup:
            comparison.at[
                index, "comparison_status"
            ] = "parameter_not_found"

            comparison.at[
                index, "comparison_notes"
            ] = "The candidate name is absent from the PyBaMM registry."

            continue

        registry_record = registry_lookup[candidate]
        raw_pybamm_value = registry_record.get("numeric_value")

        if pd.isna(raw_pybamm_value) or not str(raw_pybamm_value).strip():
            comparison.at[
                index, "comparison_status"
            ] = "non_numeric_pybamm_value"

            comparison.at[
                index, "comparison_notes"
            ] = "The mapped PyBaMM parameter is not a numeric scalar."

            continue

        pybamm_value = float(raw_pybamm_value)
        absolute_difference = abs(pybamm_value - paper_value)

        if paper_value == 0:
            relative_difference = (
                0.0 if pybamm_value == 0 else float("inf")
            )
        else:
            relative_difference = (
                absolute_difference / abs(paper_value) * 100
            )

        values_match = math.isclose(
            paper_value,
            pybamm_value,
            rel_tol=1e-12,
            abs_tol=1e-18,
        )

        comparison.at[index, "pybamm_value"] = pybamm_value
        comparison.at[
            index, "absolute_difference"
        ] = absolute_difference
        comparison.at[
            index, "relative_difference_percent"
        ] = relative_difference

        if expected_relation in {
            "expected_exact_match",
            "geometry_name_translation",
        }:
            if values_match:
                comparison.at[
                    index, "comparison_status"
                ] = "exact_match"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "The Table VII value matches the current "
                    "PyBaMM Chen2020 value."
                )
            else:
                comparison.at[
                    index, "comparison_status"
                ] = "unexpected_mismatch"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "The value was expected to match PyBaMM but differs."
                )

        elif (
            expected_relation
            == "expected_difference_table_ix_tuning"
        ):
            if values_match:
                comparison.at[
                    index, "comparison_status"
                ] = "unexpected_no_tuning_difference"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "The Table IX tuning indicated that this value "
                    "should differ."
                )
            else:
                comparison.at[
                    index, "comparison_status"
                ] = "expected_tuned_difference"

                comparison.at[
                    index, "comparison_notes"
                ] = (
                    "The difference is expected because Table IX "
                    "reports a tuned simulation value."
                )

        elif expected_relation == "not_directly_comparable":
            comparison.at[
                index, "comparison_status"
            ] = "not_directly_comparable"

        else:
            comparison.at[
                index, "comparison_status"
            ] = "unknown_expected_relation"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    status_counts = {
        str(status): int(count)
        for status, count in comparison[
            "comparison_status"
        ].value_counts().items()
    }

    expected_counts = {
        "exact_match": 18,
        "expected_tuned_difference": 7,
        "not_directly_comparable": 8,
    }

    blocking_statuses = {
        "missing_mapping",
        "parameter_not_found",
        "non_numeric_pybamm_value",
        "unexpected_mismatch",
        "unexpected_no_tuning_difference",
        "unknown_expected_relation",
    }

    blocking_records = comparison[
        comparison["comparison_status"].isin(blocking_statuses)
    ]

    counts_are_correct = all(
        status_counts.get(status, 0) == expected_count
        for status, expected_count in expected_counts.items()
    )

    validation_passed = (
        blocking_records.empty
        and counts_are_correct
        and len(comparison) == 33
    )

    summary = {
        "ground_truth_file": str(
            GROUND_TRUTH_PATH.relative_to(PROJECT_ROOT)
        ),
        "registry_file": str(
            REGISTRY_PATH.relative_to(PROJECT_ROOT)
        ),
        "comparison_file": str(
            COMPARISON_PATH.relative_to(PROJECT_ROOT)
        ),
        "record_count": int(len(comparison)),
        "status_counts": status_counts,
        "expected_status_counts": expected_counts,
        "blocking_record_count": int(len(blocking_records)),
        "validation_passed": bool(validation_passed),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== TABLE VII TO PYBAMM COMPARISON ===")
    print(f"Records: {len(comparison)}")
    print(f"Status counts: {status_counts}")
    print(f"Blocking records: {len(blocking_records)}")
    print(f"Validation passed: {validation_passed}")
    print()
    print(f"Comparison CSV: {COMPARISON_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    if not validation_passed:
        if not blocking_records.empty:
            print()
            print("=== BLOCKING RECORDS ===")
            print(
                blocking_records[
                    [
                        "record_id",
                        "parameter_raw",
                        "component",
                        "candidate_pybamm_parameter_name",
                        "comparison_status",
                    ]
                ].to_string(index=False)
            )

        raise RuntimeError(
            "Table VII comparison validation failed."
        )


if __name__ == "__main__":
    main()
