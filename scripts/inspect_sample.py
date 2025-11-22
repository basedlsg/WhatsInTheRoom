"""
Inspection helper - view details of a specific floorplan.

Usage:
    python scripts/inspect_sample.py --house-id <floorplan-id>
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.floorplan_store import load_floorplan
from src.storage.results_store import load_predictions_csv


def inspect_sample(house_id: str, data_dir: str = "data"):
    """Inspect a specific floorplan sample."""

    print("=" * 70)
    print(f"INSPECTING FLOORPLAN: {house_id}")
    print("=" * 70)
    print()

    # Try multiple locations
    possible_dirs = [
        os.path.join(data_dir, "floorplans"),
        os.path.join(data_dir, "mini_experiment", "floorplans"),
        os.path.join(data_dir, "test_local", "floorplans"),
    ]

    floorplan = None
    floorplan_path = None

    for floorplan_dir in possible_dirs:
        try:
            fp_path = os.path.join(floorplan_dir, f"{house_id}.json")
            if os.path.exists(fp_path):
                floorplan = load_floorplan(fp_path)
                floorplan_path = fp_path
                break
        except:
            continue

    if not floorplan:
        print(f"❌ Floorplan {house_id} not found in any data directory.")
        print()
        print("Searched:")
        for d in possible_dirs:
            print(f"  - {d}")
        print()
        print("Try one of these commands to see available IDs:")
        for d in possible_dirs:
            if os.path.exists(d):
                print(f"  ls {d}/")
        return

    print(f"Found: {floorplan_path}")
    print()

    # Basic info
    print("FLOORPLAN METADATA")
    print("-" * 70)
    print(f"ID: {floorplan.id}")
    print(f"Seed: {floorplan.seed}")
    print(f"Region: {floorplan.region.value}")
    print(f"Size: {floorplan.size_category.value}")
    print(f"Total area: {floorplan.total_area:.1f} m²")
    print(f"Rooms: {len(floorplan.rooms)}")
    print(f"Doors: {len(floorplan.doors)}")
    print()

    # Room list
    print("ROOMS")
    print("-" * 70)
    for i, room in enumerate(floorplan.rooms, 1):
        marker = "🔍 MYSTERY ROOM" if room.is_mystery else ""
        window = "🪟" if room.has_window else "  "
        print(f"{i:2d}. {window} {room.room_type.value:20s} ({room.area:5.1f} m²) {marker}")
    print()

    # Mystery room details
    mystery_room = floorplan.mystery_room
    if mystery_room:
        print("MYSTERY ROOM DETAILS")
        print("-" * 70)
        print(f"True type: {mystery_room.room_type.value}")
        print(f"Area: {mystery_room.area:.1f} m²")
        print(f"Dimensions: {mystery_room.bounds.width:.1f}m × {mystery_room.bounds.height:.1f}m")
        print(f"Has window: {'Yes' if mystery_room.has_window else 'No'}")

        # Connected rooms
        adjacent = floorplan.get_adjacent_rooms(mystery_room.id)
        if adjacent:
            print(f"Connected to: {', '.join(r.room_type.value for r in adjacent)}")
        print()

    # Check for predictions
    possible_pred_files = [
        os.path.join(data_dir, "results", "predictions.csv"),
        os.path.join(data_dir, "mini_experiment", "predictions.csv"),
        os.path.join(data_dir, "test_local", "results.parquet"),
        os.path.join(data_dir, "results", "predictions.parquet"),
    ]

    prediction = None
    for pred_file in possible_pred_files:
        if os.path.exists(pred_file):
            try:
                if pred_file.endswith('.csv'):
                    preds = load_predictions_csv(pred_file)
                else:
                    from src.storage.results_store import load_predictions
                    preds = load_predictions(pred_file)

                for p in preds:
                    if p.floorplan_id == house_id:
                        prediction = p
                        break

                if prediction:
                    break
            except:
                continue

    if prediction:
        print("MODEL PREDICTION")
        print("-" * 70)
        print(f"Predicted type: {prediction.predicted_room_type}")
        if mystery_room:
            correct = (prediction.predicted_room_type.lower().replace(' ', '_') ==
                      mystery_room.room_type.value.lower())
            print(f"Correct: {'✅ YES' if correct else '❌ NO'}")
        if prediction.confidence:
            print(f"Confidence: {prediction.confidence:.2%}")
        print(f"\nReasoning:")
        print(f"{prediction.reasoning}")
        print()
    else:
        print("MODEL PREDICTION")
        print("-" * 70)
        print("No prediction found for this floorplan.")
        print()

    # Image paths
    possible_image_dirs = [
        os.path.join(data_dir, "images"),
        os.path.join(data_dir, "mini_experiment", "images"),
        os.path.join(data_dir, "test_local", "images"),
    ]

    image_path = None
    for img_dir in possible_image_dirs:
        img_path = os.path.join(img_dir, f"{house_id}.png")
        if os.path.exists(img_path):
            image_path = img_path
            break

    print("FILES")
    print("-" * 70)
    print(f"Metadata: {floorplan_path}")
    if image_path:
        print(f"Image: {image_path}")
        print()
        print("To view the image:")
        print(f"  open {image_path}")
        print(f"  # or: eog {image_path}")
        print(f"  # or: display {image_path}")
    else:
        print("Image: Not found")
    print()

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Inspect a floorplan sample")
    parser.add_argument(
        "--house-id",
        type=str,
        required=True,
        help="Floorplan ID to inspect"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base data directory (default: data)"
    )

    args = parser.parse_args()
    inspect_sample(args.house_id, args.data_dir)


if __name__ == "__main__":
    main()
