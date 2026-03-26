# FloorplanQA Benchmark

VLM spatial reasoning benchmark on procedurally-generated floorplans.

## Structure
- `config/` - Benchmark configuration (locked)
- `data/` - Generated floorplans and questions
- `generation/` - Floorplan and question generators
- `evaluation/` - Evaluation scripts and baselines

## Quick Start
```bash
python3 generation/floorplan_generator.py --num 150
python3 generation/question_generator.py
python3 evaluation/evaluate.py --split data/splits/test_v1.json
```

