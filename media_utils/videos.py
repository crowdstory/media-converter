# videos.py

from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from .ffmpeg_runner import FFmpegRunner, FFmpegError

class VideoUtilsError(Exception):
    """Base exception for video utilities."""
    pass

class ThumbnailError(VideoUtilsError):
    """Raised when video thumbnail creation fails."""
    pass

class GIFError(VideoUtilsError):
    """Raised when GIF preview creation fails."""
    pass

class HLSError(VideoUtilsError):
    """Raised when HLS conversion fails."""
    pass


RESOLUTION_MAP: Dict[str, Tuple[int,int]] = {
    "8k":   (7680, 4320),
    "4k":   (3840, 2160),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "540p": (960,  540),
    "480p": (854,  480),
    "360p": (640,  360),
    "240p": (426,  240),
    "144p": (256,  144),
}

def _probe_stream(
    input_path: Path,
    runner: FFmpegRunner
) -> Tuple[int,int,int]:
    """
    Probe width, height and raw rotation (may be -90, 90, 180, -180).
    Returns (w, h, rotate). On any error returns (0,0,0).
    """
    try:
        info = runner.probe(input_path)
        vs = next(s for s in info["streams"] if s.get("codec_type") == "video")
        w = int(vs["width"])
        h = int(vs["height"])
        tags = vs.get("tags", {})
        if "rotate" in tags:
            return w, h, int(tags["rotate"])
        for sd in vs.get("side_data_list", []):
            if "rotation" in sd:
                return w, h, int(sd["rotation"])
        return w, h, 0
    except Exception:
        return 0, 0, 0


def create_video_thumbnail(
    input_path: str,
    output_path: str,
    t: float = 1.0,
    size: Optional[Tuple[int,int]] = None,
    auto_rotate: bool = False,
    *,
    runner: FFmpegRunner = FFmpegRunner(),
):
    """
    Extract a single frame as a thumbnail at time `t`, optionally auto-rotated
    and resized/cropped to `size`. Raises ThumbnailError on any failure.
    """
    inp = Path(input_path)
    out = Path(output_path)

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ThumbnailError(f"Could not create output directory '{out.parent}': {e}") from e

    _, _, raw = _probe_stream(inp, runner)

    vf: List[str] = []
    if auto_rotate and raw in (-90, 90, 180, -180):
        if raw == -90:
            vf.append("transpose=1")
        elif raw == 90:
            vf.append("transpose=2")
        else:
            vf.append("transpose=1,transpose=1")
    if size:
        w, h = size
        vf.append(f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}")

    cmd = [
        "ffmpeg", "-y", "-noautorotate",
        "-ss", str(t),
        "-i", str(inp),
        "-map_metadata", "-1", "-map_metadata:s:v:0", "-1",
    ]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += [
        "-frames:v", "1",
        "-c:v", "mjpeg",
        "-q:v", "2",
        "-an",
        str(out),
    ]

    try:
        runner.run(cmd)
    except FFmpegError as e:
        raise ThumbnailError(f"Thumbnail creation failed: {e}") from e


