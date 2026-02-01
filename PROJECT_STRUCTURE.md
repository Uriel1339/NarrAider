# NarrAider Project Structure

**Created by Andreas "Uriel1339" Lopez**

## Complete File Organization

```
NarrAider/
│
├── narraider.py                 # Core generation engine (CLI)
├── narraider_gui.py             # Graphical user interface
├── narraider_config.json        # Configuration (paths, models, parameters)
├── example_workflows.py         # Example scripts for batch generation
├── launch_gui.bat               # Windows launcher
│
├── README.md                    # Full documentation
├── QUICKSTART.md                # 5-minute getting started guide
├── INTEGRATION_GUIDE.md         # Integration with image generation and other tools
├── LICENSE.md                   # MIT License
├── PROJECT_STRUCTURE.md         # This file
├── .gitignore                   # Git ignore rules
│
└── outputs/                     # All generated content (auto-created)
    ├── characters/              # Character profiles
    │   ├── elara_profile_20260131_143022.txt
    │   └── elara_image_20260131_143122.txt
    │
    ├── magic_systems/           # Magic system designs
    │   └── runecraft_system_20260131_144530.txt
    │
    ├── science_systems/         # Sci-fi tech systems
    │   └── ftl_gates_20260131_145012.txt
    │
    ├── artifacts/               # Special items
    │   └── ancient_sword_20260131_145633.txt
    │
    ├── cultures/                # Species/faction backgrounds
    │   └── elven_society_20260131_150241.txt
    │
    ├── relationships/           # Character relationship webs
    │   └── party_dynamics_20260131_151009.txt
    │
    ├── concepts/                # Story concept files
    │   └── space_station_mystery_20260131_152134.txt
    │
    ├── scenes/                  # All scene types
    │   ├── dialogue_tavern_20260131_153022.txt
    │   ├── combat_dragon_20260131_153544.txt
    │   ├── explicit_pirates_20260131_154101.txt
    │   └── general_discovery_20260131_154639.txt
    │
    └── image_prompts/           # Character art prompts
        └── cyberpunk_hacker_20260131_155212.txt
```

## Recommended Directory Structure

```
YourProjectFolder/
│
├── NarrAider/                   # This tool (worldbuilding aid)
│   └── (files listed above)
│
├── models/                      # GGUF model files (NOT in git)
│   ├── gemma-2-9b-it-Q6_K.gguf
│   └── Stheno-v3.2-8B-Q6_K.gguf
│
└── llama_server/                # llama.cpp server executable (NOT in git)
    └── llama-server.exe
```

## File Descriptions

### Core Scripts

**narraider.py**
- Main CLI engine
- Contains all prompt templates
- Handles model loading, generation, file saving
- ~600 lines
- Key functions:
  - `generate_content()` - Main generation function
  - `ensure_model_loaded()` - Model management
  - `save_output()` - File saving with organization
  - `TEMPLATES` - Dictionary of all prompt templates

**narraider_gui.py**
- Tkinter-based GUI
- Threading for non-blocking generation
- Queue-based status updates
- ~400 lines
- Features:
  - Dropdown content type selection
  - Large prompt text area
  - Real-time output display
  - Auto-save to outputs/

**example_workflows.py**
- Demonstrates programmatic usage
- Three example workflows:
  - `workflow_complete_character()` - Full character package
  - `workflow_worldbuilding_package()` - World lore bundle
  - `workflow_scene_sequence()` - Connected scenes
- Use as templates for your own scripts

### Configuration

**narraider_config.json**
```json
{
  "llama_server_path": "Path to llama-server.exe",
  "models": {
    "worldbuilding": "Path to general model",
    "explicit": "Path to uncensored model"
  },
  "server_port": 8081,
  "context_size": 8192,
  "gpu_layers": 99,
  "output_folder": "outputs/",
  "generation_params": {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "max_tokens": 2048
  }
}
```

**Key Settings:**
- `llama_server_path`: Location of llama.cpp server
- `models.worldbuilding`: General purpose model (Gemma, Mistral, etc.)
- `models.explicit`: Uncensored model for adult content (Stheno, Magnum, etc.)
- `server_port`: 8081 (default port)
- `context_size`: 8192 tokens (reduce if OOM errors)
- `gpu_layers`: 99 = full GPU offload (reduce for CPU usage)
- `temperature`: 0.8 (creativity level, 0.7-1.0 range)

### Documentation

**README.md** (Most comprehensive)
- Complete feature list
- Installation instructions with download links
- Usage examples (GUI and CLI)
- Output type descriptions
- Integration with image generation tools
- Troubleshooting guide
- Advanced configuration

