#!/usr/bin/env python3
"""Vuelca los exports de Tecnom de esta PC a Obsidian como AGREGADOS (sin datos personales).

Lee los Excel/CSV que se bajaron de Tecnom (consultas = leads) y escribe:
  - data/fuentes/tecnom_agregado.csv           marca, anio_mes, origen, campana, leads, ventas
  - Buyer Persona/CRM/Tecnom/Tecnom - <Marca>.md   leads/ventas por año, origen y mes, con las ferias aparte
  - Buyer Persona/CRM/Tecnom/Tecnom - Indice.md    qué cubre cada fuente y qué falta

Nunca guarda nombre, teléfono, email ni documento. Solo cuenta filas.
Uso: python3 scripts/tecnom_a_obsidian.py
"""
from __future__ import annotations

import re
import warnings
from datetime import date
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

HOME = Path.home()
ESC = HOME / "Escritorio"
BASE = ESC / "BITRIX/BITRIX TECNOM/BASE TECNOM"
RAIZ = ESC / "BUYER PERSONA"
VAULT = RAIZ / "Buyer Persona" / "CRM" / "Tecnom"
CSV_SALIDA = RAIZ / "data" / "fuentes" / "tecnom_agregado.csv"

# Origen o campaña que parece feria, expo o evento (se separan en una tabla propia)
EVENTO = re.compile(r"feria|cadam|expo|shopping|evento|sal[oó]n|lanzamiento|motorshow|motor show", re.I)

# (marca, ruta, tipo). 'marca' puede ser una función de la fila cuando el archivo mezcla marcas.
FUENTES = [
    ("RENAULT", BASE / "RENAULT/Total - Total(1_1_2023 - 16_2_2026).xlsx", "tecnom"),
    ("MITSUBISHI", BASE / "MITSIBUSHI/Total - Total(1_1_2023 - 7_3_2026).xlsx", "tecnom"),
    ("LEAPMOTOR/JMEV", ESC / "PC SRPY/PC/DESCARGAS/Total - Total(22_3_2022 - 28_3_2026).xlsx", "tecnom"),
    ("JETOUR (tenant)", BASE / "JETOUR/Total - Jetour Tecnom (5_8_2022 - 20_9_2026).csv", "jetour_csv"),
    # 2025 completo de todas las marcas: solo las que no tienen archivo propio
    ("2025", ESC / "PC SRPY/LEADS TOTALES 2025 SRPY.xlsx", "total2025"),
]
MARCAS_2025_QUE_FALTAN = {"GWM", "JAC", "ZEEKR", "SOUEAST"}
JETOUR_VENDIDOS = BASE / "JETOUR/vendidos_jetour_tecnom.csv"


def limpiar(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().fillna("(sin dato)").replace("", "(sin dato)")


def normalizar(df: pd.DataFrame, marca: pd.Series | str, fecha: pd.Series, vendido: pd.Series) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "marca": marca,
            "fecha": pd.to_datetime(fecha, errors="coerce", dayfirst=True),
            "origen": limpiar(df["Origen"]),
            "campana": limpiar(df["Campaña"]),
            "vendido": vendido,
        }
    )
    out = out.dropna(subset=["fecha"])
    out["anio_mes"] = out["fecha"].dt.strftime("%Y-%m")
    return out


def cargar() -> tuple[pd.DataFrame, list[dict]]:
    partes, cobertura = [], []
    for marca, ruta, tipo in FUENTES:
        if not ruta.exists():
            cobertura.append({"fuente": ruta.name, "estado": "NO ENCONTRADO", "filas": 0, "desde": "", "hasta": ""})
            continue
        if tipo == "jetour_csv":
            df = pd.read_csv(ruta, sep=None, engine="python", dtype=str)
            df.columns = [c.replace("﻿", "") for c in df.columns]
            ventas = set()
            if JETOUR_VENDIDOS.exists():
                v = pd.read_csv(JETOUR_VENDIDOS, sep=None, engine="python", dtype=str)
                ventas = set(v.loc[v["fecha_compra"].notna(), "consulta_id"])
            vendido = df["Id Consulta"].isin(ventas)
            fecha = pd.to_datetime(df["Fecha de consulta"], errors="coerce", utc=True).dt.tz_localize(None)
            n = normalizar(df, marca, fecha, vendido)
        else:
            hojas = pd.read_excel(ruta, sheet_name=None, dtype=str)
            df = max(hojas.values(), key=len)  # la hoja grande
            vendido = df["Fecha de Vendido"].notna() & (df["Fecha de Vendido"].astype(str).str.strip() != "")
            if tipo == "total2025":
                df = df[df["MARCA"].isin(MARCAS_2025_QUE_FALTAN)]
                vendido = vendido.loc[df.index]
                n = normalizar(df, df["MARCA"].astype(str).str.upper(), df["Fecha de consulta"], vendido)
            elif marca == "LEAPMOTOR/JMEV":
                nombre = df["Producto"].astype(str).str.contains("jmev", case=False, na=False).map({True: "JMEV", False: "LEAPMOTOR"})
                n = normalizar(df, nombre, df["Fecha de consulta"], vendido)
            else:
                n = normalizar(df, marca.upper(), df["Fecha de consulta"], vendido)
        partes.append(n)
        cobertura.append(
            {"fuente": ruta.name, "estado": "ok", "filas": len(n), "desde": n["fecha"].min().date(), "hasta": n["fecha"].max().date()}
        )
    return pd.concat(partes, ignore_index=True), cobertura


def md_tabla(df: pd.DataFrame) -> str:
    if df.empty:
        return "_sin datos_\n"
    cols = list(df.columns)
    filas = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" if i == 0 else "--:" for i in range(len(cols))) + "|"]
    for _, r in df.iterrows():
        filas.append("| " + " | ".join(f"{v:,}".replace(",", ".") if isinstance(v, int) else str(v) for v in r) + " |")
    return "\n".join(filas) + "\n"


