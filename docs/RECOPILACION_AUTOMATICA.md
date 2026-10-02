# 🔁 Recopilación Automática de Buyer Personas

Esta guía explica cómo hacer que el sistema **recopile datos automáticamente**
de Google Ads y Meta Ads, regenere los buyer personas y actualice tu vault de
Obsidian **sin que tengas que hacer nada manual**.

```
    Google Ads  ─┐
                 │     ┌──────────────┐     ┌─────────────┐
    Meta Ads   ──┼────▶│  python      │────▶│  Obsidian   │
                 │     │  main.py     │     │  (vault)    │
    Ventas CSV ──┘     │  (cron)      │     │  actualizado│
                       └──────────────┘     └─────────────┘
                              │
                              ▼
                       logs/ + notificación
                       (si algo falla)
```

---

## 🚀 Opción 1: Cron (Recomendada — Linux/Mac)

Cron es el programador de tareas estándar de Linux. Ejecuta comandos en un
horario fijo. **Es lo más simple y robusto** para este caso.

### Paso 1: Instalación rápida (script incluido)

```bash
# Instala el cron con un solo comando (diario a las 06:00)
venv/bin/python3 scripts/install_cron.py --install

# Ver qué crons hay instalados
venv/bin/python3 scripts/install_cron.py --status

# Desinstalar cuando quieras
venv/bin/python3 scripts/install_cron.py --uninstall
```

### Paso 2: Instalación manual (si querés control total)

```bash
crontab -e
```

Agregá UNA de estas líneas según la frecuencia que quieras:

```cron
# ─────────────────────────────────────────────────────────────
# Cada cuanto correrlo    Línea de cron
# ─────────────────────────────────────────────────────────────
# Todos los días a las 06:00
0 6 * * *       "/home/croman/Escritorio/BUYER PERSONA/scripts/run_pipeline.sh"

# Cada 12 horas (2 veces por día)
0 6,18 * * *    "/home/croman/Escritorio/BUYER PERSONA/scripts/run_pipeline.sh"

# Cada lunes a las 06:00 (semanal, más liviano)
0 6 * * 1       "/home/croman/Escritorio/BUYER PERSONA/scripts/run_pipeline.sh"

# Cada hora (solo si tenés mucho volumen — NO recomendado)
0 * * * *       "/home/croman/Escritorio/BUYER PERSONA/scripts/run_pipeline.sh"
# ─────────────────────────────────────────────────────────────
```

### Paso 3: Verificar que el cron está corriendo

```bash
# 1. Confirmar que el servicio cron esté activo
systemctl --user status cron 2>/dev/null || sudo systemctl status cron

# 2. Ver los logs generados
ls -lht "/home/croman/Escritorio/BUYER PERSONA/logs/"

# 3. Ver el último log
tail -100 "/home/croman/Escritorio/BUYER PERSONA/logs/$(ls -t '/home/croman/Escritorio/BUYER PERSONA/logs/' | head -1)"
```

### ¿Cuál es la frecuencia ideal?

| Frecuencia | Cuándo usarla | Pros | Contras |
|------------|---------------|------|---------|
| **Diaria** (recomendada) | Negocio activo con campañas siempre on | Datos frescos, bajo impacto en rate limits | Un poquito de overhead |
| **Cada 12h** | Lanzamientos / temporada alta | Reacciona rápido a cambios | Más consumo de API |
| **Semanal** | Poco presupuesto, pocas campañas | Minimalista | Datos con hasta 7 días de retraso |
| **Mensual** | Solo análisis estratégico | Cero ruido | Personas desactualizadas |

> 💡 **Recomendación**: empezá con **diaria a las 06:00**. Es el mejor balance.
> Como el conector siempre mira `days_back: 90`, una corrida diaria es
> incremental de hecho: siempre trae los últimos 90 días corridos.

---

## 🖥️ Opción 2: Systemd Timer (Más robusto para servidores)

Systemd timers son superiores a cron cuando:
- Querés que **se recupere solo** si la máquina estaba apagada a la hora programada
- Querés **logs con journalctl** integrados
- Corrés en un servidor dedicado

