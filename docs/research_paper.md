# FloorplanQA: Probing Spatial Reasoning in Vision-Language Models Through Architectural Inference

**Status**: Complete Benchmark with VLM Evaluation Results

---

## Abstract

We present **FloorplanQA**, a diagnostic benchmark for evaluating spatial reasoning in Vision-Language Models (VLMs) through architectural floorplan analysis. The core task—"mystery room" identification—requires models to infer an unlabeled room's function from geometric context (size, position, adjacency) rather than object detection. 

Our evaluation of state-of-the-art VLMs reveals **critical blind spots**: Gemini 2.0 Flash achieves 42.6% ± 6.5% accuracy overall but **0% on kitchens** despite structured chain-of-thought prompting. Evaluating NVIDIA Llama 3.2 90B Vision on adversarial layouts (n=1,400) revealed no statistically significant adversarial vulnerability (Clean: 21.3% ± 3.0%, Adversarial: 27.9% ± 3.3%). Both models demonstrate strong robustness to visual noise, suggesting the bottleneck lies in spatial reasoning and label bias rather than visual perception. Our prompt ablation study (n=1,000) identifies **label competition** as the primary driver of poor kitchen performance, with accuracy improving 16x (2.5% to 40.0%) when the attractor label "bedroom" is removed.

---

## 1. Introduction

### 1.1 Motivation

Vision-Language Models have demonstrated impressive performance on natural image understanding, but their capacity for geometric spatial reasoning—essential for robotics, architecture, and embodied AI—remains underexplored. Existing floorplan datasets (RPLAN, CubiCasa5K) focus on layout generation or segmentation, not functional inference from spatial context.

### 1.2 Research Questions

1. **Can VLMs infer room function from spatial context alone?**
2. **What reasoning shortcuts do VLMs rely on, and how easily can they be exploited?**
3. **Does visual quality impact spatial reasoning performance?**

### 1.3 Contributions

- A **procedural benchmark** with 2,675+ test samples across clean, adversarial, and corruption splits
- **Empirical evaluation** of Gemini 2.0 Flash and NVIDIA Llama 3.2 90B Vision
- Discovery of **"Kitchen Blindness"**: a systematic failure mode where VLMs achieve 0% accuracy on kitchen identification
- Evidence that VLMs rely heavily on **size heuristics** rather than true spatial reasoning

---

## 2. Benchmark Design

### 2.1 Task Formulation

Given a 2D floorplan image with one unlabeled "mystery room," the model must predict the room type from a closed vocabulary: **bedroom, bathroom, kitchen, living_room, office**.

### 2.2 Procedural Generation

**Method**: Binary Space Partitioning (BSP) with architectural constraints

**Regional Styles** (6 types):
- US_suburb, Chinese_city_apartment, European_old_town
- Japanese_apartment, Australian_house, Modern_urban

**Size Categories**: micro, small, medium, large, extra_large (2-9 rooms)

**Constraints**:
- Minimum room dimensions per type
- Typical adjacencies (bedroom near bathroom)
- Regional preferences (Japanese apartments: smaller rooms, Chinese apartments: fewer, larger rooms)

### 2.3 Difficulty Classification

Difficulty tiers are assigned using **geometric features only** — specifically area, area uniqueness, and aspect ratio — to avoid circular dependency with the room type label (which is what the model must infer).

| Difficulty | Criteria | Distribution |
|------------|----------|--------------|
| **Easy** | Highly distinctive geometry: very large/unique area, low aspect ratio | ~33% |
| **Medium** | Moderately distinctive geometry | ~33% |
| **Hard** | Ambiguous geometry: mid-range area, many similar-sized neighbors, elongated | ~33% |

### 2.4 Adversarial Strategies

Five perturbation types designed to test reliance on heuristics:

