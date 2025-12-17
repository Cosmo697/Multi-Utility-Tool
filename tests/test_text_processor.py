from multi_utility_tool.processors import text_processor
import tempfile
import os

def test_process_text_files_creates_output(tmp_path):
    file1 = tmp_path / "a.txt"
    file1.write_text("hello world")
    file2 = tmp_path / "b.txt"
    file2.write_text("goodbye world")
    app = type("App", (), {"queue": type("Q", (), {"put": lambda *a, **k: None})(), "start_progress": lambda *a, **k: None, "increment_progress": lambda *a, **k: None})()
    text_processor.process_text_files([str(file1), str(file2)], False, False, None, None, False, False, app)
    # Should create processed output in user data dir
    from multi_utility_tool.utils.file_helpers import ensure_file_output_dir
    out_dir = ensure_file_output_dir(str(file1))
    found = any(f.endswith("a_processed.txt") or f.endswith("b_processed.txt") for f in os.listdir(out_dir))
    assert found
