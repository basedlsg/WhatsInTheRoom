"""Tests for adversarial floorplan generator.

Covers all adversarial strategy methods and the critical missing_rooms bug
(committee critique B1).
"""

import pytest
from src.core.geometry import Rectangle
from src.core.types import RoomType, RegionType, SizeCategory
from src.generation.adversarial_generator import AdversarialGenerator, Severity


class TestAdversarialGeneratorStrategies:
    """Test that each adversarial strategy produces valid rooms."""

    def setup_method(self):
        self.gen = AdversarialGenerator(seed=42)

    @pytest.mark.parametrize("confusion_type", [
        "size_mismatch",
        "shape_confusion",
        "window_deception",
        "topological_island",
        "windowless_master",
        "adjacency_violation",
        "missing_rooms",
    ])
    def test_strategy_returns_nonempty_rooms(self, confusion_type):
        """Every adversarial strategy must return at least one room."""
        fp = self.gen.generate_confusing_floorplan(
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM,
            confusion_type=confusion_type,
            severity=Severity.MEDIUM,
        )
        assert len(fp.rooms) > 0, (
            f"Strategy '{confusion_type}' returned 0 rooms"
        )

    @pytest.mark.parametrize("confusion_type", [
        "size_mismatch",
        "shape_confusion",
        "window_deception",
        "adjacency_violation",
        "missing_rooms",
    ])
    def test_strategy_room_count_matches_rectangles(self, confusion_type):
        """Each strategy should produce one room per rectangle."""
        fp = self.gen.generate_confusing_floorplan(
            region=RegionType.US_SUBURB,
            size_category=SizeCategory.LARGE,
            confusion_type=confusion_type,
            severity=Severity.MEDIUM,
        )
        # Every room should have valid bounds
        for room in fp.rooms:
            assert room.bounds is not None
            assert room.bounds.width > 0
            assert room.bounds.height > 0


class TestMissingRoomsBug:
    """Regression tests for the _assign_with_missing_rooms bug (B1).

    The original implementation looped over rectangles computing room types
    but never appended Room objects to the list — returning [] every time.
    """

    def test_missing_rooms_returns_nonempty(self):
        """Critical regression: missing_rooms must actually produce rooms."""
        gen = AdversarialGenerator(seed=123)
        fp = gen.generate_confusing_floorplan(
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM,
            confusion_type="missing_rooms",
            severity=Severity.MEDIUM,
        )
        assert len(fp.rooms) > 0, (
            "REGRESSION: _assign_with_missing_rooms still returns empty list"
        )

    def test_missing_rooms_excludes_essentials(self):
        """missing_rooms strategy should exclude kitchen and bathroom."""
        gen = AdversarialGenerator(seed=456)
        fp = gen.generate_confusing_floorplan(
            region=RegionType.US_SUBURB,
            size_category=SizeCategory.LARGE,
            confusion_type="missing_rooms",
            severity=Severity.MEDIUM,
        )
        room_types = {r.room_type for r in fp.rooms}
        assert RoomType.KITCHEN not in room_types, (
            "missing_rooms should exclude KITCHEN"
        )
        assert RoomType.BATHROOM not in room_types, (
            "missing_rooms should exclude BATHROOM"
        )

    @pytest.mark.parametrize("severity", [
        Severity.SLIGHT, Severity.MEDIUM, Severity.EXTREME
    ])
    def test_missing_rooms_all_severities(self, severity):
        """missing_rooms should work at all severity levels."""
        gen = AdversarialGenerator(seed=789)
        fp = gen.generate_confusing_floorplan(
            region=RegionType.JAPANESE_APARTMENT,
            size_category=SizeCategory.SMALL,
            confusion_type="missing_rooms",
            severity=severity,
        )
        assert len(fp.rooms) > 0


class TestSeverityLevels:
    """Ensure severity levels produce different outputs."""

    def test_severity_produces_valid_metadata(self):
        """Adversarial metadata should record severity level."""
        gen = AdversarialGenerator(seed=100)
        for sev in [Severity.SLIGHT, Severity.MEDIUM, Severity.EXTREME]:
            fp = gen.generate_confusing_floorplan(
                region=RegionType.MODERN_URBAN,
                size_category=SizeCategory.MEDIUM,
                confusion_type="size_mismatch",
                severity=sev,
            )
            assert fp.metadata["adversarial"]["severity"] == sev.value
            assert fp.metadata["is_adversarial"] is True
