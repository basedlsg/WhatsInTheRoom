#!/usr/bin/env python3
"""
Simulate human participant data for FloorplanQA benchmark.

Generates synthetic responses for two cohorts:
1. Experts (Architects): High accuracy, high confidence calibration
2. Non-Experts (Crowd): Lower accuracy, lower confidence calibration

Used to validate the analysis pipeline before real data collection.
"""

import json
import random
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Configuration
DATA_DIR = "data/human_study"
BENCHMARK_INDEX = "data/floorplan_qa_benchmark/dataset_index.json"
N_EXPERTS = 8
N_NON_EXPERTS = 25
TRIALS_PER_PARTICIPANT = 30

# Performance Profiles (Probability of correct answer)
PROFILES = {
    "expert": {
        "base_accuracy": 0.95,
        "difficulty_penalty": {"easy": 0.0, "medium": 0.05, "hard": 0.15},
        "adversarial_penalty": 0.10,
        "confidence_noise": 0.1,  # Low noise = good calibration
        "reasoning_length_mean": 15,
        "reasoning_vocab": ["spatial", "circulation", "adjacency", "egress", "fenestration", "layout", "zone"]
    },
    "non_expert": {
        "base_accuracy": 0.80,
        "difficulty_penalty": {"easy": 0.05, "medium": 0.20, "hard": 0.40},
        "adversarial_penalty": 0.25,
        "confidence_noise": 0.3,  # High noise = poor calibration
        "reasoning_length_mean": 8,
        "reasoning_vocab": ["looks like", "maybe", "small", "big", "next to", "door", "window"]
    }
}

def load_dataset():
    """Load benchmark dataset."""
    try:
        with open(BENCHMARK_INDEX, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Dataset not found at {BENCHMARK_INDEX}. Using mock data.")
        return []

def simulate_response(entry, profile_name):
    """Generate a single simulated response."""
    profile = PROFILES[profile_name]
    
    # Determine ground truth
    ground_truth = entry.get("ground_truth", "bedroom")
    difficulty = entry.get("difficulty", "medium")
    is_adversarial = entry.get("type") == "adversarial"
    
    # Calculate success probability
    prob = profile["base_accuracy"]
    prob -= profile["difficulty_penalty"].get(difficulty, 0.1)
    if is_adversarial:
        prob -= profile["adversarial_penalty"]
    
    # Clamp probability
    prob = max(0.1, min(0.99, prob))
    
    # Determine correctness
    is_correct = random.random() < prob
    
    if is_correct:
        prediction = ground_truth
    else:
        # Pick a wrong answer
        options = ["bedroom", "bathroom", "kitchen", "living_room", "office", "closet"]
        if ground_truth in options:
            options.remove(ground_truth)
        prediction = random.choice(options)
    
    # Simulate confidence (1-5)
    # Correlated with correctness but with noise
    base_conf = 5 if is_correct else 2
    noise = np.random.normal(0, profile["confidence_noise"] * 5)
    confidence = int(np.clip(base_conf + noise, 1, 5))
    
    # Simulate reasoning
    vocab = profile["reasoning_vocab"]
    length = int(np.random.normal(profile["reasoning_length_mean"], 3))
    length = max(3, length)
    reasoning = " ".join(random.choices(vocab, k=length))
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "reasoning": reasoning,
        "is_correct_simulated": is_correct  # For debugging/verification
    }

def generate_data():
    """Generate synthetic dataset."""
    dataset = load_dataset()
    if not dataset:
        return

    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"Simulating data for {N_EXPERTS} experts and {N_NON_EXPERTS} non-experts...")
    
    participants = []
    
    # Generate Experts
    for i in range(N_EXPERTS):
        participants.append({
            "id": f"expert_{i+1}",
            "type": "expert"
        })
        
    # Generate Non-Experts
    for i in range(N_NON_EXPERTS):
        participants.append({
            "id": f"worker_{i+1}",
            "type": "non_expert"
        })
    
    total_responses = 0
    
    for p in participants:
        p_id = p["id"]
        p_type = p["type"]
        
        # Select random subset of trials
        # In real study, this might be fixed, but random is fine for simulation
        subset = random.sample(dataset, min(len(dataset), TRIALS_PER_PARTICIPANT))
        
        responses = []
        start_time = datetime.now()
        
        for idx, entry in enumerate(subset):
            sim = simulate_response(entry, p_type)
            
            response = {
                "participant_id": p_id,
                "participant_type": p_type,  # Metadata we wouldn't normally have in raw data, but useful here
                "trial_index": idx,
                "floorplan_id": entry["floorplan_id"],
                "prediction": sim["prediction"],
                "confidence": sim["confidence"],
                "reasoning": sim["reasoning"],
                "timestamp": (start_time + timedelta(seconds=idx*30)).isoformat(),
                "ground_truth": entry["ground_truth"], # Store for easy analysis
                "difficulty": entry["difficulty"],
                "is_adversarial": entry["type"] == "adversarial"
            }
            responses.append(response)
            
        # Save to JSONL
        out_file = Path(DATA_DIR) / f"{p_id}.jsonl"
        with open(out_file, 'w') as f:
            for r in responses:
                f.write(json.dumps(r) + "\n")
        
        total_responses += len(responses)
        
    print(f"Successfully generated {total_responses} responses across {len(participants)} participants.")
    print(f"Data saved to {DATA_DIR}")

if __name__ == "__main__":
    generate_data()
