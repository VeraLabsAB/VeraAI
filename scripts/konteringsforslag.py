"""Konteringsförslaget: en verifikation som ännu inte är bokförd, med kontrollerna K2 och ursprunget.

Ett konteringsförslag är en verifikation som Vera föreslår, plus det som en människa behöver för att
förstå och godkänna den (DESIGN-regelbok.md avsnitt 3). Förslaget är aldrig en bokföring. Det har
inget fält för att vara bokfört eller godkänt, och inget här skriver till kundens bokföringsprogram
eller till en SIE-fil. Det sker först efter godkännande (SPEC avsnitt 4, steg 9).

skapa_konteringsforslag är den enda offentliga funktionen som skapar ett förslag. Den tar emot
förslaget som ett objekt (se nedan), regelboken från las_regelbok, kontoplanen från las_kontoplan och
perioderna från las_underlagsperiod, las_bankfil (eller sla_ihop_bankperioder) och las_kassaperiod,
och kör alltid alla kontroller. En period som förslaget inte behöver får vara None. Bara om allt
stämmer returneras ett Konteringsforslag, som inte går att ändra och bara kan skapas där. Annars
stoppas förslaget med ett KonteringsforslagFel, och inget förslag skapas. Det är ett fel i kärnan,
inte ett ärende: det betyder att koden som räknade fram förslaget har räknat fel.

Ingen siffra i förslaget får komma från modellen. Därför bär varje rad sitt ursprung, och kontrollen
räknar själv om varje belopp ur källorna. Alla belopp är heltal i öre. Ingen avrundning görs någonstans:
de tre sätten att räkna (lika, summa och skillnad) är bara addition och subtraktion av heltal, så
beloppen går alltid jämnt ut. Om momsen stämmer med momssatsen för datumet är kontrollen K5, som
byggs i nästa steg (DESIGN avsnitt 7, uppgift 4).

Förslaget som objekt har exakt nycklarna i FORSLAG_NYCKLAR:

  forslag_id    förslagets id, text
  verifikation  exakt nycklarna i VERIFIKATION_NYCKLAR:
                  datum  verifikationens datum, ÅÅÅÅ-MM-DD
                  text   verifikationens text
                  rader  en lista med rader. En rad har exakt nycklarna i RAD_NYCKLAR:
                           konto       kontonumret som text
                           debet_ore   heltal i öre, 0 eller mer
                           kredit_ore  heltal i öre, 0 eller mer
                           ursprung    exakt nycklarna i URSPRUNG_NYCKLAR: berakning (en av
                                       BERAKNINGAR) och fran (en lista med källor)
  kopplingar    exakt nycklarna i KOPPLINGAR_NYCKLAR: underlag och bankrader (listor med objekt med
                nyckeln id), z_rapporter (en lista med objekt med nycklarna kassaregister och
                znummer) och regel (ett objekt med nyckeln id, regelns id i regelboken)
  motivering    varför förslaget ser ut som det gör, text för godkännaren

Allt i förslaget ska vara objekt (dict), listor, text och heltal. En text får inte vara tom, inte ha
blanksteg först eller sist och inte ha något dolt tecken (samma tecken som normalisering.py tar bort,
utom vanligt mellanslag).

En källa i fran pekar på ett värde i en av perioderna (KALLOR):

  underlag   id och falt. falt är belopp_ore (att betala), eller underlag_ore eller moms_ore i en
             momsrad. För en momsrad krävs också momssats, som säger vilken momsrad det är
  bankrad    id (bankradens id från las_bankfil) och falt, som är belopp_ore
  z_rapport  kassaregister (namnet som i kassaformatets lista), znummer och postnamn, och sats för
             en post med momssats

Värdet är källans belopp i öre. En bankrad med pengar ut har ett negativt belopp, som räknas som
positivt: det är sidan raden står på som visar riktningen. Ett negativt värde i en Z-rapport stoppar
förslaget, eftersom det inte är bestämt hur returer ska bokföras.

Sätten att räkna (berakning):

  lika      beloppet är värdet i exakt en källa
  summa     beloppet är summan av två eller fler källor
  skillnad  beloppet är den första källan minus de andra, med minst två källor

K2 (debet = kredit), i Python:

  1. verifikationen har minst två rader,
  2. varje belopp är ett heltal (inte True eller False, som annars räknas som 1 och 0 i Python), inte
     negativt och har högst HELTAL_HOGST_SIFFROR siffror,
  3. på varje rad är exakt ett av debet_ore och kredit_ore större än 0,
  4. summan av all debet är lika med summan av all kredit,
  5. varje konto finns i kontoplanen och gäller på verifikationens datum.

Ursprunget, direkt efter K2:

  1. varje rad har ett ursprung med ett känt sätt att räkna och rätt antal källor, och ingen källa står
     två gånger på samma rad,
  2. varje källa finns i perioderna,
  3. beloppet som kontrollen själv räknar fram ur källorna är exakt radens belopp,
  4. varje underlag, bankrad och Z-rapport som en rad använder står i kopplingar, var och en en gång,
     och varje som står i kopplingar används av minst en rad. Regeln finns i regelboken,
  5. en rad på ett momskonto har bara momsbelopp som källor, och rätt sorts moms. På kontot för
     ingående moms (rollen ingaende_moms i kontoplanen) är källan moms_ore i en momsrad i ett underlag.
     På ett konto för utgående moms (rollen utgaende_moms_per_sats) är källan en momspost i en
     Z-rapport, med en av kontots satser. Sidan (debet eller kredit) prövas inte, eftersom det inte är
     bestämt hur kreditnotor ska bokföras,
  6. en rad på bankkontot (rollen bank i kontoplanen) har bara bankrader som källor, räknade med lika
     eller summa, och står på rätt sida: pengar in i debet och pengar ut i kredit,
  7. täckningen: raderna tillsammans använder varje värde i källorna högst en gång per sida, så att
     inget räknas två gånger (se nedan).

Täckningen. Varje källa består av delar:

  underlag   en del per momsrad och fält: underlag_ore och moms_ore. belopp_ore består av alla
             underlagets delar (summan av momsraderna, K13)
  bankrad    en del, bankradens belopp
  z_rapport  försäljningen med en sats består av två delar: försäljningen utan moms och momsen med
             samma sats. Momsposten är bara momsdelen, och totalsumman består av alla
             försäljningens delar. Ett betalsätt är en egen del

För debet och för kredit räknas hur många gånger varje del används, med tecken: på en rad som räknas
med skillnad dras källorna efter den första ifrån (minus en gång), annars läggs de till (plus en
gång). Regeln:

  a. varje del används 0 eller 1 gång i debet, och 0 eller 1 gång i kredit,
  b. på varje sida är det som kommer från ett underlag antingen 0 eller hela belopp_ore: underlaget
     används helt eller inte alls på en sida.

a stoppar samma värde två gånger på en sida (dubbel moms, samma bankrad två gånger, moms både i
bruttot och för sig) och en skillnad som drar ifrån något som sidan inte tar med (ett belopp ur två
orelaterade underlag). b stoppar ett underlag där en del saknas, till exempel momsen. Kortavgiften
(DESIGN 4d: kortförsäljningen minus bankraden) godtas: bankraden läggs till och dras ifrån i debet och
används där 0 gånger. Samma del får stå en gång i debet och en gång i kredit (till exempel bankraden
på både bankkontot och kostnaden i 4e).

Kopplingarna i förslaget får regelbokens kontrollsumma och kontrollsumman för varje fil förslaget
bygger på (underlaget, bankfilen och Z-filen). Summorna kommer från inläsningen, aldrig från indata.
"""

