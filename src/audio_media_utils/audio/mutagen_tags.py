from __future__ import annotations

"""Simple mutagen helpers for reading and writing tags."""

from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
import warnings

from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TPOS, TRCK, TSRC, TXXX, UFID
from mutagen.mp3 import MP3

from audio_media_utils.audio.models import AudioTags
from audio_media_utils.exceptions import MetadataError

_MUSICBRAINZ_OWNER = "http://musicbrainz.org"
_DEFAULT_REQUEST_HEADERS = {"User-Agent": "audio-media-utils/0.2"}


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
    """Write managed metadata fields while preserving unrelated existing tags.

    The writer updates only the fields managed by :class:`AudioTags`. Fields not
    represented in ``tags`` are left untouched.
    """
    file_path = Path(path)
    audio = File(file_path)
    if audio is None:
        raise ValueError(f"No compatible mutagen handler for {file_path.suffix!r}")

    if audio.tags is None and hasattr(audio, "add_tags"):
        audio.add_tags()

    if audio.tags is None:
        raise ValueError(f"Unable to initialize metadata container for {file_path}")

    if isinstance(audio, MP3):
        _write_mp3_tags(audio, tags)
    elif isinstance(audio, FLAC):
        _write_flac_tags(audio, tags)
    else:
        _write_generic_tags(file_path, tags)
        return

    audio.save()


def update_tags(path: str | Path, tags: AudioTags) -> None:
    """Alias kept for a friendlier public API while bootstrapping the package."""
    write_tags(path, tags)


def _write_generic_tags(path: Path, tags: AudioTags) -> None:
    """Fallback writer for formats that still work well through easy tags."""
    audio = File(path, easy=True)
    if audio is None:
        raise ValueError(f"No compatible mutagen handler for {path.suffix!r}")

    if audio.tags is None and hasattr(audio, "add_tags"):
        audio.add_tags()

    if audio.tags is None:
        raise ValueError(f"Unable to initialize metadata container for {path}")

    assignments: dict[str, list[str]] = {}
    _assign_easy_text(assignments, "artist", _display_artist(tags))
    _assign_easy_text(assignments, "albumartist", tags.albumartist)
    _assign_easy_text(assignments, "album", tags.album)
    _assign_easy_text(assignments, "title", tags.title)
    _assign_easy_text(assignments, "tracknumber", str(tags.tracknumber) if tags.tracknumber is not None else None)
    _assign_easy_text(assignments, "discnumber", str(tags.discnumber) if tags.discnumber is not None else None)
    _assign_easy_text(assignments, "date", tags.date)
    _assign_easy_multi(assignments, "genre", tags.genre)
    _assign_easy_text(assignments, "isrc", tags.isrc)
    _assign_easy_text(assignments, "musicbrainz_trackid", tags.musicbrainz_trackid)
    _assign_easy_text(assignments, "musicbrainz_albumid", tags.musicbrainz_albumid)

    for key, value in assignments.items():
        audio.tags[key] = value

    audio.save()


def _write_mp3_tags(audio: MP3, tags: AudioTags) -> None:
    """Write managed MP3/ID3 fields without deleting unrelated frames."""
    primary_artist = _display_artist(tags)
    if primary_artist is not None:
        _replace_id3_text_frame(audio, "TPE1", TPE1, tags.artists or [primary_artist])
    if tags.artists:
        _replace_id3_text_frame(audio, "TXXX:ARTISTS", TXXX, list(tags.artists), desc="ARTISTS")
    if tags.albumartist is not None:
        _replace_id3_text_frame(audio, "TPE2", TPE2, [tags.albumartist])
    if tags.album is not None:
        _replace_id3_text_frame(audio, "TALB", TALB, [tags.album])
    if tags.title is not None:
        _replace_id3_text_frame(audio, "TIT2", TIT2, [tags.title])
    if tags.tracknumber is not None:
        _replace_id3_text_frame(audio, "TRCK", TRCK, [str(tags.tracknumber)])
    if tags.discnumber is not None:
        _replace_id3_text_frame(audio, "TPOS", TPOS, [str(tags.discnumber)])
    if tags.date is not None:
        _replace_id3_text_frame(audio, "TDRC", TDRC, [tags.date])
    if tags.genre:
        _replace_id3_text_frame(audio, "TCON", TCON, list(tags.genre))
    if tags.isrc is not None:
        _replace_id3_text_frame(audio, "TSRC", TSRC, [tags.isrc])
    if tags.album_type is not None:
        # Picard exposes the publication type from the MusicBrainz-style
        # releasetype key rather than a custom albumtype field.
        _replace_id3_text_frame(audio, "TXXX:releasetype", TXXX, [tags.album_type], desc="releasetype")
    if tags.musicbrainz_trackid is not None:
        _replace_ufid_frame(audio, owner=_MUSICBRAINZ_OWNER, value=tags.musicbrainz_trackid)
    if tags.musicbrainz_albumid is not None:
        _replace_id3_text_frame(
            audio,
            "TXXX:MusicBrainz Album Id",
            TXXX,
            [tags.musicbrainz_albumid],
            desc="MusicBrainz Album Id",
        )
    _try_apply_cover_image(audio, tags)


