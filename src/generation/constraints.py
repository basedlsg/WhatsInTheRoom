"""Region-specific constraints and validation rules for floorplan generation."""

import random
from typing import List

from ..core.types import RoomType, RegionType, SizeCategory
from ..core.models import Room
from .parameters import (
    REGION_CONFIGS,
    SIZE_CATEGORY_RANGES,
    ROOM_AREA_RANGES,
    MIN_ROOM_DIMENSIONS,
)


def get_target_room_count(size_category: SizeCategory, region: RegionType) -> int:
    """
    Determine the target number of rooms based on size and region.

    Args:
        size_category: Size category of the floorplan
        region: Regional style

    Returns:
        Target number of rooms
    """
    # Base counts by size
    base_counts = {
        SizeCategory.MICRO: 2,
        SizeCategory.SMALL: 3,
        SizeCategory.MEDIUM: 5,
        SizeCategory.LARGE: 7,
        SizeCategory.EXTRA_LARGE: 9,
    }

    count = base_counts.get(size_category, 5)

    # Regional adjustments
    if region == RegionType.CHINESE_CITY_APARTMENT:
        count = max(2, count - 1)  # Tend to have fewer, larger rooms
    elif region == RegionType.EUROPEAN_OLD_TOWN:
        count = count + 1  # More compartmentalized
    elif region == RegionType.MODERN_URBAN and size_category in [SizeCategory.MICRO, SizeCategory.SMALL]:
        count = max(2, count - 1)  # Studio/loft style

    return count


def get_room_types_for_region(
    region: RegionType,
    size_category: SizeCategory,
    rng: random.Random
) -> list[RoomType]:
    """
    Generate a list of room types appropriate for the region and size.

    Args:
        region: Regional style
        size_category: Size category
        rng: Random number generator for reproducibility

    Returns:
        List of room types to include in the floorplan
    """
    config = REGION_CONFIGS.get(region, REGION_CONFIGS[RegionType.MODERN_URBAN])
    typical_rooms = config["typical_rooms"].copy()
    optional_rooms = config["optional_rooms"].copy()

    target_count = get_target_room_count(size_category, region)

    # Start with typical rooms
    room_types = typical_rooms.copy()

    # Add optional rooms if needed
    rng.shuffle(optional_rooms)
    while len(room_types) < target_count and optional_rooms:
        room_types.append(optional_rooms.pop(0))

    # If still need more rooms, duplicate some types (e.g., multiple bedrooms)
    duplicatable = [RoomType.BEDROOM, RoomType.CLOSET, RoomType.BATHROOM]
    while len(room_types) < target_count:
        room_type = rng.choice(duplicatable)
        if room_type in room_types:
            # Make it more specific
            if room_type == RoomType.BEDROOM:
                if RoomType.GUEST_BEDROOM not in room_types:
                    room_types.append(RoomType.GUEST_BEDROOM)
                else:
                    room_types.append(RoomType.BEDROOM)
            else:
                room_types.append(room_type)
        else:
            room_types.append(room_type)

    # Trim if too many
    if len(room_types) > target_count:
        room_types = room_types[:target_count]

    return room_types


def should_have_window(room_type: RoomType, region: RegionType, rng: random.Random) -> bool:
    """
    Determine if a room should have a window based on type and region.

    Args:
        room_type: Type of room
        region: Regional style
        rng: Random number generator

    Returns:
        True if room should have a window
    """
    config = REGION_CONFIGS.get(region, REGION_CONFIGS[RegionType.MODERN_URBAN])
    base_probability = config["window_probability"]

    # Adjust by room type
    type_modifiers = {
        RoomType.LIVING_ROOM: 1.3,
        RoomType.KITCHEN: 1.2,
        RoomType.BEDROOM: 1.3,
        RoomType.MASTER_BEDROOM: 1.4,
        RoomType.GUEST_BEDROOM: 1.2,
        RoomType.BATHROOM: 0.7,
        RoomType.HALLWAY: 0.1,
        RoomType.CLOSET: 0.1,
        RoomType.OFFICE: 1.2,
        RoomType.DINING_ROOM: 1.1,
        RoomType.BALCONY: 1.5,  # Almost always have "windows" (open air)
        RoomType.STORAGE: 0.3,
        RoomType.GARAGE: 0.5,
    }

    modifier = type_modifiers.get(room_type, 1.0)
    final_probability = min(0.95, base_probability * modifier)

    return rng.random() < final_probability


