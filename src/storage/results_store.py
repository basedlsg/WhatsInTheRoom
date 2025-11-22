"""Storage for model predictions and results."""

import os
from pathlib import Path
from typing import List, Optional
import pandas as pd

from ..core.models import ModelPrediction, Floorplan


def save_predictions(
    predictions: List[ModelPrediction],
    filepath: str,
    append: bool = False
) -> None:
    """
    Save predictions to a Parquet file.

    Args:
        predictions: List of predictions to save
        filepath: Path to save the Parquet file
        append: If True, append to existing file
    """
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # Convert predictions to dictionaries
    data = [pred.to_dict() for pred in predictions]

    # Create DataFrame
    df = pd.DataFrame(data)

    # Handle append mode
    if append and os.path.exists(filepath):
        existing_df = pd.read_parquet(filepath)
        df = pd.concat([existing_df, df], ignore_index=True)

    # Save to Parquet
    df.to_parquet(filepath, index=False)


def load_predictions(filepath: str) -> List[ModelPrediction]:
    """
    Load predictions from a Parquet file.

    Args:
        filepath: Path to the Parquet file

    Returns:
        List of ModelPrediction objects
    """
    if not os.path.exists(filepath):
        return []

    df = pd.read_parquet(filepath)

    predictions = []
    for _, row in df.iterrows():
        pred = ModelPrediction.from_dict(row.to_dict())
        predictions.append(pred)

    return predictions


def save_predictions_csv(
    predictions: List[ModelPrediction],
    filepath: str,
    append: bool = False
) -> None:
    """
    Save predictions to a CSV file (alternative to Parquet).

    Args:
        predictions: List of predictions to save
        filepath: Path to save the CSV file
        append: If True, append to existing file
    """
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # Convert predictions to dictionaries
    data = [pred.to_dict() for pred in predictions]

    # Create DataFrame
    df = pd.DataFrame(data)

    # Handle append mode
    if append and os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        df = pd.concat([existing_df, df], ignore_index=True)

    # Save to CSV
    df.to_csv(filepath, index=False)


def load_predictions_csv(filepath: str) -> List[ModelPrediction]:
    """
    Load predictions from a CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        List of ModelPrediction objects
    """
    if not os.path.exists(filepath):
        return []

    df = pd.read_csv(filepath)

    predictions = []
    for _, row in df.iterrows():
        pred = ModelPrediction.from_dict(row.to_dict())
        predictions.append(pred)

    return predictions


def get_predictions_for_floorplan(
    floorplan_id: str,
    filepath: str
) -> List[ModelPrediction]:
    """
    Get all predictions for a specific floorplan.

    Args:
        floorplan_id: ID of the floorplan
        filepath: Path to the predictions file

    Returns:
        List of predictions for this floorplan
    """
    all_predictions = load_predictions(filepath)
    return [p for p in all_predictions if p.floorplan_id == floorplan_id]


def get_predictions_by_model(
    model_name: str,
    filepath: str
) -> List[ModelPrediction]:
    """
    Get all predictions from a specific model.

    Args:
        model_name: Name of the model
        filepath: Path to the predictions file

    Returns:
        List of predictions from this model
    """
    all_predictions = load_predictions(filepath)
    return [p for p in all_predictions if p.model_name == model_name]


def create_results_dataframe(
    predictions: List[ModelPrediction],
    floorplans: Optional[List[Floorplan]] = None
) -> pd.DataFrame:
    """
    Create a pandas DataFrame with predictions and optional floorplan metadata.

    Args:
        predictions: List of predictions
        floorplans: Optional list of floorplans for additional metadata

    Returns:
        DataFrame with predictions and metadata
    """
    # Convert predictions to DataFrame
    pred_data = [pred.to_dict() for pred in predictions]
    df = pd.DataFrame(pred_data)

    # If floorplans provided, join with metadata
    if floorplans:
        floorplan_data = []
        for fp in floorplans:
            mystery_room = fp.mystery_room
            floorplan_data.append({
                'floorplan_id': fp.id,
                'region': fp.region.value,
                'size_category': fp.size_category.value,
                'total_area': fp.total_area,
                'room_count': len(fp.rooms),
                'true_room_type': mystery_room.room_type.value if mystery_room else None,
            })

        fp_df = pd.DataFrame(floorplan_data)
        df = df.merge(fp_df, on='floorplan_id', how='left')

    return df
