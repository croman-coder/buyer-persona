#!/usr/bin/env bash
# Wrapper de Python para los crons del proyecto BUYER PERSONA.
#
# Por qué existe: la sesión/cron de Hermes exporta PYTHONPATH apuntando al
# venv de Hermes (py3.11). Si se corre el .venv propio (py3.12) con ese
# PYTHONPATH, los paquetes con binarios compilados (numpy/pandas) cargan las
# .so de py3.11 y explotan con "compiled module files ... incompatible".
# Este wrapper arranca limpio.
PY="/home/croman/Escritorio/BUYER PERSONA/.venv/bin/python"
exec env -u PYTHONPATH -u VIRTUAL_ENV "$PY" "$@"
