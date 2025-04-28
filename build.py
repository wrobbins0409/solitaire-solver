#!/usr/bin/env python3
"""
Build script for creating the Solitaire Solver executable.
This script uses PyInstaller to create a standalone .exe file.
"""
import os
import subprocess
import hashlib
import sys


def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    # Check if PyInstaller is installed and install it if needed
    try:
        subprocess.run(["pyinstaller", "--version"],
                       check=True, capture_output=True)
        print("PyInstaller is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully.")

    # Create the executable
    print("Building executable...")

    # Build the command arguments
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "SolitaireSolver"
    ]

    # Add icon - using the correct path to the solitaire.ico file
    icon_path = "assets/solitaire.ico"
    if os.path.exists(icon_path):
        print(f"Found icon at {icon_path}")
        pyinstaller_args.extend(["--icon", icon_path])
    else:
        print(f"Warning: Icon file not found at {icon_path}")
        # List files in assets directory to help debug
        if os.path.exists("assets"):
            print("Files in assets directory:")
            for file in os.listdir("assets"):
                print(f"  - {file}")

    # Add the script to compile
    pyinstaller_args.append("run.py")

    print(f"Running PyInstaller with command: {' '.join(pyinstaller_args)}")
    subprocess.check_call(pyinstaller_args)

    print("\nExecutable created successfully!")
    print("Check the dist directory for SolitaireSolver.exe")


if __name__ == "__main__":
    main()
