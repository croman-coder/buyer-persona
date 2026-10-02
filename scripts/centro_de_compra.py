#!/usr/bin/env python3
"""Centro de compra con los datos que ya tenemos (idea de Valentina, 2026-09-24).

El Buyer Persona describe a un solo actor. En la compra de un auto hay más:
quien investiga e influye, quien decide, quien firma. Sin preguntar nada nuevo,
Meta ya separa dos momentos por género y edad:

1. **Quién mira y quién da el paso.** Por marca, qué tasa de clic → contacto
   tiene cada género y cada edad. Contacto = formulario enviado o chat de
   WhatsApp/Messenger iniciado. La tasa no depende de a quién le mostró Meta el
   anuncio. Un grupo que hace muchos clics y pocos contactos está mirando,
   comparando o influyendo; el que convierte más es el que da el paso.
2. **Qué le interesa a cada uno.** Cada anuncio se clasifica por ángulo con las
   mismas reglas de las fichas (``ad_copy_analyzer.RULES``). Dentro del mismo
   modelo, se mide qué parte de los clics de cada ángulo viene de mujeres y de
   mayores de 55, contra el promedio del modelo.

Se excluyen los conjuntos segmentados a un solo género, porque ahí el reparto lo
fija la segmentación y no el interés. Para la medición de 55+ se excluyen además
los que cortan la edad antes de los 55. Todo es agregado de Meta: no se lee
ningún dato personal.

Uso: python3 scripts/centro_de_compra.py <data_sources.json>
     (el JSON diario del pipeline, para anuncios y creativos; la segmentación y
     el embudo por conjunto se bajan del API y se guardan en output/raw/)
"""
import json
import os
import re
import sys
import time
from collections import defaultdict

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.generators.ad_copy_analyzer import INTEREST_LABELS, RULES  # noqa: E402
from src.generators.persona_generator import detect_models_in_ads  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))
TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"

CONTACTO = ("lead", "onsite_conversion.messaging_conversation_started_7d")
EDADES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
MARCAS_MIXTAS = {"JAC/Renault", "Multimarcas", "Santa Rosa", "Karry"}  # cuentas sin una sola marca
MIN_CONTACTOS_MARCA = 150
MIN_CONTACTOS_CONJUNTO = 30   # para comparar géneros dentro de un conjunto
MIN_CLICS_CELDA = 1000   # ángulo dentro de un modelo
MIN_ANUNCIOS_CELDA = 3
MAX_PESO_UN_ANUNCIO = 0.5  # si un anuncio pone más de la mitad de los clics, la celda habla de ese anuncio y no del ángulo


def get(path, params, intentos=6):
    params = {**params, "access_token": TOKEN}
    for i in range(intentos):
        try:
            r = requests.get(f"{API}/{path}" if not path.startswith("http") else path,
                             params=params if not path.startswith("http") else None, timeout=120).json()
        except requests.RequestException:
            time.sleep(20 * (i + 1))
            continue
        cod = r.get("error", {}).get("code")
        if cod in (4, 17, 80004, 613):   # límites de llamadas
            time.sleep(60 * (i + 1))
            continue
        return r
    return {"error": {"message": "sin respuesta tras reintentos"}}


def paginado(path, params):
    filas, r = [], get(path, params)
    while True:
        if "error" in r:
            print("   ERR", path, r["error"].get("message", "")[:120], flush=True)
            break
        filas += r.get("data", [])
        sig = r.get("paging", {}).get("next")
        if not sig:
            break
        r = get(sig, {})
    return filas


