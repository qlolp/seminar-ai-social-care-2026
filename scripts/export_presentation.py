# -*- coding: utf-8 -*-
"""Render presentation/*.page + .pptd to a 960×540 PDF via Chrome headless."""
from __future__ import annotations

import html as html_lib
import math
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRES = ROOT / "presentation"
MANIFEST = PRES / "презентация_ии.pptd"
OUT_PDF = PRES / "Презентация_ИИ_в_домах_соцобслуживания.pdf"
OUT_HTML = PRES / "_export.html"


def resolve_color(value, colors):
    if value is None:
        return None
    if isinstance(value, dict):
        return resolve_color(value.get("color"), colors)
    s = str(value)
    if s.startswith("$"):
        return colors.get(s[1:], s)
    return s


def merge_style(content, theme):
    styles = theme.get("textStyles", {})
    colors = theme.get("colors", {})
    out = {}
    ref = content.get("style")
    if isinstance(ref, str) and ref.startswith("$"):
        base = styles.get(ref[1:], {})
        out.update(base)
    for key in (
        "fontSize",
        "bold",
        "color",
        "fontFamily",
        "lineHeight",
        "letterSpacing",
        "align",
    ):
        if key in content:
            out[key] = content[key]
    if "color" in out:
        out["color"] = resolve_color(out["color"], colors)
    return out


def css_font(style):
    family = style.get("fontFamily") or "Noto Sans"
    if family == "PT Serif":
        family = "Noto Serif, PT Serif, Tinos, Liberation Serif, serif"
    else:
        family = f"{family}, Noto Sans, sans-serif"
    size = style.get("fontSize") or 14
    weight = "700" if style.get("bold") else "400"
    lh = style.get("lineHeight") or 1.35
    ls = style.get("letterSpacing")
    color = style.get("color") or "#141413"
    css = (
        f"font-family:{family};font-size:{size}px;font-weight:{weight};"
        f"line-height:{lh};color:{color};"
    )
    if ls:
        css += f"letter-spacing:{ls}px;"
    return css


def flex_align(align):
    if not align:
        return "flex-start", "flex-start"
    if isinstance(align, dict):
        h = align.get("h") or align.get(0) or "left"
        v = align.get("v") or align.get(1) or "top"
    elif isinstance(align, (list, tuple)):
        h = align[0] if len(align) > 0 else "left"
        v = align[1] if len(align) > 1 else "top"
    else:
        h, v = "left", "top"
    hm = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(h, "flex-start")
    vm = {"top": "flex-start", "middle": "center", "bottom": "flex-end"}.get(v, "flex-start")
    return hm, vm


def text_html(raw):
    if raw is None:
        return ""
    s = str(raw)
    if "<" in s and any(tag in s for tag in ("<p", "<strong", "<em", "<br", "<ul", "<li")):
        return s
    return html_lib.escape(s).replace("\n", "<br>")


def box_style(bounds, extra=""):
    x, y, w, h = bounds
    return (
        f"position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;"
        f"box-sizing:border-box;{extra}"
    )


def render_text(el, theme):
    content = el.get("content") or {}
    style = merge_style(content, theme)
    align = content.get("align") or style.get("align")
    hm, vm = flex_align(align)
    ta = {"flex-start": "left", "center": "center", "flex-end": "right"}[hm]
    extra = (
        f"display:flex;flex-direction:column;align-items:{hm};justify-content:{vm};"
        f"text-align:{ta};overflow:hidden;{css_font(style)}"
    )
    return f'<div style="{box_style(el["bounds"], extra)}">{text_html(content.get("text"))}</div>'


def render_shape(el, theme):
    colors = theme.get("colors", {})
    fill = el.get("fill") or {}
    color = resolve_color(fill.get("color") if isinstance(fill, dict) else fill, colors) or "transparent"
    return f'<div style="{box_style(el["bounds"], f"background:{color};")}"></div>'


