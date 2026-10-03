"""
Generador de Contenido de Marketing.

Crea copys de anuncios, emails y mensajes de WhatsApp personalizados
para cada Buyer Persona, listos para usar en Google Ads, Meta Ads,
campañas de email y WhatsApp Business.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime
from typing import Any

from src.catalog.models_py import category_for

logger = logging.getLogger(__name__)

# Lo que una plantilla no puede prometer: tasa, plazo, garantía o "mejor precio"
# solo salen de la oferta real de la marca (planilla de acciones), nunca de acá.
PROMESAS_SIN_RESPALDO = re.compile(r"sin inter[eé]s|\d+\s*(meses|cuotas)|\d+\s*a[nñ]os|mejor precio|garantizad"
                                   r"|entrega inmediata|garant[ií]a extendida", re.I)
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
            "septiembre", "octubre", "noviembre", "diciembre"]


def periodo_vencido(periodo: str, hoy: date) -> bool:
    """¿La planilla de acciones (período AAAA-MM) es de un mes anterior al de hoy?"""
    m = re.fullmatch(r"(\d{4})-(\d{2})", periodo or "")
    return bool(m) and (int(m.group(1)), int(m.group(2))) < (hoy.year, hoy.month)


def mes_de(periodo: str) -> str:
    """'2026-09' → 'septiembre'; '' si el período no se entiende."""
    m = re.fullmatch(r"\d{4}-(\d{2})", periodo or "")
    return MESES_ES[int(m.group(1)) - 1] if m and 1 <= int(m.group(1)) <= 12 else ""


def fecha_corta(iso: str | None) -> str:
    """'2026-09-18' → '18-09'."""
    return f"{iso[8:10]}-{iso[5:7]}" if iso and len(iso) >= 10 else ""


# Urgencia que ninguna planilla respalda: el plazo de una oferta sale de la planilla, no de acá.
URGENCIA_SIN_RESPALDO = re.compile(r"solo por este mes|hasta fin de mes|termina este mes|[uú]ltimos d[ií]as|oferta especial", re.I)
# Restos de las plantillas viejas: montos de relleno, marcadores sin completar y superlativos.
RESTOS_DE_PLANTILLA = re.compile(r"\$X|\[Concesionaria\]|\[LINK|\bGRATIS\b|mejores bancos|[uú]ltima generaci[oó]n")


class MarketingContentGenerator:
    """Genera contenido de marketing accionable desde Buyer Personas."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        # Contra esta fecha se decide si la oferta de la planilla ya venció (las pruebas la fijan).
        self.hoy: date = self.config.get("hoy") or date.today()

    def generate_all(self, personas: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Genera todo el contenido de marketing para una lista de personas.

        Returns:
            Dict con claves: ``google_ads``, ``meta_ads``, ``emails``, ``whatsapp``
        """
        result = {
            "google_ads": [],
            "meta_ads": [],
            "emails": [],
            "whatsapp": [],
        }

        for persona in personas:
            result["google_ads"].append(self._gen_google_ads(persona))
            result["meta_ads"].append(self._gen_meta_ads(persona))
            result["emails"].append(self._gen_email(persona))
            result["whatsapp"].append(self._gen_whatsapp(persona))

        return result

    # ------------------------------------------------------------------
    # Google Ads
    # ------------------------------------------------------------------

    # Límites de Google Ads para el anuncio de búsqueda responsivo y sus recursos.
    # Un texto que no entra se descarta entero y se usa la alternativa: nunca se
    # corta a la mitad (así se colaban frases como «Necesita ubicar qué escalón»).
    MAX_TITULO = 30
    MAX_DESCRIPCION = 90
    MAX_RUTA = 15
    MAX_SITELINK = 25
    MAX_SITELINK_LINEA = 35
    MAX_DESTACADO = 25

    # Tema que se repite en los anuncios del modelo (ad_copy_analyzer.INTEREST_LABELS)
    # → (título, descripción) listos para el aviso. Sin montos, tasas, plazos ni
    # garantías: una promesa concreta solo sale de la planilla de acciones comerciales.
    GOOGLE_POR_TEMA: dict[str, tuple[str, str]] = {
        "Autos eléctricos y ahorro de combustible": (
            "Eficiencia en Cada Kilómetro",
            "Consultá consumo, autonomía y costo de mantenimiento con un asesor.",
        ),
        "Financiación en cuotas": (
            "Financiación a tu Medida",
            "Consultá planes de financiación y formas de pago con un asesor.",
        ),
        "Garantía y respaldo posventa": (
            "Respaldo de Posventa Oficial",
            "Service oficial y repuestos originales, con el respaldo de la marca.",
        ),
        "Familia y espacio": (
            "Espacio para Toda la Familia",
            "Espacio y comodidad para viajar con toda la familia. Vení a conocerlo.",
        ),
        "Probar antes de comprar (test drive)": (
            "Probalo Antes de Decidir",
            "Probalo antes de decidir: coordiná tu test drive en el día y horario que prefieras.",
        ),
        "Seguridad y asistencias a la conducción": (
            "Seguridad en Cada Viaje",
            "Seguridad y asistencias a la conducción para cuidar a los que viajan con vos.",
        ),
        "Diseño y estatus": (
            "Diseño que se Nota",
            "Un diseño que se nota en cada detalle. Vení a conocerlo en persona.",
        ),
        "Trabajo, negocio y carga": (
            "Lista para Trabajar",
            "Capacidad y respaldo para tu trabajo y tu negocio, todos los días.",
        ),
        "Primer auto / primera SUV": (
            "Tu Primer 0km",
            "El primer 0km de la familia, con asesoramiento en todo el proceso.",
        ),
        "Tecnología y conectividad": (
            "Tecnología y Conectividad",
            "Tecnología y conectividad que usás todos los días. Pedí tu cotización.",
        ),
    }
    # En usados (Renew) no se habla de 0km ni de posventa oficial de fábrica.
    GOOGLE_POR_TEMA_USADO: dict[str, tuple[str, str]] = {
        "Garantía y respaldo posventa": (
            "Usado con Respaldo",
            "Usados certificados, revisados y con el respaldo de Renew.",
        ),
        "Primer auto / primera SUV": (
            "Tu Primer Auto",
            "Tu primer auto, usado certificado y con asesoramiento en todo el proceso.",
        ),
    }
    # Búsquedas de posventa o que no son de compra. "manual" no: también es la caja.
    NEGATIVAS = ["repuestos", "repuesto", "taller", "pdf", "alquiler", "empleo", "juguete", "escala"]

    @staticmethod
    def _primero_que_entra(opciones: list[str], limite: int) -> str | None:
        """La primera opción que respeta el límite; ninguna si no entra ninguna."""
        return next((o for o in opciones if o and len(o) <= limite), None)

    @staticmethod
    def _sin_tildes(texto: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")

    def _kw(self, texto: str) -> str:
        """Palabra clave como la escribe la gente: minúsculas y sin tildes."""
        return self._sin_tildes(texto).lower().strip()

    def _ruta(self, texto: str) -> str:
        """Tramo de la URL visible (máx. 15): 'Haval H6' → 'Haval-H6'."""
        r = re.sub(r"[^0-9A-Za-z]+", "-", self._sin_tildes(texto)).strip("-")
        if len(r) > self.MAX_RUTA:
            r = r.split("-")[0][: self.MAX_RUTA]
        return r

    @staticmethod
    def _usd(monto: float) -> str:
        """Monto como se escribe en Paraguay: 36990 → 'USD 36.990'."""
        return "USD " + f"{monto:,.0f}".replace(",", ".")

    def _oferta_mes(self, persona: dict[str, Any]) -> dict[str, Any] | None:
        """Precio y descuento del mes, de la planilla de acciones comerciales.

        Va aparte de los textos fijos porque vence con el mes y puede tener
        condiciones (ej. «solo válido para venta cartera Sudameris»): se confirma
        con la marca antes de publicar. La usan Google Ads, el mail y WhatsApp.
        """
        ac = ((persona.get("extras") or {}).get("acciones")) or {}
        pvp, desc = ac.get("pvp_min") or 0, ac.get("descuento_max") or 0
        if not pvp and not desc:
            return None
        periodo = ac.get("periodo") or ""
        mes = mes_de(periodo)
        condiciones = [a.strip() for a in ac.get("acciones", []) if a and a.strip() not in ("-", "")]
        if periodo_vencido(periodo, self.hoy):
            # Planilla de un mes anterior: se muestra como último dato, nunca como texto listo.
            return {"periodo": periodo, "mes": mes, "pvp_min": pvp, "descuento_max": desc, "titulos": [],
                    "descripcion": None, "condiciones": condiciones, "vencida": True}
        titulos = [t for t in ([f"Desde {self._usd(pvp)}"] if pvp else []) +
                   ([f"Hasta {self._usd(desc)} de Descuento"] if desc else [])
                   if len(t) <= self.MAX_TITULO]
        en_mes = f" en {mes}" if mes else ""
        if pvp and desc:
            opciones = [f"Desde {self._usd(pvp)} y hasta {self._usd(desc)} de descuento{en_mes}. Consultá condiciones.",
                        f"Desde {self._usd(pvp)} y hasta {self._usd(desc)} de descuento. Consultá condiciones."]
        elif desc:
            opciones = [f"Hasta {self._usd(desc)} de descuento{en_mes}. Consultá condiciones con un asesor."]
        else:
            opciones = [f"Precio de lista desde {self._usd(pvp)}. Pedí tu cotización y consultá formas de pago."]
        return {"periodo": periodo, "mes": mes, "pvp_min": pvp, "descuento_max": desc, "titulos": titulos,
                "descripcion": self._primero_que_entra(opciones, self.MAX_DESCRIPCION),
                "condiciones": condiciones, "vencida": False}

    def _contexto(self, persona: dict[str, Any]) -> dict[str, Any]:
        """Lo que Google Ads, el mail y WhatsApp necesitan saber de una persona."""
        seg = persona.get("segment", {}) or {}
        tipo = seg.get("type", "")
        productos = [p for p in persona.get("top_products", []) if p]
        if tipo == "model":
            nombre = seg.get("name") or (productos[0] if productos else "")
            marca = seg.get("brand") or nombre.split()[0]
        elif tipo == "brand":
            nombre = marca = seg.get("name", "")
        else:                                   # product_category: "Segmento SUV"
            nombre, marca = seg.get("name", "Vehículos"), ""
        usado = marca == "Renew" or (tipo == "model" and category_for(nombre) == "Usado")
        stock = (persona.get("extras") or {}).get("stock") or {}
        # Unidades en estado TEST DRIVE en el stock del ERP. Solo dice algo de un
        # modelo 0km con stock cargado; en usados o sin stock no se sabe (None).
        test_drive = stock["test_drive"] > 0 if (tipo == "model" and not usado and "test_drive" in stock) else None
        return {
            "tipo": tipo, "nombre": nombre, "marca": marca, "usado": usado,
            "corto": nombre[len(marca):].strip() if marca and nombre.startswith(marca + " ") else nombre,
            "categoria": seg.get("category") or (category_for(nombre) if tipo == "model" else ""),
            "temas": [t.get("tema") for t in (persona.get("observed_interests") or {}).get("temas", [])],
            "productos": [p[len("Renew "):] if p.startswith("Renew ") else p for p in productos[:3]],
            "test_drive": test_drive,
            "test_drive_unidades": stock.get("test_drive") if test_drive is not None else None,
            "stock_disponible": stock.get("disponible") if tipo == "model" and stock else None,
            "stock_fecha": stock.get("fecha") if stock else None,
            "oferta": self._oferta_mes(persona) if tipo == "model" else None,
        }

    def _gen_google_ads(self, persona: dict[str, Any]) -> dict[str, Any]:
        """Borrador de campaña de búsqueda (anuncio responsivo) para una persona.

        Cada texto respeta los límites de Google y sale de datos de la ficha: el
        modelo o la marca, los temas que repiten sus anuncios y, aparte, la oferta
        vigente de la planilla de acciones. Los dolores y motivaciones de la ficha
        son análisis interno y no se copian al aviso. Sin tasas, plazos ni
        garantías inventadas, y sin test drive si el stock dice que no hay unidad.
        """
        c = self._contexto(persona)
        tipo, nombre, marca, corto, usado = c["tipo"], c["nombre"], c["marca"], c["corto"], c["usado"]
        sin_marca = c["productos"]
        sin_unidad = c["test_drive"] is False          # el stock del ERP no tiene unidad de prueba
        tema_td = "Probar antes de comprar (test drive)"
        por_tema = {**self.GOOGLE_POR_TEMA, **(self.GOOGLE_POR_TEMA_USADO if usado else {})}
        de_temas = [por_tema[t] for t in c["temas"] if t in por_tema and not (sin_unidad and t == tema_td)][:4]
        invitar = ["Conocelo en el Salón"] if sin_unidad else ["Agendá tu Test Drive"]

        # --- Títulos: los fijos primero, después los temas, hasta 15 ---
        if tipo == "model" and usado:
            base = [
                [f"{corto} Usados Certificados", f"{corto} Usado Certificado", f"{corto} Usado"],
                ["Renew Usados Certificados"],
                [f"{corto} Usado en Paraguay", f"{corto} en Paraguay"],
                [f"Cotizá tu {corto} Usado", f"Cotizá tu {corto}", "Pedí tu Cotización"],
                ["Probalo Antes de Comprar"],
                ["Hablá con un Asesor"],
                ["Pedí tu Cotización Hoy"],
            ]
        elif tipo == "model":
            base = [
                [nombre, corto],
                [f"{nombre} en Paraguay", f"{corto} en Paraguay"],
                [f"Cotizá tu {corto}", "Pedí tu Cotización"],
                [f"Concesionario Oficial {marca}", "Concesionario Oficial"],
                invitar,
                [f"{corto} 0km", f"{nombre} 0km"],
                ["Versiones y Equipamiento"],
                ["Hablá con un Asesor"],
                ["Pedí tu Cotización Hoy"],
            ]
        elif tipo == "brand" and usado:
            base = [
                ["Renew Usados Certificados"],
                ["Autos Usados Certificados"],
                ["Usados en Paraguay"],
                ["Probalo Antes de Comprar"],
                *[[f"{p} Usado"] for p in sin_marca],
                ["Hablá con un Asesor"],
                ["Pedí tu Cotización Hoy"],
            ]
        elif tipo == "brand":
            base = [
                [f"{marca} en Paraguay"],
                [f"Concesionario Oficial {marca}", "Concesionario Oficial"],
                [f"{marca} 0km"],
                [f"Conocé la Gama {marca}", "Conocé Toda la Gama"],
                ["Agendá tu Test Drive"],
                *[[p] for p in sin_marca],
                ["Hablá con un Asesor"],
                ["Pedí tu Cotización Hoy"],
            ]
        else:
            base = [
                [f"{nombre} 0km en Paraguay", f"{nombre} 0km"],
                [f"Encontrá tu {nombre}"],
                ["Varias Marcas en un Lugar"],
                ["Concesionario Oficial"],
                ["Agendá tu Test Drive"],
                *[[p] for p in sin_marca],
                ["Hablá con un Asesor"],
                ["Pedí tu Cotización Hoy"],
            ]

        def sumar(opciones: list[str], limite: int, destino: list[str]) -> None:
            t = self._primero_que_entra(opciones, limite)
            if t and t.lower() not in {x.lower() for x in destino}:
                destino.append(t)

        titulos: list[str] = []
        for ops in base[:5]:
            sumar(ops, self.MAX_TITULO, titulos)
        for t, _ in de_temas:
            # El test drive ya tiene título fijo: no repetirlo con otras palabras.
            if t == por_tema[tema_td][0] and any("Test Drive" in x or x.startswith("Probalo") for x in titulos):
                continue
            sumar([t], self.MAX_TITULO, titulos)
        for ops in base[5:]:
            sumar(ops, self.MAX_TITULO, titulos)
        titulos = titulos[:15]

        # --- Descripciones: hasta 4 ---
        if tipo == "model" and usado:
            primera = [f"{corto} usados certificados en Renew: cotizá y coordiná tu visita.",
                       "Usados certificados en Renew: cotizá y coordiná tu visita."]
        elif tipo == "model":
            accion = "conocelo" if sin_unidad else "agendá tu test drive"
            primera = [f"{nombre}: cotizá y {accion} en el concesionario oficial.",
                       f"{corto}: cotizá y {accion} en el concesionario oficial.",
                       f"Cotizá y {accion} en el concesionario oficial."]
        elif tipo == "brand" and usado:
            primera = ["Usados certificados de varias marcas en Renew. Cotizá y coordiná tu visita."]
        elif tipo == "brand":
            primera = [f"Conocé la gama {marca} en el concesionario oficial. Pedí tu cotización hoy.",
                       "Conocé toda la gama en el concesionario oficial. Pedí tu cotización hoy."]
        else:
            primera = [f"{nombre} 0km de varias marcas en un solo lugar. Compará versiones y pedí tu cotización.",
                       f"{nombre} 0km de varias marcas en un solo lugar. Pedí tu cotización."]
        descripciones: list[str] = []
        sumar(primera, self.MAX_DESCRIPCION, descripciones)
        for _, d in de_temas:
            sumar([d], self.MAX_DESCRIPCION, descripciones)
        sumar(["Te asesoramos en todo el proceso, de la cotización a la entrega."], self.MAX_DESCRIPCION, descripciones)
        if not sin_unidad:
            sumar([por_tema[tema_td][1]], self.MAX_DESCRIPCION, descripciones)
        descripciones = descripciones[:4]

        # --- URL visible, palabras clave y negativas ---
        if tipo == "model":
            rutas = [self._ruta(corto), "Usados" if usado else "Cotizar"]
        elif tipo == "brand":
            rutas = [self._ruta(marca), "Usados" if usado else "Modelos"]
        else:
            rutas = [self._ruta(nombre), "0km"]
        grupos = self._gen_keywords(tipo, nombre, marca, corto, c["categoria"], usado, sin_marca, sin_unidad)
        negativas = self.NEGATIVAS + ([] if usado else ["usado", "usados"])

        # --- Extensiones ---
        sitelinks: list[dict[str, str]] = []

        def sitelink(texto: str, l1: str, l2: str) -> None:
            if len(texto) <= self.MAX_SITELINK and max(len(l1), len(l2)) <= self.MAX_SITELINK_LINEA:
                sitelinks.append({"text": texto, "desc1": l1, "desc2": l2})

        if usado:
            sitelink("Coordiná tu Visita", "Elegí el día y el horario", "Sin compromiso")
            sitelink("Financiación", "Planes a tu medida", "Consultá con un asesor")
            sitelink("Usados Disponibles", "Mirá lo que hay hoy", "Consultá por tu modelo")
        else:
            if sin_unidad:
                sitelink("Coordiná tu Visita", "Elegí el día y el horario", "Te esperamos en el salón")
            else:
                sitelink("Agendá tu Test Drive", "Elegí el día y el horario", "Sin compromiso")
            sitelink("Financiación", "Planes a tu medida", "Consultá con un asesor")
            sitelink("Versiones", "Compará las versiones", "Equipamiento de cada una")
        sitelink("Sucursales", "Encontrá la más cercana", "Horarios y ubicación")
        if usado:
            destacados = ["Usados Certificados", "Financiación Disponible", "Atención Personalizada"]
        else:
            destacados = ["Concesionario Oficial", "Financiación Disponible", "Atención Personalizada"]
            if not sin_unidad:
                destacados.insert(1, "Test Drive sin Cargo")
            if tipo == "product_category":
                destacados.insert(0, "Varias Marcas")
        destacados = [d for d in destacados if len(d) <= self.MAX_DESTACADO]

        if tipo == "model":
            campana = f"Search - {nombre}"
        elif tipo == "brand":
            campana = f"Search - Marca {marca}"
        else:
            campana = f"Search - Segmento {nombre}"
        ad = {
            "persona": persona.get("name", ""),
            "segment": (persona.get("segment") or {}).get("name", ""),
            "tipo": tipo,
            "campaign_name": campana,
            "headlines": titulos,
            "descriptions": descripciones,
            "paths": rutas,
            "keywords": [k.strip('"[]') for ks in grupos.values() for k in ks],
            "keyword_groups": grupos,
            "negative_keywords": negativas,
            "sitelinks": sitelinks,
            "callouts": destacados,
            "offer": c["oferta"],
            "used": usado,
            "test_drive": c["test_drive"],
            "test_drive_unidades": c["test_drive_unidades"],
            "stock_fecha": c["stock_fecha"],
        }
        for problema in validar_google_ads(ad):
            logger.warning("Google Ads %s: %s", ad["persona"], problema)
        return ad

    def _gen_keywords(self, tipo: str, nombre: str, marca: str, corto: str, categoria: str,
                      usado: bool, productos: list[str], sin_unidad: bool = False) -> dict[str, list[str]]:
        """Palabras clave por intención. "entre comillas" = frase, [entre corchetes] = exacta."""
        m = self._kw(marca)
        # Un nombre de 3 letras o menos ("X70", "T8", "001") solo es ambiguo: va con la marca.
        c = self._kw(nombre if len(corto) <= 3 else corto)
        if tipo == "model" and usado:
            return {
                "Modelo usado": [f'"{c} usado"', f'"{c} usados"', f'"{c} usado paraguay"'],
                "Precio y cuotas": [f'"{c} usado precio"', f'"{c} usado en cuotas"'],
                "Renew": ["[renew usados]", "[renew paraguay]", '"usados certificados"'],
            }
        if tipo == "model":
            modelo = list(dict.fromkeys([f'"{c}"', f'"{self._kw(nombre)}"', f'"{c} paraguay"']))
            marca_kw = [f"[{m} paraguay]", f"[concesionaria {m}]", f"[{m} 0km]"]
            if categoria == "Pickup":
                marca_kw += [f'"camioneta {m}"', f'"pickup {m}"']
            prueba = ([] if sin_unidad else [f'"{c} test drive"']) + [f'"{c} versiones"', f'"{c} ficha tecnica"']
            return {
                "Modelo": modelo,
                "Precio y cuotas": [f'"{c} precio"', f'"precio {c}"', f'"{c} cuotas"', f'"{c} financiacion"'],
                "Versiones" if sin_unidad else "Prueba y versiones": prueba,
                "Marca": marca_kw,
            }
        if tipo == "brand" and usado:
            return {
                "Renew": ["[renew usados]", "[renew paraguay]", '"usados certificados"', '"autos usados paraguay"'],
                "Modelos usados": [f'"{self._kw(p)} usado"' for p in productos],
            }
        if tipo == "brand":
            return {
                "Marca": [f"[{m} paraguay]", f'"{m} 0km"', f'"concesionaria {m}"', f'"{m} precios"'],
                "Modelos": [f'"{self._kw(p)}"' for p in productos],
            }
        n = self._kw(nombre)
        return {
            "Segmento": [f'"{n} 0km paraguay"', f'"comprar {n} paraguay"', f'"{n} precio paraguay"', f'"{n} en cuotas"'],
            "Modelos": [f'"{self._kw(p)}"' for p in productos],
        }

    # ------------------------------------------------------------------
    # Meta Ads (Facebook / Instagram)
    # ------------------------------------------------------------------

    MAX_TITULO_META = 40        # título del anuncio
    MAX_DESCRIPCION_META = 30   # descripción debajo del título
    MAX_TEXTO_VISIBLE = 125     # lo que se ve antes de «Ver más»

    def _gen_meta_ads(self, persona: dict[str, Any]) -> dict[str, Any]:
        """Anuncio de Meta para una persona: textos, títulos, botón y público sugerido.

        Mismas reglas que Google, el mail y WhatsApp: sale del modelo o la marca y de los
        temas que repiten sus anuncios, sin tasas, plazos, garantías ni urgencias
        inventadas; test drive solo si el stock tiene unidad de prueba; la oferta del mes
        va aparte. Los dolores y motivaciones de la ficha son análisis interno: no se copian.
        """
        c = self._contexto(persona)
        tipo, nombre, marca, corto, usado = c["tipo"], c["nombre"], c["marca"], c["corto"], c["usado"]
        demo = persona.get("demographics", {}) or {}
        td = self._invita_test_drive(c)

        # --- Textos principales ---
        if tipo == "model" and usado:
            encabezado = f"{corto} usados certificados"
            cierre = "Coordiná tu visita y probalo antes de decidir 👇"
            cortos = [f"{corto} usados certificados en Renew. Coordiná tu visita y probalo antes de decidir 👇",
                      "Usados certificados en Renew. Coordiná tu visita y probalo antes de decidir 👇"]
        elif tipo == "model":
            encabezado = nombre
            cierre = "Coordiná tu test drive sin compromiso 👇" if td else "Vení a verlo al salón y pedí tu cotización 👇"
            cortos = [f"{nombre} te espera en el concesionario oficial. " + (
                          "Probalo antes de decidir: coordiná tu test drive 👇" if td else "Vení a verlo y pedí tu cotización 👇"),
                      f"{corto} te espera en el concesionario oficial. Pedí tu cotización 👇"]
        elif usado:
            encabezado = "Usados certificados Renew"
            cierre = "Coordiná tu visita y probalo antes de decidir 👇"
            cortos = ["Usados certificados de varias marcas en Renew. Coordiná tu visita y probalo 👇"]
        elif tipo == "brand":
            encabezado = f"Gama {marca}"
            cierre = "Vení a conocer los modelos al salón 👇"
            cortos = [f"Toda la gama {marca} en el concesionario oficial. Pedí tu cotización y vení a conocerla 👇",
                      "Toda la gama en el concesionario oficial. Pedí tu cotización 👇"]
        else:
            encabezado = f"{nombre} 0km"
            cierre = "Vení a conocerlos al salón 👇"
            cortos = [f"{nombre} 0km de varias marcas en un solo lugar. Compará y pedí tu cotización 👇"]
        textos = ["\n".join([f"🚗 {encabezado}", *[f"✅ {b}" for b in self._beneficios(c)], "", cierre])]
        corto_ok = self._primero_que_entra(cortos, self.MAX_TEXTO_VISIBLE)
        if corto_ok:
            textos.append(corto_ok)
        if "Financiación en cuotas" in c["temas"]:
            textos.append("Planes de financiación y formas de pago a tu medida. "
                          "Escribinos y te pasamos las opciones 👇 Financiación sujeta a aprobación crediticia.")

        # --- Títulos (hasta 5), descripción y botón ---
        por_tema = {**self.GOOGLE_POR_TEMA, **(self.GOOGLE_POR_TEMA_USADO if usado else {})}
        de_temas = [por_tema[t][0] for t in c["temas"] if t in por_tema
                    and not (c["test_drive"] is False and t == "Probar antes de comprar (test drive)")]
        if tipo == "model" and usado:
            candidatos = [[f"{corto} Usados Certificados", f"{corto} Usado"], ["Renew Usados Certificados"],
                          [f"Cotizá tu {corto} Usado", "Pedí tu Cotización"], ["Probalo Antes de Comprar"]]
            descripcion = "Usados certificados Renew"
        elif tipo == "model":
            candidatos = [[nombre, corto], [f"{nombre} en Paraguay", f"{corto} en Paraguay"], [f"Cotizá tu {corto}"],
                          ["Agendá tu Test Drive" if td else "Conocelo en el Salón"],
                          [f"Concesionario Oficial {marca}", "Concesionario Oficial"]]
            descripcion = "Concesionario oficial"
        elif usado:
            candidatos = [["Renew Usados Certificados"], ["Autos Usados Certificados"], ["Probalo Antes de Comprar"]]
            descripcion = "Usados certificados Renew"
        elif tipo == "brand":
            candidatos = [[f"{marca} en Paraguay"], [f"Concesionario Oficial {marca}", "Concesionario Oficial"],
                          [f"Conocé la Gama {marca}", "Conocé Toda la Gama"], ["Pedí tu Cotización"]]
            descripcion = "Concesionario oficial"
        else:
            candidatos = [[f"{nombre} 0km en Paraguay", f"{nombre} 0km"], ["Varias Marcas en un Lugar"], [f"Encontrá tu {nombre}"]]
            descripcion = "Varias marcas, un lugar"
        titulos: list[str] = []
        for ops in candidatos + [[t] for t in de_temas]:
            t = self._primero_que_entra(ops, self.MAX_TITULO_META)
            if t and t.lower() not in {x.lower() for x in titulos}:
                titulos.append(t)
        titulos = titulos[:5]
        canales = str(persona.get("preferred_channels", [])) + str((persona.get("budget") or {}).get("lead_basis", ""))
        boton = "Enviar mensaje de WhatsApp" if re.search(r"whatsapp|conversaci", canales, re.I) else "Obtener cotización"
        tarjetas = [{"headline": p[: self.MAX_TITULO_META], "description": "Pedí tu cotización", "cta": boton}
                    for p in c["productos"]] if len(c["productos"]) >= 2 else []

        campana = (f"Meta - {nombre}" if tipo == "model" else f"Meta - Marca {marca}" if tipo == "brand"
                   else f"Meta - Segmento {nombre}")
        ad = {
            "persona": persona.get("name", ""),
            "tipo": tipo,
            "used": usado,
            "campaign_name": campana,
            "targeting": {
                "age_range": demo.get("age_range", ""),
                "gender": demo.get("gender", ""),
                "locations": demo.get("location", []) or [],
                "temas": [t for t in c["temas"] if t][:5],
            },
            "primary_texts": textos,
            "primary_text": textos[0],
            "headlines": titulos,
            "headline": titulos[0] if titulos else "",
            "description": descripcion,
            "cta": boton,
            "carousel_cards": tarjetas,
            "test_drive": c["test_drive"],
            "test_drive_unidades": c["test_drive_unidades"],
            "stock_disponible": c["stock_disponible"],
            "stock_fecha": c["stock_fecha"],
            "offer": c["oferta"],
            "offer_text": self._oferta_en_texto(c, "meta"),
        }
        for problema in validar_meta_ads(ad):
            logger.warning("Meta Ads %s: %s", ad["persona"], problema)
        return ad

    # ------------------------------------------------------------------
    # Email y WhatsApp: lo común
    # ------------------------------------------------------------------

    MAX_ASUNTO = 60      # asunto de mail: más largo se corta en el celular

    # Tema que repiten los anuncios → beneficio para el mail y WhatsApp. Sin cifras
    # ni promesas: lo concreto (precio, descuento, stock) va en el bloque aparte.
    BENEFICIO_POR_TEMA: dict[str, str] = {
        "Autos eléctricos y ahorro de combustible": "Consumo y autonomía: te pasamos los datos reales de cada versión.",
        "Financiación en cuotas": "Financiación: planes y formas de pago a tu medida.",
        "Garantía y respaldo posventa": "Posventa oficial: service y repuestos originales de la marca.",
        "Familia y espacio": "Espacio y comodidad para viajar en familia.",
        "Probar antes de comprar (test drive)": "Test drive sin compromiso, el día y horario que elijas.",
        "Seguridad y asistencias a la conducción": "Seguridad y asistencias a la conducción, según la versión.",
        "Diseño y estatus": "Un diseño que se nota en cada detalle.",
        "Trabajo, negocio y carga": "Capacidad y respaldo para tu trabajo y tu negocio.",
        "Primer auto / primera SUV": "Asesoramiento en todo el proceso, ideal si es tu primer 0km.",
        "Tecnología y conectividad": "Tecnología y conectividad para el día a día, según la versión.",
    }
    BENEFICIO_POR_TEMA_USADO: dict[str, str] = {
        "Garantía y respaldo posventa": "Usado certificado: revisado y con el respaldo de Renew.",
        "Primer auto / primera SUV": "Asesoramiento en todo el proceso, ideal si es tu primer auto.",
    }

    def _beneficios(self, c: dict[str, Any], n: int = 3) -> list[str]:
        """Hasta n beneficios, de los temas del modelo; sin test drive si no hay unidad."""
        por_tema = {**self.BENEFICIO_POR_TEMA, **(self.BENEFICIO_POR_TEMA_USADO if c["usado"] else {})}
        lista = [por_tema[t] for t in c["temas"] if t in por_tema
                 and not (c["test_drive"] is False and t == "Probar antes de comprar (test drive)")]
        for relleno in ("Asesoramiento personalizado, de la cotización a la entrega.", por_tema["Financiación en cuotas"]):
            if len(lista) < n and relleno not in lista:
                lista.append(relleno)
        return lista[:n]

    @staticmethod
    def _de_que_hablamos(c: dict[str, Any]) -> str:
        """Lo que consultó el cliente, sin artículo: el/la depende del modelo."""
        if c["tipo"] == "model":
            return f"{c['corto']} usados certificados" if c["usado"] else c["nombre"]
        if c["tipo"] == "brand":
            return "los usados certificados de Renew" if c["usado"] else f"la gama {c['marca']}"
        return f"la línea {c['nombre']} 0km"

    @staticmethod
    def _quien_escribe(c: dict[str, Any]) -> str:
        return "Renew" if c["usado"] else (c["marca"] or "Santa Rosa Automotores")

    @staticmethod
    def _invita_test_drive(c: dict[str, Any]) -> bool:
        """Test drive solo en un modelo 0km cuyo stock no diga que no hay unidad de prueba."""
        return c["tipo"] == "model" and not c["usado"] and c["test_drive"] is not False

    def _oferta_en_texto(self, c: dict[str, Any], canal: str) -> str | None:
        """La oferta del mes redactada para el mail o para WhatsApp (se confirma antes de usar)."""
        of = c.get("oferta")
        if not of or of.get("vencida"):
            return None
        pvp, desc = of["pvp_min"], of["descuento_max"]
        cuando = f"En {of['mes']}, " if of["mes"] else ""
        if canal == "meta":
            opciones = ([f"Este mes, {c['nombre']} con hasta {self._usd(desc)} de descuento. Consultá condiciones 👇"] if desc else []) + \
                       ([f"{c['nombre']} desde {self._usd(pvp)} (precio de lista). Pedí tu cotización 👇"] if pvp else [])
            return self._primero_que_entra(opciones, self.MAX_TEXTO_VISIBLE)
        if canal == "whatsapp":
            if desc:
                return (f"Este mes {c['nombre']} tiene hasta {self._usd(desc)} de descuento 🎁 "
                        "(consultá condiciones). ¿Te paso el detalle?")
            return f"{c['nombre']} está desde {self._usd(pvp)} (precio de lista). ¿Te paso las versiones?"
        if pvp and desc:
            return (f"{cuando}{c['nombre']} está desde {self._usd(pvp)} y con hasta {self._usd(desc)} "
                    "de descuento. Consultá condiciones con tu asesor.")
        if desc:
            return f"{cuando}{c['nombre']} tiene hasta {self._usd(desc)} de descuento. Consultá condiciones con tu asesor."
        return f"{c['nombre']} está desde {self._usd(pvp)} (precio de lista{' de ' + of['mes'] if of['mes'] else ''})."

    # ------------------------------------------------------------------
    # Email Marketing
    # ------------------------------------------------------------------

    def _gen_email(self, persona: dict[str, Any]) -> dict[str, Any]:
        """Mail para quien dejó sus datos. Sin promesas fijas ni urgencia inventada.

        Los campos entre llaves ({nombre}, {link}) los completa la herramienta de
        envío. Los beneficios salen de los temas que repiten los anuncios; la
        oferta del mes y el stock van aparte, para confirmar con la marca.
        """
        c = self._contexto(persona)
        que = self._de_que_hablamos(c)
        td = self._invita_test_drive(c)
        if c["tipo"] == "model" and c["usado"]:
            asuntos = [f"{c['corto']} usados certificados: coordiná tu visita",
                       f"{c['corto']} usado: unidades, precio y financiación"]
            preheader = "Coordiná tu visita y probalo antes de decidir."
        elif c["tipo"] == "model":
            asuntos = [f"{c['nombre']}: " + ("coordinemos tu test drive" if td else "conocelo en el salón"),
                       f"{c['nombre']}: versiones, precio y financiación",
                       f"¿Seguís pensando en {c['nombre']}?"]
            preheader = ("Elegí el día y el horario y probalo sin compromiso." if td
                         else "Te mostramos versiones, precio y formas de pago.")
        elif c["usado"]:
            asuntos = ["Usados certificados Renew: encontrá el tuyo", "Renew: usados certificados con financiación"]
            preheader = "Coordiná tu visita y probalo antes de decidir."
        elif c["tipo"] == "brand":
            asuntos = [f"{c['marca']}: encontrá tu próximo 0km", f"{c['marca']}: versiones, precios y financiación"]
            preheader = "Te mostramos cada modelo en persona, sin compromiso."
        else:
            asuntos = [f"{c['nombre']} 0km: varias marcas en un solo lugar", f"Encontrá tu {c['nombre']} 0km"]
            preheader = "Compará versiones y formas de pago con un asesor."
        asuntos = [a for a in asuntos if len(a) <= self.MAX_ASUNTO] or [que[:self.MAX_ASUNTO]]
        if td:
            cierre = "Lo mejor es probarlo: coordiná tu test drive el día y horario que prefieras, sin compromiso."
        elif c["usado"]:
            cierre = "Lo mejor es verlo en persona: coordiná tu visita y probalo antes de decidir."
        else:
            cierre = "Lo mejor es verlo en persona: coordiná tu visita al salón el día y horario que prefieras."
        firma = f"Equipo {self._quien_escribe(c)}"
        cuerpo = "\n".join([
            "Hola {nombre}:",
            "",
            f"Gracias por tu interés en {que}. Esto es lo que más nos consultan:",
            "",
            *[f"• {b}" for b in self._beneficios(c)],
            "",
            cierre,
            "",
            "👉 {link}",
            "",
            "Si preferís, respondé este mail y un asesor te escribe con versiones, precio y formas de pago.",
            "",
            "Saludos,",
            firma,
            "",
            "Financiación sujeta a aprobación crediticia.",
        ])
        seguimiento = "\n".join([
            "Hola {nombre}:",
            "",
            f"¿Pudiste ver lo que te mandamos sobre {que}? "
            + ("Si querés, coordinamos el test drive o te pasamos versiones y precio por este medio." if td
               else "Si querés, coordinamos una visita o te pasamos versiones y precio por este medio."),
            "",
            "👉 {link}",
            "",
            firma,
        ])
        email = {
            "persona": persona.get("name", ""),
            "tipo": c["tipo"],
            "used": c["usado"],
            "subject": asuntos[0],
            "subject_alternatives": asuntos[1:],
            "preheader": preheader,
            "body": cuerpo,
            "follow_up_3_days": seguimiento,
            "test_drive": c["test_drive"],
            "test_drive_unidades": c["test_drive_unidades"],
            "stock_disponible": c["stock_disponible"],
            "stock_fecha": c["stock_fecha"],
            "offer": c["oferta"],
            "offer_text": self._oferta_en_texto(c, "email"),
        }
        for problema in validar_mensajes(email):
            logger.warning("Email %s: %s", email["persona"], problema)
        return email

    # ------------------------------------------------------------------
    # WhatsApp Business
    # ------------------------------------------------------------------

    def _gen_whatsapp(self, persona: dict[str, Any]) -> dict[str, Any]:
        """Mensajes de WhatsApp para asesores y envíos. Sin promesas fijas ni urgencia inventada.

        Bienvenida, seguimiento y respuestas van dentro de las 24 h desde el último
        mensaje del cliente. Fuera de esa ventana WhatsApp solo deja escribir con
        una plantilla aprobada por Meta y a quien aceptó recibir mensajes: esa es
        la invitación. {asesor} y {nombre} se completan al enviar.
        """
        c = self._contexto(persona)
        que = self._de_que_hablamos(c)
        td = self._invita_test_drive(c)
        quien = self._quien_escribe(c)
        if c["usado"]:
            opciones = ["Unidades disponibles", "Precio y formas de pago", "Coordinar una visita para verlo y probarlo"]
        else:
            opciones = ["Versiones y equipamiento", "Precio y formas de pago",
                        "Agendar un test drive" if td else "Coordinar una visita al salón"]
        bienvenida = ("¡Hola! 👋 Soy {asesor}, de " + quien + ". Gracias por escribirnos por " + que + ".\n\n"
                      "¿En qué te ayudo?\n" + "\n".join(f"• {o}" for o in opciones) + "\n\n"
                      "Contame y te respondo por acá 😊")
        if td:
            seguimiento = (f"¡Hola! Te escribo por {que}. ¿Te gustaría coordinar un test drive esta semana? "
                           "Decime el día y el horario y te lo reservo 🚗")
            invito = "coordiná tu test drive sin compromiso"
        elif c["usado"]:
            seguimiento = (f"¡Hola! Te escribo por {que}. ¿Te gustaría venir a ver las unidades esta semana? "
                           "Decime el día y el horario y te espero 🚗")
            invito = "coordiná tu visita y probalo antes de decidir"
        elif c["tipo"] == "model":
            seguimiento = (f"¡Hola! Te escribo por {que}. ¿Te gustaría verlo en persona esta semana? "
                           "Decime el día y el horario y te espero en el salón 🚗")
            invito = "coordiná tu visita cuando te quede bien"
        else:
            seguimiento = (f"¡Hola! Te escribo por {que}. ¿Te gustaría conocer los modelos en persona esta semana? "
                           "Decime el día y el horario y te espero en el salón 🚗")
            invito = "coordiná tu visita cuando te quede bien"
        invitacion = ("Hola {nombre} 👋 Te invitamos a conocer " + que + " en persona: " + invito
                      + ". ¿Te reservo un turno?\n\nSi no querés recibir más mensajes, respondé BAJA.")

        if c["usado"]:
            precio = ("El precio depende del año, el kilometraje y la versión. ¿Qué estás buscando? "
                      "Te paso las unidades disponibles con su precio 👍")
            prueba = "¡Genial! 🎉 Decime día, horario y sucursal, y te espero para que veas la unidad y la pruebes."
        else:
            precio = ("El precio depende de la versión y de la forma de pago. ¿Qué versión te interesa? "
                      "Te paso el precio de lista vigente y las opciones de financiación 👍")
            if td:
                prueba = (f"¡Genial! 🎉 Para reservar tu test drive de {c['nombre']} decime:\n"
                          "• día y horario que te quedan bien\n• sucursal o ciudad\nTe confirmo el turno por acá.")
            elif c["tipo"] == "model":
                prueba = (f"¡Gracias! 🙌 Hoy no tenemos unidad de prueba de {c['nombre']}, pero podés verlo en el salón. "
                          "Decime día, horario y sucursal, y te espero.")
            else:
                prueba = ("¡Genial! 🎉 Decime qué modelo te interesa, el día y la sucursal, "
                          "y te confirmo si hay unidad de prueba.")
        respuestas = {
            "precio": precio,
            "test_drive": prueba,
            "financiacion": ("Te calculamos la cuota según la versión y la forma de pago que prefieras. Para la "
                             "aprobación te vamos a pedir la documentación habitual (cédula y comprobante de "
                             "ingresos). ¿Querés que te llamemos? Financiación sujeta a aprobación crediticia."),
            "usado": ("Sí, podemos evaluar tu usado como parte de pago. Pasame marca, modelo, año y kilometraje, "
                      "y te damos una cotización 👍"),
        }
        wa = {
            "persona": persona.get("name", ""),
            "segment": (persona.get("segment") or {}).get("name", ""),
            "tipo": c["tipo"],
            "used": c["usado"],
            "templates": {"welcome": bienvenida, "follow_up": seguimiento, "promo": invitacion},
            "auto_replies": respuestas,
            "test_drive": c["test_drive"],
            "test_drive_unidades": c["test_drive_unidades"],
            "stock_disponible": c["stock_disponible"],
            "stock_fecha": c["stock_fecha"],
            "offer": c["oferta"],
            "offer_text": self._oferta_en_texto(c, "whatsapp"),
        }
        for problema in validar_mensajes(wa):
            logger.warning("WhatsApp %s: %s", wa["persona"], problema)
        return wa


def validar_google_ads(ad: dict[str, Any]) -> list[str]:
    """Lo que haría que Google rechace el borrador o que promete sin respaldo."""
    g = MarketingContentGenerator
    titulos, descs = ad.get("headlines", []), ad.get("descriptions", [])
    problemas = []
    if not 3 <= len(titulos) <= 15:
        problemas.append(f"{len(titulos)} títulos (Google pide de 3 a 15)")
    if not 2 <= len(descs) <= 4:
        problemas.append(f"{len(descs)} descripciones (Google pide de 2 a 4)")
    if len({t.lower() for t in titulos}) < len(titulos):
        problemas.append("títulos repetidos")
    problemas += [f"título de {len(t)} caracteres: {t}" for t in titulos if len(t) > g.MAX_TITULO]
    problemas += [f"título con signo de exclamación: {t}" for t in titulos if "!" in t]
    problemas += [f"descripción de {len(d)} caracteres: {d}" for d in descs if len(d) > g.MAX_DESCRIPCION]
    problemas += [f"tramo de URL de {len(r)} caracteres: {r}" for r in ad.get("paths", []) if len(r) > g.MAX_RUTA]
    for s in ad.get("sitelinks", []):
        if len(s["text"]) > g.MAX_SITELINK or max(len(s["desc1"]), len(s["desc2"])) > g.MAX_SITELINK_LINEA:
            problemas.append(f"sitelink fuera de límite: {s['text']}")
    problemas += [f"texto destacado de {len(c)} caracteres: {c}" for c in ad.get("callouts", []) if len(c) > g.MAX_DESTACADO]
    of = ad.get("offer") or {}
    problemas += [f"título de oferta de {len(t)} caracteres: {t}" for t in of.get("titulos", []) if len(t) > g.MAX_TITULO]
    if of.get("descripcion") and len(of["descripcion"]) > g.MAX_DESCRIPCION:
        problemas.append(f"descripción de oferta de {len(of['descripcion'])} caracteres")
    fijos = titulos + descs + ad.get("callouts", []) + [x for s in ad.get("sitelinks", []) for x in s.values()]
    problemas += [f"promesa sin respaldo: {x}" for x in fijos if PROMESAS_SIN_RESPALDO.search(x)]
    if ad.get("test_drive") is False and any("test drive" in x.lower() for x in fijos):
        problemas.append("invita a test drive y el stock no tiene unidad de prueba")
    return problemas


def validar_mensajes(msj: dict[str, Any]) -> list[str]:
    """Lo que el mail o WhatsApp promete sin respaldo. La oferta del mes va aparte y no cuenta."""
    asuntos = [msj.get("subject", ""), *msj.get("subject_alternatives", [])]
    textos = [t for t in [*asuntos, msj.get("preheader", ""), msj.get("body", ""), msj.get("follow_up_3_days", ""),
                          *(msj.get("templates") or {}).values(), *(msj.get("auto_replies") or {}).values()] if t]
    problemas = []
    for patron, que in ((PROMESAS_SIN_RESPALDO, "promesa sin respaldo"),
                        (URGENCIA_SIN_RESPALDO, "urgencia sin respaldo"),
                        (RESTOS_DE_PLANTILLA, "resto de la plantilla vieja")):
        for t in textos:
            m = patron.search(t)
            if m:
                problemas.append(f"{que}: «{m.group(0)}»")
    problemas += [f"asunto de {len(a)} caracteres: {a}" for a in asuntos
                  if len(a) > MarketingContentGenerator.MAX_ASUNTO]
    if msj.get("test_drive") is False and any("test drive" in t.lower() for t in textos):
        problemas.append("invita a test drive y el stock no tiene unidad de prueba")
    return problemas


def validar_meta_ads(ad: dict[str, Any]) -> list[str]:
    """Lo que el aviso de Meta promete sin respaldo o lo que Meta corta. La oferta del mes no cuenta."""
    g = MarketingContentGenerator
    textos = ad.get("primary_texts", [])
    titulos = ad.get("headlines", [])
    problemas = []
    if not textos or not titulos:
        problemas.append("falta texto principal o título")
    problemas += [f"título de {len(t)} caracteres: {t}" for t in titulos if len(t) > g.MAX_TITULO_META]
    if len(ad.get("description", "")) > g.MAX_DESCRIPCION_META:
        problemas.append(f"descripción de {len(ad['description'])} caracteres")
    if len(textos) > 1 and len(textos[1]) > g.MAX_TEXTO_VISIBLE:
        problemas.append(f"texto corto de {len(textos[1])} caracteres")
    fijos = textos + titulos + [ad.get("description", "")] + [x for t in ad.get("carousel_cards", []) for x in t.values()]
    for patron, que in ((PROMESAS_SIN_RESPALDO, "promesa sin respaldo"), (URGENCIA_SIN_RESPALDO, "urgencia sin respaldo"),
                        (RESTOS_DE_PLANTILLA, "resto de la plantilla vieja")):
        for t in fijos:
            m = patron.search(t or "")
            if m:
                problemas.append(f"{que}: «{m.group(0)}»")
    if ad.get("test_drive") is False and any("test drive" in (t or "").lower() for t in fijos):
        problemas.append("invita a test drive y el stock no tiene unidad de prueba")
    return problemas
