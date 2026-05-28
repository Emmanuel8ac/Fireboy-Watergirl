import json
import random
import socket
import string
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from config import DEFAULT_HOST, DEFAULT_PORT

# Puerto usado para encontrar salas en la red
DISCOVERY_PORT = DEFAULT_PORT + 1


# Envía datos entre los dos jugadores
class NetworkManager(QObject):
    # Señales recibidas por las pantallas
    remote_input_received = Signal(object)
    remote_character_selected = Signal(str, str)
    remote_name_received = Signal(str)
    status_changed = Signal(str)
    client_connected = Signal()
    session_ready = Signal(object)
    remote_action_received = Signal(str)

    # Estado inicial de la conexión
    def __init__(self):
        super().__init__()
        self._state = "idle"
        self._code = ""
        self._host = DEFAULT_HOST
        self._port = DEFAULT_PORT
        self._sock: Optional[socket.socket] = None
        self._server: Optional[socket.socket] = None
        self._running = False
        self._send_lock = threading.Lock()
        self._remote_keys = set()
        self._local_character = ""
        self._remote_character = ""
        self._local_name = ""
        self._remote_name = ""
        self._connected = False
        self._last_error = ""

    # Datos disponibles para la interfaz
    @property
    def state(self) -> str:
        return self._state

    # Devuelve el código de la sala
    @property
    def room_code(self) -> str:
        return self._code

    # Devuelve el último error de conexión
    @property
    def last_error(self) -> str:
        return self._last_error

    # Devuelve las teclas del otro jugador
    @property
    def remote_keys(self) -> set:
        return set(self._remote_keys)

    # Devuelve el personaje elegido localmente
    @property
    def local_character(self) -> str:
        return self._local_character

    # Devuelve el personaje elegido en el otro equipo
    @property
    def remote_character(self) -> str:
        return self._remote_character

    # Devuelve el nombre del jugador local
    @property
    def local_name(self) -> str:
        return self._local_name

    # Devuelve el nombre del otro jugador
    @property
    def remote_name(self) -> str:
        return self._remote_name

    # Cambia un dato del programa
    def set_local_name(self, name: str):
        self._local_name = self._clean_name(name)

    # Comprueba el estado actual
    def is_host(self) -> bool:
        return self._state == "hosting"

    # Comprueba el estado actual
    def is_client(self) -> bool:
        return self._state == "client"

    # Comprueba el estado actual
    def is_online(self) -> bool:
        return self._state in ("hosting", "client")

    # Comprueba el estado actual
    def is_connected(self) -> bool:
        return self._connected or (self._sock is not None and self._state == "client")

    # Crea una sala para el anfitrión
    def create_room(self) -> str:
        saved_name = self._local_name
        self.disconnect()
        self._local_name = saved_name
        self._code = self._generate_code()
        self._state = "hosting"
        self._running = True
        self._last_error = ""
        self._host = self._local_ip()

        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind(("", DEFAULT_PORT))
            self._server.listen(1)
        except OSError as error:
            self._last_error = f"No pude crear el servidor: {error}"
            self.status_changed.emit(self._last_error)
            self.disconnect()
            return ""

        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        self.status_changed.emit(f"Servidor creado: {self._code}. Comparte el código con el otro jugador.")
        return self._code

    # Une al invitado mediante el código
    def join_room(self, code: str, timeout: float = 7.0) -> bool:
        saved_name = self._local_name
        self.disconnect()
        self._local_name = saved_name
        code = code.strip().upper()
        if len(code) != 6 or not code.isalnum():
            self._last_error = "El código debe tener 6 letras o números."
            return False

        self._code = code
        self._last_error = "Buscando el servidor en la red local..."
        self.status_changed.emit(self._last_error)
        found = self._discover_room(code, timeout=timeout)
        if not found:
            self._last_error = "No encontré la sala. Revisa que ambos estén en la misma red WiFi."
            self.status_changed.emit(self._last_error)
            return False

        host, port = found
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5)
            self._sock.connect((host, int(port)))
            self._sock.settimeout(None)
            self._state = "client"
            self._running = True
            self._connected = True
            threading.Thread(target=self._receive_loop, args=(self._sock,), daemon=True).start()
            self.send_player_name()
            self.status_changed.emit(f"Conectado a la sala {code}.")
            return True
        except OSError as error:
            self._last_error = f"No pude conectarme a la sala: {error}"
            self.status_changed.emit(self._last_error)
            self.disconnect()
            return False

    # Envía nombre, controles y selección
    def send_player_name(self):
        if self.is_online() and self._sock is not None and self._local_name:
            self._send({"type": "player_name", "name": self._local_name})

    # Envía las teclas presionadas
    def send_input(self, keys):
        if self.is_online() and self._sock is not None:
            self._send({"type": "input", "keys": sorted(list(keys))})

    # Envía el personaje elegido
    def send_character_choice(self, character: str):
        if character not in ("", "Fireboy", "Watergirl"):
            return
        self._local_character = character
        if self.is_online() and self._sock is not None:
            self._send({
                "type": "character_choice",
                "character": character,
                "name": self._local_name,
            })

    # Envía el nivel elegido
    def send_session_setup(self, level_number: int, player1: str, player2: str):
        if not self.is_host() or not self.is_connected():
            return
        self._send({
            "type": "session_setup",
            "level": int(level_number),
            "player1": player1,
            "player2": player2,
            "player1_name": self._local_name,
            "player2_name": self._remote_name,
        })

    # Envía acciones del menú durante la partida
    def send_game_action(self, action: str):
        if action not in ("pause", "resume", "restart", "menu"):
            return
        if self.is_connected() and self._sock is not None:
            self._send({"type": "game_action", "action": action})

    # Cierra la conexión actual
    def disconnect(self, clear_name: bool = False):
        self._running = False
        self._remote_keys = set()
        self._local_character = ""
        self._remote_character = ""
        self._remote_name = ""
        if clear_name:
            self._local_name = ""
        for active_socket in (self._sock, self._server):
            if active_socket:
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    active_socket.close()
                except OSError:
                    pass
        self._sock = None
        self._connected = False
        self._server = None
        self._state = "idle"
        self._code = ""

    # Escucha mensajes del otro jugador
    def _accept_loop(self):
        try:
            client, address = self._server.accept()
            if not self._running:
                client.close()
                return
            self._sock = client
            self._connected = True
            self.status_changed.emit(f"Jugador conectado desde {address[0]}.")
            self.send_player_name()
            self.client_connected.emit()
            self._receive_loop(client)
        except OSError:
            return

    # Recibe mensajes por red
    def _receive_loop(self, active_socket: socket.socket):
        buffer = ""
        while self._running:
            try:
                data = active_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self._read_message(json.loads(line))
            except (OSError, json.JSONDecodeError):
                break
        if self._running:
            self.status_changed.emit("El otro jugador se desconectó.")
        self._sock = None
        self._connected = False

    # Procesa un mensaje recibido
    def _read_message(self, message: dict):
        message_type = message.get("type")
        if message_type == "input":
            self._remote_keys = set(message.get("keys", []))
            self.remote_input_received.emit(self._remote_keys)
        elif message_type == "player_name":
            self._remote_name = self._clean_name(str(message.get("name", "")))
            self.remote_name_received.emit(self._remote_name)
        elif message_type == "character_choice":
            character = str(message.get("character", ""))
            name = self._clean_name(str(message.get("name", "")))
            if name:
                self._remote_name = name
                self.remote_name_received.emit(name)
            if character in ("", "Fireboy", "Watergirl"):
                self._remote_character = character
                self.remote_character_selected.emit(character, self._remote_name)
        elif message_type == "session_setup":
            self.session_ready.emit(message)
        elif message_type == "game_action":
            action = str(message.get("action", ""))
            if action in ("pause", "resume", "restart", "menu"):
                self.remote_action_received.emit(action)

    # Envía un mensaje por red
    def _send(self, message: dict):
        try:
            payload = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
            with self._send_lock:
                if self._sock:
                    self._sock.sendall(payload)
        except OSError:
            self.status_changed.emit("No pude enviar los datos al otro jugador.")

    # Publica y busca salas disponibles
    def _broadcast_loop(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self._running and self._state == "hosting":
            message = json.dumps({
                "type": "fireboy_room",
                "code": self._code,
                "host": self._local_ip(),
                "port": DEFAULT_PORT,
            }).encode("utf-8")
            try:
                udp_socket.sendto(message, ("255.255.255.255", DISCOVERY_PORT))
            except OSError:
                pass
            time.sleep(1.0)
        udp_socket.close()

    # Busca una sala disponible
    def _discover_room(self, code: str, timeout: float):
        end_time = time.time() + timeout
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp_socket.bind(("", DISCOVERY_PORT))
            udp_socket.settimeout(0.7)
            while time.time() < end_time:
                try:
                    data, address = udp_socket.recvfrom(2048)
                    message = json.loads(data.decode("utf-8", errors="ignore"))
                    if message.get("type") == "fireboy_room" and message.get("code") == code:
                        return message.get("host") or address[0], int(message.get("port", DEFAULT_PORT))
                except socket.timeout:
                    continue
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
        finally:
            udp_socket.close()
        return None

    # Prepara nombres y códigos de sala
    @staticmethod
    def _clean_name(name: str) -> str:
        return " ".join(name.strip().split())[:18]

    # Genera el código de sala
    @staticmethod
    def _generate_code() -> str:
        characters = string.ascii_uppercase + string.digits
        return "".join(random.choices(characters, k=6))

    # Obtiene la dirección de red
    @staticmethod
    def _local_ip() -> str:
        active_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            active_socket.connect(("8.8.8.8", 80))
            return active_socket.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())
        finally:
            active_socket.close()
