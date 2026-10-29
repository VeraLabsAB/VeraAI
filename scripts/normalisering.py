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
- alla tecken på Unicodes egen lista över tecken som inte ska synas tas bort (_OSYNLIGA_ENLIGT_UNICODE,
  N1, granskning 8). Listan står som koder här, så att den inte beror på vilken Unicode-version
  Python har. Hit hör de khmeriska vokaltecknen U+17B4 och U+17B5, som inte syns, och koder som
  Unicode inte har gett något tecken (U+2065, U+FFF0–U+FFF8 och U+E0000–U+E0FFF). De tecknen har
  ingen användning i vanlig text, och OSYNLIGA_SOM_INTE_ANVANDS säger vilka de är, så att
  underlagen kan stoppa dem (las_underlag.py),
- Unicode-normaliseringen görs en gång till efter att tecknen har tagits bort (M8, granskning 7).
  Ett osynligt tecken mellan en bokstav och en accent hindrar annars att de sätts ihop, så att
  "E" + osynligt tecken + accent skulle bli "E" och accenten för sig i stället för "É". Det gör
  också att ett fristående accenttecken efter en bokstav, och en accent efter ett blanksteg, sätts
  ihop med bokstaven (N4, granskning 8): den första normaliseringen gör till exempel "¨" (U+00A8)
  till ett mellanslag och en kombinerande accent, mellanslaget tas bort, och den andra sätter ihop
  accenten med bokstaven före. "A¨" jämförs alltså som "Ä", "A˚" som "Å", och "CAFE" + mellanslag +
  U+0301 (den kombinerande akuta accenten) som "CAFÉ".
  Det är den säkra riktningen: fler ägare känns igen, och fler möjliga dubbletter blir ärenden,
- stora och små bokstäver räknas som samma.

Texten i underlaget ändras aldrig. Normaliseringen används bara när två texter jämförs.

Förväxlingstecken (J1) är bokstäver som ser ut som andra, till exempel ett kyrilliskt "А" som ser
ut som ett latinskt "A". skriftsystem, blandat_ord och andra_skriftsystem hittar dem, så att
underlagen (las_underlag.py) och regelboken (las_regelbok.py) prövar dem på samma sätt.
star_som_hela_ord säger om ett namn står som hela ord i en text, efter normaliseringen för
jämförelser, till exempel om en ägare står i en bankrad (las_regelbok.py, M7). Orden delas vid
allt som inte är en bokstav, en siffra eller ett kombinerande tecken, så att ett skiljetecken
intill namnet inte döljer det (N3, granskning 8). sokform_for_namn ger namnet i den form som
star_som_hela_ord söker efter, och regelboken använder samma funktion (granskning 11, Q3).
star_som_hela_ord_utan_accenter gör samma sak, men accenter räknas inte, så att "Åsa Öberg" står i
"UTTAG ASA OBERG" och omvänt. Den används bara av ägaruppslaget i regelboken (granskning 11, Q2, Hugos
beslut 2026-10-29). normalisera_utan_accenter ger texten som normalisera_for_jamforelse, men utan accenter,
för regelbokens ägarkontroller som jämför två namn (Q2b, Hugos beslut 2026-10-29). Allt annat, till
exempel K4, dublettkontrollen i ägarlistan och matchningen mot motparter, bryr sig fortfarande om accenter.
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

# Unicodes egen lista över tecken som inte ska synas: egenskapen Default_Ignorable_Code_Point i
# Unicodes fil DerivedCoreProperties.txt (N1, granskning 8). Skriven som koder, så att den inte beror
# på vilken Unicode-version Python har. De flesta är formattecken (kategori Cf), som tas bort ändå.
_OSYNLIGA_ENLIGT_UNICODE = frozenset(map(chr, (
    0x00AD, 0x034F, 0x061C, 0x115F, 0x1160,
    0x17B4, 0x17B5,                    # khmeriska vokaltecken som inte syns
    *range(0x180B, 0x1810),            # mongoliska variantväljare och vokalavskiljare
    *range(0x200B, 0x2010),            # nollbreddstecken och de milda riktningsmärkena
    *range(0x202A, 0x202F),            # riktningstecken
    *range(0x2060, 0x2070),            # ordbindare, riktningstecken och U+2065, som inte har något tecken
    0x3164,
    *range(0xFE00, 0xFE10),            # variantväljare
    0xFEFF, 0xFFA0,
    *range(0xFFF0, 0xFFF9),            # koder utan tecken
    *range(0x1BCA0, 0x1BCA4),          # formattecken för stenografi
    *range(0x1D173, 0x1D17B),          # formattecken för noter
    *range(0xE0000, 0xE1000),          # taggar, variantväljare och koder utan tecken
)))

