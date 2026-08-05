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

    def reset_all(self):
        with self._lock:
            self._axes = [0.0] * 8
            self._button_hold = [False] * len(BUTTON_LAYOUT)
            self._button_toggle = [False] * len(BUTTON_LAYOUT)
            self._dpad_hold = {key: False for key in DPAD_DIRECTIONS}
            self._dpad_toggle = {key: False for key in DPAD_DIRECTIONS}

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
        super().__init__(parent, bg='#eef2f4')
        self._label_text = label
        self._side = side
        self._state = state
        self._radius = 45
        self._knob_radius = 12
        self._center = 60

        self._label = tk.Label(self, text=label, bg='#eef2f4', fg='#18313d')
        self._label.pack(pady=(0, 2))
        self._canvas = tk.Canvas(
            self,
            width=120,
            height=120,
            bg='#ffffff',
            highlightbackground='#90a0a8',
            highlightthickness=1,
        )
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
        self._canvas.create_oval(c - r, c - r, c + r, c + r, outline='#536873', width=2)
        self._canvas.create_line(c - r, c, c + r, c, fill='#d4dde1')
        self._canvas.create_line(c, c - r, c, c + r, fill='#d4dde1')

        kr = self._knob_radius
        self._knob = self._canvas.create_oval(c - kr, c - kr, c + kr, c + kr, fill='#147d96', outline='')

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


