"""Läser och kontrollerar ett företags kontoplan (foretag/<namn>/kontoplan.json).

Kontoplanen listar företagets konton, och säger vilka konton som har en roll som kärnan behöver
känna till, till exempel bankkontot (DESIGN-regelbok.md avsnitt 2). Rollerna behövs eftersom
kärnan aldrig får ha ett kontonummer i sin kod (SPEC 2). Vilket konto som har vilken roll står i
filen, aldrig här.

Filen ska ha exakt nycklarna i KONTOPLAN_NYCKLAR, och får ha nycklarna i KONTOPLAN_VALFRIA_NYCKLAR:

  status      text som säger vad filen är, till exempel "SYNTETISK". Visas för människor. Kärnan
              tolkar den inte
  konton      en lista med minst ett konto. Ett konto har nycklarna i KONTO_NYCKLAR och får ha
              nycklarna i KONTO_VALFRIA_NYCKLAR:
                nummer  kontonumret som text, bara siffrorna 0–9 (högst HELTAL_HOGST_SIFFROR). Text
                        och inte ett tal, så att ett konto som börjar med noll behåller nollan. Varje
                        nummer får bara stå en gång
                namn    kontots namn, text som inte är tom
                fran    första dagen kontot får användas, ÅÅÅÅ-MM-DD. Saknas den gäller kontot från
                        början
                till    sista dagen kontot får användas, ÅÅÅÅ-MM-DD, eller null. Saknas den eller är
                        den null gäller kontot tills vidare
  roller      ett objekt med exakt rollerna i ROLLER. Varje roll pekar på ett konto i 'konton'.
              Rollen utgaende_moms_per_sats är ett objekt med minst en momssats (som text, till
              exempel "25") och kontot för utgående moms med den satsen
  anteckning  fri text för människor. Används inte av koden

Hela filen stoppas vid minsta fel med ett KontoplanFel: okänd eller saknad nyckel, fel typ (till
exempel ett kontonummer som tal i stället för text), ett tomt värde, ett dolt tecken någonstans i
filen (även i nycklar och anteckningar), ett konto som står två gånger, eller en roll som pekar på
ett konto som inte finns. Filen läses med de gemensamma skydden i inlasning_skydd.py (UTF-8, dubbla
nycklar, för djup nästling och för långa tal), som de andra formatfilerna.

las_kontoplan är den enda offentliga funktionen som läser filen. Den kör alltid alla kontroller och
returnerar en Kontoplan, som inte går att ändra och bara kan skapas av las_kontoplan. Varje uppslag
i Kontoplan görs för ett datum. Ett konto som inte finns, eller inte gäller på datumet, stoppar
uppslaget med ett KontoplanFel. Kontot gissas aldrig.
"""

import re
from types import MappingProxyType

from inlasning_skydd import (
    _Filsort, _datumtext, _inga_dolda_tecken_i_json, _json_typ, _kontrollera_nycklar, _ladda_json, _text_i_json,
)
from las_momssatser import HOGSTA_SATS
from las_underlag import HELTAL_HOGST_SIFFROR

KONTOPLAN_NYCKLAR = ("status", "konton", "roller")
KONTOPLAN_VALFRIA_NYCKLAR = ("anteckning",)
KONTO_NYCKLAR = ("nummer", "namn")
KONTO_VALFRIA_NYCKLAR = ("fran", "till")
# Rollerna som kärnan känner till. Alla krävs. Rollerna i ROLLER_PER_SATS har ett konto per momssats.
ROLLER = ("bank", "leverantorsskulder", "ingaende_moms", "utgaende_moms_per_sats")
ROLLER_PER_SATS = ("utgaende_moms_per_sats",)

_KONTONUMMER = re.compile(r"[0-9]{1," + str(HELTAL_HOGST_SIFFROR) + "}", re.ASCII)
# En momssats som text, utan nollor först: "0", "6", "25".
_SATSTEXT = re.compile(r"0|[1-9][0-9]{0,2}", re.ASCII)


class KontoplanFel(Exception):
    """Kontoplanen kunde inte läsas, är fel, eller har inget giltigt konto för ett uppslag."""


# Det som skiljer kontoplanens felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
# Bara fel, formatet och nivaer används för ett JSON-format.
_KONTOPLAN = _Filsort(
    fel=KontoplanFel,
    filen="Kontoplanen",
    formatet="Kontoplanen",
    exportera_igen="Spara filen igen",
    om_styrtecken="Sådana tecken finns inte i en vanlig kontoplan.",
    ihopslaget="flera konton",
    nivaer="En kontoplan har bara tre nivåer.",
)


