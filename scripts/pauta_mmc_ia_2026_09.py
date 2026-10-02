#!/usr/bin/env python3
"""
Pauta Mitsubishi · IA Buyer Persona · L200 + Montero Sport · septiembre 2026.
Pedido de Cecilia Meyer (Brand Manager MMC) el 21-09-2026 con las piezas del
plan de la agencia (Ferrán Blau). Crea en PAUSA: 2 formularios con filtro,
campaña OUTCOME_LEADS (ABO), 2 conjuntos con lookalike + retargeting +
intereses (excluyendo a quien ya envió formulario) y por conjunto 2 gráficas
por ubicación (pieza principal y pieza de remarketing).
Presupuesto: USD 600 en 30 días → L200 USD 12/día, Montero USD 8/día
(sugerido del motor 1.519 / 527, corregido por los 89 Montero en stock).
"""
import json, os, sys
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
T = os.environ["META_ADS_ACCESS_TOKEN"]
V = "https://graph.facebook.com/v21.0"
A = "act_506680188632635"
PAGE = "103344941701936"
IG = "17841445317172019"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/claude-1000/-home-croman-Escritorio-BUYER-PERSONA/39847bea-44b3-4d28-b80d-9777dcae56b1/scratchpad/mmc/out")
OUT = ROOT / "output" / "pauta_mmc_ia_2026-09.json"
WEB = "https://www.mitsubishi-motors.com.py/"


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


def interest_ids(names):
    out = []
    for n in names:
        r = get("search", type="adinterest", q=n, limit=3, locale="es_LA").get("data", [])
        if r:
            out.append({"id": r[0]["id"], "name": r[0]["name"]})
    return out

# Audiencias comunes de la cuenta (armadas por la agencia): calientes de marca
COMMON_INCLUDE = [
    "120249166997270663",  # Público similar (1%) - RMK IG General (365)
    "120249167148430663",  # Público similar (1%) - RMK FB General (365)
    "120251504491800663",  # Público similar (5%) - RMK WEB Contact (180)
    "120249166591740663",  # RMK IG | Interactuaron (365)
    "120251504490700663",  # RMK WEB | Contact (180)
    "120249164562470663",  # RMK WEB | Page View (180)
]

