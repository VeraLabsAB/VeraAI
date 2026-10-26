"""Tester för kontoplanen (las_kontoplan.py, foretag/<namn>/kontoplan.json).

Kontoplanen för testföretaget är SYNTETISK. De små kontoplanerna nedan är påhittade, med påhittade
kontonummer (som 0101 och 9001) och påhittade satser (7 och 9 procent), och skrivs i en tillfällig
mapp för varje test.
"""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
KONTOPLAN_FIL = AGENT / "foretag" / "syntet-testbutik" / "kontoplan.json"

sys.path.insert(0, str(AGENT / "scripts"))

from las_kontoplan import ROLLER, Kontoplan, KontoplanFel, las_kontoplan  # noqa: E402
from test_las_momssatser import DOLDA, json_block_i_design  # noqa: E402


def konto(nummer, namn="påhittat", **giltighet):
    return {"nummer": nummer, "namn": namn, **giltighet}


def plan(**andrat):
    """En felfri kontoplan, med de ändringar som anges."""
    data = {
        "anteckning": "påhittad",
        "status": "PÅHITTAD",
        "konton": [konto("0101", "bank"), konto("0202", "skulder"), konto("0303", "ingående moms"),
                   konto("0707", "utgående moms 7"), konto("0909", "utgående moms 9"), konto("9001", "kostnad")],
        "roller": {"bank": "0101", "leverantorsskulder": "0202", "ingaende_moms": "0303",
                   "utgaende_moms_per_sats": {"7": "0707", "9": "0909"}},
    }
    data.update(andrat)
    return data


def roller(**andrat):
    data = plan()
    data["roller"].update(andrat)
    return data


def utan(data, nyckel):
    return {k: v for k, v in data.items() if k != nyckel}


def skriv(mapp, data, ascii=False):
    fil = mapp / "kontoplan.json"
    fil.write_text(json.dumps(data, ensure_ascii=ascii), encoding="utf-8")
    return fil


def stoppas(mapp, data, *texter, ascii=False):
    """Kräver KontoplanFel från filen, med texterna i meddelandet."""
    fil = skriv(mapp, data, ascii)
    with pytest.raises(KontoplanFel) as fel:
        las_kontoplan(fil)
    meddelande = str(fel.value)
    assert meddelande.startswith("Kontoplanen i " + str(fil)), meddelande
    for text in texter:
        assert text in meddelande, meddelande
    return meddelande


# --- Testföretagets fil ---

def test_testforetagets_fil_laddas():
    kontoplan = las_kontoplan(KONTOPLAN_FIL)
    assert kontoplan.status == "SYNTETISK"
    assert len(kontoplan.konton) == 15
    datum = "2025-02-10"
    roller_ = {roll: kontoplan.rollens_konto(roll, datum) for roll in ROLLER if roll != "utgaende_moms_per_sats"}
    assert roller_ == {"bank": "1940", "leverantorsskulder": "2440", "ingaende_moms": "2641"}
    assert kontoplan.utgaende_moms_konto(25, datum) == "2611"
    assert kontoplan.utgaende_moms_konto(12, datum) == "2621"
    assert kontoplan.kontots_namn("1940", datum) == "Företagskonto"


def test_testforetagets_fil_har_exakt_vardena_i_design():
    # Inga nya värden har hittats på: filen är exakt exemplet i DESIGN-regelbok.md avsnitt 2.
    assert json.loads(KONTOPLAN_FIL.read_text(encoding="utf-8")) == json_block_i_design("roller")


def test_testforetagets_fil_ar_markt_syntetisk():
    data = json.loads(KONTOPLAN_FIL.read_text(encoding="utf-8"))
    assert data["status"] == "SYNTETISK" and "SYNTETISK" in data["anteckning"]
    assert "INTE verifierade" in data["anteckning"]


# --- Uppslagen ---

