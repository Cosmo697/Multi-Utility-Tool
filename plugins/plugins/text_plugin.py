import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import markdown
import json
import csv
import yaml
from utils.file_helpers import create_drop_area, find_files_in_folder, read_file_content
from constants import VALID_EXTENSIONS
from processors.text_processor import process_text_files

logger = logging.getLogger(__name__)

def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("Text", tab)

    merge_var = tk.BooleanVar(value=False)
    deduplicate_var = tk.BooleanVar(value=False)
    find_var = tk.StringVar(value="")
    replace_var = tk.StringVar(value="")
    convert_md_var = tk.BooleanVar(value=False)
    freq_stats_var = tk.BooleanVar(value=False)

    opts_frame = ttk.Frame(tab)
    opts_frame.pack(fill=tk.X, pady=5)
    ttk.Checkbutton(opts_frame, text="Merge Files", variable=merge_var).grid(row=0, column=0, sticky=tk.W)
    ttk.Checkbutton(opts_frame, text="Deduplicate Words", variable=deduplicate_var).grid(row=0, column=1, sticky=tk.W)
    ttk.Label(opts_frame, text="Find:").grid(row=1, column=0, sticky=tk.E)
    ttk.Entry(opts_frame, textvariable=find_var, width=15).grid(row=1, column=1, padx=5)
    ttk.Label(opts_frame, text="Replace:").grid(row=2, column=0, sticky=tk.E)
    ttk.Entry(opts_frame, textvariable=replace_var, width=15).grid(row=2, column=1, padx=5)
    ttk.Checkbutton(opts_frame, text="Convert MD to HTML/PDF", variable=convert_md_var).grid(row=3, column=0, sticky=tk.W)
    ttk.Checkbutton(opts_frame, text="Word Freq & Stats (WordCloud)", variable=freq_stats_var).grid(row=3, column=1, sticky=tk.W)

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    drop_area = create_drop_area(drop_frame, text_str="Drag & drop text files/folders here")

    def text_drop_event(e):
        paths = tab.tk.splitlist(e.data)
        text_files = []
        for path in paths:
            if os.path.isdir(path):
                text_files.extend(find_files_in_folder(path, valid_extensions=VALID_EXTENSIONS["TEXT"]))
            elif path.lower().endswith(VALID_EXTENSIONS["TEXT"]):
                text_files.append(path)
        if not text_files:
            messagebox.showerror("Error", "No valid text files found.")
            return
        t = threading.Thread(
            target=process_text_files,
            args=(text_files, merge_var.get(), deduplicate_var.get(),
                  find_var.get(), replace_var.get(),
                  convert_md_var.get(), freq_stats_var.get(), plugin_api.app),
            daemon=True
        )
        t.start()

    drop_area.dnd_bind('<<Drop>>', text_drop_event)

    def open_file():
        file_path = filedialog.askopenfilename(filetypes=[
            ("Text files", "*.txt"),
            ("Markdown files", "*.md"),
            ("Rich Text Format", "*.rtf"),
            ("HTML files", "*.html;*.htm"),
            ("XML files", "*.xml"),
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"),
            ("YAML files", "*.yaml;*.yml"),
            ("Word files", "*.docx"),
            ("PDF files", "*.pdf"),
            ("Python files", "*.py"),
            ("All files", "*.*")
        ])
        if not file_path:
            return
        try:
            content = read_file_content(file_path)
            display_content(content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

    def display_content(content):
        preview_win = tk.Toplevel(tab)
        preview_win.title("File Preview")
        preview_win.geometry("600x400")
        text_widget = tk.Text(preview_win, wrap='word')
        text_widget.pack(expand=True, fill='both')
        text_widget.insert(tk.END, content)

    ttk.Button(tab, text="Open File", command=open_file).pack(pady=5)
