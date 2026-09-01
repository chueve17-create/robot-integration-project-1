from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(
        get_package_share_directory("e5_pick_place")
    )
    config_file = package_share / "config" / "pick_place.yaml"

    return LaunchDescription(
        [
            Node(
                package="e5_pick_place",
                executable="pick_place_node",
                name="pick_place_node",
                output="screen",
                parameters=[str(config_file)],
            )
        ]
    )
