"""Núcleo puro del analizador de logs.

Autor: Roberto Flores (25ASAB015)
Actividad: IA como Herramienta, no como Autor: Desarrollo Guiado y Validado de un Script en Python

Este módulo concentra las reglas de validación y clasificación de eventos.
Tanto la interfaz de consola (`main.py`) como el visor web (`docs/index.html` vía Pyodide)
importan este mismo módulo para garantizar resultados idénticos en ambos entornos.
"""

from __future__ import annotations

import datetime
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Niveles exactos en mayúsculas, según el formato [LEVEL].
NIVELES = ("INFO", "WARNING", "ERROR")

# Una línea bien formada es exactamente:
#   [NIVEL] YYYY-MM-DD mensaje-no-vacío
# No se admite hora, zona horaria, ni otros niveles (fuera de alcance).
_RE_BIEN = re.compile(
    r"^\[(INFO|WARNING|ERROR)\] (\d{4}-\d{2}-\d{2}) (.+)$"
)
_RE_NIVEL = re.compile(r"^\[(INFO|WARNING|ERROR)\]")
# Token "parecido a fecha" para diagnosticar ancho incorrecto (p. ej. 2024-1-02).
# No se usa para aceptar el evento: la aceptación exige 4-2-2 y calendario real.
_RE_FECHA_LAXA = re.compile(r"^\d{1,4}-\d{1,2}-\d{1,2}$")
_RE_FECHA_EXACTA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class EventoMalformado:
    """Un evento (línea no vacía) que viola al menos un criterio."""

    linea: int
    razones: list[str]
    texto: str


@dataclass
class Resultado:
    """Totales del análisis.

    Solapamiento (intencional):
    - ``eventos_totales`` = líneas físicas no vacías (en blanco no son eventos).
    - ``malformados`` ⊆ eventos; un evento malformado cuenta UNA vez aunque
      tenga varias razones.
    - Los contadores por nivel incluyen eventos bien formados Y malformados
      cuya severidad sí se reconoció. Un [WARNING] sin fecha suma WARNING y
      también malformado.
    - Severidad desconocida o ausente NO entra en INFO/WARNING/ERROR, pero
      sí en eventos_totales y en malformados.
    Por eso INFO+WARNING+ERROR puede ser menor que eventos_totales, y a la
    vez mayor que (eventos_totales - malformados).
    """

    eventos_totales: int = 0
    por_nivel: dict[str, int] = field(
        default_factory=lambda: {n: 0 for n in NIVELES}
    )
    malformados: int = 0
    lineas_en_blanco: int = 0
    detalle_malformados: list[EventoMalformado] = field(default_factory=list)
    bytes_reemplazados: bool = False


def decodificar(data: bytes) -> tuple[str, bool]:
    """UTF-8 con reemplazo y BOM tratado de forma uniforme.

    Decisión: se usa ``utf-8-sig`` para que un BOM inicial (típico de
    editores Windows) no forme parte de la primera línea, tanto en CLI
    como en la web. Los octetos inválidos se sustituyen por U+FFFD
    (``errors='replace'``) en lugar de abortar: el archivo sigue
    analizándose y esas líneas suelen resultar malformadas. No se lanza
    UnicodeDecodeError en archivos ordinarios.
    """

    reemplazo = b"\xef\xbf\xbd"  # UTF-8 de U+FFFD, para detectar reemplazos
    # utf-8-sig elimina un BOM inicial; errors=replace evita traceback.
    texto = data.decode("utf-8-sig", errors="replace")
    hubo_reemplazo = "\ufffd" in texto
    # Si el archivo original ya contenía U+FFFD válido no lo distinguimos;
    # para la evidencia basta documentar el comportamiento de octetos inválidos.
    _ = reemplazo
    return texto, hubo_reemplazo


def _es_calendario_real(fecha: str) -> bool:
    """Comprueba que YYYY-MM-DD exista en el calendario gregoriano.

    Se construye ``datetime.date`` a partir de enteros. No se usa
    ``strptime`` como criterio de formato: en CPython 3.12 ``strptime`` con
    ``%Y-%m-%d`` acepta ``2024-1-2`` (sin ceros a la izquierda). Esa
    permisividad se demostró experimentalmente (evidencia/experimento_strptime.txt)
    y se corrige exigiendo el ancho ASCII 4-2-2 *antes* de esta función.
    """

    try:
        anio = int(fecha[0:4])
        mes = int(fecha[5:7])
        dia = int(fecha[8:10])
        datetime.date(anio, mes, dia)
    except ValueError:
        return False
    return True


def _token_fecha_y_resto(texto: str, match_nivel: re.Match[str] | None) -> tuple[str | None, str]:
    """Localiza un candidato a fecha y el texto que le sigue (diagnóstico).

    Si hay severidad reconocida, el candidato está en el primer token
    posterior a ``[NIVEL]``. Así, ``[WARNING] Invalid password attempt`` no
    toma una fecha que pudiera aparecer más adelante en el mensaje.
    """

    if match_nivel is not None:
        resto = texto[match_nivel.end() :]
        if resto.startswith(" "):
            partes = resto[1:].split(" ", 1)
            token = partes[0] if partes else ""
            mensaje = partes[1] if len(partes) > 1 else ""
            return (token or None), mensaje
        return None, resto

    for token in texto.split():
        if _RE_FECHA_LAXA.fullmatch(token):
            idx = texto.find(token)
            return token, texto[idx + len(token) :]
    return None, ""


