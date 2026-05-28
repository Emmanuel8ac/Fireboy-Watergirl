from pathlib import Path
from PySide6.QtCore import QRectF


# Forma rutas dentro del proyecto
def project_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[1].joinpath(*parts)


# Crea rectángulos para interfaces o colisiones
def rect(x: float, y: float, w: float, h: float) -> QRectF:
    return QRectF(float(x), float(y), float(w), float(h))


# Mantiene un valor dentro de un rango
def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
