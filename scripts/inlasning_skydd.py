"""Skydd som är gemensamma för all inläsning av underlag i kärnan.

Inläsningsmodulerna i scripts/ läser var sin sorts CSV-fil, och var sin JSON-fil som beskriver
filens format för ett visst företag. Skydden mot trasiga filer är desamma för alla sorter och
ligger därför här:

- Teckenkodningen: först UTF-8 (med eller utan BOM), annars Windows-1252. UTF-16 stoppas.
- Styrtecken: andra styrtecken än tabb och vanliga radslut (\\n, \\r), samt de ovanliga
  radbrytningarna U+2028 och U+2029, stoppar filen. NUL-tecken (tecken nummer 0) får ett eget
  meddelande. Riktningstecknen U+202A–U+202E och U+2066–U+2069 stoppar också filen (I3).
- Sökvägen: en sökväg som inte är text eller Path stoppas innan något öppnas (I4).
- CSV-läsningen: strikt läsning, ingen radbrytning inuti ett fält, och varje rad ska ha lika
  många fält som rubrikraden. Datum och belopp tolkas på samma sätt i alla filer.
- JSON-formatet: filen läses som UTF-8, dubbla nycklar, för djup nästling och heltal med fler än
  15 siffror stoppas, och nycklar, kolumnnamn och avgränsare kontrolleras.
- Värden i ett JSON-format (för kontoplanen, momssatserna och regelboken): dolda tecken var som helst i filen,
  även i nycklar och anteckningar, stoppar filen. Text, heltal och datum kontrolleras med samma
  meddelanden i alla format.

Modulen vet inte vilken sorts fil den läser. Allt som skiljer i felmeddelandena (vilken felklass
som kastas och vad filen kallas) kommer från en _Filsort, som varje inläsningsmodul skapar själv.
Meddelandena blir därför exakt desamma som när koden låg i varje modul för sig.

Alla namn i modulen börjar med understreck. De är byggstenar för inläsningsmodulerna och inget
gränssnitt för annan kod: var för sig hoppar de över de andra skydden. Annan kod läser filer med
inläsningsmodulernas egna funktioner, som kör alla skydd i rätt ordning. Ett test
(test_inga_genvagar.py) slår larm om modulen får ett namn utan understreck, och om en annan
kärnfil använder byggstenarna.
"""

import csv
import datetime as dt
import json
import re
import unicodedata
from pathlib import PurePath
from typing import NamedTuple

from belopp import tolka_belopp
from normalisering import normalisera_for_jamforelse as _jamforbar


class _Filsort(NamedTuple):
    """Det som skiljer felmeddelandena åt mellan olika sorters filer."""

    fel: type             # felklassen som kastas
    filen: str            # vad filen kallas först i ett meddelande, till exempel "Filen"
    formatet: str         # vad JSON-formatet kallas först i ett meddelande, till exempel "Formatet"
    exportera_igen: str   # råd när filen är sparad som UTF-16
    om_styrtecken: str    # meningen efter "… en ovanlig radbrytning." när filen har ett styrtecken
    ihopslaget: str       # vad ett citattecken i fel läge kan slå ihop, till exempel "flera rader"
    nivaer: str           # meningen om hur många nivåer JSON-formatet har


_DATUM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
_HELTAL = re.compile(r"\d+", re.ASCII)

# Radbrytningar som inte får finnas inuti ett fält: \n, \r, U+2028 och U+2029.
_RADBRYTNINGAR = "\n\r\u2028\u2029"

# Styrtecken som får finnas i en fil: tabb, \n och \r. Alla andra styrtecken (Unicode-kategori
# Cc), samt U+2028 och U+2029, stoppar filen (G1). Flera av dem räknas som radslut när filen
# delas i rader, men inte av kontrollen mot radbrytning inuti fält, och kan då slå ihop flera
# rader till en.
_TILLATNA_STYRTECKEN = "\t\n\r"
# Kategori Cc omfattar bara U+0000–U+001F och U+007F–U+009F, och Unicode lovar att den aldrig ändras.
_OTILLATNA_TECKEN = re.compile("[" + re.escape("".join(
    chr(nummer) for nummer in range(0x100)
    if unicodedata.category(chr(nummer)) == "Cc" and chr(nummer) not in _TILLATNA_STYRTECKEN
) + "\u2028\u2029") + "]")
_RADSLUT = re.compile(r"\r\n|\r|\n")

