#!/usr/bin/env python3
"""¿Quién más aparece en la compra? Menciones en los chats de Messenger e Instagram.

Complemento del centro de compra (idea de Valentina, 2026-09-24). Recorre las
conversaciones de los últimos N días de todas las páginas que maneja el token
(marcas y asesores) y cuenta en cuántas el cliente nombra a otra persona que
participa de la compra: pareja, hijos, padres, familia, empresa o socio, o
dice que lo tiene que consultar con alguien.

Privacidad: los mensajes se leen en memoria y se descartan. Al disco solo va
el conteo por marca: ni textos, ni nombres, ni identificadores de personas.

El historial de WhatsApp no se puede leer por API (la plataforma no lo guarda);
por eso la fuente son Messenger e Instagram.

Uso: python3 scripts/conversaciones_actores.py [días=90] [--solo-messenger | --solo-instagram]
     (con una sola plataforma, si ya hay una lectura de la otra del mismo día, se suman)
"""
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"

# Página -> marca, por el nombre de la página (las de asesores también nombran la marca)
MARCAS = [("gwm", "GWM"), ("haval", "GWM"), ("jetour", "Jetour"), ("jac", "JAC"), ("mitsubishi", "Mitsubishi"),
          ("renault", "Renault"), ("rnlt", "Renault"), ("renew", "Renew"), ("soueast", "Soueast"),
          ("leapmotor", "Leapmotor"), ("zeekr", "Zeekr"), ("jmev", "JMEV"), ("xpeng", "XPeng"), ("karry", "Karry")]

# Quién aparece. Se busca sobre el texto en minúsculas y sin tildes.
ACTORES = {
    "pareja (ella)": r"\bmi (senora|esposa|mujer|novia|pareja|companera)\b",
    "pareja (él)": r"\bmi (esposo|marido|novio)\b",
    "hijos": r"\bmis? (hij[oa]s?|nen[ea]s?)\b",
    "padres o suegros": r"\bmis? (papa|mama|padres|padre|madre|viej[oa]|suegr[oa]s?)\b",
    "familia": r"\b(mi|la|nuestra|toda la) familia\b",
    "empresa o socio": r"\b(mi|la|nuestra) (empresa|firma|sociedad|estancia)\b|\bpara (la|mi) empresa\b"
                       r"|\bmi (soci[oa]|jef[ea]|patron)\b|\bflota\b|\ba nombre de (la|mi) empresa\b",
}
CONSULTA = (r"\b(consult\w*|habl\w*|coment\w*|charl\w*|decid\w*|convers\w*|mostr\w*|muestr\w*)\b.{0,25}\bcon (mi|mis)\b"
            r"|\b(tengo|tenemos) que (consultar|hablar|decidir|verlo|pensarlo)\b"
            r"|\blo (vamos a|tenemos que|estamos) (pensar|pensando|decidir|charlar|hablar)\b")
PARA_OTRO = r"\bpara (mi|mis) (hij\w*|senora|esposa|esposo|marido|papa|mama|padre|madre|novi[oa]|nieto\w*|soci[oa])\b"


def normalizar(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def marca_de(nombre):
    n = nombre.lower()
    for clave, marca in MARCAS:
        if clave in n:
            return marca
    return "Santa Rosa / multimarca"


def get(url, params=None, intentos=5):
    for i in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=120).json()
        except requests.RequestException:
            time.sleep(15 * (i + 1))
            continue
        cod = r.get("error", {}).get("code")
        if cod in (4, 17, 32, 613, 80001, 80006):
            time.sleep(60 * (i + 1))
            continue
        return r
    return {"error": {"message": "sin respuesta"}}


def _mensajes_ig(conv_id, token, propio):
    """Instagram no acepta los mensajes anidados en la lista: se piden de a una conversación."""
    r = get(f"{API}/{conv_id}/messages", {"access_token": token, "fields": "message,from", "limit": 10})
    if "error" in r:
        return ""
    return " ".join(m.get("message") or "" for m in r.get("data", [])
                    if m.get("from", {}).get("id") not in propio and m.get("message"))


