"""Room type assignment logic for generated partitions."""

import random
import uuid
from typing import List, Dict, Tuple
from enum import Enum

from ..core.geometry import Rectangle
from ..core.types import RoomType, RegionType
from ..core.models import Room
from .constraints import (
    get_room_types_for_region,
    should_have_window,
    validate_room_dimensions,
)
from .parameters import MYSTERY_ROOM_WEIGHTS, ROOM_AREA_RANGES


# Canonical mystery room types for publication-grade benchmark
CANDIDATE_MYSTERY_TYPES = {
    RoomType.BEDROOM,
    RoomType.BATHROOM,
    RoomType.KITCHEN,
    RoomType.LIVING_ROOM,
    RoomType.OFFICE,
    RoomType.CLOSET
}


class DifficultyTier(Enum):
    """Mystery room difficulty classification."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


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


def compute_room_difficulty_features(room: Room, all_rooms: List[Room]) -> Dict[str, float]:
    """
    Compute difficulty features for a room to classify mystery room difficulty.
    
    Args:
        room: Room to analyze
        all_rooms: All rooms in the floorplan
    
    Returns:
        Dictionary of features
    """
    features = {}
    
    # Area feature
    features['area'] = room.area
    
    # Count features (will be set separately with door/window counts)
    features['has_window'] = 1.0 if room.has_window else 0.0
    
    # Uniqueness of area among all rooms
    all_areas = [r.area for r in all_rooms]
    area_distances = [abs(room.area - a) for a in all_areas if a != room.area]
    features['area_uniqueness'] = min(area_distances) if area_distances else 10.0
    
    # Type count (how many of this type exist)
    type_count = sum(1 for r in all_rooms if r.room_type == room.room_type)
    features['type_count'] = type_count
    
    return features


def classify_room_difficulty(
    room: Room,
    all_rooms: List[Room],
    door_count: int = 1,
    adjacent_count: int = 2
) -> DifficultyTier:
    """
    Classify mystery room difficulty based on features.
    
    Easy: Large, unique size OR clear distinguishing features
    Medium: Typical sizes/adjacencies, unambiguous
    Hard: Threshold sizes, ambiguous features
    
    Args:
        room: Room to classify
        all_rooms: All rooms in floorplan
        door_count: Number of doors (from door placement)
        adjacent_count: Number of adjacent rooms
    
    Returns:
        Difficulty tier
    """
    features = compute_room_difficulty_features(room, all_rooms)
    
    # Rule-based classification
    area = features['area']
    uniqueness = features['area_uniqueness']
    type_count = features['type_count']
    
    # EASY: Clear distinguishing features
    if room.room_type == RoomType.KITCHEN and area > 12:
        return DifficultyTier.EASY
    if room.room_type == RoomType.BATHROOM and type_count == 1:
        return DifficultyTier.EASY
    if uniqueness > 5.0 and area > 15:
        # Very unique size and large
        return DifficultyTier.EASY
    
    # HARD: Ambiguous cases
    # Small bedroom vs office
    if room.room_type == RoomType.BEDROOM and 8 <= area <= 12:
        return DifficultyTier.HARD
    if room.room_type == RoomType.OFFICE and 8 <= area <= 12:
        return DifficultyTier.HARD
    # Large closet vs pantry
    if room.room_type == RoomType.CLOSET and area > 4:
        return DifficultyTier.HARD
    # Multiple of same type
    if type_count >= 2 and area < 15:
        return DifficultyTier.HARD
    
    # MEDIUM: Everything else
    return DifficultyTier.MEDIUM


def select_mystery_room(
    rooms: list[Room],
    rng: random.Random,
    target_difficulty: DifficultyTier = None
) -> Tuple[str, DifficultyTier]:
    """
    Select mystery room with difficulty-aware sampling.
    
    Publication-grade version with:
    - Canonical room types only
    - Difficulty classification
    - Balanced sampling support
    
    Args:
        rooms: List of all rooms in the floorplan
        rng: Random number generator
        target_difficulty: Optional target difficulty (for balanced sampling)
    
    Returns:
        Tuple of (room_id, difficulty_tier)
    """
    # Filter to canonical mystery room types
    candidates = [r for r in rooms if r.room_type in CANDIDATE_MYSTERY_TYPES]
    
    if not candidates:
        # Fallback: allow any room
        candidates = rooms
    
    # Classify difficulty for all candidates
    candidate_difficulties = []
    for room in candidates:
        difficulty = classify_room_difficulty(room, rooms)
        candidate_difficulties.append((room, difficulty))
    
    # Filter by target difficulty if specified
    if target_difficulty:
        filtered = [(r, d) for r, d in candidate_difficulties if d == target_difficulty]
        if filtered:
            candidate_difficulties = filtered
    
    # Select randomly from filtered candidates
    if not candidate_difficulties:
        # No candidates - fallback
        selected = rng.choice(rooms)
        difficulty = classify_room_difficulty(selected, rooms)
    else:
        selected, difficulty = rng.choice(candidate_difficulties)
    
    return selected.id, difficulty


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
