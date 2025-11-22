"""Main floorplan generation orchestrator."""

import random
from typing import Optional

from ..core.types import RegionType, SizeCategory
from ..core.models import Floorplan
from .parameters import SIZE_CATEGORY_RANGES
from .constraints import get_room_types_for_region, get_target_room_count
from .space_partition import generate_room_rectangles
from .room_assigner import assign_room_types, select_mystery_room, optimize_room_assignment
from .door_placer import place_doors


def generate_floorplan(
    seed: int,
    region: RegionType,
    size_category: SizeCategory,
    floorplan_id: Optional[str] = None
) -> Floorplan:
    """
    Generate a complete synthetic floorplan.

    This is the main entry point for floorplan generation. It orchestrates:
    1. Space partitioning (creating room rectangles)
    2. Room type assignment
    3. Door placement
    4. Mystery room selection

    Args:
        seed: Random seed for reproducible generation
        region: Regional architectural style
        size_category: Size category (micro, small, medium, large, extra_large)
        floorplan_id: Optional ID for the floorplan (auto-generated if not provided)

    Returns:
        Complete Floorplan object ready for rendering
    """
    # Initialize random number generator
    rng = random.Random(seed)

    # Generate ID if not provided
    if floorplan_id is None:
        floorplan_id = Floorplan.generate_id()

    # Determine target area
    area_range = SIZE_CATEGORY_RANGES[size_category]
    target_area = rng.uniform(area_range[0], area_range[1])

    # Determine room count and types
    room_count = get_target_room_count(size_category, region)
    room_types = get_room_types_for_region(region, size_category, rng)

    # Adjust room count to match room types
    room_count = len(room_types)

    # Generate room rectangles via space partitioning
    rectangles = generate_room_rectangles(
        target_area=target_area,
        room_count=room_count,
        seed=seed
    )

    # Assign room types to rectangles
    rooms = assign_room_types(
        rectangles=rectangles,
        region=region,
        room_types=room_types,
        rng=rng
    )

    # Optimize room assignments
    rooms = optimize_room_assignment(rooms, region, rng)

    # Place doors between rooms
    doors = place_doors(
        rooms=rooms,
        region=region,
        rng=rng,
        ensure_connectivity=True
    )

    # Select mystery room
    mystery_room_id = select_mystery_room(rooms, rng)

    # Mark the mystery room
    for room in rooms:
        if room.id == mystery_room_id:
            room.is_mystery = True

    # Create floorplan object
    floorplan = Floorplan(
        id=floorplan_id,
        seed=seed,
        region=region,
        size_category=size_category,
        rooms=rooms,
        doors=doors,
        mystery_room_id=mystery_room_id,
        metadata={
            "target_area": target_area,
            "actual_area": sum(room.area for room in rooms),
            "room_count": len(rooms),
            "door_count": len(doors),
        }
    )

    return floorplan


def validate_floorplan(floorplan: Floorplan) -> tuple[bool, list[str]]:
    """
    Validate that a floorplan meets all requirements.

    Args:
        floorplan: Floorplan to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check that mystery room exists
    mystery_room = floorplan.mystery_room
    if not mystery_room:
        errors.append(f"Mystery room {floorplan.mystery_room_id} not found in rooms")

    # Check that exactly one room is marked as mystery
    mystery_count = sum(1 for room in floorplan.rooms if room.is_mystery)
    if mystery_count != 1:
        errors.append(f"Expected 1 mystery room, found {mystery_count}")

    # Check that all rooms are non-overlapping
    for i, room1 in enumerate(floorplan.rooms):
        for room2 in floorplan.rooms[i + 1:]:
            if room1.bounds.intersects(room2.bounds):
                errors.append(f"Rooms {room1.id} and {room2.id} overlap")

    # Check that all rooms have at least one door (are connected)
    for room in floorplan.rooms:
        doors_for_room = floorplan.get_doors_for_room(room.id)
        if len(doors_for_room) == 0:
            errors.append(f"Room {room.id} ({room.room_type.value}) has no doors")

    # Check that mystery room has at least one door
    if mystery_room:
        mystery_doors = floorplan.get_doors_for_room(mystery_room.id)
        if len(mystery_doors) == 0:
            errors.append("Mystery room has no doors (isolated)")

    # Check that all doors connect valid rooms
    room_ids = {room.id for room in floorplan.rooms}
    for door in floorplan.doors:
        if door.room_a_id not in room_ids:
            errors.append(f"Door {door.id} references invalid room {door.room_a_id}")
        if door.room_b_id not in room_ids:
            errors.append(f"Door {door.id} references invalid room {door.room_b_id}")

    return len(errors) == 0, errors


def generate_batch(
    count: int,
    region: RegionType,
    size_category: SizeCategory,
    start_seed: int = 0
) -> list[Floorplan]:
    """
    Generate a batch of floorplans with sequential seeds.

    Args:
        count: Number of floorplans to generate
        region: Regional style (same for all)
        size_category: Size category (same for all)
        start_seed: Starting seed value

    Returns:
        List of generated floorplans
    """
    floorplans = []

    for i in range(count):
        seed = start_seed + i
        floorplan = generate_floorplan(
            seed=seed,
            region=region,
            size_category=size_category
        )

        # Validate
        is_valid, errors = validate_floorplan(floorplan)
        if not is_valid:
            print(f"Warning: Floorplan {floorplan.id} has validation errors: {errors}")

        floorplans.append(floorplan)

    return floorplans
