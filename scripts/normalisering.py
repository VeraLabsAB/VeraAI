"""Normalisering av fakturanummer och motparter inför jämförelser (J1, granskning 5, och L2, granskning 6).

normalisera_for_jamforelse ger en text i den form som K4 (dubbletter, las_underlag.py) och
fakturanummerregeln i matchningen (matcha_bank.py) jämför i. Två texter som ser likadana ut för
en människa ska bli samma text:

- Unicode-normalisering (NFKC), så att till exempel fullbreddstecken och två sätt att skriva "Ö"
  blir samma tecken,
- alla bindestreck och tankstreck (Unicode-kategori Pd, till exempel U+2010 och U+2013) och
  minustecknet U+2212 blir "-",
- blanksteg och osynliga tecken (kategori Cc och Cf, till exempel U+200B) tas bort,
- tecken som ser tomma ut fast de inte är blanksteg tas också bort (_OSYNLIGA_ANDRA, L2): samma
  tecken som testet test_inga_dolda_tecken.py räknar som osynliga (utfyllnadstecknen U+115F,
  U+1160, U+3164 och U+FFA0, blank blindskrift U+2800 och variantväljarna U+FE00–U+FE0F och
  U+E0100–U+E01EF), och osynliga kombinerande tecken (U+034F och de mongoliska variantväljarna
  U+180B–U+180D och U+180F),
- stora och små bokstäver räknas som samma.

Texten i underlaget ändras aldrig. Normaliseringen används bara när två texter jämförs.
"""

import unicodedata

_MINUSTECKEN = chr(0x2212)

# Tecken som ser tomma ut fast de inte är blanksteg eller formattecken (L2). Alla skrivs som koder,
# så att det syns i koden vilka tecken det gäller.
_OSYNLIGA_ANDRA = frozenset(map(chr, (
    0x115F, 0x1160, 0x3164, 0xFFA0,    # utfyllnadstecken (NFKC gör U+3164 och U+FFA0 till U+1160)
    0x2800,                            # blank blindskrift
    *range(0xFE00, 0xFE10),            # variantväljare
    *range(0xE0100, 0xE01F0),          # fler variantväljare
    0x034F,                            # kombinerande teckenbindare, syns inte
    0x180B, 0x180C, 0x180D, 0x180F,    # mongoliska variantväljare
)))


def normalisera_for_jamforelse(text):
    """Texten i den form som fakturanummer och motparter jämförs i. Se beskrivningen överst i filen."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join("-" if unicodedata.category(tecken) == "Pd" or tecken == _MINUSTECKEN else tecken
                   for tecken in text)
    text = "".join(tecken for tecken in text
                   if not tecken.isspace() and unicodedata.category(tecken) not in ("Cc", "Cf")
                   and tecken not in _OSYNLIGA_ANDRA)
    return text.casefold()
