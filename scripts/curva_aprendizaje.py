#!/usr/bin/env python3
"""Curva de aprendizaje en nuestras cuentas de Meta: ¿el costo por resultado baja con las semanas?

Pregunta (26-09-2026): el estudio de 26 semanas guardado en el vault (Google AI
Max, PMax, Meta Advantage+ Leads y Conversion Leads) dice que Meta abarata el
lead rápido y Google con estructura y tiempo. ¿Pasa lo mismo en nuestras cuentas?

1. Curva: costo por resultado de cada campaña de formulario o WhatsApp según su
   semana de vida, comparado con sus dos primeras semanas. Cohorte fija: solo
   campañas que arrancaron dentro de la ventana y siguieron pautando 8 (o 26)
   semanas, así la curva no mejora solo porque las malas se cortan.
2. Aprendizaje hoy: de los conjuntos activos, cuántos siguen aprendiendo,
   cuántos salieron y cuántos están en «aprendizaje limitado» (no juntan los
   ~50 resultados por semana que pide Meta), con su gasto de los últimos 7 días.

Resultado = formulario enviado o chat de WhatsApp/Messenger iniciado.
Solo agregados de Meta.

Uso: python3 scripts/curva_aprendizaje.py [desde=2025-06-02] [hasta=último domingo]
"""
import json
import math
import os
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"
LEAD, CHAT = "lead", "onsite_conversion.messaging_conversation_started_7d"
SIN_CONTACTO = {"OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "BRAND_AWARENESS", "REACH", "LINK_CLICKS", "VIDEO_VIEWS", "POST_ENGAGEMENT"}
BLOQUES = [("S1-2", 1, 2), ("S3-4", 3, 4), ("S5-8", 5, 8), ("S9-12", 9, 12), ("S13-18", 13, 18), ("S19-26", 19, 26)]
IA = {"120252656563550663": "Mitsubishi IA", "120250583223260518": "Renault IA"}


def get(url, params=None):
    for i in range(5):
        try:
            r = requests.get(url, params=params, timeout=180).json()
        except requests.RequestException:
            time.sleep(15 * (i + 1))
            continue
        if r.get("error", {}).get("code") in (4, 17, 80004, 613):
            time.sleep(60 * (i + 1))
            continue
        return r
    return {"error": {"message": "sin respuesta"}}


def paginar(url, params):
    out = []
    while url:
        r = get(url, params)
        params = None
        if "error" in r:
            return None, r["error"].get("message", "")
        out += r.get("data", [])
        url = r.get("paging", {}).get("next")
    return out, None


def semanal(act, desde, hasta):
    """Insights por campaña y semana. Si Meta pide menos datos, parte el rango en dos (alineado a semanas)."""
    p = {"access_token": TOKEN, "level": "campaign", "time_increment": 7, "limit": 500,
         "fields": "campaign_id,campaign_name,objective,spend,actions",
         "time_range": json.dumps({"since": desde.isoformat(), "until": hasta.isoformat()})}
    filas, err = paginar(f"{API}/{act}/insights", p)
    if filas is not None:
        return filas
    semanas = ((hasta - desde).days + 1) // 7
    if "reduce the amount" in err.lower() and semanas > 4:
        medio = desde + timedelta(days=7 * (semanas // 2))
        return semanal(act, desde, medio - timedelta(days=1)) + semanal(act, medio, hasta)
    print("  ERR", act, err[:90], flush=True)
    return []


def acc(x, tipo):
    return sum(float(a["value"]) for a in x.get("actions") or [] if a["action_type"] == tipo)


def aprendizaje(act, marca):
    p = {"access_token": TOKEN, "limit": 200, "effective_status": json.dumps(["ACTIVE"]),
         "fields": "id,name,campaign_id,optimization_goal,learning_stage_info,campaign{name,objective}"}
    conjuntos, err = paginar(f"{API}/{act}/adsets", p)
    if conjuntos is None:
        print("  ERR adsets", act, err[:90], flush=True)
        return []
    p = {"access_token": TOKEN, "level": "adset", "date_preset": "last_7d", "limit": 500, "fields": "adset_id,spend,actions"}
    ins, _ = paginar(f"{API}/{act}/insights", p)
    g7 = {x["adset_id"]: (float(x["spend"]), acc(x, LEAD) + acc(x, CHAT)) for x in ins or []}
    out = []
    for c in conjuntos:
        info = c.get("learning_stage_info") or {}
        gasto, res = g7.get(c["id"], (0.0, 0.0))
        out.append({"marca": marca, "cuenta": act, "conjunto": c["name"][:60], "campana": (c.get("campaign") or {}).get("name", "")[:60],
                    "campaign_id": c.get("campaign_id"), "objetivo": (c.get("campaign") or {}).get("objective"),
                    "optimiza": c.get("optimization_goal"), "estado": info.get("status") or "SIN_DATO",
                    "conversiones_aprendizaje": info.get("conversions"), "ultimo_cambio_significativo": info.get("last_sig_edited_ts"),
                    "gasto_7d": round(gasto, 2), "resultados_7d": int(res)})
    return out


def ultimo_domingo():
    hoy = date.today()
    return hoy - timedelta(days=hoy.weekday() + 1)


def mediana(xs):
    return round(st.median(xs), 3) if xs else None


def main():
    desde = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2025, 6, 2)
    hasta = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else ultimo_domingo()
    desde -= timedelta(days=desde.weekday())                     # lunes
    hasta = desde + timedelta(days=7 * (((hasta - desde).days + 1) // 7) - 1)   # semanas completas
    cuentas = [p.split(":", 1) for p in os.environ["META_ADS_AD_ACCOUNT_IDS"].split(",") if p.strip()]
    camp, conjuntos = {}, []
    for i, (act, marca) in enumerate(cuentas, 1):
        print(f"[{i}/{len(cuentas)}] {marca} {act}", flush=True)
        for x in semanal(act, desde, hasta):
            k = (date.fromisoformat(x["date_start"]) - desde).days // 7
            c = camp.setdefault(x["campaign_id"], {"marca": marca, "nombre": x["campaign_name"], "objetivo": x.get("objective"),
                                                   "semanas": defaultdict(lambda: [0.0, 0.0, 0.0])})
            s = c["semanas"][k]
            s[0] += float(x["spend"])
            s[1] += acc(x, LEAD)
            s[2] += acc(x, CHAT)
        conjuntos += aprendizaje(act, marca)

    # 1. Curva por semana de vida
    ultima = (hasta - desde).days // 7
    vidas = []
    for cid, c in camp.items():
        if c["objetivo"] in SIN_CONTACTO:
            continue
        activas = sorted(k for k, v in c["semanas"].items() if v[0] > 0)
        if not activas or activas[0] < 2:      # ya pautaba al abrir la ventana: edad desconocida
            continue
        k0 = activas[0]
        vida = {k - k0 + 1: v for k, v in c["semanas"].items() if k >= k0}
        leads = sum(v[1] for v in vida.values())
        chats = sum(v[2] for v in vida.values())
        vidas.append({"id": cid, "marca": c["marca"], "nombre": c["nombre"], "tipo": "WhatsApp" if chats > leads else "Formulario",
                      "lanzamiento": (desde + timedelta(days=7 * k0)).isoformat(), "semanas_posibles": ultima - k0 + 1, "vida": vida})

    def bloque(vida, a, b):
        g = sum(vida[k][0] for k in range(a, b + 1) if k in vida)
        r = sum(vida[k][1] + vida[k][2] for k in range(a, b + 1) if k in vida)
        return g, r

    curvas = {}
    for n in (8, 26):
        for tipo in ("Formulario", "WhatsApp", "Todas"):
            coh = []
            for v in vidas:
                if tipo != "Todas" and v["tipo"] != tipo:
                    continue
                if v["semanas_posibles"] < n:
                    continue
                semanas_con_gasto = sum(1 for k in range(1, n + 1) if v["vida"].get(k, [0])[0] >= 5)
                g_tot, r_tot = bloque(v["vida"], 1, n)
                g0, r0 = bloque(v["vida"], 1, 2)
                if semanas_con_gasto < math.ceil(0.8 * n) or r_tot < 5 * n or r0 < 8:
                    continue
                coh.append(v)
            bl = {}
            for nom, a, b in BLOQUES:
                if b > n:
                    continue
                ratios, gg, rr = [], 0.0, 0.0
                for v in coh:
                    g, r = bloque(v["vida"], a, b)
                    g0, r0 = bloque(v["vida"], 1, 2)
                    gg += g
                    rr += r
                    if r >= 3:
                        ratios.append((g / r) / (g0 / r0))
                bl[nom] = {"mediana_vs_S1-2": mediana(ratios), "campanas": len(ratios),
                           "mas_baratas_pct": round(100 * sum(x < 1 for x in ratios) / len(ratios)) if ratios else None,
                           "cpl_conjunto": round(gg / rr, 2) if rr else None}
            sem1 = [((v["vida"][1][0] / (v["vida"][1][1] + v["vida"][1][2])) / (bloque(v["vida"], 3, 4)[0] / bloque(v["vida"], 3, 4)[1]))
                    for v in coh if 1 in v["vida"] and v["vida"][1][1] + v["vida"][1][2] >= 3 and bloque(v["vida"], 3, 4)[1] >= 3]
            curvas[f"{n}s|{tipo}"] = {"campanas": len(coh), "bloques": bl, "semana1_vs_S3-4": mediana(sem1),
                                      "marcas": dict(sorted(((m, sum(1 for v in coh if v["marca"] == m)) for m in {v["marca"] for v in coh}), key=lambda kv: -kv[1]))}

    # 2. Aprendizaje hoy
    por_marca = defaultdict(lambda: defaultdict(lambda: [0, 0.0, 0]))
    for c in conjuntos:
        if c["objetivo"] in SIN_CONTACTO:
            continue
        t = por_marca[c["marca"]][c["estado"]]
        t[0] += 1
        t[1] += c["gasto_7d"]
        t[2] += c["resultados_7d"]
    total = defaultdict(lambda: [0, 0.0, 0])
    for m, d in por_marca.items():
        for e, t in d.items():
            for i in range(3):
                total[e][i] += t[i]

    salida = os.path.join(ROOT, "output", f"curva_aprendizaje_{date.today().isoformat()}.json")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump({"desde": desde.isoformat(), "hasta": hasta.isoformat(), "campanas_nuevas": len(vidas), "curvas": curvas,
                   "aprendizaje_total": {e: {"conjuntos": t[0], "gasto_7d": round(t[1], 2), "resultados_7d": t[2]} for e, t in total.items()},
                   "aprendizaje_por_marca": {m: {e: {"conjuntos": t[0], "gasto_7d": round(t[1], 2), "resultados_7d": t[2]} for e, t in d.items()}
                                             for m, d in por_marca.items()},
                   "conjuntos_ia": [c for c in conjuntos if c["campaign_id"] in IA],
                   "conjuntos_mitsubishi_renault": [c for c in conjuntos if c["marca"] in ("Mitsubishi", "Renault") and c["objetivo"] not in SIN_CONTACTO],
                   "vidas": [{k: v for k, v in x.items() if k != "vida"} | {"vida": {str(k): [round(s[0], 2), int(s[1]), int(s[2])] for k, s in sorted(x["vida"].items())}}
                             for x in vidas]}, fh, ensure_ascii=False, indent=1)

    print(f"\nVentana {desde} → {hasta} · campañas nuevas de contacto: {len(vidas)}")
    for k, c in curvas.items():
        linea = " · ".join(f"{nom} {b['mediana_vs_S1-2']}×({b['campanas']}, {b['mas_baratas_pct']}% más baratas)" for nom, b in c["bloques"].items())
        print(f"  {k:14s} n={c['campanas']:3d} | sem1 vs S3-4 {c['semana1_vs_S3-4']}× | {linea}")
    print("\nAprendizaje hoy (conjuntos activos de contacto):")
    for e, t in sorted(total.items(), key=lambda kv: -kv[1][1]):
        print(f"  {e:10s} {t[0]:4d} conjuntos · USD {t[1]:8.0f} en 7 días · {t[2]:5d} resultados")
    for c in [c for c in conjuntos if c["campaign_id"] in IA]:
        print(f"  IA {c['marca']:10s} {c['conjunto'][:40]:40s} {c['estado']:9s} conv={c['conversiones_aprendizaje']} 7d USD {c['gasto_7d']} → {c['resultados_7d']}")
    print("guardado en", os.path.relpath(salida, ROOT))


if __name__ == "__main__":
    main()
