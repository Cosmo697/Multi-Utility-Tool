import logging
import keyboard
import tkinter as tk
from tkinter import ttk, messagebox
from utils.config_manager import load_config, save_config

logger = logging.getLogger(__name__)

CONFIG_KEY = "hotkeys"

class HotkeyManager:
    """Manage global hotkeys that trigger preset hooks."""

    def __init__(self, app):
        self.app = app
        self.hotkeys = {}
        self._load()
        self._register_all()

    def _load(self):
        cfg = load_config()
        self.hotkeys = cfg.get(CONFIG_KEY, {})
        logger.debug("Loaded hotkeys: %s", self.hotkeys)

    def _save(self):
        cfg = load_config()
        cfg[CONFIG_KEY] = self.hotkeys
        save_config(cfg)
        logger.debug("Saved hotkeys: %s", self.hotkeys)

    def _register_all(self):
        keyboard.unhook_all_hotkeys()
        for hk, preset in self.hotkeys.items():
            self._register(hk, preset)

    def _register(self, hotkey, preset):
        keyboard.add_hotkey(hotkey, lambda p=preset: self._trigger(p))
        logger.info("Registered hotkey %s for preset %s", hotkey, preset)

    def _trigger(self, preset):
        logger.info("Hotkey triggered preset: %s", preset)
        self.app.plugin_api.trigger_hook(f"preset:{preset}")

    def add_hotkey(self, hotkey, preset):
        self.hotkeys[hotkey] = preset
        self._register(hotkey, preset)
        self._save()

    def remove_hotkey(self, hotkey):
        if hotkey in self.hotkeys:
            keyboard.remove_hotkey(hotkey)
            del self.hotkeys[hotkey]
            self._save()

    # GUI Helpers
    def open_manager(self):
        win = tk.Toplevel(self.app.root)
        win.title("Hotkey Manager")
        listbox = tk.Listbox(win, width=40)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)

        def refresh():
            listbox.delete(0, tk.END)
            for hk, pre in self.hotkeys.items():
                listbox.insert(tk.END, f"{hk} -> {pre}")
        refresh()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add", command=lambda: self._add_dialog(refresh)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove", command=lambda: self._remove_selected(listbox, refresh)).pack(side=tk.LEFT)

    def _add_dialog(self, refresh):
        dlg = tk.Toplevel(self.app.root)
        dlg.title("Add Hotkey")
        tk.Label(dlg, text="Hotkey:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        hk_var = tk.StringVar()
        tk.Entry(dlg, textvariable=hk_var, width=15).grid(row=0, column=1, padx=5, pady=2)

        tk.Label(dlg, text="Preset:").grid(row=1, column=0, sticky=tk.W, padx=5)
        presets = []
        for result in self.app.plugin_api.collect("list_presets"):
            if isinstance(result, dict):
                presets.extend(result.keys())
            elif isinstance(result, (list, tuple)):
                presets.extend(result)
        pre_var = tk.StringVar(value=presets[0] if presets else "")
        ttk.Combobox(dlg, textvariable=pre_var, values=presets, state="readonly").grid(row=1, column=1, padx=5)

        def save():
            hk = hk_var.get().strip()
            pre = pre_var.get().strip()
            if not hk or not pre:
                messagebox.showerror("Error", "Hotkey and preset required")
                return
            self.add_hotkey(hk, pre)
            refresh()
            dlg.destroy()
        ttk.Button(dlg, text="Save", command=save).grid(row=2, column=0, columnspan=2, pady=5)

    def _remove_selected(self, listbox, refresh):
        selection = listbox.curselection()
        if not selection:
            return
        item = listbox.get(selection[0])
        hotkey = item.split(" -> ")[0]
        self.remove_hotkey(hotkey)
        refresh()
