import subprocess
import logging

logger = logging.getLogger(__name__)


def run_ffmpeg_command(cmd, error_msg):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"{error_msg}: {e}")
        return str(e)
    return None


def is_gpu_available():
    try:
        result = subprocess.run(
            ["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False
