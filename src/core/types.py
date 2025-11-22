"""Type definitions and enums for the floorplan experiment."""

from enum import Enum


class RoomType(str, Enum):
    """Types of rooms that can appear in a floorplan."""
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    HALLWAY = "hallway"
    CLOSET = "closet"
    OFFICE = "office"
    DINING_ROOM = "dining_room"
    LAUNDRY = "laundry"
    GARAGE = "garage"
    BALCONY = "balcony"
    PANTRY = "pantry"
    ENTRYWAY = "entryway"
    GUEST_BEDROOM = "guest_bedroom"
    MASTER_BEDROOM = "master_bedroom"
    STORAGE = "storage"
    UTILITY_ROOM = "utility_room"


class RegionType(str, Enum):
    """Regional architectural styles for floorplan generation."""
    US_SUBURB = "US_suburb"
    CHINESE_CITY_APARTMENT = "Chinese_city_apartment"
    EUROPEAN_OLD_TOWN = "European_old_town"
    JAPANESE_APARTMENT = "Japanese_apartment"
    AUSTRALIAN_HOUSE = "Australian_house"
    MODERN_URBAN = "Modern_urban"


class SizeCategory(str, Enum):
    """Size categories for floorplans based on total area."""
    MICRO = "micro"       # < 40 m²
    SMALL = "small"       # 40-80 m²
    MEDIUM = "medium"     # 80-150 m²
    LARGE = "large"       # 150-250 m²
    EXTRA_LARGE = "extra_large"  # > 250 m²


class DoorType(str, Enum):
    """Types of doors/openings between rooms."""
    STANDARD = "standard"
    SLIDING = "sliding"
    ARCHWAY = "archway"
    DOUBLE = "double"