### Paso 1: Crear el servicio

```bash
sudo tee /etc/systemd/system/buyer-persona.service > /dev/null <<'EOF'
[Unit]
Description=Generador de Buyer Persona (Google Ads + Meta Ads)
After=network-online.target

[Service]
Type=oneshot
User=croman
WorkingDirectory=/home/croman/Escritorio/BUYER PERSONA
ExecStart=/home/croman/Escritorio/BUYER PERSONA/venv/bin/python3 main.py
StandardOutput=append:/home/croman/Escritorio/BUYER PERSONA/logs/systemd.log
StandardError=append:/home/croman/Escritorio/BUYER PERSONA/logs/systemd.log
EOF
```

### Paso 2: Crear el timer

```bash
sudo tee /etc/systemd/system/buyer-persona.timer > /dev/null <<'EOF'
[Unit]
Description=Ejecutar Buyer Persona diariamente

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true   # si la PC estaba apagada, corre al prender
RandomizedDelaySec=300   # jitter de hasta 5 min para no pegar de golpe

[Install]
WantedBy=timers.target
EOF
```

### Paso 3: Activar

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now buyer-persona.timer

# Verificar
systemctl list-timers buyer-persona.timer
systemctl status buyer-persona.service
journalctl -u buyer-persona.service -n 50
```

---

## 🔔 Notificaciones cuando algo falla

El `run_pipeline.sh` mejorado detecta fallas y puede avisarte por:

### Opción A: Email (vía `mail` o `mutt`)

```bash
# 1. Instalar mailutils
sudo apt install mailutils

# 2. Configurar en .env
echo "ALERT_EMAIL=tu@email.com" >> .env

# 3. El script ya lo usa automáticamente
```

### Opción B: Telegram (recomendado — gratis y rápido)

```bash
# 1. Crear un bot: hablar con @BotFather en Telegram → /newbot → copiar token
# 2. Obtener tu chat_id: hablar con @userinfobot
# 3. Configurar en .env
echo "TELEGRAM_BOT_TOKEN=123456:ABC-DEF..." >> .env
echo "TELEGRAM_CHAT_ID=123456789" >> .env
```

### Opción C: Webhook (Slack, Discord, etc.)

```bash
# Configurar en .env
echo "WEBHOOK_URL=https://hooks.slack.com/services/..." >> .env
```

El `run_pipeline.sh` enviará un mensaje **solo si la corrida falla** (o si un
token está por expirar). Si todo sale bien, no molesta.

---

## 🔑 Gestión automática de tokens

El problema más común de la automatización es que **los tokens caducan**:

| Plataforma | Duración del token | Renovación |
|------------|--------------------|------------|
| **Meta Ads** | ~60 días (token de usuario) | Manual — hay que regenerarlo |
| **Meta Ads** (long-lived) | ~60 días, renovable | Automática con `refresh` |
| **Google Ads** | Refresh token = semipermanente | Auto-renovable por la librería |

### Script de verificación de tokens

Incluido en el proyecto:

```bash
# Verifica tokens y avisa cuántos días les quedan
venv/bin/python3 scripts/check_tokens.py
```

Salida de ejemplo:
```
🔵 Meta Ads
  Token: ****XY12
  ⏰ Expira en 12 días (2026-07-31)
  ⚠️  Renovar pronto

🔴 Google Ads
  ✅ Refresh token activo (sin expiración)
