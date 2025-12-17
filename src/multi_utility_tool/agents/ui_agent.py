"""User interface agent responsible for layout, theming, and feedback."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
from queue import Queue, Empty
from typing import Dict

try:  # pragma: no cover - optional dependency
    from tkinterdnd2 import TkinterDnD
except ImportError:  # pragma: no cover
    TkinterDnD = None

from ..core.plugin_manifest import PluginManifest

logger = logging.getLogger(__name__)


class _HeadlessRoot:
    """Minimal stub used when the UI runs in headless mode."""

    def __init__(self) -> None:
        self._after_callbacks = []

    def after(self, *_args, **_kwargs):  # pragma: no cover - simple stub
        return None

    def bind(self, *_args, **_kwargs) -> None:  # pragma: no cover - stub
        return None

    def protocol(self, *_args, **_kwargs) -> None:  # pragma: no cover - stub
        return None

    def withdraw(self) -> None:  # pragma: no cover - stub
        return None

    def deiconify(self) -> None:  # pragma: no cover - stub
        return None

    def destroy(self) -> None:  # pragma: no cover - stub
        return None

    def quit(self) -> None:  # pragma: no cover - stub
        return None

    def mainloop(self) -> None:  # pragma: no cover - stub
        return None

    def state(self):  # pragma: no cover - stub
        return "normal"


class TextWidgetHandler(logging.Handler):
    """Logging handler that writes to a Tkinter text widget."""

    def __init__(self, text_widget) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record) -> None:
        msg = self.format(record) + "\n"
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg)
        self.text_widget.configure(state="disabled")
        self.text_widget.yview(tk.END)


class UIAgent:
    """Manage the Tkinter UI components."""

    def __init__(self, app, headless: bool = False) -> None:
        self.app = app
        self.headless = headless
        self.queue: Queue = Queue()
        self.plugin_tabs: Dict[str, tk.Frame] = {}
        self.plugin_manifests: Dict[str, PluginManifest] = {}
        self._nav_items: list[str] = []
        self._nav_filter: str = ""

        if headless:
            self.root = _HeadlessRoot()
            self.notebook = None
            return

        if TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
        else:
            logger.warning("tkinterdnd2 not available; drag-and-drop disabled")
            self.root = tk.Tk()
        self.root.title("Multi-Utility Tool")
        self.root.geometry("1320x860")
        self.root.minsize(1100, 720)
        self.style = ttk.Style(self.root)
        self._configure_theme()
        self._build_layout()

    # ------------------------------------------------------------------ UI setup
    def _configure_theme(self) -> None:
        self.style.theme_use("clam")
        dark_bg = "#1f1f28"
        light_bg = "#2b2b36"
        accent = "#4c8bf5"
        fg = "#e2e2e2"
        self.root.configure(background=dark_bg)
        self.style.configure("TFrame", background=dark_bg, foreground=fg)
        self.style.configure("TLabelframe", background=light_bg, foreground=fg)
        self.style.configure(
            "TLabelframe.Label", background=light_bg, foreground=fg, font=("Segoe UI", 10, "bold")
        )
        self.style.configure("TLabel", background=dark_bg, foreground=fg, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#ffffff")
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#ffffff",
            background=accent,
            padding=(12, 6),
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#3b6ccf"), ("pressed", "#2c4e9c")],
            relief=[("pressed", "sunken"), ("!pressed", "raised")],
        )
        self.style.configure("Plugin.TFrame", background=light_bg)
        self.style.configure("Status.TLabel", foreground="#a0a0a0")
        self.style.configure("Toast.TLabel", background="#3b3b3b", foreground="#ffffff")
        self.style.configure("Treeview", fieldbackground=light_bg, background=light_bg, foreground=fg)
        self.style.map("Treeview", background=[("selected", accent)])
        self.style.configure("TNotebook", background=light_bg, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(12, 8), font=("Segoe UI", 10))

    def _build_layout(self) -> None:
        self.main = ttk.Frame(self.root, padding=(18, 14, 18, 18))
        self.main.pack(fill="both", expand=True)

        self._build_header()
        self._build_body()
        self._build_status_bar()

    def _build_header(self) -> None:
        header = ttk.Frame(self.main)
        header.pack(fill="x")
        title = ttk.Label(header, text="Multi-Utility Tool", style="Header.TLabel")
        title.pack(side=tk.LEFT)
        subtitle = ttk.Label(
            header,
            text="Streamlined multi-tool workspace with plugin intelligence",
            style="Status.TLabel",
        )
        subtitle.pack(side=tk.LEFT, padx=(12, 0))

        search_container = ttk.Frame(header)
        search_container.pack(side=tk.RIGHT)
        ttk.Label(search_container, text="Search plugins:").pack(side=tk.LEFT, padx=(0, 6))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_container, textvariable=self.search_var, width=32)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind("<KeyRelease>", self._filter_nav)
        ttk.Button(
            search_container,
            text="Clear",
            command=self._clear_filter,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _build_body(self) -> None:
        body = ttk.Frame(self.main)
        body.pack(fill="both", expand=True, pady=(12, 0))

        self.nav_frame = ttk.Frame(body, width=260)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_tree = ttk.Treeview(
            self.nav_frame,
            columns=("category",),
            show="tree",
            selectmode="browse",
            height=20,
        )
        self.nav_tree.column("#0", width=200, stretch=True)
        self.nav_tree.column("category", width=120, stretch=True)
        self.nav_tree.pack(fill=tk.BOTH, expand=True)
        self.nav_tree.bind("<<TreeviewSelect>>", self._on_nav_select)

        nav_buttons = ttk.Frame(self.nav_frame)
        nav_buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(nav_buttons, text="Open Logs", command=self.open_logs_window).pack(
            side=tk.LEFT, expand=True, fill=tk.X
        )
        ttk.Button(nav_buttons, text="Usage Stats", command=self.show_stats).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0)
        )

        content_frame = ttk.Frame(body, style="Plugin.TFrame")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(18, 0))

        self.toast_var = tk.StringVar(value="")
        self.toast_label = ttk.Label(content_frame, textvariable=self.toast_var, style="Toast.TLabel")
        self.toast_label.pack(fill=tk.X)
        self.toast_label.pack_forget()

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._sync_nav_selection)

        info = ttk.Frame(content_frame, style="Plugin.TFrame")
        info.pack(fill=tk.X, pady=(12, 0))
        self.info_title = ttk.Label(info, text="Select a plugin to view details", font=("Segoe UI", 12, "bold"))
        self.info_title.pack(anchor=tk.W)
        self.info_body = ttk.Label(info, text="", style="Status.TLabel", wraplength=640, justify=tk.LEFT)
        self.info_body.pack(anchor=tk.W, pady=(4, 0))

        log_frame = ttk.Labelframe(content_frame, text="Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.log_widget = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            state=tk.DISABLED,
            background="#242430",
            foreground="#e4e4e4",
            font=("Consolas", 10),
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _build_status_bar(self) -> None:
        status_frame = ttk.Frame(self.main)
        status_frame.pack(fill=tk.X, pady=(12, 0))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(
            side=tk.LEFT
        )
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            length=240,
            mode="determinate",
            variable=self.progress_var,
            maximum=100,
        )
        self.progress_bar.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------ lifecycle
    def attach(self) -> None:
        if self.headless:
            return
        self.setup_menu()
        self.process_queue()
        self.root.bind("<Unmap>", self._on_minimize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def setup_menu(self) -> None:
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Logs", command=self.open_logs_window)
        file_menu.add_command(label="Usage Stats", command=self.show_stats)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(
            label="Hotkey Manager", command=getattr(self.app.hotkeys, "open_manager", lambda: None)
        )
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

    # ------------------------------------------------------------------ plugin management
    def add_plugin_tab(self, manifest: PluginManifest, frame: tk.Frame) -> None:
        self.plugin_tabs[manifest.plugin_id] = frame
        self.plugin_manifests[manifest.plugin_id] = manifest
        self._nav_items.append(manifest.plugin_id)
        if self.headless:
            return
        self.notebook.add(frame, text=manifest.name)
        self.nav_tree.insert("", tk.END, iid=manifest.plugin_id, text=manifest.name)
        if len(self._nav_items) == 1:
            self._show_plugin(manifest.plugin_id)
        self._update_manifest_info(manifest)

    def _show_plugin(self, plugin_id: str) -> None:
        if self.headless:
            return
        frame = self.plugin_tabs.get(plugin_id)
        if frame is None:
            return
        self.notebook.select(frame)
        manifest = self.plugin_manifests.get(plugin_id)
        if manifest:
            self._update_manifest_info(manifest)
            self.toast_var.set("")
            self.toast_label.pack_forget()

    def _update_manifest_info(self, manifest: PluginManifest) -> None:
        self.info_title.configure(text=f"{manifest.name} · v{manifest.version} · {manifest.author}")
        details = f"Category: {manifest.category}\nKeywords: {', '.join(manifest.keywords) or 'none'}\n{manifest.description}"
        self.info_body.configure(text=details)

    def _on_nav_select(self, event) -> None:
        selected = self.nav_tree.selection()
        if not selected:
            return
        plugin_id = selected[0]
        self._show_plugin(plugin_id)

    def _sync_nav_selection(self, event=None) -> None:
        if self.headless:
            return
        current = self.notebook.select()
        for plugin_id, frame in self.plugin_tabs.items():
            if str(frame) == current:
                self.nav_tree.selection_set(plugin_id)
                self.nav_tree.see(plugin_id)
                manifest = self.plugin_manifests.get(plugin_id)
                if manifest:
                    self._update_manifest_info(manifest)
                break

    def _filter_nav(self, event=None) -> None:
        self._nav_filter = self.search_var.get().lower().strip()
        self.nav_tree.delete(*self.nav_tree.get_children(""))
        for plugin_id in self._nav_items:
            manifest = self.plugin_manifests.get(plugin_id)
            if not manifest:
                continue
            if not self._nav_filter or self._nav_filter in manifest.search_blob:
                self.nav_tree.insert("", tk.END, iid=plugin_id, text=manifest.name)
        if not self.nav_tree.get_children(""):
            self.toast_var.set("No plugins match your search.")
            self.toast_label.pack(fill=tk.X)
        else:
            self.toast_var.set("")
            self.toast_label.pack_forget()

    def _clear_filter(self) -> None:
        self.search_var.set("")
        self._filter_nav()

    # ------------------------------------------------------------------ status & feedback
    def open_logs_window(self) -> None:
        if self.headless:
            return
        logs_win = tk.Toplevel(self.root)
        logs_win.title("Logs")
        logs_win.geometry("720x480")
        text_area = scrolledtext.ScrolledText(
            logs_win,
            wrap="word",
            state=tk.DISABLED,
            bg="#222",
            fg="#eee",
            font=("Consolas", 10),
        )
        text_area.pack(expand=True, fill="both")
        handler = TextWidgetHandler(text_area)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logger.info("Opened logs window.")

    def show_stats(self) -> None:
        from ..utils.diagnostics import get_usage_stats

        stats = get_usage_stats()
        msg = "\n".join(f"{k}: {v}" for k, v in stats.items()) or "No stats yet."
        if self.headless:
            logger.info("Usage stats: %s", msg)
            return
        messagebox.showinfo("Usage Stats", msg)

    def show_about(self) -> None:
        if self.headless:
            return
        messagebox.showinfo(
            "About",
            "Multi-Utility Tool\nComplete productivity suite for creators",
        )

    def update_status(self, message: str) -> None:
        self.status_var.set(message)
        logger.info(message)
        self._append_log(message)

    def set_progress(self, percent: float) -> None:
        self.progress_var.set(max(0.0, min(100.0, percent)))

    def start_progress(self) -> None:
        self.progress_var.set(0.0)

    def stop_progress(self) -> None:
        self.progress_var.set(0.0)

    def process_queue(self) -> None:
        if self.headless:
            self._drain_queue_headless()
            return
        try:
            while True:
                _source, msg_type, payload = self.queue.get_nowait()
                if msg_type == "status":
                    self.update_status(payload)
                elif msg_type == "progress":
                    self.set_progress(payload)
                elif msg_type == "done":
                    self.stop_progress()
                    self.update_status(payload)
                    if hasattr(self.app.tray, "notify"):
                        self.app.tray.notify(payload)
                elif msg_type == "error":
                    self._show_error(payload)
                elif msg_type == "toast":
                    self._show_toast(payload)
                elif msg_type == "log":
                    self._append_log(payload)
        except Empty:
            pass
        self.root.after(80, self.process_queue)

    def _drain_queue_headless(self) -> None:
        try:
            while True:
                _source, msg_type, payload = self.queue.get_nowait()
                if msg_type in {"status", "done", "log", "error"}:
                    logger.info("[HEADLESS] %s: %s", msg_type.upper(), payload)
        except Empty:
            pass

    def _append_log(self, message: str) -> None:
        if self.headless:
            logger.debug(message)
            return
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.configure(state=tk.DISABLED)
        self.log_widget.yview(tk.END)

    def _show_error(self, message: str) -> None:
        logger.error(message)
        if self.headless:
            return
        messagebox.showerror("Error", message)

    def _show_toast(self, message: str) -> None:
        if self.headless:
            return
        self.toast_var.set(message)
        self.toast_label.pack(fill=tk.X)
        self.root.after(4000, self.toast_label.pack_forget)

    def increment_progress(self, current: int, total: int) -> None:
        if total > 0:
            pct = (current / total) * 100
            self.queue.put((None, "progress", pct))

    def _on_minimize(self, event=None):
        if self.headless:
            return
        if self.root.state() == "iconic":
            self.root.withdraw()
            if hasattr(self.app.tray, "show"):
                self.app.tray.show()

    def _on_close(self) -> None:
        if hasattr(self.app, "shutdown"):
            self.app.shutdown()
        if hasattr(self.app.tray, "icon") and hasattr(self.app.tray.icon, "stop"):
            try:
                self.app.tray.icon.stop()
            except Exception:  # pragma: no cover - best effort
                logger.debug("Tray stop error", exc_info=True)
        if not self.headless:
            self.root.destroy()
