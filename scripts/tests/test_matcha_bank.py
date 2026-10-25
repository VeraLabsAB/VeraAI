"""Tester för matchningen av bankrader mot underlag (matcha_bank.py, K3).

Testdatan är SYNTETISK (Syntet Testbutik AB, 2025-Q1). Rätt svar står i facit.json. De små
bankfilerna och underlagen nedan är påhittade och skrivs i en tillfällig mapp för varje test. De
läses alltid med las_bankfil och las_underlagsperiod, så att matchningen får samma sorts indata
som i drift.
"""

import copy
import datetime as dt
import json
import random
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"
FORETAG = AGENT / "foretag" / "syntet-testbutik"

sys.path.insert(0, str(AGENT / "scripts"))

import matcha_bank  # noqa: E402
from las_bank import BankfilFel, ladda_bankformat, las_bankfil  # noqa: E402
from las_kassa import normalisera_kassaregister  # noqa: E402
from las_matchningsformat import MatchningsformatFel, kontrollera_matchningsformat, ladda_matchningsformat  # noqa: E402
from las_underlag import UnderlagFilFel, Underlagsperiod, las_underlagsperiod  # noqa: E402
from matcha_bank import MatchningFel, Matchningsresultat, matcha_period  # noqa: E402

BANKFORMAT = ladda_bankformat(FORETAG / "bankformat.json")
MATCHNINGSFORMAT = ladda_matchningsformat(FORETAG / "matchning.json")
GRUPPER_FOR_BANKRADER = ("matchningar", "arenden", "kraver_inte_underlag", "vantande")

