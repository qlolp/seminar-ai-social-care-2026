# -*- coding: utf-8 -*-
"""Сборка _report_full.md из chapters/ с разделителями частей и инфографикой."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_base

BASE = str(resolve_base())
CH = os.path.join(BASE, 'chapters')
OUT = os.path.join(BASE, 'output')
os.makedirs(OUT, exist_ok=True)

def rd(name):
    return open(os.path.join(CH, name), encoding='utf-8').read().strip()

parts = []
parts.append(('raw', '01_titul.md'))
parts.append(('raw', '02_kak_chitat.md'))
parts.append(('h1', 'Часть I. Основания для решений'))
for f in ['03_obektivka.md','04_shest_napravleniy.md']:
    parts.append(('raw', f))
parts.append(('inf', 'map'))
parts.append(('raw', '05_chto_takoe.md'))
parts.append(('inf', 'classes'))
parts.append(('inf', 'hitl'))
parts.append(('raw', '06_praktiki_rf.md'))
parts.append(('raw', '07_zadachi.md'))
parts.append(('inf', 'filters'))
parts.append(('raw', '08_terminy.md'))
parts.append(('h1', 'Часть II. Шесть прикладных направлений'))
parts.append(('raw', '09_dokumenty.md'))
parts.append(('raw', '10_pravo.md'))
parts.append(('inf', 'biom'))
parts.append(('raw', '11_video.md'))
parts.append(('raw', '12_nablyudenie.md'))
parts.append(('inf', 'escal'))
parts.append(('raw', '13_golos.md'))
parts.append(('raw', '14_obuchenie.md'))
parts.append(('raw', '15_analitika.md'))
parts.append(('h1', 'Часть III. Внедрение'))
parts.append(('raw', '16_dorozhnaya.md'))
parts.append(('inf', 'roadmap'))
parts.append(('raw', '17_pravo_kontur.md'))
parts.append(('raw', '18_zhiteli.md'))
parts.append(('raw', '19_personal.md'))
parts.append(('raw', '20_etika.md'))
parts.append(('inf', 'ethics'))
parts.append(('raw', '21_bezopasnost.md'))
parts.append(('raw', '22_ekonomika.md'))
parts.append(('inf', 'tco'))
parts.append(('h1', 'Часть IV. Честные ограничения'))
parts.append(('raw', '23_gde_ne_nuzhen.md'))
parts.append(('raw', '24_oshibki.md'))
parts.append(('inf', 'seven'))
parts.append(('raw', '25_kriterii_otkaza.md'))
parts.append(('inf', 'stop'))
parts.append(('raw', '35_faq.md'))
parts.append(('raw', '26_zaklyuchenie.md'))
parts.append(('h1', 'Часть V. Учебные кейсы'))
parts.append(('raw', '27_keisy_1.md'))
parts.append(('raw', '28_keisy_2.md'))
parts.append(('raw', '37_keisy_3.md'))
parts.append(('raw', '29_pril_1_3.md'))
parts.append(('raw', '30_pril_4_5.md'))
parts.append(('raw', '31_pril_6_7.md'))
parts.append(('raw', '32_pril_8_9.md'))
parts.append(('raw', '33_pril_10_11.md'))
parts.append(('raw', '36_pril_12_14.md'))
parts.append(('raw', '38_pril_15_16.md'))
parts.append(('raw', '39_pril_17.md'))
parts.append(('raw', '34_istochniki.md'))

out = []
for kind, val in parts:
    if kind == 'h1':
        out.append('\n# ' + val + '\n')
    elif kind == 'inf':
        out.append('\n[[INF:%s]]\n' % val)
    else:
        out.append(rd(val) + '\n')

md = '\n'.join(out)
open(os.path.join(OUT, '_report_full.md'), 'w', encoding='utf-8').write(md)
print('assembled:', len(md), 'chars,', len(md.split()), 'words; base=', BASE)
