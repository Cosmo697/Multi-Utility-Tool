import os

import pytest

from multi_utility_tool.utils import config_manager

def test_config_file_location():
    path = config_manager.CONFIG_FILE
    assert os.path.basename(path) == "config.yaml"
    # Should be in user config dir, not project root
    assert "MultiUtilityTool" in path

def test_save_and_load_config(tmp_path, monkeypatch):
    # Patch config file location to temp
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(tmp_path / "config.yaml"))
    data = {"foo": "bar"}
    config_manager.save_config(data)
    loaded = config_manager.load_config()
    assert loaded == data


def test_load_with_defaults_and_corrupted_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(tmp_path / "config.yaml"))
    tmp_path.mkdir(exist_ok=True)
    corrupt_file = tmp_path / "config.yaml"
    corrupt_file.write_text("::not_yaml::", encoding="utf-8")

    defaults = {"safe": True}
    loaded = config_manager.load_config(defaults=defaults)
    assert loaded == defaults


def test_save_rejects_invalid_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(tmp_path / "config.yaml"))
    with pytest.raises(TypeError):
        config_manager.save_config([1, 2, 3])


def test_update_config_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(tmp_path / "config.yaml"))
    config_manager.save_config({"a": 1})
    updated = config_manager.update_config({"b": 2})
    assert updated == {"a": 1, "b": 2}
    assert config_manager.load_config() == updated
