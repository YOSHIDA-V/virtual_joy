from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import PushRosNamespace
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

def generate_launch_description():
    original = Path(get_package_share_directory('virtual_joy')) / 'launch' / 'virtual_joy_rover.launch.py'
    return LaunchDescription([GroupAction([
        PushRosNamespace('virtual_joy_jazzy_check'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(original))),
    ])])
