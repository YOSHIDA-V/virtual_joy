# SHUTDOWN-SIGNALS-001: terminal and launch both deliver SIGINT

Target: Ubuntu-24.04-50GB, ROS 2 Jazzy, ROS_DOMAIN_ID=100, VNC :1.
Source artifact: megarover3_ros2 11c402d5657cf127478912207d1a289ed7380b1a,
virtual_joy 7f68f7f5dadc7e20f3d83e2ae283c68cd982c159; both clean.

`joy-ab/default-joy` reproduces KeyboardInterrupt during destroy_node in both
nodes. Both children share the launch parent's process group. The terminal
group SIGINT reaches them directly, and launch forwards SIGINT again.
`joy-ab/isolated-joy` changes only `launch-prefix:=setsid`: each child has its
own session/process group. The same topic/rate/neutral-command checks pass,
both children exit cleanly, and no exceptions, escalation, or residuals occur.
Raw runtime logs and numeric process identities are retained in this directory.

Scope: isolate virtual_joy's two ROS nodes from the foreground launch group.
Do not blanket-catch exceptions or change Joy/Twist algorithms or rates.

Gazebo A/B is diagnostic only. Isolated ROS static TF exits cleanly, but the
vendor relay still throws on a single shutdown, and the shell wrapping Gazebo
does not forward to its isolated Ruby child. Those are separate issues.
No claim that a global launch-prefix fixes Gazebo or navigation.

Original qualification criteria remain unchanged. Repeat the ordinary
virtual_joy launch without command-line prefix overrides after the fix.
