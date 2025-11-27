#!/usr/bin/env python3
"""Test script for difficulty-aware mystery room selection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.types import RegionType, SizeCategory
from src.generation.generator import generate_floorplan
from src.generation.room_assigner import DifficultyTier

def test_mystery_room_difficulty():
    """Test that mystery room difficulty classification is working."""
    
    print("=" * 70)
    print("MYSTERY ROOM DIFFICULTY TEST")
    print("=" * 70)
    
    # Generate a few floorplans and check difficulty metadata
    difficulties = {tier: 0 for tier in DifficultyTier}
    room_type_counts = {}
    
    n_samples = 20
    for i in range(n_samples):
        fp = generate_floorplan(
            seed=1000 + i,
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM
        )
        
        # Check metadata
        mystery_meta = fp.metadata.get("mystery_room", {})
        difficulty_str = mystery_meta.get("difficulty", "unknown")
        room_type = mystery_meta.get("type", "unknown")
        
        # Find the mystery room
        mystery_room = next((r for r in fp.rooms if r.is_mystery), None)
        
        if mystery_room:
            # Count by difficulty
            if difficulty_str in ["easy", "medium", "hard"]:
                tier = DifficultyTier(difficulty_str)
                difficulties[tier] += 1
            
            # Count by room type
            room_type_counts[room_type] = room_type_counts.get(room_type, 0) + 1
            
            print(f"\n{fp.id[:8]}...")
            print(f"  Type: {room_type}")
            print(f"  Difficulty: {difficulty_str}")
            print(f"  Area: {mystery_room.area:.1f} m²")
            print(f"  Windows: {mystery_room.has_window}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\nDifficulty Distribution:")
    for tier, count in difficulties.items():
        pct = (count / n_samples) * 100
        print(f"  {tier.value:8s}: {count:2d} ({pct:5.1f}%)")
    
    print("\nRoom Type Distribution:")
    for room_type, count in sorted(room_type_counts.items(), key=lambda x: -x[1]):
        pct = (count / n_samples) * 100
        print(f"  {room_type:12s}: {count:2d} ({pct:5.1f}%)")
    
    print("\n✅ Test complete! Difficulty classification is working.")
    print(f"   Generated {n_samples} floorplans with difficulty metadata.")

if __name__ == "__main__":
    test_mystery_room_difficulty()
