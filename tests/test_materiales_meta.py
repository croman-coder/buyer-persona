"""Materiales de Meta: clasificación de cada anuncio, cuentas por formato/ubicación y notas.

Todos los datos son inventados. Corre con pytest o directo: venv/bin/python3 tests/test_materiales_meta.py
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.connectors.meta_materiales import fila_mes, formato_de, medios_de, origen_de, rango  # noqa: E402
from src.generators.materiales_meta import (  # noqa: E402
    analizar, destino_de, incorporar_historial, nota_hub, nota_marca, resumen_moc, tramo_de, ubicacion_de, vertical_de)

HOY = date(2026, 10, 5)


def test_rango_de_meses():
    assert rango(6, HOY) == ("2026-05-01", "2026-10-05")
    assert rango(12, date(2026, 3, 9)) == ("2025-04-01", "2026-03-09")


def test_formato_de_cada_creativo():
    assert formato_de({"asset_feed_spec": {"images": [{"hash": "a"}, {"hash": "b"}], "ad_formats": ["SINGLE_IMAGE"]}}) == "Imagen"
    assert formato_de({"asset_feed_spec": {"videos": [{"video_id": "1"}], "ad_formats": ["SINGLE_VIDEO"]}}) == "Video"
    assert formato_de({"asset_feed_spec": {"images": [{"hash": "a"}] * 6, "ad_formats": ["CAROUSEL"]}}) == "Carrusel"
    assert formato_de({"asset_feed_spec": {"images": [{"hash": "a"}], "videos": [{"video_id": "1"}],
                                           "ad_formats": ["AUTOMATIC_FORMAT"]}}) == "Mixto"
    assert formato_de({"object_story_spec": {"link_data": {"child_attachments": [{}, {}, {}]}}}) == "Carrusel"
    assert formato_de({"object_story_spec": {"video_data": {"video_id": "9"}}, "object_type": "VIDEO"}) == "Video"
    assert formato_de({"object_story_spec": {"link_data": {"image_hash": "x"}}, "object_type": "SHARE"}) == "Imagen"
    assert formato_de({"object_type": "VIDEO", "source_instagram_media_id": "17"}) == "Video"
    assert formato_de({}) == "Sin dato"


def test_origen_y_medios():
    assert origen_de({"asset_feed_spec": {"images": []}}) == "anuncio"
    assert origen_de({"source_instagram_media_id": "17"}) == "publicacion_instagram"
    assert origen_de({"object_story_id": "1_2"}) == "publicacion_facebook"
    # En un video, la imagen del creativo es la miniatura: no cuenta como pieza
    videos, imagenes = medios_de({"video_id": "9", "image_hash": "mini",
                                  "object_story_spec": {"video_data": {"video_id": "9", "image_hash": "mini"}}})
    assert videos == ["9"] and imagenes == []
    videos, imagenes = medios_de({"asset_feed_spec": {"images": [{"hash": "a"}, {"hash": "b"}, {"hash": "a"}]}})
    assert videos == [] and imagenes == ["a", "b"]


def test_destino_ubicacion_duracion_vertical():
    assert destino_de({"optimizacion": "QUALITY_LEAD"}) == "formulario"
    assert destino_de({"optimizacion": "CONVERSATIONS"}) == "chat"
    assert destino_de({"optimizacion": "REACH", "formularios": 0, "chats": 3}) == "chat"
    assert destino_de({"optimizacion": "REACH"}) == "otro"
    assert ubicacion_de("instagram", "instagram_reels") == "Reels"
    assert ubicacion_de("facebook", "facebook_stories") == "Stories"
    assert ubicacion_de("audience_network", "an_classic") == "Audience Network (otras apps)"
    assert ubicacion_de("facebook", "algo_nuevo") == "Otras"
    assert [tramo_de(x) for x in (9.5, 15, 22, 45, 90, None)] == [
        "Hasta 15 s", "Hasta 15 s", "16 a 30 s", "31 a 60 s", "Más de 60 s", "Sin dato"]
    assert vertical_de({"videos": [{"ancho": 1080, "alto": 1920}, {"ancho": 1080, "alto": 1080}]}) == "Con versión vertical"
    assert vertical_de({"imagenes": [{"ancho": 1080, "alto": 1350}]}) == "Sin versión vertical"
    assert vertical_de({"imagenes": [{"hash": "a"}]}) == "Sin dato"


def _fila(ad, mes, gasto, impresiones, clics, formularios=0, chats=0, opt="QUALITY_LEAD", v3=0, v100=0):
    return fila_mes({"ad_id": ad, "date_start": f"{mes}-01", "optimization_goal": opt, "spend": str(gasto),
                     "impressions": str(impresiones), "inline_link_clicks": str(clics),
                     "actions": [{"action_type": "lead", "value": str(formularios)},
                                 {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": str(chats)},
                                 {"action_type": "video_view", "value": str(v3)}],
                     "video_p100_watched_actions": [{"action_type": "video_view", "value": str(v100)}]})


def _materiales():
    """3 imágenes a USD 3 el lead, 3 videos cortos verticales a USD 2, 3 videos largos horizontales a USD 4,
    1 carrusel con poca muestra y 3 imágenes de WhatsApp a USD 2 la conversación."""
    def ad(nombre, formato, origen="anuncio", videos=(), imagenes=()):
        return {"nombre": nombre, "marca": "GWM", "formato": formato, "origen": origen,
                "videos": list(videos), "imagenes": list(imagenes)}
    anuncios = {}
    for i in (1, 2, 3):
        anuncios[f"img{i}"] = ad(f"Flyer H6 {i}", "Imagen", imagenes=[{"hash": f"a{i}", "ancho": 1080, "alto": 1080}])
        anuncios[f"vid{i}"] = ad(f"Reel H6 | {i}", "Video", videos=[{"id": f"v{i}", "seg": 14.0, "ancho": 1080, "alto": 1920}])
        anuncios[f"lar{i}"] = ad(f"Video largo H9 {i}", "Video", videos=[{"id": f"l{i}", "seg": 75.0, "ancho": 1920, "alto": 1080}])
        anuncios[f"wa{i}"] = ad(f"WhatsApp Jolion {i}", "Imagen", origen="publicacion_instagram")
    anuncios["car1"] = ad("Carrusel gama", "Carrusel")
    por_mes = []
    for mes in ("2026-07", "2026-08", "2026-09"):
        for i in (1, 2, 3):
            por_mes += [_fila(f"img{i}", mes, 90, 30000, 300, formularios=30),
                        _fila(f"vid{i}", mes, 60, 30000, 450, formularios=30, v3=15000, v100=3000),
                        _fila(f"lar{i}", mes, 40, 20000, 100, formularios=10, v3=4000, v100=200),
                        _fila(f"wa{i}", mes, 100, 40000, 800, chats=50, opt="CONVERSATIONS")]
        por_mes.append(_fila("car1", mes, 20, 9000, 90, formularios=5))
    por_mes.append(_fila("img1", "2026-10", 9, 3000, 30, formularios=3))
    por_ubicacion = [
        {"ad_id": "img1", "plataforma": "facebook", "posicion": "feed", "gasto": 600, "impresiones": 200000, "clics": 2000,
         "formularios": 200, "chats": 0},
        {"ad_id": "img1", "plataforma": "instagram", "posicion": "instagram_reels", "gasto": 310, "impresiones": 103000,
         "clics": 1030, "formularios": 103, "chats": 0},
        {"ad_id": "vid1", "plataforma": "instagram", "posicion": "instagram_reels", "gasto": 600, "impresiones": 240000,
         "clics": 3600, "formularios": 300, "chats": 0},
        {"ad_id": "vid1", "plataforma": "facebook", "posicion": "marketplace", "gasto": 100, "impresiones": 50000,
         "clics": 500, "formularios": 100, "chats": 0},
    ]
    return {"desde": "2026-07-01", "hasta": "2026-10-05", "meses": 4, "cuentas": {"act_1": {"marca": "GWM"}},
            "anuncios": anuncios, "por_mes": [{**f, "cuenta": "act_1"} for f in por_mes], "por_ubicacion": por_ubicacion}


def test_analisis_por_formato():
    r = analizar(_materiales(), {"vid1": {"leads": 200, "ventas": 6}, "img1": {"leads": 100, "ventas": 1}}, hoy=HOY)
    gwm = r["marcas"]["GWM"]
    form = {f["clave"]: f for f in gwm["destinos"]["formulario"]["formatos"]}
    assert form["Imagen"]["costo"] == 3.0 and form["Imagen"]["resultados"] == 273
    assert form["Video"]["costo"] == 2.5 and form["Video"]["anuncios"] == 6
    assert not form["Carrusel"]["suficiente"]                 # 1 anuncio y 15 leads: poca muestra
    assert form["Video"]["ventas"] == 6 and form["Video"]["ventas_cada_100"] == 3.0
    assert gwm["destinos"]["chat"]["formatos"][0]["costo"] == 2.0
    tramos = {f["clave"]: f for f in gwm["destinos"]["formulario"]["tramos"]}
    assert tramos["Hasta 15 s"]["costo"] == 2.0 and tramos["Más de 60 s"]["costo"] == 4.0
    assert tramos["Hasta 15 s"]["mira_3s"] == 50.0 and tramos["Hasta 15 s"]["completo"] == 20.0
    ubic = {f["clave"]: f for f in gwm["destinos"]["formulario"]["ubicaciones"]}
    assert ubic["Reels"]["costo"] == round(910 / 403, 2) and ubic["Feed"]["costo"] == 3.0
    texto = " ".join(gwm["conclusiones"])
    assert ("**El video** trae el lead más barato: 17 % menos que la imagen (gráfica) en campañas comparables "
            "(marca · calidad: USD 2,50 contra USD 3,00; base: 633 leads).") in texto
    assert "**Los videos de hasta 15 s** traen el lead más barato: 50 % menos que los videos de más de 60 s" in texto
    assert "Se repite: ganó en 3 de 3 meses." in texto        # octubre va incompleto: no cuenta
    assert "**Los videos con versión vertical (9:16)** traen el lead más barato" in texto
    assert "sale en **Reels**" in texto and "Marketplace" not in texto     # solo Feed, Reels y Stories
    assert "**WhatsApp y mensajes — formato:** todo fue imagen (gráfica); no hay otro formato para comparar." in texto
    assert "Carrusel" not in gwm["conclusiones"][0]          # poca muestra: no entra en la comparación
    assert "**video de hasta 15 s con versión vertical (9:16)**" in gwm["recomendacion"]
    mejores = gwm["destinos"]["formulario"]["mejores"]
    assert {f["ad_id"] for f in mejores} == {"vid1", "vid2", "vid3"}   # solo los más baratos que el promedio


def test_notas():
    r = analizar(_materiales(), {"vid1": {"leads": 200, "ventas": 6}}, hoy=HOY)
    texto = nota_marca("GWM", r["marcas"]["GWM"], r, HOY)
    for seccion in ("¿Imagen, video o carrusel?", "¿Reels, Stories o Feed?", "Videos: ¿cortos o largos?", "Mes a mes",
                    "Los anuncios que mejor rindieron", "WhatsApp y mensajes", "_(poca muestra)_", "oct (al 5)"):
        assert seccion in texto, seccion
    assert "Reel H6 / 1" in texto and "Reel H6 | 1" not in texto   # «|» rompe la tabla
    moc = "\n".join(resumen_moc("GWM", r["marcas"]["GWM"]))
    assert "[[🎬 Materiales que funcionan — GWM]]" in moc
    hub = nota_hub(r, {"GWM"}, HOY)
    assert "[[🎬 Materiales que funcionan — GWM|GWM]]" in hub and "| Video −17 % |" in hub


def test_diferencia_de_un_solo_mes_no_es_regla():
    """El video gana en el total por un mes muy bueno, pero pierde los otros dos: no se recomienda."""
    mat = _materiales()
    for f in mat["por_mes"]:
        if f["ad_id"].startswith(("vid", "lar")) and f["mes"] != "2026-07":
            f["formularios"] = f["formularios"] * 0.7          # agosto y septiembre, más caros que la imagen
        if f["ad_id"].startswith(("vid", "lar")) and f["mes"] == "2026-07":
            f["formularios"] = f["formularios"] * 3            # julio, muchísimo más barato
    r = analizar(mat, hoy=HOY)
    gwm = r["marcas"]["GWM"]
    formato = next(c for c in gwm["conclusiones"] if "— formato:" in c)
    assert "**El video** trae el lead más barato" in formato and "Pero ganó solo en 1 de 3 meses" in formato
    assert "no se separan de forma clara y sostenida" in gwm["recomendacion"]


def test_no_mezcla_cuentas_de_asesores_con_la_de_la_marca():
    """Los asesores sacan leads más baratos: la imagen de asesor no le «gana» al video de la marca por eso."""
    mat = _materiales()
    mat["cuentas"]["act_2"] = {"marca": "GWM", "nombre": "CARMEN FRANCO | GWM CDE"}
    for f in mat["por_mes"]:
        if f["ad_id"].startswith("img"):
            f["cuenta"] = "act_2"                      # todas las imágenes, en una cuenta de asesor
            f["gasto"] = f["gasto"] / 3                # leads a USD 1: más baratos que cualquier video de la marca
    r = analizar(mat, hoy=HOY)
    comp = r["marcas"]["GWM"]["destinos"]["formulario"]["comparaciones"]["formato"]
    assert comp["estado"] == "sin_comparables"
    assert "no se pueden comparar" in r["marcas"]["GWM"]["conclusiones"][0]
    ctx = r["marcas"]["GWM"]["destinos"]["formulario"]["formatos_ctx"]
    assert set(ctx["Imagen"]) == {"asesor|calidad"} and set(ctx["Video"]) == {"marca|calidad"}


def test_sin_muestra_no_inventa():
    mat = _materiales()
    mat["por_mes"] = [f for f in mat["por_mes"] if f["ad_id"] == "car1"]
    r = analizar(mat, hoy=HOY)
    assert r["marcas"]["GWM"]["conclusiones"][0].startswith("Todavía no hay muestra suficiente")
    assert r["marcas"]["GWM"]["recomendacion"] is None


def test_historial_no_pierde_los_meses_viejos(tmp_path=None):
    import json
    import tempfile
    from pathlib import Path
    carpeta = Path(tmp_path or tempfile.mkdtemp())
    ruta = carpeta / "Memoria" / "materiales_por_mes.jsonl"
    r = analizar(_materiales(), hoy=HOY)
    incorporar_historial(r, ruta)
    guardados = [json.loads(x) for x in ruta.read_text().splitlines()]
    assert {x["mes"] for x in guardados} == {"2026-07", "2026-08", "2026-09", "2026-10"}
    # Un mes después la ventana ya no trae julio: vuelve del historial y sale en la tabla
    mat = _materiales()
    mat["por_mes"] = [f for f in mat["por_mes"] if f["mes"] != "2026-07"]
    r2 = analizar(mat, hoy=HOY)
    assert "2026-07" not in r2["marcas"]["GWM"]["destinos"]["formulario"]["meses"]
    assert incorporar_historial(r2, ruta) == 1
    julio = r2["marcas"]["GWM"]["destinos"]["formulario"]["meses"]["2026-07"]
    assert julio["Imagen"]["costo"] == 3.0 and julio["Video"]["resultados"] == 120
    assert "| jul |" in nota_marca("GWM", r2["marcas"]["GWM"], r2, HOY)


def test_exporta_nota_por_marca_y_resumen_en_el_indice():
    import tempfile
    from pathlib import Path
    from src.exporters.obsidian_exporter import ObsidianExporter
    base = Path(tempfile.mkdtemp())
    (base / "vault").mkdir()
    ex = ObsidianExporter({"output_dir": str(base / "out"), "obsidian_vault": str(base / "vault")})
    ex.materiales = analizar(_materiales(), hoy=HOY)
    personas = [{"name": "Comprador GWM", "segment": {"type": "brand", "name": "GWM"}},
                {"name": "Comprador JAC", "segment": {"type": "brand", "name": "JAC"}}]
    # Una nota vieja de una marca que ya no tiene datos se borra
    (base / "vault" / "Buyer Personas" / "Zeekr").mkdir(parents=True)
    (base / "vault" / "Buyer Personas" / "Zeekr" / "🎬 Materiales que funcionan — Zeekr.md").write_text("vieja")
    archivos = ex.export_materiales(personas)
    assert [a.name for a in archivos] == ["🎬 Materiales que funcionan — GWM.md"]
    assert (base / "vault" / "Buyer Personas" / "GWM" / "🎬 Materiales que funcionan — GWM.md").exists()
    assert not (base / "vault" / "Buyer Personas" / "Zeekr" / "🎬 Materiales que funcionan — Zeekr.md").exists()
    assert (base / "vault" / "Sistema" / "🎬 Materiales Meta — todas las marcas.md").exists()
    indice = ex._create_brand_index("GWM", personas).read_text()
    assert "## 🎬 Materiales que mejor funcionan" in indice and "[[🎬 Materiales que funcionan — GWM]]" in indice
    ficha = ex._render_strategy({"segment": {"type": "model", "brand": "GWM", "name": "GWM Haval H6"},
                                 "creative_format": {"top_format": "Reels/Stories", "top_format_share": 49.1}})
    assert "**video de hasta 15 s con versión vertical (9:16)**" in ficha and "concentra el 49.1%" not in ficha


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
