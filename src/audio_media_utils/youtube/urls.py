from __future__ import annotations

"""URL helpers for YouTube video and playlist links."""

from urllib.parse import parse_qs, urlparse


def is_playlist_url(url: str) -> bool:
    """Return whether ``url`` looks like a YouTube playlist URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return parsed.path == "/playlist" or "list" in query


def is_video_url(url: str) -> bool:
    """Return whether ``url`` looks like a YouTube video URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return parsed.path == "/watch" and "v" in query


def extract_video_id(url: str) -> str | None:
    """Extract the ``v`` parameter from a YouTube watch URL."""
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("v", [None])[0]


def extract_playlist_id(url: str) -> str | None:
    """Extract the ``list`` parameter from a YouTube playlist URL."""
    parsed = urlparse(url)
    return parse_qs(parsed.query).get("list", [None])[0]
