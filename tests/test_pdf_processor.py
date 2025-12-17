from multi_utility_tool.processors import pdf_processor
import tempfile
import os
from PyPDF2 import PdfWriter

def test_merge_pdfs_creates_output(tmp_path):
    pdf1 = tmp_path / "a.pdf"
    pdf2 = tmp_path / "b.pdf"
    for p in [pdf1, pdf2]:
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with open(p, "wb") as f:
            writer.write(f)
    app = type("App", (), {"queue": type("Q", (), {"put": lambda *a, **k: None})(), "start_progress": lambda *a, **k: None, "increment_progress": lambda *a, **k: None})()
    pdf_processor.merge_pdfs([str(pdf1), str(pdf2)], "merged", app)
    from multi_utility_tool.utils.file_helpers import ensure_file_output_dir
    out_dir = ensure_file_output_dir(str(pdf1))
    found = any(f.startswith("merged") and f.endswith(".pdf") for f in os.listdir(out_dir))
    assert found
