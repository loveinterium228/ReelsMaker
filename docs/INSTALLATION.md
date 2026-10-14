# Installation and Windows packaging

## Run from source

Use Python 3.10+ with a virtual environment. Python 3.12 on Windows was used for the local review.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

On Linux/macOS, use `.venv/bin/python` instead. A desktop session is required for normal use.

Install FFmpeg and FFprobe through the [official download page](https://ffmpeg.org/download.html). Keep both executables together. Discovery checks `ffmpeg/bin/` inside the project/application resources and then `PATH`. The Settings dialog can override discovery with a custom executable; it checks that the file and its sibling FFprobe are working executables.

Caption rendering requires a build with libass. CPU encoding uses `libx264`; hardware acceleration depends on the FFmpeg build, GPU and driver. Run `python check_gpu.py` to probe encoders without installing PyTorch.

The application does not download videos, connect to YouTube, require OAuth credentials or provide AI highlight selection. Those features appeared in the retired installation notes but are not part of this codebase.

## Speech recognition

`faster-whisper` runs on CPU with INT8 compute in a separate process. Available models are `tiny`, `base`, `small`, `medium` and `large`. Start with `tiny` or `base`; larger models require more memory and processing time.

Choose **Auto-detect** or an explicit language. Explicit UI languages are mapped to ISO language codes. Word timestamps are grouped into captions according to Words per caption. The language choice controls transcription, not translation into English.

The first use downloads model weights from Hugging Face; later runs reuse the cache. Set `HF_HOME` before launch to choose a cache location. No audio upload is implemented by the application.

`av==16.0.1` is intentionally pinned: `faster-whisper==1.2.1` passes an argument removed in PyAV 19. Reinstall `requirements.txt` after dependency changes. The regression suite includes an actual audio-decoder compatibility check.

## Windows application build

Build from a short ASCII path, such as `C:\Projects\ReelsMaker-Pro`, using a 64-bit Python environment. The delivered specs target an onedir Windows distribution.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\tools\build_windows.ps1 -Python .\.venv\Scripts\python.exe
```

The helper builds the speech process and GUI separately, then copies the complete speech bundle into the application folder. Both bundles are needed:

```text
dist/ReelsMakerPro/
├── ReelsMakerPro.exe
├── _internal/
│   ├── resources/
│   └── ... GUI libraries ...
└── transcriber/
    ├── rm-transcribe.exe
    └── _internal/
        └── ... speech libraries, without Qt ...
```

To bundle FFmpeg instead of requiring a system installation, place `ffmpeg.exe`, `ffprobe.exe` and the appropriate `FFMPEG-LICENSE.txt` in `vendor/` **before** building. The GUI spec places the binaries in its `ffmpeg/bin/` resources. Preserve the distribution's applicable notices and license materials.

Model weights are not bundled. The first transcription still downloads a model unless the model cache is prepared separately.

### Installer

With Inno Setup installed and the complete `dist/ReelsMakerPro/` folder ready:

```powershell
ISCC.exe /DAppVersion=1.1.0 installer.iss
```

The installer is English and supports installation without administrator privileges. Its stable application GUID is retained for upgrades. The output is written to `installer_output/`.

The local review built both PyInstaller bundles; Inno Setup compilation and a full install/uninstall cycle were not performed.

## Local data

| Platform | Application data |
| --- | --- |
| Windows | `%APPDATA%/ReelsMakerPro/` |
| macOS | `~/Library/Application Support/ReelsMakerPro/` |
| Linux | `$XDG_DATA_HOME/ReelsMakerPro/`, default `~/.local/share/ReelsMakerPro/` |

This folder stores `app.log`, `settings.json` and the personal `presets/` library. Automatic subtitle WAV/SRT intermediates are removed after processing. Preview images are temporary and removed when their window/application closes.

Preferences are written as JSON via a temporary file and replacement. If writing fails, the UI reports the error.

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

The test suite requires FFmpeg and FFprobe on `PATH`. Alternatively, set `FFMPEG_BINARY` and `FFPROBE_BINARY` to their absolute paths. Tests generate short synthetic fixtures; they do not use or modify personal videos or download speech models.

For a manual speech check:

```powershell
python utils/transcribe_cli.py --audio sample.wav --srt sample.srt --model tiny --language English --words-per-line 5
```

This command may download the model on first use. The SRT file contains the recognized words, so inspect the transcript as well as the exit status.
