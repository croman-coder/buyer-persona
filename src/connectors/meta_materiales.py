"""
Materiales de Meta: de qué está hecho cada anuncio y cómo rindió, mes a mes y por ubicación.

Pedido de Croman (05-10-2026): poner en la nota de cada marca qué materiales funcionan
mejor según el historial (gráfica, video, reel, carrusel), qué baja el costo por lead y
qué convierte más. Este módulo solo LEE de la Graph API; el análisis y las notas están en
``src/generators/materiales_meta.py``.

Por cada cuenta del portfolio, en los últimos N meses:
- rendimiento de cada anuncio por mes (gasto, impresiones, clics, formularios, chats y
  vistas de video: 3 segundos, 25/50/75/100 % y ThruPlay);
- rendimiento de cada anuncio por ubicación (Feed, Reels, Stories, Marketplace…);
- de qué está hecho: imágenes, videos o carrusel, la duración de cada video y si hay
  versión vertical (9:16) de cada pieza.

Son agregados de Meta: ningún dato de personas.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

ACCION_FORMULARIO = "lead"
ACCION_CHAT = "onsite_conversion.messaging_conversation_started_7d"
ACCION_VIDEO_3S = "video_view"

CAMPOS_MES = (
    "account_name,ad_id,ad_name,campaign_id,campaign_name,objective,optimization_goal,spend,impressions,reach,"
    "inline_link_clicks,actions,video_thruplay_watched_actions,video_p25_watched_actions,"
    "video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions"
)
CAMPOS_UBICACION = "ad_id,spend,impressions,inline_link_clicks,actions"
CAMPOS_CREATIVO = (
    "creative{object_type,video_id,image_hash,asset_feed_spec,object_story_spec,object_story_id,"
    "source_instagram_media_id,actor_id}"
)
LOTE_IDS = 50          # la Graph API acepta hasta 50 ids por pedido
LOTE_IMAGENES = 100
MAX_PAGINAS_VIDEOS = 25


def rango(meses: int, hoy: date | None = None) -> tuple[str, str]:
    """Desde el día 1 del mes de hace ``meses - 1`` meses hasta hoy (el mes actual va incompleto)."""
    hoy = hoy or date.today()
    anio, mes = hoy.year, hoy.month - (meses - 1)
    while mes <= 0:
        anio, mes = anio - 1, mes + 12
    return date(anio, mes, 1).isoformat(), hoy.isoformat()


def _accion(fila: dict[str, Any], tipo: str, campo: str = "actions") -> float:
    return sum(float(a.get("value") or 0) for a in fila.get(campo) or [] if a.get("action_type") == tipo)


def _num(x: Any) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def fila_mes(f: dict[str, Any]) -> dict[str, Any]:
    """Una fila anuncio × mes, solo con lo que se usa."""
    return {
        "ad_id": str(f.get("ad_id", "")), "mes": str(f.get("date_start", ""))[:7],
        "campaign_id": str(f.get("campaign_id", "")), "campaign_name": f.get("campaign_name", ""),
        "objetivo": f.get("objective", ""), "optimizacion": f.get("optimization_goal", ""),
        "gasto": _num(f.get("spend")), "impresiones": int(_num(f.get("impressions"))),
        "alcance": int(_num(f.get("reach"))), "clics": int(_num(f.get("inline_link_clicks"))),
        "formularios": _accion(f, ACCION_FORMULARIO), "chats": _accion(f, ACCION_CHAT),
        "video_3s": _accion(f, ACCION_VIDEO_3S),
        "video_25": _accion(f, "video_view", "video_p25_watched_actions"),
        "video_50": _accion(f, "video_view", "video_p50_watched_actions"),
        "video_75": _accion(f, "video_view", "video_p75_watched_actions"),
        "video_100": _accion(f, "video_view", "video_p100_watched_actions"),
        "thruplay": _accion(f, "video_view", "video_thruplay_watched_actions"),
    }


def fila_ubicacion(f: dict[str, Any]) -> dict[str, Any]:
    return {
        "ad_id": str(f.get("ad_id", "")), "plataforma": f.get("publisher_platform", ""),
        "posicion": f.get("platform_position", ""), "gasto": _num(f.get("spend")),
        "impresiones": int(_num(f.get("impressions"))), "clics": int(_num(f.get("inline_link_clicks"))),
        "formularios": _accion(f, ACCION_FORMULARIO), "chats": _accion(f, ACCION_CHAT),
    }


def medios_de(creativo: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(ids de video, hashes de imagen) que usa el creativo, sin repetir."""
    afs = creativo.get("asset_feed_spec") or {}
    oss = creativo.get("object_story_spec") or {}
    link = oss.get("link_data") or {}
    videos = [creativo.get("video_id"), (oss.get("video_data") or {}).get("video_id")]
    videos += [v.get("video_id") for v in afs.get("videos") or []]
    videos += [c.get("video_id") for c in link.get("child_attachments") or []]
    imagenes = [i.get("hash") for i in afs.get("images") or []]
    imagenes += [c.get("image_hash") for c in link.get("child_attachments") or []]
    if not any(videos):
        # En un video, la imagen del creativo es la miniatura: no es una pieza aparte
        imagenes += [creativo.get("image_hash"), link.get("image_hash"), (oss.get("photo_data") or {}).get("image_hash")]
    unicos = lambda xs: list(dict.fromkeys(str(x) for x in xs if x))  # noqa: E731
    return unicos(videos), unicos(imagenes)


