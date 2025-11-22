"""
Minimal experiment driver - runs a tiny end-to-end experiment.

Usage:
    python scripts/run_mini_experiment.py

This will:
1. Generate 10 synthetic floorplans
2. Render them to images
3. If NVIDIA_API_KEY is set, run inference
4. Print a human-readable summary
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan, validate_floorplan
from src.rendering.image_renderer import render_floorplan
from src.storage.floorplan_store import save_floorplan
from src.storage.image_store import save_image_path
from src.storage.results_store import save_predictions_csv, load_predictions_csv
from src.inference.nim_client import NIMClient
from src.inference.prompts import create_mystery_room_prompt
from collections import Counter


def run_mini_experiment():
    """Run a minimal end-to-end experiment."""

    # Configuration
    NUM_FLOORPLANS = 10
    REGIONS = [RegionType.US_SUBURB, RegionType.MODERN_URBAN]
    SIZES = [SizeCategory.SMALL, SizeCategory.MEDIUM]
    OUTPUT_DIR = "data/mini_experiment"

    print("=" * 70)
    print("MINI EXPERIMENT RUNNER")
    print("=" * 70)
    print()

    # Create output directories
    floorplan_dir = os.path.join(OUTPUT_DIR, "floorplans")
    image_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(floorplan_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Step 1: Generate floorplans
    print(f"[1/3] Generating {NUM_FLOORPLANS} synthetic floorplans...")
    floorplans = []
    seed = 1000

    for i in range(NUM_FLOORPLANS):
        region = REGIONS[i % len(REGIONS)]
        size = SIZES[i % len(SIZES)]

        try:
            floorplan = generate_floorplan(
                seed=seed + i,
                region=region,
                size_category=size
            )

            # Validate
            is_valid, errors = validate_floorplan(floorplan)
            if not is_valid:
                print(f"  ⚠️  Skipped invalid floorplan (seed {seed + i}): {errors[0]}")
                continue

            # Save
            save_floorplan(floorplan, floorplan_dir)
            floorplans.append(floorplan)

        except Exception as e:
            print(f"  ⚠️  Error generating floorplan (seed {seed + i}): {e}")

    print(f"  ✅ Generated {len(floorplans)} valid floorplans")
    print()

    # Step 2: Render images
    print(f"[2/3] Rendering floorplans to images...")
    for floorplan in floorplans:
        try:
            image_path = save_image_path(floorplan.id, image_dir)
            render_floorplan(floorplan, image_path)
        except Exception as e:
            print(f"  ⚠️  Error rendering {floorplan.id}: {e}")

    print(f"  ✅ Rendered {len(floorplans)} images")
    print()

    # Step 3: Run inference (if API key is set)
    has_api_key = bool(os.getenv("NVIDIA_API_KEY"))

    if not has_api_key:
        print("[3/3] NVIDIA_API_KEY not found; skipping model inference.")
        print("      You can still inspect the generated floorplans locally.")
        print()
        print("      To run inference, set your API key:")
        print("      export NVIDIA_API_KEY='your-key-here'")
        print()
    else:
        print(f"[3/3] Running inference with NVIDIA NIM...")
        predictions = []

        try:
            client = NIMClient()
            print(f"      Using model: {client.model_name}")

            for i, floorplan in enumerate(floorplans, 1):
                try:
                    print(f"      Processing {i}/{len(floorplans)}...", end="\r")

                    image_path = os.path.join(image_dir, f"{floorplan.id}.png")
                    prompt = create_mystery_room_prompt(
                        region=floorplan.region,
                        size_category=floorplan.size_category,
                        include_metadata=True
                    )

                    prediction = client.predict_room_type(
                        image_path=image_path,
                        prompt=prompt,
                        floorplan_id=floorplan.id
                    )

                    # Add ground truth to metadata
                    mystery_room = floorplan.mystery_room
                    if mystery_room:
                        prediction.metadata['true_room_type'] = mystery_room.room_type.value
                        prediction.metadata['region'] = floorplan.region.value
                        prediction.metadata['size_category'] = floorplan.size_category.value

                    predictions.append(prediction)

                except Exception as e:
                    print(f"\n      ⚠️  Error predicting {floorplan.id}: {e}")

            print(f"      ✅ Completed {len(predictions)} predictions")

            # Save predictions
            if predictions:
                results_path = os.path.join(OUTPUT_DIR, "predictions.csv")
                save_predictions_csv(predictions, results_path)
                print(f"      Saved predictions to: {results_path}")

        except Exception as e:
            print(f"      ❌ Error initializing NIM client: {e}")
            predictions = []

        print()

    # Print summary
    print("=" * 70)
    print("EXPERIMENT SUMMARY")
    print("=" * 70)
    print()

    print(f"Generated: {len(floorplans)} floorplans")
    print(f"Output directory: {OUTPUT_DIR}/")
    print()

    # Region distribution
    region_counts = Counter(fp.region.value for fp in floorplans)
    print("Regions:")
    for region, count in region_counts.items():
        print(f"  {region}: {count}")
    print()

    # Size distribution
    size_counts = Counter(fp.size_category.value for fp in floorplans)
    print("Sizes:")
    for size, count in size_counts.items():
        print(f"  {size}: {count}")
    print()

    # Mystery room types
    mystery_types = Counter(fp.mystery_room.room_type.value for fp in floorplans if fp.mystery_room)
    print("Mystery room types (ground truth):")
    for room_type, count in mystery_types.most_common():
        print(f"  {room_type}: {count}")
    print()

    # Model predictions (if available)
    if has_api_key and predictions:
        predicted_types = Counter(p.predicted_room_type for p in predictions)
        print("Model predictions:")
        for room_type, count in predicted_types.most_common():
            print(f"  {room_type}: {count}")
        print()

        # Quick accuracy
        correct = sum(1 for p in predictions
                     if p.predicted_room_type.lower().replace(' ', '_') ==
                        p.metadata.get('true_room_type', '').lower().replace(' ', '_'))
        accuracy = correct / len(predictions) if predictions else 0
        print(f"Accuracy: {accuracy:.1%} ({correct}/{len(predictions)})")
        print()

    # Next steps
    print("=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print()
    print("1. View images:")
    print(f"   ls {image_dir}/")
    print()
    print("2. Inspect a specific floorplan:")
    if floorplans:
        sample_id = floorplans[0].id
        print(f"   python scripts/inspect_sample.py --house-id {sample_id}")
    print()
    print("3. View all floorplan IDs:")
    print(f"   ls {floorplan_dir}/ | head -5")
    print()
    print("=" * 70)


if __name__ == "__main__":
    run_mini_experiment()
