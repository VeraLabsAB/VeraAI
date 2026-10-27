"""Tester för matchningen av bankrader mot underlag (matcha_bank.py, K3).

Testdatan är SYNTETISK (Syntet Testbutik AB, 2025-Q1). Rätt svar står i facit.json. De små
bankfilerna och underlagen nedan är påhittade och skrivs i en tillfällig mapp för varje test. De
läses alltid med las_bankfil och las_underlagsperiod, så att matchningen får samma sorts indata
som i drift. Matchningsformatet får matchningen bara genom en regelbok från las_regelbok
(granskning 8, N3). För de små fallen skrivs formatet och en regelbok i en tillfällig mapp
(regelbok_for).
"""

import copy
import datetime as dt
import itertools
import json
import random
import sys
import tempfile
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"
FORETAG = AGENT / "foretag" / "syntet-testbutik"

sys.path.insert(0, str(AGENT / "scripts"))

import matcha_bank  # noqa: E402
from las_bank import Bankperiod, BankfilFel, ladda_bankformat, las_bankfil, sla_ihop_bankperioder  # noqa: E402
from las_kassa import normalisera_kassaregister  # noqa: E402
from las_kontoplan import las_kontoplan  # noqa: E402
from las_matchningsformat import (  # noqa: E402
    MatchningsformatFel, kontrollera_matchningsformat, ladda_matchningsformat, las_matchningsformat,
)
from las_momssatser import las_momssatser  # noqa: E402
from las_regelbok import Regelbok, RegelbokFel, las_regelbok  # noqa: E402
from las_underlag import UnderlagFilFel, Underlagsperiod, las_underlagsperiod  # noqa: E402
from matcha_bank import MatchningFel, Matchningsresultat, matcha_period  # noqa: E402

BANKFORMAT = ladda_bankformat(FORETAG / "bankformat.json")
MATCHNINGSFORMAT = ladda_matchningsformat(FORETAG / "matchning.json")
KONTOPLAN = las_kontoplan(FORETAG / "kontoplan.json")
MOMSSATSER = las_momssatser(FORETAG / "momssatser.json")
# Testbutikens egen regelbok, kontrollerad mot testbutikens matchningsformat, för testdatan.
REGELBOK = las_regelbok(FORETAG / "regelbok.json", KONTOPLAN, MOMSSATSER, las_matchningsformat(FORETAG / "matchning.json"))
GRUPPER_FOR_BANKRADER = ("matchningar", "arenden", "kraver_inte_underlag", "vantande")

# Osynliga tecken byggs med chr(), så att de syns i koden (test_inga_dolda_tecken.py).
OSYNLIGT_MELLANSLAG = chr(0x200B)
HOGER_TILL_VANSTER = chr(0x202E)
# Förväxlingstecken (J1), också med chr(), så att det syns vilket tecken som används.
BINDESTRECK = chr(0x2010)
TANKSTRECK = chr(0x2013)
MINUSTECKEN = chr(0x2212)
KYRILLISKT_A = chr(0x0410)
KYRILLISKT_GHE = chr(0x0492)  # liknar F


def facit():
    return json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))


def planterat(typ):
    traffar = [fel for fel in facit()["planterade_fel"] if fel["typ"] == typ]
    assert len(traffar) == 1, typ
    return traffar[0]


def kr(ore):
    """Heltal i öre som i testdatans bankfiler, med punkt: -35100 -> "-351.00"."""
    return ("-" if ore < 0 else "") + str(abs(ore) // 100) + "." + str(abs(ore) % 100).zfill(2)


# --- Testdatan: hela kvartalet ---

def las_kvartalets_bankrader(mapp):
    """Januari, februari och mars med las_bankfil, i en kedja: varje månads ingående saldo är förra
    månadens utgående, som i test_las_bank.py. Saldona kommer från facit. Ger tre Bankperioder.

    Mars stoppas av K1 på den planterade raden (100,00 kr för högt saldo). Därför rättas raden i en
    kopia: saldot byts mot det rätta enligt facit. Inget annat i filen ändras.
    """
    bank = facit()["bank"]
    januari = las_bankfil(DATAMAPP / "bank_2025-01.csv", BANKFORMAT, bank["2025-01"]["ingaende_saldo_ore"],
                          bank["2025-01"]["utgaende_saldo_ore"])
    februari = las_bankfil(DATAMAPP / "bank_2025-02.csv", BANKFORMAT, januari.utgaende_saldo_ore,
                           bank["2025-02"]["utgaende_saldo_ore"])
    fel = planterat("brott_i_saldokedjan")
    rader = (DATAMAPP / fel["filnamn"]).read_text(encoding="utf-8").split("\n")
    felrad = [nummer for nummer, rad in enumerate(rader) if rad.startswith(str(fel["rad"]) + ",")]
    assert len(felrad) == 1 and rader[felrad[0]].endswith("," + kr(fel["visat_saldo_ore"]))
    rader[felrad[0]] = rader[felrad[0]][:-len(kr(fel["visat_saldo_ore"]))] + kr(fel["ratt_saldo_ore"])
    rattad = mapp / fel["filnamn"]
    rattad.write_text("\n".join(rader), encoding="utf-8")
    mars = las_bankfil(rattad, BANKFORMAT, februari.utgaende_saldo_ore, bank["2025-03"]["utgaende_saldo_ore"])
    return januari, februari, mars


@pytest.fixture(scope="module")
def kvartalet(tmp_path_factory):
    januari, februari, mars = las_kvartalets_bankrader(tmp_path_factory.mktemp("bank"))
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-01-01", "2025-03-31")
    bankperiod = sla_ihop_bankperioder([januari, februari, mars])
    return {"bankperiod": bankperiod, "rader": bankperiod.rader, "februari": februari, "period": period}


def bankrad_utan_underlag(kvartalet):
    """Den planterade bankraden utan underlag, ur februarifilen."""
    fel = planterat("bankrad_utan_underlag")
    assert fel["manad"] == "2025-02" and fel["filnamn"] == "bank_2025-02.csv"
    rad = kvartalet["februari"].rader[fel["rad"] - 1]
    assert (rad["radnr"], rad["belopp_ore"]) == (fel["rad"], fel["belopp_ore"]) == (85, -35100)
    assert rad["beskrivning"] == "KORTKOP BUTIK-FORBRUKNING" and rad["transaktionsdag"] == "2025-02-18"
    return rad


def test_kvartalet_ger_exakt_det_planterade_felet_som_saknat_underlag(kvartalet):
    rad = bankrad_utan_underlag(kvartalet)
    # Mer än 7 dagar efter alla bankrader i kvartalet.
    resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK,"2025-04-30")
    assert len(resultat.arenden) == 1
    arende = resultat.arenden[0]
    assert (arende["kontroll"], arende["typ"], arende["kandidater"]) == ("K3", "saknat underlag", ())
    assert dict(arende["bankrad"]) == rad
    assert arende["bankrad"]["kalla_fil"] == kvartalet["februari"].rader[0]["kalla_fil"]  # februarifilen
    assert resultat.vantande == ()
    # Facit säger att felet fångas av K3.
    assert planterat("bankrad_utan_underlag")["kontroll"] == arende["kontroll"]


def februari_till_och_med_rad(kvartalet, mapp, radnr):
    """Februarifilen fram till och med raden radnr, som om bedömningen görs innan resten av månaden
    finns på banken. Läses med las_bankfil: ingående saldo som februari, utgående saldo efter raden."""
    rader = (DATAMAPP / "bank_2025-02.csv").read_text(encoding="utf-8").split("\n")
    assert rader[radnr].startswith(str(radnr) + ",") and rader[radnr + 1].startswith(str(radnr + 1) + ",")
    fil = mapp / "bank_2025-02_del.csv"
    fil.write_text("\n".join(rader[:radnr + 1]) + "\n", encoding="utf-8")
    februari = kvartalet["februari"]
    return las_bankfil(fil, BANKFORMAT, februari.ingaende_saldo_ore, februari.rader[radnr - 1]["saldo_efter_ore"])


def test_kvartalet_fore_sju_dagar_ger_inget_arende_bara_att_raden_vantar(kvartalet, tmp_path):
    rad = bankrad_utan_underlag(kvartalet)
    # Ett bedömningsdatum före en bankrad stoppas (J9). Därför används februari fram till och med
    # rad 85, så som banken såg ut då. Den sista transaktionsdagen i den delen är 2025-02-19.
    del_ = februari_till_och_med_rad(kvartalet, tmp_path, rad["radnr"])
    assert max(r["transaktionsdag"] for r in del_.rader) == "2025-02-19"
    # 7 dagar efter transaktionsdagen 2025-02-18: inte mer än 7 dagar, så raden väntar.
    for dag in ("2025-02-19", "2025-02-20", "2025-02-25"):
        resultat = matcha_period(del_, kvartalet["period"], REGELBOK,dag)
        assert resultat.arenden == (), dag
        # Samma rad (id:t beror bara på radens innehåll), men ur en annan fil, så kalla_fil skiljer.
        assert [(post["bankrad"]["id"], post["bankrad"]["radnr"], post["arende_efter"]) for post in resultat.vantande
                ] == [(rad["id"], 85, "2025-02-25")]
    # Dagen efter blir den ett ärende.
    resultat = matcha_period(del_, kvartalet["period"], REGELBOK,"2025-02-26")
    assert [(a["typ"], a["bankrad"]["id"]) for a in resultat.arenden] == [("saknat underlag", rad["id"])]
    assert resultat.vantande == ()
    # Hela kvartalet med samma bedömningsdatum stoppas: där finns bankrader efter 2025-02-26.
    with pytest.raises(MatchningFel, match="^Bedömningsdatumet 2025-02-26 ligger före transaktionsdagen"):
        matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK,"2025-02-26")


def test_dubbletten_kommer_fran_k4_och_inte_fran_matchningen(kvartalet):
    fel = planterat("dubblett_leverantorsfaktura")
    period = kvartalet["period"]
    assert [(a["kontroll"], a["id"]) for a in period.arenden] == [("K4", fel["id"])]
    resultat = matcha_period(kvartalet["bankperiod"], period, REGELBOK,"2025-04-30")
    alla_id = json.dumps([list(map(dict, grupp)) for grupp in resultat], default=dict)
    assert fel["id"] not in alla_id  # dubbletten finns inte i matchningen alls
    # Originalet matchas med den enda betalningen.
    original = [m for m in resultat.matchningar if m["underlag"]["id"] == fel["original_id"]]
    assert len(original) == 1 and original[0]["bankrad"]["referens"] == original[0]["underlag"]["fakturanummer"]
    assert all(a["typ"] != "tvetydig" for a in resultat.arenden)


def test_kvartalets_matchningar_ar_ratt(kvartalet):
    resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK,"2025-04-30")
    leverantorsbetalningar = [rad for rad in kvartalet["rader"] if rad["referens"].startswith("SYNT-")]
    kortkop = [rad for rad in kvartalet["rader"] if rad["referens"].startswith("KORTKOP-")]
    assert (len(leverantorsbetalningar), len(kortkop)) == (16, 8)
    assert len(resultat.matchningar) == 16 + 7  # alla kortköp utom det planterade
    for matchning in resultat.matchningar:
        rad, post = matchning["bankrad"], matchning["underlag"]
        assert rad["belopp_ore"] == -post["belopp_ore"]
        if post["typ"] == "leverantorsfaktura":
            assert rad["referens"] == post["fakturanummer"] and rad["beskrivning"] == post["motpart"]
        else:
            assert rad["beskrivning"] == "KORTKOP " + post["motpart"] and rad["transaktionsdag"] == post["datum"]
    # Raderna som inte kräver underlag: kortinlösen, Swish, kontantinsättningar och bankens avgifter.
    regler = {}
    for post in resultat.kraver_inte_underlag:
        regler[post["regel"]] = regler.get(post["regel"], 0) + 1
    forvantat = {regel: len([rad for rad in kvartalet["rader"] if rad["referens"].startswith(prefix)])
                 for regel, prefix in [("kortinlosen", "AVR-"), ("swish", "SWISH-"), ("kontantinsattning", "INS-"),
                                       ("bankavgift", "AVG-")]}
    assert regler == forvantat == {"kortinlosen": 74, "swish": 278, "kontantinsattning": 13, "bankavgift": 6}
    assert sum(regler.values()) == 395 - 16 - 8  # alla rader utom leverantörsbetalningarna och kortköpen
    # Oavstämda: fakturorna som förfaller efter 31 mars. Ingen bankrad betalar dem.
    referenser = {rad["referens"] for rad in kvartalet["rader"]}
    assert resultat.oavstamda_underlag
    for post in resultat.oavstamda_underlag:
        assert post["typ"] == "leverantorsfaktura" and post["fakturanummer"] not in referenser
        assert dt.date.fromisoformat(post["datum"]) + dt.timedelta(days=30) > dt.date(2025, 3, 31)


