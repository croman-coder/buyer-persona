"""
Centro de compra: quién mira, quién da el paso y quién paga (pedido de
Valentina, 2026-09-24).

El Buyer Persona describe a un solo actor: el que compra. En la compra de un
auto hay más (quien investiga e influye, quien decide, quien firma). Sin
preguntar nada nuevo, cuatro fuentes que ya llegan al pipeline separan parte
de esos papeles:

1. **Meta, por género y edad, dentro de cada conjunto de anuncios.** Qué tanto
   contacta (formulario o chat) cada grupo que hace clic, viendo el mismo
   anuncio con el mismo botón. Comparar dentro del conjunto importa: Meta no le
   muestra lo mismo a todos, y sin ese control una campaña sin formulario hace
   parecer que un grupo "no convierte".
2. **Meta, por tema del anuncio, dentro de cada modelo.** Qué temas atraen más
   clics de mujeres o de mayores de 55 que el promedio del modelo. Solo cuentan
   temas con varios anuncios y sin uno que se lleve más de la mitad de los
   clics (si no, la conclusión es de ese anuncio y no del tema).
3. **ERP.** Qué parte de las compras a cliente final factura una empresa.
4. **Chats de Messenger e Instagram** (job semanal ``scripts/conversaciones_actores.py``).
   En cuántos el cliente nombra a otra persona: pareja, hijos, padres, empresa…

Salen conteos y porcentajes. Ningún dato personal entra ni sale de acá.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from src.generators.ad_copy_analyzer import INTEREST_LABELS, RULES

logger = logging.getLogger(__name__)

EDADES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
MAYORES = ("55-64", "65+")
MIN_CONTACTOS_CONJUNTO = 30     # para comparar dos grupos dentro de un conjunto
MIN_CONTACTOS_MARCA = 150
MIN_CONJUNTOS_SEÑAL = 4         # con menos, se informa como tendencia
MIN_CLICS_CELDA = 1000          # tema dentro de un modelo
MIN_ANUNCIOS_CELDA = 3
MAX_PESO_UN_ANUNCIO = 0.5
DIF_MUJERES_PP = 4.0
DIF_MAYORES_PP = 6.0
EMPRESA_ALTA_PCT = 30.0         # marca o modelo donde conviene una pieza para empresas
MIN_VENTAS_EMPRESA = 25
CONVERSACIONES_MAX_DIAS = 21

# Pieza sugerida por tema. Argumentos absolutos, sin nombrar competencia (ley
# PY) y sin cifras: el precio y el equipamiento los pone la marca.
PIEZA_POR_TEMA = {
    "Probar antes de comprar (test drive)": (
        "Vengan a probarla juntos",
        "Agendá una prueba de manejo para los dos: manejala, sentila en el día a día y decidan juntos."),
    "Seguridad y asistencias a la conducción": (
        "Seguridad para los que viajan con vos",
        "Asistencias a la conducción y seguridad pensadas para toda la familia. Vení a conocerla (según versión)."),
    "Diseño y estatus": (
        "Diseño que se nota",
        "Mirala en persona: terminaciones, espacio y detalles que se disfrutan todos los días."),
    "Tecnología y conectividad": (
        "Tecnología que se usa todos los días",
        "Pantallas, conectividad y asistencias que se entienden en cinco minutos. Vení a probarla."),
    "Familia y espacio": (
        "Espacio para todos",
        "Traé a tu familia a conocerla: espacio, comodidad y lugar para todo lo del día a día."),
    "Garantía y respaldo posventa": (
        "Respaldo para manejar tranquilos",
        "Garantía y servicio Santa Rosa: la tranquilidad también se prueba."),
    "Financiación en cuotas": (
        "Números claros para decidir en casa",
        "Planes de financiación para que la decisión cierre con números claros."),
    "Autos eléctricos y ahorro de combustible": (
        "Menos gasto todos los meses",
        "El ahorro en combustible se nota en el presupuesto de la casa."),
    "Primer auto / primera SUV": (
        "Tu primera SUV, acompañado",
        "Te acompañamos en toda la decisión, desde la prueba hasta la entrega."),
    "Trabajo, negocio y carga": (
        "Herramienta de trabajo",
        "Capacidad y respaldo para tu negocio, todos los días."),
    "Ofertas y promociones": (
        "Una oportunidad para decidir juntos",
        "Consultá las condiciones vigentes y vengan a verla."),
}

LECTURA_GENERO = {
    "ella_mira": "Ellas miran y el contacto lo deja él",
    "tendencia": "Misma tendencia, con pocos conjuntos para confirmarlo",
    "parejo": "Sin diferencia: ellas y ellos contactan igual",
    "ellas_avanzan": "Las que miran, contactan más que ellos",
}


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _un_genero(seg: dict | None) -> bool:
    return bool(seg and seg.get("genders") and len(seg["genders"]) == 1)


def _corta_antes_de_55(seg: dict | None) -> bool:
    try:
        return bool(seg and seg.get("age_max") and int(seg["age_max"]) < 55)
    except (TypeError, ValueError):
        return False


def _c(v: Any, dec: int = 1) -> str:
    """Número con coma decimal: 32.2 → '32,2'."""
    return f"{v:.{dec}f}".replace(".", ",") if isinstance(v, (int, float)) else "—"


def _num(x: Any) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _angulos_de(ad: dict[str, Any]) -> list[str]:
    texto = f"{ad.get('title') or ''} {ad.get('body') or ''} {ad.get('ad_name') or ''}".lower()
    return [INTEREST_LABELS[i] for i, regla in enumerate(RULES)
            if any(re.search(k, texto) for k in regla["keywords"])]


def _razon_mh(pares: list[tuple[float, float, float, float]]) -> tuple[float | None, int, int]:
    """Razón de tasas de Mantel-Haenszel del grupo A contra el B, por conjunto.

    ``pares`` = (clics A, contactos A, clics B, contactos B) de cada conjunto.
    Devuelve (razón, conjuntos comparados, conjuntos donde A convierte menos).
    """
    num = den = 0.0
    n_conj = menos = 0
    for n1, a, n0, b in pares:
        if a + b < MIN_CONTACTOS_CONJUNTO or not n1 or not n0:
            continue
        n = n1 + n0
        num += a * n0 / n
        den += b * n1 / n
        n_conj += 1
        menos += 1 if a / n1 < b / n0 else 0
    return (round(num / den, 2) if den else None), n_conj, menos


def _lectura_genero(razon: float | None, conjuntos: int, menos: int) -> str | None:
    if razon is None:
        return None
    if razon < 0.92:
        return "ella_mira" if conjuntos >= MIN_CONJUNTOS_SEÑAL and menos / conjuntos >= 0.6 else "tendencia"
    if razon > 1.08:
        return "ellas_avanzan"
    return "parejo"


# ----------------------------------------------------------------------
# 1. Quién mira y quién da el paso
# ----------------------------------------------------------------------

def _embudo(filas: list[dict[str, Any]], segm: dict[str, dict]) -> dict[str, Any] | None:
    """Clics y contactos por género y edad de un grupo de filas (marca o modelo)."""
    genero = {"female": [0.0, 0.0], "male": [0.0, 0.0]}
    edad = {e: [0.0, 0.0] for e in EDADES}
    por_conj_g: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"female": [0.0, 0.0], "male": [0.0, 0.0]})
    por_conj_e: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"may": [0.0, 0.0], "men": [0.0, 0.0]})
    for r in filas:
        seg = segm.get(str(r.get("adset_id") or ""))
        clics, cont = _num(r.get("inline_link_clicks")), _num(r.get("contactos"))
        if not _un_genero(seg) and r.get("gender") in genero:
            genero[r["gender"]][0] += clics
            genero[r["gender"]][1] += cont
            x = por_conj_g[str(r.get("adset_id"))][r["gender"]]
            x[0] += clics
            x[1] += cont
        if r.get("age") in edad:
            edad[r["age"]][0] += clics
            edad[r["age"]][1] += cont
            if not _corta_antes_de_55(seg):
                x = por_conj_e[str(r.get("adset_id"))]["may" if r["age"] in MAYORES else "men"]
                x[0] += clics
                x[1] += cont
    clics = genero["female"][0] + genero["male"][0]
    cont = genero["female"][1] + genero["male"][1]
    if not clics or cont < MIN_CONTACTOS_MARCA:
        return None
    razon, conj, menos = _razon_mh([(g["female"][0], g["female"][1], g["male"][0], g["male"][1])
                                    for g in por_conj_g.values()])
    razon_55, conj_55, menos_55 = _razon_mh([(g["may"][0], g["may"][1], g["men"][0], g["men"][1])
                                             for g in por_conj_e.values()])
    return {
        "clics": int(clics),
        "contactos": int(cont),
        "mujeres_clics_pct": round(genero["female"][0] / clics * 100, 1),
        "mujeres_contactos_pct": round(genero["female"][1] / cont * 100, 1) if cont else 0.0,
        "ellas_vs_ellos": razon,
        "conjuntos": conj,
        "conjuntos_ellas_menos": menos,
        "lectura": _lectura_genero(razon, conj, menos),
        "tasa_por_edad": {e: round(v[1] / v[0] * 100, 1) for e, v in edad.items() if v[0] >= 300},
        "mayores55_vs_resto": razon_55,
        "conjuntos_edad": conj_55,
    }


# ----------------------------------------------------------------------
# 2. Qué le interesa a cada uno
# ----------------------------------------------------------------------

def _temas(filas_modelo: dict[str, list[dict]], ads_por_id: dict[str, dict], segm: dict[str, dict],
           ad_conjunto: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for modelo, filas in filas_modelo.items():
        base = [0.0, 0.0, 0.0, 0.0]   # clics sin sesgo de género, de mujeres, sin corte de edad, de 55+
        celda: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        por_anuncio: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for r in filas:
            c = _num(r.get("clicks"))
            if not c:
                continue
            ad_id = str(r.get("ad_id"))
            seg = segm.get(str(r.get("adset_id") or ad_conjunto.get(ad_id, "")))
            v = [0.0, 0.0, 0.0, 0.0]
            if not _un_genero(seg):
                v[0], v[1] = c, (c if r.get("gender") == "female" else 0.0)
            if not _corta_antes_de_55(seg):
                v[2], v[3] = c, (c if r.get("age") in MAYORES else 0.0)
            for i in range(4):
                base[i] += v[i]
            for tema in _angulos_de(ads_por_id.get(ad_id) or {"ad_name": r.get("ad_name", "")}):
                for i in range(4):
                    celda[tema][i] += v[i]
                por_anuncio[tema][ad_id] += c
        if not base[0] or not base[2]:
            continue
        pm, p55 = base[1] / base[0] * 100, base[3] / base[2] * 100
        filas_out = []
        for tema, (cg, mu, ce, ma) in celda.items():
            anuncios = por_anuncio[tema]
            if cg < MIN_CLICS_CELDA or not ce or len(anuncios) < MIN_ANUNCIOS_CELDA:
                continue
            if max(anuncios.values()) / sum(anuncios.values()) > MAX_PESO_UN_ANUNCIO:
                continue
            dm, d55 = mu / cg * 100 - pm, ma / ce * 100 - p55
            if abs(dm) < DIF_MUJERES_PP and abs(d55) < DIF_MAYORES_PP:
                continue
            filas_out.append({"tema": tema, "clics": int(cg), "anuncios": len(anuncios),
                              "mujeres_pct": round(mu / cg * 100, 1), "mujeres_modelo_pct": round(pm, 1),
                              "dif_mujeres_pp": round(dm, 1), "mayores55_pct": round(ma / ce * 100, 1),
                              "mayores55_modelo_pct": round(p55, 1), "dif_55_pp": round(d55, 1)})
        if filas_out:
            out[modelo] = sorted(filas_out, key=lambda f: -f["dif_mujeres_pp"])
    return out


# ----------------------------------------------------------------------
# 4. Conversaciones (job semanal)
# ----------------------------------------------------------------------

def cargar_conversaciones(raw_dir: str, hoy: date | None = None) -> dict[str, Any] | None:
    """Último resumen de ``conversaciones_actores_*.json`` si tiene menos de 3 semanas."""
    hoy = hoy or date.today()
    archivos = sorted(glob.glob(os.path.join(raw_dir, "conversaciones_actores_*.json")))
    if not archivos:
        return None
    ruta = archivos[-1]
    try:
        with open(ruta, encoding="utf-8") as fh:
            data = json.load(fh)
        hasta = datetime.strptime(data["periodo"]["hasta"], "%Y-%m-%d").date()
    except (OSError, ValueError, KeyError) as exc:
        logger.warning("Centro de compra: no se pudo leer %s: %s", ruta, exc)
        return None
    if (hoy - hasta).days > CONVERSACIONES_MAX_DIAS:
        logger.info("Centro de compra: conversaciones de %s, más viejas de %d días: no se usan", hasta, CONVERSACIONES_MAX_DIAS)
        return None
    return data


# ----------------------------------------------------------------------
# Recomendaciones para Meta Ads
# ----------------------------------------------------------------------

def _recomendaciones(marca: str, m: dict[str, Any]) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    emb = m.get("embudo") or {}
    temas = m.get("temas") or {}
    # Temas que atraen a las mujeres por encima del modelo, ordenados por peso
    a_favor = sorted(((mod, t) for mod, ts in temas.items() for t in ts if t["dif_mujeres_pp"] >= DIF_MUJERES_PP),
                     key=lambda x: (-x[1]["dif_mujeres_pp"], -x[1]["clics"]))
    tema_top = a_favor[0][1]["tema"] if a_favor else None
    modelos_tema = sorted({mod for mod, t in a_favor if t["tema"] == tema_top}) if tema_top else []

    modelos_emb = {mod: (x.get("embudo") or {}) for mod, x in (m.get("modelos") or {}).items()}
    brecha = sorted(((mod, e) for mod, e in modelos_emb.items() if e.get("lectura") == "ella_mira"),
                    key=lambda x: x[1]["ellas_vs_ellos"])
    avanzan = sorted(((mod, e) for mod, e in modelos_emb.items()
                      if (e.get("ellas_vs_ellos") or 0) >= 1.2 and e.get("conjuntos", 0) >= 3),
                     key=lambda x: -x[1]["ellas_vs_ellos"])

    if emb.get("lectura") in ("ella_mira", "tendencia") or a_favor or brecha:
        titulo, texto = PIEZA_POR_TEMA.get(tema_top or "Probar antes de comprar (test drive)")
        por_que = []
        if emb.get("lectura") in ("ella_mira", "tendencia"):
            por_que.append(
                f"Ellas son el {_c(emb['mujeres_clics_pct'])} % de los clics, pero con el mismo anuncio contactan "
                f"{_c(emb['ellas_vs_ellos'], 2)}× lo que ellos (menos en {emb['conjuntos_ellas_menos']} de "
                f"{emb['conjuntos']} conjuntos): ella investiga y él da el paso.")
        if brecha:
            por_que.append("Donde más se nota: " + ", ".join(
                f"{mod} ({_c(e['ellas_vs_ellos'], 2)}×)" for mod, e in brecha[:4]) + ".")
        if tema_top:
            difs = [t for mod, t in a_favor if t["tema"] == tema_top]
            top = max(difs, key=lambda t: t["dif_mujeres_pp"])
            rango = (f"entre {_c(min(t['dif_mujeres_pp'] for t in difs), 0)} y {_c(top['dif_mujeres_pp'], 0)} puntos"
                     if len(difs) > 1 else f"{_c(top['dif_mujeres_pp'], 0)} puntos")
            por_que.append(
                f"El tema **{tema_top.lower()}** es el que más las atrae: en {', '.join(modelos_tema[:3])} "
                f"suma {rango} de mujeres sobre el promedio del modelo (hasta {_c(top['mujeres_pct'])} %).")
        recs.append({
            "clave": "acompañante",
            "titulo": "Una pieza para quien acompaña la decisión",
            "por_que": por_que,
            "modelos": modelos_tema or [],
            "pieza_titulo": titulo,
            "pieza_texto": texto,
            "donde": ("Como un anuncio más dentro del conjunto que ya funciona, con el mismo formulario o WhatsApp. "
                      "Sin cortar por género ni por edad: con Advantage+ Meta se la muestra a quien responde. "
                      "No usar la edad sugerida: en Renew dejó sin entrega a las campañas (23-09-2026)."),
            "medir": ("Ads Manager → Desglose → Por entrega → Edad y Sexo. Tasa de contacto = resultados ÷ clics en el "
                      "enlace. Éxito: que la tasa de ellas en la pieza nueva se acerque a la de ellos, sin subir el costo "
                      "por resultado del conjunto. Mirarlo después de 7 días y con al menos 30 resultados."),
        })

    if emb.get("lectura") == "ellas_avanzan" or avanzan:
        base = emb if emb.get("lectura") == "ellas_avanzan" else avanzan[0][1]
        por_que = [f"Ellas son solo el {_c(base['mujeres_clics_pct'])} % de los clics, pero las que hacen clic contactan "
                   f"{_c(base['ellas_vs_ellos'], 2)}× lo que ellos con el mismo anuncio: cuando la pieza les llega, avanzan."]
        if avanzan:
            por_que.append("Más fuerte en " + ", ".join(f"{mod} ({_c(e['ellas_vs_ellos'], 2)}×)" for mod, e in avanzan[:4]) + ".")
        tema = tema_top or "Familia y espacio"
        titulo, texto = PIEZA_POR_TEMA[tema]
        recs.append({
            "clave": "ellas_avanzan",
            "titulo": "Una pieza que les hable a ellas, que son las que avanzan",
            "por_que": por_que,
            "modelos": [mod for mod, _ in avanzan[:4]],
            "pieza_titulo": titulo,
            "pieza_texto": texto,
            "donde": ("Como un anuncio más en el conjunto del modelo, con el mismo formulario o WhatsApp. Sin cortar por género: "
                      "si la pieza les habla, Meta se la muestra más a ellas solo."),
            "medir": ("Ads Manager → Desglose → Por entrega → Edad y Sexo: que suba la parte de mujeres en los resultados sin "
                      "subir el costo por resultado. Mirarlo después de 7 días y con al menos 30 resultados."),
        })

    emp = m.get("empresa") or {}
    altos = [x for x in emp.get("modelos", []) if x["empresa_pct"] >= EMPRESA_ALTA_PCT + 10]
    if (emp.get("empresa_pct") or 0) >= EMPRESA_ALTA_PCT or altos:
        foco = altos[:3]
        por_que = [f"El {_c(emp.get('empresa_pct'))} % de las compras a cliente final de {marca} las factura una empresa "
                   f"({emp.get('ventas')} ventas en 12 meses)."]
        if foco:
            por_que.append("Más alto en " + ", ".join(f"{x['modelo']} ({_c(x['empresa_pct'])} %)" for x in foco) + ".")
        por_que.append("Cuando compra una empresa, decide el dueño o un gerente y maneja otro: "
                       "el mensaje de la persona (familia, estilo) no le habla a quien firma.")
        recs.append({
            "clave": "empresa",
            "titulo": "Una pieza para quien compra a nombre de su empresa",
            "por_que": por_que,
            "modelos": [x["modelo"] for x in foco],
            "pieza_titulo": "Para tu empresa",
            "pieza_texto": ("¿La comprás a nombre de tu empresa? Te armamos la propuesta con facturación empresarial "
                            "y te acompañamos en toda la compra."),
            "donde": ("Anuncio aparte en el mismo conjunto del modelo. Sin intereses nuevos: el texto hace el filtro. "
                      "Si el formulario tiene campo libre, el asesor confirma en la primera llamada si es para empresa."),
            "medir": ("Resultados y costo por resultado de la pieza contra el anuncio principal, y en Bitrix/ERP cuántas "
                      "ventas salen facturadas a empresa. Mirarlo a los 14 días."),
        })

    conv = m.get("conversaciones") or {}
    if conv.get("con_otra_persona_pct", 0) >= 3 and conv.get("con_texto_del_cliente", 0) >= 100:
        actores = list((conv.get("actores") or {}).items())[:3]
        recs.append({
            "clave": "compartir",
            "titulo": "Darle al cliente algo para mostrarle a quien decide con él",
            "por_que": [f"En el {_c(conv['con_otra_persona_pct'])} % de los chats de Messenger e Instagram el cliente nombra "
                        f"a otra persona" + (f" (sobre todo: {', '.join(f'{k} {v}' for k, v in actores)})" if actores else "")
                        + (f"; en {conv.get('lo_consulta_con_alguien', 0)} dice que lo tiene que consultar." if conv.get("lo_consulta_con_alguien") else ".")],
            "modelos": [],
            "pieza_titulo": "Compartila con quien decide con vos",
            "pieza_texto": "Te mandamos la ficha y la cotización para que la vean juntos, y los esperamos a los dos para la prueba.",
            "donde": ("En el mensaje de bienvenida del chat (WhatsApp/Messenger) y en el guion del asesor, no en el anuncio: "
                      "es el momento en que aparece la otra persona."),
            "medir": "Cuántos chats piden la ficha para compartir y cuántos agendan prueba para dos (Bitrix).",
        })
    return recs


# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------

def analizar(data_sources: dict[str, Any], raw_dir: str = "output/raw") -> dict[str, Any]:
    """Centro de compra por marca y modelo a partir de las fuentes del pipeline."""
    from src.generators.persona_generator import detect_models_in_ads  # evita import circular

    meta = data_sources.get("meta_ads") or {}
    filas = (meta.get("demographics") or {}).get("age_gender_ad") or []
    segm = meta.get("adset_demo_targeting") or {}
    ads = {str(a.get("ad_id")): a for a in meta.get("ad_creatives") or [] if a.get("ad_id")}
    out: dict[str, Any] = {
        "periodo_meta": meta.get("date_range") or {},
        "con_contactos": any("contactos" in r for r in filas[:50]),
        "marcas": {},
    }
    if not out["con_contactos"]:
        logger.info("Centro de compra: el JSON de Meta no trae contactos por anuncio (corrida vieja): se omite Meta")
        filas = []

    por_marca: dict[str, list[dict]] = defaultdict(list)
    por_modelo: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    cache: dict[tuple[str, str], list[str]] = {}
    for r in filas:
        marca = r.get("account", "")
        if not marca:
            continue
        por_marca[marca].append(r)
        clave = (marca, str(r.get("ad_id")))
        if clave not in cache:
            ad = ads.get(clave[1]) or {"ad_name": r.get("ad_name", "")}
            cache[clave] = list(detect_models_in_ads([ad], marca).keys())
        for modelo in cache[clave]:
            por_modelo[marca][modelo].append(r)

    ad_conjunto = {str(r.get("ad_id")): str(r.get("adset_id")) for r in filas if r.get("adset_id")}
    ventas = (data_sources.get("sales") or {}).get("comprador_empresa") or {}
    conv = cargar_conversaciones(raw_dir)
    marcas = set(por_marca) | set(ventas.get("por_marca", {})) | set((conv or {}).get("marcas", {}))

    for marca in sorted(marcas):
        m: dict[str, Any] = {"embudo": _embudo(por_marca.get(marca, []), segm)}
        m["modelos"] = {}
        for modelo, fm in por_modelo.get(marca, {}).items():
            e = _embudo(fm, segm)
            if e:
                m["modelos"][modelo] = {"embudo": e}
        m["temas"] = _temas(por_modelo.get(marca, {}), ads, segm, ad_conjunto)
        vm = ventas.get("por_marca", {}).get(marca)
        if vm and vm.get("ventas", 0) >= MIN_VENTAS_EMPRESA:
            modelos = [{"modelo": k, **v} for k, v in ventas.get("por_modelo", {}).items()
                       if k.startswith(marca) and v.get("ventas", 0) >= MIN_VENTAS_EMPRESA]
            m["empresa"] = {**vm, "desde": ventas.get("desde"), "hasta": ventas.get("hasta"),
                            "modelos": sorted(modelos, key=lambda x: -x["empresa_pct"])}
            for x in modelos:
                m["modelos"].setdefault(x["modelo"], {})["empresa"] = x
        if conv and marca in conv.get("marcas", {}):
            m["conversaciones"] = {**conv["marcas"][marca], "periodo": conv.get("periodo"), "fuente": conv.get("fuente")}
        if not (m["embudo"] or m.get("empresa") or m.get("conversaciones")):
            continue
        m["meta_ads"] = _recomendaciones(marca, m)
        out["marcas"][marca] = m
    logger.info("Centro de compra: %d marcas con datos", len(out["marcas"]))
    return out


def resumen_de(centro: dict[str, Any], marca: str, modelo: str | None = None) -> dict[str, Any] | None:
    """Lo que la ficha de una marca o de un modelo necesita mostrar."""
    m = (centro or {}).get("marcas", {}).get(marca)
    if not m:
        return None
    if modelo is None:
        return {"marca": marca, "embudo": m.get("embudo"), "empresa": m.get("empresa"),
                "recomendaciones": [r["titulo"] for r in m.get("meta_ads", [])]}
    mod = m.get("modelos", {}).get(modelo) or {}
    temas = m.get("temas", {}).get(modelo) or []
    if not (mod or temas):
        return None
    return {"marca": marca, "modelo": modelo, "embudo": mod.get("embudo"), "empresa": mod.get("empresa"),
            "temas": temas[:3]}
