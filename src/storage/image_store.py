"""Storage for rendered floorplan images."""

import os
from pathlib import Path
from typing import Optional


def get_image_path(floorplan_id: str, directory: str) -> str:
    """
    Get the standard image path for a floorplan.

    Args:
        floorplan_id: ID of the floorplan
        directory: Directory for images

    Returns:
        Full path to the image file
    """
    filename = f"{floorplan_id}.png"
    return os.path.join(directory, filename)


def save_image_path(floorplan_id: str, directory: str) -> str:
    """
    Get the path where an image should be saved and ensure directory exists.

    Args:
        floorplan_id: ID of the floorplan
        directory: Directory for images

    Returns:
        Full path to save the image
    """
    # Ensure directory exists
    Path(directory).mkdir(parents=True, exist_ok=True)

    return get_image_path(floorplan_id, directory)


def image_exists(floorplan_id: str, directory: str) -> bool:
    """
    Check if an image exists for a floorplan.

    Args:
        floorplan_id: ID of the floorplan
        directory: Directory for images

    Returns:
        True if image exists
    """
    path = get_image_path(floorplan_id, directory)
    return os.path.exists(path)


def delete_image(floorplan_id: str, directory: str) -> bool:
    """
    Delete an image file.

    Args:
        floorplan_id: ID of the floorplan
        directory: Directory for images

    Returns:
        True if deleted, False if not found
    """
    path = get_image_path(floorplan_id, directory)

    if os.path.exists(path):
        os.remove(path)
        return True

    return False


def list_images(directory: str) -> list[str]:
    """
    List all image files in a directory.

    Args:
        directory: Directory containing images

    Returns:
        List of image filenames
    """
    if not os.path.exists(directory):
        return []

    return [f for f in os.listdir(directory) if f.endswith('.png')]


def count_images(directory: str) -> int:
    """
    Count the number of images in a directory.

    Args:
        directory: Directory to count images in

    Returns:
        Number of PNG files
    """
    return len(list_images(directory))
