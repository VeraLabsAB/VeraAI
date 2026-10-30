"""Tester för Hugos beslut 2026-10-30 om granskning 25 (GRANSKNING.md, "Hugos beslut 2026-10-30 om granskning 25").

- Öppet 32 (granskning 25, P7): kostnadsraden i ett förslag med underlag ska stå på det konto som K5 räknar fram för
  underlagets momssats. Annat konto stoppar förslaget, också ett annat konto som står i regeln (fel konto inom regeln)
  och ett konto som har en roll i kontoplanen (till exempel leverantörsskulderna 2440). Granskarens två prov:
  (a) R-LEV-KAFFE får två konton i en kopia av regelboken (livsmedel på 4010, ovrigt på 5460), flödet bokför
  SYNT-U-2025-020 rätt (12 % på 4010, 25 % på 5460), men ett förslag för hand med kontona bytta godtogs förut med alla
  fem kontrollerna "ok". (b) SYNT-U-2025-003 under sin egen regel R-LEV-TE med kostnaden på 2440 i stället för 4010
  godtogs också. Skälet: ursprungskontrollen punkt 8 godtar varje konto som står i regeln eller har en roll, och
  kontot K5 räknade fram (kontrollera_underlag, 'konton') prövades aldrig mot raderna.
- Beslut 2: Öppet 31 räknas som granskad och klar. Ingen kod.
- Flödena a, b och e bygger kostnadsraderna ur K5:s konton (konteringsfloden._kostnad_och_moms), så deras förslag
  går igenom som förut. De testerna är skydd och var gröna också före rättelsen.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot en kopia av 7c1f148 (koden före rättelsen), se PROGRESS.md.
"""

import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_konteringsfloden import Korning, regelbok_med  # noqa: E402
from test_beslut_granskning_22 import skapa, stoppas  # noqa: E402
from test_beslut_granskning_23 import forslag_prov_b, momsfil_med_varugruppen_kostnad, rad  # noqa: E402

PROV_A = "SYNT-U-2025-020"  # två momssatser, egen regel R-LEV-KAFFE
PROV_B = "SYNT-U-2025-003"  # en momssats, egen regel R-LEV-TE med kostnaden på 4010
ALLA_KONTROLLER = {"K2": "ok", "ursprung": "ok", "K5": "ok", "K7": "ok", "K8": "ok"}


def tva_konton(regelbok):
    """Granskarens regelbok i prov (a): R-LEV-KAFFE med livsmedel på 4010 och ovrigt på 5460."""
    regel, = [post for post in regelbok["regler"] if post["id"] == "R-LEV-KAFFE"]
    regel["kontering"] = {"livsmedel": "4010", "ovrigt": "5460"}


@pytest.fixture(scope="module")
def korning():
    return Korning()


@pytest.fixture(scope="module")
def korning_b(tmp_path_factory):
    """Granskarens momsfil från prov B i granskning 23, där 'kostnad' är en varugrupp med 12 %."""
    return Korning(momssatser=momsfil_med_varugruppen_kostnad(tmp_path_factory.mktemp("prov_b")))


@pytest.fixture(scope="module")
def korning_tva(tmp_path_factory):
    return Korning(regelbok=regelbok_med(tmp_path_factory.mktemp("tva_konton"), tva_konton))


@pytest.fixture(scope="module")
def korning_tva_b(tmp_path_factory):
    mapp = tmp_path_factory.mktemp("tva_konton_prov_b")
    return Korning(regelbok=regelbok_med(mapp, tva_konton), momssatser=momsfil_med_varugruppen_kostnad(mapp))


def forslag_med_kontona(korning, id_, konto_for_sats):
    """Ett förslag för underlaget id_ under dess egen regel, byggt för hand förbi flödena, med kostnaden per momssats
    på kontot i konto_for_sats, momsen på kontot för ingående moms och beloppet på leverantörsskulderna.

    Med rätt konton är det samma förslag som flödet a bygger för fakturan. Raderna går ihop (K2), varje belopp har sitt
    ursprung, regeln är underlagets egen (Öppet 31) och varje konto står i regeln eller har en roll (punkt 8), så det
    enda som kan stoppa förslaget är kontot på kostnadsraden (Öppet 32).
    """
    underlag, = [post for post in korning.underlagsperiod.underlag if post["id"] == id_]
    regelbok, kontoplan, datum = korning.regelbok, korning.kontoplan, underlag["datum"]
    regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], datum)
    rader = []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        for konto, falt in ((konto_for_sats[sats], "underlag_ore"),
                            (kontoplan.rollens_konto("ingaende_moms", datum), "moms_ore")):
            if momsrad[falt]:
                rader.append(rad(konto, momsrad[falt], 0, {"kalla": "underlag", "id": id_, "falt": falt,
                                                            "momssats": sats}))
    rader.append(rad(kontoplan.rollens_konto("leverantorsskulder", datum), 0, underlag["belopp_ore"],
                     {"kalla": "underlag", "id": id_, "falt": "belopp_ore"}))
    mot = regelbok.kontrollerad_mot
    return {
        "forslag_id": "F-PROV-O32-" + id_,
        "verifikation": {"datum": datum, "text": "Prov för Öppet 32, underlag " + id_, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_}], "bankrader": [], "z_rapporter": [],
                       "regel": {"id": regel["id"], "regelbokens_kontrollsumma": regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": "Byggt för hand i testet för Öppet 32, förbi flödena.",
    }


