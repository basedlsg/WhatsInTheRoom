#!/usr/bin/env python3
"""
FloorplanQA: Split Manager
Creates deterministic train/dev/test splits with no-leakage guarantees.
"""

import os
import json
import hashlib
import random
from typing import List, Dict, Any, Tuple
from collections import defaultdict


class SplitManager:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
    
    def create_splits(
        self,
        questions: List[dict],
        dev_size: int = 100,
        test_size: int = 500,
        balance_by_type: bool = True
    ) -> Dict[str, List[dict]]:
        """
        Create deterministic splits with no image leakage.
        Images are assigned to splits at the floorplan level.
        """
        
        # Group questions by floorplan
        fp_to_questions = defaultdict(list)
        for q in questions:
            fp_id = q["floorplan_id"]
            fp_to_questions[fp_id].append(q)
        
        # Get unique floorplan IDs
        fp_ids = sorted(fp_to_questions.keys())
        
        # Deterministic shuffle
        self.rng.shuffle(fp_ids)
        
        # Assign floorplans to splits (not questions)
        # This ensures no image leakage
        num_fps = len(fp_ids)
        
        # Calculate floorplan allocation
        # Estimate questions per floorplan
        avg_q_per_fp = len(questions) / num_fps if num_fps > 0 else 1
        
        dev_fps = max(1, int(dev_size / avg_q_per_fp))
        test_fps = max(1, int(test_size / avg_q_per_fp))
        
        dev_fp_ids = set(fp_ids[:dev_fps])
        test_fp_ids = set(fp_ids[dev_fps:dev_fps + test_fps])
        train_fp_ids = set(fp_ids[dev_fps + test_fps:])  # Usually empty for zero-shot
        
        splits = {
            "train": [],
            "dev": [],
            "test": []
        }
        
        for q in questions:
            fp_id = q["floorplan_id"]
            if fp_id in dev_fp_ids:
                splits["dev"].append(q)
            elif fp_id in test_fp_ids:
                splits["test"].append(q)
            else:
                splits["train"].append(q)
        
        # Balance by question type within each split
        if balance_by_type:
            for split_name in ["dev", "test"]:
                splits[split_name] = self._balance_by_type(
                    splits[split_name],
                    dev_size if split_name == "dev" else test_size
                )
        
        return splits
    
    def _balance_by_type(self, questions: List[dict], target_size: int) -> List[dict]:
        """Balance question types in a split."""
        
        # Group by type
        by_type = defaultdict(list)
        for q in questions:
            by_type[q["question_type"]].append(q)
        
        # Calculate per-type target
        num_types = len(by_type)
        per_type = target_size // num_types if num_types > 0 else target_size
        
        balanced = []
        for qt, qs in by_type.items():
            self.rng.shuffle(qs)
            balanced.extend(qs[:per_type])
        
        # Fill remaining slots
        remaining = target_size - len(balanced)
        if remaining > 0:
            all_remaining = [q for qs in by_type.values() for q in qs[per_type:]]
            self.rng.shuffle(all_remaining)
            balanced.extend(all_remaining[:remaining])
        
        return balanced[:target_size]
    
    def verify_no_leakage(self, splits: Dict[str, List[dict]]) -> bool:
        """Verify no image appears in multiple splits."""
        
        split_fps = {}
        for split_name, questions in splits.items():
            fps = set(q["floorplan_id"] for q in questions)
            split_fps[split_name] = fps
        
        # Check overlaps
        for s1 in split_fps:
            for s2 in split_fps:
                if s1 >= s2:
                    continue
                overlap = split_fps[s1] & split_fps[s2]
                if overlap:
                    print(f"LEAKAGE DETECTED: {len(overlap)} floorplans in both {s1} and {s2}")
                    return False
        
        print("✓ No leakage detected")
        return True
    
    def get_stats(self, splits: Dict[str, List[dict]]) -> dict:
        """Get statistics for splits."""
        
        stats = {}
        for split_name, questions in splits.items():
            type_counts = defaultdict(int)
            for q in questions:
                type_counts[q["question_type"]] += 1
            
            stats[split_name] = {
                "total_questions": len(questions),
                "unique_floorplans": len(set(q["floorplan_id"] for q in questions)),
                "by_type": dict(type_counts)
            }
        
        return stats


def create_benchmark_splits(
    questions_path: str,
    output_dir: str,
    dev_size: int = 100,
    test_size: int = 500,
    seed: int = 42
):
    """Create and save benchmark splits."""
    
    with open(questions_path, "r") as f:
        questions = json.load(f)
    
    manager = SplitManager(seed=seed)
    splits = manager.create_splits(
        questions,
        dev_size=dev_size,
        test_size=test_size
    )
    
    # Verify no leakage
    if not manager.verify_no_leakage(splits):
        raise ValueError("Data leakage detected!")
    
    # Save splits
    os.makedirs(output_dir, exist_ok=True)
    
    for split_name, split_questions in splits.items():
        output_path = os.path.join(output_dir, f"{split_name}_v1.json")
        with open(output_path, "w") as f:
            json.dump(split_questions, f, indent=2)
        print(f"Saved {split_name}: {len(split_questions)} questions")
    
    # Save stats
    stats = manager.get_stats(splits)
    stats_path = os.path.join(output_dir, "split_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    print("\n=== Split Statistics ===")
    for split_name, split_stats in stats.items():
        print(f"\n{split_name.upper()}:")
        print(f"  Questions: {split_stats['total_questions']}")
        print(f"  Floorplans: {split_stats['unique_floorplans']}")
        print(f"  By type:")
        for qt, count in split_stats["by_type"].items():
            print(f"    {qt}: {count}")
    
    return splits, stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=str, default="data/generated/questions.json")
    parser.add_argument("--output", type=str, default="data/splits")
    parser.add_argument("--dev", type=int, default=100)
    parser.add_argument("--test", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verify", action="store_true", help="Verify existing splits")
    args = parser.parse_args()
    
    if args.verify:
        # Load and verify existing splits
        manager = SplitManager(args.seed)
        splits = {}
        for split_name in ["train", "dev", "test"]:
            path = os.path.join(args.output, f"{split_name}_v1.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    splits[split_name] = json.load(f)
        
        manager.verify_no_leakage(splits)
        print(manager.get_stats(splits))
    else:
        create_benchmark_splits(
            args.questions,
            args.output,
            args.dev,
            args.test,
            args.seed
        )
