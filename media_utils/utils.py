# utils.py

import mimetypes
from typing import Optional, Tuple, Callable

class MimetypeError(Exception):
    """Raised when determining MIME type fails."""
    pass

def get_media_mimetype(
    path: str,
    *,
    guess_fn: Callable[[str], Tuple[Optional[str], Optional[str]]] = mimetypes.guess_type
) -> Optional[str]:
    """
    Return the MIME type (e.g., "image/png" or "video/mp4") for a given file path,
    or None if it cannot be determined.

    Keyword Args:
      guess_fn:  Function to use for guessing the type (injected for testing).

    Raises:
      MimetypeError: if the guess_fn itself raises an exception.
    """
    try:
        mime, _ = guess_fn(path)
    except Exception as e:
        raise MimetypeError(f"Error guessing MIME type for '{path}': {e}") from e

    return mime
