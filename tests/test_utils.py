import os
import sys
import types
import subprocess
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide a minimal yaml stub if PyYAML is unavailable
if "yaml" not in sys.modules:

    def _dump(data, f):
        f.write(repr(data))

    def _load(stream):
        return eval(stream.read() or "{}")

    yaml_stub = types.SimpleNamespace(safe_load=_load, dump=_dump)
    sys.modules["yaml"] = yaml_stub

from utils import config_manager, diagnostics, file_helpers, ffmpeg_helpers
from core import hooks
from plugins import plugin_manager


def test_config_manager_load_save(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    with mock.patch.object(config_manager, "CONFIG_FILE", cfg_path):
        data = {"foo": 1}
        config_manager.save_config(data)
        assert cfg_path.exists()
        loaded = config_manager.load_config()
        assert loaded == data


def test_increment_usage_and_stats():
    diagnostics.increment_usage("test")
    diagnostics.increment_usage("test")
    stats = diagnostics.get_usage_stats()
    assert stats["test"] == 2


def test_time_block_logs(caplog):
    with caplog.at_level("DEBUG"):
        with diagnostics.time_block("unit_test"):
            pass
    assert any("unit_test" in rec.message for rec in caplog.records)


def test_ensure_file_output_dir(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("hi")
    out_dir = file_helpers.ensure_file_output_dir(str(file_path))
    assert os.path.isdir(out_dir)


def test_generate_unique_file_path(tmp_path):
    path = file_helpers.generate_unique_file_path(str(tmp_path), "name", "", "txt")
    open(path, "w").close()
    path2 = file_helpers.generate_unique_file_path(str(tmp_path), "name", "", "txt")
    assert path != path2


def test_read_file_content_txt(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello")
    assert file_helpers.read_file_content(str(p)) == "hello"


def test_run_ffmpeg_command_success():
    with mock.patch("subprocess.run") as run:
        run.return_value = mock.Mock(returncode=0)
        assert ffmpeg_helpers.run_ffmpeg_command(["ffmpeg"], "err") is None


def test_run_ffmpeg_command_failure():
    with mock.patch(
        "subprocess.run", side_effect=subprocess.CalledProcessError(1, ["ffmpeg"])
    ):
        err = ffmpeg_helpers.run_ffmpeg_command(["ffmpeg"], "oops")
        assert err is not None


def test_is_gpu_available_true():
    with mock.patch("subprocess.run") as run:
        run.return_value = mock.Mock(returncode=0)
        assert ffmpeg_helpers.is_gpu_available() is True


def test_is_gpu_available_false():
    with mock.patch("subprocess.run", side_effect=FileNotFoundError):
        assert ffmpeg_helpers.is_gpu_available() is False


def test_hooks_trigger_collect():
    h = hooks.Hooks()
    result = []

    def cb(x):
        result.append(x)
        return x * 2

    h.register("test", cb)
    h.trigger("test", 3)
    assert result == [3]
    collected = h.collect("test", 4)
    assert collected == [8]


def test_plugin_manager_load_plugins(tmp_path):
    plugins_dir = tmp_path
    plugin_file = plugins_dir / "demo.py"
    plugin_file.write_text("def register_plugin(api):\n    api.add_tab('demo', None)\n")
    called = {}

    def add_tab(name, frame):
        called["name"] = name

    api = types.SimpleNamespace(add_tab=add_tab)
    plugin_manager.load_plugins(api, plugins_dir=str(plugins_dir))
    assert called["name"] == "demo"
