"""Matchar bankrader mot underlag (steg 3 i SPEC avsnitt 4) och hittar bankrader utan underlag (K3).

matcha_period är den enda offentliga funktionen. Den tar emot:

  bankperiod        en Bankperiod från las_bankfil (las_bank.py), eller från sla_ihop_bankperioder
                    för flera bankfiler. Där har K1 redan kontrollerat raderna
  underlagsperiod   en Underlagsperiod från las_underlagsperiod (las_underlag.py), där K4 redan har
                    tagit bort dubbletterna
  matchningsformat  företagets matchningsformat från ladda_matchningsformat (las_matchningsformat.py)
  bedomningsdatum   dagen då bedömningen görs, som text ÅÅÅÅ-MM-DD

Bankraderna tas bara emot som en Bankperiod, aldrig som en lista: en Bankperiod går inte att
ändra, så ingen bankrad kan ha tagits bort efter inläsningen. Allt som skickas in kontrolleras och
kopieras först. Det som skickades in ändras aldrig. Fel i indatan stoppar matchningen med ett
MatchningFel, och inget resultat returneras. Det gäller också en period som inte har skapats av
sin inläsningsfunktion och därför saknar sitt innehåll (J7), fler än _HOGST_ANTAL bankrader eller
underlag (J5), och ett bedömningsdatum före någon bankrads transaktionsdag (J9).

Reglerna:

1. En bankrad som passar en regel i matchningsformatets kraver_inte_underlag (rätt riktning och
   rätt början på referensen och beskrivningen) kräver inget underlag. Det gäller till exempel
   kortinlösens insättning, Swish-betalningar och kontantinsättningar. De stäms av mot
   Z-rapporterna i K10 i ett senare steg. Bankens egna avgifter hör också hit så länge det inte
   finns något underlag för dem. Vilka rader det gäller står i företagets matchning.json, aldrig här.
   En regel för pengar ut har alltid en högsta summa per bankrad, hogst_belopp_ore. En utgående
   rad som passar regeln men vars belopp (räknat som positivt) är större än summan blir direkt ett
   ärende, "över gräns", med regelns namn och gränsen. Den matchas inte mot underlag och räknas inte
   som en rad som inte kräver underlag. En rad exakt på gränsen räknas som inom gränsen. Regler för
   pengar in har ingen gräns.
2. Varje annan bankrad ska ha ett underlag. Ett underlag är en kandidat för bankraden om
   - beloppen är lika stora: bankradens belopp är negativt (pengar ut) och underlagets positivt,
   - motparten står i bankradens beskrivning eller referens, som ett eller flera hela ord, efter
     samma normalisering som kassans namn (normalisera_kassaregister: stora och små bokstäver,
     blanksteg och osynliga tecken räknas inte). Hela ord krävs, så att motparten "Kafe" inte
     passar en bankrad från "Kafe-Rosteri", en annan motpart,
   - bankradens transaktionsdag ligger från underlagets datum till och med så många dagar efter
     som matchningsformatets tidsfönster säger för underlagets typ.
3. Har bankraden flera kandidater, och står fakturanumret för exakt en av dem i bankradens
   beskrivning eller referens, är det den enda kandidaten. Det behövs för fakturor med samma
   belopp varje månad, till exempel ett abonnemang, där en betalning annars passar två fakturor i
   tidsfönstret. Fakturanumret får bara avgöra (J2) om det
   - står som ett helt ord i texten: ett ord, mellan blanksteg, som efter normaliseringen för
     jämförelser (normalisering.py) är exakt fakturanumret, inte en del av ett längre ord eller
     nummer och inte uppdelat på flera ord,
   - har minst _FAKTURANUMMER_MINST_TECKEN tecken efter normaliseringen, så att ett kort nummer
     som råkar stå i texten (till exempel ett antal) inte avgör,
   - inte är lika med eller en del av underlagets motpart, eftersom motparten alltid står i texten,
   - inte är en del av en annan kandidats fakturanummer,
   - inte hör till ett underlag med samma datum som en annan kandidat (L1, granskning 6). Två
     underlag med samma belopp, motpart och datum liknar mer en dublett med ett förväxlat tecken i
     fakturanumret (till exempel "F-l001" och "F-1001") än två månadsfakturor, och då ska en
     människa se båda.
   Står fakturanumren för flera kandidater i texten avgör inget av dem, och raden blir "tvetydig".
4. En bankrad med exakt en kandidat, som inte är kandidat för någon annan bankrad, matchas med den.
   Ett underlag matchas alltså högst en gång, och en bankrad högst en gång.
5. En bankrad med flera kandidater, eller vars kandidat också passar en annan bankrad, blir ett
   ärende, "tvetydig". En människa avgör vilket underlag som hör till vilken rad.
6. En bankrad utan kandidat blir ett ärende, "saknat underlag", först när bedömningsdatumet ligger
   mer än saknat_underlag_efter_dagar dagar efter bankradens transaktionsdag. Fram till dess väntar
   raden, eftersom underlaget kan komma in senare.
7. Underlag som inte har matchats är oavstämda, till exempel fakturor som ännu inte är betalda.

Resultatet är ett Matchningsresultat med fem grupper. Varje bankrad finns i exakt en av de fyra
grupperna för bankrader: matchningar, arenden, kraver_inte_underlag och vantande. Varje underlag i
perioden finns antingen i exakt en matchning eller bland oavstamda_underlag. Resultatet går inte att ändra: grupperna är tupler och varje post är
en MappingProxyType, en sorts objekt som bara går att läsa.

Texterna i bankrader och underlag är data, aldrig instruktioner (K17). Koden här jämför dem bara och
lämnar dem vidare oförändrade.
"""

