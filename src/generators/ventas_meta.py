"""
Ventas que vinieron de Meta: cada venta del ERP se busca entre los leads de formulario de Meta.

Pregunta de Croman (03-10-2026). Bitrix carga la mayoría de las ventas como «Prospecto
del Asesor», pero el cruce a mano de las ventas de Soueast de septiembre encontró que 15
de 39 tuvieron un lead previo de Meta (12 de ellas figuraban como prospecto propio). Esto
lo hace todos los días, para todas las marcas, y da el costo por venta de cada campaña.

Cómo se cruza:
- Cada venta a cliente final (no subconcesionarios) se busca entre los leads de los 120
  días anteriores: primero por teléfono o mail (seguro) y si no por nombre, solo cuando
  todas las palabras del nombre del lead están en el del cliente y ese nombre no aparece
  en ninguna otra venta (los nombres comunes quedan como «ambiguos» y no se cuentan).
- El lead dice de qué campaña vino; la campaña, de qué cuenta. Así se separa la campaña
  de la marca, la de un asesor, la de otra marca y el formulario sin anuncio.

Privacidad: el nombre, el teléfono y el mail del cliente (ERP) y del lead (Meta) se
convierten en claves cifradas con una sal que se genera en cada corrida y nunca se
guarda. Los datos crudos no salen de la función que los lee y lo único que se guarda
son totales.
"""

from __future__ import annotations

import hashlib
import os
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

# Sal de esta corrida: con otra sal las claves no coinciden, así que no sirven fuera de acá.
SAL = os.urandom(16)
DIAS_MAX = 120            # del lead a la venta: el cruce de Soueast dio de 11 a 81 días
MARGEN_INICIO = 30        # días de leads que hacen falta antes de la primera venta evaluada
NO_ES_NOMBRE = {"DE", "DEL", "LA", "LAS", "LOS", "Y", "EL", "SA", "SRL", "EIRL", "SAE", "SACI"}
CAMPO_NOMBRE = re.compile(r"full_name|first_name|last_name|nombre|apellido", re.I)
CAMPO_TELEFONO = re.compile(r"phone|tel[eé]fono|celular|whatsapp|n[uú]mero", re.I)
CAMPO_MAIL = re.compile(r"email|e-mail|correo|mail", re.I)
NO_ES_PERSONAL = re.compile(r"modelo|empresa|ciudad|documento|c[eé]dula|ruc|ci\b", re.I)
GENERICAS_CUENTA = {"PARAGUAY", "PY", "CDE", "ST", "USADOS", "SANTA", "ROSA", "META", "ADS", "CUENTA",
                    "FACEBOOK", "OFICIAL", "MOTORS", "AUTOMOTORES", "GREAT", "WALL", "GREATWALL", "HAVAL"}


def _h(texto: str) -> str:
    return hashlib.sha256(SAL + texto.encode("utf-8")).hexdigest()[:16]


def _normalizar(texto: Any) -> str:
    s = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z ]+", " ", s)


def claves_de_nombre(texto: Any) -> frozenset[str]:
    """Palabras del nombre (3 letras o más, sin «de», «la», «SA»…), cifradas."""
    return frozenset(_h(p) for p in _normalizar(texto).split() if len(p) >= 3 and p not in NO_ES_NOMBRE)


def claves_de_telefono(texto: Any) -> set[str]:
    """Últimos 8 dígitos de cada número del campo: iguala 0981…, +595981… y 021…, +59521…"""
    claves = set()
    for parte in re.split(r"[/,;|]| - |\by\b", str(texto or "")):
        digitos = re.sub(r"\D", "", parte)
        if len(digitos) >= 8:
            claves.add(_h(digitos[-8:]))
    return claves


def clave_de_mail(texto: Any) -> str | None:
    s = str(texto or "").strip().lower()
    return _h(s) if "@" in s and "." in s.split("@")[-1] else None


