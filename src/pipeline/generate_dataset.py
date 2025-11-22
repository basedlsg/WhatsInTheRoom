"""Dataset generation pipeline for creating synthetic floorplans."""

import argparse
import os
import random
from typing import List
from tqdm import tqdm

from ..core.types import RegionType, SizeCategory
from ..core.models import Floorplan
from ..generation.generator import generate_floorplan, validate_floorplan
from ..rendering.image_renderer import render_floorplan
from ..storage.floorplan_store import save_floorplan
from ..storage.image_store import save_image_path


def parse_regions(region_str: str) -> List[RegionType]:
    """Parse comma-separated region string."""
    if region_str.lower() == 'all':
        return list(RegionType)

    regions = []
    for r in region_str.split(','):
        r = r.strip().upper()
        try:
            regions.append(RegionType[r])
        except KeyError:
            print(f"Warning: Unknown region '{r}', skipping")

    return regions


def parse_sizes(size_str: str) -> List[SizeCategory]:
    """Parse comma-separated size string."""
    if size_str.lower() == 'all':
        return list(SizeCategory)

    sizes = []
    for s in size_str.split(','):
        s = s.strip().upper()
        try:
            sizes.append(SizeCategory[s])
        except KeyError:
            print(f"Warning: Unknown size '{s}', skipping")

    return sizes


def generate_stratified_dataset(
    count: int,
    regions: List[RegionType],
    sizes: List[SizeCategory],
    start_seed: int = 0,
    floorplan_dir: str = "data/floorplans",
    image_dir: str = "data/images"
) -> List[Floorplan]:
    """
    Generate a stratified dataset of floorplans.

    Args:
        count: Total number of floorplans to generate
        regions: List of regions to sample from
        sizes: List of sizes to sample from
        start_seed: Starting seed value
        floorplan_dir: Directory to save floorplan metadata
        image_dir: Directory to save rendered images

    Returns:
        List of generated floorplans
    """
    # Create stratification plan
    combinations = [(r, s) for r in regions for s in sizes]
    per_combination = max(1, count // len(combinations))
    remainder = count % len(combinations)

    print(f"Generating {count} floorplans:")
    print(f"  Regions: {[r.value for r in regions]}")
    print(f"  Sizes: {[s.value for s in sizes]}")
    print(f"  ~{per_combination} per combination")
    print()

    floorplans = []
    seed = start_seed
    failed_count = 0

    with tqdm(total=count, desc="Generating floorplans") as pbar:
        for i, (region, size) in enumerate(combinations):
            # Add one extra to some combinations to handle remainder
            target = per_combination + (1 if i < remainder else 0)

            for _ in range(target):
                try:
                    # Generate floorplan
                    floorplan = generate_floorplan(
                        seed=seed,
                        region=region,
                        size_category=size
                    )

                    # Validate
                    is_valid, errors = validate_floorplan(floorplan)
                    if not is_valid:
                        print(f"\nWarning: Generated invalid floorplan (seed {seed}): {errors}")
                        failed_count += 1
                        seed += 1
                        continue

                    # Save metadata
                    save_floorplan(floorplan, floorplan_dir)

                    # Render and save image
                    image_path = save_image_path(floorplan.id, image_dir)
                    render_floorplan(floorplan, image_path)

                    floorplans.append(floorplan)
                    seed += 1
                    pbar.update(1)

                except Exception as e:
                    print(f"\nError generating floorplan (seed {seed}): {e}")
                    failed_count += 1
                    seed += 1

    print(f"\nGeneration complete:")
    print(f"  Successfully generated: {len(floorplans)}")
    print(f"  Failed: {failed_count}")
    print(f"  Floorplans saved to: {floorplan_dir}")
    print(f"  Images saved to: {image_dir}")

    return floorplans


def main():
    """Main entry point for dataset generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic floorplan dataset"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of floorplans to generate"
    )
    parser.add_argument(
        "--regions",
        type=str,
        default="US_SUBURB,MODERN_URBAN",
        help="Comma-separated list of regions (or 'all')"
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default="SMALL,MEDIUM,LARGE",
        help="Comma-separated list of sizes (or 'all')"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Starting seed value"
    )
    parser.add_argument(
        "--floorplan-dir",
        type=str,
        default="data/floorplans",
        help="Directory to save floorplan metadata"
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default="data/images",
        help="Directory to save rendered images"
    )

    args = parser.parse_args()

    # Parse regions and sizes
    regions = parse_regions(args.regions)
    sizes = parse_sizes(args.sizes)

    if not regions:
        print("Error: No valid regions specified")
        return

    if not sizes:
        print("Error: No valid sizes specified")
        return

    # Generate dataset
    generate_stratified_dataset(
        count=args.count,
        regions=regions,
        sizes=sizes,
        start_seed=args.seed,
        floorplan_dir=args.floorplan_dir,
        image_dir=args.image_dir
    )


if __name__ == "__main__":
    main()
