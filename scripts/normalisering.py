"""Normalisering av fakturanummer och motparter inför jämförelser (J1, granskning 5).

normalisera_for_jamforelse ger en text i den form som K4 (dubbletter, las_underlag.py) och
fakturanummerregeln i matchningen (matcha_bank.py) jämför i. Två texter som ser likadana ut för
en människa ska bli samma text:

- Unicode-normalisering (NFKC), så att till exempel fullbreddstecken och två sätt att skriva "Ö"
  blir samma tecken,
- alla bindestreck och tankstreck (Unicode-kategori Pd, till exempel U+2010 och U+2013) och
  minustecknet U+2212 blir "-",
- blanksteg och osynliga tecken (kategori Cc och Cf, till exempel U+200B) tas bort,
- stora och små bokstäver räknas som samma.

Texten i underlaget ändras aldrig. Normaliseringen används bara när två texter jämförs.
"""

import unicodedata

_MINUSTECKEN = "−"


def normalisera_for_jamforelse(text):
    """Texten i den form som fakturanummer och motparter jämförs i. Se beskrivningen överst i filen."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join("-" if unicodedata.category(tecken) == "Pd" or tecken == _MINUSTECKEN else tecken
                   for tecken in text)
    text = "".join(tecken for tecken in text
                   if not tecken.isspace() and unicodedata.category(tecken) not in ("Cc", "Cf"))
    return text.casefold()
