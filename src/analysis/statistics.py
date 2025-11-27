"""
Statistical analysis module for FloorplanQA benchmark.

Implements:
- Bootstrap confidence intervals
- Chi-square tests for categorical comparisons
- Logistic regression (custom NumPy implementation)
- FDR correction (Benjamini-Hochberg)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any


def compute_bootstrap_ci(
    data: List[float],
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for the mean.
    
    Args:
        data: List of binary outcomes (0/1) or metric values
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level (e.g., 0.95)
        seed: Random seed
        
    Returns:
        Tuple of (mean, lower_ci, upper_ci)
    """
    if not len(data):
        return 0.0, 0.0, 0.0
        
    rng = np.random.RandomState(seed)
    data_array = np.array(data)
    n = len(data_array)
    
    # Bootstrap resampling
    indices = rng.randint(0, n, (n_resamples, n))
    resampled_means = np.mean(data_array[indices], axis=1)
    
    # Compute percentiles
    alpha = 1.0 - confidence_level
    lower_p = alpha / 2.0 * 100
    upper_p = (1.0 - alpha / 2.0) * 100
    
    lower_ci = np.percentile(resampled_means, lower_p)
    upper_ci = np.percentile(resampled_means, upper_p)
    mean = np.mean(data_array)
    
    return mean, lower_ci, upper_ci


def perform_chi_square_test(
    group1_correct: int,
    group1_total: int,
    group2_correct: int,
    group2_total: int
) -> Tuple[float, float, bool]:
    """
    Perform Chi-square test for independence between two groups.
    
    Args:
        group1_correct: Number of correct predictions in group 1
        group1_total: Total samples in group 1
        group2_correct: Number of correct predictions in group 2
        group2_total: Total samples in group 2
        
    Returns:
        Tuple of (chi2_stat, p_value, significant)
    """
    # Contingency table: [[correct, incorrect], [correct, incorrect]]
    group1_incorrect = group1_total - group1_correct
    group2_incorrect = group2_total - group2_correct
    
    table = np.array([
        [group1_correct, group1_incorrect],
        [group2_correct, group2_incorrect]
    ])
    
    # Add small constant if zeros present to avoid division by zero
    if np.any(table == 0):
        if group1_total == 0 or group2_total == 0:
            return 0.0, 1.0, False
            
    try:
        chi2, p_value, dof, expected = stats.chi2_contingency(table)
    except ValueError:
        # Handle cases with zero expected frequencies
        return 0.0, 1.0, False
    
    return chi2, p_value, p_value < 0.05


class SimpleLogisticRegression:
    """
    Simple Logistic Regression using Newton-Raphson method.
    Implemented with NumPy to avoid heavy dependencies like statsmodels/sklearn.
    """
    def __init__(self, tol=1e-6, max_iter=100):
        self.tol = tol
        self.max_iter = max_iter
        self.coef_ = None
        self.p_values_ = None
        self.stderr_ = None
        
    def sigmoid(self, z):
        return 1 / (1 + np.exp(-z))
        
    def fit(self, X, y):
        """
        Fit the model using Newton-Raphson.
        X: (n_samples, n_features) with intercept column already added
        y: (n_samples,) binary labels
        """
        n_samples, n_features = X.shape
        self.coef_ = np.zeros(n_features)
        
        for _ in range(self.max_iter):
            z = np.dot(X, self.coef_)
            p = self.sigmoid(z)
            
            # Gradient
            gradient = np.dot(X.T, (y - p))
            
            # Hessian
            W = np.diag(p * (1 - p))
            hessian = -np.dot(np.dot(X.T, W), X)
            
            # Newton-Raphson update
            try:
                delta = np.linalg.solve(hessian, -gradient)
            except np.linalg.LinAlgError:
                # Fallback or break if singular
                break
                
            self.coef_ += delta
            
            if np.linalg.norm(delta) < self.tol:
                break
                
        # Compute standard errors and p-values
        z = np.dot(X, self.coef_)
        p = self.sigmoid(z)
        W = np.diag(p * (1 - p))
        hessian = -np.dot(np.dot(X.T, W), X)
        
        try:
            cov_matrix = np.linalg.inv(-hessian)
            self.stderr_ = np.sqrt(np.diag(cov_matrix))
            z_scores = self.coef_ / self.stderr_
            # Two-tailed p-values
            self.p_values_ = 2 * (1 - stats.norm.cdf(np.abs(z_scores)))
        except:
            self.stderr_ = np.zeros(n_features)
            self.p_values_ = np.ones(n_features)