MODELOS = {
    "L200": {
        "budget": 1200, "age_min": 25,
        "include": COMMON_INCLUDE + ["120252450739670663", "120252450671720663", "120252450668550663"],  # LAL 5% enviado L200 · LAL 5% abrió L200 · RMK form L200 abrió y no envió
        "exclude": ["120252450736180663"],  # LEAD FORM | L200 | Enviado 90 días
        "interests": ["Camionetas pickup", "Vehículo todoterreno", "Agricultura", "Construcción", "Ganadería"],
        "form": {
            "name": "SRPY - L200 - IA Buyer Persona - 2026-09",
            "headline": "Mitsubishi L200 4x4: cotizá tu versión, entrega inmediata",
            "context": {"title": "L200 4x4 · 2.4 Turbo Diésel · entrega inmediata",
                        "content": ["Desde USD 48.990 o cuotas desde USD 465*", "Hecha para tierra, barro y caminos difíciles", "Con el respaldo de Santa Rosa", "*Sujeto a entrega inicial"],
                        "button_text": "Quiero mi cotización"},
            "questions": [
                {"type": "CUSTOM", "key": "uso", "label": "¿Para qué la vas a usar?", "options": [{"value": "Trabajo / campo", "key": "trabajo"}, {"value": "Empresa / flota", "key": "flota"}, {"value": "Uso personal y familia", "key": "personal"}]},
                {"type": "CUSTOM", "key": "cuando", "label": "¿Cuándo pensás comprar?", "options": [{"value": "Este mes", "key": "este_mes"}, {"value": "En los próximos 3 meses", "key": "3_meses"}, {"value": "Solo estoy cotizando", "key": "cotizando"}]},
                {"type": "CUSTOM", "key": "pago", "label": "¿Cómo pensás pagarla?", "options": [{"value": "Financiación", "key": "financiacion"}, {"value": "Contado", "key": "contado"}, {"value": "Entrego mi usado + financiación", "key": "usado"}]},
                {"type": "FULL_NAME", "key": "full_name"}, {"type": "PHONE", "key": "phone_number"}, {"type": "EMAIL", "key": "email"}, {"type": "CITY", "key": "city"},
            ],
        },
        "ads": {
            "principal": {"img": "L200", "body": "Hay trabajos que necesitan más.\nConocé la Mitsubishi L200 4x4, preparada para acompañarte todos los días y con entrega inmediata.\n\n✔ Desde USD 48.990 o cuotas desde USD 465*\n✔ 2.4 Turbo Diésel, hecha para tierra, barro y caminos difíciles\n✔ Con el respaldo de Santa Rosa\n\nDejá tus datos y un asesor te cotiza la versión que necesitás.\n*Sujeto a entrega inicial.",
                          "story": "L200 4x4 · desde USD 48.990 · cuotas desde USD 465* · Entrega inmediata. Cotizá la tuya 👇\n*Sujeto a entrega inicial.",
                          "title": "L200 4x4 · cuotas desde USD 465", "desc": "Entrega inmediata. Cotizá en 1 minuto."},
            "rmk": {"img": "L200_rmk", "body": "Potencia para seguir cuando el camino se complica.\nL200 2.4 Turbo Diésel, hecha para tierra, barro y caminos difíciles.\n\n✔ Desde USD 48.990 o cuotas desde USD 465*\n✔ Entrega inmediata\n\nConsultá por las versiones disponibles de L200 4x4.\n*Sujeto a entrega inicial.",
                    "story": "L200 2.4 Turbo Diésel · desde USD 48.990* · Entrega inmediata. Consultá versiones 👇\n*Sujeto a entrega inicial.",
                    "title": "L200 2.4 Turbo Diésel · entrega inmediata", "desc": "Consultá las versiones disponibles."},
        },
    },
    "Montero": {
        "budget": 800, "age_min": 25,
        "include": COMMON_INCLUDE + ["120252450767650663", "120252450680620663", "120252450678590663"],  # LAL 5% enviado Montero · LAL 5% abrió Montero · RMK form Montero abrió y no envió
        "exclude": ["120252450766270663"],  # LEAD FORM | Montero | Enviado 90 días
        "interests": ["SUV", "Vehículo todoterreno", "Viajes", "Familia", "Camping"],
        "form": {
            "name": "SRPY - MONTERO - IA Buyer Persona - 2026-09",
            "headline": "Montero Sport 7 plazas: cotizá la tuya, entrega inmediata",
            "context": {"title": "Montero Sport · 2.4 Diésel · 7 plazas · entrega inmediata",
                        "content": ["Desde USD 47.500 o cuotas desde USD 445*", "Potencia, espacio y versatilidad para ciudad y ruta", "Con el respaldo de Santa Rosa", "*Sujeto a entrega inicial"],
                        "button_text": "Quiero mi cotización"},
            "questions": [
                {"type": "CUSTOM", "key": "cuando", "label": "¿Cuándo pensás cambiar tu vehículo?", "options": [{"value": "Este mes", "key": "este_mes"}, {"value": "En los próximos 3 meses", "key": "3_meses"}, {"value": "Solo estoy mirando", "key": "mirando"}]},
                {"type": "CUSTOM", "key": "pago", "label": "¿Cómo pensás comprarla?", "options": [{"value": "Financiación", "key": "financiacion"}, {"value": "Contado", "key": "contado"}, {"value": "Entrego mi usado + financiación", "key": "usado"}]},
                {"type": "CUSTOM", "key": "testdrive", "label": "¿Querés agendar un test drive?", "options": [{"value": "Sí, esta semana", "key": "si_semana"}, {"value": "Sí, más adelante", "key": "si_luego"}, {"value": "Solo información", "key": "info"}]},
                {"type": "FULL_NAME", "key": "full_name"}, {"type": "PHONE", "key": "phone_number"}, {"type": "EMAIL", "key": "email"}, {"type": "CITY", "key": "city"},
            ],
        },
        "ads": {
            "principal": {"img": "Montero", "body": "Ciudad, ruta o ese plan que aparece de repente.\nLa Montero Sport combina potencia, espacio y versatilidad para acompañarte mucho más allá de lo cotidiano. ¡Con entrega inmediata!\n\n✔ Desde USD 47.500 o cuotas desde USD 445*\n✔ 2.4 Diésel, 178 HP, 7 plazas\n✔ Con el respaldo de Santa Rosa\n\nDejá tus datos y agendá tu test drive.\n*Sujeto a entrega inicial.",
                          "story": "Montero Sport 7 plazas · desde USD 47.500 · cuotas desde USD 445* · Entrega inmediata. Agendá tu test drive 👇\n*Sujeto a entrega inicial.",
                          "title": "Montero Sport · cuotas desde USD 445", "desc": "7 plazas. Entrega inmediata. Agendá tu test drive."},
            "rmk": {"img": "Montero_rmk", "body": "No todos los caminos piden lo mismo.\nPara los que exigen un poco más, está la Montero Sport: cámara 360, todo lo que pasa alrededor, a la vista.\n\n✔ Desde USD 47.500 o cuotas desde USD 445*\n✔ Entrega inmediata\n\nAgendá tu test drive.\n*Sujeto a entrega inicial.",
                    "story": "Montero Sport · cámara 360 · desde USD 47.500* · Entrega inmediata. Agendá tu test drive 👇\n*Sujeto a entrega inicial.",
                    "title": "Montero Sport · agendá tu test drive", "desc": "Cámara 360. Entrega inmediata."},
        },
    },
}

