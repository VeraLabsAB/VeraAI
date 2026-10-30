"""Tester för Hugos beslut 2026-10-30 om granskning 26 (GRANSKNING.md, "Hugos beslut 2026-10-30 om granskning 26").

"Ja, i samma steg": Öppet 33 och Öppet 34 byggs i ett steg (steg 93) före uppgift 5, i _kontrollera_underlagen efter
Öppet 32, med granskarens förslag till regel för Öppet 34.

- Öppet 33 (granskning 25, P7, och Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a): varje rad med ett
  underlags 'moms_ore' som källa står på kontot för ingående moms (rollen i kontoplanen). Granskarens prov H7 i
  granskning 26: SYNT-U-2025-003 med momsen på kostnadskontot 4010 godtogs med alla kontrollerna "ok".
- Öppet 34 (granskning 26, M1): en rad med ett underlags 'belopp_ore' som källa räknas bara med 'lika' och står bara
  på leverantörsskulderna, och 'underlag_ore' och 'moms_ore' räknas aldrig med 'skillnad'. Byggsessionens tillägg:
  underlagets 'belopp_ore' står på högst en rad i förslaget. Granskarens fyra LUCKA-prov: kostnaden räknad som
  'skillnad' av 'belopp_ore' och momsen på 2440 (prov (b) från granskning 25 byggt så), kontona bytta inom regeln
  byggda så (prov (a)), hela beloppet med moms på 4010 utan momsrad, och hela beloppet på 2440 på båda sidorna.
  Alla godtogs med alla kontrollerna "ok", eftersom ingen rad hade 'underlag_ore' som källa och täckningen gick ihop.
- Flödena a, b och e bygger kostnaden ur 'underlag_ore', momsen ur 'moms_ore' på kontot för ingående moms och
  beloppet ur 'belopp_ore' en gång med 'lika' på leverantörsskulderna, så deras förslag går igenom som förut. De
  testerna är skydd och var gröna också före rättelsen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot en kopia av 5b4aa83 (koden före rättelsen), se PROGRESS.md.
"""

import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_konteringsfloden import Korning, regelbok_med  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_23 import forslag_prov_b, momsfil_med_varugruppen_kostnad  # noqa: E402
from test_beslut_granskning_25 import (  # noqa: E402
    ALLA_KONTROLLER, PROV_A, PROV_B, forslag_med_kontona, kostnadskonton, tva_konton,
)

INGAENDE_MOMS = "ingaende_moms"
LEVERANTORSSKULDER = "leverantorsskulder"


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_b(tmp_path_factory):
    """Granskarens momsfil från prov B i granskning 23, där 'kostnad' är en varugrupp med 12 %."""
    return Korning(momssatser=momsfil_med_varugruppen_kostnad(tmp_path_factory.mktemp("prov_b")))


@pytest.fixture(scope="module")
def korning_tva(tmp_path_factory):
    """Granskarens regelbok i prov (a): R-LEV-KAFFE med livsmedel på 4010 och ovrigt på 5460."""
    return Korning(regelbok=regelbok_med(tmp_path_factory.mktemp("tva_konton"), tva_konton))


# --- Förslag byggda för hand, förbi flödena ---

def kalla(id_, falt, sats=None):
    data = {"kalla": "underlag", "id": id_, "falt": falt}
    if sats is not None:
        data["momssats"] = sats
    return data


def rad(konto, debet, kredit, berakning, *kallor):
    return {"konto": konto, "debet_ore": debet, "kredit_ore": kredit,
            "ursprung": {"berakning": berakning, "fran": list(kallor)}}


def underlaget(korning, id_):
    underlag, = [post for post in korning.underlagsperiod.underlag if post["id"] == id_]
    return underlag


def momsraden(underlag, sats):
    momsrad, = [post for post in underlag["moms"] if post["momssats"] == sats]
    return momsrad


