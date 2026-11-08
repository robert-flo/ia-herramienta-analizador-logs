# Conteos esperados (definidos manualmente antes de ejecutar las pruebas)

Estas cifras fueron calculadas línea por línea a partir de las reglas de validación definidas para el proyecto antes de correr el script. La suite `tests/test_e2e.py` verifica automáticamente que la salida de `main.py` coincida con estos valores.

**Reglas de validación definidas:**
1. Cada línea física no vacía representa un evento; las líneas en blanco se ignoran del total de eventos pero se contabilizan por separado.
2. Formato válido estricto: `[NIVEL] YYYY-MM-DD mensaje` (con mensaje no vacío).
3. Niveles admitidos (en mayúsculas exactas entre corchetes): `INFO`, `WARNING`, `ERROR`.
4. Fecha válida: ancho exacto `YYYY-MM-DD` (4-2-2 dígitos ASCII) **y** fecha existente en el calendario gregoriano (incluyendo validación de años bisiestos).
5. Si una línea tiene un nivel válido reconocido (por ejemplo `[WARNING] Invalid password attempt`), suma al contador de ese nivel (`WARNING`) y además se registra como **evento malformado/incompleto** por carecer de fecha válida.

---

## 1. `pruebas/bien_formado.log` (Archivo bien formado)

| Campo | Esperado | Justificación |
| --- | --- | --- |
| Eventos totales | **6** | 6 líneas físicas con contenido |
| INFO | **3** | Líneas 1, 2 y 6 |
| WARNING | **2** | Líneas 3 y 5 |
| ERROR | **1** | Línea 4 |
| Malformados | **0** | Todas cumplen `[NIVEL] YYYY-MM-DD mensaje` y calendario real |
| Líneas en blanco | **0** | Ninguna línea vacía |

---

## 2. `pruebas/con_errores.log` (Archivo con errores e inconsistencias)

Análisis línea por línea:

1. `[WARNING] Invalid password attempt` → Nivel `WARNING` reconocido; falta la fecha → **malformado**.
2. `[INFO] 2023-02-29 fallo calendario no bisiesto` → Nivel `INFO` reconocido; 2023 no es año bisiesto → **malformado**.
3. `[error] 2024-01-15 severidad en minusculas` → Severidad en minúsculas no reconocida → **malformado** (no suma a `ERROR`).
4. `[DEBUG] 2024-01-15 nivel desconocido` → Nivel fuera de los tres permitidos → **malformado** (no suma a ningún nivel).
5. `INFO 2024-01-15 sin corchetes` → Nivel sin corchetes → **malformado** (no suma a `INFO`).
6. `[ERROR] 2024-01-15` → Nivel `ERROR` reconocido y fecha válida, pero sin mensaje → **malformado**.
7. *(línea en blanco)* → Ignorada como evento (suma a líneas en blanco).
8. *(línea en blanco)* → Ignorada como evento (suma a líneas en blanco).
9. `[INFO] 2024-03-01 sistema iniciado` → **Bien formado** (suma a `INFO`).
10. `[INFO] 2024-1-02 fecha sin relleno de ceros` → Nivel `INFO` reconocido; fecha sin formato `4-2-2` (`2024-1-02` en vez de `2024-01-02`) → **malformado** (caso borde detectado frente a `datetime.strptime`).

| Campo | Esperado | Justificación |
| --- | --- | --- |
| Líneas en blanco ignoradas | **2** | Líneas 7 y 8 |
| Eventos totales | **8** | 8 líneas no vacías (1 bien formada + 7 malformadas) |
| INFO | **3** | Líneas 2, 9 y 10 |
| WARNING | **1** | Línea 1 |
| ERROR | **1** | Línea 6 |
| Eventos malformados/incompletos | **7** | Líneas 1, 2, 3, 4, 5, 6 y 10 |

---

## 3. `pruebas/ejemplo_enunciado.log` (Ejemplo directo de la guía de la actividad)

Contiene exactamente las 3 líneas de ejemplo del enunciado:
1. `[INFO] 2025-01-10 User logged in` → Bien formado (`INFO`).
2. `[ERROR] 2025-01-10 Failed to connect to database` → Bien formado (`ERROR`).
3. `[WARNING] Invalid password attempt` → Nivel `WARNING` reconocido, pero sin fecha → **malformado**.

| Campo | Esperado |
| --- | --- |
| Eventos totales | **3** |
| INFO | **1** |
| WARNING | **1** |
| ERROR | **1** |
| Eventos malformados/incompletos | **1** (línea 3: fecha ausente) |
| Líneas en blanco ignoradas | **0** |
