import random
import string
from config import DEFAULT_HOST, DEFAULT_PORT


class NetworkManager:

    def __init__(self):
        self._state = "idle"
        self._code  = ""
        self._host  = DEFAULT_HOST
        self._port  = DEFAULT_PORT

    @property
    def state(self) -> str:
        return self._state

    @property
    def room_code(self) -> str:
        return self._code

    def create_room(self) -> str:
        self._code  = self._gen_code()
        self._state = "hosting"
        print(f"[Network] Sala creada: {self._code}  ({self._host}:{self._port})")
        return self._code

    def join_room(self, code: str) -> bool:
        code = code.strip().upper()
        if len(code) != 6:
            print(f"[Network] Código inválido: '{code}'")
            return False
        self._code  = code
        self._state = "connected"
        print(f"[Network] Unido a sala: {self._code}")
        return True

    def disconnect(self):
        print(f"[Network] Desconectado de sala: {self._code}")
        self._state = "idle"
        self._code  = ""

    @staticmethod
    def _gen_code() -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=6))