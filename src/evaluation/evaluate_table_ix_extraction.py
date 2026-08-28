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
    / "table_ix_parameter_tuning.csv"
)

EXTRACTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
    / "table_ix_extracted_rows.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "results" / "evaluation"

DETAIL_PATH = (
    OUTPUT_DIR
    / "table_ix_extraction_evaluation.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "table_ix_extraction_metrics.json"
)


PARAMETER_TO_ROW = {
    "Positive electrode diffusion coefficient": 1,
    "Negative electrode diffusion coefficient": 2,
    "Positive electrode maximum concentration": 3,
    "Negative electrode maximum concentration": 4,
    "Positive electrode 100% SOC stoichiometry": 5,
}

BRUGGEMAN_ROW = 6

COMPONENT_INDEX = {
    "positive_electrode": 0,
    "separator": 1,
    "negative_electrode": 2,
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""

    text = str(value).strip()

    replacements = {
        "\u2212": "-",
        "\u00a0": "",
        "\u00ad": "",
        "\u2219": "\u00b7",
    }

    for old, new in replacements.items():
        if old:
            text = text.replace(old, new)

    return text.replace(" ", "")


def parse_number(value: object) -> float | None:
    text = normalize_text(value)

    if not text or text in {
        "-",
        "\u2013",
        "\u2014",
    }:
        return None

    scientific_match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
        r"(?:\u00b7|\u00d7|\u2219)"
        r"10\^?([+-]?\d+)",
        text,
    )

    if scientific_match:
        coefficient = float(
            scientific_match.group(1)
        )
        exponent = int(scientific_match.group(2))

        return coefficient * (10 ** exponent)

    decimal_match = re.fullmatch(
        r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
        text,
    )

    if decimal_match:
        return float(text)

    return None


def parse_number_list(
    value: object,
) -> list[float]:
    text = normalize_text(value)

    if not text:
        return []

    parsed_values = []

    for part in text.split("/"):
        parsed = parse_number(part)

        if parsed is None:
            raise ValueError(
                f"Unable to parse numeric part: {part!r}"
            )

        parsed_values.append(parsed)

    return parsed_values


