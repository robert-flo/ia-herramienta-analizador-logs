# Documento de Reflexión Técnica

- **Actividad Individual:** IA como Herramienta, no como Autor: Desarrollo Guiado y Validado de un Script en Python
- **Módulo:** Semana 3 – IA-first mindset
- **Estudiante:** Roberto Flores (`25ASAB015` · `25asab015@ujmd.edu.sv`)
- **Repositorio GitHub:** [https://github.com/robert-flo/ia-herramienta-analizador-logs](https://github.com/robert-flo/ia-herramienta-analizador-logs)
- **Demo Web Interactiva:** [https://robert-flo.github.io/ia-herramienta-analizador-logs/](https://robert-flo.github.io/ia-herramienta-analizador-logs/)

---

## 1. Delimitación de Responsabilidades: IA como Apoyo vs. Control del Desarrollador

El objetivo central de este proyecto fue construir un analizador de logs robusto en Python manteniendo en todo momento el control humano sobre las reglas de negocio, qué constituye un error y cómo estructurar la validación, utilizando la Inteligencia Artificial únicamente como asistente técnico.

### Qué partes fueron decisión del desarrollador (Control Humano)

1. **Definición del contrato de línea válida:**
   Decidí que una línea bien formada debe cumplir estrictamente la estructura `[NIVEL] YYYY-MM-DD mensaje`, exigiendo que:
   - La severidad esté entre corchetes y en mayúsculas exactas (`[INFO]`, `[WARNING]`, `[ERROR]`). Niveles en minúsculas (`[error]`), sin corchetes (`INFO ...`) o fuera del dominio (`[DEBUG]`) se rechazan como malformados.
   - La fecha tenga exactamente 10 caracteres en formato `YYYY-MM-DD` (4-2-2 dígitos ASCII) **y** corresponda a una fecha real del calendario gregoriano.
   - El mensaje posterior a la fecha no esté vacío.
2. **Política ante información faltante o incompleta (Solapamiento intencional):**
   Tomé la decisión explícita de no descartar silenciosamente las líneas incompletas. Si una línea tiene un nivel válido pero carece de fecha (como el ejemplo de la guía: `[WARNING] Invalid password attempt`), el programa **sí contabiliza el nivel `WARNING`** dentro de las estadísticas por severidad y **simultáneamente incrementa el contador de líneas malformadas/incompletas**, detallando el número de línea y la causa exacta (`fecha ausente`).
3. **Manejo de casos borde (Edge Cases):**
   - **Líneas en blanco:** Decidí ignorarlas como eventos para no distorsionar el total ni inflar los errores por saltos de línea al final del archivo, pero reportando un contador explícito de `Líneas en blanco ignoradas`.
   - **Años bisiestos:** Se valida que `2024-02-29` sea aceptado (año bisiesto) y `2023-02-29` sea rechazado como fecha inexistente en el calendario.
   - **Codificación y errores de lectura:** Uso de `utf-8-sig` con `errors="replace"` para absorber marcas BOM de Windows y bytes corruptos sin abortar la ejecución con un `Traceback`, junto con captura limpia de `FileNotFoundError`, `IsADirectoryError` y `PermissionError` en `main.py`.
   - **Fuera de alcance delimitado:** Marcas de hora/zona horaria y trazas multilínea se dejaron fuera del formato válido para mantener la especificación acotada al requerimiento.

### Qué partes del código fueron sugeridas o apoyadas por IA

1. **Propuesta de expresiones regulares y estructura modular:**
   Utilicé IA para proponer las expresiones regulares de extracción (`_RE_BIEN`, `_RE_NIVEL`, `_RE_FECHA_LAXA`, `_RE_FECHA_EXACTA`) y para estructurar el retorno de resultados usando `@dataclass` (`Resultado` y `EventoMalformado` en `analizador.py`).
2. **Integración del visor web con Pyodide:**
   Consulté cómo ejecutar el mismo script de Python en el navegador sobre GitHub Pages sin duplicar la lógica en JavaScript. La IA sugirió cargar `analizador.py` dentro de **Pyodide (WebAssembly)** en `docs/index.html`, de modo que tanto la consola (`main.py`) como la interfaz web ejecutan exactamente el mismo código Python.
3. **Automatización de pruebas E2E (`unittest`):**
   Me apoyé en IA para estructurar el arnés de pruebas con `subprocess` en `tests/test_e2e.py`, pero los valores esperados (`pruebas/esperados.md`) los calculé manualmente línea por línea antes de ejecutar las pruebas.

---

## 2. Ejemplo Concreto: Error Sugerido por la IA, Detección y Corrección

### i. Qué sugirió la IA (Incompleto / Incorrecto para nuestro caso)

Al consultar cómo validar que el campo de fecha de cada registro cumpliera con el formato `YYYY-MM-DD` y fuera una fecha real del calendario, la sugerencia inicial de la IA fue utilizar directamente `datetime.strptime`:

```python
# Sugerencia inicial de la IA:
from datetime import datetime

def validar_fecha_ia(token: str) -> bool:
    try:
        datetime.strptime(token, "%Y-%m-%d")
        return True
    except ValueError:
        return False
```

A simple vista, el bloque parece correcto porque usa el especificador estándar `%Y-%m-%d` y rechaza fechas inexistentes como `2023-02-29`.

### ii. Cómo lo detecté y lo corregí

En lugar de dar por buena la función, diseñé casos de prueba con errores de formato sutiles y ejecuté una prueba aislada en Python 3.12 (registrada en `evidencia/experimento_strptime.txt`):

```text
CPython 3.12.3
datetime.strptime(valor, "%Y-%m-%d"):
  ACEPTA '2024-1-2'   -> 2024-01-02   <-- Falso positivo (sin ceros a la izquierda)
  ACEPTA '2024-1-02'  -> 2024-01-02   <-- Falso positivo (mes de 1 dígito)
  ACEPTA '2024-01-2'  -> 2024-01-02   <-- Falso positivo (día de 1 dígito)
  RECHAZA '2023-02-29' -> ValueError: day is out of range for month
```

**Hallazgo:** Descubrí que en Python `datetime.strptime(..., "%Y-%m-%d")` **no exige dos dígitos para el mes ni para el día**; acepta `2024-1-2` o `2024-1-02` como si fueran fechas bien formadas, violando nuestra regla de formato estricto `YYYY-MM-DD` (ancho fijo 4-2-2).

**Corrección implementada en `analizador.py`:**
Separé la validación en dos pasos explícitos bajo mi control:
1. **Validación estricta de formato y ancho ASCII (`4-2-2`):** Mediante la expresión regular `_RE_FECHA_EXACTA = re.compile(r"^\d{4}-\d{2}-\d{2}$")`. Si el token parece fecha (`_RE_FECHA_LAXA = r"^\d{1,4}-\d{1,2}-\d{1,2}$"`) pero no tiene ancho `4-2-2`, se reporta específicamente: `"fecha con formato incorrecto (se exige YYYY-MM-DD con dígitos ASCII de ancho exacto 4-2-2)"`.
2. **Validación de calendario gregoriano real:** En `_es_calendario_real(fecha)`, se extraen los enteros `anio`, `mes` y `dia` y se instancia `datetime.date(anio, mes, dia)`:

```python
def _es_calendario_real(fecha: str) -> bool:
    try:
        anio = int(fecha[0:4])
        mes = int(fecha[5:7])
        dia = int(fecha[8:10])
        datetime.date(anio, mes, dia)
    except ValueError:
        return False
    return True
```

Además, agregué la línea `[INFO] 2024-1-02 fecha sin relleno de ceros` en `pruebas/con_errores.log` (línea 10) y el test unitario `test_ancho_fecha_sin_ceros_es_malformado` en `tests/test_e2e.py` para garantizar que este error nunca regrese.

---

## 3. Aprendizajes sobre el Uso de la IA como Herramienta y no como Reemplazo

1. **Una función de librería sugerida por IA no equivale a una regla de negocio:**
   La IA tiende a asociar "validar fecha YYYY-MM-DD" con `strptime("%Y-%m-%d")` porque es el patrón más frecuente en código público. Sin embargo, conocer para qué sirve un bloque de código implica verificar sus límites reales con datos de prueba adversos antes de integrarlo.
2. **El valor del desarrollador está en definir el comportamiento esperado antes de probar:**
   Calcular a mano los conteos de `pruebas/bien_formado.log` y `pruebas/con_errores.log` en `pruebas/esperados.md` antes de dar por terminado el programa fue decisivo. Si hubiera dejado que la IA generara tanto el código como los resultados esperados, el falso positivo de `2024-1-02` habría pasado desapercibido.
3. **La IA acelera la implementación, pero la responsabilidad es intransferible:**
   Usar IA me permitió construir en poco tiempo no solo el script de consola (`main.py`), sino también una suite de pruebas automatizadas y una versión web interactiva con Pyodide (`docs/index.html`). No obstante, la claridad de los diagnósticos, la decisión de cómo contabilizar eventos incompletos y la validación final dependieron del criterio técnico humano.