class GamepadCanvas(tk.Canvas):
    WIDTH = 820
    HEIGHT = 520
    FRONT_Y = 140

    def __init__(self, parent, state: SharedJoyState):
        super().__init__(parent, bg='#f5f8f9', highlightthickness=0)
        self._state = state
        self._regions = []
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._active_stick = None
        self._active_control = None
        self.bind('<Configure>', lambda _event: self.redraw())
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_motion)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Button-3>', self._on_toggle)

    def _xy(self, x, y):
        return self._offset_x + x * self._scale, self._offset_y + y * self._scale

    def _box(self, x1, y1, x2, y2):
        a = self._xy(x1, y1)
        b = self._xy(x2, y2)
        return (*a, *b)

    def _font(self, size, bold=False):
        return ('Yu Gothic UI', max(8, int(size * self._scale)), 'bold' if bold else 'normal')

    def _round_rect(self, box, radius, **kwargs):
        x1, y1, x2, y2 = box
        r = radius * self._scale
        points = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
                  x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(points, smooth=True, splinesteps=12, **kwargs)

    @staticmethod
    def _control_color(hold, toggle):
        if hold:
            return '#f0b44d'
        if toggle:
            return '#65b88b'
        return '#ffffff'

    def _register_region(self, kind, key, logical_box):
        self._regions.append((kind, key, logical_box))

    def _draw_button(self, index, box, label, button_state, radius=12):
        state = button_state[index]
        fill = self._control_color(state['hold'], state['toggle'])
        outline = '#b16a13' if state['hold'] else ('#2f7755' if state['toggle'] else '#58707b')
        width = 3 if state['active'] else 1
        self._round_rect(self._box(*box), radius, fill=fill, outline=outline, width=width)
        x = (box[0] + box[2]) / 2
        y = (box[1] + box[3]) / 2
        self.create_text(*self._xy(x, y), text=label, fill='#18313d', font=self._font(11, True))
        self._register_region('button', index, box)

    def _draw_shoulder(self, index, box, label, button_state, rear=False):
        state = button_state[index]
        fill = self._control_color(state['hold'], state['toggle'])
        outline = '#b16a13' if state['hold'] else ('#2f7755' if state['toggle'] else '#58707b')
        x1, y1, x2, y2 = box
        inset = 12 if rear else 5
        points = []
        for point in ((x1+inset,y1), (x2-inset,y1), (x2,y2-6), (x2-5,y2),
                      (x1+5,y2), (x1,y2-6)):
            points.extend(self._xy(*point))
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=8,
            fill=fill,
            outline=outline,
            width=3 if state['active'] else 1,
        )
        self.create_text(
            *self._xy((x1+x2)/2, (y1+y2)/2),
            text=label,
            fill='#18313d',
            font=self._font(11, True),
        )
        self._register_region('button', index, box)

    def _draw_center_control(self, index, center, symbol, button_state):
        state = button_state[index]
        x, y = center
        box = (x-24, y-19, x+24, y+19)
        self.create_oval(
            *self._box(*box),
            fill=self._control_color(state['hold'], state['toggle']),
            outline='#58707b',
            width=3 if state['active'] else 1,
        )
        if symbol == 'select':
            self.create_rectangle(*self._box(x-9, y-6, x+3, y+4), outline='#18313d', width=2)
            self.create_rectangle(*self._box(x-3, y-2, x+9, y+8), outline='#18313d', width=2)
        elif symbol == 'home':
            roof = []
            for point in ((x-9,y), (x,y-8), (x+9,y), (x+7,y), (x+7,y+8), (x-7,y+8), (x-7,y)):
                roof.extend(self._xy(*point))
            self.create_polygon(roof, fill='#18313d', outline='')
        else:
            for dy in (-6, 0, 6):
                self.create_line(*self._box(x-9, y+dy, x+9, y+dy), fill='#18313d', width=2)
        self._register_region('button', index, box)

    def _draw_dpad(self, dpad_state):
        offset = self.FRONT_Y
        mapping = {
            'up': ((118, 125 + offset, 174, 181 + offset), '▲'),
            'left': ((62, 181 + offset, 118, 237 + offset), '◀'),
            'right': ((174, 181 + offset, 230, 237 + offset), '▶'),
            'down': ((118, 237 + offset, 174, 293 + offset), '▼'),
        }
        for key, (box, label) in mapping.items():
            state = dpad_state[key]
            fill = self._control_color(state['hold'], state['toggle'])
            self._round_rect(self._box(*box), 8, fill=fill, outline='#58707b', width=3 if state['active'] else 1)
            self.create_text(*self._xy((box[0]+box[2])/2, (box[1]+box[3])/2), text=label, fill='#18313d', font=self._font(15, True))
            self._register_region('dpad', key, box)

    def _draw_face(self, button_state):
        offset = self.FRONT_Y
        controls = {
            2: ((674, 143 + offset), '△', '#3b9b72'),
            3: ((618, 199 + offset), '□', '#bf5b85'),
            1: ((730, 199 + offset), '○', '#d65b56'),
            0: ((674, 255 + offset), '×', '#397fb2'),
        }
        for index, (center, label, symbol_color) in controls.items():
            state = button_state[index]
            x, y = center
            box = (x-28, y-28, x+28, y+28)
            self.create_oval(
                *self._box(*box),
                fill=self._control_color(state['hold'], state['toggle']),
                outline=symbol_color,
                width=3 if state['active'] else 2,
            )
            self.create_text(*self._xy(x, y), text=label, fill=symbol_color, font=self._font(17, True))
            self._register_region('button', index, box)

    def _draw_stick(self, side, center, axes):
        x, y = center
        radius = 45
        self.create_oval(*self._box(x-radius, y-radius, x+radius, y+radius), fill='#ffffff', outline='#58707b', width=2)
        self.create_line(*self._box(x-radius, y, x+radius, y), fill='#d1dade')
        self.create_line(*self._box(x, y-radius, x, y+radius), fill='#d1dade')
        if side == 'left':
            vx, vy = axes[0], axes[1]
        else:
            vx, vy = axes[3], axes[4]
        kx, ky = x + vx * radius, y - vy * radius
        self.create_oval(*self._box(kx-12, ky-12, kx+12, ky+12), fill='#147d96', outline='')
        self._register_region('stick', side, (x-radius, y-radius, x+radius, y+radius))

    def _draw_top_view(self, button_state):
        self.create_text(
            *self._xy(48, 20), text='上面', anchor='w', fill='#526771', font=self._font(11, True)
        )
        shell = [
            (96, 124), (101, 140), (719, 140), (724, 124),
            (716, 94), (706, 34), (696, 25), (538, 25),
            (528, 85), (510, 102), (476, 113), (344, 113),
            (310, 102), (292, 85), (282, 25), (124, 25),
            (114, 34), (104, 94),
        ]
        points = []
        for point in shell:
            points.extend(self._xy(*point))
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=18,
            fill='#dfe7ea',
            outline='#7d9099',
            width=2,
        )
        self._draw_shoulder(6, (105, 36, 275, 72), 'L2', button_state, rear=True)
        self._draw_shoulder(4, (118, 82, 262, 116), 'L1', button_state)
        self._draw_shoulder(7, (545, 36, 715, 72), 'R2', button_state, rear=True)
        self._draw_shoulder(5, (558, 82, 702, 116), 'R1', button_state)

    def _draw_front_view(self, axes, button_state, dpad_state):
        offset = self.FRONT_Y
        self.create_text(
            *self._xy(48, 160), text='正面', anchor='w', fill='#526771', font=self._font(11, True)
        )
        silhouette = [
            (720, 123 + offset), (599, 54 + offset), (447, 73 + offset),
            (205, 55 + offset), (78, 151 + offset), (50, 252 + offset),
            (64, 313 + offset), (103, 341 + offset), (165, 350 + offset),
            (317, 270 + offset), (483, 266 + offset), (619, 341 + offset),
            (701, 346 + offset), (750, 320 + offset), (770, 276 + offset),
        ]
        points = []
        for point in silhouette:
            points.extend(self._xy(*point))
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=18,
            fill='#dfe7ea',
            outline='#7d9099',
            width=2,
        )

        self._draw_center_control(8, (345, 141 + offset), 'select', button_state)
        self._draw_center_control(12, (410, 141 + offset), 'home', button_state)
        self._draw_center_control(9, (475, 141 + offset), 'menu', button_state)
        self._draw_dpad(dpad_state)
        self._draw_face(button_state)
        self._draw_stick('left', (305, 235 + offset), axes)
        self._draw_stick('right', (515, 235 + offset), axes)
        self._draw_button(10, (270, 300 + offset, 340, 332 + offset), 'L3', button_state, 8)
        self._draw_button(11, (480, 300 + offset, 550, 332 + offset), 'R3', button_state, 8)
        self.create_text(*self._xy(146, 310 + offset), text='固定移動', fill='#526771', font=self._font(10, True))
        self.create_text(*self._xy(674, 310 + offset), text='固定旋回 / 前後', fill='#526771', font=self._font(10, True))
        self.create_text(*self._xy(305, 175 + offset), text='左スティック', fill='#526771', font=self._font(10, True))
        self.create_text(*self._xy(515, 175 + offset), text='右スティック', fill='#526771', font=self._font(10, True))

    def redraw(self):
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        self._scale = min(width / self.WIDTH, height / self.HEIGHT)
        self._offset_x = (width - self.WIDTH * self._scale) / 2
        self._offset_y = (height - self.HEIGHT * self._scale) / 2
        self.delete('all')
        self._regions.clear()
        axes, _buttons, button_state, dpad_state = self._state.ui_snapshot()

        self._draw_top_view(button_state)
        self._draw_front_view(axes, button_state, dpad_state)

    def _logical_point(self, event):
        return (event.x - self._offset_x) / self._scale, (event.y - self._offset_y) / self._scale

    def _hit(self, event):
        x, y = self._logical_point(event)
        for kind, key, (x1, y1, x2, y2) in reversed(self._regions):
            if x1 <= x <= x2 and y1 <= y <= y2:
                return kind, key
        return None, None

    def _set_hold(self, kind, key, value):
        if kind == 'button':
            self._state.set_button_hold(key, value)
        elif kind == 'dpad':
            self._state.set_dpad_hold(key, value)

    def _on_press(self, event):
        kind, key = self._hit(event)
        if kind == 'stick':
            self._active_stick = key
            self._update_stick(event, key)
        else:
            self._active_control = (kind, key) if kind in {'button', 'dpad'} else None
            self._set_hold(kind, key, True)

    def _on_motion(self, event):
        if self._active_stick:
            self._update_stick(event, self._active_stick)

    def _update_stick(self, event, side):
        center = (305, 235 + self.FRONT_Y) if side == 'left' else (515, 235 + self.FRONT_Y)
        x, y = self._logical_point(event)
        dx, dy = x-center[0], y-center[1]
        length = (dx*dx + dy*dy) ** 0.5
        if length > 45:
            dx, dy = dx*45/length, dy*45/length
        self._state.set_stick(side, dx/45, -dy/45)

    def _on_release(self, event):
        if self._active_stick:
            self._state.reset_stick(self._active_stick)
            self._active_stick = None
        elif self._active_control:
            kind, key = self._active_control
            self._set_hold(kind, key, False)
            self._active_control = None

    def _on_toggle(self, event):
        kind, key = self._hit(event)
        if kind == 'button':
            self._state.toggle_button(key)
        elif kind == 'dpad':
            self._state.toggle_dpad(key)


