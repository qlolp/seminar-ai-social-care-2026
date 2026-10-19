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

# подряд идущие сноски — одним индексом через запятую, чтобы номера не склеивались
frag = re.sub(r'(?:<sup>\d+</sup>){2,}', lambda m: '<sup>' + ', '.join(re.findall(r'\d+', m.group(0))) + '</sup>', frag)

heads = re.findall(r'<h1[^>]*>(.*?)</h1>', frag, re.S)
toc_entries = [re.sub(r'<[^>]+>', '', h).strip() for h in heads]

SPARK = '<svg class="spark" viewBox="0 0 100 100"><path d="M50 0 L60 38 L85 15 L62 40 L100 50 L62 60 L85 85 L60 62 L50 100 L40 62 L15 85 L38 60 L0 50 L38 40 L15 15 L40 38 Z"/></svg>'

PART_FULL_RE = re.compile(r'^(Часть [IVX]+\..*|Приложения)')
PART_RE = re.compile(r'^(Часть [IVX]+\..*|Приложения|Список источников)')
PART_DESC = {
 'Часть I. Основания для решений': 'Исходная позиция отрасли, три класса систем, существующие практики, карта задач и рабочий словарь. Разделы 3–8.',
 'Часть II. Шесть прикладных направлений': 'Документы, правовая рамка, видеоаналитика, наблюдение за состоянием, голосовые помощники, обучение персонала и управленческая аналитика. Разделы 9–15.',
 'Часть III. Внедрение': 'Дорожная карта на двенадцать месяцев, правовой контур, работа с жителями и персоналом, этика, безопасность данных и экономика. Разделы 16–22.',
 'Часть IV. Честные ограничения': 'Где искусственный интеллект не нужен, типовые ошибки, запретная зона и критерии отказа. Разделы 23–25.',
 'Часть V. Учебные кейсы': 'Четырнадцать учебных кейсов с вопросами для разбора и опорным комментарием — материал семинара и внутреннего обучения.',
 'Приложения': 'Семнадцать приложений: приказы, регламенты, согласия, паспорта пилота и показателя, журналы, сценарии тренажёра, шаблоны отчётов. Формы — проекты для адаптации юристом учреждения.'}
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
  <div class="cover-kicker">Межрегиональный методический семинар-совещание</div>
  <div class="cover-series">Пространство новых идей 2.0</div>
  <div class="cover-title">Искусственный интеллект в&nbsp;домах социального обслуживания</div>
  <div class="cover-rule"></div>
  <p class="cover-sub">Методический доклад: карта применений, принцип «человек в&nbsp;контуре» и критерии отказа. Для руководителей стационарных организаций социального обслуживания.</p>
  <div class="cover-meta">
    <div>Санкт-Петербург · 25–27 августа 2026 года</div>
    <div>Министерство труда и социальной защиты Российской Федерации</div>
    <div>Комитет по социальной политике Санкт-Петербурга</div>
  </div>
  <div class="cover-aud">Аудитория: директора, заместители и врачи стационарных учреждений из 51 субъекта Российской Федерации. Редакция текста: 16 октября 2026 года.</div>
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

FONTS = """
<style>
@font-face { font-family:'Noto Serif'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'); font-weight:400; font-style:normal; }
@font-face { font-family:'Noto Serif'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf'); font-weight:700; font-style:normal; }
@font-face { font-family:'Noto Serif'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf'); font-weight:400; font-style:italic; }
@font-face { font-family:'Noto Serif'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerif-BoldItalic.ttf'); font-weight:700; font-style:italic; }
@font-face { font-family:'Noto Serif Display'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf'); font-weight:400; font-style:normal; }
@font-face { font-family:'Noto Serif Display'; src:url('file:///usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf'); font-weight:700; font-style:normal; }
@font-face { font-family:'Inter'; src:url('file:///usr/share/fonts/truetype/macos/Inter-Regular.ttf'); font-weight:400; font-style:normal; }
@font-face { font-family:'Inter'; src:url('file:///usr/share/fonts/truetype/macos/Inter-Medium.ttf'); font-weight:500; font-style:normal; }
@font-face { font-family:'Inter'; src:url('file:///usr/share/fonts/truetype/macos/Inter-SemiBold.ttf'); font-weight:600; font-style:normal; }
@font-face { font-family:'Inter'; src:url('file:///usr/share/fonts/truetype/macos/Inter-Bold.ttf'); font-weight:700; font-style:normal; }
</style>
"""

