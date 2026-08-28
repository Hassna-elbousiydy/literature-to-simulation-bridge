from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pybamm


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OVERRIDES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
    / "pybamm_overrides_from_table_ix.json"
)

OVERRIDES_SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
    / "pybamm_overrides_from_table_ix_summary.json"
)

REFERENCE_PATH = (
    PROJECT_ROOT
    / "results"
    / "data"
    / "chen2020_spm_1c_discharge.csv"
)

RESULTS_DATA_DIR = PROJECT_ROOT / "results" / "data"
RESULTS_FIGURE_DIR = PROJECT_ROOT / "results" / "figures"
RESULTS_EVALUATION_DIR = PROJECT_ROOT / "results" / "evaluation"

OUTPUT_CSV_PATH = (
    RESULTS_DATA_DIR
    / "literature_extracted_spm_1c_discharge.csv"
)

OUTPUT_SUMMARY_PATH = (
    RESULTS_DATA_DIR
    / "literature_extracted_spm_1c_summary.json"
)

COMPARISON_PATH = (
    RESULTS_EVALUATION_DIR
    / "literature_to_simulation_comparison.json"
)

FIGURE_PATH = (
    RESULTS_FIGURE_DIR
    / "literature_to_simulation_voltage_comparison.png"
)


def solution_array(
    solution: pybamm.Solution,
    variable_name: str,
) -> np.ndarray:
    return np.asarray(
        solution[variable_name].entries,
        dtype=float,
    ).reshape(-1)