def kontrollera_grupperna(resultat, bankperiod, period):
    """Varje bankrad i bankperioden finns i exakt en grupp. Varje underlag i perioden finns i exakt en
    matchning eller bland de oavstämda, och aldrig i två matchningar."""
    id_per_grupp = [post["bankrad"]["id"] for grupp in GRUPPER_FOR_BANKRADER for post in getattr(resultat, grupp)]
    assert sorted(id_per_grupp) == sorted(rad["id"] for rad in bankperiod.rader)
    matchade = [m["underlag"]["id"] for m in resultat.matchningar]
    assert len(matchade) == len(set(matchade))
    oavstamda = [post["id"] for post in resultat.oavstamda_underlag]
    assert sorted(matchade + oavstamda) == sorted(post["id"] for post in period.underlag)


def test_varje_bankrad_i_testdatan_finns_i_exakt_en_grupp(kvartalet):
    assert len(kvartalet["rader"]) == sum(manad["antal_rader"] for manad in facit()["bank"].values()) == 395
    # Bedömningsdatumen ligger på eller efter den sista bankraden (2025-03-31), annars stoppas de (J9).
    for dag in ("2025-03-31", "2025-04-07", "2025-04-08", "2025-04-30", "9999-12-31"):
        resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK,dag)
        kontrollera_grupperna(resultat, kvartalet["bankperiod"], kvartalet["period"])


def test_en_manad_i_taget_ger_samma_planterade_fel(kvartalet):
    # Februari för sig ger samma ärende. Underlagen från januari behövs, eftersom januaris fakturor
    # betalas i februari. Utan dem blir de bankraderna ärenden (nästa test).
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-01-01", "2025-02-28")
    resultat = matcha_period(kvartalet["februari"], period, REGELBOK,"2025-03-31")
    assert [(a["typ"], a["bankrad"]["radnr"]) for a in resultat.arenden] == [("saknat underlag", 85)]


def test_utan_underlagen_fran_januari_blir_februaris_betalningar_arenden(kvartalet):
    # Skydd: testet ovan prövar verkligen något. Betalningarna av januaris fakturor saknar då underlag.
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-02-01", "2025-02-28")
    resultat = matcha_period(kvartalet["februari"], period, REGELBOK,"2025-03-31")
    saknade = [a["bankrad"] for a in resultat.arenden if a["typ"] == "saknat underlag"]
    assert 85 in [rad["radnr"] for rad in saknade]
    assert [rad for rad in saknade if rad["radnr"] != 85]
    assert all(rad["referens"].startswith("SYNT-") for rad in saknade if rad["radnr"] != 85)


# --- Små påhittade fall i en tillfällig mapp ---

FORMAT = {
    "kraver_inte_underlag": [
        {"namn": "insattning", "riktning": "in", "referens_borjar_med": "IN-"},
        {"namn": "avgift", "riktning": "ut", "beskrivning_borjar_med": "AVGIFT", "hogst_belopp_ore": 200},
        {"namn": "kort", "riktning": "in", "referens_borjar_med": "K-", "beskrivning_borjar_med": "KORT IN"},
    ],
    "tidsfonster_dagar": {"leverantorsfaktura": 30, "kvitto": 2},
    "saknat_underlag_efter_dagar": 7,
}
RUBRIK = "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo"

# En tillfällig mapp för regelbok_for. Den tas bort när testerna är klara.
_REGELBOKSMAPP = tempfile.TemporaryDirectory(prefix="matcha-bank-")
_NUMMER = itertools.count()
_REGELBOCKER = {}


def regelbok_for(format_, agare=("AGARE-1",)):
    """En Regelbok från las_regelbok, kontrollerad mot matchningsformatet format_.

    Formatet skrivs som matchning.json och läses med las_matchningsformat. Regelboken är testbutikens,
    utan dess regler för bankrader (de pekar på testbutikens regler i matchningsformatet), och med
    agare som ägare och närstående. Varje format läses en gång. Ett trasigt format stoppas av
    las_matchningsformat eller las_regelbok, som i drift. Värden som inte finns i JSON (till exempel
    bytes) skrivs som text, så att de fortfarande är fel."""
    nyckel = json.dumps([format_, list(agare)], ensure_ascii=False, default=repr)
    if nyckel not in _REGELBOCKER:
        mapp = Path(_REGELBOKSMAPP.name) / str(next(_NUMMER))
        mapp.mkdir()
        (mapp / "matchning.json").write_text(json.dumps(format_, ensure_ascii=False, default=repr), encoding="utf-8")
        data = json.loads((FORETAG / "regelbok.json").read_text(encoding="utf-8"))
        data["regler"] = [regel for regel in data["regler"] if regel["galler"]["kalla"] != "bankrad"]
        data["agare_och_narstaende"] = list(agare)
        (mapp / "regelbok.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        _REGELBOCKER[nyckel] = las_regelbok(mapp / "regelbok.json", KONTOPLAN, MOMSSATSER,
                                            las_matchningsformat(mapp / "matchning.json"))
    return _REGELBOCKER[nyckel]


FORMATETS_REGELBOK = regelbok_for(FORMAT)


def bankrader(mapp, *rader, namn="bank.csv", ingaende=0):
    """Skriver en bankfil och läser den med las_bankfil, som ger en Bankperiod. Varje rad är
    (referens, beskrivning, belopp_ore, transaktionsdag) eller med bokforingsdag sist. Saldot börjar
    på ingaende."""
    saldo, text = ingaende, [RUBRIK]
    for nummer, rad in enumerate(rader, start=1):
        referens, beskrivning, belopp, transaktionsdag = rad[:4]
        bokforingsdag = rad[4] if len(rad) > 4 else transaktionsdag
        saldo += belopp
        text.append(",".join([str(nummer), bokforingsdag, transaktionsdag, referens, beskrivning, kr(belopp),
                              kr(saldo)]))
    fil = mapp / namn
    fil.write_text("\n".join(text) + "\n", encoding="utf-8")
    return las_bankfil(fil, BANKFORMAT, ingaende, saldo)


def underlag(**andrat):
    """Ett felfritt underlag, med de ändringar som anges. Beloppet utan moms räknas om efter belopp_ore."""
    data = {"id": "U-1", "typ": "leverantorsfaktura", "datum": "2025-01-10", "motpart": "LEV-A",
            "fakturanummer": "F-1", "belopp_ore": 12500, "moms": None, "flaggor": []}
    data.update(andrat)
    if data["moms"] is None:
        data["moms"] = [{"momssats": 0, "underlag_ore": data["belopp_ore"], "moms_ore": 0}]
    return data


def period(mapp, *poster):
    """Skriver underlagen i en egen mapp och läser dem med las_underlagsperiod."""
    mapp = mapp / "underlag"
    mapp.mkdir(exist_ok=True)
    for post in poster:
        (mapp / (post["id"] + ".json")).write_text(json.dumps(post, ensure_ascii=False), encoding="utf-8")
    return las_underlagsperiod(mapp, "0001-01-01", "9999-12-31")


def matcha(rader, underlagen, bedomning="2025-12-31", format_=None, agare=("AGARE-1",)):
    resultat = matcha_period(rader, underlagen, regelbok_for(FORMAT if format_ is None else format_, agare), bedomning)
    kontrollera_grupperna(resultat, rader, underlagen)
    return resultat


def sammanfattning(resultat):
    """Resultatet kort: vilka bankrader (radnr) som hamnade var, och med vilket underlag eller vilken regel."""
    return {
        "matchningar": [(m["bankrad"]["radnr"], m["underlag"]["id"]) for m in resultat.matchningar],
        "arenden": [(a["bankrad"]["radnr"], a["typ"], a["kandidater"]) for a in resultat.arenden],
        "oavstamda": [post["id"] for post in resultat.oavstamda_underlag],
        "kraver_inte": [(post["bankrad"]["radnr"], post["regel"]) for post in resultat.kraver_inte_underlag],
        "vantande": [(post["bankrad"]["radnr"], post["arende_efter"]) for post in resultat.vantande],
    }


def tomt(**andrat):
    resultat = {"matchningar": [], "arenden": [], "oavstamda": [], "kraver_inte": [], "vantande": []}
    resultat.update(andrat)
    return resultat


def test_samma_belopp_motpart_och_datum_matchas(tmp_path):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(matchningar=[(1, "U-1")])


