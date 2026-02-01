#!/usr/bin/env python3
"""
NarrAider - AI-Powered Narrative Creation Assistant
Created by Andreas "Uriel1339" Lopez

Generates worldbuilding content, character profiles, lore, and scenes using local LLMs.
MIT License - Free to use, modify, and distribute.
"""

import requests
import subprocess
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Version
VERSION = "1.0.0"

# System Prompts
SYSTEM_PROMPTS = {
    "Default": "",  # No system prompt, model uses its default behavior

    "Detailed": """You are a creative writing assistant focused on rich, detailed descriptions.
Include vivid sensory details, specific measurements, and concrete examples.
Avoid vague language—be precise and evocative.""",

    "Concise": """You are a creative writing assistant focused on concise, punchy prose.
Use short sentences. Cut unnecessary words. Be direct and impactful.""",

    "Creative": """You are a highly creative writing assistant. Push boundaries with unique concepts, unexpected connections, and original ideas. Subvert tropes. Be inventive.""",

    "Explicit": """You are an adult fiction writing assistant specializing in explicit romantic and sexual content.

GUIDELINES:
- Write explicit sexual content with emotional depth and character connection
- Balance physical description with psychological/emotional elements
- Use varied, evocative language—avoid repetitive clinical terms
- Build tension and anticipation before explicit moments
- Show genuine chemistry, consent, and mutual desire between characters
- Include sensory details (touch, taste, sound, smell) not just visuals
- Vary pacing: slow buildup, intense peaks, tender afterglow
- Make intimate scenes advance character development or plot

STYLE:
- Use active, immediate language ("she gasps" not "she is gasping")
- Mix poetic and raw language authentically
- Show vulnerability, power dynamics, emotional honesty
- Avoid purple prose and euphemisms—be direct but literary

Your goal is to create immersive, emotionally resonant adult content that respects the characters and engages the reader.""",
}

# Default configuration (uses home directory for portability)
def get_default_config():
    """Get default configuration with platform-agnostic paths."""
    home = Path.home()
    return {
        "llama_server_path": str(home / "llama-server" / "llama-server.exe"),
        "models": {
            "worldbuilding": str(home / "ai-models" / "model-worldbuilding.gguf"),
            "explicit": str(home / "ai-models" / "model-explicit.gguf")
        },
        "server_port": 8081,
        "context_size": 8192,
        "gpu_layers": 99,
        "output_folder": "outputs",  # Relative to narraider directory
        "keep_server_loaded": False,  # If False, kills server after each generation to free VRAM
        "generation_params": {
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": 2048
        }
    }

# Backward compatibility
DEFAULT_CONFIG = get_default_config()

# Global state
SERVER_PROCESS = None
CURRENT_MODEL = None
CONFIG = None

def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_config():
    """Load configuration from file or create default."""
    global CONFIG
    config_path = Path(__file__).parent / "narraider_config.json"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        log("Configuration loaded")
    else:
        CONFIG = DEFAULT_CONFIG
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, indent=2)
        log("Default configuration created. Edit narraider_config.json to customize.")

    # Ensure output folder exists
    Path(CONFIG["output_folder"]).mkdir(parents=True, exist_ok=True)

def kill_server():
    """Kill the running llama.cpp server."""
    global SERVER_PROCESS, CURRENT_MODEL

    if SERVER_PROCESS:
        log("Killing llama server...")
        SERVER_PROCESS.terminate()
        try:
            SERVER_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROCESS.kill()
        SERVER_PROCESS = None
        CURRENT_MODEL = None
        time.sleep(2)
        log("Server killed")

def is_server_healthy():
    """Check if server is responding."""
    try:
        response = requests.get(
            f"http://127.0.0.1:{CONFIG['server_port']}/health",
            timeout=2
        )
        return response.status_code == 200
    except:
        return False

