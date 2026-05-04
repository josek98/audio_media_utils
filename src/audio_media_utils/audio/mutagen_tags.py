from __future__ import annotations

"""Simple mutagen helpers for reading and writing tags."""

from pathlib import Path
from mutagen import File
from audio_media_utils.audio.models import AudioTags


def read_tags(path: str | Path) -> dict[str, list[str]]:
    """Read easy tags from an audio file when available."""
    file_path = Path(path)
    audio = File(file_path, easy=True)
    if audio is None or audio.tags is None:
        return {}

    return {
        str(key): [str(item) for item in value]
        for key, value in audio.tags.items()
    }


def write_tags(path: str | Path, tags: AudioTags) -> None:
    """Overwrite common audio tags with normalized values."""
    file_path = Path(path)
    audio = File(file_path, easy=True)
    if audio is None:
        raise ValueError(f"No compatible mutagen handler for {file_path.suffix!r}")

    if audio.tags is None and hasattr(audio, 'add_tags'):
        audio.add_tags()

    if audio.tags is None:
        raise ValueError(f"Unable to initialize metadata container for {file_path}")

    assignments: dict[str, list[str]] = {}
    if tags.artist:
        assignments['artist'] = [tags.artist]
    if tags.albumartist:
        assignments['albumartist'] = [tags.albumartist]
    if tags.album:
        assignments['album'] = [tags.album]
    if tags.title:
        assignments['title'] = [tags.title]
    if tags.tracknumber is not None:
        assignments['tracknumber'] = [str(tags.tracknumber)]
    if tags.date:
        assignments['date'] = [tags.date]
    if tags.genre:
        assignments['genre'] = list(tags.genre)
    if tags.musicbrainz_trackid:
        assignments['musicbrainz_trackid'] = [tags.musicbrainz_trackid]
    if tags.musicbrainz_albumid:
        assignments['musicbrainz_albumid'] = [tags.musicbrainz_albumid]

    audio.delete()
    for key, value in assignments.items():
        audio.tags[key] = value
    audio.save()


def update_tags(path: str | Path, tags: AudioTags) -> None:
    """Alias kept for a friendlier public API while bootstrapping the package."""
    write_tags(path, tags)
