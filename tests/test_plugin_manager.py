from plugins import plugin_manager


class DummyAgent:
    def __init__(self):
        self.api = DummyAPI(self)

    def register_manifest(self, manifest):
        self.last_manifest = manifest


class DummyAPI:
    def __init__(self, app):
        self.app = app
        self.added = False

    def add_tab(self, *args, **kwargs):
        self.added = True

    def begin_registration(self, manifest):
        self._manifest = manifest

    def end_registration(self):
        self._manifest = None


def test_plugin_metadata_enforcement(tmp_path):
    plugin_code = "def register_plugin(api): api.add_tab('Dummy', object())"
    plugin_file = tmp_path / "dummy_plugin.py"
    plugin_file.write_text(plugin_code)
    agent = DummyAgent()
    plugin_manager.load_plugins(agent, plugins_dir=str(tmp_path))
    assert agent.api.added
