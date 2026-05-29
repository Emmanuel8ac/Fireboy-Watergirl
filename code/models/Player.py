from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor


# Datos y movimiento de un personaje
class Player:
    # Inicializa los datos necesarios
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

    # Devuelve el área de colisión del elemento
    @property
    def rect(self):
        return QRectF(self.x, self.y, self.w, self.h)

    # Regresa al personaje al inicio
    def respawn(self):
        self.x = self.sx
        self.y = self.sy
        self.vx = 0
        self.vy = 0
        self.cooldown = 45


# Diamantes que suman puntos
class Diamond:
    # Inicializa los datos necesarios
    def __init__(self, rect: QRectF, owner: str, collected: bool = False):
        self.rect = rect
        self.owner = owner
        self.collected = collected


# Líquidos peligrosos del mapa
class Hazard:
    # Inicializa los datos necesarios
    def __init__(self, rect: QRectF, kind: str):
        self.rect = rect
        self.kind = kind


# Placas que activan mecanismos.
class Switch:
    # Inicializa los datos necesarios.
    def __init__(self, rect: QRectF, target: str, color: str, active: bool = False):
        self.rect = rect
        self.target = target
        self.color = color
        self.active = active


# Palancas que activan mecanismos
class Lever:
    # Inicializa los datos necesarios
    def __init__(self, rect: QRectF, target: str, color: str, active: bool = False):
        self.rect = rect
        self.target = target
        self.color = color
        self.active = active


# Barreras y plataformas móviles
class MovingSolid:
    # Inicializa los datos necesarios
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


# Portales conectados por pareja
class Portal:
    # Inicializa los datos necesarios
    def __init__(self, rect: QRectF, pair: int, color: str):
        self.rect = rect
        self.pair = pair
        self.color = color


# Cajas que pueden empujarse
class Box:
    # Inicializa los datos necesarios
    def __init__(self, rect: QRectF, vx: float = 0.0, vy: float = 0.0):
        self.rect = rect
        self.vx = vx
        self.vy = vy


# Partículas visuales de los personajes
class Particle:
    # Inicializa los datos necesarios
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


# Elementos que forman un nivel
class Level:
    # Inicializa los datos necesarios
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
