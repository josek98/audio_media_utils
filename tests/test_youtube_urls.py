from audio_media_utils.youtube.downloads import download_audio
from audio_media_utils.youtube.models import DownloadOptions
from audio_media_utils.youtube.playlists import expand_playlist
from audio_media_utils.youtube.urls import (
    extract_playlist_id,
    extract_video_id,
    is_playlist_url,
    is_video_url,
)


def test_is_playlist_url_detects_standard_playlist_url() -> None:
    assert is_playlist_url('https://www.youtube.com/playlist?list=PL123') is True


def test_is_playlist_url_detects_watch_url_with_list_parameter() -> None:
    assert is_playlist_url('https://www.youtube.com/watch?v=abc123&list=PL123') is True


def test_is_playlist_url_rejects_plain_video_url() -> None:
    assert is_playlist_url('https://www.youtube.com/watch?v=abc123') is False


def test_is_video_url_detects_watch_url() -> None:
    assert is_video_url('https://www.youtube.com/watch?v=abc123') is True


def test_is_video_url_rejects_playlist_only_url() -> None:
    assert is_video_url('https://www.youtube.com/playlist?list=PL123') is False


def test_extract_video_id_returns_identifier() -> None:
    assert extract_video_id('https://www.youtube.com/watch?v=abc123&list=PL123') == 'abc123'


def test_extract_video_id_returns_none_when_missing() -> None:
    assert extract_video_id('https://www.youtube.com/playlist?list=PL123') is None


def test_extract_playlist_id_returns_identifier() -> None:
    assert extract_playlist_id('https://www.youtube.com/playlist?list=PL123') == 'PL123'


def test_extract_playlist_id_returns_none_when_missing() -> None:
    assert extract_playlist_id('https://www.youtube.com/watch?v=abc123') is None


def test_expand_playlist_placeholder_returns_empty_list() -> None:
    assert expand_playlist('https://www.youtube.com/playlist?list=PL123') == []


def test_download_audio_placeholder_returns_not_implemented_result() -> None:
    result = download_audio(
        'https://www.youtube.com/watch?v=abc123',
        options=DownloadOptions(output_template='%(title)s.%(ext)s'),
    )

    assert result.success is False
    assert result.url == 'https://www.youtube.com/watch?v=abc123'
    assert result.error_reason == 'not_implemented'
