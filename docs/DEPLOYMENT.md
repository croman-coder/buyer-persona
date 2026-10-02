# 🚀 Dónde y cómo hacer deploy del Buyer Persona

Este proyecto es un **pipeline batch** (no es una web app): corre periódicamente,
lee datos de las APIs, genera archivos `.md` y termina. Eso abre varias opciones
de deployment que una app tradicional no tiene.

```
   ┌─────────────────────────────────────────────────────────────┐
   │                   ¿DÓNDE PUEDE CORRER?                      │
   ├──────────────┬──────────────┬──────────────┬────────────────┤
   │  TU PC       │  VPS barato  │  Docker      │  GitHub Actions│
   │  (cron)      │  (24/7)      │  (portátil)  │  (sin server)  │
   ├──────────────┼──────────────┼──────────────┼────────────────┤
   │  Gratis      │  $4-6/mes    │  Gratis*     │  Gratis**      │
   │  Ya armado   │  Mejor p/24h │  Reproducible│  Cero mant.   │
   │  Depende PC  │  Setup medio │  Dev/Prod    │  Vault en git  │
   └──────────────┴──────────────┴──────────────┴────────────────┘

   * Docker corre en tu PC, VPS o NAS
   ** GitHub Actions free tier: 2.000 min/mes (alcanza y sobra)
```

---

## 📊 Comparativa rápida: ¿cuál elegir?

| Criterio | Local + cron | VPS | Docker | GitHub Actions |
|----------|:---:|:---:|:---:|:---:|
| **Costo** | $0 | $4-6/mes | $0 | $0 |
| **Siempre disponible** | ❌ (si PC apagada) | ✅ | Depende dónde corra | ✅ |
| **Setup inicial** | 5 min | 30 min | 20 min | 15 min |
| **Mantenimiento** | Bajo | Medio | Bajo | Cero |
| **Vault Obsidian** | Local directo | Sync git/rsync | Volumen | Git (repo) |
| **Datos sensibles** | ✅ Privados | ✅ Privados | ✅ Privados | ⚠️ Revisa |
| **Logs centralizados** | ❌ | ✅ journalctl | ✅ docker logs | ✅ web UI |
| **Ideal si...** | PC siempre on | Querés 24/7 | Querés portabilidad | Minimalismo total |

### 🎯 Recomendación según tu caso

- **Tu PC está prendida 24/7 o casi** → **Local + cron** (ya lo tenés armado, no agregues complejidad)
- **La PC se apaga y no querés perder corridas** → **VPS Hetzner CX11 ($4.5/mes)** + git sync del vault
- **Querés probar en otro lado sin reinstalar todo** → **Docker**
- **No querés mantener infraestructura** → **GitHub Actions** (vault como repo git privado)

---

## Opción 1: Local + Cron (lo más simple)

**Ya está implementado.** Ver `docs/RECOPILACION_AUTOMATICA.md`.

```bash
# Setup (una sola vez)
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env   # poner credenciales

# Activar automatización
venv/bin/python3 scripts/install_cron.py --install
```

**Pros**: cero costo, cero infra, datos nunca salen de tu PC.
**Contras**: si la PC está apagada a las 06:00, no corre (usar systemd timer con `Persistent=true` para que se recupere al prender).

---

## Opción 2: VPS (servidor cloud 24/7)

Ideal si querés que el pipeline corra siempre sin importar el estado de tu PC.

### Paso 1: elegir VPS

| Proveedor | Plan | Precio | Por qué |
|-----------|------|--------|---------|
| **Hetzner** (recomendado) | CX11 (2GB RAM) | €4.5/mes | Mejor relación precio/calidad |
| DigitalOcean | Droplet 2GB | $6/mes | Interfaz simple |
| Contabo | VPS S | €4/mes | Más barato, pero overselling |
| Oracle Cloud | Free tier | $0 | 4 ARM cores + 24GB RAM gratis (si lo agarrás) |

> 💡 Este proyecto necesita **mínimo 1GB RAM** (pandas + google-ads son algo pesados).

### Paso 2: setup del servidor

