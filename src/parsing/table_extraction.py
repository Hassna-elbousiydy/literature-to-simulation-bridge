"""Detect and extract candidate tables from the local Chen2020 PDF."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

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

OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "chen2020"
TABLES_DIR = OUTPUT_DIR / "tables"

INDEX_PATH = OUTPUT_DIR / "table_index.json"
SUMMARY_PATH = OUTPUT_DIR / "table_detection_summary.json"

DOCUMENT_ID = "chen2020"
DOI = "10.1149/1945-7111/ab9050"

TABLE_CAPTION_PATTERN = re.compile(
    r"\bTABLE\s+(?:[IVXLCDM]+|\d+)\b",
    flags=re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Collapse whitespace while preserving textual content."""

    return " ".join(text.split())


def find_caption_candidates(page: pymupdf.Page) -> list[str]:
    """Return text blocks that look like table captions."""

    candidates: list[str] = []

    for block in page.get_text("blocks", sort=True):
        if len(block) < 7:
            continue

        text = normalize_text(str(block[4]))
        block_type = block[6]

        if block_type == 0 and TABLE_CAPTION_PATTERN.search(text):
            candidates.append(text)

    return list(dict.fromkeys(candidates))


def extract_tables() -> None:
    """Detect table candidates and export their raw cells locally."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Local PDF not found: {PDF_PATH}"
        )

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    document = pymupdf.open(PDF_PATH)

    page_records: list[dict[str, Any]] = []
    total_detected_tables = 0
    total_caption_candidates = 0

    for page_index, page in enumerate(document):
        pdf_page = page_index + 1

        try:
            page_label = page.get_label() or str(pdf_page)
        except AttributeError:
            page_label = str(pdf_page)

        caption_candidates = find_caption_candidates(page)
        total_caption_candidates += len(caption_candidates)

        table_finder = page.find_tables()
        detected_tables = list(table_finder.tables)

        table_records: list[dict[str, Any]] = []

        for table_number, table in enumerate(
            detected_tables,
            start=1,
        ):
            total_detected_tables += 1

            extracted_rows = table.extract()
            csv_name = (
                f"page_{pdf_page:03d}_"
                f"table_{table_number:02d}.csv"
            )
            csv_path = TABLES_DIR / csv_name

            dataframe = pd.DataFrame(extracted_rows)
            dataframe.to_csv(
                csv_path,
                index=False,
                header=False,
                encoding="utf-8",
            )

            table_records.append(
                {
                    "table_number_on_pdf_page": table_number,
                    "row_count": int(table.row_count),
                    "column_count": int(table.col_count),
                    "bbox": [
                        round(float(coordinate), 3)
                        for coordinate in table.bbox
                    ],
                    "local_csv": (
                        f"tables/{csv_name}"
                    ),
                }
            )

        if caption_candidates or table_records:
            page_records.append(
                {
                    "document_id": DOCUMENT_ID,
                    "doi": DOI,
                    "pdf_page": pdf_page,
                    "page_label": page_label,
                    "caption_candidates": caption_candidates,
                    "detected_table_count": len(table_records),
                    "tables": table_records,
                    "manual_review_status": "not_reviewed",
                }
            )

    document.close()

    with INDEX_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            page_records,
            file,
            indent=2,
            ensure_ascii=False,
        )

    summary = {
        "document_id": DOCUMENT_ID,
        "doi": DOI,
        "pages_with_caption_or_table": len(page_records),
        "caption_candidates": total_caption_candidates,
        "detected_tables": total_detected_tables,
        "manual_review_status": "not_started",
        "important_notice": (
            "Automatic table detection may contain false positives "
            "or miss tables. Every candidate requires manual review."
        ),
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("Chen2020 table detection completed.")
    print(
        "Pages with captions or detected tables: "
        f"{summary['pages_with_caption_or_table']}"
    )
    print(
        f"Caption candidates: "
        f"{summary['caption_candidates']}"
    )
    print(
        f"Detected tables: "
        f"{summary['detected_tables']}"
    )
    print(f"\nTable index: {INDEX_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    print(f"Local CSV directory: {TABLES_DIR}")


if __name__ == "__main__":
    extract_tables()
