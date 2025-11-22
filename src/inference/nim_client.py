"""NVIDIA NIM API client for vision-language model inference."""

import base64
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
import requests

from ..core.models import ModelPrediction


class NIMClient:
    """Client for NVIDIA NIM vision-language model API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model_name: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize NIM client.

        Args:
            api_key: NVIDIA API key (defaults to env var NVIDIA_API_KEY)
            endpoint: API endpoint URL (defaults to env var NVIDIA_NIM_ENDPOINT)
            model_name: Model name (defaults to env var NVIDIA_MODEL_NAME)
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.endpoint = endpoint or os.getenv(
            "NVIDIA_NIM_ENDPOINT",
            "https://integrate.api.nvidia.com/v1"
        )
        self.model_name = model_name or os.getenv(
            "NVIDIA_MODEL_NAME",
            "meta/llama-3.2-90b-vision-instruct"
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if not self.api_key:
            raise ValueError(
                "NVIDIA API key not provided. Set NVIDIA_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def encode_image(self, image_path: str) -> str:
        """
        Encode an image to base64.

        Args:
            image_path: Path to the image file

        Returns:
            Base64-encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def predict_room_type(
        self,
        image_path: str,
        prompt: str,
        floorplan_id: str
    ) -> ModelPrediction:
        """
        Send image + prompt to NVIDIA VLM and parse response.

        Args:
            image_path: Path to rendered floorplan image
            prompt: Question about the unlabeled room
            floorplan_id: ID of the floorplan being analyzed

        Returns:
            ModelPrediction with predicted_type, reasoning, raw_response
        """
        # Encode image
        image_base64 = self.encode_image(image_path)

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # Make API call with retries
        response = self._call_api_with_retry(payload)

        # Parse response
        prediction = self._parse_response(response, floorplan_id)

        return prediction

    def _call_api_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call with exponential backoff retry logic.

        Args:
            payload: Request payload

        Returns:
            API response as dictionary

        Raises:
            Exception: If all retries fail
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.endpoint}/chat/completions"

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay * (2 ** attempt)))
                    print(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Raise for other HTTP errors
                response.raise_for_status()

                return response.json()

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"API call failed (attempt {attempt + 1}/{self.max_retries}). "
                          f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"API call failed after {self.max_retries} attempts.")

        # All retries failed
        raise Exception(f"API call failed after {self.max_retries} attempts: {last_exception}")

    def _parse_response(
        self,
        response: Dict[str, Any],
        floorplan_id: str
    ) -> ModelPrediction:
        """
        Parse API response into ModelPrediction.

        Args:
            response: Raw API response
            floorplan_id: ID of the floorplan

        Returns:
            ModelPrediction object
        """
        try:
            # Extract the assistant's message
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices in API response")

            message = choices[0].get("message", {})
            content = message.get("content", "")

            # Try to parse as JSON first
            predicted_type, reasoning, confidence = self._parse_structured_response(content)

            # If parsing failed, extract from text
            if not predicted_type:
                predicted_type, reasoning, confidence = self._parse_text_response(content)

            return ModelPrediction(
                floorplan_id=floorplan_id,
                model_name=self.model_name,
                predicted_room_type=predicted_type,
                confidence=confidence,
                reasoning=reasoning,
                timestamp=datetime.now(),
                raw_response=response
            )

        except Exception as e:
            # Return a prediction with error information
            return ModelPrediction(
                floorplan_id=floorplan_id,
                model_name=self.model_name,
                predicted_room_type="ERROR",
                confidence=0.0,
                reasoning=f"Failed to parse response: {str(e)}",
                timestamp=datetime.now(),
                raw_response=response
            )

    def _parse_structured_response(
        self,
        content: str
    ) -> tuple[str, str, Optional[float]]:
        """
        Try to parse response as structured JSON.

        Args:
            content: Response content

        Returns:
            Tuple of (predicted_type, reasoning, confidence)
        """
        try:
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1

            if start != -1 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)

                predicted_type = data.get("room_type", "").lower().replace(" ", "_")
                reasoning = data.get("reasoning", "")
                confidence = data.get("confidence")

                return predicted_type, reasoning, confidence

        except (json.JSONDecodeError, ValueError):
            pass

        return "", "", None

    def _parse_text_response(
        self,
        content: str
    ) -> tuple[str, str, Optional[float]]:
        """
        Parse response as unstructured text.

        Args:
            content: Response content

        Returns:
            Tuple of (predicted_type, reasoning, confidence)
        """
        # Simple heuristic: look for common room type keywords
        content_lower = content.lower()

        # Common room types
        room_types = [
            "closet", "office", "storage", "bedroom", "guest_bedroom",
            "bathroom", "kitchen", "living_room", "dining_room",
            "hallway", "pantry", "laundry", "utility_room", "balcony"
        ]

        predicted_type = ""
        for room_type in room_types:
            if room_type.replace("_", " ") in content_lower:
                predicted_type = room_type
                break

        # Use the full content as reasoning
        reasoning = content.strip()

        return predicted_type, reasoning, None
