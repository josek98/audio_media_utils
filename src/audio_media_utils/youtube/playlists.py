from __future__ import annotations

"""Helpers for playlist inspection and expansion."""

from audio_media_utils.youtube.models import PlaylistEntry


def expand_playlist(url: str, *, flat: bool = True) -> list[PlaylistEntry]:
    """Expand a playlist URL into entries.

    This is a placeholder implementation that will be filled in next.
    """
    _ = (url, flat)
    return []
