"""Lectura de la Biblioteca de Anuncios de la competencia: clasificación, filtros de privacidad y memoria. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_biblioteca_competencia.py
"""
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.generators import biblioteca_competencia as B  # noqa: E402

HOY = date(2026, 10, 12)


def fila(id_, desde, pagina, cuerpo):
    return [id_, desde, pagina, cuerpo]


def test_fecha_de():
    assert B.fecha_de("7 oct 2026") == date(2026, 10, 7)
    assert B.fecha_de("12 nov 2025") == date(2025, 11, 12)
    assert B.fecha_de("3 sept 2026") == date(2026, 9, 3)
    assert B.fecha_de("") is None and B.fecha_de("ayer") is None


def test_quita_el_ruido_y_encuentra_formato_y_boton():
    a = B.analizar_anuncio(fila("1", "8 oct 2026", "Marca X",
                                "Nuevo Modelo Z llega con motor diésel. / 0:00 / 0:17 / MARCAX.COM.PY/Z / Nuevo Z / Ver más / Activo"), HOY)
    assert a["texto"] == "Nuevo Modelo Z llega con motor diésel. / Nuevo Z"
    assert a["formato"] == "video" and a["cta"] == "Ver más" and a["dias"] == 4
    b = B.analizar_anuncio(fila("2", "8 oct 2026", "Marca X", "Un auto. / Enviar mensaje de WhatsApp / Activo"), HOY)
    assert b["formato"] == "imagen o carrusel" and b["cta"] == "WhatsApp"


def test_tema_oferta_novedad_postventa_y_marca():
    t = lambda cuerpo: B.analizar_anuncio(fila("1", "1 oct 2026", "P", cuerpo), HOY)["tema"]
    assert t("Llevalo con entrega inicial desde el 15% y hasta 60 meses sin intereses.") == "oferta"
    assert t("La SUV que querés, desde Gs. 1.200.000 por mes.") == "oferta"
    assert t("Durante todo octubre, bonos especiales en precio contado.") == "oferta"
    assert t("Nuevo Tiguan. Totalmente renovado.") == "lanzamiento"
    assert t("Con nuestro Service en Casa mantenemos tu auto como nuevo sin que tengas que moverte.") == "postventa"   # «como nuevo» no es lanzamiento
    assert t("Hace 65 años acompañamos al campo paraguayo.") == "institucional"
    assert t("Abrimos las puertas de nuestra nueva sucursal. Showroom y servicio técnico.") == "institucional"
    assert t("Compacto y listo para todo.") == "producto"


def test_leer_capturas_solo_paginas_oficiales_y_cuenta_asesores():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        (carpeta / "toyotoshi.json").write_text(json.dumps({
            "competidor": "toyotoshi", "consulta": "x", "total_consulta": "~9 resultados", "cargados": 9, "asesores": 3,
            "ads": [fila("1", "2 oct 2026", "Toyotoshi S.A.", "Hola"),
                    fila("2", "2 oct 2026", "Usados Toyotoshi S.A", "Hola 2"),
                    fila("3", "2 oct 2026", B.ASESOR, "Oferta de un asesor"),
                    fila("4", "2 oct 2026", "Ana Pérez - Grupo toyotoshi", "Página personal sin anotar"),
                    fila("5", "2 oct 2026", "En circulación desde el 1 oct 2026", "Fila rota")]}), encoding="utf-8")
        out = B.leer_capturas(carpeta, HOY)
    d = out["toyotoshi"]
    assert [a["id"] for a in d["ads"]] == ["1", "2"]            # la página personal y la fila rota no entran
    assert d["asesores"] == 3
    assert "nipon" not in out                                    # sin captura no hay competidor


def test_paginas_oficiales_de_chevrolet_mazda_y_byd():
    por_slug = {c["slug"]: c for c in B.COMPETIDORES}
    assert B.es_oficial("Chevrolet - TEMA", por_slug["chevrolet"]) and B.es_oficial("Chevrolet", por_slug["chevrolet"])
    assert not B.es_oficial("Foy Chevrolet GMC", por_slug["chevrolet"])            # concesionarios de otros países
    assert B.es_oficial("Mazda Paraguay", por_slug["mazda"]) and not B.es_oficial("Mazda Motors - Walter", por_slug["mazda"])
    assert not B.es_oficial("BYD Gambatto", por_slug["byd"])                         # concesionario de Brasil, no es competencia local
    assert not any(B.es_oficial("BYD Paraguay", c) for c in B.COMPETIDORES if c["slug"] != "byd")   # una página en un solo competidor
    assert por_slug["byd"]["compite_con"] == ["Zeekr", "Leapmotor", "JMEV"]
    assert "tasa 0%" in B.analizar_anuncio(fila("1", "13 jul 2026", "Chevrolet", "Nueva Captiva. Tasa 0% hasta 18 meses."), HOY)["texto"].lower()
    assert B.analizar_anuncio(fila("1", "13 jul 2026", "Chevrolet", "Nueva Captiva. Tasa 0% hasta 18 meses."), HOY)["tema"] == "oferta"


