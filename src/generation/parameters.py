"""Parameters and constants for floorplan generation."""

from ..core.types import RoomType, RegionType, SizeCategory


# Size category area ranges (in square meters)
SIZE_CATEGORY_RANGES = {
    SizeCategory.MICRO: (25, 40),
    SizeCategory.SMALL: (40, 80),
    SizeCategory.MEDIUM: (80, 150),
    SizeCategory.LARGE: (150, 250),
    SizeCategory.EXTRA_LARGE: (250, 400),
}


# Typical room dimensions (in meters) - (min_area, max_area)
ROOM_AREA_RANGES = {
    RoomType.LIVING_ROOM: (12, 30),
    RoomType.KITCHEN: (6, 15),
    RoomType.BEDROOM: (9, 20),
    RoomType.MASTER_BEDROOM: (14, 25),
    RoomType.GUEST_BEDROOM: (9, 16),
    RoomType.BATHROOM: (3, 8),
    RoomType.HALLWAY: (2, 10),
    RoomType.CLOSET: (1.5, 4),
    RoomType.OFFICE: (6, 15),
    RoomType.DINING_ROOM: (8, 18),
    RoomType.LAUNDRY: (2, 6),
    RoomType.GARAGE: (12, 30),
    RoomType.BALCONY: (3, 10),
    RoomType.PANTRY: (2, 5),
    RoomType.ENTRYWAY: (2, 8),
    RoomType.STORAGE: (2, 6),
    RoomType.UTILITY_ROOM: (3, 8),
}


# Minimum room dimensions (width, height in meters)
MIN_ROOM_DIMENSIONS = {
    RoomType.LIVING_ROOM: (3.0, 3.0),
    RoomType.KITCHEN: (2.0, 2.5),
    RoomType.BEDROOM: (2.5, 3.0),
    RoomType.MASTER_BEDROOM: (3.0, 3.5),
    RoomType.GUEST_BEDROOM: (2.5, 3.0),
    RoomType.BATHROOM: (1.5, 1.8),
    RoomType.HALLWAY: (0.9, 1.0),
    RoomType.CLOSET: (0.8, 1.0),
    RoomType.OFFICE: (2.0, 2.5),
    RoomType.DINING_ROOM: (2.5, 2.5),
    RoomType.LAUNDRY: (1.5, 1.5),
    RoomType.GARAGE: (2.5, 4.0),
    RoomType.BALCONY: (1.2, 1.5),
    RoomType.PANTRY: (1.0, 1.5),
    RoomType.ENTRYWAY: (1.2, 1.5),
    RoomType.STORAGE: (1.0, 1.5),
    RoomType.UTILITY_ROOM: (1.5, 1.8),
}


# Room type probabilities for mystery room selection
# Lower values = less likely to be selected as mystery room
MYSTERY_ROOM_WEIGHTS = {
    RoomType.LIVING_ROOM: 0.3,  # Usually obvious
    RoomType.KITCHEN: 0.3,  # Usually obvious
    RoomType.BEDROOM: 0.5,  # Moderate ambiguity
    RoomType.MASTER_BEDROOM: 0.4,
    RoomType.GUEST_BEDROOM: 0.8,  # Good candidate - ambiguous
    RoomType.BATHROOM: 0.2,  # Usually obvious
    RoomType.HALLWAY: 0.1,  # Very obvious
    RoomType.CLOSET: 1.0,  # Excellent candidate - ambiguous
    RoomType.OFFICE: 1.0,  # Excellent candidate - could be bedroom
    RoomType.DINING_ROOM: 0.6,
    RoomType.LAUNDRY: 0.8,  # Could be storage
    RoomType.GARAGE: 0.3,  # Usually obvious
    RoomType.BALCONY: 0.5,
    RoomType.PANTRY: 0.9,  # Could be storage or closet
    RoomType.ENTRYWAY: 0.2,  # Usually obvious
    RoomType.STORAGE: 1.0,  # Excellent candidate
    RoomType.UTILITY_ROOM: 0.8,
}


