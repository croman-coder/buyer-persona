#!/usr/bin/env python3
"""Optimización del conjunto Koleos (Renault, campaña IA 2026-09).

Diagnóstico 2026-09-22 (4 días de pauta): CPL USD 27,49 contra USD 2,36 del
Master. El CTR del Koleos es el mejor de los cuatro anuncios (0,75 %), así que
la creatividad no es el problema: la caída está después del clic
(23 clics -> 1 lead = 4,3 %, contra 28,3 % del Master; Fisher p = 0,025).

Tres causas y tres cambios:

1. El formulario está en modo "mayor intención" (is_optimized_for_quality), que
   agrega una pantalla de revisión antes de enviar, y la tarjeta de contexto
   abre con el precio de contado (USD 36.990). Se crea un formulario nuevo en
   modo volumen, con las mismas preguntas, y la tarjeta reordenada: beneficio
   primero, precio al final.
2. Con USD 9/día la entrega se repartía en 12 ubicaciones. Notificaciones,
   marketplace, búsqueda, perfil e instream se llevaron ~USD 3 (11 % del gasto)
   sin traer un solo lead. Se limita a feed, stories y reels de FB e IG.
3. Los intereses genéricos "Vehículos" y "Automóviles" son los más disputados
   de Paraguay y explican el CPM de USD 8,19 contra USD 3,77 del Master. Se
   dejan solo SUV y Renault; Advantage+ audience sigue expandiendo por su
   cuenta.

No borra nada: el formulario viejo queda activo (con su lead histórico) y los
anuncios conservan su ID, solo se les cambia el creativo.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"

ACCOUNT = "act_956049245637827"
PAGE = "111900348505782"
IG_USER = "17841458364035470"
ADSET_KOLEOS = "120250583224730518"
AD_IMG = "120250583225800518"
AD_VIDEO = "120250583226020518"
VIDEO_ID = "1402847491216308"
IMG_FEED = "e52d9274d4a10cbdf99ed5696b6e4062"   # 4:5
IMG_SQ = "6c82c3842417b84cbdafa3239d8d6ead"     # 1:1
IMG_STORY = "6f679d0067c0facb035d839a7f589be4"  # 9:16

STATE = os.path.join(ROOT, "output", "pauta_renault_ia_2026-09.json")

# Intereses que se conservan (se caen "Vehículos" y "Automóviles", genéricos y caros)
INTERESES_KOLEOS = [
    {"id": "6003304473660", "name": "Vehículo utilitario deportivo (vehículos)"},
    {"id": "6003569017318", "name": "Renault (vehículos)"},
]

PLACEMENTS = {
    "publisher_platforms": ["facebook", "instagram"],
    "facebook_positions": ["feed", "story", "facebook_reels"],
    "instagram_positions": ["stream", "story", "reels", "explore"],
}

TITULO = "Koleos Full Hybrid E-Tech · desde USD 400/mes"
DESCRIPCION = "Cotizá en 1 minuto, sin compromiso."
BODY_FEED = (
    "Koleos Full Hybrid E-Tech esprit Alpine. Híbrido de verdad: arrancás en "
    "eléctrico, gastás menos y llegás con estilo.\n\n"
    "✔ Contado USD 36.990 o desde USD 400/mes*\n"
    "✔ Tecnología híbrida E-Tech e interior premium esprit Alpine\n"
    "✔ Stock disponible para entrega inmediata en Santa Rosa\n\n"
    "Dejá tus datos y un asesor te arma tu plan hoy.\n*Sujeto a entrega inicial."
)
BODY_STORY = (
    "Koleos Full Hybrid E-Tech · desde USD 400/mes* · Entrega inmediata. "
    "Pedí tu cotización 👇\n*Sujeto a entrega inicial."
)


def call(path, params=None, post=False, token=None):
    params = dict(params or {})
    params["access_token"] = token or TOKEN
    url = f"{API}/{path}"
    try:
        if post:
            data = urllib.parse.urlencode(params).encode()
            return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data)))
        return json.load(urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params)))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"ERROR {path}: {exc.read().decode()[:600]}")


def page_token():
    return call(PAGE, {"fields": "access_token"})["access_token"]


def crear_formulario(ptoken):
    """Formulario v2: modo volumen (sin pantalla de revisión) y tarjeta que abre
    con el beneficio; el precio queda al final."""
    preguntas = [
        {
            "type": "CUSTOM",
            "key": "cuando_cambias",
            "label": "¿Cuándo pensás cambiar tu vehículo?",
            "options": [
                {"key": "este_mes", "value": "Este mes"},
                {"key": "3_meses", "value": "En los próximos 3 meses"},
                {"key": "mirando", "value": "Solo estoy mirando"},
            ],
        },
        {
            "type": "CUSTOM",
            "key": "como_compras",
            "label": "¿Cómo pensás comprarlo?",
            "options": [
                {"key": "financiacion", "value": "Financiación"},
                {"key": "contado", "value": "Contado"},
                {"key": "usado", "value": "Entrego mi usado + financiación"},
            ],
        },
        {"type": "FULL_NAME"},
        {"type": "PHONE"},
        {"type": "EMAIL"},
        {"type": "CITY"},
    ]
    contexto = {
        "style": "LIST_STYLE",
        "title": "Koleos Full Hybrid E-Tech esprit Alpine",
        "content": [
            "Arrancás en eléctrico y gastás menos en combustible",
            "Entregá tu usado como parte de pago",
            "Interior premium esprit Alpine y entrega inmediata",
            "Desde USD 400/mes* · *Sujeto a entrega inicial",
        ],
        "button_text": "Quiero mi cotización",
    }
    gracias = {
        "title": "¡Gracias! Un asesor de Renault Santa Rosa te contacta hoy.",
        "body": "Mientras tanto podés ver toda la gama en nuestro sitio.",
        "button_type": "VIEW_WEBSITE",
        "button_text": "Ver la gama",
        "website_url": "https://renault.com.py/",
    }
    res = call(
        f"{PAGE}/leadgen_forms",
        {
            "name": "SRPY - KOLEOS v2 volumen - IA Buyer Persona - 2026-09",
            "locale": "es_LA",
            "questions": json.dumps(preguntas, ensure_ascii=False),
            "context_card": json.dumps(contexto, ensure_ascii=False),
            "thank_you_page": json.dumps(gracias, ensure_ascii=False),
            "privacy_policy": json.dumps(
                {"url": "https://renault.com.py/legalInfo.html", "link_text": "Información Legal"}
            ),
            "question_page_custom_headline": "Koleos Full Hybrid E-Tech: cotizá tu plan en 1 minuto",
            "follow_up_action_url": "https://renault.com.py/",
            "is_optimized_for_quality": "false",
        },
        post=True,
        token=ptoken,
    )
    return res["id"]


def dof():
    """Advantage+ creative encendido, el resto de automatizaciones apagadas."""
    return {"creative_features_spec": {"advantage_plus_creative": {"enroll_status": "OPT_IN"}}}


def crear_creativo_imagen(form_id):
    feed = {
        "publisher_platforms": ["facebook", "instagram"],
        "facebook_positions": ["feed"],
        "instagram_positions": ["stream", "explore"],
        "age_min": 13,
        "age_max": 65,
    }
    story = {
        "publisher_platforms": ["facebook", "instagram"],
        "facebook_positions": ["story", "facebook_reels"],
        "instagram_positions": ["story", "reels"],
        "age_min": 13,
        "age_max": 65,
    }
    resto = {
        "publisher_platforms": ["facebook", "instagram", "audience_network", "messenger"],
        "age_min": 13,
        "age_max": 65,
    }
    spec = {
        "images": [
            {"hash": IMG_STORY, "adlabels": [{"name": "story"}]},
            {"hash": IMG_FEED, "adlabels": [{"name": "feed"}]},
            {"hash": IMG_SQ, "adlabels": [{"name": "sq"}]},
        ],
        "bodies": [
            {"text": BODY_STORY, "adlabels": [{"name": "bstory"}]},
            {"text": BODY_FEED, "adlabels": [{"name": "bfeed"}]},
        ],
        "titles": [{"text": TITULO}],
        "descriptions": [{"text": DESCRIPCION}],
        "ad_formats": ["SINGLE_IMAGE"],
        "call_to_action_types": ["GET_QUOTE"],
        "call_to_actions": [
            {"type": "GET_QUOTE", "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"}}
        ],
        "link_urls": [{"website_url": "http://fb.me/"}],
        "optimization_type": "PLACEMENT",
        "asset_customization_rules": [
            {
                "customization_spec": story,
                "image_label": {"name": "story"},
                "body_label": {"name": "bstory"},
                "priority": 1,
            },
            {
                "customization_spec": feed,
                "image_label": {"name": "feed"},
                "body_label": {"name": "bfeed"},
                "priority": 2,
            },
            {
                "customization_spec": resto,
                "image_label": {"name": "sq"},
                "body_label": {"name": "bfeed"},
                "priority": 3,
            },
        ],
    }
    res = call(
        f"{ACCOUNT}/adcreatives",
        {
            "name": "Koleos · IA · imagen por ubicación · v2 form volumen · 2026-09-22",
            "object_story_spec": json.dumps({"page_id": PAGE, "instagram_user_id": IG_USER}),
            "asset_feed_spec": json.dumps(spec, ensure_ascii=False),
            "degrees_of_freedom_spec": json.dumps(dof()),
        },
        post=True,
    )
    return res["id"]


def crear_creativo_video(form_id):
    story_spec = {
        "page_id": PAGE,
        "instagram_user_id": IG_USER,
        "video_data": {
            "video_id": VIDEO_ID,
            "title": TITULO,
            "message": BODY_FEED,
            "link_description": DESCRIPCION,
            "image_hash": IMG_STORY,
            "call_to_action": {
                "type": "GET_QUOTE",
                "value": {"lead_gen_form_id": form_id, "link": "http://fb.me/"},
            },
        },
    }
    res = call(
        f"{ACCOUNT}/adcreatives",
        {
            "name": "Koleos · IA · reel · v2 form volumen · 2026-09-22",
            "object_story_spec": json.dumps(story_spec, ensure_ascii=False),
            "degrees_of_freedom_spec": json.dumps(dof()),
        },
        post=True,
    )
    return res["id"]


def actualizar_targeting():
    actual = call(ADSET_KOLEOS, {"fields": "targeting"})["targeting"]
    nuevo = dict(actual)
    nuevo["flexible_spec"] = [{"interests": INTERESES_KOLEOS}]
    nuevo.update(PLACEMENTS)
    # Estas dos se recalculan solas a partir de publisher_platforms
    nuevo.pop("device_platforms", None)
    call(ADSET_KOLEOS, {"targeting": json.dumps(nuevo, ensure_ascii=False)}, post=True)
    return nuevo


def main():
    ptoken = page_token()

    form_id = crear_formulario(ptoken)
    print(f"1/3  formulario v2 (modo volumen): {form_id}")

    cre_img = crear_creativo_imagen(form_id)
    cre_vid = crear_creativo_video(form_id)
    call(AD_IMG, {"creative": json.dumps({"creative_id": cre_img})}, post=True)
    call(AD_VIDEO, {"creative": json.dumps({"creative_id": cre_vid})}, post=True)
    print(f"     creativos nuevos: gráfica {cre_img} · reel {cre_vid} (anuncios actualizados)")

    nuevo = actualizar_targeting()
    print("2/3  ubicaciones:", nuevo["facebook_positions"], "/", nuevo["instagram_positions"])
    print("3/3  intereses:", [i["name"] for i in INTERESES_KOLEOS])

    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            estado = json.load(fh)
        estado["form_Koleos_v2"] = form_id
        estado["creative_Koleos_img_v2"] = cre_img
        estado["creative_Koleos_video_v2"] = cre_vid
        estado["optimizacion_2026-09-22"] = {
            "motivo": "CPL 27.49 vs 2.36 del Master; clic->lead 4.3% vs 28.3% (p=0.025)",
            "cambios": ["form modo volumen + tarjeta beneficio primero",
                        "ubicaciones limitadas a feed/story/reels",
                        "quitados intereses Vehículos y Automóviles"],
        }
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(estado, fh, ensure_ascii=False, indent=1)
        print("     estado guardado en", os.path.relpath(STATE, ROOT))


if __name__ == "__main__":
    main()
