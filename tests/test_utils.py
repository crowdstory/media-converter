# tests/test_utils.py

import pytest
from media_utils.utils import get_media_mimetype, MimetypeError

def test_get_media_mimetype_known_extension():
    # PNG file should return image/png
    mime = get_media_mimetype("example.png")
    assert mime == "image/png"

def test_get_media_mimetype_unknown_extension():
    # Unknown extension returns None
    mime = get_media_mimetype("file.unknown_ext")
    assert mime is None

def test_get_media_mimetype_injection_success():
    # Inject a custom guess_fn that returns a specific mime
    def fake_guess(path):
        assert path == "test.mp4"
        return ("video/mp4", None)
    mime = get_media_mimetype("test.mp4", guess_fn=fake_guess)
    assert mime == "video/mp4"

def test_get_media_mimetype_injection_none_success():
    # Inject a custom guess_fn that returns (None, encoding)
    def fake_guess(path):
        return (None, "utf-8")
    mime = get_media_mimetype("anything", guess_fn=fake_guess)
    assert mime is None

def test_get_media_mimetype_guess_fn_raises():
    # Inject a guess_fn that raises to trigger MimetypeError
    def broken_guess(path):
        raise RuntimeError("boom")
    with pytest.raises(MimetypeError) as exc:
        get_media_mimetype("whatever", guess_fn=broken_guess)
    msg = str(exc.value)
    assert "Error guessing MIME type for 'whatever': boom" in msg
