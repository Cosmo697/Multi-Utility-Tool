import logging
import tkinter as tk
from tkinter import ttk, messagebox
from utils.config_manager import load_config, save_config

try:  # pragma: no cover - import guard
    import keyboard  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    keyboard = None
    logging.getLogger(__name__).warning(
        "keyboard library not available; global hotkeys disabled"
    )

logger = logging.getLogger(__name__)

CONFIG_KEY = "hotkeys"


class HotkeyAgent:
    """Manage global hotkeys that trigger preset hooks."""

    def __init__(self, app) -> None:
        self.app = app
        self.hotkeys: dict[str, str] = {}
        self._load()
        if keyboard is not None:
            self._register_all()

    def _load(self) -> None:
        cfg = load_config()
        self.hotkeys = cfg.get(CONFIG_KEY, {})
        logger.debug("Loaded hotkeys: %s", self.hotkeys)

    def _save(self) -> None:
        cfg = load_config()
        cfg[CONFIG_KEY] = self.hotkeys
        save_config(cfg)
        logger.debug("Saved hotkeys: %s", self.hotkeys)

    def _clear_hotkeys(self) -> None:
        """Remove previously registered hotkeys in a version tolerant way."""
        if keyboard is None:
            return
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            try:
                keyboard.clear_all_hotkeys()
            except Exception as exc:  # pragma: no cover - best effort
                logger.debug("Failed to clear hotkeys: %s", exc)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Failed to clear hotkeys: %s", exc)

    def _register_all(self) -> None:
        if keyboard is None:
            return
        self._clear_hotkeys()
        for hk, preset in self.hotkeys.items():
            self._register(hk, preset)

    def _register(self, hotkey: str, preset: str) -> None:
        if keyboard is None:
            logger.debug("Skipping hotkey registration for %s", hotkey)
            return
        keyboard.add_hotkey(hotkey, lambda p=preset: self._trigger(p))
        logger.info("Registered hotkey %s for preset %s", hotkey, preset)

    def _trigger(self, preset: str) -> None:
        logger.info("Hotkey triggered preset: %s", preset)
        self.app.plugins.api.trigger_hook(f"preset:{preset}")

    def add_hotkey(self, hotkey: str, preset: str) -> None:
        self.hotkeys[hotkey] = preset
        self._register(hotkey, preset)
        self._save()

    def remove_hotkey(self, hotkey: str) -> None:
        if hotkey in self.hotkeys:
            if keyboard is not None:
                keyboard.remove_hotkey(hotkey)
            del self.hotkeys[hotkey]
            self._save()

    # GUI Helpers
    def open_manager(self) -> None:
        win = tk.Toplevel(self.app.root)
        win.title("Hotkey Manager")
        listbox = tk.Listbox(win, width=40)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        def refresh() -> None:
            listbox.delete(0, tk.END)
            for hk, pre in self.hotkeys.items():
                listbox.insert(tk.END, f"{hk} -> {pre}")

        refresh()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(
            btn_frame, text="Add", command=lambda: self._add_dialog(refresh)
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Remove",
            command=lambda: self._remove_selected(listbox, refresh),
        ).pack(side=tk.LEFT)

    def _add_dialog(self, refresh) -> None:
        dlg = tk.Toplevel(self.app.root)
        dlg.title("Add Hotkey")
        tk.Label(dlg, text="Hotkey:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        hk_var = tk.StringVar()
        tk.Entry(dlg, textvariable=hk_var, width=15).grid(
            row=0, column=1, padx=5, pady=2
        )

        tk.Label(dlg, text="Preset:").grid(row=1, column=0, sticky=tk.W, padx=5)
        presets = []
        for result in self.app.plugins.collect("list_presets"):
            if isinstance(result, dict):
                presets.extend(result.keys())
            elif isinstance(result, (list, tuple)):
                presets.extend(result)
        pre_var = tk.StringVar(value=presets[0] if presets else "")
        ttk.Combobox(dlg, textvariable=pre_var, values=presets, state="readonly").grid(
            row=1, column=1, padx=5
        )

        def save() -> None:
            hk = hk_var.get().strip()
            pre = pre_var.get().strip()
            if not hk or not pre:
                messagebox.showerror("Error", "Hotkey and preset required")
                return
            self.add_hotkey(hk, pre)
            refresh()
            dlg.destroy()

        ttk.Button(dlg, text="Save", command=save).grid(
            row=2, column=0, columnspan=2, pady=5
        )

    def _remove_selected(self, listbox, refresh) -> None:
        selection = listbox.curselection()
        if not selection:
            return
        item = listbox.get(selection[0])
        hotkey = item.split(" -> ")[0]
        self.remove_hotkey(hotkey)
        refresh()
