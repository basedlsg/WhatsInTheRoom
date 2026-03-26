import os
import json
import time
from pathlib import Path
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.inference.vlm_client import create_vlm_client

PROMPTS = {
    "baseline": """You are looking at a floorplan where rooms are labeled with letters (Room A, Room B, etc.). One room is completely unlabeled. Target the unlabeled room.
What type of room is the unlabeled room?
Respond in JSON format:
{
  "room_type": "your prediction",
  "reasoning": "brief explanation"
}""",

    "spatial": """You are looking at an anonymized floorplan. Focus on the unlabeled room.
Before naming the room, list all of its walls, doors, and which other rooms it connects to.
Respond in JSON format:
{
  "spatial_analysis": "list walls and adjacencies",
  "room_type": "your prediction",
  "reasoning": "brief explanation"
}""",

    "rules": """You are analyzing an architectural floorplan. Focus on the unlabeled room.
CRITICAL RULES:
1. Do not use furniture icons to guess. Look strictly at wall adjacencies.
2. If the room has an open wall adjoining a living area, it is highly likely a kitchen.
Respond in JSON format:
{
  "room_type": "your prediction",
  "reasoning": "brief explanation"
}""",

    "exclusion": """You are analyzing a floorplan. Identify the unlabeled room.
IMPORTANT: You are strictly forbidden from predicting 'bedroom', 'bathroom', or 'living_room'.
Respond in JSON format:
{
  "room_type": "your prediction",
  "reasoning": "brief explanation"
}""",

    "contrastive": """You are analyzing a floorplan. Identify the unlabeled room.
Rate the probability (1-10) that this room is a 'kitchen', and the probability it is an 'office'. 
Then state the final highest probability room_type.
Respond in JSON format:
{
  "kitchen_prob": 8,
  "office_prob": 2,
  "room_type": "your prediction",
  "reasoning": "brief explanation"
}"""
}

def run_ablation():
    client = create_vlm_client("nvidia")
    dataset_path = Path("data/kitchen_ablation/dataset.json")
    
    with open(dataset_path) as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} anonymized kitchen floorplans.")
    results_matrix = {cond: {"correct": 0, "total": 0, "accuracy": 0.0} for cond in PROMPTS.keys()}
    
    # We will test a subset (e.g. 20 samples) across all 5 conditions to respect time & rate limits
    sample_subset = data[:20]
    out_file = Path("results/kitchen_ablation_matrix.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    for condition_name, prompt in PROMPTS.items():
        print(f"\n--- Testing Condition: {condition_name.upper()} ---")
        correct = 0
        total = len(sample_subset)
        
        for entry in tqdm(sample_subset, desc=condition_name):
            img_path = Path("data/kitchen_ablation") / entry["image_path"]
            
            try:
                res = client.query(str(img_path), prompt)
                predicted = res.get("parsed_json", {}).get("room_type", "unknown").lower()
                
                # Loose matching
                if "kitchen" in predicted:
                    correct += 1
            except Exception as e:
                print(f"Error on {entry['floorplan_id']}: {e}")
                
            time.sleep(0.5)
            
        acc = (correct / total) * 100 if total > 0 else 0
        results_matrix[condition_name] = {"correct": correct, "total": total, "accuracy": acc}
        print(f"{condition_name.upper()} Accuracy: {acc:.1f}% ({correct}/{total})")
        
        # Incremental save
        with open(out_file, "w") as f:
            json.dump(results_matrix, f, indent=2)

    print("\n--- FINAL ABLATION MATRIX ---")
    for cond, stats in results_matrix.items():
        print(f"{cond.upper():12s} : {stats['accuracy']:.1f}%")

if __name__ == "__main__":
    run_ablation()
