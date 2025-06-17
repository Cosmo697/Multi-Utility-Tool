"""File Organizer plugin for managing and deduplicating files."""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
import os

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
        self._timer = None
        # Only used for duplicates tab
        self.paths = []
        self._build_ui()

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.tab)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Organize Files Tab
        self.organize_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.organize_tab, text="Organize Files")
        self._build_organize_tab()

        # Find Duplicates Tab
        self.duplicates_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.duplicates_tab, text="Find Duplicates")
        self._build_duplicates_tab()

    # --- Organize Files Tab ---
    def _build_organize_tab(self):
        # Folder selection
        folder_frame = ttk.LabelFrame(self.organize_tab, text="Browse Folder")
        folder_frame.pack(fill=tk.X, padx=5, pady=5)
        self.folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="Browse", command=self._browse_folder).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Refresh", command=self._refresh_file_list).pack(side=tk.LEFT)

        # File list
        self.file_tree = ttk.Treeview(self.organize_tab, columns=("name", "size", "modified"), show="headings", selectmode="extended")
        self.file_tree.heading("name", text="Name")
        self.file_tree.heading("size", text="Size (KB)")
        self.file_tree.heading("modified", text="Modified")
        self.file_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Organize actions
        action_frame = ttk.Frame(self.organize_tab)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(action_frame, text="Move Selected", command=self._move_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Copy Selected", command=lambda: self._move_files(copy=True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Rename Selected", command=self._rename_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Delete Selected", command=self._delete_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Bulk Rename...", command=self._bulk_rename_dialog).pack(side=tk.LEFT, padx=2)

        # Status/log area
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.organize_tab, textvariable=self.status_var).pack(fill=tk.X, padx=5, pady=2)

    def _browse_folder(self):
        path = filedialog.askdirectory(mustexist=True)
        if path:
            self.folder_var.set(path)
            self._refresh_file_list()

    def _refresh_file_list(self):
        folder = self.folder_var.get()
        self.file_tree.delete(*self.file_tree.get_children())
        if not folder or not os.path.isdir(folder):
            self.status_var.set("No folder selected or folder does not exist.")
            return
        try:
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath) // 1024
                    mtime = os.path.getmtime(fpath)
                    import datetime
                    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    self.file_tree.insert("", tk.END, values=(fname, size, mtime_str))
            self.status_var.set(f"Listed files in {folder}")
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def _selected_file_paths(self):
        folder = self.folder_var.get()
        items = self.file_tree.selection()
        return [os.path.join(folder, self.file_tree.item(it)["values"][0]) for it in items]

    def _move_files(self, copy=False):
        import shutil
        files = self._selected_file_paths()
        if not files:
            self.status_var.set("No files selected.")
            return
        dest = filedialog.askdirectory()
        if not dest:
            return
        for f in files:
            try:
                if copy:
                    shutil.copy2(f, dest)
                else:
                    shutil.move(f, dest)
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                return
        self.status_var.set(f"{'Copied' if copy else 'Moved'} {len(files)} files to {dest}")
        self._refresh_file_list()

    def _rename_files(self):
        files = self._selected_file_paths()
        if not files:
            self.status_var.set("No files selected.")
            return
        for f in files:
            new_name = simpledialog.askstring("Rename", f"Rename {os.path.basename(f)} to:")
            if new_name:
                try:
                    os.rename(f, os.path.join(os.path.dirname(f), new_name))
                except Exception as e:
                    self.status_var.set(f"Error: {e}")
                    return
        self.status_var.set("Renamed selected files.")
        self._refresh_file_list()

    def _delete_files(self):
        files = self._selected_file_paths()
        if not files:
            self.status_var.set("No files selected.")
            return
        if not messagebox.askyesno("Delete", f"Delete {len(files)} files?"):
            return
        for f in files:
            try:
                os.remove(f)
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                return
        self.status_var.set(f"Deleted {len(files)} files.")
        self._refresh_file_list()

    def _bulk_rename_dialog(self):
        # Placeholder for future bulk rename dialog
        messagebox.showinfo("Bulk Rename", "Bulk rename feature coming soon!")

    # --- Find Duplicates Tab ---
    def _build_duplicates_tab(self):
        # Folder selection
        path_frame = ttk.LabelFrame(self.duplicates_tab, text="Scan Paths")
        path_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox = tk.Listbox(path_frame, selectmode=tk.BROWSE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        btn_frame = ttk.Frame(path_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(btn_frame, text="Add", command=self._add_path).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_sel).pack(fill=tk.X, pady=2)

        opts = ttk.Frame(self.duplicates_tab)
        opts.pack(fill=tk.X, padx=5)
        self.recursive = tk.BooleanVar(value=True)
        self.use_hash = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)
        self.schedule = tk.BooleanVar(value=False)
        self.interval = tk.IntVar(value=24)
        ttk.Checkbutton(opts, text="Scan subdirectories", variable=self.recursive).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Identify duplicates by content", variable=self.use_hash).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Dry run", variable=self.dry_run).pack(side=tk.LEFT)
        ttk.Checkbutton(opts, text="Daily Scan", variable=self.schedule, command=self._toggle_schedule).pack(side=tk.LEFT)
        ttk.Label(opts, text="Interval(h)").pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(opts, from_=1, to=168, width=5, textvariable=self.interval).pack(side=tk.LEFT)

        action_frame = ttk.Frame(self.duplicates_tab)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(action_frame, text="Scan", command=self._start_scan).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Move To...", command=self._move_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Copy To...", command=lambda: self._move_selected(copy=True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)

        self.tree = ttk.Treeview(self.duplicates_tab, columns=("size", "path"), show="headings", selectmode="extended")
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
        self.api.start_thread(target=self._scan)

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