def render_table(el, theme):
    colors = theme.get("colors", {})
    x, y, w, h = el["bounds"]
    cols = el.get("columnWidths") or []
    rows = el.get("rowHeights") or []
    data = el.get("rows") or []
    st = el.get("style") or {}
    cell = st.get("cellStyle") or {}
    first = st.get("firstRowStyle") or {}
    border = cell.get("border") or []
    border_color = colors.get("line", "#E5E2D8")
    if isinstance(border, list) and len(border) > 2 and isinstance(border[2], dict):
        border_color = resolve_color(border[2].get("color"), colors) or border_color
    font = cell.get("fontSize") or 12.5
    lh = cell.get("lineHeight") or 1.3
    html = [
        f'<table style="{box_style(el["bounds"])}border-collapse:collapse;table-layout:fixed;">'
    ]
    for ri, row in enumerate(data):
        rh = rows[ri] * h if ri < len(rows) else h / max(len(data), 1)
        html.append(f'<tr style="height:{rh:.1f}px;">')
        for ci, cell_data in enumerate(row):
            cw = cols[ci] * w if ci < len(cols) else w / max(len(row), 1)
            txt = cell_data.get("text") if isinstance(cell_data, dict) else str(cell_data)
            bg = ""
            color = colors.get("text", "#141413")
            weight = "400"
            if ri == 0 and first:
                bg = f"background:{resolve_color(first.get('fill'), colors) or colors.get('primary')};"
                color = resolve_color(first.get("color"), colors) or "#FFFFFF"
                weight = "700"
                font_use = first.get("fontSize") or font
            else:
                font_use = font
            html.append(
                f'<td style="width:{cw:.1f}px;padding:4px 8px;vertical-align:middle;'
                f'border-bottom:1px solid {border_color};font-family:Noto Sans,sans-serif;'
                f'font-size:{font_use}px;line-height:{lh};color:{color};font-weight:{weight};'
                f'{bg}">{html_lib.escape(str(txt))}</td>'
            )
        html.append("</tr>")
    html.append("</table>")
    return "".join(html)


def _series_color(series, theme, fallback):
    colors = theme.get("colors", {})
    fill = series.get("fill") or (series.get("marker") or {}).get("fill") or series.get("lineColor")
    return resolve_color(fill, colors) or fallback


