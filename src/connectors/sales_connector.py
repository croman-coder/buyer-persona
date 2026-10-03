"""
Conector de Histórico de Ventas.

Lee archivos CSV o Excel con el histórico de ventas y los normaliza
para su uso en la generación de Buyer Personas.

Columnas esperadas (configurables en settings.yaml → sales.column_mapping):
    - date:            fecha de la venta
    - product:         nombre del producto
    - category:        categoría del producto
    - quantity:        cantidad vendida
    - revenue:         ingresos (monto total)
    - customer_email:  email del cliente
    - customer_age:    edad del cliente
    - customer_gender: género del cliente
    - customer_city:   ciudad del cliente
    - channel:         canal de venta
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class SalesConnector:
    """Lee y normaliza el histórico de ventas desde CSV o Excel."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        # Claves cifradas de cada venta para el cruce con Meta: en memoria, nunca a disco.
        self.claves_ventas: list[dict[str, Any]] = []
        self.file_path = config.get("file_path", "")
        self.column_mapping = config.get("column_mapping", {})

    def _load_dataframe(self) -> pd.DataFrame:
        """Carga el archivo en un DataFrame según su extensión."""
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de ventas: {path}")

        suffix = path.suffix.lower()

        # Reporte de facturación del ERP: se normaliza (y se descarta la PII)
        if str(self.config.get("format", "")).lower() == "erp":
            from src.connectors.erp_normalizer import normalize_erp
            df = normalize_erp(path, claves=self.claves_ventas)
            logger.info("Cargadas %d filas (ERP normalizado) desde %s", len(df), path.name)
            return df

        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        else:
            raise ValueError(f"Formato de archivo no soportado: {suffix}. Use CSV o Excel.")

        logger.info("Cargadas %d filas desde %s", len(df), path.name)
        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renombra las columnas del archivo al esquema interno."""
        # Mapeo inverso: nombre_esperado -> nombre_real_en_archivo
        rename_map = {}

        for expected_name, real_name in self.column_mapping.items():
            if real_name in df.columns:
                rename_map[real_name] = expected_name

        if rename_map:
            df = df.rename(columns=rename_map)

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convierte las columnas a sus tipos correctos."""
        # Fecha
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Numéricos
        numeric_cols = ["quantity", "revenue", "customer_age"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Texto
        text_cols = ["product", "brand", "category", "customer_email", "customer_gender",
                     "customer_city", "channel", "version", "branch", "seller", "tradein_brand"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace({"nan": "", "None": ""})

        return df

    def fetch_all(self) -> dict[str, Any]:
        """
        Carga y procesa el histórico de ventas.

        Returns:
            Diccionario con datos agregados listos para el generador:

            .. code-block:: python

                {
                    "source": "sales",
                    "total_records": 1234,
                    "summary": {
                        "total_revenue": 123456.78,
                        "total_orders": 1234,
                        "avg_order_value": 100.5,
                        "date_range": {"start": "...", "end": "..."},
                    },
                    "top_products": [...],
                    "top_categories": [...],
                    "demographics": {...},
                    "channels": [...],
                    "raw_columns": [...],
                }
        """
        df = self._load_dataframe()
        df = self._normalize_columns(df)
        df = self._convert_types(df)

        result: dict[str, Any] = {
            "source": "sales",
            "total_records": len(df),
            "summary": {},
            "top_products": [],
            "top_brands": [],
            "top_categories": [],
            "demographics": {},
            "channels": [],
            "cities": [],
            "by_brand": {},
            "by_category": {},
            "by_model": {},
            "raw_columns": list(df.columns),
        }

        if df.empty:
            logger.warning("El archivo de ventas está vacío.")
            return result

        # --- Resumen general ---
        total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0.0
        total_orders = len(df)

        result["summary"] = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "avg_order_value": total_revenue / total_orders if total_orders else 0,
            "date_range": {},
        }

        if "date" in df.columns and df["date"].notna().any():
            result["summary"]["date_range"] = {
                "start": df["date"].min().strftime("%Y-%m-%d"),
                "end": df["date"].max().strftime("%Y-%m-%d"),
            }

        # --- Top productos ---
        if "product" in df.columns and "revenue" in df.columns:
            top_products = (
                df.groupby("product")
                .agg(orders=("product", "size"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False)
                .head(15)
                .reset_index()
                .to_dict("records")
            )
            result["top_products"] = top_products

        # --- Top marcas ---
        if "brand" in df.columns and "revenue" in df.columns:
            top_brands = (
                df[df["brand"] != ""]
                .groupby("brand")
                .agg(orders=("brand", "size"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False)
                .head(15)
                .reset_index()
                .to_dict("records")
            )
            result["top_brands"] = top_brands

        # --- Top categorías ---
        if "category" in df.columns and "revenue" in df.columns:
            top_categories = (
                df.groupby("category")
                .agg(orders=("category", "size"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False)
                .head(10)
                .reset_index()
                .to_dict("records")
            )
            result["top_categories"] = top_categories

        # --- Demografía ---
        demo: dict[str, Any] = {}

        if "customer_age" in df.columns and df["customer_age"].notna().any():
            ages = df["customer_age"].dropna()
            demo["age"] = {
                "mean": round(float(ages.mean()), 1),
                "median": round(float(ages.median()), 1),
                "min": int(ages.min()),
                "max": int(ages.max()),
            }

        if "customer_gender" in df.columns:
            gender_counts = df["customer_gender"].value_counts()
            demo["gender"] = {
                k: int(v) for k, v in gender_counts.items() if k and k != ""
            }

        result["demographics"] = demo

        # --- Canales ---
        if "channel" in df.columns:
            channel_data = (
                df.groupby("channel")
                .agg(orders=("channel", "size"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False)
                .reset_index()
                .to_dict("records")
            )
            result["channels"] = channel_data

        # --- Ciudades ---
        if "customer_city" in df.columns:
            city_data = (
                df[df["customer_city"] != ""]
                .groupby("customer_city")
                .agg(orders=("customer_city", "size"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False)
                .head(15)
                .reset_index()
                .to_dict("records")
            )
            result["cities"] = city_data

        # --- Estadísticas por marca y por categoría (para personas segmentadas) ---
        result["by_brand"] = self._segment_stats(df, "brand")
        result["by_category"] = self._segment_stats(df, "category")
        # Nivel modelo: cada producto con su marca y categoría heredadas
        result["by_model"] = self._segment_stats(
            df, "product", attribute_cols=["brand", "category"]
        )

        # --- Quién compra: empresa o persona (centro de compra) ---
        result["comprador_empresa"] = self._comprador_empresa(df)

        return result

    @staticmethod
    def _comprador_empresa(df: pd.DataFrame, dias: int = 365) -> dict[str, Any]:
        """Parte de las ventas a cliente final que factura una empresa, por marca y modelo.

        Cuenta solo al cliente final: fuera las ventas a subconcesionarios y a
        otras concesionarias que compran para revender. La etiqueta sale del
        normalizador del ERP; el nombre del cliente nunca llega hasta acá.
        """
        if "tipo_comprador" not in df.columns or "date" not in df.columns or not df["date"].notna().any():
            return {}
        hasta = df["date"].max()
        d = df[df["date"] >= hasta - pd.Timedelta(days=dias)]
        revende = int((d["tipo_comprador"] == "revendedor").sum())
        if "tipo_cliente" in d.columns:
            revende += int((d["tipo_cliente"].str.lower() == "concesionario").sum())
            d = d[d["tipo_cliente"].str.lower() != "concesionario"]
        d = d[d["tipo_comprador"] != "revendedor"]

        def _agg(col: str) -> dict[str, dict[str, Any]]:
            out: dict[str, dict[str, Any]] = {}
            for key, g in d.groupby(col):
                if not key:
                    continue
                n = len(g)
                e = int((g["tipo_comprador"] == "empresa").sum())
                out[str(key)] = {"ventas": n, "empresa": e, "empresa_pct": round(e / n * 100, 1) if n else 0.0}
            return out

        return {
            "desde": (hasta - pd.Timedelta(days=dias)).strftime("%Y-%m-%d"),
            "hasta": hasta.strftime("%Y-%m-%d"),
            "a_revendedores": revende,
            "por_marca": _agg("brand") if "brand" in d.columns else {},
            "por_modelo": _agg("product") if "product" in d.columns else {},
        }

    def _segment_stats(
        self,
        df: pd.DataFrame,
        col: str,
        attribute_cols: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Calcula demografía y comportamiento de compra por cada valor de ``col``.

        ``attribute_cols`` son columnas de las que se toma el valor dominante
        del grupo y se guarda como atributo (ej. al agrupar por modelo, guardar
        a qué marca y categoría pertenece ese modelo).
        """
        stats_by_value: dict[str, dict[str, Any]] = {}
        if col not in df.columns:
            return stats_by_value

        attribute_cols = attribute_cols or []
        # Ventanas relativas a la última venta de TODA la base (no del grupo):
        # un modelo discontinuado no debe mostrar "últimos 90 días" de su época.
        ref_date = df["date"].max() if "date" in df.columns and df["date"].notna().any() else None

        grouped = df[df[col] != ""].groupby(col)
        for value, g in grouped:
            stats: dict[str, Any] = {
                "orders": int(len(g)),
                "revenue": float(g["revenue"].sum()) if "revenue" in g.columns else 0.0,
            }

            # Atributos heredados (marca/categoría del modelo, etc.)
            for attr in attribute_cols:
                if attr in g.columns and g[attr].notna().any():
                    top = g[attr].value_counts()
                    if len(top):
                        stats[attr] = str(top.index[0])

            # Rango de precio del segmento (útil a nivel modelo)
            if "revenue" in g.columns and "quantity" in g.columns:
                units = g["quantity"].replace(0, 1).fillna(1)
                unit_price = (g["revenue"] / units).dropna()
                if len(unit_price):
                    stats["price"] = {
                        "min": round(float(unit_price.min()), 2),
                        "max": round(float(unit_price.max()), 2),
                        "avg": round(float(unit_price.mean()), 2),
                    }
            stats["avg_order_value"] = (
                stats["revenue"] / stats["orders"] if stats["orders"] else 0.0
            )

            if "customer_age" in g.columns and g["customer_age"].notna().any():
                ages = g["customer_age"].dropna()
                stats["age"] = {
                    "mean": round(float(ages.mean()), 1),
                    "median": round(float(ages.median()), 1),
                    "range": f"{int(ages.quantile(0.25))}-{int(ages.quantile(0.75))}",
                }

            if "customer_gender" in g.columns:
                gender_counts = g["customer_gender"].value_counts()
                stats["gender"] = {k: int(v) for k, v in gender_counts.items() if k}

            if "product" in g.columns:
                stats["top_products"] = (
                    g.groupby("product").size().sort_values(ascending=False).head(5).index.tolist()
                )

            if "channel" in g.columns:
                stats["channels"] = (
                    g.groupby("channel").size().sort_values(ascending=False).head(3).index.tolist()
                )

            if "customer_city" in g.columns:
                stats["cities"] = (
                    g[g["customer_city"] != ""]
                    .groupby("customer_city").size()
                    .sort_values(ascending=False).head(5).index.tolist()
                )

            # Extras del ERP (solo si existen las columnas)
            if "version" in g.columns:
                stats["top_versions"] = (
                    g[g["version"] != ""].groupby("version").size()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
            if "tradein_brand" in g.columns:
                tr = g[g["tradein_brand"] != ""]["tradein_brand"].value_counts().head(5)
                stats["tradein_brands"] = {k: int(v) for k, v in tr.items()}
                stats["tradein_rate"] = round(float((g["tradein_brand"] != "").mean() * 100), 1)
            if "branch" in g.columns:
                stats["branches"] = (
                    g[g["branch"] != ""].groupby("branch").size()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
            if "seller" in g.columns:
                stats["top_sellers"] = (
                    g[g["seller"] != ""].groupby("seller").size()
                    .sort_values(ascending=False).head(3).index.tolist()
                )
            if ref_date is not None and "date" in g.columns:
                stats["orders_last_90d"] = int((g["date"] >= ref_date - pd.Timedelta(days=90)).sum())
                stats["orders_last_365d"] = int((g["date"] >= ref_date - pd.Timedelta(days=365)).sum())

            stats_by_value[str(value)] = stats

        return stats_by_value