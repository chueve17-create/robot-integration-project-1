# Comb and Mouse YOLO Dataset

## Classes
`0 comb`, `1 mouse`

## Class selection
Comb and mouse were chosen as the target classes because they differ clearly in shape (elongated with teeth vs. compact and rounded), material, and color, making them easier for the model to distinguish. This follows the course guidance to pick classes with strong feature differences.

## Data collection pipeline

### 1. Video capture
Short video clips were recorded on a phone camera, covering four types of footage:

| Type | Clips | Description |
|---|---|---|
| comb only | 5 | Comb alone, varying angle, background, lighting, and distance |
| mouse only | 5 | Mouse alone, varying angle, background, lighting, and distance |
| together | 4 | Comb and mouse in the same frame, to train multi-object recognition |
| negative | 3 | Only unrelated objects (cup, phone, pen, etc.), no comb or mouse, to reduce false positives on unseen objects |

Clips were shot with slow camera/object movement to cover a range of angles, backgrounds, lighting conditions, and distances. Some clips deliberately include partial occlusion or multiple objects in frame to improve model robustness.

### 2. Frame extraction
Frames were sampled at approximately 3 FPS from the source clips using `ffmpeg` (see `scripts/extract_frames.sh`), avoiding the large number of near-duplicate frames that would result from keeping every frame.

Extraction results (`extracted_frames/`):

| Class | Frame count |
|---|---|
| comb | 323 |
| mouse | 292 |
| together | 159 |
| negative | 176 |
| **Total** | **950** |

### 3. Dataset thinning
To keep the labeling workload manageable and reduce redundancy between adjacent frames, an evenly-spaced sampling script (`scripts/sample_frames.sh`) was used to thin the extracted frames. Sampling uses a fixed stride across the full sequence, preserving the angle/pose variation across the entire clip rather than simply taking the first N frames.

Thinning results (`sampled_frames/`):

| Class | Target | Kept |
|---|---|---|
| comb | 180 | 180 |
| mouse | 180 | 180 |
| together | 120 | 120 |
| negative | 40 | 40 |

### 4. Split strategy
The split into train / val / test is done by source video (shooting batch) rather than by randomly shuffling individual frames. This avoids near-duplicate frames from the same clip leaking across splits, keeping val/test evaluation results honest.

## Annotation workflow

A semi-automated "manual seed labels + model-assisted pre-labeling + manual review" workflow is used:

1. **Seed labeling**: ~30-40 representative images each for comb and mouse were manually annotated using `labelImg` (YOLO format), forming the labeling baseline.
2. **Assist model training**: A lightweight model is trained on the seed data for a small number of epochs, used only to assist labeling rather than for accuracy.
3. **Auto pre-labeling**: The assist model runs inference on the remaining unlabeled images to generate candidate bounding boxes.
4. **Manual review**: Every pre-labeled image is checked by hand — wrong boxes are corrected, missed detections are added, false detections are removed — to ensure final label quality.

All annotations are reviewed and confirmed by hand; the model is only used to speed up the process, not to replace manual verification.

## Current progress
- [x] Video capture
- [x] Frame extraction
- [x] Dataset thinning
- [ ] Seed data labeling (in progress)
- [ ] Assist model training
- [ ] Auto pre-labeling
- [ ] Manual review
- [ ] Full training

## Directory structure
```
E4_object_detection/
├── raw_videos/           Raw video footage (not tracked in git)
├── extracted_frames/     Full extracted frames (not tracked in git)
├── sampled_frames/       Thinned image set (not tracked in git)
├── seed_labels/          Seed annotation results (not tracked in git; may be added once labeling is complete)
├── scripts/
│   ├── extract_frames.sh    Batch video frame extraction script
│   └── sample_frames.sh     Dataset thinning/sampling script
└── data.yaml              YOLO training config file
```
