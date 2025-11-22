"""Door placement logic for connecting rooms."""

import random
import uuid
from typing import List, Optional, Tuple

from ..core.geometry import Point, Rectangle
from ..core.types import DoorType, RegionType
from ..core.models import Room, Door
from .constraints import should_rooms_be_connected, get_preferred_adjacencies
from .parameters import MIN_DOOR_WIDTH, MAX_DOOR_WIDTH, DOOR_PLACEMENT_MARGIN


def find_adjacent_rooms(rooms: list[Room]) -> list[tuple[Room, Room]]:
    """
    Find all pairs of rooms that share an edge (are adjacent).

    Args:
        rooms: List of rooms

    Returns:
        List of (room1, room2) tuples for adjacent rooms
    """
    adjacent_pairs = []

    for i, room1 in enumerate(rooms):
        for room2 in rooms[i + 1:]:
            if room1.bounds.shares_edge_with(room2.bounds):
                adjacent_pairs.append((room1, room2))

    return adjacent_pairs


def calculate_door_position(
    room1: Room,
    room2: Room,
    rng: random.Random
) -> Optional[Point]:
    """
    Calculate the position for a door between two adjacent rooms.

    Args:
        room1: First room
        room2: Second room
        rng: Random number generator

    Returns:
        Point representing door position, or None if rooms don't share an edge
    """
    shared_edge = room1.bounds.get_shared_edge(room2.bounds)

    if not shared_edge:
        return None

    start, end = shared_edge

    # Calculate the length of the shared edge
    if abs(start.x - end.x) > abs(start.y - end.y):
        # Horizontal edge
        edge_length = abs(end.x - start.x)
        min_x = min(start.x, end.x) + DOOR_PLACEMENT_MARGIN
        max_x = max(start.x, end.x) - DOOR_PLACEMENT_MARGIN

        if max_x - min_x < MIN_DOOR_WIDTH:
            # Edge too short, place in center
            door_x = (start.x + end.x) / 2
        else:
            door_x = rng.uniform(min_x, max_x)

        door_y = start.y
        return Point(door_x, door_y)
    else:
        # Vertical edge
        edge_length = abs(end.y - start.y)
        min_y = min(start.y, end.y) + DOOR_PLACEMENT_MARGIN
        max_y = max(start.y, end.y) - DOOR_PLACEMENT_MARGIN

        if max_y - min_y < MIN_DOOR_WIDTH:
            # Edge too short, place in center
            door_y = (start.y + end.y) / 2
        else:
            door_y = rng.uniform(min_y, max_y)

        door_x = start.x
        return Point(door_x, door_y)


def select_door_type(
    room1: Room,
    room2: Room,
    region: RegionType,
    rng: random.Random
) -> DoorType:
    """
    Select appropriate door type based on room types and region.

    Args:
        room1: First room
        room2: Second room
        region: Regional style
        rng: Random number generator

    Returns:
        Appropriate door type
    """
    from ..core.types import RoomType

    # Archways more common in open-plan layouts
    archway_candidates = {
        (RoomType.KITCHEN, RoomType.DINING_ROOM),
        (RoomType.KITCHEN, RoomType.LIVING_ROOM),
        (RoomType.DINING_ROOM, RoomType.LIVING_ROOM),
        (RoomType.HALLWAY, RoomType.LIVING_ROOM),
    }

    room_pair = {room1.room_type, room2.room_type}
    pair_tuple = (room1.room_type, room2.room_type)
    reverse_pair = (room2.room_type, room1.room_type)

    # Check for archway candidates
    if pair_tuple in archway_candidates or reverse_pair in archway_candidates:
        if rng.random() < 0.4:
            return DoorType.ARCHWAY

    # Sliding doors more common in certain regions
    if region in [RegionType.JAPANESE_APARTMENT, RegionType.MODERN_URBAN]:
        if rng.random() < 0.3:
            return DoorType.SLIDING

    # Double doors for larger openings
    large_rooms = {RoomType.LIVING_ROOM, RoomType.MASTER_BEDROOM, RoomType.DINING_ROOM}
    if room1.room_type in large_rooms and room2.room_type in large_rooms:
        if rng.random() < 0.2:
            return DoorType.DOUBLE

    # Default to standard door
    return DoorType.STANDARD


