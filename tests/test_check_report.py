# -*- coding: utf-8 -*-
"""Контрольные ошибки для scripts/check_report.py.

Каждый тест портит копию глав одним способом и требует, чтобы проверка
упала именно с сообщением об этой порче; чистая копия должна проходить.
Запуск: python3 -m unittest discover -s tests
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_report  # noqa: E402


class PlantedFaults(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / 'chapters', self.tmp / 'chapters')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, name, old, new):
        p = self.tmp / 'chapters' / name
        text = p.read_text(encoding='utf-8')
        self.assertIn(old, text, f'контроль устарел: в {name} нет «{old}»')
        p.write_text(text.replace(old, new, 1), encoding='utf-8')

    def errors(self):
        errors, _ = check_report.run(self.tmp)
        return errors

    def assertFailsWith(self, fragment):
        errors = self.errors()
        self.assertTrue(any(fragment in e for e in errors),
                        f'ожидалась ошибка с «{fragment}», получено: {errors}')

    def test_clean_tree_passes(self):
        self.assertEqual(self.errors(), [])

    def test_citation_to_missing_source(self):
        # та же ошибка, что была в 12.2: S-код вместо номера списка
        self.edit('12_nablyudenie.md', '<sup>312</sup>', '<sup>344</sup>')
        self.assertFailsWith('сноска 344 — такого номера нет')

    def test_reference_to_missing_section(self):
        self.edit('15_analitika.md', '(раздел 15.6)', '(раздел 15.9)')
        self.assertFailsWith('раздела 15.9 нет')

    def test_reference_to_missing_appendix(self):
        self.edit('26_zaklyuchenie.md', '(приложение 3)', '(приложение 30)')
        self.assertFailsWith('приложения 30 нет')

    def test_s_code_mismatch(self):
        self.edit('34_istochniki.md', '302. **[S334]**', '302. **[S335]**')
        self.assertFailsWith('код S335, ожидался S334')

    def test_gap_in_source_numbering(self):
        self.edit('34_istochniki.md', '302. **[S334]**', '303. **[S335]**')
        self.assertFailsWith('нумерация с пропуском')

    def test_duplicate_source_number(self):
        self.edit('34_istochniki.md', '302. **[S334]**', '301. **[S333]**')
        self.assertFailsWith('номер 301 повторяется')


class PdfControls(unittest.TestCase):
    def test_liberation_serif_fallback_fails(self):
        # так выглядел PDF, собранный без установленных шрифтов 19.10.2026
        errors = []
        check_report.check_fonts('x.pdf', {'Inter-Regular', 'LiberationSerif', 'LiberationSerif-Bold'}, errors)
        self.assertTrue(any('нет шрифта NotoSerif-Regular' in e for e in errors), errors)

    def test_pdf_reader_finds_missing_inter(self):
        # презентация свёрстана без Inter — чтение шрифтов из настоящего PDF обязано это заметить
        pres = ROOT / 'presentation' / 'Презентация_ИИ_в_домах_соцобслуживания.pdf'
        errors = []
        check_report.check_pdf(pres, errors)
        self.assertTrue(any('нет шрифта Inter-Regular' in e for e in errors), errors)

    def test_text_faults_seen_in_old_pdf(self):
        # строки из текстового слоя PDF до исправления вёрстки
        self.assertEqual(check_report.text_faults('эскалации (направление В\ue082 196'), (1, 0))
        # границы частной области: первый и последний её символ тоже «квадраты»
        self.assertEqual(check_report.text_faults('\ue000 и \uf8ff'), (2, 0))
        self.assertEqual(check_report.text_faults('смена реально открывала176179180.'), (0, 1))
        # самая короткая склейка, которую ловим: 46 + 302 + 15 — семь цифр
        self.assertEqual(check_report.text_faults('смена4630215.'), (0, 1))
        self.assertEqual(check_report.text_faults('открывала176, 179, 180. (раздел 16.1)207.'), (0, 0))

    def test_old_pdf_page_with_squares_fails(self):
        # страница оглавления из PDF от 19.10.2026: Inter заменял скобки символами без Юникода
        page = ROOT / 'tests' / 'fixtures' / 'old_toc_page_2026-10-19.pdf'
        errors = []
        check_report.check_pdf(page, errors)
        self.assertTrue(any('символов без Юникода' in e for e in errors), errors)

    def test_old_pdf_page_with_glued_footnotes_fails(self):
        # страница 15 того же PDF: «…т58596768» — сноски 58, 59, 67, 68 слиплись в одно число
        page = ROOT / 'tests' / 'fixtures' / 'old_glued_footnotes_page_2026-10-19.pdf'
        errors = []
        check_report.check_pdf(page, errors)
        self.assertTrue(any('склеились' in e for e in errors), errors)

    def test_report_pdf_passes(self):
        pdf = ROOT / 'output' / 'Искусственный_интеллект_в_домах_соцобслуживания_доклад.pdf'
        errors = []
        check_report.check_pdf(pdf, errors)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
