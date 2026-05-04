import pytest

from audio_media_utils.audio.models import AudioTags
from audio_media_utils.audio.mutagen_tags import read_tags, update_tags, write_tags


class _FakeAudio:
    def __init__(self, tags=None, allow_add_tags: bool = True) -> None:
        self.tags = tags
        self._allow_add_tags = allow_add_tags
        self.delete_called = False
        self.save_called = False

    def add_tags(self) -> None:
        if self._allow_add_tags:
            self.tags = {}

    def delete(self) -> None:
        self.delete_called = True
        self.tags = {}

    def save(self) -> None:
        self.save_called = True


class _FakeAudioWithoutAddTags:
    def __init__(self) -> None:
        self.tags = None


def test_read_tags_returns_empty_dict_when_handler_is_missing(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: None)

    assert read_tags(audio_file) == {}


def test_read_tags_returns_normalized_string_mapping(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    fake_audio = _FakeAudio(tags={'artist': ['Artist'], 'tracknumber': [3]})
    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: fake_audio)

    assert read_tags(audio_file) == {'artist': ['Artist'], 'tracknumber': ['3']}


def test_write_tags_overwrites_common_fields(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    fake_audio = _FakeAudio(tags={'artist': ['Old']})
    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: fake_audio)

    write_tags(
        audio_file,
        AudioTags(
            artist='Artist',
            albumartist='Album Artist',
            album='Album',
            title='Song',
            tracknumber=7,
            date='2024',
            genre=['Rock'],
            musicbrainz_trackid='track-id',
            musicbrainz_albumid='album-id',
        ),
    )

    assert fake_audio.delete_called is True
    assert fake_audio.save_called is True
    assert fake_audio.tags == {
        'artist': ['Artist'],
        'albumartist': ['Album Artist'],
        'album': ['Album'],
        'title': ['Song'],
        'tracknumber': ['7'],
        'date': ['2024'],
        'genre': ['Rock'],
        'musicbrainz_trackid': ['track-id'],
        'musicbrainz_albumid': ['album-id'],
    }


def test_write_tags_initializes_tags_when_missing(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    fake_audio = _FakeAudio(tags=None)
    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: fake_audio)

    write_tags(audio_file, AudioTags(artist='Artist'))

    assert fake_audio.tags == {'artist': ['Artist']}


def test_write_tags_raises_when_no_handler_exists(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.unknown'
    audio_file.write_bytes(b'data')

    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: None)

    with pytest.raises(ValueError, match='No compatible mutagen handler'):
        write_tags(audio_file, AudioTags(artist='Artist'))


def test_write_tags_raises_when_tag_container_cannot_be_initialized(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    fake_audio = _FakeAudioWithoutAddTags()
    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.File', lambda path, easy=True: fake_audio)

    with pytest.raises(ValueError, match='Unable to initialize metadata container'):
        write_tags(audio_file, AudioTags(artist='Artist'))


def test_update_tags_delegates_to_write_tags(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / 'song.mp3'
    audio_file.write_bytes(b'data')

    captured = {}

    def _fake_write_tags(path, tags):
        captured['path'] = path
        captured['tags'] = tags

    monkeypatch.setattr('audio_media_utils.audio.mutagen_tags.write_tags', _fake_write_tags)

    tags = AudioTags(artist='Artist')
    update_tags(audio_file, tags)

    assert captured == {'path': audio_file, 'tags': tags}
