# tabs/video_tab.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from queue import Queue, Empty
import subprocess
from tkinterdnd2 import DND_FILES
import logging

from utils.helpers import ensure_output_dir, find_files_in_folder

logger = logging.getLogger(__name__)

def setup_video_tab(tab, app):
    try:
        logger.info("Setting up Video tab.")
        ttk.Label(tab, text="Drag and drop video files or folders here for processing.").pack(pady=10)
        
        # Original:
        frame_interval_var = tk.IntVar(value=1)
        extract_audio_var = tk.BooleanVar(value=False)
        audio_format_var = tk.StringVar(value="mp3")
        skip_frame_extraction_var = tk.BooleanVar(value=True)
        remove_audio_var = tk.BooleanVar(value=False)

        ttk.Label(tab, text="Extract every nth frame:").pack()
        for interval in [1, 2, 5, 10]:
            ttk.Radiobutton(tab, text=f"Every {interval}", variable=frame_interval_var, value=interval).pack()

        ttk.Checkbutton(tab, text="Extract Audio from Video", variable=extract_audio_var).pack(pady=5)
        ttk.Label(tab, text="Select Audio Format:").pack()
        for fmt in ["mp3", "wav", "aac"]:
            ttk.Radiobutton(tab, text=fmt.upper(), variable=audio_format_var, value=fmt).pack()

        ttk.Checkbutton(tab, text="Skip Frame Extraction", variable=skip_frame_extraction_var).pack(pady=5)
        ttk.Checkbutton(tab, text="Remove Audio Track", variable=remove_audio_var).pack(pady=5)

        # NEW:
        join_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Join Multiple Clips", variable=join_var).pack(pady=5)

        convert_format_var = tk.StringVar(value="mp4")
        ttk.Label(tab, text="Convert to Format:").pack()
        ttk.Combobox(tab, textvariable=convert_format_var, values=["mp4","mkv","mov","avi"], state="readonly").pack()

        keep_quality_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Keep Original Quality", variable=keep_quality_var).pack()

        ttk.Label(tab, text="Target Bitrate (k or blank):").pack()
        bitrate_var = tk.StringVar(value="")
        ttk.Entry(tab, textvariable=bitrate_var, width=10).pack()

        extract_gif_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Extract GIF", variable=extract_gif_var).pack(pady=5)

        drop_area = create_drop_area(tab)
        drop_area.dnd_bind('<<Drop>>', lambda e: handle_video_drop(
            e, app, frame_interval_var, extract_audio_var, audio_format_var,
            skip_frame_extraction_var, remove_audio_var,
            join_var, convert_format_var, keep_quality_var, bitrate_var, extract_gif_var
        ))
        logger.info("Video tab setup complete.")
    except Exception as e:
        logger.error(f"Error setting up Video tab: {e}")
        raise

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your video files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_video_drop(event, app,
                      frame_interval_var, extract_audio_var, audio_format_var,
                      skip_frame_extraction_var, remove_audio_var,
                      join_var, convert_format_var, keep_quality_var, bitrate_var, extract_gif_var):
    try:
        logger.info("Handling dropped video files.")
        paths = app.root.tk.splitlist(event.data)
        video_files = []
        for path in paths:
            if os.path.isdir(path):
                video_files.extend(find_files_in_folder(path, valid_extensions=[".mp4", ".avi", ".mov", ".mkv"]))
            elif os.path.isfile(path) and path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
                video_files.append(path)
        
        if not video_files:
            messagebox.showerror("Error", "No valid video files were found.")
            logger.warning("No valid video files found during drop event.")
            return

        app.start_progress()
        app.update_status("Processing video files...")
        logger.info(f"Starting processing for dropped files: {video_files}")
        t = threading.Thread(
            target=process_videos,
            args=(
                video_files,
                frame_interval_var.get(),
                extract_audio_var.get(),
                audio_format_var.get(),
                skip_frame_extraction_var.get(),
                remove_audio_var.get(),
                join_var.get(),
                convert_format_var.get(),
                keep_quality_var.get(),
                bitrate_var.get(),
                extract_gif_var.get(),
                app
            ),
            daemon=True
        )
        t.start()
    except Exception as e:
        logger.error(f"Error handling video drop: {e}")
        raise

def process_videos(files, frame_interval, extract_audio, audio_fmt,
                   skip_frames, remove_audio,
                   join_clips, convert_fmt, keep_quality, bitrate_str, extract_gif,
                   app):
    try:
        logger.info("Processing dropped video files.")
        if join_clips and len(files) > 1:
            join_multiple_clips(files, convert_fmt, keep_quality, bitrate_str, app)
        else:
            for f in files:
                process_single_video(f, frame_interval, extract_audio, audio_fmt,
                                     skip_frames, remove_audio,
                                     convert_fmt, keep_quality, bitrate_str,
                                     extract_gif, app)
    except Exception as e:
        logger.error(f"Error processing dropped videos: {e}")
        app.queue.put((files[0], str(e)))
    finally:
        app.queue.put((files[0], "Done processing video(s)."))

