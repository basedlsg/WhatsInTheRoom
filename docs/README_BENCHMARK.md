# FloorplanQA: A Benchmark for Spatial Reasoning in Vision-Language Models

**FloorplanQA** is a rigorous benchmark designed to evaluate the spatial reasoning capabilities of Vision-Language Models (VLMs) in the domain of architectural floorplans. It moves beyond simple object detection to test high-level reasoning about room identity, function, and connectivity.

## 🏆 Benchmark Overview

- **Task**: "Mystery Room" Identification. Given a floorplan with one unlabeled room, the model must predict its type based on size, adjacencies, and layout context.
- **Dataset Size**: 774 entries (129 unique floorplans × 2 variants × 3 styles).
- **Core Challenge**: Robustness to adversarial layouts and visual corruptions.

## 📊 Dataset Composition

The dataset is balanced across multiple dimensions to ensure fair evaluation:

### 1. Difficulty Tiers
- **Easy**: Distinctive features (e.g., large kitchen with island).
- **Medium**: Typical residential layouts.
- **Hard**: Ambiguous spaces (e.g., small bedroom vs. office).

### 2. Adversarial Strategies
Each floorplan has a paired "adversarial" variant designed to confuse specific reasoning heuristics:
- **Size Mismatch**: Rooms with uncharacteristic dimensions (e.g., tiny living room).
- **Shape Confusion**: Extreme aspect ratios (e.g., 4:1 hallway-like bedroom).
- **Window Deception**: Misleading fenestration (e.g., bedroom without windows).
- **Adjacency Violation**: Unrealistic connections (e.g., bathroom opening to kitchen).
- **Missing Rooms**: Essential functional areas removed (e.g., house with no bathroom).

### 3. Visual Robustness
- **Rendering Styles**: Normal, Sketchy (Medium), Sketchy (Extreme).
- **Corruptions**: Gaussian Blur, Contrast Reduction, JPEG Artifacts, Rotation/Skew.

## 🚀 Getting Started

### Installation

```bash
git clone https://github.com/yourusername/FloorplanQA.git
cd FloorplanQA
pip install -r requirements.txt
```

### Running the Benchmark

Run the full evaluation pipeline using the experiment runner:

```bash
python scripts/run_publication_experiment.py \
  --dataset data/floorplan_qa_benchmark/dataset_index.json \
  --output results/my_model_results.csv \
  --prompt-type structured_cot
```

**Arguments:**
- `--prompt-type`: `direct` (baseline), `minimal` (short reasoning), or `structured_cot` (recommended).
- `--real`: Use real NVIDIA NIM client (requires API key). Omit for mock testing.

### Analyzing Results

Generate comprehensive statistical reports and visualizations:

```bash
python scripts/analyze_publication_results.py results/my_model_results.csv --output analysis/
```

This will produce:
- Accuracy tables with 95% Bootstrap CIs.
- Plots for adversarial robustness and corruption impact.
- Statistical test results (Chi-square, Logistic Regression).

## 🧠 Human Baseline

We provide a human performance baseline for comparison:
- **Expert Accuracy**: 83.8% (Architects)
- **Non-Expert Accuracy**: 51.7% (Crowdworkers)
- **VLM Gap**: Current SOTA models trail experts by ~40%.

## 📂 Repository Structure

```
FloorplanQA/
├── data/
│   ├── floorplan_qa_benchmark/  # Main dataset
│   └── human_study/             # Human baseline data
├── src/
│   ├── generation/              # Procedural generation logic
│   ├── rendering/               # Visualization & corruption pipeline
│   ├── inference/               # Prompting & VLM client
│   └── analysis/                # Statistical tools
├── scripts/                     # Runners and utilities
└── results/                     # Experiment outputs
```

## 📜 Citation

If you use this benchmark, please cite:

```bibtex
@article{floorplanqa2025,
  title={FloorplanQA: A Benchmark for Spatial Reasoning in Vision-Language Models},
  author={Antigravity, Agent and User, The},
  journal={arXiv preprint},
  year={2025}
}
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
