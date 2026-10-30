"""Tester för Hugos beslut 2026-10-30 om granskning 23 (GRANSKNING.md, "Hugos beslut 2026-10-30 om granskning 23").

- P1: K5, K7 och K8 i skapa_konteringsforslag prövas mot VARJE underlags egen regel (den regelboken ger underlaget
  på underlagets datum, Regelbok.regel_for_underlag), inte mot förslagets regel. Ett underlag som saknar egen regel
  stoppar förslaget. Granskarens prov B: momsfilen får en varugrupp som heter 'kostnad' (samma ord som nyckeln i
  R-BANK-AVGIFT:s kontering), och ett förslag byggs för hand med R-BANK-AVGIFT för underlagen SYNT-U-2025-028 och
  SYNT-U-2025-019, med bankrad 117 i januari som avgift mot banken. Förut godtogs förslaget med "K5: ok" och
  "K8: ok", eftersom kontrollerna prövades mot bankregeln. Nu stoppas 028 av K8 och 019 av K5.
- P3: betalsätten i en Z-regels kontering i regelboken och företagets namn ('foretag') prövas också mot de
  reserverade orden, bara vid exakt träff.
- Öppet 29: vid K4a och K4b stoppas BÅDA underlagen i paret, och båda får ett ärende. Vid K4c stoppas bara det
  flaggade underlaget, och originalets förslag märks med K4c-ärendet (det flaggade underlagets id) i motiveringen,
  så att den som godkänner ser kopplingen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot en kopia av d5b2fba (koden före rättelsen), se PROGRESS.md.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
TESTBUTIKEN = AGENT / "foretag" / "syntet-testbutik"
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from las_regelbok import RegelbokFel  # noqa: E402
from konteringsforslag import KonteringsforslagFel, skapa_konteringsforslag  # noqa: E402
from konteringsfloden import ARENDE_NYCKLAR  # noqa: E402
from test_konteringsfloden import Korning  # noqa: E402
from test_beslut_granskning_22 import (  # noqa: E402
    KOPIAN, annat_belopp, annat_datum, annat_nummer, forslag_for_hand, las_json, regel, regelbok_dar, skapa, skriv,
    underlagsmapp_med_kopia,
)

ORIGINALET = "SYNT-U-2025-003"


@pytest.fixture(scope="module")
def korning():
    return Korning()


# --- P1: granskarens prov B, ett förslag med underlag under en regel för bankrader ---

def momsfil_med_varugruppen_kostnad(tmp_path):
    """Testbutikens momsfil med en varugrupp 'kostnad' (12 %): samma ord som nyckeln i R-BANK-AVGIFT:s kontering."""
    data = las_json("momssatser.json")
    data["varugrupper"]["kostnad"] = [{"fran": "2025-01-01", "till": None, "sats": 12,
                                       "kalla": "SYNTETISK, granskarens prov B i granskning 23"}]
    return skriv(tmp_path, "momssatser.json", data)


@pytest.fixture(scope="module")
def korning_b(tmp_path_factory):
    return Korning(momssatser=momsfil_med_varugruppen_kostnad(tmp_path_factory.mktemp("prov_b")))


def rad(konto, debet, kredit, kalla):
    return {"konto": konto, "debet_ore": debet, "kredit_ore": kredit, "ursprung": {"berakning": "lika", "fran": [kalla]}}


def forslag_prov_b(korning, id_):
    """Granskarens prov B: underlaget id_ under bankregeln R-BANK-AVGIFT, med bankrad 117 i januari som avgift.

    Underlagets kostnad på bankregelns konto, momsen på kontot för ingående moms, beloppet på leverantörsskulderna,
    och avgiften mot banken. Raderna går ihop (K2), varje belopp har sitt ursprung, och regeln passar bankraden
    (ursprungskontrollen punkt 8 prövar bara bankraderna för en regel för bankrader). Förut prövades K5 och K8 mot
    bankregeln och sa "ok".
    """
    underlag, = [post for post in korning.underlagsperiod.underlag if post["id"] == id_]
    bankrad = korning.bankrad(1, 117)
    datum = bankrad["transaktionsdag"]
    bankregel = korning.regelbok.regel_for_bankrad("bankens-avgifter", datum)
    assert bankregel["id"] == "R-BANK-AVGIFT"
    kontoplan, kostnad, avgift = korning.kontoplan, bankregel["kontering"]["kostnad"], -bankrad["belopp_ore"]
    bankraden = {"kalla": "bankrad", "id": bankrad["id"], "falt": "belopp_ore"}
    rader = []
    for momsrad in underlag["moms"]:
        for konto, falt in ((kostnad, "underlag_ore"), (kontoplan.rollens_konto("ingaende_moms", datum), "moms_ore")):
            if momsrad[falt]:
                rader.append(rad(konto, momsrad[falt], 0, {"kalla": "underlag", "id": id_, "falt": falt,
                                                            "momssats": momsrad["momssats"]}))
    rader.append(rad(kontoplan.rollens_konto("leverantorsskulder", datum), 0, underlag["belopp_ore"],
                     {"kalla": "underlag", "id": id_, "falt": "belopp_ore"}))
    rader.append(rad(kostnad, avgift, 0, bankraden))
    rader.append(rad(kontoplan.rollens_konto("bank", datum), 0, avgift, bankraden))
    mot = korning.regelbok.kontrollerad_mot
    return {
        "forslag_id": "F-PROV-B-" + id_,
        "verifikation": {"datum": datum, "text": "Granskarens prov B, underlag " + id_, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_}], "bankrader": [{"id": bankrad["id"]}], "z_rapporter": [],
                       "regel": {"id": bankregel["id"], "regelbokens_kontrollsumma": korning.regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": "Granskarens prov B i granskning 23, byggt för hand förbi flödena.",
    }


def stoppas(korning, forslag, kontroll, *texter):
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa(korning, forslag)
    assert fel.value.kontroll == kontroll, str(fel.value)
    for text in texter:
        assert text in str(fel.value), str(fel.value)
    return str(fel.value)


def test_p1_prov_b_019_stoppas_av_k5_mot_underlagets_egen_regel(korning_b):
    # 019 har 12 % moms. Dess egen regel R-BUTIK-STAD väntar sig 25 % (varugruppen 'ovrigt'). Bankregeln har
    # 'kostnad', som i prov B har 12 %, så förut sa K5 "ok".
    text = stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-019"), "K5", "'SYNT-U-2025-019'",
                   "fel momssats", "R-BUTIK-STAD", "12 %", "Det ska vara ett ärende")
    assert "R-BANK-AVGIFT" not in text


def test_p1_prov_b_028_stoppas_av_k8_mot_underlagets_egen_regel(korning_b):
    # 028:s egen regel R-RESTAURANG-1 är avdragsbegränsad. Bankregeln är det inte, så förut sa K8 "ok".
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-028"), "K8", "'SYNT-U-2025-028'", "avdragsbegränsad",
            "R-RESTAURANG-1", "Det ska vara ett ärende")


def test_p1_prov_b_med_testbutikens_egen_momsfil_ger_ett_tydligt_fel(korning):
    # Granskning 23, P2: med testbutikens momsfil (ingen varugrupp 'kostnad') kraschade samma prov med KeyError.
    # Nu prövas underlagets egen regel, och felet säger K5 respektive K8.
    stoppas(korning, forslag_prov_b(korning, "SYNT-U-2025-019"), "K5", "R-BUTIK-STAD")
    stoppas(korning, forslag_prov_b(korning, "SYNT-U-2025-028"), "K8", "R-RESTAURANG-1")


def test_p1_ett_underlag_utan_egen_regel_stoppar_forslaget(tmp_path):
    # 019 med en motpart som regelboken inte känner. Flödena gör ärendet "ny motpart". Ett förslag byggt för hand
    # under bankregeln godtogs förut (K5 mot bankregeln sa "ok"). Nu stoppas det: utan egen regel kan K5 och K8
    # inte prövas.
    mapp = tmp_path / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    fil = mapp / "SYNT-U-2025-019.json"
    data = json.loads(fil.read_text(encoding="utf-8"))
    data["motpart"] = "OKAND-LEVERANTOR"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    korning = Korning(momssatser=momsfil_med_varugruppen_kostnad(tmp_path), underlag=mapp)
    arende, = korning.arenden_for("SYNT-U-2025-019")
    assert (arende["kontroll"], arende["typ"]) == ("regelboken", "ny motpart")
    stoppas(korning, forslag_prov_b(korning, "SYNT-U-2025-019"), "ursprung", "'SYNT-U-2025-019'",
            "har ingen regel i regelboken", "2025-02-21", "Det ska vara ett ärende")


def test_p1_ett_underlag_under_sin_egen_regel_godtas_som_forut(korning, korning_b):
    # Skydd: granskarens prov i granskning 22 (003 under sin egen regel R-LEV-TE) går igenom med alla kontrollerna,
    # också med prov B:s momsfil. Flödenas förslag är oförändrade.
    for en in (korning, korning_b):
        assert skapa(en, forslag_for_hand(en, ORIGINALET)).kontroller == {
            "K2": "ok", "ursprung": "ok", "K5": "ok", "K7": "ok", "K8": "ok"}
    assert [forslag.forslag_id for forslag in korning_b.forslag_for(ORIGINALET)] == [
        forslag.forslag_id for forslag in korning.forslag_for(ORIGINALET)]


def test_p1_kontrollera_underlag_tar_fortfarande_emot_regeln(korning_b):
    # Flödena frågar kontrollera_underlag med regeln de själva har slagit upp. Det är oförändrat (P1, granskning 22).
    # Med prov B:s momsfil, där 'kostnad' är en varugrupp: med testbutikens egen momsfil kraschar kontrollen med
    # KeyError när regeln är bankregeln (granskning 23, P2), och det är bara skapa_konteringsforslag som rättats.
    from konteringsforslag import kontrollera_underlag

    underlag, = [post for post in korning_b.underlagsperiod.underlag if post["id"] == "SYNT-U-2025-028"]
    bankregel = korning_b.regelbok.regel_for_bankrad("bankens-avgifter", "2025-01-31")
    egen = korning_b.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    assert kontrollera_underlag(underlag, egen, korning_b.regelbok, korning_b.momssatser).fynd[0].kontroll == "K8"
    # Mot bankregeln svarar kontrollen inte K8: därför ska skapa_konteringsforslag aldrig fråga med förslagets regel.
    assert kontrollera_underlag(underlag, bankregel, korning_b.regelbok, korning_b.momssatser).fynd == ()


def test_p1_spec_och_koden_sager_underlagets_egen_regel():
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "underlags egen regel" in spec and "granskning 23" in spec
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "regel_for_underlag" in kod
    assert "som ursprungskontrollen punkt 8 redan har visat är den regel" not in kod


# --- P3: betalsätten i regelboken och företagets namn prövas mot de reserverade orden ---

@pytest.mark.parametrize("namn", ["bankavgift", "Bankavgift", "BANKAVGIFT", "bank avgift"])
def test_p3_foretagets_namn_som_ar_ett_reserverat_ord_stoppar_regelboken(tmp_path, namn):
    def andring(regelbok):
        regelbok["foretag"] = namn
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'") as fel:
        Korning(regelbok=regelbok_dar(tmp_path, andring))
    assert "'foretag'" in str(fel.value)


@pytest.mark.parametrize("namn", ["bankavgift", "BANKAVGIFT", "bank avgift"])
def test_p3_ett_betalsatt_i_en_z_regel_som_ar_ett_reserverat_ord_stoppar_regelboken(tmp_path, namn):
    def andring(regelbok):
        betalsatt = regel(regelbok, "R-Z-TB-KASSA-1")["kontering"]["betalsatt"]
        betalsatt[namn] = betalsatt.pop("betalsatt_kontant")
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'") as fel:
        Korning(regelbok=regelbok_dar(tmp_path, andring))
    assert "betalsättet" in str(fel.value) and "R-Z-TB-KASSA-1" in str(fel.value)


def test_p3_bara_exakt_traff_stoppas_langre_namn_godtas(tmp_path):
    def andring(regelbok):
        regelbok["foretag"] = "Bankavgift AB"
        betalsatt = regel(regelbok, "R-Z-TB-KASSA-1")["kontering"]["betalsatt"]
        betalsatt["bankavgifter"] = betalsatt.pop("betalsatt_kontant")
        betalsatt["bank-avgift"] = betalsatt.pop("betalsatt_kort")
    korning = Korning(regelbok=regelbok_dar(tmp_path, andring))
    assert korning.regelbok.foretag == "Bankavgift AB" and korning.resultat.forslag
    z_regel, = [post for post in korning.regelbok.regler if post["id"] == "R-Z-TB-KASSA-1"]
    assert set(z_regel["kontering"]["betalsatt"]) == {"bankavgifter", "bank-avgift", "betalsatt_swish"}


def test_p3_dokumentationen_namner_betalsatten_i_regelboken_och_foretagets_namn():
    readme = (AGENT / "foretag" / "README.md").read_text(encoding="utf-8")
    avsnitt = readme.split("### Reserverade namn", 1)[1].split("\n## ", 1)[0]
    regelboksraden, = [rad_ for rad_ in avsnitt.splitlines() if rad_.startswith("- `regelbok.json`")]
    assert "`foretag`" in regelboksraden and "betalsätt" in regelboksraden
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "företagets namn" in spec.split("Reserverade ord stoppar alla namn i konfigurationen", 1)[1].split("\n", 1)[0]
    kod = (AGENT / "scripts" / "reserverade_namn.py").read_text(encoding="utf-8")
    assert "foretag" in kod and "betalsätt" in kod


# --- Öppet 29: K4a och K4b stoppar båda underlagen i paret, K4c bara det flaggade ---

def bada(data):
    annat_belopp(data)
    annat_datum(data)


@pytest.mark.parametrize("andring, kontroll, typ", [
    (annat_belopp, "K4a", "samma fakturanummer, olika belopp"),
    (annat_datum, "K4b", "samma fakturanummer, olika datum"),
    (bada, "K4a och K4b", "samma fakturanummer, olika belopp och datum"),
], ids=["k4a", "k4b", "k4a_och_k4b"])
def test_o29_k4a_och_k4b_stoppar_bada_underlagen_i_paret(tmp_path, andring, kontroll, typ):
    korning = Korning(underlag=underlagsmapp_med_kopia(tmp_path, ORIGINALET, KOPIAN, andring))
    # Inget förslag för någon av dem, varken för underlaget eller för betalningen.
    assert korning.forslag_for(KOPIAN) == [] and korning.forslag_for(ORIGINALET) == []
    # Det flaggade underlaget har sitt K4-ärende som förut (P2).
    flaggat, = korning.arenden_for(KOPIAN)
    assert (flaggat["kontroll"], flaggat["typ"], flaggat["underlag"]) == (kontroll, typ, KOPIAN)
    # Nytt: originalet har ett eget ärende med samma kontroll, som pekar på det flaggade underlaget.
    original, = korning.arenden_for(ORIGINALET)
    assert (original["kontroll"], original["typ"], original["underlag"], original["regel"]) == (
        kontroll, typ, ORIGINALET, "R-LEV-TE")
    assert KOPIAN in original["text"] and "Inget förslag" in original["text"] and "båda" in original["text"]
    assert original["niva"] is None and original["kraver_mansklig_bedomning"] is False
    assert tuple(original) == ARENDE_NYCKLAR
    # Båda ärendena står först i resultatet, som de andra K4-ärendena.
    assert [arende["underlag"] for arende in korning.resultat.arenden[:3]] == ["SYNT-U-2025-004", ORIGINALET, KOPIAN] or [
        arende["underlag"] for arende in korning.resultat.arenden[:3]] == ["SYNT-U-2025-004", KOPIAN, ORIGINALET]


def test_o29_k4c_stoppar_bara_det_flaggade_och_originalets_forslag_marks(tmp_path):
    korning = Korning(underlag=underlagsmapp_med_kopia(tmp_path, ORIGINALET, KOPIAN, annat_nummer))
    assert korning.forslag_for(KOPIAN) == []
    flaggat, = korning.arenden_for(KOPIAN)
    assert flaggat["kontroll"] == "K4c" and ORIGINALET in flaggat["text"]
    # Originalet har inget ärende och får sitt förslag, märkt med K4c-ärendet (det flaggade underlagets id).
    assert korning.arenden_for(ORIGINALET) == []
    forslagen = korning.forslag_for(ORIGINALET)
    assert [forslag.forslag_id for forslag in forslagen][0] == "F-FAKTURA-" + ORIGINALET
    for forslag in forslagen:
        assert "Märkning K4c" in forslag.motivering and KOPIAN in forslag.motivering, forslag.motivering
    # Raderna och kontrollerna är som utan kopian.
    utan_kopia = Korning().forslag_for(ORIGINALET)[0]
    assert forslagen[0].verifikation == utan_kopia.verifikation and forslagen[0].kontroller == utan_kopia.kontroller


def test_o29_bara_originalet_i_ett_k4c_par_marks(tmp_path, korning):
    # Utan kopian är inget förslag märkt, och med kopian är bara originalets förslag märkta.
    assert not [forslag for forslag in korning.resultat.forslag if "Märkning K4c" in forslag.motivering]
    med_kopia = Korning(underlag=underlagsmapp_med_kopia(tmp_path, ORIGINALET, KOPIAN, annat_nummer))
    markta = [forslag for forslag in med_kopia.resultat.forslag if "Märkning K4c" in forslag.motivering]
    assert markta and all([post["id"] for post in forslag.kopplingar["underlag"]] == [ORIGINALET] for forslag in markta)


def test_o29_dokumentationen_sager_vad_som_galler():
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "K4a och K4b" in spec and "Öppet 29" in spec
    progress = (AGENT / "PROGRESS.md").read_text(encoding="utf-8")
    assert "Öppet 29" in progress
