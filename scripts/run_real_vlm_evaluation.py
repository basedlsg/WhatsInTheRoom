"""
Run real VLM evaluation on FloorplanQA v1 dataset.

Uses actual API calls (Gemini or NVIDIA NIM).
"""

import json
import argparse
from pathlib import Path
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import time
from typing import List, Dict, Any

from src.inference.vlm_client import create_vlm_client


def create_prompt(prompt_type: str = "structured_cot") -> str:
    """Create prompt for mystery room identification."""
    if prompt_type == "direct":
        return """Look at this floorplan. One room is unlabeled. What type of room is it?

Answer with just the room type: bedroom, bathroom, kitchen, living_room, or office."""
    
    elif prompt_type == "minimal":
        return"""Analyze this floorplan. One room is not labeled.

Based on its size, location, and connections, what type of room is it?

Choose from: bedroom, bathroom, kitchen, living_room, office

Answer:"""
    
    else:  # structured_cot
        return """You are analyzing a residential floorplan. One room is unlabeled (the "mystery room").

Task: Identify the mystery room type.

Consider:
- Size and proportions
- Location in the layout  
- Adjacent rooms (connections via doors)
- Typical residential patterns

Valid room types: bedroom, bathroom, kitchen, living_room, office

Provide your answer as just the room type."""


def parse_response(response_text: str, valid_types: List[str]) -> str:
    """
    Extract room type from VLM response.
    
    Args:
        response_text: Raw VLM response
        valid_types: List of valid room types
        
    Returns:
        Predicted room type (or "unknown" if can't parse)
    """
    response_lower = response_text.lower().strip()
    
    # Direct match
    for room_type in valid_types:
        if room_type in response_lower:
            return room_type
    
    # Fuzzy matches
    if "bed" in response_lower:
        return "bedroom"
    if "bath" in response_lower:
        return "bathroom"
    if "kitchen" in response_lower or "cook" in response_lower:
        return "kitchen"
    if "living" in response_lower or "lounge" in response_lower:
        return "living_room"
    if "office" in response_lower or "study" in response_lower or "work" in response_lower:
        return "office"
    
    return "unknown"