def main() -> None:
    required_files = [
        OVERRIDES_PATH,
        OVERRIDES_SUMMARY_PATH,
        REFERENCE_PATH,
    ]

    for required_file in required_files:
        if not required_file.exists():
            raise FileNotFoundError(required_file)

    overrides = json.loads(
        OVERRIDES_PATH.read_text(encoding="utf-8")
    )

    overrides_summary = json.loads(
        OVERRIDES_SUMMARY_PATH.read_text(
            encoding="utf-8"
        )
    )

    if not overrides_summary.get("validation_passed"):
        raise RuntimeError(
            "The literature-derived overrides "
            "have not been validated."
        )

    if len(overrides) != 7:
        raise ValueError(
            f"Expected seven overrides, "
            f"obtained {len(overrides)}."
        )

    parameter_values = pybamm.ParameterValues(
        "Chen2020"
    )

    parameter_values.update(
        overrides,
    )

    model = pybamm.lithium_ion.SPM()

    experiment = pybamm.Experiment(
        [
            "Discharge at 1C until 2.5 V",
        ],
        period="30 seconds",
    )

    simulation = pybamm.Simulation(
        model,
        parameter_values=parameter_values,
        experiment=experiment,
    )

    solution = simulation.solve(initial_soc=1.0)

    time_seconds = solution_array(
        solution,
        "Time [s]",
    )

    voltage = solution_array(
        solution,
        "Terminal voltage [V]",
    )

    current = solution_array(
        solution,
        "Current [A]",
    )

    discharge_capacity = solution_array(
        solution,
        "Discharge capacity [A.h]",
    )

    output_data = pd.DataFrame(
        {
            "time_seconds": time_seconds,
            "time_hours": time_seconds / 3600,
            "voltage_v": voltage,
            "current_a": current,
            "discharge_capacity_ah":
                discharge_capacity,
        }
    )

    if output_data.isna().any().any():
        raise ValueError(
            "Missing simulation output values detected."
        )

    if not output_data[
        "time_seconds"
    ].diff().dropna().gt(0).all():
        raise ValueError(
            "Simulation time is not strictly increasing."
        )

    reference = pd.read_csv(REFERENCE_PATH)

    required_reference_columns = {
        "time_seconds",
        "voltage_v",
        "discharge_capacity_ah",
    }

    missing_reference_columns = (
        required_reference_columns
        - set(reference.columns)
    )

    if missing_reference_columns:
        raise ValueError(
            "Missing reference columns: "
            f"{sorted(missing_reference_columns)}"
        )

    reference_time = reference[
        "time_seconds"
    ].to_numpy(dtype=float)

    reference_voltage = reference[
        "voltage_v"
    ].to_numpy(dtype=float)

    reference_capacity = reference[
        "discharge_capacity_ah"
    ].to_numpy(dtype=float)

    interpolated_voltage = np.interp(
        reference_time,
        time_seconds,
        voltage,
    )

    interpolated_capacity = np.interp(
        reference_time,
        time_seconds,
        discharge_capacity,
    )

    voltage_errors = (
        interpolated_voltage - reference_voltage
    )

    voltage_rmse = float(
        np.sqrt(np.mean(voltage_errors ** 2))
    )

    maximum_absolute_voltage_error = float(
        np.max(np.abs(voltage_errors))
    )

    final_capacity_difference = float(
        abs(
            interpolated_capacity[-1]
            - reference_capacity[-1]
        )
    )

    duration_difference_seconds = float(
        abs(
            time_seconds[-1]
            - reference_time[-1]
        )
    )

    same_point_count = (
        len(output_data) == len(reference)
    )

    same_time_grid = (
        same_point_count
        and np.allclose(
            time_seconds,
            reference_time,
            rtol=1e-12,
            atol=1e-9,
        )
    )

    validation_thresholds = {
        "maximum_voltage_rmse_v": 1e-8,
        "maximum_absolute_voltage_error_v": 1e-7,
        "maximum_final_capacity_difference_ah": 1e-8,
        "maximum_duration_difference_seconds": 1e-6,
    }

    validation_passed = (
        voltage_rmse
        <= validation_thresholds[
            "maximum_voltage_rmse_v"
        ]
        and maximum_absolute_voltage_error
        <= validation_thresholds[
            "maximum_absolute_voltage_error_v"
        ]
        and final_capacity_difference
        <= validation_thresholds[
            "maximum_final_capacity_difference_ah"
        ]
        and duration_difference_seconds
        <= validation_thresholds[
            "maximum_duration_difference_seconds"
        ]
    )

    RESULTS_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_EVALUATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_data.to_csv(
        OUTPUT_CSV_PATH,
        index=False,
    )

    simulation_summary = {
        "pybamm_version": pybamm.__version__,
        "model": model.name,
        "parameter_base": "Chen2020",
        "parameter_source": (
            "Automatically extracted from "
            "Chen2020 Table IX"
        ),
        "override_count": len(overrides),
        "protocol": "Discharge at 1C until 2.5 V",
        "number_of_points": int(
            len(output_data)
        ),
        "duration_hours": float(
            time_seconds[-1] / 3600
        ),
        "initial_voltage_v": float(
            voltage[0]
        ),
        "final_voltage_v": float(
            voltage[-1]
        ),
        "final_discharge_capacity_ah": float(
            discharge_capacity[-1]
        ),
        "termination": str(
            solution.termination
        ),
        "overrides_file": str(
            OVERRIDES_PATH.relative_to(
                PROJECT_ROOT
            )
        ),
    }

    OUTPUT_SUMMARY_PATH.write_text(
        json.dumps(
            simulation_summary,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    comparison = {
        "reference_file": str(
            REFERENCE_PATH.relative_to(
                PROJECT_ROOT
            )
        ),
        "literature_simulation_file": str(
            OUTPUT_CSV_PATH.relative_to(
                PROJECT_ROOT
            )
        ),
        "reference_point_count": int(
            len(reference)
        ),
        "literature_simulation_point_count": int(
            len(output_data)
        ),
        "same_point_count": bool(
            same_point_count
        ),
        "same_time_grid": bool(
            same_time_grid
        ),
        "voltage_rmse_v": voltage_rmse,
        "maximum_absolute_voltage_error_v":
            maximum_absolute_voltage_error,
        "final_capacity_difference_ah":
            final_capacity_difference,
        "duration_difference_seconds":
            duration_difference_seconds,
        "thresholds": validation_thresholds,
        "validation_passed":
            validation_passed,
    }

    COMPARISON_PATH.write_text(
        json.dumps(
            comparison,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    plt.figure(figsize=(10, 6))

    plt.plot(
        reference_time / 3600,
        reference_voltage,
        linewidth=3,
        label="Reference Chen2020",
    )

    plt.plot(
        time_seconds / 3600,
        voltage,
        linestyle="--",
        linewidth=2,
        label="Parameters extracted from Table IX",
    )

    plt.xlabel("Time [h]")
    plt.ylabel("Terminal voltage [V]")
    plt.title(
        "Literature-to-Simulation Validation"
    )
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        FIGURE_PATH,
        dpi=180,
    )
    plt.close()

    print(
        "=== LITERATURE TO SIMULATION ==="
    )
    print("PyBaMM:", pybamm.__version__)
    print("Model:", model.name)
    print("Overrides loaded:", len(overrides))
    print(
        "Simulation points:",
        len(output_data),
    )
    print(
        f"Voltage RMSE: "
        f"{voltage_rmse:.12g} V"
    )
    print(
        "Maximum voltage error:",
        f"{maximum_absolute_voltage_error:.12g} V",
    )
    print(
        "Final capacity difference:",
        f"{final_capacity_difference:.12g} Ah",
    )
    print(
        "Duration difference:",
        f"{duration_difference_seconds:.12g} s",
    )
    print(
        "Same time grid:",
        same_time_grid,
    )
    print(
        "Validation passed:",
        validation_passed,
    )
    print(f"CSV: {OUTPUT_CSV_PATH}")
    print(f"Summary: {OUTPUT_SUMMARY_PATH}")
    print(f"Comparison: {COMPARISON_PATH}")
    print(f"Figure: {FIGURE_PATH}")

    if not validation_passed:
        raise RuntimeError(
            "Literature-derived simulation differs "
            "from the Chen2020 reference."
        )


if __name__ == "__main__":
    main()
