"""Space partitioning algorithm for generating room layouts."""

import random
from typing import List

from ..core.geometry import Rectangle
from .parameters import (
    MIN_PARTITION_AREA,
    MIN_PARTITION_RATIO,
    MAX_PARTITION_RATIO,
    MIN_ASPECT_RATIO,
    MAX_ASPECT_RATIO,
)


def partition_space(
    bounds: Rectangle,
    target_count: int,
    rng: random.Random,
    min_area: float = MIN_PARTITION_AREA,
    depth: int = 0,
    max_depth: int = 10
) -> list[Rectangle]:
    """
    Recursively partition a rectangular space into smaller rectangles.

    Uses a binary space partitioning (BSP) approach with constraints to
    generate realistic room layouts.

    Args:
        bounds: The rectangular space to partition
        target_count: Desired number of partitions
        rng: Random number generator for reproducibility
        min_area: Minimum area for a partition
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        List of rectangles representing room candidates
    """
    # Base cases
    if depth >= max_depth:
        return [bounds]

    if bounds.area < min_area * 2:
        return [bounds]

    # If we only need one room, return the current bounds
    if target_count <= 1:
        return [bounds]

    # Decide whether to split horizontally or vertically
    # Prefer splitting the longer dimension
    aspect_ratio = bounds.width / bounds.height

    if aspect_ratio > 1.5:
        # Wide rectangle - prefer vertical split
        split_vertically = rng.random() < 0.7
    elif aspect_ratio < 0.67:
        # Tall rectangle - prefer horizontal split
        split_vertically = rng.random() < 0.3
    else:
        # Roughly square - random choice
        split_vertically = rng.random() < 0.5

    # Calculate split position
    if split_vertically:
        min_split = bounds.width * MIN_PARTITION_RATIO
        max_split = bounds.width * MAX_PARTITION_RATIO
        split_pos = rng.uniform(min_split, max_split)

        rect1 = Rectangle(
            x=bounds.x,
            y=bounds.y,
            width=split_pos,
            height=bounds.height
        )
        rect2 = Rectangle(
            x=bounds.x + split_pos,
            y=bounds.y,
            width=bounds.width - split_pos,
            height=bounds.height
        )
    else:
        # Horizontal split
        min_split = bounds.height * MIN_PARTITION_RATIO
        max_split = bounds.height * MAX_PARTITION_RATIO
        split_pos = rng.uniform(min_split, max_split)

        rect1 = Rectangle(
            x=bounds.x,
            y=bounds.y,
            width=bounds.width,
            height=split_pos
        )
        rect2 = Rectangle(
            x=bounds.x,
            y=bounds.y + split_pos,
            width=bounds.width,
            height=bounds.height - split_pos
        )

    # Validate split results
    if rect1.area < min_area or rect2.area < min_area:
        return [bounds]

    # Check aspect ratios
    aspect1 = rect1.width / rect1.height
    aspect2 = rect2.width / rect2.height

    if (aspect1 < MIN_ASPECT_RATIO or aspect1 > MAX_ASPECT_RATIO or
        aspect2 < MIN_ASPECT_RATIO or aspect2 > MAX_ASPECT_RATIO):
        # Bad aspect ratios, don't split
        return [bounds]

    # Distribute target count between the two partitions
    # Roughly proportional to their areas, with some randomness
    area_ratio = rect1.area / (rect1.area + rect2.area)
    count1 = max(1, int(target_count * area_ratio))
    count2 = max(1, target_count - count1)

    # Add some randomness to the distribution
    if rng.random() < 0.3 and count1 > 1 and count2 > 1:
        if rng.random() < 0.5:
            count1 -= 1
            count2 += 1
        else:
            count1 += 1
            count2 -= 1

    # Recursively partition each side
    partitions1 = partition_space(rect1, count1, rng, min_area, depth + 1, max_depth)
    partitions2 = partition_space(rect2, count2, rng, min_area, depth + 1, max_depth)

    return partitions1 + partitions2


def create_bounding_box(
    target_area: float,
    rng: random.Random,
    preferred_aspect_ratio: float = 1.3
) -> Rectangle:
    """
    Create an initial bounding box for the floorplan.

    Args:
        target_area: Desired total area in square meters
        rng: Random number generator
        preferred_aspect_ratio: Preferred width/height ratio

    Returns:
        Rectangle representing the bounding box
    """
    # Add some variation to the aspect ratio
    aspect_ratio = preferred_aspect_ratio * rng.uniform(0.8, 1.2)

    # Calculate dimensions
    # area = width * height
    # aspect_ratio = width / height
    # => width = aspect_ratio * height
    # => area = aspect_ratio * height^2
    # => height = sqrt(area / aspect_ratio)

    height = (target_area / aspect_ratio) ** 0.5
    width = aspect_ratio * height

    return Rectangle(x=0, y=0, width=width, height=height)


def refine_partitions(
    partitions: list[Rectangle],
    target_area: float,
    rng: random.Random
) -> list[Rectangle]:
    """
    Refine partitions to better match target area and improve layout.

    Args:
        partitions: Initial list of partitions
        target_area: Target total area
        rng: Random number generator

    Returns:
        Refined list of partitions
    """
    total_area = sum(p.area for p in partitions)

    # If total area is too different from target, scale all partitions
    if abs(total_area - target_area) / target_area > 0.15:
        scale_factor = (target_area / total_area) ** 0.5
        partitions = [
            Rectangle(
                x=p.x * scale_factor,
                y=p.y * scale_factor,
                width=p.width * scale_factor,
                height=p.height * scale_factor
            )
            for p in partitions
        ]

    # Remove partitions that are too small
    min_allowed_area = MIN_PARTITION_AREA * 0.8
    partitions = [p for p in partitions if p.area >= min_allowed_area]

    # Sort by y, then x for consistent ordering
    partitions.sort(key=lambda p: (p.y, p.x))

    return partitions


def generate_room_rectangles(
    target_area: float,
    room_count: int,
    seed: int
) -> list[Rectangle]:
    """
    Generate a list of room rectangles using space partitioning.

    Args:
        target_area: Target total area in square meters
        room_count: Desired number of rooms
        seed: Random seed for reproducibility

    Returns:
        List of rectangles representing rooms
    """
    rng = random.Random(seed)

    # Create initial bounding box
    bounds = create_bounding_box(target_area, rng)

    # Partition the space
    partitions = partition_space(
        bounds=bounds,
        target_count=room_count,
        rng=rng
    )

    # Refine partitions
    partitions = refine_partitions(partitions, target_area, rng)

    # If we got too many or too few partitions, retry with adjusted parameters
    if len(partitions) < room_count * 0.7 or len(partitions) > room_count * 1.3:
        # Adjust and retry once
        adjusted_count = room_count
        if len(partitions) < room_count:
            adjusted_count = int(room_count * 1.2)
        else:
            adjusted_count = int(room_count * 0.8)

        partitions = partition_space(
            bounds=bounds,
            target_count=adjusted_count,
            rng=rng
        )
        partitions = refine_partitions(partitions, target_area, rng)

    return partitions
