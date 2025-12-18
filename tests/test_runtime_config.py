from __future__ import annotations

import pytest

from core.runtime import RuntimeConfig
from utils.diagnostics import emit_metrics_snapshot


def test_runtime_config_parses_and_validates(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()

    config = RuntimeConfig.from_env_and_args(
        ["--headless", "--no-hotkeys", "--no-tray", "--workers", "6", "--plugin-dir", str(plugin_dir)]
    )

    assert config.headless is True
    assert config.enable_hotkeys is False
    assert config.enable_tray is False
    assert config.worker_count == 6
    assert config.plugin_dir == plugin_dir.resolve()


def test_runtime_config_invalid_workers():
    with pytest.raises(ValueError):
        RuntimeConfig.from_env_and_args(["--workers", "0"])


def test_runtime_config_invalid_plugin_dir(tmp_path):
    bogus = tmp_path / "missing"
    with pytest.raises(ValueError):
        RuntimeConfig.from_env_and_args(["--plugin-dir", str(bogus)])


def test_runtime_config_env_default(monkeypatch, tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    monkeypatch.setenv("MUT_PLUGIN_DIR", str(plugin_dir))
    monkeypatch.setenv("MUT_LOG_LEVEL", "DEBUG")

    config = RuntimeConfig.from_env_and_args([])

    assert config.plugin_dir == plugin_dir.resolve()
    assert config.log_level <= 10  # DEBUG level


def test_metrics_emission(tmp_path):
    metrics_file = tmp_path / "metrics.jsonl"
    payload = emit_metrics_snapshot(path=metrics_file, extra={"runtime": "test"})

    assert payload["usage"] == {}
    assert metrics_file.exists()
    lines = metrics_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "runtime" in lines[0]
