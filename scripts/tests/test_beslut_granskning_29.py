"""Tester för Hugos beslut 2026-11-04 om granskning 29: (b), flödenas former rakt av (steg 97, Öppet 39).

Beslut 1: ett förslag med underlag måste ha exakt en av flödenas tre former, fakturan, betalningen eller kvittot. Allt
annat stoppas, också b2 och två betalningar i samma förslag. Det som flödena inte bygger stoppas och läggs till
uttryckligen om det behövs, som vaktens kommandolista. Byggt i _kontrollera_flodets_form, som anropas sist i
_kontrollera_underlagen, efter Öppet 36.

Formerna, så som flödena bygger dem (konteringsfloden.py, _kostnad_och_moms, _leverantorsfaktura och _kvitto):

- Fakturan (leverantorsfaktura, ett underlag, inga bankrader): kostnaden och momsen per momsrad i debet, och
  leverantörsskulderna i kredit med 'belopp_ore'. Inga andra rader.
- Betalningen (leverantorsfaktura, ett underlag, en bankrad): exakt två rader, leverantörsskulderna i debet med
  'belopp_ore' och bankkontot i kredit med bankraden som enda källa.
- Kvittot (kvitto, ett underlag, en bankrad): kostnaden och momsen i debet, och bankkontot i kredit med bankraden som
  enda källa. Inga andra rader.
- En rad med beloppet 0 tas inte med, varken för kostnaden eller för momsen, som i flödena och K2 (Hugos svar i chatten
  2026-11-04: följ koden). Raderna får stå i vilken ordning som helst, eftersom ordningen inte ändrar konteringen.

Förslag utan underlag (bankavgiften i flöde e) berörs inte.

Granskarens prov ur granskning 29 (P1, P3 och P4) stoppas av formen. r5 (P2, Öppet 40) har flöde a:s form och stoppas
sedan steg 98 av kontrollen att bankraden hör till underlaget (beslut 2, test_beslut_granskning_30.py). P5 (Öppet 41) rör
datumet och ingår inte (beslut 4).

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot koden i c9a6cee (före rättelsen): 19 av 25 här, och de 6 gröna är skydd eller
dokumenterar r5. Dessutom 3 omgjorda test i test_beslut_granskning_26.py och 28, se PROGRESS.md.
"""

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import konteringsforslag  # noqa: E402
from konteringsforslag import KonteringsforslagFel, kontrollera_underlag  # noqa: E402
from test_konteringsfloden import DATAMAPP, Korning, underlagsmapp  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_25 import ALLA_KONTROLLER, PROV_A, PROV_B  # noqa: E402
from test_beslut_granskning_26 import (  # noqa: E402
    INGAENDE_MOMS, LEVERANTORSSKULDER, kalla, momsraden, prov_b_003, rad, roll, underlaget,
)
from test_beslut_granskning_27 import ANDRA, betalningen_for_hand, korning_lika  # noqa: E402, F401
from test_beslut_granskning_28 import (  # noqa: E402
    BANK, bankkalla, forslag_b2, forslag_med, forslag_tva_betalningar,
)

KVITTO = "SYNT-U-2025-015"
OPPET_39 = "Öppet 39"


@pytest.fixture(scope="module")
def korning():
    return Korning()


def korning_med_009(tmp_path_factory, namn, underlag_ore, moms_ore):
    """En kopia av underlagen där 009 har en momsrad med 12 % och de här beloppen. Datum och nummer är 009:s egna."""
    mapp = tmp_path_factory.mktemp(namn) / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    sokvag = mapp / (ANDRA + ".json")
    nio = json.loads(sokvag.read_text(encoding="utf-8"))
    nio["belopp_ore"] = underlag_ore + moms_ore
    nio["moms"] = [{"momssats": 12, "underlag_ore": underlag_ore, "moms_ore": moms_ore}]
    sokvag.write_text(json.dumps(nio, ensure_ascii=False, indent=2), encoding="utf-8")
    return Korning(underlag=mapp)


