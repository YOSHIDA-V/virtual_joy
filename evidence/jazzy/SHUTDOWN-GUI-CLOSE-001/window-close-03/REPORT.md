# GUI close succeeds; converter SIGINT shutdown still fails

Test commit `4b0e544` selects the observed Tk client, excluding its GNOME frame. No matching application existed before launch. The client did not expose `_NET_WM_PID`; the test records this limitation and the before/after process inventories. WM_DELETE_WINDOW was sent only to this newly created client. No pointer, keyboard or focus event was synthesized.

The GUI process finishes cleanly, and its X11 window disappears. After three seconds the ROS launch parent and `rover_gamepad_node` remain. The observed last Twist has linear.x=0, linear.y=0 and angular.z=0. This was an idle-controller close test; it does not verify closing while a user is commanding motion.

The subsequent owned process-group SIGINT interrupts `node.destroy_node()` in the converter: runtime.log contains KeyboardInterrupt and child exit -2. Parent exit 0 does not override this failure. Combined result is FAIL, and the test wrapper exits 1. No marked processes remain after completion.

No application source was changed. Previous lookup failures are retained in window-close and window-close-02. Screenshots and full X11 inventories remain local.
