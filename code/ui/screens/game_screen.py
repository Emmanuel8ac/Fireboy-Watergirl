from pathlib import Path
import math
import random

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap, QPolygonF, QTransform
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QMessageBox

from config import GAME_DURATION_SECONDS, CHARACTERS_DIR, TEXTURES_DIR, ELEMENTS_DIR, ORIGINAL_DIR
from logic.game_manager import GameManager
from logic.audio_manager import AudioManager
from logic.network_manager import NetworkManager
from models.player import Player, Diamond, Hazard, Switch, Lever, MovingSolid, Portal, Box, Particle, Level


def R(x, y, w, h):
    return QRectF(float(x), float(y), float(w), float(h))


class GameCanvas(QWidget):
    """Fast canvas with code-based physics and original-game visual assets."""

    WORLD_W = 1024
    WORLD_H = 768
    SOURCE_W = 1200
    SOURCE_H = 720
    GRAVITY = 0.70
    MOVE = 5.0
    JUMP = -14.8
    MAX_FALL = 17.0
    PLAYER_W = 43.0
    PLAYER_H = 59.0

    def __init__(self, game_mgr: GameManager, audio: AudioManager, network: NetworkManager = None, parent=None):
        super().__init__(parent)
        self._gm = game_mgr
        self._audio = audio
        self._network = network
        self.remote_keys = set()
        if self._network is not None:
            self._network.remote_input_received.connect(self._on_remote_input)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(560)
        self.keys = set()
        self.level_number = 1
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._frame)
        self.frame = 0
        self.particles = []
        self.sound_button_rect = QRectF()
        self._static_layer = QPixmap()
        self._static_dirty = True
        self._pixmap_cache = {}
        self._last_sent_keys = set()
        self._load_assets()
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

    def _trim(self, pixmap: QPixmap) -> QPixmap:

        if pixmap.isNull():
            return pixmap
        img = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        left, top, right, bottom = img.width(), img.height(), -1, -1
        for y in range(img.height()):
            for x in range(img.width()):
                if img.pixelColor(x, y).alpha() > 12:
                    left, top = min(left, x), min(top, y)
                    right, bottom = max(right, x), max(bottom, y)
        if right < left:
            return pixmap
        return QPixmap.fromImage(img.copy(left, top, right - left + 1, bottom - top + 1))

    def _load_frames(self, folder: Path):
        frames = []
        if folder.exists():
            paths = sorted(folder.glob("*.png"), key=lambda p: int(p.stem) if p.stem.isdigit() else 999)

            for path in paths[:8]:
                pixmap = self._trim(QPixmap(str(path)))
                if not pixmap.isNull():
                    frames.append(pixmap)
        return frames

    def _asset(self, name: str) -> QPixmap:
        return self._trim(QPixmap(str(Path(ELEMENTS_DIR) / name)))

    def _load_assets(self):
        chars = Path(CHARACTERS_DIR)

        fire_source = chars / "fireboy" / "FireBoy_stairs"
        water_source = chars / "watergirl" / "WaterGirlStairs"
        self.fire_frames = self._load_frames(
            fire_source if fire_source.exists() else chars / "fireboy" / "FireBoy_running")
        self.water_frames = self._load_frames(
            water_source if water_source.exists() else chars / "watergirl" / "WaterGirl_running")
        self.fire_idle = self.fire_frames[0] if self.fire_frames else QPixmap()
        self.water_idle = self.water_frames[0] if self.water_frames else QPixmap()

        self.texture_jungle = QPixmap(str(Path(TEXTURES_DIR) / "jungle_texture.png"))
        self.texture_temple = QPixmap(str(Path(TEXTURES_DIR) / "temple_texture.png"))
        self.asset_platform = self._asset("platform.png")
        self.asset_vertical = self._asset("vertical_platform.png")
        self.asset_box = self._asset("moving_box.png")
        self.asset_lava = self._asset("lava.png")
        self.asset_water = self._asset("water.png")
        self.asset_diamond_red = self._asset("diamond_red.png")
        self.asset_diamond_blue = self._asset("diamond_blue.png")
        self.asset_volume = self._asset("volume.png")
        self.asset_switch = self._asset("pressure_plate.png")
        self.asset_lever_base = self._asset("lever_base.png")
        self.asset_lever_handle = self._asset("lever_handle.png")
        self.fire_door_asset = self._asset("fire_door.png")
        self.water_door_asset = self._asset("water_door.png")

    def _walls(self):
        return [R(0, 0, 28, 720), R(1172, 0, 28, 720), R(0, 0, 1200, 24), R(0, 706, 1200, 14)]

    def _diamonds(self, points):
        return [Diamond(R(x, y, 44, 44), owner) for x, y, owner in points]

    def _level(self):
        """Build four progressive maps with reachable jumps and sensible mechanisms."""
        walls = self._walls()

        if self.level_number == 1:
            return Level(
                1, "jungle", (58, 606), (116, 606), R(1060, 72, 72, 98), R(975, 72, 72, 98),
                platforms=walls + [
                    R(32, 670, 250, 28), R(340, 670, 258, 28), R(654, 670, 238, 28), R(952, 670, 208, 28),
                    R(54, 560, 272, 26), R(384, 560, 238, 26), R(684, 560, 250, 26), R(1000, 560, 144, 26),
                    R(62, 450, 210, 26), R(322, 450, 250, 26), R(632, 450, 282, 26), R(988, 450, 158, 26),
                    R(52, 340, 274, 26), R(392, 340, 246, 26), R(710, 340, 236, 26), R(1004, 340, 142, 26),
                    R(84, 232, 238, 26), R(396, 232, 260, 26), R(720, 232, 242, 26), R(970, 170, 188, 26),
                ],
                hazards=[
                    Hazard(R(282, 682, 56, 18), "fire"), Hazard(R(598, 682, 56, 18), "water"),
                    Hazard(R(892, 682, 56, 18), "poison"), Hazard(R(572, 444, 58, 18), "poison"),
                ],
                diamonds=self._diamonds([
                    (170, 620, "fire"), (444, 510, "water"), (736, 510, "fire"),
                    (1048, 400, "water"), (454, 286, "fire"), (778, 178, "water"),
                ]),
                switches=[], levers=[], movers=[], portals=[], boxes=[],
            )

        if self.level_number == 2:
            return Level(
                2, "temple", (62, 606), (120, 606), R(1060, 76, 72, 98), R(975, 76, 72, 98),
                platforms=walls + [
                    R(32, 670, 310, 28), R(396, 670, 240, 28), R(692, 670, 208, 28), R(954, 670, 208, 28),
                    R(54, 558, 226, 26), R(356, 558, 232, 26), R(662, 558, 264, 26), R(996, 558, 150, 26),
                    R(48, 446, 276, 26), R(396, 446, 222, 26), R(690, 446, 220, 26), R(980, 446, 166, 26),
                    R(70, 334, 230, 26), R(370, 334, 258, 26), R(700, 334, 230, 26), R(1000, 334, 146, 26),
                    R(56, 224, 240, 26), R(382, 224, 216, 26), R(710, 224, 248, 26), R(970, 174, 190, 26),
                ],
                hazards=[
                    Hazard(R(342, 682, 52, 18), "poison"), Hazard(R(636, 682, 54, 18), "fire"),
                    Hazard(R(900, 682, 52, 18), "water"), Hazard(R(618, 552, 42, 18), "poison"),
                ],
                diamonds=self._diamonds([
                    (178, 508, "water"), (430, 396, "fire"), (746, 506, "water"),
                    (1028, 396, "fire"), (425, 176, "water"), (770, 176, "fire"),
                ]),
                switches=[Switch(R(198, 650, 64, 18), "lift", "green")],
                levers=[],
                movers=[MovingSolid(R(600, 558, 86, 24), "lift", "green", R(600, 446, 86, 24), speed=0.045)],
                portals=[], boxes=[Box(R(124, 626, 42, 42))],
            )

        if self.level_number == 3:
            return Level(
                3, "jungle", (58, 606), (116, 606), R(1060, 72, 72, 98), R(975, 72, 72, 98),
                platforms=walls + [
                    R(32, 670, 245, 28), R(332, 670, 246, 28), R(638, 670, 250, 28), R(944, 670, 218, 28),
                    R(52, 556, 235, 26), R(350, 556, 262, 26), R(670, 556, 238, 26), R(976, 556, 170, 26),
                    R(70, 442, 246, 26), R(374, 442, 220, 26), R(684, 442, 246, 26), R(1000, 442, 146, 26),
                    R(48, 326, 258, 26), R(376, 326, 248, 26), R(694, 326, 214, 26), R(990, 326, 156, 26),
                    R(64, 214, 238, 26), R(360, 214, 244, 26), R(690, 214, 188, 26), R(968, 170, 192, 26),
                ],
                hazards=[
                    Hazard(R(278, 682, 52, 18), "water"), Hazard(R(580, 682, 56, 18), "fire"),
                    Hazard(R(890, 682, 52, 18), "poison"), Hazard(R(594, 436, 86, 18), "water"),
                ],
                diamonds=self._diamonds([
                    (145, 506, "fire"), (420, 506, "water"), (744, 392, "fire"),
                    (1035, 278, "water"), (416, 164, "fire"), (760, 164, "water"),
                ]),
                switches=[],
                levers=[Lever(R(754, 404, 56, 38), "exit_bridge", "yellow")],
                movers=[MovingSolid(R(878, 214, 86, 24), "exit_bridge", "yellow", R(878, 170, 86, 24), speed=0.05)],
                portals=[Portal(R(230, 606, 48, 48), 1, "purple"), Portal(R(658, 272, 48, 48), 1, "purple")],
                boxes=[],
            )

        return Level(
            4, "temple", (58, 606), (116, 606), R(1060, 72, 72, 98), R(975, 72, 72, 98),
            platforms=walls + [
                R(32, 670, 250, 28), R(344, 670, 220, 28), R(636, 670, 240, 28), R(944, 670, 218, 28),
                R(48, 560, 235, 26), R(342, 560, 230, 26), R(640, 560, 240, 26), R(974, 560, 172, 26),
                R(64, 446, 252, 26), R(386, 446, 214, 26), R(680, 446, 246, 26), R(992, 446, 154, 26),
                R(48, 330, 220, 26), R(334, 330, 248, 26), R(672, 330, 252, 26), R(996, 330, 150, 26),
                R(62, 216, 238, 26), R(374, 216, 230, 26), R(698, 216, 226, 26), R(968, 170, 192, 26),
            ],
            hazards=[
                Hazard(R(282, 682, 60, 18), "fire"), Hazard(R(566, 682, 68, 18), "water"),
                Hazard(R(878, 682, 64, 18), "poison"), Hazard(R(600, 440, 76, 18), "poison"),
            ],
            diamonds=self._diamonds([
                (142, 512, "fire"), (420, 512, "water"), (734, 396, "fire"),
                (1034, 396, "water"), (426, 164, "water"), (766, 164, "fire"),
            ]),
            switches=[Switch(R(176, 650, 64, 18), "central_lift", "green"),
                      Switch(R(746, 540, 64, 18), "central_lift", "orange")],
            levers=[],
            movers=[MovingSolid(R(598, 560, 82, 24), "central_lift", "green", R(598, 446, 82, 24), speed=0.045)],
            portals=[Portal(R(1016, 604, 48, 48), 1, "purple"), Portal(R(300, 278, 48, 48), 1, "purple")],
            boxes=[Box(R(94, 626, 42, 42))],
        )

    def set_level(self, level_number: int):
        self.level_number = max(1, min(4, int(level_number)))
        self.reset_level()

    def _fit_to_original_viewport(self, level):

        sx = self.WORLD_W / self.SOURCE_W
        sy = self.WORLD_H / self.SOURCE_H

        def mapped(rect):
            return R(rect.x() * sx, rect.y() * sy, rect.width() * sx, rect.height() * sy)

        level.fire_spawn = (level.fire_spawn[0] * sx, level.fire_spawn[1] * sy)
        level.water_spawn = (level.water_spawn[0] * sx, level.water_spawn[1] * sy)
        level.platforms = [mapped(rect) for rect in level.platforms]
        level.hazards = [Hazard(mapped(item.rect), item.kind) for item in level.hazards]
        level.diamonds = [Diamond(mapped(item.rect), item.owner, item.collected) for item in level.diamonds]
        level.switches = [Switch(mapped(item.rect), item.target, item.color, item.active) for item in level.switches]
        level.levers = [Lever(mapped(item.rect), item.target, item.color, item.active) for item in level.levers]
        level.movers = [
            MovingSolid(mapped(item.rect), item.target, item.color, mapped(item.to_rect), item.progress, item.speed,
                        item.vanish) for item in level.movers]
        level.portals = [Portal(mapped(item.rect), item.pair, item.color) for item in level.portals]
        level.boxes = [Box(mapped(item.rect), item.vx, item.vy) for item in level.boxes]

        def fitted_door(rect):
            transformed = mapped(rect)
            return R(transformed.x(), transformed.bottom() - 86, 58, 86)

        level.fire_door = fitted_door(level.fire_door)
        level.water_door = fitted_door(level.water_door)
        return level

    def reset_level(self):
        self.keys.clear()
        self.remote_keys.clear()
        self.data = self._fit_to_original_viewport(self._level())
        fx, fy = self.data.fire_spawn
        wx, wy = self.data.water_spawn
        self.fire = Player("Fireboy", "fire", fx, fy, fx, fy, w=self.PLAYER_W, h=self.PLAYER_H)
        self.water = Player("Watergirl", "water", wx, wy, wx, wy, w=self.PLAYER_W, h=self.PLAYER_H)
        self.platforms = [QRectF(p) for p in self.data.platforms]
        self.hazards = [Hazard(QRectF(h.rect), h.kind) for h in self.data.hazards]
        self.diamonds = [Diamond(QRectF(d.rect), d.owner, False) for d in self.data.diamonds]
        self.switches = [Switch(QRectF(s.rect), s.target, s.color, False) for s in self.data.switches]
        self.levers = [Lever(QRectF(l.rect), l.target, l.color, False) for l in self.data.levers]
        self.movers = [MovingSolid(QRectF(m.rect), m.target, m.color, QRectF(m.to_rect), 0.0, m.speed, m.vanish) for m
                       in self.data.movers]
        self.portals = [Portal(QRectF(p.rect), p.pair, p.color) for p in self.data.portals]
        self.boxes = [Box(QRectF(b.rect), 0.0, 0.0) for b in self.data.boxes]
        self._last_lever = False
        self.frame = 0
        self.particles.clear()
        self._last_sent_keys = set()
        self._static_dirty = True
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
            self._audio.toggle_audio()
            self.update()
            return
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        self._static_dirty = True
        self._pixmap_cache.clear()
        super().resizeEvent(event)

    def _scale(self):
        return self.width() / self.WORLD_W, self.height() / self.WORLD_H

    def _r(self, rect):
        sx, sy = self._scale()
        return QRectF(rect.x() * sx, rect.y() * sy, rect.width() * sx, rect.height() * sy)

    def _active_targets(self):
        active = set()
        for switch in self.switches:
            switch.active = (
                    self.fire.rect.intersects(switch.rect)
                    or self.water.rect.intersects(switch.rect)
                    or any(box.rect.intersects(switch.rect) for box in self.boxes)
            )
            if switch.active:
                active.add(switch.target)
        for lever in self.levers:
            if lever.active:
                active.add(lever.target)
        return active

    def _mover_rect(self, mover):
        t = max(0.0, min(1.0, mover.progress))
        return R(
            mover.rect.x() + (mover.to_rect.x() - mover.rect.x()) * t,
            mover.rect.y() + (mover.to_rect.y() - mover.rect.y()) * t,
            mover.rect.width(), mover.rect.height(),
        )

    def _solid_movers(self):
        return [self._mover_rect(mover) for mover in self.movers]

    def _solids(self):
        return self.platforms + self._solid_movers() + [box.rect for box in self.boxes]

    def _frame(self):
        if not self._gm.is_running:
            return
        self.frame += 1
        if self._network is not None and self._network.is_online():
            local_keys = self._key_names(self.keys)
            if local_keys != self._last_sent_keys or self.frame % 15 == 0:
                self._network.send_input(local_keys)
                self._last_sent_keys = set(local_keys)
        self._input()
        self._move_movers()
        self._update_boxes()
        self._update_player(self.fire)
        self._update_player(self.water)
        self._activate_levers()
        self._collect_diamonds()
        self._check_hazards()
        self._check_portals()
        self._check_doors()
        self._update_particles()
        self.update()

    def _input(self):
        local = self._key_names(self.keys)
        remote = set(self.remote_keys)
        if self._network is not None and self._network.is_host() and self._network.is_connected():
            fire_keys, water_keys = local, remote
        elif self._network is not None and self._network.is_client() and self._network.is_connected():
            fire_keys, water_keys = remote, local
        else:
            fire_keys = water_keys = local

        self.fire.vx = (-self.MOVE if "A" in fire_keys else 0) + (self.MOVE if "D" in fire_keys else 0)
        self.water.vx = (-self.MOVE if "LEFT" in water_keys else 0) + (self.MOVE if "RIGHT" in water_keys else 0)
        if self.fire.vx:
            self.fire.facing = 1 if self.fire.vx > 0 else -1
        if self.water.vx:
            self.water.facing = 1 if self.water.vx > 0 else -1
        if "W" in fire_keys and self.fire.on_ground:
            self.fire.vy = self.JUMP
            self.fire.on_ground = False
            self._audio.play_effect("jump_fire")
        if "UP" in water_keys and self.water.on_ground:
            self.water.vy = self.JUMP
            self.water.on_ground = False
            self._audio.play_effect("jump_water")

    def _move_movers(self):
        active = self._active_targets()
        for mover in self.movers:
            before = self._mover_rect(mover)
            target = 1.0 if mover.target in active else 0.0
            old_progress = mover.progress
            if mover.progress < target:
                mover.progress = min(target, mover.progress + mover.speed)
            elif mover.progress > target:
                mover.progress = max(target, mover.progress - mover.speed)
            if mover.progress == old_progress:
                mover._was_moving = False
                continue
            after = self._mover_rect(mover)
            dx, dy = after.x() - before.x(), after.y() - before.y()
            if not getattr(mover, "_was_moving", False):
                self._audio.play_effect("platform")
            mover._was_moving = True
            for player in (self.fire, self.water):
                standing = abs(
                    player.rect.bottom() - before.top()) <= 7 and player.rect.right() > before.left() and player.rect.left() < before.right()
                if standing:
                    player.x += dx
                    player.y += dy

    def _update_boxes(self):
        solids = self.platforms + self._solid_movers()
        for box in self.boxes:
            box.vy = min(self.MAX_FALL, box.vy + self.GRAVITY)
            box.rect.translate(0, box.vy)
            for solid in solids:
                if box.rect.intersects(solid) and box.vy >= 0:
                    box.rect.moveBottom(solid.top())
                    box.vy = 0

    def _push_boxes(self, player):
        if abs(player.vx) < 0.1:
            return
        fixed_solids = self.platforms + self._solid_movers()
        for box in self.boxes:
            if player.rect.intersects(box.rect):
                old = QRectF(box.rect)
                box.rect.translate(player.vx, 0)
                if any(box.rect.intersects(solid) for solid in fixed_solids):
                    box.rect = old
                    player.x = box.rect.left() - player.w if player.vx > 0 else box.rect.right()

    def _update_player(self, player):
        if player.cooldown > 0:
            player.cooldown -= 1
        player.x += player.vx
        self._push_boxes(player)
        for solid in self._solids():
            if player.rect.intersects(solid):
                if player.vx > 0:
                    player.x = solid.left() - player.w
                elif player.vx < 0:
                    player.x = solid.right()
        player.vy = min(self.MAX_FALL, player.vy + self.GRAVITY)
        player.y += player.vy
        player.on_ground = False
        for solid in self._solids():
            if player.rect.intersects(solid):
                if player.vy >= 0:
                    player.y = solid.top() - player.h
                    player.vy = 0
                    player.on_ground = True
                else:
                    player.y = solid.bottom()
                    player.vy = 0
        if player.vx:
            player.anim += 1
        if player.y > self.WORLD_H + 60:
            player.respawn()

    def _activate_levers(self):
        pressed = bool({"E", "DOWN", "ENTER"} & (self._key_names(self.keys) | self.remote_keys))
        if pressed and not self._last_lever:
            for lever in self.levers:
                close_to_fire = self.fire.rect.adjusted(-20, -20, 20, 20).intersects(lever.rect)
                close_to_water = self.water.rect.adjusted(-20, -20, 20, 20).intersects(lever.rect)
                if close_to_fire or close_to_water:
                    lever.active = not lever.active
                    self._audio.play_effect("lever")
        self._last_lever = pressed

    def _collect_diamonds(self):
        for diamond in self.diamonds:
            if diamond.collected:
                continue
            if diamond.owner == "fire" and self.fire.rect.intersects(diamond.rect):
                diamond.collected = True
                self._gm.add_point(1, 10)
                self._audio.play_effect("diamond")
            elif diamond.owner == "water" and self.water.rect.intersects(diamond.rect):
                diamond.collected = True
                self._gm.add_point(2, 10)
                self._audio.play_effect("diamond")

    def _check_hazards(self):
        for hazard in self.hazards:
            if self.fire.rect.intersects(hazard.rect) and hazard.kind in ("water", "poison"):
                self._burst(self.fire.rect.center(), QColor("#ff6b12"))
                self.fire.respawn()
                self._audio.play_effect("over")
            if self.water.rect.intersects(hazard.rect) and hazard.kind in ("fire", "poison"):
                self._burst(self.water.rect.center(), QColor("#35caff"))
                self.water.respawn()
                self._audio.play_effect("over")

    def _check_portals(self):
        for player in (self.fire, self.water):
            if player.cooldown > 0:
                continue
            for portal in self.portals:
                if player.rect.intersects(portal.rect):
                    other = next((candidate for candidate in self.portals if
                                  candidate.pair == portal.pair and candidate is not portal), None)
                    if other:
                        player.x = other.rect.center().x() - player.w / 2
                        player.y = other.rect.top() - player.h - 3
                        player.vx = player.vy = 0
                        player.cooldown = 38
                        self._audio.play_effect("pusher")
                        self._burst(other.rect.center(), QColor("#ba49ff"))
                    break

    def _check_doors(self):
        fire_zone = self.data.fire_door.adjusted(-8, -4, 8, 6)
        water_zone = self.data.water_door.adjusted(-8, -4, 8, 6)
        if self.fire.rect.intersects(fire_zone) and self.water.rect.intersects(water_zone):
            self._gm.finish()

    def _update_particles(self):
        if self.frame % 7 == 0:
            self._add_particle(self.fire.x + self.fire.w / 2, self.fire.y + self.fire.h - 5, QColor("#ff6d17"), True)
            self._add_particle(self.water.x + self.water.w / 2, self.water.y + self.water.h - 5, QColor("#39c9ff"),
                               False)
        alive = []
        for particle in self.particles:
            particle.life -= 1
            particle.x += particle.vx
            particle.y += particle.vy
            particle.vy += 0.04
            particle.size *= 0.95
            if particle.life > 0 and particle.size > 0.7:
                alive.append(particle)
        self.particles = alive[-36:]

    def _add_particle(self, x, y, color, rising):
        self.particles.append(Particle(
            x + random.uniform(-4, 4), y + random.uniform(-2, 2), random.uniform(-0.5, 0.5),
            random.uniform(-1.1, -0.2) if rising else random.uniform(-0.3, 0.4),
            random.randint(10, 18), color, random.uniform(2.2, 4.2),
        ))

    def _burst(self, center, color):
        for _ in range(7):
            angle = random.random() * math.tau
            speed = random.uniform(1.0, 3.2)
            self.particles.append(Particle(center.x(), center.y(), math.cos(angle) * speed, math.sin(angle) * speed,
                                           random.randint(12, 22), color, random.uniform(2.5, 5.0)))

    def _scaled_asset(self, key, pixmap, width, height):
        cache_key = (key, int(width), int(height))
        if cache_key not in self._pixmap_cache:
            self._pixmap_cache[cache_key] = pixmap.scaled(int(width), int(height), Qt.IgnoreAspectRatio,
                                                          Qt.FastTransformation)
        return self._pixmap_cache[cache_key]

    def _rebuild_static_layer(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        self._static_layer = QPixmap(self.size())
        self._static_layer.fill(Qt.transparent)
        painter = QPainter(self._static_layer)
        painter.setRenderHint(QPainter.Antialiasing, False)
        self._draw_background(painter)
        for platform in self.platforms:
            self._draw_platform(painter, platform)
        for hazard in self.hazards:
            self._draw_hazard(painter, hazard)
        self._draw_doors(painter)
        painter.end()
        self._static_dirty = False

    def paintEvent(self, event):
        if self._static_dirty or self._static_layer.size() != self.size():
            self._rebuild_static_layer()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.drawPixmap(0, 0, self._static_layer)
        for mover in self.movers:
            self._draw_mover(painter, mover)
        for switch in self.switches:
            self._draw_switch(painter, switch)
        for lever in self.levers:
            self._draw_lever(painter, lever)
        for portal in self.portals:
            self._draw_portal(painter, portal)
        for box in self.boxes:
            self._draw_box(painter, box.rect)
        for diamond in self.diamonds:
            if not diamond.collected:
                self._draw_diamond(painter, diamond)
        self._draw_particles(painter)
        self._draw_player(painter, self.fire, self.fire_frames, self.fire_idle, QColor("#ff5b1a"))
        self._draw_player(painter, self.water, self.water_frames, self.water_idle, QColor("#35caff"))
        self._draw_timer(painter)
        self._draw_sound(painter)

    def _draw_background(self, painter):
        texture = self.texture_jungle if self.data.theme == "jungle" else self.texture_temple
        painter.fillRect(self.rect(), QColor("#101a12" if self.data.theme == "jungle" else "#1c1615"))
        if not texture.isNull():
            painter.save()
            painter.setOpacity(0.48)
            painter.drawTiledPixmap(self.rect(), texture)
            painter.restore()
        painter.fillRect(self.rect(), QColor(8, 13, 10, 42))

    def _draw_platform(self, painter, rect):
        visible = self._r(rect)
        if self.asset_platform.isNull():
            painter.fillRect(visible, QColor("#775335"))
            return
        tile_h = max(16, int(visible.height()))
        tile_w = max(62, int(tile_h * 4.1))
        tile = self._scaled_asset("platform", self.asset_platform, tile_w, tile_h)
        painter.save()
        painter.setClipRect(visible)
        painter.drawTiledPixmap(visible, tile)
        painter.restore()

    def _draw_mover(self, painter, mover):
        visible = self._r(self._mover_rect(mover))
        tile = self._scaled_asset("mover", self.asset_platform, visible.width(),
                                  visible.height()) if not self.asset_platform.isNull() else QPixmap()
        if not tile.isNull():
            painter.drawPixmap(visible.toRect(), tile)
        else:
            painter.fillRect(visible, QColor("#d6bb6a"))
        border = {"green": "#55f85e", "orange": "#ff922a", "yellow": "#ffe04a"}.get(mover.color, "#ffe04a")
        painter.setPen(QPen(QColor(border), 3))
        painter.drawRoundedRect(visible, 4, 4)

    def _draw_hazard(self, painter, hazard):
        visible = self._r(hazard.rect)
        if hazard.kind == "fire" and not self.asset_lava.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("lava", self.asset_lava, visible.width(), visible.height()))
        elif hazard.kind == "water" and not self.asset_water.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("water", self.asset_water, visible.width(), visible.height()))
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#52db42"))
            painter.drawRoundedRect(visible, 8, 8)
            painter.setPen(QPen(QColor("#9dff6a"), 2))
            painter.drawLine(visible.left() + 5, visible.top() + 4, visible.right() - 5, visible.top() + 4)

    def _draw_switch(self, painter, switch):
        visible = self._r(switch.rect)
        if not self.asset_switch.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("switch", self.asset_switch, visible.width(), visible.height()))
        else:
            painter.fillRect(visible, QColor("#53e45c"))
        if switch.active:
            painter.setPen(QPen(QColor("#fbff99"), 3))
            painter.drawRoundedRect(visible, 4, 4)

    def _draw_lever(self, painter, lever):
        visible = self._r(lever.rect)
        if not self.asset_lever_base.isNull():
            painter.drawPixmap(QRectF(visible.x(), visible.bottom() - visible.height() * .45, visible.width(),
                                      visible.height() * .45).toRect(),
                               self._scaled_asset("leverbase", self.asset_lever_base, visible.width(),
                                                  visible.height() * .45))
        pivot = QPointF(visible.center().x(), visible.bottom() - visible.height() * 0.35)
        tip = QPointF(pivot.x() + (visible.width() * 0.31 if lever.active else -visible.width() * 0.31),
                      visible.top() + 5)
        painter.setPen(QPen(QColor("#ffe044"), 6))
        painter.drawLine(pivot, tip)
        painter.setBrush(QColor("#ffe044"))
        painter.drawEllipse(tip, 5, 5)

    def _draw_portal(self, painter, portal):
        visible = self._r(portal.rect)
        color = {"purple": "#c653ff", "green": "#57f263"}.get(portal.color, "#c653ff")
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor(255, 255, 255, 22))
        painter.setPen(QPen(QColor(color), 5))
        painter.drawEllipse(visible)
        painter.setRenderHint(QPainter.Antialiasing, False)

    def _draw_box(self, painter, rect):
        visible = self._r(rect)
        if not self.asset_box.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("box", self.asset_box, visible.width(), visible.height()))
        else:
            painter.fillRect(visible, QColor("#e5dfbe"))

    def _draw_doors(self, painter):
        self._draw_door(painter, self.data.fire_door, self.fire_door_asset, QColor("#ff421f"))
        self._draw_door(painter, self.data.water_door, self.water_door_asset, QColor("#27d6ff"))

    def _draw_door(self, painter, rect, asset, fallback):
        visible = self._r(rect)
        if not asset.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("door" + fallback.name(), asset, visible.width(), visible.height()))
        else:
            painter.setBrush(QColor("#353536"))
            painter.setPen(QPen(fallback, 4))
            painter.drawRoundedRect(visible, 6, 6)

    def _draw_diamond(self, painter, diamond):
        visible = self._r(diamond.rect)
        asset = self.asset_diamond_red if diamond.owner == "fire" else self.asset_diamond_blue
        if not asset.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("gem_" + diamond.owner, asset, visible.width(), visible.height()))
        else:
            center = visible.center()
            shape = QPolygonF([QPointF(center.x(), visible.top()), QPointF(visible.right(), center.y()),
                               QPointF(center.x(), visible.bottom()), QPointF(visible.left(), center.y())])
            painter.setBrush(QColor("#ff3939" if diamond.owner == "fire" else "#35d9ff"))
            painter.drawPolygon(shape)

    def _draw_player(self, painter, player, frames, idle, fallback):
        visible = self._r(player.rect)
        pixmap = idle
        if frames and abs(player.vx) > 0.1:
            pixmap = frames[(player.anim // 3) % len(frames)]
        if pixmap.isNull():
            painter.setBrush(fallback)
            painter.drawRoundedRect(visible, 10, 10)
            return
        key = "fire" if player.kind == "fire" else "water"
        cache_key = (key, (player.anim // 3) % 8, int(visible.width()), int(visible.height()))
        sprite = self._pixmap_cache.get(cache_key)
        if sprite is None:
            sprite = pixmap.scaled(int(visible.width()), int(visible.height()), Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)
            self._pixmap_cache[cache_key] = sprite
        if player.facing < 0:
            sprite = sprite.transformed(QTransform().scale(-1, 1))
        target = QRectF(
            visible.center().x() - sprite.width() / 2,
            visible.bottom() - sprite.height(),
            sprite.width(), sprite.height(),
        )
        painter.drawPixmap(target.toRect(), sprite)

    def _draw_particles(self, painter):
        painter.setPen(Qt.NoPen)
        sx, sy = self._scale()
        for particle in self.particles:
            color = QColor(particle.color)
            color.setAlpha(max(20, min(140, particle.life * 8)))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(particle.x * sx, particle.y * sy), particle.size * sx, particle.size * sy)

    def _draw_timer(self, painter):
        width, height = 132, 52
        x = (self.width() - width) / 2
        painter.setBrush(QColor(35, 35, 35, 235))
        painter.setPen(QPen(QColor("#080808"), 4))
        painter.drawRoundedRect(QRectF(x, 5, width, height), 7, 7)
        seconds = max(0, int(self._gm.time_left))
        text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        painter.setFont(QFont("Arial", 26, QFont.Bold))
        painter.setPen(QColor("#ffd42d"))
        painter.drawText(QRectF(x, 5, width, height), Qt.AlignCenter, text)

    def _draw_sound(self, painter):
        self.sound_button_rect = QRectF(self.width() - 57, 12, 42, 42)
        visible = self.sound_button_rect
        if not self.asset_volume.isNull():
            painter.drawPixmap(visible.toRect(),
                               self._scaled_asset("volume", self.asset_volume, visible.width(), visible.height()))
        else:
            painter.setFont(QFont("Arial", 23, QFont.Bold))
            painter.setPen(QColor("#ffd72b"))
            painter.drawText(visible, Qt.AlignCenter, "S")
        if not self._audio.is_enabled():
            painter.setPen(QPen(QColor("#ee3c37"), 5))
            painter.drawLine(visible.left() + 5, visible.top() + 5, visible.right() - 5, visible.bottom() - 5)

    def _draw_help(self, painter):
        painter.setPen(QColor("#ffe36c"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(12, self.height() - 12,
                         f"Level {self.level_number} | Fireboy: A/D/W + E | Watergirl: Left/Right/Up + Down/Enter")


class GameViewport(QWidget):

    def __init__(self, canvas: GameCanvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.canvas.setParent(self)
        self.setStyleSheet("background:#080808;")

        elements = Path(ELEMENTS_DIR)
        emerald = (elements / "pause_emerald.png").as_posix()
        emerald_over = (elements / "pause_emerald_hover.png").as_posix()
        emerald_down = (elements / "pause_emerald_down.png").as_posix()
        panel_img = (elements / "pause_panel.png").as_posix()

        self.gem_button = QPushButton(self)
        self.gem_button.setCursor(Qt.PointingHandCursor)
        self.gem_button.setStyleSheet(f"""
            QPushButton {{ border:none; background:transparent; image:url('{emerald}'); }}
            QPushButton:hover {{ image:url('{emerald_over}'); }}
            QPushButton:pressed {{ image:url('{emerald_down}'); }}
        """)

        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 138);")
        self.overlay.hide()

        self.card = QFrame(self.overlay)
        self.card.setObjectName("pauseCard")
        self.card.setStyleSheet(f"""
            QFrame#pauseCard {{ border-image: url('{panel_img}') 0 0 0 0 stretch stretch; background:transparent; }}
            QLabel {{ background:transparent; color:#2b2118; font-weight:bold; }}
            QPushButton {{
                background:transparent; border:none; color:#2d261e;
                font-family:'Times New Roman'; font-size:27px; font-weight:bold;
            }}
            QPushButton:hover {{ color:#f2cc34; }}
        """)
        panel = QVBoxLayout(self.card)
        panel.setContentsMargins(62, 68, 62, 42)
        panel.setSpacing(8)

        self.btn_resume = QPushButton("RESUME")
        self.btn_reset = QPushButton("RETRY LEVEL")
        self.lbl_blue = QLabel("◆  X 0")
        self.lbl_red = QLabel("◆  X 0")
        self.lbl_blue.setStyleSheet(
            "background:transparent; color:#21bfff; font-family:'Times New Roman'; font-size:27px;")
        self.lbl_red.setStyleSheet(
            "background:transparent; color:#ef322a; font-family:'Times New Roman'; font-size:27px;")
        self.btn_menu = QPushButton("MAIN MENU")
        for item in (self.btn_resume, self.btn_reset, self.lbl_blue, self.lbl_red, self.btn_menu):
            if isinstance(item, QLabel):
                item.setAlignment(Qt.AlignCenter)
            panel.addWidget(item)
        panel.setStretch(0, 1)
        panel.setStretch(1, 1)
        panel.setStretch(2, 1)
        panel.setStretch(3, 1)
        panel.setStretch(4, 1)

    def set_scores(self, fire_score: int, water_score: int):
        self.lbl_blue.setText(f"◆  X {water_score // 10}")
        self.lbl_red.setText(f"◆  X {fire_score // 10}")

    def show_pause(self, fire_score: int, water_score: int):
        self.set_scores(fire_score, water_score)
        self.overlay.show()
        self.overlay.raise_()
        self.card.raise_()

    def hide_pause(self):
        self.overlay.hide()
        self.gem_button.raise_()

    def resizeEvent(self, event):
        margin = 8
        available_w = max(10, self.width() - margin * 2)
        available_h = max(10, self.height() - margin * 2)
        ratio = 4 / 3
        game_w = min(available_w, int(available_h * ratio))
        game_h = int(game_w / ratio)
        if game_h > available_h:
            game_h = available_h
            game_w = int(game_h * ratio)
        x = (self.width() - game_w) // 2
        y = (self.height() - game_h) // 2
        self.canvas.setGeometry(x, y, game_w, game_h)
        self.overlay.setGeometry(x, y, game_w, game_h)

        gem_size = max(60, min(82, int(game_h * 0.094)))
        self.gem_button.setGeometry(x + game_w // 2 - gem_size // 2, y + game_h - gem_size + 16, gem_size, gem_size)
        self.gem_button.raise_()

        card_h = min(int(game_h * 0.70), 492)
        card_w = int(card_h * 336 / 325)
        self.card.setGeometry((game_w - card_w) // 2, (game_h - card_h) // 2, card_w, card_h)
        super().resizeEvent(event)


class GameScreen(QWidget):
    def __init__(self, game_mgr: GameManager, audio: AudioManager, network: NetworkManager = None):
        super().__init__()
        self._gm = game_mgr
        self._audio = audio
        self._network = network
        self.current_level = 1
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.canvas = GameCanvas(self._gm, self._audio, self._network, self)
        self.viewport = GameViewport(self.canvas, self)
        self.btn_menu = self.viewport.btn_menu
        self.btn_reset = self.viewport.btn_reset
        self.btn_pause = self.viewport.gem_button
        layout.addWidget(self.viewport, 1)
        self.setStyleSheet("background-color:#080808;")

    def _connect_signals(self):
        self._gm.score_changed.connect(self._on_score_changed)
        self.btn_pause.clicked.connect(self._open_pause_menu)
        self.viewport.btn_resume.clicked.connect(self._resume_level)
        self.btn_reset.clicked.connect(self._restart_level)

    def set_level(self, level_number: int):
        self.current_level = max(1, min(4, int(level_number)))
        self.canvas.set_level(self.current_level)

    def reset(self):
        self.viewport.hide_pause()
        self.viewport.set_scores(0, 0)
        self.canvas.set_level(self.current_level)

    def _restart_level(self):
        self.viewport.hide_pause()
        self._audio.resume_music()
        self._gm.start()
        self.reset()
        self.canvas.start()

    def start_level(self):
        self.viewport.hide_pause()
        self.canvas.start()

    def stop_level(self):
        self.viewport.hide_pause()
        self.canvas.stop()

    def show_game_over(self, score1: int, score2: int, winner: str):
        message = QMessageBox(self)
        message.setWindowTitle("Level Complete")
        message.setText(
            f"<b>Level {self.current_level} complete</b><br><br>"
            f"{self._gm.player1}: <b>{score1}</b> points<br>"
            f"{self._gm.player2}: <b>{score2}</b> points<br><br>"
            f"Result: <b>{winner}</b>"
        )
        message.exec()

    def _open_pause_menu(self):
        if not self._gm.is_running or not self.canvas.timer.isActive():
            return
        self._gm.pause()
        self.canvas.stop()
        self._audio.pause_music()
        self.viewport.show_pause(self._gm.score1, self._gm.score2)

    def _resume_level(self):
        if not self._gm.is_running:
            return
        self.viewport.hide_pause()
        self._gm.resume()
        self._audio.resume_music()
        self.canvas.start()
        self.canvas.setFocus()

    def _on_score_changed(self, score1: int, score2: int):
        self.viewport.set_scores(score1, score2)
