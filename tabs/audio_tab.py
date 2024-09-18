# tabs/audio_tab.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from queue import Queue, Empty
import subprocess
from datetime import datetime
from tkinterdnd2 import DND_FILES
from utils.helpers import ensure_output_dir, update_status_label, find_files_in_folder

def setup(tab, app):
    ttk.Label(tab, text="Drag and drop audio files or folders here for processing.").pack(pady=10)
    ttk.Label(tab, text="Select Output Format:").pack()
    audio_format_var = tk.StringVar(value="mp3")
    audio_formats = ["mp3", "wav", "flac", "m4a", "aac", "ogg", "wma"]
    for fmt in audio_formats:
        ttk.Radiobutton(tab, text=fmt.upper(), variable=audio_format_var, value=fmt).pack()
    bitrate_var = tk.IntVar(value=128)
    ttk.Label(tab, text="Select MP3 Bitrate (kbps):").pack()
    mp3_bitrates = [96, 128, 192, 320]
    for rate in mp3_bitrates:
        ttk.Radiobutton(tab, text=f"{rate} kbps", variable=bitrate_var, value=rate).pack()
    
    # Mono conversion checkbox
    mono_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(tab, text="Convert to Mono", variable=mono_var).pack(pady=5)
    
    drop_area = create_drop_area(tab)
    drop_area.bind("<Enter>", lambda event: drop_area.config(bg="lightgreen"))
    drop_area.bind("<Leave>", lambda event: drop_area.config(bg="darkgray"))
    drop_area.config(bg="darkgray")  # Initial color when mouse is not hovering

    drop_area.dnd_bind('<<Drop>>', lambda event: handle_audio_drop(event, app, audio_format_var, bitrate_var, mono_var, app.status_label, app.queue))
    app.root.after(100, lambda: process_queue(app, app.queue, app.status_label))

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your audio files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_audio_drop(event, app, audio_format_var, bitrate_var, mono_var, status_label, queue):
    paths = app.root.tk.splitlist(event.data)
    audio_files = []
    for path in paths:
        if os.path.isdir(path):
            audio_files.extend(find_files_in_folder(path, valid_extensions=[".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"]))
        elif os.path.isfile(path) and path.lower().endswith(('.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma')):
            audio_files.append(path)
    
    if not audio_files:
        messagebox.showerror("Error", "No valid audio files were found")
        return

    app.start_progress()
    status_label.config(text="Processing audio files...")
    t = threading.Thread(target=process_dropped_files, args=(audio_files, audio_format_var, bitrate_var, mono_var, queue))
    t.start()

def process_dropped_files(files, audio_format_var, bitrate_var, mono_var, queue):
    for file in files:
        try:
            process_audio_file(file, audio_format_var.get(), bitrate_var.get(), mono_var.get(), queue)
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

def generate_unique_file_path(output_folder, base_name, output_format, bitrate):
    suffix = f"_{bitrate}kbps"
    potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}.{output_format}")
    counter = 1
    while os.path.exists(potential_file_path):
        padded_counter = f"{counter:03}"
        potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}_{padded_counter}.{output_format}")
        counter += 1
    return potential_file_path

def process_audio_file(file_path, output_format, bitrate, convert_to_mono, queue):
    try:
        output_bitrate = f"{bitrate}k"
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, output_format, bitrate)
        ffmpeg_cmd = ["ffmpeg", "-i", file_path]
        if convert_to_mono:
            ffmpeg_cmd.extend(["-ac", "1"])
        if output_format == "mp3":
            ffmpeg_cmd.extend(["-b:a", output_bitrate, output_file])
        else:
            ffmpeg_cmd.append(output_file)
        subprocess.run(ffmpeg_cmd, check=True)
        queue.put((file_path, f"Audio saved to: {output_file}"))
    except subprocess.CalledProcessError as e:
        queue.put((file_path, f"Error: {str(e)}"))