# tabs/image_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageEnhance
import threading
from queue import Queue, Empty
from tkinterdnd2 import DND_FILES
from utils.helpers import ensure_output_dir, update_status_label, find_files_in_folder
from datetime import datetime

def setup(tab, app):
    ttk.Label(tab, text="Drag and drop images or folders here for processing.").pack(pady=10)
    ttk.Label(tab, text="Resize Options:").pack()
    resolution_var = tk.StringVar(value="1024x1024")
    resolutions = ["1024x1024", "768x768", "512x512"]
    for res in resolutions:
        ttk.Radiobutton(tab, text=res, variable=resolution_var, value=res).pack()
    add_margin = tk.BooleanVar(value=False)
    ttk.Checkbutton(tab, text="Add 16-pixel margin", variable=add_margin).pack()
    
    drop_area = create_drop_area(tab)
    drop_area.bind("<Enter>", lambda event: drop_area.config(bg="lightgreen"))
    drop_area.bind("<Leave>", lambda event: drop_area.config(bg="darkgray"))
    drop_area.config(bg="darkgray")  # Initial color when mouse is not hovering

    drop_area.dnd_bind('<<Drop>>', lambda event: handle_image_drop(event, app, resolution_var, add_margin, app.status_label, app.queue))
    app.root.after(100, lambda: process_queue(app, app.queue, app.status_label))

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your image files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_image_drop(event, app, resolution_var, add_margin, status_label, queue):
    paths = app.root.tk.splitlist(event.data)
    image_files = []
    for path in paths:
        if os.path.isdir(path):
            image_files.extend(find_files_in_folder(path, valid_extensions=[".jpg", ".jpeg", ".png", ".bmp"]))
        elif os.path.isfile(path) and path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            image_files.append(path)

    if not image_files:
        messagebox.showerror("Error", "No valid image files were found.")
        return

    app.start_progress()
    status_label.config(text="Processing image files...")
    t = threading.Thread(target=process_dropped_files, args=(image_files, resolution_var, add_margin, queue))
    t.start()

def process_dropped_files(files, resolution_var, add_margin, queue):
    for file in files:
        try:
            process_image(file, resolution_var, add_margin, queue)
        except Exception as e:
            queue.put((file, str(e)))

def process_queue(app, queue, status_label):
    try:
        while True:
            msg = queue.get_nowait()
            update_status_label(status_label, msg[1])
            app.stop_progress()
    except Empty:
        app.root.after(100, lambda: process_queue(app, queue, status_label))

def get_timestamped_suffix():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def generate_unique_file_path(output_folder, base_name, suffix, ext):
    potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}.{ext}")
    counter = 1
    while os.path.exists(potential_file_path):
        padded_counter = f"{counter:03}"
        potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}_{padded_counter}.{ext}")
        counter += 1
    return potential_file_path

def process_image(file_path, resolution_var, add_margin, queue):
    try:
        img = Image.open(file_path)
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        suffix = ""
        
        img = crop_to_square(img)
        img = resize_image(img, resolution_var.get())
        suffix += f"_resized_{resolution_var.get()}"
        
        if add_margin.get():
            img = add_image_inner_margin(img)
            suffix += "_margin"
        
        img = sharpen_image(img)
        suffix += "_sharpened"
        
        output_folder = os.path.join(os.path.dirname(file_path), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, suffix, ext[1:])
        img.save(output_file)
        queue.put((file_path, f"Image saved to: {output_file}"))
    except Exception as e:
        queue.put((file_path, f"Error: {str(e)}"))

def crop_to_square(img):
    width, height = img.size
    min_side = min(width, height)
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    return img.crop((left, top, width - left, height - top))

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