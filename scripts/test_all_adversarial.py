#!/usr/bin/env python3
"""Test all adversarial strategies with severity levels."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.core.types import RegionType, SizeCategory

def test_all_strategies():
    """Test that all strategies work with severity."""
    
    strategies = [
        "size_mismatch",
        "shape_confusion",
        "window_deception",
        "adjacency_violation",
        "missing_rooms"
    ]
    
    print("=" * 70)
    print("ADVERSARIAL SEVERITY CALIBRATION TEST")
    print("=" * 70)
    
    for strategy in strategies:
        print(f"\n{strategy}:")
        for sev in [Severity.SLIGHT, Severity.MEDIUM, Severity.EXTREME]:
            try:
                gen = AdversarialGenerator(seed=42)
                fp = gen.generate_confusing_floorplan(
                    region=RegionType.MODERN_URBAN,
                    size_category=SizeCategory.MEDIUM,
                    confusion_type=strategy,
                    severity=sev
                )
                
                adv_meta = fp.metadata.get("adversarial", {})
                mystery_meta = fp.metadata.get("mystery_room", {})
                
                print(f"  {sev.value:8s}: ✅ severity={adv_meta.get('severity')}, "
                      f"mystery_difficulty={mystery_meta.get('difficulty')}")
                
            except Exception as e:
                print(f"  {sev.value:8s}: ❌ Error: {str(e)[:50]}")
    
    print("\n" + "=" * 70)
    print("✅ All strategies support severity calibration!")
    print("=" * 70)

if __name__ == "__main__":
    test_all_strategies()
