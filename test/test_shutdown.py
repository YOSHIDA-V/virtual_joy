"""Exercise the shutdown/publish race with real Jazzy contexts and publishers.

spin is replaced only to force the timing of the race; no input events or
physical command topics are used. A virtual display is needed for the GUI tests.
"""
import threading
import tkinter as tk
import unittest
from unittest.mock import patch

import rclpy
from rclpy.impl.implementation_singleton import rclpy_implementation as _rclpy

from virtual_joy import rover_gamepad_node as rover
from virtual_joy import virtual_joy_node as gui


def publish_after_context_shutdown(node):
    node.context.shutdown()
    if isinstance(node, gui.VirtualJoyNode):
        node._on_timer()
    else:
        node._timer_callback()


def live_context_error(node):
    if not node.context.ok():
        raise AssertionError('the fault must be injected into a live context')
    raise _rclpy.RCLError('test live-context publisher error')


class ShutdownRaceTest(unittest.TestCase):
    def tearDown(self):
        rclpy.try_shutdown()

    def test_rover_ignores_publish_failure_only_after_context_shutdown(self):
        with patch.object(rover.rclpy, 'spin', side_effect=publish_after_context_shutdown):
            rover.main(args=['--ros-args', '-r', '__ns:=/virtual_joy_jazzy_shutdown_check'])

    def test_rover_preserves_live_context_publish_failure(self):
        with patch.object(rover.rclpy, 'spin', side_effect=live_context_error):
            with self.assertRaisesRegex(_rclpy.RCLError, 'live-context'):
                rover.main(args=['--ros-args', '-r', '__ns:=/virtual_joy_jazzy_shutdown_check'])

    def run_gui(self, spin):
        errors = []
        roots = []
        original_tk = tk.Tk

        def create_root():
            root = original_tk()
            roots.append(root)
            # Call the application's close callback. No mouse/keyboard event.
            root.after(500, lambda: root.tk.call(root.protocol('WM_DELETE_WINDOW')))
            return root

        with patch.object(gui.rclpy, 'spin', side_effect=spin), \
                patch.object(gui.tk, 'Tk', side_effect=create_root), \
                patch.object(threading, 'excepthook', side_effect=lambda args: errors.append(args.exc_value)):
            try:
                gui.main(args=['--ros-args', '-r', '__ns:=/virtual_joy_jazzy_shutdown_check'])
            finally:
                # A second Tk instance in the same test process must not run
                # callbacks left in the first instance's Tcl interpreter.
                for root in roots:
                    for job in root.tk.call('after', 'info'):
                        root.tk.call('after', 'cancel', job)
        return errors

    def test_gui_ignores_publish_failure_only_after_context_shutdown(self):
        self.assertEqual(self.run_gui(publish_after_context_shutdown), [])

    def test_gui_preserves_live_context_publish_failure(self):
        errors = self.run_gui(live_context_error)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], _rclpy.RCLError)
        self.assertIn('live-context', str(errors[0]))


if __name__ == '__main__':
    unittest.main()
