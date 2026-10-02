"""
Fuentes complementarias del negocio (Excel en data/fuentes/, fuera de git):

- stock_unidades_nuevas.xlsx   → stock real por marca/modelo (en stock, en
  viaje, propuestas, días promedio en stock).
- acciones_comerciales_*.xlsx  → por versión: PVP, descuento vigente,
  promedio de ventas, stock; se agrega a nivel modelo (sin márgenes).
- objetivos_ventas.xlsx        → objetivo mensual de unidades y facturación
  por marca (budget), y avance real del mes/año desde las ventas unificadas.
- negociacion_semanal_*.xlsx   → resumen semanal de la fuerza de ventas
  por marca (promesa, venta MTD, leads del mes, negociaciones, perdidas),
  SIN nombres de vendedores.

Todo sale agregado; nada de esto lleva datos personales al vault.
"""
from __future__ import annotations

import glob
import logging
import re
import warnings
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.connectors.erp_normalizer import BRAND_MAP, _match_model

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

SHEET_BRAND = {"JETOUR": "Jetour", "GWM": "GWM", "JAC": "JAC", "RENAULT": "Renault", "LEAP": "Leapmotor",
               "SOUEAST": "Soueast", "XPENG": "XPeng", "JMEV": "JMEV", "ZEEKR": "Zeekr", "MMC": "Mitsubishi",
               "MITSUBISHI": "Mitsubishi", "GREATWALL": "GWM", "LEAP & JMEV": "Leapmotor", "RENEW": "Renew"}
