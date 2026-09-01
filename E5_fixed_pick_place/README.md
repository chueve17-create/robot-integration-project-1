# E5 — Fixed-Point Pick-and-Place Simulation

This directory contains the simulation work for E5 of **Robot Integration Group Project I**. The goal is to simulate a mechArm 270 M5 performing a fixed-point pick-and-place task using ROS 2 Humble, Gazebo Classic, and `ros2_control`.

The experiment does not use visual localization. The pick position (A), place position (B), and safe travel height are predefined parameters.

## Current status

The following components are currently working:

- mechArm 270 M5 model with adaptive gripper
- Gazebo experiment world with a table, pick object, and place region
- local mesh loading without dependence on the Gazebo online model database
- `gazebo_ros2_control` integration
- six-joint trajectory controller
- gripper position controller
- joint-state publication
- single ROS 2 launch file for the simulation stack

The automatic pick-and-place state machine, reachability checks, result logger, and repeated-trial evaluation are the next development milestones.

## Repository structure

```text
E5_fixed_pick_place/
└── ros2_ws/
    └── src/
        └── e5_arm_sim/
            ├── CMakeLists.txt
            ├── package.xml
            ├── config/
            │   └── controllers.yaml
            ├── launch/
            │   └── e5_sim.launch.py
            ├── models/
            ├── urdf/
            │   └── mecharm_270_m5_sim.urdf.xacro
            └── worlds/
                └── e5_pick_place.world
```

## System requirements

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- MoveIt 2
- `gazebo_ros2_control`
- `ros2_control` controllers

The project has been developed and tested under Ubuntu 22.04 on WSL 2.

## External robot model dependency

The Elephant Robotics ROS 2 repository is used for the original mechArm 270 meshes and robot-description resources. It is intentionally not copied into this repository.

Create a ROS 2 workspace and clone the Humble branch:

```bash
mkdir -p ~/e5_ws/src
cd ~/e5_ws/src

git clone -b humble --depth 1 \
  https://github.com/elephantrobotics/mycobot_ros2.git
```

Link or copy this repository's simulation package into the workspace:

```bash
ln -s \
  ~/robot-integration-project-1/E5_fixed_pick_place/ros2_ws/src/e5_arm_sim \
  ~/e5_ws/src/e5_arm_sim
```

## Dependency installation

```bash
sudo apt update
sudo apt install -y \
  gazebo \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-moveit \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-tk
```

Install resolvable package dependencies:

```bash
cd ~/e5_ws
source /opt/ros/humble/setup.bash

rosdep install \
  --from-paths src \
  --ignore-src \
  -r -y \
  --skip-keys="python-tk warehouse_ros_mongo"
```

`python-tk` is an obsolete Python 2 dependency name in some upstream packages. `warehouse_ros_mongo` is an optional MoveIt warehouse dependency and is not required for this simulation.

## Build

```bash
cd ~/e5_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source ~/e5_ws/install/setup.bash
```

To rebuild only the E5 simulation package:

```bash
colcon build --symlink-install --packages-select e5_arm_sim
source ~/e5_ws/install/setup.bash
```

## Run the simulation

```bash
ros2 launch e5_arm_sim e5_sim.launch.py
```

The launch file starts:

- Gazebo Classic and the E5 experiment world
- `robot_state_publisher`
- the mechArm 270 M5 model
- `joint_state_broadcaster`
- `arm_controller`
- `gripper_position_controller`

## Verify the controllers

In a second terminal:

```bash
source ~/e5_ws/install/setup.bash
ros2 control list_controllers
```

Expected controller state:

```text
joint_state_broadcaster       active
arm_controller                active
gripper_position_controller   active
```

## Basic motion test

Send a slow six-joint trajectory:

```bash
ros2 topic pub --once \
  /arm_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  "{joint_names: ['joint1_to_base', 'joint2_to_joint1', 'joint3_to_joint2', 'joint4_to_joint3', 'joint5_to_joint4', 'joint6_to_joint5'], points: [{positions: [0.0, -0.4, 0.7, 0.0, 0.3, 0.0], time_from_start: {sec: 3, nanosec: 0}}]}"
```

Test the gripper:

```bash
ros2 topic pub --once \
  /gripper_position_controller/commands \
  std_msgs/msg/Float64MultiArray \
  "{data: [-0.5]}"
```

Read the current simulated joint state:

```bash
ros2 topic echo /joint_states --once
```

## Initial scene parameters

| Item | Initial configuration |
| --- | --- |
| Table top height | 0.40 m |
| Robot base height | 0.42 m |
| Pick point A | x = 0.18 m, y = 0.10 m |
| Place point B | x = 0.18 m, y = -0.10 m |
| Object mass | 0.05 kg |

These values are initial simulation parameters and may be refined after reachability and collision testing.

## Planned work

- add named home, pick, place, and safe-height configurations
- implement the automatic pick-and-place state machine
- integrate MoveIt 2 planning and inverse kinematics
- reject unreachable or joint-limit-violating targets
- stop safely after planning, controller, or communication failures
- save trajectories, execution results, and error logs
- run five consecutive trials and achieve at least four successes
- record normal-operation and abnormal-target demonstration videos
- reuse the same task interface for the physical mechArm 270

## Notes

- Generated directories such as `build/`, `install/`, and `log/` must not be committed.
- The upstream `mycobot_ros2` repository must not be vendored into this repository.
- The current inertial values are simulation approximations and should not be treated as manufacturer-certified physical parameters.
- Gazebo Classic is used for compatibility with ROS 2 Humble and the available robot resources.
