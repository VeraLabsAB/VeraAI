"""Tester för Hugos beslut 2026-11-04 om granskning 28, Öppet 36 (GRANSKNING.md, granskning 28, M1).

Beslut 1, skrivet av Hugo i uppdraget till den här sessionen: Öppet 36 byggs enligt granskarens (a). För varje rad
med ett underlags 'belopp_ore' i debet ska förslaget ha en egen rad på bankkontot (rollen bank i kontoplanen) i
kredit, med samma belopp, och med en bankrad som källa. Uppdraget lade till: två rader med 'belopp_ore' i debet och
samma belopp får inte dela en och samma rad på bankkontot (varje bankkontorad räknas bara en gång). Byggt i
_kontrollera_beloppssidan, i grenen för debet, efter Öppet 35:s krav på att förslaget har någon bankrad alls.

- Granskarens prov b1 i granskning 28: 003 spegelvänd (2440 debet 'belopp_ore', 4010 kredit 'underlag_ore', 2641
  kredit 'moms_ore') i samma förslag som 009:s riktiga betalning (2440 debet 009 'belopp_ore', 1940 kredit bankrad 84
  i februari). Godtogs med alla kontrollerna "ok": Öppet 35 frågar bara om förslaget har någon bankrad.
- Granskarens prov b2: 003 och 009 med samma belopp (en kopia av testdatan) kvittade mot varandra på 2440, plus 009
  som delar i debet mot bankrad 26 (003:s betalning, 16 730,56 kr) i kredit på 1940. Godtogs också, och godtas
  fortfarande: b2 uppfyller (a), eftersom bankrad 26 är 003:s betalning och står mot 003:s belopp. Konteringen är
  identisk med flöde a:s två förslag (009:s faktura och 003:s betalning) i samma förslag, så det är inte felaktig
  bokföring och inte ett nytt hål i familjen (Hugos beslut 2026-11-04, 1). b2 är därför ett skydd här.
- Granskarens prov b3: 003:s 'belopp_ore' i debet på 2440 mot bankrad 26 som källa på 4010 i kredit, utan någon rad på
  bankkontot. Godtogs också: punkt 6 säger bara vad bankkontot får ha som källa, inte var en bankrad får stå.
- Byggsessionens prov: två rader med 'belopp_ore' i debet (003 och 009 med samma belopp) mot en enda rad på
  bankkontot med det beloppet. Utan regeln att varje bankkontorad räknas bara en gång skulle båda raderna hitta samma
  bankkontorad.
- Flödena a och b bygger betalningen med 'belopp_ore' i debet på leverantörsskulderna och exakt en rad på bankkontot i
  kredit med samma belopp ur bankraden (granskarens f4), så deras förslag går igenom som förut. De testerna är skydd
  och var gröna också före rättelsen.
- Kreditnotor (Ö8) finns inte än: typen saknas och negativa belopp stoppas i las_underlag (test i
  test_beslut_granskning_27.py). När Ö8 byggs måste regeln prövas igen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot koden i 3f36f6b (före rättelsen): b1, b3, den delade bankkontoraden och
texttestet, körda i projektmappen innan konteringsforslag.py ändrades (då var också b2 skrivet som ett stopp och
rött, både före och efter rättelsen), se PROGRESS.md.
"""

import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from las_bank import kronor  # noqa: E402
from test_konteringsfloden import Korning  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_25 import ALLA_KONTROLLER, PROV_B  # noqa: E402
from test_beslut_granskning_26 import (  # noqa: E402
    INGAENDE_MOMS, LEVERANTORSSKULDER, forslag_for_hand, kalla, momsraden, prov_b_003, rad, roll, underlaget,
)
from test_beslut_granskning_27 import ANDRA, betalningen_for_hand, korning_lika  # noqa: E402, F401

BANK = "bank"


@pytest.fixture(scope="module")
def korning():
    return Korning()


def bankkalla(bankraden):
    return {"kalla": "bankrad", "id": bankraden["id"], "falt": "belopp_ore"}


