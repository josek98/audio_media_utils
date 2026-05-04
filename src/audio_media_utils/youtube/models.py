from __future__ import annotations

"""Typed models used by the YouTube helpers."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PlaylistEntry:
    """Single entry extracted from a playlist."""

    video_id: str
    url: str
    title: str | None = None


@dataclass(frozen=True)
class VideoMetadata:
    """Subset of metadata commonly returned by yt-dlp."""

    video_id: str | None
    url: str
    title: str | None = None
    upload_date: str | None = None
    duration_seconds: int | None = None
    live_status: str | None = None
    was_live: bool = False
    release_timestamp: int | None = None


@dataclass(frozen=True)
class DownloadOptions:
    """Options used when downloading audio with yt-dlp."""

    output_template: str
    audio_format: str = "mp3"
    audio_quality: str | None = None
    archive_file: Path | None = None
    cookies_file: Path | None = None
    timeout_seconds: int = 120
    extra_args: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DownloadResult:
    """Result of a download attempt."""

    success: bool
    url: str
    file_path: Path | None = None
    title: str | None = None
    already_downloaded: bool = False
    stdout: str = ""
    stderr: str = ""
    error_reason: str | None = None
