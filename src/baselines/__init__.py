"""
Simple baseline models for FloorplanQA benchmark.

Implements non-ML baselines to establish performance bounds:
1. MajorityClassBaseline - Always predicts most common room type
2. RandomBaseline - Uniform random selection
3. HeuristicBaseline - Rule-based logic using size and adjacency
"""

import random
from typing import Dict, Any, List
from collections import Counter

from ..core.models import Floorplan, Room
from ..core.types import RoomType


class BaselineModel:
    """Base class for baseline models."""
    
    def __init__(self, name: str):
        self.name = name
        
    def fit(self, floorplans: List[Floorplan]) -> None:
        """Learn from training data (if applicable)."""
        pass
        
    def predict(self, floorplan: Floorplan) -> str:
        """Predict the mystery room type."""
        raise NotImplementedError
        
    def predict_with_confidence(self, floorplan: Floorplan) -> tuple[str, float]:
        """Predict with confidence score."""
        prediction = self.predict(floorplan)
        return prediction, 1.0  # Default confidence


class MajorityClassBaseline(BaselineModel):
    """Always predicts the most common room type from training data."""
    
    def __init__(self):
        super().__init__("Majority Class")
        self.most_common_type = None
        
    def fit(self, floorplans: List[Floorplan]) -> None:
        """Learn the most common mystery room type."""
        room_types = [fp.mystery_room.room_type.value for fp in floorplans]
        counter = Counter(room_types)
        self.most_common_type = counter.most_common(1)[0][0]
        print(f"Majority class baseline: Always predicting '{self.most_common_type}'")
        
    def predict(self, floorplan: Floorplan) -> str:
        """Always return the most common type."""
        if self.most_common_type is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return self.most_common_type


class RandomBaseline(BaselineModel):
    """Randomly selects from possible room types."""
    
    def __init__(self, seed: int = 42):
        super().__init__("Random")
        self.rng = random.Random(seed)
        self.room_types = [
            "bedroom", "bathroom", "kitchen", "living_room", "office"
        ]
        
    def predict(self, floorplan: Floorplan) -> str:
        """Randomly select a room type."""
        return self.rng.choice(self.room_types)
        
    def predict_with_confidence(self, floorplan: Floorplan) -> tuple[str, float]:
        """Random prediction with uniform confidence."""
        prediction = self.predict(floorplan)
        confidence = 1.0 / len(self.room_types)  # Uniform probability
        return prediction, confidence


class HeuristicBaseline(BaselineModel):
    """Rule-based heuristic using size and adjacency information."""
    
    def __init__(self):
        super().__init__("Heuristic")
        
    def predict(self, floorplan: Floorplan) -> str:
        """Apply heuristic rules to predict room type."""
        mystery_room = floorplan.mystery_room
        if not mystery_room:
            return "bedroom"  # Fallback
            
        area = mystery_room.area
        adjacent_rooms = floorplan.get_adjacent_rooms(mystery_room.id)
        adjacent_types = [r.room_type.value for r in adjacent_rooms]
        
        # Rule 1: Very small rooms (< 6m²) are likely bathrooms or closets
        if area < 6.0:
            # If adjacent to bedroom, likely bathroom
            if "bedroom" in adjacent_types:
                return "bathroom"
            # Otherwise could be office (small study)
            return "office"
            
        # Rule 2: Large rooms (> 20m²) are likely living rooms or kitchens
        if area > 20.0:
            # If has many connections, likely living room (central)
            if len(adjacent_rooms) >= 3:
                return "living_room"
            # Otherwise kitchen
            return "kitchen"
            
        # Rule 3: Medium rooms adjacent to bathroom are likely bedrooms
        if "bathroom" in adjacent_types:
            return "bedroom"
            
        # Rule 4: Medium rooms with few connections might be office
        if len(adjacent_rooms) <= 1:
            return "office"
            
        # Rule 5: Check for typical kitchen adjacency (near living room)
        if "living_room" in adjacent_types and area > 10.0:
            return "kitchen"
            
        # Default fallback: bedroom (most common residential room)
        return "bedroom"
        
    def predict_with_confidence(self, floorplan: Floorplan) -> tuple[str, float]:
        """Predict with rule-based confidence."""
        mystery_room = floorplan.mystery_room
        prediction = self.predict(floorplan)
        
        # Assign confidence based on how clear the signals are
        area = mystery_room.area
        adjacent_rooms = floorplan.get_adjacent_rooms(mystery_room.id)
        
        # High confidence for extreme sizes
        if area < 5.0 or area > 25.0:
            confidence = 0.8
        # Medium confidence for clear adjacency patterns
        elif len(adjacent_rooms) >= 3 or "bathroom" in [r.room_type.value for r in adjacent_rooms]:
            confidence = 0.6
        # Low confidence otherwise
        else:
            confidence = 0.4
            
        return prediction, confidence


def evaluate_baseline(
    model: BaselineModel,
    floorplans: List[Floorplan],
    split_name: str = "test"
) -> Dict[str, Any]:
    """
    Evaluate a baseline model on a set of floorplans.
    
    Args:
        model: Baseline model to evaluate
        floorplans: List of floorplans to test on
        split_name: Name of the split (for logging)
        
    Returns:
        Dictionary with accuracy and other metrics
    """
    correct = 0
    total = len(floorplans)
    predictions = []
    
    for fp in floorplans:
        pred = model.predict(fp)
        actual = fp.mystery_room.room_type.value
        
        predictions.append({
            "floorplan_id": fp.id,
            "predicted": pred,
            "actual": actual,
            "correct": pred == actual
        })
        
        if pred == actual:
            correct += 1
            
    accuracy = correct / total if total > 0 else 0.0
    
    # Calculate per-class accuracy
    per_class_correct = Counter()
    per_class_total = Counter()
    
    for pred_data in predictions:
        actual = pred_data["actual"]
        per_class_total[actual] += 1
        if pred_data["correct"]:
            per_class_correct[actual] += 1
            
    per_class_accuracy = {
        room_type: per_class_correct[room_type] / per_class_total[room_type]
        if per_class_total[room_type] > 0 else 0.0
        for room_type in per_class_total
    }
    
    return {
        "model": model.name,
        "split": split_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "per_class_accuracy": per_class_accuracy,
        "predictions": predictions
    }
