"""Tester för momsfilen (las_momssatser.py, foretag/<namn>/momssatser.json).

Momsfilen för testföretaget är SYNTETISK. De små filerna nedan är påhittade, med påhittade satser
(7 och 9 procent) som inte är några riktiga momssatser, och skrivs i en tillfällig mapp för varje test.
"""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
MOMS_FIL = AGENT / "foretag" / "syntet-testbutik" / "momssatser.json"

sys.path.insert(0, str(AGENT / "scripts"))

from las_momssatser import HOGSTA_SATS, Momssatser, MomssatsFel, las_momssatser  # noqa: E402

# Dolda tecken byggs med chr(), så att de syns i koden (test_inga_dolda_tecken.py).
DOLDA = {
    "nollbredd": chr(0x200B), "riktning": chr(0x202E), "milt_riktningsmarke": chr(0x200E), "bom": chr(0xFEFF),
    "hart_mellanslag": chr(0xA0), "tabb": chr(0x9), "radbrytning": chr(0xA), "nel": chr(0x85),
    "u2028": chr(0x2028), "utfyllnad": chr(0x3164), "variantvaljare": chr(0xFE0F), "mjukt_bindestreck": chr(0xAD),
}


def period(fran="2024-01-01", till=None, sats=7, kalla="påhittad"):
    return {"fran": fran, "till": till, "sats": sats, "kalla": kalla}


def moms(**andrat):
    """En felfri momsfil, med de ändringar som anges."""
    data = {
        "anteckning": "påhittad",
        "status": "PÅHITTAD",
        "varugrupper": {"grupp_a": [period()], "grupp_b": [period(sats=0)]},
        "moms_tolerans_ore_per_rad": 1,
    }
    data.update(andrat)
    return data


def perioder(*poster):
    return moms(varugrupper={"grupp_a": list(poster)})


def skriv(mapp, data, ascii=False):
    fil = mapp / "momssatser.json"
    fil.write_text(json.dumps(data, ensure_ascii=ascii), encoding="utf-8")
    return fil


def stoppas(mapp, data, *texter, ascii=False):
    """Kräver MomssatsFel från filen, med texterna i meddelandet."""
    fil = skriv(mapp, data, ascii)
    with pytest.raises(MomssatsFel) as fel:
        las_momssatser(fil)
    meddelande = str(fel.value)
    assert meddelande.startswith("Momsfilen i " + str(fil)), meddelande
    for text in texter:
        assert text in meddelande, meddelande
    return meddelande


def json_block_i_design(nyckel):
    """JSON-exemplet i DESIGN-regelbok.md som har nyckeln, som Python-värden."""
    text = (AGENT / "DESIGN-regelbok.md").read_text(encoding="utf-8")
    block = [b for b in re.findall(r"```json\n(.*?)```", text, re.DOTALL) if '"' + nyckel + '"' in b]
    assert len(block) == 1, nyckel
    return json.loads(block[0])


# --- Testföretagets fil ---

def test_testforetagets_fil_laddas():
    satser = las_momssatser(MOMS_FIL)
    assert satser.status == "SYNTETISK"
    assert satser.varugrupper == ("livsmedel", "ovrigt", "momsfritt")
    assert satser.tolerans_ore_per_rad == 1
    assert [satser.sats(grupp, "2025-02-10") for grupp in satser.varugrupper] == [12, 25, 0]


def test_testforetagets_fil_har_exakt_vardena_i_design():
    # Inga nya värden har hittats på: filen är exakt exemplet i DESIGN-regelbok.md avsnitt 2.
    assert json.loads(MOMS_FIL.read_text(encoding="utf-8")) == json_block_i_design("moms_tolerans_ore_per_rad")


def test_testforetagets_fil_ar_markt_syntetisk():
    data = json.loads(MOMS_FIL.read_text(encoding="utf-8"))
    assert data["status"] == "SYNTETISK" and "SYNTETISKA" in data["anteckning"]
    assert "INTE verifierade" in data["anteckning"]
    satser = las_momssatser(MOMS_FIL)
    for grupp in satser.varugrupper:
        assert "SYNTETISK" in satser.period(grupp, "2025-01-01")["kalla"], grupp


