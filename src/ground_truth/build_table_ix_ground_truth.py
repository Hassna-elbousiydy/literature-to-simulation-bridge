from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "ground_truth" / "chen2020"

CSV_PATH = OUTPUT_DIR / "table_ix_parameter_tuning.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_ix_parameter_tuning_summary.json"

DOCUMENT_ID = "chen2020_parameterization"
DOI = "10.1149/1945-7111/ab9050"


RECORDS = [
    {
        "record_id": "chen2020_table_ix_001",
        "parameter_raw": "Positive electrode diffusion coefficient",
        "component": "positive_electrode",
        "unit": "m2.s-1",
        "experimental_value": 1.48e-15,
        "simulation_value": 4.0e-15,
        "reported_variation_percent": 170.0,
        "candidate_pybamm_parameter_name":
            "Positive particle diffusivity [m2.s-1]",
        "mapping_status": "exact_current_pybamm_name",
        "notes": "",
    },
    {
        "record_id": "chen2020_table_ix_002",
        "parameter_raw": "Negative electrode diffusion coefficient",
        "component": "negative_electrode",
        "unit": "m2.s-1",
        "experimental_value": 1.74e-15,
        "simulation_value": 3.3e-14,
        "reported_variation_percent": 1797.0,
        "candidate_pybamm_parameter_name":
            "Negative particle diffusivity [m2.s-1]",
        "mapping_status": "exact_current_pybamm_name",
        "notes": "",
    },
    {
        "record_id": "chen2020_table_ix_003",
        "parameter_raw": "Positive electrode maximum concentration",
        "component": "positive_electrode",
        "unit": "mol.m-3",
        "experimental_value": 51765.0,
        "simulation_value": 63104.0,
        "reported_variation_percent": 22.0,
        "candidate_pybamm_parameter_name":
            "Maximum concentration in positive electrode [mol.m-3]",
        "mapping_status": "exact_current_pybamm_name",
        "notes": "",
    },
    {
        "record_id": "chen2020_table_ix_004",
        "parameter_raw": "Negative electrode maximum concentration",
        "component": "negative_electrode",
        "unit": "mol.m-3",
        "experimental_value": 29583.0,
        "simulation_value": 33133.0,
        "reported_variation_percent": 12.0,
        "candidate_pybamm_parameter_name":
            "Maximum concentration in negative electrode [mol.m-3]",
        "mapping_status": "exact_current_pybamm_name",
        "notes": "",
    },
    {
        "record_id": "chen2020_table_ix_005",
        "parameter_raw": "Positive electrode 100% SOC stoichiometry",
        "component": "positive_electrode",
        "unit": "dimensionless",
        "experimental_value": 0.2661,
        "simulation_value": 0.27,
        "reported_variation_percent": 1.47,
        "candidate_pybamm_parameter_name": "",
        "mapping_status": "requires_initial_condition_conversion",
        "notes":
            "Stoichiometry is not represented as a direct scalar "
            "parameter in the current registry.",
    },
    {
        "record_id": "chen2020_table_ix_006",
        "parameter_raw": "Bruggeman constant",
        "component": "positive_electrode",
        "unit": "dimensionless",
        "experimental_value": 2.43,
        "simulation_value": 1.5,
        "reported_variation_percent": 38.0,
        "candidate_pybamm_parameter_name":
            "Positive electrode Bruggeman coefficient (electrolyte)",
        "mapping_status": "candidate_current_pybamm_name",
        "notes":
            "The paper reports one constant per porous region.",
    },
    {
        "record_id": "chen2020_table_ix_007",
        "parameter_raw": "Bruggeman constant",
        "component": "separator",
        "unit": "dimensionless",
        "experimental_value": 2.57,
        "simulation_value": 1.5,
        "reported_variation_percent": 42.0,
        "candidate_pybamm_parameter_name":
            "Separator Bruggeman coefficient (electrolyte)",
        "mapping_status": "candidate_current_pybamm_name",
        "notes":
            "The paper reports one constant per porous region.",
    },
    {
        "record_id": "chen2020_table_ix_008",
        "parameter_raw": "Bruggeman constant",
        "component": "negative_electrode",
        "unit": "dimensionless",
        "experimental_value": 2.91,
        "simulation_value": 1.5,
        "reported_variation_percent": 48.0,
        "candidate_pybamm_parameter_name":
            "Negative electrode Bruggeman coefficient (electrolyte)",
        "mapping_status": "candidate_current_pybamm_name",
        "notes":
            "The paper reports one constant per porous region.",
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(RECORDS)

    dataframe.insert(1, "document_id", DOCUMENT_ID)
    dataframe.insert(2, "doi", DOI)
    dataframe.insert(3, "table_id", "Table IX")
    dataframe.insert(4, "pdf_page", 20)
    dataframe.insert(5, "verification_status", "visually_verified")

    calculated = (
        (
            dataframe["simulation_value"]
            - dataframe["experimental_value"]
        )
        .abs()
        .div(dataframe["experimental_value"])
        .mul(100)
    )

    dataframe["calculated_absolute_variation_percent"] = calculated.round(4)
    dataframe["variation_difference_percent"] = (
        calculated - dataframe["reported_variation_percent"]
    ).abs().round(4)

    if dataframe["record_id"].duplicated().any():
        raise ValueError("Duplicate record IDs detected.")

    if dataframe[
        ["experimental_value", "simulation_value"]
    ].isna().any().any():
        raise ValueError("Missing numeric values detected.")

    if dataframe["variation_difference_percent"].max() > 1.0:
        raise ValueError(
            "A calculated variation differs by more than one percentage point "
            "from the value reported in Table IX."
        )

    dataframe.to_csv(CSV_PATH, index=False)

    summary = {
        "document_id": DOCUMENT_ID,
        "doi": DOI,
        "table_id": "Table IX",
        "pdf_page": 20,
        "record_count": int(len(dataframe)),
        "components": sorted(dataframe["component"].unique().tolist()),
        "mapping_status_counts": {
            str(key): int(value)
            for key, value in dataframe["mapping_status"]
            .value_counts()
            .items()
        },
        "maximum_variation_difference_percent": float(
            dataframe["variation_difference_percent"].max()
        ),
        "source_verification": "visually_verified",
        "csv_path": str(CSV_PATH.relative_to(PROJECT_ROOT)),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Records: {len(dataframe)}")
    print(f"CSV: {CSV_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    print()
    print(
        dataframe[
            [
                "component",
                "parameter_raw",
                "experimental_value",
                "simulation_value",
                "reported_variation_percent",
                "variation_difference_percent",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

