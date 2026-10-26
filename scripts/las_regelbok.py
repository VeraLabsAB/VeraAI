"""Läser och kontrollerar ett företags regelbok (foretag/<namn>/regelbok.json).

Regelboken säger hur företagets händelser ska konteras: "när det här kommer in, föreslå den här
konteringen, på den här nivån" (DESIGN-regelbok.md avsnitt 1). Kärnan vet inte vilka motparter,
konton eller varugrupper ett företag har. Allt det står i filen, aldrig här.

Filen ska ha exakt nycklarna i REGELBOK_NYCKLAR, och får ha nycklarna i REGELBOK_VALFRIA_NYCKLAR:

  foretag     företagets namn, text. Visas för människor och i loggen
  version     regelbokens version, ett heltal från 1. Visas för människor och i loggen
  godkand     vem som godkände regelboken och när: exakt nycklarna i GODKAND_NYCKLAR (av: text,
              datum: ÅÅÅÅ-MM-DD). Visas för människor. Det som skyddar är kontrollsumman
  granser     företagets beloppsgränser för nivå A och B, i öre: exakt nycklarna i GRANSER_NYCKLAR.
              Heltal större än 0. A-gränsen får inte vara högre än B-gränsen
  k9          värdena för K9 (ovanliga belopp): exakt nycklarna i K9_NYCKLAR. minst_historik är
              också hur många gånger en regel ska ha godkänts innan den kan ge nivå A (avsnitt 5).
              minst_historik är ett heltal från 1, hogst_procent_av_median från 100 och
              lagst_procent_av_median från 0 till och med 100
  oppettider  företagets stängda dagar, för varningssignalen i K8 (Hugos beslut D21): exakt
              nycklarna i OPPETTIDER_NYCKLAR. stangda_veckodagar är en lista med veckodagar ur
              VECKODAGAR, och stangda_datum en lista med datum, ÅÅÅÅ-MM-DD. Varje dag får stå en
              gång. En lista får vara tom: då har företaget inga sådana stängda dagar. Läses och
              kontrolleras, men används inte än
  regler      en lista med minst en regel, se nedan
  anteckning  fri text för människor. Används inte av koden
  agare_och_narstaende
              valfri lista med motparter som är ägare eller närstående (K7, Hugos beslut
              2026-10-26). Varje motpart är text och får stå en gång: två motparter som blir samma
              efter normaliseringen (normalisering.py) räknas som samma och stoppar filen. Saknas
              nyckeln är listan tom, och en tom lista godtas. Uppslaget ar_agare_eller_narstaende
              säger om en motpart står i listan, så att nivåsteget kan använda det

En regel har exakt nycklarna i REGEL_NYCKLAR, och får ha nycklarna i REGEL_VALFRIA_NYCKLAR:

  id          regelns fasta id, text. Står i varje förslag. Två id som blir samma efter
              normaliseringen (normalisering.py) räknas som samma och stoppar filen
  galler      vad regeln gäller. Nyckeln kalla säger vilken källa, en av KALLOR, och de andra
              nycklarna beror på källan (KALLOR):
                underlag   typ (en av las_underlag.TYPER) och motpart
                z_rapport  kassaregister
                bankrad    matchningsregel: namnet på en regel i matchning.json, för bankrader
                           som inte kräver underlag
  kontering   vilka konton regeln bokför på. Formen beror på källan:
                underlag   ett objekt med ett konto per varugrupp
                z_rapport  exakt nycklarna i KONTERING_Z_NYCKLAR: forsaljning (ett konto per
                           varugrupp) och betalsatt (ett konto per betalsätt, med betalsättets
                           postnamn i kassaformatet)
                bankrad    en eller flera av nycklarna i KONTERING_BANKRAD_NYCKLAR, var och en
                           med ett konto
              Ett konto skrivs som text, till exempel "1234", och ska finnas i kontoplanen och
              gälla under hela tiden regeln gäller. En varugrupp ska ha en sats i momsfilen för
              varje dag regeln gäller
  villkor     exakt nycklarna i VILLKOR_NYCKLAR, och valfritt de i VILLKOR_VALFRIA_NYCKLAR:
                giltig_fran       första dagen regeln gäller, ÅÅÅÅ-MM-DD
                giltig_till       sista dagen regeln gäller, ÅÅÅÅ-MM-DD, eller null (tills vidare)
                hogst_belopp_ore  regelns egen beloppsgräns i öre, ett heltal större än 0. Får
                                  inte vara högre än företagets B-gräns: en regel kan bara skärpa
                                  företagets gränser, aldrig höja dem (Hugos beslut D20)
                avdragsbegransad  true eller false. true betyder att posten alltid blir ett ärende
                                  på nivå D (K8)
  niva        den lägsta nivån ett förslag med regeln kan få, en av NIVAER
  anteckning  fri text för människor. Används inte av koden

Regler för regelboken som helhet:

- Högst en regel får passa. Två regler med samma källa och samma värden i 'galler' (efter
  normaliseringen) och datum som överlappar stoppar filen. Ingen regel får vara tvetydig.
- En regel för bankrader pekar på en regel i matchning.json, som ska finnas. Är den regeln för
  pengar ut måste regelboken också ha hogst_belopp_ore, och gränsen får inte vara högre än
  gränsen i matchning.json.
- En regel för bankrader får aldrig ha nivå A, eftersom bankrader utan underlag aldrig blir A
  (Hugos beslut D20).
- En regel för underlag vars motpart står i agare_och_narstaende (efter normaliseringen) måste
  ha nivå D (K7). Annars stoppas filen.

Hela filen stoppas vid minsta fel med ett RegelbokFel: okänd eller saknad nyckel, fel typ (till
exempel ett decimaltal i ett belopp), ett tomt värde, ett dolt tecken någonstans i filen (även i
nycklar och anteckningar), en regel som står två gånger eller kan passa samma sak som en annan,
ett konto som inte finns i kontoplanen, en varugrupp som saknar sats i momsfilen, en motpart som
står två gånger i agare_och_narstaende, eller en regel för en ägare eller närstående som inte har
nivå D. Filen läses
med de gemensamma skydden i inlasning_skydd.py (UTF-8, dubbla nycklar, för djup nästling och för
långa tal), som de andra formatfilerna.

las_regelbok är den enda offentliga funktionen som läser filen. Den tar emot kontoplanen från
las_kontoplan, momssatserna från las_momssatser och matchningsformatet från
ladda_matchningsformat, och kör alltid alla kontroller. Den returnerar en Regelbok, som inte går
att ändra och bara kan skapas av las_regelbok. Regelboken har en kontrollsumma (SHA-256 av filens
bytes, som text med 64 tecken), så att varje förslag kan visa vilken regelbok som användes. Samma
fil ger alltid samma summa, och minsta ändring ger en annan.
"""

