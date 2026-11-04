"""Tester för steg 100, Öppet 44: ett förslag utan underlag måste ha flöde e:s form, bankavgiften.

Hugos beslut 2026-11-04 om granskning 30, beslut 2 (P2 i granskning 30, proven n1 och n4–n8): förslag utan underlag ska ha
fasta former, samma princip som (b) i steg 97. Allt annat utan underlag stoppas tills dess flöde finns. Byggt i
_kontrollera_forslag_utan_underlag, som skapa_konteringsforslag anropar allra sist, efter K4-kontrollen. Filen heter 32
eftersom uppdraget kom med besluten om granskning 32.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets tillfälliga
mapp. Vilka test som var röda före rättelsen, och varför, står i PROGRESS.md, "Läge 2026-11-04, steg 100 byggt".
"""

import ast
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import konteringsforslag  # noqa: E402
from konteringsforslag import KonteringsforslagFel, skapa_konteringsforslag  # noqa: E402
from las_bank import ladda_bankformat, las_bankfil  # noqa: E402
from las_regelbok import FLODE_BANKAVGIFT, FLODETS_KONTERING  # noqa: E402
from matcha_bank import MatchningFel, Matchningsresultat, matcha_period  # noqa: E402
from test_konteringsfloden import Korning, avgiftsregelns_grans  # noqa: E402
from test_konteringsfloden import regelbok_med as regelbok_for_flodena  # noqa: E402
from test_konteringsforslag import (  # noqa: E402
    TESTBUTIKEN, Kallor, bankavgiften, bankrad, fakturan, forslag, kortinlosen, rad, regelbok_med, regeln, skapa,
    skapa_med_regelboken, stoppas, z_1001,
)

OPPET_44 = "Öppet 44"
AVGIFT = "R-BANK-AVGIFT"
SWISH = "R-BANK-SWISH"
KORTINLOSEN = "R-BANK-KORTINLOSEN"
Z_REGEL = "R-Z-TB-KASSA-1"
# Testbutikens konton: kostnaden för bankens avgifter, bankkontot och leverantörsskulderna.
KOSTNADSKONTOT = "6570"
BANKKONTOT = "1940"
SKULDERNA = "2440"


@pytest.fixture(scope="module")
def kallor():
    return Kallor()


@pytest.fixture(scope="module")
def korning():
    return Korning()


def avgiften_med(kallor, debetkonto, kreditkonto, radnr=117, ore=12500, regel=AVGIFT):
    """Bankrad radnr i januari med bankraden som enda källa på båda raderna, på de här kontona."""
    bank = kallor.bankrad(kallor.januari, radnr)
    return forslag("2025-01-31", "Bankavgift för hand", [
        rad(debetkonto, ore, 0, "lika", bankrad(bank)),
        rad(kreditkonto, 0, ore, "lika", bankrad(bank)),
    ], regel, bankrader=[bank])


def stoppas_av_formen(kallor, data, *texter, **perioder):
    return stoppas(kallor, data, "ursprung", OPPET_44, *texter, **perioder)


def bankperiod_ur(tmp_path, *rader):
    """En bankperiod med de här raderna. Saldona räknas ihop med beloppen i öre: ingående 10 000 kr."""
    fil = tmp_path / "bank.csv"
    fil.write_text("\n".join(["Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo", *rader])
                   + "\n", encoding="utf-8")
    return las_bankfil(fil, ladda_bankformat(TESTBUTIKEN / "bankformat.json"), 1000000, 980000)


def med_bankrad_i_z_rapporten(bank, ore=10000):
    """Z 1001 i sin riktiga kontering, plus en bankrad på två rader. Regeln gäller Z-rapporter, så punkt 8 prövar inte bankraden."""
    data = z_1001()
    data["verifikation"]["rader"] += [rad(SKULDERNA, ore, 0, "lika", bankrad(bank)),
                                      rad(BANKKONTOT, 0, ore, "lika", bankrad(bank))]
    data["kopplingar"]["bankrader"] = [{"id": bank}]
    return data


# --- Proven n1 och n4–n8 i granskning 30, P2 ---

