"""Aggregation utilities for analyzing prediction results."""

import pandas as pd
from typing import List, Dict, Any
from collections import Counter

from ..core.models import ModelPrediction, Floorplan
from ..storage.results_store import load_predictions, create_results_dataframe
from ..storage.floorplan_store import load_all_floorplans


def calculate_accuracy(predictions: List[ModelPrediction]) -> float:
    """
    Calculate overall prediction accuracy.

    Args:
        predictions: List of predictions with ground truth

    Returns:
        Accuracy ratio (0-1)
    """
    correct = 0
    total = 0

    for pred in predictions:
        true_type = pred.metadata.get('true_room_type')
        if true_type:
            total += 1
            pred_norm = pred.predicted_room_type.lower().replace(' ', '_')
            true_norm = true_type.lower().replace(' ', '_')

            if pred_norm == true_norm:
                correct += 1

    return correct / total if total > 0 else 0.0


def calculate_accuracy_by_region(
    predictions: List[ModelPrediction]
) -> Dict[str, float]:
    """
    Calculate accuracy grouped by region.

    Args:
        predictions: List of predictions

    Returns:
        Dictionary mapping region to accuracy
    """
    by_region = {}

    for pred in predictions:
        region = pred.metadata.get('region')
        if not region:
            continue

        if region not in by_region:
            by_region[region] = {'correct': 0, 'total': 0}

        true_type = pred.metadata.get('true_room_type')
        if true_type:
            by_region[region]['total'] += 1

            pred_norm = pred.predicted_room_type.lower().replace(' ', '_')
            true_norm = true_type.lower().replace(' ', '_')

            if pred_norm == true_norm:
                by_region[region]['correct'] += 1

    # Calculate ratios
    accuracies = {}
    for region, counts in by_region.items():
        if counts['total'] > 0:
            accuracies[region] = counts['correct'] / counts['total']

    return accuracies


def calculate_accuracy_by_size(
    predictions: List[ModelPrediction]
) -> Dict[str, float]:
    """
    Calculate accuracy grouped by size category.

    Args:
        predictions: List of predictions

    Returns:
        Dictionary mapping size category to accuracy
    """
    by_size = {}

    for pred in predictions:
        size = pred.metadata.get('size_category')
        if not size:
            continue

        if size not in by_size:
            by_size[size] = {'correct': 0, 'total': 0}

        true_type = pred.metadata.get('true_room_type')
        if true_type:
            by_size[size]['total'] += 1

            pred_norm = pred.predicted_room_type.lower().replace(' ', '_')
            true_norm = true_type.lower().replace(' ', '_')

            if pred_norm == true_norm:
                by_size[size]['correct'] += 1

    # Calculate ratios
    accuracies = {}
    for size, counts in by_size.items():
        if counts['total'] > 0:
            accuracies[size] = counts['correct'] / counts['total']

    return accuracies


def get_confusion_matrix(predictions: List[ModelPrediction]) -> pd.DataFrame:
    """
    Create a confusion matrix of predictions.

    Args:
        predictions: List of predictions

    Returns:
        DataFrame with true types as rows and predicted types as columns
    """
    data = []

    for pred in predictions:
        true_type = pred.metadata.get('true_room_type')
        if true_type:
            data.append({
                'true': true_type,
                'predicted': pred.predicted_room_type
            })

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return pd.crosstab(df['true'], df['predicted'])


def get_prediction_distribution(
    predictions: List[ModelPrediction]
) -> Counter:
    """
    Get the distribution of predicted room types.

    Args:
        predictions: List of predictions

    Returns:
        Counter of predicted room types
    """
    return Counter(pred.predicted_room_type for pred in predictions)


def get_true_distribution(
    predictions: List[ModelPrediction]
) -> Counter:
    """
    Get the distribution of true room types.

    Args:
        predictions: List of predictions

    Returns:
        Counter of true room types
    """
    true_types = []
    for pred in predictions:
        true_type = pred.metadata.get('true_room_type')
        if true_type:
            true_types.append(true_type)

    return Counter(true_types)


def generate_summary_stats(
    predictions_file: str,
    floorplans_dir: str = None
) -> Dict[str, Any]:
    """
    Generate comprehensive summary statistics.

    Args:
        predictions_file: Path to predictions file
        floorplans_dir: Optional path to floorplans directory

    Returns:
        Dictionary of summary statistics
    """
    predictions = load_predictions(predictions_file)

    if not predictions:
        return {'error': 'No predictions found'}

    stats = {
        'total_predictions': len(predictions),
        'overall_accuracy': calculate_accuracy(predictions),
        'accuracy_by_region': calculate_accuracy_by_region(predictions),
        'accuracy_by_size': calculate_accuracy_by_size(predictions),
        'predicted_distribution': dict(get_prediction_distribution(predictions)),
        'true_distribution': dict(get_true_distribution(predictions)),
    }

    return stats


def print_summary(stats: Dict[str, Any]) -> None:
    """
    Print formatted summary statistics.

    Args:
        stats: Statistics dictionary from generate_summary_stats
    """
    print("=" * 60)
    print("PREDICTION SUMMARY")
    print("=" * 60)

    print(f"\nTotal Predictions: {stats['total_predictions']}")
    print(f"Overall Accuracy: {stats['overall_accuracy']:.2%}")

    print("\n--- Accuracy by Region ---")
    for region, acc in sorted(stats['accuracy_by_region'].items()):
        print(f"  {region:30s}: {acc:.2%}")

    print("\n--- Accuracy by Size ---")
    for size, acc in sorted(stats['accuracy_by_size'].items()):
        print(f"  {size:30s}: {acc:.2%}")

    print("\n--- Top Predicted Room Types ---")
    pred_dist = stats['predicted_distribution']
    for room_type, count in sorted(pred_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / stats['total_predictions']
        print(f"  {room_type:30s}: {count:4d} ({pct:.1%})")

    print("\n--- Top True Room Types ---")
    true_dist = stats['true_distribution']
    total_true = sum(true_dist.values())
    for room_type, count in sorted(true_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / total_true if total_true > 0 else 0
        print(f"  {room_type:30s}: {count:4d} ({pct:.1%})")

    print("=" * 60)
