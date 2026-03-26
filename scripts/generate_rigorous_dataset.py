import sys
from pathlib import Path
import os
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import HIGH_CONTRAST_STYLE, SKETCHY_STYLE
from src.storage.floorplan_store import save_floorplan

def generate_rigorous_dataset():
    print("🚀 Generating Rigorous Scientific Dataset...")
    
    output_dir = "data/rigorous_dataset"
    floorplan_dir = os.path.join(output_dir, "floorplans")
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(floorplan_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    
    dataset_index = []
    
    # Configuration
    strategies = [
        ("normal", None),
        ("adversarial", "size_mismatch"),
        ("adversarial", "topological_island"),
        ("adversarial", "windowless_master")
    ]
    
    SAMPLES_PER_STRATEGY = 25
    adv_gen = AdversarialGenerator(seed=2025)
    
    total_count = 0
    
    for main_type, subtype in strategies:
        print(f"\n📂 Processing Strategy: {main_type} - {subtype if subtype else 'default'}")
        
        for i in range(SAMPLES_PER_STRATEGY):
            seed = 3000 + total_count
            
            if main_type == "normal":
                fp = generate_floorplan(
                    seed=seed,
                    region=RegionType.MODERN_URBAN,
                    size_category=SizeCategory.LARGE
                )
            else:
                fp = adv_gen.generate_confusing_floorplan(
                    region=RegionType.MODERN_URBAN,
                    size_category=SizeCategory.LARGE,
                    confusion_type=subtype,
                    severity=Severity.EXTREME
                )
            
            save_floorplan(fp, floorplan_dir)
            
            # Render Normal (with furniture by default now)
            img_name = f"{fp.id}_render.png"
            img_path = os.path.join(image_dir, img_name)
            render_floorplan(fp, img_path, style=HIGH_CONTRAST_STYLE)
            
            dataset_index.append({
                "id": fp.id,
                "strategy": main_type,
                "subtype": subtype,
                "ground_truth": fp.mystery_room.room_type.value if fp.mystery_room else None,
                "image_path": img_path,
                "is_adversarial": main_type == "adversarial"
            })
            total_count += 1
            print(f"  ✅ Generated {fp.id} ({main_type}/{subtype})")
            
    # Save index
    index_path = os.path.join(output_dir, "dataset_index.json")
    with open(index_path, "w") as f:
        json.dump(dataset_index, f, indent=2)
        
    print(f"\n✨ Rigorous Dataset generation complete!")
    print(f"📊 Total samples: {len(dataset_index)}")
    print(f"📄 Index saved to {index_path}")

if __name__ == "__main__":
    generate_rigorous_dataset()
