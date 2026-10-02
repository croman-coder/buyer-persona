"""
Conector de Embudo Completo (Full Funnel).

Captura datos de cada etapa del viaje del cliente:

1. TOFU (Top of Funnel) - Descubrimiento
   - Google Analytics: visitas al sitio web
   - Meta/Instagram: engagement (likes, comments, shares)
   - YouTube: visualizaciones de videos

2. MOFU (Middle of Funnel) - Consideración
   - Formularios web: solicitudes de info
   - Test drives solicitados
   - Descargas de catálogo
   - WhatsApp: conversaciones iniciadas

3. BOFU (Bottom of Funnel) - Decisión
   - Cotizaciones solicitadas
   - Visitas al showroom
   - Emails de seguimiento

4. Post-venta - Retención
   - Encuestas de satisfacción
   - Repuestos y servicio
   - Referidos

Cada etapa alimenta el Buyer Persona con datos reales del comportamiento.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)


class FunnelConnector:
    """Conecta con múltiples fuentes para alimentar el embudo completo."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def fetch_all(self) -> dict[str, Any]:
        """
        Recopila datos de todas las etapas del embudo.

        Returns:
            Dict estructurado por etapa del embudo.
        """
        logger.info("📡 Recopilando datos del embudo completo...")

        return {
            "source": "funnel",
            "date_range": self._get_date_range(),
            "tofu": self._fetch_tofu(),
            "mofu": self._fetch_mofu(),
            "bofu": self._fetch_bofu(),
            "post_sale": self._fetch_post_sale(),
        }

    def _get_date_range(self) -> dict[str, str]:
        days_back = int(self.config.get("days_back", 90))
        end = datetime.now()
        start = end - timedelta(days=days_back)
        return {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}

    # ------------------------------------------------------------------
    # TOFU - Descubrimiento / Conciencia
    # ------------------------------------------------------------------

    def _fetch_tofu(self) -> dict[str, Any]:
        """Top of Funnel: visitas, alcance, impresiones."""
        data: dict[str, Any] = {}

        # --- Google Analytics 4 (vía API) ---
        if self.config.get("google_analytics", {}).get("enabled"):
            data["google_analytics"] = self._fetch_ga4()

        # --- Meta / Instagram Engagement ---
        if self.config.get("meta_social", {}).get("enabled"):
            data["meta_social"] = self._fetch_meta_social()

        # --- YouTube ---
        if self.config.get("youtube", {}).get("enabled"):
            data["youtube"] = self._fetch_youtube()

        # --- TikTok (si está configurado) ---
        if self.config.get("tiktok", {}).get("enabled"):
            data["tiktok"] = self._fetch_tiktok()

        return data

    def _fetch_ga4(self) -> dict[str, Any]:
        """
        Extrae datos de Google Analytics 4.

        Requiere:
        - service_account_json (clave de servicio de Google Cloud)
        - property_id (ID de propiedad de GA4)
        """
        ga_cfg = self.config.get("google_analytics", {})
        property_id = ga_cfg.get("property_id", "")

        if not property_id:
            return {}

        try:
            # Usar la API de Google Analytics Data
            # from google.analytics.data_v1beta import BetaAnalyticsDataClient
            # Esta es una implementación simplificada

            logger.info("Consultando Google Analytics 4 (Property: %s)", property_id)

            return {
                "source": "google_analytics_4",
                "metrics": {
                    "total_users": "N/D (requiere configuración API)",
                    "page_views": "N/D",
                    "avg_session_duration": "N/D",
                    "bounce_rate": "N/D",
                },
                "top_pages": [],
                "traffic_sources": [],
                "device_breakdown": {},
                "note": "Configurar service_account_json y property_id en settings.yaml",
            }
        except Exception as e:
            logger.error("Error en GA4: %s", e)
            return {}

    def _fetch_meta_social(self) -> dict[str, Any]:
        """Extrae engagement de la página de Facebook/Instagram."""
        social_cfg = self.config.get("meta_social", {})
        page_id = social_cfg.get("page_id", "")
        access_token = social_cfg.get("access_token", "")
        api_version = social_cfg.get("api_version", "v21.0")

        if not page_id or not access_token:
            return {}

        try:
            url = f"https://graph.facebook.com/{api_version}/{page_id}/insights"
            params = {
                "metric": "page_impressions,page_post_engagements,page_reach",
                "period": "day",
                "access_token": access_token,
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Procesar métricas
            metrics: dict[str, Any] = {}
            for item in data.get("data", []):
                name = item.get("name", "")
                values = item.get("values", [])
                if values:
                    metrics[name] = values[-1].get("value", 0)

            return {
                "source": "meta_social",
                "metrics": metrics,
                "engagement_rate": "N/D",
            }
        except Exception as e:
            logger.error("Error en Meta Social: %s", e)
            return {}

    def _fetch_youtube(self) -> dict[str, Any]:
        """Extrae métricas del canal de YouTube."""
        yt_cfg = self.config.get("youtube", {})
        channel_id = yt_cfg.get("channel_id", "")
        api_key = yt_cfg.get("api_key", "")

        if not channel_id or not api_key:
            return {}

        try:
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                "part": "statistics",
                "id": channel_id,
                "key": api_key,
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if items:
                stats = items[0].get("statistics", {})
                return {
                    "source": "youtube",
                    "subscribers": stats.get("subscriberCount", 0),
                    "total_views": stats.get("viewCount", 0),
                    "total_videos": stats.get("videoCount", 0),
                }
            return {}
        except Exception as e:
            logger.error("Error en YouTube: %s", e)
            return {}

    def _fetch_tiktok(self) -> dict[str, Any]:
        """Extrae métricas de TikTok Business."""
        # TikTok Business API requiere OAuth
        return {
            "source": "tiktok",
            "note": "Requiere configuración de TikTok Business API",
        }

    # ------------------------------------------------------------------
    # MOFU - Consideración / Interés
    # ------------------------------------------------------------------

    def _fetch_mofu(self) -> dict[str, Any]:
        """Middle of Funnel: formularios, test drives, catálogos descargados."""
        data: dict[str, Any] = {}

        # --- Formularios Web (Google Forms / Typeform / propio) ---
        form_cfg = self.config.get("web_forms", {})
        if form_cfg.get("enabled"):
            data["web_forms"] = self._fetch_web_forms()

        # --- Meta Lead Forms (Formularios de Facebook/Instagram) ---
        lead_cfg = self.config.get("meta_leads", {})
        if lead_cfg.get("enabled"):
            data["meta_leads"] = self._fetch_meta_leads()

        # --- Test Drives ---
        testdrive_cfg = self.config.get("test_drives", {})
        if testdrive_cfg.get("enabled"):
            data["test_drives"] = self._fetch_test_drives(testdrive_cfg)

        # --- WhatsApp Conversations ---
        wa_cfg = self.config.get("whatsapp", {})
        if wa_cfg.get("enabled"):
            data["whatsapp"] = self._fetch_whatsapp(wa_cfg)

        return data

    def _fetch_web_forms(self) -> dict[str, Any]:
        """
        Lee formularios web desde un CSV o API.

        Columnas esperadas en CSV de formularios:
        - fecha, nombre, email, telefono, vehiculo_interes,
          mensaje, fuente (web/meta/google)
        """
        form_cfg = self.config.get("web_forms", {})
        csv_path = form_cfg.get("csv_path", "")

        if not csv_path:
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            return {
                "source": "web_forms",
                "total_leads": len(df),
                "by_vehicle": df.groupby("vehiculo_interes").size().to_dict()
                if "vehiculo_interes" in df.columns
                else {},
                "by_source": df.groupby("fuente").size().to_dict()
                if "fuente" in df.columns
                else {},
            }
        except Exception as e:
            logger.error("Error en web forms: %s", e)
            return {}

    def _fetch_meta_leads(self) -> dict[str, Any]:
        """
        Extrae leads de Meta Lead Forms (Instant Forms).

        Vía Graph API: /{page_id}/leadgen_forms
        """
        lead_cfg = self.config.get("meta_leads", {})
        page_id = lead_cfg.get("page_id", "")
        access_token = lead_cfg.get("access_token", "")

        if not page_id or not access_token:
            return {}

        try:
            api_version = lead_cfg.get("api_version", "v21.0")
            url = f"https://graph.facebook.com/{api_version}/{page_id}/leadgen_forms"
            params = {"access_token": access_token, "fields": "id,name,leadgen_export_csv_url"}

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            forms = data.get("data", [])
            return {
                "source": "meta_leads",
                "total_forms": len(forms),
                "forms": [{"id": f.get("id"), "name": f.get("name", "")} for f in forms],
            }
        except Exception as e:
            logger.error("Error en Meta Leads: %s", e)
            return {}

    def _fetch_test_drives(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Lee solicitudes de test drive desde CSV o CRM.

        Columnas esperadas:
        - fecha, nombre, email, telefono, vehiculo,
          ciudad, fecha_preferida, estado (pendiente/confirmado/completado/cancelado)
        """
        csv_path = cfg.get("csv_path", "")

        if not csv_path:
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            result: dict[str, Any] = {
                "source": "test_drives",
                "total_requests": len(df),
            }

            if "estado" in df.columns:
                result["by_status"] = df["estado"].value_counts().to_dict()
            if "vehiculo" in df.columns:
                result["by_vehicle"] = df["vehiculo"].value_counts().head(10).to_dict()
            if "ciudad" in df.columns:
                result["by_city"] = df["ciudad"].value_counts().head(10).to_dict()

            # Tasa de conversión de test drive a venta
            if "estado" in df.columns:
                completed = (df["estado"] == "completado").sum()
                result["completion_rate"] = f"{(completed / len(df) * 100):.1f}%" if len(df) > 0 else "0%"

            return result
        except Exception as e:
            logger.error("Error en test drives: %s", e)
            return {}

    def _fetch_whatsapp(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Extrae métricas de conversaciones de WhatsApp Business.

        Vía WhatsApp Business API o CSV exportado.
        """
        csv_path = cfg.get("csv_path", "")

        if csv_path:
            try:
                import pandas as pd

                df = pd.read_csv(csv_path)

                return {
                    "source": "whatsapp",
                    "total_conversations": len(df),
                    "unique_contacts": df["telefono"].nunique() if "telefono" in df.columns else 0,
                }
            except Exception as e:
                logger.error("Error en WhatsApp CSV: %s", e)

        # WhatsApp Cloud API
        api_token = cfg.get("api_token", "")
        phone_number_id = cfg.get("phone_number_id", "")

        if api_token and phone_number_id:
            try:
                url = f"https://graph.facebook.com/v21.0/{phone_number_id}/whatsapp_business_profile"
                params = {"access_token": api_token}

                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                return {
                    "source": "whatsapp_cloud_api",
                    "status": "connected",
                }
            except Exception as e:
                logger.error("Error en WhatsApp API: %s", e)

        return {}

    # ------------------------------------------------------------------
    # BOFU - Decisión / Acción
    # ------------------------------------------------------------------

    def _fetch_bofu(self) -> dict[str, Any]:
        """Bottom of Funnel: cotizaciones, visitas a showroom, negociaciones."""
        data: dict[str, Any] = {}

        # --- Cotizaciones ---
        quote_cfg = self.config.get("quotes", {})
        if quote_cfg.get("enabled"):
            data["quotes"] = self._fetch_quotes(quote_cfg)

        # --- Visitas a Showroom ---
        showroom_cfg = self.config.get("showroom", {})
        if showroom_cfg.get("enabled"):
            data["showroom"] = self._fetch_showroom(showroom_cfg)

        return data

    def _fetch_quotes(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Lee cotizaciones desde CSV o CRM.

        Columnas esperadas:
        - fecha, cliente, vehiculo, precio_cotizado, estado,
          vendedor, dias_para_cerrar, resultado (vendido/perdido/en_proceso)
        """
        csv_path = cfg.get("csv_path", "")

        if not csv_path:
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            result: dict[str, Any] = {
                "source": "quotes",
                "total_quotes": len(df),
            }

            if "resultado" in df.columns:
                result["by_result"] = df["resultado"].value_counts().to_dict()
                won = (df["resultado"] == "vendido").sum()
                result["win_rate"] = f"{(won / len(df) * 100):.1f}%" if len(df) > 0 else "0%"

            if "vehiculo" in df.columns:
                result["by_vehicle"] = df["vehiculo"].value_counts().head(10).to_dict()

            if "vendedor" in df.columns:
                result["by_salesperson"] = df["vendedor"].value_counts().to_dict()

            return result
        except Exception as e:
            logger.error("Error en quotes: %s", e)
            return {}

    def _fetch_showroom(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Registra visitas al showroom desde CSV o sistema de turnos.

        Columnas esperadas:
        - fecha, cliente, vehiculo_interes, vendedor,
          tiempo_visita_min, resultado (compro/no_compro/pending)
        """
        csv_path = cfg.get("csv_path", "")

        if not csv_path:
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            result: dict[str, Any] = {
                "source": "showroom_visits",
                "total_visits": len(df),
            }

            if "resultado" in df.columns:
                result["by_result"] = df["resultado"].value_counts().to_dict()

            if "vehiculo_interes" in df.columns:
                result["by_vehicle"] = df["vehiculo_interes"].value_counts().head(10).to_dict()

            return result
        except Exception as e:
            logger.error("Error en showroom: %s", e)
            return {}

    # ------------------------------------------------------------------
    # Post-Venta - Retención y Referidos
    # ------------------------------------------------------------------

    def _fetch_post_sale(self) -> dict[str, Any]:
        """Post-venta: satisfacción, repuestos, referidos."""
        data: dict[str, Any] = {}

        survey_cfg = self.config.get("surveys", {})
        if survey_cfg.get("enabled"):
            data["surveys"] = self._fetch_surveys(survey_cfg)

        return data

    def _fetch_surveys(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Lee encuestas de satisfacción desde CSV.

        Columnas esperadas:
        - fecha, cliente, vehiculo, score (1-10),
          recomendaria (si/no), comentario
        """
        csv_path = cfg.get("csv_path", "")

        if not csv_path:
            return {}

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            result: dict[str, Any] = {
                "source": "satisfaction_surveys",
                "total_responses": len(df),
            }

            if "score" in df.columns:
                result["avg_score"] = round(float(df["score"].mean()), 1)
                result["nps_promoters"] = int((df["score"] >= 9).sum())
                result["nps_detractors"] = int((df["score"] <= 6).sum())
                total = len(df)
                if total > 0:
                    nps = ((result["nps_promoters"] - result["nps_detractors"]) / total) * 100
                    result["nps_score"] = round(nps, 1)

            if "recomendaria" in df.columns:
                would_recommend = (df["recomendaria"].str.lower() == "si").sum()
                result["recommendation_rate"] = f"{(would_recommend / len(df) * 100):.1f}%"

            return result
        except Exception as e:
            logger.error("Error en surveys: %s", e)
            return {}