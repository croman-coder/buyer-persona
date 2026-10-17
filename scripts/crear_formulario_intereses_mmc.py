#!/usr/bin/env python3
"""Crea en Meta el formulario de intereses de Mitsubishi (página Mitsubishi Motors Paraguay), SIN anuncios ni campaña.

Para qué: el brand de Mitsubishi pidió saber qué les gusta a quienes se interesan por la marca (deporte, música, comunidad)
para mapear su presencia en eventos (audio del 16-10-2026). Meta ya no entrega intereses declarados y ningún formulario
los preguntaba: este formulario los pregunta.

Qué NO hace: no crea campañas, conjuntos ni anuncios, y no toca nada de la agencia. Meta no tiene «pausa» para los
formularios (la API ignora DRAFT y los deja ACTIVE), así que se crea y se ARCHIVA enseguida: archivado no se puede usar
en un anuncio ni recoge nada, y se reactiva con --activar (comprobado el 16-10-2026). Para usarlo hace falta un anuncio,
que se crea en PAUSA y con el OK de Croman y de la brand manager de Mitsubishi (Cecilia).

Reglas de la pregunta: solo gustos y clubes. Nada sensible (religión, salud, política, ingresos): Meta no lo permite en
formularios y la ley de datos personales tampoco.

Uso:
    venv/bin/python3 scripts/crear_formulario_intereses_mmc.py            # muestra lo que crearía; no llama a Meta para escribir
    venv/bin/python3 scripts/crear_formulario_intereses_mmc.py --crear    # lo crea y lo deja archivado (en pausa)
    venv/bin/python3 scripts/crear_formulario_intereses_mmc.py --activar  # lo reactiva para usarlo en un anuncio
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://graph.facebook.com/v21.0"
PAGE = "103344941701936"                       # Mitsubishi Motors Paraguay
WEB = "https://www.mitsubishi-motors.com.py/"
NOMBRE = "SRPY - MITSUBISHI - Buyer Persona - 2026-10 - Intereses y comunidad"
ESTADO = ROOT / "output" / "raw" / "formulario_intereses_mmc.json"


def opciones(*pares: tuple[str, str]) -> list[dict[str, str]]:
    return [{"key": k, "value": v} for k, v in pares]


QUESTIONS = [
    {"type": "CUSTOM", "key": "tiempo_libre", "label": "¿Qué te gusta hacer en tu tiempo libre?", "options": opciones(
        ("futbol_deportes", "Fútbol y otros deportes"), ("motores", "Automovilismo y motos"), ("aventura", "Aventura, 4x4 y camping"),
        ("pesca_naturaleza", "Pesca y naturaleza"), ("musica_shows", "Música y shows"), ("familia", "Familia y paseos"),
        ("gastronomia", "Gastronomía y salidas"), ("otro", "Otro"))},
    {"type": "CUSTOM", "key": "comunidad", "label": "¿Participás de algún club o comunidad?", "options": opciones(
        ("club_motores", "Club de autos, motos o 4x4"), ("club_deportivo", "Club deportivo"),
        ("grupo_social", "Comunidad o grupo social"), ("ninguno", "Ninguno por ahora"))},
    {"type": "CUSTOM", "key": "cuando", "label": "¿Cuándo pensás comprar?", "options": opciones(
        ("este_mes", "Este mes"), ("proximos_3_meses", "En los próximos 3 meses"), ("solo_cotizando", "Solo estoy cotizando"))},
    {"type": "FULL_NAME", "key": "full_name"}, {"type": "PHONE", "key": "phone_number"},
    {"type": "EMAIL", "key": "email"}, {"type": "CITY", "key": "city"},
]
CONTEXT_CARD = {"title": "Mitsubishi Motors Paraguay · Comunidad", "style": "LIST_STYLE", "button_text": "Continuar",
                "content": ["Contanos qué te gusta y conocé más de Mitsubishi", "Un asesor de Santa Rosa te va a contactar",
                            "Con el respaldo de Santa Rosa"]}
THANK_YOU = {"title": "¡Gracias! Un asesor de Santa Rosa te va a contactar.", "body": "Mientras tanto podés conocer toda la gama en nuestro sitio.",
             "button_text": "Descubrí todos nuestros modelos", "button_type": "VIEW_WEBSITE", "website_url": WEB, "enable_messenger": False}


def payload(estado: str | None = None) -> dict[str, str]:
    """Los parámetros del formulario, listos para el POST (sin el token)."""
    d = {"name": NOMBRE, "locale": "es_LA",
         "privacy_policy": json.dumps({"url": WEB, "link_text": "Política de privacidad"}),
         "follow_up_action_url": WEB, "question_page_custom_headline": "Contanos qué te gusta",
         "context_card": json.dumps(CONTEXT_CARD, ensure_ascii=False), "questions": json.dumps(QUESTIONS, ensure_ascii=False),
         "thank_you_page": json.dumps(THANK_YOU, ensure_ascii=False),
         "is_optimized_for_quality": "true", "block_display_for_non_targeted_viewer": "false"}
    if estado:
        d["status"] = estado
    return d


def _llamar(metodo: str, ruta: str, token: str, datos: dict | None = None) -> dict:
    import requests
    if metodo == "GET":
        r = requests.get(f"{API}/{ruta}", params={**(datos or {}), "access_token": token}, timeout=60)
    else:
        r = requests.post(f"{API}/{ruta}", data={**(datos or {}), "access_token": token}, timeout=60)
    return r.json()


def crear(token: str) -> dict:
    pt = _llamar("GET", PAGE, token, {"fields": "access_token"}).get("access_token")
    if not pt:
        raise SystemExit("No se pudo obtener el token de la página de Mitsubishi.")
    ya = _llamar("GET", f"{PAGE}/leadgen_forms", pt, {"fields": "id,name,status", "limit": 100}).get("data", [])
    igual = [f for f in ya if f.get("name") == NOMBRE]
    if igual:
        raise SystemExit(f"Ya existe un formulario con ese nombre ({igual[0]['id']}, {igual[0].get('status')}). No se crea otro.")
    r = _llamar("POST", f"{PAGE}/leadgen_forms", pt, payload())
    if "error" in r:
        raise SystemExit(f"Meta respondió: {r['error'].get('message')}")
    aviso = None
    if not _llamar("POST", r["id"], pt, {"status": "ARCHIVED"}).get("success"):
        aviso = "El formulario se creó pero no se pudo archivar: quedó ACTIVE, sin anuncios (no recoge nada). Archivarlo a mano."
    estado = _llamar("GET", r["id"], pt, {"fields": "name,status,leads_count"})
    return {"id": r["id"], "estado": estado.get("status"), "leads": estado.get("leads_count"), "aviso": aviso}


def activar(token: str) -> dict:
    """Reactiva el formulario creado (el de output/raw/formulario_intereses_mmc.json) para poder usarlo en un anuncio."""
    fid = json.loads(ESTADO.read_text(encoding="utf-8"))["form_id"]
    pt = _llamar("GET", PAGE, token, {"fields": "access_token"}).get("access_token")
    if not _llamar("POST", fid, pt, {"status": "ACTIVE"}).get("success"):
        raise SystemExit(f"No se pudo reactivar el formulario {fid}.")
    return {"id": fid, "estado": _llamar("GET", fid, pt, {"fields": "status"}).get("status")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crear", action="store_true", help="lo crea en Meta y lo deja archivado (necesita el OK de Croman)")
    ap.add_argument("--activar", action="store_true", help="reactiva el formulario ya creado para usarlo en un anuncio")
    a = ap.parse_args()
    print(f"Formulario: {NOMBRE}\nPágina: Mitsubishi Motors Paraguay ({PAGE})\nPreguntas:")
    for q in QUESTIONS:
        ops = " | ".join(o["value"] for o in q.get("options", []))
        print(f"  - {q['type']:10} {q.get('label', ''):48} {ops}")
    if not (a.crear or a.activar):
        print("\nSin --crear: no se escribió nada en Meta.")
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    token = os.environ.get("META_ADS_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Falta META_ADS_ACCESS_TOKEN en .env")
    if a.activar:
        print(f"\nReactivado: {activar(token)}")
        return
    r = crear(token)
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps({"form_id": r["id"], "nombre": NOMBRE, "page": PAGE, "estado": r["estado"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nCreado: {r['id']} · estado {r['estado']} · leads {r['leads']}" + (f"\n⚠️ {r['aviso']}" if r["aviso"] else ""))


if __name__ == "__main__":
    main()
