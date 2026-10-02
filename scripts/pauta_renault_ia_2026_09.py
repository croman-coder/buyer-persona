#!/usr/bin/env python3
"""
Pauta Renault · IA Buyer Persona · Koleos + Master · septiembre 2026.
Crea (todo en PAUSA): 2 formularios, 1 campaña OUTCOME_LEADS (ABO),
2 conjuntos (Koleos, Master) con lookalike + retargeting + segmentación,
y por conjunto 1 anuncio de imagen (1:1 / 4:5 / 9:16 por ubicación) + 1 reel.
Presupuesto: USD 600 en 30 días → Koleos USD 9/día, Master USD 11/día
(misma proporción que el sugerido del motor: 589 / 787).
"""
import json, os, sys, time
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
T = os.environ["META_ADS_ACCESS_TOKEN"]
V = "https://graph.facebook.com/v21.0"
A = "act_956049245637827"
PAGE = "111900348505782"
IG = "17841458364035470"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/claude-1000/-home-croman-Escritorio-BUYER-PERSONA/39847bea-44b3-4d28-b80d-9777dcae56b1/scratchpad/drive_fabri/NUEVA PAUTA IA")
OUT = ROOT / "output" / "pauta_renault_ia_2026-09.json"


def call(method, path, **data):
    r = requests.request(method, f"{V}/{path}", data={"access_token": T, **{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in data.items()}}, timeout=120)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{path}: {json.dumps(j['error'], ensure_ascii=False)}")
    return j


def get(path, **q):
    return requests.get(f"{V}/{path}", params={"access_token": T, **q}, timeout=60).json()


