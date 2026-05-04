from pathlib import Path

from audio_media_utils.audio.naming import build_music_path, sanitize_path_component


def test_sanitize_path_component_normalizes_invalid_characters() -> None:
    assert sanitize_path_component(' AC/DC: Live? ') == 'AC_DC_ Live_'


def test_sanitize_path_component_returns_unknown_for_empty_result() -> None:
    assert sanitize_path_component('   ...   ') == 'Unknown'


def test_build_music_path_includes_track_prefix_when_present() -> None:
    path = build_music_path(
        Path('library'),
        artist='Artist',
        album='Album',
        title='Song',
        track_number=3,
        suffix='.flac',
    )

    assert path == Path('library/Artist/Album/03 - Song.flac')


def test_build_music_path_omits_track_prefix_when_missing() -> None:
    path = build_music_path(
        Path('library'),
        artist='Artist',
        album='Album',
        title='Song',
    )

    assert path == Path('library/Artist/Album/Song.mp3')