import datetime as dt
import re
import unicodedata
import weakref
from types import MappingProxyType
from typing import NamedTuple

from las_bank import Bankperiod, kronor
from las_kassa import Kassaperiod
from las_kontoplan import Kontoplan, KontoplanFel
from las_regelbok import Regelbok
from las_underlag import HELTAL_HOGST_SIFFROR, Underlagsperiod
from normalisering import normalisera_for_jamforelse

FORSLAG_NYCKLAR = ("forslag_id", "verifikation", "kopplingar", "motivering")
# "datum" är samma ord som underlagets egen nyckel för datumet (las_underlag.NYCKLAR).
VERIFIKATION_NYCKLAR = ("datum", "text", "rader")
RAD_NYCKLAR = ("konto", "debet_ore", "kredit_ore", "ursprung")
URSPRUNG_NYCKLAR = ("berakning", "fran")
BERAKNINGAR = ("lika", "summa", "skillnad")
KOPPLINGAR_NYCKLAR = ("underlag", "bankrader", "z_rapporter", "regel")
# Nycklarna i varje post i kopplingarnas listor.
KOPPLINGARNAS_NYCKLAR = {"underlag": ("id",), "bankrader": ("id",), "z_rapporter": ("kassaregister", "znummer")}
# Källorna en rad kan räknas ur: nycklarna utöver "kalla", och de valfria nycklarna.
KALLOR = {
    "underlag": (("id", "falt"), ("momssats",)),
    "bankrad": (("id", "falt"), ()),
    "z_rapport": (("kassaregister", "znummer", "postnamn"), ("sats",)),
}
# Fälten som en källa kan peka på. Namnen är underlagets och bankradens egna (las_underlag, las_bank).
UNDERLAGETS_FALT = ("belopp_ore",)
MOMSRADENS_FALT = ("underlag_ore", "moms_ore")
BANKRADENS_FALT = ("belopp_ore",)

# Det största beloppet på en rad, som för talen i underlagen.
_HOGSTA_BELOPP = 10 ** HELTAL_HOGST_SIFFROR - 1

# Kontrollernas namn i felen.
_INDATA = "indata"
_K2 = "K2"
_URSPRUNG = "ursprung"

# Rollerna i kontoplanen som kontrollerna känner igen (las_kontoplan.ROLLER), och kassans post för moms
# (las_kassa.POSTTYPER).
_BANK = "bank"
_INGAENDE_MOMS = "ingaende_moms"
_UTGAENDE_MOMS = "utgaende_moms_per_sats"
_MOMSPOST = "moms_per_sats"
_FORSALJNINGSPOST = "forsaljning_per_sats"
_TOTALSUMMA = "totalsumma"
# Fälten i en momsrad: beloppet utan moms och momsen.
_UNDERLAGSFALT = "underlag_ore"
_MOMSFALT = "moms_ore"
# Sidorna i täckningen.
_SIDOR = ("debet", "kredit")
_DELARNA = ("Ett underlags 'belopp_ore' räknas som alla dess momsraders '" + _UNDERLAGSFALT + "' och '" + _MOMSFALT
            + "', och en Z-rapports försäljning med en sats som försäljningen utan moms plus momsen med samma sats.")

_DATUMFORM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)


class KonteringsforslagFel(Exception):
    """Förslaget skapades inte. kontroll är "indata", "K2" eller "ursprung", efter vad som slog larm."""

    def __init__(self, meddelande, kontroll):
        super().__init__(meddelande)
        self.kontroll = kontroll


def _fel(kontroll, text):
    return KonteringsforslagFel("Konteringsförslaget skapas inte (" + kontroll + "): " + text, kontroll)


_SORTER = {str: "text", int: "ett heltal", float: "ett decimaltal", bool: "True eller False", type(None): "None",
           list: "en lista", tuple: "en tupel", dict: "ett objekt"}


def _sort(varde):
    """Vad ett värde är, för ett felmeddelande, till exempel "ett decimaltal"."""
    return _SORTER.get(type(varde), type(varde).__name__)


# --- Formen ---

def _ren_kopia(varde, plats):
    """En kopia av förslaget med bara objekt, listor, text, tal, True, False och None. Annat stoppas.

    Kopian görs innan något kontrolleras, så att förslaget inte kan ändras under kontrollerna, och så
    att ett objekt som bara liknar en dict eller lista aldrig kommer in. type() i stället för
    isinstance(), så att en underklass med egna regler inte släpps igenom.
    """
    if type(varde) is dict:
        kopia = {}
        for nyckel, del_ in varde.items():
            if type(nyckel) is not str:
                raise _fel(_INDATA, plats + " har nyckeln " + repr(nyckel) + ", som inte är text.")
            kopia[nyckel] = _ren_kopia(del_, plats + ", " + repr(nyckel))
        return kopia
    if type(varde) is list:
        return [_ren_kopia(del_, plats + ", nummer " + str(nummer)) for nummer, del_ in enumerate(varde, start=1)]
    if varde is None or type(varde) in (str, int, float, bool):
        return varde
    raise _fel(_INDATA, plats + " är " + _sort(varde) + ". Förslaget får bara innehålla objekt (dict), listor,"
                        " text, tal, True, False och None.")


