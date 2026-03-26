#!/usr/bin/env python3
"""
FloorplanQA: Procedural Floorplan Generator
Generates synthetic floorplans with ground-truth room graphs.
"""

import os
import json
import random
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class Room:
    id: str
    room_type: str
    x: int
    y: int
    width: int
    height: int
    color: Tuple[int, int, int] = field(default_factory=lambda: (200, 200, 200))
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def intersects(self, other: 'Room', margin: int = 5) -> bool:
        return not (
            self.x + self.width + margin < other.x or
            other.x + other.width + margin < self.x or
            self.y + self.height + margin < other.y or
            other.y + other.height + margin < self.y
        )
    
    def is_adjacent(self, other: 'Room', threshold: int = 10) -> bool:
        """Check if rooms share a wall (are adjacent)."""
        # Horizontal adjacency
        h_adjacent = (
            abs((self.x + self.width) - other.x) < threshold or
            abs((other.x + other.width) - self.x) < threshold
        )
        h_overlap = not (self.y + self.height < other.y or other.y + other.height < self.y)
        
        # Vertical adjacency
        v_adjacent = (
            abs((self.y + self.height) - other.y) < threshold or
            abs((other.y + other.height) - self.y) < threshold
        )
        v_overlap = not (self.x + self.width < other.x or other.x + other.width < self.x)
        
        return (h_adjacent and h_overlap) or (v_adjacent and v_overlap)


@dataclass
class Floorplan:
    id: str
    rooms: List[Room]
    adjacency_graph: Dict[str, List[str]]
    width: int = 1024
    height: int = 1024
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rooms": [asdict(r) for r in self.rooms],
            "adjacency_graph": self.adjacency_graph,
            "width": self.width,
            "height": self.height
        }


# ==============================================================================
# ROOM TYPE CONFIGURATIONS
# ==============================================================================

ROOM_COLORS = {
    "bedroom": (173, 216, 230),      # Light blue
    "bathroom": (144, 238, 144),     # Light green
    "kitchen": (255, 218, 185),      # Peach
    "living_room": (255, 255, 224),  # Light yellow
    "dining_room": (255, 228, 196),  # Bisque
    "office": (221, 160, 221),       # Plum
    "closet": (192, 192, 192),       # Silver
    "hallway": (245, 245, 220),      # Beige
}

ROOM_SIZE_RANGES = {
    "bedroom": (120, 200),
    "bathroom": (60, 100),
    "kitchen": (100, 180),
    "living_room": (150, 250),
    "dining_room": (100, 160),
    "office": (80, 140),
    "closet": (40, 70),
    "hallway": (40, 80),
}


# ==============================================================================
# FLOORPLAN GENERATOR
# ==============================================================================

class FloorplanGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        
    def generate(
        self,
        num_rooms: int = 5,
        width: int = 1024,
        height: int = 1024,
        room_types: Optional[List[str]] = None
    ) -> Floorplan:
        """Generate a random floorplan with the specified number of rooms."""
        
        if room_types is None:
            room_types = list(ROOM_COLORS.keys())
        
        rooms = []
        attempts = 0
        max_attempts = 1000
        
        # Generate ID based on seed and params
        fp_id = hashlib.md5(f"{self.seed}_{num_rooms}".encode()).hexdigest()[:8]
        
        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            
            # Pick room type
            room_type = self.rng.choice(room_types)
            size_range = ROOM_SIZE_RANGES.get(room_type, (80, 150))
            
            # Generate room dimensions
            room_width = self.rng.randint(size_range[0], size_range[1])
            room_height = self.rng.randint(size_range[0], size_range[1])
            
            # Try to place room
            margin = 50
            x = self.rng.randint(margin, width - room_width - margin)
            y = self.rng.randint(margin, height - room_height - margin)
            
            new_room = Room(
                id=f"room_{len(rooms)}",
                room_type=room_type,
                x=x, y=y,
                width=room_width,
                height=room_height,
                color=ROOM_COLORS.get(room_type, (200, 200, 200))
            )
            
            # Check for overlaps
            overlaps = any(new_room.intersects(r) for r in rooms)
            if not overlaps:
                rooms.append(new_room)
        
        # Build adjacency graph
        adjacency_graph = {r.id: [] for r in rooms}
        for i, r1 in enumerate(rooms):
            for r2 in rooms[i+1:]:
                if r1.is_adjacent(r2):
                    adjacency_graph[r1.id].append(r2.id)
                    adjacency_graph[r2.id].append(r1.id)
        
        return Floorplan(
            id=fp_id,
            rooms=rooms,
            adjacency_graph=adjacency_graph,
            width=width,
            height=height
        )
    
    def render(
        self,
        floorplan: Floorplan,
        style: str = "default",
        show_labels: bool = True
    ) -> Image.Image:
        """Render floorplan to PIL Image."""
        
        img = Image.new("RGB", (floorplan.width, floorplan.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        for room in floorplan.rooms:
            # Determine color based on style
            if style == "monochrome":
                fill_color = (220, 220, 220)
                outline_color = (0, 0, 0)
            elif style == "blueprint":
                fill_color = (240, 248, 255)  # Alice blue
                outline_color = (0, 0, 139)   # Dark blue
            else:  # default
                fill_color = room.color
                outline_color = (0, 0, 0)
            
            # Draw room
            draw.rectangle(
                [room.x, room.y, room.x + room.width, room.y + room.height],
                fill=fill_color,
                outline=outline_color,
                width=2
            )
            
            # Draw label
            if show_labels:
                label = room.room_type.replace("_", " ").title()
                cx, cy = room.center
                # Simple text centering
                draw.text((cx - 30, cy - 8), label, fill=(0, 0, 0))
        
        return img


# ==============================================================================
# MAIN
# ==============================================================================

def generate_dataset(
    output_dir: str,
    num_floorplans: int = 100,
    seed: int = 42,
    min_rooms: int = 3,
    max_rooms: int = 8
):
    """Generate a dataset of floorplans."""
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    
    generator = FloorplanGenerator(seed=seed)
    manifest = []
    
    for i in range(num_floorplans):
        # Vary seed for each floorplan
        generator.rng = random.Random(seed + i)
        
        num_rooms = random.Random(seed + i).randint(min_rooms, max_rooms)
        fp = generator.generate(num_rooms=num_rooms)
        
        # Render and save image
        img = generator.render(fp, style="default")
        img_path = os.path.join(output_dir, "images", f"{fp.id}.png")
        img.save(img_path)
        
        # Save metadata
        manifest.append({
            "id": fp.id,
            "image_path": f"images/{fp.id}.png",
            "num_rooms": len(fp.rooms),
            "metadata": fp.to_dict()
        })
        
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{num_floorplans} floorplans")
    
    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Dataset saved to {output_dir}")
    print(f"Total floorplans: {len(manifest)}")
    return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="data/generated")
    parser.add_argument("--num", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    generate_dataset(args.output, args.num, args.seed)
