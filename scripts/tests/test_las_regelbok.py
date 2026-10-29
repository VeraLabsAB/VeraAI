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
from las_matchningsformat import ladda_matchningsformat, las_matchningsformat  # noqa: E402
from las_momssatser import las_momssatser  # noqa: E402
from las_regelbok import REGELBOK_NYCKLAR, Regelbok, RegelbokFel, las_regelbok  # noqa: E402
from test_las_momssatser import DOLDA, N1_OSYNLIGA, json_block_i_design  # noqa: E402


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
            las_matchningsformat(mapp / "matchning.json"))


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


def bokforing():
    """Felfria val i 'bokforing', med andra datum än testbutikens där det finns flera att välja på."""
    return {"antaget": True, "metod": "faktureringsmetoden",
            "verifikationsdatum": {"leverantorsfaktura": "fakturadatum", "betalning": "bokforingsdag",
                                   "kvitto": "transaktionsdag", "bankrad": "bokforingsdag"}}


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
        # Nyckeln krävs (Hugos beslut 2026-10-29, inför uppgift 4).
        "bokforing": bokforing(),
        # Listan krävs och får inte vara tom (Hugos beslut 2026-10-27, beslut a). En påhittad ägare.
        "agare_och_narstaende": ["PAHITTAD-AGARE"],
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


def med_agare(agare, *nya_regler):
    """En felfri regelbok med listan agare_och_narstaende och reglerna nya_regler till sist."""
    return bok(agare_och_narstaende=agare, regler=regler() + list(nya_regler))


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
                        las_matchningsformat(TESTBUTIKEN / "matchning.json"))


def test_testforetagets_fil_laddas():
    regelbok = las_testbutikens_regelbok()
    assert regelbok.foretag == "syntet-testbutik" and regelbok.version == 1
    assert len(regelbok.regler) == 10
    # Hugos beslut D18 och D19: A-gräns 20 000 kr, B-gräns 40 000 kr, 3 godkännanden, K9 3 / 300 % / 33 %.
    assert regelbok.granser == {"a_hogst_ore": 2000000, "b_hogst_ore": 4000000}
    assert regelbok.k9 == {"minst_historik": 3, "hogst_procent_av_median": 300, "lagst_procent_av_median": 33}
    assert regelbok.oppettider == {"stangda_veckodagar": ["sondag"], "stangda_datum": ["2025-01-01", "2025-01-06"]}
    # B3, D1 och D14, antagna för testföretaget (Hugos beslut 2026-10-29).
    assert regelbok.bokforing == {"antaget": True, "metod": "faktureringsmetoden",
                                  "verifikationsdatum": {"leverantorsfaktura": "fakturadatum",
                                                         "betalning": "transaktionsdag", "kvitto": "kvittodatum",
                                                         "bankrad": "transaktionsdag"}}
    datum = "2025-02-06"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "LEV-TE", datum)["id"] == "R-LEV-TE"
    assert regelbok.regel_for_underlag("kvitto", "RESTAURANG-1", datum)["villkor"]["avdragsbegransad"] is True
    assert regelbok.regel_for_z_rapport("TB-KASSA-1", datum)["id"] == "R-Z-TB-KASSA-1"
    assert regelbok.regel_for_bankrad("bankens-avgifter", datum)["villkor"]["hogst_belopp_ore"] == 25000
    # Ny motpart: ingen regel. Det blir ett ärende senare, Vera gissar inget konto.
    assert regelbok.regel_for_underlag("leverantorsfaktura", "HYRESVARD", datum) is None
    # Före regelns första dag finns ingen regel.
    assert regelbok.regel_for_underlag("leverantorsfaktura", "LEV-TE", "2024-12-31") is None
    # Ägare och närstående (K7). Testbutiken har ingen regel för ägaren än.
    assert regelbok.agare_och_narstaende == ["AGARE-1"]
    assert regelbok.ar_agare_eller_narstaende("AGARE-1") is True
    assert regelbok.ar_agare_eller_narstaende("LEV-TE") is False


def test_testforetagets_fil_har_exakt_vardena_i_design_och_fyra_tillagg():
    # Inga nya värden har hittats på: filen är exemplet i DESIGN-regelbok.md avsnitt 1, med fyra
    # tillägg som Hugo har godkänt och som alla kommer från redan bestämda värden:
    # - 'oppettider' (Hugos beslut D21), med testbutikens stängda dagar ur testdata/README.md,
    # - gränsen för bankavgiften, som är en regel för pengar ut och därför måste ha
    #   'hogst_belopp_ore'. Värdet är gränsen i matchning.json, som Hugo bestämde 2026-10-25,
    # - 'agare_och_narstaende' (Hugos beslut 2026-10-26), med det syntetiska värdet AGARE-1 ur
    #   DESIGN-regelbok.md avsnitt 1 och testforetag/FIKTIVT_FORETAG.md,
    # - 'bokforing' (Hugos OK i chatten 2026-10-29, i sessionen för uppgift 4), med valen i B3, D1 och D14:
    #   faktureringsmetoden, fakturadatum, kvittodatum och transaktionsdagen, märkta antagna.
    design = json_block_i_design("regler")
    design["oppettider"] = {"stangda_veckodagar": ["sondag"], "stangda_datum": ["2025-01-01", "2025-01-06"]}
    design["agare_och_narstaende"] = ["AGARE-1"]
    bokforing_ = json.loads(REGELBOK_FIL.read_text(encoding="utf-8"))["bokforing"]
    assert bokforing_.pop("anteckning").startswith("ANTAGET för testföretaget (Hugos beslut 2026-10-29")
    assert bokforing_ == {"antaget": True, "metod": "faktureringsmetoden",
                          "verifikationsdatum": {"leverantorsfaktura": "fakturadatum", "betalning": "transaktionsdag",
                                                 "kvitto": "kvittodatum", "bankrad": "transaktionsdag"}}
    design["bokforing"] = json.loads(REGELBOK_FIL.read_text(encoding="utf-8"))["bokforing"]
    avgift = [regel_ for regel_ in design["regler"] if regel_["id"] == "R-BANK-AVGIFT"]
    assert len(avgift) == 1 and "hogst_belopp_ore" not in avgift[0]["villkor"]
    avgift[0]["villkor"]["hogst_belopp_ore"] = 25000
    assert json.loads(REGELBOK_FIL.read_text(encoding="utf-8")) == design
    # Tilläggens källor.
    assert "Stängt söndagar, 1 januari och 6 januari" in (AGENT / "testdata" / "README.md").read_text(encoding="utf-8")
    bankavgift = [r for r in ladda_matchningsformat(TESTBUTIKEN / "matchning.json")["kraver_inte_underlag"]
                  if r["namn"] == "bankens-avgifter"]
    assert bankavgift[0]["hogst_belopp_ore"] == 25000
    assert "En regel med motparten `AGARE-1` får bara" in (AGENT / "DESIGN-regelbok.md").read_text(encoding="utf-8")
    assert "| AGARE-1 | Ägare 1 (påhittad person)" in (AGENT / "testforetag" / "FIKTIVT_FORETAG.md").read_text(
        encoding="utf-8")


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


def test_uppslaget_for_agare_och_narstaende(tmp_path, konfiguration):
    # Motparten jämförs efter normaliseringen, som i K4 och regel_for_underlag (DESIGN avsnitt 1).
    data = bok(agare_och_narstaende=["AGARE-X", "NARSTAENDE-Y"])
    data["regler"].append(regel("R-6", underlag("kvitto", "agare" + chr(0x2010) + "x"), {"grupp_a": "9002"}, niva="D"))
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.agare_och_narstaende == ["AGARE-X", "NARSTAENDE-Y"]
    for motpart in ["AGARE-X", "agare-x", "AGARE" + chr(0x2010) + "X", "AGARE-X" + chr(0x200B), " AGARE-X ",
                    "narstaende-y"]:
        assert regelbok.ar_agare_eller_narstaende(motpart) is True, motpart
    for motpart in ["MOTPART-A", "AGARE-XY", "AGARE", "", "NARSTAENDE-X"]:
        assert regelbok.ar_agare_eller_narstaende(motpart) is False, motpart


