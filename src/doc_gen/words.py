"""Amounts in Ukrainian words: '1 250,00' -> 'Одна тисяча двісті п'ятдесят гривень 00 копійок'."""
from decimal import ROUND_HALF_UP, Decimal

UNITS_M = ["нуль", "один", "два", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"]
UNITS_F = ["нуль", "одна", "дві", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"]
TEENS = ["десять", "одинадцять", "дванадцять", "тринадцять", "чотирнадцять", "п'ятнадцять", "шістнадцять",
         "сімнадцять", "вісімнадцять", "дев'ятнадцять"]
TENS = ["", "", "двадцять", "тридцять", "сорок", "п'ятдесят", "шістдесят", "сімдесят", "вісімдесят", "дев'яносто"]
HUNDREDS = ["", "сто", "двісті", "триста", "чотириста", "п'ятсот", "шістсот", "сімсот", "вісімсот", "дев'ятсот"]


def form(n, one, few, many):
    """Ukrainian plural forms: 1 гривня, 2-4 гривні, 5+ гривень (11-14 are 'many')."""
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    last = n % 10
    return one if last == 1 else few if 2 <= last <= 4 else many


def triple(n, feminine=False):
    """0..999 as a list of words (no 'нуль' inside bigger numbers)."""
    out = [HUNDREDS[n // 100]] if n >= 100 else []
    n %= 100
    if 10 <= n <= 19:
        out.append(TEENS[n - 10])
    else:
        if n >= 20:
            out.append(TENS[n // 10])
        if n % 10:
            out.append((UNITS_F if feminine else UNITS_M)[n % 10])
    return [w for w in out if w]


def int_words(n, feminine=False):
    if not 0 <= n < 10**12:
        raise ValueError("number out of range: %d" % n)
    if n == 0:
        return "нуль"
    parts = []
    for size, (one, few, many), fem in ((10**9, ("мільярд", "мільярди", "мільярдів"), False),
                                         (10**6, ("мільйон", "мільйони", "мільйонів"), False),
                                         (10**3, ("тисяча", "тисячі", "тисяч"), True)):
        chunk = (n // size) % 1000
        if chunk:
            parts += triple(chunk, fem) + [form(chunk, one, few, many)]
    rest = n % 1000
    if rest:
        parts += triple(rest, feminine)
    return " ".join(parts)


def amount_words(value):
    """value: Decimal, int or str like '1250.5'. Rounded to kopecks (half up). Returns the sentence."""
    d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d < 0:
        raise ValueError("negative amount")
    grn, kop = int(d), int((d - int(d)) * 100)
    text = "%s %s %02d %s" % (int_words(grn, feminine=True), form(grn, "гривня", "гривні", "гривень"), kop,
                              form(kop, "копійка", "копійки", "копійок"))
    return text[0].upper() + text[1:]