def _write_flac_tags(audio: FLAC, tags: AudioTags) -> None:
    """Write managed FLAC/Vorbis fields without deleting unrelated comments."""
    primary_artist = _display_artist(tags)
    if primary_artist is not None:
        audio["artist"] = [primary_artist]
    if tags.artists:
        audio["artists"] = list(tags.artists)
    if tags.albumartist is not None:
        audio["albumartist"] = [tags.albumartist]
    if tags.album is not None:
        audio["album"] = [tags.album]
    if tags.title is not None:
        audio["title"] = [tags.title]
    if tags.tracknumber is not None:
        audio["tracknumber"] = [str(tags.tracknumber)]
    if tags.discnumber is not None:
        audio["discnumber"] = [str(tags.discnumber)]
    if tags.date is not None:
        audio["date"] = [tags.date]
    if tags.genre:
        audio["genre"] = list(tags.genre)
    if tags.isrc is not None:
        audio["isrc"] = [tags.isrc]
    if tags.album_type is not None:
        # Picard interprets the Vorbis releasetype field as "Tipo de publicacion".
        audio["releasetype"] = [tags.album_type]
    if tags.musicbrainz_trackid is not None:
        audio["musicbrainz_trackid"] = [tags.musicbrainz_trackid]
    if tags.musicbrainz_albumid is not None:
        audio["musicbrainz_albumid"] = [tags.musicbrainz_albumid]
    _try_apply_cover_image(audio, tags)


def _assign_easy_text(assignments: dict[str, list[str]], key: str, value: str | None) -> None:
    """Populate a generic easy-tag assignment when a text value is present."""
    if value is not None:
        assignments[key] = [value]


def _assign_easy_multi(assignments: dict[str, list[str]], key: str, values: list[str]) -> None:
    """Populate a generic easy-tag assignment when multiple values are present."""
    if values:
        assignments[key] = list(values)


def _display_artist(tags: AudioTags) -> str | None:
    """Return the human-readable primary artist string to expose publicly."""
    if tags.artist is not None:
        return tags.artist
    if tags.artists:
        return ", ".join(tags.artists)
    return None


def _replace_id3_text_frame(audio: MP3, frame_key: str, frame_class, values: list[str], *, desc: str | None = None) -> None:
    """Replace one managed ID3 text frame while preserving unrelated frames."""
    audio.tags.delall(frame_key)
    kwargs = {"encoding": 3, "text": list(values)}
    if desc is not None:
        kwargs["desc"] = desc
    audio.tags.add(frame_class(**kwargs))


def _replace_ufid_frame(audio: MP3, *, owner: str, value: str) -> None:
    """Replace one managed UFID frame while preserving unrelated frames."""
    audio.tags.delall(f"UFID:{owner}")
    audio.tags.add(UFID(owner=owner, data=value.encode("ascii")))


def _try_apply_cover_image(audio: MP3 | FLAC, tags: AudioTags) -> None:
    """Download and embed cover art, degrading to a warning on failures."""
    if not tags.cover_image_url:
        return

    try:
        image_data, mime_type = _download_cover_image(tags.cover_image_url)
        if isinstance(audio, MP3):
            _set_mp3_cover_image(audio, image_data, mime_type)
        elif isinstance(audio, FLAC):
            _set_flac_cover_image(audio, image_data, mime_type)
    except MetadataError as error:
        warnings.warn(str(error), stacklevel=2)


def _download_cover_image(url: str) -> tuple[bytes, str]:
    """Download cover art bytes and detect a usable MIME type."""
    request = Request(url, headers=_DEFAULT_REQUEST_HEADERS)
    try:
        with urlopen(request, timeout=20) as response:
            image_data = response.read()
            mime_type = response.headers.get_content_type() or ""
    except OSError as error:
        raise MetadataError(f"Could not download cover image from {url}: {error}") from error
    except URLError as error:
        raise MetadataError(f"Could not download cover image from {url}: {error}") from error

    if not image_data:
        raise MetadataError(f"Could not download cover image from {url}: empty response")

    normalized_mime = _normalize_cover_mime_type(image_data, mime_type)
    if normalized_mime is None:
        raise MetadataError(f"Unsupported cover image format from {url}")

    return image_data, normalized_mime


def _normalize_cover_mime_type(image_data: bytes, mime_type: str) -> str | None:
    """Normalize downloaded image content type to a cover-art MIME type."""
    lowered = mime_type.lower()
    if lowered in {"image/jpeg", "image/jpg"}:
        return "image/jpeg"
    if lowered == "image/png":
        return "image/png"
    if lowered == "image/webp":
        return "image/webp"

    if image_data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _set_mp3_cover_image(audio: MP3, image_data: bytes, mime_type: str) -> None:
    """Embed cover art into an MP3/ID3 tag set using APIC."""
    audio.tags.delall("APIC")
    audio.tags.add(APIC(encoding=3, mime=mime_type, type=3, desc="Cover", data=image_data))


def _set_flac_cover_image(audio: FLAC, image_data: bytes, mime_type: str) -> None:
    """Embed cover art into a FLAC metadata block using PICTURE."""
    picture = Picture()
    picture.type = 3
    picture.mime = mime_type
    picture.desc = "Cover"
    picture.data = image_data
    audio.clear_pictures()
    audio.add_picture(picture)