def values_match(
    expected: float,
    predicted: float | None,
) -> bool:
    if predicted is None:
        return False

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

    if len(ground_truth) != 8:
        raise ValueError(
            "Expected eight Table IX ground-truth "
            f"records, obtained {len(ground_truth)}."
        )

    if len(extraction) != 6:
        raise ValueError(
            "Expected six extracted Table IX rows, "
            f"obtained {len(extraction)}."
        )

    extracted_rows = extraction.set_index(
        "row_number"
    ).to_dict("index")

    bruggeman_row = extracted_rows[BRUGGEMAN_ROW]

    bruggeman_experiments = parse_number_list(
        bruggeman_row["experiment_raw"]
    )

    bruggeman_simulation = parse_number(
        bruggeman_row["simulation_raw"]
    )

    bruggeman_variations = parse_number_list(
        bruggeman_row["variation_raw"]
    )

    if len(bruggeman_experiments) != 3:
        raise ValueError(
            "Three experimental Bruggeman values "
            "were expected."
        )

    if len(bruggeman_variations) != 3:
        raise ValueError(
            "Three Bruggeman variation values "
            "were expected."
        )

    if bruggeman_simulation is None:
        raise ValueError(
            "The tuned Bruggeman value is missing."
        )

    evaluation_records = []

    true_positive_count = 0
    false_positive_count = 0
    false_negative_count = 0
    predicted_value_count = 0

    for _, truth_row in ground_truth.iterrows():
        parameter_name = str(
            truth_row["parameter_raw"]
        )

        component = str(truth_row["component"])

        expected_experiment = float(
            truth_row["experimental_value"]
        )

        expected_simulation = float(
            truth_row["simulation_value"]
        )

        expected_variation = float(
            truth_row["reported_variation_percent"]
        )

        if parameter_name == "Bruggeman constant":
            if component not in COMPONENT_INDEX:
                raise KeyError(
                    "Unknown Bruggeman component: "
                    f"{component}"
                )

            component_index = COMPONENT_INDEX[component]

            extracted_row = bruggeman_row

            predicted_experiment = (
                bruggeman_experiments[component_index]
            )

            predicted_simulation = (
                bruggeman_simulation
            )

            predicted_variation = (
                bruggeman_variations[component_index]
            )

        else:
            if parameter_name not in PARAMETER_TO_ROW:
                raise KeyError(
                    "No Table IX row mapping for: "
                    f"{parameter_name}"
                )

            row_number = PARAMETER_TO_ROW[
                parameter_name
            ]

            extracted_row = extracted_rows[row_number]

            predicted_experiment = parse_number(
                extracted_row["experiment_raw"]
            )

            predicted_simulation = parse_number(
                extracted_row["simulation_raw"]
            )

            predicted_variation = parse_number(
                extracted_row["variation_raw"]
            )

        comparisons = {
            "experiment": (
                expected_experiment,
                predicted_experiment,
            ),
            "simulation": (
                expected_simulation,
                predicted_simulation,
            ),
            "variation": (
                expected_variation,
                predicted_variation,
            ),
        }

        field_matches = {}

        for field_name, (
            expected,
            predicted,
        ) in comparisons.items():
            matched = values_match(
                expected,
                predicted,
            )

            field_matches[field_name] = matched

            if predicted is not None:
                predicted_value_count += 1

            if matched:
                true_positive_count += 1
            else:
                false_negative_count += 1

                if predicted is not None:
                    false_positive_count += 1

        record_matches = all(field_matches.values())

        evaluation_records.append(
            {
                "record_id": truth_row["record_id"],
                "parameter_raw": parameter_name,
                "component": component,
                "extracted_parameter_raw":
                    extracted_row["parameter_raw"],
                "experiment_raw":
                    extracted_row["experiment_raw"],
                "expected_experiment":
                    expected_experiment,
                "predicted_experiment":
                    predicted_experiment,
                "experiment_match":
                    field_matches["experiment"],
                "simulation_raw":
                    extracted_row["simulation_raw"],
                "expected_simulation":
                    expected_simulation,
                "predicted_simulation":
                    predicted_simulation,
                "simulation_match":
                    field_matches["simulation"],
                "variation_raw":
                    extracted_row["variation_raw"],
                "expected_variation_percent":
                    expected_variation,
                "predicted_variation_percent":
                    predicted_variation,
                "variation_match":
                    field_matches["variation"],
                "evaluation_status": (
                    "exact_match"
                    if record_matches
                    else "value_mismatch"
                ),
            }
        )

    expected_value_count = len(ground_truth) * 3

    precision = (
        true_positive_count
        / (
            true_positive_count
            + false_positive_count
        )
        if (
            true_positive_count
            + false_positive_count
        )
        else 0.0
    )

    recall = (
        true_positive_count
        / (
            true_positive_count
            + false_negative_count
        )
        if (
            true_positive_count
            + false_negative_count
        )
        else 0.0
    )

    f1_score = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    detail = pd.DataFrame(evaluation_records)

    exact_record_count = int(
        (
            detail["evaluation_status"]
            == "exact_match"
        ).sum()
    )

    status_counts = {
        str(status): int(count)
        for status, count in detail[
            "evaluation_status"
        ].value_counts().items()
    }

    validation_passed = (
        expected_value_count == 24
        and predicted_value_count == 24
        and true_positive_count == 24
        and false_positive_count == 0
        and false_negative_count == 0
        and exact_record_count == 8
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail.to_csv(DETAIL_PATH, index=False)

    summary = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "table_id": "Table IX",
        "ground_truth_record_count": int(
            len(ground_truth)
        ),
        "extracted_table_row_count": int(
            len(extraction)
        ),
        "expected_numeric_value_count":
            expected_value_count,
        "predicted_numeric_value_count":
            predicted_value_count,
        "true_positive_count":
            true_positive_count,
        "false_positive_count":
            false_positive_count,
        "false_negative_count":
            false_negative_count,
        "exact_record_count":
            exact_record_count,
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
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=== TABLE IX EXTRACTION EVALUATION ===")
    print(
        "Ground-truth records:",
        len(ground_truth),
    )
    print(
        "Extracted table rows:",
        len(extraction),
    )
    print(
        "Expected numeric values:",
        expected_value_count,
    )
    print(
        "Predicted numeric values:",
        predicted_value_count,
    )
    print(
        "True positives:",
        true_positive_count,
    )
    print(
        "False positives:",
        false_positive_count,
    )
    print(
        "False negatives:",
        false_negative_count,
    )
    print(
        "Exact records:",
        exact_record_count,
    )
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1_score:.4f}")
    print(
        "Status counts:",
        status_counts,
    )
    print(
        "Validation passed:",
        validation_passed,
    )
    print(f"Details: {DETAIL_PATH}")
    print(f"Summary: {SUMMARY_PATH}")

    if not validation_passed:
        print()
        print("=== NON-MATCHING RECORDS ===")

        problems = detail[
            detail["evaluation_status"]
            != "exact_match"
        ]

        if problems.empty:
            print(
                "No record-level mismatch found. "
                "Inspect value counts."
            )
        else:
            print(
                problems.to_string(index=False)
            )

        raise RuntimeError(
            "Table IX extraction evaluation failed."
        )


if __name__ == "__main__":
    main()
