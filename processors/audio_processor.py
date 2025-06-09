import os
import logging

from utils.file_helpers import ensure_file_output_dir, generate_unique_file_path
from utils.ffmpeg_helpers import run_ffmpeg_command
from utils.diagnostics import increment_usage, time_block

logger = logging.getLogger(__name__)

def process_audio_files(audio_files, output_format, bitrate, mono, remove_silence, normalize, app):
    """Process a list of audio files with progress callbacks."""
    increment_usage("audio")
    total = len(audio_files)
    app.queue.put((None, "status", "Processing audio files..."))
    app.start_progress()
    for i, file_path in enumerate(audio_files, start=1):
        with time_block(f"audio:{os.path.basename(file_path)}"):
            process_audio_file(file_path, output_format, bitrate, mono, remove_silence, normalize, app)
        app.increment_progress(i, total)
    app.queue.put((None, "done", "Audio processing complete."))

def process_audio_file(file_path, output_format, bitrate, mono, remove_silence, normalize, app):
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    out_dir = ensure_file_output_dir(file_path)
    suffix = f"_{bitrate}kbps" if output_format == "mp3" else ""
    output_file = generate_unique_file_path(out_dir, base_name, suffix, output_format)

    ffmpeg_cmd = ["ffmpeg", "-i", file_path]
    filter_chain = []
    if remove_silence:
        filter_chain.append("silenceremove=1:0:-50dB")
    if mono:
        ffmpeg_cmd += ["-ac", "1"]
    if normalize:
        filter_chain.append("volume=-0.1dB")
    if filter_chain:
        ffmpeg_cmd += ["-af", ",".join(filter_chain)]
    if output_format == "mp3":
        ffmpeg_cmd += ["-b:a", f"{bitrate}k", output_file]
    else:
        ffmpeg_cmd.append(output_file)

    err = run_ffmpeg_command(ffmpeg_cmd, "Error processing audio file")
    if not err:
        app.queue.put((file_path, "status", f"Audio saved to {output_file}"))
    else:
        app.queue.put((file_path, "status", f"Audio error: {err}"))
