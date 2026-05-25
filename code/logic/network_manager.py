import json
import random
import socket
import string
import threading
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal

from config import DEFAULT_HOST, DEFAULT_PORT

DISCOVERY_PORT = DEFAULT_PORT + 1


class NetworkManager(QObject):

    remote_input_received = Signal(object)
    status_changed = Signal(str)
    client_connected = Signal()

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
        self._connected = False
        self._last_error = ""

    @property
    def state(self) -> str:
        return self._state

    @property
    def room_code(self) -> str:
        return self._code

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def remote_keys(self) -> set:
        return set(self._remote_keys)

    def is_host(self) -> bool:
        return self._state == "hosting"

    def is_client(self) -> bool:
        return self._state == "client"

    def is_online(self) -> bool:
        return self._state in ("hosting", "client")

    def is_connected(self) -> bool:
        return self._connected or (self._sock is not None and self._state == "client")

    def create_room(self) -> str:
        self.disconnect()
        self._code = self._gen_code()
        self._state = "hosting"
        self._running = True
        self._last_error = ""
        self._host = self._local_ip()

        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("", DEFAULT_PORT))
        self._server.listen(1)

        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        self.status_changed.emit(f"Sala creada: {self._code}. Comparte el código con el otro jugador.")
        return self._code

    def join_room(self, code: str, timeout: float = 7.0) -> bool:
        self.disconnect()
        code = code.strip().upper()
        if len(code) != 6 or not code.isalnum():
            self._last_error = "El código debe tener 6 letras o números."
            return False

        self._code = code
        self._last_error = "Buscando sala en la red local..."
        self.status_changed.emit(self._last_error)
        found = self._discover_room(code, timeout=timeout)
        if not found:
            self._last_error = "No encontré esa sala. Asegúrate de estar en el mismo WiFi y que el host ya haya creado la partida."
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
            threading.Thread(target=self._recv_loop, args=(self._sock,), daemon=True).start()
            self.status_changed.emit(f"Conectado a la sala {code}.")
            return True
        except OSError as exc:
            self._last_error = f"No pude conectarme a la sala: {exc}"
            self.status_changed.emit(self._last_error)
            self.disconnect()
            return False

    def send_input(self, keys):
        if not self.is_online() or self._sock is None:
            return
        self._send({"type": "input", "keys": sorted(list(keys))})

    def disconnect(self):
        self._running = False
        self._remote_keys = set()
        for s in (self._sock, self._server):
            if s:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    s.close()
                except OSError:
                    pass
        self._sock = None
        self._connected = False
        self._server = None
        self._state = "idle"
        self._code = ""

    def _accept_loop(self):
        try:
            client, addr = self._server.accept()
            if not self._running:
                client.close()
                return
            self._sock = client
            self._connected = True
            self.status_changed.emit(f"Jugador conectado desde {addr[0]}.")
            self.client_connected.emit()
            self._recv_loop(client)
        except OSError:
            return

    def _recv_loop(self, sock: socket.socket):
        buffer = ""
        while self._running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    if msg.get("type") == "input":
                        self._remote_keys = set(msg.get("keys", []))
                        self.remote_input_received.emit(self._remote_keys)
            except (OSError, json.JSONDecodeError):
                break
        if self._running:
            self.status_changed.emit("El otro jugador se desconectó.")
        self._sock = None
        self._connected = False

    def _send(self, msg: dict):
        try:
            payload = (json.dumps(msg, separators=(",", ":")) + "\n").encode("utf-8")
            with self._send_lock:
                if self._sock:
                    self._sock.sendall(payload)
        except OSError:
            self.status_changed.emit("No se pudo enviar información al otro jugador.")

    def _broadcast_loop(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = lambda: json.dumps({
            "type": "fireboy_room",
            "code": self._code,
            "host": self._local_ip(),
            "port": DEFAULT_PORT,
        }).encode("utf-8")
        while self._running and self._state == "hosting":
            try:
                udp.sendto(msg(), ("255.255.255.255", DISCOVERY_PORT))
            except OSError:
                pass
            time.sleep(1.0)
        udp.close()

    def _discover_room(self, code: str, timeout: float):
        end = time.time() + timeout
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind(("", DISCOVERY_PORT))
            udp.settimeout(0.7)
            while time.time() < end:
                try:
                    data, addr = udp.recvfrom(2048)
                    msg = json.loads(data.decode("utf-8", errors="ignore"))
                    if msg.get("type") == "fireboy_room" and msg.get("code") == code:
                        return msg.get("host") or addr[0], int(msg.get("port", DEFAULT_PORT))
                except socket.timeout:
                    continue
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
        finally:
            udp.close()
        return None

    @staticmethod
    def _gen_code() -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=6))

    @staticmethod
    def _local_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
