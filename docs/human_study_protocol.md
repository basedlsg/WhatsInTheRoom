# FloorplanQA Human Baseline Study Protocol

## 1. Study Objective
To establish a human performance baseline for the FloorplanQA benchmark, enabling direct comparison between Vision-Language Models (VLMs) and human spatial reasoning capabilities. Specifically, we aim to:
1.  Quantify the "gap" between VLM and human performance.
2.  Compare expert (architects) vs. non-expert reasoning strategies.
3.  Validate the difficulty tier classification (Easy/Medium/Hard).

## 2. Participants
We will recruit two distinct cohorts:

### Cohort A: Experts (n=5-10)
- **Criteria**: Architecture students (3rd year+), professional architects, or civil engineers.
- **Recruitment**: University mailing lists, professional networks.
- **Compensation**: $15/hr equivalent (or volunteer).

### Cohort B: Non-Experts (n=20-30)
- **Criteria**: General population, no formal architecture training.
- **Recruitment**: Crowdworking platform (e.g., Prolific, MTurk) or convenience sampling.
- **Compensation**: Standard crowdworking rate (~$10-12/hr).

## 3. Stimuli Selection
From the `floorplan_qa_benchmark` dataset, we will select a balanced subset of **30 floorplans**:

- **Difficulty Balance**:
  - 10 Easy
  - 10 Medium
  - 10 Hard
- **Adversarial Balance**:
  - 15 Normal layouts
  - 15 Adversarial layouts (3 of each strategy: size, shape, window, adjacency, missing)
- **Rendering**:
  - All presented in `normal` rendering style to isolate spatial reasoning from visual noise initially.
  - *Optional extension*: 5 additional "sketchy" samples at the end.

## 4. Experimental Procedure
The study will be conducted via a web-based interface.

### Step 1: Onboarding
- **Consent Form**: Standard research consent.
- **Instructions**: Explanation of the "Mystery Room" task.
- **Tutorial**: 1 practice trial with feedback.

### Step 2: Main Task (30 Trials)
For each floorplan, participants will see:
1.  **Image**: The floorplan with the target room highlighted/unlabeled.
2.  **Question**: "Identify the type of the unlabeled room."
3.  **Response Fields**:
    - **Prediction**: Dropdown menu (Bedroom, Bathroom, Kitchen, Living Room, Office, Closet, Other).
    - **Confidence**: Likert scale (1=Guessing, 5=Certain).
    - **Reasoning**: "Why did you choose this?" (Short text, required for experts, optional for non-experts).

### Step 3: Exit Survey
- Demographics (Age, Education).
- Expertise check ("Have you ever designed a floorplan?").
- Strategy reflection ("What features did you look for?").

## 5. Metrics & Analysis
We will compute:
1.  **Accuracy**: % Correct (Overall, by Difficulty, by Adversarial Type).
2.  **Confidence-Accuracy Calibration**: Do humans know when they are wrong?
3.  **Inter-Rater Agreement**: Fleiss' kappa among humans.
4.  **VLM Gap**: `Human_Accuracy - VLM_Accuracy`.

## 6. Implementation Plan
- **Interface**: Simple HTML/JS web app (hosted locally or on GitHub Pages).
- **Backend**: Python script to serve images and save JSON responses.
- **Timeline**:
  - Design & Build: 2 days
  - Pilot (n=2): 1 day
  - Data Collection: 1 week
  - Analysis: 2 days
