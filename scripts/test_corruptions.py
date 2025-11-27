#!/usr/bin/env python3
"""Test script for image corruption pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import DEFAULT_STYLE
from src.rendering.corruptions import (
    CorruptionType,
    apply_corruption,
    get_corruption_severity
)
from PIL import Image

def test_corruptions():
    """Test all corruption types on a sample floorplan."""
    
    print("=" * 70)
    print("CORRUPTION PIPELINE TEST")
    print("=" * 70)
    
    # Generate a test floorplan
    fp = generate_floorplan(
        seed=42,
        region=RegionType.MODERN_URBAN,
        size_category=SizeCategory.MEDIUM
    )
    
    # Render to PIL Image
    output_path = "data/test_corruptions/base.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    render_floorplan(fp, output_path, DEFAULT_STYLE)
    
    # Load base image
    base_image = Image.open(output_path)
    print(f"\n✅ Generated base floorplan: {output_path}")
    print(f"   Size: {base_image.size}, Mode: {base_image.mode}")
    
    # Test each corruption type
    corruption_types = [
        CorruptionType.BLUR,
        CorruptionType.CONTRAST,
        CorruptionType.JPEG,
        CorruptionType.SKEW
    ]
    
    levels = ["slight", "medium", "extreme"]
    
    for corruption_type in corruption_types:
        print(f"\n{corruption_type.value}:")
        for level in levels:
            severity = get_corruption_severity(corruption_type, level)
            corrupted, metadata = apply_corruption(base_image, corruption_type, severity)
            
            output_file = f"data/test_corruptions/{corruption_type.value}_{level}.png"
            corrupted.save(output_file)
            
            print(f"  {level:8s} (severity={severity:3d}): ✅ {output_file}")
    
    print("\n" + "=" * 70)
    print("✅ All corruptions applied successfully!")
    print(f"   Check outputs in: data/test_corruptions/")
    print("=" * 70)

if __name__ == "__main__":
    test_corruptions()