import datetime as dt
import hashlib
from types import MappingProxyType

from inlasning_skydd import (
    _Filsort, _datumtext, _heltal_i_json, _inga_dolda_tecken_i_json, _json_typ, _kontrollera_nycklar, _las_jsonfil,
    _text_i_json, _tolka_json,
)
from las_kontoplan import Kontoplan
from las_matchningsformat import MatchningsformatFel, kontrollera_matchningsformat
from las_momssatser import Momssatser, MomssatsFel
from las_underlag import HELTAL_HOGST_SIFFROR, TYPER
from normalisering import normalisera_for_jamforelse

REGELBOK_NYCKLAR = ("foretag", "version", "godkand", "granser", "k9", "oppettider", "regler")
REGELBOK_VALFRIA_NYCKLAR = ("anteckning", "agare_och_narstaende")
GODKAND_NYCKLAR = ("av", "datum")
GRANSER_NYCKLAR = ("a_hogst_ore", "b_hogst_ore")
K9_NYCKLAR = ("minst_historik", "hogst_procent_av_median", "lagst_procent_av_median")
OPPETTIDER_NYCKLAR = ("stangda_veckodagar", "stangda_datum")
VECKODAGAR = ("mandag", "tisdag", "onsdag", "torsdag", "fredag", "lordag", "sondag")
REGEL_NYCKLAR = ("id", "galler", "kontering", "villkor", "niva")
REGEL_VALFRIA_NYCKLAR = ("anteckning",)
# Källorna en regel kan gälla, och nycklarna i 'galler' för varje källa utöver 'kalla'.
KALLOR = {"underlag": ("typ", "motpart"), "z_rapport": ("kassaregister",), "bankrad": ("matchningsregel",)}
KONTERING_Z_NYCKLAR = ("forsaljning", "betalsatt")
KONTERING_BANKRAD_NYCKLAR = ("motkonto", "avgift", "kostnad")
VILLKOR_NYCKLAR = ("giltig_fran",)
VILLKOR_VALFRIA_NYCKLAR = ("giltig_till", "hogst_belopp_ore", "avdragsbegransad")
NIVAER = ("A", "B", "C", "D")

# Det största heltalet i filen, som för talen i underlagen.
_HOGSTA_TAL = 10 ** HELTAL_HOGST_SIFFROR - 1


class RegelbokFel(Exception):
    """Regelboken kunde inte läsas eller är fel."""


# Det som skiljer regelbokens felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
# Bara fel, formatet och nivaer används för ett JSON-format.
_REGELBOK = _Filsort(
    fel=RegelbokFel,
    filen="Regelboken",
    formatet="Regelboken",
    exportera_igen="Spara filen igen",
    om_styrtecken="Sådana tecken finns inte i en vanlig regelbok.",
    ihopslaget="flera regler",
    nivaer="En regelbok har bara fem nivåer.",
)