def test_m8_agare_med_osynligt_tecken_fore_accenten_kanns_igen(tmp_path, konfiguration):
    # M8 (granskning 7): "A" + osynligt tecken + trema ser ut som "Ä". Förut kändes ägaren inte igen.
    regelbok = las(tmp_path, bok(agare_och_narstaende=["ÄGARE-X"]), konfiguration)
    for osynligt in (chr(0x034F), chr(0x200B), chr(0xFE00)):
        assert regelbok.ar_agare_eller_narstaende("A" + osynligt + chr(0x0308) + "GARE-X") is True


# --- Beslut (a): en saknad, tom eller oläsbar lista över ägare och närstående stoppar hela körningen ---
# Hugos beslut 2026-10-27 (SPEC avsnitt 11). Förut godtogs en saknad nyckel och en tom lista.

STOPP_UTAN_AGARLISTA = "Hela körningen stoppas"


def test_a_saknad_agarlista_stoppar_hela_korningen(tmp_path, konfiguration):
    data = bok()
    del data["agare_och_narstaende"]
    stoppas(tmp_path, data, konfiguration, "saknar nyckeln 'agare_och_narstaende'", "ägare och närstående",
            STOPP_UTAN_AGARLISTA)


def test_a_tom_agarlista_stoppar_hela_korningen(tmp_path, konfiguration):
    stoppas(tmp_path, bok(agare_och_narstaende=[]), konfiguration, "'agare_och_narstaende' är tom",
            STOPP_UTAN_AGARLISTA)


@pytest.mark.parametrize("varde, text", [
    ("PAHITTAD-AGARE", "'agare_och_narstaende' ska vara en lista, inte text"),
    (None, "'agare_och_narstaende' ska vara en lista"),
    ({"PAHITTAD-AGARE": True}, "'agare_och_narstaende' ska vara en lista"),
    (7, "'agare_och_narstaende' ska vara en lista"),
    (["PAHITTAD-AGARE", 1], "motpart nummer 2 i 'agare_och_narstaende'"),
    ([None], "motpart nummer 1 i 'agare_och_narstaende'"),
    ([""], "motpart nummer 1 i 'agare_och_narstaende' får inte vara tom"),
    (["PAHITTAD-AGARE", "pahittad-agare"], "står flera gånger i 'agare_och_narstaende'"),
    (["PAHITTAD&AGARE"], "motpart nummer 1 i 'agare_och_narstaende' har tecknet U+0026"),
], ids=["text", "null", "objekt", "heltal", "heltal_i_listan", "null_i_listan", "tom_text", "dubblett", "fel_tecken"])
def test_a_olasbar_agarlista_stoppar_hela_korningen(tmp_path, konfiguration, varde, text):
    stoppas(tmp_path, bok(agare_och_narstaende=varde), konfiguration, text, STOPP_UTAN_AGARLISTA)


def test_a_utan_godkand_agarlista_finns_ingen_regelbok_att_ga_vidare_med(tmp_path, konfiguration):
    # Allt efter regelboken (matchningen och konteringsförslagen) tar bara emot en Regelbok från
    # las_regelbok. När listan stoppar regelboken finns ingen Regelbok, så ingenting kan gå vidare.
    for data in (bok(agare_och_narstaende=[]), bok(agare_och_narstaende=None)):
        with pytest.raises(RegelbokFel, match=STOPP_UTAN_AGARLISTA):
            las(tmp_path, data, konfiguration)
    # Skydd: med en giltig lista går regelboken att läsa.
    assert las(tmp_path, bok(), konfiguration).agare_och_narstaende == ["PAHITTAD-AGARE"]


# --- Granskning 10, P1: ett namn utan bokstäver och siffror räknas som tomt ---
# Hugos beslut 2026-10-28. Ett namn som bara har skiljetecken och mellanslag blir tomt när det delas i
# ord (normalisering.star_som_hela_ord) och står därför aldrig i en bankrad. En lista med ett sådant namn
# ser ifylld ut men känner aldrig igen den ägaren, och stoppar hela körningen som en tom lista.

TANKSTRECK = chr(0x2013)


@pytest.mark.parametrize("agare, nummer", [
    (["-"], 1),
    (["."], 1),
    (["_"], 1),
    (["-.-"], 1),
    (["_ ."], 1),
    ([TANKSTRECK], 1),
    (["PAHITTAD-AGARE", "-"], 2),
    (["-", "PAHITTAD-AGARE"], 1),
], ids=["bindestreck", "punkt", "understreck", "blandat", "med_mellanslag", "tankstreck", "efter_ett_giltigt_namn",
        "fore_ett_giltigt_namn"])
def test_p1_namn_utan_bokstaver_och_siffror_stoppar_hela_korningen(tmp_path, konfiguration, agare, nummer):
    namn = agare[nummer - 1]
    meddelande = stoppas(
        tmp_path, bok(agare_och_narstaende=agare), konfiguration,
        "motpart nummer " + str(nummer) + " i listan över ägare och närstående ('agare_och_narstaende') är "
        + repr(namn) + ", som saknar bokstäver och siffror",
        "aldrig kan kännas igen i en bankrad",
        "skriv in ägarens eller den närståendes namn",
        STOPP_UTAN_AGARLISTA,
    )
    # Felet säger vilken fil (stoppas prövar början), vilket värde, var det står och hur det rättas, i en
    # mening före texten om att hela körningen stoppas.
    forklaring = meddelande.split(": ", 1)[1].split(" Utan en giltig lista")[0]
    assert forklaring.endswith("."), meddelande
    assert forklaring.replace(repr(namn), "").count(".") == 1, meddelande


def test_p1_ingen_regelbok_med_ett_namn_utan_bokstaver_och_siffror(tmp_path, konfiguration):
    # Utan en Regelbok kan varken matchningen eller konteringsförslagen köras.
    for agare in (["-"], ["PAHITTAD-AGARE", "-"]):
        with pytest.raises(RegelbokFel, match=STOPP_UTAN_AGARLISTA):
            las(tmp_path, bok(agare_och_narstaende=agare), konfiguration)


def test_p1_namn_med_minst_en_bokstav_eller_siffra_godtas(tmp_path, konfiguration):
    # Skydd: ett namn med en enda bokstav eller siffra, och vanliga påhittade namn med accent, mellanslag,
    # punkt och bindestreck, godtas fortfarande och känns igen i en bankrad.
    namn = ["0", "A", "PAHITTAD-AGARE", "Åsa Öberg", "Ägare 2", "É. Larsson AB"]
    for ett in namn:
        regelbok = las(tmp_path, bok(agare_och_narstaende=[ett]), konfiguration)
        assert regelbok.agare_och_narstaende == [ett]
        assert regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": "UTTAG " + ett, "referens": ""}), ett
    regelbok = las(tmp_path, bok(agare_och_narstaende=namn), konfiguration)
    assert regelbok.agare_och_narstaende == namn


@pytest.mark.parametrize("varde", [None, 5, True, ["AGARE-X"]])
def test_uppslag_av_agare_med_annat_an_text_stoppar(tmp_path, konfiguration, varde):
    regelbok = las(tmp_path, bok(agare_och_narstaende=["AGARE-X"]), konfiguration)
    with pytest.raises(RegelbokFel, match="Uppslaget i regelboken: motpart ska vara text"):
        regelbok.ar_agare_eller_narstaende(varde)


def test_regel_for_agare_med_niva_d_godtas(tmp_path, konfiguration):
    # Båda typerna av underlag. Regler för Z-rapporter och bankrader har ingen motpart.
    data = bok(agare_och_narstaende=["AGARE-X"])
    data["regler"].append(regel("R-6", underlag(motpart="AGARE-X"), {"grupp_a": "9001"}, niva="D"))
    data["regler"].append(regel("R-7", underlag("kvitto", "AGARE-X"), {"grupp_a": "9002"}, niva="D"))
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regel_for_underlag("kvitto", "AGARE-X", "2025-01-01")["niva"] == "D"


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


