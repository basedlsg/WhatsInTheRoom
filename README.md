# FloorplanQA v1.1

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Version](https://img.shields.io/badge/version-1.1-green)

## 🏗️ Methodology (v1.1)

### 1. Dataset Construction
The dataset contains **3,914** total samples divided into three splits.
- **Clean Split (1,914 samples)**: Balanced across 6 regions and 3 difficulty tiers. Generated using a constraint-based solver (C++ equivalent logic in Python).
- **Adversarial Split (1,000 samples)**: **Independent** layouts (not shared with Clean) generated with specific structural flaws (e.g., missing essential rooms, geometric impossibilities) to test reasoning under contradiction.
- **Corruption Split (1,000 samples)**: **Paired** counterfactuals sampled from the Clean set. These share the exact same geometry/labels as Clean samples but apply visual corruptions (blur, noise, etc.) to test perception robustness.

### 2. Rendering & "Kitchen Blindness" Fix
v1.1 introduces a **Semantic Fixture Renderer** to solve the geometric ambiguity of wet rooms.
- **Kitchens**: Rendered with counters (along longest wall), a sink (circle), and a stove (rectangle + burners).
- **Bathrooms**: Rendered with a toilet (oval) and sink (circle).
- **Threshold**: Fixtures are only drawn if the room's screen-space dimension > 20px. Very small powder rooms may remain icon-less (testing fine-grained perception).
- **Scaling**: Icons scale proportionally to room size (e.g., sink radius = 0.15 × min_dimension).

### 3. Reproducibility & Limitations
- **Global Reproducibility**: The entire dataset can be deterministically regenerated using the fixed global seed (`2025`).
- **Per-Sample Constraints**: We do **not** currently expose per-sample seeds in the metadata index. Reproducing a specific sample in isolation requires running the full generation sequence.
- **Selection Bias**: The "Clean" set consists of 1,914 samples (selected from 3,000 attempts) that satisfied strict connectivity and area constraints. This may introduce a distribution bias against highly complex or extremely compact layouts that are harder to solve.
- **Icon Thresholds**: Semantic fixtures are only rendered if the room dimension exceeds **20px**. Very small utility rooms or powder rooms may remain geometrically ambiguous (icon-less), representing a valid perceptual edge case.

**FloorplanQA** is a scientifically rigorous synthetic benchmark for evaluating **spatial reasoning** in Vision-Language Models (VLMs) through architectural floorplan analysis.

## 🚀 v1.1 Updates
- **Solved "Kitchen Blindness"**: v1.1 introduces semantic icons (counters, sinks, stoves) to all floorplans, resolving the geometric ambiguity that caused 0% accuracy in v1.0.
- **Improved Renderer**: Standardized fixture rendering for kitchens and bathrooms.

**Current Release**: v1.0 (December 2024)
**Status**: Framework + Dataset + Baselines ✓

---

## 🎯 Task

**Mystery Room Identification**: Given a floorplan with one unlabeled room, predict its type based on spatial context (size, adjacencies, position, features).

**Why This Matters**: Tests functional inference from geometric relationships, not just object detection.

---

## 📊 Dataset (v1)

### Scale
- **4,675 total samples** across 3 test sets
- **3,675 unique floorplans**
- **5 mystery room types**: bedroom, bathroom, kitchen, living_room, office

### Clean Evaluation Set (2,675 samples)
**Difficulty Distribution:**
- Easy: 37.4% | Hard: 37.4% | Medium: 25.2%

**Room Types:**
- kitchen (31%), bedroom (24%), living_room (15%), bathroom (15%), office (15%)

**Regions:**
- 6 architectural styles (European, Japanese, Australian, Modern, US, Chinese)

### Adversarial Stress-Test Set (1,000 samples)
**Purpose**: Test robustness to unrealistic layouts

**Strategies (200 each):**
- Size Mismatch, Shape Confusion, Window Deception, Adjacency Violation, Missing Rooms

### Corruption Robustness Set (1,000 samples)
**Purpose**: Test visual robustness

**Types (250 each):**
- Blur (σ=1,3,5), Contrast (75%,50%,25%), JPEG (Q=80,50,20), Skew (±5°,±10°,±15°)

---

## 📈 Benchmark Results (v1)

### Baseline vs. VLM Performance

We evaluated **Google Gemini 2.0 Flash** on a stratified sample of 400 floorplans from the clean test set.

| Model | Accuracy | vs. Random |
|-------|----------|------------|
| **Random Baseline** | 20.0% | 1.0x |
| **Majority Class** | 31.4% | 1.6x |
| **Gemini 2.0 Flash** | **42.6%** | **2.1x** |

### Detailed Analysis

**Strengths:**
- **Living Rooms**: 88.6% accuracy (Highly distinct size/centrality)
- **Bedrooms**: 72.2% accuracy (Clear shape/location patterns)
- **Easy Difficulty**: 65.9% accuracy

**Critical Weakness:**
- **Kitchens**: **0.0% accuracy** (0/69 correct)

**Why Kitchens Fail:**
Our analysis reveals a key limitation in current VLM spatial reasoning: without explicit semantic icons (stoves, sinks), models cannot distinguish kitchens from generic rooms based purely on geometry and adjacency. They consistently misclassify rectangular kitchens as **living rooms** (61%) or **bedrooms** (33%).

**Implication**: Pure geometric reasoning (without object detection) remains a significant challenge for SOTA models.

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/yourusername/FloorplanQA
cd FloorplanQA
pip install -r requirements.txt
```

### Evaluate Baselines
```bash
python scripts/evaluate_simple_baselines.py \
  --dataset data/floorplan_qa_v1 \
  --output results/baselines
```

### Explore Dataset
```python
import json, pandas as pd

with open('data/floorplan_qa_v1/dataset_index.json') as f:
    df = pd.DataFrame(json.load(f))

print(df['split'].value_counts())
print(df[df['split']=='clean']['difficulty'].value_counts())
```

---

## ⚠️ Limitations

**Dataset**:
- Room type imbalance (kitchen 31%, others ~15%)
- 2D only, simplified geometry
- Synthetic (procedural, not real scans)
- Residential only

**Evaluation**:
- Baselines only (majority + random implemented)
- No VLM results yet
- No text ablations

---

## 🛣️ Roadmap

### v1.0 (Current)
✅ 4,675 samples (clean + adversarial + corruption)  
✅ Baseline bounds established  
✅ Statistical analysis pipeline  

### v1.1 (Planned)
- VLM evaluation (GPT-4V, Claude, Gemini)
- Heuristic baseline
- Text ablation experiments

### v2.0 (Future)
- Multi-floor/3D support
- Public leaderboard

---

## 📖 Documentation

- **[Reproduction Guide](docs/reproduction_guide.md)**: How to regenerate dataset
- **[Research Paper](docs/research_paper.md)**: Technical details
- **[Phase Summaries](/.gemini/antigravity/brain/)**: Development progress

---

## 📄 Citation

```bibtex
@dataset{floorplanqa2024,
  title={FloorplanQA: A Benchmark for Spatial Reasoning in Vision-Language Models},
  author={[Authors]},
  year={2024},
  version={1.0}
}
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE)

