# FloorplanQA Framework: Infrastructure Overview

**Audience**: Technical decision-makers, ML practitioners  
**Format**: Technical briefing (framework v0)

---

## Executive Summary

**FloorplanQA** is an open-source framework for testing spatial reasoning in AI vision systems. It generates synthetic floorplans and tests whether models can identify room types from geometric context.

**Current Status**: Infrastructure release (v0)  
**Target Use**: Research prototyping, not production deployment

---

## The Problem

Modern AI systems excel at recognizing objects in images but struggle with **spatial functional reasoning**—understanding *why* a space is designed the way it is based on its relationships to other spaces.

**Example**:  
A model might recognize "this is a small rectangular room" but fail to infer "this is a closet because it's 2m², attached to a bedroom, and has no windows."

This capability gap matters for:
- **Robotics**: Navigation planning requires understanding room function
- **Real Estate Tech**: Automated property analysis
- **Building Design**: AI-assisted architectural review

---

## Our Approach

### The Task: "Mystery Room"

Given a labeled floorplan with one unlabeled room, predict its type.

**Why this tests spatial reasoning:**
- No furniture or objects visible
- Must use geometric cues (size, adjacency, position)
- Requires functional knowledge (bathrooms are small and near bedrooms)

### The Framework Components

**1. Procedural Generation**
- Generates floorplans algorithmically (no manual drawing)
- Controlled difficulty tiers
- Regional architectural variations (US, European, Asian styles)

**2. Adversarial Testing**
- Intentionally confusing layouts:
  - Tiny living rooms
  - Houses without bathrooms
  - Bedrooms without windows
  - Implausible connections

**3. Analysis Pipeline**
- Statistical tools for performance analysis
- Bootstrap confidence intervals
- Stratified evaluation

---

## What's Included (v0)

### Infrastructure Code
✅ Floorplan generation engine  
✅ 5 adversarial strategies  
✅ Visual corruption pipeline  
✅ Statistical analysis tools  

### Pilot Dataset
- 258 unique floorplans
- 774 test samples (variants × styles)
- 6 room types

---

## What's NOT Included (v0)

❌ AI model performance results (no testing conducted)  
❌ Comparison baselines (heuristic, graph-based)  
❌ Balanced dataset (current version has imbalances)  
❌ Production-ready evaluation suite

---

## Known Limitations

### Dataset Issues
- **Imbalanced**: 35% living rooms, <1% balconies
- **Skewed difficulty**: 58% easy, 5% hard
- **Small scale**: 774 samples (need 5k+ for rigor)

### No Real Evaluation
- Models not tested (mock client only)
- No baseline comparisons

### Scope Constraints
- 2D only (no multi-floor)
- Synthetic (not real building scans)
- Residential only
- Simplified geometry

---

## Planned v1 (Roadmap)

**Dataset Regeneration:**
- 5,000 balanced samples
- Equal difficulty distribution
- Applied visual corruptions
- Regional metadata tracking

**Real Evaluations:**
- 3+ commercial AI models (GPT-4V, Claude, Gemini)
- Baseline comparisons

**Statistical Rigor:**
- Separate clean/adversarial/corruption test sets
- Mixed-effects models
- Pre-registered hypotheses

---

## Use Cases for v0

### ✅ Appropriate Uses
- Understanding spatial reasoning task design
- Prototyping evaluation pipelines
- Generating custom floorplan datasets
- Academic research on procedural generation

### ❌ Inappropriate Uses
- Claiming validated AI performance metrics
- Production deployment decisions
- Marketing "AI spatial IQ" scores
- Safety-critical system validation

---

## Technical Requirements

**Dependencies:**
```
Python 3.10+
numpy, pandas, matplotlib, pillow
scipy (statistics)
```

**Compute:**
- Dataset generation: ~1 min per 100 floorplans (CPU)
- Analysis: seconds (no GPU needed)

**Storage:**
- ~15 KB per floorplan image
- ~5 KB per metadata JSON

---

## Comparison to Existing Work

| Dataset | Task | Scale | Adversarial? | Open Source? |
|---------|------|-------|--------------|--------------|
| RPLAN | Generation | 80k | No | Yes |
| CubiCasa5K | Segmentation | 5k | No | Yes |
| **FloorplanQA v0** | **Function Inference** | **774** | **Yes** | **Yes** |

**Key differentiator**: Focus on reasoning, not detection or generation.

---

## Honest Assessment

**Strengths:**
- Well-engineered, reproducible code
- Adversarial strategies
- Clear task formulation
- Extensible architecture

**Weaknesses:**
- No validated results
- Small pilot dataset
- Statistical limitations
- Narrow scope (2D residential only)

**Bottom Line:**  
v0 is a **framework prototype**, not a complete benchmark. It demonstrates the approach but requires significant work before making performance claims.

---

## Getting Started

```bash
# Clone and install
git clone https://github.com/yourusername/FloorplanQA
cd FloorplanQA
pip install -r requirements.txt

# Generate custom dataset
python scripts/generate_publication_dataset.py --count 50

# Explore pilot data
python scripts/analyze_publication_results.py
```

---

## Roadmap Timeline

- **Q1 2025**: Framework v0 (current)
- **Q2 2025**: Dataset v1 (5k samples, balanced)
- **Q3 2025**: Evaluation v1 (real VLM)
- **Q4 2025**: Full benchmark release

---

## Contact & Contributions

**Repository**: [GitHub link]  
**Issues**: Report bugs or request features via GitHub Issues  
**Contributions**: Pull requests welcome (see CONTRIBUTING.md)

---

## Legal & Licensing

**License**: MIT  
**Data**: Synthetic, no privacy concerns  
**Commercial Use**: Permitted under MIT terms

---

## Disclaimer

This framework is provided for **research purposes**. 

**Do NOT use for:**
- Production AI system validation
- Safety-critical decision-making
- Marketing claims about "AI spatial intelligence"
- Deployment without additional testing

The current v0 dataset is a pilot demonstration. Results from this dataset should not be considered statistically rigorous or generalizable to real-world architectural reasoning tasks.

---

**Last Updated**: December 2025  
**Version**: 0.1 (Infrastructure Release)