def analizar_linea(texto: str) -> tuple[str | None, list[str]]:
    """Devuelve (nivel reconocido o None, lista de razones de malformación).

    Lista vacía de razones = evento bien formado.
    Varias razones siguen siendo UN solo evento malformado.
    """

    match_nivel = _RE_NIVEL.match(texto)
    nivel = match_nivel.group(1) if match_nivel else None
    razones: list[str] = []

    match_bien = _RE_BIEN.fullmatch(texto)
    if match_bien is not None:
        fecha = match_bien.group(2)
        mensaje = match_bien.group(3)
        # El grupo fecha ya tiene ancho 4-2-2 por la regex; falta el calendario.
        if not _es_calendario_real(fecha):
            razones.append("fecha no es una fecha de calendario real")
        if mensaje.strip() == "":
            razones.append("mensaje vacío o ausente")
        return nivel, razones

    if nivel is None:
        razones.append(
            "severidad ausente o no reconocida "
            "(se exige [INFO], [WARNING] o [ERROR] en mayúsculas exactas)"
        )

    token, mensaje = _token_fecha_y_resto(texto, match_nivel)
    if token is None or not _RE_FECHA_LAXA.fullmatch(token):
        razones.append("fecha ausente")
    elif not _RE_FECHA_EXACTA.fullmatch(token):
        razones.append(
            "fecha con formato incorrecto "
            "(se exige YYYY-MM-DD con dígitos ASCII de ancho exacto 4-2-2)"
        )
    elif not _es_calendario_real(token):
        razones.append("fecha no es una fecha de calendario real")

    if token is None or not _RE_FECHA_LAXA.fullmatch(token):
        # Sin fecha: el resto después del nivel, si existe, cuenta como mensaje.
        if match_nivel is not None and texto[match_nivel.end() :].strip() == "":
            razones.append("mensaje vacío o ausente")
    elif mensaje.strip() == "":
        razones.append("mensaje vacío o ausente")

    if not razones:
        # Nivel, fecha 4-2-2 válida y mensaje presentes, pero la línea no
        # coincidió con el patrón exacto (p. ej. falta el espacio tras ]).
        razones.append(
            "estructura distinta de '[NIVEL] YYYY-MM-DD mensaje' no vacío"
        )
    return nivel, razones


def analizar_texto(texto: str, bytes_reemplazados: bool = False) -> Resultado:
    """Analiza el contenido ya decodificado. Línea física no vacía = evento."""

    resultado = Resultado(bytes_reemplazados=bytes_reemplazados)
    # splitlines() trata \n, \r\n y \r de forma uniforme; no se piden
    # eventos multilínea (fuera de alcance).
    for indice, cruda in enumerate(texto.splitlines(), start=1):
        if cruda.strip() == "":
            resultado.lineas_en_blanco += 1
            continue
        resultado.eventos_totales += 1
        nivel, razones = analizar_linea(cruda)
        if nivel is not None:
            resultado.por_nivel[nivel] += 1
        if razones:
            resultado.malformados += 1
            resultado.detalle_malformados.append(
                EventoMalformado(linea=indice, razones=razones, texto=cruda)
            )
    return resultado


def analizar_bytes(data: bytes) -> Resultado:
    texto, reemplazos = decodificar(data)
    return analizar_texto(texto, bytes_reemplazados=reemplazos)


def analizar_archivo(ruta: str | Path) -> Resultado:
    """Lee un archivo. Las excepciones de E/S se dejan al CLI para no trazar."""

    data = Path(ruta).read_bytes()
    return analizar_bytes(data)


def formatear_informe(resultado: Resultado, origen: str) -> str:
    """Informe en español para consola y para el recuadro de la web."""

    lineas = [
        f"Origen: {origen}",
        f"Líneas en blanco ignoradas: {resultado.lineas_en_blanco}",
        f"Eventos totales: {resultado.eventos_totales}",
        f"  INFO: {resultado.por_nivel['INFO']}",
        f"  WARNING: {resultado.por_nivel['WARNING']}",
        f"  ERROR: {resultado.por_nivel['ERROR']}",
        f"Eventos malformados/incompletos: {resultado.malformados}",
    ]
    if resultado.bytes_reemplazados:
        lineas.append(
            "Aviso: se sustituyeron octetos inválidos por U+FFFD "
            "(UTF-8 con replacement)."
        )
    if resultado.detalle_malformados:
        lineas.append("")
        lineas.append("Detalle de malformados (una cuenta por línea, aunque haya varias razones):")
        for item in resultado.detalle_malformados:
            razones = "; ".join(item.razones)
            lineas.append(f"  - línea {item.linea}: {razones}")
    lineas.append("")
    lineas.append(
        "Solapamiento: el total de eventos es el de líneas no vacías. "
        "Un evento malformado con severidad reconocida suma en su nivel Y en "
        "malformados. Una severidad desconocida no suma en INFO/WARNING/ERROR."
    )
    return "\n".join(lineas) + "\n"


def resultado_a_dict(resultado: Resultado) -> dict[str, Any]:
    """Estructura JSON-serializable para la UI (mismos números que el CLI)."""

    return {
        "eventos_totales": resultado.eventos_totales,
        "por_nivel": dict(resultado.por_nivel),
        "malformados": resultado.malformados,
        "lineas_en_blanco": resultado.lineas_en_blanco,
        "bytes_reemplazados": resultado.bytes_reemplazados,
        "detalle_malformados": [asdict(item) for item in resultado.detalle_malformados],
        "informe": formatear_informe(resultado, origen="(memoria)"),
    }


def resultado_a_json(resultado: Resultado) -> str:
    return json.dumps(resultado_a_dict(resultado), ensure_ascii=False)