state = json.loads(OUT.read_text()) if OUT.exists() else {}
def save():
    OUT.parent.mkdir(exist_ok=True, parents=True); OUT.write_text(json.dumps(state, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ audiencias
LOOKALIKE = ["120250271050560518", "120250271086430518", "120250271104860518"]   # 1% form abierto / IG 30D / FB 30D
RETARGET = ["120250271050060518", "120249455485140518", "120249455489180518", "120249455491890518"]  # form abierto·no enviado / web / IG / FB
CA = [{"id": i} for i in LOOKALIKE + RETARGET]

def interest_ids(names):
    out = []
    for n in names:
        r = get("search", type="adinterest", q=n, limit=3, locale="es_LA").get("data", [])
        if r:
            out.append({"id": r[0]["id"], "name": r[0]["name"]})
    return out

MODELOS = {
    "Koleos": {
        "dir": "KOLEOS", "budget": 900, "age": (25, 50),
        "interests": ["SUV", "Hybrid vehicles", "Renault", "Vehículos", "Automóviles"],
        "form": {
            "name": "SRPY - KOLEOS - IA Buyer Persona - 2026-09",
            "headline": "Koleos Full Hybrid E-Tech: cotizá tu plan en 1 minuto",
            "context": {"title": "Koleos Full Hybrid E-Tech esprit Alpine",
                        "content": ["Contado USD 36.990 o desde USD 400/mes*", "Híbrido E-Tech: arrancás en eléctrico y gastás menos", "Stock disponible para entrega inmediata", "*Sujeto a entrega inicial"],
                        "button_text": "Quiero mi cotización"},
            "questions": [
                {"type": "CUSTOM", "key": "cuando_cambias", "label": "¿Cuándo pensás cambiar tu vehículo?", "options": [{"value": "Este mes", "key": "este_mes"}, {"value": "En los próximos 3 meses", "key": "3_meses"}, {"value": "Solo estoy mirando", "key": "mirando"}]},
                {"type": "CUSTOM", "key": "como_compras", "label": "¿Cómo pensás comprarlo?", "options": [{"value": "Financiación", "key": "financiacion"}, {"value": "Contado", "key": "contado"}, {"value": "Entrego mi usado + financiación", "key": "usado"}]},
                {"type": "FULL_NAME", "key": "full_name"}, {"type": "PHONE", "key": "phone_number"}, {"type": "EMAIL", "key": "email"}, {"type": "CITY", "key": "city"},
            ],
        },
        "copy": {
            "body_feed": "Koleos Full Hybrid E-Tech esprit Alpine. Híbrido de verdad: arrancás en eléctrico, gastás menos y llegás con estilo.\n\n✔ Contado USD 36.990 o desde USD 400/mes*\n✔ Tecnología híbrida E-Tech e interior premium esprit Alpine\n✔ Stock disponible para entrega inmediata en Santa Rosa\n\nDejá tus datos y un asesor te arma tu plan hoy.\n*Sujeto a entrega inicial.",
            "body_story": "Koleos Full Hybrid E-Tech · desde USD 400/mes* · Entrega inmediata. Pedí tu cotización 👇\n*Sujeto a entrega inicial.",
            "titles": ["Koleos Full Hybrid E-Tech · desde USD 400/mes", "Koleos híbrido · entrega inmediata"],
            "desc": "Cotizá en 1 minuto, sin compromiso.",
            "video_title": "Koleos Full Hybrid E-Tech · desde USD 400/mes",
        },
    },
    "Master": {
        "dir": "MASTER", "budget": 1100, "age": (25, 65),
        "interests": ["Pequeñas y medianas empresas", "Logística", "Furgoneta", "Distribución", "Espíritu empresarial"],
        "form": {
            "name": "SRPY - MASTER - IA Buyer Persona - 2026-09",
            "headline": "Renault Master: cotizá la versión que necesita tu negocio",
            "context": {"title": "Renault Master · para llevar tu negocio más lejos",
                        "content": ["Contado USD 37.990 o desde USD 450/mes*", "Versiones de carga y de pasajeros", "Financiación y planes para empresas", "*Sujeto a entrega inicial"],
                        "button_text": "Cotizar mi Master"},
            "questions": [
                {"type": "CUSTOM", "key": "uso", "label": "¿Para qué la usarías?", "options": [{"value": "Reparto / logística", "key": "reparto"}, {"value": "Transporte de pasajeros", "key": "pasajeros"}, {"value": "Mi propio negocio u oficio", "key": "negocio"}, {"value": "Otro", "key": "otro"}]},
                {"type": "CUSTOM", "key": "cuando", "label": "¿Cuándo la necesitás?", "options": [{"value": "Este mes", "key": "este_mes"}, {"value": "En los próximos 3 meses", "key": "3_meses"}, {"value": "Solo estoy cotizando", "key": "cotizando"}]},
                {"type": "CUSTOM", "key": "como_compras", "label": "¿Cómo pensás comprarla?", "options": [{"value": "Financiación", "key": "financiacion"}, {"value": "Contado", "key": "contado"}, {"value": "A nombre de mi empresa", "key": "empresa"}]},
                {"type": "FULL_NAME", "key": "full_name"}, {"type": "PHONE", "key": "phone_number"}, {"type": "EMAIL", "key": "email"}, {"type": "CITY", "key": "city"},
            ],
        },
        "copy": {
            "body_feed": "Renault Master: más capacidad para llevar tu negocio más lejos.\n\n✔ Contado USD 37.990 o desde USD 450/mes*\n✔ Versiones de carga y de pasajeros, para reparto, logística y transporte\n✔ Financiación y planes para empresas\n\nDejá tus datos y un asesor te cotiza la versión que necesita tu negocio.\n*Sujeto a entrega inicial.",
            "body_story": "Renault Master · desde USD 450/mes* · Carga o pasajeros. Cotizá la tuya 👇\n*Sujeto a entrega inicial.",
            "titles": ["Renault Master · desde USD 450/mes", "Master: el furgón para tu negocio"],
            "desc": "Versiones carga y pasajeros. Cotizá hoy.",
            "video_title": "Renault Master · desde USD 450/mes",
        },
    },
}

# ------------------------------------------------------------------ 1. formularios (token de página)
PT = get(PAGE, fields="access_token")["access_token"]
for m, cfg in MODELOS.items():
    key = f"form_{m}"
    if key in state:
        continue
    f = cfg["form"]
    payload = {
        "access_token": PT, "name": f["name"], "locale": "es_LA",
        "privacy_policy": json.dumps({"url": "https://renault.com.py/legalInfo.html", "link_text": "Información Legal"}),
        "follow_up_action_url": "https://renault.com.py/",
        "question_page_custom_headline": f["headline"],
        "context_card": json.dumps({"title": f["context"]["title"], "style": "LIST_STYLE", "content": f["context"]["content"], "button_text": f["context"]["button_text"]}),
        "questions": json.dumps(f["questions"]),
        "thank_you_page": json.dumps({"title": "¡Gracias! Un asesor de Renault Santa Rosa te contacta hoy.", "body": "Mientras tanto podés ver toda la gama en nuestro sitio.", "button_type": "VIEW_WEBSITE", "button_text": "Ver la gama", "website_url": "https://renault.com.py/"}),
        "is_optimized_for_quality": "true",
        "block_display_for_non_targeted_viewer": "false",
    }
    r = requests.post(f"{V}/{PAGE}/leadgen_forms", data=payload, timeout=60).json()
    if "error" in r:
        raise RuntimeError(f"form {m}: {r['error']}")
    state[key] = r["id"]; save(); print("form", m, r["id"])

# ------------------------------------------------------------------ 2. imágenes y videos
for m, cfg in MODELOS.items():
    d = SRC / cfg["dir"]
    imgs = {"1x1": next(d.glob("*_feed_pautas*.png")), "4x5": next(d.glob("*_feed 4.5_*.png")), "9x16": next(d.glob("*_IGS_*.png"))}
    for ratio, p in imgs.items():
        key = f"img_{m}_{ratio}"
        if key in state:
            continue
        r = requests.post(f"{V}/{A}/adimages", data={"access_token": T}, files={"filename": (p.name, p.read_bytes(), "image/png")}, timeout=120).json()
        if "error" in r:
            raise RuntimeError(f"img {p.name}: {r['error']}")
        state[key] = list(r["images"].values())[0]["hash"]; save(); print("img", m, ratio, state[key])
    key = f"video_{m}"
    if key not in state:
        p = next(d.glob("*.mp4"))
        r = requests.post(f"{V}/{A}/advideos", data={"access_token": T, "name": f"Renault {m} · Reel IA 2026-09"}, files={"source": (p.name, p.read_bytes(), "video/mp4")}, timeout=600).json()
        if "error" in r:
            raise RuntimeError(f"video {m}: {r['error']}")
        state[key] = r["id"]; save(); print("video", m, r["id"])

for m in MODELOS:
    for _ in range(40):
        st = get(state[f"video_{m}"], fields="status").get("status", {}).get("video_status")
        if st == "ready":
            break
        time.sleep(5)
    print("video", m, "status", st)

# ------------------------------------------------------------------ 3. campaña
if "campaign" not in state:
    r = call("POST", f"{A}/campaigns", name="RENAULT | IA Buyer Persona | Leads | Koleos + Master | 2026-09",
             objective="OUTCOME_LEADS", status="PAUSED", buying_type="AUCTION",
             special_ad_categories=[], is_adset_budget_sharing_enabled="false")
    state["campaign"] = r["id"]; save(); print("campaign", r["id"])

# ------------------------------------------------------------------ 4. conjuntos + anuncios
for m, cfg in MODELOS.items():
    if f"adset_{m}" not in state:
        ints = interest_ids(cfg["interests"])
        targeting = {
            "geo_locations": {"countries": ["PY"], "location_types": ["home", "recent"]},
            # Advantage+ audience: edad mínima como control duro, máxima fija en 65 (Meta no deja bajarla)
            "age_min": cfg["age"][0], "age_max": 65,
            "custom_audiences": CA,
            "flexible_spec": [{"interests": ints}] if ints else [],
            "targeting_automation": {"advantage_audience": 1, "individual_setting": {"age": 1}},
        }
        r = call("POST", f"{A}/adsets", name=f"{m} | IA | Lookalike + Retargeting + Intereses | PY {cfg['age'][0]}+",
                 campaign_id=state["campaign"], status="PAUSED", daily_budget=cfg["budget"],
                 optimization_goal="LEAD_GENERATION", billing_event="IMPRESSIONS", bid_strategy="LOWEST_COST_WITHOUT_CAP",
                 destination_type="ON_AD", promoted_object={"page_id": PAGE}, targeting=targeting)
        state[f"adset_{m}"] = r["id"]; state[f"interests_{m}"] = ints; save(); print("adset", m, r["id"], [i["name"] for i in ints])

    form_id = state[f"form_{m}"]; c = cfg["copy"]
    # 4a. anuncio de imagen, una pieza por ubicación
    if f"ad_img_{m}" not in state:
        afs = {
            "images": [{"hash": state[f"img_{m}_1x1"], "adlabels": [{"name": "sq"}]},
                       {"hash": state[f"img_{m}_4x5"], "adlabels": [{"name": "feed"}]},
                       {"hash": state[f"img_{m}_9x16"], "adlabels": [{"name": "story"}]}],
            "bodies": [{"text": c["body_feed"], "adlabels": [{"name": "bfeed"}]}, {"text": c["body_story"], "adlabels": [{"name": "bstory"}]}],
            "titles": [{"text": c["titles"][0]}],   # con reglas por ubicación Meta exige una sola pieza de cada tipo
            "descriptions": [{"text": c["desc"]}],
            "link_urls": [{"website_url": "http://fb.me/"}],
            "call_to_action_types": ["GET_QUOTE"],
            "call_to_actions": [{"type": "GET_QUOTE", "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"}}],
            "ad_formats": ["SINGLE_IMAGE"],
            "optimization_type": "PLACEMENT",
            "asset_customization_rules": [
                {"priority": 1, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["story", "facebook_reels"], "instagram_positions": ["story", "reels"]},
                 "image_label": {"name": "story"}, "body_label": {"name": "bstory"}},
                {"priority": 2, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["feed", "profile_feed"], "instagram_positions": ["stream", "explore", "explore_home", "profile_feed"]},
                 "image_label": {"name": "feed"}, "body_label": {"name": "bfeed"}},
                {"priority": 3, "customization_spec": {"publisher_platforms": ["facebook", "instagram", "audience_network", "messenger"]},
                 "image_label": {"name": "sq"}, "body_label": {"name": "bfeed"}},
            ],
        }
        cr = call("POST", f"{A}/adcreatives", name=f"{m} · IA · imagen por ubicación · 2026-09",
                  object_story_spec={"page_id": PAGE, "instagram_user_id": IG},
                  asset_feed_spec=afs,
                  degrees_of_freedom_spec={"creative_features_spec": {"advantage_plus_creative": {"enroll_status": "OPT_IN"}}})
        ad = call("POST", f"{A}/ads", name=f"{m} | IA | Gráfica feed + story | 2026-09", adset_id=state[f"adset_{m}"], creative={"creative_id": cr["id"]}, status="PAUSED")
        state[f"ad_img_{m}"] = ad["id"]; save(); print("ad img", m, ad["id"])
    # 4b. reel
    if f"ad_video_{m}" not in state:
        cr = call("POST", f"{A}/adcreatives", name=f"{m} · IA · reel · 2026-09",
                  object_story_spec={"page_id": PAGE, "instagram_user_id": IG, "video_data": {
                      "video_id": state[f"video_{m}"], "image_hash": state[f"img_{m}_9x16"],
                      "title": c["video_title"], "message": c["body_feed"], "link_description": c["desc"],
                      "call_to_action": {"type": "GET_QUOTE", "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"}}}},
                  degrees_of_freedom_spec={"creative_features_spec": {"advantage_plus_creative": {"enroll_status": "OPT_IN"}}})
        ad = call("POST", f"{A}/ads", name=f"{m} | IA | Reel | 2026-09", adset_id=state[f"adset_{m}"], creative={"creative_id": cr["id"]}, status="PAUSED")
        state[f"ad_video_{m}"] = ad["id"]; save(); print("ad video", m, ad["id"])

print(json.dumps(state, indent=1, ensure_ascii=False))
