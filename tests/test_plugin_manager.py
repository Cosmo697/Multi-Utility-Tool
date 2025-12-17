from multi_utility_tool.plugins import plugin_manager
from multi_utility_tool.plugins.plugin_manager import PluginLoadResult


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
    results = plugin_manager.load_plugins(agent, plugins_dir=str(tmp_path))
    assert agent.api.added
    assert results == [
        PluginLoadResult(
            name="dummy_plugin",
            path=str(plugin_file.resolve()),
            success=True,
            duration=results[0].duration,
            error=None,
        )
    ]


def test_plugin_failure_recorded(tmp_path):
    plugin_code = "def register_plugin(api): raise RuntimeError('boom')"
    plugin_file = tmp_path / "bad_plugin.py"
    plugin_file.write_text(plugin_code)
    agent = DummyAgent()
    results = plugin_manager.load_plugins(agent, plugins_dir=str(tmp_path))

    assert len(results) == 1
    result = results[0]
    assert not result.success
    assert result.error
    assert result.name == "bad_plugin"
    assert result.path == str(plugin_file.resolve())


def test_plugin_outside_directory_is_skipped(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    outside_file = tmp_path / ".." / "outside.py"
    outside_file.write_text("def register_plugin(api): pass")
    symlink_path = plugins_dir / "outside.py"
    symlink_path.symlink_to(outside_file.resolve())

    agent = DummyAgent()
    results = plugin_manager.load_plugins(agent, plugins_dir=str(plugins_dir))

    assert results == []
    assert not agent.api.added
