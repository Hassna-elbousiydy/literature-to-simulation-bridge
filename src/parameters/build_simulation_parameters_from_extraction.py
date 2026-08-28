from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd
import pybamm


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXTRACTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
    / "table_ix_extracted_rows.csv"
)

EVALUATION_PATH = (
    PROJECT_ROOT
    / "results"
    / "evaluation"
    / "table_ix_extraction_metrics.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
)

OVERRIDES_PATH = (
    OUTPUT_DIR
    / "pybamm_overrides_from_table_ix.json"
)

PROVENANCE_PATH = (
    OUTPUT_DIR
    / "pybamm_overrides_from_table_ix_provenance.json"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "pybamm_overrides_from_table_ix_summary.json"
)


ROW_MAPPINGS = {
    1: [
        {
            "pybamm_parameter_name":
                "Positive particle diffusivity [m2.s-1]",
            "normalized_unit": "m2.s-1",
        }
    ],
    2: [
        {
            "pybamm_parameter_name":
                "Negative particle diffusivity [m2.s-1]",
            "normalized_unit": "m2.s-1",
        }
    ],
    3: [
        {
            "pybamm_parameter_name": (
                "Maximum concentration in positive "
                "electrode [mol.m-3]"
            ),
            "normalized_unit": "mol.m-3",
        }
    ],
    4: [
        {
            "pybamm_parameter_name": (
                "Maximum concentration in negative "
                "electrode [mol.m-3]"
            ),
            "normalized_unit": "mol.m-3",
        }
    ],
    6: [
        {
            "pybamm_parameter_name": (
                "Positive electrode Bruggeman "
                "coefficient (electrolyte)"
            ),
            "normalized_unit": "dimensionless",
        },
        {
            "pybamm_parameter_name": (
                "Separator Bruggeman coefficient "
                "(electrolyte)"
            ),
            "normalized_unit": "dimensionless",
        },
        {
            "pybamm_parameter_name": (
                "Negative electrode Bruggeman "
                "coefficient (electrolyte)"
            ),
            "normalized_unit": "dimensionless",
        },
    ],
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


def parse_number(value: object) -> float:
    text = normalize_text(value)

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

    raise ValueError(
        f"Unable to parse simulation value: {value!r}"
    )


def main() -> None:
    if not EXTRACTION_PATH.exists():
        raise FileNotFoundError(EXTRACTION_PATH)

    if not EVALUATION_PATH.exists():
        raise FileNotFoundError(EVALUATION_PATH)

    evaluation = json.loads(
        EVALUATION_PATH.read_text(encoding="utf-8")
    )

    if not evaluation.get("validation_passed"):
        raise RuntimeError(
            "Table IX extraction must be validated "
            "before creating PyBaMM overrides."
        )

    extraction = pd.read_csv(
        EXTRACTION_PATH,
        keep_default_na=False,
    )

    if len(extraction) != 6:
        raise ValueError(
            "Expected six extracted Table IX rows, "
            f"obtained {len(extraction)}."
        )

    extracted_rows = extraction.set_index(
        "row_number"
    ).to_dict("index")

    current_parameters = pybamm.ParameterValues(
        "Chen2020"
    )

    overrides: dict[str, float] = {}
    provenance_records = []

    current_pybamm_match_count = 0

    for row_number, mappings in ROW_MAPPINGS.items():
        extracted_row = extracted_rows[row_number]

        extracted_value = parse_number(
            extracted_row["simulation_raw"]
        )

        for mapping in mappings:
            parameter_name = mapping[
                "pybamm_parameter_name"
            ]

            current_value = float(
                current_parameters[parameter_name]
            )

            matches_current_pybamm = math.isclose(
                extracted_value,
                current_value,
                rel_tol=1e-12,
                abs_tol=1e-18,
            )

            if matches_current_pybamm:
                current_pybamm_match_count += 1

            overrides[parameter_name] = extracted_value

            provenance_records.append(
                {
                    "pybamm_parameter_name":
                        parameter_name,
                    "value": extracted_value,
                    "normalized_unit":
                        mapping["normalized_unit"],
                    "document_id":
                        "chen2020_parameterization",
                    "doi":
                        "10.1149/1945-7111/ab9050",
                    "table_id": "Table IX",
                    "pdf_page": 20,
                    "source_row_number":
                        row_number,
                    "source_extraction_id":
                        extracted_row[
                            "extraction_id"
                        ],
                    "source_parameter_raw":
                        extracted_row[
                            "parameter_raw"
                        ],
                    "source_simulation_raw":
                        extracted_row[
                            "simulation_raw"
                        ],
                    "mapping_status":
                        "direct_simulation_parameter",
                    "current_pybamm_value":
                        current_value,
                    "matches_current_pybamm":
                        matches_current_pybamm,
                }
            )

    if len(overrides) != 7:
        raise ValueError(
            f"Expected seven overrides, "
            f"obtained {len(overrides)}."
        )

    # Validate that every name exists in PyBaMM.
    validated_parameters = pybamm.ParameterValues(
        "Chen2020"
    )

    validated_parameters.update(
        overrides,
        check_already_exists=True,
    )

    excluded_records = [
        {
            "source_row_number": 5,
            "source_parameter_raw": (
                extracted_rows[5]["parameter_raw"]
            ),
            "source_simulation_raw": (
                extracted_rows[5]["simulation_raw"]
            ),
            "reason": (
                "Stoichiometry requires conversion to an "
                "initial concentration or SOC condition and "
                "is not a direct scalar override."
            ),
        }
    ]

    validation_passed = (
        len(overrides) == 7
        and current_pybamm_match_count == 7
        and all(
            record["matches_current_pybamm"]
            for record in provenance_records
        )
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    OVERRIDES_PATH.write_text(
        json.dumps(
            overrides,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    provenance = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "table_id": "Table IX",
        "pdf_page": 20,
        "parameter_records": provenance_records,
        "excluded_records": excluded_records,
    }

    PROVENANCE_PATH.write_text(
        json.dumps(
            provenance,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "source_table": "Table IX",
        "override_count": len(overrides),
        "excluded_record_count":
            len(excluded_records),
        "current_pybamm_match_count":
            current_pybamm_match_count,
        "pybamm_version": pybamm.__version__,
        "validation_passed": validation_passed,
        "overrides_file": str(
            OVERRIDES_PATH.relative_to(PROJECT_ROOT)
        ),
        "provenance_file": str(
            PROVENANCE_PATH.relative_to(PROJECT_ROOT)
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

    print(
        "=== LITERATURE TO PYBAMM OVERRIDES ==="
    )
    print("Overrides:", len(overrides))
    print(
        "Matches current PyBaMM:",
        current_pybamm_match_count,
    )
    print(
        "Excluded indirect records:",
        len(excluded_records),
    )
    print(
        "Validation passed:",
        validation_passed,
    )
    print(f"Overrides: {OVERRIDES_PATH}")
    print(f"Provenance: {PROVENANCE_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    print()

    for parameter_name, value in overrides.items():
        print(
            f"{parameter_name}: {value}"
        )

    if not validation_passed:
        raise RuntimeError(
            "Literature-to-PyBaMM override "
            "validation failed."
        )


if __name__ == "__main__":
    main()
