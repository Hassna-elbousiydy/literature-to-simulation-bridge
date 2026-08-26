from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "ground_truth" / "chen2020"

CSV_PATH = OUTPUT_DIR / "table_vii_numeric_parameters.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_vii_numeric_parameters_summary.json"

DOCUMENT_ID = "chen2020_parameterization"
DOI = "10.1149/1945-7111/ab9050"

records: list[dict] = []


def add_record(
    *,
    category: str,
    parameter_raw: str,
    symbol: str,
    component: str,
    raw_value: str,
    raw_unit: str,
    normalized_value: float,
    normalized_unit: str,
    value_role: str,
    candidate_pybamm_parameter_name: str = "",
    mapping_status: str,
    expected_pybamm_relation: str,
    notes: str = "",
) -> None:
    record_number = len(records) + 1

    records.append(
        {
            "record_id": f"chen2020_table_vii_{record_number:03d}",
            "document_id": DOCUMENT_ID,
            "doi": DOI,
            "table_id": "Table VII",
            "pdf_page": 19,
            "category": category,
            "parameter_raw": parameter_raw,
            "symbol": symbol,
            "component": component,
            "raw_value": raw_value,
            "raw_unit": raw_unit,
            "normalized_value": normalized_value,
            "normalized_unit": normalized_unit,
            "value_role": value_role,
            "candidate_pybamm_parameter_name":
                candidate_pybamm_parameter_name,
            "mapping_status": mapping_status,
            "expected_pybamm_relation": expected_pybamm_relation,
            "verification_status": "visually_verified",
            "notes": notes,
        }
    )


# ------------------------------------------------------------------
# Design specifications
# ------------------------------------------------------------------

