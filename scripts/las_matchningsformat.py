"""Läser och kontrollerar ett företags matchningsformat (foretag/<namn>/matchning.json).

Matchningsformatet säger hur bankrader matchas mot underlag för just det företaget
(matcha_bank.py). Allt som skiljer mellan företag ligger här, aldrig i kärnan:

  kraver_inte_underlag         en lista med regler för bankrader som inte ska ha ett underlag,
                               till exempel kortinlösens insättning av kortförsäljningen. Varje
                               regel har exakt nycklarna i REGEL_NYCKLAR och REGEL_VALFRIA_NYCKLAR:
                                 namn                    regelns namn, till exempel vilken sorts rad
                                                         det är. Visas i resultatet
                                 riktning                "in" (pengar in, positivt belopp) eller "ut"
                                                         (pengar ut, negativt belopp)
                                 referens_borjar_med     text som bankradens referens ska börja med
                                 beskrivning_borjar_med  text som bankradens beskrivning ska börja med
                                 anteckning              fri text för människor, till exempel varför
                                                         raden inte kräver underlag
                               Minst en av referens_borjar_med och beskrivning_borjar_med krävs.
                               Finns båda ska båda stämma. Texten jämförs exakt, med stora och små
                               bokstäver och utan normalisering, så att en rad med ett osynligt
                               tecken eller en annan stavning aldrig undantas av misstag. Den
                               kräver då ett underlag, och saknas det blir det ett ärende.
  tidsfonster_dagar            för varje underlagstyp (las_underlag.TYPER): hur många dagar efter
                               underlagets datum betalningen får ligga på banken
  saknat_underlag_efter_dagar  hur många dagar efter bankradens transaktionsdag en bankrad utan
                               underlag får vänta innan den blir ett ärende
  anteckning                   valfri, fri text för människor. Används inte av koden

Två regler med samma riktning som kan passa samma bankrad stoppar formatet, så att det aldrig
är oklart vilken regel en rad hör till. Antal dagar är heltal från 0 till och med HOGST_DAGAR.
Minsta fel stoppar formatet med ett MatchningsformatFel.

Filen läses med de gemensamma skydden i inlasning_skydd.py (UTF-8, dubbla nycklar, för djup
nästling och för långa tal), på samma sätt som bankformat.json och kassaformat.json.
"""

from inlasning_skydd import (
    _Filsort, _kontrollera_anteckning, _kontrollera_namn, _kontrollera_nycklar, _ladda_json,
)
from las_underlag import TYPER

MATCHNINGSFORMAT_NYCKLAR = ("kraver_inte_underlag", "tidsfonster_dagar", "saknat_underlag_efter_dagar")
MATCHNINGSFORMAT_VALFRIA_NYCKLAR = ("anteckning",)
REGEL_NYCKLAR = ("namn", "riktning")
REGEL_VALFRIA_NYCKLAR = ("referens_borjar_med", "beskrivning_borjar_med", "anteckning")
MONSTER_NYCKLAR = ("referens_borjar_med", "beskrivning_borjar_med")
RIKTNINGAR = ("in", "ut")

# Ett år. Ett större antal dagar betyder att formatet är fel, och skyddar mot datum som inte finns.
HOGST_DAGAR = 366


class MatchningsformatFel(Exception):
    """Matchningsformatet kunde inte läsas eller är fel."""


# Det som skiljer matchningsformatets felmeddelanden från andra filers, för skydden i
# inlasning_skydd.py. Bara fel, formatet och nivaer används för ett JSON-format.
_MATCHNINGSFORMAT = _Filsort(
    fel=MatchningsformatFel,
    filen="Matchningsformatet",
    formatet="Matchningsformatet",
    exportera_igen="Spara filen igen",
    om_styrtecken="Sådana tecken finns inte i ett vanligt matchningsformat.",
    ihopslaget="flera regler",
    nivaer="Ett matchningsformat har bara tre nivåer.",
)

_JSON_TYPER = {str: "text", float: "decimaltal", bool: "true eller false", type(None): "null", list: "en lista",
               dict: "ett objekt"}


def _visa(varde):
    """Ett värde ur formatet, kort, för ett felmeddelande: ett heltal som det är, annat med sin sort."""
    return str(varde) if type(varde) is int else _JSON_TYPER.get(type(varde), type(varde).__name__)


def _nycklar(data, obligatoriska, valfria, var):
    """Som _kontrollera_nycklar, men stoppar först nycklar som inte är text.

    Ett format från JSON har bara text som nycklar, men matcha_period kan få ett objekt direkt från
    Python. Där kan en nyckel vara ett tal, och då går nycklarna inte att sortera i meddelandet.
    """
    if isinstance(data, dict) and not all(isinstance(nyckel, str) for nyckel in data):
        raise MatchningsformatFel(var + " har en nyckel som inte är text. Alla nycklar ska vara text.")
    _kontrollera_nycklar(data, obligatoriska, valfria, var, _MATCHNINGSFORMAT)


