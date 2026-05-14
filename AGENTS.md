# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Sweet Signal 2.0 is a macaron-themed pure tone (sine wave) generator with two modes:

- **Web mode** (`web/index.html`): Standalone HTML/CSS/JS using Web Audio API, no backend needed.
- **Desktop mode** (`desktop_app/main.py`): Python app using `pywebview` + `sounddevice` (NumPy + PortAudio) for system audio output.

### Running the web version

Serve `web/index.html` via any HTTP server:
```bash
source .venv/bin/activate
python -m http.server 8080 --directory web
```
Then open `http://localhost:8080/index.html` in Chrome.

### Running the desktop version

The desktop app requires a display server (X11/Wayland) and audio output device. On a headless Cloud VM, it will fail to open a GUI window. Use the web version for testing on Cloud VMs instead.

```bash
source .venv/bin/activate
cd desktop_app && python main.py
```

### System dependencies (Linux)

The following system packages are required for the Python dependencies to work:
- `libportaudio2` — required by `sounddevice`
- `python3-gi`, `gir1.2-webkit2-4.1`, `gobject-introspection` — required by `pywebview` on Linux
- `python3.12-venv` — required for creating virtual environments

### Key caveats

- There are **no automated tests or linters** in this repository. Verification is manual: open the web UI and confirm Play/Stop, frequency knob, and volume slider work.
- The desktop app (`pywebview`) will not launch on headless VMs; always use the web version for Cloud Agent testing.
- Build/packaging instructions are in `docs/BUILD.md`. CI builds a Windows `.exe` via GitHub Actions (see `.github/workflows/build-windows.yml`).
- When editing UI, keep both `desktop_app/src/index.html` (desktop) and `web/index.html` (browser) in sync.
