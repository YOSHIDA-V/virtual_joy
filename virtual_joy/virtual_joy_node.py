#!/usr/bin/env python3

import threading
import tkinter as tk

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


BUTTON_LAYOUT = [
    (0, 'CROSS'),
    (1, 'CIRCLE'),
    (2, 'TRIANGLE'),
    (3, 'SQUARE'),
    (4, 'L1'),
    (5, 'R1'),
    (6, 'L2'),
    (7, 'R2'),
    (8, 'SELECT'),
    (9, 'START'),
    (10, 'L3'),
    (11, 'R3'),
    (12, 'PS'),
]

DPAD_DIRECTIONS = ('left', 'right', 'up', 'down')
DISPLAY_LABELS = {
    0: '×',   # CROSS
    1: '○',   # CIRCLE
    2: '△',   # TRIANGLE
    3: '□',   # SQUARE
}


class SharedJoyState:
    def __init__(self):
        self._lock = threading.Lock()
        # Axis layout aligned with megarover3_bringup/src/rover_gamepad.cpp:
        # 0: LEFT_X, 1: LEFT_Y, 2: UNUSED, 3: RIGHT_X, 4: RIGHT_Y, 5: UNUSED, 6: DPAD_X, 7: DPAD_Y
        self._axes = [0.0] * 8
        self._button_hold = [False] * len(BUTTON_LAYOUT)
        self._button_toggle = [False] * len(BUTTON_LAYOUT)
        self._dpad_hold = {key: False for key in DPAD_DIRECTIONS}
        self._dpad_toggle = {key: False for key in DPAD_DIRECTIONS}

    def set_button_hold(self, index: int, pressed: bool):
        with self._lock:
            self._button_hold[index] = pressed

    def toggle_button(self, index: int):
        with self._lock:
            self._button_toggle[index] = not self._button_toggle[index]

    def set_dpad_hold(self, direction: str, pressed: bool):
        with self._lock:
            self._dpad_hold[direction] = pressed

    def toggle_dpad(self, direction: str):
        with self._lock:
            self._dpad_toggle[direction] = not self._dpad_toggle[direction]

    def set_stick(self, side: str, x: float, y: float):
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        with self._lock:
            if side == 'left':
                self._axes[0] = x
                self._axes[1] = y
            elif side == 'right':
                self._axes[3] = x
                self._axes[4] = y

    def reset_stick(self, side: str):
        self.set_stick(side, 0.0, 0.0)

    def _dpad_axes(self):
        left_active = self._dpad_hold['left'] or self._dpad_toggle['left']
        right_active = self._dpad_hold['right'] or self._dpad_toggle['right']
        up_active = self._dpad_hold['up'] or self._dpad_toggle['up']
        down_active = self._dpad_hold['down'] or self._dpad_toggle['down']

        dpad_x = int(right_active) - int(left_active)
        dpad_y = int(up_active) - int(down_active)
        return float(max(-1, min(1, dpad_x))), float(max(-1, min(1, dpad_y)))

    def snapshot(self):
        with self._lock:
            axes = list(self._axes)
            buttons = [
                1 if self._button_hold[i] or self._button_toggle[i] else 0
                for i in range(len(self._button_hold))
            ]
            axes[6], axes[7] = self._dpad_axes()
            return axes, buttons

    def ui_snapshot(self):
        with self._lock:
            axes = list(self._axes)
            buttons = [
                1 if self._button_hold[i] or self._button_toggle[i] else 0
                for i in range(len(self._button_hold))
            ]
            axes[6], axes[7] = self._dpad_axes()

            button_state = [
                {
                    'active': self._button_hold[i] or self._button_toggle[i],
                    'hold': self._button_hold[i],
                    'toggle': self._button_toggle[i],
                }
                for i in range(len(self._button_hold))
            ]
            dpad_state = {
                key: {
                    'active': self._dpad_hold[key] or self._dpad_toggle[key],
                    'hold': self._dpad_hold[key],
                    'toggle': self._dpad_toggle[key],
                }
                for key in DPAD_DIRECTIONS
            }
            return axes, buttons, button_state, dpad_state


