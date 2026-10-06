# SHUTDOWN-GUI-CLOSE-001

Observed/reproduced: closing the Tk client removes the GUI, but ros2 launch
and rover_gamepad stay alive after three seconds. Raw records in
window-close-03 came from the same domain100/Jazzy/VNC environment.
Cause in source: the launch description has no process-exit relationship
between the GUI and the companion converter.

One change: launch shutdown when the GUI exits, guarded during an existing
shutdown. Criteria: GUI WM_DELETE, GUI and converter and launch exit cleanly
within 10 seconds, no exceptions/escalation/residuals. Topic/rate/neutral
checks and repeated terminal-group Ctrl+C still pass. No algorithm changes.
The WM_DELETE test does not inject mouse or keyboard input.
