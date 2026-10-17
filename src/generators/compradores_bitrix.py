"""
Compradores reales de Bitrix que vinieron de un lead de Meta, para afinar el Buyer Persona con quien COMPRA y no solo
con quien hace clic o deja sus datos.

Fuente: la tabla ``ventas_origen`` de la base del tablero de Meta (contenedor ``bitrix-supabase-db``), que llena
``api/_ventas-origen.js`` del tablero: los negocios **ganados** de los últimos 365 días y **todos los que están hoy en
Facturación** de los pipelines «<MARCA> Ventas» («esos ya son los que se van a cerrar», Croman, 14-10-2026), cruzados
con el lead de Meta por teléfono o mail.

- Solo cuentan los cruces **seguros** (``directa``, ``telefono``, ``email``); los ``posible`` se informan aparte.
- No se leen nombres de clientes ni de asesores: solo etapa, marca, anuncio, plataforma, tipo de cuenta, campaña y días.
- **Edad y género son estimados**: Meta no da la edad de cada lead, así que cada comprador reparte su peso según los
  contactos por edad y género de SU anuncio (desglose por anuncio del día). Se muestran por marca solo con
  ``MIN_COMPRADORES_PERFIL`` compradores o más.
- No usar ``roi_embudo.deal_id`` para esto: los asesores crean el negocio aparte y el lead casi nunca se convierte.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter, defaultdict
from typing import Any, Callable

SEGURAS = ("directa", "telefono", "email")
EDADES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
MIN_COMPRADORES_PERFIL = 15
PLATAFORMAS = {"fb": "Facebook", "ig": "Instagram", "an": "Audience Network", "msg": "Messenger"}
CUENTAS = {"madre": "Cuenta madre", "asesor": "Cuentas de asesores"}

SQL = """SELECT coalesce(json_agg(json_build_object(
  'etapa', etapa, 'brand', brand, 'certeza', certeza, 'ad_id', origen->>'ad_id', 'platform', origen->>'platform',
  'account_type', origen->>'account_type', 'campaign', origen->>'campaign_name', 'dias', dias_a_venta, 'fecha', fecha)), '[]')