# 1. formularios
PT = get(PAGE, fields="access_token")["access_token"]
for m, cfg in MODELOS.items():
    key = f"form_{m}"
    if key in state:
        continue
    f = cfg["form"]
    r = requests.post(f"{V}/{PAGE}/leadgen_forms", data={
        "access_token": PT, "name": f["name"], "locale": "es_LA",
        "privacy_policy": json.dumps({"url": WEB, "link_text": "Política de privacidad"}),
        "follow_up_action_url": WEB,
        "question_page_custom_headline": f["headline"],
        "context_card": json.dumps({"title": f["context"]["title"], "style": "LIST_STYLE", "content": f["context"]["content"], "button_text": f["context"]["button_text"]}),
        "questions": json.dumps(f["questions"]),
        "thank_you_page": json.dumps({"title": "¡Gracias! Un asesor de Mitsubishi te contacta hoy.", "body": "Mientras tanto podés conocer toda la gama en nuestro sitio.", "button_type": "VIEW_WEBSITE", "button_text": "Descubrí todos nuestros modelos", "website_url": WEB}),
        "is_optimized_for_quality": "true", "block_display_for_non_targeted_viewer": "false",
    }, timeout=60).json()
    if "error" in r:
        raise RuntimeError(f"form {m}: {r['error']}")
    state[key] = r["id"]; save(); print("form", m, r["id"])

# 2. imágenes
for m, cfg in MODELOS.items():
    for ad_key, ad in cfg["ads"].items():
        for ratio in ("1x1", "4x5", "9x16"):
            key = f"img_{ad['img']}_{ratio}"
            if key in state:
                continue
            p = SRC / f"{ad['img']}_{ratio}.png"
            r = requests.post(f"{V}/{A}/adimages", data={"access_token": T}, files={"filename": (p.name, p.read_bytes(), "image/png")}, timeout=120).json()
            if "error" in r:
                raise RuntimeError(f"img {p.name}: {r['error']}")
            state[key] = list(r["images"].values())[0]["hash"]; save(); print("img", key)

# 3. campaña
if "campaign" not in state:
    r = call("POST", f"{A}/campaigns", name="MITSUBISHI | IA Buyer Persona | Leads | L200 + Montero | 2026-09",
             objective="OUTCOME_LEADS", status="PAUSED", buying_type="AUCTION", special_ad_categories=[], is_adset_budget_sharing_enabled="false")
    state["campaign"] = r["id"]; save(); print("campaign", r["id"])

