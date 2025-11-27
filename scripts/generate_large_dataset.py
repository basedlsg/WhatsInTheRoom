
import sys
import os
import json
import argparse
import random
from pathlib import Path
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.generation.adversarial_generator import AdversarialGenerator
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import (
    DEFAULT_STYLE, 
    MEDIUM_SKETCHY_STYLE, 
    EXTREME_SKETCHY_STYLE
)

def generate_dataset(count: int = 100, output_dir: str = "data/scientific_dataset_large"):
    """Generate a large, balanced dataset for scientific experiments."""
    
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    floorplans_dir = os.path.join(output_dir, "floorplans")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(floorplans_dir, exist_ok=True)
    
    # Define distribution
    # We want roughly equal parts of each category
    categories = [
        "normal",
        "size_mismatch",
        "shape_confusion",
        "window_deception",
        "adjacency_violation",
        "missing_rooms"
    ]
    
    samples_per_category = count // len(categories)
    remainder = count % len(categories)
    
    dataset_index = []
    
    adv_gen = AdversarialGenerator(seed=42)
    
    pbar = tqdm(total=count, desc="Generating Dataset")
    
    for i, category in enumerate(categories):
        # Add remainder to first category (normal)
        n_samples = samples_per_category + (remainder if i == 0 else 0)
        
        for j in range(n_samples):
            seed = i * 10000 + j
            
            # Randomize parameters
            region = random.choice(list(RegionType))
            size_cat = random.choice(list(SizeCategory))
            
            if category == "normal":
                fp = generate_floorplan(
                    seed=seed,
                    region=region,
                    size_category=size_cat
                )
                is_adversarial = False
                subtype = "n/a"
            else:
                fp = adv_gen.generate_confusing_floorplan(
                    region=region,
                    size_category=size_cat,
                    confusion_type=category
                )
                is_adversarial = True
                subtype = category
                
            # Save floorplan JSON
            fp_path = os.path.join(floorplans_dir, f"{fp.id}.json")
            with open(fp_path, "w") as f:
                f.write(json.dumps(fp.to_dict(), indent=4))
                
            # Render in 3 styles
            styles = {
                "normal": DEFAULT_STYLE,
                "sketchy_medium": MEDIUM_SKETCHY_STYLE,
                "sketchy_extreme": EXTREME_SKETCHY_STYLE
            }
            
            image_paths = {}
            for style_name, style in styles.items():
                img_filename = f"{fp.id}_{style_name}.png"
                img_path = os.path.join(images_dir, img_filename)
                render_floorplan(fp, img_path, style=style)
                image_paths[style_name] = img_path
                
            # Add to index
            # Find ground truth (mystery room type)
            mystery_room = next((r for r in fp.rooms if r.is_mystery), None)
            ground_truth = mystery_room.room_type.value if mystery_room else "unknown"
            
            dataset_index.append({
                "id": fp.id,
                "type": "adversarial" if is_adversarial else "normal",
                "subtype": subtype,
                "ground_truth": ground_truth,
                "region": region.value,
                "size": size_cat.value,
                "images": image_paths,
                "floorplan_path": fp_path
            })
            
            pbar.update(1)
            
    pbar.close()
    
    # Save index
    index_path = os.path.join(output_dir, "dataset_index.json")
    with open(index_path, "w") as f:
        json.dump(dataset_index, f, indent=4)
        
    print(f"\n✅ Generated {len(dataset_index)} samples in {output_dir}")
    print(f"   - Normal: {samples_per_category + remainder}")
    print(f"   - Adversarial: {samples_per_category * (len(categories)-1)} (across 5 strategies)")
    print(f"   - Total Images: {len(dataset_index) * 3}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate large scientific dataset")
    parser.add_argument("--count", type=int, default=100, help="Number of floorplans to generate")
    parser.add_argument("--output", type=str, default="data/scientific_dataset_large", help="Output directory")
    
    args = parser.parse_args()
    
    generate_dataset(args.count, args.output)