def validate_room_dimensions(room_type: RoomType, width: float, height: float) -> bool:
    """
    Check if room dimensions meet minimum requirements for the room type.

    Args:
        room_type: Type of room
        width: Room width in meters
        height: Room height in meters

    Returns:
        True if dimensions are valid
    """
    min_dims = MIN_ROOM_DIMENSIONS.get(room_type, (1.5, 1.5))
    min_width, min_height = min_dims

    # Check both orientations (room can be rotated)
    valid_orientation_1 = width >= min_width and height >= min_height
    valid_orientation_2 = width >= min_height and height >= min_width

    return valid_orientation_1 or valid_orientation_2


def validate_room_area(room_type: RoomType, area: float) -> bool:
    """
    Check if room area is within acceptable range for the room type.

    Args:
        room_type: Type of room
        area: Room area in square meters

    Returns:
        True if area is valid
    """
    area_range = ROOM_AREA_RANGES.get(room_type, (2, 50))
    min_area, max_area = area_range

    # Allow some flexibility (80% of min, 150% of max)
    return min_area * 0.8 <= area <= max_area * 1.5


def get_preferred_adjacencies(room_type: RoomType) -> list[RoomType]:
    """
    Get list of room types that should preferably be adjacent to this room.

    Args:
        room_type: Type of room

    Returns:
        List of preferred adjacent room types
    """
    adjacency_preferences = {
        RoomType.KITCHEN: [RoomType.DINING_ROOM, RoomType.LIVING_ROOM, RoomType.PANTRY],
        RoomType.BATHROOM: [RoomType.BEDROOM, RoomType.MASTER_BEDROOM, RoomType.HALLWAY],
        RoomType.CLOSET: [RoomType.BEDROOM, RoomType.MASTER_BEDROOM, RoomType.ENTRYWAY],
        RoomType.MASTER_BEDROOM: [RoomType.BATHROOM, RoomType.CLOSET],
        RoomType.BEDROOM: [RoomType.HALLWAY, RoomType.CLOSET],
        RoomType.LAUNDRY: [RoomType.BATHROOM, RoomType.KITCHEN, RoomType.UTILITY_ROOM],
        RoomType.PANTRY: [RoomType.KITCHEN],
        RoomType.GARAGE: [RoomType.ENTRYWAY, RoomType.HALLWAY, RoomType.LAUNDRY],
        RoomType.OFFICE: [RoomType.HALLWAY, RoomType.LIVING_ROOM],
        RoomType.DINING_ROOM: [RoomType.KITCHEN, RoomType.LIVING_ROOM],
        RoomType.BALCONY: [RoomType.LIVING_ROOM, RoomType.BEDROOM, RoomType.MASTER_BEDROOM],
    }

    return adjacency_preferences.get(room_type, [RoomType.HALLWAY])


def should_rooms_be_connected(
    room_type_a: RoomType,
    room_type_b: RoomType,
    region: RegionType
) -> bool:
    """
    Determine if two room types should have a direct door connection.

    Args:
        room_type_a: First room type
        room_type_b: Second room type
        region: Regional style

    Returns:
        True if rooms should be connected
    """
    # Check if they're in each other's preferred adjacencies
    prefs_a = get_preferred_adjacencies(room_type_a)
    prefs_b = get_preferred_adjacencies(room_type_b)

    if room_type_b in prefs_a or room_type_a in prefs_b:
        return True

    # Open plan considerations
    config = REGION_CONFIGS.get(region, REGION_CONFIGS[RegionType.MODERN_URBAN])
    if config["open_plan_probability"] > 0.5:
        # In open-plan layouts, kitchen-living-dining often connect
        open_plan_rooms = {RoomType.KITCHEN, RoomType.LIVING_ROOM, RoomType.DINING_ROOM}
        if room_type_a in open_plan_rooms and room_type_b in open_plan_rooms:
            return True

    return False