BUDGET_BRAND = {"GREATWALL": "GWM", "JAC": "JAC", "JETOUR": "Jetour", "LEAP Y JMEV": "Leapmotor", "MITSUBISHI": "Mitsubishi",
                "RENAULT": "Renault", "RENEW": "Renew", "SOUEAST": "Soueast", "ZEEKR": "Zeekr", "XPENG": "XPeng"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _latest(pattern: str) -> Path | None:
    files = sorted(glob.glob(pattern))
    return Path(files[-1]) if files else None


def _num(x) -> float:
    try:
        v = float(x)
        return 0.0 if v != v else v   # NaN → 0
    except (TypeError, ValueError):
        return 0.0


# ----------------------------------------------------------------------------- stock
def load_stock(path: Path, today: date) -> dict[str, Any]:
    df = pd.read_excel(path, sheet_name="Datos", header=2)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Marca"])
    df["marca"] = df["Marca"].astype(str).str.upper().str.strip().map(BRAND_MAP)
    df = df.dropna(subset=["marca"])
    df["modelo"] = [_match_model(b, m, v) for b, m, v in zip(df["marca"], df["Modelo"].fillna(""), df["Version"].fillna(""))]
    df["estado"] = df["Estado"].astype(str).str.strip().str.upper()
    df["situacion"] = df["Situación"].astype(str).str.strip().str.upper()
    df["fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["dias"] = (pd.Timestamp(today) - df["fecha"]).dt.days

    by_model: dict[str, dict[str, Any]] = {}
    by_brand: dict[str, dict[str, Any]] = {}
    for key, g in df.groupby("modelo"):
        d = {
            "brand": g["marca"].iloc[0],
            "total": int(len(g)),
            "en_viaje": int((g["estado"] == "EN VIAJE").sum()),
            "disponible": int(g["estado"].isin(["DESPACHADO", "SIN DESPACHAR", "STOCK CDE", "DISPONIBLE"]).sum()),
            "propuesta": int((g["situacion"] == "PROPUESTA").sum()),
            "test_drive": int((g["estado"] == "TEST DRIVE").sum()),
            "dias_promedio": int(g["dias"].dropna().mean()) if g["dias"].notna().any() else None,
        }
        by_model[key] = d
        b = by_brand.setdefault(d["brand"], {"total": 0, "en_viaje": 0, "disponible": 0, "propuesta": 0})
        for k in ("total", "en_viaje", "disponible", "propuesta"):
            b[k] += d[k]
    return {"file": path.name, "by_model": by_model, "by_brand": by_brand, "total": int(len(df))}


def load_stock_usados(path: Path, today: date) -> dict[str, Any]:
    """Stock de usados (Renew): la marca del usado hace de modelo."""
    df = pd.read_excel(path, sheet_name="Datos", header=2)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Marca"])
    df["modelo"] = [_match_model("Renew", m, v) for m, v in zip(df["Marca"].fillna(""), df["Version"].fillna(""))]
    df["estado"] = df["Estado"].astype(str).str.strip().str.upper()
    fecha = pd.to_datetime(df.get("Fecha de Ingreso"), errors="coerce") if "Fecha de Ingreso" in df else None
    df["dias"] = (pd.Timestamp(today) - fecha).dt.days if fecha is not None else None
    by_model: dict[str, dict[str, Any]] = {}
    for key, g in df.groupby("modelo"):
        by_model[key] = {
            "brand": "Renew", "total": int(len(g)), "en_viaje": 0,
            "disponible": int(g["estado"].isin(["DISPONIBLE", "STOCK"]).sum()), "propuesta": 0, "test_drive": 0,
            "dias_promedio": int(g["dias"].dropna().mean()) if g["dias"].notna().any() else None,
        }
    tot = {"total": int(len(df)), "en_viaje": 0, "disponible": int(df["estado"].isin(["DISPONIBLE", "STOCK"]).sum()), "propuesta": 0}
    return {"file": path.name, "by_model": by_model, "by_brand": {"Renew": tot}, "total": int(len(df))}


# ----------------------------------------------------------------------------- acciones comerciales
def load_acciones(path: Path) -> dict[str, Any]:
    xl = pd.ExcelFile(path)
    by_model: dict[str, dict[str, Any]] = {}
    for sheet in xl.sheet_names:
        brand = SHEET_BRAND.get(sheet.strip().upper())
        if not brand:
            continue
        df = xl.parse(sheet)
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "MODELO" not in df.columns or "PVP" not in df.columns:
            continue
        col_stock_viaje = next((c for c in ("STOCK EN VIAJE", "EN VIAJE") if c in df.columns), None)
        col_dcto = next((c for c in ("DESCUENTO", "DCTO") if c in df.columns), None)
        col_obs = next((c for c in df.columns if c.startswith("OBSERVACIONES")), None)
        for _, r in df.iterrows():
            version = str(r.get("MODELO", "") or "").strip()
            pvp = _num(r.get("PVP"))
            if not version or version.lower() == "nan" or pvp <= 0:
                continue
            model = _match_model(brand, version, version)
            d = by_model.setdefault(model, {"brand": brand, "versiones": 0, "pvp_min": None, "pvp_max": None,
                                            "descuento_max": 0.0, "stock": 0, "en_viaje": 0, "avg_ventas_mes": 0.0, "acciones": []})
            d["versiones"] += 1
            d["pvp_min"] = pvp if d["pvp_min"] is None else min(d["pvp_min"], pvp)
            d["pvp_max"] = pvp if d["pvp_max"] is None else max(d["pvp_max"], pvp)
            d["descuento_max"] = max(d["descuento_max"], _num(r.get(col_dcto)) if col_dcto else 0.0)
            d["stock"] += int(_num(r.get("STOCK")))
            d["en_viaje"] += int(_num(r.get(col_stock_viaje))) if col_stock_viaje else 0
            d["avg_ventas_mes"] += _num(r.get("AVG VENTAS"))
            obs = str(r.get(col_obs) or "").strip() if col_obs else ""
            if obs and obs.lower() != "nan" and obs not in d["acciones"] and len(d["acciones"]) < 3:
                d["acciones"].append(obs[:160])
    for d in by_model.values():
        d["avg_ventas_mes"] = round(d["avg_ventas_mes"], 1)
    m = re.search(r"(\d{4}-\d{2})", path.name)
    return {"file": path.name, "periodo": m.group(1) if m else "", "by_model": by_model}


# ----------------------------------------------------------------------------- objetivos
def load_objetivos(path: Path, sales_path: Path | None, today: date) -> dict[str, Any]:
    df = pd.read_excel(path, sheet_name="budget ventas")
    df.columns = [str(c).strip() for c in df.columns]
    df["marca"] = df["MARCA"].astype(str).str.upper().str.strip().map(BUDGET_BRAND)
    df["mes_n"] = df["Mes"].astype(str).str.lower().str.strip().map(lambda m: MESES.index(m) + 1 if m in MESES else None)
    df = df.dropna(subset=["marca", "mes_n"])
    df["Año"] = df["Año"].astype(int)

    real_mes: dict[str, int] = {}
    real_ytd: dict[str, int] = {}
    real_fact_ytd: dict[str, float] = {}
    if sales_path and sales_path.exists():
        s = pd.read_excel(sales_path, sheet_name="Datos", header=2, usecols=["Fecha", "Marca", "Neto"])
        s["Fecha"] = pd.to_datetime(s["Fecha"], errors="coerce")
        s["marca"] = s["Marca"].astype(str).str.upper().str.strip().map(BRAND_MAP)
        s = s.dropna(subset=["Fecha", "marca"])
        y = s[s["Fecha"].dt.year == today.year]
        real_ytd = y.groupby("marca").size().to_dict()
        real_fact_ytd = y.groupby("marca")["Neto"].sum().round(0).to_dict()
        real_mes = y[y["Fecha"].dt.month == today.month].groupby("marca").size().to_dict()
        # Leapmotor y JMEV comparten objetivo
        for k in ("Leapmotor",):
            real_ytd[k] = real_ytd.get("Leapmotor", 0) + real_ytd.get("JMEV", 0)
            real_mes[k] = real_mes.get("Leapmotor", 0) + real_mes.get("JMEV", 0)

    by_brand: dict[str, dict[str, Any]] = {}
    cur = df[df["Año"] == today.year]
    for brand, g in cur.groupby("marca"):
        mes = g[g["mes_n"] == today.month]
        ytd = g[g["mes_n"] <= today.month]
        d = {
            "objetivo_mes": int(mes["Objetivo ventas"].sum()) if len(mes) else None,
            "objetivo_fact_mes": float(mes["Objetivo Facturacion"].sum()) if len(mes) else None,
            "objetivo_ytd": int(ytd["Objetivo ventas"].sum()),
            "objetivo_anual": int(g["Objetivo ventas"].sum()),
            "real_mes": int(real_mes.get(brand, 0)),
            "real_ytd": int(real_ytd.get(brand, 0)),
            "real_fact_ytd": float(real_fact_ytd.get(brand, 0.0)),
        }
        d["avance_ytd_pct"] = round(d["real_ytd"] / d["objetivo_ytd"] * 100, 1) if d["objetivo_ytd"] else None
        d["avance_mes_pct"] = round(d["real_mes"] / d["objetivo_mes"] * 100, 1) if d.get("objetivo_mes") else None
        by_brand[brand] = d
    if "Leapmotor" in by_brand:
        by_brand["JMEV"] = {**by_brand["Leapmotor"], "compartido_con": "Leapmotor"}
    return {"file": path.name, "year": today.year, "month": today.month, "by_brand": by_brand,
            "sales_until": str(s["Fecha"].max().date()) if sales_path and sales_path.exists() else None}


# ----------------------------------------------------------------------------- negociación semanal
def load_negociacion(path: Path) -> dict[str, Any]:
    """
    Cada hoja de marca trae dos tablas: el resumen semanal por vendedor y,
    debajo, las negociaciones abiertas (vendedor, modelo, precio). Se agrega
    todo por marca y por modelo; los vendedores solo se cuentan.
    """
    xl = pd.ExcelFile(path)
    by_brand: dict[str, dict[str, Any]] = {}
    by_model: dict[str, dict[str, Any]] = {}
    for sheet in xl.sheet_names:
        brand = SHEET_BRAND.get(sheet.strip().upper())
        if not brand:
            continue
        raw = xl.parse(sheet, header=None)
        # cortes: filas de encabezado (col 0 == "Año")
        headers = raw.index[raw.iloc[:, 0].astype(str).str.strip().eq("Año")].tolist()
        if not headers:
            continue
        blocks = []
        for i, h in enumerate(headers):
            end_row = headers[i + 1] - 1 if i + 1 < len(headers) else len(raw)
            blk = raw.iloc[h + 1:end_row].copy()
            blk.columns = [str(c).strip() for c in raw.iloc[h]]
            blk = blk[pd.to_numeric(blk["Año"], errors="coerce").notna()]
            blocks.append(blk)
        resumen = blocks[0]
        for c in ("Año", "Mes", "Semana"):
            resumen[c] = pd.to_numeric(resumen[c], errors="coerce")
        resumen = resumen.dropna(subset=["Semana"])
        if resumen.empty:
            continue
        last = resumen.sort_values(["Año", "Mes", "Semana"]).iloc[-1]
        w = resumen[(resumen["Año"] == last["Año"]) & (resumen["Mes"] == last["Mes"]) & (resumen["Semana"] == last["Semana"])]
        num = lambda c: int(pd.to_numeric(w[c], errors="coerce").fillna(0).sum()) if c in w.columns else 0
        periodo = f"{int(last['Año'])}-{int(last['Mes']):02d} semana {int(last['Semana'])}"
        by_brand[brand] = {
            "periodo": periodo,
            "vendedores": int(w["Vendedor"].astype(str).str.strip().replace("", pd.NA).dropna().nunique()),
            "promesa_mes": num("Promesa mes"),
            "venta_mtd": num("Venta MTD"),
            "leads_mes": num("Leads del mes"),
            "nego_actual": num("Nego. sem. actual"),
            "nego_pasada": num("Nego. sem. pasada"),
            "perdidas": num("Perdidas"),
            "nuevas": num("Nuevas"),
            "promesa_semanal": num("Promesa semanal"),
            "negociaciones_abiertas": 0,
        }
        # segunda tabla: negociaciones abiertas por modelo
        if len(blocks) > 1 and "Modelo" in blocks[1].columns:
            neg = blocks[1]
            neg = neg[neg["Modelo"].astype(str).str.strip().ne("") & neg["Modelo"].notna()]
            by_brand[brand]["negociaciones_abiertas"] = int(len(neg))
            for _, r in neg.iterrows():
                version = str(r["Modelo"]).strip()
                model = _match_model(brand, version, version)
                d = by_model.setdefault(model, {"brand": brand, "negociaciones": 0, "periodo": periodo})
                d["negociaciones"] += 1
    return {"file": path.name, "by_brand": by_brand, "by_model": by_model}


# ----------------------------------------------------------------------------- entrada
def fetch_extras(cfg: dict[str, Any], sales_path: str | Path | None, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    base = Path(cfg.get("dir", "data/fuentes"))
    out: dict[str, Any] = {"source": "extras_erp", "date": today.isoformat()}
    jobs = {
        "stock": (cfg.get("stock", "stock_unidades_nuevas.xlsx"), lambda p: load_stock(p, today)),
        "acciones": (cfg.get("acciones", "acciones_comerciales_*.xlsx"), load_acciones),
        "objetivos": (cfg.get("objetivos", "objetivos_ventas.xlsx"), lambda p: load_objetivos(p, Path(sales_path) if sales_path else None, today)),
        "negociacion": (cfg.get("negociacion", "negociacion_semanal_*.xlsx"), load_negociacion),
    }
    for key, (pattern, fn) in jobs.items():
        path = _latest(str(base / pattern))
        if not path:
            logger.info("Extras: sin archivo para %s (%s)", key, pattern)
            continue
        try:
            out[key] = fn(path)
            logger.info("Extras: %s leído de %s", key, path.name)
        except Exception as exc:  # una fuente rota no tumba las demás
            logger.warning("Extras: fallo leyendo %s (%s): %s", key, path.name, exc)
    # Stock de usados (Renew) se suma al stock general
    usados = _latest(str(base / cfg.get("stock_usados", "stock_unidades_usadas.xlsx")))
    if usados and "stock" in out:
        try:
            u = load_stock_usados(usados, today)
            out["stock"]["by_model"].update(u["by_model"]); out["stock"]["by_brand"].update(u["by_brand"]); out["stock"]["total"] += u["total"]
            logger.info("Extras: stock usados (Renew) leído de %s: %d unidades", usados.name, u["total"])
        except Exception as exc:
            logger.warning("Extras: fallo leyendo stock usados (%s): %s", usados.name, exc)
    return out
