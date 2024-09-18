# tabs/text_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from queue import Queue, Empty
from datetime import datetime
from tkinterdnd2 import DND_FILES
from utils.helpers import ensure_output_dir, update_status_label, find_files_in_folder

def setup(tab, app):
    ttk.Label(tab, text="Drag and drop text files or folders here for processing.").pack(pady=10)
    merge_var = tk.BooleanVar(value=False)
    deduplicate_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(tab, text="Merge Files", variable=merge_var).pack(pady=5)
    ttk.Checkbutton(tab, text="Deduplicate Words", variable=deduplicate_var).pack(pady=5)
    
    drop_area = create_drop_area(tab)
    drop_area.bind("<Enter>", lambda event: drop_area.config(bg="lightgreen"))
    drop_area.bind("<Leave>", lambda event: drop_area.config(bg="darkgray"))
    drop_area.config(bg="darkgray")  # Initial color when mouse is not hovering

    drop_area.dnd_bind('<<Drop>>', lambda event: handle_text_drop(event, app, merge_var, deduplicate_var, app.status_label, app.queue))
    app.root.after(100, lambda: process_queue(app, app.queue, app.status_label))

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your text files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_text_drop(event, app, merge_var, deduplicate_var, status_label, queue):
    paths = app.root.tk.splitlist(event.data)
    text_files = []
    for path in paths:
        if os.path.isdir(path):
            text_files.extend(find_files_in_folder(path, valid_extensions=[".txt"]))
        elif os.path.isfile(path) and path.endswith('.txt'):
            text_files.append(path)
            
    if not text_files:
        messagebox.showerror("Error", "No valid text files were found.")
        return

    app.start_progress()
    status_label.config(text="Processing text files...")
    t = threading.Thread(target=process_dropped_files, args=(text_files, merge_var, deduplicate_var, queue))
    t.start()

def process_dropped_files(files, merge_var, deduplicate_var, queue):
    output_files = []
    for file in files:
        try:
            if merge_var.get():
                merge_text_files(files, queue)
                return
            elif deduplicate_var.get():
                output_files.append(deduplicate_text_files(file, queue))
            else:
                output_files.append(process_text_file(file, queue))
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

def process_text_file(file_path, queue):
    try:
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "", ext[1:])
        with open(file_path, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                outfile.write(line)
        queue.put((file_path, f"Text file saved to: {output_file}"))
        return output_file
    except Exception as e:
        queue.put((file_path, str(e)))
    
def merge_text_files(file_paths, queue):
    try:
        base_name = "merged"
        ext = "txt"
        output_folder = os.path.join(os.path.dirname(file_paths[0]), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "", ext)
        with open(output_file, 'w') as outfile:
            for i, file_path in enumerate(file_paths):
                with open(file_path, 'r') as infile:
                    outfile.write(infile.read())
                    if i < len(file_paths) - 1:
                        outfile.write("\n---\n")
        queue.put((file_paths[0], f"Text files merged and saved to: {output_file}"))
    except Exception as e:
        queue.put((file_paths[0], str(e)))

def deduplicate_text_files(file_path, queue):
    try:
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "_deduplicated", ext[1:])
        unique_words = set()
        with open(file_path, 'r') as infile, open(output_file, 'w') as outfile:
            for word in infile.read().split():
                if word not in unique_words:
                    outfile.write(f"{word} ")
                    unique_words.add(word)
        queue.put((file_path, f"Duplicate words removed, file saved to: {output_file}"))
        return output_file
    except Exception as e:
        queue.put((file_path, str(e)))