def _objekt(varde, vad, var):
    """varde ska vara ett objekt med nycklar."""
    if not isinstance(varde, dict):
        raise RegelbokFel(var + ": " + vad + " ska vara ett objekt med nycklar, inte " + _json_typ(varde) + ".")
    return varde


def _belopp(varde, vad, var):
    """Ett belopp i öre: ett heltal större än 0. Decimaltal, text och true/false stoppas."""
    return _heltal_i_json(varde, vad, 1, _HOGSTA_TAL, var, _REGELBOK)


def _kontrollera_godkand(godkand, var):
    _objekt(godkand, "'godkand'", var)
    _kontrollera_nycklar(godkand, GODKAND_NYCKLAR, (), var + ", 'godkand',", _REGELBOK)
    return {"av": _text_i_json(godkand["av"], "'av' i 'godkand'", var, _REGELBOK),
            "datum": _datumtext(godkand["datum"], "'datum' i 'godkand'", var, _REGELBOK)}


def _kontrollera_granser(granser, var):
    """Företagets gränser för nivå A och B. A-gränsen får inte vara högre än B-gränsen."""
    _objekt(granser, "'granser'", var)
    _kontrollera_nycklar(granser, GRANSER_NYCKLAR, (), var + ", 'granser',", _REGELBOK)
    nya = {nyckel: _belopp(granser[nyckel], repr(nyckel) + " i 'granser'", var) for nyckel in GRANSER_NYCKLAR}
    if nya["a_hogst_ore"] > nya["b_hogst_ore"]:
        raise RegelbokFel(
            var + ": 'a_hogst_ore' (" + str(nya["a_hogst_ore"]) + ") är högre än 'b_hogst_ore' ("
            + str(nya["b_hogst_ore"]) + "). Gränsen för nivå A får inte vara högre än gränsen för nivå B."
        )
    return nya


def _kontrollera_k9(k9, var):
    _objekt(k9, "'k9'", var)
    _kontrollera_nycklar(k9, K9_NYCKLAR, (), var + ", 'k9',", _REGELBOK)
    return {
        "minst_historik": _heltal_i_json(k9["minst_historik"], "'minst_historik' i 'k9'", 1, _HOGSTA_TAL, var,
                                         _REGELBOK),
        "hogst_procent_av_median": _heltal_i_json(k9["hogst_procent_av_median"], "'hogst_procent_av_median' i 'k9'",
                                                  100, _HOGSTA_TAL, var, _REGELBOK),
        "lagst_procent_av_median": _heltal_i_json(k9["lagst_procent_av_median"], "'lagst_procent_av_median' i 'k9'",
                                                  0, 100, var, _REGELBOK),
    }


def _lista(varden, vad, var):
    """varden ska vara en lista. Den får vara tom."""
    if not isinstance(varden, list):
        raise RegelbokFel(var + ": " + vad + " ska vara en lista, inte " + _json_typ(varden) + ".")
    return varden


def _inga_dubbletter(varden, vad, var):
    """Varje värde i listan (text, redan kontrollerad) ska stå en gång. Returnerar en ny lista."""
    for nummer, varde in enumerate(varden):
        if varde in varden[:nummer]:
            raise RegelbokFel(var + ": " + repr(varde) + " står flera gånger i " + vad + ".")
    return list(varden)


def _kontrollera_oppettider(oppettider, var):
    """Företagets stängda veckodagar och datum (D21). Läses och kontrolleras, men används inte än."""
    _objekt(oppettider, "'oppettider'", var)
    _kontrollera_nycklar(oppettider, OPPETTIDER_NYCKLAR, (), var + ", 'oppettider',", _REGELBOK)
    veckodagar = _lista(oppettider["stangda_veckodagar"], "'stangda_veckodagar'", var)
    for dag in veckodagar:
        if not isinstance(dag, str) or dag not in VECKODAGAR:
            raise RegelbokFel(
                var + ": " + (repr(dag) if isinstance(dag, str) else _json_typ(dag)) + " i 'stangda_veckodagar' är"
                " ingen veckodag. Veckodagarna skrivs " + ", ".join(map(repr, VECKODAGAR)) + "."
            )
    datum = [_datumtext(dag, "datum nummer " + str(nummer) + " i 'stangda_datum'", var, _REGELBOK)
             for nummer, dag in enumerate(_lista(oppettider["stangda_datum"], "'stangda_datum'", var), start=1)]
    return {"stangda_veckodagar": _inga_dubbletter(veckodagar, "'stangda_veckodagar'", var),
            "stangda_datum": _inga_dubbletter(datum, "'stangda_datum'", var)}


