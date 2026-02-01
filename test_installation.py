#!/usr/bin/env python3
"""
Test script to verify NarrAider installation
Run this before first use to check everything is configured correctly.
"""

import os
import sys
import json
from pathlib import Path

def test_installation():
    """Run installation checks."""
    print("="*60)
    print("NarrAider Installation Test")
    print("="*60)
    print()

    all_good = True

    # Check Python version
    print("1. Checking Python version...")
    if sys.version_info >= (3, 8):
        print(f"   [OK] Python {sys.version_info.major}.{sys.version_info.minor} (OK)")
    else:
        print(f"   [X] Python {sys.version_info.major}.{sys.version_info.minor} (Need 3.8+)")
        all_good = False

    # Check required modules
    print("\n2. Checking required Python modules...")
    required = ['requests', 'tkinter']
    for module in required:
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
            print(f"   [OK] {module}")
        except ImportError:
            print(f"   [X] {module} (Run: pip install {module})")
            all_good = False

    # Check config file
    print("\n3. Checking configuration file...")
    config_path = Path(__file__).parent / "narraider_config.json"
    if config_path.exists():
        print(f"   [OK] Config file exists")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Check llama server path
        server_path = Path(config.get("llama_server_path", ""))
        if server_path.exists():
            print(f"   [OK] llama-server found: {server_path}")
        else:
            print(f"   [X] llama-server NOT found: {server_path}")
            print(f"      Download from: https://github.com/ggerganov/llama.cpp/releases")
            all_good = False

        # Check models
        models = config.get("models", {})
        for model_type, model_path in models.items():
            model_file = Path(model_path)
            if model_file.exists():
                size_gb = model_file.stat().st_size / (1024**3)
                print(f"   [OK] Model '{model_type}': {model_file.name} ({size_gb:.1f} GB)")
            else:
                print(f"   [X] Model '{model_type}' NOT found: {model_path}")
                print(f"      Download from HuggingFace (see README.md)")
                all_good = False

    else:
        print(f"   [X] Config file NOT found")
        print(f"      Run narraider.py once to create default config")
        all_good = False

    # Check output folders
    print("\n4. Checking output folders...")
    output_dir = Path(__file__).parent / "outputs"
    expected_folders = [
        "characters", "magic_systems", "science_systems", "artifacts",
        "cultures", "relationships", "concepts", "scenes", "image_prompts"
    ]

    if output_dir.exists():
        print(f"   [OK] Output directory exists: {output_dir}")
        for folder in expected_folders:
            folder_path = output_dir / folder
            if folder_path.exists():
                print(f"   [OK] {folder}/")
            else:
                print(f"   [!] {folder}/ (will be created on first use)")
    else:
        print(f"   [!] Output directory will be created on first use")

    # Check core files
    print("\n5. Checking core files...")
    core_files = [
        "narraider.py",
        "narraider_gui.py",
        "README.md",
        "QUICKSTART.md"
    ]

    for filename in core_files:
        file_path = Path(__file__).parent / filename
        if file_path.exists():
            print(f"   [OK] {filename}")
        else:
            print(f"   [X] {filename} (MISSING!)")
            all_good = False

    # Final verdict
    print("\n" + "="*60)
    if all_good:
        print("[OK] Installation looks good!")
        print("\nNext steps:")
        print("1. Run: python narraider_gui.py")
        print("2. Or: python narraider.py --type character --prompt 'Test character'")
        print("\nSee QUICKSTART.md for a 5-minute tutorial")
    else:
        print("[X] Installation has issues")
        print("\nPlease fix the errors above, then run this test again.")
        print("See README.md for detailed installation instructions")

    print("="*60)

    return all_good

if __name__ == "__main__":
    success = test_installation()
    sys.exit(0 if success else 1)
