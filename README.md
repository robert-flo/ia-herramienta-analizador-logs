# Analizador de Logs en Python (CLI + Demo Web Interactiva)

- **Programa:** Kodigo — AI For Devs Jr. 5
- **Módulo:** Semana 3 – IA-first mindset
- **Actividad Individual:** IA como Herramienta, no como Autor: Desarrollo Guiado y Validado de un Script en Python
- **Instructor:** Ing. Ronald Mejia
- **Estudiante:** Roberto Carlos Flores Quintanilla
- **Repositorio GitHub:** [https://github.com/robert-flo/ia-herramienta-analizador-logs](https://github.com/robert-flo/ia-herramienta-analizador-logs)
- **Demo Web en Vivo (GitHub Pages):** [https://robert-flo.github.io/ia-herramienta-analizador-logs/](https://robert-flo.github.io/ia-herramienta-analizador-logs/)
- **Documento de Entrega PDF (con Carátula Kodigo):** [`RobertoFlores-Tarea03.pdf`](RobertoFlores-Tarea03.pdf) | [`RobertoFlores-Tarea03.docx`](RobertoFlores-Tarea03.docx)

---

## Descripción del Proyecto

Script en Python que analiza archivos de texto de registros de eventos (`.log` / `.txt`), identifica el nivel de severidad (`INFO`, `WARNING`, `ERROR`), verifica si cada línea posee una fecha válida en formato estricto `YYYY-MM-DD` y calendario real, y genera un resumen claro en consola y en navegador detallando tanto los totales por tipo como las líneas mal formateadas o incompletas.

Toda la lógica reside en un único módulo canónico: **[`analizador.py`](analizador.py)**. Tanto el programa de consola (**[`main.py`](main.py)**) como la aplicación web (**[`docs/index.html`](docs/index.html)** mediante Pyodide) ejecutan exactamente el mismo código Python.

---

## Ejecución Rápida (Consola y Demo)

### 1. Probar en la Web (sin instalar nada)
Abre **[https://robert-flo.github.io/ia-herramienta-analizador-logs/](https://robert-flo.github.io/ia-herramienta-analizador-logs/)**, espera unos segundos a que cargue Python (Pyodide) y:
- Pulsa cualquiera de los **botones de prueba rápida en 1 clic** (`▶ Probar bien_formado.log`, `▶ Probar con_errores.log`, `▶ Probar ejemplo_enunciado.log`), o
- Selecciona un archivo `.log` desde tu computadora, o edita las líneas en vivo desde el panel de texto integrado.

### 2. Ejecutar desde la Terminal (CLI)

```bash
# Analizar el archivo de prueba bien formado
python3 main.py pruebas/bien_formado.log

# Analizar el archivo de prueba con errores y casos borde
python3 main.py pruebas/con_errores.log

# Analizar las 3 líneas de ejemplo del enunciado de la actividad
python3 main.py pruebas/ejemplo_enunciado.log

# Modo interactivo (el programa solicita la ruta del archivo al usuario)
python3 main.py

# Ejecutar la demostración completa guiada en terminal
./demo.sh

# Ejecutar las 8 pruebas automatizadas E2E
python3 -m unittest tests.test_e2e -v
```

---

## Decisiones Técnicas y Reglas de Validación (Definidas por el Desarrollador)

1. **Unidad de evento y líneas en blanco:** Cada línea física no vacía representa un evento. Las líneas en blanco o compuestas solo de espacios se ignoran del total de eventos pero se informan por separado (`Líneas en blanco ignoradas`).
2. **Estructura de una línea bien formada:** Exactamente `[NIVEL] YYYY-MM-DD mensaje` donde el mensaje posterior a la fecha no sea vacío.
3. **Niveles de severidad admitidos:** Únicamente `[INFO]`, `[WARNING]` y `[ERROR]` en mayúsculas exactas y entre corchetes. Niveles en minúsculas (`[error]`), sin corchetes (`INFO ...`) o desconocidos (`[DEBUG]`) se marcan como malformados y no suman a ningún nivel.
4. **Validación de fecha en dos capas (Corrección sobre `strptime`):**
   - **Capa 1 (Formato estricto 4-2-2):** Se exige la expresión regular `^\d{4}-\d{2}-\d{2}$`. Fechas sin ceros a la izquierda como `2024-1-02` o `2024-1-2` se rechazan como malformadas (a diferencia de `datetime.strptime("%Y-%m-%d")`, que las aceptaría por error).
   - **Capa 2 (Calendario gregoriano real):** Se construye `datetime.date(anio, mes, dia)` para validar años bisiestos y días por mes (ej. `2024-02-29` es válido; `2023-02-29` se rechaza como malformado).
5. **Política ante información incompleta (Contabilización dual):**
   Si una línea contiene una severidad válida pero le falta la fecha o el mensaje (por ejemplo, `[WARNING] Invalid password attempt`), **se contabiliza dentro de su nivel (`WARNING`) y también se suma como línea malformada/incompleta**, reportando el número de línea y el motivo exacto.
6. **Robustez de entrada/salida:** Decodificación `utf-8-sig` con `errors="replace"` (maneja archivos con BOM de Windows y octetos inválidos sin romper la ejecución) y mensajes claros en español ante archivos inexistentes o sin permisos.

---

## Evidencia de Pruebas: Resultados Esperados vs. Obtenidos

El detalle línea por línea de los cálculos manuales previos se encuentra en [`pruebas/esperados.md`](pruebas/esperados.md) y los registros de salida real en la carpeta [`evidencia/`](evidencia/).

| Archivo de Prueba | Eventos Totales | INFO | WARNING | ERROR | Malformados / Incompletos | Líneas en Blanco | Resultado |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [`pruebas/bien_formado.log`](pruebas/bien_formado.log) | **6** | **3** | **2** | **1** | **0** | **0** | ✅ Coincide |
| [`pruebas/con_errores.log`](pruebas/con_errores.log) | **8** | **3** | **1** | **1** | **7** | **2** | ✅ Coincide |
| [`pruebas/ejemplo_enunciado.log`](pruebas/ejemplo_enunciado.log) | **3** | **1** | **1** | **1** | **1** | **0** | ✅ Coincide |

### Salida en consola para `pruebas/bien_formado.log`

```text
Origen: pruebas/bien_formado.log
Líneas en blanco ignoradas: 0
Eventos totales: 6
  INFO: 3
  WARNING: 2
  ERROR: 1
Eventos malformados/incompletos: 0

Solapamiento: el total de eventos es el de líneas no vacías. Un evento malformado con severidad reconocida suma en su nivel Y en malformados. Una severidad desconocida no suma en INFO/WARNING/ERROR.
```

### Salida en consola para `pruebas/con_errores.log`

```text
Origen: pruebas/con_errores.log
Líneas en blanco ignoradas: 2
Eventos totales: 8
  INFO: 3
  WARNING: 1
  ERROR: 1
Eventos malformados/incompletos: 7

Detalle de malformados (una cuenta por línea, aunque haya varias razones):
  - línea 1: fecha ausente
  - línea 2: fecha no es una fecha de calendario real
  - línea 3: severidad ausente o no reconocida (se exige [INFO], [WARNING] o [ERROR] en mayúsculas exactas)
  - línea 4: severidad ausente o no reconocida (se exige [INFO], [WARNING] o [ERROR] en mayúsculas exactas)
  - línea 5: severidad ausente o no reconocida (se exige [INFO], [WARNING] o [ERROR] en mayúsculas exactas)
  - línea 6: mensaje vacío o ausente
  - línea 10: fecha con formato incorrecto (se exige YYYY-MM-DD con dígitos ASCII de ancho exacto 4-2-2)

Solapamiento: el total de eventos es el de líneas no vacías. Un evento malformado con severidad reconocida suma en su nivel Y en malformados. Una severidad desconocida no suma en INFO/WARNING/ERROR.
```

---

## Estructura del Repositorio

```text
├── RobertoFlores-Tarea03.pdf  # Documento formal de entrega con carátula Kodigo, links, reflexión y evidencias
├── RobertoFlores-Tarea03.docx # Versión editable en Word del documento de entrega
├── analizador.py              # Módulo principal con las reglas de validación y análisis
├── main.py                    # Interfaz de línea de comandos (argumento o interactivo)
├── demo.sh                    # Script ejecutable para demostración en vivo paso a paso
├── README.md                  # Documentación general, reglas y evidencias de pruebas
├── REFLEXION.md               # Documento de reflexión técnica (1–3 páginas)
├── pruebas/
│   ├── bien_formado.log       # Caso de prueba 1: registros 100% válidos
│   ├── con_errores.log        # Caso de prueba 2: errores de fecha, bisiesto, nivel y vacíos
│   ├── ejemplo_enunciado.log  # Caso de prueba 3: las 3 líneas de ejemplo del enunciado
│   └── esperados.md           # Conteos esperados calculados manualmente línea por línea
├── tests/
│   ├── test_e2e.py            # 8 pruebas automatizadas E2E sobre el CLI real
│   └── verificar_web.py       # Verificación automatizada de paridad entre CLI y Web
├── docs/
│   └── index.html             # Interfaz web interactiva con Pyodide y botones de demo
└── evidencia/                 # Salidas reales de CLI, experimento strptime y capturas web
```
