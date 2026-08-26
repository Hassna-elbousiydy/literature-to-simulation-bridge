"""Export the PyBaMM Chen2020 parameter registry.

This registry represents the parameters implemented in PyBaMM. It does not
claim that every value has already been verified in the Chen et al. paper.
"""

from __future__ import annotations

import json
import numbers
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pybamm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "reference" / "pybamm"

CSV_PATH = OUTPUT_DIR / "chen2020_parameter_registry.csv"
JSON_PATH = OUTPUT_DIR / "chen2020_parameter_registry.json"
SUMMARY_PATH = OUTPUT_DIR / "chen2020_parameter_registry_summary.json"

PARAMETER_SET_NAME = "Chen2020"
CANDIDATE_SOURCE_DOI = "10.1149/1945-7111/ab9050"


def extract_unit(parameter_name: str) -> str:
    """Extract the final unit written between square brackets."""

    matches = re.findall(r"\[([^\[\]]+)\]", parameter_name)
    return matches[-1] if matches else ""


def serialize_value(value: Any) -> tuple[str, float | None, str]:
    """Classify and serialize a PyBaMM parameter value."""

    if isinstance(value, bool):
        return "boolean", None, str(value).lower()

    if isinstance(value, numbers.Real):
        return "scalar", float(value), ""

    if callable(value):
        function_name = getattr(
            value,
            "__qualname__",
            getattr(value, "__name__", type(value).__name__),
        )
        module_name = getattr(value, "__module__", "")

        callable_reference = (
            f"{module_name}.{function_name}"
            if module_name
            else function_name
        )

        return "function", None, callable_reference

    if isinstance(value, str):
        return "string", None, value

    if isinstance(value, (list, tuple, dict)):
        return "structured", None, json.dumps(value, default=str)

    return "object", None, repr(value)


def export_parameter_registry() -> None:
    """Export the complete Chen2020 registry from the installed PyBaMM."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    parameter_values = pybamm.ParameterValues(PARAMETER_SET_NAME)
    records: list[dict[str, Any]] = []

    for parameter_name, value in sorted(parameter_values.items()):
        value_type, numeric_value, text_value = serialize_value(value)

        records.append(
            {
                "parameter_name": parameter_name,
                "unit": extract_unit(parameter_name),
                "value_type": value_type,
                "numeric_value": numeric_value,
                "text_value": text_value,
                "parameter_set_name": PARAMETER_SET_NAME,
                "pybamm_version": pybamm.__version__,
                "candidate_source_doi": CANDIDATE_SOURCE_DOI,
                "paper_verification_status": "not_checked",
                "paper_page": "",
                "paper_table": "",
                "paper_raw_name": "",
                "paper_raw_value": "",
                "paper_raw_unit": "",
                "verification_notes": "",
            }
        )

    dataframe = pd.DataFrame(records)
    dataframe.to_csv(CSV_PATH, index=False)

    with JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    type_counts = dataframe["value_type"].value_counts().to_dict()

    try:
        parameter_set_description = pybamm.parameter_sets.get_docstring(
            PARAMETER_SET_NAME
        )
    except (AttributeError, KeyError):
        parameter_set_description = ""

    summary = {
        "parameter_set_name": PARAMETER_SET_NAME,
        "pybamm_version": pybamm.__version__,
        "candidate_source_doi": CANDIDATE_SOURCE_DOI,
        "total_parameters": int(len(dataframe)),
        "value_type_counts": {
            key: int(value)
            for key, value in type_counts.items()
        },
        "paper_verified_parameters": 0,
        "paper_verification_status": "not_started",
        "important_notice": (
            "The registry describes the PyBaMM implementation. "
            "Each value must still be verified against the scientific paper."
        ),
        "parameter_set_description": parameter_set_description,
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print("Chen2020 parameter registry exported successfully.")
    print(f"PyBaMM version: {pybamm.__version__}")
    print(f"Total parameters: {len(dataframe)}")

    for value_type, count in sorted(type_counts.items()):
        print(f"{value_type}: {count}")

    print(f"\nCSV: {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    export_parameter_registry()