def test_bokforing_lases_och_kan_inte_andras(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    assert regelbok.bokforing == bokforing()
    regelbok.bokforing["metod"] = "kontantmetoden"
    assert regelbok.bokforing == bokforing()


@pytest.mark.parametrize("nyckel, varde", [("betalning", "transaktionsdag"), ("kvitto", "kvittodatum"),
                                           ("kvitto", "bokforingsdag"), ("bankrad", "transaktionsdag")])
def test_alla_byggda_datum_godtas(tmp_path, konfiguration, nyckel, varde):
    data = bok()
    data["bokforing"]["verifikationsdatum"][nyckel] = varde
    assert las(tmp_path, data, konfiguration).bokforing["verifikationsdatum"][nyckel] == varde


def test_bokforing_som_inte_ar_antagen_och_med_anteckning_godtas(tmp_path, konfiguration):
    data = bok()
    data["bokforing"].update(antaget=False, anteckning="Beslutat av företaget.")
    # Anteckningen är för människor och följer inte med.
    assert las(tmp_path, data, konfiguration).bokforing == {**bokforing(), "antaget": False}


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


def test_listan_med_agare_kan_inte_andras(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(agare_och_narstaende=["AGARE-X"]), konfiguration)
    with pytest.raises(AttributeError):
        regelbok._regelboken["agare_och_narstaende"].append("MOTPART-A")
    regelbok.agare_och_narstaende.append("MOTPART-A")
    regelbok.agare_och_narstaende.clear()
    assert regelbok.agare_och_narstaende == ["AGARE-X"]
    assert regelbok.ar_agare_eller_narstaende("MOTPART-A") is False


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


def test_matchningsformatet_ska_komma_fran_las_matchningsformat(tmp_path, konfiguration):
    # Granskning 7, M4: ett vanligt objekt (dict) har ingen kontrollsumma, så regelboken kan inte visa
    # vilket matchningsformat den kontrollerades mot. Det stoppas, även när innehållet är rätt. Ett
    # trasigt innehåll (testet hette förut test_matchningsformatet_kontrolleras_igen) stoppas också.
    kontoplan, momssatser, matchning = konfiguration
    ratt = matchning.innehall
    trasigt = matchning.innehall
    del trasigt["kraver_inte_underlag"][1]["hogst_belopp_ore"]
    for innehall in (ratt, trasigt, ladda_matchningsformat(TESTBUTIKEN / "matchning.json")):
        with pytest.raises(RegelbokFel, match="matchningsformatet ska komma från las_matchningsformat, inte vara dict"):
            las_regelbok(skriv(tmp_path, bok()), kontoplan, momssatser, innehall)


def test_ett_paihittat_matchningsformat_stoppas(tmp_path, konfiguration):
    # Ett objekt med samma delar som ett Matchningsformat (innehall och kontrollsumma), men som inte
    # kommer från las_matchningsformat, och en underklass. Båda stoppas, så att ingen kan välja summan själv.
    import las_matchningsformat as modulen

    kontoplan, momssatser, matchning = konfiguration

    class Paihittat:
        innehall = matchning.innehall
        kontrollsumma = "0" * 64

    class Underklass(modulen.Matchningsformat):
        __slots__ = ()

    for falskt, namn in ((Paihittat(), "Paihittat"), (object.__new__(Underklass), "Underklass")):
        with pytest.raises(RegelbokFel, match="matchningsformatet ska komma från las_matchningsformat, inte vara " + namn):
            las_regelbok(skriv(tmp_path, bok()), kontoplan, momssatser, falskt)


def test_regelboken_vet_vilka_filer_den_kontrollerades_mot(tmp_path, konfiguration):
    # Granskning 7, M4: kontrollsummorna kommer från de inlästa objekten, och kan inte ändras.
    kontoplan, momssatser, matchning = konfiguration
    regelbok = las(tmp_path, bok(), konfiguration)
    mapp = tmp_path / "konfiguration"
    assert regelbok.kontrollerad_mot == {
        "kontoplan": hashlib.sha256((mapp / "kontoplan.json").read_bytes()).hexdigest(),
        "momssatser": hashlib.sha256((mapp / "momssatser.json").read_bytes()).hexdigest(),
        "matchningsformat": hashlib.sha256((mapp / "matchning.json").read_bytes()).hexdigest()}
    assert regelbok.kontrollerad_mot == {"kontoplan": kontoplan.kontrollsumma, "momssatser": momssatser.kontrollsumma,
                                         "matchningsformat": matchning.kontrollsumma}
    regelbok.kontrollerad_mot["kontoplan"] = "0" * 64
    assert regelbok.kontrollerad_mot["kontoplan"] == kontoplan.kontrollsumma
    with pytest.raises(TypeError):
        regelbok._regelboken["kontrollerad_mot"]["kontoplan"] = "0" * 64


def test_en_annan_kontoplan_ger_en_annan_kontrollsumma_i_regelboken(tmp_path, konfiguration):
    _, momssatser, matchning = konfiguration
    data = copy.deepcopy(KONTOPLAN)
    data["konton"][4]["namn"] = "ett annat namn"
    fil = tmp_path / "annan_kontoplan.json"
    fil.write_text(json.dumps(data), encoding="utf-8")
    fore = las(tmp_path, bok(), konfiguration)
    efter = las_regelbok(skriv(tmp_path, bok()), las_kontoplan(fil), momssatser, matchning)
    assert efter.kontrollsumma == fore.kontrollsumma
    assert efter.kontrollerad_mot["kontoplan"] != fore.kontrollerad_mot["kontoplan"]
    assert efter.kontrollerad_mot["momssatser"] == fore.kontrollerad_mot["momssatser"]


def test_matchningsregel_for_bankrad_i_regelboken(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(), konfiguration)
    assert regelbok.matchningsregel_for_bankrad({"belopp_ore": 100, "referens": "IN-7", "beskrivning": "x"}) == "regel_in"
    assert regelbok.matchningsregel_for_bankrad({"belopp_ore": -100, "referens": "UT-7", "beskrivning": "x"}) == "regel_ut"
    assert regelbok.matchningsregel_for_bankrad({"belopp_ore": -100, "referens": "IN-7", "beskrivning": "x"}) is None


def test_regelboken_ger_matchningsformatet_den_kontrollerades_mot(tmp_path, konfiguration):
    # Granskning 8, N3: matcha_period tar matchningsformatet från regelboken, så att matchningen och
    # regelboken alltid använder samma format. Det är hela det kontrollerade innehållet, som en ny kopia.
    _, _, matchning = konfiguration
    regelbok = las(tmp_path, bok(), konfiguration)
    assert regelbok.matchningsformat == matchning.innehall
    assert sorted(regelbok.matchningsformat) == ["kraver_inte_underlag", "saknat_underlag_efter_dagar",
                                                 "tidsfonster_dagar"]
    kopia = regelbok.matchningsformat
    kopia["kraver_inte_underlag"].clear()
    kopia["tidsfonster_dagar"]["kvitto"] = 0
    kopia["saknat_underlag_efter_dagar"] = 0
    assert regelbok.matchningsformat == matchning.innehall
    assert regelbok.matchningsregel_for_bankrad({"belopp_ore": 100, "referens": "IN-7", "beskrivning": "x"}) == "regel_in"


# --- Stoppregler ---

@pytest.mark.parametrize("ascii", [False, True], ids=["som_tecken", "som_kod_i_json"])
@pytest.mark.parametrize("tecken", DOLDA.values(), ids=DOLDA.keys())
@pytest.mark.parametrize("plats", ["anteckning", "foretag", "id", "motpart", "konto", "varugrupp", "veckodag",
                                   "nyckel", "agare"])
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
    elif plats == "agare":
        data["agare_och_narstaende"] = ["AGARE-X", "AGARE" + tecken + "-Y"]
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
    # 'bokforing' (Hugos beslut 2026-10-29, inför uppgift 4): inget val görs åt företaget.
    "okand_nyckel_i_bokforing": (andrad((("bokforing", "avrundning"), "ingen")), "okänd nyckel: 'avrundning'"),
    "saknar_metod": (andrad((("bokforing", "metod"), BORT)), "saknar nyckeln 'metod'"),
    "saknar_antaget": (andrad((("bokforing", "antaget"), BORT)), "saknar nyckeln 'antaget'"),
    "saknar_verifikationsdatum": (andrad((("bokforing", "verifikationsdatum"), BORT)),
                                  "saknar nyckeln 'verifikationsdatum'"),
    "saknar_datum_for_kvitto": (andrad((("bokforing", "verifikationsdatum", "kvitto"), BORT)),
                                "saknar nyckeln 'kvitto'"),
    "okant_datum_i_bokforing": (andrad((("bokforing", "verifikationsdatum", "kassa"), "datum")),
                                "okänd nyckel: 'kassa'"),
    "kontantmetoden_ar_inte_byggd": (andrad((("bokforing", "metod"), "kontantmetoden")),
                                     "'metod' i 'bokforing' är 'kontantmetoden', men ska vara 'faktureringsmetoden'."
                                     " Andra val är inte byggda"),
    "metod_heltal": (andrad((("bokforing", "metod"), 1)), "'metod' i 'bokforing' är heltal"),
    "antaget_text": (andrad((("bokforing", "antaget"), "ja")), "'antaget' i 'bokforing' ska vara true eller false,"
                     " inte text"),
    "antaget_heltal": (andrad((("bokforing", "antaget"), 1)), "ska vara true eller false, inte heltal"),
    "bokforing_lista": (bok(bokforing=["faktureringsmetoden"]), "'bokforing' ska vara ett objekt"),
    "verifikationsdatum_text": (andrad((("bokforing", "verifikationsdatum"), "fakturadatum")),
                                "'verifikationsdatum' i 'bokforing' ska vara ett objekt"),
    "fakturan_pa_betaldagen": (andrad((("bokforing", "verifikationsdatum", "leverantorsfaktura"), "transaktionsdag")),
                               "'leverantorsfaktura' i 'verifikationsdatum' är 'transaktionsdag', men ska vara"
                               " 'fakturadatum'"),
    "betalningen_pa_fakturadatum": (andrad((("bokforing", "verifikationsdatum", "betalning"), "fakturadatum")),
                                    "ska vara en av 'transaktionsdag', 'bokforingsdag'"),
    "kvitto_med_okant_datum": (andrad((("bokforing", "verifikationsdatum", "kvitto"), "Kvittodatum")),
                               "'kvitto' i 'verifikationsdatum' är 'Kvittodatum'"),
    "bankrad_datum_heltal": (andrad((("bokforing", "verifikationsdatum", "bankrad"), 20250131)), "är heltal"),
    "anteckning_i_bokforing_tom": (andrad((("bokforing", "anteckning"), "")), "'anteckning' i 'bokforing'"),
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
    # Ägare och närstående (K7, Hugos beslut 2026-10-26)
    "agare_text": (bok(agare_och_narstaende="AGARE-X"), "'agare_och_narstaende' ska vara en lista, inte text"),
    "agare_objekt": (bok(agare_och_narstaende={"AGARE-X": True}), "'agare_och_narstaende' ska vara en lista, inte"
                     " ett objekt"),
    "agare_null": (bok(agare_och_narstaende=None), "'agare_och_narstaende' ska vara en lista", "inte null"),
    "agare_heltal": (bok(agare_och_narstaende=["AGARE-X", 1]), "motpart nummer 2 i 'agare_och_narstaende' ska vara"
                     " text, inte heltal"),
    "agare_null_i_listan": (bok(agare_och_narstaende=[None]), "motpart nummer 1 i 'agare_och_narstaende'",
                            "inte null"),
    "agare_lista_i_listan": (bok(agare_och_narstaende=[["AGARE-X"]]), "motpart nummer 1", "inte en lista"),
    "agare_tom": (bok(agare_och_narstaende=[""]), "motpart nummer 1 i 'agare_och_narstaende' får inte vara tom"),
    "agare_blanksteg": (bok(agare_och_narstaende=["AGARE-X", "   "]), "motpart nummer 2 i 'agare_och_narstaende' får"
                        " inte vara tom"),
    "agare_blanksteg_sist": (bok(agare_och_narstaende=["AGARE-X "]), "blanksteg först eller sist"),
    "agare_dubblett": (bok(agare_och_narstaende=["AGARE-X", "NARSTAENDE-Y", "AGARE-X"]),
                       "'AGARE-X' står flera gånger i 'agare_och_narstaende' (som 'AGARE-X')"),
    "agare_dubblett_efter_normalisering": (bok(agare_och_narstaende=["AGARE-X", "agare" + chr(0x2010) + "x"]),
                                           "står flera gånger i 'agare_och_narstaende' (som 'AGARE-X')"),
    "agarregel_niva_b": (med_agare(["AGARE-X"], regel("R-6", underlag(motpart="AGARE-X"), {"grupp_a": "9001"})),
                         "regel nummer 6 (R-6) gäller motparten 'AGARE-X', som står i 'agare_och_narstaende' (som"
                         " 'AGARE-X'), och har nivå 'B'", "ska alltid ha nivå D"),
    "agarregel_niva_a": (med_agare(["AGARE-X"], regel("R-6", underlag("kvitto", "AGARE-X"), {"grupp_a": "9001"},
                                                      niva="A")), "och har nivå 'A'"),
    "agarregel_niva_c": (med_agare(["NARSTAENDE-Y", "AGARE-X"], regel("R-6", underlag(motpart="AGARE-X"),
                                                                      {"grupp_a": "9001"}, niva="C")),
                         "och har nivå 'C'"),
    "agarregel_efter_normalisering": (med_agare(["AGARE-X"], regel("R-6", underlag(motpart="agare - x"),
                                                                   {"grupp_a": "9001"})),
                                      "gäller motparten 'agare - x', som står i 'agare_och_narstaende' (som 'AGARE-X')"),
    "agarregel_bland_andra": (med_agare(["AGARE-X"], regel("R-6", underlag(motpart="AGARE-X"), {"grupp_a": "9001"},
                                                           niva="D", giltig_till="2024-12-31"),
                                        regel("R-7", underlag(motpart="AGARE-X"), {"grupp_a": "9001"},
                                              giltig_fran="2025-01-01")),
                              "regel nummer 7 (R-7) gäller motparten 'AGARE-X'"),
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


# --- Granskning 7, M5: förväxlingstecken i regelbokens namn ---
# En förväxlingsbokstav ser ut som en latinsk bokstav men är en annan, så att namnet jämförs som ett
# annat namn. Granskarens prov med testbutikens ägare AGARE-1 och en regel med nivå A.

KYRILLISKT_A = chr(0x0410)
KYRILLISKT_E = chr(0x0415)
GREKISKT_OMIKRON = chr(0x039F)
CHEROKEE_AGARE = "".join(map(chr, (0x13AA, 0x13C0, 0x13AA, 0x13D2, 0x13AC)))  # ser ut som "AGARE"
ARABISK_ETTA = chr(0x0661)


def regelbok_fran_testbutiken_med(tmp_path, *nya_regler, agare=None):
    """Testbutikens regelbok med nya_regler till sist och, om agare anges, en annan lista med ägare."""
    data = json.loads(REGELBOK_FIL.read_text(encoding="utf-8"))
    data["regler"] += list(nya_regler)
    if agare is not None:
        data["agare_och_narstaende"] = agare
    fil = tmp_path / "regelbok.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return fil


def leverantorsregel(id_, motpart, konto="4010", niva="A"):
    return {"id": id_, "galler": {"kalla": "underlag", "typ": "leverantorsfaktura", "motpart": motpart},
            "kontering": {"livsmedel": konto}, "villkor": {"giltig_fran": "2025-01-01"}, "niva": niva}


@pytest.mark.parametrize("motpart, tecken", [
    (KYRILLISKT_A + "GARE-1", "U+0410 (CYRILLIC CAPITAL LETTER A)"),
    (CHEROKEE_AGARE + "-1", "U+13AA (CHEROKEE LETTER GO)"),
    ("AGARE-" + ARABISK_ETTA, "U+0661 (ARABIC-INDIC DIGIT ONE)"),
], ids=["kyrilliskt_a", "cherokee", "arabisk_etta"])
def test_m5_regel_for_agaren_med_forvaxlingstecken_stoppar_filen(tmp_path, motpart, tecken):
    # Förut godtogs regeln med nivå A, och ar_agare_eller_narstaende sade False: ägaren kändes inte igen.
    fil = regelbok_fran_testbutiken_med(tmp_path, leverantorsregel("R-AGARE-X", motpart))
    with pytest.raises(RegelbokFel) as fel:
        las_testbutikens_regelbok(fil)
    meddelande = str(fel.value)
    assert "'motpart' i 'galler' i regel nummer 11 (R-AGARE-X)" in meddelande and tecken in meddelande, meddelande


def test_m5_p12_tva_regler_som_ser_likadana_ut_stoppar_filen(tmp_path):
    # P12: en andra regel med id R-LEV-TЕ och motparten LEV-TЕ (kyrilliskt Е sist), konto 6071, bredvid
    # den vanliga R-LEV-TE. Förut godtogs den. Nu stoppas både id:t och motparten var för sig.
    for id_, motpart, vad in (("R-LEV-T" + KYRILLISKT_E, "LEV-T" + KYRILLISKT_E, "'id' i regel nummer 11"),
                              ("R-LEV-TE-2", "LEV-T" + KYRILLISKT_E, "'motpart' i 'galler' i regel nummer 11"),
                              ("R-LEV-T" + KYRILLISKT_E, "LEV-TE-2", "'id' i regel nummer 11")):
        fil = regelbok_fran_testbutiken_med(tmp_path, leverantorsregel(id_, motpart, konto="6071"))
        with pytest.raises(RegelbokFel) as fel:
            las_testbutikens_regelbok(fil)
        assert vad in str(fel.value) and "U+0415 (CYRILLIC CAPITAL LETTER IE)" in str(fel.value), str(fel.value)


@pytest.mark.parametrize("agare, tecken", [
    (["AGARE-1", CHEROKEE_AGARE + "-1"], "U+13AA (CHEROKEE LETTER GO)"),
    (["AGARE-1", "N" + KYRILLISKT_A + "RSTAENDE-2"], "U+0410 (CYRILLIC CAPITAL LETTER A)"),
], ids=["cherokee", "kyrilliskt_a"])
def test_m5_forvaxlingstecken_i_listan_med_agare_stoppar_filen(tmp_path, agare, tecken):
    fil = regelbok_fran_testbutiken_med(tmp_path, agare=agare)
    with pytest.raises(RegelbokFel) as fel:
        las_testbutikens_regelbok(fil)
    assert "motpart nummer 2 i 'agare_och_narstaende'" in str(fel.value) and tecken in str(fel.value), str(fel.value)


M5_STOPPAS = {
    # Ett ord som blandar latinska och andra bokstäver, som i underlagen (J1).
    "motpart_blandad": (andrad(((R, 0, "galler", "motpart"), "MOTPART-" + KYRILLISKT_A)), "'motpart' i 'galler' i"
                        " regel nummer 1 (R-1) har ordet 'MOTPART-" + KYRILLISKT_A + "', som blandar latinska"
                        " bokstäver med bokstaven U+0410 (CYRILLIC CAPITAL LETTER A) från ett annat skriftsystem"),
    "motpart_grekisk": (andrad(((R, 0, "galler", "motpart"), GREKISKT_OMIKRON + "K HANDEL")),
                        "U+039F (GREEK CAPITAL LETTER OMICRON)", "blandar latinska bokstäver"),
    # Regelboken är strängare än underlagen: ett helt ord i ett annat skriftsystem stoppas också.
    "motpart_helt_cherokee": (andrad(((R, 0, "galler", "motpart"), CHEROKEE_AGARE)), "'motpart' i 'galler' i regel"
                              " nummer 1 (R-1) har bokstaven U+13AA (CHEROKEE LETTER GO), som inte är en latinsk"
                              " bokstav", "får bara ha latinska bokstäver"),
    "motpart_helt_kyrillisk": (andrad(((R, 0, "galler", "motpart"), "МОСКВА")), "U+041C (CYRILLIC CAPITAL LETTER EM)",
                               "inte är en latinsk bokstav"),
    "motpart_arabisk_siffra": (andrad(((R, 0, "galler", "motpart"), "MOTPART-" + ARABISK_ETTA)),
                               "har siffran U+0661 (ARABIC-INDIC DIGIT ONE)", "siffrorna 0–9"),
    "kassaregister_blandat": (andrad(((R, 2, "galler", "kassaregister"), "K" + KYRILLISKT_A + "SSA-X")),
                              "'kassaregister' i 'galler' i regel nummer 3 (R-3)", "U+0410"),
    "kassaregister_cherokee": (andrad(((R, 2, "galler", "kassaregister"), CHEROKEE_AGARE)),
                               "'kassaregister' i 'galler' i regel nummer 3 (R-3) har bokstaven U+13AA"),
    "agare_cherokee": (bok(agare_och_narstaende=[CHEROKEE_AGARE + "-1"]), "motpart nummer 1 i"
                       " 'agare_och_narstaende' har bokstaven U+13AA (CHEROKEE LETTER GO)"),
    # Regel-id: bara a–z, siffror och bindestreck efter normaliseringen, som fakturanumret i underlagen.
    "id_kyrilliskt": (andrad(((R, 0, "id"), "R-" + KYRILLISKT_A)), "'id' i regel nummer 1 innehåller tecknet U+0410"
                      " (CYRILLIC CAPITAL LETTER A). Ett regel-id får bara innehålla bokstäverna a–z, siffror och"
                      " bindestreck"),
    "id_cherokee": (andrad(((R, 0, "id"), "R-" + CHEROKEE_AGARE)), "U+13AA (CHEROKEE LETTER GO)"),
    "id_a_med_accent": (andrad(((R, 0, "id"), "R-" + chr(0x00C5))), "U+00C5 (LATIN CAPITAL LETTER A WITH RING ABOVE)"),
    "id_understreck": (andrad(((R, 0, "id"), "R_1")), "U+005F (LOW LINE)"),
    "id_arabisk_siffra": (andrad(((R, 0, "id"), "R-" + ARABISK_ETTA)), "U+0661 (ARABIC-INDIC DIGIT ONE)"),
    # Konton och varugrupper var redan skyddade: de ska finnas i kontoplanen (bara 0–9) och momsfilen
    # (bara a–z, siffror och understreck). Testerna låser det.
    "konto_arabiska_siffror": (andrad(((R, 0, "kontering", "grupp_a"), ARABISK_ETTA + "001")),
                               "som inte finns i kontoplanen"),
    "konto_fullbredd": (andrad(((R, 0, "kontering", "grupp_a"), chr(0xFF19) + "001")), "som inte finns i kontoplanen"),
    "varugrupp_kyrillisk": (andrad(((R, 1, "kontering"), {"grupp_" + chr(0x0430): "9002"})),
                            "ingen varugrupp 'grupp_" + chr(0x0430) + "'"),
}


@pytest.mark.parametrize("data, texter", [(fall[0], fall[1:]) for fall in M5_STOPPAS.values()], ids=M5_STOPPAS.keys())
def test_m5_stoppregel(tmp_path, konfiguration, data, texter):
    stoppas(tmp_path, data, konfiguration, *texter)


def test_m5_latinska_namn_godtas(tmp_path, konfiguration):
    # Skydd: svenska och andra latinska bokstäver, fullbreddsbokstäver (som är latinska efter NFKC),
    # vanliga tecken och olika sorters bindestreck i ett id godtas, och namnen sparas som de står.
    # Ändrat efter granskning 8 (N2): "&", "Ø" och "ß" stoppas nu (test_n2_stoppregel).
    data = bok(agare_och_narstaende=["Ägare Åström", "Ölhus Strasse"])
    data["regler"][0]["galler"]["motpart"] = "Café Ölund och Söner AB"
    data["regler"][2]["galler"]["kassaregister"] = "Ｋａｓｓａ-7"
    data["regler"][0]["id"] = "r" + chr(0x2010) + "LEV-1"
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regler[0]["galler"]["motpart"] == "Café Ölund och Söner AB"
    assert regelbok.regler[0]["id"] == "r" + chr(0x2010) + "LEV-1"
    assert regelbok.ar_agare_eller_narstaende("ÄGARE ÅSTRÖM") is True


def test_m5_testbutikens_regelbok_godtas_fortfarande():
    # Skydd: testbutikens regelbok har bara latinska namn och vanliga id.
    assert len(las_testbutikens_regelbok().regler) == 10


# --- Granskning 7, M6: en egen variant av kontoplanen eller momsfilen ---

def test_m6_egen_variant_av_kontoplanen_stoppas(tmp_path, konfiguration):
    # Mut7: med isinstance() i stället för type() släpptes en egen variant av Kontoplan igenom. Den här
    # är skapad med object.__new__ och svarar som den riktiga kontoplanen, men med ett konto till, så att
    # regelboken godtar ett konto som inte finns i filen.
    from las_kontoplan import Kontoplan

    kontoplan, momssatser, matchning = konfiguration
    riktig = kontoplan

    class EgenKontoplan(Kontoplan):
        __slots__ = ()

        @property
        def konton(self):
            return riktig.konton + [{"nummer": "9999", "namn": "påhittat", "fran": None, "till": None}]

        @property
        def kontrollsumma(self):
            return riktig.kontrollsumma

    data = andrad(((R, 0, "kontering", "grupp_a"), "9999"))
    stoppas(tmp_path, data, konfiguration, "'9999', som inte finns i kontoplanen")
    with pytest.raises(RegelbokFel, match="kontoplanen ska komma från las_kontoplan, inte vara EgenKontoplan"):
        las_regelbok(skriv(tmp_path, data), object.__new__(EgenKontoplan), momssatser, matchning)


def test_m6_egen_variant_av_momsfilen_stoppas(tmp_path, konfiguration):
    # Samma sak för momsfilen: en variant med en varugrupp till.
    from las_momssatser import Momssatser

    kontoplan, momssatser, matchning = konfiguration
    riktig = momssatser

    class EgnaMomssatser(Momssatser):
        __slots__ = ()

        @property
        def kontrollsumma(self):
            return riktig.kontrollsumma

        def period(self, varugrupp, datum):
            if varugrupp == "grupp_x":
                return {"fran": "2024-01-01", "till": None, "sats": 7, "kalla": "påhittad"}
            return riktig.period(varugrupp, datum)

    data = andrad(((R, 0, "kontering", "grupp_x"), "9001"))
    stoppas(tmp_path, data, konfiguration, "ingen varugrupp 'grupp_x'")
    with pytest.raises(RegelbokFel, match="momssatserna ska komma från las_momssatser, inte vara EgnaMomssatser"):
        las_regelbok(skriv(tmp_path, data), kontoplan, object.__new__(EgnaMomssatser), matchning)


# --- Granskning 7, M12: kontoplan, momsfil eller matchningsformat skapade med __new__ ---

@pytest.mark.parametrize("plats, text", [
    (0, "kontoplanen är tom eller trasig. Den har inte skapats av las_kontoplan."),
    (1, "momsfilen är tom eller trasig. Den har inte skapats av las_momssatser."),
    (2, "matchningsformatet är tomt eller trasigt. Det har inte skapats av las_matchningsformat."),
], ids=["kontoplan", "momsfil", "matchningsformat"])
def test_m12_tom_konfiguration_ger_ett_tydligt_fel(tmp_path, konfiguration, plats, text):
    # Förut gav ett objekt utan innehåll (skapat med __new__) ett AttributeError, som inte förklarar något.
    argument = list(konfiguration)
    argument[plats] = object.__new__(type(argument[plats]))
    with pytest.raises(RegelbokFel, match=re.escape("Regelboken kan inte kontrolleras: " + text)):
        las_regelbok(skriv(tmp_path, bok()), *argument)


# --- Granskning 7, M10: en regel som gäller en enda dag ---

def test_m10_regel_som_galler_en_enda_dag_godtas(tmp_path, konfiguration):
    # Mut3: en regel där giltig_fran och giltig_till är samma dag gäller just den dagen.
    data = andrad(((R, 0, "villkor", "giltig_fran"), "2025-03-01"), ((R, 0, "villkor", "giltig_till"), "2025-03-01"))
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", "2025-03-01")["id"] == "R-1"
    for datum in ("2025-02-28", "2025-03-02"):
        assert regelbok.regel_for_underlag("leverantorsfaktura", "MOTPART-A", datum) is None


# --- Granskning 7, M7: bankrader mot en ägare eller närstående ---

def test_m7_uppslaget_pekar_ut_agarens_bankrader(tmp_path):
    # En påhittad bankfil med testbutikens format, läst med las_bankfil, och testbutikens regelbok
    # (agare_och_narstaende är ["AGARE-1"]). Raderna 1, 3 och 5 är mot ägaren: i beskrivningen, i
    # referensen och med ett annat bindestreck och små bokstäver. Rad 4 är en annan motpart (AGARE-12),
    # och rad 2 en vanlig Swish-rad. Rad 1 passar ingen regel i matchningsformatet, men uppslaget gäller
    # alla bankrader.
    from las_bank import ladda_bankformat, las_bankfil

    rader = [
        "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo",
        "1,2025-04-01,2025-04-01,UTTAG-1,UTTAG AGARE-1,-500.00,9500.00",
        "2,2025-04-01,2025-04-01,SWISH-20250401-1,BET-SWISH INBETALNING,100.00,9600.00",
        "3,2025-04-02,2025-04-02,AGARE-1,OVERFORING,-100.00,9500.00",
        "4,2025-04-02,2025-04-02,KOP-1,KOP AGARE-12 AB,-50.00,9450.00",
        "5,2025-04-03,2025-04-03,UTL-1,UTLAGG agare" + chr(0x2013) + "1,-20.00,9430.00",
    ]
    fil = tmp_path / "bank.csv"
    fil.write_text("\n".join(rader) + "\n", encoding="utf-8")
    period = las_bankfil(fil, ladda_bankformat(TESTBUTIKEN / "bankformat.json"), 1000000, 943000)
    regelbok = las_testbutikens_regelbok()
    assert [rad["radnr"] for rad in period.rader if regelbok.ar_bankrad_mot_agare_eller_narstaende(rad)] == [1, 3, 5]


def test_m7_inga_av_testdatans_bankrader_i_q1_ar_mot_agaren():
    # Skydd: ägaren förekommer först från Q2 i testdatan (testforetag/FIKTIVT_FORETAG.md), så inget i Q1
    # pekas ut. Utan ägare i regelboken pekas ingen bankrad ut alls.
    from las_bank import ladda_bankformat, las_bankfil

    datamapp = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"
    bank = json.loads((datamapp / "facit.json").read_text(encoding="utf-8"))["bank"]
    regelbok = las_testbutikens_regelbok()
    antal = 0
    for manad in ("2025-01", "2025-02"):
        period = las_bankfil(datamapp / ("bank_" + manad + ".csv"), ladda_bankformat(TESTBUTIKEN / "bankformat.json"),
                             bank[manad]["ingaende_saldo_ore"], bank[manad]["utgaende_saldo_ore"])
        antal += len(period.rader)
        assert not any(regelbok.ar_bankrad_mot_agare_eller_narstaende(rad) for rad in period.rader)
    assert antal > 100


def test_m7_uppslaget_for_bankrader(tmp_path, konfiguration):
    regelbok = las(tmp_path, bok(agare_och_narstaende=["AGARE-X", "Anna Nilsson"]), konfiguration)
    ja = [("UTTAG AGARE-X", ""), ("", "AGARE-X"), ("BET agare - x", "R-1"), ("LON ANNA NILSSON", ""),
          ("KOP ANNANILSSON", ""), ("UTTAG AGARE-X" + chr(0x200B), "")]
    nej = [("UTTAG AGARE-XY", ""), ("UTTAGAGARE-X", ""), ("ANNA", "NILSSONS"), ("", "")]
    for beskrivning, referens in ja:
        assert regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": beskrivning, "referens": referens}), (
            beskrivning, referens)
    for beskrivning, referens in nej:
        assert not regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": beskrivning, "referens": referens}), (
            beskrivning, referens)
    utan = las(tmp_path, bok(), konfiguration)
    assert utan.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": "UTTAG AGARE-X", "referens": ""}) is False


