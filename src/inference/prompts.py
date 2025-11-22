"""Prompt templates for vision-language model inference."""

from ..core.types import RegionType, SizeCategory


def create_mystery_room_prompt(
    region: RegionType,
    size_category: SizeCategory,
    include_metadata: bool = True
) -> str:
    """
    Create a prompt asking the model to identify the mystery room.

    Args:
        region: Regional style of the floorplan
        size_category: Size category
        include_metadata: Whether to include metadata in prompt

    Returns:
        Formatted prompt string
    """
    base_prompt = """You are analyzing a residential floorplan. This image shows a floor plan with multiple labeled rooms. However, one room is intentionally left unlabeled - this is the "mystery room."

Your task:
1. Identify which room is unlabeled (the mystery room)
2. Predict what type of room it is based on:
   - Its size and proportions
   - Its location in the floorplan
   - Which rooms it connects to (via doors)
   - The overall layout and architectural style

3. Explain your reasoning in 1-3 sentences

Please respond in the following JSON format:
{
  "room_type": "your prediction (e.g., closet, office, bedroom, storage, etc.)",
  "reasoning": "your explanation in 1-3 sentences"
}"""

    if include_metadata:
        metadata_info = f"""

Additional context:
- Regional style: {region.value.replace('_', ' ')}
- Size category: {size_category.value}
"""
        base_prompt += metadata_info

    return base_prompt


def create_simple_prompt() -> str:
    """
    Create a simpler prompt without metadata.

    Returns:
        Simple prompt string
    """
    return """Look at this floorplan. One room is not labeled. What type of room do you think it is and why?

Respond in JSON format:
{
  "room_type": "your prediction",
  "reasoning": "your explanation"
}"""


def create_detailed_prompt(
    region: RegionType,
    size_category: SizeCategory,
    total_rooms: int
) -> str:
    """
    Create a detailed prompt with rich context.

    Args:
        region: Regional style
        size_category: Size category
        total_rooms: Total number of rooms in floorplan

    Returns:
        Detailed prompt string
    """
    return f"""You are an expert in residential architecture and spatial reasoning.

You are looking at a {size_category.value}-sized home with a {region.value.replace('_', ' ')} architectural style. The floorplan contains {total_rooms} rooms total.

Most rooms are labeled with their type (kitchen, bedroom, bathroom, etc.), but ONE room has been intentionally left unlabeled. This is your "mystery room."

Your task is to identify the unlabeled room and predict its type. Consider:

1. **Size and proportions**: Does the room's area match typical dimensions for certain room types?
2. **Adjacency**: Which rooms does it connect to? Certain rooms typically neighbor each other.
3. **Position**: Where is it in the layout? (e.g., bedrooms rarely connect to kitchens)
4. **Regional patterns**: Different regions have different typical layouts
5. **Architectural logic**: Does the overall floorplan suggest a specific room is missing?

Common room types to consider:
- Closet (small, adjacent to bedrooms)
- Office/Study (medium, could be mistaken for bedroom)
- Storage room
- Guest bedroom
- Pantry (small, adjacent to kitchen)
- Laundry room
- Utility room

Please provide your answer in JSON format:
{{
  "room_type": "your prediction (lowercase, use underscores for spaces)",
  "reasoning": "detailed explanation (1-3 sentences)"
}}"""


def create_chain_of_thought_prompt() -> str:
    """
    Create a prompt that encourages step-by-step reasoning.

    Returns:
        Chain-of-thought prompt
    """
    return """Analyze this floorplan step by step:

Step 1: Identify which room is unlabeled
Step 2: Measure or estimate its approximate size
Step 3: Note which labeled rooms it connects to
Step 4: Consider its position in the overall layout
Step 5: Make your prediction

Think through each step, then provide your final answer in JSON format:
{
  "unlabeled_room_location": "brief description of where it is",
  "approximate_size": "small/medium/large",
  "connected_to": "list the adjacent rooms",
  "room_type": "your final prediction",
  "reasoning": "your reasoning (1-3 sentences)"
}"""


# Default prompt to use
DEFAULT_PROMPT = create_simple_prompt()