def join_multiple_clips(files, output_format, keep_quality, bitrate_str, app):
    try:
        logger.info("Joining multiple clips.")
        base_path = os.path.dirname(files[0])
        output_folder = os.path.join(base_path, "output", "joined_videos")
        ensure_output_dir(output_folder)

        concat_file = os.path.join(output_folder, "concat_list.txt")
        with open(concat_file, 'w', encoding='utf-8') as cf:
            for f in files:
                cf.write(f"file '{f}'\n")

        joined_output = os.path.join(output_folder, f"joined_output.{output_format}")
        if not keep_quality and bitrate_str.strip():
            # re-encode with set bitrate
            cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c:v", "libx264", "-b:v", f"{bitrate_str}",
                "-c:a", "aac", joined_output
            ]
        else:
            # copy streams
            cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c", "copy", joined_output
            ]
        subprocess.run(cmd, check=True)

        app.increment_progress()
        app.queue.put((None, f"Joined video saved to: {joined_output}"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error joining video files: {e}")
        app.queue.put((None, f"Join error: {str(e)}"))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        app.queue.put((None, f"Join error: {str(e)}"))

def process_single_video(file_path, frame_interval, extract_audio, audio_fmt,
                         skip_frames, remove_audio,
                         convert_fmt, keep_quality, bitrate_str, extract_gif, app):
    try:
        logger.info(f"Processing video file: {file_path}")
        
        # Remove audio track
        if remove_audio:
            strip_audio_from_video(file_path, app)

        # Extract audio
        if extract_audio:
            extract_audio_from_video(file_path, audio_fmt, app)

        # Extract frames
        if not skip_frames:
            extract_frames_from_video(file_path, frame_interval, app)

        # Convert to new format
        out_folders = convert_single_video(file_path, convert_fmt, keep_quality, bitrate_str, app)

        # Extract GIF
        if extract_gif:
            gif_folder = extract_gif_from_video(file_path, app)
            if gif_folder and gif_folder not in out_folders:
                out_folders.append(gif_folder)

        app.increment_progress()
    except Exception as e:
        logger.error(f"Error processing single video {file_path}: {e}")
        app.queue.put((file_path, str(e)))

def strip_audio_from_video(file_path, app):
    try:
        logger.info(f"Removing audio from: {file_path}")
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "video_no_audio")
        ensure_output_dir(output_folder)
        output_file = os.path.join(output_folder, f"{base_name}_noaudio{ext}")

        cmd = ["ffmpeg", "-i", file_path, "-c", "copy", "-an", output_file]
        subprocess.run(cmd, check=True)
        app.queue.put((file_path, f"Audio removed: {output_file}"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error removing audio: {e}")
        app.queue.put((file_path, f"Remove audio error: {str(e)}"))

def extract_audio_from_video(file_path, audio_fmt, app):
    try:
        logger.info(f"Extracting audio from: {file_path}")
        base_name, _ = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "extracted_audio")
        ensure_output_dir(output_folder)
        output_file = os.path.join(output_folder, f"{base_name}.{audio_fmt}")

        cmd = ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", output_file]
        subprocess.run(cmd, check=True)
        app.queue.put((file_path, f"Audio extracted: {output_file}"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting audio: {e}")
        app.queue.put((file_path, f"Extract audio error: {str(e)}"))

def extract_frames_from_video(file_path, frame_interval, app):
    try:
        base_name, _ = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "frames")
        ensure_output_dir(output_folder)
        output_pattern = os.path.join(output_folder, f"{base_name}_%04d.png")

        cmd = [
            "ffmpeg", "-i", file_path,
            "-vf", f"select=not(mod(n\\,{frame_interval})),setpts=N/TB",
            "-vsync", "vfr", output_pattern
        ]
        subprocess.run(cmd, check=True)
        app.queue.put((file_path, f"Frames extracted to: {output_folder}"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting frames: {e}")
        app.queue.put((file_path, f"Frame extract error: {str(e)}"))

def convert_single_video(file_path, output_format, keep_quality, bitrate_str, app):
    try:
        logger.info(f"Converting video to {output_format}: {file_path}")
        base_name, _ = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "converted_video")
        ensure_output_dir(output_folder)
        out_file = os.path.join(output_folder, f"{base_name}.{output_format}")

        if keep_quality or not bitrate_str.strip():
            # copy streams
            cmd = ["ffmpeg", "-i", file_path, "-c:v", "copy", "-c:a", "copy", out_file]
        else:
            # re-encode with target bitrate
            cmd = [
                "ffmpeg", "-i", file_path,
                "-c:v", "libx264", "-b:v", f"{bitrate_str}",
                "-c:a", "aac", out_file
            ]
        subprocess.run(cmd, check=True)
        app.queue.put((file_path, f"Converted video: {out_file}"))
        return [output_folder]
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting video: {e}")
        app.queue.put((file_path, f"Video convert error: {str(e)}"))
    return []

def extract_gif_from_video(file_path, app):
    try:
        logger.info(f"Extracting GIF from: {file_path}")
        base_name, _ = os.path.splitext(os.path.basename(file_path))
        gif_folder = os.path.join(os.path.dirname(file_path), "output", "gif_extracted")
        ensure_output_dir(gif_folder)
        gif_file = os.path.join(gif_folder, f"{base_name}.gif")

        # simple approach:
        cmd = [
            "ffmpeg", "-i", file_path,
            "-vf", "fps=10,scale=480:-1:flags=lanczos",
            "-gifflags", "+transdiff",
            gif_file
        ]
        subprocess.run(cmd, check=True)
        app.queue.put((file_path, f"GIF extracted: {gif_file}"))
        return gif_folder
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting gif: {e}")
        app.queue.put((file_path, f"GIF extract error: {str(e)}"))
    return None
