"""
Enhanced prompt templates for publication-grade FloorplanQA benchmark.

Implements three prompting conditions:
1. Direct Prediction (baseline)
2. Minimal Reasoning (one-sentence explanation)
3. Structured Chain-of-Thought (step-by-step with few-shot examples)
"""

from ..core.types import RegionType, SizeCategory
from enum import Enum


class PromptType(Enum):
    """Types of prompts for evaluation."""
    DIRECT = "direct"
    MINIMAL = "minimal"
    STRUCTURED_COT = "structured_cot"


def create_direct_prediction_prompt() -> str:
    """
    Direct prediction prompt (baseline).
    
    No reasoning requested, just the answer.
    
    Returns:
        Direct prompt string
    """
    return """Look at the floorplan and name the type of the mystery room (the unlabeled room).

Respond in JSON format:
{
  "room_type": "your prediction"
}"""


def create_minimal_reasoning_prompt() -> str:
    """
    Minimal reasoning prompt.
    
    Requests one-sentence explanation.
    
    Returns:
        Minimal reasoning prompt string
    """
    return """Look at the floorplan. One room is unlabeled - this is the mystery room.

Briefly explain your reasoning in ONE sentence, then give the room type.

Respond in JSON format:
{
  "reasoning": "One sentence explaining your logic",
  "room_type": "your prediction"
}"""


def create_structured_cot_prompt_with_examples(
    region: RegionType = None,
    size_category: SizeCategory = None
) -> str:
    """
    Structured Chain-of-Thought prompt with few-shot examples.
    
    Guides through 5-step reasoning process with example demonstrations.
    
    Args:
        region: Regional style (optional, for context)
        size_category: Size category (optional, for context)
    
    Returns:
        Structured CoT prompt with examples
    """
    context = ""
    if region and size_category:
        context = f"""
Context for this floorplan:
- Architectural style: {region.value.replace('_', ' ')}
- Size category: {size_category.value}

"""
    
    prompt = f"""You are analyzing a residential floorplan to identify an unlabeled "mystery room".

{context}Follow this structured reasoning process:

Step 1: LOCATE - Describe where the unlabeled room is (e.g., "top left corner, next to kitchen")
Step 2: SIZE - Estimate dimensions (width × height in meters, or relative size like "small", "medium", "large")
Step 3: ADJACENCY - List which labeled rooms it connects to via doors
Step 4: FEATURES - Note distinguishing features (windows, shape, corridor access)
Step 5: PREDICT - State the most likely room type with confidence (low/medium/high)

Keep each step under ~40 words. Total reasoning under 200 words.

---

EXAMPLE 1:

Floorplan description: 4-room apartment, unlabeled room in center

Step 1: The unlabeled room is in the center of the layout, between the kitchen and bedroom.
Step 2: Approximately 3m × 2.5m, medium-small size.
Step 3: Connects to kitchen via door, shares wall with bedroom but no direct door.
Step 4: No windows visible, rectangular shape, acts as circulation space.
Step 5: Most likely a HALLWAY - central position, no windows, connects main areas. Confidence: HIGH

---

EXAMPLE 2:

Floorplan description: 2-bedroom home, unlabeled room adjacent to master bedroom

Step 1: Located next to the master bedroom on the right side of the layout.
Step 2: Very small, approximately 1.5m × 2m.
Step 3: Door from master bedroom, no other connections.
Step 4: No windows, narrow rectangular shape.
Step 5: Most likely a CLOSET - small size, bedroom-adjacent, no windows. Confidence: HIGH

---

EXAMPLE 3:

Floorplan description: Large home, unlabeled room between living and dining areas

Step 1: Positioned between living room and dining room, center-left of layout.
Step 2: Medium size, approximately 4m × 3.5m.
Step 3: Open passage to living room, door to hallway, near dining area.
Step 4: Has window on exterior wall, nearly square shape.
Step 5: Most likely OFFICE/STUDY - medium size, semi-private location, has window. Could also be guest bedroom. Confidence: MEDIUM

---

Now analyze the provided floorplan using the same 5-step process.

Respond in JSON format:
{{
  "step_1_locate": "location description",
  "step_2_size": "size estimate",
  "step_3_adjacency": "connected rooms",
  "step_4_features": "distinguishing features",
  "step_5_prediction": "room type with confidence level",
  "room_type": "your final answer (lowercase with underscores)",
  "reasoning": "brief summary of your conclusion"
}}"""
    
    return prompt


def get_prompt_for_type(
    prompt_type: PromptType,
    region: RegionType = None,
    size_category: SizeCategory = None
) -> str:
    """
    Get the appropriate prompt based on prompt type.
    
    Args:
        prompt_type: Type of prompt to generate
        region: Regional style
        size_category: Size category
    
    Returns:
        Formatted prompt string
    """
    if prompt_type == PromptType.DIRECT:
        return create_direct_prediction_prompt()
    elif prompt_type == PromptType.MINIMAL:
        return create_minimal_reasoning_prompt()
    elif prompt_type == PromptType.STRUCTURED_COT:
        return create_structured_cot_prompt_with_examples(region, size_category)
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")


# Legacy prompts (kept for backward compatibility)
def create_mystery_room_prompt(
    region: RegionType,
    size_category: SizeCategory,
    include_metadata: bool = True
) -> str:
    """Legacy prompt - use get_prompt_for_type() instead."""
    return get_prompt_for_type(PromptType.MINIMAL, region, size_category)