def bajar_api(desde, hasta):
    """Embudo por conjunto (edad × género), segmentación de cada conjunto y
    a qué conjunto pertenece cada anuncio."""
    cuentas = [p.split(":", 1) for p in os.environ["META_ADS_AD_ACCOUNT_IDS"].split(",") if p.strip()]
    rango = json.dumps({"since": desde, "until": hasta})
    filas, anuncio_conjunto, conjuntos = [], {}, set()
    for n, (act, marca) in enumerate(cuentas, 1):
        if marca in MARCAS_MIXTAS:
            continue
        ins = paginado(f"{act}/insights", {"level": "adset", "breakdowns": "age,gender", "time_range": rango,
                                           "fields": "adset_id,inline_link_clicks,actions", "limit": 500})
        for x in ins:
            x["account"] = marca
            conjuntos.add(x["adset_id"])
        filas += ins
        for x in paginado(f"{act}/insights", {"level": "ad", "time_range": rango, "fields": "ad_id,adset_id", "limit": 500}):
            anuncio_conjunto[x["ad_id"]] = x["adset_id"]
        print(f"   {n}/{len(cuentas)} {marca:10s} {act} · {len(ins)} filas", flush=True)
    segm, ids = {}, sorted(conjuntos)
    for i in range(0, len(ids), 50):
        r = get("", {"ids": ",".join(ids[i:i + 50]), "fields": "targeting{genders,age_min,age_max}"})
        for k, v in r.items():
            if isinstance(v, dict) and "targeting" in v:
                t = v["targeting"]
                segm[k] = {"genders": t.get("genders"), "age_min": t.get("age_min"), "age_max": t.get("age_max")}
    return {"periodo": {"desde": desde, "hasta": hasta}, "filas": filas,
            "segmentacion": segm, "anuncio_conjunto": anuncio_conjunto}


def un_genero(seg):
    return bool(seg and seg.get("genders") and len(seg["genders"]) == 1)


def corta_antes_de_55(seg):
    return bool(seg and seg.get("age_max") and int(seg["age_max"]) < 55)


def accion(row, tipo):
    return sum(float(a["value"]) for a in row.get("actions") or [] if a["action_type"] == tipo)


def embudo(api):
    segm = api["segmentacion"]
    out = defaultdict(lambda: {"genero": defaultdict(lambda: [0.0, 0.0]),
                               "edad": defaultdict(lambda: [0.0, 0.0]), "excluidos": 0.0, "total": 0.0})
    for r in api["filas"]:
        clics = float(r.get("inline_link_clicks") or 0)
        contactos = sum(accion(r, t) for t in CONTACTO)
        m = out[r["account"]]
        m["total"] += clics
        if un_genero(segm.get(r["adset_id"])):
            m["excluidos"] += clics
            continue
        if r.get("gender") in ("male", "female"):
            g = m["genero"][r["gender"]]
            g[0] += clics
            g[1] += contactos
        if r.get("age") in EDADES:
            e = m["edad"][r["age"]]
            e[0] += clics
            e[1] += contactos
    # Comparación dentro de cada conjunto: mismo anuncio y mismo botón para los
    # dos géneros, así una campaña sin formulario ni chat no ensucia la tasa.
    por_conjunto = defaultdict(lambda: {"female": [0.0, 0.0], "male": [0.0, 0.0]})
    for r in api["filas"]:
        if r.get("gender") not in ("male", "female") or un_genero(segm.get(r["adset_id"])):
            continue
        x = por_conjunto[(r["account"], r["adset_id"])][r["gender"]]
        x[0] += float(r.get("inline_link_clicks") or 0)
        x[1] += sum(accion(r, t) for t in CONTACTO)
    mh = defaultdict(lambda: [0.0, 0.0, 0, 0])   # marca -> [num, den, conjuntos, conjuntos donde ellas convierten menos]
    for (marca, _), g in por_conjunto.items():
        (n1, a), (n0, b) = g["female"], g["male"]
        if a + b < MIN_CONTACTOS_CONJUNTO or not n1 or not n0:
            continue
        n = n1 + n0
        m = mh[marca]
        m[0] += a * n0 / n
        m[1] += b * n1 / n
        m[2] += 1
        m[3] += 1 if a / n1 < b / n0 else 0
    res = []
    for marca, m in out.items():
        g = m["genero"]
        clics = sum(v[0] for v in g.values())
        contactos = sum(v[1] for v in g.values())
        if contactos < MIN_CONTACTOS_MARCA or not clics:
            continue
        tasa = {k: (v[1] / v[0] * 100 if v[0] else 0.0) for k, v in g.items()}
        edades = {k: {"clics": int(m["edad"][k][0]), "contactos": int(m["edad"][k][1]),
                      "tasa_pct": round(m["edad"][k][1] / m["edad"][k][0] * 100, 1) if m["edad"][k][0] else None}
                  for k in EDADES if k in m["edad"]}
        res.append({
            "marca": marca, "clics": int(clics), "contactos": int(contactos),
            "clics_excluidos_pct": round(m["excluidos"] / m["total"] * 100, 1) if m["total"] else 0,
            "mujeres_clics_pct": round(g["female"][0] / clics * 100, 1),
            "mujeres_contactos_pct": round(g["female"][1] / contactos * 100, 1),
            "tasa_mujeres_pct": round(tasa.get("female", 0), 1),
            "tasa_hombres_pct": round(tasa.get("male", 0), 1),
            "tasa_total_pct": round(contactos / clics * 100, 1),
            "edades": edades,
            "mujeres_vs_hombres_mismo_conjunto": round(mh[marca][0] / mh[marca][1], 2) if mh[marca][1] else None,
            "conjuntos_comparados": mh[marca][2],
            "conjuntos_ellas_convierten_menos": mh[marca][3],
        })
    return sorted(res, key=lambda x: -x["contactos"])


