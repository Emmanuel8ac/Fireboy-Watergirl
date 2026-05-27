from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor


class Player:
    def __init__(
        self,
        name: str,
        kind: str,
        x: float,
        y: float,
        sx: float,
        sy: float,
        vx: float = 0.0,
        vy: float = 0.0,
        w: float = 42.0,
        h: float = 58.0,
        on_ground: bool = False,
        facing: int = 1,
        anim: int = 0,
        cooldown: int = 0,
    ):
        self.name = name
        self.kind = kind
        self.x = x
        self.y = y
        self.sx = sx
        self.sy = sy
        self.vx = vx
        self.vy = vy
        self.w = w
        self.h = h
        self.on_ground = on_ground
        self.facing = facing
        self.anim = anim
        self.cooldown = cooldown

    @property
    def rect(self):
        return QRectF(self.x, self.y, self.w, self.h)

    def respawn(self):
        self.x = self.sx
        self.y = self.sy
        self.vx = 0
        self.vy = 0
        self.cooldown = 45


class Diamond:
    def __init__(self, rect: QRectF, owner: str, collected: bool = False):
        self.rect = rect
        self.owner = owner
        self.collected = collected


class Hazard:
    def __init__(self, rect: QRectF, kind: str):
        self.rect = rect
        self.kind = kind


class Switch:
    def __init__(self, rect: QRectF, target: str, color: str, active: bool = False):
        self.rect = rect
        self.target = target
        self.color = color
        self.active = active


class Lever:
    def __init__(self, rect: QRectF, target: str, color: str, active: bool = False):
        self.rect = rect
        self.target = target
        self.color = color
        self.active = active


class MovingSolid:
    def __init__(
        self,
        rect: QRectF,
        target: str,
        color: str,
        to_rect: QRectF,
        progress: float = 0.0,
        speed: float = 0.045,
        vanish: bool = False,
    ):
        self.rect = rect
        self.target = target
        self.color = color
        self.to_rect = to_rect
        self.progress = progress
        self.speed = speed
        self.vanish = vanish


class Portal:
    def __init__(self, rect: QRectF, pair: int, color: str):
        self.rect = rect
        self.pair = pair
        self.color = color


class Box:
    def __init__(self, rect: QRectF, vx: float = 0.0, vy: float = 0.0):
        self.rect = rect
        self.vx = vx
        self.vy = vy


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: int,
        color: QColor,
        size: float,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.color = color
        self.size = size


class Level:
    def __init__(
        self,
        n: int,
        theme: str,
        fire_spawn: tuple,
        water_spawn: tuple,
        fire_door: QRectF,
        water_door: QRectF,
        platforms=None,
        hazards=None,
        diamonds=None,
        switches=None,
        levers=None,
        movers=None,
        portals=None,
        boxes=None,
    ):
        self.n = n
        self.theme = theme
        self.fire_spawn = fire_spawn
        self.water_spawn = water_spawn
        self.fire_door = fire_door
        self.water_door = water_door
        self.platforms = platforms if platforms is not None else []
        self.hazards = hazards if hazards is not None else []
        self.diamonds = diamonds if diamonds is not None else []
        self.switches = switches if switches is not None else []
        self.levers = levers if levers is not None else []
        self.movers = movers if movers is not None else []
        self.portals = portals if portals is not None else []
        self.boxes = boxes if boxes is not None else []
