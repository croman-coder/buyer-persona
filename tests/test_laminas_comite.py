"""Láminas del comité: textos de las tarjetas de marca y de las pruebas. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_laminas_comite.py
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_spec = importlib.util.spec_from_file_location("laminas_comite", os.path.join(ROOT, "scripts", "laminas_comite.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

HOY = "2026-10-05"


def _modelo(nombre, ventas, anuncios, gap, hoy, sugerido, stock=None, genero="Masculino", edad="35-44", share=70.0, nivel="modelo"):
    return {"name": nombre, "segment": {"type": "model", "brand": "Marca", "orders_last_365d": ventas, "ad_count": anuncios, "gap": gap},
            "demographics": {"gender": genero, "age_range": edad, "meta_level": nivel, "meta": {"gender_share": share}},
            "budget": {"current_month_est": hoy, "suggested_month": sugerido}, "extras": {"stock": stock} if stock else {}}


def _comp(estado, ganador="Imagen", rival="Video", dif=0.2, meses=5, ganados=4):
    return {"estado": estado, "ganador": ganador, "rival": rival, "dif": dif, "meses": meses, "meses_ganados": ganados}


def _mat(formato, tramo=None, ubic=None, chat=False, vertical=None):
    """Análisis de materiales mínimo: 3 meses completos a USD 2 por resultado (300) y octubre incompleto."""
    meses = {m: {"Total": {"gasto": 200.0, "resultados": 100}} for m in ("2026-07", "2026-08", "2026-09")}
    meses["2026-10"] = {"Total": {"gasto": 50.0, "resultados": 10}}
    ubic = ubic or [{"clave": "Feed", "costo": 2.0, "suficiente": True}, {"clave": "Reels", "costo": 2.1, "suficiente": True}]
    comps = {"formato": formato, "tramo": tramo or {}}
    if vertical:
        comps[f"vertical|{formato.get('ganador')}"] = vertical
    r = {"total": {"gasto": 1000}, "meses": meses, "ubicaciones": ubic, "comparaciones": comps}
    return {"destinos": {"chat" if chat else "formulario": r}}


def test_formatos():
    assert L.usd(2.5) == "USD 2,50" and L.usd(1234) == "USD 1.234" and L.usd(None) == "—"
    assert L.dec(7.04) == "7,0" and L.corta("2026-10-04") == "04/10"
    assert L.dia_local("2026-10-05T01:00:00+0000") == "2026-10-04"          # 22 h del 04/10 en Paraguay
    assert L.y_lista(["H6"]) == "H6" and L.y_lista(["H6", "H9", "Tank 400"]) == "H6, H9 y Tank 400"


def test_publico_y_stock():
    assert L.publico(_modelo("Marca X", 1, 1, "equilibrado", 0, 0, share=68.8, edad="25-34")) == "Hombre 25-34 (69 %)"
    assert L.publico(_modelo("Marca X", 1, 1, "equilibrado", 0, 0, genero="Femenino", nivel="marca")).endswith("(70 %) · dato de la marca")
    assert L.stock_txt({"total": 108, "disponible": 20, "en_viaje": 83}) == "20 disponibles + 83 en viaje"
    assert L.stock_txt({"total": 2, "disponible": 1, "en_viaje": 1}) == "1 disponible + 1 en viaje"
    assert L.stock_txt({"total": 49, "disponible": 43, "en_viaje": 0}, largo=True) == "49 en stock (43 disponibles)"


def test_hoy():
    c, n, et = L.costo_reciente(_mat(_comp("gana"))["destinos"]["formulario"], HOY)
    assert (round(c, 2), n, et) == (2.0, 300, "jul a sep")                  # octubre va incompleto: no cuenta
    t = L.linea_hoy(_mat(_comp("gana")), {"ventas": 118, "con_meta": 10}, ("2026-08-06", "2026-09-11"), HOY)
    assert t.startswith("<b>USD 2,00</b> por lead de formulario (jul a sep)") and "<b>10 de 118 ventas</b> (8 %)" in t
    assert "pocas ventas para cruzar con Meta (3 del 06/08 al 11/09)" in L.ventas_con_meta(
        {"ventas": 3, "con_meta": 0}, "2026-08-06", "2026-09-11")
    assert "por conversación de WhatsApp" in L.linea_hoy(_mat(_comp("uno"), chat=True), None, ("2026-08-06", "2026-09-11"), HOY)


def test_que_funciona():
    gana = L.que_funciona(_mat(_comp("gana"), tramo=_comp("gana", "16 a 30 s", "31 a 60 s", 0.3, 5, 3),
                               vertical=_comp("gana", "Imagen|Con versión vertical", "Imagen|Sin versión vertical", 0.3, 4, 3)), {})
    assert gana[0] == "La imagen (gráfica) trae el lead 20 % más barato que el video (4 de 5 meses), mejor con versión vertical (9:16)"
    assert gana[1] == "En video, los de 16 a 30 s: 30 % más baratos (3 de 5 meses)"
    assert gana[2] == "Feed, Reels y Stories cuestan parecido: no forzar una ubicación"
    assert "no todos los meses: tener los dos" in L.que_funciona(_mat(_comp("gana", ganados=2)), {})[0]
    assert L.que_funciona(_mat(_comp("empate")), {})[0] == "La imagen (gráfica) y el video rinden parecido: tener los dos"
    assert L.que_funciona(_mat(_comp("uno")), {})[0] == "Casi todo fue la imagen (gráfica): falta probar otro formato"
    ubic = [{"clave": "Feed", "costo": 1.34, "suficiente": True}, {"clave": "Reels", "costo": 1.62, "suficiente": True}]
    assert "El lead más barato sale en Feed (USD 1,34 contra USD 1,62 en Reels)" in L.que_funciona(_mat(_comp("empate"), ubic=ubic), {})[1]
    chat = L.que_funciona(_mat(_comp("uno"), chat=True, ubic=[{"clave": "Feed", "costo": 0.5, "suficiente": True},
                                                            {"clave": "Stories", "costo": 0.9, "suficiente": True}]), {})
    assert "La conversación más barata sale en Feed" in chat[1]
    ellas = L.que_funciona(_mat(_comp("empate")), {"embudo": {"lectura": "ellas_avanzan", "ellas_vs_ellos": 1.23}})
    assert ellas[-1] == "Ellas son pocas en los clics, pero contactan 1,23× lo que ellos"
    assert L.que_funciona(None, {}) == ["Todavía sin análisis de materiales"]


def test_buenas_practicas():
    centro = {"empresa": {"empresa_pct": 35.0}, "meta_ads": [
        {"clave": "acompañante", "modelos": ["Marca H6", "Marca H9"]},
        {"clave": "empresa", "modelos": ["Marca H9"]},
        {"clave": "compartir", "modelos": []}]}
    mods = [_modelo("Marca H6", 295, 230, "equilibrado", 1270, 1516,
                    {"total": 108, "disponible": 20, "en_viaje": 83, "test_drive": 3, "fecha": "2026-09-18"}),
            _modelo("Marca H9", 70, 48, "equilibrado", 300, 357)]
    bp = L.buenas_practicas("Marca", _mat(_comp("gana")), centro, {"audience_mix": {"frio_pct": 100}}, mods, HOY)
    assert bp[0] == ("USD 14/día o más por conjunto (~50 leads por semana); juzgar a las 3-4 semanas y cortar antes solo "
                     "si a las 2 semanas pasa de USD 4,00 por lead")
    assert bp[1] == "Pieza para quien acompaña la decisión (H6 y H9)"
    assert bp[2] == "Pieza «Para tu empresa»: el 35 % lo factura una empresa (H9)"      # solo las 2 primeras del centro de compra
    assert bp[3] == "Sumar similares y retargeting: el 100 % de los conjuntos va a público frío"
    assert bp[4] == "Test drive solo con unidad de prueba: H6 (stock del 18/09)" and len(bp) == 5
    # WhatsApp barato: nunca menos de USD 5 por día. Marca con agencia en la cuenta. Sin unidad de prueba.
    meses_baratos = _mat(_comp("uno"), chat=True)
    for m in meses_baratos["destinos"]["chat"]["meses"].values():
        m["Total"]["gasto"] = m["Total"]["resultados"] * 0.4
    chat = L.buenas_practicas("Renault", meses_baratos, {}, {"audience_mix": {"frio_pct": 80}}, [], HOY)
    assert chat[0].startswith("USD 5/día o más por conjunto (~50 conversaciones por semana)")
    assert "No pautarle al mismo público que la agencia en la misma cuenta: se encarecen las dos" in chat
    assert chat[-1] == "Sin unidad de test drive en stock: invitar al salón"


def test_proximo_paso():
    sin = _modelo("Marca Wingle", 44, 12, "sub-pautado", 67, 228, {"total": 11, "disponible": 0, "en_viaje": 11})
    t = L.proximo_paso("Marca", [sin], {})
    assert "Esperar el stock de Wingle" in t and "hoy no tiene unidades disponibles (11 en viaje)" in t
    con = _modelo("Marca X50", 291, 75, "sub-pautado", 362, 995, {"total": 137, "disponible": 88, "en_viaje": 47})
    t = L.proximo_paso("Marca", [sin, con], {})
    assert "Probar primero X50" in t and "88 disponibles + 47 en viaje" in t and "sugerido USD 33/día, hoy USD 12/día" in t
    assert "Textos listos" not in t                                   # «Marca» no tiene notas en el vault
    assert "Mantener el reparto" in L.proximo_paso("Marca", [_modelo("Marca Chico", 8, 5, "sub-pautado", 10, 60)], {})
    assert "Mover pauta" not in L.proximo_paso("Marca", [_modelo("Marca C11", 0, 43, "sobre-pautado", 300, 0)], {})
    assert "Mover pauta de Duster" in L.proximo_paso("Marca", [_modelo("Marca Duster", 11, 96, "sobre-pautado", 400, 100)], {})
    una = L.proximo_paso("Marca", [_modelo("Marca G9", 1, 25, "equilibrado", 890, 890)], {"budget": {"spend_month": 890}})
    assert "Mucha pauta para pocas ventas" in una and "1 venta en 12 meses" in una and "USD 890" not in una
    assert "ver la lámina 1" in L.proximo_paso("Renault", [_modelo("Renault Koleos", 57, 108, "equilibrado", 400, 565)], {})


def test_tarjetas():
    datos = {"marca": {"budget": {"spend_month": 890}, "audience_mix": {"adsets": 5, "frio_pct": 60}},
             "modelos": [_modelo("XPeng G9", 1, 25, "equilibrado", 890, 890,
                                 {"total": 2, "disponible": 1, "en_viaje": 1, "test_drive": 1, "fecha": "2026-09-18"})],
             "hoy": HOY, "centro": {}, "material": _mat(_comp("gana", "Video", "Imagen", 0.27, 3, 1)),
             "ventas": {"ventas": 1, "con_meta": 0}, "rango_ventas": ("2026-08-06", "2026-09-11")}
    h = L.tarjeta_marca("XPeng", datos, oscura=True)
    assert 'class="t m"' in h and "<th>" not in h and "/mes en Meta" not in h
    for texto in ("Quién compra", "Qué funciona", "Buenas prácticas", "Próximo paso", "Mucha pauta para pocas ventas",
                  "Ejemplo con datos reales: 1 modelo de referencia, el que más vendió en 12 meses"):
        assert texto in h, texto
    renew = L.tarjeta_marca("Renew", {**datos, "modelos": [_modelo("Renew Jetour", 31, 66, "equilibrado", 166, 219),
                                                           _modelo("Renew Renault", 23, 78, "equilibrado", 197, 163)]}, oscura=False)
    assert "2 marcas de usados de referencia, las que más vendieron" in renew
    reglas = L.tarjeta_reglas("05/10")
    assert "en pausa" in reglas and "competencia" in reglas and "USD 5 por día" in reglas and "3-4 semanas" in reglas


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