```

### Programar la verificación de tokens (recomendado)

Agregá a crontab **además** del pipeline:

```cron
# Todos los lunes a las 09:00, revisar tokens
0 9 * * 1  "/home/croman/Escritorio/BUYER PERSONA/venv/bin/python3 /home/croman/Escritorio/BUYER PERSONA/scripts/check_tokens.py"
```

El script te avisa cuando falta **menos de 14 días** para que expire algún
token, dándote tiempo de renovarlo sin que el pipeline se caiga.

---

## 📊 ¿Qué se actualiza automáticamente en cada corrida?

Cada vez que corre `main.py` (sea manual o por cron), se refrescan:

| Fuente | Qué se actualiza | Período |
|--------|------------------|---------|
| **Meta Ads** | Demografía, intereses, copy de anuncios, performance | Últimos 90 días |
| **Google Ads** | Demografía, ubicaciones, intereses, performance | Últimos 90 días |
| **Ventas CSV** | Histórico completo | Todo el archivo |
| **Buyer Personas** | Recalculadas con clustering sobre datos nuevos | — |
| **Copys marketing** | Google/Meta/Email/WhatsApp regenerados | — |
| **Embudo** (si activo) | Dashboard de conversión | — |

Los archivos `.md` en Obsidian se **sobrescriben** con la versión nueva, así
que siempre ves la versión más reciente. Los JSON crudos se guardan con
timestamp en `output/raw/` para histórico.

---

## 🩺 Monitoreo y diagnóstico

### Ver si la última corrida fue OK

```bash
cat "/home/croman/Escritorio/BUYER PERSONA/logs/last_status.txt"
# Contenido:  "OK 2026-07-20 06:00:12"  o  "FAIL 2026-07-20 06:00:45 <motivo>"
```

### Ver los últimos N logs

```bash
ls -lht "/home/croman/Escritorio/BUYER PERSONA/logs/" | head -10
```

### Diagnosticar una falla

```bash
# El log más reciente
LATEST=$(ls -t "/home/croman/Escritorio/BUYER PERSONA/logs/"pipeline_*.log | head -1)
less "$LATEST"

# Buscar errores
grep -iE "error|fail|❌|⚠️" "$LATEST"
```

### Causas más comunes de fallas

| Síntoma en el log | Causa probable | Solución |
|-------------------|----------------|----------|
| `Meta API: rate limit` | Demasiadas cuentas / muy frecuente | Bajar frecuencia o desactivar `full` demographics |
| `Token inválido` o `190` | Token de Meta expiró | Regenerar token en Facebook |
| `DEVELOPER_TOKEN_NOT_APPROVED` | Token Google en modo test con gasto | Solicitar acceso estándar |
| `No module named 'google.ads'` | Faltan dependencias | `venv/bin/pip install -r requirements.txt` |
| `No hay datos de ninguna fuente` | Todas las fuentes deshabilitadas | Revisar `config/settings.yaml` |

---

## 🧪 Buenas prácticas

1. **Empezar con `--demo`** antes de automatizar lo real, para validar el pipeline.
2. **Correr manualmente una vez** después de poner credenciales nuevas:
   `venv/bin/python3 main.py` y confirmar que genera archivos.
3. **Dejar logs al menos 30 días** (el `run_pipeline.sh` ya lo hace).
4. **No correr más de una vez por hora** — las APIs tienen rate limits.
5. **Mantener el CSV de ventas actualizado** — si el CSV no cambia, la parte
   de ventas no se actualiza (considerar conectar a tu CRM/API de ventas).
6. **Hacer backup del vault de Obsidian** antes de cambios mayores (git o copia).

---

## 📋 Checklist de automatización

- [ ] Credenciales de Google Ads y/o Meta Ads en `.env`
- [ ] `venv/bin/python3 scripts/test_connections.py` pasa sin errores
- [ ] `google_ads.enabled: true` y/o `meta_ads.enabled: true` en settings.yaml
- [ ] `venv/bin/python3 main.py` corre manualmente sin errores
- [ ] `scripts/run_pipeline.sh` ejecutable (`chmod +x`)
- [ ] Cron o systemd timer instalado
- [ ] Notificaciones configuradas (email/telegram/webhook) — opcional
- [ ] `scripts/check_tokens.py` programado semanalmente
- [ ] Verificar logs al día siguiente de la primera corrida automática

---

## 🔗 Archivos relevantes

- `scripts/run_pipeline.sh` — wrapper robusto para cron (con logging, notificaciones y lockfile)
- `scripts/install_cron.py` — instala/desinstala el cron con un comando
- `scripts/check_tokens.py` — verifica y alerta sobre expiración de tokens
- `scripts/test_connections.py` — prueba credenciales sin correr el pipeline completo
- `config/settings.yaml` — habilitar/deshabilitar fuentes y ventana de días