"""Lista de compradores para Meta: limpieza de contactos que no son del comprador. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_publico_compradores.py
"""
import hashlib
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("publico_compradores", os.path.join(ROOT, "scripts", "publico_compradores.py"))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def venta(marca="JETOUR", mail=None, tel=None, tipo="Salon", fecha="2025-03-10 00:00:00"):
    return {"Marca": marca, "E-Mail": mail, "Teléfonos": tel, "Tipo Cliente": tipo, "Fecha": fecha}


def test_normaliza_mails_y_telefonos_de_paraguay():
    assert P.normalizar_mail("  Ana.Perez@Gmail.COM ") == "ana.perez@gmail.com"
    assert P.normalizar_mail("sin dato") is None
    assert P.normalizar_telefonos("0981 123 456 // 021 555 666") == ["595981123456", "59521555666"]
    assert P.normalizar_telefonos("+595 971-222-333") == ["595971222333"]
    assert P.normalizar_telefonos("981222333") == ["595981222333"]
    assert P.normalizar_telefonos("123") == [] and P.normalizar_telefonos(None) == []


def test_descarta_lo_que_no_es_del_comprador():
    filas = [
        venta(mail="cliente1@gmail.com", tel="0981000001"),
        venta(mail="ventas@santarosa.com.py", tel="0981000002"),            # mail de la empresa: queda el teléfono
        venta(mail="sincorreo@gmail.com"),                                  # relleno y sin teléfono: fuera
        venta(mail="compras@otroconcesionario.com.py", tipo="Concesionario"),
        # un teléfono que aparece en 3 ventas (de cualquier marca) es de la empresa o de un vendedor
        venta(mail="cliente2@gmail.com", tel="0981999999"),
        venta(marca="GREATWALL", tel="0981999999"),
        venta(marca="JAC", tel="0981999999"),
    ]
    c = P.limpiar(filas, "Jetour")
    assert c["ventas"] == 5
    assert c["motivos"] == {"mail de Santa Rosa o de Nipon": 1, "mail de relleno": 1, "venta sin ningún contacto limpio": 1,
                            "venta a un concesionario": 1, "teléfono repetido en 3 ventas o más": 1}
    planos = sorted(sum((p["mails"] + p["telefonos"] for p in c["personas"]), []))
    assert planos == ["595981000001", "595981000002", "cliente1@gmail.com", "cliente2@gmail.com"]
    assert "595981999999" not in planos


def test_une_a_la_misma_persona_por_mail_o_telefono():
    filas = [venta(mail="pedro@gmail.com", tel="0981111111", fecha="2024-05-01"),
             venta(mail="pedro.trabajo@gmail.com", tel="0981111111", fecha="2025-07-01"),   # mismo teléfono: misma persona
             venta(mail="lucia@gmail.com", fecha="2026-02-01")]
    c = P.limpiar(filas, "Jetour")
    assert len(c["personas"]) == 2
    assert c["desde"] == "2024-05-01" and c["hasta"] == "2026-02-01" and c["por_anio"] == {"2024": 1, "2025": 1, "2026": 1}
    filas_meta = P.filas_para_meta(c["personas"])
    h = lambda v: hashlib.sha256(v.encode()).hexdigest()
    assert [h("pedro@gmail.com"), h("595981111111")] in filas_meta
    assert [h("pedro.trabajo@gmail.com"), ""] in filas_meta                # el segundo mail va en una fila aparte
    assert [h("lucia@gmail.com"), ""] in filas_meta
    assert all(len(x) == 64 or x == "" for fila in filas_meta for x in fila), "solo cifrado, nada en claro"


def test_mitsubishi_esta_bloqueada():
    try:
        P.limpiar([venta(marca="MITSUBISHI", mail="a@b.com")], "Mitsubishi")
    except SystemExit as e:
        assert "Nipon" in str(e)
    else:
        raise AssertionError("Mitsubishi no debía poder usarse")


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
