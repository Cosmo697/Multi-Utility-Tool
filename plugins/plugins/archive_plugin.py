"""Simple archive creation and extraction plugin."""

import threading
import tkinter as tk
from tkinter import ttk, filedialog

from processors.archive_processor import process_archives
from utils.file_helpers import create_drop_area


def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("Archive", tab)

    action_var = tk.StringVar(value="compress")
    ttk.Radiobutton(tab, text="Compress", variable=action_var, value="compress").grid(row=0, column=0, sticky=tk.W, padx=5)
    ttk.Radiobutton(tab, text="Extract", variable=action_var, value="extract").grid(row=0, column=1, sticky=tk.W, padx=5)

    name_var = tk.StringVar(value="archive")
    ttk.Label(tab, text="Output Name/Folder:").grid(row=1, column=0, sticky=tk.W, padx=5)
    name_entry = ttk.Entry(tab, textvariable=name_var, width=20)
    name_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

    browse_var = tk.StringVar(value="")

    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            browse_var.set(folder)

    browse_button = ttk.Button(tab, text="Select Folder", command=browse_folder)
    browse_button.grid(row=1, column=2, padx=5)

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    tab.columnconfigure(1, weight=1)
    drop_area = create_drop_area(drop_frame, text_str="Drag & drop files/folders here")

    def handle_drop(event):
        paths = tab.tk.splitlist(event.data)
        if not paths:
            return
        action = action_var.get()
        output = browse_var.get() if action == "extract" else name_var.get().strip() or "archive"
        threading.Thread(
            target=process_archives,
            args=(paths, action, output, plugin_api.app),
            daemon=True,
        ).start()

    drop_area.dnd_bind("<<Drop>>", handle_drop)

