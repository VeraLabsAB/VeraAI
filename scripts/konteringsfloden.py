"""Flödena som gör konteringsförslag av underlag och bankrader, med kontrollerna K5 och K8.

kontera_period är den enda offentliga funktionen. Den tar emot regelboken från las_regelbok,
kontoplanen från las_kontoplan, momsfilen från las_momssatser, underlagsperioden från
las_underlagsperiod, bankperioden från las_bankfil (eller sla_ihop_bankperioder) och
bedömningsdatumet, ÅÅÅÅ-MM-DD. Den matchar själv bankraderna mot underlagen med matcha_period, så
att matchningen alltid är gjord mot samma perioder och samma regelbok som förslagen. Varje förslag
skapas av skapa_konteringsforslag, som alltid kör K2 och ursprungskontrollen. Inget förslag skapas
på något annat sätt.

Inget här bokför något. Resultatet är förslag och ärenden som en människa ska titta på. Ett förslag
har inget fält för att vara bokfört eller godkänt, och inget skrivs till en SIE-fil eller till kundens
bokföringsprogram (SPEC avsnitt 4, steg 9). Alla belopp tas oförändrade ur underlagen och bankraderna,
som heltal i öre. Ingen moms räknas om eller avrundas (Hugos beslut 2026-10-29, B3, D4).

Hur förslagen ser ut bestämmer företagets val i regelbokens 'bokforing' (Hugos beslut 2026-10-29, B3,
D1, D13 och D14): metoden och vilket datum varje verifikation får (verifikationsdatum). Kontona står i
regelboken och kontoplanen, aldrig här.

Flöde a, leverantörsfaktura, med faktureringsmetoden (DESIGN-regelbok.md avsnitt 4a):

  1. Fakturan, på datumet för 'leverantorsfaktura'. Per momsrad: beloppet utan moms i debet på
     regelns konto för varugruppen, och momsen i debet på kontot för ingående moms (rollen
     ingaende_moms i kontoplanen). Hela beloppet att betala i kredit på leverantörsskulderna (rollen
     leverantorsskulder). En rad med beloppet 0, till exempel momsen på en momsfri rad, tas inte med.
  2. Betalningen, när matchningen har parat ihop fakturan med en bankrad, på datumet för 'betalning':
     leverantörsskulderna i debet och bankkontot (rollen bank) i kredit. En obetald faktura har bara
     verifikation 1 och står bland matchningens oavstämda underlag.

Kontrollerna för varje underlag, innan något förslag görs:

  Regeln: regelboken ger regeln för underlagets typ och motpart på underlagets datum. Ingen regel
     betyder en ny motpart: ett ärende, "ny motpart", och Vera gissar inget konto.
  K7: ett underlag från en ägare eller närstående (Regelbok.ar_agare_eller_narstaende) blir alltid ett
     ärende, "kräver mänsklig bedömning", som ägarens bankrader i matchningen (SPEC K7). Nivån sätts i
     nivåsteget (uppgift 6).
  K5 (DESIGN avsnitt 6), för varje momsrad:
     1. satsen finns: minst en varugrupp i momsfilen har satsen på underlagets datum,
     2. satsen passar regeln: satsen är satsen för minst en av varugrupperna i regelns kontering på
        datumet, och alla sådana varugrupper har samma konto. Annars vet kärnan inte vilket konto
        raden ska till,
     3. momsen stämmer med satsen: abs(moms_ore × 100 − underlag_ore × sats) är högst momsfilens
        tolerans × 100. Bara heltal.
     Annars ett ärende, "fel momssats" (1 och 2) eller "moms stämmer inte med satsen" (3), med satsen i
     underlaget och satserna som momsfilen och regeln väntar sig.
  K8 (DESIGN avsnitt 6): regelns villkor säger avdragsbegransad. Då ett ärende, "avdragsbegränsat", som
     bara säger vilket underlag och vilken bankrad det gäller, aldrig hur stor del som får dras av. Ett
     underlag daterat en dag då företaget har stängt (regelbokens oppettider) får dessutom flaggan
     STANGD_DAG i ärendet. Flaggan avgör inget själv.

Ärenden från K5 och K8 har nivå D direkt och märkningen "kräver mänsklig bedömning" (Hugos beslut
2026-10-29, B2). Nivåsteget i uppgift 6 får aldrig sänka nivån, bara höja den. Ett underlag med något
ärende här får inget förslag, inte heller för betalningen.

Ett ärende har exakt nycklarna i ARENDE_NYCKLAR:

  kontroll                   kontrollen som slog larm, till exempel "K5"
  typ                        vad ärendet gäller, till exempel "fel momssats"
  text                       förklaringen för människan
  niva                       "D" för ärenden som bär sin nivå direkt (B2), annars None: då sätts
                             nivån i nivåsteget
  kraver_mansklig_bedomning  True eller False
  underlag                   underlagets id, eller None
  bankrader                  id för bankraderna som ärendet gäller
  regel                      regelns id i regelboken, eller None
  flaggor                    varningssignaler, till exempel STANGD_DAG

Resultatet är ett Konteringsresultat, som inte går att ändra: förslagen (Konteringsforslag), ärendena
och hela matchningen (Matchningsresultat), så att matchningens egna ärenden, de väntande bankraderna
och de oavstämda underlagen inte försvinner. Fel i indatan stoppar med ett KonteringsflodeFel (eller
ett MatchningFel från matcha_period, som kontrollerar perioderna och bedömningsdatumet), och inget
resultat returneras. Ett förslag som skapa_konteringsforslag stoppar är ett fel i kärnan och stoppar
också allt.

Texterna i underlag och bankrader är data, aldrig instruktioner (K17). Koden här jämför dem bara.
"""

