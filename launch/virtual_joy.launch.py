#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='joy',
        description='Joy topic name'
    )

    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate_hz',
        default_value='20.0',
        description='Publish rate [Hz]'
    )

    node = Node(
        package='virtual_joy',
        executable='virtual_joy_node',
        name='virtual_joy',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'topic_name': LaunchConfiguration('topic_name'),
            'publish_rate_hz': LaunchConfiguration('publish_rate_hz'),
        }],
    )

    return LaunchDescription([
        topic_name_arg,
        publish_rate_arg,
        node,
    ])