@pytest.mark.parametrize("belopp", [-12499, -12501, -1250000, 12500])
def test_annat_belopp_eller_fel_tecken_matchas_inte(tmp_path, belopp):
    # Bankradens belopp ska vara exakt underlagets, med minustecken (pengar ut).
    rader = bankrader(tmp_path, ("F-1", "LEV-A", belopp, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(
        arenden=[(1, "saknat underlag", ())], oavstamda=["U-1"])


@pytest.mark.parametrize("referens, beskrivning, motpart", [
    ("F-1", "LEV-A", "LEV-A"),
    ("LEV-A", "BETALNING", "LEV-A"),                      # motparten i referensen
    ("F-1", "KORTKOP LEV-A", "LEV-A"),                    # ett ord av flera
    ("F-1", "lev-a", "LEV-A"),                            # stora och små bokstäver
    ("F-1", "LEV-A", "Lev-A" + OSYNLIGT_MELLANSLAG),      # osynligt tecken
    ("F-1", "KORTKOP MOTPART A", "Motpart A"),            # två ord
    ("F-1", "KORTKOP MOTPARTA", "Motpart A"),             # blanksteg räknas inte
    ("F-1", "KORTKOP  MOTPART   A  X", "MOTPART A"),      # flera blanksteg
])
def test_motparten_i_bankradens_text_matchas(tmp_path, referens, beskrivning, motpart):
    rader = bankrader(tmp_path, (referens, beskrivning, -12500, "2025-01-20"))
    resultat = matcha(rader, period(tmp_path, underlag(motpart=motpart)))
    assert sammanfattning(resultat) == tomt(matchningar=[(1, "U-1")])


@pytest.mark.parametrize("referens, beskrivning", [
    ("F-1", "LEV-AB"),              # en annan motpart som börjar likadant, som LEV-TE och LEV-TELE
    ("F-1", "XLEV-A"),              # en annan motpart som slutar likadant
    ("F-1", "LEV"),                 # bara en del av namnet
    ("F-1", "BETALNING"),           # ingen motpart alls
    ("LEV-A1", "BETALNING"),        # ett annat ord i referensen
])
def test_motpart_som_inte_star_som_hela_ord_matchas_inte(tmp_path, referens, beskrivning):
    rader = bankrader(tmp_path, (referens, beskrivning, -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(
        arenden=[(1, "saknat underlag", ())], oavstamda=["U-1"])


@pytest.mark.parametrize("typ, dag, matchas", [
    ("leverantorsfaktura", "2025-01-10", True),    # samma dag som underlaget
    ("leverantorsfaktura", "2025-02-09", True),    # sista dagen i tidsfönstret, 30 dagar efter
    ("leverantorsfaktura", "2025-02-10", False),   # en dag för sent
    ("leverantorsfaktura", "2025-01-09", False),   # dagen före underlaget
    ("kvitto", "2025-01-12", True),                # kvittots tidsfönster är 2 dagar
    ("kvitto", "2025-01-13", False),
])
def test_tidsfonstret_per_underlagstyp(tmp_path, typ, dag, matchas):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, dag))
    resultat = sammanfattning(matcha(rader, period(tmp_path, underlag(typ=typ)), "2025-12-31"))
    if matchas:
        assert resultat == tomt(matchningar=[(1, "U-1")])
    else:
        assert resultat == tomt(arenden=[(1, "saknat underlag", ())], oavstamda=["U-1"])


def test_tidsfonstret_galler_transaktionsdagen_inte_bokforingsdagen(tmp_path):
    # Kortköpet gjordes dagen för kvittot och bokfördes fyra dagar senare, utanför kvittots tidsfönster.
    rader = bankrader(tmp_path, ("K-1", "KORTKOP LEV-A", -12500, "2025-01-10", "2025-01-14"),
                      ("K-2", "KORTKOP LEV-B", -500, "2025-01-14", "2025-01-10"))
    resultat = matcha(rader, period(tmp_path, underlag(typ="kvitto"),
                                    underlag(id="U-2", typ="kvitto", motpart="LEV-B", belopp_ore=500)))
    assert sammanfattning(resultat) == tomt(matchningar=[(1, "U-1")], arenden=[(2, "saknat underlag", ())],
                                            oavstamda=["U-2"])


def test_saknat_underlag_blir_arende_forst_efter_antalet_dagar_i_formatet(tmp_path):
    rader = bankrader(tmp_path, ("X-1", "OKAND", -100, "2025-03-01"))
    underlagen = period(tmp_path)
    for dag in ("2025-03-01", "2025-03-08"):  # 2025-03-08 är 7 dagar efter
        assert sammanfattning(matcha(rader, underlagen, dag)) == tomt(vantande=[(1, "2025-03-08")]), dag
    assert sammanfattning(matcha(rader, underlagen, "2025-03-09")) == tomt(arenden=[(1, "saknat underlag", ())])
    # Med 0 dagar i formatet blir raden ett ärende redan dagen efter.
    noll = {**FORMAT, "saknat_underlag_efter_dagar": 0}
    assert sammanfattning(matcha(rader, underlagen, "2025-03-01", noll)) == tomt(vantande=[(1, "2025-03-01")])
    assert sammanfattning(matcha(rader, underlagen, "2025-03-02", noll)) == tomt(
        arenden=[(1, "saknat underlag", ())])


def test_saknat_underlag_text_namner_dagarna_men_inga_texter_ur_bankraden(tmp_path):
    rader = bankrader(tmp_path, ("X-1", "GOR SA HAR", -100, "2025-03-01"))
    arende = matcha(rader, period(tmp_path)).arenden[0]
    assert arende["text"] == ("Inget underlag med samma belopp, motpart och datum har hittats, och det har gått"
                              " mer än 7 dagar sedan transaktionsdagen.")
    assert arende["bankrad"]["beskrivning"] == "GOR SA HAR"  # texten följer med som data, oförändrad


def test_sista_dagen_som_finns_ger_inget_fel(tmp_path):
    # 9999-12-31 plus 7 dagar finns inte som datum. Raden väntar till den sista dagen som finns.
    rader = bankrader(tmp_path, ("X-1", "OKAND", -100, "9999-12-31"))
    assert sammanfattning(matcha(rader, period(tmp_path), "9999-12-31")) == tomt(vantande=[(1, "9999-12-31")])
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "9999-12-31"))
    resultat = matcha(rader, period(tmp_path, underlag(datum="9999-12-30")), "9999-12-31")
    assert sammanfattning(resultat) == tomt(matchningar=[(1, "U-1")])


def test_tvetydigt_tva_lika_underlag_och_en_bankrad(tmp_path):
    rader = bankrader(tmp_path, ("BETALNING", "LEV-A", -12500, "2025-01-20"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2"))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(
        arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])
    arende = matcha(rader, underlagen).arenden[0]
    assert arende["kontroll"] == "K3" and "En människa behöver avgöra" in arende["text"]


def test_fakturanumret_avgor_nar_flera_underlag_passar(tmp_path):
    # Som telefonfakturorna i testdatan: samma belopp varje månad, och betalningen ligger i båda
    # fakturornas tidsfönster. Fakturanumret i referensen säger vilken som betalas.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"),
                        underlag(id="U-2", fakturanummer="F-1002", datum="2025-02-09"))
    for referens, resultat in [
        ("F-1002", tomt(matchningar=[(1, "U-2")], oavstamda=["U-1"])),
        ("f-1002", tomt(matchningar=[(1, "U-2")], oavstamda=["U-1"])),        # stora och små bokstäver
        ("F-1001", tomt(matchningar=[(1, "U-1")], oavstamda=["U-2"])),
        ("F-1002X", tomt(arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])),  # inte hela ord
        ("F-1001 F-1002", tomt(arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])),
    ]:
        rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-02-09"))
        assert sammanfattning(matcha(rader, underlagen)) == resultat, referens


def test_fakturanumret_avgor_bara_nar_det_pekar_ut_exakt_ett_underlag(tmp_path):
    # Tre kandidater, och två fakturanummer står i texten. Fakturanumret avgör inte, och människan
    # får se alla tre kandidaterna i ärendet.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"), underlag(id="U-2", fakturanummer="F-1002"),
                        underlag(id="U-3", fakturanummer="F-1003"))
    rader = bankrader(tmp_path, ("F-1001 F-1002", "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(
        arenden=[(1, "tvetydig", ("U-1", "U-2", "U-3"))], oavstamda=["U-1", "U-2", "U-3"])


# --- J2: när fakturanumret får avgöra ---

def tva_fakturor(tmp_path, forsta, andra, motpart="LEV-A"):
    """Två fakturor från samma motpart med samma belopp, som båda passar en betalning 2025-01-20.

    De har olika datum (2025-01-10 och 2025-01-11), eftersom fakturanumret aldrig avgör mellan
    underlag med samma datum (L1, granskning 6).
    """
    return period(tmp_path, underlag(fakturanummer=forsta, motpart=motpart),
                  underlag(id="U-2", fakturanummer=andra, motpart=motpart, datum="2025-01-11"))


TVETYDIG = tomt(arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])


def betalar(id_):
    """Resultatet när bankraden matchas med underlaget id_ och det andra är oavstämt."""
    return tomt(matchningar=[(1, id_)], oavstamda=[{"U-1": "U-2", "U-2": "U-1"}[id_]])


