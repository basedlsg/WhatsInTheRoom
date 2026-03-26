#!/usr/bin/env python3
"""
FloorplanQA: VLM Runner Abstraction
Unified interface for multiple vision-language models.
"""

import os
import base64
import json
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VLMResponse:
    model: str
    question_id: str
    predicted_answer: str
    predicted_index: int
    raw_response: str
    latency_ms: float
    error: Optional[str] = None


class VLMBackend(ABC):
    """Abstract base class for VLM backends."""
    
    @abstractmethod
    def query(
        self,
        image_path: str,
        question: str,
        choices: List[str],
        prompt_style: str = "structured"
    ) -> VLMResponse:
        pass
    
    @abstractmethod
    def name(self) -> str:
        pass


class GeminiVLM(VLMBackend):
    """Google Gemini Pro Vision backend."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        import google.generativeai as genai
        
        # Use project's existing API key with fallback
        api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyCe_O4tWkG1B_vJD_tXQ_-UAKvLJHokhzQ")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def name(self) -> str:
        return f"gemini:{self.model_name}"
    
    def query(
        self,
        image_path: str,
        question: str,
        choices: List[str],
        prompt_style: str = "structured"
    ) -> VLMResponse:
        from PIL import Image
        
        start_time = time.time()
        
        try:
            img = Image.open(image_path)
            prompt = self._build_prompt(question, choices, prompt_style)
            
            response = self.model.generate_content([prompt, img])
            raw_text = response.text.strip()
            
            # Parse answer
            predicted_answer, predicted_index = self._parse_answer(raw_text, choices)
            
            latency = (time.time() - start_time) * 1000
            
            return VLMResponse(
                model=self.name(),
                question_id="",
                predicted_answer=predicted_answer,
                predicted_index=predicted_index,
                raw_response=raw_text,
                latency_ms=latency
            )
        
        except Exception as e:
            return VLMResponse(
                model=self.name(),
                question_id="",
                predicted_answer="",
                predicted_index=-1,
                raw_response="",
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    def _build_prompt(self, question: str, choices: List[str], style: str) -> str:
        choice_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices)])
        
        if style == "minimal":
            return f"{question}\n{choice_str}\n\nAnswer with just the letter (A, B, C, or D):"
        
        elif style == "cot":
            return f"""Look at this floorplan image carefully.

Question: {question}

Choices:
{choice_str}

Think step by step:
1. First, identify what the question is asking
2. Examine the relevant parts of the floorplan
3. Consider each choice
4. Select the best answer

After your reasoning, provide your final answer as: "ANSWER: [letter]"
"""
        
        else:  # structured
            return f"""You are analyzing a floorplan image. Answer the following question.

Question: {question}

Choices:
{choice_str}

Instructions:
- Look carefully at the floorplan image
- Select the most accurate answer
- Respond with ONLY the letter of your choice (A, B, C, or D)

