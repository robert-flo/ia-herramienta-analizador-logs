#!/usr/bin/env python3
"""CLI del analizador de logs.

Uso:
  python3 main.py ruta/al/archivo.log
  python3 main.py          # pide la ruta de forma interactiva

La ruta la elige el usuario (argumento posicional o prompt). No se envía
nada a un servidor. Los errores ordinarios de archivo se informan en
español y terminan con código distinto de cero, sin traceback.
"""

from __future__ import annotations

import sys
from pathlib import Path

from analizador import analizar_archivo, formatear_informe


def _obtener_ruta(argv: list[str]) -> str | None:
    if len(argv) > 1:
        return argv[1]
    try:
        return input("Ruta del archivo de log: ").strip()
    except EOFError:
        print("Error: no se proporcionó una ruta.", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    ruta = _obtener_ruta(argv)
    if not ruta:
        print("Error: la ruta está vacía.", file=sys.stderr)
        return 1

    camino = Path(ruta)
    try:
        resultado = analizar_archivo(camino)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {ruta!r}.", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: {ruta!r} es un directorio, no un archivo.", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: sin permiso para leer {ruta!r}.", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error al leer el archivo {ruta!r}: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(formatear_informe(resultado, origen=str(camino)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
