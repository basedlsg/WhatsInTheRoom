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
    wall_color: tuple[int, int, int] = (0, 0, 0)  # Pure Black for walls
    door_color: tuple[int, int, int] = (255, 100, 0)  # Brighter Orange
    window_color: tuple[int, int, int] = (0, 150, 255)  # Brighter Blue
    text_color: tuple[int, int, int] = (0, 0, 0)  # Black
    mystery_room_color: tuple[int, int, int] = (240, 240, 240)  # Very light gray
    furniture_color: tuple[int, int, int] = (100, 100, 100) # Darker gray for furniture

    # Line widths (in pixels)
    wall_width: float = 4.0
    door_width: float = 3.5
    window_width: float = 3.0
    fixture_width: float = 3.0  # Increased for visibility
    fixture_color: tuple[int, int, int] = (0, 0, 0) # Defaults to black

    # Font settings
    font_family: str = "sans-serif"
    font_size: int = 14
    font_size_small: int = 10

    # Rendering options
    show_room_labels: bool = True
    show_doors: bool = True
    show_windows: bool = True
    show_fixtures: bool = True  # Show fixed furniture like sinks/toilets
    show_furniture: bool = True  # Show movable furniture like beds/sofas
    show_measurements: bool = False  # Show room dimensions
    highlight_mystery_room: bool = True

    # Margins and padding
    margin: int = 50  # Margin around the floorplan
    label_padding: int = 5

    # Visual Noise / Sketchiness
    is_sketchy: bool = False
    sketch_intensity: float = 1.0


# Default style
DEFAULT_STYLE = RenderStyle()


# Alternative style for high-contrast rendering
HIGH_CONTRAST_STYLE = RenderStyle(
    wall_color=(0, 0, 0),
    door_color=(255, 0, 0),
    window_color=(0, 0, 255),
    wall_width=4.0,
    font_size=16,
    fixture_color=(0, 0, 255),  # Pure Blue
    fixture_width=4.0
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

# Sketchy style variants for testing visual robustness
MEDIUM_SKETCHY_STYLE = RenderStyle(
    is_sketchy=True,
    sketch_intensity=5.0,
    wall_width=2.0,
    font_family="serif"
)

HIGH_SKETCHY_STYLE = RenderStyle(
    is_sketchy=True,
    sketch_intensity=7.5,
    wall_width=2.0,
    font_family="serif"
)

EXTREME_SKETCHY_STYLE = RenderStyle(
    is_sketchy=True,
    sketch_intensity=10.0,
    wall_width=1.5,
    font_family="serif"
)

# Default sketchy style (now using extreme for visibility)
SKETCHY_STYLE = EXTREME_SKETCHY_STYLE