@pytest.mark.parametrize("referens, beskrivning, forvantat", [
    ("F-1001", "LEV-A", "U-1"),
    ("BET F-1001", "LEV-A", "U-1"),                    # ett ord av flera
    ("f" + TANKSTRECK + "1001", "LEV-A", "U-1"),       # annat bindestreck och små bokstäver (J1)
    ("F" + MINUSTECKEN + "1001", "LEV-A", "U-1"),
    ("BETALNING", "LEV-A F-1002", "U-2"),              # i beskrivningen (J8)
    ("F-1001X", "LEV-A", None),                        # en del av ett längre ord
    ("XF-1001", "LEV-A", None),
    ("F-10011", "LEV-A", None),                        # en del av ett längre nummer
    ("F-1001/2", "LEV-A", None),
    ("F-1001.", "LEV-A", None),
    ("F - 1001", "LEV-A", None),                       # uppdelat på flera ord
    ("F-10 01", "LEV-A", None),
])
def test_fakturanumret_avgor_bara_som_ett_helt_ord(tmp_path, referens, beskrivning, forvantat):
    # J2: fakturanumret ska stå som ett eget ord i bankradens referens eller beskrivning, inte som en
    # del av ett längre ord eller nummer och inte uppdelat på flera ord.
    underlagen = tva_fakturor(tmp_path, "F-1001", "F-1002")
    rader = bankrader(tmp_path, (referens, beskrivning, -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == (betalar(forvantat) if forvantat else TVETYDIG)


def test_fakturanumret_i_beskrivningen_avgor(tmp_path):
    # J8: förut prövade inget test att fakturanumret också söks i beskrivningen.
    underlagen = tva_fakturor(tmp_path, "F-1001", "F-1002")
    for beskrivning, forvantat in [("LEV-A F-1002", "U-2"), ("F-1001 LEV-A", "U-1"), ("LEV-A", None)]:
        rader = bankrader(tmp_path, ("BETALNING 5555", beskrivning, -12500, "2025-01-20"))
        assert sammanfattning(matcha(rader, underlagen)) == (betalar(forvantat) if forvantat else TVETYDIG), beskrivning


def test_kort_fakturanummer_avgor_inte(tmp_path):
    # J2, granskarens fall: fakturorna 10 och 11, och bankradens beskrivning råkar innehålla "10".
    underlagen = tva_fakturor(tmp_path, "10", "11")
    rader = bankrader(tmp_path, ("BETALNING", "LEV-A 10 ST", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == TVETYDIG


@pytest.mark.parametrize("forsta, andra, forvantat", [
    ("F-12", "F-13", None),        # fyra tecken: avgör inte
    ("F-123", "F-124", "U-1"),     # fem tecken: avgör
    ("F" + chr(0x00AD) + "-12", "F-13", None),  # ett osynligt tecken räknas inte
])
def test_fakturanumret_ska_ha_minst_fem_tecken(tmp_path, forsta, andra, forvantat):
    underlagen = tva_fakturor(tmp_path, forsta, andra)
    rader = bankrader(tmp_path, (forsta, "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == (betalar(forvantat) if forvantat else TVETYDIG)


@pytest.mark.parametrize("forsta, motpart, forvantat", [
    ("LEV-A", "LEV-A", None),                          # fakturanumret är motpartens namn (granskarens fall)
    ("V-ALFA", "LEV-ALFA", None),                      # en del av motpartens namn
    ("lev" + TANKSTRECK + "alfa", "LEV-ALFA", None),   # samma som namnet efter normaliseringen
    ("V-BETA", "LEV-ALFA", "U-1"),                     # skydd: ett annat ord avgör
])
def test_fakturanummer_som_ar_motpartens_namn_avgor_inte(tmp_path, forsta, motpart, forvantat):
    # J2: motpartens namn står alltid i bankradens text, så ett fakturanummer som är (en del av)
    # namnet säger inget om vilken faktura som betalas.
    underlagen = tva_fakturor(tmp_path, forsta, "F-2002", motpart=motpart)
    rader = bankrader(tmp_path, (forsta, motpart, -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == (betalar(forvantat) if forvantat else TVETYDIG)


@pytest.mark.parametrize("forsta, andra, referens, forvantat", [
    ("4711", "ABC-DE-4711", "ABC DE 4711", None),        # granskarens fall
    ("DE-4711", "ABC-DE-4711", "BET DE-4711", None),     # en del av det andra numret
    ("DE-4711", "ABC-DE-4711", "ABC-DE-4711", "U-2"),    # det längre numret avgör
    ("DE-4711", "XY-4712", "BET DE-4711", "U-1"),        # skydd: inte en del av det andra
])
def test_fakturanummer_som_ar_en_del_av_ett_annat_avgor_inte(tmp_path, forsta, andra, referens, forvantat):
    # J2: ett nummer som står inuti en annan kandidats nummer kan vara en del av det numret.
    underlagen = tva_fakturor(tmp_path, forsta, andra)
    rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == (betalar(forvantat) if forvantat else TVETYDIG)


def test_samma_fakturanummer_pa_tva_kandidater_avgor_inte(tmp_path):
    # Som K4b: samma fakturanummer två gånger, med olika datum. Numret pekar inte ut en av dem.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"),
                        underlag(id="U-2", fakturanummer="F-1001", datum="2025-01-11"))
    assert [a["kontroll"] for a in underlagen.arenden] == ["K4b"]
    rader = bankrader(tmp_path, ("F-1001", "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == TVETYDIG


# --- J1: en dubblett med förväxlingstecken blir aldrig ett oavstämt underlag utan ärende ---

@pytest.mark.parametrize("andrat, stoppas", [
    ({"fakturanummer": "F" + BINDESTRECK + "1"}, False),
    ({"fakturanummer": "F" + TANKSTRECK + "1"}, False),
    ({"fakturanummer": "F" + MINUSTECKEN + "1"}, False),
    ({"fakturanummer": " F  -  1"}, False),
    ({"fakturanummer": "F-1" + OSYNLIGT_MELLANSLAG}, False),
    ({"motpart": "LEV" + TANKSTRECK + "A"}, False),
    ({"motpart": "LEV-" + KYRILLISKT_A}, True),
    ({"fakturanummer": KYRILLISKT_GHE + "-1"}, True),
    ({"fakturanummer": "F-" + KYRILLISKT_A}, True),
], ids=["bindestreck", "tankstreck", "minustecken", "blanksteg", "osynligt", "motpart_tankstreck",
        "motpart_kyrilliskt_a", "fakturanummer_kyrilliskt", "fakturanummer_blandat"])
def test_dublett_med_forvaxlingstecken_blir_aldrig_oavstamd_utan_arende(tmp_path, andrat, stoppas):
    # J1 (hög): förut fångades dubbletten varken av K4 eller av matchningen. Fakturanummerregeln
    # matchade originalet, och dubbletten blev ett oavstämt underlag, som en obetald faktura, utan
    # något ärende. Nu blir den ett K4-ärende, eller så stoppas underlaget med ett tydligt fel.
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"))
    if stoppas:
        with pytest.raises(UnderlagFilFel, match="Underlaget 'U-2.json' stoppas: 'motpart|Underlaget 'U-2.json' stoppas: 'fakturanummer"):
            period(tmp_path, underlag(), underlag(id="U-2", **andrat))
        return
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", **andrat))
    assert [(a["kontroll"], a["id"], a["text"]) for a in underlagen.arenden] == [("K4", "U-2", "dublett av U-1")]
    resultat = matcha(rader, underlagen)
    assert sammanfattning(resultat) == tomt(matchningar=[(1, "U-1")])  # U-2 finns inte bland de oavstämda


# --- L1 och L2 (granskning 6): fakturanumret avgör inte mellan underlag med samma datum ---

L1_FAKTURANUMMER = {
    "litet_l": "F-l001", "utan_bindestreck": "F1001", "stora_o": "F-1OO1",
    "mjukt_bindestreck": "F" + chr(0x00AD) + "1001", "ogham_mellanslag": "F" + chr(0x1680) + "1001",
}
# Motparter som ser ut som "LEV-A" men är en annan text även efter normaliseringen: möjlig dublett (K4c).
L2_MOTPART = {
    "mellanslag": "LEV A", "med_ab": "LEV-A AB",
    "cherokee": chr(0x13DE) + chr(0x13AC) + chr(0x13D9) + "-" + chr(0x13AA),  # ser ut som "LEV-A"
    "harfint_mellanslag_kyrilliskt": "LEV-" + chr(0x200A) + KYRILLISKT_A,
}
# Motparter med ett tecken som ser tomt ut. Normaliseringen tar bort det (L2): en vanlig dublett (K4).
L2_MOTPART_OSYNLIGT = {
    "teckenbindare": "LEV-A" + chr(0x034F), "variantvaljare": "LEV-A" + chr(0xFE0F),
    "blank_blindskrift": "LEV-A" + chr(0x2800), "utfyllnad_eget_ord": "LEV-A " + chr(0x3164),
}


def oavstamda_utan_arende(underlagen, resultat):
    """Id:n för oavstämda underlag som varken har ett K4-ärende eller är kandidat i ett matchningsärende."""
    med_arende = {a["id"] for a in underlagen.arenden}
    med_arende |= {id_ for a in resultat.arenden for id_ in a["kandidater"]}
    return [post["id"] for post in resultat.oavstamda_underlag if post["id"] not in med_arende]


@pytest.mark.parametrize("andrat, kontroll, forvantat", [
    *[({"fakturanummer": varde}, "K4c", TVETYDIG) for varde in L1_FAKTURANUMMER.values()],
    *[({"motpart": varde}, "K4c", tomt(matchningar=[(1, "U-1")], oavstamda=["U-2"])) for varde in L2_MOTPART.values()],
    *[({"motpart": varde}, "K4", tomt(matchningar=[(1, "U-1")])) for varde in L2_MOTPART_OSYNLIGT.values()],
], ids=list(L1_FAKTURANUMMER) + ["motpart_" + namn for namn in [*L2_MOTPART, *L2_MOTPART_OSYNLIGT]])
def test_granskning_6_dubbletterna_blir_aldrig_oavstamda_utan_arende(tmp_path, andrat, kontroll, forvantat):
    # L1 och L2: U-2 är U-1 med ett förväxlat tecken i fakturanumret eller motparten. Förut matchade
    # fakturanummerregeln U-1, och U-2 blev ett oavstämt underlag, som en obetald faktura, utan
    # något ärende. Nu gäller:
    # - fakturanumret förväxlat: möjlig dublett (K4c). Båda är kandidater, och fakturanumret avgör
    #   inte, eftersom datumen är samma, så raden blir "tvetydig",
    # - motparten förväxlad: möjlig dublett (K4c). Motparten står inte i bankradens text, så U-2 är
    #   ingen kandidat och blir oavstämd, men med ett ärende,
    # - ett tecken som ser tomt ut i motparten: normaliseringen tar bort det, så U-2 är en dublett (K4).
    original = underlag(fakturanummer="F-1001")
    underlagen = period(tmp_path, original, {**original, "id": "U-2", **andrat})
    rader = bankrader(tmp_path, ("F-1001", "LEV-A", -12500, "2025-01-20"))
    resultat = matcha(rader, underlagen)
    assert oavstamda_utan_arende(underlagen, resultat) == []
    assert [(a["kontroll"], a["id"], a["jamfort_med"]) for a in underlagen.arenden] == [(kontroll, "U-2", "U-1")]
    assert sammanfattning(resultat) == forvantat


def test_fakturanumret_avgor_inte_mellan_underlag_med_samma_datum(tmp_path):
    # L1: två underlag med samma belopp, motpart och datum liknar mer en dublett än två
    # månadsfakturor. Förut avgjorde fakturanumret, och det andra underlaget blev oavstämt.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"), underlag(id="U-2", fakturanummer="F-1002"))
    for referens in ("F-1001", "F-1002", "BET F-1002"):
        rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-01-20"))
        assert sammanfattning(matcha(rader, underlagen)) == TVETYDIG, referens


def test_fakturanumret_avgor_bara_for_ett_underlag_utan_samma_datum_som_en_annan_kandidat(tmp_path):
    # U-1 och U-2 har samma datum, U-3 ett annat. Numret för U-3 avgör, men inte numret för U-1.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"), underlag(id="U-2", fakturanummer="F-1002"),
                        underlag(id="U-3", fakturanummer="F-1003", datum="2025-01-11"))
    alla_tre = tomt(arenden=[(1, "tvetydig", ("U-1", "U-2", "U-3"))], oavstamda=["U-1", "U-2", "U-3"])
    for referens, forvantat in [
        ("F-1003", tomt(matchningar=[(1, "U-3")], oavstamda=["U-1", "U-2"])),
        ("F-1001", alla_tre),
        ("F-1002", alla_tre),
    ]:
        rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-01-20"))
        assert sammanfattning(matcha(rader, underlagen)) == forvantat, referens


@pytest.mark.parametrize("andra_datum", ["2025-01-11", "2025-01-09", "2025-01-20"])
def test_manadsfakturor_med_olika_datum_avgors_fortfarande_av_fakturanumret(tmp_path, andra_datum):
    # Skydd: två fakturor med samma belopp och motpart men olika datum (till exempel ett abonnemang)
    # avgörs fortfarande av fakturanumret, åt båda hållen, även när datumen bara skiljer en dag.
    underlagen = period(tmp_path, underlag(fakturanummer="F-1001"),
                        underlag(id="U-2", fakturanummer="F-1002", datum=andra_datum))
    assert underlagen.arenden == []  # olika datum och fakturanummer: inte K4, K4b eller K4c
    for referens, forvantat in [("F-1001", "U-1"), ("F-1002", "U-2")]:
        rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-01-20"))
        assert sammanfattning(matcha(rader, underlagen)) == betalar(forvantat), (andra_datum, referens)


def test_bedomningsdatumet_jamfors_med_transaktionsdagen_inte_bokforingsdagen(tmp_path):
    # L6 (beslut 3 i åtgärderna efter granskning 5): bankraden gjordes 2025-01-20 men bokfördes
    # 2025-01-22. Ett bedömningsdatum mellan dagarna godtas, eftersom raden finns från
    # transaktionsdagen. Ett bedömningsdatum före transaktionsdagen stoppas.
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20", "2025-01-22"))
    underlagen = period(tmp_path, underlag())
    for dag in ("2025-01-20", "2025-01-21"):
        assert sammanfattning(matcha(rader, underlagen, dag)) == tomt(matchningar=[(1, "U-1")]), dag
    with pytest.raises(MatchningFel, match="ligger före transaktionsdagen 2025-01-20"):
        matcha_period(rader, underlagen, FORMATETS_REGELBOK, "2025-01-19")


def test_fakturanumret_ensamt_racker_inte(tmp_path):
    # Fakturanumret avgör bara mellan underlag som redan passar. Belopp, motpart och tidsfönster krävs ändå.
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", motpart="LEV-B"))
    rader = bankrader(tmp_path, ("F-2", "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(matchningar=[(1, "U-1")], oavstamda=["U-2"])


def test_tvetydigt_ett_underlag_och_tva_bankrader(tmp_path):
    # Underlaget får matchas högst en gång. Båda raderna blir ärenden, och underlaget är oavstämt.
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("F-1", "LEV-A", -12500, "2025-01-21"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(
        arenden=[(1, "tvetydig", ("U-1",)), (2, "tvetydig", ("U-1",))], oavstamda=["U-1"])


def test_tvetydigt_nar_en_kandidat_ocksa_passar_en_annan_bankrad(tmp_path):
    # Rad 1 passar bara U-1, men U-1 passar också rad 2 (som också passar U-2). Ingen matchas.
    rader = bankrader(tmp_path, ("BET-1", "LEV-A", -12500, "2025-01-15"), ("BET-2", "LEV-A", -12500, "2025-01-25"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", datum="2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(
        arenden=[(1, "tvetydig", ("U-1",)), (2, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])


def test_varje_underlag_och_varje_bankrad_matchas_hogst_en_gang(tmp_path):
    # Två rader och två underlag med olika belopp: var sin matchning.
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("F-2", "LEV-A", -500, "2025-01-20"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", belopp_ore=500))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(matchningar=[(1, "U-1"), (2, "U-2")])


def test_obetalt_underlag_ar_oavstamt(tmp_path):
    rader = bankrader(tmp_path, ("IN-1", "INSATTNING", 100, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(
        kraver_inte=[(1, "insattning")], oavstamda=["U-1"])


@pytest.mark.parametrize("referens, beskrivning, belopp, regel", [
    ("IN-1", "VAD SOM HELST", 100, "insattning"),       # referensen räcker för den regeln
    ("X", "AVGIFT FOR KONTOT", -100, "avgift"),          # beskrivningen räcker för den regeln
    ("K-5", "KORT IN 2025-01-20", 100, "kort"),          # båda ska stämma för den regeln
    ("IN-1", "VAD SOM HELST", -100, None),               # fel riktning: pengar ut
    ("X", "AVGIFT FOR KONTOT", 100, None),               # fel riktning: pengar in
    ("K-5", "KORT UT", 100, None),                       # bara referensen stämmer
    ("X-5", "KORT IN", 100, None),                       # bara beskrivningen stämmer
    ("in-1", "VAD SOM HELST", 100, None),                # små bokstäver: ingen normalisering
    ("I" + OSYNLIGT_MELLANSLAG + "N-1", "X", 100, None),  # osynligt tecken: ingen normalisering
    ("XIN-1", "X", 100, None),                           # texten ska börja med mönstret
    ("IN-1", "X", 0, None),                              # 0 kr har ingen riktning
])
def test_bankrader_som_inte_kraver_underlag(tmp_path, referens, beskrivning, belopp, regel):
    rader = bankrader(tmp_path, (referens, beskrivning, belopp, "2025-01-20"))
    resultat = sammanfattning(matcha(rader, period(tmp_path)))
    if regel:
        assert resultat == tomt(kraver_inte=[(1, regel)])
    else:
        assert resultat == tomt(arenden=[(1, "saknat underlag", ())])


def test_rad_som_inte_kraver_underlag_matchas_inte_mot_ett_underlag(tmp_path):
    # En insättning med samma belopp och motpart som ett underlag är fortfarande en insättning.
    rader = bankrader(tmp_path, ("IN-1", "LEV-A", 12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag()))) == tomt(
        kraver_inte=[(1, "insattning")], oavstamda=["U-1"])


# --- Gränsen för regler för pengar ut (hogst_belopp_ore), Hugos beslut 2026-10-25 ---

def over_grans(radnr):
    return (radnr, "över gräns", ())


@pytest.mark.parametrize("belopp, ar_inom", [
    (-1, True), (-199, True),             # under gränsen 200 öre
    (-200, True),                         # exakt på gränsen räknas som inom
    (-201, False), (-12500, False), (-10 ** 12, False),  # över gränsen
])
def test_utgaende_rad_under_pa_och_over_gransen(tmp_path, belopp, ar_inom):
    rader = bankrader(tmp_path, ("X", "AVGIFT FOR KONTOT", belopp, "2025-01-20"))
    resultat = sammanfattning(matcha(rader, period(tmp_path)))
    if ar_inom:
        assert resultat == tomt(kraver_inte=[(1, "avgift")])
    else:
        assert resultat == tomt(arenden=[over_grans(1)])


def test_over_gransen_ger_ett_arende_med_regeln_och_gransen(tmp_path):
    rader = bankrader(tmp_path, ("GOR SA HAR", "AVGIFT GOR SA HAR", -201, "2025-01-20"))
    resultat = matcha(rader, period(tmp_path), "2025-01-20")  # direkt, utan att vänta 7 dagar
    assert resultat.vantande == () and resultat.kraver_inte_underlag == ()
    arende = resultat.arenden[0]
    assert dict(arende, bankrad=None) == {
        "kontroll": "K3", "typ": "över gräns", "regel": "avgift", "hogst_belopp_ore": 200, "kandidater": (),
        "bankrad": None,
        "text": "Bankraden passar regeln 'avgift' för rader som inte kräver underlag, men beloppet är större än"
                " regelns gräns, 2,00 kr per bankrad. En människa behöver avgöra vad raden är och vilket underlag"
                " den ska ha.",
    }
    assert "GOR SA HAR" not in arende["text"]  # inga texter ur bankraden
    assert dict(arende["bankrad"]) == rader.rader[0]


def test_over_gransen_matchas_inte_mot_underlag(tmp_path):
    # En rad över gränsen med samma belopp, motpart och datum som ett underlag matchas inte med det.
    # En människa ska se den, eftersom en så stor rad inte ser ut som det regeln är till för.
    rader = bankrader(tmp_path, ("F-1", "AVGIFT LEV-A", -12500, "2025-01-20"))
    underlagen = period(tmp_path, underlag())
    assert sammanfattning(matcha(rader, underlagen)) == tomt(arenden=[over_grans(1)], oavstamda=["U-1"])
    # Skydd: utan regeln matchas samma rad med underlaget.
    utan_regel = {**FORMAT, "kraver_inte_underlag": [r for r in FORMAT["kraver_inte_underlag"] if r["namn"] != "avgift"]}
    assert sammanfattning(matcha(rader, underlagen, format_=utan_regel)) == tomt(matchningar=[(1, "U-1")])


def test_inkommande_rad_paverkas_inte_av_gransen(tmp_path):
    # Regler för pengar in har ingen gräns. En stor insättning kräver fortfarande inget underlag, och
    # en stor inkommande rad som börjar som en avgift passar inte regeln för pengar ut.
    rader = bankrader(tmp_path, ("IN-1", "X", 10 ** 12, "2025-01-20"), ("K-1", "KORT IN", 201, "2025-01-20"),
                      ("X", "AVGIFT FOR KONTOT", 201, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path))) == tomt(
        kraver_inte=[(1, "insattning"), (2, "kort")], arenden=[(3, "saknat underlag", ())])


def test_gransen_galler_varje_bankrad_for_sig(tmp_path):
    # Två avgifter som tillsammans är över gränsen, men var för sig inom: inget ärende.
    rader = bankrader(tmp_path, ("X", "AVGIFT A", -200, "2025-01-20"), ("X", "AVGIFT B", -200, "2025-01-20"),
                      ("X", "AVGIFT C", -201, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path))) == tomt(
        kraver_inte=[(1, "avgift"), (2, "avgift")], arenden=[over_grans(3)])


def test_testdatans_avgifter_ligger_inom_gransen(kvartalet):
    # Avgifterna i testdatan är 125 och 199 kr, under gränsen 250 kr. Med en gräns på 198,99 kr blir
    # de tre avgifterna på 199 kr ärenden, så gränsen prövas verkligen på testdatans rader.
    avgifter = sorted(-rad["belopp_ore"] for rad in kvartalet["rader"] if rad["referens"].startswith("AVG-"))
    assert avgifter == [12500] * 3 + [19900] * 3
    bankavgift = [r for r in MATCHNINGSFORMAT["kraver_inte_underlag"] if r["namn"] == "bankavgift"][0]
    assert bankavgift["hogst_belopp_ore"] == 25000
    lagre = copy.deepcopy(MATCHNINGSFORMAT)
    [r for r in lagre["kraver_inte_underlag"] if r["namn"] == "bankavgift"][0]["hogst_belopp_ore"] = 19899
    resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], regelbok_for(lagre), "2025-04-30")
    over = [a for a in resultat.arenden if a["typ"] == "över gräns"]
    assert [(a["regel"], a["bankrad"]["belopp_ore"]) for a in over] == [("bankavgift", -19900)] * 3
    assert len(resultat.arenden) == 4  # och det planterade ärendet
    kontrollera_grupperna(resultat, kvartalet["bankperiod"], kvartalet["period"])
    # Exakt på 199 kr: inom gränsen, inga nya ärenden.
    [r for r in lagre["kraver_inte_underlag"] if r["namn"] == "bankavgift"][0]["hogst_belopp_ore"] = 19900
    resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], regelbok_for(lagre), "2025-04-30")
    assert [a["typ"] for a in resultat.arenden] == ["saknat underlag"]


# --- Granskning 8, N3: ägarens bankrader kräver alltid underlag (beslutet 2026-10-27) ---

AGARUTTAG = {"namn": "agaruttag", "riktning": "ut", "beskrivning_borjar_med": "UTTAG AGARE", "hogst_belopp_ore": 100000}
MED_AGARUTTAG = {**FORMAT, "kraver_inte_underlag": FORMAT["kraver_inte_underlag"] + [AGARUTTAG]}


def granskarens_rader(tmp_path):
    """Granskarens prov ur granskning 8, N3. Rad 1–3 är mot ägaren AGARE-1, rad 4 och 5 kan vara andra motparter."""
    return bankrader(tmp_path, ("UTTAG-1", "UTTAG AGARE-1", -50000, "2025-04-01"),
                     ("UTTAG-2", "UTTAG AGARE-1/LAN", -10000, "2025-04-01"),
                     ("UTTAG-3", "UTTAG AGARE-1.", -10000, "2025-04-02"),
                     ("UTTAG-4", "UTTAG AGARE-1X", -10000, "2025-04-02"),
                     ("UTTAG-5", "UTTAG AGARE-10", -10000, "2025-04-03"))


def test_n3_granskarens_prov_agarens_rader_kraver_underlag(tmp_path):
    # Förut hamnade alla fem raderna bland raderna som inte kräver underlag, eftersom matchningen inte
    # visste vem som är ägare. Nu kräver rad 1–3 underlag: de väntar på det, och blir ärenden "saknat
    # underlag" efter 7 dagar (K3). Rad 4 och 5 undantas fortfarande av regeln.
    rader = granskarens_rader(tmp_path)
    assert [rad["radnr"] for rad in rader.rader if regelbok_for(MED_AGARUTTAG).ar_bankrad_mot_agare_eller_narstaende(
        rad)] == [1, 2, 3]
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-03", format_=MED_AGARUTTAG)) == tomt(
        vantande=[(1, "2025-04-08"), (2, "2025-04-08"), (3, "2025-04-09")],
        kraver_inte=[(4, "agaruttag"), (5, "agaruttag")])
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-30", format_=MED_AGARUTTAG)) == tomt(
        arenden=[(1, "saknat underlag", ()), (2, "saknat underlag", ()), (3, "saknat underlag", ())],
        kraver_inte=[(4, "agaruttag"), (5, "agaruttag")])
    # Skydd: utan ägare i regelboken passar alla fem raderna regeln, så regeln prövas verkligen.
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-30", format_=MED_AGARUTTAG, agare=())) == tomt(
        kraver_inte=[(nummer, "agaruttag") for nummer in range(1, 6)])


def test_n3_agarens_rad_over_gransen_kraver_underlag_och_ar_inte_over_grans(tmp_path):
    # En rad mot ägaren över regelns gräns ska inte bli "över gräns" med regelns namn, eftersom regeln
    # aldrig gäller den. Den kräver underlag som alla andra rader. En annan motpart över gränsen blir
    # fortfarande "över gräns".
    rader = bankrader(tmp_path, ("UTTAG-1", "UTTAG AGARE-1", -100001, "2025-04-01"),
                      ("UTTAG-2", "UTTAG AGARE-10", -100001, "2025-04-01"),
                      ("UTTAG-3", "UTTAG AGARE-1", -10 ** 12, "2025-04-01"))
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-01", format_=MED_AGARUTTAG)) == tomt(
        arenden=[over_grans(2)], vantande=[(1, "2025-04-08"), (3, "2025-04-08")])
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-09", format_=MED_AGARUTTAG)) == tomt(
        arenden=[over_grans(2), (1, "saknat underlag", ()), (3, "saknat underlag", ())])
    # Skydd: utan ägare i regelboken är rad 1 och 3 också över gränsen.
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-01", format_=MED_AGARUTTAG, agare=())) == tomt(
        arenden=[over_grans(1), over_grans(2), over_grans(3)])


def test_n3_agarens_rad_matchas_mot_ett_underlag(tmp_path):
    # Raden behandlas som alla rader som kräver underlag: finns ett underlag matchas den med det.
    rader = bankrader(tmp_path, ("UTTAG-1", "UTTAG AGARE-1", -50000, "2025-04-01"))
    underlagen = period(tmp_path, underlag(motpart="AGARE-1", fakturanummer="UTTAG-1", belopp_ore=50000,
                                           datum="2025-04-01"))
    assert sammanfattning(matcha(rader, underlagen, format_=MED_AGARUTTAG)) == tomt(matchningar=[(1, "U-1")])


@pytest.mark.parametrize("referens, beskrivning", [
    ("TILL:AGARE-1", "UTTAG AGARE"),       # ägaren står i referensen
    ("X", "UTTAG AGARE 1"),                # mellanslag i stället för bindestreck
    ("X", "UTTAG AGARE" + TANKSTRECK + "1"),  # ett tankstreck i stället för bindestreck
    ("X", "UTTAG AGARE (agare-1)"),        # små bokstäver, inom parentes
])
def test_n3_agaren_pekas_ut_med_regelbokens_uppslag(tmp_path, referens, beskrivning):
    # Matchningen jämför inga namn själv: den använder regelbokens uppslag, med samma regler för hela ord.
    rader = bankrader(tmp_path, (referens, beskrivning, -10000, "2025-04-01"))
    assert regelbok_for(MED_AGARUTTAG).ar_bankrad_mot_agare_eller_narstaende(rader.rader[0])
    # Skydd: regeln passar raden, så det är ägaren som gör att den kräver underlag.
    assert regelbok_for(MED_AGARUTTAG, agare=()).matchningsregel_for_bankrad(rader.rader[0]) == "agaruttag"
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-30", format_=MED_AGARUTTAG)) == tomt(
        arenden=[(1, "saknat underlag", ())])


def test_n3_en_narstaende_i_listan_galler_som_agaren(tmp_path):
    # Listan heter agare_och_narstaende: en närstående behandlas som en ägare.
    rader = bankrader(tmp_path, ("X", "UTTAG AGARE-2", -10000, "2025-04-01"), ("X", "UTTAG AGARE-1", -10000, "2025-04-01"))
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-30", format_=MED_AGARUTTAG,
                                 agare=("AGARE-1", "AGARE-2"))) == tomt(
        arenden=[(1, "saknat underlag", ()), (2, "saknat underlag", ())])
    assert sammanfattning(matcha(rader, period(tmp_path), "2025-04-30", format_=MED_AGARUTTAG, agare=("AGARE-2",))) == tomt(
        arenden=[(1, "saknat underlag", ())], kraver_inte=[(2, "agaruttag")])


def test_n3_testdatans_rader_ger_samma_resultat_som_utan_agare(kvartalet):
    # Ingen av testdatans rader i Q1 är mot ägaren, så resultatet är exakt detsamma som med en regelbok
    # utan ägare och närstående (som förut, då matchningen inte visste vilka som är ägare). Testerna
    # ovan för kvartalet visar att resultatet är detsamma som förut, rad för rad.
    assert not [rad for rad in kvartalet["rader"] if REGELBOK.ar_bankrad_mot_agare_eller_narstaende(rad)]
    assert REGELBOK.agare_och_narstaende == ["AGARE-1"]
    for dag in ("2025-03-31", "2025-04-30"):
        med = matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK, dag)
        for regelbok in (regelbok_for(MATCHNINGSFORMAT), regelbok_for(MATCHNINGSFORMAT, agare=())):
            assert matcha_period(kvartalet["bankperiod"], kvartalet["period"], regelbok, dag) == med
        kontrollera_grupperna(med, kvartalet["bankperiod"], kvartalet["period"])
    assert [(a["typ"], a["bankrad"]["radnr"]) for a in med.arenden] == [("saknat underlag", 85)]
    assert (len(med.matchningar), len(med.kraver_inte_underlag), len(med.vantande)) == (23, 371, 0)


