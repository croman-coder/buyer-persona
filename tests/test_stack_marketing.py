"""Stack de marketing de las webs del mercado: lectura del registro de red, clasificación, cambios y nota. Datos inventados.

Corre con pytest o directo: venv/bin/python3 tests/test_stack_marketing.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stack_marketing_competencia as S  # noqa: E402

CUANDO = "19/10 05:00"
KIA = {"nombre": "Kia Paraguay (Garden)", "url": "https://kia.com.py", "propio": False}
JETOUR = {"nombre": "Jetour Paraguay", "url": "https://www.jetour.com.py", "propio": True}


def test_lee_el_registro_de_red_completo_y_cortado():
    netlog = {"constants": {}, "events": [
        {"type": 1, "params": {"url": "https://connect.facebook.net/en_US/fbevents.js"}},
        {"type": 2, "params": {"net_error": -3}},
        {"type": 1, "params": {"url": "data:image/png;base64,AAAA"}},
        {"type": 1},
    ]}
    texto = json.dumps(netlog)
    assert S.urls_de_netlog(texto) == {"https://connect.facebook.net/en_US/fbevents.js"}
    # Chrome cortado por el timeout deja el JSON sin cerrar: igual se lee.
    cortado = texto[: texto.rindex("]")] + ","
    assert S.urls_de_netlog(cortado) == {"https://connect.facebook.net/en_US/fbevents.js"}
    assert S.urls_de_netlog("") == set() and S.urls_de_netlog("basura") == set()


def test_clasifica_herramientas_y_cuentas():
    urls = [
        "https://connect.facebook.net/signals/config/1234567890?v=2.9",
        "https://www.facebook.com/tr/?id=1234567890&ev=PageView",
        "https://analytics.tiktok.com/i18n/pixel/events.js?sdkid=CABC123XYZ&lib=ttq",
        "https://www.googletagmanager.com/gtm.js?id=GTM-ABC12",
        "https://www.googletagmanager.com/gtag/js?id=G-XYZ987&l=dataLayer",
        "https://www.googletagmanager.com/gtag/js?id=AW-555",
        "https://googleads.g.doubleclick.net/pagead/viewthroughconversion/777/?random=1",
        "https://11179852.fls.doubleclick.net/activityi;src=11179852;type=x",
        "https://www.clarity.ms/tag/abc12def",
        "https://c.clarity.ms/c.gif",
        "https://cdp.customer.io/v1/b",
        "https://dpm.demdex.net/id?d_visid_ver=1",
        "https://x.bidswitch.net/sync",
        "https://static.ads-twitter.com/uwt.js",
    ]
    herramientas, otros = S.clasificar(urls, "kia.com.py")
    assert herramientas == {
        "Meta Pixel": ["1234567890"],
        "TikTok Pixel": ["CABC123XYZ"],
        "Google Tag Manager": ["GTM-ABC12"],
        "Google Analytics 4": ["G-XYZ987"],
        "Google Ads": ["AW-555", "AW-777"],
        "Campaign Manager 360": ["11179852"],
        "Microsoft Clarity": ["abc12def"],
        "Customer.io": [],
        "Adobe Audience Manager": [],
        "BidSwitch": [],
        "X (Twitter) Ads": [],
    }
    assert otros == []
    for h in herramientas:
        assert S.CATEGORIA[h] in S.CATEGORIAS


def test_ignora_el_trafico_de_chrome_y_el_propio_sitio():
    urls = [
        "https://clients2.google.com/service/update2/crx",
        "https://update.googleapis.com/service/update2/json",
        "https://optimizationguide-pa.googleapis.com/v1:GetModels",
        "https://rr6---sn-abc.gvt1.com/edgedl/chrome/x.crx",
        "https://kia.com.py/",
        "https://cdn.kia.com.py/img/a.jpg",
        "https://www.kia.com.py/modelos",
        "https://wt.rqtrk.eu/pixel",
    ]
    herramientas, otros = S.clasificar(urls, "kia.com.py")
    assert herramientas == {}
    assert otros == ["wt.rqtrk.eu"]                    # tercero sin firma: queda anotado para revisar


def test_gateway_de_conversions_api_en_subdominio_propio():
    herramientas, otros = S.clasificar(
        ["https://capi.garden.com.py/events", "https://capi-automation.s3.us-east-2.amazonaws.com/x.js",
         "https://scripts.icommkt.online/t.js", "https://capitulo.ejemplo.com/a"], "kia.com.py")
    assert herramientas == {"Meta Conversions API (gateway)": [], "iCommKT (email marketing)": []}
    assert otros == ["capitulo.ejemplo.com"]


def test_el_dominio_tiene_que_coincidir_entero():
    herramientas, otros = S.clasificar(
        ["https://notfacebook.net/tr?id=1", "https://clarity.ms.evil.com/tag/x", "https://xclarity.ms/a"], "kia.com.py")
    assert herramientas == {}
    assert otros == ["clarity.ms.evil.com", "notfacebook.net", "xclarity.ms"]


def test_dominio_propio_sin_www():
    assert S.dominio_propio("https://www.jetour.com.py") == "jetour.com.py"
    assert S.dominio_propio("https://kia.com.py/modelos") == "kia.com.py"


def test_primera_lectura_no_genera_eventos():
    estado, eventos = S.comparar(KIA, None, {"Meta Pixel": ["1"]}, CUANDO)
    assert eventos == []
    assert estado["herramientas"] == {"Meta Pixel": {"ids": ["1"], "faltas": 0}}


def test_herramienta_nueva_y_cuenta_nueva():
    previo, _ = S.comparar(KIA, None, {"Meta Pixel": ["1"], "Google Ads": ["AW-1"]}, CUANDO)
    estado, eventos = S.comparar(KIA, previo, {"Meta Pixel": ["1"], "Google Ads": ["AW-1", "AW-2"],
                                               "TikTok Pixel": ["C1"]}, CUANDO)
    assert eventos == [
        f"- **{CUANDO}** · Kia Paraguay (Garden) (competencia) — empezó a usar TikTok Pixel (C1)",
        f"- **{CUANDO}** · Kia Paraguay (Garden) (competencia) — cuenta nueva de Google Ads: AW-2",
    ]
    assert estado["herramientas"]["Google Ads"]["ids"] == ["AW-1", "AW-2"]


def test_para_dar_de_baja_hacen_falta_dos_semanas_sin_verla():
    s0, _ = S.comparar(JETOUR, None, {"Meta Pixel": ["9"], "Hotjar": ["5"]}, CUANDO)
    s1, ev1 = S.comparar(JETOUR, s0, {"Meta Pixel": ["9"]}, CUANDO)
    assert ev1 == []                                         # una semana sin verla puede ser carga diferida
    assert s1["herramientas"]["Hotjar"] == {"ids": ["5"], "faltas": 1}
    vuelve, ev = S.comparar(JETOUR, s1, {"Meta Pixel": ["9"], "Hotjar": ["5"]}, CUANDO)
    assert ev == [] and vuelve["herramientas"]["Hotjar"]["faltas"] == 0
    s2, ev2 = S.comparar(JETOUR, s1, {"Meta Pixel": ["9"]}, CUANDO)
    assert ev2 == [f"- **{CUANDO}** · Jetour Paraguay (propio) — dejó de cargar Hotjar (dos semanas sin verla)"]
    assert "Hotjar" not in s2["herramientas"]


def test_nota_separa_competencia_y_propios_y_marca_lo_que_falta():
    estado = {
        KIA["nombre"]: S.comparar(KIA, None, {"Meta Pixel": ["1"], "TikTok Pixel": ["C1"],
                                              "Customer.io": []}, CUANDO)[0],
        JETOUR["nombre"]: S.comparar(JETOUR, None, {"Meta Pixel": ["9"]}, CUANDO)[0],
    }
    estado[KIA["nombre"]]["herramientas"]["Customer.io"]["faltas"] = 1
    nota = S.render(estado, [KIA, JETOUR], "2026-10-19")
    assert "> [!danger] Uso interno" in nota
    assert nota.index("## Competencia") < nota.index("Kia Paraguay (Garden)") < nota.index("## Nuestros sitios")
    assert "Customer.io (no se vio esta semana)" in nota
    lo_que_falta = nota.split("## Lo que usa la competencia y nosotros no", 1)[1].split("##", 1)[0]
    assert "TikTok Pixel" in lo_que_falta and "Meta Pixel" not in lo_que_falta
    assert nota.rstrip().endswith(S.MARCADOR_FIN)


def test_un_sitio_caido_no_cuenta_como_lectura():
    assert S.lectura_valida(set(), "kia.com.py") is False
    assert S.lectura_valida({"https://kia.com.py/"}, "kia.com.py") is False      # solo el propio sitio: no cargó nada de afuera
    # El tráfico de fondo de Chrome no prueba que la página haya cargado.
    assert S.lectura_valida({"https://kia.com.py/", "https://update.googleapis.com/x"}, "kia.com.py") is False
    assert S.lectura_valida({"https://kia.com.py/", "https://connect.facebook.net/x.js"}, "kia.com.py") is True
    pagina = "<html><body>" + "x" * 6000 + "</body></html>"
    assert S.lectura_valida({"https://kia.com.py/"}, "kia.com.py", pagina) is True
    error = '<html><body><div id="main-frame-error">' + "x" * 6000 + "</div></body></html>"
    assert S.lectura_valida({"https://kia.com.py/"}, "kia.com.py", error) is False


if __name__ == "__main__":
    pruebas = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"OK: {len(pruebas)} pruebas")