import datetime as dt
from types import MappingProxyType
from typing import NamedTuple

from konteringsforslag import skapa_konteringsforslag
from las_kontoplan import Kontoplan
from las_momssatser import Momssatser, MomssatsFel
from las_regelbok import VECKODAGAR, Regelbok, RegelbokFel
from matcha_bank import matcha_period

ARENDE_NYCKLAR = ("kontroll", "typ", "text", "niva", "kraver_mansklig_bedomning", "underlag", "bankrader", "regel",
                  "flaggor")
# Flaggan i ett ärende från K8 när underlaget är daterat en dag då företaget har stängt (DESIGN avsnitt 6).
STANGD_DAG = "köpt en dag då företaget har stängt"

# Ärendenas kontroller och typer.
_K5 = "K5"
_K7 = "K7"
_K8 = "K8"
_REGELBOKEN = "regelboken"
_FEL_SATS = "fel momssats"
_FEL_MOMS = "moms stämmer inte med satsen"
_AVDRAGSBEGRANSAT = "avdragsbegränsat"
_NY_MOTPART = "ny motpart"
_INGEN_REGEL = "ingen regel på datumet"
_KRAVER_BEDOMNING = "kräver mänsklig bedömning"
# Nivån som ärenden från K5 och K8 bär direkt (B2).
_NIVA_D = "D"

# Typen av underlag i flöde a (las_underlag.TYPER).
_LEVERANTORSFAKTURA = "leverantorsfaktura"
# Värdena i 'verifikationsdatum' som är underlagets eget datum (las_regelbok.VERIFIKATIONSDATUM). Alla
# andra värden är namnet på ett fält i bankraden.
_UNDERLAGETS_DATUM = ("fakturadatum", "kvittodatum")
_BETALNING = "betalning"
# Rollerna i kontoplanen som flödena bokför på (las_kontoplan.ROLLER).
_BANK = "bank"
_LEVERANTORSSKULDER = "leverantorsskulder"
_INGAENDE_MOMS = "ingaende_moms"
# Fälten i en momsrad (las_underlag.MOMSRAD_NYCKLAR) och i underlaget och bankraden.
_UNDERLAGSFALT = "underlag_ore"
_MOMSFALT = "moms_ore"
_BELOPPSFALT = "belopp_ore"


class KonteringsflodeFel(Exception):
    """Flödena kunde inte köras, eftersom indatan är fel. Inget resultat har returnerats."""


