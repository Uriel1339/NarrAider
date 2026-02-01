# NarrAider Integration Guide

**Created by Andreas "Uriel1339" Lopez**

## Using NarrAider for Worldbuilding

NarrAider generates focused, reference-quality content for writers and worldbuilders:

### Planning Your World

Use NarrAider to flesh out your setting before writing:

```bash
# Generate magic system
python narraider.py --type magic --prompt "Your magic concept"

# Generate protagonist
python narraider.py --type character --prompt "Your protagonist idea"

# Generate supporting cast
python narraider.py --type character --prompt "Supporting character 1"
python narraider.py --type character --prompt "Supporting character 2"

# Generate cultural background
python narraider.py --type culture --prompt "Your primary culture/species"

# Generate key artifact
python narraider.py --type artifact --prompt "MacGuffin or important item"
```

Review all these outputs and refine your ideas.

### Generate Story Concepts

Use NarrAider to create comprehensive story outlines:

```bash
python narraider.py --type concept --prompt "Detailed story premise incorporating your worldbuilding" --output outputs/concepts/story_concept.txt
```

Use the generated concept as a reference for your writing projects.

### Fill Gaps During Writing

As you write, generate additional content as needed:

```bash
# Generate a specific scene that needs expansion
python narraider.py --type scene-dialogue --prompt "Conversation between X and Y about Z from chapter 7"

# Generate relationship dynamics
python narraider.py --type relationships --prompt "Character dynamics for X, Y, and Z"

# Generate image prompts for cover art
python narraider.py --type image-prompt --prompt "Your protagonist based on generated profile"
```

## Programmatic Usage

### Use NarrAider in Your Own Scripts

```python
from narraider import load_config, generate_content, save_output

# Initialize
load_config()

# Generate character
character = generate_content(
    content_type="character",
    user_prompt="Female dwarf engineer, 45, expert in runic tech",
    model_type="worldbuilding"
)

# Save
save_output(character, "character", "my_character.txt")

# Use the generated content
print(character)
```

### Batch Generation

```python
from narraider import load_config, generate_content, save_output

load_config()

# Generate multiple characters
party = [
    "Tank warrior, gruff but protective",
    "Healer mage, optimistic and naive",
    "Rogue thief, sarcastic and cynical",
    "Ranger scout, quiet and observant"
]

for i, prompt in enumerate(party, 1):
    char = generate_content("character", prompt, "worldbuilding")
    save_output(char, "character", f"party_member_{i}.txt")
```

### Custom Templates

Add your own templates to `narraider.py` in the `TEMPLATES` dictionary:

```python
TEMPLATES = {
    # ... existing templates ...

    "quest": """You are a game master creating a quest.

Design a complete quest based on:
{user_prompt}

Include:
- Quest Name
- Quest Giver
- Objective
- Challenges
- Rewards
- Optional side objectives

Quest Design:""",

    "location": """You are a worldbuilder describing a location.

Create a detailed location based on:
{user_prompt}

Include:
- Name and Type
- Geography and Climate
- Notable Features
- Inhabitants
- History
- Adventure Hooks

Location Profile:"""
}
```

Then use with:
```bash
python narraider.py --type quest --prompt "Save village from dragon"
python narraider.py --type location --prompt "Ancient wizard's tower"
```

## API Server Mode (Advanced)

Convert NarrAider to a web API for integration with other tools:

```python
# narraider_server.py
from flask import Flask, request, jsonify
from narraider import load_config, generate_content

app = Flask(__name__)
load_config()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    result = generate_content(
        data['type'],
        data['prompt'],
        data.get('model', 'worldbuilding')
    )
    return jsonify({"result": result})

if __name__ == '__main__':
    app.run(port=5000)
```

Then call from any language:
```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"type": "character", "prompt": "Elf ranger"}'
```

## Image Generation Integration

NarrAider's image prompt generator creates optimized prompts for AI image generation tools. Here's how to use them effectively with different platforms.

### Stable Diffusion (Local)

**Best for**: Full creative control, local generation, unlimited iterations

