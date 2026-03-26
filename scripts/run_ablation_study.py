import json
import logging
import concurrent.futures
from pathlib import Path
from tqdm import tqdm
from src.inference.vlm_client import create_vlm_client
from src.inference.prompts import (
    create_ablation_baseline_prompt,
    create_ablation_spatial_prompt,
    create_ablation_rules_prompt,
    create_ablation_exclusion_prompt,
    create_ablation_contrastive_prompt
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONDITIONS = {
    "baseline": create_ablation_baseline_prompt(),
    "spatial": create_ablation_spatial_prompt(),
    "rules": create_ablation_rules_prompt(),
    "exclusion": create_ablation_exclusion_prompt(),
    "contrastive": create_ablation_contrastive_prompt()
}

def evaluate_ablation():
    data_path = Path("data/ablation_200.json")
    with open(data_path) as f:
        dataset = json.load(f)
        
    logger.info("Initializing Llama 3.2 11B vision client (NVIDIA NIM)...")
    client = create_vlm_client("nvidia", model="meta/llama-3.2-11b-vision-instruct")
    out_file = Path("results/ablation_results.json")
    
    results = {}
    if out_file.exists():
        with open(out_file) as f:
            results = json.load(f)
            
    for cond_name, prompt_text in CONDITIONS.items():
        if cond_name not in results:
            results[cond_name] = []
            
        processed_ids = {r["floorplan_id"] for r in results[cond_name]}
        remaining = [d for d in dataset if d["floorplan_id"] not in processed_ids]
        
        if not remaining:
            logger.info(f"Condition '{cond_name}' already complete.")
            continue
            
        logger.info(f"Running condition '{cond_name}' ({len(remaining)} samples)...")
        
        def evaluate_entry(entry):
            logger.info(f"Evaluating floorplan {entry['floorplan_id']}...")
            img_path = Path("data/floorplan_qa_benchmark/") / entry["image_path"]
            
            # Retry mechanism for 429s
            import time
            max_retries = 5
            response = None
            for attempt in range(max_retries):
                try:
                    response = client.query(image_path=str(img_path), prompt=prompt_text)
                    break
                except Exception as e:
                    err_str = str(e).lower()
                    if ("429" in err_str or "timeout" in err_str or "500" in err_str or "502" in err_str or "504" in err_str) and attempt < max_retries - 1:
                        time.sleep(2 ** attempt * 2) 
                    else:
                        logger.error(f"Failed {entry['floorplan_id']} entirely: {e}")
                        return {
                            "floorplan_id": entry["floorplan_id"],
                            "ground_truth": entry["ground_truth"],
                            "prediction": "error",
                            "correct": False,
                            "raw_response": str(e)
                        }
                        
            if not response:
                return {
                    "floorplan_id": entry["floorplan_id"],
                    "ground_truth": entry["ground_truth"],
                    "prediction": "error",
                    "correct": False,
                    "raw_response": "empty response"
                }
                
            # Try to parse as JSON or string fallback
            try:
                import re
                match = re.search(r'\{.*\}', response["response"], re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    # Fallback chain for different condition schemas
                    if "room_type" in parsed:
                        pred = parsed["room_type"]
                    elif "prediction" in parsed:
                        pred = parsed["prediction"]
                    else:
                        pred = "error"
                else:
                    pred = "error"
            except:
                pred = "error"
                
            pred = str(pred).replace(" ", "_").lower()
            
            truth = entry["ground_truth"]
            correct = (pred == truth)
                
            return {
                "floorplan_id": entry["floorplan_id"],
                "ground_truth": truth,
                "prediction": pred,
                "correct": correct,
                "raw_response": response["response"]
            }

        # Execute concurrently with 5 threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(evaluate_entry, entry): entry for entry in remaining}
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(remaining), desc=f"Evaluating {cond_name}"):
                res = future.result()
                if res is not None:
                    results[cond_name].append(res)
                    
                    # Intermittent checkpoint
                    if len(results[cond_name]) % 10 == 0:
                        with open(out_file, "w") as f:
                            json.dump(results, f, indent=2)
                            
        # Final condition checkpoint
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
                
    logger.info("Ablation study complete.")

if __name__ == "__main__":
    evaluate_ablation()
