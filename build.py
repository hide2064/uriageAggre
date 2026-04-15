#!/usr/bin/env python3
"""Build: compile Vue then package with PyInstaller."""
import subprocess
import sys
from pathlib import Path


def build_frontend():
    print("[*] Building Vue frontend...")
    subprocess.run(["npm", "run", "build"], cwd=Path(__file__).parent / "frontend", check=True)
    print("[OK] Frontend built.")


def build_exe():
    print("[*] Running PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"],
        check=True,
    )
    print("[OK] Executable built in dist/SalesAggregator/")


if __name__ == "__main__":
    build_frontend()
    build_exe()
    print("\nBuild complete: dist/SalesAggregator/SalesAggregator.exe")
