# FloorplanQA Reproduction Guide

This guide details how to reproduce the entire FloorplanQA dataset and benchmark results from scratch.

## 1. Environment Setup

Ensure you have Python 3.10+ installed.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install numpy pandas matplotlib seaborn pillow tqdm python-dotenv requests scipy
```

## 2. Dataset Generation

To regenerate the publication-grade dataset (180 floorplans target):

```bash
python scripts/generate_publication_dataset.py \
  --count 180 \
  --output data/floorplan_qa_benchmark_repro \
  --seed 42
```

This script handles:
- Procedural generation of layouts.
- Adversarial modification.
- Rendering in multiple styles.
- Application of image corruptions.
- Metadata indexing.

## 3. Running Experiments

To evaluate a model (e.g., Llama-3.2-90b-vision via NVIDIA NIM):

1. Set your API key in `.env`:
   ```
   NVIDIA_API_KEY=your_key_here
   ```

2. Run the experiment:
   ```bash
   python scripts/run_publication_experiment.py \
     --dataset data/floorplan_qa_benchmark_repro/dataset_index.json \
     --output results/reproduction_results.csv \
     --prompt-type structured_cot \
     --real
   ```

## 4. Statistical Analysis

To generate the tables and figures used in the paper:

```bash
python scripts/analyze_publication_results.py \
  results/reproduction_results.csv \
  --output analysis_repro/
```

## 5. Human Study (Optional)

To run the human baseline interface locally:

```bash
python src/human_study/study_server.py
```
Access at `http://localhost:8001`.

To simulate human data:
```bash
python scripts/simulate_human_data.py
python scripts/analyze_human_data.py
```
