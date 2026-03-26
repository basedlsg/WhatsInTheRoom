"""
Real VLM client implementations for FloorplanQA evaluation.

NO MOCK DATA - Uses actual API calls.
"""

import os
import base64
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from PIL import Image
import io

import time
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def retry_with_backoff(max_retries=5, initial_delay=2.0, backoff_factor=2.0, max_delay=60.0):
    """Decorator for exponential backoff on API rate limits (429) or server errors (5xx)."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            import requests # ensure requests is available
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    # Check for rate limits (429) or transient server errors (500, 502, 503, 504)
                    status_code = None
                    if hasattr(e, 'response') and e.response is not None:
                        status_code = e.response.status_code
                    
                    if status_code in [429, 500, 502, 503, 504] or isinstance(e, requests.exceptions.ConnectionError):
                        if attempt == max_retries - 1:
                            print(f"\n❌ CRITICAL: Max retries ({max_retries}) reached for API limit/error.")
                            print("   Logical hard-stop triggered to prevent further API errors.")
                            raise RuntimeError("Logical Hard-Stop: Unrecoverable API Error (429/50x)")
                        print(f"\n⚠️ API error {status_code or 'ConnectionError'}. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        print(f"\n❌ FATAL: Unrecoverable API Error {status_code}.")
                        raise RuntimeError(f"Logical Hard-Stop: Unrecoverable API Error {status_code}") # Other errors (400, 401, 403) trigger immediate logical stop
            return func(*args, **kwargs)
        return wrapper
    return decorator


class VLMClient(ABC):
    """Base class for Vision-Language Model clients."""
    
    @abstractmethod
    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Query the VLM with an image and text prompt.
        
        Args:
            image_path: Path to image file
            prompt: Text prompt
            
        Returns:
            Dictionary with 'response', 'confidence', 'raw' fields
        """
        pass


class GeminiVLMClient(VLMClient):
    """Google Gemini Vision client - REAL API calls."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
        """
        import google.generativeai as genai
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        
    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Query Gemini with image and prompt."""
        # Load image
        img = Image.open(image_path)
        
        # Call Gemini API
        response = self.model.generate_content([prompt, img])
        
        # Extract response text
        response_text = response.text.strip()
        
        # Try to extract confidence if present
        confidence = None
        # Gemini doesn't provide confidence by default, set to None
        
        return {
            "response": response_text,
            "confidence": confidence,
            "raw": {
                "text": response_text,
                "model": self.model_name,
                "candidates": len(response.candidates) if hasattr(response, 'candidates') else 1
            }
        }


class NVIDIANIMClient(VLMClient):
    """NVIDIA NIM client - REAL API calls."""
    
    def __init__(self, model: str = "meta/llama-3.2-90b-vision-instruct", api_key: str = None):
        """
        Initialize NVIDIA NIM client.
        
        Args:
            api_key: NVIDIA API key (uses NVIDIA_API_KEY env var if not provided)
            model: Model identifier (Defaulting to NVIDIA NVLM to separate from Meta API)
        """
        import requests
        
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not found in environment or provided")
        
        self.model = model
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Query NVIDIA NIM with image and prompt."""
        # Encode image
        img_b64 = self._encode_image(image_path)
        
        # Prepare request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 512,
            "temperature": 0.0  # Deterministic
        }
        
        # Call API
        import requests
        
        @retry_with_backoff(max_retries=6, initial_delay=5.0)
        def _make_request():
            print(f"Calling NVIDIA API for {self.model}...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=(10, 30)
            )
            response.raise_for_status()
            return response

        response = _make_request()
        data = response.json()
        
        # Extract response
        response_text = data["choices"][0]["message"]["content"]
        
        return {
            "response": response_text,
            "confidence": None,
            "raw": data
        }


class VertexAIClient(VLMClient):
    """Vertex AI Gemini client - REAL API calls."""
    
    def __init__(self, project: str = "vertex-test-1-467818", location: str = "us-central1", model: str = "gemini-1.5-pro-002"):
        """
        Initialize Vertex AI client.
        
        Args:
            project: GCP Project ID
            location: GCP Region
            model: Model name
        """
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        vertexai.init(project=project, location=location)
        self.model = GenerativeModel(model)
        self.model_name = model
        
    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Query Vertex AI with image and prompt."""
        from vertexai.generative_models import Part
        
        # Load image
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        image_part = Part.from_data(data=image_bytes, mime_type="image/png")
        
        # Call Vertex AI
        response = self.model.generate_content([prompt, image_part])
        
        # Extract response
        response_text = response.text.strip()
        
        return {
            "response": response_text,
            "confidence": None,
            "raw": {
                "text": response_text,
                "model": self.model_name,
                "usage_metadata": str(response.usage_metadata) if hasattr(response, 'usage_metadata') else None
            }
        }


class HuggingFaceClient(VLMClient):
    """Hugging Face Inference API client."""
    
    def __init__(self, model: str = "allenai/Molmo2-8B-Instruct", api_key: str = None):
        import requests
        self.api_key = api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise ValueError("HF_TOKEN not found in environment")
            
        self.model = model
        # Using the standard 2026 router API path
        self.base_url = "https://router.huggingface.co/hf-inference/v1"
        
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        import requests
        img_b64 = self._encode_image(image_path)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ],
            "max_tokens": 512,
            "temperature": 0.0
        }

        @retry_with_backoff(max_retries=6, initial_delay=5.0)
        def _make_request():
            print(f"Calling Hugging Face API for {self.model}...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response

        response = _make_request()
        data = response.json()
        response_text = data["choices"][0]["message"]["content"]
        
        return {
            "response": response_text,
            "confidence": None,
            "raw": data
        }


class MetaLlamaClient(VLMClient):
    """Meta Developer Center API client."""
    
    def __init__(self, model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8", api_key: str = None):
        import requests
        self.api_key = api_key or os.getenv("LLAMA_API_KEY")
        if not self.api_key:
            raise ValueError("LLAMA_API_KEY not found in environment")
            
        self.model = model
        self.base_url = "https://api.llama.com/v1"
        
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def query(self, image_path: str, prompt: str) -> Dict[str, Any]:
        import requests
        img_b64 = self._encode_image(image_path)
        
        # Following the OpenAI compatible schema as requested
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ],
            "max_tokens": 512,
            "temperature": 0.0
        }

        @retry_with_backoff(max_retries=6, initial_delay=5.0)
        def _make_request():
            print(f"Calling Meta API for {self.model}...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response

        response = _make_request()
        data = response.json()
        # Meta Developer API uses a completely different response schema than OpenAI
        try:
            response_text = data["completion_message"]["content"]["text"]
        except KeyError:
            # Fallback for standard OpenAI schema if they update the endpoint dynamically
            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
        
        return {
            "response": response_text,
            "confidence": None,
            "raw": data
        }



def create_vlm_client(provider: str = "nvidia", **kwargs) -> VLMClient:
    """
    Factory function to create VLM client.
    
    Args:
        provider: "gemini", "nvidia", "vertex", "huggingface", "meta"
        **kwargs: Additional arguments for client
        
    Returns:
        VLMClient instance
    """
    if provider.lower() == "gemini":
        return GeminiVLMClient(**kwargs)
    elif provider.lower() == "nvidia":
        return NVIDIANIMClient(**kwargs)
    elif provider.lower() == "vertex":
        return VertexAIClient(**kwargs)
    elif provider.lower() == "huggingface":
        return HuggingFaceClient(**kwargs)
    elif provider.lower() == "meta":
        return MetaLlamaClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
