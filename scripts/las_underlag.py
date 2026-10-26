"""Läser underlag (kvitton och leverantörsfakturor) och kontrollerar dem, med K4 (dubbletter).

Ett underlag är ett kvitto eller en leverantörsfaktura i Veras interna form: en JSON-fil per
dokument, med uppgifterna som har lästs ur kvittot eller fakturan. Formen är densamma för alla
företag och beskrivs därför här, inte i foretag/<namn>/. Filen ska ha exakt de här nycklarna,
inga fler och inga färre (NYCKLAR):

  id             dokumentets id, en icke-tom text. Filen heter id + ".json"
  typ            en av TYPER
  datum          fakturadatum eller kvittodatum, ett giltigt datum som text, ÅÅÅÅ-MM-DD
  motpart        motpartens namn, en icke-tom text
  fakturanummer  faktura- eller kvittonumret, en icke-tom text
  belopp_ore     att betala inklusive moms, heltal i öre
  moms           en lista med en rad per momssats, minst en rad. Varje rad har exakt nycklarna
                 MOMSRAD_NYCKLAR: momssatsen i procent och beloppet utan moms och momsen, heltal i
                 öre. Ett momsfritt underlag har en rad med sats 0 och moms 0 (beslut i SPEC 11)
  flaggor        en lista med korta texter

Alla tal ska vara heltal i JSON, aldrig decimaltal, text, true/false, NaN eller Infinity, och
högst HELTAL_HOGST_SIFFROR siffror långa. Negativa tal stoppas: hur kreditnotor ska behandlas är
inte bestämt. En text får vara högst TEXT_HOGST_TECKEN tecken. En text som bara består av
blanksteg och osynliga tecken räknas som tom.

Förväxlingstecken (J1) är tecken som ser ut som andra tecken, till exempel ett kyrilliskt "А" som
ser ut som ett latinskt "A". De kan dölja att två underlag är samma. Därför stoppas:

- ett ord i motpart eller fakturanummer som blandar latinska bokstäver med bokstäver från ett
  annat skriftsystem (till exempel kyrilliska eller grekiska). Ord helt på ett annat språk godtas,
- ett fakturanummer med andra tecken än a–z, siffror, bindestreck, snedstreck, punkt och
  understreck, efter normaliseringen för jämförelser (normalisering.py: blanksteg och osynliga
  tecken räknas inte, alla sorters bindestreck räknas som "-", stora och små bokstäver är samma).

Intern kontroll (K13): summan av underlag_ore och moms_ore över alla momsrader ska vara lika med
belopp_ore. Eftersom varje underlag har minst en momsrad kontrolleras alla underlag så.

Inläsningen skyddas på samma sätt som bank- och kassafilen, med de gemensamma skydden i
inlasning_skydd.py: sökvägen ska vara text eller en Path, filen får vara högst FIL_HOGST_BYTE
byte och läses aldrig längre än så, den ska vara sparad som UTF-8, NUL-tecken, styrtecken och
riktningstecken stoppar filen, och dubbla nycklar och för djup nästling stoppar filen. Styrtecken,
riktningstecken och halva tecken som har skrivits som koder i JSON (till exempel "\\u202e")
stoppas också, eftersom de blir riktiga tecken när filen har lästs.

las_underlagsperiod är den enda offentliga funktionen. Den läser alla underlag i en mapp, var och
en med alla kontroller ovan, stoppar perioden om två filer har samma id, och kör sedan K4 på
underlagen med datum i perioden. Mappen får bara innehålla underlag, vanliga filer vars namn slutar
på exakt FILANDELSE (J6). Allt annat stoppar perioden, till exempel en undermapp, en fil som heter
".JSON", en symbolisk länk (länkar följs aldrig) eller en rörledning. Bara filerna i
IGNORERADE_FILER hoppas över.

  K4: två underlag med samma motpart, fakturanummer, belopp_ore och datum är dubbletter. Motpart
  och fakturanummer jämförs efter normaliseringen för jämförelser (normalisering.py). Underlaget
  med lägst id behålls. De andra blir ärenden, "dublett av <id>", med kontrollen K4.
  K4a och K4b: samma motpart och fakturanummer med ett annat belopp (K4a) eller ett annat datum
  (K4b) är också ett ärende, eftersom det kan vara fel, men då behålls båda underlagen. Skiljer
  både beloppet och datumet är ärendet både K4a och K4b, och texten nämner båda.
  K4c, möjlig dublett (L1, granskning 6): samma belopp_ore och datum, och samma motpart ELLER
  samma fakturanummer (efter normaliseringen för jämförelser), men inte båda. Det kan vara samma
  underlag med ett förväxlat tecken, till exempel "F-l001" (litet L) i stället för "F-1001", eller
  en motpart i ett annat skriftsystem som ser likadan ut. Underlaget med högre id blir ett ärende,
  "möjlig dublett av <id>", med kontrollen K4c. Båda underlagen behålls, och en människa avgör. Ett
  underlag som redan har ett ärende från K4, K4a eller K4b får inget ärende från K4c.

Resultatet är en Underlagsperiod, som inte går att ändra. Vid minsta fel i en fil stoppas hela
perioden med ett UnderlagFilFel som pekar ut filen, och inget returneras.

Texterna i underlaget är data, aldrig instruktioner (K17). Koden här läser dem bara, jämför dem
och lämnar dem vidare oförändrade.
"""

