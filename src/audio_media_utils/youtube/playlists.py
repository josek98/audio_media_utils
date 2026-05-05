from __future__ import annotations

"""Helpers for playlist inspection and expansion."""

import json

from audio_media_utils.exceptions import YtDlpError
from audio_media_utils.youtube.models import PlaylistEntry
from audio_media_utils.youtube.ytdlp_runner import run_ytdlp


def expand_playlist(url: str, *, flat: bool = True) -> list[PlaylistEntry]:
    """Expand a YouTube playlist URL into typed entries.

    Parameters
    ----------
    url : str
        Playlist URL to inspect with ``yt-dlp``.
    flat : bool, default=True
        Whether to request flat playlist entries instead of full metadata.

    Returns
    -------
    list[PlaylistEntry]
        Playlist entries with valid video identifiers.

    Raises
    ------
    YtDlpError
        If ``yt-dlp`` fails or returns malformed JSON output.
    """
    command = [
        "yt-dlp",
        "--dump-single-json",
    ]
    if flat:
        command.append("--flat-playlist")
    command.append("--no-warnings")
    command.append(url)

    result = run_ytdlp(command, timeout_seconds=120)
    if result.returncode != 0:
        raise YtDlpError(
            "Could not expand playlist with yt-dlp. "
            f"returncode={result.returncode} reason={result.reason!r} stderr={result.stderr.strip()}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise YtDlpError("yt-dlp returned invalid JSON while expanding playlist") from error

    entries = data.get("entries", []) or []
    playlist_entries: list[PlaylistEntry] = []

    for item in entries:
        if not isinstance(item, dict):
            continue

        video_id = item.get("id")
        if not video_id:
            continue

        playlist_entries.append(
            PlaylistEntry(
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=item.get("title"),
            )
        )

    return playlist_entries
