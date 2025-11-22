# What's in the Unlabeled Room?

An experiment to understand how vision-language models reason about spatial context in residential architecture by generating synthetic floorplans, rendering them with one unlabeled "mystery" room, and analyzing model predictions.

## Overview

This project generates thousands of synthetic residential floorplans programmatically, renders them as images with one unlabeled room, sends them to NVIDIA vision-language models for inference, and analyzes the results to understand spatial reasoning capabilities.

**Key Features:**
- Fully synthetic floorplan generation (no external datasets)
- Parameterized generation with region-specific architectural styles
- Realistic constraints (room adjacency, size requirements, connectivity)
- Integration with NVIDIA NIM vision-language models
- Comprehensive analysis and visualization tools

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd WhatsInTheRoom

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### 2. Generate Floorplans

```bash
# Generate 100 floorplans across different regions and sizes
python -m src.pipeline.generate_dataset \
    --count 100 \
    --regions US_SUBURB,MODERN_URBAN \
    --sizes SMALL,MEDIUM,LARGE \
    --floorplan-dir data/floorplans \
    --image-dir data/images
```

### 3. Run Inference

```bash
# Run VLM inference on generated floorplans
export NVIDIA_API_KEY="your-api-key-here"

python -m src.pipeline.run_inference \
    --floorplan-dir data/floorplans \
    --image-dir data/images \
    --output data/results/predictions.parquet \
    --batch-delay 0.5
```

### 4. Analyze Results

```bash
# Generate visualizations
python -m src.analysis.visualization \
    --predictions data/results/predictions.parquet \
    --output-dir data/analysis

# View the generated plots in data/analysis/
```

## Project Structure

```
WhatsInTheRoom/
├── src/
│   ├── core/              # Core data models and geometry
│   │   ├── geometry.py    # Point, Rectangle, collision detection
│   │   ├── types.py       # Enums (RoomType, RegionType, etc.)
│   │   └── models.py      # Floorplan, Room, Door, ModelPrediction
│   │
│   ├── generation/        # Floorplan generation logic
│   │   ├── generator.py   # Main generation orchestrator
│   │   ├── space_partition.py  # Binary space partitioning
│   │   ├── room_assigner.py    # Room type assignment
│   │   ├── door_placer.py      # Door placement logic
│   │   ├── constraints.py      # Region-specific rules
│   │   └── parameters.py       # Configuration constants
│   │
│   ├── rendering/         # Image rendering
│   │   ├── image_renderer.py  # PIL-based rendering
│   │   └── styles.py          # Visual styles
│   │
│   ├── inference/         # NIM API integration
│   │   ├── nim_client.py  # NVIDIA API client
│   │   ├── prompts.py     # Prompt templates
│   │   └── parsers.py     # Response parsing
│   │
│   ├── storage/           # Persistence layer
│   │   ├── floorplan_store.py  # JSON storage for floorplans
│   │   ├── image_store.py      # Image file management
│   │   └── results_store.py    # Parquet storage for predictions
│   │
│   ├── pipeline/          # Orchestration scripts
│   │   ├── generate_dataset.py  # Batch generation
│   │   └── run_inference.py     # Batch inference
│   │
│   └── analysis/          # Analysis and visualization
│       ├── aggregation.py       # Statistics and metrics
│       ├── visualization.py     # Plot generation
│       └── metrics.py           # Precision, recall, F1
│
├── data/
│   ├── floorplans/        # Generated metadata (JSON)
│   ├── images/            # Rendered floorplans (PNG)
│   ├── results/           # Predictions (Parquet)
│   └── analysis/          # Generated plots
│
├── tests/                 # Unit tests
├── CLAUDE.md             # Development guidelines
└── README.md             # This file
```

## Usage Examples

### Generate a Custom Dataset

```bash
# Generate 500 floorplans stratified across all regions and sizes
python -m src.pipeline.generate_dataset \
    --count 500 \
    --regions all \
    --sizes all \
    --seed 42

# Generate only Chinese city apartments
python -m src.pipeline.generate_dataset \
    --count 200 \
    --regions CHINESE_CITY_APARTMENT \
    --sizes MICRO,SMALL,MEDIUM
```

### Run Inference with Different Models

```bash
# Use a different NVIDIA model
python -m src.pipeline.run_inference \
    --model "meta/llama-3.2-11b-vision-instruct" \
    --max-samples 50 \
    --batch-delay 1.0
```

### Analyze Specific Subsets

```python
from src.storage.results_store import load_predictions
from src.analysis.aggregation import calculate_accuracy_by_region, print_summary, generate_summary_stats

# Load predictions
predictions = load_predictions("data/results/predictions.parquet")

# Filter to specific region
us_suburb_preds = [p for p in predictions if p.metadata.get('region') == 'US_suburb']

# Calculate accuracy
accuracy = calculate_accuracy_by_region(us_suburb_preds)
print(accuracy)

# Generate full summary
stats = generate_summary_stats("data/results/predictions.parquet")
print_summary(stats)
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
NVIDIA_API_KEY=your_api_key_here

# Optional (defaults provided)
NVIDIA_NIM_ENDPOINT=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL_NAME=meta/llama-3.2-90b-vision-instruct

# Data directories
DATA_DIR=data
FLOORPLANS_DIR=data/floorplans
IMAGES_DIR=data/images
RESULTS_DIR=data/results
ANALYSIS_DIR=data/analysis
```

