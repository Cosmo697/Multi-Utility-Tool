import tkinter as tk
from tkinter import ttk, messagebox
import logging
from queue import Queue, Empty
from ttkthemes import ThemedStyle
from tkinterdnd2 import TkinterDnD
from core.hooks import Hooks
from core.plugin_api import PluginAPI
from utils.logging_config import setup_logging
from utils.diagnostics import get_usage_stats

logger = logging.getLogger(__name__)

class AppCore:
    def __init__(self, root):
        self.root = root
        setup_logging()
        logger.info("Logging setup complete.")
        self.queue = Queue()
        self.hooks = Hooks()
        self.plugin_api = PluginAPI(self)
        self.setup_ui()
        self.process_queue()

    def setup_ui(self):
        self.root.title("Multi-Utility Tool with Plugins")
        self.root.geometry("900x600")
        self.setup_menu()
        self.setup_tabs()
        self.setup_status_bar()

    def setup_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Logs", command=self.open_logs_window)
        file_menu.add_command(label="Usage Stats", command=self.show_stats)
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def setup_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')
        self.plugin_tabs = {}

    def add_plugin_tab(self, title, frame):
        self.notebook.add(frame, text=title)
        self.plugin_tabs[title] = frame

    def setup_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=200,
                                             mode="determinate", variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def open_logs_window(self):
        logs_win = tk.Toplevel(self.root)
        logs_win.title("Logs")
        logs_win.geometry("600x400")
        text_area = tk.Text(logs_win, wrap='word', state=tk.DISABLED, bg="#222", fg="#eee")
        text_area.pack(expand=True, fill='both')
        handler = TextWidgetHandler(text_area)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logger.info("Opened logs window.")

    def show_stats(self):
        stats = get_usage_stats()
        msg = "\n".join(f"{k}: {v}" for k, v in stats.items()) or "No stats yet."
        messagebox.showinfo("Usage Stats", msg)

    def show_about(self):
        messagebox.showinfo("About", "Multi-Utility Tool with Plugin Support\nVersion 1.0\n© 2023")

    def update_status(self, message):
        self.status_var.set(message)
        logger.info(message)

    def set_progress(self, percent):
        self.progress_var.set(percent)

    def start_progress(self):
        self.progress_var.set(0.0)

    def stop_progress(self):
        self.progress_var.set(0.0)

    def process_queue(self):
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
        except Empty:
            pass
        self.root.after(50, self.process_queue)

    def increment_progress(self, current, total):
        if total > 0:
            pct = (current / total) * 100
            self.queue.put((None, "progress", pct))

# Logging handler for Tkinter text widget
import logging
class TextWidgetHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record) + "\n"
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg)
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)
