"""Tester för regelboken (las_regelbok.py, foretag/<namn>/regelbok.json).

Regelboken för testföretaget är SYNTETISK. De små regelböckerna nedan är påhittade, med påhittade
konton (som 0101 och 9001), påhittade varugrupper (grupp_a, grupp_b, grupp_c), påhittade satser (7
och 9 procent) och påhittade motparter, och skrivs i en tillfällig mapp för varje test.
"""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
TESTBUTIKEN = AGENT / "foretag" / "syntet-testbutik"
REGELBOK_FIL = TESTBUTIKEN / "regelbok.json"

sys.path.insert(0, str(AGENT / "scripts"))

from las_kontoplan import las_kontoplan  # noqa: E402
from las_matchningsformat import ladda_matchningsformat  # noqa: E402
from las_momssatser import las_momssatser  # noqa: E402
from las_regelbok import REGELBOK_NYCKLAR, Regelbok, RegelbokFel, las_regelbok  # noqa: E402
from test_las_momssatser import DOLDA, json_block_i_design  # noqa: E402


# --- Påhittad konfiguration ---

def konto(nummer, **giltighet):
    return {"nummer": nummer, "namn": "påhittat " + nummer, **giltighet}


KONTOPLAN = {
    "status": "PÅHITTAD",
    "konton": [konto("0101"), konto("0202"), konto("0303"), konto("0707"), konto("9001"), konto("9002"),
               konto("9003", fran="2024-01-01", till="2024-12-31"), konto("9004", fran="2025-01-01")],
    "roller": {"bank": "0101", "leverantorsskulder": "0202", "ingaende_moms": "0303",
               "utgaende_moms_per_sats": {"7": "0707"}},
}


def sats(fran, till, procent):
    return {"fran": fran, "till": till, "sats": procent, "kalla": "påhittad"}


MOMSSATSER = {
    "status": "PÅHITTAD",
    "varugrupper": {
        "grupp_a": [sats("2024-01-01", None, 7)],
        # Satsen ändras vid årsskiftet: en regel som gäller båda åren ska ändå godtas.
        "grupp_b": [sats("2024-01-01", "2024-12-31", 7), sats("2025-01-01", None, 9)],
        # Har ingen sats före 2025.
        "grupp_c": [sats("2025-01-01", None, 0)],
        # Har ingen sats efter 2025.
        "grupp_d": [sats("2024-01-01", "2025-12-31", 7)],
    },
    "moms_tolerans_ore_per_rad": 1,
}

MATCHNING = {
    "kraver_inte_underlag": [
        {"namn": "regel_in", "riktning": "in", "referens_borjar_med": "IN-"},
        {"namn": "regel_ut", "riktning": "ut", "referens_borjar_med": "UT-", "hogst_belopp_ore": 3000},
    ],
    "tidsfonster_dagar": {"leverantorsfaktura": 30, "kvitto": 3},
    "saknat_underlag_efter_dagar": 7,
}


@pytest.fixture
def konfiguration(tmp_path):
    """(kontoplan, momssatser, matchningsformat), lästa med de vanliga inläsningsfunktionerna."""
    mapp = tmp_path / "konfiguration"
    mapp.mkdir()
    for namn, data in [("kontoplan", KONTOPLAN), ("momssatser", MOMSSATSER), ("matchning", MATCHNING)]:
        (mapp / (namn + ".json")).write_text(json.dumps(data), encoding="utf-8")
    return (las_kontoplan(mapp / "kontoplan.json"), las_momssatser(mapp / "momssatser.json"),
            ladda_matchningsformat(mapp / "matchning.json"))


def regel(id_, galler, kontering, niva="B", **villkor):
    return {"id": id_, "galler": galler, "kontering": kontering, "villkor": {"giltig_fran": "2024-01-01", **villkor},
            "niva": niva}


def underlag(typ="leverantorsfaktura", motpart="MOTPART-A"):
    return {"kalla": "underlag", "typ": typ, "motpart": motpart}


def z(kassaregister="KASSA-X"):
    return {"kalla": "z_rapport", "kassaregister": kassaregister}


def bankrad(namn="regel_in"):
    return {"kalla": "bankrad", "matchningsregel": namn}


def regler():
    """Fem felfria regler, en för varje sorts källa och riktning. Index 0–4 används i testerna."""
    return [
        regel("R-1", underlag(), {"grupp_a": "9001", "grupp_b": "9001"}, niva="A"),
        regel("R-2", underlag("kvitto"), {"grupp_a": "9002"}, hogst_belopp_ore=5000, avdragsbegransad=True),
        regel("R-3", z(), {"forsaljning": {"grupp_a": "9002", "grupp_b": "9002"}, "betalsatt": {"post_kort": "0101"}}),
        regel("R-4", bankrad(), {"motkonto": "0101", "avgift": "9001"}, niva="C"),
        regel("R-5", bankrad("regel_ut"), {"kostnad": "9001"}, hogst_belopp_ore=2500),
    ]


def bok(**andrat):
    """En felfri regelbok, med de ändringar som anges."""
    data = {
        "anteckning": "påhittad",
        "foretag": "påhittat-ab",
        "version": 1,
        "godkand": {"av": "Påhittad godkännare", "datum": "2025-01-01"},
        "granser": {"a_hogst_ore": 1000, "b_hogst_ore": 5000},
        "k9": {"minst_historik": 3, "hogst_procent_av_median": 300, "lagst_procent_av_median": 33},
        "oppettider": {"stangda_veckodagar": ["sondag"], "stangda_datum": ["2025-01-01"]},
        "regler": regler(),
    }
    data.update(andrat)
    return data


BORT = object()


def andrad(*andringar):
    """En felfri regelbok där varje (väg, värde) i andringar är ändrat. Värdet BORT tar bort nyckeln."""
    data = bok()
    for vag, varde in andringar:
        mal = data
        for steg in vag[:-1]:
            mal = mal[steg]
        if varde is BORT:
            del mal[vag[-1]]
        else:
            mal[vag[-1]] = varde
    return data


def med_regel(ny):
    """En felfri regelbok med en regel till sist."""
    return bok(regler=regler() + [ny])


def skriv(mapp, data, ascii=False):
    fil = mapp / "regelbok.json"
    fil.write_text(json.dumps(data, ensure_ascii=ascii), encoding="utf-8")
    return fil


def las(mapp, data, konfiguration):
    return las_regelbok(skriv(mapp, data), *konfiguration)


def stoppas(mapp, data, konfiguration, *texter, ascii=False):
    """Kräver RegelbokFel från filen, med texterna i meddelandet."""
    fil = skriv(mapp, data, ascii)
    with pytest.raises(RegelbokFel) as fel:
        las_regelbok(fil, *konfiguration)
    meddelande = str(fel.value)
    assert meddelande.startswith("Regelboken i " + str(fil)), meddelande
    for text in texter:
        assert text in meddelande, meddelande
    return meddelande


