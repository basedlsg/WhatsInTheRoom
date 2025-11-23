# Large-Scale Experiment Log

## Experiment Configuration

**Date:** 2025-11-22-23
**Goal:** Generate maximum practical dataset to analyze VLM spatial reasoning

### Dataset Specifications - EXPANDED TO MASSIVE SCALE

- **Initial Target:** 1000 floorplans → **Expanded to 3000 floorplans**
- **Generated:** 2,391 valid floorplans (79.7% average success rate)
  - First batch: 783 floorplans (seeds 2000-2999, 78.3% success)
  - Second batch: 1,608 floorplans (seeds 3000-4999, 80.4% success)
- **Regions:** 6 (US_suburb, Modern_urban, Chinese_city_apartment, European_old_town, Japanese_apartment, Australian_house)
- **Size Categories:** 4 (micro, small, medium, large)
- **Stratification:** ~100 samples per region-size combination (24 combinations)

### Generation Performance

- **Time:** ~40 seconds
- **Speed:** ~20 floorplans/second
- **Validation failures:** 217/1000 (21.7%)
  - Primary cause: Isolated rooms (no door connections)
  - Secondary cause: Room overlaps (3 cases)

### Inference Configuration

- **Model:** meta/llama-3.2-90b-vision-instruct
- **API:** NVIDIA NIM
- **Batch delay:** 0.5 seconds
- **Prompt:** Mystery room identification with reasoning

### Inference Performance (In Progress)

- **Status:** Running on full expanded dataset
- **Progress:** 34/2391 (1.4%) after 2.5 minutes
- **Average time:** ~5 seconds/sample (varies with API response)
- **Estimated completion:** ~3.3 hours remaining
- **Total estimated time:** ~3.5 hours for complete dataset

## Expected Outcomes

### Statistical Power

With baseline accuracy of 9.21% from previous 76-sample run:
- Expected correct predictions: ~220/2391 (if accuracy holds)
- **31x larger sample size** than initial pilot study
- **3x larger than initial maximum target**
- Extremely robust statistical power for all analyses
- Narrow confidence intervals for per-region and per-size breakdowns
- Sufficient samples to detect subtle patterns in failure modes

### Analysis Capabilities

This dataset will enable:
1. **Robust accuracy metrics** across all regions and sizes
2. **Detailed confusion matrix** with statistical significance
3. **Failure pattern analysis** with dozens of examples per category
4. **Model bias quantification** (e.g., over-prediction of "closet")
5. **Spatial reasoning insights** from 783 detailed reasoning traces

### Research Questions

1. Does the 9.21% accuracy hold at scale?
2. Which regions are most challenging for the model?
3. Does model performance degrade with house complexity?
4. What are the most common misclassification patterns?
5. Can we identify systematic biases in spatial reasoning?

## Preliminary Findings (from 76-sample pilot)

- **Overall accuracy:** 9.21%
- **Model bias:** Heavy over-prediction of "closet" (26.3% of predictions)
- **Worst performance:** Kitchens (only 4/22 identified correctly)
- **Size effect:** Large houses (0% accuracy), Medium houses (14.81% best)
- **Regional variation:** Minimal (7-10% across all regions)

## Next Steps

1. Complete inference on 783 samples
2. Generate comprehensive visualizations
3. Perform statistical analysis of failure modes
4. Document findings in research summary
5. Consider prompt engineering experiments to improve performance

## Files Generated

```
data/
├── floorplans/          # 2,391 JSON metadata files (~2KB each)
├── images/              # 2,391 PNG renderings (~10KB each)
├── results/
│   └── predictions.parquet  # All predictions with reasoning
└── analysis/            # Plots and visualizations (generated post-inference)
```

**Total dataset size:** ~28.7 MB (5.8 MB JSON + 22.9 MB PNG + predictions)

## Notes

- All data synthetically generated (no external datasets)
- Deterministic with seed=2000 (fully reproducible)
- Real API calls (no mock data)
- All reasoning traces preserved for qualitative analysis
