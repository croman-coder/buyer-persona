"""
Normalizador del reporte de facturación del ERP (Santa Rosa).

Convierte ``FacturacionUnidades-*.xlsx`` (hoja ``Datos``, encabezado en la
fila 3) al esquema interno del SalesConnector, SIN datos personales:
se descartan Cliente, E-Mail, Teléfonos, VIN, factura. Lo que sale es
agregable y seguro para el vault.

Limitaciones conocidas del ERP (verificadas 2026-09-16):
- ``Tipo Venta`` / ``Tipo Cliente`` / ``Fuente`` / ``Medio`` vienen todos
  como "Salon": no hay contado vs financiado ni origen del lead.
- No hay edad ni género: eso lo aporta Meta (demografía por cuenta).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd

from src.catalog.models_py import MODEL_CATALOG, category_for

logger = logging.getLogger(__name__)

# Marca tal como la escribe el ERP -> marca del portfolio
BRAND_MAP = {
    "GREATWALL": "GWM",
    "GREAT WALL": "GWM",
    "JETOUR": "Jetour",
    "RENAULT": "Renault",
    "MITSUBISHI": "Mitsubishi",
    "JAC": "JAC",
    "SOUEAST": "Soueast",
    "LEAPMOTOR": "Leapmotor",
    "JMEV": "JMEV",
    "ZEEKR": "Zeekr",
    "XPENG": "XPeng",
    "RENEW": "Renew",     # usados certificados: el "modelo" es la marca del usado
}

# Sucursal del ERP -> ciudad (proxy de ubicación del comprador)
LOCAL_CITY = {
    "COSTA ORIENTAL": "Ciudad del Este",
    "SHOPPING SAN LORENZO": "San Lorenzo",
}
DEFAULT_CITY = "Asunción"

DROP_COLS = ["Cliente", "E-Mail", "Teléfonos", "V.I.N.", "NroFactura", "Matrícula"]

# Razón social de una empresa u organismo (el nombre se lee acá y se descarta:
# solo sobrevive la etiqueta). Verificado 2026-09-24 contra las ventas de 12 meses.
_EMPRESA = re.compile(
    r"\b(S ?A|S ?R ?L|E ?A ?S|S ?A ?C ?I|S ?A ?E|S ?A ?E ?C ?A|S ?A ?I ?C|LTDA|LIMITADA|SOCIEDAD|COOPERATIVA|COOP|"
    r"MINISTERIO|MUNICIPALIDAD|GOBERNACION|UNIVERSIDAD|IGLESIA|ASOCIACION|FUNDACION|CONSORCIO|EMPRESA|INSTITUTO|"
    r"COLEGIO|CLUB|HOLDING|GRUPO|GROUP|INC|CORP|AGROPECUARIA|AGROGANADERA|GANADERA|ESTANCIA|INDUSTRIA|INDUSTRIAL|"
    r"COMERCIAL|CONSTRUCTORA|IMPORTADORA|DISTRIBUIDORA|TRANSPORTE|TRANSPORTADORA|SERVICIOS|ENTIDAD|BINACIONAL|"
    r"ITAIPU|YACYRETA|ANDE|ESSAP|PETROPAR|CONMEBOL|EMBAJADA)\b"
)
# Otra concesionaria que compra para revender (Mitsubishi se factura casi
# entero a Nipon): no es cliente final y no dice nada de quién decide.
_REVENDEDOR = re.compile(r"AUTOMOTOR|AUTOLIDER|\bMOTORS\b|CONCESIONARIA|\bAUTOS\b|AUTOMOVIL")


def _tipo_comprador(cliente: object) -> str:
    """'empresa', 'revendedor' o 'persona' a partir del nombre del cliente."""
    s = unicodedata.normalize("NFKD", str(cliente or "").upper())
    s = "".join(c for c in s if not unicodedata.combining(c)).replace(".", "")
    s = re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s))
    if _EMPRESA.search(s):
        return "revendedor" if _REVENDEDOR.search(s) else "empresa"
    return "persona"


def _match_model(brand: str, modelo: str, version: str) -> str:
    """Nombre comercial del catálogo para un (marca, modelo, versión) del ERP."""
    if brand == "Renew":
        # En Renew la columna Modelo trae la marca del usado (JETOUR, KIA...) o
        # "USADOS" genérico; la versión trae el modelo. Se agrupa por marca.
        m = str(modelo).strip().upper()
        for name, pat in MODEL_CATALOG["Renew"].items():
            if name != "Renew Usados" and re.search(pat, f"{m} {version}".lower(), re.I):
                return name
        return "Renew Usados" if m in ("", "USADOS", "NAN") else f"Renew {m.title()}"
    text = f"{brand} {modelo} {version}".lower()
    # Versión primero: desambigua TANK 300/400/500, HAVAL H6/JOLION, TRAVELLER T1/T2
    for name, pat in MODEL_CATALOG.get(brand, {}).items():
        if re.search(pat, f"{brand} {version}".lower(), re.I):
            return name
    for name, pat in MODEL_CATALOG.get(brand, {}).items():
        if re.search(pat, text, re.I):
            return name
    return f"{brand} {str(modelo).strip().title()}"


def normalize_erp(xlsx_path: str | Path, sheet: str = "Datos") -> pd.DataFrame:
    """Lee el xlsx del ERP y devuelve un DataFrame en el esquema interno (sin PII)."""
    df = pd.read_excel(xlsx_path, sheet_name=sheet, header=2)
    df = df.dropna(subset=["Marca"])
    # Única lectura del nombre del cliente: se convierte en etiqueta y se descarta
    df["tipo_comprador"] = df["Cliente"].map(_tipo_comprador) if "Cliente" in df.columns else "persona"
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns], errors="ignore")

    # Notas de crédito / devoluciones vienen con Neto negativo
    df = df[pd.to_numeric(df["Neto"], errors="coerce") > 0].copy()

    df["marca"] = df["Marca"].astype(str).str.upper().str.strip().map(BRAND_MAP)
    df = df.dropna(subset=["marca"])  # JMC, Karry: fuera del portfolio

    df["producto"] = [
        _match_model(b, m, v)
        for b, m, v in zip(df["marca"], df["Modelo"].fillna(""), df["Version"].fillna(""))
    ]
    df["categoria"] = df["producto"].map(category_for)
    df["version"] = df["Version"].fillna("").astype(str).str.strip()

    out = pd.DataFrame({
        "fecha": pd.to_datetime(df["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "producto": df["producto"],
        "marca": df["marca"],
        "categoria": df["categoria"],
        "version": df["version"],
        "cantidad": 1,
        "ingresos": pd.to_numeric(df["Neto"], errors="coerce").round(2),
        "sucursal": df["Local"].fillna("").astype(str).str.strip(),
        "ciudad_cliente": df["Local"].fillna("").astype(str).str.strip().map(
            lambda l: LOCAL_CITY.get(l, DEFAULT_CITY)
        ),
        "canal": "Showroom",
        "vendedor": df["Vendedor"].fillna("").astype(str).str.strip(),
        "retoma_marca": df["Marca Ret."].fillna("").astype(str).str.strip().str.title(),
        # "Concesionario" = venta a un subconcesionario, no a un cliente final
        "tipo_cliente": df["Tipo Cliente"].fillna("").astype(str).str.strip() if "Tipo Cliente" in df.columns else "",
        "tipo_comprador": df["tipo_comprador"],
    })
    out = out.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)
    logger.info("ERP normalizado: %d unidades, %s → %s", len(out), out["fecha"].min(), out["fecha"].max())
    return out


def export_csv(xlsx_path: str | Path, csv_path: str | Path) -> Path:
    """Genera el CSV normalizado (para inspección o para el servidor)."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    normalize_erp(xlsx_path).to_csv(csv_path, index=False, encoding="utf-8")
    return csv_path
