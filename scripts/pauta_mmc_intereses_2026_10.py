#!/usr/bin/env python3
"""Arma EN PAUSA la campaña, el conjunto y el anuncio que usan el formulario de intereses de Mitsubishi.

Contexto: el brand de Mitsubishi pidió saber qué les gusta a quienes se interesan por la marca (deporte, música, comunidad)
para sus eventos (audio del 16-10-2026). El formulario ya está creado (scripts/crear_formulario_intereses_mmc.py). Este
script lo reactiva y arma el anuncio, TODO EN PAUSA: nada gasta ni se publica hasta que Croman y la brand digan que sí.

Decisiones (y por qué):
- Segmentación por VEHÍCULO (camioneta, SUV, Montero), nunca por pasatiempos: si se apuntara a «fans del fútbol», las
  respuestas dirían «fútbol» por cómo se segmentó y no por lo que les gusta.
- Se excluyen los públicos de quienes ya dejaron sus datos o abrieron un formulario (los mismos que excluye la campaña de
  L200 del Buyer Persona): no se paga por gente que ya está en Bitrix.
- Sin precios, ofertas, tasas ni plazos: el anuncio solo invita a contar qué les gusta. La oferta del mes no entra.
- Imagen: la de una L200 en un camino de tierra, sin texto ni precio, que ya está en la cuenta (la de la agencia), con el
  mensaje escrito encima: en Stories no se ve el texto del anuncio, solo la imagen y el botón, y sin eso nadie sabría de qué
  se trata. Es PROVISORIA: una pickup en el campo puede inclinar las respuestas hacia «aventura y 4x4»; marketing puede
  cambiarla por una pieza propia.
- Presupuesto de USD 15 por día: PROPUESTA para poder activarlo con Cecilia; la regla del Buyer Persona pide al menos USD 5.

Qué NO hace: no toca ninguna campaña ni anuncio de la agencia ni sus presupuestos. Crea cosas nuevas y separadas.

Uso:
    venv/bin/python3 scripts/pauta_mmc_intereses_2026_10.py            # muestra lo que armaría; no escribe en Meta
    venv/bin/python3 scripts/pauta_mmc_intereses_2026_10.py --crear    # reactiva el formulario y arma todo en PAUSA
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://graph.facebook.com/v21.0"
CUENTA = "act_506680188632635"                 # Mitsubishi Paraguay (MMC)
PAGE = "103344941701936"                       # Mitsubishi Motors Paraguay
IG = "17841445317172019"                       # Instagram de Mitsubishi
ESTADO = ROOT / "output" / "raw" / "pauta_mmc_intereses_2026_10.json"
FORMULARIO = ROOT / "output" / "raw" / "formulario_intereses_mmc.json"

PRESUPUESTO_DIA_USD = 15
IMAGEN_HASH = "1cddd3ba5c51136977e6dd65075ebad4"   # L200 en camino de tierra, 1080x1920, sin texto ni precio (de la cuenta)
INTERESES = [{"id": "6003025566093", "name": "Camioneta (vehículo)"},
             {"id": "6003304473660", "name": "Vehículo utilitario deportivo (vehículos)"},
             {"id": "6003470330764", "name": "Mitsubishi Montero"}]
# Los mismos públicos que ya excluye la campaña «Buyer Persona | Leads | L200 | 2026-10 V2» de la cuenta
EXCLUIR = [("120249164586790663", "RMK WEB | Lead (180)"), ("120252450678590663", "RMK FORM | Montero | Abrió y no envió | 90 días"),
           ("120252450736180663", "LEAD FORM | L200 | Enviado | 90 días"), ("120252959226730663", "MONTERO | FORMULARIOS ABIERTOS NO ENVIADOS")]

NOMBRE_CAMPANA = "MITSUBISHI | Buyer Persona | Intereses y comunidad | Leads | 2026-10"
NOMBRE_CONJUNTO = "Intereses y comunidad | PY 25-55 | Vehículo (sin pasatiempos)"
NOMBRE_ANUNCIO = "MITSUBISHI | Intereses y comunidad | Pickup 9:16 | 2026-10"
TEXTO = "Contanos qué te gusta y conocé más de Mitsubishi. Respondé unas preguntas cortas y un asesor de Santa Rosa te contacta."
TITULO = "Comunidad Mitsubishi"
DESCRIPCION = "Contanos qué te gusta"


def campana() -> dict:
    return {"name": NOMBRE_CAMPANA, "objective": "OUTCOME_LEADS", "status": "PAUSED", "buying_type": "AUCTION",
            "special_ad_categories": [], "is_adset_budget_sharing_enabled": "false"}


def targeting() -> dict:
    return {"geo_locations": {"countries": ["PY"], "location_types": ["home", "recent"]}, "age_min": 25, "age_max": 55,
            "flexible_spec": [{"interests": INTERESES}],
            "excluded_custom_audiences": [{"id": i} for i, _ in EXCLUIR],
            "targeting_automation": {"advantage_audience": 0},
            # la imagen es vertical: se muestra en Stories y Reels de Facebook e Instagram
            "publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["story", "facebook_reels"],
            "instagram_positions": ["story", "reels"]}


def conjunto(campana_id: str) -> dict:
    return {"name": NOMBRE_CONJUNTO, "campaign_id": campana_id, "status": "PAUSED", "daily_budget": PRESUPUESTO_DIA_USD * 100,
            "optimization_goal": "LEAD_GENERATION", "billing_event": "IMPRESSIONS", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "destination_type": "ON_AD", "promoted_object": {"page_id": PAGE}, "targeting": targeting()}


def html_imagen(base64_jpg: str) -> str:
    """La imagen de la L200 con el mensaje en la zona segura de Stories (lejos del nombre arriba, de los logos y del botón)."""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#111}}
.f{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{base64_jpg}) center/cover}}
.p{{position:absolute;left:70px;right:70px;top:340px;padding:46px 54px 52px;border-radius:34px;background:rgba(12,12,14,.62);
    font-family:Inter,Archivo,Arial,sans-serif;color:#fff}}
.k{{font-weight:700;font-size:32px;letter-spacing:.14em;color:#ff4a3d;margin-bottom:18px}}
.t{{font-weight:800;font-size:104px;line-height:1.04;letter-spacing:-.01em}}
.s{{font-weight:500;font-size:46px;line-height:1.25;margin-top:26px;color:#f1f1f1}}
</style></head><body><div class="f"></div><div class="p"><div class="k">COMUNIDAD MITSUBISHI</div>
<div class="t">Contanos<br>qué te gusta</div><div class="s">Respondé unas preguntas cortas y conocé más de Mitsubishi</div></div></body></html>"""


