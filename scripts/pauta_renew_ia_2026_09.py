#!/usr/bin/env python3
"""
Pauta Renew IA 2026-09 · Clavos y Mantecas → ventas por WhatsApp.

Dos campañas aparte de la pauta vigente de Renew, solo hasta el 30-09-2026,
USD 100 en total, con las 10 gráficas del Drive de marketing:

  CLAVOS (difíciles de vender) · USD 60 · ABO
      Un conjunto por unidad con USD 12 de presupuesto total cada uno: cada
      clavo tiene su parte asegurada y ninguno queda sin salir.
  MANTECAS (las más vendibles) · USD 40 · CBO
      Presupuesto de campaña: Meta lleva la plata a las unidades que
      consiguen conversaciones más baratas.

Esquema copiado de la campaña que ya funciona en la cuenta ("LEADS 2026 -
VENTAS WHATSAPP"): objetivo Ventas, optimiza conversaciones, destino
WhatsApp 0991 703 063, Paraguay, Advantage+ audience. Encima, lo del
Buyer Persona (mismo esquema que Renault/MMC IA): públicos de retargeting
y similares como sugerencia de audiencia y la edad de la persona de cada
marca como rango sugerido.

Todo se crea en PAUSA a nivel campaña: los conjuntos y anuncios quedan
listos, así activar son dos clics. Presupuesto de por vida con fecha de
fin, así el total nunca pasa de USD 100 aunque se active tarde.

Idempotente: el estado queda en output/pauta_renew_ia_2026-09.json y una
segunda corrida retoma donde quedó.
"""
import json, os, sys, time
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
T = os.environ["META_ADS_ACCESS_TOKEN"]
V = "https://graph.facebook.com/v21.0"
A = "act_1006324631233144"           # Renew Usados
PAGE = "118807831155424"             # página Renew
IG = "17841458717719802"             # Instagram Renew
WA = "595991703063"                  # WhatsApp 0991 703 063 (el de la campaña vigente)
PIXEL = "1864069597698281"           # "Renew Paraguay", el único que dispara
PIEZAS = ROOT / "data/fuentes/creatividades/renew_2026-09/piezas"
OUT = ROOT / "output" / "pauta_renew_ia_2026-09.json"
FIN = "2026-09-30T23:59:59-0300"     # Paraguay es UTC-3 todo el año desde 2024

state = json.loads(OUT.read_text()) if OUT.exists() else {}
def save(): OUT.write_text(json.dumps(state, indent=1, ensure_ascii=False))

def call(method, path, **data):
    body = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in data.items()}
    r = requests.request(method, f"{V}/{path}", data={"access_token": T, **body}, timeout=180).json()
    if "error" in r:
        e = r["error"]
        raise RuntimeError(f"{path}: {e.get('error_user_title') or ''} {e.get('error_user_msg') or e.get('message')}".strip())
    return r
def get(path, **q): return requests.get(f"{V}/{path}", params={"access_token": T, **q}, timeout=60).json()

