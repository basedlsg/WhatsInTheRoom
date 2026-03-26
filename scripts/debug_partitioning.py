from src.core.geometry import Rectangle
from src.generation.space_partition import generate_room_rectangles
from src.core.types import SizeCategory
from src.generation.parameters import SIZE_CATEGORY_RANGES
import random

def test_large_partitioning():
    seed = 3000
    target_area = 200 # Middle of LARGE range
    room_count = 7
    
    rects = generate_room_rectangles(target_area, room_count, seed)
    print(f"Target Area: {target_area}, Target Count: {room_count}")
    print(f"Generated {len(rects)} rectangles.")
    for i, r in enumerate(rects):
        print(f"  Rect {i}: {r.area:.2f} m2 ({r.width:.2f}x{r.height:.2f}) at ({r.x:.2f}, {r.y:.2f})")

if __name__ == "__main__":
    test_large_partitioning()