def _kontrollera_agare_och_narstaende(agare, var):
    """Motparterna som är ägare eller närstående (K7). Varje motpart en gång, efter normaliseringen."""
    vad = "'agare_och_narstaende'"
    resultat = []
    for nummer, motpart in enumerate(_lista(agare, vad, var), start=1):
        ny = _text_i_json(motpart, "motpart nummer " + str(nummer) + " i " + vad, var, _REGELBOK)
        for annan in resultat:
            if normalisera_for_jamforelse(annan) == normalisera_for_jamforelse(ny):
                raise RegelbokFel(
                    var + ": " + repr(ny) + " står flera gånger i " + vad + " (som " + repr(annan) + "). Varje"
                    " motpart ska stå en gång."
                )
        resultat.append(ny)
    return resultat


def _kontrollera_galler(galler, vad, var):
    """Vad regeln gäller: kalla och nycklarna för källan (KALLOR). Returnerar ett nytt objekt."""
    _objekt(galler, "'galler' i " + vad, var)
    if "kalla" not in galler:
        raise RegelbokFel(var + ", 'galler' i " + vad + ", saknar nyckeln 'kalla'.")
    kalla = galler["kalla"]
    if not isinstance(kalla, str) or kalla not in KALLOR:
        raise RegelbokFel(
            var + ": 'kalla' i 'galler' i " + vad + " ska vara en av " + ", ".join(map(repr, KALLOR)) + ", inte "
            + (repr(kalla) if isinstance(kalla, str) else _json_typ(kalla)) + "."
        )
    _kontrollera_nycklar(galler, ("kalla",) + KALLOR[kalla], (), var + ", 'galler' i " + vad + ",", _REGELBOK)
    nytt = {"kalla": kalla}
    for nyckel in KALLOR[kalla]:
        nytt[nyckel] = _text_i_json(galler[nyckel], repr(nyckel) + " i 'galler' i " + vad, var, _REGELBOK)
    if "typ" in nytt and nytt["typ"] not in TYPER:
        raise RegelbokFel(
            var + ": 'typ' i 'galler' i " + vad + " ska vara en av " + ", ".join(map(repr, TYPER)) + ", inte "
            + repr(nytt["typ"]) + "."
        )
    return nytt


def _kontrollera_villkor(villkor, vad, granser, var):
    """Regelns villkor. Returnerar ett nytt objekt, där giltig_till alltid finns (None betyder tills vidare)."""
    _objekt(villkor, "'villkor' i " + vad, var)
    _kontrollera_nycklar(villkor, VILLKOR_NYCKLAR, VILLKOR_VALFRIA_NYCKLAR, var + ", 'villkor' i " + vad + ",",
                         _REGELBOK)
    fran = _datumtext(villkor["giltig_fran"], "'giltig_fran' i " + vad, var, _REGELBOK)
    till = None
    if villkor.get("giltig_till") is not None:
        till = _datumtext(villkor["giltig_till"], "'giltig_till' i " + vad, var, _REGELBOK)
        if till < fran:
            raise RegelbokFel(var + ": " + vad + " slutar " + till + ", före sitt första datum " + fran + ".")
    nytt = {"giltig_fran": fran, "giltig_till": till}
    if "hogst_belopp_ore" in villkor:
        grans = _belopp(villkor["hogst_belopp_ore"], "'hogst_belopp_ore' i " + vad, var)
        if grans > granser["b_hogst_ore"]:
            raise RegelbokFel(
                var + ": 'hogst_belopp_ore' i " + vad + " (" + str(grans) + ") är högre än företagets gräns"
                " 'b_hogst_ore' (" + str(granser["b_hogst_ore"]) + "). En regel kan bara skärpa företagets gränser,"
                " aldrig höja dem."
            )
        nytt["hogst_belopp_ore"] = grans
    if "avdragsbegransad" in villkor:
        if type(villkor["avdragsbegransad"]) is not bool:
            raise RegelbokFel(
                var + ": 'avdragsbegransad' i " + vad + " ska vara true eller false, inte "
                + _json_typ(villkor["avdragsbegransad"]) + "."
            )
        nytt["avdragsbegransad"] = villkor["avdragsbegransad"]
    return nytt


def _tills_vidare(till):
    return "tills vidare" if till is None else till