# Region-specific configuration
REGION_CONFIGS = {
    RegionType.US_SUBURB: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.MASTER_BEDROOM,
            RoomType.BEDROOM,
            RoomType.BATHROOM,
            RoomType.GARAGE,
            RoomType.DINING_ROOM,
        ],
        "optional_rooms": [
            RoomType.GUEST_BEDROOM,
            RoomType.OFFICE,
            RoomType.LAUNDRY,
            RoomType.CLOSET,
            RoomType.PANTRY,
        ],
        "window_probability": 0.7,  # Higher for suburbs
        "open_plan_probability": 0.6,  # Kitchen-living room connection
    },
    RegionType.CHINESE_CITY_APARTMENT: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.BEDROOM,
            RoomType.BATHROOM,
            RoomType.BALCONY,
        ],
        "optional_rooms": [
            RoomType.GUEST_BEDROOM,
            RoomType.STORAGE,
            RoomType.DINING_ROOM,
        ],
        "window_probability": 0.5,
        "open_plan_probability": 0.3,
    },
    RegionType.EUROPEAN_OLD_TOWN: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.BEDROOM,
            RoomType.BATHROOM,
            RoomType.HALLWAY,
        ],
        "optional_rooms": [
            RoomType.OFFICE,
            RoomType.DINING_ROOM,
            RoomType.GUEST_BEDROOM,
            RoomType.STORAGE,
        ],
        "window_probability": 0.6,
        "open_plan_probability": 0.2,  # More separate rooms
    },
    RegionType.JAPANESE_APARTMENT: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.BEDROOM,
            RoomType.BATHROOM,
            RoomType.BALCONY,
        ],
        "optional_rooms": [
            RoomType.STORAGE,
            RoomType.ENTRYWAY,
        ],
        "window_probability": 0.5,
        "open_plan_probability": 0.4,
    },
    RegionType.AUSTRALIAN_HOUSE: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.BEDROOM,
            RoomType.MASTER_BEDROOM,
            RoomType.BATHROOM,
            RoomType.GARAGE,
        ],
        "optional_rooms": [
            RoomType.GUEST_BEDROOM,
            RoomType.OFFICE,
            RoomType.LAUNDRY,
            RoomType.DINING_ROOM,
        ],
        "window_probability": 0.7,
        "open_plan_probability": 0.7,  # Very common in Australia
    },
    RegionType.MODERN_URBAN: {
        "typical_rooms": [
            RoomType.LIVING_ROOM,
            RoomType.KITCHEN,
            RoomType.BEDROOM,
            RoomType.BATHROOM,
        ],
        "optional_rooms": [
            RoomType.OFFICE,
            RoomType.GUEST_BEDROOM,
            RoomType.BALCONY,
            RoomType.STORAGE,
        ],
        "window_probability": 0.6,
        "open_plan_probability": 0.8,  # Very open modern design
    },
}


# Space partitioning parameters
MIN_PARTITION_AREA = 3.0  # Minimum area for a room partition (m²)
MAX_PARTITION_ATTEMPTS = 50  # Max attempts for space partitioning
MIN_PARTITION_RATIO = 0.3  # Minimum ratio for splitting (30/70)
MAX_PARTITION_RATIO = 0.7  # Maximum ratio for splitting (70/30)


# Door placement parameters
MIN_DOOR_WIDTH = 0.8  # Minimum door width in meters
MAX_DOOR_WIDTH = 1.2  # Maximum door width in meters
DOOR_PLACEMENT_MARGIN = 0.5  # Margin from corners when placing doors


# Aspect ratio constraints
MIN_ASPECT_RATIO = 0.4  # Minimum width/height ratio (avoid very narrow rooms)
MAX_ASPECT_RATIO = 3.0  # Maximum width/height ratio (avoid very elongated rooms)
