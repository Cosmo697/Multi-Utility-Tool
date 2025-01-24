# tabs/image_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageEnhance, ImageOps
import threading
from queue import Empty
from tkinterdnd2 import DND_FILES
import logging

from utils.helpers import ensure_output_dir, update_status_label, find_files_in_folder, generate_unique_file_path

logger = logging.getLogger(__name__)

def setup_image_tab(tab, app):
    try:
        logger.info("Setting up Image tab.")
        
        ttk.Label(tab, text="Drag and drop images or folders here for processing.").pack(pady=10)
        
        # Resize Options
        ttk.Label(tab, text="Resize Options:").pack()
        resolution_var = tk.StringVar(value="1024x1024")
        resolutions = ["1024x1024", "768x768", "512x512"]
        for res in resolutions:
            ttk.Radiobutton(tab, text=res, variable=resolution_var, value=res).pack()

        add_margin = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Add 16-pixel margin", variable=add_margin).pack()

        # Original features done above. Now new ones:
        batch_rename_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Batch Rename", variable=batch_rename_var).pack(pady=5)
        rename_prefix_var = tk.StringVar(value="Picture")
        ttk.Label(tab, text="Rename Prefix:").pack()
        ttk.Entry(tab, textvariable=rename_prefix_var).pack()

        reformat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Reformat Image", variable=reformat_var).pack()
        # Choose new format
        new_format_var = tk.StringVar(value="jpg")
        ttk.Label(tab, text="New Format:").pack()
        ttk.Combobox(tab, textvariable=new_format_var, values=["jpg","jpeg","png","bmp","webp"], state="readonly").pack()

        # Quality / Compression
        ttk.Label(tab, text="Quality / Compression (1-100):").pack()
        compression_var = tk.IntVar(value=85)
        ttk.Spinbox(tab, from_=1, to=100, textvariable=compression_var, width=5).pack()

        auto_rotate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Auto-Rotate (EXIF)", variable=auto_rotate_var).pack(pady=5)

        drop_area = create_drop_area(tab)
        drop_area.dnd_bind('<<Drop>>', lambda e: handle_image_drop(
            e, app, resolution_var, add_margin,
            batch_rename_var, rename_prefix_var,
            reformat_var, new_format_var, compression_var,
            auto_rotate_var
        ))
        logger.info("Image tab setup complete.")
    except Exception as e:
        logger.error(f"Error setting up Image tab: {e}")
        raise

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your image files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_image_drop(event, app, resolution_var, add_margin,
                      batch_rename_var, rename_prefix_var,
                      reformat_var, new_format_var, compression_var,
                      auto_rotate_var):
    try:
        logger.info("Handling dropped image files.")
        paths = app.root.tk.splitlist(event.data)
        image_files = []
        for path in paths:
            if os.path.isdir(path):
                image_files.extend(find_files_in_folder(path, valid_extensions=[".jpg",".jpeg",".png",".bmp",".webp",".tiff"]))
            elif os.path.isfile(path) and path.lower().endswith((".jpg",".jpeg",".png",".bmp",".webp",".tiff")):
                image_files.append(path)

        if not image_files:
            messagebox.showerror("Error", "No valid image files were found.")
            logger.warning("No valid image files found during drop event.")
            return

        app.start_progress()
        app.update_status("Processing image files...")
        logger.info(f"Starting processing for dropped files: {image_files}")
        t = threading.Thread(
            target=process_dropped_files,
            args=(image_files, resolution_var.get(), add_margin.get(),
                  batch_rename_var.get(), rename_prefix_var.get(),
                  reformat_var.get(), new_format_var.get(), compression_var.get(),
                  auto_rotate_var.get(), app),
            daemon=True
        )
        t.start()
    except Exception as e:
        logger.error(f"Error handling image drop: {e}")
        raise

def process_dropped_files(files, resolution, add_margin, do_rename, rename_prefix,
                          do_reformat, new_format, compression, auto_rotate, app):
    try:
        logger.info("Processing dropped image files.")
        for idx, f in enumerate(files, start=1):
            process_image(f, resolution, add_margin, do_rename, rename_prefix,
                          do_reformat, new_format, compression, auto_rotate, idx, app)
    except Exception as e:
        logger.error(f"Error processing dropped files: {e}")
        app.queue.put((files[0], str(e)))
    finally:
        app.queue.put((files[0], "Done processing dropped image files."))

def process_image(file_path, resolution, add_margin, do_rename, rename_prefix,
                  do_reformat, new_format, compression, auto_rotate, idx, app):
    try:
        logger.info(f"Processing image: {file_path}")
        img = Image.open(file_path)

        # Original features first:
        # 1) Crop to square
        img = crop_to_square(img)

        # 2) Resize
        img = resize_image(img, resolution)

        # 3) Add margin if chosen
        if add_margin:
            img = add_image_inner_margin(img)

        # 4) Sharpen
        img = sharpen_image(img)

        # NEW feature: auto-rotate
        if auto_rotate:
            img = ImageOps.exif_transpose(img)

        # Figure out base name
        base_name, ext = os.path.splitext(os.path.basename(file_path))

        # If do_rename -> rename_prefix + padded index
        if do_rename:
            new_base_name = f"{rename_prefix}_{idx:04d}"
        else:
            new_base_name = base_name + "_processed"

        # If do_reformat -> use new format, else use old ext
        if do_reformat:
            final_ext = new_format.lower()
        else:
            final_ext = ext.lower().replace('.', '')

        suffix = ""
        output_folder = os.path.join(os.path.dirname(file_path), "output", "images_processed")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, new_base_name, suffix, final_ext)

        # Handle compression/quality if do_reformat is set
        save_params = {}
        if do_reformat:
            if final_ext in ["jpg", "jpeg", "webp"]:
                save_params["quality"] = compression
            elif final_ext == "png":
                # map 1-100 to 0-9
                cl = 9 - int((compression / 100)*9)
                save_params["compress_level"] = cl

        img.save(output_file, **save_params)
        app.increment_progress()
        app.queue.put((file_path, f"Image saved to: {output_file}"))
        logger.info(f"Image saved to: {output_file}")
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {e}")
        app.queue.put((file_path, f"Error: {str(e)}"))

def crop_to_square(img):
    width, height = img.size
    min_side = min(width, height)
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    return img.crop((left, top, left + min_side, top + min_side))

def resize_image(img, resolution):
    new_size = tuple(map(int, resolution.split("x")))
    return img.resize(new_size, Image.LANCZOS)

def add_image_inner_margin(img):
    margin = 16
    width, height = img.size
    new_img = Image.new("RGB", (width, height), (255, 255, 255))
    new_img.paste(img.crop((margin, margin, width - margin, height - margin)), (margin, margin))
    return new_img

def sharpen_image(img):
    enhancer = ImageEnhance.Sharpness(img)
    return enhancer.enhance(1.5)