def _kontrollera_konto(varde, vad, konton, villkor, var):
    """Ett konto i konteringen. Det ska finnas i kontoplanen och gälla under hela tiden regeln gäller."""
    if not isinstance(varde, str):
        raise RegelbokFel(
            var + ": kontot för " + vad + " ska vara text, till exempel \"1234\", inte " + _json_typ(varde) + "."
        )
    if varde not in konton:
        raise RegelbokFel(var + ": kontot för " + vad + " är " + repr(varde) + ", som inte finns i kontoplanen.")
    konto, fran, till = konton[varde], villkor["giltig_fran"], villkor["giltig_till"]
    if ((konto["fran"] is not None and konto["fran"] > fran)
            or (konto["till"] is not None and (till is None or konto["till"] < till))):
        raise RegelbokFel(
            var + ": kontot för " + vad + " är " + repr(varde) + ", som bara gäller från " + (konto["fran"] or "början")
            + " till " + _tills_vidare(konto["till"]) + ". Regeln gäller från " + fran + " till " + _tills_vidare(till)
            + ", och kontot ska gälla under hela den tiden."
        )
    return varde


def _kontrollera_varugrupp(namn, vad, momssatser, villkor, var):
    """En varugrupp i konteringen. Den ska ha en sats i momsfilen för varje dag regeln gäller."""
    datum, till = villkor["giltig_fran"], villkor["giltig_till"]
    while True:
        try:
            period = momssatser.period(namn, datum)
        except MomssatsFel as fel:
            raise RegelbokFel(
                var + ": varugruppen " + repr(namn) + " i " + vad + " har ingen sats i momsfilen för hela tiden regeln"
                " gäller (från " + villkor["giltig_fran"] + " till " + _tills_vidare(till) + "). " + str(fel)
            ) from None
        if period["till"] is None or (till is not None and period["till"] >= till):
            return namn
        datum = (dt.date.fromisoformat(period["till"]) + dt.timedelta(days=1)).isoformat()


def _konto_per_varugrupp(karta, vad, konton, momssatser, villkor, var):
    """Ett objekt med minst en varugrupp och ett konto för varje. Returnerar ett nytt objekt."""
    if not isinstance(karta, dict):
        raise RegelbokFel(
            var + ": " + vad + " ska vara ett objekt med ett konto per varugrupp, inte " + _json_typ(karta) + "."
        )
    if not karta:
        raise RegelbokFel(var + ": " + vad + " är tom. Den ska ha ett konto för minst en varugrupp.")
    return {_kontrollera_varugrupp(namn, vad, momssatser, villkor, var):
            _kontrollera_konto(konto, "varugruppen " + repr(namn) + " i " + vad, konton, villkor, var)
            for namn, konto in karta.items()}


def _kontrollera_kontering(kontering, kalla, vad, konton, momssatser, villkor, var):
    """Konteringen i den form som källan har. Returnerar ett nytt objekt."""
    vad = "'kontering' i " + vad
    if kalla == "underlag":
        return _konto_per_varugrupp(kontering, vad, konton, momssatser, villkor, var)
    _objekt(kontering, vad, var)
    if kalla == "z_rapport":
        _kontrollera_nycklar(kontering, KONTERING_Z_NYCKLAR, (), var + ", " + vad + ",", _REGELBOK)
        betalsatt = kontering["betalsatt"]
        if not isinstance(betalsatt, dict):
            raise RegelbokFel(
                var + ": 'betalsatt' i " + vad + " ska vara ett objekt med ett konto per betalsätt, inte "
                + _json_typ(betalsatt) + "."
            )
        if not betalsatt:
            raise RegelbokFel(var + ": 'betalsatt' i " + vad + " är tom. Den ska ha ett konto för minst ett betalsätt.")
        nya_betalsatt = {}
        for namn, konto in betalsatt.items():
            _text_i_json(namn, "betalsättet " + repr(namn) + " i " + vad, var, _REGELBOK)
            nya_betalsatt[namn] = _kontrollera_konto(konto, "betalsättet " + repr(namn) + " i " + vad, konton,
                                                     villkor, var)
        return {"forsaljning": _konto_per_varugrupp(kontering["forsaljning"], "'forsaljning' i " + vad, konton,
                                                    momssatser, villkor, var),
                "betalsatt": nya_betalsatt}
    _kontrollera_nycklar(kontering, (), KONTERING_BANKRAD_NYCKLAR, var + ", " + vad + ",", _REGELBOK)
    if not kontering:
        raise RegelbokFel(
            var + ": " + vad + " är tom. Den ska ha minst en av " + ", ".join(map(repr, KONTERING_BANKRAD_NYCKLAR)) + "."
        )
    return {nyckel: _kontrollera_konto(konto, repr(nyckel) + " i " + vad, konton, villkor, var)
            for nyckel, konto in kontering.items()}


