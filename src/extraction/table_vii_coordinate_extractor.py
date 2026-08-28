from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "papers"
    / "chen2020_parameterization.pdf"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chen2020"
)

CSV_PATH = OUTPUT_DIR / "table_vii_extracted_rows.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_vii_extraction_summary.json"

PDF_PAGE = 19
PAGE_INDEX = PDF_PAGE - 1

# Coordinates observed on the rotated PDF page.
COLUMN_RANGES = {
    "negative_electrode_raw": (50.0, 160.0),
    "separator_raw": (165.0, 290.0),
    "positive_electrode_raw": (295.0, 400.0),
    "unit_raw": (400.0, 495.0),
    "parameter_raw": (495.0, 665.0),
}

PARAMETER_MIN_X = 155.0
PARAMETER_MAX_X = 390.0

ROW_CLUSTER_MAX_GAP = 5.5
WORD_TO_ROW_MAX_DISTANCE = 12.0


def normalize_text(text: str) -> str:
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\u2212": "-",
        "\u00a0": " ",
        "\u00ad": "",
    }

    for old, new in replacements.items():
        if old:
            text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def word_center_x(word: dict) -> float:
    return (word["x0"] + word["x1"]) / 2


def word_center_y(word: dict) -> float:
    return (word["y0"] + word["y1"]) / 2


def join_words(words: list[dict]) -> str:
    ordered = sorted(
        words,
        key=lambda item: (
            item["block_no"],
            item["line_no"],
            item["word_no"],
            item["source_order"],
        ),
    )

    return normalize_text(
        " ".join(item["text"] for item in ordered)
    )


def cluster_parameter_words(
    parameter_words: list[dict],
) -> list[list[dict]]:
    ordered = sorted(parameter_words, key=word_center_x)

    clusters: list[list[dict]] = []

    for word in ordered:
        centre = word_center_x(word)

        if not clusters:
            clusters.append([word])
            continue

        current_cluster = clusters[-1]

        current_centre = sum(
            word_center_x(item)
            for item in current_cluster
        ) / len(current_cluster)

        if centre - current_centre <= ROW_CLUSTER_MAX_GAP:
            current_cluster.append(word)
        else:
            clusters.append([word])

    return clusters


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    document = pymupdf.open(PDF_PATH)
    page = document[PAGE_INDEX]

    page_rotation = int(page.rotation)

    raw_words = page.get_text("words", sort=True)

    words = []

    for source_order, raw_word in enumerate(raw_words):
        (
            x0,
            y0,
            x1,
            y1,
            text,
            block_no,
            line_no,
            word_no,
        ) = raw_word

        words.append(
            {
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
                "text": str(text),
                "block_no": int(block_no),
                "line_no": int(line_no),
                "word_no": int(word_no),
                "source_order": source_order,
            }
        )

    document.close()

    parameter_y_min, parameter_y_max = (
        COLUMN_RANGES["parameter_raw"]
    )

    parameter_words = [
        word
        for word in words
        if parameter_y_min
        <= word_center_y(word)
        <= parameter_y_max
        and PARAMETER_MIN_X
        <= word_center_x(word)
        <= PARAMETER_MAX_X
    ]

    parameter_clusters = cluster_parameter_words(
        parameter_words
    )

    row_definitions = []

    for cluster in parameter_clusters:
        row_centre = sum(
            word_center_x(word)
            for word in cluster
        ) / len(cluster)

        parameter_text = join_words(cluster)

        if not parameter_text:
            continue

        row_definitions.append(
            {
                "row_coordinate_x": row_centre,
                "parameter_raw": parameter_text,
            }
        )

    row_definitions.sort(
        key=lambda row: row["row_coordinate_x"]
    )

    if len(row_definitions) != 21:
        print("Detected parameter rows:")
        for row in row_definitions:
            print(
                round(row["row_coordinate_x"], 2),
                row["parameter_raw"],
            )

        raise ValueError(
            "Expected 21 Table VII rows, "
            f"detected {len(row_definitions)}."
        )

    row_centres = [
        row["row_coordinate_x"]
        for row in row_definitions
    ]

    extracted_rows = []

    for row_number, row_definition in enumerate(
        row_definitions,
        start=1,
    ):
        extracted_row = {
            "extraction_id":
                f"chen2020_table_vii_auto_{row_number:03d}",
            "document_id": "chen2020_parameterization",
            "doi": "10.1149/1945-7111/ab9050",
            "table_id": "Table VII",
            "pdf_page": PDF_PAGE,
            "row_number": row_number,
            "row_coordinate_x": round(
                row_definition["row_coordinate_x"],
                4,
            ),
        }

        for column_name, (
            column_y_min,
            column_y_max,
        ) in COLUMN_RANGES.items():
            cell_words = []

            for word in words:
                y_centre = word_center_y(word)

                if not (
                    column_y_min
                    <= y_centre
                    <= column_y_max
                ):
                    continue

                x_centre = word_center_x(word)

                nearest_row_index = min(
                    range(len(row_centres)),
                    key=lambda index: abs(
                        row_centres[index] - x_centre
                    ),
                )

                if nearest_row_index != row_number - 1:
                    continue

                distance = abs(
                    row_centres[nearest_row_index] - x_centre
                )

                if distance <= WORD_TO_ROW_MAX_DISTANCE:
                    cell_words.append(word)

            extracted_row[column_name] = join_words(
                cell_words
            )

        extracted_rows.append(extracted_row)

    dataframe = pd.DataFrame(extracted_rows)

    if dataframe["extraction_id"].duplicated().any():
        raise ValueError("Duplicate extraction IDs detected.")

    if dataframe["parameter_raw"].eq("").any():
        raise ValueError("Empty parameter names detected.")

    value_columns = [
        "positive_electrode_raw",
        "separator_raw",
        "negative_electrode_raw",
    ]

    dataframe["reported_cell_count"] = (
        dataframe[value_columns]
        .ne("")
        .sum(axis=1)
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(CSV_PATH, index=False)

    summary = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "table_id": "Table VII",
        "pdf_page": PDF_PAGE,
        "page_rotation_degrees": page_rotation,
        "source_word_count": int(len(words)),
        "extracted_row_count": int(len(dataframe)),
        "rows_with_reported_cells": int(
            dataframe["reported_cell_count"].gt(0).sum()
        ),
        "non_empty_cell_counts": {
            column: int(dataframe[column].ne("").sum())
            for column in [
                "parameter_raw",
                "unit_raw",
                "positive_electrode_raw",
                "separator_raw",
                "negative_electrode_raw",
            ]
        },
        "extraction_method":
            "coordinate_based_word_clustering",
        "csv_path": str(CSV_PATH.relative_to(PROJECT_ROOT)),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== TABLE VII COORDINATE EXTRACTION ===")
    print(f"Source words: {len(words)}")
    print(f"Extracted rows: {len(dataframe)}")
    print(
        "Rows with reported cells:",
        summary["rows_with_reported_cells"],
    )
    print(
        "Non-empty cells:",
        summary["non_empty_cell_counts"],
    )
    print(f"CSV: {CSV_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    print()
    print(
        dataframe[
            [
                "row_number",
                "parameter_raw",
                "unit_raw",
                "positive_electrode_raw",
                "separator_raw",
                "negative_electrode_raw",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()


