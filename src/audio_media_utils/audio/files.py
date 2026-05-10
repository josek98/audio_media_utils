from __future__ import annotations

"""Helpers for file-level audio operations."""

from pathlib import Path
from mutagen import File

_YTDLP_TEMPORARY_EXTENSIONS = (".part", ".temp", ".ytdl")
_YTDLP_INTERMEDIATE_EXTENSIONS = (
    ".webm",
    ".m4a",
    ".mp4",
    ".mkv",
    ".opus",
    ".ogg",
    ".wav",
    ".webp",
    ".jpg",
    ".jpeg",
    ".png",
)


def read_audio_duration(path: str | Path) -> float:
    """Return audio duration in seconds."""
    file_path = Path(path)
    audio = File(file_path)
    if audio is None or not hasattr(audio, 'info') or audio.info is None:
        raise ValueError(f"Unable to read duration from {file_path}")

    return float(audio.info.length)


def cleanup_ytdlp_artifacts_for_target(path: str | Path) -> list[Path]:
    """Delete yt-dlp artifacts clearly associated with a final target file.

    Parameters
    ----------
    path : str | Path
        Final expected download target.

    Returns
    -------
    list[Path]
        Deleted artifact paths.
    """
    target_path = Path(path)
    deleted_paths: list[Path] = []

    candidate_paths = [
        target_path.parent / f"{target_path.name}{suffix}"
        for suffix in _YTDLP_TEMPORARY_EXTENSIONS
    ]
    candidate_paths.extend(
        target_path.with_suffix(suffix)
        for suffix in _YTDLP_INTERMEDIATE_EXTENSIONS
    )

    seen_paths: set[Path] = set()
    for candidate_path in candidate_paths:
        if candidate_path == target_path or candidate_path in seen_paths:
            continue

        seen_paths.add(candidate_path)
        if not candidate_path.exists():
            continue

        candidate_path.unlink()
        deleted_paths.append(candidate_path)

    return deleted_paths
