"""Tester för steg 99, Öppet 43: ett underlag som K4 har flaggat stoppas också i skapa_konteringsforslag.

Hugos beslut 2026-11-04 om granskning 30, beslut 1 (P1, prov g11), med samma regler som flödena: Hugos beslut 2026-10-30 om
granskning 22, punkt 3 ("inget förslag alls"), och om granskning 23, Öppet 29. K4 är kontrollen för dubbletter i
underlagsperioden (las_underlag.py), och dess ärenden står i underlagsperiod.arenden. Byggt i _kontrollera_k4, som
skapa_konteringsforslag anropar allra sist, efter Öppet 40. Ingen ny K4-logik.

  K4a, K4b och "K4a och K4b"  båda underlagen i paret stoppas, det flaggade och originalet.
  K4c                         det flaggade stoppas. Originalet godtas bara med K4c-märkningen i motiveringen, som flödena
                              skriver den (MARKNING_K4C).
  K4 (dublett)                dubletten finns inte i perioden och kan inte nås.

Alla stopp-test bygger förslaget för hand, förbi flödena, i exakt flödenas form, och `stoppas_av_k4` kräver att det är K4 som
stoppar. Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Vilka test som var röda före rättelsen, och varför, står i PROGRESS.md, "Läge 2026-11-04, steg 99 byggt".
"""

import ast
import inspect
import json
import shutil
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import konteringsfloden  # noqa: E402
import konteringsforslag  # noqa: E402
from konteringsforslag import kontrollera_underlag, skapa_konteringsforslag  # noqa: E402
from las_underlag import las_underlagsperiod  # noqa: E402
from test_konteringsfloden import DATAMAPP, Korning  # noqa: E402
from test_beslut_granskning_22 import (  # noqa: E402
    KOPIAN, annat_belopp, annat_datum, annat_nummer, skapa, stoppas, underlagsmapp_med_kopia,
)
from test_beslut_granskning_25 import ALLA_KONTROLLER, PROV_B  # noqa: E402
from test_beslut_granskning_26 import INGAENDE_MOMS, LEVERANTORSSKULDER, kalla, rad, roll, underlaget  # noqa: E402
from test_beslut_granskning_27 import ANDRA  # noqa: E402
from test_beslut_granskning_28 import forslag_med  # noqa: E402
from test_beslut_granskning_29 import KVITTO  # noqa: E402
from test_beslut_granskning_30 import betalningen, kvittot  # noqa: E402

OPPET_43 = "Öppet 43"
DUBLETTEN = "SYNT-U-2025-004"  # testdatans planterade dubblett av 003, K4
KOPIA_2 = "SYNT-U-2025-904"
K4AB = "K4a och K4b"


def lasa(mapp, id_):
    return json.loads((mapp / (id_ + ".json")).read_text(encoding="utf-8"))


def skriva(mapp, id_, data):
    (mapp / (id_ + ".json")).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def kopia_av_underlagen(tmp_path_factory, namn):
    mapp = tmp_path_factory.mktemp(namn) / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    return mapp


def mapp_g11(tmp_path_factory, namn):
    """Granskarens g11: 009 har 003:s fakturanummer, så att K4 flaggar paret (K4a och K4b)."""
    mapp = kopia_av_underlagen(tmp_path_factory, namn)
    nio = lasa(mapp, ANDRA)
    nio["fakturanummer"] = lasa(mapp, PROV_B)["fakturanummer"]
    skriva(mapp, ANDRA, nio)
    return mapp


