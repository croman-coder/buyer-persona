"""Lectura de los anuncios activos de la competencia en la Biblioteca de Anuncios de Meta.

Qué hace: toma las capturas que deja una sesión de lectura (una por competidor, ver el skill
``biblioteca-competencia``) y las convierte en datos comparables: de qué trata cada anuncio, qué ofrece, cómo
está armado (gancho, formato, botón), hace cuánto corre y qué cambió desde la lectura anterior.

Qué NO hace: leer la Biblioteca. La API oficial de Meta no entrega anuncios comerciales de Paraguay (solo los
de temas sociales, elecciones y política, y todos los de la UE) y la página pública no se entrega a navegadores
automatizados. La captura la hace una persona, o una sesión de Claude con un navegador real.

Solo uso interno: por ley de Paraguay no se puede nombrar marcas ni modelos de la competencia en un texto público.

Privacidad: solo se guardan páginas oficiales de cada competidor. Las páginas personales de asesores se cuentan
sin nombre. Nunca se guardan datos de clientes.
"""
from __future__ import annotations

import json
import re
import statistics
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "set": 9,
         "oct": 10, "nov": 11, "dic": 12}

# Competidores del monitor de webs (scripts/monitor_competencia.py). «paginas» son las páginas oficiales de cada
# uno en Meta (expresiones sobre el nombre, sin acentos y en minúsculas); «compite_con» sale de ese mismo monitor.
# Diesa no lleva marcas propias: su BYD compite con Zeekr, Leapmotor y JMEV pero todavía no se leyó la página de BYD.
COMPETIDORES: list[dict[str, Any]] = [
    {"slug": "nipon", "nombre": "Nipon Automotores", "vende": "Mitsubishi (mismo producto que nosotros)",
     "consulta": "Nipon Automotores", "paginas": [r"^nipon automotores"], "compite_con": ["Mitsubishi"], "directo": True},
    {"slug": "garden-kia", "nombre": "Garden · Kia", "vende": "Kia", "consulta": "Kia Paraguay",
     "paginas": [r"^kia paraguay$"], "compite_con": []},
    {"slug": "chery", "nombre": "Garden · Chery", "vende": "Chery e iCAUR", "consulta": "Chery Paraguay",
     "paginas": [r"^chery paraguay$", r"^icaur paraguay$"], "compite_con": ["Jetour", "Soueast"]},
    {"slug": "geely", "nombre": "Geely Paraguay", "vende": "Geely", "consulta": "Geely Paraguay",
     "paginas": [r"^geely paraguay$"], "compite_con": ["Jetour", "Soueast"]},
    {"slug": "diesa", "nombre": "Diesa", "vende": "Volkswagen y Honda (BYD va aparte)", "consulta": "Diesa",
     "paginas": [r"^volkswagen$", r"^volkswagen camiones", r"^honda paraguay$", r"^diesa"], "compite_con": []},
    {"slug": "byd", "nombre": "BYD (Diesa)", "vende": "BYD", "consulta": "BYD Paraguay",
     "paginas": [r"^byd paraguay", r"^byd diesa", r"^byd py"], "compite_con": ["Zeekr", "Leapmotor", "JMEV"],
     "aviso": "El 12-10 no apareció una página de BYD de Paraguay con anuncios activos: al buscar «BYD» salen concesionarios de Brasil y "
              "exportadores, que no son competencia local y no se leen. Si BYD pauta con otro nombre, sumar esa página a COMPETIDORES."},
    {"slug": "chevrolet", "nombre": "Garden · Chevrolet", "vende": "Chevrolet", "consulta": "Chevrolet",
     "paginas": [r"^chevrolet$", r"^chevrolet - tema$"], "compite_con": [],
     "aviso": "Se leyeron las páginas «Chevrolet» y «Chevrolet - TEMA» por su nombre. No se verificó en Meta quién es el dueño de cada una: "
              "el proyecto ubica Chevrolet en Garden."},
    {"slug": "mazda", "nombre": "Garden · Mazda", "vende": "Mazda", "consulta": "Mazda Paraguay",
     "paginas": [r"^mazda paraguay$"], "compite_con": []},
    {"slug": "toyotoshi", "nombre": "Toyotoshi", "vende": "Toyota y Lexus", "consulta": "Toyotoshi",
     "paginas": [r"^toyotoshi s\.a\.$", r"^usados toyotoshi", r"^lexus paraguay$"], "compite_con": []},
    {"slug": "nissan", "nombre": "Nissan Paraguay", "vende": "Nissan", "consulta": "Nissan Paraguay",
     "paginas": [r"^nissan paraguay$"], "compite_con": ["Renault", "Jetour", "GWM", "JAC", "Mitsubishi"]},
    {"slug": "automaq", "nombre": "Automaq", "vende": "Peugeot, Citroën y Kaiyi", "consulta": "Automaq",
     "paginas": [r"^automaq$", r"^automaq usados", r"^kaiyi paraguay$", r"^citroen$", r"^peugeot"], "compite_con": []},
    {"slug": "dls", "nombre": "DLS Motors", "vende": "GAC", "consulta": "DLS Motors",
     "paginas": [r"^dls", r"^gac"], "compite_con": []},
]

