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
    wine_prefix = config["wineprefix"]
    os.environ["WINEPREFIX"] = wine_prefix
    os.environ["WINEDEBUG"] = "-all"
    
    # Cari wine executable
    wine_dir = Path(config["wine_path"]) / "bin"
    wine_exe = wine_dir / "wine"
    wineserver_exe = wine_dir / "wineserver"
    
    if not wine_exe.exists():
        print("Error: Wine tidak ditemukan")
        sys.exit(1)
    
    # Cari afterfx.exe
    aenux_path = Path(config["aenux_path"])
    afterfx_exe = aenux_path / "AfterFX.exe"
    
    if not afterfx_exe.exists():
        print("Error: AfterFX.exe tidak ditemukan")
        sys.exit(1)
    
    # Jalankan AfterFX
    print(f"Running: {wine_exe} {afterfx_exe}")
    
    try:
        # Jalankan AfterFX
        subprocess.run([str(wine_exe), str(afterfx_exe)], check=True)
    except subprocess.CalledProcessError:
        print("AfterFX exited with error")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Kill wine processes setelah AfterFX ditutup
        print("Cleaning up wine processes...")
        
        # Cek apakah wineserver ada
        if wineserver_exe.exists():
            try:
                # Coba terminasi dengan normal
                result = subprocess.run(
                    [str(wineserver_exe), "-k"],
                    env={**os.environ, "WINEPREFIX": wine_prefix},
                    timeout=5,
                    capture_output=True,
                    text=True
                )
                print(f"Wineserver output: {result.stdout}")
                if result.stderr:
                    print(f"Wineserver errors: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("Normal termination timeout, trying force kill...")
                # Force kill jika timeout
                subprocess.run(
                    [str(wineserver_exe), "-k", "9"],
                    env={**os.environ, "WINEPREFIX": wine_prefix},
                    timeout=10
                )
        else:
            print(f"Warning: wineserver not found at {wineserver_exe}")
            print("Trying alternative cleanup methods...")
            
            # Alternatif: cari wine processes secara manual
            try:
                # Gunakan pkill untuk mencari proses dengan WINEPREFIX
                subprocess.run(
                    ["pkill", "-f", f"WINEPREFIX={wine_prefix}"],
                    timeout=5
                )
            except:
                pass
            
            # Coba kill dengan wineboot
            wineboot_exe = wine_dir / "wineboot"
            if wineboot_exe.exists():
                try:
                    subprocess.run(
                        [str(wineboot_exe), "-k"],
                        env={**os.environ, "WINEPREFIX": wine_prefix},
                        timeout=5
                    )
                except:
                    pass
        
        print("Cleanup completed")

if __name__ == "__main__":
    main()