def _nycklar(varde, nycklar, valfria, vad, kontroll=_INDATA):
    """varde ska vara ett objekt med alla nycklarna och inga andra än de valfria. Returnerar det."""
    if type(varde) is not dict:
        raise _fel(kontroll, vad + " ska vara ett objekt (dict), inte " + _sort(varde) + ".")
    saknas = [nyckel for nyckel in nycklar if nyckel not in varde]
    if saknas:
        raise _fel(kontroll, vad + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in varde if nyckel not in nycklar + valfria)
    if okanda:
        raise _fel(kontroll, vad + " har en okänd nyckel: " + ", ".join(map(repr, okanda)) + ". Tillåtna nycklar är "
                   + ", ".join(map(repr, nycklar + valfria)) + ".")
    return varde


def _lista(varde, vad):
    if type(varde) is not list:
        raise _fel(_INDATA, vad + " ska vara en lista, inte " + _sort(varde) + ".")
    return varde


def _ar_dolt(tecken):
    """True för ett tecken som inte syns, utom vanligt mellanslag: det som normaliseringen tar bort.

    Dessutom halva tecken (kategori Cs), som inte är giltig Unicode.
    """
    if tecken == " ":
        return False
    return unicodedata.category(tecken) == "Cs" or not normalisera_for_jamforelse(tecken)


def _text(varde, vad, kontroll=_INDATA):
    """En text som inte är tom, inte har blanksteg först eller sist och inte har något dolt tecken."""
    if type(varde) is not str:
        raise _fel(kontroll, vad + " ska vara text, inte " + _sort(varde) + ".")
    if not varde.strip():
        raise _fel(kontroll, vad + " får inte vara tom.")
    if varde != varde.strip():
        raise _fel(kontroll, vad + " får inte ha blanksteg först eller sist.")
    dolda = [tecken for tecken in varde if _ar_dolt(tecken)]
    if dolda:
        raise _fel(kontroll, vad + " innehåller tecknet U+" + format(ord(dolda[0]), "04X") + ", som inte syns (ett"
                   " styrtecken, ett osynligt tecken eller ett ovanligt blanksteg). Sådana tecken kan dölja eller"
                   " ändra text för godkännaren.")
    return varde


def _heltal(varde, vad, kontroll):
    """Ett heltal som inte är negativt. True och False räknas inte som heltal."""
    if type(varde) is not int:
        raise _fel(kontroll, vad + " ska vara ett heltal, inte " + _sort(varde) + ".")
    if varde < 0:
        raise _fel(kontroll, vad + " är negativt (" + str(varde) + ").")
    return varde


def _datum(varde, vad):
    """Ett giltigt datum som text, ÅÅÅÅ-MM-DD."""
    if type(varde) is str and _DATUMFORM.fullmatch(varde):
        try:
            dt.date.fromisoformat(varde)
            return varde
        except ValueError:
            pass
    raise _fel(_INDATA, vad + " ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte "
               + (repr(varde) if type(varde) is str else _sort(varde)) + ".")


def _kontrollera_formen(forslag):
    """Kopierar förslaget och kontrollerar formen: nycklar, listor, texter och datum. Returnerar kopian."""
    try:
        forslag = _ren_kopia(forslag, "förslaget")
    except RecursionError:
        raise _fel(_INDATA, "förslaget har för många objekt och listor inuti varandra.") from None
    _nycklar(forslag, FORSLAG_NYCKLAR, (), "förslaget")
    _text(forslag["forslag_id"], "'forslag_id'")
    _text(forslag["motivering"], "'motivering'")
    verifikation = _nycklar(forslag["verifikation"], VERIFIKATION_NYCKLAR, (), "'verifikation'")
    _datum(verifikation["datum"], "'datum' i 'verifikation'")
    _text(verifikation["text"], "'text' i 'verifikation'")
    for nummer, rad in enumerate(_lista(verifikation["rader"], "'rader' i 'verifikation'"), start=1):
        vad = "rad " + str(nummer)
        _nycklar(rad, RAD_NYCKLAR, (), vad)
        _nycklar(rad["ursprung"], URSPRUNG_NYCKLAR, (), "'ursprung' på " + vad)
        _lista(rad["ursprung"]["fran"], "'fran' i 'ursprung' på " + vad)
    kopplingar = _nycklar(forslag["kopplingar"], KOPPLINGAR_NYCKLAR, (), "'kopplingar'")
    for typ, nycklar in KOPPLINGARNAS_NYCKLAR.items():
        for nummer, post in enumerate(_lista(kopplingar[typ], repr(typ) + " i 'kopplingar'"), start=1):
            vad = "post nummer " + str(nummer) + " i " + repr(typ) + " i 'kopplingar'"
            _nycklar(post, nycklar, (), vad)
            for nyckel in nycklar:
                if nyckel == "znummer":
                    _heltal(post[nyckel], repr(nyckel) + " i " + vad, _INDATA)
                else:
                    _text(post[nyckel], repr(nyckel) + " i " + vad)
    _text(_nycklar(kopplingar["regel"], ("id",), (), "'regel' i 'kopplingar'")["id"], "'id' i 'regel' i 'kopplingar'")
    return forslag


