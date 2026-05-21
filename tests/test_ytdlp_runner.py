import subprocess

from audio_media_utils.youtube.ytdlp_runner import YtDlpCommandResult, run_ytdlp


class _CompletedProcess:
    def __init__(self, returncode: int, stdout, stderr) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_ytdlp_returns_normalized_result_on_success(monkeypatch) -> None:
    def _fake_run(*args, **kwargs):
        return _CompletedProcess(returncode=0, stdout=b"ok", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = run_ytdlp(["yt-dlp", "--version"], timeout_seconds=10)

    assert result == YtDlpCommandResult(returncode=0, stdout="ok", stderr="", reason=None)


def test_run_ytdlp_decodes_cp1252_output_when_utf8_fails(monkeypatch) -> None:
    def _fake_run(*args, **kwargs):
        return _CompletedProcess(returncode=0, stdout=bytes([67, 97, 110, 99, 105, 243, 110]), stderr=b"")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = run_ytdlp(["yt-dlp", "--version"], timeout_seconds=10)

    assert result.stdout == "Canción"
    assert result.stderr == ""


def test_run_ytdlp_returns_timeout_result(monkeypatch) -> None:
    def _fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="yt-dlp", timeout=10, output=b"partial", stderr=b"late stderr")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = run_ytdlp(["yt-dlp", "--version"], timeout_seconds=10)

    assert result.returncode == -1
    assert result.stdout == "partial"
    assert result.stderr == "late stderr"
    assert result.reason == "timeout"


def test_run_ytdlp_returns_os_error_result(monkeypatch) -> None:
    def _fake_run(*args, **kwargs):
        raise OSError("yt-dlp not found")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    result = run_ytdlp(["yt-dlp", "--version"], timeout_seconds=10)

    assert result.returncode == -1
    assert result.stdout == ""
    assert result.stderr == "yt-dlp not found"
    assert result.reason == "os_error"

