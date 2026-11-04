"""Flödena som gör konteringsförslag av underlag och bankrader, med ärenden från K4, K5, K7 och K8.

kontera_period är den enda offentliga funktionen. Den tar emot regelboken från las_regelbok,
kontoplanen från las_kontoplan, momsfilen från las_momssatser, underlagsperioden från
las_underlagsperiod, bankperioden från las_bankfil (eller sla_ihop_bankperioder) och
bedömningsdatumet, ÅÅÅÅ-MM-DD. Den matchar själv bankraderna mot underlagen med matcha_period, så
att matchningen alltid är gjord mot samma perioder och samma regelbok som förslagen. Varje förslag
skapas av skapa_konteringsforslag, som alltid kör K2, ursprungskontrollen och, för underlag, K5, K7
och K8 (konteringsforslag.py, Hugos beslut 2026-10-30, granskning 22, P1). Inget förslag skapas på
något annat sätt.

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

Flöde b, kvitto betalat från bankkontot (DESIGN avsnitt 4b): en verifikation när matchningen har parat
ihop kvittot med en bankrad, på datumet för 'kvitto'. Kostnaden och momsen per momsrad i debet, som i
flöde a, och bankkontot i kredit. Ett kvitto utan bankrad får inget förslag än: det väntar och står
bland matchningens oavstämda underlag.

Flöde e, bankrader utan underlag som regelboken pekar ut som rena avgifter (DESIGN avsnitt 4e, Hugos
beslut 2026-10-29, D13 och beslut c efter uppgift 4): en bankrad som matchningen har lagt bland raderna
som inte kräver underlag, och vars regel i regelboken (Regelbok.regel_for_bankrad, på datumet för
'bankrad') säger det uttryckligen med nyckeln 'flode' (las_regelbok.FLODE_BANKAVGIFT). Kärnan väljer
aldrig flödet utan nyckeln, till exempel för att regeln bara har kontot 'kostnad'. En verifikation:
kostnaden i debet och bankkontot i kredit, båda med bankraden som ursprung, utan moms och med
bankraden som underlag tills bankens specifikation finns (Ö11). Gränserna står i konfigurationen,
aldrig här: matchningsformatets hogst_belopp_ore och regelns eget hogst_belopp_ore i villkoren.

  regeln saknar flöde (beslut c): pengar ut på en regel utan 'flode'. Inget annat flöde tar pengar ut
     från banken utan underlag, så Vera gissar inte: ett ärende med nivå D och "kräver mänsklig
     bedömning" (som allt annat från banken, D13), inget förslag. Pengar in på en regel utan 'flode'
     (kortinlösen, Swish och kontanter) hör till flöde d (uppgift 5) och får varken förslag eller
     ärende här.
  över gräns (D13): en bankrad som passar en regel i matchningsformatet för pengar ut men är större än
     matchningsformatets gräns (matchningens ärende "över gräns"), eller större än gränsen i regelns
     villkor. Allt annat från banken kräver en faktura: ett ärende med nivå D och "kräver mänsklig
     bedömning", inget förslag, för alla regler för pengar ut (beslut d). Andra bankrader utan underlag
     är matchningens ärenden (K3, "saknat underlag"), och deras nivå sätts i nivåsteget.
  oklar post: pengar in på en regel för flödet för bankavgifter. Inget förslag.
  ingen regel på datumet: ingen regel i regelboken gäller bankraden på datumet.

Kontrollerna för varje underlag, innan något förslag görs:

  K4 (Hugos beslut 2026-10-30, granskning 22, P2): ett underlag som underlagsperiodens kontroll K4 har
     flaggat (K4 dublett, K4a och K4b samma fakturanummer med annat belopp eller datum, K4c möjlig
     dublett) får inget förslag alls, inte heller för betalningen, och inga andra ärenden: det ligger
     på samma linje som K5 och K8. Varje ärende i Underlagsperiod.arenden följer med i resultatet, med
     underlagsperiodens kontroll som kontroll, dess text (till exempel "möjlig dublett av <id>") som
     typ, och underlagets bankrad och regel om de finns. En dublett (K4) står inte i perioden och har
     därför varken bankrad eller regel. Nivån sätts i nivåsteget (DESIGN avsnitt 5 säger C), så ärendet
     har varken nivå eller märkningen "kräver mänsklig bedömning". Det underlag som flaggan jämför med
     (originalet, underlaget med lägst id) behandlas efter kontrollen (Hugos beslut 2026-10-30 om
     granskning 23, Öppet 29):
       K4a och K4b (samma fakturanummer, olika belopp eller datum): BÅDA underlagen i paret stoppas.
          Två underlag med samma fakturanummer och olika uppgifter kan inte båda vara rätt, och bara en
          människa vet vilket. Originalet får ett eget ärende med samma kontroll och typ, som pekar på
          det flaggade underlaget, och inget förslag, varken för underlaget eller för betalningen.
       K4c (möjlig dublett): bara det flaggade underlaget stoppas. Originalet får sitt förslag, och
          förslagets motivering märks med K4c-ärendet (det flaggade underlagets id, MARKNING_K4C), så att
          den som godkänner ser kopplingen. Ett ärende har inget eget id: det pekas ut av kontrollen och
          underlagets id.
       K4 (dublett): dubletten är redan borttagen ur perioden, och originalet får sitt förslag som förut.
     Svaret på ett ärende går sedan genom samma kontroller som ett nytt förslag (SPEC 4).
  Regeln: regelboken ger regeln för underlagets typ och motpart på underlagets datum. Ingen regel
     betyder en ny motpart: ett ärende, "ny motpart", och Vera gissar inget konto.
  K7, K5 och K8 körs av konteringsforslag.kontrollera_underlag, samma kod som skapa_konteringsforslag
     kör på varje förslag med underlag (Hugos beslut 2026-10-30, granskning 22, P1). Flödena anropar
     den före förslaget för att göra ärenden i stället för förslag. Vad kontrollerna prövar står i
     konteringsforslag.py:
     K7: ett underlag från en ägare eller närstående blir alltid ett ärende, "kräver mänsklig
        bedömning", som ägarens bankrader i matchningen (SPEC K7). Nivån sätts i nivåsteget (uppgift 6).
     K5 (DESIGN avsnitt 6): ett ärende, "fel momssats" eller "moms stämmer inte med satsen".
     K8 (DESIGN avsnitt 6): ett ärende, "avdragsbegränsat", som bara säger vilket underlag och vilken
        bankrad det gäller, aldrig hur stor del som får dras av. Ett underlag daterat en dag då företaget
        har stängt (regelbokens oppettider) får dessutom flaggan STANGD_DAG i ärendet. Flaggan avgör
        inget själv.

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
(K4-ärendena först, sedan underlagens och bankradernas) och hela matchningen (Matchningsresultat), så
att matchningens egna ärenden, de väntande bankraderna och de oavstämda underlagen inte försvinner. Fel i indatan stoppar med ett KonteringsflodeFel (eller
ett MatchningFel från matcha_period, som kontrollerar perioderna och bedömningsdatumet), och inget
resultat returneras. Ett förslag som skapa_konteringsforslag stoppar är ett fel i kärnan och stoppar
också allt.

Texterna i underlag och bankrader är data, aldrig instruktioner (K17). Koden här jämför dem bara.
"""

