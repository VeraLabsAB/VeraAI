"""Läser och kontrollerar ett företags momssatser (foretag/<namn>/momssatser.json).

Momsfilen säger vilken momssats varje varugrupp har, och från och till vilket datum satsen gäller
(DESIGN-regelbok.md avsnitt 2). Kärnan vet inte vilka varugrupper eller satser ett företag har.
Allt det står i filen, aldrig här. Ingen sats i filen är en skatteregel: varje sats har en källa
(kalla), och för ett riktigt företag ska den peka på ett beslut av en redovisningskonsult.

Filen ska ha exakt nycklarna i MOMSSATSER_NYCKLAR, och får ha nycklarna i
MOMSSATSER_VALFRIA_NYCKLAR:

  status                     text som säger vad filen är, till exempel "SYNTETISK". Visas för
                             människor. Kärnan tolkar den inte
  varugrupper                ett objekt med minst en varugrupp. Varugruppens namn får bara ha
                             små bokstäverna a–z, siffror och understreck och ska börja med en
                             bokstav, så att två namn som ser likadana ut aldrig är olika. Varje
                             varugrupp har en lista med minst en period. En period har exakt
                             nycklarna i PERIOD_NYCKLAR:
                               fran   första dagen satsen gäller, ÅÅÅÅ-MM-DD
                               till   sista dagen satsen gäller, ÅÅÅÅ-MM-DD, eller null om satsen
                                      gäller tills vidare. Bara den sista perioden får ha null
                               sats   momssatsen i procent, ett heltal från 0 till och med
                                      HOGSTA_SATS. Behövs en sats som inte är ett helt tal måste
                                      formatet ändras
                               kalla  varifrån satsen kommer, text som inte är tom
  moms_tolerans_ore_per_rad  hur många öre momsen på en momsrad får skilja från sats × belopp
                             (används av K5). Ett heltal från 0, med högst HELTAL_HOGST_SIFFROR
                             siffror
  anteckning                 fri text för människor. Används inte av koden

Perioderna för en varugrupp står i tidsordning och ska följa direkt på varandra: nästa period
börjar dagen efter att den förra slutar. En period som överlappar en annan, eller ett glapp
mellan två perioder, stoppar filen. När en sats ändras läggs en ny period till och den gamla får
ett slutdatum, så att ett gammalt underlag kontrolleras mot satsen som gällde då.

Hela filen stoppas vid minsta fel med ett MomssatsFel: okänd eller saknad nyckel, fel typ (till
exempel ett decimaltal, text eller true i stället för ett heltal), ett tomt värde, ett dolt tecken
någonstans i filen (även i nycklar och anteckningar), perioder som överlappar eller har glapp.
Filen läses med de gemensamma skydden i inlasning_skydd.py (UTF-8, dubbla nycklar, för djup
nästling och för långa tal), som de andra formatfilerna.

las_momssatser är den enda offentliga funktionen som läser filen. Den kör alltid alla kontroller
och returnerar Momssatser, som inte går att ändra och bara kan skapas av las_momssatser.
Momssatser.sats slår upp satsen för en varugrupp på ett datum. Finns ingen sats för datumet
stoppas uppslaget med ett MomssatsFel. Satsen gissas aldrig.
"""

import datetime as dt
import re
from types import MappingProxyType

from inlasning_skydd import (
    _Filsort, _datumtext, _heltal_i_json, _inga_dolda_tecken_i_json, _json_typ, _kontrollera_nycklar, _ladda_json,
    _text_i_json,
)
from las_underlag import HELTAL_HOGST_SIFFROR

MOMSSATSER_NYCKLAR = ("status", "varugrupper", "moms_tolerans_ore_per_rad")
MOMSSATSER_VALFRIA_NYCKLAR = ("anteckning",)
PERIOD_NYCKLAR = ("fran", "till", "sats", "kalla")

# En sats över 100 procent betyder att filen är trasig.
HOGSTA_SATS = 100

# Ett varugruppsnamn: små bokstäver a–z, siffror och understreck, och en bokstav först.
_VARUGRUPPSNAMN = re.compile(r"[a-z][a-z0-9_]*", re.ASCII)


class MomssatsFel(Exception):
    """Momsfilen kunde inte läsas, är fel, eller har ingen sats för ett datum."""


