import tkinter as tk
from tkinter import ttk, messagebox
import logging
from queue import Queue, Empty
from ttkthemes import ThemedStyle
from tkinterdnd2 import TkinterDnD
from utils.diagnostics import get_usage_stats

logger = logging.getLogger(__name__)


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

    def __init__(self, app) -> None:
        self.app = app
        self.root = TkinterDnD.Tk()
        self.style = ThemedStyle(self.root)
        try:
            self.style.set_theme("equilux")
        except Exception:
            self.style.set_theme("arc")
        self.root.configure(background="#2e2e2e")
        self.style.configure(
            ".", background="#2e2e2e", foreground="#d3d3d3", font=("Segoe UI", 10)
        )
        self.style.configure("TFrame", background="#2e2e2e")
        self.style.configure("TLabel", background="#2e2e2e", foreground="#d3d3d3")
        self.style.configure("TButton", background="#3e3e3e", foreground="#d3d3d3")
        self.style.configure("TNotebook", background="#2e2e2e")
        self.style.configure(
            "TNotebook.Tab", background="#3e3e3e", foreground="#d3d3d3"
        )
        # Hide tab bar for a cleaner look; navigation handled by sidebar
        self.style.layout("TNotebook.Tab", [])

        self.queue: Queue = Queue()
        self.plugin_tabs: dict[str, tk.Frame] = {}
        self.setup_tabs()
        self.setup_status_bar()

    # Called after other agents exist
    def attach(self) -> None:
        self.setup_menu()
        self.process_queue()
        self.root.bind("<Unmap>", self._on_minimize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def setup_tabs(self) -> None:
        container = ttk.Frame(self.root)
        container.pack(expand=True, fill="both")
        self.sidebar = tk.Listbox(container, exportselection=False, width=20)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.bind("<<ListboxSelect>>", self._on_plugin_select)
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(side=tk.RIGHT, expand=True, fill="both")

    def add_plugin_tab(self, title: str, frame: tk.Frame) -> None:
        self.notebook.add(frame, text=title)
        self.sidebar.insert(tk.END, title)
        self.plugin_tabs[title] = frame

    def _on_plugin_select(self, event=None) -> None:
        idx = self.sidebar.curselection()
        if not idx:
            return
        self.notebook.select(idx[0])

    def setup_menu(self) -> None:
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Logs", command=self.open_logs_window)
        file_menu.add_command(label="Usage Stats", command=self.show_stats)
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(
            label="Hotkey Manager", command=self.app.hotkeys.open_manager
        )
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def setup_status_bar(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            length=200,
            mode="determinate",
            variable=self.progress_var,
            maximum=100,
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def open_logs_window(self) -> None:
        logs_win = tk.Toplevel(self.root)
        logs_win.title("Logs")
        logs_win.geometry("600x400")
        text_area = tk.Text(
            logs_win, wrap="word", state=tk.DISABLED, bg="#222", fg="#eee"
        )
        text_area.pack(expand=True, fill="both")
        handler = TextWidgetHandler(text_area)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logger.info("Opened logs window.")

    def show_stats(self) -> None:
        stats = get_usage_stats()
        msg = "\n".join(f"{k}: {v}" for k, v in stats.items()) or "No stats yet."
        messagebox.showinfo("Usage Stats", msg)

    def show_about(self) -> None:
        messagebox.showinfo(
            "About", "Multi-Utility Tool with Plugin Support\nVersion 1.0\n© 2023"
        )

    def show_error(self, message: str) -> None:
        messagebox.showerror("Error", message)
        logger.error(message)

    def update_status(self, message: str) -> None:
        self.status_var.set(message)
        logger.info(message)

    def set_progress(self, percent: float) -> None:
        self.progress_var.set(percent)

    def start_progress(self) -> None:
        self.progress_var.set(0.0)

    def stop_progress(self) -> None:
        self.progress_var.set(0.0)

    def process_queue(self) -> None:
        try:
            while True:
                file_path, msg_type, payload = self.queue.get_nowait()
                if msg_type == "status":
                    self.update_status(payload)
                elif msg_type == "progress":
                    self.set_progress(payload)
                elif msg_type == "done":
                    self.stop_progress()
                    self.update_status(payload)
                    self.app.tray.notify(payload)
                elif msg_type == "error":
                    self.show_error(payload)
        except Empty:
            pass
        self.root.after(50, self.process_queue)

    def increment_progress(self, current: int, total: int) -> None:
        if total > 0:
            pct = (current / total) * 100
            self.queue.put((None, "progress", pct))

    def _on_minimize(self, event=None):
        if self.root.state() == "iconic":
            self.root.withdraw()
            self.app.tray.show()

    def _on_close(self) -> None:
        # Gracefully stop any running worker threads
        for t in getattr(self.app, "threads", []):
            if t.is_alive():
                t.join(timeout=1)
        if getattr(self.app.tray, "icon", None):
            self.app.tray.icon.stop()
        self.root.destroy()