def start_server(model_path, model_name):
    """Start llama.cpp server with specified model."""
    global SERVER_PROCESS, CURRENT_MODEL

    kill_server()

    log(f"Starting {model_name}...")

    # Convert paths to Path objects and then to strings to handle Windows paths correctly
    server_path_obj = Path(CONFIG["llama_server_path"])
    model_path_obj = Path(model_path)

    # Verify paths exist
    if not server_path_obj.exists():
        log(f"ERROR: llama-server not found at: {server_path_obj}")
        return False

    if not model_path_obj.exists():
        log(f"ERROR: Model not found at: {model_path_obj}")
        return False

    server_path_str = str(server_path_obj)
    model_path_str = str(model_path_obj)

    # Debug: print the command being executed
    log(f"Server path: {server_path_str}")
    log(f"Model path: {model_path_str}")

    cmd = [
        server_path_str,
        "-m", model_path_str,
        "--host", "127.0.0.1",  # Bind to localhost only for security
        "--port", str(CONFIG["server_port"]),
        "--ctx-size", str(CONFIG["context_size"]),
        "-ngl", str(CONFIG["gpu_layers"]),
        "--log-disable"
    ]

    log(f"Command: {' '.join(cmd)}")

    try:
        # Set working directory to where llama-server.exe is located
        # This ensures it can find its DLL dependencies
        server_dir = server_path_obj.parent

        SERVER_PROCESS = subprocess.Popen(
            cmd,
            cwd=str(server_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        log(f"Server process started with PID: {SERVER_PROCESS.pid}")
    except Exception as e:
        log(f"ERROR: Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        return False

    log("Waiting for server to initialize (large models may take up to 2 minutes)...")
    time.sleep(15)

    # Poll for ready (increased timeout for large 27B models)
    for attempt in range(90):
        if is_server_healthy():
            log(f"{model_name} is ready!")
            CURRENT_MODEL = model_name
            return True
        time.sleep(1)

    log(f"ERROR: Server failed to start within timeout")

    # Try to capture server output for debugging
    if SERVER_PROCESS.poll() is not None:
        stdout, stderr = SERVER_PROCESS.communicate()
        if stdout:
            log(f"Server stdout: {stdout[:500]}")
        if stderr:
            log(f"Server stderr: {stderr[:500]}")
    else:
        log("Server process is still running but not responding to health checks")
        log("Check the server console window for error messages")

    kill_server()
    return False

def ensure_model_loaded(model_type):
    """Ensure correct model is loaded."""
    model_path = CONFIG["models"].get(model_type)
    if not model_path:
        log(f"ERROR: No model configured for type '{model_type}'")
        return False

    if CURRENT_MODEL == model_type and is_server_healthy():
        return True

    return start_server(model_path, model_type)

def generate_completion(prompt, max_tokens=None, system_prompt=""):
    """Generate completion from loaded model."""
    params = CONFIG["generation_params"].copy()
    if max_tokens:
        params["max_tokens"] = max_tokens

    # If system prompt provided, prepend it to the user prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    else:
        full_prompt = prompt

    payload = {
        "prompt": full_prompt,
        **params
    }

    try:
        response = requests.post(
            f"http://127.0.0.1:{CONFIG['server_port']}/completion",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result.get("content", "").strip()
    except Exception as e:
        log(f"ERROR: Generation failed: {e}")
        return None

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

TEMPLATES = {
    "character": """You are an expert writer creating a detailed character profile.

Generate a comprehensive character profile based on this description:
{user_prompt}

The profile must include these sections:

**BASIC INFORMATION**
- Full Name
- Age & Species
- Physical Appearance (height, build, distinguishing features)
- Occupation/Role

**PERSONALITY**
- Core Personality Traits (3-5 traits)
- Strengths & Weaknesses
- Motivations & Goals
- Fears & Vulnerabilities

**BACKGROUND**
- Origin/Birthplace
- Family & Early Life
- Formative Experiences
- Current Situation

**SKILLS & ABILITIES**
- Special Skills/Talents
- Combat Abilities (if applicable)
- Magic/Tech Proficiency (if applicable)
- Weaknesses/Limitations

**APPEARANCE VARIATIONS**
- Default Outfit
- Combat/Work Outfit
- Formal/Special Occasion Outfit
- Distinctive Accessories

**CHARACTER PROGRESSION**
- Arc Potential (how might they grow/change?)
- Key Relationships
- Internal Conflicts

**VOICE & MANNERISMS**
- Speech patterns
- Distinctive mannerisms
- Emotional tells

Write in clear, specific prose. Be creative but consistent. Target length: 800-1200 words.

Character Profile:""",

    "magic": """You are an expert worldbuilder creating a magic system.

Design a complete magic system based on this concept:
{user_prompt}

The system must include:

**CORE MECHANICS**
- Source of Power (where does magic come from?)
- How Magic is Accessed (rituals, innate, tools, etc.)
- Types/Schools of Magic
- Power Scaling (novice to master)

**LIMITATIONS & COSTS**
- What prevents unlimited power?
- Physical/mental costs of use
- Forbidden or dangerous techniques
- Societal restrictions

**LEARNING & MASTERY**
- How is magic learned?
- Training methods
- Talent vs. Study
- Time required for competency

**VISUAL & SENSORY**
- What does magic look like?
- Sounds, smells, physical sensations
- Observable effects

**SOCIETAL IMPACT**
- How common is magic?
- Social status of magic users
- Economic implications
- Cultural attitudes toward magic

**EXAMPLES**
- Novice-level spell example
- Intermediate-level spell example
- Master-level spell example
- Forbidden/dangerous spell example

Be specific about rules and limitations. Create internal consistency. Target length: 1000-1500 words.

Magic System:""",

    "science": """You are a science fiction worldbuilder creating a technological system.

Design a detailed sci-fi technology/science system based on:
{user_prompt}

The system must include:

**CORE PRINCIPLES**
- Scientific foundation (pseudo-science is fine, but internally consistent)
- How it works (layman's explanation)
- Discovery/invention history
- Current state of technology

**TECHNICAL SPECIFICATIONS**
- Key components
- Energy requirements
- Operational limitations
- Safety concerns

**PRACTICAL APPLICATIONS**
- Primary uses
- Military applications (if any)
- Civilian applications
- Experimental/emerging uses

**LIMITATIONS & DRAWBACKS**
- Why isn't this everywhere?
- Cost (economic/resource)
- Technical barriers
- Side effects or dangers

**SOCIETAL IMPACT**
- Who has access?
- Economic implications
- Political ramifications
- Cultural/social changes

**VISUAL & TECHNICAL AESTHETICS**
- What does it look like?
- Sound/visual effects
- User interface elements

**EXAMPLES**
- Basic application example
- Advanced application example
- Cutting-edge experimental use
- Failed/dangerous attempt

Be scientifically plausible (within your setting's rules). Target length: 1000-1500 words.

Technology System:""",

    "artifact": """You are a creative writer designing a powerful artifact or relic.

Create a detailed artifact based on this description:
{user_prompt}

Include these elements:

**BASIC DESCRIPTION**
- Name of the artifact
- Physical appearance
- Size, weight, materials
- Current condition

**HISTORY & ORIGIN**
- Who created it and when?
- Why was it made?
- Previous owners/wielders
- How was it lost/found?

**POWERS & ABILITIES**
- Primary power/function
- Secondary abilities
- Passive effects
- Hidden or unlockable abilities

**LIMITATIONS & DRAWBACKS**
- Usage costs or requirements
- Weaknesses or vulnerabilities
- Dangers to the wielder
- Moral/ethical complications

**LORE & LEGEND**
- Stories told about it
- Prophecies or myths
- Famous moments in history
- Conflicting accounts

**CURRENT STATUS**
- Where is it now?
- Who seeks it?
- Protection/security measures
- Potential consequences if misused

Be creative with both powers and limitations. Make it narratively interesting, not just "overpowered." Target length: 600-800 words.

Artifact Profile:""",

    "culture": """You are an expert worldbuilder creating a detailed cultural background.

Design a comprehensive culture/species/faction based on:
{user_prompt}

Include these elements:

**OVERVIEW**
- Name of culture/species/faction
- Population size and distribution
- Key characteristics that define them
- Place in the larger world/setting

**BIOLOGY/PHYSIOLOGY** (if non-human species)
- Physical characteristics
- Lifespan and lifecycle
- Special abilities or adaptations
- Biological needs and weaknesses

**SOCIETY & GOVERNANCE**
- Social structure and hierarchy
- Government/leadership model
- Class systems or castes
- Gender roles and family structure

**CULTURE & BELIEFS**
- Core values and philosophy
- Religious or spiritual beliefs
- Art, music, and creative expression
- Important rituals and traditions

**TECHNOLOGY & MAGIC**
- Level of technological advancement
- Relationship with magic (if applicable)
- Notable inventions or techniques
- Architectural style

**ECONOMY & RESOURCES**
- Primary industries and exports
- Currency and trade practices
- Resource abundance/scarcity
- Economic relationship with other cultures

**MILITARY & CONFLICT**
- Military structure and tactics
- Warrior traditions
- Historical conflicts
- Current threats or enemies

**RELATIONSHIPS**
- Allies and trading partners
- Rivals and enemies
- Diplomatic standing
- Cultural exchange or isolation

**NOTABLE INDIVIDUALS**
- Famous historical figures
- Current leaders
- Cultural heroes or villains

Be specific and internally consistent. Create depth and nuance. Target length: 1200-1500 words.

Cultural Profile:""",

    "relationships": """You are a narrative designer mapping character relationships.

Create a relationship web for these characters:
{user_prompt}

For each relationship, detail:

**RELATIONSHIP MATRIX**
For each pair of characters, describe:

- **Nature of Relationship**: Family, friends, rivals, enemies, romantic, professional, etc.
- **History**: How did they meet? What shaped their relationship?
- **Current Dynamic**: How do they interact now?
- **Power Balance**: Who has more influence/power in the relationship?
- **Emotional Core**: What feelings drive this relationship?
- **Unresolved Issues**: Conflicts, secrets, debts
- **Potential Development**: How might this relationship change?

**GROUP DYNAMICS**
- How do these characters function as a group?
- Alliances and factions within the group
- Social hierarchy or pecking order
- Group conflicts and tensions

**NARRATIVE POTENTIAL**
- Key conflicts that could arise
- Romantic possibilities
- Betrayal opportunities
- Redemption arcs

**RELATIONSHIP EVOLUTION**
- How relationships might change over time
- Potential breaking points
- Healing or reconciliation opportunities

Be specific about emotions, history, and narrative potential. Target length: 800-1000 words.

Relationship Web:""",

    "concept": """You are an expert story developer creating a complete Concept.txt file for AI-assisted book generation.

Based on this premise:
{user_prompt}

Create a comprehensive concept document following this exact structure:

[CONCEPT]
(Write a 150-200 word logline/premise that captures the core story, conflict, and stakes)

[CONSTRAINTS]
GENRE: (Be specific: LitRPG, Romance, Sci-Fi, Fantasy, etc.)
TONE: (List 3-4 tone descriptors)
FORMAT: Novella (~40,000-50,000 words)
CHAPTER COUNT: 20 chapters
HEAT LEVEL: (None/Mild/Moderate/Explicit - specify if publishable or adult)
POV: (First Person/Third Person Limited - specify whose perspective)
THEMES: (List 3-5 core themes)

[SUPER STRUCTURE SIGNPOSTS - JAMES SCOTT BELL]
**CRITICAL: These structural beats must appear at the specified chapters.**

1. **DISTURBANCE** (Ch 2, ~10%): (What shatters the protagonist's normal world?)

2. **CARE PACKAGE** (Ch 4, ~20%): (What shows the protagonist's humanity/compassion?)

3. **ARGUMENT AGAINST TRANSFORMATION** (Ch 5, ~25%): (What tempts them to give up?)

4. **DOORWAY OF NO RETURN #1** (Ch 5, ~25%): (What irreversible choice/event commits them to the journey?)

5. **MIRROR MOMENT** (Ch 10, ~50% - MIDPOINT): **MOST IMPORTANT BEAT**
   (What forces the protagonist to confront who they really are? What question do they face about themselves? What do they choose?)

6. **PET THE DOG** (Ch 13, ~65%): (What shows their deeper compassion/humanity?)

7. **DOORWAY OF NO RETURN #2** (Ch 15, ~75%): (What raises the stakes so high they can't turn back?)

8. **MOUNTING FORCES** (Ch 16-18, 80-90%): (How do things get progressively worse?)

9. **FINAL BATTLE** (Ch 19, ~95%): (The climactic confrontation - may be physical, emotional, or intellectual)

10. **RESOLUTION** (Ch 20, 100%): (How is the new status quo established? What has changed?)

[STORY STRUCTURE]
ACT 1 (Chapters 1-7): (Title for Act 1)
- (Brief bullet points for each chapter's purpose)

ACT 2 (Chapters 8-14): (Title for Act 2)
- (Brief bullet points for each chapter's purpose)

ACT 3 (Chapters 15-20): (Title for Act 3)
- (Brief bullet points for each chapter's purpose)

[CHARACTER REQUIREMENTS]
PROTAGONIST: (Name, age, role, personality, arc)
KEY SUPPORTING CHARACTERS: (3-5 main supporting characters with names, roles, relationships to protagonist)

[EMOTIONAL BEATS - BY CHAPTER]
(List each chapter 1-20 with its primary emotional beat or plot event in one sentence)

[PROSE STYLE]
(Describe narrative voice, pacing, any special stylistic elements, influences)

[UNIQUE ELEMENTS]
(What makes this story distinctive? Special mechanics, narrative devices, thematic depth, etc.)

Target length: 2000-3000 words. Be specific and detailed.

Concept Document:""",

    "scene-dialogue": """You are a skilled fiction writer crafting a dialogue scene.

Write a dialogue-focused scene based on:
{user_prompt}

Requirements:
- Length: 500-800 words
- Focus on character voice and subtext
- Show emotion through dialogue and small actions
- Include brief action beats between dialogue
- Create tension or development through conversation
- End with emotional impact or revelation

Use proper formatting:
"Dialogue," she said, action beat.
"More dialogue."

Write vivid, character-driven dialogue. Avoid "on-the-nose" exposition.

Scene:""",

    "scene-combat": """You are an action writer crafting an exciting combat scene.

Write a dynamic combat/action scene based on:
{user_prompt}

Requirements:
- Length: 600-1000 words
- Clear choreography (reader can visualize the action)
- Vary sentence length for pacing (short sentences for intensity)
- Include sensory details (sounds, pain, movement)
- Show character personality through fighting style
- Have clear stakes and consequences
- Build to a climax and resolution

Write visceral, exciting action. Make every move matter.

Combat Scene:""",

    "scene-explicit": """You are a skilled adult fiction writer crafting an intimate scene.

Write an explicit romantic/sexual scene based on:
{user_prompt}

Requirements:
- Length: 800-1200 words
- Focus on emotional connection and character dynamics
- Use evocative but tasteful language
- Show consent and mutual desire
- Include sensory details and emotional responses
- Build tension gradually
- Balance physical intimacy with emotional intimacy

Write sensual, character-driven content. Show the relationship dynamic through intimacy.

Scene:""",

    "scene-general": """You are a versatile fiction writer crafting a narrative scene.

Write a complete scene based on:
{user_prompt}

Requirements:
- Length: 500-1000 words
- Clear setting (place, time, atmosphere)
- Character development or plot progression
- Sensory details that ground the reader
- Emotional resonance
- Strong opening and ending

Write engaging, immersive prose. Make the scene feel complete.

Scene:""",

    "image-prompt": """You are an expert at creating detailed image generation prompts for character art.

Create a comprehensive image generation prompt for:
{user_prompt}

The prompt should include:

**MAIN PROMPT** (For AI image generation):
(A detailed, comma-separated description optimized for Stable Diffusion/DALL-E including: character description, clothing, pose, setting, art style, lighting, mood. 150-200 words)

**NEGATIVE PROMPT**:
(Things to avoid: low quality, bad anatomy, etc. Standard negative prompt additions)

**TECHNICAL SETTINGS**:
- Recommended model: (e.g., "Stable Diffusion XL" or "Midjourney v6")
- Aspect ratio: (e.g., "Portrait 2:3" or "Square 1:1")
- Style tags: (e.g., "digital art, anime, realistic, etc.")

**VARIATIONS**:
- Alternative outfit prompt
- Alternative pose/expression prompt
- Alternative art style prompt

**VISUALNOVEL.PICS INTEGRATION**:
Structured JSON for import (see below)

Be extremely specific about visual details. Optimize for AI image generation clarity.

Image Generation Prompt:"""
}

# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_content(content_type, user_prompt, model_type="worldbuilding", output_format=".md", system_prompt="Default"):
    """Generate content based on type and prompt."""

    if content_type not in TEMPLATES:
        log(f"ERROR: Unknown content type '{content_type}'")
        return None

    # Ensure model is loaded
    if not ensure_model_loaded(model_type):
        return None

    # Build prompt
    template = TEMPLATES[content_type]
    full_prompt = template.format(user_prompt=user_prompt)

    # Add format-specific instructions (before the final output marker)
    format_instructions = {
        ".txt": "\n\nFORMAT REQUIREMENT: Plain text only. Do not use markdown syntax (no *, #, _, or other formatting). Do not include these instructions in your output. Write only the requested content in clean, readable prose.",
        ".md": "\n\nFORMAT REQUIREMENT: Use markdown formatting (# headers, **bold**, *italics*, lists). Do not include these instructions in your output. Write only the requested content.",
        ".html": "\n\nFORMAT REQUIREMENT: Output valid HTML with proper tags (<h1>, <h2>, <p>, <ul>, <ol>, <table>). Do not include these instructions in your output. Write only the HTML content.",
        ".json": "\n\nFORMAT REQUIREMENT: Output ONLY valid JSON. Do not write explanations or include these instructions. Start directly with { or [ and end with } or ]. Use proper JSON syntax throughout.",
        ".xml": "\n\nFORMAT REQUIREMENT: Output ONLY valid XML. Do not write explanations or include these instructions. Start directly with <?xml or root tags. Use proper XML syntax throughout."
    }

    if output_format in format_instructions:
        full_prompt += format_instructions[output_format]

    # Get system prompt text
    sys_prompt_text = SYSTEM_PROMPTS.get(system_prompt, "")

    log(f"Generating {content_type} as {output_format} with '{system_prompt}' system prompt...")
    start_time = time.time()

    # Generate
    result = generate_completion(full_prompt, system_prompt=sys_prompt_text)

    if result:
        # Clean up any leaked instructions or meta-text
        result = clean_output(result, output_format)

        elapsed = time.time() - start_time
        word_count = len(result.split())
        log(f"Generated {word_count} words in {elapsed:.1f}s")

        # Free VRAM if configured to do so
        if not CONFIG.get("keep_server_loaded", False):
            log("Releasing VRAM (keep_server_loaded=False)")
            kill_server()

        return result

    return None

def clean_output(text, output_format):
    """Remove leaked instruction text and meta-commentary from output."""
    import re

    # Patterns that indicate leaked instructions (case-insensitive)
    instruction_patterns = [
        r'^.*?FORMAT REQUIREMENT:.*?\n',
        r'^.*?IMPORTANT:.*?\n',
        r'^.*?Do not include these instructions.*?\n',
        r'^.*?The scene must follow all requirements.*?\n',
        r'^.*?Each sentence should be clear and concise.*?\n',
        r'^.*?demonstrate a skilled understanding.*?\n',
        r'^.*?Target length:.*?\n',
        r'^.*?Requirements:.*?\n\n',
    ]

    cleaned = text
    for pattern in instruction_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned

def save_output(content, content_type, output_format=".md", filename=None):
    """Save generated content to file."""
    if content is None:
        log("ERROR: Cannot save None content")
        return None

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{content_type}_{timestamp}{output_format}"

    # Determine subfolder based on type
    subfolder = {
        "character": "characters",
        "magic": "magic_systems",
        "science": "science_systems",
        "artifact": "artifacts",
        "culture": "cultures",
        "relationships": "relationships",
        "concept": "concepts",
        "scene-dialogue": "scenes",
        "scene-combat": "scenes",
        "scene-explicit": "scenes",
        "scene-general": "scenes",
        "image-prompt": "image_prompts"
    }.get(content_type, "misc")

    output_dir = Path(CONFIG["output_folder"]) / subfolder
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    log(f"Saved to: {output_path}")
    return output_path

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NarrAider - AI-Powered Narrative Creation Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Character profile
  python narraider.py --type character --prompt "Elven warrior princess, 200 years old"

  # Magic system
  python narraider.py --type magic --prompt "Blood magic with aging cost"

  # Explicit scene
  python narraider.py --type scene-explicit --prompt "Space pirates after near-death" --model explicit

  # Story concept
  python narraider.py --type concept --prompt "Cozy coffee shop romance" --output outputs/concepts/coffee_shop.txt
        """
    )

    parser.add_argument('--type', required=True, choices=list(TEMPLATES.keys()),
                       help='Type of content to generate')
    parser.add_argument('--prompt', required=True,
                       help='Description of what to generate')
    parser.add_argument('--model', default='worldbuilding', choices=['worldbuilding', 'explicit'],
                       help='Which model to use (default: worldbuilding)')
    parser.add_argument('--format', default='.md', choices=['.txt', '.md', '.html', '.json', '.xml'],
                       help='Output format (default: .md)')
    parser.add_argument('--output', help='Output file path (optional)')
    parser.add_argument('--version', action='version', version=f'NarrAider {VERSION}')

    args = parser.parse_args()

    # Load config
    load_config()

    try:
        # Generate content
        result = generate_content(args.type, args.prompt, args.model, args.format)

        if result:
            # Save to file
            output_path = save_output(result, args.type, args.format, args.output)

            # Print to console
            print("\n" + "="*80)
            print(result)
            print("="*80 + "\n")

            log("Generation complete!")
        else:
            log("Generation failed.")
            return 1

    finally:
        # Cleanup
        kill_server()

    return 0

if __name__ == "__main__":
    exit(main())
