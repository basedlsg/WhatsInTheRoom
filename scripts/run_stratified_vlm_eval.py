"""
Run stratified VLM evaluation on FloorplanQA v1 dataset.

Uses stratified sampling to ensure balanced representation across difficulty levels.
Includes longer delays to respect API rate limits.
"""

import json
import argparse
from pathlib import Path
from tqdm import tqdm
import time
import random
from typing import List, Dict, Any
from collections import Counter

from src.inference.vlm_client import create_vlm_client


def create_prompt(prompt_type: str = "structured_cot") -> str:
    """Create prompt for mystery room identification."""
    if prompt_type == "direct":
        return """Look at this floorplan. One room is unlabeled. What type of room is it?

Answer with just the room type: bedroom, bathroom, kitchen, living_room, or office."""
    
    elif prompt_type == "minimal":
        return """Analyze this floorplan. One room is not labeled.

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
    """Extract room type from VLM response."""
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


def stratified_sample(data: List[Dict], n_samples: int, random_seed: int = 42) -> List[Dict]:
    """
    Perform stratified sampling by difficulty level.
    
    Args:
        data: Full dataset
        n_samples: Target number of samples
        random_seed: Random seed for reproducibility
        
    Returns:
        Stratified sample
    """
    rng = random.Random(random_seed)
    
    # Group by difficulty
    by_difficulty = {}
    for entry in data:
        diff = entry.get("difficulty", "unknown")
        if diff not in by_difficulty:
            by_difficulty[diff] = []
        by_difficulty[diff].append(entry)
    
    # Calculate samples per difficulty (proportional)
    total = len(data)
    samples_per_diff = {}
    for diff, items in by_difficulty.items():
        proportion = len(items) / total
        samples_per_diff[diff] = int(n_samples * proportion)
    
    # Adjust to ensure we get exactly n_samples
    current_total = sum(samples_per_diff.values())
    if current_total < n_samples:
        # Add extras to largest group
        largest = max(by_difficulty.keys(), key=lambda d: len(by_difficulty[d]))
        samples_per_diff[largest] += (n_samples - current_total)
    
    # Sample from each difficulty
    sampled = []
    for diff, target_count in samples_per_diff.items():
        available = by_difficulty[diff]
        if len(available) <= target_count:
            sampled.extend(available)
        else:
            sampled.extend(rng.sample(available, target_count))
    
    # Shuffle final sample
    rng.shuffle(sampled)
    
    print("Stratified sampling:")
    for diff, count in sorted(samples_per_diff.items()):
        print(f"  {diff:8s}: {count} samples")
    
    return sampled


def evaluate_vlm_stratified(
    client_type: str = "nvidia",
    dataset_dir: Path = Path("data/floorplan_qa_v1"),
    output_path: Path = Path("results/vlm_stratified.json"),
    prompt_type: str = "structured_cot",
    n_samples: int = 400,
    split: str = "clean",
    delay: float = 6.0,
    random_seed: int = 42
):
    """
    Run stratified VLM evaluation.
    
    Args:
        client_type: "gemini" or "nvidia"
        dataset_dir: Path to dataset
        output_path: Where to save results
        prompt_type: "direct", "minimal", or "structured_cot"
        n_samples: Number of samples to evaluate
        split: Which split to evaluate
        delay: Seconds to wait between requests (to avoid rate limits)
        random_seed: Random seed for sampling
    """
    print(f"\n{'='*70}")
    print(f"FloorplanQA Stratified VLM Evaluation ({client_type.upper()})")
    print(f"{'='*70}\n")
    
    # Load dataset
    with open(dataset_dir / "dataset_index.json") as f:
        data = json.load(f)
    
    # Filter by split
    if split != "all":
        data = [entry for entry in data if entry["split"] == split]
    
    print(f"Full dataset: {len(data)} samples")
    print(f"Target sample size: {n_samples}")
    print(f"Delay between requests: {delay}s")
    print(f"Estimated time: {n_samples * delay / 60:.1f} minutes\n")
    
    # Stratified sampling
    sampled_data = stratified_sample(data, n_samples, random_seed)
    
    print(f"\nEvaluating {len(sampled_data)} samples")
    print(f"Prompt type: {prompt_type}")
    print(f"Provider: {client_type}\n")
    
    # Create VLM client
    client = create_vlm_client(client_type)
    
    # Valid room types
    valid_types = ["bedroom", "bathroom", "kitchen", "living_room", "office"]
    
    # Run evaluation
    results = []
    correct = 0
    errors = 0
    
    for i, entry in enumerate(tqdm(sampled_data, desc="Evaluating")):
        # Get image path
        image_path = Path(entry["image_path"])
        if not image_path.is_absolute():
            image_path = dataset_dir.parent / image_path
        
        # Create prompt
        prompt = create_prompt(prompt_type)
        
        # Query VLM
        try:
            response = client.query(str(image_path), prompt)
            prediction = parse_response(response["response"], valid_types)
            
            # Check correctness
            actual = entry["ground_truth"]
            is_correct = prediction == actual
            if is_correct:
                correct += 1
            
            # Store result
            results.append({
                "floorplan_id": entry["floorplan_id"],
                "split": entry["split"],
                "difficulty": entry["difficulty"],
                "ground_truth": actual,
                "prediction": prediction,
                "correct": is_correct,
                "raw_response": response["response"],
                "confidence": response.get("confidence"),
                "region": entry["region"],
                "adversarial_strategy": entry.get("subtype", "n/a"),
                "corruption_type": entry.get("corruption_type", "none")
            })
            
            # Delay to respect rate limits
            if i < len(sampled_data) - 1:  # Don't delay after last request
                time.sleep(delay)
            
        except Exception as e:
            errors += 1
            print(f"\nError on {entry['floorplan_id']}: {e}")
            results.append({
                "floorplan_id": entry["floorplan_id"],
                "split": entry["split"],
                "difficulty": entry["difficulty"],
                "ground_truth": entry["ground_truth"],
                "prediction": "error",
                "correct": False,
                "error": str(e)
            })
            
            # Still delay even on error
            if i < len(sampled_data) - 1:
                time.sleep(delay)
    
    # Calculate metrics
    successful = len(results) - errors
    if successful > 0:
        accuracy = correct / successful
    else:
        accuracy = 0.0
    
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Total samples: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Errors: {errors}")
    print(f"\nOverall Accuracy: {accuracy:.1%} ({correct}/{successful})")
    
    # Per-difficulty accuracy
    per_diff_correct = Counter()
    per_diff_total = Counter()
    
    for r in results:
        if r.get("difficulty") and r.get("prediction") != "error":
            per_diff_total[r["difficulty"]] += 1
            if r["correct"]:
                per_diff_correct[r["difficulty"]] += 1
    
    print("\nPer-Difficulty Accuracy:")
    for diff in ["easy", "medium", "hard"]:
        if diff in per_diff_total:
            acc = per_diff_correct[diff] / per_diff_total[diff]
            print(f"  {diff:8s}: {acc:.1%} ({per_diff_correct[diff]}/{per_diff_total[diff]})")
    
    # Per-room-type accuracy
    per_room_correct = Counter()
    per_room_total = Counter()
    
    for r in results:
        if r.get("prediction") != "error":
            room = r["ground_truth"]
            per_room_total[room] += 1
            if r["correct"]:
                per_room_correct[room] += 1
    
    print("\nPer-Room-Type Accuracy:")
    for room in sorted(per_room_total.keys()):
        acc = per_room_correct[room] / per_room_total[room]
        print(f"  {room:15s}: {acc:.1%} ({per_room_correct[room]}/{per_room_total[room]})")
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "provider": client_type,
        "prompt_type": prompt_type,
        "split": split,
        "sampling": "stratified",
        "n_samples": len(results),
        "successful": successful,
        "errors": errors,
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
        "per_room_type": {
            room: {
                "correct": per_room_correct[room],
                "total": per_room_total[room],
                "accuracy": per_room_correct[room] / per_room_total[room]
            }
            for room in per_room_total
        },
        "predictions": results
    }
    
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Results saved to {output_path}")
    print(f"\nEstimated cost: ~${len(results) * 0.01:.2f} USD")


def main():
    parser = argparse.ArgumentParser(description="Run stratified VLM evaluation")
    parser.add_argument("--provider", choices=["gemini", "nvidia", "vertex", "meta", "huggingface"], default="nvidia")
    parser.add_argument("--dataset", type=str, default="data/floorplan_qa_v1")
    parser.add_argument("--output", type=str, default="results/vlm_stratified.json")
    parser.add_argument("--prompt", choices=["direct", "minimal", "structured_cot"], default="structured_cot")
    parser.add_argument("--n-samples", type=int, default=400, help="Number of samples to evaluate")
    parser.add_argument("--split", type=str, default="clean", help="Split to evaluate")
    parser.add_argument("--delay", type=float, default=6.0, help="Seconds between requests")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    
    args = parser.parse_args()
    
    evaluate_vlm_stratified(
        client_type=args.provider,
        dataset_dir=Path(args.dataset),
        output_path=Path(args.output),
        prompt_type=args.prompt,
        n_samples=args.n_samples,
        split=args.split,
        delay=args.delay,
        random_seed=args.seed
    )


if __name__ == "__main__":
    main()
