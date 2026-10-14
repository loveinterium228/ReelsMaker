# Changelog

## 1.1.0 — 2026-10-14

### Fixed

- Original-format exports and previews no longer query an unused random-background library.

- Batch export failure caused by missing random-background imports.
- Crashes caused by releasing an active Qt worker after a file error.
- Incomplete cancellation and unsafe shutdown of encoding/preview/speech workers.
- Audio-stream assumptions that rejected silent video inputs.
- Invalid or unbounded GIF export behavior.
- Infinite split-screen backgrounds when no audio stream limited duration.
- Music extending or prematurely ending exports.
- Zoom changing the requested canvas size and producing odd encoder dimensions.
- Fragile SRT path escaping, lost caption styles, reversed position labels and incorrect ASS color order.
- Subtitle preview timestamps and partial preset overwrites.
- Missing language-code mappings and floating-point SRT timestamp truncation.
- faster-whisper/PyAV dependency incompatibility.
- Existing exports being overwritten and equal source basenames colliding.
- Relative media paths breaking when FFmpeg changed its working directory.
- FFmpeg diagnostics being lost through generic exception wrapping.
- Custom FFmpeg settings being ignored and preferences being lost between sessions.
- Filter checkboxes being toggled twice when clicked directly.
- GPU diagnostic script requiring an undeclared PyTorch installation.

### Added

- 30 deterministic logical regressions in addition to the media-rendering test suite (89 tests total).

- Regression tests using real FFmpeg and Qt, plus decoder compatibility coverage.
- Shared cancellation and child-process cleanup.
- Numbered output reservation and temporary render files.
- Windows build helper that includes the separate transcription bundle.
- GitHub Actions test workflow for Python 3.10 and 3.12.
- English installation guide, review evidence and architecture/pipeline diagrams.
- Real application screenshots in dark and light themes.

### Changed

- English interface, presets, dialogs, status messages, installer and developer documentation.
- Public author identity and MIT attribution use `loveinterium228`.
- Author footer links to GitHub.
- Main preview and export share the visual graph builder.
- Per-file variations are described as editing controls without platform-evasion claims.
- The installation guide describes the actual supported application features.
