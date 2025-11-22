"""Geometric primitives and utilities for floorplan generation."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Point:
    """A 2D point in space."""
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __add__(self, other: "Point") -> "Point":
        """Add two points."""
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        """Subtract two points."""
        return Point(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Rectangle:
    """An axis-aligned rectangle."""
    x: float  # Left edge
    y: float  # Top edge
    width: float
    height: float

    @property
    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height

    @property
    def center(self) -> Point:
        """Get the center point of the rectangle."""
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    @property
    def left(self) -> float:
        """Left edge x-coordinate."""
        return self.x

    @property
    def right(self) -> float:
        """Right edge x-coordinate."""
        return self.x + self.width

    @property
    def top(self) -> float:
        """Top edge y-coordinate."""
        return self.y

    @property
    def bottom(self) -> float:
        """Bottom edge y-coordinate."""
        return self.y + self.height

    def contains_point(self, point: Point) -> bool:
        """Check if the rectangle contains a point."""
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)

    def intersects(self, other: "Rectangle") -> bool:
        """Check if this rectangle intersects with another."""
        return not (self.right <= other.left or
                   self.left >= other.right or
                   self.bottom <= other.top or
                   self.top >= other.bottom)

    def intersection(self, other: "Rectangle") -> Optional["Rectangle"]:
        """
        Calculate the intersection rectangle with another rectangle.

        Returns:
            Rectangle representing the intersection, or None if no intersection.
        """
        if not self.intersects(other):
            return None

        left = max(self.left, other.left)
        right = min(self.right, other.right)
        top = max(self.top, other.top)
        bottom = min(self.bottom, other.bottom)

        return Rectangle(
            x=left,
            y=top,
            width=right - left,
            height=bottom - top
        )

    def shares_edge_with(self, other: "Rectangle", tolerance: float = 0.1) -> bool:
        """
        Check if this rectangle shares an edge with another rectangle.

        Args:
            other: Another rectangle
            tolerance: Allowed distance for edge alignment

        Returns:
            True if rectangles share an edge (are adjacent)
        """
        # Check for vertical adjacency (shared left-right edge)
        if abs(self.right - other.left) < tolerance or abs(self.left - other.right) < tolerance:
            # Check if they overlap in y-direction
            return not (self.bottom <= other.top or self.top >= other.bottom)

        # Check for horizontal adjacency (shared top-bottom edge)
        if abs(self.bottom - other.top) < tolerance or abs(self.top - other.bottom) < tolerance:
            # Check if they overlap in x-direction
            return not (self.right <= other.left or self.left >= other.right)

        return False

    def get_shared_edge(self, other: "Rectangle", tolerance: float = 0.1) -> Optional[tuple[Point, Point]]:
        """
        Get the shared edge between two adjacent rectangles.

        Args:
            other: Another rectangle
            tolerance: Allowed distance for edge alignment

        Returns:
            Tuple of (start_point, end_point) defining the shared edge, or None
        """
        if not self.shares_edge_with(other, tolerance):
            return None

        # Vertical edge (left-right)
        if abs(self.right - other.left) < tolerance:
            # self is on the left
            overlap_top = max(self.top, other.top)
            overlap_bottom = min(self.bottom, other.bottom)
            return (Point(self.right, overlap_top), Point(self.right, overlap_bottom))
        elif abs(self.left - other.right) < tolerance:
            # self is on the right
            overlap_top = max(self.top, other.top)
            overlap_bottom = min(self.bottom, other.bottom)
            return (Point(self.left, overlap_top), Point(self.left, overlap_bottom))

        # Horizontal edge (top-bottom)
        if abs(self.bottom - other.top) < tolerance:
            # self is above
            overlap_left = max(self.left, other.left)
            overlap_right = min(self.right, other.right)
            return (Point(overlap_left, self.bottom), Point(overlap_right, self.bottom))
        elif abs(self.top - other.bottom) < tolerance:
            # self is below
            overlap_left = max(self.left, other.left)
            overlap_right = min(self.right, other.right)
            return (Point(overlap_left, self.top), Point(overlap_right, self.top))

        return None

    def expand(self, amount: float) -> "Rectangle":
        """
        Expand the rectangle by a given amount in all directions.

        Args:
            amount: Amount to expand (negative to shrink)

        Returns:
            New expanded rectangle
        """
        return Rectangle(
            x=self.x - amount,
            y=self.y - amount,
            width=self.width + 2 * amount,
            height=self.height + 2 * amount
        )
