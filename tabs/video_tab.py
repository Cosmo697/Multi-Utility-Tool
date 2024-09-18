# tabs/video_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from queue import Queue, Empty
import subprocess
from tkinterdnd2 import DND_FILES
from utils.helpers import ensure_output_dir, update_status_label, find_files_in_folder

def setup(tab, app):
    ttk.Label(tab, text="Drag and drop video files or folders here for processing.").pack(pady=10)
    ttk.Label(tab, text="Extract every nth frame:").pack()
    frame_interval_var = tk.IntVar(value=1)
    frame_options = [1, 2, 3, 4, 5]
    for interval in frame_options:
        ttk.Radiobutton(tab, text=f"Every {interval} frame", variable=frame_interval_var, value=interval).pack()
    
    drop_area = create_drop_area(tab)
    drop_area.bind("<Enter>", lambda event: drop_area.config(bg="lightgreen"))
    drop_area.bind("<Leave>", lambda event: drop_area.config(bg="darkgray"))
    drop_area.config(bg="darkgray")  # Initial color when mouse is not hovering
    
    drop_area.dnd_bind('<<Drop>>', lambda event: handle_video_drop(event, app, frame_interval_var, app.status_label, app.queue))
    app.root.after(100, lambda: process_queue(app, app.queue, app.status_label))

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your video files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_video_drop(event, app, frame_interval_var, status_label, queue):
    paths = app.root.tk.splitlist(event.data)
    video_files = []
    for path in paths:
        if os.path.isdir(path):
            video_files.extend(find_files_in_folder(path, valid_extensions=[".mp4", ".avi", ".mov", ".mkv"]))
        elif os.path.isfile(path) and path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            video_files.append(path)
    
    if not video_files:
        messagebox.showerror("Error", "No valid video files were found.")
        return

    app.start_progress()
    status_label.config(text="Processing video files...")
    t = threading.Thread(target=process_dropped_files, args=(video_files, frame_interval_var, queue))
    t.start()

def process_dropped_files(files, frame_interval_var, queue):
    for file in files:
        try:
            process_video_file(file, frame_interval_var.get(), queue)
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

def generate_unique_file_path(output_folder, base_name, suffix, ext, frame_num):
    padded_counter = f"{frame_num:04}"
    potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}_{padded_counter}.{ext}")
    return potential_file_path

def process_video_file(file_path, frame_interval, queue):
    try:
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "frames")
        ensure_output_dir(output_folder)

        # Use ffmpeg to extract frames with padded file names
        ffmpeg_cmd = [
            "ffmpeg", "-i", file_path, "-vf", f"select=not(mod(n\\,{frame_interval})),setpts=N/TB", 
            "-vsync", "vfr", os.path.join(output_folder, f"{base_name}_%04d.png")
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        queue.put((file_path, f"Frames extracted to: {output_folder}"))
    except subprocess.CalledProcessError as e:
        queue.put((file_path, str(e)))
    except Exception as err:
        queue.put((file_path, f"Unexpected error: {str(err)}"))