import datetime as dt
from types import MappingProxyType
from typing import NamedTuple

from belopp import formatera_ore as _kronor
from konteringsforslag import MARKNING_K4C, kontrollera_underlag, skapa_konteringsforslag
from las_kontoplan import Kontoplan
from las_momssatser import Momssatser
from las_regelbok import FLODE_BANKAVGIFT, VECKODAGAR, Regelbok, RegelbokFel
from matcha_bank import matcha_period

ARENDE_NYCKLAR = ("kontroll", "typ", "text", "niva", "kraver_mansklig_bedomning", "underlag", "bankrader", "regel",
                  "flaggor")
# Flaggan i ett ärende från K8 när underlaget är daterat en dag då företaget har stängt (DESIGN avsnitt 6).
STANGD_DAG = "köpt en dag då företaget har stängt"
# K4-kontrollerna i underlagsperioden (las_underlag.py) som stoppar båda underlagen i paret (Öppet 29). Skiljer
# både beloppet och datumet är kontrollen "K4a och K4b".
_K4A = "K4a"
_K4B = "K4b"
_K4C = "K4c"
_STOPPAR_BADA = (_K4A, _K4B, _K4A + " och " + _K4B)

# Ärendenas kontroller och typer. "över gräns" är samma typ som matchningens (matcha_bank.py). K5, K7 och
# K8 heter som i fynden från konteringsforslag.kontrollera_underlag.
_K3 = "K3"
_OVER_GRANS = "över gräns"
_OKLAR_POST = "oklar post"
_K5 = "K5"
_K8 = "K8"
_REGELBOKEN = "regelboken"
_NY_MOTPART = "ny motpart"
_INGEN_REGEL = "ingen regel på datumet"
_SAKNAR_FLODE = "regeln saknar flöde"
# Nivån som ärenden från K5 och K8 bär direkt (B2).
_NIVA_D = "D"

