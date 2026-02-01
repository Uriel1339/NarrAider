#!/usr/bin/env python3
"""
NarrAider Unified GUI - All-in-one narrative creation tool
Created by Andreas "Uriel1339" Lopez

Beginner-friendly interface with setup wizard, model management, and generation.
MIT License - Free to use, modify, and distribute.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import json
import subprocess
import os
import sys
import urllib.request
import hashlib
from pathlib import Path
from datetime import datetime
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Version
VERSION = "2.0.0"

# Import core functionality
try:
    from narraider import (
        load_config, ensure_model_loaded, generate_content,
        save_output, kill_server,
        TEMPLATES, SYSTEM_PROMPTS,
        save_custom_system_prompt, delete_custom_system_prompt, is_custom_system_prompt
    )
    import narraider
    # Load config immediately (load_config sets narraider.CONFIG as a side effect)
    load_config()
    CONFIG = narraider.CONFIG
    if CONFIG is None:
        raise RuntimeError("Failed to load configuration")
except ImportError:
    print("ERROR: narraider.py not found. Make sure it's in the same directory.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to initialize: {e}")
    sys.exit(1)

def set_window_icon(window):
    """Set the NarrAider logo as window icon if available."""
    if not PILLOW_AVAILABLE:
        return

    logo_path = Path(__file__).parent / "narraider-logo.jpg"
    if not logo_path.exists():
        return

    try:
        # Load and resize logo for icon use
        img = Image.open(logo_path)
        img = img.resize((64, 64), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        window.iconphoto(True, photo)
        # Keep reference to prevent garbage collection
        window._logo_image = photo
    except Exception as e:
        print(f"Warning: Could not load logo: {e}")

class SetupWizard:
    """First-time setup wizard for beginners."""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("NarrAider Setup Wizard")
        self.window.geometry("700x500")
        set_window_icon(self.window)
        self.window.transient(parent)
        self.window.grab_set()

        self.current_step = 0
        self.steps = [
            self.step_welcome,
            self.step_detect_gpu,
            self.step_recommend_models,
            self.step_llama_server,
            self.step_finish
        ]

        self.gpu_tier = None  # Will be "tier1" (24GB) or "tier2" (10GB)
        self.model_choices = []

        # Main container
        self.container = ttk.Frame(self.window, padding="20")
        self.container.pack(fill=tk.BOTH, expand=True)

        # Show first step
        self.show_step()

    def show_step(self):
        """Display current step."""
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()

        # Run current step
        self.steps[self.current_step]()

    def next_step(self):
        """Go to next step."""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.show_step()

    def prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()

    def step_welcome(self):
        """Welcome screen."""
        ttk.Label(
            self.container,
            text="Welcome to NarrAider!",
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))

        text = """NarrAider is an AI-powered creative writing assistant that runs locally on your computer.

This wizard will help you:
- Detect your GPU and recommend models
- Guide you through downloading models
- Set up the AI server
- Get you creating in 5 minutes!

Everything runs on YOUR computer - no cloud, no subscriptions, completely private.