def formato_de(creativo: dict[str, Any]) -> str:
    """Imagen, Video, Carrusel o Mixto, según de qué está armado el creativo."""
    afs = creativo.get("asset_feed_spec") or {}
    oss = creativo.get("object_story_spec") or {}
    link = oss.get("link_data") or {}
    formatos = set(afs.get("ad_formats") or [])
    n_img, n_vid = len(afs.get("images") or []), len(afs.get("videos") or [])
    if "CAROUSEL" in formatos or len(link.get("child_attachments") or []) > 1:
        return "Carrusel"
    if n_img and n_vid:
        return "Mixto"
    if n_vid:
        return "Video"
    if n_img:
        return "Imagen"
    if creativo.get("video_id") or oss.get("video_data") or creativo.get("object_type") == "VIDEO":
        return "Video"
    if link or oss.get("photo_data") or creativo.get("image_hash") or creativo.get("object_type") in ("PHOTO", "SHARE"):
        return "Imagen"
    return "Sin dato"


def origen_de(creativo: dict[str, Any]) -> str:
    """«anuncio» si se armó en el administrador; si no, qué publicación se promocionó."""
    if creativo.get("asset_feed_spec") or creativo.get("object_story_spec"):
        return "anuncio"
    if creativo.get("source_instagram_media_id"):
        return "publicacion_instagram"
    if creativo.get("object_story_id"):
        return "publicacion_facebook"
    return "anuncio"


