"""Tester för Hugos beslut 2026-10-31 om granskning 27, Öppet 35 (GRANSKNING.md, granskning 27, M1).

Beslutet, skrivet av Hugo i chatten 2026-10-31: "Beloppet i debet ska kräva en bankrad. belopp_ore får bara stå i
kredit när delarna inte gör det." Byggt i _kontrollera_underlagen, sist, efter Öppet 33.

- Granskarens prov h1 i granskning 27: SYNT-U-2025-003 spegelvänd, 2440 debet 'belopp_ore', 4010 kredit
  'underlag_ore', 2641 kredit 'moms_ore', utan bankrad. Godtogs med alla kontrollerna "ok": en leverantörsfaktura
  bokförd som en kreditnota, fast kreditnotor är en egen dokumenttyp som inte finns (SPEC 11, Ö8).
- Granskarens prov h2: två fakturor under samma regel med exakt samma belopp, den enas 'belopp_ore' i debet på 2440
  och den andras i kredit på 2440, utan bankrad. Godtogs också: varje underlag står på exakt en rad, så regeln om
  högst en rad (Öppet 34) ser det inte.
- Kreditnotor: en riktig kreditnota kan inte läsas in i dag. Typen 'kreditnota' finns inte och negativa belopp stoppas
  i las_underlag, så ingen kreditnota når konteringsförslaget, och den nya regeln stoppar ingen. Testerna nedan visar
  hur de hanteras i dag. När Ö8 byggs måste regeln prövas igen.
- Flödena a och b bygger betalningen med 'belopp_ore' i debet tillsammans med bankraden, fakturan med 'belopp_ore' i
  kredit och delarna i debet, och kvittot utan 'belopp_ore', så deras förslag går igenom som förut. De testerna är
  skydd och var gröna också före rättelsen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot koden i b7d9fac (före rättelsen), körda i projektmappen innan
konteringsforslag.py ändrades, se PROGRESS.md.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import konteringsforslag  # noqa: E402
from konteringsforslag import KonteringsforslagFel  # noqa: E402
from las_underlag import UnderlagFilFel, las_underlagsperiod  # noqa: E402
from test_konteringsfloden import DATAMAPP, Korning  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_25 import ALLA_KONTROLLER, PROV_B  # noqa: E402
from test_beslut_granskning_26 import (  # noqa: E402
    INGAENDE_MOMS, LEVERANTORSSKULDER, forslag_for_hand, kalla, momsraden, prov_b_003, rad, roll, underlaget,
)

ANDRA = "SYNT-U-2025-009"  # samma regel som 003 (R-LEV-TE), annat datum och fakturanummer


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_lika(tmp_path_factory):
    """Testdatans underlag kopierade till testets mapp, där 009 har exakt 003:s belopp och momsrad (granskarens h2).

    Datum och fakturanummer är 009:s egna, så K4 flaggar inte paret."""
    mapp = tmp_path_factory.mktemp("lika_belopp") / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    tre = json.loads((mapp / (PROV_B + ".json")).read_text(encoding="utf-8"))
    sokvag = mapp / (ANDRA + ".json")
    nio = json.loads(sokvag.read_text(encoding="utf-8"))
    nio["belopp_ore"], nio["moms"] = tre["belopp_ore"], tre["moms"]
    sokvag.write_text(json.dumps(nio, ensure_ascii=False, indent=2), encoding="utf-8")
    return Korning(underlag=mapp)


def betalningen_for_hand(korning):
    """Betalningen av 003 som flöde a bygger den (2440 debet 'belopp_ore', 1940 kredit bankraden), för hand.

    Bankraden är radnummer 26 i bank_2025-02.csv, 2025-02-06, exakt 003:s belopp."""
    underlag, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    forslag = forslag_for_hand(korning, PROV_B, [
        rad(roll(korning, LEVERANTORSSKULDER), underlag["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(roll(korning, "bank"), 0, underlag["belopp_ore"], "lika",
            {"kalla": "bankrad", "id": bankraden["id"], "falt": "belopp_ore"}),
    ], "Betalningen för hand")
    forslag["verifikation"]["datum"] = bankraden["transaktionsdag"]
    forslag["kopplingar"]["bankrader"] = [{"id": bankraden["id"]}]
    return forslag


# --- Kreditnotor i dag (steg 1 i uppdraget): de når aldrig konteringsförslaget ---

def kreditnota(tmp_path, **andrat):
    """En mapp med ett enda underlag: 003 som kreditnota från samma leverantör, med andrat i stället för 003:s värden."""
    data = json.loads((DATAMAPP / "underlag" / (PROV_B + ".json")).read_text(encoding="utf-8"))
    data.update(id="SYNT-U-2025-K01", fakturanummer="SYNT-TE-K01", **andrat)
    mapp = tmp_path / "underlag"
    mapp.mkdir()
    (mapp / (data["id"] + ".json")).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return mapp


def test_kreditnota_som_egen_typ_stoppas_redan_nar_den_lases(tmp_path):
    # Ö8 säger att kreditnotor ska bli en egen dokumenttyp. Den finns inte: bara 'leverantorsfaktura' och 'kvitto'.
    with pytest.raises(UnderlagFilFel) as fel:
        las_underlagsperiod(kreditnota(tmp_path, typ="kreditnota"), "2025-01-01", "2025-03-31")
    assert "'typ' är 'kreditnota', men ska vara en av 'leverantorsfaktura', 'kvitto'" in str(fel.value)


def test_kreditnota_med_negativa_belopp_stoppas_redan_nar_den_lases(tmp_path):
    # Ö8 säger att alla belopp i en kreditnota är negativa. Negativa belopp stoppas tills det är bestämt.
    with pytest.raises(UnderlagFilFel) as fel:
        las_underlagsperiod(kreditnota(tmp_path, belopp_ore=-1673056, moms=[
            {"momssats": 12, "underlag_ore": -1493800, "moms_ore": -179256}]), "2025-01-01", "2025-03-31")
    assert "Negativa tal stoppas tills det är bestämt hur kreditnotor ska behandlas" in str(fel.value)


# --- Öppet 35: beloppet i debet kräver en bankrad ---

def test_o35_a_fakturan_spegelvand_utan_bankrad_stoppas(korning):
    # Granskarens h1: 2440 debet 16 730,56 kr ('belopp_ore'), 4010 kredit 14 938,00 kr ('underlag_ore') och 2641
    # kredit 1 792,56 kr ('moms_ore'). Täckningen går ihop och Öppet 31–34 godtar. Godtogs före rättelsen med alla
    # kontrollerna "ok". Nu stoppas den: beloppet i debet kräver en bankrad.
    underlag = underlaget(korning, PROV_B)
    momsrad = momsraden(underlag, 12)
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad(skulder, underlag["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), 0, momsrad["moms_ore"], "lika", kalla(PROV_B, "moms_ore", 12)),
    ], "h1 i granskning 27"), "ursprung", "rad 1 (konto " + skulder + ")", "'" + PROV_B + "'", "'belopp_ore'",
        "i debet", "ingen bankrad", "Öppet 35")
    assert "Öppet 33" not in text and "Öppet 34" not in text


def test_o35_b_tva_lika_stora_fakturor_mot_varandra_utan_bankrad_stoppas(korning, korning_lika):
    # Granskarens h2: 2440 debet 16 730,56 kr (003 'belopp_ore') och 2440 kredit 16 730,56 kr (009 'belopp_ore'), på
    # 009:s datum. Ingen kostnad och ingen moms bokförs, och fakturorna kvittas mot varandra. Godtogs före
    # rättelsen med alla kontrollerna "ok". Nu stoppas den: 003:s belopp står i debet utan bankrad.
    tre, nio = underlaget(korning_lika, PROV_B), underlaget(korning_lika, ANDRA)
    assert tre["belopp_ore"] == nio["belopp_ore"] and tre["moms"] == nio["moms"]
    # Det ändrade 009 ger inga nya K4-ärenden: samma ärenden som testdatan har utan ändringen.
    assert korning_lika.underlagsperiod.arenden == korning.underlagsperiod.arenden
    skulder = roll(korning_lika, LEVERANTORSSKULDER)
    forslag = forslag_for_hand(korning_lika, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, 0, nio["belopp_ore"], "lika", kalla(ANDRA, "belopp_ore")),
    ], "h2 i granskning 27")
    forslag["verifikation"]["datum"] = nio["datum"]
    forslag["kopplingar"]["underlag"] = [{"id": PROV_B}, {"id": ANDRA}]
    text = stoppas(korning_lika, forslag, "ursprung", "rad 1 (konto " + skulder + ")", "'" + PROV_B + "'",
                   "'belopp_ore'", "i debet", "ingen bankrad", "Öppet 35")
    assert "Öppet 34" not in text


def test_o35_ordningen_oppet_33_provas_fore_oppet_35(korning):
    # Den nya kontrollen ligger sist. Fakturan spegelvänd med momsen på 4010 bryter mot både Öppet 33 och Öppet 35,
    # och felet är Öppet 33:s.
    underlag = underlaget(korning, PROV_B)
    momsrad = momsraden(underlag, 12)
    text = stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad(roll(korning, LEVERANTORSSKULDER), underlag["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad("4010", 0, momsrad["moms_ore"], "lika", kalla(PROV_B, "moms_ore", 12)),
    ], "Ordningen"), "ursprung", "Öppet 33")
    assert "Öppet 35" not in text


# --- Öppet 35: beloppet i kredit bara när delarna inte står i kredit ---

def test_o35_beloppet_i_kredit_med_delarna_i_kredit_stoppas_av_den_nya_kontrollen(korning):
    # Den andra halvan av beslutet. I ett helt förslag stoppar täckningen (punkt 7) eller Öppet 34 det här först,
    # eftersom 'belopp_ore' redan räknar med alla delarna på sin sida, så kontrollen prövas här direkt, med raderna
    # ensamma. Kontoplanen är ett argument sedan steg 95 (Öppet 36 behöver rollen bank).
    verifikation = {"datum": "2025-01-07", "rader": [
        rad("4010", 1493800, 0, "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad("2641", 0, 179256, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad("2440", 0, 1673056, "lika", kalla(PROV_B, "belopp_ore")),
    ]}
    with pytest.raises(KonteringsforslagFel) as fel:
        konteringsforslag._kontrollera_beloppssidan(PROV_B, korning.kontoplan, {"bankrader": [{"id": "B"}]},
                                                    verifikation)
    text = str(fel.value)
    assert fel.value.kontroll == "ursprung"
    for del_ in ("rad 3 (konto 2440)", "'" + PROV_B + "'", "'belopp_ore'", "i kredit", "rad 2 (konto 2641)",
                 "'moms_ore'", "Öppet 35"):
        assert del_ in text, text


def test_o35_beloppet_i_kredit_med_delarna_i_debet_godtas_av_den_nya_kontrollen(korning):
    # Fakturan som flöde a bygger den: kontrollen säger ingenting, med eller utan bankrad.
    verifikation = {"datum": "2025-01-07", "rader": [
        rad("4010", 1493800, 0, "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad("2641", 179256, 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad("2440", 0, 1673056, "lika", kalla(PROV_B, "belopp_ore")),
    ]}
    for bankrader in ([], [{"id": "B"}]):
        assert konteringsforslag._kontrollera_beloppssidan(PROV_B, korning.kontoplan, {"bankrader": bankrader},
                                                           verifikation) is None


# --- Rätt förslag godtas: flödena och förslag för hand med rätt form ---

def test_skydd_fakturan_for_hand_godtas(korning):
    # Skydd (grönt också före rättelsen): fakturan för 003 med 'belopp_ore' i kredit och delarna i debet.
    assert skapa(korning, prov_b_003(korning)).kontroller == ALLA_KONTROLLER


def test_skydd_betalningen_med_bankrad_godtas_for_hand(korning):
    # Skydd (grönt också före rättelsen), granskarens s0: betalningen med 'belopp_ore' i debet och bankraden.
    assert skapa(korning, betalningen_for_hand(korning)).kontroller == ALLA_KONTROLLER


def test_skydd_flode_a_fakturan_och_betalningen_gar_igenom(korning):
    # Skydd (grönt också före rättelsen): flöde a bygger fakturan utan bankrad och betalningen med bankraden.
    fakturan, betalningen = korning.forslag_for(PROV_B)
    assert fakturan.kopplingar["bankrader"] == [] and len(betalningen.kopplingar["bankrader"]) == 1
    assert fakturan.kontroller == betalningen.kontroller == ALLA_KONTROLLER
    assert korning.arenden_for(PROV_B) == []


def test_skydd_flode_b_kvittot_med_bankrad_gar_igenom(korning):
    # Skydd (grönt också före rättelsen): kvittot 015 med kostnaden och momsen i debet och bankraden i kredit.
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    assert kvittot.kontroller == ALLA_KONTROLLER and len(kvittot.kopplingar["bankrader"]) == 1
    assert korning.arenden_for("SYNT-U-2025-015") == []


def test_skydd_varje_belopp_i_debet_i_flodena_har_en_bankrad(korning):
    # Skydd (grönt också före rättelsen): i hela körningen har varje förslag med ett underlags 'belopp_ore' i debet
    # exakt en rad på bankkontot i kredit, med samma belopp som raden i debet och med bara bankrader som källor
    # (granskarens f4 i granskning 28; skärpt i steg 95 efter L1, förut prövades bara att förslaget hade någon
    # bankrad), och ingen rad med 'belopp_ore' i kredit har underlagets delar i kredit. Det är därför flödena inte
    # berörs av Öppet 35 och 36.
    kontoplan = korning.kontoplan
    med_underlag = [forslag for forslag in korning.resultat.forslag if forslag.kopplingar["underlag"]]
    assert med_underlag
    for forslag in med_underlag:
        rader = forslag.verifikation["rader"]
        for rad_ in rader:
            for kalla_ in rad_["ursprung"]["fran"]:
                if kalla_["kalla"] != "underlag" or kalla_["falt"] != "belopp_ore":
                    continue
                if rad_["debet_ore"] > 0:
                    assert forslag.kopplingar["bankrader"], forslag.forslag_id
                    pa_bankkontot = [annan for annan in rader
                                     if annan["kredit_ore"] > 0 and ("bank", None) in kontoplan.kontots_roller(annan["konto"])]
                    assert len(pa_bankkontot) == 1, forslag.forslag_id
                    assert pa_bankkontot[0]["kredit_ore"] == rad_["debet_ore"], forslag.forslag_id
                    assert all(kalla2["kalla"] == "bankrad" for kalla2 in pa_bankkontot[0]["ursprung"]["fran"]), \
                        forslag.forslag_id
                else:
                    assert not any(annan["kredit_ore"] > 0 and kalla2["kalla"] == "underlag"
                                   and kalla2["id"] == kalla_["id"] and kalla2["falt"] != "belopp_ore"
                                   for annan in rader for kalla2 in annan["ursprung"]["fran"]), forslag.forslag_id


# --- Dokumentationen i koden ---

def test_koden_namner_regeln():
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 35" in kod and "granskning 27" in kod
