#!/usr/bin/env python3
"""Informe de las pautas IA contra el resto de cada cuenta (Mitsubishi y Renault).

Pregunta de Croman (25-09-2026): cómo van las pautas de prueba, en qué afectan a
las demás campañas de la cuenta (o si las mejoran) y si la cuenta mejoró en
general.

Por cuenta y por día: gasto y leads de la campaña IA y del resto (agencia), el
total de la cuenta y el de los modelos que pauta la IA sumando todas las
campañas. Se compara la ventana anterior al lanzamiento (mismos días) contra lo
que va desde que la IA entrega. Solo agregados de Meta.

Uso: python3 scripts/informe_pautas_ia.py [hasta=AAAA-MM-DD]
"""
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"

CUENTAS = {
    "Mitsubishi": {"act": "act_506680188632635", "ia": "120252656563550663",
                   "modelos": {"L200": ["l200"], "Montero": ["montero"]},
                   "fases": {"antes": ("2026-09-07", "2026-09-20"), "IA 1ª versión": ("2026-09-21", "2026-09-23"),
                             "IA corregida": ("2026-09-24", None)},
                   "cambios": {"2026-09-23": "IA: remarketing y Montero pausados, L200 a prospección (tarde)"}},
    "Renault": {"act": "act_956049245637827", "ia": "120250583223260518",
                "modelos": {"Koleos": ["koleos"], "Master": ["master"]},
                "fases": {"antes": ("2026-09-04", "2026-09-17"), "IA 1ª versión": ("2026-09-18", "2026-09-21"),
                          "IA corregida": ("2026-09-22", None)},
                "cambios": {"2026-09-22": "IA Koleos: formulario, ubicaciones e intereses nuevos"}},
}
CONTACTO = ("lead", "onsite_conversion.messaging_conversation_started_7d")


def filas(act, desde, hasta):
    out, url = [], f"{API}/{act}/insights"
    p = {"access_token": TOKEN, "level": "adset", "time_increment": 1, "limit": 500,
         "fields": "campaign_id,campaign_name,adset_name,spend,actions",
         "time_range": json.dumps({"since": desde, "until": hasta})}
    while url:
        r = requests.get(url, params=p, timeout=120).json()
        p = None
        if "error" in r:
            raise SystemExit(f"{act}: {r['error'].get('message')}")
        out += r.get("data", [])
        url = r.get("paging", {}).get("next")
    return out


def acc(x, tipo):
    return sum(float(a["value"]) for a in x.get("actions") or [] if a["action_type"] == tipo)


def cpl(g, l):
    return round(g / l, 2) if l else None


