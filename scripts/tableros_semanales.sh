#!/usr/bin/env bash
# Refresco semanal de los tableros de marketing en el vault de Obsidian.
#
# Lo dispara el cron de Hermes `tableros-semanales` (lunes 8:00, modo
# --no-agent). Hermes exige que el script del job viva dentro de
# ~/.hermes/scripts/ y rechaza symlinks que apunten afuera (guard
# anti symlink-escape en cron/scheduler.py), así que allí hay un stub
# de una línea que hace `exec` de ESTE archivo. La lógica vive acá,
# versionada; el stub no cambia nunca.
#
# Tres pasos deterministas (cero costo de modelo):
#   1. main.py            → baja Meta Ads de las 85 cuentas + leads por página
#   2. generar_tablero_meta.py → notas de Campañas y Scorecard de Asesores
#   3. tablero_bitrix.py  → nota del embudo CRM
#
# Un paso que falla no impide los siguientes: el tablero de Bitrix no
# depende de Meta, y los tableros de Meta pueden regenerarse del último
# JSON bueno aunque el pipeline haya fallado hoy.

set -uo pipefail

# La ruta sale de la ubicacion del script, no de un usuario fijo: este
# mismo archivo corre en la notebook (/home/croman) y en el servidor
# (/home/santarosa). Con la ruta fija, en el servidor salia
# "No existe /home/croman/..." y el cron de los lunes fallaba con exit 1.
PROYECTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$PROYECTO/venv/bin/python"
cd "$PROYECTO" || { echo "❌ No existe $PROYECTO"; exit 1; }

fallos=0
resumen=""

paso() {
    local etiqueta="$1"; shift
    local salida
    if salida=$("$@" 2>&1); then
        # Última línea informativa del script
        resumen+="✅ ${etiqueta}: $(echo "$salida" | grep -vE '^\s*$' | tail -1)"$'\n'
    else
        fallos=$((fallos + 1))
        resumen+="❌ ${etiqueta} FALLÓ:"$'\n'"$(echo "$salida" | tail -5)"$'\n'
    fi
}

paso "Pipeline Meta"      "$PY" main.py
paso "Campañas+Asesores"  "$PY" scripts/generar_tablero_meta.py
paso "Embudo Bitrix"      "$PY" scripts/tablero_bitrix.py

if [ "$fallos" -eq 0 ]; then
    echo "📊 Tableros semanales actualizados"
else
    echo "⚠️ Tableros semanales: $fallos de 3 pasos fallaron"
fi
echo ""
printf '%s' "$resumen"

# El código de salida es lo único que mira el scheduler para marcar el job
# como succeeded/failed. Sin esto el printf de arriba devolvía 0 siempre y
# una semana con la API caída se reportaba como exitosa.
exit "$fallos"
