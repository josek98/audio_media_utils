from pathlib import Path

import pytest

from audio_media_utils.exceptions import YtDlpError
from audio_media_utils.youtube import downloads, metadata, playlists, search
from audio_media_utils.youtube.downloads import download_audio
from audio_media_utils.youtube.models import DownloadOptions
from audio_media_utils.youtube.metadata import fetch_video_metadata
from audio_media_utils.youtube.playlists import expand_playlist
from audio_media_utils.youtube.search import search_youtube_videos
from audio_media_utils.youtube.ytdlp_runner import YtDlpCommandResult
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


def test_expand_playlist_returns_entries_from_flat_playlist_json(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert command == [
            'yt-dlp',
            '--dump-single-json',
            '--flat-playlist',
            '--no-warnings',
            'https://www.youtube.com/playlist?list=PL123',
        ]
        assert timeout_seconds == 120
        return YtDlpCommandResult(
            returncode=0,
            stdout=(
                '{"entries": ['
                '{"id": "abc123", "title": "Episode 1"}, '
                '{"id": "def456"}, '
                '{"title": "missing id"}'
                ']}'
            ),
            stderr='',
        )

    monkeypatch.setattr(playlists, 'run_ytdlp', _fake_run_ytdlp)

    result = expand_playlist('https://www.youtube.com/playlist?list=PL123')

    assert result == [
        playlists.PlaylistEntry(
            video_id='abc123',
            url='https://www.youtube.com/watch?v=abc123',
            title='Episode 1',
        ),
        playlists.PlaylistEntry(
            video_id='def456',
            url='https://www.youtube.com/watch?v=def456',
            title=None,
        ),
    ]


def test_expand_playlist_supports_cookies_file(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert command == [
            'yt-dlp',
            '--cookies',
            'cookies.txt',
            '--dump-single-json',
            '--flat-playlist',
            '--no-warnings',
            'https://www.youtube.com/playlist?list=PL123',
        ]
        assert timeout_seconds == 45
        return YtDlpCommandResult(returncode=0, stdout='{"entries": []}', stderr='')

    monkeypatch.setattr(playlists, 'run_ytdlp', _fake_run_ytdlp)

    result = expand_playlist(
        'https://www.youtube.com/playlist?list=PL123',
        cookies_file='cookies.txt',
        timeout_seconds=45,
    )

    assert result == []


def test_expand_playlist_raises_when_ytdlp_fails(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(returncode=1, stdout='', stderr='boom', reason=None)

    monkeypatch.setattr(playlists, 'run_ytdlp', _fake_run_ytdlp)

    with pytest.raises(YtDlpError, match='Could not expand playlist'):
        expand_playlist('https://www.youtube.com/playlist?list=PL123')


def test_fetch_video_metadata_returns_normalized_fields(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert command == [
            'yt-dlp',
            '--cookies',
            'cookies.txt',
            '--dump-single-json',
            '--skip-download',
            '--no-warnings',
            '--no-playlist',
            'https://www.youtube.com/watch?v=abc123',
        ]
        assert timeout_seconds == 45
        return YtDlpCommandResult(
            returncode=0,
            stdout=(
                '{'
                '"id": "abc123", '
                '"title": "Episode title", '
                '"upload_date": "20260506", '
                '"duration": 3600, '
                '"live_status": "not_live", '
                '"was_live": true, '
                '"release_timestamp": 1746496800'
                '}'
            ),
            stderr='',
        )

    monkeypatch.setattr(metadata, 'run_ytdlp', _fake_run_ytdlp)

    result = fetch_video_metadata(
        'https://www.youtube.com/watch?v=abc123',
        cookies_file='cookies.txt',
        timeout_seconds=45,
    )

    assert result.video_id == 'abc123'
    assert result.url == 'https://www.youtube.com/watch?v=abc123'
    assert result.title == 'Episode title'
    assert result.upload_date == '20260506'
    assert result.duration_seconds == 3600
    assert result.live_status == 'not_live'
    assert result.was_live is True
    assert result.release_timestamp == 1746496800


def test_fetch_video_metadata_uses_timestamp_fallback(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(
            returncode=0,
            stdout='{"id": "abc123", "is_live": true, "timestamp": 1746496800}',
            stderr='',
        )

    monkeypatch.setattr(metadata, 'run_ytdlp', _fake_run_ytdlp)

    result = fetch_video_metadata('https://www.youtube.com/watch?v=abc123')

    assert result.was_live is True
    assert result.release_timestamp == 1746496800


def test_fetch_video_metadata_raises_when_ytdlp_fails(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(returncode=1, stdout='', stderr='boom', reason='os_error')

    monkeypatch.setattr(metadata, 'run_ytdlp', _fake_run_ytdlp)

    with pytest.raises(YtDlpError, match='Could not fetch video metadata'):
        fetch_video_metadata('https://www.youtube.com/watch?v=abc123')


def test_fetch_video_metadata_raises_when_video_id_is_missing(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(returncode=0, stdout='{"title": "No id"}', stderr='')

    monkeypatch.setattr(metadata, 'run_ytdlp', _fake_run_ytdlp)

    with pytest.raises(YtDlpError, match='did not return a video id'):
        fetch_video_metadata('https://www.youtube.com/watch?v=abc123')


def test_search_youtube_videos_returns_normalized_results(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert command == [
            'yt-dlp',
            '--cookies',
            'cookies.txt',
            '--dump-single-json',
            '--no-warnings',
            'ytsearch3:metallica one lyrics',
        ]
        assert timeout_seconds == 30
        return YtDlpCommandResult(
            returncode=0,
            stdout=(
                '{"entries": ['
                '{"id": "abc123", "title": "Metallica - One (Lyrics)", "duration": 448, "webpage_url": "https://www.youtube.com/watch?v=abc123"}, '
                '{"id": "def456", "title": "Metallica - One", "duration": 447, "is_live": true}, '
                '{"title": "missing id"}'
                ']}'
            ),
            stderr='',
        )

    monkeypatch.setattr(search, 'run_ytdlp', _fake_run_ytdlp)

    result = search_youtube_videos(
        'metallica one lyrics',
        max_results=3,
        cookies_file='cookies.txt',
        timeout_seconds=30,
    )

    assert len(result) == 2
    assert result[0].video_id == 'abc123'
    assert result[0].url == 'https://www.youtube.com/watch?v=abc123'
    assert result[0].title == 'Metallica - One (Lyrics)'
    assert result[0].duration_seconds == 448
    assert result[1].video_id == 'def456'
    assert result[1].url == 'https://www.youtube.com/watch?v=def456'
    assert result[1].was_live is True


def test_search_youtube_videos_raises_on_invalid_max_results() -> None:
    with pytest.raises(ValueError, match='max_results must be greater than 0'):
        search_youtube_videos('query', max_results=0)


def test_search_youtube_videos_raises_when_ytdlp_fails(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(returncode=1, stdout='', stderr='boom', reason='os_error')

    monkeypatch.setattr(search, 'run_ytdlp', _fake_run_ytdlp)

    with pytest.raises(YtDlpError, match='Could not search YouTube videos'):
        search_youtube_videos('query')


def test_download_audio_builds_expected_command_and_returns_success(monkeypatch) -> None:
    expected_path = Path('downloads/episode.mp3')

    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert command == [
            'yt-dlp',
            '--cookies',
            'cookies.txt',
            '--download-archive',
            'archive.txt',
            '-x',
            '--no-playlist',
            '--audio-format',
            'mp3',
            '--audio-quality',
            '0',
            '--embed-metadata',
            '--embed-thumbnail',
            '--print',
            'after_move:filepath',
            '-o',
            '%(title)s.%(ext)s',
            '--no-warnings',
            'https://www.youtube.com/watch?v=abc123',
        ]
        assert timeout_seconds == 30
        return YtDlpCommandResult(
            returncode=0,
            stdout='Episode title\ndownloads/episode.mp3\n',
            stderr='',
        )

    monkeypatch.setattr(downloads, 'run_ytdlp', _fake_run_ytdlp)

    result = download_audio(
        'https://www.youtube.com/watch?v=abc123',
        options=DownloadOptions(
            output_template='%(title)s.%(ext)s',
            audio_quality='0',
            archive_file=Path('archive.txt'),
            cookies_file=Path('cookies.txt'),
            timeout_seconds=30,
            extra_args=['--no-warnings'],
        ),
    )

    assert result.url == 'https://www.youtube.com/watch?v=abc123'
    assert result.file_path == expected_path
    assert result.title == 'Episode title'
    assert result.already_downloaded is False


def test_download_audio_forces_single_video_for_mix_url(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        assert '--no-playlist' in command
        assert command[-1] == 'https://www.youtube.com/watch?v=abc123&list=RDabc123&start_radio=1'
        assert timeout_seconds == 120
        return YtDlpCommandResult(
            returncode=0,
            stdout='Mix song\ndownloads/mix-song.flac\n',
            stderr='',
        )

    monkeypatch.setattr(downloads, 'run_ytdlp', _fake_run_ytdlp)

    result = download_audio(
        'https://www.youtube.com/watch?v=abc123&list=RDabc123&start_radio=1',
        options=DownloadOptions(
            output_template='%(title)s.%(ext)s',
            audio_format='flac',
        ),
    )

    assert result.file_path == Path('downloads/mix-song.flac')
    assert result.already_downloaded is False


def test_download_audio_marks_already_downloaded_from_ytdlp_output(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(
            returncode=0,
            stdout='',
            stderr='Video has already been recorded in the archive',
        )

    monkeypatch.setattr(downloads, 'run_ytdlp', _fake_run_ytdlp)

    result = download_audio(
        'https://www.youtube.com/watch?v=abc123',
        options=DownloadOptions(output_template='%(title)s.%(ext)s'),
    )

    assert result.already_downloaded is True
    assert result.file_path is None


def test_download_audio_raises_when_ytdlp_fails(monkeypatch) -> None:
    def _fake_run_ytdlp(command: list[str], timeout_seconds: int) -> YtDlpCommandResult:
        _ = (command, timeout_seconds)
        return YtDlpCommandResult(
            returncode=-1,
            stdout='partial output',
            stderr='timed out',
            reason='timeout',
        )

    monkeypatch.setattr(downloads, 'run_ytdlp', _fake_run_ytdlp)

    with pytest.raises(YtDlpError, match='Could not download audio'):
        download_audio(
            'https://www.youtube.com/watch?v=abc123',
            options=DownloadOptions(output_template='%(title)s.%(ext)s'),
        )