# Tecknen på listan som inte är formattecken och inte stod bland de andra osynliga tecknen före
# granskning 8 (N1): de två khmeriska vokaltecknen, som Unicode avråder från, och koder som Unicode
# inte har gett något tecken. De har ingen användning i vanlig text.
OSYNLIGA_SOM_INTE_ANVANDS = frozenset(map(chr, (
    0x17B4, 0x17B5, 0x2065, *range(0xFFF0, 0xFFF9), 0xE0000, *range(0xE0002, 0xE0020), *range(0xE0080, 0xE0100),
    *range(0xE01F0, 0xE1000),
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
                   and tecken not in _OSYNLIGA_ANDRA and tecken not in _OSYNLIGA_ENLIGT_UNICODE)
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


def _ord_i(text):
    """Orden i texten, efter Unicode-normaliseringen (NFKC), som de står.

    Ett ord är bokstäver, siffror och kombinerande tecken (Unicode-kategori L, N och M) i följd. Allt
    annat skiljer orden åt: blanksteg, bindestreck, skiljetecken, symboler och osynliga formattecken
    (N3, granskning 8). NFKC görs först, så att till exempel ett fristående accenttecken blir ett
    mellanslag och en kombinerande accent, som när två texter jämförs (N4).
    """
    ord_, nu = [], ""
    for tecken in unicodedata.normalize("NFKC", text):
        if unicodedata.category(tecken)[0] in "LNM":
            nu += tecken
        elif nu:
            ord_.append(nu)
            nu = ""
    return ord_ + [nu] if nu else ord_


def sokform_for_namn(namn):
    """Namnet i den form som star_som_hela_ord söker efter: orden ihopsatta och normaliserade för jämförelser.

    Namnet delas i ord som i _ord_i, orden sätts ihop och normaliseras med normalisera_for_jamforelse. Ett
    namn utan bokstäver och siffror, till exempel "-" eller "_ .", blir tomt och står aldrig i en text.
    Regelboken (las_regelbok.py) använder samma funktion för att stoppa ett sådant namn i listan över
    ägare och närstående, så att det som regelboken godtar också kan hittas (granskning 11, Q3, Hugos
    beslut 2026-10-29).
    """
    return normalisera_for_jamforelse("".join(_ord_i(namn)))


def star_som_hela_ord(namn, text):
    """True om namnet står i texten som ett eller flera hela ord i följd, efter normaliseringen för jämförelser.

    Både namnet och texten delas i ord vid allt som inte är en bokstav, en siffra eller ett
    kombinerande tecken (_ord_i), så att ett skiljetecken intill namnet inte döljer det (N3, granskning
    8). Ord i följd i texten sätts ihop och normaliseras tillsammans med normalisera_for_jamforelse
    (N4), och jämförs med namnets sökform (sokform_for_namn). "Namn-7" står alltså i "UTTAG NAMN-7", i
    "UTTAG namn–7", i "UTTAG NAMN -7", i "UTTAG NAMN 7", i "UTTAG NAMN-7/LAN" och i "UTTAG (NAMN-7)",
    men inte i "UTTAG NAMN-77", "UTTAG NAMN-7X" eller "UTTAGNAMN-7". Ett namn som blir tomt efter
    normaliseringen står aldrig i en text.
    """
    sokt = sokform_for_namn(namn)
    if not sokt:
        return False
    ord_ = _ord_i(text)
    for start in range(len(ord_)):
        for slut in range(start + 1, len(ord_) + 1):
            sammansatt = normalisera_for_jamforelse("".join(ord_[start:slut]))
            if sammansatt == sokt:
                return True
            # Ett ord till gör aldrig texten kortare: ett kombinerande tecken kan sättas ihop med
            # bokstaven före, men då blir längden densamma. Därför går det att sluta här.
            if len(sammansatt) > len(sokt):
                break
    return False


def _utan_accenter(text):
    """Texten utan accenter: uppdelad med Unicodes NFKD och utan kombinerande tecken (kategori M).

    "Å" blir "A", "é" blir "e", och en bokstav med ett separat accenttecken blir bokstaven. NFKD gör
    också ett fristående accenttecken (till exempel U+00A8, "¨") till ett mellanslag och en kombinerande
    accent, så att det försvinner på samma sätt. Andra stavningar, till exempel "AA" för "Å" eller "OE"
    för "Ö", ändras inte (Ö5).
    """
    return "".join(tecken for tecken in unicodedata.normalize("NFKD", text)
                   if not unicodedata.category(tecken).startswith("M"))


def star_som_hela_ord_utan_accenter(namn, text):
    """Som star_som_hela_ord, men accenter räknas inte: "Åsa Öberg" står i "UTTAG ASA OBERG", och omvänt.

    Bara för ägaruppslaget i regelboken (las_regelbok.py, granskning 11, Q2, Hugos beslut 2026-10-29).
    Accenterna tas bort från både namnet och texten, och sedan söks namnet med star_som_hela_ord. Allt
    annat i star_som_hela_ord gäller som förut: namnet ska stå som hela ord, så "NAMN-7" står inte i
    "UTTAG NAMN-77". En ägare med minst en bokstav eller siffra i namnet känns alltså igen i fler bankrader,
    aldrig i färre. Ett namn utan bokstäver och siffror stoppas redan av regelboken.
    """
    return star_som_hela_ord(_utan_accenter(namn), _utan_accenter(text))


def normalisera_utan_accenter(text):
    """Som normalisera_for_jamforelse, men utan accenter: "Åsa Öberg" och "ASA OBERG" ger samma text.

    Bara för ägarkontrollerna i regelboken som jämför två namn (las_regelbok.py, granskning 11, Q2b, Hugos
    beslut 2026-10-29). Accenterna tas bort på samma sätt som i star_som_hela_ord_utan_accenter, och sedan
    normaliseras texten med normalisera_for_jamforelse.
    """
    return normalisera_for_jamforelse(_utan_accenter(text))
