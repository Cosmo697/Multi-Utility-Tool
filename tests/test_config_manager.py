from utils import config_manager
import os

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
