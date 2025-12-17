import os
import logging
from ..constants import VALID_EXTENSIONS
from ..utils.diagnostics import increment_usage, time_block
from ..utils.ffmpeg_helpers import is_gpu_available, run_ffmpeg_command
from ..utils.file_helpers import ensure_file_output_dir, generate_unique_file_path


USE_GPU = is_gpu_available()


def _encoder_opts(bitrate=None, quality="18"):
    """Return ffmpeg encoding options based on hardware availability."""
    if bitrate:
        rate_opt = ["-b:v", bitrate]
    else:
        rate_opt = ["-cq", quality] if USE_GPU else ["-crf", quality]

    codec = ["-c:v", "h264_nvenc"] if USE_GPU else ["-c:v", "libx264"]
    preset = ["-preset", "p4"] if USE_GPU else ["-preset", "veryslow"]
    return codec + preset + rate_opt


logger = logging.getLogger(__name__)


def process_videos(files, options, app):
    """
    Process each video file based on the requested options.
    Options is a dict with keys:
      - convert_video (bool)
      - remove_audio (bool)
      - rotate_option (str): "None", "Rotate 90° CW", or "Rotate 90° CCW"
      - output_format (str): e.g. "mp4"
      - keep_quality (bool)
      - bitrate (str) -> interpreted in Mbps
      - extract_frames (bool)
      - frame_interval (int)
      - extract_audio (bool)
      - audio_format (str)
      - extract_gif (bool)
    """
    increment_usage("video")
    app.queue.put((None, "status", "Processing video files..."))
    app.start_progress()
    total = len(files)
    for i, f in enumerate(files, start=1):
        with time_block(f"video:{os.path.basename(f)}"):
            process_single_video(f, options, app)
        app.increment_progress(i, total)
    app.queue.put((None, "done", "Video processing complete."))


def process_single_video(file_path, options, app):
    # Run conversion if any conversion task is requested.
    if (
        options.get("convert_video")
        or options.get("remove_audio")
        or (options.get("rotate_option") and options.get("rotate_option") != "None")
    ):
        process_video_conversion(file_path, options, app)
    else:
        app.queue.put((file_path, "status", "Skipping video conversion."))

    if options.get("extract_frames"):
        extract_frames_from_video(file_path, options.get("frame_interval", 1), app)
    if options.get("extract_audio"):
        extract_audio_from_video(file_path, options.get("audio_format", "mp3"), app)
    if options.get("extract_gif"):
        extract_gif_from_video(file_path, app)


def process_video_conversion(file_path, options, app):
    # Build filter chain for rotation if requested.
    vf_filters = []
    rotate_option = options.get("rotate_option", "None")
    if rotate_option and rotate_option != "None":
        if rotate_option == "Rotate 90° CW":
            vf_filters.append("transpose=1")
        elif rotate_option == "Rotate 90° CCW":
            vf_filters.append("transpose=2")
    vf = ",".join(vf_filters) if vf_filters else None

    # Set audio options.
    audio_opts = ["-c:a", "copy"]
    if options.get("remove_audio"):
        audio_opts = ["-an"]

    # Determine if re-encoding is necessary:
    need_reencode = (
        options.get("convert_video")
        or vf is not None
        or not options.get("keep_quality", True)
    )

    if need_reencode:
        bitrate_str = options.get("bitrate", "").strip()
        min_bitrate_mbps = 1
        if bitrate_str.isdigit():
            bitrate_val_mbps = int(bitrate_str)
            if bitrate_val_mbps < min_bitrate_mbps:
                app.queue.put(
                    (
                        file_path,
                        "status",
                        f"Provided bitrate ({bitrate_val_mbps} Mbps) is too low; using minimum {min_bitrate_mbps} Mbps.",
                    )
                )
                bitrate_val_mbps = min_bitrate_mbps
            bitrate_val = f"{bitrate_val_mbps * 1000}k"
            video_opts = _encoder_opts(bitrate=bitrate_val)
        else:
            video_opts = _encoder_opts()
    else:
        video_opts = ["-c:v", "copy"]

    # Add video filter if needed.
    filter_opts = []
    if vf:
        filter_opts = ["-vf", vf]
        if video_opts == ["-c:v", "copy"]:
            video_opts = _encoder_opts()

    base_name, ext = os.path.splitext(os.path.basename(file_path))
    output_format = options.get("output_format", ext.replace(".", ""))
    suffix = ""
    if options.get("remove_audio"):
        suffix += "_noaudio"
    if vf:
        suffix += "_rotated"
    if options.get("convert_video"):
        suffix += "_converted"
    out_dir = ensure_file_output_dir(file_path)
    output_file = generate_unique_file_path(out_dir, base_name, suffix, output_format)

    cmd = (
        ["ffmpeg", "-i", file_path]
        + filter_opts
        + video_opts
        + audio_opts
        + [output_file]
    )
    err = run_ffmpeg_command(cmd, "Error processing video")
    if not err:
        app.queue.put((file_path, "status", f"Converted video saved: {output_file}"))
    else:
        app.queue.put((file_path, "status", f"Conversion error: {err}"))


