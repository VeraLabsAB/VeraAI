"""Tester för matchningsformatet (las_matchningsformat.py, foretag/<namn>/matchning.json).

Formatet för testföretaget är SYNTETISKT. De små formaten nedan är påhittade och skrivs i en
tillfällig mapp för varje test.
"""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
MATCHNING_FIL = AGENT / "foretag" / "syntet-testbutik" / "matchning.json"

sys.path.insert(0, str(AGENT / "scripts"))

from las_matchningsformat import (  # noqa: E402
    HOGST_DAGAR, Matchningsformat, MatchningsformatFel, kontrollera_matchningsformat, ladda_matchningsformat,
    las_matchningsformat, matchningsregel_for_bankrad,
)

# Osynliga tecken byggs med chr(), så att de syns i koden (test_inga_dolda_tecken.py).
OSYNLIGT_MELLANSLAG = chr(0x200B)


def format_(**andrat):
    """Ett felfritt format, med de ändringar som anges."""
    data = {
        "anteckning": "påhittat",
        "kraver_inte_underlag": [
            {"namn": "insattning", "riktning": "in", "referens_borjar_med": "IN-", "anteckning": "x"},
            {"namn": "avgift", "riktning": "ut", "beskrivning_borjar_med": "AVGIFT", "hogst_belopp_ore": 5000},
        ],
        "tidsfonster_dagar": {"leverantorsfaktura": 30, "kvitto": 2},
        "saknat_underlag_efter_dagar": 7,
    }
    data.update(andrat)
    return data


def regler(*poster):
    return format_(kraver_inte_underlag=list(poster))


def skriv(mapp, data):
    fil = mapp / "matchning.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return fil


def stoppas(mapp, data, *texter):
    """Kräver MatchningsformatFel både från filen och när formatet kontrolleras direkt."""
    fil = skriv(mapp, data)
    with pytest.raises(MatchningsformatFel) as fel:
        ladda_matchningsformat(fil)
    meddelande = str(fel.value)
    assert meddelande.startswith("Matchningsformatet i " + str(fil)), meddelande
    for text in texter:
        assert text in meddelande, meddelande
    with pytest.raises(MatchningsformatFel) as direkt:
        kontrollera_matchningsformat(copy.deepcopy(data))
    assert str(direkt.value) == meddelande.replace("Matchningsformatet i " + str(fil), "Matchningsformatet")
    return meddelande


def test_testforetagets_format_laddas():
    format_ = ladda_matchningsformat(MATCHNING_FIL)
    assert format_ == {
        "kraver_inte_underlag": [
            {"namn": "kortinlosen", "riktning": "in", "referens_borjar_med": "AVR-",
             "beskrivning_borjar_med": "BET-KORT AVRAKNING"},
            {"namn": "swish", "riktning": "in", "referens_borjar_med": "SWISH-",
             "beskrivning_borjar_med": "BET-SWISH INBETALNING"},
            {"namn": "kontantinsattning", "riktning": "in", "referens_borjar_med": "INS-",
             "beskrivning_borjar_med": "KONTANTINSATTNING"},
            {"namn": "bankavgift", "riktning": "ut", "referens_borjar_med": "AVG-",
             "beskrivning_borjar_med": "BANK AVGIFT", "hogst_belopp_ore": 25000},
        ],
        "tidsfonster_dagar": {"leverantorsfaktura": 40, "kvitto": 3},
        "saknat_underlag_efter_dagar": 7,
    }
    # Facit säger att en bankrad utan underlag blir ett ärende efter 7 dagar.
    facit = json.loads((AGENT / "testdata" / "syntet-testbutik" / "2025-Q1" / "facit.json").read_text(encoding="utf-8"))
    assert "efter 7 dagar" in [f for f in facit["planterade_fel"] if f["typ"] == "bankrad_utan_underlag"][0][
        "beskrivning"]


