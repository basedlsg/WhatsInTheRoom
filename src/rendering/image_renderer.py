"""Image rendering for floorplans using PIL."""

from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import os
import random

from ..core.models import Floorplan, Room, Door
from ..core.geometry import Rectangle, Point
from .styles import RenderStyle, DEFAULT_STYLE


class FloorplanRenderer:
    """Renders floorplans to images."""

    def __init__(self, style: RenderStyle = DEFAULT_STYLE):
        """
        Initialize renderer with a style.

        Args:
            style: Rendering style configuration
        """
        self.style = style

    def render(self, floorplan: Floorplan, output_path: str) -> None:
        """
        Render a floorplan to an image file.

        Args:
            floorplan: Floorplan to render
            output_path: Path to save the image
        """
        image = self.render_to_image(floorplan)
        image.save(output_path, "PNG")

    def render_to_image(self, floorplan: Floorplan) -> Image.Image:
        """
        Render a floorplan to a PIL Image.

        Args:
            floorplan: Floorplan to render

        Returns:
            PIL Image object
        """
        # Create blank image
        image = Image.new(
            "RGB",
            (self.style.image_width, self.style.image_height),
            self.style.background_color
        )
        draw = ImageDraw.Draw(image)

        # Calculate scale and offset to fit floorplan in image
        scale, offset_x, offset_y = self._calculate_transform(floorplan)

        # Highlight mystery room background if enabled
        if self.style.highlight_mystery_room:
            mystery_room = floorplan.mystery_room
            if mystery_room:
                self._draw_room_background(
                    draw, mystery_room, scale, offset_x, offset_y,
                    self.style.mystery_room_color
                )

        # Draw rooms (walls)
        for room in floorplan.rooms:
            self._draw_room_walls(draw, room, scale, offset_x, offset_y)

        # Draw doors
        if self.style.show_doors:
            for door in floorplan.doors:
                self._draw_door(draw, door, floorplan, scale, offset_x, offset_y)

        # Draw windows
        if self.style.show_windows:
            for room in floorplan.rooms:
                if room.has_window:
                    self._draw_windows(draw, room, scale, offset_x, offset_y)

        # Draw room labels (excluding mystery room)
        if self.style.show_room_labels:
            for room in floorplan.rooms:
                if not room.is_mystery:
                    self._draw_room_label(draw, room, scale, offset_x, offset_y)

        return image

    def _calculate_transform(self, floorplan: Floorplan) -> tuple[float, float, float]:
        """
        Calculate scale and offset to fit floorplan in image.

        Args:
            floorplan: Floorplan to render

        Returns:
            Tuple of (scale, offset_x, offset_y)
        """
        # Find bounding box of all rooms
        if not floorplan.rooms:
            return 1.0, 0.0, 0.0

        min_x = min(room.bounds.x for room in floorplan.rooms)
        min_y = min(room.bounds.y for room in floorplan.rooms)
        max_x = max(room.bounds.right for room in floorplan.rooms)
        max_y = max(room.bounds.bottom for room in floorplan.rooms)

        floorplan_width = max_x - min_x
        floorplan_height = max_y - min_y

        # Calculate scale to fit in image with margins
        available_width = self.style.image_width - 2 * self.style.margin
        available_height = self.style.image_height - 2 * self.style.margin

        scale_x = available_width / floorplan_width if floorplan_width > 0 else 1.0
        scale_y = available_height / floorplan_height if floorplan_height > 0 else 1.0
        scale = min(scale_x, scale_y)

        # Calculate offset to center the floorplan
        scaled_width = floorplan_width * scale
        scaled_height = floorplan_height * scale

        offset_x = (self.style.image_width - scaled_width) / 2 - min_x * scale
        offset_y = (self.style.image_height - scaled_height) / 2 - min_y * scale

        return scale, offset_x, offset_y

    def _transform_point(
        self, point: Point, scale: float, offset_x: float, offset_y: float
    ) -> tuple[float, float]:
        """Transform a point from floorplan coordinates to image coordinates."""
        x = point.x * scale + offset_x
        y = point.y * scale + offset_y
        return (x, y)

    def _transform_rect(
        self, rect: Rectangle, scale: float, offset_x: float, offset_y: float
    ) -> tuple[float, float, float, float]:
        """Transform a rectangle from floorplan coordinates to image coordinates."""
        x1 = rect.x * scale + offset_x
        y1 = rect.y * scale + offset_y
        x2 = (rect.x + rect.width) * scale + offset_x
        y2 = (rect.y + rect.height) * scale + offset_y
        return (x1, y1, x2, y2)

    def _draw_room_background(
        self,
        draw: ImageDraw.ImageDraw,
        room: Room,
        scale: float,
        offset_x: float,
        offset_y: float,
        color: tuple[int, int, int]
    ) -> None:
        """Draw a filled background for a room."""
        coords = self._transform_rect(room.bounds, scale, offset_x, offset_y)
        draw.rectangle(coords, fill=color)

    def _draw_room_walls(
        self,
        draw: ImageDraw.ImageDraw,
        room: Room,
        scale: float,
        offset_x: float,
        offset_y: float
    ) -> None:
        """Draw the walls (outline) of a room."""
        coords = self._transform_rect(room.bounds, scale, offset_x, offset_y)
        if self.style.is_sketchy:
            self._draw_rect_sketchy(
                draw, coords,
                outline=self.style.wall_color,
                width=int(self.style.wall_width)
            )
        else:
            draw.rectangle(
                coords,
                outline=self.style.wall_color,
                width=int(self.style.wall_width)
            )

    def _draw_door(
        self,
        draw: ImageDraw.ImageDraw,
        door: Door,
        floorplan: Floorplan,
        scale: float,
        offset_x: float,
        offset_y: float
    ) -> None:
        """Draw a door between two rooms."""
        # Get the two rooms
        room_a = floorplan.get_room_by_id(door.room_a_id)
        room_b = floorplan.get_room_by_id(door.room_b_id)

        if not room_a or not room_b:
            return

        # Transform door position
        door_x, door_y = self._transform_point(door.position, scale, offset_x, offset_y)

        # Determine door orientation based on shared edge
        shared_edge = room_a.bounds.get_shared_edge(room_b.bounds)
        if not shared_edge:
            return

        start, end = shared_edge

        # Door width in image coordinates
        door_width = 0.8 * scale  # ~0.8 meters

        if abs(start.x - end.x) > abs(start.y - end.y):
            # Horizontal door
            self._draw_line(
                draw,
                (door_x - door_width / 2, door_y),
                (door_x + door_width / 2, door_y),
                fill=self.style.door_color,
                width=int(self.style.door_width)
            )
        else:
            # Vertical door
            self._draw_line(
                draw,
                (door_x, door_y - door_width / 2),
                (door_x, door_y + door_width / 2),
                fill=self.style.door_color,
                width=int(self.style.door_width)
            )

    def _draw_windows(
        self,
        draw: ImageDraw.ImageDraw,
        room: Room,
        scale: float,
        offset_x: float,
        offset_y: float
    ) -> None:
        """Draw windows on exterior walls of a room."""
        # Simplified: draw a small window marker on one wall
        # In a real implementation, you'd detect exterior walls

        bounds = room.bounds
        window_size = 1.5 * scale  # 1.5 meters

        # Place window on the top wall (assuming it's exterior)
        center_x = (bounds.x + bounds.width / 2) * scale + offset_x
        top_y = bounds.y * scale + offset_y

        self._draw_line(
            draw,
            (center_x - window_size / 2, top_y),
            (center_x + window_size / 2, top_y),
            fill=self.style.window_color,
            width=int(self.style.window_width)
        )

    def _draw_room_label(
        self,
        draw: ImageDraw.ImageDraw,
        room: Room,
        scale: float,
        offset_x: float,
        offset_y: float
    ) -> None:
        """Draw the label for a room."""
        # Get room center in image coordinates
        center = room.bounds.center
        center_x, center_y = self._transform_point(center, scale, offset_x, offset_y)

        # Format label text
        label = room.room_type.value.replace("_", " ").title()

        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.style.font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((center_x, center_y), label, font=font, anchor="mm")

        # Draw text
        draw.text(
            (center_x, center_y),
            label,
            fill=self.style.text_color,
            font=font,
            anchor="mm"
        )

    def _draw_line(
        self,
        draw: ImageDraw.ImageDraw,
        start: tuple[float, float],
        end: tuple[float, float],
        fill: tuple[int, int, int],
        width: int
    ) -> None:
        """Draw a line, optionally sketchy."""
        if self.style.is_sketchy:
            # Draw multiple wobbly lines
            intensity = self.style.sketch_intensity
            for _ in range(3):
                # Perturb start and end
                s_x = start[0] + random.uniform(-2, 2) * intensity
                s_y = start[1] + random.uniform(-2, 2) * intensity
                e_x = end[0] + random.uniform(-2, 2) * intensity
                e_y = end[1] + random.uniform(-2, 2) * intensity
                
                # Overshoot
                dx = e_x - s_x
                dy = e_y - s_y
                length = (dx*dx + dy*dy)**0.5
                if length > 0:
                    overshoot = random.uniform(-5, 5) * intensity
                    e_x += (dx/length) * overshoot
                    e_y += (dy/length) * overshoot
                    s_x -= (dx/length) * overshoot
                    s_y -= (dy/length) * overshoot

                draw.line([(s_x, s_y), (e_x, e_y)], fill=fill, width=width)
        else:
            draw.line([start, end], fill=fill, width=width)

    def _draw_rect_sketchy(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple[float, float, float, float],
        outline: tuple[int, int, int],
        width: int
    ) -> None:
        """Draw a rectangle using sketchy lines."""
        x1, y1, x2, y2 = coords
        
        # Draw 4 sides
        self._draw_line(draw, (x1, y1), (x2, y1), outline, width)
        self._draw_line(draw, (x2, y1), (x2, y2), outline, width)
        self._draw_line(draw, (x2, y2), (x1, y2), outline, width)
        self._draw_line(draw, (x1, y2), (x1, y1), outline, width)


def render_floorplan(
    floorplan: Floorplan,
    output_path: str,
    style: RenderStyle = DEFAULT_STYLE
) -> None:
    """
    Convenience function to render a floorplan to an image.

    Args:
        floorplan: Floorplan to render
        output_path: Path to save the image
        style: Rendering style (optional)
    """
    renderer = FloorplanRenderer(style)
    renderer.render(floorplan, output_path)
