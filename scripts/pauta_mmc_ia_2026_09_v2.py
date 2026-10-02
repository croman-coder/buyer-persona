#!/usr/bin/env python3
"""
Pauta Mitsubishi IA 2026-09 · v2: reemplaza las piezas provisorias (mockups
del PDF) por los materiales reales del Drive de Cecilia (21-09-2026):
estáticos nativos 1:1 / 4:5 / 9:16, motion 7 s en los tres formatos y
piezas de remarketing. Pausa los anuncios v1 (no los borra) y crea por
conjunto: gráfica, motion y remarketing. Campaña y conjuntos se mantienen.
"""
import json, os, sys, time
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
T = os.environ["META_ADS_ACCESS_TOKEN"]
V = "https://graph.facebook.com/v21.0"
A = "act_506680188632635"; PAGE = "103344941701936"; IG = "17841445317172019"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/fuentes/creatividades/mmc_2026-09/PAUTA"
OUT = ROOT / "output" / "pauta_mmc_ia_2026-09.json"
state = json.loads(OUT.read_text())
def save(): OUT.write_text(json.dumps(state, indent=1, ensure_ascii=False))

def call(method, path, **data):
    r = requests.request(method, f"{V}/{path}", data={"access_token": T, **{k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in data.items()}}, timeout=120).json()
    if "error" in r: raise RuntimeError(f"{path}: {json.dumps(r['error'], ensure_ascii=False)}")
    return r
def get(path, **q): return requests.get(f"{V}/{path}", params={"access_token": T, **q}, timeout=60).json()

def _dir(prefix):
    return next(d for d in SRC.iterdir() if d.is_dir() and d.name.upper().startswith(prefix))
E, M, R = _dir("EST"), _dir("MOTION"), _dir("REMARKETING")
def _f(d, sub, needle):
    """archivo dentro de d/sub cuyo nombre contiene needle (tolerante a acentos/mayúsculas)"""
    import unicodedata
    n = lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().upper()
    folder = next(x for x in d.iterdir() if n(x.name) == n(sub))
    return next(x for x in folder.iterdir() if n(needle) in n(x.name))
