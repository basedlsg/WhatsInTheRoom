
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.adversarial_generator import AdversarialGenerator
from src.rendering.image_renderer import render_floorplan
from src.storage.floorplan_store import save_floorplan
from src.storage.image_store import save_image_path
import os

def test_adversarial():
    print("Testing Adversarial Generator...")
    
    generator = AdversarialGenerator(seed=42)
    
    floorplan = generator.generate_confusing_floorplan(
        region=RegionType.MODERN_URBAN,
        size_category=SizeCategory.MEDIUM,
        confusion_type="size_mismatch"
    )
    
    print(f"Generated Floorplan ID: {floorplan.id}")
    print(f"Metadata: {floorplan.metadata}")
    
    print("\nRoom Assignments (Area -> Type):")
    for room in floorplan.rooms:
        print(f"  {room.area:.2f} m2 -> {room.room_type.value}")
        
    # Save and render
    output_dir = "data/adversarial_test"
    os.makedirs(output_dir, exist_ok=True)
    
    save_floorplan(floorplan, output_dir)
    image_path = os.path.join(output_dir, f"{floorplan.id}.png")
    render_floorplan(floorplan, image_path)
    print(f"\nSaved to {output_dir}")

if __name__ == "__main__":
    test_adversarial()