# Det som skiljer momsfilens felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
# Bara fel, formatet och nivaer används för ett JSON-format.
_MOMSSATSER = _Filsort(
    fel=MomssatsFel,
    filen="Momsfilen",
    formatet="Momsfilen",
    exportera_igen="Spara filen igen",
    om_styrtecken="Sådana tecken finns inte i en vanlig momsfil.",
    ihopslaget="flera perioder",
    nivaer="En momsfil har bara fyra nivåer.",
)


def _kontrollera_period(period, vad, var):
    """En period för en varugrupp. Returnerar den som ett nytt objekt."""
    if not isinstance(period, dict):
        raise MomssatsFel(var + ": " + vad + " ska vara ett objekt med nycklar, inte " + _json_typ(period) + ".")
    _kontrollera_nycklar(period, PERIOD_NYCKLAR, (), var + ", " + vad + ",", _MOMSSATSER)
    fran = _datumtext(period["fran"], "'fran' i " + vad, var, _MOMSSATSER)
    till = None if period["till"] is None else _datumtext(period["till"], "'till' i " + vad, var, _MOMSSATSER)
    if till is not None and till < fran:
        raise MomssatsFel(var + ": " + vad + " slutar " + till + ", före sitt första datum " + fran + ".")
    return {
        "fran": fran,
        "till": till,
        "sats": _heltal_i_json(period["sats"], "'sats' i " + vad, 0, HOGSTA_SATS, var, _MOMSSATSER),
        "kalla": _text_i_json(period["kalla"], "'kalla' i " + vad, var, _MOMSSATSER),
    }


def _kontrollera_perioder(perioder, varugrupp, var):
    """Varugruppens perioder: minst en, i tidsordning, utan överlapp och utan glapp. Returnerar nya perioder."""
    vad = "varugruppen " + repr(varugrupp)
    if not isinstance(perioder, list):
        raise MomssatsFel(var + ": " + vad + " ska ha en lista med perioder, inte " + _json_typ(perioder) + ".")
    if not perioder:
        raise MomssatsFel(var + ": " + vad + " har inga perioder. Varje varugrupp ska ha minst en period med en sats.")
    resultat = [_kontrollera_period(period, "period nummer " + str(nummer) + " för " + vad, var)
                for nummer, period in enumerate(perioder, start=1)]
    for nummer in range(1, len(resultat)):
        forra, nasta = resultat[nummer - 1], resultat[nummer]
        if forra["till"] is None or forra["till"] >= nasta["fran"]:
            raise MomssatsFel(
                var + ": för " + vad + " överlappar period nummer " + str(nummer) + " (från " + forra["fran"]
                + (", till " + forra["till"] if forra["till"] else ", utan slutdatum") + ") och period nummer "
                + str(nummer + 1)
                + " (från " + nasta["fran"] + "). Perioderna ska stå i tidsordning, och varje dag får ha en enda sats."
            )
        if dt.date.fromisoformat(nasta["fran"]) - dt.date.fromisoformat(forra["till"]) > dt.timedelta(days=1):
            raise MomssatsFel(
                var + ": för " + vad + " finns ett glapp mellan period nummer " + str(nummer) + " (slutar "
                + forra["till"] + ") och period nummer " + str(nummer + 1) + " (börjar " + nasta["fran"]
                + "). Nästa period ska börja dagen efter att den förra slutar, så att varje dag har en sats."
            )
    return resultat


def _kontrollera_momssatser(data, var):
    """Kontrollerar hela momsfilen och returnerar (status, varugrupper, tolerans) i den form kärnan använder."""
    _inga_dolda_tecken_i_json(data, var, _MOMSSATSER)
    if not isinstance(data, dict):
        raise MomssatsFel(var + " ska vara ett objekt med nycklar, inte " + _json_typ(data) + ".")
    _kontrollera_nycklar(data, MOMSSATSER_NYCKLAR, MOMSSATSER_VALFRIA_NYCKLAR, var, _MOMSSATSER)
    if "anteckning" in data:
        _text_i_json(data["anteckning"], "'anteckning'", var, _MOMSSATSER)
    status = _text_i_json(data["status"], "'status'", var, _MOMSSATSER)
    grupper = data["varugrupper"]
    if not isinstance(grupper, dict):
        raise MomssatsFel(var + ": 'varugrupper' ska vara ett objekt med varugrupper, inte " + _json_typ(grupper) + ".")
    if not grupper:
        raise MomssatsFel(var + ": 'varugrupper' är tom. Filen ska ha minst en varugrupp.")
    varugrupper = {}
    for namn, perioder in grupper.items():
        if not _VARUGRUPPSNAMN.fullmatch(namn):
            raise MomssatsFel(
                var + ": varugruppen " + repr(namn) + " har ett ogiltigt namn. Ett varugruppsnamn får bara ha små"
                " bokstäverna a–z, siffror och understreck, och ska börja med en bokstav."
            )
        varugrupper[namn] = _kontrollera_perioder(perioder, namn, var)
    tolerans = _heltal_i_json(data["moms_tolerans_ore_per_rad"], "'moms_tolerans_ore_per_rad'", 0,
                              10 ** HELTAL_HOGST_SIFFROR - 1, var, _MOMSSATSER)
    return status, varugrupper, tolerans