FILES = {
    "L200": {
        "static": {"1x1": _f(E,"1.1","L200"), "4x5": _f(E,"4.5","L200"), "9x16": _f(E,"9.16","L200")},
        "rmk": {"1x1": _f(R,"1.1","L200"), "4x5": _f(R,"4.5","L200"), "9x16": _f(R,"9.16","L200")},
        "motion": {"1x1": _f(M,"1.1","L200"), "4x5": _f(M,"4.5","L200"), "9x16": _f(M,"9.16","L200")},
    },
    "Montero": {
        "static": {"1x1": _f(E,"1.1","MONTERO"), "4x5": _f(E,"4.5","MONTERO"), "9x16": _f(E,"9.16","MONTERO")},
        "rmk": {"1x1": _f(R,"1.1","MONTERO"), "4x5": _f(R,"4.5","MONTERO"), "9x16": _f(R,"9.16","MONTERO")},
        "motion": {"1x1": _f(M,"1.1","MONTERO"), "4x5": _f(M,"4.5","MONTERO"), "9x16": _f(M,"9.16","MONTERO")},
    },
}
COPY = {
    "L200": {
        "static": {"body": "Hay trabajos que necesitan más.\nConocé la Mitsubishi L200 4x4, preparada para acompañarte todos los días y con entrega inmediata.\n\n✔ Desde USD 48.990 o cuotas desde USD 465*\n✔ 2.4 Turbo Diésel, hecha para tierra, barro y caminos difíciles\n✔ Con el respaldo de Santa Rosa\n\nDejá tus datos y un asesor te cotiza la versión que necesitás.\n*Sujeto a entrega inicial.",
                   "story": "L200 4x4 · desde USD 48.990 · cuotas desde USD 465* · Entrega inmediata. Cotizá la tuya 👇\n*Sujeto a entrega inicial.", "title": "L200 4x4 · cuotas desde USD 465", "desc": "Entrega inmediata. Cotizá en 1 minuto."},
        "motion": {"body": "Más capacidad para el trabajo de todos los días.\nConocé la Mitsubishi L200 4x4 y consultá las opciones disponibles.\n\n✔ Desde USD 48.990 o cuotas desde USD 465*\n✔ Entrega inmediata, con el respaldo de Santa Rosa\n\nCotizá la tuya hoy.\n*Sujeto a entrega inicial.",
                   "story": "L200 4x4 · más capacidad para el trabajo de todos los días · Entrega inmediata. Cotizá la tuya hoy 👇", "title": "L200 4x4 · cotizá la tuya hoy", "desc": "Cuotas desde USD 465. Entrega inmediata."},
        "rmk": {"body": "Potencia para seguir cuando el camino se complica.\nL200 2.4 Turbo Diésel, hecha para tierra, barro y caminos difíciles.\n\n✔ Desde USD 48.990 o cuotas desde USD 465*\n✔ Entrega inmediata\n\nConsultá por las versiones disponibles de L200 4x4.\n*Sujeto a entrega inicial.",
                "story": "L200 2.4 Turbo Diésel · desde USD 48.990* · Entrega inmediata. Consultá versiones 👇\n*Sujeto a entrega inicial.", "title": "L200 2.4 Turbo Diésel · entrega inmediata", "desc": "Consultá las versiones disponibles."},
    },
    "Montero": {
        "static": {"body": "Ciudad, ruta o ese plan que aparece de repente.\nLa Montero Sport combina potencia, espacio y versatilidad para acompañarte mucho más allá de lo cotidiano. ¡Con entrega inmediata!\n\n✔ Desde USD 47.500 o cuotas desde USD 445*\n✔ 2.4 Diésel, 178 HP, 7 plazas\n✔ Con el respaldo de Santa Rosa\n\nDejá tus datos y agendá tu test drive.\n*Sujeto a entrega inicial.",
                   "story": "Montero Sport 7 plazas · desde USD 47.500 · cuotas desde USD 445* · Entrega inmediata. Agendá tu test drive 👇\n*Sujeto a entrega inicial.", "title": "Montero Sport · cuotas desde USD 445", "desc": "7 plazas. Entrega inmediata. Agendá tu test drive."},
        "motion": {"body": "No todos los caminos piden lo mismo.\nPara los que exigen un poco más, está la Montero Sport.\n\n✔ Desde USD 47.500 o cuotas desde USD 445*\n✔ 2.4 Diésel, 7 plazas, entrega inmediata\n\nAgendá tu test drive.\n*Sujeto a entrega inicial.",
                   "story": "Montero Sport · para los que exigen un poco más · Entrega inmediata. Agendá tu test drive 👇", "title": "Montero Sport · agendá tu test drive", "desc": "Cuotas desde USD 445. Entrega inmediata."},
        "rmk": {"body": "Más control para moverte con confianza en cada maniobra.\nMontero Sport con cámara 360: todo lo que pasa alrededor, a la vista.\n\n✔ Desde USD 47.500 o cuotas desde USD 445*\n✔ Entrega inmediata\n\n¡Agendá tu test drive hoy!\n*Sujeto a entrega inicial.",
                "story": "Montero Sport · cámara 360 · desde USD 47.500* · Entrega inmediata. Agendá tu test drive 👇\n*Sujeto a entrega inicial.", "title": "Montero Sport · cámara 360", "desc": "Entrega inmediata. Agendá tu test drive hoy."},
    },
}

# 0. pausar v1
for k in ("ad_L200_principal", "ad_L200_rmk", "ad_Montero_principal", "ad_Montero_rmk"):
    if k in state and not state.get(k + "_paused"):
        call("POST", state[k], status="PAUSED"); state[k + "_paused"] = True; save(); print("pausado v1", k)

# 1. subir imágenes y videos
def upload_img(p):
    r = requests.post(f"{V}/{A}/adimages", data={"access_token": T}, files={"filename": (p.name, p.read_bytes(), "image/jpeg")}, timeout=120).json()
    if "error" in r: raise RuntimeError(f"img {p.name}: {r['error']}")
    return list(r["images"].values())[0]["hash"]
def upload_vid(p, name):
    r = requests.post(f"{V}/{A}/advideos", data={"access_token": T, "name": name}, files={"source": (p.name, p.read_bytes(), "video/mp4")}, timeout=600).json()
    if "error" in r: raise RuntimeError(f"video {p.name}: {r['error']}")
    return r["id"]