**QUICKSTART.md** (Fastest path to first generation)
- 5-minute setup
- Download links
- First generation walkthrough
- Common workflows
- Tips for prompts

**INTEGRATION_GUIDE.md** (For advanced users)
- Programmatic usage examples
- Custom template creation
- API server mode
- Export formats (Markdown, Obsidian, World Anvil)

**PROJECT_STRUCTURE.md** (This file)
- File organization
- Purpose of each file
- Configuration details
- Workflow diagrams

## Output File Naming

All generated files follow this pattern:
```
{content_type}_{timestamp}.txt
```

Examples:
- `character_20260131_143022.txt`
- `magic_20260131_144530.txt`
- `scene-dialogue_20260131_153022.txt`

**Special cases:**
- Characters with image prompts: Also creates `_image_{timestamp}.txt`

## Workflow Diagram

```
User Input (GUI or CLI)
    ↓
narraider.py
    ↓
Load Config → Check Model → Start llama.cpp Server
    ↓
Build Prompt (Template + User Input)
    ↓
Send to Model → Generate (30-120s)
    ↓
Save to outputs/{category}/
    ↓
Return Result to User
    ↓
Kill Server (cleanup)
```

## Integration Points

### With Image Generation Tools

```
NarrAider                        Image Generation Tools
-----------                      ----------------------
Generate character       →       Use character description
Generate image prompt    →       Stable Diffusion/Midjourney/Nano Banana Pro
                                     ↓
                                 Generate character art
```

## Development Workflow

### Adding New Content Types

1. Add template to `TEMPLATES` dict in `narraider.py`:
```python
TEMPLATES = {
    # ... existing templates ...

    "new_type": """Your prompt template here.

    Use {user_prompt} to inject user input.

    Instructions for the model..."""
}
```

2. Add to GUI dropdown in `narraider_gui.py`:
```python
type_choices = [
    # ... existing types ...
    ("Display Name", "new_type")
]
```

3. Test:
```bash
python narraider.py --type new_type --prompt "Test prompt"
```

### Customizing Output

Edit `save_output()` in `narraider.py` to change:
- Subfolder organization
- File naming patterns
- Output formatting

### Adjusting Generation

Edit `generation_params` in config:
- `temperature`: Higher = more creative (0.7-1.0)
- `top_p`: Nucleus sampling (0.9 recommended)
- `top_k`: Top-k sampling (40 recommended)
- `repeat_penalty`: Prevent repetition (1.1 recommended)
- `max_tokens`: Output length limit

## Port Usage

- **8081**: NarrAider (this tool)
- **5000**: NarrAider API mode (optional, see INTEGRATION_GUIDE.md)

## Typical Usage Patterns

### Solo Worldbuilding Session
1. Launch GUI: `python narraider_gui.py`
2. Generate magic system
3. Generate 2-3 cultures
4. Generate 5-10 characters
5. Generate key artifacts
6. Save everything to `outputs/`
7. Review and refine

### Preparing Story Concepts
1. Generate worldbuilding pieces (characters, systems, etc.)
2. Review all outputs
3. Generate story concept incorporating your lore
4. Save to `outputs/concepts/`
5. Use for your writing projects

### Scene Prototyping
1. Generate 3-5 sample scenes
2. Check tone and style
3. Adjust temperature/model if needed
4. Regenerate until satisfied
5. Use best scenes as reference for full book

## Maintenance

### Updating Models
1. Download new .gguf file
2. Place in `models/` folder
3. Update path in `narraider_config.json`
4. Test: `python narraider.py --type character --prompt "Test"`

### Clearing Outputs
```bash
# Windows
rmdir /s outputs

# Linux/Mac
rm -rf outputs/
```
Folder will auto-recreate on next generation.

### Backing Up Work
```bash
# Backup all outputs
tar -czf narraider_backup_$(date +%Y%m%d).tar.gz outputs/

# Backup config
cp narraider_config.json narraider_config_backup.json
```

## Performance Notes

### Generation Speed
- Character: 30-60 seconds
- Magic System: 60-90 seconds
- Scene: 30-60 seconds
- Concept: 90-120 seconds

### Memory Usage
- Gemma 2 9B Q6_K: ~7GB VRAM
- Stheno 8B Q6_K: ~6GB VRAM
- Context: ~1-2GB additional

### Optimization
- Use Q4 quantization for 2x speed, slight quality loss
- Reduce `gpu_layers` to offload to CPU
- Reduce `context_size` to 4096 for faster generation

---

For questions or issues, see README.md troubleshooting section.