FROM public.ventas_origen;"""


def leer(ejecutar: Callable[..., Any] | None = None) -> list[dict[str, Any]] | None:
    """Filas de ``ventas_origen`` sin datos de personas. None donde no está la base (fuera del servidor)."""
    if ejecutar is None:
        if shutil.which("docker") is None:
            return None
        ejecutar = subprocess.run
    from src.exporters.tablero_meta import _psql
    return json.loads(_psql(ejecutar, SQL).strip() or "[]")


def _mediana(xs: list[float]) -> float | None:
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return float(xs[m]) if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _percentil(xs: list[float], p: float) -> float | None:
    xs = sorted(xs)
    return float(xs[min(len(xs) - 1, int(len(xs) * p))]) if xs else None


def _por_anuncio(age_gender_ad: list[dict[str, Any]]) -> tuple[dict[str, Counter], dict[str, Counter]]:
    edad: dict[str, Counter] = defaultdict(Counter)
    genero: dict[str, Counter] = defaultdict(Counter)
    for r in age_gender_ad or []:
        ad, c = str(r.get("ad_id") or ""), float(r.get("contactos") or 0)
        if not ad or not c:
            continue
        if r.get("age") in EDADES:
            edad[ad][r["age"]] += c
        if r.get("gender") in ("male", "female"):
            genero[ad]["Masculino" if r["gender"] == "male" else "Femenino"] += c
    return edad, genero


def _bloque(filas: list[dict[str, Any]], edad_ad: dict[str, Counter], gen_ad: dict[str, Counter]) -> dict[str, Any]:
    seg = [f for f in filas if f.get("certeza") in SEGURAS]
    dias = [float(f["dias"]) for f in seg if f.get("dias") is not None]
    out: dict[str, Any] = {
        "negocios": len(filas),
        "ganados": sum(f.get("etapa") == "concretada" for f in filas),
        "facturacion": sum(f.get("etapa") == "facturacion" for f in filas),
        "con_meta": len(seg),
        "con_meta_ganados": sum(f.get("etapa") == "concretada" for f in seg),
        "con_meta_facturacion": sum(f.get("etapa") == "facturacion" for f in seg),
        "posibles": sum(f.get("certeza") == "posible" for f in filas),
        "plataforma": dict(Counter(PLATAFORMAS.get(str(f.get("platform") or ""), "Otra") for f in seg).most_common()),
        "cuenta": dict(Counter(CUENTAS.get(str(f.get("account_type") or ""), "Otra") for f in seg).most_common()),
        "dias_mediana": _mediana(dias), "dias_p75": _percentil(dias, 0.75),
        "campanas": dict(Counter(f.get("campaign") or "—" for f in seg).most_common(5)),
        "edad_estimada": None, "genero_estimado": None, "con_anuncio": 0,
    }
    edad, gen, usados = Counter(), Counter(), 0
    for f in seg:
        a, g = edad_ad.get(str(f.get("ad_id") or "")), gen_ad.get(str(f.get("ad_id") or ""))
        if not a:
            continue
        usados += 1
        t = sum(a.values())
        for e in EDADES:
            edad[e] += a[e] / t
        if g:
            tg = sum(g.values())
            for k, v in g.items():
                gen[k] += v / tg
    out["con_anuncio"] = usados
    if usados:
        te = sum(edad.values())
        out["edad_estimada"] = {e: round(100 * edad[e] / te, 1) for e in EDADES}
        if gen:
            tg = sum(gen.values())
            out["genero_estimado"] = {k: round(100 * v / tg, 1) for k, v in gen.most_common()}
    return out


def resumir(filas: list[dict[str, Any]], age_gender_ad: list[dict[str, Any]]) -> dict[str, Any]:
    """Totales y por marca (marca en mayúsculas, como en Bitrix y el tablero)."""
    edad_ad, gen_ad = _por_anuncio(age_gender_ad)
    por_marca: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in filas or []:
        por_marca[str(f.get("brand") or "").strip().upper() or "SIN MARCA"].append(f)
    fechas = sorted(str(f.get("fecha"))[:10] for f in filas or [] if f.get("fecha"))
    return {"total": _bloque(filas or [], edad_ad, gen_ad),
            "marcas": {m: _bloque(fs, edad_ad, gen_ad) for m, fs in sorted(por_marca.items())},
            "desde": fechas[0] if fechas else None, "hasta": fechas[-1] if fechas else None,
            "min_perfil": MIN_COMPRADORES_PERFIL}


def edad_top(b: dict[str, Any]) -> str | None:
    e = b.get("edad_estimada") or {}
    return max(e, key=e.get) if e else None


def _pct(n: float, d: float) -> str:
    return f"{100 * n / d:.0f} %" if d else "—"


def reparto(d: dict[str, Any]) -> str:
    return " · ".join(f"{k} {v}" for k, v in d.items()) or "—"


def edad_txt(b: dict[str, Any]) -> str:
    e = b.get("edad_estimada") or {}
    return " · ".join(f"{k}: {v:.0f} %" for k, v in sorted(e.items(), key=lambda kv: -kv[1])[:4]) if e else "—"


def genero_txt(b: dict[str, Any]) -> str:
    return reparto({k: f"{v:.0f} %" for k, v in (b.get("genero_estimado") or {}).items()})


def dias_txt(b: dict[str, Any]) -> str:
    if b.get("dias_mediana") is None:
        return "sin datos"
    return f"mediana de {b['dias_mediana']:.0f} días; el 75 % compra antes de los {b['dias_p75']:.0f}"


def nombre_marca(m: str) -> str:
    return m if m in ("GWM", "JAC", "JMEV") else m.title()


def nota(r: dict[str, Any], fecha: str) -> str:
    """Nota de sistema con todas las marcas (sin datos de personas)."""
    t = r["total"]
    L = ["---", "type: compradores-bitrix", f"generado: '{fecha}'", "tags: [bitrix, ventas, meta-ads, buyer-persona]", "---",
         "# 🧾 Compradores reales (Bitrix)", "",
         "> [!info] Qué es y de dónde sale",
         "> - **Compradores** = negocios **ganados** de los pipelines «<Marca> Ventas» de Bitrix en los últimos 365 días, más **todos los "
         "que están hoy en Facturación** (ya son ventas que se van a cerrar).",
         "> - **Con lead de Meta** = el tablero de Meta los unió a un lead de Meta por teléfono, mail o directamente (cruce seguro). "
         "Los «posibles» se cuentan aparte y no entran en los números.",
         "> - **Edad y género son estimados**: Meta no da la edad de cada lead, así que cada comprador toma la edad y el género de quienes "
         "contactaron por **su** anuncio. Sirve para ver hacia dónde se corre el perfil, no como dato exacto.",
         "> - Sin nombres de clientes ni de asesores. Fuente: tabla `ventas_origen` del tablero de Meta.", "",
         f"Negocios del **{r.get('desde') or '—'}** al **{r.get('hasta') or '—'}**.", "",
         "## Todas las marcas", "",
         f"- **{t['negocios']} negocios**: {t['ganados']} ganados y {t['facturacion']} en Facturación.",
         f"- **{t['con_meta']} vinieron de un lead de Meta** ({_pct(t['con_meta'], t['negocios'])}): {t['con_meta_ganados']} ganados y "
         f"{t['con_meta_facturacion']} en Facturación. Otros {t['posibles']} son posibles, sin confirmar.",
         f"- **Plataforma del lead:** {reparto(t['plataforma'])}. **Cuenta:** {reparto(t['cuenta'])}.",
         f"- **Del lead a la venta:** {dias_txt(t)}. En ventas, una campaña se juzga recién a las ~6 semanas.",
         f"- **Edad estimada:** {edad_txt(t)}. **Género estimado:** {genero_txt(t)}.", "",
         "## Por marca", "",
         "| Marca | Negocios (ganados + Facturación) | Con lead de Meta | Plataforma | Cuenta | Días (mediana) | Edad estimada |",
         "|---|---|---|---|---|---|---|"]
    for m, b in sorted(r["marcas"].items(), key=lambda kv: -kv[1]["con_meta"]):
        top = edad_top(b)
        edad = (f"{top} ({(b['edad_estimada'] or {}).get(top, 0):.0f} %)" if b["con_meta"] >= r["min_perfil"] and top
                else f"pocos ({b['con_meta']} de {r['min_perfil']})")
        dias = f"{b['dias_mediana']:.0f}" if b.get("dias_mediana") is not None else "—"
        L.append(f"| {nombre_marca(m)} | {b['negocios']} ({b['ganados']} + {b['facturacion']}) | {b['con_meta']} "
                 f"({_pct(b['con_meta'], b['negocios'])}) | {reparto(b['plataforma'])} | {reparto(b['cuenta'])} | {dias} | {edad} |")
    L += ["", "## Cómo usarlo", "",
          "- La edad, el género y la plataforma de quien **compra** pesan más que los de quien hace clic o deja sus datos.",
          f"- Una marca con menos de {r['min_perfil']} compradores con lead de Meta todavía no tiene perfil propio de compra: se mira el de todas las marcas.",
          "- Cuantos más negocios se carguen bien en Bitrix (y pasen por Facturación), más fino queda este perfil.", ""]
    return "\n".join(L)
