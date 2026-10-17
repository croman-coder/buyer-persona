#!/usr/bin/env python3
"""Crea en Meta la lista de compradores reales de una marca (mail y teléfono del ERP) y su público similar en Paraguay.

Para qué: buscar en Meta gente parecida a quien ya compró, en vez de pautar solo a público frío.

Limpieza («fino», pedido de Croman del 14-10-2026). El ERP trae muchos contactos que NO son del comprador:
- ventas a concesionarios (`Tipo Cliente` = Concesionario);
- mails de la propia Santa Rosa o de Nipon (en Mitsubishi, 524 de 525 ventas tenían el contacto de Nipon);
- mails de relleno («sin correo», «no tiene»…);
- mails o teléfonos que se repiten en 3 ventas o más de TODA la base: son de la empresa, de un vendedor o de relleno
  (en Jetour, un mismo teléfono aparecía en 1.146 ventas).
Después se une a cada persona por mail o teléfono, para no contarla dos veces.

Privacidad (reglas del proyecto):
- Mails y teléfonos se normalizan y se cifran con SHA-256 **en memoria**. No se escriben a disco, no se imprimen y no quedan
  en el vault: la nota guarda solo cuántos, por qué se descartaron, de qué período y los IDs de los públicos.
- Subir una lista necesita el OK de Croman. Sin `--subir` el script solo cuenta y no escribe nada en Meta.
- Mitsubishi está bloqueada: su base tiene los contactos de Nipon.
- Antes de subir se confirma que la cuenta de destino es de la marca (por su nombre en Meta).

Uso:
    venv/bin/python3 scripts/publico_compradores.py --marca Jetour --cuenta act_494721666377008            # solo cuenta
    venv/bin/python3 scripts/publico_compradores.py --marca Jetour --cuenta act_494721666377008 --subir    # crea los públicos
    venv/bin/python3 scripts/publico_compradores.py --marca Jetour --cuenta act_… --similar <id de la lista>  # solo el similar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
import warnings
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
VENTAS = ROOT / "data" / "fuentes" / "ventas_unificadas.xlsx"
NOTA = ROOT / "Buyer Persona" / "Campañas" / "🎯 Públicos de compradores (listas de clientes).md"
API = "https://graph.facebook.com/v21.0"

BLOQUEADAS = {"MITSUBISHI": "su base de ventas tiene los contactos de Nipon"}
DOMINIOS_FUERA = ("santarosa.com.py", "nipon.com.py")
RELLENO = re.compile(r"^(sin|no|ninguno|nn|x+|a+|test|prueba)[^@]*@|notiene|sincorreo|nomail|correo@correo")
MAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")
MAX_VENTAS_POR_CONTACTO = 2      # con 3 o más ventas en toda la base, el contacto no es de un comprador


def normalizar_mail(valor: Any) -> str | None:
    """Como pide Meta: sin espacios y en minúsculas. None si no parece un mail."""
    m = unicodedata.normalize("NFKC", str(valor or "")).strip().lower()
    return m if MAIL_RE.match(m) else None


def normalizar_telefonos(valor: Any) -> list[str]:
    """Teléfonos de Paraguay con código de país y sin «+» (595…), como pide Meta. Una celda puede traer varios."""
    out: list[str] = []
    for parte in re.split(r"//|/|,|;|\|| y ", str(valor or "")):
        d = re.sub(r"\D", "", parte)
        if d.startswith("595"):
            pass
        elif d.startswith("0") and len(d) >= 9:      # 0981 000 000 (celular) o 021 000 000 (fijo)
            d = "595" + d[1:]
        elif len(d) == 9 and d.startswith("9"):       # 981 000 000
            d = "595" + d
        else:
            continue
        if 11 <= len(d) <= 12 and d not in out:
            out.append(d)
    return out


def sha256(v: str) -> str:
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def limpiar(filas: list[dict[str, Any]], marca: str) -> dict[str, Any]:
    """
    Compradores reales de la marca a partir de las filas del ERP (todas las marcas: la repetición se mide en toda la base).
    Devuelve las personas (mails y teléfonos limpios, en claro, solo en memoria), los motivos de descarte y el período.
    """
    if marca.upper() in BLOQUEADAS:
        raise SystemExit(f"{marca}: no se puede usar para públicos, {BLOQUEADAS[marca.upper()]}.")
    norm = [(f, normalizar_mail(f.get("E-Mail")), normalizar_telefonos(f.get("Teléfonos"))) for f in filas]
    veces_mail = Counter(m for _, m, _ in norm if m)
    veces_tel = Counter(t for _, _, ts in norm for t in ts)
    motivos: Counter = Counter()
    ventas: list[tuple[str | None, list[str], Any]] = []
    total = 0
    for f, m, ts in norm:
        if str(f.get("Marca") or "").strip().upper() != marca.upper():
            continue
        total += 1
        if not (m or ts):
            continue
        if str(f.get("Tipo Cliente") or "").strip().lower() == "concesionario":
            motivos["venta a un concesionario"] += 1
            continue
        if m and m.split("@")[1] in DOMINIOS_FUERA:
            motivos["mail de Santa Rosa o de Nipon"] += 1
            m = None
        elif m and RELLENO.search(m):
            motivos["mail de relleno"] += 1
            m = None
        elif m and veces_mail[m] > MAX_VENTAS_POR_CONTACTO:
            motivos["mail repetido en 3 ventas o más"] += 1
            m = None
        limpios = [t for t in ts if veces_tel[t] <= MAX_VENTAS_POR_CONTACTO]
        if len(limpios) < len(ts):
            motivos["teléfono repetido en 3 ventas o más"] += 1
        if not (m or limpios):
            motivos["venta sin ningún contacto limpio"] += 1
            continue
        ventas.append((m, limpios, f.get("Fecha")))

    # una persona = ventas que comparten mail o teléfono
    padre = list(range(len(ventas)))

    def raiz(i: int) -> int:
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    visto: dict[tuple[str, str], int] = {}
    for i, (m, ts, _) in enumerate(ventas):
        for k in ([("m", m)] if m else []) + [("t", t) for t in ts]:
            if k in visto:
                padre[raiz(i)] = raiz(visto[k])
            else:
                visto[k] = i
    personas: dict[int, dict[str, list[str]]] = {}
    for i, (m, ts, _) in enumerate(ventas):
        p = personas.setdefault(raiz(i), {"mails": [], "telefonos": []})
        if m and m not in p["mails"]:
            p["mails"].append(m)
        p["telefonos"] += [t for t in ts if t not in p["telefonos"]]
    fechas = sorted(str(f)[:10] for _, _, f in ventas if f is not None and str(f)[:4].isdigit())
    return {"ventas": total, "ventas_limpias": len(ventas), "personas": list(personas.values()), "motivos": dict(motivos),
            "desde": fechas[0] if fechas else "—", "hasta": fechas[-1] if fechas else "—",
            "por_anio": dict(sorted(Counter(f[:4] for f in fechas).items()))}


def filas_para_meta(personas: list[dict[str, list[str]]]) -> list[list[str]]:
    """Una fila por persona con mail y teléfono cifrados (multi-clave de Meta); los teléfonos extra van en filas aparte."""
    out = []
    for p in personas:
        mails, tels = [sha256(m) for m in p["mails"]], [sha256(t) for t in p["telefonos"]]
        out.append([mails[0] if mails else "", tels[0] if tels else ""])
        out += [[m, ""] for m in mails[1:]] + [["", t] for t in tels[1:]]
    return out


def leer_erp() -> list[dict[str, Any]]:
    import pandas as pd
    warnings.filterwarnings("ignore")
    df = pd.read_excel(VENTAS, sheet_name="Datos", header=2, dtype=str)
    return df[["Fecha", "Marca", "Tipo Cliente", "E-Mail", "Teléfonos"]].where(df.notna(), None).to_dict("records")


def _meta(metodo: str, ruta: str, token: str, datos: dict[str, Any] | None = None) -> dict[str, Any]:
    import requests
    if metodo == "GET":
        r = requests.get(f"{API}/{ruta}", params={**(datos or {}), "access_token": token}, timeout=60)
    else:
        r = requests.post(f"{API}/{ruta}", data={**(datos or {}), "access_token": token}, timeout=180)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"Meta respondió: {j['error'].get('message', j['error'])}")
    return j


def crear_similar(marca: str, cuenta: str, token: str, lista_id: str) -> tuple[str | None, str | None]:
    try:
        sim = _meta("POST", f"{cuenta}/customaudiences", token, {
            "name": f"Similar 1 % PY · Compradores {marca} · Buyer Persona", "subtype": "LOOKALIKE",
            "origin_audience_id": lista_id, "lookalike_spec": json.dumps({"ratio": 0.01, "country": "PY"})})
        return sim["id"], None
    except RuntimeError as e:   # la lista recién subida a veces todavía no se puede usar de origen
        return None, str(e)


def subir(marca: str, cuenta: str, token: str, c: dict[str, Any]) -> dict[str, Any]:
    cta = _meta("GET", cuenta, token, {"fields": "name,account_status"})
    if marca.lower() not in str(cta.get("name", "")).lower():
        raise SystemExit(f"La cuenta {cuenta} se llama «{cta.get('name')}»: no es de {marca}. No se sube nada.")
    lista = _meta("POST", f"{cuenta}/customaudiences", token, {
        "name": f"Compradores {marca} (ERP {c['desde'][:7]} a {c['hasta'][:7]}) · Buyer Persona",
        "subtype": "CUSTOM", "customer_file_source": "USER_PROVIDED_ONLY",
        "description": (f"{len(c['personas'])} compradores reales de {marca} del ERP (sin concesionarios, sin contactos de "
                        f"Santa Rosa ni repetidos). Subida el {date.today().isoformat()} con OK de Croman.")})
    lista_id = lista["id"]
    filas = filas_para_meta(c["personas"])
    carga = {"recibidos": 0, "invalidos": 0}
    for i in range(0, len(filas), 10000):
        r = _meta("POST", f"{lista_id}/users", token,
                  {"payload": json.dumps({"schema": ["EMAIL", "PHONE"], "data": filas[i:i + 10000]})})
        carga["recibidos"] += int(r.get("num_received", 0))
        carga["invalidos"] += int(r.get("num_invalid_entries", 0))
    similar_id, similar_error = crear_similar(marca, cuenta, token, lista_id)
    return {"lista_id": lista_id, "carga": carga, "filas": len(filas), "similar_id": similar_id, "similar_error": similar_error,
            "cuenta_nombre": cta.get("name")}


def anotar(marca: str, cuenta: str, c: dict[str, Any], r: dict[str, Any]) -> None:
    """Registro en el vault, sin datos de personas."""
    if not NOTA.exists():
        NOTA.write_text("\n".join([
            "---", "type: publicos", "tags: [meta-ads, publicos, lista-de-clientes, uso-interno]", "---",
            "# 🎯 Públicos de compradores (listas de clientes)", "",
            "> [!info] Qué es",
            "> Listas de **compradores reales** del ERP subidas a Meta (mail y teléfono **cifrados**: Meta no los ve en claro) y su "
            "**público similar** en Paraguay: gente parecida a quien ya compró. Se arman con `scripts/publico_compradores.py`.",
            "> Ningún dato de personas queda en este vault: solo cuántos, por qué se descartaron, de qué período y los IDs.", "",
            "> [!warning] Reglas",
            "> - Subir una lista necesita el OK de Croman. **Mitsubishi no se usa**: su base tiene los contactos de Nipon.",
            "> - Se descartan las ventas a concesionarios, los mails de Santa Rosa y Nipon, los de relleno y todo mail o teléfono "
            "que aparezca en 3 ventas o más de la base (es de la empresa, de un vendedor o de relleno).",
            "> - Usar el similar como **un conjunto aparte**, con su propio presupuesto, para compararlo con el público frío.",
            "> - Desde mayo 2026 el ERP casi no trae mail ni teléfono: hasta que vuelvan esas columnas, la lista no suma compradores nuevos.",
            "", "## Registro", ""]) + "\n", encoding="utf-8")
    texto = NOTA.read_text(encoding="utf-8")
    descartes = " · ".join(f"{k}: {v}" for k, v in sorted(c["motivos"].items(), key=lambda kv: -kv[1]))
    similar = f"`{r['similar_id']}`" if r["similar_id"] else f"pendiente ({r['similar_error']}). Reintentar con `--similar {r['lista_id']}`"
    bloque = [f"### {marca} · {date.today().strftime('%d-%m-%Y')}", "",
              "| | |", "|---|---|",
              f"| Cuenta | {r['cuenta_nombre']} (`{cuenta}`) |",
              f"| Compradores reales | **{len(c['personas'])} personas** de {c['ventas_limpias']} ventas limpias ({c['ventas']} ventas de la marca en la base) |",
              f"| Período de las compras | {c['desde']} → {c['hasta']} · por año: {', '.join(f'{a}: {n}' for a, n in c['por_anio'].items())} |",
              f"| Descartados (ventas) | {descartes} |",
              f"| Cargados en Meta | {r['filas']} filas · Meta las recibió: {r['carga']['recibidos']} · inválidas: {r['carga']['invalidos']} |",
              f"| Lista de compradores | `{r['lista_id']}` |",
              f"| Similar 1 % Paraguay | {similar} |",
              "| Estado | Creados, **sin usar en ninguna campaña** todavía. Meta tarda unas horas en calcular el tamaño |", ""]
    NOTA.write_text(texto.rstrip("\n") + "\n\n" + "\n".join(bloque) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marca", required=True)
    ap.add_argument("--cuenta", required=True, help="cuenta publicitaria de la marca (act_…)")
    ap.add_argument("--subir", action="store_true", help="crea los públicos en Meta (necesita el OK de Croman)")
    ap.add_argument("--similar", default="", help="solo crea el similar de una lista ya subida (su id)")
    a = ap.parse_args()
    c = limpiar(leer_erp(), a.marca)
    print(f"{a.marca}: {len(c['personas'])} personas de {c['ventas_limpias']} ventas limpias ({c['ventas']} ventas en la base) · "
          f"{c['desde']} → {c['hasta']} · por año {c['por_anio']}")
    print("descartes:", c["motivos"])
    if not (a.subir or a.similar):
        print("Sin --subir: solo se contó. No se escribió nada en Meta.")
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    token = os.environ.get("META_ADS_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Falta META_ADS_ACCESS_TOKEN en .env")
    if a.similar:
        sid, err = crear_similar(a.marca, a.cuenta, token, a.similar)
        print(f"similar: {sid or 'pendiente: ' + str(err)}")
        return
    r = subir(a.marca, a.cuenta, token, c)
    print(f"lista {r['lista_id']} · filas {r['filas']} · carga {r['carga']} · similar {r['similar_id'] or 'pendiente: ' + str(r['similar_error'])}")
    anotar(a.marca, a.cuenta, c, r)
    print(f"nota: {NOTA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
