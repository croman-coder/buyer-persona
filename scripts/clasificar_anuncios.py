#!/usr/bin/env python3
"""Clasifica con Jev (TypeSafe, vía Vercel AI Gateway u OpenRouter) los anuncios de Meta y escribe la nota
«🏷️ Clasificación de Anuncios» en el vault (Buyer Persona/Campañas/).

Fuente: el último output/raw/data_sources_*.json que deja el pipeline de las 06:00.
Bases: una nota por anuncio en Cuentas Meta/Anuncios/ (fuera de las carpetas que lee el globo del Cerebro) y la base
Cuentas Meta/🏷️ Anuncios Meta.base con vistas filtradas. Solo se reescribe lo que cambió.
Cache: output/raw/clasificacion_anuncios.json, por hash del texto: cada corrida solo le pregunta a
Jev por los textos nuevos. Los anuncios son contenido público; no se manda ningún dato de clientes.

Uso:
  venv/bin/python3 scripts/clasificar_anuncios.py            # clasifica lo nuevo y escribe la nota
  venv/bin/python3 scripts/clasificar_anuncios.py --max 20   # prueba con 20 textos, sin escribir la nota
  venv/bin/python3 scripts/clasificar_anuncios.py --hilos 1  # más despacio, si el proveedor devuelve 429
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import random
import re
import sys
import urllib.parse
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "output/raw"
CACHE = RAW / "clasificacion_anuncios.json"
NOTA = RAIZ / "Buyer Persona/Campañas/🏷️ Clasificación de Anuncios.md"
DIR_ANUNCIOS = RAIZ / "Buyer Persona/Cuentas Meta/Anuncios"   # fuera de las fuentes del Cerebro: no llena el globo
BASE = RAIZ / "Buyer Persona/Cuentas Meta/🏷️ Anuncios Meta.base"
# Mismo modelo por dos puertas. Vercel si hay clave de AI Gateway (~/.config/typesafe/vercel.env, con tope de gasto
# mensual); si no, OpenRouter con la clave de Hermes.
PROVEEDORES = {
    "vercel": ("Vercel AI Gateway", "https://ai-gateway.vercel.sh/typesafe/v1/systemone", "typesafe-ai/jev"),
    "openrouter": ("OpenRouter", "https://openrouter.ai/api/v1/systemone", "~typesafe/jev-latest"),
}
CLAVE_VERCEL = Path.home() / ".config/typesafe/vercel.env"
ESTADOS = ("ACTIVE", "WITH_ISSUES", "DISAPPROVED")
HILOS = 3
VERSION_PREGUNTAS = 2  # subir si cambian las preguntas: invalida la cache


def noul(i):
    return {"type": "noul", "instructions": i}


def choice(i, c):
    return {"type": "choice", "instructions": i, "criteria": c}


def score(i, c):
    return {"type": "score", "instructions": i, "criteria": c}


PREGUNTAS = {
    "oferta": choice("¿Cuál es la oferta principal del anuncio?", {
        "precio": "un precio concreto es el gancho principal (USD, 'desde')",
        "financiacion": "cuotas, financiación, tasa o entrega inicial",
        "descuento_bono": "descuento, bono, regalo o precio especial por tiempo limitado",
        "permuta": "toma de usado o canje",
        "lanzamiento": "preventa, lanzamiento o novedad que llega a Paraguay",
        "unidad_usada": "una unidad usada puntual (año, versión, kilometraje)",
        "prueba_evento": "invita a probar el vehículo o a un evento",
        "sin_oferta": "habla del vehículo sin oferta concreta",
    }),
    "argumento": choice("¿Qué argumento usa para convencer?", {
        "precio_ahorro": "precio bajo, ahorro, conveniencia",
        "tecnologia": "equipamiento, pantallas, tecnología, conectividad",
        "seguridad": "airbags, frenos, asistencias, seguridad",
        "electrico": "eléctrico o híbrido: autonomía, carga, sin combustible",
        "espacio_familia": "espacio, 7 asientos, familia, viajes",
        "diseno_estatus": "diseño, lujo, premium, estatus",
        "trabajo_potencia": "potencia, 4x4, carga, trabajo, robustez",
        "respaldo": "garantía, service, respaldo de la marca o de la empresa",
    }),
    "segmento": choice("¿Qué tipo de vehículo promociona?", {
        "suv": None, "pickup": None, "sedan_hatch": "sedán o hatchback",
        "utilitario_van": "utilitario, furgón o van", "varios": "varios modelos distintos",
        "no_dice": "no se puede saber",
    }),
    # v2: las marcas propias no son competencia (la v1 marcaba T2 naftera vs híbrida o Jetour vs GWM Jolion)
    "comparativa": noul("¿El anuncio se compara con una marca o modelo de la COMPETENCIA, o dice que es mejor que otra marca? "
                        "Las marcas de Santa Rosa no son competencia: Renault, Mitsubishi, GWM (Haval, Tank, Ora, Poer), Jetour, JAC, "
                        "Zeekr, Leapmotor, JMEV, Soueast y XPeng. Comparar modelos o versiones de esas marcas entre sí NO cuenta. "
                        "Tampoco cuenta nombrar el vehículo usado que se vende ni el usado que se recibe como parte de pago."),
    "precio": noul("¿Muestra un precio concreto?"),
    "financiacion": noul("¿Menciona cuotas o financiación?"),
    "llamado": noul("¿Le dice claramente al cliente qué hacer (escribir por WhatsApp, visitar, llamar, reservar)?"),
    "urgencia": score("¿Cuánta urgencia transmite?", [
        "ninguna", "genérica (aprovechá ya, no te lo pierdas)", "plazo o cupo concreto (hasta tal fecha, últimas unidades)"]),
}


def _leer_env(ruta: Path, variable: str) -> str:
    if not ruta.is_file():
        return ""
    for linea in ruta.read_text().splitlines():
        linea = linea.strip().removeprefix("export ").strip()
        if linea.startswith(variable + "="):
            return linea.split("=", 1)[1].strip().strip("\"'")
    return ""


def credencial() -> tuple[str, str, str, str]:
    """(nombre, url, modelo, clave): Vercel primero, OpenRouter si no hay clave de AI Gateway."""
    k = os.environ.get("AI_GATEWAY_API_KEY", "").strip() or _leer_env(CLAVE_VERCEL, "AI_GATEWAY_API_KEY")
    if k:
        return (*PROVEEDORES["vercel"], k)
    k = os.environ.get("OPENROUTER_API_KEY", "").strip() or _leer_env(Path.home() / ".hermes/.env", "OPENROUTER_API_KEY")
    if k:
        return (*PROVEEDORES["openrouter"], k)
    sys.exit("Falta la clave: AI_GATEWAY_API_KEY (~/.config/typesafe/vercel.env) u OPENROUTER_API_KEY (~/.hermes/.env).")


def _mensaje(e: urllib.error.HTTPError) -> str:
    try:
        d = json.load(e)
        err = d.get("error") if isinstance(d.get("error"), dict) else d
        tipo = err.get("error_type") or err.get("type") or err.get("code") or ""
        return (f"{tipo}: " if tipo else "") + str(err.get("message") or d)[:200]
    except Exception:
        return str(e.reason)


class Bloqueado(RuntimeError):
    """Error que no se arregla reintentando (sin saldo, clave inválida, equipo sin verificar): corta la corrida."""


def preguntar(prov: tuple, estado: str) -> dict:
    nombre, url, modelo, clave = prov
    cuerpo = json.dumps({"model": modelo, "state": estado, "questions": PREGUNTAS}).encode()
    for intento in range(6):
        pedido = urllib.request.Request(url, data=cuerpo, method="POST",
                                        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403):
                raise Bloqueado(f"{nombre} {e.code}: {_mensaje(e)}") from None
            if e.code in (429, 500, 502, 503, 504) and intento < 5:
                # 429/503 llegan en ráfagas cuando el proveedor está cargado: esperar más y desfasar los hilos
                time.sleep((4 if e.code == 429 else 2) * 2 ** intento + random.uniform(0, 2))
                continue
            raise RuntimeError(f"HTTP {e.code}: {_mensaje(e)}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if intento < 5:
                time.sleep(2 ** intento)
                continue
            raise RuntimeError(f"red: {e}") from None
    raise RuntimeError("sin respuesta")


def hash_texto(a: dict) -> str:
    return hashlib.sha1(f"{VERSION_PREGUNTAS}\n{a.get('title', '')}\n{a.get('body', '')}".encode()).hexdigest()[:16]


def estado_de(a: dict) -> str:
    return f"Cuenta: {a.get('account', '')}\nTítulo: {a.get('title', '')}\nTexto: {a.get('body', '')}"


def resumir(r: dict) -> dict:
    ans = r.get("answers", {})
    out = {}
    for k in ("oferta", "argumento", "segmento"):
        out[k] = ans.get(k, {}).get("choice")
        out[f"{k}_conf"] = round(ans.get(k, {}).get("confidence", 0), 2)
    for k in ("comparativa", "precio", "financiacion", "llamado"):
        out[k] = round(ans.get(k, {}).get("noul", 0), 2)
    out["urgencia"] = round(ans.get("urgencia", {}).get("score", 0), 2)
    out["tokens"] = r.get("usage", {}).get("input_tokens", 0)
    out["costo"] = float(r.get("usage", {}).get("cost")                                         # OpenRouter
                         or r.get("provider_metadata", {}).get("gateway", {}).get("cost") or 0)  # Vercel
    return out


def limpio(t: str, n: int) -> str:
    t = " ".join(str(t or "").split()).replace("|", "/")
    return t if len(t) <= n else t[: n - 1] + "…"


def pct(n: int, d: int) -> str:
    return f"{round(100 * n / d)} %" if d else "—"


HUBS = ("Campañas Meta - ultimos 90 dias", "🎯 Playbook Meta Ads", "🤖 Meta Ads Lo Que Funciona", "💸 Pauta Meta Rendimiento")


def _existe(nombre: str) -> bool:
    return any(NOTA.parent.parent.rglob(f"{nombre}.md"))


def enlace_marca(cuenta: str) -> str:
    """Enlace a la ficha de la marca (así la nota queda conectada en el globo del Cerebro). Fuera de tablas:
    el Cerebro corta el destino en el primer '|', y dentro de una tabla el alias tiene que ir escapado."""
    base = NOTA.parent.parent / "Buyer Personas" / cuenta
    for nombre in (cuenta, f"Comprador {cuenta}"):
        if (base / f"{nombre}.md").is_file():
            return f"[[{nombre}|{cuenta}]]" if nombre != cuenta else f"[[{nombre}]]"
    return ""


# --- Todo lo que ve marketing: etiquetas en castellano en vez de los códigos internos de las preguntas ---
ETIQUETAS = {
    "oferta": {
        "precio": "Precio como gancho", "financiacion": "Financiación o cuotas", "descuento_bono": "Descuento o bono",
        "permuta": "Toma de usado", "lanzamiento": "Lanzamiento o preventa", "unidad_usada": "Usado puntual",
        "prueba_evento": "Invitación a probar o a un evento", "sin_oferta": "Sin oferta concreta",
    },
    "argumento": {
        "precio_ahorro": "Precio y ahorro", "tecnologia": "Tecnología", "seguridad": "Seguridad",
        "electrico": "Eléctrico o híbrido", "espacio_familia": "Espacio y familia", "diseno_estatus": "Diseño y estatus",
        "trabajo_potencia": "Potencia y trabajo", "respaldo": "Respaldo y garantía",
    },
    "segmento": {
        "suv": "SUV", "pickup": "Pickup", "sedan_hatch": "Sedán o hatchback", "utilitario_van": "Utilitario o van",
        "varios": "Varios modelos", "no_dice": "No se sabe",
    },
}
ESTADO_ES = {"ACTIVE": "Activo", "WITH_ISSUES": "Con problemas en Meta", "DISAPPROVED": "Rechazado por Meta"}
BOTON_ES = {
    "WHATSAPP_MESSAGE": "Enviar WhatsApp", "MESSAGE_PAGE": "Enviar mensaje", "INSTAGRAM_MESSAGE": "Enviar mensaje por Instagram",
    "VIEW_INSTAGRAM_PROFILE": "Ver perfil de Instagram", "LEARN_MORE": "Más información", "SIGN_UP": "Registrarte",
    "CONTACT_US": "Contactanos", "GET_QUOTE": "Pedir cotización", "CALL_NOW": "Llamar", "APPLY_NOW": "Postularte",
    "BOOK_TRAVEL": "Reservar", "SHOP_NOW": "Comprar", "GET_OFFER": "Obtener oferta", "SUBSCRIBE": "Suscribirte",
    "WATCH_MORE": "Ver más", "NO_BUTTON": "Sin botón",
}
UMBRAL_REVISAR, UMBRAL_DUDOSO = 0.5, 0.35


def et(campo: str, valor) -> str:
    return ETIQUETAS[campo].get(valor, valor or "—")


def estado_es(s) -> str:
    return ESTADO_ES.get(s, s or "—")


def boton_es(b) -> str:
    return BOTON_ES.get(b, str(b or "").replace("_", " ").capitalize() or "Sin botón")


def riesgo_pct(r: float) -> str:
    return f"{round(100 * r)} %"


def revisar(r: float) -> str:
    return "⚠️ Posible comparativa" if r >= UMBRAL_REVISAR else ("Dudoso" if r >= UMBRAL_DUDOSO else "—")


def si_no(p: float) -> str:
    return "Sí" if p >= 0.5 else "No"


def _urgencia(score: float) -> str:
    return "Sin urgencia" if score < 0.5 else ("Urgencia genérica" if score < 1.5 else "Con fecha o cupo")


def escribir_nota(ads: list[dict], cls: dict, fuente: str, costo_corrida: float, aviso: str = "", proveedor: str = "") -> None:
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    filas = [(a, cls[hash_texto(a)]) for a in ads if hash_texto(a) in cls]
    activos = [(a, c) for a, c in filas if a.get("status") == "ACTIVE"]
    por_cuenta = collections.defaultdict(list)
    for a, c in activos:
        por_cuenta[a.get("account") or "?"].append(c)
    leidos, total = len({hash_texto(a) for a, _ in filas}), len({hash_texto(a) for a in ads})

    L = ["---", "type: clasificacion-anuncios", f"generado: '{ahora}'", f"fuente: {fuente}",
         f"modelo: typesafe/jev ({proveedor or '?'})", f"anuncios_activos: {len(activos)}", f"textos_clasificados: {leidos}",
         "tags:", "- meta-ads", "- clasificacion", "- jev", "---", "",
         "# 🏷️ Clasificación de Anuncios", "",
         "Todos los días una IA lee el texto de **cada anuncio de Meta** de todas las marcas (los activos y los que Meta frenó) "
         "y lo clasifica: qué ofrece, con qué argumento vende, qué tipo de vehículo muestra, si pone precio o cuotas, si le dice "
         "al cliente qué hacer y, lo más importante, si puede estar haciendo **publicidad comparativa**, que en Paraguay no está "
         "permitida.", ""]
    if aviso:
        L += [f"> [!danger] {aviso}", ""]
    L += [f"> [!info] Actualizado el **{ahora}** · {len(activos)} anuncios activos · {leidos} de {total} textos leídos", "",
          "> [!info]- Cómo leer esta nota (tocá para abrir)",
          "> - **Es una ayuda para revisar, no un dictamen.** La IA (Jev, de TypeSafe) lee solo el *texto* del aviso: no ve la imagen ni el video.",
          "> - **Riesgo de publicidad comparativa**, de 0 % a 100 %: desde 50 % el aviso aparece en **«Para revisar»**; entre 35 % y 50 %, en **«Dudosos»**.",
          "> - **Qué cuenta como comparativa:** nombrar una marca o un modelo de la competencia para compararse, o decir que somos mejores que otra marca. "
          "**No cuenta:** comparar modelos o versiones de nuestras marcas entre sí, ni nombrar el usado que vende Renew o el que se recibe como parte de pago.",
          "> - **Oferta principal:** el gancho del aviso (precio, cuotas, descuento, lanzamiento…). «Sin oferta concreta» quiere decir que habla del auto pero no ofrece nada puntual.",
          "> - **Argumento:** la razón que da para comprar (precio, tecnología, seguridad, espacio, diseño, potencia…).",
          "> - **Invita a actuar:** si el *texto* le dice al cliente qué hacer (escribir, venir, llamar). El botón de Meta aparece igual; esto mide solo el texto.",
          "> - **Apura:** si el aviso transmite urgencia («aprovechá ya») o pone fecha o cupo.",
          "> - Se actualiza solo todas las mañanas (06:50). Si cambian un aviso en Meta, se ve acá al día siguiente.", ""]

    marcas = [e for e in (enlace_marca(cu) for cu in sorted(por_cuenta, key=lambda x: -len(por_cuenta[x]))) if e]
    hubs = [f"[[{h}]]" for h in HUBS if _existe(h)]
    if marcas:
        L += ["**Fichas de marca:** " + " · ".join(marcas), ""]
    if hubs:
        L += ["**Relacionado:** " + " · ".join(hubs), ""]

    comp = sorted(((a, c) for a, c in filas if c["comparativa"] >= UMBRAL_REVISAR), key=lambda x: -x[1]["comparativa"])
    L += [f"## ⚠️ Para revisar: posible publicidad comparativa ({len(comp)})", "",
          "Avisos donde la IA cree que se nombra o se compara con otra marca. **Qué hacer:** abrir el aviso, leerlo y decidir con "
          "el responsable de la marca si se corrige o se pausa.", ""]
    if comp:
        L += ["| Riesgo | Cuenta | Estado | Anuncio | Qué dice el texto |", "|---:|---|---|---|---|"]
        L += [f"| {riesgo_pct(c['comparativa'])} | {a.get('account')} | {estado_es(a.get('status'))} | {limpio(a.get('ad_name'), 40)} | "
              f"{limpio(a.get('body') or a.get('title'), 120)} |" for a, c in comp[:60]]
    else:
        L += ["Ningún aviso se compara con otra marca. ✅"]
    dudosos = sorted(((a, c) for a, c in filas if UMBRAL_DUDOSO <= c["comparativa"] < UMBRAL_REVISAR), key=lambda x: -x[1]["comparativa"])
    if dudosos:
        L += ["", f"<details><summary>Dudosos ({len(dudosos)}): la IA no está segura, conviene una mirada rápida</summary>", "",
              "| Riesgo | Cuenta | Anuncio | Qué dice el texto |", "|---:|---|---|---|"]
        L += [f"| {riesgo_pct(c['comparativa'])} | {a.get('account')} | {limpio(a.get('ad_name'), 40)} | {limpio(a.get('body') or a.get('title'), 120)} |"
              for a, c in dudosos[:30]]
        L += ["", "</details>"]

    rech = collections.Counter((estado_es(a.get("status")), a.get("account"), limpio(a.get("ad_name"), 40), et("oferta", c["oferta"]),
                                limpio(a.get("title"), 60)) for a, c in filas if a.get("status") in ("DISAPPROVED", "WITH_ISSUES"))
    if rech:
        L += ["", f"## 🚫 Frenados por Meta ({sum(rech.values())})", "",
              "Meta rechazó estos avisos o les encontró un problema, así que no se están mostrando bien. El motivo exacto está en el "
              "Administrador de anuncios de cada cuenta.", "",
              "| Estado | Cuenta | Anuncio | Oferta | Título | Veces |", "|---|---|---|---|---|---:|"]
        L += [f"| {e} | {cu} | {n} | {o} | {ti} | {v} |" for (e, cu, n, o, ti), v in sorted(rech.items(), key=lambda x: (x[0][0], x[0][1]))]

    L += ["", "## Cómo vende cada marca (anuncios activos)", "",
          "Para cada cuenta: la oferta y el argumento que más usa, y qué parte de sus avisos muestra precio, menciona cuotas, "
          "invita a actuar o apura.", "",
          "| Cuenta | Activos | Oferta que más usa | Argumento que más usa | Muestra precio | Menciona cuotas | Invita a actuar | Apura |",
          "|---|---:|---|---|---:|---:|---:|---:|"]
    for cuenta, cs in sorted(por_cuenta.items(), key=lambda x: -len(x[1])):
        n = len(cs)
        of = collections.Counter(c["oferta"] for c in cs).most_common(1)[0]
        ar = collections.Counter(c["argumento"] for c in cs).most_common(1)[0]
        L.append(f"| {cuenta} | {n} | {et('oferta', of[0])} ({pct(of[1], n)}) | {et('argumento', ar[0])} ({pct(ar[1], n)}) | "
                 f"{pct(sum(c['precio'] >= 0.5 for c in cs), n)} | {pct(sum(c['financiacion'] >= 0.5 for c in cs), n)} | "
                 f"{pct(sum(c['llamado'] >= 0.5 for c in cs), n)} | {pct(sum(c['urgencia'] >= 0.75 for c in cs), n)} |")

    for campo, titulo, explica in (("oferta", "Qué ofrecen los avisos", "El gancho principal de cada aviso activo."),
                                   ("argumento", "Con qué argumento venden", "La razón que da el aviso para comprar."),
                                   ("segmento", "Qué tipo de vehículo muestran", "Según lo que dice el texto.")):
        cnt = collections.Counter(c[campo] for _, c in activos)
        L += ["", f"## {titulo}", "", explica, "", "| | Avisos | % |", "|---|---:|---:|"]
        L += [f"| {et(campo, k)} | {v} | {pct(v, len(activos))} |" for k, v in cnt.most_common()]

    sin = sum(1 for _, c in activos if c["llamado"] < 0.5)
    L += ["", f"En **{sin}** avisos activos el texto no le dice al cliente qué hacer (el botón de Meta está igual). "
          "La lista completa está en la vista «El texto no invita a actuar» de la tabla."]

    uri = "obsidian://open?vault=" + urllib.parse.quote(NOTA.parent.parent.name) + "&file=" + urllib.parse.quote(
        str(BASE.relative_to(NOTA.parent.parent)))
    L += ["", "## 🗂️ Tabla para filtrar (en Obsidian)", "",
          f"Cada aviso tiene su ficha en `Cuentas Meta/Anuncios/`, y la tabla [🏷️ Anuncios Meta]({uri}) los junta con estas vistas "
          "(pestañas arriba de la tabla):", "",
          "- **Por cuenta**: todos los avisos, agrupados por marca.",
          "- **⚠️ Para revisar**: posibles comparativos y dudosos, primero los de mayor riesgo.",
          "- **🚫 Frenados por Meta**: rechazados o con problemas.",
          "- **El texto no invita a actuar**: avisos activos cuyo texto no dice qué hacer.",
          "- **Sin oferta concreta**: avisos activos que no ofrecen nada puntual.", "",
          "Se puede ordenar tocando el nombre de una columna y filtrar desde el menú de la tabla. Lo que se edite a mano se pisa en la "
          "próxima actualización."]
    L += ["", "---", f"*Generado por `scripts/clasificar_anuncios.py` · fuente {fuente} · última corrida US$ {costo_corrida:.4f}*", ""]
    NOTA.parent.mkdir(parents=True, exist_ok=True)
    tmp = NOTA.with_suffix(".md.tmp")
    tmp.write_text("\n".join(L), encoding="utf-8")
    tmp.replace(NOTA)


def _nombre_archivo(a: dict) -> str:
    base = re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", f"{a.get('account') or '?'} · {a.get('ad_name') or 'sin nombre'}")
    base = " ".join(base.split())[:80].rstrip(" .")
    return f"{base} · {str(a.get('ad_id', ''))[-8:]}.md"


def _q(s) -> str:
    return json.dumps(str(s or ""), ensure_ascii=False)  # un string JSON es un string YAML válido


def _nota_anuncio(a: dict, c: dict) -> str:
    r = c["comparativa"]
    nombre = " ".join(str(a.get("ad_name") or "Anuncio").split())
    titulo = " ".join(str(a.get("title") or "").split())
    cuerpo = re.sub(r"(^|\s)#", r"\1\\#", str(a.get("body") or ""))  # que los #hashtags del aviso no sean tags del vault
    estado, boton = estado_es(a.get("status")), boton_es(a.get("cta"))
    avisos = []
    if r >= UMBRAL_REVISAR:
        avisos += ["> [!warning] Para revisar", f"> La IA cree que este aviso puede estar nombrando o comparándose con otra marca "
                   f"(riesgo {riesgo_pct(r)}). Leé el texto y decidí con el responsable de la marca si se corrige o se pausa.", ""]
    elif r >= UMBRAL_DUDOSO:
        avisos += ["> [!note] Dudoso", f"> La IA no está segura de si este aviso se compara con otra marca (riesgo {riesgo_pct(r)}). "
                   "Conviene una mirada rápida.", ""]
    if a.get("status") in ("DISAPPROVED", "WITH_ISSUES"):
        avisos += [f"> [!danger] {estado}", "> Meta frenó este aviso o le encontró un problema. El motivo está en el Administrador de anuncios.", ""]
    L = ["---", "type: anuncio-meta",
         f"cuenta: {_q(a.get('account'))}", f"estado: {_q(estado)}", f"revisar: {_q(revisar(r))}", f"riesgo_comparativa: {r}",
         f"oferta: {_q(et('oferta', c['oferta']))}", f"argumento: {_q(et('argumento', c['argumento']))}",
         f"tipo_de_vehiculo: {_q(et('segmento', c['segmento']))}",
         f"muestra_precio: {'true' if c['precio'] >= 0.5 else 'false'}",
         f"menciona_cuotas: {'true' if c['financiacion'] >= 0.5 else 'false'}",
         f"invita_a_actuar: {'true' if c['llamado'] >= 0.5 else 'false'}",
         f"urgencia: {_q(_urgencia(c['urgencia']))}", f"boton: {_q(boton)}",
         f"anuncio: {_q(nombre)}", f"titulo: {_q(titulo)}", f"ad_id: {_q(a.get('ad_id'))}",
         "tags:", "- anuncio-meta", "---", "",
         f"# {nombre}", "", *avisos,
         f"**Cuenta:** {a.get('account')} · **Estado:** {estado} · **Botón:** {boton}", "",
         "| Qué miró la IA | Resultado |", "|---|---|",
         f"| Oferta principal | {et('oferta', c['oferta'])} |", f"| Argumento de venta | {et('argumento', c['argumento'])} |",
         f"| Tipo de vehículo | {et('segmento', c['segmento'])} |", f"| Muestra precio | {si_no(c['precio'])} |",
         f"| Menciona cuotas | {si_no(c['financiacion'])} |",
         f"| El texto le dice al cliente qué hacer | {si_no(c['llamado'])}{'' if c['llamado'] >= 0.5 else ' (el botón está igual)'} |",
         f"| Urgencia | {_urgencia(c['urgencia'])} |", f"| Riesgo de publicidad comparativa | {riesgo_pct(r)} |", "",
         "## Texto del aviso", ""]
    if titulo and not re.fullmatch(r"[\w.-]+\.[a-z]{2,4}", titulo):  # Meta pone «instagram.com» como título de los avisos de IG
        L += [f"**Título:** {titulo}", ""]
    L += [cuerpo.strip(), "", "---", "*Ficha generada sola todos los días a partir de Meta. Qué significa cada cosa: "
          "[[🏷️ Clasificación de Anuncios]], sección «Cómo leer esta nota».*", ""]
    return "\n".join(L)


COLUMNAS = ["file.name", "revisar", "cuenta", "estado", "oferta", "argumento", "tipo_de_vehiculo", "muestra_precio",
            "menciona_cuotas", "invita_a_actuar", "urgencia", "riesgo_comparativa"]
NOMBRES = {"file.name": "Anuncio", "revisar": "Revisar", "cuenta": "Cuenta", "estado": "Estado", "oferta": "Oferta principal",
           "argumento": "Argumento", "tipo_de_vehiculo": "Tipo de vehículo", "muestra_precio": "Muestra precio",
           "menciona_cuotas": "Menciona cuotas", "invita_a_actuar": "Invita a actuar", "urgencia": "Urgencia",
           "riesgo_comparativa": "Riesgo de comparativa (0 a 1)", "boton": "Botón", "titulo": "Título"}


def _base() -> str:
    def vista(nombre, filtros=None, agrupar=False):
        v = ["  - type: table", f"    name: {_q(nombre)}"]
        if agrupar:
            v += ["    groupBy:", "      property: note.cuenta", "      direction: ASC"]
        if filtros:
            clave, lista = filtros
            v += ["    filters:", f"      {clave}:"] + [f"        - {_q(f)}" for f in lista]
        v += ["    order:"] + [f"      - {col}" for col in COLUMNAS]
        v += ["    sort:", "      - property: riesgo_comparativa", "        direction: DESC"]
        return v
    L = ["# Generado por scripts/clasificar_anuncios.py: los cambios a mano se pisan en la próxima corrida.",
         "filters:", "  and:", '    - file.inFolder("Cuentas Meta/Anuncios")', "    - 'type == \"anuncio-meta\"'",
         "properties:"]
    for k, n in NOMBRES.items():
        L += [f"  {k}:", f"    displayName: {_q(n)}"]
    L += ["views:"]
    L += vista("Por cuenta", agrupar=True)
    L += vista("⚠️ Para revisar", ("and", [f"riesgo_comparativa >= {UMBRAL_DUDOSO}"]))
    L += vista("🚫 Frenados por Meta", ("or", ['estado == "Rechazado por Meta"', 'estado == "Con problemas en Meta"']))
    L += vista("El texto no invita a actuar", ("and", ['estado == "Activo"', "invita_a_actuar == false"]), agrupar=True)
    L += vista("Sin oferta concreta", ("and", ['estado == "Activo"', 'oferta == "Sin oferta concreta"']), agrupar=True)
    return "\n".join(L) + "\n"


def _escribir_si_cambio(ruta: Path, texto: str) -> bool:
    if ruta.is_file() and ruta.read_text(encoding="utf-8") == texto:
        return False
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    tmp.replace(ruta)
    return True


def escribir_bases(ads: list[dict], cls: dict) -> tuple[int, int, int]:
    """Una nota por anuncio clasificado + la base. Borra solo notas propias (type: anuncio-meta) que ya no están."""
    DIR_ANUNCIOS.mkdir(parents=True, exist_ok=True)
    deseadas = {}
    for a in ads:
        c = cls.get(hash_texto(a))
        if c and a.get("ad_id"):
            deseadas[_nombre_archivo(a)] = _nota_anuncio(a, c)
    cambiadas = sum(_escribir_si_cambio(DIR_ANUNCIOS / n, txt) for n, txt in deseadas.items())
    borradas = 0
    for f in DIR_ANUNCIOS.glob("*.md"):
        if f.name not in deseadas and f.read_text(encoding="utf-8", errors="replace").startswith("---\ntype: anuncio-meta\n"):
            f.unlink()
            borradas += 1
    _escribir_si_cambio(BASE, _base())
    return len(deseadas), cambiadas, borradas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="clasificar como mucho N textos nuevos (prueba; no escribe la nota)")
    ap.add_argument("--hilos", type=int, default=HILOS, help=f"pedidos en paralelo (por defecto {HILOS})")
    args = ap.parse_args()

    fuentes = sorted(RAW.glob("data_sources_*.json"), key=lambda p: p.stat().st_mtime)
    if not fuentes:
        sys.exit("No hay output/raw/data_sources_*.json (¿corrió el pipeline?)")
    fuente = fuentes[-1]
    ads = [a for a in json.loads(fuente.read_text(encoding="utf-8")).get("meta_ads", {}).get("ad_creatives", [])
           if a.get("status") in ESTADOS and (a.get("title") or a.get("body"))]
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.is_file() else {}
    cls: dict = cache.get("textos", {})

    nuevos = {}
    for a in ads:
        h = hash_texto(a)
        if h not in cls and h not in nuevos:
            nuevos[h] = estado_de(a)
    pendientes = list(nuevos.items())[: args.max] if args.max else list(nuevos.items())
    print(f"{fuente.name}: {len(ads)} anuncios · {len(cls)} textos en cache · {len(pendientes)} para clasificar")

    prov = credencial()
    print(f"proveedor: {prov[0]} ({prov[2]})")
    costo, errores, bloqueo, ok, t0 = 0.0, [], "", 0, time.time()
    with concurrent.futures.ThreadPoolExecutor(max(1, args.hilos)) as ex:
        futuros = {ex.submit(preguntar, prov, estado): h for h, estado in pendientes}
        for i, f in enumerate(concurrent.futures.as_completed(futuros), 1):
            h = futuros[f]
            try:
                c = resumir(f.result())
                cls[h] = c
                ok += 1
                costo += float(c["costo"])
            except concurrent.futures.CancelledError:
                continue
            except Bloqueado as e:
                errores.append(str(e))
                if not bloqueo:
                    bloqueo = str(e)
                    for otro in futuros:
                        otro.cancel()
            except RuntimeError as e:
                errores.append(str(e))
            if i % 100 == 0:
                print(f"  {i}/{len(pendientes)} · {time.time() - t0:.0f} s")
                CACHE.write_text(json.dumps({"version": VERSION_PREGUNTAS, "textos": cls}, ensure_ascii=False), encoding="utf-8")
    vigentes = {hash_texto(a) for a in ads}  # la cache guarda solo los textos de la versión y los anuncios actuales
    cls = {h: v for h, v in cls.items() if h in vigentes}
    CACHE.write_text(json.dumps({"version": VERSION_PREGUNTAS, "textos": cls}, ensure_ascii=False), encoding="utf-8")
    print(f"clasificados {ok} de {len(pendientes)} en {time.time() - t0:.0f} s · US$ {costo:.4f} · errores {len(errores)}")
    for e in sorted(set(errores))[:5]:
        print("  error:", e)

    if args.max:
        print("(modo prueba: no se escribe la nota)")
        return
    # La cache guarda todo lo ya clasificado: una corrida con errores no empeora la nota, así que se escribe siempre
    # y el aviso dice cuánto quedó pendiente.
    faltan = len({hash_texto(a) for a in ads} - set(cls))
    if bloqueo:
        aviso = f"Incompleta: {prov[0]} cortó la corrida ({bloqueo}). La próxima corrida completa lo que falta."
    elif faltan:
        aviso = (f"Incompleta: {faltan} textos quedaron sin clasificar por errores temporales de {prov[0]} "
                 "(demanda alta). La próxima corrida los reintenta.")
    else:
        aviso = ""
    escribir_nota(ads, cls, fuente.name, costo, aviso, prov[0])
    total, cambiadas, borradas = escribir_bases(ads, cls)
    print(f"nota: {NOTA.relative_to(RAIZ)} · base: {total} anuncios ({cambiadas} escritos, {borradas} borrados)")
    if bloqueo or faltan:
        sys.exit(f"incompleta: faltan {faltan} textos" + (f" ({bloqueo})" if bloqueo else ""))


if __name__ == "__main__":
    main()
