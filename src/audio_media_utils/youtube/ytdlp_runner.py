from __future__ import annotations

"""Thin subprocess wrapper around yt-dlp."""

import locale
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
            text=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        return YtDlpCommandResult(
            returncode=-1,
            stdout=_decode_ytdlp_output(error.stdout),
            stderr=_decode_ytdlp_output(error.stderr),
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
        stdout=_decode_ytdlp_output(result.stdout),
        stderr=_decode_ytdlp_output(result.stderr),
    )


def _decode_ytdlp_output(payload: bytes | str | None) -> str:
    """Decode yt-dlp output with UTF-8 first and OS-specific fallbacks.

    Parameters
    ----------
    payload : bytes | str | None
        Raw stdout or stderr produced by ``subprocess.run``.

    Returns
    -------
    str
        Decoded text safe for downstream parsing and logging.
    """
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload

    encodings: list[str] = ["utf-8"]
    preferred_encoding = locale.getpreferredencoding(False)
    if preferred_encoding and preferred_encoding.lower() not in {"utf-8", "utf8"}:
        encodings.append(preferred_encoding)
    if "cp1252" not in {encoding.lower() for encoding in encodings}:
        encodings.append("cp1252")

    for encoding in encodings:
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue

    return payload.decode("utf-8", errors="replace")
