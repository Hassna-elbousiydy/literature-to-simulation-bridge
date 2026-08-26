"""Extract page-level and block-level text from the local Chen2020 PDF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

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

PAGES_PATH = OUTPUT_DIR / "pages.jsonl"
BLOCKS_PATH = OUTPUT_DIR / "blocks.jsonl"
FULL_TEXT_PATH = OUTPUT_DIR / "full_text.txt"
SUMMARY_PATH = OUTPUT_DIR / "extraction_summary.json"

DOCUMENT_ID = "chen2020"
DOI = "10.1149/1945-7111/ab9050"


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write one JSON object per line."""

    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )
            file.write("\n")


def get_page_label(page: pymupdf.Page, pdf_page: int) -> str:
    """Return the PDF page label when one is available."""

    try:
        label = page.get_label()
    except AttributeError:
        label = ""

    return label or str(pdf_page)


def extract_pdf() -> None:
    """Extract text and spatial blocks while preserving page provenance."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Local PDF not found: {PDF_PATH}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pages: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    full_text_sections: list[str] = []

    document = pymupdf.open(PDF_PATH)
    metadata = document.metadata or {}

    for page_index, page in enumerate(document):
        pdf_page = page_index + 1
        page_label = get_page_label(page, pdf_page)

        page_text = page.get_text("text", sort=True).strip()
        page_blocks = page.get_text("blocks", sort=True)

        pages.append(
            {
                "document_id": DOCUMENT_ID,
                "doi": DOI,
                "pdf_page": pdf_page,
                "page_label": page_label,
                "character_count": len(page_text),
                "word_count": len(page_text.split()),
                "text": page_text,
            }
        )

        full_text_sections.append(
            f"===== PDF PAGE {pdf_page} "
            f"| LABEL {page_label} =====\n"
            f"{page_text}\n"
        )

        for block in page_blocks:
            if len(block) < 7:
                continue

            x0, y0, x1, y1, text, block_number, block_type = block[:7]
            cleaned_text = text.strip()

            # Type 0 corresponds to text blocks.
            if block_type != 0 or not cleaned_text:
                continue

            blocks.append(
                {
                    "document_id": DOCUMENT_ID,
                    "doi": DOI,
                    "pdf_page": pdf_page,
                    "page_label": page_label,
                    "block_id": (
                        f"{DOCUMENT_ID}-"
                        f"p{pdf_page:03d}-"
                        f"b{int(block_number):03d}"
                    ),
                    "block_number": int(block_number),
                    "block_type": "text",
                    "bbox": {
                        "x0": round(float(x0), 3),
                        "y0": round(float(y0), 3),
                        "x1": round(float(x1), 3),
                        "y1": round(float(y1), 3),
                    },
                    "character_count": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "text": cleaned_text,
                }
            )

    document.close()

    write_jsonl(PAGES_PATH, pages)
    write_jsonl(BLOCKS_PATH, blocks)

    FULL_TEXT_PATH.write_text(
        "\n".join(full_text_sections),
        encoding="utf-8",
    )

    summary = {
        "document_id": DOCUMENT_ID,
        "doi": DOI,
        "source_filename": PDF_PATH.name,
        "source_sha256": hashlib.sha256(
            PDF_PATH.read_bytes()
        ).hexdigest(),
        "pymupdf_version": getattr(
            pymupdf,
            "VersionBind",
            getattr(pymupdf, "__version__", "unknown"),
        ),
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "page_count": len(pages),
        "pages_with_text": sum(
            bool(page_record["text"])
            for page_record in pages
        ),
        "total_page_characters": sum(
            page_record["character_count"]
            for page_record in pages
        ),
        "total_page_words": sum(
            page_record["word_count"]
            for page_record in pages
        ),
        "text_block_count": len(blocks),
        "important_notice": (
            "Full extracted text and blocks are local-only inputs "
            "and are excluded from Git."
        ),
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("Chen2020 PDF extraction completed successfully.")
    print(f"Pages: {summary['page_count']}")
    print(f"Pages with text: {summary['pages_with_text']}")
    print(f"Total characters: {summary['total_page_characters']}")
    print(f"Total words: {summary['total_page_words']}")
    print(f"Text blocks: {summary['text_block_count']}")
    print(f"\nPages JSONL: {PAGES_PATH}")
    print(f"Blocks JSONL: {BLOCKS_PATH}")
    print(f"Full text: {FULL_TEXT_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    extract_pdf()