def forslag_med(korning, id_, rader, vad, datum, underlagen, bankrader):
    """Ett förslag för hand under id_:s egen regel, med egna kopplingar och eget datum."""
    forslag = forslag_for_hand(korning, id_, rader, vad)
    forslag["verifikation"]["datum"] = datum
    forslag["kopplingar"]["underlag"] = [{"id": ett} for ett in underlagen]
    forslag["kopplingar"]["bankrader"] = [{"id": bankrad["id"]} for bankrad in bankrader]
    return forslag


# --- Öppet 36: granskarens tre prov som gick igenom i granskning 28 ---

def test_o36_b1_fakturan_spegelvand_ihop_med_en_annan_fakturas_betalning_stoppas(korning):
    # Granskarens b1: 003 spegelvänd (rad 1–3) och 009:s riktiga betalning (rad 4–5, bankrad 84 i februari,
    # 15 037,12 kr), datum 2025-02-19, båda underlagen och bankraden i kopplingarna. Godtogs före rättelsen med alla
    # fem kontrollerna "ok". Nu stoppas den: 003:s belopp i debet har ingen egen rad på bankkontot med samma belopp.
    tre, nio = underlaget(korning, PROV_B), underlaget(korning, ANDRA)
    assert len(korning.forslag_for(ANDRA)) == 2  # 009 är inte K4-flaggad: fakturan och betalningen finns i flöde a
    momsrad, bankraden = momsraden(tre, 12), korning.bankrad(2, 84)
    assert -bankraden["belopp_ore"] == nio["belopp_ore"] != tre["belopp_ore"]
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, forslag_med(korning, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), 0, momsrad["moms_ore"], "lika", kalla(PROV_B, "moms_ore", 12)),
        rad(skulder, nio["belopp_ore"], 0, "lika", kalla(ANDRA, "belopp_ore")),
        rad(roll(korning, BANK), 0, nio["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "b1 i granskning 28", bankraden["transaktionsdag"], [PROV_B, ANDRA], [bankraden]),
        "ursprung", "rad 1 (konto " + skulder + ")", "'" + PROV_B + "'", "'belopp_ore'", "i debet",
        kronor(tre["belopp_ore"]), "rad 5 (konto " + roll(korning, BANK) + "), " + kronor(nio["belopp_ore"]),
        "redan betalningen för rad 4", "Öppet 36")
    assert "Öppet 35" not in text


def test_skydd_b2_en_fakturas_betalning_och_en_annan_faktura_i_samma_forslag_godtas(korning, korning_lika):
    # Granskarens b2, i kopian där 009 har 003:s belopp: 2440 debet 003 'belopp_ore', 2440 kredit 009 'belopp_ore',
    # 4010 debet 009 'underlag_ore', 2641 debet 009 'moms_ore' och 1940 kredit bankrad 26 (16 730,56 kr, 003:s
    # betalning). Skydd (grönt också före rättelsen): b2 godtas under (a), Hugos beslut 2026-11-04 (1). Granskaren
    # räknade b2 som ett hål, men bankrad 26 är 003:s betalning och står mot just 003:s belopp: regeln ser en rad
    # med 'belopp_ore' i debet och en egen rad på bankkontot i kredit med samma belopp ur en bankrad (003:s
    # betalning), och ett belopp i kredit med delarna i debet (009:s faktura). Konteringen är identisk med flöde a:s
    # två förslag för 009:s faktura och 003:s betalning, bara i samma förslag, så det är inte felaktig bokföring
    # och inte ett nytt hål i familjen. Att en faktura och en annan fakturas betalning står i samma förslag ska
    # kontrolleras med en redovisningskonsult och tas upp igen när godkännandekortet i appen byggs (samma beslut,
    # 3, PROGRESS.md, Öppet).
    tre, nio = underlaget(korning_lika, PROV_B), underlaget(korning_lika, ANDRA)
    assert tre["belopp_ore"] == nio["belopp_ore"] and tre["moms"] == nio["moms"]
    assert korning_lika.underlagsperiod.arenden == korning.underlagsperiod.arenden
    momsrad, bankraden = momsraden(nio, 12), korning_lika.bankrad(2, 26)
    assert -bankraden["belopp_ore"] == tre["belopp_ore"]
    skulder = roll(korning_lika, LEVERANTORSSKULDER)
    forslag = skapa(korning_lika, forslag_med(korning_lika, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, 0, nio["belopp_ore"], "lika", kalla(ANDRA, "belopp_ore")),
        rad("4010", momsrad["underlag_ore"], 0, "lika", kalla(ANDRA, "underlag_ore", 12)),
        rad(roll(korning_lika, INGAENDE_MOMS), momsrad["moms_ore"], 0, "lika", kalla(ANDRA, "moms_ore", 12)),
        rad(roll(korning_lika, BANK), 0, tre["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "b2 i granskning 28", bankraden["transaktionsdag"], [PROV_B, ANDRA], [bankraden]))
    assert forslag.kontroller == ALLA_KONTROLLER
    # Samma kontering som flöde a:s två förslag, per konto och sida.
    fakturan_009, betalningen_003 = korning_lika.forslag_for(ANDRA)[0], korning_lika.forslag_for(PROV_B)[1]
    assert fakturan_009.forslag_id == "F-FAKTURA-" + ANDRA and betalningen_003.forslag_id == "F-BETALNING-" + PROV_B

    def per_konto(rader):
        summor = {}
        for rad_ in rader:
            summor[rad_["konto"]] = summor.get(rad_["konto"], 0) + rad_["debet_ore"] - rad_["kredit_ore"]
        return summor
    assert per_konto(forslag.verifikation["rader"]) == per_konto(
        fakturan_009.verifikation["rader"] + betalningen_003.verifikation["rader"])


def test_o36_b3_bankraden_pa_kostnadskontot_i_stallet_for_bankkontot_stoppas(korning):
    # Granskarens b3: 2440 debet 003 'belopp_ore' och 4010 kredit med bankrad 26 som källa (16 730,56 kr), ingen rad
    # på bankkontot. Godtogs före rättelsen med alla kontrollerna "ok". Nu stoppas den: bankraden står inte på
    # bankkontot.
    tre, bankraden = underlaget(korning, PROV_B), korning.bankrad(2, 26)
    assert -bankraden["belopp_ore"] == tre["belopp_ore"]
    skulder = roll(korning, LEVERANTORSSKULDER)
    text = stoppas(korning, forslag_med(korning, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad("4010", 0, tre["belopp_ore"], "lika", bankkalla(bankraden)),
    ], "b3 i granskning 28", bankraden["transaktionsdag"], [PROV_B], [bankraden]),
        "ursprung", "rad 1 (konto " + skulder + ")", "'" + PROV_B + "'", "'belopp_ore'", "i debet",
        "ingen rad på bankkontot", "Öppet 36")
    assert "Öppet 35" not in text


def test_o36_tva_belopp_i_debet_far_inte_dela_en_rad_pa_bankkontot(korning, korning_lika):
    # Byggsessionens prov: 003 och 009 (samma belopp i kopian) båda med 'belopp_ore' i debet på 2440, en enda rad på
    # bankkontot i kredit med det beloppet (bankrad 26), och 009:s delar i kredit så att det går ihop. Varje
    # bankkontorad räknas bara en gång: rad 1 får rad 3, och rad 2 stoppas.
    tre, nio = underlaget(korning_lika, PROV_B), underlaget(korning_lika, ANDRA)
    momsrad, bankraden = momsraden(nio, 12), korning_lika.bankrad(2, 26)
    skulder, bank = roll(korning_lika, LEVERANTORSSKULDER), roll(korning_lika, BANK)
    text = stoppas(korning_lika, forslag_med(korning_lika, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, nio["belopp_ore"], 0, "lika", kalla(ANDRA, "belopp_ore")),
        rad(bank, 0, tre["belopp_ore"], "lika", bankkalla(bankraden)),
        rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(ANDRA, "underlag_ore", 12)),
        rad(roll(korning_lika, INGAENDE_MOMS), 0, momsrad["moms_ore"], "lika", kalla(ANDRA, "moms_ore", 12)),
    ], "Delad bankkontorad", bankraden["transaktionsdag"], [PROV_B, ANDRA], [bankraden]),
        "ursprung", "rad 2 (konto " + skulder + ")", "'" + ANDRA + "'", "'belopp_ore'", "i debet",
        "rad 3 (konto " + bank + ")", "rad 1", "Öppet 36")
    assert "Öppet 35" not in text