import datetime as dt
import hashlib
import json
import re
import stat
import unicodedata
from pathlib import Path
from types import MappingProxyType

from inlasning_skydd import (
    _DATUM, _RADBRYTNINGAR, _RIKTNINGSTECKEN, _DubbelNyckel, _Filsort, _ar_sokvag, _filrad_for, _inga_dubbla_nycklar,
    _inga_otillatna_tecken, _las_fil, _nul_fel, _sokvagens_typ,
)
from las_bank import kronor as _kronor
from las_kassa import normalisera_kassaregister as _normalisera
from normalisering import blandat_ord as _blandat_ord
from normalisering import normalisera_for_jamforelse as _jamforbar
from normalisering import tecken_med_namn as _tecken_med_namn

# Underlagets form. Gemensam för alla företag.
NYCKLAR = ("id", "typ", "datum", "motpart", "fakturanummer", "belopp_ore", "moms", "flaggor")
MOMSRAD_NYCKLAR = ("momssats", "underlag_ore", "moms_ore")
TYPER = ("leverantorsfaktura", "kvitto")
FILANDELSE = ".json"
# Filer i underlagsmappen som inte är underlag och hoppas över. macOS lägger .DS_Store i mappar som
# har öppnats i Finder.
IGNORERADE_FILER = (".DS_Store",)

# Ett tecken som ett fakturanummer får innehålla efter normaliseringen för jämförelser (J1).
_FAKTURANUMRETS_TECKEN = re.compile(r"[a-z0-9/._-]", re.ASCII)

# Kontrollernas namn i K4:s ärenden (SPEC avsnitt 6).
_K4 = "K4"     # dublett
_K4A = "K4a"   # samma motpart och fakturanummer, olika belopp
_K4B = "K4b"   # samma motpart och fakturanummer, olika datum
_K4C = "K4c"   # möjlig dublett: samma belopp och datum, och samma motpart eller fakturanummer

# Gränser som skyddar mot trasiga filer. De gäller alla företag och ligger därför här. Ett
# underlag är några hundra byte, så 1 MB ger mycket god marginal. Femton siffror räcker till
# belopp upp till tusentals miljarder kronor, och ett längre tal betyder att filen är trasig.
FIL_HOGST_BYTE = 1_000_000
TEXT_HOGST_TECKEN = 200
HELTAL_HOGST_SIFFROR = 15


class UnderlagFilFel(Exception):
    """Ett underlag kunde inte läsas in. Hela perioden är stoppad."""


# Det som skiljer underlagets felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
# filen byts ut mot filens namn för varje fil som läses, så att varje meddelande pekar ut filen.
_UNDERLAGSFIL = _Filsort(
    fel=UnderlagFilFel,
    filen="Underlaget",
    formatet="Underlaget",
    exportera_igen="Spara underlaget igen",
    om_styrtecken="Sådana tecken finns inte i ett vanligt underlag, och de kan dölja eller ändra text.",
    ihopslaget="flera uppgifter",
    nivaer="Ett underlag har bara tre nivåer.",
)