def fakturan(korning, id_):
    """Fakturans form för hand: kostnaden och momsen per momsrad i debet, beloppet i kredit på leverantörsskulderna."""
    underlag = underlaget(korning, id_)
    regel = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    konton = kontrollera_underlag(underlag, regel, korning.regelbok, korning.momssatser).konton
    rader = []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        rader.append(rad(konton[sats], momsrad["underlag_ore"], 0, "lika", kalla(id_, "underlag_ore", sats)))
        rader.append(rad(roll(korning, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(id_, "moms_ore", sats)))
    rader.append(rad(roll(korning, LEVERANTORSSKULDER), 0, underlag["belopp_ore"], "lika", kalla(id_, "belopp_ore")))
    return forslag_med(korning, id_, rader, "Fakturan för hand", underlag["datum"], [id_], [])


def med_motivering(forslag, motivering):
    forslag["motivering"] = motivering
    return forslag


def stoppas_av_k4(korning, forslag, kontroll, id_, andra, *texter):
    """Förslaget stoppas av K4, och felet namnger underlaget, K4-kontrollen, det andra underlaget i paret och Öppet 43."""
    return stoppas(korning, forslag, kontroll, repr(id_), repr(andra), "'" + kontroll + "'", OPPET_43, *texter)


def flaggat_ar_ett_par(korning, kontroll, flaggat, original):
    """Skydd för uppställningen: K4 har verkligen flaggat paret, och flödena bygger inget förslag för det flaggade."""
    assert (kontroll, flaggat, original) in [(k4["kontroll"], k4["id"], k4["jamfort_med"])
                                             for k4 in korning.underlagsperiod.arenden]
    assert korning.forslag_for(flaggat) == []


def markning(*flaggade):
    """K4c-märkningen, skriven här för sig: testet ska se om flödena och kontrollen glider isär."""
    return (" Märkning K4c: " + ("underlaget " if len(flaggade) == 1 else "underlagen ") + ", ".join(map(repr, flaggade))
            + " är flaggat i underlagsperioden som möjlig dublett av det här förslagets underlag och har ett eget ärende"
            " (K4c) utan förslag. Den som godkänner bör se förslaget och ärendet tillsammans.")


def igen_for_hand(korning, forslag):
    """Skapar flödets förslag en gång till, med samma innehåll, genom skapa_konteringsforslag."""
    kopplingar = forslag.kopplingar
    kopplingar["underlag"] = [{"id": post["id"]} for post in kopplingar["underlag"]]
    kopplingar["bankrader"] = [{"id": post["id"]} for post in kopplingar["bankrader"]]
    return skapa(korning, {"forslag_id": forslag.forslag_id, "verifikation": forslag.verifikation,
                           "kopplingar": kopplingar, "motivering": forslag.motivering})


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_g11(tmp_path_factory):
    return Korning(underlag=mapp_g11(tmp_path_factory, "g11"))


def annan_motpart(data):
    data["motpart"] = "LEV-KAFFE"


@pytest.fixture(scope="module")
def korning_k4c(tmp_path_factory):
    """903 är 003 från en annan motpart, med samma nummer, belopp och datum: K4c flaggar 903 mot 003.

    Annan motpart, så att bankrad 26 bara passar 003 och förblir ett par. Med samma motpart och samma datum är raden tvetydig,
    eftersom fakturanumret då inte får avgöra (_kan_avgora i matcha_bank.py), och då stoppar Öppet 40 betalningen först.
    """
    return Korning(underlag=underlagsmapp_med_kopia(tmp_path_factory.mktemp("k4c"), PROV_B, KOPIAN, annan_motpart))


@pytest.fixture(scope="module")
def korning_k4c_samma_motpart(tmp_path_factory):
    """903 är 003 med ett annat fakturanummer: K4c flaggar 903 mot 003. Bankrad 26 är tvetydig, så bara fakturan går att pröva."""
    return Korning(underlag=underlagsmapp_med_kopia(tmp_path_factory.mktemp("k4c_motpart"), PROV_B, KOPIAN, annat_nummer))


@pytest.fixture(scope="module")
def korning_k4c_tva(tmp_path_factory):
    """Både 903 och 904 är 003 från andra motparter, med samma nummer, belopp och datum: K4c flaggar båda mot 003."""
    mapp = underlagsmapp_med_kopia(tmp_path_factory.mktemp("k4c_tva"), PROV_B, KOPIAN, annan_motpart)
    skriva(mapp, KOPIA_2, dict(lasa(mapp, PROV_B), id=KOPIA_2, motpart="LEV-TILLBEHOR"))
    return Korning(underlag=mapp)


@pytest.fixture(scope="module")
def korning_k4c_kvitto(tmp_path_factory):
    """903 är kvittot 015 från en annan motpart, med samma nummer, belopp och datum: K4c flaggar 903 mot 015.

    Bankrad 50 har 015:s motpart, så att matchningen parar den med 015 och inte kan tveka mellan de två.
    """
    mapp = kopia_av_underlagen(tmp_path_factory, "k4c_kvitto")
    femton = lasa(mapp, KVITTO)
    femton["id"], femton["motpart"] = KOPIAN, "BUTIK-STAD"
    skriva(mapp, KOPIAN, femton)
    return Korning(underlag=mapp)


@pytest.fixture(scope="module")
def korning_k4ab_kvitto(tmp_path_factory):
    """903 har 015:s motpart och nummer men bankrad 85:s belopp och datum: K4 flaggar paret, och båda har sin bankrad."""
    mapp = kopia_av_underlagen(tmp_path_factory, "k4ab_kvitto")
    femton = lasa(mapp, KVITTO)
    femton.update(id=KOPIAN, datum="2025-02-18", belopp_ore=35100,
                  moms=[{"momssats": 25, "underlag_ore": 28080, "moms_ore": 7020}])
    skriva(mapp, KOPIAN, femton)
    return Korning(underlag=mapp)


# --- g11 och resten av K4a och K4b: båda underlagen i paret stoppas ---

@pytest.mark.parametrize("id_, andra", [(PROV_B, ANDRA), (ANDRA, PROV_B)], ids=["003", "009"])
def test_g11_fakturan_for_hand_stoppas_for_bada_underlagen(korning_g11, id_, andra):
    # g11 i granskning 30, P1: K4 flaggar paret, flödena bygger inget, men fakturan för hand godtogs för båda.
    flaggat_ar_ett_par(korning_g11, K4AB, ANDRA, PROV_B)
    assert korning_g11.forslag_for(PROV_B) == []
    stoppas_av_k4(korning_g11, fakturan(korning_g11, id_), K4AB, id_, andra)


@pytest.mark.parametrize("andring, kontroll", [(annat_belopp, "K4a"), (annat_datum, "K4b")], ids=["k4a", "k4b"])
@pytest.mark.parametrize("id_, andra", [(PROV_B, KOPIAN), (KOPIAN, PROV_B)], ids=["originalet", "det_flaggade"])
def test_k4a_och_k4b_fakturan_stoppas_for_bada_underlagen(tmp_path, andring, kontroll, id_, andra):
    korningen = Korning(underlag=underlagsmapp_med_kopia(tmp_path, PROV_B, KOPIAN, andring))
    flaggat_ar_ett_par(korningen, kontroll, KOPIAN, PROV_B)
    stoppas_av_k4(korningen, fakturan(korningen, id_), kontroll, id_, andra)


@pytest.mark.parametrize("id_, andra, rad_nr", [(PROV_B, ANDRA, 26), (ANDRA, PROV_B, 84)], ids=["003", "009"])
def test_k4ab_betalningen_for_hand_stoppas_for_bada_underlagen(korning_g11, id_, andra, rad_nr):
    # Båda betalningarna är riktiga par i matchningen (granskning 31, v9), så Öppet 40 stoppar dem inte.
    bankraden = korning_g11.bankrad(2, rad_nr)
    assert (id_, bankraden["id"]) in {(post["underlag"]["id"], post["bankrad"]["id"])
                                      for post in korning_g11.resultat.matchning.matchningar}
    stoppas_av_k4(korning_g11, betalningen(korning_g11, id_, bankraden), K4AB, id_, andra)


@pytest.mark.parametrize("id_, andra, rad_nr", [(KVITTO, KOPIAN, 50), (KOPIAN, KVITTO, 85)], ids=["originalet", "det_flaggade"])
def test_k4ab_kvittot_for_hand_stoppas_for_bada_underlagen(korning_k4ab_kvitto, id_, andra, rad_nr):
    flaggat_ar_ett_par(korning_k4ab_kvitto, K4AB, KOPIAN, KVITTO)
    assert korning_k4ab_kvitto.forslag_for(KVITTO) == []
    stoppas_av_k4(korning_k4ab_kvitto, kvittot(korning_k4ab_kvitto, id_, korning_k4ab_kvitto.bankrad(2, rad_nr)), K4AB, id_,
                  andra)


def test_k4ab_ratt_markning_hjalper_inte(korning_g11):
    # Märkningen hör till K4c. Vid K4a och K4b stoppas båda, vad motiveringen än säger.
    forslag = med_motivering(fakturan(korning_g11, PROV_B), "Regeln i regelboken." + markning(ANDRA))
    stoppas_av_k4(korning_g11, forslag, K4AB, PROV_B, ANDRA)


# --- K4c: det flaggade underlaget stoppas ---

def test_k4c_det_flaggade_fakturan_stoppas(korning_k4c):
    flaggat_ar_ett_par(korning_k4c, "K4c", KOPIAN, PROV_B)
    stoppas_av_k4(korning_k4c, fakturan(korning_k4c, KOPIAN), "K4c", KOPIAN, PROV_B)


def test_k4c_det_flaggade_stoppas_ocksa_med_markningen(korning_k4c):
    forslag = med_motivering(fakturan(korning_k4c, KOPIAN), "Regeln i regelboken." + markning(KOPIAN))
    stoppas_av_k4(korning_k4c, forslag, "K4c", KOPIAN, PROV_B)


def test_k4c_det_flaggade_med_samma_motpart_fakturan_stoppas(korning_k4c_samma_motpart):
    flaggat_ar_ett_par(korning_k4c_samma_motpart, "K4c", KOPIAN, PROV_B)
    stoppas_av_k4(korning_k4c_samma_motpart, fakturan(korning_k4c_samma_motpart, KOPIAN), "K4c", KOPIAN, PROV_B)


def test_k4c_det_flaggades_betalning_stoppas(tmp_path_factory):
    # 003 är från LEV-KAFFE och 903 är samma faktura från LEV-TE, bankrad 26:s motpart. K4c flaggar 903 mot 003, och raden är ett
    # par med 903, så Öppet 40 stoppar inte. 004 tas bort: den är annars inte längre en dublett av 003.
    mapp = kopia_av_underlagen(tmp_path_factory, "k4c_betalning")
    (mapp / (DUBLETTEN + ".json")).unlink()
    tre = lasa(mapp, PROV_B)
    skriva(mapp, KOPIAN, dict(tre, id=KOPIAN))
    annan_motpart(tre)
    skriva(mapp, PROV_B, tre)
    korningen = Korning(underlag=mapp)
    flaggat_ar_ett_par(korningen, "K4c", KOPIAN, PROV_B)
    tjugosex = korningen.bankrad(2, 26)
    assert (KOPIAN, tjugosex["id"]) in {(post["underlag"]["id"], post["bankrad"]["id"])
                                        for post in korningen.resultat.matchning.matchningar}
    stoppas_av_k4(korningen, betalningen(korningen, KOPIAN, tjugosex), "K4c", KOPIAN, PROV_B)


def test_k4c_det_flaggades_kvitto_stoppas(tmp_path_factory):
    # 015 får belopp och datum från bankrad 110, och 903 är samma kvitto från BUTIK-STAD, radens motpart. K4c flaggar 903 mot
    # 015, och raden är ett par med 903. 019 tas bort: den har samma belopp och motpart och skulle göra raden tvetydig.
    mapp = kopia_av_underlagen(tmp_path_factory, "k4c_kvitto_flaggat")
    (mapp / "SYNT-U-2025-019.json").unlink()
    femton = lasa(mapp, KVITTO)
    femton.update(datum="2025-02-21", belopp_ore=32400, moms=[{"momssats": 25, "underlag_ore": 25920, "moms_ore": 6480}])
    skriva(mapp, KVITTO, femton)
    skriva(mapp, KOPIAN, dict(femton, id=KOPIAN, motpart="BUTIK-STAD"))
    korningen = Korning(underlag=mapp)
    flaggat_ar_ett_par(korningen, "K4c", KOPIAN, KVITTO)
    etthundratio = korningen.bankrad(2, 110)
    assert (KOPIAN, etthundratio["id"]) in {(post["underlag"]["id"], post["bankrad"]["id"])
                                            for post in korningen.resultat.matchning.matchningar}
    stoppas_av_k4(korningen, kvittot(korningen, KOPIAN, etthundratio), "K4c", KOPIAN, KVITTO)


# --- K4c: originalet godtas bara med märkningen ---

def originalets_fakturan(korning):
    return fakturan(korning, PROV_B)


def originalets_betalning(korning):
    return betalningen(korning, PROV_B, korning.bankrad(2, 26))


FEL_MOTIVERINGAR = {
    "ingen_markning": "Regeln i regelboken.",
    "fel_underlag": "Regeln i regelboken." + markning(ANDRA),
    "bara_ordet": "Regeln i regelboken. Märkning K4c.",
    "utan_underlaget": "Märkning K4c: se ärendet.",
    "namnet_utan_markning": "Underlaget " + repr(KOPIAN) + " är flaggat, se ärendet.",
    "namnet_efter_fel_markning": "Regeln." + markning(ANDRA) + " Se också " + repr(KOPIAN) + ".",
    "namnet_utan_citattecken": "Märkning K4c: underlaget " + KOPIAN + " är flaggat.",
    "bara_en_del_av_id": "Märkning K4c: underlaget " + repr(KOPIAN[:-1]) + " är flaggat.",
    "andra_bokstaver": "Regeln." + markning(KOPIAN).replace("Märkning K4c", "märkning k4c"),
}


@pytest.mark.parametrize("motivering", list(FEL_MOTIVERINGAR.values()), ids=list(FEL_MOTIVERINGAR))
@pytest.mark.parametrize("bygg", [originalets_fakturan, originalets_betalning], ids=["fakturan", "betalningen"])
def test_k4c_originalet_utan_ratt_markning_stoppas(korning_k4c, bygg, motivering):
    fel = stoppas_av_k4(korning_k4c, med_motivering(bygg(korning_k4c), motivering), "K4c", PROV_B, KOPIAN)
    assert "K4c-märkningen" in fel


@pytest.mark.parametrize("motivering", [FEL_MOTIVERINGAR["ingen_markning"], "Regeln." + markning(ANDRA)],
                         ids=["ingen_markning", "fel_underlag"])
def test_k4c_originalets_kvitto_utan_ratt_markning_stoppas(korning_k4c_kvitto, motivering):
    forslag = kvittot(korning_k4c_kvitto, KVITTO, korning_k4c_kvitto.bankrad(2, 50))
    stoppas_av_k4(korning_k4c_kvitto, med_motivering(forslag, motivering), "K4c", KVITTO, KOPIAN)


@pytest.mark.parametrize("bygg", [originalets_fakturan, originalets_betalning], ids=["fakturan", "betalningen"])
def test_k4c_originalet_med_ratt_markning_godtas(korning_k4c, bygg):
    forslag = med_motivering(bygg(korning_k4c), "Regeln i regelboken." + markning(KOPIAN))
    assert skapa(korning_k4c, forslag).kontroller == ALLA_KONTROLLER


def test_k4c_samma_motpart_originalets_faktura_kraver_markningen(korning_k4c_samma_motpart):
    forslag = fakturan(korning_k4c_samma_motpart, PROV_B)
    stoppas_av_k4(korning_k4c_samma_motpart, forslag, "K4c", PROV_B, KOPIAN)
    forslag = med_motivering(forslag, "Regeln i regelboken." + markning(KOPIAN))
    assert skapa(korning_k4c_samma_motpart, forslag).kontroller == ALLA_KONTROLLER


def test_k4c_originalets_kvitto_med_ratt_markning_godtas(korning_k4c_kvitto):
    forslag = kvittot(korning_k4c_kvitto, KVITTO, korning_k4c_kvitto.bankrad(2, 50))
    forslag = med_motivering(forslag, "Regeln i regelboken." + markning(KOPIAN))
    assert skapa(korning_k4c_kvitto, forslag).kontroller == ALLA_KONTROLLER


@pytest.mark.parametrize("motivering", ["Regeln." + markning(KOPIAN), "Regeln." + markning(KOPIA_2),
                                        "Regeln." + markning(KOPIA_2, KOPIAN)],
                         ids=["bara_den_ena", "bara_den_andra", "fel_ordning"])
def test_k4c_tva_flaggade_utan_bada_i_markningen_stoppas(korning_k4c_tva, motivering):
    # Har K4c flaggat två underlag mot originalet ska märkningen ha båda, i samma ordning som flödena skriver dem.
    stoppas_av_k4(korning_k4c_tva, med_motivering(originalets_fakturan(korning_k4c_tva), motivering), "K4c", PROV_B, KOPIAN)


def test_k4c_tva_flaggade_med_bada_i_markningen_godtas(korning_k4c_tva):
    forslag = med_motivering(originalets_fakturan(korning_k4c_tva), "Regeln." + markning(KOPIAN, KOPIA_2))
    assert skapa(korning_k4c_tva, forslag).kontroller == ALLA_KONTROLLER


def test_originalet_i_bade_k4a_och_k4c_stoppas_ocksa_med_markningen(tmp_path):
    # 903 flaggas med K4a och 904 med K4c, båda mot 003. K4a stoppar båda, så märkningen för 904 hjälper inte, i vilken
    # ordning ärendena än står.
    mapp = underlagsmapp_med_kopia(tmp_path, PROV_B, KOPIA_2, annat_belopp)
    tre = lasa(mapp, PROV_B)
    tre["id"], tre["fakturanummer"] = KOPIAN, tre["fakturanummer"] + "-B"
    skriva(mapp, KOPIAN, tre)
    korningen = Korning(underlag=mapp)
    assert {(k4["kontroll"], k4["id"]) for k4 in korningen.underlagsperiod.arenden} >= {("K4a", KOPIA_2), ("K4c", KOPIAN)}
    forslag = med_motivering(originalets_fakturan(korningen), "Regeln." + markning(KOPIAN))
    stoppas_av_k4(korningen, forslag, "K4a", PROV_B, KOPIA_2)


# --- K4 (dublett): dubletten kan inte nås, och originalet godtas som förut ---

def test_k4_dubletten_finns_inte_i_perioden_och_kan_inte_nas(korning):
    # Skydd: K4 har tagit bort 004 ur perioden, så ett förslag för den stoppas redan av ursprunget, K4-kontrollen behövs inte.
    assert [(k4["kontroll"], k4["jamfort_med"]) for k4 in korning.underlagsperiod.arenden if k4["id"] == DUBLETTEN] == [
        ("K4", PROV_B)]
    assert DUBLETTEN not in [post["id"] for post in korning.underlagsperiod.underlag]
    forslag = json.loads(json.dumps(fakturan(korning, PROV_B)).replace(PROV_B, DUBLETTEN))
    stoppas(korning, forslag, "ursprung", repr(DUBLETTEN), "inte finns i underlagsperioden")


def test_k4_originalet_till_en_dublett_godtas_utan_markning(korning):
    # Skydd: K4 tar bort dubletten, och originalet får sitt förslag som förut. Ingen märkning behövs.
    assert skapa(korning, fakturan(korning, PROV_B)).kontroller == ALLA_KONTROLLER
    assert skapa(korning, originalets_betalning(korning)).kontroller == ALLA_KONTROLLER


# --- Flödena: inget de bygger stoppas ---

def test_skydd_flodena_ger_samma_forslag_som_forut(korning):
    # 16 fakturor, 6 betalningar och 3 kvitton (granskning 30), och 4 bankavgifter utan underlag.
    former = {"FAKTURA": 0, "BETALNING": 0, "KVITTO": 0, "BANKRAD": 0}
    for forslag in korning.resultat.forslag:
        former[forslag.forslag_id.split("-")[1]] += 1
    assert former == {"FAKTURA": 16, "BETALNING": 6, "KVITTO": 3, "BANKRAD": 4}


def test_skydd_flodena_bygger_inget_som_kontrollen_stoppar(korning, korning_g11, korning_k4c, korning_k4c_samma_motpart,
                                                           korning_k4c_tva, korning_k4c_kvitto, korning_k4ab_kvitto, tmp_path):
    # Varje körning är en uppställning från testerna ovan. Att flödena gick att köra visar att inget av deras förslag stoppas,
    # eftersom ett stopp i skapa_konteringsforslag stoppar hela körningen. Här skapas varje förslag en gång till med samma
    # innehåll, så att det inte hänger på den vägen. Inget flaggat underlag får ha ett förslag, och antalet visar att skyddet
    # inte är tomt.
    korningar = [korning, korning_g11, korning_k4c, korning_k4c_samma_motpart, korning_k4c_tva, korning_k4c_kvitto,
                 korning_k4ab_kvitto]
    for namn, andring in (("k4a", annat_belopp), ("k4b", annat_datum)):
        mapp = tmp_path / namn
        mapp.mkdir()
        korningar.append(Korning(underlag=underlagsmapp_med_kopia(mapp, PROV_B, KOPIAN, andring)))
    antal = 0
    for korningen in korningar:
        flaggade = {k4["id"] for k4 in korningen.underlagsperiod.arenden}
        flaggade |= {k4["jamfort_med"] for k4 in korningen.underlagsperiod.arenden if k4["kontroll"] not in ("K4", "K4c")}
        for forslag in korningen.resultat.forslag:
            assert not flaggade & {post["id"] for post in forslag.kopplingar["underlag"]}, forslag.forslag_id
            igen = igen_for_hand(korningen, forslag)
            assert (igen.kontroller, igen.motivering, igen.verifikation) == (forslag.kontroller, forslag.motivering,
                                                                             forslag.verifikation)
            antal += 1
    assert antal >= 200


def test_skydd_flodenas_markning_godtas_och_stammer_med_kontrollen(korning_k4c, korning_k4c_samma_motpart, korning_k4c_tva,
                                                                   korning_k4c_kvitto):
    # Originalets förslag får flödenas märkning, och den stoppas inte. Testets egen text är densamma som flödenas, så det här
    # slår larm om flödena och kontrollen skulle glida isär.
    for korningen, id_, flaggade, antal in ((korning_k4c, PROV_B, (KOPIAN,), 2), (korning_k4c_tva, PROV_B, (KOPIAN, KOPIA_2), 2),
                                            (korning_k4c_samma_motpart, PROV_B, (KOPIAN,), 1),
                                            (korning_k4c_kvitto, KVITTO, (KOPIAN,), 1)):
        forslagen = korningen.forslag_for(id_)
        assert len(forslagen) == antal
        for forslag in forslagen:
            assert forslag.motivering.endswith(markning(*flaggade)), forslag.motivering
            assert igen_for_hand(korningen, forslag).kontroller == ALLA_KONTROLLER


def test_skydd_flodenas_arenden_ar_kvar(korning_g11, korning_k4c):
    # Ärendena görs av flödena, inte av kontrollen. De ska vara kvar som förut.
    assert {arende["kontroll"] for arende in korning_g11.arenden_for(ANDRA)} == {K4AB}
    assert {arende["kontroll"] for arende in korning_g11.arenden_for(PROV_B)} == {K4AB}
    assert {arende["kontroll"] for arende in korning_k4c.arenden_for(KOPIAN)} == {"K4c"}
    assert korning_k4c.arenden_for(PROV_B) == []


# --- Ordningen, och vad som ska vara oförändrat ---

def test_k4_provas_efter_oppet_40(korning_k4c):
    # Kontrollen ligger sist. 903 är flaggat, men bankrad 26 är ett par med 003, så Öppet 40 säger sitt först.
    stoppas(korning_k4c, betalningen(korning_k4c, KOPIAN, korning_k4c.bankrad(2, 26)), "ursprung", "Öppet 40")


def test_skydd_ett_forslag_utan_underlag_berors_inte(korning, korning_g11):
    # Bankavgiften (flöde e) har inget underlag, och kontrollen frågar inte ens efter perioden.
    for korningen in (korning, korning_g11):
        avgiften = [forslag for forslag in korningen.resultat.forslag if not forslag.kopplingar["underlag"]][0]
        assert igen_for_hand(korningen, avgiften).kontroller == {"K2": "ok", "ursprung": "ok"}


def test_skydd_returvardet_och_anropet_ar_oforandrade(korning):
    assert skapa(korning, fakturan(korning, PROV_B)).kontroller == ALLA_KONTROLLER
    assert list(inspect.signature(skapa_konteringsforslag).parameters) == [
        "forslag", "regelbok", "kontoplan", "momssatser", "underlagsperiod", "bankperiod", "kassaperiod"]


# --- Kvar efter steget: dokumenterat, inte önskat ---

def test_kvar_k4_ser_bara_underlagen_i_perioden(tmp_path_factory, korning_g11):
    # Dokumenterar en gräns, inte ett önskat beteende (granskning 31, P1, Öppet 46). K4 körs på underlagen i perioden. 003 är
    # daterad 2025-01-15 och 009 2025-01-20. Slutar perioden före 009 flaggar K4 inget, och fakturan för 003 godtas. Registret i
    # designsteget för Öppet 46 och 47 ska ta hand om det över körningar.
    mapp = mapp_g11(tmp_path_factory, "smalare")
    smalare = las_underlagsperiod(mapp, "2025-01-01", "2025-01-19")
    assert ANDRA not in {k4["id"] for k4 in smalare.arenden} and ANDRA not in {post["id"] for post in smalare.underlag}
    assert skapa(korning_g11, fakturan(korning_g11, PROV_B), underlagsperiod=smalare).kontroller == ALLA_KONTROLLER


# --- Koden ---

KOD_FORSLAG = AGENT / "scripts" / "konteringsforslag.py"
KOD_FLODEN = AGENT / "scripts" / "konteringsfloden.py"


def funktionen(trad, namn):
    hittad, = [nod for nod in ast.walk(trad) if isinstance(nod, ast.FunctionDef) and nod.name == namn]
    return hittad


def test_koden_markningen_ar_en_enda_konstant_i_konteringsforslag():
    # En enda konstant: i konteringsforslag.py, importerad i konteringsfloden.py. Ingen import åt andra hållet (cirkel).
    forslag, floden = ast.parse(KOD_FORSLAG.read_text(encoding="utf-8")), ast.parse(KOD_FLODEN.read_text(encoding="utf-8"))
    assert konteringsfloden.MARKNING_K4C is konteringsforslag.MARKNING_K4C
    for trad, antal in ((forslag, 1), (floden, 0)):
        assert len([nod for nod in ast.walk(trad) if isinstance(nod, ast.Constant) and nod.value == "Märkning K4c"]) == antal
    fran_forslaget = [namn.name for nod in ast.walk(floden) if isinstance(nod, ast.ImportFrom)
                      and nod.module == "konteringsforslag" for namn in nod.names]
    assert "MARKNING_K4C" in fran_forslaget
    assert not [nod for nod in ast.walk(forslag) if isinstance(nod, (ast.Import, ast.ImportFrom)) and "konteringsfloden" in (
        [namn.name for namn in nod.names] + [getattr(nod, "module", None)])]


def test_koden_samma_regler_som_flodena():
    # Samma kontroller stoppar båda, här och i flödena, och K4-listan får inte glida isär.
    assert konteringsforslag._STOPPAR_BADA == konteringsfloden._STOPPAR_BADA
    assert konteringsforslag._K4C == konteringsfloden._K4C


def test_koden_kontrollen_ligger_sist_i_skapa_konteringsforslag():
    trad = ast.parse(KOD_FORSLAG.read_text(encoding="utf-8"))
    skapar = funktionen(trad, "skapa_konteringsforslag")
    rader = {nod.func.id: nod.lineno for nod in ast.walk(skapar) if isinstance(nod, ast.Call) and isinstance(nod.func, ast.Name)}
    assert rader["_kontrollera_underlagen"] < rader["_kontrollera_bankradens_par"] < rader["_kontrollera_k4"]
    assert rader["_kontrollera_k4"] < rader["Konteringsforslag"]


def test_koden_ingen_ny_k4_logik():
    # Kontrollen läser ärendena ur underlagsperioden och jämför inga fakturanummer, belopp, datum eller motparter själv.
    kod = ast.parse(KOD_FORSLAG.read_text(encoding="utf-8"))
    kontrollen = funktionen(kod, "_kontrollera_k4")
    texter = {nod.value for nod in ast.walk(kontrollen) if isinstance(nod, ast.Constant) and isinstance(nod.value, str)}
    assert not texter & {"fakturanummer", "belopp_ore", "datum", "motpart"}
    assert "arenden" in {nod.attr for nod in ast.walk(kontrollen) if isinstance(nod, ast.Attribute)}


def test_koden_namner_regeln():
    kod = KOD_FORSLAG.read_text(encoding="utf-8")
    assert OPPET_43 in kod and "steg 99" in kod and "Hugos beslut 2026-11-04 om granskning 30" in kod