add_record(
    category="design_specifications",
    parameter_raw="Current collector thickness",
    symbol="",
    component="positive_current_collector",
    raw_value="16e-6",
    raw_unit="m",
    normalized_value=16e-6,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name=(
        "Positive current collector thickness [m]"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Current collector thickness",
    symbol="",
    component="negative_current_collector",
    raw_value="12e-6",
    raw_unit="m",
    normalized_value=12e-6,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name=(
        "Negative current collector thickness [m]"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrode thickness",
    symbol="L_p",
    component="positive_electrode",
    raw_value="75.6e-6",
    raw_unit="m",
    normalized_value=75.6e-6,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name="Positive electrode thickness [m]",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrode thickness",
    symbol="L_s",
    component="separator",
    raw_value="12e-6",
    raw_unit="m",
    normalized_value=12e-6,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name="Separator thickness [m]",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrode thickness",
    symbol="L_n",
    component="negative_electrode",
    raw_value="85.2e-6",
    raw_unit="m",
    normalized_value=85.2e-6,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name="Negative electrode thickness [m]",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrode length",
    symbol="",
    component="cell",
    raw_value="1.58",
    raw_unit="m",
    normalized_value=1.58,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name="Electrode width [m]",
    mapping_status="candidate_geometry_mapping",
    expected_pybamm_relation="geometry_name_translation",
    notes=(
        "The paper calls this dimension electrode length, while the "
        "Chen2020 PyBaMM registry stores the value 1.58 as electrode width."
    ),
)

add_record(
    category="design_specifications",
    parameter_raw="Electrode width",
    symbol="",
    component="cell",
    raw_value="6.5e-2",
    raw_unit="m",
    normalized_value=6.5e-2,
    normalized_unit="m",
    value_role="design_specification",
    candidate_pybamm_parameter_name="Electrode height [m]",
    mapping_status="candidate_geometry_mapping",
    expected_pybamm_relation="geometry_name_translation",
    notes=(
        "The paper calls this dimension electrode width, while the "
        "Chen2020 PyBaMM registry stores the value 0.065 as electrode height."
    ),
)

add_record(
    category="design_specifications",
    parameter_raw="Mean particle radius",
    symbol="R_p",
    component="positive_electrode",
    raw_value="5.22e-6",
    raw_unit="m",
    normalized_value=5.22e-6,
    normalized_unit="m",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Positive particle radius [m]",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Mean particle radius",
    symbol="R_n",
    component="negative_electrode",
    raw_value="5.86e-6",
    raw_unit="m",
    normalized_value=5.86e-6,
    normalized_unit="m",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Negative particle radius [m]",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrolyte volume fraction",
    symbol="epsilon_p",
    component="positive_electrode",
    raw_value="33.5",
    raw_unit="%",
    normalized_value=0.335,
    normalized_unit="fraction",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Positive electrode porosity",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrolyte volume fraction",
    symbol="epsilon_s",
    component="separator",
    raw_value="47",
    raw_unit="%",
    normalized_value=0.47,
    normalized_unit="fraction",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Separator porosity",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Electrolyte volume fraction",
    symbol="epsilon_n",
    component="negative_electrode",
    raw_value="25",
    raw_unit="%",
    normalized_value=0.25,
    normalized_unit="fraction",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Negative electrode porosity",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Active material volume fraction",
    symbol="epsilon_act_p",
    component="positive_electrode",
    raw_value="66.5",
    raw_unit="%",
    normalized_value=0.665,
    normalized_unit="fraction",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Positive electrode active material volume fraction"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Active material volume fraction",
    symbol="epsilon_act_n",
    component="negative_electrode",
    raw_value="75",
    raw_unit="%",
    normalized_value=0.75,
    normalized_unit="fraction",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Negative electrode active material volume fraction"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="design_specifications",
    parameter_raw="Bruggeman exponent",
    symbol="b_p",
    component="positive_electrode",
    raw_value="2.43",
    raw_unit="dimensionless",
    normalized_value=2.43,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Positive electrode Bruggeman coefficient (electrolyte)"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="design_specifications",
    parameter_raw="Bruggeman exponent",
    symbol="b_s",
    component="separator",
    raw_value="2.57",
    raw_unit="dimensionless",
    normalized_value=2.57,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Separator Bruggeman coefficient (electrolyte)"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="design_specifications",
    parameter_raw="Bruggeman exponent",
    symbol="b_n",
    component="negative_electrode",
    raw_value="2.91",
    raw_unit="dimensionless",
    normalized_value=2.91,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Negative electrode Bruggeman coefficient (electrolyte)"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

# ------------------------------------------------------------------
# Electrode parameters
# ------------------------------------------------------------------

add_record(
    category="electrode",
    parameter_raw="Solid phase lithium diffusivity",
    symbol="D_s_p",
    component="positive_electrode",
    raw_value="1.48e-15",
    raw_unit="m2.s-1",
    normalized_value=1.48e-15,
    normalized_unit="m2.s-1",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Positive particle diffusivity [m2.s-1]"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="electrode",
    parameter_raw="Solid phase lithium diffusivity",
    symbol="D_s_n",
    component="negative_electrode",
    raw_value="1.74e-15",
    raw_unit="m2.s-1",
    normalized_value=1.74e-15,
    normalized_unit="m2.s-1",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Negative particle diffusivity [m2.s-1]"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="electrode",
    parameter_raw="Solid phase electronic conductivity",
    symbol="sigma_s_p",
    component="positive_electrode",
    raw_value="0.18",
    raw_unit="S.m-1",
    normalized_value=0.18,
    normalized_unit="S.m-1",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Positive electrode conductivity [S.m-1]"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="electrode",
    parameter_raw="Solid phase electronic conductivity",
    symbol="sigma_s_n",
    component="negative_electrode",
    raw_value="215",
    raw_unit="S.m-1",
    normalized_value=215.0,
    normalized_unit="S.m-1",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Negative electrode conductivity [S.m-1]"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="electrode",
    parameter_raw="Maximum concentration",
    symbol="c_s_p_max",
    component="positive_electrode",
    raw_value="51765",
    raw_unit="mol.m-3",
    normalized_value=51765.0,
    normalized_unit="mol.m-3",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Maximum concentration in positive electrode [mol.m-3]"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="electrode",
    parameter_raw="Maximum concentration",
    symbol="c_s_n_max",
    component="negative_electrode",
    raw_value="29583",
    raw_unit="mol.m-3",
    normalized_value=29583.0,
    normalized_unit="mol.m-3",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name=(
        "Maximum concentration in negative electrode [mol.m-3]"
    ),
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="expected_difference_table_ix_tuning",
)

add_record(
    category="electrode",
    parameter_raw="Stoichiometry at 0% SOC",
    symbol="",
    component="positive_electrode",
    raw_value="0.9084",
    raw_unit="dimensionless",
    normalized_value=0.9084,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    mapping_status="requires_conversion",
    expected_pybamm_relation="not_directly_comparable",
)

add_record(
    category="electrode",
    parameter_raw="Stoichiometry at 0% SOC",
    symbol="",
    component="negative_electrode",
    raw_value="0.0279",
    raw_unit="dimensionless",
    normalized_value=0.0279,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    mapping_status="requires_conversion",
    expected_pybamm_relation="not_directly_comparable",
)

add_record(
    category="electrode",
    parameter_raw="Stoichiometry at 100% SOC",
    symbol="",
    component="positive_electrode",
    raw_value="0.2661",
    raw_unit="dimensionless",
    normalized_value=0.2661,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    mapping_status="tuned_in_table_ix",
    expected_pybamm_relation="not_directly_comparable",
)

add_record(
    category="electrode",
    parameter_raw="Stoichiometry at 100% SOC",
    symbol="",
    component="negative_electrode",
    raw_value="0.9014",
    raw_unit="dimensionless",
    normalized_value=0.9014,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    mapping_status="requires_conversion",
    expected_pybamm_relation="not_directly_comparable",
)

# ------------------------------------------------------------------
# Electrolyte parameters
# ------------------------------------------------------------------

add_record(
    category="electrolyte",
    parameter_raw="Transference number",
    symbol="t_plus",
    component="electrolyte",
    raw_value="0.2594",
    raw_unit="dimensionless",
    normalized_value=0.2594,
    normalized_unit="dimensionless",
    value_role="experimentally_determined",
    candidate_pybamm_parameter_name="Cation transference number",
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

add_record(
    category="electrolyte",
    parameter_raw="Initial electrolyte concentration",
    symbol="c_e_0",
    component="electrolyte",
    raw_value="1000",
    raw_unit="mol.m-3",
    normalized_value=1000.0,
    normalized_unit="mol.m-3",
    value_role="design_specification",
    candidate_pybamm_parameter_name=(
        "Initial concentration in electrolyte [mol.m-3]"
    ),
    mapping_status="exact_name_candidate",
    expected_pybamm_relation="expected_exact_match",
)

# ------------------------------------------------------------------
# Reaction parameters
# ------------------------------------------------------------------

add_record(
    category="reaction",
    parameter_raw="Activation energy",
    symbol="",
    component="positive_electrode",
    raw_value="17.8e3",
    raw_unit="J.mol-1",
    normalized_value=17.8e3,
    normalized_unit="J.mol-1",
    value_role="experimentally_determined",
    mapping_status="embedded_in_function",
    expected_pybamm_relation="not_directly_comparable",
    notes="Used inside a temperature-dependent kinetic expression.",
)

add_record(
    category="reaction",
    parameter_raw="Activation energy",
    symbol="",
    component="negative_electrode",
    raw_value="35.0e3",
    raw_unit="J.mol-1",
    normalized_value=35.0e3,
    normalized_unit="J.mol-1",
    value_role="experimentally_determined",
    mapping_status="embedded_in_function",
    expected_pybamm_relation="not_directly_comparable",
    notes="Used inside a temperature-dependent kinetic expression.",
)

add_record(
    category="reaction",
    parameter_raw="Reaction rate",
    symbol="m_p",
    component="positive_electrode",
    raw_value="3.42e-6",
    raw_unit="A.m-2.(m3.mol-1)^1.5",
    normalized_value=3.42e-6,
    normalized_unit="A.m-2.(m3.mol-1)^1.5",
    value_role="experimentally_determined",
    mapping_status="embedded_in_function",
    expected_pybamm_relation="not_directly_comparable",
    notes="Used inside the positive exchange-current density function.",
)

add_record(
    category="reaction",
    parameter_raw="Reaction rate",
    symbol="m_n",
    component="negative_electrode",
    raw_value="6.48e-7",
    raw_unit="A.m-2.(m3.mol-1)^1.5",
    normalized_value=6.48e-7,
    normalized_unit="A.m-2.(m3.mol-1)^1.5",
    value_role="experimentally_determined",
    mapping_status="embedded_in_function",
    expected_pybamm_relation="not_directly_comparable",
    notes="Used inside the negative exchange-current density function.",
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(records)

    if len(dataframe) != 33:
        raise ValueError(
            f"Expected 33 numeric records, obtained {len(dataframe)}."
        )

    if dataframe["record_id"].duplicated().any():
        raise ValueError("Duplicate record IDs detected.")

    required_columns = [
        "record_id",
        "parameter_raw",
        "component",
        "raw_value",
        "raw_unit",
        "normalized_value",
        "normalized_unit",
        "mapping_status",
        "verification_status",
    ]

    if dataframe[required_columns].isna().any().any():
        raise ValueError("Missing required values detected.")

    percentage_rows = dataframe["raw_unit"] == "%"

    invalid_percentages = dataframe[
        percentage_rows
        & ~dataframe["normalized_value"].between(0, 1)
    ]

    if not invalid_percentages.empty:
        raise ValueError("Invalid normalized percentage values detected.")

    dataframe.to_csv(CSV_PATH, index=False)

    summary = {
        "document_id": DOCUMENT_ID,
        "doi": DOI,
        "table_id": "Table VII",
        "pdf_page": 19,
        "record_count": int(len(dataframe)),
        "category_counts": {
            str(key): int(value)
            for key, value in dataframe["category"].value_counts().items()
        },
        "component_counts": {
            str(key): int(value)
            for key, value in dataframe["component"].value_counts().items()
        },
        "mapping_status_counts": {
            str(key): int(value)
            for key, value in dataframe[
                "mapping_status"
            ].value_counts().items()
        },
        "expected_relation_counts": {
            str(key): int(value)
            for key, value in dataframe[
                "expected_pybamm_relation"
            ].value_counts().items()
        },
        "source_verification": "visually_verified",
        "csv_path": str(CSV_PATH.relative_to(PROJECT_ROOT)),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== CHEN2020 TABLE VII GROUND TRUTH ===")
    print(f"Records: {len(dataframe)}")
    print(f"Categories: {summary['category_counts']}")
    print(f"Mapping statuses: {summary['mapping_status_counts']}")
    print(f"CSV: {CSV_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