def run_logistic_regression(
    df: pd.DataFrame,
    target_col: str = "is_correct",
    predictor_cols: List[str] = None
) -> Dict[str, Any]:
    """
    Run logistic regression to analyze factor impact on accuracy.
    
    Args:
        df: Pandas DataFrame with experiment results
        target_col: Name of target column (binary)
        predictor_cols: List of predictor column names
        
    Returns:
        Dictionary with regression summary and significant factors
    """
    if predictor_cols is None:
        predictor_cols = [
            "difficulty", "adversarial_severity", "corruption_severity", 
            "prompt_type", "rendering_style"
        ]
    
    # Preprocessing: Convert categorical to dummy/numeric
    df_processed = df.copy()
    
    # Map ordinal variables to numeric
    severity_map = {"n/a": 0, "slight": 1, "medium": 2, "extreme": 3}
    difficulty_map = {"easy": 0, "medium": 1, "hard": 2}
    
    if "adversarial_severity" in df_processed.columns:
        df_processed["adversarial_severity_num"] = df_processed["adversarial_severity"].map(severity_map).fillna(0)
    
    if "difficulty" in df_processed.columns:
        df_processed["difficulty_num"] = df_processed["difficulty"].map(difficulty_map).fillna(1)
        
    # Prepare X and y
    model_cols = []
    
    # Add numeric predictors
    if "difficulty_num" in df_processed.columns:
        model_cols.append("difficulty_num")
    if "adversarial_severity_num" in df_processed.columns:
        model_cols.append("adversarial_severity_num")
    if "corruption_severity" in df_processed.columns:
        # Ensure numeric
        df_processed["corruption_severity"] = pd.to_numeric(df_processed["corruption_severity"], errors='coerce').fillna(0)
        model_cols.append("corruption_severity")
        
    # Add dummies for prompt_type if multiple exist
    if "prompt_type" in df_processed.columns and df_processed["prompt_type"].nunique() > 1:
        dummies = pd.get_dummies(df_processed["prompt_type"], prefix="prompt", drop_first=True)
        # Convert bool dummies to int
        dummies = dummies.astype(int)
        df_processed = pd.concat([df_processed, dummies], axis=1)
        model_cols.extend(dummies.columns)
        
    # Add dummies for rendering_style
    if "rendering_style" in df_processed.columns and df_processed["rendering_style"].nunique() > 1:
        dummies = pd.get_dummies(df_processed["rendering_style"], prefix="style", drop_first=True)
        # Convert bool dummies to int
        dummies = dummies.astype(int)
        df_processed = pd.concat([df_processed, dummies], axis=1)
        model_cols.extend(dummies.columns)

    # Check if we have enough data
    if len(df_processed) < 10 or not model_cols:
        return {"error": "Insufficient data for regression"}
        
    # Prepare matrices
    X_df = df_processed[model_cols]
    # Add constant (intercept) manually
    X_df.insert(0, 'const', 1)
    
    X = X_df.values.astype(float)
    y = df_processed[target_col].astype(int).values
    
    try:
        model = SimpleLogisticRegression()
        model.fit(X, y)
        
        # Format results
        params = {col: val for col, val in zip(X_df.columns, model.coef_)}
        pvalues = {col: val for col, val in zip(X_df.columns, model.p_values_)}
        
        # Create text summary
        summary = "Simple Logistic Regression Results\n"
        summary += "=" * 40 + "\n"
        summary += f"{'Variable':<25} {'Coef':<10} {'P-value':<10}\n"
        summary += "-" * 40 + "\n"
        
        for col in X_df.columns:
            summary += f"{col:<25} {params[col]:.4f}     {pvalues[col]:.4f}\n"
            
        return {
            "summary": summary,
            "params": params,
            "pvalues": pvalues,
            "aic": 0  # Not implemented
        }
    except Exception as e:
        return {"error": str(e)}


def correct_p_values(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: List of raw p-values
        method: Only 'fdr_bh' supported in this simple version
        
    Returns:
        List of corrected p-values
    """
    if not p_values:
        return []
        
    p_vals = np.array(p_values)
    n = len(p_vals)
    
    # Sort p-values
    sort_indices = np.argsort(p_vals)
    sorted_p = p_vals[sort_indices]
    
    # Compute BH critical values
    # q-value = p * (n / rank)
    ranks = np.arange(1, n + 1)
    adjusted = sorted_p * n / ranks
    
    # Enforce monotonicity (step-up)
    # q_i = min(q_i, q_{i+1})
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
        
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Restore original order
    final_adjusted = np.zeros(n)
    final_adjusted[sort_indices] = adjusted
    
    return final_adjusted.tolist()