def test_konto_med_giltighetstid(tmp_path):
    data = plan()
    data["konton"].append(konto("9002", fran="2024-01-01", till="2024-12-31"))
    data["konton"].append(konto("9003", fran="2025-01-01"))
    data["konton"].append(konto("9004", till=None))
    kontoplan = las_kontoplan(skriv(tmp_path, data))
    assert kontoplan.kontots_namn("9002", "2024-01-01") == "påhittat"
    assert kontoplan.kontots_namn("9002", "2024-12-31") == "påhittat"
    assert kontoplan.kontots_namn("9003", "2099-01-01") == "påhittat"
    assert kontoplan.kontots_namn("9004", "1900-01-01") == "påhittat"
    for nummer, datum in [("9002", "2023-12-31"), ("9002", "2025-01-01"), ("9003", "2024-12-31")]:
        with pytest.raises(KontoplanFel, match="Kontot " + nummer + " gäller inte på " + datum):
            kontoplan.kontots_namn(nummer, datum)


def test_rollens_konto_maste_galla_pa_datumet(tmp_path):
    data = plan()
    data["konton"][0] = konto("0101", "bank", till="2024-12-31")
    kontoplan = las_kontoplan(skriv(tmp_path, data))
    assert kontoplan.rollens_konto("bank", "2024-12-31") == "0101"
    with pytest.raises(KontoplanFel, match="Kontot 0101 gäller inte på 2025-01-01"):
        kontoplan.rollens_konto("bank", "2025-01-01")
    data["konton"][3] = konto("0707", fran="2025-01-01")
    kontoplan = las_kontoplan(skriv(tmp_path, data))
    with pytest.raises(KontoplanFel, match="Kontot 0707 gäller inte på 2024-12-31"):
        kontoplan.utgaende_moms_konto(7, "2024-12-31")


@pytest.mark.parametrize("nummer", ["1234", "0101 ", "101", 101, None])
def test_okant_konto_stoppar(tmp_path, nummer):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    with pytest.raises(KontoplanFel, match="inget konto"):
        kontoplan.kontots_namn(nummer, "2025-01-01")


@pytest.mark.parametrize("roll, meddelande", [
    ("kassa", "ingen roll 'kassa'"), ("BANK", "ingen roll 'BANK'"), (None, "ingen roll None"),
    ("utgaende_moms_per_sats", "Använd utgaende_moms_konto"),
])
def test_okand_roll_stoppar(tmp_path, roll, meddelande):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    with pytest.raises(KontoplanFel, match=meddelande):
        kontoplan.rollens_konto(roll, "2025-01-01")


@pytest.mark.parametrize("sats, meddelande", [
    (8, "inget konto för utgående moms med satsen 8 %"), (0, "satsen 0 %"),
    ("7", "ska vara ett heltal i procent, inte text"), (True, "inte true eller false"), (7.0, "inte decimaltal"),
])
def test_sats_utan_konto_stoppar(tmp_path, sats, meddelande):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    assert kontoplan.utgaende_moms_konto(7, "2025-01-01") == "0707"
    with pytest.raises(KontoplanFel, match=meddelande):
        kontoplan.utgaende_moms_konto(sats, "2025-01-01")


def test_kontots_roller(tmp_path):
    kontoplan = las_kontoplan(skriv(tmp_path, roller(leverantorsskulder="0101",
                                                     utgaende_moms_per_sats={"9": "0707", "7": "0707", "0": "0909"})))
    assert kontoplan.kontots_roller("0101") == [("bank", None), ("leverantorsskulder", None)]
    assert kontoplan.kontots_roller("0303") == [("ingaende_moms", None)]
    assert kontoplan.kontots_roller("0707") == [("utgaende_moms_per_sats", 7), ("utgaende_moms_per_sats", 9)]
    assert kontoplan.kontots_roller("0909") == [("utgaende_moms_per_sats", 0)]
    assert kontoplan.kontots_roller("9001") == [] == kontoplan.kontots_roller("0202")
    testbutiken = las_kontoplan(KONTOPLAN_FIL)
    assert testbutiken.kontots_roller("1940") == [("bank", None)]
    assert testbutiken.kontots_roller("2621") == [("utgaende_moms_per_sats", 12)]


@pytest.mark.parametrize("nummer", ["1234", "0101 ", 101, None])
def test_kontots_roller_for_okant_konto_stoppar(tmp_path, nummer):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    with pytest.raises(KontoplanFel, match="inget konto"):
        kontoplan.kontots_roller(nummer)


