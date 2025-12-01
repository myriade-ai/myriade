from __future__ import annotations

import html
import io
import json
import os
import re
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session, selectinload

from models import Chart, Document, Query

TAG_PATTERN = re.compile(r"(<QUERY:([^>]+)>|<CHART:([^>]+)>)")
MAX_TABLE_ROWS = 25
INLINE_CODE_FONT = "DejaVuSansMono"


@dataclass
class QueryExportData:
    query: Query
    rows: list[dict[str, Any]]
    column_names: list[str]


def generate_document_pdf(
    document: Document,
    session: Session,
    include_sql: bool = True,
) -> bytes:
    """Generate a PDF export for a document."""

    buffer = io.BytesIO()
    template = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )

    styles = _build_styles()
    flowables: list[Any] = []

    title = document.title or "Untitled Report"
    flowables.append(Paragraph(html.escape(title), styles["DocTitle"]))
    flowables.append(Spacer(1, 12))

    parts = _parse_document_content(document.content or "")
    chart_ids = [part["chart_id"] for part in parts if part["type"] == "chart"]
    charts = _load_charts(session, chart_ids)

    query_ids = [part["query_id"] for part in parts if part["type"] == "query"]
    chart_query_ids = [
        str(chart.queryId) for chart in charts.values() if chart.queryId is not None
    ]
    queries = _load_queries(session, query_ids + chart_query_ids)

    has_content = False
    for part in parts:
        if part["type"] == "markdown" and part["content"].strip():
            flowables.extend(_markdown_to_flowables(part["content"], styles))
            has_content = True
        elif part["type"] == "query":
            flowables.extend(
                _build_query_section(
                    part["query_id"], queries, include_sql, template.width, styles
                )
            )
            has_content = True
        elif part["type"] == "chart":
            flowables.extend(
                _build_chart_section(
                    part["chart_id"], charts, queries, template.width, styles
                )
            )
            has_content = True

    if not has_content:
        flowables.append(
            Paragraph(
                "This document does not contain any content yet.", styles["DocBody"]
            )
        )

    template.build(flowables)
    return buffer.getvalue()


def _parse_document_content(content: str) -> list[dict[str, str]]:
    parts: list[dict[str, str]] = []
    last_end = 0
    for match in TAG_PATTERN.finditer(content):
        start, end = match.start(), match.end()
        if start > last_end:
            parts.append({"type": "markdown", "content": content[last_end:start]})

        if match.group(2):
            parts.append({"type": "query", "query_id": match.group(2).strip()})
        elif match.group(3):
            parts.append({"type": "chart", "chart_id": match.group(3).strip()})

        last_end = end

    if last_end < len(content):
        parts.append({"type": "markdown", "content": content[last_end:]})

    if not parts:
        parts.append({"type": "markdown", "content": content})

    return parts


def _load_queries(session: Session, ids: Iterable[str]) -> dict[str, QueryExportData]:
    valid_ids = [_safe_uuid(identifier) for identifier in ids]
    uuid_ids = [identifier for identifier in valid_ids if identifier is not None]
    if not uuid_ids:
        return {}

    records = (
        session.query(Query)
        .options(selectinload(Query.database))
        .filter(Query.id.in_(uuid_ids))
        .all()
    )

    result: dict[str, QueryExportData] = {}
    for query in records:
        rows, column_names = _prepare_query_rows(query)
        result[str(query.id)] = QueryExportData(
            query=query, rows=rows, column_names=column_names
        )
    return result


def _load_charts(session: Session, ids: Iterable[str]) -> dict[str, Chart]:
    valid_ids = [_safe_uuid(identifier) for identifier in ids]
    uuid_ids = [identifier for identifier in valid_ids if identifier is not None]
    if not uuid_ids:
        return {}

    records = (
        session.query(Chart)
        .options(selectinload(Chart.query).selectinload(Query.database))
        .filter(Chart.id.in_(uuid_ids))
        .all()
    )
    return {str(chart.id): chart for chart in records}


