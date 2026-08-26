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
    / "table_ix_parameter_tuning.csv"
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

COMPARISON_PATH = OUTPUT_DIR / "table_ix_pybamm_comparison.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_ix_pybamm_comparison_summary.json"


def main() -> None:
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground-truth file not found: {GROUND_TRUTH_PATH}"
        )

    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"PyBaMM registry not found: {REGISTRY_PATH}"
        )

    ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
    registry = pd.read_csv(REGISTRY_PATH)

    required_ground_truth_columns = {
        "record_id",
        "parameter_raw",
        "component",
        "simulation_value",
        "candidate_pybamm_parameter_name",
        "mapping_status",
    }

    required_registry_columns = {
        "parameter_name",
        "value_type",
        "numeric_value",
    }

    missing_ground_truth = (
        required_ground_truth_columns - set(ground_truth.columns)
    )
    missing_registry = required_registry_columns - set(registry.columns)

    if missing_ground_truth:
        raise ValueError(
            "Missing ground-truth columns: "
            f"{sorted(missing_ground_truth)}"
        )

    if missing_registry:
        raise ValueError(
            "Missing registry columns: "
            f"{sorted(missing_registry)}"
        )

    registry_lookup = registry.set_index("parameter_name").to_dict("index")

    comparison = ground_truth.copy()

    comparison["pybamm_value"] = pd.NA
    comparison["absolute_difference"] = pd.NA
    comparison["relative_difference_percent"] = pd.NA
    comparison["comparison_status"] = ""
    comparison["comparison_notes"] = ""

    for index, row in comparison.iterrows():
        candidate_name = row.get("candidate_pybamm_parameter_name")

        if pd.isna(candidate_name) or not str(candidate_name).strip():
            comparison.at[index, "comparison_status"] = (
                "not_directly_mapped"
            )
            comparison.at[index, "comparison_notes"] = (
                "The paper value requires a conversion or derived "
                "initial-condition mapping."
            )
            continue

        candidate_name = str(candidate_name).strip()

        if candidate_name not in registry_lookup:
            comparison.at[index, "comparison_status"] = (
                "parameter_not_found"
            )
            comparison.at[index, "comparison_notes"] = (
                "Candidate parameter name was not found in the "
                "exported PyBaMM registry."
            )
            continue

        registry_record = registry_lookup[candidate_name]
        raw_pybamm_value = registry_record.get("numeric_value")

        if pd.isna(raw_pybamm_value) or str(raw_pybamm_value).strip() == "":
            comparison.at[index, "comparison_status"] = (
                "non_numeric_pybamm_value"
            )
            comparison.at[index, "comparison_notes"] = (
                "The corresponding PyBaMM value is not a numeric scalar."
            )
            continue

        paper_value = float(row["simulation_value"])
        pybamm_value = float(raw_pybamm_value)

        absolute_difference = abs(pybamm_value - paper_value)

        if paper_value == 0:
            relative_difference_percent = (
                0.0 if pybamm_value == 0 else float("inf")
            )
        else:
            relative_difference_percent = (
                absolute_difference / abs(paper_value) * 100
            )

        values_match = math.isclose(
            paper_value,
            pybamm_value,
            rel_tol=1e-12,
            abs_tol=1e-18,
        )

        comparison.at[index, "pybamm_value"] = pybamm_value
        comparison.at[index, "absolute_difference"] = absolute_difference
        comparison.at[
            index,
            "relative_difference_percent",
        ] = relative_difference_percent

        if values_match:
            comparison.at[index, "comparison_status"] = "exact_match"
            comparison.at[index, "comparison_notes"] = (
                "The paper simulation value matches the exported "
                "PyBaMM Chen2020 value."
            )
        else:
            comparison.at[index, "comparison_status"] = "value_mismatch"
            comparison.at[index, "comparison_notes"] = (
                "The paper simulation value differs from the exported "
                "PyBaMM Chen2020 value."
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)

    status_counts = {
        str(status): int(count)
        for status, count in comparison[
            "comparison_status"
        ].value_counts().items()
    }

    blocking_statuses = {
        "parameter_not_found",
        "non_numeric_pybamm_value",
        "value_mismatch",
    }

    blocking_records = comparison[
        comparison["comparison_status"].isin(blocking_statuses)
    ]

    summary = {
        "ground_truth_file": str(
            GROUND_TRUTH_PATH.relative_to(PROJECT_ROOT)
        ),
        "registry_file": str(REGISTRY_PATH.relative_to(PROJECT_ROOT)),
        "comparison_file": str(COMPARISON_PATH.relative_to(PROJECT_ROOT)),
        "record_count": int(len(comparison)),
        "status_counts": status_counts,
        "exact_match_count": int(
            (comparison["comparison_status"] == "exact_match").sum()
        ),
        "not_directly_mapped_count": int(
            (
                comparison["comparison_status"]
                == "not_directly_mapped"
            ).sum()
        ),
        "blocking_record_count": int(len(blocking_records)),
        "validation_passed": bool(blocking_records.empty),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== TABLE IX TO PYBAMM COMPARISON ===")
    print(f"Records: {len(comparison)}")
    print(f"Status counts: {status_counts}")
    print(f"Validation passed: {blocking_records.empty}")
    print()

    print(
        comparison[
            [
                "component",
                "parameter_raw",
                "simulation_value",
                "pybamm_value",
                "comparison_status",
            ]
        ].to_string(index=False)
    )

    print()
    print(f"Comparison CSV: {COMPARISON_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    if not blocking_records.empty:
        raise RuntimeError(
            "Comparison contains missing parameters or value mismatches."
        )


if __name__ == "__main__":
    main()
