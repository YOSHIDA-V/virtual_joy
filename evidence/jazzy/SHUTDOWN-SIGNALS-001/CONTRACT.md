# SHUTDOWN-SIGNALS-001

Observed: terminal process-group SIGINT followed by ROS launch's signal forwarding interrupts node destruction and produces abnormal child exit codes. The default group relationship is a hypothesis until measured.
Preserved failures: NONHARDWARE-20261006, virtual_joy and Gazebo; SHUTDOWN-WALL-001/slam-fixed. Full PID/runtime/config identity is already pushed.
Target: same Ubuntu 24.04/Jazzy/domain100/VNC:1, same controller/model/kinematics and baseline operating values.
Proof before edit: record real process group/session for every owned child and compare default launch to the same artifact with the existing launch-prefix=setsid configuration. The only diagnostic variable is signal-group isolation.
Allowed: application launch descriptions for process isolation and their dependency declarations. Python node algorithms, vendor submodule, physical model, operating parameters, tests' pass thresholds and global ROS installations are forbidden changes for this issue.
Controlled criteria: child group differs from launch parent; same Joy/Twist rates and idle values or Gazebo forward/stop observations; original termination procedure emits no newly isolated child cleanup exceptions. Remaining independent failures stay recorded.
Target criteria: immutable installed launcher bytes, same repeated README workflows, no regression of the original functional criteria. Full qualification still requires fixing any separate root causes.
State: OBSERVED; A/B proof follows before production edits.
