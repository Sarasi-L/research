#backend/services/utils/env_fix.py
import os
import platform
from pathlib import Path

def fix_windows_conda():
    if platform.system() == "Windows" and "CONDA_PREFIX" in os.environ:
        env_path = Path(os.environ["CONDA_PREFIX"])
        bin_path = env_path / "Library" / "bin"
        mingw_path = env_path / "Library" / "mingw-w64" / "bin"

        if bin_path.exists():
            os.add_dll_directory(str(bin_path))
        if mingw_path.exists():
            os.add_dll_directory(str(mingw_path))
