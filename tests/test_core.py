"""Unit tests for core geometry and models."""

import pytest
from src.core.geometry import Point, Rectangle
from src.core.types import RoomType, RegionType, SizeCategory
from src.core.models import Room, Door, Floorplan


class TestPoint:
    """Tests for Point class."""

    def test_point_creation(self):
        p = Point(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0

    def test_point_distance(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        assert p1.distance_to(p2) == 5.0

    def test_point_addition(self):
        p1 = Point(1.0, 2.0)
        p2 = Point(3.0, 4.0)
        p3 = p1 + p2
        assert p3.x == 4.0
        assert p3.y == 6.0


class TestRectangle:
    """Tests for Rectangle class."""

    def test_rectangle_creation(self):
        r = Rectangle(x=0, y=0, width=10, height=20)
        assert r.x == 0
        assert r.width == 10
        assert r.height == 20

    def test_rectangle_area(self):
        r = Rectangle(x=0, y=0, width=10, height=20)
        assert r.area == 200

    def test_rectangle_center(self):
        r = Rectangle(x=0, y=0, width=10, height=20)
        center = r.center
        assert center.x == 5.0
        assert center.y == 10.0

    def test_rectangle_contains_point(self):
        r = Rectangle(x=0, y=0, width=10, height=20)
        assert r.contains_point(Point(5, 10))
        assert not r.contains_point(Point(15, 10))

    def test_rectangle_intersects(self):
        r1 = Rectangle(x=0, y=0, width=10, height=10)
        r2 = Rectangle(x=5, y=5, width=10, height=10)
        r3 = Rectangle(x=20, y=20, width=10, height=10)

        assert r1.intersects(r2)
        assert not r1.intersects(r3)

    def test_rectangle_shares_edge(self):
        r1 = Rectangle(x=0, y=0, width=10, height=10)
        r2 = Rectangle(x=10, y=0, width=10, height=10)
        r3 = Rectangle(x=20, y=0, width=10, height=10)

        assert r1.shares_edge_with(r2)
        assert not r1.shares_edge_with(r3)


class TestRoom:
    """Tests for Room class."""

    def test_room_creation(self):
        bounds = Rectangle(x=0, y=0, width=5, height=5)
        room = Room(
            id="test-id",
            room_type=RoomType.BEDROOM,
            bounds=bounds,
            has_window=True
        )

        assert room.id == "test-id"
        assert room.room_type == RoomType.BEDROOM
        assert room.area == 25
        assert room.has_window

    def test_room_serialization(self):
        bounds = Rectangle(x=0, y=0, width=5, height=5)
        room = Room(
            id="test-id",
            room_type=RoomType.BEDROOM,
            bounds=bounds
        )

        # Convert to dict and back
        data = room.to_dict()
        room2 = Room.from_dict(data)

        assert room2.id == room.id
        assert room2.room_type == room.room_type
        assert room2.bounds.width == room.bounds.width


class TestDoor:
    """Tests for Door class."""

    def test_door_creation(self):
        door = Door(
            id="door-1",
            room_a_id="room-a",
            room_b_id="room-b",
            position=Point(5, 5)
        )

        assert door.id == "door-1"
        assert door.connects_rooms("room-a", "room-b")
        assert door.get_other_room("room-a") == "room-b"


class TestFloorplan:
    """Tests for Floorplan class."""

    def test_floorplan_creation(self):
        room1 = Room(
            id="room-1",
            room_type=RoomType.KITCHEN,
            bounds=Rectangle(0, 0, 5, 5)
        )
        room2 = Room(
            id="room-2",
            room_type=RoomType.BEDROOM,
            bounds=Rectangle(5, 0, 5, 5),
            is_mystery=True
        )

        door = Door(
            id="door-1",
            room_a_id="room-1",
            room_b_id="room-2",
            position=Point(5, 2.5)
        )

        floorplan = Floorplan(
            id="fp-1",
            seed=42,
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.SMALL,
            rooms=[room1, room2],
            doors=[door],
            mystery_room_id="room-2"
        )

        assert floorplan.total_area == 50
        assert floorplan.mystery_room.id == "room-2"
        assert len(floorplan.get_adjacent_rooms("room-1")) == 1

    def test_floorplan_serialization(self):
        room1 = Room(
            id="room-1",
            room_type=RoomType.KITCHEN,
            bounds=Rectangle(0, 0, 5, 5)
        )

        floorplan = Floorplan(
            id="fp-1",
            seed=42,
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.SMALL,
            rooms=[room1],
            doors=[],
            mystery_room_id="room-1"
        )

        # Convert to dict and back
        data = floorplan.to_dict()
        floorplan2 = Floorplan.from_dict(data)

        assert floorplan2.id == floorplan.id
        assert floorplan2.seed == floorplan.seed
        assert len(floorplan2.rooms) == 1
