# NarrAider Quick Start Guide

**Created by Andreas "Uriel1339" Lopez**

## First Time Setup (5 minutes)

### 1. Download Models (Choose Your Tier)

**Choose based on your GPU VRAM:**

---

#### [TIER 1] **Tier 1: RTX 4090 / RTX 3090 (24GB VRAM)**
*Best quality for worldbuilding and scene generation*

**Creative Writing Model: Gemma-3-27B-IT**
1. Visit: https://huggingface.co/bartowski/google_gemma-3-27b-it-GGUF
2. Download: `google_gemma-3-27b-it-Q4_K_M.gguf` (~17GB)
3. Save to your models folder (e.g., `~/ai-models/` on macOS/Linux or `%USERPROFILE%\ai-models\` on Windows)

**Explicit Content Model: Amoral-Gemma3-27B**
1. Visit: https://huggingface.co/mradermacher/amoral-gemma3-27B-v2-i1-GGUF
2. Download: `amoral-gemma3-27B-v2-i1-Q4_K_M.gguf` (~17GB)
3. Save to your models folder

---

#### [TIER 2] **Tier 2: RTX 3080 / RTX 4070 (10-12GB VRAM)**
*Optimized for mid-range cards - Excellent quality/performance balance*

**Creative Writing Model: MythoMax L2 13B** (Recommended)
1. Visit: https://huggingface.co/TheBloke/MythoMax-L2-13B-GGUF
2. Download: `mythomax-l2-13b.Q4_K_M.gguf` (~7.9GB)
3. Save to your models folder

**Alternative: Chronos Hermes 13B** (Strong narrative skills)
1. Visit: https://huggingface.co/TheBloke/Chronos-Hermes-13b-v2-GGUF
2. Download: `chronos-hermes-13b-v2.Q4_K_M.gguf` (~7.9GB)
3. Save to your models folder

**Explicit Content Model: Stheno v3.2 8B**
1. Visit: https://huggingface.co/bartowski/L3-8B-Stheno-v3.2-GGUF
2. Download: `L3-8B-Stheno-v3.2-Q4_K_M.gguf` (~4.9GB)
3. Save to your models folder

**Budget Option: Mistral 7B** (More headroom, still high quality)
1. Visit: https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF
2. Download: `Mistral-7B-Instruct-v0.3-Q6_K.gguf` (~5.9GB)

---

**Not sure which tier?**
- Check your GPU: NVIDIA Control Panel → System Information → Components
- RTX 4090/3090/4080: Use Tier 1 (24GB)
- RTX 3080/4070/3060 12GB: Use Tier 2 (10-12GB)
- Lower VRAM? Use Mistral 7B Q4_K_M (~4.4GB)

### 2. Download llama.cpp Server

**Windows:**
1. Go to: https://github.com/ggerganov/llama.cpp/releases
2. Download the latest:
   - NVIDIA: `llama-b[XXXX]-bin-win-cuda-cu12.2.0-x64.zip`
   - AMD/Intel: `llama-b[XXXX]-bin-win-vulkan-x64.zip`
3. Extract to a folder of your choice (e.g., `%USERPROFILE%\llama-server\`)
4. Remember the path to `llama-server.exe` for configuration

### 3. Verify Configuration

The Setup Wizard will help you configure paths, or you can manually edit `narraider_config.json`:

```json
{
  "llama_server_path": "/path/to/your/llama-server/llama-server.exe",
  "models": {
    "worldbuilding": "/path/to/your/ai-models/your-model.gguf"
  }
}
```

Example paths:
- Windows: `C:/Users/YourName/llama-server/llama-server.exe`
- macOS/Linux: `/Users/YourName/llama-server/llama-server` or `~/llama-server/llama-server`

### 4. Launch NarrAider

**GUI Mode (Easiest):**
```bash
python3 narraider_gui.py
```

**Command Line:**
```bash
python3 narraider.py --type character --prompt "Describe your character"
```

## Common Workflows

### Create a Character

**GUI:**
1. Launch `narraider_gui.py`
2. Select "Character Profile" from dropdown
3. Enter prompt: `Female elf ranger, 150 years old, haunted by past failure, expert tracker`
4. Click "Generate"
5. Wait 30-60 seconds
6. Character saved to `outputs/characters/`

**CLI:**
```bash
python3 narraider.py --type character --prompt "Female elf ranger, 150 years old, haunted by past failure, expert tracker"
```

### Design a Magic System

**GUI:**
1. Select "Magic System"
2. Enter: `Elemental magic where users bond with elemental spirits, permanent connection, spirits have personalities`
3. Generate
4. Saved to `outputs/magic_systems/`

**CLI:**
```bash
python3 narraider.py --type magic --prompt "Elemental magic with spirit bonds"
```

### Write a Combat Scene

**GUI:**
1. Select "Scene: Combat/Action"
2. Enter: `Protagonist fights three bandits in cramped tavern, using environment as weapons, trying not to kill anyone`
3. Generate
4. Saved to `outputs/scenes/`

### Create a Story Concept

**GUI:**
1. Select "Story Concept"
2. Enter: `Space station mystery where crew members are being replaced by perfect duplicates, paranoia thriller, isolation horror`
3. Generate
4. Output saved to: `outputs/concepts/`

**CLI:**
```bash
python3 narraider.py --type concept --prompt "Space station duplicate mystery" --output outputs/concepts/doppelganger.txt
```

Use the concept file as a reference for your writing projects.

### Generate Character Art Prompts

**For use with Stable Diffusion, Midjourney, Nano Banana Pro, etc.:**

**GUI:**
1. Select "Image Prompt"
2. Enter character description
3. Generate
4. Copy the MAIN PROMPT section
5. Paste into your image generation tool (Stable Diffusion, Midjourney, Nano Banana Pro/Gemini)

**Nano Banana Pro Tip**: Upload reference images (style, costume, pose) for best results. See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for detailed workflows.


## Output Organization

All outputs are automatically saved:

```
NarrAider/outputs/
├── characters/          # Character profiles
├── magic_systems/       # Magic systems
├── science_systems/     # Tech/science systems
├── artifacts/          # Special items
├── cultures/           # Species/faction backgrounds
├── relationships/      # Character relationship webs
├── concepts/           # Story concept files
├── scenes/             # All scene types
└── image_prompts/      # Character art prompts
```

## Tips for Great Results

### Character Prompts
[OK] Good: `Male orc blacksmith, 35, gentle giant personality, lost family in war, now dedicated pacifist, master craftsman`
[X] Vague: `An orc character`

### Magic System Prompts
[OK] Good: `Necromancy powered by grief, requires personal loss to access, stronger magic = more painful memories, society stigmatizes users`
[X] Vague: `A magic system about death`

### Scene Prompts
[OK] Good: `Two rivals forced to work together during zombie apocalypse, trapped in abandoned mall, tension and grudging respect`
[X] Vague: `Action scene with zombies`

## Keyboard Shortcuts (GUI)

- **Ctrl+G** - Generate (when ready)
- **Ctrl+S** - Save to file
- **Ctrl+C** - Copy to clipboard (when output selected)
- **Ctrl+Q** - Quit

## Troubleshooting

**"Server failed to start"**
- Check `narraider_config.json` paths are correct
- Ensure model file exists
- Try running `llama-server.exe` manually to see errors

**"Generation failed"**
- Check server is running (new console window should appear)
- Verify model is compatible (must be .gguf format)
- Try reducing context_size in config (4096 instead of 8192)

**"Out of memory"**
- Use smaller quantization (Q4_K_M instead of Q6_K)
- Reduce gpu_layers in config
- Try smaller model (7B instead of 9B)

**Output is low quality**
- Be more specific in prompts
- Try different model
- Adjust temperature in config (higher = more creative)

## Next Steps

1. [OK] Generate your first character
2. [OK] Design a magic or tech system
3. [OK] Write a practice scene
4. [OK] Create a full story concept
5. [OK] Use for your writing projects
6. [OK] Build your world!

For full documentation, see `README.md`

Happy worldbuilding!
