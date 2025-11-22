"""Inference pipeline for running VLM predictions on floorplans."""

import argparse
import os
import time
from typing import List, Optional
from tqdm import tqdm

from ..core.models import Floorplan, ModelPrediction
from ..inference.nim_client import NIMClient
from ..inference.prompts import create_mystery_room_prompt, DEFAULT_PROMPT
from ..storage.floorplan_store import load_all_floorplans
from ..storage.image_store import get_image_path, image_exists
from ..storage.results_store import save_predictions


def run_inference_batch(
    floorplan_dir: str,
    image_dir: str,
    output_file: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    max_samples: Optional[int] = None,
    use_metadata: bool = True,
    batch_delay: float = 0.5
) -> List[ModelPrediction]:
    """
    Run inference on a batch of floorplans.

    Args:
        floorplan_dir: Directory containing floorplan metadata
        image_dir: Directory containing rendered images
        output_file: Path to save predictions
        model_name: Model name (optional, uses env var if not provided)
        api_key: API key (optional, uses env var if not provided)
        max_samples: Maximum number of samples to process (None = all)
        use_metadata: Whether to include metadata in prompts
        batch_delay: Delay between API calls in seconds

    Returns:
        List of predictions
    """
    # Load floorplans
    print(f"Loading floorplans from {floorplan_dir}...")
    floorplans = load_all_floorplans(floorplan_dir)

    if not floorplans:
        print("No floorplans found!")
        return []

    print(f"Found {len(floorplans)} floorplans")

    # Limit samples if requested
    if max_samples and max_samples < len(floorplans):
        floorplans = floorplans[:max_samples]
        print(f"Limited to {max_samples} samples")

    # Initialize NIM client
    print("Initializing NVIDIA NIM client...")
    try:
        client = NIMClient(api_key=api_key, model_name=model_name)
        print(f"Using model: {client.model_name}")
    except Exception as e:
        print(f"Error initializing NIM client: {e}")
        return []

    # Run inference
    predictions = []
    errors = []

    print(f"\nRunning inference on {len(floorplans)} floorplans...\n")

    with tqdm(total=len(floorplans), desc="Processing") as pbar:
        for floorplan in floorplans:
            try:
                # Check if image exists
                image_path = get_image_path(floorplan.id, image_dir)

                if not image_exists(floorplan.id, image_dir):
                    print(f"\nWarning: Image not found for {floorplan.id}, skipping")
                    errors.append((floorplan.id, "Image not found"))
                    pbar.update(1)
                    continue

                # Create prompt
                if use_metadata:
                    prompt = create_mystery_room_prompt(
                        region=floorplan.region,
                        size_category=floorplan.size_category,
                        include_metadata=True
                    )
                else:
                    prompt = DEFAULT_PROMPT

                # Run prediction
                prediction = client.predict_room_type(
                    image_path=image_path,
                    prompt=prompt,
                    floorplan_id=floorplan.id
                )

                # Add ground truth to metadata
                mystery_room = floorplan.mystery_room
                if mystery_room:
                    prediction.metadata['true_room_type'] = mystery_room.room_type.value
                    prediction.metadata['region'] = floorplan.region.value
                    prediction.metadata['size_category'] = floorplan.size_category.value

                predictions.append(prediction)

                # Rate limiting delay
                if batch_delay > 0:
                    time.sleep(batch_delay)

            except Exception as e:
                print(f"\nError processing {floorplan.id}: {e}")
                errors.append((floorplan.id, str(e)))

            pbar.update(1)

    # Save results
    if predictions:
        print(f"\nSaving {len(predictions)} predictions to {output_file}...")
        save_predictions(predictions, output_file)
        print("Predictions saved successfully!")

    # Report errors
    if errors:
        print(f"\nEncountered {len(errors)} errors:")
        for floorplan_id, error in errors[:10]:  # Show first 10
            print(f"  {floorplan_id}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Print summary
    print(f"\nInference complete:")
    print(f"  Successful predictions: {len(predictions)}")
    print(f"  Errors: {len(errors)}")

    # Calculate basic accuracy if we have ground truth
    if predictions:
        correct = 0
        total = 0

        for pred in predictions:
            true_type = pred.metadata.get('true_room_type')
            if true_type:
                total += 1
                # Normalize comparison
                pred_type_norm = pred.predicted_room_type.lower().replace(' ', '_')
                true_type_norm = true_type.lower().replace(' ', '_')

                if pred_type_norm == true_type_norm:
                    correct += 1

        if total > 0:
            accuracy = correct / total
            print(f"  Accuracy: {accuracy:.2%} ({correct}/{total})")

    return predictions


def main():
    """Main entry point for inference pipeline."""
    parser = argparse.ArgumentParser(
        description="Run VLM inference on floorplan dataset"
    )
    parser.add_argument(
        "--floorplan-dir",
        type=str,
        default="data/floorplans",
        help="Directory containing floorplan metadata"
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default="data/images",
        help="Directory containing rendered images"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/predictions.parquet",
        help="Output file for predictions"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (defaults to env var NVIDIA_MODEL_NAME)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key (defaults to env var NVIDIA_API_KEY)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Maximum number of samples to process"
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't include metadata in prompts"
    )
    parser.add_argument(
        "--batch-delay",
        type=float,
        default=0.5,
        help="Delay between API calls (seconds)"
    )

    args = parser.parse_args()

    # Run inference
    run_inference_batch(
        floorplan_dir=args.floorplan_dir,
        image_dir=args.image_dir,
        output_file=args.output,
        model_name=args.model,
        api_key=args.api_key,
        max_samples=args.max_samples,
        use_metadata=not args.no_metadata,
        batch_delay=args.batch_delay
    )


if __name__ == "__main__":
    main()