def test_n1_bankavgiften_pa_leverantorsskulderna_stoppas(kallor):
    fel = stoppas_av_formen(kallor, avgiften_med(kallor, SKULDERNA, BANKKONTOT))
    assert "konto " + SKULDERNA in fel and KOSTNADSKONTOT in fel


def test_n4_swish_in_stoppas(kallor):
    # Pengar in: 1940 i debet och 2440 i kredit. Flöde d finns inte än. Bankrad 1 är 323 kr.
    bank = kallor.bankrad(kallor.januari, 1)
    stoppas_av_formen(kallor, forslag("2025-01-02", "Swish in", [
        rad(BANKKONTOT, 32300, 0, "lika", bankrad(bank)),
        rad(SKULDERNA, 0, 32300, "lika", bankrad(bank)),
    ], SWISH, bankrader=[bank]), "pengar in")


def test_n5_kortinlosen_som_minskad_avgift_stoppas(kallor):
    # Pengar in: en insättning med 1940 i debet och 6570 i kredit, alltså som en minskad avgift.
    bank = kallor.bankrad(kallor.januari, 3)
    stoppas_av_formen(kallor, forslag("2025-01-03", "Kortinlösen", [
        rad(BANKKONTOT, 406562, 0, "lika", bankrad(bank)),
        rad(KOSTNADSKONTOT, 0, 406562, "lika", bankrad(bank)),
    ], KORTINLOSEN, bankrader=[bank]), "pengar in")


def test_n6_bankavgift_over_regelns_grans_stoppas(kallor, tmp_path):
    # Bankrad 117 är 125 kr, och regeln i kopian säger högst 100 kr. Matchningsformatets gräns är kvar på 250 kr.
    def lagre_grans(data):
        regeln(data, AVGIFT)["villkor"]["hogst_belopp_ore"] = 10000
    regelbok, summa = regelbok_med(kallor, tmp_path, lagre_grans)
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_med_regelboken(kallor, bankavgiften(kallor), regelbok, summa)
    assert OPPET_44 in str(fel.value) and "gräns" in str(fel.value) and fel.value.kontroll == "ursprung"


def test_n7_bankavgift_pa_en_regel_utan_flode_stoppas(kallor, tmp_path):
    def utan_flode(data):
        del regeln(data, AVGIFT)["flode"]
    regelbok, summa = regelbok_med(kallor, tmp_path, utan_flode)
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_med_regelboken(kallor, bankavgiften(kallor), regelbok, summa)
    assert OPPET_44 in str(fel.value) and "'flode'" in str(fel.value) and fel.value.kontroll == "ursprung"


def test_n8_z_rapporten_med_swish_pa_leverantorsskulderna_stoppas(kallor):
    data = z_1001()
    data["verifikation"]["rader"][2]["konto"] = SKULDERNA
    stoppas_av_formen(kallor, data, "Z-rapport")


# --- Två bankrader ---

def test_bankavgift_med_tva_bankrader_pa_en_rad_per_sida_stoppas(kallor):
    forsta, andra = kallor.bankrad(kallor.januari, 117), kallor.bankrad(kallor.januari, 118)
    stoppas_av_formen(kallor, forslag("2025-01-31", "Två avgifter", [
        rad(KOSTNADSKONTOT, 32400, 0, "summa", bankrad(forsta), bankrad(andra)),
        rad(BANKKONTOT, 0, 32400, "summa", bankrad(forsta), bankrad(andra)),
    ], AVGIFT, bankrader=[forsta, andra]), "2 bankrader")


def test_bankavgift_med_tva_bankrader_pa_fyra_rader_stoppas(kallor):
    forsta, andra = kallor.bankrad(kallor.januari, 117), kallor.bankrad(kallor.januari, 118)
    stoppas_av_formen(kallor, forslag("2025-01-31", "Två avgifter", [
        rad(KOSTNADSKONTOT, 12500, 0, "lika", bankrad(forsta)),
        rad(BANKKONTOT, 0, 12500, "lika", bankrad(forsta)),
        rad(KOSTNADSKONTOT, 19900, 0, "lika", bankrad(andra)),
        rad(BANKKONTOT, 0, 19900, "lika", bankrad(andra)),
    ], AVGIFT, bankrader=[forsta, andra]), "2 bankrader")


