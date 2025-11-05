"""PDF merging and splitting plugin."""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from processors.pdf_processor import merge_pdfs, split_pdf
from utils.file_helpers import create_drop_area

PLUGIN_MANIFEST = {
    "plugin_id": "pdf-tools",
    "name": "PDF Studio",
    "description": "Merge and split PDF documents with range presets and drag-and-drop input.",
    "category": "Documents",
    "keywords": ("pdf", "merge", "split"),
    "version": "2.0.0",
    "author": "Multi-Utility Team",
}


def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("PDF Tools", tab)

    action_var = tk.StringVar(value="merge")
    ttk.Radiobutton(tab, text="Merge", variable=action_var, value="merge").grid(
        row=0, column=0, sticky=tk.W, padx=5
    )
    ttk.Radiobutton(tab, text="Split", variable=action_var, value="split").grid(
        row=0, column=1, sticky=tk.W, padx=5
    )

    name_var = tk.StringVar(value="output")
    ttk.Label(tab, text="Output Name:").grid(row=1, column=0, sticky=tk.W, padx=5)
    name_entry = ttk.Entry(tab, textvariable=name_var, width=20)
    name_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

    start_var = tk.IntVar(value=1)
    end_var = tk.IntVar(value=1)
    ttk.Label(tab, text="Start Page:").grid(row=2, column=0, sticky=tk.W, padx=5)
    ttk.Entry(tab, textvariable=start_var, width=5).grid(row=2, column=1, sticky=tk.W)
    ttk.Label(tab, text="End Page:").grid(row=3, column=0, sticky=tk.W, padx=5)
    ttk.Entry(tab, textvariable=end_var, width=5).grid(row=3, column=1, sticky=tk.W)

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
    tab.columnconfigure(1, weight=1)
    drop_area = create_drop_area(
        drop_frame, plugin_api, text_str="Drag & drop PDF files here"
    )

    def handle_drop(event):
        paths = tab.tk.splitlist(event.data)
        pdf_files = [p for p in paths if p.lower().endswith(".pdf")]
        if not pdf_files:
            messagebox.showerror("Error", "No PDF files provided.")
            return
        drop_area.set_files(pdf_files)
        if action_var.get() == "merge":
            threading.Thread(
                target=merge_pdfs,
                args=(pdf_files, name_var.get().strip() or "output", plugin_api.app),
                daemon=True,
            ).start()
        else:
            # use first file for split
            threading.Thread(
                target=split_pdf,
                args=(pdf_files[0], start_var.get(), end_var.get(), plugin_api.app),
                daemon=True,
            ).start()

    drop_area.dnd_bind("<<Drop>>", handle_drop)
