import logging
from core.hooks import Hooks
from core.plugin_api import PluginAPI
from plugins.plugin_manager import load_plugins

logger = logging.getLogger(__name__)


class PluginAgent:
    """Manage hooks and load plugins."""

    def __init__(self, app) -> None:
        self.app = app
        self.hooks = Hooks()
        # expose hooks to the application for PluginAPI compatibility
        self.app.hooks = self.hooks
        self.api = PluginAPI(app)
        # maintain backward compatibility with old code
        self.app.plugin_api = self.api
        logger.info("Loading plugins")
        load_plugins(self.api)

    def trigger(self, hook: str, *args, **kwargs) -> None:
        self.hooks.trigger(hook, *args, **kwargs)

    def collect(self, hook: str, *args, **kwargs):
        return self.hooks.collect(hook, *args, **kwargs)