@pytest.mark.parametrize("rad, text", [
    (None, "bankraden ska vara ett objekt med nycklar, inte null"),
    (["UTTAG AGARE-X"], "bankraden ska vara ett objekt med nycklar, inte en lista"),
    ({"beskrivning": "UTTAG AGARE-X"}, "bankradens 'referens' ska vara text, inte null"),
    ({"beskrivning": 5, "referens": ""}, "bankradens 'beskrivning' ska vara text, inte heltal"),
])
def test_m7_uppslag_med_fel_bankrad_stoppar(tmp_path, konfiguration, rad, text):
    regelbok = las(tmp_path, bok(agare_och_narstaende=["AGARE-X"]), konfiguration)
    with pytest.raises(RegelbokFel, match=re.escape("Uppslaget i regelboken: " + text)):
        regelbok.ar_bankrad_mot_agare_eller_narstaende(rad)


# --- Granskning 8, N1: osynliga tecken enligt Unicodes egen lista ---
# Granskarens prov Q08–Q12: testbutikens regelbok (med AGARE-1 i agare_och_narstaende) och en ny regel
# R-AGARE-X för leverantörsfakturor med nivå A. Förut godtogs regeln, och ägaren kändes inte igen.

N1_PROV = {
    "q08_17b4": ("AGARE-1" + chr(0x17B4), chr(0x17B4)),
    "q09_17b5": ("AGA" + chr(0x17B5) + "RE-1", chr(0x17B5)),
    "q10_2065": ("AGARE-1" + chr(0x2065), chr(0x2065)),
    "q11_fff0": ("AGARE-1" + chr(0xFFF0), chr(0xFFF0)),
    "q12_e0080": ("AGARE-1" + chr(0xE0080), chr(0xE0080)),
}


