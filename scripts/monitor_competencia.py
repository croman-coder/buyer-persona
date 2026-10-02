#!/usr/bin/env python3
"""
Monitor de Promociones Competitivas — Santa Rosa Automotores
============================================================
Scrapea las webs de competidores clave, detecta cambios en promociones/ofertas,
modelos nuevos y precios, y genera un reporte Markdown para Obsidian.

Funciona con detección de cambios vía hash: solo reporta novedades reales.

Uso:
    python3 scripts/monitor_competencia.py

Salida:
    output/competencia/📢 Promociones Competencia.md  (siempre, sobreescribe)
    output/competencia/.state_promos.json              (estado para diff)
    logs/monitor_competencia_YYYYMMDD_HHMMSS.log       (log de ejecución)
"""
import hashlib
import json
import os
import shutil
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── Configuración ───────────────────────────────────────────────────────────
# Relativo al script y no a un usuario fijo: corre en la notebook y en el
# servidor (/home/santarosa), donde la ruta vieja no existia.
PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "output" / "competencia"
STATE_FILE = OUTPUT_DIR / ".state_promos.json"
REPORT_FILE = OUTPUT_DIR / "📢 Promociones Competencia.md"
# Copia en el vault (output/personas/): es la que se lee desde Obsidian.
VAULT_REPORT_FILE = PROJECT_DIR / "output" / "personas" / "📢 Promociones Competencia.md"
LOG_DIR = PROJECT_DIR / "logs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-PY,es;q=0.9,en;q=0.8",
}

# Competidores a monitorear con selectores específicos
COMPETIDORES = [
    {
        "nombre": "Nissan Paraguay",
        "url": "https://www.nissan.com.py",
        "secciones": {},  # Nissan carga todo por JS en la home, no hay URLs estáticas de ofertas
        "tipo": "precios_publicos",
        "prioridad": "alta",
        "marca_competencia": "Renault, Jetour, GWM, JAC, Mitsubishi",
    },
    {
        "nombre": "Nipon Automotores (Mitsubishi)",
        "url": "https://www.nipon.com.py",
        "secciones": {},
        "tipo": "precios_publicos",
        "prioridad": "critica",
        "marca_competencia": "Mitsubishi (competidor directo)",
    },
    {
        "nombre": "Grupo Garden (KIA)",
        "url": "https://www.kia.com.py",
        "secciones": {
            "promociones_url": "https://www.kia.com.py/promociones",
        },
        "tipo": "promociones",
        "prioridad": "alta",
        "marca_competencia": "KIA (líder del mercado)",
    },
    {
        "nombre": "Chery Paraguay (Garden)",
        "url": "https://www.chery.com.py",
        "secciones": {},  # Chery es SPA Next.js, todo se carga en home
        "tipo": "modelos_nuevos",
        "prioridad": "media",
        "marca_competencia": "Chery (SUV chino, compite con Jetour/Soueast)",
    },
    {
        "nombre": "Geely Paraguay",
        "url": "https://geelyparaguay.com",
        "secciones": {},  # Geely carga todo en home
        "tipo": "modelos_nuevos",
        "prioridad": "media",
        "marca_competencia": "Geely (SUV chino, compite con Jetour/Soueast)",
    },
    {
        "nombre": "Diesa (VW/Honda/BYD)",
        "url": "https://www.diesa.com.py",
        "secciones": {
            "noticias_url": "https://www.diesa.com.py/noticias",
        },
        "tipo": "electromovilidad",
        "prioridad": "alta",
        "marca_competencia": "BYD (compite con Zeekr/Leapmotor/JMEV)",
    },
    {
        "nombre": "DLS Motors (GAC)",
        "url": "https://www.dlsmotors.com.py",
        "secciones": {},
        "tipo": "general",
        "prioridad": "baja",
        "marca_competencia": "GAC Motor (SUV chino)",
    },
    {
        "nombre": "Automaq (Peugeot/Citroën)",
        "url": "https://automaq.com.py",
        "secciones": {},
        "tipo": "general",
        "prioridad": "baja",
        "marca_competencia": "Peugeot, Citroën",
    },
    {
        "nombre": "Toyotoshi (Toyota/Lexus)",
        "url": "https://www.toyotoshi.com.py",
        "secciones": {},
        "tipo": "general",
        "prioridad": "baja",
        "marca_competencia": "Toyota, Lexus",
    },
]


