# tests/conftest.py

import pytest
from pathlib import Path
from PIL import Image, ExifTags

@pytest.fixture
def tmp_image(tmp_path):
    """
    Creates and returns a simple JPEG with no EXIF data.
    """
    p = tmp_path / "plain.jpg"
    img = Image.new("RGB", (100, 80), color="green")
    img.save(p)
    return p

@pytest.fixture
def exif_image_factory(tmp_path):
    """
    Returns a factory that, given an EXIF Orientation code,
    writes and returns a JPEG tagged with that code.
    """
    orientation_tag = next(
        k for k, v in ExifTags.TAGS.items() if v == "Orientation"
    )

    def _factory(code: int) -> Path:
        p = tmp_path / f"exif_{code}.jpg"
        img = Image.new("RGB", (10, 10), color="blue")
        exif = img.getexif()
        exif[orientation_tag] = code
        img.save(p, exif=exif.tobytes())
        return p

    return _factory
