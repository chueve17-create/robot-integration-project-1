# Robot Integration Project 1 — 机器人集成小组项目 I

Course project repository covering a series of robotics integration experiments, built on the following stack:

- **OS**: Ubuntu 22.04 (WSL2 for development, Jetson Orin Nano/NX for deployment)
- **Middleware**: ROS2 Humble
- **Language**: Python 3.10
- **Detection model**: YOLOv8 (Ultralytics)
- **Interfaces**: `sensor_msgs/Image`, `vision_msgs/Detection2DArray`, etc.
- **Coordinate chain**: `world → camera_link → arm_base → end_effector`

## Experiments

### E4 — Custom Object Detection
Two-class (comb, mouse) object detector built from a self-recorded video dataset, trained with YOLOv8n. Status: **training and test evaluation complete** (test mAP50 0.992); Jetson deployment + ROS2 integration is the next phase.

See [`E4_object_detection/README.md`](./E4_object_detection/README.md) for the full data pipeline, annotation workflow, training results, and known limitations.

## Repository structure
```
robot-integration-project-1/
├── E4_object_detection/     E4: custom object detection (see its own README)
├── runs/                    Model evaluation outputs (test set results)
├── .gitignore
└── README.md                This file
```

## Setup notes
- Package installs use Tsinghua/SJTU mirrors for reliability in this network environment.
- Environment and large data artifacts (raw videos, extracted frames, model weights where applicable) follow `.gitignore` rules — see individual experiment READMEs for what's tracked vs. excluded.
