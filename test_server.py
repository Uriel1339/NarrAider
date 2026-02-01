#!/usr/bin/env python3
"""
Test script to manually start llama-server and verify it works.
"""

import subprocess
import time
from pathlib import Path
import sys

# Your paths (update these to match your installation)
SERVER_PATH = Path("/path/to/llama-server/llama-server.exe")
MODEL_PATH = Path("/path/to/models/gemma-3-27b-it-Q4_K_M.gguf")

print("="*60)
print("llama-server Test Script")
print("="*60)

# Check files exist
print("\n1. Checking files...")
if not SERVER_PATH.exists():
    print(f"ERROR: Server not found at {SERVER_PATH}")
    sys.exit(1)
print(f"[OK] Server: {SERVER_PATH}")

if not MODEL_PATH.exists():
    print(f"ERROR: Model not found at {MODEL_PATH}")
    sys.exit(1)
print(f"[OK] Model: {MODEL_PATH}")

# Build command
cmd = [
    str(SERVER_PATH),
    "-m", str(MODEL_PATH),
    "--port", "8081",
    "--ctx-size", "8192",
    "-ngl", "99",
    "--log-disable"
]

print("\n2. Starting server...")
print(f"Working directory: {SERVER_PATH.parent}")
print(f"Command: {' '.join(cmd)}")

try:
    process = subprocess.Popen(
        cmd,
        cwd=str(SERVER_PATH.parent),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print(f"[OK] Server started with PID: {process.pid}")
    print("\nWaiting 15 seconds for server to initialize...")
    print("Check the new console window that appeared!")

    time.sleep(15)

    # Check if still running
    if process.poll() is None:
        print("\n[OK] Server is still running!")
        print("\nPress Ctrl+C to stop the server...")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping server...")
            process.terminate()
            process.wait()
            print("[OK] Server stopped")
    else:
        print(f"\n[ERROR] Server exited with code: {process.returncode}")
        stdout, stderr = process.communicate()
        if stdout:
            print(f"STDOUT:\n{stdout}")
        if stderr:
            print(f"STDERR:\n{stderr}")

except Exception as e:
    print(f"[ERROR] Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTest complete!")
