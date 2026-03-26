"""
Simple baseline evaluation using only dataset index metadata.

This version works with the existing dataset without needing full floorplan objects.
Evaluates majority class and random baselines only (heuristic needs full data).
"""

import json
import argparse
from pathlib import Path
from collections import Counter
import random
import pandas as pd


def evaluate_majority_class(data, split_name="clean"):
    """Evaluate majority class baseline."""
    # Find most common room type in the data
    room_types = [entry["ground_truth"] for entry in data]
    counter = Counter(room_types)
    most_common = counter.most_common(1)[0][0]
   
    print(f"Majority class: {most_common} ({counter[most_common]/len(room_types):.1%})")
    
    # Evaluate: always predict most common
    correct = sum(1 for entry in data if entry["ground_truth"] == most_common)
    accuracy = correct / len(data)
    
    # Per-class accuracy
    per_class = {}
    for room_type in counter:
        # Majority baseline gets 100% on majority class, 0% on others
        per_class[room_type] = 1.0 if room_type == most_common else 0.0
    
    return {
        "model": "Majority Class",
        "split": split_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": len(data),
        "per_class_accuracy": per_class,
        "majority_class": most_common
    }


def evaluate_random(data, split_name="clean", seed=42):
    """Evaluate random baseline."""
    rng = random.Random(seed)
    
    # Get unique room types
    room_types = list(set(entry["ground_truth"] for entry in data))
    
    # Randomly predict for each sample
    correct = 0
    per_class_correct = Counter()
    per_class_total = Counter()
    
    for entry in data:
        prediction = rng.choice(room_types)
        actual = entry["ground_truth"]
        
        per_class_total[actual] += 1
        if prediction == actual:
            correct += 1
            per_class_correct[actual] += 1
    
    accuracy = correct / len(data)
    
    per_class = {
        room_type: per_class_correct[room_type] / per_class_total[room_type]
        if per_class_total[room_type] > 0 else 0.0
        for room_type in per_class_total
    }
    
    return {
        "model": "Random",
        "split": split_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": len(data),
        "per_class_accuracy": per_class
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate simple baselines")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/floorplan_qa_v1",
        help="Dataset directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/baseline_evaluation",
        help="Output directory for results"
    )
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print("FloorplanQA v1: Simple Baseline Evaluation")
    print(f"{'='*70}\n")
    
    # Load dataset index
    with open(dataset_dir / "dataset_index.json") as f:
        index = json.load(f)
    
    # Evaluate on each split
    splits = ["clean", "adversarial", "corruption"]
    all_results = []
    
    for split in splits:
        split_data = [entry for entry in index if entry["split"] == split]
        
        if not split_data:
            continue
        
        print(f"\n{split.upper()} SET ({len(split_data)} samples)")
        print("-" * 70)
        
        # Majority class
        maj_result = evaluate_majority_class(split_data, split)
        all_results.append(maj_result)
        
        print(f"\nMajority Class Baseline:")
        print(f"  Predicts: {maj_result['majority_class']}")
        print(f"  Accuracy: {maj_result['accuracy']:.1%} ({maj_result['correct']}/{maj_result['total']})")
        
        # Random
        rand_result = evaluate_random(split_data, split)
        all_results.append(rand_result)
        
        print(f"\nRandom Baseline:")
        print(f"  Accuracy: {rand_result['accuracy']:.1%} ({rand_result['correct']}/{rand_result['total']})")
        print(f"  Per-class accuracy:")
        for room_type, acc in sorted(rand_result['per_class_accuracy'].items()):
            print(f"    {room_type:15s}: {acc:.1%}")
    
    # Save summary
    summary = pd.DataFrame([
        {
            "model": r["model"],
            "split": r["split"],
            "accuracy": f"{r['accuracy']:.1%}",
            "correct": r["correct"],
            "total": r["total"]
        }
        for r in all_results
    ])
    
    summary_path = output_dir / "baseline_summary.csv"
    summary.to_csv(summary_path, index=False)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    print(summary.to_string(index=False))
    
    print(f"\n✓ Results saved to {output_dir}/")
    
    # Save detailed results
    with open(output_dir / "baseline_results_detailed.json", "w") as f:
        json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    main()