def nota_marca(marca: str, d: pd.DataFrame, hoy: str) -> str:
    d = d.copy()
    d["anio"] = d["fecha"].dt.year
    por_anio = d.groupby("anio").agg(leads=("vendido", "size"), ventas=("vendido", "sum")).reset_index()
    por_anio["ventas"] = por_anio["ventas"].astype(int)
    por_anio["conversion"] = (100 * por_anio["ventas"] / por_anio["leads"]).round(1).astype(str) + "%"
    por_anio["anio"] = por_anio["anio"].astype(str)

    ev = d[d["origen"].str.contains(EVENTO) | d["campana"].str.contains(EVENTO)]
    ev_t = (
        ev.groupby(["origen", "anio_mes"]).agg(leads=("vendido", "size"), ventas=("vendido", "sum")).reset_index().sort_values(["anio_mes", "leads"], ascending=[True, False])
    )
    ev_t["ventas"] = ev_t["ventas"].astype(int)

    orig = d.groupby(["anio", "origen"]).agg(leads=("vendido", "size"), ventas=("vendido", "sum")).reset_index()
    orig["ventas"] = orig["ventas"].astype(int)
    orig["anio"] = orig["anio"].astype(str)
    orig = orig.sort_values(["anio", "leads"], ascending=[True, False]).groupby("anio").head(12)

    camp = d.groupby(["anio_mes", "campana"]).agg(leads=("vendido", "size"), ventas=("vendido", "sum")).reset_index()
    camp["ventas"] = camp["ventas"].astype(int)
    camp = camp.sort_values("leads", ascending=False).head(40).sort_values("anio_mes")

    return f"""---
tipo: tecnom-agregado
marca: {marca}
fuente: exports de Tecnom bajados a mano (consultas = leads)
desde: {d['fecha'].min().date()}
hasta: {d['fecha'].max().date()}
actualizado: {hoy}
tags: [crm, tecnom, leads, ventas, campanas]
---
# Tecnom — {marca}

> Agregados de las consultas (leads) de Tecnom. **Sin nombres ni teléfonos.** Volver al [[Tecnom - Indice|índice]].
> Un lead cuenta como **venta** si Tecnom le puso fecha de vendido. Es la venta que registró el vendedor en el CRM, no la facturación del ERP.

## Por año

{md_tabla(por_anio)}
## Ferias y eventos (por origen y mes)

Origen o campaña que menciona feria, expo, CADAM, shopping, salón o lanzamiento.

{md_tabla(ev_t.rename(columns={"anio_mes": "mes"}))}
## Origen por año (los 12 mayores)

{md_tabla(orig)}
## Campañas con más leads (por mes)

{md_tabla(camp.rename(columns={"anio_mes": "mes"}))}
"""


def main() -> None:
    hoy = date.today().isoformat()
    todo, cobertura = cargar()
    CSV_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    agg = todo.groupby(["marca", "anio_mes", "origen", "campana"]).agg(leads=("vendido", "size"), ventas=("vendido", "sum")).reset_index()
    agg["ventas"] = agg["ventas"].astype(int)
    agg.to_csv(CSV_SALIDA, index=False)

    VAULT.mkdir(parents=True, exist_ok=True)
    for marca, d in todo.groupby("marca"):
        (VAULT / f"Tecnom - {marca}.md").write_text(nota_marca(marca, d, hoy), encoding="utf-8")

    filas = "\n".join(f"| {c['fuente']} | {c['estado']} | {c['filas']:,} | {c['desde']} | {c['hasta']} |".replace(",", ".") for c in cobertura)
    marcas = "\n".join(f"- [[Tecnom - {m}]] — {len(d):,} leads".replace(",", ".") for m, d in todo.groupby("marca"))
    (VAULT / "Tecnom - Indice.md").write_text(
        f"""---
tipo: tecnom-indice
actualizado: {hoy}
tags: [crm, tecnom, indice]
---
# Tecnom — índice de lo que hay en esta PC

Generado por `BUYER PERSONA/scripts/tecnom_a_obsidian.py` (se puede volver a correr cuando se bajen exports nuevos). Datos agregados en `data/fuentes/tecnom_agregado.csv` (marca, mes, origen, campaña, leads, ventas).

## Marcas con datos
{marcas}

## Fuentes leídas
| Archivo | Estado | Filas | Desde | Hasta |
|---|---|--:|---|---|
{filas}

## Lo que NO está (huecos conocidos)
- **Renew (usados) antes de noviembre 2025.** No hay export de Tecnom de Renew de 2024 en esta PC. Los leads de Renew que sí están son de noviembre 2025 (`RENEW (2).xlsx`), y no se volcaron aquí porque ese archivo no trae ventas ni el resto del año. Pedido pendiente: feria CADAM Usados Renew de junio 2024.
- **GWM, JAC, Zeekr y Soueast antes de 2025.** Solo está 2025 completo. El JSON de GWM de Descargas es la lista de usuarios, no de consultas. Soueast tiene exports por vendedor (abril 2024 a abril 2026) bajados en la carpeta `SOUEAST` que no se incluyeron.
- **Ventas por campaña.** La venta es la que cargó el vendedor en Tecnom. La facturación real del ERP no trae el canal de origen (ver [[Ventas Reales - abril 2024 a abril 2026]]).
- Los datos personales de los leads quedan solo en los Excel originales; Obsidian solo tiene conteos.
""",
        encoding="utf-8",
    )
    print(f"{len(todo):,} consultas -> {len(agg):,} filas agregadas".replace(",", "."))
    print(f"Notas en {VAULT}")


if __name__ == "__main__":
    main()