CSS = """
<style>
@page {
  size: A4;
  margin: 22mm 20mm 20mm 20mm;
  background: #FFFdf8;
  @top-left {
    content: string(chapter);
    font-family: Inter, sans-serif;
    font-size: 8pt;
    color: #7A7468;
    letter-spacing: 0.02em;
  }
  @top-right {
    content: "Методический доклад · 2026";
    font-family: Inter, sans-serif;
    font-size: 8pt;
    color: #7A7468;
  }
  @bottom-left {
    content: "Искусственный интеллект в домах социального обслуживания";
    font-family: Inter, sans-serif;
    font-size: 8pt;
    color: #9A9488;
  }
  @bottom-right {
    content: counter(page);
    font-family: Inter, sans-serif;
    font-size: 10pt;
    font-weight: 600;
    color: #7A2E22;
  }
}
@page cover {
  margin: 0;
  background: #F4EFE6;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-right { content: none; }
  @bottom-left { content: none; }
}
@page part {
  margin: 0;
  background: #F4EFE6;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-right { content: none; }
  @bottom-left { content: none; }
}

html { font-size: 11pt; }
body {
  font-family: "Noto Serif", "Liberation Serif", serif;
  font-size: 11pt;
  line-height: 1.62;
  text-align: left;
  color: #1C1917;
  background: #FFFdf8;
}
p, li { text-align: justify; hyphens: auto; }
/* Inter подменяет скобки и тире рядом с заглавными на контекстные глифы без Юникода — в тексте PDF они превращаются в «квадраты» */
body, table, h1, h2, h3, h4, sup, .callout strong { font-variant-ligatures: no-contextual; font-feature-settings: "calt" 0, "case" 0; }
p { margin: 0 0 8pt; orphans: 3; widows: 3; }

.spark { width: 10pt; height: 10pt; fill: #7A2E22; }
.cover {
  page: cover;
  page-break-after: always;
  min-height: 240mm;
  height: auto;
  background: #F4EFE6;
  color: #1C1917;
  padding: 24mm 26mm 20mm;
  box-sizing: border-box;
}
.cover-kicker {
  font-family: Inter, sans-serif;
  font-size: 9.5pt;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7A2E22;
  margin-bottom: 8pt;
}
.cover-series {
  font-family: "Noto Serif Display", "Noto Serif", serif;
  font-size: 15pt;
  color: #1C1917;
  margin-bottom: 42mm;
}
.cover-title {
  font-family: "Noto Serif Display", "Noto Serif", serif;
  font-size: 34pt;
  font-weight: 700;
  line-height: 1.16;
  max-width: 168mm;
  letter-spacing: -0.01em;
}
.cover-rule { width: 42pt; height: 2pt; background: #7A2E22; margin: 22pt 0 18pt; }
.cover-sub {
  font-size: 13pt;
  line-height: 1.5;
  color: #3F3A34;
  max-width: 155mm;
  text-align: left;
}
.cover-meta {
  font-family: Inter, sans-serif;
  font-size: 10pt;
  line-height: 1.55;
  color: #5C574E;
  margin-top: 28mm;
}
.cover-aud {
  font-family: Inter, sans-serif;
  font-size: 9.5pt;
  line-height: 1.45;
  color: #7A7468;
  margin-top: 14pt;
  border-top: 0.6pt solid #D8D1C4;
  padding-top: 10pt;
  max-width: 155mm;
}

h1 {
  font-family: "Noto Serif Display", "Noto Serif", serif;
  font-size: 19pt;
  font-weight: 700;
  color: #1C1917;
  page-break-before: always;
  margin: 0 0 10pt;
  text-align: left;
  line-height: 1.22;
  page-break-after: avoid;
  string-set: chapter content();
}
h1::after { content: ""; display: block; width: 36pt; height: 2pt; background: #7A2E22; margin-top: 7pt; }
h1.part { background: none; color: #1C1917; font-size: 20pt; padding: 0; border-bottom: none; margin-top: 0; }
h2 {
  font-family: "Noto Serif", serif;
  font-size: 13.5pt;
  font-weight: 700;
  color: #1C1917;
  margin: 15pt 0 5pt;
  text-align: left;
  page-break-after: avoid;
  break-after: avoid;
  padding-left: 9pt;
  border-left: 2.5pt solid #7A2E22;
}
h3 {
  font-family: Inter, sans-serif;
  font-size: 10.5pt;
  color: #7A2E22;
  margin: 11pt 0 4pt;
  font-weight: 600;
  page-break-after: avoid;
  break-after: avoid;
}

table { border-collapse: collapse; width: 100%; font-family: Inter, sans-serif; font-size: 9.2pt; margin: 10pt 0; page-break-inside: auto; background: #FFFFFF; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
td, th { border: 0.6pt solid #D8D1C4; padding: 4.5pt 6pt; vertical-align: top; text-align: left; line-height: 1.35; overflow-wrap: break-word; word-break: normal; hyphens: auto; }
th { background: #F4EFE6; color: #1C1917; font-size: 8.8pt; font-weight: 600; overflow-wrap: normal; word-break: normal; }
tr:nth-child(even) td { background: #FAF7F1; }

sup { font-size: 7.5pt; color: #7A2E22; font-weight: 700; font-family: Inter, sans-serif; }
a { color: #1C1917; text-decoration: none; overflow-wrap: anywhere; word-break: break-all; }
blockquote { margin: 8pt 0; padding: 8pt 12pt; background: #F4EFE6; border-left: 2.5pt solid #7A2E22; font-style: italic; color: #3F3A34; }
ul, ol { margin: 0 0 7pt 0; padding-left: 18pt; }
li { margin-bottom: 3pt; }
li::marker { color: #7A2E22; font-weight: 600; }
hr { border: none; border-top: 0.6pt solid #D8D1C4; margin: 12pt 0; }

.lead {
  font-family: "Noto Serif", serif;
  font-size: 10.6pt;
  line-height: 1.5;
  color: #2A2622;
  background: #F4EFE6;
  border-left: 3pt solid #7A2E22;
  padding: 8pt 11pt;
  margin: 0 0 12pt;
  page-break-inside: avoid;
}
.lead p { margin: 0; text-align: left; }
.callout {
  margin: 9pt 0 11pt;
  padding: 8pt 11pt;
  page-break-inside: avoid;
  background: #FFFFFF;
  border: 0.6pt solid #D8D1C4;
}
.callout.thesis { border-left: 3pt solid #7A2E22; background: #FBF6EF; }
.callout.example { border-left: 3pt solid #3D5A4C; background: #F3F6F3; }
.callout p { margin: 0; text-align: left; }
.callout strong { font-family: Inter, sans-serif; font-size: 9pt; letter-spacing: 0.04em; text-transform: uppercase; color: #7A2E22; }

.toc { page-break-after: always; }
.toc-title {
  font-family: "Noto Serif Display", "Noto Serif", serif;
  font-size: 20pt;
  font-weight: 700;
  color: #1C1917;
  margin-bottom: 12pt;
  padding-bottom: 6pt;
  border-bottom: 1.5pt solid #7A2E22;
}
.toc table { font-size: 10pt; background: none; font-family: Inter, sans-serif; }
.toc td { border: none; border-bottom: 0.5pt dotted #C9C1B4; padding: 3.2pt 4pt; text-align: left !important; }
.toc td a { display: inline; text-align: left; overflow-wrap: normal; word-break: normal; hyphens: manual; }
.toc-p { width: 36pt; text-align: right; color: #7A2E22; font-weight: 600; }
.toc-part td { background: #F4EFE6; font-weight: 700; color: #1C1917; padding-top: 7pt; }

.page-inf h1, .page-inf h2 { page-break-before: avoid; }
h2.case { margin-top: 0; }
.casebox { page-break-inside: avoid; margin-bottom: 16pt; }
.casebox + .casebox { border-top: 1pt solid #D8D1C4; padding-top: 14pt; }
h1 + .casebox h2.case { margin-top: 6pt; }

.part-page {
  page: part;
  page-break-before: always;
  page-break-after: always;
  min-height: 220mm;
  height: auto;
  box-sizing: border-box;
  background: #F4EFE6;
  color: #1C1917;
  padding: 36mm 28mm 28mm;
}
.part-page .pp-kick {
  display: flex;
  align-items: center;
  gap: 9pt;
  font-family: Inter, sans-serif;
  font-size: 10.5pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #7A2E22;
  font-weight: 600;
  margin-bottom: 20pt;
}
.part-page .pp-kick .spark { width: 12pt; height: 12pt; }
.part-page h1 { page-break-before: avoid; border-bottom: none; color: #1C1917; font-size: 32pt; line-height: 1.16; margin: 0; padding-bottom: 0; }
.part-page h1::after { display: none; }
.part-page .pp-rule { width: 42pt; height: 2pt; background: #7A2E22; margin: 24pt 0 20pt; }
.part-page .pp-desc { font-size: 13pt; line-height: 1.6; color: #3F3A34; max-width: 150mm; text-align: left; }
</style>
"""

html = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>Искусственный интеллект в домах социального обслуживания</title>{FONTS}{CSS}{CSS_COLOR}</head><body>
{COVER}
{TOC_HTML}
{frag}
</body></html>"""

open(f'{OUT}/_report_color.html', 'w', encoding='utf-8').write(html)
print('color HTML written:', len(html), 'chars; TOC entries:', len(toc_rows), '; base=', BASE)
