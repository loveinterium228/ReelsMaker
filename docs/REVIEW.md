# Maintenance review — ReelsMaker Pro 1.1.0

Reviewed on **2026-10-14** for English-language portfolio presentation and functional reliability.

## Scope and method

The supplied folder is a source archive without a `.git` directory. OCR's Git preview could not operate on it, so the review used direct source inspection, failure reproduction, regression tests, real media processing and local Windows builds. Findings below are host-reviewed findings; they are not presented as an OCR-generated result.

The review covered the entry point, both UI modules, batch worker, every utility module, shared constants/links, theme generator and generated themes, dependency declarations, both PyInstaller specs, installer script, license and documentation. Icon assets were checked as resources; binary background clips were retained and renamed without editing their contents. Empty package markers were checked for import side effects. The independent `advanced_filters.py` and `audio_uniquify.py` helpers are experimental and are not wired into the desktop editing workflow; they are not advertised as application features.

This report covers the first project only. The follow-up publication targets the owner's repository at https://github.com/loveinterium228/ReelsMaker; the original source archive remains backed up locally.

## Findings and fixes

| Priority | Finding | Result |
| --- | --- | --- |
| High | Every export evaluated an undefined `RANDOM_FILLER`; random selection also lacked its function import. | Restored imports and verified ordinary/random batch exports. |
| High | A file error cleared the active Qt worker reference while `run()` could continue. | Keep the worker until the native `QThread.finished` signal; report failures without freeing a running thread. |
| High | Stop only changed a Python flag; encoding and transcription continued. | Shared cancellation controller terminates the active subprocess and cleanup reaps it. |
| High | Shutdown waited briefly and could destroy running processing/preview/probe threads. | Cancel and wait for all owned workers; reject closing if a worker still has not stopped. |
| High | Non-GIF inputs were assumed to have an audio stream. | Probe actual streams and create audio filters only when applicable. |
| High | GIF export combined infinite input looping with invalid output/input option ordering. | Finite GIF-source playback and an explicit processed-source duration. |
| High | A looping split-screen background could continue indefinitely for silent inputs. | `vstack` ends with the main panel and export has a hard duration boundary. |
| High | Existing outputs and equal basenames from different folders were overwritten. | Exclusive numbered name reservation, partial render file and publish-on-success. |
| High | Fresh dependency resolution installed a PyAV version incompatible with faster-whisper. | Pin tested `av==16.0.1`; include an actual decoder compatibility test. |
| Medium | Music could truncate or extend the expected result; an original audio tail could also extend the picture. | Pad audio, limit output duration, and prefer the video stream's duration over container/audio length. |
| Medium | Zoom-out reduced the output canvas; rounded scale calculations could produce odd or drifting dimensions. | Composite the scaled view onto the original-sized canvas and enforce even dimensions. |
| Medium | SRT paths containing apostrophes/brackets/commas broke the filter graph. | Escape both filter parsing layers; exercise an actual punctuated path. |
| Medium | Export discarded most settings chosen in the subtitle style dialog. | Carry font, colors, outline, bold, position and size into the shared ASS builder. |
| Medium | Subtitle preview used RGB values as ASS BGR and reversed top/bottom alignment labels. | Correct ASS color conversion and numeric position labels. |
| Medium | Seeking before the subtitle filter made the midpoint preview miss active captions. | Apply caption rendering on the source timeline and seek the filtered output frame. |
| Medium | Preset loading emitted intermediate edit signals that overwrote parts of the preset. | Block control signals while applying all preset values. |
| Medium | Starting another caption preview could release a running worker. | Stop and wait before replacing the preview thread; close the dialog safely. |
| Medium | German/French/Spanish/Italian UI values were passed as words rather than ISO codes. | Complete the language map and default to Auto-detect. |
| Medium | Floating-point truncation lost milliseconds in generated SRT timestamps. | Round total milliseconds before splitting hours/minutes/seconds. |
| Medium | FFmpeg changed its working directory, breaking relative media paths. | Keep the caller's working directory; use absolute paths for probing. |
| Medium | Generic exception wrapping discarded FFmpeg error details; debug output accumulated without a bound. | Preserve `CalledProcessError` diagnostics and retain a bounded output tail. |
| Medium | Custom FFmpeg paths were collected but unused; preferences were transient. | Validate and apply FFmpeg/FFprobe paths, rerun encoder detection and persist JSON settings. |
| Medium | Black-bar analysis ran on the UI thread and skipped short clips by starting at 5 seconds. | Move preview analysis into its worker; choose a sample offset within the clip. |
| Medium | Filter checkbox clicks toggled twice while label clicks worked. | Handle checkbox/label mouse events through one toggle path; test both targets. |
| Medium | The GPU diagnostic imported an undeclared PyTorch dependency. | Probe FFmpeg encoders directly. |
| Medium | AMD quality options incorrectly reused NVIDIA flags. | Use encoder-specific AMF CQP, NVENC CQ and QSV quality options. |
| Medium | Random-background preview treated the random sentinel as a filename. | Resolve the background selection before building the preview graph. |
| Medium | Folder drag-and-drop omitted GIFs despite folder import supporting them. | Use consistent folder discovery for both paths. |
| Medium | Packaging could omit the separate transcription bundle. | Build helper assembles both bundles; dependency-collection errors no longer disappear silently. |
| Documentation | Installation notes advertised absent AI clipping, downloading, OAuth and unrelated dependencies. | Replace them with the actual installation/build guide. |
| Documentation | README screenshot was missing and dependency descriptions were obsolete. | Add real screenshots, exact workflow documentation and four Mermaid diagrams. |

