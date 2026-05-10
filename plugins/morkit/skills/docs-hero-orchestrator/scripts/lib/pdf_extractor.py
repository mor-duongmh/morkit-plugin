"""PDF extraction wrapper combining pypdf (text) and pdfplumber (tables).

Public API:
    extract_pdf(path) -> PdfContent
    PdfContent: dataclass with .text, .pages, .tables
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

log = logging.getLogger(__name__)


@dataclass
class PdfPage:
    page_num: int  # 1-indexed
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)  # list of (rows of cells)


@dataclass
class PdfContent:
    path: str
    page_count: int
    text: str  # full doc text concatenated
    pages: list[PdfPage] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)  # all tables flattened
    extraction_warnings: list[str] = field(default_factory=list)


def extract_pdf(path: str | Path) -> PdfContent:
    """Extract text + tables from PDF.

    Strategy:
      - pypdf for text (fast, reliable for body text)
      - pdfplumber for tables (better than pypdf for tabular data)
    """
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    content = PdfContent(path=str(pdf_path), page_count=0, text="")

    # Text via pypdf
    try:
        reader = PdfReader(str(pdf_path))
        content.page_count = len(reader.pages)
        text_parts: list[str] = []
        for idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:  # pypdf can throw on malformed pages
                log.warning("pypdf failed on page %d: %s", idx, exc)
                content.extraction_warnings.append(f"page {idx}: {exc}")
                page_text = ""
            content.pages.append(PdfPage(page_num=idx, text=page_text))
            text_parts.append(page_text)
        content.text = "\n\n".join(text_parts)
    except Exception as exc:
        log.error("pypdf failed entirely on %s: %s", pdf_path, exc)
        content.extraction_warnings.append(f"pypdf-fatal: {exc}")

    # Tables via pdfplumber (best-effort)
    try:
        with pdfplumber.open(str(pdf_path)) as plumber_pdf:
            for idx, page in enumerate(plumber_pdf.pages, start=1):
                page_tables = page.extract_tables() or []
                # Filter empty tables
                page_tables = [
                    [[cell or "" for cell in row] for row in table]
                    for table in page_tables
                    if table and any(any(cell for cell in row) for row in table)
                ]
                if idx - 1 < len(content.pages):
                    content.pages[idx - 1].tables = page_tables
                content.tables.extend(page_tables)
    except Exception as exc:
        log.warning("pdfplumber failed on %s: %s", pdf_path, exc)
        content.extraction_warnings.append(f"pdfplumber: {exc}")

    return content