# 4. conjuntos + anuncios
for m, cfg in MODELOS.items():
    if f"adset_{m}" not in state:
        ints = interest_ids(cfg["interests"])
        targeting = {
            "geo_locations": {"countries": ["PY"], "location_types": ["home", "recent"]},
            "age_min": cfg["age_min"], "age_max": 65,
            "custom_audiences": [{"id": i} for i in cfg["include"]],
            "excluded_custom_audiences": [{"id": i} for i in cfg["exclude"]],
            "flexible_spec": [{"interests": ints}] if ints else [],
            "targeting_automation": {"advantage_audience": 1, "individual_setting": {"age": 1}},
        }
        r = call("POST", f"{A}/adsets", name=f"{m} | IA | Lookalike + Retargeting + Intereses | PY {cfg['age_min']}+",
                 campaign_id=state["campaign"], status="PAUSED", daily_budget=cfg["budget"],
                 optimization_goal="LEAD_GENERATION", billing_event="IMPRESSIONS", bid_strategy="LOWEST_COST_WITHOUT_CAP",
                 destination_type="ON_AD", promoted_object={"page_id": PAGE}, targeting=targeting)
        state[f"adset_{m}"] = r["id"]; state[f"interests_{m}"] = ints; save(); print("adset", m, r["id"], [i["name"] for i in ints])
    form_id = state[f"form_{m}"]
    for ad_key, ad in cfg["ads"].items():
        skey = f"ad_{m}_{ad_key}"
        if skey in state:
            continue
        img = ad["img"]
        afs = {
            "images": [{"hash": state[f"img_{img}_1x1"], "adlabels": [{"name": "sq"}]},
                       {"hash": state[f"img_{img}_4x5"], "adlabels": [{"name": "feed"}]},
                       {"hash": state[f"img_{img}_9x16"], "adlabels": [{"name": "story"}]}],
            "bodies": [{"text": ad["body"], "adlabels": [{"name": "bfeed"}]}, {"text": ad["story"], "adlabels": [{"name": "bstory"}]}],
            "titles": [{"text": ad["title"]}], "descriptions": [{"text": ad["desc"]}],
            "link_urls": [{"website_url": "http://fb.me/"}],
            "call_to_action_types": ["GET_QUOTE"],
            "call_to_actions": [{"type": "GET_QUOTE", "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"}}],
            "ad_formats": ["SINGLE_IMAGE"], "optimization_type": "PLACEMENT",
            "asset_customization_rules": [
                {"priority": 1, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["story", "facebook_reels"], "instagram_positions": ["story", "reels"]}, "image_label": {"name": "story"}, "body_label": {"name": "bstory"}},
                {"priority": 2, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["feed", "profile_feed"], "instagram_positions": ["stream", "explore", "explore_home", "profile_feed"]}, "image_label": {"name": "feed"}, "body_label": {"name": "bfeed"}},
                {"priority": 3, "customization_spec": {"publisher_platforms": ["facebook", "instagram", "audience_network", "messenger"]}, "image_label": {"name": "sq"}, "body_label": {"name": "bfeed"}},
            ],
        }
        cr = call("POST", f"{A}/adcreatives", name=f"{m} · IA · {ad_key} · 2026-09",
                  object_story_spec={"page_id": PAGE, "instagram_user_id": IG}, asset_feed_spec=afs,
                  degrees_of_freedom_spec={"creative_features_spec": {"advantage_plus_creative": {"enroll_status": "OPT_IN"}}})
        r = call("POST", f"{A}/ads", name=f"{m} | IA | {'Gráfica principal' if ad_key == 'principal' else 'Gráfica remarketing'} | 2026-09",
                 adset_id=state[f"adset_{m}"], creative={"creative_id": cr["id"]}, status="PAUSED")
        state[skey] = r["id"]; save(); print("ad", skey, r["id"])

print(json.dumps(state, indent=1, ensure_ascii=False))