# --- Testföretagets fil ---

def las_testbutikens_regelbok(fil=REGELBOK_FIL):
    return las_regelbok(fil, las_kontoplan(TESTBUTIKEN / "kontoplan.json"),
                        las_momssatser(TESTBUTIKEN / "momssatser.json"),
                        ladda_matchningsformat(TESTBUTIKEN / "matchning.json"))


def test_testforetagets_fil_laddas():
    regelbok = las_testbutikens_regelbok()
    assert regelbok.foretag == "syntet-testbutik" and regelbok.version == 1
    assert len(regelbok.regler) == 10
    # Hugos beslut D18 och D19: A-gräns 20 000 kr, B-gräns 40 000 kr, 3 godkännanden, K9 3 / 300 % / 33 %.
    assert regelbok.granser == {"a_hogst_ore": 2000000, "b_hogst_ore": 4000000}
    assert regelbok.k9 == {"minst_historik": 3, "hogst_procent_av_median": 300, "lagst_procent_av_median": 33}
    assert regelbok.oppettider == {"stangda_veckodagar": ["sondag"], "stangda_datum": ["2025-01-01", "2025-01-06"]}
    datum = "2025-02-06"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "LEV-TE", datum)["id"] == "R-LEV-TE"
    assert regelbok.regel_for_underlag("kvitto", "RESTAURANG-1", datum)["villkor"]["avdragsbegransad"] is True
    assert regelbok.regel_for_z_rapport("TB-KASSA-1", datum)["id"] == "R-Z-TB-KASSA-1"
    assert regelbok.regel_for_bankrad("bankavgift", datum)["villkor"]["hogst_belopp_ore"] == 25000
    # Ny motpart: ingen regel. Det blir ett ärende senare, Vera gissar inget konto.
    assert regelbok.regel_for_underlag("leverantorsfaktura", "HYRESVARD", datum) is None
    # Före regelns första dag finns ingen regel.
    assert regelbok.regel_for_underlag("leverantorsfaktura", "LEV-TE", "2024-12-31") is None


def test_testforetagets_fil_har_exakt_vardena_i_design_och_tva_tillagg():
    # Inga nya värden har hittats på: filen är exemplet i DESIGN-regelbok.md avsnitt 1, med två
    # tillägg som uppgiften kräver och som båda kommer från redan bestämda värden:
    # - 'oppettider' (Hugos beslut D21), med testbutikens stängda dagar ur testdata/README.md,
    # - gränsen för bankavgiften, som är en regel för pengar ut och därför måste ha
    #   'hogst_belopp_ore'. Värdet är gränsen i matchning.json, som Hugo bestämde 2026-10-25.
    design = json_block_i_design("regler")
    design["oppettider"] = {"stangda_veckodagar": ["sondag"], "stangda_datum": ["2025-01-01", "2025-01-06"]}
    avgift = [regel_ for regel_ in design["regler"] if regel_["id"] == "R-BANK-AVGIFT"]
    assert len(avgift) == 1 and "hogst_belopp_ore" not in avgift[0]["villkor"]
    avgift[0]["villkor"]["hogst_belopp_ore"] = 25000
    assert json.loads(REGELBOK_FIL.read_text(encoding="utf-8")) == design
    # Tilläggens källor.
    assert "Stängt söndagar, 1 januari och 6 januari" in (AGENT / "testdata" / "README.md").read_text(encoding="utf-8")
    bankavgift = [r for r in ladda_matchningsformat(TESTBUTIKEN / "matchning.json")["kraver_inte_underlag"]
                  if r["namn"] == "bankavgift"]
    assert bankavgift[0]["hogst_belopp_ore"] == 25000


def test_testforetagets_fil_ar_markt_syntetisk():
    data = json.loads(REGELBOK_FIL.read_text(encoding="utf-8"))
    assert "SYNTETISK" in data["anteckning"] and "INTE verifierade" in data["anteckning"]
    assert "(påhittad)" in data["godkand"]["av"]


# --- Kontrollsumman ---

def test_kontrollsumman_ar_sha256_av_filen(tmp_path, konfiguration):
    fil = skriv(tmp_path, bok())
    regelbok = las_regelbok(fil, *konfiguration)
    assert regelbok.kontrollsumma == hashlib.sha256(fil.read_bytes()).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", regelbok.kontrollsumma)


def test_samma_innehall_ger_samma_kontrollsumma(tmp_path, konfiguration):
    forsta = las(tmp_path, bok(), konfiguration).kontrollsumma
    andra = tmp_path / "en_annan_mapp"
    andra.mkdir()
    assert las(andra, bok(), konfiguration).kontrollsumma == forsta
    assert las(tmp_path, bok(), konfiguration).kontrollsumma == forsta


def test_en_andrad_rad_ger_en_annan_kontrollsumma(tmp_path):
    # En enda rad i testbutikens regelbok ändras: R-BUTIK-STAD får nivå C i stället för B. Båda
    # filerna är giltiga, men summorna skiljer sig.
    fore = las_testbutikens_regelbok()
    rader = REGELBOK_FIL.read_text(encoding="utf-8").split("\n")
    nummer = [i for i, rad in enumerate(rader) if '"niva": "B"' in rad][0]
    andrade = rader[:nummer] + [rader[nummer].replace('"niva": "B"', '"niva": "C"')] + rader[nummer + 1:]
    assert [i for i, (gammal, ny) in enumerate(zip(rader, andrade)) if gammal != ny] == [nummer]
    fil = tmp_path / "regelbok.json"
    fil.write_text("\n".join(andrade), encoding="utf-8")
    efter = las_testbutikens_regelbok(fil)
    assert efter.regel_for_underlag("kvitto", "BUTIK-STAD", "2025-02-10")["niva"] == "C"
    assert efter.kontrollsumma != fore.kontrollsumma
    assert efter.kontrollsumma == hashlib.sha256(fil.read_bytes()).hexdigest()
    assert fore.kontrollsumma == hashlib.sha256(REGELBOK_FIL.read_bytes()).hexdigest()


@pytest.mark.parametrize("andring", ["mellanslag", "radslut", "anteckning", "ordning"])
def test_minsta_andring_ger_en_annan_kontrollsumma(tmp_path, konfiguration, andring):
    fil = skriv(tmp_path, bok())
    fore = las_regelbok(fil, *konfiguration).kontrollsumma
    text = fil.read_text(encoding="utf-8")
    if andring == "mellanslag":
        text = text.replace(": ", ":  ", 1)
    elif andring == "radslut":
        text = text + "\n"
    elif andring == "anteckning":
        text = text.replace("påhittad", "påhittaD", 1)
    else:
        data = bok()
        data["regler"] = list(reversed(data["regler"]))
        text = json.dumps(data, ensure_ascii=False)
    fil.write_text(text, encoding="utf-8")
    assert las_regelbok(fil, *konfiguration).kontrollsumma != fore


