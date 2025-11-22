"""Response parsers for model predictions."""

import json
import re
from typing import Optional, Dict, Any


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain markdown or other formatting.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON dictionary or None if not found
    """
    # Try to find JSON in code blocks
    code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(code_block_pattern, text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.finditer(json_pattern, text, re.DOTALL)

    for match in matches:
        try:
            data = json.loads(match.group(0))
            # Verify it has expected keys
            if 'room_type' in data or 'reasoning' in data:
                return data
        except json.JSONDecodeError:
            continue

    return None


def normalize_room_type(room_type: str) -> str:
    """
    Normalize a room type string to standard format.

    Args:
        room_type: Raw room type string

    Returns:
        Normalized room type (lowercase, underscores)
    """
    # Convert to lowercase
    room_type = room_type.lower().strip()

    # Replace spaces and hyphens with underscores
    room_type = room_type.replace(' ', '_').replace('-', '_')

    # Remove common prefixes/suffixes
    room_type = room_type.replace('_room', '')
    room_type = room_type.replace('the_', '')

    # Common aliases
    aliases = {
        'study': 'office',
        'den': 'office',
        'wc': 'bathroom',
        'restroom': 'bathroom',
        'washroom': 'bathroom',
        'loo': 'bathroom',
        'wardrobe': 'closet',
        'store': 'storage',
        'storeroom': 'storage',
        'utility': 'utility_room',
        'mudroom': 'entryway',
        'foyer': 'entryway',
        'corridor': 'hallway',
        'passage': 'hallway',
    }

    return aliases.get(room_type, room_type)


def validate_room_type(room_type: str) -> bool:
    """
    Check if a room type is valid/recognized.

    Args:
        room_type: Room type to validate

    Returns:
        True if valid
    """
    valid_types = {
        'living_room', 'kitchen', 'bedroom', 'bathroom', 'hallway',
        'closet', 'office', 'dining_room', 'laundry', 'garage',
        'balcony', 'pantry', 'entryway', 'guest_bedroom',
        'master_bedroom', 'storage', 'utility_room'
    }

    return room_type in valid_types


def parse_confidence(text: str) -> Optional[float]:
    """
    Try to extract a confidence score from text.

    Args:
        text: Text that may contain confidence

    Returns:
        Confidence score (0-1) or None
    """
    # Look for percentage
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
    match = re.search(percentage_pattern, text)

    if match:
        value = float(match.group(1))
        return value / 100.0

    # Look for decimal confidence
    confidence_pattern = r'confidence[:\s]+(\d+(?:\.\d+)?)'
    match = re.search(confidence_pattern, text.lower())

    if match:
        value = float(match.group(1))
        # Normalize to 0-1 range
        if value > 1.0:
            value = value / 100.0
        return value

    return None
