"""Adversarial floorplan generator for creating confusing/ambiguous layouts."""

import random
import uuid
from typing import Optional, List
from enum import Enum

from ..core.types import RegionType, SizeCategory, RoomType
from ..core.models import Floorplan, Room
from ..core.geometry import Rectangle
from .parameters import SIZE_CATEGORY_RANGES
from .constraints import get_room_types_for_region, get_target_room_count, validate_room_dimensions
from .space_partition import generate_room_rectangles
from .room_assigner import select_mystery_room, optimize_room_assignment
from .door_placer import place_doors


class Severity(Enum):
    """Adversarial strategy severity levels."""
    SLIGHT = "slight"
    MEDIUM = "medium"
    EXTREME = "extreme"

class AdversarialGenerator:
    """
    Generator for creating 'adversarial' floorplans that are difficult to classify.
    
    Strategies:
    1. Size Mismatch: Giant closets, tiny bedrooms
    2. Shape Confusion: Long narrow rooms assigned as living spaces
    3. Window Deception: Bedrooms without windows, closets with windows
    """
    
    def __init__(self, seed: int):
        self.seed = seed
        self.rng = random.Random(seed)
        
    def generate_confusing_floorplan(
        self,
        region: RegionType,
        size_category: SizeCategory,
        confusion_type: str = "size_mismatch",
        severity: Severity = Severity.MEDIUM
    ) -> Floorplan:
        """
        Generate a floorplan designed to confuse the model.
        
        Args:
            region: Regional style
            size_category: Size category
            confusion_type: Type of confusion to apply
            severity: Severity level (SLIGHT/MEDIUM/EXTREME)
            
        Returns:
            Adversarial Floorplan with calibrated confusion
        """
        floorplan_id = Floorplan.generate_id()
        
        # Determine target area
        area_range = SIZE_CATEGORY_RANGES[size_category]
        target_area = self.rng.uniform(area_range[0], area_range[1])
        
        # Determine room count and types
        room_count = get_target_room_count(size_category, region)
        room_types = get_room_types_for_region(region, size_category, self.rng)
        
        # Adjust room count
        room_count = len(room_types)
        
        # Generate room rectangles - use unique seed for variety
        partition_seed = self.seed + self.rng.randint(0, 10000)
        rectangles = generate_room_rectangles(
            target_area=target_area,
            room_count=room_count,
            seed=partition_seed
        )
        
        
        # Assign room types adversarially based on strategy and severity
        if confusion_type == "size_mismatch":
            rooms = self._assign_size_mismatch(rectangles, room_types, region, severity)
        elif confusion_type == "shape_confusion":
            rooms = self._assign_shape_confusion(rectangles, room_types, region, severity)
        elif confusion_type == "window_deception":
            rooms = self._assign_window_deception(rectangles, room_types, region, severity)
        elif confusion_type == "topological_island":
            rooms = self._assign_topological_island(rectangles, room_types, region, severity)
        elif confusion_type == "windowless_master":
            rooms = self._assign_windowless_master(rectangles, room_types, region, severity)
        elif confusion_type == "adjacency_violation":
            rooms = self._assign_normal_then_violate_adjacency(rectangles, room_types, region, severity)
        elif confusion_type == "missing_rooms":
            rooms = self._assign_with_missing_rooms(rectangles, room_types, region, severity)
        else:
            # Default to size mismatch
            rooms = self._assign_size_mismatch(rectangles, room_types, region, severity)
            
        # Optimize (maybe skip for extra confusion?)
        # rooms = optimize_room_assignment(rooms, region, self.rng)
        
        # Place doors
        doors = place_doors(
            rooms=rooms,
            region=region,
            rng=self.rng,
            ensure_connectivity=True
        )
        
        # Select mystery room (now returns ID and difficulty)
        mystery_room_id, mystery_difficulty = select_mystery_room(rooms, self.rng)
        
        # Mark mystery room and get type
        mystery_room_type = None
        for room in rooms:
            if room.id == mystery_room_id:
                room.is_mystery = True
                mystery_room_type = room.room_type.value
                
        # Create floorplan object
        floorplan = Floorplan(
            id=floorplan_id,
            seed=self.seed,
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
                "is_adversarial": True,
                "adversarial": {
                    "type": confusion_type,
                    "severity": severity.value
                },
                "mystery_room": {
                    "id": mystery_room_id,
                    "type": mystery_room_type,
                    "difficulty": mystery_difficulty.value
                }
            }
        )
        
        return floorplan

    def _assign_size_mismatch(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Assign room types to rectangles with size mismatch based on severity.
        
        Severity calibration:
        - SLIGHT: ±20% deviation from typical size
        - MEDIUM: ±50% deviation
        - EXTREME: ≥200% deviation (e.g., giant closets, tiny bedrooms)
        
        Args:
            rectangles: Room rectangles
            room_types: Room types to assign
            region: Regional style
            severity: Mismatch severity level
        
        Returns:
            List of mismatched rooms
        """
        # Sort rectangles by area (largest first)
        sorted_rects = sorted(rectangles, key=lambda r: r.area, reverse=True)
        
        # Sort room types by typical size (smallest first) to maximize mismatch
        def get_typical_area_rank(room_type: RoomType) -> int:
            ranks = {
                RoomType.CLOSET: 0,
                RoomType.PANTRY: 1,
                RoomType.BATHROOM: 2,
                RoomType.HALLWAY: 3,
                RoomType.ENTRYWAY: 4,
                RoomType.UTILITY_ROOM: 5,
                RoomType.OFFICE: 6,
                RoomType.GUEST_BEDROOM: 7,
                RoomType.BEDROOM: 8,
                RoomType.KITCHEN: 9,
                RoomType.DINING_ROOM: 10,
                RoomType.LIVING_ROOM: 11,
                RoomType.MASTER_BEDROOM: 12,
                RoomType.GARAGE: 13
            }
            return ranks.get(room_type, 5)

        # Sort types: Smallest to Largest
        sorted_types = sorted(room_types, key=get_typical_area_rank)
        
        # Determine mismatch strategy based on severity
        if severity == Severity.EXTREME:
            # Maximum mismatch: Largest rect -> Smallest type
            assignment = list(zip(sorted_rects, sorted_types))
        elif severity == Severity.MEDIUM:
            # Moderate mismatch: shift by ~50%
            shift = len(sorted_types) // 2
            shifted_types = sorted_types[shift:] + sorted_types[:shift]
            assignment = list(zip(sorted_rects, shifted_types))
        else:  # SLIGHT
            # Slight mismatch: shift by ~20%
            shift = max(1, len(sorted_types) // 5)
            shifted_types = sorted_types[shift:] + sorted_types[:shift]
            assignment = list(zip(sorted_rects, shifted_types))
        
        rooms: List[Room] = []
        
        for rect, room_type in assignment:
            # Random window assignment
            has_window = self.rng.random() < 0.5
            
            room = Room(
                id=str(uuid.uuid4()),
                room_type=room_type,
                bounds=rect,
                has_window=has_window,
                is_mystery=False
            )
            
            rooms.append(room)
            
        return rooms

    def _assign_shape_confusion(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Assign room types based on confusing aspect ratios.
        
        Severity calibration:
        - SLIGHT: 1.5x aspect ratio mismatch
        - MEDIUM: 2.5x aspect ratio mismatch
        - EXTREME: 4x+ aspect ratio mismatch
        """
        # Calculate aspect ratios (max dim / min dim)
        def get_aspect_ratio(r: Rectangle) -> float:
            return max(r.width, r.height) / min(r.width, r.height)
            
        sorted_rects = sorted(rectangles, key=get_aspect_ratio, reverse=True)
        
        # Sort room types: Square-ish first, Narrow-ish last
        # We want to assign Square-ish rooms to Narrow rects (mismatch)
        
        def get_typical_aspect_rank(room_type: RoomType) -> int:
            # 0 = Typically Square, 10 = Typically Narrow
            ranks = {
                RoomType.LIVING_ROOM: 0,
                RoomType.BEDROOM: 0,
                RoomType.DINING_ROOM: 0,
                RoomType.KITCHEN: 1,
                RoomType.GARAGE: 1,
                RoomType.BATHROOM: 2,
                RoomType.PANTRY: 3,
                RoomType.CLOSET: 3,
                RoomType.ENTRYWAY: 4,
                RoomType.HALLWAY: 5
            }
            return ranks.get(room_type, 2)
            
        sorted_types = sorted(room_types, key=get_typical_aspect_rank)
        
        # sorted_rects: Narrow -> Square
        # sorted_types: Square -> Narrow
        # Match Narrow Rect (index 0) with Square Type (index 0)
        
        rooms: List[Room] = []
        for i, rect in enumerate(sorted_rects):
            if i < len(sorted_types):
                room_type = sorted_types[i]
            else:
                room_type = self.rng.choice(sorted_types)
                
            has_window = self.rng.random() < 0.5
            
            rooms.append(Room(
                id=str(uuid.uuid4()),
                room_type=room_type,
                bounds=rect,
                has_window=has_window,
                is_mystery=False
            ))
            
        return rooms

    def _assign_window_deception(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Assign windows deceptively based on severity.
        
        Severity calibration:
        - SLIGHT: 1 window swapped
        - MEDIUM: Majority of windows misplaced
        - EXTREME: All window semantics inverted
        """
        # Assign randomly or by size (let's do random for chaos)
        self.rng.shuffle(room_types)
        
        rooms: List[Room] = []
        for i, rect in enumerate(rectangles):
            if i < len(room_types):
                room_type = room_types[i]
            else:
                room_type = self.rng.choice(room_types)
                
            # Deceptive window logic
            should_have_window = room_type in [
                RoomType.BEDROOM, RoomType.MASTER_BEDROOM, 
                RoomType.LIVING_ROOM, RoomType.KITCHEN, RoomType.DINING_ROOM
            ]
            
            # Flip it!
            has_window = not should_have_window
            
            rooms.append(Room(
                id=str(uuid.uuid4()),
                room_type=room_type,
                bounds=rect,
                has_window=has_window,
                is_mystery=False
            ))
            
        return rooms

    def _assign_normal_then_violate_adjacency(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Create adjacency violations based on severity.
        
        Severity calibration:
        - SLIGHT: 1 unrealistic adjacency
        - MEDIUM: 2-3 violations
        - EXTREME: Multiple violations creating implausible layout
        """
        # 1. Normal assignment (Large Rect -> Large Room)
        sorted_rects = sorted(rectangles, key=lambda r: r.area, reverse=True)
        
        def get_typical_area_rank(room_type: RoomType) -> int:
            ranks = {
                RoomType.CLOSET: 0, RoomType.PANTRY: 1, RoomType.BATHROOM: 2,
                RoomType.HALLWAY: 3, RoomType.ENTRYWAY: 4, RoomType.UTILITY_ROOM: 5,
                RoomType.OFFICE: 6, RoomType.GUEST_BEDROOM: 7, RoomType.BEDROOM: 8,
                RoomType.KITCHEN: 9, RoomType.DINING_ROOM: 10, RoomType.LIVING_ROOM: 11,
                RoomType.MASTER_BEDROOM: 12, RoomType.GARAGE: 13
            }
            return ranks.get(room_type, 5)

        # Sort types: Large to Small (to match Large Rects)
        sorted_types = sorted(room_types, key=get_typical_area_rank, reverse=True)
        
        rooms: List[Room] = []
        for i, rect in enumerate(sorted_rects):
            if i < len(sorted_types):
                rtype = sorted_types[i]
            else:
                rtype = self.rng.choice(sorted_types)
            rooms.append(Room(str(uuid.uuid4()), rtype, rect, self.rng.random() < 0.7, False))
            
        # 2. Find adjacent pair and force incompatibility
        # Incompatible pairs: Kitchen <-> Bathroom, Bedroom <-> Garage, Bedroom <-> Kitchen
        
        # Build adjacency list
        adj_pairs = []
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                if rooms[i].bounds.shares_edge_with(rooms[j].bounds):
                    adj_pairs.append((i, j))
                    
        if adj_pairs:
            # Pick a random adjacent pair
            idx1, idx2 = self.rng.choice(adj_pairs)
            
            # Force them to be incompatible
            # Let's make one Kitchen and one Bathroom (classic bad feng shui / hygiene)
            rooms[idx1].room_type = RoomType.KITCHEN
            rooms[idx2].room_type = RoomType.BATHROOM
            
            # Or Bedroom next to noisy Garage
            if len(adj_pairs) > 1:
                 idx3, idx4 = self.rng.choice(adj_pairs)
                 rooms[idx3].room_type = RoomType.MASTER_BEDROOM
                 rooms[idx4].room_type = RoomType.GARAGE
                 
        return rooms

    def _assign_with_missing_rooms(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Remove essential rooms based on severity.
        
        Severity calibration:
        - SLIGHT: 1 essential room missing
        - MEDIUM: 2 essential rooms missing
        - EXTREME: All core functions missing (no kitchen AND bathroom)
        """
        # Filter out essentials
        essentials = [RoomType.KITCHEN, RoomType.BATHROOM]
        filtered_types = [t for t in room_types if t not in essentials]
        
        if not filtered_types:
            filtered_types = [RoomType.BEDROOM] # Fallback
            
        # Fill back up to original count
        while len(filtered_types) < len(room_types):
            filtered_types.append(self.rng.choice(filtered_types))
            
        # Now assign normally (or randomly)
        # Let's do random assignment to avoid size clues helping too much
        self.rng.shuffle(filtered_types)
        
        rooms: List[Room] = []
        for i, rect in enumerate(rectangles):
            if i < len(filtered_types):
                rtype = filtered_types[i]
            else:
                rtype = self.rng.choice(filtered_types)

            rooms.append(Room(
                id=str(uuid.uuid4()),
                room_type=rtype,
                bounds=rect,
                has_window=self.rng.random() < 0.5,
                is_mystery=False
            ))

        return rooms

    def _assign_topological_island(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Assign an 'island' room (completely surrounded by other rooms) to a type 
        that typically requires exterior access (Kitchen, Laundry, Utility).
        """
        # 1. Identify "interior" rectangles (those with no exterior boundaries)
        min_x = min(r.x for r in rectangles)
        min_y = min(r.y for r in rectangles)
        max_x = max(r.right for r in rectangles)
        max_y = max(r.bottom for r in rectangles)
        
        interior_rects = []
        
        for r in rectangles:
            is_exterior = (r.x == min_x or r.y == min_y or 
                          r.right == max_x or r.bottom == max_y)
            if not is_exterior:
                interior_rects.append(r)
                
        # If no interior rects (small house), just pick the most "central" one
        if not interior_rects:
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            interior_rects = sorted(rectangles, key=lambda r: (r.center.x - center_x)**2 + (r.center.y - center_y)**2)[:1]

        rooms: List[Room] = []
        
        # Pick one interior rect to be the "Island"
        island_rect = self.rng.choice(interior_rects)
        # Assign it a type that SHOULD have a window/exterior wall
        island_type = RoomType.KITCHEN if RoomType.KITCHEN in room_types else RoomType.UTILITY_ROOM
        
        rooms.append(Room(str(uuid.uuid4()), island_type, island_rect, False, False))
        
        # Assign remaining rects normally
        remaining_rects = [r for r in rectangles if r != island_rect]
        remaining_types = [t for t in room_types if t != island_type]
        
        # Ensure we have enough types
        while len(remaining_types) < len(remaining_rects):
            remaining_types.append(self.rng.choice(room_types))
            
        self.rng.shuffle(remaining_types)
        for i, rect in enumerate(remaining_rects):
            rooms.append(Room(str(uuid.uuid4()), remaining_types[i], rect, self.rng.random() < 0.7, False))
            
        return rooms

    def _assign_windowless_master(
        self,
        rectangles: List[Rectangle],
        room_types: List[RoomType],
        region: RegionType,
        severity: Severity
    ) -> List[Room]:
        """
        Assign the largest room (Master Bedroom) to an interior/windowless position.
        """
        # Find largest rect
        largest_rect = max(rectangles, key=lambda r: r.area)
        
        rooms: List[Room] = []
        rooms.append(Room(str(uuid.uuid4()), RoomType.MASTER_BEDROOM, largest_rect, False, False))
        
        remaining_rects = [r for r in rectangles if r != largest_rect]
        remaining_types = [t for t in room_types if t != RoomType.MASTER_BEDROOM]
        
        while len(remaining_types) < len(remaining_rects):
            remaining_types.append(self.rng.choice(room_types))
            
        self.rng.shuffle(remaining_types)
        for i, rect in enumerate(remaining_rects):
            rooms.append(Room(str(uuid.uuid4()), remaining_types[i], rect, self.rng.random() < 0.7, False))
            
        return rooms