def test_flera_bankfiler(tmp_path):
    # Två bankfiler i en kedja, ihopsatta med sla_ihop_bankperioder.
    forsta = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), namn="a.csv")
    andra = bankrader(tmp_path, ("IN-1", "X", 100, "2025-02-01"), namn="b.csv", ingaende=-12500)
    underlagen = period(tmp_path, underlag())
    assert sammanfattning(matcha(sla_ihop_bankperioder([forsta, andra]), underlagen)) == tomt(
        matchningar=[(1, "U-1")], kraver_inte=[(1, "insattning")])
    assert sammanfattning(matcha(andra, underlagen)) == tomt(kraver_inte=[(1, "insattning")], oavstamda=["U-1"])


# --- Indatan kontrolleras ---

def en_rad(tmp_path):
    return bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"))


def test_bankraderna_ska_vara_en_bankperiod(tmp_path):
    # Bankraderna tas bara emot som en Bankperiod från las_bankfil, aldrig som en lista. Inte heller
    # raderna från en riktig Bankperiod, eftersom de kan ha ändrats efter inläsningen.
    bankperiod = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 100, "2025-01-20"))
    underlagen = period(tmp_path, underlag())

    class Underklass(Bankperiod):
        __slots__ = ()

    for varde, text in [
        (None, "None"), ({"id": "x"}, "ett objekt"), ("bankrader", "'bankrader'"), (iter([]), "list_iterator"),
        ([], "en lista"), ((), "en tupel"), ([None], "en lista"), (bankperiod.rader, "en lista"),
        (tuple(bankperiod.rader), "en tupel"), (bankperiod.rader[:1], "en lista"), (underlagen, "Underlagsperiod"),
        (Underklass.__new__(Underklass), "Underklass"),
    ]:
        with pytest.raises(MatchningFel, match="^Bankraderna ska vara en Bankperiod från las_bankfil eller"
                                               " sla_ihop_bankperioder, inte " + text + r"\.$"):
            matcha_period(varde, underlagen, FORMATETS_REGELBOK, "2025-12-31")
    # Skydd: samma Bankperiod godtas.
    assert sammanfattning(matcha(bankperiod, underlagen)) == tomt(matchningar=[(1, "U-1")], kraver_inte=[(2, "insattning")])


