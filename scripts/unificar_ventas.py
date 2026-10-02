#!/usr/bin/env python3
"""
Unifica las dos fuentes de ventas del ERP en un solo archivo con el layout
de FacturacionUnidades (hoja Datos, encabezado en la fila 3), para que el
pipeline, las semillas de audiencias y la base de recompra lean UNA base:

- data/fuentes/ventas_bi_2018_2026.xlsx  (REPORTE DE VENTAS_MARCAS_BI, hoja
  Datos): 2018-07 → hoy, sin email/teléfono.
- ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx: 2024-04 → 2026-04, con
  E-Mail/Teléfonos/Marca Ret./Fuente/Medio.

Reglas:
- Notas de crédito (Total = -1) anulan la factura anterior del mismo VIN:
  se netean por VIN y queda la última factura vigente.
- Por VIN manda la fila del BI (más reciente); del FU se copian los campos
  que el BI no tiene (contacto, retoma, fuente/medio).
- Salida: data/fuentes/ventas_unificadas.xlsx (fuera de git: tiene PII).

Uso: venv/bin/python3 scripts/unificar_ventas.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
BI = ROOT / "data" / "fuentes" / "ventas_bi_2018_2026.xlsx"
FU = ROOT / "ENCUESTA AGESTA" / "FacturacionUnidades-7343.xlsx"
OUT = ROOT / "data" / "fuentes" / "ventas_unificadas.xlsx"

FU_ONLY = ["E-Mail", "Teléfonos", "Local de Vendedor", "Imesi", "IVA Ret.", "Observaciones", "Marca Ret.",
           "Modelo/Versión", "Matrícula", "Nro. Unidad", "Precio", "Medio", "Fuente", "Ver"]


def _net_by_vin(df: pd.DataFrame) -> pd.DataFrame:
    """Quita notas de crédito y la factura que anulan (misma VIN, anterior)."""
    df = df.copy()
    df["_vin"] = df["V.I.N."].astype(str).str.strip()
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    df = df.sort_values(["_vin", "Fecha"])
    keep = []
    for vin, g in df.groupby("_vin", sort=False):
        if vin in ("", "nan"):
            keep.extend(g.index[g["Total"] > 0].tolist())
            continue
        pos = g.index[g["Total"] > 0].tolist()
        neg = int((g["Total"] < 0).sum())
        keep.extend(pos[neg:] if neg < len(pos) else [])   # cada NC anula la factura más vieja
    return df.loc[sorted(keep)].drop(columns="_vin")


def main() -> None:
    bi = pd.read_excel(BI, sheet_name="Datos")
    bi["Fecha"] = pd.to_datetime(bi["Fecha"], errors="coerce")
    bi = bi.dropna(subset=["Fecha", "Marca"])
    bi = bi.drop(columns=[c for c in bi.columns if str(c).startswith("Unnamed") or c == "Año2"], errors="ignore")
    bi["Marca"] = bi["Marca"].astype(str).str.replace("\xa0", " ").str.strip()

    fu = pd.read_excel(FU, sheet_name="Datos", header=2)
    fu["Fecha"] = pd.to_datetime(fu["Fecha"], errors="coerce")
    fu = fu.dropna(subset=["Fecha", "Marca"])
    fu = fu.drop(columns=[c for c in fu.columns if str(c).startswith("Unnamed") or c in ("Año.1", "V.I.N..1", "Fecha.1")], errors="ignore")
    fu_cols = list(fu.columns)

    bi_n, fu_n = _net_by_vin(bi), _net_by_vin(fu)
    bi_n["_vin"] = bi_n["V.I.N."].astype(str).str.strip()
    fu_n["_vin"] = fu_n["V.I.N."].astype(str).str.strip()

    # contacto/retoma/fuente del FU por VIN
    extra = fu_n.drop_duplicates("_vin", keep="last").set_index("_vin")[[c for c in FU_ONLY if c in fu_n.columns]]
    merged = bi_n.merge(extra, left_on="_vin", right_index=True, how="left")

    # VINs que solo están en el FU (pocos)
    only_fu = fu_n[~fu_n["_vin"].isin(set(bi_n["_vin"]))]
    out = pd.concat([merged, only_fu], ignore_index=True)
    out = out.drop(columns="_vin").sort_values("Fecha")
    out = out.reindex(columns=[c for c in fu_cols if c in out.columns] + [c for c in out.columns if c not in fu_cols])
    out["Fecha"] = out["Fecha"].dt.strftime("%Y-%m-%d")

    # Layout FU: 2 filas de título + encabezado en la fila 3
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        pd.DataFrame([["EMPRESA: SANTA ROSA PARAGUAY S.A. — ventas unificadas (BI 2018→hoy + FacturacionUnidades)"],
                      [f"Fechas Desde/Hasta : {out['Fecha'].min()} - {out['Fecha'].max()}  Moneda Informe : DOLARES"]]
                     ).to_excel(xw, sheet_name="Datos", index=False, header=False, startrow=0)
        out.to_excel(xw, sheet_name="Datos", index=False, startrow=2)

    years = pd.to_datetime(out["Fecha"]).dt.year.value_counts().sort_index().to_dict()
    contact = out["E-Mail"].notna().mean() if "E-Mail" in out else 0
    print(f"BI: {len(bi)} filas → {len(bi_n)} netas · FU: {len(fu)} → {len(fu_n)} · solo FU: {len(only_fu)}")
    print(f"Unificado: {len(out)} unidades, {out['Fecha'].min()} → {out['Fecha'].max()}, con email {contact:.0%}")
    print("Por año:", years)
    print("Salida:", OUT.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