**Workflow**:
```bash
# Generate image prompt
python narraider.py --type image-prompt --prompt "Your character description"

# Copy output and paste into Stable Diffusion WebUI or ComfyUI
# Recommended settings:
# - Steps: 40-50
# - CFG Scale: 7-9
# - Sampler: DPM++ 2M Karras or Euler A
```

**Tips**:
- NarrAider prompts include style modifiers - remove or adjust as needed
- Add your preferred checkpoint/model to the prompt (e.g., "photorealistic, shot on Canon EOS")
- Use negative prompts: "blurry, low quality, amateur"

### Midjourney (Discord)

**Best for**: Artistic quality, fast iteration, community sharing

**Workflow**:
```bash
# Generate image prompt
python narraider.py --type image-prompt --prompt "Your character description"

# In Discord:
/imagine [paste NarrAider prompt] --v 6 --ar 2:3
```

**Tips**:
- NarrAider prompts work well with Midjourney v6 and v6.1
- Add `--style raw` for more literal interpretation
- Use `--chaos 20` for more variation
- Character sheets work best with `--ar 2:3` or `--ar 9:16`

### Nano Banana Pro (Gemini 3 Pro Image)

**Best for**: Text rendering, multi-image references, 4K quality, fast generation (<10 seconds)

**Platform**: Gemini app with 'Thinking' model

**Workflow**:
```bash
# Generate image prompt
python narraider.py --type image-prompt --prompt "Detailed character with specific outfit and pose"

# In Gemini app:
1. Select Gemini 3 Pro Image (Nano Banana Pro)
2. Paste NarrAider prompt
3. Optional: Upload reference images (up to 14) for style, color palette, or costume references
4. Submit
```

**Best Practices for Nano Banana Pro**:

**Leverage Text Rendering**:
- NarrAider prompts include character names - Nano Banana Pro can render text IN the image
- Add specific text requests: "with name 'Elara Moonwhisper' on a nameplate"
- Great for: book covers, character cards, posters with titles

**Use Multi-Image References**:
```
Prompt: [NarrAider generated prompt]

Reference Images:
1. Style guide (art style you want)
2. Color palette (mood board)
3. Costume reference (medieval armor example)
4. Pose reference (action pose)
```

**Optimize for 4K Output**:
- NarrAider prompts are detailed enough for 4K generation
- Request specific resolutions: "4K resolution, ultra detailed"
- Nano Banana Pro generates in seconds even at 4K

**Knowledge Integration**:
- Nano Banana Pro uses Gemini 3's knowledge base
- Reference real-world locations: "in the style of Petra, Jordan"
- Historical accuracy: "accurate 15th century Italian Renaissance clothing"

**Prompt Adjustments for Nano Banana Pro**:
```python
# Example: Enhance NarrAider prompt for Nano Banana Pro
base_prompt = generate_content("image-prompt", "Your character", "worldbuilding")

# Add Nano Banana-specific enhancements
enhanced = f"""{base_prompt}

[Technical specs for 4K]
- Native 4K resolution
- Professional studio lighting
- Photorealistic rendering

[Optional text overlay]
Include character name "Elara Moonwhisper" in elegant script at bottom right

[Style references]
Reference uploaded images for costume accuracy and color grading
"""
```

**Subscription Tiers**:
- Free tier: Limited generations per day
- Google AI Plus/Pro/Ultra: Higher quotas
- Enterprise: API access via Google Cloud

### Comparison Table

| Platform | Speed | Quality | Text Rendering | Local? | Best For |
|----------|-------|---------|---------------|--------|----------|
| Stable Diffusion | Slow (30s-2min) | High (with good model) | Poor | Yes | Full control, unlimited iterations |
| Midjourney | Fast (1-2min) | Very High | Moderate | No | Artistic quality, fast results |
| Nano Banana Pro | Very Fast (<10s) | Very High | Excellent | No | Text-heavy images, multi-reference, 4K |

### Batch Character Art Generation

