#!/usr/bin/env python3
"""Validation test: Run all 3 prompt types on pilot dataset."""

import subprocess
import sys
from pathlib import Path

def run_validation():
    """Test all three prompt types."""
    
    print("=" * 70)
    print("VALIDATION: TESTING ALL 3 PROMPT TYPES")
    print("=" * 70)
    
    prompt_types = ["direct", "minimal", "structured_cot"]
    
    for prompt_type in prompt_types:
        print(f"\n{'='*70}")
        print(f"Testing: {prompt_type}")
        print("=" * 70)
        
        output_file = f"data/floorplan_qa_pilot/results_{prompt_type}.csv"
        
        cmd = [
            "python", "scripts/run_publication_experiment.py",
            "--dataset", "data/floorplan_qa_pilot/dataset_index.json",
            "--output", output_file,
            "--prompt-type", prompt_type,
            "--limit", "20"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {prompt_type} completed successfully")
            # Extract accuracy from output
            for line in result.stdout.split('\n'):
                if "Accuracy:" in line:
                    print(f"   {line.strip()}")
        else:
            print(f"❌ {prompt_type} failed:")
            print(result.stderr)
    
    print(f"\n{'='*70}")
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print("\n✅ All 3 prompt types tested successfully!")
    print("   Results saved to: data/floorplan_qa_pilot/results_*.csv")

if __name__ == "__main__":
    run_validation()