# --- Uppslagen ---

def test_uppslagen(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2025-03-01")["id"] == "R-1"
    assert regelbok.regel_for_underlag("kvitto", "MOTPART-A", "2025-03-01")["id"] == "R-2"
    assert regelbok.regel_for_z_rapport("KASSA-X", "2025-03-01")["id"] == "R-3"
    assert regelbok.regel_for_bankrad("regel_in", "2025-03-01")["id"] == "R-4"
    assert regelbok.regel_for_bankrad("regel_ut", "2025-03-01")["id"] == "R-5"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-B", "2025-03-01") is None
    assert regelbok.regel_for_z_rapport("KASSA-Y", "2025-03-01") is None
    assert regelbok.regel_for_bankrad("regel_okand", "2025-03-01") is None
    # Fel källa ger ingen träff: en Z-rapport hittar inte en regel för underlag.
    assert regelbok.regel_for_z_rapport("MOTPART-A", "2025-03-01") is None


def test_uppslaget_normaliserar_motparten_som_k4(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    for motpart in ["motpart-a", "MOTPART" + chr(0x2010) + "A", "MOTPART-A" + chr(0x200B), " MOTPART-A "]:
        assert regelbok.regel_for_underlag("leverantorsfaktura", motpart, "2025-03-01")["id"] == "R-1", motpart
    assert regelbok.regel_for_z_rapport("kassa-x", "2025-03-01")["id"] == "R-3"


def test_uppslaget_galler_bara_regelns_datum(tmp_path, konfiguration):
    data = bok()
    data["regler"][0]["villkor"]["giltig_till"] = "2024-12-31"
    data["regler"].append(regel("R-6", underlag(), {"grupp_a": "9002"}, giltig_fran="2025-01-01"))
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2023-12-31") is None
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2024-01-01")["id"] == "R-1"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2024-12-31")["id"] == "R-1"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2025-01-01")["id"] == "R-6"


@pytest.mark.parametrize("datum", ["2025-02-30", "2025-1-01", None, 20250101])
def test_ogiltigt_datum_i_uppslaget_stoppar(tmp_path, konfiguration, datum):
    regelbok = las(tmp_path, bok(), konfiguration)
    for uppslag in (lambda: regelbok.regel_for_underlag("kvitto", "MOTPART-A", datum),
                    lambda: regelbok.regel_for_z_rapport("KASSA-X", datum),
                    lambda: regelbok.regel_for_bankrad("regel_in", datum)):
        with pytest.raises(RegelbokFel, match="datumet ska vara ett giltigt datum"):
            uppslag()


@pytest.mark.parametrize("varde", [None, 5, True, ["MOTPART-A"]])
def test_uppslag_med_annat_an_text_stoppar(tmp_path, konfiguration, varde):
    regelbok = las(tmp_path, bok(), konfiguration)
    with pytest.raises(RegelbokFel, match="motpart ska vara text"):
        regelbok.regel_for_underlag("kvitto", varde, "2025-01-01")
    with pytest.raises(RegelbokFel, match="typ ska vara text"):
        regelbok.regel_for_underlag(varde, "MOTPART-A", "2025-01-01")
    with pytest.raises(RegelbokFel, match="kassaregister ska vara text"):
        regelbok.regel_for_z_rapport(varde, "2025-01-01")
    with pytest.raises(RegelbokFel, match="matchningsregel ska vara text"):
        regelbok.regel_for_bankrad(varde, "2025-01-01")


def test_resultatets_form(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    assert regelbok.godkand == {"av": "Påhittad godkännare", "datum": "2025-01-01"}
    assert regelbok.regler[1] == {
        "id": "R-2", "galler": underlag("kvitto"), "kontering": {"grupp_a": "9002"},
        "villkor": {"giltig_fran": "2024-01-01", "giltig_till": None, "hogst_belopp_ore": 5000,
                    "avdragsbegransad": True},
        "niva": "B",
    }
    assert regelbok.regler[2]["kontering"] == {"forsaljning": {"grupp_a": "9002", "grupp_b": "9002"},
                                               "betalsatt": {"post_kort": "0101"}}
    assert "R" in repr(regelbok) and regelbok.kontrollsumma[:12] in repr(regelbok)


# --- Det som godtas ---

def test_utan_anteckning_godtas(tmp_path, konfiguration):
    assert las(tmp_path, {k: v for k, v in bok().items() if k != "anteckning"}, konfiguration).version == 1


def test_tomma_listor_med_stangda_dagar_godtas(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(oppettider={"stangda_veckodagar": [], "stangda_datum": []}), konfiguration)
    assert regelbok.oppettider == {"stangda_veckodagar": [], "stangda_datum": []}


def test_alla_veckodagar_godtas(tmp_path, konfiguration):
    dagar = ["mandag", "tisdag", "onsdag", "torsdag", "fredag", "lordag", "sondag"]
    regelbok = las(tmp_path, bok(oppettider={"stangda_veckodagar": dagar, "stangda_datum": []}), konfiguration)
    assert regelbok.oppettider["stangda_veckodagar"] == dagar


def test_regler_for_samma_sak_som_foljer_pa_varandra_godtas(tmp_path, konfiguration):
    data = bok()
    data["regler"][0]["villkor"]["giltig_till"] = "2024-12-31"
    data["regler"].append(regel("R-6", underlag(), {"grupp_a": "9002"}, giltig_fran="2025-01-01", giltig_till=None))
    assert len(las(tmp_path, data, konfiguration).regler) == 6


def test_regler_for_samma_sak_i_omvand_tidsordning_godtas(tmp_path, konfiguration):
    # Den senare regeln står först i filen. Överlappskontrollen ska pröva båda riktningarna.
    data = bok(regler=[regel("R-1", underlag(), {"grupp_a": "9002"}, giltig_fran="2025-01-01"),
                       regel("R-2", underlag(), {"grupp_a": "9001"}, giltig_till="2024-12-31")])
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2024-12-31")["id"] == "R-2"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2025-01-01")["id"] == "R-1"


def test_samma_motpart_med_annan_typ_eller_kalla_godtas(tmp_path, konfiguration):
    # R-1 och R-2 har samma motpart men olika typ. En Z-rapport och en bankrad med samma namn som
    # motparten är också andra saker.
    data = med_regel(regel("R-6", z("MOTPART-A"), {"forsaljning": {"grupp_a": "9001"}, "betalsatt": {"x": "0101"}}))
    assert len(las(tmp_path, data, konfiguration).regler) == 6


def test_konto_och_varugrupp_som_galler_hela_regelns_tid_godtas(tmp_path, konfiguration):
    # Gränsfallen: kontot och satsen slutar samma dag som regeln, eller börjar samma dag.
    data = med_regel(regel("R-6", underlag(motpart="MOTPART-B"), {"grupp_a": "9003"}, giltig_till="2024-12-31"))
    data["regler"].append(regel("R-7", underlag(motpart="MOTPART-C"), {"grupp_c": "9004"}, giltig_fran="2025-01-01"))
    data["regler"].append(regel("R-8", underlag(motpart="MOTPART-D"), {"grupp_d": "9001", "grupp_b": "9001"},
                                giltig_till="2025-12-31"))
    assert len(las(tmp_path, data, konfiguration).regler) == 8


def test_granser_som_ar_lika_godtas(tmp_path, konfiguration):
    # En regels gräns lika med företagets B-gräns, och A-gräns lika med B-gräns, skärper inte men höjer inte heller.
    data = andrad((("granser", "a_hogst_ore"), 5000), (("regler", 1, "villkor", "hogst_belopp_ore"), 5000))
    data["regler"][4]["villkor"]["hogst_belopp_ore"] = 3000
    assert las(tmp_path, data, konfiguration).granser == {"a_hogst_ore": 5000, "b_hogst_ore": 5000}


def test_avdragsbegransad_false_och_grans_for_pengar_in_godtas(tmp_path, konfiguration):
    data = andrad((("regler", 1, "villkor", "avdragsbegransad"), False),
                  (("regler", 3, "villkor", "hogst_belopp_ore"), 4000))
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regler[1]["villkor"]["avdragsbegransad"] is False
    assert regelbok.regler[3]["villkor"]["hogst_belopp_ore"] == 4000


# --- Resultatet går inte att ändra ---

def test_regelboken_kan_inte_andras(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    with pytest.raises(AttributeError):
        regelbok._kontrollsumma = "0" * 64
    with pytest.raises(AttributeError):
        del regelbok._regelboken
    with pytest.raises(TypeError):
        regelbok._regelboken["granser"]["b_hogst_ore"] = 10 ** 9
    with pytest.raises(TypeError):
        regelbok._regelboken["regler"][0]["kontering"]["grupp_a"] = "9002"
    with pytest.raises(AttributeError):
        regelbok._regelboken["regler"].append({})
    kopior = regelbok.regler
    kopior[0]["kontering"]["grupp_a"] = "9002"
    kopior.clear()
    granser = regelbok.granser
    granser["b_hogst_ore"] = 10 ** 9
    regelbok.oppettider["stangda_veckodagar"].append("mandag")
    regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2025-01-01")["niva"] = "D"
    assert regelbok.regler[0]["kontering"]["grupp_a"] == "9001" and regelbok.regler[0]["niva"] == "A"
    assert regelbok.granser["b_hogst_ore"] == 5000
    assert regelbok.oppettider["stangda_veckodagar"] == ["sondag"]


def test_regelboken_kan_bara_skapas_av_las_regelbok():
    with pytest.raises(RegelbokFel, match="kan bara skapas av las_regelbok"):
        Regelbok(object(), "0" * 64, {})


def test_filen_andras_inte_av_inlasningen(tmp_path, konfiguration):
    data = bok()
    fore = copy.deepcopy(data)
    las(tmp_path, data, konfiguration)
    assert data == fore


# --- Indata: kontoplan, momssatser och matchningsformat ---

def test_kontoplanen_ska_komma_fran_las_kontoplan(tmp_path, konfiguration):
    _, momssatser, matchning = konfiguration
    with pytest.raises(RegelbokFel, match="kontoplanen ska komma från las_kontoplan, inte vara dict"):
        las_regelbok(skriv(tmp_path, bok()), copy.deepcopy(KONTOPLAN), momssatser, matchning)


def test_momssatserna_ska_komma_fran_las_momssatser(tmp_path, konfiguration):
    kontoplan, _, matchning = konfiguration
    with pytest.raises(RegelbokFel, match="momssatserna ska komma från las_momssatser, inte vara dict"):
        las_regelbok(skriv(tmp_path, bok()), kontoplan, copy.deepcopy(MOMSSATSER), matchning)


def test_matchningsformatet_kontrolleras_igen(tmp_path, konfiguration):
    kontoplan, momssatser, matchning = konfiguration
    trasigt = copy.deepcopy(matchning)
    del trasigt["kraver_inte_underlag"][1]["hogst_belopp_ore"]
    with pytest.raises(RegelbokFel, match="matchningsformatet är fel.*saknar 'hogst_belopp_ore'"):
        las_regelbok(skriv(tmp_path, bok()), kontoplan, momssatser, trasigt)


# --- Stoppregler ---

@pytest.mark.parametrize("ascii", [False, True], ids=["som_tecken", "som_kod_i_json"])
@pytest.mark.parametrize("tecken", DOLDA.values(), ids=DOLDA.keys())
@pytest.mark.parametrize("plats", ["anteckning", "foretag", "id", "motpart", "konto", "varugrupp", "veckodag",
                                   "nyckel"])
def test_dolt_tecken_var_som_helst_stoppar(tmp_path, konfiguration, tecken, ascii, plats):
    data = bok()
    if plats == "anteckning":
        data["anteckning"] = "på" + tecken + "hittad"
    elif plats == "foretag":
        data["foretag"] = "påhittat" + tecken + "-ab"
    elif plats == "id":
        data["regler"][0]["id"] = "R" + tecken + "-1"
    elif plats == "motpart":
        data["regler"][0]["galler"]["motpart"] = "MOTPART" + tecken + "-A"
    elif plats == "konto":
        data["regler"][0]["kontering"]["grupp_a"] = "90" + tecken + "01"
    elif plats == "varugrupp":
        data["regler"][1]["kontering"] = {"grupp" + tecken + "_a": "9002"}
    elif plats == "veckodag":
        data["oppettider"]["stangda_veckodagar"] = ["son" + tecken + "dag"]
    else:
        data["granser"] = {**data["granser"], "a" + tecken: 1}
    stoppas(tmp_path, data, konfiguration, "U+" + format(ord(tecken), "04X"), "inte syns", ascii=ascii)


@pytest.mark.parametrize("nyckel", REGELBOK_NYCKLAR)
def test_saknad_nyckel_stoppar(tmp_path, konfiguration, nyckel):
    stoppas(tmp_path, andrad(((nyckel,), BORT)), konfiguration, "saknar nyckeln " + repr(nyckel))


@pytest.mark.parametrize("nyckel", ["id", "galler", "kontering", "villkor", "niva"])
def test_regel_utan_nyckel_stoppar(tmp_path, konfiguration, nyckel):
    stoppas(tmp_path, andrad((("regler", 0, nyckel), BORT)), konfiguration, "regel nummer 1",
            "saknar nyckeln " + repr(nyckel))


R = "regler"
STOPPAS = {
    # Okända och saknade nycklar
    "okand_nyckel": (bok(extra=1), "okänd nyckel: 'extra'"),
    "okand_nyckel_i_regel": (andrad(((R, 0, "prioritet"), 1)), "okänd nyckel: 'prioritet'"),
    "okand_nyckel_i_galler": (andrad(((R, 0, "galler", "fakturanummer"), "F-1")), "okänd nyckel: 'fakturanummer'"),
    "kassaregister_i_galler_for_underlag": (andrad(((R, 0, "galler", "kassaregister"), "KASSA-X")),
                                            "okänd nyckel: 'kassaregister'"),
    "saknar_kalla": (andrad(((R, 0, "galler", "kalla"), BORT)), "saknar nyckeln 'kalla'"),
    "saknar_motpart": (andrad(((R, 0, "galler", "motpart"), BORT)), "saknar nyckeln 'motpart'"),
    "saknar_typ": (andrad(((R, 1, "galler", "typ"), BORT)), "saknar nyckeln 'typ'"),
    "saknar_kassaregister": (andrad(((R, 2, "galler", "kassaregister"), BORT)), "saknar nyckeln 'kassaregister'"),
    "saknar_matchningsregel": (andrad(((R, 3, "galler", "matchningsregel"), BORT)), "saknar nyckeln 'matchningsregel'"),
    "okand_nyckel_i_villkor": (andrad(((R, 0, "villkor", "lagst_belopp_ore"), 1)), "okänd nyckel: 'lagst_belopp_ore'"),
    "saknar_giltig_fran": (andrad(((R, 0, "villkor", "giltig_fran"), BORT)), "saknar nyckeln 'giltig_fran'"),
    "okand_nyckel_i_bankradens_kontering": (andrad(((R, 3, "kontering", "moms"), "0303")), "okänd nyckel: 'moms'"),
    "okand_nyckel_i_z_kontering": (andrad(((R, 2, "kontering", "moms"), {})), "okänd nyckel: 'moms'"),
    "saknar_betalsatt": (andrad(((R, 2, "kontering", "betalsatt"), BORT)), "saknar nyckeln 'betalsatt'"),
    "saknar_forsaljning": (andrad(((R, 2, "kontering", "forsaljning"), BORT)), "saknar nyckeln 'forsaljning'"),
    "okand_nyckel_i_granser": (andrad((("granser", "c_hogst_ore"), 1)), "okänd nyckel: 'c_hogst_ore'"),
    "saknar_b_grans": (andrad((("granser", "b_hogst_ore"), BORT)), "saknar nyckeln 'b_hogst_ore'"),
    "okand_nyckel_i_k9": (andrad((("k9", "procent"), 1)), "okänd nyckel: 'procent'"),
    "saknar_minst_historik": (andrad((("k9", "minst_historik"), BORT)), "saknar nyckeln 'minst_historik'"),
    "okand_nyckel_i_oppettider": (andrad((("oppettider", "oppna_dagar"), [])), "okänd nyckel: 'oppna_dagar'"),
    "saknar_stangda_datum": (andrad((("oppettider", "stangda_datum"), BORT)), "saknar nyckeln 'stangda_datum'"),
    "okand_nyckel_i_godkand": (andrad((("godkand", "tid"), "12:00")), "okänd nyckel: 'tid'"),
    "saknar_godkand_av": (andrad((("godkand", "av"), BORT)), "saknar nyckeln 'av'"),
    # Fel typ
    "filen_ar_en_lista": ([bok()], "ska vara ett objekt med nycklar, inte en lista"),
    "version_text": (bok(version="1"), "'version' ska vara ett heltal, inte text"),
    "version_decimaltal": (bok(version=1.0), "'version' ska vara ett heltal, inte decimaltal"),
    "version_true": (bok(version=True), "inte true eller false"),
    "version_noll": (bok(version=0), "'version' ska vara från 1"),
    "foretag_heltal": (bok(foretag=1), "'foretag' ska vara text, inte heltal"),
    "godkand_text": (bok(godkand="ja"), "'godkand' ska vara ett objekt"),
    "godkand_datum_ogiltigt": (andrad((("godkand", "datum"), "2025-02-30")), "'datum' i 'godkand' ska vara ett giltigt"),
    "granser_lista": (bok(granser=[1000, 5000]), "'granser' ska vara ett objekt"),
    "a_grans_decimaltal": (andrad((("granser", "a_hogst_ore"), 1000.0)), "'a_hogst_ore' i 'granser' ska vara ett"
                           " heltal, inte decimaltal"),
    "a_grans_kronor_med_decimal": (andrad((("granser", "a_hogst_ore"), 10.5)), "inte decimaltal"),
    "a_grans_nan": (andrad((("granser", "a_hogst_ore"), float("nan"))), "inte decimaltal"),
    "b_grans_text": (andrad((("granser", "b_hogst_ore"), "5000")), "'b_hogst_ore' i 'granser' ska vara ett heltal"),
    "b_grans_true": (andrad((("granser", "b_hogst_ore"), True)), "inte true eller false"),
    "a_grans_noll": (andrad((("granser", "a_hogst_ore"), 0)), "ska vara från 1"),
    "a_grans_negativ": (andrad((("granser", "a_hogst_ore"), -1000)), "ska vara från 1"),
    "a_hogre_an_b": (andrad((("granser", "a_hogst_ore"), 5001)), "'a_hogst_ore' (5001) är högre än 'b_hogst_ore'"
                     " (5000)"),
    "k9_lista": (bok(k9=[3, 300, 33]), "'k9' ska vara ett objekt"),
    "k9_minst_historik_noll": (andrad((("k9", "minst_historik"), 0)), "'minst_historik' i 'k9' ska vara från 1"),
    "k9_minst_historik_decimaltal": (andrad((("k9", "minst_historik"), 3.0)), "inte decimaltal"),
    "k9_hogst_under_100": (andrad((("k9", "hogst_procent_av_median"), 99)), "'hogst_procent_av_median' i 'k9' ska"
                           " vara från 100"),
    "k9_lagst_over_100": (andrad((("k9", "lagst_procent_av_median"), 101)), "till och med 100, inte 101"),
    "k9_lagst_negativ": (andrad((("k9", "lagst_procent_av_median"), -1)), "'lagst_procent_av_median' i 'k9' ska"
                         " vara från 0"),
    "oppettider_lista": (bok(oppettider=["sondag"]), "'oppettider' ska vara ett objekt"),
    "veckodagar_text": (andrad((("oppettider", "stangda_veckodagar"), "sondag")), "'stangda_veckodagar' ska vara en"
                        " lista, inte text"),
    "veckodag_okand": (andrad((("oppettider", "stangda_veckodagar"), ["söndag"])), "'söndag' i 'stangda_veckodagar'"
                       " är ingen veckodag"),
    "veckodag_stor_bokstav": (andrad((("oppettider", "stangda_veckodagar"), ["Sondag"])), "ingen veckodag"),
    "veckodag_heltal": (andrad((("oppettider", "stangda_veckodagar"), [7])), "heltal i 'stangda_veckodagar' är ingen"),
    "veckodag_dubblett": (andrad((("oppettider", "stangda_veckodagar"), ["sondag", "lordag", "sondag"])),
                          "'sondag' står flera gånger i 'stangda_veckodagar'"),
    "stangda_datum_objekt": (andrad((("oppettider", "stangda_datum"), {})), "'stangda_datum' ska vara en lista"),
    "stangt_datum_ogiltigt": (andrad((("oppettider", "stangda_datum"), ["2025-01-01", "2025-13-01"])),
                              "datum nummer 2 i 'stangda_datum' ska vara ett giltigt datum"),
    "stangt_datum_dubblett": (andrad((("oppettider", "stangda_datum"), ["2025-01-01", "2025-01-01"])),
                              "'2025-01-01' står flera gånger i 'stangda_datum'"),
    "regler_objekt": (bok(regler={"R-1": {}}), "'regler' ska vara en lista med regler, inte ett objekt"),
    "regel_lista": (bok(regler=[["R-1"]]), "regel nummer 1 ska vara ett objekt"),
    "id_heltal": (andrad(((R, 0, "id"), 1)), "'id' i regel nummer 1 ska vara text, inte heltal"),
    "galler_text": (andrad(((R, 0, "galler"), "underlag")), "'galler' i regel nummer 1 (R-1) ska vara ett objekt"),
    "kalla_okand": (andrad(((R, 0, "galler", "kalla"), "kvitto")), "'kalla' i 'galler' i regel nummer 1 (R-1) ska"
                    " vara en av 'underlag', 'z_rapport', 'bankrad', inte 'kvitto'"),
    "kalla_heltal": (andrad(((R, 0, "galler", "kalla"), 1)), "inte heltal"),
    "typ_okand": (andrad(((R, 0, "galler", "typ"), "faktura")), "'typ' i 'galler' i regel nummer 1 (R-1) ska vara"
                  " en av 'leverantorsfaktura', 'kvitto', inte 'faktura'"),
    "motpart_heltal": (andrad(((R, 0, "galler", "motpart"), 5)), "'motpart' i 'galler' i regel nummer 1 (R-1) ska"
                       " vara text"),
    "matchningsregel_lista": (andrad(((R, 3, "galler", "matchningsregel"), ["regel_in"])), "'matchningsregel' i"
                              " 'galler' i regel nummer 4 (R-4) ska vara text"),
    "villkor_lista": (andrad(((R, 0, "villkor"), ["2024-01-01"])), "'villkor' i regel nummer 1 (R-1) ska vara ett"
                      " objekt"),
    "giltig_fran_ogiltigt": (andrad(((R, 0, "villkor", "giltig_fran"), "2024-02-30")), "'giltig_fran' i regel"
                             " nummer 1 (R-1) ska vara ett giltigt datum"),
    "giltig_fran_null": (andrad(((R, 0, "villkor", "giltig_fran"), None)), "'giltig_fran'", "inte null"),
    "giltig_till_ogiltigt": (andrad(((R, 0, "villkor", "giltig_till"), "2025")), "'giltig_till' i regel nummer 1"),
    "slutar_fore_start": (andrad(((R, 0, "villkor", "giltig_till"), "2023-12-31")), "regel nummer 1 (R-1) slutar"
                          " 2023-12-31, före sitt första datum 2024-01-01"),
    "regelns_grans_decimaltal": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), 2500.0)), "'hogst_belopp_ore' i"
                                 " regel nummer 2 (R-2) ska vara ett heltal, inte decimaltal"),
    "regelns_grans_text": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), "2500")), "inte text"),
    "regelns_grans_noll": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), 0)), "ska vara från 1"),
    "regelns_grans_negativ": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), -2500)), "ska vara från 1"),
    "regelns_grans_null": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), None)), "inte null"),
    "avdragsbegransad_text": (andrad(((R, 1, "villkor", "avdragsbegransad"), "ja")), "'avdragsbegransad' i regel"
                              " nummer 2 (R-2) ska vara true eller false, inte text"),
    "avdragsbegransad_heltal": (andrad(((R, 1, "villkor", "avdragsbegransad"), 1)), "inte heltal"),
    "avdragsbegransad_null": (andrad(((R, 1, "villkor", "avdragsbegransad"), None)), "inte null"),
    "niva_okand": (andrad(((R, 0, "niva"), "E")), "'niva' i regel nummer 1 (R-1) ska vara en av 'A', 'B', 'C', 'D'"),
    "niva_liten_bokstav": (andrad(((R, 0, "niva"), "a")), "'niva' i regel nummer 1"),
    "niva_heltal": (andrad(((R, 0, "niva"), 1)), "'niva' i regel nummer 1"),
    "anteckning_i_regel_heltal": (andrad(((R, 0, "anteckning"), 1)), "'anteckning' i regel nummer 1 (R-1) ska vara"
                                  " text"),
    "anteckning_lista": (bok(anteckning=["x"]), "'anteckning' ska vara text, inte en lista"),
    "kontering_lista": (andrad(((R, 0, "kontering"), ["9001"])), "'kontering' i regel nummer 1 (R-1) ska vara ett"
                        " objekt med ett konto per varugrupp, inte en lista"),
    "bankradens_kontering_text": (andrad(((R, 3, "kontering"), "0101")), "'kontering' i regel nummer 4 (R-4) ska"
                                  " vara ett objekt med nycklar, inte text"),
    "z_kontering_lista": (andrad(((R, 2, "kontering"), [])), "'kontering' i regel nummer 3 (R-3) ska vara ett"
                          " objekt med nycklar, inte en lista"),
    "forsaljning_lista": (andrad(((R, 2, "kontering", "forsaljning"), ["9002"])), "'forsaljning' i 'kontering' i"
                          " regel nummer 3 (R-3) ska vara ett objekt med ett konto per varugrupp"),
    "betalsatt_lista": (andrad(((R, 2, "kontering", "betalsatt"), ["0101"])), "'betalsatt' i 'kontering' i regel"
                        " nummer 3 (R-3) ska vara ett objekt med ett konto per betalsätt, inte en lista"),
    "konto_heltal": (andrad(((R, 0, "kontering", "grupp_a"), 9001)), "kontot för varugruppen 'grupp_a' i"
                     " 'kontering' i regel nummer 1 (R-1) ska vara text", "inte heltal"),
    "konto_null": (andrad(((R, 3, "kontering", "motkonto"), None)), "kontot för 'motkonto'", "inte null"),
    "betalsattets_konto_decimaltal": (andrad(((R, 2, "kontering", "betalsatt", "post_kort"), 101.0)),
                                      "kontot för betalsättet 'post_kort'", "inte decimaltal"),
    # Tomma värden
    "foretag_tomt": (bok(foretag=""), "'foretag' får inte vara tom"),
    "foretag_blanksteg": (bok(foretag="  "), "'foretag' får inte vara tom"),
    "foretag_blanksteg_sist": (bok(foretag="påhittat-ab "), "blanksteg först eller sist"),
    "anteckning_tom": (bok(anteckning=""), "'anteckning' får inte vara tom"),
    "godkand_av_tom": (andrad((("godkand", "av"), "")), "'av' i 'godkand' får inte vara tom"),
    "inga_regler": (bok(regler=[]), "'regler' är tom"),
    "id_tomt": (andrad(((R, 0, "id"), "")), "'id' i regel nummer 1 får inte vara tom"),
    "motpart_tom": (andrad(((R, 0, "galler", "motpart"), "  ")), "'motpart' i 'galler' i regel nummer 1 (R-1) får"
                    " inte vara tom"),
    "kassaregister_tomt": (andrad(((R, 2, "galler", "kassaregister"), "")), "'kassaregister'", "får inte vara tom"),
    "matchningsregel_tom": (andrad(((R, 3, "galler", "matchningsregel"), "")), "'matchningsregel'",
                            "får inte vara tom"),
    "kontering_tom": (andrad(((R, 0, "kontering"), {})), "'kontering' i regel nummer 1 (R-1) är tom"),
    "forsaljning_tom": (andrad(((R, 2, "kontering", "forsaljning"), {})), "'forsaljning' i 'kontering' i regel"
                        " nummer 3 (R-3) är tom"),
    "betalsatt_tom": (andrad(((R, 2, "kontering", "betalsatt"), {})), "'betalsatt' i 'kontering' i regel nummer 3"
                      " (R-3) är tom"),
    "betalsattets_namn_tomt": (andrad(((R, 2, "kontering", "betalsatt"), {"": "0101"})), "betalsättet ''",
                               "får inte vara tom"),
    "betalsattets_namn_blanksteg_sist": (andrad(((R, 2, "kontering", "betalsatt"), {"post_kort ": "0101"})),
                                         "blanksteg först eller sist"),
    "bankradens_kontering_tom": (andrad(((R, 3, "kontering"), {})), "'kontering' i regel nummer 4 (R-4) är tom",
                                 "'motkonto', 'avgift', 'kostnad'"),
    "konto_tomt": (andrad(((R, 0, "kontering", "grupp_a"), "")), "kontot för varugruppen 'grupp_a'", "är '', som"
                   " inte finns i kontoplanen"),
    # Dublettregler och tvetydiga regler
    "samma_id": (med_regel(regel("R-1", underlag(motpart="MOTPART-B"), {"grupp_a": "9001"})),
                 "regel-id 'R-1' står flera gånger"),
    "samma_id_efter_normalisering": (med_regel(regel("r" + chr(0x2010) + "1", underlag(motpart="MOTPART-B"),
                                                     {"grupp_a": "9001"})), "står flera gånger (som 'R-1')"),
    "dublettregel": (med_regel(regler()[0] | {"id": "R-6"}), "reglerna 'R-1' och 'R-6' kan båda passa samma sak"),
    "samma_motpart_efter_normalisering": (med_regel(regel("R-6", underlag(motpart="motpart - a"), {"grupp_a": "9002"},
                                                          giltig_fran="2030-01-01")),
                                          "reglerna 'R-1' och 'R-6' kan båda passa"),
    "overlappar_en_dag": (bok(regler=[regel("R-1", underlag(), {"grupp_a": "9001"}, giltig_till="2025-01-01"),
                                      regel("R-2", underlag(), {"grupp_a": "9002"}, giltig_fran="2025-01-01")]),
                          "reglerna 'R-1' och 'R-2' kan båda passa"),
    "overlappar_inuti": (bok(regler=[regel("R-1", underlag(), {"grupp_a": "9001"}, giltig_fran="2025-03-01",
                                           giltig_till="2025-03-31"),
                                     regel("R-2", underlag(), {"grupp_a": "9002"}, giltig_till="2025-12-31")]),
                         "reglerna 'R-1' och 'R-2' kan båda passa"),
    "overlappar_bakat": (bok(regler=[regel("R-1", underlag(), {"grupp_a": "9001"}, giltig_fran="2025-01-01"),
                                     regel("R-2", underlag(), {"grupp_a": "9002"}, giltig_till="2025-01-01")]),
                         "reglerna 'R-1' och 'R-2' kan båda passa"),
    "samma_kassa": (med_regel(regel("R-6", z("kassa-x"), {"forsaljning": {"grupp_a": "9001"}, "betalsatt": {"x": "0101"}},
                                    niva="C")), "reglerna 'R-3' och 'R-6' kan båda passa"),
    "samma_matchningsregel": (med_regel(regel("R-6", bankrad(), {"motkonto": "0101"})),
                              "reglerna 'R-4' och 'R-6' kan båda passa"),
    # D20: en regel kan bara skärpa företagets gränser
    "regelns_grans_hogre_an_b": (andrad(((R, 1, "villkor", "hogst_belopp_ore"), 5001)), "'hogst_belopp_ore' i regel"
                                 " nummer 2 (R-2) (5001) är högre än företagets gräns 'b_hogst_ore' (5000)",
                                 "kan bara skärpa företagets gränser, aldrig höja dem"),
    "bankradens_grans_hogre_an_matchningen": (andrad(((R, 4, "villkor", "hogst_belopp_ore"), 3001)),
                                              "(3001) är högre än gränsen för regeln 'regel_ut' i matchningsformatet"
                                              " (3000)", "aldrig höja den"),
    "pengar_ut_utan_grans": (andrad(((R, 4, "villkor", "hogst_belopp_ore"), BORT)), "regel nummer 5 (R-5) gäller"
                             " bankrader med pengar ut och saknar 'hogst_belopp_ore'"),
    "bankrad_niva_a": (andrad(((R, 3, "niva"), "A")), "regel nummer 4 (R-4) gäller bankrader och har nivå 'A'",
                       "aldrig nivå A"),
    "bankrad_ut_niva_a": (andrad(((R, 4, "niva"), "A")), "regel nummer 5 (R-5) gäller bankrader och har nivå 'A'"),
    # Okända referenser till matchningsformatet, kontoplanen och momsfilen
    "okand_matchningsregel": (andrad(((R, 3, "galler", "matchningsregel"), "regel_okand")), "pekar på regeln"
                              " 'regel_okand' i matchningsformatet, som inte finns. Reglerna där är 'regel_in',"
                              " 'regel_ut'"),
    "matchningsregel_annan_stavning": (andrad(((R, 3, "galler", "matchningsregel"), "Regel_in")),
                                       "'Regel_in' i matchningsformatet, som inte finns"),
    "okant_konto": (andrad(((R, 0, "kontering", "grupp_a"), "9999")), "kontot för varugruppen 'grupp_a' i"
                    " 'kontering' i regel nummer 1 (R-1) är '9999', som inte finns i kontoplanen"),
    "okant_konto_med_mellanslag": (andrad(((R, 0, "kontering", "grupp_a"), "9001 ")), "'9001 ', som inte finns"),
    "okant_konto_for_betalsatt": (andrad(((R, 2, "kontering", "betalsatt", "post_kort"), "1234")),
                                  "kontot för betalsättet 'post_kort'", "'1234', som inte finns i kontoplanen"),
    "okant_konto_for_forsaljning": (andrad(((R, 2, "kontering", "forsaljning", "grupp_b"), "1234")),
                                    "varugruppen 'grupp_b' i 'forsaljning' i 'kontering' i regel nummer 3",
                                    "'1234', som inte finns"),
    "okant_konto_for_bankrad": (andrad(((R, 4, "kontering", "kostnad"), "1234")), "kontot för 'kostnad' i"
                                " 'kontering' i regel nummer 5 (R-5) är '1234', som inte finns"),
    "konto_slutar_fore_regeln": (andrad(((R, 0, "kontering", "grupp_a"), "9003")), "'9003', som bara gäller från"
                                 " 2024-01-01 till 2024-12-31. Regeln gäller från 2024-01-01 till tills vidare"),
    "konto_borjar_efter_regeln": (andrad(((R, 0, "kontering", "grupp_a"), "9004")), "'9004', som bara gäller från"
                                  " 2025-01-01 till tills vidare"),
    "konto_slutar_fore_regelns_slut": (andrad(((R, 0, "kontering", "grupp_a"), "9003"),
                                              ((R, 0, "villkor", "giltig_till"), "2025-01-01")),
                                       "Regeln gäller från 2024-01-01 till 2025-01-01"),
    "okand_varugrupp": (andrad(((R, 0, "kontering", "grupp_x"), "9001")), "varugruppen 'grupp_x' i 'kontering' i"
                        " regel nummer 1 (R-1) har ingen sats i momsfilen", "ingen varugrupp 'grupp_x'"),
    "okand_varugrupp_i_forsaljning": (andrad(((R, 2, "kontering", "forsaljning", "grupp_x"), "9002")),
                                      "varugruppen 'grupp_x' i 'forsaljning'"),
    "varugrupp_utan_sats_i_borjan": (andrad(((R, 0, "kontering", "grupp_c"), "9001")), "varugruppen 'grupp_c'",
                                     "från 2024-01-01 till tills vidare", "ingen sats för varugruppen 'grupp_c' på"
                                     " 2024-01-01"),
    "varugrupp_utan_sats_i_slutet": (andrad(((R, 0, "kontering", "grupp_d"), "9001")), "varugruppen 'grupp_d'",
                                     "ingen sats för varugruppen 'grupp_d' på 2026-01-01"),
    "varugrupp_utan_sats_efter_regelns_slut": (andrad(((R, 0, "kontering", "grupp_d"), "9001"),
                                                      ((R, 0, "villkor", "giltig_till"), "2026-01-01")),
                                               "ingen sats för varugruppen 'grupp_d' på 2026-01-01"),
    "varugrupp_stor_bokstav": (andrad(((R, 1, "kontering"), {"Grupp_a": "9002"})), "varugruppen 'Grupp_a'"),
}