ASESOR = "Asesor (página personal)"   # nombre con el que se anotan los anuncios de páginas personales de asesores

TEMAS = {"oferta": "Oferta (precio, cuotas o bono)", "lanzamiento": "Lanzamiento o novedad",
         "producto": "Muestra el modelo", "postventa": "Postventa y service", "institucional": "Marca o sucursal"}

# «Novedad» se busca sobre el texto original: «nuevo» solo cuenta si va seguido de un nombre propio («Nuevo Tiguan»);
# «como nuevo» o «nuevos caminos» no son un lanzamiento.
NOVEDAD = re.compile(r"\b[Nn]uev[oa]s?\s+[A-ZÁÉÍÓÚ0-9]|\b[Aa]ll[- ][Nn]ew|\b[Ll]leg[óo]\b|\b[Ll]egamos\b|\b[Ll]anzamiento|\b[Pp]reventa|\blo nuevo\b|\b2027\b")

# Cada patrón se busca sobre el texto sin acentos y en minúsculas.
PATRONES = {
    "precio": r"(gs\.?|usd|u\$s|\$)\s?\d[\d.,]*|\bdesde\s+(gs|usd)",
    "cuotas": r"cuota|financ|sin interes|entrega inicial|entrega usd|plan(es)? de pago|\btasa\b",
    "bono": r"\bbono|descuento|bonific|promo|\boferta|precio promocional",
    "cero_km": r"\b0 ?km\b|cero ?km",
    "test_drive": r"test drive|prueba de manejo",
    "postventa": r"service|servicio|taller|repuesto|posventa|postventa|mantenimiento|lavado|garantia|aceite|frenos|neumaticos|chequeo",
    "institucional": r"\b\d{2,3} anos\b|aniversario|sucursal|abrimos",
    "urgencia": r"stock limitado|ultimos|solo por|hasta el|durante todo|este mes|aprovech|tiempo limitado|cupos?\b",
}

CTAS = [("WhatsApp", r"whatsapp"), ("Cotizar", r"get quote|cotiz"),
        ("Registrarse o enviar solicitud", r"registrarte|apply now|enviar solicitud|request time"),
        ("Enviar mensaje", r"^enviar mensaje$"),
        ("Ver más", r"^(ver mas|conocer mas\.?|see details|watch more|conoce mas de .*)$")]

_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅‼]")


def sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower()


def fecha_de(texto: str) -> date | None:
    """«7 oct 2026» → date(2026, 10, 7)."""
    m = re.match(r"\s*(\d{1,2}) (\w{3})\w* (\d{4})", sin_acentos(texto or ""))
    if not m or m.group(2) not in MESES:
        return None
    try:
        return date(int(m.group(3)), MESES[m.group(2)], int(m.group(1)))
    except ValueError:
        return None


def _es_cta(seg: str) -> str | None:
    s = sin_acentos(seg).strip()
    if len(s) >= 60:
        return None
    for nombre, patron in CTAS:
        if re.search(patron, s):
            return nombre
    return None


def _es_ruido(seg: str) -> bool:
    """Minutos del video, dominios en mayúsculas, estado y botones: no son el texto del anuncio."""
    s = seg.strip()
    return (not s or bool(re.fullmatch(r"\d+:\d{2}", s)) or s in ("Activo", "See Details", "Auto Dealer")
            or (s.upper() == s and ("." in s or s in ("WHATSAPP", "FB.ME"))) or _es_cta(s) is not None)


