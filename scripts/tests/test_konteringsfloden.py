"""Tester för flödena a, b och e med K5 och K8 (konteringsfloden.py, DESIGN-regelbok.md avsnitt 7, uppgift 4).

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1, läst med de vanliga
inläsningsfunktionerna. Valen i regelbokens 'bokforing' är antagna för testföretaget (Hugos beslut
2026-10-29, B3, D1, D13 och D14).
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

from las_bank import ladda_bankformat, las_bankfil, sla_ihop_bankperioder  # noqa: E402
from las_kontoplan import las_kontoplan  # noqa: E402
from las_matchningsformat import las_matchningsformat  # noqa: E402
from las_momssatser import las_momssatser  # noqa: E402
from las_regelbok import las_regelbok  # noqa: E402
from las_underlag import las_underlagsperiod  # noqa: E402
from konteringsfloden import (  # noqa: E402
    ARENDE_NYCKLAR, STANGD_DAG, KonteringsflodeFel, Konteringsresultat, kontera_period,
)
from konteringsforslag import Konteringsforslag  # noqa: E402

BEDOMNING = "2025-04-15"


def bankperiod():
    """Testdatans bankrader för januari och februari, med saldona ur facit.json.

    Mars stoppas av K1: bank_2025-03.csv har ett planterat brott i saldokedjan på radnummer 74 (facit.json).
    Underlagen från mars har därför ingen bankrad här.
    """
    saldon = json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))["bank"]
    bankformat = ladda_bankformat(TESTBUTIKEN / "bankformat.json")
    manader, ingaende = [], saldon["2025-01"]["ingaende_saldo_ore"]
    for manad in ("2025-01", "2025-02"):
        manader.append(las_bankfil(DATAMAPP / ("bank_" + manad + ".csv"), bankformat, ingaende,
                                   saldon[manad]["utgaende_saldo_ore"]))
        ingaende = manader[-1].utgaende_saldo_ore
    return manader, sla_ihop_bankperioder(manader)


class Korning:
    """En körning av flödena, med testbutikens filer om inget annat anges."""

    def __init__(self, regelbok=TESTBUTIKEN / "regelbok.json", momssatser=TESTBUTIKEN / "momssatser.json",
                 underlag=DATAMAPP / "underlag", bedomning=BEDOMNING, matchning=TESTBUTIKEN / "matchning.json"):
        self.kontoplan = las_kontoplan(TESTBUTIKEN / "kontoplan.json")
        self.momssatser = las_momssatser(momssatser)
        self.regelbok = las_regelbok(regelbok, self.kontoplan, self.momssatser, las_matchningsformat(matchning))
        self.manader, self.bankperiod = bankperiod()
        self.underlagsperiod = las_underlagsperiod(underlag, "2025-01-01", "2025-03-31")
        self.resultat = kontera_period(self.regelbok, self.kontoplan, self.momssatser, self.underlagsperiod,
                                       self.bankperiod, bedomning)

    def forslag_for(self, id_):
        """Förslagen som bygger på underlaget id_, i resultatets ordning."""
        return [forslag for forslag in self.resultat.forslag
                if id_ in [post["id"] for post in forslag.kopplingar["underlag"]]]

    def arenden_for(self, id_):
        return [arende for arende in self.resultat.arenden if arende["underlag"] == id_]

    def bankrad(self, manad, radnr):
        rad = self.manader[manad - 1].rader[radnr - 1]
        assert rad["radnr"] == radnr
        return rad


@pytest.fixture(scope="module")
def korning():
    return Korning()


def raderna(forslag):
    """(konto, debet, kredit, källorna) för varje rad i förslagets verifikation."""
    return [(rad["konto"], rad["debet_ore"], rad["kredit_ore"],
             [(kalla["kalla"], kalla["falt"]) for kalla in rad["ursprung"]["fran"]])
            for rad in forslag.verifikation["rader"]]


# --- Flöde a: SYNT-U-2025-003 och dess betalning (DESIGN 4a) ---

def test_003_och_betalningen_ger_exakt_verifikationerna_i_design_4a(korning):
    fakturan, betalningen = korning.forslag_for("SYNT-U-2025-003")
    # Verifikation 1, fakturan, 2025-01-07: 4010 och 2641 i debet, 2440 i kredit.
    assert fakturan.verifikation["datum"] == "2025-01-07"
    assert raderna(fakturan) == [
        ("4010", 1493800, 0, [("underlag", "underlag_ore")]),
        ("2641", 179256, 0, [("underlag", "moms_ore")]),
        ("2440", 0, 1673056, [("underlag", "belopp_ore")]),
    ]
    assert fakturan.kopplingar["bankrader"] == [] and fakturan.kopplingar["regel"]["id"] == "R-LEV-TE"
    # Verifikation 2, betalningen 2025-02-06, bank_2025-02.csv radnummer 26.
    bankraden = korning.bankrad(2, 26)
    assert betalningen.verifikation["datum"] == "2025-02-06" == bankraden["transaktionsdag"]
    assert raderna(betalningen) == [
        ("2440", 1673056, 0, [("underlag", "belopp_ore")]),
        ("1940", 0, 1673056, [("bankrad", "belopp_ore")]),
    ]
    assert betalningen.verifikation["rader"][1]["ursprung"]["fran"][0]["id"] == bankraden["id"]
    assert [(post["id"], post["radnr"]) for post in betalningen.kopplingar["bankrader"]] == [(bankraden["id"], 26)]
    assert betalningen.kopplingar["regel"]["id"] == "R-LEV-TE"
    assert korning.arenden_for("SYNT-U-2025-003") == []


def test_forslagen_ar_konteringsforslag_som_klarat_kontrollerna(korning):
    assert type(korning.resultat) is Konteringsresultat and korning.resultat.forslag
    for forslag in korning.resultat.forslag:
        assert type(forslag) is Konteringsforslag
        assert forslag.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_020_med_tva_momssatser_far_en_kostnadsrad_och_en_momsrad_per_sats(korning):
    fakturan = korning.forslag_for("SYNT-U-2025-020")[0]
    assert [(konto, debet, kredit) for konto, debet, kredit, _ in raderna(fakturan)][-1][0] == "2440"
    satser = [kalla["momssats"] for rad in fakturan.verifikation["rader"] for kalla in rad["ursprung"]["fran"]
              if "momssats" in kalla]
    assert sorted(satser) == [12, 12, 25, 25]


def test_obetald_faktura_far_bara_fakturan(korning):
    obetalda = {post["id"] for post in korning.resultat.matchning.oavstamda_underlag
                if post["typ"] == "leverantorsfaktura"}
    med_forslag = [id_ for id_ in obetalda if korning.forslag_for(id_)]
    assert med_forslag  # skydd mot att testet inte prövar något
    for id_ in med_forslag:
        assert [forslag.forslag_id for forslag in korning.forslag_for(id_)] == ["F-FAKTURA-" + id_]


def test_varje_betald_faktura_med_regel_har_fakturan_och_betalningen(korning):
    betalda = {post["underlag"]["id"]: post["bankrad"] for post in korning.resultat.matchning.matchningar
               if post["underlag"]["typ"] == "leverantorsfaktura"}
    provade = 0
    for id_, bankraden in betalda.items():
        forslag = korning.forslag_for(id_)
        if not forslag:
            assert korning.arenden_for(id_), id_  # utan förslag finns alltid ett ärende
            continue
        provade += 1
        assert [f.forslag_id for f in forslag] == ["F-FAKTURA-" + id_, "F-BETALNING-" + id_]
        assert forslag[1].verifikation["datum"] == bankraden["transaktionsdag"]
    assert provade >= 5


def test_summan_av_ingaende_moms_stammer_med_underlagens_moms(korning):
    # Underlagen som ska bokföras med sin moms: varje faktura och varje kvitto med en bankrad som inte har
    # något ärende. Räknat ur underlagen, matchningen och ärendena, inte ur förslagen.
    matchade = {post["underlag"]["id"] for post in korning.resultat.matchning.matchningar}
    med_arende = {arende["underlag"] for arende in korning.resultat.arenden}
    bokforda = [underlag for underlag in korning.underlagsperiod.underlag if underlag["id"] not in med_arende
                and (underlag["typ"] == "leverantorsfaktura" or (underlag["typ"] == "kvitto"
                                                                 and underlag["id"] in matchade))]
    assert any(underlag["typ"] == "kvitto" for underlag in bokforda)  # skydd: kvittona prövas också
    vantat = sum(rad["moms_ore"] for underlag in bokforda for rad in underlag["moms"])
    ingaende = korning.kontoplan.rollens_konto("ingaende_moms", "2025-01-01")
    i_forslagen = sum(rad["debet_ore"] - rad["kredit_ore"] for forslag in korning.resultat.forslag
                      for rad in forslag.verifikation["rader"] if rad["konto"] == ingaende)
    assert vantat > 0 and i_forslagen == vantat
    # Varje underlags moms står i ett enda förslag. Ett momsfritt underlag (moms 0) har ingen momsrad.
    for underlag in bokforda:
        momsforslag = [forslag for forslag in korning.forslag_for(underlag["id"])
                       if any(rad["konto"] == ingaende for rad in forslag.verifikation["rader"])]
        assert len(momsforslag) == (1 if any(rad["moms_ore"] for rad in underlag["moms"]) else 0), underlag["id"]


# --- K5: SYNT-U-2025-019 (DESIGN 4b och 6) ---

def test_019_blir_k5_niva_d_och_far_inget_forslag(korning):
    assert korning.forslag_for("SYNT-U-2025-019") == []
    arende, = korning.arenden_for("SYNT-U-2025-019")
    assert arende["kontroll"] == "K5" and arende["typ"] == "fel momssats"
    # B2: nivå D direkt, och märkningen "kräver mänsklig bedömning".
    assert arende["niva"] == "D" and arende["kraver_mansklig_bedomning"] is True
    assert arende["regel"] == "R-BUTIK-STAD"
    # Satsen i underlaget och satsen som regeln väntar sig.
    assert "12 %" in arende["text"] and "'ovrigt' (25 %)" in arende["text"]
    # Kvittot är betalt med bankraden 2025-02-21 (bank_2025-02.csv radnummer 110).
    assert arende["bankrader"] == (korning.bankrad(2, 110)["id"],)


def test_arendena_har_exakt_nycklarna_och_kan_inte_andras(korning):
    assert korning.resultat.arenden
    for arende in korning.resultat.arenden:
        assert tuple(arende) == ARENDE_NYCKLAR
        with pytest.raises(TypeError):
            arende["niva"] = "A"
    with pytest.raises(AttributeError):
        korning.resultat.forslag = ()


def test_inget_falt_for_bokfort_eller_godkant(korning):
    for arende in korning.resultat.arenden:
        assert not [nyckel for nyckel in arende if "bokf" in nyckel or "godk" in nyckel]
    for forslag in korning.resultat.forslag:
        assert not [namn for namn in dir(forslag) if "bokf" in namn or "godk" in namn]


def underlagsmapp(tmp_path, **andrade):
    """En kopia av testdatans underlag, där varje underlag i andrade får de nya värdena."""
    mapp = tmp_path / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    for id_, andring in andrade.items():
        fil = mapp / (id_.replace("_", "-") + ".json")
        data = json.loads(fil.read_text(encoding="utf-8"))
        andring(data)
        fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return mapp


def satt_moms(sats=None, underlag_ore=None, moms_ore=None, belopp_ore=None):
    def andring(data):
        rad = data["moms"][0]
        for nyckel, varde in (("momssats", sats), ("underlag_ore", underlag_ore), ("moms_ore", moms_ore)):
            if varde is not None:
                rad[nyckel] = varde
        if belopp_ore is not None:
            data["belopp_ore"] = belopp_ore
    return andring


def test_k5_moms_som_inte_stammer_med_satsen(tmp_path):
    # 003: 14 938,00 kr med 12 % ger 1 792,56 kr. Fem öre flyttas från beloppet till momsen, så att
    # underlaget fortfarande går ihop (K13), men momsen skiljer mer än momsfilens 1 öre från satsen.
    mapp = underlagsmapp(tmp_path, SYNT_U_2025_003=satt_moms(underlag_ore=1493795, moms_ore=179261))
    korning = Korning(underlag=mapp)
    arende, = korning.arenden_for("SYNT-U-2025-003")
    assert (arende["kontroll"], arende["typ"], arende["niva"]) == ("K5", "moms stämmer inte med satsen", "D")
    assert arende["kraver_mansklig_bedomning"] is True
    # Ingen faktura och ingen betalning.
    assert korning.forslag_for("SYNT-U-2025-003") == []


def test_k5_moms_inom_toleransen_godtas(tmp_path):
    # Ett öre från satsen är inom momsfilens tolerans (D4: momsen tas exakt som på underlaget). Beloppet
    # att betala ökas med samma öre, så att underlaget går ihop (K13). Då passar det inte längre bankraden.
    mapp = underlagsmapp(tmp_path, SYNT_U_2025_003=satt_moms(moms_ore=179257, belopp_ore=1673057))
    korning = Korning(underlag=mapp)
    assert korning.arenden_for("SYNT-U-2025-003") == []
    fakturan = korning.forslag_for("SYNT-U-2025-003")[0]
    assert raderna(fakturan)[1][:2] == ("2641", 179257)


def test_k5_sats_som_ingen_varugrupp_har(tmp_path):
    # 6 % finns inte i momsfilen. Momsen är räknad med 6 %, så bara punkt 1 slår larm.
    mapp = underlagsmapp(tmp_path, SYNT_U_2025_003=satt_moms(sats=6, underlag_ore=1578355, moms_ore=94701))
    arende, = Korning(underlag=mapp).arenden_for("SYNT-U-2025-003")
    assert (arende["kontroll"], arende["typ"], arende["niva"]) == ("K5", "fel momssats", "D")
    assert "ingen varugrupp i momsfilen har satsen" in arende["text"]


def konfiguration_med_tva_grupper_med_samma_sats(tmp_path, samma_konto):
    """En momsfil med en andra varugrupp med satsen 12 %, och R-LEV-TE med båda varugrupperna."""
    momsfil = json.loads((TESTBUTIKEN / "momssatser.json").read_text(encoding="utf-8"))
    momsfil["varugrupper"]["livsmedel_tva"] = momsfil["varugrupper"]["livsmedel"]
    (tmp_path / "momssatser.json").write_text(json.dumps(momsfil, ensure_ascii=False), encoding="utf-8")
    regelbok = json.loads((TESTBUTIKEN / "regelbok.json").read_text(encoding="utf-8"))
    regel = [regel for regel in regelbok["regler"] if regel["id"] == "R-LEV-TE"][0]
    regel["kontering"]["livsmedel_tva"] = "4010" if samma_konto else "5460"
    (tmp_path / "regelbok.json").write_text(json.dumps(regelbok, ensure_ascii=False), encoding="utf-8")
    return Korning(regelbok=tmp_path / "regelbok.json", momssatser=tmp_path / "momssatser.json")


def test_k5_satsen_passar_flera_varugrupper_med_olika_konton(tmp_path):
    korning = konfiguration_med_tva_grupper_med_samma_sats(tmp_path, samma_konto=False)
    arende, = korning.arenden_for("SYNT-U-2025-003")
    assert (arende["kontroll"], arende["typ"], arende["niva"]) == ("K5", "fel momssats", "D")
    assert "olika konton" in arende["text"]
    assert korning.forslag_for("SYNT-U-2025-003") == []


def test_k5_satsen_passar_flera_varugrupper_med_samma_konto(tmp_path):
    korning = konfiguration_med_tva_grupper_med_samma_sats(tmp_path, samma_konto=True)
    assert korning.arenden_for("SYNT-U-2025-003") == []
    assert raderna(korning.forslag_for("SYNT-U-2025-003")[0])[0][0] == "4010"


# --- Flöde b: kvitton och K8 (DESIGN 4b och 6) ---

def regelbok_med(tmp_path, andring):
    """En kopia av testbutikens regelbok med andring gjord, som fil i tmp_path."""
    regelbok = json.loads((TESTBUTIKEN / "regelbok.json").read_text(encoding="utf-8"))
    andring(regelbok)
    fil = tmp_path / "regelbok.json"
    fil.write_text(json.dumps(regelbok, ensure_ascii=False), encoding="utf-8")
    return fil


def test_015_ger_exakt_verifikationen_i_design_4b(korning):
    # Med testbutikens egen regel R-BUTIK-FORBRUKNING, utan någon regel som bara finns i testet (Hugos
    # beslut 2026-10-29, f).
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    bankraden = korning.bankrad(2, 50)
    assert kvittot.forslag_id == "F-KVITTO-SYNT-U-2025-015"
    # Kvittodatum (D14), inte transaktionsdagen eller bankens bokföringsdag.
    assert kvittot.verifikation["datum"] == "2025-02-10"
    assert raderna(kvittot) == [
        ("5460", 19760, 0, [("underlag", "underlag_ore")]),
        ("2641", 4940, 0, [("underlag", "moms_ore")]),
        ("1940", 0, 24700, [("bankrad", "belopp_ore")]),
    ]
    assert [post["id"] for post in kvittot.kopplingar["bankrader"]] == [bankraden["id"]]
    assert kvittot.kopplingar["regel"]["id"] == "R-BUTIK-FORBRUKNING"


@pytest.mark.parametrize("val, datum", [("transaktionsdag", "2025-02-10"), ("bokforingsdag", "2025-02-11")])
def test_kvittots_datum_foljer_regelbokens_val(tmp_path, val, datum):
    # Bankraden för 015 har transaktionsdagen 2025-02-10 och bokföringsdagen 2025-02-11.
    def andring(regelbok):
        regelbok["bokforing"]["verifikationsdatum"]["kvitto"] = val
    kvittot, = Korning(regelbok=regelbok_med(tmp_path, andring)).forslag_for("SYNT-U-2025-015")
    assert kvittot.verifikation["datum"] == datum


def test_015_har_regeln_i_testbutikens_regelbok_och_inget_arende(korning):
    # Ärendet "ny motpart" för 015 är borta: regeln står i testbutikens regelbok, inte bara i testet.
    assert korning.arenden_for("SYNT-U-2025-015") == []
    assert korning.regelbok.regel_for_underlag("kvitto", "BUTIK-FORBRUKNING", "2025-02-10")["id"] == (
        "R-BUTIK-FORBRUKNING")


def test_lev_tillbehor_far_faktura_och_betalning_pa_4010(korning):
    # R-LEV-TILLBEHOR (Hugos beslut 2026-10-29, f): SYNT-U-2025-008, fakturan från januari.
    forslag = korning.forslag_for("SYNT-U-2025-008")
    assert [f.forslag_id for f in forslag] == ["F-FAKTURA-SYNT-U-2025-008", "F-BETALNING-SYNT-U-2025-008"]
    assert raderna(forslag[0])[0][0] == "4010" and forslag[0].kopplingar["regel"]["id"] == "R-LEV-TILLBEHOR"
    assert korning.arenden_for("SYNT-U-2025-008") == []


# LEV-TELE (001), LEV-EL (002) och HYRESVARD (021).
@pytest.mark.parametrize("id_", ["SYNT-U-2025-001", "SYNT-U-2025-002", "SYNT-U-2025-021"])
def test_hyresvard_el_och_tele_ar_fortfarande_nya_motparter(korning, id_):
    # Kontona för hyra, el och telefon finns inte i kontoplanen än (PROGRESS.md, Öppet). Vera gissar inget.
    arende, = korning.arenden_for(id_)
    assert arende["typ"] == "ny motpart" and korning.forslag_for(id_) == []


def test_kvitto_med_bankrad_far_ett_forslag(korning):
    # BUTIK-STAD 2025-01-22, betalt med bank_2025-01.csv radnummer 81 (212,00 kr).
    bankraden = korning.bankrad(1, 81)
    kvitton = [forslag for forslag in korning.resultat.forslag if forslag.forslag_id.startswith("F-KVITTO-")
               and forslag.kopplingar["bankrader"][0]["id"] == bankraden["id"]]
    kvittot, = kvitton
    assert kvittot.verifikation["datum"] == "2025-01-22" and kvittot.kopplingar["regel"]["id"] == "R-BUTIK-STAD"
    assert [(konto, debet, kredit) for konto, debet, kredit, _ in raderna(kvittot)][-1] == ("1940", 0, 21200)
    assert sum(rad["debet_ore"] for rad in kvittot.verifikation["rader"]) == 21200


def test_kvitto_utan_bankrad_far_inget_forslag_och_inget_arende(korning):
    # Mars har ingen bankperiod här (K1), så kvittona från mars med en regel väntar på sin bankrad.
    vantande = [underlag for underlag in korning.underlagsperiod.underlag
                if underlag["typ"] == "kvitto" and underlag["datum"] >= "2025-03-01"
                and korning.regelbok.regel_for_underlag("kvitto", underlag["motpart"], underlag["datum"])
                and not korning.arenden_for(underlag["id"])]
    assert vantande
    oavstamda = {post["id"] for post in korning.resultat.matchning.oavstamda_underlag}
    for underlag in vantande:
        assert korning.forslag_for(underlag["id"]) == [] and underlag["id"] in oavstamda


def test_028_blir_k8_niva_d_och_far_inget_forslag(korning):
    assert korning.forslag_for("SYNT-U-2025-028") == []
    arende, = korning.arenden_for("SYNT-U-2025-028")
    assert arende["kontroll"] == "K8" and arende["typ"] == "avdragsbegränsat"
    # B2: nivå D direkt, och märkningen "kräver mänsklig bedömning".
    assert arende["niva"] == "D" and arende["kraver_mansklig_bedomning"] is True
    assert arende["regel"] == "R-RESTAURANG-1"
    # 2025-03-16 är en söndag, då butiken har stängt (regelbokens oppettider).
    assert arende["flaggor"] == (STANGD_DAG,)
    # Vera föreslår ingen fördelning mellan avdragsgill och icke avdragsgill del: inget belopp i ärendet.
    assert "föreslår inte hur stor del" in arende["text"]
    utan_namn = arende["text"].replace(arende["regel"], "").replace("K8", "")
    assert not any(tecken.isdigit() for tecken in utan_namn), utan_namn


def test_k8_sager_vilken_bankrad_det_galler_och_flaggar_inte_en_oppen_dag(tmp_path):
    # Med R-BUTIK-STAD avdragsbegränsad blir kvittot 2025-01-22 (en onsdag) ett K8-ärende med sin bankrad.
    def andring(regelbok):
        [regel for regel in regelbok["regler"] if regel["id"] == "R-BUTIK-STAD"][0]["villkor"]["avdragsbegransad"] = True
    korning = Korning(regelbok=regelbok_med(tmp_path, andring))
    bankraden = korning.bankrad(1, 81)
    arende, = [arende for arende in korning.resultat.arenden if arende["bankrader"] == (bankraden["id"],)]
    assert (arende["kontroll"], arende["niva"], arende["flaggor"]) == ("K8", "D", ())
    assert not [forslag for forslag in korning.resultat.forslag
                if bankraden["id"] in [post["id"] for post in forslag.kopplingar["bankrader"]]]


def test_004_ar_en_dublett_och_far_inget_forslag(korning):
    # K4 tar bort dubbletten redan i underlagsperioden, där den är ett ärende (DESIGN 4a).
    assert "SYNT-U-2025-004" not in [underlag["id"] for underlag in korning.underlagsperiod.underlag]
    assert "SYNT-U-2025-004" in str(korning.underlagsperiod.arenden)
    assert korning.forslag_for("SYNT-U-2025-004") == [] and korning.arenden_for("SYNT-U-2025-004") == []
    # Originalet SYNT-U-2025-003 bokförs en gång.
    assert len(korning.forslag_for("SYNT-U-2025-003")) == 2


# --- Flöde e: bankavgifter (DESIGN 4e, D13) ---

def bankradens_forslag(korning, rad):
    return [forslag for forslag in korning.resultat.forslag
            if [post["id"] for post in forslag.kopplingar["bankrader"]] == [rad["id"]]]


@pytest.mark.parametrize("radnr, ore", [(117, 12500), (118, 19900)])
def test_4e_bankavgifterna_i_januari(korning, radnr, ore):
    rad = korning.bankrad(1, radnr)
    forslag, = bankradens_forslag(korning, rad)
    assert forslag.forslag_id == "F-BANKRAD-" + rad["id"]
    # Transaktionsdagen (D14), utan moms och med bankraden som ursprung på båda raderna (D13).
    assert forslag.verifikation["datum"] == "2025-01-31" == rad["transaktionsdag"]
    assert raderna(forslag) == [("6570", ore, 0, [("bankrad", "belopp_ore")]),
                                ("1940", 0, ore, [("bankrad", "belopp_ore")])]
    assert forslag.kopplingar["underlag"] == [] and forslag.kopplingar["regel"]["id"] == "R-BANK-AVGIFT"
    assert "D13" in forslag.motivering


def test_alla_bankavgifter_far_ett_forslag_och_inget_annat_fran_matchningen_gor_det(korning):
    utan_underlag = [post for post in korning.resultat.matchning.kraver_inte_underlag]
    avgifter = [post["bankrad"] for post in utan_underlag if post["regel"] == "bankens-avgifter"]
    assert len(avgifter) == 4  # två i januari och två i februari
    for rad in avgifter:
        assert len(bankradens_forslag(korning, rad)) == 1
    # Kortinlösen, Swish och kontanter hör till flöde d (uppgift 5): inget förslag och inget ärende här.
    andra = [post["bankrad"] for post in utan_underlag if post["regel"] != "bankens-avgifter"]
    assert andra
    alla_bankrader = {id_ for arende in korning.resultat.arenden for id_ in arende["bankrader"]}
    for rad in andra:
        assert bankradens_forslag(korning, rad) == [] and rad["id"] not in alla_bankrader


def test_ingen_moms_pa_bankavgifterna(korning):
    ingaende = korning.kontoplan.rollens_konto("ingaende_moms", "2025-01-01")
    for forslag in korning.resultat.forslag:
        if forslag.forslag_id.startswith("F-BANKRAD-"):
            assert ingaende not in [rad["konto"] for rad in forslag.verifikation["rader"]]


def matchning_med_grans(tmp_path, grans):
    data = json.loads((TESTBUTIKEN / "matchning.json").read_text(encoding="utf-8"))
    [regel for regel in data["kraver_inte_underlag"] if regel["namn"] == "bankens-avgifter"][0]["hogst_belopp_ore"] = grans
    fil = tmp_path / "matchning.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return fil


def avgiftsregelns_grans(grans):
    def andring(regelbok):
        [regel for regel in regelbok["regler"] if regel["id"] == "R-BANK-AVGIFT"][0]["villkor"]["hogst_belopp_ore"] = grans
    return andring


def test_avgift_over_matchningens_grans_blir_ett_arende_med_niva_d(tmp_path):
    # Med gränsen 150 kr i matchningsformatet (och i regeln, som inte får ha en högre) är avgiften 199 kr
    # över gränsen. Gränsen läses ur konfigurationen, som i testbutikens 250 kr.
    korning = Korning(regelbok=regelbok_med(tmp_path, avgiftsregelns_grans(15000)),
                      matchning=matchning_med_grans(tmp_path, 15000))
    rad, rad_125 = korning.bankrad(1, 118), korning.bankrad(1, 117)
    arende, = [arende for arende in korning.resultat.arenden if arende["bankrader"] == (rad["id"],)]
    assert (arende["kontroll"], arende["typ"], arende["niva"]) == ("K3", "över gräns", "D")
    assert arende["kraver_mansklig_bedomning"] is True and arende["regel"] == "R-BANK-AVGIFT"
    assert "199,00 kr" in arende["text"] and "150,00 kr" in arende["text"] and "D13" in arende["text"]
    assert bankradens_forslag(korning, rad) == []
    # Matchningens eget ärende finns kvar, och avgiften på 125 kr får sitt förslag.
    assert [post["typ"] for post in korning.resultat.matchning.arenden if post["bankrad"]["id"] == rad["id"]] == [
        "över gräns"]
    assert len(bankradens_forslag(korning, rad_125)) == 1


def test_avgift_over_regelns_egen_grans_blir_ett_arende_med_niva_d(tmp_path):
    # Regeln skärper matchningsformatets 250 kr till 150 kr. Matchningen släpper igenom raden, flödet inte.
    korning = Korning(regelbok=regelbok_med(tmp_path, avgiftsregelns_grans(15000)))
    rad = korning.bankrad(1, 118)
    arende, = [arende for arende in korning.resultat.arenden if arende["bankrader"] == (rad["id"],)]
    assert (arende["kontroll"], arende["typ"], arende["niva"], arende["kraver_mansklig_bedomning"]) == (
        "K3", "över gräns", "D", True)
    assert "regelns gräns, 150,00 kr" in arende["text"]
    assert bankradens_forslag(korning, rad) == []


def test_avgift_exakt_pa_regelns_grans_far_ett_forslag(tmp_path):
    korning = Korning(regelbok=regelbok_med(tmp_path, avgiftsregelns_grans(19900)))
    assert len(bankradens_forslag(korning, korning.bankrad(1, 118))) == 1


def test_avgift_utan_regel_pa_datumet_blir_ett_arende(tmp_path):
    def andring(regelbok):
        [regel for regel in regelbok["regler"] if regel["id"] == "R-BANK-AVGIFT"][0]["villkor"]["giltig_till"] = (
            "2025-01-30")
    korning = Korning(regelbok=regelbok_med(tmp_path, andring))
    rad = korning.bankrad(1, 117)
    arende, = [arende for arende in korning.resultat.arenden if arende["bankrader"] == (rad["id"],)]
    assert (arende["kontroll"], arende["typ"], arende["regel"]) == ("regelboken", "ingen regel på datumet", None)
    assert bankradens_forslag(korning, rad) == []


def test_bankavgiftens_datum_foljer_regelbokens_val(tmp_path):
    def andring(regelbok):
        regelbok["bokforing"]["verifikationsdatum"]["bankrad"] = "bokforingsdag"
    korning = Korning(regelbok=regelbok_med(tmp_path, andring))
    rad = korning.bankrad(1, 117)
    forslag, = bankradens_forslag(korning, rad)
    assert forslag.verifikation["datum"] == rad["bokforingsdag"]
    assert "bokforingsdag" in forslag.motivering


# --- Regeln och K7 ---

def test_ny_motpart_blir_ett_arende_och_far_inget_forslag(korning):
    # HYRESVARD (SYNT-U-2025-021) har ingen regel i testbutikens regelbok.
    arende, = korning.arenden_for("SYNT-U-2025-021")
    assert (arende["kontroll"], arende["typ"], arende["regel"]) == ("regelboken", "ny motpart", None)
    assert arende["niva"] is None and arende["kraver_mansklig_bedomning"] is False
    assert korning.forslag_for("SYNT-U-2025-021") == []


def test_underlag_fran_en_agare_blir_alltid_ett_arende(tmp_path):
    # Ett påhittat underlag från AGARE-1, och en regel för ägaren (nivå D, som regelboken kräver).
    def till_agaren(data):
        data["motpart"] = "AGARE-1"
    mapp = underlagsmapp(tmp_path, SYNT_U_2025_003=till_agaren)
    regelbok = json.loads((TESTBUTIKEN / "regelbok.json").read_text(encoding="utf-8"))
    regelbok["regler"].append({"id": "R-AGARE", "galler": {"kalla": "underlag", "typ": "leverantorsfaktura",
                                                           "motpart": "AGARE-1"},
                               "kontering": {"livsmedel": "4010"}, "villkor": {"giltig_fran": "2025-01-01"},
                               "niva": "D"})
    (tmp_path / "regelbok.json").write_text(json.dumps(regelbok, ensure_ascii=False), encoding="utf-8")
    korning = Korning(regelbok=tmp_path / "regelbok.json", underlag=mapp)
    arende, = korning.arenden_for("SYNT-U-2025-003")
    assert (arende["kontroll"], arende["typ"], arende["regel"]) == ("K7", "kräver mänsklig bedömning", "R-AGARE")
    assert arende["kraver_mansklig_bedomning"] is True
    assert korning.forslag_for("SYNT-U-2025-003") == []


def test_betalning_efter_regelns_sista_dag_blir_ett_arende(tmp_path):
    # R-LEV-TE slutar dagen före betalningen av 003 (2025-02-06). Fakturan får sitt förslag, betalningen inte.
    regelbok = json.loads((TESTBUTIKEN / "regelbok.json").read_text(encoding="utf-8"))
    [regel for regel in regelbok["regler"] if regel["id"] == "R-LEV-TE"][0]["villkor"]["giltig_till"] = "2025-02-05"
    (tmp_path / "regelbok.json").write_text(json.dumps(regelbok, ensure_ascii=False), encoding="utf-8")
    korning = Korning(regelbok=tmp_path / "regelbok.json")
    assert [forslag.forslag_id for forslag in korning.forslag_for("SYNT-U-2025-003")] == ["F-FAKTURA-SYNT-U-2025-003"]
    arende, = korning.arenden_for("SYNT-U-2025-003")
    assert (arende["typ"], arende["regel"]) == ("ingen regel på datumet", "R-LEV-TE")


# --- Indatan ---

def test_en_annan_momsfil_an_regelbokens_stoppas(korning, tmp_path):
    fil = tmp_path / "momssatser.json"
    fil.write_bytes((TESTBUTIKEN / "momssatser.json").read_bytes() + b" ")
    with pytest.raises(KonteringsflodeFel, match="momsfilen är inte den som regelboken kontrollerades mot"):
        kontera_period(korning.regelbok, korning.kontoplan, las_momssatser(fil), korning.underlagsperiod,
                       korning.bankperiod, BEDOMNING)


def test_en_annan_kontoplan_an_regelbokens_stoppas(korning, tmp_path):
    fil = tmp_path / "kontoplan.json"
    fil.write_bytes((TESTBUTIKEN / "kontoplan.json").read_bytes() + b" ")
    with pytest.raises(KonteringsflodeFel, match="kontoplanen är inte den som regelboken kontrollerades mot"):
        kontera_period(korning.regelbok, las_kontoplan(fil), korning.momssatser, korning.underlagsperiod,
                       korning.bankperiod, BEDOMNING)


@pytest.mark.parametrize("plats, text", [(0, "regelboken ska komma från las_regelbok"),
                                         (1, "kontoplanen ska komma från las_kontoplan"),
                                         (2, "momsfilen ska komma från las_momssatser")])
def test_indata_som_inte_kommer_fran_inlasningen_stoppas(korning, plats, text):
    indata = [korning.regelbok, korning.kontoplan, korning.momssatser]
    indata[plats] = {}
    with pytest.raises(KonteringsflodeFel, match=text):
        kontera_period(*indata, korning.underlagsperiod, korning.bankperiod, BEDOMNING)


@pytest.mark.parametrize("plats, text", [(0, "regelboken är tom eller trasig"), (1, "kontoplanen är tom eller trasig"),
                                         (2, "momsfilen är tom eller trasig")])
def test_tomt_objekt_av_ratt_typ_stoppas(korning, plats, text):
    indata = [korning.regelbok, korning.kontoplan, korning.momssatser]
    indata[plats] = object.__new__(type(indata[plats]))
    with pytest.raises(KonteringsflodeFel, match=text):
        kontera_period(*indata, korning.underlagsperiod, korning.bankperiod, BEDOMNING)


def test_stangd_dag_flaggan_finns():
    # Skydd: flaggans text är den som DESIGN avsnitt 6 säger.
    assert STANGD_DAG == "köpt en dag då företaget har stängt"