# --- Bankraden står inte bland raderna som inte kräver underlag ---

def test_en_bankrad_som_matchningen_har_parat_med_ett_underlag_stoppas(kallor):
    # Bankrad 26 i februari är betalningen av 003. Bakad in i Z-rapportens förslag gick den igenom före rättelsen.
    stoppas_av_formen(kallor, med_bankrad_i_z_rapporten(kallor.bankrad(kallor.februari, 26), 1673056))


def test_skydd_en_bankrad_som_matchningen_har_parat_stoppas_ocksa_ensam(kallor):
    # Skydd (grönt också före rättelsen): under bankregeln stoppar ursprunget punkt 8 den först.
    bank = kallor.bankrad(kallor.februari, 26)
    stoppas(kallor, forslag("2025-02-06", "Betalning som avgift", [
        rad(KOSTNADSKONTOT, 1673056, 0, "lika", bankrad(bank)),
        rad(BANKKONTOT, 0, 1673056, "lika", bankrad(bank)),
    ], AVGIFT, bankrader=[bank]), "ursprung", "inte passar någon regel")


def test_kontrollen_foljer_matchningen_nar_den_har_parat_raden(kallor, monkeypatch):
    # Matchningen ger aldrig en rad med en regel för bankrader utan underlag ett par (matcha_bank.py), så det här går bara
    # att nå med ett påhittat svar. Kontrollen ska följa svaret: inget eget svar att falla tillbaka på.
    rad_117 = kallor.januari.rader[116]
    parat = Matchningsresultat(matchningar=({"bankrad": rad_117, "underlag": kallor.underlagsperiod.underlag[0],
                                             "kraver_mansklig_bedomning": False},),
                               arenden=(), oavstamda_underlag=(), kraver_inte_underlag=(), vantande=())
    monkeypatch.setattr(konteringsforslag, "matcha_period", lambda *_: parat, raising=False)
    stoppas_av_formen(kallor, bankavgiften(kallor), "parat ihop")


def test_en_bankrad_mot_agaren_stoppas(kallor, tmp_path):
    # Raden har ägaren i texten. Bakad in i Z-rapportens förslag gick den igenom före rättelsen.
    bankperiod = bankperiod_ur(tmp_path, "1,2025-04-01,2025-04-01,AVG-1,BANK AVGIFT AGARE-1/APRIL,-100.00,9900.00",
                               "2,2025-04-02,2025-04-02,AVG-2,BANK AVGIFT APRIL,-100.00,9800.00")
    stoppas_av_formen(kallor, med_bankrad_i_z_rapporten(bankperiod.rader[0]["id"]), bankperiod=bankperiod)


def test_skydd_en_bankrad_mot_agaren_stoppas_ocksa_ensam(kallor, tmp_path):
    # Skydd (grönt också före rättelsen): ursprunget punkt 8, som test_n3_bankavgift_mot_agaren_stoppas.
    bankperiod = bankperiod_ur(tmp_path, "1,2025-04-01,2025-04-01,AVG-1,BANK AVGIFT AGARE-1/APRIL,-100.00,9900.00",
                               "2,2025-04-02,2025-04-02,AVG-2,BANK AVGIFT APRIL,-100.00,9800.00")
    bank = bankperiod.rader[0]["id"]
    stoppas(kallor, forslag("2025-04-01", "Bankavgift", [
        rad(KOSTNADSKONTOT, 10000, 0, "lika", bankrad(bank)),
        rad(BANKKONTOT, 0, 10000, "lika", bankrad(bank)),
    ], AVGIFT, bankrader=[bank]), "ursprung", "ägare eller närstående", bankperiod=bankperiod)