# ---------------------------------------------------------------- unidades
# Datos de la gráfica (precio contado y cuota referencial) + versión y color
# del stock de usados (data/fuentes/stock_unidades_usadas.xlsx, 11-09-2026).
# edad = rango sugerido según la persona Renew de esa marca en el vault; si
# la marca no tiene persona propia en Renew, la del Comprador Renew general.
CLAVOS = {
    "GLC 200": dict(pieza="clavos__glc_200", marca="Mercedes-Benz", modelo="GLC 200 4MATIC", anio=2023,
                    color="negro", contado="52.000", cuota="7.800.000", edad=(35, 54), persona="Comprador Renew"),
    "GLC 220d": dict(pieza="clavos__mercdes_glc_220d", marca="Mercedes-Benz", modelo="GLC 220d", anio=2017,
                     color="blanco", contado="27.000", cuota="3.900.000", edad=(35, 54), persona="Comprador Renew"),
    "Peugeot 2008": dict(pieza="clavos__peugeot_2008", marca="Peugeot", modelo="2008 Active 1.6", anio=2020,
                         color="rojo", contado="7.000", cuota="1.100.000", edad=(25, 44), persona="Renew Peugeot"),
    "Territory": dict(pieza="clavos__territory", marca="Ford", modelo="Territory Titanium", anio=2023,
                      color="blanco", contado="19.500", cuota="2.800.000", edad=(35, 54), persona="Renew Ford"),
    "Tucson": dict(pieza="clavos__tucson", marca="Hyundai", modelo="Tucson GL 2.0", anio=2022,
                   color="azul", contado="22.000", cuota="3.200.000", edad=(35, 54), persona="Renew Hyundai"),
}
MANTECAS = {
    "Uni-K": dict(pieza="mantecas__changan_unik", marca="Changan", modelo="Uni-K AWD", anio=2023,
                  color="blanco", contado="26.000", cuota="3.800.000", edad=(35, 54), persona="Comprador Renew"),
    "Fastback": dict(pieza="mantecas__fiat_fastback", marca="Fiat", modelo="Fastback Limited", anio=2024,
                     color="gris", contado="18.000", cuota="2.600.000", edad=(35, 64), persona="Renew Fiat"),
    "H6 PHEV": dict(pieza="mantecas__gwm_h6_phev", marca="GWM", modelo="H6 PHEV 4WD", anio=2024,
                    color="gris", contado="26.500", cuota="3.800.000", edad=(25, 44), persona="Renew GWM"),
    "X70": dict(pieza="mantecas__jetour_x70", marca="Jetour", modelo="X70 GLX", anio=2023,
                color="rojo", contado="17.500", cuota="2.500.000", edad=(25, 44), persona="Renew Jetour"),
    "Zeekr X": dict(pieza="mantecas__zeekr_x", marca="Zeekr", modelo="X Flagship", anio=2025,
                    color="verde", contado="35.000", cuota="5.000.000", edad=(35, 54), persona="Comprador Renew"),
}
GRUPOS = {
    "CLAVOS": dict(unidades=CLAVOS, total=6000, modo="ABO",
                   gancho="💥 Oportunidad Renew · unidad única."),
    "MANTECAS": dict(unidades=MANTECAS, total=4000, modo="CBO",
                     gancho="🔥 Unidad única · consultá hoy."),
}

LEGAL = ("*Cuota referencial con entrega inicial del 20 %. Sujeto a aprobación bancaria y tipo de cambio "
         "del día. Consultá planes de financiación disponibles.")
PIE = "📍Av. Mariscal López 4561 e/ Nicanor Torales y Bélgica.\n📲 0991 703 063"

def textos(u, gancho):
    nombre = f"{u['marca']} {u['modelo']} {u['anio']}"
    feed = (f"👉{u['marca'].upper()} {u['modelo'].upper()} {u['anio']}💥\n{gancho}\n\n"
            f"* Año {u['anio']}\n* Versión {u['modelo']}\n* Color {u['color']}\n"
            f"* Contado USD {u['contado']}*\n* Cuota referencial Gs. {u['cuota']}*\n\n"
            "✅ Con el respaldo de Santa Rosa\n✅ Tomamos tu usado como parte de pago\n✅ Financiación bancaria\n\n"
            f"{LEGAL}\n\n{PIE}")
    story = (f"{nombre} · Contado USD {u['contado']}* · Cuota ref. Gs. {u['cuota']}*. "
             "Tomamos tu usado. Escribinos por WhatsApp 👇\n*Entrega inicial 20 %, sujeto a aprobación bancaria.")
    titulo = f"{u['marca']} {u['modelo'].split(' ')[0]} {u['anio']} · USD {u['contado']}"
    saludo = f"¡Hola! Quiero más información del {nombre} (USD {u['contado']})."
    return nombre, feed, story, titulo, saludo

def bienvenida(saludo):
    """Mismo formato que el anuncio que ya corre (JETOUR X90), con el saludo de la unidad."""
    return json.dumps({
        "type": "VISUAL_EDITOR", "version": 2, "landing_screen_type": "welcome_message", "media_type": "text",
        "text_format": {"customer_action_type": "autofill_message",
                        "message": {"autofill_message": {"content": saludo}, "text": "¡Hola! ¿Cómo podemos ayudarte?"}},
        "user_edit": True, "surface": "visual_editor_new", "autofill_message_edited": True,
        "performance_booster_enabled": False,
    }, ensure_ascii=False)

# ---------------------------------------------------------------- 1. piezas
for grupo in GRUPOS.values():
    for m, u in grupo["unidades"].items():
        for fmt in ("4x5", "9x16", "1x1"):
            k = f"img_{u['pieza']}_{fmt}"
            if k in state: continue
            p = PIEZAS / f"{u['pieza']}__{fmt}.jpg"
            r = requests.post(f"{V}/{A}/adimages", data={"access_token": T},
                              files={"filename": (p.name, p.read_bytes(), "image/jpeg")}, timeout=180).json()
            if "error" in r: raise RuntimeError(f"adimages {p.name}: {r['error'].get('message')}")
            state[k] = next(iter(r["images"].values()))["hash"]; save()
