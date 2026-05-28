from PySide6.QtCore import QRectF

from models.player import Diamond, Hazard, Level, Lever, MovingSolid, Switch


# Crea rectángulos para el mapa
def rectangle(x, y, width, height):
    return QRectF(float(x), float(y), float(width), float(height))


# Crea una plataforma horizontal
def platform(x, y, width):
    return rectangle(x, y, width, 26)


# Crea una pared visible
def wall(x, y, height):
    return rectangle(x, y, 26, height)


# Coloca los bordes del escenario
def borders():
    return [
        wall(0, 0, 720),
        wall(1174, 0, 720),
        platform(0, 0, 1200),
    ]


# Coloca diamantes pequeños en zonas alcanzables
def diamonds(points):
    return [Diamond(rectangle(x, y, 34, 34), owner) for x, y, owner in points]


# Devuelve el nivel elegido
def create_level(number: int) -> Level:
    builders = {1: level_one, 2: level_two, 3: level_three, 4: level_four}
    return builders.get(number, level_one)()


# Nivel 1: enseña movimiento y saltos cómodos
def level_one():
    return Level(
        1,
        "jungle",
        (64, 624),
        (112, 624),
        rectangle(1010, 70, 66, 96),
        rectangle(1084, 70, 66, 96),
        platforms=borders() + [
            platform(26, 680, 274),
            platform(378, 680, 304),
            platform(760, 680, 414),
            platform(72, 576, 350),
            platform(360, 474, 370),
            platform(686, 372, 356),
            platform(420, 270, 348),
            platform(824, 166, 350),
        ],
        hazards=[
            Hazard(rectangle(300, 680, 78, 40), "water"),
            Hazard(rectangle(682, 680, 78, 40), "fire"),
        ],
        diamonds=diamonds([
            (188, 632, "fire"),
            (236, 532, "water"),
            (498, 430, "fire"),
            (822, 328, "water"),
            (562, 226, "fire"),
            (1100, 122, "water"),
        ]),
    )


# Nivel 2: dos elevadores permiten subir hasta las puertas
def level_two():
    return Level(
        2,
        "temple",
        (112, 624),
        (162, 624),
        rectangle(1004, 44, 66, 96),
        rectangle(1080, 44, 66, 96),
        platforms=borders() + [
            platform(26, 680, 430),
            platform(526, 680, 286),
            platform(884, 680, 188),
            platform(126, 450, 414),
            platform(612, 450, 460),
            platform(126, 236, 650),
            platform(720, 140, 454),
        ],
        hazards=[
            Hazard(rectangle(456, 680, 70, 40), "water"),
            Hazard(rectangle(812, 680, 72, 40), "fire"),
            Hazard(rectangle(540, 450, 72, 26), "poison"),
        ],
        diamonds=diamonds([
            (270, 634, "fire"),
            (650, 634, "water"),
            (952, 634, "fire"),
            (850, 406, "water"),
            (286, 406, "fire"),
            (344, 192, "water"),
            (794, 96, "fire"),
            (1110, 96, "water"),
        ]),
        levers=[
            Lever(rectangle(1110, 636, 48, 42), "right_lift", "green"),
            Lever(rectangle(40, 406, 48, 42), "left_lift", "yellow"),
        ],
        movers=[
            MovingSolid(rectangle(1072, 680, 102, 26), "right_lift", "green", rectangle(1072, 450, 102, 26), speed=0.026),
            MovingSolid(rectangle(26, 450, 100, 26), "left_lift", "yellow", rectangle(26, 236, 100, 26), speed=0.026),
        ],
    )


# Nivel 3: cada personaje ayuda a subir al otro y la palanca baja el puente
def level_three():
    return Level(
        3,
        "temple",
        (978, 624),
        (150, 624),
        rectangle(956, 76, 66, 96),
        rectangle(1032, 76, 66, 96),
        platforms=borders() + [
            platform(26, 680, 480),
            platform(694, 680, 480),
            platform(126, 416, 294),
            platform(780, 416, 292),
            platform(72, 300, 356),
            platform(772, 300, 374),
            platform(836, 172, 338),
            wall(572, 430, 250),
        ],
        hazards=[
            Hazard(rectangle(506, 680, 188, 40), "poison"),
            Hazard(rectangle(270, 416, 90, 26), "water"),
            Hazard(rectangle(826, 416, 90, 26), "fire"),
        ],
        diamonds=diamonds([
            (206, 634, "water"),
            (1032, 634, "fire"),
            (184, 370, "water"),
            (364, 370, "fire"),
            (822, 370, "water"),
            (998, 370, "fire"),
            (248, 254, "water"),
            (1076, 128, "fire"),
        ]),
        switches=[
            Switch(rectangle(300, 662, 60, 18), "right_lift", "orange"),
            Switch(rectangle(870, 398, 60, 18), "left_lift", "green"),
        ],
        levers=[
            Lever(rectangle(930, 258, 48, 42), "upper_bridge", "yellow"),
        ],
        movers=[
            MovingSolid(rectangle(32, 654, 94, 26), "left_lift", "green", rectangle(32, 416, 94, 26), speed=0.035),
            MovingSolid(rectangle(1072, 654, 94, 26), "right_lift", "orange", rectangle(1072, 416, 94, 26), speed=0.035),
            MovingSolid(rectangle(428, 78, 344, 26), "upper_bridge", "yellow", rectangle(428, 300, 344, 26), speed=0.05),
        ],
    )


# Nivel 4: dos elevadores junto a los muros forman el recorrido final
def level_four():
    return Level(
        4,
        "temple",
        (550, 624),
        (602, 624),
        rectangle(958, 70, 66, 96),
        rectangle(1034, 70, 66, 96),
        platforms=borders() + [
            platform(26, 680, 292),
            platform(398, 680, 402),
            platform(878, 680, 296),
            platform(700, 478, 374),
            platform(126, 478, 474),
            platform(126, 276, 392),
            platform(630, 276, 434),
            platform(838, 166, 336),
        ],
        hazards=[
            Hazard(rectangle(318, 680, 80, 40), "water"),
            Hazard(rectangle(800, 680, 78, 40), "fire"),
            Hazard(rectangle(600, 478, 100, 26), "poison"),
            Hazard(rectangle(518, 276, 112, 26), "water"),
        ],
        diamonds=diamonds([
            (212, 634, "water"),
            (694, 634, "fire"),
            (920, 634, "water"),
            (780, 432, "water"),
            (284, 432, "fire"),
            (486, 432, "water"),
            (210, 230, "water"),
            (712, 230, "fire"),
            (1080, 122, "water"),
        ]),
        switches=[
            Switch(rectangle(676, 662, 60, 18), "right_lift", "orange"),
            Switch(rectangle(928, 460, 60, 18), "right_lift", "orange"),
            Switch(rectangle(246, 460, 60, 18), "left_lift", "green"),
            Switch(rectangle(208, 258, 60, 18), "left_lift", "green"),
        ],
        movers=[
            MovingSolid(rectangle(1076, 654, 92, 26), "right_lift", "orange", rectangle(1076, 478, 92, 26), speed=0.035),
            MovingSolid(rectangle(32, 452, 94, 26), "left_lift", "green", rectangle(32, 276, 94, 26), speed=0.035),
        ],
    )
