#!/usr/bin/env python3
"""Qué herramientas de marketing carga cada web del mercado, y cuándo cambian.

Abre la portada de cada sitio (la misma lista que gama_precios_competencia.py)
en Chrome headless, guarda el registro de red de Chrome (--log-net-log) y
clasifica cada pedido a terceros por herramienta: pixel de Meta y TikTok,
Google Ads, Campaign Manager, GA4, Clarity, programática (Adobe, Xandr,
OpenX...), CRM y chat (Customer.io, HubSpot, Bitrix24...). Con las cuentas
que se ven en la URL (ID de pixel, AW-..., GTM-...).

Por qué: una herramienta nueva en la web de un competidor (TikTok, una DSP,
un CRM) dice dónde va a pautar o cómo trabaja sus leads antes de que se vea
en los anuncios. En las webs propias avisa si se cae un pixel.

Salió de las pruebas con REA del 2026-10-15 (nota «🔬 REA — Ingeniería
inversa»). REA hace la misma captura, pero el servidor no tiene Node; Chrome
con --log-net-log da los mismos dominios sin dependencias nuevas (medido con
kia.com.py: 59 dominios, los mismos que encontró REA).

Lo que NO ve: lo que carga recién al hacer scroll o clic, lo que se envía
desde el servidor del competidor (Conversions API) y lo que espera un
consentimiento de cookies.

Una herramienta que no aparece una semana queda marcada «no se vio esta
semana» y recién se da de baja a la segunda: algunas se cargan con demora.

Salidas:
  output/competencia/stack_marketing.json             estado por sitio
  Buyer Persona/Competencia/🛰️ Stack de Marketing — Competencia.md   nota regenerada
  Buyer Persona/Competencia/⚔️ Bitácora de Competencia.md   eventos (alta, baja, cuenta nueva)

Uso: stack_marketing_competencia.py [--dry-run] [--solo TEXTO] [--verbose]
Corre los lunes 05:00 en el servidor (Hermes, sin agente); también a mano.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from gama_precios_competencia import HEADERS, OUTPUT, SITIOS, VAULT, agregar_bitacora, chrome_disponible, log

NOTA = VAULT / "Competencia" / "🛰️ Stack de Marketing — Competencia.md"
ESTADO = OUTPUT / "stack_marketing.json"
MARCADOR_FIN = "<!-- hermes:fin -->"
ESPERA_MS = 10_000     # tiempo virtual que Chrome deja correr la página
TIMEOUT_S = 90

CATEGORIAS = ["Pauta", "Medición", "Programática y datos", "CRM, chat y automatización"]


def _firma(herramienta: str, categoria: str, dominios: str, cuando: str | None = None, ids=()) -> dict:
    return {"herramienta": herramienta, "categoria": categoria, "dominios": tuple(dominios.split()),
            "cuando": re.compile(cuando) if cuando else None,
            "ids": [(re.compile(rx), plantilla) for rx, plantilla in ids]}


# Una firma aplica si el host es (o es subdominio de) uno de sus dominios y,
# si tiene `cuando`, la URL lo cumple. `ids` saca la cuenta de la URL.
FIRMAS = [
    # --- Pauta ---
    _firma("Meta Pixel", "Pauta", "facebook.com", r"facebook\.com/tr\b", [(r"[?&]id=(\d+)", "{}")]),
    _firma("Meta Pixel", "Pauta", "connect.facebook.net", r"fbevents|/signals/", [(r"/signals/config/(\d+)", "{}")]),
    _firma("TikTok Pixel", "Pauta", "analytics.tiktok.com analytics-ipv6.tiktokw.us business-api.tiktok.com",
           ids=[(r"[?&]sdkid=([A-Z0-9]+)", "{}")]),
    _firma("Google Ads", "Pauta", "googletagmanager.com", r"[?&]id=AW-", [(r"[?&]id=AW-(\d+)", "AW-{}")]),
    _firma("Google Ads", "Pauta", "googleadservices.com googleads.g.doubleclick.net",
           ids=[(r"/pagead/(?:viewthrough)?conversion/(\d+)", "AW-{}")]),
    _firma("Google Ads", "Pauta", "google.com", r"/pagead/1p-(?:user-list|conversion)/",
           [(r"/pagead/1p-(?:user-list|conversion)/(\d+)", "AW-{}")]),
    _firma("Campaign Manager 360", "Pauta", "fls.doubleclick.net",
           ids=[(r"//(\d+)\.fls\.doubleclick\.net", "{}"), (r"[;?&]src=(\d+)", "{}")]),
    _firma("Campaign Manager 360", "Pauta", "ad.doubleclick.net", r"/activity", [(r"[;?&]src=(\d+)", "{}")]),
    _firma("Campaign Manager 360", "Pauta", "googletagmanager.com", r"[?&]id=DC-", [(r"[?&]id=DC-(\d+)", "{}")]),
    _firma("X (Twitter) Ads", "Pauta", "ads-twitter.com analytics.twitter.com", ids=[(r"[?&]txn_id=(\w+)", "{}")]),
    _firma("X (Twitter) Ads", "Pauta", "t.co", r"/i/adsct", [(r"[?&]txn_id=(\w+)", "{}")]),
    # Gateway de la Conversions API de Meta en un subdominio propio
    # (capi.garden.com.py lo usan Kia y Nissan) o el script de Meta en S3.
    _firma("Meta Conversions API (gateway)", "Pauta", "*", r"^https?://capi\.|//capi-automation\.s3\."),
    _firma("Microsoft Ads (UET)", "Pauta", "bat.bing.com", ids=[(r"[?&]ti=(\d+)", "{}")]),
    _firma("LinkedIn Insight", "Pauta", "snap.licdn.com px.ads.linkedin.com", ids=[(r"[?&]pid=(\d+)", "{}")]),
    _firma("Pinterest Tag", "Pauta", "ct.pinterest.com", ids=[(r"[?&]tid=(\d+)", "{}")]),
    _firma("Snap Pixel", "Pauta", "sc-static.net tr.snapchat.com"),
    _firma("Taboola", "Pauta", "taboola.com"),
    _firma("Outbrain", "Pauta", "outbrain.com"),
    _firma("Criteo", "Pauta", "criteo.com criteo.net"),
    # --- Medición ---
    _firma("Google Tag Manager", "Medición", "googletagmanager.com", r"gtm\.js", [(r"[?&]id=(GTM-[A-Z0-9]+)", "{}")]),
    _firma("Google Analytics 4", "Medición", "googletagmanager.com", r"[?&]id=G-", [(r"[?&]id=(G-[A-Z0-9]+)", "{}")]),
    _firma("Google Analytics 4", "Medición", "google-analytics.com analytics.google.com",
           ids=[(r"[?&]tid=(G-[A-Z0-9]+)", "{}")]),
    _firma("Microsoft Clarity", "Medición", "clarity.ms", ids=[(r"clarity\.ms/tag/([a-z0-9]+)", "{}")]),
    _firma("Hotjar", "Medición", "hotjar.com hotjar.io", ids=[(r"[?&]hjid=(\d+)", "{}"), (r"hotjar-(\d+)\.js", "{}")]),
    _firma("Adobe Analytics", "Medición", "omtrdc.net 2o7.net"),
    _firma("Adobe Launch (tags)", "Medición", "adobedtm.com"),
    _firma("Cloudflare Web Analytics", "Medición", "cloudflareinsights.com"),
    _firma("Segment", "Medición", "segment.com segment.io"),
    _firma("Mixpanel", "Medición", "mixpanel.com"),
    _firma("Yandex Metrica", "Medición", "mc.yandex.ru mc.yandex.com"),
    # --- Programática y datos ---
    _firma("Adobe Audience Manager", "Programática y datos", "demdex.net"),
    _firma("Adobe Advertising (DSP)", "Programática y datos", "everesttech.net"),
    _firma("Xandr", "Programática y datos", "adnxs.com"),
    _firma("OpenX", "Programática y datos", "openx.net"),
    _firma("Index Exchange", "Programática y datos", "casalemedia.com"),
    _firma("PubMatic", "Programática y datos", "pubmatic.com"),
    _firma("Magnite", "Programática y datos", "rubiconproject.com"),
    _firma("BidSwitch", "Programática y datos", "bidswitch.net"),
    _firma("The Trade Desk", "Programática y datos", "adsrvr.org"),
    _firma("Amazon Ads", "Programática y datos", "amazon-adsystem.com"),
    _firma("Zeta Global", "Programática y datos", "rfihub.com rfihub.net rezync.com"),
    _firma("LiveRamp", "Programática y datos", "rlcdn.com"),
    _firma("LiveIntent", "Programática y datos", "liadm.com"),
    _firma("Eyeota", "Programática y datos", "eyeota.net"),
    _firma("Neustar (TransUnion)", "Programática y datos", "agkn.com"),
    _firma("Media.net", "Programática y datos", "media.net"),
    _firma("Nexxen (Tremor)", "Programática y datos", "tremorhub.com"),
    _firma("Quantcast", "Programática y datos", "quantserve.com quantcount.com"),
    _firma("Lotame", "Programática y datos", "crwdcntrl.net"),
    _firma("e-planning", "Programática y datos", "e-planning.net"),
    # --- CRM, chat y automatización ---
    _firma("Customer.io", "CRM, chat y automatización", "customer.io"),
    _firma("iCommKT (email marketing)", "CRM, chat y automatización", "icommkt.online icommkt.com"),
    _firma("Chat Santa Rosa", "CRM, chat y automatización", "chat.santarosa.lat"),
    _firma("HubSpot", "CRM, chat y automatización",
           "hs-scripts.com hs-analytics.net hsforms.com hsforms.net hubspot.com hs-banner.com usemessages.com"),
    _firma("Bitrix24", "CRM, chat y automatización", "bitrix24.com bitrix24.es bitrix24.com.br bitrix24.ru bitrix24.net"),
    _firma("RD Station", "CRM, chat y automatización", "rdstation.com rdstation.com.br"),
    _firma("Salesforce Marketing Cloud", "CRM, chat y automatización", "exacttarget.com igodigital.com"),
    _firma("Pardot", "CRM, chat y automatización", "pardot.com"),
    _firma("Tawk.to", "CRM, chat y automatización", "tawk.to"),
    _firma("JivoChat", "CRM, chat y automatización", "jivosite.com jivochat.com"),
    _firma("Botmaker", "CRM, chat y automatización", "botmaker.com"),
    _firma("Zendesk", "CRM, chat y automatización", "zdassets.com zendesk.com zopim.com"),
    _firma("Intercom", "CRM, chat y automatización", "intercom.io intercomcdn.com"),
    _firma("OneSignal", "CRM, chat y automatización", "onesignal.com"),
    _firma("Leadster", "CRM, chat y automatización", "leadster.com.br"),
    _firma("Callbell", "CRM, chat y automatización", "callbell.eu"),
    _firma("Tidio", "CRM, chat y automatización", "tidio.co tidiochat.com"),
    _firma("Smartsupp", "CRM, chat y automatización", "smartsupp.com"),
    _firma("GetButton (WhatsApp)", "CRM, chat y automatización", "getbutton.io"),
    _firma("Elfsight (widgets)", "CRM, chat y automatización", "elfsight.com"),
]
CATEGORIA = {f["herramienta"]: f["categoria"] for f in FIRMAS}

# Lo que no es una herramienta de marketing: el tráfico propio de Chrome
# (actualizaciones, Safe Browsing), CDNs, fuentes, videos, y los pedidos a
# dominios de Meta, Google o X que no son el pixel (SDK, mapas, captcha).
IGNORAR = tuple("""
    google.com google.com.py googleapis.com gstatic.com googleusercontent.com gvt1.com gvt2.com
    doubleclick.net googlesyndication.com googletagmanager.com googlevideo.com ggpht.com
    youtube.com ytimg.com youtube-nocookie.com facebook.com facebook.net fbcdn.net instagram.com
    cdninstagram.com twitter.com twimg.com t.co tiktok.com tiktokcdn.com bing.com
    cloudflare.com jsdelivr.net unpkg.com jquery.com bootstrapcdn.com fontawesome.com typekit.net
    cloudfront.net akamaihd.net akamaized.net vimeo.com vimeocdn.com w.org wp.com gravatar.com
    recaptcha.net hcaptcha.com wa.me whatsapp.com whatsapp.net withgoogle.com linkedin.com
    onlinewebfonts.com cdnfonts.com ipify.org
