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
MatchningFel, och inget resultat returneras.

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
   beskrivning eller referens (som hela ord, på samma sätt som motparten), är det den enda
   kandidaten. Det behövs för fakturor med samma belopp varje månad, till exempel ett abonnemang,
   där en betalning annars passar två fakturor i tidsfönstret.
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
from las_matchningsformat import MatchningsformatFel, kontrollera_matchningsformat
from las_underlag import Underlagsperiod

_DATUMFORM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)

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


def _sort(varde):
    """Vad ett värde är, kort, för ett felmeddelande. Text och heltal visas som de är."""
    if isinstance(varde, str):
        return repr(varde[:40]) + ("…" if len(varde) > 40 else "")
    if type(varde) is int:
        return str(varde)
    return _SORTER.get(type(varde), type(varde).__name__)


# --- Reglerna ---

def _regel_for(rad, regler):
    """Regeln i kraver_inte_underlag som bankraden passar, eller None.

    Riktningen ska stämma och referensen och beskrivningen ska börja exakt med regelns text.
    Formatet ser till att högst en regel kan passa. Beloppsgränsen prövas inte här.
    """
    riktning = "in" if rad["belopp_ore"] > 0 else "ut" if rad["belopp_ore"] < 0 else None
    for regel in regler:
        if (regel["riktning"] == riktning
                and rad["referens"].startswith(regel.get("referens_borjar_med", ""))
                and rad["beskrivning"].startswith(regel.get("beskrivning_borjar_med", ""))):
            return regel
    return None


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


def _kandidater(rad, underlag, tidsfonster):
    """Underlagen som kan höra till bankraden (regel 2 och 3 ovan)."""
    kandidater = [post for post in underlag if _ar_kandidat(rad, post, tidsfonster)]
    if len(kandidater) > 1:
        med_fakturanummer = [post for post in kandidater if _star_i_raden(post["fakturanummer"], rad)]
        if len(med_fakturanummer) == 1:
            return med_fakturanummer
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
    rader = bankperiod.rader  # nya kopior, i filernas ordning
    if type(underlagsperiod) is not Underlagsperiod:
        raise MatchningFel(
            "Underlagen ska vara en Underlagsperiod från las_underlagsperiod, inte " + _sort(underlagsperiod) + "."
        )
    try:
        format_ = kontrollera_matchningsformat(matchningsformat)
    except MatchningsformatFel as fel:
        raise MatchningFel(str(fel)) from None
    bedomning = _datum(bedomningsdatum, "Bedömningsdatumet")
    underlag = underlagsperiod.underlag  # en ny kopia, sorterad efter id

    behover = []  # (rad, kandidaterna) för raderna som ska ha underlag
    kraver_inte, arenden = [], []
    for rad in rader:
        regel = _regel_for(rad, format_["kraver_inte_underlag"])
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
