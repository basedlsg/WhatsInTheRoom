"""Metrics calculation for model evaluation."""

from typing import List, Dict
from collections import defaultdict

from ..core.models import ModelPrediction


def calculate_precision_recall_f1(
    predictions: List[ModelPrediction]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate precision, recall, and F1 score for each room type.

    Args:
        predictions: List of predictions with ground truth

    Returns:
        Dictionary mapping room type to metrics
    """
    # Count true positives, false positives, false negatives per class
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    for pred in predictions:
        true_type = pred.metadata.get('true_room_type')
        if not true_type:
            continue

        pred_type = pred.predicted_room_type.lower().replace(' ', '_')
        true_type = true_type.lower().replace(' ', '_')

        if pred_type == true_type:
            tp[true_type] += 1
        else:
            fp[pred_type] += 1
            fn[true_type] += 1

    # Calculate metrics
    metrics = {}

    all_types = set(list(tp.keys()) + list(fp.keys()) + list(fn.keys()))

    for room_type in all_types:
        precision = tp[room_type] / (tp[room_type] + fp[room_type]) if (tp[room_type] + fp[room_type]) > 0 else 0
        recall = tp[room_type] / (tp[room_type] + fn[room_type]) if (tp[room_type] + fn[room_type]) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        metrics[room_type] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': tp[room_type] + fn[room_type]
        }

    return metrics


def print_classification_report(metrics: Dict[str, Dict[str, float]]) -> None:
    """
    Print a classification report similar to sklearn.

    Args:
        metrics: Metrics dictionary from calculate_precision_recall_f1
    """
    print("\n" + "=" * 70)
    print("CLASSIFICATION REPORT")
    print("=" * 70)
    print(f"{'Room Type':<25} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    print("-" * 70)

    # Sort by support (descending)
    sorted_types = sorted(metrics.items(), key=lambda x: x[1]['support'], reverse=True)

    for room_type, scores in sorted_types:
        if scores['support'] > 0:
            print(f"{room_type:<25} {scores['precision']:>10.3f} {scores['recall']:>10.3f} "
                  f"{scores['f1']:>10.3f} {scores['support']:>10d}")

    # Calculate macro averages
    if metrics:
        avg_precision = sum(m['precision'] for m in metrics.values()) / len(metrics)
        avg_recall = sum(m['recall'] for m in metrics.values()) / len(metrics)
        avg_f1 = sum(m['f1'] for m in metrics.values()) / len(metrics)

        print("-" * 70)
        print(f"{'Macro Average':<25} {avg_precision:>10.3f} {avg_recall:>10.3f} {avg_f1:>10.3f}")

    print("=" * 70)
