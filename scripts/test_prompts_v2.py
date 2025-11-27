#!/usr/bin/env python3
"""Test the three prompting conditions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.prompts_v2 import PromptType, get_prompt_for_type
from src.core.types import RegionType, SizeCategory

def test_prompts():
    """Test all three prompt types."""
    
    print("=" * 70)
    print("PROMPT CONDITIONS TEST")
    print("=" * 70)
    
    region = RegionType.MODERN_URBAN
    size_cat = SizeCategory.MEDIUM
    
    for prompt_type in PromptType:
        print(f"\n{'='*70}")
        print(f"{prompt_type.value.upper()} PROMPT")
        print("=" * 70)
        
        prompt = get_prompt_for_type(prompt_type, region, size_cat)
        print(prompt)
        print(f"\nLength: {len(prompt)} characters")
        print(f"Word count: {len(prompt.split())}")
    
    print("\n" + "=" * 70)
    print("✅ All three prompt types generated successfully!")
    print("=" * 70)

if __name__ == "__main__":
    test_prompts()
