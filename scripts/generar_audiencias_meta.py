#!/usr/bin/env python3
"""
Genera las semillas de Custom Audiences de Meta desde la base real de ventas
(ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx).

Pipeline acordado: normalizar -> hash SHA-256 -> CSV por marca.
Los CSV resultantes se suben a mano (o via API) a las cuentas madre de cada
marca para crear las Custom Audiences y de ahí los lookalikes PY.

Formatos de hash exigidos por Meta:
- email: minúsculas, sin espacios alrededor, SHA-256 hex.
- teléfono: solo dígitos con código de país (PY = 595), SHA-256 hex.

Salida: output/audiencias_meta/<MARCA>/emails.csv + phones.csv + resumen.md
"""
import hashlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import openpyxl

PROJECT_DIR = Path("/home/croman/Escritorio/BUYER PERSONA")
XLSX = PROJECT_DIR / "data" / "fuentes" / "ventas_unificadas.xlsx"   # ventas unificadas 2018→hoy
OUT_DIR = PROJECT_DIR / "output" / "audiencias_meta"
RESUMEN = PROJECT_DIR / "output" / "personas" / "Audiencias" / "📊 Semillas Custom Audiences - Ventas Reales.md"

# Normalización de nombres de marca del ERP -> nombre de cuenta/carpeta
MARCA_MAP = {
    "JETOUR": "Jetour",
    "GREATWALL": "GWM",
    "RENAULT": "Renault",
    "MITSUBISHI": "Mitsubishi",
    "JAC": "JAC",
    "SOUEAST": "Soueast",
    "LEAPMOTOR": "Leapmotor",
    "JMEV": "JMEV",
    "ZEEKR": "Zeekr",
}
# Sin cuenta madre propia en el sistema actual: quedan fuera del split principal
# pero se guardan en OTROS por si hacen falta.
SIN_CUENTA = {"JMC", "KARRY"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def norm_email(raw) -> str | None:
    if raw is None:
        return None
    e = unicodedata.normalize("NFKC", str(raw)).strip().lower()
    return e if EMAIL_RE.match(e) else None


def norm_phone_py(raw) -> str | None:
    """Primer teléfono antes de '//'. Devuelve dígitos con 595 adelante."""
    if raw is None:
        return None
    primero = str(raw).split("//")[0]
    digits = re.sub(r"\D", "", primero)
    if len(digits) == 11 and digits.startswith("595"):
        return digits
    if len(digits) == 10 and digits.startswith("0"):   # móvil 09XXXXXXXX
        return "595" + digits[1:]
    if len(digits) == 9 and digits.startswith("0"):    # fijo corto 02X XXXXXX
        return "595" + digits[1:]
    return None


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb["Datos"]

    # marca -> sets deduplicados
    emails_por_marca: dict[str, set] = defaultdict(set)
    phones_por_marca: dict[str, set] = defaultdict(set)
    filas_leidas = 0
    filas_utiles = 0

    # Índices por nombre de columna (fila 3 = encabezado), no fijos: el
    # archivo unificado no tiene exactamente las mismas columnas que el ERP.
    header = [str(c).strip() if c is not None else "" for c in next(ws.iter_rows(min_row=3, max_row=3, values_only=True))]
    i_marca, i_mail, i_tel = header.index("Marca"), header.index("E-Mail"), header.index("Teléfonos")
    for row in ws.iter_rows(min_row=4, values_only=True):
        if not any(v is not None and str(v).strip() for v in row):
            continue
        filas_leidas += 1
        marca_raw = str(row[i_marca]).strip().upper() if row[i_marca] else ""
        if not marca_raw:
            continue
        marca = MARCA_MAP.get(marca_raw, "OTROS")
        filas_utiles += 1
        e = norm_email(row[i_mail])
        p = norm_phone_py(row[i_tel])
        if e:
            emails_por_marca[marca].add(e)
        if p:
            phones_por_marca[marca].add(p)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESUMEN.parent.mkdir(parents=True, exist_ok=True)

    lineas_md = [
        "# 📊 Semillas Custom Audiences — Ventas Reales",
        "",
        f"> Generado automáticamente desde `ENCUESTA AGESTA/FacturacionUnidades-7343.xlsx` "
        f"(hoja Datos, {filas_leidas} filas con datos).",
        ">",
        "> Pipeline: normalización → dedup → hash **SHA-256** → CSV en `output/audiencias_meta/<Marca>/`.",
        "> Los CSV se suben a la **cuenta madre** de cada marca como Custom Audience "
        "(fuente: datos propios, sin PII visible) y de ahí salen los **lookalikes PY**.",
        "",
        "| Marca | Emails únicos | Teléfonos únicos | Carpeta |",
        "|---|---|---|---|",
    ]

    marcas_ordenadas = sorted(
        [m for m in set(list(emails_por_marca) + list(phones_por_marca)) if m != "OTROS"],
        key=lambda m: -len(emails_por_marca[m] | phones_por_marca[m]),
    )

    total_e = total_p = 0
    for marca in marcas_ordenadas:
        es = sorted(emails_por_marca.get(marca, set()))
        ps = sorted(phones_por_marca.get(marca, set()))
        total_e += len(es)
        total_p += len(ps)
        carpeta = OUT_DIR / marca
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "emails.csv").write_text(
            "email_sha256\n" + "\n".join(sha(e) for e in es) + "\n", encoding="utf-8"
        )
        (carpeta / "phones.csv").write_text(
            "phone_sha256\n" + "\n".join(sha(p) for p in ps) + "\n", encoding="utf-8"
        )
        lineas_md.append(f"| {marca} | {len(es)} | {len(ps)} | `output/audiencias_meta/{marca}/` |")

    # Combinada EV (plan acordado: Zeekr+Leapmotor juntas por volumen bajo)
    ev_emails = sorted(emails_por_marca.get("Zeekr", set()) | emails_por_marca.get("Leapmotor", set()))
    ev_phones = sorted(phones_por_marca.get("Zeekr", set()) | phones_por_marca.get("Leapmotor", set()))
    if ev_emails or ev_phones:
        carpeta = OUT_DIR / "ZEEKR_LEAPMOTOR_EV"
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "emails.csv").write_text(
            "email_sha256\n" + "\n".join(sha(e) for e in ev_emails) + "\n", encoding="utf-8"
        )
        (carpeta / "phones.csv").write_text(
            "phone_sha256\n" + "\n".join(sha(p) for p in ev_phones) + "\n", encoding="utf-8"
        )
        lineas_md.append(
            f"| Zeekr + Leapmotor (EV combinada) | {len(ev_emails)} | {len(ev_phones)} | `output/audiencias_meta/ZEEKR_LEAPMOTOR_EV/` |"
        )

    otros_e = len(emails_por_marca.get("OTROS", set()))
    otros_p = len(phones_por_marca.get("OTROS", set()))
    if otros_e or otros_p:
        lineas_md.append(f"| Otros (JMC/Karry/sin marca) | {otros_e} | {otros_p} | — |")

    lineas_md += [
        "",
        f"**Total semillas:** {total_e} emails + {total_p} teléfonos únicos con hash.",
        "",
        "## Cómo subir cada lista a Meta",
        "1. Ads Manager → *Audiences* → *Create a Custom Audience* → *Customer list*.",
        "2. Elegir *Upload customers manually*, marcar que los identificadores ya vienen hasheados con SHA-256.",
        "3. Subir `emails.csv` (columna `email_sha256`) y repetir con `phones.csv` (columna `phone_sha256`).",
        "4. Nombrar la audiencia `VENTAS REALES <MARCA> — base`.",
        "5. Una vez madurada (~500+ personas), crear Lookalike origen esa audiencia, país Paraguay, 1%.",
        "",
        "## Notas",
        "- Un mismo cliente aparece en varias marcas si compró más de una vez: correcto, cada cuenta usa su propia semilla.",
        "- `GREATWALL` del ERP se mapea a **GWM**.",
        "- Zeekr y Leapmotor van combinadas porque por separado quedan debajo del mínimo útil de Meta (~100 matching).",
        "- ⚠️ Uso interno: los CSV tienen PII hasheada, no commitear a ningún repo público.",
        "",
        "## ⚠️ Mitsubishi: data de contacto inservible",
        "Las 525 ventas de Mitsubishi en el ERP están cargadas con el email y teléfono "
        "**corporativos de Nipon** (`impor@nipon.com.py` / `021505511`) — 524 de 525 filas. "
        "Es decir, quien cargó esas ventas puso el contacto del importador competidor, no del "
        "cliente real. **No subir esa lista a Meta**: contaminaría la semilla con datos del "
        "competidor y además no representa compradores propios. Pendiente de negocio: recuperar "
        "los contactos reales de los compradores Mitsubishi desde Bitrix u otra fuente.",
    ]
    RESUMEN.write_text("\n".join(lineas_md) + "\n", encoding="utf-8")

    print(f"Filas leídas: {filas_leidas}")
    print(f"Semillas totales: {total_e} emails, {total_p} teléfonos")
    for l in lineas_md[6:17]:
        if l.startswith("|"):
            print(l)


if __name__ == "__main__":
    main()
