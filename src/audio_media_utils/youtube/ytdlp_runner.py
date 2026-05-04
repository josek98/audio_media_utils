from __future__ import annotations

"""Thin subprocess wrapper around yt-dlp."""

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class YtDlpCommandResult:
    """Raw result of a yt-dlp invocation."""

    returncode: int
    stdout: str
    stderr: str
    reason: str | None = None


def run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
    """Run a yt-dlp command and normalize timeout and OS errors."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return YtDlpCommandResult(
            returncode=-1,
            stdout=error.stdout or "",
            stderr=error.stderr or "",
            reason="timeout",
        )
    except OSError as error:
        return YtDlpCommandResult(
            returncode=-1,
            stdout="",
            stderr=str(error),
            reason="os_error",
        )

    return YtDlpCommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
