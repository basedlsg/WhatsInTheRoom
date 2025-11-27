
import sys
import os
import pandas as pd
import json
from pathlib import Path
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_results(results_path: str = "data/scientific_dataset_pilot/experiment_results.csv"):
    print("=" * 70)
    print("SCIENTIFIC EXPERIMENT ANALYSIS")
    print("=" * 70)
    
    if not os.path.exists(results_path):
        print(f"Error: Results not found at {results_path}")
        return
        
    df = pd.read_csv(results_path)
    
    print(f"\nTotal predictions: {len(df)}")
    print(f"Unique floorplans: {df['floorplan_id'].nunique()}")
    
    # Calculate accuracy for Mystery Room (Standard)
    df['is_correct_mystery'] = df.apply(
        lambda row: str(row['mystery_pred']).lower().replace(' ', '_') == 
                    str(row['ground_truth']).lower().replace(' ', '_'),
        axis=1
    )
    
    # Calculate accuracy for Chain of Thought
    if 'cot_pred' in df.columns:
        df['is_correct_cot'] = df.apply(
            lambda row: str(row['cot_pred']).lower().replace(' ', '_') == 
                        str(row['ground_truth']).lower().replace(' ', '_'),
            axis=1
        )
    
    print("\n" + "=" * 70)
    print("ACCURACY BY CONDITION")
    print("=" * 70)
    
    # Overall accuracy
    print(f"\nOverall Mystery Accuracy: {df['is_correct_mystery'].mean():.1%}")
    if 'is_correct_cot' in df.columns:
        print(f"Overall CoT Accuracy:     {df['is_correct_cot'].mean():.1%}")
    
    # By type (normal vs adversarial)
    print("\nBy Floorplan Type:")
    type_acc = df.groupby('type')['is_correct_mystery'].agg(['mean', 'count'])
    type_acc.columns = ['Accuracy', 'Count']
    print(type_acc.to_string())
    
    # By subtype (specific adversarial strategy)
    if 'subtype' in df.columns:
        print("\nBy Adversarial Strategy (Subtype):")
        subtype_acc = df.groupby('subtype')['is_correct_mystery'].agg(['mean', 'count'])
        subtype_acc.columns = ['Accuracy', 'Count']
        print(subtype_acc.to_string())
    
    # By style (normal vs sketchy variants)
    print("\nBy Rendering Style:")
    style_acc = df.groupby('style')['is_correct_mystery'].agg(['mean', 'count'])
    style_acc.columns = ['Accuracy', 'Count']
    print(style_acc.to_string())
    
    # CoT vs Standard Comparison
    if 'is_correct_cot' in df.columns:
        print("\nStandard vs Chain-of-Thought:")
        cot_comparison = df[['is_correct_mystery', 'is_correct_cot']].mean()
        print(cot_comparison.to_string())
    
    print("\n" + "=" * 70)
    print("QUALITATIVE ANALYSIS")
    print("=" * 70)
    
    # Show some example predictions
    print("\nExample Predictions (Adversarial):")
    examples = df[df['type'] == 'adversarial'].head(3)
    for idx, row in examples.iterrows():
        correct = "✅" if row['is_correct_mystery'] else "❌"
        print(f"\n{correct} Floorplan: {row['floorplan_id'][:8]}... ({row['subtype']}, {row['style']})")
        print(f"   Ground Truth: {row['ground_truth']}")
        print(f"   Predicted: {row['mystery_pred']}")
        if 'cot_pred' in row:
            cot_correct = "✅" if row['is_correct_cot'] else "❌"
            print(f"   CoT Pred:  {row['cot_pred']} {cot_correct}")
            print(f"   CoT Reasoning: {str(row['cot_reasoning'])[:100]}...")
        
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    # Calculate key metrics
    normal_acc = df[df['type'] == 'normal']['is_correct_mystery'].mean()
    adv_acc = df[df['type'] == 'adversarial']['is_correct_mystery'].mean()
    
    print(f"\n1. Normal Floorplans: {normal_acc:.1%} accuracy")
    print(f"2. Adversarial Floorplans: {adv_acc:.1%} accuracy")
    print(f"   → Adversarial drop: {(normal_acc - adv_acc):.1%}")
    
    # Style impact
    normal_style_acc = df[df['style'] == 'normal']['is_correct_mystery'].mean()
    # Average of all sketchy styles
    sketchy_styles = [s for s in df['style'].unique() if 'sketchy' in s]
    if sketchy_styles:
        sketchy_acc = df[df['style'].isin(sketchy_styles)]['is_correct_mystery'].mean()
        print(f"\n3. Normal Rendering: {normal_style_acc:.1%} accuracy")
        print(f"4. Sketchy Rendering (Avg): {sketchy_acc:.1%} accuracy")
        print(f"   → Sketchy drop: {(normal_style_acc - sketchy_acc):.1%}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/scientific_dataset_pilot/experiment_results.csv")
    args = parser.parse_args()
    analyze_results(args.results)
