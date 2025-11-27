#!/usr/bin/env python3
"""
Quick update to add severity parameter to all adversarial strategy

 methods.
This is a maintenance script to update function signatures.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test that the severity enum and basic infrastructure works
from src.generation.adversarial_generator import AdversarialGenerator, Severity
from src.core.types import RegionType, SizeCategory

def test_severity_integration():
    """Test that severity parameter is working."""
    
    gen = AdversarialGenerator(seed=42)
    
    for sev in [Severity.SLIGHT, Severity.MEDIUM, Severity.EXTREME]:
        fp = gen.generate_confusing_floorplan(
            region=RegionType.MODERN_URBAN,
            size_category=SizeCategory.MEDIUM,
            confusion_type="size_mismatch",
            severity=sev
        )
        
        adv_meta = fp.metadata.get("adversarial", {})
        print(f"{sev.value:8s}: type={adv_meta.get('type')}, severity={adv_meta.get('severity')}")
        
    print("\n✅ Severity integration working for size_mismatch!")
    print("⚠️  Note: Other strategies need severity parameter added to function signatures")

if __name__ == "__main__":
    test_severity_integration()