def test_o36_ordningen_oppet_35_provas_fore_oppet_36(korning):
    # Utan någon bankrad alls är felet fortfarande Öppet 35:s (h1 i granskning 27), inte Öppet 36:s.
    tre = underlaget(korning, PROV_B)
    momsrad = momsraden(tre, 12)
    text = stoppas(korning, forslag_for_hand(korning, PROV_B, [
        rad(roll(korning, LEVERANTORSSKULDER), tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad("4010", 0, momsrad["underlag_ore"], "lika", kalla(PROV_B, "underlag_ore", 12)),
        rad(roll(korning, INGAENDE_MOMS), 0, momsrad["moms_ore"], "lika", kalla(PROV_B, "moms_ore", 12)),
    ], "h1 i granskning 27"), "ursprung", "ingen bankrad", "Öppet 35")
    assert "Öppet 36" not in text


# --- Rätt förslag godtas: flödena och förslag för hand med rätt form ---

def test_skydd_fakturan_och_betalningen_for_hand_godtas(korning):
    # Skydd (grönt också före rättelsen): fakturan (beloppet i kredit) och betalningen (beloppet i debet, bankraden
    # på bankkontot i kredit med samma belopp).
    assert skapa(korning, prov_b_003(korning)).kontroller == ALLA_KONTROLLER
    assert skapa(korning, betalningen_for_hand(korning)).kontroller == ALLA_KONTROLLER


def test_skydd_tva_betalningar_i_ett_forslag_med_var_sin_bankkontorad_godtas(korning):
    # Skydd (grönt också före rättelsen): 003:s och 009:s betalningar i samma förslag, var och en med sin egen rad på
    # bankkontot (bankrad 26 och 84 i februari). Två rader med 'belopp_ore' i debet, två rader på bankkontot.
    tre, nio = underlaget(korning, PROV_B), underlaget(korning, ANDRA)
    tjugosex, attiofyra = korning.bankrad(2, 26), korning.bankrad(2, 84)
    skulder, bank = roll(korning, LEVERANTORSSKULDER), roll(korning, BANK)
    forslag = skapa(korning, forslag_med(korning, PROV_B, [
        rad(skulder, tre["belopp_ore"], 0, "lika", kalla(PROV_B, "belopp_ore")),
        rad(skulder, nio["belopp_ore"], 0, "lika", kalla(ANDRA, "belopp_ore")),
        rad(bank, 0, tre["belopp_ore"], "lika", bankkalla(tjugosex)),
        rad(bank, 0, nio["belopp_ore"], "lika", bankkalla(attiofyra)),
    ], "Två betalningar", attiofyra["transaktionsdag"], [PROV_B, ANDRA], [tjugosex, attiofyra]))
    assert forslag.kontroller == ALLA_KONTROLLER


def test_skydd_flode_a_b_och_e_gar_igenom(korning):
    # Skydd (grönt också före rättelsen): fakturan och betalningen för 003, kvittot 015 och bankavgiften (bankrad
    # 117 i januari, utan underlag) går igenom utan ärenden.
    fakturan, betalningen = korning.forslag_for(PROV_B)
    assert fakturan.kontroller == betalningen.kontroller == ALLA_KONTROLLER
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    assert kvittot.kontroller == ALLA_KONTROLLER
    avgiften = korning.bankrad(1, 117)
    bankavgiften, = [post for post in korning.resultat.forslag
                     if [bankrad["id"] for bankrad in post.kopplingar["bankrader"]] == [avgiften["id"]]]
    assert bankavgiften.kopplingar["underlag"] == [] and bankavgiften.kontroller == {"K2": "ok", "ursprung": "ok"}
    assert korning.arenden_for(PROV_B) == [] and korning.arenden_for("SYNT-U-2025-015") == []


# --- Dokumentationen i koden ---

def test_koden_namner_regeln():
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 36" in kod and "granskning 28" in kod and "Hugos beslut 2026-11-04" in kod
    assert "Ö8" in kod
