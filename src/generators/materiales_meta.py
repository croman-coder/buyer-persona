"""
Qué materiales funcionan en Meta, marca por marca, con el historial de los últimos meses.

Pedido de Croman (05-10-2026): en la nota de cada marca, qué rinde mejor (gráfica, video,
reel, carrusel), qué baja el costo por lead y qué convierte más.

Responde cuatro preguntas por marca, siempre dentro de un mismo destino (formularios por
un lado, WhatsApp por otro):
1. ¿Imagen, video o carrusel?
2. ¿Reels, Stories o Feed?
3. ¿Video corto o largo? ¿Con o sin versión vertical (9:16)?
4. ¿Qué anuncios rindieron mejor y cuáles gastaron sin traer?

**Los materiales se comparan solo dentro de campañas comparables.** Las cuentas de asesores
sacan leads mucho más baratos que la de la marca (GWM, may-oct 2026: USD 1,38 contra 3,10)
y los formularios de volumen más baratos que los de calidad. Si se mezclan, gana el formato
que más usaron los asesores, no el que mejor funciona: así salía que «la imagen sin versión
vertical» era la más barata en cinco marcas, y era solo porque los asesores usan una sola
imagen. Por eso cada comparación es un promedio de las diferencias dentro de cada contexto
(tipo de cuenta × tipo de formulario) donde se usaron los dos materiales, y se mira además
si la diferencia se repite mes a mes.

Los datos los lee ``src/connectors/meta_materiales.py``. Las ventas por anuncio salen del
cruce de ``src/generators/ventas_meta.py`` (solo conteos por anuncio).
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.generators.ventas_meta import es_cuenta_de_asesor

NOMBRE_FORMATO = {"Imagen": "Imagen (gráfica)", "Video": "Video", "Carrusel": "Carrusel",
                  "Mixto": "Imagen y video juntos", "Sin dato": "Sin dato"}
ORDEN_FORMATOS = ("Imagen", "Video", "Carrusel", "Mixto", "Sin dato")
DESTINOS = ("formulario", "chat")
NOMBRE_DESTINO = {"formulario": "Formularios", "chat": "WhatsApp y mensajes", "otro": "Alcance, tráfico e interacción"}
RESULTADO = {"formulario": ("lead", "leads"), "chat": ("conversación", "conversaciones")}
GENERO = {"lead": ("el", "barato"), "conversación": ("la", "barata")}
OPT_FORMULARIO = {"LEAD_GENERATION", "QUALITY_LEAD"}
OPT_CHAT = {"CONVERSATIONS", "REPLIES", "MESSAGING_PURCHASE_CONVERSION", "MESSAGING_APPOINTMENT_CONVERSION"}

# Contexto = tipo de cuenta × tipo de formulario: dentro de cada uno el costo es comparable
CONTEXTOS = ("marca|calidad", "marca|volumen", "asesor|calidad", "asesor|volumen", "marca", "asesor")
CONTEXTO_CORTO = {"marca|calidad": "Marca · calidad", "marca|volumen": "Marca · volumen",
                  "asesor|calidad": "Asesores · calidad", "asesor|volumen": "Asesores · volumen",
                  "marca": "Cuenta de la marca", "asesor": "Cuentas de asesores", "": "—"}
CONTEXTO_FRASE = {"marca|calidad": "en la cuenta de la marca (formularios de calidad)",
                  "marca|volumen": "en la cuenta de la marca (formularios de volumen)",
                  "asesor|calidad": "en las cuentas de asesores (formularios de calidad)",
                  "asesor|volumen": "en las cuentas de asesores (formularios de volumen)",
                  "marca": "en la cuenta de la marca", "asesor": "en las cuentas de asesores"}

UBICACION = {
    ("facebook", "feed"): "Feed", ("instagram", "feed"): "Feed", ("facebook", "facebook_profile_feed"): "Feed",
    ("instagram", "instagram_profile_feed"): "Feed", ("instagram", "instagram_explore"): "Feed",
    ("instagram", "instagram_explore_grid_home"): "Feed", ("threads", "threads_feed"): "Feed",
    ("facebook", "facebook_reels"): "Reels", ("instagram", "instagram_reels"): "Reels",
    ("facebook", "facebook_stories"): "Stories", ("instagram", "instagram_stories"): "Stories",
    ("messenger", "messenger_stories"): "Stories", ("whatsapp", "status"): "Estados de WhatsApp",
    ("facebook", "facebook_reels_overlay"): "Banner sobre Reels y videos",
    ("facebook", "instream_video"): "Banner sobre Reels y videos",
    ("facebook", "marketplace"): "Marketplace y búsqueda", ("facebook", "search"): "Marketplace y búsqueda",
    ("instagram", "instagram_search"): "Marketplace y búsqueda",
}
ORDEN_UBICACIONES = ("Feed", "Reels", "Stories", "Estados de WhatsApp", "Banner sobre Reels y videos",
                     "Marketplace y búsqueda", "Audience Network (otras apps)", "Otras")
PRINCIPALES = ("Feed", "Reels", "Stories")   # donde se decide el tamaño de la pieza
TRAMOS = ((15, "Hasta 15 s"), (30, "16 a 30 s"), (60, "31 a 60 s"), (float("inf"), "Más de 60 s"))
ORDEN_TRAMOS = tuple(t for _, t in TRAMOS) + ("Sin dato",)
VERTICALES = ("Con versión vertical", "Sin versión vertical", "Sin dato")
ORDEN_VERTICAL = tuple(f"{fo}|{v}" for fo in ORDEN_FORMATOS for v in VERTICALES)
ORDEN_ORIGEN = ("anuncio", "publicacion_instagram", "publicacion_facebook")
NOMBRE_ORIGEN = {"anuncio": "Armado como anuncio", "publicacion_instagram": "Publicación de Instagram promocionada",
                 "publicacion_facebook": "Publicación de Facebook promocionada"}
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")

# Por debajo de esto la diferencia es ruido: la fila se muestra, pero no entra en las conclusiones.
MIN_GASTO = 50.0
MIN_RESULTADOS = 20
MIN_ANUNCIOS = 3              # un formato o duración con menos anuncios depende de una sola pieza
MIN_RESULTADOS_CONTEXTO = 20  # para comparar dos materiales dentro de un mismo contexto
MIN_RESULTADOS_MES = 10       # ídem, dentro de un mes
MIN_GASTO_CONTEXTO = 100.0    # un contexto con menos inversión no lleva columna propia
DIFERENCIA = 0.15             # 15 %: menos que eso es un empate
MIN_VENTAS = 5                # ventas cruzadas para listar la conversión por formato
MIN_ANUNCIO_GASTO, MIN_ANUNCIO_RESULTADOS = 30.0, 10


# ---------------------------------------------------------------------------
# Clasificación
# ---------------------------------------------------------------------------

def destino_de(f: dict[str, Any]) -> str:
    """formulario, chat u otro, según lo que optimiza el conjunto (y si no, lo que trajo)."""
    opt = f.get("optimizacion", "")
    if opt in OPT_FORMULARIO:
        return "formulario"
    if opt in OPT_CHAT:
        return "chat"
    if f.get("formularios") or f.get("chats"):
        return "formulario" if f.get("formularios", 0) >= f.get("chats", 0) else "chat"
    return "otro"


def contexto_de(tipo_cuenta: str, destino: str, optimizacion: str) -> str:
    """«marca|calidad», «asesor|volumen»… (en chats solo cuenta el tipo de cuenta)."""
    if destino == "formulario":
        return f"{tipo_cuenta}|{'calidad' if optimizacion == 'QUALITY_LEAD' else 'volumen'}"
    return tipo_cuenta


def ubicacion_de(plataforma: str, posicion: str) -> str:
    if plataforma == "audience_network":
        return "Audience Network (otras apps)"
    return UBICACION.get((plataforma, posicion), "Otras")


def duracion_de(anuncio: dict[str, Any]) -> float | None:
    segs = [float(v["seg"]) for v in anuncio.get("videos", []) if v.get("seg")]
    return max(segs) if segs else None


def tramo_de(segundos: float | None) -> str:
    if segundos is None:
        return "Sin dato"
    return next(nombre for tope, nombre in TRAMOS if segundos <= tope)


def vertical_de(anuncio: dict[str, Any]) -> str:
    """«Con versión vertical» si alguna pieza es 9:16 (o casi), que es la que llena Reels y Stories."""
    medidas = [(m.get("ancho"), m.get("alto")) for m in anuncio.get("videos", []) + anuncio.get("imagenes", [])]
    medidas = [(a, h) for a, h in medidas if a and h]
    if not medidas:
        return "Sin dato"
    return "Con versión vertical" if any(h / a >= 1.5 for a, h in medidas) else "Sin versión vertical"


def _claves(anuncio: dict[str, Any]) -> dict[str, str]:
    """Dimensiones en las que se compara un anuncio."""
    formato = anuncio.get("formato", "Sin dato")
    claves = {"formato": formato, "vertical": f"{formato}|{vertical_de(anuncio)}",
              "origen": anuncio.get("origen", "anuncio")}
    if formato in ("Video", "Mixto"):
        claves["tramo"] = tramo_de(duracion_de(anuncio))
    return claves


# ---------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------

CAMPOS_SUMA = ("gasto", "impresiones", "clics", "formularios", "chats", "video_3s", "video_100", "thruplay")


def _vacio() -> dict[str, Any]:
    return {**{c: 0.0 for c in CAMPOS_SUMA}, "anuncios": set(), "leads_cruce": 0, "ventas": 0}


def _sumar(destino: dict[str, Any], f: dict[str, Any]) -> None:
    for c in CAMPOS_SUMA:
        destino[c] += float(f.get(c) or 0)
    if "ad_id" in f:
        destino["anuncios"].add(f["ad_id"])
    else:
        destino["anuncios"] |= f.get("anuncios", set())


def _resultados(s: dict[str, Any], destino: str) -> float:
    return s["formularios"] if destino == "formulario" else s["chats"] if destino == "chat" else 0.0


def _metricas(s: dict[str, Any], destino: str) -> dict[str, Any]:
    res = _resultados(s, destino)
    return {
        "anuncios": len(s["anuncios"]), "gasto": round(s["gasto"], 2), "impresiones": int(s["impresiones"]),
        "clics": int(s["clics"]), "resultados": int(round(res)),
        "costo": round(s["gasto"] / res, 2) if res else None,
        "ctr": round(s["clics"] / s["impresiones"] * 100, 2) if s["impresiones"] else None,
        "cada_100_clics": round(res / s["clics"] * 100, 1) if s["clics"] else None,
        "cpm": round(s["gasto"] / s["impresiones"] * 1000, 2) if s["impresiones"] else None,
        "mira_3s": round(s["video_3s"] / s["impresiones"] * 100, 1) if s["impresiones"] and s["video_3s"] else None,
        "completo": round(s["video_100"] / s["video_3s"] * 100, 1) if s["video_3s"] else None,
        "leads_cruce": s["leads_cruce"], "ventas": s["ventas"],
        "ventas_cada_100": round(s["ventas"] / s["leads_cruce"] * 100, 1) if s["leads_cruce"] else None,
        "suficiente": s["gasto"] >= MIN_GASTO and res >= MIN_RESULTADOS,
    }


def _tabla(grupos: dict[str, dict[str, Any]], destino: str, orden: tuple[str, ...],
           min_anuncios: int = 1) -> list[dict[str, Any]]:
    filas = []
    for clave in sorted(grupos, key=lambda k: orden.index(k) if k in orden else len(orden)):
        m = _metricas(grupos[clave], destino)
        if m["gasto"] > 0:
            m["suficiente"] = m["suficiente"] and m["anuncios"] >= min_anuncios
            filas.append({"clave": clave, **m})
    total = sum(f["gasto"] for f in filas)
    for f in filas:
        f["pct_gasto"] = round(f["gasto"] / total * 100, 1) if total else 0
    return filas


def _juntar(celdas: dict[tuple, dict[str, Any]], clave) -> dict[Any, dict[str, Any]]:
    """Suma las celdas del cubo (contexto, clave, mes) agrupando por ``clave(k)``."""
    out: dict[Any, dict[str, Any]] = defaultdict(_vacio)
    for k, s in celdas.items():
        _sumar(out[clave(k)], s)
    return out


def _estratos(cubo: dict[tuple, dict[str, Any]], clave: str, destino: str,
              mes: str | None = None) -> dict[str, list[float]]:
    """contexto → [gasto, resultados] de una clave (en un mes, o en toda la ventana)."""
    out: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for (ctx, c, me), s in cubo.items():
        if c == clave and (mes is None or me == mes):
            out[ctx][0] += s["gasto"]
            out[ctx][1] += _resultados(s, destino)
    return out


def _pares(cubo: dict, a: str, b: str, destino: str, mes: str | None = None,
           minimo: int = MIN_RESULTADOS_CONTEXTO) -> list[tuple[str, float, float, float, float]]:
    """Contextos donde se usaron A y B con muestra: (contexto, gasto A, resultados A, gasto B, resultados B)."""
    ea, eb = _estratos(cubo, a, destino, mes), _estratos(cubo, b, destino, mes)
    return [(ctx, ea[ctx][0], ea[ctx][1], eb[ctx][0], eb[ctx][1]) for ctx in ea
            if ctx in eb and min(ea[ctx][1], eb[ctx][1]) >= minimo and ea[ctx][0] > 0 and eb[ctx][0] > 0]


def _razon(pares: list[tuple[str, float, float, float, float]]) -> float:
    """Costo de A ÷ costo de B: promedio geométrico de cada contexto, pesado por resultados."""
    pesos = [ra + rb for _, _, ra, _, rb in pares]
    logs = [math.log((ga / ra) / (gb / rb)) for _, ga, ra, gb, rb in pares]
    return math.exp(sum(p * x for p, x in zip(pesos, logs)) / sum(pesos))


def _comparar(cubo: dict, candidatos: list[dict[str, Any]], destino: str, hoy: date) -> dict[str, Any]:
    """Compara los dos materiales más usados, solo dentro de contextos comparables, y mira si se repite mes a mes."""
    if not candidatos:
        return {"estado": "sin_muestra"}
    if len(candidatos) == 1:
        return {"estado": "uno", "ganador": candidatos[0]["clave"]}
    a, b = candidatos[0]["clave"], candidatos[1]["clave"]
    pares = _pares(cubo, a, b, destino)
    if not pares:
        return {"estado": "sin_comparables", "a": a, "b": b}
    razon = _razon(pares)
    ganador, rival = (a, b) if razon < 1 else (b, a)
    dif = 1 - min(razon, 1 / razon)
    detalle = []
    for ctx, ga, ra, gb, rb in sorted(pares, key=lambda x: -(x[2] + x[4]))[:3]:
        costo = {a: ga / ra, b: gb / rb}
        detalle.append({"contexto": ctx, "ganador": round(costo[ganador], 2), "rival": round(costo[rival], 2),
                        "resultados": int(ra + rb)})
    out: dict[str, Any] = {
        "estado": "gana" if dif >= DIFERENCIA else "empate", "ganador": ganador, "rival": rival,
        "dif": round(dif, 3), "base": int(sum(x[2] + x[4] for x in pares)), "contextos": len(pares),
        "detalle": detalle}
    actual = hoy.isoformat()[:7]
    ganados = comparables = 0
    for mes in sorted({k[2] for k in cubo if k[2] != actual}):
        pm = _pares(cubo, ganador, rival, destino, mes, MIN_RESULTADOS_MES)
        if pm:
            comparables += 1
            ganados += _razon(pm) < 1
    out["meses_ganados"], out["meses"] = ganados, comparables
    # Un tercero, menos usado, que le gana claro al ganador
    for c in candidatos[2:]:
        pt = _pares(cubo, c["clave"], ganador, destino)
        if pt and _razon(pt) <= 1 - DIFERENCIA:
            out["tercero"] = {"clave": c["clave"], "dif": round(1 - _razon(pt), 3)}
            break
    return out


def _candidatos(filas: list[dict[str, Any]], prefijo: str = "") -> list[dict[str, Any]]:
    return sorted((f for f in filas if f["suficiente"] and f["costo"] and "Sin dato" not in f["clave"]
                   and f["clave"].startswith(prefijo)), key=lambda f: -f["resultados"])


def _se_repite(comp: dict[str, Any]) -> bool:
    return comp.get("estado") == "gana" and comp.get("meses", 0) >= 2 and comp["meses_ganados"] / comp["meses"] >= 0.6


def _tendencia(cubo: dict, formato: str, destino: str, hoy: date) -> dict[str, Any] | None:
    """El último mes completo contra el promedio de los anteriores, en el contexto donde más se usó el formato."""
    estratos = _estratos(cubo, formato, destino)
    if not estratos:
        return None
    ctx = max(estratos, key=lambda c: estratos[c][1])
    actual = hoy.isoformat()[:7]
    serie = []
    for mes in sorted({k[2] for k in cubo if k[2] != actual}):
        g, r = _estratos(cubo, formato, destino, mes).get(ctx, [0.0, 0.0])
        if r >= MIN_RESULTADOS_MES:
            serie.append((mes, g / r))
    if len(serie) < 3:
        return None
    previos = [c for _, c in serie[:-1]]
    promedio = sum(previos) / len(previos)
    cambio = serie[-1][1] / promedio - 1
    if abs(cambio) < DIFERENCIA:
        return None
    return {"formato": formato, "contexto": ctx, "mes": serie[-1][0], "costo": round(serie[-1][1], 2),
            "promedio": round(promedio, 2), "cambio": round(cambio, 3)}


def _nueva_marca() -> dict[str, Any]:
    return {"gasto": 0.0, "cuentas": set(), "anuncios": set(), "destinos": defaultdict(_vacio),
            # cubo[destino][dimensión][(contexto, clave, mes)]
            "cubo": defaultdict(lambda: defaultdict(lambda: defaultdict(_vacio))),
            "ventas": defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0]))),
            "mes": defaultdict(lambda: defaultdict(_vacio)),
            "anuncio": defaultdict(lambda: {"s": _vacio(), "meses": set()}),
            "ubic": defaultdict(lambda: defaultdict(_vacio)), "ubic_formato": defaultdict(lambda: defaultdict(_vacio))}


def analizar(mat: dict[str, Any], ventas_por_anuncio: dict[str, dict[str, int]] | None = None,
             hoy: date | None = None) -> dict[str, Any]:
    """Arma el análisis de todas las marcas. ``ventas_por_anuncio``: ad_id → {leads, ventas}."""
    hoy = hoy or date.today()
    ventas_por_anuncio = ventas_por_anuncio or {}
    anuncios = mat.get("anuncios") or {}
    cuentas = mat.get("cuentas") or {}

    def marca_de(ad_id: str, cuenta: str = "") -> str:
        return (anuncios.get(ad_id) or {}).get("marca") or (cuentas.get(cuenta) or {}).get("marca", "")

    acc: dict[str, dict[str, Any]] = {}
    principal: dict[str, dict[tuple[str, str], float]] = defaultdict(lambda: defaultdict(float))
    for f in mat.get("por_mes") or []:
        marca = marca_de(f["ad_id"], f.get("cuenta", ""))
        if not marca:
            continue
        a = anuncios.get(f["ad_id"]) or {}
        d = destino_de(f)
        nombre_cuenta = (cuentas.get(f.get("cuenta", "")) or {}).get("nombre", "")
        ctx = contexto_de("asesor" if es_cuenta_de_asesor(nombre_cuenta, marca) else "marca", d,
                          f.get("optimizacion", ""))
        m = acc.setdefault(marca, _nueva_marca())
        m["gasto"] += f["gasto"]
        m["cuentas"].add(f.get("cuenta", ""))
        m["anuncios"].add(f["ad_id"])
        _sumar(m["destinos"][d], f)
        for dim, clave in _claves(a).items():
            _sumar(m["cubo"][d][dim][(ctx, clave, f["mes"])], f)
        formato = a.get("formato", "Sin dato")
        _sumar(m["mes"][d][(f["mes"], formato)], f)
        _sumar(m["mes"][d][(f["mes"], "Total")], f)
        an = m["anuncio"][f["ad_id"]]
        _sumar(an["s"], f)
        an["meses"].add(f["mes"])
        principal[f["ad_id"]][(d, ctx)] += f["gasto"]
    # Destino y contexto de cada anuncio: donde más gastó
    donde = {ad: max(v, key=v.get) for ad, v in principal.items()}

    # Ventas cruzadas (leads de formulario de los últimos 90 días): solo totales por material
    for ad_id, v in ventas_por_anuncio.items():
        marca = marca_de(ad_id)
        if marca not in acc or ad_id not in donde:
            continue
        m, (d, _) = acc[marca], donde[ad_id]
        leads, ventas = int(v.get("leads", 0)), int(v.get("ventas", 0))
        for dim, clave in _claves(anuncios.get(ad_id) or {}).items():
            m["ventas"][d][dim][clave][0] += leads
            m["ventas"][d][dim][clave][1] += ventas
        for s in (m["destinos"][d], m["anuncio"][ad_id]["s"]):
            s["leads_cruce"] += leads
            s["ventas"] += ventas

    # Ubicaciones (anuncio × ubicación en toda la ventana). Cada anuncio sale en todas las
    # ubicaciones a la vez, así que acá la comparación ya es entre las mismas piezas.
    for f in mat.get("por_ubicacion") or []:
        marca = marca_de(f["ad_id"])
        if marca not in acc or f["ad_id"] not in donde:
            continue
        d = donde[f["ad_id"]][0]
        u = ubicacion_de(f.get("plataforma", ""), f.get("posicion", ""))
        _sumar(acc[marca]["ubic"][d][u], f)
        formato = (anuncios.get(f["ad_id"]) or {}).get("formato", "Sin dato")
        _sumar(acc[marca]["ubic_formato"][d][(formato, u)], f)

    meses_ventana = sorted({f["mes"] for f in mat.get("por_mes") or []})
    marcas: dict[str, dict[str, Any]] = {}
    for marca, m in acc.items():
        out: dict[str, Any] = {"gasto": round(m["gasto"], 2), "cuentas": len(m["cuentas"] - {""}),
                               "anuncios": len(m["anuncios"]), "destinos": {}}
        for d in ("formulario", "chat", "otro"):
            if m["destinos"][d]["gasto"] <= 0:
                continue
            cubo = m["cubo"][d]
            res: dict[str, Any] = {"total": _metricas(m["destinos"][d], d)}
            gasto_ctx = _juntar(cubo["formato"], lambda k: k[0])
            res["contextos"] = [c for c in sorted(gasto_ctx, key=lambda c: -gasto_ctx[c]["gasto"])
                                if gasto_ctx[c]["gasto"] >= MIN_GASTO_CONTEXTO]
            for dim, nombre, orden in (("formato", "formatos", ORDEN_FORMATOS), ("tramo", "tramos", ORDEN_TRAMOS),
                                       ("vertical", "vertical", ORDEN_VERTICAL), ("origen", "origen", ORDEN_ORIGEN)):
                totales = _juntar(cubo[dim], lambda k: k[1])
                for clave, (leads, ventas) in m["ventas"][d][dim].items():
                    if clave in totales:
                        totales[clave]["leads_cruce"] += leads
                        totales[clave]["ventas"] += ventas
                res[nombre] = _tabla(totales, d, orden, MIN_ANUNCIOS)
                por_ctx: dict[str, dict[str, Any]] = defaultdict(dict)
                for (ctx, clave), s in _juntar(cubo[dim], lambda k: (k[0], k[1])).items():
                    por_ctx[clave][ctx] = _metricas(s, d)
                res[f"{nombre}_ctx"] = dict(por_ctx)
            res["comparaciones"] = {
                "formato": _comparar(cubo["formato"], _candidatos(res["formatos"]), d, hoy),
                "tramo": _comparar(cubo["tramo"], _candidatos(res["tramos"]), d, hoy),
                **{f"vertical|{fo}": _comparar(cubo["vertical"], _candidatos(res["vertical"], fo + "|"), d, hoy)
                   for fo in ("Imagen", "Video")},
            }
            principal_fmt = (res["comparaciones"]["formato"].get("ganador")
                             or next((f["clave"] for f in sorted(res["formatos"], key=lambda f: -f["resultados"])), None))
            res["tendencia"] = _tendencia(cubo["formato"], principal_fmt, d, hoy) if principal_fmt and d in DESTINOS else None
            res["ubicaciones"] = _tabla(m["ubic"][d], d, ORDEN_UBICACIONES)
            res["formato_ubicacion"] = {f"{fo}|{u}": _metricas(s, d) for (fo, u), s in m["ubic_formato"][d].items()
                                        if s["gasto"] > 0}
            res["meses"] = {mes: {fo: _metricas(s, d) for (me, fo), s in m["mes"][d].items() if me == mes and s["gasto"] > 0}
                            for mes in meses_ventana}
            res["mejores"], res["peores"] = _ranking(m["anuncio"], d, donde, cubo["formato"], anuncios)
            out["destinos"][d] = res
        out["conclusiones"] = conclusiones(out, meses_ventana, hoy)
        out["recomendacion"] = recomendacion(out)
        marcas[marca] = out

    return {"generado": datetime.now().isoformat(timespec="minutes"), "desde": mat.get("desde"),
            "hasta": mat.get("hasta"), "meses": meses_ventana, "con_ventas": bool(ventas_por_anuncio),
            "marcas": dict(sorted(marcas.items(), key=lambda kv: -kv[1]["gasto"]))}


def _ranking(por_anuncio: dict[str, dict[str, Any]], destino: str, donde: dict[str, tuple[str, str]],
             cubo_formato: dict, anuncios: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Cada anuncio contra el promedio de SU contexto: un anuncio de asesor no gana solo por ser de asesor."""
    promedio: dict[str, float] = {}
    for ctx, s in _juntar(cubo_formato, lambda k: k[0]).items():
        r = _resultados(s, destino)
        if r:
            promedio[ctx] = s["gasto"] / r
    filas = []
    for ad_id, an in por_anuncio.items():
        d, ctx = donde.get(ad_id, ("otro", ""))
        if d != destino:
            continue
        m = _metricas(an["s"], destino)
        a = anuncios.get(ad_id) or {}
        base = promedio.get(ctx)
        filas.append({"ad_id": ad_id, "nombre": a.get("nombre", ad_id), "formato": a.get("formato", "Sin dato"),
                      "tramo": tramo_de(duracion_de(a)) if a.get("formato") in ("Video", "Mixto") else "",
                      "vertical": vertical_de(a), "meses": sorted(an["meses"]), "contexto": ctx,
                      "relativo": round(m["costo"] / base, 2) if m["costo"] and base else None, **m})
    mejores = sorted((f for f in filas if f["gasto"] >= MIN_ANUNCIO_GASTO and f["resultados"] >= MIN_ANUNCIO_RESULTADOS
                      and f["relativo"] is not None and f["relativo"] <= 1), key=lambda f: f["relativo"])[:5]
    peores = sorted((f for f in filas if f["gasto"] >= MIN_GASTO
                     and (not f["resultados"] or (f["relativo"] is not None and f["relativo"] >= 2))),
                    key=lambda f: -f["gasto"])[:5]
    return mejores, peores