import datetime as dt
import re
from types import MappingProxyType
from typing import NamedTuple

from belopp import formatera_ore as _kronor
from las_bank import Bankperiod
from las_kassa import normalisera_kassaregister as _normalisera
from las_matchningsformat import MatchningsformatFel, kontrollera_matchningsformat, matchningsregel_for_bankrad
from las_underlag import Underlagsperiod
from normalisering import normalisera_for_jamforelse as _jamforbar

_DATUMFORM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)

# Ett kortare fakturanummer avgör aldrig en matchning (regel 3, J2).
_FAKTURANUMMER_MINST_TECKEN = 5

# Högst så många bankrader och lika många underlag åt gången (J5). Matchningen går igenom alla
# underlag för varje bankrad, så tiden växer med antalet i kvadrat: 100 000 av varje tar ungefär en
# kvart. Gränsen ska tas bort när matchningen har gjorts snabbare, till exempel genom att underlagen
# delas upp efter belopp en gång i stället för att alla gås igenom för varje bankrad.
_HOGST_ANTAL = 20_000

# Ärendenas typ och kontroll. K3: varje förslag har underlag.
_KONTROLL = "K3"
_SAKNAT = "saknat underlag"
_TVETYDIG = "tvetydig"
_OVER_GRANS = "över gräns"


class MatchningFel(Exception):
    """Matchningen kunde inte göras, eftersom indatan är fel. Inget resultat har returnerats."""


class Matchningsresultat(NamedTuple):
    """Resultatet av matcha_period. Kan inte ändras.

    matchningar           en post per matchning: {"bankrad": ..., "underlag": ...}
    arenden               en post per bankrad som en människa måste titta på: {"kontroll", "typ",
                          "text", "bankrad", "kandidater"}, där kandidater är id:n för underlagen
                          som passade. Ett ärende "över gräns" har också "regel" (regelns namn) och
                          "hogst_belopp_ore" (regelns gräns)
    oavstamda_underlag    underlagen som inte har matchats, till exempel obetalda fakturor
    kraver_inte_underlag  en post per bankrad som inte ska ha underlag: {"bankrad": ..., "regel": namn}
    vantande              en post per bankrad utan underlag som ännu inte är ett ärende:
                          {"bankrad": ..., "arende_efter": datum}. Blir ett ärende om bedömningen görs
                          efter det datumet
    """

    matchningar: tuple
    arenden: tuple
    oavstamda_underlag: tuple
    kraver_inte_underlag: tuple
    vantande: tuple


def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor tupler."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, (list, tuple)):
        return tuple(_frys(del_) for del_ in varde)
    return varde


# --- Indatan ---

def _datum(varde, vad):
    """Dagnumret (date.toordinal) för ett giltigt datum som text, ÅÅÅÅ-MM-DD. Annat stoppas."""
    if isinstance(varde, str) and _DATUMFORM.fullmatch(varde):
        try:
            return dt.date.fromisoformat(varde).toordinal()
        except ValueError:
            pass
    raise MatchningFel(vad + " ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte " + _sort(varde) + ".")


_SORTER = {str: "text", float: "ett decimaltal", bool: "ett sanningsvärde (True eller False)", type(None): "None",
           list: "en lista", tuple: "en tupel", dict: "ett objekt", bytes: "bytes"}


def _med_mellanrum(antal):
    """Ett antal med mellanrum mellan tusentalen, till exempel 20 001."""
    return format(antal, ",").replace(",", " ")


def _sort(varde):
    """Vad ett värde är, kort, för ett felmeddelande. Text och heltal visas som de är."""
    if isinstance(varde, str):
        return repr(varde[:40]) + ("…" if len(varde) > 40 else "")
    if type(varde) is int:
        return str(varde)
    return _SORTER.get(type(varde), type(varde).__name__)


