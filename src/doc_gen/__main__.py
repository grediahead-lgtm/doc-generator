import argparse
import json
import os
import sys

from .render import read_items, render, safe_number


def main(argv=None):
    ap = argparse.ArgumentParser(prog="doc_gen", description="Make a print-ready invoice or act (HTML) from a CSV of items.")
    ap.add_argument("spec", help="JSON: type (invoice|act), number, date, seller, buyer, vat_percent, items_csv")
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(args.spec))
    items = read_items(os.path.join(base, spec["items_csv"]))
    doc = render(spec, items)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "%s-%s.html" % (spec["type"], safe_number(str(spec["number"]))))
    if os.path.exists(path):
        raise FileExistsError("%s already exists: documents are not overwritten silently" % path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
