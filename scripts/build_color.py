# -*- coding: utf-8 -*-
"""Журнальная цветная сборка доклада об ИИ: _report_full.md → HTML → PDF."""
import os, re, sys, json, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_base

BASE = str(resolve_base())
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

SPARK = '<svg class="spark" viewBox="0 0 100 100"><path d="M50 0 L60 38 L85 15 L62 40 L100 50 L62 60 L85 85 L60 62 L50 100 L40 62 L15 85 L38 60 L0 50 L38 40 L15 15 L40 38 Z"/></svg>'

PART_FULL_RE = re.compile(r'^(Часть [IVX]+\..*|Приложения)')
PART_RE = re.compile(r'^(Часть [IVX]+\..*|Приложения|Список источников)')
PART_DESC = {
 'Часть I. Основания для решений': 'Объективка отрасли, три класса искусственного интеллекта, существующие практики, карта задач и рабочий словарь — всё, чтобы говорить о теме без мифов. Разделы 3–8.',
 'Часть II. Шесть прикладных направлений': 'Документы, правовая рамка, видеоаналитика, наблюдение за состоянием, голосовые помощники, обучение персонала и управленческая аналитика. Разделы 9–15.',
 'Часть III. Внедрение': 'Дорожная карта на двенадцать месяцев, правовой контур пошагово, работа с жителями и персоналом, этика, безопасность данных и экономика. Разделы 16–22.',
 'Часть IV. Честные ограничения': 'Где искусственный интеллект не нужен, типовые ошибки, запретная зона и критерии отказа — части доклада, которые экономят бюджет и репутацию. Разделы 23–25.',
 'Часть V. Учебные кейсы': 'Четырнадцать кейсов с вопросами для разбора и опорными ответами — материал для семинара и внутреннего обучения персонала.',
 'Приложения': 'Семнадцать приложений с формами документов: приказы, регламенты, согласия, паспорта пилота и показателя, журналы, сценарии тренажёра, шаблоны отчётов. Все формы — проекты для адаптации: реквизиты учреждения и региональные требования подставляет ваш юрист.'}
def add_anchor(m):
    t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    aid = re.sub(r'[^0-9A-Za-zА-Яа-я]+', '_', t)[:60]
    cls = ' class="part"' if PART_RE.match(t) else ''
    return f'<h1 id="{aid}"{cls}>{m.group(1)}</h1>'
frag = re.sub(r'<h1[^>]*>(.*?)</h1>', add_anchor, frag)
frag = re.sub(r'<h2[^>]*>(Кейс \d+\..*?)</h2>', lambda m: '<h2 class="case">' + m.group(1) + '</h2>', frag)

def wrap_part(m):
    title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    desc = PART_DESC.get(title, '')
    kick, _, rest = title.partition('. ')
    return ('<div class="part-page"><div class="pp-kick">' + SPARK + '<span>' + kick + '</span></div>'
            + m.group(1) + rest + '</h1>'
            + ('<div class="pp-rule"></div><p class="pp-desc">' + desc + '</p>' if desc else '')
            + '</div>')
frag = re.sub(r'(<h1 id="[^"]*" class="part">)(Часть [IVX]+\..*?|Приложения)</h1>', wrap_part, frag)

# каждый кейс — в .casebox с page-break-inside:avoid:
# короткие кейсы упаковываются по два на страницу, кейс никогда не рвётся
def wrap_cases(html):
    out, buf, inside = [], [], False
    for tok in re.split(r'(?=<h2 class="case">|<h1 )', html):
        starts_case = tok.startswith('<h2 class="case">')
        if inside and (starts_case or tok.startswith('<h1 ')):
            out.append('<div class="casebox">' + ''.join(buf) + '</div>'); buf = []; inside = False
        if starts_case: inside = True
        (buf if inside else out).append(tok)
    if buf: out.append('<div class="casebox">' + ''.join(buf) + '</div>')
    return ''.join(out)
frag = wrap_cases(frag)

