#!/usr/bin/env bash
# =============================================================================
# Instala el timer de systemd para Buyer Persona.
# Genera el wrapper en /usr/local/bin/buyer-persona-run, copia el .service
# y el .timer, habilita el timer y muestra el estado.
#
# Uso:
#   sudo bash scripts/install_systemd.sh
#
# Desinstalar:
#   sudo bash scripts/install_systemd.sh --uninstall
# =============================================================================
set -euo pipefail

# --- Detección automática del proyecto ---------------------------------------
# Usar PROJECT_DIR de env si está seteado, sino inferir desde el script.
PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
WRAPPER="/usr/local/bin/buyer-persona-run"
SERVICE_SRC="$PROJECT_DIR/scripts/buyer-persona.service"
TIMER_SRC="$PROJECT_DIR/scripts/buyer-persona.timer"
SERVICE_DST="/etc/systemd/system/buyer-persona.service"
TIMER_DST="/etc/systemd/system/buyer-persona.timer"
USER_NAME="${SUDO_USER:-$USER}"

# --- Verificar root -----------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ Este script necesita permisos de root."
  echo "   Ejecutá: sudo bash scripts/install_systemd.sh"
  exit 1
fi

# --- Verificar que el proyecto existe ----------------------------------------
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ No se encontró el directorio del proyecto: $PROJECT_DIR"
  exit 1
fi

echo "📂 Proyecto: $PROJECT_DIR"
echo "👤 Usuario : $USER_NAME"
echo ""

# --- Modo desinstalar ---------------------------------------------------------
if [ "${1:-}" = "--uninstall" ]; then
  echo "🗑️  Desinstalando..."
  systemctl disable --now buyer-persona.timer 2>/dev/null || true
  rm -f "$SERVICE_DST" "$TIMER_DST" "$WRAPPER"
  systemctl daemon-reload
  echo "✅ Timer de buyer-persona desinstalado."
  exit 0
fi

# --- 1. Generar wrapper en /usr/local/bin -------------------------------------
echo "1️⃣  Generando wrapper $WRAPPER ..."
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
# AUTOGENERADO por scripts/install_systemd.sh
# Wrapper para ejecutar main.py desde systemd (resuelve el problema
# de los espacios en "BUYER PERSONA").

set -euo pipefail
cd "$PROJECT_DIR"

# Ejecutar como el usuario que instaló (no como root)
if [ "\$(id -u)" = "0" ] && [ -n "$USER_NAME" ] && [ "$USER_NAME" != "root" ]; then
  exec su - "$USER_NAME" -c "cd '$PROJECT_DIR' && '$PROJECT_DIR/venv/bin/python3' main.py"
fi

exec "$PROJECT_DIR/venv/bin/python3" main.py
EOF
chmod 755 "$WRAPPER"
echo "   ✅ Wrapper creado."

# --- 2. Copiar unit files ----------------------------------------------------
echo "2️⃣  Copiando unit files a /etc/systemd/system/ ..."
cp "$SERVICE_SRC" "$SERVICE_DST"
cp "$TIMER_SRC" "$TIMER_DST"

# --- 3. Recargar systemd -----------------------------------------------------
echo "3️⃣  Recargando systemd ..."
systemctl daemon-reload

# --- 4. Verificar sintaxis ---------------------------------------------------
echo "4️⃣  Verificando configuración ..."
if ! systemd-analyze verify "$SERVICE_DST" "$TIMER_DST"; then
  echo "⚠️  Hubo advertencias en la verificación (ver arriba)."
  echo "   Fijate de que el wrapper $WRAPPER sea ejecutable."
fi

# --- 5. Habilitar timer ------------------------------------------------------
echo "5️⃣  Habilitando timer ..."
systemctl enable --now buyer-persona.timer

# --- 6. Estado final ---------------------------------------------------------
echo ""
echo "✅ Instalación completa."
echo ""
echo "📋 Próxima corrida programada:"
systemctl list-timers buyer-persona.timer --no-pager || true
echo ""
echo "🔧 Comandos útiles:"
echo "   systemctl status buyer-persona.timer"
echo "   systemctl status buyer-persona.service"
echo "   journalctl -u buyer-persona.service -n 50"
echo "   sudo systemctl start buyer-persona.service   # correr ahora"
echo ""
echo "🗑️  Para desinstalar:"
echo "   sudo bash $PROJECT_DIR/scripts/install_systemd.sh --uninstall"