@pytest.fixture(scope="module")
def korning_summa(tmp_path_factory):
    """Granskarens r3: 009 har 31 767,68 kr, som är bankrad 26 och 84 i februari tillsammans."""
    return korning_med_009(tmp_path_factory, "r3", 2836400, 340368)


@pytest.fixture(scope="module")
def korning_tele(tmp_path_factory):
    """Granskarens r5: 009 har 748,75 kr, samma belopp som bankrad 8 i februari, som är betalningen till LEV-TELE."""
    return korning_med_009(tmp_path_factory, "r5", 66852, 8023)


def fakturans_rader(korning):
    return prov_b_003(korning)["verifikation"]["rader"]


def betalningens_rader(korning):
    return betalningen_for_hand(korning)["verifikation"]["rader"]


def baklanges(korning, id_=PROV_B):
    """Fakturan baklänges: beloppet i debet på leverantörsskulderna, kostnaden och momsen i kredit."""
    underlag = underlaget(korning, id_)
    momsrad = momsraden(underlag, 12)
    return [rad(roll(korning, LEVERANTORSSKULDER), underlag["belopp_ore"], 0, "lika", kalla(id_, "belopp_ore")),
            rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(id_, "underlag_ore", 12)),
            rad(roll(korning, INGAENDE_MOMS), 0, momsrad["moms_ore"], "lika", kalla(id_, "moms_ore", 12))]


def bankraden_pa_kostnadskontot(korning, bankrad):
    """Bankraden i debet på kostnadskontot och i kredit på bankkontot (pengar ut)."""
    belopp = -bankrad["belopp_ore"]
    return [rad("4010", belopp, 0, "lika", bankkalla(bankrad)),
            rad(roll(korning, BANK), 0, belopp, "lika", bankkalla(bankrad))]


def kvittots_delar(korning):
    """Kvittot 015:s rader för kostnad och moms, och dess bankrad, ur flödets eget förslag."""
    forslaget, = korning.forslag_for(KVITTO)
    id_ = forslaget.kopplingar["bankrader"][0]["id"]
    bankrad, = [post for post in korning.bankperiod.rader if post["id"] == id_]
    rader = [{nyckel: varde for nyckel, varde in post.items()} for post in forslaget.verifikation["rader"]]
    return [post for post in rader if post["debet_ore"] > 0], bankrad, forslaget.verifikation["datum"]


# --- P1: en bankrad som källa på kostnadskontot (Öppet 39) ---

