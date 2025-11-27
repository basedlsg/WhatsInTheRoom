
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import DEFAULT_STYLE, SKETCHY_STYLE, RenderStyle

def create_comparison():
    """Create side-by-side comparison of rendering styles."""
    
    # Generate one floorplan
    fp = generate_floorplan(
        seed=999,
        region=RegionType.MODERN_URBAN,
        size_category=SizeCategory.MEDIUM
    )
    
    output_dir = "data/visual_comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Normal style (clean lines)
    normal_path = os.path.join(output_dir, "1_normal_clean.png")
    render_floorplan(fp, normal_path, style=DEFAULT_STYLE)
    print(f"✓ Normal (clean): {normal_path}")
    
    # 2. Sketchy style (current implementation)
    sketchy_path = os.path.join(output_dir, "2_sketchy_subtle.png")
    render_floorplan(fp, sketchy_path, style=SKETCHY_STYLE)
    print(f"✓ Sketchy (subtle): {sketchy_path}")
    
    # 3. VERY sketchy (increased intensity)
    very_sketchy = RenderStyle(
        is_sketchy=True,
        sketch_intensity=5.0,  # Much higher
        wall_width=2.0
    )
    very_sketchy_path = os.path.join(output_dir, "3_very_sketchy.png")
    render_floorplan(fp, very_sketchy_path, style=very_sketchy)
    print(f"✓ Very sketchy: {very_sketchy_path}")
    
    # 4. EXTREME sketchy
    extreme_sketchy = RenderStyle(
        is_sketchy=True,
        sketch_intensity=10.0,  # Extreme
        wall_width=1.5
    )
    extreme_path = os.path.join(output_dir, "4_extreme_sketchy.png")
    render_floorplan(fp, extreme_path, style=extreme_sketchy)
    print(f"✓ Extreme sketchy: {extreme_path}")
    
    print(f"\n✅ Created 4 comparison images in {output_dir}/")
    print("\nIntensity levels:")
    print("  1. Normal: Clean, perfect lines")
    print("  2. Sketchy (current): intensity=2.0")
    print("  3. Very Sketchy: intensity=5.0")
    print("  4. Extreme: intensity=10.0")

if __name__ == "__main__":
    create_comparison()
