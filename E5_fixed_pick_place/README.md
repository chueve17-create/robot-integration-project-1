# E5 — Fixed-Point Pick-and-Place Simulation

This directory contains the E5 simulation task for **Robot Integration Group Project I**. It demonstrates a mechArm 270 M5 performing an automatic fixed-point pick-and-place sequence using ROS 2 Humble, Gazebo Classic, `ros2_control`, and the Gazebo model attachment plugin.

The task uses predefined joint-space configurations rather than visual localisation. The robot opens the gripper, approaches pick point A, grasps the object, transfers it above place point B, releases it, retreats, and returns to a safe pose.

## Current status

The following functions have been implemented and verified:

- mechArm 270 M5 model with an adaptive gripper
- Gazebo world containing a table, red pick object, and green place region
- local robot mesh loading without the Gazebo online model database
- `gazebo_ros2_control` integration
- six-joint trajectory control and gripper position control
- calibrated gripper collision geometry and contact parameters
- automatic attach and detach of the grasped object
- complete automatic pick-and-place sequence
- final return to a safe joint configuration
- actual `/joint_states` trajectory sampling
- CSV trajectory output, JSON execution summary, and text error/event log
- successful repeated execution using unique attachment-joint names

## Repository structure

```text
E5_fixed_pick_place/
├── E5_机械臂抓取实验参数手册.docx
├── README.md
├── simulation.mp4
├── results/
│   └── example_success/
│       ├── pick_place.log
│       ├── result.json
│       └── trajectory.csv
└── ros2_ws/
    └── src/
        ├── e5_arm_sim/
        │   ├── config/controllers.yaml
        │   ├── launch/e5_sim.launch.py
        │   ├── urdf/mecharm_270_m5_sim.urdf.xacro
        │   └── worlds/e5_pick_place.world
        └── e5_pick_place/
            ├── config/pick_place.yaml
            ├── e5_pick_place/pick_place_node.py
            ├── launch/pick_place.launch.py
            ├── package.xml
            └── setup.py
```

## System requirements

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- `gazebo_ros2_control`
- `ros2_control` controllers
- Gazebo model attachment plugin

The project was developed and tested under Ubuntu 22.04 on WSL 2.

## External robot model dependency

The Elephant Robotics ROS 2 repository supplies the original mechArm 270 meshes and description resources. It is intentionally not copied into this repository.

```bash
mkdir -p ~/e5_ws/src
cd ~/e5_ws/src

git clone -b humble --depth 1 \
  https://github.com/elephantrobotics/mycobot_ros2.git
```

Link both E5 packages into the workspace:

```bash
ln -s \
  ~/robot-integration-project-1/E5_fixed_pick_place/ros2_ws/src/e5_arm_sim \
  ~/e5_ws/src/e5_arm_sim

ln -s \
  ~/robot-integration-project-1/E5_fixed_pick_place/ros2_ws/src/e5_pick_place \
  ~/e5_ws/src/e5_pick_place
```

## Dependency installation

```bash
sudo apt update
sudo apt install -y \
  gazebo \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-robot-state-publisher \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-xacro \
  ros-humble-gazebo-model-attachment-plugin \
  ros-humble-gazebo-model-attachment-plugin-msgs \
  python3-colcon-common-extensions \
  python3-rosdep
```

Install resolvable ROS package dependencies:

```bash
cd ~/e5_ws
source /opt/ros/humble/setup.bash

rosdep install \
  --from-paths src \
  --ignore-src \
  -r -y \
  --skip-keys="python-tk warehouse_ros_mongo"
```

## Build

```bash
cd ~/e5_ws
source /opt/ros/humble/setup.bash

colcon build \
  --symlink-install \
  --packages-select e5_arm_sim e5_pick_place

source ~/e5_ws/install/setup.bash
```

## Run the simulation

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/e5_ws/install/setup.bash

export GAZEBO_MODEL_DATABASE_URI=""

ros2 launch e5_arm_sim e5_sim.launch.py
```

If Gazebo opens without a GUI, keep `gzserver` running and start the client in another terminal:

```bash
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source ~/e5_ws/install/setup.bash

