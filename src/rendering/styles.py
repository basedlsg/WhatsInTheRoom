"""Visual styles and configuration for floorplan rendering."""

from dataclasses import dataclass


@dataclass
class RenderStyle:
    """Configuration for rendering floorplans."""

    # Image dimensions
    image_width: int = 1200
    image_height: int = 1200
    dpi: int = 100

    # Colors (RGB tuples)
    background_color: tuple[int, int, int] = (255, 255, 255)  # White
    wall_color: tuple[int, int, int] = (50, 50, 50)  # Dark gray
    door_color: tuple[int, int, int] = (200, 100, 50)  # Brown
    window_color: tuple[int, int, int] = (100, 150, 200)  # Light blue
    text_color: tuple[int, int, int] = (0, 0, 0)  # Black
    mystery_room_color: tuple[int, int, int] = (220, 220, 220)  # Light gray background

    # Line widths (in pixels)
    wall_width: float = 3.0
    door_width: float = 2.5
    window_width: float = 2.0

    # Font settings
    font_family: str = "sans-serif"
    font_size: int = 14
    font_size_small: int = 10

    # Rendering options
    show_room_labels: bool = True
    show_doors: bool = True
    show_windows: bool = True
    show_measurements: bool = False  # Show room dimensions
    highlight_mystery_room: bool = True

    # Margins and padding
    margin: int = 50  # Margin around the floorplan
    label_padding: int = 5


# Default style
DEFAULT_STYLE = RenderStyle()


# Alternative style for high-contrast rendering
HIGH_CONTRAST_STYLE = RenderStyle(
    wall_color=(0, 0, 0),
    door_color=(255, 0, 0),
    window_color=(0, 0, 255),
    wall_width=4.0,
    font_size=16,
)


# Minimal style for clean visualization
MINIMAL_STYLE = RenderStyle(
    wall_color=(100, 100, 100),
    door_color=(150, 150, 150),
    window_color=(150, 150, 255),
    wall_width=2.0,
    show_windows=False,
    highlight_mystery_room=False,
)