def _kontrollera_dagar(varde, vad, var):
    """Ett antal dagar: ett heltal från 0 till och med HOGST_DAGAR. true/false och decimaltal stoppas."""
    # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
    if type(varde) is not int or not 0 <= varde <= HOGST_DAGAR:
        raise MatchningsformatFel(
            var + ": " + vad + " ska vara ett heltal från 0 till och med " + str(HOGST_DAGAR) + " (antal dagar),"
            " inte " + _visa(varde) + "."
        )
    return varde


def _kontrollera_regel(regel, nummer, var):
    """En regel i kraver_inte_underlag. Returnerar den som ett nytt objekt, utan anteckningen."""
    vad = var + ", regel nummer " + str(nummer) + " i 'kraver_inte_underlag'"
    _nycklar(regel, REGEL_NYCKLAR, REGEL_VALFRIA_NYCKLAR, vad)
    _kontrollera_anteckning(regel, vad, _MATCHNINGSFORMAT)
    ny = {"namn": _kontrollera_namn(regel["namn"], "'namn'", vad, _MATCHNINGSFORMAT, "ett namn")}
    if not isinstance(regel["riktning"], str) or regel["riktning"] not in RIKTNINGAR:
        raise MatchningsformatFel(vad + ": 'riktning' ska vara en av " + ", ".join(map(repr, RIKTNINGAR)) + ".")
    ny["riktning"] = regel["riktning"]
    if not any(nyckel in regel for nyckel in MONSTER_NYCKLAR):
        raise MatchningsformatFel(
            vad + " ska ha minst en av " + " och ".join(map(repr, MONSTER_NYCKLAR)) + ", annars passar den alla"
            " bankrader."
        )
    for nyckel in MONSTER_NYCKLAR:
        if nyckel in regel:
            ny[nyckel] = _kontrollera_namn(regel[nyckel], repr(nyckel), vad, _MATCHNINGSFORMAT, "ett mönster")
    return ny


def _kan_passa_samma_rad(en, annan):
    """True om det finns en bankrad som båda reglerna passar: samma riktning, och för varje mönster
    saknas det i någon av dem, eller så börjar det ena med det andra."""
    if en["riktning"] != annan["riktning"]:
        return False
    return all(nyckel not in en or nyckel not in annan or en[nyckel].startswith(annan[nyckel])
               or annan[nyckel].startswith(en[nyckel]) for nyckel in MONSTER_NYCKLAR)


def _kontrollera_regler(regler, var):
    if not isinstance(regler, list):
        raise MatchningsformatFel(var + ": 'kraver_inte_underlag' ska vara en lista med regler.")
    resultat = []
    for nummer, regel in enumerate(regler, start=1):
        ny = _kontrollera_regel(regel, nummer, var)
        for annan in resultat:
            if annan["namn"] == ny["namn"]:
                raise MatchningsformatFel(var + ": regelnamnet " + repr(ny["namn"]) + " står flera gånger.")
            if _kan_passa_samma_rad(annan, ny):
                raise MatchningsformatFel(
                    var + ": reglerna " + repr(annan["namn"]) + " och " + repr(ny["namn"]) + " kan båda passa samma"
                    " bankrad. Varje bankrad ska höra till högst en regel."
                )
        resultat.append(ny)
    return resultat


def kontrollera_matchningsformat(data, var="Matchningsformatet"):
    """Kontrollerar ett matchningsformat och returnerar det som ett nytt objekt, utan anteckningar.

    Används av ladda_matchningsformat och igen av matcha_bank.matcha_period, så att ett trasigt
    eller ändrat format aldrig används.
    """
    _nycklar(data, MATCHNINGSFORMAT_NYCKLAR, MATCHNINGSFORMAT_VALFRIA_NYCKLAR, var)
    _kontrollera_anteckning(data, var, _MATCHNINGSFORMAT)
    regler = _kontrollera_regler(data["kraver_inte_underlag"], var)
    _nycklar(data["tidsfonster_dagar"], TYPER, (), var + ", 'tidsfonster_dagar',")
    tidsfonster = {typ: _kontrollera_dagar(data["tidsfonster_dagar"][typ], "tidsfönstret för " + repr(typ), var)
                   for typ in TYPER}
    saknat = _kontrollera_dagar(data["saknat_underlag_efter_dagar"], "'saknat_underlag_efter_dagar'", var)
    return {"kraver_inte_underlag": regler, "tidsfonster_dagar": tidsfonster, "saknat_underlag_efter_dagar": saknat}


def ladda_matchningsformat(sokvag):
    """Läser och kontrollerar ett företags matchning.json. Fel ger MatchningsformatFel."""
    innehall, var = _ladda_json(sokvag, _MATCHNINGSFORMAT)
    return kontrollera_matchningsformat(innehall, var)