def _kontrollera_indatans_typer(regelbok, kontoplan, underlagsperiod, bankperiod, kassaperiod):
    """Regelboken, kontoplanen och perioderna ska komma från de enda tillåtna inläsningsfunktionerna."""
    # type() i stället för isinstance(), så att en underklass med egna regler inte släpps igenom.
    if type(regelbok) is not Regelbok:
        raise _fel(_INDATA, "regelboken ska komma från las_regelbok, inte vara " + type(regelbok).__name__ + ".")
    if type(kontoplan) is not Kontoplan:
        raise _fel(_INDATA, "kontoplanen ska komma från las_kontoplan, inte vara " + type(kontoplan).__name__ + ".")
    for period, klass, vad, funktion in (
            (underlagsperiod, Underlagsperiod, "underlagsperioden", "las_underlagsperiod"),
            (bankperiod, Bankperiod, "bankperioden", "las_bankfil eller sla_ihop_bankperioder"),
            (kassaperiod, Kassaperiod, "kassaperioden", "las_kassaperiod")):
        if period is not None and type(period) is not klass:
            raise _fel(_INDATA, vad + " ska komma från " + funktion + " (eller vara None), inte vara "
                       + type(period).__name__ + ".")


# --- K2 ---

def _radens_belopp(rad):
    return rad["debet_ore"] or rad["kredit_ore"]


def _kontrollera_k2(verifikation, kontoplan):
    """K2: minst två rader, rätta belopp, en sida per rad, debet = kredit och konton som finns på datumet."""
    rader = verifikation["rader"]
    if len(rader) < 2:
        raise _fel(_K2, "verifikationen har " + str(len(rader)) + " rad" + ("" if len(rader) == 1 else "er")
                   + ", men en verifikation ska ha minst två rader.")
    for nummer, rad in enumerate(rader, start=1):
        for falt in ("debet_ore", "kredit_ore"):
            belopp, vad = rad[falt], repr(falt) + " på rad " + str(nummer)
            # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
            if type(belopp) is not int:
                raise _fel(_K2, vad + " ska vara ett heltal i öre, inte " + _sort(belopp) + ".")
            if belopp < 0:
                raise _fel(_K2, vad + " är negativt (" + kronor(belopp) + "). Inget belopp får vara negativt."
                           " Minus visas genom att beloppet står på andra sidan.")
            if belopp > _HOGSTA_BELOPP:
                raise _fel(_K2, vad + " har fler än " + str(HELTAL_HOGST_SIFFROR) + " siffror. Beloppet är"
                           " troligen fel räknat.")
        if (rad["debet_ore"] > 0) == (rad["kredit_ore"] > 0):
            raise _fel(_K2, "rad " + str(nummer) + " har " + ("både debet och kredit" if rad["debet_ore"] > 0 else
                                                              "varken debet eller kredit")
                       + ". På varje rad ska exakt ett av 'debet_ore' och 'kredit_ore' vara större än 0.")
    debet = sum(rad["debet_ore"] for rad in rader)
    kredit = sum(rad["kredit_ore"] for rad in rader)
    if debet != kredit:
        raise _fel(_K2, "summan av debet är " + kronor(debet) + ", men summan av kredit är " + kronor(kredit)
                   + ", skillnad " + kronor(debet - kredit) + ". Debet och kredit ska alltid vara lika.")
    for nummer, rad in enumerate(rader, start=1):
        if type(rad["konto"]) is not str:
            raise _fel(_K2, "'konto' på rad " + str(nummer) + " ska vara text, till exempel \"1234\", inte "
                       + _sort(rad["konto"]) + ".")
        try:
            kontoplan.kontots_namn(rad["konto"], verifikation["datum"])
        except KontoplanFel as fel:
            raise _fel(_K2, "rad " + str(nummer) + ": " + str(fel)) from None


# --- Ursprunget ---

class _Del(NamedTuple):
    """En del av en källa, som täckningen räknar (punkt 7 överst i filen)."""

    nyckel: tuple  # vilken del det är
    visas: str     # delen i ett felmeddelande
    belopp: int    # delens värde i öre


class _Varde(NamedTuple):
    """Ett värde ur en källa, som kontrollen själv har slagit upp i perioderna."""

    nyckel: tuple          # vilket värde det är, för att hitta en källa som står två gånger
    visas: str             # källan i ett felmeddelande
    belopp: int            # värdet i öre, aldrig negativt
    moms: object           # vilken sorts moms värdet är: "underlag" (moms_ore i en momsrad i ett underlag),
                           # "z_rapport" (en momspost i en Z-rapport), eller None om det inte är moms
    sats: object           # momssatsen, eller None om källan inte har någon
    koppling: tuple        # (typen i kopplingar, vad som står där): ("underlag", id) och så vidare
    bankens_belopp: object  # bankradens belopp med tecken (in är positivt, ut negativt), annars None
    delar: tuple           # delarna som värdet består av (_Del), för täckningen


class _Kallorna(NamedTuple):
    """Det som källorna slås upp i. None om förslaget inte fick perioden."""

    underlag: object     # {id: underlaget}
    bankrader: object    # {id: bankraden}
    z_rapporter: object  # {(kassaregister, znummer): raderna i Z-rapporten}


def _kallorna(underlagsperiod, bankperiod, kassaperiod):
    return _Kallorna(
        None if underlagsperiod is None else {underlag["id"]: underlag for underlag in underlagsperiod.underlag},
        None if bankperiod is None else {rad["id"]: rad for rad in bankperiod.rader},
        None if kassaperiod is None else {(rader[0]["kassaregister"], rader[0]["znummer"]): rader
                                          for rader in kassaperiod.rapporter},
    )


def _falt(kalla, tillatna, vad):
    falt = kalla["falt"]
    if type(falt) is not str or falt not in tillatna:
        raise _fel(_URSPRUNG, "'falt' i " + vad + " ska vara en av " + ", ".join(map(repr, tillatna)) + ", inte "
                   + (repr(falt) if type(falt) is str else _sort(falt)) + ".")
    return falt