def analizar_anuncio(fila: list[str], hoy: date) -> dict[str, Any]:
    """[id, «7 oct 2026», página, cuerpo] → ficha del anuncio."""
    id_, desde_txt, pagina, cuerpo = fila[0], fila[1], fila[2], fila[3]
    segs = [s.strip() for s in cuerpo.split(" / ")]
    texto = " / ".join(s for s in segs if not _es_ruido(s))
    plano = sin_acentos(texto)
    tags = [k for k, p in PATRONES.items() if re.search(p, plano)]
    if NOVEDAD.search(texto):
        tags.append("lanzamiento")
    if "precio" in tags or "cuotas" in tags or "bono" in tags:
        tema = "oferta"
    elif "institucional" in tags:
        tema = "institucional"
    elif "postventa" in tags and "lanzamiento" not in tags:
        tema = "postventa"
    elif "lanzamiento" in tags:
        tema = "lanzamiento"
    else:
        tema = "producto"
    desde = fecha_de(desde_txt)
    ctas = [c for c in (_es_cta(s) for s in segs) if c]
    gancho = next((s for s in segs if not _es_ruido(s)), "")
    return {"id": id_, "pagina": pagina, "desde": desde.isoformat() if desde else None,
            "dias": (hoy - desde).days if desde else None, "tema": tema, "tags": tags,
            "formato": "video" if any(re.fullmatch(r"\d+:\d{2}", s) for s in segs) else "imagen o carrusel",
            "cta": ctas[0] if ctas else None, "gancho": gancho[:160], "texto": texto,
            "hashtags": len(re.findall(r"#\w+", texto)), "emojis": len(_EMOJI.findall(texto)),
            "palabras": len(texto.split())}


def frase_oferta(a: dict[str, Any]) -> str:
    """La frase del anuncio que contiene la oferta (precio, cuotas, bono); si no hay, el gancho."""
    patron = re.compile("|".join(PATRONES[k] for k in ("precio", "cuotas", "bono")))
    for trozo in a["texto"].split(" / "):
        # no corta en «Gs.» ni en números: solo después de «!», «?» o de un punto que sigue a una palabra de 3 letras o más
        for frase in re.split(r"(?<=[!?])\s+|(?<=[a-záéíóú]{3}\.)\s+(?=[A-ZÁÉÍÓÚ¡¿])", trozo):
            if patron.search(sin_acentos(frase)):
                return frase.strip()
    return a["gancho"]


def agrupar_iguales(ads: list[dict[str, Any]]) -> list[tuple[dict[str, Any], int]]:
    """Un mismo creativo suele estar en varias páginas (casa matriz y sucursales): se cuenta una vez."""
    vistos: dict[str, tuple[dict[str, Any], int]] = {}
    for a in ads:
        clave = sin_acentos(a["texto"])
        vistos[clave] = (vistos[clave][0], vistos[clave][1] + 1) if clave in vistos else (a, 1)
    return list(vistos.values())


def es_oficial(pagina: str, comp: dict[str, Any]) -> bool:
    n = sin_acentos(pagina).strip()
    return any(re.search(p, n) for p in comp["paginas"])


def leer_capturas(carpeta: Path, hoy: date) -> dict[str, dict[str, Any]]:
    """Una captura por competidor → fichas de anuncios. Lo que no es página oficial ni asesor anotado se descarta."""
    out: dict[str, dict[str, Any]] = {}
    for comp in COMPETIDORES:
        f = carpeta / f"{comp['slug']}.json"
        if not f.exists():
            continue
        cap = json.loads(f.read_text(encoding="utf-8"))
        ads, asesores = [], 0
        for fila in cap.get("ads", []):
            if fila[2] == ASESOR:
                asesores += 1
            elif es_oficial(fila[2], comp):
                ads.append(analizar_anuncio(fila, hoy))
        out[comp["slug"]] = {"comp": comp, "ads": ads, "consulta": cap.get("consulta"), "total_consulta": cap.get("total_consulta"),
                             "cargados": cap.get("cargados", 0), "asesores": max(cap.get("asesores", 0), asesores)}
    return out


def resumen(ads: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(ads)
    temas = {t: sum(1 for a in ads if a["tema"] == t) for t in TEMAS}
    ctas: dict[str, int] = {}
    for a in ads:
        if a["cta"]:
            ctas[a["cta"]] = ctas.get(a["cta"], 0) + 1
    dias = [a["dias"] for a in ads if a["dias"] is not None]
    etiquetas = {t: sum(1 for a in ads if t in a["tags"]) for t in [*PATRONES, "lanzamiento"]}
    return {"n": n, "temas": temas, "ctas": dict(sorted(ctas.items(), key=lambda x: -x[1])),
            "video": sum(1 for a in ads if a["formato"] == "video"), "etiquetas": etiquetas,
            "dias_mediana": int(statistics.median(dias)) if dias else None,
            "nuevos_7d": sum(1 for d in dias if d <= 7), "sostenidos_30d": sum(1 for d in dias if d >= 30),
            "palabras_mediana": int(statistics.median([a["palabras"] for a in ads])) if ads else None}


def comparar(previos: list[str], actuales: list[str]) -> dict[str, list[str]]:
    p, a = set(previos), set(actuales)
    return {"nuevos": sorted(a - p), "terminados": sorted(p - a)}


# ---------------------------------------------------------------------------
# Memoria (en el vault, para que viaje con él y sirva de comparación entre lecturas)
# ---------------------------------------------------------------------------

def cargar_historial(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    out = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(linea))
        except ValueError:
            continue
    return out


def guardar_lectura(ruta: Path, fecha: str, leidos: dict[str, dict[str, Any]]) -> None:
    """Una línea por competidor y fecha; si se vuelve a leer el mismo día, reemplaza la anterior."""
    filas = [f for f in cargar_historial(ruta) if f.get("fecha") != fecha]
    for slug, d in leidos.items():
        filas.append({"fecha": fecha, "competidor": slug, "vistos": len(d["ads"]), "asesores": d["asesores"],
                      "ids": [a["id"] for a in d["ads"]],
                      "anuncios": [{"id": a["id"], "desde": a["desde"], "tema": a["tema"]} for a in d["ads"]]})
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in filas) + "\n", encoding="utf-8")


