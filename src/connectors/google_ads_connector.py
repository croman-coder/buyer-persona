"""
Conector de Google Ads.

Extrae información relevante para construir Buyer Personas:
- Demografía por edad y género (audience_insights / demographic)
- Ubicaciones geográficas con mejor rendimiento
- Intereses y audiencias afines
- Rendimiento general de campañas (CTR, conversión, costos)

Referencia de la API:
    https://developers.google.com/google-ads/api/docs/start
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class GoogleAdsConnector:
    """Wrapper sobre la API de Google Ads para extraer insights de audiencia."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._client = None

    @property
    def client(self):
        """Cliente de Google Ads (lazy init)."""
        if self._client is None:
            try:
                from google.ads.googleads.client import GoogleAdsClient
            except ImportError as exc:
                raise ImportError(
                    "La librería google-ads no está instalada. "
                    "Ejecuta: pip install google-ads"
                ) from exc

            credentials = {
                "developer_token": self.config.get("developer_token", ""),
                "client_id": self.config.get("client_id", ""),
                "client_secret": self.config.get("client_secret", ""),
                "refresh_token": self.config.get("refresh_token", ""),
                "login_customer_id": self.config.get("login_customer_id", ""),
                "use_proto_plus": True,
            }
            self._client = GoogleAdsClient.load_from_dict(credentials)
        return self._client

    def _get_date_range(self) -> tuple[str, str]:
        """Devuelve (desde, hasta) en formato YYYY-MM-DD."""
        days_back = int(self.config.get("days_back", 90))
        end = datetime.now()
        start = end - timedelta(days=days_back)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def fetch_all(self) -> dict[str, Any]:
        """
        Ejecuta todas las consultas y devuelve un dict estructurado:

        .. code-block:: python

            {
                "source": "google_ads",
                "date_range": {"start": "...", "end": "..."},
                "demographics": {"age": [...], "gender": [...]},
                "locations": [...],
                "interests": [...],
                "campaigns": [...],
            }
        """
        start_date, end_date = self._get_date_range()

        logger.info("Consultando Google Ads desde %s hasta %s", start_date, end_date)

        return {
            "source": "google_ads",
            "date_range": {"start": start_date, "end": end_date},
            "demographics": self._fetch_demographics(start_date, end_date),
            "locations": self._fetch_locations(start_date, end_date),
            "interests": self._fetch_interests(start_date, end_date),
            "campaigns": self._fetch_campaign_performance(start_date, end_date),
        }

    # ------------------------------------------------------------------
    # Consultas GAQL (Google Ads Query Language)
    # ------------------------------------------------------------------

    def _run_query(self, query: str) -> list:
        """Ejecuta una consulta GAQL y devuelve las filas."""
        from google.ads.googleads.errors import GoogleAdsException

        customer_id = self.config.get("customer_id", "").replace("-", "")
        ga_service = self.client.get_service("GoogleAdsService")

        try:
            response = ga_service.search(customer_id=customer_id, query=query)
            return list(response)
        except GoogleAdsException as ex:
            logger.error("Error de Google Ads: %s", ex.failure)
            return []

    def _fetch_demographics(self, start: str, end: str) -> dict[str, list]:
        """Extrae demografía por edad y género."""
        age_query = f"""
            SELECT
              ad_group_criterion.age_range.type,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions,
              metrics.cost_micros
            FROM age_range_view
            WHERE segments.date >= '{start}' AND segments.date <= '{end}'
            ORDER BY metrics.impressions DESC
        """
        gender_query = f"""
            SELECT
              ad_group_criterion.gender.type,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions,
              metrics.cost_micros
            FROM gender_view
            WHERE segments.date >= '{start}' AND segments.date <= '{end}'
            ORDER BY metrics.impressions DESC
        """
        age_rows = []
        for row in self._run_query(age_query):
            age_rows.append({
                "age_range": row.ad_group_criterion.age_range.type_.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
                "cost": row.metrics.cost_micros / 1_000_000,
            })

        gender_rows = []
        for row in self._run_query(gender_query):
            gender_rows.append({
                "gender": row.ad_group_criterion.gender.type_.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
                "cost": row.metrics.cost_micros / 1_000_000,
            })

        return {"age": age_rows, "gender": gender_rows}

    def _fetch_locations(self, start: str, end: str) -> list[dict]:
        """Extrae ubicaciones geográficas con mejor rendimiento."""
        query = f"""
            SELECT
              geographic_view.country_criterion_id,
              geographic_view.location_type,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions,
              segments.geo_target_country
            FROM geographic_view
            WHERE segments.date >= '{start}' AND segments.date <= '{end}'
            ORDER BY metrics.conversions DESC
            LIMIT 20
        """
        locations = []
        for row in self._run_query(query):
            locations.append({
                "country_id": row.geographic_view.country_criterion_id,
                "location_type": row.geographic_view.location_type_.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
            })
        return locations

    def _fetch_interests(self, start: str, end: str) -> list[dict]:
        """Extrae intereses y audiencias afines (affinity / in-market)."""
        query = f"""
            SELECT
              ad_group_criterion.user_interest.user_interest_category,
              metrics.impressions,
              metrics.clicks,
              metrics.conversions
            FROM user_interest_view
            WHERE segments.date >= '{start}' AND segments.date <= '{end}'
            ORDER BY metrics.impressions DESC
            LIMIT 30
        """
        interests = []
        for row in self._run_query(query):
            interests.append({
                "category": row.ad_group_criterion.user_interest.user_interest_category,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "conversions": row.metrics.conversions,
            })
        return interests

    def _fetch_campaign_performance(self, start: str, end: str) -> list[dict]:
        """Extrae rendimiento agregado por campaña."""
        query = f"""
            SELECT
              campaign.name,
              campaign.advertising_channel_type,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions,
              metrics.conversions_value,
              metrics.ctr
            FROM campaign
            WHERE segments.date >= '{start}' AND segments.date <= '{end}'
              AND campaign.status = 'ENABLED'
            ORDER BY metrics.cost_micros DESC
        """
        campaigns = []
        for row in self._run_query(query):
            metrics = row.metrics
            campaigns.append({
                "name": row.campaign.name,
                "channel": row.campaign.advertising_channel_type_.name,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "cost": metrics.cost_micros / 1_000_000,
                "conversions": metrics.conversions,
                "revenue": metrics.conversions_value,
                "ctr": metrics.ctr,
            })
        return campaigns