def _underlagets_varde(kalla, vad, underlagen):
    if underlagen is None:
        raise _fel(_URSPRUNG, vad + " pekar på ett underlag, men förslaget fick ingen underlagsperiod.")
    id_ = _text(kalla["id"], "'id' i " + vad, _URSPRUNG)
    falt = _falt(kalla, UNDERLAGETS_FALT + MOMSRADENS_FALT, vad)
    if id_ not in underlagen:
        raise _fel(_URSPRUNG, vad + " pekar på underlaget " + repr(id_) + ", som inte finns i underlagsperioden. Det"
                   " kan ha ett datum utanför perioden, eller vara en dublett som K4 har tagit bort.")
    underlag = underlagen[id_]
    if falt in UNDERLAGETS_FALT:
        if "momssats" in kalla:
            raise _fel(_URSPRUNG, vad + " har 'momssats', men " + repr(falt) + " står inte i en momsrad. 'momssats'"
                       " hör bara till fälten " + ", ".join(map(repr, MOMSRADENS_FALT)) + ".")
        # belopp_ore är summan av momsraderna (K13), så det består av alla underlagets delar.
        return _Varde(("underlag", id_, None, falt), "underlaget " + repr(id_) + ", " + repr(falt), underlag[falt],
                      None, None, ("underlag", id_), None, _underlagets_delar(id_, underlag))
    if "momssats" not in kalla:
        raise _fel(_URSPRUNG, vad + " pekar på " + repr(falt) + " i en momsrad men saknar 'momssats', som säger"
                   " vilken momsrad det är.")
    sats = _heltal(kalla["momssats"], "'momssats' i " + vad, _URSPRUNG)
    momsrader = [rad for rad in underlag["moms"] if rad["momssats"] == sats]
    if not momsrader:
        raise _fel(_URSPRUNG, vad + ": underlaget " + repr(id_) + " har ingen momsrad med satsen " + str(sats) + " %."
                   " Satserna i underlaget är " + ", ".join(str(rad["momssats"]) + " %" for rad in underlag["moms"])
                   + ".")
    del_ = _momsradens_del(id_, momsrader[0], falt)
    return _Varde(del_.nyckel, del_.visas, del_.belopp, "underlag" if falt == _MOMSFALT else None, sats,
                  ("underlag", id_), None, (del_,))


def _momsradens_del(id_, momsrad, falt):
    """Fältet falt i en momsrad i underlaget id_, som en del för täckningen."""
    return _Del(("underlag", id_, momsrad["momssats"], falt), "underlaget " + repr(id_) + ", momsraden med satsen "
                + str(momsrad["momssats"]) + " %, " + repr(falt), momsrad[falt])


def _underlagets_delar(id_, underlag):
    """Alla delar i underlaget: underlag_ore och moms_ore i varje momsrad."""
    return tuple(_momsradens_del(id_, momsrad, falt) for momsrad in underlag["moms"] for falt in MOMSRADENS_FALT)


def _bankradens_varde(kalla, vad, bankrader):
    if bankrader is None:
        raise _fel(_URSPRUNG, vad + " pekar på en bankrad, men förslaget fick ingen bankperiod.")
    id_ = _text(kalla["id"], "'id' i " + vad, _URSPRUNG)
    falt = _falt(kalla, BANKRADENS_FALT, vad)
    if id_ not in bankrader:
        raise _fel(_URSPRUNG, vad + " pekar på bankraden " + repr(id_) + ", som inte finns i bankperioden.")
    belopp = bankrader[id_][falt]
    # Pengar ut har ett negativt belopp. På vilken sida raden står visar riktningen.
    del_ = _Del(("bankrad", id_, falt), "bankraden " + repr(id_) + " (radnummer " + str(bankrader[id_]["radnr"]) + ")",
                abs(belopp))
    return _Varde(del_.nyckel, del_.visas, del_.belopp, None, None, ("bankrader", id_), belopp, (del_,))


def _z_postens_varde(kalla, vad, rapporterna):
    if rapporterna is None:
        raise _fel(_URSPRUNG, vad + " pekar på en Z-rapport, men förslaget fick ingen kassaperiod.")
    kassaregister = _text(kalla["kassaregister"], "'kassaregister' i " + vad, _URSPRUNG)
    znummer = _heltal(kalla["znummer"], "'znummer' i " + vad, _URSPRUNG)
    postnamn = _text(kalla["postnamn"], "'postnamn' i " + vad, _URSPRUNG)
    sats = _heltal(kalla["sats"], "'sats' i " + vad, _URSPRUNG) if "sats" in kalla else None
    rapport = rapporterna.get((kassaregister, znummer))
    if rapport is None:
        raise _fel(_URSPRUNG, vad + " pekar på Z-rapport " + str(znummer) + " från kassaregistret "
                   + repr(kassaregister) + ", som inte finns i kassaperioden.")
    visas = "Z-rapport " + str(znummer) + " (" + kassaregister + "), posten " + repr(postnamn) + (
        "" if sats is None else " med satsen " + str(sats) + " %")
    poster = [rad for rad in rapport if rad["postnamn"] == postnamn and rad["sats"] == sats]
    if not poster:
        raise _fel(_URSPRUNG, vad + ": " + visas + " finns inte. Posterna i rapporten är " + ", ".join(
            repr(rad["postnamn"]) + ("" if rad["sats"] is None else " med satsen " + str(rad["sats"]) + " %")
            for rad in rapport) + ".")
    post = poster[0]
    if post["belopp_ore"] < 0:
        raise _fel(_URSPRUNG, vad + ": " + visas + " är negativ (" + kronor(post["belopp_ore"]) + "). Hur returer"
                   " och andra negativa poster i kassan ska bokföras är inte bestämt.")
    return _Varde(("z_rapport", kassaregister, znummer, postnamn, sats), visas, post["belopp_ore"],
                  "z_rapport" if post["posttyp"] == _MOMSPOST else None, post["sats"],
                  ("z_rapporter", (kassaregister, znummer)), None, _z_postens_delar(post, rapport))


