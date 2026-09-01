from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("e5_arm_sim")

    xacro_file = os.path.join(
        package_share,
        "urdf",
        "mecharm_270_m5_sim.urdf.xacro",
    )

    world_file = os.path.join(
        package_share,
        "worlds",
        "e5_pick_place.world",
    )

    gazebo_share = get_package_share_directory("gazebo_ros")
    description_share = get_package_share_directory(
        "mycobot_description"
    )

    gazebo_model_path = os.pathsep.join(
        [
            os.path.dirname(description_share),
            os.environ.get("GAZEBO_MODEL_PATH", ""),
        ]
    )

    disable_online_models = SetEnvironmentVariable(
        name="GAZEBO_MODEL_DATABASE_URI",
        value="",
    )

    set_local_model_path = SetEnvironmentVariable(
        name="GAZEBO_MODEL_PATH",
        value=gazebo_model_path,
    )

    robot_description = ParameterValue(
        Command(["xacro ", xacro_file]),
        value_type=str,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": world_file,
            "verbose": "true",
        }.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,
            }
        ],
    )

    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        name="spawn_mecharm",
        output="screen",
        arguments=[
            "-entity",
            "mecharm_270",
            "-topic",
            "robot_description",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.0",
        ],
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_position_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    delayed_controllers = TimerAction(
        period=6.0,
        actions=[
            joint_state_broadcaster,
            arm_controller,
            gripper_controller,
        ],
    )

    return LaunchDescription(
    [
        disable_online_models,
        set_local_model_path,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        delayed_controllers,
      ]
    )
