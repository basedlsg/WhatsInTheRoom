#!/usr/bin/env python3
"""
Publication-grade dataset generator for FloorplanQA benchmark.

Generates balanced dataset with:
- Difficulty tiers (easy/medium/hard)
- Adversarial strategies with severity levels
- Multiple rendering styles and corruptions
"""

import json
import os
import random
from pathlib import Path
from tqdm import tqdm
from typing import List, Dict
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.generation.room_assigner import DifficultyTier
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import DEFAULT_STYLE, MEDIUM_SKETCHY_STYLE, EXTREME_SKETCHY_STYLE
from src.rendering.corruptions import CorruptionType, apply_corruption, get_corruption_severity
from PIL import Image


def generate_publication_dataset(
    output_dir: str = "data/floorplan_qa_benchmark",
    n_samples: int = 180,
    seed: int = 42
):
    """
    Generate publication-grade FloorplanQA benchmark dataset.
    
    Target distribution:
    - 180 floorplans total
    - 60 easy, 60 medium, 60 hard (by mystery room difficulty)
    - Within each difficulty: ~10 of each room type
    - Each floorplan: 1 normal + 1 adversarial variant
    - Each variant: normal, sketchy_medium, sketchy_extreme renderings
    - Subset with corruptions (blur, contrast, JPEG, skew)
    
    Args:
        output_dir: Output directory
        n_samples: Target number of floorplans
        seed: Random seed
    """
    random.seed(seed)
    rng = random.Random(seed)
    
    # Create output directories
    base_path = Path(output_dir)
    images_dir = base_path / "images"
    floorplans_dir = base_path / "floorplans"
    images_dir.mkdir(parents=True, exist_ok=True)
    floorplans_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("FLOORPLANQA PUBLICATION-GRADE DATASET GENERATION")
    print("=" * 70)
    print(f"\nTarget: {n_samples} floorplans")
    print(f"Output: {output_dir}")
    print(f"Seed: {seed}\n")
    
    # Target distribution
    samples_per_difficulty = n_samples // 3
    
    # Adversarial strategies
    adversarial_types = [
        "size_mismatch",
        "shape_confusion",
        "window_deception",
        "adjacency_violation",
        "missing_rooms"
    ]
    
    severity_levels = [Severity.SLIGHT, Severity.MEDIUM, Severity.EXTREME]
    
    # Corruption types (apply to subset)
    corruption_types = [
        CorruptionType.NONE,
        CorruptionType.BLUR,
        CorruptionType.CONTRAST,
        CorruptionType.JPEG,
        CorruptionType.SKEW
    ]
    
    dataset_index = []
    current_seed = seed
    
    # Generate floorplans with difficulty tracking
    difficulty_counts = {tier: 0 for tier in DifficultyTier}
    floorplan_count = 0
    attempts = 0
    max_attempts = n_samples * 5  # Allow more attempts
    
    with tqdm(total=n_samples, desc="Generating Dataset") as pbar:
        while floorplan_count < n_samples and attempts < max_attempts:
            attempts += 1
            current_seed += 1
            
            # Generate normal floorplan
            try:
                fp = generate_floorplan(
                    seed=current_seed,
                    region=RegionType.MODERN_URBAN,
                    size_category=SizeCategory.MEDIUM
                )
            except Exception as e:
                continue
            
            # Check mystery room difficulty
            mystery_meta = fp.metadata.get("mystery_room", {})
            difficulty_str = mystery_meta.get("difficulty", "medium")
            difficulty = DifficultyTier(difficulty_str)
            
            # For larger datasets, balance difficulty distribution
            # For smaller datasets (pilot), allow more flexibility
            if n_samples >= 60:
                if difficulty_counts[difficulty] >= samples_per_difficulty:
                    continue  # Skip to balance
            
            difficulty_counts[difficulty] += 1
            floorplan_count += 1
            
            # Save floorplan JSON
            fp_json_path = floorplans_dir / f"{fp.id}.json"
            with open(fp_json_path, "w") as f:
                f.write(json.dumps(fp.to_dict(), indent=2))
            
            # Normal variant
            normal_entry = generate_variants(
                fp, images_dir, "normal", None, None, corruption_types, rng
            )
            dataset_index.extend(normal_entry)
            
            # Adversarial variant
            adv_type = rng.choice(adversarial_types)
            adv_severity = rng.choice(severity_levels)
            
            adv_gen = AdversarialGenerator(seed=current_seed + 10000)
            try:
                fp_adv = adv_gen.generate_confusing_floorplan(
                    region=RegionType.MODERN_URBAN,
                    size_category=SizeCategory.MEDIUM,
                    confusion_type=adv_type,
                    severity=adv_severity
                )
                
                # Save adversarial floorplan JSON
                fp_adv_json_path = floorplans_dir / f"{fp_adv.id}.json"
                with open(fp_adv_json_path, "w") as f:
                    f.write(json.dumps(fp_adv.to_dict(), indent=2))
                
                adv_entry = generate_variants(
                    fp_adv, images_dir, "adversarial", adv_type, adv_severity, corruption_types, rng
                )
                dataset_index.extend(adv_entry)
                
            except Exception as e:
                print(f"\n⚠️  Skipping adversarial for {fp.id}: {e}")
            
            pbar.update(1)
    
    # Save dataset index
    index_path = base_path / "dataset_index.json"
    with open(index_path, "w") as f:
        json.dump(dataset_index, f, indent=2)
    
    # Print summary
    print(f"\n{'=' * 70}")
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated {len(dataset_index)} entries from {n_samples} floorplans")
    print(f"\nDifficulty distribution:")
    for tier, count in difficulty_counts.items():
        pct = (count / n_samples) * 100 if n_samples > 0 else 0
        print(f"  {tier.value:8s}: {count:3d} ({pct:5.1f}%)")
    
    # Count by type
    normal_count = sum(1 for e in dataset_index if e['type'] == 'normal')
    adv_count = sum(1 for e in dataset_index if e['type'] == 'adversarial')
    print(f"\nFloorplan types:")
    print(f"  Normal:      {normal_count}")
    print(f"  Adversarial: {adv_count}")
    
    print(f"\nDataset saved to: {output_dir}")
    print(f"Index: {index_path}")