# Typerna av underlag i flöde a och b (las_underlag.TYPER).
_LEVERANTORSFAKTURA = "leverantorsfaktura"
_KVITTO = "kvitto"
# Värdena i 'verifikationsdatum' som är underlagets eget datum (las_regelbok.VERIFIKATIONSDATUM). Alla
# andra värden är namnet på ett fält i bankraden.
_UNDERLAGETS_DATUM = ("fakturadatum", "kvittodatum")
_BETALNING = "betalning"
_BANKRAD = "bankrad"
# Nyckeln i konteringen för en regel för bankrader som bara har en kostnad (las_regelbok.KONTERING_BANKRAD_NYCKLAR).
_KOSTNAD = "kostnad"
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
    k4c_markeringar: object  # {originalets id: [id för underlag som K4c har flaggat som möjlig dublett av det]}


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


def _stangd_dag(datum, oppettider):
    """True om företaget har stängt på datumet (regelbokens oppettider)."""
    veckodag = VECKODAGAR[dt.date.fromisoformat(datum).weekday()]
    return veckodag in oppettider["stangda_veckodagar"] or datum in oppettider["stangda_datum"]


def _underlagets_regel_id(underlag, regelbok):
    """Regelns id för underlaget på dess datum, eller None (också när underlag är None, en borttagen dublett)."""
    regel = None if underlag is None else regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"],
                                                                      underlag["datum"])
    return None if regel is None else regel["id"]


def _k4_arende(k4, underlag, bankrad, regelbok):
    """Ärendet i resultatet för ett ärende k4 från underlagsperiodens K4 (P2). underlag är None för en dublett."""
    bada = " Inget förslag görs för något av de två underlagen." if k4["kontroll"] in _STOPPAR_BADA else ""
    return _arende(k4["kontroll"], k4["text"], "Underlaget är flaggat av kontrollen " + k4["kontroll"]
                   + " i underlagsperioden: " + k4["text"] + ". Inget förslag görs, varken för underlaget eller för"
                   " dess betalning." + bada + " En människa avgör om det är samma underlag som "
                   + repr(k4["jamfort_med"]) + " eller ett annat.", k4["id"], [] if bankrad is None else [bankrad["id"]],
                   _underlagets_regel_id(underlag, regelbok))


