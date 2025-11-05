import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
from utils.file_helpers import find_files_in_folder, create_drop_area
from constants import VALID_EXTENSIONS
from processors.audio_processor import process_audio_files

PLUGIN_MANIFEST = {
    "plugin_id": "audio",
    "name": "Audio Studio",
    "description": "Batch convert, normalize, and master audio assets with reusable presets.",
    "category": "Audio",
    "keywords": ("audio", "conversion", "normalization", "batch"),
    "version": "2.0.0",
    "author": "Multi-Utility Team",
}

logger = logging.getLogger(__name__)


def register_plugin(plugin_api):
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("Audio", tab)

    options_frame = ttk.Frame(tab)
    options_frame.pack(fill=tk.X, pady=5)

    ttk.Label(options_frame, text="Select Output Format:").grid(
        row=0, column=0, sticky=tk.W, padx=5
    )
    audio_format_var = tk.StringVar(value="mp3")
    audio_formats = ["mp3", "wav", "flac", "m4a", "aac", "ogg", "wma"]
    format_combo = ttk.Combobox(
        options_frame,
        textvariable=audio_format_var,
        values=audio_formats,
        state="readonly",
        width=10,
    )
    format_combo.grid(row=0, column=1, padx=5, pady=2)

    ttk.Label(options_frame, text="Quick Presets:").grid(
        row=0, column=2, sticky=tk.W, padx=5
    )
    preset_var = tk.StringVar(value="Custom")
    preset_combo = ttk.Combobox(
        options_frame,
        textvariable=preset_var,
        values=["Custom", "Podcast", "Voiceover"],
        state="readonly",
        width=10,
    )
    preset_combo.grid(row=0, column=3, padx=5)

    def apply_preset(*_):
        preset = preset_var.get()
        if preset == "Podcast":
            audio_format_var.set("mp3")
            bitrate_var.set(128)
            mono_var.set(True)
            remove_silence_var.set(True)
            normalize_var.set(True)
        elif preset == "Voiceover":
            audio_format_var.set("wav")
            bitrate_var.set(192)
            mono_var.set(True)
            remove_silence_var.set(False)
            normalize_var.set(True)

    preset_var.trace_add("write", lambda *_: apply_preset())

    ttk.Label(options_frame, text="MP3 Bitrate (kbps):").grid(
        row=1, column=0, sticky=tk.W, padx=5
    )
    bitrate_var = tk.IntVar(value=192)
    bitrates = [96, 128, 192, 320]
    bitrate_combo = ttk.Combobox(
        options_frame,
        textvariable=bitrate_var,
        values=bitrates,
        state="readonly",
        width=5,
    )
    bitrate_combo.grid(row=1, column=1, padx=5, pady=2)

    mono_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(options_frame, text="Convert to Mono", variable=mono_var).grid(
        row=2, column=0, sticky=tk.W, padx=5
    )

    remove_silence_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(
        options_frame, text="Remove Silence", variable=remove_silence_var
    ).grid(row=2, column=1, sticky=tk.W, padx=5)

    normalize_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(
        options_frame, text="Volume Normalize (-0.1 dB)", variable=normalize_var
    ).grid(row=3, column=0, sticky=tk.W, padx=5)

    drop_frame = ttk.LabelFrame(tab, text="Drop Area")
    drop_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    drop_area = create_drop_area(
        drop_frame, plugin_api, text_str="Drag & drop audio files/folders here"
    )

    def audio_drop_event(e):
        paths = tab.tk.splitlist(e.data)
        audio_files = []
        for path in paths:
            if os.path.isdir(path):
                audio_files.extend(
                    find_files_in_folder(
                        path, valid_extensions=VALID_EXTENSIONS["AUDIO"]
                    )
                )
            elif path.lower().endswith(VALID_EXTENSIONS["AUDIO"]):
                audio_files.append(path)
        if not audio_files:
            messagebox.showerror("Error", "No valid audio files found.")
            return
        drop_area.set_files(audio_files)
        t = threading.Thread(
            target=process_audio_files,
            args=(
                audio_files,
                audio_format_var.get(),
                bitrate_var.get(),
                mono_var.get(),
                remove_silence_var.get(),
                normalize_var.get(),
                plugin_api.app,
            ),
            daemon=True,
        )
        t.start()

    drop_area.dnd_bind("<<Drop>>", audio_drop_event)

    # preset definitions
    def run_podcast_preset():
        files = tk.filedialog.askopenfilenames(
            filetypes=[("Audio", "*.mp3;*.wav;*.flac")]
        )
        if not files:
            return
        threading.Thread(
            target=process_audio_files,
            args=(files, "mp3", 128, True, True, True, plugin_api.app),
            daemon=True,
        ).start()

    def run_voiceover_preset():
        files = tk.filedialog.askopenfilenames(filetypes=[("Audio", "*.wav;*.flac")])
        if not files:
            return
        threading.Thread(
            target=process_audio_files,
            args=(files, "wav", 192, True, False, True, plugin_api.app),
            daemon=True,
        ).start()

    plugin_api.register_hook("preset:Podcast", run_podcast_preset)
    plugin_api.register_hook("preset:Voiceover", run_voiceover_preset)
    plugin_api.register_hook("list_presets", lambda: ["Podcast", "Voiceover"])
