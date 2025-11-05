import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from utils.file_helpers import find_files_in_folder, create_drop_area
from constants import VALID_EXTENSIONS
from processors.image_processor import process_images

PLUGIN_MANIFEST = {
    "plugin_id": "image",
    "name": "Image Studio",
    "description": "Resize, reformat, and rename large batches of images with intelligent presets.",
    "category": "Imaging",
    "keywords": ("image", "resize", "batch", "optimize"),
    "version": "2.0.0",
    "author": "Multi-Utility Team",
}

logger = logging.getLogger(__name__)


def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("Image", tab)

    resize_options_frame = ttk.LabelFrame(tab, text="Resize Options")
    resize_options_frame.pack(fill=tk.X, pady=5)

    resize_method_var = tk.StringVar(value="none")
    none_rb = ttk.Radiobutton(
        resize_options_frame,
        text="No Resizing",
        variable=resize_method_var,
        value="none",
    )
    percentage_rb = ttk.Radiobutton(
        resize_options_frame,
        text="By Percentage",
        variable=resize_method_var,
        value="percentage",
    )
    fixed_rb = ttk.Radiobutton(
        resize_options_frame,
        text="Fixed Dimensions",
        variable=resize_method_var,
        value="fixed",
    )
    none_rb.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
    percentage_rb.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
    fixed_rb.grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)

    ttk.Label(resize_options_frame, text="Resize %:").grid(
        row=1, column=0, sticky=tk.W, padx=5
    )
    resize_percentage_var = tk.IntVar(value=50)
    percentage_entry = ttk.Entry(
        resize_options_frame, textvariable=resize_percentage_var, width=5
    )
    percentage_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

    ttk.Label(resize_options_frame, text="Width:").grid(
        row=2, column=0, sticky=tk.W, padx=5
    )
    fixed_width_var = tk.IntVar(value=800)
    fixed_width_entry = ttk.Entry(
        resize_options_frame, textvariable=fixed_width_var, width=7
    )
    fixed_width_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

    ttk.Label(resize_options_frame, text="Height:").grid(
        row=3, column=0, sticky=tk.W, padx=5
    )
    fixed_height_var = tk.IntVar(value=600)
    fixed_height_entry = ttk.Entry(
        resize_options_frame, textvariable=fixed_height_var, width=7
    )
    fixed_height_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)

    maintain_aspect_var = tk.BooleanVar(value=False)
    aspect_check = ttk.Checkbutton(
        resize_options_frame, text="Maintain Aspect Ratio", variable=maintain_aspect_var
    )
    aspect_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

    ttk.Label(resize_options_frame, text="Aspect Ratio:").grid(
        row=5, column=0, sticky=tk.W, padx=5
    )
    aspect_choice_var = tk.StringVar(value="Original")
    aspect_options = ["Original", "1:1", "4:3", "16:9", "3:2"]
    aspect_combo = ttk.Combobox(
        resize_options_frame,
        textvariable=aspect_choice_var,
        values=aspect_options,
        state="readonly",
        width=10,
    )
    aspect_combo.grid(row=5, column=1, padx=5, pady=2, sticky=tk.W)

    def toggle_resize_options(*args):
        method = resize_method_var.get()
        if method == "percentage":
            percentage_entry.config(state="normal")
            fixed_width_entry.config(state="disabled")
            fixed_height_entry.config(state="disabled")
            aspect_check.config(state="disabled")
            aspect_combo.config(state="disabled")
        elif method == "fixed":
            percentage_entry.config(state="disabled")
            fixed_width_entry.config(state="normal")
            fixed_height_entry.config(state="normal")
            aspect_check.config(state="normal")
            if maintain_aspect_var.get():
                aspect_combo.config(state="readonly")
            else:
                aspect_combo.config(state="disabled")
        else:
            percentage_entry.config(state="disabled")
            fixed_width_entry.config(state="disabled")
            fixed_height_entry.config(state="disabled")
            aspect_check.config(state="disabled")
            aspect_combo.config(state="disabled")

    resize_method_var.trace("w", toggle_resize_options)
    maintain_aspect_var.trace("w", toggle_resize_options)
    toggle_resize_options()

    opts_frame = ttk.Frame(tab)
    opts_frame.pack(fill=tk.X, pady=5)
    margin_var = tk.BooleanVar(value=False)
    batch_rename_var = tk.BooleanVar(value=False)
    rename_prefix_var = tk.StringVar(value="Picture")
    reformat_var = tk.BooleanVar(value=False)
    new_format_var = tk.StringVar(value="jpg")
    ttk.Checkbutton(opts_frame, text="Add 16px Margin", variable=margin_var).grid(
        row=0, column=0, sticky=tk.W
    )
    ttk.Checkbutton(opts_frame, text="Batch Rename", variable=batch_rename_var).grid(
        row=1, column=0, sticky=tk.W
    )
    ttk.Label(opts_frame, text="Rename Prefix:").grid(row=1, column=1, sticky=tk.W)
    ttk.Entry(opts_frame, textvariable=rename_prefix_var, width=12).grid(
        row=1, column=2, padx=5
    )
    ttk.Checkbutton(opts_frame, text="Reformat Image", variable=reformat_var).grid(
        row=2, column=0, sticky=tk.W
    )
    ttk.Label(opts_frame, text="New Format:").grid(row=2, column=1, sticky=tk.W)
    ttk.Combobox(
        opts_frame,
        textvariable=new_format_var,
        values=["jpg", "png", "bmp", "gif"],
        state="readonly",
        width=5,
    ).grid(row=2, column=2, padx=5)

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    drop_area = create_drop_area(
        drop_frame, plugin_api, text_str="Drag & drop image files/folders here"
    )

    def image_drop_event(e):
        paths = tab.tk.splitlist(e.data)
        image_files = []
        for path in paths:
            if os.path.isdir(path):
                image_files.extend(
                    find_files_in_folder(
                        path, valid_extensions=VALID_EXTENSIONS["IMAGE"]
                    )
                )
            elif path.lower().endswith(VALID_EXTENSIONS["IMAGE"]):
                image_files.append(path)
        if not image_files:
            messagebox.showerror("Error", "No valid image files found.")
            return
        drop_area.set_files(image_files)
        t = threading.Thread(
            target=process_images,
            args=(
                image_files,
                resize_method_var.get(),
                resize_percentage_var.get(),
                fixed_width_var.get(),
                fixed_height_var.get(),
                maintain_aspect_var.get(),
                aspect_choice_var.get(),
                margin_var.get(),
                batch_rename_var.get(),
                rename_prefix_var.get(),
                reformat_var.get(),
                new_format_var.get(),
                plugin_api.app,
            ),
            daemon=True,
        )
        t.start()

    drop_area.dnd_bind("<<Drop>>", image_drop_event)
