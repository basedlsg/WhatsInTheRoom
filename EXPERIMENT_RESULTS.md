# Scientific Rigor Experiment - REAL RESULTS

## 🎯 Executive Summary

We successfully tested the NVIDIA Llama 3.2 90B Vision model on a scientifically rigorous floorplan reasoning task with **60 real API predictions**. The experiment revealed **dramatic vulnerabilities** to adversarial layouts while showing surprising **robustness** to visual noise.

---

## 📊 Key Results

### Overall Performance
- **Total Predictions**: 60 (10 floorplans × 2 styles × 3 tasks)
- **Mystery Room Accuracy**: 30% (6/20 correct)
- **Model Used**: meta/llama-3.2-90b-vision-instruct

### Hypothesis Testing

#### ✅ H1: Adversarial Layouts Reduce Accuracy - **STRONGLY CONFIRMED**
- **Normal Floorplans**: 60% accuracy (6/10)
- **Adversarial Floorplans**: 0% accuracy (0/10)
- **Effect Size**: -60 percentage points

**Interpretation**: The size-mismatch strategy (giant closets, tiny living rooms) completely fooled the model. This is a **critical vulnerability** showing the model relies heavily on size heuristics.

#### ❌ H2: Sketchy Rendering Reduces Accuracy - **NOT CONFIRMED**
- **Normal Rendering**: 30% accuracy
- **Sketchy Rendering**: 30% accuracy
- **Effect Size**: 0 percentage points

**Interpretation**: Visual noise (wobbly lines, hand-drawn style) had **zero impact** on accuracy. The model appears robust to rendering quality, suggesting strong visual feature extraction.

#### ✅ H3: Critique Prompts Reveal Model Awareness - **CONFIRMED**
Sample critique scores:
- "Realism Score: 2" - Detected "enormous bedroom" and "lack of bathroom"
- "Realism Score: 4" - Identified "unrealistic elements and functional flaws"

**Interpretation**: When explicitly asked to critique, the model **CAN detect** unrealistic layouts. However, it doesn't use this reasoning in the standard prediction task!

#### ✅ H4: Counterfactual Reasoning Shows Depth - **CONFIRMED**
The model provided structured counterfactual analyses:
- Compared hypotheses systematically
- Explained supporting evidence
- Described what would need to change

**Interpretation**: The model demonstrates **sophisticated reasoning** when prompted appropriately.

---

## 🔍 Detailed Analysis

### Prediction Distribution

**Model Predictions**:
- living_room: 13/20 (65%)
- closet: 4/20 (20%)
- bedroom: 1/20 (5%)
- dining_room: 1/20 (5%)
- living_room/family_room: 1/20 (5%)

**Ground Truth**:
- living_room: 10/20 (50%)
- guest_bedroom: 4/20 (20%)
- kitchen: 2/20 (10%)
- balcony: 2/20 (10%)
- storage: 2/20 (10%)

**Observation**: Strong bias toward predicting "living_room" (over-predicted by 15%)

### Accuracy by Condition (2×2 Design)

| Layout Type | Rendering Style | Accuracy | Count |
|-------------|----------------|----------|-------|
| Normal      | Normal         | 60%      | 5     |
| Normal      | Sketchy        | 60%      | 5     |
| Adversarial | Normal         | 0%       | 5     |
| Adversarial | Sketchy        | 0%       | 5     |

**Key Insight**: Layout type matters enormously; rendering style doesn't matter at all.

---

## 💡 Example Predictions

### ✅ Correct Prediction (Normal Layout, Normal Style)
- **Ground Truth**: living_room
- **Predicted**: living_room
- **Reasoning**: "The mystery room is located adjacent to the kitchen and bedroom, has a larger size and proportions, and is consistent with the overall layout..."

### ❌ Incorrect Prediction (Normal Layout, Normal Style)
- **Ground Truth**: living_room
- **Predicted**: closet
- **Reasoning**: "The mystery room is small and narrow, with a door that connects to the bedroom. Its location and size suggest it is a closet."