def _z_postens_delar(post, rapport):
    """Delarna i en post i Z-rapporten (rapport är alla dess rader), för täckningen.

    Försäljningen med en sats är försäljningen utan moms plus momsen med samma sats (Z-kontroll e).
    Totalsumman är all försäljning (Z-kontroll c). En annan post är en egen del.
    """
    rapporten = "Z-rapport " + str(post["znummer"]) + " (" + post["kassaregister"] + "), "
    borjan = ("z_rapport", post["kassaregister"], post["znummer"])
    if post["posttyp"] == _TOTALSUMMA:
        return tuple(del_ for rad in rapport if rad["posttyp"] == _FORSALJNINGSPOST
                     for del_ in _z_postens_delar(rad, rapport))
    if post["posttyp"] not in (_FORSALJNINGSPOST, _MOMSPOST):
        return (_Del(borjan + (post["posttyp"], post["postnamn"]), rapporten + "posten " + repr(post["postnamn"]),
                     post["belopp_ore"]),)
    sats = post["sats"]
    # En sats utan momspost har momsen 0 (Z-kontroll e).
    moms = sum(rad["belopp_ore"] for rad in rapport if rad["posttyp"] == _MOMSPOST and rad["sats"] == sats)
    momsdelen = _Del(borjan + (_MOMSPOST, sats), rapporten + "momsen med satsen " + str(sats) + " %", moms)
    if post["posttyp"] == _MOMSPOST:
        return (momsdelen,)
    return (_Del(borjan + (_FORSALJNINGSPOST, sats), rapporten + "försäljningen utan moms med satsen " + str(sats)
                 + " %", post["belopp_ore"] - moms), momsdelen)


def _sla_upp(kalla, vad, kallorna):
    """Slår upp en källa i perioderna. Returnerar ett _Varde. En källa som inte finns stoppar förslaget."""
    if type(kalla) is not dict:
        raise _fel(_URSPRUNG, vad + " ska vara ett objekt (dict), inte " + _sort(kalla) + ".")
    sort = kalla.get("kalla")
    if type(sort) is not str or sort not in KALLOR:
        raise _fel(_URSPRUNG, "'kalla' i " + vad + " ska vara en av " + ", ".join(map(repr, KALLOR)) + ", inte "
                   + (repr(sort) if type(sort) is str else _sort(sort)) + ".")
    nycklar, valfria = KALLOR[sort]
    _nycklar(kalla, ("kalla",) + nycklar, valfria, vad, _URSPRUNG)
    if sort == "underlag":
        return _underlagets_varde(kalla, vad, kallorna.underlag)
    if sort == "bankrad":
        return _bankradens_varde(kalla, vad, kallorna.bankrader)
    return _z_postens_varde(kalla, vad, kallorna.z_rapporter)


def _rakna(berakning, belopp):
    """Beloppet räknat ur källornas värden, i öre."""
    if berakning == "lika":
        return belopp[0]
    if berakning == "summa":
        return sum(belopp)
    return belopp[0] - sum(belopp[1:])


def _kontrollera_momskonto(roller, varden, vad):
    """En rad på ett momskonto har bara momsbelopp som källor, av rätt sort och med rätt sats.

    Ingående moms kommer bara från moms_ore i en momsrad i ett underlag, och utgående moms bara från
    en momspost i en Z-rapport med en av kontots satser. Sidan prövas inte (kreditnotor är inte bestämda).
    """
    ingaende = (_INGAENDE_MOMS, None) in roller
    satser = [sats for roll, sats in roller if roll == _UTGAENDE_MOMS]
    if not ingaende and not satser:
        return
    utgaende = "kontot för utgående moms med satsen " + " och ".join(str(sats) + " %" for sats in satser)
    for varde in varden:
        if varde.moms is None:
            raise _fel(_URSPRUNG, vad + " är ett momskonto, men källan " + varde.visas + " är inte ett momsbelopp. En"
                       " rad på ett momskonto ska ha momsen i en momsrad ('" + _MOMSFALT + "') eller en momspost i en"
                       " Z-rapport som ursprung.")
        if varde.moms == "underlag" and ingaende:
            continue
        if varde.moms == "z_rapport" and varde.sats in satser:
            continue
        if varde.moms == "underlag":
            raise _fel(_URSPRUNG, vad + " är " + utgaende + ", men källan " + varde.visas + " är momsen i ett"
                       " underlag. Utgående moms ska komma från en momspost i en Z-rapport.")
        if not satser:
            raise _fel(_URSPRUNG, vad + " är kontot för ingående moms, men källan " + varde.visas + " är momsen i en"
                       " Z-rapport. Ingående moms ska komma från momsen i en momsrad i ett underlag ('" + _MOMSFALT
                       + "').")
        raise _fel(_URSPRUNG, vad + " är " + utgaende + ", men källan " + varde.visas + " har satsen "
                   + str(varde.sats) + " %.")


def _kontrollera_bankkonto(rad, roller, berakning, varden, vad):
    """En rad på bankkontot har bara bankrader som källor, räknade med lika eller summa, och rätt riktning."""
    if (_BANK, None) not in roller:
        return
    if berakning not in ("lika", "summa"):
        raise _fel(_URSPRUNG, vad + " är bankkontot och räknas med " + repr(berakning) + ". En rad på bankkontot ska"
                   " vara en eller flera bankrader, räknade med 'lika' eller 'summa'.")
    for varde in varden:
        if varde.bankens_belopp is None:
            raise _fel(_URSPRUNG, vad + " är bankkontot, men källan " + varde.visas + " är inte en bankrad. Pengar på"
                       " banken ska alltid komma från en bankrad.")
        if (varde.bankens_belopp > 0) != (rad["debet_ore"] > 0):
            raise _fel(_URSPRUNG, vad + " är bankkontot och står i " + ("debet" if rad["debet_ore"] > 0 else "kredit")
                       + ", men " + varde.visas + " är pengar " + ("in" if varde.bankens_belopp > 0 else "ut") + ". Pengar"
                       " in står i debet på bankkontot och pengar ut i kredit.")


def _kopplingens_uppgifter(typ, vad, kallorna):
    """En post i kopplingarna, med kontrollsumman från inläsningen."""
    if typ == "underlag":
        return {"id": vad, "kontrollsumma": kallorna.underlag[vad]["kalla_fil"]}
    if typ == "bankrader":
        rad = kallorna.bankrader[vad]
        return {"id": vad, "radnr": rad["radnr"], "filens_kontrollsumma": rad["kalla_fil"]}
    rader = kallorna.z_rapporter[vad]
    return {"kassaregister": vad[0], "znummer": vad[1], "rapportdatum": rader[0]["rapportdatum"],
            "filens_kontrollsumma": rader[0]["kalla_fil"]}


def _visa_koppling(typ, vad):
    if typ == "z_rapporter":
        return "Z-rapport " + str(vad[1]) + " (" + vad[0] + ")"
    return ("underlaget " if typ == "underlag" else "bankraden ") + repr(vad)


