# PyInstaller frozen build: PortAudio (sounddevice) loads via ctypes; DLLs live under
# sys._MEIPASS (one-file and one-folder layouts). Prepend _MEIPASS to PATH before imports
# that load native code.
import os
import sys

if getattr(sys, 'frozen', False):
    root = getattr(sys, "_MEIPASS", None)
    if root:
        os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
