"""Custom exceptions used across the package."""


class AudioMediaUtilsError(Exception):
    """Base exception for the package."""


class YtDlpError(AudioMediaUtilsError):
    """Raised when a yt-dlp command fails."""


class MetadataError(AudioMediaUtilsError):
    """Raised when audio metadata cannot be processed."""
