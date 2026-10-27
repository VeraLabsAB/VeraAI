"""Ingen .py-fil i scripts/ (även tests/) får innehålla dolda tecken som de är (granskning 4, uppgift C).

Ett tecken som inte syns i en textredigerare kan ändra vad koden gör utan att någon ser det. Tecken
som behövs med flit, till exempel ett hårt mellanslag i en teststräng, skrivs därför som synliga
koder: \\u00a0, \\u202f, \\u200b, \\u2028 och så vidare. Testet slår larm för:

- styrtecken (Unicode-kategori Cc), utom \\n som radslut. Även tabb och \\r (Windows-radslut),
- osynliga formattecken (kategori Cf), bland dem riktningstecknen U+202A–U+202E och U+2066–U+2069,
  nollbreddstecken som U+200B och U+200D, U+FEFF och mjukt bindestreck (U+00AD),
- andra blanksteg än vanligt mellanslag (kategori Zs, Zl och Zp), till exempel hårt mellanslag
  (U+00A0), smalt hårt mellanslag (U+202F) och de ovanliga radbrytningarna U+2028 och U+2029,
- tecken som ser tomma ut fast de inte är blanksteg: utfyllnadstecken (U+115F, U+1160, U+3164,
  U+FFA0), blank blindskrift (U+2800) och variantväljare (U+FE00–U+FE0F, U+E0100–U+E01EF),
- alla tecken på Unicodes lista över tecken som inte ska synas (Default_Ignorable_Code_Point,
  granskning 8, N1), till exempel de khmeriska vokaltecknen U+17B4 och U+17B5 och koder som
  Unicode inte har gett något tecken (U+2065, U+FFF0–U+FFF8 och U+E0000–U+E0FFF).
"""

import unicodedata
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]

OSYNLIGA_ANDRA = {0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800, *range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0)}
# Unicodes lista över tecken som inte ska synas (Default_Ignorable_Code_Point i DerivedCoreProperties.txt),
# skriven som koder, så att den inte beror på Pythons Unicode-version (granskning 8, N1).
OSYNLIGA_ENLIGT_UNICODE = {
    0x00AD, 0x034F, 0x061C, 0x115F, 0x1160, 0x17B4, 0x17B5, *range(0x180B, 0x1810), *range(0x200B, 0x2010),
    *range(0x202A, 0x202F), *range(0x2060, 0x2070), 0x3164, *range(0xFE00, 0xFE10), 0xFEFF, 0xFFA0,
    *range(0xFFF0, 0xFFF9), *range(0x1BCA0, 0x1BCA4), *range(0x1D173, 0x1D17B), *range(0xE0000, 0xE1000),
}


def ar_dolt(tecken):
    kategori = unicodedata.category(tecken)
    if tecken == "\n":
        return False
    if kategori in ("Cc", "Cf", "Zl", "Zp"):
        return True
    if kategori == "Zs":
        return tecken != " "
    return ord(tecken) in OSYNLIGA_ANDRA or ord(tecken) in OSYNLIGA_ENLIGT_UNICODE


def dolda_tecken_i(text):
    """Lista med (rad, kolumn, "U+XXXX") för varje dolt tecken i texten. Rad och kolumn börjar på 1."""
    fynd = []
    for radnummer, rad in enumerate(text.split("\n"), start=1):
        for kolumn, tecken in enumerate(rad, start=1):
            if ar_dolt(tecken):
                fynd.append((radnummer, kolumn, "U+" + format(ord(tecken), "04X")))
    return fynd


def pythonfiler():
    return sorted(SCRIPTS.rglob("*.py"))


def test_det_finns_filer_att_soka_i():
    # Skydd mot att testet blir grönt för att det inte hittar några filer alls.
    filer = pythonfiler()
    assert SCRIPTS / "belopp.py" in filer
    assert Path(__file__).resolve() in filer
    assert SCRIPTS / "tests" / "test_las_kassa.py" in filer


def test_ingen_pythonfil_innehaller_dolda_tecken():
    fynd = []
    for fil in pythonfiler():
        data = fil.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            fynd.append(str(fil.relative_to(SCRIPTS)) + ": filen är inte sparad som UTF-8")
            continue
        fynd += [str(fil.relative_to(SCRIPTS)) + ":" + str(rad) + ":" + str(kolumn) + " " + kod
                 for rad, kolumn, kod in dolda_tecken_i(text)]
    assert not fynd, ("Dolda tecken i koden. Skriv dem som synliga koder, till exempel \\u00a0:\n"
                      + "\n".join(fynd))


# --- Skydd: kontrollen hittar verkligen de dolda tecknen ---

DOLDA = {
    "nul": "\x00", "tabb": "\t", "vagnretur": "\r", "vt": "\x0b", "ff": "\x0c", "esc": "\x1b", "del": "\x7f",
    "nel": "\x85", "hart_mellanslag": "\u00a0", "smalt_hart_mellanslag": "\u202f", "em_mellanslag": "\u2003",
    "ideografiskt_mellanslag": "\u3000", "u2028": "\u2028", "u2029": "\u2029", "u200b": "\u200b",
    "u200c": "\u200c", "u200d": "\u200d", "u2060": "\u2060", "bom": "\ufeff", "mjukt_bindestreck": "\u00ad",
    "lrm": "\u200e", "rlm": "\u200f", "alm": "\u061c", "lre": "\u202a", "rle": "\u202b", "pdf": "\u202c",
    "lro": "\u202d", "rlo": "\u202e", "lri": "\u2066", "rli": "\u2067", "fsi": "\u2068", "pdi": "\u2069",
    "utfyllnad_115f": "\u115f", "utfyllnad_3164": "\u3164", "blank_blindskrift": "\u2800",
    "variantvaljare": "\ufe0f", "variantvaljare_e0100": "\U000e0100", "tagg": "\U000e0041",
}


@pytest.mark.parametrize("tecken", DOLDA.values(), ids=DOLDA.keys())
def test_kontrollen_hittar_dolda_tecken(tecken):
    text = 'x = 1\nnamn = "a' + tecken + 'b"\n'
    assert dolda_tecken_i(text) == [(2, 10, "U+" + format(ord(tecken), "04X"))]


N1_OSYNLIGA = {namn: chr(kod) for namn, kod in (
    ("khmer_17b4", 0x17B4), ("khmer_17b5", 0x17B5), ("u2065", 0x2065), ("ufff0", 0xFFF0), ("ufff8", 0xFFF8),
    ("ue0000", 0xE0000), ("ue0080", 0xE0080), ("ue01f0", 0xE01F0), ("ue0fff", 0xE0FFF))}


@pytest.mark.parametrize("tecken", N1_OSYNLIGA.values(), ids=N1_OSYNLIGA.keys())
def test_n1_kontrollen_hittar_unicodes_osynliga_tecken(tecken):
    # Granskning 8, N1: förut räknades de här tecknen inte som dolda, fast de inte syns.
    text = 'x = 1\nnamn = "a' + tecken + 'b"\n'
    assert dolda_tecken_i(text) == [(2, 10, "U+" + format(ord(tecken), "04X"))]


def test_kontrollen_slapper_igenom_vanlig_kod():
    text = ('"""Svensk text: åäö ÅÄÖ é ü, tecken som € – … och fullbredd ＴＢ."""\n'
            'x = "\\u00a0\\u202f\\u200b\\u2028"  # synliga koder\n\n')
    assert dolda_tecken_i(text) == []
