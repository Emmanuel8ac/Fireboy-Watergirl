from dataclasses import dataclass, field
from pathlib import Path
import math
import random

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap, QImage, QPolygonF
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox

from config import GAME_DURATION_SECONDS, CHARACTERS_DIR
from logic.game_manager import GameManager
from logic.audio_manager import AudioManager
from logic.network_manager import NetworkManager


def R(x, y, w, h):
    return QRectF(float(x), float(y), float(w), float(h))


@dataclass
class Player:
    name: str
    kind: str
    x: float
    y: float
    sx: float
    sy: float
    vx: float = 0.0
    vy: float = 0.0
    w: float = 42.0
    h: float = 58.0
    on_ground: bool = False
    facing: int = 1
    anim: int = 0
    cooldown: int = 0

    @property
    def rect(self):
        return QRectF(self.x, self.y, self.w, self.h)

    def respawn(self):
        self.x, self.y = self.sx, self.sy
        self.vx = self.vy = 0
        self.cooldown = 45


@dataclass
class Diamond:
    rect: QRectF
    owner: str
    collected: bool = False


@dataclass
class Hazard:
    rect: QRectF
    kind: str  # fire, water, poison


@dataclass
class Switch:
    rect: QRectF
    target: str
    color: str
    active: bool = False


@dataclass
class Lever:
    rect: QRectF
    target: str
    color: str
    active: bool = False


@dataclass
class MovingSolid:
    rect: QRectF
    target: str
    color: str
    to_rect: QRectF
    progress: float = 0.0
    speed: float = 0.045
    vanish: bool = False


@dataclass
class Portal:
    rect: QRectF
    pair: int
    color: str


@dataclass
class Box:
    rect: QRectF
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: int
    color: QColor
    size: float


@dataclass
class Level:
    n: int
    theme: str
    fire_spawn: tuple
    water_spawn: tuple
    fire_door: QRectF
    water_door: QRectF
    platforms: list[QRectF] = field(default_factory=list)
    hazards: list[Hazard] = field(default_factory=list)
    diamonds: list[Diamond] = field(default_factory=list)
    switches: list[Switch] = field(default_factory=list)
    levers: list[Lever] = field(default_factory=list)
    movers: list[MovingSolid] = field(default_factory=list)
    portals: list[Portal] = field(default_factory=list)
    boxes: list[Box] = field(default_factory=list)