def test_varfor_bankens_avgifter_inte_kraver_underlag_star_i_formatet():
    data = json.loads(MATCHNING_FIL.read_text(encoding="utf-8"))
    avgift = [regel for regel in data["kraver_inte_underlag"] if regel["namn"] == "bankavgift"][0]
    assert "inget underlag" in avgift["anteckning"] and "testdata/README.md" in avgift["anteckning"]
    assert "ska den här regeln tas bort" in avgift["anteckning"]


def test_varfor_bankens_avgifter_har_gransen_250_kr_star_i_formatet():
    # Hugos beslut 2026-10-25: gränsen för bankavgift är 250 kr, och anteckningen säger varför.
    data = json.loads(MATCHNING_FIL.read_text(encoding="utf-8"))
    avgift = [regel for regel in data["kraver_inte_underlag"] if regel["namn"] == "bankavgift"][0]
    assert avgift["hogst_belopp_ore"] == 25000
    for text in ("250 kr", "Hugo", "aldrig undantar en stor betalning", "125 och 199 kr", "'över gräns'"):
        assert text in avgift["anteckning"], text
    assert "oavsett belopp" not in avgift["anteckning"]  # den gamla varningen gäller inte längre


# --- Matchningsformatet med kontrollsumma (granskning 7, M4) ---

def test_kontrollsumman_ar_sha256_av_filen_och_innehallet_ar_det_kontrollerade(tmp_path):
    fil = skriv(tmp_path, format_())
    resultat = las_matchningsformat(fil)
    assert type(resultat) is Matchningsformat
    assert resultat.kontrollsumma == hashlib.sha256(fil.read_bytes()).hexdigest()
    assert resultat.innehall == kontrollera_matchningsformat(format_()) == ladda_matchningsformat(fil)
    assert las_matchningsformat(MATCHNING_FIL).kontrollsumma == hashlib.sha256(MATCHNING_FIL.read_bytes()).hexdigest()


@pytest.mark.parametrize("andring", [b" ", b"\n"])
def test_minsta_andring_ger_en_annan_kontrollsumma(tmp_path, andring):
    # Samma innehåll, men ett blanksteg eller en radbrytning till i filen: summan räknas på filens bytes.
    fil = skriv(tmp_path, format_())
    fore = las_matchningsformat(fil)
    fil.write_bytes(fil.read_bytes() + andring)
    efter = las_matchningsformat(fil)
    assert efter.innehall == fore.innehall and efter.kontrollsumma != fore.kontrollsumma


def test_matchningsformatet_kan_inte_andras(tmp_path):
    resultat = las_matchningsformat(skriv(tmp_path, format_()))
    for namn in ("_kontrollsumma", "_matchningsformatet", "kontrollsumma", "x"):
        with pytest.raises(AttributeError, match="Ett Matchningsformat kan inte ändras"):
            setattr(resultat, namn, None)
        with pytest.raises(AttributeError, match="Ett Matchningsformat kan inte ändras"):
            delattr(resultat, namn)
    with pytest.raises(TypeError):
        resultat._matchningsformatet["saknat_underlag_efter_dagar"] = 99
    kopia = resultat.innehall
    kopia["kraver_inte_underlag"].clear()
    assert len(resultat.innehall["kraver_inte_underlag"]) == 2
    assert repr(resultat) == "Matchningsformat(2 regler, kontrollsumma " + resultat.kontrollsumma[:12] + "…)"


def test_matchningsformatet_kan_bara_skapas_av_las_matchningsformat():
    with pytest.raises(MatchningsformatFel, match="kan bara skapas av las_matchningsformat"):
        Matchningsformat(object(), "0" * 64, format_())


def test_matchningsregel_for_bankrad():
    regler_ = kontrollera_matchningsformat(format_())["kraver_inte_underlag"]

    def rad(belopp, referens="", beskrivning=""):
        return {"belopp_ore": belopp, "referens": referens, "beskrivning": beskrivning}

    assert matchningsregel_for_bankrad(rad(100, "IN-1"), regler_)["namn"] == "insattning"
    assert matchningsregel_for_bankrad(rad(-100, "x", "AVGIFT JAN"), regler_)["namn"] == "avgift"
    assert matchningsregel_for_bankrad(rad(-100, "IN-1"), regler_) is None  # fel riktning
    assert matchningsregel_for_bankrad(rad(100, "in-1"), regler_) is None  # texten jämförs exakt
    assert matchningsregel_for_bankrad(rad(0, "IN-1"), regler_) is None