def claves_de_venta(df: Any) -> list[dict[str, Any]]:
    """Claves de cada venta del ERP, antes de descartar los datos personales.

    ``df`` es el reporte del ERP ya filtrado (sin notas de crédito) con ``marca`` y
    ``producto`` resueltos. Devuelve solo fecha, marca, modelo, tipo de comprador y
    claves cifradas.
    """
    out = []
    col = lambda c: df[c] if c in df.columns else [None] * len(df)  # noqa: E731
    for fecha, marca, modelo, tipo, cliente, tels, mail in zip(
            col("Fecha"), col("marca"), col("producto"), col("tipo_comprador"),
            col("Cliente"), col("Teléfonos"), col("E-Mail")):
        try:
            f = fecha.date() if hasattr(fecha, "date") else date.fromisoformat(str(fecha)[:10])
        except (TypeError, ValueError):
            continue
        out.append({"fecha": f, "marca": marca, "modelo": modelo, "tipo_comprador": tipo or "persona",
                    "nombre": claves_de_nombre(cliente), "tels": claves_de_telefono(tels), "mail": clave_de_mail(mail)})
    return out


def claves_de_lead(lead: dict[str, Any], marca_pagina: str) -> dict[str, Any] | None:
    """Claves de un lead de formulario de Meta, con su campaña. Nada crudo sale de acá."""
    nombre, apellido, tels, mail = "", "", set(), None
    for campo in lead.get("field_data", []):
        n = str(campo.get("name", "")).lower()
        valor = str((campo.get("values") or [""])[0] or "").strip()
        if not valor or NO_ES_PERSONAL.search(n):
            continue
        if CAMPO_MAIL.search(n):
            mail = mail or clave_de_mail(valor)
        elif CAMPO_TELEFONO.search(n):
            tels |= claves_de_telefono(valor)
        elif CAMPO_NOMBRE.search(n):
            if "last_name" in n or "apellido" in n:
                apellido = valor
            else:
                nombre = f"{nombre} {valor}".strip()
    try:
        fecha = date.fromisoformat(str(lead.get("created_time", ""))[:10])
    except ValueError:
        return None
    claves = claves_de_nombre(f"{nombre} {apellido}")
    if not (claves or tels or mail):
        return None
    return {"fecha": fecha, "marca_pagina": marca_pagina, "campaign_id": lead.get("campaign_id") or "",
            "campaign_name": lead.get("campaign_name") or "", "ad_name": lead.get("ad_name") or "",
            "organico": bool(lead.get("is_organic")), "nombre": claves, "tels": tels, "mail": mail}


def es_cuenta_de_asesor(cuenta: str, marca: str) -> bool:
    """Las cuentas de asesor llevan el nombre de la persona («CARMEN FRANCO | GWM CDE»)."""
    if "ASESOR" in _normalizar(cuenta):
        return True
    propias = set(_normalizar(marca).split()) | GENERICAS_CUENTA
    resto = [p for p in _normalizar(cuenta).split() if len(p) >= 3 and p not in propias]
    return len(resto) >= 2


