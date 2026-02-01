#!/usr/bin/env python3
"""
NarrAider GUI - Graphical interface for narrative content generation
Created by Andreas "Uriel1339" Lopez

MIT License - Free to use, modify, and distribute.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
from pathlib import Path
import json
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Import core functionality
from narraider import (
    load_config, ensure_model_loaded, generate_content,
    save_output, kill_server,
    TEMPLATES, VERSION
)

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

class NarrAiderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"NarrAider {VERSION} - Narrative Creation Assistant")
        self.root.geometry("1000x800")
        set_window_icon(self.root)

        # Generation queue for threading
        self.gen_queue = queue.Queue()
        self.generating = False

        # Load configuration
        load_config()

        self.setup_ui()

        # Start queue checker
        self.check_queue()

    def setup_ui(self):
        """Setup the user interface."""

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # ========== HEADER ==========
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(header_frame, text="NarrAider", font=("Arial", 24, "bold")).pack(side=tk.LEFT)
        ttk.Label(header_frame, text="AI-Powered Narrative Creation", font=("Arial", 12)).pack(side=tk.LEFT, padx=(10, 0))

        # ========== CONTROLS ==========
        controls_frame = ttk.LabelFrame(main_frame, text="Generation Settings", padding="10")
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Content type selection
        ttk.Label(controls_frame, text="Content Type:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.content_type = tk.StringVar(value="character")
        type_choices = [
            ("Character Profile", "character"),
            ("Magic System", "magic"),
            ("Science/Tech System", "science"),
            ("Artifact/Relic", "artifact"),
            ("Culture/Species", "culture"),
            ("Character Relationships", "relationships"),
            ("Story Concept", "concept"),
            ("--- Scenes ---", ""),
            ("Scene: Dialogue", "scene-dialogue"),
            ("Scene: Combat/Action", "scene-combat"),
            ("Scene: Explicit/Adult", "scene-explicit"),
            ("Scene: General", "scene-general"),
            ("--- Other ---", ""),
            ("Image Prompt", "image-prompt")
        ]

        type_combo = ttk.Combobox(controls_frame, textvariable=self.content_type, width=40, state="readonly")
        type_combo['values'] = [display for display, _ in type_choices]
        type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        # Map display names to actual values
        self.type_map = {display: value for display, value in type_choices if value}

        # Model selection
        ttk.Label(controls_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.model_type = tk.StringVar(value="worldbuilding")
        model_combo = ttk.Combobox(controls_frame, textvariable=self.model_type, width=40, state="readonly")
        model_combo['values'] = ["Worldbuilding (General)", "Explicit (Adult Scenes)"]
        model_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))

        controls_frame.columnconfigure(1, weight=1)

        # ========== PROMPT ==========
        prompt_frame = ttk.LabelFrame(main_frame, text="Prompt (describe what you want to generate)", padding="10")
        prompt_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        prompt_frame.columnconfigure(0, weight=1)

        self.prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Prompt scrollbar
        prompt_scroll = ttk.Scrollbar(prompt_frame, orient=tk.VERTICAL, command=self.prompt_text.yview)
        prompt_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.prompt_text['yscrollcommand'] = prompt_scroll.set

        # Example prompts button
        ttk.Button(prompt_frame, text="Example Prompts", command=self.show_examples).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # ========== OUTPUT ==========
        output_frame = ttk.LabelFrame(main_frame, text="Generated Output", padding="10")
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ========== ACTION BUTTONS ==========
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        self.generate_btn = ttk.Button(button_frame, text="Generate", command=self.generate, style="Accent.TButton")
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="Save to File", command=self.save_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = ttk.Label(button_frame, text="Ready", foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Progress bar (hidden by default)
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate', length=200)

    def show_examples(self):
        """Show example prompts for current content type."""
        selected_display = self.content_type.get()
        content_type_val = self.type_map.get(selected_display, "character")

        examples = {
            "character": "Female dwarf engineer, 45 years old, gruff exterior but soft heart, lost her forge in a fire, seeking redemption, expert in runic machinery",
            "magic": "Blood magic system where mages sacrifice vitality for power, creates permanent aging, society fears and persecutes practitioners",
            "science": "FTL using quantum entanglement gates, requires massive infrastructure, only governments can afford it, creates travel monopolies",
            "artifact": "Ancient sword that grants perfect combat skill but slowly erases the wielder's personality, forged by a forgotten civilization",
            "culture": "Nomadic desert people who harvest water from morning dew using crystal technology, matriarchal society, trade rare gems",
            "relationships": "Five characters: mentor/student pair with betrayal history, two rival siblings, and an outsider trying to mediate",
            "concept": "Cozy coffee shop romance in small town during autumn, barista falls for mysterious writer who visits daily",
            "scene-dialogue": "Tense conversation between former lovers who meet accidentally at their friend's wedding, unresolved feelings",
            "scene-combat": "Sword duel on a burning ship, protagonist outmatched but fights desperately to protect escaped prisoners",
            "scene-explicit": "Two space pirates sharing a moment of vulnerability after nearly dying, gradual intimacy in cramped quarters",
            "scene-general": "Character discovers their mentor's secret laboratory filled with forbidden experiments",
            "image-prompt": "Cyberpunk hacker with neon mohawk, leather jacket covered in tech patches, sitting in front of holographic screens"
        }

        example = examples.get(content_type_val, "Describe what you want to create...")

        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", example)

    def generate(self):
        """Start generation in background thread."""
        if self.generating:
            messagebox.showwarning("Busy", "Generation already in progress. Please wait.")
            return

        # Get inputs
        selected_display = self.content_type.get()
        content_type = self.type_map.get(selected_display)

        if not content_type:
            messagebox.showerror("Error", "Please select a valid content type.")
            return

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt describing what to generate.")
            return

        model_display = self.model_type.get()
        model = "explicit" if "Explicit" in model_display else "worldbuilding"

        # Update UI
        self.generating = True
        self.generate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Generating...", foreground="orange")
        self.progress.pack(side=tk.RIGHT, padx=(0, 10))
        self.progress.start()

        # Clear output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", "Generating, please wait...\n\nThis may take 30-120 seconds depending on model and complexity.")
        self.output_text.config(state=tk.DISABLED)

        # Start generation thread
        thread = threading.Thread(target=self.generate_thread, args=(content_type, prompt, model))
        thread.daemon = True
        thread.start()

    def generate_thread(self, content_type, prompt, model):
        """Background generation thread."""
        try:
            result = generate_content(content_type, prompt, model)
            self.gen_queue.put(("success", result, content_type))
        except Exception as e:
            self.gen_queue.put(("error", str(e), None))

    def check_queue(self):
        """Check generation queue for results."""
        try:
            while True:
                status, result, content_type = self.gen_queue.get_nowait()

                if status == "success":
                    # Update output
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.delete("1.0", tk.END)
                    self.output_text.insert("1.0", result)
                    self.output_text.config(state=tk.DISABLED)

                    self.status_label.config(text="Generation complete!", foreground="green")

                    # Auto-save
                    saved_path = save_output(result, content_type)
                    messagebox.showinfo("Success", f"Generated and saved to:\n{saved_path}")

                elif status == "error":
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.delete("1.0", tk.END)
                    self.output_text.insert("1.0", f"ERROR: {result}")
                    self.output_text.config(state=tk.DISABLED)

                    self.status_label.config(text="Generation failed", foreground="red")
                    messagebox.showerror("Error", f"Generation failed:\n{result}")

                # Reset UI
                self.generating = False
                self.generate_btn.config(state=tk.NORMAL)
                self.progress.stop()
                self.progress.pack_forget()

        except queue.Empty:
            pass

        # Check again in 100ms
        self.root.after(100, self.check_queue)

    def save_file(self):
        """Save output to user-selected file."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content or content == "Generating, please wait...":
            messagebox.showwarning("No Content", "Nothing to save. Generate content first.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Content saved to:\n{filename}")

    def clear_output(self):
        """Clear the output text area."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_label.config(text="Ready", foreground="green")

    def copy_to_clipboard(self):
        """Copy output to clipboard."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Nothing to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_label.config(text="Copied to clipboard!", foreground="blue")

def main():
    """Main GUI entry point."""
    root = tk.Tk()

    # Set theme if available
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # Theme not available, use default

    # Create GUI
    app = NarrAiderGUI(root)

    # Handle cleanup on close
    def on_closing():
        if messagebox.askokcancel("Quit", "Quit NarrAider? This will stop any running generation."):
            kill_server()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Run
    root.mainloop()

if __name__ == "__main__":
    main()