@pytest.mark.parametrize("motpart, tecken", N1_PROV.values(), ids=N1_PROV.keys())
def test_n1_regel_for_agaren_med_osynligt_tecken_stoppar_filen(tmp_path, motpart, tecken):
    # Samma tecken i listan med ägare, och granskarens andra regel R-LEV-TE-2 för LEV-TE med tecknet,
    # bredvid den vanliga R-LEV-TE, stoppas också.
    for nya_regler, agare in (([leverantorsregel("R-AGARE-X", motpart)], None), ([], ["AGARE-1", motpart]),
                              ([leverantorsregel("R-LEV-TE-2", "LEV-TE" + tecken, konto="6071")], None)):
        with pytest.raises(RegelbokFel) as fel:
            las_testbutikens_regelbok(regelbok_fran_testbutiken_med(tmp_path, *nya_regler, agare=agare))
        meddelande = str(fel.value)
        assert "tecknet U+" + format(ord(tecken), "04X") + ", som inte syns" in meddelande, meddelande


@pytest.mark.parametrize("ascii", [False, True], ids=["som_tecken", "som_kod_i_json"])
@pytest.mark.parametrize("tecken", N1_OSYNLIGA.values(), ids=N1_OSYNLIGA.keys())
def test_n1_osynligt_tecken_enligt_unicode_stoppar_regelboken(tmp_path, konfiguration, tecken, ascii):
    for data in (andrad(((R, 0, "galler", "motpart"), "MOTPART-A" + tecken)),
                 andrad(((R, 2, "galler", "kassaregister"), "KASSA" + tecken + "-X")),
                 bok(agare_och_narstaende=["AGARE-X" + tecken]), bok(anteckning="på" + tecken + "hittad")):
        stoppas(tmp_path, data, konfiguration, "U+" + format(ord(tecken), "04X"), "inte syns", ascii=ascii)


