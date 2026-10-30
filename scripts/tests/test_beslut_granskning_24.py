"""Tester för Hugos beslut 2026-10-30 om granskning 24 (GRANSKNING.md, "Hugos beslut 2026-10-30 om granskning 24").

- Öppet 31 (granskning 24, P5): skapa_konteringsforslag stoppar ett förslag med underlag när förslagets regel (den i
  'kopplingar') inte är underlagets egen regel, den regelboken ger underlaget på underlagets datum. Granskarens prov:
  SYNT-U-2025-003 (12 %, egen regel R-LEV-TE med kostnaden på 4010) byggt för hand under bankregeln R-BANK-AVGIFT med
  kostnaden på bankregelns konto 6570 och bankrad 117 i januari som avgift. Förut godtogs förslaget med alla
  kontroller "ok": K5 prövade satsen mot R-LEV-TE, men kontot prövades av ursprungskontrollen punkt 8 mot
  förslagets regel, där 6570 står. Det var den enda vägen kvar där ett förslag med underlag bokför kostnaden på fel
  konto med alla kontroller gröna. Nu stoppas det.
- Flödena a, b och e bygger alltid med underlagets egen regel (flöde e har inget underlag), så deras förslag går
  igenom som förut. De testerna är skydd och var gröna också före rättelsen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot en kopia av 6dfcdcd (koden före rättelsen), se PROGRESS.md.
"""

import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_konteringsfloden import Korning  # noqa: E402
from test_beslut_granskning_22 import forslag_for_hand, skapa, stoppas  # noqa: E402
from test_beslut_granskning_23 import forslag_prov_b, momsfil_med_varugruppen_kostnad  # noqa: E402

PROVET = "SYNT-U-2025-003"
EGEN_REGEL = "R-LEV-TE"
BANKREGEL = "R-BANK-AVGIFT"
ALLA_KONTROLLER = {"K2": "ok", "ursprung": "ok", "K5": "ok", "K7": "ok", "K8": "ok"}


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_b(tmp_path_factory):
    """Granskarens momsfil från prov B i granskning 23, där 'kostnad' är en varugrupp med 12 %."""
    return Korning(momssatser=momsfil_med_varugruppen_kostnad(tmp_path_factory.mktemp("prov_b")))


# --- Öppet 31: förslagets regel ska vara underlagets egen regel ---

@pytest.mark.parametrize("vilken", ["korning", "korning_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o31_granskarens_prov_003_under_bankregeln_stoppas(request, vilken):
    # 003:s egen regel R-LEV-TE godtar 12 %, så K5 säger "ok", och R-LEV-TE är inte avdragsbegränsad, så K8 säger
    # "ok". Förut godtogs förslaget fast kostnaden står på 6570, bankregelns konto. Nu stoppas det, med båda
    # reglerna i felet, och felet säger att det är regeln som är fel, inte momsen.
    korning = request.getfixturevalue(vilken)
    text = stoppas(korning, forslag_prov_b(korning, PROVET), "ursprung", "'" + PROVET + "'", "'" + EGEN_REGEL + "'",
                   "'" + BANKREGEL + "'", "2025-01-07", "underlagets egen regel")
    assert "K5" not in text and "momssats" not in text


def test_o31_felet_namner_forslagets_regel_som_den_i_kopplingar(korning):
    text = stoppas(korning, forslag_prov_b(korning, PROVET), "ursprung")
    assert "'kopplingar'" in text and "Öppet 31" in text


def test_o31_prov_b_019_och_028_stoppas_fortfarande_av_k5_och_k8_forst(korning_b):
    # Den nya kontrollen prövas efter K5, K7 och K8, så prov B från granskning 23 stoppas med samma kontroll och
    # samma text som förut: 019 av K5 (fel momssats mot R-BUTIK-STAD) och 028 av K8 (R-RESTAURANG-1 är
    # avdragsbegränsad). Testerna i test_beslut_granskning_23.py gäller alltså oförändrade.
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-019"), "K5", "R-BUTIK-STAD")
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-028"), "K8", "R-RESTAURANG-1")


def test_o31_ett_forslag_for_hand_under_underlagets_egen_regel_godtas(korning, korning_b):
    # Skydd (grönt också före rättelsen): samma underlag under sin egen regel, med kostnaden på regelns konto, går
    # igenom med alla kontrollerna.
    for en in (korning, korning_b):
        forslag = skapa(en, forslag_for_hand(en, PROVET))
        assert forslag.kontroller == ALLA_KONTROLLER and forslag.kopplingar["regel"]["id"] == EGEN_REGEL


# --- Flödena a, b och e går igenom: regeln är underlagets egen ---

def test_o31_flode_a_fakturan_och_betalningen_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde a: fakturan på underlagets datum och betalningen på bankens datum,
    # båda med underlagets egen regel.
    fakturan, betalningen = korning.forslag_for(PROVET)
    assert (fakturan.forslag_id, betalningen.forslag_id) == ("F-FAKTURA-" + PROVET, "F-BETALNING-" + PROVET)
    assert fakturan.kopplingar["regel"]["id"] == betalningen.kopplingar["regel"]["id"] == EGEN_REGEL
    assert fakturan.kontroller == betalningen.kontroller == ALLA_KONTROLLER
    assert korning.arenden_for(PROVET) == []


def test_o31_flode_b_kvittot_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde b: kvittot 015 med sin egen regel R-BUTIK-FORBRUKNING.
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    assert kvittot.forslag_id == "F-KVITTO-SYNT-U-2025-015"
    assert kvittot.kopplingar["regel"]["id"] == "R-BUTIK-FORBRUKNING" and kvittot.kontroller == ALLA_KONTROLLER
    assert korning.arenden_for("SYNT-U-2025-015") == []


def test_o31_flode_e_bankavgiften_gar_igenom_utan_underlag(korning):
    # Skydd (grönt också före rättelsen). Flöde e: bankrad 117 i januari under R-BANK-AVGIFT, utan underlag. Den
    # nya kontrollen gäller bara underlag, så ett förslag utan underlag berörs inte.
    rad = korning.bankrad(1, 117)
    forslag, = [post for post in korning.resultat.forslag
                if [bankrad["id"] for bankrad in post.kopplingar["bankrader"]] == [rad["id"]]]
    assert forslag.forslag_id == "F-BANKRAD-" + rad["id"] and forslag.kopplingar["underlag"] == []
    assert forslag.kopplingar["regel"]["id"] == BANKREGEL and forslag.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_o31_varje_forslag_med_underlag_i_flodena_har_underlagets_egen_regel(korning):
    # Skydd (grönt också före rättelsen): i hela körningen är förslagets regel underlagets egen regel på
    # underlagets datum, för varje underlag i varje förslag. Det är därför flödena inte berörs av den nya kontrollen.
    underlagen = {post["id"]: post for post in korning.underlagsperiod.underlag}
    med_underlag = [forslag for forslag in korning.resultat.forslag if forslag.kopplingar["underlag"]]
    assert med_underlag
    for forslag in med_underlag:
        for post in forslag.kopplingar["underlag"]:
            underlag = underlagen[post["id"]]
            egen = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
            assert egen["id"] == forslag.kopplingar["regel"]["id"], forslag.forslag_id


# --- Dokumentationen ---

def test_o31_spec_och_koden_sager_att_forslagets_regel_ska_vara_underlagets():
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "Öppet 31" in spec and "granskning 24" in spec
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 31" in kod