def _k4_arende_for_originalet(k4, original, bankrad, regelbok):
    """Ärendet för originalet i ett par som K4a eller K4b har flaggat: båda stoppas (Öppet 29)."""
    return _arende(k4["kontroll"], k4["text"], "Underlaget " + repr(k4["id"]) + " är flaggat av kontrollen "
                   + k4["kontroll"] + " i underlagsperioden mot det här underlaget: " + k4["text"] + ". Inget förslag"
                   " görs för något av de två underlagen, varken för underlaget eller för dess betalning, eftersom"
                   " båda inte kan vara rätt och bara en människa kan avgöra vilket som stämmer.", original["id"],
                   [] if bankrad is None else [bankrad["id"]], _underlagets_regel_id(original, regelbok))


def _markning_k4c(underlag, korning):
    """Texten som läggs till motiveringen när K4c har flaggat andra underlag som möjliga dubbletter av underlag."""
    flaggade = [id_ for original in underlag for id_ in korning.k4c_markeringar.get(original, [])]
    if not flaggade:
        return ""
    return (" " + MARKNING_K4C + ": " + ("underlaget " if len(flaggade) == 1 else "underlagen ")
            + ", ".join(map(repr, flaggade)) + " är flaggat i underlagsperioden som möjlig dublett av det här"
            " förslagets underlag och har ett eget ärende (K4c) utan förslag. Den som godkänner bör se förslaget och"
            " ärendet tillsammans.")


def _underlagets_arenden(underlag, regel, korning, bankrader):
    """Ärendena för ett underlag före förslaget: regeln, och K7, K5 och K8. Returnerar (konton per sats, ärenden).

    K7, K5 och K8 körs av konteringsforslag.kontrollera_underlag, samma kod som skapa_konteringsforslag
    sedan kör på förslaget (P1). Varje fynd blir ett ärende, med nivå D för K5 och K8 (B2) och flaggan
    STANGD_DAG på K8 när underlaget är daterat en stängd dag.
    """
    id_, regelbok = underlag["id"], korning.regelbok
    if regel is None:
        return None, [_arende(_REGELBOKEN, _NY_MOTPART, "Ingen regel i regelboken passar underlaget (" + underlag["typ"]
                              + ") på " + underlag["datum"] + ". Vera gissar inget konto. En människa väljer konto,"
                              " och svaret kan bli ett förslag till en ny regel.", id_, bankrader,
                              kraver=regelbok.ar_agare_eller_narstaende(underlag["motpart"]))]
    kontroll = kontrollera_underlag(underlag, regel, regelbok, korning.momssatser)
    arenden = []
    for fynd in kontroll.fynd:
        flaggor = [STANGD_DAG] if fynd.kontroll == _K8 and _stangd_dag(underlag["datum"], korning.oppettider) else []
        arenden.append(_arende(fynd.kontroll, fynd.typ, fynd.text, id_, bankrader, regel["id"],
                               _NIVA_D if fynd.kontroll in (_K5, _K8) else None, True, flaggor))
    return kontroll.konton, arenden


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
    """Skapar förslaget med skapa_konteringsforslag, som kör K2, ursprungskontrollen och K5, K7 och K8. Returnerar det."""
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
        "motivering": motivering + _markning_k4c(underlag, korning),
    }
    return skapa_konteringsforslag(forslag, regelbok, kontoplan, korning.momssatser, korning.underlagsperiod,
                                   korning.bankperiod)


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


def _kvitto(underlag, regel, konton, bankrad, korning):
    """Flöde b: kvittot, när matchningen har parat ihop det med en bankrad. Returnerar (förslag, ärenden)."""
    if bankrad is None:
        return [], []
    id_, kontoplan, bokforing = underlag["id"], korning.kontoplan, korning.bokforing
    val = bokforing["verifikationsdatum"][_KVITTO]
    datum = _verifikationens_datum(val, underlag, bankrad)
    arende = _regeln_pa(underlag, regel, datum, korning, bankrad, "Kvittot")
    if arende is not None:
        return [], [arende]
    return [_skapa(
        "F-KVITTO-" + id_, datum, "Kvitto " + underlag["fakturanummer"] + ", underlag " + id_,
        _kostnad_och_moms(underlag, konton, kontoplan, datum)
        + [_rad(kontoplan.rollens_konto(_BANK, datum), 0, -bankrad[_BELOPPSFALT], _bankradens(bankrad["id"]))],
        regel, korning, "Regeln " + regel["id"] + " i regelboken. Kvittot är betalt från bankkontot: matchningen har"
        " parat ihop det med bankraden med radnummer " + str(bankrad["radnr"]) + " (samma belopp och motpart, inom"
        " tidsfönstret). Verifikationen får " + val + _antaget(bokforing) + ".",
        underlag=[id_], bankrader=[bankrad["id"]])], []


