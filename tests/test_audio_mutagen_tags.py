from __future__ import annotations

import warnings

import pytest

from audio_media_utils.audio.models import AudioTags
from audio_media_utils.audio.mutagen_tags import read_tags, update_tags, write_tags
from audio_media_utils.exceptions import MetadataError


class _FakeVorbisAudio:
    def __init__(self, tags=None, allow_add_tags: bool = True) -> None:
        self.tags = tags
        self._allow_add_tags = allow_add_tags
        self.save_called = False

    def add_tags(self) -> None:
        if self._allow_add_tags:
            self.tags = {}

    def save(self) -> None:
        self.save_called = True

    def __setitem__(self, key: str, value) -> None:
        self.tags[key] = value

    def __getitem__(self, key: str):
        return self.tags[key]


class _FakePicture:
    def __init__(self) -> None:
        self.type = None
        self.mime = None
        self.desc = None
        self.data = None


class _FakeFlacAudio(_FakeVorbisAudio):
    def __init__(self, tags=None, allow_add_tags: bool = True) -> None:
        super().__init__(tags=tags, allow_add_tags=allow_add_tags)
        self.pictures = ["old-picture"]
        self.clear_pictures_called = False

    def clear_pictures(self) -> None:
        self.clear_pictures_called = True
        self.pictures = []

    def add_picture(self, picture) -> None:
        self.pictures.append(picture)


class _FakeFrame:
    def __init__(self, frame_id: str, **payload) -> None:
        self.frame_id = frame_id
        self.payload = payload


class _FakeID3Tags:
    def __init__(self, initial=None) -> None:
        self.frames = dict(initial or {})
        self.deleted = []

    def delall(self, frame_key: str) -> None:
        self.deleted.append(frame_key)
        self.frames.pop(frame_key, None)

    def add(self, frame) -> None:
        self.frames[frame.frame_id] = frame

    def __contains__(self, key: str) -> bool:
        return key in self.frames

    def __getitem__(self, key: str):
        return self.frames[key]


class _FakeMp3Audio:
    def __init__(self, tags=None, allow_add_tags: bool = True) -> None:
        self.tags = tags
        self._allow_add_tags = allow_add_tags
        self.save_called = False

    def add_tags(self) -> None:
        if self._allow_add_tags:
            self.tags = _FakeID3Tags()

    def save(self) -> None:
        self.save_called = True


class _FakeAudioWithoutAddTags:
    def __init__(self) -> None:
        self.tags = None


def _frame_factory(frame_id: str):
    def _factory(**payload):
        return _FakeFrame(frame_id, **payload)

    return _factory


def _fake_ufid_factory(*, owner, data):
    return _FakeFrame(f"UFID:{owner}", owner=owner, data=data)


def test_read_tags_returns_empty_dict_when_handler_is_missing(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path, easy=True: None)

    assert read_tags(audio_file) == {}


def test_read_tags_returns_normalized_string_mapping(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeVorbisAudio(tags={"artist": ["Artist"], "tracknumber": [3]})
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path, easy=True: fake_audio)

    assert read_tags(audio_file) == {"artist": ["Artist"], "tracknumber": ["3"]}