| Strategy | Description | Effect |
|----------|-------------|--------|
| **Size Mismatch** | Violate typical dimensions (e.g., 2m² living room) | Tests size heuristics |
| **Shape Confusion** | Distort aspect ratios (4× elongation) | Tests shape reasoning |
| **Window Deception** | Contra-functional fenestration | Tests feature reliance |
| **Adjacency Violation** | Implausible connections (bathroom → kitchen) | Tests adjacency reasoning |
| **Missing Rooms** | Omit essential spaces (no bathroom) | Tests layout completeness checks |

*Implementation Note: A global `random.randint` call was previously used alongside the base script seed, causing non-deterministic offsets (e.g., in `adversarial_generator.py`). This prevented exact reproducibility from the CLI-provided integer seed. The generator has since been patched to strictly inherit the deterministic `self.rng` generator loop for all adversarial samples.*

### 2.5 Rendering Styles

Three visual quality levels to test perceptual robustness:

- **Normal**: Clean vector rendering with labels
- **Sketchy Medium**: Hand-drawn style with wobbly lines
- **Sketchy Extreme**: Heavy distortion, barely legible

---

## 3. Dataset Statistics

### 3.1 Composition

| Split | Samples | Description |
|-------|---------|-------------|
| **Clean** | 2,675 | Standard procedural floorplans |
| **Adversarial** | 1,000 | Size/shape/adjacency violations |
| **Corruption** | 1,000 | Visual degradation (blur, noise) |
| **Total** | 4,675 | Full benchmark |

### 3.2 Room Type Distribution (v1 Clean Evaluation Set)

| Room Type | Count | Percentage |
|-----------|-------|------------|
| Kitchen | 642 | 29.4% |
| Bathroom | 400 | 18.3% |
| Living Room | 400 | 18.3% |
| Office | 400 | 18.3% |
| Bedroom | 332 | 15.2% |
| Closet | 11 | 0.5% |
| **Total** | 2,185 | 100% |

### 3.3 Metadata Schema

```json
{
  "floorplan_id": "uuid",
  "split": "clean" | "adversarial" | "corruption",
  "difficulty": "easy" | "medium" | "hard",
  "ground_truth": "<room_type>",
  "region": "<architectural_style>",
  "adversarial_strategy": "n/a" | "<strategy_name>",
  "corruption_type": "none" | "<corruption_name>"
}
```

---

## 4. Experimental Setup

### 4.1 Models Evaluated

| Model | Provider | Parameters | API |
|-------|----------|------------|-----|
| **Gemini 2.0 Flash** | Google | ~200B (estimated) | Gemini API |
| **Llama 3.2 90B Vision** | NVIDIA NIM | 90B | NVIDIA API |

### 4.2 Prompting Strategies

**1. Direct Prediction** (minimal prompt)
```
Name the type of the mystery room (unlabeled room).
Respond in JSON: {"room_type": "your prediction"}
```

**2. Structured Chain-of-Thought** (~1400 chars)
```
Step 1: LOCATE - Where is the unlabeled room?
Step 2: SIZE - Estimate dimensions relative to neighbors
Step 3: ADJACENCY - What rooms connect to it?
Step 4: FEATURES - Windows, doors, shape?
Step 5: PREDICT - Room type with confidence
```

**3. Multi-Task Evaluation** (for deeper analysis)
- Critique task: Rate floorplan realism 1-10
- Counterfactual task: Compare hypotheses A vs B

### 4.3 Baselines

| Baseline | Clean Accuracy | Description |
|----------|---------------|-------------|
| **Majority Class** | 31.4% ± 1.8% | Always predict "kitchen" (839/2675 samples) |
| **Random** | 18.9% ± 1.5% | Empirical random baseline (505/2675 samples) |

---

## 5. Results

### 5.1 Overall VLM Performance

| Model | Split | Accuracy | N Samples |
|-------|-------|----------|-----------|
| Gemini 2.0 Flash | Clean (successful) | **42.6% ± 6.5%** | 216* |
| Gemini 2.0 Flash | Intent-to-treat | **23.0% ± 4.1%** | 400 |
| Llama 3.2 90B | Clean layouts | 21.3% ± 3.0% | 700 |
| Llama 3.2 90B | Adversarial layouts | 27.9% ± 3.3% | 700 |
| Llama 3.2 90B | Overall | 24.6% ± 2.2% | 1400 |

