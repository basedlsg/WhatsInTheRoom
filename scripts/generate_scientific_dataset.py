
import sys
from pathlib import Path
import os
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.generation.adversarial_generator import AdversarialGenerator
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import DEFAULT_STYLE, SKETCHY_STYLE
from src.storage.floorplan_store import save_floorplan

def generate_scientific_dataset():
    print("Generating Scientific Dataset...")
    
    output_dir = "data/scientific_dataset"
    floorplan_dir = os.path.join(output_dir, "floorplans")
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(floorplan_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    
    dataset_index = []
    
    # Configuration
    NUM_NORMAL = 5
    NUM_ADVERSARIAL = 5
    
    # 1. Generate Normal Floorplans
    print(f"Generating {NUM_NORMAL} normal floorplans...")
    for i in range(NUM_NORMAL):
        fp = generate_floorplan(
            seed=1000 + i,
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM
        )
        save_floorplan(fp, floorplan_dir)
        
        # Render Normal
        img_path_normal = os.path.join(image_dir, f"{fp.id}_normal.png")
        render_floorplan(fp, img_path_normal, style=DEFAULT_STYLE)
        
        # Render Sketchy
        img_path_sketchy = os.path.join(image_dir, f"{fp.id}_sketchy.png")
        render_floorplan(fp, img_path_sketchy, style=SKETCHY_STYLE)
        
        dataset_index.append({
            "id": fp.id,
            "type": "normal",
            "ground_truth": fp.mystery_room.room_type.value if fp.mystery_room else None,
            "images": {
                "normal": img_path_normal,
                "sketchy": img_path_sketchy
            }
        })
        
    # 2. Generate Adversarial Floorplans
    print(f"Generating {NUM_ADVERSARIAL} adversarial floorplans...")
    adv_gen = AdversarialGenerator(seed=2000)
    for i in range(NUM_ADVERSARIAL):
        fp = adv_gen.generate_confusing_floorplan(
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM,
            confusion_type="size_mismatch"
        )
        save_floorplan(fp, floorplan_dir)
        
        # Render Normal
        img_path_normal = os.path.join(image_dir, f"{fp.id}_normal.png")
        render_floorplan(fp, img_path_normal, style=DEFAULT_STYLE)
        
        # Render Sketchy
        img_path_sketchy = os.path.join(image_dir, f"{fp.id}_sketchy.png")
        render_floorplan(fp, img_path_sketchy, style=SKETCHY_STYLE)
        
        dataset_index.append({
            "id": fp.id,
            "type": "adversarial",
            "subtype": "size_mismatch",
            "ground_truth": fp.mystery_room.room_type.value if fp.mystery_room else None,
            "images": {
                "normal": img_path_normal,
                "sketchy": img_path_sketchy
            }
        })
        
    # Save index
    with open(os.path.join(output_dir, "dataset_index.json"), "w") as f:
        json.dump(dataset_index, f, indent=2)
        
    print(f"Dataset generated with {len(dataset_index)} samples.")
    print(f"Index saved to {os.path.join(output_dir, 'dataset_index.json')}")

if __name__ == "__main__":
    generate_scientific_dataset()
