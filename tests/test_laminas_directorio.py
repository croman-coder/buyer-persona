"""Láminas de directorio: titular, edades, ciudades y señales del NSE. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_laminas_directorio.py
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
_spec = importlib.util.spec_from_file_location("laminas_directorio", os.path.join(ROOT, "scripts", "laminas_directorio.py"))
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)


def test_rango_de_edad():
    assert D.rango_edad({"25-34": 29, "35-44": 30, "45-54": 20}) == "de 25 a 44 años"
    assert D.rango_edad({"55-64": 20, "65+": 30, "35-44": 10}) == "de 55 años o más"
    assert D.rango_edad({"65+": 24, "35-44": 23}) == "de todas las edades"       # ninguna edad llega al 25 %
    assert D.rango_edad({"35-44": 40, "65+": 30}) == "de 35 a 44 años"


def test_ciudades_juntan_acentos():
    assert D.ciudades({"city": {"Asunción": 646, "Asuncion": 76, "Luque": 127, "Ciudad del Este": 248}}) == [
        ("Asunción", 722), ("Ciudad del Este", 248), ("Luque", 127)]


def test_senales_nse():
    nse = {"senales": ["74% pide financiación en el formulario (436 respuestas)",
                       "31.0% de los clics desde iPhone (promedio del portfolio ~21%)", "zona: Asunción"]}
    assert D.senales_nse(nse, 29476.7) == ["ticket facturado <b>USD 29.477</b>", "74 % pide financiación (436 respuestas)",
                                           "31 % de los clics desde iPhone (promedio 21 %)"]
    # con una sola respuesta el % de financiación no dice nada
    assert D.senales_nse({"senales": ["100% pide financiación en el formulario (1 respuestas)"]}, None) == []


def test_titular():
    mp = {"demographics": {"gender": "Masculino", "meta": {"age_distribution": {"25-34": 29, "35-44": 30}}},
          "nse": {"nivel": "C (medio)"}, "observed_interests": {"temas": [{"tema": "Garantía y respaldo posventa", "pct": 42}]}}
    negro, naranja = D.titular("JAC", mp, {"empresa": {"empresa_pct": 46.6}, "embudo": {"lectura": "parejo"}})
    assert negro == "Quién compra JAC: hombre de 25 a 44 años, NSE C (medio);"
    assert naranja == "el 47 % compra a nombre de una empresa y lo que más mira es garantía y posventa."
    assert D.titular("GWM", mp, {"embudo": {"lectura": "ella_mira"}, "empresa": {"empresa_pct": 35}})[1] == \
        "ella investiga y él da el paso."
    assert D.titular("Renew", mp, {"embudo": {"lectura": "parejo"}})[1] == "lo que más mira es garantía y posventa."


def test_lectura_recomienda_sin_afirmar_lo_que_no_medimos():
    mp = {"audience_mix": {"adsets": 117, "frio_pct": 100.0, "caliente": 0}}
    t = D.lectura("GWM", mp, {"embudo": {"lectura": "ella_mira"}}, None)
    assert t.startswith("<b>Lectura:</b> El 100 % de los conjuntos le habla a gente que no conoce la marca y ninguno")
    assert "conviene sumar una pieza para quien acompaña la decisión" in t and "ningún anuncio" not in t
    poco = D.lectura("Leapmotor", {"audience_mix": {"adsets": 40, "frio_pct": 92.5, "caliente": 3}}, {}, None)
    assert "El 92 % de los conjuntos va a público frío y solo 3 usan retargeting o base propia" in poco
    mucho = D.lectura("Soueast", {"audience_mix": {"adsets": 51, "frio_pct": 56.9, "caliente": 22}}, {}, None)
    assert "Ya hay retargeting o base propia en 43 % de los conjuntos" in mucho


def _pruebas():
    fase = lambda desde, hasta, dias, ld, cpl, ia, resto, total: {
        "desde": desde, "hasta": hasta, "dias": dias, "cuenta": {"leads_dia": ld, "cpl": cpl},
        "modelos": {"Master": {"ia": {"leads_dia": ia}, "resto": {"leads_dia": resto}, "total": {"leads_dia": total}}}}
    return {"hasta": "2026-10-11",
            "renew": {"Clavos": {"gasto": 60.0, "conversaciones": 180}, "Mantecas": {"gasto": 40.0, "conversaciones": 43}},
            "renew_habitual": {"gasto": 248.24, "conversaciones": 375.0},
            "Renault": {"acumulado": {"cuenta|ia": [442.0, 67], "cuenta|resto": [1277.0, 409]},
                        "fases": {"antes": fase("2026-09-04", "2026-09-17", 14, 14.0, 3.70, 0, 0.4, 0.4),
                                  "IA 1ª versión": fase("2026-09-18", "2026-09-21", 4, 16.0, 3.95, 3.2, 1.2, 4.5),
                                  "IA corregida": fase("2026-09-22", "2026-10-11", 20, 20.6, 3.56, 1.8, 5.0, 6.8)},
                        "conjuntos": {"Koleos": {"estado": "ACTIVE", "dia": 9.0}, "Master": {"estado": "PAUSED", "dia": 11.0}},
                        "respuestas": {"Master": {"leads": 48, "este_mes": 11, "empresa": 8}}},
            "Mitsubishi": {"acumulado": {"cuenta|ia": [420.61, 36], "cuenta|resto": [1192.0, 385]},
                           "fases": {"antes": fase("2026-09-07", "2026-09-20", 14, 27.0, 2.38, 0, 0, 0),
                                     "IA corregida": fase("2026-09-24", "2026-10-11", 18, 20.1, 3.75, 0, 0, 0)},
                           "conjuntos": {"L200": {"estado": "ACTIVE", "dia": 20.0}},
                           "respuestas": {"L200": {"leads": 29, "este_mes": 9, "financiacion": 22}}}}


def test_resultados_comparan_sin_culpar_a_nadie():
    html = D.lamina_resultados(_pruebas(), "12/10")
    assert "USD 0,45" in html and "USD 0,66" in html and "32 % más barato" in html
    assert "+47 %" in html and "pasó de <b>0,4 a 6,8 leads por día</b>" in html
    assert "1,8 de la prueba y 5,0 de la agencia" in html
    assert "04/09 al 17/09" in html and "22/09 al 11/10" in html           # fechas exactas de la comparación
    assert "USD 6,60" in html and "USD 3,12" in html and "USD 11,68" in html and "USD 3,10" in html
    assert "USD 963" in html                                    # lo invertido en las tres pruebas
    assert "recién arrancaba" in html
    assert "guía de los anuncios que ya están hechos" in html and "no como campañas nuevas" in html
    for prohibido in ("compit", "pele", "culpa", "se encarec", "bajó"):
        assert prohibido not in html.lower(), prohibido


def test_renew_habitual_saca_las_campanas_de_prueba():
    filas = [{"campaign_id": D.base.RENEW["Clavos"], "spend": "60", "actions": [
                 {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "180"}]},
             {"campaign_id": "1", "spend": "248.24", "actions": [
                 {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "375"}]},
             {"campaign_id": "2", "spend": "50", "actions": [{"action_type": "lead", "value": "10"}]}]
    original = D.base._get
    D.base._get = lambda *a, **k: {"data": filas}
    try:
        assert D.renew_habitual("t") == {"gasto": 248.24, "conversaciones": 375.0}
    finally:
        D.base._get = original


def _marcas_roadmap():
    def modelo(nombre, gap, ventas, sugerido, actual, stock):
        return {"name": nombre, "segment": {"gap": gap, "orders_last_365d": ventas, "ad_count": 5},
                "budget": {"suggested_month": sugerido, "current_month_est": actual}, "extras": {"stock": stock}}
    return {"Jetour": {"marca": {"audience_mix": {"frio_pct": 99.6}},
                       "modelos": [modelo("Jetour X50", "sub-pautado", 291, 900, 300,
                                          {"total": 300, "disponible": 102, "en_viaje": 198, "fecha": "2026-09-18"}),
                                   modelo("Jetour T2", "sobre-pautado", 50, 100, 900, {})]},
            "GWM": {"marca": {"audience_mix": {"frio_pct": 100}},
                    "modelos": [modelo("GWM Wingle", "sub-pautado", 40, 700, 100,
                                       {"total": 20, "disponible": 0, "en_viaje": 20, "fecha": "2026-09-18"}),
                                modelo("GWM Tank", "sub-pautado", 5, 900, 0, {})]},          # pocas ventas: no entra
            "JAC": {"marca": {"audience_mix": {"frio_pct": 80}},
                    "modelos": [modelo("JAC LD250", "sub-pautado", 17, 266, 90, {})]},       # sin dato de stock: a confirmar
            "Soueast": {"marca": {"audience_mix": {"frio_pct": 57}}, "modelos": []}}


def test_candidatos_roadmap():
    c = D.candidatos_roadmap(_marcas_roadmap(), {"marcas": {"GWM": {"embudo": {"lectura": "ella_mira"}}}})
    assert c == {"probar": ["Jetour X50 (291 ventas al año; 102 disponibles + 198 en viaje al 18/09)"],
                 "esperar": ["GWM Wingle (40 ventas al año; 0 disponibles + 20 en viaje al 18/09)"],
                 "confirmar": ["JAC LD250 (17 ventas al año; sin dato de stock)"],
                 "frio": ["GWM", "Jetour"], "acompana": ["GWM"]}
    html = D.lamina_roadmap(c, "12/10")
    assert "Confirmar el stock antes de pautar" in html and "95 % o más de los conjuntos" in html
    assert "Guía de los anuncios hechos" in html and "solo donde falta pauta" in html
    assert "Falta pauta:" in html and "Retargeting:" in html          # las palabras difíciles vienen definidas en la lámina
    assert "tablero mensual" not in html                               # ya existen los dashboards


def test_guia_explica_cada_lamina_con_los_mismos_datos():
    c = D.candidatos_roadmap(_marcas_roadmap(), {"marcas": {}})
    inv = {"anuncios": 1972, "conjuntos": 772, "anuncios_activos": 1320, "comparativos": 0, "competidores": 9, "cambios": 203,
           "versiones": 662, "marcas_datacar": 48, "nuestras_versiones": 124, "mercado": 62314, "unidades_sr": 4137, "share": "6.6",
           "marcas_mercado": 80, "facturadas": 3662, "ventas_meta": 43, "ventas": 422, "sitios": 8, "google": 97, "publicos": 55,
           "corridas": 25, "notas": 2137, "bib_fecha": ("2026", "10", "12"), "bib_anuncios": 52, "bib_competidores": 8}
    secciones = D.guia(_pruebas(), inv, c, "12/10", _cv())
    assert [t.split(" · ")[0] for t, _ in secciones] == ["Lámina 1", "Lámina 2", "Lámina 3", "Lámina 4", "Preguntas que puede hacer Valentina"]
    texto = " ".join(a + " " + b for _, items in secciones for a, b in items)
    for dato in ("USD 0.45", "USD 0.66", "+47 %", "USD 963", "6,6 %", "Koleos activo (USD 9 por día), Master en pausa",
                 "L200 activo (USD 20 por día)", "sin dato de stock", "52 anuncios de 8 marcas o casas competidoras", "se leen a pedido"):
        assert dato in texto or dato.replace(".", ",") in texto, dato
    for prohibido in ("peleó", "se encarecen", "culpa"):
        assert prohibido not in texto, prohibido
    md = D.guia_md(secciones, "2026-10-12", "12/10")
    assert md.startswith("---") and "## Lámina 3 · Cómo seguir con las demás marcas" in md and "## Lámina 2 · ¿Esos leads convirtieron?" in md


def _cv():
    def marca(con_p, con_r, mad_p, mad_r, antes, con, ant):
        return {"fechas": {"con": con, "antes": ant, "madura_hasta": "2026-10-04"}, "con": {"prueba": con_p, "resto": con_r},
                "madura": {"prueba": mad_p, "resto": mad_r}, "antes": {"cuenta": antes}}
    return {"fecha": "2026-10-12", "septiembre": [13123, 7233, 4, 12],
            "Renault": marca([53, 53, 30, 0, 0], [360, 359, 202, 0, 0], [38, 38, 19, 0, 0], [226, 226, 87, 0, 0], [197, 197, 139, 0, 1],
                             ["2026-09-22", "2026-10-11"], ["2026-09-04", "2026-09-17"]),
            "Mitsubishi": marca([30, 30, 24, 0, 0], [328, 326, 195, 0, 0], [24, 24, 19, 0, 0], [230, 230, 122, 0, 0], [378, 378, 138, 0, 0],
                                ["2026-09-24", "2026-10-11"], ["2026-09-07", "2026-09-20"])}


_INV = {"ventas_meta": 43, "ventas": 422, "ventas_hasta": "2026-09-11"}


def test_sql_de_conversion_solo_cuenta_y_valida_entradas():
    sql = D.sql_conversion("act_956049245637827", "120250583223260518", ("2026-09-04", "2026-09-17"), ("2026-09-22", "2026-10-11"), "2026-10-04")
    assert sql.count("count(*)") >= 3 and "roi_embudo" in sql
    for dato_personal in ("phone", "email", "telefono", "nombre", "name"):
        assert dato_personal not in sql.lower().replace("account_name", "")          # solo conteos: nada de datos de clientes
    for malo in (("act_1; drop table x", "1", "2026-09-04"), ("act_1", "1 or 1=1", "2026-09-04"), ("act_1", "1", "ayer")):
        try:
            D.sql_conversion(malo[0], malo[1], (malo[2], "2026-09-17"), ("2026-09-22", "2026-10-11"), "2026-10-04")
        except AssertionError:
            continue
        raise AssertionError(f"debía rechazar {malo}")


def test_lamina_de_conversion_dice_lo_que_se_mide_y_lo_que_no():
    html = D.lamina_conversion(_cv(), _INV, {"ventas": {"ventas_hasta": "2026-09-11"}}, "12/10")
    for dato in ("56,6", "56,1", "80,0", "59,5", "50,0", "38,5", "79,2", "13.123", "7.233", "llega al <b>11/09</b>", "43 de 422",
                 "Cómo leerlo", "Falta sumar el total por marca", "todavía no se alcanzan a medir"):
        assert dato in html, dato
    assert "igual o más que los demás" in html and "la venta todavía no se alcanza a medir" in html
    for prohibido in ("vende más", "convirtió en venta", "compit"):
        assert prohibido not in html, prohibido                                        # no se afirma lo que no se midió


def test_datos_de_conversion_con_servidor_falso():
    pr = _pruebas()
    filas = {"Renault": [["con", "prueba", "53", "53", "30", "0", "0"], ["con", "resto", "360", "359", "202", "0", "0"],
                         ["madura", "prueba", "38", "38", "19", "0", "0"], ["antes", "cuenta", "197", "197", "139", "0", "1"]]}
    original = D.consulta_servidor

    def falso(sql):                                   # las consultas por marca empiezan con «with r as»; la de septiembre, no
        return filas["Renault"] if sql.startswith("with r as") else [["13123", "7233", "4", "12"]]
    D.consulta_servidor = falso
    cache = Path(ROOT) / "output" / "raw" / "conversion_directorio_2099-01-01.json"
    try:
        cv = D.datos_conversion("2099-01-01", pr, sin_meta=False)
        assert cv["Renault"]["con"]["prueba"] == [53, 53, 30, 0, 0] and cv["Renault"]["antes"]["cuenta"] == [197, 197, 139, 0, 1]
        assert cv["Renault"]["fechas"]["madura_hasta"] == "2026-10-04"                # 7 días antes del fin de la ventana
        assert cv["septiembre"] == [13123, 7233, 4, 12]
        assert cache.exists() and D.datos_conversion("2099-01-01", pr, sin_meta=True) == json.loads(cache.read_text(encoding="utf-8"))
    finally:
        D.consulta_servidor = original
        if cache.exists():
            cache.unlink()


def test_guia_de_conversion_no_atribuye_la_baja_a_la_prueba():
    items = dict(D.guia_conversion(_cv(), _INV, 13))
    assert "Mismas fechas (22/09 al 11/10)" in items["Renault: ¿se contactan?"] and "50,0 % (19 de 38)" in items["Renault: ¿se contactan?"]
    assert "no viene de la prueba" in items["Renault: ¿se contactan?"] and "70,4 %" not in items["Renault: ¿se contactan?"]
    assert "Son pocos leads" in items["Mitsubishi: ¿se contactan?"]
    assert "11/09" in items["Qué todavía no se mide"] and "Renew" in items["Qué todavía no se mide"]
    assert "comparativo con el período anterior" in items["Qué haría falta para medir la venta"]


def test_inventario_lee_el_vault():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmp:
        v = Path(tmp)
        archivos = {
            "Buyer Personas/📢 Promociones Competencia.md": "# x\n### 🟢 A\n### 🟢 B\n",
            "Competencia/⚔️ Bitácora de Competencia.md": "- **06/10 17:21** · A\n- **05/10 17:06** · B\n- nota\n",
            "Competencia/💰 Precios Mercado 0km (Datacar).md": "---\nversiones: 662\n---\n48 marcas · 296 modelos\n",
            "Competencia/📊 Mercado Automotor PY 2026.md": "---\nunidades_mercado: 62314\nshare_santa_rosa: 6.6\nmarcas_en_el_mercado: 80\n---\n",
            "Sistema/🧠 Memoria de Audiencia.md": "**25 corridas**\n## ✅ Lo que ya sabemos\n| a | 🟢 sólido |\n| b | 🟢 sólido |\n## 🔄 Qué cambió\n| c | 🟢 sólido |\n",
            "Campañas/🏷️ Clasificación de Anuncios.md": "---\nanuncios_activos: 1320\n---\n## ⚠️ Para revisar: posible publicidad comparativa (0)\n",
            "Competencia/📣 Anuncios de la Competencia.md": "---\ngenerado: '2026-10-12'\n---\n## Resumen\n\n| Competidor | Leídos |\n|---|---|\n| A | 3 | 3 |\n| B | 0 | 0 |\n| C | 5 | 1 |\n\n## Por competidor\n\n| Desde | Días |\n| 17/08 | 56 | x |\n\nDe **52** anuncios leídos, 6 hablan de una oferta",
            "Buyer Personas/GWM/Marketing/Google Ads - GWM Poer.md": "x",
            "Seguridad/hallazgo.md": "x",
        }
        for rel, txt in archivos.items():
            (v / rel).parent.mkdir(parents=True, exist_ok=True)
            (v / rel).write_text(txt, encoding="utf-8")
        original = D.VAULT
        D.VAULT = v
        try:
            inv = D.inventario({"ventas": {}, "materiales": {}}, {})
        finally:
            D.VAULT = original
    assert (inv["competidores"], inv["cambios"], inv["versiones"], inv["marcas_datacar"]) == (2, 2, 662, 48)
    assert (inv["mercado"], inv["share"], inv["marcas_mercado"]) == (62314, "6.6", 80)
    assert (inv["corridas"], inv["publicos"], inv["anuncios_activos"], inv["comparativos"]) == (25, 2, 1320, 0)
    assert inv["google"] == 1 and inv["notas"] == 8                    # Seguridad no cuenta
    assert inv["bib_fecha"] == ("2026", "10", "12") and inv["bib_anuncios"] == 52 and inv["bib_competidores"] == 2
    assert inv["facturadas"] is None and inv["sitios"] == 8           # sin nota no inventa; sin el manual quedan los 8 sitios del 24-25/09
    html = D.lamina_sistema(inv, "12/10")
    assert "6,6 %" in html and "1.320" in html and "—" in html
    assert "se leen a pedido: 52 anuncios de 2 marcas o casas el 12/10" in html          # la Biblioteca no corre sola
    sin_nota = D.lamina_sistema({**inv, "bib_fecha": (None, None, None), "bib_anuncios": None}, "12/10")
    assert "se leen a pedido, con una sesión de Claude" in sin_nota

if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
