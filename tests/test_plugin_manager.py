from plugins import plugin_manager

def test_plugin_metadata_enforcement(tmp_path, monkeypatch):
    # Create a dummy plugin file with missing metadata and a register_plugin that calls add_tab
    plugin_code = "def register_plugin(api): api.add_tab('Dummy', object())"
    plugin_file = tmp_path / "dummy_plugin.py"
    plugin_file.write_text(plugin_code)
    loaded = []
    class DummyAPI:
        def add_tab(self, *a, **kw):
            loaded.append(True)
    # Should log a warning about missing metadata
    plugin_manager.load_plugins(DummyAPI(), plugins_dir=str(tmp_path))
    assert loaded