```python
# Generate prompts for entire party
from narraider import generate_content, save_output

characters = [
    "Gruff dwarf warrior in heavy plate armor",
    "Elven mage with flowing robes and glowing staff",
    "Human rogue in dark leather with twin daggers"
]

prompts = []
for i, char in enumerate(characters, 1):
    prompt = generate_content("image-prompt", char, "worldbuilding")
    save_output(prompt, "image-prompt", f"party_member_{i}_prompt.txt")
    prompts.append(prompt)

print("Generated prompts for all characters!")
print("Use with your preferred image generation platform.")
```

### Platform-Specific Tips

**For Stable Diffusion**:
- Try different checkpoints (Realistic Vision, DreamShaper, etc.)
- Use LoRAs for specific styles or characters
- Inpainting for outfit variations

**For Midjourney**:
- Use `/describe` on reference images, then combine with NarrAider prompts
- Remix feature lets you iterate on generations
- Blend mode for combining concepts

**For Nano Banana Pro**:
- Upload logo/watermark as reference if generating for brand/IP
- Use for character cards that need text (name, stats, titles)
- Multilingual text rendering works (character names in different scripts)
- Best for generating sets of characters with consistent style (upload first character as style reference)

## Export Formats

### Export to Markdown

```python
from narraider import generate_content

character = generate_content("character", "Your prompt", "worldbuilding")

# Convert to markdown
markdown = f"""# Character Profile

{character}

---
*Generated with NarrAider {VERSION}*
"""

with open("character.md", "w") as f:
    f.write(markdown)
```

### Export to Obsidian Wiki

```python
# Create Obsidian-compatible notes
def create_obsidian_note(name, content, tags):
    frontmatter = f"""---
tags: {', '.join(tags)}
created: {datetime.now().isoformat()}
---

# {name}

{content}
"""
    return frontmatter

# Use it
character = generate_content("character", prompt, "worldbuilding")
note = create_obsidian_note("Elara Moonwhisper", character, ["character", "pc", "elf"])

with open("vault/Characters/Elara.md", "w") as f:
    f.write(note)
```

### Export to World Anvil Format

```python
def to_world_anvil(content, content_type):
    """Format for World Anvil BBCode."""
    sections = content.split('\n\n')
    formatted = []

    for section in sections:
        if section.startswith('**'):
            # Convert bold headers to World Anvil sections
            header = section.split('**')[1]
            formatted.append(f"[section:{header}]")
        else:
            formatted.append(section)

    return '\n\n'.join(formatted)
```

## Best Practices

### 1. Generate in Layers

**Bottom-Up Worldbuilding:**
1. Generate magic/tech systems (foundation)
2. Generate cultures (built on foundation)
3. Generate characters (inhabit cultures)
4. Generate conflicts (between characters)
5. Generate story concept (ties everything together)

### 2. Iterate and Refine

Don't expect perfection first try:
1. Generate initial version
2. Read and note what to change
3. Regenerate with refined prompt
4. Mix and match best parts from multiple generations

### 3. Use Scenes for Prototyping

Before starting your writing project:
1. Generate 2-3 sample scenes with NarrAider
2. Check if tone/style matches your vision
3. Adjust story concept if needed
4. Use as reference for your writing

### 4. Maintain Consistency

Create a "canon" folder:
```
MyWorld/
├── canon/
│   ├── magic_system.txt       # Official magic rules
│   ├── timeline.txt            # Historical events
│   ├── geography.txt           # World map notes
│   └── characters/             # Canonical character profiles
├── concepts/                   # Story concepts for writing projects
└── generated/                  # Experimental generations
```

Reference canon files when generating new content to maintain consistency.

## Troubleshooting Integration

**Q: How long should each generation take?**
A: Characters and scenes: 30-60 seconds. Systems and concepts: 1-2 minutes.

**Q: Can I use NarrAider output in my published works?**
A: Yes! All output is yours. Just check the license of the AI model you're using.

**Q: How detailed is the output?**
A: Characters: 800-1200 words. Systems: 1000-1500 words. Scenes: 500-1000 words.

**Q: Can I customize the templates?**
A: Yes! Edit the TEMPLATES dictionary in narraider.py to create custom content types.

---

Happy Creating! 🎨📚
