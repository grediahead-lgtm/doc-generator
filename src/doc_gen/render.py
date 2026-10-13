import csv
import html
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .words import amount_words

TITLES = {"invoice": "Рахунок-фактура", "act": "Акт виконаних робіт (наданих послуг)"}
Q = Decimal("0.01")


def money(d):
    return "{:,.2f}".format(d).replace(",", " ").replace(".", ",")


def parse_dec(s, what, row):
    try:
        d = Decimal(str(s).strip().replace(" ", "").replace(",", "."))
    except InvalidOperation:
        raise ValueError("row %d: %s %r is not a number" % (row, what, s))
    return d


def read_items(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    items = []
    for n, r in enumerate(rows, start=2):
        name = (r.get("name") or "").strip()
        if not name:
            raise ValueError("row %d: empty name" % n)
        qty, price = parse_dec(r.get("qty", ""), "qty", n), parse_dec(r.get("price", ""), "price", n)
        if qty <= 0 or price < 0:
            raise ValueError("row %d: qty must be positive and price not negative" % n)
        items.append({"name": name, "unit": (r.get("unit") or "шт.").strip(), "qty": qty, "price": price,
                      "sum": (qty * price).quantize(Q, rounding=ROUND_HALF_UP)})
    if not items:
        raise ValueError("no items in %s" % path)
    return items


def totals(items, vat_percent=Decimal("0")):
    """Prices are treated as final (VAT, if any, is already inside them): VAT is shown, not added."""
    total = sum((i["sum"] for i in items), Decimal("0"))
    vat = (total * vat_percent / (100 + vat_percent)).quantize(Q, rounding=ROUND_HALF_UP) if vat_percent else Decimal("0")
    return total, vat


def safe_number(number):
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,30}", number):
        raise ValueError("number may contain only letters, digits, dot, dash, underscore (max 30)")
    return number


def render(spec, items):
    e = html.escape
    kind = spec["type"]
    if kind not in TITLES:
        raise ValueError("type must be invoice or act")
    number = safe_number(str(spec["number"]))
    vat_p = Decimal(str(spec.get("vat_percent", 0)))
    total, vat = totals(items, vat_p)
    rows = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>" % (
            k, e(i["name"]), e(i["unit"]), e("{:g}".format(i["qty"])), money(i["price"]), money(i["sum"]))
        for k, i in enumerate(items, start=1))
    s, b = spec["seller"], spec["buyer"]
    vat_line = "<p>У тому числі ПДВ %s%%: %s грн</p>" % (e("{:g}".format(vat_p)), money(vat)) if vat_p else "<p>Без ПДВ</p>"
    return """<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><title>%(title)s № %(number)s</title>
<style>body{font:14px/1.45 Arial,sans-serif;max-width:800px;margin:24px auto;padding:0 16px}
table{border-collapse:collapse;width:100%%}td,th{border:1px solid #444;padding:5px 8px}th{background:#eee}.n{text-align:right;white-space:nowrap}
h1{font-size:20px}.sign{display:flex;gap:48px;margin-top:40px}.sign div{flex:1;border-top:1px solid #444;padding-top:4px}
@media print{body{margin:0}}</style></head><body>
<h1>%(title)s № %(number)s від %(date)s</h1>
<p><b>Постачальник (виконавець):</b> %(seller)s</p>
<p><b>Покупець (замовник):</b> %(buyer)s</p>
<table><thead><tr><th>№</th><th>Найменування</th><th>Од.</th><th>Кількість</th><th>Ціна, грн</th><th>Сума, грн</th></tr></thead>
<tbody>%(rows)s</tbody></table>
<p><b>Разом: %(total)s грн</b></p>%(vat)s
<p>Всього на суму: <b>%(words)s</b></p>
<div class="sign"><div>Постачальник (виконавець) / підпис</div><div>Покупець (замовник) / підпис</div></div>
</body></html>
""" % {"title": e(TITLES[kind]), "number": e(number), "date": e(str(spec["date"])), "seller": e(_party(s)), "buyer": e(_party(b)),
       "rows": rows, "total": money(total), "vat": vat_line, "words": e(amount_words(total))}


def _party(p):
    parts = [p["name"]] + [("%s: %s" % (label, p[key])) for key, label in (("tax_id", "РНОКПП/ЄДРПОУ"), ("iban", "IBAN"), ("address", "адреса")) if p.get(key)]
    return ", ".join(parts)
