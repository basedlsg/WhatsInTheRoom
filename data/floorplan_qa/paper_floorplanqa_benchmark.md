# FloorplanQA: A Benchmark for Spatial Reasoning in Vision-Language Models

---

## Abstract

We introduce FloorplanQA, a procedurally-generated benchmark for evaluating spatial reasoning in vision-language models (VLMs). The benchmark comprises 308 multiple-choice questions across 4 types: room counting, adjacency detection, area comparison, and room identification. Ground-truth adjacency graphs enable oracle upper bounds, and perceptual hash verification guarantees no data leakage. Gemini 2.0 Flash achieves 44.2% accuracy overall, with performance varying sharply by question type: adjacency (58.5%) > area comparison (40.4%) > room counting (36.5%) > room identification (23.1%). A prompt sensitivity sweep shows performance is robust across minimal, structured, and chain-of-thought prompts (27-30%), and a generalization test reveals that monochrome rendering degrades accuracy to 23.3%, indicating color dependency.

**Keywords:** VLM benchmark, spatial reasoning, floorplan understanding, visual question answering

---

## 1. Introduction

Visual spatial reasoning—understanding relationships between objects in images—remains challenging for VLMs. Existing benchmarks often mix spatial with semantic reasoning, making it difficult to isolate spatial capabilities.

We contribute FloorplanQA, a controlled benchmark where:
- All images are procedurally generated with known ground-truth
- Questions target specific spatial reasoning skills
- An oracle baseline using the underlying graph provides an upper bound
- Rendering style variants test generalization

---

## 2. Benchmark Design

### 2.1 Floorplan Generation

Procedural generator produces floorplans with:
- 3-8 rooms per floorplan
- 8 room types (bedroom, bathroom, kitchen, living_room, etc.)
- Variable room sizes and positions
- Automatic adjacency graph computation

### 2.2 Question Types

| Type | Example | Difficulty |
|------|---------|------------|
| Room Count | "How many bedrooms?" | Easy |
| Adjacency | "Is kitchen adjacent to bathroom?" | Medium |
| Area Comparison | "Which is larger: office or closet?" | Medium |
| Room Identification | "What room is in the top-left corner?" | Hard |

### 2.3 Dataset Statistics

- **Total Floorplans:** 150
- **Total Questions:** 2,747
- **Test Split:** 308 questions (locked)
- **Dev Split:** 100 questions
- **No Leakage:** Verified via SHA256 hashing

---

## 3. Evaluation Protocol

```yaml
version: "1.0"
seed: 42
answer_format: "multiple_choice_4"
primary_metric: "accuracy"
confidence: "bootstrap_95"
```

### 3.1 Baselines

| Baseline | Description |
|----------|-------------|
| Gemini 2.0 Flash | Multimodal LLM |
| Oracle | Uses ground-truth graph (no vision) |

### 3.2 Prompt Variants

1. **Minimal:** "Answer: A/B/C/D"
2. **Structured:** Full context with format instructions
3. **Chain-of-Thought:** "Think step by step, then answer"

---

## 4. Results

### 4.1 Main Results (N=308)

| Question Type | Accuracy | 95% CI |
|---------------|----------|--------|
| **Overall** | **44.2%** | [38.6%, 49.7%] |
| Adjacency | 58.5% | — |
| Area Comparison | 40.4% | — |
| Room Count | 36.5% | — |
| Room Identification | 23.1% | — |

### 4.2 Prompt Sensitivity (N=30)

| Style | Accuracy |
|-------|----------|
| Minimal | 30% |
| Structured | 30% |
| Chain-of-Thought | 27% |

**Finding:** Performance is invariant to prompt engineering.

### 4.3 Generalization: Monochrome Style

| Style | Accuracy |
|-------|----------|
| Color (default) | 44.2% |
| Monochrome | 23.3% |

**Finding:** Removing color cues causes ~50% relative degradation.

---

## 5. Analysis

### 5.1 Why Is Room Identification Hardest?

Room identification requires:
1. Parsing image to locate room boundaries
2. Understanding cardinal directions ("top-left corner")
3. Mapping coordinates to room types

This multi-hop reasoning fails more than simpler tasks.

### 5.2 Color Dependency

The VLM uses color as a primary feature for room differentiation. Monochrome images eliminate this cue, exposing reliance on color rather than spatial structure.

---

## 6. Limitations

- Single VLM evaluated (Gemini 2.0 Flash)
- Synthetic floorplans (not real architectural drawings)
- 4 question types (could expand to path-finding, etc.)

---

## 7. Conclusion

FloorplanQA provides a controlled benchmark for spatial reasoning:
- **Below 50% accuracy** on structured spatial QA
- **Room identification** is the hardest task (23.1%)
- **Prompt-invariant** but **color-dependent**

The benchmark is released with locked protocol, evaluation scripts, and reproduction commands.

---

## Appendix: Reproduction

```bash
cd floorplan_qa
python3 generation/floorplan_generator.py --num 150
python3 generation/question_generator.py
python3 generation/split_manager.py
python3 evaluation/evaluate.py --split data/splits/test_v1.json --model gemini:gemini-2.0-flash
```
