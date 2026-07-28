# -*- coding: utf-8 -*-
"""Журнальная цветная сборка доклада об ИИ: _report_full.md → HTML → PDF."""
import os, re, sys, json, subprocess

BASE = '/mnt/agents/output/seminar_ai_2026'
OUT  = os.path.join(BASE, 'output')
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from figures_color import CSS_COLOR
from figures_inf import INF

md = open(f'{OUT}/_report_full.md', encoding='utf-8').read()

env = dict(os.environ); env['LANG'] = 'C.UTF-8'
frag = subprocess.run(
    ['pandoc', '-f', 'markdown+superscript+autolink_bare_uris', '-t', 'html', '--wrap=none'],
    input=md, capture_output=True, text=True, env=env).stdout

# убрать титульный фрагмент (заменяется цветной обложкой)
frag = re.sub(r'^.*?<h1[^>]*>2\.', '<h1>2.', frag, count=1, flags=re.S)

frag = re.sub(r'<p>\[\[INF:([a-z0-9_]+)\]\]</p>', lambda m: INF.get(m.group(1), ''), frag)

heads = re.findall(r'<h1[^>]*>(.*?)</h1>', frag, re.S)
toc_entries = [re.sub(r'<[^>]+>', '', h).strip() for h in heads]

PART_RE = re.compile(r'^(Часть [IVX]+\..*|Приложения|Список источников)')
def add_anchor(m):
    t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    aid = re.sub(r'[^0-9A-Za-zА-Яа-я]+', '_', t)[:60]
    cls = ' class="part"' if PART_RE.match(t) else ''
    return f'<h1 id="{aid}"{cls}>{m.group(1)}</h1>'
frag = re.sub(r'<h1[^>]*>(.*?)</h1>', add_anchor, frag)
frag = re.sub(r'<h2[^>]*>(Кейс \d+\..*?)</h2>', lambda m: '<h2 class="case">' + m.group(1) + '</h2>', frag)

COVER = """
<div class="cover">
  <div class="cover-kick">МЕЖРЕГИОНАЛЬНЫЙ МЕТОДИЧЕСКИЙ СЕМИНАР-СОВЕЩАНИЕ<br>«ПРОСТРАНСТВО НОВЫХ ИДЕЙ 2.0»</div>
  <div class="cover-rule"></div>
  <div class="cover-title">ИСКУССТВЕННЫЙ<br>ИНТЕЛЛЕКТ<br>В ДОМАХ<br>СОЦИАЛЬНОГО<br>ОБСЛУЖИВАНИЯ</div>
  <div class="cover-sub">Практическое руководство для руководителей: что внедрять, чего не делать и с чего начать в понедельник</div>
  <div class="cover-meta">Санкт-Петербург · 25–27 августа 2026 года<br>Министерство труда и социальной защиты Российской Федерации · Комитет по социальной политике Санкт-Петербурга</div>
  <div class="cover-aud">Доклад для руководителей стационарных организаций социального обслуживания из 51 субъекта Российской Федерации</div>
</div>
"""
frag = COVER + frag

toc_pages = {}
if os.path.exists(f'{OUT}/toc_pages_color.json'):
    toc_pages = json.load(open(f'{OUT}/toc_pages_color.json'))

toc_rows = []
for t in toc_entries:
    aid = re.sub(r'[^0-9A-Za-zА-Яа-я]+', '_', t)[:60]
    pg = toc_pages.get(aid, '')
    part = ' class="toc-part"' if PART_RE.match(t) else ''
    toc_rows.append(f'<tr{part}><td class="toc-t"><a href="#{aid}">{t}</a></td><td class="toc-p">{pg}</td></tr>')
TOC_HTML = ('<div class="toc"><p class="toc-title">Содержание</p><table>'
            + ''.join(toc_rows) + '</table></div>')