def main():
    hasta = sys.argv[1] if len(sys.argv) > 1 else (date.today() - timedelta(days=1)).isoformat()
    informe = {}
    for marca, c in CUENTAS.items():
        rows = filas(c["act"], "2026-08-25", hasta)
        camp = defaultdict(dict)
        dia = defaultdict(lambda: {"ia": [0.0, 0.0, 0.0], "resto": [0.0, 0.0, 0.0],
                                   **{m: {"ia": [0.0, 0.0], "resto": [0.0, 0.0]} for m in c["modelos"]}})
        for x in rows:
            quien = "ia" if x["campaign_id"] == c["ia"] else "resto"
            g, l, w = float(x["spend"]), acc(x, "lead"), acc(x, CONTACTO[1])
            d = dia[x["date_start"]]
            d[quien][0] += g
            d[quien][1] += l
            d[quien][2] += w
            en_conjunto = [m for m, ks in c["modelos"].items() if any(k in x["adset_name"].lower() for k in ks)]
            en_campana = [m for m, ks in c["modelos"].items() if any(k in x["campaign_name"].lower() for k in ks)]
            for m in (en_conjunto or (en_campana if len(en_campana) == 1 else [])):
                d[m][quien][0] += g
                d[m][quien][1] += l
                camp[(m, quien, x["campaign_name"])][x["date_start"]] = [camp[(m, quien, x["campaign_name"])].get(x["date_start"], [0, 0])[0] + g,
                                                                        camp[(m, quien, x["campaign_name"])].get(x["date_start"], [0, 0])[1] + l]
        lanz = min((k for k, v in dia.items() if v["ia"][0] > 0), default=None)

        def suma(desde, hasta_, clave, sub=None):
            g = l = 0.0
            for k, v in dia.items():
                if desde <= k <= hasta_:
                    t = v[clave] if sub is None else v[clave][sub]
                    g += t[0]
                    l += t[1]
            return g, l

        res = {"lanzamiento": lanz, "cambios": c["cambios"], "fases": {}}
        for nom, (d_, h_) in c["fases"].items():
            h_ = h_ or hasta
            n = (date.fromisoformat(h_) - date.fromisoformat(d_)).days + 1
            f = {"desde": d_, "hasta": h_, "dias": n}
            for clave in ("ia", "resto"):
                g, l = suma(d_, h_, clave)
                f[clave] = {"gasto_dia": round(g / n, 2), "leads_dia": round(l / n, 1), "cpl": cpl(g, l)}
            g = sum(suma(d_, h_, k)[0] for k in ("ia", "resto"))
            l = sum(suma(d_, h_, k)[1] for k in ("ia", "resto"))
            f["cuenta"] = {"gasto_dia": round(g / n, 2), "leads_dia": round(l / n, 1), "cpl": cpl(g, l)}
            f["modelos"] = {}
            for m in c["modelos"]:
                f["modelos"][m] = {}
                for clave in ("ia", "resto"):
                    g, l = suma(d_, h_, m, clave)
                    f["modelos"][m][clave] = {"gasto_dia": round(g / n, 2), "leads_dia": round(l / n, 1), "cpl": cpl(g, l)}
                gt = sum(suma(d_, h_, m, k)[0] for k in ("ia", "resto"))
                lt = sum(suma(d_, h_, m, k)[1] for k in ("ia", "resto"))
                f["modelos"][m]["total"] = {"gasto_dia": round(gt / n, 2), "leads_dia": round(lt / n, 1), "cpl": cpl(gt, lt)}
            res["fases"][nom] = f
        res["campanas_por_modelo"] = {f"{m} | {q} | {cn}": {k: [round(v[0], 2), int(v[1])] for k, v in sorted(dd.items()) if k >= "2026-09-04"}
                                      for (m, q, cn), dd in camp.items()}
        res["diario"] = {k: {"ia": [round(v["ia"][0], 2), int(v["ia"][1])], "resto": [round(v["resto"][0], 2), int(v["resto"][1])],
                             **{m: {"ia": [round(v[m]["ia"][0], 2), int(v[m]["ia"][1])], "resto": [round(v[m]["resto"][0], 2), int(v[m]["resto"][1])]}
                                for m in c["modelos"]}}
                         for k, v in sorted(dia.items()) if k >= "2026-09-04"}
        informe[marca] = res
    salida = os.path.join(ROOT, "output", f"informe_pautas_ia_{hasta}.json")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(informe, fh, ensure_ascii=False, indent=1)
    for m, r in informe.items():
        print(f"\n=== {m} (IA desde {r.get('lanzamiento')}) ===")
        for nom, f in r.get("fases", {}).items():
            cu, ia, re_ = f["cuenta"], f["ia"], f["resto"]
            print(f"  {nom:14s} {f['desde']}→{f['hasta']} ({f['dias']} d) · CUENTA USD {cu['gasto_dia']:6.2f}/día · {cu['leads_dia']:5.1f} leads/día · CPL {cu['cpl']}"
                  f" | IA {ia['leads_dia']:4.1f}/día CPL {ia['cpl']} | resto {re_['leads_dia']:5.1f}/día CPL {re_['cpl']}")
            for mo, v in f["modelos"].items():
                print(f"      {mo:8s} total {v['total']['leads_dia']:4.1f}/día CPL {v['total']['cpl']} · IA {v['ia']['leads_dia']:4.1f}/día CPL {v['ia']['cpl']} · agencia {v['resto']['leads_dia']:4.1f}/día CPL {v['resto']['cpl']}")
    print("guardado en", os.path.relpath(salida, ROOT))


if __name__ == "__main__":
    main()