def _kontrollera_kopplingar(kopplingar, anvanda, regelbok, kallorna):
    """Kopplingarna och raderna använder samma källor, och regeln finns. Returnerar de nya kopplingarna."""
    nya = {}
    for typ, nycklar in KOPPLINGARNAS_NYCKLAR.items():
        angivna = [post[nycklar[0]] if len(nycklar) == 1 else tuple(post[nyckel] for nyckel in nycklar)
                   for post in kopplingar[typ]]
        for nummer, vad in enumerate(angivna):
            if vad in angivna[:nummer]:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " står flera gånger i " + repr(typ)
                           + " i 'kopplingar'.")
        for vad in anvanda[typ]:
            if vad not in angivna:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " används av en rad, men står inte i " + repr(typ)
                           + " i 'kopplingar'.")
        for vad in angivna:
            if vad not in anvanda[typ]:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " står i " + repr(typ) + " i 'kopplingar', men"
                           " ingen rad använder det.")
        nya[typ] = [_kopplingens_uppgifter(typ, vad, kallorna) for vad in angivna]
    regelns_id = kopplingar["regel"]["id"]
    if not any(regel["id"] == regelns_id for regel in regelbok.regler):
        raise _fel(_URSPRUNG, "regeln " + repr(regelns_id) + " i 'kopplingar' finns inte i regelboken.")
    nya["regel"] = {"id": regelns_id, "regelbokens_kontrollsumma": regelbok.kontrollsumma}
    return nya


def _visa_rader(nummer):
    """Radnumren i ett felmeddelande, till exempel "rad 2" eller "rad 1, 2 och 4"."""
    nummer = [str(tal) for tal in sorted(set(nummer))]
    return "rad " + (nummer[0] if len(nummer) == 1 else ", ".join(nummer[:-1]) + " och " + nummer[-1])


def _kontrollera_tackning(raderna, underlagen, kallorna):
    """Täckningen, punkt 7 överst i filen.

    raderna är (radnummer, sida, berakning, värdena) för varje rad, och underlagen är id för
    underlagen som raderna använder.
    """
    for sida in _SIDOR:
        antal = {}  # delens nyckel: [delen, antal gånger med tecken, radnumren]
        for nummer, radens_sida, berakning, varden in raderna:
            if radens_sida != sida:
                continue
            for plats, varde in enumerate(varden):
                tecken = -1 if berakning == "skillnad" and plats > 0 else 1
                for del_ in varde.delar:
                    rakning = antal.setdefault(del_.nyckel, [del_, 0, []])
                    rakning[1] += tecken
                    rakning[2].append(nummer)
        for del_, ganger, nummer in antal.values():
            if ganger > 1:
                raise _fel(_URSPRUNG, "i " + sida + " används " + del_.visas + " " + str(ganger) + " gånger ("
                           + _visa_rader(nummer) + "). Varje del av en källa får användas högst en gång i debet och"
                           " en gång i kredit, så att inget värde räknas två gånger. " + _DELARNA)
            if ganger < 0:
                raise _fel(_URSPRUNG, "i " + sida + " dras " + del_.visas + " ifrån " + str(-ganger) + " gång"
                           + ("" if ganger == -1 else "er") + " mer än den läggs till (" + _visa_rader(nummer) + "). En"
                           " skillnad får bara dra ifrån något som samma sida också tar med. " + _DELARNA)
        for id_ in underlagen:
            underlag = kallorna.underlag[id_]
            delar = _underlagets_delar(id_, underlag)
            anvanda = [del_ for del_ in delar if del_.nyckel in antal and antal[del_.nyckel][1] == 1]
            anvant = sum(del_.belopp for del_ in anvanda)
            if anvant not in (0, underlag["belopp_ore"]):
                saknas = [del_ for del_ in delar if del_ not in anvanda and del_.belopp]
                raise _fel(_URSPRUNG, "i " + sida + " används " + kronor(anvant) + " av underlaget " + repr(id_)
                           + ", men ett underlag ska användas helt eller inte alls på varje sida: 0 kr eller hela"
                           " 'belopp_ore', " + kronor(underlag["belopp_ore"]) + ". Det som saknas är " + "; ".join(
                               del_.visas + ": " + kronor(del_.belopp) for del_ in saknas) + ".")


def _kontrollera_ursprung(forslag, regelbok, kontoplan, kallorna):
    """Ursprungskontrollen, punkt 1–7 överst i filen. Returnerar kopplingarna med kontrollsummorna."""
    anvanda = {typ: [] for typ in KOPPLINGARNAS_NYCKLAR}
    raderna = []
    for nummer, rad in enumerate(forslag["verifikation"]["rader"], start=1):
        vad = "rad " + str(nummer) + " (konto " + rad["konto"] + ")"
        berakning, fran = rad["ursprung"]["berakning"], rad["ursprung"]["fran"]
        if type(berakning) is not str or berakning not in BERAKNINGAR:
            raise _fel(_URSPRUNG, "'berakning' på " + vad + " ska vara en av " + ", ".join(map(repr, BERAKNINGAR))
                       + ", inte " + (repr(berakning) if type(berakning) is str else _sort(berakning)) + ".")
        if berakning == "lika" and len(fran) != 1:
            raise _fel(_URSPRUNG, vad + " räknas med 'lika' och ska ha exakt en källa i 'fran', men har "
                       + str(len(fran)) + ".")
        if berakning != "lika" and len(fran) < 2:
            raise _fel(_URSPRUNG, vad + " räknas med " + repr(berakning) + " och ska ha minst två källor i 'fran', men"
                       " har " + str(len(fran)) + ".")
        varden = []
        for kallans_nummer, kalla in enumerate(fran, start=1):
            varde = _sla_upp(kalla, "källa nummer " + str(kallans_nummer) + " på " + vad, kallorna)
            if any(annat.nyckel == varde.nyckel for annat in varden):
                raise _fel(_URSPRUNG, vad + " har " + varde.visas + " flera gånger i 'fran'. Varje källa får stå en"
                           " gång på en rad, så att inget värde räknas två gånger.")
            varden.append(varde)
            typ, vad_i_kopplingar = varde.koppling
            if vad_i_kopplingar not in anvanda[typ]:
                anvanda[typ].append(vad_i_kopplingar)
        raknat = _rakna(berakning, [varde.belopp for varde in varden])
        if raknat != _radens_belopp(rad):
            raise _fel(_URSPRUNG, vad + " har beloppet " + kronor(_radens_belopp(rad)) + ", men " + repr(berakning)
                       + " av källorna (" + "; ".join(varde.visas + ": " + kronor(varde.belopp) for varde in varden)
                       + ") blir " + kronor(raknat) + ", skillnad " + kronor(_radens_belopp(rad) - raknat) + ".")
        roller = kontoplan.kontots_roller(rad["konto"])
        _kontrollera_momskonto(roller, varden, vad)
        _kontrollera_bankkonto(rad, roller, berakning, varden, vad)
        raderna.append((nummer, _SIDOR[0] if rad["debet_ore"] > 0 else _SIDOR[1], berakning, varden))
    kopplingar = _kontrollera_kopplingar(forslag["kopplingar"], anvanda, regelbok, kallorna)
    _kontrollera_tackning(raderna, anvanda["underlag"], kallorna)
    return kopplingar


