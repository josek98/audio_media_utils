from __future__ import annotations

"""Helpers for building safe music file paths."""

import re
import unicodedata
from pathlib import Path

_INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*\n\r\t]+')
_MULTISPACE_CHARS = re.compile(r'\s+')
_MULTI_UNDERSCORES = re.compile(r'_+')


def sanitize_path_component(value: str) -> str:
    """Normalize a filesystem path component for music libraries."""
    normalized = unicodedata.normalize('NFKC', value)
    cleaned = _INVALID_PATH_CHARS.sub('_', normalized)
    cleaned = _MULTISPACE_CHARS.sub(' ', cleaned)
    cleaned = _MULTI_UNDERSCORES.sub('_', cleaned)
    cleaned = cleaned.strip(' .')
    return cleaned or 'Unknown'


def build_music_path(
    base_dir: str | Path,
    *,
    artist: str,
    album: str,
    title: str,
    track_number: int | None = None,
    suffix: str = '.mp3',
) -> Path:
    """Build a normalized destination path for a tagged music file."""
    root = Path(base_dir)
    safe_artist = sanitize_path_component(artist)
    safe_album = sanitize_path_component(album)
    safe_title = sanitize_path_component(title)
    prefix = f'{track_number:02d} - ' if track_number is not None else ''
    return root / safe_artist / safe_album / f'{prefix}{safe_title}{suffix}'