print("piezas subidas:", sum(1 for k in state if k.startswith("img_")))

# ---------------------------------------------------------------- 2. públicos
# Sin datos personales: todo sale de interacciones con Meta y del píxel.
AN0 = 365 * 86400
# Meta no deja mezclar orígenes (Instagram y Facebook) en una misma regla: un público por red.
ORIGENES = {
    "ig": ("Instagram", {"id": IG, "type": "ig_business"}, "ig_business_profile_all"),
    "fb": ("Facebook", {"id": PAGE, "type": "page"}, "page_engaged"),
}
for k, (red, fuente, evento) in ORIGENES.items():
    if f"aud_{k}" in state: continue
    rule = {"inclusions": {"operator": "or", "rules": [
        {"event_sources": [fuente], "retention_seconds": AN0,
         "filter": {"operator": "and", "filters": [{"field": "event", "operator": "eq", "value": evento}]}}]}}
    r = call("POST", f"{A}/customaudiences", name=f"RENEW | IA | Interacción {red} 365d",
             description=f"Interactuó con {red} de Renew en el último año. Pauta IA 2026-09.",
             rule=rule, prefill=1)
    state[f"aud_{k}"] = r["id"]; save()
if "aud_web" not in state:
    rule = {"inclusions": {"operator": "or", "rules": [
        {"event_sources": [{"id": PIXEL, "type": "pixel"}], "retention_seconds": 180 * 86400,
         "filter": {"operator": "and", "filters": [{"field": "url", "operator": "i_contains", "value": ""}]}},
    ]}}
    r = call("POST", f"{A}/customaudiences", name="RENEW | IA | Web 180d (píxel Renew Paraguay)",
             description="Visitó el sitio en los últimos 180 días. Reemplaza al 'RENEW | Público Web' de 90 días, que Meta marca chico y desactualizado.",
             rule=rule, prefill=1)
    state["aud_web"] = r["id"]; save()
for seed in ("ig", "fb", "web"):
    k = f"lal_{seed}"
    if k in state: continue
    try:
        r = call("POST", f"{A}/customaudiences", name=f"RENEW | IA | Similar 1% PY ← {seed}",
                 subtype="LOOKALIKE", origin_audience_id=state[f"aud_{seed}"],
                 lookalike_spec={"ratio": 0.01, "country": "PY"})
        state[k] = r["id"]; save()
    except RuntimeError as e:
        # La semilla recién creada puede estar llenándose: se reintenta en la próxima corrida.
        state[f"{k}_pendiente"] = str(e)[:200]; save()
        print(f"similar {seed}: pendiente →", str(e)[:160])
CLAVES_AUD = ("aud_ig", "aud_fb", "aud_web", "lal_ig", "lal_fb", "lal_web")
AUD = [state[k] for k in CLAVES_AUD if k in state]
print("públicos:", {k: state[k] for k in CLAVES_AUD if k in state})

# ---------------------------------------------------------------- 3-5. campañas, conjuntos, anuncios
RULES = [
    {"priority": 1, "customization_spec": {"publisher_platforms": ["facebook", "instagram"],
        "facebook_positions": ["story", "facebook_reels"], "instagram_positions": ["story", "reels"]},
     "image_label": {"name": "story"}, "body_label": {"name": "bstory"}},
    {"priority": 2, "customization_spec": {"publisher_platforms": ["facebook", "instagram"],
        "facebook_positions": ["feed", "profile_feed"], "instagram_positions": ["stream", "explore", "explore_home", "profile_feed"]},
     "image_label": {"name": "feed"}, "body_label": {"name": "bfeed"}},
    {"priority": 3, "customization_spec": {"publisher_platforms": ["facebook", "instagram", "audience_network", "messenger"]},
     "image_label": {"name": "sq"}, "body_label": {"name": "bfeed"}},
]
WA_LINK = f"https://api.whatsapp.com/send?phone={WA}"