def _info_campanas(campanas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    info: dict[str, dict[str, Any]] = {}
    for c in campanas:
        cid = str(c.get("campaign_id") or "")
        if not cid:
            continue
        d = info.setdefault(cid, {"nombre": c.get("campaign_name", ""), "marca_cuenta": c.get("account", ""),
                                  "cuenta": c.get("account_name", ""), "gasto": 0.0})
        try:
            d["gasto"] += float(c.get("spend") or 0)
        except (TypeError, ValueError):
            pass
    return info


def _origen(lead: dict[str, Any], marca_venta: str, info: dict[str, dict[str, Any]]) -> tuple[str, str]:
    """(origen, marca de la campaña) del lead que terminó en esta venta."""
    if lead["organico"] or not lead["campaign_id"]:
        return "Formulario sin anuncio", lead["marca_pagina"]
    c = info.get(lead["campaign_id"])
    if not c:
        # Cuenta fuera de la lista (asesores, multimarca): no se adivina la marca por la página.
        return "Campaña de una cuenta que no se lee", ""
    if c["marca_cuenta"] != marca_venta:
        return "Campaña de otra marca", c["marca_cuenta"]
    return ("Campaña de un asesor" if es_cuenta_de_asesor(c["cuenta"], marca_venta) else "Campaña de la marca"), c["marca_cuenta"]


def cruzar(ventas: list[dict[str, Any]], leads: list[dict[str, Any]], campanas: list[dict[str, Any]],
           dias_max: int = DIAS_MAX) -> dict[str, Any]:
    """Cruza ventas y leads (claves cifradas) y devuelve solo totales."""
    if not ventas or not leads:
        return {}
    info = _info_campanas(campanas)
    desde_leads, hasta_leads = min(l["fecha"] for l in leads), max(l["fecha"] for l in leads)
    finales = [v for v in ventas if v["tipo_comprador"] != "revendedor"]
    inicio = desde_leads + timedelta(days=MARGEN_INICIO)
    evaluadas = [v for v in finales if v["fecha"] >= inicio]

    por_tel, por_mail, por_token = defaultdict(list), defaultdict(list), defaultdict(list)
    for i, l in enumerate(leads):
        for t in l["tels"]:
            por_tel[t].append(i)
        if l["mail"]:
            por_mail[l["mail"]].append(i)
        for tok in l["nombre"]:
            por_token[tok].append(i)
    # Un nombre que aparece en más de 3 leads es de varias personas: no sirve para cruzar.
    leads_por_nombre = Counter(l["nombre"] for l in leads if len(l["nombre"]) >= 2)
    ventas_por_token = defaultdict(set)
    for j, v in enumerate(finales):
        for tok in v["nombre"]:
            ventas_por_token[tok].add(j)

    def en_ventana(v, l):
        return 0 <= (v["fecha"] - l["fecha"]).days <= dias_max

    def unico(nombre_lead) -> bool:
        conjuntos = [ventas_por_token.get(t, set()) for t in nombre_lead]
        return (bool(conjuntos) and len(set.intersection(*conjuntos)) == 1
                and leads_por_nombre.get(nombre_lead, 0) <= 3)

    def preferencia(v, l):
        """Entre leads de la misma persona: primero el de la marca que compró, después el más reciente."""
        c = info.get(l["campaign_id"]) if l["campaign_id"] else None
        return ((c or {}).get("marca_cuenta") == v["marca"], l["fecha"])

    por_marca: dict[str, dict[str, Any]] = {}
    entre_marcas: Counter = Counter()
    por_campana: dict[str, dict[str, Any]] = {}
    dias_todos: list[int] = []
    for v in evaluadas:
        m = por_marca.setdefault(v["marca"], {"ventas": 0, "con_contacto": 0, "con_meta": 0, "por_contacto": 0,
                                             "por_nombre": 0, "ambiguas": 0, "origen": Counter(), "dias": [],
                                             "por_mes": defaultdict(lambda: [0, 0])})
        mes = v["fecha"].isoformat()[:7]
        m["ventas"] += 1
        m["por_mes"][mes][0] += 1
        m["con_contacto"] += bool(v["tels"] or v["mail"])

        fuertes = {i for t in v["tels"] for i in por_tel.get(t, [])} | set(por_mail.get(v["mail"], []) if v["mail"] else [])
        fuertes = [leads[i] for i in fuertes if en_ventana(v, leads[i])]
        elegido, evidencia = None, ""
        if fuertes:
            elegido, evidencia = max(fuertes, key=lambda l: preferencia(v, l)), "contacto"
        else:
            cuenta_tok = Counter(i for tok in v["nombre"] for i in por_token.get(tok, []))
            candidatos = [leads[i] for i, n in cuenta_tok.items()
                          if len(leads[i]["nombre"]) >= 2 and n == len(leads[i]["nombre"]) and en_ventana(v, leads[i])]
            if candidatos:
                largo = max(len(l["nombre"]) for l in candidatos)
                mejor = max((l for l in candidatos if len(l["nombre"]) == largo), key=lambda l: preferencia(v, l))
                if unico(mejor["nombre"]):
                    elegido, evidencia = mejor, "nombre"
                else:
                    m["ambiguas"] += 1
        if not elegido:
            continue
        origen, marca_lead = _origen(elegido, v["marca"], info)
        dias = (v["fecha"] - elegido["fecha"]).days
        m["con_meta"] += 1
        m["por_mes"][mes][1] += 1
        m["por_contacto" if evidencia == "contacto" else "por_nombre"] += 1
        m["origen"][origen] += 1
        m["dias"].append(dias)
        dias_todos.append(dias)
        if marca_lead and marca_lead != v["marca"]:
            entre_marcas[(marca_lead, v["marca"])] += 1
        if elegido["campaign_id"] and not elegido["organico"]:
            c = info.get(elegido["campaign_id"], {})
            pc = por_campana.setdefault(elegido["campaign_id"], {
                "campana": c.get("nombre") or elegido["campaign_name"], "cuenta": c.get("cuenta", ""),
                "marca_cuenta": c.get("marca_cuenta") or elegido["marca_pagina"], "ventas": 0,
                "marcas_vendidas": Counter(), "gasto_90d": round(c.get("gasto", 0.0), 2) if c else None})
            pc["ventas"] += 1
            pc["marcas_vendidas"][v["marca"]] += 1

    def mediana(xs):
        return round(statistics.median(xs)) if xs else None

    campanas_out = []
    for pc in sorted(por_campana.values(), key=lambda x: -x["ventas"]):
        costo = round(pc["gasto_90d"] / pc["ventas"], 2) if pc["gasto_90d"] else None
        campanas_out.append({**pc, "marcas_vendidas": dict(pc["marcas_vendidas"]), "costo_por_venta": costo})
    q = statistics.quantiles(dias_todos, n=4) if len(dias_todos) >= 4 else []
    return {
        "generado": datetime.now().isoformat(timespec="minutes"),
        "ventana_leads": {"desde": desde_leads.isoformat(), "hasta": hasta_leads.isoformat()},
        "leads_leidos": len(leads),
        "ventas_desde": inicio.isoformat(),
        "ventas_hasta": max(v["fecha"] for v in ventas).isoformat(),
        "ventas_evaluadas": len(evaluadas),
        "por_marca": {k: {**{x: v[x] for x in ("ventas", "con_contacto", "con_meta", "por_contacto", "por_nombre", "ambiguas")},
                          "origen": dict(v["origen"]), "dias_mediana": mediana(v["dias"]),
                          "por_mes": {mes: {"ventas": a, "con_meta": b} for mes, (a, b) in sorted(v["por_mes"].items())}}
                      for k, v in sorted(por_marca.items(), key=lambda kv: -kv[1]["ventas"])},
        "entre_marcas": [{"campana_de": a, "venta_de": b, "ventas": n} for (a, b), n in entre_marcas.most_common()],
        "campanas": campanas_out[:25],
        "dias": {"mediana": mediana(dias_todos), "p25": round(q[0]) if q else None, "p75": round(q[2]) if q else None,
                 "n": len(dias_todos)},
    }


def _n(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _pct(a: int, b: int) -> str:
    return f"{a / b * 100:.0f} %" if b else "—"


def nota(r: dict[str, Any]) -> str:
    """Nota del vault (uso interno: compara marcas entre sí)."""
    hoy = date.today().isoformat()
    if not r:
        return f"# 💰 Ventas que vinieron de Meta\n\nSin datos en la corrida del {hoy}.\n"
    tot_v = sum(m["ventas"] for m in r["por_marca"].values())
    tot_m = sum(m["con_meta"] for m in r["por_marca"].values())
    L = [
        "---", "type: ventas-meta", f"updated: {hoy}", "tags: [meta-ads, ventas, atribucion, interno]", "---",
        "# 💰 Ventas que vinieron de Meta", "",
        "> [!info] Qué es",
        "> Cada venta del ERP a un cliente final se busca entre los leads de formulario de Meta de los 120 días "
        "anteriores: primero por teléfono o mail, y si no por nombre, solo cuando ese nombre no aparece en otra venta. "
        "Se actualiza en cada corrida. **No se guarda ningún nombre, teléfono ni mail: solo totales.** Uso interno.", "",
        f"**Ventas evaluadas:** {_n(r['ventas_evaluadas'])} a clientes finales, del {r['ventas_desde']} al {r['ventas_hasta']} "
        f"(último dato del ERP) · **leads de Meta:** {_n(r['leads_leidos'])}, del {r['ventana_leads']['desde']} al "
        f"{r['ventana_leads']['hasta']}.", "",
        f"**En total, {_n(tot_m)} de {_n(tot_v)} ventas ({_pct(tot_m, tot_v)}) tuvieron un lead previo de Meta.** "
        + (f"Del lead a la venta pasan {r['dias']['mediana']} días (mediana; la mitad, entre {r['dias']['p25']} y "
           f"{r['dias']['p75']})." if r["dias"].get("mediana") is not None else ""), "",
        *([f"> [!warning] El ERP casi no trae teléfono ni mail en estas ventas ({_pct(sum(m['con_contacto'] for m in r['por_marca'].values()), tot_v)})",
            "> Entonces el cruce depende del nombre, que es menos seguro. Antes de agosto de 2026 el reporte de facturación traía "
            "teléfono o mail en el 41 % de las ventas: pedir que se vuelvan a exportar esas columnas.", ""]
          if sum(m["con_contacto"] for m in r["por_marca"].values()) < 0.2 * tot_v else []),
        "## Por marca", "",
        "| Marca | Ventas | Con lead de Meta | % | Por teléfono o mail | Por nombre | Ventas con teléfono o mail en el ERP | Del lead a la venta |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for marca, m in r["por_marca"].items():
        dias = f"{m['dias_mediana']} días" if m["dias_mediana"] is not None else "—"
        L.append(f"| {marca} | {m['ventas']} | {m['con_meta']} | {_pct(m['con_meta'], m['ventas'])} | {m['por_contacto']} | "
                 f"{m['por_nombre']} | {_pct(m['con_contacto'], m['ventas'])} | {dias} |")
    origenes = ["Campaña de la marca", "Campaña de un asesor", "Campaña de otra marca", "Formulario sin anuncio",
                "Campaña de una cuenta que no se lee"]
    L += ["", "## De dónde vino el lead", "", "| Marca | " + " | ".join(origenes) + " |", "|---" * (len(origenes) + 1) + "|"]
    for marca, m in r["por_marca"].items():
        if m["con_meta"]:
            L.append(f"| {marca} | " + " | ".join(str(m["origen"].get(o, 0)) for o in origenes) + " |")
    if r["entre_marcas"]:
        L += ["", "## La venta es de una marca y el lead de otra", "",
              "La gente compara por segmento y precio, no por marca: el lead de una marca termina comprando otra.", "",
              "| Lead de | Venta de | Ventas |", "|---|---|---|"]
        L += [f"| {x['campana_de']} | {x['venta_de']} | {x['ventas']} |" for x in r["entre_marcas"][:15]]
    if r["campanas"]:
        L += ["", "## Campañas con más ventas", "",
              "| Campaña | Cuenta | Marca de la cuenta | Ventas | Gasto 90 días (USD) | Costo por venta (USD) |", "|---|---|---|---|---|---|"]
        for c in r["campanas"][:20]:
            gasto = _n(c["gasto_90d"]) if c.get("gasto_90d") else "—"
            costo = _n(c["costo_por_venta"]) if c.get("costo_por_venta") else "—"
            L.append(f"| {c['campana'][:60]} | {c['cuenta'][:40] or '—'} | {c['marca_cuenta'] or '—'} | {c['ventas']} | {gasto} | {costo} |")
    L += ["", "## Cómo leerlo", "",
          "- **Es un piso, no el total.** Solo cuenta leads de formulario (los chats de WhatsApp no se pueden leer por API), "
          "Meta guarda los leads 90 días y no todas las ventas del ERP traen teléfono o mail.",
          "- **«Por nombre»** es una coincidencia probable: todas las palabras del nombre del lead están en el del cliente, "
          "ese nombre no se repite en otra venta y no aparece en más de 3 leads. Los nombres comunes quedan afuera.",
          "- **Qué tan bien anda:** contra el cruce hecho a mano de Soueast (septiembre, 39 ventas, 03-10-2026) encontró 6 de "
          "las 13 ventas que habían venido de una campaña de Meta y marcó 3 que a mano no aparecían. Con teléfono o mail en el "
          "ERP la coincidencia es casi segura.",
          "- **Costo por venta** = gasto de la campaña en los últimos 90 días ÷ ventas que salieron de sus leads. Sirve para "
          "comparar campañas entre sí, no como costo exacto.",
          "- **Bitrix:** muchas de estas ventas figuran como «Prospecto del Asesor». En el cruce a mano de Soueast de "
          "septiembre, 12 de 15 ventas que vinieron de Meta estaban cargadas así. Si el origen se carga bien, este número sube.", "",
          "Relacionado: [[📘 Manual Buyer Persona#4.6 Que el algoritmo aprenda de las ventas|Manual, 4.6]] · datos en "
          "`output/raw/ventas_meta_<fecha>.json`."]
    return "\n".join(L) + "\n"
