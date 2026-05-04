from audio_media_utils.exceptions import AudioMediaUtilsError, MetadataError, YtDlpError


def test_audio_media_utils_error_is_package_base_exception() -> None:
    error = AudioMediaUtilsError("base error")

    assert str(error) == "base error"
    assert isinstance(error, Exception)


def test_ytdlp_error_inherits_from_package_base_exception() -> None:
    error = YtDlpError("yt-dlp failed")

    assert str(error) == "yt-dlp failed"
    assert isinstance(error, AudioMediaUtilsError)


def test_metadata_error_inherits_from_package_base_exception() -> None:
    error = MetadataError("metadata failed")

    assert str(error) == "metadata failed"
    assert isinstance(error, AudioMediaUtilsError)