Click 'Next' to begin setup."""

        ttk.Label(
            self.container,
            text=text,
            wraplength=600,
            justify=tk.LEFT
        ).pack(pady=20)

        # Navigation
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        ttk.Button(nav_frame, text="Next", command=self.next_step).pack(side=tk.RIGHT)
        ttk.Button(nav_frame, text="Exit", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def step_detect_gpu(self):
        """Detect GPU and determine tier."""
        ttk.Label(
            self.container,
            text="Step 1: GPU Detection",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))

        info_frame = ttk.Frame(self.container)
        info_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            info_frame,
            text="Detecting your GPU...",
            font=("Arial", 12)
        ).pack(pady=10)

        # Try to detect GPU
        gpu_info = self.detect_gpu()

        result_text = scrolledtext.ScrolledText(info_frame, height=10, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True, pady=10)

        if gpu_info:
            result_text.insert("1.0", f"Detected GPU:\n{gpu_info}\n\n")

            # Determine tier
            vram = self.estimate_vram(gpu_info)
            if vram >= 20:
                self.gpu_tier = "tier1"
                tier_text = "[TIER 1] Tier 1: High-end GPU (24GB VRAM)\n"
                tier_text += "You can use the best models for highest quality output\n"
                tier_text += "Recommended: Gemma-3-27B-IT (~17GB)"
            elif vram >= 8:
                self.gpu_tier = "tier2"
                tier_text = "[TIER 2] Tier 2: Mid-range GPU (10-12GB VRAM)\n"
                tier_text += "You can use excellent 13B models\n"
                tier_text += "Recommended: MythoMax L2 13B (~8GB)"
            else:
                self.gpu_tier = "tier2"
                tier_text = "[BUDGET] Budget Tier: Lower VRAM\n"
                tier_text += "You can use optimized 7B models\n"
                tier_text += "Recommended: Mistral 7B (~5GB)"

            result_text.insert(tk.END, tier_text)
        else:
            result_text.insert("1.0", "Could not detect GPU automatically.\n\n")
            result_text.insert(tk.END, "Please select your GPU tier manually:\n\n")
            result_text.insert(tk.END, "Tier 1: RTX 4090, RTX 3090, RTX 4080 (24GB)\n")
            result_text.insert(tk.END, "Tier 2: RTX 3080, RTX 4070, RTX 3060 12GB (10GB)\n")

            self.gpu_tier = "tier2"  # Default to tier2 if detection fails

        result_text.config(state=tk.DISABLED)

        # Manual selection
        manual_frame = ttk.LabelFrame(info_frame, text="Or choose manually:", padding=10)
        manual_frame.pack(fill=tk.X, pady=10)

        tier_var = tk.StringVar(value=self.gpu_tier)

        ttk.Radiobutton(
            manual_frame,
            text="Tier 1: RTX 4090 / 3090 (24GB VRAM) - Best quality",
            variable=tier_var,
            value="tier1",
            command=lambda: setattr(self, 'gpu_tier', tier_var.get())
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            manual_frame,
            text="Tier 2: RTX 3080 / 4070 (10GB VRAM) - Excellent balance",
            variable=tier_var,
            value="tier2",
            command=lambda: setattr(self, 'gpu_tier', tier_var.get())
        ).pack(anchor=tk.W)

        # Navigation
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        ttk.Button(nav_frame, text="Next", command=self.next_step).pack(side=tk.RIGHT)
        ttk.Button(nav_frame, text="Back", command=self.prev_step).pack(side=tk.RIGHT, padx=5)

    def detect_gpu(self):
        """Try to detect GPU using nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def estimate_vram(self, gpu_info):
        """Estimate VRAM from GPU info string."""
        try:
            # Extract memory value (e.g., "24576 MiB")
            parts = gpu_info.split(',')
            if len(parts) >= 2:
                mem_str = parts[1].strip()
                mem_value = int(mem_str.split()[0])
                return mem_value / 1024  # Convert MiB to GB
        except:
            pass
        return 0

    def step_recommend_models(self):
        """Recommend models based on tier."""
        ttk.Label(
            self.container,
            text="Step 2: Recommended Models",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))

        info_text = scrolledtext.ScrolledText(self.container, height=15, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, pady=10)

        if self.gpu_tier == "tier1":
            recommendations = """[TIER 1] TIER 1 RECOMMENDATIONS (24GB VRAM)

These are high-quality models for best worldbuilding results:

1. CREATIVE WRITING (Required):
   Model: Gemma-3-27B-IT Q4_K_M (~17GB)
   Download: https://huggingface.co/bartowski/google_gemma-3-27b-it-GGUF
   File: google_gemma-3-27b-it-Q4_K_M.gguf

   Best for: Character profiles, worldbuilding, magic systems, scenes

2. EXPLICIT CONTENT (Optional):
   Model: Amoral-Gemma3-27B Q4_K_M (~17GB)
   Download: https://huggingface.co/mradermacher/amoral-gemma3-27B-v2-i1-GGUF
   File: amoral-gemma3-27B-v2-i1-Q4_K_M.gguf

   Best for: Adult scenes, mature content

INSTALLATION:
1. Click the download links above
2. Download the .gguf files
3. Save to your models folder (you'll configure the exact path in Settings)
4. Come back here and click 'Next'

You can use both models interchangeably!"""

        else:  # tier2
            recommendations = """[TIER 2] TIER 2 RECOMMENDATIONS (10-12GB VRAM)

Optimized for RTX 3080, RTX 4070, RTX 3060 12GB:

1. CREATIVE WRITING (Pick ONE):

   A) MythoMax L2 13B Q4_K_M (~7.9GB) - RECOMMENDED
      Download: https://huggingface.co/TheBloke/MythoMax-L2-13B-GGUF
      File: mythomax-l2-13b.Q4_K_M.gguf
      Best for: Rich descriptions, fantasy, roleplay, creative prose

   B) Chronos Hermes 13B Q4_K_M (~7.9GB) - ALTERNATIVE
      Download: https://huggingface.co/TheBloke/Chronos-Hermes-13b-v2-GGUF
      File: chronos-hermes-13b-v2.Q4_K_M.gguf
      Best for: Strong narratives, instruction following

   C) Mistral 7B Q6_K (~5.9GB) - BUDGET OPTION
      Download: https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF
      File: Mistral-7B-Instruct-v0.3-Q6_K.gguf
      Best for: If you have <10GB VRAM or want more headroom

2. EXPLICIT CONTENT (Optional):
   Model: Stheno v3.2 8B Q4_K_M (~4.9GB)
   Download: https://huggingface.co/bartowski/L3-8B-Stheno-v3.2-GGUF
   File: L3-8B-Stheno-v3.2-Q4_K_M.gguf

INSTALLATION:
1. Click the download links above
2. Download at least ONE creative writing model
3. Save to your models folder (you'll configure the exact path in Settings)
4. Come back here and click 'Next'"""

        info_text.insert("1.0", recommendations)
        info_text.config(state=tk.DISABLED)

        # Open folder button
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="[Folder] Open Models Folder",
            command=self.open_models_folder
        ).pack(side=tk.LEFT)

        ttk.Label(
            btn_frame,
            text="  ← Save downloaded .gguf files here",
            foreground="blue"
        ).pack(side=tk.LEFT, padx=10)

        # Navigation
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        ttk.Button(nav_frame, text="Next", command=self.next_step).pack(side=tk.RIGHT)
        ttk.Button(nav_frame, text="Back", command=self.prev_step).pack(side=tk.RIGHT, padx=5)

    def open_models_folder(self):
        """Open models folder in file explorer."""
        # Check config first, otherwise use home directory default
        if CONFIG and 'models' in CONFIG and CONFIG['models']:
            # Get first model path and use its parent directory
            first_model = list(CONFIG['models'].values())[0]
            models_path = Path(first_model).parent
        else:
            # Default to ~/ai-models
            models_path = Path.home() / "ai-models"

        models_path.mkdir(parents=True, exist_ok=True)

        if os.name == 'nt':  # Windows
            os.startfile(models_path)
        elif os.name == 'posix':  # Mac/Linux
            subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(models_path)])

    def step_llama_server(self):
        """Download llama.cpp server."""
        ttk.Label(
            self.container,
            text="Step 3: llama.cpp Server",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))

        info_text = scrolledtext.ScrolledText(self.container, height=12, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, pady=10)

        # Get suggested installation path
        suggested_path = Path.home() / "llama-server"

        instructions = f"""llama.cpp server runs the AI models locally.

DOWNLOAD INSTRUCTIONS:

Windows:
1. Visit: https://github.com/ggerganov/llama.cpp/releases
2. Download the latest release:
   - NVIDIA GPUs: llama-b[XXXX]-bin-win-cuda-cu12.2.0-x64.zip
   - AMD/Intel: llama-b[XXXX]-bin-win-vulkan-x64.zip
   - CPU only: llama-b[XXXX]-bin-win-avx2-x64.zip
3. Extract the ZIP to a folder of your choice (suggested: {suggested_path})
4. Remember the path to llama-server.exe for configuration

macOS:
1. Download: llama-b[XXXX]-bin-macos-arm64.zip (M1/M2/M3)
   or llama-b[XXXX]-bin-macos-x64.zip (Intel)
2. Extract and remember the path to llama-server

Linux:
1. Build from source or download binary
2. See: https://github.com/ggerganov/llama.cpp

You'll configure the exact path in Settings after installation.
Click 'Open Download Link' to visit GitHub releases."""

        info_text.insert("1.0", instructions)
        info_text.config(state=tk.DISABLED)

        # Button frame
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="[Web] Open Download Link",
            command=lambda: self.open_url("https://github.com/ggerganov/llama.cpp/releases")
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="[Folder] Open Installation Folder",
            command=lambda: self.open_folder(str(Path.home()))
        ).pack(side=tk.LEFT, padx=10)

        # Check if llama-server exists (check config first)
        if CONFIG and 'llama_server_path' in CONFIG:
            server_path = Path(CONFIG['llama_server_path'])
        else:
            server_path = Path.home() / "llama-server" / "llama-server.exe"
        if server_path.exists():
            status_label = ttk.Label(
                btn_frame,
                text="[OK] llama-server.exe found!",
                foreground="green",
                font=("Arial", 10, "bold")
            )
        else:
            status_label = ttk.Label(
                btn_frame,
                text="[!] llama-server.exe not found yet",
                foreground="orange",
                font=("Arial", 10, "bold")
            )
        status_label.pack(side=tk.LEFT, padx=10)

        # Navigation
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        ttk.Button(nav_frame, text="Next", command=self.next_step).pack(side=tk.RIGHT)
        ttk.Button(nav_frame, text="Back", command=self.prev_step).pack(side=tk.RIGHT, padx=5)

    def open_url(self, url):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)

    def open_folder(self, path):
        """Open folder in file explorer."""
        folder_path = Path(path)
        folder_path.mkdir(parents=True, exist_ok=True)

        if os.name == 'nt':
            os.startfile(folder_path)
        elif os.name == 'posix':
            subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(folder_path)])

    def step_finish(self):
        """Final step - verify installation."""
        ttk.Label(
            self.container,
            text="Setup Complete!",
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))

        # Run verification
        verification = self.verify_installation()

        result_text = scrolledtext.ScrolledText(self.container, height=15, wrap=tk.WORD)
        result_text.pack(fill=tk.BOTH, expand=True, pady=10)

        result_text.insert("1.0", "Checking installation...\n\n")

        all_good = True
        for check, status, message in verification:
            if status:
                result_text.insert(tk.END, f"[OK] {check}\n")
            else:
                result_text.insert(tk.END, f"[X] {check}\n")
                result_text.insert(tk.END, f"  -> {message}\n")
                all_good = False
            result_text.insert(tk.END, "\n")

        if all_good:
            result_text.insert(tk.END, "\n" + "="*50 + "\n")
            result_text.insert(tk.END, "[OK] Everything is ready!\n\n")
            result_text.insert(tk.END, "Click 'Start NarrAider' to begin creating.\n")
            result_text.insert(tk.END, "="*50)
        else:
            result_text.insert(tk.END, "\n" + "="*50 + "\n")
            result_text.insert(tk.END, "[!] Some items need attention.\n\n")
            result_text.insert(tk.END, "Fix the issues above, then re-run setup.\n")
            result_text.insert(tk.END, "="*50)

        result_text.config(state=tk.DISABLED)

        # Navigation
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        if all_good:
            ttk.Button(
                nav_frame,
                text="Start NarrAider!",
                command=self.window.destroy,
                style="Accent.TButton"
            ).pack(side=tk.RIGHT)
        else:
            ttk.Button(nav_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT)

        ttk.Button(nav_frame, text="Back", command=self.prev_step).pack(side=tk.RIGHT, padx=5)

    def verify_installation(self):
        """Verify installation is complete."""
        checks = []

        # Check llama-server (use config path if available)
        if CONFIG and 'llama_server_path' in CONFIG:
            server_path = Path(CONFIG['llama_server_path'])
        else:
            server_path = Path.home() / "llama-server" / "llama-server.exe"

        checks.append((
            "llama-server.exe installed",
            server_path.exists(),
            "Download from GitHub and configure path in Settings"
        ))

        # Check for at least one model (use config paths if available)
        if CONFIG and 'models' in CONFIG and CONFIG['models']:
            # Check if any configured model exists
            model_exists = any(Path(m).exists() for m in CONFIG['models'].values())
            model_count = sum(1 for m in CONFIG['models'].values() if Path(m).exists())
            checks.append((
                "At least one .gguf model downloaded",
                model_exists,
                f"Download models and configure in Settings. Found {model_count} configured models."
            ))
        else:
            # Fallback: check default location
            models_path = Path.home() / "ai-models"
            models_path.mkdir(parents=True, exist_ok=True)
            gguf_files = list(models_path.glob("*.gguf"))
            checks.append((
                "At least one .gguf model downloaded",
                len(gguf_files) > 0,
                f"Download a model and configure in Settings. Found {len(gguf_files)} models in {models_path}."
            ))

        # Check config exists
        config_path = Path(__file__).parent / "narraider_config.json"
        checks.append((
            "Configuration file exists",
            config_path.exists(),
            "Run narraider.py once to create config"
        ))

        # Check Python modules
        try:
            import requests
            checks.append(("Python 'requests' module", True, ""))
        except ImportError:
            checks.append(("Python 'requests' module", False, "Run: pip install requests"))

        return checks


