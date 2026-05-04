from __future__ import annotations

"""Helpers for audio downloads through yt-dlp."""

from audio_media_utils.youtube.models import DownloadOptions, DownloadResult


def download_audio(url: str, *, options: DownloadOptions) -> DownloadResult:
    """Download audio from ``url`` using the provided options.

    This is a placeholder implementation that will be filled in next.
    """
    return DownloadResult(success=False, url=url, error_reason="not_implemented")
