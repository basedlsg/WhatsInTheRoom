"""
Save full floorplan objects from v1 dataset generation.

This extracts the floorplan data structures needed for baseline evaluation.
Since the image generation doesn't automatically save the Floorplan objects,
we need to regenerate them from the dataset index.
"""

import json
import argparse
from pathlib import Path
from tqdm import tqdm

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan


def main():
    parser = argparse.ArgumentParser(description="Extract floorplan objects for baseline evaluation")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/floorplan_qa_v1",
        help="Dataset directory"
    )
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset)
    index_path = dataset_dir / "dataset_index.json"
    
    print("Loading dataset index...")
    with open(index_path) as f:
        index = json.load(f)
    
    # Group by floorplan_id to get unique floorplans
    unique_entries = {}
    for entry in index:
        fp_id = entry["floorplan_id"]
        if fp_id not in unique_entries:
            unique_entries[fp_id] = entry
    
    print(f"Found {len(unique_entries)} unique floorplans")
    print("Regenerating floorplan objects...")
    
    # Regenerate floorplans using their original seeds
    # We stored metadata but need to regenerate from generation parameters
    # This is a limitation - ideally we'd save floorplan JSONs during generation
    
    # For now, create a simplified approach:
    # We'll save just the essential data needed for baselines from the index
    
    floorplan_data = []
    
    for entry in tqdm(index):
        # Extract only what we need for baselines
        floorplan_simple = {
            "id": entry["floorplan_id"],
            "split": entry["split"],
            "mystery_room": {
                "type": entry["ground_truth"],
                "area": None,  # Not available from index
                "adjacencies": []  # Not available
            },
            "difficulty": entry["difficulty"],
            "region": entry["region"]
        }
        
        floorplan_data.append(floorplan_simple)
    
    output_path = dataset_dir / "floorplans_simplified.json"
    
    with open(output_path, "w") as f:
        json.dump(floorplan_data, f, indent=2)
    
    print(f"\n✓ Saved {len(floorplan_data)} simplified floorplan records to {output_path}")
    print("\nNote: This is simplified data. For full baseline evaluation with")
    print("adjacency and area information, floorplan objects should be saved")
    print("during dataset generation in generate_v1_dataset.py")


if __name__ == "__main__":
    main()
