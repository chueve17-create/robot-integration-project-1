# Cup and Mouse YOLO Dataset

Classes: `0 cup`, `1 mouse`.

Frames were sampled at approximately 3 FPS from the source clips.
The split is by whole source video to avoid near-duplicate frame leakage.
Annotations were reviewed against the source frames, corrected at the supplied examples, and then refined across similar frames using a pretrained detector only when class, confidence, and box geometry agreed with the existing annotation.

The raw images are unmodified; YOLO boxes are stored in the matching files under `labels/`. Rendered previews with visible boxes are in `visualized/`.

The correction audit is saved at `../Output/reports/annotation_feedback_corrections.json` and the full refinement audit at `../Output/reports/pretrained_refinement.json`.
The manually verified adjacent-frame sequence corrections are recorded at `../Output/reports/followup_sequence_corrections.json`.
