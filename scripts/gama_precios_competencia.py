#!/usr/bin/env python3
"""Gama y precios publicados, modelo por modelo, de las webs del mercado.

Qué agrega sobre el monitor de competencia (monitor-competencia.sh):

  - El monitor detecta QUE algo cambió en la oferta de un sitio. Este
    script dice QUÉ: qué modelos lista cada sitio (la gama) y a qué precio
    publica cada uno, y guarda el histórico para ver cómo se mueve.
  - Cubre también las webs PROPIAS (gwm.com.py, jetour.com.py, ...): son
    las únicas que publican precio en HTML, y conviene vigilar que lo
    publicado coincida con lo que se quiere vender.

Lo que NO puede hacer, medido el 2026-09-04 sobre 18 sitios: Kia, Chery,
Hyundai, Diesa, Automaq, Garden, Toyotoshi y DLS no publican precios ni
siquiera después de renderizar el JavaScript con Chrome. De esos sitios
sale la gama (qué modelos ofrecen y cuándo aparece uno nuevo), no el
precio. Nissan y Geely publican precio en algunas fichas de modelo.

Cómo asocia precio y modelo: a cada precio del texto visible le asigna el
modelo mencionado más cerca ANTES del precio (hasta 120 caracteres), que
es el patrón "MODELO ... desde US$ X" de todas las webs del mercado; si
antes del precio hay 3+ modelos distintos es una lista y se descarta. Por
cada (sitio, modelo) se guarda el precio MÁS BAJO visto, que es el "desde"
que publican. Verificado el 2026-09-04 contra las Battle Cards (precios
tomados a mano el 04/08): Renault 5/5, GWM 8/8, Mitsubishi L200 exacto.

Salidas:
  output/competencia/gama_precios.json      estado (última gama y precios por sitio)
  output/competencia/precios_historico.csv  histórico: una fila por cambio
  Buyer Persona/Competencia/💰 Precios por Modelo.md   nota regenerada
  Buyer Persona/Competencia/⚔️ Bitácora de Competencia.md   eventos (modelo nuevo, precio nuevo/cambiado)

Uso: gama_precios_competencia.py [--dry-run] [--sin-chrome]
Corre desde el monitor de competencia; también a mano. Sin dependencias
fuera de requests + beautifulsoup4 (las del proyecto).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

PROYECTO = Path(__file__).resolve().parents[1]
OUTPUT = PROYECTO / "output" / "competencia"
VAULT = PROYECTO / "Buyer Persona"
NOTA = VAULT / "Competencia" / "💰 Precios por Modelo.md"
BITACORA = VAULT / "Competencia" / "⚔️ Bitácora de Competencia.md"
ESTADO = OUTPUT / "gama_precios.json"
HISTORICO = OUTPUT / "precios_historico.csv"
MARCADOR_FIN = "<!-- hermes:fin -->"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-PY,es;q=0.9,en;q=0.8",
}
MAX_SUBPAGINAS = 12
VENTANA_CHARS = 120          # distancia máxima entre un precio y su modelo
RANGO_USD = (5_000, 300_000)  # fuera de esto no es un precio de vehículo
RANGO_GS = (30_000_000, 2_500_000_000)

# Sitios. `js` = la home se arma por JavaScript, hace falta Chrome para ver
# la gama. `js_sub` = también las fichas de modelo (Nissan: el precio de la
# ficha solo aparece renderizado; medido con Kicks, $24.990 con Chrome y
# nada sin él). Chrome tarda ~5 s por página, por eso no va en todos.
# `marcas` = qué catálogos buscar en ese sitio (una concesionaria multimarca
# lista varias; buscar todo en todos lados mete ruido).
SITIOS = [
    # ---- propios: publican precio; vigilar lo publicado ----
    {"nombre": "GWM Paraguay",        "url": "https://www.gwm.com.py",        "propio": True,  "js": False, "marcas": ["GWM"]},
    {"nombre": "Jetour Paraguay",     "url": "https://www.jetour.com.py",     "propio": True,  "js": False, "marcas": ["Jetour"]},
    {"nombre": "Renault Paraguay",    "url": "https://www.renault.com.py",    "propio": True,  "js": False, "marcas": ["Renault"]},
    {"nombre": "JAC Paraguay",        "url": "https://www.jac.com.py",        "propio": True,  "js": False, "marcas": ["JAC"]},
    {"nombre": "Mitsubishi Paraguay", "url": "https://www.mitsubishi.com.py", "propio": True,  "js": True,  "marcas": ["Mitsubishi"]},
    {"nombre": "Leapmotor Paraguay",  "url": "https://www.leapmotor.com.py",  "propio": True,  "js": True,  "marcas": ["Leapmotor"]},
    {"nombre": "Santa Rosa",          "url": "https://santarosa.com.py",      "propio": True,  "js": False, "marcas": ["GWM", "Jetour", "Renault", "JAC", "Mitsubishi", "Soueast", "Zeekr", "Leapmotor", "JMEV"]},
    # ---- competencia ----
    {"nombre": "Nissan Paraguay",     "url": "https://www.nissan.com.py",     "propio": False, "js": False, "js_sub": True, "marcas": ["Nissan"]},
    {"nombre": "Nipon (Mitsubishi)",  "url": "https://www.nipon.com.py",      "propio": False, "js": False, "marcas": ["Mitsubishi"]},
    {"nombre": "Kia Paraguay (Garden)", "url": "https://www.kia.com.py/modelos", "propio": False, "js": True, "marcas": ["Kia"]},
    {"nombre": "Chery Paraguay (Garden)", "url": "https://www.chery.com.py",  "propio": False, "js": True,  "marcas": ["Chery"]},
    {"nombre": "Geely Paraguay",      "url": "https://geelyparaguay.com",     "propio": False, "js": False, "marcas": ["Geely"]},
    {"nombre": "Hyundai Paraguay",    "url": "https://www.hyundai.com.py",    "propio": False, "js": True,  "marcas": ["Hyundai"]},
    {"nombre": "Diesa (VW/Honda/BYD)", "url": "https://www.diesa.com.py",     "propio": False, "js": False, "marcas": ["Volkswagen", "Honda", "BYD"]},
    {"nombre": "Toyotoshi (Toyota)",  "url": "https://www.toyotoshi.com.py",  "propio": False, "js": False, "marcas": ["Toyota"]},
    {"nombre": "Automaq (Peugeot/Citroën)", "url": "https://automaq.com.py",  "propio": False, "js": False, "marcas": ["Peugeot", "Citroën"]},
    {"nombre": "Grupo Garden",        "url": "https://www.garden.com.py",     "propio": False, "js": False, "marcas": ["Kia", "Chevrolet", "Mazda", "Chery", "Geely", "Volvo"]},
    {"nombre": "DLS Motors (GAC)",    "url": "https://www.dlsmotors.com.py",  "propio": False, "js": False, "marcas": ["GAC"]},
]

# Modelos de la competencia. Los propios salen del catálogo del pipeline
# (src/catalog/models_py.py), que se valida contra los anuncios reales.
# Los de acá son los que CADAM registra con volumen en 2025-2026 más los
# que cada marca exhibe en su web paraguaya.
COMPETENCIA = {
    "Nissan": ["Kait", "Kicks", "Sentra", "Qashqai", "X-Trail", "Frontier", "Pathfinder", "Patrol", "Versa", "Magnite"],
    "Kia": ["Picanto", "Soluto", "Sonet", "Seltos", "Sportage", "Sorento", "Carnival", "Niro", "EV5", "EV9", "Tasman", "K3", "Carens", "K2700", "Stonic"],
    "Chery": ["Tiggo 2", "Tiggo 4", "Tiggo 7", "Tiggo 8", "T2", "T4", "T7", "T8", "Himla", "M7", "Arrizo"],
    "Geely": ["GX3", "Emgrand", "Coolray", "Azkarra", "Starray", "Cityray", "EX5", "Okavango", "Monjaro", "Galaxy"],
    "Hyundai": ["Creta", "HB20", "Tucson", "Santa Fe", "Kona", "Venue", "Grand i10", "i10", "Staria", "Palisade", "Ioniq"],
    "Toyota": ["Hilux", "Corolla Cross", "Corolla", "Fortuner", "Yaris", "RAV4", "SW4", "Hiace", "Raize", "Land Cruiser", "Prado", "Yaris Cross"],
    "Volkswagen": ["Polo", "Voyage", "Virtus", "T-Cross", "Taos", "Amarok", "Nivus", "Saveiro", "Tiguan", "Tera"],
    "Honda": ["WR-V", "HR-V", "CR-V", "Pilot", "City", "Civic", "ZR-V"],
    "BYD": ["Dolphin", "Song", "Yuan", "Han", "Tang", "Seal", "Atto 3", "Shark", "Sealion", "King"],
    "Chevrolet": ["Onix", "Tracker", "S10", "Montana", "Spin", "Equinox", "Trailblazer", "Spark", "Groove"],
    "Mazda": ["CX-5", "CX-30", "CX-3", "Mazda 3", "Mazda 2", "BT-50", "CX-60", "CX-90"],
    "Volvo": ["XC40", "XC60", "XC90", "EX30", "EX90"],
    "Peugeot": ["208", "2008", "3008", "5008", "Partner", "Expert", "Landtrek"],
    "Citroën": ["C3", "C3 Aircross", "C4", "C5 Aircross", "Berlingo", "Jumpy"],
    "GAC": ["GS8", "GS4", "GS3", "Emzoom", "Empow", "Aion"],
    "Suzuki": ["Fronx", "Swift", "Vitara", "Jimny", "Baleno", "Grand Vitara", "S-Presso", "Dzire"],
    "Fiat": ["Strada", "Toro", "Pulse", "Fastback", "Cronos", "Argo", "Mobi", "Fiorino"],
    "Ford": ["Ranger", "Territory", "Bronco", "Maverick", "Everest"],
    "MG": ["ZS", "MG3", "MG5", "HS", "RX5", "MG4"],
    "DFSK": ["K05S", "K01", "C35", "Glory 580"],
}


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Catálogos → regex por (marca, modelo)
# ---------------------------------------------------------------------------

def catalogo_propio() -> dict[str, dict[str, str]]:
    try:
        sys.path.insert(0, str(PROYECTO))
        from src.catalog.models_py import MODEL_CATALOG  # type: ignore
        return MODEL_CATALOG
    except Exception as e:  # pragma: no cover - solo si el repo está roto
        log(f"  ⚠️ sin catálogo propio ({e}); solo competencia")
        return {}


def compilar(marcas: list[str], propio: dict) -> dict[str, tuple[str, re.Pattern]]:
    """{nombre_visible: (marca, regex)} para las marcas pedidas."""
    out: dict[str, tuple[str, re.Pattern]] = {}
    for marca in marcas:
        if marca in propio:
            for nombre, pat in propio[marca].items():
                out[nombre] = (marca, re.compile(pat, re.I))
        for modelo in COMPETENCIA.get(marca, []):
            # Guiones y espacios opcionales: "X-Trail", "X Trail", "XTrail".
            flexible = re.escape(modelo).replace(r"\-", "[- ]?").replace(r"\ ", "[- ]?")
            out[f"{marca} {modelo}"] = (marca, re.compile(r"\b" + flexible + r"\b", re.I))
    return out


# ---------------------------------------------------------------------------
# Descarga
# ---------------------------------------------------------------------------

def chrome_disponible() -> str | None:
    for b in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(b)
        if p:
            return p
    return None


def descargar(url: str, js: bool, chrome: str | None) -> str | None:
    """HTML de la página. Con Chrome si el sitio se arma por JS y hay Chrome."""
    if js and chrome:
        try:
            r = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                 "--dump-dom", "--virtual-time-budget=8000", url],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0 and len(r.stdout) > 500:
                return r.stdout
        except (subprocess.TimeoutExpired, OSError):
            pass
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        # Un hosting suspendido responde 200 con una página que no es el sitio.
        if "suspendedpage" in resp.url or "suspended" in resp.text[:2000].lower():
            return None
        return resp.text
    except requests.RequestException:
        return None


def texto_visible(html: str) -> tuple[str, BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")), soup


def subpaginas(soup: BeautifulSoup, base: str) -> list[str]:
    host = urlparse(base).netloc
    vistos: list[str] = []
    for a in soup.find_all("a", href=True):
        l = urljoin(base, a["href"]).split("#")[0]
        if urlparse(l).netloc != host or l == base or l in vistos:
            continue
        if re.search(r"model|vehic|auto|suv|pick|promo|ofert|precio|catalog|linea|gama|electric|hibrid", l, re.I):
            vistos.append(l)
        if len(vistos) >= MAX_SUBPAGINAS:
            break
    return vistos


# ---------------------------------------------------------------------------
# Extracción
# ---------------------------------------------------------------------------

PRECIO_RE = re.compile(r"(US\$|USD|U\$S|\$|Gs\.?|G\$)\s?(\d{1,3}(?:[.,]\d{3})+)", re.I)


def precios_en(texto: str) -> list[tuple[int, str, int]]:
    """[(posición, moneda, monto)] con los montos fuera de rango descartados."""
    out = []
    for m in PRECIO_RE.finditer(texto):
        moneda = "Gs" if m.group(1).lower().startswith("g") else "USD"
        monto = int(re.sub(r"[.,]", "", m.group(2)))
        lo, hi = RANGO_GS if moneda == "Gs" else RANGO_USD
        if lo <= monto <= hi:
            out.append((m.start(), moneda, monto))
    return out


def analizar(texto: str, patrones: dict[str, tuple[str, re.Pattern]]):
    """Gama (modelos mencionados) y precio por modelo en un texto."""
    menciones: list[tuple[int, str]] = []
    for nombre, (_marca, rx) in patrones.items():
        for m in rx.finditer(texto):
            menciones.append((m.start(), nombre))
    menciones.sort()
    gama = sorted({n for _, n in menciones})
    precios: dict[str, tuple[str, int]] = {}
    for pos, moneda, monto in precios_en(texto):
        # El modelo que PRECEDE al precio, el más cercano. En las webs del
        # mercado el patrón es "MODELO ... desde US$ X" (Jetour, Renault, GWM
        # lo hacen igual), y en un listado el siguiente modelo viene pegado
        # después del precio: tomar el más cercano en cualquier dirección
        # asignaba a X70 el precio del X50. Solo si nada precede dentro de la
        # ventana se acepta el que sigue (fichas que ponen el precio arriba).
        # Una lista de modelos seguida de un solo precio ("X70, T1, T2, G700.
        # Los precios arrancan en US$ 14.990" — FAQ de Jetour) no es un precio
        # de ningún modelo: si en la ventana previa hay 3 o más modelos
        # distintos, el precio se descarta. En un listado real cada precio
        # tiene a lo sumo dos modelos antes (el suyo y el anterior).
        previos = {n for mpos, n in menciones if mpos < pos and pos - mpos <= VENTANA_CHARS}
        if len(previos) >= 3:
            continue
        mejor, dist = None, VENTANA_CHARS + 1
        for mpos, nombre in menciones:
            if mpos < pos and pos - mpos < dist:
                mejor, dist = nombre, pos - mpos
        if mejor is None:
            for mpos, nombre in menciones:
                if mpos > pos and mpos - pos < dist:
                    mejor, dist = nombre, mpos - pos
        if mejor is None:
            continue
        actual = precios.get(mejor)
        if actual is None or (actual[0] == moneda and monto < actual[1]):
            precios[mejor] = (moneda, monto)
    return gama, precios


def escanear(sitio: dict, propio: dict, chrome: str | None) -> dict | None:
    patrones = compilar(sitio["marcas"], propio)
    html = descargar(sitio["url"], sitio["js"], chrome)
    if not html:
        return None
    texto, soup = texto_visible(html)
    gama, precios = analizar(texto, patrones)
    paginas = 1
    for url in subpaginas(soup, sitio["url"]):
        h = descargar(url, sitio.get("js_sub", False), chrome)
        if not h:
            continue
        paginas += 1
        t, _ = texto_visible(h)
        g2, p2 = analizar(t, patrones)
        gama = sorted(set(gama) | set(g2))
        for modelo, (moneda, monto) in p2.items():
            actual = precios.get(modelo)
            if actual is None or (actual[0] == moneda and monto < actual[1]):
                precios[modelo] = (moneda, monto)
    return {
        "gama": gama,
        "precios": {m: {"moneda": mo, "monto": mt} for m, (mo, mt) in precios.items()},
        "paginas": paginas,
        "fecha": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Estado, histórico, eventos
# ---------------------------------------------------------------------------

def fmt(moneda: str, monto: int) -> str:
    n = f"{monto:,}".replace(",", ".")
    return f"USD {n}" if moneda == "USD" else f"Gs. {n}"


def comparar(nombre: str, previo: dict | None, actual: dict, propio: bool) -> list[str]:
    """Eventos legibles entre dos escaneos del mismo sitio."""
    eventos = []
    hoy = datetime.now().strftime("%d/%m %H:%M")
    quien = "propio" if propio else "competencia"
    if previo:
        nuevos = sorted(set(actual["gama"]) - set(previo.get("gama", [])))
        retirados = sorted(set(previo.get("gama", [])) - set(actual["gama"]))
        if nuevos:
            eventos.append(f"- **{hoy}** · {nombre} ({quien}) — modelo nuevo en la web: {', '.join(nuevos)}")
        if retirados:
            eventos.append(f"- **{hoy}** · {nombre} ({quien}) — ya no lista: {', '.join(retirados)}")
    for modelo, p in actual["precios"].items():
        antes = (previo or {}).get("precios", {}).get(modelo)
        if antes is None:
            if previo is not None:
                eventos.append(f"- **{hoy}** · {nombre} ({quien}) — precio publicado {modelo}: {fmt(p['moneda'], p['monto'])}")
        elif antes["moneda"] == p["moneda"] and antes["monto"] != p["monto"]:
            var = 100 * (p["monto"] - antes["monto"]) / antes["monto"]
            eventos.append(f"- **{hoy}** · {nombre} ({quien}) — {modelo}: {fmt(antes['moneda'], antes['monto'])} → "
                           f"{fmt(p['moneda'], p['monto'])} ({var:+.1f}%)")
    return eventos


def agregar_bitacora(eventos: list[str]) -> None:
    """Mismo marcador y misma estructura que usa monitor-competencia.sh."""
    if not eventos or not BITACORA.exists():
        return
    texto = BITACORA.read_text(encoding="utf-8")
    marca = "<!-- INICIO EVENTOS -->"
    if marca not in texto:
        return
    cabeza, cola = texto.split(marca, 1)
    encabezado = f"## {date.today().strftime('%Y-%m')}"
    bloque = "\n".join(eventos)
    if encabezado in cola:
        cola = cola.replace(encabezado + "\n", encabezado + "\n\n" + bloque + "\n", 1)
    else:
        cola = f"\n\n{encabezado}\n\n{bloque}\n" + cola.lstrip("\n")
    BITACORA.write_text(cabeza + marca + cola, encoding="utf-8")


def registrar_historico(filas: list[list]) -> None:
    nuevo = not HISTORICO.exists()
    with HISTORICO.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "sitio", "propio", "modelo", "moneda", "monto"])
        w.writerows(filas)


# ---------------------------------------------------------------------------
# Nota
# ---------------------------------------------------------------------------

def render(estado: dict, eventos_hoy: list[str]) -> str:
    hoy = date.today().isoformat()
    sitios_ok = [s for s in SITIOS if s["nombre"] in estado]
    con_precio = sum(len(estado[s["nombre"]]["precios"]) for s in sitios_ok)
    L = ["---", "tipo: precios-competencia",
         "fuente: webs oficiales, texto visible (Chrome para las que se arman por JS)",
         f"actualizado: {hoy}", f"sitios_leidos: {len(sitios_ok)}",
         f"modelos_con_precio: {con_precio}",
         "tags: [competencia, precios, gama, modelos]", "---", "",
         "# 💰 Precios y gama publicados, por modelo", "",
         f"Lo que cada web del mercado paraguayo publica hoy ({hoy}): qué modelos lista y a qué "
         "precio. Lo escribe el monitor de competencia en cada corrida; el histórico completo "
         "está en `output/competencia/precios_historico.csv`.", "",
         "Relacionado: [[📊 Mercado por Modelo 2026|Mercado por modelo]] · "
         "[[⚔️ Battle Cards Modelo vs Modelo|Battle Cards]] · [[⚔️ Bitácora de Competencia|Bitácora]]", "",
         "> [!warning] Alcance real, medido",
         "> Kia, Chery, Hyundai, Diesa, Automaq, Garden, Toyotoshi y DLS **no publican precio** en su web, "
         "ni siquiera renderizando el JavaScript. De ellos sale la gama, no el precio. Publican precio: "
         "las webs propias, Nissan (fichas de modelo) y Geely (algunas fichas).", "",
         "> [!info] Cómo se asocia precio y modelo",
         "> Al precio se le asigna el modelo mencionado más cerca en el texto y se guarda el más bajo "
         "visto (el \"desde\"). En una ficha de modelo acierta; en una home con carrusel puede cruzar. "
         "Ante la duda, el enlace del sitio está en cada tabla.", ""]

    def tabla(sitios: list[dict]) -> None:
        L.append("| Sitio | Modelo | Precio publicado | Visto |")
        L.append("| --- | --- | --: | --- |")
        vacios = []
        for s in sitios:
            e = estado[s["nombre"]]
            if not e["precios"]:
                vacios.append(s)
                continue
            for modelo, p in sorted(e["precios"].items(), key=lambda kv: kv[1]["monto"]):
                L.append(f"| [{s['nombre']}]({s['url']}) | {modelo} | **{fmt(p['moneda'], p['monto'])}** | {e['fecha']} |")
        if vacios:
            L.append("")
            L.append("Sin precio publicado: " + ", ".join(f"[{s['nombre']}]({s['url']})" for s in vacios))
        L.append("")

    L.append("## Nuestras marcas — lo que publicamos")
    L.append("")
    tabla([s for s in sitios_ok if s["propio"]])
    L.append("## Competencia — lo que publican")
    L.append("")
    tabla([s for s in sitios_ok if not s["propio"]])

    L.append("## Gama por sitio")
    L.append("")
    L.append("Modelos que cada web menciona hoy. Un modelo que aparece por primera vez o desaparece queda en la Bitácora.")
    L.append("")
    L.append("| Sitio | Modelos en la web | Páginas leídas |")
    L.append("| --- | --- | --: |")
    for s in sitios_ok:
        e = estado[s["nombre"]]
        L.append(f"| [{s['nombre']}]({s['url']}) | {', '.join(e['gama']) or '—'} | {e['paginas']} |")
    caidos = [s for s in SITIOS if s["nombre"] not in estado]
    if caidos:
        L.append("")
        L.append("No se pudo leer: " + ", ".join(f"[{s['nombre']}]({s['url']})" for s in caidos) +
                 ". Si es Nipon: su web está suspendida por el hosting (`suspendedpage.cgi`, visto el 2026-09-04).")
    L.append("")

    if eventos_hoy:
        L.append("## Cambios de esta corrida")
        L.append("")
        L.extend(eventos_hoy)
        L.append("")

    L.append("> [!danger] Uso interno")
    L.append("> Por ley de Paraguay no se puede hacer publicidad comparativa nombrando marcas o modelos "
             "de la competencia. Estos precios sirven para posicionar los nuestros — nunca para un copy público.")
    L.append("")
    L.append(f"*Generado el {hoy} por gama_precios_competencia.py*")
    L.append("")
    L.append(MARCADOR_FIN)
    return "\n".join(L)


def escribir_nota(nuevo: str) -> None:
    cola = ""
    if NOTA.exists():
        viejo = NOTA.read_text(encoding="utf-8")
        if MARCADOR_FIN in viejo:
            cola = viejo.split(MARCADOR_FIN, 1)[1]
    NOTA.parent.mkdir(parents=True, exist_ok=True)
    NOTA.write_text(nuevo + cola, encoding="utf-8")


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="escanea e imprime, no escribe nada")
    ap.add_argument("--sin-chrome", action="store_true", help="no usar Chrome aunque esté")
    ap.add_argument("--verbose", action="store_true", help="resumen por sitio aunque no haya cambios")
    args = ap.parse_args()
    # Patrón watchdog del cron: callado si no hay novedad. El detalle por
    # sitio solo se muestra a pedido o en dry-run; si no, cada 6 h llegaban
    # 18 líneas que no decían nada nuevo.
    detalle = args.verbose or args.dry_run

    OUTPUT.mkdir(parents=True, exist_ok=True)
    chrome = None if args.sin_chrome else chrome_disponible()
    propio = catalogo_propio()
    previo_todo = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    primera_vez = not previo_todo

    estado, eventos, filas = {}, [], []
    for sitio in SITIOS:
        r = escanear(sitio, propio, chrome)
        if r is None:
            if detalle:
                log(f"  ⚠️ {sitio['nombre']}: sin lectura")
            continue
        estado[sitio["nombre"]] = r
        previo = previo_todo.get(sitio["nombre"])
        ev = comparar(sitio["nombre"], previo, r, sitio["propio"])
        eventos.extend(ev)
        # Al histórico van los precios nuevos o cambiados (y todos la primera vez).
        for modelo, p in r["precios"].items():
            antes = (previo or {}).get("precios", {}).get(modelo)
            if antes is None or antes["monto"] != p["monto"]:
                filas.append([r["fecha"], sitio["nombre"], int(sitio["propio"]), modelo, p["moneda"], p["monto"]])
        if detalle:
            log(f"  {sitio['nombre']}: {len(r['gama'])} modelos, {len(r['precios'])} con precio, {r['paginas']} pág.")

    if not estado:
        if detalle:
            log("  ningún sitio respondió; no se toca nada")
        return 0

    if args.dry_run:
        print(render(estado, eventos))
        print(f"\n--- {len(eventos)} eventos, {len(filas)} filas de histórico (no se escribió) ---")
        return 0

    # Los sitios que hoy no respondieron conservan su último estado: una
    # caída puntual no debe borrar la gama conocida ni disparar "retirados".
    for nombre, e in previo_todo.items():
        estado.setdefault(nombre, e)

    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    if filas:
        registrar_historico(filas)
    if not primera_vez:
        agregar_bitacora(eventos)
    escribir_nota(render(estado, eventos if not primera_vez else []))

    # Patrón watchdog: solo hablar si hay algo que decir.
    if eventos and not primera_vez:
        log(f"💰 GAMA Y PRECIOS: {len(eventos)} cambio(s)")
        for e in eventos:
            log(e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