# --- Granskning 8, N2: ett namn får bara ha de tecken som SPEC tillåter ---
# Granskarens prov: samma regel R-AGARE-X med nivå A, med ett tecken som syns och ser ut som ett
# bindestreck, en etta eller ett A. Förut godtogs alla, och ägaren kändes inte igen.

N2_PROV = {
    "q05_02d7": ("AGARE" + chr(0x02D7) + "1", "U+02D7 (MODIFIER LETTER MINUS SIGN)"),
    "q06_2043": ("AGARE" + chr(0x2043) + "1", "U+2043 (HYPHEN BULLET)"),
    "q07_2500": ("AGARE" + chr(0x2500) + "1", "U+2500 (BOX DRAWINGS LIGHT HORIZONTAL)"),
    "q13_01c0": ("AGARE-" + chr(0x01C0), "U+01C0 (LATIN LETTER DENTAL CLICK)"),
    "q14_05c0": ("AGARE-" + chr(0x05C0), "U+05C0 (HEBREW PUNCTUATION PASEQ)"),
    "q15_0323": ("AGARE-1" + chr(0x0323), "U+0323 (COMBINING DOT BELOW)"),
    "q18_1d00": (chr(0x1D00) + "GARE-1", "U+1D00 (LATIN LETTER SMALL CAPITAL A)"),
    "q19_0131": ("AGARE-" + chr(0x0131), "U+0131 (LATIN SMALL LETTER DOTLESS I)"),
    "q20_0336": ("AGARE-1" + chr(0x0336), "U+0336 (COMBINING LONG STROKE OVERLAY)"),
}


