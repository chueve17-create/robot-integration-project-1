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

Extraction results (`extracted_frames/`): 950 frames total (comb 323, mouse 292, together 159, negative 176).

### 3. Dataset thinning
To keep the labeling workload manageable and reduce redundancy between adjacent frames, an evenly-spaced sampling script (`scripts/sample_frames.sh`) was used to thin the extracted frames. Sampling uses a fixed stride across the full sequence, preserving the angle/pose variation across the entire clip rather than simply taking the first N frames.

Thinning results (`sampled_frames/`): 520 frames total (comb 180, mouse 180, together 120, negative 40).

### 4. Split strategy
The final split into train / val / test is done by source video (shooting batch) rather than by randomly shuffling individual frames. This avoids near-duplicate frames from the same clip leaking across splits, keeping val/test evaluation results honest.

## Annotation workflow

A semi-automated "manual seed labels + model-assisted pre-labeling + manual review" workflow was used, all annotations reviewed and confirmed by hand:

1. **Seed labeling**: ~40 representative images each for comb and mouse were manually annotated using Roboflow (YOLO format), forming the labeling baseline (83 images total, merged into `seed_dataset/` with class indices remapped via `scripts/merge_seed_data.sh`).
2. **Assist model training**: A YOLOv8n model was trained on the seed data for 30 epochs (not for accuracy, only to assist labeling). Result: mAP50 0.995 on the small seed validation set — sufficient to bootstrap pre-labeling.
3. **Auto pre-labeling**: The assist model (`scripts/auto_prelabel.py`) ran inference on all 520 sampled frames (comb, mouse, together, negative), generating candidate YOLO-format bounding boxes and preview images for review. 513/520 images received at least one detection.
4. **Manual review**: All 520 images were re-uploaded to Roboflow together with their auto-generated labels (using a `labelmap.txt` to map class indices to names) and reviewed by hand — wrong boxes corrected, missed detections added, false positives (mainly on `negative` images) removed.

The final reviewed dataset lives in `DataSet/` with 364 train / 104 val / 52 test images, `nc: 2`, `names: [comb, mouse]`.

## Current progress
- [x] Video capture
- [x] Frame extraction
- [x] Dataset thinning
- [x] Seed data labeling
- [x] Assist model training
- [x] Auto pre-labeling
- [x] Manual review (Roboflow)
- [ ] Full training (in progress)
- [ ] Model evaluation (mAP, precision/recall on held-out test set)
- [ ] Jetson deployment
- [ ] ROS2 integration

## Directory structure
```
E4_object_detection/
├── raw_videos/           Raw video footage (not tracked in git)
├── extracted_frames/     Full extracted frames, 950 images (not tracked in git)
├── sampled_frames/       Thinned image set, 520 images (not tracked in git)
├── seed_labels/          Seed annotation results from Roboflow, per-class (not tracked in git)
├── seed_dataset/         Merged seed dataset used to train the assist model (not tracked in git)
├── pre_labels/           Auto-generated candidate labels from the assist model (not tracked in git)
├── pre_labels_preview/   Preview images with predicted boxes drawn, for quick review (not tracked in git)
├── DataSet/              Final reviewed dataset: train/valid/test, ready for training (not tracked in git)
├── labelmap.txt          Class index-to-name mapping used for Roboflow re-import during review
├── scripts/
│   ├── extract_frames.sh     Batch video frame extraction script
│   ├── sample_frames.sh      Dataset thinning/sampling script
│   ├── merge_seed_data.sh    Merges per-class seed labels into one dataset with remapped class ids
│   └── auto_prelabel.py      Runs the assist model on all images to generate candidate labels
└── data.yaml              YOLO training config file (in DataSet/)
```
