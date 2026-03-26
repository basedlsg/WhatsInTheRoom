"""
Main script for generating the FloorplanQA v1 Benchmark Dataset.

Generates three distinct splits:
1. Clean Set: Balanced difficulty/room types, normal style.
2. Adversarial Set: Stress tests with specific perturbations.
3. Corruption Set: Visual robustness tests.
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any

from tqdm import tqdm

from src.core.types import RegionType, RoomType
from src.generation.balanced_generator import BalancedGenerator
from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.rendering.image_renderer import FloorplanRenderer
from src.rendering.styles import DEFAULT_STYLE as NORMAL_STYLE, MEDIUM_SKETCHY_STYLE, EXTREME_SKETCHY_STYLE
from src.rendering.corruptions import apply_corruption, CorruptionType, CORRUPTION_PRESETS

# Configuration
CLEAN_COUNT = 3000
ADVERSARIAL_COUNT = 1000
CORRUPTION_COUNT = 1000
SEED = 2025

def save_dataset_entry(
    entry: Dict[str, Any], 
    output_dir: Path, 
    index_list: List[Dict]
):
    """Save image and append metadata to index."""
    # Save image
    image_filename = f"{entry['floorplan_id']}_{entry['split']}_{entry['subtype']}.png"
    image_path = output_dir / "images" / image_filename
    image_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    entry['image'].save(image_path)
    
    # Create metadata entry (exclude PIL image)
    metadata = entry.copy()
    del metadata['image']
    metadata['image_path'] = str(image_path.relative_to(output_dir.parent))
    
    index_list.append(metadata)


def generate_clean_set(generator: BalancedGenerator, output_dir: Path) -> List[Dict]:
    """Generate the clean evaluation set."""
    print(f"\n=== Generating Clean Set ({CLEAN_COUNT} samples) ===")
    
    regions = list(RegionType)
    floorplans = generator.generate_balanced_dataset(
        target_count=CLEAN_COUNT,
        regions=regions,
        min_samples_per_room_type=400
    )
    
    entries = []
    for fp in tqdm(floorplans, desc="Rendering clean set"):
        # Render normal style
        renderer = FloorplanRenderer(NORMAL_STYLE)
        img = renderer.render_to_image(fp)
        
        entries.append({
            "floorplan_id": fp.id,
            "split": "clean",
            "type": "normal",
            "subtype": "n/a",
            "difficulty": fp.metadata["mystery_room"]["difficulty"],
            "ground_truth": fp.mystery_room.room_type.value,
            "region": fp.region.value,
            "rendering_style": "normal",
            "corruption_type": "none",
            "corruption_type": "none",
            "corruption_severity": 0,
            "image": img,
            # v1.2 Reproducibility
            "generation_seed": fp.metadata.get("generation", {}).get("seed"),
            "attempt_index": fp.metadata.get("generation", {}).get("attempt_index"),
            "renderer_version": "1.1.0"
        })
        
    return entries


def generate_adversarial_set(
    clean_floorplans: List[Any], # actually List[Floorplan] but avoiding circular import issues if any
    output_dir: Path,
    seed: int
) -> List[Dict]:
    """Generate the adversarial stress-test set."""
    print(f"\n=== Generating Adversarial Set ({ADVERSARIAL_COUNT} samples) ===")
    
    adv_gen = AdversarialGenerator(seed=seed)
    entries = []
    
    # Strategies to cycle through
    strategies = [
        "size_mismatch", 
        "shape_confusion", 
        "window_deception", 
        "adjacency_violation", 
        "missing_rooms"
    ]
    
    # Generate new adversarial floorplans
    # We generate fresh ones to ensure they are tailored to the strategy
    # rather than modifying the clean set (which might not be susceptible)
    
    samples_per_strategy = ADVERSARIAL_COUNT // len(strategies)
    
    for strategy_idx, strategy in enumerate(strategies):
        print(f"Generating {strategy}...")
        for i in tqdm(range(samples_per_strategy)):
            # Generate a base floorplan tailored for this strategy
            # (AdversarialGenerator handles the creation)
            # We pick random region/size
            region = adv_gen.rng.choice(list(RegionType))
            # Pick size based on strategy (some need space)
            from src.core.types import SizeCategory
            size = adv_gen.rng.choice([SizeCategory.MEDIUM, SizeCategory.LARGE])
            # Actually AdversarialGenerator.generate_confusing_floorplan takes region/size
            # We need to pick them.
            
            # Simplified: Use the generator's internal logic
            # We need to expose a method to generate random adversarial
            # For now, we'll manually pick parameters
            region = adv_gen.rng.choice(list(RegionType))
            # Pick size based on strategy (some need space)
            from src.core.types import SizeCategory
            size = adv_gen.rng.choice([SizeCategory.MEDIUM, SizeCategory.LARGE])
            
            fp = adv_gen.generate_confusing_floorplan(
                region=region,
                size_category=size,
                confusion_type=strategy,
                severity=Severity.MEDIUM # Standardize on Medium for the main test set
            )
            
            renderer = FloorplanRenderer(NORMAL_STYLE)
            img = renderer.render_to_image(fp)
            
            entries.append({
                "floorplan_id": fp.id,
                "split": "adversarial",
                "type": "adversarial",
                "subtype": strategy,
                "difficulty": fp.metadata["mystery_room"]["difficulty"], # Adversarial might break difficulty calc, but we keep it
                "ground_truth": fp.mystery_room.room_type.value,
                "region": fp.region.value,
                "rendering_style": "normal",
                "corruption_type": "none",
                "corruption_type": "none",
                "corruption_severity": 0,
                "image": img,
                # v1.2 Reproducibility
                "generation_seed": seed, # The base seed for the adv generator
                "attempt_index": strategy_idx * samples_per_strategy + i, # Linear index in the sequence
                "renderer_version": "1.1.0"
            })
            
    return entries


def generate_corruption_set(clean_entries: List[Dict], seed: int) -> List[Dict]:
    """Generate the corruption robustness set."""
    print(f"\n=== Generating Corruption Set ({CORRUPTION_COUNT} samples) ===")
    
    import random
    rng = random.Random(seed)
    
    # Select subset of clean entries to corrupt
    # We want to test same floorplans across different corruptions if possible
    # Or just random sample. Let's do random sample for coverage.
    
    source_entries = rng.sample(clean_entries, CORRUPTION_COUNT)
    entries = []
    
    corruption_types = [
        CorruptionType.BLUR,
        CorruptionType.CONTRAST,
        CorruptionType.JPEG,
        CorruptionType.SKEW
    ]
    
    for i, source in enumerate(tqdm(source_entries, desc="Applying corruptions")):
        # Cycle through corruption types
        c_type = corruption_types[i % len(corruption_types)]
        # Pick random severity
        severity_level = rng.choice(["slight", "medium", "extreme"])
        severity_val = CORRUPTION_PRESETS[c_type][severity_level]
        
        # Apply corruption to the source image
        # Note: source['image'] is a PIL object
        corrupted_img, _ = apply_corruption(source['image'], c_type, severity_val)
        
        entries.append({
            "floorplan_id": source['floorplan_id'], # Same ID as clean
            "split": "corruption",
            "type": "normal", # Underlying layout is normal
            "subtype": "n/a",
            "difficulty": source['difficulty'],
            "ground_truth": source['ground_truth'],
            "region": source['region'],
            "rendering_style": "normal",
            "corruption_type": c_type.value,
            "corruption_severity": severity_val,
            "image": corrupted_img,
            # v1.2 Reproducibility - Inherit from source
            "generation_seed": source.get("generation_seed"),
            "attempt_index": source.get("attempt_index"),
            "renderer_version": "1.1.0"
        })
        
    return entries


def main():
    parser = argparse.ArgumentParser(description="Generate FloorplanQA v1 Dataset")
    parser.add_argument("--output", type=str, default="data/floorplan_qa_v1", help="Output directory")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    if output_dir.exists():
        print(f"Warning: Output directory {output_dir} exists. Cleaning up...")
        shutil.rmtree(output_dir)
    
    (output_dir / "images").mkdir(parents=True)
    
    # 1. Clean Set
    clean_gen = BalancedGenerator(seed=SEED)
    clean_entries = generate_clean_set(clean_gen, output_dir)
    
    # 2. Adversarial Set
    adv_entries = generate_adversarial_set([], output_dir, seed=SEED + 1)
    
    # 3. Corruption Set
    # We use clean_entries as source
    corr_entries = generate_corruption_set(clean_entries, seed=SEED + 2)
    
    # Combine and Save
    all_entries = clean_entries + adv_entries + corr_entries
    dataset_index = []
    
    print(f"\nSaving {len(all_entries)} total entries...")
    for entry in tqdm(all_entries, desc="Saving to disk"):
        save_dataset_entry(entry, output_dir, dataset_index)
        
    # Save index
    with open(output_dir / "dataset_index.json", "w") as f:
        json.dump(dataset_index, f, indent=2)
        
    # v1.2 Metadata - Save Global Config
    meta_info = {
        "dataset_version": "1.2.0",
        "global_seed": SEED,
        "renderer_version": "1.1.0", # The logic is v1.1 (icons), schema is v1.2
        "generator_version": "1.2.0",
        "counts": {
            "clean": len(clean_entries),
            "adversarial": len(adv_entries),
            "corruption": len(corr_entries),
            "total": len(dataset_index)
        }
    }
    with open(output_dir / "meta.json", "w") as f:
        json.dump(meta_info, f, indent=2)

    print("\n=== Generation Complete (v1.2) ===")
    print(f"Total samples: {len(dataset_index)}")
    print(f"Clean: {len(clean_entries)}")
    print(f"Adversarial: {len(adv_entries)}")
    print(f"Corruption: {len(corr_entries)}")


if __name__ == "__main__":
    main()