def _kontonummer(varde, vad, var):
    """Ett kontonummer: text med bara siffrorna 0–9. Returnerar det."""
    if not isinstance(varde, str):
        raise KontoplanFel(
            var + ": " + vad + " ska vara text, till exempel \"1234\", inte " + _json_typ(varde) + ". Ett"
            " kontonummer är text, så att ett konto som börjar med noll behåller nollan."
        )
    if not _KONTONUMMER.fullmatch(varde):
        raise KontoplanFel(
            var + ": " + vad + " är " + repr(varde) + ", men ett kontonummer får bara ha siffrorna 0–9, högst "
            + str(HELTAL_HOGST_SIFFROR) + " stycken."
        )
    return varde


def _kontrollera_konto(konto, vad, var):
    """Ett konto i listan. Returnerar det som ett nytt objekt, med fran och till (None om de saknas)."""
    if not isinstance(konto, dict):
        raise KontoplanFel(var + ": " + vad + " ska vara ett objekt med nycklar, inte " + _json_typ(konto) + ".")
    _kontrollera_nycklar(konto, KONTO_NYCKLAR, KONTO_VALFRIA_NYCKLAR, var + ", " + vad + ",", _KONTOPLAN)
    nytt = {
        "nummer": _kontonummer(konto["nummer"], "'nummer' i " + vad, var),
        "namn": _text_i_json(konto["namn"], "'namn' i " + vad, var, _KONTOPLAN),
        "fran": None,
        "till": None,
    }
    if "fran" in konto:
        nytt["fran"] = _datumtext(konto["fran"], "'fran' i " + vad, var, _KONTOPLAN)
    if konto.get("till") is not None:
        nytt["till"] = _datumtext(konto["till"], "'till' i " + vad, var, _KONTOPLAN)
    if nytt["fran"] is not None and nytt["till"] is not None and nytt["till"] < nytt["fran"]:
        raise KontoplanFel(var + ": " + vad + " slutar " + nytt["till"] + ", före sitt första datum " + nytt["fran"] + ".")
    return nytt


def _kontrollera_konton(konton, var):
    """Listan med konton: minst ett, och varje nummer en gång. Returnerar {nummer: konto}."""
    if not isinstance(konton, list):
        raise KontoplanFel(var + ": 'konton' ska vara en lista med konton, inte " + _json_typ(konton) + ".")
    if not konton:
        raise KontoplanFel(var + ": 'konton' är tom. Kontoplanen ska ha minst ett konto.")
    resultat = {}
    for nummer, konto in enumerate(konton, start=1):
        nytt = _kontrollera_konto(konto, "konto nummer " + str(nummer), var)
        if nytt["nummer"] in resultat:
            raise KontoplanFel(
                var + ": kontot " + repr(nytt["nummer"]) + " står flera gånger i 'konton'. Varje konto ska stå en gång."
            )
        resultat[nytt["nummer"]] = nytt
    return resultat


def _rollens_konto(varde, vad, konton, var):
    """Ett konto för en roll. Det ska finnas i 'konton'."""
    nummer = _kontonummer(varde, vad, var)
    if nummer not in konton:
        raise KontoplanFel(var + ": " + vad + " pekar på kontot " + repr(nummer) + ", som inte finns i 'konton'.")
    return nummer


def _kontrollera_roller(roller, konton, var):
    """Rollerna: exakt ROLLER, och varje konto finns i 'konton'. Returnerar dem som ett nytt objekt."""
    if not isinstance(roller, dict):
        raise KontoplanFel(var + ": 'roller' ska vara ett objekt med roller, inte " + _json_typ(roller) + ".")
    _kontrollera_nycklar(roller, ROLLER, (), var + ", 'roller',", _KONTOPLAN)
    resultat = {}
    for roll in ROLLER:
        vad = "rollen " + repr(roll)
        if roll not in ROLLER_PER_SATS:
            resultat[roll] = _rollens_konto(roller[roll], vad, konton, var)
            continue
        per_sats = roller[roll]
        if not isinstance(per_sats, dict):
            raise KontoplanFel(
                var + ": " + vad + " ska vara ett objekt med ett konto per momssats, inte " + _json_typ(per_sats) + "."
            )
        if not per_sats:
            raise KontoplanFel(var + ": " + vad + " är tom. Den ska ha ett konto för minst en momssats.")
        resultat[roll] = {}
        for sats, konto in per_sats.items():
            if not _SATSTEXT.fullmatch(sats) or int(sats) > HOGSTA_SATS:
                raise KontoplanFel(
                    var + ": " + vad + " har momssatsen " + repr(sats) + ". En momssats skrivs som ett heltal i text,"
                    " från \"0\" till och med \"" + str(HOGSTA_SATS) + "\", utan nollor först."
                )
            resultat[roll][sats] = _rollens_konto(konto, vad + " för satsen " + sats, konton, var)
    return resultat