class VirtualJoyNode(Node):
    def __init__(self, shared_state: SharedJoyState):
        super().__init__('virtual_joy')
        self._state = shared_state

        self.declare_parameter('topic_name', 'joy')
        self.declare_parameter('publish_rate_hz', 20.0)

        topic_name = self.get_parameter('topic_name').value
        publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        publish_rate_hz = max(1.0, publish_rate_hz)

        self._publisher = self.create_publisher(Joy, topic_name, 10)
        self._timer = self.create_timer(1.0 / publish_rate_hz, self._on_timer)

        self.get_logger().info(
            f'virtual_joy started topic={topic_name} rate={publish_rate_hz:.1f}Hz'
        )

    def _on_timer(self):
        axes, buttons = self._state.snapshot()
        msg = Joy()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.axes = axes
        msg.buttons = buttons
        self._publisher.publish(msg)


class StickCanvas(tk.Frame):
    def __init__(self, parent, label: str, side: str, state: SharedJoyState, scale: float = 1.0):
        super().__init__(parent)
        self._label_text = label
        self._side = side
        self._state = state
        self._radius = 45
        self._knob_radius = 12
        self._center = 60

        self._label = tk.Label(self, text=label)
        self._label.pack(pady=(0, 2))
        self._canvas = tk.Canvas(self, width=120, height=120, bg='white', highlightthickness=1)
        self._canvas.pack()
        self._knob = None

        self._canvas.bind('<ButtonPress-1>', self._on_drag)
        self._canvas.bind('<B1-Motion>', self._on_drag)
        self._canvas.bind('<ButtonRelease-1>', self._on_release)
        self.set_scale(scale)

    def set_scale(self, scale: float):
        self._radius = max(24, int(round(45 * scale)))
        self._knob_radius = max(8, int(round(12 * scale)))
        self._center = max(self._radius + self._knob_radius + 2, int(round(60 * scale)))
        canvas_size = self._center * 2

        self._label.configure(font=('Segoe UI', max(8, int(round(10 * scale))), 'bold'))
        self._label.pack_configure(pady=(0, max(1, int(round(2 * scale)))))
        self._canvas.configure(width=canvas_size, height=canvas_size)

        self._canvas.delete('all')
        c = self._center
        r = self._radius
        self._canvas.create_oval(c - r, c - r, c + r, c + r, outline='#666', width=2)
        self._canvas.create_line(c - r, c, c + r, c, fill='#ddd')
        self._canvas.create_line(c, c - r, c, c + r, fill='#ddd')

        kr = self._knob_radius
        self._knob = self._canvas.create_oval(c - kr, c - kr, c + kr, c + kr, fill='#4aa3ff', outline='')

        axes, _buttons = self._state.snapshot()
        if self._side == 'left':
            x_norm, y_norm = axes[0], axes[1]
        else:
            x_norm, y_norm = axes[3], axes[4]
        self._set_knob(x_norm, y_norm)

    def _set_knob(self, x_norm: float, y_norm: float):
        c = self._center
        px = c + x_norm * self._radius
        py = c - y_norm * self._radius
        kr = self._knob_radius
        self._canvas.coords(self._knob, px - kr, py - kr, px + kr, py + kr)

    def _on_drag(self, event):
        dx = event.x - self._center
        dy = event.y - self._center
        length = (dx * dx + dy * dy) ** 0.5
        if length > self._radius:
            scale = self._radius / length
            dx *= scale
            dy *= scale
        x_norm = dx / self._radius
        y_norm = -dy / self._radius

        self._set_knob(x_norm, y_norm)
        self._state.set_stick(self._side, x_norm, y_norm)

    def _on_release(self, _event):
        self._set_knob(0.0, 0.0)
        self._state.reset_stick(self._side)