def test_kontrollen_ger_en_ny_kopia_utan_anteckningar():
    data = format_()
    fore = copy.deepcopy(data)
    resultat = kontrollera_matchningsformat(data)
    assert data == fore
    assert "anteckning" not in resultat and all("anteckning" not in regel for regel in resultat["kraver_inte_underlag"])
    resultat["kraver_inte_underlag"].append({})
    resultat["tidsfonster_dagar"]["kvitto"] = 99
    assert data == fore


def test_utan_anteckning_och_utan_regler_godtas(tmp_path):
    data = format_(kraver_inte_underlag=[])
    del data["anteckning"]
    assert ladda_matchningsformat(skriv(tmp_path, data))["kraver_inte_underlag"] == []


@pytest.mark.parametrize("andring, text", [
    (lambda d: d.pop("tidsfonster_dagar"), "saknar nyckeln 'tidsfonster_dagar'"),
    (lambda d: d.pop("saknat_underlag_efter_dagar"), "saknar nyckeln 'saknat_underlag_efter_dagar'"),
    (lambda d: d.pop("kraver_inte_underlag"), "saknar nyckeln 'kraver_inte_underlag'"),
    (lambda d: d.update(okand=1), "har en okänd nyckel: 'okand'"),
    (lambda d: d.update(anteckning=5), "'anteckning' ska vara text"),
    (lambda d: d.update(kraver_inte_underlag={}), "'kraver_inte_underlag' ska vara en lista med regler"),
    (lambda d: d.update(tidsfonster_dagar=[30, 2]), "'tidsfonster_dagar', ska vara ett objekt med nycklar"),
    (lambda d: d["tidsfonster_dagar"].pop("kvitto"), "'tidsfonster_dagar', saknar nyckeln 'kvitto'"),
    (lambda d: d["tidsfonster_dagar"].update(kreditnota=5), "'tidsfonster_dagar', har en okänd nyckel: 'kreditnota'"),
])
def test_trasig_form_stoppas(tmp_path, andring, text):
    data = format_()
    andring(data)
    stoppas(tmp_path, data, text)


@pytest.mark.parametrize("varde, visas", [(-1, "-1"), (HOGST_DAGAR + 1, "367"), (True, "true eller false"),
                                          (1.5, "decimaltal"), ("7", "text"), (None, "null"), ([7], "en lista"),
                                          (10 ** 14, str(10 ** 14))])
def test_antal_dagar_ska_vara_ett_heltal_fran_0_till_366(tmp_path, varde, visas):
    stoppas(tmp_path, format_(saknat_underlag_efter_dagar=varde),
            "'saknat_underlag_efter_dagar' ska vara ett heltal från 0 till och med 366 (antal dagar), inte " + visas)
    stoppas(tmp_path, format_(tidsfonster_dagar={"leverantorsfaktura": varde, "kvitto": 2}),
            "tidsfönstret för 'leverantorsfaktura' ska vara ett heltal från 0 till och med 366")


@pytest.mark.parametrize("dagar", [0, 1, HOGST_DAGAR])
def test_gransvarden_for_dagar_godtas(tmp_path, dagar):
    data = format_(saknat_underlag_efter_dagar=dagar, tidsfonster_dagar={"leverantorsfaktura": dagar, "kvitto": dagar})
    resultat = ladda_matchningsformat(skriv(tmp_path, data))
    assert resultat["saknat_underlag_efter_dagar"] == dagar
    assert resultat["tidsfonster_dagar"] == {"leverantorsfaktura": dagar, "kvitto": dagar}


