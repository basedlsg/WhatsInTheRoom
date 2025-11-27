#!/usr/bin/env python3
"""
Analyze publication experiment results with statistical rigor.

Generates:
- Accuracy tables with 95% CIs
- Statistical test results (Chi-square, Regression)
- Plots for key factors
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.statistics import (
    compute_bootstrap_ci,
    perform_chi_square_test,
    run_logistic_regression,
    correct_p_values
)

def analyze_results(csv_path: str, output_dir: str):
    """
    Run comprehensive statistical analysis on experiment results.
    """
    print("=" * 70)
    print("STATISTICAL ANALYSIS PIPELINE")
    print("=" * 70)
    
    # Load data
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from {csv_path}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Overall Accuracy with CI
    mean, lower, upper = compute_bootstrap_ci(df['is_correct'])
    print(f"\nOverall Accuracy: {mean:.1%} [{lower:.1%}, {upper:.1%}]")
    
    # 2. Accuracy by Condition Tables
    conditions = [
        'difficulty', 'prompt_type', 'rendering_style', 
        'adversarial_severity', 'corruption_severity'
    ]
    
    summary_data = []
    
    for cond in conditions:
        if cond not in df.columns:
            continue
            
        print(f"\nAnalysis by {cond}:")
        groups = df.groupby(cond)
        
        for name, group in groups:
            acc, low, high = compute_bootstrap_ci(group['is_correct'])
            count = len(group)
            print(f"  {str(name):15s}: {acc:.1%} (n={count}) [{low:.1%}, {high:.1%}]")
            
            summary_data.append({
                'Factor': cond,
                'Level': name,
                'Accuracy': acc,
                'CI_Lower': low,
                'CI_Upper': high,
                'N': count
            })
            
    # Save summary table
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(out_path / "accuracy_summary.csv", index=False)
    
    # 3. Hypothesis Testing (Chi-square)
    print("\n--- Hypothesis Testing ---")
    
    # H2: Adversarial vs Normal
    normal = df[df['type'] == 'normal']
    adv = df[df['type'] == 'adversarial']
    
    chi2, p, sig = perform_chi_square_test(
        normal['is_correct'].sum(), len(normal),
        adv['is_correct'].sum(), len(adv)
    )
    print(f"\nH2 (Adversarial Impact):")
    print(f"  Normal: {normal['is_correct'].mean():.1%}, Adv: {adv['is_correct'].mean():.1%}")
    print(f"  Chi2: {chi2:.2f}, p={p:.4f} ({'Significant' if sig else 'Not significant'})")
    
    # 4. Logistic Regression
    print("\n--- Logistic Regression Analysis ---")
    reg_result = run_logistic_regression(df)
    
    if "error" in reg_result:
        print(f"Regression failed: {reg_result['error']}")
    else:
        print("Significant Factors (p < 0.05):")
        for param, pval in reg_result['pvalues'].items():
            if pval < 0.05:
                coef = reg_result['params'][param]
                print(f"  {param:20s}: coef={coef:.3f}, p={pval:.4f}")
                
        # Save full regression summary
        with open(out_path / "regression_summary.txt", "w") as f:
            f.write(reg_result['summary'])
            
    # 5. Visualization
    print("\nGenerating plots...")
    
    # Plot Accuracy by Difficulty
    if 'difficulty' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.barplot(x='difficulty', y='is_correct', data=df, order=['easy', 'medium', 'hard'], capsize=.1)
        plt.title('Accuracy by Difficulty Tier')
        plt.ylabel('Accuracy')
        plt.savefig(out_path / "accuracy_by_difficulty.png")
        plt.close()
        
    # Plot Accuracy by Adversarial Severity
    if 'adversarial_severity' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.barplot(x='adversarial_severity', y='is_correct', data=df, order=['n/a', 'slight', 'medium', 'extreme'], capsize=.1)
        plt.title('Accuracy by Adversarial Severity')
        plt.ylabel('Accuracy')
        plt.savefig(out_path / "accuracy_by_adv_severity.png")
        plt.close()

    # Plot Accuracy by Adversarial Type
    if 'subtype' in df.columns:
        plt.figure(figsize=(10, 6))
        # Filter out n/a
        adv_df = df[df['subtype'] != 'n/a']
        if not adv_df.empty:
            sns.barplot(x='subtype', y='is_correct', data=adv_df, capsize=.1)
            plt.title('Accuracy by Adversarial Strategy')
            plt.ylabel('Accuracy')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(out_path / "accuracy_by_adv_type.png")
        plt.close()

    # Plot Direct vs CoT
    if 'prompt_type' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.barplot(x='prompt_type', y='is_correct', data=df, order=['direct', 'minimal', 'structured_cot'], capsize=.1)
        plt.title('Prompting Strategy Comparison')
        plt.ylabel('Accuracy')
        plt.savefig(out_path / "accuracy_by_prompt.png")
        plt.close()

    # Correlation Matrix
    # Select numeric/boolean columns
    corr_cols = ['is_correct', 'reasoning_length', 'corruption_severity']
    # Add mapped numeric columns if possible
    df_corr = df[corr_cols].copy()
    
    # Map ordinal columns
    if 'difficulty' in df.columns:
        df_corr['difficulty'] = df['difficulty'].map({'easy': 0, 'medium': 1, 'hard': 2})
    if 'adversarial_severity' in df.columns:
        df_corr['adv_severity'] = df['adversarial_severity'].map({'n/a': 0, 'slight': 1, 'medium': 2, 'extreme': 3})
        
    plt.figure(figsize=(10, 8))
    sns.heatmap(df_corr.corr(), annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.savefig(out_path / "correlation_matrix.png")
    plt.close()

    print(f"\nAnalysis complete! Results saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze FloorplanQA results")
    parser.add_argument("csv_path", help="Path to results CSV")
    parser.add_argument("--output", default="analysis_results", help="Output directory")
    
    args = parser.parse_args()
    analyze_results(args.csv_path, args.output)
