#!/usr/bin/env python3
"""
Example workflows showing how to use NarrAider programmatically
"""

from narraider import (
    load_config, generate_content, save_output,
    generate_vnpics_json, kill_server
)
from pathlib import Path
import json

def workflow_complete_character(character_prompt):
    """
    Generate a complete character package:
    - Character profile
    - Image prompt
    - VNPics JSON
    """
    print("=== Complete Character Generation Workflow ===\n")

    # Load config
    load_config()

    try:
        # 1. Generate character profile
        print(f"Generating character profile for: {character_prompt}\n")
        profile = generate_content("character", character_prompt, "worldbuilding")

        if not profile:
            print("Failed to generate profile")
            return

        # 2. Generate image prompt
        print("\nGenerating image prompt...\n")
        image_prompt = generate_content("image-prompt", character_prompt, "worldbuilding")

        # 3. Save everything
        character_name = character_prompt.split(',')[0].strip()
        timestamp = Path(save_output(profile, "character")).stem

        # Save profile
        profile_path = save_output(profile, "character", f"{character_name}_profile_{timestamp}.txt")

        # Save image prompt
        if image_prompt:
            img_path = save_output(image_prompt, "image-prompt", f"{character_name}_image_{timestamp}.txt")

        # Generate VNPics JSON
        vnpics_json = generate_vnpics_json(profile, character_name)
        vnpics_path = profile_path.with_name(f"{character_name}_vnpics_{timestamp}.json")
        with open(vnpics_path, 'w', encoding='utf-8') as f:
            f.write(vnpics_json)

        print("\n=== Generation Complete! ===")
        print(f"Profile: {profile_path}")
        if image_prompt:
            print(f"Image Prompt: {img_path}")
        print(f"VNPics JSON: {vnpics_path}")

    finally:
        kill_server()

def workflow_worldbuilding_package(world_name, setting_description):
    """
    Generate a complete worldbuilding package:
    - Magic system
    - Main culture
    - Key artifact
    - Protagonist character
    """
    print(f"=== Worldbuilding Package: {world_name} ===\n")

    load_config()

    try:
        # 1. Magic system
        print("Generating magic system...")
        magic = generate_content("magic", f"Magic system for {setting_description}", "worldbuilding")
        if magic:
            save_output(magic, "magic", f"{world_name}_magic_system.txt")

        # 2. Culture
        print("\nGenerating primary culture...")
        culture = generate_content("culture", f"Primary culture in {setting_description}", "worldbuilding")
        if culture:
            save_output(culture, "culture", f"{world_name}_culture.txt")

        # 3. Artifact
        print("\nGenerating legendary artifact...")
        artifact = generate_content("artifact", f"Legendary artifact central to {setting_description}", "worldbuilding")
        if artifact:
            save_output(artifact, "artifact", f"{world_name}_artifact.txt")

        # 4. Protagonist
        print("\nGenerating protagonist character...")
        protagonist = generate_content("character", f"Protagonist for story set in {setting_description}", "worldbuilding")
        if protagonist:
            save_output(protagonist, "character", f"{world_name}_protagonist.txt")

        print(f"\n=== {world_name} Worldbuilding Package Complete! ===")
        print(f"Check outputs/ folder for all generated files")

    finally:
        kill_server()

def workflow_scene_sequence(scene_descriptions):
    """
    Generate a sequence of connected scenes.

    Example:
    scenes = [
        ("scene-general", "Character discovers mysterious artifact in ruins"),
        ("scene-dialogue", "Character discusses artifact with mentor, mentor warns of danger"),
        ("scene-combat", "Character ambushed by thieves who want the artifact")
    ]
    """
    print("=== Scene Sequence Generation ===\n")

    load_config()

    try:
        for i, (scene_type, description) in enumerate(scene_descriptions, 1):
            print(f"\nGenerating scene {i}/{len(scene_descriptions)}: {scene_type}")
            print(f"Description: {description}\n")

            scene = generate_content(scene_type, description, "worldbuilding")

            if scene:
                save_output(scene, scene_type, f"scene_{i:02d}_{scene_type}.txt")
            else:
                print(f"Failed to generate scene {i}")

        print("\n=== Scene Sequence Complete! ===")

    finally:
        kill_server()

# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Example Workflows for NarrAider\n")
        print("Usage:")
        print("  python example_workflows.py character [prompt]")
        print("  python example_workflows.py world [name] [description]")
        print("  python example_workflows.py scenes")
        print("\nExamples:")
        print('  python example_workflows.py character "Elven warrior princess, 200 years old"')
        print('  python example_workflows.py world "Shadowmere" "Dark fantasy world with blood magic"')
        print('  python example_workflows.py scenes')
        sys.exit(0)

    command = sys.argv[1]

    if command == "character":
        if len(sys.argv) < 3:
            print("Usage: python example_workflows.py character [prompt]")
            sys.exit(1)
        workflow_complete_character(" ".join(sys.argv[2:]))

    elif command == "world":
        if len(sys.argv) < 4:
            print("Usage: python example_workflows.py world [name] [description]")
            sys.exit(1)
        world_name = sys.argv[2]
        description = " ".join(sys.argv[3:])
        workflow_worldbuilding_package(world_name, description)

    elif command == "scenes":
        # Example scene sequence
        scenes = [
            ("scene-general", "Adventurer discovers ancient temple hidden in jungle"),
            ("scene-dialogue", "Adventurer's guide warns them about temple's curse, tense conversation"),
            ("scene-combat", "Temple guardians attack, desperate fight in crumbling ruins")
        ]
        workflow_scene_sequence(scenes)

    else:
        print(f"Unknown command: {command}")
        print("Available: character, world, scenes")