# Riktningstecken (I3): osynliga tecken som får text att visas i en annan ordning än den är lagrad,
# U+202A–U+202E och U+2066–U+2069. En beskrivning kan då se ut som en annan text än den är. Andra
# osynliga formattecken, till exempel U+200D som binder ihop emoji, stoppar inte filen.
_RIKTNINGSTECKEN = re.compile("[\u202a-\u202e\u2066-\u2069]")

# Avgränsare som ett format får använda (G2): komma, semikolon, tabb och lodstreck.
_TILLATNA_AVGRANSARE = (",", ";", "\t", "|")


# --- Sökvägen ---

def _ar_sokvag(sokvag):
    """True om sokvag är text eller en Path. Annat, till exempel None, ett tal eller True, får inte öppnas.

    Ett heltal (och True och False) tolkas annars av Python som ett filnummer, så att programmets
    egen in- eller utdata läses och sedan stängs (I4).
    """
    return isinstance(sokvag, (str, PurePath))


def _sokvagens_typ(sokvag):
    """Början på meddelandet för en sökväg av fel typ."""
    return "sökvägen ska vara text eller en Path, inte " + type(sokvag).__name__ + "."


# --- JSON-formatet ---

class _DubbelNyckel(Exception):
    """En nyckel står två gånger i samma JSON-objekt. Fångas i _ladda_json."""


class _OgiltigtTal(Exception):
    """Ett tal som inte får finnas i ett JSON-format. Fångas i _ladda_json."""


def _heltal_ur_json(text, hogst_siffror=15):
    """Ett heltal i ett JSON-format, med högst hogst_siffror siffror (samma gräns som i underlagen).

    Längden prövas innan talet räknas ut. Annars tar ett jättelångt tal mycket lång tid att läsa i
    äldre Pythonversioner, och ger ett ValueError på engelska i nyare (som har en egen gräns på 4300
    siffror). Gränsen står här och inte som ett eget namn, eftersom ett skyddstest
    (test_inga_genvagar.py) annars tar talet för en byggsten när en annan modul har samma tal.
    """
    siffror = len(text.lstrip("-"))
    if siffror > hogst_siffror:
        raise _OgiltigtTal(
            "ett heltal med " + str(siffror) + " siffror, men ett tal i formatet får ha högst "
            + str(hogst_siffror) + " siffror"
        )
    return int(text)


def _inga_dubbla_nycklar(par):
    objekt = {}
    for nyckel, varde in par:
        if nyckel in objekt:
            raise _DubbelNyckel("nyckeln " + repr(nyckel) + " står flera gånger")
        objekt[nyckel] = varde
    return objekt


def _ladda_json(sokvag, filsort):
    """Läser ett JSON-format. Returnerar (innehållet, var), där var är början på felmeddelanden.

    Innehållet är inte kontrollerat. Det gör anroparen, med funktionerna nedan.
    """
    data, var = _las_jsonfil(sokvag, filsort)
    return _tolka_json(data, var, filsort), var


