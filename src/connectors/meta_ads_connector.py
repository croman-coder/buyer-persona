"""
Conector de Meta Ads (Facebook / Instagram).

Extrae información relevante para construir Buyer Personas:
- Demografía de audiencia (edad, género, ubicación)
- Intereses y comportamientos de targeting
- Rendimiento de campañas y conjuntos de anuncios
- Métricas de engagement (CTR, CPL, ROAS)

Referencia de la API:
    https://developers.facebook.com/docs/marketing-api/insights
    https://developers.facebook.com/docs/marketing-api/audiences/reference
"""

from __future__ import annotations

import logging
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)


class MetaAdsConnector:
    """Wrapper sobre la Graph API de Meta para extraer insights de audiencia."""

    BASE_URL = "https://graph.facebook.com"

    # Un "contacto" es un formulario enviado o un chat (WhatsApp/Messenger/IG) iniciado
    CONTACT_ACTIONS = ("lead", "onsite_conversion.messaging_conversation_started_7d")

    def __init__(self, config: dict[str, Any]):
        self.config = config
        # Claves cifradas de cada lead para el cruce con las ventas: en memoria, nunca a disco.
        self.claves_leads: list[dict[str, Any]] = []
        self.access_token = config.get("access_token", "")
        self.ad_account_id = config.get("ad_account_id", "")
        self.api_version = config.get("api_version", "v21.0")
        self.app_id = config.get("app_id", "")
        self.app_secret = config.get("app_secret", "")
        # Multi-cuenta: "act_111:Marca1,act_222:Marca2" (la etiqueta es opcional)
        self.ad_accounts = self._parse_accounts(
            config.get("ad_account_ids", "") or self.ad_account_id
        )
        # Cuentas cuya etiqueta no es una marca del portfolio (compartidas,
        # multimarca, marcas ajenas): se saltan para no ensuciar los agregados.
        excluded = {str(x).strip().lower() for x in (config.get("exclude_labels") or [])}
        if excluded:
            before = len(self.ad_accounts)
            self.ad_accounts = [a for a in self.ad_accounts if a["label"].lower() not in excluded]
            skipped = before - len(self.ad_accounts)
            if skipped:
                logger.info("Meta Ads: %d cuenta(s) excluidas por etiqueta (%s)", skipped, ", ".join(sorted(excluded)))

    @staticmethod
    def _parse_accounts(raw: str) -> list[dict[str, str]]:
        """Parsea 'act_111:Etiqueta,act_222' → [{'id': ..., 'label': ...}, ...]."""
        accounts: list[dict[str, str]] = []
        for part in str(raw).split(","):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                acc_id, label = part.split(":", 1)
            else:
                acc_id, label = part, part
            accounts.append({"id": acc_id.strip(), "label": label.strip()})
        return accounts

    def _get_date_range(self) -> tuple[str, str]:
        """Devuelve (desde, hasta) en formato YYYY-MM-DD."""
        days_back = int(self.config.get("days_back", 90))
        end = datetime.now()
        start = end - timedelta(days=days_back)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def _build_url(self, path: str) -> str:
        """Construye la URL completa de la Graph API."""
        return f"{self.BASE_URL}/{self.api_version}/{path}"

    # Códigos de error de la Graph API que indican rate limiting (reintentable)
    _RATE_LIMIT_CODES = {4, 17, 32, 613, 80004}
    _MAX_RETRIES = 5

    def _request(self, path: str, params: dict, token: str | None = None) -> dict | list:
        """Hace una petición GET a la Graph API con reintento ante rate limits.

        ``token`` permite usar un page access token en vez del token de la app;
        los endpoints de formularios de leads sólo aceptan el de la página.
        """
        params["access_token"] = token or self.access_token
        url = self._build_url(path)
        logger.debug("Meta API GET %s", url)

        backoff = 20
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as exc:
                error_data = exc.response.json() if exc.response is not None else {}
                code = error_data.get("error", {}).get("code")
                if code in self._RATE_LIMIT_CODES and attempt < self._MAX_RETRIES:
                    logger.warning(
                        "Meta API: rate limit (code %s), reintento %d/%d en %ds",
                        code, attempt, self._MAX_RETRIES, backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("Error HTTP de Meta API: %s", error_data)
                return {}
            except requests.exceptions.RequestException as exc:
                logger.error("Error de conexión a Meta API: %s", exc)
                return {}
        return {}

    def _request_paginated(
        self, path: str, params: dict, limit: int = 100, token: str | None = None
    ) -> list[dict]:
        """Hace peticiones paginadas y acumula resultados."""
        params.setdefault("limit", limit)
        results: list[dict] = []
        url = path
        next_cursor = None

        while url:
            if next_cursor:
                params["after"] = next_cursor

            data = self._request(url, params, token=token)
            if not isinstance(data, dict):
                break

            results.extend(data.get("data", []))

            paging = data.get("paging", {})
            cursors = paging.get("cursors", {})
            next_cursor = cursors.get("after")

            # Si no hay cursor "after" o no hay más datos, terminar
            if not next_cursor or not data.get("data"):
                break

            # Pausa para respetar rate limits
            time.sleep(0.1)

        return results

    def fetch_all(self) -> dict[str, Any]:
        """
        Ejecuta todas las consultas y devuelve un dict estructurado:

        .. code-block:: python

            {
                "source": "meta_ads",
                "date_range": {"start": "...", "end": "..."},
                "demographics": {"age_gender": [...], "country": [...]},
                "interests": [...],
                "campaigns": [...],
            }
        """
        start_date, end_date = self._get_date_range()

        logger.info("Consultando Meta Ads desde %s hasta %s", start_date, end_date)

        merged: dict[str, Any] = {
            "source": "meta_ads",
            "date_range": {"start": start_date, "end": end_date},
            "demographics": {"age_gender": [], "age_gender_ad": [], "device": [], "country": [], "region": []},
            "interests": [],
            "adset_targeting": [],
            "campaigns": [],
            "ad_creatives": [],
            "placements": [],
            "audiences": [],
            "leads_by_brand": {},
            "accounts": {},
        }

        total = len(self.ad_accounts)
        # Con portfolios chicos se pide el desglose completo (país/región);
        # con muchas cuentas se recorta para no pegar contra el rate limit.
        full_demographics = total <= 5

        for i, account in enumerate(self.ad_accounts, start=1):
            acc_id, label = account["id"], account["label"]
            logger.info("Meta Ads: consultando cuenta %s (%s) [%d/%d]", acc_id, label, i, total)

            self.ad_account_id = acc_id
            try:
                demo = self._fetch_demographics(start_date, end_date, full=full_demographics)
                interests, adset_targeting = self._fetch_targeting_insights(start_date, end_date)
                campaigns = self._fetch_campaign_insights(start_date, end_date)
                creatives = self._fetch_ad_creatives(start_date, end_date)
                placements = self._fetch_placement_breakdown(start_date, end_date)
                audiences = self._fetch_custom_audiences()
            except Exception as exc:  # una cuenta caída no debe tumbar el resto
                logger.warning("Meta Ads: fallo en cuenta %s (%s): %s", acc_id, label, exc)
                continue
            finally:
                if total > 10:
                    time.sleep(1.5)  # dar aire al rate limit de la app

            # Etiquetar cada registro con su cuenta/marca
            for key in ("age_gender", "age_gender_ad", "device", "country", "region"):
                for row in demo.get(key, []):
                    row["account"] = label
                merged["demographics"][key].extend(demo.get(key, []))
            for row in interests:
                row["account"] = label
            for row in adset_targeting:
                row["account"] = label
            merged["adset_targeting"].extend(adset_targeting)
            for row in campaigns:
                row["account"] = label
            for row in creatives:
                row["account"] = label
            for row in placements:
                row["account"] = label
            for row in audiences:
                row["account"] = label
            merged["interests"].extend(interests)
            merged["campaigns"].extend(campaigns)
            merged["ad_creatives"].extend(creatives)
            merged["placements"].extend(placements)
            merged["audiences"].extend(audiences)

            # Varias cuentas pueden compartir la misma marca (una por vendedor):
            # acumular en una lista, no pisar.
            merged["accounts"].setdefault(label, []).append({
                "account_id": acc_id,
                "demographics": demo,
                "interests": interests,
                "campaigns": campaigns,
                "ad_creatives": creatives,
            })

        # --- Leads: una sola pasada por PÁGINAS ---
        # Los formularios cuelgan de páginas, no de cuentas publicitarias, y
        # varias cuentas comparten marca. Recorrer páginas una vez evita
        # consultar la misma página 85 veces.
        try:
            self._collect_leads_from_pages(merged, days_back=int(self.config.get("days_back", 90)))
        except Exception as exc:  # los leads no deben tumbar el resto del fetch
            logger.warning("Meta Ads: no se pudieron leer los leads por página: %s", exc)

        # Género y edad segmentados de cada conjunto con entrega (activos o no):
        # el centro de compra descarta los que apuntan a un solo género.
        try:
            ids = {str(r["adset_id"]) for r in merged["demographics"]["age_gender_ad"] if r.get("adset_id")}
            merged["adset_demo_targeting"] = self._fetch_adset_demo_targeting(ids)
        except Exception as exc:
            logger.warning("Meta Ads: no se pudo leer la segmentación por conjunto: %s", exc)
            merged["adset_demo_targeting"] = {}

        # Counter -> dict plano (top 10) para que sea JSON-serializable y fácil de consumir
        for brand, agg in merged["leads_by_brand"].items():
            merged["leads_by_brand"][brand] = {
                "total_leads": agg["total_leads"],
                "model_interest": dict(agg["model_interest"].most_common(10)),
                "payment_method": dict(agg["payment_method"].most_common(10)),
                "city": dict(agg["city"].most_common(10)),
                "purchase_intent": dict(agg["purchase_intent"].most_common(10)),
            }

        return merged

    # ------------------------------------------------------------------
    # Consultas a la Graph API
    # ------------------------------------------------------------------

    def _fetch_demographics(self, start: str, end: str, full: bool = False) -> dict[str, list]:
        """
        Extrae demografía por edad+género (siempre) y, si ``full=True``,
        también por país y región. Con portfolios grandes (muchas cuentas)
        se omite país/región por defecto para no agotar el rate limit de
        la app — la ubicación ya se cubre con las ciudades del histórico
        de ventas.
        """
        age_gender = self._request_paginated(
            f"{self.ad_account_id}/insights",
            {
                "fields": "impressions,clicks,actions,spend,conversions",
                "time_range": f'{{"since":"{start}","until":"{end}"}}',
                "breakdowns": "age,gender",
                "level": "account",
            },
        )

        # Mismo desglose pero a nivel anuncio: permite atribuir edad/género a
        # cada MODELO (el anuncio nombra al modelo) en vez de heredar la marca.
        # También trae clics al enlace y contactos (formulario o chat) con el
        # conjunto de cada fila: con eso el centro de compra compara quién mira
        # y quién da el paso dentro del mismo conjunto.
        age_gender_ad = self._request_paginated(
            f"{self.ad_account_id}/insights",
            {
                "fields": "ad_id,ad_name,adset_id,impressions,clicks,inline_link_clicks,spend,actions",
                "time_range": f'{{"since":"{start}","until":"{end}"}}',
                "breakdowns": "age,gender",
                "level": "ad",
                "limit": 500,
            },
        )
        for row in age_gender_ad:
            # Solo se guarda el total de contactos: la lista completa de acciones
            # duplicaría el tamaño del JSON diario sin uso.
            acciones = row.pop("actions", None) or []
            row["contactos"] = sum(
                float(a.get("value", 0)) for a in acciones if a.get("action_type") in self.CONTACT_ACTIONS
            )

        # Dispositivo (iPhone vs Android): proxy de nivel socioeconómico en PY
        device = self._request_paginated(
            f"{self.ad_account_id}/insights",
            {"fields": "impressions,clicks,spend", "time_range": f'{{"since":"{start}","until":"{end}"}}',
             "breakdowns": "impression_device", "level": "account"},
        )

        country: list[dict] = []
        region: list[dict] = []
        if full:
            country = self._request_paginated(
                f"{self.ad_account_id}/insights",
                {
                    "fields": "impressions,clicks,spend,conversions",
                    "time_range": f'{{"since":"{start}","until":"{end}"}}',
                    "breakdowns": "country",
                    "level": "account",
                },
            )
            region = self._request_paginated(
                f"{self.ad_account_id}/insights",
                {
                    "fields": "impressions,clicks,spend,conversions",
                    "time_range": f'{{"since":"{start}","until":"{end}"}}',
                    "breakdowns": "region",
                    "level": "account",
                },
            )

        return {
            "age_gender": age_gender,
            "age_gender_ad": age_gender_ad,
            "device": device,
            "country": country,
            "region": region,
        }

    def _fetch_adset_demo_targeting(self, adset_ids: set[str]) -> dict[str, dict]:
        """Género y rango de edad segmentados de cada conjunto, de a 50 por llamada.

        Incluye conjuntos pausados o archivados: lo que importa es que hayan
        entregado en la ventana. ``genders`` vacío = los dos géneros.
        """
        out: dict[str, dict] = {}
        ids = sorted(adset_ids)
        for i in range(0, len(ids), 50):
            data = self._request("", {"ids": ",".join(ids[i:i + 50]), "fields": "targeting{genders,age_min,age_max}"})
            if not isinstance(data, dict):
                continue
            for adset_id, obj in data.items():
                t = (obj or {}).get("targeting") if isinstance(obj, dict) else None
                if t is not None:
                    out[adset_id] = {"genders": t.get("genders") or [], "age_min": t.get("age_min"),
                                     "age_max": t.get("age_max")}
            time.sleep(0.2)
        logger.info("Meta Ads: segmentación de %d conjuntos", len(out))
        return out

    def _fetch_targeting_insights(self, start: str, end: str) -> tuple[list[dict], list[dict]]:
        """
        Extrae intereses y comportamientos del targeting de los conjuntos
        de anuncios activos, y por cada adset registra qué tipo de público
        usa (custom audience / lookalike / solo intereses = frío).
        """
        # Obtener ad sets activos
        adsets = self._request_paginated(
            f"{self.ad_account_id}/adsets",
            {
                "fields": "id,name,targeting,effective_status",
                "filtering": '[{"field":"effective_status","operator":"IN","value":["ACTIVE"]}]',
            },
        )

        interests: list[dict] = []
        adset_targeting: list[dict] = []
        seen = set()

        for adset in adsets:
            targeting = adset.get("targeting", {}) or {}
            # Público del adset: custom audiences (retargeting/lookalike) vs frío
            custom = [a.get("name", "") for a in targeting.get("custom_audiences", []) or []]
            excluded = [a.get("name", "") for a in targeting.get("excluded_custom_audiences", []) or []]
            flex = targeting.get("flexible_spec", []) or []
            flex_interests = any(f.get("interests") or f.get("behaviors") for f in flex)
            adset_targeting.append({
                "adset": adset.get("name", ""),
                "custom_audiences": custom,
                "excluded_custom_audiences": excluded,
                "lookalike": any("lookalike" in c.lower() or "similar" in c.lower() for c in custom),
                "has_interests": bool(targeting.get("interests") or targeting.get("behaviors") or flex_interests),
                "advantage_audience": bool((targeting.get("targeting_automation") or {}).get("advantage_audience")),
                "audience_type": "caliente" if custom else "frio",
            })
            # Intereses
            for interest in targeting.get("interests", []):
                key = interest.get("id") or interest.get("name")
                if key and key not in seen:
                    seen.add(key)
                    interests.append({
                        "id": interest.get("id"),
                        "name": interest.get("name", ""),
                        "type": "interest",
                        "adset": adset.get("name", ""),
                    })
            # Comportamientos
            for behavior in targeting.get("behaviors", []):
                key = behavior.get("id") or behavior.get("name")
                if key and key not in seen:
                    seen.add(key)
                    interests.append({
                        "id": behavior.get("id"),
                        "name": behavior.get("name", ""),
                        "type": "behavior",
                        "adset": adset.get("name", ""),
                    })
            # Datos demográficos del targeting
            for demo_key in ["life_events", "industries", "income", "family_statuses"]:
                for item in targeting.get(demo_key, []):
                    key = item.get("id") or item.get("name")
                    if key and key not in seen:
                        seen.add(key)
                        interests.append({
                            "id": item.get("id"),
                            "name": item.get("name", ""),
                            "type": demo_key,
                            "adset": adset.get("name", ""),
                        })

        return interests, adset_targeting

    def _fetch_ad_creatives(self, start: str, end: str) -> list[dict]:
        """Trae el copy real (título, texto, CTA) de los anuncios de la cuenta."""
        ads = self._request_paginated(
            f"{self.ad_account_id}/ads",
            {
                "fields": (
                    "id,name,effective_status,"
                    "creative{id,title,body,object_story_spec,"
                    "call_to_action_type,asset_feed_spec}"
                ),
            },
        )
        return [self._extract_ad_copy(ad) for ad in ads]

    @staticmethod
    def _extract_ad_copy(ad: dict) -> dict[str, Any]:
        """Extrae el texto/copy legible de un anuncio, sea cual sea su formato."""
        creative = ad.get("creative", {}) or {}
        story = creative.get("object_story_spec", {}) or {}

        body = creative.get("body", "")
        title = creative.get("title", "")
        cta = creative.get("call_to_action_type", "")

        link_data = story.get("link_data", {})
        if link_data:
            body = body or link_data.get("message", "")
            title = title or link_data.get("name", "")
            cta = cta or (link_data.get("call_to_action", {}) or {}).get("type", "")
            if not body and link_data.get("child_attachments"):
                cards = [c.get("name", "") for c in link_data["child_attachments"] if c.get("name")]
                if cards:
                    title = title or " | ".join(cards)

        video_data = story.get("video_data", {})
        if video_data:
            body = body or video_data.get("message", "")
            title = title or video_data.get("title", "")
            cta = cta or (video_data.get("call_to_action", {}) or {}).get("type", "")

        afs = creative.get("asset_feed_spec", {}) or {}
        if afs and not body:
            bodies = afs.get("bodies", [])
            titles = afs.get("titles", [])
            if bodies:
                body = " / ".join(b.get("text", "") for b in bodies if b.get("text"))
            if titles:
                title = " / ".join(t.get("text", "") for t in titles if t.get("text"))

        return {
            "ad_id": str(ad.get("id", "")),
            "ad_name": ad.get("name", ""),
            "status": ad.get("effective_status", ""),
            "title": title,
            "body": body,
            "cta": cta,
        }

    def _fetch_placement_breakdown(self, start: str, end: str) -> list[dict]:
        """Desglosa impresiones/gasto por plataforma y ubicación (Feed, Reels, Stories...)."""
        data = self._request_paginated(
            f"{self.ad_account_id}/insights",
            {
                "fields": "impressions,spend,actions",
                "time_range": f'{{"since":"{start}","until":"{end}"}}',
                "breakdowns": "publisher_platform,platform_position",
                "level": "account",
            },
        )
        return data if isinstance(data, list) else []

    def _fetch_custom_audiences(self) -> list[dict]:
        """Trae las custom audiences/lookalikes ya guardadas en la cuenta (solo metadata, sin usuarios)."""
        data = self._request_paginated(
            f"{self.ad_account_id}/customaudiences",
            {"fields": "name,subtype,approximate_count_upper_bound,description"},
        )
        audiences = []
        for a in data if isinstance(data, list) else []:
            name = str(a.get("name", "")).strip()
            # Descartar públicos sin nombre útil (".", "-", "," etc.)
            if len(name) <= 2:
                continue
            audiences.append({
                "name": name,
                "subtype": a.get("subtype", ""),
                "size": a.get("approximate_count_upper_bound", 0),
                "description": a.get("description", ""),
            })
        return audiences

    # Campos de formulario que nos interesa agregar (regex sobre el nombre del campo)
    _LEAD_FIELD_PATTERNS = {
        "model_interest": r"model|modelo|veh[ií]culo",
        "payment_method": r"pago|financia|contado",
        "city": r"ciudad|city|localidad",
        "purchase_intent": r"inter[eé]s",
    }

    @staticmethod
    def _empty_lead_agg() -> dict[str, Any]:
        return {"total_leads": 0, "model_interest": Counter(), "payment_method": Counter(),
                "city": Counter(), "purchase_intent": Counter()}

    @staticmethod
    def _merge_lead_agg(target: dict[str, Any], source: dict[str, Any]) -> None:
        target["total_leads"] += source["total_leads"]
        for key in ("model_interest", "payment_method", "city", "purchase_intent"):
            target[key].update(source[key])

    # Los valores de un formulario no respetan el nombre del campo: una
    # pregunta llamada "interes" puede responderse con un plazo de compra
    # ("en_1_a_3_meses") o con un método de pago ("financiación"). Se
    # reclasifica por el CONTENIDO del valor antes de acumular.
    _VALOR_ES_PLAZO = re.compile(
        r"inmediat|mes|averigu|evaluando|semana|a_[0-9]|[0-9]_a_|proximo|futuro|año|anio"
    )
    _VALOR_ES_PAGO = re.compile(r"financ|contado|credito|crédito|banc")

    def _clasificar_valor(self, agg_key: str, value: str) -> str:
        """Corrige la categoría cuando el valor contradice el nombre del campo.

        Funciona en ambos sentidos: un campo "interés" respondido con un plazo
        va a ``purchase_intent``, y un campo "cuándo comprás" respondido con un
        modelo ("x70") va a ``model_interest``.
        """
        v = value.lower()
        es_plazo = bool(self._VALOR_ES_PLAZO.search(v))
        es_pago = bool(self._VALOR_ES_PAGO.search(v))

        if es_plazo:
            return "purchase_intent"
        if es_pago:
            return "payment_method"
        # No es plazo ni pago: si vino etiquetado como intención o pago, en
        # realidad es un modelo. La ciudad se respeta (viene de un campo
        # dedicado y sus valores son nombres propios, no clasificables aquí).
        if agg_key in ("purchase_intent", "payment_method"):
            return "model_interest"
        return agg_key

    # Etiquetas que identifican al grupo/concesionaria, no a una marca de auto.
    _ETIQUETAS_GENERICAS = {"Santa Rosa", "Multimarcas"}

    def _marca_de_pagina(self, page_name: str) -> str:
        """Mapea el nombre de una página a una de las marcas del portfolio.

        Usa las etiquetas ya declaradas en ``ad_account_ids``; si ninguna
        coincide, devuelve el nombre de la página tal cual para no perder
        los leads en un cajón genérico.
        """
        nombre = page_name.lower()
        etiquetas = {a["label"] for a in self.ad_accounts if a.get("label")}

        coincidencias = [l for l in etiquetas if l.lower() in nombre]
        if not coincidencias:
            return page_name.strip()

        # "Santa Rosa" es el grupo, no una marca: si la página nombra además
        # una marca concreta ("Renault Santa Rosa Paraguay"), esa manda.
        concretas = [l for l in coincidencias if l not in self._ETIQUETAS_GENERICAS]
        candidatas = concretas or coincidencias

        # Entre marcas concretas, la coincidencia más larga es la más específica.
        return max(candidatas, key=len)

    def _collect_leads_from_pages(self, merged: dict[str, Any], days_back: int = 90) -> None:
        """Recorre las páginas una vez y acumula sus leads por marca."""
        since = datetime.now(timezone.utc) - timedelta(days=days_back)
        pages = self._fetch_pages()
        logger.info("Meta Ads: leyendo leads de %d páginas (ventana %dd)", len(pages), days_back)

        for page in pages:
            nombre = page.get("name", "")
            marca = self._marca_de_pagina(nombre)
            agg = self._fetch_lead_insights_by_page(page, since=since, marca=marca)
            if not agg:
                continue
            destino = merged["leads_by_brand"].setdefault(marca, self._empty_lead_agg())
            self._merge_lead_agg(destino, agg)
            logger.info("Meta Ads: %s → %s: %d leads", nombre, marca, agg["total_leads"])

    def _fetch_pages(self) -> list[dict[str, str]]:
        """Devuelve las páginas accesibles, cada una con su page access token.

        Los formularios de leads cuelgan de la PÁGINA (no de la cuenta
        publicitaria) y exigen el token de esa página, no el de la app.
        """
        pages = self._request_paginated(
            "me/accounts", {"fields": "id,name,access_token"}, limit=200
        )
        return [p for p in pages if p.get("access_token")]

    def _fetch_lead_insights_by_page(
        self, page: dict[str, str], since: datetime | None = None, marca: str = ""
    ) -> dict[str, Any] | None:
        """
        Agrega las respuestas de los formularios de leads de una página
        (modelo elegido, método de pago, ciudad, interés) SIN guardar
        nombre, teléfono ni email — solo conteos. Los datos crudos del
        lead nunca salen de esta función: para el cruce con las ventas
        solo sale una clave cifrada (``ventas_meta.claves_de_lead``) con la
        campaña de la que vino.
        """
        from src.generators.ventas_meta import claves_de_lead
        page_token = page.get("access_token", "")
        forms = self._request_paginated(
            f"{page['id']}/leadgen_forms",
            {"fields": "id,name,leads_count"},
            token=page_token,
        )
        agg = self._empty_lead_agg()
        has_data = False

        for form in forms if isinstance(forms, list) else []:
            if not form.get("leads_count"):
                continue
            leads = self._request_paginated(
                f"{form['id']}/leads",
                {"fields": "created_time,field_data,campaign_id,campaign_name,ad_name,is_organic"},
                limit=200,
                token=page_token,
            )
            for lead in leads:
                if since:
                    creado = lead.get("created_time", "")
                    try:
                        if creado and datetime.fromisoformat(
                            creado.replace("Z", "+00:00")
                        ) < since:
                            continue  # fuera de la ventana de days_back
                    except ValueError:
                        pass  # sin fecha parseable: se cuenta igual
                has_data = True
                agg["total_leads"] += 1
                clave = claves_de_lead(lead, marca)
                if clave:
                    self.claves_leads.append(clave)
                for field in lead.get("field_data", []):
                    field_name = str(field.get("name", "")).lower()
                    values = field.get("values", [])
                    if not values:
                        continue
                    value = str(values[0]).strip()
                    if not value:
                        continue
                    for agg_key, pattern in self._LEAD_FIELD_PATTERNS.items():
                        if re.search(pattern, field_name):
                            destino = self._clasificar_valor(agg_key, value)
                            agg[destino][value] += 1
                            break

        return agg if has_data else None

    def _fetch_campaign_insights(self, start: str, end: str) -> list[dict]:
        """Extrae rendimiento de campañas."""
        data = self._request_paginated(
            f"{self.ad_account_id}/insights",
            {
                "fields": (
                    "account_id,account_name,campaign_name,campaign_id,impressions,clicks,spend,"
                    "conversions,actions,ctr,cpc,cpm,reach,frequency,"
                    "purchase_roas,cost_per_action_type"
                ),
                "time_range": f'{{"since":"{start}","until":"{end}"}}',
                "level": "campaign",
            },
        )
        return data if isinstance(data, list) else []