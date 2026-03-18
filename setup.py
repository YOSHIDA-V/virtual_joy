from glob import glob
from setuptools import setup
from setuptools import find_packages

package_name = 'virtual_joy'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@example.com',
    description='Virtual Joy publisher',
    license='MIT',
    entry_points={
        'console_scripts': [
            'virtual_joy_node = virtual_joy.virtual_joy_node:main',
            'rover_gamepad_node = virtual_joy.rover_gamepad_node:main',
        ],
    },
)

