
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import SKETCHY_STYLE

def test_sketchy():
    print("Testing Sketchy Renderer...")
    
    # Generate a normal floorplan
    floorplan = generate_floorplan(
        seed=123,
        region=RegionType.MODERN_URBAN,
        size_category=SizeCategory.MEDIUM
    )
    
    output_dir = "data/sketchy_test"
    os.makedirs(output_dir, exist_ok=True)
    
    image_path = os.path.join(output_dir, f"{floorplan.id}_sketchy.png")
    
    # Render with sketchy style
    render_floorplan(floorplan, image_path, style=SKETCHY_STYLE)
    
    print(f"Rendered sketchy floorplan to {image_path}")

if __name__ == "__main__":
    test_sketchy()