def test_p1_r16_hela_beloppet_med_moms_pa_kostnadskontot_ur_en_bankrad_stoppas(korning):
    # r16: 4010 debet med bankrad 26 som källa, 2440 kredit 003:s 'belopp_ore'. Netto: 1 792,56 kr ingående moms
    # försvinner in i kostnaden. Ett underlag med en bankrad ska ha betalningens form.
    tre, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    text = stoppas(korning, forslag_med(korning, PROV_B, [
        rad("4010", tre["belopp_ore"], 0, "lika", bankkalla(bankraden)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, tre["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "r16", bankraden["transaktionsdag"], [PROV_B], [bankraden]),
        "ursprung", "'" + PROV_B + "'", "formen betalningen", "rad 1 (konto 4010)", OPPET_39)
    assert "Öppet 36" not in text


def test_p1_r6_fakturan_baklanges_med_en_egen_bankkontorad_stoppas(korning):
    # r6: h1 tillbaka. Raden med beloppet i debet har sin egen bankkontorad, så Öppet 35 och 36 ser inget.
    bankraden = korning.bankrad(2, 26)
    stoppas(korning, forslag_med(korning, PROV_B, baklanges(korning) + bankraden_pa_kostnadskontot(korning, bankraden),
                                 "r6", bankraden["transaktionsdag"], [PROV_B], [bankraden]),
            "ursprung", "formen betalningen", "rad 2 (konto 4010)", "rad 3", OPPET_39)


def test_p1_r7_en_teleraknings_bankrad_pa_kostnadskontot_bredvid_betalningen_stoppas(korning):
    # r7: 003:s riktiga betalning plus teleräkningens bankrad (bankrad 8 i februari) på 4010. Två bankrader.
    tjugosex, atta = korning.bankrad(2, 26), korning.bankrad(2, 8)
    stoppas(korning, forslag_med(korning, PROV_B,
                                 betalningens_rader(korning) + bankraden_pa_kostnadskontot(korning, atta),
                                 "r7", tjugosex["transaktionsdag"], [PROV_B], [tjugosex, atta]),
            "ursprung", "2 bankrader", OPPET_39)


def test_p1_r8_fakturan_med_en_annan_bankrad_pa_kostnadskontot_stoppas(korning):
    # r8: 003:s riktiga faktura plus samma två rader med bankrad 8.
    atta = korning.bankrad(2, 8)
    stoppas(korning, forslag_med(korning, PROV_B,
                                 fakturans_rader(korning) + bankraden_pa_kostnadskontot(korning, atta),
                                 "r8", atta["transaktionsdag"], [PROV_B], [atta]),
            "ursprung", "formen betalningen", OPPET_39)


def test_p1_r9_pengar_in_som_minskad_kostnad_bredvid_betalningen_stoppas(korning):
    # r9: 003:s riktiga betalning plus 1940 debet och 4010 kredit med bankrad 1 i januari (Swish in, 323,00 kr).
    tjugosex, ett = korning.bankrad(2, 26), korning.bankrad(1, 1)
    assert ett["belopp_ore"] > 0
    stoppas(korning, forslag_med(korning, PROV_B, betalningens_rader(korning) + [
        rad(roll(korning, BANK), ett["belopp_ore"], 0, "lika", bankkalla(ett)),
        rad("4010", 0, ett["belopp_ore"], "lika", bankkalla(ett)),
    ], "r9", tjugosex["transaktionsdag"], [PROV_B], [tjugosex, ett]), "ursprung", "2 bankrader", OPPET_39)


# --- P3: "en bankrad" gäller ordagrant (beslut 3) ---

def test_p3_r3_en_betalning_ur_tva_bankrader_stoppas(korning_summa):
    # r3: 2440 debet 009 'belopp_ore', 1940 kredit med 'summa' av bankrad 26 och 84. Nettot är en riktig betalning, men
    # "en bankrad" gäller ordagrant. Delbetalningar läggs till som en egen form senare, om ett riktigt företag behöver
    # det (beslut 3). Samlingsbetalningar är en egen punkt under Öppet (beslut 7).
    nio = underlaget(korning_summa, ANDRA)
    tjugosex, attiofyra = korning_summa.bankrad(2, 26), korning_summa.bankrad(2, 84)
    assert nio["belopp_ore"] == -tjugosex["belopp_ore"] - attiofyra["belopp_ore"]
    stoppas(korning_summa, forslag_med(korning_summa, ANDRA, [
        rad(roll(korning_summa, LEVERANTORSSKULDER), nio["belopp_ore"], 0, "lika", kalla(ANDRA, "belopp_ore")),
        rad(roll(korning_summa, BANK), 0, nio["belopp_ore"], "summa", bankkalla(tjugosex), bankkalla(attiofyra)),
    ], "r3", attiofyra["transaktionsdag"], [ANDRA], [tjugosex, attiofyra]),
        "ursprung", "2 bankrader", OPPET_39)


# --- P4: fakturan baklänges ihop med en annan fakturas delar ---

def test_p4_r11_fakturan_baklanges_ihop_med_en_annan_fakturas_delar_stoppas(korning_lika):
    # r11, i kopian där 009 har 003:s belopp: 003 baklänges, 009:s kostnad och moms i debet och bankrad 26 i kredit.
    nio, bankraden = underlaget(korning_lika, ANDRA), korning_lika.bankrad(2, 26)
    momsrad = momsraden(nio, 12)
    stoppas(korning_lika, forslag_med(korning_lika, PROV_B, baklanges(korning_lika) + [
        rad("4010", momsrad["underlag_ore"], 0, "lika", kalla(ANDRA, "underlag_ore", 12)),
        rad(roll(korning_lika, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(ANDRA, "moms_ore", 12)),
        rad(roll(korning_lika, BANK), 0, nio["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "r11", bankraden["transaktionsdag"], [PROV_B, ANDRA], [bankraden]), "ursprung", "2 underlag", OPPET_39)


# --- Beslut 1 och 6: b2 och två betalningar i samma förslag stoppas ---

def test_b2_stoppas(korning_lika):
    # Beslutet att godta b2 (granskning 28) är ersatt (beslut 6). Öppet 38 står kvar: säger konsulten ja kan formen
    # "faktura + annan fakturas betalning" läggas till uttryckligen.
    stoppas(korning_lika, forslag_b2(korning_lika), "ursprung", "2 underlag", OPPET_39)


def test_tva_betalningar_i_samma_forslag_stoppas(korning):
    stoppas(korning, forslag_tva_betalningar(korning), "ursprung", "2 underlag", OPPET_39)


def test_tva_fakturor_i_samma_forslag_stoppas(korning):
    # Två kompletta fakturor i ett förslag: varje faktura har rätt rader, men formen är ett underlag.
    tre, nio = underlaget(korning, PROV_B), underlaget(korning, ANDRA)
    tolv = momsraden(nio, 12)
    stoppas(korning, forslag_med(korning, PROV_B, fakturans_rader(korning) + [
        rad("4010", tolv["underlag_ore"], 0, "lika", kalla(ANDRA, "underlag_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), tolv["moms_ore"], 0, "lika", kalla(ANDRA, "moms_ore", 12)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, nio["belopp_ore"], "lika", kalla(ANDRA, "belopp_ore")),
    ], "Två fakturor", tre["datum"], [PROV_B, ANDRA], []), "ursprung", "2 underlag", OPPET_39)


# --- Fel form för typen av underlag ---

def test_en_faktura_med_en_bankrad_stoppas(korning):
    # Fakturans tre rader, och betalningen med bankraden som källa också på leverantörsskulderna. Beloppet står en gång,
    # och Öppet 36 prövar bara rader med 'belopp_ore' i debet. En faktura med en bankrad har bara betalningens form.
    tre, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    stoppas(korning, forslag_med(korning, PROV_B, fakturans_rader(korning) + [
        rad(roll(korning, LEVERANTORSSKULDER), tre["belopp_ore"], 0, "lika", bankkalla(bankraden)),
        rad(roll(korning, BANK), 0, tre["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "Faktura med bankrad", bankraden["transaktionsdag"], [PROV_B], [bankraden]),
        "ursprung", "formen betalningen", OPPET_39)


def test_skydd_en_bankrad_bara_i_kopplingarna_stoppas_redan_av_punkt_4(korning):
    # Skydd (grönt också före rättelsen): fakturan med en bankrad i kopplingarna som ingen rad använder.
    bankraden = korning.bankrad(2, 26)
    stoppas(korning, forslag_med(korning, PROV_B, fakturans_rader(korning), "Bankrad utan rad", "2025-01-07",
                                 [PROV_B], [bankraden]), "ursprung", "ingen rad använder det")


def test_fakturans_form_pa_ett_kvitto_stoppas_och_ett_kvitto_utan_bankrad_stoppas(korning):
    # Ett kvitto utan bankrad går bara ihop med fakturans form (kredit på leverantörsskulderna), så "fakturaform på ett
    # kvitto" och "kvitto utan bankrad" är samma förslag. Ett kvitto väntar på sin bankrad (flöde b).
    delar, _, datum = kvittots_delar(korning)
    kvitto = underlaget(korning, KVITTO)
    stoppas(korning, forslag_med(korning, KVITTO, delar + [
        rad(roll(korning, LEVERANTORSSKULDER), 0, kvitto["belopp_ore"], "lika", kalla(KVITTO, "belopp_ore")),
    ], "Kvitto som faktura", datum, [KVITTO], []), "ursprung", "'" + KVITTO + "'", "kvitto", "ingen bankrad", OPPET_39)


def test_betalningens_form_pa_ett_kvitto_stoppas(korning):
    _, bankraden, datum = kvittots_delar(korning)
    kvitto = underlaget(korning, KVITTO)
    stoppas(korning, forslag_med(korning, KVITTO, [
        rad(roll(korning, LEVERANTORSSKULDER), kvitto["belopp_ore"], 0, "lika", kalla(KVITTO, "belopp_ore")),
        rad(roll(korning, BANK), 0, kvitto["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "Kvitto som betalning", datum, [KVITTO], [bankraden]), "ursprung", "formen kvittot", OPPET_39)


def test_kvittots_form_pa_en_faktura_stoppas(korning):
    # 003 med kostnad och moms i debet och bankraden i kredit, utan leverantörsskulderna. Så bokförs bara ett kvitto.
    tre, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    momsrad = momsraden(tre, 12)
    stoppas(korning, forslag_med(korning, PROV_B, [
        rad("4010", momsrad["underlag_ore"], 0, "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(roll(korning, BANK), 0, tre["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "Faktura som kvitto", bankraden["transaktionsdag"], [PROV_B], [bankraden]),
        "ursprung", "formen betalningen", OPPET_39)


def test_felet_namnger_vad_som_saknas_och_vad_som_ar_for_mycket(korning):
    # En människa ska kunna läsa felet: raden som inte hör till formen, och raderna formen väntar sig.
    tre, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    text = stoppas(korning, forslag_med(korning, PROV_B, [
        rad("4010", tre["belopp_ore"], 0, "lika", bankkalla(bankraden)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, tre["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "r16", bankraden["transaktionsdag"], [PROV_B], [bankraden]), "ursprung")
    assert "Saknas:" in text and "Hör inte till formen:" in text
    assert "leverantörsskulderna" in text and "bankkontot" in text
    assert "fakturan, betalningen och kvittot" in text and "granskning 29" in text


# --- Det som kod förbi flödena ändå inte kan nå: ny typ och Z-rapporter ---

def form_direkt(korning, underlag, kopplingar, rader):
    """Delkontrollen direkt, för fall som inte går att nå med en inläst period."""
    konton = {momsrad["momssats"]: "4010" for momsrad in underlag["moms"]}
    konteringsforslag._kontrollera_flodets_form(underlag, konton, korning.kontoplan, kopplingar,
                                                {"datum": underlag["datum"], "rader": rader})


def test_en_ny_typ_av_underlag_har_ingen_form(korning):
    # Typerna är bara faktura och kvitto i dag (las_underlag.TYPER). En ny typ, till exempel kreditnotan i Ö8, ska stoppas
    # tills dess form är tillagd uttryckligen, inte tas för en faktura.
    tre = dict(underlaget(korning, PROV_B), typ="kreditnota")
    kopplingar = {"underlag": [{"id": PROV_B}], "bankrader": [], "z_rapporter": []}
    with pytest.raises(KonteringsforslagFel) as fel:
        form_direkt(korning, tre, kopplingar, fakturans_rader(korning))
    assert "'kreditnota'" in str(fel.value) and OPPET_39 in str(fel.value)


def test_en_rad_som_saknas_stoppas_av_formen_ocksa_utan_k2(korning):
    # Via skapa_konteringsforslag stoppar K2 först, eftersom en form utan en av sina rader inte går ihop. Delkontrollen
    # ska ändå hålla själv, så den prövas direkt (mutationsprovet i steg 97 visade att inget annat test ser det).
    tre = underlaget(korning, PROV_B)
    kopplingar = {"underlag": [{"id": PROV_B}], "bankrader": [], "z_rapporter": []}
    utan_momsen = [post for post in fakturans_rader(korning) if post["ursprung"]["fran"][0]["falt"] != "moms_ore"]
    with pytest.raises(KonteringsforslagFel) as fel:
        form_direkt(korning, tre, kopplingar, utan_momsen)
    assert "Saknas: momsen i debet" in str(fel.value) and OPPET_39 in str(fel.value)
    assert "Hör inte till formen" not in str(fel.value)


def test_en_z_rapport_i_ett_forslag_med_underlag_stoppas(korning):
    tre = underlaget(korning, PROV_B)
    kopplingar = {"underlag": [{"id": PROV_B}], "bankrader": [],
                  "z_rapporter": [{"kassaregister": "kassa", "znummer": 1}]}
    with pytest.raises(KonteringsforslagFel) as fel:
        form_direkt(korning, tre, kopplingar, fakturans_rader(korning))
    assert "Z-rapport" in str(fel.value) and OPPET_39 in str(fel.value)


# --- P2 (Öppet 40): stängt i steg 98 ---

def test_oppet_40_r5_en_annan_leverantors_bankrad_stoppas(korning_tele):
    # r5 i kopian där 009 har 748,75 kr: 2440 debet 009 'belopp_ore', 1940 kredit bankrad 8 i februari, som är betalningen
    # till LEV-TELE, inte till LEV-TE. Formen är flöde a:s betalning, så (b) ändrar inget. Dokumenterade hålet i steg 97 och
    # är ett stopp-test sedan steg 98: bankraden kontrolleras mot underlaget med samma matchning som flödena (beslut 2).
    nio, atta = underlaget(korning_tele, ANDRA), korning_tele.bankrad(2, 8)
    assert -atta["belopp_ore"] == nio["belopp_ore"]
    stoppas(korning_tele, forslag_med(korning_tele, ANDRA, [
        rad(roll(korning_tele, LEVERANTORSSKULDER), nio["belopp_ore"], 0, "lika", kalla(ANDRA, "belopp_ore")),
        rad(roll(korning_tele, BANK), 0, nio["belopp_ore"], "lika", bankkalla(atta)),
    ], "r5", atta["transaktionsdag"], [ANDRA], [atta]), "ursprung", repr(ANDRA), repr(atta["id"]), "Öppet 40")


# --- Rätt former godtas ---

def rader_i_flodets_form(korning, forslag):
    """(formens namn, raderna som formen ska ha), räknat här i testet, oberoende av delkontrollen i koden."""
    id_, = [post["id"] for post in forslag.kopplingar["underlag"]]
    underlag = underlaget(korning, id_)
    datum, bankrader = forslag.verifikation["datum"], [post["id"] for post in forslag.kopplingar["bankrader"]]
    assert forslag.kopplingar["z_rapporter"] == [] and len(bankrader) <= 1

    def en(konto, debet, kredit, **kallan):
        return {"konto": konto, "debet_ore": debet, "kredit_ore": kredit,
                "ursprung": {"berakning": "lika", "fran": [kallan]}}
    skulder, bank = roll(korning, LEVERANTORSSKULDER, datum), roll(korning, BANK, datum)
    regel = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    konton = kontrollera_underlag(underlag, regel, korning.regelbok, korning.momssatser).konton
    delar = []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        if momsrad["underlag_ore"]:
            delar.append(en(konton[sats], momsrad["underlag_ore"], 0, kalla="underlag", id=id_, falt="underlag_ore",
                            momssats=sats))
        if momsrad["moms_ore"]:
            delar.append(en(roll(korning, INGAENDE_MOMS, datum), momsrad["moms_ore"], 0, kalla="underlag", id=id_,
                            falt="moms_ore", momssats=sats))
    belopp = underlag["belopp_ore"]
    if underlag["typ"] == "kvitto":
        return "kvittot", delar + [en(bank, 0, belopp, kalla="bankrad", id=bankrader[0], falt="belopp_ore")]
    if not bankrader:
        return "fakturan", delar + [en(skulder, 0, belopp, kalla="underlag", id=id_, falt="belopp_ore")]
    return "betalningen", [en(skulder, belopp, 0, kalla="underlag", id=id_, falt="belopp_ore"),
                           en(bank, 0, belopp, kalla="bankrad", id=bankrader[0], falt="belopp_ore")]


def test_skydd_varje_forslag_med_underlag_i_hela_korningen_har_exakt_en_av_de_tre_formerna(korning):
    # Skydd (grönt också före rättelsen): raderna räknas här i testet, oberoende av koden, och jämförs exakt.
    former = Counter()
    for forslag in korning.resultat.forslag:
        if not forslag.kopplingar["underlag"]:
            continue
        form, vantade = rader_i_flodets_form(korning, forslag)
        assert sorted(forslag.verifikation["rader"], key=repr) == sorted(vantade, key=repr), forslag.forslag_id
        assert forslag.kontroller == ALLA_KONTROLLER
        former[form] += 1
    # Antalen från granskning 29 (f1): 16 fakturor, 6 betalningar och 3 kvitton. Skyddet är alltså inte tomt.
    assert former == {"fakturan": 16, "betalningen": 6, "kvittot": 3}


def test_skydd_flode_a_b_och_e_gar_igenom(korning):
    # Skydd (grönt också före rättelsen): flöde a och b, och bankavgiften i flöde e, som inte har något underlag.
    fakturan, betalningen = korning.forslag_for(PROV_B)
    assert fakturan.forslag_id == "F-FAKTURA-" + PROV_B and betalningen.forslag_id == "F-BETALNING-" + PROV_B
    kvittot, = korning.forslag_for(KVITTO)
    assert kvittot.forslag_id == "F-KVITTO-" + KVITTO
    utan_underlag = [post for post in korning.resultat.forslag if not post.kopplingar["underlag"]]
    assert utan_underlag
    for post in utan_underlag:
        assert post.kontroller == {"K2": "ok", "ursprung": "ok"} and len(post.kopplingar["bankrader"]) == 1


def test_skydd_raderna_i_en_annan_ordning_ar_samma_form(korning):
    # Skydd (grönt också före rättelsen): ordningen ändrar inte konteringen.
    fakturan = prov_b_003(korning)
    fakturan["verifikation"]["rader"].reverse()
    assert skapa(korning, fakturan).kontroller == ALLA_KONTROLLER
    betalningen = betalningen_for_hand(korning)
    betalningen["verifikation"]["rader"].reverse()
    assert skapa(korning, betalningen).kontroller == ALLA_KONTROLLER


def test_skydd_en_momsrad_med_kostnaden_0_har_ingen_rad_i_formen(tmp_path):
    # Skydd (grönt också före rättelsen, Hugos svar i chatten 2026-11-04: följ koden). Flödena tar inte med en rad med
    # beloppet 0, varken kostnaden eller momsen, och K2 förbjuder sådana rader. Formen får då inte kräva dem, för då
    # skulle flödets eget förslag stoppas och hela körningen stanna.
    def utan_25(data):
        tjugofem, = [post for post in data["moms"] if post["momssats"] == 25]
        data["belopp_ore"] -= tjugofem["underlag_ore"] + tjugofem["moms_ore"]
        tjugofem["underlag_ore"] = tjugofem["moms_ore"] = 0
    korningen = Korning(underlag=underlagsmapp(tmp_path, **{PROV_A: utan_25}))
    fakturan = korningen.forslag_for(PROV_A)[0]
    assert fakturan.forslag_id == "F-FAKTURA-" + PROV_A
    assert len(fakturan.verifikation["rader"]) == 3
    assert fakturan.kontroller == ALLA_KONTROLLER


# --- Dokumentationen i koden ---

def test_koden_namner_regeln():
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 39" in kod and "granskning 29" in kod and "Hugos beslut 2026-11-04 om granskning 29" in kod
    assert "steg 97" in kod and "Ö8" in kod