def _uppslagets_datum(datum):
    """Datumet för ett uppslag: ett giltigt datum som text, ÅÅÅÅ-MM-DD."""
    return _datumtext(datum, "datumet", "Uppslaget i momsfilen", _MOMSSATSER)


# Nyckeln som bara las_momssatser har. Utan den går det inte att skapa Momssatser som inte har gått
# igenom kontrollerna. Ett test (test_inga_genvagar.py) stoppar annan kärnkod från att använda den.
_MOMSNYCKEL = object()


class Momssatser:
    """Ett företags momssatser, från las_momssatser. Kan bara skapas där och kan inte ändras."""

    __slots__ = ("_status", "_varugrupper", "_tolerans_ore_per_rad")

    def __init__(self, nyckel, status, varugrupper, tolerans_ore_per_rad):
        if nyckel is not _MOMSNYCKEL:
            raise MomssatsFel("Momssatser kan bara skapas av las_momssatser, som kör alla kontroller först.")
        # object.__setattr__ behövs eftersom vanlig tilldelning är spärrad nedan.
        object.__setattr__(self, "_status", status)
        object.__setattr__(self, "_varugrupper", MappingProxyType({
            namn: tuple(MappingProxyType(dict(period)) for period in perioder) for namn, perioder in varugrupper.items()
        }))
        object.__setattr__(self, "_tolerans_ore_per_rad", tolerans_ore_per_rad)

    def __setattr__(self, namn, varde):
        raise AttributeError("Momssatser kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("Momssatser kan inte ändras.")

    @property
    def status(self):
        return self._status

    @property
    def tolerans_ore_per_rad(self):
        return self._tolerans_ore_per_rad

    @property
    def varugrupper(self):
        """Varugruppernas namn, i filens ordning."""
        return tuple(self._varugrupper)

    def period(self, varugrupp, datum):
        """Perioden som gäller för varugruppen på datumet, som en ny kopia: fran, till, sats och kalla.

        En okänd varugrupp, eller ett datum utan sats, stoppar med MomssatsFel. Satsen gissas aldrig.
        """
        datum = _uppslagets_datum(datum)
        if not isinstance(varugrupp, str) or varugrupp not in self._varugrupper:
            raise MomssatsFel(
                "Momsfilen har ingen varugrupp " + repr(varugrupp) + ". Varugrupperna är "
                + ", ".join(map(repr, self._varugrupper)) + "."
            )
        for period in self._varugrupper[varugrupp]:
            if period["fran"] <= datum and (period["till"] is None or datum <= period["till"]):
                return dict(period)
        raise MomssatsFel(
            "Momsfilen har ingen sats för varugruppen " + repr(varugrupp) + " på " + datum + ". Satsen gissas"
            " inte. En människa måste lägga till satsen för datumet i momsfilen, med en källa."
        )

    def sats(self, varugrupp, datum):
        """Momssatsen i procent (ett heltal) för varugruppen på datumet. Se period."""
        return self.period(varugrupp, datum)["sats"]

    def __repr__(self):
        return ("Momssatser(" + repr(self._status) + ", " + str(len(self._varugrupper)) + " varugrupper, tolerans "
                + str(self._tolerans_ore_per_rad) + " öre per rad)")


def las_momssatser(sokvag):
    """Läser och kontrollerar ett företags momssatser.json. Returnerar Momssatser, annars MomssatsFel."""
    innehall, var = _ladda_json(sokvag, _MOMSSATSER)
    status, varugrupper, tolerans = _kontrollera_momssatser(innehall, var)
    return Momssatser(_MOMSNYCKEL, status, varugrupper, tolerans)
