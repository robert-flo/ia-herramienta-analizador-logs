"""Comprueba paridad CLI/web en el navegador (no solo el render de la página).

Sirve el repo por HTTP, carga docs/index.html, espera Pyodide, selecciona
los fixtures y compara los números del DOM con el CLI. Guarda capturas.
"""

from __future__ import annotations

import subprocess
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

RAIZ = Path(__file__).resolve().parents[1]
EVID = RAIZ / "evidencia"
BIEN = RAIZ / "pruebas" / "bien_formado.log"
MAL = RAIZ / "pruebas" / "con_errores.log"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RAIZ), **kwargs)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def cli_campos(ruta: Path) -> dict[str, str]:
    proc = subprocess.run(
        [sys.executable, str(RAIZ / "main.py"), str(ruta)],
        capture_output=True,
        text=True,
        cwd=str(RAIZ),
        check=True,
    )
    out = proc.stdout

    def n(etiqueta: str) -> str:
        for linea in out.splitlines():
            if linea.startswith(etiqueta):
                return linea.split(":")[-1].strip()
        raise RuntimeError(etiqueta)

    return {
        "total": n("Eventos totales"),
        "info": n("  INFO"),
        "warning": n("  WARNING"),
        "error": n("  ERROR"),
        "mal": n("Eventos malformados/incompletos"),
        "blanco": n("Líneas en blanco ignoradas"),
        "informe": out,
    }


def main() -> int:
    EVID.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/docs/index.html"

    from playwright.sync_api import sync_playwright

    esperado_bien = cli_campos(BIEN)
    esperado_mal = cli_campos(MAL)
    notas = [f"URL local: {url}", f"Python: {sys.version}"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                channel="chrome",
                args=["--no-sandbox"],
            )
            page = browser.new_page(viewport={"width": 1100, "height": 900})
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_function(
                """() => {
                  const t = document.getElementById('estado')?.textContent || '';
                  return t.includes('Listo') || t.includes('No se pudo');
                }""",
                timeout=120000,
            )
            estado = page.inner_text("#estado")
            notas.append(f"Estado tras carga: {estado}")
            if "No se pudo" in estado:
                page.screenshot(path=str(EVID / "web_error_carga.png"), full_page=True)
                raise SystemExit(f"Pyodide no arrancó: {estado}")

            def comprobar(ruta: Path, esperado: dict[str, str], nombre: str) -> None:
                page.set_input_files("#archivo", str(ruta))
                page.wait_for_function(
                    "() => document.getElementById('resultados') && "
                    "!document.getElementById('resultados').classList.contains('oculto')",
                    timeout=30000,
                )
                # Espera a que el total coincida (el input change es async).
                page.wait_for_function(
                    """(total) => document.getElementById('n-total')?.textContent === total""",
                    arg=esperado["total"],
                    timeout=30000,
                )
                obtenidos = {
                    "total": page.inner_text("#n-total"),
                    "info": page.inner_text("#n-info"),
                    "warning": page.inner_text("#n-warning"),
                    "error": page.inner_text("#n-error"),
                    "mal": page.inner_text("#n-mal"),
                    "blanco": page.inner_text("#n-blanco"),
                }
                notas.append(f"{nombre} CLI={ {k: esperado[k] for k in obtenidos} }")
                notas.append(f"{nombre} WEB={obtenidos}")
                for k, v in obtenidos.items():
                    if v != esperado[k]:
                        raise SystemExit(
                            f"Paridad fallida en {nombre}.{k}: web={v!r} cli={esperado[k]!r}"
                        )
                shot = EVID / f"web_{nombre}.png"
                page.screenshot(path=str(shot), full_page=True)
                notas.append(f"captura: {shot}")

            comprobar(BIEN, esperado_bien, "bien_formado")
            comprobar(MAL, esperado_mal, "con_errores")
            browser.close()
    finally:
        server.shutdown()

    (EVID / "web_paridad.txt").write_text("\n".join(notas) + "\n", encoding="utf-8")
    print("\n".join(notas))
    print("PARIDAD OK")
    return 0


if __name__ == "__main__":
    # Pequeña espera por si el servidor tarda en bind; ThreadingHTTPServer ya está listo.
    time.sleep(0.05)
    sys.exit(main())