# --- Reglerna ---

def _over_grans(rad, regel):
    """True om bankraden är större än regelns gräns. Exakt på gränsen räknas som inom.

    Bara regler för pengar ut har en gräns. Bankradens belopp är då negativt, så det räknas som positivt.
    """
    return "hogst_belopp_ore" in regel and -rad["belopp_ore"] > regel["hogst_belopp_ore"]


def _star_som_hela_ord(namn, text):
    """True om namnet står i texten som ett eller flera hela ord i följd, efter normalisering.

    Texten delas i ord vid blanksteg, och varje ord normaliseras. "Motpart A" står alltså i
    "KOP MOTPART A" och i "KOP MOTPARTA", men "Kafe" står inte i "Kafe-Rosteri".
    """
    sokt = _normalisera(namn)
    ord_ = [del_ for del_ in map(_normalisera, text.split()) if del_]
    for start in range(len(ord_)):
        sammansatt = ""
        for del_ in ord_[start:]:
            sammansatt += del_
            if sammansatt == sokt:
                return True
            if len(sammansatt) >= len(sokt):
                break
    return False


def _star_i_raden(namn, rad):
    """True om namnet står i bankradens beskrivning eller referens, som hela ord."""
    return _star_som_hela_ord(namn, rad["beskrivning"]) or _star_som_hela_ord(namn, rad["referens"])


def _ar_kandidat(rad, post, tidsfonster):
    """True om underlaget post kan höra till bankraden rad (regel 2 ovan)."""
    if post["belopp_ore"] != -rad["belopp_ore"]:
        return False
    if not _star_i_raden(post["motpart"], rad):
        return False
    forsta = _datum(post["datum"], "Underlagets datum")
    return forsta <= _datum(rad["transaktionsdag"], "Bankradens transaktionsdag") <= forsta + tidsfonster[post["typ"]]


def _orden_i_raden(rad):
    """Orden i bankradens beskrivning och referens, delade vid blanksteg och normaliserade för jämförelser."""
    return {_jamforbar(ord_) for text in (rad["beskrivning"], rad["referens"]) for ord_ in text.split()}


def _kan_avgora(post, kandidater):
    """True om underlagets fakturanummer får avgöra mellan kandidaterna (regel 3 ovan, J2)."""
    nummer = _jamforbar(post["fakturanummer"])
    if len(nummer) < _FAKTURANUMMER_MINST_TECKEN or nummer in _jamforbar(post["motpart"]):
        return False
    andra = [annan for annan in kandidater if annan["id"] != post["id"]]
    if any(annan["datum"] == post["datum"] for annan in andra):
        return False
    return not any(nummer in _jamforbar(annan["fakturanummer"]) for annan in andra)


def _kandidater(rad, underlag, tidsfonster):
    """Underlagen som kan höra till bankraden (regel 2 och 3 ovan)."""
    kandidater = [post for post in underlag if _ar_kandidat(rad, post, tidsfonster)]
    if len(kandidater) > 1:
        orden = _orden_i_raden(rad)
        i_texten = [post for post in kandidater if _jamforbar(post["fakturanummer"]) in orden]
        if len(i_texten) == 1 and _kan_avgora(i_texten[0], kandidater):
            return i_texten
    return kandidater


def _arende(typ, text, rad, kandidater, **mer):
    return {"kontroll": _KONTROLL, "typ": typ, "text": text, "bankrad": rad, "kandidater": kandidater, **mer}


