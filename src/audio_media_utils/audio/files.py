from __future__ import annotations

"""Helpers for file-level audio operations."""

from pathlib import Path
from mutagen import File


def read_audio_duration(path: str | Path) -> float:
    """Return audio duration in seconds."""
    file_path = Path(path)
    audio = File(file_path)
    if audio is None or not hasattr(audio, 'info') or audio.info is None:
        raise ValueError(f"Unable to read duration from {file_path}")

    return float(audio.info.length)
