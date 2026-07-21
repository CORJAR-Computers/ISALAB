#!/usr/bin/env python3
"""Script temporal para eliminar directorios ISALAB-fase* redundantes."""
import shutil
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
dirs_to_remove = [
    "ISALAB-fase 1",
    "ISALAB-fase2",
    "ISALAB-fase3",
    "ISALAB-fase4",
    "ISALAB-fase5",
    "ISALAB-fase6",
]

removed = []
failed = []

for d in dirs_to_remove:
    target = ROOT / d
    if target.exists():
        try:
            shutil.rmtree(target)
            removed.append(d)
            print(f"  OK Eliminado: {d}")
        except Exception as e:
            failed.append((d, str(e)))
            print(f"  FAIL Error eliminando {d}: {e}")
    else:
        print(f"  SKIP No existe: {d}")

print(f"\nResumen: {len(removed)} eliminados, {len(failed)} fallidos")

if failed:
    for name, err in failed:
        print(f"  FALLO: {name} - {err}")

# Auto-eliminarse
try:
    os.remove(__file__)
    print("\nScript temporal eliminado correctamente.")
except Exception as e:
    print(f"\nNo se pudo auto-eliminar el script: {e}")
