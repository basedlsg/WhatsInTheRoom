import json
from pathlib import Path

def analyze_ablation():
    results_path = Path("results/ablation_results.json")
    if not results_path.exists():
        print("Ablation results file not found.")
        return
        
    with open(results_path) as f:
        results = json.load(f)
        
    conditions = ["baseline", "spatial", "rules", "exclusion", "contrastive"]
    rooms = ["bedroom", "bathroom", "kitchen", "living_room", "office"]
    
    # Initialize the 5x5 matrix mapping
    matrix = {cond: {r: {"correct": 0, "total": 0} for r in rooms} for cond in conditions}
    
    # Process results
    for cond in conditions:
        if cond not in results:
            continue
            
        for entry in results[cond]:
            truth = entry["ground_truth"]
            if truth not in rooms:
                continue
                
            matrix[cond][truth]["total"] += 1
            if entry["correct"]:
                matrix[cond][truth]["correct"] += 1
                
    # Print the 5x5 Matrix (Condition x Room Type)
    print("\n" + "="*80)
    print(" " * 15 + "".join([f"{r:>12}" for r in rooms]) + f"{'OVERALL':>12}")
    print("-" * 80)
    
    for cond in conditions:
        row_str = f"{cond:<15}"
        cond_correct = 0
        cond_total = 0
        
        for r in rooms:
            stats = matrix[cond][r]
            if stats["total"] > 0:
                acc = (stats["correct"] / stats["total"]) * 100
                row_str += f"{acc:>11.1f}%"
                
                cond_correct += stats["correct"]
                cond_total += stats["total"]
            else:
                row_str += f"{'N/A':>12}"
                
        # Overall
        if cond_total > 0:
            overall_acc = (cond_correct / cond_total) * 100
            row_str += f" | {overall_acc:>9.1f}%"
            
        print(row_str)
        
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_ablation()
