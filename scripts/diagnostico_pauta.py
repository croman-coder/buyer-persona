#!/usr/bin/env python3
"""Diagnóstico de la pauta de todas las cuentas: dónde mejorar sin tocar el presupuesto.

Lee los últimos N días (por defecto 14) a nivel conjunto en todas las cuentas del
portfolio y responde, por marca:

- **Gasto sin resultado**: conjuntos con gasto relevante y costo por resultado
  del doble o más que la marca (o sin resultados). Esa plata se puede mover a
  los mejores conjuntos de la misma marca.
- **Fragmentación**: conjuntos que no llegan a 10 resultados por semana (Meta
  pide ~50 para salir de aprendizaje). Muchos conjuntos chicos = aprendizaje
  eterno y resultados más caros.
- **Cuentas que compiten entre sí**: cuántas cuentas de la misma marca pautan
  a la vez y cuánto cuesta el resultado en cada una.
- **Frecuencia**: conjuntos con frecuencia > 4 en la ventana (fatiga).

Resultado = formulario enviado o chat de WhatsApp/Messenger iniciado.
Solo agregados de Meta.

Uso: python3 scripts/diagnostico_pauta.py [días=14]
"""
import json
import os
import sys
import time
from collections import defaultdict

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"
RESULTADO = ("lead", "onsite_conversion.messaging_conversation_started_7d")
MIXTAS = {"JAC/Renault", "Multimarcas", "Santa Rosa", "Karry"}
# Objetivos que no optimizan formularios ni chats: se informan aparte (no son "caros", buscan otra cosa)
NO_CONTACTO = {"OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT", "BRAND_AWARENESS", "REACH", "LINK_CLICKS", "POST_ENGAGEMENT", "VIDEO_VIEWS"}


def get(url, params=None):
    for i in range(5):
        try:
            r = requests.get(url, params=params, timeout=120).json()
        except requests.RequestException:
            time.sleep(15 * (i + 1))
            continue
        if r.get("error", {}).get("code") in (4, 17, 80004, 613):
            time.sleep(60 * (i + 1))
            continue
        return r
    return {"error": {"message": "sin respuesta"}}