@pytest.mark.parametrize("regel, text", [
    ("insattning", "regel nummer 1 i 'kraver_inte_underlag' ska vara ett objekt med nycklar"),
    ({"riktning": "in", "referens_borjar_med": "A"}, "regel nummer 1 i 'kraver_inte_underlag' saknar nyckeln 'namn'"),
    ({"namn": "a", "referens_borjar_med": "A"}, "saknar nyckeln 'riktning'"),
    ({"namn": "a", "riktning": "in", "referens": "A"}, "har en okänd nyckel: 'referens'"),
    ({"namn": "a", "riktning": "IN", "referens_borjar_med": "A"}, "'riktning' ska vara en av 'in', 'ut'"),
    ({"namn": "a", "riktning": None, "referens_borjar_med": "A"}, "'riktning' ska vara en av 'in', 'ut'"),
    ({"namn": "a", "riktning": "in"}, "ska ha minst en av 'referens_borjar_med' och 'beskrivning_borjar_med',"
                                      " annars passar den alla bankrader"),
    ({"namn": "", "riktning": "in", "referens_borjar_med": "A"}, "'namn' får inte vara tomt"),
    ({"namn": "a", "riktning": "in", "referens_borjar_med": " "}, "'referens_borjar_med' får inte vara tomt"),
    ({"namn": "a", "riktning": "in", "beskrivning_borjar_med": 5}, "'beskrivning_borjar_med' får inte vara tomt"),
    ({"namn": "a", "riktning": "in", "referens_borjar_med": "A" + OSYNLIGT_MELLANSLAG},
     "'referens_borjar_med' innehåller tecknet U+200B"),
    ({"namn": "a", "riktning": "in", "referens_borjar_med": "A\nB"}, "får inte innehålla radbrytning"),
    ({"namn": "a", "riktning": "in", "referens_borjar_med": "A", "anteckning": []}, "'anteckning' ska vara text"),
])
def test_trasiga_regler_stoppas(tmp_path, regel, text):
    stoppas(tmp_path, regler(regel), text)


def test_samma_regelnamn_tva_ganger_stoppas(tmp_path):
    stoppas(tmp_path, regler({"namn": "a", "riktning": "in", "referens_borjar_med": "A"},
                             {"namn": "a", "riktning": "ut", "referens_borjar_med": "B", "hogst_belopp_ore": 1}),
            "regelnamnet 'a' står flera gånger")


@pytest.mark.parametrize("forsta, andra", [
    ({"referens_borjar_med": "IN-"}, {"referens_borjar_med": "IN-"}),
    ({"referens_borjar_med": "IN"}, {"referens_borjar_med": "IN-1"}),              # det ena börjar med det andra
    ({"referens_borjar_med": "IN-1"}, {"referens_borjar_med": "IN"}),
    ({"referens_borjar_med": "IN-"}, {"beskrivning_borjar_med": "X"}),             # olika fält: kan passa samma rad
    ({"referens_borjar_med": "IN-", "beskrivning_borjar_med": "X"}, {"referens_borjar_med": "IN-"}),
    ({"referens_borjar_med": "A", "beskrivning_borjar_med": "XY"}, {"referens_borjar_med": "AB",
                                                                    "beskrivning_borjar_med": "X"}),
])
def test_regler_som_kan_passa_samma_bankrad_stoppas(tmp_path, forsta, andra):
    stoppas(tmp_path, regler({"namn": "a", "riktning": "in", **forsta}, {"namn": "b", "riktning": "in", **andra}),
            "reglerna 'a' och 'b' kan båda passa samma bankrad. Varje bankrad ska höra till högst en regel.")


