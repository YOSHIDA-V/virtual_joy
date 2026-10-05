#!/usr/bin/env python3
"""Jazzy runtime qualification on isolated topics and display; no input events."""
import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from PIL import ImageGrab

SOURCE = Path(__file__).resolve().parents[1]
COMMIT = ""
REQUIRE_CLEAN_SHUTDOWN = False
REQUIRE_LATERAL_STOP = False
NS = "/virtual_joy_jazzy_check"
CRITERIA = {
    "source": "unchanged clean checkout at the specified commit",
    "launch": "installed README rover launch stays alive and publishes neutral Joy/Twist",
    "joy": "8 axes, 13 buttons, unique timestamps, at least 10 received messages/s",
    "twist": "at least 50 received messages/s",
    "conversion": "hold/release, dpad, toggle/reset and enabled/disabled stick state reach ROS subscriptions",
    "forward_timeout": "linear.x and angular.z become zero after Joy stops for more than 1 second",
    "gui": "whole Xvfb display screenshots; visual inspection is required separately",
    "diagnostic": "lateral timeout is measured separately; no hardware-readiness conclusion",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(SOURCE), *args], text=True).strip()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def descendants(parent):
    entries = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
                entries[int(entry.name)] = int(fields[1])
            except (OSError, ValueError, IndexError):
                pass
    found = {parent}
    while True:
        expanded = found | {pid for pid, ppid in entries.items() if ppid in found}
        if expanded == found:
            return sorted(found)
        found = expanded


def process_record(pid):
    base = Path(f"/proc/{pid}")
    try:
        command = (base / "cmdline").read_bytes().decode().rstrip("\0").split("\0")
        environment = dict(item.split("=", 1) for item in (base / "environ").read_bytes().decode().split("\0") if "=" in item)
        return {
            "pid": pid,
            "command": command,
            "cwd": str((base / "cwd").resolve()),
            "environment": {key: environment.get(key) for key in ("ROS_DISTRO", "ROS_DOMAIN_ID", "ROS_AUTOMATIC_DISCOVERY_RANGE", "RMW_IMPLEMENTATION", "DISPLAY")},
            "script_hashes": {item: sha(item) for item in command if Path(item).is_file() and item.endswith((".py", "virtual_joy_node", "rover_gamepad_node"))},
        }
    except (OSError, ValueError):
        return {"pid": pid, "status": "exited_before_inspection"}


class Observer(Node):
    def __init__(self):
        super().__init__("qualification_observer")
        self.joy = []
        self.twist = []
        self.create_subscription(Joy, "joy", self.on_joy, 100)
        self.create_subscription(Twist, "rover_twist", self.on_twist, 100)

    def on_joy(self, msg):
        self.joy.append({"time": time.monotonic(), "stamp": (msg.header.stamp.sec, msg.header.stamp.nanosec), "axes": list(msg.axes), "buttons": list(msg.buttons)})

    def on_twist(self, msg):
        self.twist.append({"time": time.monotonic(), "value": [msg.linear.x, msg.linear.y, msg.angular.z]})


def close_command(proc):
    if proc.poll() is None:
        # launch forwards SIGINT to each owned child. Avoid sending it twice.
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=12)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def near(a, b):
    return len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-5) for x, y in zip(a, b))


def pump(executor, duration, root=None):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        if root is not None:
            root.update()
        executor.spin_once(timeout_sec=0.003)


