#!/usr/bin/env bash
# =============================================================================
# Corre el pipeline completo de Buyer Persona y deja logs + estado.
# Pensado para llamarse desde cron o systemd.
#
# Features:
#   - Lockfile para evitar corridas superpuestas
#   - Verifica que el venv y dependencias existan
#   - Guarda estado (OK/FAIL) en logs/last_status.txt
#   - Notifica fallos por Email / Telegram / Webhook (lo que esté configurado)
#   - Rota logs (mantiene los últimos 30)
#
# Instalar en cron:
#   crontab -e
#   Instalado como systemd user timer: buyer-persona-pipeline.timer (Persistent=true)
#
# O con el instalador incluido:
#   venv/bin/python3 scripts/install_cron.py --install
# =============================================================================

set -euo pipefail

# --- Configuración de rutas --------------------------------------------------
# La ruta sale del script y no de un usuario fijo: desde el 2026-09-04 el
# pipeline diario corre en el servidor (/home/santarosa), no en la notebook.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/pipeline_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="$LOG_DIR/last_status.txt"
LOCK_FILE="$LOG_DIR/pipeline.lock"
PYTHON="$PROJECT_DIR/venv/bin/python3"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

START_TS=$(date '+%Y-%m-%d %H:%M:%S')

# --- Cargar .env si existe (para notificaciones) -----------------------------
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$PROJECT_DIR/.env" 2>/dev/null || true
    set +a
fi

# --- Funciones helper --------------------------------------------------------
log()          { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
write_status() { echo "$1 $START_TS — $2" > "$STATUS_FILE"; }

notify() {
    local subject="$1"
    local body="$2"

    # Telegram
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        curl -s --max-time 10 \
             -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
             -d chat_id="${TELEGRAM_CHAT_ID}" \
             --data-urlencode "text=🚨 Buyer Persona

${subject}

${body}" >/dev/null 2>&1 || true
    fi

    # Webhook (Slack/Discord/genérico)
    if [ -n "${WEBHOOK_URL:-}" ]; then
        curl -s --max-time 10 \
             -X POST "$WEBHOOK_URL" \
             -H 'Content-Type: application/json' \
             -d "{\"text\":\"🚨 Buyer Persona — ${subject}\\n${body}\"}" >/dev/null 2>&1 || true
    fi

    # Email (requiere mailutils/postfix configurado)
    if [ -n "${ALERT_EMAIL:-}" ] && command -v mail >/dev/null 2>&1; then
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# --- 1. Lockfile: no correr dos veces en paralelo ---------------------------
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] ⏭️  Otra corrida está en progreso (PID $LOCK_PID). Saliendo." >> "$LOG_FILE"
        # No es un fallo: simplemente saltamos
        exit 0
    else
        # Lock stale: el proceso murió. Lo limpiamos.
        rm -f "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# --- 2. Verificar entorno ---------------------------------------------------
log "=== Iniciando corrida $START_TS ==="

if [ ! -f "$PYTHON" ]; then
    MSG="No existe el venv en $PYTHON. Crear con: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    log "❌ FALLO: $MSG"
    write_status "FAIL" "$MSG"
    notify "❌ Buyer Persona falló" "$MSG"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    log "⚠️  No hay .env — probablemente falten credenciales (modo demo forzado)"
fi

# --- 3. Correr el pipeline ---------------------------------------------------
log "Lanzando: $PYTHON main.py"
set +e
"$PYTHON" main.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
set -e

END_TS=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$EXIT_CODE" -eq 0 ]; then
    log "=== Corrida finalizada OK: $END_TS ==="
    write_status "OK" "Pipeline completado"
else
    log "=== Corrida finalizada con error (exit $EXIT_CODE): $END_TS ==="
    write_status "FAIL" "exit code $EXIT_CODE — ver $LOG_FILE"
    notify "❌ Buyer Persona falló (exit $EXIT_CODE)" "Revisar: $LOG_FILE"
fi

# --- Rotación de logs: quedarse con los últimos 30 ---------------------------
ls -1t "$LOG_DIR"/pipeline_*.log 2>/dev/null | tail -n +31 | while read -r old; do
    rm -f "$old"
done

exit "$EXIT_CODE"