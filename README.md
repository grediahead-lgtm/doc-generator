# doc-generator

Makes **print-ready invoices and acts of completed work** (Ukrainian text) from a short JSON and a CSV of items, with the **amount written in words** ("Одна тисяча двісті п'ятдесят гривень 00 копійок"). Output is a plain HTML page: open it in a browser and print or "Save as PDF". Python standard library only, no internet.

## What it does
- Input: a spec JSON (`type`: `invoice` or `act`, `number`, `date`, `seller`, `buyer`, `vat_percent`, `items_csv`) and a CSV with `name, unit, qty, price`.
- Totals are computed with exact decimal arithmetic (no floating-point cents). Prices are treated as final: with `vat_percent` above 0 the VAT is **shown as included**, not added on top; with 0 the document says "Без ПДВ".
- **Amount in words** in correct Ukrainian: gender and number agreement (`одна/дві тисячі`, `двадцять одна гривня`, `п'ять гривень`, `11 копійок`), up to 999 999 999 999 UAH, rounded to kopecks half up.
- All text from your files is HTML-escaped. The document number may contain only letters, digits, dot, dash, underscore, and an existing file is **never overwritten**, so a document number cannot be silently reused.
- Bad rows (empty name, quantity not above 0, negative price, not a number) stop the run with the row number.

## Use
```bash
PYTHONPATH=src python3 -m doc_gen examples/invoice.json --out out      # writes out/invoice-2026-001.html
```
Edit `examples/invoice.json` and `examples/items.csv`; the example party names and numbers are fakes. Tests: `python3 -m unittest discover -s tests`.

## Limits (read this)
- **These are generic templates, not legal advice.** Requirements for primary documents (details, signatures, e-invoicing, VAT) depend on your status and the contract; have your accountant check the form before you send documents to clients.
- No PDF writer, no numbering sequence (you choose the number), one currency (UAH), no discounts, no per-line VAT.
- The words function covers numbers up to 999 999 999 999 and UAH/kopecks only.

MIT license.

---

# doc-generator (українською)

Створює **рахунки та акти виконаних робіт**, готові до друку, з **сумою прописом** українською. Результат — HTML-сторінка: відкрийте в браузері й роздрукуйте або збережіть як PDF. Лише стандартна бібліотека Python.

**Запуск:** `PYTHONPATH=src python3 -m doc_gen examples/invoice.json --out out`. Ціни вважаються підсумковими: ПДВ показується як включений.

**Важливо:** це типові шаблони, а не юридична порада — форму первинних документів перевірте з бухгалтером. Існуючі файли не перезаписуються.