# ---------------------------------------------------------------------------
# Conclusiones (texto)
# ---------------------------------------------------------------------------

def _usd(x: float | None) -> str:
    if x is None:
        return "—"
    if x >= 100:
        return "USD " + f"{x:,.0f}".replace(",", ".")
    return "USD " + f"{x:.2f}".replace(".", ",")


def _miles(x: float | int) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _pct(x: float | None, dec: int = 0) -> str:
    return "—" if x is None else f"{x:.{dec}f} %".replace(".", ",")


def _mes(clave: str, hoy: date | None = None) -> str:
    anio, mes = clave.split("-")
    txt = MESES[int(mes) - 1]
    if hoy and (hoy.year, hoy.month) == (int(anio), int(mes)):
        txt += f" (al {hoy.day})"
    return txt


def _may(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


SUJETO_FORMATO = {"Imagen": "la imagen (gráfica)", "Video": "el video", "Carrusel": "el carrusel",
                  "Mixto": "los anuncios con imagen y video juntos"}
SUJETO_TRAMO = {"Hasta 15 s": "los videos de hasta 15 s", "16 a 30 s": "los videos de 16 a 30 s",
                "31 a 60 s": "los videos de 31 a 60 s", "Más de 60 s": "los videos de más de 60 s"}
SUJETO_VERTICAL = {"Imagen|Con versión vertical": "las imágenes con versión vertical (9:16)",
                   "Imagen|Sin versión vertical": "las imágenes sin versión vertical",
                   "Video|Con versión vertical": "los videos con versión vertical (9:16)",
                   "Video|Sin versión vertical": "los videos sin versión vertical"}


def _plural(sujeto: str) -> bool:
    return sujeto.split(" ", 1)[0] in ("los", "las")


def _texto_meses(comp: dict[str, Any]) -> str:
    if comp.get("meses", 0) < 2:
        return " Todavía no hay meses suficientes para ver si se repite."
    if _se_repite(comp):
        return f" Se repite: ganó en {comp['meses_ganados']} de {comp['meses']} meses."
    return (f" Pero ganó solo en {comp['meses_ganados']} de {comp['meses']} meses: tomarlo como pista, "
            "no como regla.")


def _detalle(comp: dict[str, Any], union: str) -> str:
    """«marca · calidad: USD 3,10 contra USD 3,65; asesores · volumen: …» (los contextos que se compararon)."""
    return "; ".join(f"{CONTEXTO_CORTO.get(x['contexto'], x['contexto']).lower()}: {_usd(x['ganador'])}{union}"
                     f"{_usd(x['rival'])}" for x in comp["detalle"])


def _texto_comparacion(comp: dict[str, Any], sujetos: dict[str, str], unidad: str, unidades: str) -> str | None:
    """La frase de una comparación, o None si no hay nada que decir."""
    nombre = lambda k: sujetos.get(k, k)  # noqa: E731
    estado = comp.get("estado")
    if estado == "gana":
        art, barato = GENERO[unidad]
        g, p = nombre(comp["ganador"]), nombre(comp["rival"])
        txt = (f"**{_may(g)}** {'traen' if _plural(g) else 'trae'} {art} {unidad} más {barato}: "
               f"{_pct(comp['dif'] * 100)} menos que {p} en campañas comparables ({_detalle(comp, ' contra ')}; "
               f"base: {_miles(comp['base'])} {unidades}).") + _texto_meses(comp)
        if comp.get("tercero"):
            t = nombre(comp["tercero"]["clave"])
            txt += (f" Además, {t}, con menos anuncios, {'salieron' if _plural(t) else 'salió'} "
                    f"{_pct(comp['tercero']['dif'] * 100)} más {'baratos' if _plural(t) else barato} todavía: vale la "
                    "pena probarlo más.")
        return txt
    if estado == "empate":
        return (f"{_may(nombre(comp['ganador']))} y {nombre(comp['rival'])} cuestan parecido en campañas comparables "
                f"({_detalle(comp, ' y ')} por {unidad}): menos de 15 % de diferencia no alcanza para elegir.")
    if estado == "sin_comparables":
        return (f"{_may(nombre(comp['a']))} y {nombre(comp['b'])} no se pueden comparar: se usaron en cuentas o tipos "
                "de formulario distintos (por ejemplo, uno en la cuenta de la marca y el otro en las de asesores).")
    return None


def conclusiones(m: dict[str, Any], meses: list[str], hoy: date | None = None) -> list[str]:
    """Lo que dice el historial, en frases cortas. Solo con muestra suficiente y en campañas comparables."""
    out: list[str] = []
    destinos = sorted(((d, r) for d, r in m["destinos"].items() if d in DESTINOS),
                      key=lambda dr: -dr[1]["total"]["gasto"])
    for d, r in destinos:
        unidad, unidades = RESULTADO[d]
        etiqueta = NOMBRE_DESTINO[d]
        art, barato = GENERO[unidad]
        comp = r["comparaciones"]["formato"]
        if comp["estado"] == "uno":
            nombre = NOMBRE_FORMATO.get(comp["ganador"], comp["ganador"]).lower()
            otros = [NOMBRE_FORMATO.get(f["clave"], f["clave"]).lower() for f in r["formatos"]
                     if f["clave"] not in (comp["ganador"], "Sin dato")]
            out.append(f"**{etiqueta} — formato:** " + (
                f"solo {nombre} tiene muestra suficiente; se probó poco {', '.join(otros)}." if otros else
                f"todo fue {nombre}; no hay otro formato para comparar."))
        else:
            txt = _texto_comparacion(comp, SUJETO_FORMATO, unidad, unidades)
            if txt:
                out.append(f"**{etiqueta} — formato:** {txt}")
        con_muestra = sorted((f for f in r["ubicaciones"] if f["clave"] in PRINCIPALES and f["suficiente"] and f["costo"]),
                             key=lambda f: f["costo"])
        if len(con_muestra) >= 2:
            if 1 - con_muestra[0]["costo"] / con_muestra[-1]["costo"] >= DIFERENCIA:
                resto = " · ".join(f"{f['clave']} {_usd(f['costo'])}" for f in con_muestra[1:])
                out.append(f"**{etiqueta} — Reels, Stories o Feed:** {art} {unidad} más {barato} sale en "
                           f"**{con_muestra[0]['clave']}** ({_usd(con_muestra[0]['costo'])}); después {resto}. "
                           "Son las mismas piezas en distintas ubicaciones: tener la versión para la que rinde.")
            else:
                out.append(f"**{etiqueta} — Reels, Stories o Feed:** cuesta parecido en las tres "
                           f"({' · '.join(f['clave'] + ' ' + _usd(f['costo']) for f in con_muestra)}).")
        txt = _texto_comparacion(r["comparaciones"]["tramo"], SUJETO_TRAMO, unidad, unidades)
        if txt:
            out.append(f"**{etiqueta} — duración del video:** {txt}")
        for formato, plural in (("Imagen", "imágenes"), ("Video", "videos")):
            txt = _texto_comparacion(r["comparaciones"][f"vertical|{formato}"], SUJETO_VERTICAL, unidad, unidades)
            if txt:
                out.append(f"**{etiqueta} — {plural} con o sin versión vertical:** {txt}")
        con_ventas = [f for f in r["formatos"] if f["leads_cruce"] and f["clave"] != "Sin dato"]
        total_ventas = sum(f["ventas"] for f in con_ventas)
        if d == "formulario" and con_ventas:
            if total_ventas >= MIN_VENTAS:
                partes = [f"{NOMBRE_FORMATO.get(f['clave'], f['clave']).lower()} {f['ventas']} de "
                          f"{_miles(f['leads_cruce'])} leads ({_pct(f['ventas_cada_100'], 1)})"
                          for f in con_ventas if f["leads_cruce"] >= 30]
                if partes:
                    out.append(f"**Ventas (cruce con el ERP, leads de los últimos 90 días):** {total_ventas} ventas: "
                               + "; ".join(partes) + ". Mezcla cuentas de la marca y de asesores: es orientativo.")
            elif total_ventas:
                out.append(f"**Ventas:** {total_ventas} venta{'s' if total_ventas != 1 else ''} cruzada"
                           f"{'s' if total_ventas != 1 else ''} con leads de formulario de los últimos 90 días: "
                           "pocas para decir qué formato vende más.")
            else:
                out.append("**Ventas:** todavía ninguna venta del ERP se pudo cruzar con los leads de formulario de los "
                           "últimos 90 días (el ERP casi no trae teléfono ni mail): no se puede decir qué formato vende más.")
        t = r.get("tendencia")
        if t:
            out.append(f"**{etiqueta} — tendencia:** en {_mes(t['mes'])}, {SUJETO_FORMATO.get(t['formato'], t['formato'])} "
                       f"costó {_usd(t['costo'])} por {unidad} {CONTEXTO_FRASE.get(t['contexto'], '')}, "
                       f"{_pct(abs(t['cambio']) * 100)} {'más' if t['cambio'] > 0 else 'menos'} que su promedio de los "
                       f"meses anteriores ({_usd(t['promedio'])})"
                       + (": puede ser cansancio de las piezas." if t["cambio"] > 0 else "."))
    if not out:
        out.append("Todavía no hay muestra suficiente para comparar materiales (hace falta al menos "
                   f"{_usd(MIN_GASTO)}, {MIN_RESULTADOS} resultados y {MIN_ANUNCIOS} anuncios por formato).")
    return out


def recomendacion(m: dict[str, Any]) -> str | None:
    """La pieza que conviene probar primero: solo lo que ganó claro, en campañas comparables y mes a mes."""
    destinos = sorted(((d, r) for d, r in m["destinos"].items() if d in DESTINOS),
                      key=lambda dr: -dr[1]["total"]["gasto"])
    if not destinos:
        return None
    d, r = destinos[0]
    unidad = RESULTADO[d][0]
    art, barato = GENERO[unidad]
    comp = r["comparaciones"]["formato"]
    destino = NOMBRE_DESTINO[d].lower()
    if comp["estado"] == "sin_muestra":
        return None
    if comp["estado"] == "uno":
        return (f"En {destino} casi todo fue {NOMBRE_FORMATO.get(comp['ganador'], comp['ganador']).lower()}: para saber "
                "si otro formato rinde más, sumar uno distinto en el mismo conjunto.")
    if not _se_repite(comp):
        a, b = (comp.get("ganador") or comp.get("a")), (comp.get("rival") or comp.get("b"))
        return (f"En {destino}, {SUJETO_FORMATO.get(a, a)} y {SUJETO_FORMATO.get(b, b)} no se separan de forma clara y "
                "sostenida en campañas comparables: elegir por la pieza que haya y probar las dos en el mismo conjunto.")
    ganador = comp["ganador"]
    pieza = NOMBRE_FORMATO.get(ganador, ganador).lower()
    if ganador in ("Video", "Mixto"):
        tramo = r["comparaciones"]["tramo"]
        if _se_repite(tramo):
            pieza += f" de {tramo['ganador'].lower()}"
    vert = r["comparaciones"].get(f"vertical|{ganador}") or {}
    if _se_repite(vert) and vert["ganador"].endswith("Con versión vertical"):
        pieza += " con versión vertical (9:16)"
    return (f"Para la próxima pauta de {destino}: **{pieza}**, que trajo {art} {unidad} más {barato} en campañas "
            f"comparables y se repitió mes a mes. En el mismo conjunto, sumar {SUJETO_FORMATO.get(comp['rival'], comp['rival'])} "
            "para seguir comparando.")


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------

def _celda(texto: Any, largo: int = 55) -> str:
    return str(texto or "—").replace("|", "/").replace("[", "(").replace("]", ")")[:largo].strip() or "—"


def _periodo(r: dict[str, Any], hoy: date | None = None) -> str:
    meses = r.get("meses") or []
    if not meses:
        return f"{r.get('desde')} a {r.get('hasta')}"
    return f"{_mes(meses[0])} a {_mes(meses[-1], hoy)} ({len(meses)} meses, del {r.get('desde')} al {r.get('hasta')})"


def _tabla_md(filas: list[dict[str, Any]], unidad: str, nombre=lambda k: k, ventas: bool = False,
              video: bool = False, solo_video: tuple[str, ...] = ()) -> list[str]:
    """``solo_video``: las filas que llevan las columnas de video (en la de formatos, una imagen no se «mira 3 s»)."""
    plural = "Leads" if unidad == "lead" else "Conversaciones"
    cab = ["", "Anuncios", "Inversión", "% inversión", plural, f"Costo por {unidad}", "CTR", f"{plural} cada 100 clics"]
    if video:
        cab += ["Lo miran 3 s", "Lo ven completo"]
    if ventas:
        cab += ["Ventas (cruce ERP)", "Ventas cada 100 leads"]
    L = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for f in filas:
        poca = "" if f["suficiente"] else " _(poca muestra)_"
        cada_100 = "—" if f["cada_100_clics"] is None else f"{f['cada_100_clics']:.1f}".replace(".", ",")
        celdas = [f"**{nombre(f['clave'])}**{poca}", str(f["anuncios"]), _usd(f["gasto"]), _pct(f["pct_gasto"]),
                  _miles(f["resultados"]), f"**{_usd(f['costo'])}**" if f["costo"] else "—", _pct(f["ctr"], 2), cada_100]
        if video:
            es_video = not solo_video or f["clave"] in solo_video
            celdas += [_pct(f["mira_3s"], 1), _pct(f["completo"], 1)] if es_video else ["—", "—"]
        if ventas:
            celdas += [str(f["ventas"]) if f["leads_cruce"] else "—", _pct(f["ventas_cada_100"], 1)]
        L.append("| " + " | ".join(celdas) + " |")
    return L


def _tabla_contextos(filas: list[dict[str, Any]], por_ctx: dict[str, dict[str, Any]], contextos: list[str],
                     nombre=lambda k: k) -> list[str]:
    """Costo de cada material en cada contexto: se compara leyendo cada columna de arriba a abajo."""
    claves = [f["clave"] for f in filas if "Sin dato" not in f["clave"]]
    cols = [c for c in contextos if any(c in por_ctx.get(k, {}) for k in claves)]
    if not claves or not cols:
        return []
    L = ["| | " + " | ".join(CONTEXTO_CORTO.get(c, c) for c in cols) + " |", "|---|" + "---|" * len(cols)]
    for k in claves:
        celdas = []
        for c in cols:
            x = por_ctx.get(k, {}).get(c)
            if not x or not x["gasto"]:
                celdas.append("—")
            elif x["resultados"] >= MIN_RESULTADOS_MES and x["costo"]:
                celdas.append(f"{_usd(x['costo'])} ({_miles(x['resultados'])})")
            else:
                celdas.append("_poca muestra_")
        L.append(f"| **{nombre(k)}** | " + " | ".join(celdas) + " |")
    return L


def nota_marca(marca: str, m: dict[str, Any], r: dict[str, Any], hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    L = ["---", "type: materiales-meta", f"marca: {marca}", f"periodo: {r.get('desde')} a {r.get('hasta')}",
         f"created: {hoy.isoformat()}", f"tags:\n  - meta-ads\n  - materiales\n  - marca/{marca.lower().replace(' ', '-')}",
         "---", "", f"# 🎬 Materiales que funcionan — {marca}", "",
         "> [!info] De dónde sale",
         f"> Todos los anuncios de Meta de {marca} de **{_periodo(r, hoy)}**: {m['anuncios']} anuncios con gasto en "
         f"{m['cuentas']} cuenta{'s' if m['cuentas'] != 1 else ''} (la de la marca y las de los asesores), "
         f"{_usd(m['gasto'])} de inversión. Se lee anuncio por anuncio de la API de Meta (formato, duración y tamaño de "
         "cada pieza, ubicación y resultados) y se cruza con las ventas del ERP. Se actualiza en cada corrida: "
         "**no editar a mano**.", "",
         "## ✅ Qué dice el historial", ""]
    if m.get("recomendacion"):
        L += [f"> [!success] {m['recomendacion']}", ""]
    L += [f"- {c}" for c in m["conclusiones"]]
    L += ["", "> [!tip] Cómo usarlo",
          "> Para la próxima pieza, empezar por lo que ganó acá y probarlo contra una variante (otro formato u otra "
          "duración) en el mismo conjunto. Juzgar a las 3-4 semanas, no antes "
          "([[📘 Manual Buyer Persona#4.4 Cuándo juzgar una campaña|Manual, 4.4]]).", ""]
    for d in ("formulario", "chat"):
        res = m["destinos"].get(d)
        if not res:
            continue
        unidad, unidades = RESULTADO[d]
        cuantos = "cuántos" if unidad == "lead" else "cuántas"
        t = res["total"]
        ventas = bool(d == "formulario" and r.get("con_ventas"))
        ctxs = res["contextos"]
        L += [f"## {'📝' if d == 'formulario' else '💬'} {NOMBRE_DESTINO[d]}", "",
              f"{_usd(t['gasto'])} de inversión, {_miles(t['resultados'])} {unidades}, **{_usd(t['costo'])} por {unidad}** "
              "en promedio.", "", "### ¿Imagen, video o carrusel?", ""]
        tabla = _tabla_contextos(res["formatos"], res["formatos_ctx"], ctxs, lambda k: NOMBRE_FORMATO.get(k, k))
        if tabla:
            L += [f"**Costo por {unidad} en cada contexto** (entre paréntesis, {cuantos} {unidades}). Para comparar "
                  "formatos, leer cada columna de arriba a abajo: entre columnas el costo cambia por la cuenta y el "
                  "tipo de formulario, no por el material.", ""] + tabla + [""]
        L += [f"**Totales por formato** (mezclan contextos: sirven para ver volumen, CTR, retención"
              f"{' y ventas' if ventas else ''}).", ""]
        L += _tabla_md(res["formatos"], unidad, lambda k: NOMBRE_FORMATO.get(k, k), ventas=ventas, video=True,
                       solo_video=("Video", "Mixto"))
        L += ["", "### ¿Reels, Stories o Feed?", "",
              "Cada anuncio sale en todas las ubicaciones a la vez, así que acá se comparan las mismas piezas.", ""]
        L += _tabla_md(res["ubicaciones"], unidad)
        cruce = _cruce_formato_ubicacion(res)
        if cruce:
            L += ["", f"**Costo por {unidad} de cada formato en cada ubicación** (solo combinaciones con {MIN_RESULTADOS} "
                  f"{unidades} o más):", ""] + cruce
        if res["tramos"]:
            L += ["", "### Videos: ¿cortos o largos?", ""]
            tabla = _tabla_contextos(res["tramos"], res["tramos_ctx"], ctxs)
            if tabla:
                L += [f"**Costo por {unidad} en cada contexto:**", ""] + tabla + ["", "**Totales:**", ""]
            L += _tabla_md(res["tramos"], unidad, video=True, ventas=ventas)
        filas_v = [f for f in res["vertical"] if f["clave"].split("|")[0] in ("Imagen", "Video")]
        tabla = _tabla_contextos(filas_v, res["vertical_ctx"], ctxs,
                                 lambda k: f"{NOMBRE_FORMATO.get(k.split('|')[0], k)}, {k.split('|')[1].lower()}")
        if tabla and any(sum(1 for f in filas_v if f["clave"].startswith(fo + "|") and "Sin dato" not in f["clave"]) > 1
                         for fo in ("Imagen", "Video")):
            L += ["", "### ¿Con versión vertical (9:16)?", "",
                  "La versión vertical es la que llena la pantalla en Reels y Stories. Se compara dentro de cada formato "
                  f"y de cada contexto (costo por {unidad}):", ""] + tabla
        if len(res["origen"]) > 1:
            L += ["", "### ¿Anuncio armado o publicación promocionada?", ""]
            L += _tabla_md(res["origen"], unidad, lambda k: NOMBRE_ORIGEN.get(k, k))
        L += ["", "### Mes a mes", "",
              f"Costo por {unidad} de cada formato (entre paréntesis, {cuantos} {unidades}). Mezcla contextos: sirve para "
              "ver la evolución, no para comparar formatos entre sí.", ""]
        L += _tabla_meses(res, hoy)
        if res["mejores"]:
            L += ["", "### 🏆 Los anuncios que mejor rindieron", "",
                  f"Cada anuncio contra el promedio de su contexto (al menos {_usd(MIN_ANUNCIO_GASTO)} y "
                  f"{MIN_ANUNCIO_RESULTADOS} {unidades}).", ""]
            L += _tabla_anuncios(res["mejores"], unidad, ventas)
        if res["peores"]:
            L += ["", "### 💸 Los que más gastaron para lo que trajeron", "",
                  f"Costo por {unidad} del doble o más que el promedio de su contexto, o sin {unidades}.", ""]
            L += _tabla_anuncios(res["peores"], unidad, ventas)
        L.append("")
    otro = m["destinos"].get("otro")
    if otro and otro["total"]["gasto"] >= MIN_GASTO:
        t = otro["total"]
        L += ["## 📣 Alcance, tráfico e interacción", "",
              f"{_usd(t['gasto'])} en campañas que no buscan formularios ni chats. No se juzgan por costo por lead: "
              f"CPM {_usd(t['cpm'])}, CTR {_pct(t['ctr'], 2)}"
              + (f", el {_pct(t['mira_3s'], 1)} mira 3 s o más de los videos." if t.get("mira_3s") else "."), ""]
    L += ["## 📏 Cómo leerlo", "",
          "- **Resultado** = formulario enviado (campañas de formularios) o conversación iniciada (WhatsApp y mensajes). "
          "Los dos destinos no se comparan entre sí.",
          "- **Campañas comparables.** Las cuentas de asesores sacan leads más baratos que la de la marca, y los "
          "formularios de volumen más baratos que los de calidad. Si se mezclan, «gana» el material que más usaron los "
          "asesores. Por eso cada material se compara dentro de cada contexto (cuenta de la marca o de asesores × "
          "formulario de calidad o de volumen) y la conclusión promedia esas diferencias. Si dos materiales nunca se "
          "usaron en el mismo contexto, la nota dice que no se pueden comparar.",
          f"- _(poca muestra)_ = menos de {_usd(MIN_GASTO)}, de {MIN_RESULTADOS} resultados o de {MIN_ANUNCIOS} anuncios: no "
          "entra en las conclusiones. Menos de 15 % de diferencia es un empate, y una diferencia que no se repite en la "
          "mayoría de los meses es una pista, no una regla.",
          "- **Reels** es una ubicación, no un formato: un video o una imagen con versión vertical se muestran ahí. "
          "Meta reparte el presupuesto entre ubicaciones; forzar una sola suele encarecer el resto.",
          "- **Lo miran 3 s** = vistas de 3 segundos ÷ impresiones (qué tan bien engancha el comienzo). "
          "**Lo ven completo** = vistas al 100 % ÷ vistas de 3 s.",
          "- **Ventas (cruce ERP)**: ventas a clientes finales cuyo lead de formulario vino de ese anuncio (leads de los "
          "últimos 90 días, ver [[💰 Ventas que vinieron de Meta]] para el método). Es un piso: los chats de WhatsApp "
          "no se pueden cruzar y el ERP casi no trae teléfono ni mail desde agosto de 2026.",
          "- El formato no es lo único que cambia entre anuncios: también el modelo, la oferta y el público.", "",
          f"← [[{marca}|Volver a {marca}]]", ""]
    return "\n".join(L)


def _cruce_formato_ubicacion(res: dict[str, Any]) -> list[str]:
    datos = res.get("formato_ubicacion") or {}
    ubicaciones = [u for u in PRINCIPALES if any(k.endswith("|" + u) for k in datos)]
    formatos = [f for f in ORDEN_FORMATOS if f != "Sin dato" and any(k.startswith(f + "|") for k in datos)]
    filas = []
    for fo in formatos:
        celdas = []
        for u in ubicaciones:
            x = datos.get(f"{fo}|{u}")
            celdas.append(_usd(x["costo"]) if x and x["resultados"] >= MIN_RESULTADOS and x["costo"] else "—")
        if any(c != "—" for c in celdas):
            filas.append(f"| {NOMBRE_FORMATO.get(fo, fo)} | " + " | ".join(celdas) + " |")
    if not filas or not ubicaciones:
        return []
    return ["| Formato | " + " | ".join(ubicaciones) + " |", "|---|" + "---|" * len(ubicaciones)] + filas


def _tabla_meses(res: dict[str, Any], hoy: date) -> list[str]:
    formatos = [f["clave"] for f in res["formatos"] if f["clave"] != "Sin dato"]
    for mes in res["meses"].values():
        formatos += [fo for fo in mes if fo not in formatos and fo not in ("Total", "Sin dato")]
    L = ["| Mes | " + " | ".join(NOMBRE_FORMATO.get(f, f) for f in formatos) + " | Total |",
         "|---|" + "---|" * (len(formatos) + 1)]
    for mes in sorted(res["meses"]):
        fila = res["meses"][mes] or {}
        if not fila:
            continue
        celdas = []
        for fo in formatos + ["Total"]:
            x = fila.get(fo)
            celdas.append(f"{_usd(x['costo'])} ({_miles(x['resultados'])})" if x and x.get("costo") else
                          ("sin resultados" if x and x["gasto"] >= 10 else "—"))
        etiqueta = _mes(mes, hoy)
        if mes[:4] != str(hoy.year):
            etiqueta += f" {mes[:4]}"
        L.append(f"| {etiqueta} | " + " | ".join(celdas) + " |")
    return L


def _tabla_anuncios(filas: list[dict[str, Any]], unidad: str, ventas: bool) -> list[str]:
    cab = ["Anuncio", "Formato", "Dónde", "Meses", "Inversión", f"{'Leads' if unidad == 'lead' else 'Conversaciones'}",
           f"Costo por {unidad}", "Contra su contexto", "CTR"] + (["Ventas"] if ventas else [])
    L = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for f in filas:
        detalle = NOMBRE_FORMATO.get(f["formato"], f["formato"])
        if f["tramo"] and f["tramo"] != "Sin dato":
            detalle += f", {f['tramo'].lower()}"
        if f["vertical"] == "Con versión vertical":
            detalle += ", con vertical"
        meses = f"{_mes(f['meses'][0])}–{_mes(f['meses'][-1])}" if len(f["meses"]) > 1 else _mes(f["meses"][0])
        relativo = "sin resultados" if not f["resultados"] else (
            "—" if f["relativo"] is None else f"{'+' if f['relativo'] >= 1 else '−'}{_pct(abs(f['relativo'] - 1) * 100)}")
        celdas = [_celda(f["nombre"]), detalle, CONTEXTO_CORTO.get(f["contexto"], f["contexto"]), meses,
                  _usd(f["gasto"]), _miles(f["resultados"]), _usd(f["costo"]) if f["costo"] else "—", relativo,
                  _pct(f["ctr"], 2)]
        if ventas:
            celdas.append(str(f["ventas"]) if f["leads_cruce"] else "—")
        L.append("| " + " | ".join(celdas) + " |")
    return L


def resumen_moc(marca: str, m: dict[str, Any] | None) -> list[str]:
    """Bloque corto para el índice de la marca."""
    if not m:
        return []
    L = ["## 🎬 Materiales que mejor funcionan", ""]
    if m.get("recomendacion"):
        L.append(f"- {m['recomendacion']}")
    L += [f"- {c}" for c in m["conclusiones"][:3]]
    L += [f"- **Formato, ubicación, duración, mes a mes y mejores anuncios:** [[🎬 Materiales que funcionan — {marca}]]", ""]
    return L


def _resumen_comparacion(comp: dict[str, Any], nombres: dict[str, str]) -> str:
    estado = comp.get("estado")
    if estado == "gana":
        txt = f"{nombres.get(comp['ganador'], comp['ganador'])} −{_pct(comp['dif'] * 100)}"
        return txt + ("" if _se_repite(comp) else " (no se repite)")
    if estado == "empate":
        return "empate"
    if estado == "sin_comparables":
        return "no comparables"
    if estado == "uno":
        return f"solo {nombres.get(comp['ganador'], comp['ganador']).lower()}"
    return "—"


def nota_hub(r: dict[str, Any], marcas_con_nota: set[str], hoy: date | None = None) -> str:
    """Comparación entre marcas (uso interno, en Sistema/)."""
    hoy = hoy or date.today()
    L = ["---", "type: materiales-meta-hub", f"periodo: {r.get('desde')} a {r.get('hasta')}", f"created: {hoy.isoformat()}",
         "tags:\n  - meta-ads\n  - materiales\n  - sistema", "---", "", "# 🎬 Materiales Meta — todas las marcas", "",
         "> [!info] Uso interno",
         f"> Qué formato, ubicación y duración de video rinden en cada marca, de {_periodo(r, hoy)}. "
         "Cada marca ve solo su nota en el cerebro. Se actualiza en cada corrida. Las comparaciones son dentro de "
         "campañas comparables (cuenta de la marca o de asesores × formulario de calidad o de volumen): ver el «Cómo "
         "leerlo» de cualquier nota de marca.", "",
         "## Por marca", "",
         "| Marca | Inversión | Destino principal | Formato (diferencia en campañas comparables) | Duración del video | "
         "Ubicación más barata | Ventas cruzadas |",
         "|---|---|---|---|---|---|---|"]
    tramos = {k: k.lower() for k in ORDEN_TRAMOS}
    for marca, m in r["marcas"].items():
        dests = sorted(((d, x) for d, x in m["destinos"].items() if d in DESTINOS), key=lambda dx: -dx[1]["total"]["gasto"])
        if not dests:
            continue
        d, x = dests[0]
        ubic = sorted((f for f in x["ubicaciones"] if f["clave"] in PRINCIPALES and f["suficiente"] and f["costo"]),
                      key=lambda f: f["costo"])
        ventas = sum(f["ventas"] for f in (m["destinos"].get("formulario") or {}).get("formatos", []))
        nombre = f"[[🎬 Materiales que funcionan — {marca}|{marca}]]" if marca in marcas_con_nota else marca
        L.append(f"| {nombre} | {_usd(m['gasto'])} | {NOMBRE_DESTINO[d]} | "
                 f"{_resumen_comparacion(x['comparaciones']['formato'], NOMBRE_FORMATO)} | "
                 f"{_resumen_comparacion(x['comparaciones']['tramo'], tramos)} | "
                 f"{(ubic[0]['clave'] + ' ' + _usd(ubic[0]['costo'])) if ubic else '—'} | {ventas or '—'} |")
    L += ["", "_«−22 %» = el material ganador cuesta 22 % menos por resultado que el segundo más usado, en las mismas "
          "cuentas y tipo de formulario. «(no se repite)» = ganó en el total pero no en la mayoría de los meses._", "",
          "Cómo se calcula: `src/generators/materiales_meta.py` · datos en `output/raw/materiales_meta_<fecha>.json`.", ""]
    return "\n".join(L)


def incorporar_historial(r: dict[str, Any], ruta: str | Path) -> int:
    """Guarda cada mes de cada marca/destino/formato y trae de vuelta los meses que ya salieron de la ventana.

    La API se lee con una ventana móvil de N meses: sin esto, el mes que sale de la ventana se pierde.
    El archivo es un JSONL en el vault (Sistema/Memoria/), un registro por mes × marca × destino × formato.
    Devuelve cuántos meses de historial (fuera de la ventana) se sumaron a las notas.
    """
    ruta = Path(ruta)
    guardado: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(linea)
                guardado[(x["mes"], x["marca"], x["destino"], x["formato"])] = x
            except (ValueError, KeyError):
                continue
    ventana = set(r.get("meses") or [])
    hoy = date.today().isoformat()
    for marca, m in r["marcas"].items():
        for d, res in m["destinos"].items():
            for mes, formatos in res["meses"].items():
                for fo, x in formatos.items():
                    guardado[(mes, marca, d, fo)] = {
                        "mes": mes, "marca": marca, "destino": d, "formato": fo, "gasto": x["gasto"],
                        "resultados": x["resultados"], "impresiones": x["impresiones"], "clics": x["clics"],
                        "anuncios": x["anuncios"], "actualizado": hoy}
    sumados = set()
    for (mes, marca, d, fo), x in guardado.items():
        if mes in ventana or marca not in r["marcas"] or d not in r["marcas"][marca]["destinos"]:
            continue
        res = r["marcas"][marca]["destinos"][d]
        res["meses"].setdefault(mes, {})[fo] = {**x, "costo": round(x["gasto"] / x["resultados"], 2) if x["resultados"] else None}
        sumados.add(mes)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for _, x in sorted(guardado.items())), encoding="utf-8")
    return len(sumados)


def ventas_por_anuncio_guardadas(raw_dir: str | Path) -> dict[str, dict[str, int]]:
    """Las ventas por anuncio del último cruce guardado (para correr con --from-json)."""
    archivos = sorted(Path(raw_dir).glob("ventas_meta_*.json"))
    for archivo in reversed(archivos):
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if datos.get("por_anuncio"):
            return datos["por_anuncio"]
    return {}
