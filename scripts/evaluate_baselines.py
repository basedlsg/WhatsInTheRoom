"""
Evaluate baseline models on FloorplanQA v1 dataset.

Runs all baseline models and compares their performance.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
import pandas as pd

from src.baselines import (
    MajorityClassBaseline,
    RandomBaseline,
    HeuristicBaseline,
    evaluate_baseline
)
from src.core.models import Floorplan


def load_floorplans_from_index(dataset_dir: Path, split: str = "clean") -> list[Floorplan]:
    """Load floorplans from dataset index."""
    index_path = dataset_dir / "dataset_index.json"
    
    with open(index_path) as f:
        index = json.load(f)
    
    # Filter by split
    filtered = [entry for entry in index if entry["split"] == split]
    
    print(f"Loading {len(filtered)} floorplans from '{split}' split...")
    
    # For baselines, we need to reconstruct Floorplan objects from stored data
    # This is a simplified version - we only need mystery room and adjacency
    # Let's load the actual floorplan JSON files if they exist
    
    # For now, create minimal Floorplan objects from metadata
    floorplans = []
    
    # Group by floorplan_id to get unique floorplans
    unique_ids = set(entry["floorplan_id"] for entry in filtered)
    
    for fp_id in unique_ids:
        # Find first entry with this ID
        entry = next(e for e in filtered if e["floorplan_id"] == fp_id)
        
        # Try to load the full floorplan data
        # Assume there's a floorplan_data.json or similar
        # For baseline evaluation, we actually need to generate these on-the-fly
        # or store them separately
        
        # Placeholder: We'll need to store floorplan JSONs alongside images
        # For now, skip and use a different approach
        pass
    
    # Alternative: Load from a separate floorplans.json file
    floorplans_json_path = dataset_dir / "floorplans.json"
    if floorplans_json_path.exists():
        with open(floorplans_json_path) as f:
            floorplan_data = json.load(f)
        
        for fp_dict in floorplan_data:
            if fp_dict.get("split") == split:
                floorplans.append(Floorplan.from_dict(fp_dict))
    else:
        raise FileNotFoundError(
            f"Floorplan data not found. Expected {floorplans_json_path}. "
            "The dataset generation script needs to save full floorplan objects."
        )
    
    return floorplans


def main():
    parser = argparse.ArgumentParser(description="Evaluate baseline models")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/floorplan_qa_v1",
        help="Path to dataset directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/baseline_evaluation.csv",
        help="Output CSV file for results"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="clean",
        choices=["clean", "adversarial", "corruption"],
        help="Dataset split to evaluate on"
    )
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("FloorplanQA Baseline Model Evaluation")
    print(f"{'='*60}\n")
    
    # Load floorplans
    try:
        floorplans = load_floorplans_from_index(dataset_dir, args.split)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nNote: Run scripts/save_floorplan_objects.py first to extract floorplan data.")
        return
    
    # Split into train (for majority class) and test
    # Use first 80% for "training" (just to find majority class)
    train_size = int(0.8 * len(floorplans))
    train_floorplans = floorplans[:train_size]
    test_floorplans = floorplans[train_size:]
    
    print(f"Train set: {len(train_floorplans)} floorplans")
    print(f"Test set: {len(test_floorplans)} floorplans\n")
    
    # Initialize baselines
    baselines = [
        MajorityClassBaseline(),
        RandomBaseline(seed=42),
        HeuristicBaseline()
    ]
    
    # Fit models that need training
    for model in baselines:
        if hasattr(model, 'fit') and model.name == "Majority Class":
            model.fit(train_floorplans)
    
    # Evaluate each baseline
    results = []
    
    for model in baselines:
        print(f"\nEvaluating {model.name}...")
        result = evaluate_baseline(model, test_floorplans, args.split)
        results.append(result)
        
        print(f"  Accuracy: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
        print(f"  Per-class accuracy:")
        for room_type, acc in sorted(result['per_class_accuracy'].items()):
            print(f"    {room_type:15s}: {acc:.1%}")
    
    # Save summary results
    summary_df = pd.DataFrame([
        {
            "model": r["model"],
            "split": r["split"],
            "accuracy": r["accuracy"],
            "correct": r["correct"],
            "total": r["total"]
        }
        for r in results
    ])
    
    summary_df.to_csv(output_path, index=False)
    print(f"\n✓ Results saved to {output_path}")
    
    # Save detailed predictions
    predictions_path = output_path.parent / f"baseline_predictions_{args.split}.json"
    detailed_results = {
        r["model"]: r["predictions"]
        for r in results
    }
    
    with open(predictions_path, "w") as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"✓ Detailed predictions saved to {predictions_path}")
    
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}\n")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