def test_en_bankrad_som_tas_bort_efter_inlasningen_blir_anda_ett_arende(tmp_path):
    # Hugos beslut 2026-10-25: en bankrad som tas bort efter inläsningen får inte försvinna ur
    # matchningen. Raderna som läses ut ur en Bankperiod är kopior, så att ta bort eller ändra en rad
    # i dem når inte perioden.
    bankperiod = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("X-1", "OKAND", -100, "2025-01-20"))
    underlagen = period(tmp_path, underlag())
    rader = bankperiod.rader
    del rader[1]
    rader[0]["belopp_ore"] = -1
    with pytest.raises(MatchningFel, match="^Bankraderna ska vara en Bankperiod"):
        matcha_period(rader, underlagen, FORMATETS_REGELBOK, "2025-12-31")
    assert sammanfattning(matcha(bankperiod, underlagen)) == tomt(
        matchningar=[(1, "U-1")], arenden=[(2, "saknat underlag", ())])


def test_samma_bankfil_tva_ganger_stoppas_redan_nar_perioderna_satts_ihop(tmp_path):
    # Samma bankfil inläst två gånger kan inte nå matchningen: sla_ihop_bankperioder stoppar den.
    noll = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 12500, "2025-01-21"))
    with pytest.raises(BankfilFel, match="finns i flera Bankperioder"):
        sla_ihop_bankperioder([noll, noll])


def test_underlagen_ska_vara_en_underlagsperiod(tmp_path):
    rader = en_rad(tmp_path)
    underlagen = period(tmp_path, underlag())

    class Underklass(Underlagsperiod):
        pass

    for varde, text in [(underlagen.underlag, "en lista"), (None, "None"), ({}, "ett objekt"),
                        (Underklass.__new__(Underklass), "Underklass")]:
        with pytest.raises(MatchningFel, match="^Underlagen ska vara en Underlagsperiod från las_underlagsperiod,"
                                               " inte " + text):
            matcha_period(rader, varde, FORMATETS_REGELBOK, "2025-12-31")


def test_regelboken_ska_vara_en_regelbok(tmp_path):
    # Granskning 8, N3: matchningen får matchningsformatet och listan över ägare och närstående bara
    # genom en Regelbok från las_regelbok. Ett matchningsformat för sig, som ett vanligt objekt eller
    # från las_matchningsformat, godtas inte längre: då skulle matchningen kunna använda ett annat format
    # än regelboken kontrollerades mot, och inte veta vilka som är ägare.
    rader = en_rad(tmp_path)
    underlagen = period(tmp_path, underlag())

    class Underklass(Regelbok):
        __slots__ = ()

    for varde, text in [(None, "None"), (FORMAT, "ett objekt"), (copy.deepcopy(MATCHNINGSFORMAT), "ett objekt"),
                        (las_matchningsformat(FORETAG / "matchning.json"), "Matchningsformat"),
                        ("regelbok", "'regelbok'"), (object.__new__(Underklass), "Underklass")]:
        with pytest.raises(MatchningFel, match="^Regelboken ska vara en Regelbok från las_regelbok, inte " + text
                                               + r"\.$"):
            matcha_period(rader, underlagen, varde, "2025-12-31")
    # Skydd: en Regelbok godtas.
    assert sammanfattning(matcha(rader, underlagen)) == tomt(matchningar=[(1, "U-1")])


def test_tom_regelbok_ger_matchningfel(tmp_path):
    # Som för perioderna (J7): en Regelbok skapad med __new__, utan las_regelbok, saknar sitt innehåll.
    with pytest.raises(MatchningFel, match=r"^Regelboken är tom eller trasig: den har inte skapats av las_regelbok\.$"):
        matcha_period(en_rad(tmp_path), period(tmp_path), object.__new__(Regelbok), "2025-12-31")


@pytest.mark.parametrize("varde", [None, "", "2025-1-01", "2025-02-30", "31/12/2025", 20251231,
                                   dt.date(2025, 12, 31), " 2025-12-31", "２０２５-12-31"])
def test_bedomningsdatum_ska_vara_ett_giltigt_datum(tmp_path, varde):
    with pytest.raises(MatchningFel, match="^Bedömningsdatumet ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD"):
        matcha_period(en_rad(tmp_path), period(tmp_path), FORMATETS_REGELBOK, varde)


def test_bedomningsdatum_fore_en_bankrad_stoppas(tmp_path):
    # J9: en bedömning kan inte göras innan bankraden finns. Förut godtogs det, och raden väntade.
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("X-1", "GOR SA HAR", -100, "2025-03-01"))
    underlagen = period(tmp_path, underlag())
    for dag in ("2025-02-28", "2025-01-19", "0001-01-01"):
        with pytest.raises(MatchningFel) as fel:
            matcha_period(rader, underlagen, FORMATETS_REGELBOK, dag)
        assert str(fel.value).startswith(
            "Bedömningsdatumet " + dag + " ligger före transaktionsdagen 2025-03-01 för bankraden med radnummer 2"
            if dag == "2025-02-28" else "Bedömningsdatumet " + dag + " ligger före transaktionsdagen 2025-01-20 för"
            " bankraden med radnummer 1"), str(fel.value)
        assert "GOR SA HAR" not in str(fel.value)  # inga texter ur bankraden
    # Skydd: samma dag som den sista bankraden godtas.
    assert sammanfattning(matcha(rader, underlagen, "2025-03-01")) == tomt(
        matchningar=[(1, "U-1")], vantande=[(2, "2025-03-08")])


def test_fler_an_20_000_bankrader_stoppas(tmp_path):
    # J5: matchningen tar tid som växer med antalet i kvadrat. Tills den har gjorts snabbare tar den
    # högst 20 000 bankrader och 20 000 underlag åt gången.
    rader = [("IN-" + str(nummer), "X", 1, "2025-01-20") for nummer in range(20_001)]
    for_manga = bankrader(tmp_path, *rader)
    with pytest.raises(MatchningFel, match="^Matchningen stoppas: det finns 20 001 bankrader, men matchningen tar"
                                           " högst 20 000 åt gången"):
        matcha_period(for_manga, period(tmp_path), FORMATETS_REGELBOK, "2025-12-31")
    precis = bankrader(tmp_path, *rader[:20_000])
    assert len(matcha_period(precis, period(tmp_path), FORMATETS_REGELBOK, "2025-12-31").kraver_inte_underlag) == 20_000
    assert matcha_bank._HOGST_ANTAL == 20_000  # samma gräns gäller underlagen (nästa test)


def test_fler_underlag_an_gransen_stoppas(tmp_path, monkeypatch):
    # J5 för underlagen, med en lägre gräns så att testet går fort. Gränsen själv prövas ovan.
    # raising=False: testet ska kunna köras mot koden före rättelsen, där gränsen inte finns.
    monkeypatch.setattr(matcha_bank, "_HOGST_ANTAL", 3, raising=False)
    rader = bankrader(tmp_path, ("IN-1", "X", 1, "2025-01-20"))
    poster = [underlag(id="U-" + str(nummer), fakturanummer="F-" + str(nummer)) for nummer in range(1, 5)]
    with pytest.raises(MatchningFel, match="^Matchningen stoppas: det finns 4 underlag, men matchningen tar högst 3"):
        matcha_period(rader, period(tmp_path, *poster), FORMATETS_REGELBOK, "2025-12-31")
    tre = tmp_path / "tre"
    tre.mkdir()
    assert len(matcha(rader, period(tre, *poster[:3])).oavstamda_underlag) == 3  # exakt på gränsen godtas
    fyra_rader = bankrader(tmp_path, *[("IN-" + str(nummer), "X", 1, "2025-01-20") for nummer in range(4)])
    with pytest.raises(MatchningFel, match="^Matchningen stoppas: det finns 4 bankrader"):
        matcha_period(fyra_rader, period(tre), FORMATETS_REGELBOK, "2025-12-31")