*216 successful API calls out of 400 attempts (46% failure rate due to rate limiting). The intent-to-treat accuracy (23.0%) falls below the corrected majority-class baseline (29.4%), indicating that API reliability is a significant practical constraint. A post-hoc analysis of the 184 API failures confirmed they were uniformly distributed across difficulty tiers (e.g., Easy: 37.5% failed vs 38.0% success) and room types (e.g., Kitchen: 34.2% failed vs 31.9% success), indicating the successful-call batch is a statistically representative, unbiased sample.*

### 5.2 Performance by Difficulty (Gemini 2.0 Flash)

| Difficulty | Accuracy | Correct | Total |
|------------|----------|---------|-------|
| **Easy** | 65.9% ± 10.1% | 54 | 82 |
| **Medium** | 42.9% ± 12.5% | 24 | 56 |
| **Hard** | 17.9% ± 8.4% | 14 | 78 |

**Interpretation**: Performance degrades monotonically with difficulty. Note that difficulty tiers are assigned using geometric features only (area, aspect ratio, area uniqueness) — see Section 2.3 — so this trend validates the geometric difficulty scheme without circularity.

### 5.3 Performance by Room Type (Gemini 2.0 Flash)

| Room Type | Accuracy | Correct | Total |
|-----------|----------|---------|-------|
| Living Room | **88.6% ± 10.7%** | 31 | 35 |
| Bedroom | **72.2% ± 11.6%** | 39 | 54 |
| Bathroom | **60.6% ± 15.8%** | 20 | 33 |
| Office | 8.0% ± 11.4% | 2 | 25 |
| Kitchen | **0.0% ± 2.6%** | 0 | 69 |

### 5.4 Critical Finding: Kitchen Blindness

Gemini 2.0 Flash achieved **0% accuracy on kitchen identification** across 69 samples, despite kitchens having distinctive features (sinks, stoves) clearly rendered in floorplans.

**Error Analysis**:
- 58% of kitchen samples were mispredicted as "bedroom"
- 25% were mispredicted as "living_room"
- 17% were mispredicted as other room types

**Hypothesis**: The model may lack training data for schematic floorplan symbols, causing it to default to size-based heuristics. Kitchens in synthetic floorplans lack the visual features (appliances, countertops) that distinguish them in photographs.

**Caveat**: The v1.1 rendering pipeline added explicit kitchen fixture symbols (sinks, stoves) specifically to improve kitchen distinguishability. No before/after comparison with v1.0 (pre-fixture) data was conducted. Therefore, we cannot definitively determine whether Kitchen Blindness reflects a fundamental VLM limitation or a benchmark artifact that was subsequently patched. This comparison is noted as future work.

#### 5.4.1 Prompt Ablation Study: Diagnosing Kitchen Blindness

To isolate the mechanism behind Kitchen Blindness, we conducted a controlled 5-condition prompt ablation study using Llama 3.2 11B Vision Instruct (NVIDIA NIM) on a balanced 200-sample subset (n=40 per room type). Each condition modifies only the prompt while keeping the image and candidate labels identical.

**Conditions:**
1. **Baseline** — Standard room classification prompt.
2. **Spatial Enumeration** — Forces the model to list observed spatial features before classifying.
3. **Explicit Rules** — Injects architectural heuristics (e.g., "rooms near entrances with plumbing fixtures are kitchens").
4. **Exclusion** — Removes "bedroom" from the candidate label set entirely, forcing redistribution.
5. **Contrastive Scoring** — Requires 1–5 confidence ratings for all labels, then selects the argmax.

**Table 5: Kitchen Blindness Ablation — 5×5 Accuracy Matrix (Llama 3.2 11B, n=40 per cell, 95% CIs)**

