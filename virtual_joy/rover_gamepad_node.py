#!/usr/bin/env python3

import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy


class RoverGamepadNode(Node):
    def __init__(self):
        super().__init__('rover_gamepad')

        self.declare_parameter('publish_rate', 100.0)
        self.declare_parameter('joy_topic', 'joy')
        self.declare_parameter('twist_topic', 'rover_twist')
        self.declare_parameter('joy_timeout_sec', 1.0)

        publish_rate = float(self.get_parameter('publish_rate').value)
        publish_rate = max(1.0, publish_rate)
        joy_topic = str(self.get_parameter('joy_topic').value)
        twist_topic = str(self.get_parameter('twist_topic').value)
        self._joy_timeout_sec = float(self.get_parameter('joy_timeout_sec').value)

        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.VOLATILE

        self._mutex = threading.Lock()
        self._current_cmd = Twist()
        self._last_time = self.get_clock().now()

        self._joy_sub = self.create_subscription(
            Joy,
            joy_topic,
            self._joy_callback,
            qos,
        )

        self._twist_pub = self.create_publisher(Twist, twist_topic, qos)

        period_sec = 1.0 / publish_rate
        self._timer = self.create_timer(period_sec, self._timer_callback)

        self.get_logger().info(
            f'rover_gamepad started joy_topic={joy_topic} twist_topic={twist_topic} rate={publish_rate:.1f}Hz'
        )

    @staticmethod
    def _get_axis(msg: Joy, index: int) -> float:
        return msg.axes[index] if index < len(msg.axes) else 0.0

    @staticmethod
    def _get_button(msg: Joy, index: int) -> int:
        return msg.buttons[index] if index < len(msg.buttons) else 0

    def _joy_callback(self, msg: Joy):
        with self._mutex:
            self._last_time = self.get_clock().now()
            cmd = Twist()

            axis_left_x = 0
            axis_left_y = 1
            axis_right_x = 3
            axis_right_y = 4
            axis_dpad_x = 6
            axis_dpad_y = 7

            btn_triangle = 2
            btn_circle = 1
            btn_cross = 0
            btn_square = 3
            btn_l1 = 4
            btn_r1 = 5
            btn_l2 = 6
            btn_r2 = 7

            xs_micro = 0.1
            xs_slow = 0.3
            zs_micro = 0.3

            stick_enabled = (
                self._get_button(msg, btn_l1)
                or self._get_button(msg, btn_r1)
                or self._get_button(msg, btn_l2)
                or self._get_button(msg, btn_r2)
            )

            if self._get_button(msg, btn_r1):
                stick_linear_speed = 0.5
                stick_angular_speed = 1.04
            else:
                stick_linear_speed = 1.0
                stick_angular_speed = 1.0
            if self._get_button(msg, btn_l1):
                stick_linear_speed = 0.8
                stick_angular_speed = 1.57
            if self._get_button(msg, btn_r2):
                stick_linear_speed = 1.0
                stick_angular_speed = 2.10
            if self._get_button(msg, btn_l2):
                stick_linear_speed = 1.5
                stick_angular_speed = 2.5

            if self._get_button(msg, btn_triangle):
                cmd.linear.x += xs_micro
            if self._get_button(msg, btn_cross):
                cmd.linear.x -= xs_micro
            if self._get_button(msg, btn_square):
                cmd.angular.z += zs_micro
            if self._get_button(msg, btn_circle):
                cmd.angular.z -= zs_micro

            dpad_y = self._get_axis(msg, axis_dpad_y)
            dpad_x = self._get_axis(msg, axis_dpad_x)
            if dpad_y > 0.5:
                cmd.linear.x += xs_slow
            if dpad_y < -0.5:
                cmd.linear.x -= xs_slow
            if dpad_x < -0.5:
                cmd.linear.y += zs_micro
            if dpad_x > 0.5:
                cmd.linear.y -= zs_micro

            if stick_enabled:
                lx = self._get_axis(msg, axis_left_x)
                ly = self._get_axis(msg, axis_left_y)
                rx = self._get_axis(msg, axis_right_x)
                ry = self._get_axis(msg, axis_right_y)

                left_forward = ly * stick_linear_speed
                left_strafe = -lx * stick_angular_speed
                right_forward = ry * stick_linear_speed
                right_rotate = -rx * stick_angular_speed

                cmd.linear.x += left_forward + right_forward
                cmd.linear.y += left_strafe
                cmd.angular.z += right_rotate

            self._current_cmd = cmd

    def _timer_callback(self):
        with self._mutex:
            now = self.get_clock().now()
            if (now - self._last_time).nanoseconds / 1e9 > self._joy_timeout_sec:
                self._current_cmd.linear.x = 0.0
                self._current_cmd.angular.z = 0.0

            self._twist_pub.publish(self._current_cmd)


def main(args=None):
    rclpy.init(args=args)
    node = RoverGamepadNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
