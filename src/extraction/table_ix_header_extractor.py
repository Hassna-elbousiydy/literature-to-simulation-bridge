from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import median

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

CSV_PATH = OUTPUT_DIR / "table_ix_extracted_rows.csv"
SUMMARY_PATH = OUTPUT_DIR / "table_ix_extraction_summary.json"

PDF_PAGE = 20
PAGE_INDEX = PDF_PAGE - 1

HEADER_NAMES = [
    "Units",
    "Experiments",
    "Simulations",
    "Variation (%)",
]


def normalize_text(text: str) -> str:
    replacements = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\u2212": "-",
        "\u00a0": " ",
        "\u00ad": "",
        "\u2219": "\u00b7",
    }

    for old, new in replacements.items():
        if old:
            text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def centre_x(word: dict) -> float:
    return (word["x0"] + word["x1"]) / 2


def centre_y(word: dict) -> float:
    return (word["y0"] + word["y1"]) / 2


def join_words(words: list[dict]) -> str:
    ordered = sorted(
        words,
        key=lambda word: (
            word["block_no"],
            word["line_no"],
            word["word_no"],
            word["source_order"],
        ),
    )

    return normalize_text(
        " ".join(word["text"] for word in ordered)
    )


def find_single_rectangle(
    page: pymupdf.Page,
    text: str,
    *,
    minimum_y: float | None = None,
) -> pymupdf.Rect:
    rectangles = page.search_for(text)

    if minimum_y is not None:
        rectangles = [
            rectangle
            for rectangle in rectangles
            if float(rectangle.y0) > minimum_y
        ]

    if len(rectangles) != 1:
        coordinates = [
            [
                round(float(rectangle.x0), 2),
                round(float(rectangle.y0), 2),
                round(float(rectangle.x1), 2),
                round(float(rectangle.y1), 2),
            ]
            for rectangle in rectangles
        ]

        raise RuntimeError(
            f"Expected one rectangle for {text!r} "
            f"below y={minimum_y}, "
            f"obtained {len(rectangles)}: {coordinates}"
        )

    return rectangles[0]


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)

    document = pymupdf.open(PDF_PATH)
    page = document[PAGE_INDEX]

    page_rotation = int(page.rotation)
    page_width = float(page.rect.width)
    page_height = float(page.rect.height)

    caption_rectangle = find_single_rectangle(
        page,
        "Table IX",
    )

    header_rectangles = {
        header: find_single_rectangle(
            page,
            header,
            minimum_y=float(caption_rectangle.y1),
        )
        for header in HEADER_NAMES
    }

    header_centres = {
        header: (
            float(rectangle.x0)
            + float(rectangle.x1)
        ) / 2
        for header, rectangle
        in header_rectangles.items()
    }

    ordered_header_centres = [
        header_centres[header]
        for header in HEADER_NAMES
    ]

    header_gaps = [
        second - first
        for first, second in zip(
            ordered_header_centres,
            ordered_header_centres[1:],
        )
    ]

    typical_gap = float(median(header_gaps))

    inferred_parameter_centre = (
        ordered_header_centres[0] - typical_gap
    )

    column_centres = [
        inferred_parameter_centre,
        *ordered_header_centres,
    ]

    column_names = [
        "parameter_raw",
        "unit_raw",
        "experiment_raw",
        "simulation_raw",
        "variation_raw",
    ]

    column_boundaries = [
        (
            column_centres[index]
            + column_centres[index + 1]
        ) / 2
        for index in range(len(column_centres) - 1)
    ]

    column_ranges = {
        "parameter_raw": (
            float(caption_rectangle.x0),
            column_boundaries[0],
        ),
        "unit_raw": (
            column_boundaries[0],
            column_boundaries[1],
        ),
        "experiment_raw": (
            column_boundaries[1],
            column_boundaries[2],
        ),
        "simulation_raw": (
            column_boundaries[2],
            column_boundaries[3],
        ),
        "variation_raw": (
            column_boundaries[3],
            page_width,
        ),
    }

    data_y_min = max(
        float(rectangle.y1)
        for rectangle in header_rectangles.values()
    ) + 3

    data_y_max = page_height - 20

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

    parameter_x_min, parameter_x_max = (
        column_ranges["parameter_raw"]
    )

    parameter_words = [
        word
        for word in words
        if data_y_min <= centre_y(word) <= data_y_max
        and parameter_x_min
        <= centre_x(word)
        < parameter_x_max
    ]

    parameter_lines: dict[
        tuple[int, int],
        list[dict],
    ] = {}

    for word in parameter_words:
        key = (
            word["block_no"],
            word["line_no"],
        )

        parameter_lines.setdefault(key, []).append(word)

    row_definitions = []

    for line_words in parameter_lines.values():
        parameter_text = join_words(line_words)

        if not parameter_text:
            continue

        row_definitions.append(
            {
                "row_coordinate_y": sum(
                    centre_y(word)
                    for word in line_words
                ) / len(line_words),
                "parameter_raw": parameter_text,
            }
        )

    row_definitions.sort(
        key=lambda row: row["row_coordinate_y"]
    )

    if len(row_definitions) != 6:
        print("Detected parameter rows:")

        for row in row_definitions:
            print(
                round(row["row_coordinate_y"], 2),
                row["parameter_raw"],
            )

        document.close()

        raise ValueError(
            "Expected six Table IX parameter rows, "
            f"obtained {len(row_definitions)}."
        )

    row_centres = [
        row["row_coordinate_y"]
        for row in row_definitions
    ]

    extracted_rows = []

    for row_index, row_definition in enumerate(
        row_definitions
    ):
        extracted_row = {
            "extraction_id":
                f"chen2020_table_ix_auto_{row_index + 1:03d}",
            "document_id": "chen2020_parameterization",
            "doi": "10.1149/1945-7111/ab9050",
            "table_id": "Table IX",
            "pdf_page": PDF_PAGE,
            "row_number": row_index + 1,
            "row_coordinate_y": round(
                row_definition["row_coordinate_y"],
                4,
            ),
        }

        for column_name in column_names:
            x_min, x_max = column_ranges[column_name]

            cell_words = []

            for word in words:
                x_position = centre_x(word)
                y_position = centre_y(word)

                if not (
                    x_min <= x_position < x_max
                    and data_y_min
                    <= y_position
                    <= data_y_max
                ):
                    continue

                nearest_row_index = min(
                    range(len(row_centres)),
                    key=lambda index: abs(
                        row_centres[index] - y_position
                    ),
                )

                if nearest_row_index != row_index:
                    continue

                if abs(
                    row_centres[nearest_row_index]
                    - y_position
                ) <= 6:
                    cell_words.append(word)

            extracted_row[column_name] = join_words(
                cell_words
            )

        extracted_rows.append(extracted_row)

    document.close()

    dataframe = pd.DataFrame(extracted_rows)

    if dataframe["parameter_raw"].eq("").any():
        raise ValueError("Empty parameter names detected.")

    if dataframe["extraction_id"].duplicated().any():
        raise ValueError("Duplicate extraction IDs detected.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(CSV_PATH, index=False)

    summary = {
        "document_id": "chen2020_parameterization",
        "doi": "10.1149/1945-7111/ab9050",
        "table_id": "Table IX",
        "pdf_page": PDF_PAGE,
        "page_rotation_degrees": page_rotation,
        "caption_y": round(
            float(caption_rectangle.y0),
            4,
        ),
        "data_y_min": round(data_y_min, 4),
        "data_y_max": round(data_y_max, 4),
        "header_centres": {
            key: round(value, 4)
            for key, value in header_centres.items()
        },
        "inferred_parameter_centre": round(
            inferred_parameter_centre,
            4,
        ),
        "column_boundaries": [
            round(boundary, 4)
            for boundary in column_boundaries
        ],
        "extracted_row_count": int(len(dataframe)),
        "non_empty_cell_counts": {
            column: int(dataframe[column].ne("").sum())
            for column in column_names
        },
        "extraction_method":
            "header_anchored_coordinate_extraction",
        "csv_path": str(CSV_PATH.relative_to(PROJECT_ROOT)),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== TABLE IX HEADER-ANCHORED EXTRACTION ===")
    print("Extracted rows:", len(dataframe))
    print(
        "Column boundaries:",
        summary["column_boundaries"],
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
                "experiment_raw",
                "simulation_raw",
                "variation_raw",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()