export GAZEBO_MODEL_DATABASE_URI=""
gzclient --verbose
```

## Run the automatic task

Terminal 2:

```bash
source ~/e5_ws/install/setup.bash
ros2 launch e5_pick_place pick_place.launch.py
```

The automatic sequence is:

1. open the gripper;
2. move to `pick_joints`;
3. close the gripper;
4. attach `pick_object` to `grasp_attach_link`;
5. lift to `above_pick_joints`;
6. transfer to `above_place_joints`;
7. lower to `place_joints`;
8. detach and release the object;
9. retreat to `above_place_joints`;
10. return to `safe_joints`.

## Task parameters

The runtime parameters are stored in:

```text
ros2_ws/src/e5_pick_place/config/pick_place.yaml
```

### Scene configuration

| Item | Final configuration |
| --- | --- |
| Table top height | 0.40 m |
| Pick object pose | `[0.14, 0.08, 0.425, 0, 0, 0]` |
| Place region pose | `[0.14, -0.08, 0.402, 0, 0, 0]` |
| Object size | `0.025 × 0.025 × 0.050 m` |
| Object mass | `0.05 kg` |

### Joint configurations

Joint order:

```text
joint1_to_base, joint2_to_joint1, joint3_to_joint2,
joint4_to_joint3, joint5_to_joint4, joint6_to_joint5
```

| Configuration | Joint positions in radians |
| --- | --- |
| `pick_joints` | `[0.5017, 0.660, -0.330, 0.0, 1.241, 0.500]` |
| `above_pick_joints` | `[0.5017, 0.660, -0.530, 0.0, 1.441, 0.500]` |
| `above_place_joints` | `[-0.5017, 0.660, -0.530, 0.0, 1.441, 0.500]` |
| `place_joints` | `[-0.5017, 0.660, -0.380, 0.0, 1.291, 0.500]` |
| `safe_joints` | `[0.502656, -0.492589, 0.130444, 0.0, 1.042811, 0.001002]` |

`above_pick_joints` and `above_place_joints` are complete joint-space configurations at safe travel height. They are not Cartesian Z values. `safe_joints` is the final parking pose after the task.

### Motion and gripper parameters

| Parameter | Value |
| --- | ---: |
| Arm motion duration | 6.0 s |
| Transfer duration | 8.0 s |
| Gripper wait time | 2.0 s |
| Gripper open position | 0.15 |
| Gripper closed position | -0.35 |
| Joint-state sample period | 0.10 s |

## Grasp attachment

The attachment plugin creates a temporary fixed joint between:

```text
mecharm_270 / grasp_attach_link
pick_object / object_link
```

`grasp_attach_link` is calibrated for the final closed-gripper pose. Attaching directly to `link6` causes the object to jump into the robot because the link origins do not match the grasp pose.

Every run uses a unique joint name:

```text
pick_object_grasp_joint_<time_ns>
```

This prevents repeated runs from blocking on an attachment joint left from an earlier execution.

## Controllers and services

Expected active controllers:

```text
joint_state_broadcaster       active
arm_controller                active
gripper_position_controller   active
```

Required Gazebo services:

```text
/gazebo/attach
/gazebo/detach
/gazebo/get_entity_state
/gazebo/set_entity_state
```

Verify them with:

```bash
ros2 control list_controllers
ros2 service list | grep -E '/gazebo/(attach|detach|get_entity_state|set_entity_state)'
```

## Execution records

Each run creates a timestamped directory under:

```text
~/e5_ws/logs/pick_place/YYYYMMDD_HHMMSS/
```

Three files are generated:

| File | Contents |
| --- | --- |
| `trajectory.csv` | Timestamped arm commands, gripper commands, service responses, and sampled `/joint_states`. |
| `result.json` | Parameters, stage timings, overall success, failed stage, and exception traceback. |
| `pick_place.log` | Human-readable stage, motion, attachment, completion, and error messages. |

Inspect the latest run:

```bash
latest=$(find ~/e5_ws/logs/pick_place \
  -mindepth 1 -maxdepth 1 -type d | sort | tail -1)

cat "$latest/result.json"
head "$latest/trajectory.csv"
cat "$latest/pick_place.log"
```

A validated successful run is included in `results/example_success/`. Its recorded duration was **50.034 seconds**, and all 11 execution stages completed successfully.

## Tests

```bash
cd ~/e5_ws

colcon test \
  --packages-select e5_pick_place \
  --event-handlers console_direct+

colcon test-result --verbose
```

Validated test result:

```text
3 tests, 0 errors, 0 failures, 1 skipped
```

The skipped copyright test and the `SelectableGroups` deprecation warnings do not affect runtime behaviour.

## Demonstration evidence

- `simulation.mp4`: successful automatic pick-and-place demonstration
- `results/example_success/result.json`: machine-readable successful execution summary
- `results/example_success/trajectory.csv`: recorded commanded and actual joint trajectory data
- `results/example_success/pick_place.log`: readable execution log
- `E5_机械臂抓取实验参数手册.docx`: consolidated experiment parameters for report writing

## Notes

- Generated workspace directories such as `build/`, `install/`, and `log/` must not be committed.
- Python caches, `*.pyc`, and temporary `*.bak` files must not be committed.
- The upstream `mycobot_ros2` repository must not be vendored into this repository.
- Current inertial and contact parameters are simulation approximations, not manufacturer-certified physical parameters.
- Gazebo Classic is used for compatibility with ROS 2 Humble and the available robot resources.
