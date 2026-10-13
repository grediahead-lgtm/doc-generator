import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from doc_gen.__main__ import main  # noqa: E402
from doc_gen.render import money, read_items, render, safe_number, totals  # noqa: E402
from doc_gen.words import amount_words, form, int_words  # noqa: E402


class WordsTests(unittest.TestCase):
    def test_cases(self):
        cases = {
            0: "Нуль гривень 00 копійок", 1: "Одна гривня 00 копійок", 2: "Дві гривні 00 копійок", 5: "П'ять гривень 00 копійок",
            11: "Одинадцять гривень 00 копійок", 21: "Двадцять одна гривня 00 копійок", 22: "Двадцять дві гривні 00 копійок",
            101: "Сто одна гривня 00 копійок", 112: "Сто дванадцять гривень 00 копійок",
            1000: "Одна тисяча гривень 00 копійок", 2000: "Дві тисячі гривень 00 копійок", 5000: "П'ять тисяч гривень 00 копійок",
            11000: "Одинадцять тисяч гривень 00 копійок", 21000: "Двадцять одна тисяча гривень 00 копійок",
            1250.5: "Одна тисяча двісті п'ятдесят гривень 50 копійок", 1000000: "Один мільйон гривень 00 копійок",
            2000001: "Два мільйони одна гривня 00 копійок", 0.01: "Нуль гривень 01 копійка", 0.02: "Нуль гривень 02 копійки",
            12345.67: "Дванадцять тисяч триста сорок п'ять гривень 67 копійок",
        }
        for value, want in cases.items():
            self.assertEqual(amount_words(value), want, value)

    def test_rounding_and_strings(self):
        self.assertEqual(amount_words("10.005"), "Десять гривень 01 копійка")  # half up
        self.assertEqual(amount_words(Decimal("1999.999")), "Дві тисячі гривень 00 копійок")

    def test_forms_and_limits(self):
        self.assertEqual([form(n, "a", "b", "c") for n in (1, 2, 5, 11, 12, 14, 21, 101, 111)], list("abccccaac"))
        with self.assertRaises(ValueError):
            amount_words(-1)
        with self.assertRaises(ValueError):
            int_words(10**12)


class ItemsTests(unittest.TestCase):
    def write(self, d, text):
        p = os.path.join(d, "i.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def test_example(self):
        items = read_items(os.path.join(ROOT, "examples", "items.csv"))
        total, vat = totals(items)
        self.assertEqual((total, vat), (Decimal("1750.00"), Decimal("0")))
        self.assertEqual(money(total), "1 750,00")

    def test_vat_is_inside_the_price(self):
        items = [{"sum": Decimal("120.00")}]
        self.assertEqual(totals(items, Decimal("20")), (Decimal("120.00"), Decimal("20.00")))

    def test_bad_rows(self):
        with tempfile.TemporaryDirectory() as d:
            for text in ("name,qty,price\n,1,1\n", "name,qty,price\nx,0,1\n", "name,qty,price\nx,1,-5\n", "name,qty,price\nx,abc,1\n", "name,qty,price\n"):
                with self.assertRaises(ValueError, msg=text):
                    read_items(self.write(d, text))

    def test_decimal_comma(self):
        with tempfile.TemporaryDirectory() as d:
            items = read_items(self.write(d, 'name,qty,price\nx,"2,5","10,10"\n'))
        self.assertEqual(items[0]["sum"], Decimal("25.25"))


class RenderTests(unittest.TestCase):
    SPEC = {"type": "invoice", "number": "7", "date": "13.10.2026", "seller": {"name": "A <b>"}, "buyer": {"name": "B"}}

    def items(self):
        return [{"name": "<script>x</script>", "unit": "шт.", "qty": Decimal("2"), "price": Decimal("10"), "sum": Decimal("20.00")}]

    def test_html_is_escaped_and_has_words(self):
        out = render(self.SPEC, self.items())
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("A &lt;b&gt;", out)
        self.assertIn("Двадцять гривень 00 копійок", out)
        self.assertIn("Без ПДВ", out)

    def test_bad_type_and_number(self):
        with self.assertRaises(ValueError):
            render(dict(self.SPEC, type="receipt"), self.items())
        for bad in ("../x", "a b", "", "x" * 31):
            with self.assertRaises(ValueError, msg=bad):
                safe_number(bad)


class CliTests(unittest.TestCase):
    def test_cli_writes_once_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            spec = os.path.join(ROOT, "examples", "invoice.json")
            self.assertEqual(main([spec, "--out", d]), 0)
            self.assertTrue(os.path.exists(os.path.join(d, "invoice-2026-001.html")))
            with self.assertRaises(FileExistsError):
                main([spec, "--out", d])


if __name__ == "__main__":
    unittest.main()
