import threading
import logging
import pystray
from pystray import MenuItem as Item, Menu
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

class TrayAgent:
    """System tray integration with quick preset actions."""

    def __init__(self, app) -> None:
        self.app = app
        self.icon = pystray.Icon("MUT", self._create_image(), "Multi-Utility Tool")
        self.icon.menu = self._build_menu()

    def _create_image(self):
        image = Image.new("RGB", (64, 64), "black")
        d = ImageDraw.Draw(image)
        d.rectangle((16, 16, 48, 48), fill="white")
        return image

    def _build_menu(self):
        preset_items = []
        for result in self.app.plugins.collect("list_presets"):
            if isinstance(result, dict):
                for name in result.keys():
                    preset_items.append(Item(name, lambda _, n=name: self._trigger(n)))
            elif isinstance(result, (list, tuple)):
                for name in result:
                    preset_items.append(Item(name, lambda _, n=name: self._trigger(n)))
        if not preset_items:
            preset_items.append(Item("None", lambda: None, enabled=False))
        menu = Menu(
            Item("Restore", self._restore),
            Item("Exit", self._exit),
            Item("Presets", Menu(*preset_items))
        )
        return menu

    def show(self) -> None:
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _restore(self, icon=None, item=None):
        logger.info("Restoring window from tray")
        self.icon.stop()
        self.app.root.after(0, self.app.root.deiconify)

    def _exit(self, icon=None, item=None):
        logger.info("Exiting from tray menu")
        self.icon.stop()
        self.app.root.after(0, self.app.root.quit)

    def _trigger(self, preset: str) -> None:
        logger.info("Tray preset triggered: %s", preset)
        self.app.plugins.api.trigger_hook(f"preset:{preset}")

    def notify(self, message: str) -> None:
        try:
            self.icon.notify(message)
        except Exception:
            logger.debug("Tray notification unsupported on this platform")
