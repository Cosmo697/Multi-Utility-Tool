"""File Organizer plugin for managing and deduplicating files."""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging

from processors.file_organizer_processor import (
    scan_for_duplicates,
    move_files,
    delete_files,
    _get_db,
)
from utils.config_manager import load_config, save_config

logger = logging.getLogger(__name__)

CONFIG_KEY = "file_organizer"


def _load_prefs():
    cfg = load_config()
    return cfg.get(CONFIG_KEY, {})


def _save_prefs(data):
    cfg = load_config()
    cfg[CONFIG_KEY] = data
    save_config(cfg)


class OrganizerUI:
    def __init__(self, tab, plugin_api):
        self.tab = tab
        self.api = plugin_api
        self.paths = []
        prefs = _load_prefs()
        self.recursive = tk.BooleanVar(value=prefs.get("recursive", True))
        self.use_hash = tk.BooleanVar(value=prefs.get("use_hash", True))
        self.dry_run = tk.BooleanVar(value=False)
        self.schedule = tk.BooleanVar(value=prefs.get("schedule", False))
        self.interval = tk.IntVar(value=prefs.get("interval", 24))
        self._timer = None
        self._build_ui()
        if self.schedule.get():
            self._schedule_scan()

    def _build_ui(self):
        path_frame = ttk.LabelFrame(self.tab, text="Scan Paths")
        path_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox = tk.Listbox(path_frame, selectmode=tk.BROWSE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_frame = ttk.Frame(path_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn_frame, text="Add", command=self._add_path).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_sel).pack(fill=tk.X, pady=2)

        opts = ttk.Frame(self.tab)
        opts.pack(fill=tk.X, padx=5)
        ttk.Checkbutton(opts, text="Scan subdirectories", variable=self.recursive).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Identify duplicates by content", variable=self.use_hash).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Dry run", variable=self.dry_run).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Daily Scan", variable=self.schedule, command=self._toggle_schedule).pack(side=tk.LEFT)
        ttk.Label(opts, text="Interval(h)").pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(opts, from_=1, to=168, width=5, textvariable=self.interval).pack(side=tk.LEFT)

        action_frame = ttk.Frame(self.tab)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(action_frame, text="Scan", command=self._start_scan).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Move To...", command=self._move_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Copy To...", command=lambda: self._move_selected(copy=True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)

        self.tree = ttk.Treeview(self.tab, columns=("size", "path"), show="headings", selectmode="extended")
        self.tree.heading("size", text="Key")
        self.tree.heading("path", text="Path")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _add_path(self):
        path = filedialog.askdirectory(mustexist=True)
        if not path:
            return
        self.paths.append(path)
        self.listbox.insert(tk.END, path)

    def _remove_sel(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.listbox.delete(idx)
        del self.paths[idx]

    def _toggle_schedule(self):
        if self.schedule.get():
            self._schedule_scan()
        elif self._timer:
            self._timer.cancel()
            self._timer = None
        _save_prefs({
            "recursive": self.recursive.get(),
            "use_hash": self.use_hash.get(),
            "schedule": self.schedule.get(),
            "interval": self.interval.get(),
        })

    def _schedule_scan(self):
        if self._timer:
            self._timer.cancel()
        hours = self.interval.get()
        self._timer = threading.Timer(hours * 3600, self._start_scan)
        self._timer.daemon = True
        self._timer.start()

    def _start_scan(self):
        if not self.paths:
            messagebox.showerror("Error", "No paths selected")
            return
        data = {
            "recursive": self.recursive.get(),
            "use_hash": self.use_hash.get(),
            "schedule": self.schedule.get(),
            "interval": self.interval.get(),
        }
        _save_prefs(data)
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        self.api.trigger_hook("organizer_pre_scan", self.paths)
        conn = _get_db()
        dupes = scan_for_duplicates(
            self.paths,
            recursive=self.recursive.get(),
            use_hash=self.use_hash.get(),
            fuzzy=False,
            conn=conn,
        )
        self.tree.delete(*self.tree.get_children())
        for key, paths in dupes.items():
            for p in paths:
                self.tree.insert("", tk.END, values=(key, p))
        self.api.trigger_hook("organizer_post_action", dupes)

    def _selected_files(self):
        items = self.tree.selection()
        return [self.tree.item(it)["values"][1] for it in items]

    def _move_selected(self, copy=False):
        files = self._selected_files()
        if not files:
            return
        dest = filedialog.askdirectory()
        if not dest:
            return
        if self.dry_run.get():
            messagebox.showinfo("Dry Run", f"Would move {len(files)} files to {dest}")
            return
        move_files(files, dest, delete=not copy)
        self._start_scan()

    def _delete_selected(self):
        files = self._selected_files()
        if not files:
            return
        if messagebox.askyesno("Delete", f"Delete {len(files)} files?"):
            if self.dry_run.get():
                messagebox.showinfo("Dry Run", f"Would delete {len(files)} files")
                return
            delete_files(files)
            self._start_scan()

def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("File Organizer", tab)
    ui = OrganizerUI(tab, plugin_api)

    def run_last_scan():
        ui._start_scan()

    plugin_api.register_hook("preset:Scan Duplicates", run_last_scan)
    plugin_api.register_hook("list_presets", lambda: ["Scan Duplicates"])
    plugin_api.register_hook("organizer_pre_scan", lambda paths: None)
    plugin_api.register_hook("organizer_post_action", lambda results: None)

