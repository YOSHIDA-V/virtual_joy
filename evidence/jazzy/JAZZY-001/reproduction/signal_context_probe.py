import time
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
rclpy.init()
node=Node("signal_context_probe", namespace="/virtual_joy_jazzy_context_probe")
print("READY context_ok="+str(rclpy.ok()),flush=True)
try:
    rclpy.spin(node)
except (KeyboardInterrupt, ExternalShutdownException) as error:
    time.sleep(0.05)
    print("spin_exception="+type(error).__name__+" context_ok="+str(rclpy.ok()),flush=True)
try:
    rclpy.shutdown()
except Exception as error:
    print("second_shutdown="+type(error).__name__+": "+str(error),flush=True)
finally:
    node.destroy_node()
    rclpy.try_shutdown()
