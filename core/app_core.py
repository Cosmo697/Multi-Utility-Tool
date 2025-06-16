import logging
from agents.logger_agent import LoggerAgent
from agents.ui_agent import UIAgent
from agents.plugin_agent import PluginAgent
from agents.hotkey_agent import HotkeyAgent
from agents.tray_agent import TrayAgent

logger = logging.getLogger(__name__)


class AppCore:
    """Central coordinator that wires individual agents together."""

    def __init__(self) -> None:
        self.logger = LoggerAgent()
        self.ui = UIAgent(self)
        self.root = self.ui.root
        self.notebook = self.ui.notebook  # Expose notebook for plugins
        self.plugins = PluginAgent(self)
        self.hotkeys = HotkeyAgent(self)
        self.tray = TrayAgent(self)
        self.threads = []  # Added for thread tracking
        self.ui.attach()
        logger.info("App core initialized")

    def register_thread(self, thread):
        self.threads.append(thread)

    # Delegate tab addition for plugins
    def add_plugin_tab(self, title, frame):
        self.ui.add_plugin_tab(title, frame)