def test_en_bankrad_over_matchningens_grans_stoppas(kallor, tmp_path):
    # 300 kr med en avgifts text. Matchningen gör raden till ärendet "över gräns", och den når aldrig flöde e.
    bankperiod = bankperiod_ur(tmp_path, "1,2025-04-01,2025-04-01,AVG-1,BANK AVGIFT APRIL,-300.00,9700.00",
                               "2,2025-04-02,2025-04-02,INS-1,KONTANTINSATTNING,100.00,9800.00")
    bank = bankperiod.rader[0]["id"]
    stoppas_av_formen(kallor, forslag("2025-04-01", "Bankavgift", [
        rad(KOSTNADSKONTOT, 30000, 0, "lika", bankrad(bank)),
        rad(BANKKONTOT, 0, 30000, "lika", bankrad(bank)),
    ], AVGIFT, bankrader=[bank]), "över gräns", bankperiod=bankperiod)


# --- Raderna ---

def test_bada_raderna_pa_kostnadskontot_stoppas(kallor):
    fel = stoppas_av_formen(kallor, avgiften_med(kallor, KOSTNADSKONTOT, KOSTNADSKONTOT))
    assert "bankkontot" in fel and "konto " + KOSTNADSKONTOT in fel


def test_skydd_bankkontot_i_debet_for_pengar_ut_stoppas(kallor):
    # Skydd (grönt också före rättelsen): fel sida på bankkontot stoppas av ursprunget punkt 6.
    stoppas(kallor, avgiften_med(kallor, BANKKONTOT, KOSTNADSKONTOT), "ursprung", "pengar")


# --- Z-rapporter och kortinlösen: stoppas tills deras flöden finns (uppgift 5) ---

@pytest.mark.parametrize("bygg", [lambda kallor: z_1001(), kortinlosen], ids=["z_1001", "kortinlosen"])
def test_z_rapporten_och_kortinlosen_i_design_4_stoppas_tills_flodena_finns(kallor, bygg):
    stoppas_av_formen(kallor, bygg(kallor), "Z-rapport")


# --- Det som ska godtas ---

def test_skydd_flodena_a_b_och_e_ger_samma_forslag_som_forut(korning):
    former = {"FAKTURA": 0, "BETALNING": 0, "KVITTO": 0, "BANKRAD": 0}
    for ett in korning.resultat.forslag:
        former[ett.forslag_id.split("-")[1]] += 1
    assert former == {"FAKTURA": 16, "BETALNING": 6, "KVITTO": 3, "BANKRAD": 4}


def test_skydd_varje_forslag_utan_underlag_i_hela_korningen_har_flode_es_form(korning):
    # Räknat för sig här, utan koden i konteringsforslag.py. Antalet visar att skyddet inte är tomt.
    undantagna = {post["bankrad"]["id"]: post["regel"] for post in korning.resultat.matchning.kraver_inte_underlag}
    bankens = {post["id"]: post for post in korning.bankperiod.rader}
    antal = 0
    for ett in korning.resultat.forslag:
        if ett.kopplingar["underlag"]:
            continue
        assert ett.kopplingar["z_rapporter"] == []
        post, = ett.kopplingar["bankrader"]
        bank = bankens[post["id"]]
        assert bank["belopp_ore"] < 0
        datum = ett.verifikation["datum"]
        regel = korning.regelbok.regel_for_bankrad(undantagna[post["id"]], datum)
        assert regel["flode"] == FLODE_BANKAVGIFT and regel["id"] == ett.kopplingar["regel"]["id"]
        belopp = -bank["belopp_ore"]
        assert belopp <= regel["villkor"]["hogst_belopp_ore"]
        kalla = {"kalla": "bankrad", "id": post["id"], "falt": "belopp_ore"}
        assert ett.verifikation["rader"] == [
            rad(regel["kontering"]["kostnad"], belopp, 0, "lika", kalla),
            rad(korning.kontoplan.rollens_konto("bank", datum), 0, belopp, "lika", kalla)]
        assert ett.kontroller == {"K2": "ok", "ursprung": "ok"}
        antal += 1
    assert antal == 4


def test_skydd_bankavgiften_for_hand_godtas_och_returvardet_ar_oforandrat(kallor):
    resultat = skapa(kallor, bankavgiften(kallor))
    assert resultat.kontroller == {"K2": "ok", "ursprung": "ok"}
    assert resultat.kopplingar["bankrader"][0]["radnr"] == 117 and resultat.kopplingar["regel"]["id"] == AVGIFT


