"""Room type assignment logic for generated partitions."""

import random
import uuid
from typing import List

from ..core.geometry import Rectangle
from ..core.types import RoomType, RegionType
from ..core.models import Room
from .constraints import (
    get_room_types_for_region,
    should_have_window,
    validate_room_dimensions,
)
from .parameters import MYSTERY_ROOM_WEIGHTS, ROOM_AREA_RANGES


def assign_room_types(
    rectangles: list[Rectangle],
    region: RegionType,
    room_types: list[RoomType],
    rng: random.Random
) -> list[Room]:
    """
    Assign room types to rectangles based on size and constraints.

    Args:
        rectangles: List of partitioned rectangles
        region: Regional style
        room_types: List of room types to assign
        rng: Random number generator

    Returns:
        List of Room objects with assigned types
    """
    # Sort rectangles by area (largest first)
    sorted_rects = sorted(rectangles, key=lambda r: r.area, reverse=True)

    # Sort room types by typical size (largest first)
    def get_typical_area(room_type: RoomType) -> float:
        area_range = ROOM_AREA_RANGES.get(room_type, (5, 10))
        return sum(area_range) / 2

    sorted_types = sorted(room_types, key=get_typical_area, reverse=True)

    # Create assignment mapping with some flexibility
    rooms: list[Room] = []
    used_types = []

    # First pass: assign types that closely match area requirements
    for i, rect in enumerate(sorted_rects):
        if i < len(sorted_types):
            room_type = sorted_types[i]
        else:
            # More rectangles than types - reuse types
            # Prefer bedroom, closet, bathroom for duplicates
            duplicatable = [t for t in sorted_types if t in [
                RoomType.BEDROOM, RoomType.CLOSET, RoomType.BATHROOM,
                RoomType.STORAGE, RoomType.OFFICE
            ]]
            if duplicatable:
                room_type = rng.choice(duplicatable)
            else:
                room_type = rng.choice(sorted_types)

        # Validate dimensions
        if not validate_room_dimensions(room_type, rect.width, rect.height):
            # Try to find a better match
            for alternative_type in sorted_types:
                if validate_room_dimensions(alternative_type, rect.width, rect.height):
                    room_type = alternative_type
                    break

        # Determine if room should have window
        has_window = should_have_window(room_type, region, rng)

        room = Room(
            id=str(uuid.uuid4()),
            room_type=room_type,
            bounds=rect,
            has_window=has_window,
            is_mystery=False
        )

        rooms.append(room)
        used_types.append(room_type)

    return rooms


def select_mystery_room(rooms: list[Room], rng: random.Random) -> str:
    """
    Select which room should be the mystery (unlabeled) room.

    Prefers ambiguous room types like closet, office, storage.
    Avoids selecting the only instance of a critical room type.

    Args:
        rooms: List of all rooms in the floorplan
        rng: Random number generator

    Returns:
        ID of the room to be marked as mystery
    """
    # Count occurrences of each room type
    type_counts = {}
    for room in rooms:
        room_type = room.room_type
        type_counts[room_type] = type_counts.get(room_type, 0) + 1

    # Filter candidates: rooms that aren't the only one of their type
    candidates = []
    weights = []

    for room in rooms:
        room_type = room.room_type

        # Don't select if it's the only one of its type
        if type_counts[room_type] == 1:
            # Exception: allow if it's a highly ambiguous type
            if room_type not in [RoomType.CLOSET, RoomType.OFFICE, RoomType.STORAGE,
                                RoomType.GUEST_BEDROOM, RoomType.PANTRY]:
                continue

        # Get weight for this room type
        weight = MYSTERY_ROOM_WEIGHTS.get(room_type, 0.5)

        # Prefer rooms that are not too large or too small
        # Medium-sized rooms are more ambiguous
        area_factor = 1.0
        if room.area < 4:  # Very small
            area_factor = 0.7
        elif room.area > 25:  # Very large
            area_factor = 0.6

        final_weight = weight * area_factor

        if final_weight > 0:
            candidates.append(room)
            weights.append(final_weight)

    # If no suitable candidates (shouldn't happen), just pick a random room
    if not candidates:
        return rng.choice(rooms).id

    # Select based on weights
    mystery_room = rng.choices(candidates, weights=weights, k=1)[0]
    return mystery_room.id


def optimize_room_assignment(
    rooms: list[Room],
    region: RegionType,
    rng: random.Random
) -> list[Room]:
    """
    Optimize room assignments based on spatial relationships and constraints.

    This is a post-processing step to improve the realism of the layout.

    Args:
        rooms: Initial list of rooms
        region: Regional style
        rng: Random number generator

    Returns:
        Optimized list of rooms
    """
    # Sort rooms by position (top to bottom, left to right)
    rooms.sort(key=lambda r: (r.bounds.y, r.bounds.x))

    # Simple optimization: ensure living room and kitchen are not isolated
    # Find rooms by type
    living_rooms = [r for r in rooms if r.room_type == RoomType.LIVING_ROOM]
    kitchens = [r for r in rooms if r.room_type == RoomType.KITCHEN]

    # If both exist, prefer them to be near each other
    # This is handled better by door placement, so we'll keep this simple

    return rooms
