# FloorplanQA v0: Reproduction Guide

This guide shows how to reproduce the FloorplanQA framework infrastructure and pilot dataset from scratch.

**⚠️ Important**: This reproduces the v0 FRAMEWORK only. VLM evaluations are NOT included in v0.

---

## Prerequisites

### Environment
- Python 3.10 or higher
- 4GB RAM minimum
- No GPU required

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/FloorplanQA.git
cd FloorplanQA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install numpy pandas matplotlib seaborn pillow tqdm scipy python-dotenv
```

---

## 1. Generate Pilot Dataset (Current v0)

### Reproduce Exact Pilot Dataset
```bash
# Generate 258 floorplans (takes ~5-10 minutes)
python scripts/generate_publication_dataset.py \
  --count 180 \
  --output data/floorplan_qa_benchmark_repro \
  --seed 42
```

**Note**: The count of 180 typically results in ~258 unique floorplans after generation adjustments.

### Verify Dataset Composition
```bash
python -c "
import json, pandas as pd
df = pd.DataFrame(json.load(open('data/floorplan_qa_benchmark_repro/dataset_index.json')))
print('Total entries:', len(df))
print('Unique floorplans:', df['floorplan_id'].nunique())
print('\nDifficulty:')
print(df['difficulty'].value_counts())
print('\nRoom types:')
print(df['ground_truth'].value_counts())
"
```

**Expected output:**
```
Total entries: 774
Unique floorplans: 258
Difficulty:
easy      453
medium    285
hard       36
Room types:
living_room    273
bedroom        210
kitchen        135
bathroom       114
office          36
balcony          6
```

---

## 2. Explore Generation Code

### View a Single Floorplan
```python
import json
from PIL import Image

# Load dataset
with open('data/floorplan_qa_benchmark/dataset_index.json') as f:
    dataset = json.load(f)

# Pick first entry
sample = dataset[0]
print(f"Floorplan ID: {sample['floorplan_id']}")
print(f"Type: {sample['type']}")
print(f"Difficulty: {sample['difficulty']}")
print(f"Ground truth: {sample['ground_truth']}")

# View image
img = Image.open(sample['image_path'])
img.show()
```

### Generate Custom Floorplan
```python
from src.generation.generator import generate_standard_floorplan
from src.rendering.image_renderer import render_floorplan_to_image
from src.rendering.styles import NORMAL_STYLE

# Generate
floorplan = generate_standard_floorplan(
    seed=12345,
    region="US_SUBURB",
    size_category="MEDIUM"
)

# Render
img = render_floorplan_to_image(floorplan, NORMAL_STYLE)
img.save("custom_floorplan.png")
```

---

## 3. Run Statistical Analysis (on Pilot Data)

### Analyze Mock Results
```bash
# The pilot includes mock predictions (random guessing)
python scripts/analyze_publication_results.py \
  data/floorplan_qa_pilot/results_test.csv \
  --output analysis_repro/
```

**Outputs:**
- `analysis_repro/accuracy_summary.csv`
- `analysis_repro/accuracy_by_difficulty.png`
- `analysis_repro/correlation_matrix.png`
- ... (5 total plots)

### Expected Results (Mock Data)
- Overall accuracy: ~10% (random baseline for 6 room types ≈ 16.7%, actual varies)
- No significant differences (because mock client returns random predictions)

---

---

## 5. Understanding the Code Structure

### Generation Pipeline
```
FloorplanGenerator (src/generation/generator.py)
  ↓
1. Binary Space Partition (space_partition.py)
  → Creates room rectangles
  ↓
2. Room Assignment (room_assigner.py)
  → Assigns types (bedroom, kitchen, etc.)
  → Selects mystery room
  → Classifies difficulty
  ↓
3. Door Placement (door_placer.py)
  → Ensures connectivity
  ↓
4. Rendering (src/rendering/image_renderer.py)
  → Generates PNG
```

### Adversarial Generation
```
AdversarialGenerator (src/generation/adversarial_generator.py)
  ↓
Applies one of 5 strategies:
  - size_mismatch: Distort room dimensions
  - shape_confusion: Extreme aspect ratios
  - window_deception: Misleading fenestration
  - adjacency_violation: Implausible connections
  - missing_rooms: Omit essential spaces
```

---

## 6. Common Issues & Solutions

### Issue: "KeyError: 'corruption_type'" in analysis
**Cause**: Corruptions not applied to v0 dataset  
**Solution**: This is expected. Corruption code exists but wasn't run on pilot dataset.

### Issue: Numbers don't match README exactly
**Cause**: Random seed variations or different generation parameters  
**Solution**: Use `--seed 42` for exact reproducibility

### Issue: "Module not found: statsmodels"
**Cause**: We removed statsmodels dependency  
**Solution**: Already fixed in v0 code (uses custom NumPy logistic regression)

---

## 7. Extending the Framework

### Add a New Room Type
```python
# 1. Add to enum (src/core/types.py)
class RoomType(Enum):
    # ... existing types
    PANTRY = "pantry"

# 2. Add to constraints (src/generation/parameters.py)
ROOM_AREA_RANGES[RoomType.PANTRY] = (3.0, 8.0)

# 3. Add to mystery candidates (src/generation/room_assigner.py)
CANDIDATE_MYSTERY_TYPES.add(RoomType.PANTRY)
```

### Add a New Adversarial Strategy
```python
# Add method to AdversarialGenerator
def _assign_furniture_confusion(self, rectangles, room_types, region, severity):
    # Your logic here
    pass

# Update generate_confusing_floorplan()
elif confusion_type == "furniture_confusion":
    rooms = self._assign_furniture_confusion(...)
```

---

## 8. What You CANNOT Reproduce from v0

The following are NOT included in v0 code:

❌ Real VLM evaluation results  
❌ Baseline model implementations (majority-class, heuristic, GNN)  
❌ Text-ablation experiments  
❌ Applied corruptions on dataset  
❌ Regional metadata tracking  
❌ Balanced dataset (current is imbalanced)

These are planned for v1.

---

## 9. Validation Checklist

After reproduction, verify:

- [ ] Dataset has 774 entries, 258 unique floorplans
- [ ] Difficulty distribution: ~58% easy, ~37% medium, ~5% hard
- [ ] Room types: 6 types (bedroom, bathroom, kitchen, living_room, office, balcony)
- [ ] 50/50 normal/adversarial split
- [ ] 3 rendering styles (normal, sketchy_medium, sketchy_extreme)
- [ ] Analysis scripts run without errors
- [ ] Plots generate successfully

---

## 10. Next Steps

### For Researchers
- Modify generation parameters to test different difficulty distributions
- Add new adversarial strategies
- Experiment with different rendering styles

### For Benchmark Developers
- Study the adversarial strategy implementations
- Examine the difficulty classification algorithm
- Review statistical analysis pipeline

### For VLM Practitioners
- Use the framework to generate custom test sets
- Adapt prompt templates for your models
- Build on the evaluation infrastructure

---

## Support

**Issues**: File on GitHub  
**Questions**: See README.md for contact information  
**Contributing**: Pull requests welcome

---

**Version**: 0.1  
**Last Updated**: December 2025