Your answer:"""
    
    def _parse_answer(self, text: str, choices: List[str]) -> tuple:
        """Parse model response to extract answer."""
        text_upper = text.upper().strip()
        
        # Look for explicit "ANSWER: X" pattern
        if "ANSWER:" in text_upper:
            after_answer = text_upper.split("ANSWER:")[-1].strip()
            for i, letter in enumerate(["A", "B", "C", "D"]):
                if after_answer.startswith(letter):
                    return choices[i] if i < len(choices) else "", i
        
        # Look for standalone letter
        for i, letter in enumerate(["A", "B", "C", "D"]):
            if text_upper == letter or text_upper.startswith(f"{letter}.") or text_upper.startswith(f"{letter} "):
                return choices[i] if i < len(choices) else "", i
        
        # Check if response matches a choice directly
        for i, choice in enumerate(choices):
            if choice.lower() in text.lower():
                return choice, i
        
        return text[:50], -1


class HeuristicBaseline(VLMBackend):
    """Rule-based baseline using ground-truth graph (for oracle comparison)."""
    
    def __init__(self, manifest_path: str):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        self.floorplan_data = {}
        for item in manifest:
            fp_id = item["id"]
            self.floorplan_data[fp_id] = item.get("metadata", {})
    
    def name(self) -> str:
        return "heuristic:graph_oracle"
    
    def query(
        self,
        image_path: str,
        question: str,
        choices: List[str],
        prompt_style: str = "structured",
        question_data: Optional[dict] = None
    ) -> VLMResponse:
        """
        Answer using ground-truth graph (no vision needed).
        This is the ORACLE baseline - upper bound on performance.
        """
        start_time = time.time()
        
        if question_data is None:
            return VLMResponse(
                model=self.name(),
                question_id="",
                predicted_answer="",
                predicted_index=-1,
                raw_response="No question metadata provided",
                latency_ms=0,
                error="Missing question_data"
            )
        
        fp_id = question_data.get("floorplan_id")
        q_type = question_data.get("question_type")
        metadata = question_data.get("metadata", {})
        
        fp_data = self.floorplan_data.get(fp_id, {})
        rooms = fp_data.get("rooms", [])
        graph = fp_data.get("adjacency_graph", {})
        
        predicted = ""
        predicted_idx = -1
        
        try:
            if q_type == "adjacency":
                room_a = metadata.get("room_a")
                room_b = metadata.get("room_b")
                is_adj = room_b in graph.get(room_a, [])
                predicted = "Yes" if is_adj else "No"
                predicted_idx = choices.index(predicted) if predicted in choices else -1
            
            elif q_type == "room_count":
                room_type = metadata.get("room_type")
                count = sum(1 for r in rooms if r.get("room_type") == room_type)
                predicted = str(count)
                predicted_idx = choices.index(predicted) if predicted in choices else -1
            
            elif q_type == "area_comparison":
                room_a_id = metadata.get("room_a")
                room_b_id = metadata.get("room_b")
                room_a = next((r for r in rooms if r["id"] == room_a_id), None)
                room_b = next((r for r in rooms if r["id"] == room_b_id), None)
                
                if room_a and room_b:
                    area_a = room_a["width"] * room_a["height"]
                    area_b = room_b["width"] * room_b["height"]
                    
                    if area_a > area_b:
                        predicted = f"The {room_a['room_type'].replace('_', ' ')}"
                    else:
                        predicted = f"The {room_b['room_type'].replace('_', ' ')}"
                    
                    predicted_idx = choices.index(predicted) if predicted in choices else -1
            
            elif q_type == "room_identification":
                # Use metadata directly since we generated the question
                room_id = metadata.get("room_id")
                room = next((r for r in rooms if r["id"] == room_id), None)
                if room:
                    predicted = room["room_type"].replace("_", " ")
                    predicted_idx = choices.index(predicted) if predicted in choices else -1
        
        except Exception as e:
            return VLMResponse(
                model=self.name(),
                question_id="",
                predicted_answer="",
                predicted_index=-1,
                raw_response=str(e),
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
        
        return VLMResponse(
            model=self.name(),
            question_id=question_data.get("id", ""),
            predicted_answer=predicted,
            predicted_index=predicted_idx,
            raw_response=f"Oracle answer: {predicted}",
            latency_ms=(time.time() - start_time) * 1000
        )


def get_vlm_backend(model_spec: str, **kwargs) -> VLMBackend:
    """Factory function for VLM backends."""
    
    if model_spec.startswith("gemini"):
        model_name = model_spec.split(":")[-1] if ":" in model_spec else "gemini-1.5-flash"
        return GeminiVLM(model_name=model_name)
    
    elif model_spec == "heuristic":
        return HeuristicBaseline(kwargs.get("manifest_path", "data/generated/manifest.json"))
    
    else:
        raise ValueError(f"Unknown model spec: {model_spec}")


if __name__ == "__main__":
    # Quick test
    print("Testing Gemini VLM...")
    try:
        vlm = get_vlm_backend("gemini:gemini-1.5-flash")
        print(f"Loaded: {vlm.name()}")
    except Exception as e:
        print(f"Error: {e}")
