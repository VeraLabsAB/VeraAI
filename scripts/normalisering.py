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
- Unicode-normaliseringen görs en gång till efter att tecknen har tagits bort (M8, granskning 7).
  Ett osynligt tecken mellan en bokstav och en accent hindrar annars att de sätts ihop, så att
  "E" + osynligt tecken + accent skulle bli "E" och accenten för sig i stället för "É",
- stora och små bokstäver räknas som samma.

Texten i underlaget ändras aldrig. Normaliseringen används bara när två texter jämförs.

Förväxlingstecken (J1) är bokstäver som ser ut som andra, till exempel ett kyrilliskt "А" som ser
ut som ett latinskt "A". skriftsystem, blandat_ord och andra_skriftsystem hittar dem, så att
underlagen (las_underlag.py) och regelboken (las_regelbok.py) prövar dem på samma sätt.
star_som_hela_ord säger om ett namn står som hela ord i en text, efter normaliseringen för
jämförelser, till exempel om en ägare står i en bankrad (las_regelbok.py, M7).
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

# Skriftsystemet för latinska bokstäver, som det står först i bokstavens namn i Unicode.
_LATIN = "LATIN"


def normalisera_for_jamforelse(text):
    """Texten i den form som fakturanummer och motparter jämförs i. Se beskrivningen överst i filen."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join("-" if unicodedata.category(tecken) == "Pd" or tecken == _MINUSTECKEN else tecken
                   for tecken in text)
    text = "".join(tecken for tecken in text
                   if not tecken.isspace() and unicodedata.category(tecken) not in ("Cc", "Cf")
                   and tecken not in _OSYNLIGA_ANDRA)
    # En gång till, så att en bokstav och en accent som stod på var sin sida om ett borttaget tecken
    # sätts ihop (M8).
    text = unicodedata.normalize("NFKC", text)
    return text.casefold()


def tecken_med_namn(tecken):
    """Ett tecken för ett felmeddelande: koden och namnet, till exempel "U+0410 (CYRILLIC CAPITAL LETTER A)"."""
    return "U+" + format(ord(tecken), "04X") + " (" + unicodedata.name(tecken, "utan namn") + ")"


def skriftsystem(bokstav):
    """Skriftsystemet för en bokstav, ur tecknets namn i Unicode: till exempel LATIN, CYRILLIC eller GREEK.

    Python har inget eget sätt att slå upp skriftsystemet. Namnets första ord räcker här: en bokstav
    vars namn inte börjar med LATIN räknas som ett annat skriftsystem.
    """
    return unicodedata.name(bokstav, "").split(" ")[0]


def _bokstaver(text):
    """Bokstäverna i texten, efter Unicode-normaliseringen (NFKC)."""
    return [tecken for tecken in unicodedata.normalize("NFKC", text) if unicodedata.category(tecken).startswith("L")]


def blandat_ord(text):
    """Det första ordet som blandar latinska bokstäver med bokstäver från ett annat skriftsystem (J1).

    Returnerar (ordet, den första bokstaven från ett annat skriftsystem), eller None. Texten
    Unicode-normaliseras först (NFKC), så att till exempel fullbreddsbokstäver räknas som latinska.
    Ett ord helt i ett annat skriftsystem blandar inget.
    """
    for ord_ in unicodedata.normalize("NFKC", text).split():
        bokstaver = _bokstaver(ord_)
        andra = [tecken for tecken in bokstaver if skriftsystem(tecken) != _LATIN]
        if andra and len(andra) < len(bokstaver):
            return ord_, andra[0]
    return None


def andra_skriftsystem(text):
    """Bokstäverna i texten som inte är latinska, efter Unicode-normaliseringen (NFKC), i textens ordning.

    Till exempel cherokee-bokstäverna i en text som ser ut som ett latinskt namn (M5, granskning 7).
    """
    return [tecken for tecken in _bokstaver(text) if skriftsystem(tecken) != _LATIN]


def star_som_hela_ord(namn, text):
    """True om namnet står i texten som ett eller flera hela ord i följd, efter normaliseringen för jämförelser.

    Texten delas i ord vid blanksteg, och varje ord normaliseras med normalisera_for_jamforelse.
    "Namn-7" står alltså i "UTTAG NAMN-7", i "UTTAG namn–7" och i "UTTAG NAMN -7", men inte i
    "UTTAG NAMN-77". Ett namn som blir tomt efter normaliseringen står aldrig i en text.
    """
    sokt = normalisera_for_jamforelse(namn)
    ord_ = [del_ for del_ in map(normalisera_for_jamforelse, text.split()) if del_]
    for start in range(len(ord_)):
        sammansatt = ""
        for del_ in ord_[start:]:
            sammansatt += del_
            if sammansatt == sokt:
                return True
            if len(sammansatt) >= len(sokt):
                break
    return False
