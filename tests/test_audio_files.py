from types import SimpleNamespace

import pytest

from audio_media_utils.audio.files import cleanup_ytdlp_artifacts_for_target, read_audio_duration


def test_read_audio_duration_returns_length(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    def _fake_file(path):
        return SimpleNamespace(info=SimpleNamespace(length=123.45))

    monkeypatch.setattr('audio_media_utils.audio.files.File', _fake_file)

    assert read_audio_duration(audio_file) == 123.45


def test_read_audio_duration_raises_for_missing_metadata(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    monkeypatch.setattr('audio_media_utils.audio.files.File', lambda path: None)

    with pytest.raises(ValueError, match='Unable to read duration'):
        read_audio_duration(audio_file)


def test_cleanup_ytdlp_artifacts_for_target_deletes_related_artifacts(tmp_path) -> None:
    target_file = tmp_path / 'episode.flac'
    target_file.write_bytes(b'final')

    part_file = tmp_path / 'episode.flac.part'
    webm_file = tmp_path / 'episode.webm'
    webp_file = tmp_path / 'episode.webp'
    other_file = tmp_path / 'other.webm'

    part_file.write_bytes(b'partial')
    webm_file.write_bytes(b'intermediate')
    webp_file.write_bytes(b'thumbnail')
    other_file.write_bytes(b'unrelated')

    deleted_paths = cleanup_ytdlp_artifacts_for_target(target_file)

    assert deleted_paths == [part_file, webm_file, webp_file]
    assert target_file.exists() is True
    assert part_file.exists() is False
    assert webm_file.exists() is False
    assert webp_file.exists() is False
    assert other_file.exists() is True


def test_cleanup_ytdlp_artifacts_for_target_ignores_missing_files(tmp_path) -> None:
    target_file = tmp_path / 'episode.flac'

    assert cleanup_ytdlp_artifacts_for_target(target_file) == []
