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


def create_chain_of_thought_prompt(
    region: RegionType,
    size_category: SizeCategory
) -> str:
    """
    Create a prompt that encourages step-by-step reasoning.
    
    Args:
        region: Regional style
        size_category: Size category

    Returns:
        Chain-of-thought prompt
    """
    prompt = f"""You are analyzing a residential floorplan.
Context:
- Style: {region.value.replace('_', ' ')}
- Size: {size_category.value}

Analyze this floorplan step by step to identify the unlabeled "mystery room":

Step 1: Identify which room is unlabeled
Step 2: Measure or estimate its approximate size relative to other rooms
Step 3: Note which labeled rooms it connects to (adjacencies)
Step 4: Consider its position in the overall layout and flow
Step 5: Make your prediction based on architectural logic

Think through each step, then provide your final answer in JSON format:
{{
  "step_1_identification": "location of unlabeled room",
  "step_2_size_analysis": "size observation",
  "step_3_adjacency_analysis": "connected rooms",
  "step_4_layout_analysis": "positional logic",
  "room_type": "your final prediction",
  "reasoning": "summary of your conclusion"
}}"""
    return prompt


# Default prompt to use
DEFAULT_PROMPT = create_simple_prompt()


def create_critique_prompt(
    region: RegionType,
    size_category: SizeCategory
) -> str:
    """
    Create a prompt asking for architectural critique.
    
    Args:
        region: Regional style
        size_category: Size category
        
    Returns:
        Critique prompt string
    """
    return f"""You are a senior architect reviewing a floorplan design.
    
Context:
- Style: {region.value.replace('_', ' ')}
- Size: {size_category.value}

Your task is to critique this layout for realism and functionality.
1. Identify any "odd" or unrealistic elements (e.g., strange room sizes, bad adjacencies).
2. Evaluate if the flow makes sense for a human resident.
3. Rate the realism on a scale of 1-10.

Provide your critique in JSON format:
{{
  "realism_score": 5,
  "critique": "Your detailed critique here...",
  "flaws": ["list", "of", "specific", "flaws"],
  "strengths": ["list", "of", "strengths"]
}}"""


def create_counterfactual_prompt(
    target_room_type: str,
    alternative_room_type: str
) -> str:
    """
    Create a counterfactual reasoning prompt.
    
    Args:
        target_room_type: The actual type of the mystery room (or a hypothesis)
        alternative_room_type: An alternative type to consider
        
    Returns:
        Counterfactual prompt string
    """
    return f"""Consider the unlabeled mystery room in this floorplan.

Hypothesis A: The room is a {target_room_type}.
Hypothesis B: The room is a {alternative_room_type}.

Compare these two hypotheses.
1. Which one fits the layout better?
2. What evidence supports A?
3. What evidence supports B?
4. What would need to change in the layout to make the OTHER hypothesis valid?

Provide your analysis in JSON format:
{{
  "preferred_hypothesis": "A or B",
  "reasoning": "Explanation of why one fits better",
  "counterfactual_analysis": "What would make the other one work?"
}}"""

# ==========================================
# PHASE 5: KITCHEN BLINDNESS ABLATION PROMPTS
# ==========================================

def create_ablation_baseline_prompt() -> str:
    """Condition 1: Baseline prediction."""
    return """This is a 2D architectural floorplan. One room is labeled with a "?". 
Based on its size, position, and connections to other rooms, what type 
of room do you think it is? Choose from: bedroom, bathroom, kitchen, 
living_room, office. Respond with your answer and 1-3 sentences of reasoning.

Respond in JSON format:
{
  "room_type": "predicted_type",
  "reasoning": "your explanation"
}"""

def create_ablation_spatial_prompt() -> str:
    """Condition 2: Forced spatial enumeration before prediction."""
    return """This is a 2D architectural floorplan. One room is labeled with a "?".

Before making your prediction, you must answer these questions:
1. Approximately how large is the mystery room compared to others on the plan?
2. Which labeled rooms share a direct door connection with it?
3. Does it appear to have exterior wall access (along the outer boundary)?
4. Is it positioned near the entrance, center, or back of the floor?

After answering all four questions, predict the room type. 
Choose from: bedroom, bathroom, kitchen, living_room, office.

Respond in JSON format:
{
  "q1_size": "answer",
  "q2_connections": "answer",
  "q3_exterior": "answer",
  "q4_position": "answer",
  "room_type": "predicted_type"
}"""

def create_ablation_rules_prompt() -> str:
    """Condition 3: Explicit architectural rules injected."""
    return """This is a 2D architectural floorplan. One room is labeled with a "?".

Use these architectural constraints to guide your reasoning:
- Kitchens: typically have exterior wall access, adjacent to dining or living areas
- Bathrooms: small, adjacent to bedrooms or hallways, rarely have exterior access
- Bedrooms: medium-to-large, private, away from entrance and social spaces
- Living rooms: large, near entrance, connected to multiple rooms
- Offices: medium, can be isolated, sometimes share walls with bedrooms

Given these rules, what is the mystery room? 
Choose from: bedroom, bathroom, kitchen, living_room, office.

Respond in JSON format:
{
  "reasoning": "your explanation using the rules",
  "room_type": "predicted_type"
}"""

def create_ablation_exclusion_prompt() -> str:
    """Condition 4: Exclusion prompt (bedroom blocked)."""
    return """This is a 2D architectural floorplan. One room is labeled with a "?".

Important: the mystery room is definitively NOT a bedroom. 

Given its size, connections, and position relative to other rooms, 
what type of room is it? Choose from: bathroom, kitchen, living_room, office.
Explain your reasoning in 1-3 sentences.

Respond in JSON format:
{
  "reasoning": "your explanation",
  "room_type": "predicted_type"
}"""

def create_ablation_contrastive_prompt() -> str:
    """Condition 5: Contrastive scoring."""
    return """This is a 2D architectural floorplan. One room is labeled with a "?".

Rate the likelihood that the mystery room is each of the following types, 
using a scale of 1 (very unlikely) to 5 (very likely).

Then state your final prediction (the highest-rated type) and one sentence of justification.

Respond in JSON format:
{
  "scores": {
    "bedroom": 1,
    "bathroom": 1,
    "kitchen": 1,
    "living_room": 1,
    "office": 1
  },
  "room_type": "predicted_type",
  "reasoning": "one sentence justification"
}"""