def main():
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    cuentas = [p.split(":", 1) for p in os.environ["META_ADS_AD_ACCOUNT_IDS"].split(",") if p.strip()]
    filas = []
    for act, marca in cuentas:
        if marca in MIXTAS:
            continue
        url, p = f"{API}/{act}/insights", {"access_token": TOKEN, "level": "adset", "date_preset": f"last_{dias}d",
                                             "fields": "account_id,account_name,campaign_name,adset_id,adset_name,objective,optimization_goal,spend,impressions,frequency,inline_link_clicks,actions",
                                             "limit": 500}
        while url:
            r = get(url, p)
            p = None
            if "error" in r:
                print("  ERR", act, r["error"].get("message", "")[:80], flush=True)
                break
            for x in r.get("data", []):
                x["marca"] = marca
                x["leads"] = sum(float(a["value"]) for a in x.get("actions") or [] if a["action_type"] == RESULTADO[0])
                x["chats"] = sum(float(a["value"]) for a in x.get("actions") or [] if a["action_type"] == RESULTADO[1])
                x["resultados"] = x["leads"] + x["chats"]
                x.pop("actions", None)
                filas.append(x)
            url = r.get("paging", {}).get("next")
    por_marca = defaultdict(list)
    alcance = defaultdict(lambda: [0.0, 0.0, set()])   # marca -> gasto, resultados, campañas
    for x in filas:
        if float(x["spend"]) <= 0:
            continue
        if x.get("objective") in NO_CONTACTO and not x["resultados"] >= 5:
            a = alcance[x["marca"]]
            a[0] += float(x["spend"])
            a[1] += x["resultados"]
            a[2].add(f"{x['campaign_name'][:40]} ({x.get('objective')})")
            continue
        por_marca[x["marca"]].append(x)
    semanas = dias / 7
    out = {}
    for marca, fs in sorted(por_marca.items(), key=lambda kv: -sum(float(x["spend"]) for x in kv[1])):
        g = sum(float(x["spend"]) for x in fs)
        r = sum(x["resultados"] for x in fs)
        cpr = g / r if r else None
        def ref(x):
            tipo = [y for y in fs if (y["leads"] >= y["chats"]) == (x["leads"] >= x["chats"])]
            gg, rr = sum(float(y["spend"]) for y in tipo), sum(y["resultados"] for y in tipo)
            return gg / rr if rr else None
        caros = [x for x in fs if float(x["spend"]) >= 25 and (not x["resultados"] or float(x["spend"]) / x["resultados"] >= 2 * (ref(x) or 1e9))]
        chicos = [x for x in fs if x["resultados"] / semanas < 10]
        fatiga = [x for x in fs if float(x.get("frequency") or 0) > 4 and float(x["spend"]) >= 10]
        cuentas_m = defaultdict(lambda: [0.0, 0.0])
        for x in fs:
            cuentas_m[(x["account_id"], x["account_name"])][0] += float(x["spend"])
            cuentas_m[(x["account_id"], x["account_name"])][1] += x["resultados"]
            cuentas_m[(x["account_id"], x["account_name"])].append(x["chats"])
        lg = sum(float(x["spend"]) for x in fs if x["leads"] >= x["chats"])
        ll = sum(x["leads"] for x in fs if x["leads"] >= x["chats"])
        cg = sum(float(x["spend"]) for x in fs if x["chats"] > x["leads"])
        cc = sum(x["chats"] for x in fs if x["chats"] > x["leads"])
        out[marca] = {
            "gasto": round(g, 2), "resultados": int(r), "costo_por_resultado": round(cpr, 2) if cpr else None,
            "formularios": {"gasto": round(lg, 2), "leads": int(ll), "cpl": round(lg / ll, 2) if ll else None},
            "whatsapp": {"gasto": round(cg, 2), "chats": int(cc), "costo_chat": round(cg / cc, 2) if cc else None},
            "alcance_trafico": {"gasto": round(alcance[marca][0], 2), "resultados": int(alcance[marca][1]),
                                "campanas": sorted(alcance[marca][2])},
            "conjuntos": len(fs),
            "caros": {"n": len(caros), "gasto": round(sum(float(x["spend"]) for x in caros), 2),
                      "resultados": int(sum(x["resultados"] for x in caros)),
                      "detalle": [(x["campaign_name"][:40], x["adset_name"][:40], round(float(x["spend"]), 2), int(x["resultados"]), x.get("optimization_goal"))
                                  for x in sorted(caros, key=lambda x: -float(x["spend"]))[:6]]},
            "chicos": {"n": len(chicos), "gasto": round(sum(float(x["spend"]) for x in chicos), 2),
                       "resultados": int(sum(x["resultados"] for x in chicos))},
            "fatiga": {"n": len(fatiga), "gasto": round(sum(float(x["spend"]) for x in fatiga), 2),
                       "detalle": [(x["adset_name"][:40], round(float(x["frequency"]), 1)) for x in fatiga[:5]]},
            "cuentas": [{"cuenta": n[:36], "gasto": round(v[0], 2), "resultados": int(v[1]),
                         "costo": round(v[0] / v[1], 2) if v[1] else None, "chats_pct": round(sum(v[2:]) / v[1] * 100) if v[1] else 0}
                        for (_, n), v in sorted(cuentas_m.items(), key=lambda kv: -kv[1][0])],
        }
    ruta = os.path.join(ROOT, "output", f"diagnostico_pauta_{time.strftime('%Y-%m-%d')}.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump({"dias": dias, "marcas": out}, fh, ensure_ascii=False, indent=1)
    tg = sum(v["gasto"] for v in out.values())
    print(f"ÚLTIMOS {dias} DÍAS · gasto total USD {tg:,.0f}")
    print(f"{'marca':10s} {'gasto':>6s} | {'form: USD/leads/CPL':>22s} | {'WA: USD/chats/c-u':>20s} | {'alcance/tráf USD':>16s} | {'caros n/USD/res':>16s} | {'chicos n/USD':>12s} | cuentas")
    for m, v in out.items():
        f, w, a = v["formularios"], v["whatsapp"], v["alcance_trafico"]
        print(f"{m:10s} {v['gasto']+a['gasto']:6.0f} | {f['gasto']:6.0f}/{f['leads']:5d}/{f['cpl'] or 0:5.2f}   | {w['gasto']:6.0f}/{w['chats']:5d}/{w['costo_chat'] or 0:5.2f} | "
              f"{a['gasto']:8.0f} ({a['resultados']:3d}) | {v['caros']['n']:3d}/{v['caros']['gasto']:6.0f}/{v['caros']['resultados']:4d} | {v['chicos']['n']:3d}/{v['chicos']['gasto']:6.0f} | {len(v['cuentas'])}")
    print("guardado en", os.path.relpath(ruta, ROOT))


if __name__ == "__main__":
    main()