def _kontrollera_bankradsregel(regel, vad, matchningsregler, var):
    """Det som gäller bara en regel för bankrader: nivån, regeln i matchning.json och gränsen för pengar ut."""
    if regel["niva"] == "A":
        raise RegelbokFel(
            var + ": " + vad + " gäller bankrader och har nivå 'A'. Bankrader utan underlag blir aldrig nivå A."
        )
    namn = regel["galler"]["matchningsregel"]
    if namn not in matchningsregler:
        raise RegelbokFel(
            var + ": " + vad + " pekar på regeln " + repr(namn) + " i matchningsformatet, som inte finns. Reglerna där"
            " är " + (", ".join(map(repr, matchningsregler)) or "inga") + "."
        )
    matchningsregel = matchningsregler[namn]
    if matchningsregel["riktning"] != "ut":
        return
    if "hogst_belopp_ore" not in regel["villkor"]:
        raise RegelbokFel(
            var + ": " + vad + " gäller bankrader med pengar ut och saknar 'hogst_belopp_ore' i 'villkor'. En regel för"
            " pengar ut ska alltid ha en högsta summa per bankrad."
        )
    if regel["villkor"]["hogst_belopp_ore"] > matchningsregel["hogst_belopp_ore"]:
        raise RegelbokFel(
            var + ": 'hogst_belopp_ore' i " + vad + " (" + str(regel["villkor"]["hogst_belopp_ore"]) + ") är högre än"
            " gränsen för regeln " + repr(namn) + " i matchningsformatet (" + str(matchningsregel["hogst_belopp_ore"])
            + "). En regel kan bara skärpa gränsen, aldrig höja den."
        )


def _kontrollera_agarregel(regel, vad, agare, var):
    """En regel för underlag från en ägare eller närstående (efter normaliseringen) ska ha nivå D (K7)."""
    motpart = normalisera_for_jamforelse(regel["galler"]["motpart"])
    for namn in agare:
        if normalisera_for_jamforelse(namn) == motpart and regel["niva"] != "D":
            raise RegelbokFel(
                var + ": " + vad + " gäller motparten " + repr(regel["galler"]["motpart"]) + ", som står i"
                " 'agare_och_narstaende' (som " + repr(namn) + "), och har nivå " + repr(regel["niva"]) + ". En regel"
                " för ägare och närstående ska alltid ha nivå D."
            )


def _kontrollera_regelboksregel(regel, nummer, granser, agare, konton, momssatser, matchningsregler, var):
    """En regel i 'regler'. Returnerar den som ett nytt objekt."""
    vad = "regel nummer " + str(nummer)
    _objekt(regel, vad, var)
    _kontrollera_nycklar(regel, REGEL_NYCKLAR, REGEL_VALFRIA_NYCKLAR, var + ", " + vad + ",", _REGELBOK)
    nytt = {"id": _text_i_json(regel["id"], "'id' i " + vad, var, _REGELBOK)}
    vad = vad + " (" + nytt["id"] + ")"
    nytt["galler"] = _kontrollera_galler(regel["galler"], vad, var)
    nytt["villkor"] = _kontrollera_villkor(regel["villkor"], vad, granser, var)
    nytt["kontering"] = _kontrollera_kontering(regel["kontering"], nytt["galler"]["kalla"], vad, konton, momssatser,
                                               nytt["villkor"], var)
    if not isinstance(regel["niva"], str) or regel["niva"] not in NIVAER:
        raise RegelbokFel(var + ": 'niva' i " + vad + " ska vara en av " + ", ".join(map(repr, NIVAER)) + ".")
    nytt["niva"] = regel["niva"]
    if "anteckning" in regel:
        nytt["anteckning"] = _text_i_json(regel["anteckning"], "'anteckning' i " + vad, var, _REGELBOK)
    if nytt["galler"]["kalla"] == "bankrad":
        _kontrollera_bankradsregel(nytt, vad, matchningsregler, var)
    if nytt["galler"]["kalla"] == "underlag":
        _kontrollera_agarregel(nytt, vad, agare, var)
    return nytt


def _vad_regeln_galler(galler):
    """Det som avgör om två regler kan passa samma sak: källan och de normaliserade värdena i 'galler'."""
    return (galler["kalla"],) + tuple(normalisera_for_jamforelse(galler[nyckel]) for nyckel in KALLOR[galler["kalla"]])


def _overlappar(en, annan):
    """True om de två reglernas datum har minst en dag gemensamt."""
    return ((en["giltig_till"] is None or annan["giltig_fran"] <= en["giltig_till"])
            and (annan["giltig_till"] is None or en["giltig_fran"] <= annan["giltig_till"]))