def _kontrollera_kontoplan(data, var):
    """Kontrollerar hela kontoplanen och returnerar (status, konton, roller) i den form kärnan använder."""
    _inga_dolda_tecken_i_json(data, var, _KONTOPLAN)
    if not isinstance(data, dict):
        raise KontoplanFel(var + " ska vara ett objekt med nycklar, inte " + _json_typ(data) + ".")
    _kontrollera_nycklar(data, KONTOPLAN_NYCKLAR, KONTOPLAN_VALFRIA_NYCKLAR, var, _KONTOPLAN)
    if "anteckning" in data:
        _text_i_json(data["anteckning"], "'anteckning'", var, _KONTOPLAN)
    status = _text_i_json(data["status"], "'status'", var, _KONTOPLAN)
    konton = _kontrollera_konton(data["konton"], var)
    roller = _kontrollera_roller(data["roller"], konton, var)
    return status, konton, roller


def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    return varde


# Nyckeln som bara las_kontoplan har. Utan den går det inte att skapa en Kontoplan som inte har gått
# igenom kontrollerna. Ett test (test_inga_genvagar.py) stoppar annan kärnkod från att använda den.
_KONTOPLANSNYCKEL = object()


class Kontoplan:
    """Ett företags kontoplan, från las_kontoplan. Kan bara skapas där och kan inte ändras."""

    __slots__ = ("_status", "_konton", "_roller")

    def __init__(self, nyckel, status, konton, roller):
        if nyckel is not _KONTOPLANSNYCKEL:
            raise KontoplanFel("En Kontoplan kan bara skapas av las_kontoplan, som kör alla kontroller först.")
        # object.__setattr__ behövs eftersom vanlig tilldelning är spärrad nedan.
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_konton", _frys(konton))
        object.__setattr__(self, "_roller", _frys(roller))

    def __setattr__(self, namn, varde):
        raise AttributeError("En Kontoplan kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("En Kontoplan kan inte ändras.")

    @property
    def status(self):
        return self._status

    @property
    def konton(self):
        """Kontona i filens ordning, som nya kopior: nummer, namn, fran och till (None om de saknas)."""
        return [dict(konto) for konto in self._konton.values()]

    def kontots_namn(self, nummer, datum):
        """Namnet på kontot, om det finns och gäller på datumet. Annars stoppar KontoplanFel."""
        datum = _datumtext(datum, "datumet", "Uppslaget i kontoplanen", _KONTOPLAN)
        if not isinstance(nummer, str) or nummer not in self._konton:
            raise KontoplanFel("Kontoplanen har inget konto " + repr(nummer) + ". Kontot gissas inte.")
        konto = self._konton[nummer]
        if (konto["fran"] is not None and datum < konto["fran"]) or (konto["till"] is not None and datum > konto["till"]):
            raise KontoplanFel(
                "Kontot " + nummer + " gäller inte på " + datum + ". Det gäller från " + (konto["fran"] or "början")
                + " till " + (konto["till"] or "tills vidare") + ". Kontot gissas inte."
            )
        return konto["namn"]

    def rollens_konto(self, roll, datum):
        """Kontot med rollen, till exempel "bank", om det gäller på datumet. Annars stoppar KontoplanFel."""
        if roll in ROLLER_PER_SATS:
            raise KontoplanFel("Rollen " + repr(roll) + " har ett konto per momssats. Använd utgaende_moms_konto.")
        if roll not in ROLLER:
            raise KontoplanFel("Kontoplanen har ingen roll " + repr(roll) + ". Rollerna är " + ", ".join(map(repr, ROLLER))
                               + ".")
        nummer = self._roller[roll]
        self.kontots_namn(nummer, datum)
        return nummer

    def utgaende_moms_konto(self, sats, datum):
        """Kontot för utgående moms med satsen (ett heltal i procent) på datumet. Annars stoppar KontoplanFel."""
        # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
        if type(sats) is not int:
            raise KontoplanFel("Momssatsen ska vara ett heltal i procent, inte " + _json_typ(sats) + ".")
        per_sats = self._roller["utgaende_moms_per_sats"]
        if str(sats) not in per_sats:
            raise KontoplanFel(
                "Kontoplanen har inget konto för utgående moms med satsen " + str(sats) + " %. Kontot gissas inte."
            )
        nummer = per_sats[str(sats)]
        self.kontots_namn(nummer, datum)
        return nummer

    def __repr__(self):
        return "Kontoplan(" + repr(self._status) + ", " + str(len(self._konton)) + " konton)"


def las_kontoplan(sokvag):
    """Läser och kontrollerar ett företags kontoplan.json. Returnerar en Kontoplan, annars KontoplanFel."""
    innehall, var = _ladda_json(sokvag, _KONTOPLAN)
    status, konton, roller = _kontrollera_kontoplan(innehall, var)
    return Kontoplan(_KONTOPLANSNYCKEL, status, konton, roller)
