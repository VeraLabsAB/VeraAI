"""Tester för Hugos beslut efter uppgift 4 (2026-10-29): beslut c och de reserverade namnen.

GRANSKNING.md, "Beslut efter uppgift 4 (2026-10-29)":

- c: flöde e (bankavgifter) väljs bara när regeln i regelboken säger det med nyckeln 'flode', aldrig för
  att regeln råkar bara ha kontot 'kostnad'. Ett otillåtet värde stoppar regelboken. En regel för pengar
  ut utan nyckeln ger inget förslag utan ett ärende.
- Namnbytet: en regel i matchning.json eller regelbok.json får inte heta som ett reserverat ord
  (kärnans egna namn på flöden), så att kärnans ord aldrig krockar med ett företags namn.

Testerna hittar bankavgiftens regel på dess mönster ('AVG-'), inte på namnet, så att de går att köra
mot versionen före beslutet. Allt skrivs i testets tillfälliga mapp.
"""

import json
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
TESTBUTIKEN = AGENT / "foretag" / "syntet-testbutik"

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from las_matchningsformat import MatchningsformatFel, las_matchningsformat  # noqa: E402
from las_regelbok import RegelbokFel  # noqa: E402
from test_konteringsfloden import Korning  # noqa: E402

FLODET = "bankavgift"


def las_json(namn):
    return json.loads((TESTBUTIKEN / namn).read_text(encoding="utf-8"))


def skriv(tmp_path, namn, data):
    fil = tmp_path / namn
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return fil


def avgiftens_namn():
    """Namnet på regeln för bankens avgifter i testbutikens matchning.json, hittad på mönstret."""
    regel, = [regel for regel in las_json("matchning.json")["kraver_inte_underlag"]
              if regel.get("referens_borjar_med") == "AVG-"]
    return regel["namn"]


def avgiftsregeln(regelbok):
    """Regeln i regelboken (data) för bankens avgifter."""
    regel, = [regel for regel in regelbok["regler"] if regel["galler"].get("matchningsregel") == avgiftens_namn()]
    return regel


def regelbok_med(tmp_path, andring):
    regelbok = las_json("regelbok.json")
    andring(regelbok)
    return skriv(tmp_path, "regelbok.json", regelbok)


def avgifterna(korning):
    """Bankraderna som matchningen lägger under avgiftsregeln (två i januari och två i februari)."""
    rader = [post["bankrad"] for post in korning.resultat.matchning.kraver_inte_underlag
             if post["regel"] == avgiftens_namn()]
    assert len(rader) == 4
    return rader


def bankradens_forslag(korning, rad):
    return [forslag for forslag in korning.resultat.forslag
            if [post["id"] for post in forslag.kopplingar["bankrader"]] == [rad["id"]]]


def bankradens_arenden(korning, rad):
    return [arende for arende in korning.resultat.arenden if rad["id"] in arende["bankrader"]]


# --- c (i): bara kontot 'kostnad', utan 'flode', ger inte flöde e ---

def test_regel_med_bara_kostnad_och_utan_flode_ger_inte_flode_e_utan_ett_arende(tmp_path):
    def utan_flode(regelbok):
        regel = avgiftsregeln(regelbok)
        regel.pop("flode", None)
        assert set(regel["kontering"]) == {"kostnad"}  # skydd: regeln har bara kostnaden, som förut
    korning = Korning(regelbok=regelbok_med(tmp_path, utan_flode))
    regel_id = avgiftsregeln(las_json("regelbok.json"))["id"]
    for rad in avgifterna(korning):
        assert bankradens_forslag(korning, rad) == []
        arende, = bankradens_arenden(korning, rad)
        assert (arende["kontroll"], arende["typ"], arende["regel"]) == ("regelboken", "regeln saknar flöde", regel_id)
        # Pengar ut från banken utan ett känt flöde: nivå D och en människa avgör (D13).
        assert arende["niva"] == "D" and arende["kraver_mansklig_bedomning"] is True
        assert "'flode'" in arende["text"] and "gissar inte" in arende["text"]


def test_regel_for_pengar_in_utan_flode_ger_varken_forslag_eller_arende(tmp_path):
    # Kortinlösen, Swish och kontanter är pengar in och hör till flöde d (uppgift 5). Ingen av dem har
    # 'flode', och de får varken förslag eller ärende här, som förut.
    korning = Korning()
    andra = [post["bankrad"] for post in korning.resultat.matchning.kraver_inte_underlag
             if post["regel"] != avgiftens_namn()]
    assert andra and all(rad["belopp_ore"] > 0 for rad in andra)
    for rad in andra:
        assert bankradens_forslag(korning, rad) == [] and bankradens_arenden(korning, rad) == []


# --- c (ii): 'flode': "bankavgift" ger flöde e ---

