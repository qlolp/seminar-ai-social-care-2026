# -*- coding: utf-8 -*-
"""Второй проход: номера страниц оглавления из собранного PDF."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_base
from pypdf import PdfReader

BASE = resolve_base()
OUT = BASE / 'output'
PDF = OUT / 'Искусственный_интеллект_в_домах_соцобслуживания_доклад.pdf'
HTML = OUT / '_report_color.html'

html = HTML.read_text(encoding='utf-8')
ids = re.findall(r'<h1 id="([^"]+)"', html)
titles = []
for aid in ids:
    m = re.search(rf'<h1 id="{re.escape(aid)}"[^>]*>(.*?)</h1>', html, re.S)
    title = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else aid
    titles.append((aid, title))

reader = PdfReader(str(PDF))
pages = []
for i, page in enumerate(reader.pages, start=1):
    text = re.sub(r'\s+', ' ', page.extract_text() or '').strip()
    pages.append((i, text))

body_start = 1
for i, text in pages:
    if 'Содержание' in text:
        continue
    if '2. Как читать этот доклад' in text:
        body_start = i
        break

found = {}
for aid, title in titles:
    needle = re.sub(r'\s+', ' ', title).strip()
    stem = needle[:42]
    if not stem:
        continue
    hit = None
    for i, text in pages:
        if i < body_start:
            continue
        if 'Содержание' in text:
            continue
        if stem not in text:
            continue
        # prefer a page that starts with the heading (after running header)
        head = text[:220]
        score = 0 if stem in head else 1
        if hit is None or score < hit[1]:
            hit = (i, score)
            if score == 0:
                break
    if hit:
        found[aid] = hit[0]

(OUT / 'toc_pages_color.json').write_text(
    json.dumps(found, ensure_ascii=False, indent=2), encoding='utf-8')
print('toc pages:', len(found), 'of', len(titles),
      '; pdf pages:', len(reader.pages),
      '; body_start=', body_start)