def _las_jsonfil(sokvag, filsort):
    """Filens bytes, som de är. Returnerar (bytes, var). Tolkas med _tolka_json.

    Uppdelad från _ladda_json så att en kontrollsumma kan räknas på exakt de bytes som sedan
    tolkas. Filen läses alltså bara en gång, och kan inte bytas mellan summan och tolkningen.
    """
    if not _ar_sokvag(sokvag):
        raise filsort.fel(filsort.formatet + " går inte att läsa: " + _sokvagens_typ(sokvag))
    var = filsort.formatet + " i " + str(sokvag)
    try:
        with open(sokvag, "rb") as fil:
            return fil.read(), var
    except FileNotFoundError:
        raise filsort.fel(filsort.formatet + " saknas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise filsort.fel(filsort.formatet + " saknas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise filsort.fel(
            filsort.formatet + " går inte att läsa: " + str(sokvag) + " (" + (fel.strerror or str(fel)) + ")."
        ) from None


def _tolka_json(data, var, filsort):
    """Tolkar bytes från _las_jsonfil som JSON, med skydden mot dubbla nycklar, långa tal och djup nästling."""
    try:
        innehall = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_inga_dubbla_nycklar,
                              parse_int=_heltal_ur_json)
    except UnicodeDecodeError:
        raise filsort.fel(var + " är inte sparat som UTF-8.") from None
    except json.JSONDecodeError as fel:
        raise filsort.fel(
            var + " är inte giltig JSON (rad " + str(fel.lineno) + ", tecken " + str(fel.colno) + ")."
        ) from None
    except _DubbelNyckel as fel:
        raise filsort.fel(var + ": " + str(fel) + ".") from None
    except _OgiltigtTal as fel:
        raise filsort.fel(var + " innehåller " + str(fel) + ".") from None
    except RecursionError:
        raise filsort.fel(
            var + " är inte giltigt: för många hakparenteser eller klammerparenteser inuti varandra. "
            + filsort.nivaer + " Filen är troligen trasig."
        ) from None
    return innehall


def _kontrollera_nycklar(data, obligatoriska, valfria, var, filsort):
    """data ska vara ett objekt med alla obligatoriska nycklar och inga andra än de valfria."""
    if not isinstance(data, dict):
        raise filsort.fel(var + " ska vara ett objekt med nycklar, inte " + type(data).__name__ + ".")
    saknas = [nyckel for nyckel in obligatoriska if nyckel not in data]
    if saknas:
        raise filsort.fel(var + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in data if nyckel not in obligatoriska + valfria)
    if okanda:
        raise filsort.fel(
            var + " har en okänd nyckel: " + ", ".join(map(repr, okanda)) + ". Tillåtna nycklar är "
            + ", ".join(map(repr, obligatoriska + valfria)) + "."
        )


def _kontrollera_anteckning(data, var, filsort):
    """Den valfria nyckeln "anteckning" ska vara text om den finns."""
    if "anteckning" in data and not isinstance(data["anteckning"], str):
        raise filsort.fel(var + ": 'anteckning' ska vara text.")


def _kontrollera_namn(namn, vad, var, filsort, ett_namn="ett namn"):
    """Kontrollerar ett namn i formatet och returnerar det utan mellanslag runt om.

    vad är början på meddelandet, till exempel "kolumnnamnet för 'belopp'". ett_namn är vad
    namnet kallas i meddelandet om osynliga tecken, till exempel "ett kolumnnamn".
    """
    if not isinstance(namn, str) or not namn.strip():
        raise filsort.fel(var + ": " + vad + " får inte vara tomt.")
    if any(tecken in namn for tecken in _RADBRYTNINGAR + '"'):
        raise filsort.fel(var + ": " + vad + " får inte innehålla radbrytning eller citattecken.")
    osynliga = [tecken for tecken in namn if unicodedata.category(tecken) in ("Cc", "Cf")]
    if osynliga:
        raise filsort.fel(
            var + ": " + vad + " innehåller tecknet U+" + format(ord(osynliga[0]), "04X")
            + ", som är ett styrtecken eller ett osynligt tecken. Sådana tecken får inte finnas i "
            + ett_namn + "."
        )
    return namn.strip()


def _inga_dubbla_kolumnnamn(kolumner, var, filsort):
    """Varje uppgift i kolumner ({nyckel: kolumnnamn}) måste ha ett eget kolumnnamn."""
    for nyckel, namn in kolumner.items():
        andra = [annan for annan, annat_namn in kolumner.items() if annat_namn == namn and annan != nyckel]
        if andra:
            raise filsort.fel(
                var + ": kolumnnamnet " + repr(namn) + " används för både " + repr(nyckel)
                + " och " + repr(andra[0]) + ". Varje kolumn måste ha ett eget namn."
            )


