"""
Exportador a Obsidian.

Genera notas Markdown compatibles con Obsidian:
- Frontmatter YAML con metadatos estructurados
- Tags de Obsidian
- Wikilinks ``[[nota]]`` entre personas y productos
- Callouts (bloques de nota) para dolores, objetivos y motivaciones
- Archivo índice MOC (Map of Content)

Las notas se guardan en ``output/personas/`` y, opcionalmente, se copian
al vault de Obsidian si está configurado.
"""

from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from src.generators.centro_de_compra import LECTURA_GENERO as LECTURA

logger = logging.getLogger(__name__)


class ObsidianExporter:
    """Exporta Buyer Personas a notas Markdown para Obsidian."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        # Se completan en export_all: marca -> nombre de su persona, y
        # marca -> personas de sus modelos (para linkear en ambos sentidos)
        self._brand_persona_names: dict[str, str] = {}
        self._models_by_brand: dict[str, list[str]] = {}
        # True cuando el histórico de ventas sigue siendo el CSV de ejemplo
        self.sales_is_sample = bool(config.get("sales_is_sample", False))
        self.output_dir = Path(config.get("output_dir", "output/personas"))
        self.use_frontmatter = config.get("use_frontmatter", True)
        self.default_tags = config.get("default_tags", ["buyer-persona", "marketing"])
        self.create_index = config.get("create_index", True)
        self.index_filename = config.get("index_filename", "Buyer Personas MOC.md")
        # Centro de compra (quién mira / quién decide): lo carga main antes de
        # export_all para que fichas e índices lo muestren
        self.centro: dict[str, Any] = {}

    # Nota del centro de compra de cada marca (vive en la carpeta de la marca,
    # así la ve el usuario de esa marca en el cerebro)
    CENTRO_PREFIJO = "👥 Quién mira y quién decide — "
    CENTRO_HUB = "👥 Centro de compra — todas las marcas"

    @classmethod
    def centro_nota(cls, brand: str) -> str:
        return f"{cls.CENTRO_PREFIJO}{cls._sanitize_filename(brand)}"

    def export_all(self, personas: list[dict[str, Any]]) -> list[Path]:
        """
        Exporta todas las personas a archivos Markdown.

        Returns:
            Lista de rutas a los archivos generados.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Índices para interconectar marca <-> modelos
        self._brand_persona_names = {
            p["segment"]["name"]: p.get("name", "")
            for p in personas
            if p.get("segment", {}).get("type") == "brand" and p["segment"].get("name")
        }
        self._models_by_brand = {}
        for p in personas:
            seg = p.get("segment", {})
            if seg.get("type") == "model" and seg.get("brand"):
                self._models_by_brand.setdefault(seg["brand"], []).append(p.get("name", ""))

        generated_files: list[Path] = []

        # Exportar cada persona (en la carpeta de su marca)
        for persona in personas:
            file_path = self._export_persona(persona)
            generated_files.append(file_path)

        # Un índice por marca (Comprador + modelos + marketing + audiencias)
        for brand in sorted(self._brands_of(personas)):
            generated_files.append(self._create_brand_index(brand, personas))

        # Crear índice MOC general agrupado por marca
        if self.create_index:
            index_path = self._create_index(personas)
            generated_files.append(index_path)

        # Copiar al vault de Obsidian si está configurado
        vault_path = self.config.get("obsidian_vault", "")
        if vault_path:
            self._copy_to_vault(generated_files, Path(vault_path))

        return generated_files

    # ------------------------------------------------------------------
    # Exportación individual
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Agrupación por marca
    # ------------------------------------------------------------------

    @staticmethod
    def persona_subdir(persona: dict[str, Any]) -> str:
        """
        Carpeta (relativa a "Buyer Personas") donde vive la persona:
        la marca para personas de marca y de modelo, "Segmentos" para los
        tipos de vehículo. Así el vault se lee Marca → modelos, como pidió
        marketing, en vez de una lista plana de 70+ notas.
        """
        seg = persona.get("segment", {}) or {}
        t = seg.get("type", "")
        if t == "brand" and seg.get("name"):
            return ObsidianExporter._sanitize_filename(seg["name"])
        if t == "model" and seg.get("brand"):
            return ObsidianExporter._sanitize_filename(seg["brand"])
        if t == "product_category":
            return "Segmentos"
        return "Otros"

    @staticmethod
    def _brands_of(personas: list[dict[str, Any]]) -> set[str]:
        out: set[str] = set()
        for p in personas:
            seg = p.get("segment", {}) or {}
            if seg.get("type") == "brand" and seg.get("name"):
                out.add(seg["name"])
            elif seg.get("type") == "model" and seg.get("brand"):
                out.add(seg["brand"])
        return out

    def _export_persona(self, persona: dict[str, Any]) -> Path:
        """Genera el archivo Markdown para una persona."""
        safe_name = self._sanitize_filename(persona.get("name", persona.get("id", "persona")))
        filename = f"{safe_name}.md"
        file_path = self.output_dir / self.persona_subdir(persona) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._render_persona_markdown(persona)

        file_path.write_text(content, encoding="utf-8")
        logger.info("Persona exportada: %s", file_path.name)
        return file_path

    def _render_persona_markdown(self, persona: dict[str, Any]) -> str:
        """Renderiza el contenido Markdown completo de una persona."""
        sections: list[str] = []

        # Frontmatter
        if self.use_frontmatter:
            sections.append(self._render_frontmatter(persona))

        # Título
        sections.append(f"# {persona.get('name', persona.get('id', 'Buyer Persona'))}\n")

        # Cómo leer la ficha (plegado): responde de una vez las preguntas que
        # se repiten en cada reunión — qué es, de dónde sale, por qué no coinciden.
        sections.append(self._render_how_to_read(persona))

        # Resumen rápido
        sections.append(self._render_summary(persona))

        # Quién mira y quién decide (centro de compra): arriba, para que se vea
        bloque = self._render_centro_block(persona)
        if bloque:
            sections.append(bloque)

        # Demografía
        sections.append(self._render_demographics(persona))

        # Intereses
        sections.append(self._render_interests(persona))

        # Comportamiento de compra
        sections.append(self._render_purchase(persona))

        # Dolores
        sections.append(self._render_pains(persona))

        # Objetivos
        sections.append(self._render_goals(persona))

        # Motivaciones
        sections.append(self._render_motivations(persona))

        # Estrategia recomendada
        sections.append(self._render_strategy(persona))

        # Modelos de esta marca (solo en personas de marca)
        segment = persona.get("segment", {})
        if segment.get("type") == "brand":
            models = self._models_by_brand.get(segment.get("name", ""), [])
            if models:
                lines = [f"## 🚗 Modelos de {segment['name']}\n"]
                lines.extend(f"- [[{m}]]" for m in models)
                sections.append("\n".join(lines) + "\n")

        # Leads reales (agregado, sin datos personales)
        if persona.get("real_leads"):
            sections.append(self._render_real_leads(persona))

        # Embudo CRM Bitrix (agregado por marca)
        if persona.get("crm"):
            sections.append(self._render_crm(persona))

        # Precio de lista y competencia directa (Datacar, uso interno)
        if persona.get("competitors"):
            sections.append(self._render_competitors(persona))

        # Stock, oferta vigente, objetivos y negociación (Excel del negocio)
        if persona.get("extras"):
            sections.append(self._render_extras(persona))

        # Fuentes de datos
        sections.append(self._render_sources(persona))

        # Metadata de generación
        sections.append(f"\n---\n*Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Secciones del Markdown
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Centro de compra: quién mira, quién da el paso, quién paga
    # ------------------------------------------------------------------

    @staticmethod
    def _x(v: Any) -> str:
        """0.87 → '0,87×'."""
        return f"{v:.2f}×".replace(".", ",") if isinstance(v, (int, float)) else "—"

    @staticmethod
    def _miles(n: Any) -> str:
        return f"{int(n):,}".replace(",", ".") if isinstance(n, (int, float)) else "—"

    @staticmethod
    def _pct(v: Any) -> str:
        return f"{v:.1f} %".replace(".", ",") if isinstance(v, (int, float)) else "—"

    def _frase_genero(self, e: dict[str, Any]) -> str:
        """Una línea en castellano llano sobre ellas y ellos."""
        l = e.get("lectura")
        base = f"ellas son el {self._pct(e.get('mujeres_clics_pct'))} de los clics"
        if l == "ella_mira":
            return (f"{base} pero, viendo el mismo anuncio, contactan {self._x(e['ellas_vs_ellos'])} lo que ellos "
                    f"(menos en {e['conjuntos_ellas_menos']} de {e['conjuntos']} conjuntos): **ella investiga y él da el paso**")
        if l == "tendencia":
            return (f"{base}; con el mismo anuncio contactan {self._x(e['ellas_vs_ellos'])} lo que ellos, "
                    f"pero con {e['conjuntos']} conjuntos todavía es una tendencia")
        if l == "ellas_avanzan":
            return (f"{base} y las que miran **contactan más** que ellos con el mismo anuncio "
                    f"({self._x(e['ellas_vs_ellos'])})")
        if l == "parejo":
            return f"{base} y contactan igual que ellos con el mismo anuncio ({self._x(e['ellas_vs_ellos'])})"
        return base

    def _render_centro_block(self, persona: dict[str, Any]) -> str:
        seg = persona.get("segment", {}) or {}
        tipo = seg.get("type")
        if tipo not in ("brand", "model") or not self.centro:
            return ""
        marca = seg.get("name") if tipo == "brand" else seg.get("brand")
        m = (self.centro.get("marcas") or {}).get(marca)
        if not m:
            return ""
        nota = self.centro_nota(marca)
        lines = ["## 👥 Quién mira y quién decide\n"]
        if tipo == "brand":
            e = m.get("embudo") or {}
            emp = m.get("empresa") or {}
            if e:
                lines.append(f"- **Meta:** {self._frase_genero(e)}.")
            if emp:
                lines.append(f"- **Quién paga (ERP, 12 meses):** el {self._pct(emp.get('empresa_pct'))} de las compras "
                             f"a cliente final las factura una empresa.")
            recs = m.get("meta_ads") or []
            if recs:
                lines.append("- **Para Meta Ads:** " + " · ".join(r["titulo"] for r in recs) + ".")
        else:
            modelo = seg.get("name", "")
            mod = (m.get("modelos") or {}).get(modelo) or {}
            temas = (m.get("temas") or {}).get(modelo) or []
            e = mod.get("embudo")
            if e:
                lines.append(f"- **Meta:** {self._frase_genero(e)}.")
            fav = [t for t in temas if t["dif_mujeres_pp"] >= 4]
            if fav:
                t = fav[0]
                lines.append(f"- **Lo que más las atrae:** anuncios de *{t['tema'].lower()}* "
                             f"({self._pct(t['mujeres_pct'])} de mujeres contra {self._pct(t['mujeres_modelo_pct'])} del modelo).")
            may = [t for t in temas if t["dif_55_pp"] >= 6]
            if may:
                t = max(may, key=lambda x: x["dif_55_pp"])
                lines.append(f"- **Lo que más atrae a los mayores de 55:** *{t['tema'].lower()}* "
                             f"({self._pct(t['mayores55_pct'])} contra {self._pct(t['mayores55_modelo_pct'])} del modelo).")
            emp = mod.get("empresa")
            if emp:
                lines.append(f"- **Quién paga (ERP, 12 meses):** el {self._pct(emp['empresa_pct'])} de sus "
                             f"{emp['ventas']} ventas a cliente final las facturó una empresa.")
            if len(lines) == 1:
                lines.append("- Todavía sin datos suficientes de este modelo: ver la nota de la marca.")
        lines.append(f"\n→ Detalle, cómo leerlo y qué hacer en Meta Ads: [[{nota}]]\n")
        return "\n".join(lines)

    def export_centro_de_compra(self, personas: list[dict[str, Any]]) -> list[Path]:
        """Una nota por marca con todo el centro de compra y cómo usarlo en Meta Ads."""
        if not self.centro:
            return []
        marcas_persona = self._brands_of(personas)
        files: list[Path] = []
        for marca, m in sorted((self.centro.get("marcas") or {}).items()):
            if marca not in marcas_persona:
                continue
            path = self.output_dir / self._sanitize_filename(marca) / f"{self.centro_nota(marca)}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self._render_centro_marca(marca, m), encoding="utf-8")
            files.append(path)
        # Marcas que ya no tienen datos: su nota vieja se va
        vivas = {p.name for p in files}
        for vieja in self.output_dir.glob(f"*/{self.CENTRO_PREFIJO}*.md"):
            if vieja.name not in vivas:
                vieja.unlink()
        vault = self.config.get("obsidian_vault", "")
        if vault:
            self._copy_to_vault(files, Path(vault))
            for vieja in (Path(vault) / "Buyer Personas").glob(f"*/{self.CENTRO_PREFIJO}*.md"):
                if vieja.name not in vivas:
                    vieja.unlink()
        logger.info("Centro de compra: %d notas de marca", len(files))
        return files

    def _render_centro_marca(self, marca: str, m: dict[str, Any]) -> str:
        per = self.centro.get("periodo_meta") or {}
        e = m.get("embudo") or {}
        emp = m.get("empresa") or {}
        conv = m.get("conversaciones") or {}
        recs = m.get("meta_ads") or []
        hoy = datetime.now()
        L: list[str] = [
            "---",
            "type: centro-de-compra",
            f"marca: {marca}",
            f"periodo_meta: {per.get('start', '')} a {per.get('end', '')}",
            f"created: {hoy.strftime('%Y-%m-%d')}",
            f"tags:\n  - centro-de-compra\n  - meta-ads\n  - marca/{self._sanitize_tag(marca)}",
            "---\n",
            f"# 👥 Quién mira y quién decide — {marca}\n",
        ]
        # --- En una línea ---
        frases = []
        if e:
            frases.append(f"En Meta, {self._frase_genero(e)}.")
        if emp:
            frases.append(f"El {self._pct(emp.get('empresa_pct'))} de las compras a cliente final las factura una empresa.")
        if conv.get("con_texto_del_cliente", 0) >= 100:
            frases.append(f"En el {self._pct(conv.get('con_otra_persona_pct'))} de los chats el cliente nombra a otra persona.")
        L += ["> [!summary] En una línea", "> " + " ".join(frases or ["Todavía sin datos suficientes."]), ""]
        # --- Qué hacer en Meta (resumen visible arriba) ---
        if recs:
            L.append("> [!tip] 🎯 Qué hacer en Meta Ads")
            for i, r in enumerate(recs, 1):
                L.append(f"> {i}. **{r['titulo']}** — «{r['pieza_titulo']}». Detalle en la sección 5.")
            L.append("")
        # --- Cómo leer ---
        L += [
            "> [!question]- Cómo leer esta nota (abrir)",
            "> - **El Buyer Persona describe a quien compra. Esta nota agrega a los otros papeles**: quien investiga o influye, quien da el paso (deja el contacto) y quien paga.",
            "> - **Clic** = tocó el anuncio. **Contacto** = envió el formulario o empezó un chat de WhatsApp, Messenger o Instagram.",
            "> - **«Ellas vs. ellos con el mismo anuncio»**: dentro de cada conjunto de anuncios (mismo aviso, mismo botón) se compara qué tanto contactan las mujeres que hicieron clic contra los hombres, y se suman todos los conjuntos. **1,00×** = igual; **0,87×** = ellas contactan 13 % menos; **1,20×** = 20 % más. Se compara dentro del conjunto porque Meta no le muestra lo mismo a todos: sin ese control, una campaña sin formulario hace parecer que un grupo «no convierte».",
            "> - **«Ellas menos en X de Y conjuntos»** dice qué tan pareja es la señal: si pasa en casi todos los conjuntos, no es casualidad.",
            "> - **Temas**: cada anuncio se clasifica por lo que dice (prueba de manejo, seguridad, cuotas…) y se mira qué parte de sus clics viene de mujeres o de mayores de 55, **contra el promedio del mismo modelo**. Solo se muestran temas con 3 anuncios o más y sin uno que se lleve más de la mitad de los clics.",
            "> - **Qué NO dice**: Meta no sabe quién decidió la compra. Una mujer que hace clic y no contacta puede ser la esposa investigando o alguien con menos interés. Es una **señal**, que se confirma con las compras de empresa (ERP) y con los chats.",
            "",
        ]
        # --- 1. Quién mira y quién da el paso ---
        L.append("## 1. ¿Quién mira y quién da el paso?\n")
        if e:
            L += [
                f"Meta del **{per.get('start', '')}** al **{per.get('end', '')}**. Se excluyen los conjuntos apuntados a un solo género.\n",
                "| | Mujeres en los clics | Mujeres en los contactos | Ellas vs. ellos, mismo anuncio | Conjuntos comparados | Lectura |",
                "|---|---|---|---|---|---|",
                f"| **{marca}** | {self._pct(e['mujeres_clics_pct'])} | {self._pct(e['mujeres_contactos_pct'])} | "
                f"**{self._x(e['ellas_vs_ellos'])}** | {e['conjuntos']} (ellas menos en {e['conjuntos_ellas_menos']}) | "
                f"{LECTURA.get(e.get('lectura'), '—')} |",
            ]
            for modelo, mm in sorted((m.get("modelos") or {}).items(), key=lambda x: -((x[1].get("embudo") or {}).get("contactos") or 0)):
                me = mm.get("embudo")
                if not me or not me.get("conjuntos"):
                    continue
                L.append(f"| [[{self._sanitize_filename(modelo)}|{modelo}]] | {self._pct(me['mujeres_clics_pct'])} | "
                         f"{self._pct(me['mujeres_contactos_pct'])} | {self._x(me['ellas_vs_ellos'])} | {me['conjuntos']} "
                         f"(ellas menos en {me['conjuntos_ellas_menos']}) | {LECTURA.get(me.get('lectura'), '—')} |")
            L.append("")
            tasas = e.get("tasa_por_edad") or {}
            if tasas:
                L += ["**Por edad** — de cada 100 clics, cuántos terminan en contacto:\n",
                      "| " + " | ".join(tasas) + " |", "|" + "---|" * len(tasas),
                      "| " + " | ".join(self._pct(v) for v in tasas.values()) + " |", ""]
                r55 = e.get("mayores55_vs_resto")
                if isinstance(r55, (int, float)):
                    if r55 < 0.8:
                        L.append(f"Los **mayores de 55** hacen clic pero, con el mismo anuncio, contactan {self._x(r55)} lo que los menores de 55: "
                                 "miran mucho y el contacto suele dejarlo alguien más joven (o no lo deja). Pieza sugerida: invitarlos a probarla con quien los acompaña.\n")
                    elif r55 > 1.2:
                        L.append(f"Los **mayores de 55** que hacen clic contactan {self._x(r55)} lo que los menores de 55: cuando miran, avanzan.\n")
                    else:
                        L.append(f"Los mayores de 55 contactan parecido al resto con el mismo anuncio ({self._x(r55)}).\n")
        else:
            L.append("_Sin contactos suficientes en Meta para comparar (mínimo 150 en la ventana)._\n")
        # --- 2. Qué le interesa a cada uno ---
        L.append("## 2. ¿Qué le interesa a cada uno?\n")
        temas = m.get("temas") or {}
        if temas:
            def pp(v: float) -> str:
                return f"{v:+.1f}".replace(".", ",")
            todas = [(mod, t) for mod, ts in temas.items() for t in ts]
            ellas = sorted((x for x in todas if x[1]["dif_mujeres_pp"] >= 4), key=lambda x: -x[1]["dif_mujeres_pp"])
            mayores = sorted((x for x in todas if x[1]["dif_55_pp"] >= 6), key=lambda x: -x[1]["dif_55_pp"])
            menos = sorted((x for x in todas if x[1]["dif_mujeres_pp"] <= -4), key=lambda x: x[1]["dif_mujeres_pp"])
            L.append("Cada tema se compara con el **promedio del mismo modelo**: «+10» = ese tema suma 10 puntos de mujeres "
                     "(o de mayores de 55) sobre lo normal del modelo. Clics y cantidad de anuncios entre paréntesis.\n")
            if ellas:
                L += ["**Lo que más atrae a las mujeres** → el tema para la pieza de quien acompaña:\n",
                      "| Modelo | Tema del anuncio | Mujeres en los clics | Sobre el modelo | Clics (anuncios) |",
                      "|---|---|---|---|---|"]
                L += [f"| {mod} | {t['tema']} | {self._pct(t['mujeres_pct'])} | {pp(t['dif_mujeres_pp'])} | "
                      f"{self._miles(t['clics'])} ({t['anuncios']}) |" for mod, t in ellas]
                L.append("")
            if mayores:
                L += ["**Lo que más atrae a los mayores de 55:**\n",
                      "| Modelo | Tema del anuncio | 55+ en los clics | Sobre el modelo | Clics (anuncios) |",
                      "|---|---|---|---|---|"]
                L += [f"| {mod} | {t['tema']} | {self._pct(t['mayores55_pct'])} | {pp(t['dif_55_pp'])} | "
                      f"{self._miles(t['clics'])} ({t['anuncios']}) |" for mod, t in mayores]
                L.append("")
            if menos:
                L.append("**Lo que menos las atrae** (evitarlo en la pieza para ellas): " + "; ".join(
                    f"{mod}: {t['tema'].lower()} ({pp(t['dif_mujeres_pp'])})" for mod, t in menos[:6]) + ".\n")
        else:
            L.append("_Ningún tema se aparta lo suficiente del promedio con anuncios variados._\n")
        # --- 3. Quién paga ---
        L.append("## 3. ¿Quién paga? Empresa o persona\n")
        if emp:
            L += [f"ERP, ventas a **cliente final** del {emp.get('desde')} al {emp.get('hasta')} "
                  "(sin ventas a subconcesionarios ni a otras concesionarias que revenden). "
                  "Se detecta la razón social (S.A., S.R.L., cooperativa, ministerio…); el nombre del cliente no se guarda.\n",
                  f"- **{marca}:** {self._pct(emp.get('empresa_pct'))} de {emp.get('ventas')} ventas facturadas a una empresa.", ""]
            mods = [x for x in emp.get("modelos") or [] if x.get("ventas", 0) >= 25]
            if mods:
                L += ["| Modelo | Ventas 12 meses | Factura una empresa |", "|---|---|---|"]
                L += [f"| {x['modelo']} | {x['ventas']} | {self._pct(x['empresa_pct'])} |" for x in mods]
                L.append("")
            L.append("Cuando compra una empresa hay un **comité**: decide el dueño o un gerente, paga la empresa y maneja otro. "
                     "El mensaje de la persona (familia, estilo) no le habla a quien firma.\n")
        else:
            L.append("_Sin ventas suficientes a cliente final en el ERP._\n")
        # --- 4. Conversaciones ---
        L.append("## 4. ¿Quién más aparece en las conversaciones?\n")
        if conv.get("con_texto_del_cliente", 0) >= 30:
            per_c = conv.get("periodo") or {}
            L += [f"Chats de **Messenger e Instagram** de las páginas de {marca} y de sus asesores, del {per_c.get('desde')} al {per_c.get('hasta')}. "
                  "Se cuenta en cuántos el cliente nombra a otra persona; no se guarda ningún mensaje. "
                  "WhatsApp no deja leer el historial por API, así que no entra.\n",
                  f"- **{self._miles(conv['con_texto_del_cliente'])}** chats con texto del cliente · **{self._pct(conv.get('con_otra_persona_pct'))}** nombran a otra persona."]
            for k, v in (conv.get("actores") or {}).items():
                L.append(f"  - {k}: {v}")
            if conv.get("lo_consulta_con_alguien"):
                L.append(f"- Dicen que lo tienen que consultar o decidir con alguien: **{conv['lo_consulta_con_alguien']}**.")
            if conv.get("es_para_otro"):
                L.append(f"- Es para otra persona («para mi hijo», «para mi señora»…): **{conv['es_para_otro']}**.")
            L.append("\n_Es un piso: mucha gente no lo escribe. Sirve para ver **quién** aparece, más que cuántas veces._\n")
        else:
            L.append("_Sin chats suficientes en la última lectura semanal._\n")
        # --- 5. Meta Ads ---
        L.append("## 5. 🎯 Cómo usarlo en Meta Ads\n")
        if recs:
            for i, r in enumerate(recs, 1):
                L.append(f"### 5.{i} {r['titulo']}\n")
                L.append("**Por qué:** " + " ".join(r["por_que"]) + "\n")
                if r.get("modelos"):
                    L.append("**Modelos donde más pesa:** " + ", ".join(r["modelos"]) + "\n")
                L += ["**La pieza (texto base, ajustar al tono de la marca):**", "",
                      f"> **{r['pieza_titulo']}**", f"> {r['pieza_texto']}", "",
                      f"**Dónde ponerla:** {r['donde']}\n", f"**Cómo medirla:** {r['medir']}\n"]
        else:
            L.append("_Sin una señal clara que justifique una pieza distinta: seguir con la pauta actual._\n")
        L += ["> [!warning] Reglas que no cambian",
              "> - Por ley, **nunca nombrar marcas ni modelos de la competencia** en los anuncios: solo argumentos propios.",
              "> - Un cambio por vez, para saber qué movió el resultado.",
              "> - No segmentar por género o edad para «buscarla» a ella: se pierde alcance y Meta ya la encuentra si la pieza le habla.",
              ""]
        # --- Límites y fuentes ---
        L += ["## Límites\n",
              "- Meta mide clics y contactos, no quién decidió: el papel de cada uno es una **inferencia** que se refuerza cuando Meta, el ERP y los chats apuntan al mismo lado.",
              "- Un tema puede venir mezclado con el público al que se le mostró: por eso se exigen varios anuncios por tema.",
              "- Los porcentajes de empresa dependen de cómo se factura: una compra personal a nombre de la empresa cuenta como empresa (y es, de hecho, una decisión de empresa).",
              "",
              "## Fuentes y período\n",
              f"- Meta Ads: {per.get('start', '')} a {per.get('end', '')}, a nivel anuncio × edad × género, con la segmentación de cada conjunto.",
              f"- ERP: ventas a cliente final, {emp.get('desde', '—')} a {emp.get('hasta', '—')}." if emp else "- ERP: sin datos suficientes.",
              f"- Chats: Messenger e Instagram, lectura semanal ({(conv.get('periodo') or {}).get('hasta', '—')})." if conv else "- Chats: sin lectura reciente.",
              f"- Generado el {hoy.strftime('%Y-%m-%d %H:%M')} por el pipeline Buyer Persona (se actualiza solo cada mañana).",
              "",
              f"← [[{self._sanitize_filename(marca)}|Volver a {marca}]] · [[📘 Manual Buyer Persona#👥 Quién mira y quién decide|Cómo se calcula]]",
              ""]
        return "\n".join(L)

    def export_centro_hub(self, personas: list[dict[str, Any]]) -> Path | None:
        """Comparación entre marcas (uso interno: vive en Sistema/, que los brands no ven)."""
        vault = self.config.get("obsidian_vault", "")
        if not self.centro or not vault:
            return None
        marcas = {k: v for k, v in (self.centro.get("marcas") or {}).items() if k in self._brands_of(personas)}
        per = self.centro.get("periodo_meta") or {}
        L = ["---", "type: centro-de-compra-hub", f"created: {datetime.now().strftime('%Y-%m-%d')}",
             "tags:\n  - centro-de-compra\n  - meta-ads\n  - sistema", "---\n",
             f"# {self.CENTRO_HUB}\n",
             "> [!info] Uso interno",
             "> Compara todas las marcas: los usuarios de cada marca solo ven la nota de la suya en el cerebro. "
             "Cómo se calcula: [[📘 Manual Buyer Persona#👥 Quién mira y quién decide|Manual]]. "
             "Pedido de Valentina (audio del 24-09-2026): el Buyer Persona describía solo al comprador.\n",
             f"Meta del {per.get('start', '')} al {per.get('end', '')}.\n",
             "| Marca | Mujeres en clics | Ellas vs. ellos (mismo anuncio) | Lectura | 55+ vs. resto | Compra empresa | Chats con otra persona | Qué hacer en Meta |",
             "|---|---|---|---|---|---|---|---|"]
        for marca, m in sorted(marcas.items(), key=lambda x: -((x[1].get("embudo") or {}).get("contactos") or 0)):
            e, emp, conv = m.get("embudo") or {}, m.get("empresa") or {}, m.get("conversaciones") or {}
            L.append(f"| [[{self.centro_nota(marca)}|{marca}]] | {self._pct(e.get('mujeres_clics_pct'))} | "
                     f"{self._x(e.get('ellas_vs_ellos'))} ({e.get('conjuntos_ellas_menos', '—')}/{e.get('conjuntos', '—')}) | "
                     f"{LECTURA.get(e.get('lectura'), '—')} | {self._x(e.get('mayores55_vs_resto'))} | "
                     f"{self._pct(emp.get('empresa_pct'))} | {self._pct(conv.get('con_otra_persona_pct')) if conv else '—'} | "
                     f"{' · '.join(r['titulo'] for r in m.get('meta_ads', [])) or '—'} |")
        L += ["", "_(28/44) = en 28 de 44 conjuntos ellas contactaron menos que ellos._", ""]
        path = Path(vault) / "Sistema" / f"{self.CENTRO_HUB}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(L) + "\n", encoding="utf-8")
        return path

    def _render_frontmatter(self, persona: dict[str, Any]) -> str:
        """Genera el frontmatter YAML."""
        demo = persona.get("demographics", {})
        tags = list(self.default_tags)
        tags.append(persona.get("id", "").lower().replace(" ", "-"))

        # Tags adicionales basados en el segmento
        segment = persona.get("segment", {})
        seg_type = segment.get("type", "")
        seg_name = segment.get("name", "")
        if seg_type == "model":
            if segment.get("brand"):
                tags.append(f"marca/{self._sanitize_tag(segment['brand'])}")
            if seg_name:
                tags.append(f"modelo/{self._sanitize_tag(seg_name)}")
            if segment.get("category"):
                tags.append(f"segmento/{self._sanitize_tag(segment['category'])}")
        elif seg_type == "brand":
            if seg_name:
                tags.append(f"marca/{self._sanitize_tag(seg_name)}")
        else:
            if seg_type:
                tags.append(f"segmento/{seg_type}")
            if seg_name:
                tags.append(f"segmento/{self._sanitize_tag(seg_name)}")

        frontmatter = {
            "id": persona.get("id", ""),
            "name": persona.get("name", ""),
            "type": "buyer-persona",
            "age_range": demo.get("age_range", ""),
            "gender": demo.get("gender", ""),
            "locations": demo.get("location", []),
            "created": datetime.now().strftime("%Y-%m-%d"),
            "tags": tags,
        }

        # Añadir edad media si existe
        if demo.get("age_mean"):
            frontmatter["age_mean"] = demo["age_mean"]

        yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n"

    def _render_how_to_read(self, persona: dict[str, Any]) -> str:
        """Callout plegado con las reglas de lectura de la ficha."""
        per = persona.get("periods") or {}
        m = per.get("meta") or {}
        sd = per.get("sales") or {}
        bx = per.get("bitrix") or {}
        cortes = []
        if m.get("start"):
            cortes.append(f"Meta {m['start']} → {m['end']}")
        if sd.get("end"):
            cortes.append(f"ERP hasta {sd['end']}")
        if bx.get("days_back"):
            cortes.append(f"Bitrix últimos {bx['days_back']} días")
        cortes_txt = " · ".join(cortes) if cortes else "cada bloque indica su ventana"
        es_modelo = (persona.get("segment") or {}).get("type") == "model"
        quien = "este modelo" if es_modelo else "este público"
        return "\n".join([
            "> [!note]- Cómo leer esta ficha",
            f"> **Qué es:** el retrato de quién mira y quién compra {quien}, armado solo con datos propios: "
            "los anuncios de Meta (clics por edad y género, temas, respuestas de formulario), las ventas del ERP "
            "y el embudo del CRM Bitrix. Se rehace sola todas las mañanas a las 06:00.",
            f"> **Ventanas de cada fuente:** {cortes_txt}. Si dos números no coinciden, casi siempre es porque vienen "
            "de fuentes con cortes distintos; cada bloque dice de cuál sale.",
            "> **Edad y género son de quién hace clic en los anuncios**, no de quién firmó la compra: el ERP no guarda "
            "edad ni género. Ubicación en el ERP = sucursal donde se vendió.",
            "> **Lo que dice «estimado»** (nivel socioeconómico) es un cálculo nuestro para orientar la pauta, no un dato "
            "declarado por el cliente.",
            "> **Uso interno:** los bloques marcados así traen precios de la competencia, stock y objetivos. No van a "
            "copies públicos (ley de publicidad comparativa).",
            "> Glosario y detalle de cada bloque: [[📘 Manual Buyer Persona]], sección 3.",
            "",
        ]) + "\n"

    def _render_summary(self, persona: dict[str, Any]) -> str:
        """Resumen rápido en formato callout."""
        demo = persona.get("demographics", {})
        segment = persona.get("segment", {})
        spending = persona.get("spending", {})

        seg_desc = ""
        if segment.get("type") and segment.get("name"):
            type_labels = {
                "brand": "Marca",
                "model": "Modelo",
                "product_category": "Tipo de vehículo",
                "channel": "Canal de venta",
                "interest": "Interés principal",
            }
            seg_desc = f"- **Segmento:** {type_labels.get(segment['type'], segment['type'])} → `{segment['name']}`"

        meta = demo.get("meta") or {}
        gender_txt = demo.get("gender", "N/D")
        if demo.get("source") == "meta" and meta.get("gender_share"):
            gender_txt = f"{gender_txt} ({meta['gender_share']}%)"
        age_txt = demo.get("age_range", "N/D")
        if demo.get("source") == "meta" and meta.get("age_share"):
            age_txt = f"{age_txt} ({meta['age_share']}% de los clics)"
        level = demo.get("meta_level")
        level_txt = {"modelo": " · perfil propio del modelo", "marca": " · heredado de la marca"}.get(level, "")

        lines = [
            "> [!summary] Perfil Resumido",
            f"- **Edad:** {age_txt}"
            + (f" (media: {demo['age_mean']})" if demo.get("age_mean") else "") + level_txt,
            f"- **Género predominante:** {gender_txt}",
            f"- **Ubicación:** {', '.join(demo.get('location', ['N/D'])) or 'N/D'}",
            self._period_line(persona),
        ]
        if seg_desc:
            lines.append(seg_desc)

        # Persona de modelo: marca a la que pertenece + nivel de pauta real
        if segment.get("type") == "model":
            if segment.get("brand"):
                brand_persona = self._brand_persona_names.get(segment["brand"])
                brand_ref = f"[[{brand_persona}|{segment['brand']}]]" if brand_persona else segment["brand"]
                lines.append(f"- **Marca:** {brand_ref}")
            if segment.get("category"):
                lines.append(f"- **Tipo de vehículo:** {segment['category']}")
            if segment.get("orders"):
                lines.append(
                    f"- **Ventas reales (ERP):** {segment['orders']:,} unidades desde 2018"
                    + (f" · últimos 12 meses: {segment['orders_last_365d']}" if segment.get("orders_last_365d") else "")
                    + (f" · últimos 90 días: {segment['orders_last_90d']}" if segment.get("orders_last_90d") else "")
                )
            lines.append(
                f"- **Pauta real (90 días):** {segment.get('ad_count', 0)} anuncios "
                f"({segment.get('active_ads', 0)} activos)"
            )
            gap = segment.get("gap")
            if gap and gap != "sin datos":
                icon = {"sub-pautado": "🟢 escalar", "sobre-pautado": "🔴 revisar",
                        "equilibrado": "⚖️", "lanzamiento": "🆕 sin ventas aún en el ERP"}.get(gap, "")
                until = f" (ERP hasta {segment['sales_until']})" if segment.get("sales_until") else ""
                win = f" ({segment['gap_window']})" if segment.get("gap_window") else ""
                lines.append(
                    f"- **Brecha pauta/venta:** {gap} {icon} — "
                    f"{segment.get('sales_share', 0)}% de las ventas de la marca{win} vs "
                    f"{segment.get('ad_share', 0)}% de sus anuncios{until}"
                )
                lines.append(
                    "  _Cómo se decide: **sub-pautado** si el modelo pone ≥5 % de las ventas de la marca y tiene "
                    "menos de la mitad de anuncios que de ventas (escalar); **sobre-pautado** si pone ≥5 % de los "
                    "anuncios y vende menos de la mitad de eso (revisar); **equilibrado** si no pasa ninguna de las dos._"
                )

        if spending.get("avg_order_value"):
            lines.append(f"- **Ticket promedio (ERP, facturado):** USD {spending['avg_order_value']:,.0f}")
        lines.append("")

        return "\n".join(lines) + "\n"

    def _render_demographics(self, persona: dict[str, Any]) -> str:
        """Sección de demografía."""
        demo = persona.get("demographics", {})
        lines = ["## 👤 Demografía\n"]
        lines.append(
            "_Qué es: quién hace clic en los anuncios de este público, por edad y género. "
            "De dónde sale: Meta, desglose por anuncio, ponderado por clics. "
            "No es quién compró: eso el ERP no lo registra._\n"
        )

        lines.append(f"- **Rango de edad:** {demo.get('age_range', 'N/D')}")
        if demo.get("age_mean"):
            lines.append(f"- **Edad media:** {demo.get('age_mean')} años")
        if demo.get("age_median"):
            lines.append(f"- **Edad mediana:** {demo.get('age_median')} años")
        lines.append(f"- **Género predominante:** {demo.get('gender', 'N/D')}")

        locations = demo.get("location", [])
        if locations:
            lines.append(f"- **Ubicaciones principales:** {', '.join(locations)}")

        meta = demo.get("meta") or {}
        if demo.get("source") == "meta" and meta:
            dist = meta.get("age_distribution") or {}
            top = ", ".join(f"{k}: {v}%" for k, v in list(dist.items())[:6])
            level = demo.get("meta_level", "marca")
            seg = persona.get("segment", {}) or {}
            if level == "modelo":
                origen = (
                    f"anuncios de Meta que nombran a **{seg.get('name', '')}** "
                    f"({meta.get('weight', 0):,} clics en la ventana)"
                )
            else:
                origen = (
                    f"audiencia de Meta de la marca **{seg.get('brand') or seg.get('name', '')}** "
                    f"({meta.get('weight', 0):,} clics)"
                )
            lines.append(
                f"- **Fuente edad/género:** {origen}, ponderado por clics — "
                f"{meta.get('gender', '')} {meta.get('gender_share', 0)}%"
            )
            if top:
                lines.append(f"- **Distribución de edad (Meta):** {top}")
            sample = meta.get("model_sample")
            if level == "marca" and sample:
                lines.append(
                    f"- ⚠️ El modelo tiene anuncios propios pero pocos clics "
                    f"({sample.get('weight', 0)}): {sample.get('gender', '')} {sample.get('gender_share', 0)}%, "
                    f"edad {sample.get('age_range', '')}. Se usa el perfil de la marca hasta juntar "
                    f"más de 100 clics."
                )
            elif level == "marca" and seg.get("type") == "model":
                if seg.get("ad_count"):
                    lines.append("- ⚠️ Perfil heredado de la marca: el desglose edad/género por anuncio no estaba "
                                 "disponible en esta corrida (se atribuye por modelo desde el 2026-09-18).")
                else:
                    lines.append("- ⚠️ Sin anuncios propios del modelo en la ventana: perfil heredado de la marca.")
            lines.append("- _El ERP no registra edad ni género del comprador; ubicación = sucursal de la venta._")
        elif demo.get("source") == "ventas":
            lines.append("- **Fuente:** histórico de ventas")

        lines.append("")
        return "\n".join(lines)

    def _render_interests(self, persona: dict[str, Any]) -> str:
        """Intereses observados (temas de anuncios + modelos pedidos) y NSE estimado."""
        lines = ["## 🎯 Intereses y Comportamientos\n"]
        lines.append(
            "_Qué es: los temas que aparecen en los anuncios que este público ve y clickea. "
            "No son intereses declarados (Meta dejó de exponerlos en 2021): es con qué le estamos hablando y qué responde. "
            "El % es la parte de los anuncios que toca cada tema._\n"
        )
        obs = persona.get("observed_interests") or {}
        interests = persona.get("interests", [])
        if obs.get("temas"):
            lines.append(f"**Intereses observados** ({obs.get('base_anuncios', 0)} anuncios reales leídos):")
            for t in obs["temas"]:
                lines.append(f"- {t['tema']} · {t['pct']}% de los anuncios")
        if obs.get("modelos_pedidos"):
            lines.append("\n_Qué modelos piden en el formulario: está en **Leads reales**, más abajo, para no tener el mismo número dos veces._")
        for interest in interests:
            lines.append(f"- {interest}")
        if not obs and not interests:
            lines.append("_Sin datos de intereses disponibles._")
        lines.append("\n> _Meta ya no expone intereses declarados de la audiencia (Audience Insights cerró en 2021); esto es lo que el público ve y con lo que interactúa._\n")

        nse = persona.get("nse")
        lines.append("## 🏷️ Nivel socioeconómico (estimado)\n")
        if nse:
            lines.append(f"- **NSE estimado:** {nse['nivel']}")
            lines.append("- **Señales que se usaron:**")
            for sig in nse.get("senales", []):
                lines.append(f"  - {sig}")
            lines.append(
                "- _Cómo leerlo: **AB** alto · **C+** medio-alto · **C** medio · **C-/D** entrada. "
                "Es una estimación nuestra con esas cuatro señales (precio facturado, financiación vs contado en el "
                "formulario, iPhone vs Android en los clics, zona). Meta no entrega nivel socioeconómico en Paraguay. "
                "Sirve para orientar pauta y oferta; no es un dato del cliente._"
            )
        else:
            lines.append("_Sin señales suficientes para estimar._")
        lines.append("")
        return "\n".join(lines)

    def _render_purchase(self, persona: dict[str, Any]) -> str:
        """Sección de comportamiento de compra."""
        lines = ["## 🛒 Comportamiento de Compra\n"]
        lines.append("_Qué es: qué se vendió de verdad. De dónde sale: el ERP (facturación), no la pauta._\n")

        # Productos
        products = persona.get("top_products", [])
        if products:
            lines.append("**Productos más comprados:**")
            for p in products:
                lines.append(f"- [[{self._sanitize_wikilink(p)}]]")
            lines.append("")

        # Categorías
        categories = persona.get("top_categories", [])
        es_modelo = (persona.get("segment") or {}).get("type") == "model"
        if categories and not es_modelo:
            lines.append("**Tipos de vehículo que compra este público (ERP):**")
            for c in categories:
                lines.append(f"- `#{self._sanitize_tag(c)}`")
            lines.append("")

        # Canales (solo si el ERP los tiene para este segmento)
        channels = persona.get("preferred_channels", [])
        if channels:
            lines.append("**Canal de la venta (ERP):**")
            for ch in channels:
                lines.append(f"- {ch}")
            lines.append("")

        # Extras del ERP (versiones, retoma, sucursal, vendedores)
        erp = persona.get("erp") or {}
        if erp.get("top_versions"):
            lines.append("**Versiones más vendidas:**")
            lines.extend(f"- {v}" for v in erp["top_versions"])
            lines.append("")
        if erp.get("tradein_brands"):
            tr = ", ".join(f"{k} ({v})" for k, v in list(erp["tradein_brands"].items())[:5])
            lines.append(
                f"**De qué marca vienen (retoma, {erp.get('tradein_rate', 0)}% de las ventas):** {tr}"
            )
            lines.append("_Retoma = entregó un usado como parte de pago. El % es sobre las ventas de este segmento; "
                         "entre paréntesis, cuántas unidades por marca entregada._")
            lines.append("")
        if erp.get("branches"):
            lines.append(f"**Sucursales donde más se vende:** {', '.join(erp['branches'])}")
            lines.append("")
        if erp.get("price"):
            pr = erp["price"]
            lines.append(
                f"**Precio real facturado:** USD {pr.get('min', 0):,.0f} – {pr.get('max', 0):,.0f} "
                f"(promedio {pr.get('avg', 0):,.0f})"
            )
            lines.append("_Es lo que se facturó, no la lista: el máximo puede superar el precio vigente porque incluye "
                         "versiones anteriores, accesorios y precios de otros períodos; el mínimo, descuentos y retomas._")
            lines.append("")

        if not products and not categories and not channels:
            lines.append("_Sin datos de compra disponibles._\n")

        return "\n".join(lines)

    def _render_pains(self, persona: dict[str, Any]) -> str:
        """Sección de dolores (callout de alerta)."""
        pains = persona.get("pains", [])
        lines = ["> [!warning] 🔴 Dolores y Frustraciones\n"]
        lines.append(self._insight_basis_line(persona))

        if not pains:
            lines.append("> _Sin datos suficientes para identificar dolores._\n")
            return "\n".join(lines)

        for pain in pains:
            lines.append(f"> - {pain}")

        lines.append("\n")
        return "\n".join(lines)

    @staticmethod
    def _insight_basis_line(persona: dict[str, Any]) -> str:
        """Una línea que dice de dónde salen dolores/objetivos/motivaciones."""
        b = persona.get("insight_basis") or {}
        seg = persona.get("segment") or {}
        if b.get("level") == "manual":
            marca = seg.get("brand") or seg.get("name", "")
            return (f"> _De dónde sale: curación manual del equipo de marketing sobre los anuncios de {marca} "
                    "(se revisa cuando cambia la campaña). No son encuestas._\n>")
        if b.get("sample"):
            de = "de este modelo" if b.get("level") == "modelo" else (
                f"de la marca {seg.get('brand') or seg.get('name', '')} (el modelo tiene pocos anuncios propios)"
                if seg.get("type") == "model" else "de esta marca")
            return (f"> _De dónde sale: del texto de {b['sample']} anuncios reales {de}. Son los temas con los que la "
                    "pauta ya le habla y a los que responde; no son encuestas._\n>")
        return "> _De dónde sale: reglas generales por ticket y canal (esta marca no tiene anuncios con texto para leer)._\n>"

    def _render_goals(self, persona: dict[str, Any]) -> str:
        """Sección de objetivos (callout de éxito)."""
        goals = persona.get("goals", [])
        lines = ["> [!tip] 🎯 Objetivos y Necesidades\n"]

        if not goals:
            lines.append("> _Sin datos suficientes para identificar objetivos._\n")
            return "\n".join(lines)

        for goal in goals:
            lines.append(f"> - {goal}")

        lines.append("\n")
        return "\n".join(lines)

    def _render_motivations(self, persona: dict[str, Any]) -> str:
        """Sección de motivaciones (callout de info)."""
        motivations = persona.get("motivations", [])
        lines = ["> [!info] 💡 Motivaciones de Compra\n"]

        if not motivations:
            lines.append("> _Sin datos suficientes para identificar motivaciones._\n")
            return "\n".join(lines)

        for motivation in motivations:
            lines.append(f"> - {motivation}")

        lines.append("\n")
        return "\n".join(lines)

    def _render_strategy(self, persona: dict[str, Any]) -> str:
        """Sección de estrategia recomendada (callout de ejemplo)."""
        lines = ["> [!example] 📣 Estrategia Recomendada\n"]

        interests = persona.get("interests", [])
        channels = persona.get("preferred_channels", [])
        segment = persona.get("segment", {})

        # Mensaje clave
        if segment.get("name"):
            lines.append(f"> **Mensaje clave:** Enfoca la comunicación en '{segment['name']}'.")

        # Canal
        if channels:
            lines.append(f"> **Canales:** Prioriza {', '.join(channels[:2])}.")

        # Oferta: la vigente de verdad (planilla de acciones comerciales), no una regla genérica.
        ac = ((persona.get("extras") or {}).get("acciones")) or {}
        if ac.get("descuento_max"):
            lines.append(f"> **Oferta vigente:** descuento hasta USD {ac['descuento_max']:,.0f} "
                         f"({ac.get('periodo') or 'planilla de acciones comerciales'}). Usarla en el copy mientras dure.")
        elif ac:
            lines.append("> **Oferta vigente:** sin descuento cargado en la planilla de acciones comerciales este período.")

        # Targeting
        if interests:
            top_3 = interests[:3]
            lines.append(f"> **Targeting:** Crea audiencias similares basadas en: {', '.join(top_3)}.")

        # Formato de creatividad (real, según dónde cae hoy el gasto)
        fmt = persona.get("creative_format")
        if fmt:
            lines.append(
                f"> **Formato:** {fmt['top_format']} concentra el {fmt['top_format_share']}% "
                f"de las impresiones reales — priorizá ese formato en las piezas nuevas."
            )

        # Públicos: ¿la pauta actual va toda a público frío?
        mix = persona.get("audience_mix") or {}
        if mix.get("adsets"):
            if mix.get("caliente"):
                warm = f"{mix['caliente']} de {mix['adsets']} adsets usan base propia"
                if mix.get("lookalike"):
                    warm += f" ({mix['lookalike']} lookalike)"
                lines.append(f"> **Públicos hoy:** {mix['frio_pct']}% de los adsets activos van a público frío; {warm}.")
            else:
                lines.append(
                    f"> **Públicos hoy:** los {mix['adsets']} adsets activos van a público frío "
                    f"({mix.get('advantage', 0)} con Advantage+). Sumar retargeting (formulario abierto sin enviar, "
                    "visitantes web) y la base de compradores del ERP."
                )

        # Presupuesto sugerido (modelo) o gasto actual (marca)
        b = persona.get("budget") or {}
        if b.get("spend_month"):
            if segment.get("type") == "model":
                cur = b.get("current_month_est")
                sug = b.get("suggested_month")
                if sug:
                    txt = f"> **Presupuesto sugerido:** ~USD {sug:,.0f}/mes (hoy ~USD {cur:,.0f}/mes según su peso en anuncios)"
                    if b.get("expected_leads_month"):
                        txt += f" → ~{b['expected_leads_month']} leads/mes al CPL actual de la marca (USD {b['cpl']})"
                    lines.append(txt + ".")
                    lines.append(f"> _Base del cálculo: {b.get('basis', '')}. El CPL es el de **toda la marca** en la "
                                 "ventana (gasto ÷ leads de formulario); si el modelo tiene campaña propia, el CPL real es "
                                 "el de esa campaña y puede ser distinto._")
                elif b.get("basis"):
                    lines.append(f"> **Presupuesto:** {b['basis']}.")
            else:
                txt = f"> **Inversión actual:** USD {b['spend_90d']:,.0f} en la ventana (~USD {b['spend_month']:,.0f}/mes)"
                if b.get("cpl"):
                    unidad = "conversaciones de WhatsApp" if b.get("lead_basis") == "conversacion" else "leads"
                    txt += f", {b['leads_90d']:,} {unidad} → costo por {'conversación' if b.get('lead_basis') == 'conversacion' else 'lead'} USD {b['cpl']}"
                lines.append(txt + ".")

        # De dónde sale cada recomendación (pedido de marketing: "¿y de dónde lo saca?")
        lines.append("> ")
        lines.append("> **De dónde sale:** el mensaje clave es el segmento de la nota; los canales salen del "
                     "formato con más impresiones reales en Meta; el targeting, de los intereses configurados "
                     "hoy en los adsets activos; los públicos, del targeting real de esos adsets; el presupuesto, "
                     "del gasto real de la marca repartido según el peso de cada modelo en las ventas del ERP.")

        lines.append("\n")
        return "\n".join(lines)

    def _period_line(self, persona: dict[str, Any]) -> str:
        """Línea con la ventana de tiempo que lee cada fuente."""
        per = persona.get("periods") or {}
        parts = []
        m = per.get("meta") or {}
        if m.get("start"):
            parts.append(f"Meta {m['start']} → {m['end']}")
        sd = per.get("sales") or {}
        if sd.get("start") or sd.get("end"):
            parts.append(f"ERP {sd.get('start', '?')} → {sd.get('end', '?')}")
        bx = per.get("bitrix") or {}
        if bx.get("days_back"):
            parts.append(f"Bitrix últimos {bx['days_back']} días")
        return "- **Período leído:** " + (" · ".join(parts) if parts else "N/D")

    def _render_real_leads(self, persona: dict[str, Any]) -> str:
        """Resumen agregado de leads reales del formulario (sin PII: solo conteos)."""
        leads = persona.get("real_leads", {}) or {}
        seg = persona.get("segment") or {}
        marca = seg.get("brand") if seg.get("type") == "model" else seg.get("name", "")
        lines = [f"> [!quote] 📥 Leads reales del formulario de Meta — {marca} (ventana Meta)\n"]
        lines.append("> _Qué es: lo que la gente respondió en los formularios de Meta de **toda la marca** (los formularios "
                     "son por cuenta, no por modelo). Son conteos agregados, sin datos personales. Distinto del CRM: acá "
                     "solo Meta; en Bitrix entran todos los canales._")
        lines.append(f"> **Total de leads de la marca en la ventana:** {leads.get('total_leads', 0):,}")
        tm = leads.get("this_model")
        if tm is not None:
            lines.append(f"> **Pidieron este modelo:** {tm.get('count', 0):,} de esos leads ({tm.get('pct', 0)} %)")

        def _top_line(label: str, key: str) -> str | None:
            data = leads.get(key) or {}
            if not data:
                return None
            top = list(data.items())[:3]
            parts = ", ".join(f"{k} ({v})" for k, v in top)
            return f"> **{label}:** {parts}"

        for label, key in [
            ("Modelos más pedidos (toda la marca)", "model_interest_norm" if leads.get("model_interest_norm") else "model_interest"),
            ("Método de pago preferido", "payment_method"),
            ("Ciudad", "city"),
            ("Interés de compra", "purchase_intent"),
        ]:
            line = _top_line(label, key)
            if line:
                lines.append(line)

        lines.append("\n")
        return "\n".join(lines)

    def _render_crm(self, persona: dict[str, Any]) -> str:
        """Embudo CRM de Bitrix para la marca (lead → convertido → deal ganado)."""
        crm = persona.get("crm", {}) or {}
        segment = persona.get("segment", {})
        brand = segment.get("brand") if segment.get("type") == "model" else segment.get("name", "")
        lines = [f"> [!abstract] 📈 Embudo CRM Bitrix — {brand} (90 días)\n"]
        lines.append(
            f"> **Leads:** {crm.get('leads', 0):,} → **convertidos:** {crm.get('converted', 0):,} "
            f"({crm.get('conversion_rate', 0)}%)"
        )
        ch = crm.get("leads_by_channel") or {}
        if ch:
            lines.append("> **Por canal:** " + ", ".join(f"{k} {v:,}" for k, v in list(ch.items())[:4]))
        lines.append(
            f"> **Deals:** {crm.get('deals', 0):,} — ganados {crm.get('won', 0)}, "
            f"perdidos {crm.get('lost', 0)}, en proceso {crm.get('in_progress', 0)} "
            f"(win rate {crm.get('win_rate', 0)}%)"
        )
        if crm.get("won"):
            lines.append(
                f"> **Monto ganado:** USD {crm.get('won_amount', 0):,.0f} · "
                f"ticket promedio USD {crm.get('avg_ticket_won', 0):,.0f}"
            )
        lines.append("> _Cómo leerlo: **lead** = contacto que entró al CRM por cualquier canal; **convertido** = ese lead "
                     "pasó a negociación (estado «Convertido» en Bitrix); **deal** = negociación con monto cargada. "
                     "Si dice 0 deals, Bitrix no tiene negociaciones cargadas para la marca en esta ventana — no significa "
                     "que no se vendió: la venta real está arriba, en «Ventas reales (ERP)»._")
        if segment.get("type") == "model":
            lines.append("> _Bitrix agrega por marca; este embudo es el de la marca, no del modelo._")
        lines.append("\n")
        return "\n".join(lines)

    def _render_competitors(self, persona: dict[str, Any]) -> str:
        """Precio de lista en el mercado y competidores directos del modelo (Datacar)."""
        c = persona.get("competitors", {}) or {}
        lines = ["> [!danger] ⚔️ Precio de mercado y competencia directa — uso interno (Datacar)\n"]
        rng = f"USD {c.get('price_min', 0):,.0f}"
        if c.get("price_max") and c["price_max"] != c.get("price_min"):
            rng += f" – {c['price_max']:,.0f}"
        lines.append(f"> **Precio de lista:** {rng} · segmento {c.get('subsegment', '—')} · {c.get('rank_in_subsegment', '—')}")
        comps = c.get("competitors") or []
        if comps:
            lines.append("> **Competencia directa (±25% de precio):**")
            for x in comps[:6]:
                lines.append(f"> - {x['brand']} {x['model']} {x['version']} — USD {x['price_usd']:,.0f} "
                             f"({x['delta_pct']:+.0f}%) · {x['dealer_group']}")
        internal = c.get("internal_overlap") or []
        if internal:
            lines.append("> **Solapa con modelos propios:** "
                         + ", ".join(f"{x['brand']} {x['model']} ({x['delta_pct']:+.0f}%)" for x in internal[:4]))
        lines.append("> Detalle completo: [[💰 Precios Mercado 0km (Datacar)]]. _No usar en copies públicos._")
        lines.append("\n")
        return "\n".join(lines)

    def _render_extras(self, persona: dict[str, Any]) -> str:
        """Stock real, acciones comerciales, objetivos de venta y negociación (uso interno)."""
        ex = persona.get("extras") or {}
        seg = persona.get("segment", {}) or {}
        lines = ["> [!info] 📦 Stock, oferta y objetivos — uso interno\n"]
        st = ex.get("stock")
        if st and seg.get("type") == "model":
            dias = f" · {st['dias_promedio']} días promedio en stock" if st.get("dias_promedio") is not None else ""
            lines.append(f"> **Stock hoy:** {st['total']} unidades ({st['disponible']} disponibles, {st['en_viaje']} en viaje, "
                         f"{st['propuesta']} con propuesta){dias}.")
        elif st:
            lines.append(f"> **Stock de la marca:** {st['total']} unidades ({st['disponible']} disponibles, {st['en_viaje']} en viaje, {st['propuesta']} con propuesta).")
        ac = ex.get("acciones")
        if ac:
            precio = f"USD {ac['pvp_min']:,.0f}" + (f" a {ac['pvp_max']:,.0f}" if ac["pvp_max"] != ac["pvp_min"] else "")
            txt = f"> **Precio de lista ({ac.get('periodo') or 'vigente'}):** {precio} en {ac['versiones']} versión(es)"
            if ac.get("descuento_max"):
                txt += f" · **descuento vigente hasta USD {ac['descuento_max']:,.0f}**"
            if ac.get("avg_ventas_mes"):
                txt += f" · ritmo {ac['avg_ventas_mes']:g} unidades/mes"
            lines.append(txt + ".")
            for a in ac.get("acciones", []):
                lines.append(f"> **Acción comercial:** {a}")
            if st and ac.get("avg_ventas_mes"):
                meses = (st.get("total", 0)) / ac["avg_ventas_mes"]
                if meses >= 6:
                    lines.append(f"> ⚠️ **Presión de stock:** ~{meses:.0f} meses de stock al ritmo actual → candidato a más pauta u oferta.")
                elif meses <= 1.5 and st.get("en_viaje", 0) == 0:
                    lines.append(f"> ⚠️ **Poco stock:** ~{meses:.1f} meses al ritmo actual y nada en viaje → no escalar pauta hasta reponer.")
        ng = ex.get("negociaciones_modelo")
        if ng:
            lines.append(f"> **Negociaciones abiertas del modelo:** {ng['negociaciones']} ({ng['periodo']}).")
        ob = ex.get("objetivos")
        if ob:
            mes = f"{ob['real_mes']} de {ob['objetivo_mes']} ({ob['avance_mes_pct']}%)" if ob.get("objetivo_mes") else "sin objetivo cargado"
            comp = f" (objetivo compartido con {ob['compartido_con']})" if ob.get("compartido_con") else ""
            lines.append(f"> **Objetivo de la marca{comp} (según el ERP):** mes {ob['month']}/{ob['year']}: {mes} · "
                         f"acumulado {ob['year']}: {ob['real_ytd']} de {ob['objetivo_ytd']} ({ob['avance_ytd_pct']}%) · "
                         f"anual {ob['objetivo_anual']} unidades. Ventas cargadas hasta {ob.get('sales_until', '?')}: "
                         "lo vendido después de esa fecha todavía no cuenta acá.")
        nb = ex.get("negociacion_marca")
        if nb:
            lines.append(f"> **Equipo comercial (planilla semanal de negociación, {nb['periodo']}):** {nb['vendedores']} vendedores · "
                         f"promesa del mes {nb['promesa_mes']} · venta del mes a esa semana (MTD) {nb['venta_mtd']} · leads del mes {nb['leads_mes']} · "
                         f"negociaciones abiertas {nb['negociaciones_abiertas']} (semana actual {nb['nego_actual']}, pasada {nb['nego_pasada']}) · "
                         f"perdidas {nb['perdidas']}.")
            lines.append("> _La planilla y el ERP tienen cortes distintos (una semana vs. la última carga), por eso la venta del mes "
                         "de acá puede no coincidir con el objetivo de arriba. El ERP manda._")
        lines.append("> _Fuentes: stock del ERP, planilla de acciones comerciales, budget de ventas y resumen semanal de negociación (data/fuentes/). Sin datos personales._")
        lines.append("\n")
        return "\n".join(lines)

    def _render_sources(self, persona: dict[str, Any]) -> str:
        """Sección de fuentes de datos."""
        sources = persona.get("data_sources", [])
        lines = ["## 📊 Fuentes de Datos\n"]

        # Aviso explícito cuando el histórico de ventas todavía es el de ejemplo:
        # sin esto, la demografía y el ticket ficticios se leen como reales.
        if self.sales_is_sample and "sales" in sources:
            lines.append(
                "> [!warning] Demografía y ticket = datos de EJEMPLO\n"
                "> El histórico de ventas conectado todavía es el CSV de muestra, "
                "así que **edad, género, ciudades y ticket promedio son ficticios**.\n"
                "> Lo que sí es real: el modelo, su marca, el volumen de pauta, "
                "el copy analizado, el formato por placement y los leads de formulario.\n"
            )

        source_labels = {
            "bitrix": "CRM Bitrix24 (agregados)",
            "datacar": "Datacar (precios de mercado)",
            "sales": "Histórico de Ventas",
            "google_ads": "Google Ads",
            "meta_ads": "Meta Ads",
        }

        if not sources:
            lines.append("_Sin fuentes de datos registradas._\n")
            return "\n".join(lines)

        for src in sources:
            label = source_labels.get(src, src)
            lines.append(f"- [x] {label}")

        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Índice MOC
    # ------------------------------------------------------------------

    @staticmethod
    def _row(p: dict[str, Any]) -> str:
        """Fila de tabla resumen para una persona (MOC general y por marca)."""
        demo = p.get("demographics", {}) or {}
        seg = p.get("segment", {}) or {}
        meta = demo.get("meta") or {}
        name = ObsidianExporter._sanitize_filename(p.get("name", p.get("id", "")))
        age = demo.get("age_range", "N/D")
        gender = demo.get("gender", "N/D")
        if demo.get("source") == "meta" and meta.get("gender_share"):
            gender = f"{gender} {meta['gender_share']}%"
        level = {"modelo": "modelo", "marca": "marca"}.get(demo.get("meta_level", ""), "")
        if seg.get("type") == "model":
            orders = seg.get("orders_last_365d") or seg.get("orders", 0)
            ads = seg.get("ad_count", 0)
            gap = seg.get("gap", "")
            icon = {"sub-pautado": "🟢", "sobre-pautado": "🔴", "equilibrado": "⚖️", "lanzamiento": "🆕"}.get(gap, "")
            b = p.get("budget") or {}
            sug = f"USD {b['suggested_month']:,.0f}" if b.get("suggested_month") else "—"
            return f"| [[{name}]] | {age} | {gender} | {level} | {orders:,} | {ads} | {icon} {gap} | {sug} |"
        return f"| [[{name}]] | {age} | {gender} | {level} | | | | |"

    MODEL_TABLE_HEADER = (
        "| Nota | Edad | Género | Demo | Ventas 12m | Anuncios | Brecha | Presup. sugerido/mes |\n"
        "|---|---|---|---|---|---|---|---|"
    )

    def _create_brand_index(self, brand: str, personas: list[dict[str, Any]]) -> Path:
        """Índice de una marca: comprador + modelos + marketing + audiencias."""
        safe_brand = self._sanitize_filename(brand)
        path = self.output_dir / safe_brand / f"{safe_brand}.md"
        path.parent.mkdir(parents=True, exist_ok=True)

        brand_p = next((p for p in personas if p.get("segment", {}).get("type") == "brand"
                        and p["segment"].get("name") == brand), None)
        models = [p for p in personas if p.get("segment", {}).get("type") == "model"
                  and p["segment"].get("brand") == brand]
        models.sort(key=lambda p: (p["segment"].get("orders_last_365d") or 0, p["segment"].get("orders", 0), p["segment"].get("ad_count", 0)), reverse=True)

        lines = [
            "---",
            f"type: moc-marca",
            f"marca: {brand}",
            f"created: {datetime.now().strftime('%Y-%m-%d')}",
            f"tags:\n  - moc\n  - marca/{self._sanitize_tag(brand)}",
            "---\n",
            f"# 🚗 {brand}\n",
            f"> Generado el **{datetime.now().strftime('%Y-%m-%d %H:%M')}** · "
            f"{len(models)} modelos con persona propia.\n",
        ]
        if brand_p:
            lines.append(f"## 👤 Comprador de la marca\n")
            lines.append(f"- [[{self._sanitize_filename(brand_p['name'])}]]")
            b = brand_p.get("budget") or {}
            if b.get("spend_month"):
                txt = f"- **Inversión Meta:** ~USD {b['spend_month']:,.0f}/mes"
                if b.get("cpl"):
                    if b.get("lead_basis") == "conversacion":
                        txt += f" · costo por conversación USD {b['cpl']} · {b['leads_90d']:,} conversaciones de WhatsApp en la ventana (formularios: {b.get('form_leads_90d', 0)})"
                    else:
                        txt += f" · CPL USD {b['cpl']} · {b['leads_90d']:,} leads en la ventana"
                lines.append(txt)
            mix = brand_p.get("audience_mix") or {}
            if mix.get("adsets"):
                lines.append(f"- **Públicos:** {mix['frio_pct']}% de {mix['adsets']} adsets activos a público frío")
            lines.append("")
        m_centro = (self.centro.get("marcas") or {}).get(brand) if self.centro else None
        if m_centro:
            lines.append("## 👥 Quién mira y quién decide\n")
            e = m_centro.get("embudo") or {}
            if e:
                lines.append(f"- En Meta, {self._frase_genero(e)}.")
            emp = m_centro.get("empresa") or {}
            if emp:
                lines.append(f"- El {self._pct(emp.get('empresa_pct'))} de las compras a cliente final las factura una empresa.")
            lines.append(f"- **Qué hacer en Meta Ads y cómo leerlo:** [[{self.centro_nota(brand)}]]\n")
        if models:
            lines.append("## 🚘 Modelos\n")
            lines.append(self.MODEL_TABLE_HEADER)
            lines.extend(self._row(p) for p in models)
            lines.append("")
            lines.append("_Demo = de dónde sale edad/género: **modelo** (anuncios propios del modelo) o "
                         "**marca** (heredado, pocos clics propios). Brecha: 🟢 sub-pautado = vende más de lo "
                         "que se pauta, 🔴 sobre-pautado, 🆕 lanzamiento sin ventas en el ERP aún._\n")
        lines.append("## 📣 Marketing y audiencias\n")
        lines.append(f"- [[Audiencias Meta - {safe_brand}]] · [[🔁 Base de Recompra (ERP)|Base de recompra]]")
        for p in ([brand_p] if brand_p else []) + models:
            n = self._sanitize_filename(p["name"])
            lines.append(f"- {n}: [[Meta Ads - {n}|Meta]] · [[Google Ads - {n}|Google]] · [[Email - {n}|Email]] · [[WhatsApp - {n}|WhatsApp]]")
        lines.append("")
        lines.append("← [[ Buyer Personas MOC|Volver al mapa general]]")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _create_index(self, personas: list[dict[str, Any]]) -> Path:
        """Crea el MOC general, agrupado por marca (y segmentos al final)."""
        index_path = self.output_dir / self.index_filename

        lines = [
            "---",
            f"created: {datetime.now().strftime('%Y-%m-%d')}",
            f"type: moc",
            f"tags:",
        ]
        for tag in self.default_tags:
            lines.append(f"  - {tag}")
        lines.append("  - moc")
        lines.append("---\n")
        lines.append("# 🗺️ Buyer Personas - Mapa de Contenidos\n")
        lines.append(f"> Generado el **{datetime.now().strftime('%Y-%m-%d %H:%M')}** "
                      f"con **{len(personas)}** perfiles, agrupados por marca.\n")
        per = (personas[0].get("periods") if personas else {}) or {}
        m, sd = per.get("meta") or {}, per.get("sales") or {}
        if m.get("start") or sd.get("end"):
            lines.append(f"> **Período:** Meta {m.get('start', '?')} → {m.get('end', '?')} · "
                         f"ERP {sd.get('start', '?')} → {sd.get('end', '?')}\n")

        brands = sorted(self._brands_of(personas), key=lambda b: -sum(
            p["segment"].get("orders", 0) for p in personas
            if p.get("segment", {}).get("type") == "model" and p["segment"].get("brand") == b))
        for brand in brands:
            safe_brand = self._sanitize_filename(brand)
            brand_p = next((p for p in personas if p.get("segment", {}).get("type") == "brand"
                            and p["segment"].get("name") == brand), None)
            models = [p for p in personas if p.get("segment", {}).get("type") == "model"
                      and p["segment"].get("brand") == brand]
            models.sort(key=lambda p: (p["segment"].get("orders_last_365d") or 0, p["segment"].get("orders", 0), p["segment"].get("ad_count", 0)), reverse=True)
            lines.append(f"## [[{safe_brand}]]\n")
            lines.append(self.MODEL_TABLE_HEADER)
            if brand_p:
                lines.append(self._row(brand_p))
            lines.extend(self._row(p) for p in models)
            lines.append("")

        others = [p for p in personas if p.get("segment", {}).get("type") not in ("brand", "model")]
        if others:
            lines.append("## Segmentos (tipo de vehículo)\n")
            lines.append("| Nota | Edad | Género | Demo | | | | |")
            lines.append("|---|---|---|---|---|---|---|---|")
            lines.extend(self._row(p) for p in others)
            lines.append("")

        lines.append("---")
        lines.append("## 🔍 Cómo usar este MOC")
        lines.append("- Cada marca tiene su carpeta: comprador de la marca, un modelo por nota, Marketing/ y sus audiencias.")
        lines.append("- **Demo** dice si edad/género salen de los anuncios del modelo o se heredan de la marca.")
        lines.append("- **Presup. sugerido** reparte el gasto real de la marca según el peso de cada modelo en ventas.")
        lines.append("- Usa el graph view de Obsidian para ver las relaciones; los tags `marca/` y `modelo/` filtran.")
        lines.append("- Lo que el sistema aprende corrida tras corrida (público confirmado, cambios, tendencias, reglas): [[🧠 Memoria de Audiencia]].")

        index_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Índice MOC creado: %s", index_path.name)
        return index_path

    # ------------------------------------------------------------------
    # Copiar al Vault de Obsidian
    # ------------------------------------------------------------------

    def _copy_to_vault(self, files: list[Path], vault_path: Path) -> None:
        """Copia los archivos generados al vault de Obsidian."""
        if not vault_path.exists():
            logger.warning("El vault de Obsidian no existe: %s", vault_path)
            return

        target_dir = vault_path / "Buyer Personas"
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            try:
                rel = f.relative_to(self.output_dir)
            except ValueError:
                rel = Path(f.name)
            dest = target_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)

        self.cleanup_legacy_notes(target_dir)
        self.cleanup_legacy_notes(self.output_dir)
        logger.info("Copiados %d archivos al vault: %s", len(files), target_dir)

    @staticmethod
    def cleanup_legacy_notes(base: Path) -> int:
        """
        Borra las notas del layout viejo (lista plana "Persona NN - ...",
        y su marketing "Canal - Persona NN - ..."). Eran generadas por el
        pipeline, no editadas a mano, y su numeración producía duplicados.
        """
        if not base.is_dir():
            return 0
        removed = 0
        for f in list(base.glob("Persona [0-9][0-9]* - *.md")):
            f.unlink(); removed += 1
        mk = base / "Marketing"
        if mk.is_dir():
            for f in list(mk.glob("* - Persona [0-9][0-9]* - *.md")):
                f.unlink(); removed += 1
            if not any(mk.iterdir()):
                mk.rmdir()
        aud = base / "Audiencias"
        if aud.is_dir():
            for f in list(aud.glob("Audiencias Meta - *.md")):
                f.unlink(); removed += 1
        if removed:
            logger.info("Limpieza layout viejo en %s: %d notas numeradas borradas", base, removed)
        return removed

    CANALES_MARKETING = ("Meta Ads", "Google Ads", "Email", "WhatsApp")

    @classmethod
    def cleanup_stale_notes(cls, base: Path, current_names: set[str]) -> list[Path]:
        """
        Borra las fichas (y su marketing) de personas que esta corrida ya no
        produce. Sin esto, un modelo que sale del portfolio o pierde pauta
        deja su nota vieja en el vault, con datos y formato de otra fecha,
        y se lee como si fuera actual.

        Solo toca lo que generó el pipeline: fichas con ``type: buyer-persona``
        en el frontmatter y notas ``<Canal> - <Persona>.md`` dentro de
        ``Marketing/``. Lo escrito a mano (índices, audiencias, notas de
        ventas) no cumple ninguna de las dos y no se toca.
        """
        if not base.is_dir():
            return []
        vivos = {cls._sanitize_filename(n) for n in current_names if n}
        borradas: list[Path] = []
        for carpeta in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "Audiencias"):
            for f in sorted(carpeta.glob("*.md")):
                if f.stem == carpeta.name or f.stem in vivos:
                    continue
                try:
                    cabecera = f.read_text(encoding="utf-8", errors="ignore")[:600]
                except OSError:
                    continue
                if "type: buyer-persona" in cabecera:
                    f.unlink(); borradas.append(f)
            mk = carpeta / "Marketing"
            if mk.is_dir():
                for f in sorted(mk.glob("*.md")):
                    partes = f.stem.split(" - ", 1)
                    if len(partes) == 2 and partes[0] in cls.CANALES_MARKETING and partes[1] not in vivos:
                        f.unlink(); borradas.append(f)
        if borradas:
            logger.info("Limpieza de notas viejas en %s: %d borradas (personas que esta corrida ya no genera)",
                        base, len(borradas))
            for f in borradas:
                logger.info("   · %s", f.relative_to(base))
        return borradas

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Convierte un nombre en un nombre de archivo válido."""
        # Reemplazar caracteres no válidos (Obsidian admite espacios literales en nombres/wikilinks)
        safe = re.sub(r'[<>:"/\\|?*]', "", name)
        safe = safe.strip()
        return safe or "persona"

    @staticmethod
    def _sanitize_wikilink(text: str) -> str:
        """Limpia un texto para usar como wikilink de Obsidian."""
        safe = re.sub(r'[<>:"/\\|?*#\[\]]', "", text)
        return safe.strip() or "producto"

    @staticmethod
    def _sanitize_tag(text: str) -> str:
        """Limpia un texto para usar como tag de Obsidian."""
        # Primero separadores -> guion, después limpiar el resto
        safe = text.strip().replace(" ", "-").replace("_", "-")
        safe = re.sub(r'[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ-]', "", safe)
        safe = re.sub(r'-{2,}', "-", safe).strip("-")
        return safe.lower() or "tag"