@pytest.mark.parametrize("datum", ["2025-02-30", "2025-1-01", None, 20250101])
def test_ogiltigt_datum_i_uppslaget_stoppar(tmp_path, datum):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    for uppslag in (lambda: kontoplan.kontots_namn("0101", datum), lambda: kontoplan.rollens_konto("bank", datum),
                    lambda: kontoplan.utgaende_moms_konto(7, datum)):
        with pytest.raises(KontoplanFel, match="datumet ska vara ett giltigt datum"):
            uppslag()


# --- Resultatet går inte att ändra ---

def test_kontoplanen_kan_inte_andras(tmp_path):
    kontoplan = las_kontoplan(skriv(tmp_path, plan()))
    with pytest.raises(AttributeError):
        kontoplan._roller = {}
    with pytest.raises(AttributeError):
        del kontoplan._konton
    with pytest.raises(TypeError):
        kontoplan._roller["bank"] = "9001"
    with pytest.raises(TypeError):
        kontoplan._roller["utgaende_moms_per_sats"]["7"] = "9001"
    with pytest.raises(TypeError):
        kontoplan._konton["0101"]["namn"] = "ändrat"
    kopior = kontoplan.konton
    kopior[0]["namn"] = "ändrat"
    kopior.clear()
    assert kontoplan.kontots_namn("0101", "2025-01-01") == "bank"
    assert kontoplan.konton[0] == {"nummer": "0101", "namn": "bank", "fran": None, "till": None}


def test_kontoplanen_kan_bara_skapas_av_las_kontoplan():
    with pytest.raises(KontoplanFel, match="kan bara skapas av las_kontoplan"):
        Kontoplan(object(), "PÅHITTAD", {}, {})


def test_kontrollsumman_ar_sha256_av_filen(tmp_path):
    # Granskning 7, M4: summan räknas på exakt de bytes som tolkas, så samma innehåll med ett
    # blanksteg till ger en annan summa.
    fil = skriv(tmp_path, plan())
    fore = las_kontoplan(fil)
    assert fore.kontrollsumma == hashlib.sha256(fil.read_bytes()).hexdigest()
    assert las_kontoplan(KONTOPLAN_FIL).kontrollsumma == hashlib.sha256(KONTOPLAN_FIL.read_bytes()).hexdigest()
    fil.write_bytes(fil.read_bytes() + b" ")
    efter = las_kontoplan(fil)
    assert efter.konton == fore.konton and efter.kontrollsumma != fore.kontrollsumma
    with pytest.raises(AttributeError):
        efter._kontrollsumma = fore.kontrollsumma


def test_filen_andras_inte_av_inlasningen(tmp_path):
    data = plan()
    fore = copy.deepcopy(data)
    las_kontoplan(skriv(tmp_path, data))
    assert data == fore


def test_utan_anteckning_godtas(tmp_path):
    assert las_kontoplan(skriv(tmp_path, utan(plan(), "anteckning"))).status == "PÅHITTAD"


def test_samma_konto_for_flera_roller_och_satsen_noll_godtas(tmp_path):
    kontoplan = las_kontoplan(skriv(tmp_path, roller(utgaende_moms_per_sats={"0": "0707", "100": "0707"})))
    assert kontoplan.utgaende_moms_konto(0, "2025-01-01") == kontoplan.utgaende_moms_konto(100, "2025-01-01") == "0707"


# --- Stoppregler ---

@pytest.mark.parametrize("ascii", [False, True], ids=["som_tecken", "som_kod_i_json"])
@pytest.mark.parametrize("tecken", DOLDA.values(), ids=DOLDA.keys())
@pytest.mark.parametrize("plats", ["anteckning", "kontonamn", "kontonummer", "roll", "nyckel"])
def test_dolt_tecken_var_som_helst_stoppar(tmp_path, tecken, ascii, plats):
    data = plan()
    if plats == "anteckning":
        data["anteckning"] = "på" + tecken + "hittad"
    elif plats == "kontonamn":
        data["konton"][5]["namn"] = "kost" + tecken + "nad"
    elif plats == "kontonummer":
        data["konton"][5]["nummer"] = "90" + tecken + "01"
    elif plats == "roll":
        data["roller"]["bank"] = "01" + tecken + "01"
    else:
        data["roller"] = {**data["roller"], "bank" + tecken: "0101"}
    stoppas(tmp_path, data, "U+" + format(ord(tecken), "04X"), "inte syns", ascii=ascii)


