from __future__ import annotations

"""Helpers for searching YouTube videos through yt-dlp."""

import json
from pathlib import Path

from audio_media_utils.exceptions import YtDlpError
from audio_media_utils.youtube.models import VideoMetadata
from audio_media_utils.youtube.ytdlp_runner import run_ytdlp


def _build_video_metadata_from_search_entry(entry: dict, *, fallback_url: str | None = None) -> VideoMetadata | None:
    """Convert one yt-dlp search entry into ``VideoMetadata`` when possible."""
    video_id = entry.get("id")
    if not video_id:
        return None

    return VideoMetadata(
        video_id=video_id,
        url=entry.get("webpage_url") or fallback_url or f"https://www.youtube.com/watch?v={video_id}",
        title=entry.get("title"),
        upload_date=entry.get("upload_date"),
        duration_seconds=entry.get("duration"),
        live_status=entry.get("live_status"),
        was_live=bool(entry.get("was_live") or entry.get("is_live")),
        release_timestamp=entry.get("release_timestamp") or entry.get("timestamp"),
    )


def search_youtube_videos(
    query: str,
    *,
    max_results: int = 10,
    cookies_file: str | Path | None = None,
    timeout_seconds: int = 120,
) -> list[VideoMetadata]:
    """Search YouTube and return normalized metadata for the top results.

    Parameters
    ----------
    query : str
        Search query sent to ``yt-dlp`` using ``ytsearch``.
    max_results : int, default=10
        Maximum number of results requested from YouTube.
    cookies_file : str | Path | None, default=None
        Optional cookies file passed to ``yt-dlp`` for authenticated access.
    timeout_seconds : int, default=120
        Maximum command execution time.

    Returns
    -------
    list[VideoMetadata]
        Search results in the order returned by ``yt-dlp``.

    Raises
    ------
    ValueError
        If ``max_results`` is not positive.
    YtDlpError
        If ``yt-dlp`` fails or returns malformed JSON.
    """
    if max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    command = ["yt-dlp"]
    if cookies_file is not None:
        command.extend(["--cookies", str(cookies_file)])

    command.extend(
        [
            "--dump-single-json",
            "--no-warnings",
            f"ytsearch{max_results}:{query}",
        ]
    )

    result = run_ytdlp(command, timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise YtDlpError(
            "Could not search YouTube videos with yt-dlp. "
            f"returncode={result.returncode} reason={result.reason!r} stderr={result.stderr.strip()}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise YtDlpError("yt-dlp returned invalid JSON while searching YouTube videos") from error

    entries = data.get("entries", []) or []
    search_results: list[VideoMetadata] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue

        video_metadata = _build_video_metadata_from_search_entry(entry)
        if video_metadata is None:
            continue

        search_results.append(video_metadata)

    return search_results