class VirtualJoyUI:
    def __init__(self, root: tk.Tk, shared_state: SharedJoyState):
        self._root = root
        self._state = shared_state
        self._button_widgets = {}
        self._dpad_widgets = {}
        self._base_ui_scale = 0.58
        self._ui_scale = self._base_ui_scale
        self._layout_density = 1.0
        self._resize_after_id = None
        self._enforcing_aspect = False
        self._base_win_w = 620
        self._base_win_h = 360
        self._aspect_n = 31
        self._aspect_d = 18

        root.title('Virtual Joy (PS3-like)')
        root.geometry(f'{self._base_win_w}x{self._base_win_h}')
        root.wm_aspect(self._aspect_n, self._aspect_d, self._aspect_n, self._aspect_d)

        self._top = tk.Frame(root, padx=self._s(8), pady=self._s(8))
        self._top.pack(fill='both', expand=True)

        self._pad = tk.LabelFrame(self._top, text='PS3-like Controller', padx=self._s(10), pady=self._s(10))
        self._pad.pack(fill='both', expand=True)

        for i in range(9):
            self._pad.columnconfigure(i, weight=1)
        for i in range(7):
            self._pad.rowconfigure(i, weight=1)

        self._add_ps_button(self._pad, 4, 0, 1, width=4, height=1)
        self._add_ps_button(self._pad, 6, 1, 1, width=4, height=1)
        self._add_ps_button(self._pad, 5, 0, 7, width=4, height=1)
        self._add_ps_button(self._pad, 7, 1, 7, width=4, height=1)

        self._add_ps_button(self._pad, 8, 3, 3, width=4, height=1)
        self._add_ps_button(self._pad, 12, 3, 4, width=4, height=1)
        self._add_ps_button(self._pad, 9, 3, 5, width=4, height=1)

        self._dpad_frame = tk.LabelFrame(self._pad, text='D-Pad', padx=self._s(6), pady=self._s(6))
        self._dpad_frame.grid(row=2, column=1, rowspan=3, sticky='n')
        self._build_dpad(self._dpad_frame)

        self._face_frame = tk.LabelFrame(self._pad, text='Face', padx=self._s(6), pady=self._s(6))
        self._face_frame.grid(row=2, column=7, rowspan=3, sticky='n')
        self._build_face_cluster(self._face_frame)

        self._left_stick_frame = tk.LabelFrame(self._pad, text='Left Stick', padx=self._s(2), pady=self._s(2))
        self._left_stick_frame.grid(row=4, column=2, rowspan=2, columnspan=2, sticky='n')
        self._left_stick_canvas = StickCanvas(
            self._left_stick_frame, 'L', 'left', shared_state, scale=self._ui_scale
        )
        self._left_stick_canvas.pack()

        self._right_stick_frame = tk.LabelFrame(self._pad, text='Right Stick', padx=self._s(2), pady=self._s(2))
        self._right_stick_frame.grid(row=4, column=5, rowspan=2, columnspan=2, sticky='n')
        self._right_stick_canvas = StickCanvas(
            self._right_stick_frame, 'R', 'right', shared_state, scale=self._ui_scale
        )
        self._right_stick_canvas.pack()

        self._add_ps_button(self._pad, 10, 6, 3, width=3, height=1)
        self._add_ps_button(self._pad, 11, 6, 5, width=3, height=1)

        status_font = ('Segoe UI', max(8, int(round(9 * self._ui_scale))))
        self._status = tk.Label(root, anchor='w', padx=self._s(8), font=status_font)
        self._status.pack(fill='x', pady=(self._s(2), self._s(6)))

        self._help = tk.Label(
            root,
            text='Left click: hold  |  Right click: toggle  |  Stick: left-drag and release to center',
            anchor='w',
            padx=self._s(8),
            font=status_font,
        )
        self._help.pack(fill='x', pady=(0, self._s(8)))

        root.update_idletasks()
        min_w = root.winfo_reqwidth()
        min_h = root.winfo_reqheight()
        root.minsize(min_w, min_h)
        root.geometry(f'{min_w}x{min_h}')
        self._base_win_w = min_w
        self._base_win_h = min_h
        root.bind('<Configure>', self._on_root_resize)
        self._apply_scale()

        self._refresh_ui()

    def _s(self, value: int) -> int:
        return max(1, int(round(value * self._ui_scale * self._layout_density)))

    def _btn_h(self, base_height: int = 1) -> int:
        ratio = self._ui_scale / max(0.01, self._base_ui_scale)
        return max(1, int(round(base_height * max(1.0, ratio * 0.65))))

    def _bind_button_events(self, widget: tk.Widget, on_hold, on_toggle):
        widget.bind('<ButtonPress-1>', lambda _e: on_hold(True))
        widget.bind('<ButtonRelease-1>', lambda _e: on_hold(False))
        widget.bind('<Button-3>', lambda _e: (on_toggle(), 'break')[1])

    def _add_ps_button(self, parent, index, row, col, width=5, height=1):
        labels = {idx: name for idx, name in BUTTON_LAYOUT}
        text = DISPLAY_LABELS.get(index, labels[index])
        base_width = width
        btn = tk.Button(
            parent,
            text=text,
            width=max(2, int(round(base_width * self._ui_scale))),
            height=self._btn_h(height),
            bg='#f0f0f0',
            font=('Segoe UI', max(8, int(round(9 * self._ui_scale)))),
        )
        btn._base_width = base_width
        btn._base_height = height
        btn.grid(row=row, column=col, padx=self._s(3), pady=self._s(3), sticky='nsew')
        self._bind_button_events(
            btn,
            on_hold=lambda pressed, i=index: self._state.set_button_hold(i, pressed),
            on_toggle=lambda i=index: self._state.toggle_button(i),
        )
        self._button_widgets[index] = btn

    def _build_face_cluster(self, parent):
        placements = {
            2: (0, 1),
            3: (1, 0),
            1: (1, 2),
            0: (2, 1),
        }
        for idx, (row, col) in placements.items():
            self._add_ps_button(parent, idx, row, col, width=4, height=1)

    def _build_dpad(self, parent):
        mapping = {
            'up': ('UP', 0, 1),
            'left': ('LEFT', 1, 0),
            'right': ('RIGHT', 1, 2),
            'down': ('DOWN', 2, 1),
        }

        for key, (label, row, col) in mapping.items():
            base_width = 4
            btn = tk.Button(
                parent,
                text=label,
                width=max(2, int(round(base_width * self._ui_scale))),
                height=self._btn_h(1),
                bg='#f0f0f0',
                font=('Segoe UI', max(8, int(round(9 * self._ui_scale)))),
            )
            btn._base_width = base_width
            btn._base_height = 1
            btn.grid(row=row, column=col, padx=self._s(3), pady=self._s(3))
            self._bind_button_events(
                btn,
                on_hold=lambda pressed, d=key: self._state.set_dpad_hold(d, pressed),
                on_toggle=lambda d=key: self._state.toggle_dpad(d),
            )
            self._dpad_widgets[key] = btn

    @staticmethod
    def _color_for_state(active: bool, hold: bool, toggle: bool):
        if hold:
            return '#f6c667'
        if toggle:
            return '#87d37c'
        if active:
            return '#9ec9ff'
        return '#f0f0f0'

    def _refresh_ui(self):
        axes, buttons, button_state, dpad_state = self._state.ui_snapshot()

        for idx, widget in self._button_widgets.items():
            st = button_state[idx]
            color = self._color_for_state(st['active'], st['hold'], st['toggle'])
            widget.configure(bg=color, activebackground=color)

        for key, widget in self._dpad_widgets.items():
            st = dpad_state[key]
            color = self._color_for_state(st['active'], st['hold'], st['toggle'])
            widget.configure(bg=color, activebackground=color)

        self._status.configure(text=f'axes={axes}  buttons={buttons}')
        self._root.after(50, self._refresh_ui)

    def _on_root_resize(self, event):
        if event.widget is not self._root or self._enforcing_aspect:
            return
        if self._enforce_aspect_ratio(event.width, event.height):
            return
        if self._resize_after_id is not None:
            self._root.after_cancel(self._resize_after_id)
        self._resize_after_id = self._root.after(60, self._apply_resize_scale)

    def _enforce_aspect_ratio(self, width: int, height: int) -> bool:
        target_w = int(round(height * self._aspect_n / self._aspect_d))
        target_h = int(round(width * self._aspect_d / self._aspect_n))
        if abs(target_w - width) <= abs(target_h - height):
            new_w = target_w
            new_h = height
        else:
            new_w = width
            new_h = target_h

        new_w = max(self._base_win_w, new_w)
        new_h = max(self._base_win_h, new_h)
        if abs(new_w - width) <= 1 and abs(new_h - height) <= 1:
            return False

        self._enforcing_aspect = True
        try:
            self._root.geometry(f'{new_w}x{new_h}')
        finally:
            self._root.after(30, lambda: setattr(self, '_enforcing_aspect', False))
        return True

    def _apply_resize_scale(self):
        self._resize_after_id = None
        width_ratio = self._root.winfo_width() / max(1, self._base_win_w)
        height_ratio = self._root.winfo_height() / max(1, self._base_win_h)
        ratio = min(width_ratio, height_ratio)
        new_scale = max(self._base_ui_scale, min(self._base_ui_scale * ratio, self._base_ui_scale * 4.2))
        screen_w = max(1, self._root.winfo_screenwidth())
        screen_h = max(1, self._root.winfo_screenheight())
        is_near_fullscreen = (
            self._root.winfo_width() >= int(screen_w * 0.92)
            or self._root.winfo_height() >= int(screen_h * 0.92)
        )
        new_density = min(1.6, max(1.0, ratio ** 0.35))
        if is_near_fullscreen:
            new_density = max(new_density, 1.25)

        if abs(new_scale - self._ui_scale) < 0.03 and abs(new_density - self._layout_density) < 0.01:
            return
        self._ui_scale = new_scale
        self._layout_density = new_density
        self._apply_scale()

    def _apply_scale(self):
        button_font = ('Segoe UI', max(8, int(round(9 * self._ui_scale))))
        status_font = ('Segoe UI', max(8, int(round(9 * self._ui_scale))))
        frame_font = ('Segoe UI', max(8, int(round(10 * self._ui_scale))), 'bold')

        self._top.configure(padx=self._s(8), pady=self._s(8))
        self._pad.configure(padx=self._s(10), pady=self._s(10), font=frame_font)
        self._dpad_frame.configure(padx=self._s(6), pady=self._s(6), font=frame_font)
        self._face_frame.configure(padx=self._s(6), pady=self._s(6), font=frame_font)
        self._left_stick_frame.configure(padx=self._s(2), pady=self._s(2), font=frame_font)
        self._right_stick_frame.configure(padx=self._s(2), pady=self._s(2), font=frame_font)

        for widget in self._button_widgets.values():
            widget.configure(
                width=max(2, int(round(widget._base_width * self._ui_scale))),
                height=self._btn_h(widget._base_height),
                font=button_font,
            )
            widget.grid_configure(padx=self._s(3), pady=self._s(3))

        for widget in self._dpad_widgets.values():
            widget.configure(
                width=max(2, int(round(widget._base_width * self._ui_scale))),
                height=self._btn_h(widget._base_height),
                font=button_font,
            )
            widget.grid_configure(padx=self._s(3), pady=self._s(3))

        self._left_stick_canvas.set_scale(self._ui_scale)
        self._right_stick_canvas.set_scale(self._ui_scale)

        self._status.configure(font=status_font, padx=self._s(8))
        self._status.pack_configure(pady=(self._s(2), self._s(6)))
        self._help.configure(font=status_font, padx=self._s(8))
        self._help.pack_configure(pady=(0, self._s(8)))


def main(args=None):
    rclpy.init(args=args)
    shared_state = SharedJoyState()
    node = VirtualJoyNode(shared_state)

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    root = tk.Tk()
    VirtualJoyUI(root, shared_state)

    def on_close():
        try:
            node.destroy_node()
            rclpy.shutdown()
        except Exception:
            pass
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)

    try:
        root.mainloop()
    finally:
        if spin_thread.is_alive():
            spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()
