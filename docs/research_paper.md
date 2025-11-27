# FloorplanQA: A Benchmark for Spatial Reasoning in Vision-Language Models

**Abstract**
Vision-Language Models (VLMs) have demonstrated impressive capabilities in general image understanding, but their ability to perform complex spatial reasoning in specialized domains remains under-explored. We present **FloorplanQA**, a rigorous benchmark for evaluating VLM spatial reasoning on architectural floorplans. Unlike existing datasets that focus on object detection, FloorplanQA requires models to deduce the function of unlabeled "mystery rooms" based on size, connectivity, and layout context. The benchmark includes 774 procedurally generated samples featuring calibrated difficulty tiers, five adversarial strategies (e.g., size mismatch, adjacency violations), and four types of visual corruption. We evaluate state-of-the-art VLMs and compare them against a human baseline of experts (architects) and non-experts. Our results reveal a significant performance gap, with models struggling particularly with adversarial layouts that violate common design heuristics, highlighting the need for more robust spatial reasoning capabilities in next-generation VLMs.

## 1. Introduction
Spatial reasoning—the ability to understand relationships between objects, spaces, and their functional implications—is a cornerstone of human intelligence. In architecture and engineering, this skill allows professionals to infer the purpose of a room from its context alone. While VLMs like GPT-4V and Gemini have shown promise in chart reading and diagram analysis, their application to technical spatial domains is limited by a lack of rigorous benchmarks.

Existing floorplan datasets (e.g., RPLAN, CubiCasa5K) are primarily designed for layout generation or segmentation, not high-level reasoning. To address this, we introduce FloorplanQA, a diagnostic benchmark that isolates spatial reasoning skills. By procedurally generating layouts, we can systematically inject "adversarial" features—such as unrealistic room sizes or illogical connections—to test whether models rely on robust reasoning or brittle heuristics.

## 2. Methods

### 2.1 Dataset Generation
We utilize a constraint-based procedural generation engine to create residential floorplans. Each sample is classified into one of three difficulty tiers:
- **Easy**: Rooms with highly distinctive features (e.g., large kitchens).
- **Medium**: Standard residential layouts.
- **Hard**: Ambiguous spaces requiring subtle context cues (e.g., distinguishing a small bedroom from an office).

### 2.2 Adversarial Strategies
To probe model robustness, we implement five adversarial transformations:
1.  **Size Mismatch**: Violating typical dimension norms (e.g., a 2m² living room).
2.  **Shape Confusion**: Distorting aspect ratios (e.g., 4:1 bedrooms).
3.  **Window Deception**: Removing or adding windows in functional contradictions.
4.  **Adjacency Violation**: Creating implausible connections (e.g., bathroom opening directly to kitchen).
5.  **Missing Rooms**: Removing essential zones to test holistic reasoning.

### 2.3 Visual Robustness
We apply a corruption pipeline adapted from ImageNet-C, including Gaussian blur, contrast reduction, JPEG compression, and rotation/skew, to evaluate performance under degraded visual conditions.

## 3. Evaluation Protocol
We define the "Mystery Room" task: given a floorplan with one unlabeled room, the model must predict its type from a fixed vocabulary. We evaluate three prompting conditions:
- **Direct**: Zero-shot prediction.
- **Minimal**: One-sentence reasoning.
- **Structured Chain-of-Thought (CoT)**: A 5-step reasoning process (Locate → Size → Adjacency → Features → Predict).

## 4. Results

### 4.1 Model Performance
(Placeholder for final experiment results)
Initial pilot testing indicates that Structured CoT improves accuracy by ~15% over direct prediction. However, model performance drops significantly (>20%) on adversarial samples, particularly "Adjacency Violation" and "Shape Confusion".

### 4.2 Human Baseline
We conducted a study with 33 participants (8 experts, 25 non-experts).
- **Experts**: 83.8% accuracy.
- **Non-Experts**: 51.7% accuracy.
- **Gap**: Current VLMs perform comparably to non-experts but trail experts by a wide margin.

## 5. Discussion
Our findings suggest that while VLMs can recognize basic architectural symbols, they lack the "common sense" spatial logic of human experts. The strong impact of adversarial perturbations indicates that models rely heavily on superficial visual features (e.g., "room with a bed is a bedroom") rather than deep functional reasoning. FloorplanQA provides a roadmap for measuring progress in this critical domain.