STOPPAS = {
    # Okända och saknade nycklar
    "okand_nyckel": (plan(extra=1), "okänd nyckel: 'extra'"),
    "saknar_status": (utan(plan(), "status"), "saknar nyckeln 'status'"),
    "saknar_konton": (utan(plan(), "konton"), "saknar nyckeln 'konton'"),
    "saknar_roller": (utan(plan(), "roller"), "saknar nyckeln 'roller'"),
    "okand_nyckel_i_konto": (plan(konton=[{**konto("0101"), "typ": "tillgång"}]), "okänd nyckel: 'typ'"),
    "saknar_nummer": (plan(konton=[{"namn": "x"}]), "saknar nyckeln 'nummer'"),
    "saknar_namn": (plan(konton=[{"nummer": "0101"}]), "saknar nyckeln 'namn'"),
    "okand_roll": (roller(kassa="0101"), "okänd nyckel: 'kassa'"),
    "saknar_roll": (plan(roller=utan(plan()["roller"], "ingaende_moms")), "saknar nyckeln 'ingaende_moms'"),
    # Fel typ
    "filen_ar_en_lista": ([plan()], "ska vara ett objekt med nycklar, inte en lista"),
    "konton_objekt": (plan(konton={"0101": "bank"}), "'konton' ska vara en lista"),
    "konto_lista": (plan(konton=[["0101", "bank"]]), "konto nummer 1 ska vara ett objekt"),
    "nummer_heltal": (plan(konton=[konto(101)]), "'nummer' i konto nummer 1 ska vara text", "inte heltal"),
    "nummer_decimaltal": (plan(konton=[konto(101.0)]), "inte decimaltal"),
    "namn_heltal": (plan(konton=[konto("0101", 5)]), "'namn' i konto nummer 1 ska vara text, inte heltal"),
    "fran_ogiltigt": (plan(konton=[konto("0101", fran="2025-02-30")]), "'fran' i konto nummer 1"),
    "fran_null": (plan(konton=[konto("0101", fran=None)]), "'fran'", "inte null"),
    "till_ogiltigt": (plan(konton=[konto("0101", till="2025")]), "'till' i konto nummer 1"),
    "roller_lista": (plan(roller=["0101"]), "'roller' ska vara ett objekt"),
    "roll_heltal": (roller(bank=101), "rollen 'bank' ska vara text", "inte heltal"),
    "roll_null": (roller(bank=None), "inte null"),
    "per_sats_text": (roller(utgaende_moms_per_sats="0707"), "ett konto per momssats, inte text"),
    "per_sats_konto_heltal": (roller(utgaende_moms_per_sats={"7": 707}), "för satsen 7 ska vara text"),
    "status_null": (plan(status=None), "'status' ska vara text, inte null"),
    "anteckning_lista": (plan(anteckning=["x"]), "'anteckning' ska vara text, inte en lista"),
    # Tomma värden
    "status_tom": (plan(status=""), "'status' får inte vara tom"),
    "namn_tomt": (plan(konton=[konto("0101", "")]), "'namn' i konto nummer 1 får inte vara tom"),
    "namn_blanksteg": (plan(konton=[konto("0101", "  ")]), "får inte vara tom"),
    "nummer_tomt": (plan(konton=[konto("")]), "får bara ha siffrorna 0–9"),
    "anteckning_tom": (plan(anteckning=""), "'anteckning' får inte vara tom"),
    "inga_konton": (plan(konton=[]), "'konton' är tom"),
    "per_sats_tom": (roller(utgaende_moms_per_sats={}), "'utgaende_moms_per_sats' är tom"),
    "namn_blanksteg_sist": (plan(konton=[konto("0101", "bank ")]), "blanksteg först eller sist"),
    # Kontonumret
    "nummer_mellanslag": (plan(konton=[konto("01 01")]), "'01 01'", "får bara ha siffrorna 0–9"),
    "nummer_bokstav": (plan(konton=[konto("0101a")]), "får bara ha siffrorna 0–9"),
    "nummer_minus": (plan(konton=[konto("-101")]), "får bara ha siffrorna 0–9"),
    "nummer_fullbredd": (plan(konton=[konto(chr(0xFF10) + "101")]), "får bara ha siffrorna 0–9"),
    "nummer_arabiska_siffror": (plan(konton=[konto(chr(0x661) + "01")]), "får bara ha siffrorna 0–9"),
    "nummer_for_langt": (plan(konton=[konto("1" * 16)]), "högst 15 stycken"),
    # Dubblettkonton
    "dublettkonto": (plan(konton=plan()["konton"] + [konto("9001", "annat namn")]), "kontot '9001' står flera gånger"),
    "dublettkonto_med_giltighet": (plan(konton=plan()["konton"] + [konto("9001", fran="2030-01-01")]),
                                   "står flera gånger"),
    # Giltighetstid
    "slutar_fore_start": (plan(konton=[konto("0101", fran="2025-05-01", till="2025-04-30")]),
                          "slutar 2025-04-30, före sitt första datum 2025-05-01"),
    # Roller som pekar fel
    "roll_saknat_konto": (roller(bank="1234"), "rollen 'bank' pekar på kontot '1234', som inte finns"),
    "roll_ogiltigt_nummer": (roller(leverantorsskulder="02 02"), "får bara ha siffrorna 0–9"),
    "per_sats_saknat_konto": (roller(utgaende_moms_per_sats={"7": "0708"}), "för satsen 7 pekar på kontot '0708'"),
    "sats_nolla_forst": (roller(utgaende_moms_per_sats={"07": "0707"}), "momssatsen '07'"),
    "sats_decimal": (roller(utgaende_moms_per_sats={"7.0": "0707"}), "momssatsen '7.0'"),
    "sats_over_100": (roller(utgaende_moms_per_sats={"101": "0707"}), "momssatsen '101'"),
    "sats_negativ": (roller(utgaende_moms_per_sats={"-7": "0707"}), "momssatsen '-7'"),
    "sats_ord": (roller(utgaende_moms_per_sats={"sju": "0707"}), "momssatsen 'sju'"),
    "sats_tom": (roller(utgaende_moms_per_sats={"": "0707"}), "momssatsen ''"),
    "sats_procent": (roller(utgaende_moms_per_sats={"7 %": "0707"}), "momssatsen '7 %'"),
}