def test_skydd_bankavgiften_godtas_med_en_bankperiod_for_en_manad(kallor):
    assert skapa(kallor, bankavgiften(kallor), bankperiod=kallor.januari)


def test_skydd_raderna_far_sta_i_vilken_ordning_som_helst(kallor):
    data = bankavgiften(kallor)
    data["verifikation"]["rader"].reverse()
    assert skapa(kallor, data)


def test_skydd_avgift_exakt_pa_regelns_grans_godtas_ocksa_i_flodet(tmp_path):
    korningen = Korning(regelbok=regelbok_for_flodena(tmp_path, avgiftsregelns_grans(19900)))
    assert len([ett for ett in korningen.resultat.forslag if not ett.kopplingar["underlag"]]) == 4


def test_skydd_flodet_med_bokforingsdagen_som_datum_stoppas_inte(tmp_path):
    def andring(regelbok):
        regelbok["bokforing"]["verifikationsdatum"]["bankrad"] = "bokforingsdag"
    korningen = Korning(regelbok=regelbok_for_flodena(tmp_path, andring))
    assert len([ett for ett in korningen.resultat.forslag if not ett.kopplingar["underlag"]]) == 4


# --- Matchningen: samma anrop som Öppet 40, och aldrig två för samma förslag ---

def spion(monkeypatch):
    anrop = []

    def matcha(*args):
        anrop.append(args)
        return matcha_period(*args)
    monkeypatch.setattr(konteringsforslag, "matcha_period", matcha, raising=False)
    return anrop


def test_bankavgiften_kor_matchningen_en_gang_med_samma_perioder_regelbok_och_datum(kallor, monkeypatch):
    anrop = spion(monkeypatch)
    skapa(kallor, bankavgiften(kallor))
    assert len(anrop) == 1
    assert anrop[0][0] is kallor.bankperiod and anrop[0][1] is kallor.underlagsperiod and anrop[0][2] is kallor.regelbok
    assert anrop[0][3] == konteringsforslag._SENT_BEDOMNINGSDATUM


def test_skydd_fakturan_kor_ingen_matchning(kallor, monkeypatch):
    anrop = spion(monkeypatch)
    skapa(kallor, fakturan())
    assert anrop == []


def test_gar_matchningen_inte_att_gora_stoppas_bankavgiften(kallor, monkeypatch):
    def gar_inte(*_):
        raise MatchningFel("Matchningen stoppas: för många bankrader.")
    monkeypatch.setattr(konteringsforslag, "matcha_period", gar_inte, raising=False)
    stoppas_av_formen(kallor, bankavgiften(kallor), "för många bankrader")


def test_utan_underlagsperioden_stoppas_bankavgiften(kallor):
    # Matchningen behöver båda perioderna. Ändrat i steg 100: förut fick perioden vara None för ett förslag utan underlag.
    stoppas_av_formen(kallor, bankavgiften(kallor), "Underlagsperiod", underlagsperiod=None)


# --- Grenar som tidigare kontroller alltid hinner före. Prövas direkt, så att kontrollen håller själv ---

def direkt(kallor, data, kopplingar=None):
    """Kontrollen för sig, utan K2 och ursprunget före."""
    bank = data["kopplingar"]["bankrader"]
    konteringsforslag._kontrollera_forslag_utan_underlag(
        kopplingar or {"underlag": [], "z_rapporter": [], "bankrader": bank, "regel": data["kopplingar"]["regel"]},
        data["verifikation"], kallor.regelbok, kallor.kontoplan,
        konteringsforslag._kallorna(kallor.underlagsperiod, kallor.bankperiod, kallor.kassaperiod),
        kallor.underlagsperiod, kallor.bankperiod)


def test_skydd_direkt_den_riktiga_bankavgiften_godtas(kallor):
    direkt(kallor, bankavgiften(kallor))