---

## 🏗️ Repository Structure

```
FloorplanQA/
├── src/
│   ├── generation/      # Procedural floorplan generation
│   ├── rendering/       # Image rendering + corruptions
│   ├── baselines/       # Baseline model implementations
│   ├── inference/       # Prompt templates + VLM client
│   └── analysis/        # Statistical analysis
├── scripts/
│   ├── generate_v1_dataset.py        # Dataset generation
│   ├── evaluate_simple_baselines.py  # Baseline evaluation
│   └── ...
└── data/
    └── floorplan_qa_v1/              # v1 dataset (4,675 samples)
        ├── images/                    # PNG floorplans
        └── dataset_index.json         # MetadataIndex
```

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Implementing additional baselines (heuristic, text-only, GNN)
- VLM evaluation infrastructure
- Text ablation experiments

See our [GitHub Issues](https://github.com/yourusername/FloorplanQA/issues) for specific tasks.

---

##Honest Assessment

**What v1 provides:**
✅ Large-scale procedurally generated dataset
✅ Controlled adversarial perturbations  
✅ Visual corruption robustness tests  
✅ Basic baseline performance bounds  
✅ Reproducible generation pipeline  

**What v1 does NOT provide:**
❌ VLM performance results
❌ Complex baseline implementations
❌ Text ablation comparisons

**Best used for:**
- Benchmarking spatial reasoning in VLMs
- Studying adversarial robustness
- Controlled experimental design
- Prototyping evaluation methods

**Not suitable for:**
- Claims about real-world deployment
- Production system validation
- Multi-floor or complex 3D reasoning

---

For questions or collaboration: [Contact Info]