## English adaptation

The interface, tooltips, errors, presets, workflow names, subtitle editor, installer, comments/docstrings and documentation are in English. Background filenames use English names. The public author identity and MIT attribution use `loveinterium228`; the footer links to GitHub. Retired promotional/payment links have been removed.

The installer upgrade GUID and the application's data-directory name are retained so this presentation update does not create a separate application identity or data location.

## Verification evidence

The final results are recorded after the complete verification run. The suite uses actual FFmpeg processes, real Qt widgets and synthetic media. It does not substitute fake FFmpeg success responses for rendering tests.

- Full pytest regression suite: **89 passing tests**, including 30 additional deterministic logic cases for source duration precedence, inactive backgrounds, speed/trim priority, invalid inputs, source preservation, cancellation and SRT time boundaries.
- Ruff source checks and Python syntax compilation.
- All **27 fixed filters**, random color and random-filter selection rendered successfully with the tested FFmpeg build.
- Real CPU Whisper `tiny` transcription of an English speech sample, both from source and from `rm-transcribe.exe`. The recognized output included “Create vertical videos and captions” and “on your computer.” The product name was transcribed imperfectly, illustrating that captions still need human review.
- Both GUI and isolated speech PyInstaller bundles built successfully on Windows.
- Dark/light and transform screenshots captured from the running Qt application using synthetic demonstration media. Pixels inspected for legibility and layout.
- Source and deliverable scans for untranslated project text, retired identity links and missing local documentation assets.

The extra logical checks reproduced and fixed one further issue before publication: original-format export and preview attempted to select a random split-screen background even though that output mode does not use one. An empty background library could therefore block an unrelated transcode. Background selection now happens only for vertical split-screen processing.

Local environment: Windows x64, Python 3.12, PyQt5 5.15.11, QtAwesome 1.4.2, faster-whisper 1.2.1, PyAV 16.0.1, FFmpeg/FFprobe 9.0.2 and PyInstaller 6.22.3. External versions are recorded as test evidence, not minimum compatibility promises.

## Practical limits and remaining release work

- **Hardware coverage:** GPU encoders are probed on startup, but successful NVENC/QSV/AMF exports were not validated on separate supported GPUs. The CPU path is the validated rendering baseline.
- **Platforms:** Windows was tested locally. The included Linux CI workflow has not run in GitHub during this local task; macOS was not tested.
- **Installer:** Inno Setup compilation, installation, upgrades, signing and uninstall were not exercised. The scripts and bundle layout were reviewed.
- **Transcription:** The real-model check used `tiny` and one synthetic English sample. It is a pipeline smoke test, not an accuracy benchmark for all models/languages.
- **Preview scope:** Main preview omits captions, audio, speed and variations. The separate caption preview uses the source canvas. This behavior is explicitly documented.
- **Media permissions:** The supplied background clips have no documented provenance. See [third-party notes](../THIRD_PARTY_NOTICES.md) before including them in a public release.
- **Hard termination:** A forced OS kill or power loss can leave an owned partial/reservation file. Normal cancellation and handled errors clean up their files. Completed exports are not overwritten.
- **Durations without stream metadata:** When a container omits video duration, probing falls back to the container duration. FFmpeg still limits the final render; unusual or damaged media may need repair before import.

The review fixes reproduced issues and improves the release foundation. It does not claim that every possible codec, driver, input container or external dependency combination has been exhaustively tested.