def conversaciones(pagina, plataforma, desde, propio):
    """Genera, por conversación, el texto del cliente concatenado (solo en memoria)."""
    if plataforma == "instagram":
        url = f"{API}/{pagina['id']}/conversations"
        params = {"access_token": pagina["access_token"], "platform": "instagram", "limit": 25, "fields": "updated_time"}
        while url:
            r = get(url, params)
            if "error" in r:
                yield None, r["error"].get("message", "")[:90]
                return
            for c in r.get("data", []):
                if c.get("updated_time", "") < desde:
                    return
                yield _mensajes_ig(c["id"], pagina["access_token"], propio), None
            url, params = r.get("paging", {}).get("next"), None
        return
    limite, msgs = 50, 25
    url = f"{API}/{pagina['id']}/conversations"
    params = {"access_token": pagina["access_token"], "platform": plataforma, "limit": limite,
              "fields": f"updated_time,messages.limit({msgs}){{from,message}}"}
    while url:
        r = get(url, params)
        if "error" in r:
            msg = r["error"].get("message", "").lower()
            if (r["error"].get("code") == 1 or "reduce" in msg or "timeout" in msg) and limite > 5:
                limite, msgs = max(5, limite // 2), max(5, msgs // 2)
                params = {**(params or {}), "limit": limite,
                          "fields": f"updated_time,messages.limit({msgs}){{from,message}}"}
                continue
            yield None, r["error"].get("message", "")[:90]
            return
        for c in r.get("data", []):
            if c.get("updated_time", "") < desde:
                return
            texto = " ".join(m.get("message") or "" for m in c.get("messages", {}).get("data", [])
                             if m.get("from", {}).get("id") not in propio and m.get("message"))
            yield texto, None
        url, params = r.get("paging", {}).get("next"), None


def _sumar(previo, nuevo):
    """Suma conteos de dos lecturas del mismo período (una por plataforma)."""
    for marca, v in previo.get("marcas", {}).items():
        n = nuevo["marcas"].setdefault(marca, {k: (0 if not isinstance(x, dict) else {}) for k, x in v.items()})
        for k, x in v.items():
            if k == "actores":
                for a, c in x.items():
                    n["actores"][a] = n["actores"].get(a, 0) + c
            elif k == "por_plataforma":
                for a, c in x.items():
                    n["por_plataforma"][a] = n["por_plataforma"].get(a, 0) + c
            elif isinstance(x, (int, float)) and k not in ("con_otra_persona_pct", "paginas"):
                n[k] = n.get(k, 0) + x
            elif k == "paginas":
                n[k] = max(n.get(k, 0), x)
    for n in nuevo["marcas"].values():
        n["con_otra_persona_pct"] = round(n["con_otra_persona"] / n["con_texto_del_cliente"] * 100, 1) if n["con_texto_del_cliente"] else 0
        n["actores"] = dict(sorted(n["actores"].items(), key=lambda x: -x[1]))
    nuevo["marcas"] = dict(sorted(nuevo["marcas"].items(), key=lambda x: -x[1]["con_texto_del_cliente"]))
    return nuevo


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dias = int(args[0]) if args else 90
    plataformas = ("messenger", "instagram")
    if "--solo-instagram" in sys.argv:
        plataformas = ("instagram",)
    if "--solo-messenger" in sys.argv:
        plataformas = ("messenger",)
    hoy = datetime.now(timezone.utc)
    desde = (hoy - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%S")
    pags = get(f"{API}/me/accounts", {"access_token": TOKEN, "fields": "id,name,access_token,instagram_business_account",
                                       "limit": 100}).get("data", [])
    res = defaultdict(lambda: {"conversaciones": 0, "con_texto_del_cliente": 0, "con_otra_persona": 0,
                               "actores": defaultdict(int), "lo_consulta_con_alguien": 0, "es_para_otro": 0,
                               "paginas": set(), "por_plataforma": defaultdict(int)})
    pat = {k: re.compile(v) for k, v in ACTORES.items()}
    consulta, para_otro = re.compile(CONSULTA), re.compile(PARA_OTRO)
    for n, p in enumerate(pags, 1):
        marca = marca_de(p["name"])
        propio = {p["id"]} | ({p["instagram_business_account"]["id"]} if p.get("instagram_business_account") else set())
        for plat in plataformas:
            if plat == "instagram" and not p.get("instagram_business_account"):
                continue
            cuenta = 0
            for texto, err in conversaciones(p, plat, desde, propio):
                if err:
                    print(f"   {p['name'][:28]} {plat}: {err}", flush=True)
                    break
                m = res[marca]
                m["conversaciones"] += 1
                m["por_plataforma"][plat] += 1
                m["paginas"].add(p["name"])
                cuenta += 1
                t = normalizar(texto or "")
                if not t.strip():
                    continue
                m["con_texto_del_cliente"] += 1
                hallados = [k for k, rx in pat.items() if rx.search(t)]
                c = bool(consulta.search(t))
                o = bool(para_otro.search(t))
                for k in hallados:
                    m["actores"][k] += 1
                m["lo_consulta_con_alguien"] += c
                m["es_para_otro"] += o
                if hallados or c or o:
                    m["con_otra_persona"] += 1
            print(f"   {n}/{len(pags)} {p['name'][:30]:30s} {plat:9s} {cuenta} conversaciones", flush=True)
    salida = {"periodo": {"desde": desde[:10], "hasta": hoy.strftime("%Y-%m-%d"), "dias": dias},
              "fuente": "Messenger e Instagram de las páginas de marca y de asesores (WhatsApp no guarda historial accesible)",
              "marcas": {}}
    for marca, m in sorted(res.items(), key=lambda x: -x[1]["con_texto_del_cliente"]):
        salida["marcas"][marca] = {
            "conversaciones": m["conversaciones"], "con_texto_del_cliente": m["con_texto_del_cliente"],
            "con_otra_persona": m["con_otra_persona"],
            "con_otra_persona_pct": round(m["con_otra_persona"] / m["con_texto_del_cliente"] * 100, 1) if m["con_texto_del_cliente"] else 0,
            "actores": dict(sorted(m["actores"].items(), key=lambda x: -x[1])),
            "lo_consulta_con_alguien": m["lo_consulta_con_alguien"], "es_para_otro": m["es_para_otro"],
            "paginas": len(m["paginas"]), "por_plataforma": dict(m["por_plataforma"]),
        }
    ruta = os.path.join(ROOT, "output", "raw", f"conversaciones_actores_{salida['periodo']['hasta']}.json")
    salida["plataformas"] = list(plataformas)
    if len(plataformas) == 1 and os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            previo = json.load(fh)
        if set(previo.get("plataformas", ["messenger", "instagram"])) != set(plataformas):
            salida = _sumar(previo, salida)
            salida["plataformas"] = sorted(set(previo.get("plataformas", [])) | set(plataformas))
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print("\nRESULTADO (solo conteos)")
    for marca, m in salida["marcas"].items():
        print(f"  {marca:24s} {m['con_texto_del_cliente']:6d} chats con texto · {m['con_otra_persona_pct']:4.1f}% nombran a otra persona · "
              f"{m['actores']} · consulta {m['lo_consulta_con_alguien']} · para otro {m['es_para_otro']}")
    print("guardado en", os.path.relpath(ruta, ROOT))


if __name__ == "__main__":
    main()
