"""Single-source geometry for the virtual controller UI."""

from dataclasses import dataclass
from typing import Optional, Tuple, Union


Point = Tuple[int, int]
Box = Tuple[int, int, int, int]
ControlKey = Union[int, str]


@dataclass(frozen=True)
class ControlGeometry:
    kind: str
    key: ControlKey
    shape: str
    label: str
    points: Tuple[Point, ...] = ()
    box: Optional[Box] = None
    symbol_color: str = "#18313d"
    smooth: bool = False


# Controller shells are decorative only. Interactive geometry is defined once
# in CONTROLS and reused for rendering, state feedback, and hit testing.
TOP_SHELL: Tuple[Point, ...] = (
    (520, 172), (110, 176), (112, 148), (132, 122), (142, 76),
    (153, 66), (209, 64), (218, 124), (254, 146), (364, 148),
    (410, 124), (418, 67), (468, 64), (484, 71), (498, 124),
    (516, 147),
)

BODY_SHELL: Tuple[Point, ...] = (
    (92, 298), (121, 258), (163, 234), (162, 222), (171, 214),
    (236, 214), (245, 229), (302, 236), (374, 230), (384, 214),
    (450, 214), (458, 232), (485, 242), (514, 266), (548, 322),
    (570, 438), (569, 484), (561, 512), (529, 550), (509, 558),
    (486, 558), (450, 540), (400, 480), (377, 464), (270, 460),
    (236, 472), (199, 520), (166, 549), (137, 560), (108, 555),
    (72, 522), (58, 470), (66, 378),
)


CONTROLS: Tuple[ControlGeometry, ...] = (
    ControlGeometry(
        "button", 6, "polygon", "L2",
        points=((152, 78), (141, 125), (169, 119), (188, 119),
                (207, 123), (201, 73), (159, 73)),
        smooth=True,
    ),
    ControlGeometry(
        "button", 4, "polygon", "L1",
        points=((129, 138), (129, 161), (160, 156), (192, 156),
                (224, 161), (224, 138), (200, 130), (188, 128),
                (165, 128), (145, 132)),
        smooth=True,
    ),
    ControlGeometry(
        "button", 7, "polygon", "R2",
        points=((427, 74), (422, 123), (442, 119), (461, 119),
                (489, 125), (478, 79), (475, 75), (471, 73)),
        smooth=True,
    ),
    ControlGeometry(
        "button", 5, "polygon", "R1",
        points=((405, 138), (405, 161), (437, 156), (469, 156),
                (500, 161), (500, 138), (476, 130), (465, 128),
                (440, 128), (421, 132)),
        smooth=True,
    ),
    ControlGeometry("dpad", "up", "polygon", "▲",
                    points=((158, 261), (158, 285), (175, 301),
                            (191, 285), (191, 261))),
    ControlGeometry("dpad", "left", "polygon", "◀",
                    points=((127, 292), (127, 325), (151, 325),
                            (167, 309), (151, 292))),
    ControlGeometry("dpad", "right", "polygon", "▶",
                    points=((183, 308), (186, 313), (199, 325),
                            (223, 325), (223, 292), (199, 292))),
    ControlGeometry("dpad", "down", "polygon", "▼",
                    points=((174, 317), (158, 333), (158, 356),
                            (191, 356), (191, 332), (176, 317))),
    ControlGeometry("button", 8, "oval", "select", box=(247, 273, 269, 295)),
    ControlGeometry("button", 9, "oval", "menu", box=(356, 273, 378, 295)),
    ControlGeometry("button", 2, "oval", "△", box=(436, 253, 471, 289),
                    symbol_color="#3b9b72"),
    ControlGeometry("button", 3, "oval", "□", box=(398, 291, 432, 326),
                    symbol_color="#bf5b85"),
    ControlGeometry("button", 1, "oval", "○", box=(474, 291, 508, 326),
                    symbol_color="#d65b56"),
    ControlGeometry("button", 0, "oval", "×", box=(435, 329, 470, 364),
                    symbol_color="#397fb2"),
    ControlGeometry("stick", "left", "oval", "L3", box=(204, 372, 272, 441)),
    ControlGeometry("stick", "right", "oval", "R3", box=(356, 372, 425, 441)),
)
