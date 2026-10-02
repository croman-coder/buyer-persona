"""
Exportador de Embudo para Obsidian.

Genera un dashboard visual del embudo completo con:
- Visualización de conversión por etapa
- Métricas clave de cada fuente
- Tasa de conversión entre etapas
- Recomendaciones automáticas
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class FunnelExporter:
    """Exporta el análisis del embudo como nota de Obsidian."""

    def __init__(self, output_dir: str | Path = "output/personas"):
        self.output_dir = Path(output_dir)

    def export(self, funnel_data: dict[str, Any]) -> Path:
        """Genera la nota del embudo en Obsidian."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.output_dir / "📊 Embudo de Ventas.md"

        content = self._render_funnel(funnel_data)
        file_path.write_text(content, encoding="utf-8")

        logger.info("Embudo exportado: %s", file_path.name)
        return file_path

    def _render_funnel(self, data: dict[str, Any]) -> str:
        """Renderiza la nota completa del embudo."""
        tofu = data.get("tofu", {})
        mofu = data.get("mofu", {})
        bofu = data.get("bofu", {})
        post_sale = data.get("post_sale", {})
        date_range = data.get("date_range", {})

        sections: list[str] = []

        # Frontmatter
        sections.append(self._render_frontmatter(date_range))

        # Título
        sections.append("# 📊 Embudo de Ventas Completo\n")

        if date_range:
            sections.append(
                f"> Período analizado: **{date_range.get('start', 'N/D')}** "
                f"a **{date_range.get('end', 'N/D')}**\n"
            )

        # Resumen de conversión
        sections.append(self._render_conversion_summary(tofu, mofu, bofu))

        # TOFU
        sections.append(self._render_tofu(tofu))

        # MOFU
        sections.append(self._render_mofu(mofu))

        # BOFU
        sections.append(self._render_bofu(bofu))

        # Post-venta
        sections.append(self._render_post_sale(post_sale))

        # Recomendaciones
        sections.append(self._render_recommendations(tofu, mofu, bofu, post_sale))

        sections.append(f"\n---\n*Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

        return "\n".join(sections)

    def _render_frontmatter(self, date_range: dict) -> str:
        frontmatter = {
            "type": "funnel-dashboard",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["funnel", "dashboard", "marketing"],
        }
        if date_range:
            frontmatter["period_start"] = date_range.get("start", "")
            frontmatter["period_end"] = date_range.get("end", "")

        yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_str}---\n"

    def _render_conversion_summary(self, tofu, mofu, bofu) -> str:
        """Crea un resumen visual de conversión del embudo."""
        lines = ["## 🔻 Resumen de Conversión\n"]

        # Estimar números en cada etapa
        tofu_count = self._estimate_tofu_count(tofu)
        mofu_count = self._estimate_mofu_count(mofu)
        bofu_count = self._estimate_bofu_count(bofu)

        # Calcular tasas
        rate_1 = (mofu_count / tofu_count * 100) if tofu_count > 0 else 0
        rate_2 = (bofu_count / mofu_count * 100) if mofu_count > 0 else 0
        overall = (bofu_count / tofu_count * 100) if tofu_count > 0 else 0

        lines.append("```mermaid")
        lines.append("graph TD")
        lines.append(f'    A["🔍 TOFU - Descubrimiento<br/>{tofu_count:,} personas"]')
        lines.append(f'    B["📋 MOFU - Consideración<br/>{mofu_count:,} leads"]')
        lines.append(f'    C["🚗 BOFU - Cotizaciones<br/>{bofu_count:,} cotizaciones"]')
        lines.append(f'    D["✅ Venta"]')
        lines.append(f'    A -->|"Tasa: {rate_1:.1f}%"| B')
        lines.append(f'    B -->|"Tasa: {rate_2:.1f}%"| C')
        lines.append(f'    C --> D')
        lines.append("```\n")

        lines.append(f"> [!summary] **Conversión global del embudo: {overall:.1f}%**")
        lines.append(f"> De cada 100 personas que te descubren, ~{overall:.0f} llegan a cotizar.\n")

        return "\n".join(lines)

    def _estimate_tofu_count(self, tofu) -> int:
        total = 0
        ga = tofu.get("google_analytics", {})
        if ga.get("metrics", {}).get("total_users"):
            try:
                total += int(ga["metrics"]["total_users"])
            except (ValueError, TypeError):
                pass
        meta = tofu.get("meta_social", {}).get("metrics", {})
        if meta.get("page_impressions"):
            try:
                total += int(meta["page_impressions"])
            except (ValueError, TypeError):
                pass
        yt = tofu.get("youtube", {})
        if yt.get("total_views"):
            try:
                total += int(yt["total_views"])
            except (ValueError, TypeError):
                pass
        return total if total > 0 else 5000  # Default estimado

    def _estimate_mofu_count(self, mofu) -> int:
        total = 0
        forms = mofu.get("web_forms", {})
        if forms.get("total_leads"):
            total += forms["total_leads"]
        td = mofu.get("test_drives", {})
        if td.get("total_requests"):
            total += td["total_requests"]
        wa = mofu.get("whatsapp", {})
        if wa.get("total_conversations"):
            total += wa["total_conversations"]
        return total if total > 0 else 400

    def _estimate_bofu_count(self, bofu) -> int:
        total = 0
        quotes = bofu.get("quotes", {})
        if quotes.get("total_quotes"):
            total += quotes["total_quotes"]
        showroom = bofu.get("showroom", {})
        if showroom.get("total_visits"):
            total += showroom["total_visits"]
        return total if total > 0 else 150

    def _render_tofu(self, tofu) -> str:
        lines = ["## 🔍 TOFU - Descubrimiento / Conciencia\n"]

        if not tofu:
            lines.append("_Sin datos de esta etapa. Activar fuentes en settings.yaml_\n")
            return "\n".join(lines)

        # Google Analytics
        ga = tofu.get("google_analytics", {})
        if ga:
            lines.append("### 📈 Google Analytics 4")
            metrics = ga.get("metrics", {})
            for k, v in metrics.items():
                label = k.replace("_", " ").title()
                lines.append(f"- **{label}:** {v}")
            lines.append("")

        # Meta Social
        meta = tofu.get("meta_social", {})
        if meta:
            lines.append("### 📘 Meta / Instagram")
            metrics = meta.get("metrics", {})
            for k, v in metrics.items():
                label = k.replace("_", " ").title()
                lines.append(f"- **{label}:** {v:,}")
            lines.append("")

        # YouTube
        yt = tofu.get("youtube", {})
        if yt:
            lines.append("### ▶️ YouTube")
            lines.append(f"- **Suscriptores:** {yt.get('subscribers', 'N/D'):,}")
            lines.append(f"- **Visualizaciones totales:** {yt.get('total_views', 'N/D'):,}")
            lines.append(f"- **Videos:** {yt.get('total_videos', 'N/D')}")
            lines.append("")

        return "\n".join(lines)

    def _render_mofu(self, mofu) -> str:
        lines = ["## 📋 MOFU - Consideración / Interés\n"]

        if not mofu:
            lines.append("_Sin datos de esta etapa._\n")
            return "\n".join(lines)

        # Formularios web
        forms = mofu.get("web_forms", {})
        if forms:
            lines.append("### 🌐 Formularios Web (Leads)")
            lines.append(f"- **Total de leads:** {forms.get('total_leads', 0)}")
            by_vehicle = forms.get("by_vehicle", {})
            if by_vehicle:
                lines.append("- **Por vehículo:**")
                for v, count in sorted(by_vehicle.items(), key=lambda x: x[1], reverse=True)[:5]:
                    lines.append(f"  - {v}: {count}")
            by_source = forms.get("by_source", {})
            if by_source:
                lines.append("- **Por fuente:**")
                for s, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"  - {s}: {count}")
            lines.append("")

        # Test drives
        td = mofu.get("test_drives", {})
        if td:
            lines.append("### 🚗 Test Drives")
            lines.append(f"- **Total solicitados:** {td.get('total_requests', 0)}")
            if td.get("completion_rate"):
                lines.append(f"- **Tasa de completado:** {td['completion_rate']}")
            by_vehicle = td.get("by_vehicle", {})
            if by_vehicle:
                lines.append("- **Más solicitados:**")
                for v, count in sorted(by_vehicle.items(), key=lambda x: x[1], reverse=True)[:5]:
                    lines.append(f"  - {v}: {count}")
            lines.append("")

        # WhatsApp
        wa = mofu.get("whatsapp", {})
        if wa:
            lines.append("### 💬 WhatsApp Business")
            lines.append(f"- **Conversaciones totales:** {wa.get('total_conversations', 0)}")
            lines.append(f"- **Contactos únicos:** {wa.get('unique_contacts', 0)}")
            lines.append("")

        return "\n".join(lines)

    def _render_bofu(self, bofu) -> str:
        lines = ["## 🚗 BOFU - Decisión / Acción\n"]

        if not bofu:
            lines.append("_Sin datos de esta etapa._\n")
            return "\n".join(lines)

        # Cotizaciones
        quotes = bofu.get("quotes", {})
        if quotes:
            lines.append("### 💰 Cotizaciones")
            lines.append(f"- **Total:** {quotes.get('total_quotes', 0)}")
            if quotes.get("win_rate"):
                lines.append(f"- **Tasa de cierre (Win Rate):** {quotes['win_rate']}")
            by_result = quotes.get("by_result", {})
            if by_result:
                lines.append("- **Por resultado:**")
                for r, count in by_result.items():
                    lines.append(f"  - {r}: {count}")
            lines.append("")

        # Showroom
        showroom = bofu.get("showroom", {})
        if showroom:
            lines.append("### 🏪 Visitas al Showroom")
            lines.append(f"- **Total de visitas:** {showroom.get('total_visits', 0)}")
            by_result = showroom.get("by_result", {})
            if by_result:
                lines.append("- **Resultado:**")
                for r, count in by_result.items():
                    lines.append(f"  - {r}: {count}")
            lines.append("")

        return "\n".join(lines)

    def _render_post_sale(self, post_sale) -> str:
        lines = ["## ⭐ Post-Venta - Satisfacción\n"]

        if not post_sale:
            lines.append("_Sin datos de post-venta._\n")
            return "\n".join(lines)

        surveys = post_sale.get("surveys", {})
        if surveys:
            lines.append("### 📊 Encuestas de Satisfacción")
            lines.append(f"- **Total respuestas:** {surveys.get('total_responses', 0)}")
            lines.append(f"- **Score promedio:** {surveys.get('avg_score', 'N/D')}/10")

            if surveys.get("nps_score") is not None:
                nps = surveys["nps_score"]
                emoji = "🟢" if nps > 0 else "🔴"
                lines.append(f"- **NPS Score:** {emoji} {nps}")
                lines.append(f"- **Promotores:** {surveys.get('nps_promoters', 0)}")
                lines.append(f"- **Detractores:** {surveys.get('nps_detractors', 0)}")

            if surveys.get("recommendation_rate"):
                lines.append(f"- **Recomendarían:** {surveys['recommendation_rate']}")

            lines.append("")

        return "\n".join(lines)

    def _render_recommendations(self, tofu, mofu, bofu, post_sale) -> str:
        """Genera recomendaciones automáticas basadas en los datos."""
        lines = ["> [!example] 💡 Recomendaciones Automáticas\n"]

        recs: list[str] = []

        # Analizar MOFU
        mofu_count = self._estimate_mofu_count(mofu)
        bofu_count = self._estimate_bofu_count(bofu)

        if mofu_count > 0 and bofu_count > 0:
            conversion = bofu_count / mofu_count * 100
            if conversion < 30:
                recs.append(
                    f"⚠️ La conversión MOFU→BOFU es baja ({conversion:.0f}%). "
                    "Considera mejorar el seguimiento de leads con respuestas más rápidas."
                )
            elif conversion > 60:
                recs.append(
                    f"✅ Excelente conversión MOFU→BOFU ({conversion:.0f}%). "
                    "Tu embudo medio funciona muy bien."
                )

        # Analizar cotizaciones
        quotes = bofu.get("quotes", {})
        win_rate_str = quotes.get("win_rate", "")
        if "%" in str(win_rate_str):
            try:
                win_rate = float(str(win_rate_str).replace("%", ""))
                if win_rate < 25:
                    recs.append(
                        f"🔴 Win Rate bajo ({win_rate}%). Revisar pricing, "
                        "ofertas y capacitación de vendedores."
                    )
                elif win_rate > 40:
                    recs.append(f"🟢 Excelente Win Rate ({win_rate}%). ¡Sigan así!")
            except ValueError:
                pass

        # Analizar encuestas
        surveys = post_sale.get("surveys", {})
        nps = surveys.get("nps_score")
        if nps is not None:
            if nps < 0:
                recs.append(
                    f"🔴 NPS negativo ({nps}). Urgente mejorar experiencia post-venta "
                    "y contactar detractores."
                )
            elif nps > 30:
                recs.append(f"🟢 NPS excelente ({nps}). Considera programa de referidos.")

        # Recomendación de test drives
        td = mofu.get("test_drives", {})
        completion = td.get("completion_rate", "")
        if "%" in str(completion):
            try:
                comp_rate = float(str(completion).replace("%", ""))
                if comp_rate < 50:
                    recs.append(
                        f"⚠️ Solo {comp_rate}% de test drives se completan. "
                        "Implementar recordatorios automáticos por WhatsApp."
                    )
            except ValueError:
                pass

        if not recs:
            recs.append("📊 Activa más fuentes de datos para recibir recomendaciones personalizadas.")

        for rec in recs:
            lines.append(f"> {rec}")

        lines.append("\n")
        return "\n".join(lines)