def _kontrollera_avgransare(avgransare, kolumner, var, filsort):
    """Kontrollerar formatets lista med avgränsare och returnerar den som en ny lista."""
    if not isinstance(avgransare, list) or not avgransare:
        raise filsort.fel(var + ": 'avgransare' ska vara en lista med minst en avgränsare.")
    for tecken in avgransare:
        if not isinstance(tecken, str) or tecken not in _TILLATNA_AVGRANSARE:
            raise filsort.fel(
                var + ": avgränsaren " + repr(tecken) + " är ogiltig. Tillåtna avgränsare är komma,"
                " semikolon, tabb och lodstreck (" + ", ".join(map(repr, _TILLATNA_AVGRANSARE)) + ")."
            )
    if len(set(avgransare)) != len(avgransare):
        raise filsort.fel(var + ": samma avgränsare står flera gånger i 'avgransare'.")
    if any(tecken in namn for tecken in avgransare for namn in kolumner.values()):
        raise filsort.fel(var + ": ett kolumnnamn innehåller en av avgränsarna.")
    return list(avgransare)


# --- Värden i ett JSON-format ---

_JSON_TYPER = {str: "text", int: "heltal", float: "decimaltal", bool: "true eller false", type(None): "null",
               list: "en lista", dict: "ett objekt"}


def _json_typ(varde):
    """Vad ett värde ur ett JSON-format är, för ett felmeddelande, till exempel "decimaltal"."""
    return _JSON_TYPER.get(type(varde), type(varde).__name__)


def _ar_dolt_tecken(tecken):
    """True för ett tecken som inte syns, utom vanligt mellanslag.

    Det gäller allt som normaliseringen för jämförelser tar bort (normalisering.py): blanksteg
    utom vanligt mellanslag, styrtecken, osynliga formattecken (bland dem riktningstecknen),
    tecken som ser tomma ut och alla tecken på Unicodes lista över tecken som inte ska synas (N1,
    granskning 8). Dessutom halva tecken (kategori Cs), som inte är giltig Unicode.
    """
    if tecken == " ":
        return False
    return unicodedata.category(tecken) == "Cs" or not _jamforbar(tecken)


def _inga_dolda_tecken_i_json(data, var, filsort, plats=""):
    """Stoppar formatet om en text någonstans i det, även en nyckel, innehåller ett dolt tecken.

    Ett tecken som har skrivits som kod i JSON (till exempel "\\u200b") blir ett riktigt tecken när
    filen har lästs, och stoppas därför också. plats är var i formatet texten står, för meddelandet.
    """
    if isinstance(data, dict):
        for nyckel, varde in data.items():
            _inga_dolda_tecken_i_json(nyckel, var, filsort, plats + " nyckeln " + repr(nyckel))
            _inga_dolda_tecken_i_json(varde, var, filsort, plats + " " + repr(nyckel))
    elif isinstance(data, list):
        for nummer, varde in enumerate(data, start=1):
            _inga_dolda_tecken_i_json(varde, var, filsort, plats + " nummer " + str(nummer))
    elif isinstance(data, str):
        dolda = [tecken for tecken in data if _ar_dolt_tecken(tecken)]
        if dolda:
            raise filsort.fel(
                var + ":" + (plats or " texten") + " innehåller tecknet U+" + format(ord(dolda[0]), "04X")
                + ", som inte syns (ett styrtecken, ett osynligt tecken eller ett ovanligt blanksteg). Sådana"
                " tecken kan dölja eller ändra text och får inte finnas någonstans i filen."
            )


def _text_i_json(varde, vad, var, filsort):
    """En text som inte är tom och inte har blanksteg först eller sist. Returnerar den."""
    if not isinstance(varde, str):
        raise filsort.fel(var + ": " + vad + " ska vara text, inte " + _json_typ(varde) + ".")
    if not varde.strip():
        raise filsort.fel(var + ": " + vad + " får inte vara tom.")
    if varde != varde.strip():
        raise filsort.fel(var + ": " + vad + " får inte ha blanksteg först eller sist.")
    return varde


