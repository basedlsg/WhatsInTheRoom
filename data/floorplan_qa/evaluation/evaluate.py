#!/usr/bin/env python3
"""
FloorplanQA: Main Evaluation Script
Reproducible evaluation with confidence intervals.
"""

import os
import json
import time
import argparse
from typing import List, Dict, Any
from collections import defaultdict
import random

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.baselines.vlm_runner import get_vlm_backend, VLMResponse


def load_split(split_path: str) -> List[dict]:
    """Load a split file."""
    with open(split_path, "r") as f:
        return json.load(f)


def evaluate_model(
    model_spec: str,
    questions: List[dict],
    image_base_dir: str,
    prompt_style: str = "structured",
    max_questions: int = None,
    manifest_path: str = None
) -> Dict[str, Any]:
    """Run evaluation on a set of questions."""
    
    # Initialize backend
    kwargs = {}
    if manifest_path:
        kwargs["manifest_path"] = manifest_path
    
    vlm = get_vlm_backend(model_spec, **kwargs)
    
    results = []
    correct = 0
    total = 0
    
    if max_questions:
        questions = questions[:max_questions]
    
    type_correct = defaultdict(int)
    type_total = defaultdict(int)
    
    print(f"\nEvaluating {vlm.name()} with {prompt_style} prompt...")
    print(f"Questions: {len(questions)}")
    
    for i, q in enumerate(questions):
        image_path = os.path.join(image_base_dir, q["image_path"])
        
        # For oracle baseline, pass question data
        if model_spec == "heuristic":
            response = vlm.query(
                image_path=image_path,
                question=q["question_text"],
                choices=q["choices"],
                prompt_style=prompt_style,
                question_data=q
            )
        else:
            response = vlm.query(
                image_path=image_path,
                question=q["question_text"],
                choices=q["choices"],
                prompt_style=prompt_style
            )
        
        response.question_id = q["id"]
        
        is_correct = response.predicted_index == q["correct_index"]
        
        results.append({
            "question_id": q["id"],
            "question_type": q["question_type"],
            "correct_answer": q["correct_answer"],
            "correct_index": q["correct_index"],
            "predicted_answer": response.predicted_answer,
            "predicted_index": response.predicted_index,
            "is_correct": is_correct,
            "latency_ms": response.latency_ms,
            "error": response.error
        })
        
        if not response.error:
            total += 1
            type_total[q["question_type"]] += 1
            
            if is_correct:
                correct += 1
                type_correct[q["question_type"]] += 1
        
        if (i + 1) % 10 == 0:
            acc = correct / total if total > 0 else 0
            print(f"  Progress: {i+1}/{len(questions)} | Accuracy: {acc:.2%}")
    
    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    
    type_accuracy = {}
    for qt in type_total:
        type_accuracy[qt] = type_correct[qt] / type_total[qt] if type_total[qt] > 0 else 0
    
    # Bootstrap confidence interval
    ci_lower, ci_upper = bootstrap_ci(results)
    
    return {
        "model": vlm.name(),
        "prompt_style": prompt_style,
        "accuracy": accuracy,
        "accuracy_ci_95": [ci_lower, ci_upper],
        "correct": correct,
        "total": total,
        "accuracy_by_type": type_accuracy,
        "results": results
    }


def bootstrap_ci(results: List[dict], n_samples: int = 1000, confidence: float = 0.95) -> tuple:
    """Calculate bootstrap confidence interval for accuracy."""
    
    correct_flags = [r["is_correct"] for r in results if r["error"] is None]
    
    if len(correct_flags) < 10:
        return (0.0, 1.0)
    
    rng = random.Random(42)
    accuracies = []
    
    for _ in range(n_samples):
        sample = rng.choices(correct_flags, k=len(correct_flags))
        acc = sum(sample) / len(sample)
        accuracies.append(acc)
    
    accuracies.sort()
    alpha = 1 - confidence
    lower_idx = int(n_samples * alpha / 2)
    upper_idx = int(n_samples * (1 - alpha / 2))
    
    return (accuracies[lower_idx], accuracies[upper_idx])


def print_results(eval_results: Dict[str, Any]):
    """Print formatted evaluation results."""
    
    print("\n" + "=" * 60)
    print(f"Model: {eval_results['model']}")
    print(f"Prompt: {eval_results['prompt_style']}")
    print("=" * 60)
    
    acc = eval_results['accuracy']
    ci = eval_results['accuracy_ci_95']
    print(f"\nOverall Accuracy: {acc:.2%} (95% CI: [{ci[0]:.2%}, {ci[1]:.2%}])")
    print(f"Correct: {eval_results['correct']} / {eval_results['total']}")
    
    print("\nAccuracy by Question Type:")
    for qt, qa in sorted(eval_results['accuracy_by_type'].items()):
        print(f"  {qt}: {qa:.2%}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", type=str, default="data/splits/test_v1.json")
    parser.add_argument("--images", type=str, default="data/generated")
    parser.add_argument("--model", type=str, default="gemini:gemini-1.5-flash")
    parser.add_argument("--prompt", type=str, default="structured", 
                        choices=["minimal", "structured", "cot"])
    parser.add_argument("--max", type=int, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--manifest", type=str, default="data/generated/manifest.json")
    args = parser.parse_args()
    
    questions = load_split(args.split)
    
    results = evaluate_model(
        model_spec=args.model,
        questions=questions,
        image_base_dir=args.images,
        prompt_style=args.prompt,
        max_questions=args.max,
        manifest_path=args.manifest
    )
    
    print_results(results)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