def test_testforetagets_fil_har_ingen_sats_fore_2025():
    # Ett datum utan sats stoppar, även för testföretaget. Satsen gissas inte.
    with pytest.raises(MomssatsFel, match="ingen sats för varugruppen 'livsmedel' på 2024-12-31"):
        las_momssatser(MOMS_FIL).sats("livsmedel", "2024-12-31")


# --- Uppslaget per datum ---

def test_satsen_fore_och_efter_en_andring(tmp_path):
    satser = las_momssatser(skriv(tmp_path, perioder(period("2024-01-01", "2024-06-30", 7),
                                                     period("2024-07-01", None, 9))))
    assert satser.sats("grupp_a", "2024-01-01") == 7
    assert satser.sats("grupp_a", "2024-06-30") == 7
    assert satser.sats("grupp_a", "2024-07-01") == 9
    assert satser.sats("grupp_a", "2099-12-31") == 9
    assert satser.period("grupp_a", "2024-03-01") == {"fran": "2024-01-01", "till": "2024-06-30", "sats": 7,
                                                      "kalla": "påhittad"}


@pytest.mark.parametrize("datum", ["2023-12-31", "2025-01-01"])
def test_datum_utan_sats_stoppar(tmp_path, datum):
    satser = las_momssatser(skriv(tmp_path, perioder(period("2024-01-01", "2024-12-31"))))
    assert satser.sats("grupp_a", "2024-12-31") == 7
    with pytest.raises(MomssatsFel, match="ingen sats för varugruppen 'grupp_a' på " + datum + ". Satsen gissas inte"):
        satser.sats("grupp_a", datum)


@pytest.mark.parametrize("varugrupp", ["grupp_c", "GRUPP_A", "grupp_a ", None, 1])
def test_okand_varugrupp_stoppar(tmp_path, varugrupp):
    satser = las_momssatser(skriv(tmp_path, moms()))
    with pytest.raises(MomssatsFel, match="ingen varugrupp"):
        satser.sats(varugrupp, "2024-05-05")


BREDA_SIFFROR = "".join(map(chr, (0xFF12, 0xFF10, 0xFF12, 0xFF14))) + "-01-05"  # "2024" med fullbreddssiffror


@pytest.mark.parametrize("datum", ["2024-02-30", "2024-1-05", "20240105", "", None, 20240105, "2024-01-05 ",
                                   BREDA_SIFFROR])
def test_ogiltigt_datum_i_uppslaget_stoppar(tmp_path, datum):
    satser = las_momssatser(skriv(tmp_path, moms()))
    with pytest.raises(MomssatsFel, match="datumet ska vara ett giltigt datum"):
        satser.sats("grupp_a", datum)


# --- Resultatet går inte att ändra ---

def test_momssatser_kan_inte_andras(tmp_path):
    satser = las_momssatser(skriv(tmp_path, moms()))
    with pytest.raises(AttributeError):
        satser._status = "ÄNDRAD"
    with pytest.raises(AttributeError):
        del satser._varugrupper
    with pytest.raises(TypeError):
        satser._varugrupper["grupp_a"] = ()
    with pytest.raises(TypeError):
        satser._varugrupper["grupp_a"][0]["sats"] = 99
    kopia = satser.period("grupp_a", "2024-05-05")
    kopia["sats"] = 99
    assert satser.sats("grupp_a", "2024-05-05") == 7


def test_momssatser_kan_bara_skapas_av_las_momssatser():
    with pytest.raises(MomssatsFel, match="kan bara skapas av las_momssatser"):
        Momssatser(object(), "PÅHITTAD", {"grupp_a": [period()]}, 1)


