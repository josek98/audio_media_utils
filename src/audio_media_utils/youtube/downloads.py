from __future__ import annotations

"""Helpers for audio downloads through yt-dlp."""

from pathlib import Path

from audio_media_utils.exceptions import YtDlpError
from audio_media_utils.youtube.models import DownloadOptions, DownloadResult
from audio_media_utils.youtube.ytdlp_runner import run_ytdlp


def _extract_downloaded_file_path(stdout: str) -> Path | None:
    """Extract the final file path printed by ``yt-dlp`` if present."""
    printed_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not printed_lines:
        return None

    return Path(printed_lines[-1])


def _extract_download_title(stdout: str) -> str | None:
    """Extract a human-friendly title from printed ``yt-dlp`` output."""
    printed_lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if len(printed_lines) <= 1:
        return None

    return printed_lines[0]


def download_audio(url: str, *, options: DownloadOptions) -> DownloadResult:
    """Download audio from ``url`` using ``yt-dlp``.

    Parameters
    ----------
    url : str
        Video or media URL to download.
    options : DownloadOptions
        Download parameters used to build the ``yt-dlp`` command.

    Returns
    -------
    DownloadResult
        Successful download metadata, including already-downloaded archive hits.

    Raises
    ------
    YtDlpError
        If ``yt-dlp`` fails to download the requested URL.
    """
    command = ["yt-dlp"]

    if options.cookies_file is not None:
        command.extend(["--cookies", str(options.cookies_file)])

    if options.archive_file is not None:
        command.extend(["--download-archive", str(options.archive_file)])

    command.extend(
        [
            "-x",
            "--no-playlist",
            "--audio-format",
            options.audio_format,
        ]
    )

    if options.audio_quality is not None:
        command.extend(["--audio-quality", options.audio_quality])

    command.extend(
        [
            "--embed-metadata",
            "--embed-thumbnail",
            "--print",
            "after_move:filepath",
            "-o",
            options.output_template,
        ]
    )

    command.extend(options.extra_args)
    command.append(url)

    result = run_ytdlp(command, timeout_seconds=options.timeout_seconds)
    if result.returncode != 0:
        raise YtDlpError(
            "Could not download audio with yt-dlp. "
            f"returncode={result.returncode} reason={result.reason!r} stderr={result.stderr.strip()}"
        )

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    already_downloaded = "has already been recorded in the archive" in combined_output

    return DownloadResult(
        url=url,
        file_path=_extract_downloaded_file_path(result.stdout),
        title=_extract_download_title(result.stdout),
        already_downloaded=already_downloaded,
        stdout=result.stdout,
        stderr=result.stderr,
    )
