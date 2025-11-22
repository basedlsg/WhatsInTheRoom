"""Core data models for floorplan generation and analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from .geometry import Rectangle, Point
from .types import RoomType, RegionType, SizeCategory, DoorType


@dataclass
class Room:
    """A room within a floorplan."""
    id: str
    room_type: RoomType
    bounds: Rectangle
    has_window: bool = False
    is_mystery: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def area(self) -> float:
        """Get the room's area in square meters."""
        return self.bounds.area

    @property
    def center(self) -> Point:
        """Get the center point of the room."""
        return self.bounds.center

    def to_dict(self) -> dict[str, Any]:
        """Convert room to dictionary for serialization."""
        return {
            "id": self.id,
            "room_type": self.room_type.value,
            "bounds": {
                "x": self.bounds.x,
                "y": self.bounds.y,
                "width": self.bounds.width,
                "height": self.bounds.height,
            },
            "has_window": self.has_window,
            "is_mystery": self.is_mystery,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Room":
        """Create a Room from a dictionary."""
        bounds_data = data["bounds"]
        return cls(
            id=data["id"],
            room_type=RoomType(data["room_type"]),
            bounds=Rectangle(
                x=bounds_data["x"],
                y=bounds_data["y"],
                width=bounds_data["width"],
                height=bounds_data["height"],
            ),
            has_window=data.get("has_window", False),
            is_mystery=data.get("is_mystery", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Door:
    """A door connecting two rooms."""
    id: str
    room_a_id: str
    room_b_id: str
    position: Point
    door_type: DoorType = DoorType.STANDARD
    metadata: dict[str, Any] = field(default_factory=dict)

    def connects_rooms(self, room_id_1: str, room_id_2: str) -> bool:
        """Check if this door connects two specific rooms."""
        return {self.room_a_id, self.room_b_id} == {room_id_1, room_id_2}

    def get_other_room(self, room_id: str) -> str | None:
        """Get the ID of the room on the other side of this door."""
        if self.room_a_id == room_id:
            return self.room_b_id
        elif self.room_b_id == room_id:
            return self.room_a_id
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert door to dictionary for serialization."""
        return {
            "id": self.id,
            "room_a_id": self.room_a_id,
            "room_b_id": self.room_b_id,
            "position": {"x": self.position.x, "y": self.position.y},
            "door_type": self.door_type.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Door":
        """Create a Door from a dictionary."""
        position_data = data["position"]
        return cls(
            id=data["id"],
            room_a_id=data["room_a_id"],
            room_b_id=data["room_b_id"],
            position=Point(x=position_data["x"], y=position_data["y"]),
            door_type=DoorType(data.get("door_type", DoorType.STANDARD.value)),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Floorplan:
    """A complete floorplan with rooms and doors."""
    id: str
    seed: int
    region: RegionType
    size_category: SizeCategory
    rooms: list[Room]
    doors: list[Door]
    mystery_room_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_area(self) -> float:
        """Calculate total area of all rooms."""
        return sum(room.area for room in self.rooms)

    @property
    def mystery_room(self) -> Room | None:
        """Get the mystery room."""
        for room in self.rooms:
            if room.id == self.mystery_room_id:
                return room
        return None

    def get_room_by_id(self, room_id: str) -> Room | None:
        """Get a room by its ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None

    def get_adjacent_rooms(self, room_id: str) -> list[Room]:
        """Get all rooms adjacent to a given room (connected by doors)."""
        adjacent_ids = []
        for door in self.doors:
            other_room_id = door.get_other_room(room_id)
            if other_room_id:
                adjacent_ids.append(other_room_id)

        return [room for room in self.rooms if room.id in adjacent_ids]

    def get_doors_for_room(self, room_id: str) -> list[Door]:
        """Get all doors connected to a specific room."""
        return [door for door in self.doors
                if door.room_a_id == room_id or door.room_b_id == room_id]

    def to_dict(self) -> dict[str, Any]:
        """Convert floorplan to dictionary for serialization."""
        return {
            "id": self.id,
            "seed": self.seed,
            "region": self.region.value,
            "size_category": self.size_category.value,
            "rooms": [room.to_dict() for room in self.rooms],
            "doors": [door.to_dict() for door in self.doors],
            "mystery_room_id": self.mystery_room_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Floorplan":
        """Create a Floorplan from a dictionary."""
        return cls(
            id=data["id"],
            seed=data["seed"],
            region=RegionType(data["region"]),
            size_category=SizeCategory(data["size_category"]),
            rooms=[Room.from_dict(room_data) for room_data in data["rooms"]],
            doors=[Door.from_dict(door_data) for door_data in data["doors"]],
            mystery_room_id=data["mystery_room_id"],
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID for a floorplan."""
        return str(uuid.uuid4())


@dataclass
class ModelPrediction:
    """A prediction from a vision-language model about the mystery room."""
    floorplan_id: str
    model_name: str
    predicted_room_type: str
    confidence: float | None = None
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert prediction to dictionary for serialization."""
        return {
            "floorplan_id": self.floorplan_id,
            "model_name": self.model_name,
            "predicted_room_type": self.predicted_room_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "raw_response": self.raw_response,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelPrediction":
        """Create a ModelPrediction from a dictionary."""
        return cls(
            floorplan_id=data["floorplan_id"],
            model_name=data["model_name"],
            predicted_room_type=data["predicted_room_type"],
            confidence=data.get("confidence"),
            reasoning=data.get("reasoning", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            raw_response=data.get("raw_response", {}),
            metadata=data.get("metadata", {}),
        )