def test_tom_bankperiod_eller_underlagsperiod_ger_matchningfel(tmp_path):
    # J7: en period som skapas med __new__, utan las_bankfil eller las_underlagsperiod, saknar sitt
    # innehåll. Förut gav det AttributeError i stället för MatchningFel.
    rader = en_rad(tmp_path)
    underlagen = period(tmp_path, underlag())
    with pytest.raises(MatchningFel, match="^Bankperioden är tom eller trasig: den har inte skapats av las_bankfil"
                                           " eller sla_ihop_bankperioder"):
        matcha_period(Bankperiod.__new__(Bankperiod), underlagen, FORMATETS_REGELBOK, "2025-12-31")
    with pytest.raises(MatchningFel, match="^Underlagsperioden är tom eller trasig: den har inte skapats av"
                                           " las_underlagsperiod"):
        matcha_period(rader, Underlagsperiod.__new__(Underlagsperiod), FORMATETS_REGELBOK, "2025-12-31")


def test_datumets_form_kontrolleras_aven_med_nyare_python(tmp_path, monkeypatch):
    # Python 3.9 godtar bara ÅÅÅÅ-MM-DD i date.fromisoformat. Python 3.11 och senare godtar fler
    # skrivsätt, till exempel 20251231. Här efterliknas det, så att testet visar att formen
    # kontrolleras av matcha_bank själv, i alla Pythonversioner.
    vanlig = dt.date

    class Slapp(vanlig):
        @classmethod
        def fromisoformat(cls, text):
            return vanlig(int(text[:4]), int(text[-4:-2]), int(text[-2:])) if text.isdigit() else \
                vanlig.fromisoformat(text)

    monkeypatch.setattr(matcha_bank.dt, "date", Slapp)
    assert Slapp.fromisoformat("20251231") == dt.date(2025, 12, 31)  # skydd: efterliknandet fungerar
    with pytest.raises(MatchningFel, match="^Bedömningsdatumet ska vara ett giltigt datum"):
        matcha_period(en_rad(tmp_path), period(tmp_path), FORMATETS_REGELBOK, "20251231")


@pytest.mark.parametrize("andring, text", [
    (lambda f: f.pop("tidsfonster_dagar"), "saknar nyckeln 'tidsfonster_dagar'"),
    (lambda f: f.update(saknat_underlag_efter_dagar=-1), "'saknat_underlag_efter_dagar' ska vara ett heltal"),
    (lambda f: f["tidsfonster_dagar"].update(kvitto=True), "tidsfönstret för 'kvitto' ska vara ett heltal"),
    (lambda f: f["kraver_inte_underlag"][0].update(riktning="IN"), "'riktning' ska vara en av 'in', 'ut'"),
    (lambda f: f.update({7: 7}), "har en nyckel som inte är text"),
    (lambda f: f["kraver_inte_underlag"][1].pop("hogst_belopp_ore"), "saknar 'hogst_belopp_ore'"),
    (lambda f: f["kraver_inte_underlag"][1].update(hogst_belopp_ore=0), "'hogst_belopp_ore' ska vara ett heltal"),
    (lambda f: f["kraver_inte_underlag"][0].update(hogst_belopp_ore=1), "har 'hogst_belopp_ore', men gäller pengar in"),
])
def test_trasigt_format_i_regelboken_stoppas_anda(tmp_path, monkeypatch, andring, text):
    # Formatet kommer från regelboken och kan inte längre skickas in direkt (granskning 8, N3). Det
    # kontrolleras ändå igen i matcha_period. Här efterliknas en regelbok med ett trasigt format (det går
    # inte att få fram med las_regelbok), så att testet visar att kontrollen finns kvar.
    format_ = copy.deepcopy(FORMAT)
    andring(format_)
    monkeypatch.setattr(Regelbok, "matchningsformat", property(lambda bok: format_), raising=False)
    with pytest.raises(MatchningFel) as fel:
        matcha_period(en_rad(tmp_path), period(tmp_path), FORMATETS_REGELBOK, "2025-12-31")
    assert type(fel.value) is MatchningFel and text in str(fel.value), str(fel.value)


# --- Indatan ändras aldrig, och resultatet går inte att ändra ---