""".split())
# Lo que Chrome pide por su cuenta aunque la página no cargue.
CHROME = ("google.com", "googleapis.com", "googleusercontent.com", "gvt1.com", "gvt2.com")

_URL_EN_NETLOG = re.compile(r'"url"\s*:\s*"((?:[^"\\]|\\.)*)"')


# ---------------------------------------------------------------------------
# Lectura y clasificación
# ---------------------------------------------------------------------------

def urls_de_netlog(texto: str) -> set[str]:
    """URLs http(s) del registro de red de Chrome. Por regex y no json.loads:
    el registro pesa ~35 MB por sitio y, si Chrome se corta, queda sin cerrar."""
    urls = set()
    for m in _URL_EN_NETLOG.finditer(texto):
        try:
            u = json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            continue
        if u.startswith(("http://", "https://")):
            urls.add(u)
    return urls


def es_de(host: str, dominio: str) -> bool:
    return host == dominio or host.endswith("." + dominio)


def dominio_propio(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def identificar(host: str, url: str) -> list[tuple[str, str | None]]:
    hallado = []
    for f in FIRMAS:
        if "*" not in f["dominios"] and not any(es_de(host, d) for d in f["dominios"]):
            continue
        if f["cuando"] and not f["cuando"].search(url):
            continue
        ids = [plantilla.format(m.group(1)) for rx, plantilla in f["ids"] for m in [rx.search(url)] if m]
        hallado.extend((f["herramienta"], i) for i in ids or [None])
    return hallado


def clasificar(urls, propio: str) -> tuple[dict[str, list[str]], list[str]]:
    """{herramienta: [cuentas]} y los hosts de terceros que no tienen firma."""
    herramientas: dict[str, set[str]] = {}
    otros = set()
    for u in urls:
        host = (urlparse(u).hostname or "").lower()
        if not host or es_de(host, propio):
            continue
        hallado = identificar(host, u)
        if not hallado:
            if not any(es_de(host, d) for d in IGNORAR):
                otros.add(host)
            continue
        for herramienta, cuenta in hallado:
            herramientas.setdefault(herramienta, set())
            if cuenta:
                herramientas[herramienta].add(cuenta)
    return {h: sorted(c) for h, c in herramientas.items()}, sorted(otros)


def lectura_valida(urls: set[str], propio: str, html: str = "") -> bool:
    """El sitio cargó: hubo pedidos al propio dominio y, además, a algún
    tercero o una página de verdad. Si no, un sitio caído daría de baja todo."""
    hosts = {(urlparse(u).hostname or "").lower() for u in urls}
    if not any(es_de(h, propio) for h in hosts):
        return False
    terceros = [h for h in hosts if h and not es_de(h, propio) and not any(es_de(h, d) for d in CHROME)]
    pagina = len(html) > 5000 and "main-frame-error" not in html
    return bool(terceros) or pagina


def capturar(url: str, chrome: str) -> tuple[set[str], str]:
    """URLs pedidas al abrir la página, y el DOM final. Vacío si Chrome se
    colgó: una captura cortada dejaría herramientas afuera y, a la segunda
    semana, las daría de baja sin motivo."""
    with tempfile.TemporaryDirectory(prefix="stack-marketing-") as tmp:
        red = Path(tmp) / "red.json"
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
               f"--user-data-dir={tmp}/perfil", f"--user-agent={HEADERS['User-Agent']}",
               f"--log-net-log={red}", "--net-log-capture-mode=Default",
               "--disable-background-networking", "--disable-component-update", "--disable-sync",
               "--disable-features=Translate,OptimizationHints,MediaRouter",
               f"--virtual-time-budget={ESPERA_MS}", "--dump-dom", url]
        # Grupo de procesos propio: si se cuelga, se matan también los
        # procesos hijos de Chrome (renderer, GPU), no solo el principal.
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                             start_new_session=True)
        try:
            html, _ = p.communicate(timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
            return set(), ""
        texto = red.read_text(encoding="utf-8", errors="replace") if red.exists() else ""
    return urls_de_netlog(texto), html or ""


# ---------------------------------------------------------------------------
# Cambios
# ---------------------------------------------------------------------------

def comparar(sitio: dict, previo: dict | None, herramientas: dict[str, list[str]], cuando: str):
    """Estado nuevo del sitio y eventos para la bitácora. Una herramienta que
    falta una semana queda con faltas=1; a la segunda se da de baja."""
    quien = "propio" if sitio["propio"] else "competencia"
    pre = f"- **{cuando}** · {sitio['nombre']} ({quien}) — "
    antes = (previo or {}).get("herramientas", {})
    nuevo, altas, cuentas, bajas = {}, [], [], []
    for h in sorted(herramientas):
        ids = sorted(set(herramientas[h]))
        if h in antes:
            nuevas = [i for i in ids if i not in antes[h]["ids"]]
            if nuevas:
                cuentas.append(f"{pre}cuenta nueva de {h}: {', '.join(nuevas)}")
            ids = sorted(set(antes[h]["ids"]) | set(ids))
        elif previo is not None:
            altas.append(f"{pre}empezó a usar {h}" + (f" ({', '.join(ids)})" if ids else ""))
        nuevo[h] = {"ids": ids, "faltas": 0}
    for h in sorted(set(antes) - set(herramientas)):
        faltas = antes[h]["faltas"] + 1
        if faltas >= 2:
            bajas.append(f"{pre}dejó de cargar {h} (dos semanas sin verla)")
        else:
            nuevo[h] = {"ids": antes[h]["ids"], "faltas": faltas}
    return {"herramientas": nuevo}, altas + cuentas + bajas


# ---------------------------------------------------------------------------
# Nota
# ---------------------------------------------------------------------------

def _celda(e: dict, categoria: str) -> str:
    items = [h + (" (no se vio esta semana)" if v["faltas"] else "")
             for h, v in sorted(e["herramientas"].items()) if CATEGORIA.get(h) == categoria]
    return ", ".join(items) or "—"


def _tabla(estado: dict, sitios: list[dict], hoy: str) -> list[str]:
    L = ["| Sitio | " + " | ".join(CATEGORIAS) + " |", "|---" * (len(CATEGORIAS) + 1) + "|"]
    caidos = []
    for s in sitios:
        e = estado.get(s["nombre"])
        if e is None:
            caidos.append(f"[{s['nombre']}]({s['url']})")
            continue
        cuando = "" if e.get("fecha", hoy) == hoy else f" *(leído el {e['fecha']})*"
        L.append(f"| [{s['nombre']}]({s['url']}){cuando} | " + " | ".join(_celda(e, c) for c in CATEGORIAS) + " |")
    if caidos:
        L += ["", "No se pudo leer: " + ", ".join(caidos) + "."]
    return L


def render(estado: dict, sitios: list[dict], hoy: str) -> str:
    competencia = [s for s in sitios if not s["propio"]]
    propios = [s for s in sitios if s["propio"]]
    nuestras = {h for s in propios for h in estado.get(s["nombre"], {}).get("herramientas", {})}
    falta: dict[str, list[str]] = {}
    for s in competencia:
        for h in estado.get(s["nombre"], {}).get("herramientas", {}):
            if h not in nuestras:
                falta.setdefault(h, []).append(s["nombre"])

    L = ["---", "tipo: competencia", "tema: herramientas de marketing de las webs del mercado",
         f"actualizado: {hoy}", "tags: [competencia, marketing, pixel, generado]", "---", "",
         "# 🛰️ Stack de Marketing — Competencia", "",
         "> [!info] Qué herramientas de marketing carga cada web",
         "> Cada lunes a las 05:00 el servidor abre la portada de cada sitio en Chrome, la deja correr 10 s "
         "sin tocar nada y anota a qué herramientas de terceros llama (pixel, analítica, programática, CRM). "
         "No ve lo que carga recién con scroll o clic, lo que espera a que el visitante acepte las cookies "
         "(así carga el pixel de Meta en algunos sitios, el nuestro de JAC incluido), ni lo que se manda desde "
         "el servidor del sitio (Conversions API): un «—» no siempre quiere decir que no lo tenga. Una herramienta que no aparece una semana queda «no se vio esta semana»; "
         "a la segunda se da de baja y queda en la bitácora.", "",
         "Relacionado: [[⚔️ Benchmark Competitivo]] · [[⚔️ Bitácora de Competencia]] · "
         "[[🔬 REA — Ingeniería inversa (pruebas 2026-10-15)]]", "",
         "## Competencia", ""]
    L += _tabla(estado, competencia, hoy)
    L += ["", "## Nuestros sitios", ""]
    L += _tabla(estado, propios, hoy)
    L += ["", "## Lo que usa la competencia y nosotros no", ""]
    if falta:
        for h in sorted(falta, key=lambda h: (CATEGORIAS.index(CATEGORIA[h]), h)):
            L.append(f"- **{h}** ({CATEGORIA[h]}): {', '.join(falta[h])}")
    else:
        L.append("Nada: todo lo que carga la competencia lo tenemos en al menos uno de nuestros sitios.")

    L += ["", "## Cuentas detectadas", "",
          "> [!note]- Cuentas por sitio (si cambia una, puede haber cambiado la agencia)",
          "> | Sitio | Herramienta | Cuentas |", "> |---|---|---|"]
    for s in sitios:
        for h, v in sorted(estado.get(s["nombre"], {}).get("herramientas", {}).items()):
            if v["ids"]:
                L.append(f"> | {s['nombre']} | {h} | {', '.join(v['ids'])} |")

    otros: dict[str, list[str]] = {}
    for s in sitios:
        for host in estado.get(s["nombre"], {}).get("otros", []):
            otros.setdefault(host, []).append(s["nombre"])
    if otros:
        L += ["", f"> [!note]- Dominios de terceros sin clasificar ({len(otros)}): si alguno es una herramienta, "
                  "sumarle una firma en `FIRMAS`"]
        L += [f"> - `{host}` — {', '.join(n)}" for host, n in sorted(otros.items())]

    L += ["", "> [!danger] Uso interno",
          "> Por ley de Paraguay no se puede hacer publicidad comparativa nombrando marcas o modelos de la "
          "competencia. Esto sirve para decidir qué medir y dónde pautar nosotros, nunca para un copy público.", "",
          f"*Generado el {hoy} por stack_marketing_competencia.py*", "", MARCADOR_FIN]
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
    ap.add_argument("--dry-run", action="store_true", help="captura e imprime, no escribe nada")
    ap.add_argument("--solo", help="solo los sitios cuyo nombre contiene este texto")
    ap.add_argument("--verbose", action="store_true", help="resumen por sitio aunque no haya cambios")
    args = ap.parse_args()
    detalle = args.verbose or args.dry_run

    chrome = chrome_disponible()
    if not chrome:
        log("❌ stack de marketing: no hay Chrome en esta máquina")
        return 1
    sitios = [s for s in SITIOS if not args.solo or args.solo.lower() in s["nombre"].lower()]
    previo_todo = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    primera_vez = not previo_todo
    hoy = date.today().isoformat()
    cuando = datetime.now().strftime("%d/%m %H:%M")

    estado, eventos = {}, []
    for sitio in sitios:
        propio = dominio_propio(sitio["url"])
        for _ in range(2):        # un reintento: a veces Chrome se cuelga al arrancar
            urls, html = capturar(sitio["url"], chrome)
            if lectura_valida(urls, propio, html):
                break
        else:
            if detalle:
                log(f"  ⚠️ {sitio['nombre']}: sin lectura ({len(urls)} pedidos)")
            continue
        herramientas, otros = clasificar(urls, propio)
        e, ev = comparar(sitio, previo_todo.get(sitio["nombre"]), herramientas, cuando)
        e.update(fecha=hoy, otros=otros)
        estado[sitio["nombre"]] = e
        eventos.extend(ev)
        if detalle:
            log(f"  {sitio['nombre']}: {', '.join(sorted(herramientas)) or 'ninguna'}"
                + (f" · {len(otros)} sin clasificar" if otros else ""))

    if not estado:
        if detalle:
            log("  ningún sitio respondió; no se toca nada")
        return 0

    # Los sitios que hoy no respondieron conservan su último estado.
    for nombre, e in previo_todo.items():
        estado.setdefault(nombre, e)

    if args.dry_run:
        print(render(estado, sitios, hoy))
        print(f"\n--- {len(eventos)} eventos (no se escribió) ---")
        for e in eventos:
            print(e)
        return 0

    OUTPUT.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    if not primera_vez:
        agregar_bitacora(eventos)
    escribir_nota(render(estado, SITIOS, hoy))

    # Patrón watchdog: solo hablar si hay algo que decir.
    if eventos and not primera_vez:
        log(f"🛰️ STACK DE MARKETING: {len(eventos)} cambio(s)")
        for e in eventos:
            log(e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
