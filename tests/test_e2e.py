"""E2E mínimo vía subprocess: CLI real, no mocks del analizador.

Los conteos de los fixtures están anclados en pruebas/esperados.md
(calculados a mano antes de ejecutar este archivo).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAIN = RAIZ / "main.py"
BIEN = RAIZ / "pruebas" / "bien_formado.log"
MAL = RAIZ / "pruebas" / "con_errores.log"


def correr(*args: str, entrada: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        input=entrada,
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        env={**os.environ, "PYTHONPATH": str(RAIZ)},
    )


def campo(salida: str, etiqueta: str) -> int:
    for linea in salida.splitlines():
        if linea.startswith(etiqueta):
            return int(linea.split(":")[-1].strip())
    raise AssertionError(f"no se encontró {etiqueta!r} en:\n{salida}")


class TestFixtures(unittest.TestCase):
    def test_bien_formado_coincide_con_esperados(self) -> None:
        proc = correr(str(BIEN))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertNotIn("Traceback", proc.stdout)
        self.assertEqual(campo(proc.stdout, "Eventos totales"), 6)
        self.assertEqual(campo(proc.stdout, "  INFO"), 3)
        self.assertEqual(campo(proc.stdout, "  WARNING"), 2)
        self.assertEqual(campo(proc.stdout, "  ERROR"), 1)
        self.assertEqual(campo(proc.stdout, "Eventos malformados/incompletos"), 0)
        self.assertEqual(campo(proc.stdout, "Líneas en blanco ignoradas"), 0)

    def test_con_errores_coincide_con_esperados(self) -> None:
        proc = correr(str(MAL))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(campo(proc.stdout, "Eventos totales"), 8)
        self.assertEqual(campo(proc.stdout, "  INFO"), 3)
        self.assertEqual(campo(proc.stdout, "  WARNING"), 1)
        self.assertEqual(campo(proc.stdout, "  ERROR"), 1)
        self.assertEqual(campo(proc.stdout, "Eventos malformados/incompletos"), 7)
        self.assertEqual(campo(proc.stdout, "Líneas en blanco ignoradas"), 2)
        self.assertIn("línea 1:", proc.stdout)
        self.assertIn("fecha ausente", proc.stdout)
        self.assertIn("línea 10:", proc.stdout)
        self.assertIn("ancho exacto 4-2-2", proc.stdout)


class TestSeleccionYErroresDeArchivo(unittest.TestCase):
    def test_seleccion_interactiva(self) -> None:
        proc = correr(entrada=f"{BIEN}\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(campo(proc.stdout, "Eventos totales"), 6)

    def test_archivo_inexistente_sin_traceback(self) -> None:
        proc = correr(str(RAIZ / "no_existe_este_log.log"))
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertNotIn("Traceback", proc.stdout)
        self.assertIn("no se encontró", proc.stderr.lower())

    def test_archivo_vacio(self) -> None:
        with tempfile.NamedTemporaryFile("wb", suffix=".log", delete=False) as tmp:
            ruta = tmp.name
        try:
            proc = correr(ruta)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(campo(proc.stdout, "Eventos totales"), 0)
            self.assertEqual(campo(proc.stdout, "Eventos malformados/incompletos"), 0)
            self.assertEqual(campo(proc.stdout, "  INFO"), 0)
        finally:
            os.unlink(ruta)


class TestFechasCalendarioYAncho(unittest.TestCase):
    def _analizar(self, contenido: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8") as tmp:
            tmp.write(contenido)
            ruta = tmp.name
        try:
            proc = correr(ruta)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout
        finally:
            os.unlink(ruta)

    def test_bisiesto_2024_02_29_valido(self) -> None:
        out = self._analizar("[INFO] 2024-02-29 dia bisiesto valido\n")
        self.assertEqual(campo(out, "Eventos totales"), 1)
        self.assertEqual(campo(out, "  INFO"), 1)
        self.assertEqual(campo(out, "Eventos malformados/incompletos"), 0)

    def test_no_bisiesto_2023_02_29_invalido(self) -> None:
        out = self._analizar("[INFO] 2023-02-29 no bisiesto\n")
        self.assertEqual(campo(out, "Eventos totales"), 1)
        self.assertEqual(campo(out, "  INFO"), 1)
        self.assertEqual(campo(out, "Eventos malformados/incompletos"), 1)
        self.assertIn("calendario real", out)

    def test_ancho_fecha_sin_ceros_es_malformado(self) -> None:
        # Contrasta con datetime.strptime(..., '%Y-%m-%d'), que acepta 2024-1-2.
        out = self._analizar("[INFO] 2024-1-2 ancho insuficiente\n")
        self.assertEqual(campo(out, "Eventos totales"), 1)
        self.assertEqual(campo(out, "  INFO"), 1)
        self.assertEqual(campo(out, "Eventos malformados/incompletos"), 1)
        self.assertIn("4-2-2", out)


if __name__ == "__main__":
    unittest.main()
