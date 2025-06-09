import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from utils.file_helpers import create_drop_area, find_files_in_folder
from constants import VALID_EXTENSIONS
from processors.video_processor import process_videos, join_multiple_clips

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)

def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("Video", tab)

    opts_frame = ttk.Frame(tab)
    opts_frame.pack(fill=tk.X, pady=5)

    # Video processing options UI.
    frame_interval_var = tk.IntVar(value=1)
    ttk.Label(opts_frame, text="Extract every nth frame:").grid(row=0, column=0, sticky=tk.W)
    ttk.Entry(opts_frame, textvariable=frame_interval_var, width=5).grid(row=0, column=1, padx=5)
    extract_frames_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Extract Frames", variable=extract_frames_var)\
        .grid(row=0, column=2, sticky=tk.W, padx=5)

    extract_audio_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Extract Audio", variable=extract_audio_var)\
        .grid(row=1, column=0, sticky=tk.W)
    audio_format_var = tk.StringVar(value="mp3")
    ttk.Label(opts_frame, text="Audio Format:").grid(row=1, column=1, sticky=tk.W)
    ttk.Combobox(opts_frame, textvariable=audio_format_var,
                 values=["mp3", "wav", "aac"], state="readonly", width=5)\
        .grid(row=1, column=2, padx=5)

    remove_audio_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Remove Audio Track", variable=remove_audio_var)\
        .grid(row=2, column=0, sticky=tk.W)

    join_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Join Multiple Clips", variable=join_var)\
        .grid(row=3, column=0, sticky=tk.W)

    convert_video_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Convert Video Format", variable=convert_video_var)\
        .grid(row=4, column=0, sticky=tk.W)
    convert_format_var = tk.StringVar(value="mp4")
    ttk.Label(opts_frame, text="Convert to Format:").grid(row=4, column=1, sticky=tk.W)
    ttk.Combobox(opts_frame, textvariable=convert_format_var,
                 values=["mp4", "mkv", "mov", "avi"], state="readonly", width=5)\
        .grid(row=4, column=2, padx=5)

    keep_quality_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(opts_frame, text="Keep Original Quality", variable=keep_quality_var)\
        .grid(row=5, column=0, sticky=tk.W)
    # Now working in Mbps
    ttk.Label(opts_frame, text="Target Bitrate (Mbps):").grid(row=5, column=1, sticky=tk.W)
    bitrate_options = ["1", "2", "3", "5", "8"]
    bitrate_var = tk.StringVar(value="3")
    ttk.Combobox(opts_frame, textvariable=bitrate_var,
                 values=bitrate_options, state="readonly", width=5)\
        .grid(row=5, column=2, padx=5)

    extract_gif_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(opts_frame, text="Extract GIF", variable=extract_gif_var)\
        .grid(row=6, column=0, sticky=tk.W)

    ttk.Label(opts_frame, text="Rotate:").grid(row=7, column=0, sticky=tk.W)
    rotate_option_var = tk.StringVar(value="None")
    rotate_options = ["None", "Rotate 90° CW", "Rotate 90° CCW"]
    ttk.Combobox(opts_frame, textvariable=rotate_option_var,
                 values=rotate_options, state="readonly", width=12)\
        .grid(row=7, column=1, padx=5, pady=2)

    # GPU acceleration is always used by default.

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    drop_area = create_drop_area(drop_frame, plugin_api, text_str="Drag & drop video files/folders here")

    def video_drop_event(e):
        paths = tab.tk.splitlist(e.data)
        video_files = []
        for path in paths:
            if os.path.isdir(path):
                video_files.extend(find_files_in_folder(path, valid_extensions=VALID_EXTENSIONS["VIDEO"]))
            elif path.lower().endswith(VALID_EXTENSIONS["VIDEO"]):
                video_files.append(path)
        if not video_files:
            messagebox.showerror("Error", "No valid video files were found.")
            return
        options = {
            'frame_interval': frame_interval_var.get(),
            'extract_frames': extract_frames_var.get(),
            'extract_audio': extract_audio_var.get(),
            'audio_format': audio_format_var.get(),
            'remove_audio': remove_audio_var.get(),
            'convert_video': convert_video_var.get(),
            'output_format': convert_format_var.get(),
            'keep_quality': keep_quality_var.get(),
            'bitrate': bitrate_var.get(),  # in Mbps
            'extract_gif': extract_gif_var.get(),
            'rotate_option': rotate_option_var.get(),
        }
        drop_area.set_files(video_files)
        if join_var.get() and len(video_files) > 1:
            join_multiple_clips(video_files, options, plugin_api.app)
        else:
            executor.submit(process_videos, video_files, options, plugin_api.app)
    drop_area.dnd_bind('<<Drop>>', video_drop_event)
