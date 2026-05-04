from types import SimpleNamespace

import pytest

from audio_media_utils.audio.files import read_audio_duration


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