class Konteringsresultat(NamedTuple):
    """Resultatet av kontera_period. Kan inte ändras.

    forslag    förslagen, som Konteringsforslag från skapa_konteringsforslag
    arenden    ärendena från flödena, var och en en MappingProxyType med ARENDE_NYCKLAR
    matchning  Matchningsresultatet från matcha_period, med matchningens egna ärenden
    """

    forslag: tuple
    arenden: tuple
    matchning: tuple


class _Korning(NamedTuple):
    """Det som alla delar av en körning använder, kontrollerat av kontera_period."""

    regelbok: object
    kontoplan: object
    momssatser: object
    underlagsperiod: object
    bankperiod: object
    bokforing: object   # regelbokens 'bokforing'
    oppettider: object  # regelbokens 'oppettider'


def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor tupler."""
    if isinstance(varde, (dict, MappingProxyType)):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, (list, tuple)):
        return tuple(_frys(del_) for del_ in varde)
    return varde


# --- Indatan ---

def _kontrollera_indata(regelbok, kontoplan, momssatser):
    """Regelboken, kontoplanen och momsfilen ska komma från sina inläsningsfunktioner och höra ihop.

    Returnerar (regelbokens val i 'bokforing', regelbokens oppettider). Kontoplanen och momsfilen ska
    vara de som regelboken kontrollerades mot (samma kontrollsummor), eftersom regelns konton och
    varugrupper bara betyder något med dem.
    """
    # type() i stället för isinstance(), så att en underklass med egna regler inte släpps igenom.
    for objekt, klass, vad, funktion in ((regelbok, Regelbok, "regelboken", "las_regelbok"),
                                         (kontoplan, Kontoplan, "kontoplanen", "las_kontoplan"),
                                         (momssatser, Momssatser, "momsfilen", "las_momssatser")):
        if type(objekt) is not klass:
            raise KonteringsflodeFel("Flödena körs inte: " + vad + " ska komma från " + funktion + ", inte vara "
                                     + type(objekt).__name__ + ".")
    # Ett objekt av rätt typ som har skapats förbi sin inläsningsfunktion saknar sitt innehåll.
    try:
        mot, bokforing, oppettider = regelbok.kontrollerad_mot, regelbok.bokforing, regelbok.oppettider
    except (AttributeError, RegelbokFel):
        raise KonteringsflodeFel("Flödena körs inte: regelboken är tom eller trasig. Den har inte skapats av"
                                 " las_regelbok.") from None
    for objekt, vad, nyckel, funktion in ((kontoplan, "kontoplanen", "kontoplan", "las_kontoplan"),
                                          (momssatser, "momsfilen", "momssatser", "las_momssatser")):
        try:
            summa = objekt.kontrollsumma
        except AttributeError:
            raise KonteringsflodeFel("Flödena körs inte: " + vad + " är tom eller trasig. Den har inte skapats av "
                                     + funktion + ".") from None
        if summa != mot[nyckel]:
            raise KonteringsflodeFel("Flödena körs inte: " + vad + " är inte den som regelboken kontrollerades mot"
                                     " (kontrollsumman är en annan). Regelboken, kontoplanen och momsfilen ska vara"
                                     " lästa från samma företags filer.")
    return bokforing, oppettider


# --- Ärendena ---

def _arende(kontroll, typ, text, underlag=None, bankrader=(), regel=None, niva=None, kraver=False, flaggor=()):
    return {"kontroll": kontroll, "typ": typ, "text": text, "niva": niva, "kraver_mansklig_bedomning": kraver,
            "underlag": underlag, "bankrader": list(bankrader), "regel": regel, "flaggor": list(flaggor)}


def _satser_pa_datumet(momssatser, datum):
    """{varugrupp: sats} för varugrupperna i momsfilen som har en sats på datumet."""
    satser = {}
    for grupp in momssatser.varugrupper:
        try:
            satser[grupp] = momssatser.sats(grupp, datum)
        except MomssatsFel:
            pass
    return satser


def _visa_grupper(grupper, satser):
    """Varugrupperna med sina satser i ett ärende, till exempel "'grupp' (6 %)"."""
    return ", ".join(repr(grupp) + " (" + str(satser[grupp]) + " %)" for grupp in grupper)


def _k5(underlag, regel, momssatser):
    """K5 för underlagets momsrader. Returnerar ({sats: konto}, []) eller (None, [(typ, text), ...])."""
    datum = underlag["datum"]
    satser = _satser_pa_datumet(momssatser, datum)
    tolerans = momssatser.tolerans_ore_per_rad
    konton, fel = {}, []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        rad = "Momsraden med satsen " + str(sats) + " %"
        regelns = {grupp: konto for grupp, konto in regel["kontering"].items() if satser.get(grupp) == sats}
        if sats not in satser.values():
            fel.append((_FEL_SATS, rad + ": ingen varugrupp i momsfilen har satsen på " + datum + ". Satserna där på"
                        " datumet är " + _visa_grupper(satser, satser) + "."))
        elif not regelns:
            fel.append((_FEL_SATS, rad + ": regeln " + regel["id"] + " har varugrupperna " + _visa_grupper(
                regel["kontering"], satser) + " på " + datum + ", och ingen av dem har satsen i underlaget."))
        elif len(set(regelns.values())) > 1:
            fel.append((_FEL_SATS, rad + ": satsen passar flera varugrupper i regeln " + regel["id"] + " med olika"
                        " konton (" + _visa_grupper(regelns, satser) + "). Kärnan vet inte vilket konto raden ska"
                        " till."))
        elif abs(momsrad[_MOMSFALT] * 100 - momsrad[_UNDERLAGSFALT] * sats) > tolerans * 100:
            fel.append((_FEL_MOMS, rad + ": momsen är " + str(momsrad[_MOMSFALT]) + " öre på " + str(
                momsrad[_UNDERLAGSFALT]) + " öre utan moms, men satsen ger " + str(
                momsrad[_UNDERLAGSFALT] * sats // 100) + " öre, och momsfilen godtar högst " + str(tolerans)
                        + " öre i skillnad per rad."))
        else:
            konton[sats] = sorted(set(regelns.values()))[0]
    return (None, fel) if fel else (konton, [])


def _stangd_dag(datum, oppettider):
    """True om företaget har stängt på datumet (regelbokens oppettider)."""
    veckodag = VECKODAGAR[dt.date.fromisoformat(datum).weekday()]
    return veckodag in oppettider["stangda_veckodagar"] or datum in oppettider["stangda_datum"]


def _underlagets_arenden(underlag, regel, korning, bankrader):
    """Ärendena för ett underlag före förslaget: regeln, K7, K5 och K8. Returnerar (konton per sats, ärenden)."""
    id_, regelbok = underlag["id"], korning.regelbok
    if regel is None:
        return None, [_arende(_REGELBOKEN, _NY_MOTPART, "Ingen regel i regelboken passar underlaget (" + underlag["typ"]
                              + ") på " + underlag["datum"] + ". Vera gissar inget konto. En människa väljer konto,"
                              " och svaret kan bli ett förslag till en ny regel.", id_, bankrader,
                              kraver=regelbok.ar_agare_eller_narstaende(underlag["motpart"]))]
    if regelbok.ar_agare_eller_narstaende(underlag["motpart"]):
        return None, [_arende(_K7, _KRAVER_BEDOMNING, "Underlaget är från en ägare eller närstående (K7). Det blir"
                              " alltid ett ärende, och en människa avgör hur det ska bokföras.", id_, bankrader,
                              regel["id"], kraver=True)]
    konton, fel = _k5(underlag, regel, korning.momssatser)
    arenden = []
    if fel:
        typ = _FEL_SATS if any(typ == _FEL_SATS for typ, _ in fel) else _FEL_MOMS
        arenden.append(_arende(_K5, typ, " ".join(text for _, text in fel) + " Inget förslag görs. En människa avgör"
                               " vilken moms som gäller.", id_, bankrader, regel["id"], _NIVA_D, True))
    if regel["villkor"].get("avdragsbegransad") is True:
        arenden.append(_arende(
            _K8, _AVDRAGSBEGRANSAT, "Regeln " + regel["id"] + " är avdragsbegränsad (K8). Inget förslag görs, och Vera"
            " föreslår inte hur stor del av kostnaden eller momsen som får dras av. En människa avgör det, med stöd av"
            " en redovisningskonsult.", id_, bankrader, regel["id"], _NIVA_D, True,
            [STANGD_DAG] if _stangd_dag(underlag["datum"], korning.oppettider) else []))
    return (None if arenden else konton), arenden


# --- Förslagen ---

def _underlagets(id_, falt, sats=None):
    kalla = {"kalla": "underlag", "id": id_, "falt": falt}
    if sats is not None:
        kalla["momssats"] = sats
    return kalla


def _bankradens(id_):
    return {"kalla": "bankrad", "id": id_, "falt": _BELOPPSFALT}


def _rad(konto, debet, kredit, kalla):
    return {"konto": konto, "debet_ore": debet, "kredit_ore": kredit, "ursprung": {"berakning": "lika",
                                                                                   "fran": [kalla]}}


def _skapa(forslag_id, datum, text, rader, regel, korning, motivering, underlag=(), bankrader=()):
    """Skapar förslaget med skapa_konteringsforslag, som kör K2 och ursprungskontrollen. Returnerar det."""
    regelbok, kontoplan = korning.regelbok, korning.kontoplan
    mot = regelbok.kontrollerad_mot
    forslag = {
        "forslag_id": forslag_id,
        "verifikation": {"datum": datum, "text": text, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_} for id_ in underlag], "bankrader": [{"id": id_} for id_ in bankrader],
                       "z_rapporter": [],
                       "regel": {"id": regel["id"], "regelbokens_kontrollsumma": regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": motivering,
    }
    return skapa_konteringsforslag(forslag, regelbok, kontoplan, korning.underlagsperiod, korning.bankperiod)


def _verifikationens_datum(val, underlag, bankrad):
    """Datumet som 'verifikationsdatum' i regelbokens 'bokforing' väljer: underlagets eller ett fält i bankraden."""
    return underlag["datum"] if val in _UNDERLAGETS_DATUM else bankrad[val]


def _antaget(bokforing):
    return ", antaget för företaget" if bokforing["antaget"] else ""


def _kostnad_och_moms(underlag, konton, kontoplan, datum):
    """Raderna i debet för underlagets kostnad och moms: per momsrad, kostnaden och sedan momsen."""
    ingaende = kontoplan.rollens_konto(_INGAENDE_MOMS, datum)
    rader = []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        for konto, falt in ((konton[sats], _UNDERLAGSFALT), (ingaende, _MOMSFALT)):
            if momsrad[falt]:
                rader.append(_rad(konto, momsrad[falt], 0, _underlagets(underlag["id"], falt, sats)))
    return rader


def _regeln_pa(underlag, regel, datum, korning, bankrad, vad):
    """None om regeln också gäller underlaget på datumet, annars ett ärende (verifikationen får ett senare datum)."""
    pa_datumet = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], datum)
    if pa_datumet is not None and pa_datumet["id"] == regel["id"]:
        return None
    return _arende(_REGELBOKEN, _INGEN_REGEL, vad + " bokförs på " + datum + ", men regeln " + regel["id"] + " gäller"
                   " inte underlaget då. Inget förslag görs. En människa avgör vilken regel som gäller.",
                   underlag["id"], [bankrad["id"]], regel["id"])


def _leverantorsfaktura(underlag, regel, konton, bankrad, korning):
    """Flöde a: fakturan och, om matchningen har en bankrad, betalningen. Returnerar (förslag, ärenden)."""
    id_, nummer, kontoplan, bokforing = underlag["id"], underlag["fakturanummer"], korning.kontoplan, korning.bokforing
    datum = _verifikationens_datum(bokforing["verifikationsdatum"][_LEVERANTORSFAKTURA], underlag, bankrad)
    forslag = [_skapa(
        "F-FAKTURA-" + id_, datum, "Leverantörsfaktura " + nummer + ", underlag " + id_,
        _kostnad_och_moms(underlag, konton, kontoplan, datum)
        + [_rad(kontoplan.rollens_konto(_LEVERANTORSSKULDER, datum), 0, underlag[_BELOPPSFALT],
                _underlagets(id_, _BELOPPSFALT))],
        regel, korning, "Regeln " + regel["id"] + " i regelboken. Fakturan bokförs på sitt eget datum med "
        + bokforing["metod"] + _antaget(bokforing) + ", och betalningen bokförs för sig.", underlag=[id_])]
    if bankrad is None:
        return forslag, []
    datum = _verifikationens_datum(bokforing["verifikationsdatum"][_BETALNING], underlag, bankrad)
    arende = _regeln_pa(underlag, regel, datum, korning, bankrad, "Betalningen")
    if arende is not None:
        return forslag, [arende]
    forslag.append(_skapa(
        "F-BETALNING-" + id_, datum, "Betalning av leverantörsfaktura " + nummer + ", underlag " + id_,
        [_rad(kontoplan.rollens_konto(_LEVERANTORSSKULDER, datum), underlag[_BELOPPSFALT], 0,
              _underlagets(id_, _BELOPPSFALT)),
         _rad(kontoplan.rollens_konto(_BANK, datum), 0, -bankrad[_BELOPPSFALT], _bankradens(bankrad["id"]))],
        regel, korning, "Regeln " + regel["id"] + " i regelboken. Matchningen har parat ihop bankraden med"
        " radnummer " + str(bankrad["radnr"]) + " med fakturan (samma belopp och motpart, inom tidsfönstret)."
        " Betalningen bokförs på bankradens " + bokforing["verifikationsdatum"][_BETALNING] + _antaget(bokforing)
        + ".", underlag=[id_], bankrader=[bankrad["id"]]))
    return forslag, []


# Flödet för varje typ av underlag (las_underlag.TYPER). Ett underlag av en typ som saknas här får
# kontrollerna men inget förslag.
_FLODEN = {_LEVERANTORSFAKTURA: _leverantorsfaktura}


def kontera_period(regelbok, kontoplan, momssatser, underlagsperiod, bankperiod, bedomningsdatum):
    """Kör flödena på perioderna. Returnerar ett Konteringsresultat, annars KonteringsflodeFel eller MatchningFel.

    regelbok ska komma från las_regelbok, kontoplan från las_kontoplan och momssatser från
    las_momssatser, och kontoplanen och momsfilen ska vara de som regelboken kontrollerades mot.
    underlagsperiod ska komma från las_underlagsperiod och bankperiod från las_bankfil eller
    sla_ihop_bankperioder. Matchningen görs här med matcha_period, på bedomningsdatum. Se överst i filen.
    """
    bokforing, oppettider = _kontrollera_indata(regelbok, kontoplan, momssatser)
    # matcha_period kontrollerar bankperioden, underlagsperioden, regelboken och bedömningsdatumet.
    matchning = matcha_period(bankperiod, underlagsperiod, regelbok, bedomningsdatum)
    korning = _Korning(regelbok, kontoplan, momssatser, underlagsperiod, bankperiod, bokforing, oppettider)
    bankrad_for = {post["underlag"]["id"]: post["bankrad"] for post in matchning.matchningar}
    forslag, arenden = [], []
    for underlag in underlagsperiod.underlag:
        bankrad = bankrad_for.get(underlag["id"])
        bankrader = [] if bankrad is None else [bankrad["id"]]
        regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
        konton, nya = _underlagets_arenden(underlag, regel, korning, bankrader)
        arenden += nya
        if konton is not None and underlag["typ"] in _FLODEN:
            nya_forslag, nya = _FLODEN[underlag["typ"]](underlag, regel, konton, bankrad, korning)
            forslag += nya_forslag
            arenden += nya
    return Konteringsresultat(forslag=tuple(forslag), arenden=_frys(arenden), matchning=matchning)
