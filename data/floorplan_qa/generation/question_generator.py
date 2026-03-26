#!/usr/bin/env python3
"""
FloorplanQA: Question Generator
Generates multi-choice QA pairs from floorplan metadata.
"""

import os
import json
import random
import hashlib
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Question:
    id: str
    floorplan_id: str
    question_type: str
    question_text: str
    choices: List[str]
    correct_answer: str
    correct_index: int
    difficulty: str
    metadata: Dict[str, Any]


class QuestionGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        
    def generate_all(self, floorplan_data: dict) -> List[Question]:
        """Generate all question types for a floorplan."""
        questions = []
        
        rooms = floorplan_data.get("rooms", [])
        graph = floorplan_data.get("adjacency_graph", {})
        fp_id = floorplan_data.get("id", "unknown")
        
        if len(rooms) < 2:
            return questions
        
        # Room count questions
        questions.extend(self._room_count_questions(fp_id, rooms))
        
        # Adjacency questions
        questions.extend(self._adjacency_questions(fp_id, rooms, graph))
        
        # Area comparison questions
        questions.extend(self._area_comparison_questions(fp_id, rooms))
        
        # Room identification questions
        questions.extend(self._room_identification_questions(fp_id, rooms, floorplan_data))
        
        return questions
    
    def _room_count_questions(self, fp_id: str, rooms: List[dict]) -> List[Question]:
        """How many [room_type] are in this floorplan?"""
        questions = []
        
        # Count room types
        type_counts = {}
        for r in rooms:
            rt = r["room_type"]
            type_counts[rt] = type_counts.get(rt, 0) + 1
        
        for room_type, correct_count in type_counts.items():
            # Generate wrong answers
            wrong_answers = [correct_count + i for i in [-2, -1, 1, 2] if correct_count + i >= 0]
            wrong_answers = [str(w) for w in wrong_answers if w != correct_count][:3]
            
            if len(wrong_answers) < 3:
                wrong_answers.extend(["0", "1", "2"])
            wrong_answers = list(set(wrong_answers) - {str(correct_count)})[:3]
            
            choices = [str(correct_count)] + wrong_answers
            self.rng.shuffle(choices)
            correct_idx = choices.index(str(correct_count))
            
            q_id = hashlib.md5(f"{fp_id}_count_{room_type}".encode()).hexdigest()[:8]
            
            questions.append(Question(
                id=q_id,
                floorplan_id=fp_id,
                question_type="room_count",
                question_text=f"How many {room_type.replace('_', ' ')}s are in this floorplan?",
                choices=choices,
                correct_answer=str(correct_count),
                correct_index=correct_idx,
                difficulty="easy",
                metadata={"room_type": room_type, "count": correct_count}
            ))
        
        return questions
    
    def _adjacency_questions(self, fp_id: str, rooms: List[dict], graph: Dict[str, List[str]]) -> List[Question]:
        """Is [room_A] adjacent to [room_B]?"""
        questions = []
        
        if len(rooms) < 2:
            return questions
        
        # Pick a pair of rooms
        for i, r1 in enumerate(rooms[:5]):  # Limit to avoid explosion
            for r2 in rooms[i+1:i+3]:
                r1_id = r1["id"]
                r2_id = r2["id"]
                r1_type = r1["room_type"].replace("_", " ")
                r2_type = r2["room_type"].replace("_", " ")
                
                is_adjacent = r2_id in graph.get(r1_id, [])
                correct_answer = "Yes" if is_adjacent else "No"
                
                choices = ["Yes", "No", "Cannot determine", "They are the same room"]
                correct_idx = choices.index(correct_answer)
                
                q_id = hashlib.md5(f"{fp_id}_adj_{r1_id}_{r2_id}".encode()).hexdigest()[:8]
                
                questions.append(Question(
                    id=q_id,
                    floorplan_id=fp_id,
                    question_type="adjacency",
                    question_text=f"Is the {r1_type} adjacent to the {r2_type}?",
                    choices=choices,
                    correct_answer=correct_answer,
                    correct_index=correct_idx,
                    difficulty="medium",
                    metadata={"room_a": r1_id, "room_b": r2_id, "is_adjacent": is_adjacent}
                ))
        
        return questions
    
    def _area_comparison_questions(self, fp_id: str, rooms: List[dict]) -> List[Question]:
        """Which is larger: [room_A] or [room_B]?"""
        questions = []
        
        if len(rooms) < 2:
            return questions
        
        # Pick pairs with different sizes
        for i, r1 in enumerate(rooms[:4]):
            for r2 in rooms[i+1:i+2]:
                r1_area = r1["width"] * r1["height"]
                r2_area = r2["width"] * r2["height"]
                
                if r1_area == r2_area:
                    continue
                
                r1_type = r1["room_type"].replace("_", " ")
                r2_type = r2["room_type"].replace("_", " ")
                
                if r1_area > r2_area:
                    correct_answer = f"The {r1_type}"
                else:
                    correct_answer = f"The {r2_type}"
                
                choices = [
                    f"The {r1_type}",
                    f"The {r2_type}",
                    "They are the same size",
                    "Cannot determine from this image"
                ]
                correct_idx = choices.index(correct_answer)
                
                q_id = hashlib.md5(f"{fp_id}_area_{r1['id']}_{r2['id']}".encode()).hexdigest()[:8]
                
                questions.append(Question(
                    id=q_id,
                    floorplan_id=fp_id,
                    question_type="area_comparison",
                    question_text=f"Which room is larger: the {r1_type} or the {r2_type}?",
                    choices=choices,
                    correct_answer=correct_answer,
                    correct_index=correct_idx,
                    difficulty="medium",
                    metadata={"room_a": r1["id"], "room_b": r2["id"], "area_a": r1_area, "area_b": r2_area}
                ))
        
        return questions
    
    def _room_identification_questions(self, fp_id: str, rooms: List[dict], fp_data: dict) -> List[Question]:
        """What room is in the [direction] corner?"""
        questions = []
        
        if len(rooms) < 2:
            return questions
        
        width = fp_data.get("width", 1024)
        height = fp_data.get("height", 1024)
        
        corners = {
            "top-left": (0, 0),
            "top-right": (width, 0),
            "bottom-left": (0, height),
            "bottom-right": (width, height)
        }
        
        for corner_name, (cx, cy) in corners.items():
            # Find closest room to corner
            closest_room = None
            min_dist = float('inf')
            
            for r in rooms:
                room_cx = r["x"] + r["width"] // 2
                room_cy = r["y"] + r["height"] // 2
                dist = ((room_cx - cx) ** 2 + (room_cy - cy) ** 2) ** 0.5
                
                if dist < min_dist:
                    min_dist = dist
                    closest_room = r
            
            if closest_room is None:
                continue
            
            correct_type = closest_room["room_type"].replace("_", " ")
            
            # Generate wrong answers from other room types
            other_types = list(set(r["room_type"].replace("_", " ") for r in rooms if r["id"] != closest_room["id"]))
            wrong_answers = other_types[:3]
            if len(wrong_answers) < 3:
                wrong_answers.extend(["storage", "garage", "patio"][:3 - len(wrong_answers)])
            
            choices = [correct_type] + wrong_answers[:3]
            self.rng.shuffle(choices)
            correct_idx = choices.index(correct_type)
            
            q_id = hashlib.md5(f"{fp_id}_corner_{corner_name}".encode()).hexdigest()[:8]
            
            questions.append(Question(
                id=q_id,
                floorplan_id=fp_id,
                question_type="room_identification",
                question_text=f"What type of room is closest to the {corner_name} corner of the floorplan?",
                choices=choices,
                correct_answer=correct_type,
                correct_index=correct_idx,
                difficulty="medium",
                metadata={"corner": corner_name, "room_id": closest_room["id"]}
            ))
        
        return questions


def generate_questions(manifest_path: str, output_path: str, seed: int = 42):
    """Generate questions for all floorplans in manifest."""
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    generator = QuestionGenerator(seed=seed)
    all_questions = []
    
    for item in manifest:
        fp_data = item.get("metadata", {})
        questions = generator.generate_all(fp_data)
        
        for q in questions:
            q_dict = asdict(q)
            q_dict["image_path"] = item["image_path"]
            all_questions.append(q_dict)
    
    with open(output_path, "w") as f:
        json.dump(all_questions, f, indent=2)
    
    print(f"Generated {len(all_questions)} questions")
    print(f"Saved to {output_path}")
    
    # Print breakdown
    type_counts = {}
    for q in all_questions:
        qt = q["question_type"]
        type_counts[qt] = type_counts.get(qt, 0) + 1
    
    print("\nBreakdown by type:")
    for qt, count in sorted(type_counts.items()):
        print(f"  {qt}: {count}")
    
    return all_questions


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default="data/generated/manifest.json")
    parser.add_argument("--output", type=str, default="data/generated/questions.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    generate_questions(args.manifest, args.output, args.seed)
