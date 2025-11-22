"""Storage and retrieval for floorplan metadata."""

import json
import os
from pathlib import Path
from typing import Optional, List

from ..core.models import Floorplan


def save_floorplan(floorplan: Floorplan, directory: str) -> str:
    """
    Save a floorplan to JSON file.

    Args:
        floorplan: Floorplan to save
        directory: Directory to save to

    Returns:
        Path to the saved file
    """
    # Ensure directory exists
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Create filename from floorplan ID
    filename = f"{floorplan.id}.json"
    filepath = os.path.join(directory, filename)

    # Convert to dictionary and save
    data = floorplan.to_dict()

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_floorplan(filepath: str) -> Floorplan:
    """
    Load a floorplan from JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        Loaded Floorplan object
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return Floorplan.from_dict(data)


def load_all_floorplans(directory: str) -> List[Floorplan]:
    """
    Load all floorplans from a directory.

    Args:
        directory: Directory containing floorplan JSON files

    Returns:
        List of loaded Floorplan objects
    """
    floorplans = []

    if not os.path.exists(directory):
        return floorplans

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                floorplan = load_floorplan(filepath)
                floorplans.append(floorplan)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

    return floorplans


def get_floorplan_by_id(floorplan_id: str, directory: str) -> Optional[Floorplan]:
    """
    Load a specific floorplan by ID.

    Args:
        floorplan_id: ID of the floorplan
        directory: Directory containing floorplan JSON files

    Returns:
        Floorplan object or None if not found
    """
    filepath = os.path.join(directory, f"{floorplan_id}.json")

    if not os.path.exists(filepath):
        return None

    return load_floorplan(filepath)


def delete_floorplan(floorplan_id: str, directory: str) -> bool:
    """
    Delete a floorplan file.

    Args:
        floorplan_id: ID of the floorplan to delete
        directory: Directory containing floorplan JSON files

    Returns:
        True if deleted, False if not found
    """
    filepath = os.path.join(directory, f"{floorplan_id}.json")

    if os.path.exists(filepath):
        os.remove(filepath)
        return True

    return False


def count_floorplans(directory: str) -> int:
    """
    Count the number of floorplan files in a directory.

    Args:
        directory: Directory to count files in

    Returns:
        Number of JSON files
    """
    if not os.path.exists(directory):
        return 0

    return len([f for f in os.listdir(directory) if f.endswith('.json')])
