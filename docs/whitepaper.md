# AI Robustness in Spatial Domains: The FloorplanQA Whitepaper

## Executive Summary
As AI systems are increasingly deployed in physical world applications—from autonomous robotics to automated facility management—their ability to reason spatially is becoming business-critical. **FloorplanQA** is a new diagnostic tool designed to stress-test Vision-Language Models (VLMs) on their ability to understand architectural layouts. Our findings reveal that while current models are promising, they remain brittle when faced with "adversarial" layouts that defy standard conventions, posing risks for deployment in safety-critical or high-precision environments.

## The Challenge: Beyond Object Detection
Traditional computer vision excels at identifying objects ("this is a chair"). However, spatial reasoning requires understanding context ("this chair is in a room next to a kitchen, so it's likely a dining room"). This higher-order logic is essential for:
- **Real Estate Tech**: Automated property valuation and description.
- **Robotics**: Navigation planning in unseen environments.
- **AEC (Architecture, Engineering, Construction)**: Automated code compliance checking.

## Our Methodology
We developed a rigorous testing framework comprising:
1.  **774 Test Cases**: Ranging from simple to highly ambiguous layouts.
2.  **Adversarial Stress Tests**: Intentionally confusing layouts (e.g., tiny rooms, missing windows) to expose model biases.
3.  **Visual Corruption**: Testing performance under poor image quality (blur, low contrast).

## Key Findings

### 1. The "Expert Gap"
We compared AI performance against human architects.
- **Human Experts**: 84% Accuracy
- **AI Models**: ~45-55% Accuracy (varies by model)
*Implication*: AI is currently performing at the level of a non-expert layperson, not a professional.

### 2. Fragility to Anomalies
Models performed well on standard layouts but failed significantly when rules were broken (e.g., a bathroom opening into a kitchen).
*Implication*: Current AI relies on surface-level pattern matching rather than deep functional understanding.

### 3. The Value of "Chain of Thought"
Forcing models to "show their work" (step-by-step reasoning) improved accuracy by ~15%.
*Recommendation*: Deployments should utilize structured prompting strategies to enhance reliability.

## Recommendations for Industry
1.  **Human-in-the-Loop**: For now, AI should assist rather than replace human experts in spatial tasks.
2.  **Robustness Testing**: Use benchmarks like FloorplanQA to validate models before deployment.
3.  **Prompt Engineering**: Invest in structured reasoning prompts (CoT) to unlock maximum model performance.

## Conclusion
FloorplanQA serves as a standard for measuring "Spatial AI IQ." By highlighting current limitations, we aim to drive the development of more robust, reasoning-capable AI systems for the physical world.
