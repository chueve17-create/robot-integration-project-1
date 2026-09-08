#!/usr/bin/env python3

import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from e3_sorting_interfaces.action import PickAndSort


class PickActionServer(Node):

    def __init__(self):
        super().__init__("e3_pick_action_server")

        self.declare_parameter("action_name", "/e3/pick_and_sort")
        self.declare_parameter("dry_run", True)
        self.declare_parameter("feedback_delay", 0.4)

        self.action_name = self.get_parameter("action_name").value
        self.dry_run = bool(self.get_parameter("dry_run").value)
        self.feedback_delay = float(
            self.get_parameter("feedback_delay").value
        )

        self.valid_grids = set(range(1, 7))
        self.valid_classes = {"comb", "mouse"}

        self.callback_group = ReentrantCallbackGroup()

        self.server = ActionServer(
            self,
            PickAndSort,
            self.action_name,
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.callback_group,
        )

        self.get_logger().info(
            f"Pick-and-sort Action Server: {self.action_name}"
        )
        self.get_logger().info(
            f"Dry-run mode: {self.dry_run}"
        )

    def goal_callback(self, goal_request):
        self.get_logger().info(
            "Goal received: "
            f"grid={goal_request.grid_id}, "
            f"class={goal_request.object_class}, "
            f"model={goal_request.object_model}"
        )

        if goal_request.grid_id not in self.valid_grids:
            self.get_logger().warning(
                f"Rejecting invalid grid: {goal_request.grid_id}"
            )
            return GoalResponse.REJECT

        if goal_request.object_class not in self.valid_classes:
            self.get_logger().warning(
                "Rejecting unsupported class: "
                f"{goal_request.object_class}"
            )
            return GoalResponse.REJECT

        expected_model = f"pick_object_{goal_request.grid_id}"
        if goal_request.object_model != expected_model:
            self.get_logger().warning(
                "Rejecting mismatched model: "
                f"expected={expected_model}, "
                f"received={goal_request.object_model}"
            )
            return GoalResponse.REJECT

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().warning("Cancellation requested")
        return CancelResponse.ACCEPT

    def publish_feedback(
        self,
        goal_handle,
        stage,
        progress,
    ):
        feedback = PickAndSort.Feedback()
        feedback.stage = stage
        feedback.progress = float(progress)
        goal_handle.publish_feedback(feedback)

        self.get_logger().info(
            f"Stage: {stage}, progress={progress:.0%}"
        )

        time.sleep(self.feedback_delay)

    def execute_callback(self, goal_handle):
        request = goal_handle.request

        stages = [
            ("validating_goal", 0.10),
            ("opening_gripper", 0.20),
            ("moving_to_grid", 0.35),
            ("closing_gripper", 0.45),
            ("attaching_object", 0.55),
            ("lifting_object", 0.65),
            ("moving_to_destination", 0.75),
            ("releasing_object", 0.85),
            ("returning_safe", 0.95),
            ("completed", 1.00),
        ]

        for stage, progress in stages:
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()

                result = PickAndSort.Result()
                result.success = False
                result.final_state = "cancelled"
                result.message = "Action cancelled safely"
                return result

            self.publish_feedback(
                goal_handle,
                stage,
                progress,
            )

        goal_handle.succeed()

        result = PickAndSort.Result()
        result.success = True
        result.final_state = "completed"

        if self.dry_run:
            result.message = (
                "Dry-run completed: "
                f"grid={request.grid_id}, "
                f"class={request.object_class}, "
                f"model={request.object_model}"
            )
        else:
            result.message = "Physical simulation completed"

        return result

    def destroy_node(self):
        self.server.destroy()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PickActionServer()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