def test_indatan_andras_aldrig(tmp_path):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 100, "2025-01-20"),
                      ("X-1", "OKAND", -1, "2025-01-20"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", belopp_ore=1))
    regelbok = FORMATETS_REGELBOK
    fore = (rader.rader, underlagen.underlag, underlagen.arenden, regelbok.matchningsformat,
            regelbok.agare_och_narstaende, regelbok.kontrollsumma)
    resultat = matcha_period(rader, underlagen, regelbok, "2025-12-31")
    assert (rader.rader, underlagen.underlag, underlagen.arenden, regelbok.matchningsformat,
            regelbok.agare_och_narstaende, regelbok.kontrollsumma) == fore
    assert regelbok.matchningsformat == kontrollera_matchningsformat(FORMAT)
    # Resultatet är en kopia: att ändra det som läses ur indatan efteråt ändrar inte resultatet.
    regelbok.matchningsformat["kraver_inte_underlag"].clear()
    assert resultat.matchningar[0]["bankrad"]["belopp_ore"] == -12500
    assert len([post for grupp in GRUPPER_FOR_BANKRADER for post in getattr(resultat, grupp)]) == 3


def test_resultatet_gar_inte_att_andra(tmp_path):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 100, "2025-01-20"),
                      ("X-1", "OKAND", -1, "2025-01-20"), ("X-2", "OKAND", -2, "2025-12-30"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", belopp_ore=3))
    resultat = matcha_period(rader, underlagen, FORMATETS_REGELBOK, "2025-12-31")
    assert type(resultat) is Matchningsresultat
    assert all(getattr(resultat, grupp) for grupp in Matchningsresultat._fields)  # alla grupper har något
    with pytest.raises(AttributeError):
        resultat.matchningar = ()
    with pytest.raises(AttributeError):
        del resultat.arenden
    for grupp in resultat:
        assert type(grupp) is tuple
        with pytest.raises(AttributeError):
            grupp.append(1)
        with pytest.raises(TypeError):
            grupp[0] = 1
        for post in grupp:
            with pytest.raises(TypeError):
                post["ny"] = 1
            for varde in post.values():
                if hasattr(varde, "keys"):
                    with pytest.raises(TypeError):
                        varde["belopp_ore"] = 1
    with pytest.raises(TypeError):
        resultat.oavstamda_underlag[0]["moms"][0]["moms_ore"] = 1
    with pytest.raises(AttributeError):
        resultat.arenden[0]["kandidater"].append("U-9")


def test_det_finns_bara_en_offentlig_funktion():
    # matcha_period är den enda offentliga funktionen. MatchningFel och Matchningsresultat är klasser.
    import inspect

    offentliga = [namn for namn, varde in vars(matcha_bank).items() if not namn.startswith("_")
                  and (inspect.isfunction(varde) or inspect.isclass(varde)) and varde.__module__ == "matcha_bank"]
    assert sorted(offentliga) == ["MatchningFel", "Matchningsresultat", "matcha_period"]


# --- Fuzz: slumpade skador på bankrader, underlag och format ---

FARLIGA_VARDEN = [None, True, False, 0, -1, 1.5, 10 ** 30, -10 ** 30, "", " ", "x" * 1000, HOGER_TILL_VANSTER,
                  OSYNLIGT_MELLANSLAG, "\x00", "2025-02-30", "0001-01-01", "9999-12-31", "2025-01-20", [], {},
                  [1], {"a": 1}, b"x", "LEV-A", "IN-", "AVGIFT", "-12500", 12500, -12500, dt.date(2025, 1, 1)]


def skada_rader(rng, rader, motparter):
    """Ändringar i en liten bankfils rader, (referens, beskrivning, belopp_ore, transaktionsdag). Bankfilen
    skrivs sedan och läses med las_bankfil, så att matchningen bara får en Bankperiod."""
    rader = list(rader)
    sort = rng.randrange(5)
    if sort == 0 and rader:  # belopp, datum, motpart eller mönster
        nummer = rng.randrange(len(rader))
        referens, beskrivning, belopp, dag = rader[nummer]
        val = rng.randrange(4)
        if val == 0:
            belopp = rng.choice([-belopp, belopp + 1, 0, -12500, 100])
        elif val == 1:
            dag = rng.choice(["2025-01-01", "2025-01-10", "2025-02-09", "9999-12-31", "0001-01-01"])
        elif val == 2:
            beskrivning = rng.choice(motparter + ["X " + rng.choice(motparter), "AVGIFT X", "KORT IN", "AVGIFT AGARE-1",
                                                  "KORT IN AGARE-1"])
        else:
            referens = rng.choice(["IN-1", "K-1", "F-1", "", rng.choice(motparter)])
        rader[nummer] = (referens, beskrivning, belopp, dag)
    elif sort == 1 and rader:  # samma rad två gånger (med ett nytt radnummer i filen)
        rader.insert(rng.randrange(len(rader) + 1), rng.choice(rader))
    elif sort == 2 and rader:  # byt plats på två rader
        a, b = rng.randrange(len(rader)), rng.randrange(len(rader))
        rader[a], rader[b] = rader[b], rader[a]
    elif sort == 3 and len(rader) > 1:  # ta bort en rad
        del rader[rng.randrange(len(rader))]
    return rader


def inte_en_bankperiod(rng, bankperiod):
    """Något annat än en Bankperiod, till exempel periodens rader som en lista. Ska alltid ge MatchningFel."""
    rader = bankperiod.rader
    return rng.choice([None, {}, "rader", 5, [], (), rader, tuple(rader), rader[1:], rader + rader[:1],
                       rader[:1] + [{"id": "x"}], dt.date(2025, 1, 1)])


def ogonblick(varde):
    """En jämförbar kopia av indatan. En Bankperiod kopieras med sina rader och saldon, eftersom den
    inte går att kopiera med deepcopy (den kan inte ändras, inte ens av deepcopy)."""
    if type(varde) is Bankperiod:
        return ("Bankperiod", varde.rader, varde.ingaende_saldo_ore, varde.utgaende_saldo_ore)
    return copy.deepcopy(varde)


# Gränser för regler för pengar ut: kring testdatans avgifter (12500 och 19900) och de små fallens
# (125), utanför gränserna, och av fel typ.
GODA_GRANSER = [1, 124, 125, 126, 199, 200, 12499, 12500, 19899, 19900, 25000, 10 ** 15 - 1]
TRASIGA_GRANSER = [10 ** 15, 0, -1, True, 125.0, "125", None]


def grans(rng):
    """Oftast en giltig gräns, så att fuzzen ger resultat och inte bara stopp."""
    return rng.choice(GODA_GRANSER if rng.random() < 0.8 else TRASIGA_GRANSER)


def skada_format(rng, format_):
    format_ = copy.deepcopy(format_)
    sort = rng.randrange(8)
    if sort == 0:  # byt ut ett värde överst
        format_[rng.choice(sorted(format_))] = rng.choice(FARLIGA_VARDEN)
    elif sort == 1:  # byt ut ett tidsfönster eller antalet dagar
        varde = rng.choice([0, 1, 366, 367, -1, True, 1.5, "7", None, 10 ** 30])
        if rng.random() < 0.5:
            format_["tidsfonster_dagar"][rng.choice(["kvitto", "leverantorsfaktura", "annat"])] = varde
        else:
            format_["saknat_underlag_efter_dagar"] = varde
    elif sort == 2 and format_["kraver_inte_underlag"]:  # byt ut ett värde i en regel
        regel = rng.choice(format_["kraver_inte_underlag"])
        regel[rng.choice(["namn", "riktning", "referens_borjar_med", "beskrivning_borjar_med", "anteckning",
                          "hogst_belopp_ore", "okand"])] = rng.choice(FARLIGA_VARDEN + ["in", "ut"])
    elif sort == 3:  # en regel till, som kan krocka med en annan, med eller utan gräns
        ny = {"namn": rng.choice(["ny", "insattning"]), "riktning": rng.choice(["in", "ut"]),
              rng.choice(["referens_borjar_med", "beskrivning_borjar_med"]): rng.choice(["IN-1", "Q", "K", "AVG"])}
        if rng.random() < (0.9 if ny["riktning"] == "ut" else 0.1):
            ny["hogst_belopp_ore"] = grans(rng)
        format_["kraver_inte_underlag"].append(ny)
    elif sort == 6 and format_["kraver_inte_underlag"]:  # ändra eller ta bort gränsen i en regel för pengar ut
        ut = [regel for regel in format_["kraver_inte_underlag"] if regel.get("riktning") == "ut"]
        regel = rng.choice(ut or format_["kraver_inte_underlag"])
        if rng.random() < 0.15:
            regel.pop("hogst_belopp_ore", None)
        else:
            regel["hogst_belopp_ore"] = grans(rng)
    elif sort == 4:  # ta bort en nyckel, eller en regel
        if rng.random() < 0.5:
            del format_[rng.choice(sorted(format_))]
        elif format_["kraver_inte_underlag"]:
            del format_["kraver_inte_underlag"][0]
    elif sort == 5:
        return rng.choice([None, [], "format", 1, {1: 2}])
    return format_


def skada_underlag(rng, poster):
    poster = copy.deepcopy(poster)
    post = rng.choice(poster)
    val = rng.randrange(5)
    if val == 0:
        post["belopp_ore"] = rng.choice([1, 100, 12500, 0])
        post["moms"] = [{"momssats": 0, "underlag_ore": post["belopp_ore"], "moms_ore": 0}]
    elif val == 1:
        post["datum"] = rng.choice(["2025-01-01", "2025-01-20", "2025-12-31", "2025-02-30"])
    elif val == 2:
        post["motpart"] = rng.choice(["LEV-A", "LEV-B", "lev a", "", HOGER_TILL_VANSTER, "X" * 300])
    elif val == 3:
        post["typ"] = rng.choice(["kvitto", "leverantorsfaktura", "kreditnota"])
    else:
        kopia = dict(post, id=post["id"] + "-K")  # ett underlag till med samma uppgifter
        poster.append(kopia)
    return poster


def ar_giltigt(resultat, bankperiod, underlagen, regelbok, bedomning):
    """Ett resultat ska alltid följa reglerna i matcha_bank.py, med regelbokens matchningsformat."""
    format_ = kontrollera_matchningsformat(regelbok.matchningsformat)
    kontrollera_grupperna(resultat, bankperiod, underlagen)
    # En rad mot en ägare eller närstående undantas aldrig av en regel (granskning 8, N3).
    for post in resultat.kraver_inte_underlag + tuple(a for a in resultat.arenden if a["typ"] == "över gräns"):
        assert not regelbok.ar_bankrad_mot_agare_eller_narstaende(post["bankrad"])
    assert all(rad["transaktionsdag"] <= bedomning for rad in bankperiod.rader)  # annars stoppas den (J9)
    dag = dt.date.fromisoformat(bedomning)
    for matchning in resultat.matchningar:
        rad, post = matchning["bankrad"], matchning["underlag"]
        assert rad["belopp_ore"] == -post["belopp_ore"]
        forsta = dt.date.fromisoformat(post["datum"])
        assert 0 <= (dt.date.fromisoformat(rad["transaktionsdag"]) - forsta).days <= format_["tidsfonster_dagar"][
            post["typ"]]
        assert normalisera_kassaregister(post["motpart"]) in (normalisera_kassaregister(rad["beskrivning"])
                                                              + normalisera_kassaregister(rad["referens"]))
    regler = {regel["namn"]: regel for regel in format_["kraver_inte_underlag"]}
    for arende in resultat.arenden:
        assert (arende["typ"] == "tvetydig") == bool(arende["kandidater"])
        assert arende["typ"] in ("tvetydig", "saknat underlag", "över gräns")
        if arende["typ"] == "saknat underlag":
            assert (dag - dt.date.fromisoformat(arende["bankrad"]["transaktionsdag"])).days > format_[
                "saknat_underlag_efter_dagar"]
        if arende["typ"] == "över gräns":  # en utgående rad som passar regeln, över regelns gräns
            regel, rad = regler[arende["regel"]], arende["bankrad"]
            assert regel["riktning"] == "ut" and arende["hogst_belopp_ore"] == regel["hogst_belopp_ore"]
            assert passar(rad, regel) and -rad["belopp_ore"] > regel["hogst_belopp_ore"]
        else:
            assert "regel" not in arende and "hogst_belopp_ore" not in arende
    for post in resultat.vantande:
        assert bedomning <= post["arende_efter"]
    for post in resultat.kraver_inte_underlag:  # rätt regel, och inom gränsen för pengar ut
        regel, rad = regler[post["regel"]], post["bankrad"]
        assert passar(rad, regel)
        if regel["riktning"] == "ut":
            assert 0 < -rad["belopp_ore"] <= regel["hogst_belopp_ore"]
        else:
            assert "hogst_belopp_ore" not in regel and rad["belopp_ore"] > 0
    return len([a for a in resultat.arenden if a["typ"] == "över gräns"])


def passar(rad, regel):
    """True om bankraden har regelns riktning och börjar med regelns mönster."""
    return (("in" if rad["belopp_ore"] > 0 else "ut") == regel["riktning"]
            and rad["referens"].startswith(regel.get("referens_borjar_med", ""))
            and rad["beskrivning"].startswith(regel.get("beskrivning_borjar_med", "")))


def test_fuzz_skadade_indata_ger_ratt_resultat_eller_matchningfel(tmp_path, kvartalet):
    rng = random.Random(20251025)
    sma_rader = [("F-1", "LEV-A", -12500, "2025-01-20"), ("F-2", "LEV-B", -500, "2025-01-21"),
                 ("IN-1", "X", 100, "2025-01-21"), ("X-1", "AVGIFT KONTO", -125, "2025-01-31"),
                 ("K-1", "KORT IN 2025-01-21", 300, "2025-01-22"), ("Z-1", "OKAND", -77, "2025-01-25"),
                 ("X-2", "AVGIFT AGARE-1", -150, "2025-01-25")]  # mot ägaren: passar regeln avgift, men kräver underlag
    sma_underlag = [underlag(), underlag(id="U-2", motpart="LEV-B", fakturanummer="F-2", belopp_ore=500,
                                         typ="kvitto", datum="2025-01-20"),
                    underlag(id="U-3", fakturanummer="F-3", belopp_ore=999)]
    motparter = ["LEV-A", "LEV-B", "lev-a", "LEV-TE", "KORTKOP BUTIK-STAD"]
    inte_en_regelbok = [None, FORMAT, MATCHNINGSFORMAT, las_matchningsformat(FORETAG / "matchning.json"), "regelbok",
                        object.__new__(Regelbok)]
    resultat_antal = stoppade = over_grans_antal = agarrader = 0
    for nummer in range(800):
        if nummer % 2:  # testdatans kvartal eller februari, med skadat format
            bankperiod = rng.choice([kvartalet["bankperiod"], kvartalet["februari"]])
            underlagen, format_ = kvartalet["period"], MATCHNINGSFORMAT
        else:  # små påhittade fall, där bankfilen och underlagen ändras och läses in igen
            format_ = FORMAT
            mapp = tmp_path / str(nummer)
            mapp.mkdir()
            poster = sma_underlag
            for _ in range(rng.choice([0, 1, 2])):
                poster = skada_underlag(rng, poster)
            rader = sma_rader
            for _ in range(rng.choice([0, 1, 2, 3])):
                rader = skada_rader(rng, rader, motparter)
            try:
                underlagen = period(mapp, *poster)
                bankperiod = bankrader(mapp, *rader)
            except (UnderlagFilFel, BankfilFel):
                stoppade += 1
                continue
        for _ in range(rng.choice([1, 1, 2, 3])):
            val = rng.random()
            if val < 0.15 and type(bankperiod) is Bankperiod:
                bankperiod = inte_en_bankperiod(rng, bankperiod)
            elif val < 0.85 and isinstance(format_, dict) and isinstance(format_.get("kraver_inte_underlag"), list) \
                    and isinstance(format_.get("tidsfonster_dagar"), dict):
                format_ = skada_format(rng, format_)
        fore_formatet = copy.deepcopy(format_)
        # Matchningen får formatet bara genom en regelbok. Ett trasigt format stoppas redan där, av
        # las_matchningsformat eller las_regelbok, och når aldrig matchningen.
        try:
            regelbok = regelbok_for(format_)
        except (MatchningsformatFel, RegelbokFel) as fel:
            assert str(fel).startswith(("Matchningsformatet", "Regelboken")), str(fel)
            stoppade += 1
            continue
        assert format_ == fore_formatet
        if rng.random() < 0.1:
            regelbok = rng.choice(inte_en_regelbok)
        # Ett bedömningsdatum före en bankrad stoppas (J9), så de flesta datum ligger efter raderna.
        bedomning = rng.choice(["2025-01-25", "2025-02-28", "2025-03-31", "2025-04-30", "2025-04-30", "9999-12-31",
                                "2025-13-01", None])
        fore = ogonblick(bankperiod)
        try:
            resultat = matcha_period(bankperiod, underlagen, regelbok, bedomning)
        except MatchningFel as fel:
            assert str(fel) and not str(fel).startswith(("Traceback", "'")), str(fel)
            stoppade += 1
        else:
            # Allt annat än en Bankperiod och en Regelbok ska ge MatchningFel.
            assert type(bankperiod) is Bankperiod and type(regelbok) is Regelbok
            over_grans_antal += ar_giltigt(resultat, bankperiod, underlagen, regelbok, bedomning)
            agarrader += len([rad for rad in bankperiod.rader if regelbok.ar_bankrad_mot_agare_eller_narstaende(rad)])
            resultat_antal += 1
        assert ogonblick(bankperiod) == fore  # indatan är oförändrad
    # Skydd: fuzzen ska ge både resultat och stopp, ibland rader över en gräns och ibland rader mot ägaren,
    # annars prövar den inte mycket.
    assert resultat_antal > 100 and stoppade > 150 and over_grans_antal > 10 and agarrader > 10, (
        resultat_antal, stoppade, over_grans_antal, agarrader)


def test_fuzz_skadad_matchningsfil_laddas_ratt_eller_stoppas(tmp_path):
    # Skador på själva filen matchning.json: varje försök ger ett kontrollerat format eller MatchningsformatFel.
    rng = random.Random(20251026)
    original = (FORETAG / "matchning.json").read_bytes()
    bitar = [b"\x00", b"\xff", b'"', b"{", b"}", b"[", b"]", b",", b":", b"9" * 5000, b"NaN", b"-1", b"true",
             b"[" * 3000, HOGER_TILL_VANSTER.encode("utf-8"), b"\\u0000", b'"ut"', b'"in"']
    laddade = stoppade = 0
    for nummer in range(300):
        data = original
        for _ in range(rng.choice([1, 2])):
            plats = rng.randrange(len(data) + 1)
            if rng.random() < 0.5:
                data = data[:plats] + rng.choice(bitar) + data[plats:]
            else:
                data = data[:plats] + data[plats + rng.randrange(1, 30):]
        fil = tmp_path / ("matchning_" + str(nummer) + ".json")
        fil.write_bytes(data)
        try:
            format_ = ladda_matchningsformat(fil)
        except MatchningsformatFel as fel:
            assert "Matchningsformatet" in str(fel)
            stoppade += 1
            continue
        assert format_ == kontrollera_matchningsformat(format_)
        laddade += 1
    assert laddade > 20 and stoppade > 150, (laddade, stoppade)


def test_bankfilfel_och_matchningsfel_ar_olika_fel():
    # Skydd: fuzzen ovan godtar bara MatchningFel. Det får inte vara samma klass som inläsningens fel.
    assert not issubclass(MatchningFel, (BankfilFel, UnderlagFilFel, MatchningsformatFel))