class GameCanvas(QWidget):
    WORLD_W = 1200
    WORLD_H = 720
    GRAVITY = 0.72
    MOVE = 4.8
    JUMP = -14.2
    MAX_FALL = 17

    def __init__(self, game_mgr: GameManager, audio: AudioManager, network: NetworkManager = None, parent=None):
        super().__init__(parent)
        self._gm = game_mgr
        self._audio = audio
        self._network = network
        self.remote_keys = set()
        if self._network is not None:
            self._network.remote_input_received.connect(self._on_remote_input)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(610)
        self.keys = set()
        self.level_number = 1
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._frame)
        self.frame = 0
        self.particles = []
        self.sound_button_rect = QRectF()
        self._load_sprites()
        self.reset_level()

    def _on_remote_input(self, keys):
        self.remote_keys = set(keys)

    @staticmethod
    def _key_names(keys):
        table = {
            Qt.Key_A: "A", Qt.Key_D: "D", Qt.Key_W: "W", Qt.Key_E: "E",
            Qt.Key_Left: "LEFT", Qt.Key_Right: "RIGHT", Qt.Key_Up: "UP",
            Qt.Key_Down: "DOWN", Qt.Key_Return: "ENTER", Qt.Key_Enter: "ENTER",
        }
        return {name for key, name in table.items() if key in keys}

    def _load_frames(self, folder: Path):
        frames = []
        if folder.exists():
            for p in sorted(folder.glob("*.png"), key=lambda p: int(p.stem) if p.stem.isdigit() else 999):
                px = QPixmap(str(p))
                if not px.isNull():
                    frames.append(self._trim(px))
        return frames

    def _trim(self, pix: QPixmap):
        img = pix.toImage().convertToFormat(QImage.Format_ARGB32)
        minx, miny, maxx, maxy = img.width(), img.height(), -1, -1
        for y in range(img.height()):
            for x in range(img.width()):
                if img.pixelColor(x, y).alpha() > 12:
                    minx, miny = min(minx, x), min(miny, y)
                    maxx, maxy = max(maxx, x), max(maxy, y)
        if maxx < minx or maxy < miny:
            return pix
        return QPixmap.fromImage(img.copy(minx, miny, maxx - minx + 1, maxy - miny + 1))

    def _load_sprites(self):
        c = Path(CHARACTERS_DIR)
        self.fire_frames = self._load_frames(c / "fireboy" / "FireBoy_running")
        self.water_frames = self._load_frames(c / "watergirl" / "WaterGirl_running")
        self.fire_idle = self.fire_frames[0] if self.fire_frames else QPixmap()
        self.water_idle = self.water_frames[0] if self.water_frames else QPixmap()

    def _base(self):
        return [R(0, 0, 30, 720), R(1170, 0, 30, 720), R(0, 690, 1200, 30), R(0, 0, 1200, 24)]

    def _diamonds_line(self, points):
        return [Diamond(R(x, y, 26, 31), owner) for x, y, owner in points]

    def _level(self):
        b = self._base()
        if self.level_number == 1:
            return Level(1, "temple", (76, 624), (136, 624), R(1070, 78, 52, 75), R(1008, 78, 52, 75),
                platforms=b + [R(40,650,260,24),R(345,650,240,24),R(640,650,260,24),R(935,650,220,24), R(40,540,210,24),R(310,520,250,24),R(650,520,230,24),R(950,505,200,24), R(80,410,190,24),R(335,395,240,24),R(650,390,245,24),R(940,370,205,24), R(35,285,230,24),R(350,275,260,24),R(675,270,210,24),R(980,240,170,24), R(70,155,240,24),R(390,150,220,24),R(705,145,180,24),R(990,155,150,24)],
                hazards=[Hazard(R(682,630,96,18),"fire"),Hazard(R(830,630,96,18),"water"),Hazard(R(490,502,80,16),"poison")],
                diamonds=self._diamonds_line([(155,610,"fire"),(410,610,"water"),(735,485,"fire"),(980,472,"water"),(425,245,"fire"),(780,232,"water"),(165,122,"water"),(940,205,"fire")]),
                switches=[Switch(R(220,635,62,15),"lift","green"),Switch(R(1010,490,62,15),"door","orange")],
                levers=[Lever(R(560,610,48,35),"bridge","yellow")],
                movers=[MovingSolid(R(585,650,120,20),"bridge","yellow",R(585,565,120,20)), MovingSolid(R(885,145,22,95),"lift","green",R(885,60,22,95)), MovingSolid(R(1095,240,24,130),"door","orange",R(1095,115,24,130))],
                portals=[Portal(R(42,596,40,40),1,"purple"),Portal(R(1110,110,40,40),1,"purple")], boxes=[Box(R(720,216,45,45))])
        if self.level_number == 2:
            return Level(2, "dark", (75, 620), (75, 540), R(1075, 90, 50, 72), R(1015, 90, 50, 72),
                platforms=b+[R(40,650,310,24),R(450,650,300,24),R(835,650,320,24), R(60,560,220,24),R(355,540,310,24),R(760,540,360,24), R(40,430,330,24),R(455,430,280,24),R(825,420,325,24), R(155,310,270,24),R(520,310,260,24),R(880,300,250,24), R(40,190,215,24),R(340,175,270,24),R(700,180,430,24)],
                hazards=[Hazard(R(555,632,90,17),"fire"),Hazard(R(705,632,90,17),"water"),Hazard(R(800,525,90,17),"poison")],
                diamonds=self._diamonds_line([(120,150,"water"),(380,145,"fire"),(710,150,"water"),(260,390,"fire"),(540,390,"water"),(1010,260,"fire"),(875,600,"water")]),
                switches=[Switch(R(310,415,60,15),"purple","purple"),Switch(R(1020,405,60,15),"purple","purple")],
                levers=[Lever(R(315,610,50,35),"gate","yellow")],
                movers=[MovingSolid(R(720,540,120,20),"gate","yellow",R(720,460,120,20)),MovingSolid(R(1090,300,24,120),"purple","purple",R(1090,205,24,120))], boxes=[Box(R(600,265,44,44))])
        if self.level_number == 3:
            return Level(3,"temple",(80,625),(135,625),R(1045,80,52,75),R(985,80,52,75),
                platforms=b+[R(40,650,260,24),R(340,650,200,24),R(610,650,240,24),R(920,650,230,24),R(50,535,240,24),R(360,525,210,24),R(650,500,230,24),R(930,485,230,24),R(80,405,250,24),R(410,385,260,24),R(740,365,220,24),R(1000,330,150,24),R(40,260,230,24),R(330,245,245,24),R(650,230,260,24),R(970,155,180,24),R(720,115,170,24)],
                hazards=[Hazard(R(705,480,115,17),"fire"),Hazard(R(780,345,105,17),"water"),Hazard(R(605,213,80,17),"poison"),Hazard(R(875,632,85,17),"poison")],
                diamonds=self._diamonds_line([(90,220,"water"),(355,215,"fire"),(500,485,"water"),(930,445,"water"),(915,315,"fire"),(1045,610,"fire"),(380,610,"water")]),
                switches=[Switch(R(60,520,62,15),"green","green"),Switch(R(1045,470,62,15),"orange","orange")],
                levers=[Lever(R(410,610,50,35),"purple","purple")],
                movers=[MovingSolid(R(530,650,22,95),"purple","purple",R(530,535,22,95)),MovingSolid(R(1085,485,22,95),"orange","orange",R(1085,395,22,95)),MovingSolid(R(725,230,120,20),"green","green",R(725,175,120,20))],
                portals=[Portal(R(435,600,40,40),1,"yellow"),Portal(R(815,72,40,40),1,"yellow")])
        if self.level_number == 4:
            return Level(4,"temple",(70,365),(130,365),R(1030,80,52,75),R(970,80,52,75),
                platforms=b+[R(40,420,210,24),R(250,505,320,24),R(610,610,330,24),R(975,610,180,24),R(40,610,170,24),R(210,650,250,24),R(40,280,480,24),R(570,280,420,24),R(1020,250,140,24),R(80,175,260,24),R(470,160,230,24),R(755,140,360,24),R(580,430,330,24)],
                hazards=[Hazard(R(540,400,300,17),"water"),Hazard(R(830,632,80,17),"water")],
                diamonds=self._diamonds_line([(275,475,"water"),(840,430,"fire"),(500,575,"water"),(1040,580,"fire"),(1060,100,"water"),(130,582,"fire")]),
                switches=[Switch(R(990,235,62,15),"orange","orange"),Switch(R(700,595,62,15),"green","green")],
                levers=[Lever(R(690,590,50,35),"bridge","green")],
                movers=[MovingSolid(R(715,330,160,20),"bridge","white",R(660,250,160,20)),MovingSolid(R(120,485,100,20),"orange","orange",R(120,420,100,20))],
                boxes=[Box(R(190,560,45,45))],portals=[Portal(R(42,625,40,40),1,"white"),Portal(R(1100,340,40,40),1,"white")])
        if self.level_number == 5:
            return Level(5,"temple",(850,625),(360,625),R(1005,420,52,75),R(680,615,52,75),
                platforms=b+[R(40,650,500,24),R(600,650,550,24),R(60,520,500,24),R(850,455,250,24),R(760,560,180,24),R(1020,580,130,24),R(420,355,430,24),R(820,275,330,24),R(40,270,340,24),R(180,175,330,24),R(550,135,310,24),R(920,165,230,24)],
                hazards=[Hazard(R(785,632,85,17),"poison"),Hazard(R(610,334,85,17),"water")],
                diamonds=self._diamonds_line([(92,592,"water"),(320,492,"fire"),(690,492,"water"),(710,105,"water"),(1070,355,"fire"),(660,400,"water"),(1080,130,"fire")]),
                switches=[Switch(R(500,505,62,15),"purple","purple"),Switch(R(1070,565,62,15),"purple","purple")],
                levers=[Lever(R(825,420,50,35),"cyan","cyan")],
                movers=[MovingSolid(R(960,275,22,95),"purple","purple",R(960,180,22,95)),MovingSolid(R(150,130,22,95),"cyan","cyan",R(150,240,22,95))],
                portals=[Portal(R(1070,170,40,40),1,"green"),Portal(R(1070,610,40,40),1,"green"),Portal(R(40,590,40,40),2,"white"),Portal(R(40,650,40,40),2,"white")])
        return Level(6,"jungle",(82,625),(142,625),R(1055,80,52,75),R(995,80,52,75),
            platforms=b+[R(40,650,260,24),R(365,650,260,24),R(690,650,240,24),R(1000,650,150,24),R(35,540,290,24),R(425,520,260,24),R(780,505,250,24),R(60,410,240,24),R(365,390,270,24),R(690,370,240,24),R(1020,345,130,24),R(80,275,250,24),R(410,250,260,24),R(720,220,230,24),R(990,170,165,24)],
            hazards=[Hazard(R(150,390,90,17),"fire"),Hazard(R(520,632,110,17),"water"),Hazard(R(820,492,90,17),"fire"),Hazard(R(1015,330,80,17),"water")],
            diamonds=self._diamonds_line([(115,610,"water"),(345,610,"fire"),(715,610,"water"),(990,312,"fire"),(855,190,"water"),(520,215,"fire"),(250,245,"water")]),
            switches=[Switch(R(520,635,62,15),"yellow","yellow"),Switch(R(1010,635,62,15),"orange","orange")],
            levers=[Lever(R(90,370,50,35),"bridge","cyan"),Lever(R(1030,600,50,35),"door","orange")],
            movers=[MovingSolid(R(600,520,140,20),"bridge","cyan",R(600,430,140,20)),MovingSolid(R(1080,170,22,120),"door","orange",R(1080,65,22,120)),MovingSolid(R(760,650,130,20),"yellow","yellow",R(760,575,130,20))],
            portals=[Portal(R(42,595,40,40),1,"green"),Portal(R(1110,120,40,40),1,"green")])

    def set_level(self, level_number: int):
        self.level_number = max(1, min(6, int(level_number)))
        self.reset_level()

    def reset_level(self):
        self.keys.clear()
        self.remote_keys.clear()
        self.data = self._level()
        fx, fy = self.data.fire_spawn
        wx, wy = self.data.water_spawn
        self.fire = Player("Fireboy", "fire", fx, fy, fx, fy)
        self.water = Player("Watergirl", "water", wx, wy, wx, wy)
        self.platforms = [QRectF(p) for p in self.data.platforms]
        self.hazards = [Hazard(QRectF(h.rect), h.kind) for h in self.data.hazards]
        self.diamonds = [Diamond(QRectF(d.rect), d.owner, False) for d in self.data.diamonds]
        self.switches = [Switch(QRectF(s.rect), s.target, s.color, False) for s in self.data.switches]
        self.levers = [Lever(QRectF(l.rect), l.target, l.color, False) for l in self.data.levers]
        self.movers = [MovingSolid(QRectF(m.rect), m.target, m.color, QRectF(m.to_rect), 0.0, m.speed, m.vanish) for m in self.data.movers]
        self.portals = [Portal(QRectF(p.rect), p.pair, p.color) for p in self.data.portals]
        self.boxes = [Box(QRectF(b.rect), 0, 0) for b in self.data.boxes]
        self._last_lever = False
        self.frame = 0
        self.particles.clear()
        self.update()

    def start(self):
        self.setFocus()
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.keys.clear()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            self.keys.add(event.key())
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.keys.discard(event.key())
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if self.sound_button_rect.contains(event.position()):
            enabled = self._audio.toggle_audio()
            if enabled:
                self._audio.play_music("game")
            self.update()
            return
        super().mousePressEvent(event)

    def _scale(self):
        return self.width() / self.WORLD_W, self.height() / self.WORLD_H

    def _r(self, rect):
        sx, sy = self._scale()
        return QRectF(rect.x()*sx, rect.y()*sy, rect.width()*sx, rect.height()*sy)

    def _wr_at(self, p):
        return QPointF(p.x / self._scale()[0], p.y / self._scale()[1])

    def _active_targets(self):
        active = set()
        for s in self.switches:
            s.active = self.fire.rect.intersects(s.rect) or self.water.rect.intersects(s.rect) or any(b.rect.intersects(s.rect) for b in self.boxes)
            if s.active:
                active.add(s.target)
        for l in self.levers:
            if l.active:
                active.add(l.target)
        return active

    def _mover_rect(self, m):
        t = max(0.0, min(1.0, m.progress))
        return R(m.rect.x()+(m.to_rect.x()-m.rect.x())*t, m.rect.y()+(m.to_rect.y()-m.rect.y())*t, m.rect.width(), m.rect.height())

    def _solid_movers(self):
        return [self._mover_rect(m) for m in self.movers if not (m.vanish and m.progress > .95)]

    def _solids(self):
        return self.platforms + self._solid_movers() + [b.rect for b in self.boxes]

    def _frame(self):
        if not self._gm.is_running:
            return
        self.frame += 1
        if self._network is not None and self._network.is_online():
            self._network.send_input(self._key_names(self.keys))
        self._input()
        self._move_movers()
        self._update_boxes()
        self._update_player(self.fire)
        self._update_player(self.water)
        self._levers()
        self._diamonds()
        self._hazards()
        self._portals()
        self._doors()
        self._particles()
        self.update()

    def _input(self):
        local = self._key_names(self.keys)
        remote = set(self.remote_keys)
        if self._network is not None and self._network.is_host() and self._network.is_connected():
            fk, wk = local, remote
        elif self._network is not None and self._network.is_client() and self._network.is_connected():
            fk, wk = remote, local
        else:
            fk = wk = local
        self.fire.vx = (-self.MOVE if "A" in fk else 0) + (self.MOVE if "D" in fk else 0)
        self.water.vx = (-self.MOVE if "LEFT" in wk else 0) + (self.MOVE if "RIGHT" in wk else 0)
        if self.fire.vx: self.fire.facing = 1 if self.fire.vx > 0 else -1
        if self.water.vx: self.water.facing = 1 if self.water.vx > 0 else -1
        if "W" in fk and self.fire.on_ground:
            self.fire.vy = self.JUMP; self.fire.on_ground = False; self._audio.play_effect("jump")
        if "UP" in wk and self.water.on_ground:
            self.water.vy = self.JUMP; self.water.on_ground = False; self._audio.play_effect("jump")

    def _move_movers(self):
        active = self._active_targets()
        for m in self.movers:
            before = self._mover_rect(m)
            target = 1.0 if m.target in active else 0.0
            if m.progress < target:
                m.progress = min(target, m.progress + m.speed)
            elif m.progress > target:
                m.progress = max(target, m.progress - m.speed)
            after = self._mover_rect(m)
            dx, dy = after.x()-before.x(), after.y()-before.y()
            if abs(dx)+abs(dy) > 0:
                for p in (self.fire, self.water):
                    if abs(p.rect.bottom()-before.top()) <= 6 and p.rect.right() > before.left()+3 and p.rect.left() < before.right()-3:
                        p.x += dx; p.y += dy

    def _update_boxes(self):
        solids = self.platforms + self._solid_movers()
        for b in self.boxes:
            b.vy = min(self.MAX_FALL, b.vy + self.GRAVITY)
            b.rect.translate(0, b.vy)
            for s in solids:
                if b.rect.intersects(s):
                    if b.vy > 0: b.rect.moveTop(s.top()-b.rect.height())
                    else: b.rect.moveTop(s.bottom())
                    b.vy = 0

    def _push_boxes(self, p):
        if abs(p.vx) < .1: return
        solids = self.platforms + self._solid_movers()
        for b in self.boxes:
            if p.rect.intersects(b.rect):
                old = QRectF(b.rect)
                b.rect.translate(p.vx, 0)
                if any(b.rect.intersects(s) for s in solids):
                    b.rect = old
                    p.x = b.rect.left()-p.w if p.vx > 0 else b.rect.right()

    def _update_player(self, p):
        if p.cooldown > 0: p.cooldown -= 1
        p.x += p.vx
        self._push_boxes(p)
        for s in self._solids():
            if p.rect.intersects(s):
                if p.vx > 0: p.x = s.left()-p.w
                elif p.vx < 0: p.x = s.right()
        p.vy = min(self.MAX_FALL, p.vy + self.GRAVITY)
        p.y += p.vy
        p.on_ground = False
        for s in self._solids():
            if p.rect.intersects(s):
                if p.vy > 0:
                    p.y = s.top()-p.h; p.vy = 0; p.on_ground = True
                elif p.vy < 0:
                    p.y = s.bottom(); p.vy = 0
        if p.vx: p.anim += 1
        if p.y > self.WORLD_H + 120: p.respawn()

    def _levers(self):
        pressed = bool({"E", "DOWN", "ENTER"} & (self._key_names(self.keys) | self.remote_keys))
        if pressed and not self._last_lever:
            for l in self.levers:
                if self.fire.rect.adjusted(-18,-18,18,18).intersects(l.rect) or self.water.rect.adjusted(-18,-18,18,18).intersects(l.rect):
                    l.active = not l.active
                    self._audio.play_effect("click")
        self._last_lever = pressed

    def _diamonds(self):
        for d in self.diamonds:
            if d.collected: continue
            if d.owner == "fire" and self.fire.rect.intersects(d.rect):
                d.collected = True; self._gm.add_point(1, 10); self._audio.play_effect("point")
            if d.owner == "water" and self.water.rect.intersects(d.rect):
                d.collected = True; self._gm.add_point(2, 10); self._audio.play_effect("point")

    def _hazards(self):
        for h in self.hazards:
            if self.fire.rect.intersects(h.rect) and h.kind in ("water", "poison"):
                self._burst(self.fire.rect.center(), QColor("#ff6b12")); self.fire.respawn(); self._audio.play_effect("over")
            if self.water.rect.intersects(h.rect) and h.kind in ("fire", "poison"):
                self._burst(self.water.rect.center(), QColor("#35caff")); self.water.respawn(); self._audio.play_effect("over")

    def _portals(self):
        for pl in (self.fire, self.water):
            if pl.cooldown > 0: continue
            for po in self.portals:
                if pl.rect.intersects(po.rect):
                    other = next((x for x in self.portals if x.pair == po.pair and x is not po), None)
                    if other:
                        pl.x = other.rect.center().x() - pl.w/2
                        pl.y = other.rect.top() - pl.h - 2
                        pl.vx = pl.vy = 0
                        pl.cooldown = 60
                        self._audio.play_effect("click")
                        self._burst(other.rect.center(), QColor("#b03cff"))
                    break

    def _doors(self):
        if all(d.collected for d in self.diamonds) and self.fire.rect.intersects(self.data.fire_door) and self.water.rect.intersects(self.data.water_door):
            self._gm.finish()

    def _particles(self):
        if self.frame % 3 == 0:
            self._add_particle(self.fire.x+self.fire.w/2, self.fire.y+self.fire.h-4, QColor("#ff6d17"), True)
            self._add_particle(self.water.x+self.water.w/2, self.water.y+self.water.h-4, QColor("#39c9ff"), False)
        alive=[]
        for p in self.particles:
            p.life -= 1; p.x += p.vx; p.y += p.vy; p.vy += .04; p.size *= .96
            if p.life > 0 and p.size > .6: alive.append(p)
        self.particles = alive[-180:]

    def _add_particle(self, x, y, color, fire=True):
        self.particles.append(Particle(x+random.uniform(-5,5), y+random.uniform(-3,3), random.uniform(-.6,.6), random.uniform(-1.4,-.2) if fire else random.uniform(-.45,.55), random.randint(14,26), color, random.uniform(2.5,6)))

    def _burst(self, c, color):
        for _ in range(20):
            a = random.random()*math.tau; s=random.uniform(1,4)
            self.particles.append(Particle(c.x(), c.y(), math.cos(a)*s, math.sin(a)*s, random.randint(16,30), color, random.uniform(3,8)))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self._draw_background(p)
        for plat in self.platforms: self._draw_platform(p, plat)
        for m in self.movers: self._draw_mover(p, m)
        for h in self.hazards: self._draw_hazard(p, h)
        for sw in self.switches: self._draw_switch(p, sw)
        for lv in self.levers: self._draw_lever(p, lv)
        for po in self.portals: self._draw_portal(p, po)
        for b in self.boxes: self._draw_box(p, b.rect)
        self._draw_doors(p)
        for d in self.diamonds:
            if not d.collected: self._draw_diamond(p, d.rect, QColor("#ff2222") if d.owner=="fire" else QColor("#22d7ff"))
        self._draw_particles(p)
        self._draw_player(p, self.fire, self.fire_frames, self.fire_idle, QColor("#ff5b1a"))
        self._draw_player(p, self.water, self.water_frames, self.water_idle, QColor("#35caff"))
        self._draw_timer(p)
        self._draw_sound(p)
        self._draw_help(p)

    def _draw_background(self, p):
        if self.data.theme == "jungle":
            top, bottom = QColor("#20351d"), QColor("#364323")
        elif self.data.theme == "dark":
            top, bottom = QColor("#211a1c"), QColor("#322423")
        else:
            top, bottom = QColor("#858585"), QColor("#666666")
        p.fillRect(self.rect(), bottom)
        sx, sy = self._scale()
        p.setPen(QPen(QColor(0,0,0,45), 1))
        for x in range(0, self.WORLD_W, 85): p.drawLine(int(x*sx), 0, int(x*sx), self.height())
        for y in range(0, self.WORLD_H, 58): p.drawLine(0, int(y*sy), self.width(), int(y*sy))
        p.fillRect(0,0,self.width(),self.height(),QColor(top.red(), top.green(), top.blue(), 55))

    def _draw_platform(self, p, rect):
        r=self._r(rect)
        if r.width()<4 or r.height()<4: return
        if self.data.theme == "jungle": fill, edge = QColor("#88815b"), QColor("#313722")
        elif self.data.theme == "dark": fill, edge = QColor("#5c3d34"), QColor("#201614")
        else: fill, edge = QColor("#1e2021"), QColor("#070707")
        p.setBrush(fill); p.setPen(QPen(edge,3)); p.drawRoundedRect(r,5,5)
        p.setPen(QPen(QColor(255,255,255,35),1))
        x=int(r.left())
        while x<r.right():
            p.drawLine(x, int(r.top()+4), min(int(r.right()), x+34), int(r.top()+4)); x+=34

    def _draw_mover(self, p, m):
        r = self._mover_rect(m)
        rr = self._r(r)
        c={"yellow":"#ffd930","purple":"#bf36ff","orange":"#ff8322","cyan":"#52dcff","green":"#41f047","white":"#eeeeee"}.get(m.color,"#ffd930")
        p.setBrush(QColor(c)); p.setPen(QPen(QColor("#111"),3)); p.drawRoundedRect(rr,4,4)

    def _draw_hazard(self, p, h):
        r=self._r(h.rect); c={"fire":"#ff5c00","water":"#41c8ff","poison":"#39e340"}[h.kind]
        p.setBrush(QColor(c)); p.setPen(QPen(QColor("#111"),2)); p.drawRoundedRect(r,8,8)
        p.setPen(QPen(QColor(255,255,255,145),1))
        for x in range(int(r.left()), int(r.right()), 20): p.drawArc(x, int(r.top()-6), 24, 18, 0, 180*16)

    def _draw_switch(self,p,sw):
        r=self._r(sw.rect); c={"yellow":"#ffd930","purple":"#bf36ff","orange":"#ff8322","cyan":"#52dcff","green":"#41f047","white":"#eee"}.get(sw.color,"#ffd930")
        p.setBrush(QColor(c if sw.active else "#695a45")); p.setPen(QPen(QColor("#111"),2)); p.drawRoundedRect(r,9,9)

    def _draw_lever(self,p,lv):
        r=self._r(lv.rect)
        p.setBrush(QColor("#c9a32b")); p.setPen(QPen(QColor("#111"),2)); p.drawRoundedRect(r.adjusted(4,r.height()*0.65,-4,0),6,6)
        base=QPointF(r.center().x(), r.bottom()-r.height()*.25); tip=QPointF(r.center().x()+(r.width()*.28 if lv.active else -r.width()*.25), r.top()+5)
        p.setPen(QPen(QColor("#ffe255"),5)); p.drawLine(base,tip); p.setBrush(QColor("#f5e43e")); p.drawEllipse(tip,6,6)

    def _draw_portal(self,p,po):
        r=self._r(po.rect); c={"purple":"#c545ff","green":"#46ff56","white":"#fff","yellow":"#ffe43b"}.get(po.color,"#c545ff")
        p.setBrush(QColor(255,255,255,30)); p.setPen(QPen(QColor(c),5)); p.drawEllipse(r)

    def _draw_box(self,p,rect):
        r=self._r(rect); p.setBrush(QColor("#cfcfcf")); p.setPen(QPen(QColor("#d8b723"),4)); p.drawRoundedRect(r,4,4); p.setPen(QPen(QColor("#777"),1)); p.drawLine(r.topLeft(), r.bottomRight()); p.drawLine(r.topRight(), r.bottomLeft())

    def _draw_doors(self,p):
        self._draw_door(p,self.data.fire_door,QColor("#ff2d18"),"♂")
        self._draw_door(p,self.data.water_door,QColor("#25d3ff"),"♀")

    def _draw_door(self,p,rect,color,symbol):
        r=self._r(rect); p.setBrush(QColor(50,50,50,210)); p.setPen(QPen(QColor("#111"),4)); p.drawRoundedRect(r,5,5)
        p.setPen(QPen(color,3)); p.setFont(QFont("Arial", int(r.height()*0.45), QFont.Bold)); p.drawText(r,Qt.AlignCenter,symbol)

    def _draw_diamond(self,p,rect,color):
        r=self._r(rect); glow=QColor(color); glow.setAlpha(60); p.setBrush(glow); p.setPen(Qt.NoPen); p.drawEllipse(r.adjusted(-8,-8,8,8))
        cx,cy=r.center().x(),r.center().y(); poly=QPolygonF([QPointF(cx,r.top()),QPointF(r.right(),cy),QPointF(cx,r.bottom()),QPointF(r.left(),cy)])
        p.setBrush(color); p.setPen(QPen(QColor("#111"),2)); p.drawPolygon(poly)

    def _draw_player(self,p,pl,frames,idle,fallback):
        r=self._r(pl.rect); pix=idle
        if frames and abs(pl.vx)>.1: pix=frames[(pl.anim//4)%len(frames)]
        if not pix.isNull():
            if pl.facing<0:
                p.save(); p.translate(r.center()); p.scale(-1,1); p.drawPixmap(QRectF(-r.width()/2,-r.height()/2,r.width(),r.height()).toRect(),pix); p.restore()
            else: p.drawPixmap(r.toRect(),pix)
        else:
            p.setBrush(fallback); p.setPen(QPen(QColor("white"),2)); p.drawRoundedRect(r,12,12)

    def _draw_particles(self,p):
        p.setPen(Qt.NoPen); sx,sy=self._scale()
        for q in self.particles:
            c=QColor(q.color); c.setAlpha(max(25,min(170,q.life*8))); p.setBrush(c); p.drawEllipse(QPointF(q.x*sx,q.y*sy),q.size*sx,q.size*sy)

    def _draw_timer(self,p):
        w,h=150,52; x=(self.width()-w)/2; y=4
        p.setBrush(QColor(45,45,45,235)); p.setPen(QPen(QColor("#111"),5)); p.drawRoundedRect(QRectF(x,y,w,h),8,8)
        p.setBrush(QColor(15,15,15,235)); p.setPen(QPen(QColor("#777"),2)); p.drawRoundedRect(QRectF(x+16,y+7,w-32,h-14),4,4)
        sec=max(0,int(self._gm.time_left)); txt=f"{sec//60:02d}:{sec%60:02d}"
        p.setFont(QFont("Arial",27,QFont.Bold)); p.setPen(QPen(QColor("#000"),4)); p.drawText(QRectF(x,y+2,w,h),Qt.AlignCenter,txt); p.setPen(QPen(QColor("#ffd52e"),1)); p.drawText(QRectF(x,y,w,h),Qt.AlignCenter,txt)

    def _draw_sound(self,p):
        self.sound_button_rect=QRectF(self.width()-62,12,44,44)
        r=self.sound_button_rect; p.setBrush(QColor(0,0,0,90)); p.setPen(QPen(QColor("#ffd72b"),2)); p.drawEllipse(r)
        p.setFont(QFont("Arial",23,QFont.Bold)); p.setPen(QColor("#ffd72b")); p.drawText(r,Qt.AlignCenter,"🔊" if self._audio.is_enabled() else "🔇")

    def _draw_help(self,p):
        p.setPen(QColor("#ffe36c")); p.setFont(QFont("Arial",10,QFont.Bold)); p.drawText(12,self.height()-12,f"Nivel {self.level_number} | Fireboy: A/D/W + E | Watergirl: ←/→/↑ + ↓/Enter")


class GameScreen(QWidget):
    def __init__(self, game_mgr: GameManager, audio: AudioManager, network: NetworkManager = None):
        super().__init__()
        self._gm=game_mgr; self._audio=audio; self._network=network; self.current_level=1
        self._build_ui(); self._connect_signals()

    def _build_ui(self):
        layout=QVBoxLayout(self); layout.setSpacing(6); layout.setContentsMargins(8,8,8,8)
        top=QHBoxLayout(); self.lbl_player1=QLabel("J1: Fireboy"); self.lbl_level=QLabel("Nivel 1"); self.lbl_timer=QLabel(f"⏱ {GAME_DURATION_SECONDS}s"); self.lbl_player2=QLabel("J2: Watergirl")
        for lbl in (self.lbl_player1,self.lbl_level,self.lbl_timer,self.lbl_player2): lbl.setFont(QFont("Arial",13,QFont.Bold)); lbl.setAlignment(Qt.AlignCenter)
        top.addWidget(self.lbl_player1); top.addWidget(self.lbl_level); top.addWidget(self.lbl_timer); top.addWidget(self.lbl_player2)
        self.canvas=GameCanvas(self._gm,self._audio,self._network,self)
        row=QHBoxLayout(); self.lbl_score1=QLabel("0"); self.lbl_score2=QLabel("0"); self.lbl_help=QLabel("Juega local con ambos personajes o usa el código de red LAN."); self.lbl_help.setAlignment(Qt.AlignCenter)
        for lbl in (self.lbl_score1,self.lbl_score2): lbl.setFont(QFont("Arial",16,QFont.Bold))
        row.addWidget(self.lbl_score1); row.addWidget(self.lbl_help,2); row.addWidget(self.lbl_score2)
        buttons=QHBoxLayout(); self.btn_reset=QPushButton("REINICIAR NIVEL"); self.btn_pause=QPushButton("PAUSA"); self.btn_exit=QPushButton("SALIR")
        buttons.addStretch(); buttons.addWidget(self.btn_reset); buttons.addWidget(self.btn_pause); buttons.addWidget(self.btn_exit); buttons.addStretch()
        layout.addLayout(top); layout.addWidget(self.canvas,1); layout.addLayout(row); layout.addLayout(buttons); self._apply_styles()

    def _connect_signals(self):
        self._gm.tick.connect(self._on_tick); self._gm.score_changed.connect(self._on_score_changed); self.btn_reset.clicked.connect(self.reset); self.btn_pause.clicked.connect(self._toggle_pause)

    def set_level(self, level_number:int):
        self.current_level=level_number; self.canvas.set_level(level_number); self.lbl_level.setText(f"Nivel {level_number}")

    def reset(self):
        self.lbl_player1.setText(f"J1: {self._gm.player1}"); self.lbl_player2.setText(f"J2: {self._gm.player2}"); self.lbl_level.setText(f"Nivel {self.current_level}")
        self.lbl_score1.setText("0"); self.lbl_score2.setText("0"); self.lbl_timer.setText(f"{GAME_DURATION_SECONDS}s"); self.btn_pause.setText("PAUSA"); self.canvas.set_level(self.current_level)

    def start_level(self): self.canvas.start()
    def stop_level(self): self.canvas.stop()

    def show_game_over(self, score1:int, score2:int, winner:str):
        msg=QMessageBox(self); msg.setWindowTitle("¡Fin de la partida!"); msg.setText(f"<b>Nivel {self.current_level} terminado</b><br><br>{self._gm.player1}: <b>{score1}</b> pts<br>{self._gm.player2}: <b>{score2}</b> pts<br><br>Resultado: <b>{winner}</b>"); msg.exec()

    def _toggle_pause(self):
        if self._gm.is_running and self.canvas.timer.isActive(): self._gm.pause(); self.canvas.stop(); self.btn_pause.setText("CONTINUAR")
        elif self._gm.is_running: self._gm.resume(); self.canvas.start(); self.btn_pause.setText("PAUSA")

    def _on_tick(self, seconds:int):
        self.lbl_timer.setText(f"⏱ {seconds}s"); self.lbl_timer.setStyleSheet("color:#ff6767;font-weight:bold;" if seconds<=10 else "color:#f6dfb4;")

    def _on_score_changed(self,s1:int,s2:int):
        self.lbl_score1.setText(f" {s1}"); self.lbl_score2.setText(f" {s2}")

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color:#141414; color:#f6dfb4; }
            QPushButton { background-color:#d9b38c; border:2px solid #2f1b0e; color:#21160e; padding:8px; border-radius:7px; font-weight:bold; }
            QPushButton:hover { background-color:#efc58b; }
        """)