def angulos_de(ad):
    texto = f"{ad.get('title') or ''} {ad.get('body') or ''} {ad.get('ad_name') or ''}".lower()
    return [INTEREST_LABELS[i] for i, regla in enumerate(RULES)
            if any(re.search(k, texto) for k in regla["keywords"])]


def intereses(rows_ad, creativos, api):
    """Por marca → modelo → ángulo: % de clics de mujeres y de 55+, contra el
    promedio del mismo modelo."""
    segm, a2s = api["segmentacion"], api["anuncio_conjunto"]
    por_id = {str(c["ad_id"]): c for c in creativos if c.get("ad_id")}
    cache = {}
    # [clics sin sesgo de género, de mujeres, clics sin corte de edad, de 55+]
    base = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    celda = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    clics_por_anuncio = defaultdict(lambda: defaultdict(float))   # celda -> anuncio -> clics
    for r in rows_ad:
        c = float(r.get("clicks") or 0)
        marca = r["account"]
        if not c or marca in MARCAS_MIXTAS:
            continue
        ad_id = str(r.get("ad_id"))
        seg = segm.get(a2s.get(ad_id, ""))
        if ad_id not in cache:
            ad = por_id.get(ad_id) or {"ad_name": r.get("ad_name", "")}
            cache[ad_id] = (list(detect_models_in_ads([ad], marca).keys()), angulos_de(ad))
        modelos, angs = cache[ad_id]
        v = [0.0, 0.0, 0.0, 0.0]
        if not un_genero(seg):
            v[0], v[1] = c, (c if r.get("gender") == "female" else 0.0)
        if not corta_antes_de_55(seg):
            v[2], v[3] = c, (c if r.get("age") in ("55-64", "65+") else 0.0)
        for mo in modelos:
            for i in range(4):
                base[(marca, mo)][i] += v[i]
            for a in angs:
                for i in range(4):
                    celda[(marca, mo, a)][i] += v[i]
                clics_por_anuncio[(marca, mo, a)][ad_id] += c
    out = defaultdict(list)
    for (marca, mo, a), (cg, mu, ce, ma) in celda.items():
        b = base[(marca, mo)]
        if cg < MIN_CLICS_CELDA or not b[0] or not b[2]:
            continue
        anuncios = clics_por_anuncio[(marca, mo, a)]
        peso_max = max(anuncios.values()) / sum(anuncios.values())
        if len(anuncios) < MIN_ANUNCIOS_CELDA or peso_max > MAX_PESO_UN_ANUNCIO:
            continue
        out[marca].append({
            "modelo": mo, "angulo": a, "clics": int(cg), "anuncios": len(anuncios), "peso_mayor_anuncio": round(peso_max, 2),
            "mujeres_pct": round(mu / cg * 100, 1), "mujeres_modelo_pct": round(b[1] / b[0] * 100, 1),
            "dif_mujeres_pp": round(mu / cg * 100 - b[1] / b[0] * 100, 1),
            "mayores55_pct": round(ma / ce * 100, 1) if ce else None,
            "dif_55_pp": round(ma / ce * 100 - b[3] / b[2] * 100, 1) if ce else None,
        })
    return dict(out)