@pytest.mark.parametrize("forsta, andra", [
    ({"riktning": "in", "referens_borjar_med": "IN-"}, {"riktning": "ut", "referens_borjar_med": "IN-",
                                                        "hogst_belopp_ore": 1}),
    ({"riktning": "in", "referens_borjar_med": "IN-"}, {"riktning": "in", "referens_borjar_med": "UT-"}),
    ({"riktning": "in", "referens_borjar_med": "A", "beskrivning_borjar_med": "X"},
     {"riktning": "in", "referens_borjar_med": "A", "beskrivning_borjar_med": "Y"}),
    ({"riktning": "in", "referens_borjar_med": "in-"}, {"riktning": "in", "referens_borjar_med": "IN-"}),
])
def test_regler_som_aldrig_passar_samma_bankrad_godtas(tmp_path, forsta, andra):
    data = regler({"namn": "a", **forsta}, {"namn": "b", **andra})
    assert len(ladda_matchningsformat(skriv(tmp_path, data))["kraver_inte_underlag"]) == 2


# --- Gränsen för regler för pengar ut (hogst_belopp_ore), Hugos beslut 2026-10-25 ---

UT = {"namn": "a", "riktning": "ut", "beskrivning_borjar_med": "AVGIFT"}
GRANSEN_TEXT = "'hogst_belopp_ore' ska vara ett heltal i öre, större än 0 och med högst 15 siffror, inte "


def test_regel_for_pengar_ut_utan_grans_stoppas(tmp_path):
    stoppas(tmp_path, regler(UT),
            "regel nummer 1 i 'kraver_inte_underlag' saknar 'hogst_belopp_ore'. En regel för pengar ut ska ha en"
            " högsta summa i öre per bankrad, så att den aldrig gäller obegränsat.")


def test_testforetagets_regel_utan_grans_stoppas(tmp_path):
    # Samma sak i testföretagets eget format: utan gränsen går det inte att läsa.
    data = json.loads(MATCHNING_FIL.read_text(encoding="utf-8"))
    del [regel for regel in data["kraver_inte_underlag"] if regel["namn"] == "bankavgift"][0]["hogst_belopp_ore"]
    stoppas(tmp_path, data, "regel nummer 4 i 'kraver_inte_underlag' saknar 'hogst_belopp_ore'")


@pytest.mark.parametrize("varde, visas", [
    (True, "true eller false"), (False, "true eller false"), (1.5, "decimaltal"), (25000.0, "decimaltal"),
    ("25000", "text"), (None, "null"), ([25000], "en lista"), ({"ore": 1}, "ett objekt"),
])
def test_gransen_av_fel_typ_stoppas(tmp_path, varde, visas):
    stoppas(tmp_path, regler({**UT, "hogst_belopp_ore": varde}), GRANSEN_TEXT + visas + ".")


@pytest.mark.parametrize("varde", [0, -1, -25000, -(10 ** 15 - 1)])
def test_gransen_0_eller_negativ_stoppas(tmp_path, varde):
    stoppas(tmp_path, regler({**UT, "hogst_belopp_ore": varde}), GRANSEN_TEXT + str(varde) + ".")


@pytest.mark.parametrize("varde", [10 ** 15, 10 ** 15 + 1, 10 ** 30, 10 ** 5000, -10 ** 15])
def test_gransen_med_fler_an_15_siffror_stoppas_nar_formatet_kommer_direkt(varde):
    # Från filen stoppas ett så långt tal redan när JSON läses (nästa test). Ett format kan också
    # skickas direkt till matcha_period, och då stoppar kontrollen av gränsen det. Talet skrivs inte ut.
    with pytest.raises(MatchningsformatFel) as fel:
        kontrollera_matchningsformat(regler({**UT, "hogst_belopp_ore": varde}))
    assert str(fel.value) == ("Matchningsformatet, regel nummer 1 i 'kraver_inte_underlag': " + GRANSEN_TEXT
                              + "ett heltal med fler än 15 siffror.")


def test_gransen_med_fler_an_15_siffror_stoppas_i_filen(tmp_path):
    fil = tmp_path / "matchning.json"
    fil.write_text(json.dumps(regler({**UT, "hogst_belopp_ore": 1})).replace(
        '"hogst_belopp_ore": 1', '"hogst_belopp_ore": ' + "9" * 16), encoding="utf-8")
    with pytest.raises(MatchningsformatFel, match="innehåller ett heltal med 16 siffror"):
        ladda_matchningsformat(fil)


