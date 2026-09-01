#!/usr/bin/env python3

import csv
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
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
SAFE_JOINTS = [
    0.502656,
    -0.492589,
    0.130444,
    0.0,
    1.042811,
    0.001002,
]

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
                ("log_root", "~/e5_ws/logs/pick_place"),
                ("joint_sample_period", 0.10),
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
        self.joint_sample_period = float(
            self.get_parameter("joint_sample_period").value
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
        self.joint_state_sub = self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_state_callback,
            50,
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
        self.current_stage = "initialising"
        self.last_sample_time = 0.0
        self.latest_gripper_position = None
        self.start_wall_time = time.time()
        self.stage_results = []

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_root = Path(
            str(self.get_parameter("log_root").value)
        ).expanduser()
        self.run_dir = log_root / stamp
        self.run_dir.mkdir(parents=True, exist_ok=False)

        self.csv_path = self.run_dir / "trajectory.csv"
        self.json_path = self.run_dir / "result.json"
        self.log_path = self.run_dir / "pick_place.log"

        self.csv_file = self.csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        )
        self.csv_writer = csv.writer(
            self.csv_file,
            lineterminator="\\n",
        )
        self.csv_writer.writerow(
            [
                "wall_time_iso",
                "elapsed_s",
                "record_type",
                "stage",
                *JOINT_NAMES,
                "gripper_position",
                "message",
            ]
        )
        self.csv_file.flush()

        self.result = {
            "run_id": stamp,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "duration_s": None,
            "success": False,
            "failed_stage": None,
            "error": None,
            "attachment_joint_name": self.attachment_joint_name,
            "files": {
                "trajectory_csv": str(self.csv_path),
                "text_log": str(self.log_path),
                "result_json": str(self.json_path),
            },
            "parameters": self.parameter_snapshot(),
            "stages": self.stage_results,
        }
        self.log_event("INFO", f"Run directory: {self.run_dir}")

    def parameter_snapshot(self):
        return {
            "arm_controller_topic": self.arm_topic,
            "gripper_controller_topic": self.gripper_topic,
            "arm_motion_duration": self.arm_motion_duration,
            "transfer_duration": self.transfer_duration,
            "gripper_wait_time": self.gripper_wait_time,
            "gripper_open": self.gripper_open,
            "gripper_closed": self.gripper_closed,
            "pick_joints": self.pick_joints,
            "above_pick_joints": self.above_pick_joints,
            "above_place_joints": self.above_place_joints,
            "place_joints": self.place_joints,
            "safe_joints": self.safe_joints,
            "joint_sample_period": self.joint_sample_period,
        }

    def log_event(self, level, message):
        timestamp = datetime.now().isoformat(timespec="milliseconds")
        line = f"{timestamp} [{level}] [{self.current_stage}] {message}"
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")

        if level == "ERROR":
            self.get_logger().error(message)
        elif level == "WARN":
            self.get_logger().warning(message)
        else:
            self.get_logger().info(message)

    def write_csv_row(
        self,
        record_type,
        positions=None,
        message="",
    ):
        values = [""] * len(JOINT_NAMES)
        if positions is not None:
            values = [f"{float(value):.9f}" for value in positions]

        self.csv_writer.writerow(
            [
                datetime.now().isoformat(timespec="milliseconds"),
                f"{time.time() - self.start_wall_time:.3f}",
                record_type,
                self.current_stage,
                *values,
                (
                    ""
                    if self.latest_gripper_position is None
                    else f"{self.latest_gripper_position:.9f}"
                ),
                message,
            ]
        )
        self.csv_file.flush()

    def joint_state_callback(self, msg):
        now = time.monotonic()
        if now - self.last_sample_time < self.joint_sample_period:
            return

        position_by_name = dict(zip(msg.name, msg.position))
        if not all(name in position_by_name for name in JOINT_NAMES):
            return

        positions = [position_by_name[name] for name in JOINT_NAMES]
        if "gripper_controller" in position_by_name:
            self.latest_gripper_position = position_by_name[
                "gripper_controller"
            ]

        self.write_csv_row("joint_state", positions)
        self.last_sample_time = now

    def wait_and_collect(self, duration):
        deadline = time.monotonic() + duration
        while rclpy.ok() and time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            rclpy.spin_once(
                self,
                timeout_sec=min(0.05, max(0.0, remaining)),
            )

    def run_stage(self, name, action):
        self.current_stage = name
        started = time.time()
        self.log_event("INFO", "Stage started")
        stage = {
            "name": name,
            "started_at": datetime.now().isoformat(timespec="milliseconds"),
            "finished_at": None,
            "duration_s": None,
            "success": False,
            "error": None,
        }
        self.stage_results.append(stage)

        try:
            action()
            stage["success"] = True
            self.log_event("INFO", "Stage completed")
        except Exception as exc:
            stage["error"] = str(exc)
            self.log_event("ERROR", f"Stage failed: {exc}")
            raise
        finally:
            stage["finished_at"] = datetime.now().isoformat(
                timespec="milliseconds"
            )
            stage["duration_s"] = round(time.time() - started, 3)
            self.save_result()

    def move_arm(self, positions, duration):
        if len(positions) != len(JOINT_NAMES):
            raise ValueError("Arm target must contain six joint positions")

        msg = JointTrajectory()
        msg.joint_names = JOINT_NAMES

        point = JointTrajectoryPoint()
        point.positions = [float(value) for value in positions]
        seconds = float(duration)
        point.time_from_start.sec = int(seconds)
        point.time_from_start.nanosec = int(
            (seconds - int(seconds)) * 1_000_000_000
        )
        msg.points = [point]

        self.log_event("INFO", f"Moving arm to {positions}")
        self.write_csv_row(
            "arm_command",
            positions,
            f"duration={seconds:.3f}",
        )
        self.arm_pub.publish(msg)
        self.wait_and_collect(seconds + 0.5)

    def move_gripper(self, position, wait_time=2.0):
        msg = Float64MultiArray()
        msg.data = [float(position)]
        self.latest_gripper_position = float(position)

        self.log_event("INFO", f"Moving gripper to {position}")
        self.write_csv_row(
            "gripper_command",
            message=f"target={position}",
        )
        self.gripper_pub.publish(msg)
        self.wait_and_collect(float(wait_time))

    def wait_for_service(self, client, service_name, timeout_sec=15.0):
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            if client.wait_for_service(timeout_sec=1.0):
                return
            self.log_event("INFO", f"Waiting for {service_name}")
        raise RuntimeError(f"Service unavailable: {service_name}")

    def attach_object(self):
        self.wait_for_service(self.attach_client, "/gazebo/attach")

        request = Attach.Request()
        request.joint_name = self.attachment_joint_name
        request.model_name_1 = "mecharm_270"
        request.link_name_1 = "grasp_attach_link"
        request.model_name_2 = "pick_object"
        request.link_name_2 = "object_link"

        self.log_event(
            "INFO",
            f"Calling attach with {self.attachment_joint_name}",
        )
        future = self.attach_client.call_async(request)
        rclpy.spin_until_future_complete(
            self,
            future,
            timeout_sec=10.0,
        )
        if not future.done():
            raise RuntimeError("Attach service timed out")

        response = future.result()
        if response is None or not response.success:
            message = response.message if response else "No response"
            raise RuntimeError(f"Attach failed: {message}")

        self.write_csv_row("service_response", message="attach success")
        self.log_event("INFO", "Object attached")

    def detach_object(self):
        self.wait_for_service(self.detach_client, "/gazebo/detach")

        request = Detach.Request()
        request.joint_name = self.attachment_joint_name
        request.model_name_1 = "mecharm_270"
        request.model_name_2 = "pick_object"

        self.log_event(
            "INFO",
            f"Calling detach with {self.attachment_joint_name}",
        )
        future = self.detach_client.call_async(request)
        rclpy.spin_until_future_complete(
            self,
            future,
            timeout_sec=10.0,
        )
        if not future.done():
            raise RuntimeError("Detach service timed out")

        response = future.result()
        if response is None or not response.success:
            message = response.message if response else "No response"
            raise RuntimeError(f"Detach failed: {message}")

        self.write_csv_row("service_response", message="detach success")
        self.log_event("INFO", "Object detached")

    def execute(self):
        self.wait_and_collect(1.0)

        self.run_stage(
            "open_gripper",
            lambda: self.move_gripper(
                self.gripper_open,
                self.gripper_wait_time,
            ),
        )
        self.run_stage(
            "move_to_pick",
            lambda: self.move_arm(
                self.pick_joints,
                self.arm_motion_duration,
            ),
        )
        self.run_stage(
            "close_gripper",
            lambda: self.move_gripper(
                self.gripper_closed,
                self.gripper_wait_time,
            ),
        )
        self.run_stage("attach_object", self.attach_object)
        self.run_stage(
            "lift_object",
            lambda: self.move_arm(
                self.above_pick_joints,
                self.arm_motion_duration,
            ),
        )
        self.run_stage(
            "transfer_object",
            lambda: self.move_arm(
                self.above_place_joints,
                self.transfer_duration,
            ),
        )
        self.run_stage(
            "lower_to_place",
            lambda: self.move_arm(
                self.place_joints,
                self.arm_motion_duration,
            ),
        )
        self.run_stage("detach_object", self.detach_object)
        self.run_stage(
            "release_object",
            lambda: self.move_gripper(
                self.gripper_open,
                self.gripper_wait_time,
            ),
        )
        self.run_stage(
            "retreat_from_place",
            lambda: self.move_arm(
                self.above_place_joints,
                self.arm_motion_duration,
            ),
        )
        self.run_stage(
            "return_to_safe",
            lambda: self.move_arm(
                self.safe_joints,
                self.transfer_duration,
            ),
        )

        self.result["success"] = True
        self.current_stage = "completed"
        self.log_event("INFO", "Pick-and-place completed")

    def save_result(self):
        self.json_path.write_text(
            json.dumps(self.result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def finish_result(self, error=None):
        self.result["finished_at"] = datetime.now().isoformat(
            timespec="seconds"
        )
        self.result["duration_s"] = round(
            time.time() - self.start_wall_time,
            3,
        )
        if error is not None:
            self.result["success"] = False
            self.result["failed_stage"] = self.current_stage
            self.result["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": "".join(
                    traceback.format_exception(
                        type(error),
                        error,
                        error.__traceback__,
                    )
                ),
            }
            self.log_event("ERROR", str(error))
        self.save_result()

    def close_files(self):
        if not self.csv_file.closed:
            self.csv_file.flush()
            self.csv_file.close()


def main(args=None):
    rclpy.init(args=args)
    node = None
    error = None

    try:
        node = PickPlaceNode()
        node.execute()
    except Exception as exc:
        error = exc
    finally:
        if node is not None:
            node.finish_result(error)
            node.close_files()
            node.get_logger().info(
                f"Results saved in: {node.run_dir}"
            )
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if error is not None:
        raise error


if __name__ == "__main__":
    main()