def run_launch(run_dir, observer, executor):
    wrapper = run_dir / "isolated_readme_launch.py"
    wrapper.write_text('''from launch import LaunchDescription
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
''', encoding="utf-8")
    command = ["ros2", "launch", str(wrapper)]
    log = (run_dir / "readme-launch-runtime.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    processes = []
    try:
        deadline = time.monotonic() + 15
        while not (observer.joy and observer.twist) and time.monotonic() < deadline:
            pump(executor, 0.05)
            check(proc.poll() is None, "README launch exited before topic discovery")
        check(observer.joy and observer.twist, "README launch topic discovery timed out")
        pump(executor, 0.5)
        processes = [process_record(pid) for pid in descendants(proc.pid)]
        for item in processes:
            command_line = item.get("command", [])
            item["parameter_files"] = []
            for index, value in enumerate(command_line[:-1]):
                if value == "--params-file":
                    original = Path(command_line[index + 1])
                    stored = run_dir / f"pid-{item['pid']}-parameters.yaml"
                    stored.write_bytes(original.read_bytes())
                    item["parameter_files"].append({"runtime_path": str(original), "sha256": sha(original), "stored_file": stored.name})
        write_json(run_dir / "launch-processes.json", processes)
        joy_start, twist_start = len(observer.joy), len(observer.twist)
        start = time.monotonic()
        pump(executor, 4.0)
        elapsed = time.monotonic() - start
        joy = observer.joy[joy_start:]
        twist = observer.twist[twist_start:]
        check(proc.poll() is None, "README launch exited during measurement")
        check(len(joy) / elapsed >= 10, "Joy measured rate below criterion")
        check(len(twist) / elapsed >= 50, "Twist measured rate below criterion")
        check(all(len(item["axes"]) == 8 and len(item["buttons"]) == 13 for item in joy), "Joy layout mismatch")
        check(len({tuple(item["stamp"]) for item in joy}) == len(joy), "Joy timestamps repeated")
        check(all(near(item["axes"], [0.0] * 8) and item["buttons"] == [0] * 13 for item in joy), "Initial Joy not neutral")
        check(all(near(item["value"], [0, 0, 0]) for item in twist), "Initial Twist not neutral")
        # ROS timers start before Tk initialization. Capture after the measurement
        # window, then inspect the full virtual display separately.
        display = ImageGrab.grab(xdisplay=os.environ["DISPLAY"])
        check(display.getbbox() is not None, "README GUI display remained blank")
        display.save(run_dir / "readme-launch-display.png")
        sample = {"command": command, "wrapper_sha256": sha(wrapper), "measurement_seconds": elapsed, "joy_messages": len(joy), "joy_hz": len(joy) / elapsed, "twist_messages": len(twist), "twist_hz": len(twist) / elapsed, "joy_topic": NS + "/joy", "twist_topic": NS + "/rover_twist", "status": "PASS"}
        write_json(run_dir / "launch-messages.json", {"joy": joy, "twist": twist})
        return sample
    finally:
        close_command(proc)
        log.close()
        output = (run_dir / "readme-launch-runtime.log").read_text(encoding="utf-8")
        errors = [word for word in ("Traceback (most recent call last)", "ExternalShutdownException", "RCLError", "KeyboardInterrupt") if word in output]
        alive = [item["pid"] for item in processes if item["pid"] != proc.pid and Path(f"/proc/{item['pid']}").exists()]
        shutdown = {"launch_returncode": proc.returncode, "errors": errors, "clean_node_exits": output.count("process has finished cleanly"), "owned_child_pids_remaining": alive}
        write_json(run_dir / "shutdown-result.json", shutdown)
        if REQUIRE_CLEAN_SHUTDOWN:
            check(not errors and not alive and shutdown["clean_node_exits"] == 2, "SIGINT shutdown was not clean")


def run_state_cases(run_dir, observer, executor):
    import tkinter as tk
    from virtual_joy.virtual_joy_node import SharedJoyState, VirtualJoyNode, VirtualJoyUI
    from virtual_joy.rover_gamepad_node import RoverGamepadNode

    state = SharedJoyState()
    front = VirtualJoyNode(state)
    converter = RoverGamepadNode()
    root = tk.Tk()
    ui = VirtualJoyUI(root, state)
    executor.add_node(front)
    executor.add_node(converter)
    cases = []

    def case(name, change, expected, axes=None, buttons=None, screenshot=None, reset=True):
        if reset:
            state.reset_all()
        change()
        mark = time.monotonic()
        pump(executor, 0.5, root)
        joys = [item for item in observer.joy if item["time"] > mark + 0.25]
        twists = [item for item in observer.twist if item["time"] > mark + 0.25]
        check(joys and twists, name + ": no fresh ROS messages")
        check(all(near(item["value"], expected) for item in twists), name + ": unexpected Twist")
        for index, value in (axes or {}).items():
            check(all(math.isclose(item["axes"][index], value, abs_tol=1e-5) for item in joys), name + ": axis mismatch")
        for index, value in (buttons or {}).items():
            check(all(item["buttons"][index] == value for item in joys), name + ": button mismatch")
        row = {"name": name, "input_method": "SharedJoyState application-state API; no mouse/keyboard event", "joy": joys[-1], "twist": twists[-1], "status": "PASS"}
        cases.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if screenshot:
            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(run_dir / screenshot)

    try:
        pump(executor, 1.0, root)
        case("neutral", lambda: None, [0, 0, 0], screenshot="state-neutral-display.png")
        case("triangle_hold", lambda: state.set_button_hold(2, True), [0.1, 0, 0], buttons={2: 1})
        case("release", lambda: state.set_button_hold(2, False), [0, 0, 0], buttons={2: 0}, reset=False)
        case("cross_hold", lambda: state.set_button_hold(0, True), [-0.1, 0, 0], buttons={0: 1})
        case("square_toggle", lambda: state.toggle_button(3), [0, 0, 0.3], buttons={3: 1}, screenshot="state-active-display.png")
        case("reset", lambda: ui._reset_all(), [0, 0, 0], buttons={3: 0}, reset=False)
        case("circle_hold", lambda: state.set_button_hold(1, True), [0, 0, -0.3], buttons={1: 1})
        case("dpad_up", lambda: state.set_dpad_hold("up", True), [0.3, 0, 0], axes={7: 1})
        case("dpad_down", lambda: state.set_dpad_hold("down", True), [-0.3, 0, 0], axes={7: -1})
        case("stick_disabled", lambda: state.set_stick("left", 0, 0.5), [0, 0, 0], axes={1: 0.5})
        case("r1_left_forward", lambda: (state.set_stick("left", 0, 0.5), state.set_button_hold(5, True)), [0.25, 0, 0], axes={1: 0.5}, buttons={5: 1})
        case("r1_right_rotation", lambda: (state.set_stick("right", 0.25, 0), state.set_button_hold(5, True)), [0, 0, -0.26], axes={3: 0.25}, buttons={5: 1})
        case("forward_before_timeout", lambda: state.set_button_hold(2, True), [0.1, 0, 0])
        front._timer.cancel()
        stopped_at = time.monotonic()
        pump(executor, 1.35, root)
        after = [item for item in observer.twist if item["time"] > stopped_at + 1.15]
        check(after and all(near(item["value"], [0, 0, 0]) for item in after), "forward timeout did not stop x/z")
        cases.append({"name": "forward_timeout", "seconds_without_joy": time.monotonic() - stopped_at, "twist": after[-1], "status": "PASS"})
        front._timer.reset()
        case("lateral_before_timeout", lambda: state.set_dpad_hold("left", True), [0, 0.3, 0], axes={6: -1})
        front._timer.cancel()
        stopped_at = time.monotonic()
        pump(executor, 1.35, root)
        after = [item for item in observer.twist if item["time"] > stopped_at + 1.15]
        check(after, "no lateral timeout diagnostic messages")
        diagnostic = {"name": "lateral_timeout", "seconds_without_joy": time.monotonic() - stopped_at, "expected_if_all_motion_components_stopped": [0, 0, 0], "observed_twist": after[-1]["value"], "linear_y_remains_nonzero": abs(after[-1]["value"][1]) > 1e-5, "classification": "existing source behavior; separate from Jazzy compatibility criteria"}
        print(json.dumps(diagnostic, ensure_ascii=False), flush=True)
        write_json(run_dir / "lateral-timeout-result.json", diagnostic)
        write_json(run_dir / "state-messages.json", {"joy": observer.joy, "twist": observer.twist})
        if REQUIRE_LATERAL_STOP:
            check(all(near(item["value"], [0, 0, 0]) for item in after), "lateral velocity remained after Joy timeout")
            cases.append({"name": "lateral_timeout", "twist": after[-1], "status": "PASS"})
        front._timer.reset()
        case("resume_after_timeout", lambda: state.set_button_hold(2, True), [0.1, 0, 0])
        case("angular_before_timeout", lambda: state.set_button_hold(3, True), [0, 0, 0.3])
        front._timer.cancel()
        stopped_at = time.monotonic()
        pump(executor, 1.35, root)
        after = [item for item in observer.twist if item["time"] > stopped_at + 1.15]
        check(after and all(near(item["value"], [0, 0, 0]) for item in after), "angular timeout did not stop rotation")
        cases.append({"name": "angular_timeout", "twist": after[-1], "status": "PASS"})
        write_json(run_dir / "state-messages.json", {"joy": observer.joy, "twist": observer.twist})
        return {"cases": cases, "diagnostic": diagnostic, "status": "PASS"}
    finally:
        state.reset_all()
        root.destroy()
        for node in (front, converter):
            executor.remove_node(node)
            node.destroy_node()


def main():
    global COMMIT, REQUIRE_CLEAN_SHUTDOWN, REQUIRE_LATERAL_STOP
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--state-only", action="store_true", help="component diagnostic; does not qualify cross-process launch")
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--require-clean-shutdown", action="store_true")
    parser.add_argument("--require-lateral-stop", action="store_true")
    args = parser.parse_args()
    COMMIT = args.expected_commit
    REQUIRE_CLEAN_SHUTDOWN = args.require_clean_shutdown
    REQUIRE_LATERAL_STOP = args.require_lateral_stop
    CRITERIA["clean_shutdown"] = "two launch children exit cleanly after SIGINT, no traceback or owned child left" if REQUIRE_CLEAN_SHUTDOWN else "diagnostic only"
    CRITERIA["lateral_timeout"] = "all published x/y/z commands zero after Joy stops for more than one second" if REQUIRE_LATERAL_STOP else "diagnostic only"
    run_dir = Path(args.run_dir)
    check(os.environ.get("ROS_DOMAIN_ID") == "100", "domain must be 100")
    check(os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE") == "LOCALHOST", "local-only discovery required for this test")
    check(git("rev-parse", "HEAD") == COMMIT and not git("status", "--porcelain"), "source checkout must be pinned and clean")
    modules = [importlib.import_module(name) for name in ("virtual_joy.virtual_joy_node", "virtual_joy.rover_gamepad_node", "virtual_joy.controller_ui")]
    files = {str(Path(module.__file__).resolve()): sha(module.__file__) for module in modules}
    for module in modules:
        check(sha(module.__file__) == sha(SOURCE / "virtual_joy" / Path(module.__file__).name), "installed module differs from candidate source")
    from ament_index_python.packages import get_package_share_directory
    installed_share = Path(get_package_share_directory("virtual_joy"))
    for relative in ("package.xml", "launch/virtual_joy_rover.launch.py", "launch/virtual_joy.launch.py"):
        installed = installed_share / relative
        check(sha(installed) == sha(SOURCE / relative), "installed manifest/launch differs from source")
        files[str(installed)] = sha(installed)
    for relative in ("package.xml", "setup.py", "launch/virtual_joy_rover.launch.py", "launch/virtual_joy.launch.py"):
        path = SOURCE / relative
        files[str(path)] = sha(path)
    manifest = {"run_id": run_dir.name, "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "commit": COMMIT, "criteria": CRITERIA, "helper_sha256": sha(__file__), "files_sha256": files, "environment": dict(item.split("=", 1) for item in Path("/etc/os-release").read_text().splitlines() if "=" in item), "python": sys.version, "process": process_record(os.getpid()), "namespace": NS, "topic_isolation": "relative Joy/Twist topics under test namespace; ROS discovery restricted to localhost", "user_mouse_keyboard_events": "none", "source_status_before": git("status", "--porcelain")}
    write_json(run_dir / "runtime-manifest.json", manifest)
    rclpy.init(args=["--ros-args", "-r", "__ns:=" + NS])
    check(rclpy.get_default_context().get_domain_id() == 100, "actual ROS context domain is not 100")
    manifest["actual_rclpy_domain_id"] = rclpy.get_default_context().get_domain_id()
    manifest["actual_rmw"] = rclpy.get_rmw_implementation_identifier()
    manifest["package_prefix"] = subprocess.check_output(["ros2", "pkg", "prefix", "virtual_joy"], text=True).strip()
    write_json(run_dir / "runtime-manifest.json", manifest)
    observer = Observer()
    executor = SingleThreadedExecutor()
    executor.add_node(observer)
    result = {"software_compatibility": "NOT_COMPLETED", "windows_desktop_and_manual_mouse_operation": "UNVERIFIED", "physical_rover": "UNVERIFIED"}
    try:
        if not args.state_only:
            result["readme_launch"] = run_launch(run_dir, observer, executor)
        result["state_runtime"] = run_state_cases(run_dir, observer, executor)
        check(not git("status", "--porcelain"), "source became dirty during test")
        check(all(sha(path) == value for path, value in files.items()), "source artifact hash changed during test")
        result["software_compatibility"] = "COMPONENTS_ONLY" if args.state_only else "PASS"
        result["source_status_after"] = git("status", "--porcelain")
        result["files_unchanged"] = True
    except Exception:
        result["failure"] = traceback.format_exc()
        raise
    finally:
        result["finish_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_json(run_dir / "runtime-result.json", result)
        executor.remove_node(observer)
        observer.destroy_node()
        executor.shutdown()
        rclpy.shutdown()
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