class VirtualJoyUI:
    BACKGROUND = '#e8edef'
    PANEL = '#f8fafb'
    CONTROLLER = '#eef2f4'
    TEXT = '#18313d'
    MUTED = '#526771'
    NAVY = '#142f3d'
    BUTTON = '#ffffff'
    HOLD = '#f0b44d'
    TOGGLE = '#65b88b'

    def __init__(self, root: tk.Tk, shared_state: SharedJoyState):
        self._root = root
        self._state = shared_state
        self._status_names = {idx: name for idx, name in BUTTON_LAYOUT}

        root.title('virtual_joy')
        root.geometry('860x720')
        root.minsize(760, 660)
        root.configure(bg=self.BACKGROUND)

        header = tk.Frame(root, bg=self.NAVY, height=54)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(
            header,
            text='virtual_joy',
            bg=self.NAVY,
            fg='white',
            font=('Yu Gothic UI', 20, 'bold'),
        ).pack(side='left', padx=(18, 8))
        tk.Label(
            header,
            text='仮想コントローラー',
            bg=self.NAVY,
            fg='#c7d7de',
            font=('Yu Gothic UI', 11),
        ).pack(side='left', pady=(6, 0))
        self._input_state = tk.Label(
            header,
            text='● 入力待機中',
            bg='#244b5b',
            fg='white',
            font=('Yu Gothic UI', 11, 'bold'),
            padx=12,
            pady=6,
        )
        self._input_state.pack(side='right', padx=14)

        body = tk.Frame(root, bg=self.BACKGROUND, padx=10, pady=8)
        body.pack(fill='both', expand=True)
        self._gamepad = GamepadCanvas(body, shared_state)
        self._gamepad.pack(fill='both', expand=True)
        tk.Label(
            body,
            text='△ 前進　× 後退　□ 左旋回　○ 右旋回　｜　R1 低速　L1 中速　R2 標準　L2 高速',
            bg=self.BACKGROUND,
            fg=self.MUTED,
            font=('Yu Gothic UI', 10),
        ).pack(pady=(3, 0))

        footer = tk.Frame(root, bg=self.PANEL, padx=12, pady=8)
        footer.pack(fill='x')
        self._status = tk.Label(
            footer,
            anchor='w',
            justify='left',
            bg=self.PANEL,
            fg=self.TEXT,
            font=('Cascadia Mono', 10),
        )
        self._status.pack(fill='x')
        help_row = tk.Frame(footer, bg=self.PANEL)
        help_row.pack(fill='x', pady=(7, 0))
        self._help = tk.Label(
            help_row,
            text='左: ホールド　　右: 固定　　スティック: ドラッグ',
            anchor='w',
            bg=self.PANEL,
            fg=self.MUTED,
            font=('Yu Gothic UI', 10),
        )
        self._help.pack(side='left', fill='x', expand=True)
        tk.Button(
            help_row,
            text='すべての入力を解除',
            command=self._reset_all,
            bg='#b4443e',
            fg='white',
            activebackground='#943732',
            activeforeground='white',
            font=('Yu Gothic UI', 11, 'bold'),
            padx=12,
            pady=5,
            bd=0,
        ).pack(side='right')

        self._refresh_ui()

    def _reset_all(self):
        self._state.reset_all()

    def _refresh_ui(self):
        axes, _buttons, button_state, dpad_state = self._state.ui_snapshot()
        active_names = []
        active_names.extend(self._status_names[index] for index, state in enumerate(button_state) if state['active'])
        active_names.extend({'up':'上','left':'左','right':'右','down':'下'}[key] for key, state in dpad_state.items() if state['active'])

        active_text = '、'.join(active_names) if active_names else 'なし'
        self._status.configure(
            text=(
                f'左 X {axes[0]:+0.2f}  Y {axes[1]:+0.2f}　 '
                f'右 X {axes[3]:+0.2f}  Y {axes[4]:+0.2f}　 '
                f'十字 X {axes[6]:+0.0f}  Y {axes[7]:+0.0f}\n'
                f'入力中: {active_text}'
            )
        )
        self._input_state.configure(
            text='● 入力中' if active_names or any(abs(value) > 0.001 for value in axes) else '● 入力待機中',
            bg='#9a6510' if active_names or any(abs(value) > 0.001 for value in axes) else '#244b5b',
        )
        self._gamepad.redraw()
        self._root.after(50, self._refresh_ui)


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
