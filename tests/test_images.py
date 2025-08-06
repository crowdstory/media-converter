# tests/test_images.py

import pytest
from pathlib import Path
from PIL import UnidentifiedImageError, Image
from media_utils.images import (
    create_image_thumbnail,
    ThumbnailError,
    get_image_orientation,
    OrientationError
)

def test_create_thumbnail_success(tmp_image, tmp_path):
    out = tmp_path / "thumb.jpg"
    create_image_thumbnail(str(tmp_image), str(out), size=(50, 60))
    thumb = Image.open(out)
    assert thumb.size == (50, 60)

def test_create_thumbnail_missing_input(tmp_path):
    inp = tmp_path / "missing.jpg"
    out = tmp_path / "thumb.jpg"
    with pytest.raises(ThumbnailError) as exc:
        create_image_thumbnail(str(inp), str(out))
    assert "Cannot open image" in str(exc.value)

def test_create_thumbnail_resize_error(tmp_image, tmp_path):
    # simulate fit failure
    def fake_fit(img, size, filter, centering):
        raise ValueError("resize failed")
    out = tmp_path / "thumb.jpg"
    with pytest.raises(ThumbnailError) as exc:
        create_image_thumbnail(
            str(tmp_image),
            str(out),
            size=(20, 20),
            fit_image=fake_fit
        )
    assert "Error resizing/cropping" in str(exc.value)

def test_create_thumbnail_save_error(tmp_image, tmp_path):
    # simulate save failure
    class DummyThumb:
        def save(self, path):
            raise IOError("disk full")
    def fake_fit(img, size, filter, centering):
        return DummyThumb()

    out = tmp_path / "thumb.jpg"
    with pytest.raises(ThumbnailError) as exc:
        create_image_thumbnail(
            str(tmp_image),
            str(out),
            size=(20, 20),
            fit_image=fake_fit
        )
    assert "Could not save thumbnail" in str(exc.value)


def test_get_orientation_no_exif(tmp_image):
    deg = get_image_orientation(str(tmp_image))
    assert deg == 0

def test_get_orientation_missing_file(tmp_path):
    with pytest.raises(OrientationError) as exc:
        get_image_orientation(str(tmp_path / "nope.jpg"))
    assert "Input file not found" in str(exc.value)

def test_get_orientation_bad_image(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    with pytest.raises(OrientationError):
        get_image_orientation(str(bad))

def test_get_orientation_read_exif_error(monkeypatch):
    class FakeImg:
        def _getexif(self):
            raise RuntimeError("parse error")
        def close(self): pass

    def fake_open(path):
        return FakeImg()

    with pytest.raises(OrientationError) as exc:
        get_image_orientation("ignored.jpg", open_image=fake_open)
    assert "Error reading EXIF" in str(exc.value)

def test_get_orientation_open_io_error():
    def fake_open(path):
        raise OSError("disk error")
    with pytest.raises(OrientationError) as exc:
        get_image_orientation("any.jpg", open_image=fake_open)
    assert "I/O error opening image" in str(exc.value)

@pytest.mark.parametrize("code,expected", [
    (1, 0), (2, 0), (3, 180), (4, 180),
    (5, 270), (6, 90), (7, 90), (8, 270), (999, 0)
])
def test_get_orientation_mapping(code, expected, exif_image_factory):
    path = exif_image_factory(code)
    deg = get_image_orientation(str(path))
    assert deg == expected

def test_create_thumbnail_mkdir_failure(tmp_image, tmp_path, monkeypatch):
    # Arrange: stub Path.mkdir to raise
    from pathlib import Path
    def fake_mkdir(self, *args, **kwargs):
        raise OSError("permission denied")
    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    # Act & Assert
    out = tmp_path / "nested" / "thumb.jpg"
    with pytest.raises(ThumbnailError) as exc:
        create_image_thumbnail(str(tmp_image), str(out), size=(50, 50))
    assert "Could not create output directory" in str(exc.value)

def test_create_thumbnail_unexpected_open_error(tmp_image, tmp_path):
    # Arrange
    out = tmp_path / "thumb.jpg"
    def fake_open(path):
        raise ValueError("boom")

    # Act & Assert
    with pytest.raises(ThumbnailError) as exc:
        create_image_thumbnail(
            str(tmp_image),
            str(out),
            (50, 50),
            open_image=fake_open
        )
    msg = str(exc.value)
    assert "Unexpected error opening image" in msg
    assert "boom" in msg

def test_get_orientation_unexpected_open_error():
    # Stub open_image to raise an unexpected exception
    def fake_open(path):
        raise ValueError("oops")

    with pytest.raises(OrientationError) as exc:
        get_image_orientation("dummy.jpg", open_image=fake_open)

    msg = str(exc.value)
    assert "Unexpected error opening image 'dummy.jpg': oops" in msg

def test_get_orientation_close_raises_and_is_suppressed():
    # Prepare a dummy image whose _getexif returns empty, but close() raises
    class DummyImg:
        def __init__(self):
            pass
        def _getexif(self):
            return {}  # no EXIF data
        def close(self):
            raise RuntimeError("close failed")

    # Stub open_image to return our DummyImg
    def fake_open(path):
        return DummyImg()

    # Should return 0 (no orientation) and not propagate the close error
    result = get_image_orientation("ignored.jpg", open_image=fake_open)
    assert result == 0

def test_get_orientation_tag_iteration_exception(monkeypatch):
    # 1) Stub a dummy image with non-empty EXIF
    class DummyImg:
        def _getexif(self):
            return {274: 6}  # orientation tag present but we won't get that far
        def close(self):
            pass

    def fake_open(path):
        return DummyImg()

    # 2) Monkey‐patch ExifTags.TAGS to None so `.items()` raises
    import media_utils.images as imgs
    monkeypatch.setattr(imgs.ExifTags, 'TAGS', None)

    # 3) Call and assert we get 0 (fallback on exception)
    deg = imgs.get_image_orientation("ignored.jpg", open_image=fake_open)
    assert deg == 0

def test_get_orientation_fetch_error(monkeypatch):
    # Dummy EXIF dict that is non-empty but raises on .get()
    class BadExif(dict):
        def __init__(self):
            super().__init__({999: 'x'})  # ensure truthy so code skips the empty-exif return
        def get(self, key, default=None):
            raise RuntimeError("fetch error")

    # Dummy image whose _getexif returns our BadExif
    class DummyImg:
        def _getexif(self):
            return BadExif()
        def close(self):
            pass

    # Stub open_image to return the dummy image
    def fake_open(path):
        return DummyImg()

    # Now this should hit the exif.get exception branch
    with pytest.raises(OrientationError) as exc:
        get_image_orientation("ignored.jpg", open_image=fake_open)

    assert "Error fetching Orientation tag value: fetch error" in str(exc.value)