def create_gif_preview(
    input_path: str,
    output_path: str,
    start: float = 0,
    duration: float = 5,
    fps: int = 10,
    size: Optional[Tuple[int,int]] = None,
    auto_rotate: bool = False,
    *,
    runner: FFmpegRunner = FFmpegRunner()
):
    """
    Create an optimized GIF preview (two-pass) of a clip from `start` for `duration` seconds.
    Raises GIFError on any failure.
    """
    inp = Path(input_path)
    out = Path(output_path)

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise GIFError(f"Could not create output directory '{out.parent}': {e}") from e

    _, _, raw = _probe_stream(inp, runner)

    vf_parts: List[str] = []
    if auto_rotate and raw in (-90, 90, 180, -180):
        if raw == -90:
            vf_parts.append("transpose=1")
        elif raw == 90:
            vf_parts.append("transpose=2")
        else:
            vf_parts.append("transpose=1,transpose=1")
    vf_parts.append(f"fps={fps}")
    if size:
        w, h = size
        vf_parts.append(f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}")
    vf = ",".join(vf_parts)

    palette = out.with_suffix(".png")

    cmd1 = [
        "ffmpeg", "-y", "-noautorotate",
        "-ss", str(start), "-t", str(duration),
        "-i", str(inp),
        "-map_metadata", "-1", "-map_metadata:s:v:0", "-1",
        "-vf", f"{vf},palettegen",
        str(palette),
    ]
    try:
        runner.run(cmd1)
    except FFmpegError as e:
        raise GIFError(f"Palette generation failed: {e}") from e

    cmd2 = [
        "ffmpeg", "-y", "-noautorotate",
        "-ss", str(start), "-t", str(duration),
        "-i", str(inp),
        "-i", str(palette),
        "-map_metadata", "-1", "-map_metadata:s:v:0", "-1",
        "-filter_complex", f"[0:v]{vf}[x];[x][1:v]paletteuse",
        "-loop", "0",
        str(out),
    ]
    try:
        runner.run(cmd2)
    except FFmpegError as e:
        raise GIFError(f"GIF creation failed: {e}") from e
    finally:
        try:
            palette.unlink()
        except OSError:
            pass


def convert_to_hls(
    input_path: str,
    output_dir: str,
    base_name: str,
    segment_time: int = 10,
    resolution: Optional[str] = None,
    auto_rotate: bool = False,
    *,
    runner: FFmpegRunner = FFmpegRunner()
):
    """
    Convert to HLS (playlist + segments), with optional auto-rotate
    and named-resolution downscaling. Raises HLSError on any failure.
    """
    inp = Path(input_path)
    out_dir = Path(output_dir)

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HLSError(f"Could not create output directory '{out_dir}': {e}") from e

    playlist = out_dir / f"{base_name}.m3u8"
    orig_w, orig_h, raw = _probe_stream(inp, runner)

    vf_filters: List[str] = []
    if auto_rotate and raw in (-90, 90, 180, -180):
        if raw == -90:
            vf_filters.append("transpose=1")
            src_w, src_h = orig_h, orig_w
        elif raw == 90:
            vf_filters.append("transpose=2")
            src_w, src_h = orig_h, orig_w
        else:
            vf_filters.append("transpose=1,transpose=1")
            src_w, src_h = orig_h, orig_w
    else:
        src_w, src_h = orig_w, orig_h

    if resolution:
        key = resolution.lower()
        if key not in RESOLUTION_MAP:
            raise ValueError(f"Unknown resolution '{resolution}'. Valid: {list(RESOLUTION_MAP)}")
        tgt_w, tgt_h = RESOLUTION_MAP[key]
        if src_h > src_w:
            tgt_w, tgt_h = tgt_h, tgt_w
        if src_w > tgt_w or src_h > tgt_h:
            vf_filters.append(
                f"scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2"
            )

    cmd = [
        "ffmpeg", "-y", "-noautorotate",
        "-i", str(inp),
        "-map_metadata", "-1",
        "-map_metadata:s:v:0", "-1",
    ]
    if vf_filters:
        cmd += ["-vf", ",".join(vf_filters)]
        cmd += ["-metadata:s:v:0", "rotate=0", "-c:v", "libx264", "-c:a", "aac", "-strict", "-2"]
    else:
        cmd += ["-c", "copy", "-metadata:s:v:0", "rotate=0"]

    cmd += [
        "-start_number", "0",
        "-hls_time", str(segment_time),
        "-hls_list_size", "0",
        "-hls_segment_filename", str(out_dir / f"{base_name}%d.ts"),
        "-f", "hls",
        str(playlist),
    ]

    try:
        runner.run(cmd)
    except FFmpegError as e:
        raise HLSError(f"HLS conversion failed: {e}") from e
