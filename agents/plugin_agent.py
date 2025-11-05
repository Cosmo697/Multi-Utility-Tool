import logging
from core.hooks import Hooks
from core.plugin_api import PluginAPI
from core.plugin_manifest import PluginManifest
from plugins.plugin_manager import load_plugins

logger = logging.getLogger(__name__)


class PluginAgent:
    """Manage hooks and load plugins."""

    def __init__(self, app, autoload: bool = True) -> None:
        self.app = app
        self.hooks = Hooks()
        # expose hooks to the application for PluginAPI compatibility
        self.app.hooks = self.hooks
        self.api = PluginAPI(app)
        # maintain backward compatibility with old code
        self.app.plugin_api = self.api
        self.manifests: dict[str, PluginManifest] = {}
        logger.info("Loading plugins")
        if autoload:
            load_plugins(self)

    def trigger(self, hook: str, *args, **kwargs) -> None:
        self.hooks.trigger(hook, *args, **kwargs)

    def collect(self, hook: str, *args, **kwargs):
        return self.hooks.collect(hook, *args, **kwargs)

    def register_manifest(self, manifest: PluginManifest) -> None:
        """Store manifest information for later discovery."""

        self.manifests[manifest.plugin_id] = manifest
        logger.debug("Registered plugin manifest: %s", manifest)