def imagen_con_texto(token: str) -> str:
    """Baja la imagen de la cuenta, le escribe el mensaje con Chrome y la sube de nuevo: devuelve el hash de la nueva."""
    import requests
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise SystemExit("Falta google-chrome o chromium para escribir el texto en la imagen")
    datos = _llamar("GET", f"{CUENTA}/adimages", token, {"hashes": [IMAGEN_HASH], "fields": "url"})["data"]
    jpg = requests.get(datos[0]["url"], timeout=90).content
    with tempfile.TemporaryDirectory() as d:
        html, png = Path(d) / "i.html", Path(d) / "i.png"
        html.write_text(html_imagen(base64.b64encode(jpg).decode()), encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--window-size=1080,1920",
                        f"--screenshot={png}", f"file://{html}"], check=True, timeout=120, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        r = requests.post(f"{API}/{CUENTA}/adimages", data={"access_token": token},
                          files={"filename": ("MITSUBISHI_intereses_pickup_9x16_texto.png", png.read_bytes(), "image/png")}, timeout=120).json()
    if "error" in r:
        raise RuntimeError(f"Meta respondió al subir la imagen: {r['error'].get('message')}")
    return list(r["images"].values())[0]["hash"]


def creativo(formulario_id: str, imagen_hash: str = IMAGEN_HASH) -> dict:
    return {"name": "MITSUBISHI · Intereses y comunidad · Pickup 9:16 con texto · 2026-10",
            "object_story_spec": {"page_id": PAGE, "instagram_user_id": IG, "link_data": {
                "image_hash": imagen_hash, "link": "http://fb.me/", "message": TEXTO, "name": TITULO, "description": DESCRIPCION,
                "call_to_action": {"type": "LEARN_MORE", "value": {"lead_gen_form_id": formulario_id, "link": "http://fb.me/"}}}}}


