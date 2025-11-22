"""Visualization utilities for prediction results."""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import pandas as pd
import os
from pathlib import Path
from typing import List, Optional

from ..core.models import ModelPrediction
from ..storage.results_store import load_predictions
from .aggregation import (
    get_confusion_matrix,
    get_prediction_distribution,
    calculate_accuracy_by_region,
    calculate_accuracy_by_size
)


def plot_accuracy_by_region(
    predictions: List[ModelPrediction],
    output_path: str
) -> None:
    """
    Plot accuracy by region as a bar chart.

    Args:
        predictions: List of predictions
        output_path: Path to save the plot
    """
    accuracies = calculate_accuracy_by_region(predictions)

    if not accuracies:
        print("No data for accuracy by region")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    regions = list(accuracies.keys())
    values = [accuracies[r] * 100 for r in regions]

    ax.bar(regions, values, color='steelblue')
    ax.set_xlabel('Region', fontsize=12)
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title('Prediction Accuracy by Region', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')

    # Add value labels on bars
    for i, v in enumerate(values):
        ax.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved accuracy by region plot to {output_path}")


def plot_accuracy_by_size(
    predictions: List[ModelPrediction],
    output_path: str
) -> None:
    """
    Plot accuracy by size category as a bar chart.

    Args:
        predictions: List of predictions
        output_path: Path to save the plot
    """
    accuracies = calculate_accuracy_by_size(predictions)

    if not accuracies:
        print("No data for accuracy by size")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    sizes = list(accuracies.keys())
    values = [accuracies[s] * 100 for s in sizes]

    ax.bar(sizes, values, color='coral')
    ax.set_xlabel('Size Category', fontsize=12)
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title('Prediction Accuracy by Size Category', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)

    # Add value labels on bars
    for i, v in enumerate(values):
        ax.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved accuracy by size plot to {output_path}")


def plot_prediction_distribution(
    predictions: List[ModelPrediction],
    output_path: str,
    top_n: int = 15
) -> None:
    """
    Plot distribution of predicted room types.

    Args:
        predictions: List of predictions
        output_path: Path to save the plot
        top_n: Number of top room types to show
    """
    distribution = get_prediction_distribution(predictions)

    if not distribution:
        print("No prediction data")
        return

    # Get top N
    top_items = distribution.most_common(top_n)
    room_types = [item[0] for item in top_items]
    counts = [item[1] for item in top_items]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.barh(room_types, counts, color='mediumseagreen')
    ax.set_xlabel('Count', fontsize=12)
    ax.set_ylabel('Room Type', fontsize=12)
    ax.set_title(f'Top {top_n} Predicted Room Types', fontsize=14, fontweight='bold')

    # Add value labels
    for i, v in enumerate(counts):
        ax.text(v + 0.5, i, str(v), ha='left', va='center')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved prediction distribution plot to {output_path}")


def plot_confusion_matrix(
    predictions: List[ModelPrediction],
    output_path: str,
    max_categories: int = 15
) -> None:
    """
    Plot confusion matrix heatmap.

    Args:
        predictions: List of predictions
        output_path: Path to save the plot
        max_categories: Maximum number of categories to show
    """
    cm = get_confusion_matrix(predictions)

    if cm.empty:
        print("No data for confusion matrix")
        return

    # Limit to most common categories
    if len(cm) > max_categories:
        # Get most common true types
        row_sums = cm.sum(axis=1).sort_values(ascending=False)
        top_rows = row_sums.head(max_categories).index
        cm = cm.loc[top_rows]

    if len(cm.columns) > max_categories:
        # Get most common predicted types
        col_sums = cm.sum(axis=0).sort_values(ascending=False)
        top_cols = col_sums.head(max_categories).index
        cm = cm[top_cols]

    fig, ax = plt.subplots(figsize=(12, 10))

    # Create heatmap
    im = ax.imshow(cm.values, cmap='Blues', aspect='auto')

    # Set ticks
    ax.set_xticks(range(len(cm.columns)))
    ax.set_yticks(range(len(cm.index)))
    ax.set_xticklabels(cm.columns, rotation=45, ha='right')
    ax.set_yticklabels(cm.index)

    # Add colorbar
    plt.colorbar(im, ax=ax)

    # Add text annotations
    for i in range(len(cm.index)):
        for j in range(len(cm.columns)):
            value = cm.iloc[i, j]
            if value > 0:
                text = ax.text(j, i, int(value),
                             ha="center", va="center",
                             color="white" if value > cm.values.max() / 2 else "black",
                             fontsize=8)

    ax.set_xlabel('Predicted Room Type', fontsize=12)
    ax.set_ylabel('True Room Type', fontsize=12)
    ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    print(f"Saved confusion matrix to {output_path}")


def generate_all_plots(
    predictions_file: str,
    output_dir: str
) -> None:
    """
    Generate all standard plots.

    Args:
        predictions_file: Path to predictions file
        output_dir: Directory to save plots
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load predictions
    print(f"Loading predictions from {predictions_file}...")
    predictions = load_predictions(predictions_file)

    if not predictions:
        print("No predictions found!")
        return

    print(f"Loaded {len(predictions)} predictions")

    # Generate plots
    print("\nGenerating plots...")

    plot_accuracy_by_region(
        predictions,
        os.path.join(output_dir, 'accuracy_by_region.png')
    )

    plot_accuracy_by_size(
        predictions,
        os.path.join(output_dir, 'accuracy_by_size.png')
    )

    plot_prediction_distribution(
        predictions,
        os.path.join(output_dir, 'prediction_distribution.png')
    )

    plot_confusion_matrix(
        predictions,
        os.path.join(output_dir, 'confusion_matrix.png')
    )

    print(f"\nAll plots saved to {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate visualizations")
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/predictions.parquet",
        help="Path to predictions file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/analysis",
        help="Directory to save plots"
    )

    args = parser.parse_args()

    generate_all_plots(args.predictions, args.output_dir)