def _prepare_query_rows(query: Query) -> tuple[list[dict[str, Any]], list[str]]:
    rows = list(query.rows or [])
    column_names: list[str] = [
        str(column.get("name"))
        for column in (query.columns or [])
        if isinstance(column, dict) and column.get("name")
    ]

    if not rows and query.sql and getattr(query, "database", None):
        try:
            data_warehouse = query.database.create_data_warehouse()
            rows, *_ = data_warehouse.query(query.sql, role="users")
        except Exception as exc:  # pragma: no cover - best-effort fallback
            current_app.logger.warning(
                "Failed to refresh query %s for PDF export: %s", query.id, exc
            )
            rows = []

    normalized_rows = [_row_to_mapping(row, column_names) for row in rows]
    if not column_names and normalized_rows:
        column_names = list(normalized_rows[0].keys())

    return normalized_rows, column_names


def _markdown_to_flowables(text: str, styles: StyleSheet1) -> list[Any]:
    flowables: list[Any] = []
    for block in _split_markdown_blocks(text):
        stripped = block.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            flowables.append(
                Paragraph(_format_inline(stripped[4:]), styles["DocHeading3"])
            )
        elif stripped.startswith("## "):
            flowables.append(
                Paragraph(_format_inline(stripped[3:]), styles["DocHeading2"])
            )
        elif stripped.startswith("# "):
            flowables.append(
                Paragraph(_format_inline(stripped[2:]), styles["DocHeading1"])
            )
        elif stripped == "---":
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        elif all(line.strip().startswith("- ") for line in stripped.splitlines()):
            items = []
            for line in stripped.splitlines():
                line_text = line.strip()[2:].strip()
                items.append(
                    ListItem(
                        Paragraph(_format_inline(line_text), styles["DocBody"]),
                        leftIndent=18,
                    )
                )
            flowables.append(ListFlowable(items, bulletType="bullet"))
        else:
            flowables.append(Paragraph(_format_inline(stripped), styles["DocBody"]))

        flowables.append(Spacer(1, 8))

    return flowables


def _split_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks if blocks else [text]


def _build_query_section(
    query_id: str,
    queries: dict[str, QueryExportData],
    include_sql: bool,
    max_width: float,
    styles: StyleSheet1,
) -> list[Any]:
    flowables: list[Any] = []
    data = queries.get(query_id)
    if not data:
        flowables.append(
            Paragraph(
                f"Query {html.escape(query_id)} could not be found.", styles["DocMeta"]
            )
        )
        flowables.append(Spacer(1, 6))
        return flowables

    title = data.query.title or f"Query {data.query.id}"
    flowables.append(Paragraph(html.escape(title), styles["DocSectionHeading"]))

    if include_sql and data.query.sql:
        # Create SQL code block with dark background using a table wrapper
        sql_preformatted = Preformatted(data.query.sql, styles["DocCode"])
        sql_table = Table([[sql_preformatted]], colWidths=[max_width])
        sql_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        flowables.append(sql_table)
        flowables.append(Spacer(1, 8))

    table = _build_results_table(data, max_width)
    if table:
        flowables.append(table)
        if len(data.rows) > MAX_TABLE_ROWS:
            flowables.append(
                Paragraph(
                    f"Showing first {MAX_TABLE_ROWS} rows of {len(data.rows)}.",
                    styles["DocMeta"],
                )
            )
    else:
        flowables.append(
            Paragraph("No rows returned for this query.", styles["DocMeta"])
        )

    flowables.append(Spacer(1, 12))
    return flowables


def _build_results_table(data: QueryExportData, max_width: float) -> Table | None:
    if not data.rows:
        return None

    columns = data.column_names or list(data.rows[0].keys())
    if not columns:
        return None

    table_data = [[col or f"Column {index + 1}" for index, col in enumerate(columns)]]

    limited_rows = data.rows[:MAX_TABLE_ROWS]
    for row in limited_rows:
        table_data.append([_format_table_value(row.get(column)) for column in columns])

    col_widths = [max_width / len(columns)] * len(columns)
    table = Table(table_data, repeatRows=1, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 1), (-1, -1), "DejaVuSans"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f9fafb")],
                ),
            ]
        )
    )

    return table