_JSON_TYPER = {str: "text", int: "heltal", float: "decimaltal", bool: "true eller false", type(None): "null",
               list: "en lista", dict: "ett objekt"}


def _typnamn(varde):
    return _JSON_TYPER.get(type(varde), type(varde).__name__)


def _visa(varde):
    """Ett värde ur filen, kort, för ett felmeddelande. Bara text och heltal visas, annat med sin sort.

    Texten visas med repr, så att osynliga tecken syns som koder och inte följer med som de är.
    """
    if isinstance(varde, str):
        return repr(varde[:40]) + ("…" if len(varde) > 40 else "")
    if type(varde) is int:
        return str(varde)
    return _typnamn(varde)


# --- Filen ---

def _avkoda_utf8(data, var, filsort):
    """Filens text. Bara UTF-8 (med eller utan BOM) godtas. NUL, styrtecken och riktningstecken stoppas."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise filsort.fel(var + ": filen är sparad som UTF-16, men ett underlag ska vara sparat som UTF-8.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as fel:
        raise filsort.fel(
            var + ": filen är inte giltig UTF-8 (fel vid byte " + str(fel.start + 1) + "). Ett underlag ska vara"
            " sparat som UTF-8."
        ) from None
    if "\x00" in text:
        raise _nul_fel(_filrad_for(text, text.index("\x00")), filsort)
    _inga_otillatna_tecken(text, filsort)
    return text


class _OgiltigtTal(Exception):
    """Ett tal som inte får finnas i ett underlag. Fångas i _tolka_json."""


def _heltal_ur_json(text):
    """Ett heltal i JSON. Längden prövas innan talet räknas ut, så att ett jättelångt tal inte tar tid."""
    siffror = len(text.lstrip("-"))
    if siffror > HELTAL_HOGST_SIFFROR:
        raise _OgiltigtTal(
            "ett heltal med " + str(siffror) + " siffror, men ett tal i ett underlag får ha högst "
            + str(HELTAL_HOGST_SIFFROR) + " siffror"
        )
    return int(text)


def _konstant_ur_json(namn):
    """NaN, Infinity och -Infinity. Pythons JSON-läsare godtar dem, men de är inga tal."""
    raise _OgiltigtTal(namn + ", som inte är ett tal. Alla tal i ett underlag ska vara heltal")


def _tolka_json(text, var, filsort):
    """Filens innehåll som Python-värden. Innehållet är inte kontrollerat; det gör _kontrollera_underlag."""
    try:
        return json.loads(text, object_pairs_hook=_inga_dubbla_nycklar, parse_int=_heltal_ur_json,
                          parse_constant=_konstant_ur_json)
    except json.JSONDecodeError as fel:
        raise filsort.fel(
            var + ": filen är inte giltig JSON (rad " + str(fel.lineno) + ", tecken " + str(fel.colno) + ")."
        ) from None
    except _DubbelNyckel as fel:
        raise filsort.fel(var + ": " + str(fel) + ".") from None
    except _OgiltigtTal as fel:
        raise filsort.fel(var + ": filen innehåller " + str(fel) + ".") from None
    except RecursionError:
        raise filsort.fel(
            var + ": för många hakparenteser eller klammerparenteser inuti varandra. " + filsort.nivaer
            + " Filen är troligen trasig."
        ) from None


# --- Uppgifterna i underlaget ---

def _exakta_nycklar(objekt, nycklar, vad, var, filsort):
    """objekt ska vara ett JSON-objekt med exakt nycklarna, inga fler och inga färre."""
    if not isinstance(objekt, dict):
        raise filsort.fel(var + ": " + vad + " ska vara ett objekt med nycklar, inte " + _typnamn(objekt) + ".")
    saknas = [nyckel for nyckel in nycklar if nyckel not in objekt]
    if saknas:
        raise filsort.fel(var + ": " + vad + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in objekt if nyckel not in nycklar)
    if okanda:
        raise filsort.fel(
            var + ": " + vad + " har en okänd nyckel: " + ", ".join(map(_visa, okanda[:3]))
            + (" med flera" if len(okanda) > 3 else "") + ". Tillåtna nycklar är "
            + ", ".join(map(repr, nycklar)) + "."
        )


def _kontrollera_text(varde, vad, var, filsort):
    """En icke-tom text på högst TEXT_HOGST_TECKEN tecken, utan styrtecken, riktningstecken eller halva tecken."""
    if not isinstance(varde, str):
        raise filsort.fel(var + ": " + vad + " ska vara text, inte " + _typnamn(varde) + ".")
    if len(varde) > TEXT_HOGST_TECKEN:
        raise filsort.fel(
            var + ": " + vad + " är " + str(len(varde)) + " tecken lång, men en text i ett underlag får vara högst "
            + str(TEXT_HOGST_TECKEN) + " tecken. Den börjar " + _visa(varde) + "."
        )
    for tecken in varde:
        kod = "U+" + format(ord(tecken), "04X")
        if tecken == "\x00":
            raise filsort.fel(var + ": " + vad + " innehåller ett NUL-tecken (tecken nummer 0).")
        if unicodedata.category(tecken) == "Cc" or tecken in _RADBRYTNINGAR:
            raise filsort.fel(
                var + ": " + vad + " innehåller tecknet " + kod + ", som är ett styrtecken eller en ovanlig"
                " radbrytning. " + filsort.om_styrtecken
            )
        if _RIKTNINGSTECKEN.fullmatch(tecken):
            raise filsort.fel(
                var + ": " + vad + " innehåller tecknet " + kod + ", som är ett riktningstecken. Riktningstecken"
                " är osynliga och får text att visas i en annan ordning än den är lagrad."
            )
        if unicodedata.category(tecken) == "Cs":
            raise filsort.fel(
                var + ": " + vad + " innehåller " + kod + ", ett halvt tecken som inte är giltig Unicode."
            )
    if not _normalisera(varde):
        raise filsort.fel(var + ": " + vad + " får inte vara tom eller bara bestå av blanksteg och osynliga tecken.")
    return varde


def _inga_blandade_ord(text, vad, var, filsort):
    """Inget ord i texten får blanda latinska bokstäver med bokstäver från ett annat skriftsystem (J1).

    Texten Unicode-normaliseras först (NFKC), så att till exempel fullbreddsbokstäver räknas som latinska.
    Samma prövning som regelboken gör (normalisering.blandat_ord).
    """
    blandat = _blandat_ord(text)
    if blandat:
        ord_, bokstav = blandat
        raise filsort.fel(
            var + ": " + vad + " har ordet " + _visa(ord_) + ", som blandar latinska bokstäver med bokstaven "
            + _tecken_med_namn(bokstav) + " från ett annat skriftsystem. En sådan bokstav kan se ut precis som"
            " en latinsk bokstav och dölja att två underlag är samma (en dublett)."
        )


def _kontrollera_fakturanumrets_tecken(fakturanummer, var, filsort):
    """Efter normaliseringen för jämförelser får fakturanumret bara ha a–z, siffror, -, /, . och _ (J1)."""
    for tecken in fakturanummer:
        if not all(_FAKTURANUMRETS_TECKEN.fullmatch(del_) for del_ in _jamforbar(tecken)):
            raise filsort.fel(
                var + ": 'fakturanummer' innehåller tecknet " + _tecken_med_namn(tecken) + ". Ett fakturanummer får"
                " bara innehålla bokstäverna a–z, siffror, bindestreck, snedstreck, punkt och understreck."
                " Blanksteg och osynliga tecken räknas inte, och alla sorters bindestreck räknas som '-'. Andra"
                " tecken kan se ut som vanliga tecken och dölja att två underlag är samma (en dublett)."
            )


def _kontrollera_heltal(varde, vad, var, filsort):
    """Ett heltal i JSON som inte är negativt. Decimaltal, text, true/false och null stoppas."""
    # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
    if type(varde) is not int:
        raise filsort.fel(
            var + ": " + vad + " ska vara ett heltal, till exempel 12345, inte " + _typnamn(varde) + "."
        )
    if varde < 0:
        raise filsort.fel(
            var + ": " + vad + " är negativt (" + str(varde) + "). Negativa tal stoppas tills det är bestämt hur"
            " kreditnotor ska behandlas."
        )
    return varde


def _kontrollera_datum(varde, var, filsort):
    """Ett giltigt datum som text, ÅÅÅÅ-MM-DD."""
    if isinstance(varde, str) and _DATUM.fullmatch(varde):
        try:
            dt.date.fromisoformat(varde)
            return varde
        except ValueError:
            pass
    raise filsort.fel(var + ": 'datum' ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte " + _visa(varde) + ".")


def _kontrollera_momsrader(rader, var, filsort):
    """Listan med momsrader, en rad per momssats och minst en rad. Returnerar nya rader."""
    if not isinstance(rader, list):
        raise filsort.fel(var + ": 'moms' ska vara en lista med momsrader, inte " + _typnamn(rader) + ".")
    if not rader:
        raise filsort.fel(
            var + ": 'moms' har inga momsrader. Varje underlag ska ha minst en momsrad, så att beloppet kan"
            " kontrolleras (K13). Ett momsfritt underlag har en rad med momssats 0 och moms 0."
        )
    resultat = []
    for nummer, rad in enumerate(rader, start=1):
        vad = "momsrad nummer " + str(nummer)
        _exakta_nycklar(rad, MOMSRAD_NYCKLAR, vad, var, filsort)
        ny = {nyckel: _kontrollera_heltal(rad[nyckel], repr(nyckel) + " i " + vad, var, filsort)
              for nyckel in MOMSRAD_NYCKLAR}
        if any(annan["momssats"] == ny["momssats"] for annan in resultat):
            raise filsort.fel(
                var + ": momssatsen " + str(ny["momssats"]) + " % står på flera momsrader. Varje momssats ska"
                " ha en enda rad."
            )
        resultat.append(ny)
    return resultat


def _kontrollera_flaggor(flaggor, var, filsort):
    if not isinstance(flaggor, list):
        raise filsort.fel(var + ": 'flaggor' ska vara en lista med texter, inte " + _typnamn(flaggor) + ".")
    return [_kontrollera_text(flagga, "flagga nummer " + str(nummer), var, filsort)
            for nummer, flagga in enumerate(flaggor, start=1)]


def _kontroll_summa(underlag, var, filsort):
    """K13, intern kontroll: underlag_ore plus moms_ore över alla momsrader är lika med belopp_ore."""
    summa = sum(rad["underlag_ore"] + rad["moms_ore"] for rad in underlag["moms"])
    if summa != underlag["belopp_ore"]:
        raise filsort.fel(
            var + ": beloppen utan moms och momsen på momsraderna summerar till " + _kronor(summa)
            + ", men 'belopp_ore' är " + _kronor(underlag["belopp_ore"]) + ", skillnad "
            + _kronor(summa - underlag["belopp_ore"]) + "."
        )


def _kontrollera_underlag(data, var, filsort):
    """Kontrollerar underlagets uppgifter och returnerar dem som ett nytt objekt."""
    _exakta_nycklar(data, NYCKLAR, "underlaget", var, filsort)
    typ = data["typ"]
    if not isinstance(typ, str) or typ not in TYPER:
        raise filsort.fel(var + ": 'typ' är " + _visa(typ) + ", men ska vara en av " + ", ".join(map(repr, TYPER)) + ".")
    underlag = {
        "id": _kontrollera_text(data["id"], "'id'", var, filsort),
        "typ": typ,
        "datum": _kontrollera_datum(data["datum"], var, filsort),
        "motpart": _kontrollera_text(data["motpart"], "'motpart'", var, filsort),
        "fakturanummer": _kontrollera_text(data["fakturanummer"], "'fakturanummer'", var, filsort),
        "belopp_ore": _kontrollera_heltal(data["belopp_ore"], "'belopp_ore'", var, filsort),
        "moms": _kontrollera_momsrader(data["moms"], var, filsort),
        "flaggor": _kontrollera_flaggor(data["flaggor"], var, filsort),
    }
    _inga_blandade_ord(underlag["motpart"], "'motpart'", var, filsort)
    _inga_blandade_ord(underlag["fakturanummer"], "'fakturanummer'", var, filsort)
    _kontrollera_fakturanumrets_tecken(underlag["fakturanummer"], var, filsort)
    _kontroll_summa(underlag, var, filsort)
    return underlag


def _las_underlagsfil(sokvag):
    """Läser ETT underlag och kör alla kontroller av filen.

    Kör INTE kontrollen av dubbla id och inte K4; det gör las_underlagsperiod. Returnerar
    uppgifterna och kalla_fil, SHA-256 av hela filen.
    """
    if not _ar_sokvag(sokvag):
        raise UnderlagFilFel("Underlaget stoppas: " + _sokvagens_typ(sokvag))
    sokvag = Path(sokvag)
    filsort = _UNDERLAGSFIL._replace(filen="Underlaget " + repr(sokvag.name))
    var = filsort.filen + " stoppas"
    data = _las_fil(sokvag, filsort, hogst=FIL_HOGST_BYTE)
    if len(data) > FIL_HOGST_BYTE:
        raise filsort.fel(
            var + ": filen är större än " + format(FIL_HOGST_BYTE, ",").replace(",", " ") + " byte (1 MB). Ett"
            " underlag är bara några hundra byte, så filen är troligen fel eller trasig."
        )
    text = _avkoda_utf8(data, var, filsort)
    underlag = _kontrollera_underlag(_tolka_json(text, var, filsort), var, filsort)
    if sokvag.name != underlag["id"] + FILANDELSE:
        raise filsort.fel(
            var + ": filen ska heta som underlagets id plus " + repr(FILANDELSE) + ", alltså "
            + repr(underlag["id"] + FILANDELSE) + "."
        )
    underlag["kalla_fil"] = hashlib.sha256(data).hexdigest()
    return underlag


# --- En hel period ---

def _vad_det_ar(lage):
    """Vad något i underlagsmappen är, för felmeddelandet. lage är st_mode från lstat."""
    if stat.S_ISDIR(lage):
        return "är en mapp, inte en fil"
    if stat.S_ISLNK(lage):
        return "är en symbolisk länk (en genväg till en annan fil eller mapp). Länkar följs aldrig"
    if stat.S_ISFIFO(lage):
        return "är en rörledning (FIFO), inte en vanlig fil"
    if stat.S_ISREG(lage):
        return "slutar inte på exakt " + repr(FILANDELSE) + " (stora och små bokstäver räknas)"
    return "är inte en vanlig fil"


def _underlagsfiler(mapp):
    """Sökvägarna till underlagen direkt i mappen, i namnordning.

    Mappen får bara innehålla vanliga filer vars namn slutar på exakt FILANDELSE, utom
    IGNORERADE_FILER. Allt annat stoppar perioden (J6). Varje sak i mappen undersöks med lstat, som
    inte följer symboliska länkar och inte öppnar något, så att en rörledning inte får inläsningen
    att stanna.
    """
    if not _ar_sokvag(mapp):
        raise UnderlagFilFel("Underlagsperioden: " + _sokvagens_typ(mapp))
    mapp = Path(mapp)
    try:
        namn = [fil.name for fil in mapp.iterdir()]
    except FileNotFoundError:
        raise UnderlagFilFel("Underlagsperioden: mappen finns inte: " + str(mapp) + ".") from None
    except NotADirectoryError:
        raise UnderlagFilFel("Underlagsperioden: " + str(mapp) + " är en fil, inte en mapp.") from None
    except OSError as fel:
        raise UnderlagFilFel(
            "Underlagsperioden: mappen " + str(mapp) + " går inte att läsa (" + (fel.strerror or str(fel)) + ")."
        ) from None
    sokvagar = []
    for filnamn in sorted(namn):
        if filnamn in IGNORERADE_FILER:
            continue
        try:
            lage = (mapp / filnamn).lstat().st_mode
        except OSError as fel:
            raise UnderlagFilFel(
                "Underlagsperioden stoppas: " + repr(filnamn) + " i mappen " + str(mapp) + " går inte att undersöka ("
                + (fel.strerror or str(fel)) + ")."
            ) from None
        if not (stat.S_ISREG(lage) and filnamn.endswith(FILANDELSE)):
            raise UnderlagFilFel(
                "Underlagsperioden stoppas: " + repr(filnamn) + " i mappen " + str(mapp) + " " + _vad_det_ar(lage)
                + ". Mappen får bara innehålla underlag: vanliga filer vars namn slutar på exakt " + repr(FILANDELSE)
                + ". Flytta det andra till en annan mapp, så att inget underlag hoppas över utan att det märks."
            )
        sokvagar.append(mapp / filnamn)
    return sokvagar


def _periodens_datum(datum, namn):
    """Ett datum som text, ÅÅÅÅ-MM-DD. Annat stoppas med UnderlagFilFel."""
    if isinstance(datum, str) and _DATUM.fullmatch(datum):
        try:
            dt.date.fromisoformat(datum)
            return datum
        except ValueError:
            pass
    raise UnderlagFilFel(
        "Underlagsperioden: " + namn + " ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte " + repr(datum) + "."
    )


def _inga_dubbla_id(alla):
    """Två filer får inte ha samma id. Jämförs efter normalisering, så "a" och "A" är samma id."""
    sedda = {}  # normaliserat id -> id
    for underlag in alla:
        normaliserat = _normalisera(underlag["id"])
        if normaliserat in sedda:
            raise UnderlagFilFel(
                "Underlagsperioden stoppas: filerna " + repr(sedda[normaliserat] + FILANDELSE) + " och "
                + repr(underlag["id"] + FILANDELSE) + " har samma id (stora och små bokstäver, blanksteg och"
                " osynliga tecken räknas inte). Varje underlag måste ha ett eget id."
            )
        sedda[normaliserat] = underlag["id"]


def _arende(underlag, kontroll, text, jamfort_med):
    return {"kontroll": kontroll, "id": underlag["id"], "text": text, "jamfort_med": jamfort_med["id"]}


def _kontroll_k4(underlag):
    """K4, K4a, K4b och K4c. underlag ska vara sorterade efter id. Returnerar (underlagen som behålls, ärenden).

    Samma motpart, fakturanummer, belopp och datum är en dublett (K4) av det första av dem (lägst
    id), och tas inte med. Samma motpart och fakturanummer men ett annat belopp (K4a) eller datum
    (K4b) blir ett ärende, och båda underlagen behålls. Samma belopp och datum och samma motpart
    eller samma fakturanummer, men inte båda, är en möjlig dublett (K4c, L1): ett ärende, och båda
    underlagen behålls. Motpart och fakturanummer jämförs efter normaliseringen för jämförelser (J1).
    """
    behallna, arenden = [], []
    per_faktura = {}  # (motpart, fakturanummer), normaliserade -> underlag som behålls
    per_motpart_dag = {}  # (motpart, belopp, datum) -> underlag som behålls, för K4c
    per_nummer_dag = {}  # (fakturanummer, belopp, datum) -> underlag som behålls, för K4c
    for post in underlag:
        motpart, nummer = _jamforbar(post["motpart"]), _jamforbar(post["fakturanummer"])
        tidigare = per_faktura.setdefault((motpart, nummer), [])
        original = [annan for annan in tidigare
                    if annan["belopp_ore"] == post["belopp_ore"] and annan["datum"] == post["datum"]]
        if original:
            arenden.append(_arende(post, _K4, "dublett av " + original[0]["id"], original[0]))
            continue
        samma_motpart = per_motpart_dag.setdefault((motpart, post["belopp_ore"], post["datum"]), [])
        samma_nummer = per_nummer_dag.setdefault((nummer, post["belopp_ore"], post["datum"]), [])
        if tidigare:
            forsta = tidigare[0]
            olika_belopp = forsta["belopp_ore"] != post["belopp_ore"]
            if olika_belopp and forsta["datum"] != post["datum"]:
                arenden.append(_arende(post, _K4A + " och " + _K4B, "samma fakturanummer, olika belopp och datum",
                                       forsta))
            elif olika_belopp:
                arenden.append(_arende(post, _K4A, "samma fakturanummer, olika belopp", forsta))
            else:
                arenden.append(_arende(post, _K4B, "samma fakturanummer, olika datum", forsta))
        elif samma_motpart or samma_nummer:
            # Ingen av dem har både samma motpart och samma fakturanummer, för då vore det K4 ovan.
            forsta = min(samma_motpart + samma_nummer, key=lambda annan: annan["id"])
            arenden.append(_arende(post, _K4C, "möjlig dublett av " + forsta["id"], forsta))
        tidigare.append(post)
        samma_motpart.append(post)
        samma_nummer.append(post)
        behallna.append(post)
    return behallna, arenden


def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor tupler."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, list):
        return tuple(_frys(del_) for del_ in varde)
    return varde


def _tina(varde):
    """En vanlig kopia av något som _frys har gjort oföränderligt."""
    if isinstance(varde, MappingProxyType):
        return {nyckel: _tina(del_) for nyckel, del_ in varde.items()}
    if isinstance(varde, tuple):
        return [_tina(del_) for del_ in varde]
    return varde


# Nyckeln som bara las_underlagsperiod har. Utan den går det inte att skapa en Underlagsperiod med
# underlag som inte har gått igenom kontrollerna. Ett test (test_inga_genvagar.py) stoppar annan
# kärnkod från att använda den.
_PERIODNYCKEL = object()


class Underlagsperiod:
    """Underlagen för en period, från las_underlagsperiod. Kan bara skapas där och kan inte ändras.

    underlag är underlagen med datum i perioden som har gått igenom alla kontroller, utom de som K4
    har tagit bort som dubbletter, sorterade efter id. arenden är K4:s ärenden till en människa.
    Varje gång de läses ges nya kopior, så att en ändring i dem aldrig når perioden.
    """

    __slots__ = ("_underlag", "_arenden", "_fran_datum", "_till_datum")

    def __init__(self, nyckel, underlag, arenden, fran_datum, till_datum):
        if nyckel is not _PERIODNYCKEL:
            raise UnderlagFilFel(
                "En Underlagsperiod kan bara skapas av las_underlagsperiod, som läser underlagen och kör alla"
                " kontroller först."
            )
        # object.__setattr__ behövs eftersom vanlig tilldelning är spärrad nedan.
        object.__setattr__(self, "_underlag", _frys(list(underlag)))
        object.__setattr__(self, "_arenden", _frys(list(arenden)))
        object.__setattr__(self, "_fran_datum", fran_datum)
        object.__setattr__(self, "_till_datum", till_datum)

    def __setattr__(self, namn, varde):
        raise AttributeError("En Underlagsperiod kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("En Underlagsperiod kan inte ändras.")

    @property
    def underlag(self):
        return _tina(self._underlag)

    @property
    def arenden(self):
        return _tina(self._arenden)

    @property
    def fran_datum(self):
        return self._fran_datum

    @property
    def till_datum(self):
        return self._till_datum

    def __repr__(self):
        return ("Underlagsperiod(" + self._fran_datum + " till " + self._till_datum + ", "
                + str(len(self._underlag)) + " underlag, " + str(len(self._arenden)) + " ärenden)")


def las_underlagsperiod(mapp, fran_datum, till_datum):
    """Läser underlagen i mappen med datum från fran_datum till till_datum, gränserna medräknade.

    Mappen får bara innehålla underlag, vanliga filer som slutar på exakt FILANDELSE (utom
    IGNORERADE_FILER). Annat stoppar perioden. Alla underlag i mappen läses, var och en med alla
    kontroller, även de med datum utanför perioden: datumet står i filen, och en trasig fil kan inte
    ha ett datum som går att lita på. Två
    filer med samma id stoppar perioden. Sedan körs K4 på underlagen i perioden. Minsta fel stoppar
    hela perioden med UnderlagFilFel, och inget returneras.

    Datumen ges som text, ÅÅÅÅ-MM-DD. En period utan underlag ger en tom Underlagsperiod.
    """
    fran = _periodens_datum(fran_datum, "fran_datum")
    till = _periodens_datum(till_datum, "till_datum")
    if fran > till:
        raise UnderlagFilFel("Underlagsperioden: fran_datum (" + fran + ") ligger efter till_datum (" + till + ").")
    alla = [_las_underlagsfil(sokvag) for sokvag in _underlagsfiler(mapp)]
    _inga_dubbla_id(alla)
    i_perioden = sorted((underlag for underlag in alla if fran <= underlag["datum"] <= till),
                        key=lambda underlag: underlag["id"])
    underlag, arenden = _kontroll_k4(i_perioden)
    return Underlagsperiod(_PERIODNYCKEL, underlag, arenden, fran, till)