def test_kontrollsumman_ar_sha256_av_filen(tmp_path):
    # Granskning 7, M4: summan räknas på exakt de bytes som tolkas, så samma innehåll med ett
    # blanksteg till ger en annan summa.
    fil = skriv(tmp_path, moms())
    fore = las_momssatser(fil)
    assert fore.kontrollsumma == hashlib.sha256(fil.read_bytes()).hexdigest()
    assert las_momssatser(MOMS_FIL).kontrollsumma == hashlib.sha256(MOMS_FIL.read_bytes()).hexdigest()
    fil.write_bytes(fil.read_bytes() + b" ")
    efter = las_momssatser(fil)
    assert efter.varugrupper == fore.varugrupper and efter.kontrollsumma != fore.kontrollsumma
    with pytest.raises(AttributeError):
        efter._kontrollsumma = fore.kontrollsumma


def test_filen_andras_inte_av_inlasningen(tmp_path):
    data = moms()
    fore = copy.deepcopy(data)
    las_momssatser(skriv(tmp_path, data))
    assert data == fore


def test_utan_anteckning_godtas(tmp_path):
    data = moms()
    del data["anteckning"]
    assert las_momssatser(skriv(tmp_path, data)).status == "PÅHITTAD"


def test_period_utan_slut_i_slutet_och_flera_perioder_godtas(tmp_path):
    satser = las_momssatser(skriv(tmp_path, perioder(period("2024-01-01", "2024-01-01", 7),
                                                     period("2024-01-02", "2024-12-31", 9),
                                                     period("2025-01-01", None, 0))))
    assert [satser.sats("grupp_a", d) for d in ("2024-01-01", "2024-01-02", "2025-06-01")] == [7, 9, 0]


def test_gransvarden_godtas(tmp_path):
    satser = las_momssatser(skriv(tmp_path, moms(varugrupper={"a": [period(sats=0)], "b9_x": [period(sats=HOGSTA_SATS)]},
                                                 moms_tolerans_ore_per_rad=0)))
    assert satser.sats("b9_x", "2024-01-01") == HOGSTA_SATS and satser.tolerans_ore_per_rad == 0


# --- Stoppregler ---

@pytest.mark.parametrize("ascii", [False, True], ids=["som_tecken", "som_kod_i_json"])
@pytest.mark.parametrize("tecken", DOLDA.values(), ids=DOLDA.keys())
@pytest.mark.parametrize("plats", ["anteckning", "status", "kalla", "varugrupp", "nyckel"])
def test_dolt_tecken_var_som_helst_stoppar(tmp_path, tecken, ascii, plats):
    data = moms()
    if plats in ("anteckning", "status"):
        data[plats] = "PÅ" + tecken + "HITTAD"
    elif plats == "kalla":
        data["varugrupper"]["grupp_a"][0]["kalla"] = "på" + tecken + "hittad"
    elif plats == "varugrupp":
        data["varugrupper"] = {"grupp" + tecken + "_a": [period()]}
    else:
        data["varugrupper"]["grupp_a"][0] = {"fran": "2024-01-01", "till": None, "sats" + tecken: 7, "kalla": "x"}
    stoppas(tmp_path, data, "U+" + format(ord(tecken), "04X"), "inte syns", ascii=ascii)


def test_halvt_tecken_stoppar(tmp_path):
    # Ett halvt tecken (U+D800) går bara att skriva som kod i JSON.
    fil = tmp_path / "momssatser.json"
    fil.write_text(json.dumps(moms(status="X")).replace('"X"', '"X\\ud800"'), encoding="utf-8")
    with pytest.raises(MomssatsFel, match="U\\+D800"):
        las_momssatser(fil)