def _build_chart_section(
    chart_id: str,
    charts: dict[str, Chart],
    queries: dict[str, QueryExportData],
    max_width: float,
    styles: StyleSheet1,
) -> list[Any]:
    flowables: list[Any] = []
    chart = charts.get(chart_id)
    if not chart:
        flowables.append(
            Paragraph(
                f"Chart {html.escape(chart_id)} could not be found.", styles["DocMeta"]
            )
        )
        flowables.append(Spacer(1, 6))
        return flowables

    query_data = queries.get(str(chart.queryId))
    if not query_data:
        flowables.append(
            Paragraph(
                "The query powering this chart could not be loaded for export.",
                styles["DocMeta"],
            )
        )
        flowables.append(Spacer(1, 12))
        return flowables

    try:
        image_bytes = _render_chart_image(chart, query_data.rows)
    except RuntimeError as exc:
        flowables.append(
            Paragraph(
                f"Unable to render chart preview: {html.escape(str(exc))}",
                styles["DocMeta"],
            )
        )
        flowables.append(Spacer(1, 12))
        return flowables

    # Chart image already includes the title, so just add the image
    image = Image(io.BytesIO(image_bytes))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth = max_width
    image.drawHeight = max_width * ratio
    flowables.append(image)
    flowables.append(Spacer(1, 12))

    return flowables


def _render_chart_image(chart: Chart, rows: list[dict[str, Any]]) -> bytes:
    if not chart.config:
        raise RuntimeError("Chart configuration is missing")

    chart_options = dict(chart.config)
    dataset = chart_options.get("dataset")
    if not isinstance(dataset, dict):
        dataset = {}
    dataset["source"] = [_normalize_for_json(row) for row in rows]
    chart_options["dataset"] = dataset

    payload = json.dumps(chart_options, default=_json_default)
    script_path = (
        Path(__file__).resolve().parent.parent
        / "chat"
        / "tools"
        / "echarts-render"
        / "render.js"
    )

    # Use a unique temporary file to avoid race conditions between concurrent renders
    # Create temp file with .png suffix and delete=False so we can read it after subprocess
    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False, dir=tempfile.gettempdir()
    ) as tmp_file:
        output_path = tmp_file.name

    try:
        # Render at high resolution (3x the default size) for better quality in PDFs
        # 1500x1200 provides crisp output when scaled down in the document
        try:
            subprocess.run(
                ["node", str(script_path), payload, "750", "600", output_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            raise RuntimeError("Node.js is required to render charts") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                exc.stderr or "Failed to execute chart renderer"
            ) from exc

        if not os.path.exists(output_path):
            raise RuntimeError("Chart renderer did not produce an image")

        with open(output_path, "rb") as f:
            return f.read()
    finally:
        # Clean up the temporary file
        try:
            os.unlink(output_path)
        except OSError:
            pass  # Ignore errors during cleanup


def _row_to_mapping(row: Any, columns: list[str]) -> dict[str, Any]:
    if isinstance(row, dict):
        return {str(key): _normalize_value(value) for key, value in row.items()}

    if isinstance(row, (list, tuple)):
        data: dict[str, Any] = {}
        for index, value in enumerate(row):
            column = (
                columns[index]
                if index < len(columns) and columns[index]
                else f"column_{index + 1}"
            )
            data[column] = _normalize_value(value)
        return data

    return {"value": _normalize_value(row)}


def _format_inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<i>\1</i>", escaped)
    escaped = re.sub(
        r"`(.+?)`",
        rf"<font face='{INLINE_CODE_FONT}'>\1</font>",
        escaped,
    )
    return escaped.replace("\n", "<br/>")


def _format_table_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def _normalize_for_json(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_value(value) for key, value in row.items()}


def _json_default(value: Any) -> Any:
    normalized = _normalize_value(value)
    if normalized is value:
        return str(value)
    return normalized


def _safe_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _build_styles() -> StyleSheet1:
    fonts = _register_fonts()

    body_font = fonts["body"]
    mono_font = fonts["mono"]
    fallback_fonts = fonts.get("emoji_fallbacks", [])
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = body_font
    styles["BodyText"].fontName = body_font
    styles["Heading1"].fontName = body_font
    styles["Heading2"].fontName = body_font
    styles["Heading3"].fontName = body_font
    for style_name in ("Normal", "BodyText", "Heading1", "Heading2", "Heading3"):
        style = styles[style_name]
        style.fallbackFonts = fallback_fonts
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=26,
            spaceAfter=6,
            fontName=body_font,
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocMeta",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=6,
            fontName=body_font,
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocBody",
            parent=styles["BodyText"],
            fontSize=11,
            leading=16,
            fontName=body_font,
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocHeading1",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            fontName="DejaVuSans-Bold",
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocHeading2",
            parent=styles["Heading2"],
            fontSize=15,
            leading=19,
            fontName="DejaVuSans-Bold",
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocHeading3",
            parent=styles["Heading3"],
            fontSize=13,
            leading=17,
            fontName="DejaVuSans-Bold",
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocSectionHeading",
            parent=styles["Heading3"],
            fontSize=12,
            leading=16,
            spaceBefore=4,
            spaceAfter=6,
            fontName="DejaVuSans-Bold",
            fallbackFonts=fallback_fonts,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocCode",
            parent=styles["Code"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#f9fafb"),
            spaceAfter=0,
            fontName=mono_font,
            fallbackFonts=fallback_fonts,
        )
    )
    return styles