@pytest.mark.parametrize("data, texter", [(fall[0], fall[1:]) for fall in STOPPAS.values()], ids=STOPPAS.keys())
def test_stoppregel(tmp_path, konfiguration, data, texter):
    stoppas(tmp_path, data, konfiguration, *texter)


@pytest.mark.parametrize("text, vad", [
    ('{"foretag": "A", "foretag": "B"}', "står flera gånger"),
    ('{"regler": [{"id": "R-1", "id": "R-2"}]}', "står flera gånger"),
    ('{"version": 1234567890123456}', "högst 15 siffror"),
    ('{"foretag": "x",', "är inte giltig JSON"),
])
def test_trasig_json_stoppar(tmp_path, konfiguration, text, vad):
    fil = tmp_path / "regelbok.json"
    fil.write_text(text, encoding="utf-8")
    with pytest.raises(RegelbokFel, match=re.escape(vad)):
        las_regelbok(fil, *konfiguration)


def test_fil_som_inte_ar_utf8_stoppar(tmp_path, konfiguration):
    fil = tmp_path / "regelbok.json"
    fil.write_bytes(json.dumps(bok(), ensure_ascii=False).encode("cp1252"))
    with pytest.raises(RegelbokFel, match="inte sparat som UTF-8"):
        las_regelbok(fil, *konfiguration)


def test_for_djup_fil_stoppar(tmp_path, konfiguration):
    fil = tmp_path / "regelbok.json"
    fil.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
    with pytest.raises(RegelbokFel, match="En regelbok har bara fem nivåer"):
        las_regelbok(fil, *konfiguration)


@pytest.mark.parametrize("sokvag", [None, 1, True])
def test_sokvag_av_fel_typ_stoppar(konfiguration, sokvag):
    with pytest.raises(RegelbokFel, match="sökvägen ska vara text eller en Path"):
        las_regelbok(sokvag, *konfiguration)


def test_fil_som_saknas_stoppar(tmp_path, konfiguration):
    with pytest.raises(RegelbokFel, match="Regelboken saknas"):
        las_regelbok(tmp_path / "finns_inte.json", *konfiguration)


def test_mapp_i_stallet_for_fil_stoppar(tmp_path, konfiguration):
    with pytest.raises(RegelbokFel, match="är en mapp, inte en fil"):
        las_regelbok(tmp_path, *konfiguration)