def _por_lotes(xs: list[str], n: int):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def leer_materiales(con: Any, meses: int = 6, hoy: date | None = None, hilos: int = 4) -> dict[str, Any]:
    """Lee todas las cuentas de ``con`` (un ``MetaAdsConnector``), de a ``hilos`` cuentas a la vez.

    Una cuenta caída no frena las demás. El límite de la API es por cuenta publicitaria, así
    que leer cuentas distintas en paralelo no lo agota; ``con._request`` reintenta si igual pasa.
    """
    desde, hasta = rango(meses, hoy)
    rango_json = json.dumps({"since": desde, "until": hasta})
    out: dict[str, Any] = {"desde": desde, "hasta": hasta, "meses": meses, "cuentas": {},
                           "anuncios": {}, "por_mes": [], "por_ubicacion": []}
    # Los videos subidos a una página (no a la cuenta) solo se leen con el token de esa página
    try:
        tokens = {str(p["id"]): p["access_token"] for p in con._fetch_pages()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Materiales Meta: sin tokens de página (%s); la duración de algunos videos queda sin dato", exc)
        tokens = {}
    with ThreadPoolExecutor(max_workers=max(1, hilos)) as pool:
        resultados = list(pool.map(lambda c: _leer_cuenta(con, c["id"], c["label"], rango_json, tokens),
                                   con.ad_accounts))
    for cuenta, res in zip(con.ad_accounts, resultados):
        if not res:
            continue
        act = cuenta["id"]
        out["cuentas"][act] = {"marca": cuenta["label"], "nombre": res["nombre"]}
        out["por_mes"].extend(res["filas"])
        out["por_ubicacion"].extend(res["ubic"])
        out["anuncios"].update(res["anuncios"])
    return out


def _leer_cuenta(con: Any, act: str, marca: str, rango_json: str, tokens: dict[str, str]) -> dict[str, Any] | None:
    try:
        filas = con._request_paginated(
            f"{act}/insights",
            {"level": "ad", "fields": CAMPOS_MES, "time_increment": "monthly", "time_range": rango_json},
            limit=500)
        nombre = next((f.get("account_name") for f in filas if f.get("account_name")), "")
        filas = [{**fila_mes(f), "cuenta": act} for f in filas if _num(f.get("spend")) > 0]
        if not filas:
            return None
        ubic = con._request_paginated(
            f"{act}/insights",
            {"level": "ad", "fields": CAMPOS_UBICACION, "breakdowns": "publisher_platform,platform_position",
             "time_range": rango_json},
            limit=500)
        ubic = [fila_ubicacion(f) for f in ubic if _num(f.get("spend")) > 0]
        anuncios = _leer_anuncios(con, act, marca, sorted({f["ad_id"] for f in filas}), tokens)
    except Exception as exc:  # noqa: BLE001 — una cuenta caída no debe tumbar el resto
        logger.warning("Materiales Meta: falló la cuenta %s (%s): %s", act, marca, exc)
        return None
    logger.info("Materiales Meta: %s (%s): %d anuncios, %d filas mes, %d filas ubicación",
                act, marca, len(anuncios), len(filas), len(ubic))
    return {"nombre": nombre, "filas": filas, "ubic": ubic, "anuncios": anuncios}


def _info_video(v: dict[str, Any]) -> dict[str, Any]:
    formatos = v.get("format") or [{}]
    nativo = next((f for f in formatos if f.get("filter") == "native"), None) or max(formatos, key=lambda f: f.get("width") or 0)
    return {"seg": v.get("length"), "ancho": nativo.get("width"), "alto": nativo.get("height")}


def _leer_anuncios(con: Any, act: str, marca: str, ids: list[str],
                   tokens: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """Creativo de cada anuncio + duración/orientación de sus videos e imágenes."""
    tokens = tokens or {}
    anuncios: dict[str, dict[str, Any]] = {}
    campos = f"name,created_time,{CAMPOS_CREATIVO}"
    for lote in _por_lotes(ids, LOTE_IDS):
        data = con._request("", {"ids": ",".join(lote), "fields": campos})
        if not data:
            # Un id que ya no se puede leer hace fallar el lote entero: de a uno
            data = {}
            for ad_id in lote:
                data.update({ad_id: con._request(ad_id, {"fields": campos})})
        for ad_id, ad in (data or {}).items():
            if not isinstance(ad, dict) or not ad:
                continue
            cr = ad.get("creative") or {}
            videos, imagenes = medios_de(cr)
            anuncios[str(ad_id)] = {
                "nombre": ad.get("name", ""), "creado": str(ad.get("created_time", ""))[:10],
                "cuenta": act, "marca": marca, "formato": formato_de(cr), "origen": origen_de(cr),
                "pagina": str((cr.get("object_story_spec") or {}).get("page_id") or cr.get("actor_id") or ""),
                "ig_media": cr.get("source_instagram_media_id") or "",
                "videos": [{"id": v} for v in videos], "imagenes": [{"hash": h} for h in imagenes],
            }
    # Duración y tamaño de los videos. El nodo del video no se lee con el token de la app:
    # 1) los subidos a la página, con el token de esa página; 2) el resto, en la lista de
    # videos de la cuenta publicitaria.
    info_video: dict[str, dict[str, Any]] = {}
    por_pagina: dict[str, set[str]] = {}
    for a in anuncios.values():
        if a["videos"] and a["pagina"] in tokens:
            por_pagina.setdefault(a["pagina"], set()).update(v["id"] for v in a["videos"])
    for pagina, vids in por_pagina.items():
        for lote in _por_lotes(sorted(vids), LOTE_IDS):
            data = con._request("", {"ids": ",".join(lote), "fields": "length,format{width,height,filter}"},
                                token=tokens[pagina])
            for vid, v in (data or {}).items():
                if isinstance(v, dict) and v.get("length"):
                    info_video[str(vid)] = _info_video(v)
    faltan = {v["id"] for a in anuncios.values() for v in a["videos"]} - set(info_video)
    if faltan:
        params: dict[str, Any] = {"fields": "id,length,format{width,height,filter}", "limit": 200}
        paginas = 0
        while faltan - set(info_video) and paginas < MAX_PAGINAS_VIDEOS:
            data = con._request(f"{act}/advideos", params)
            paginas += 1
            for v in (data or {}).get("data", []):
                info_video[str(v.get("id"))] = _info_video(v)
            despues = (((data or {}).get("paging") or {}).get("cursors") or {}).get("after")
            if not despues or not (data or {}).get("paging", {}).get("next"):
                break
            params = {"fields": params["fields"], "limit": 200, "after": despues}
    hashes = sorted({i["hash"] for a in anuncios.values() for i in a["imagenes"]})
    info_imagen: dict[str, dict[str, Any]] = {}
    for lote in _por_lotes(hashes, LOTE_IMAGENES):
        data = con._request(f"{act}/adimages", {"hashes": json.dumps(lote), "fields": "hash,width,height",
                                                "limit": LOTE_IMAGENES})
        for im in (data or {}).get("data", []):
            info_imagen[str(im.get("hash"))] = {"ancho": im.get("width"), "alto": im.get("height")}
    # Publicaciones de Instagram promocionadas: ¿era un reel?
    ig_ids = sorted({a["ig_media"] for a in anuncios.values() if a["origen"] == "publicacion_instagram" and a["ig_media"]})
    info_ig: dict[str, dict[str, Any]] = {}
    for lote in _por_lotes(ig_ids, LOTE_IDS):
        data = con._request("", {"ids": ",".join(lote), "fields": "media_type,media_product_type"})
        info_ig.update({str(k): v for k, v in (data or {}).items() if isinstance(v, dict)})
    for a in anuncios.values():
        for v in a["videos"]:
            v.update(info_video.get(v["id"], {}))
        for im in a["imagenes"]:
            im.update(info_imagen.get(im["hash"], {}))
        ig = info_ig.get(a.pop("ig_media"), {})
        if ig:
            a["ig_tipo"] = ig.get("media_product_type", "")
            if ig.get("media_type") == "VIDEO":
                a["formato"] = "Video"
            elif ig.get("media_type") == "CAROUSEL_ALBUM":
                a["formato"] = "Carrusel"
            elif ig.get("media_type") == "IMAGE":
                a["formato"] = "Imagen"
    return anuncios