def main():
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    meta = d["meta_ads"]
    desde, hasta = meta["date_range"]["start"], meta["date_range"]["end"]
    cache = os.path.join(ROOT, "output", "raw", f"centro_de_compra_api_{hasta}.json")
    if os.path.exists(cache):
        api = json.load(open(cache, encoding="utf-8"))
    else:
        print("Bajando embudo y segmentación de Meta…", flush=True)
        api = bajar_api(desde, hasta)
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(api, fh, ensure_ascii=False)
    print(f"\nMeta {desde} → {hasta} · {len(api['segmentacion'])} conjuntos con segmentación · "
          f"{sum(1 for s in api['segmentacion'].values() if un_genero(s))} a un solo género (excluidos)\n")

    emb = embudo(api)
    print("1) QUIÉN MIRA Y QUIÉN DA EL PASO (tasa clic → formulario o chat)")
    for x in emb:
        eds = {k: v["tasa_pct"] for k, v in x["edades"].items() if v["tasa_pct"] is not None and v["clics"] >= 500}
        print(f"  {x['marca']:10s} contactos {x['contactos']:6d} · mujeres {x['mujeres_clics_pct']:4.1f}% de clics → "
              f"{x['mujeres_contactos_pct']:4.1f}% de contactos · tasa mujeres {x['tasa_mujeres_pct']:4.1f}% vs hombres "
              f"{x['tasa_hombres_pct']:4.1f}% · excluido {x['clics_excluidos_pct']}%")
        print(f"             mismo conjunto: ellas convierten {x['mujeres_vs_hombres_mismo_conjunto']}× lo que ellos · "
              f"menos en {x['conjuntos_ellas_convierten_menos']} de {x['conjuntos_comparados']} conjuntos")
        print("             tasa por edad: " + " · ".join(f"{k} {v}%" for k, v in eds.items()))

    inte = intereses(meta["demographics"]["age_gender_ad"], meta["ad_creatives"], api)
    print("\n2) DENTRO DEL MISMO MODELO: ÁNGULOS QUE ATRAEN MÁS O MENOS MUJERES (±4 pp) Y 55+ (±6 pp)")
    for marca in [x["marca"] for x in emb]:
        filas = [f for f in inte.get(marca, []) if abs(f["dif_mujeres_pp"]) >= 4 or abs(f["dif_55_pp"] or 0) >= 6]
        if not filas:
            continue
        print(f"\n  {marca}")
        for f in sorted(filas, key=lambda f: (f["modelo"], -f["dif_mujeres_pp"])):
            print(f"    {f['modelo']:22s} {f['angulo']:40s} {f['clics']:6d} clics/{f['anuncios']:2d} anuncios · mujeres {f['mujeres_pct']:5.1f}% "
                  f"(modelo {f['mujeres_modelo_pct']}%, {f['dif_mujeres_pp']:+.1f}) · 55+ {f['mayores55_pct']}% ({f['dif_55_pp']:+.1f})")

    salida = os.path.join(ROOT, "output", f"centro_de_compra_{hasta}.json")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump({"periodo": {"desde": desde, "hasta": hasta}, "embudo": emb, "intereses": inte},
                  fh, ensure_ascii=False, indent=1)
    print("\nguardado en", os.path.relpath(salida, ROOT))


if __name__ == "__main__":
    main()
