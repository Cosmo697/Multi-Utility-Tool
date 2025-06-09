"""Utility functions for compressing and extracting archives."""

from __future__ import annotations

import logging
import os
import zipfile
from typing import Iterable

from utils.diagnostics import increment_usage, time_block
from utils.file_helpers import ensure_file_output_dir, generate_unique_file_path

logger = logging.getLogger(__name__)


def compress_items(items: Iterable[str], output_name: str, app) -> None:
    """Compress the given files/folders into a zip archive."""
    increment_usage("archive_compress")
    first_path = next(iter(items))
    out_dir = ensure_file_output_dir(first_path)
    archive_path = generate_unique_file_path(out_dir, output_name, "", "zip")
    with time_block(f"compress:{os.path.basename(archive_path)}"):
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                if os.path.isdir(item):
                    for root, _, files in os.walk(item):
                        for f in files:
                            file_path = os.path.join(root, f)
                            arcname = os.path.relpath(file_path, os.path.dirname(item))
                            zf.write(file_path, arcname)
                else:
                    zf.write(item, os.path.basename(item))
    app.queue.put((None, "status", f"Archive created: {archive_path}"))


def extract_archives(files: Iterable[str], app) -> None:
    """Extract each archive to its own folder."""
    increment_usage("archive_extract")
    for file_path in files:
        with time_block(f"extract:{os.path.basename(file_path)}"):
            if not zipfile.is_zipfile(file_path):
                app.queue.put((file_path, "status", "Skipping non-zip file."))
                continue
            out_dir = ensure_file_output_dir(file_path)
            extract_dir = os.path.join(out_dir, os.path.splitext(os.path.basename(file_path))[0])
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path) as zf:
                zf.extractall(extract_dir)
        app.queue.put((file_path, "status", f"Extracted to: {extract_dir}"))


def process_archives(files: Iterable[str], action: str, output_name: str, app) -> None:
    """Entry point for archive processing."""
    if action == "compress":
        compress_items(files, output_name, app)
    else:
        extract_archives(files, app)
    app.queue.put((None, "done", "Archive operation complete."))