def place_doors(
    rooms: list[Room],
    region: RegionType,
    rng: random.Random,
    ensure_connectivity: bool = True
) -> list[Door]:
    """
    Place doors between adjacent rooms based on architectural constraints.

    Args:
        rooms: List of rooms in the floorplan
        region: Regional style
        rng: Random number generator
        ensure_connectivity: If True, ensure all rooms are reachable

    Returns:
        List of Door objects
    """
    doors = []
    connected_pairs = set()

    # Find all adjacent room pairs
    adjacent_pairs = find_adjacent_rooms(rooms)

    # Score each pair based on how much they should be connected
    pair_scores = []
    for room1, room2 in adjacent_pairs:
        # Base score
        score = 0.5

        # Increase score if rooms should be connected per constraints
        if should_rooms_be_connected(room1.room_type, room2.room_type, region):
            score += 0.4

        # Check preferred adjacencies
        prefs1 = get_preferred_adjacencies(room1.room_type)
        prefs2 = get_preferred_adjacencies(room2.room_type)

        if room2.room_type in prefs1 or room1.room_type in prefs2:
            score += 0.3

        pair_scores.append(((room1, room2), score))

    # Sort by score (highest first)
    pair_scores.sort(key=lambda x: x[1], reverse=True)

    # Place doors for high-scoring pairs
    for (room1, room2), score in pair_scores:
        # Decide whether to place a door
        # High score = more likely
        if score > 0.7 or (score > 0.3 and rng.random() < score):
            position = calculate_door_position(room1, room2, rng)

            if position:
                door_type = select_door_type(room1, room2, region, rng)

                door = Door(
                    id=str(uuid.uuid4()),
                    room_a_id=room1.id,
                    room_b_id=room2.id,
                    position=position,
                    door_type=door_type
                )

                doors.append(door)
                connected_pairs.add(frozenset([room1.id, room2.id]))

    # Ensure connectivity if requested
    if ensure_connectivity:
        doors = ensure_all_rooms_connected(rooms, doors, adjacent_pairs, rng, region)

    return doors


def ensure_all_rooms_connected(
    rooms: list[Room],
    doors: list[Door],
    adjacent_pairs: list[tuple[Room, Room]],
    rng: random.Random,
    region: RegionType
) -> list[Door]:
    """
    Ensure all rooms are reachable by adding minimum necessary doors.

    Uses a Union-Find approach to detect connected components.

    Args:
        rooms: List of all rooms
        doors: Current list of doors
        adjacent_pairs: List of adjacent room pairs
        rng: Random number generator
        region: Regional style

    Returns:
        Updated list of doors with connectivity ensured
    """
    # Build adjacency from existing doors
    room_ids = {room.id for room in rooms}
    connected_components = UnionFind(room_ids)

    for door in doors:
        connected_components.union(door.room_a_id, door.room_b_id)

    # Check if all rooms are in one component
    if connected_components.num_components() == 1:
        return doors

    # Find disconnected components
    # Add doors to connect them
    doors_to_add = []

    # For each adjacent pair not yet connected, check if adding it would merge components
    for room1, room2 in adjacent_pairs:
        if not connected_components.connected(room1.id, room2.id):
            # Adding this door would merge components
            position = calculate_door_position(room1, room2, rng)

            if position:
                door_type = select_door_type(room1, room2, region, rng)

                door = Door(
                    id=str(uuid.uuid4()),
                    room_a_id=room1.id,
                    room_b_id=room2.id,
                    position=position,
                    door_type=door_type
                )

                doors_to_add.append(door)
                connected_components.union(room1.id, room2.id)

                # Check if we're now fully connected
                if connected_components.num_components() == 1:
                    break

    return doors + doors_to_add


class UnionFind:
    """Simple Union-Find data structure for connectivity checking."""

    def __init__(self, elements: set[str]):
        self.parent = {elem: elem for elem in elements}
        self.rank = {elem: 0 for elem in elements}

    def find(self, x: str) -> str:
        """Find the root of the component containing x."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        """Merge the components containing x and y."""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

    def connected(self, x: str, y: str) -> bool:
        """Check if x and y are in the same component."""
        return self.find(x) == self.find(y)

    def num_components(self) -> int:
        """Count the number of connected components."""
        roots = {self.find(elem) for elem in self.parent}
        return len(roots)
