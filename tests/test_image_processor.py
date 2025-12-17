from multi_utility_tool.processors import image_processor
import tempfile
import os
from PIL import Image

def test_process_images_creates_output(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    img.save(img_path)
    app = type("App", (), {"queue": type("Q", (), {"put": lambda *a, **k: None})(), "start_progress": lambda *a, **k: None, "increment_progress": lambda *a, **k: None})()
    image_processor.process_images([str(img_path)], "none", 100, 10, 10, True, "", 0, False, "", False, "png", app)
    from multi_utility_tool.utils.file_helpers import ensure_file_output_dir
    out_dir = ensure_file_output_dir(str(img_path))
    found = any(f.endswith(".png") for f in os.listdir(out_dir))
    assert found
