#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from gazebo_model_attachment_plugin_msgs.srv import Attach, Detach


JOINT_NAMES = [
    "joint1_to_base",
    "joint2_to_joint1",
    "joint3_to_joint2",
    "joint4_to_joint3",
    "joint5_to_joint4",
    "joint6_to_joint5",
]

PICK_JOINTS = [0.5017, 0.660, -0.330, 0.0, 1.241, 0.50]
LIFT_JOINTS = [0.5017, 0.660, -0.530, 0.0, 1.441, 0.50]
ABOVE_PLACE_JOINTS = [-0.5017, 0.660, -0.530, 0.0, 1.441, 0.50]
PLACE_JOINTS = [-0.5017, 0.660, -0.380, 0.0, 1.291, 0.50]
SAFE_JOINTS = [0.502656, -0.492589, 0.130444, 0.0, 1.042811, 0.001002]

GRIPPER_OPEN = 0.15
GRIPPER_CLOSED = -0.35


class PickPlaceNode(Node):

    def __init__(self):
        super().__init__("pick_place_node")

        self.declare_parameters(
            namespace="",
            parameters=[
                ("arm_controller_topic", "/arm_controller/joint_trajectory"),
                (
                    "gripper_controller_topic",
                    "/gripper_position_controller/commands",
                ),
                ("arm_motion_duration", 6.0),
                ("transfer_duration", 8.0),
                ("gripper_wait_time", 2.0),
                ("gripper_open", GRIPPER_OPEN),
                ("gripper_closed", GRIPPER_CLOSED),
                ("pick_joints", PICK_JOINTS),
                ("above_pick_joints", LIFT_JOINTS),
                ("above_place_joints", ABOVE_PLACE_JOINTS),
                ("place_joints", PLACE_JOINTS),
                ("safe_joints", SAFE_JOINTS),
            ],
        )

        self.arm_topic = self.get_parameter(
            "arm_controller_topic"
        ).value
        self.gripper_topic = self.get_parameter(
            "gripper_controller_topic"
        ).value

        self.arm_motion_duration = float(
            self.get_parameter("arm_motion_duration").value
        )
        self.transfer_duration = float(
            self.get_parameter("transfer_duration").value
        )
        self.gripper_wait_time = float(
            self.get_parameter("gripper_wait_time").value
        )

        self.gripper_open = float(
            self.get_parameter("gripper_open").value
        )
        self.gripper_closed = float(
            self.get_parameter("gripper_closed").value
        )

        self.pick_joints = list(
            self.get_parameter("pick_joints").value
        )
        self.above_pick_joints = list(
            self.get_parameter("above_pick_joints").value
        )
        self.above_place_joints = list(
            self.get_parameter("above_place_joints").value
        )
        self.place_joints = list(
            self.get_parameter("place_joints").value
        )
        self.safe_joints = list(
            self.get_parameter("safe_joints").value
        )

        self.arm_pub = self.create_publisher(
            JointTrajectory,
            self.arm_topic,
            10,
        )
        self.gripper_pub = self.create_publisher(
            Float64MultiArray,
            self.gripper_topic,
            10,
        )

        self.attach_client = self.create_client(
            Attach,
            "/gazebo/attach",
        )
        self.detach_client = self.create_client(
            Detach,
            "/gazebo/detach",
        )

        self.attachment_joint_name = (
            f"pick_object_grasp_joint_{time.time_ns()}"
        )

    def move_arm(self, positions, duration):
        msg = JointTrajectory()
        msg.joint_names = JOINT_NAMES

        point = JointTrajectoryPoint()
        point.positions = [float(value) for value in positions]
        point.time_from_start.sec = int(duration)

        msg.points = [point]

        self.get_logger().info(f"Moving arm to {positions}")
        self.arm_pub.publish(msg)
        time.sleep(duration + 0.5)

    def move_gripper(self, position, wait_time=2.0):
        msg = Float64MultiArray()
        msg.data = [float(position)]

        self.get_logger().info(f"Moving gripper to {position}")
        self.gripper_pub.publish(msg)
        time.sleep(wait_time)

    def attach_object(self):
        while not self.attach_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /gazebo/attach")

        request = Attach.Request()
        request.joint_name = self.attachment_joint_name
        request.model_name_1 = "mecharm_270"
        request.link_name_1 = "grasp_attach_link"
        request.model_name_2 = "pick_object"
        request.link_name_2 = "object_link"

        self.get_logger().info(
            f"Calling attach with {self.attachment_joint_name}"
        )
        future = self.attach_client.call_async(request)
        rclpy.spin_until_future_complete(
            self, future, timeout_sec=10.0
        )
        if not future.done():
            raise RuntimeError("Attach service timed out")

        response = future.result()
        if response is None or not response.success:
            message = response.message if response else "No response"
            raise RuntimeError(f"Attach failed: {message}")

        self.get_logger().info("Object attached")

    def detach_object(self):
        while not self.detach_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for /gazebo/detach")

        request = Detach.Request()
        request.joint_name = self.attachment_joint_name
        request.model_name_1 = "mecharm_270"
        request.model_name_2 = "pick_object"

        self.get_logger().info(
            f"Calling detach with {self.attachment_joint_name}"
        )
        future = self.detach_client.call_async(request)
        rclpy.spin_until_future_complete(
            self, future, timeout_sec=10.0
        )
        if not future.done():
            raise RuntimeError("Detach service timed out")

        response = future.result()
        if response is None or not response.success:
            message = response.message if response else "No response"
            raise RuntimeError(f"Detach failed: {message}")

        self.get_logger().info("Object detached")

    def execute(self):
        time.sleep(1.0)

        self.move_gripper(
            self.gripper_open,
            self.gripper_wait_time,
        )
        self.move_arm(
            self.pick_joints,
            self.arm_motion_duration,
        )

        self.move_gripper(
            self.gripper_closed,
            self.gripper_wait_time,
        )
        self.attach_object()

        self.move_arm(
            self.above_pick_joints,
            self.arm_motion_duration,
        )
        self.move_arm(
            self.above_place_joints,
            self.transfer_duration,
        )
        self.move_arm(
            self.place_joints,
            self.arm_motion_duration,
        )

        self.detach_object()
        self.move_gripper(
            self.gripper_open,
            self.gripper_wait_time,
        )

        self.move_arm(
            self.above_place_joints,
            self.arm_motion_duration,
        )
        self.move_arm(
            self.safe_joints,
            self.transfer_duration,
        )
        self.get_logger().info("Pick-and-place completed")


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()

    try:
        node.execute()
    except Exception as exc:
        node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