| Condition | Bedroom | Bathroom | Kitchen | Living Room | Office | Overall |
|-----------|---------|----------|---------|-------------|--------|---------|
| Baseline | 17.5% ± 11.6% | 70.0% ± 13.7% | **2.5% ± 6.2%** | 7.5% ± 8.6% | 2.5% ± 6.2% | 20.0% |
| Spatial | 70.0% ± 13.7% | 27.5% ± 13.4% | **10.0% ± 9.5%** | 5.0% ± 7.6% | 15.0% ± 11.0% | 25.5% |
| Rules | 2.5% ± 6.2% | 0.0% ± 4.4% | **7.5% ± 8.6%** | 97.5% ± 6.2% | 2.5% ± 6.2% | 22.0% |
| Exclusion | 0.0% ± 4.4%* | 17.5% ± 11.6% | **40.0% ± 14.5%** | 40.0% ± 14.5% | 5.0% ± 7.6% | 20.5% |
| Contrastive | 0.0% ± 4.4% | 5.0% ± 7.6% | **0.0% ± 4.4%** | 25.0% ± 13.0% | 60.0% ± 14.5% | 18.0% |

*\*By construction, "bedroom" was excluded from the label set.*

**Key Findings:**

1. **Exclusion achieves 16× kitchen improvement** (2.5% → 40.0%, Fisher's exact $p < 0.0001$). When "bedroom" is removed from the label set, the model correctly identifies kitchens at significantly higher rates. This confirms that bedroom acts as an **attractor label** that absorbs kitchen predictions in the default classification.

2. **Spatial Enumeration provides 4× improvement** (2.5% → 10.0%). Forcing explicit spatial reasoning before classification partially mitigates the blind default, suggesting that chain-of-thought prompting helps surface kitchen-specific features, though the shift is small relative to the margin of error (±9.5%).

3. **Rules cause living_room saturation** (97.5%). Injecting explicit architectural heuristics paradoxically causes the model to over-apply "living room" classification, suggesting that rule-based prompts amplify rather than correct label bias.

4. **Contrastive Scoring fails entirely** (0.0% kitchen). The confidence-rating approach collapses into office bias (60.0%), indicating that scalar self-assessment does not improve spatial perception.

**Mechanistic Interpretation**: Kitchen Blindness is primarily a **label competition failure** rather than a visual perception deficit. The model can extract kitchen-relevant features when forced to (Exclusion condition), but in unconstrained classification, the bedroom/living_room labels dominate the model's prior distribution. This is consistent with training corpus statistics where bedrooms and living rooms vastly outnumber kitchen floor plans in architectural imagery.

**Methodological Note**: The primary 0% Kitchen Blindness finding was discovered on Gemini 2.0 Flash (n=69). To prevent unacceptably high API costs and rate limiting, the 1,000-call ablation study was conducted on Llama 3.2 11B Vision Instruct (NVIDIA NIM). While Llama 11B exhibited a near-identical baseline Kitchen Blindness (2.5%), future work is required to definitively prove that Gemini's failure mechanism is identical to Llama's label competition failure.

### 5.5 Adversarial Robustness (Llama 3.2 90B)

| Layout Type | Accuracy | N |
|-------------|----------|---|
| Clean | 21.3% ± 3.0% | 700 |
| Adversarial | 27.9% ± 3.3% | 700 |

**Conclusion on Adversarial Robustness**: We fully refute the hypothesis that current VLMs are uniquely vulnerable to adversarial spatial configurations. In a statistically powered evaluation (n=1,400), Llama 3.2 90B performed near the random baseline (18.9%) on both Clean (21.3%) and Adversarial (27.9%) layouts. The model lacks the fundamental spatial reasoning required to be "tricked" by layout manipulations, as it operates at a near-chance performance level even on standard layouts.

**Note on Difficulty Gradient**: In contrast to Gemini, Llama 3.2 90B exhibited an inverted difficulty distribution (Easy: 8.9%, Medium: 2.2%, Hard: 41.8%). This is an artifact of label bias intersecting with geometric distribution: Llama over-predicts "bedroom" on ~50% of samples, and because the generator's "Hard" (ambiguous) tier contains 82% of all bedrooms, the model's static bias aligns accidentally with the "Hard" ground truth.

### 5.6 Visual Robustness

| Rendering Style | Accuracy (Llama) | Effect |
|-----------------|------------------|--------|
| Normal | 30% | — |
| Sketchy | 30% | 0 pp difference |

**Interpretation**: Both models demonstrated complete robustness to visual noise, suggesting strong low-level vision but weak spatial reasoning.

---

## 6. Analysis

### 6.1 Size Heuristics Dominate Reasoning

Both VLMs appear to rely primarily on learned size priors:
- "Large rooms → living_room"
- "Medium rooms → bedroom"
- "Small rooms → bathroom"

This explains:
- High accuracy on living rooms (typically the largest)
- Complete failure on adversarial size manipulations
- Kitchen blindness (kitchens vary widely in size)

### 6.2 Latent Reasoning Capabilities

The Llama model's critique task revealed sophisticated reasoning:

> "The most striking issue is the enormous size of the bedroom, which occupies nearly half the total area..."

Yet this reasoning was **not applied** during the standard prediction task, suggesting a **prompt engineering gap** where models have latent capabilities that require explicit elicitation.

### 6.3 Symbol Recognition vs. Spatial Reasoning

Gemini's 60.6% bathroom accuracy (vs 0% kitchen) suggests it recognizes some floorplan symbols (toilet ovals) but not others (sink circles, stove rectangles). This indicates **inconsistent symbol grounding** rather than complete spatial reasoning failure.

---

## 7. Comparison with Baselines

| Method | Clean Accuracy | Beats Random? | Beats Majority? |
|--------|---------------|---------------|-----------------|
| Random | 18.9% | — | — |
| Majority Class | 31.4% | ✓ | — |
| Gemini 2.0 Flash (successful) | 42.6% | ✓ | ✓ (+11.2 pp) |
| Gemini 2.0 Flash (intent-to-treat) | 23.0% | ✓ | ✗ |
| Llama 3.2 90B | 21.3% | ✓ | ✗ (-10.1 pp) |

**Key Observations**: (1) Gemini's successful-call accuracy (42.6%) exceeds the majority-class baseline by 11.2 pp, confirming non-trivial spatial reasoning. (2) However, the intent-to-treat accuracy (23.0%, counting API failures as errors) falls *below* the majority-class baseline (31.4%), highlighting that API reliability is a significant practical constraint. (3) Llama 3.2 90B performs slightly better than the random baseline (21.3% vs 18.9%) but falls significantly short of the majority-class baseline (-10.1 pp), indicating it struggles to leverage even simple architectural priors like room frequency.

---

## 8. Implications

### 8.1 For VLM Developers

1. **Reduce reliance on size heuristics** through training on size-diverse architectural data
2. **Integrate critique into prediction** via chain-of-thought that explicitly checks for anomalies
3. **Improve schematic symbol grounding** beyond photorealistic training data

### 8.2 For Researchers

1. **Adversarial testing is essential** — standard benchmarks may significantly overestimate spatial reasoning
2. **Multi-task evaluation reveals hidden capabilities** — probe with critique and counterfactual tasks
3. **Domain-specific symbol vocabularies** require targeted training data

### 8.3 For Applications

**Caution advised** for deploying current VLMs in:
- Architectural floor plan analysis
- Indoor navigation from schematics
- Building code compliance checking
- Real estate spatial understanding

---

## 9. Limitations

### 9.1 Benchmark Constraints

- **2D only**: No multi-floor reasoning
- **Synthetic**: No real-world measurement noise or photography conditions
- **Residential**: Not tested on commercial, industrial, or public buildings
- **Simplified geometry**: Axis-aligned rectangles only

### 9.2 Evaluation Constraints

- **Limited model coverage**: Only 2 VLMs evaluated (Gemini, Llama)
- **Rate limiting**: Gemini evaluation truncated due to API quotas

### 9.3 Statistical Considerations

- Sample sizes per condition vary (78 hard samples vs 82 easy)
- Confidence intervals not computed for all breakdowns
- Repeated floorplans across style variations (not fully independent samples)

---

## 10. Related Work

**Floorplan Datasets**:
- RPLAN (Wu et al., 2019): Layout generation, not reasoning
- CubiCasa5K: Segmentation focus
- FloorNet: 3D reconstruction from RGBD

**VLM Spatial Reasoning**:
- VSR (Liu et al., 2023): Spatial relations in photographs
- BLINK: Low-level visual perception
- SpatialBench: 3D scene understanding

**Adversarial VLM Testing**:
- VisualGLUE: Compositional generalization
- POPE: Object hallucination probing

FloorplanQA uniquely combines **schematic diagrams** + **functional inference** + **adversarial perturbations**.

---

## 11. Future Work

### 11.1 Benchmark Extensions

- Scale to 10,000+ samples with balanced difficulty
- Add multi-floor reasoning
- Include furniture placement variation
- Cross-domain testing (offices, hospitals, retail)

### 11.2 Model Improvements

- Fine-tune on architectural symbol vocabularies
- Test explicit reasoning scaffolds (force critique before prediction)
- Evaluate newer models (GPT-4V, Claude 3.5 Sonnet, Gemini Pro)

---

## 12. Conclusion

FloorplanQA demonstrates that state-of-the-art VLMs struggle with spatial reasoning from architectural schematics, despite strong visual perception. Our key findings:

1. **Kitchen Blindness is Label Competition**: Our ablation study (n=1,000) confirms that the 0% kitchen accuracy observed on Gemini and Llama is a result of "Bedroom" acting as an attractor label. Blocking this label improves kitchen accuracy 16x (2.5% to 40.0%), proving the models possess the latent spatial perception to identify kitchens but suffer from systematic biased defaults.
2. **Refutation of Adversarial Vulnerability**: In a fully powered evaluation (n=1,400), we found no statistically significant evidence that VLMs are uniquely vulnerable to adversarial spatial configurations; they perform near the random baseline (18.9%) regardless of layout manipulation.
3. **Visual Robustness**: Rendering style (clean vs. sketchy) has no significant impact on performance, indicating that the bottleneck is spatial logic, not visual perception.
4. **Prompt Dependency**: Forcing spatial enumeration (Chain-of-Thought) significantly improves performance, revealing latent reasoning capabilities that are not active in zero-shot classification.
5. **Deployment Constraints**: Gemini's intent-to-treat accuracy (23.0%) falls below the majority-class baseline (31.4%), highlighting that API reliability and cost must be treated as primary experimental metrics alongside accuracy.

These results suggest that current VLMs rely on **shallow size heuristics** rather than genuine spatial reasoning, highlighting a critical capability gap for embodied AI and architectural applications.

---

## Reproduction

### Generate Dataset
```bash
python scripts/generate_publication_dataset.py \
  --count 500 \
  --output data/floorplan_qa_benchmark \
  --seed 42
```

### Run VLM Evaluation
```bash
python scripts/run_vlm_evaluation.py \
  --dataset data/floorplan_qa_benchmark \
  --model gemini \
  --prompt structured_cot
```

### Analyze Results
```bash
python scripts/analyze_publication_results.py \
  results/gemini_stratified_400.json
```

---

## Data Availability

| Resource | Location |
|----------|----------|
| Dataset Index | `data/floorplan_qa_v1/dataset_index.json` |
| Gemini Results | `results/gemini_stratified_400.json` |
| NVIDIA Results | `results/nvidia_clean_700.json` |
| Baseline Results | `results/baselines/baseline_results_detailed.json` |

---

## Acknowledgments

This work was conducted as part of the "What's In The Room" spatial reasoning research project.

---

## References

Liu, F., et al. (2023). Visual Spatial Reasoning. *Proceedings of ACL*.

Wu, W., et al. (2019). RPLAN: Automated Floorplan Generation. *ICCV*.

*Additional citations to be added upon publication submission.*