def test_write_tags_updates_mp3_fields_without_deleting_unrelated_metadata(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeMp3Audio(tags=_FakeID3Tags(initial={"COMM": _FakeFrame("COMM", text=["keep me"])}))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TPE1", _frame_factory("TPE1"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TPE2", _frame_factory("TPE2"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TALB", _frame_factory("TALB"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TIT2", _frame_factory("TIT2"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TRCK", _frame_factory("TRCK"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TPOS", _frame_factory("TPOS"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TDRC", _frame_factory("TDRC"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TCON", _frame_factory("TCON"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TSRC", _frame_factory("TSRC"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TXXX", lambda **payload: _FakeFrame(f"TXXX:{payload['desc']}", **payload))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.UFID", _fake_ufid_factory)

    write_tags(
        audio_file,
        AudioTags(
            artists=["Artist One", "Artist Two"],
            artist="Artist One feat. Artist Two",
            albumartist="Album Artist",
            album="Album",
            title="Song",
            tracknumber=7,
            discnumber=2,
            date="2024",
            genre=["Rock"],
            isrc="ISRC123",
            album_type="single",
            musicbrainz_trackid="track-id",
            musicbrainz_albumid="album-id",
        ),
    )

    assert fake_audio.save_called is True
    assert "COMM" in fake_audio.tags.frames
    assert fake_audio.tags["TPE1"].payload["text"] == ["Artist One", "Artist Two"]
    assert fake_audio.tags["TXXX:ARTISTS"].payload["text"] == ["Artist One", "Artist Two"]
    assert fake_audio.tags["TPE2"].payload["text"] == ["Album Artist"]
    assert fake_audio.tags["TALB"].payload["text"] == ["Album"]
    assert fake_audio.tags["TIT2"].payload["text"] == ["Song"]
    assert fake_audio.tags["TRCK"].payload["text"] == ["7"]
    assert fake_audio.tags["TPOS"].payload["text"] == ["2"]
    assert fake_audio.tags["TDRC"].payload["text"] == ["2024"]
    assert fake_audio.tags["TCON"].payload["text"] == ["Rock"]
    assert fake_audio.tags["TSRC"].payload["text"] == ["ISRC123"]
    assert fake_audio.tags["TXXX:releasetype"].payload["text"] == ["single"]
    assert fake_audio.tags["UFID:http://musicbrainz.org"].payload["data"] == b"track-id"
    assert fake_audio.tags["TXXX:MusicBrainz Album Id"].payload["text"] == ["album-id"]


def test_write_tags_updates_flac_fields_without_deleting_unrelated_metadata(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.flac"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeFlacAudio(tags={"comment": ["keep me"]})
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)

    write_tags(
        audio_file,
        AudioTags(
            artists=["Artist One", "Artist Two"],
            artist="Artist One feat. Artist Two",
            albumartist="Album Artist",
            album="Album",
            title="Song",
            tracknumber=7,
            discnumber=2,
            date="2024",
            genre=["Rock"],
            isrc="ISRC123",
            album_type="album",
            musicbrainz_trackid="track-id",
            musicbrainz_albumid="album-id",
        ),
    )

    assert fake_audio.save_called is True
    assert fake_audio.tags["comment"] == ["keep me"]
    assert fake_audio.tags["artist"] == ["Artist One feat. Artist Two"]
    assert fake_audio.tags["artists"] == ["Artist One", "Artist Two"]
    assert fake_audio.tags["albumartist"] == ["Album Artist"]
    assert fake_audio.tags["album"] == ["Album"]
    assert fake_audio.tags["title"] == ["Song"]
    assert fake_audio.tags["tracknumber"] == ["7"]
    assert fake_audio.tags["discnumber"] == ["2"]
    assert fake_audio.tags["date"] == ["2024"]
    assert fake_audio.tags["genre"] == ["Rock"]
    assert fake_audio.tags["isrc"] == ["ISRC123"]
    assert fake_audio.tags["releasetype"] == ["album"]
    assert fake_audio.tags["musicbrainz_trackid"] == ["track-id"]
    assert fake_audio.tags["musicbrainz_albumid"] == ["album-id"]


def test_write_tags_embeds_mp3_cover_image_without_breaking_other_tags(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeMp3Audio(tags=_FakeID3Tags(initial={"COMM": _FakeFrame("COMM", text=["keep me"])}))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.APIC", _frame_factory("APIC"))
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags._download_cover_image", lambda url: (b"image-bytes", "image/jpeg"))

    write_tags(audio_file, AudioTags(cover_image_url="https://example.com/cover.jpg"))

    assert "COMM" in fake_audio.tags.frames
    assert fake_audio.tags["APIC"].payload["data"] == b"image-bytes"
    assert fake_audio.tags["APIC"].payload["mime"] == "image/jpeg"


def test_write_tags_embeds_flac_cover_image_without_breaking_other_tags(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.flac"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeFlacAudio(tags={"comment": ["keep me"]})
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.Picture", _FakePicture)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags._download_cover_image", lambda url: (b"image-bytes", "image/png"))

    write_tags(audio_file, AudioTags(cover_image_url="https://example.com/cover.png"))

    assert fake_audio.tags["comment"] == ["keep me"]
    assert fake_audio.clear_pictures_called is True
    assert fake_audio.pictures[0].data == b"image-bytes"
    assert fake_audio.pictures[0].mime == "image/png"


def test_write_tags_warns_when_cover_download_fails_and_still_saves(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.flac"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeFlacAudio(tags={"title": ["Old"]})
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)

    monkeypatch.setattr(
        "audio_media_utils.audio.mutagen_tags._download_cover_image",
        lambda url: (_ for _ in ()).throw(MetadataError("cover failed")),
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        write_tags(audio_file, AudioTags(title="Song", cover_image_url="https://example.com/cover.jpg"))

    assert fake_audio.save_called is True
    assert fake_audio.tags["title"] == ["Song"]
    assert len(captured) == 1
    assert "cover failed" in str(captured[0].message)


def test_write_tags_initializes_tags_when_missing(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeMp3Audio(tags=None)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.TPE1", _frame_factory("TPE1"))

    write_tags(audio_file, AudioTags(artist="Artist"))

    assert fake_audio.tags["TPE1"].payload["text"] == ["Artist"]


def test_write_tags_raises_when_no_handler_exists(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.unknown"
    audio_file.write_bytes(b"data")

    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: None)

    with pytest.raises(ValueError, match="No compatible mutagen handler"):
        write_tags(audio_file, AudioTags(artist="Artist"))


def test_write_tags_raises_when_tag_container_cannot_be_initialized(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    fake_audio = _FakeAudioWithoutAddTags()
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.File", lambda path: fake_audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.MP3", _FakeMp3Audio)
    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.FLAC", _FakeFlacAudio)

    with pytest.raises(ValueError, match="Unable to initialize metadata container"):
        write_tags(audio_file, AudioTags(artist="Artist"))


def test_update_tags_delegates_to_write_tags(monkeypatch, tmp_path) -> None:
    audio_file = tmp_path / "song.mp3"
    audio_file.write_bytes(b"data")

    captured = {}

    def _fake_write_tags(path, tags):
        captured["path"] = path
        captured["tags"] = tags

    monkeypatch.setattr("audio_media_utils.audio.mutagen_tags.write_tags", _fake_write_tags)

    tags = AudioTags(artist="Artist")
    update_tags(audio_file, tags)

    assert captured == {"path": audio_file, "tags": tags}
