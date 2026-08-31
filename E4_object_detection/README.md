# Comb and Mouse Detection on Jetson Orin NX

This module implements a two-class object detector for **comb** and **mouse**, trained with Ultralytics YOLO and deployed on an NVIDIA Jetson Orin NX through ROS 2 Humble.

## Classes

| Class ID | Class name |
|---:|---|
| 0 | `comb` |
| 1 | `mouse` |

The two classes differ strongly in shape: a comb is elongated and has repeated teeth, while a mouse is compact and rounded. This makes them suitable for demonstrating multi-class object detection while still presenting realistic challenges such as partial occlusion and dark backgrounds.

## Final status

- [x] Video-based data collection
- [x] Frame extraction and redundancy reduction
- [x] Seed labeling in Roboflow
- [x] Model-assisted pre-labeling
- [x] Manual annotation review
- [x] Initial YOLO training and evaluation
- [x] Hard-negative data collection
- [x] Incremental fine-tuning
- [x] Jetson Orin NX deployment
- [x] ROS 2 image subscription and detection publishing
- [x] Real-time camera validation

## Data collection and annotation

### Initial dataset

Short videos were recorded under varied angles, distances, lighting conditions, backgrounds, and occlusion levels. The original footage covered four scene types:

| Type | Description |
|---|---|
| `comb` | Comb-only scenes |
| `mouse` | Mouse-only scenes |
| `together` | Comb and mouse in the same frame |
| `negative` | Cluttered or unrelated scenes used to reduce false positives |

Frames were extracted at approximately 3 FPS with `scripts/extract_frames.sh`, then evenly sampled with `scripts/sample_frames.sh` to reduce near-duplicate images.

Annotation used a semi-automated workflow:

1. Representative seed images were manually annotated in Roboflow.
2. A small assist model generated candidate YOLO annotations.
3. All candidate boxes were reviewed in Roboflow.
4. Incorrect boxes were removed and missed objects were added manually.

### Expanded dataset and hard-negative mining

During the first Jetson camera test, the initial model occasionally classified keyboard corners and dark regions as `mouse`. To address this, additional deployment-domain footage was collected with the same camera setup:

- keyboard corners and dark regions without target objects;
- combs and mice near visually confusing background objects;
- varied object positions, orientations, distances, and lighting.

The new frames were pre-labeled by the initial model and manually corrected in Roboflow. Pure background frames were explicitly reviewed and marked as null annotations. The final exported YOLOv8 dataset contains:

| Split | Images |
|---|---:|
| Train | 707 |
| Validation | 104 |
| Test | 52 |
| **Total** | **863** |

The final training split contains 148 empty-label images for hard-negative learning. Mixed polygon and bounding-box annotations exported from Roboflow were normalized to standard five-column YOLO detection labels before final training. Dataset images and labels are excluded from Git because of their size.

## Training

The final detector was trained from the pretrained Ultralytics YOLOv8n checkpoint after all annotations were normalized to detection-box format.

```bash
yolo detect train \
  data=DataSet_v2/data.yaml \
  model=yolov8n.pt \
  epochs=100 \
  imgsz=640 \
  batch=16 \
  project=training_results \
  name=dataset_v3_fixed \
  amp=False
```

Training hardware: NVIDIA GeForce RTX 4060 Laptop GPU with 8 GB VRAM.

### Final validation results

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| `comb` | 65 | 67 | 0.998 | 0.985 | 0.985 | 0.848 |
| `mouse` | 82 | 89 | 0.920 | 0.899 | 0.971 | 0.825 |
| **all** | **104** | **156** | **0.959** | **0.942** | **0.978** | **0.837** |

### Final test-set results

The selected checkpoint was evaluated on all 52 test images after annotation-format correction.

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| `comb` | 32 | 32 | 1.000 | 0.997 | 0.995 | 0.860 |
| `mouse` | 36 | 41 | 0.901 | 0.951 | 0.965 | 0.853 |
| **all** | **52** | **73** | **0.951** | **0.974** | **0.980** | **0.856** |

The final checkpoint is stored at:

```text
models/best_v3.pt
```

## Jetson and ROS 2 deployment

### Tested platform

- NVIDIA Jetson Orin NX
- Ubuntu 22.04
- Python 3.10.12
- ROS 2 Humble
- CUDA-enabled PyTorch
- Ultralytics YOLO
- USB camera publishing ROS images

### Deployment components

| File | Purpose |
|---|---|
| `jetson_deploy/ros2_detection_node.py` | Main ROS 2 detection node |
| `jetson_deploy/video_input.py` | Video input helper |
| `jetson_deploy/fps_overlay.py` | FPS overlay |
| `jetson_deploy/result_publisher.py` | Converts and publishes detection results |

The detection node subscribes to:

```text
/camera/image_raw
```

and publishes detection results as `vision_msgs/Detection2DArray` messages on:

```text
/detections
```

### Run the detector

Place the final weight next to the deployment script using the filename expected by the code:

```bash
cp models/best_v3.pt jetson_deploy/best.pt
cd jetson_deploy
```

Activate the Python environment and load ROS 2:

```bash
source /path/to/yolov8_env/bin/activate
source /opt/ros/humble/setup.bash
python ros2_detection_node.py
```

In a second terminal, publish the USB camera stream:

```bash
source /opt/ros/humble/setup.bash
ros2 run image_tools cam2image --ros-args -r image:=/camera/image_raw
```

The detector opens a `YOLO Detection` window with bounding boxes, class labels, confidence values, and an FPS overlay.

### Verify ROS 2 topics

```bash
ros2 topic list
ros2 topic info /camera/image_raw
ros2 topic echo /detections
```

The camera topic should report at least one publisher while `cam2image` is running.

## Deployment validation

The final model was tested using a live USB camera on the Jetson Orin NX. Validation included:

- correct detection of a mouse;
- correct detection of a comb;
- simultaneous and cluttered scenes;
- keyboard corners and dark areas that previously caused false positives.

The hard-negative fine-tuning substantially reduced the observed false positives while preserving real-time inference.

## Repository structure

```text
E4_object_detection/
├── config/
│   └── dataset_v2/          Dataset v2 metadata and Roboflow attribution
├── jetson_deploy/           ROS 2 deployment code
├── models/
│   ├── best_v2.pt           Previous Jetson-tested checkpoint
│   └── best_v3.pt           Final expanded-dataset checkpoint
├── scripts/
│   ├── extract_frames.sh
│   ├── sample_frames.sh
│   ├── merge_seed_data.sh
│   └── auto_prelabel.py
├── labelmap.txt              Class order: comb, mouse
├── raw_videos/               Not tracked in Git
├── extracted_frames/         Not tracked in Git
├── sampled_frames/           Not tracked in Git
├── pre_labels/               Not tracked in Git
├── DataSet/                  Initial dataset; not tracked in Git
├── DataSet_new/              Previous incremental dataset; not tracked in Git
└── DataSet_v2/               Final expanded dataset; not tracked in Git
```

## Notes

- Use `best_v3.pt` for final deployment; `last.pt` is not the selected checkpoint.
- Do not run the YOLOv8 checkpoint with the YOLOv5 `detect.py` script.
- If the ROS 2 node appears idle, check that `/camera/image_raw` has an active publisher.
- The dataset, raw videos, generated previews, and training runs are intentionally excluded from Git.