def _kontrollera_regelbokens_regler(regler, granser, agare, konton, momssatser, matchningsregler, var):
    """Alla regler: minst en, varje id en gång, och ingen regel som kan passa samma sak som en annan."""
    if not isinstance(regler, list):
        raise RegelbokFel(var + ": 'regler' ska vara en lista med regler, inte " + _json_typ(regler) + ".")
    if not regler:
        raise RegelbokFel(var + ": 'regler' är tom. Regelboken ska ha minst en regel.")
    resultat = []
    for nummer, regel in enumerate(regler, start=1):
        ny = _kontrollera_regelboksregel(regel, nummer, granser, agare, konton, momssatser, matchningsregler, var)
        for annan in resultat:
            if normalisera_for_jamforelse(annan["id"]) == normalisera_for_jamforelse(ny["id"]):
                raise RegelbokFel(
                    var + ": regel-id " + repr(ny["id"]) + " står flera gånger (som " + repr(annan["id"]) + "). Varje"
                    " regel ska ha ett eget id."
                )
            if _vad_regeln_galler(annan["galler"]) == _vad_regeln_galler(ny["galler"]) and _overlappar(
                    annan["villkor"], ny["villkor"]):
                raise RegelbokFel(
                    var + ": reglerna " + repr(annan["id"]) + " och " + repr(ny["id"]) + " kan båda passa samma sak"
                    " på samma dag. Högst en regel får passa, så att det aldrig är oklart vilken regel som gäller."
                )
        resultat.append(ny)
    return resultat


def _konfigurationen(kontoplan, momssatser, matchningsformat):
    """Kontrollerar indata och returnerar (konton, matchningsregler) i den form kontrollerna använder."""
    # type() i stället för isinstance(), så att en underklass med egna regler inte släpps igenom.
    if type(kontoplan) is not Kontoplan:
        raise RegelbokFel("Regelboken kan inte kontrolleras: kontoplanen ska komma från las_kontoplan, inte vara "
                          + type(kontoplan).__name__ + ".")
    if type(momssatser) is not Momssatser:
        raise RegelbokFel("Regelboken kan inte kontrolleras: momssatserna ska komma från las_momssatser, inte vara "
                          + type(momssatser).__name__ + ".")
    try:
        matchning = kontrollera_matchningsformat(matchningsformat)
    except MatchningsformatFel as fel:
        raise RegelbokFel("Regelboken kan inte kontrolleras: matchningsformatet är fel. " + str(fel)) from None
    konton = {konto["nummer"]: konto for konto in kontoplan.konton}
    return konton, {regel["namn"]: regel for regel in matchning["kraver_inte_underlag"]}


def _kontrollera_regelbok(data, kontoplan, momssatser, matchningsformat, var):
    """Kontrollerar hela regelboken och returnerar den som ett nytt objekt i den form kärnan använder."""
    konton, matchningsregler = _konfigurationen(kontoplan, momssatser, matchningsformat)
    _inga_dolda_tecken_i_json(data, var, _REGELBOK)
    _objekt(data, "filen", var)
    _kontrollera_nycklar(data, REGELBOK_NYCKLAR, REGELBOK_VALFRIA_NYCKLAR, var, _REGELBOK)
    if "anteckning" in data:
        _text_i_json(data["anteckning"], "'anteckning'", var, _REGELBOK)
    granser = _kontrollera_granser(data["granser"], var)
    # Saknas nyckeln är listan tom (Hugos beslut 2026-10-26).
    agare = _kontrollera_agare_och_narstaende(data.get("agare_och_narstaende", []), var)
    return {
        "foretag": _text_i_json(data["foretag"], "'foretag'", var, _REGELBOK),
        "version": _heltal_i_json(data["version"], "'version'", 1, _HOGSTA_TAL, var, _REGELBOK),
        "godkand": _kontrollera_godkand(data["godkand"], var),
        "granser": granser,
        "k9": _kontrollera_k9(data["k9"], var),
        "oppettider": _kontrollera_oppettider(data["oppettider"], var),
        "agare_och_narstaende": agare,
        "regler": _kontrollera_regelbokens_regler(data["regler"], granser, agare, konton, momssatser, matchningsregler,
                                                  var),
    }


def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor blir tupler."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, list):
        return tuple(_frys(del_) for del_ in varde)
    return varde


def _kopia(varde):
    """En vanlig kopia av ett fryst värde, som anroparen får ändra utan att regelboken ändras."""
    if isinstance(varde, MappingProxyType):
        return {nyckel: _kopia(del_) for nyckel, del_ in varde.items()}
    if isinstance(varde, tuple):
        return [_kopia(del_) for del_ in varde]
    return varde


# Nyckeln som bara las_regelbok har. Utan den går det inte att skapa en Regelbok som inte har gått
# igenom kontrollerna. Ett test (test_inga_genvagar.py) stoppar annan kärnkod från att använda den.
_REGELBOKSNYCKEL = object()