def forslag_for_hand(korning, id_, rader, vad):
    """Ett förslag för underlaget id_ under dess egen regel, på underlagets datum, med raderna rader.

    Regeln är underlagets egen (Öppet 31) och kontona står i regeln eller har en roll (punkt 8), så det som kan
    stoppa förslaget är kontrollerna av raderna från underlaget: Öppet 32, 34 och 33.
    """
    underlag = underlaget(korning, id_)
    regelbok, kontoplan = korning.regelbok, korning.kontoplan
    regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    mot = regelbok.kontrollerad_mot
    return {
        "forslag_id": "F-PROV-G26-" + id_,
        "verifikation": {"datum": underlag["datum"], "text": vad + ", underlag " + id_, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_}], "bankrader": [], "z_rapporter": [],
                       "regel": {"id": regel["id"], "regelbokens_kontrollsumma": regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": "Byggt för hand i testet för granskning 26, förbi flödena.",
    }


def roll(korning, vilken, datum="2025-01-07"):
    return korning.kontoplan.rollens_konto(vilken, datum)


def prov_b_003(korning, momskonto=None, kostnadskonto="4010"):
    """SYNT-U-2025-003 som flöde a bygger fakturan, men med momsen på momskonto (om det anges) och kostnaden på
    kostnadskonto. Momsraden har 12 %: 14 938,00 kr utan moms, 1 792,56 kr moms, 16 730,56 kr att betala."""
    underlag = underlaget(korning, PROV_B)
    momsrad = momsraden(underlag, 12)
    if momskonto is None:
        momskonto = roll(korning, INGAENDE_MOMS)
    return forslag_for_hand(korning, PROV_B, [
        rad(kostnadskonto, momsrad["underlag_ore"], 0, "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad(momskonto, momsrad["moms_ore"], 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, underlag["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "Prov för Öppet 33")


# --- Öppet 33: granskarens prov H7, momsen på kostnadskontot ---

@pytest.mark.parametrize("vilken", ["korning", "korning_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o33_h7_momsen_pa_kostnadskontot_stoppas(request, vilken):
    # H7 i granskning 26: 003 med momsen på 4010 i stället för 2641 godtogs med alla kontrollerna "ok". Punkt 5
    # säger bara vad en rad på ett momskonto får ha som källa. Nu stoppas förslaget, och felet namnger raden,
    # underlaget, satsen, kontot raden står på och kontot för ingående moms.
    korning = request.getfixturevalue(vilken)
    ingaende = roll(korning, INGAENDE_MOMS)
    text = stoppas(korning, prov_b_003(korning, momskonto="4010"), "ursprung", "rad 2 (konto 4010)",
                   "'" + PROV_B + "'", "12 %", "'moms_ore'", "står på kontot 4010", "kontot " + ingaende,
                   "'ingaende_moms'", "Öppet 33")
    # Felet hänvisar till beslutet om byggsessionen för Öppet 32, men stoppet är inte Öppet 32:s eller 34:s.
    assert "(Öppet 32," not in text and "Öppet 34" not in text


def test_o33_momsen_pa_leverantorsskulderna_stoppas(korning):
    # Ett rollkonto i stället för ett konto i regeln: momsen på 2440 (debet), beloppet på 2440 (kredit). Punkt 8
    # godtar kontot eftersom det har en roll, och punkt 5 prövar inte raden eftersom 2440 inte är ett momskonto.
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, prov_b_003(korning, momskonto=skulder), "ursprung", "rad 2 (konto " + skulder + ")",
                   "'" + PROV_B + "'", "'moms_ore'", "inte är kontot för ingående moms", "Öppet 33")
    assert "roll i kontoplanen" in text


# --- Öppet 34: granskarens fyra LUCKA-prov ---

def lucka_1_kostnaden_som_skillnad(korning, konto):
    """Kostnaden räknad som 'skillnad' av 'belopp_ore' och momsen, på kontot konto. Samma verifikation som prov (b)
    i granskning 25 när konto är 2440, men utan 'underlag_ore' som källa, så Öppet 32 ser inte raden."""
    underlag = underlaget(korning, PROV_B)
    momsrad = momsraden(underlag, 12)
    return forslag_for_hand(korning, PROV_B, [
        rad(konto, underlag["belopp_ore"] - momsrad["moms_ore"], 0, "skillnad", kalla(PROV_B, "belopp_ore"),
            kalla(PROV_B, "moms_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, underlag["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "LUCKA 1 i granskning 26")


@pytest.mark.parametrize("vilken", ["korning", "korning_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o34_lucka_1_kostnaden_som_skillnad_pa_leverantorsskulderna_stoppas(request, vilken):
    # test_l1_kostnaden_som_skillnad_belopp_minus_moms_pa_2440_godtas_LUCKA i granskning 26: 2440 debet 14 938,00 kr,
    # 2641 debet 1 792,56 kr, 2440 kredit 16 730,56 kr, kostnaden räknad som 'skillnad'. Godtogs med alla
    # kontrollerna "ok". Nu stoppas den: 'belopp_ore' räknas bara med 'lika'.
    korning = request.getfixturevalue(vilken)
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, lucka_1_kostnaden_som_skillnad(korning, skulder), "ursprung",
                   "rad 1 (konto " + skulder + ") räknas med 'skillnad'", "'" + PROV_B + "'", "'belopp_ore'",
                   "bara med 'lika'", "Öppet 34")
    assert "Öppet 32" not in text and "Öppet 33" not in text


def test_o34_lucka_1_ocksa_pa_ratt_konto_stoppas(korning):
    # Också på kostnadskontot 4010, där beloppet blir rätt: sättet att räkna är fel, så raden stoppas ändå. Felet
    # handlar om beräkningen (Öppet 34), inte om kontot.
    stoppas(korning, lucka_1_kostnaden_som_skillnad(korning, "4010"), "ursprung",
            "rad 1 (konto 4010) räknas med 'skillnad'", "'belopp_ore'", "Öppet 34")


def lucka_2_kontona_bytta_som_skillnad(korning):
    """Prov (a) från granskning 25 byggt som 'skillnad': 020 i granskarens regelbok (12 % på 4010, 25 % på 5460), med
    kostnaden för 12 % på 5460 och för 25 % på 4010, båda räknade som 'belopp_ore' minus de tre andra delarna."""
    underlag = underlaget(korning, PROV_A)
    tolv, tjugofem = momsraden(underlag, 12), momsraden(underlag, 25)
    belopp, ingaende = underlag["belopp_ore"], roll(korning, INGAENDE_MOMS, underlag["datum"])
    return forslag_for_hand(korning, PROV_A, [
        rad("5460", tolv["underlag_ore"], 0, "skillnad", kalla(PROV_A, "belopp_ore"), kalla(PROV_A, "moms_ore", 12),
            kalla(PROV_A, "underlag_ore", 25), kalla(PROV_A, "moms_ore", 25)),
        rad(ingaende, tolv["moms_ore"], 0, "lika", kalla(PROV_A, "moms_ore", 12)),
        rad("4010", tjugofem["underlag_ore"], 0, "skillnad", kalla(PROV_A, "belopp_ore"),
            kalla(PROV_A, "moms_ore", 12), kalla(PROV_A, "underlag_ore", 12), kalla(PROV_A, "moms_ore", 25)),
        rad(ingaende, tjugofem["moms_ore"], 0, "lika", kalla(PROV_A, "moms_ore", 25)),
        rad(roll(korning, LEVERANTORSSKULDER, underlag["datum"]), 0, belopp, "lika", kalla(PROV_A, "belopp_ore")),
    ], "LUCKA 2 i granskning 26")


def test_o34_lucka_2_kontona_bytta_som_skillnad_stoppas(korning_tva):
    # test_l1_prov_a_kontona_bytta_som_skillnad_godtas_LUCKA i granskning 26: godtogs med alla kontrollerna "ok",
    # med 10 249,00 kr på 5460 och 916,00 kr på 4010, tvärtom mot vad K5 ger. Öppet 32 ser bara de subtraherade
    # 'underlag_ore'-källorna, som råkar stämma med kontot. Nu stoppas raden för att den räknas med 'skillnad'.
    underlag = underlaget(korning_tva, PROV_A)
    assert momsraden(underlag, 12)["underlag_ore"] == 1024900 and momsraden(underlag, 25)["underlag_ore"] == 91600
    text = stoppas(korning_tva, lucka_2_kontona_bytta_som_skillnad(korning_tva), "ursprung",
                   "rad 1 (konto 5460) räknas med 'skillnad'", "'" + PROV_A + "'", "'belopp_ore'", "Öppet 34")
    assert "Öppet 32" not in text


def test_o34_lucka_3_hela_beloppet_med_moms_pa_kostnadskontot_utan_momsrad_stoppas(korning):
    # test_l2_hela_beloppet_med_moms_pa_kostnadskontot_utan_momsrad_godtas_LUCKA: 16 730,56 kr på 4010 debet och
    # 2440 kredit, ingen momsrad. Godtogs: täckningen går ihop (hela underlaget på varje sida), och ingen rad har
    # 'underlag_ore'. Nu stoppas den: 'belopp_ore' står bara på leverantörsskulderna.
    underlag = underlaget(korning, PROV_B)
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad("4010", underlag["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, 0, underlag["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "LUCKA 3 i granskning 26"), "ursprung", "rad 1 (konto 4010)", "'" + PROV_B + "'", "'belopp_ore'",
        "inte är leverantörsskulderna", "kontot " + skulder, "'leverantorsskulder'", "Öppet 34")
    assert "ingående moms" in text  # felet säger var momsen och kostnaden ska stå


def test_o34_lucka_4_hela_beloppet_pa_leverantorsskulderna_pa_bada_sidorna_stoppas(korning):
    # test_l2_hela_beloppet_pa_leverantorsskulderna_bada_sidor_godtas_LUCKA: 2440 debet och 2440 kredit ur
    # 'belopp_ore', ingen kostnad och ingen moms bokförs alls. Granskarens regel ensam ('lika', leverantörsskulderna)
    # släpper igenom den, därför byggsessionens tillägg: 'belopp_ore' står på högst en rad i förslaget.
    underlag = underlaget(korning, PROV_B)
    skulder = roll(korning, LEVERANTORSSKULDER)
    stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad(skulder, underlag["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, 0, underlag["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "LUCKA 4 i granskning 26"), "ursprung", "rad 1 och 2", "'" + PROV_B + "'", "'belopp_ore'", "högst en rad",
        "Öppet 34")


def test_o34_underlag_ore_med_skillnad_stoppas_fast_kontot_ar_ratt(korning):
    # Byggsessionens eget prov: kostnaden på 4010 räknad som 'underlag_ore' minus momsen (13 145,44 kr), och momsen
    # två gånger på 2641. Täckningen går ihop (momsen dras ifrån en gång och läggs till två gånger i debet), Öppet
    # 32 godtar (raden har 'underlag_ore' på kontot K5 ger). Godtogs före steg 93 med alla kontrollerna "ok". Nu
    # stoppas den: 'underlag_ore' och 'moms_ore' räknas aldrig med 'skillnad'.
    underlag = underlaget(korning, PROV_B)
    momsrad, ingaende = momsraden(underlag, 12), roll(korning, INGAENDE_MOMS)
    text = stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad("4010", momsrad["underlag_ore"] - momsrad["moms_ore"], 0, "skillnad", kalla(PROV_B, "underlag_ore", 12),
            kalla(PROV_B, "moms_ore", 12)),
        rad(ingaende, momsrad["moms_ore"], 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(ingaende, momsrad["moms_ore"], 0, "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(roll(korning, LEVERANTORSSKULDER), 0, underlag["belopp_ore"], "lika", kalla(PROV_B, "belopp_ore")),
    ], "Byggsessionens prov för Öppet 34"), "ursprung", "rad 1 (konto 4010) räknas med 'skillnad'",
        "'" + PROV_B + "'", "12 %", "'underlag_ore'", "aldrig med 'skillnad'", "Öppet 34")
    assert "Öppet 32" not in text and "Öppet 33" not in text


# --- Ordningen: K5, K8, Öppet 31 och Öppet 32 prövas före de nya kontrollerna ---

def test_ordning_prov_b_019_och_028_stoppas_fortfarande_av_k5_och_k8_forst(korning_b):
    # Skydd (grönt också före rättelsen): prov B från granskning 23 stoppas med samma kontroll som förut.
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-019"), "K5", "R-BUTIK-STAD")
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-028"), "K8", "R-RESTAURANG-1")


def test_ordning_granskarens_prov_fran_granskning_24_stoppas_fortfarande_av_oppet_31(korning):
    # Skydd (grönt också före rättelsen): 003 under bankregeln stoppas av Öppet 31 (fel regel).
    text = stoppas(korning, forslag_prov_b(korning, PROV_B), "ursprung", "Öppet 31", "'R-BANK-AVGIFT'")
    assert "Öppet 33" not in text and "Öppet 34" not in text


def test_ordning_prov_b_fran_granskning_25_stoppas_fortfarande_av_oppet_32(korning):
    # Skydd (grönt också före rättelsen): 003 med kostnaden på 2440 ur 'underlag_ore' stoppas av Öppet 32, före
    # Öppet 34 och 33, fast beloppet står på 2440 på båda sidorna.
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, forslag_med_kontona(korning, PROV_B, {12: skulder}), "ursprung", "Öppet 32",
                   "K5 ger kontot 4010")
    assert "Öppet 33" not in text and "Öppet 34" not in text


def test_ordning_oppet_34_provas_fore_oppet_33(korning):
    # Kostnaden som 'skillnad' av 'belopp_ore' och momsen (LUCKA 1) har momsen som källa på en rad som inte är
    # momskontot. Felet säger att raden räknas fel (Öppet 34), inte att momsen står på fel konto (Öppet 33).
    text = stoppas(korning, lucka_1_kostnaden_som_skillnad(korning, "4010"), "ursprung", "Öppet 34")
    assert "Öppet 33" not in text


# --- Rätt förslag godtas: flödena och förslag för hand med rätt form ---

def test_skydd_ett_forslag_med_ratt_form_godtas(korning, korning_b):
    # Skydd (grönt också före rättelsen): fakturan för 003 som flöde a bygger den, för hand, med båda momsfilerna.
    for en in (korning, korning_b):
        forslag = skapa(en, prov_b_003(en))
        assert forslag.kontroller == ALLA_KONTROLLER and kostnadskonton(forslag) == {12: "4010"}


def test_skydd_momsen_summerad_over_tva_satser_godtas(korning):
    # 'summa' är tillåtet för 'moms_ore': 020:s två momsrader på en rad på kontot för ingående moms, med kostnaden
    # per sats på kontot K5 ger (testbutikens regelbok ger samma konto för båda satserna).
    underlag = underlaget(korning, PROV_A)
    tolv, tjugofem, datum = momsraden(underlag, 12), momsraden(underlag, 25), underlag["datum"]
    egen = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], datum)
    from konteringsforslag import kontrollera_underlag
    konton = kontrollera_underlag(underlag, egen, korning.regelbok, korning.momssatser).konton
    forslag = skapa(korning, forslag_for_hand(korning, PROV_A, [
        rad(konton[12], tolv["underlag_ore"], 0, "lika", kalla(PROV_A, "underlag_ore", 12)),
        rad(konton[25], tjugofem["underlag_ore"], 0, "lika", kalla(PROV_A, "underlag_ore", 25)),
        rad(roll(korning, INGAENDE_MOMS, datum), tolv["moms_ore"] + tjugofem["moms_ore"], 0, "summa",
            kalla(PROV_A, "moms_ore", 12), kalla(PROV_A, "moms_ore", 25)),
        rad(roll(korning, LEVERANTORSSKULDER, datum), 0, underlag["belopp_ore"], "lika", kalla(PROV_A, "belopp_ore")),
    ], "Momsen summerad"))
    assert forslag.kontroller == ALLA_KONTROLLER


def test_skydd_020_med_tva_konton_i_regeln_godtas_med_ratt_konton(korning_tva):
    # Skydd (grönt också före rättelsen): prov (a) med rätt konton, flödet och för hand.
    fakturan = korning_tva.forslag_for(PROV_A)[0]
    assert kostnadskonton(fakturan) == {12: "4010", 25: "5460"}
    for_hand = skapa(korning_tva, forslag_med_kontona(korning_tva, PROV_A, {12: "4010", 25: "5460"}))
    assert for_hand.kontroller == ALLA_KONTROLLER and for_hand.verifikation["rader"] == fakturan.verifikation["rader"]


def test_skydd_flode_a_fakturan_och_betalningen_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde a: fakturan med 'belopp_ore' en gång i kredit på 2440, och
    # betalningen med 'belopp_ore' en gång i debet på 2440 och bankraden i kredit.
    fakturan, betalningen = korning.forslag_for(PROV_B)
    assert (fakturan.forslag_id, betalningen.forslag_id) == ("F-FAKTURA-" + PROV_B, "F-BETALNING-" + PROV_B)
    assert fakturan.kontroller == betalningen.kontroller == ALLA_KONTROLLER
    assert [rad_["konto"] for rad_ in fakturan.verifikation["rader"]] == ["4010", "2641", "2440"]
    assert [rad_["konto"] for rad_ in betalningen.verifikation["rader"]] == ["2440", "1940"]
    assert korning.arenden_for(PROV_B) == []


def test_skydd_flode_b_kvittot_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde b: kvittot 015 med kostnaden på 5460, momsen på 2641 och bankraden.
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    assert kvittot.forslag_id == "F-KVITTO-SYNT-U-2025-015" and kvittot.kontroller == ALLA_KONTROLLER
    assert [rad_["konto"] for rad_ in kvittot.verifikation["rader"]] == ["5460", "2641", "1940"]
    assert korning.arenden_for("SYNT-U-2025-015") == []


def test_skydd_flode_e_bankavgiften_gar_igenom_utan_underlag(korning):
    # Skydd (grönt också före rättelsen). Flöde e: bankrad 117 i januari under R-BANK-AVGIFT, utan underlag. De nya
    # kontrollerna gäller bara rader med ett underlag som källa.
    rad_ = korning.bankrad(1, 117)
    forslag, = [post for post in korning.resultat.forslag
                if [bankrad["id"] for bankrad in post.kopplingar["bankrader"]] == [rad_["id"]]]
    assert forslag.forslag_id == "F-BANKRAD-" + rad_["id"] and forslag.kopplingar["underlag"] == []
    assert forslag.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_skydd_varje_rad_fran_ett_underlag_i_flodena_har_ratt_form(korning):
    # Skydd (grönt också före rättelsen): i hela körningen står varje 'moms_ore'-rad på kontot för ingående moms,
    # varje 'belopp_ore'-rad räknas med 'lika' och står på leverantörsskulderna, högst en per underlag och förslag,
    # och ingen rad med ett underlag som källa räknas med 'skillnad'. Det är därför flödena inte berörs.
    kontoplan = korning.kontoplan
    med_underlag = [forslag for forslag in korning.resultat.forslag if forslag.kopplingar["underlag"]]
    assert med_underlag
    for forslag in med_underlag:
        beloppsrader = {}
        for rad_ in forslag.verifikation["rader"]:
            roller = kontoplan.kontots_roller(rad_["konto"])
            for kalla_ in rad_["ursprung"]["fran"]:
                if kalla_["kalla"] != "underlag":
                    continue
                assert rad_["ursprung"]["berakning"] != "skillnad", forslag.forslag_id
                if kalla_["falt"] == "moms_ore":
                    assert (INGAENDE_MOMS, None) in roller, forslag.forslag_id
                if kalla_["falt"] == "belopp_ore":
                    assert rad_["ursprung"]["berakning"] == "lika", forslag.forslag_id
                    assert (LEVERANTORSSKULDER, None) in roller, forslag.forslag_id
                    beloppsrader[kalla_["id"]] = beloppsrader.get(kalla_["id"], 0) + 1
        assert all(antal == 1 for antal in beloppsrader.values()), forslag.forslag_id


# --- Dokumentationen ---

def test_spec_och_koden_namner_reglerna():
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "Öppet 33" in spec and "Öppet 34" in spec and "granskning 26" in spec
    for text in ("räknas bara med `lika`", "högst en rad", "aldrig med `skillnad`", "kontot för ingående moms"):
        assert text in spec, text
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 33" in kod and "Öppet 34" in kod
    assert "inte beslutat" not in kod  # granskning 26, L1
