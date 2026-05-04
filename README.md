# audio_media_utils

Utilities for audio-oriented download workflows and simple metadata editing.

This repository is intentionally focused on reusable domain helpers for:

- YouTube and `yt-dlp` download helpers
- playlist detection and expansion
- simple audio metadata reads and writes with `mutagen`
- filename and path helpers for tagged audio files

It does not include worker loops, logging infrastructure, Docker wiring, or service-specific orchestration.

## Planned package layout

```txt
src/audio_media_utils/
|-- youtube/
|   |-- models.py
|   |-- urls.py
|   |-- ytdlp_runner.py
|   |-- playlists.py
|   `-- downloads.py
|-- audio/
|   |-- models.py
|   |-- mutagen_tags.py
|   |-- files.py
|   `-- naming.py
`-- exceptions.py
```