```bash
# En el VPS, una sola vez
sudo apt update && sudo apt install -y python3-venv python3-pip git

# Clonar el repo (usar deploy key o HTTPS con token)
cd /opt
git clone https://github.com/TU_USUARIO/buyer-persona.git
cd buyer-persona

# Crear venv e instalar
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
nano .env   # pegar tokens

# Test
venv/bin/python3 scripts/test_connections.py

# Activar systemd timer (mejor que cron en servidores)
sudo cp scripts/buyer-persona.service /etc/systemd/system/
sudo cp scripts/buyer-persona.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now buyer-persona.timer
```

### Paso 3: sincronizar el vault con tu PC

El vault de Obsidian vive en el VPS, pero lo querés ver en tu PC. Opciones:

#### Opción A: Git (recomendada)
```bash
# En el VPS: hacer del vault un repo
cd /opt/buyer-persona/Buyer\ Persona
git init && git add . && git commit -m "vault inicial"
git remote add origin git@github.com:TU_USUARIO/buyer-persona-vault.git
git push -u origin main

# Después de cada corrida, pushear cambios
# (agregar al final de scripts/run_pipeline.sh)
cd /opt/buyer-persona/Buyer\ Persona && git add . && git commit -m "update $(date)" && git push

# En tu PC: clonar/pull para ver actualizado
cd ~/Escritorio
git clone git@github.com:TU_USUARIO/buyer-persona-vault.git "Buyer Persona"
```

#### Opción B: Syncthing (sync automático P2P)
```bash
# Sin intermediarios, sync directo VPS ↔ PC
sudo apt install syncthing
# Configurar en https://localhost:8384 de ambos lados
```

### Paso 4: seguridad del VPS

```bash
# Firewall (solo SSH + Syncthing si lo usás)
sudo ufw allow OpenSSH
sudo ufw allow 8384/tcp   # Syncthing UI (solo si lo usás)
sudo ufw enable

# SSH con clave, deshabilitar password
sudo nano /etc/ssh/sshd_config
#   PasswordAuthentication no
sudo systemctl restart ssh

# Fail2ban (anti-fuerza bruta)
sudo apt install fail2ban
```

---

## Opción 3: Docker (portabilidad total)

Docker empaqueta todo (Python + dependencias + código) en una imagen
reproducible. La misma imagen corre en tu PC, en un VPS o en un NAS.

### Archivos incluidos

- `Dockerfile` — define la imagen
- `docker-compose.yml` — orquestación (volúmenes + schedule)

### Uso

```bash
# 1. Construir la imagen (una sola vez)
docker compose build

# 2. Configurar credenciales
cp .env.example .env
nano .env

# 3. Probar una corrida
docker compose run --rm buyer-persona

# 4. Dejarlo corriendo con schedule automático
docker compose up -d
```

El `docker-compose.yml` monta:
- `./Buyer Persona:/app/Buyer Persona` → el vault se ve en tu PC
- `./data:/app/data` → CSV de ventas
- `./.env:/app/.env:ro` → credenciales (read-only)
- `./logs:/app/logs` → logs persistentes

### Docker en un NAS (Synology/QNAP)

Si tenés un NAS, podés correr el container ahí con Container Manager / Container Station. Es gratis y está siempre prendido.

---

## Opción 4: GitHub Actions (serverless)

**Sin mantener infraestructura.** GitHub corre el pipeline en la nube gratis
(2.000 minutos/mes en plan free). El vault se sincroniza via git.

### Archivo incluido

`.github/workflows/pipeline.yml`

### Configuración (una sola vez)

1. **Subir el proyecto a GitHub** (repo privado, recomendado por los datos):

```bash
# En tu PC
cd "/home/croman/Escritorio/BUYER PERSONA"
git init
git add .
git commit -m "proyecto inicial"
git remote add origin git@github.com:TU_USUARIO/buyer-persona.git
git push -u origin main
```

2. **Configurar secrets** (credenciales, nunca en el repo):

```
GitHub → TU_REPO → Settings → Secrets and variables → Actions
→ New repository secret por cada variable del .env:
   GOOGLE_ADS_DEVELOPER_TOKEN
   META_ADS_ACCESS_TOKEN
   META_ADS_AD_ACCOUNT_IDS
   ... etc
```

3. **Listo.** El workflow corre automáticamente todos los días a las 06:00 UTC.

### Pros y contras de GitHub Actions

