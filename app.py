import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD
from ttkthemes import ThemedStyle
from queue import Queue, Empty
import threading
import time
import logging

# Tab setup imports (Option A: match the actual function names in each tab file)
from tabs.audio_tab import setup_audio_tab
from tabs.image_tab import setup_image_tab
from tabs.text_tab import setup_text_tab
from tabs.video_tab import setup_video_tab

AVAILABLE_THEMES = [
    "arc", "black", "blue", "clam", "clearlooks", "elegance", "equilux", "keramik",
    "kroc", "plastik", "radiance", "scidblue", "scidgreen", "scidgrey", "scidpink",
    "scidpurple", "vista", "xpnative"
]

def on_closing(root):
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

class TextLogHandler(logging.Handler):
    """
    A logging handler that writes log messages into a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record) + "\n"
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg)
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Utility Application")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Use ttkthemes
        self.style = ThemedStyle(root)
        self.style.set_theme("black")  # default theme

        # 1) Real Menu Bar
        self.menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(self.menubar, tearoff=False)
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=lambda: on_closing(self.root))
        self.menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(self.menubar, tearoff=False)
        view_menu.add_command(label="Logs", command=self.open_logs_window)
        self.menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self.menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar)

        # Header (just a title bar)
        self.header_frame = ttk.Frame(self.root)
        self.header_frame.pack(side="top", fill="x")

        self.header_label = ttk.Label(
            self.header_frame,
            text="My Multi-Utility Application",
            font=('Segoe UI', 14, 'bold')
        )
        self.header_label.pack(side="left", padx=20, pady=10)

        # Main Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Create frames for each tab
        self.audio_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.text_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)

        # Add tabs
        self.notebook.add(self.audio_tab, text='Audio')
        self.notebook.add(self.image_tab, text='Images')
        self.notebook.add(self.text_tab, text='Text')
        self.notebook.add(self.video_tab, text='Video')

        # Setup tab contents
        try:
            setup_audio_tab(self.audio_tab, self)
        except Exception as e:
            self.update_status(f"Audio tab error: {e}")

        try:
            setup_image_tab(self.image_tab, self)
        except Exception as e:
            self.update_status(f"Image tab error: {e}")

        try:
            setup_text_tab(self.text_tab, self)
        except Exception as e:
            self.update_status(f"Text tab error: {e}")

        try:
            setup_video_tab(self.video_tab, self)
        except Exception as e:
            self.update_status(f"Video tab error: {e}")

        # Footer
        self.footer_frame = ttk.Frame(self.root)
        self.footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(
            self.footer_frame, 
            orient='horizontal', 
            mode='determinate', 
            length=400
        )
        self.progress_bar.pack(side="left", padx=10)

        self.status_label = ttk.Label(self.footer_frame, text="Ready")
        self.status_label.pack(side="right", padx=10)

        self.queue = Queue()
        self.root.protocol("WM_DELETE_WINDOW", lambda: on_closing(self.root))
        self.root.after(100, self.process_queue)

        # Logging
        self.log_stream = None
        self.text_log_handler = None
        self.init_logging()

    def init_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        # Remove existing handlers
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        logger.debug("Logging initialized.")

    def process_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                self.update_status(msg[1])
                # If you prefer to only stop progress after all tasks, do so after the loop
                self.stop_progress()
        except Empty:
            self.root.after(100, self.process_queue)

    def set_progress_total(self, total_files):
        """Set progress bar to a determinate mode with a maximum."""
        self.progress_bar.config(mode='determinate', maximum=total_files, value=0)

    def increment_progress(self):
        """Increment progress bar by 1."""
        self.progress_bar['value'] += 1

    def start_progress(self):
        """Fallback for indefinite tasks if needed."""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()

    def stop_progress(self):
        self.progress_bar.stop()

    def update_status(self, message):
        self.status_label.config(text=message)
        logging.debug(f"Status updated: {message}")

    def open_settings(self):
        """Open the Settings dialog with an instant theme preview."""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("300x140")

        ttk.Label(settings_win, text="Select Theme:").pack(pady=(10,0))

        theme_var = tk.StringVar(value=self.style.theme)

        def on_theme_select(event):
            hovered = combo.get()
            if hovered in AVAILABLE_THEMES:
                self.style.set_theme(hovered)

        combo = ttk.Combobox(
            settings_win, 
            textvariable=theme_var, 
            values=AVAILABLE_THEMES, 
            state="readonly"
        )
        combo.pack(pady=5)
        combo.bind("<<ComboboxSelected>>", on_theme_select)

        def close_settings():
            settings_win.destroy()

        ttk.Button(settings_win, text="Close", command=close_settings).pack(pady=5)

    def open_logs_window(self):
        logs_win = tk.Toplevel(self.root)
        logs_win.title("Application Logs")
        logs_win.geometry("600x400")

        text_area = tk.Text(logs_win, wrap='word', state=tk.DISABLED, bg="#222", fg="#eee")
        text_area.pack(expand=True, fill='both')

        if not self.text_log_handler:
            self.text_log_handler = TextLogHandler(text_area)
            self.text_log_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')
            self.text_log_handler.setFormatter(formatter)
            logging.getLogger().addHandler(self.text_log_handler)

        logging.info("Opened logs window.")

    def show_about(self):
        messagebox.showinfo("About", "Multi-Utility Application\nVersion 1.0\n© 2023")

    def start_long_task(self):
        threading.Thread(target=self.long_task, daemon=True).start()

    def long_task(self):
        self.update_status("Processing...")
        self.start_progress()
        time.sleep(2)
        self.stop_progress()
        self.update_status("Done")

if __name__ == "__main__":
    print("Launching application via batch file...")  # Debug print
    root = TkinterDnD.Tk()
    app = App(root)
    root.mainloop()
    print("Application closed.")
