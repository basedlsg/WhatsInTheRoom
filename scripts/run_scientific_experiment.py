
import sys
import os
import json
import argparse
import random
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.inference.nim_client import NIMClient
from src.inference.prompts import (
    create_critique_prompt,
    create_counterfactual_prompt,
    create_mystery_room_prompt,
    create_chain_of_thought_prompt
)
from src.core.models import ModelPrediction

class MockNIMClient:
    """Mock client for testing without API key."""
    def __init__(self, model_name="mock-model"):
        self.model_name = model_name
        
    def predict_room_type(self, image_path, prompt, floorplan_id):
        # Simulate processing time
        import time
        time.sleep(0.01) # Faster for large dataset
        
        # Return a mock prediction
        return ModelPrediction(
            floorplan_id=floorplan_id,
            model_name=self.model_name,
            predicted_room_type="bedroom",
            confidence=0.85,
            reasoning="This is a mock prediction. The room is large and has a window.",
            timestamp=datetime.now(),
            raw_response={"mock": True},
            metadata={"is_mock": True}
        )

def run_experiment(args):
    print("=" * 70)
    print("SCIENTIFIC EXPERIMENT RUNNER (ENHANCED)")
    print("=" * 70)
    
    # Load dataset index
    # Default to large dataset, fallback to small if not found
    dataset_path = args.dataset or "data/scientific_dataset_large/dataset_index.json"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}, trying small dataset...")
        dataset_path = "data/scientific_dataset/dataset_index.json"
        
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        print("Run scripts/generate_large_dataset.py first.")
        return
        
    with open(dataset_path, "r") as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} samples from dataset: {dataset_path}")
    
    # Initialize client
    api_key = os.getenv("NVIDIA_API_KEY")
    use_mock = args.mock or not api_key or api_key == "placeholder_key"
    
    if use_mock:
        print("⚠️  Using MOCK client (no valid API key found or --mock requested)")
        client = MockNIMClient()
    else:
        print("✅ Using REAL NVIDIA NIM client")
        client = NIMClient()
        
    results = []
    
    # Limit samples if requested for pilot
    samples_to_run = dataset[:args.limit] if args.limit else dataset
    
    for i, sample in enumerate(samples_to_run):
        print(f"\nProcessing sample {i+1}/{len(samples_to_run)}: {sample['id']} ({sample['type']} - {sample.get('subtype', 'n/a')})")
        
        floorplan_id = sample['id']
        ground_truth = sample['ground_truth']
        region = RegionType(sample.get('region', 'modern_urban'))
        size_cat = SizeCategory(sample.get('size', 'medium'))
        
        # Iterate over all available styles in the sample
        for style, image_path in sample['images'].items():
            if not os.path.exists(image_path):
                print(f"  ⚠️  Image not found: {image_path}")
                continue
                
            # 1. Standard Prediction (Mystery Room)
            prompt_mystery = create_mystery_room_prompt(
                region=region,
                size_category=size_cat
            )
            
            print(f"  [{style}] Running Mystery Room Prediction...")
            pred_mystery = client.predict_room_type(
                image_path=image_path,
                prompt=prompt_mystery,
                floorplan_id=floorplan_id
            )
            
            # 2. Chain of Thought (NEW)
            prompt_cot = create_chain_of_thought_prompt(
                region=region,
                size_category=size_cat
            )
            
            print(f"  [{style}] Running Chain-of-Thought...")
            pred_cot = client.predict_room_type(
                image_path=image_path,
                prompt=prompt_cot,
                floorplan_id=floorplan_id
            )
            
            # 3. Critique
            prompt_critique = create_critique_prompt(
                region=region,
                size_category=size_cat
            )
            
            print(f"  [{style}] Running Critique...")
            pred_critique = client.predict_room_type(
                image_path=image_path,
                prompt=prompt_critique,
                floorplan_id=floorplan_id
            )
            
            # 4. Counterfactual
            # Pick a distractor (e.g., if GT is bedroom, ask why not kitchen)
            distractor = "kitchen" if ground_truth != "kitchen" else "bedroom"
            prompt_counterfactual = create_counterfactual_prompt(
                target_room_type=ground_truth,
                alternative_room_type=distractor
            )
            
            print(f"  [{style}] Running Counterfactual...")
            pred_counterfactual = client.predict_room_type(
                image_path=image_path,
                prompt=prompt_counterfactual,
                floorplan_id=floorplan_id
            )
            
            # Store results
            results.append({
                "floorplan_id": floorplan_id,
                "type": sample['type'],
                "subtype": sample.get('subtype', 'n/a'),
                "ground_truth": ground_truth,
                "style": style,
                "mystery_pred": pred_mystery.predicted_room_type,
                "mystery_reasoning": pred_mystery.reasoning,
                "cot_pred": pred_cot.predicted_room_type,
                "cot_reasoning": pred_cot.reasoning,
                "critique_response": pred_critique.reasoning,
                "counterfactual_response": pred_counterfactual.reasoning
            })
            
    # Save results
    output_file = args.output or "data/scientific_dataset_large/experiment_results.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"\n✅ Experiment completed. Results saved to {output_file}")
    
    # Print summary
    print("\nSummary:")
    print(df.groupby(['type', 'subtype', 'style']).size())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run scientific experiment")
    parser.add_argument("--mock", action="store_true", help="Force use of mock client")
    parser.add_argument("--dataset", type=str, help="Path to dataset index")
    parser.add_argument("--output", type=str, help="Path to output CSV")
    parser.add_argument("--limit", type=int, help="Limit number of samples to run")
    args = parser.parse_args()
    
    run_experiment(args)
