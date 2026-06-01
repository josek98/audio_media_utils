from __future__ import annotations

"""Typed models used by the audio helpers."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AudioTags:
    """Normalized tag container for simple mutagen write operations."""

    artists: list[str] = field(default_factory=list)
    artist: str | None = None
    albumartist: str | None = None
    album: str | None = None
    title: str | None = None
    tracknumber: int | None = None
    discnumber: int | None = None
    date: str | None = None
    genre: list[str] = field(default_factory=list)
    isrc: str | None = None
    album_type: str | None = None
    cover_image_url: str | None = None
    musicbrainz_trackid: str | None = None
    musicbrainz_albumid: str | None = None
