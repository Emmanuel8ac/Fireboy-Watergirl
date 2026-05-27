from pathlib import Path
import math
import random

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF, QTransform
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox

from config import GAME_DURATION_SECONDS, CHARACTERS_DIR, TEXTURES_DIR, ELEMENTS_DIR, UI_DIR
from logic.game_manager import GameManager
from logic.audio_manager import AudioManager
from logic.network_manager import NetworkManager
from models.player import Player, Diamond, Hazard, Switch, Lever, MovingSolid, Portal, Box, Particle
from logic.level_builder import create_level


def R(x, y, w, h):
    return QRectF(float(x), float(y), float(w), float(h))


class GameCanvas(QWidget):

    WORLD_W = 1200
    WORLD_H = 720
    GRAVITY = 0.66
    MOVE = 5.6
    JUMP = -15.4
    MAX_FALL = 17.0
    PLAYER_W = 46.0
    PLAYER_H = 64.0

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
        ui_game = Path(UI_DIR) / "game"
        self.fire_frames = self._load_frames(chars / "fireboy" / "FireBoy_running")
        self.water_frames = self._load_frames(chars / "watergirl" / "WaterGirl_running")
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
        self.asset_pause_menu = QPixmap(str(ui_game / "pause_menu_exact.png"))
        self.asset_pause_emerald = QPixmap(str(ui_game / "pause_emerald_exact.png"))

    def set_level(self, level_number: int):
        self.level_number = max(1, min(4, int(level_number)))
        self.reset_level()

    def reset_level(self):
        self.keys.clear()
        self.remote_keys.clear()
        self.data = create_level(self.level_number)
        fx, fy = self.data.fire_spawn
        wx, wy = self.data.water_spawn
        self.fire = Player("Fireboy", "fire", fx, fy, fx, fy, w=self.PLAYER_W, h=self.PLAYER_H)
        self.water = Player("Watergirl", "water", wx, wy, wx, wy, w=self.PLAYER_W, h=self.PLAYER_H)
        self.platforms = [QRectF(p) for p in self.data.platforms]
        self.hazards = [Hazard(QRectF(h.rect), h.kind) for h in self.data.hazards]
        self.diamonds = [Diamond(QRectF(d.rect), d.owner, False) for d in self.data.diamonds]
        self.switches = [Switch(QRectF(s.rect), s.target, s.color, False) for s in self.data.switches]
        self.levers = [Lever(QRectF(l.rect), l.target, l.color, False) for l in self.data.levers]
        self.movers = [MovingSolid(QRectF(m.rect), m.target, m.color, QRectF(m.to_rect), 0.0, m.speed, m.vanish) for m in self.data.movers]
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
        if self._network is None or not self._network.is_connected():
            self.fire.vx = 0
            self.water.vx = 0
            return

        local_keys = self._key_names(self.keys)
        remote_keys = set(self.remote_keys)
        if self._network.is_host():
            host_keys, guest_keys = local_keys, remote_keys
        else:
            host_keys, guest_keys = remote_keys, local_keys
        controls = {self._gm.player1: host_keys, self._gm.player2: guest_keys}
        self._control_online_player(self.fire, controls.get("Fireboy", set()))
        self._control_online_player(self.water, controls.get("Watergirl", set()))

    def _control_online_player(self, player, keys):
        left = "A" in keys or "LEFT" in keys
        right = "D" in keys or "RIGHT" in keys
        jump = "W" in keys or "UP" in keys
        player.vx = (-self.MOVE if left else 0) + (self.MOVE if right else 0)
        self._face_player(player)
        sound = "jump_fire" if player.kind == "fire" else "jump_water"
        self._jump(player, jump, sound)

    @staticmethod
    def _face_player(player):
        if player.vx:
            player.facing = 1 if player.vx > 0 else -1

    def _jump(self, player, pressed, sound):
        if pressed and player.on_ground:
            player.vy = self.JUMP
            player.on_ground = False
            self._audio.play_effect(sound)

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
                standing = abs(player.rect.bottom() - before.top()) <= 7 and player.rect.right() > before.left() and player.rect.left() < before.right()
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
                self._gm.add_point(self._player_number("Fireboy"), 10)
                self._audio.play_effect("diamond")
            elif diamond.owner == "water" and self.water.rect.intersects(diamond.rect):
                diamond.collected = True
                self._gm.add_point(self._player_number("Watergirl"), 10)
                self._audio.play_effect("diamond")

    def _player_number(self, character):
        return 1 if self._gm.player1 == character else 2

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
                    other = next((candidate for candidate in self.portals if candidate.pair == portal.pair and candidate is not portal), None)
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
            self._gm.complete_level()

    def _update_particles(self):
        if self.frame % 7 == 0:
            self._add_particle(self.fire.x + self.fire.w / 2, self.fire.y + self.fire.h - 5, QColor("#ff6d17"), True)
            self._add_particle(self.water.x + self.water.w / 2, self.water.y + self.water.h - 5, QColor("#39c9ff"), False)
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
            self.particles.append(Particle(center.x(), center.y(), math.cos(angle) * speed, math.sin(angle) * speed, random.randint(12, 22), color, random.uniform(2.5, 5.0)))

    def _scaled_asset(self, key, pixmap, width, height):
        cache_key = (key, int(width), int(height))
        if cache_key not in self._pixmap_cache:
            self._pixmap_cache[cache_key] = pixmap.scaled(int(width), int(height), Qt.IgnoreAspectRatio, Qt.FastTransformation)
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
        self._draw_help(painter)

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
        if visible.height() > visible.width() * 2:
            self._draw_vertical_barrier(painter, visible, "wall")
            return
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

    def _draw_vertical_barrier(self, painter, visible, key):
        if self.asset_platform.isNull():
            painter.fillRect(visible, QColor("#775335"))
            return
        rotated = self.asset_platform.transformed(QTransform().rotate(90))
        tile_w = max(18, int(visible.width()))
        tile_h = max(58, int(tile_w * 3.2))
        tile = self._scaled_asset(key, rotated, tile_w, tile_h)
        painter.save()
        painter.setClipRect(visible)
        painter.drawTiledPixmap(visible, tile)
        painter.restore()

    def _draw_mover(self, painter, mover):
        visible = self._r(self._mover_rect(mover))
        vertical = visible.height() > visible.width() * 1.4
        if vertical:
            self._draw_vertical_barrier(painter, visible, "gate")
        elif not self.asset_platform.isNull():
            tile = self._scaled_asset("mover", self.asset_platform, visible.width(), visible.height())
            painter.drawPixmap(visible.toRect(), tile)
        else:
            painter.fillRect(visible, QColor("#d6bb6a"))
        border = {"green": "#55f85e", "orange": "#ff922a", "yellow": "#ffe04a"}.get(mover.color, "#ffe04a")
        painter.setPen(QPen(QColor(border), 3))
        painter.drawRoundedRect(visible, 4, 4)

    def _draw_hazard(self, painter, hazard):
        visible = self._r(hazard.rect)
        if hazard.kind == "fire" and not self.asset_lava.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("lava", self.asset_lava, visible.width(), visible.height()))
        elif hazard.kind == "water" and not self.asset_water.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("water", self.asset_water, visible.width(), visible.height()))
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#52db42"))
            painter.drawRoundedRect(visible, 8, 8)
            painter.setPen(QPen(QColor("#9dff6a"), 2))
            painter.drawLine(visible.left() + 5, visible.top() + 4, visible.right() - 5, visible.top() + 4)

    def _draw_switch(self, painter, switch):
        visible = self._r(switch.rect)
        if not self.asset_switch.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("switch", self.asset_switch, visible.width(), visible.height()))
        else:
            painter.fillRect(visible, QColor("#53e45c"))
        if switch.active:
            painter.setPen(QPen(QColor("#fbff99"), 3))
            painter.drawRoundedRect(visible, 4, 4)

    def _draw_lever(self, painter, lever):
        visible = self._r(lever.rect)
        base = QRectF(visible.x(), visible.bottom() - visible.height() * .45, visible.width(), visible.height() * .45)
        if not self.asset_lever_base.isNull():
            painter.drawPixmap(base.toRect(), self._scaled_asset("lever_base", self.asset_lever_base, base.width(), base.height()))
        pivot = QPointF(visible.center().x(), visible.bottom() - visible.height() * 0.32)
        if not self.asset_lever_handle.isNull():
            handle = self._scaled_asset("lever_handle", self.asset_lever_handle, visible.width() * 0.28, visible.height() * 0.8)
            painter.save()
            painter.translate(pivot)
            painter.rotate(30 if lever.active else -30)
            target = QRectF(-handle.width() / 2, -handle.height() + 7, handle.width(), handle.height())
            painter.drawPixmap(target.toRect(), handle)
            painter.restore()
        else:
            tip = QPointF(pivot.x() + (visible.width() * 0.31 if lever.active else -visible.width() * 0.31), visible.top() + 5)
            painter.setPen(QPen(QColor("#ffe044"), 6))
            painter.drawLine(pivot, tip)

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
            painter.drawPixmap(visible.toRect(), self._scaled_asset("box", self.asset_box, visible.width(), visible.height()))
        else:
            painter.fillRect(visible, QColor("#e5dfbe"))

    def _draw_doors(self, painter):
        self._draw_door(painter, self.data.fire_door, self.fire_door_asset, QColor("#ff421f"))
        self._draw_door(painter, self.data.water_door, self.water_door_asset, QColor("#27d6ff"))

    def _draw_door(self, painter, rect, asset, fallback):
        visible = self._r(rect)
        if not asset.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("door" + fallback.name(), asset, visible.width(), visible.height()))
        else:
            painter.setBrush(QColor("#353536"))
            painter.setPen(QPen(fallback, 4))
            painter.drawRoundedRect(visible, 6, 6)

    def _draw_diamond(self, painter, diamond):
        visible = self._r(diamond.rect)
        asset = self.asset_diamond_red if diamond.owner == "fire" else self.asset_diamond_blue
        if not asset.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("gem_" + diamond.owner, asset, visible.width(), visible.height()))
        else:
            center = visible.center()
            shape = QPolygonF([QPointF(center.x(), visible.top()), QPointF(visible.right(), center.y()), QPointF(center.x(), visible.bottom()), QPointF(visible.left(), center.y())])
            painter.setBrush(QColor("#ff3939" if diamond.owner == "fire" else "#35d9ff"))
            painter.drawPolygon(shape)

    def _draw_player(self, painter, player, frames, idle, fallback):
        visible = self._r(player.rect)
        pixmap = idle
        if frames and abs(player.vx) > 0.1:
            pixmap = frames[(player.anim // 3) % len(frames)]
        if pixmap.isNull():
            painter.setBrush(fallback)
            painter.drawRoundedRect(visible, 12, 12)
            return
        key = "fire" if player.kind == "fire" else "water"
        sprite = self._scaled_asset(key + str((player.anim // 3) % 8), pixmap, visible.width(), visible.height())
        if player.facing < 0:
            sprite = sprite.transformed(QTransform().scale(-1, 1))
        painter.drawPixmap(visible.toRect(), sprite)

    def _draw_particles(self, painter):
        painter.setPen(Qt.NoPen)
        sx, sy = self._scale()
        for particle in self.particles:
            color = QColor(particle.color)
            color.setAlpha(max(20, min(140, particle.life * 8)))
            painter.setBrush(color)
            painter.drawEllipse(QPointF(particle.x * sx, particle.y * sy), particle.size * sx, particle.size * sy)

    def _draw_timer(self, painter):
        width, height = 152, 54
        x = (self.width() - width) / 2
        painter.setBrush(QColor(35, 35, 35, 235))
        painter.setPen(QPen(QColor("#080808"), 4))
        painter.drawRoundedRect(QRectF(x, 5, width, height), 7, 7)
        seconds = max(0, int(self._gm.time_left))
        text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.setPen(QColor("#ffd42d"))
        painter.drawText(QRectF(x, 5, width, height), Qt.AlignCenter, text)

    def _draw_sound(self, painter):
        self.sound_button_rect = QRectF(self.width() - 64, 12, 48, 48)
        visible = self.sound_button_rect
        if not self.asset_volume.isNull():
            painter.drawPixmap(visible.toRect(), self._scaled_asset("volume", self.asset_volume, visible.width(), visible.height()))
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
        character = self._network.local_character if self._network is not None else ""
        text = f"Nivel {self.level_number} | Tu personaje: {character or '-'} | Mover: A/D o flechas | Saltar: W o arriba"
        painter.drawText(12, self.height() - 12, text)


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
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        top = QHBoxLayout()
        self.lbl_player1 = QLabel("Jugador 1")
        self.lbl_level = QLabel("Nivel 1")
        self.lbl_timer = QLabel(f"Tiempo: {GAME_DURATION_SECONDS}s")
        self.lbl_player2 = QLabel("Jugador 2")
        for label in (self.lbl_player1, self.lbl_level, self.lbl_timer, self.lbl_player2):
            label.setFont(QFont("Arial", 13, QFont.Bold))
            label.setAlignment(Qt.AlignCenter)
            top.addWidget(label)

        self.canvas = GameCanvas(self._gm, self._audio, self._network, self)
        self._create_pause_panel()

        bottom = QHBoxLayout()
        self.lbl_score1 = QLabel("Jugador 1: 0")
        self.lbl_score2 = QLabel("Jugador 2: 0")
        for label in (self.lbl_score1, self.lbl_score2):
            label.setFont(QFont("Arial", 14, QFont.Bold))
            label.setMinimumWidth(220)

        self.lbl_score2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.btn_emerald = QPushButton()
        self.btn_emerald.setObjectName("emeraldButton")
        self.btn_emerald.setFlat(True)
        self.btn_emerald.setFixedSize(82, 82)
        if not self.canvas.asset_pause_emerald.isNull():
            self.btn_emerald.setIcon(QIcon(self.canvas.asset_pause_emerald))
            self.btn_emerald.setIconSize(QSize(74, 74))

        bottom.addWidget(self.lbl_score1)
        bottom.addStretch()
        bottom.addWidget(self.btn_emerald)
        bottom.addStretch()
        bottom.addWidget(self.lbl_score2)

        layout.addLayout(top)
        layout.addWidget(self.canvas, 1)
        layout.addLayout(bottom)
        self._apply_styles()

    def _create_pause_panel(self):
        self.pause_panel = QLabel(self.canvas)
        self.pause_panel.setObjectName("pausePanel")
        self.pause_panel.setScaledContents(True)
        self.pause_panel.hide()

        self.btn_pause = QPushButton(self.pause_panel)
        self.btn_reset = QPushButton(self.pause_panel)
        self.btn_menu = QPushButton(self.pause_panel)
        for button in (self.btn_pause, self.btn_reset, self.btn_menu):
            button.setObjectName("menuHitBox")
            button.setCursor(Qt.PointingHandCursor)

        self.lbl_menu_blue = QLabel("0", self.pause_panel)
        self.lbl_menu_red = QLabel("0", self.pause_panel)
        for label in (self.lbl_menu_blue, self.lbl_menu_red):
            label.setObjectName("menuCount")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def _connect_signals(self):
        self._gm.tick.connect(self._on_tick)
        self._gm.score_changed.connect(self._on_score_changed)
        self.btn_emerald.clicked.connect(self._open_pause_menu)
        self.btn_reset.clicked.connect(self._restart_level)
        self.btn_pause.clicked.connect(self._close_pause_menu)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_pause_panel()

    def _place_pause_panel(self):
        if not hasattr(self, "pause_panel"):
            return
        ratio_w, ratio_h = 620, 632
        max_w = min(480, max(310, self.canvas.width() - 80))
        width = max_w
        height = int(width * ratio_h / ratio_w)
        if height > self.canvas.height() - 40:
            height = self.canvas.height() - 40
            width = int(height * ratio_w / ratio_h)
        x = (self.canvas.width() - width) // 2
        y = max(6, self.canvas.height() - height + 8)
        self.pause_panel.setGeometry(x, y, width, height)
        if not self.canvas.asset_pause_menu.isNull():
            self.pause_panel.setPixmap(self.canvas.asset_pause_menu.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

        self.btn_pause.setGeometry(int(width * 0.19), int(height * 0.20), int(width * 0.62), int(height * 0.12))
        self.btn_reset.setGeometry(int(width * 0.15), int(height * 0.35), int(width * 0.70), int(height * 0.12))
        self.btn_menu.setGeometry(int(width * 0.18), int(height * 0.77), int(width * 0.64), int(height * 0.12))

        count_w = int(width * 0.065)
        count_h = int(height * 0.075)
        self.lbl_menu_blue.setGeometry(int(width * 0.56), int(height * 0.505), count_w, count_h)
        self.lbl_menu_red.setGeometry(int(width * 0.56), int(height * 0.612), count_w, count_h)

        font = QFont("Times New Roman", max(14, width // 20), QFont.Bold)
        self.lbl_menu_blue.setFont(font)
        self.lbl_menu_red.setFont(font)

    def _open_pause_menu(self):
        if not self._gm.is_running:
            return
        self._gm.pause()
        self.canvas.stop()
        self._place_pause_panel()
        self.pause_panel.show()
        self.pause_panel.raise_()
        self.btn_emerald.hide()

    def _close_pause_menu(self):
        self.pause_panel.hide()
        self.btn_emerald.show()
        if self._gm.is_running:
            self._gm.resume()
            self.canvas.start()

    def set_level(self, level_number: int):
        self.current_level = max(1, min(4, int(level_number)))
        self.canvas.set_level(self.current_level)
        self.lbl_level.setText(f"Nivel {self.current_level}")

    def reset(self):
        self.pause_panel.hide()
        self.btn_emerald.show()
        self.lbl_player1.setText(f"{self._gm.name1} ({self._gm.player1})")
        self.lbl_player2.setText(f"{self._gm.name2} ({self._gm.player2})")
        self.lbl_level.setText(f"Nivel {self.current_level}")
        self.lbl_score1.setText(f"{self._gm.name1}: 0")
        self.lbl_score2.setText(f"{self._gm.name2}: 0")
        self.lbl_menu_blue.setText("0")
        self.lbl_menu_red.setText("0")
        self.lbl_timer.setText(f"Tiempo: {GAME_DURATION_SECONDS}s")
        self.canvas.set_level(self.current_level)

    def _restart_level(self):
        self.pause_panel.hide()
        self.btn_emerald.show()
        self._gm.start()
        self.reset()
        self.canvas.start()

    def start_level(self):
        self.pause_panel.hide()
        self.btn_emerald.show()
        self.canvas.start()

    def stop_level(self):
        self.pause_panel.hide()
        self.canvas.stop()

    def show_game_over(self, score1: int, score2: int, winner: str):
        self.pause_panel.hide()
        self.btn_emerald.show()
        message = QMessageBox(self)
        message.setWindowTitle("Nivel terminado")
        message.setText(
            f"<b>Nivel {self.current_level} terminado</b><br><br>"
            f"{self._gm.name1} ({self._gm.player1}): <b>{score1}</b> puntos<br>"
            f"{self._gm.name2} ({self._gm.player2}): <b>{score2}</b> puntos<br><br>"
            f"Resultado: <b>{winner}</b>"
        )
        message.exec()

    def _on_tick(self, seconds: int):
        self.lbl_timer.setText(f"Tiempo: {seconds}s")
        self.lbl_timer.setStyleSheet("color:#ff6767;font-weight:bold;" if seconds <= 10 else "color:#f6dfb4;")

    def _on_score_changed(self, score1: int, score2: int):
        self.lbl_score1.setText(f"{self._gm.name1}: {score1}")
        self.lbl_score2.setText(f"{self._gm.name2}: {score2}")
        fire_score = score1 if self._gm.player1 == "Fireboy" else score2
        water_score = score1 if self._gm.player1 == "Watergirl" else score2
        self.lbl_menu_blue.setText(str(water_score // 10))
        self.lbl_menu_red.setText(str(fire_score // 10))

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color:#141414; color:#f6dfb4; }
            #emeraldButton {
                background-color:transparent; border:none; padding:0px;
            }
            #emeraldButton:hover { background-color:transparent; }
            #pausePanel { background-color:transparent; }
            #menuHitBox {
                background-color:rgba(0, 0, 0, 0);
                border:none;
            }
            #menuCount {
                background-color:#636462;
                color:#f0cf32;
                font-weight:bold;
            }
        """)