def test_regel_med_flode_bankavgift_ger_flode_e(tmp_path):
    def med_flode(regelbok):
        avgiftsregeln(regelbok)["flode"] = FLODET
    korning = Korning(regelbok=regelbok_med(tmp_path, med_flode))
    regel_id = avgiftsregeln(las_json("regelbok.json"))["id"]
    assert korning.regelbok.regel_for_bankrad(avgiftens_namn(), "2025-01-31")["flode"] == FLODET
    for rad in avgifterna(korning):
        forslag, = bankradens_forslag(korning, rad)
        assert forslag.forslag_id == "F-BANKRAD-" + rad["id"] and forslag.kopplingar["regel"]["id"] == regel_id
        assert bankradens_arenden(korning, rad) == []


def test_testbutikens_avgiftsregel_har_flode_bankavgift():
    assert avgiftsregeln(las_json("regelbok.json"))["flode"] == FLODET


# --- c (iii): ett otillåtet värde på 'flode' stoppar regelboken ---

@pytest.mark.parametrize("varde", ["Bankavgift", "bankavgifter", "kortinlosen", "", 1, None, True, [FLODET],
                                   {"namn": FLODET}])
def test_otillatet_varde_pa_flode_stoppar_regelboken(tmp_path, varde):
    def med_varde(regelbok):
        avgiftsregeln(regelbok)["flode"] = varde
    with pytest.raises(RegelbokFel, match="'flode' i regel nummer .* ska vara 'bankavgift'"):
        Korning(regelbok=regelbok_med(tmp_path, med_varde))


def test_flode_i_en_regel_for_underlag_stoppar_regelboken(tmp_path):
    def pa_underlag(regelbok):
        [regel for regel in regelbok["regler"] if regel["galler"]["kalla"] == "underlag"][0]["flode"] = FLODET
    with pytest.raises(RegelbokFel, match="'flode' får bara finnas i en regel för bankrader"):
        Korning(regelbok=regelbok_med(tmp_path, pa_underlag))


def test_flode_bankavgift_med_andra_konton_an_kostnad_stoppar_regelboken(tmp_path):
    # Flödet bokför bara kostnaden mot banken. En regel med till exempel ett motkonto passar inte flödet.
    def med_motkonto(regelbok):
        regel = avgiftsregeln(regelbok)
        regel["flode"] = FLODET
        regel["kontering"]["motkonto"] = regel["kontering"]["kostnad"]
    with pytest.raises(RegelbokFel, match="ska bara ha kontot 'kostnad'"):
        Korning(regelbok=regelbok_med(tmp_path, med_motkonto))


# --- Reserverade namn (Hugos beslut i chatten 2026-10-29) ---

def matchning_med_namn(tmp_path, namn):
    """Testbutikens matchning.json där avgiftsregeln heter namn, och regelboken som pekar på samma namn."""
    gammalt = avgiftens_namn()
    matchning = las_json("matchning.json")
    [regel for regel in matchning["kraver_inte_underlag"] if regel["namn"] == gammalt][0]["namn"] = namn
    regelbok = las_json("regelbok.json")
    avgiftsregeln(regelbok)["galler"]["matchningsregel"] = namn
    return skriv(tmp_path, "matchning.json", matchning), skriv(tmp_path, "regelbok.json", regelbok)


@pytest.mark.parametrize("namn", ["bankavgift", "BANKAVGIFT", "Bankavgift", "bank avgift"])
def test_regel_i_matchningsformatet_med_ett_reserverat_namn_stoppas(tmp_path, namn):
    matchning, _ = matchning_med_namn(tmp_path, namn)
    with pytest.raises(MatchningsformatFel, match="det reserverade ordet 'bankavgift'"):
        las_matchningsformat(matchning)


@pytest.mark.parametrize("namn", ["bank-avgift", "bankavgifter", "bankens-avgifter"])
def test_namn_som_bara_liknar_ett_reserverat_ord_godtas(tmp_path, namn):
    matchning, regelbok = matchning_med_namn(tmp_path, namn)
    korning = Korning(regelbok=regelbok, matchning=matchning)
    assert korning.regelbok.regel_for_bankrad(namn, "2025-01-31") is not None


@pytest.mark.parametrize("regel_id", ["bankavgift", "BANKAVGIFT"])
def test_regel_i_regelboken_med_ett_reserverat_id_stoppas(tmp_path, regel_id):
    def med_id(regelbok):
        avgiftsregeln(regelbok)["id"] = regel_id
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'"):
        Korning(regelbok=regelbok_med(tmp_path, med_id))


def test_varje_flode_ar_ett_reserverat_namn():
    # Kärnans namn på ett flöde får aldrig vara ett namn som ett företag kan ge en regel.
    import las_matchningsformat
    import las_regelbok

    assert las_regelbok.FLODEN == (FLODET,)
    assert set(las_regelbok.FLODEN) <= set(las_matchningsformat.RESERVERADE_NAMN)


def test_readme_listar_de_reserverade_namnen():
    import las_matchningsformat

    readme = (AGENT / "foretag" / "README.md").read_text(encoding="utf-8")
    avsnitt = readme.split("### Reserverade namn", 1)[1].split("\n## ", 1)[0]
    for namn in las_matchningsformat.RESERVERADE_NAMN:
        assert "`" + namn + "`" in avsnitt, namn