class NarrAiderUnified:
    """Unified GUI for NarrAider."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"NarrAider {VERSION} - Unified Creation Suite")
        self.root.geometry("1200x800")
        set_window_icon(self.root)

        # Check if first run
        config_path = Path(__file__).parent / "narraider_config.json"
        if not config_path.exists():
            # Run setup wizard
            wizard = SetupWizard(self.root)
            self.root.wait_window(wizard.window)

        # Load configuration
        load_config()

        # Generation queue
        self.gen_queue = queue.Queue()
        self.generating = False

        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        """Setup the main UI."""

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Quick Generate (main interface)
        self.tab_generate = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_generate, text="Generate Content")
        self.setup_generate_tab()

        # Tab 2: Model Manager
        self.tab_models = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_models, text="Model Manager")
        self.setup_models_tab()

        # Tab 3: Settings
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="Settings")
        self.setup_settings_tab()

        # Tab 4: Help & Guides
        self.tab_help = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_help, text="[?] Help")
        self.setup_help_tab()

        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_generate_tab(self):
        """Setup main generation tab."""
        # Left panel: Controls
        left_panel = ttk.Frame(self.tab_generate, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        left_panel.pack_propagate(False)

        # Header
        ttk.Label(
            left_panel,
            text="What do you want to create?",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        # Content type selection
        ttk.Label(left_panel, text="Content Type:").pack(anchor=tk.W, pady=(5, 2))

        self.content_type = tk.StringVar(value="character")

        # Categorized content types
        categories = {
            "Characters & Lore": [
                ("Character Profile", "character"),
                ("Magic System", "magic"),
                ("Science/Tech System", "science"),
                ("Artifact/Relic", "artifact"),
                ("Culture/Species", "culture"),
                ("Relationships", "relationships"),
            ],
            "Scenes & Stories": [
                ("Dialogue Scene", "scene-dialogue"),
                ("Combat Scene", "scene-combat"),
                ("General Scene", "scene-general"),
                ("Explicit Scene", "scene-explicit"),
            ],
            "Full Projects": [
                ("Complete Book Concept", "concept"),
                ("Character Art Prompt", "image-prompt"),
            ]
        }

        self.type_map = {}
        type_display = []

        for category, items in categories.items():
            type_display.append(f"--- {category} ---")
            for display, value in items:
                type_display.append(display)
                self.type_map[display] = value

        type_combo = ttk.Combobox(
            left_panel,
            textvariable=self.content_type,
            values=type_display,
            state="readonly",
            width=28
        )
        type_combo.pack(fill=tk.X, pady=(0, 10))
        type_combo.bind("<<ComboboxSelected>>", self.on_type_changed)

        # Model selection
        ttk.Label(left_panel, text="Model:").pack(anchor=tk.W, pady=(5, 2))

        self.model_type = tk.StringVar(value="Creative Writing")
        model_combo = ttk.Combobox(
            left_panel,
            textvariable=self.model_type,
            values=["Creative Writing", "Explicit/Adult"],
            state="readonly",
            width=28
        )
        model_combo.pack(fill=tk.X, pady=(0, 5))

        # Model settings indicator
        self.model_settings_label = tk.Label(
            left_panel,
            text=f"CTX: {CONFIG.get('context_size', 8192)} | GPU: {CONFIG.get('gpu_layers', 99)} | Tokens: {CONFIG.get('generation_params', {}).get('max_tokens', 2048)}",
            font=("Arial", 8),
            fg="#666",
            anchor=tk.W
        )
        self.model_settings_label.pack(fill=tk.X, pady=(0, 10))

        # System prompt selection
        system_prompt_frame = ttk.Frame(left_panel)
        system_prompt_frame.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(system_prompt_frame, text="System Prompt:").pack(anchor=tk.W)

        system_select_frame = ttk.Frame(system_prompt_frame)
        system_select_frame.pack(fill=tk.X, pady=(2, 0))

        self.system_prompt = tk.StringVar(value="Default")
        self.system_combo = ttk.Combobox(
            system_select_frame,
            textvariable=self.system_prompt,
            values=list(SYSTEM_PROMPTS.keys()),
            state="readonly",
            width=20
        )
        self.system_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            system_select_frame,
            text="View/Edit",
            command=self.view_system_prompts,
            width=10
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Output format selection
        ttk.Label(left_panel, text="Output Format:").pack(anchor=tk.W, pady=(5, 2))

        self.output_format = tk.StringVar(value=".md")
        format_combo = ttk.Combobox(
            left_panel,
            textvariable=self.output_format,
            values=[".txt", ".md", ".html", ".json", ".xml"],
            state="readonly",
            width=28
        )
        format_combo.pack(fill=tk.X, pady=(0, 10))

        # Format descriptions
        format_descriptions = {
            ".txt": "Plain text - no formatting, clean prose",
            ".md": "Markdown - current output with formatting",
            ".html": "HTML - structured with headings, lists, tables",
            ".json": "JSON - data-optimized, template-aware",
            ".xml": "XML - data-optimized, template-aware"
        }

        self.format_hint = tk.Label(
            left_panel,
            text=format_descriptions[".md"],
            font=("Arial", 8),
            fg="#666",
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.format_hint.pack(fill=tk.X, pady=(0, 10))

        format_combo.bind("<<ComboboxSelected>>",
                         lambda e: self.format_hint.config(text=format_descriptions[self.output_format.get()]))

        # Description tooltip
        self.type_description = tk.Text(
            left_panel,
            height=4,
            wrap=tk.WORD,
            bg="#f0f0f0",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.type_description.pack(fill=tk.X, pady=10)

        # Example prompt button
        ttk.Button(
            left_panel,
            text="Tip: Show Example Prompt",
            command=self.show_example
        ).pack(fill=tk.X, pady=(10, 5))

        # Generate button
        self.generate_btn = ttk.Button(
            left_panel,
            text="=> Generate",
            command=self.generate,
            style="Accent.TButton"
        )
        self.generate_btn.pack(fill=tk.X, pady=(10, 5))

        # Progress bar
        self.progress = ttk.Progressbar(left_panel, mode='indeterminate')

        # Right panel: Prompt and output
        right_panel = ttk.Frame(self.tab_generate)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        # Prompt section
        prompt_frame = ttk.LabelFrame(right_panel, text="Your Prompt", padding=10)
        prompt_frame.pack(fill=tk.BOTH, pady=(0, 10))

        ttk.Label(
            prompt_frame,
            text="Describe what you want to generate:",
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=(0, 5))

        self.prompt_text = tk.Text(prompt_frame, height=6, wrap=tk.WORD)
        self.prompt_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Prompt optimizer button
        ttk.Button(
            prompt_frame,
            text="⚡ Optimize Prompt",
            command=self.optimize_prompt
        ).pack(fill=tk.X)

        # Output section
        output_frame = ttk.LabelFrame(right_panel, text="Generated Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Output buttons
        output_btn_frame = ttk.Frame(output_frame)
        output_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            output_btn_frame,
            text="Save",
            command=self.save_file
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            output_btn_frame,
            text="Copy",
            command=self.copy_to_clipboard
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            output_btn_frame,
            text="Clear",
            command=self.clear_output
        ).pack(side=tk.LEFT, padx=2)

        # Update type description
        self.on_type_changed()

    def setup_models_tab(self):
        """Setup model management tab."""
        # Create scrollable container
        canvas = tk.Canvas(self.tab_models)
        scrollbar = ttk.Scrollbar(self.tab_models, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        ttk.Label(
            scrollable_frame,
            text="Model Manager",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Active Models Section
        active_frame = ttk.LabelFrame(scrollable_frame, text="Configured Models", padding=10)
        active_frame.pack(fill=tk.X, padx=20, pady=10)

        # Get models from config
        models = CONFIG.get("models", {})

        # Creative Writing Model Card
        self.create_model_card(active_frame, "Creative Writing", models.get("worldbuilding", ""))

        # Explicit/Adult Model Card
        self.create_model_card(active_frame, "Explicit/Adult", models.get("explicit", ""))

        # Detected Models Section
        detect_frame = ttk.LabelFrame(scrollable_frame, text="Detected Models in Folder", padding=10)
        detect_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(
            detect_frame,
            text="🔍 Scan for Models",
            command=self.scan_for_models
        ).pack(pady=5)

        self.detected_models_text = tk.Text(detect_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.detected_models_text.pack(fill=tk.X, pady=5)

        # Download Recommendations Section
        dl_frame = ttk.LabelFrame(scrollable_frame, text="Download Recommendations", padding=10)
        dl_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(
            dl_frame,
            text="Based on your configuration, here are recommended models:",
            wraplength=600
        ).pack(pady=5)

        ttk.Button(
            dl_frame,
            text="📖 Open Setup Wizard",
            command=lambda: SetupWizard(self.root)
        ).pack(pady=5)

    def create_model_card(self, parent, model_name, model_path):
        """Create a model info card with preset management."""
        card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        card.pack(fill=tk.X, pady=5, padx=5)

        # Header
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(
            header_frame,
            text=model_name,
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)

        # Check if model exists
        model_file = Path(model_path) if model_path else None
        if model_file and model_file.exists():
            size_gb = model_file.stat().st_size / (1024**3)
            status_label = ttk.Label(
                header_frame,
                text=f"✓ Found ({size_gb:.1f} GB)",
                foreground="green"
            )
        else:
            status_label = ttk.Label(
                header_frame,
                text="✗ Not Found",
                foreground="red"
            )
        status_label.pack(side=tk.RIGHT)

        # Path
        ttk.Label(
            card,
            text=f"Path: {model_file.name if model_file and model_file.exists() else 'Not configured'}",
            font=("Arial", 9),
            foreground="#666"
        ).pack(anchor=tk.W, padx=10)

        # Preset management
        preset_frame = ttk.Frame(card)
        preset_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(preset_frame, text="Quick Preset:").pack(side=tk.LEFT, padx=(0, 5))

        preset_var = tk.StringVar(value="Use Global Settings")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=preset_var,
            values=["Use Global Settings", "Fast (4K CTX)", "Balanced (8K CTX)", "Quality (16K CTX)", "Maximum (24K CTX)", "Custom"],
            state="readonly",
            width=25
        )
        preset_combo.pack(side=tk.LEFT)

        # Buttons
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            btn_frame,
            text="Test Generate",
            command=lambda: self.test_model(model_name)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="Open Folder",
            command=lambda: self.open_model_folder(model_path)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="Change Model",
            command=lambda: self.change_model(model_name)
        ).pack(side=tk.LEFT, padx=2)

    def scan_for_models(self):
        """Scan for .gguf models in the models folder."""
        try:
            # Get models folder from config
            models = CONFIG.get("models", {})
            if models:
                first_model = list(models.values())[0]
                models_folder = Path(first_model).parent
            else:
                models_folder = Path.home() / "ai-models"

            if not models_folder.exists():
                self.detected_models_text.config(state=tk.NORMAL)
                self.detected_models_text.delete("1.0", tk.END)
                self.detected_models_text.insert("1.0", f"Models folder not found: {models_folder}")
                self.detected_models_text.config(state=tk.DISABLED)
                return

            # Find all .gguf files
            gguf_files = list(models_folder.glob("*.gguf"))

            # Get currently configured models
            configured = set(Path(m).name for m in models.values() if Path(m).exists())

            # Find unconfigured models
            unconfigured = [f for f in gguf_files if f.name not in configured]

            self.detected_models_text.config(state=tk.NORMAL)
            self.detected_models_text.delete("1.0", tk.END)

            if unconfigured:
                self.detected_models_text.insert("1.0", f"Found {len(unconfigured)} unconfigured model(s):\n\n")
                for model in unconfigured:
                    size_gb = model.stat().st_size / (1024**3)
                    self.detected_models_text.insert(tk.END, f"• {model.name} ({size_gb:.1f} GB)\n")
                self.detected_models_text.insert(tk.END, "\n[Use 'Change Model' buttons above to configure]")
            else:
                self.detected_models_text.insert("1.0", "No unconfigured models found.\n\nAll .gguf files in the folder are already configured.")

            self.detected_models_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan for models:\n{e}")

    def test_model(self, model_name):
        """Test generate with the selected model."""
        messagebox.showinfo("Test Generate", f"Test generation for {model_name} will be added in the next update.")

    def open_model_folder(self, model_path):
        """Open the folder containing the model."""
        if model_path:
            folder = Path(model_path).parent
            if folder.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
                elif os.name == 'posix':  # Mac/Linux
                    subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(folder)])
        else:
            messagebox.showwarning("No Path", "Model path not configured.")

    def change_model(self, model_name):
        """Change the model file for a specific model type."""
        filename = filedialog.askopenfilename(
            title=f"Select {model_name} model",
            filetypes=[("GGUF Model", "*.gguf"), ("All Files", "*.*")]
        )
        if filename:
            # Update config based on model name
            model_type = "worldbuilding" if "Creative" in model_name else "explicit"

            if model_type == "worldbuilding":
                self.worldbuilding_model_var.set(filename)
            else:
                self.explicit_model_var.set(filename)

            # Save config
            self.save_config()

            # Refresh model manager
            messagebox.showinfo("Success", f"Updated {model_name} model.\n\nRefresh the Model Manager tab to see changes.")

    def setup_settings_tab(self):
        """Setup settings tab."""
        # Create scrollable container
        canvas = tk.Canvas(self.tab_settings)
        scrollbar = ttk.Scrollbar(self.tab_settings, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        ttk.Label(
            scrollable_frame,
            text="NarrAider Configuration",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Quick Settings Presets
        preset_frame = ttk.LabelFrame(scrollable_frame, text="Quick Settings (GPU-Based Presets)", padding=10)
        preset_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(preset_frame, text="GPU VRAM Preset:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.gpu_preset_var = tk.StringVar(value="Custom")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.gpu_preset_var,
            values=["8GB VRAM", "12GB VRAM", "16GB VRAM", "24GB VRAM", "Custom"],
            state="readonly",
            width=20
        )
        preset_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        preset_combo.bind("<<ComboboxSelected>>", self.apply_gpu_preset)

        ttk.Label(
            preset_frame,
            text="(Auto-configures Context Size, GPU Layers, Max Tokens)",
            foreground="gray"
        ).grid(row=0, column=2, sticky=tk.W, padx=5)

        # Warning note
        warning_text = tk.Text(preset_frame, height=4, wrap=tk.WORD, font=("Arial", 9), relief=tk.FLAT, bg="#FFF3CD", fg="#856404")
        warning_text.grid(row=1, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)
        warning_text.insert("1.0", "NOTE: These are conservative recommendations based on llama.cpp community benchmarks (2025-2026). Always test with your specific GPU and model. KV cache grows with context size - if you get out-of-memory errors, reduce Context Size first (e.g., 8192→4096), then GPU Layers. Settings optimized for Q4_K_M quantization.")
        warning_text.config(state=tk.DISABLED)

        # llama.cpp Server Settings
        server_frame = ttk.LabelFrame(scrollable_frame, text="llama.cpp Server", padding=10)
        server_frame.pack(fill=tk.X, padx=20, pady=10)

        # Server path
        ttk.Label(server_frame, text="llama-server.exe Path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_path_var = tk.StringVar(value=CONFIG.get("llama_server_path", ""))
        server_entry = ttk.Entry(server_frame, textvariable=self.server_path_var, width=50)
        server_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(server_frame, text="Browse...", command=self.browse_server).grid(row=0, column=2, padx=5)

        # Server port
        ttk.Label(server_frame, text="Server Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=str(CONFIG.get("server_port", 8081)))
        ttk.Entry(server_frame, textvariable=self.port_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Model Settings
        model_frame = ttk.LabelFrame(scrollable_frame, text="Models", padding=10)
        model_frame.pack(fill=tk.X, padx=20, pady=10)

        # Worldbuilding model
        ttk.Label(model_frame, text="Creative Writing Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.worldbuilding_model_var = tk.StringVar(value=CONFIG.get("models", {}).get("worldbuilding", ""))
        wb_entry = ttk.Entry(model_frame, textvariable=self.worldbuilding_model_var, width=50)
        wb_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(model_frame, text="Browse...", command=lambda: self.browse_model("worldbuilding")).grid(row=0, column=2, padx=5)

        # Explicit model
        ttk.Label(model_frame, text="Explicit/Adult Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.explicit_model_var = tk.StringVar(value=CONFIG.get("models", {}).get("explicit", ""))
        exp_entry = ttk.Entry(model_frame, textvariable=self.explicit_model_var, width=50)
        exp_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(model_frame, text="Browse...", command=lambda: self.browse_model("explicit")).grid(row=1, column=2, padx=5)

        # Performance Settings
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance", padding=10)
        perf_frame.pack(fill=tk.X, padx=20, pady=10)

        # Context size
        ttk.Label(perf_frame, text="Context Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.context_var = tk.StringVar(value=str(CONFIG.get("context_size", 8192)))
        context_combo = ttk.Combobox(perf_frame, textvariable=self.context_var, values=["2048", "4096", "8192", "16384", "24576", "32768"], width=10)
        context_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(perf_frame, text="(Lower = faster, less memory)").grid(row=0, column=2, sticky=tk.W, padx=5)

        # GPU layers
        ttk.Label(perf_frame, text="GPU Layers:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.gpu_layers_var = tk.StringVar(value=str(CONFIG.get("gpu_layers", 99)))
        gpu_entry = ttk.Entry(perf_frame, textvariable=self.gpu_layers_var, width=10)
        gpu_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(perf_frame, text="(99 = full GPU offload, 0 = CPU only)").grid(row=1, column=2, sticky=tk.W, padx=5)

        # Keep server loaded
        self.keep_server_var = tk.BooleanVar(value=CONFIG.get("keep_server_loaded", False))
        keep_server_check = ttk.Checkbutton(
            perf_frame,
            text="Keep server loaded (faster subsequent generations, uses VRAM)",
            variable=self.keep_server_var
        )
        keep_server_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=10)

        # Generation Parameters
        gen_frame = ttk.LabelFrame(scrollable_frame, text="Generation Parameters", padding=10)
        gen_frame.pack(fill=tk.X, padx=20, pady=10)

        gen_params = CONFIG.get("generation_params", {})

        # Temperature
        ttk.Label(gen_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.temp_var = tk.DoubleVar(value=gen_params.get("temperature", 0.8))
        temp_scale = ttk.Scale(gen_frame, from_=0.1, to=2.0, variable=self.temp_var, orient=tk.HORIZONTAL, length=200)
        temp_scale.grid(row=0, column=1, padx=5, pady=5)
        self.temp_label = ttk.Label(gen_frame, text=f"{self.temp_var.get():.2f}")
        self.temp_label.grid(row=0, column=2, padx=5)
        temp_scale.configure(command=lambda v: self.temp_label.config(text=f"{float(v):.2f}"))
        ttk.Label(gen_frame, text="(Higher = more creative/random)").grid(row=0, column=3, sticky=tk.W, padx=5)

        # Top P
        ttk.Label(gen_frame, text="Top P:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.top_p_var = tk.DoubleVar(value=gen_params.get("top_p", 0.9))
        top_p_scale = ttk.Scale(gen_frame, from_=0.1, to=1.0, variable=self.top_p_var, orient=tk.HORIZONTAL, length=200)
        top_p_scale.grid(row=1, column=1, padx=5, pady=5)
        self.top_p_label = ttk.Label(gen_frame, text=f"{self.top_p_var.get():.2f}")
        self.top_p_label.grid(row=1, column=2, padx=5)
        top_p_scale.configure(command=lambda v: self.top_p_label.config(text=f"{float(v):.2f}"))

        # Top K
        ttk.Label(gen_frame, text="Top K:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.top_k_var = tk.StringVar(value=str(gen_params.get("top_k", 40)))
        ttk.Entry(gen_frame, textvariable=self.top_k_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Repeat penalty
        ttk.Label(gen_frame, text="Repeat Penalty:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.repeat_penalty_var = tk.DoubleVar(value=gen_params.get("repeat_penalty", 1.1))
        rp_scale = ttk.Scale(gen_frame, from_=1.0, to=1.5, variable=self.repeat_penalty_var, orient=tk.HORIZONTAL, length=200)
        rp_scale.grid(row=3, column=1, padx=5, pady=5)
        self.rp_label = ttk.Label(gen_frame, text=f"{self.repeat_penalty_var.get():.2f}")
        self.rp_label.grid(row=3, column=2, padx=5)
        rp_scale.configure(command=lambda v: self.rp_label.config(text=f"{float(v):.2f}"))

        # Max tokens
        ttk.Label(gen_frame, text="Max Tokens:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.StringVar(value=str(gen_params.get("max_tokens", 2048)))
        max_tokens_combo = ttk.Combobox(gen_frame, textvariable=self.max_tokens_var, values=["512", "1024", "2048", "4096"], width=10)
        max_tokens_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        # Output folder
        output_frame = ttk.LabelFrame(scrollable_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar(value=CONFIG.get("output_folder", "outputs/"))
        ttk.Entry(output_frame, textvariable=self.output_folder_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_folder).grid(row=0, column=2, padx=5)

        # Save/Reset buttons
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(btn_frame, text="Save Configuration", command=self.save_config, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Test Server", command=self.test_server).pack(side=tk.LEFT, padx=5)

    def apply_gpu_preset(self, event=None):
        """Apply GPU-based performance preset."""
        preset = self.gpu_preset_var.get()

        # Preset configurations based on VRAM and recent community research
        # Conservative settings verified against llama.cpp community benchmarks
        # Context size is the main VRAM consumer (KV cache grows linearly)
        presets = {
            "8GB VRAM": {
                "context_size": "4096",
                "gpu_layers": "99",
                "max_tokens": "1024",
                "description": "RTX 3060 Ti, RTX 2080 - 7B-13B models Q4_K_M. Safe for 13B, can try 8192 ctx for 7B."
            },
            "12GB VRAM": {
                "context_size": "8192",
                "gpu_layers": "99",
                "max_tokens": "2048",
                "description": "RTX 3060 12GB, RTX 3080, RTX 4070 - Sweet spot for 13B-14B Q4_K_M. 30-150+ tok/s."
            },
            "16GB VRAM": {
                "context_size": "8192",
                "gpu_layers": "99",
                "max_tokens": "2048",
                "description": "RTX 4060 Ti 16GB - Handles 13B-27B Q4_K_M. Can increase ctx to 16384 for smaller models."
            },
            "24GB VRAM": {
                "context_size": "24576",
                "gpu_layers": "99",
                "max_tokens": "4096",
                "description": "RTX 3090, RTX 4090 - Runs 22-35B Q4_K_M (Gemma 3 27B). Proven NightShift settings."
            }
        }

        if preset in presets:
            config = presets[preset]
            self.context_var.set(config["context_size"])
            self.gpu_layers_var.set(config["gpu_layers"])
            self.max_tokens_var.set(config["max_tokens"])

            self.status_bar.config(text=f"Applied preset: {preset} - {config['description']}")

    def browse_server(self):
        """Browse for llama-server executable."""
        filename = filedialog.askopenfilename(
            title="Select llama-server executable",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if filename:
            self.server_path_var.set(filename)

    def browse_model(self, model_type):
        """Browse for model file."""
        filename = filedialog.askopenfilename(
            title=f"Select {model_type} model",
            filetypes=[("GGUF Model", "*.gguf"), ("All Files", "*.*")]
        )
        if filename:
            if model_type == "worldbuilding":
                self.worldbuilding_model_var.set(filename)
            else:
                self.explicit_model_var.set(filename)

    def browse_output_folder(self):
        """Browse for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)

    def save_config(self):
        """Save configuration to file."""
        try:
            config = {
                "llama_server_path": self.server_path_var.get(),
                "models": {
                    "worldbuilding": self.worldbuilding_model_var.get(),
                    "explicit": self.explicit_model_var.get()
                },
                "server_port": int(self.port_var.get()),
                "context_size": int(self.context_var.get()),
                "gpu_layers": int(self.gpu_layers_var.get()),
                "output_folder": self.output_folder_var.get(),
                "keep_server_loaded": self.keep_server_var.get(),
                "generation_params": {
                    "temperature": float(self.temp_var.get()),
                    "top_p": float(self.top_p_var.get()),
                    "top_k": int(self.top_k_var.get()),
                    "repeat_penalty": float(self.repeat_penalty_var.get()),
                    "max_tokens": int(self.max_tokens_var.get())
                }
            }

            config_path = Path(__file__).parent / "narraider_config.json"
            print(f"[DEBUG] Saving config to: {config_path}")
            print(f"[DEBUG] Config content: {json.dumps(config, indent=2)}")

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print("[DEBUG] Config file written successfully")

            # Reload config in memory
            global CONFIG
            import narraider
            CONFIG = config
            narraider.CONFIG = config

            print("[DEBUG] CONFIG updated in memory")

            messagebox.showinfo("Success", f"Configuration saved successfully!\n\nSaved to: {config_path}\n\nRestart NarrAider for all changes to take effect.")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")

    def reset_config(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno("Reset Configuration", "Reset all settings to defaults?"):
            # Use platform-agnostic default paths
            home = Path.home()
            self.server_path_var.set(str(home / "llama-server" / "llama-server.exe"))
            self.worldbuilding_model_var.set(str(home / "ai-models" / "model-worldbuilding.gguf"))
            self.explicit_model_var.set(str(home / "ai-models" / "model-explicit.gguf"))
            self.port_var.set("8081")
            self.context_var.set("8192")
            self.gpu_layers_var.set("99")
            self.temp_var.set(0.8)
            self.top_p_var.set(0.9)
            self.top_k_var.set("40")
            self.repeat_penalty_var.set(1.1)
            self.max_tokens_var.set("2048")
            self.output_folder_var.set("outputs/")

    def test_server(self):
        """Test if server can be started."""
        server_path = Path(self.server_path_var.get())
        if not server_path.exists():
            messagebox.showerror("Error", f"Server not found at:\n{server_path}\n\nPlease check the path.")
            return

        model_path = Path(self.worldbuilding_model_var.get())
        if not model_path.exists():
            messagebox.showerror("Error", f"Model not found at:\n{model_path}\n\nPlease check the path.")
            return

        messagebox.showinfo("Test", "Paths look good!\n\nNote: Full server test requires actually loading the model, which takes time.\n\nTry generating content to test the full setup.")

    def setup_help_tab(self):
        """Setup help tab."""
        help_text = scrolledtext.ScrolledText(self.tab_help, wrap=tk.WORD, font=("Arial", 10))
        help_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        guide = """NARRAIDER QUICK GUIDE

*** WHAT IS THIS?
NarrAider is an AI writing assistant that runs on YOUR computer.
No internet required. Completely private. Free forever.

*** HOW TO USE:
1. Select what you want to create (character, magic system, scene, etc.)
2. Describe it in the prompt box
3. Click Generate
4. Wait 30-120 seconds
5. Done! Your content is ready and auto-saved

*** TIPS FOR GREAT RESULTS:

For Characters:
- Include age, species, personality, background
- Example: "Female elf ranger, 150 years old, haunted by past failure, expert tracker"

For Magic Systems:
- Define power source, limitations, societal impact
- Example: "Blood magic where users sacrifice vitality for power, creates aging"

For Scenes:
- Set location, characters involved, emotional tone
- Example: "Tense dialogue in rain-soaked alley, former allies now enemies"

*** MODELS:
- Creative Writing: For characters, worldbuilding, general scenes
- Explicit/Adult: For mature content and adult scenes

*** INTEGRATION:
- Generate story concept files for writing projects
- Export character data for visualnovel.pics
- Create image prompts for Stable Diffusion/Midjourney

*** OUTPUT:
All generated content is auto-saved to:
NarrAider/outputs/[content_type]/

*** KEYBOARD SHORTCUTS:
Ctrl+G: Generate
Ctrl+S: Save
Ctrl+C: Copy
Ctrl+Q: Quit

*** NEED HELP?
See QUICKSTART.md for detailed tutorial
See README.md for complete documentation
See INTEGRATION_GUIDE.md for advanced features

*** HAVE FUN CREATING!

---
"Like the Gundam Heavy Arms, NarrAider brings maximum creative firepower.
Just keep your targeting systems locked on your story goals!" - Trowa Barton (probably)
"""

        help_text.insert("1.0", guide)
        help_text.config(state=tk.DISABLED)

    def on_type_changed(self, event=None):
        """Update description when content type changes."""
        selected = self.content_type.get()
        content_type = self.type_map.get(selected)

        descriptions = {
            "character": "Creates detailed character profiles with personality, background, skills, and appearance variations. Perfect for D&D, novels, or games. ~800-1200 words.",
            "magic": "Designs complete magic systems with rules, limitations, progression, and societal impact. ~1000-1500 words.",
            "science": "Creates sci-fi technology systems (FTL, weapons, etc.) with pseudo-scientific foundations. ~1000-1500 words.",
            "artifact": "Generates legendary items with history, powers, and drawbacks. ~600-800 words.",
            "culture": "Develops complete species/faction backgrounds with society, beliefs, and traditions. ~1200-1500 words.",
            "relationships": "Maps character dynamics, conflicts, and relationship webs. ~800-1000 words.",
            "concept": "Creates complete story concept files for writing projects. ~2000-3000 words.",
            "scene-dialogue": "Writes character-driven dialogue scenes with subtext and emotion. ~500-800 words.",
            "scene-combat": "Creates exciting action/combat sequences with clear choreography. ~600-1000 words.",
            "scene-general": "Generates narrative scenes with setting, character development, and atmosphere. ~500-1000 words.",
            "scene-explicit": "Writes adult/sexual scenes with emotional connection and sensual detail. ~800-1200 words.",
            "image-prompt": "Creates detailed prompts for AI image generation (Stable Diffusion, Midjourney, etc.). ~200-300 words."
        }

        desc = descriptions.get(content_type, "Select a content type to see description.")

        self.type_description.config(state=tk.NORMAL)
        self.type_description.delete("1.0", tk.END)
        self.type_description.insert("1.0", desc)
        self.type_description.config(state=tk.DISABLED)

    def show_example(self):
        """Show example prompt for current content type."""
        selected = self.content_type.get()
        content_type = self.type_map.get(selected, "character")

        examples = {
            "character": "Female dwarf engineer, 45, gruff exterior but caring heart, lost her forge in a fire, seeking redemption, expert in runic machinery",
            "magic": "Blood magic where mages sacrifice vitality for power, creates permanent aging, society fears and persecutes practitioners",
            "science": "FTL using quantum entanglement gates, requires massive infrastructure, only governments can afford it",
            "artifact": "Ancient sword granting perfect combat skill but slowly erasing wielder's personality",
            "culture": "Nomadic desert people who harvest water from dew using crystal technology, matriarchal society",
            "relationships": "Five person adventuring party with mentor/student betrayal, rival siblings, outsider mediator",
            "concept": "Cozy coffee shop romance in small town during autumn, barista falls for mysterious writer",
            "scene-dialogue": "Former lovers meet at friend's wedding, unresolved feelings, rain outside",
            "scene-combat": "Sword duel on burning ship, protagonist outmatched but protecting escaped prisoners",
            "scene-general": "Character discovers mentor's secret laboratory filled with forbidden experiments",
            "scene-explicit": "Two space pirates sharing vulnerability after near-death, intimacy in cramped quarters",
            "image-prompt": "Cyberpunk hacker, neon mohawk, leather jacket with tech patches, holographic screens"
        }

        example = examples.get(content_type, "Describe what you want...")

        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", example)

    def optimize_prompt(self):
        """Optimize the user's prompt with more detail based on content type and model."""
        # Get current prompt
        current_prompt = self.prompt_text.get("1.0", tk.END).strip()

        if not current_prompt:
            messagebox.showwarning("Empty Prompt", "Please enter a prompt first before optimizing.")
            return

        # Get content type
        selected = self.content_type.get()
        content_type = self.type_map.get(selected, "character")

        # Get model type
        model_display = self.model_type.get()
        is_explicit = "Explicit" in model_display

        # Build optimization guidelines based on content type
        guidelines = {
            "character": "Include: age, species/race, physical traits, personality, background/history, skills, motivations, flaws",
            "magic": "Include: power source, mechanics/rules, limitations, cost to user, societal impact, visual effects",
            "science": "Include: scientific principle, practical applications, limitations, infrastructure needs, who has access",
            "artifact": "Include: physical description, powers/abilities, drawbacks/costs, history/origin, current status",
            "culture": "Include: population, location, governance, values/beliefs, technology level, notable customs",
            "relationships": "Include: number of people, their roles, conflict points, emotional dynamics, history together",
            "concept": "Include: genre, setting, main conflict, tone/mood, key themes, target audience feel",
            "scene-dialogue": "Include: location, participants, emotional state, what's at stake, subtext",
            "scene-combat": "Include: location, combatants, fighting styles, what's at stake, environmental factors",
            "scene-general": "Include: location, time of day, atmosphere, characters present, sensory details, what happens",
            "scene-explicit": "Include: participants, emotional context, location/atmosphere, relationship dynamic, consent/desire",
            "image-prompt": "Include: subject, clothing/gear, pose/expression, environment, lighting, art style, mood"
        }

        guideline = guidelines.get(content_type, "Add more specific details")

        # Show optimization dialog
        optimize_window = tk.Toplevel(self.root)
        optimize_window.title("Prompt Optimizer")
        optimize_window.geometry("700x500")

        ttk.Label(
            optimize_window,
            text="✨ Prompt Optimizer",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        ttk.Label(
            optimize_window,
            text=f"Content Type: {selected}",
            font=("Arial", 10)
        ).pack(pady=5)

        ttk.Label(
            optimize_window,
            text=f"Optimization Tips: {guideline}",
            wraplength=650,
            font=("Arial", 9),
            foreground="#666"
        ).pack(pady=5)

        # Original prompt
        ttk.Label(optimize_window, text="Your Original Prompt:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 2))
        original_text = tk.Text(optimize_window, height=4, wrap=tk.WORD, bg="#f0f0f0")
        original_text.pack(fill=tk.X, padx=20, pady=5)
        original_text.insert("1.0", current_prompt)
        original_text.config(state=tk.DISABLED)

        # Optimized prompt
        ttk.Label(optimize_window, text="Suggested Optimized Prompt:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(10, 2))
        optimized_text = tk.Text(optimize_window, height=8, wrap=tk.WORD)
        optimized_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Generate optimized version
        optimized = self.generate_optimized_prompt(current_prompt, content_type, guideline)
        optimized_text.insert("1.0", optimized)

        # Buttons
        btn_frame = ttk.Frame(optimize_window)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        def apply_optimization():
            new_prompt = optimized_text.get("1.0", tk.END).strip()
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", new_prompt)
            optimize_window.destroy()
            self.status_bar.config(text="[OK] Prompt optimized!")

        ttk.Button(
            btn_frame,
            text="✓ Use This Prompt",
            command=apply_optimization,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Keep Original",
            command=optimize_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def generate_optimized_prompt(self, original, content_type, guideline):
        """Generate an optimized version of the prompt."""
        # This is a simple expansion based on keywords
        # In the future, this could use an LLM to actually optimize

        words = original.lower().split()

        # Content-specific expansions
        if content_type == "character":
            additions = []
            if not any(word in words for word in ["years", "old", "age"]):
                additions.append("age not specified (suggest adding age)")
            if not any(word in words for word in ["personality", "trait", "character"]):
                additions.append("personality traits needed (e.g., 'brave but reckless')")
            if not any(word in words for word in ["background", "history", "past"]):
                additions.append("backstory missing (e.g., 'raised by monks, seeking lost sibling')")

            if additions:
                return f"{original}\n\nSuggested additions:\n- " + "\n- ".join(additions)

        elif content_type in ["scene-dialogue", "scene-combat", "scene-general", "scene-explicit"]:
            additions = []
            if not any(word in words for word in ["in", "at", "inside", "outside"]):
                additions.append("location/setting (e.g., 'in a rain-soaked alley')")
            if not any(word in words for word in ["tense", "happy", "sad", "angry", "emotional"]):
                additions.append("emotional tone (e.g., 'tension builds', 'bittersweet moment')")

            if additions:
                return f"{original}\n\nSuggested additions:\n- " + "\n- ".join(additions)

        # Default: just add guideline hints
        return f"{original}\n\nConsider adding more details:\n{guideline}"

    def refresh_system_prompts_dropdown(self):
        """Refresh the system prompts dropdown with current prompts."""
        self.system_combo['values'] = list(narraider.SYSTEM_PROMPTS.keys())

    def view_system_prompts(self):
        """Show system prompts viewer/editor dialog."""
        # Refresh main dropdown first in case prompts were loaded from config
        self.refresh_system_prompts_dropdown()

        dialog = tk.Toplevel(self.root)
        dialog.title("System Prompts - View/Edit/Create")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        set_window_icon(dialog)

        # Instructions
        ttk.Label(
            dialog,
            text="System prompts guide the AI's tone and style. Built-in prompts are read-only. You can create custom prompts!",
            wraplength=750
        ).pack(padx=10, pady=10)

        # Prompt selector and buttons frame
        selector_frame = ttk.Frame(dialog)
        selector_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(selector_frame, text="Select Prompt:").pack(side=tk.LEFT, padx=(0, 10))

        current_prompt = tk.StringVar(value=self.system_prompt.get())
        prompt_combo = ttk.Combobox(
            selector_frame,
            textvariable=current_prompt,
            values=list(narraider.SYSTEM_PROMPTS.keys()),
            state="readonly",
            width=25
        )
        prompt_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Buttons frame
        buttons_frame = ttk.Frame(selector_frame)
        buttons_frame.pack(side=tk.LEFT)

        def create_new_prompt():
            """Create a new custom system prompt."""
            # Name dialog
            name_dialog = tk.Toplevel(dialog)
            name_dialog.title("New Custom Prompt")
            name_dialog.geometry("400x150")
            name_dialog.transient(dialog)
            name_dialog.grab_set()

            ttk.Label(name_dialog, text="Enter a name for your custom system prompt:").pack(padx=10, pady=10)

            name_var = tk.StringVar()
            name_entry = ttk.Entry(name_dialog, textvariable=name_var, width=40)
            name_entry.pack(padx=10, pady=(0, 10))
            name_entry.focus()

            def save_new():
                name = name_var.get().strip()
                if not name:
                    messagebox.showwarning("Invalid Name", "Please enter a name.")
                    return

                # Check if name already exists
                if name in narraider.SYSTEM_PROMPTS:
                    messagebox.showwarning("Name Exists", f"A prompt named '{name}' already exists. Choose a different name.")
                    return

                # Save with empty content initially
                save_custom_system_prompt(name, "")
                # Refresh combo boxes (dialog and main window)
                prompt_combo['values'] = list(narraider.SYSTEM_PROMPTS.keys())
                self.refresh_system_prompts_dropdown()
                current_prompt.set(name)
                name_dialog.destroy()
                messagebox.showinfo("Success", f"Custom prompt '{name}' created! Edit it below and click 'Save Changes'.")

            button_frame = ttk.Frame(name_dialog)
            button_frame.pack(pady=10)
            ttk.Button(button_frame, text="Create", command=save_new).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=name_dialog.destroy).pack(side=tk.LEFT, padx=5)

        def delete_prompt():
            """Delete the currently selected custom prompt."""
            selected = current_prompt.get()
            if not selected:
                return

            if not is_custom_system_prompt(selected):
                messagebox.showwarning("Cannot Delete", "Built-in prompts cannot be deleted. Only custom prompts can be removed.")
                return

            if messagebox.askyesno("Confirm Delete", f"Delete custom prompt '{selected}'?"):
                delete_custom_system_prompt(selected)
                # Refresh combo boxes (dialog and main window)
                prompt_combo['values'] = list(narraider.SYSTEM_PROMPTS.keys())
                self.refresh_system_prompts_dropdown()
                current_prompt.set("Default")
                messagebox.showinfo("Deleted", f"Custom prompt '{selected}' deleted.")

        ttk.Button(buttons_frame, text="Create New", command=create_new_prompt, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Delete", command=delete_prompt, width=10).pack(side=tk.LEFT, padx=2)

        # Text display
        text_frame = ttk.LabelFrame(dialog, text="Prompt Content (Editable for Custom Prompts)", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True)

        def update_display(*args):
            """Update the text display when selection changes."""
            selected = current_prompt.get()
            content = narraider.SYSTEM_PROMPTS.get(selected, "")
            text_widget.config(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            if content:
                text_widget.insert("1.0", content)
            else:
                text_widget.insert("1.0", "(No system prompt - model uses default behavior)")

            # Make read-only for built-in prompts, editable for custom
            if is_custom_system_prompt(selected):
                text_widget.config(state=tk.NORMAL, background="white")
            else:
                text_widget.config(state=tk.DISABLED, background="#f0f0f0")

        def save_changes():
            """Save changes to custom prompt."""
            selected = current_prompt.get()
            if not is_custom_system_prompt(selected):
                messagebox.showinfo("Read-Only", "Built-in prompts cannot be edited. Create a new custom prompt instead.")
                return

            content = text_widget.get("1.0", tk.END).strip()
            save_custom_system_prompt(selected, content)
            messagebox.showinfo("Saved", f"Custom prompt '{selected}' saved!")

        # Initial display
        update_display()
        current_prompt.trace_add("write", update_display)

        # Info text
        info_text = """Built-in Prompts: Default, Detailed, Concise, Creative, Explicit
Custom prompts appear below built-in ones. Edit them and click 'Save Changes' to update."""

        ttk.Label(dialog, text=info_text, justify=tk.LEFT, foreground="#666").pack(padx=10, pady=(0, 10))

        # Bottom buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=(0, 10))
        ttk.Button(button_frame, text="Save Changes", command=save_changes, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def generate(self):
        """Start generation."""
        if self.generating:
            messagebox.showwarning("Busy", "Generation in progress. Please wait.")
            return

        # Get inputs
        selected = self.content_type.get()
        content_type = self.type_map.get(selected)

        if not content_type:
            messagebox.showerror("Error", "Please select a content type.")
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt.")
            return

        model_display = self.model_type.get()
        model = "explicit" if "Explicit" in model_display else "worldbuilding"

        output_format = self.output_format.get()
        system_prompt = self.system_prompt.get()

        # Update UI
        self.generating = True
        self.generate_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="Generating...")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        self.progress.start()

        # Clear output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", "[...] Generating, please wait...\n\nThis may take 30-120 seconds.\n\nModel is processing your request...")
        self.output_text.config(state=tk.DISABLED)

        # Start thread
        thread = threading.Thread(
            target=self.generate_thread,
            args=(content_type, prompt, model, output_format, system_prompt)
        )
        thread.daemon = True
        thread.start()

    def generate_thread(self, content_type, prompt, model, output_format, system_prompt):
        """Background generation thread."""
        try:
            result = generate_content(content_type, prompt, model, output_format, system_prompt)
            self.gen_queue.put(("success", result, content_type, output_format))
        except Exception as e:
            self.gen_queue.put(("error", str(e), None, None))

    def check_queue(self):
        """Check generation queue."""
        try:
            while True:
                status, result, content_type, output_format = self.gen_queue.get_nowait()

                if status == "success":
                    # Update output
                    try:
                        self.output_text.config(state=tk.NORMAL)
                        self.output_text.delete("1.0", tk.END)
                        if result:  # Only insert if result is not None/empty
                            self.output_text.insert(tk.END, str(result))
                        self.output_text.config(state=tk.DISABLED)
                    except Exception as e:
                        print(f"Error updating output text: {e}")
                        # Fallback: just set it normally
                        self.output_text.config(state=tk.NORMAL)
                        self.output_text.delete("1.0", tk.END)
                        self.output_text.insert(tk.END, str(result) if result else "Error: No output generated")
                        self.output_text.config(state=tk.DISABLED)

                    self.status_bar.config(text="[OK] Generation complete!")

                    # Auto-save
                    saved_path = save_output(result, content_type, output_format)
                    messagebox.showinfo("Success", f"Generated and saved to:\n{saved_path}")

                elif status == "error":
                    try:
                        self.output_text.config(state=tk.NORMAL)
                        self.output_text.delete("1.0", tk.END)
                        self.output_text.insert(tk.END, f"[ERROR]\n\n{result}")
                        self.output_text.config(state=tk.DISABLED)
                    except Exception as e:
                        print(f"Error updating error text: {e}")

                    self.status_bar.config(text="[ERROR] Generation failed")
                    messagebox.showerror("Error", f"Generation failed:\n{result}")

                # Reset UI
                self.generating = False
                self.generate_btn.config(state=tk.NORMAL)
                self.progress.stop()
                self.progress.pack_forget()

        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def save_file(self):
        """Save output to file."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content or "Generating" in content:
            messagebox.showwarning("No Content", "Nothing to save.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Saved to:\n{filename}")

    def copy_to_clipboard(self):
        """Copy to clipboard."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Nothing to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_bar.config(text="[OK] Copied to clipboard!")

    def clear_output(self):
        """Clear output."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_bar.config(text="Ready")


def main():
    """Main entry point."""
    root = tk.Tk()

    # Try to set theme
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass

    # Create app
    app = NarrAiderUnified(root)

    # Handle close
    def on_closing():
        if messagebox.askokcancel("Quit", "Quit NarrAider?"):
            kill_server()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Bind keyboard shortcuts
    root.bind('<Control-g>', lambda e: app.generate_btn.invoke())
    root.bind('<Control-s>', lambda e: app.save_file())
    root.bind('<Control-q>', lambda e: on_closing())

    root.mainloop()


if __name__ == "__main__":
    main()
