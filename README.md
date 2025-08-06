# media_utils

A Python library for media processing: create image and video thumbnails, generate GIF previews, convert videos to HLS streams, and detect file MIME types. Built on top of FFmpeg and Pillow, with a clean, testable base code.

---

## Features

- **MIME type detection** via file extension.  
- **Image thumbnails** with exact size, centered crop, EXIF‐aware.  
- **EXIF orientation** reader for arbitrary JPEGs.  
- **Video thumbnails** (single frame), with optional auto‐rotation & resizing.  
- **GIF previews** (two‐pass palette), optional auto‐rotate & resize.  
- **HLS conversion** (m3u8 + TS segments), named‐resolution downscaling & auto‐rotate.  
- **100% unit‐tested** logic, with injectable FFmpeg runner for easy stubbing.  

---

## Installation

```bash
# from source
git clone https://github.com/crowdstory/media-converter
cd media_utils
pip install -e .
```

Requires FFmpeg installed on your PATH.

## Quickstart

Detect MIME type
```python
from media_utils.utils import get_media_mimetype

print(get_media_mimetype("foo.png"))   # → "image/png"
print(get_media_mimetype("bar.unknown"))  # → None
```

Image utilities
```python
from media_utils.images import create_image_thumbnail, get_image_orientation

# 1) Thumbnail (320×240), auto‐centered crop
create_image_thumbnail(
    "photos/input.jpg",
    "photos/thumb.jpg",
    size=(320,240)
)

# 2) EXIF orientation
deg = get_image_orientation("photos/input.jpg")
print(f"Needs rotation: {deg}°")
```

Video utilities
```python

from media_utils.videos import (
    create_video_thumbnail,
    create_gif_preview,
    convert_to_hls
)

# 1) Video thumbnail @ t=2.5s, size=200×150, auto‐rotate
create_video_thumbnail(
    "videos/clip.mp4",
    "videos/clip-thumb.jpg",
    t=2.5,
    size=(200,150),
    auto_rotate=True
)

# 2) GIF preview: 5s clip @ start=1s, 5FPS, 320×240
create_gif_preview(
    "videos/clip.mp4",
    "videos/clip-preview.gif",
    start=1,
    duration=5,
    fps=5,
    size=(320,240),
    auto_rotate=True
)

# 3) HLS conversion: 10s segments, downscale to 480p, auto‐rotate
convert_to_hls(
    "videos/clip.mp4",
    "videos/hls-output",
    base_name="clip-480p",
    segment_time=10,
    resolution="480p",
    auto_rotate=True
)
# → writes:
#   videos/hls-output/clip-480p.m3u8
#   videos/hls-output/clip-480p0.ts, clip-480p1.ts, …
```

### API Reference

#### `get_media_mimetype(path: str, *, guess_fn=...) → Optional[str]`
- Guesses MIME type by extension.  
- Raises `MimetypeError` if the underlying guess function throws.

#### `create_image_thumbnail(
    input_path, 
    output_path, 
    size=(320,240), 
    *, 
    open_image=…, 
    fit_image=…
) → None`
- Loads via PIL, crops to the exact `size` with Lanczos filter.  
- Raises `ThumbnailError` on directory creation, open, resize, or save failures.  
- Injection points (`open_image`, `fit_image`) make it fully unit-testable.

#### `get_image_orientation(path: str, *, open_image=...) → int`
- Reads EXIF Orientation tag and returns one of `0 | 90 | 180 | 270`.  
- Raises `OrientationError` on I/O or EXIF-parsing failures.

#### `create_video_thumbnail(
    input_path, 
    output_path, 
    t=1.0, 
    size=None, 
    auto_rotate=False, 
    *, 
    runner=FFmpegRunner()
) → None`
- Extracts a single frame via FFmpeg (`mjpeg`) at time `-ss t`.  
- Optional `-vf transpose…` for auto-rotation and `scale/crop` for resizing.  
- Raises `ThumbnailError` if FFmpeg fails.

#### `create_gif_preview(
    input_path, 
    output_path, 
    start=0, 
    duration=5, 
    fps=10, 
    size=None, 
    auto_rotate=False, 
    *, 
    runner=…
) → None`
- Two-pass GIF: first `palettegen`, then `paletteuse`.  
- Auto-rotation and resize/crop via `-vf`.  
- Cleans up the intermediate palette file.  
- Raises `GIFError` on any step failure.

#### `convert_to_hls(
    input_path, 
    output_dir, 
    base_name, 
    segment_time=10, 
    resolution=None, 
    auto_rotate=False, 
    *, 
    runner=…
) → None`
- Outputs `{base_name}.m3u8` plus `{base_name}%d.ts` segments.  
- Supports auto-rotate and named-resolution downscaling (via `RESOLUTION_MAP`).  
- Raises `HLSError` on directory creation or FFmpeg errors.

#### `FFmpegRunner`
- **`.probe(path: Path) → Dict`** wraps `ffmpeg.probe`; raises `FFmpegError`.  
- **`.run(cmd: List[str]) → None`** wraps `subprocess.run(..., check=True)`; raises `FFmpegError`.  


## Tests
We inject stubs for PIL and FFmpeg, so you can achieve 100% coverage without real media. All tests live in tests/:

```bash
pytest --maxfail=1 --disable-warnings --cov=media_utils --cov-report=term-missing

============================================ tests coverage =============================================
___________________________ coverage: platform linux, python 3.11.13-final-0 ____________________________

Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
media_utils/__init__.py            4      0   100%
media_utils/ffmpeg_runner.py      17      0   100%
media_utils/images.py             58      0   100%
media_utils/utils.py              10      0   100%
media_utils/videos.py            127      0   100%
------------------------------------------------------------
TOTAL                            216      0   100%
```

## Licence
MIT © Crowdstory