def generate_variants(
    fp,
    images_dir: Path,
    plan_type: str,
    adv_type: str,
    adv_severity: Severity,
    corruption_types: List[CorruptionType],
    rng: random.Random
) -> List[Dict]:
    """
    Generate rendering variants for a floorplan.
    
    Returns list of dataset entries.
    """
    entries = []
    
    styles = {
        "normal": DEFAULT_STYLE,
        "sketchy_medium": MEDIUM_SKETCHY_STYLE,
        "sketchy_extreme": EXTREME_SKETCHY_STYLE
    }
    
    # Render in each style
    for style_name, style in styles.items():
        # Base rendering
        img_filename = f"{fp.id}_{style_name}.png"
        img_path = images_dir / img_filename
        render_floorplan(fp, str(img_path), style)
        
        # Load image for potential corruption
        img = Image.open(img_path)
        
        # Optionally apply corruption (to subset)
        corruption = rng.choice(corruption_types)
        
        if corruption != CorruptionType.NONE:
            severity_level = rng.choice(["slight", "medium", "extreme"])
            severity_value = get_corruption_severity(corruption, severity_level)
            corrupted_img, _ = apply_corruption(img, corruption, severity_value)
            
            # Save corrupted version
            corrupted_filename = f"{fp.id}_{style_name}_{corruption.value}_{severity_level}.png"
            corrupted_path = images_dir / corrupted_filename
            corrupted_img.save(corrupted_path)
            
            img_path = corrupted_path
            corruption_meta = {
                "type": corruption.value,
                "severity": severity_value
            }
        else:
            corruption_meta = None
        
        # Create entry
        entry = {
            "floorplan_id": fp.id,
            "type": plan_type,
            "subtype": adv_type if adv_type else "n/a",
            "adversarial_severity": adv_severity.value if adv_severity else "n/a",
            "rendering_style": style_name,
            "corruption": corruption_meta,
            "image_path": str(img_path.relative_to(images_dir.parent)),
            "ground_truth": fp.metadata["mystery_room"]["type"],
            "difficulty": fp.metadata["mystery_room"]["difficulty"],
            "metadata": fp.metadata
        }
        
        entries.append(entry)
    
    return entries


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate FloorplanQA benchmark dataset")
    parser.add_argument("--output", default="data/floorplan_qa_benchmark", help="Output directory")
    parser.add_argument("--count", type=int, default=180, help="Number of floorplans to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    generate_publication_dataset(
        output_dir=args.output,
        n_samples=args.count,
        seed=args.seed
    )
