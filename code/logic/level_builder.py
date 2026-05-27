from PySide6.QtCore import QRectF

from models.player import Box, Diamond, Hazard, Level, Lever, MovingSolid, Switch


def rectangle(x, y, width, height):
    return QRectF(float(x), float(y), float(width), float(height))


def _borders():
    return [
        rectangle(0, 0, 30, 720),
        rectangle(1170, 0, 30, 720),
        rectangle(0, 0, 1200, 26),
    ]


def _diamonds(points):
    return [Diamond(rectangle(x, y, 44, 44), owner) for x, y, owner in points]


def create_level(number: int) -> Level:
    builders = {1: _level_one, 2: _level_two, 3: _level_three, 4: _level_four}
    return builders.get(number, _level_one)()


def _level_one():
    return Level(
        1,
        "jungle",
        (66, 606),
        (126, 606),
        rectangle(940, 78, 76, 100),
        rectangle(1030, 78, 76, 100),
        platforms=_borders() + [
            rectangle(30, 670, 250, 50),
            rectangle(370, 670, 250, 50),
            rectangle(710, 670, 460, 50),
            rectangle(80, 548, 260, 26),
            rectangle(470, 548, 250, 26),
            rectangle(780, 508, 260, 26),
            rectangle(300, 426, 290, 26),
            rectangle(720, 386, 340, 26),
            rectangle(105, 304, 300, 26),
            rectangle(515, 264, 270, 26),
            rectangle(888, 178, 250, 26),
        ],
        hazards=[
            Hazard(rectangle(280, 670, 90, 50), "water"),
            Hazard(rectangle(620, 670, 90, 50), "fire"),
        ],
        diamonds=_diamonds([
            (190, 612, "fire"),
            (500, 612, "water"),
            (182, 494, "water"),
            (438, 372, "fire"),
            (646, 210, "water"),
            (948, 128, "fire"),
            (1040, 128, "water"),
        ]),
    )


def _level_two():
    return Level(
        2,
        "temple",
        (66, 606),
        (126, 606),
        rectangle(88, 82, 76, 100),
        rectangle(996, 82, 76, 100),
        platforms=_borders() + [
            rectangle(30, 670, 285, 50),
            rectangle(395, 670, 150, 50),
            rectangle(625, 670, 545, 50),
            rectangle(72, 548, 250, 26),
            rectangle(432, 548, 160, 26),
            rectangle(682, 548, 260, 26),
            rectangle(138, 426, 290, 26),
            rectangle(620, 426, 300, 26),
            rectangle(70, 304, 270, 26),
            rectangle(500, 304, 220, 26),
            rectangle(850, 304, 240, 26),
            rectangle(66, 182, 240, 26),
            rectangle(934, 182, 220, 26),
        ],
        hazards=[
            Hazard(rectangle(315, 670, 80, 50), "fire"),
            Hazard(rectangle(545, 670, 80, 50), "water"),
        ],
        diamonds=_diamonds([
            (205, 612, "water"),
            (448, 612, "fire"),
            (760, 494, "fire"),
            (225, 372, "water"),
            (585, 250, "fire"),
            (936, 250, "water"),
            (1008, 128, "fire"),
        ]),
        switches=[
            Switch(rectangle(470, 652, 72, 18), "gate_one", "green"),
            Switch(rectangle(630, 652, 72, 18), "gate_one", "green"),
        ],
        movers=[
            MovingSolid(
                rectangle(580, 426, 42, 244),
                "gate_one",
                "green",
                rectangle(580, 138, 42, 244),
                speed=0.085,
            )
        ],
    )


def _level_three():
    return Level(
        3,
        "jungle",
        (66, 606),
        (126, 606),
        rectangle(946, 82, 76, 100),
        rectangle(1036, 82, 76, 100),
        platforms=_borders() + [
            rectangle(30, 670, 230, 50),
            rectangle(340, 670, 240, 50),
            rectangle(745, 670, 425, 50),
            rectangle(76, 548, 250, 26),
            rectangle(424, 548, 230, 26),
            rectangle(790, 548, 260, 26),
            rectangle(198, 426, 260, 26),
            rectangle(548, 426, 165, 26),
            rectangle(872, 426, 240, 26),
            rectangle(70, 304, 235, 26),
            rectangle(715, 304, 290, 26),
            rectangle(460, 182, 235, 26),
            rectangle(900, 182, 250, 26),
        ],
        hazards=[
            Hazard(rectangle(260, 670, 80, 50), "water"),
            Hazard(rectangle(580, 670, 165, 50), "fire"),
        ],
        diamonds=_diamonds([
            (170, 612, "fire"),
            (466, 612, "water"),
            (156, 494, "water"),
            (374, 372, "fire"),
            (604, 128, "water"),
            (904, 372, "fire"),
            (1042, 128, "water"),
        ]),
        levers=[
            Lever(rectangle(270, 386, 54, 46), "bridge", "yellow")
        ],
        movers=[
            MovingSolid(
                rectangle(660, 548, 90, 26),
                "bridge",
                "yellow",
                rectangle(655, 426, 90, 26),
                speed=0.045,
            )
        ],
    )


def _level_four():
    return Level(
        4,
        "temple",
        (66, 606),
        (126, 606),
        rectangle(926, 82, 76, 100),
        rectangle(1020, 82, 76, 100),
        platforms=_borders() + [
            rectangle(30, 670, 220, 50),
            rectangle(330, 670, 170, 50),
            rectangle(580, 670, 190, 50),
            rectangle(850, 670, 320, 50),
            rectangle(84, 548, 250, 26),
            rectangle(415, 548, 210, 26),
            rectangle(720, 548, 220, 26),
            rectangle(178, 426, 270, 26),
            rectangle(540, 426, 215, 26),
            rectangle(860, 426, 255, 26),
            rectangle(78, 304, 220, 26),
            rectangle(430, 304, 220, 26),
            rectangle(772, 304, 335, 26),
            rectangle(214, 182, 200, 26),
            rectangle(885, 182, 260, 26),
        ],
        hazards=[
            Hazard(rectangle(250, 670, 80, 50), "fire"),
            Hazard(rectangle(500, 670, 80, 50), "water"),
            Hazard(rectangle(770, 670, 80, 50), "poison"),
        ],
        diamonds=_diamonds([
            (164, 612, "water"),
            (384, 612, "fire"),
            (885, 612, "water"),
            (235, 372, "fire"),
            (570, 372, "water"),
            (850, 250, "fire"),
            (1030, 128, "water"),
        ]),
        switches=[
            Switch(rectangle(360, 652, 70, 18), "first_gate", "green"),
            Switch(rectangle(610, 652, 70, 18), "first_gate", "green"),
            Switch(rectangle(574, 408, 70, 18), "second_gate", "orange"),
            Switch(rectangle(802, 286, 70, 18), "second_gate", "orange"),
        ],
        movers=[
            MovingSolid(
                rectangle(532, 426, 42, 244),
                "first_gate",
                "green",
                rectangle(532, 138, 42, 244),
                speed=0.085,
            ),
            MovingSolid(
                rectangle(755, 304, 42, 244),
                "second_gate",
                "orange",
                rectangle(755, 36, 42, 244),
                speed=0.085,
            ),
        ],
        boxes=[
            Box(rectangle(105, 626, 44, 44)),
            Box(rectangle(445, 504, 44, 44)),
        ],
    )