# Flödet för varje typ av underlag (las_underlag.TYPER). Ett underlag av en typ som saknas här får
# kontrollerna men inget förslag.
_FLODEN = {_LEVERANTORSFAKTURA: _leverantorsfaktura, _KVITTO: _kvitto}


def _over_grans(rad, regel, text):
    """D13: en bankrad som passar en regel för bankrader utan underlag men är över gränsen. Nivå D, inget förslag."""
    return _arende(_K3, _OVER_GRANS, text + " Enligt D13 kräver allt annat från banken en faktura. Inget förslag görs."
                   " En människa avgör vad raden är och vilket underlag den ska ha.", bankrader=[rad["id"]],
                   regel=None if regel is None else regel["id"], niva=_NIVA_D, kraver=True)


def _bankrad_utan_underlag(rad, namn, korning):
    """Flöde e för en bankrad som matchningen har lagt bland raderna som inte kräver underlag. (förslag, ärenden)."""
    bokforing = korning.bokforing
    val = bokforing["verifikationsdatum"][_BANKRAD]
    datum = _verifikationens_datum(val, None, rad)
    regel = korning.regelbok.regel_for_bankrad(namn, datum)
    if regel is None:
        return [], [_arende(_REGELBOKEN, _INGEN_REGEL, "Bankraden med radnummer " + str(rad["radnr"]) + " passar"
                            " regeln " + repr(namn) + " för bankrader utan underlag, men ingen regel i regelboken gäller"
                            " den på " + datum + ". Inget förslag görs.", bankrader=[rad["id"]])]
    if regel.get("flode") != FLODE_BANKAVGIFT:
        if rad[_BELOPPSFALT] > 0:
            # Pengar in (kortinlösen, Swish och kontanter): flöde d (uppgift 5).
            return [], []
        return [], [_arende(
            _REGELBOKEN, _SAKNAR_FLODE, "Bankraden med radnummer " + str(rad["radnr"]) + " passar regeln " + repr(namn)
            + " för bankrader utan underlag, och regeln " + regel["id"] + " i regelboken gäller pengar ut men säger"
            " inte vilket flöde den hör till (nyckeln 'flode'). Vera gissar inte. Inget förslag görs. En människa"
            " avgör vad raden är, och regelboken behöver nyckeln.", bankrader=[rad["id"]], regel=regel["id"],
            niva=_NIVA_D, kraver=True)]
    if rad[_BELOPPSFALT] > 0:
        # Nås inte med en regelbok från las_regelbok, som stoppar 'flode' på en regel för pengar in (Öppet 28,
        # Hugos beslut 2026-10-30). Står kvar som ett skydd: pengar in bokförs aldrig som en avgift.
        return [], [_arende(_REGELBOKEN, _OKLAR_POST, "Bankraden med radnummer " + str(rad["radnr"]) + " är pengar in,"
                            " men regeln " + regel["id"] + " gäller avgifter, som är pengar ut. Inget förslag görs.",
                            bankrader=[rad["id"]], regel=regel["id"], kraver=True)]
    grans = regel["villkor"].get("hogst_belopp_ore")
    if grans is not None and -rad[_BELOPPSFALT] > grans:
        return [], [_over_grans(rad, regel, "Bankraden med radnummer " + str(rad["radnr"]) + " passar regeln "
                                + regel["id"] + ", men beloppet " + _kronor(-rad[_BELOPPSFALT]) + " kr är större än"
                                " regelns gräns, " + _kronor(grans) + " kr.")]
    kontoplan, belopp = korning.kontoplan, -rad[_BELOPPSFALT]
    return [_skapa(
        "F-BANKRAD-" + rad["id"], datum, "Bankrad utan underlag, radnummer " + str(rad["radnr"]),
        [_rad(regel["kontering"][_KOSTNAD], belopp, 0, _bankradens(rad["id"])),
         _rad(kontoplan.rollens_konto(_BANK, datum), 0, belopp, _bankradens(rad["id"]))],
        regel, korning, "Regeln " + regel["id"] + " i regelboken, för bankrader utan underlag (regeln " + repr(namn)
        + " i matchningsformatet). Utan moms och med bankraden som underlag tills bankens specifikation finns (D13,"
        " Ö11). Verifikationen får bankradens " + val + _antaget(bokforing) + ".", bankrader=[rad["id"]])], []


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
    bankrad_for = {post["underlag"]["id"]: post["bankrad"] for post in matchning.matchningar}
    forslag, arenden = [], []
    # K4 (P2): underlagsperiodens ärenden följer med, och de flaggade underlagen får inget förslag. Öppet 29: vid
    # K4a och K4b stoppas också originalet, med ett eget ärende, och vid K4c märks originalets förslag.
    i_perioden = {underlag["id"]: underlag for underlag in underlagsperiod.underlag}
    flaggade, k4c_markeringar = set(), {}
    for k4 in underlagsperiod.arenden:
        flaggade.add(k4["id"])
        arenden.append(_k4_arende(k4, i_perioden.get(k4["id"]), bankrad_for.get(k4["id"]), regelbok))
        original = k4["jamfort_med"]
        if k4["kontroll"] in _STOPPAR_BADA:
            flaggade.add(original)
            arenden.append(_k4_arende_for_originalet(k4, i_perioden[original], bankrad_for.get(original), regelbok))
        elif k4["kontroll"] == _K4C:
            k4c_markeringar.setdefault(original, []).append(k4["id"])
    korning = _Korning(regelbok, kontoplan, momssatser, underlagsperiod, bankperiod, bokforing, oppettider,
                       k4c_markeringar)
    for underlag in underlagsperiod.underlag:
        if underlag["id"] in flaggade:
            continue
        bankrad = bankrad_for.get(underlag["id"])
        bankrader = [] if bankrad is None else [bankrad["id"]]
        regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
        konton, nya = _underlagets_arenden(underlag, regel, korning, bankrader)
        arenden += nya
        if konton is not None and underlag["typ"] in _FLODEN:
            nya_forslag, nya = _FLODEN[underlag["typ"]](underlag, regel, konton, bankrad, korning)
            forslag += nya_forslag
            arenden += nya
    for post in matchning.kraver_inte_underlag:
        nya_forslag, nya = _bankrad_utan_underlag(post["bankrad"], post["regel"], korning)
        forslag += nya_forslag
        arenden += nya
    for arende in matchning.arenden:
        if arende["typ"] == _OVER_GRANS:
            rad = arende["bankrad"]
            datum = _verifikationens_datum(bokforing["verifikationsdatum"][_BANKRAD], None, rad)
            arenden.append(_over_grans(rad, regelbok.regel_for_bankrad(arende["regel"], datum), (
                "Bankraden med radnummer " + str(rad["radnr"]) + " passar regeln " + repr(arende["regel"]) + " för"
                " bankrader utan underlag, men beloppet " + _kronor(-rad[_BELOPPSFALT]) + " kr är större än gränsen i"
                " matchningsformatet, " + _kronor(arende["hogst_belopp_ore"]) + " kr.")))
    return Konteringsresultat(forslag=tuple(forslag), arenden=_frys(arenden), matchning=matchning)
