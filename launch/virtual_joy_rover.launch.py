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

    joy_publish_rate_arg = DeclareLaunchArgument(
        'joy_publish_rate_hz',
        default_value='20.0',
        description='virtual_joy publish rate [Hz]'
    )

    cmd_publish_rate_arg = DeclareLaunchArgument(
        'cmd_publish_rate',
        default_value='100.0',
        description='rover_gamepad publish rate [Hz]'
    )

    joy_node = Node(
        package='virtual_joy',
        executable='virtual_joy_node',
        name='virtual_joy',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'topic_name': LaunchConfiguration('topic_name'),
            'publish_rate_hz': LaunchConfiguration('joy_publish_rate_hz'),
        }],
    )

    rover_gamepad = Node(
        package='virtual_joy',
        executable='rover_gamepad_node',
        name='rover_gamepad',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'joy_topic': LaunchConfiguration('topic_name'),
            'publish_rate': LaunchConfiguration('cmd_publish_rate'),
            'twist_topic': 'rover_twist',
            'joy_timeout_sec': 1.0,
        }],
    )

    return LaunchDescription([
        topic_name_arg,
        joy_publish_rate_arg,
        cmd_publish_rate_arg,
        joy_node,
        rover_gamepad,
    ])