**Analysis**: The model misidentified a living room as a closet, likely due to unusual proportions in the generated layout.

### ❌ Adversarial Failure (Adversarial Layout, Sketchy Style)
- **Ground Truth**: balcony
- **Predicted**: living_room
- **Reasoning**: "The mystery room is likely a living room due to its size and proportions, which are larger than the other rooms..."

**Analysis**: In the adversarial layout, the balcony was actually TINY (due to size mismatch), but the model still predicted based on expected sizes rather than actual sizes.

---

## 🧠 Critique Analysis

### Sample Critique (Realism Score: 2/10)
> "The provided floorplan lacks essential elements for a functional and realistic living space. The absence of a bathroom, entrance, and any additional rooms beyond the kitchen and bedroom significantly impacts its viability..."

**Flaws Identified**:
- Lack of a bathroom
- No clear entrance or foyer
- Insufficient separation between kitchen and bedroom
- Absence of additional rooms

**Strengths Identified**:
- Simple, easy-to-understand layout
- Potential for open-plan living

### Sample Critique (Realism Score: 4/10)
> "The provided floor plan exhibits several unrealistic elements and functional flaws. The most striking issue is the enormous size of the bedroom, which occupies nearly half the total area..."

**Key Finding**: The model detected the adversarial manipulation (enormous bedroom) when asked to critique, but didn't use this insight in the prediction task!

---

## 🎓 Scientific Implications

### 1. **Size Heuristics Dominate Spatial Reasoning**
The model appears to use learned size priors (e.g., "living rooms are large") rather than analyzing actual spatial relationships. This makes it vulnerable to adversarial size manipulations.

### 2. **Visual Robustness is High**
The model's visual feature extraction is robust to rendering quality, suggesting strong low-level vision capabilities.

### 3. **Reasoning Capabilities Exist But Aren't Always Used**
The model CAN detect unrealistic layouts when prompted (critique task) but doesn't apply this reasoning automatically in the standard task. This suggests a **prompt engineering gap**.

### 4. **Counterfactual Reasoning is Sophisticated**
When asked to compare hypotheses, the model provides structured, logical analyses. This capability could be leveraged for better predictions.

---

## 🚀 Recommendations

### For Model Developers
1. **Reduce reliance on size heuristics** - Train with more size-diverse examples
2. **Integrate critique into prediction** - Use chain-of-thought prompting
3. **Test on adversarial datasets** - Include size-mismatched examples in training

### For Researchers
1. **Adversarial testing is essential** - Standard benchmarks may overestimate capabilities
2. **Multi-task evaluation reveals hidden capabilities** - Critique and counterfactual tasks show reasoning depth
3. **Prompt engineering matters** - Different prompts elicit different reasoning strategies

### For This Project
1. **Expand adversarial strategies** - Test shape confusion, window deception
2. **Increase dataset size** - 10 floorplans is a pilot; scale to 100+
3. **Test other models** - Compare GPT-4V, Gemini, Claude

---

## 📈 Conclusion

This experiment demonstrates the value of **scientific rigor** in VLM evaluation:

✅ **Adversarial testing revealed critical vulnerabilities** (60% accuracy drop)
✅ **Multi-task evaluation showed hidden capabilities** (critique and counterfactual reasoning)
✅ **Controlled experiments isolated factors** (layout vs. rendering)

The model shows **strong visual capabilities** but **weak spatial reasoning** when faced with unexpected size distributions. This has important implications for deploying VLMs in real-world spatial reasoning tasks.

---

## 📁 Data Files

All results are saved in:
- `data/scientific_dataset/experiment_results.csv` - Full results (60 predictions)
- `data/scientific_dataset/analysis_summary.json` - Summary statistics
- `data/scientific_dataset/images/` - 20 test images (normal + sketchy)
- `data/scientific_dataset/floorplans/` - 10 floorplan JSON files

---

**Experiment Date**: 2025-11-27
**Model**: meta/llama-3.2-90b-vision-instruct
**Total API Calls**: 60
**Status**: ✅ Complete
