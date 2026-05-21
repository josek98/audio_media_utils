from pathlib import Path

from audio_media_utils.youtube.downloads import _extract_download_title, _extract_downloaded_file_path


def test_extract_download_helpers_handle_none_stdout() -> None:
    assert _extract_downloaded_file_path(None) is None
    assert _extract_download_title(None) is None


def test_extract_downloaded_file_path_uses_last_printed_line() -> None:
    stdout = "Titulo\nC:/music/out.flac\n"
    assert _extract_downloaded_file_path(stdout) == Path("C:/music/out.flac")
