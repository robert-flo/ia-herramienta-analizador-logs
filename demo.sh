#!/usr/bin/env bash
# Script de demostración en vivo del Analizador de Logs en Python
# Estudiante: Roberto Flores (25ASAB015)

set -e

AZUL='\033[1;34m'
VERDE='\033[1;32m'
AMARILLO='\033[1;33m'
RESET='\033[0m'

echo -e "${AZUL}======================================================================${RESET}"
echo -e "${AZUL}   DEMOSTRACIÓN EN VIVO: ANALIZADOR DE LOGS EN PYTHON                 ${RESET}"
echo -e "${AZUL}   Estudiante: Roberto Flores (25ASAB015)                             ${RESET}"
echo -e "${AZUL}======================================================================${RESET}"
echo ""

echo -e "${AMARILLO}[1/4] Caso 1: Archivo bien formado (pruebas/bien_formado.log)${RESET}"
echo -e "Contenido del archivo:"
cat -n pruebas/bien_formado.log
echo ""
echo -e "${VERDE}-> Ejecutando: python3 main.py pruebas/bien_formado.log${RESET}"
python3 main.py pruebas/bien_formado.log
echo ""

echo -e "${AMARILLO}[2/4] Caso 2: Archivo con errores y casos borde (pruebas/con_errores.log)${RESET}"
echo -e "Contenido del archivo:"
cat -n pruebas/con_errores.log
echo ""
echo -e "${VERDE}-> Ejecutando: python3 main.py pruebas/con_errores.log${RESET}"
python3 main.py pruebas/con_errores.log
echo ""

echo -e "${AMARILLO}[3/4] Caso 3: Ejemplo directo del enunciado (pruebas/ejemplo_enunciado.log)${RESET}"
echo -e "Contenido del archivo:"
cat -n pruebas/ejemplo_enunciado.log
echo ""
echo -e "${VERDE}-> Ejecutando: python3 main.py pruebas/ejemplo_enunciado.log${RESET}"
python3 main.py pruebas/ejemplo_enunciado.log
echo ""

echo -e "${AMARILLO}[4/4] Suite de pruebas automatizadas E2E (tests/test_e2e.py)${RESET}"
echo -e "${VERDE}-> Ejecutando: python3 -m unittest tests.test_e2e -v${RESET}"
python3 -m unittest tests.test_e2e -v
echo ""
echo -e "${AZUL}======================================================================${RESET}"
echo -e "${VERDE}Demostración completada exitosamente.${RESET}"
echo -e "Web Interactiva: https://robert-flo.github.io/ia-herramienta-analizador-logs/"
echo -e "Repositorio:     https://github.com/robert-flo/ia-herramienta-analizador-logs"
echo -e "${AZUL}======================================================================${RESET}"
