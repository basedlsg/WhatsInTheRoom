import json
import random
from pathlib import Path
from tqdm import tqdm
from PIL import Image

from src.generation.generator import generate_floorplan
from src.core.types import RegionType, SizeCategory, RoomType
from src.rendering.image_renderer import FloorplanRenderer
from src.rendering.styles import DEFAULT_STYLE as NORMAL_STYLE

# Output directory for fixed images
OUTPUT_DIR = Path("data/floorplan_qa_v1_fixed/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    renderer = FloorplanRenderer(NORMAL_STYLE) # Fixtures enabled by default
    
    # Check if fixtures enabled
    print(f"Renderer fixtures enabled: {renderer.style.show_fixtures}")
    
    SEED = 9999 # New seed for test
    rng = random.Random(SEED)
    
    test_set = []
    
    print("Regenerating 20 kitchen samples with fixtures...")
    
    generated_count = 0
    
    # We want 20 clean kitchens
    with tqdm(total=20) as pbar:
        while generated_count < 20:
            # Generate random parameters
            region = rng.choice(list(RegionType))
            size = rng.choice(list(SizeCategory))
            current_seed = rng.randint(0, 1000000)
            
            # Generate
            try:
                fp = generate_floorplan(current_seed, region, size)
            except Exception:
                continue
                
            # Check if mystery room is kichen
            if fp.mystery_room and fp.mystery_room.room_type == RoomType.KITCHEN:
                # Found one!
                img_path = OUTPUT_DIR / f"fixed_kitchen_{generated_count}.png"
                img = renderer.render_to_image(fp)
                img.save(img_path)
                
                # Save relative path (relative to 'data' directory)
                # Hardcoding to avoid Path ambiguity
                rel_path_str = f"floorplan_qa_v1_fixed/images/fixed_kitchen_{generated_count}.png"
                
                test_set.append({
                    "floorplan_id": f"fixed_test_{generated_count}",
                    "image_path": rel_path_str,
                    "ground_truth": "kitchen",
                    "region": fp.region.value,
                    "difficulty": fp.metadata["mystery_room"]["difficulty"],
                    "split": "test_fix"
                })
                
                generated_count += 1
                pbar.update(1)
        
    # Save a mini index
    with open("data/floorplan_qa_v1_fixed/dataset_index.json", "w") as f:
        json.dump(test_set, f, indent=2)
        
    print(f"Saved 20 fixed kitchen samples to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
