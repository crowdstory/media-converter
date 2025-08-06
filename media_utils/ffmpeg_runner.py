# ffmpeg_runner.py

import subprocess
import ffmpeg
from pathlib import Path
from typing import List, Dict, Any

class FFmpegError(Exception):
    """Raised for errors during FFmpeg operations."""
    pass

class FFmpegRunner:
    """
    Encapsulates all FFmpeg interactions for probing and running commands.
    """

    def probe(self, path: Path) -> Dict[str, Any]:
        """
        Run ffprobe on the given file and return its metadata dict.
        Raises FFmpegError on failure.
        """
        try:
            return ffmpeg.probe(str(path))
        except Exception as e:
            raise FFmpegError(f"probe failed for {path}: {e}") from e

    def run(self, cmd: List[str]) -> None:
        """
        Run the given FFmpeg command via subprocess.
        Raises FFmpegError on non-zero exit.
        """
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"ffmpeg cmd failed: {' '.join(cmd)}") from e
