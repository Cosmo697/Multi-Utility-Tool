import os
from multi_utility_tool.utils.file_helpers import ensure_file_output_dir

def test_ensure_file_output_dir_creates_dir(tmp_path):
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("test")
    output_dir = ensure_file_output_dir(str(dummy_file))
    assert os.path.exists(output_dir)
    assert output_dir.endswith("outputs")
