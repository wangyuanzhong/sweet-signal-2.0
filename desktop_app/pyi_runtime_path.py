# PyInstaller one-file: PortAudio (sounddevice) loads via ctypes; DLLs live under
# sys._MEIPASS. Ensure that directory is searched before import side-effects run.
import os
import sys

if getattr(sys, 'frozen', False):
    root = getattr(sys, "_MEIPASS", None)
    if root:
        os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