def lectura_anterior(historial: list[dict[str, Any]], slug: str, fecha: str) -> dict[str, Any] | None:
    previas = [f for f in historial if f["competidor"] == slug and f["fecha"] < fecha]
    return max(previas, key=lambda f: f["fecha"]) if previas else None


# ---------------------------------------------------------------------------
# Qué responder (sugerencias; siempre con argumentos propios y sin nombrar al rival)
# ---------------------------------------------------------------------------

def _financiacion(marca_persona: dict[str, Any]) -> tuple[int, int] | None:
    for s in ((marca_persona.get("nse") or {}).get("senales") or []):
        m = re.search(r"(\d+)% pide financiación.*\((\d+) respuestas\)", s)
        if m and int(m.group(2)) >= 30:
            return int(m.group(1)), int(m.group(2))
    return None


def _tema_top(marca_persona: dict[str, Any]) -> tuple[str, int] | None:
    t = ((marca_persona.get("observed_interests") or {}).get("temas") or [])
    return (t[0]["tema"], round(t[0]["pct"])) if t else None


def que_responder(comp: dict[str, Any], r: dict[str, Any], marcas: dict[str, Any] | None) -> list[str]:
    """Pistas para responder, ancladas en lo que mide el Buyer Persona de las marcas que compiten con ese rival."""
    n = r["n"]
    if not n:
        return []
    et, mis = r["etiquetas"], marcas or {}
    propias = [m for m in comp["compite_con"] if (mis.get(m) or {}).get("marca")]
    pistas: list[str] = []
    if et["cuotas"]:
        base = f"Hablan de financiación o entrega inicial en {et['cuotas']} de {n} anuncios."
        datos = [f"{m} {f[0]} % ({f[1]} respuestas)" for m in propias if (f := _financiacion(mis[m]["marca"]))]
        pistas.append(base + (" Dato propio, % de quienes llenan el formulario y piden financiación: " + "; ".join(datos) + "." if datos else "")
                      + " Responder con la financiación real de la marca (nota «Oferta del mes»), sin tasas ni plazos inventados.")
    if et["bono"] or et["precio"]:
        pistas.append(f"Compiten por precio o bono en {max(et['bono'], et['precio'])} de {n} anuncios. "
                      "Antes de contestar con precio, confirmar la oferta vigente de la marca; si la planilla es de un mes anterior, la nota la marca vencida.")
    if r["temas"]["postventa"]:
        top = [f"{m} «{t[0].lower()}» {t[1]} %" for m in propias if (t := _tema_top(mis[m]["marca"]))]
        pistas.append(f"Pautan postventa y service en {r['temas']['postventa']} de {n} anuncios."
                      + (" Dato propio, el tema que más repiten nuestros anuncios: " + "; ".join(top) + "." if top else "")
                      + " El respaldo y el service propios son un argumento absoluto que se puede usar.")
    if r["temas"]["lanzamiento"]:
        pistas.append(f"Tienen {r['temas']['lanzamiento']} anuncios de lanzamiento o novedad. Revisar si hay un modelo propio del mismo segmento con una pieza de novedad.")
    if et["test_drive"]:
        pistas.append(f"Piden «agendá tu test drive» en {et['test_drive']} anuncios. Responder igual solo si la nota de stock de la marca muestra unidad de prueba.")
    if comp.get("directo"):
        pistas.append("Es el mismo producto con otra concesionaria: se compite por precio, bono y servicio, no por el auto. "
                      "La pauta de Mitsubishi la maneja su agencia: coordinar antes de tocar presupuesto, segmentación o anuncios.")
    return pistas