### Region Types

Available architectural regions:
- `US_SUBURB`: American suburban homes (larger rooms, open-plan)
- `CHINESE_CITY_APARTMENT`: Compact Chinese urban apartments
- `EUROPEAN_OLD_TOWN`: European traditional layouts
- `JAPANESE_APARTMENT`: Japanese residential style
- `AUSTRALIAN_HOUSE`: Australian homes (very open-plan)
- `MODERN_URBAN`: Contemporary urban design

### Size Categories

- `MICRO`: < 40 m² (studio apartments)
- `SMALL`: 40-80 m² (1-2 bedroom apartments)
- `MEDIUM`: 80-150 m² (2-3 bedroom homes)
- `LARGE`: 150-250 m² (4+ bedroom homes)
- `EXTRA_LARGE`: > 250 m² (large houses)

## Development

### Adding a New Region

1. Add to `RegionType` enum in `src/core/types.py`
2. Define constraints in `src/generation/constraints.py` (REGION_CONFIGS)
3. Update tests in `tests/test_generation.py`

### Adding a New Room Type

1. Add to `RoomType` enum in `src/core/types.py`
2. Define typical dimensions in `src/generation/parameters.py` (ROOM_AREA_RANGES)
3. Add adjacency rules in `src/generation/constraints.py` if needed

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_generation.py
```

## Experiment Design

### The Core Question

Can a vision-language model infer the type of an unlabeled room based solely on:
- Its size and proportions
- Its spatial position in the layout
- Which rooms it connects to via doors
- The overall architectural context

### Mystery Room Selection

The system selects mystery rooms that are:
- Ambiguous (e.g., closet vs. storage, office vs. bedroom)
- Connected (not isolated)
- Not the only instance of their type (unless highly ambiguous)

High-priority candidates:
- Closet
- Office/Study
- Storage room
- Guest bedroom
- Pantry
- Utility room

### Prompt Strategy

The default prompt asks the model to:
1. Identify the unlabeled room
2. Predict its type
3. Explain reasoning in 1-3 sentences

The prompt can optionally include metadata (region, size) for context.

## Analysis Capabilities

### Metrics

- **Overall Accuracy**: % of correct predictions
- **Accuracy by Region**: Performance across architectural styles
- **Accuracy by Size**: Performance across floorplan sizes
- **Confusion Matrix**: True vs. predicted room types
- **Precision/Recall/F1**: Per-room-type metrics

### Visualizations

Generated automatically:
- Accuracy by region (bar chart)
- Accuracy by size category (bar chart)
- Prediction distribution (horizontal bar chart)
- Confusion matrix (heatmap)

## Performance Notes

### Generation

- ~5-20 floorplans/second on modern hardware
- Memory usage: ~50MB per 1000 floorplans
- Deterministic with seed (reproducible)

### Inference

- Rate limited by NVIDIA API (~0.5-2 seconds per request)
- Recommend `--batch-delay 0.5` to avoid rate limiting
- Can process ~1000 floorplans in ~15-30 minutes

### Storage

- Floorplan metadata: ~2-5KB per JSON file
- Rendered images: ~10-15KB per PNG file
- Predictions: ~500 bytes per row in Parquet

## Troubleshooting

### "No module named 'src'"

Make sure you're running commands from the project root:
```bash
cd WhatsInTheRoom
python -m src.pipeline.generate_dataset ...
```

### API Rate Limiting

If you hit rate limits:
```bash
# Increase batch delay
python -m src.pipeline.run_inference --batch-delay 2.0

# Or process in smaller batches
python -m src.pipeline.run_inference --max-samples 100
```

### Validation Errors

Some generated floorplans may fail validation (isolated rooms). This is normal - the system will retry. If you see many failures, check:
- Room count matches target
- All rooms have doors
- Mystery room is not isolated

### Memory Issues

For large datasets (>10K floorplans):
- Process in batches
- Use `--max-samples` to limit memory usage
- Consider using CSV instead of Parquet for predictions

## Citation

If you use this code in your research, please cite:

```bibtex
@software{whats_in_the_room_2024,
  title={What's in the Unlabeled Room? Probing Spatial Reasoning in Vision-Language Models},
  author={[Your Name]},
  year={2024},
  url={https://github.com/[your-username]/WhatsInTheRoom}
}
```

## License

MIT License (or your chosen license)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See `CLAUDE.md` for development guidelines and coding standards.

## Acknowledgments

- NVIDIA NIM for vision-language model inference
- Claude Code for development assistance