def test_frase_de_la_oferta_y_anuncios_repetidos():
    a = B.analizar_anuncio(fila("1", "7 oct 2026", "Nipon Automotores S.A.",
                                "Tu próxima gran decisión tiene nombre. / Durante todo octubre, accedé a bonos especiales en precio contado 😉 / WHATSAPP / Enviar mensaje de WhatsApp"), HOY)
    assert B.frase_oferta(a) == "Durante todo octubre, accedé a bonos especiales en precio contado 😉"
    g = B.analizar_anuncio(fila("2", "7 oct 2026", "Geely Paraguay", "La SUV que querés, desde Gs. 1.200.000 por mes. / Conocé la GX3."), HOY)
    assert B.frase_oferta(g) == "La SUV que querés, desde Gs. 1.200.000 por mes."      # no corta en «Gs.»
    b = dict(a, id="3")
    assert [(x["id"], k) for x, k in B.agrupar_iguales([a, b, g])] == [("1", 2), ("2", 1)]


def test_resumen_y_comparacion():
    ads = [B.analizar_anuncio(fila(str(i), d, "P", "Texto. / 0:00 / 0:10 / Ver más"), HOY)
           for i, d in enumerate(["10 oct 2026", "1 sep 2026", "1 ago 2026"])]
    r = B.resumen(ads)
    assert r["n"] == 3 and r["video"] == 3 and r["nuevos_7d"] == 1 and r["sostenidos_30d"] == 2 and r["ctas"] == {"Ver más": 3}
    assert B.comparar(["a", "b"], ["b", "c"]) == {"nuevos": ["c"], "terminados": ["a"]}


def test_memoria_reemplaza_la_lectura_del_mismo_dia():
    leidos = {"nipon": {"ads": [B.analizar_anuncio(fila("1", "7 oct 2026", "Nipon Automotores S.A.", "Hola"), HOY)], "asesores": 0}}
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "m" / "b.jsonl"
        B.guardar_lectura(ruta, "2026-10-05", leidos)
        B.guardar_lectura(ruta, "2026-10-12", leidos)
        B.guardar_lectura(ruta, "2026-10-12", leidos)          # vuelve a leer el mismo día
        h = B.cargar_historial(ruta)
    assert [f["fecha"] for f in h] == ["2026-10-05", "2026-10-12"]
    assert B.lectura_anterior(h, "nipon", "2026-10-12")["fecha"] == "2026-10-05"
    assert B.lectura_anterior(h, "nipon", "2026-10-05") is None
    assert h[1]["ids"] == ["1"] and h[1]["anuncios"][0]["tema"] == "producto"


def test_que_responder_se_apoya_en_datos_propios_solo_si_son_firmes():
    comp = {"compite_con": ["Mitsubishi", "Renault"], "directo": True}
    ads = [B.analizar_anuncio(fila("1", "7 oct 2026", "P", "Entrega inicial desde el 15% y hasta 60 meses sin intereses. Agendá tu test drive."), HOY)]
    marcas = {"Mitsubishi": {"marca": {"nse": {"senales": ["54% pide financiación en el formulario (32 respuestas)"]}}},
              "Renault": {"marca": {"nse": {"senales": ["100% pide financiación en el formulario (4 respuestas)"]}}}}   # pocas respuestas: no cuenta
    pistas = B.que_responder(comp, B.resumen(ads), marcas)
    texto = " ".join(pistas)
    assert "Mitsubishi 54 % (32 respuestas)" in texto and "Renault 100" not in texto
    assert "sin tasas ni plazos inventados" in texto and "test drive" in texto
    assert "agencia" in texto                                    # el competidor directo recuerda coordinar con la agencia
    assert B.que_responder(comp, B.resumen([]), marcas) == []
    for prohibido in ("mejor que", "más barato que"):
        assert prohibido not in texto                            # nunca se compara nombrando al rival


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
