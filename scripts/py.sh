#!/usr/bin/env bash
# Wrapper de Python para los crons del proyecto BUYER PERSONA.
#
# Por qué existe: la sesión/cron de Hermes exporta PYTHONPATH apuntando al
# venv de Hermes (py3.11). Si se corre el .venv propio (py3.12) con ese
# PYTHONPATH, los paquetes con binarios compilados (numpy/pandas) cargan las
# .so de py3.11 y explotan con "compiled module files ... incompatible".
# Este wrapper arranca limpio.
#
# La ruta sale de la ubicación del propio script, así anda igual en la
# notebook (/home/croman, .venv) y en el servidor (/home/santarosa, venv).
PROYECTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for PY in "$PROYECTO/.venv/bin/python" "$PROYECTO/venv/bin/python"; do
  [ -x "$PY" ] && exec env -u PYTHONPATH -u VIRTUAL_ENV "$PY" "$@"
done
echo "py.sh: no hay .venv ni venv en $PROYECTO" >&2
exit 127