CSS = """
<style>
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
  @bottom-right { content: counter(page); font-family:'MiSans',sans-serif; font-size:10pt; color:#2F5D50; }
  @bottom-left { content: 'Искусственный интеллект в домах социального обслуживания · 2026'; font-family:'MiSans',sans-serif; font-size:8.5pt; color:#9AA7A1; } }
@page cover { margin:0; @bottom-right{content:none} @bottom-left{content:none} }
html { font-size: 11.5pt; }
body { font-family:'MiSans','PT Sans',sans-serif; font-size:11.5pt; line-height:1.68; text-align:left; color:#20242A; }
p, li { text-align:justify; }
p { margin:0 0 8.5pt; orphans:2; widows:2; }

.cover { page: cover; page-break-after:always; height:297mm; background:linear-gradient(160deg,#1F3D33 0%,#2F5D50 55%,#3A6E5D 100%); color:#fff; padding:30mm 24mm; box-sizing:border-box; }
.cover-kick { font-size:10.5pt; letter-spacing:2.5pt; color:#DCE6E0; line-height:1.7; }
.cover-rule { width:90pt; height:3.5pt; background:#B57517; margin:14pt 0 22pt; }
.cover-title { font-size:34pt; font-weight:bold; line-height:1.12; letter-spacing:0.5pt; }
.cover-sub { font-size:13.5pt; line-height:1.5; color:#DCE6E0; margin-top:20pt; max-width:155mm; }
.cover-meta { font-size:10.5pt; line-height:1.6; color:#B9C9C1; margin-top:26pt; }
.cover-aud { font-size:10pt; color:#9DB4AB; margin-top:12pt; border-top:1pt solid #4E7A6C; padding-top:10pt; }

h1 { font-size:17pt; color:#1F3D33; page-break-before:always; margin:0 0 4pt; text-align:left; line-height:1.25; padding-bottom:6pt; border-bottom:2.5pt solid #B57517; page-break-after:avoid; }
h1.part { background:linear-gradient(135deg,#1F3D33,#2F5D50); color:#fff; font-size:20pt; padding:26pt 20pt; border-bottom:none; margin-top:40pt; }
h1.part + p, h1.part + p + p { font-size:11.5pt; }
h2 { font-size:13pt; color:#2F5D50; margin:15pt 0 5pt; text-align:left; page-break-after:avoid; break-after:avoid; padding-left:9pt; border-left:3.5pt solid #B57517;}
h3 { font-size:11.5pt; color:#B57517; margin:11pt 0 4pt; font-style:normal; font-weight:bold; page-break-after:avoid; break-after:avoid;}

table { border-collapse:collapse; width:100%; font-size:10pt; margin:10pt 0; page-break-inside:auto; }
tr { page-break-inside:avoid; }
thead { display:table-header-group; }
td, th { border:0.7pt solid #C7BFAF; padding:4pt 6pt; vertical-align:top; text-align:left; line-height:1.3; overflow-wrap:anywhere; word-break:break-word; }
th { background:#2F5D50; color:#fff; font-size:9.5pt; overflow-wrap:normal; word-break:normal; }
tr:nth-child(even) td { background:#F4F1EA; }

sup { font-size:8pt; color:#B57517; font-weight:bold; }
a { color:#1F3D33; text-decoration:none; overflow-wrap:anywhere; word-break:break-all; }
blockquote { margin:7pt 14pt; padding:8pt 12pt; background:#F2F5F3; border-left:3.5pt solid #2F5D50; font-style:italic; color:#37423C; }
ul, ol { margin:0 0 7pt 0; padding-left:20pt; }
li { margin-bottom:3pt; }
li::marker { color:#B57517; font-weight:bold; }
hr { border:none; border-top:1pt solid #C7BFAF; margin:12pt 0; }

.toc { page-break-after:always; }
.toc-title { font-size:17pt; font-weight:bold; color:#1F3D33; margin-bottom:12pt; padding-bottom:6pt; border-bottom:2.5pt solid #B57517; }
.toc table { font-size:10pt; }
.toc td { border:none; border-bottom:0.5pt dotted #B9A77F; padding:3pt 4pt; text-align:left !important; }
.toc td a { display:inline; text-align:left; }
.toc-p { width:40pt; text-align:right; color:#2F5D50; font-weight:bold; }
.toc-part td { background:#EEF4F1; font-weight:bold; color:#1F3D33; padding-top:6pt; }

.page-inf h1, .page-inf h2 { page-break-before:avoid; }
h2.case { page-break-before:always; margin-top:0; }
</style>
"""

html = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>Искусственный интеллект в домах социального обслуживания — журнальная версия</title>{CSS}{CSS_COLOR}</head><body>
{TOC_HTML}
{frag}
</body></html>"""

open(f'{OUT}/_report_color.html', 'w', encoding='utf-8').write(html)
print('color HTML written:', len(html), 'chars; TOC entries:', len(toc_rows))