def kostnadskonton(forslag):
    """{momssats: konto} för raderna i förslaget som har ett underlags 'underlag_ore' som källa."""
    return {kalla["momssats"]: rad_["konto"] for rad_ in forslag.verifikation["rader"]
            for kalla in rad_["ursprung"]["fran"] if kalla["kalla"] == "underlag" and kalla["falt"] == "underlag_ore"}


# --- Öppet 32: granskarens prov (a), fel konto inom regeln ---

@pytest.mark.parametrize("vilken", ["korning_tva", "korning_tva_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o32_granskarens_prov_a_kontona_bytta_inom_regeln_stoppas(request, vilken):
    # 020 har 12 % (livsmedel, 4010) och 25 % (ovrigt, 5460) i granskarens regelbok. Med kontona bytta står båda
    # kostnadsraderna på ett konto som står i regeln, så punkt 8 godtar dem, och K5 godtar satserna. Förut godtogs
    # förslaget med alla kontrollerna "ok". Nu stoppas det, och felet säger vilket konto K5 ger och vilket raden står på.
    korning = request.getfixturevalue(vilken)
    text = stoppas(korning, forslag_med_kontona(korning, PROV_A, {12: "5460", 25: "4010"}), "ursprung",
                   "'" + PROV_A + "'", "12 %", "K5 ger kontot 4010", "står på kontot 5460", "'R-LEV-KAFFE'",
                   "2025-02-24", "Öppet 32")
    assert "fel momssats" not in text


@pytest.mark.parametrize("vilken", ["korning_tva", "korning_tva_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o32_flodet_bokfor_020_ratt_med_tva_konton_i_regeln(request, vilken):
    # Skydd (grönt också före rättelsen): flöde a bygger kostnadsraderna ur K5:s konton, så fakturan för 020 får
    # 12 % på 4010 och 25 % på 5460, och samma förslag byggt för hand med rätt konton godtas.
    korning = request.getfixturevalue(vilken)
    fakturan = korning.forslag_for(PROV_A)[0]
    assert fakturan.forslag_id == "F-FAKTURA-" + PROV_A and kostnadskonton(fakturan) == {12: "4010", 25: "5460"}
    for_hand = skapa(korning, forslag_med_kontona(korning, PROV_A, {12: "4010", 25: "5460"}))
    assert for_hand.kontroller == ALLA_KONTROLLER and for_hand.verifikation["rader"] == fakturan.verifikation["rader"]


# --- Öppet 32: granskarens prov (b), kostnaden på ett rollkonto ---

@pytest.mark.parametrize("vilken", ["korning", "korning_b"], ids=["testbutikens_momsfil", "prov_b_momsfil"])
def test_o32_granskarens_prov_b_kostnaden_pa_leverantorsskulderna_stoppas(request, vilken):
    # 003 under sin egen regel R-LEV-TE, men kostnaden på leverantörsskulderna (rollen i kontoplanen) i stället för
    # 4010: verifikationen blir 2440 debet, 2641 debet, 2440 kredit. Punkt 8 godtar kontot eftersom det har en roll.
    # Förut godtogs förslaget med alla kontrollerna "ok". Nu stoppas det.
    korning = request.getfixturevalue(vilken)
    skulder = korning.kontoplan.rollens_konto("leverantorsskulder", "2025-01-07")
    text = stoppas(korning, forslag_med_kontona(korning, PROV_B, {12: skulder}), "ursprung", "'" + PROV_B + "'",
                   "12 %", "K5 ger kontot 4010", "står på kontot " + skulder, "'R-LEV-TE'", "2025-01-07", "Öppet 32")
    assert "roll i kontoplanen" in text


def test_o32_ett_forslag_med_ratt_konto_godtas(korning, korning_b):
    # Skydd (grönt också före rättelsen): samma underlag med kostnaden på kontot K5 ger går igenom med alla
    # kontrollerna, med båda momsfilerna.
    for en in (korning, korning_b):
        forslag = skapa(en, forslag_med_kontona(en, PROV_B, {12: "4010"}))
        assert forslag.kontroller == ALLA_KONTROLLER and kostnadskonton(forslag) == {12: "4010"}


# --- Ordningen: K5, K7, K8 och Öppet 31 prövas före den nya kontrollen ---

def test_o32_prov_b_019_och_028_stoppas_fortfarande_av_k5_och_k8_forst(korning_b):
    # Skydd (grönt också före rättelsen): prov B från granskning 23 stoppas med samma kontroll som förut.
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-019"), "K5", "R-BUTIK-STAD")
    stoppas(korning_b, forslag_prov_b(korning_b, "SYNT-U-2025-028"), "K8", "R-RESTAURANG-1")


def test_o32_granskarens_prov_fran_granskning_24_stoppas_fortfarande_av_oppet_31(korning):
    # Skydd (grönt också före rättelsen): 003 under bankregeln med kostnaden på 6570 stoppas av Öppet 31 (fel regel),
    # innan kontot på kostnadsraden prövas.
    text = stoppas(korning, forslag_prov_b(korning, PROV_B), "ursprung", "Öppet 31", "'R-BANK-AVGIFT'")
    assert "Öppet 32" not in text


# --- Flödena a, b och e går igenom: kostnadsraderna byggs ur K5:s konton ---

def test_o32_flode_a_fakturan_och_betalningen_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde a: fakturan med kostnaden på 4010, och betalningen utan kostnadsrad.
    fakturan, betalningen = korning.forslag_for(PROV_B)
    assert (fakturan.forslag_id, betalningen.forslag_id) == ("F-FAKTURA-" + PROV_B, "F-BETALNING-" + PROV_B)
    assert kostnadskonton(fakturan) == {12: "4010"} and kostnadskonton(betalningen) == {}
    assert fakturan.kontroller == betalningen.kontroller == ALLA_KONTROLLER
    assert korning.arenden_for(PROV_B) == []


def test_o32_flode_b_kvittot_gar_igenom(korning):
    # Skydd (grönt också före rättelsen). Flöde b: kvittot 015 under R-BUTIK-FORBRUKNING med kostnaden på 5460.
    kvittot, = korning.forslag_for("SYNT-U-2025-015")
    assert kvittot.forslag_id == "F-KVITTO-SYNT-U-2025-015" and kvittot.kontroller == ALLA_KONTROLLER
    assert kostnadskonton(kvittot) == {25: "5460"}
    assert korning.arenden_for("SYNT-U-2025-015") == []


def test_o32_flode_e_bankavgiften_gar_igenom_utan_underlag(korning):
    # Skydd (grönt också före rättelsen). Flöde e: bankrad 117 i januari under R-BANK-AVGIFT, utan underlag. Den
    # nya kontrollen gäller bara rader med ett underlag som källa, så ett förslag utan underlag berörs inte.
    rad_ = korning.bankrad(1, 117)
    forslag, = [post for post in korning.resultat.forslag
                if [bankrad["id"] for bankrad in post.kopplingar["bankrader"]] == [rad_["id"]]]
    assert forslag.forslag_id == "F-BANKRAD-" + rad_["id"] and forslag.kopplingar["underlag"] == []
    assert forslag.kopplingar["regel"]["id"] == "R-BANK-AVGIFT" and forslag.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_o32_varje_kostnadsrad_i_flodena_star_pa_kontot_k5_ger(korning):
    # Skydd (grönt också före rättelsen): i hela körningen står varje rad med ett underlags 'underlag_ore' som källa
    # på det konto kontrollera_underlag ger för satsen, mot underlagets egen regel. Det är därför flödena inte berörs.
    from konteringsforslag import kontrollera_underlag

    underlagen = {post["id"]: post for post in korning.underlagsperiod.underlag}
    med_kostnadsrad = [forslag for forslag in korning.resultat.forslag if kostnadskonton(forslag)]
    assert med_kostnadsrad
    for forslag in med_kostnadsrad:
        for rad_ in forslag.verifikation["rader"]:
            for kalla in rad_["ursprung"]["fran"]:
                if kalla["kalla"] != "underlag" or kalla["falt"] != "underlag_ore":
                    continue
                underlag = underlagen[kalla["id"]]
                egen = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
                konton = kontrollera_underlag(underlag, egen, korning.regelbok, korning.momssatser).konton
                assert rad_["konto"] == konton[kalla["momssats"]], forslag.forslag_id


# --- Dokumentationen ---

def test_o32_spec_och_koden_namner_regeln():
    spec = (AGENT / "SPEC.md").read_text(encoding="utf-8")
    assert "Öppet 32" in spec and "granskning 25" in spec
    kod = (AGENT / "scripts" / "konteringsforslag.py").read_text(encoding="utf-8")
    assert "Öppet 32" in kod
