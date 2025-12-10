#!/usr/bin/python3
"""
AeNux Runner - Minimal Version
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def main():
    # Baca config
    config_path = Path(__file__).parent / "aenux_config.json"
    if not config_path.exists():
        print("Error: Config file tidak ditemukan")
        sys.exit(1)
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Setup environment
    os.environ["WINEPREFIX"] = config["wineprefix"]
    os.environ["WINEDEBUG"] = "-all"
    
    # Cari wine executable
    wine_dir = Path(config["wine_path"]) / "bin"
    wine_exe = wine_dir / "wine"
    
    if not wine_exe.exists():
        print("Error: Wine tidak ditemukan")
        sys.exit(1)
    
    # Cari afterfx.exe
    aenux_path = Path(config["aenux_path"])
    afterfx_exe = aenux_path / "AfterFX.exe"
    
    if not afterfx_exe.exists():
        print("Error: AfterFX.exe tidak ditemukan")
        sys.exit(1)
    
    # Jalankan
    print(f"Running: {wine_exe} {afterfx_exe}")
    subprocess.run([str(wine_exe), str(afterfx_exe)])

if __name__ == "__main__":
    main()
    