@pytest.mark.parametrize("data, texter", [(fall[0], fall[1:]) for fall in STOPPAS.values()], ids=STOPPAS.keys())
def test_stoppregel(tmp_path, data, texter):
    stoppas(tmp_path, data, *texter)


@pytest.mark.parametrize("text, vad", [
    ('{"status": "A", "status": "B"}', "står flera gånger"),
    ('{"status": "x", "konton": [{"nummer": "1", "namn": "x", "namn": "y"}], "roller": {}}', "står flera gånger"),
    ('{"status": "x", "konton": [{"nummer": NaN, "namn": "x"}], "roller": {}}', "inte decimaltal"),
    ('{"status": "x",', "är inte giltig JSON"),
])
def test_trasig_json_stoppar(tmp_path, text, vad):
    fil = tmp_path / "kontoplan.json"
    fil.write_text(text, encoding="utf-8")
    with pytest.raises(KontoplanFel, match=re.escape(vad)):
        las_kontoplan(fil)


def test_fil_som_inte_ar_utf8_stoppar(tmp_path):
    fil = tmp_path / "kontoplan.json"
    fil.write_bytes(json.dumps(plan(), ensure_ascii=False).encode("cp1252"))
    with pytest.raises(KontoplanFel, match="inte sparat som UTF-8"):
        las_kontoplan(fil)


@pytest.mark.parametrize("sokvag", [None, 1, True])
def test_sokvag_av_fel_typ_stoppar(sokvag):
    with pytest.raises(KontoplanFel, match="sökvägen ska vara text eller en Path"):
        las_kontoplan(sokvag)


def test_fil_som_saknas_stoppar(tmp_path):
    with pytest.raises(KontoplanFel, match="Kontoplanen saknas"):
        las_kontoplan(tmp_path / "finns_inte.json")