def _register_fonts() -> dict[str, list[str] | str]:
    """Register body, mono, and optional emoji fonts.

    Returns a mapping of font roles so styles can reference fallbacks.
    """

    logger = None
    try:  # Avoid requiring an application context
        logger = current_app.logger
    except Exception:  # pragma: no cover - only hit without Flask context
        pass

    search_paths = [
        Path(__file__).resolve().parent / "fonts",
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/share/fonts/truetype/noto"),
        Path("/usr/local/share/fonts"),
    ]

    def find_font(filename: str) -> Path | None:
        for base in search_paths:
            candidate = base / filename
            if candidate.exists():
                return candidate
        return None

    base_fonts = {
        "body": ("DejaVuSans", "DejaVuSans.ttf"),
        "body_bold": ("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"),
        "mono": ("DejaVuSansMono", "DejaVuSansMono.ttf"),
    }
    registered: dict[str, str] = {}
    for role, (name, filename) in base_fonts.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            font_path = find_font(filename)
            if font_path:
                pdfmetrics.registerFont(TTFont(name, str(font_path)))
            elif logger:
                logger.warning("Font %s not found; falling back to defaults", name)

        if name in pdfmetrics.getRegisteredFontNames():
            registered[role] = name
        elif role == "mono":
            registered[role] = "Courier"
        else:
            registered[role] = "Helvetica"

    emoji_candidates = [
        ("NotoColorEmoji", "NotoColorEmoji.ttf"),
        ("NotoEmoji", "NotoEmoji-Regular.ttf"),
        ("OpenMoji", "OpenMoji-Black.ttf"),
        ("Twemoji", "TwitterColorEmoji-SVGinOT.ttf"),
    ]

    emoji_fonts: list[str] = []
    for name, filename in emoji_candidates:
        if name in pdfmetrics.getRegisteredFontNames():
            emoji_fonts.append(name)
            continue

        font_path = find_font(filename)
        if font_path:
            try:
                pdfmetrics.registerFont(TTFont(name, str(font_path)))
                emoji_fonts.append(name)
            except Exception:
                # Skip fonts ReportLab cannot handle (e.g., unsupported emoji formats)
                continue

    return {"body": registered["body"], "mono": registered["mono"], "emoji_fallbacks": emoji_fonts}
