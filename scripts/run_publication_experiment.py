#!/usr/bin/env python3
"""
Publication-grade experiment runner for FloorplanQA benchmark.

Supports:
- Multiple prompt types (direct, minimal, structured_cot)
- Comprehensive metadata logging
- FloorplanQA dataset format
- Mock and real VLM clients
"""

import json
import os
import sys
import csv
import argparse
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.prompts_v2 import PromptType, get_prompt_for_type
from src.core.types import RegionType, SizeCategory

# Load environment variables
load_dotenv()


class MockVLMClient:
    """Mock VLM client for testing (returns random predictions)."""
    
    def __init__(self):
        import random
        self.rng = random.Random(42)
        self.room_types = ["bedroom", "bathroom", "kitchen", "living_room", "office", "closet"]
    
    def predict(self, image_path: str, prompt: str) -> dict:
        """Mock prediction."""
        import time
        time.sleep(0.01)  # Simulate API latency
        
        return {
            "room_type": self.rng.choice(self.room_types),
            "reasoning": "Mock reasoning from test client",
            "confidence": "medium"
        }


def run_publication_experiment(
    dataset_index_path: str,
    output_csv_path: str,
    prompt_type: PromptType = PromptType.MINIMAL,
    limit: int = None,
    use_real_client: bool = False
):
    """
    Run FloorplanQA benchmark experiment.
    
    Args:
        dataset_index_path: Path to dataset_index.json
        output_csv_path: Where to save results CSV
        prompt_type: Which prompt condition to use
        limit: Optional limit on number of samples
        use_real_client: Whether to use real NVIDIA NIM client
    """
    print("=" * 70)
    print("FLOORPLANQA BENCHMARK EXPERIMENT")
    print("=" * 70)
    print(f"\nDataset: {dataset_index_path}")
    print(f"Prompt type: {prompt_type.value}")
    print(f"Output: {output_csv_path}")
    
    # Load dataset index
    with open(dataset_index_path, 'r') as f:
        dataset = json.load(f)
    
    if limit:
        dataset = dataset[:limit]
        print(f"Limited to: {limit} samples")
    
    print(f"Total samples: {len(dataset)}")
    
    # Initialize VLM client
    if use_real_client and os.getenv("NVIDIA_API_KEY"):
        print("\n✅ Using REAL NVIDIA NIM client")
        from src.inference.nim_client import NIMClient
        client = NIMClient()
    else:
        print("\n⚠️  Using MOCK client (for testing)")
        client = MockVLMClient()
    
    # Prepare output
    output_dir = Path(output_csv_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Process each sample
    for entry in tqdm(dataset, desc="Running Experiment"):
        # Extract metadata
        floorplan_id = entry["floorplan_id"]
        plan_type = entry["type"]
        subtype = entry.get("subtype", "n/a")
        adv_severity = entry.get("adversarial_severity", "n/a")
        rendering_style = entry["rendering_style"]
        corruption = entry.get("corruption")
        ground_truth = entry["ground_truth"]
        difficulty = entry["difficulty"]
        
        # Get region and size from metadata if available
        metadata = entry.get("metadata", {})
        region_str = metadata.get("region", "modern_urban")
        size_str = metadata.get("size_category", "medium")
        
        try:
            region = RegionType(region_str)
            size_cat = SizeCategory(size_str)
        except:
            region = RegionType.MODERN_URBAN
            size_cat = SizeCategory.MEDIUM
        
        # Generate prompt
        prompt = get_prompt_for_type(prompt_type, region, size_cat)
        
        # Get image path
        dataset_dir = Path(dataset_index_path).parent
        image_path = dataset_dir / entry["image_path"]
        
        # Run inference
        try:
            response = client.predict(str(image_path), prompt)
            
            # Extract fields
            predicted_room = response.get("room_type", "unknown")
            reasoning = response.get("reasoning", "")
            confidence = response.get("confidence", "unknown")
            
            # Calculate reasoning length
            reasoning_length = len(reasoning.split()) if reasoning else 0
            
            # Determine correctness
            is_correct = (
                predicted_room.lower().replace(" ", "_") == 
                ground_truth.lower().replace(" ", "_")
            )
            
        except Exception as e:
            print(f"\n⚠️  Error on {floorplan_id}: {e}")
            predicted_room = "error"
            reasoning = str(e)
            confidence = "n/a"
            reasoning_length = 0
            is_correct = False
        
        # Store result
        result = {
            "floorplan_id": floorplan_id,
            "type": plan_type,
            "subtype": subtype,
            "adversarial_severity": adv_severity,
            "rendering_style": rendering_style,
            "corruption_type": corruption["type"] if corruption else "none",
            "corruption_severity": corruption["severity"] if corruption else 0,
            "difficulty": difficulty,
            "prompt_type": prompt_type.value,
            "ground_truth": ground_truth,
            "predicted": predicted_room,
            "reasoning": reasoning,
            "confidence": confidence,
            "reasoning_length": reasoning_length,
            "is_correct": is_correct
        }
        
        results.append(result)
    
    # Save to CSV
    if results:
        fieldnames = results[0].keys()
        with open(output_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    # Print summary
    print(f"\n{'='*70}")
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"\nProcessed: {len(results)} samples")
    
    if results:
        correct = sum(1 for r in results if r["is_correct"])
        accuracy = correct / len(results)
        print(f"Accuracy: {accuracy:.1%} ({correct}/{len(results)})")
        
        # Breakdown by type
        print(f"\nBy type:")
        for t in ["normal", "adversarial"]:
            type_results = [r for r in results if r["type"] == t]
            if type_results:
                type_correct = sum(1 for r in type_results if r["is_correct"])
                type_acc = type_correct / len(type_results)
                print(f"  {t}: {type_acc:.1%} ({type_correct}/{len(type_results)})")
        
        # Breakdown by difficulty
        print(f"\nBy difficulty:")
        for d in ["easy", "medium", "hard"]:
            diff_results = [r for r in results if r["difficulty"] == d]
            if diff_results:
                diff_correct = sum(1 for r in diff_results if r["is_correct"])
                diff_acc = diff_correct / len(diff_results)
                print(f"  {d}: {diff_acc:.1%} ({diff_correct}/{len(diff_results)})")
    
    print(f"\nResults saved to: {output_csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FloorplanQA benchmark experiment")
    parser.add_argument(
        "--dataset",
        default="data/floorplan_qa_benchmark/dataset_index.json",
        help="Path to dataset index JSON"
    )
    parser.add_argument(
        "--output",
        default="data/floorplan_qa_benchmark/results.csv",
        help="Path to output CSV"
    )
    parser.add_argument(
        "--prompt-type",
        choices=["direct", "minimal", "structured_cot"],
        default="minimal",
        help="Which prompting condition to use"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples (for testing)"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real NVIDIA NIM client (requires API key)"
    )
    
    args = parser.parse_args()
    
    # Convert prompt type string to enum
    prompt_type = PromptType(args.prompt_type)
    
    run_publication_experiment(
        dataset_index_path=args.dataset,
        output_csv_path=args.output,
        prompt_type=prompt_type,
        limit=args.limit,
        use_real_client=args.real
    )