def anuncio(conjunto_id: str, creativo_id: str) -> dict:
    return {"name": NOMBRE_ANUNCIO, "adset_id": conjunto_id, "creative": {"creative_id": creativo_id}, "status": "PAUSED"}


def _llamar(metodo: str, ruta: str, token: str, datos: dict | None = None) -> dict:
    import requests
    datos = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in (datos or {}).items()}
    if metodo == "GET":
        r = requests.get(f"{API}/{ruta}", params={**datos, "access_token": token}, timeout=90)
    else:
        r = requests.post(f"{API}/{ruta}", data={**datos, "access_token": token}, timeout=90)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"Meta respondió en {ruta}: {j['error'].get('message')} {j['error'].get('error_user_msg', '')}")
    return j


def crear(token: str) -> dict:
    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    formulario_id = json.loads(FORMULARIO.read_text(encoding="utf-8"))["form_id"]
    pt = _llamar("GET", PAGE, token, {"fields": "access_token"})["access_token"]
    if "formulario_activo" not in estado:                     # 1. reactivar el formulario (estaba archivado)
        _llamar("POST", formulario_id, pt, {"status": "ACTIVE"})
        estado["formulario_activo"] = True
        ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")
    if "imagen" not in estado:                                # 2. la imagen con el mensaje escrito
        estado["imagen"] = imagen_con_texto(token)
        ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")
        print(f"  imagen: {estado['imagen']}")
    for clave, ruta, datos in (("campana", f"{CUENTA}/campaigns", lambda: campana()),
                               ("conjunto", f"{CUENTA}/adsets", lambda: conjunto(estado["campana"])),
                               ("creativo", f"{CUENTA}/adcreatives", lambda: creativo(formulario_id, estado["imagen"])),
                               ("anuncio", f"{CUENTA}/ads", lambda: anuncio(estado["conjunto"], estado["creativo"]))):
        if clave in estado:
            continue
        estado[clave] = _llamar("POST", ruta, token, datos())["id"]
        if clave == "anuncio":
            estado["creativo_en_anuncio"] = estado["creativo"]
        ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")
        print(f"  {clave}: {estado[clave]}")
    if estado.get("creativo_en_anuncio") != estado["creativo"]:   # un creativo nuevo para un anuncio ya creado (sigue en pausa)
        _llamar("POST", estado["anuncio"], token, {"creative": {"creative_id": estado["creativo"]}})
        estado["creativo_en_anuncio"] = estado["creativo"]
        ESTADO.write_text(json.dumps(estado, indent=1), encoding="utf-8")
        print("  creativo del anuncio actualizado")
    return estado


def revisar(token: str, estado: dict) -> dict:
    """Lee de vuelta el estado de todo: tiene que estar en pausa."""
    campos = {"campana": "name,status,effective_status", "conjunto": "name,status,effective_status,daily_budget",
              "anuncio": "name,status,effective_status"}
    return {k: _llamar("GET", estado[k], token, {"fields": c}) for k, c in campos.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crear", action="store_true", help="reactiva el formulario y arma campaña, conjunto y anuncio EN PAUSA")
    a = ap.parse_args()
    print(f"Campaña:  {NOMBRE_CAMPANA}\nConjunto: {NOMBRE_CONJUNTO} · USD {PRESUPUESTO_DIA_USD}/día · Paraguay, 25-55 años")
    print("Intereses (de vehículo): " + ", ".join(i["name"] for i in INTERESES))
    print("Excluye: " + " | ".join(n for _, n in EXCLUIR))
    print(f"Anuncio:  {NOMBRE_ANUNCIO}\n  «{TEXTO}»\n  Título: {TITULO}")
    if not a.crear:
        print("\nSin --crear: no se escribió nada en Meta.")
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    token = os.environ.get("META_ADS_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Falta META_ADS_ACCESS_TOKEN en .env")
    estado = crear(token)
    print("\nVerificación (tiene que decir PAUSED en las tres):")
    for k, v in revisar(token, estado).items():
        print(f"  {k:9} {v.get('status')} / {v.get('effective_status')} · {v.get('name')}")


if __name__ == "__main__":
    main()