def log(msg: str):
    """Log con timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"monitor_competencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch_page(url: str, timeout: int = 15) -> str | None:
    """Descarga una página con manejo de errores."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        log(f"  ⚠️ Error fetching {url}: {e}")
        return None


def extract_text_content(html: str) -> dict:
    """Extrae contenido relevante de una página HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remover scripts y estilos
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    result = {
        "title": soup.find("title").get_text(strip=True) if soup.find("title") else "",
        "headings": [],
        "precios": [],
        "promociones": [],
        "modelos": [],
        "text_sample": "",
    }

    # Headings (h1, h2, h3)
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text and len(text) > 3:
            result["headings"].append(text)

    # Buscar precios (patrones: $XX.XXX, USD XX.XXX, Gs. XX.XXX)
    full_text = soup.get_text(separator=" ")
    price_patterns = [
        r"\$\s?(\d{1,3}(?:\.\d{3})+)",
        r"USD\s*(\d{1,3}(?:\.\d{3})+)",
        r"(?:desde|desde\s+USD)\s+\$?(\d{1,3}(?:\.\d{3})+)",
        r"PRECIO\s+DESDE\s*\$?(\d{1,3}(?:\.\d{3})+)",
    ]
    for pattern in price_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for m in matches:
            if m not in result["precios"]:
                result["precios"].append(m)

    # Buscar keywords de promoción
    promo_keywords = [
        "oferta", "promoción", "promocion", "descuento", "bonificación",
        "cuota", "financiación", "financiacion", "0km", "0 km",
        "beneficio", "exclusivo", "imperdible", "oportunidad",
        "entrega", "prueba de manejo", "test drive",
        "promociones más esperadas", "llevás", "regalás",
    ]
    text_lower = full_text.lower()
    for kw in promo_keywords:
        if kw in text_lower:
            # Extraer contexto alrededor del keyword
            idx = text_lower.find(kw)
            start = max(0, idx - 40)
            end = min(len(full_text), idx + 80)
            contexto = full_text[start:end].strip().replace("\n", " ")
            contexto = re.sub(r"\s+", " ", contexto)
            if contexto and len(contexto) > 10:
                result["promociones"].append({"keyword": kw, "contexto": contexto[:150]})

    # Buscar nombres de modelos conocidos
    modelos_conocidos = [
        # Nissan
        "Kait", "Kicks", "Sentra", "Qashqai", "X-Trail", "Frontier",
        "Pathfinder", "Patrol", "X-Trail E-Power",
        # Mitsubishi
        "L200", "Triton", "Montero", "Eclipse Cross", "Outlander", "ASX", "Lancer",
        # KIA
        "Picanto", "Soluto", "Sportage", "Seltos", "Sorento", "Carnival",
        "Niro", "EV5", "EV9", "Tasman", "K3", "Sonet", "Carens", "K2700",
        # Chery
        "T2 Pro", "T4 Pro", "T7 Pro", "T8 Pro", "Himla", "M7",
        # Geely
        "GX3", "Coolray", "Azkarra", "Starray", "Cityray", "EX5",
        # Honda
        "WR-V", "HR-V", "CR-V", "Pilot",
        # VW
        "Polo", "Voyage", "Virtus", "T-Cross", "Taos", "Amarok", "Nivus",
        # BYD
        "Dolphin", "Song", "Yuan", "Han", "Tang", "Seal",
        # GAC
        "GS8", "GS4", "GS3",
        # Toyota
        "Corolla", "Hilux", "SW4", "RAV4", "Yaris",
    ]
    for modelo in modelos_conocidos:
        if re.search(r"\b" + re.escape(modelo) + r"\b", full_text, re.IGNORECASE):
            result["modelos"].append(modelo)

    # Muestra de texto (primeros 800 caracteres limpios)
    clean_text = re.sub(r"\s+", " ", full_text).strip()
    result["text_sample"] = clean_text[:800]

    # Limitar listas para no inflar el estado
    result["headings"] = result["headings"][:30]
    result["promociones"] = result["promociones"][:15]
    result["modelos"] = list(set(result["modelos"]))[:25]

    return result


def compute_hash(data: dict) -> str:
    """Genera un hash del contenido para detectar cambios."""
    # Solo hashear headings + precios + promociones (no text_sample completo)
    relevant = {
        "headings": data.get("headings", []),
        "precios": data.get("precios", []),
        "promociones": [p["keyword"] if isinstance(p, dict) else p for p in data.get("promociones", [])],
        "modelos": sorted(data.get("modelos", [])),
    }
    return hashlib.sha256(
        json.dumps(relevant, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:12]


def load_state() -> dict:
    """Carga el estado previo."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_state(state: dict):
    """Guarda el estado."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def format_price(p: str) -> str:
    """Formatea un precio para display."""
    return f"${p}"


def generate_report(resultados: list[dict], cambios: list[dict], now: datetime) -> str:
    """Genera el reporte Markdown para Obsidian."""
    fecha_str = now.strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("---")
    lines.append("type: monitor-competencia")
    lines.append(f"created: '{now.strftime('%Y-%m-%d')}'")
    lines.append("tags:")
    lines.append("- competencia")
    lines.append("- monitor")
    lines.append("- promociones")
    lines.append(f"last_scan: '{fecha_str}'")
    lines.append("---")
    lines.append("")
    lines.append("# 📢 Promociones de la Competencia")
    lines.append("")
    lines.append(f"> [!info] Última actualización: **{fecha_str}** · Próximo scan automático")
    lines.append("")
    lines.append(f"> [!warning] 🔴 = Cambio detectado en este scan · 🟢 = Sin cambios")
    lines.append("")

    # Sección de cambios detectados
    if cambios:
        lines.append("## 🚨 Cambios Detectados en Este Scan")
        lines.append("")
        for c in cambios:
            lines.append(f"### {'🔴' if c['prioridad'] == 'critica' else '⚠️'} {c['competidor']}")
            lines.append("")
            lines.append(f"**Marcas afectadas:** {c['marca_competencia']}")
            lines.append("")
            if c.get("cambios_detalle"):
                for detalle in c["cambios_detalle"]:
                    lines.append(f"- {detalle}")
                lines.append("")
            if c.get("precios_nuevos"):
                lines.append("**Precios detectados:**")
                lines.append("")
                lines.append("| Precio |")
                lines.append("|--------|")
                for p in c["precios_nuevos"]:
                    lines.append(f"| {format_price(p)} |")
                lines.append("")
            lines.append(f"**Prioridad:** {c['prioridad'].upper()}")
            lines.append(f"**URL:** [{c['url']}]({c['url']})")
            lines.append("")
        lines.append("---")
        lines.append("")
    else:
        lines.append("## ✅ Sin Cambios Detectados")
        lines.append("")
        lines.append(f"No se detectaron cambios en promociones, precios o modelos desde el último scan ({fecha_str}).")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Estado actual de cada competidor
    lines.append("## 📊 Estado Actual por Competidor")
    lines.append("")

    for r in resultados:
        icon = "🔴" if r.get("cambio") else "🟢"
        prio_icon = {"critica": "🚨", "alta": "⚠️", "media": "📍", "baja": "📌"}.get(r["prioridad"], "📌")

        lines.append(f"### {icon} {prio_icon} {r['competidor']}")
        lines.append("")
        lines.append(f"**Marcas que compiten con:** {r['marca_competencia']}")
        lines.append(f"**URL:** [{r['url']}]({r['url']})")
        lines.append("")

        if r.get("precios"):
            lines.append("**Precios detectados en sitio:**")
            lines.append("")
            lines.append("| Precio |")
            lines.append("|--------|")
            for p in r["precios"][:10]:
                lines.append(f"| {format_price(p)} |")
            lines.append("")

        if r.get("promociones"):
            lines.append("**Promociones / Keywords detectados:**")
            lines.append("")
            seen_kws = set()
            for promo in r["promociones"]:
                kw = promo["keyword"] if isinstance(promo, dict) else promo
                if kw not in seen_kws:
                    seen_kws.add(kw)
                    lines.append(f"- `{kw}`")
            lines.append("")

        if r.get("modelos"):
            lines.append(f"**Modelos mencionados:** {', '.join(r['modelos'][:15])}")
            lines.append("")

        if r.get("headings"):
            lines.append("<details><summary>📄 Headings de la página</summary>")
            lines.append("")
            for h in r["headings"][:10]:
                lines.append(f"- {h}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Resumen ejecutivo
    lines.append("## 📋 Resumen Ejecutivo")
    lines.append("")
    total_competidores = len(resultados)
    con_cambios = sum(1 for r in resultados if r.get("cambio"))
    sin_cambios = total_competidores - con_cambios
    lines.append(f"- **Competidores monitoreados:** {total_competidores}")
    lines.append(f"- **Con cambios detectados:** {con_cambios} 🔴")
    lines.append(f"- **Sin cambios:** {sin_cambios} 🟢")
    lines.append("")

    # Prioridades
    criticos = [r for r in resultados if r["prioridad"] == "critica" and r.get("cambio")]
    altos = [r for r in resultados if r["prioridad"] == "alta" and r.get("cambio")]
    if criticos:
        lines.append(f"> [!danger] 🚨 ACCIÓN CRÍTICA: {len(criticos)} competidor(es) crítico(s) con cambios")
        for c in criticos:
            lines.append(f"> - **{c['competidor']}** — revisar de inmediato")
        lines.append("")
    if altos:
        lines.append(f"> [!warning] ⚠️ ACCIÓN RECOMENDADA: {len(altos)} competidor(es) de prioridad alta con cambios")
        for c in altos:
            lines.append(f"> - **{c['competidor']}** — evaluar contraoferta")
        lines.append("")

    # Links a Meta Ads Library
    lines.append("## 🔗 Auditoría Meta Ads (verificar anuncios activos)")
    lines.append("")
    lines.append("| Competidor | Ver anuncios activos |")
    lines.append("|---|---|")
    meta_ads_links = {
        "Nissan Paraguay": "Nissan%20Paraguay",
        "Nipon Automotores (Mitsubishi)": "Nipon%20Automotores",
        "Grupo Garden (KIA)": "Kia%20Paraguay",
        "Chery Paraguay (Garden)": "Chery%20Paraguay",
        "Geely Paraguay": "Geely%20Paraguay",
        "Diesa (VW/Honda/BYD)": "BYD%20Paraguay",
    }
    for nombre, q in meta_ads_links.items():
        lines.append(f"| {nombre} | [Ver anuncios](https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=PY&q={q}) |")
    lines.append("")

    # Contenido relacionado
    lines.append("## 🔗 Contenido Relacionado")
    lines.append("- [[⚔️ Benchmark Competitivo]]")
    lines.append("- [[Buyer Personas MOC]]")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generado automáticamente el {fecha_str} por monitor_competencia.py*")
    lines.append("")

    return "\n".join(lines)


def main():
    log("=" * 60)
    log("INICIO — Monitor de Promociones Competitivas")
    log("=" * 60)

    now = datetime.now()
    state_previo = load_state()
    state_nuevo = {}
    resultados = []
    cambios_detectados = []

    for comp in COMPETIDORES:
        nombre = comp["nombre"]
        url = comp["url"]
        log(f"📡 Scrapeando: {nombre} ({url})")

        # Fetch página principal
        html = fetch_page(url)
        if not html:
            log(f"  ❌ No se pudo cargar {nombre}, saltando...")
            resultados.append({
                "competidor": nombre,
                "url": url,
                "marca_competencia": comp["marca_competencia"],
                "prioridad": comp["prioridad"],
                "error": "No se pudo cargar la página",
                "precios": [],
                "promociones": [],
                "modelos": [],
                "headings": [],
                "cambio": False,
            })
            continue

        # Extraer contenido
        content = extract_text_content(html)

        # Si hay secciones adicionales, scrapearlas también
        for sec_name, sec_url in comp.get("secciones", {}).items():
            log(f"  📄 Sección extra: {sec_name}")
            sec_html = fetch_page(sec_url)
            if sec_html:
                sec_content = extract_text_content(sec_html)
                # Mergear contenido
                content["precios"].extend(sec_content.get("precios", []))
                content["promociones"].extend(sec_content.get("promociones", []))
                content["modelos"].extend(sec_content.get("modelos", []))
                content["headings"].extend(sec_content.get("headings", []))
            # Rate limiting simple
            import time
            time.sleep(0.5)

        # Deduplicar
        content["precios"] = list(dict.fromkeys(content["precios"]))
        content["modelos"] = list(set(content["modelos"]))

        # Hash para detección de cambios
        current_hash = compute_hash(content)
        state_key = f"promo_{url}"
        prev_hash = state_previo.get(state_key, "")
        cambio = current_hash != prev_hash

        if cambio and prev_hash:
            log(f"  🔴 CAMBIO DETECTADO en {nombre}!")
            cambios_detectados.append({
                "competidor": nombre,
                "url": url,
                "marca_competencia": comp["marca_competencia"],
                "prioridad": comp["prioridad"],
                "cambios_detalle": [],
                "precios_nuevos": content["precios"][:10],
            })
        elif cambio and not prev_hash:
            log(f"  🆕 Primera carga de {nombre} (baseline)")
        else:
            log(f"  🟢 Sin cambios en {nombre}")

        # Guardar en estado nuevo
        state_nuevo[state_key] = current_hash
        state_nuevo[f"{state_key}_precios"] = content["precios"]
        state_nuevo[f"{state_key}_modelos"] = content["modelos"]
        state_nuevo[f"{state_key}_timestamp"] = now.isoformat()

        # Agregar flag de cambio al resultado
        content["cambio"] = cambio and bool(prev_hash)
        content["competidor"] = nombre
        content["url"] = url
        content["marca_competencia"] = comp["marca_competencia"]
        content["prioridad"] = comp["prioridad"]
        resultados.append(content)

        # Rate limiting entre competidores
        import time
        time.sleep(1)

    # Guardar estado
    save_state(state_nuevo)
    log(f"💾 Estado guardado en {STATE_FILE}")

    # Generar reporte
    reporte = generate_report(resultados, cambios_detectados, now)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(reporte)
    log(f"📝 Reporte generado: {REPORT_FILE}")

    # Copia al vault para lectura desde Obsidian (best-effort: si falla, no
    # rompe la corrida; el original queda en output/competencia/).
    try:
        VAULT_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPORT_FILE, VAULT_REPORT_FILE)
        log(f"📝 Copia en vault: {VAULT_REPORT_FILE}")
    except OSError as e:
        log(f"⚠️ No se pudo copiar al vault: {e}")

    # Resumen final
    log("")
    log("=" * 60)
    log(f"COMPLETADO — {len(resultados)} competidores escaneados")
    log(f"Cambios detectados: {len(cambios_detectados)}")
    log("=" * 60)


if __name__ == "__main__":
    main()