def extract_frames_from_video(file_path, interval, app):
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    out_dir = ensure_file_output_dir(file_path)
    out_pattern = os.path.join(out_dir, f"{base_name}_%04d.png")
    cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-vf",
        f"select='not(mod(n,{interval}))',setpts=N/TB",
        "-vsync",
        "vfr",
        "-f",
        "image2",
        out_pattern,
    ]
    err = run_ffmpeg_command(cmd, "Error extracting frames")
    if not err:
        app.queue.put((file_path, "status", f"Frames extracted to: {out_dir}"))
    else:
        app.queue.put((file_path, "status", f"Frame extraction error: {err}"))


def extract_audio_from_video(file_path, audio_fmt, app):
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    out_dir = ensure_file_output_dir(file_path)
    out_file = generate_unique_file_path(out_dir, base_name, "", audio_fmt)
    cmd = ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", out_file]
    err = run_ffmpeg_command(cmd, "Error extracting audio")
    if not err:
        app.queue.put((file_path, "status", f"Audio extracted: {out_file}"))
    else:
        app.queue.put((file_path, "status", f"Audio extraction error: {err}"))


def extract_gif_from_video(file_path, app):
    base_name, _ = os.path.splitext(os.path.basename(file_path))
    out_dir = ensure_file_output_dir(file_path)
    gif_file = generate_unique_file_path(out_dir, base_name, "", "gif")
    cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-vf",
        "fps=10,scale=480:-1:flags=lanczos",
        "-gifflags",
        "+transdiff",
        gif_file,
    ]
    err = run_ffmpeg_command(cmd, "Error extracting GIF")
    if not err:
        app.queue.put((file_path, "status", f"GIF extracted: {gif_file}"))
    else:
        app.queue.put((file_path, "status", f"GIF extraction error: {err}"))


def join_multiple_clips(files, options, app):
    """
    Join multiple video clips into one output file.
    'options' is a dict with keys: convert_video, output_format, keep_quality, bitrate.
    """
    out_dir = ensure_file_output_dir(files[0])
    concat_file = os.path.join(out_dir, "concat_list.txt")
    try:
        with open(concat_file, "w", encoding="utf-8") as cf:
            for f in files:
                cf.write(f"file '{f}'\n")
        output_format = options.get("output_format", "mp4")
        joined_output = os.path.join(out_dir, f"joined_output.{output_format}")
        if options.get("convert_video"):
            if not options.get("keep_quality", True):
                bitrate_str = options.get("bitrate", "").strip()
                min_bitrate_mbps = 1
                if bitrate_str.isdigit():
                    bitrate_val_mbps = int(bitrate_str)
                    if bitrate_val_mbps < min_bitrate_mbps:
                        app.queue.put(
                            (
                                files[0],
                                "status",
                                f"Provided bitrate ({bitrate_val_mbps} Mbps) is too low; using minimum {min_bitrate_mbps} Mbps.",
                            )
                        )
                        bitrate_val_mbps = min_bitrate_mbps
                    bitrate_val = f"{bitrate_val_mbps * 1000}k"
                    cmd = (
                        [
                            "ffmpeg",
                            "-f",
                            "concat",
                            "-safe",
                            "0",
                            "-i",
                            concat_file,
                        ]
                        + _encoder_opts(bitrate_val)
                        + ["-c:a", "copy", joined_output]
                    )
                else:
                    cmd = (
                        [
                            "ffmpeg",
                            "-f",
                            "concat",
                            "-safe",
                            "0",
                            "-i",
                            concat_file,
                        ]
                        + _encoder_opts()
                        + ["-c:a", "copy", joined_output]
                    )
            else:
                cmd = [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_file,
                    "-c:v",
                    "copy",
                    "-c:a",
                    "copy",
                    joined_output,
                ]
        else:
            original_ext = os.path.splitext(files[0])[1].replace(".", "")
            joined_output = os.path.join(out_dir, f"joined_output.{original_ext}")
            cmd = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file,
                "-c",
                "copy",
                joined_output,
            ]
        err = run_ffmpeg_command(cmd, "Error joining videos")
        if not err:
            app.queue.put((None, "status", f"Joined video saved to: {joined_output}"))
        else:
            app.queue.put((None, "status", f"Join error: {err}"))
    except Exception as e:
        app.queue.put((None, "status", f"Join error: {str(e)}"))