def evaluate_vlm(
    client_type: str = "nvidia",
    dataset_dir: Path = Path("data/floorplan_qa_v1"),
    output_path: Path = Path("results/vlm_evaluation.json"),
    prompt_type: str = "structured_cot",
    max_samples: int = None,
    split: str = "clean"
):
    """
    Run VLM evaluation on dataset.
    
    Args:
        client_type: "gemini" or "nvidia"
        dataset_dir: Path to dataset
        output_path: Where to save results
        prompt_type: "direct", "minimal", or "structured_cot"
        max_samples: Limit number of samples (None = all)
        split: Which split to evaluate ("clean", "adversarial", "corruption", or "all")
    """
    print(f"\n{'='*70}")
    print(f"FloorplanQA Real VLM Evaluation ({client_type.upper()})")
    print(f"{'='*70}\n")
    
    # Load dataset
    with open(dataset_dir / "dataset_index.json") as f:
        data = json.load(f)
    
    # Filter by split
    if split != "all":
        target_splits = [split]
        if split == "clean":
            target_splits.extend(["normal"])
        data = [entry for entry in data if entry.get("type", entry.get("split")) in target_splits]
    
    # Limit samples if requested using stratified sampling
    if max_samples and max_samples < len(data):
        import random
        rng = random.Random(42)
        # Group data for stratification
        groups = {}
        for entry in data:
            # For adversarial, try to balance the confusion strategy (subtype). Else balance room type.
            group_key = entry.get("subtype", "unknown") if split == "adversarial" else entry.get("ground_truth", "unknown")
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(entry)
            
        # Shuffle within groups
        for key in groups:
            rng.seed(42)  # Consistent sampling per group
            rng.shuffle(groups[key])
            
        sampled_data = []
        samples_per_group = max_samples // max(1, len(groups))
        remainder = max_samples % max(1, len(groups))
        
        for key, items in groups.items():
            take = min(samples_per_group + (1 if remainder > 0 else 0), len(items))
            sampled_data.extend(items[:take])
            if remainder > 0:
                remainder -= 1
                
        # If we didn't hit max_samples (e.g. some groups too small), backfill randomly
        if len(sampled_data) < max_samples:
            remaining = [x for x in data if x not in sampled_data]
            rng.shuffle(remaining)
            sampled_data.extend(remaining[:max_samples - len(sampled_data)])
            
        # Final shuffle
        rng.shuffle(sampled_data)
        data = sampled_data
    
    print(f"Evaluating {len(data)} samples from '{split}' split")
    print(f"Prompt type: {prompt_type}")
    print(f"Provider: {client_type}\n")
    
    # Create VLM client
    client = create_vlm_client(client_type)
    
    # Valid room types
    valid_types = ["bedroom", "bathroom", "kitchen", "living_room", "office"]
    
    # Run evaluation
    results = []
    correct = 0
    
    import concurrent.futures

    def evaluate_entry(entry):
        # Get image path
        image_path = Path(entry["image_path"])
        if not image_path.is_absolute():
            if str(image_path).startswith("images/"):
                image_path = dataset_dir / image_path
            else:
                image_path = dataset_dir.parent / image_path
        
        prompt = create_prompt(prompt_type)
        
        # Query VLM with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.query(str(image_path), prompt)
                prediction = parse_response(response["response"], valid_types)
                
                # Check correctness
                actual = entry["ground_truth"]
                is_correct = prediction == actual
                
                res = {
                    "floorplan_id": entry["floorplan_id"],
                    "split": entry.get("type", entry.get("split", split)),
                    "difficulty": entry["difficulty"],
                    "ground_truth": actual,
                    "prediction": prediction,
                    "correct": is_correct,
                    "raw_response": response["response"],
                    "confidence": response.get("confidence"),
                    "region": entry.get("region", "unknown"),
                    "adversarial_strategy": entry.get("subtype", "n/a"),
                    "corruption_type": entry.get("corruption_type", "none")
                }
                
                # Rate limiting (avoid overwhelming API)
                sleep_time = 15.0 if client_type == "gemini" else 0.5
                time.sleep(sleep_time)
                return res
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(10.0)
                else:
                    return {
                        "floorplan_id": entry["floorplan_id"],
                        "split": entry.get("type", entry.get("split", split)),
                        "difficulty": entry["difficulty"],
                        "ground_truth": entry["ground_truth"],
                        "prediction": "error",
                        "correct": False,
                        "error": str(e)
                    }

    max_workers = 1 if client_type == "gemini" else 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(evaluate_entry, entry): entry for entry in data}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(data), desc="Evaluating"):
            res = future.result()
            results.append(res)
            if res.get("correct", False):
                correct += 1
    
    # Calculate accuracy
    accuracy = correct / len(results) if results else 0.0
    
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Overall Accuracy: {accuracy:.1%} ({correct}/{len(results)})")
    
    # Per-difficulty accuracy
    from collections import Counter
    per_diff_correct = Counter()
    per_diff_total = Counter()
    
    for r in results:
        if r.get("difficulty"):
            per_diff_total[r["difficulty"]] += 1
            if r["correct"]:
                per_diff_correct[r["difficulty"]] += 1
    
    print("\nPer-Difficulty Accuracy:")
    for diff in ["easy", "medium", "hard"]:
        if diff in per_diff_total:
            acc = per_diff_correct[diff] / per_diff_total[diff]
            print(f"  {diff:8s}: {acc:.1%} ({per_diff_correct[diff]}/{per_diff_total[diff]})")
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "provider": client_type,
        "prompt_type": prompt_type,
        "split": split,
        "total_samples": len(results),
        "correct": correct,
        "accuracy": accuracy,
        "per_difficulty": {
            diff: {
                "correct": per_diff_correct[diff],
                "total": per_diff_total[diff],
                "accuracy": per_diff_correct[diff] / per_diff_total[diff]
            }
            for diff in per_diff_total
        },
        "predictions": results
    }
    
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Results saved to {output_path}")
    print(f"\nCost estimate: ~${len(results) * 0.01:.2f} USD")


def main():
    parser = argparse.ArgumentParser(description="Run real VLM evaluation")
    parser.add_argument("--provider", choices=["gemini", "nvidia", "vertex"], default="nvidia",)
    parser.add_argument("--dataset", type=str, default="data/floorplan_qa_v1")
    parser.add_argument("--output", type=str, default="results/vlm_evaluation.json")
    parser.add_argument("--prompt", choices=["direct", "minimal", "structured_cot"], default="structured_cot")
    parser.add_argument("--max-samples", type=int, default=None, help="Limit evaluation (for testing)")
    parser.add_argument("--split", choices=["clean", "adversarial", "corruption", "all"], default="clean")
    
    args = parser.parse_args()
    
    evaluate_vlm(
        client_type=args.provider,
        dataset_dir=Path(args.dataset),
        output_path=Path(args.output),
        prompt_type=args.prompt,
        max_samples=args.max_samples,
        split=args.split
    )


if __name__ == "__main__":
    main()