# Osynliga tecken byggs med chr(), så att de syns i koden (test_inga_dolda_tecken.py).
OSYNLIGT_MELLANSLAG = chr(0x200B)
HOGER_TILL_VANSTER = chr(0x202E)


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
    månadens utgående, som i test_las_bank.py. Saldona kommer från facit.

    Mars stoppas av K1 på den planterade raden (100,00 kr för högt saldo). Därför rättas raden i en
    kopia: saldot byts mot det rätta enligt facit. Inget annat i filen ändras.
    """
    bank = facit()["bank"]
    januari = las_bankfil(DATAMAPP / "bank_2025-01.csv", BANKFORMAT, bank["2025-01"]["ingaende_saldo_ore"],
                          bank["2025-01"]["utgaende_saldo_ore"])
    februari = las_bankfil(DATAMAPP / "bank_2025-02.csv", BANKFORMAT, januari[-1]["saldo_efter_ore"],
                           bank["2025-02"]["utgaende_saldo_ore"])
    fel = planterat("brott_i_saldokedjan")
    rader = (DATAMAPP / fel["filnamn"]).read_text(encoding="utf-8").split("\n")
    felrad = [nummer for nummer, rad in enumerate(rader) if rad.startswith(str(fel["rad"]) + ",")]
    assert len(felrad) == 1 and rader[felrad[0]].endswith("," + kr(fel["visat_saldo_ore"]))
    rader[felrad[0]] = rader[felrad[0]][:-len(kr(fel["visat_saldo_ore"]))] + kr(fel["ratt_saldo_ore"])
    rattad = mapp / fel["filnamn"]
    rattad.write_text("\n".join(rader), encoding="utf-8")
    mars = las_bankfil(rattad, BANKFORMAT, februari[-1]["saldo_efter_ore"], bank["2025-03"]["utgaende_saldo_ore"])
    return januari, februari, mars


@pytest.fixture(scope="module")
def kvartalet(tmp_path_factory):
    januari, februari, mars = las_kvartalets_bankrader(tmp_path_factory.mktemp("bank"))
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-01-01", "2025-03-31")
    return {"rader": januari + februari + mars, "februari": februari, "period": period}


def bankrad_utan_underlag(kvartalet):
    """Den planterade bankraden utan underlag, ur februarifilen."""
    fel = planterat("bankrad_utan_underlag")
    assert fel["manad"] == "2025-02" and fel["filnamn"] == "bank_2025-02.csv"
    rad = kvartalet["februari"][fel["rad"] - 1]
    assert (rad["radnr"], rad["belopp_ore"]) == (fel["rad"], fel["belopp_ore"]) == (85, -35100)
    assert rad["beskrivning"] == "KORTKOP BUTIK-FORBRUKNING" and rad["transaktionsdag"] == "2025-02-18"
    return rad


def test_kvartalet_ger_exakt_det_planterade_felet_som_saknat_underlag(kvartalet):
    rad = bankrad_utan_underlag(kvartalet)
    # Mer än 7 dagar efter alla bankrader i kvartalet.
    resultat = matcha_period(kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT, "2025-04-30")
    assert len(resultat.arenden) == 1
    arende = resultat.arenden[0]
    assert (arende["kontroll"], arende["typ"], arende["kandidater"]) == ("K3", "saknat underlag", ())
    assert dict(arende["bankrad"]) == rad
    assert arende["bankrad"]["kalla_fil"] == kvartalet["februari"][0]["kalla_fil"]  # februarifilen
    assert resultat.vantande == ()
    # Facit säger att felet fångas av K3.
    assert planterat("bankrad_utan_underlag")["kontroll"] == arende["kontroll"]


def test_kvartalet_fore_sju_dagar_ger_inget_arende_bara_att_raden_vantar(kvartalet):
    rad = bankrad_utan_underlag(kvartalet)
    # 7 dagar efter transaktionsdagen 2025-02-18: inte mer än 7 dagar, så raden väntar.
    for dag in ("2025-02-18", "2025-02-20", "2025-02-25"):
        resultat = matcha_period(kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT, dag)
        assert resultat.arenden == (), dag
        assert [(dict(post["bankrad"]), post["arende_efter"]) for post in resultat.vantande] == [(rad, "2025-02-25")]
    # Dagen efter blir den ett ärende.
    resultat = matcha_period(kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT, "2025-02-26")
    assert [(a["typ"], a["bankrad"]["id"]) for a in resultat.arenden] == [("saknat underlag", rad["id"])]
    assert resultat.vantande == ()


def test_dubbletten_kommer_fran_k4_och_inte_fran_matchningen(kvartalet):
    fel = planterat("dubblett_leverantorsfaktura")
    period = kvartalet["period"]
    assert [(a["kontroll"], a["id"]) for a in period.arenden] == [("K4", fel["id"])]
    resultat = matcha_period(kvartalet["rader"], period, MATCHNINGSFORMAT, "2025-04-30")
    alla_id = json.dumps([list(map(dict, grupp)) for grupp in resultat], default=dict)
    assert fel["id"] not in alla_id  # dubbletten finns inte i matchningen alls
    # Originalet matchas med den enda betalningen.
    original = [m for m in resultat.matchningar if m["underlag"]["id"] == fel["original_id"]]
    assert len(original) == 1 and original[0]["bankrad"]["referens"] == original[0]["underlag"]["fakturanummer"]
    assert all(a["typ"] != "tvetydig" for a in resultat.arenden)


def test_kvartalets_matchningar_ar_ratt(kvartalet):
    resultat = matcha_period(kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT, "2025-04-30")
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


def kontrollera_grupperna(resultat, bankrader, period):
    """Varje bankrad finns i exakt en grupp. Varje underlag i perioden finns i exakt en matchning eller
    bland de oavstämda, och aldrig i två matchningar."""
    id_per_grupp = [post["bankrad"]["id"] for grupp in GRUPPER_FOR_BANKRADER for post in getattr(resultat, grupp)]
    assert sorted(id_per_grupp) == sorted(rad["id"] for rad in bankrader)
    matchade = [m["underlag"]["id"] for m in resultat.matchningar]
    assert len(matchade) == len(set(matchade))
    oavstamda = [post["id"] for post in resultat.oavstamda_underlag]
    assert sorted(matchade + oavstamda) == sorted(post["id"] for post in period.underlag)


def test_varje_bankrad_i_testdatan_finns_i_exakt_en_grupp(kvartalet):
    assert len(kvartalet["rader"]) == sum(manad["antal_rader"] for manad in facit()["bank"].values()) == 395
    for dag in ("2025-01-01", "2025-02-25", "2025-02-26", "2025-03-31", "2025-04-30"):
        resultat = matcha_period(kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT, dag)
        kontrollera_grupperna(resultat, kvartalet["rader"], kvartalet["period"])


def test_en_manad_i_taget_ger_samma_planterade_fel(kvartalet):
    # Februari för sig ger samma ärende. Underlagen från januari behövs, eftersom januaris fakturor
    # betalas i februari. Utan dem blir de bankraderna ärenden (nästa test).
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-01-01", "2025-02-28")
    resultat = matcha_period(kvartalet["februari"], period, MATCHNINGSFORMAT, "2025-03-31")
    assert [(a["typ"], a["bankrad"]["radnr"]) for a in resultat.arenden] == [("saknat underlag", 85)]


def test_utan_underlagen_fran_januari_blir_februaris_betalningar_arenden(kvartalet):
    # Skydd: testet ovan prövar verkligen något. Betalningarna av januaris fakturor saknar då underlag.
    period = las_underlagsperiod(DATAMAPP / "underlag", "2025-02-01", "2025-02-28")
    resultat = matcha_period(kvartalet["februari"], period, MATCHNINGSFORMAT, "2025-03-31")
    saknade = [a["bankrad"] for a in resultat.arenden if a["typ"] == "saknat underlag"]
    assert 85 in [rad["radnr"] for rad in saknade]
    assert [rad for rad in saknade if rad["radnr"] != 85]
    assert all(rad["referens"].startswith("SYNT-") for rad in saknade if rad["radnr"] != 85)


# --- Små påhittade fall i en tillfällig mapp ---

FORMAT = {
    "kraver_inte_underlag": [
        {"namn": "insattning", "riktning": "in", "referens_borjar_med": "IN-"},
        {"namn": "avgift", "riktning": "ut", "beskrivning_borjar_med": "AVGIFT"},
        {"namn": "kort", "riktning": "in", "referens_borjar_med": "K-", "beskrivning_borjar_med": "KORT IN"},
    ],
    "tidsfonster_dagar": {"leverantorsfaktura": 30, "kvitto": 2},
    "saknat_underlag_efter_dagar": 7,
}
RUBRIK = "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo"


def bankrader(mapp, *rader, namn="bank.csv"):
    """Skriver en bankfil och läser den med las_bankfil. Varje rad är (referens, beskrivning,
    belopp_ore, transaktionsdag) eller med bokforingsdag sist. Saldot börjar på 0."""
    saldo, text = 0, [RUBRIK]
    for nummer, rad in enumerate(rader, start=1):
        referens, beskrivning, belopp, transaktionsdag = rad[:4]
        bokforingsdag = rad[4] if len(rad) > 4 else transaktionsdag
        saldo += belopp
        text.append(",".join([str(nummer), bokforingsdag, transaktionsdag, referens, beskrivning, kr(belopp),
                              kr(saldo)]))
    fil = mapp / namn
    fil.write_text("\n".join(text) + "\n", encoding="utf-8")
    return las_bankfil(fil, BANKFORMAT, 0, saldo)


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


def matcha(rader, underlagen, bedomning="2025-12-31", format_=None):
    resultat = matcha_period(rader, underlagen, FORMAT if format_ is None else format_, bedomning)
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
    for dag in ("2025-02-01", "2025-03-01", "2025-03-08"):  # 2025-03-08 är 7 dagar efter
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
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", datum="2025-02-09"))
    for referens, resultat in [
        ("F-2", tomt(matchningar=[(1, "U-2")], oavstamda=["U-1"])),
        ("f-2", tomt(matchningar=[(1, "U-2")], oavstamda=["U-1"])),            # normaliseras som motparten
        ("F-1", tomt(matchningar=[(1, "U-1")], oavstamda=["U-2"])),
        ("F-2X", tomt(arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])),  # inte hela ord
        ("F-1 F-2", tomt(arenden=[(1, "tvetydig", ("U-1", "U-2"))], oavstamda=["U-1", "U-2"])),
    ]:
        rader = bankrader(tmp_path, (referens, "LEV-A", -12500, "2025-02-09"))
        assert sammanfattning(matcha(rader, underlagen)) == resultat, referens


def test_fakturanumret_avgor_bara_nar_det_pekar_ut_exakt_ett_underlag(tmp_path):
    # Tre kandidater, och två fakturanummer står i texten. Fakturanumret avgör inte, och människan
    # får se alla tre kandidaterna i ärendet.
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2"),
                        underlag(id="U-3", fakturanummer="F-3"))
    rader = bankrader(tmp_path, ("F-1 F-2", "LEV-A", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, underlagen)) == tomt(
        arenden=[(1, "tvetydig", ("U-1", "U-2", "U-3"))], oavstamda=["U-1", "U-2", "U-3"])


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


def test_flera_bankfiler_och_tom_lista(tmp_path):
    forsta = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), namn="a.csv")
    andra = bankrader(tmp_path, ("IN-1", "X", 100, "2025-02-01"), namn="b.csv")
    underlagen = period(tmp_path, underlag())
    assert sammanfattning(matcha(forsta + andra, underlagen)) == tomt(
        matchningar=[(1, "U-1")], kraver_inte=[(1, "insattning")])
    assert sammanfattning(matcha(tuple(forsta), underlagen)) == tomt(matchningar=[(1, "U-1")])
    assert sammanfattning(matcha([], underlagen)) == tomt(oavstamda=["U-1"])


# --- Indatan kontrolleras ---

def en_rad(tmp_path):
    return bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"))


@pytest.mark.parametrize("varde, text", [
    (None, "Bankraderna ska vara en lista med rader från las_bankfil, inte None"),
    ({"id": "x"}, "Bankraderna ska vara en lista med rader från las_bankfil, inte ett objekt"),
    ("bankrader", "Bankraderna ska vara en lista med rader från las_bankfil, inte 'bankrader'"),
    (iter([]), "Bankraderna ska vara en lista med rader från las_bankfil, inte list_iterator"),
    ([None], "Bankrad nummer 1 i listan ska vara en rad från las_bankfil, inte None"),
    ([["id"]], "Bankrad nummer 1 i listan ska vara en rad från las_bankfil, inte en lista"),
])
def test_bankrader_av_fel_typ_stoppas(tmp_path, varde, text):
    with pytest.raises(MatchningFel, match="^" + text):
        matcha_period(varde, period(tmp_path), FORMAT, "2025-12-31")


@pytest.mark.parametrize("andring, text", [
    (lambda rad: rad.pop("radnr"), "har inte uppgifterna som las_bankfil ger"),
    (lambda rad: rad.update(extra=1), "har inte uppgifterna som las_bankfil ger"),
    (lambda rad: rad.update({1: 1}), "har inte uppgifterna som las_bankfil ger"),
    (lambda rad: rad.update(belopp_ore=-125.0), "'belopp_ore' ska vara ett heltal, inte ett decimaltal"),
    (lambda rad: rad.update(belopp_ore="-12500"), "'belopp_ore' ska vara ett heltal, inte '-12500'"),
    (lambda rad: rad.update(saldo_efter_ore=True), "'saldo_efter_ore' ska vara ett heltal, inte ett sanningsvärde"),
    (lambda rad: rad.update(radnr=None), "'radnr' ska vara ett heltal, inte None"),
    (lambda rad: rad.update(id=""), "'id' får inte vara tomt"),
    (lambda rad: rad.update(id=5), "'id' ska vara text, inte 5"),
    (lambda rad: rad.update(referens=None), "'referens' ska vara text, inte None"),
    (lambda rad: rad.update(beskrivning=b"LEV-A"), "'beskrivning' ska vara text, inte bytes"),
    (lambda rad: rad.update(kalla_fil=["x"]), "'kalla_fil' ska vara text, inte en lista"),
    (lambda rad: rad.update(transaktionsdag="2025-02-30"),
     "'transaktionsdag' ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte '2025-02-30'"),
    (lambda rad: rad.update(bokforingsdag="20250120"), "'bokforingsdag' ska vara ett giltigt datum"),
    (lambda rad: rad.update(bokforingsdag=dt.date(2025, 1, 20)), "'bokforingsdag' ska vara ett giltigt datum"),
])
def test_trasiga_bankrader_stoppas(tmp_path, andring, text):
    rader = en_rad(tmp_path)
    andring(rader[0])
    with pytest.raises(MatchningFel) as fel:
        matcha_period(rader, period(tmp_path), FORMAT, "2025-12-31")
    assert str(fel.value).startswith("Bankrad nummer 1 i listan") and text in str(fel.value), str(fel.value)


def test_samma_bankrad_tva_ganger_stoppas(tmp_path):
    # Till exempel samma bankfil inläst två gånger.
    rader = en_rad(tmp_path)
    with pytest.raises(MatchningFel, match="Bankraden med id '" + rader[0]["id"] + "' finns flera gånger"):
        matcha_period(rader + rader, period(tmp_path), FORMAT, "2025-12-31")
    with pytest.raises(MatchningFel, match="finns flera gånger"):
        matcha_period(rader + [dict(rader[0], radnr=2)], period(tmp_path), FORMAT, "2025-12-31")


def test_underlagen_ska_vara_en_underlagsperiod(tmp_path):
    rader = en_rad(tmp_path)
    underlagen = period(tmp_path, underlag())

    class Underklass(Underlagsperiod):
        pass

    for varde, text in [(underlagen.underlag, "en lista"), (None, "None"), ({}, "ett objekt"),
                        (Underklass.__new__(Underklass), "Underklass")]:
        with pytest.raises(MatchningFel, match="^Underlagen ska vara en Underlagsperiod från las_underlagsperiod,"
                                               " inte " + text):
            matcha_period(rader, varde, FORMAT, "2025-12-31")


@pytest.mark.parametrize("varde", [None, "", "2025-1-01", "2025-02-30", "31/12/2025", 20251231,
                                   dt.date(2025, 12, 31), " 2025-12-31", "２０２５-12-31"])
def test_bedomningsdatum_ska_vara_ett_giltigt_datum(tmp_path, varde):
    with pytest.raises(MatchningFel, match="^Bedömningsdatumet ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD"):
        matcha_period(en_rad(tmp_path), period(tmp_path), FORMAT, varde)


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
        matcha_period(en_rad(tmp_path), period(tmp_path), FORMAT, "20251231")
    rader = en_rad(tmp_path)
    rader[0]["transaktionsdag"] = "20250120"
    with pytest.raises(MatchningFel, match="'transaktionsdag' ska vara ett giltigt datum"):
        matcha_period(rader, period(tmp_path), FORMAT, "2025-12-31")


@pytest.mark.parametrize("andring, text", [
    (lambda f: f.pop("tidsfonster_dagar"), "saknar nyckeln 'tidsfonster_dagar'"),
    (lambda f: f.update(saknat_underlag_efter_dagar=-1), "'saknat_underlag_efter_dagar' ska vara ett heltal"),
    (lambda f: f["tidsfonster_dagar"].update(kvitto=True), "tidsfönstret för 'kvitto' ska vara ett heltal"),
    (lambda f: f["kraver_inte_underlag"][0].update(riktning="IN"), "'riktning' ska vara en av 'in', 'ut'"),
    (lambda f: f.update({7: 7}), "har en nyckel som inte är text"),
])
def test_trasigt_format_stoppas_aven_nar_det_skickas_direkt(tmp_path, andring, text):
    # Formatet kontrolleras igen i matcha_period, så att ett format som har ändrats efter
    # ladda_matchningsformat aldrig används.
    format_ = copy.deepcopy(FORMAT)
    andring(format_)
    with pytest.raises(MatchningFel) as fel:
        matcha_period(en_rad(tmp_path), period(tmp_path), format_, "2025-12-31")
    assert type(fel.value) is MatchningFel and text in str(fel.value), str(fel.value)


# --- Indatan ändras aldrig, och resultatet går inte att ändra ---

def test_indatan_andras_aldrig(tmp_path):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 100, "2025-01-20"),
                      ("X-1", "OKAND", -1, "2025-01-20"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", belopp_ore=1))
    format_ = copy.deepcopy(FORMAT)
    fore = (copy.deepcopy(rader), underlagen.underlag, underlagen.arenden, copy.deepcopy(format_))
    lista = rader
    resultat = matcha_period(rader, underlagen, format_, "2025-12-31")
    assert (rader, underlagen.underlag, underlagen.arenden, format_) == fore
    assert rader is lista and all(type(rad) is dict for rad in rader)
    # Resultatet är en kopia: att ändra indatan efteråt ändrar inte resultatet.
    rader[0]["belopp_ore"] = 1
    rader.append({})
    assert resultat.matchningar[0]["bankrad"]["belopp_ore"] == -12500
    assert len([post for grupp in GRUPPER_FOR_BANKRADER for post in getattr(resultat, grupp)]) == 3


def test_resultatet_gar_inte_att_andra(tmp_path):
    rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("IN-1", "X", 100, "2025-01-20"),
                      ("X-1", "OKAND", -1, "2025-01-20"), ("X-2", "OKAND", -2, "2025-12-30"))
    underlagen = period(tmp_path, underlag(), underlag(id="U-2", fakturanummer="F-2", belopp_ore=3))
    resultat = matcha_period(rader, underlagen, FORMAT, "2025-12-31")
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
    rader = copy.deepcopy(rader)
    sort = rng.randrange(9)
    if sort == 0 and rader:  # byt ut ett värde
        rad = rng.choice(rader)
        rad[rng.choice(sorted(rad))] = rng.choice(FARLIGA_VARDEN)
    elif sort == 1 and rader:  # ta bort eller lägg till en nyckel
        rad = rng.choice(rader)
        if rng.random() < 0.5:
            del rad[rng.choice(sorted(rad))]
        else:
            rad[rng.choice(["extra", "Id", 1, None])] = 1
    elif sort == 2 and rader:  # samma rad två gånger
        rader.insert(rng.randrange(len(rader) + 1), copy.deepcopy(rng.choice(rader)))
    elif sort == 3 and rader:  # en rad som inte är en rad
        rader[rng.randrange(len(rader))] = rng.choice(FARLIGA_VARDEN)
    elif sort == 4:  # hela listan byts ut
        return rng.choice([None, {}, "rader", 5, tuple(rader), rader[:1], []])
    elif sort == 5 and rader:  # en giltig ändring: belopp, datum, motpart eller mönster
        rad = rng.choice(rader)
        val = rng.randrange(4)
        if val == 0:
            rad["belopp_ore"] = rng.choice([-rad["belopp_ore"], rad["belopp_ore"] + 1, 0, -12500, 100])
        elif val == 1:
            rad["transaktionsdag"] = rng.choice(["2025-01-01", "2025-01-10", "2025-02-09", "9999-12-31", "0001-01-01"])
        elif val == 2:
            rad["beskrivning"] = rng.choice(motparter + ["X " + rng.choice(motparter), "AVGIFT X", "KORT IN"])
        else:
            rad["referens"] = rng.choice(["IN-1", "K-1", "F-1", "", rng.choice(motparter)])
        rad["id"] = rad["id"] + "-" + str(rng.randrange(10 ** 6))  # ett nytt id, som efter en ändring i filen
    elif sort == 6 and rader:  # byt plats på två rader
        a, b = rng.randrange(len(rader)), rng.randrange(len(rader))
        rader[a], rader[b] = rader[b], rader[a]
    elif sort == 7 and rader:  # ta bort en rad
        del rader[rng.randrange(len(rader))]
    return rader


def skada_format(rng, format_):
    format_ = copy.deepcopy(format_)
    sort = rng.randrange(7)
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
                          "okand"])] = rng.choice(FARLIGA_VARDEN + ["in", "ut"])
    elif sort == 3:  # en regel till, som kan krocka med en annan
        format_["kraver_inte_underlag"].append(
            {"namn": rng.choice(["ny", "insattning"]), "riktning": rng.choice(["in", "ut"]),
             rng.choice(["referens_borjar_med", "beskrivning_borjar_med"]): rng.choice(["IN-1", "Q", "K", "AVG"])})
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


def ar_giltigt(resultat, rader, underlagen, format_, bedomning):
    """Ett resultat ska alltid följa reglerna i matcha_bank.py."""
    format_ = kontrollera_matchningsformat(format_)
    kontrollera_grupperna(resultat, rader, underlagen)
    dag = dt.date.fromisoformat(bedomning)
    for matchning in resultat.matchningar:
        rad, post = matchning["bankrad"], matchning["underlag"]
        assert rad["belopp_ore"] == -post["belopp_ore"]
        forsta = dt.date.fromisoformat(post["datum"])
        assert 0 <= (dt.date.fromisoformat(rad["transaktionsdag"]) - forsta).days <= format_["tidsfonster_dagar"][
            post["typ"]]
        assert normalisera_kassaregister(post["motpart"]) in (normalisera_kassaregister(rad["beskrivning"])
                                                              + normalisera_kassaregister(rad["referens"]))
    for arende in resultat.arenden:
        assert (arende["typ"] == "tvetydig") == bool(arende["kandidater"])
        if arende["typ"] == "saknat underlag":
            assert (dag - dt.date.fromisoformat(arende["bankrad"]["transaktionsdag"])).days > format_[
                "saknat_underlag_efter_dagar"]
    for post in resultat.vantande:
        assert bedomning <= post["arende_efter"]
    namn = {regel["namn"] for regel in format_["kraver_inte_underlag"]}
    assert all(post["regel"] in namn for post in resultat.kraver_inte_underlag)


def test_fuzz_skadade_indata_ger_ratt_resultat_eller_matchningfel(tmp_path, kvartalet):
    rng = random.Random(20251025)
    sma_rader = bankrader(tmp_path, ("F-1", "LEV-A", -12500, "2025-01-20"), ("F-2", "LEV-B", -500, "2025-01-21"),
                          ("IN-1", "X", 100, "2025-01-21"), ("X-1", "AVGIFT KONTO", -125, "2025-01-31"),
                          ("K-1", "KORT IN 2025-01-21", 300, "2025-01-22"), ("Z-1", "OKAND", -77, "2025-01-25"))
    sma_underlag = [underlag(), underlag(id="U-2", motpart="LEV-B", fakturanummer="F-2", belopp_ore=500,
                                         typ="kvitto", datum="2025-01-20"),
                    underlag(id="U-3", fakturanummer="F-3", belopp_ore=999)]
    motparter = ["LEV-A", "LEV-B", "lev-a", "LEV-TE", "KORTKOP BUTIK-STAD"]
    resultat_antal = stoppade = 0
    for nummer in range(600):
        if nummer % 2:  # testdatans kvartal, med skadade bankrader eller skadat format
            rader, underlagen, format_ = kvartalet["rader"], kvartalet["period"], MATCHNINGSFORMAT
        else:  # små påhittade fall, där även underlagen skadas och läses in igen
            rader, format_ = sma_rader, FORMAT
            mapp = tmp_path / str(nummer)
            mapp.mkdir()
            poster = sma_underlag
            for _ in range(rng.choice([0, 1, 2])):
                poster = skada_underlag(rng, poster)
            try:
                underlagen = period(mapp, *poster)
            except UnderlagFilFel:
                stoppade += 1
                continue
        for _ in range(rng.choice([1, 1, 2, 3])):
            val = rng.random()
            if val < 0.5 and isinstance(rader, list):
                rader = skada_rader(rng, rader, motparter)
            elif val < 0.85 and isinstance(format_, dict) and isinstance(format_.get("kraver_inte_underlag"), list) \
                    and isinstance(format_.get("tidsfonster_dagar"), dict):
                format_ = skada_format(rng, format_)
        bedomning = rng.choice(["2025-01-25", "2025-02-28", "2025-04-30", "9999-12-31", "2025-13-01", None])
        fore = copy.deepcopy((rader, format_))
        try:
            resultat = matcha_period(rader, underlagen, format_, bedomning)
        except MatchningFel as fel:
            assert str(fel) and not str(fel).startswith(("Traceback", "'")), str(fel)
            stoppade += 1
        else:
            ar_giltigt(resultat, rader, underlagen, format_, bedomning)
            resultat_antal += 1
        assert copy.deepcopy((rader, format_)) == fore  # indatan är oförändrad
    # Skydd: fuzzen ska ge både resultat och stopp, annars prövar den inte mycket.
    assert resultat_antal > 100 and stoppade > 150, (resultat_antal, stoppade)


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
