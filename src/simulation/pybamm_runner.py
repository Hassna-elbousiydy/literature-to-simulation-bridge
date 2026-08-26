"""Run the reference Chen2020 discharge simulation with PyBaMM."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pybamm


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "results" / "data"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

CSV_PATH = DATA_DIR / "chen2020_spm_1c_discharge.csv"
JSON_PATH = DATA_DIR / "chen2020_spm_1c_summary.json"
FIGURE_PATH = FIGURES_DIR / "chen2020_spm_1c_voltage.png"


def run_reference_simulation() -> None:
    """Run and save a reproducible Chen2020 SPM discharge simulation."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"PyBaMM version: {pybamm.__version__}")
    print("Model: Single Particle Model (SPM)")
    print("Parameter set: Chen2020")
    print("Protocol: Discharge at 1C until 2.5 V")

    model = pybamm.lithium_ion.SPM()
    parameter_values = pybamm.ParameterValues("Chen2020")

    experiment = pybamm.Experiment(
        ["Discharge at 1C until 2.5 V"],
        period="30 seconds",
    )

    simulation = pybamm.Simulation(
        model=model,
        parameter_values=parameter_values,
        experiment=experiment,
    )

    solution = simulation.solve(initial_soc=1.0)

    time_seconds = np.asarray(solution.t, dtype=float).reshape(-1)
    voltage = np.asarray(
        solution["Voltage [V]"].entries,
        dtype=float,
    ).reshape(-1)
    current = np.asarray(
        solution["Current [A]"].entries,
        dtype=float,
    ).reshape(-1)
    discharge_capacity = np.asarray(
        solution["Discharge capacity [A.h]"].entries,
        dtype=float,
    ).reshape(-1)

    results = pd.DataFrame(
        {
            "time_seconds": time_seconds,
            "time_hours": time_seconds / 3600,
            "voltage_v": voltage,
            "current_a": current,
            "discharge_capacity_ah": discharge_capacity,
        }
    )

    results.to_csv(CSV_PATH, index=False)

    summary = {
        "pybamm_version": pybamm.__version__,
        "model": "Single Particle Model (SPM)",
        "parameter_set": "Chen2020",
        "protocol": "Discharge at 1C until 2.5 V",
        "number_of_points": int(len(results)),
        "duration_hours": float(results["time_hours"].iloc[-1]),
        "initial_voltage_v": float(results["voltage_v"].iloc[0]),
        "final_voltage_v": float(results["voltage_v"].iloc[-1]),
        "final_discharge_capacity_ah": float(
            results["discharge_capacity_ah"].iloc[-1]
        ),
        "termination": str(solution.termination),
    }

    with JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(
        results["time_hours"],
        results["voltage_v"],
        color="#1f77b4",
        linewidth=2,
    )

    ax.set_title("Chen2020 SPM - 1C Discharge")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Terminal voltage [V]")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("\nSimulation completed successfully.")
    print(f"Number of points: {summary['number_of_points']}")
    print(f"Duration: {summary['duration_hours']:.4f} h")
    print(f"Initial voltage: {summary['initial_voltage_v']:.4f} V")
    print(f"Final voltage: {summary['final_voltage_v']:.4f} V")
    print(
        "Final discharge capacity: "
        f"{summary['final_discharge_capacity_ah']:.4f} Ah"
    )
    print(f"Termination: {summary['termination']}")
    print(f"\nCSV: {CSV_PATH}")
    print(f"Summary: {JSON_PATH}")
    print(f"Figure: {FIGURE_PATH}")


if __name__ == "__main__":
    run_reference_simulation()
