#!/usr/bin/env python3
"""
Analyze Human Baseline Study data.

Calculates:
- Accuracy by cohort (Expert vs Non-Expert)
- Accuracy by difficulty and adversarial status
- Confidence-Accuracy calibration
- Comparison with VLM performance (mock data for now)
"""

import json
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
DATA_DIR = "data/human_study"
OUTPUT_DIR = "data/human_study/analysis"
VLM_RESULTS_PATH = "data/floorplan_qa_pilot/results_test.csv"  # Use pilot results for comparison

def load_human_data():
    """Load all JSONL files from data directory."""
    files = glob.glob(f"{DATA_DIR}/*.jsonl")
    all_responses = []
    
    for f in files:
        with open(f, 'r') as file:
            for line in file:
                try:
                    resp = json.loads(line)
                    # Infer correctness if not present (for real data)
                    if "is_correct_simulated" not in resp:
                         # In real usage, we'd check against ground truth here
                         # For simulation, we used the simulated flag
                         pass
                    
                    # Normalize fields
                    resp["is_correct"] = resp.get("is_correct_simulated", False)
                    # If real data, we need to compute is_correct from prediction vs ground_truth
                    if "ground_truth" in resp and "prediction" in resp:
                        resp["is_correct"] = (resp["prediction"].lower() == resp["ground_truth"].lower())
                        
                    all_responses.append(resp)
                except json.JSONDecodeError:
                    continue
                    
    return pd.DataFrame(all_responses)

def analyze_human_performance():
    """Run analysis pipeline."""
    df = load_human_data()
    if df.empty:
        print("No data found.")
        return

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"Loaded {len(df)} responses from {df['participant_id'].nunique()} participants.")
    
    # 1. Overall Accuracy by Cohort
    print("\n--- Accuracy by Cohort ---")
    cohort_acc = df.groupby("participant_type")["is_correct"].agg(['mean', 'count', 'std'])
    # Compute CI
    cohort_acc['ci'] = 1.96 * (cohort_acc['std'] / np.sqrt(cohort_acc['count'])) # Approximation for binary
    print(cohort_acc)
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x="participant_type", y="is_correct", data=df, capsize=.1)
    plt.title("Human Accuracy: Experts vs Non-Experts")
    plt.ylabel("Accuracy")
    plt.savefig(f"{OUTPUT_DIR}/accuracy_by_cohort.png")
    plt.close()
    
    # 2. Accuracy by Difficulty
    print("\n--- Accuracy by Difficulty ---")
    diff_acc = df.groupby(["participant_type", "difficulty"])["is_correct"].mean().unstack()
    print(diff_acc)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="difficulty", y="is_correct", hue="participant_type", data=df, order=["easy", "medium", "hard"])
    plt.title("Accuracy by Difficulty Tier")
    plt.ylabel("Accuracy")
    plt.savefig(f"{OUTPUT_DIR}/accuracy_by_difficulty.png")
    plt.close()
    
    # 3. Adversarial Impact
    print("\n--- Adversarial Impact ---")
    adv_acc = df.groupby(["participant_type", "is_adversarial"])["is_correct"].mean().unstack()
    print(adv_acc)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="is_adversarial", y="is_correct", hue="participant_type", data=df)
    plt.title("Impact of Adversarial Layouts")
    plt.ylabel("Accuracy")
    plt.xticks([0, 1], ["Normal", "Adversarial"])
    plt.savefig(f"{OUTPUT_DIR}/accuracy_adversarial.png")
    plt.close()
    
    # 4. Confidence Calibration
    print("\n--- Confidence Calibration ---")
    # Bin confidence into low (1-2), medium (3), high (4-5)
    df['conf_bin'] = pd.cut(df['confidence'], bins=[0, 2, 3, 5], labels=["Low", "Medium", "High"])
    calib = df.groupby(["participant_type", "conf_bin"])["is_correct"].mean().unstack()
    print(calib)
    
    plt.figure(figsize=(10, 6))
    sns.lineplot(x="confidence", y="is_correct", hue="participant_type", data=df, marker="o")
    plt.plot([1, 5], [0.2, 1.0], 'k--', alpha=0.5, label="Perfect Calibration") # Ideal slope
    plt.title("Confidence-Accuracy Calibration")
    plt.ylabel("Accuracy")
    plt.xlabel("Reported Confidence (1-5)")
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/calibration.png")
    plt.close()
    
    # 5. VLM Comparison (Placeholder)
    # In a real run, we'd load VLM results and merge
    print("\n--- VLM Comparison (Simulated) ---")
    # Mock VLM accuracy for comparison plot
    vlm_acc = 0.45 # Placeholder
    
    comparison_data = []
    comparison_data.append({"Agent": "VLM (Zero-shot)", "Accuracy": vlm_acc})
    comparison_data.append({"Agent": "Non-Expert Human", "Accuracy": df[df["participant_type"]=="non_expert"]["is_correct"].mean()})
    comparison_data.append({"Agent": "Expert Human", "Accuracy": df[df["participant_type"]=="expert"]["is_correct"].mean()})
    
    comp_df = pd.DataFrame(comparison_data)
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x="Agent", y="Accuracy", data=comp_df)
    plt.title("Performance Gap: AI vs Humans")
    plt.ylabel("Accuracy")
    plt.axhline(y=vlm_acc, color='r', linestyle='--', alpha=0.5)
    plt.savefig(f"{OUTPUT_DIR}/vlm_human_comparison.png")
    plt.close()
    
    print(f"\nAnalysis complete. Plots saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    analyze_human_performance()
