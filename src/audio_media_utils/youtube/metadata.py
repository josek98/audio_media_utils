from __future__ import annotations

"""Helpers for retrieving YouTube video metadata through yt-dlp."""

import json

from audio_media_utils.exceptions import YtDlpError
from audio_media_utils.youtube.models import VideoMetadata
from audio_media_utils.youtube.ytdlp_runner import run_ytdlp


def fetch_video_metadata(url: str, *, cookies_file: str | None = None, timeout_seconds: int = 120) -> VideoMetadata:
    """Fetch normalized metadata for a YouTube video URL.

    Parameters
    ----------
    url : str
        Video URL to inspect with ``yt-dlp``.
    cookies_file : str | None, default=None
        Optional cookies file passed to ``yt-dlp`` for authenticated access.
    timeout_seconds : int, default=120
        Maximum command execution time.

    Returns
    -------
    VideoMetadata
        Normalized subset of fields commonly used by download services.

    Raises
    ------
    YtDlpError
        If ``yt-dlp`` fails, returns malformed JSON, or omits the video id.
    """
    command = ["yt-dlp"]

    if cookies_file is not None:
        command.extend(["--cookies", cookies_file])

    command.extend(
        [
            "--dump-single-json",
            "--skip-download",
            "--no-warnings",
            "--no-playlist",
            url,
        ]
    )

    result = run_ytdlp(command, timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise YtDlpError(
            "Could not fetch video metadata with yt-dlp. "
            f"returncode={result.returncode} reason={result.reason!r} stderr={result.stderr.strip()}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise YtDlpError("yt-dlp returned invalid JSON while fetching video metadata") from error

    video_id = data.get("id")
    if not video_id:
        raise YtDlpError(f"yt-dlp did not return a video id for {url}")

    return VideoMetadata(
        video_id=video_id,
        url=url,
        title=data.get("title"),
        upload_date=data.get("upload_date"),
        duration_seconds=data.get("duration"),
        live_status=data.get("live_status"),
        was_live=bool(data.get("was_live") or data.get("is_live")),
        release_timestamp=data.get("release_timestamp") or data.get("timestamp"),
    )
