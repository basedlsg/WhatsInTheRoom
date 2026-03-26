"""Verification script for new FloorplanQA rigor improvements."""
import os
from src.core.types import RegionType, SizeCategory
from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.rendering.image_renderer import render_floorplan
from src.rendering.styles import DEFAULT_STYLE

def main():
    # Setup
    output_dir = "data/rigor_verification"
    os.makedirs(output_dir, exist_ok=True)
    
    gen = AdversarialGenerator(seed=2025)
    
    # 1. Test Topological Island
    print("Generating Topological Island...")
    island_fp = gen.generate_confusing_floorplan(
        region=RegionType.US_SUBURB,
        size_category=SizeCategory.MEDIUM,
        confusion_type="topological_island",
        severity=Severity.EXTREME
    )
    render_floorplan(island_fp, os.path.join(output_dir, "island_kitchen.png"), DEFAULT_STYLE)
    
    # 2. Test Windowless Master
    print("Generating Windowless Master...")
    master_fp = gen.generate_confusing_floorplan(
        region=RegionType.CHINESE_CITY_APARTMENT,
        size_category=SizeCategory.SMALL,
        confusion_type="windowless_master",
        severity=Severity.EXTREME
    )
    render_floorplan(master_fp, os.path.join(output_dir, "windowless_master.png"), DEFAULT_STYLE)
    
    print(f"Verification images saved to {output_dir}")

if __name__ == "__main__":
    main()