def render_chart(el, theme):
    colors = theme.get("colors", {})
    x, y, w, h = el["bounds"]
    data = el.get("data") or {}
    cols = data.get("cols") or []
    rows = data.get("rows") or []
    series = el.get("series") or []
    if not series:
        return ""
    kind = series[0].get("type")
    pad_l, pad_r, pad_t, pad_b = 48, 16, 12, 36
    iw, ih = w - pad_l - pad_r, h - pad_t - pad_b
    svg = [
        f'<svg style="{box_style(el["bounds"])}" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]

    def gx(v, vmin, vmax):
        return pad_l + (0 if vmax == vmin else (v - vmin) / (vmax - vmin) * iw)

    def gy(v, vmin, vmax):
        return pad_t + ih - (0 if vmax == vmin else (v - vmin) / (vmax - vmin) * ih)

    if kind == "scatter":
        xa = el.get("xAxis") or {}
        ya = el.get("yAxis") or {}
        xmin, xmax = xa.get("min", 0), xa.get("max", 6)
        ymin, ymax = ya.get("min", 0), ya.get("max", 6)
        grid = resolve_color((xa.get("gridLine") or {}).get("color"), colors) or "#E5E2D8"
        for i in range(int(xmin), int(xmax) + 1):
            xx = gx(i, xmin, xmax)
            svg.append(f'<line x1="{xx}" y1="{pad_t}" x2="{xx}" y2="{pad_t+ih}" stroke="{grid}" stroke-width="1"/>')
        for i in range(int(ymin), int(ymax) + 1):
            yy = gy(i, ymin, ymax)
            svg.append(f'<line x1="{pad_l}" y1="{yy}" x2="{pad_l+iw}" y2="{yy}" stroke="{grid}" stroke-width="1"/>')
        mute = colors.get("muted", "#8A8578")
        if xa.get("title"):
            svg.append(
                f'<text x="{pad_l+iw/2}" y="{h-6}" text-anchor="middle" fill="{mute}" '
                f'font-size="11" font-family="Noto Sans">{html_lib.escape(xa["title"])}</text>'
            )
        if ya.get("title"):
            svg.append(
                f'<text x="12" y="{pad_t+ih/2}" text-anchor="middle" fill="{mute}" '
                f'font-size="11" font-family="Noto Sans" transform="rotate(-90 12 {pad_t+ih/2})">'
                f'{html_lib.escape(ya["title"])}</text>'
            )
        defaults = ["#D97757", "#B85C3D", "#4A463C", "#8A8578", "#D9A28B", "#6E6A5E"]
        legend = []
        for si, s in enumerate(series):
            enc = s.get("encode") or {}
            cx, cy = enc.get("x"), enc.get("y")
            if not rows or cx not in cols or cy not in cols:
                continue
            xi, yi = cols.index(cx), cols.index(cy)
            color = _series_color(s, theme, defaults[si % len(defaults)])
            xv, yv = float(rows[0][xi]), float(rows[0][yi])
            svg.append(f'<circle cx="{gx(xv,xmin,xmax)}" cy="{gy(yv,ymin,ymax)}" r="7" fill="{color}"/>')
            legend.append((s.get("name") or "", color))
        lx = pad_l
        for name, color in legend:
            svg.append(f'<circle cx="{lx+6}" cy="{h-20}" r="4" fill="{color}"/>')
            svg.append(
                f'<text x="{lx+14}" y="{h-16}" fill="#6E6A5E" font-size="10" '
                f'font-family="Noto Sans">{html_lib.escape(name)}</text>'
            )
            lx += 120

    elif kind == "bar":
        enc0 = series[0].get("encode") or {}
        cat_key = enc0.get("y") if (el.get("yAxis") or {}).get("type") == "category" else enc0.get("x")
        stacked = bool(series[0].get("stack"))
        cats = [r[cols.index(cat_key)] for r in rows] if cat_key in cols else [r[0] for r in rows]
        n = max(len(cats), 1)
        horizontal = (el.get("yAxis") or {}).get("type") == "category"
        values = []
        for s in series:
            enc = s.get("encode") or {}
            key = enc.get("x") if horizontal else enc.get("y")
            idx = cols.index(key) if key in cols else 1
            values.append([float(r[idx]) for r in rows])
        vmax = max((sum(col) if stacked else max(col) for col in zip(*values)), default=1)
        vmax = max(vmax, (el.get("xAxis") or {}).get("max") or 0, 1)
        defaults = ["#D97757", "#4A463C", "#A8A294", "#B85C3D"]
        grid = "#E5E2D8"
        if horizontal:
            bw = ih / n * float(el.get("barWidth") or 0.55)
            for i, cat in enumerate(cats):
                yy = pad_t + (i + 0.5) * (ih / n) - bw / 2
                acc = 0
                for si, series_vals in enumerate(values):
                    val = series_vals[i]
                    ww = val / vmax * iw
                    color = _series_color(series[si], theme, defaults[si % len(defaults)])
                    svg.append(
                        f'<rect x="{pad_l+acc}" y="{yy}" width="{ww}" height="{bw}" fill="{color}"/>'
                    )
                    if (series[si].get("dataLabels") or {}).get("show"):
                        svg.append(
                            f'<text x="{pad_l+acc+ww-8}" y="{yy+bw/2+4}" text-anchor="end" '
                            f'fill="#fff" font-size="12" font-family="Noto Sans">{int(val)}</text>'
                        )
                    acc += ww if stacked else 0
                svg.append(
                    f'<text x="{pad_l-8}" y="{yy+bw/2+4}" text-anchor="end" fill="#4A463C" '
                    f'font-size="11" font-family="Noto Sans">{html_lib.escape(str(cat))}</text>'
                )
        else:
            gap = iw / n
            bw = gap * float(el.get("barWidth") or 0.45)
            for gxline in range(5):
                yy = gy(vmax * gxline / 4, 0, vmax)
                svg.append(f'<line x1="{pad_l}" y1="{yy}" x2="{pad_l+iw}" y2="{yy}" stroke="{grid}"/>')
            for i, cat in enumerate(cats):
                xx = pad_l + i * gap + (gap - bw) / 2
                acc = 0
                for si, series_vals in enumerate(values):
                    val = series_vals[i]
                    hh = val / vmax * ih
                    color = _series_color(series[si], theme, defaults[si % len(defaults)])
                    svg.append(
                        f'<rect x="{xx}" y="{pad_t+ih-acc-hh}" width="{bw}" height="{hh}" fill="{color}"/>'
                    )
                    acc += hh if stacked else 0
                svg.append(
                    f'<text x="{xx+bw/2}" y="{pad_t+ih+16}" text-anchor="middle" fill="#4A463C" '
                    f'font-size="11" font-family="Noto Sans">{html_lib.escape(str(cat))}</text>'
                )
            legend = el.get("legend") or {}
            if legend:
                lx = pad_l
                for si, s in enumerate(series):
                    color = _series_color(s, theme, defaults[si % len(defaults)])
                    svg.append(f'<rect x="{lx}" y="{h-18}" width="10" height="10" fill="{color}"/>')
                    svg.append(
                        f'<text x="{lx+14}" y="{h-9}" fill="#6E6A5E" font-size="10" '
                        f'font-family="Noto Sans">{html_lib.escape(s.get("name") or "")}</text>'
                    )
                    lx += 200

    elif kind == "radar":
        axes = [r[0] for r in rows]
        n = len(axes) or 1
        rmax = (el.get("spokeAxis") or {}).get("max") or 4
        cx, cy = pad_l + iw / 2, pad_t + ih / 2 - 8
        radius = min(iw, ih) * 0.38
        grid = "#E5E2D8"
        for ring in range(1, 5):
            rr = radius * ring / 4
            pts = []
            for i in range(n):
                ang = -math.pi / 2 + 2 * math.pi * i / n
                pts.append(f"{cx+rr*math.cos(ang):.1f},{cy+rr*math.sin(ang):.1f}")
            svg.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{grid}"/>')
        for i, name in enumerate(axes):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            svg.append(
                f'<line x1="{cx}" y1="{cy}" x2="{cx+radius*math.cos(ang)}" '
                f'y2="{cy+radius*math.sin(ang)}" stroke="{grid}"/>'
            )
            svg.append(
                f'<text x="{cx+(radius+18)*math.cos(ang)}" y="{cy+(radius+18)*math.sin(ang)}" '
                f'text-anchor="middle" fill="#4A463C" font-size="11" font-family="Noto Sans">'
                f'{html_lib.escape(str(name))}</text>'
            )
        defaults = ["#A8A294", "#D97757"]
        for si, s in enumerate(series):
            enc = s.get("encode") or {}
            key = enc.get("y")
            idx = cols.index(key) if key in cols else si + 1
            pts = []
            for i, r in enumerate(rows):
                val = float(r[idx])
                ang = -math.pi / 2 + 2 * math.pi * i / n
                rr = radius * val / rmax
                pts.append(f"{cx+rr*math.cos(ang):.1f},{cy+rr*math.sin(ang):.1f}")
            color = _series_color(s, theme, defaults[si % len(defaults)])
            area = s.get("areaColor") or (color + "33")
            svg.append(
                f'<polygon points="{" ".join(pts)}" fill="{area}" stroke="{color}" stroke-width="2"/>'
            )
    else:
        svg.append(
            f'<text x="{w/2}" y="{h/2}" text-anchor="middle" fill="#8A8578" '
            f'font-size="13" font-family="Noto Sans">[{kind}]</text>'
        )

    svg.append("</svg>")
    return "".join(svg)


RENDERERS = {
    "text": render_text,
    "shape": render_shape,
    "table": render_table,
    "chart": render_chart,
}


def render_page(page, theme):
    bg = ((page.get("background") or {}).get("color")) or "$bg"
    bg = resolve_color(bg, theme.get("colors", {}))
    parts = [f'<section class="slide" style="background:{bg}">']
    for el in page.get("elements") or []:
        fn = RENDERERS.get(el.get("elementType"))
        if fn:
            parts.append(fn(el, theme))
    parts.append("</section>")
    return "\n".join(parts)


def build_html(manifest):
    theme = manifest.get("theme") or {}
    slides = []
    for rel in manifest["pages"]:
        page = yaml.safe_load((PRES / rel).read_text(encoding="utf-8"))
        slides.append(render_page(page, theme))
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{html_lib.escape(manifest.get("title") or "Презентация")}</title>
<style>
  @page {{ size: 960px 540px; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #fff; }}
  .slide {{
    width: 960px; height: 540px; position: relative; overflow: hidden;
    page-break-after: always; break-after: page;
  }}
  .slide:last-child {{ page-break-after: auto; }}
  .slide p {{ margin: 0 0 0.55em 0; }}
  .slide p:last-child {{ margin-bottom: 0; }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
</style>
</head>
<body>
{"".join(slides)}
</body>
</html>
"""


def export_pdf(html_path: Path, pdf_path: Path):
    chrome = "google-chrome"
    profile = Path("/tmp/chrome-pres-export")
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--hide-scrollbars",
        f"--user-data-dir={profile}",
        "--crash-dumps-dir=/tmp/chrome-crash",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, cwd=str(PRES), timeout=90)


def main():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    html = build_html(manifest)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML: {OUT_HTML} ({len(manifest['pages'])} slides)")
    try:
        export_pdf(OUT_HTML, OUT_PDF)
    except subprocess.TimeoutExpired:
        if not OUT_PDF.exists() or OUT_PDF.stat().st_size < 10000:
            print("PDF export timed out before a file was written", file=sys.stderr)
            return 1
        print("Chrome timed out after writing PDF (headless hang); file kept")
    except Exception as exc:
        print(f"PDF export failed: {exc}", file=sys.stderr)
        return 1
    print(f"PDF:  {OUT_PDF} ({OUT_PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