STOPPAS = {
    # Okända och saknade nycklar
    "okand_nyckel": (moms(extra=1), "okänd nyckel: 'extra'"),
    "saknar_status": ({k: v for k, v in moms().items() if k != "status"}, "saknar nyckeln 'status'"),
    "saknar_varugrupper": ({k: v for k, v in moms().items() if k != "varugrupper"}, "saknar nyckeln 'varugrupper'"),
    "saknar_tolerans": ({k: v for k, v in moms().items() if k != "moms_tolerans_ore_per_rad"},
                        "saknar nyckeln 'moms_tolerans_ore_per_rad'"),
    "okand_nyckel_i_period": (perioder({**period(), "momsfri": True}), "okänd nyckel: 'momsfri'"),
    "saknar_till": (perioder({k: v for k, v in period().items() if k != "till"}), "saknar nyckeln 'till'"),
    "saknar_kalla": (perioder({k: v for k, v in period().items() if k != "kalla"}), "saknar nyckeln 'kalla'"),
    # Fel typ
    "filen_ar_en_lista": ([moms()], "ska vara ett objekt med nycklar, inte en lista"),
    "varugrupper_lista": (moms(varugrupper=[period()]), "'varugrupper' ska vara ett objekt"),
    "perioder_objekt": (moms(varugrupper={"grupp_a": period()}), "ska ha en lista med perioder, inte ett objekt"),
    "period_lista": (perioder([period()]), "ska vara ett objekt med nycklar, inte en lista"),
    "sats_decimaltal": (perioder(period(sats=12.0)), "'sats' i period nummer 1", "inte decimaltal"),
    "sats_text": (perioder(period(sats="12")), "ska vara ett heltal, inte text"),
    "sats_true": (perioder(period(sats=True)), "ska vara ett heltal, inte true eller false"),
    "sats_null": (perioder(period(sats=None)), "ska vara ett heltal, inte null"),
    "sats_negativ": (perioder(period(sats=-1)), "ska vara från 0 till och med 100, inte -1"),
    "sats_over_100": (perioder(period(sats=101)), "ska vara från 0 till och med 100, inte 101"),
    "tolerans_decimaltal": (moms(moms_tolerans_ore_per_rad=0.5), "'moms_tolerans_ore_per_rad' ska vara ett heltal"),
    "tolerans_true": (moms(moms_tolerans_ore_per_rad=True), "inte true eller false"),
    "tolerans_negativ": (moms(moms_tolerans_ore_per_rad=-1), "'moms_tolerans_ore_per_rad' ska vara från 0"),
    "fran_ogiltigt": (perioder(period(fran="2024-02-30")), "'fran' i period nummer 1", "inte '2024-02-30'"),
    "fran_tal": (perioder(period(fran=20240101)), "'fran'", "inte heltal"),
    "fran_breda_siffror": (perioder(period(fran=BREDA_SIFFROR)), "'fran'", "ska vara ett giltigt datum"),
    "fran_null": (perioder(period(fran=None)), "'fran'", "inte null"),
    "till_ogiltigt": (perioder(period(till="31/12/2024")), "'till' i period nummer 1"),
    "till_tom": (perioder(period(till="")), "'till'", "inte ''"),
    "kalla_tal": (perioder(period(kalla=5)), "'kalla' i period nummer 1", "ska vara text, inte heltal"),
    "status_null": (moms(status=None), "'status' ska vara text, inte null"),
    "anteckning_tal": (moms(anteckning=3), "'anteckning' ska vara text"),
    # Tomma värden
    "status_tom": (moms(status=""), "'status' får inte vara tom"),
    "status_blanksteg": (moms(status="   "), "'status' får inte vara tom"),
    "kalla_tom": (perioder(period(kalla="")), "'kalla'", "får inte vara tom"),
    "anteckning_tom": (moms(anteckning=""), "'anteckning' får inte vara tom"),
    "inga_varugrupper": (moms(varugrupper={}), "'varugrupper' är tom"),
    "inga_perioder": (moms(varugrupper={"grupp_a": []}), "har inga perioder"),
    # Blanksteg först eller sist
    "status_blanksteg_forst": (moms(status=" SYNTETISK"), "blanksteg först eller sist"),
    "kalla_blanksteg_sist": (perioder(period(kalla="x ")), "blanksteg först eller sist"),
    # Varugruppens namn
    "namn_stor_bokstav": (moms(varugrupper={"Grupp_a": [period()]}), "ogiltigt namn"),
    "namn_mellanslag": (moms(varugrupper={"grupp a": [period()]}), "ogiltigt namn"),
    "namn_siffra_forst": (moms(varugrupper={"1grupp": [period()]}), "ogiltigt namn"),
    "namn_tomt": (moms(varugrupper={"": [period()]}), "ogiltigt namn"),
    "namn_kyrilliskt_a": (moms(varugrupper={"grupp_" + chr(0x430): [period()]}), "ogiltigt namn"),
    "namn_bindestreck": (moms(varugrupper={"grupp-a": [period()]}), "ogiltigt namn"),
    "namn_aao": (moms(varugrupper={"övrigt": [period()]}), "ogiltigt namn"),
    # Perioderna
    "slutar_fore_start": (perioder(period("2024-05-01", "2024-04-30")), "slutar 2024-04-30, före sitt första datum"),
    "overlapp": (perioder(period("2024-01-01", "2024-06-30"), period("2024-06-30", None)), "överlappar"),
    "samma_start": (perioder(period("2024-01-01", "2024-06-30"), period("2024-01-01", None)), "överlappar"),
    "fel_ordning": (perioder(period("2024-07-01", None), period("2024-01-01", "2024-06-30")), "överlappar"),
    "fel_ordning_med_slut": (perioder(period("2024-07-01", "2024-12-31"), period("2024-01-01", "2024-06-30")),
                             "överlappar"),
    "utan_slut_inte_sist": (perioder(period("2024-01-01", None), period("2025-01-01", None)), "utan slutdatum"),
    "glapp": (perioder(period("2024-01-01", "2024-06-29"), period("2024-07-01", None)), "glapp", "2024-06-29"),
    "glapp_ett_ar": (perioder(period("2023-01-01", "2023-12-31"), period("2025-01-01", None)), "glapp"),
    "glapp_i_tredje": (perioder(period("2024-01-01", "2024-01-31"), period("2024-02-01", "2024-02-28"),
                                period("2024-03-01", None)), "glapp", "period nummer 2"),
    "sista_dagen_som_slut": (perioder(period("9999-12-31", "9999-12-31"), period("9999-12-31", None)), "överlappar"),
}