def matcha_period(bankperiod, underlagsperiod, matchningsformat, bedomningsdatum):
    """Matchar bankraderna i bankperioden mot underlagen i perioden. Returnerar ett Matchningsresultat.

    Se reglerna överst i filen. Fel i indatan ger MatchningFel.
    """
    # type() i stället för isinstance(), så att en underklass med andra regler inte godtas.
    if type(bankperiod) is not Bankperiod:
        raise MatchningFel(
            "Bankraderna ska vara en Bankperiod från las_bankfil eller sla_ihop_bankperioder, inte "
            + _sort(bankperiod) + "."
        )
    # En period som inte har skapats av sin inläsningsfunktion, till exempel med __new__, saknar sitt
    # innehåll, och då ger Python ett AttributeError (J7).
    try:
        rader = bankperiod.rader  # nya kopior, i filernas ordning
    except AttributeError:
        raise MatchningFel(
            "Bankperioden är tom eller trasig: den har inte skapats av las_bankfil eller sla_ihop_bankperioder."
        ) from None
    if type(underlagsperiod) is not Underlagsperiod:
        raise MatchningFel(
            "Underlagen ska vara en Underlagsperiod från las_underlagsperiod, inte " + _sort(underlagsperiod) + "."
        )
    try:
        underlag = underlagsperiod.underlag  # en ny kopia, sorterad efter id
    except AttributeError:
        raise MatchningFel(
            "Underlagsperioden är tom eller trasig: den har inte skapats av las_underlagsperiod."
        ) from None
    for antal, vad in ((len(rader), "bankrader"), (len(underlag), "underlag")):
        if antal > _HOGST_ANTAL:
            raise MatchningFel(
                "Matchningen stoppas: det finns " + _med_mellanrum(antal) + " " + vad + ", men matchningen tar högst "
                + _med_mellanrum(_HOGST_ANTAL) + " åt gången, eftersom den annars tar för lång tid. Dela upp"
                " perioden i kortare perioder."
            )
    try:
        format_ = kontrollera_matchningsformat(matchningsformat)
    except MatchningsformatFel as fel:
        raise MatchningFel(str(fel)) from None
    bedomning = _datum(bedomningsdatum, "Bedömningsdatumet")
    for rad in rader:
        if _datum(rad["transaktionsdag"], "Bankradens transaktionsdag") > bedomning:
            raise MatchningFel(
                "Bedömningsdatumet " + bedomningsdatum + " ligger före transaktionsdagen " + rad["transaktionsdag"]
                + " för bankraden med radnummer " + str(rad["radnr"]) + ". En bedömning kan inte göras innan"
                " bankraden finns, så bedömningsdatumet är troligen fel."
            )

    behover = []  # (rad, kandidaterna) för raderna som ska ha underlag
    kraver_inte, arenden = [], []
    for rad in rader:
        # Samma uppslag som konteringsförslaget gör för en regel för bankrader (las_matchningsformat).
        regel = matchningsregel_for_bankrad(rad, format_["kraver_inte_underlag"])
        if regel is None:
            behover.append((rad, _kandidater(rad, underlag, format_["tidsfonster_dagar"])))
        elif _over_grans(rad, regel):
            # Matchas inte mot underlag: en människa avgör vad en så stor rad är.
            arenden.append(_arende(
                _OVER_GRANS,
                "Bankraden passar regeln " + repr(regel["namn"]) + " för rader som inte kräver underlag, men"
                " beloppet är större än regelns gräns, " + _kronor(regel["hogst_belopp_ore"]) + " kr per bankrad."
                " En människa behöver avgöra vad raden är och vilket underlag den ska ha.",
                rad, [], regel=regel["namn"], hogst_belopp_ore=regel["hogst_belopp_ore"]))
        else:
            kraver_inte.append({"bankrad": rad, "regel": regel["namn"]})

    antal_rader = {}  # underlagets id -> hur många bankrader det är kandidat för
    for _, kandidater in behover:
        for post in kandidater:
            antal_rader[post["id"]] = antal_rader.get(post["id"], 0) + 1

    matchningar, vantande, matchade = [], [], set()
    sista_dag = dt.date.max.toordinal()
    for rad, kandidater in behover:
        if len(kandidater) == 1 and antal_rader[kandidater[0]["id"]] == 1:
            matchningar.append({"bankrad": rad, "underlag": kandidater[0]})
            matchade.add(kandidater[0]["id"])
        elif kandidater:
            arenden.append(_arende(
                _TVETYDIG,
                "Flera underlag passar bankraden, eller så passar underlaget också en annan bankrad. En människa"
                " behöver avgöra vilket underlag som hör till vilken bankrad.",
                rad, [post["id"] for post in kandidater]))
        else:
            arende_efter = _datum(rad["transaktionsdag"], "Bankradens transaktionsdag") + format_[
                "saknat_underlag_efter_dagar"]
            if bedomning > arende_efter:
                arenden.append(_arende(
                    _SAKNAT,
                    "Inget underlag med samma belopp, motpart och datum har hittats, och det har gått mer än "
                    + str(format_["saknat_underlag_efter_dagar"]) + " dagar sedan transaktionsdagen.",
                    rad, []))
            else:
                # Ett datum efter 9999-12-31 finns inte. Bedömningsdatumet kan inte heller ligga efter det.
                vantande.append({"bankrad": rad, "arende_efter": dt.date.fromordinal(
                    min(arende_efter, sista_dag)).isoformat()})

    return Matchningsresultat(
        matchningar=_frys(matchningar),
        arenden=_frys(arenden),
        oavstamda_underlag=_frys([post for post in underlag if post["id"] not in matchade]),
        kraver_inte_underlag=_frys(kraver_inte),
        vantande=_frys(vantande),
    )