for gname, g in GRUPOS.items():
    ck = f"campaign_{gname}"
    if ck not in state:
        extra = {"is_adset_budget_sharing_enabled": "false"} if g["modo"] == "ABO" else {
            "lifetime_budget": g["total"], "bid_strategy": "LOWEST_COST_WITHOUT_CAP"}
        r = call("POST", f"{A}/campaigns",
                 name=f"RENEW | IA Buyer Persona | Ventas WhatsApp | {gname} | 23 al 30-09",
                 objective="OUTCOME_SALES", status="PAUSED", buying_type="AUCTION",
                 special_ad_categories=[], **extra)
        state[ck] = r["id"]; save(); print("campaña", gname, r["id"])

    por_unidad = g["total"] // len(g["unidades"])
    for m, u in g["unidades"].items():
        sk = f"adset_{u['pieza']}"
        if sk not in state:
            # 23-09: con la edad de la persona como sugerencia (age_range) no
            # entregó nada en una hora; Renault IA, igual pero sin age_range,
            # sí entrega. Clavos: 6 públicos como sugerencia de Advantage+, con
            # la expansión de similares y personalizados encendida (sin
            # targeting_relaxation_types, Meta rechaza después cualquier edición
            # del conjunto: "No se pueden desactivar las opciones de Advantage").
            # Mantecas: Advantage+ abierto, igual que LEADS 2026 - VENTAS WHATSAPP.
            targeting = {
                "geo_locations": {"countries": ["PY"], "location_types": ["home", "recent"]},
                "age_min": 22, "age_max": 65,             # piso de la campaña vigente; Advantage+ exige 65
                "targeting_automation": {"advantage_audience": 1},
            }
            if gname == "CLAVOS":
                targeting["custom_audiences"] = [{"id": x} for x in AUD]
                targeting["targeting_relaxation_types"] = {"lookalike": 1, "custom_audience": 1}
            presupuesto = {"lifetime_budget": por_unidad} if g["modo"] == "ABO" else {}
            r = call("POST", f"{A}/adsets",
                     name=f"{m} | IA | Similares + Retargeting + Persona {u['edad'][0]}-{u['edad'][1]} | hasta 30-09",
                     campaign_id=state[ck], status="ACTIVE",
                     optimization_goal="CONVERSATIONS", billing_event="IMPRESSIONS",
                     bid_strategy="LOWEST_COST_WITHOUT_CAP", destination_type="WHATSAPP",
                     promoted_object={"page_id": PAGE, "whatsapp_phone_number": WA},
                     start_time=time.strftime("%Y-%m-%dT%H:%M:%S-0300", time.gmtime(time.time() - 3 * 3600 + 600)),
                     end_time=FIN, targeting=targeting, **presupuesto)
            state[sk] = r["id"]; save(); print("  conjunto", m, r["id"])

        nombre, feed, story, titulo, saludo = textos(u, g["gancho"])
        # Formato del anuncio de WhatsApp que ya anda en la cuenta (JETOUR X90):
        # una imagen, object_story_spec.link_data, sin mejoras automáticas.
        # La primera versión (asset_feed_spec con una pieza por ubicación) la
        # aceptaba el API pero el editor de Ads Manager la mostraba rota:
        # "Selecciona una imagen" (#1487212), "falta el título" (#2016052) y
        # "no se pudo analizar la llamada a la acción" (#1373054), y no
        # entregaba. Va la 4:5: la gráfica es vertical y así queda casi entera.
        crk = f"creative2_{u['pieza']}"
        if crk not in state:
            r = call("POST", f"{A}/adcreatives", name=f"{nombre} · IA · {gname.lower()} · WhatsApp 4:5 · 2026-09",
                     object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "link_data": {
                         "link": WA_LINK,
                         "message": feed,
                         "name": titulo,
                         "description": "Agendá tu test drive por WhatsApp",
                         "image_hash": state[f"img_{u['pieza']}_4x5"],
                         "call_to_action": {"type": "WHATSAPP_MESSAGE",
                                            "value": {"app_destination": "WHATSAPP", "link": WA_LINK}},
                         "page_welcome_message": bienvenida(saludo),
                     }})
            state[crk] = r["id"]; save(); time.sleep(1)

        ak = f"ad_{u['pieza']}"
        if ak not in state:
            r = call("POST", f"{A}/ads", name=f"{m} | IA | {gname.lower()} | WhatsApp | 2026-09",
                     adset_id=state[sk], creative={"creative_id": state[crk]}, status="ACTIVE")
            state[ak] = r["id"]; state[f"ad_creative_{u['pieza']}"] = state[crk]; save(); print("  anuncio", m, r["id"])
        elif state.get(f"ad_creative_{u['pieza']}") != state[crk]:
            # Anuncio ya creado con el creativo viejo: se le cambia el creativo, conserva el ID.
            call("POST", state[ak], creative={"creative_id": state[crk]},
                 name=f"{m} | IA | {gname.lower()} | WhatsApp | 2026-09")
            state[f"ad_creative_{u['pieza']}"] = state[crk]; save(); time.sleep(1)
            print("  anuncio", m, "→ creativo nuevo", state[crk])

print("\nlisto — estado en", OUT.relative_to(ROOT))
