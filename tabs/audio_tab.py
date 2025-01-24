# tabs/audio_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
from tkinterdnd2 import DND_FILES
import logging

from utils.helpers import ensure_output_dir, find_files_in_folder, generate_unique_file_path

logger = logging.getLogger(__name__)

def setup_audio_tab(tab, app):
    try:
        logger.info("Setting up Audio tab.")
        ttk.Label(tab, text="Drag and drop audio files or folders here for processing.").pack(pady=10)
        ttk.Label(tab, text="Select Output Format:").pack()
        
        audio_format_var = tk.StringVar(value="mp3")
        audio_formats = ["mp3", "wav", "flac", "m4a", "aac", "ogg", "wma"]
        for fmt in audio_formats:
            ttk.Radiobutton(tab, text=fmt.upper(), variable=audio_format_var, value=fmt).pack()

        bitrate_var = tk.IntVar(value=192)  # default was 192
        ttk.Label(tab, text="Select MP3 Bitrate (kbps):").pack()
        mp3_bitrates = [96, 128, 192, 320]
        for rate in mp3_bitrates:
            ttk.Radiobutton(tab, text=f"{rate} kbps", variable=bitrate_var, value=rate).pack()

        mono_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Convert to Mono", variable=mono_var).pack(pady=5)

        # NEW: Additional checkboxes
        remove_silence_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Remove Silence", variable=remove_silence_var).pack(pady=5)

        normalize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Volume Normalize (-0.1 dB)", variable=normalize_var).pack(pady=5)

        # Drop area
        drop_area = create_drop_area(tab)
        drop_area.dnd_bind('<<Drop>>',
            lambda e: handle_audio_drop(e, app, audio_format_var, bitrate_var, mono_var,
                                        remove_silence_var, normalize_var)
        )
        logger.info("Audio tab setup complete.")
    except Exception as e:
        logger.error(f"Error setting up Audio tab: {e}")
        raise

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your audio files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_audio_drop(event, app, audio_format_var, bitrate_var, mono_var, remove_silence_var, normalize_var):
    try:
        logger.info("Handling dropped audio files.")
        paths = app.root.tk.splitlist(event.data)
        audio_files = []
        for path in paths:
            if os.path.isdir(path):
                audio_files.extend(
                    find_files_in_folder(
                        path,
                        valid_extensions=[".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"]
                    )
                )
            elif os.path.isfile(path) and path.lower().endswith((".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma")):
                audio_files.append(path)

        if not audio_files:
            messagebox.showerror("Error", "No valid audio files were found")
            logger.warning("No valid audio files found during drop event.")
            return

        app.start_progress()
        app.update_status("Processing audio files...")
        logger.info(f"Starting processing for dropped files: {audio_files}")
        t = threading.Thread(
            target=process_dropped_files,
            args=(audio_files, audio_format_var.get(), bitrate_var.get(), mono_var.get(),
                  remove_silence_var.get(), normalize_var.get(), app),
            daemon=True
        )
        t.start()
    except Exception as e:
        logger.error(f"Error handling audio drop: {e}")
        raise

def process_dropped_files(files, output_format, bitrate, mono, remove_silence, normalize, app):
    try:
        logger.info("Processing dropped audio files.")
        for file in files:
            process_audio_file(file, output_format, bitrate, mono, remove_silence, normalize, app)
    except Exception as e:
        logger.error(f"Error processing dropped files: {e}")
        app.queue.put((files[0], str(e)))
    finally:
        app.queue.put((files[0], "Done processing audio files."))

def process_audio_file(file_path, output_format, bitrate, mono, remove_silence, normalize, app):
    try:
        logger.info(f"Processing audio file: {file_path}")
        output_bitrate = f"{bitrate}k"
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "audio")
        ensure_output_dir(output_folder)
        suffix = f"_{bitrate}kbps" if output_format == "mp3" else ""
        output_file = generate_unique_file_path(output_folder, base_name, suffix, output_format)

        ffmpeg_cmd = ["ffmpeg", "-i", file_path]

        # Remove silence (example: remove from start/end if below -50dB)
        if remove_silence:
            # if you also want to combine with other filters, you'd chain them with commas
            ffmpeg_cmd += ["-af", "silenceremove=1:0:-50dB"]

        # Mono
        if mono:
            ffmpeg_cmd += ["-ac", "1"]

        # Normalization
        if normalize:
            # If we already used "-af", chain them
            # Example: if remove_silence was also used, we chain the filters
            if remove_silence:
                # Replace the last filter param with a chain
                # The last item in ffmpeg_cmd is e.g. "silenceremove=1:0:-50dB"
                last_filter = ffmpeg_cmd.pop()
                combined_filter = last_filter + ",volume=-0.1dB"
                ffmpeg_cmd += [combined_filter]
            else:
                ffmpeg_cmd += ["-af", "volume=-0.1dB"]

        # If mp3, set bitrate
        if output_format == "mp3":
            ffmpeg_cmd += ["-b:a", output_bitrate, output_file]
        else:
            ffmpeg_cmd.append(output_file)

        subprocess.run(ffmpeg_cmd, check=True)
        app.queue.put((file_path, f"Audio saved to: {output_file}"))
        logger.info(f"Audio saved to: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error processing audio file {file_path}: {e}")
        app.queue.put((file_path, f"Error: {str(e)}"))
    except Exception as e:
        logger.error(f"Unexpected error processing audio file {file_path}: {e}")
        app.queue.put((file_path, f"Error: {str(e)}"))
    finally:
        app.increment_progress()