def test_en_annan_regel_i_kopplingarna_stoppas_av_kontrollen_sjalv(kallor):
    # Ursprunget punkt 8 stoppar det först i skapa_konteringsforslag.
    data = bankavgiften(kallor)
    data["kopplingar"]["regel"]["id"] = SWISH
    with pytest.raises(KonteringsforslagFel) as fel:
        direkt(kallor, data)
    assert OPPET_44 in str(fel.value) and repr(SWISH) in str(fel.value) and repr(AVGIFT) in str(fel.value)


def test_ingen_regel_pa_datumet_stoppas_av_kontrollen_sjalv(kallor):
    # Ursprunget punkt 8 stoppar det först i skapa_konteringsforslag. Regeln gäller från 2025-01-01.
    data = bankavgiften(kallor)
    data["verifikation"]["datum"] = "2024-12-31"
    with pytest.raises(KonteringsforslagFel) as fel:
        direkt(kallor, data)
    assert OPPET_44 in str(fel.value) and "2024-12-31" in str(fel.value)


def test_fler_an_tva_rader_stoppas_av_kontrollen_sjalv(kallor):
    # Täckningen stoppar samma rad två gånger först i skapa_konteringsforslag. Exakt två rader står i formen.
    data = bankavgiften(kallor)
    data["verifikation"]["rader"] += bankavgiften(kallor)["verifikation"]["rader"]
    with pytest.raises(KonteringsforslagFel) as fel:
        direkt(kallor, data)
    assert OPPET_44 in str(fel.value) and "exakt två rader" in str(fel.value)


# --- Kvar efter steget: dokumenterat, inte önskat ---

def test_kvar_verifikationens_datum_ingar_inte_i_formen(kallor):
    # Dokumenterar en gräns, som för formerna i steg 97 (Öppet 41). Så länge regeln gäller på datumet godtas ett annat datum
    # än bankradens. Formen i uppdraget nämner inget datum.
    data = bankavgiften(kallor)
    data["verifikation"]["datum"] = "2025-02-15"
    assert skapa(kallor, data)


# --- Koden ---

def kodens_trad():
    return ast.parse((AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8"))


def test_koden_anropar_kontrollen_sist_i_skapa_konteringsforslag():
    trad = kodens_trad()
    skapa_, = [nod for nod in ast.walk(trad) if isinstance(nod, ast.FunctionDef) and nod.name == "skapa_konteringsforslag"]
    rader = {nod.func.id: nod.lineno for nod in ast.walk(skapa_) if isinstance(nod, ast.Call)
             and isinstance(nod.func, ast.Name)}
    assert rader["_kontrollera_k4"] < rader["_kontrollera_forslag_utan_underlag"] < rader["Konteringsforslag"]


def test_koden_importerar_inte_floden_och_har_inget_foretagsspecifikt():
    trad = kodens_trad()
    moduler = {nod.module for nod in ast.walk(trad) if isinstance(nod, ast.ImportFrom)}
    moduler |= {namn.name for nod in ast.walk(trad) if isinstance(nod, ast.Import) for namn in nod.names}
    assert "konteringsfloden" not in moduler
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    for namn in (KOSTNADSKONTOT, BANKKONTOT, SKULDERNA, AVGIFT, SWISH, "bankens-avgifter"):
        assert namn not in kod, namn


def test_kostnadens_nyckel_ar_regelbokens_for_flodet():
    assert konteringsforslag._KOSTNAD in FLODETS_KONTERING[FLODE_BANKAVGIFT]


def test_koden_namner_regeln_for_nya_floden():
    doc = ast.get_docstring(kodens_trad())
    assert "Öppet 44" in doc and "steg 100" in doc
    # Regel framåt: varje nytt flöde byggs med sin form i samma steg (beslut 2 om granskning 30).
    assert "uppgift 5" in doc and "samma steg" in doc and "Z-rapporter" in doc


def test_skydd_parametrarna_ar_oforandrade():
    # Inget matchningsresultat eller annat kan lämnas in vid sidan av förslaget.
    assert skapa_konteringsforslag.__code__.co_varnames[:7] == (
        "forslag", "regelbok", "kontoplan", "momssatser", "underlagsperiod", "bankperiod", "kassaperiod")
