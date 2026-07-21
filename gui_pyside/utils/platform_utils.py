# gui_pyside/utils/platform_utils.py
"""Utilidades multiplataforma para la GUI de IsaLab.

Fase 4 (C4): el código de `muestra_dialog.py` llamaba directamente
`os.startfile(filepath)` para abrir el PDF generado. `os.startfile`
SOLO existe en Windows; en macOS/Linux levanta
`AttributeError: module 'os' has no attribute 'startfile'` y rompe
los botones "🖨️ Guardar e Imprimir PDF" y "🖨️ Imprimir Resultados Pro".

Este módulo expone `open_file_externally(filepath)` que usa el
comando nativo de cada sistema operativo:

* Windows  → `os.startfile(filepath)`
* macOS    → `open filepath`
* Linux    → `xdg-open filepath`

El helper no bloquea el hilo de la GUI: dispara el visor en un
subproceso desechable y reporta cualquier error sin levantar.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Union

from utils.logger import setup_logger

logger = setup_logger()

PathLike = Union[str, "os.PathLike[str]"]


def open_file_externally(filepath: PathLike) -> bool:
    """Abre un archivo con la aplicación predeterminada del SO.

    Devuelve `True` si la llamada al visor se dispatchó sin error
    (no garantiza que el visor haya abierto el archivo — solo que
    el comando arrancó). Devuelve `False` si no se pudo iniciar
    el visor o si el archivo no existe.

    Es intencionalmente tolerante: en caso de error se loguea y
    se devuelve `False`, para no romper flujos críticos como el
    guardado de resultados.
    """
    path = Path(filepath)
    if not path.exists():
        logger.error(
            f"open_file_externally: el archivo no existe: {path}")
        return False

    try:
        if sys.platform.startswith("win"):
            # Windows: `os.startfile` solo existe aquí.
            os.startfile(str(path))  # type: ignore[attr-defined]
            logger.info(f"open_file_externally (win): {path}")
            return True
        elif sys.platform == "darwin":
            # macOS: comando `open`.
            subprocess.Popen(
                ["open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            logger.info(f"open_file_externally (mac): {path}")
            return True
        else:
            # Linux / *BSD / Solaris: `xdg-open`.
            subprocess.Popen(
                ["xdg-open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            logger.info(f"open_file_externally (linux): {path}")
            return True
    except FileNotFoundError as e:
        # El visor nativo no está instalado (p.ej. contenedores
        # sin `xdg-utils`). No es un error de la app — lo dejamos
        # registrado para el usuario sin propagar la excepción.
        logger.error(
            f"open_file_externally: visor no disponible en {sys.platform}: {e}")
        return False
    except Exception as e:
        logger.error(f"open_file_externally: error inesperado: {e}")
        return False
