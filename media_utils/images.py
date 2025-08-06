# images.py

from PIL import Image, ExifTags, ImageOps, UnidentifiedImageError
from pathlib import Path
from typing import Tuple, Callable, Any

class ThumbnailError(Exception):
    """Raised when thumbnail creation fails."""
    pass

class OrientationError(Exception):
    """Raised when reading image orientation fails."""
    pass

def create_image_thumbnail(
    input_path: str,
    output_path: str,
    size: Tuple[int,int] = (320, 240),
    *,
    open_image: Callable[[str], Any] = Image.open,
    fit_image:  Callable[..., Any] = ImageOps.fit
):
    """
    Create a thumbnail for an image file, exact size, centered & cropped,
    with robust error handling.

    Args:
      input_path:    Path to source image.
      output_path:   Where to save thumbnail.
      size:          (width, height) of the final thumbnail.

    Keyword Args:
      open_image:    Callable to open an image (injected for testing).
      fit_image:     Callable to resize+crop an image (injected for testing).

    Raises:
      ThumbnailError on any failure.
    """
    inp = Path(input_path)
    out = Path(output_path)

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ThumbnailError(f"Could not create output directory '{out.parent}': {e}") from e

    try:
        img = open_image(str(inp))
    except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
        raise ThumbnailError(f"Cannot open image '{inp}': {e}") from e
    except Exception as e:
        raise ThumbnailError(f"Unexpected error opening image '{inp}': {e}") from e

    # 3) Resize & center-crop to exact size
    try:
        thumb = fit_image(img, size, Image.LANCZOS, centering=(0.5, 0.5))
    except Exception as e:
        raise ThumbnailError(f"Error resizing/cropping image to {size}: {e}") from e

    # 4) Save thumbnail
    try:
        thumb.save(out)
    except Exception as e:
        raise ThumbnailError(f"Could not save thumbnail to '{out}': {e}") from e


def get_image_orientation(
    path: str,
    *,
    open_image: Callable[[str], Any] = Image.open
) -> int:
    """
    Read the EXIF Orientation tag and return the degrees needed 
    to rotate the image for correct viewing.

    Returns:
      0: no rotation needed or EXIF tag absent
      90: rotate 90° clockwise
      180: rotate 180°
      270: rotate 270° clockwise

    Keyword Args:
      open_image: Callable to open an image (injected for testing).

    Raises:
      OrientationError on I/O or EXIF parsing failures.
    """

    try:
        img = open_image(path)
    except FileNotFoundError as e:
        raise OrientationError(f"Input file not found: '{path}'") from e
    except UnidentifiedImageError as e:
        raise OrientationError(f"Cannot identify image file: '{path}'") from e
    except OSError as e:
        raise OrientationError(f"I/O error opening image '{path}': {e}") from e
    except Exception as e:
        raise OrientationError(f"Unexpected error opening image '{path}': {e}") from e

    try:
        exif = img._getexif() or {}
    except Exception as e:
        raise OrientationError(f"Error reading EXIF from '{path}': {e}") from e
    finally:
        try:
            img.close()
        except Exception:
            pass

    if not exif:
        return 0

    try:
        orientation_tag = next(
            tag for tag, name in ExifTags.TAGS.items()
            if name == "Orientation"
        )
    except Exception:
        return 0

    try:
        raw = exif.get(orientation_tag, 1)
    except Exception as e:
        raise OrientationError(f"Error fetching Orientation tag value: {e}") from e

    return {
        1: 0,
        2: 0,
        3: 180,
        4: 180,
        5: 270,
        6: 90,
        7: 90,
        8: 270
    }.get(raw, 0)