COVER = """
<div class="cover">
  <div class="cover-top"><svg class="spark cover-spark" viewBox="0 0 100 100"><path d="M50 0 L60 38 L85 15 L62 40 L100 50 L62 60 L85 85 L60 62 L50 100 L40 62 L15 85 L38 60 L0 50 L38 40 L15 15 L40 38 Z"/></svg><span class="cover-brand">Пространство новых идей 2.0</span></div>
  <div class="cover-kick">МЕЖРЕГИОНАЛЬНЫЙ МЕТОДИЧЕСКИЙ СЕМИНАР-СОВЕЩАНИЕ</div>
  <div class="cover-title">Искусственный интеллект в&nbsp;домах социального обслуживания</div>
  <div class="cover-rule"></div>
  <div class="cover-sub">Что внедрять, чего не делать и&nbsp;с&nbsp;чего начать в&nbsp;понедельник.<br>Практическое руководство для директора, заместителя и врача.</div>
  <div class="cover-meta">Санкт-Петербург · 25–27 августа 2026 года<br>Министерство труда и социальной защиты Российской Федерации · Комитет по социальной политике Санкт-Петербурга</div>
  <div class="cover-aud">Доклад для руководителей стационарных организаций социального обслуживания из 51 субъекта Российской Федерации</div>
</div>
"""
# обложка вставляется в шаблон первой, перед оглавлением

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
@page { size: A4; margin: 20mm 18mm 18mm 18mm; background:#F9F9F7;
  @bottom-right { content: counter(page); font-family:'Noto Sans',sans-serif; font-size:10pt; color:#D97757; }
  @bottom-left { content: 'Искусственный интеллект в домах социального обслуживания · 2026'; font-family:'Noto Sans',sans-serif; font-size:8.5pt; color:#A8A294; } }
@page cover { margin:0; background:#F9F9F7; @bottom-right{content:none} @bottom-left{content:none} }
html { font-size: 11.5pt; }
body { font-family:'Noto Sans',sans-serif; font-size:11.5pt; line-height:1.68; text-align:left; color:#141413; background:#F9F9F7; }
p, li { text-align:justify; }
p { margin:0 0 8.5pt; orphans:2; widows:2; }

.spark { width:11pt; height:11pt; fill:#D97757; }
.cover { page: cover; page-break-after:always; height:297mm; background:#F9F9F7; color:#141413; padding:26mm 26mm; box-sizing:border-box; }
.cover-top { display:flex; align-items:center; gap:8pt; margin-bottom:52mm; }
.cover-spark { width:22pt; height:22pt; }
.cover-brand { font-family:'PT Serif',serif; font-size:16pt; color:#141413; }
.cover-kick { font-size:10pt; letter-spacing:2.8pt; color:#6E6A5E; line-height:1.7; margin-bottom:14pt; }
.cover-title { font-family:'PT Serif',serif; font-size:39pt; line-height:1.14; letter-spacing:0.2pt; max-width:165mm; }
.cover-rule { width:64pt; height:3.5pt; background:#D97757; margin:24pt 0 20pt; }
.cover-sub { font-size:13.5pt; line-height:1.55; color:#4A463C; max-width:150mm; }
.cover-meta { font-size:10.5pt; line-height:1.6; color:#6E6A5E; margin-top:30mm; }
.cover-aud { font-size:10pt; color:#8A8578; margin-top:12pt; border-top:1pt solid #E5E2D8; padding-top:10pt; max-width:150mm; }

h1 { font-family:'PT Serif',serif; font-size:20pt; font-weight:bold; color:#141413; page-break-before:always; margin:0 0 10pt; text-align:left; line-height:1.22; page-break-after:avoid; }
h1::after { content:''; display:block; width:46pt; height:2.5pt; background:#D97757; margin-top:6pt; }
h1.part { background:none; color:#141413; font-size:20pt; padding:0; border-bottom:none; margin-top:0; }
h2 { font-family:'PT Serif',serif; font-size:14pt; font-weight:bold; color:#141413; margin:16pt 0 5pt; text-align:left; page-break-after:avoid; break-after:avoid; padding-left:9pt; border-left:3.5pt solid #D97757; }
h3 { font-size:11pt; color:#B85C3D; margin:11pt 0 4pt; font-style:normal; font-weight:bold; page-break-after:avoid; break-after:avoid; }

table { border-collapse:collapse; width:100%; font-size:10pt; margin:10pt 0; page-break-inside:auto; background:#FFFFFF; }
tr { page-break-inside:avoid; }
thead { display:table-header-group; }
td, th { border:0.7pt solid #E5E2D8; padding:4pt 6pt; vertical-align:top; text-align:left; line-height:1.3; overflow-wrap:anywhere; word-break:break-word; }
th { background:#F2EFE6; color:#141413; font-size:9.5pt; overflow-wrap:normal; word-break:normal; }
tr:nth-child(even) td { background:#FAF8F3; }

sup { font-size:8pt; color:#B85C3D; font-weight:bold; }
a { color:#141413; text-decoration:none; overflow-wrap:anywhere; word-break:break-all; }
blockquote { margin:7pt 14pt; padding:8pt 12pt; background:#F2EFE6; border-left:3.5pt solid #D97757; font-style:italic; color:#4A463C; }
ul, ol { margin:0 0 7pt 0; padding-left:20pt; }
li { margin-bottom:3pt; }
li::marker { color:#D97757; font-weight:bold; }
hr { border:none; border-top:1pt solid #E5E2D8; margin:12pt 0; }

.toc { page-break-after:always; }
.toc-title { font-family:'PT Serif',serif; font-size:20pt; font-weight:bold; color:#141413; margin-bottom:12pt; padding-bottom:6pt; border-bottom:1pt solid #E5E2D8; }
.toc table { font-size:10pt; background:none; }
.toc td { border:none; border-bottom:0.5pt dotted #D8D2C2; padding:3pt 4pt; text-align:left !important; }
.toc td a { display:inline; text-align:left; }
.toc-p { width:40pt; text-align:right; color:#B85C3D; font-weight:bold; }
.toc-part td { background:#F2EFE6; font-weight:bold; color:#141413; padding-top:6pt; }

.page-inf h1, .page-inf h2 { page-break-before:avoid; }
h2.case { margin-top:0; }
.casebox { page-break-inside:avoid; margin-bottom:18pt; }
.casebox + .casebox { border-top:1.5pt solid #E5E2D8; padding-top:16pt; }
h1 + .casebox h2.case { margin-top:6pt; }
@page part { margin:0; background:#F1EDE3; @bottom-right{content:none} @bottom-left{content:none} }
.part-page { page: part; page-break-before:always; page-break-after:always; height:297mm; box-sizing:border-box;
  background:#F1EDE3; color:#141413; padding:52mm 28mm 28mm; }
.part-page .pp-kick { display:flex; align-items:center; gap:9pt; font-size:11pt; letter-spacing:4pt; color:#B85C3D; font-weight:bold; margin-bottom:22pt; }
.part-page .pp-kick .spark { width:15pt; height:15pt; }
.part-page h1 { page-break-before:avoid; border-bottom:none; color:#141413; font-size:34pt; line-height:1.18; margin:0; padding-bottom:0; }
.part-page h1::after { display:none; }
.part-page .pp-rule { width:64pt; height:3.5pt; background:#D97757; margin:26pt 0 24pt; }
.part-page .pp-desc { font-size:13pt; line-height:1.7; color:#4A463C; max-width:150mm; text-align:left; }
</style>
"""

html = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>Искусственный интеллект в домах социального обслуживания — журнальная версия</title>{CSS}{CSS_COLOR}</head><body>
{COVER}
{TOC_HTML}
{frag}
</body></html>"""

open(f'{OUT}/_report_color.html', 'w', encoding='utf-8').write(html)
print('color HTML written:', len(html), 'chars; TOC entries:', len(toc_rows), '; base=', BASE)
