"""
Balanced floorplan generator for creating publication-grade datasets.

This module provides the BalancedGenerator class, which wraps the standard
FloorplanGenerator to enforce strict quotas on difficulty tiers and room types.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
from tqdm import tqdm

from ..core.models import Floorplan
from ..core.types import RoomType, RegionType, SizeCategory
from .generator import generate_floorplan
from .room_assigner import CANDIDATE_MYSTERY_TYPES, DifficultyTier


class BalancedGenerator:
    """
    Generator that enforces strict quotas for dataset balance.
    
    Ensures:
    1. Equal distribution of difficulty tiers (Easy/Medium/Hard)
    2. Minimum representation of each mystery room type
    3. Balanced regional representation
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Quota tracking
        self.generated_counts = {
            "difficulty": Counter(),
            "room_type": Counter(),
            "region": Counter()
        }
        
    def generate_balanced_dataset(
        self,
        target_count: int,
        regions: List[RegionType],
        min_samples_per_room_type: int = 400
    ) -> List[Floorplan]:
        """
        Generate a balanced dataset of floorplans.
        
        Args:
            target_count: Total number of floorplans to generate
            regions: List of regions to sample from
            min_samples_per_room_type: Minimum samples required for each mystery type
            
        Returns:
            List of generated Floorplan objects
        """
        dataset = []
        pbar = tqdm(total=target_count, desc="Generating balanced dataset")
        
        # Targets
        target_per_difficulty = target_count // 3
        
        attempts = 0
        max_attempts = target_count * 50  # Prevent infinite loops
        
        while len(dataset) < target_count and attempts < max_attempts:
            attempts += 1
            
            # 1. Determine what we need
            needed_difficulty = self._get_needed_difficulty(target_per_difficulty)
            needed_room_type = self._get_needed_room_type(min_samples_per_room_type)
            
            # 2. Select parameters to encourage needed traits
            region = self.rng.choice(regions)
            size_category = self._select_size_for_difficulty(needed_difficulty)
            
            # 3. Generate candidate
            # Use a derived seed for reproducibility
            candidate_seed = self.seed + attempts
            
            try:
                floorplan = generate_floorplan(
                    seed=candidate_seed,
                    region=region,
                    size_category=size_category
                )
                
                # v1.2 Traceability
                floorplan.metadata["generation"] = {
                    "seed": candidate_seed,
                    "attempt_index": attempts,
                    "global_seed": self.seed
                }
            except Exception:
                continue
                
            # 4. Check if candidate meets criteria
            if not self._accept_candidate(
                floorplan, 
                needed_difficulty, 
                needed_room_type,
                target_per_difficulty
            ):
                continue
                
            # 5. Accept and update counters
            self._update_counters(floorplan)
            dataset.append(floorplan)
            pbar.update(1)
            pbar.set_postfix({
                "Easy": self.generated_counts["difficulty"][DifficultyTier.EASY],
                "Med": self.generated_counts["difficulty"][DifficultyTier.MEDIUM],
                "Hard": self.generated_counts["difficulty"][DifficultyTier.HARD]
            })
            
        pbar.close()
        
        if len(dataset) < target_count:
            print(f"Warning: Could not fully satisfy quotas. Generated {len(dataset)}/{target_count}")
            
        return dataset
        
    def _get_needed_difficulty(self, target: int) -> Optional[DifficultyTier]:
        """Return a difficulty tier that hasn't met its quota yet."""
        # Prioritize Hard > Medium > Easy since Hard is rarest
        if self.generated_counts["difficulty"][DifficultyTier.HARD] < target:
            return DifficultyTier.HARD
        if self.generated_counts["difficulty"][DifficultyTier.MEDIUM] < target:
            return DifficultyTier.MEDIUM
        if self.generated_counts["difficulty"][DifficultyTier.EASY] < target:
            return DifficultyTier.EASY
        return None  # All full (shouldn't happen in main loop logic)
        
    def _get_needed_room_type(self, min_target: int) -> Optional[RoomType]:
        """Return a room type that is under-represented."""
        # Check all candidate types
        for r_type in CANDIDATE_MYSTERY_TYPES:
            if self.generated_counts["room_type"][r_type] < min_target:
                return r_type
        return None
        
    def _select_size_for_difficulty(self, difficulty: Optional[DifficultyTier]) -> SizeCategory:
        """Heuristic to select size category based on desired difficulty."""
        if difficulty == DifficultyTier.HARD:
            # Hard floorplans tend to be Micro (cramped) or Extra Large (complex)
            return self.rng.choice([SizeCategory.MICRO, SizeCategory.SMALL])
        elif difficulty == DifficultyTier.EASY:
            # Easy floorplans tend to be Medium/Large with clear layouts
            return self.rng.choice([SizeCategory.MEDIUM, SizeCategory.LARGE])
        else:
            return self.rng.choice(list(SizeCategory))
            
    def _accept_candidate(
        self, 
        floorplan: Floorplan, 
        needed_difficulty: Optional[DifficultyTier],
        needed_room_type: Optional[RoomType],
        difficulty_limit: int
    ) -> bool:
        """Decide whether to accept a generated floorplan."""
        
        # 1. Check difficulty quota
        # If we specifically need a tier, reject others
        # If we don't specifically need one (balanced phase), just ensure we don't exceed limit
        # Extract difficulty from metadata
        difficulty_val = floorplan.metadata["mystery_room"]["difficulty"]
        difficulty = DifficultyTier(difficulty_val)
        
        current_diff_count = self.generated_counts["difficulty"][difficulty]
        if current_diff_count >= difficulty_limit:
            return False
            
        # 2. Check room type needs
        # If we are hunting for a specific rare type (e.g. Office), reject others
        # unless the floorplan is also Hard (which is rare and valuable)
        if needed_room_type:
            is_needed_type = floorplan.mystery_room.room_type == needed_room_type
            is_hard = difficulty == DifficultyTier.HARD
            
            if not is_needed_type and not is_hard:
                # Reject common types if we desperately need a rare one
                # But accept Hard ones because they are hard to get
                return False
                
        return True

    def _update_counters(self, floorplan: Floorplan):
        """Update internal counters with the accepted floorplan."""
        difficulty_val = floorplan.metadata["mystery_room"]["difficulty"]
        difficulty = DifficultyTier(difficulty_val)
        
        self.generated_counts["difficulty"][difficulty] += 1
        self.generated_counts["room_type"][floorplan.mystery_room.room_type] += 1
        self.generated_counts["region"][floorplan.region] += 1
