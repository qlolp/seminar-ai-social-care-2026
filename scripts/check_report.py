# -*- coding: utf-8 -*-
"""Проверка целостности доклада: сноски, список источников, отсылки к разделам и приложениям.

Запуск:  python3 scripts/check_report.py            — проверка глав
         python3 scripts/check_report.py --pdf PATH — плюс проверка готового PDF
Код выхода 1, если найдена хотя бы одна ошибка. Предупреждения выход не меняют.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_base

SOURCES_FILE = '34_istochniki.md'
S_OFFSET = 32          # код [Sxxx] = номер в списке + 32
REF_WORD = r'раздел(?:е|а|ы|ах|ов|ам|ом)?'
NUM = r'\d+(?:\.\d+[а-я]?)?'


def load_chapters(base):
    chap = base / 'chapters'
    return {p.name: p.read_text(encoding='utf-8') for p in sorted(chap.glob('*.md'))}


def check_sources(texts, errors, warnings):
    src = texts.get(SOURCES_FILE)
    if src is None:
        errors.append(f'нет файла chapters/{SOURCES_FILE}')
        return set()
    entries = re.findall(r'(?m)^(\d+)\. (?:\*\*\[S(\d+)\]\*\*)?', src)
    nums = [int(n) for n, _ in entries]
    seen = set()
    for n in nums:
        if n in seen:
            errors.append(f'{SOURCES_FILE}: номер {n} повторяется')
        seen.add(n)
    for expected, n in enumerate(nums, start=1):
        if n != expected:
            errors.append(f'{SOURCES_FILE}: после {expected - 1} идёт {n} — нумерация с пропуском или не по порядку')
            break
    for n, s in entries:
        if s and int(s) != int(n) + S_OFFSET:
            errors.append(f'{SOURCES_FILE}: у источника {n} код S{s}, ожидался S{int(n) + S_OFFSET:03d}')
    return seen


def check_citations(texts, sources, errors, warnings):
    used = set()
    for name, text in texts.items():
        if name == SOURCES_FILE:
            continue
        for ln, line in enumerate(text.splitlines(), start=1):
            for m in re.finditer(r'<sup>([^<]*)</sup>', line):
                for tok in re.split(r'[,\s]+', m.group(1).strip()):
                    if not tok:
                        continue
                    if not tok.isdigit():
                        errors.append(f'{name}:{ln}: сноска «{m.group(0)}» — не номер источника')
                        continue
                    n = int(tok)
                    used.add(n)
                    if n not in sources:
                        errors.append(f'{name}:{ln}: сноска {n} — такого номера нет в списке источников')
    unused = sorted(sources - used)
    if unused:
        warnings.append(f'источники без ссылок в тексте ({len(unused)}): {", ".join(map(str, unused))}')


def headings(texts):
    heads = set()
    appendices = set()
    for text in texts.values():
        heads |= set(re.findall(r'(?m)^#{1,3} (\d+(?:\.\d+[а-я]?)?)\.', text))
        appendices |= {int(x) for x in re.findall(r'(?m)^#{1,2} Приложение (\d+)\.', text)}
    return heads, appendices


def check_cross_refs(texts, errors):
    heads, appendices = headings(texts)
    ref_re = re.compile(REF_WORD + r'\s+(' + NUM + r'(?:\s*(?:,|и|–|-|—)\s*' + NUM + r')*)')
    app_re = re.compile(r'[Пп]риложени(?:е|я|ю|и|ях|ям)\s+(\d+(?:\s*(?:,|и|–|-)\s*\d+)*)')
    for name, text in texts.items():
        if name == SOURCES_FILE:
            continue
        for ln, line in enumerate(text.splitlines(), start=1):
            if line.startswith('#'):
                continue
            for m in ref_re.finditer(line):
                for num in re.findall(NUM, m.group(1)):
                    if num not in heads:
                        errors.append(f'{name}:{ln}: отсылка «{m.group(0)}» — раздела {num} нет')
            for m in app_re.finditer(line):
                for num in re.findall(r'\d+', m.group(1)):
                    if int(num) not in appendices:
                        errors.append(f'{name}:{ln}: отсылка «{m.group(0)}» — приложения {num} нет')


def text_faults(text):
    """Число символов из частной области Юникода и склеенных номеров сносок в тексте PDF."""
    return (len(re.findall('[\\ue000-\\uf8ff]', text)),
            len(re.findall(r'[а-яё]\d{7,}', text)))


REQUIRED_FONTS = ('NotoSerif-Regular', 'Inter-Regular')


def check_fonts(label, fonts, errors):
    for need in REQUIRED_FONTS:
        if not any(need in f for f in fonts):
            errors.append(f'{label}: в PDF нет шрифта {need} — сборка подставила другой шрифт ({", ".join(sorted(fonts))})')


def check_pdf(path, errors):
    try:
        from pypdf import PdfReader
    except ImportError:
        errors.append('для --pdf нужен пакет pypdf')
        return
    reader = PdfReader(str(path))
    fonts = set()
    for page in reader.pages:
        res = page.get('/Resources') or {}
        for f in (res.get('/Font') or {}).values():
            fonts.add(str(f.get_object().get('/BaseFont', '')).split('+')[-1])
    check_fonts(path.name, fonts, errors)
    pua = glued = 0
    for page in reader.pages:
        p, g = text_faults(page.extract_text() or '')
        pua += p
        glued += g
    if pua:
        errors.append(f'{path.name}: {pua} символов без Юникода (скобки и тире превратились в «квадраты»)')
    if glued:
        errors.append(f'{path.name}: {glued} мест, где номера сносок склеились в одно число')


def run(base, pdf=None):
    texts = load_chapters(base)
    errors, warnings = [], []
    sources = check_sources(texts, errors, warnings)
    check_citations(texts, sources, errors, warnings)
    check_cross_refs(texts, errors)
    if pdf:
        check_pdf(pdf, errors)
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', help='проверить и готовый PDF')
    args = ap.parse_args()
    from pathlib import Path
    errors, warnings = run(resolve_base(), Path(args.pdf) if args.pdf else None)
    for w in warnings:
        print('предупреждение:', w)
    for e in errors:
        print('ОШИБКА:', e)
    if errors:
        print(f'НЕ ПРОЙДЕНО: ошибок {len(errors)}')
        return 1
    print('ПРОЙДЕНО: сноски, список источников и отсылки согласованы')
    return 0


if __name__ == '__main__':
    sys.exit(main())