for m, groups in FILES.items():
    for kind, ratios in groups.items():
        for ratio, p in ratios.items():
            key = f"v2_{m}_{kind}_{ratio}"
            if key in state: continue
            state[key] = upload_vid(p, f"{m} motion {ratio} · IA 2026-09") if kind == "motion" else upload_img(p)
            save(); print("subido", key)
for m in FILES:
    for ratio in ("1x1", "4x5", "9x16"):
        vid = state[f"v2_{m}_motion_{ratio}"]
        for _ in range(60):
            if get(vid, fields="status").get("status", {}).get("video_status") == "ready": break
            time.sleep(5)
    print("videos listos", m)

RULES = [
    {"priority": 1, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["story", "facebook_reels"], "instagram_positions": ["story", "reels"]}, "LBL": "story"},
    {"priority": 2, "customization_spec": {"publisher_platforms": ["facebook", "instagram"], "facebook_positions": ["feed", "profile_feed"], "instagram_positions": ["stream", "explore", "explore_home", "profile_feed"]}, "LBL": "feed"},
    {"priority": 3, "customization_spec": {"publisher_platforms": ["facebook", "instagram", "audience_network", "messenger"]}, "LBL": "sq"},
]
def rules(media_key):
    out = []
    for r in RULES:
        lbl = r["LBL"]; rr = {"priority": r["priority"], "customization_spec": r["customization_spec"], media_key: {"name": lbl}, "body_label": {"name": "bstory" if lbl == "story" else "bfeed"}}
        out.append(rr)
    return out

# 2. anuncios v2
for m in FILES:
    form_id = state[f"form_{m}"]; adset = state[f"adset_{m}"]
    for kind, label in (("static", "Gráfica"), ("motion", "Motion"), ("rmk", "Remarketing")):
        key = f"v2_ad_{m}_{kind}"
        if key in state: continue
        c = COPY[m][kind]
        afs = {
            "bodies": [{"text": c["body"], "adlabels": [{"name": "bfeed"}]}, {"text": c["story"], "adlabels": [{"name": "bstory"}]}],
            "titles": [{"text": c["title"]}], "descriptions": [{"text": c["desc"]}],
            "link_urls": [{"website_url": "http://fb.me/"}],
            "call_to_action_types": ["GET_QUOTE"],
            "call_to_actions": [{"type": "GET_QUOTE", "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"}}],
            "optimization_type": "PLACEMENT",
        }
        if kind == "motion":
            afs["videos"] = [{"video_id": state[f"v2_{m}_motion_1x1"], "thumbnail_hash": state[f"v2_{m}_static_1x1"], "adlabels": [{"name": "sq"}]},
                             {"video_id": state[f"v2_{m}_motion_4x5"], "thumbnail_hash": state[f"v2_{m}_static_4x5"], "adlabels": [{"name": "feed"}]},
                             {"video_id": state[f"v2_{m}_motion_9x16"], "thumbnail_hash": state[f"v2_{m}_static_9x16"], "adlabels": [{"name": "story"}]}]
            afs["ad_formats"] = ["SINGLE_VIDEO"]; afs["asset_customization_rules"] = rules("video_label")
        else:
            afs["images"] = [{"hash": state[f"v2_{m}_{kind}_1x1"], "adlabels": [{"name": "sq"}]},
                             {"hash": state[f"v2_{m}_{kind}_4x5"], "adlabels": [{"name": "feed"}]},
                             {"hash": state[f"v2_{m}_{kind}_9x16"], "adlabels": [{"name": "story"}]}]
            afs["ad_formats"] = ["SINGLE_IMAGE"]; afs["asset_customization_rules"] = rules("image_label")
        cr = call("POST", f"{A}/adcreatives", name=f"{m} · IA · {label} v2 · 2026-09",
                  object_story_spec={"page_id": PAGE, "instagram_user_id": IG}, asset_feed_spec=afs,
                  degrees_of_freedom_spec={"creative_features_spec": {"advantage_plus_creative": {"enroll_status": "OPT_IN"}}})
        ad = call("POST", f"{A}/ads", name=f"{m} | IA | {label} | 2026-09 v2", adset_id=adset, creative={"creative_id": cr["id"]}, status="ACTIVE")
        state[key] = ad["id"]; save(); print("ad v2", key, ad["id"])
print(json.dumps({k: v for k, v in state.items() if k.startswith("v2_ad") or k.endswith("_paused")}, indent=1))