def _heltal_i_json(varde, vad, lagst, hogst, var, filsort):
    """Ett heltal från lagst till och med hogst. true/false, decimaltal och text stoppas. Returnerar det."""
    # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
    if type(varde) is not int:
        raise filsort.fel(var + ": " + vad + " ska vara ett heltal, inte " + _json_typ(varde) + ".")
    if not lagst <= varde <= hogst:
        raise filsort.fel(
            var + ": " + vad + " ska vara från " + str(lagst) + " till och med " + str(hogst) + ", inte "
            + str(varde) + "."
        )
    return varde


def _datumtext(varde, vad, var, filsort):
    """Ett giltigt datum som text, ÅÅÅÅ-MM-DD. Returnerar det som text."""
    if isinstance(varde, str) and _DATUM.fullmatch(varde):
        try:
            dt.date.fromisoformat(varde)
            return varde
        except ValueError:
            pass
    visas = repr(varde) if isinstance(varde, str) else _json_typ(varde)
    raise filsort.fel(var + ": " + vad + " ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte " + visas + ".")


# --- Filen: teckenkodning och styrtecken ---

def _las_fil(sokvag, filsort, hogst=None):
    """Filens innehåll som bytes. En fil som saknas eller inte går att läsa stoppas.

    Med hogst läses högst hogst + 1 byte, så att anroparen ser att filen är för stor utan att
    hela filen läses in. En fil som aldrig tar slut (till exempel en länk till en enhet) blir då
    inget problem.
    """
    if not _ar_sokvag(sokvag):
        raise filsort.fel(filsort.filen + " stoppas: " + _sokvagens_typ(sokvag))
    try:
        with open(sokvag, "rb") as fil:
            return fil.read() if hogst is None else fil.read(hogst + 1)
    except FileNotFoundError:
        raise filsort.fel(filsort.filen + " stoppas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise filsort.fel(filsort.filen + " stoppas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise filsort.fel(
            filsort.filen + " stoppas: filen " + str(sokvag) + " går inte att läsa ("
            + (fel.strerror or str(fel)) + ")."
        ) from None


def _avkoda(data, filsort):
    """Returnerar (filens text, True om den var giltig UTF-8). Provar UTF-8 först och Windows-1252 sedan."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise filsort.fel(
            filsort.filen + " stoppas: filen är sparad som UTF-16 (\"Unicode-text\"), som inte stöds. "
            + filsort.exportera_igen + ", eller spara den som UTF-8 eller CSV."
        )
    try:
        return data.decode("utf-8-sig"), True
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252"), False
    except UnicodeDecodeError:
        raise filsort.fel(filsort.filen + " stoppas: teckenkodningen är varken UTF-8 eller Windows-1252.") from None


def _filrad_for(text, position):
    """Radnumret i filen för en position i texten. Räknar bara \\n, \\r och \\r\\n, som en vanlig textredigerare."""
    return len(_RADSLUT.findall(text, 0, position)) + 1


def _nul_fel(filrad, filsort):
    """Felet för ett NUL-tecken (tecken nummer 0) på raden filrad. Anroparen räknar ut raden."""
    return filsort.fel(
        filsort.filen + " stoppas: rad " + str(filrad) + " i filen innehåller ett NUL-tecken"
        " (tecken nummer 0). Filen är troligen trasig eller sparad i fel format."
    )


def _inga_otillatna_tecken(text, filsort):
    """Stoppar filen om den innehåller ett styrtecken utom tabb, \\n och \\r, U+2028/U+2029 eller ett riktningstecken."""
    fynd = _OTILLATNA_TECKEN.search(text)
    if fynd:
        raise filsort.fel(
            filsort.filen + " stoppas: rad " + str(_filrad_for(text, fynd.start())) + " i filen innehåller tecknet U+"
            + format(ord(fynd.group()), "04X") + ", som är ett styrtecken eller en ovanlig radbrytning. "
            + filsort.om_styrtecken
        )
    fynd = _RIKTNINGSTECKEN.search(text)
    if fynd:
        raise filsort.fel(
            filsort.filen + " stoppas: rad " + str(_filrad_for(text, fynd.start())) + " i filen innehåller tecknet U+"
            + format(ord(fynd.group()), "04X") + ", som är ett riktningstecken. Riktningstecken är osynliga och"
            " får text att visas i en annan ordning än den är lagrad, så att till exempel en beskrivning kan se ut"
            " som en annan text än den är."
        )


# --- CSV-läsningen ---

def _rubrikens_falt(rad, avgransare_lista, kolumner):
    """(avgränsare, fälten) om raden är en rubrikrad med alla kolumnnamnen, annars None.

    Avgränsarna prövas i tur och ordning. Fälten har mellanslagen runt om borttagna.
    """
    for avgransare in avgransare_lista:
        try:
            falt = [f.strip() for f in next(csv.reader([rad], delimiter=avgransare), [])]
        except csv.Error:
            continue  # raden går inte att tolka, så den är ingen rubrikrad
        if all(namn in falt for namn in kolumner.values()):
            return avgransare, falt
    return None


def _csv_fel(fel, var, filsort):
    """Översätter ett fel från csv-läsaren till ett fel med svenskt meddelande."""
    if "field larger than field limit" in str(fel):
        return filsort.fel(
            var + " har ett fält som är längre än " + str(csv.field_size_limit())
            + " tecken. Filen är troligen trasig."
        )
    return filsort.fel(
        var + " kan inte tolkas som CSV, till exempel på grund av ett citattecken i fel läge."
        + " Teknisk detalj: " + str(fel) + "."
    )


def _csv_rader(textrader, forsta_filrad, avgransare, antal_kolumner, filsort):
    """Läser raderna efter rubrikraden. Ger (filrad, var, fälten) för varje rad som inte är tom.

    textrader är filens rader efter rubrikraden, och forsta_filrad radnumret i filen för den
    första av dem. var är början på felmeddelanden om raden. En rad som inte går att tolka, som
    har en radbrytning inuti ett fält eller som har ett annat antal fält än rubrikraden stoppar
    filen.
    """
    # strict=True: text direkt efter ett citerat fält, som "REF"X, stoppar filen i stället för
    # att tyst läsas som REFX.
    lasare = csv.reader(textrader, delimiter=avgransare, strict=True)
    lasta_rader = 0  # antal textrader som läsaren har gått igenom
    while True:
        filrad = forsta_filrad + lasta_rader  # raden i filen där posten börjar
        var = filsort.filen + " stoppas: rad " + str(filrad) + " i filen"
        try:
            falt = next(lasare)
        except StopIteration:
            return
        except csv.Error as fel:
            raise _csv_fel(fel, var, filsort) from None
        lasta_rader = lasare.line_num
        if not falt or all(not f.strip() for f in falt):
            continue  # tom rad
        for index, text in enumerate(falt):
            if any(tecken in text for tecken in _RADBRYTNINGAR):
                raise filsort.fel(
                    var + " har en radbrytning inuti fält nummer " + str(index + 1)
                    + ". Det beror troligen på ett citattecken i fel läge, som kan slå ihop "
                    + filsort.ihopslaget + " till en."
                )
        if len(falt) != antal_kolumner:
            raise filsort.fel(
                var + " har " + str(len(falt)) + " fält, men rubrikraden har " + str(antal_kolumner) + "."
            )
        yield filrad, var, falt


def _tolka_datum(text, kolumn, var, filsort):
    """Ett datum som ÅÅÅÅ-MM-DD, som text. Ett ogiltigt datum stoppar filen."""
    if _DATUM.fullmatch(text):
        try:
            dt.date.fromisoformat(text)
            return text
        except ValueError:
            pass
    raise filsort.fel(var + " har ett ogiltigt datum i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")


def _tolka_ore(text, kolumn, var, filsort):
    """Ett belopp som heltal i öre, med belopp.tolka_belopp. Ett ogiltigt belopp stoppar filen."""
    try:
        return tolka_belopp(text)
    except ValueError:
        raise filsort.fel(var + " har ett ogiltigt belopp i kolumnen " + repr(kolumn) + ": " + repr(text) + ".") from None