class Regelbok:
    """Ett företags regelbok, från las_regelbok. Kan bara skapas där och kan inte ändras."""

    __slots__ = ("_kontrollsumma", "_regelboken")

    def __init__(self, nyckel, kontrollsumma, regelboken):
        if nyckel is not _REGELBOKSNYCKEL:
            raise RegelbokFel("En Regelbok kan bara skapas av las_regelbok, som kör alla kontroller först.")
        # object.__setattr__ behövs eftersom vanlig tilldelning är spärrad nedan.
        object.__setattr__(self, "_kontrollsumma", kontrollsumma)
        object.__setattr__(self, "_regelboken", _frys(regelboken))

    def __setattr__(self, namn, varde):
        raise AttributeError("En Regelbok kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("En Regelbok kan inte ändras.")

    @property
    def kontrollsumma(self):
        """SHA-256 av regelbokens fil, som text med 64 tecken. Ändras om ett enda tecken i filen ändras."""
        return self._kontrollsumma

    @property
    def foretag(self):
        return self._regelboken["foretag"]

    @property
    def version(self):
        return self._regelboken["version"]

    @property
    def godkand(self):
        return _kopia(self._regelboken["godkand"])

    @property
    def granser(self):
        return _kopia(self._regelboken["granser"])

    @property
    def k9(self):
        return _kopia(self._regelboken["k9"])

    @property
    def oppettider(self):
        return _kopia(self._regelboken["oppettider"])

    @property
    def agare_och_narstaende(self):
        """Motparterna som är ägare eller närstående, som de står i filen. En tom lista om nyckeln saknas."""
        return _kopia(self._regelboken["agare_och_narstaende"])

    @property
    def regler(self):
        """Reglerna i filens ordning, som nya kopior."""
        return _kopia(self._regelboken["regler"])

    def ar_agare_eller_narstaende(self, motpart):
        """True om motparten står i 'agare_och_narstaende', annars False (K7).

        Motparten jämförs efter normaliseringen (normalisering.py), som i K4 och regel_for_underlag.
        """
        if not isinstance(motpart, str):
            raise RegelbokFel("Uppslaget i regelboken: motpart ska vara text, inte " + _json_typ(motpart) + ".")
        sokt = normalisera_for_jamforelse(motpart)
        return any(normalisera_for_jamforelse(namn) == sokt for namn in self._regelboken["agare_och_narstaende"])

    def _regel_for(self, galler, datum):
        """Regeln som gäller samma sak på datumet, som en ny kopia, eller None om ingen regel passar."""
        datum = _datumtext(datum, "datumet", "Uppslaget i regelboken", _REGELBOK)
        for nyckel, varde in galler.items():
            if not isinstance(varde, str):
                raise RegelbokFel("Uppslaget i regelboken: " + nyckel + " ska vara text, inte " + _json_typ(varde) + ".")
        sokt = _vad_regeln_galler(galler)
        for regel in self._regelboken["regler"]:
            villkor = regel["villkor"]
            if (_vad_regeln_galler(regel["galler"]) == sokt and villkor["giltig_fran"] <= datum
                    and (villkor["giltig_till"] is None or datum <= villkor["giltig_till"])):
                return _kopia(regel)
        return None

    def regel_for_underlag(self, typ, motpart, datum):
        """Regeln för ett underlag med typen och motparten på datumet, eller None (ny motpart, ett ärende).

        Motparten jämförs efter normaliseringen (normalisering.py), som i K4.
        """
        return self._regel_for({"kalla": "underlag", "typ": typ, "motpart": motpart}, datum)

    def regel_for_z_rapport(self, kassaregister, datum):
        """Regeln för en Z-rapport från kassaregistret på datumet, eller None."""
        return self._regel_for({"kalla": "z_rapport", "kassaregister": kassaregister}, datum)

    def regel_for_bankrad(self, matchningsregel, datum):
        """Regeln för en bankrad som hör till regeln matchningsregel i matchning.json, på datumet, eller None."""
        return self._regel_for({"kalla": "bankrad", "matchningsregel": matchningsregel}, datum)

    def __repr__(self):
        return ("Regelbok(" + repr(self._regelboken["foretag"]) + ", version " + str(self._regelboken["version"]) + ", "
                + str(len(self._regelboken["regler"])) + " regler, kontrollsumma " + self._kontrollsumma[:12] + "…)")


def las_regelbok(sokvag, kontoplan, momssatser, matchningsformat):
    """Läser och kontrollerar ett företags regelbok.json. Returnerar en Regelbok, annars RegelbokFel.

    kontoplan ska komma från las_kontoplan, momssatser från las_momssatser och matchningsformat från
    ladda_matchningsformat (det kontrolleras igen här). Kontrollsumman räknas på exakt de bytes som tolkas.
    """
    data, var = _las_jsonfil(sokvag, _REGELBOK)
    kontrollsumma = hashlib.sha256(data).hexdigest()
    innehall = _tolka_json(data, var, _REGELBOK)
    return Regelbok(_REGELBOKSNYCKEL, kontrollsumma, _kontrollera_regelbok(innehall, kontoplan, momssatser,
                                                                          matchningsformat, var))