@pytest.mark.parametrize("motpart, tecken", N2_PROV.values(), ids=N2_PROV.keys())
def test_n2_regel_for_agaren_med_tecken_som_inte_ar_tillatet_stoppar_filen(tmp_path, motpart, tecken):
    for nya_regler, agare, vad in (([leverantorsregel("R-AGARE-X", motpart)], None,
                                    "'motpart' i 'galler' i regel nummer 11 (R-AGARE-X)"),
                                   ([], ["AGARE-1", motpart], "motpart nummer 2 i 'agare_och_narstaende'")):
        with pytest.raises(RegelbokFel) as fel:
            las_testbutikens_regelbok(regelbok_fran_testbutiken_med(tmp_path, *nya_regler, agare=agare))
        meddelande = str(fel.value)
        assert vad + " har tecknet " + tecken in meddelande and "får bara ha" in meddelande, meddelande


N2_STOPPAS = {
    # Skiljetecken som SPEC inte tillåter i ett namn. Vilka som ska godtas väntar på Hugos beslut (N2).
    "et_tecken": (andrad(((R, 0, "galler", "motpart"), "Café Ölund & Söner AB")), "regel nummer 1 (R-1) har"
                  " tecknet U+0026 (AMPERSAND)"),
    "snedstreck": (andrad(((R, 0, "galler", "motpart"), "LEV/A")), "U+002F (SOLIDUS)"),
    "komma": (andrad(((R, 0, "galler", "motpart"), "LEV A, AB")), "U+002C (COMMA)"),
    "apostrof": (andrad(((R, 0, "galler", "motpart"), "O'LEV")), "U+0027 (APOSTROPHE)"),
    "parentes": (andrad(((R, 0, "galler", "motpart"), "LEV (A)")), "U+0028 (LEFT PARENTHESIS)"),
    "mittpunkt": (andrad(((R, 0, "galler", "motpart"), "LEV" + chr(0x00B7) + "A")), "U+00B7 (MIDDLE DOT)"),
    # Latinska bokstäver som inte är a–z med eller utan accent.
    "o_med_snedstreck": (andrad(((R, 0, "galler", "motpart"), "Ølhus")),
                         "U+00D8 (LATIN CAPITAL LETTER O WITH STROKE)"),
    "skarpt_s": (andrad(((R, 0, "galler", "motpart"), "Straße")), "U+00DF (LATIN SMALL LETTER SHARP S)"),
    "ae": (andrad(((R, 0, "galler", "motpart"), "Æble")), "U+00C6 (LATIN CAPITAL LETTER AE)"),
    "kassaregister": (andrad(((R, 2, "galler", "kassaregister"), "KASSA" + chr(0x2043) + "X")),
                      "'kassaregister' i 'galler' i regel nummer 3 (R-3) har tecknet U+2043 (HYPHEN BULLET)"),
    "agare": (bok(agare_och_narstaende=["AGARE" + chr(0x2500) + "X"]), "motpart nummer 1 i 'agare_och_narstaende'"
              " har tecknet U+2500"),
}


@pytest.mark.parametrize("data, texter", [(fall[0], fall[1:]) for fall in N2_STOPPAS.values()], ids=N2_STOPPAS.keys())
def test_n2_stoppregel(tmp_path, konfiguration, data, texter):
    stoppas(tmp_path, data, konfiguration, *texter, "får bara ha")


def test_n2_namnkontrollen_godtar_inte_heller_dolda_tecken():
    # Två lager: ett dolt tecken stoppar redan hela filen (_inga_dolda_tecken_i_json), men namnkontrollen
    # godtar det inte heller. Bara ett vanligt mellanslag godtas av de tecken som normaliseringen tar bort.
    from las_regelbok import _tillatet_i_namn

    assert _tillatet_i_namn(" ") and _tillatet_i_namn("-") and _tillatet_i_namn(chr(0x2010))
    for tecken in (chr(0x200B), chr(0x00A0), chr(0x17B4), chr(0xE0080)):
        assert not _tillatet_i_namn(tecken), hex(ord(tecken))