# --- Förslaget ---

def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor blir tupler."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, list):
        return tuple(_frys(del_) for del_ in varde)
    return varde


def _kopia(varde):
    """En vanlig kopia av ett fryst värde, som anroparen får ändra utan att förslaget ändras."""
    if isinstance(varde, MappingProxyType):
        return {nyckel: _kopia(del_) for nyckel, del_ in varde.items()}
    if isinstance(varde, tuple):
        return [_kopia(del_) for del_ in varde]
    return varde


# Nyckeln som bara skapa_konteringsforslag har. Utan den går det inte att skapa ett Konteringsforslag
# som inte har gått igenom K2 och ursprungskontrollen.
_FORSLAGSNYCKEL = object()

# Innehållet i varje förslag. Det ligger här och inte i förslaget självt, så att ett förslag inte har
# något som går att ändra, och så att ett förslag som har skapats förbi skapa_konteringsforslag (till
# exempel med object.__new__) är tomt och inte går att läsa. Ett test (test_inga_genvagar.py) stoppar
# annan kärnkod från att använda nyckeln och innehållet.
_FORSLAGEN = weakref.WeakKeyDictionary()


def _innehallet(forslag):
    try:
        return _FORSLAGEN[forslag]
    except KeyError:
        raise KonteringsforslagFel("Förslaget har inte skapats av skapa_konteringsforslag och kan inte läsas.",
                                   _INDATA) from None


class Konteringsforslag:
    """Ett konteringsförslag från skapa_konteringsforslag. Kan bara skapas där och kan inte ändras.

    Förslaget är aldrig bokfört eller godkänt och har inget fält för det. Varje gång en del läses ges
    en ny kopia, så att en ändring i den aldrig når förslaget.
    """

    __slots__ = ("__weakref__",)

    def __init__(self, nyckel, innehall):
        if nyckel is not _FORSLAGSNYCKEL:
            raise KonteringsforslagFel("Ett Konteringsforslag kan bara skapas av skapa_konteringsforslag, som kör K2"
                                       " och ursprungskontrollen först.", _INDATA)
        if self in _FORSLAGEN:
            raise KonteringsforslagFel("Ett Konteringsforslag kan inte ändras.", _INDATA)
        _FORSLAGEN[self] = _frys(innehall)

    def __setattr__(self, namn, varde):
        raise AttributeError("Ett Konteringsforslag kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("Ett Konteringsforslag kan inte ändras.")

    @property
    def forslag_id(self):
        return _innehallet(self)["forslag_id"]

    @property
    def verifikation(self):
        """Datum, text och rader, som en ny kopia. Varje rad har konto, debet_ore, kredit_ore och ursprung."""
        return _kopia(_innehallet(self)["verifikation"])

    @property
    def kopplingar(self):
        """Underlagen, bankraderna, Z-rapporterna och regeln, med kontrollsummorna, som en ny kopia."""
        return _kopia(_innehallet(self)["kopplingar"])

    @property
    def motivering(self):
        return _innehallet(self)["motivering"]

    @property
    def kontroller(self):
        """Kontrollerna som förslaget har klarat, som en ny kopia."""
        return _kopia(_innehallet(self)["kontroller"])

    def __repr__(self):
        innehall = _innehallet(self)
        verifikation = innehall["verifikation"]
        return ("Konteringsforslag(" + repr(innehall["forslag_id"]) + ", " + verifikation["datum"] + ", "
                + str(len(verifikation["rader"])) + " rader, debet = kredit = "
                + kronor(sum(rad["debet_ore"] for rad in verifikation["rader"])) + ")")


def skapa_konteringsforslag(forslag, regelbok, kontoplan, underlagsperiod=None, bankperiod=None, kassaperiod=None):
    """Kontrollerar förslaget med K2 och ursprungskontrollen. Returnerar ett Konteringsforslag, annars fel.

    forslag är förslaget som objekt (se överst i filen). regelbok ska komma från las_regelbok,
    kontoplan från las_kontoplan, underlagsperiod från las_underlagsperiod, bankperiod från las_bankfil
    eller sla_ihop_bankperioder och kassaperiod från las_kassaperiod. En period som förslaget inte
    använder får vara None. Allt som inte går ihop stoppar förslaget med ett KonteringsforslagFel.
    """
    _kontrollera_indatans_typer(regelbok, kontoplan, underlagsperiod, bankperiod, kassaperiod)
    nytt = _kontrollera_formen(forslag)
    _kontrollera_k2(nytt["verifikation"], kontoplan)
    kopplingar = _kontrollera_ursprung(nytt, regelbok, kontoplan, _kallorna(underlagsperiod, bankperiod, kassaperiod))
    return Konteringsforslag(_FORSLAGSNYCKEL, {
        "forslag_id": nytt["forslag_id"],
        "verifikation": nytt["verifikation"],
        "kopplingar": kopplingar,
        "motivering": nytt["motivering"],
        "kontroller": {_K2: "ok", _URSPRUNG: "ok"},
    })
