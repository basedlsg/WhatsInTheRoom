import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.inference.vlm_client import create_vlm_client

def test_vertex_connection():
    print("Initializing VertexAIClient...")
    try:
        # Use the hardcoded default project from the class or override here
        client = create_vlm_client(provider="vertex")
        
        # Select a sample image from the dataset
        image_dir = Path("data/floorplan_qa_v1/images")
        if not image_dir.exists():
            print(f"Error: {image_dir} not found.")
            return
            
        sample_image = next(image_dir.glob("*.png"), None)
        if not sample_image:
            print("Error: No sample images found in data directory.")
            return
            
        print(f"Using sample image: {sample_image}")
        prompt = "This is a 2D floorplan. What room types are present in this image? List them."
        
        print("Querying Vertex AI (Gemini 1.5 Pro)...")
        result = client.query(str(sample_image), prompt)
        
        print("\n--- Response ---")
        print(result["response"])
        print("----------------")
        print("\nConnection Successful!")
        
    except Exception as e:
        print(f"\nConnection Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vertex_connection()