def test_n2_tillatna_tecken_godtas(tmp_path, konfiguration):
    # Skydd: latinska bokstäver med och utan accent, fullbreddsbokstäver, siffrorna 0–9, mellanslag,
    # bindestreck (alla sorter, eftersom de blir "-" efter normaliseringen), understreck och punkt godtas.
    data = bok(agare_och_narstaende=["Ägare Åström", "agare" + chr(0x2013) + "Y"])
    data["regler"][0]["galler"]["motpart"] = "Café Ñandú Ü-ç_9.AB"
    data["regler"][2]["galler"]["kassaregister"] = "Ｋａｓｓａ" + chr(0x2010) + "7"
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regler[0]["galler"]["motpart"] == "Café Ñandú Ü-ç_9.AB"
    assert regelbok.ar_agare_eller_narstaende("AGARE-Y") is True


# --- Granskning 8, N3: ägarens namn med ett skiljetecken intill ---

def test_n3_uppslaget_hittar_agaren_med_skiljetecken_intill():
    # Granskarens prov med testbutikens regelbok (AGARE-1). Förut pekades raderna med ett skiljetecken
    # intill namnet inte ut, och inte heller ett mellanslag i stället för bindestrecket.
    regelbok = las_testbutikens_regelbok()
    ja = [("UTTAG AGARE-1", ""), ("UTTAG AGARE-1,LAN", ""), ("UTTAG AGARE-1, LAN", ""), ("UTTAG AGARE-1.", ""),
          ("UTTAG (AGARE-1)", ""), ("TILL:AGARE-1", ""), ("UTTAG AGARE-1/MARS", ""), ("X", "AGARE-1;LON"),
          ("UTTAG AGARE 1", ""), ("UTTAG AGARE" + chr(0x02D7) + "1", ""), ("UTTAG AGARE-1" + chr(0x17B4), ""),
          ("LON A GARE-1", "")]
    nej = [("UTTAG AGARE-1X", ""), ("UTTAG AGARE-10", ""), ("KOP AGARE-12 AB", ""), ("UTTAG GARE-1", ""),
           ("UTTAGAGARE-1", ""), ("", "")]
    for beskrivning, referens in ja:
        assert regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": beskrivning, "referens": referens}), (
            beskrivning, referens)
    for beskrivning, referens in nej:
        assert not regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": beskrivning, "referens": referens}), (
            beskrivning, referens)


def matchningsformat_fran_testbutiken_med(tmp_path, *nya_regler):
    """Testbutikens matchningsformat med nya_regler till sist i kraver_inte_underlag, läst med las_matchningsformat."""
    data = json.loads((TESTBUTIKEN / "matchning.json").read_text(encoding="utf-8"))
    data["kraver_inte_underlag"] += list(nya_regler)
    fil = tmp_path / "matchning.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return las_matchningsformat(fil)


def regelbok_fran_testbutiken_mot(matchningsformat):
    """Testbutikens regelbok, kontoplan och momsfil, och matchningsformatet."""
    return las_regelbok(REGELBOK_FIL, las_kontoplan(TESTBUTIKEN / "kontoplan.json"),
                        las_momssatser(TESTBUTIKEN / "momssatser.json"), matchningsformat)


def test_n3_en_regel_i_matchningsformatet_undantar_aldrig_agarens_bankrader(tmp_path):
    # Granskarens prov: regeln agaruttag (pengar ut, beskrivningen börjar med "UTTAG AGARE") och en
    # bankfil läst med las_bankfil. Rad 1–3 är ägarens uttag. Förut passade alla fem raderna regeln, så
    # att rad 2 och 3 slapp underlag utan att pekas ut. Nu pekas rad 1–3 ut, och regeln gäller dem inte.
    # Rad 4 och 5 kan vara andra motparter.
    from las_bank import ladda_bankformat, las_bankfil

    rader = [
        "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo",
        "1,2025-04-01,2025-04-01,UTTAG-1,UTTAG AGARE-1,-500.00,9500.00",
        "2,2025-04-01,2025-04-01,UTTAG-2,UTTAG AGARE-1/LAN,-100.00,9400.00",
        "3,2025-04-02,2025-04-02,UTTAG-3,UTTAG AGARE-1.,-100.00,9300.00",
        "4,2025-04-02,2025-04-02,UTTAG-4,UTTAG AGARE-1X,-100.00,9200.00",
        "5,2025-04-03,2025-04-03,UTTAG-5,UTTAG AGARE-10,-100.00,9100.00",
    ]
    fil = tmp_path / "bank.csv"
    fil.write_text("\n".join(rader) + "\n", encoding="utf-8")
    period = las_bankfil(fil, ladda_bankformat(TESTBUTIKEN / "bankformat.json"), 1000000, 910000)
    regelbok = regelbok_fran_testbutiken_mot(matchningsformat_fran_testbutiken_med(tmp_path, {
        "namn": "agaruttag", "riktning": "ut", "beskrivning_borjar_med": "UTTAG AGARE", "hogst_belopp_ore": 100000}))
    assert [rad["radnr"] for rad in period.rader if regelbok.ar_bankrad_mot_agare_eller_narstaende(rad)] == [1, 2, 3]
    assert [regelbok.matchningsregel_for_bankrad(rad) for rad in period.rader] == [
        None, None, None, "agaruttag", "agaruttag"]


@pytest.mark.parametrize("regel, text", [
    ({"namn": "agaruttag", "riktning": "ut", "beskrivning_borjar_med": "UTTAG AGARE-1", "hogst_belopp_ore": 100000},
     "är 'beskrivning_borjar_med' 'UTTAG AGARE-1'"),
    ({"namn": "agaruttag", "riktning": "ut", "referens_borjar_med": "agare" + chr(0x2013) + "1/",
      "hogst_belopp_ore": 100000}, "är 'referens_borjar_med' 'agare" + chr(0x2013) + "1/'"),
    ({"namn": "agarinsattning", "riktning": "in", "beskrivning_borjar_med": "INSATTNING FRAN (AGARE-1)"},
     "är 'beskrivning_borjar_med' 'INSATTNING FRAN (AGARE-1)'"),
], ids=["beskrivning", "referens_med_tankstreck", "pengar_in"])
def test_n3_regel_i_matchningsformatet_som_namner_en_agare_stoppar_regelboken(tmp_path, regel, text):
    # En sådan regel skulle undanta ägarens bankrader från underlag. Förut godtogs den.
    with pytest.raises(RegelbokFel) as fel:
        regelbok_fran_testbutiken_mot(matchningsformat_fran_testbutiken_med(tmp_path, regel))
    meddelande = str(fel.value)
    assert meddelande.startswith("Regelboken i " + str(REGELBOK_FIL)), meddelande
    for del_ in ("i regeln " + repr(regel["namn"]) + " i matchningsformatet", text, "'AGARE-1' i 'agare_och_narstaende'",
                 "aldrig undanta"):
        assert del_ in meddelande, meddelande


# --- Granskning 8, N7: regelbokens uppslag på ett objekt skapat med __new__ ---

@pytest.mark.parametrize("uppslag", [
    lambda bok_: bok_.regel_for_underlag("kvitto", "MOTPART-A", "2025-01-01"),
    lambda bok_: bok_.regel_for_z_rapport("KASSA-X", "2025-01-01"),
    lambda bok_: bok_.regel_for_bankrad("regel_in", "2025-01-01"),
    lambda bok_: bok_.ar_agare_eller_narstaende("AGARE-X"),
    lambda bok_: bok_.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": "UTTAG AGARE-X", "referens": ""}),
    lambda bok_: bok_.matchningsregel_for_bankrad({"belopp_ore": 100, "referens": "IN-7", "beskrivning": "x"}),
    lambda bok_: bok_.matchningsformat,
], ids=["regel_for_underlag", "regel_for_z_rapport", "regel_for_bankrad", "ar_agare_eller_narstaende",
        "ar_bankrad_mot_agare_eller_narstaende", "matchningsregel_for_bankrad", "matchningsformat"])
def test_n7_uppslag_i_en_tom_regelbok_ger_ett_tydligt_fel(uppslag):
    # Förut gav uppslaget AttributeError: _regelboken, som inte förklarar något.
    with pytest.raises(RegelbokFel, match=re.escape("Uppslaget i regelboken: regelboken är tom eller trasig. Den har"
                                                    " inte skapats av las_regelbok.")):
        uppslag(object.__new__(Regelbok))