@pytest.mark.parametrize("varde", [1, 25000, 10 ** 15 - 1])
def test_gransvarden_for_gransen_godtas(tmp_path, varde):
    resultat = ladda_matchningsformat(skriv(tmp_path, regler({**UT, "hogst_belopp_ore": varde})))
    assert resultat["kraver_inte_underlag"] == [{**UT, "hogst_belopp_ore": varde}]
    assert type(resultat["kraver_inte_underlag"][0]["hogst_belopp_ore"]) is int


def test_regel_for_pengar_in_far_inte_ha_en_grans(tmp_path):
    # Bestämt i den här uppgiften: en gräns för pengar in används inte, och ska inte se ut som ett skydd.
    for varde in (25000, 0, "x"):
        stoppas(tmp_path, regler({"namn": "a", "riktning": "in", "referens_borjar_med": "IN-",
                                  "hogst_belopp_ore": varde}),
                "regel nummer 1 i 'kraver_inte_underlag' har 'hogst_belopp_ore', men gäller pengar in. En gräns"
                " gäller bara regler med riktning 'ut'")
    # Skydd: utan gränsen godtas samma regel.
    assert ladda_matchningsformat(skriv(tmp_path, regler({"namn": "a", "riktning": "in",
                                                          "referens_borjar_med": "IN-"})))["kraver_inte_underlag"]


def test_nycklar_som_inte_ar_text_stoppas_nar_formatet_kommer_direkt():
    # Från JSON är nycklarna alltid text, men ett format kan skickas direkt till matcha_period.
    for data, var in [({1: 2, "x": 3}, "Matchningsformatet"),
                      (format_(tidsfonster_dagar={"kvitto": 2, None: 1}), "Matchningsformatet, 'tidsfonster_dagar',"),
                      (regler({"namn": "a", "riktning": "in", "referens_borjar_med": "A", 5: 1}),
                       "Matchningsformatet, regel nummer 1 i 'kraver_inte_underlag'")]:
        with pytest.raises(MatchningsformatFel, match="^" + var + " har en nyckel som inte är text"):
            kontrollera_matchningsformat(data)


@pytest.mark.parametrize("innehall, text", [
    ("{", "är inte giltig JSON"),
    ('{"a": 1, "a": 2}', "nyckeln 'a' står flera gånger"),
    ("[" * 100_000 + "]" * 100_000, "för många hakparenteser eller klammerparenteser"),
    ('{"saknat_underlag_efter_dagar": ' + "9" * 5000 + "}", "innehåller ett heltal med 5000 siffror"),
    ("[]", "ska vara ett objekt med nycklar, inte list"),
])
def test_trasig_fil_stoppas(tmp_path, innehall, text):
    fil = tmp_path / "matchning.json"
    fil.write_text(innehall, encoding="utf-8")
    with pytest.raises(MatchningsformatFel, match="^Matchningsformatet") as fel:
        ladda_matchningsformat(fil)
    assert text in str(fel.value)


def test_saknad_fil_mapp_och_sokvag_av_fel_typ_stoppas(tmp_path):
    with pytest.raises(MatchningsformatFel, match="^Matchningsformatet saknas: filen finns inte"):
        ladda_matchningsformat(tmp_path / "finns-inte.json")
    with pytest.raises(MatchningsformatFel, match="^Matchningsformatet saknas: .* är en mapp"):
        ladda_matchningsformat(tmp_path)
    for sokvag in (None, 1, True, b"matchning.json"):
        with pytest.raises(MatchningsformatFel, match="sökvägen ska vara text eller en Path"):
            ladda_matchningsformat(sokvag)
    (tmp_path / "latin1.json").write_bytes('{"anteckning": "å"}'.encode("latin-1"))
    with pytest.raises(MatchningsformatFel, match="är inte sparat som UTF-8"):
        ladda_matchningsformat(tmp_path / "latin1.json")
