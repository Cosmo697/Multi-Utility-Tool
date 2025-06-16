from processors import video_processor
import tempfile
import os

def test_video_processor_runs(tmp_path):
    # This test only checks that the function runs without error for empty input
    app = type("App", (), {"queue": type("Q", (), {"put": lambda *a, **k: None})(), "start_progress": lambda *a, **k: None, "increment_progress": lambda *a, **k: None})()
    video_processor.process_videos([], {}, app)