@pytest.mark.parametrize("data, texter", [(fall[0], fall[1:]) for fall in STOPPAS.values()], ids=STOPPAS.keys())
def test_stoppregel(tmp_path, data, texter):
    stoppas(tmp_path, data, *texter)


@pytest.mark.parametrize("text, vad", [
    ('{"status": "A", "status": "B"}', "står flera gånger"),
    ('{"anteckning": NaN, "status": "x", "varugrupper": {"a": [{"fran": "2024-01-01", "till": null, "sats": 7,'
     ' "kalla": "x"}]}, "moms_tolerans_ore_per_rad": 1}', "'anteckning' ska vara text, inte decimaltal"),
    ('{"status": "x", "varugrupper": {"a": [{"fran": "2024-01-01", "till": null, "sats": Infinity, "kalla": "x"}]},'
     ' "moms_tolerans_ore_per_rad": 1}', "inte decimaltal"),
    ('{"status": "x", "varugrupper": {}, "moms_tolerans_ore_per_rad": 1234567890123456}', "16 siffror"),
    ('{"status": "x",', "är inte giltig JSON"),
    ("", "är inte giltig JSON"),
])
def test_trasig_json_stoppar(tmp_path, text, vad):
    fil = tmp_path / "momssatser.json"
    fil.write_text(text, encoding="utf-8")
    with pytest.raises(MomssatsFel, match=re.escape(vad)):
        las_momssatser(fil)


def test_fil_som_inte_ar_utf8_stoppar(tmp_path):
    fil = tmp_path / "momssatser.json"
    fil.write_bytes(json.dumps(moms(status="PÅHITTAD"), ensure_ascii=False).encode("cp1252"))
    with pytest.raises(MomssatsFel, match="inte sparat som UTF-8"):
        las_momssatser(fil)


@pytest.mark.parametrize("sokvag", [None, 1, True])
def test_sokvag_av_fel_typ_stoppar(sokvag):
    with pytest.raises(MomssatsFel, match="sökvägen ska vara text eller en Path"):
        las_momssatser(sokvag)


def test_fil_som_saknas_stoppar(tmp_path):
    with pytest.raises(MomssatsFel, match="Momsfilen saknas"):
        las_momssatser(tmp_path / "finns_inte.json")