| ✅ Pros | ❌ Contras |
|---------|-----------|
| Cero infraestructura que mantener | El vault tiene que vivir en git |
| Logs web elegantes | 2.000 min/mes límite (alcanza y sobra) |
| Re-ejecutable con 1 click | Datos sensibles en repo privado (revisar) |
| Versionado del vault en git | Tiempo de corrida limitado a 6h/job |

> ⚠️ **Importante**: si tus datos de ventas contienen info personal de clientes
> (emails, nombres), NO subas `data/ventas.csv` al repo. Usá un almacenamiento
> externo (Google Sheets API, S3, etc.) o quedate con opción 1/2.

---

## 🔄 Sincronizar el vault de Obsidian

Sea cual sea el deployment, el output del pipeline es el vault de Obsidian.
Para verlo en tu PC hay 3 caminos:

| Método | Cuándo | Dificultad |
|--------|--------|------------|
| **Git** (repo privado) | VPS / GitHub Actions | Fácil |
| **Syncthing** (P2P) | VPS / NAS | Media |
| **rsync** (cron) | VPS | Fácil |
| **Volumen Docker** | Docker local | Trivial |

### rsync desde VPS a tu PC (ejemplo)

```bash
# En tu PC, en el crontab (cada hora, baja los cambios del VPS)
0 * * * * rsync -az --delete usuario@vps:/opt/buyer-persona/Buyer\ Persona/ "/home/croman/Escritorio/BUYER Persona/" 2>> ~/rsync-buyer.log
```

---

## 📋 Checklist de deployment

### Local (Opción 1)
- [ ] `venv/bin/pip install -r requirements.txt`
- [ ] `.env` con credenciales completas
- [ ] `scripts/test_connections.py` pasa OK
- [ ] `main.py` corre manualmente sin error
- [ ] `scripts/install_cron.py --install`
- [ ] Verificar al día siguiente: `cat logs/last_status.txt`

### VPS (Opción 2)
- [ ] VPS creado y accesible por SSH
- [ ] Firewall + SSH key hardened
- [ ] Repo clonado en `/opt/buyer-persona`
- [ ] venv + dependencias instaladas
- [ ] `.env` con credenciales
- [ ] `test_connections.py` OK
- [ ] systemd timer activo (`systemctl status buyer-persona.timer`)
- [ ] Vault sincronizado a tu PC (git/syncthing/rsync)

### Docker (Opción 3)
- [ ] Docker + Docker Compose instalados
- [ ] `.env` configurado
- [ ] `docker compose build` exitoso
- [ ] `docker compose run --rm buyer-persona` genera `.md`
- [ ] `docker compose up -d` corriendo

### GitHub Actions (Opción 4)
- [ ] Repo subido a GitHub (privado)
- [ ] Secrets configurados en Settings → Secrets
- [ ] Workflow `.github/workflows/pipeline.yml` presente
- [ ] Primera corrida manual (Actions → Run workflow)
- [ ] Logs sin errores
- [ ] Vault commiteado de vuelta (si lo querés local)

---

## 🆘 Ayuda para elegir

Si no sabés cuál elegir, respondé estas 3 preguntas:

1. **¿Tu PC está prendida más de 20h al día?**
   - Sí → **Opción 1 (Local)**. No te compliques.
   - No → siguiente pregunta.

2. **¿Estás cómodo con la terminal y SSH?**
   - Sí → **Opción 2 (VPS)**. Mejor relación costo/beneficio 24/7.
   - No → **Opción 4 (GitHub Actions)**. Cero configuración de servidor.

3. **¿Tenés datos sensibles en el CSV de ventas?**
   - Sí → **Opción 1 o 2** (todo bajo tu control).
   - No / son sintéticos → **Opción 4** también es válida.

---

## 🔗 Archivos relevantes de deployment

- `Dockerfile` — imagen Docker del pipeline
- `docker-compose.yml` — orquestación con volúmenes
- `.github/workflows/pipeline.yml` — workflow GitHub Actions
- `scripts/buyer-persona.service` — unit file systemd (Opción 2)
- `scripts/buyer-persona.timer` — timer systemd (Opción 2)
- `scripts/run_pipeline.sh` — wrapper robusto (todas las opciones)