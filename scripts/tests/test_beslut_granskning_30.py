"""Tester för steg 98, Öppet 40: bankraden ska höra till underlaget enligt samma matchning som flödena använder.

Hugos beslut 2026-11-04 om granskning 29, beslut 2 (P2, r5), och Hugos beslut 2026-11-04 om granskning 30, beslut 3 (P3, g9
och g10). Byggt i _kontrollera_bankradens_par, som skapa_konteringsforslag anropar allra sist, efter flödenas former.

Kontrollen kör matcha_period själv, med samma perioder och samma regelbok som förslaget kontrolleras mot, och ett fast sent
datum. Det finns alltså inget matchningsresultat att lämna in, och därför inget som kan vara handbyggt. Saknas perioderna,
eller går matchningen inte att göra, stoppas förslaget. Flödena är inte ändrade.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets tillfälliga
mapp. Vilka test som var röda före rättelsen, och varför, står i PROGRESS.md, "Läge 2026-11-04, steg 98 byggt".
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

import konteringsforslag  # noqa: E402
from konteringsfloden import kontera_period  # noqa: E402
from konteringsforslag import KonteringsforslagFel, kontrollera_underlag, skapa_konteringsforslag  # noqa: E402
from las_bank import Bankperiod, ladda_bankformat, las_bankfil, sla_ihop_bankperioder  # noqa: E402
from las_underlag import las_underlagsperiod  # noqa: E402
from matcha_bank import MatchningFel, Matchningsresultat, matcha_period  # noqa: E402
from test_konteringsfloden import BEDOMNING, DATAMAPP, TESTBUTIKEN, Korning, underlagsmapp  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_25 import ALLA_KONTROLLER, PROV_B  # noqa: E402
from test_beslut_granskning_26 import (  # noqa: E402
    INGAENDE_MOMS, LEVERANTORSSKULDER, kalla, prov_b_003, rad, roll, underlaget,
)
from test_beslut_granskning_27 import ANDRA, betalningen_for_hand  # noqa: E402
from test_beslut_granskning_28 import BANK, bankkalla, forslag_med  # noqa: E402
from test_beslut_granskning_29 import KVITTO, korning_med_009  # noqa: E402

OPPET_40 = "Öppet 40"
# Bankrad 8 i februari är betalningen till LEV-TELE, och bankrad 26 är betalningen av 003 till LEV-TE.
RAD_8 = "8,2025-02-03,2025-02-03,SYNT-TELE-713,LEV-TELE,-748.75,"
RAD_26 = "26,2025-02-06,2025-02-06,SYNT-TE-761,LEV-TE,-16730.56,"


def bankperioden_med(mapp, gammal, ny):
    """Bankperioden för januari och februari, där raden gammal i februari är utbytt mot ny. Saldona är oförändrade."""
    saldon = json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))["bank"]
    bankformat = ladda_bankformat(TESTBUTIKEN / "bankformat.json")
    manader, ingaende = [], saldon["2025-01"]["ingaende_saldo_ore"]
    for manad in ("2025-01", "2025-02"):
        fil = mapp / ("bank_" + manad + ".csv")
        text = (DATAMAPP / fil.name).read_text(encoding="utf-8")
        if manad == "2025-02":
            assert gammal in text
            text = text.replace(gammal, ny)
        fil.write_text(text, encoding="utf-8")
        manader.append(las_bankfil(fil, bankformat, ingaende, saldon[manad]["utgaende_saldo_ore"]))
        ingaende = manader[-1].utgaende_saldo_ore
    return manader, sla_ihop_bankperioder(manader)


def korning_med_banken(korning, mapp, gammal, ny):
    """Samma körning, men med en bankperiod där en rad i februari är utbytt, och flödena körda igen på den."""
    korning.manader, korning.bankperiod = bankperioden_med(mapp, gammal, ny)
    korning.resultat = kontera_period(korning.regelbok, korning.kontoplan, korning.momssatser, korning.underlagsperiod,
                                      korning.bankperiod, BEDOMNING)
    return korning


def betalningen(korning, id_, bankrad):
    """Betalningens form för hand: underlagets belopp i debet på leverantörsskulderna, bankraden i kredit på bankkontot."""
    belopp = underlaget(korning, id_)["belopp_ore"]
    return forslag_med(korning, id_, [
        rad(roll(korning, LEVERANTORSSKULDER), belopp, 0, "lika", kalla(id_, "belopp_ore")),
        rad(roll(korning, BANK), 0, belopp, "lika", bankkalla(bankrad)),
    ], "Betalning för hand", bankrad["transaktionsdag"], [id_], [bankrad])


def kvittot(korning, id_, bankrad):
    """Kvittots form för hand: kostnaden och momsen per momsrad i debet, bankraden i kredit på bankkontot."""
    underlag = underlaget(korning, id_)
    regel = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    konton = kontrollera_underlag(underlag, regel, korning.regelbok, korning.momssatser).konton
    rader = []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        rader.append(rad(konton[sats], momsrad["underlag_ore"], 0, "lika", kalla(id_, "underlag_ore", sats)))
        rader.append(rad(roll(korning, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(id_, "moms_ore", sats)))
    rader.append(rad(roll(korning, BANK), 0, underlag["belopp_ore"], "lika", bankkalla(bankrad)))
    return forslag_med(korning, id_, rader, "Kvitto för hand", bankrad["transaktionsdag"], [id_], [bankrad])


def forslagen_for(korning, id_):
    return [forslag.forslag_id for forslag in korning.forslag_for(id_)]


def stoppas_av_paret(korning, forslag, id_, bankrad, *texter):
    """Förslaget stoppas av kontrollen av paret, och felet namnger underlaget, bankraden och Öppet 40."""
    return stoppas(korning, forslag, "ursprung", repr(id_), repr(bankrad["id"]), OPPET_40, *texter)


def lika_kopia_med_flera_kandidater(tmp_path_factory, namn):
    """Mappen där 009 har 003:s belopp och momsrad och 003 inte har sitt fakturanummer i bankraden.

    Då passar båda underlagen bankrad 26 (samma belopp och motpart, inom tidsfönstret), och inget fakturanummer avgör.
    004, testdatans planterade dubblett av 003, tas bort: med ett annat fakturanummer på 003 vore den annars en kandidat till.
    """
    mapp = tmp_path_factory.mktemp(namn) / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    (mapp / "SYNT-U-2025-004.json").unlink()
    tre = json.loads((mapp / (PROV_B + ".json")).read_text(encoding="utf-8"))
    nio = json.loads((mapp / (ANDRA + ".json")).read_text(encoding="utf-8"))
    nio["belopp_ore"], nio["moms"], tre["fakturanummer"] = tre["belopp_ore"], tre["moms"], "ANNAT-NUMMER-1"
    (mapp / (PROV_B + ".json")).write_text(json.dumps(tre, ensure_ascii=False), encoding="utf-8")
    (mapp / (ANDRA + ".json")).write_text(json.dumps(nio, ensure_ascii=False), encoding="utf-8")
    return mapp


def kvitto_med(tmp_path, underlag_ore, moms_ore):
    """En körning där kvittot 015 har de här beloppen. Datum och nummer är kvittots egna."""
    def andra(data):
        data["belopp_ore"] = underlag_ore + moms_ore
        data["moms"] = [{"momssats": 25, "underlag_ore": underlag_ore, "moms_ore": moms_ore}]
    return Korning(underlag=underlagsmapp(tmp_path, **{KVITTO: andra}))


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_tele(tmp_path_factory):
    """Granskarens r5 och g10: 009 har 748,75 kr, samma belopp som bankrad 8 i februari, betalningen till LEV-TELE."""
    return korning_med_009(tmp_path_factory, "oppet40", 66852, 8023)


@pytest.fixture(scope="module")
def korning_tvetydig(tmp_path_factory):
    return Korning(underlag=lika_kopia_med_flera_kandidater(tmp_path_factory, "tvetydig"))


# --- r5, g9 och g10: rätt form, fel bankrad ---

def test_r5_en_annan_leverantors_bankrad_stoppas(korning_tele):
    # r5 (granskning 29, P2): 009 mot bankrad 8, som är betalningen till LEV-TELE, inte till LEV-TE. Formen är flöde a:s.
    atta = korning_tele.bankrad(2, 8)
    assert -atta["belopp_ore"] == underlaget(korning_tele, ANDRA)["belopp_ore"]
    stoppas_av_paret(korning_tele, betalningen(korning_tele, ANDRA, atta), ANDRA, atta)


def test_g9_ett_kvitto_mot_en_annan_motparts_bankrad_stoppas(tmp_path):
    # g9 (granskning 30, P3): kvittot 015 har 748,75 kr. Kvittots form med bankrad 8, som är LEV-TELE.
    korningen = kvitto_med(tmp_path, 59900, 14975)
    atta = korningen.bankrad(2, 8)
    assert -atta["belopp_ore"] == underlaget(korningen, KVITTO)["belopp_ore"]
    assert forslagen_for(korningen, KVITTO) == []  # flödena bygger inget förslag för det
    stoppas_av_paret(korningen, kvittot(korningen, KVITTO, atta), KVITTO, atta)


def test_g10_en_bankrad_mot_agaren_utan_motparten_stoppas(tmp_path, korning_tele):
    # g10 (granskning 30, P3): 009 har 748,75 kr, och bankrad 8 har texten AGARE-1.
    manader, bankperioden = bankperioden_med(tmp_path, RAD_8, "8,2025-02-03,2025-02-03,SYNT-TELE-713,AGARE-1,-748.75,")
    atta = manader[1].rader[7]
    assert korning_tele.regelbok.ar_bankrad_mot_agare_eller_narstaende(atta)
    forslag = betalningen(korning_tele, ANDRA, atta)
    stoppas(korning_tele, forslag, "ursprung", repr(ANDRA), repr(atta["id"]), OPPET_40, bankperiod=bankperioden)


def test_en_bankrad_mot_agaren_med_ratt_motpart_och_belopp_stoppas(tmp_path):
    # Vassare än g10: bankrad 26 passar 003 på allt utom att raden också är mot ägaren. Matchningen gör den till ett ärende
    # (regel 8), aldrig en matchning, och flödena bygger bara fakturan. Då får inte heller ett förslag för hand gå igenom.
    korningen = korning_med_banken(Korning(), tmp_path, RAD_26, "26,2025-02-06,2025-02-06,SYNT-TE-761,LEV-TE AGARE-1,"
                                   "-16730.56,")
    sextio = korningen.bankrad(2, 26)
    assert forslagen_for(korningen, PROV_B) == ["F-FAKTURA-" + PROV_B]
    stoppas_av_paret(korningen, betalningen(korningen, PROV_B, sextio), PROV_B, sextio, "kräver mänsklig bedömning")


def test_en_bankrad_som_passar_flera_underlag_stoppas(korning_tvetydig):
    # Matchningen kan inte avgöra vilket underlag raden hör till, så en människa ska se det. För hand går det inte förbi.
    tjugosex = korning_tvetydig.bankrad(2, 26)
    assert forslagen_for(korning_tvetydig, PROV_B) == ["F-FAKTURA-" + PROV_B]
    stoppas_av_paret(korning_tvetydig, betalningen(korning_tvetydig, PROV_B, tjugosex), PROV_B, tjugosex, "tvetydig")


def test_en_bankrad_fore_fakturans_datum_stoppas(tmp_path):
    # Rätt belopp och motpart, men bankrad 84 (2025-02-19) är äldre än fakturan, alltså utanför tidsfönstret. 009 används
    # eftersom testdatan har en planterad dubblett av 003, så att K4 flaggar 003 om dess datum flyttas.
    def senare(data):
        data["datum"] = "2025-02-25"
    korningen = Korning(underlag=underlagsmapp(tmp_path, **{ANDRA: senare}))
    attiofyra = korningen.bankrad(2, 84)
    assert forslagen_for(korningen, ANDRA) == ["F-FAKTURA-" + ANDRA]
    stoppas_av_paret(korningen, betalningen(korningen, ANDRA, attiofyra), ANDRA, attiofyra)


def test_ett_kvitto_utanfor_tidsfonstret_stoppas(tmp_path):
    # Bankrad 85 har rätt belopp och motpart, men är 8 dagar efter kvittot, och fönstret för kvitton är 3 dagar.
    korningen = kvitto_med(tmp_path, 28080, 7020)
    attiofem = korningen.bankrad(2, 85)
    assert -attiofem["belopp_ore"] == underlaget(korningen, KVITTO)["belopp_ore"]
    stoppas_av_paret(korningen, kvittot(korningen, KVITTO, attiofem), KVITTO, attiofem)


def test_en_annan_fakturas_bankrad_stoppas_och_felet_sager_vilken_faktura_den_hor_till(tmp_path):
    # Bankrad 84 är betalningen av 009. Här har 003 samma belopp, så beloppet stämmer, men fakturanumret i raden är 009:s.
    def lika(data):
        nio = json.loads((DATAMAPP / "underlag" / (ANDRA + ".json")).read_text(encoding="utf-8"))
        data["belopp_ore"], data["moms"] = nio["belopp_ore"], nio["moms"]
    korningen = Korning(underlag=underlagsmapp(tmp_path, **{PROV_B: lika}))
    attiofyra = korningen.bankrad(2, 84)
    assert "F-BETALNING-" + ANDRA in forslagen_for(korningen, ANDRA)
    stoppas_av_paret(korningen, betalningen(korningen, PROV_B, attiofyra), PROV_B, attiofyra, repr(ANDRA))


def test_ett_underlag_med_ett_eget_par_kan_inte_anvanda_en_annan_bankrad_med_samma_belopp(tmp_path, tmp_path_factory):
    # Kräver att BÅDE underlaget och bankraden prövas som ett par (mutationsprovet i steg 98 visade att inget annat test ser
    # det). Rad 84 och 85 får samma belopp, med summan och saldot efter rad 85 oförändrade, så att K1 håller. 009 får samma
    # belopp och har sitt riktiga par i rad 84. Förslaget använder rad 85, kortköpet, som har rätt belopp men en annan motpart.
    korningen = korning_med_banken(
        korning_med_009(tmp_path_factory, "samma_belopp", 686970, 82436), tmp_path,
        "84,2025-02-19,2025-02-19,SYNT-TE-762,LEV-TE,-15037.12,220227.34\n"
        "85,2025-02-19,2025-02-18,KORTKOP-20250218,KORTKOP BUTIK-FORBRUKNING,-351.00,219876.34",
        "84,2025-02-19,2025-02-19,SYNT-TE-762,LEV-TE,-7694.06,227570.40\n"
        "85,2025-02-19,2025-02-18,KORTKOP-20250218,KORTKOP BUTIK-FORBRUKNING,-7694.06,219876.34")
    attiofyra, attiofem = korningen.bankrad(2, 84), korningen.bankrad(2, 85)
    assert "F-BETALNING-" + ANDRA in forslagen_for(korningen, ANDRA)
    assert skapa(korningen, betalningen(korningen, ANDRA, attiofyra)).kontroller == ALLA_KONTROLLER
    assert -attiofem["belopp_ore"] == underlaget(korningen, ANDRA)["belopp_ore"]
    stoppas_av_paret(korningen, betalningen(korningen, ANDRA, attiofem), ANDRA, attiofem)


# --- Matchningsresultatet saknas eller är handbyggt ---

def test_gar_matchningen_inte_att_gora_stoppas_betalningen_och_kvittot(korning, monkeypatch):
    # Till exempel fler bankrader än matchningen tar. Inget svar från matchningen betyder inget förslag.
    def gar_inte(*_):
        raise MatchningFel("Matchningen stoppas: för många bankrader.")
    monkeypatch.setattr(konteringsforslag, "matcha_period", gar_inte, raising=False)
    tjugosex, femtio = korning.bankrad(2, 26), korning.bankrad(2, 50)
    stoppas_av_paret(korning, betalningen_for_hand(korning), PROV_B, tjugosex, "för många bankrader")
    stoppas_av_paret(korning, kvittot(korning, KVITTO, femtio), KVITTO, femtio, "för många bankrader")


def test_kontrollen_foljer_svaret_fran_matcha_period(korning, monkeypatch):
    # Ett riktigt par stoppas om matcha_period inte har paret: kontrollen har inget eget svar att falla tillbaka på.
    tom = Matchningsresultat(matchningar=(), arenden=(), oavstamda_underlag=(), kraver_inte_underlag=(), vantande=())
    monkeypatch.setattr(konteringsforslag, "matcha_period", lambda *_: tom, raising=False)
    stoppas_av_paret(korning, betalningen_for_hand(korning), PROV_B, korning.bankrad(2, 26))


def test_kontrollen_fragar_matcha_period_med_samma_perioder_och_regelbok(korning, monkeypatch):
    anrop = []

    def spion(*args):
        anrop.append(args)
        return matcha_period(*args)
    monkeypatch.setattr(konteringsforslag, "matcha_period", spion, raising=False)
    skapa(korning, betalningen_for_hand(korning))
    assert len(anrop) == 1
    assert anrop[0][0] is korning.bankperiod and anrop[0][1] is korning.underlagsperiod
    assert anrop[0][2] is korning.regelbok


def test_utan_perioderna_stoppas_kontrollen_av_paret(korning):
    # Säker riktning: ursprungskontrollen stoppar redan en källa utan period, men kontrollen ska hålla själv.
    kopplingar = {"underlag": [{"id": PROV_B}], "bankrader": [{"id": korning.bankrad(2, 26)["id"], "radnr": 26}]}
    for underlagsperioden, bankperioden in ((None, korning.bankperiod), (korning.underlagsperiod, None)):
        with pytest.raises(KonteringsforslagFel) as fel:
            konteringsforslag._kontrollera_bankradens_par(kopplingar, korning.regelbok, underlagsperioden, bankperioden)
        assert OPPET_40 in str(fel.value) and repr(PROV_B) in str(fel.value)


def test_skydd_utan_bankperioden_eller_underlagsperioden_skapas_inget_forslag(korning):
    # Skydd (grönt också före rättelsen): ursprungskontrollen stoppar det först.
    stoppas(korning, betalningen_for_hand(korning), "ursprung", "fick ingen bankperiod", bankperiod=None)
    stoppas(korning, betalningen_for_hand(korning), "ursprung", "fick ingen underlagsperiod", underlagsperiod=None)


def test_skydd_ett_handbyggt_matchningsresultat_kan_inte_lamnas_in(korning_tele):
    # Skydd (grönt också före rättelsen, eftersom det aldrig har funnits någon väg in). Ett resultat som påstår att r5 är
    # ett par kan inte lämnas in, varken som argument eller i förslaget.
    atta, nio = korning_tele.bankrad(2, 8), underlaget(korning_tele, ANDRA)
    handbyggt = Matchningsresultat(matchningar=({"bankrad": atta, "underlag": nio, "kraver_mansklig_bedomning": False},),
                                   arenden=(), oavstamda_underlag=(), kraver_inte_underlag=(), vantande=())
    forslag = betalningen(korning_tele, ANDRA, atta)
    with pytest.raises(TypeError):
        skapa(korning_tele, forslag, matchning=handbyggt)
    forslag["kopplingar"]["matchning"] = handbyggt
    stoppas(korning_tele, forslag, "indata")
    assert list(inspect.signature(skapa_konteringsforslag).parameters) == [
        "forslag", "regelbok", "kontoplan", "momssatser", "underlagsperiod", "bankperiod", "kassaperiod"]


def test_skydd_en_bankperiod_som_inte_kommer_fran_inlasningen_stoppas(korning):
    # Skydd (grönt också före rättelsen): perioderna kan inte bytas mot något som bara liknar dem (typskyddet).
    class Falsk(Bankperiod):
        pass
    stoppas(korning, betalningen_for_hand(korning), "indata", "bankperioden", bankperiod=Falsk.__new__(Falsk))


# --- Det som ska godtas ---

def test_skydd_flodena_ger_samma_forslag_som_forut(korning):
    # Skydd: 16 fakturor, 6 betalningar och 3 kvitton (granskning 30), och 4 bankavgifter utan underlag.
    former = {"FAKTURA": 0, "BETALNING": 0, "KVITTO": 0, "BANKRAD": 0}
    for forslag in korning.resultat.forslag:
        former[forslag.forslag_id.split("-")[1]] += 1
    assert former == {"FAKTURA": 16, "BETALNING": 6, "KVITTO": 3, "BANKRAD": 4}


def test_skydd_varje_forslag_med_bankrad_i_hela_korningen_har_ett_par_i_matchningen(korning):
    # Matchningen här är flödenas egen (på deras bedömningsdatum), inte den kontrollen gör. Ett förslag med underlag och
    # bankrad ska vara ett par i den, och en bankavgift (flöde e) har inget underlag och ska stå bland raderna som inte
    # kräver underlag. Antalen visar att skyddet inte är tomt.
    par = {(post["underlag"]["id"], post["bankrad"]["id"]) for post in korning.resultat.matchning.matchningar}
    utan_underlag = {post["bankrad"]["id"] for post in korning.resultat.matchning.kraver_inte_underlag}
    med_underlag, bara_bankrad = 0, 0
    for forslag in korning.resultat.forslag:
        for bankrad in forslag.kopplingar["bankrader"]:
            if forslag.kopplingar["underlag"]:
                underlag, = forslag.kopplingar["underlag"]
                assert (underlag["id"], bankrad["id"]) in par, forslag.forslag_id
                assert forslag.kontroller == ALLA_KONTROLLER
                med_underlag += 1
            else:
                assert bankrad["id"] in utan_underlag, forslag.forslag_id
                bara_bankrad += 1
    assert (med_underlag, bara_bankrad) == (9, 4)


def test_skydd_ett_riktigt_par_for_hand_godtas_och_returvardet_ar_oforandrat(korning):
    betalning = skapa(korning, betalningen_for_hand(korning))
    assert betalning.kontroller == ALLA_KONTROLLER
    assert betalning.kopplingar["bankrader"][0]["radnr"] == 26
    kvitto = skapa(korning, kvittot(korning, KVITTO, korning.bankrad(2, 50)))
    assert kvitto.kontroller == ALLA_KONTROLLER


def test_skydd_paren_beror_inte_pa_bedomningsdatumet(korning):
    # Skälet till att kontrollen kan ha ett fast datum och ändå ge samma par som flödena: datumet ändrar bara vilka rader
    # som väntar och vilka som är ärendet "saknat underlag". Prövas från första möjliga dagen till det fasta datumet.
    senaste = max(rad_["transaktionsdag"] for rad_ in korning.bankperiod.rader)
    flodenas = korning.resultat.matchning.matchningar
    # 12 matchningar, fler än de 9 förslagen med bankrad: underlag som K4, K5 eller K8 stoppar får inget förslag.
    assert len(flodenas) == 12
    for datum in (senaste, "2025-03-01", BEDOMNING, "2030-01-01", "9999-12-31"):
        svar = matcha_period(korning.bankperiod, korning.underlagsperiod, korning.regelbok, datum)
        assert svar.matchningar == flodenas, datum


def test_skydd_en_faktura_behover_ingen_matchning(korning, monkeypatch):
    # Fakturan berörs inte: Öppet 40 prövar bara ett förslag med både underlag och bankrad.
    def far_inte_koras(*_):
        raise AssertionError("Matchningen ska inte köras för ett förslag utan par.")
    monkeypatch.setattr(konteringsforslag, "matcha_period", far_inte_koras, raising=False)
    assert skapa(korning, prov_b_003(korning), bankperiod=None).kontroller == ALLA_KONTROLLER


def test_skydd_en_bankavgift_fran_flodet_godtas_igen_med_en_enda_matchning(korning, monkeypatch):
    # Ändrat i steg 100 (Öppet 44, beslut 2 om granskning 30): bankavgiften kör nu matchningen, en gång, för sin form.
    anrop = []

    def spion(*args):
        anrop.append(args)
        return matcha_period(*args)
    monkeypatch.setattr(konteringsforslag, "matcha_period", spion, raising=False)
    avgiften = [forslag for forslag in korning.resultat.forslag if not forslag.kopplingar["underlag"]][0]
    kopplingar = avgiften.kopplingar
    kopplingar["bankrader"] = [{"id": post["id"]} for post in kopplingar["bankrader"]]
    igen = skapa(korning, {"forslag_id": avgiften.forslag_id, "verifikation": avgiften.verifikation,
                           "kopplingar": kopplingar, "motivering": avgiften.motivering})
    assert igen.kontroller == {"K2": "ok", "ursprung": "ok"}
    assert len(anrop) == 1


# --- Kvar efter steget: dokumenterat, inte önskat ---

def test_kvar_en_smalare_underlagsperiod_kan_ge_ett_par_som_hela_perioden_inte_ger(tmp_path_factory, korning_tvetydig):
    # Dokumenterar en gräns, inte ett önskat beteende. Kontrollen matchar mot perioderna den får. Bygger någon förslaget med
    # en riktigt inläst period där det andra underlaget saknas, är paret entydigt i den perioden. Inget i
    # skapa_konteringsforslag vet vad hela perioden är. Se "Beslut som behövs" i PROGRESS.md.
    mapp = lika_kopia_med_flera_kandidater(tmp_path_factory, "smalare")
    (mapp / (ANDRA + ".json")).unlink()
    smalare = las_underlagsperiod(mapp, "2025-01-01", "2025-03-31")
    forslag = betalningen(korning_tvetydig, PROV_B, korning_tvetydig.bankrad(2, 26))
    assert skapa(korning_tvetydig, forslag, underlagsperiod=smalare).kontroller == ALLA_KONTROLLER


# --- Koden ---

def test_koden_anvander_matcha_period_och_ingen_egen_matchning():
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    trad = ast.parse(kod)
    fran_matchningen = [namn.name for nod in ast.walk(trad) if isinstance(nod, ast.ImportFrom)
                        and nod.module == "matcha_bank" for namn in nod.names]
    assert sorted(fran_matchningen) == ["MatchningFel", "matcha_period"]
    # Matchningens egna villkor får inte finnas kopierade här.
    for namn in ("tidsfonster", "transaktionsdag", "fakturanummer", "_kandidater", "_ar_kandidat", "_star_i_raden"):
        anvanda = [nod for nod in ast.walk(trad) if isinstance(nod, ast.Constant) and nod.value == namn]
        anvanda += [nod for nod in ast.walk(trad) if isinstance(nod, ast.Name) and nod.id == namn]
        assert not anvanda, namn

    def funktionen(namn):
        hittad, = [nod for nod in ast.walk(trad) if isinstance(nod, ast.FunctionDef) and nod.name == namn]
        return {nod.func.id for nod in ast.walk(hittad) if isinstance(nod, ast.Call) and isinstance(nod.func, ast.Name)}
    assert "matcha_period" in funktionen("_kontrollera_bankradens_par")
    assert "_kontrollera_bankradens_par" in funktionen("skapa_konteringsforslag")


def test_koden_namner_regeln():
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 40" in kod and "steg 98" in kod and "Hugos beslut 2026-11-04 om granskning 30" in kod
