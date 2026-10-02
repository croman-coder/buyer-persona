#!/usr/bin/env python3
"""Optimización de la campaña Mitsubishi IA (L200 + Montero, 2026-09).

Auditoría 2026-09-23 (2,5 días de pauta): CPL USD 8,33 (USD 50, 6 leads)
contra USD 2,34 de L200 y 2,68 de Montero en la misma cuenta (30 días).

Tres causas y tres cambios:

1. Los dos anuncios de remarketing se llevaron el 49 % del gasto (USD 24,57)
   y trajeron 1 lead. La gráfica de L200, con el mismo público y el mismo
   formulario, hizo 4 leads a USD 3,25 (13,3 % de los clics). Se pausan los
   dos anuncios; la gráfica y el motion siguen.
2. El conjunto Montero sumó USD 19 y 1 lead, mientras la agencia sacó 10 leads
   de Montero a USD 1,73 en los mismos días. Se pausa (no se borra) y sus
   USD 8/día pasan a L200: la campaña sigue en USD 20/día.
3. Los conjuntos L200 de la agencia apuntan solo a públicos calientes
   (seguidores FB y FB General 365, sin Advantage+) y el nuestro se los
   sugería a Meta como prioridad: los dos pujaban por la misma gente dentro de
   la misma cuenta. L200 en toda la cuenta pasó de CPL 3,19 (14-20/09) a 10,98
   (21-23/09). El conjunto L200 IA queda como prospección pura: salen de las
   sugerencias los públicos calientes y se excluyen los que usa la agencia en
   L200 y Montero. Quedan como sugerencia los similares propios de L200 y los
   intereses.

Targeting y presupuesto van en una sola edición para que el aprendizaje se
reinicie una sola vez. El targeting anterior queda guardado en el estado para
poder volver atrás.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

TOKEN = os.environ["META_ADS_ACCESS_TOKEN"]
API = "https://graph.facebook.com/v21.0"

ADSET_L200 = "120252656564300663"
ADSET_MONTERO = "120252656568820663"
AD_L200_RMK = "120252657586430663"
AD_MONTERO_RMK = "120252657593820663"

PRESUPUESTO_L200 = 2000  # centavos: USD 12 + los USD 8 de Montero

STATE = os.path.join(ROOT, "output", "pauta_mmc_ia_2026-09.json")

# Sugerencias que quedan: similares de gente que ya pidió o miró L200 y de las
# cuentas de FB/IG. Sale el similar de "RMK WEB | Contact", que la agencia usa
# en Destinator.
SUGERENCIAS = [
    {"id": "120249166997270663", "name": "Público similar (1%) - RMK IG | General (365)"},
    {"id": "120249167148430663", "name": "Público similar (1%) - RMK FB | General (365)"},
    {"id": "120252450671720663", "name": "Público similar (5%) - RMK FORM | L200 | Abrió y no envió | 90 días"},
    {"id": "120252450739670663", "name": "Público similar (5%) - LEAD FORM | L200 | Enviado | 90 días"},
]

# Públicos calientes que la agencia ya paga en sus conjuntos de L200 y Montero,
# más quienes ya enviaron el formulario L200.
EXCLUIDOS = [
    {"id": "120252450736180663", "name": "LEAD FORM | L200 | Enviado | 90 días"},
    {"id": "120249166803880663", "name": "RMK FB | Seguidores actuales"},
    {"id": "120249167131890663", "name": "RMK FB | General (365)"},
    {"id": "120249164517200663", "name": "RMK WEB | Todos los visitantes del sitio web (180)"},
    {"id": "120249166991780663", "name": "RMK IG | General (365)"},
    {"id": "120252450668550663", "name": "RMK FORM | L200 | Abrió y no envió | 90 días"},
    {"id": "120252450678590663", "name": "RMK FORM | Montero | Abrió y no envió | 90 días"},
]


def call(path, params=None, post=False, intentos=6):
    params = dict(params or {})
    params["access_token"] = TOKEN
    url = f"{API}/{path}"
    for intento in range(intentos):
        try:
            if post:
                data = urllib.parse.urlencode(params).encode()
                return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data)))
            return json.load(urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params)))
        except urllib.error.HTTPError as exc:
            cuerpo = exc.read().decode()
            codigo = json.loads(cuerpo).get("error", {}).get("code") if cuerpo.startswith("{") else None
            # 17 = límite de la cuenta, 613 = una edición de conjunto cada ~30 s
            if codigo in (17, 613) and intento < intentos - 1:
                espera = 45 * (intento + 1)
                print(f"     límite de Meta ({codigo}), reintento en {espera} s")
                time.sleep(espera)
                continue
            raise SystemExit(f"ERROR {path}: {cuerpo[:600]}")


def main():
    antes = call(ADSET_L200, {"fields": "targeting,daily_budget"})

    for ad in (AD_L200_RMK, AD_MONTERO_RMK):
        call(ad, {"status": "PAUSED"}, post=True)
    print("1/3  anuncios de remarketing pausados:", AD_L200_RMK, AD_MONTERO_RMK)

    call(ADSET_MONTERO, {"status": "PAUSED"}, post=True)
    print("2/3  conjunto Montero pausado:", ADSET_MONTERO)
    time.sleep(35)

    nuevo = dict(antes["targeting"])
    nuevo["custom_audiences"] = SUGERENCIAS
    nuevo["excluded_custom_audiences"] = EXCLUIDOS
    # Advantage+ con públicos personalizados: sin esto Meta rechaza la edición (1359202)
    nuevo["targeting_relaxation_types"] = {"lookalike": 1, "custom_audience": 1}
    call(ADSET_L200, {"targeting": json.dumps(nuevo, ensure_ascii=False),
                      "daily_budget": PRESUPUESTO_L200}, post=True)
    print(f"3/3  L200 en prospección: {len(SUGERENCIAS)} similares sugeridos, "
          f"{len(EXCLUIDOS)} públicos excluidos, USD {PRESUPUESTO_L200 / 100:.0f}/día")

    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            estado = json.load(fh)
        estado["optimizacion_2026-09-23"] = {
            "motivo": "CPL 8.33 vs 2.34 L200 / 2.68 Montero de la cuenta; remarketing 49 % del gasto "
                      "con 1 lead; superposición con los conjuntos L200 de la agencia",
            "cambios": ["pausados anuncios remarketing L200 y Montero",
                        "pausado conjunto Montero, sus USD 8/día pasan a L200",
                        "L200 prospección pura: sin públicos calientes, excluidos los de la agencia"],
            "antes_L200": antes,
        }
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(estado, fh, ensure_ascii=False, indent=1)
        print("     estado guardado en", os.path.relpath(STATE, ROOT))


if __name__ == "__main__":
    main()
