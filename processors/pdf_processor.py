"""PDF utility functions for merging and splitting PDFs."""

from __future__ import annotations

import os
import logging
from typing import Iterable

from PyPDF2 import PdfReader, PdfWriter

from utils.diagnostics import increment_usage, time_block
from utils.file_helpers import ensure_file_output_dir, generate_unique_file_path

logger = logging.getLogger(__name__)


def merge_pdfs(pdf_files: Iterable[str], output_name: str, app) -> None:
    """Merge the given PDF files into a single document."""
    increment_usage("pdf_merge")
    first = next(iter(pdf_files))
    out_dir = ensure_file_output_dir(first)
    output_path = generate_unique_file_path(out_dir, output_name, "", "pdf")
    writer = PdfWriter()
    with time_block(f"pdf_merge:{os.path.basename(output_path)}"):
        for pdf in pdf_files:
            try:
                reader = PdfReader(pdf)
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                logger.error("Error reading %s: %s", pdf, e)
                app.queue.put((pdf, "status", f"Read error: {e}"))
    with open(output_path, "wb") as out_f:
        writer.write(out_f)
    app.queue.put((None, "status", f"Merged PDF saved: {output_path}"))


def split_pdf(pdf_file: str, start: int, end: int, app) -> None:
    """Split the provided PDF into the page range [start, end] (1-indexed)."""
    increment_usage("pdf_split")
    with time_block(f"pdf_split:{os.path.basename(pdf_file)}"):
        try:
            reader = PdfReader(pdf_file)
        except Exception as e:
            logger.error("Error opening %s: %s", pdf_file, e)
            app.queue.put((pdf_file, "status", f"Open error: {e}"))
            return
        if start < 1 or start > len(reader.pages):
            start = 1
        if end < start or end > len(reader.pages):
            end = len(reader.pages)
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        out_dir = ensure_file_output_dir(pdf_file)
        base = os.path.splitext(os.path.basename(pdf_file))[0]
        output_path = generate_unique_file_path(out_dir, base, f"_{start}-{end}", "pdf")
        with open(output_path, "wb") as out_f:
            writer.write(out_f)
    app.queue.put((None, "status", f"Split PDF saved: {output_path}"))
    app.queue.put((None, "done", "PDF operation complete."))
