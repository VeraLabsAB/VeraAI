"""Tester för Hugos beslut 2026-10-30 om granskning 22 (GRANSKNING.md, "Hugos beslut 2026-10-30 om granskning 22").

- P1: kontrollerna K5, K7 och K8 ligger i skapa_konteringsforslag, så att ingen kod kan få ett förslag för ett
  underlag utan att de har körts. Flödena anropar dem inte för sig: de frågar kontrollera_underlag (samma kod) för
  att göra ärenden, och förslaget kör kontrollerna igen.
- P2: ett underlag som K4 (dubbletter: K4, K4a, K4b eller K4c) har flaggat får inget förslag alls, och K4-ärendet
  följer med i resultatet från kontera_period.
- Öppet 27: reserverade ord stoppar alla namn i konfigurationen, men bara vid exakt träff (efter normaliseringen),
  inte som delsträng.
- Öppet 28: 'flode' stoppas på en regel för pengar in.

Allt körs mot testbutikens SYNTETISKA konfiguration och testdatan för 2025-Q1. Allt som ändras skrivs i testets
tillfälliga mapp. Testerna var röda mot en kopia av 7d8cae9 (koden före rättelsen), se PROGRESS.md.
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

from las_bank import BankfilFel, ladda_bankformat  # noqa: E402
from las_kassa import KassafilFel, ladda_kassaformat  # noqa: E402
from las_kontoplan import KontoplanFel, las_kontoplan  # noqa: E402
from las_momssatser import MomssatsFel, las_momssatser  # noqa: E402
from las_regelbok import RegelbokFel  # noqa: E402
from konteringsforslag import KonteringsforslagFel, skapa_konteringsforslag  # noqa: E402
from konteringsfloden import ARENDE_NYCKLAR  # noqa: E402
from test_konteringsfloden import Korning, regelbok_med  # noqa: E402

RESERVERAT = "bankavgift"


def las_json(namn):
    return json.loads((TESTBUTIKEN / namn).read_text(encoding="utf-8"))


def skriv(tmp_path, namn, data):
    fil = tmp_path / namn
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return fil


@pytest.fixture(scope="module")
def korning():
    return Korning()


# --- P1: ett förslag byggt för hand, förbi flödena ---

def forslag_for_hand(korning, id_, regelbok=None):
    """Ett förslag för underlaget id_, byggt direkt utan flödena: kostnaden och momsen i debet, beloppet i kredit.

    Så byggde granskaren sitt prov i granskning 22 (P1). Raderna går ihop (K2) och varje belopp har sitt ursprung,
    så förut godtogs förslaget fast underlaget är ett K5- eller K8-ärende.
    """
    regelbok = korning.regelbok if regelbok is None else regelbok
    underlag, = [post for post in korning.underlagsperiod.underlag if post["id"] == id_]
    regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
    kontoplan, datum = korning.kontoplan, underlag["datum"]
    kostnad = sorted(regel["kontering"].values())[0]
    rader = []
    for momsrad in underlag["moms"]:
        for konto, falt in ((kostnad, "underlag_ore"), (kontoplan.rollens_konto("ingaende_moms", datum), "moms_ore")):
            if momsrad[falt]:
                rader.append({"konto": konto, "debet_ore": momsrad[falt], "kredit_ore": 0, "ursprung": {
                    "berakning": "lika",
                    "fran": [{"kalla": "underlag", "id": id_, "falt": falt, "momssats": momsrad["momssats"]}]}})
    rader.append({"konto": kontoplan.rollens_konto("leverantorsskulder", datum), "debet_ore": 0,
                  "kredit_ore": underlag["belopp_ore"],
                  "ursprung": {"berakning": "lika", "fran": [{"kalla": "underlag", "id": id_, "falt": "belopp_ore"}]}})
    mot = regelbok.kontrollerad_mot
    return {
        "forslag_id": "F-PROV-" + id_,
        "verifikation": {"datum": datum, "text": "Prov för P1, underlag " + id_, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_}], "bankrader": [], "z_rapporter": [],
                       "regel": {"id": regel["id"], "regelbokens_kontrollsumma": regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": "Byggt för hand i testet för P1, förbi flödena.",
    }


def skapa(korning, forslag, **andrat):
    allt = {"momssatser": korning.momssatser, "underlagsperiod": korning.underlagsperiod,
            "bankperiod": korning.bankperiod, **andrat}
    return skapa_konteringsforslag(forslag, korning.regelbok, korning.kontoplan, **allt)


def stoppas(korning, forslag, kontroll, *texter, **andrat):
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa(korning, forslag, **andrat)
    assert fel.value.kontroll == kontroll, str(fel.value)
    for text in texter:
        assert text in str(fel.value), str(fel.value)
    return str(fel.value)


def test_p1_granskarens_prov_ett_forslag_utan_momsfil_for_019_stoppas(korning):
    # Granskarens prov i granskning 22: skapa_konteringsforslag direkt, utan momsfilen, för SYNT-U-2025-019 (K5).
    # Förut kom ett godkänt Konteringsforslag tillbaka. Nu stoppas det: utan momsfilen kan K5 inte köras.
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_konteringsforslag(forslag_for_hand(korning, "SYNT-U-2025-019"), korning.regelbok, korning.kontoplan,
                                underlagsperiod=korning.underlagsperiod, bankperiod=korning.bankperiod)
    assert fel.value.kontroll == "indata" and "fick ingen momsfil" in str(fel.value)
    assert "K5" in str(fel.value)


def test_p1_k5_stoppar_ett_forslag_byggt_for_hand(korning):
    # SYNT-U-2025-019 har 12 % moms, men regeln R-BUTIK-STAD väntar sig 25 % (DESIGN 6). Nivå D, inget förslag.
    text = stoppas(korning, forslag_for_hand(korning, "SYNT-U-2025-019"), "K5", "'SYNT-U-2025-019'", "fel momssats",
                   "12 %", "Det ska vara ett ärende")
    assert text.startswith("Konteringsförslaget skapas inte (K5): ")


def test_p1_k8_stoppar_ett_forslag_byggt_for_hand(korning):
    # SYNT-U-2025-028 har regeln R-RESTAURANG-1, som är avdragsbegränsad (K8).
    stoppas(korning, forslag_for_hand(korning, "SYNT-U-2025-028"), "K8", "'SYNT-U-2025-028'", "avdragsbegränsad",
            "R-RESTAURANG-1", "Det ska vara ett ärende")


def test_p1_k7_stoppar_ett_forslag_byggt_for_hand(tmp_path):
    # Ett påhittat underlag från ägaren AGARE-1, med en regel för ägaren (nivå D, som regelboken kräver).
    mapp = tmp_path / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    fil = mapp / "SYNT-U-2025-003.json"
    data = json.loads(fil.read_text(encoding="utf-8"))
    data["motpart"] = "AGARE-1"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def med_agarregel(regelbok):
        regelbok["regler"].append({"id": "R-AGARE", "galler": {"kalla": "underlag", "typ": "leverantorsfaktura",
                                                               "motpart": "AGARE-1"},
                                   "kontering": {"livsmedel": "4010"}, "villkor": {"giltig_fran": "2025-01-01"},
                                   "niva": "D"})
    korning = Korning(regelbok=regelbok_med(tmp_path, med_agarregel), underlag=mapp)
    stoppas(korning, forslag_for_hand(korning, "SYNT-U-2025-003"), "K7", "ägare eller närstående",
            "Det ska vara ett ärende")
    # Flödena gör samma bedömning: ett K7-ärende och inget förslag.
    assert [arende["kontroll"] for arende in korning.arenden_for("SYNT-U-2025-003")] == ["K7"]
    assert korning.forslag_for("SYNT-U-2025-003") == []


def test_p1_ett_godkant_underlag_far_ett_forslag_som_visar_alla_kontrollerna(korning):
    forslag = skapa(korning, forslag_for_hand(korning, "SYNT-U-2025-003"))
    assert forslag.kontroller == {"K2": "ok", "ursprung": "ok", "K5": "ok", "K7": "ok", "K8": "ok"}
    # Flödenas förslag för underlag visar samma kontroller, och förslag utan underlag bara K2 och ursprunget.
    for forslag in korning.resultat.forslag:
        if forslag.kopplingar["underlag"]:
            assert forslag.kontroller == {"K2": "ok", "ursprung": "ok", "K5": "ok", "K7": "ok", "K8": "ok"}
        else:
            assert forslag.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_p1_ett_forslag_utan_underlag_behover_ingen_momsfil(korning):
    # Bankavgiften (flöde e) bygger bara på en bankrad. K5, K7 och K8 gäller underlag.
    rad = korning.bankrad(1, 117)
    bankavgiften, = [forslag for forslag in korning.resultat.forslag
                     if [post["id"] for post in forslag.kopplingar["bankrader"]] == [rad["id"]]]
    mot = korning.regelbok.kontrollerad_mot
    forslag = {
        "forslag_id": "F-PROV-BANKRAD", "verifikation": {"datum": rad["transaktionsdag"], "text": "Prov", "rader": [
            {"konto": "6570", "debet_ore": 12500, "kredit_ore": 0,
             "ursprung": {"berakning": "lika", "fran": [{"kalla": "bankrad", "id": rad["id"], "falt": "belopp_ore"}]}},
            {"konto": "1940", "debet_ore": 0, "kredit_ore": 12500,
             "ursprung": {"berakning": "lika", "fran": [{"kalla": "bankrad", "id": rad["id"], "falt": "belopp_ore"}]}},
        ]},
        "kopplingar": {"underlag": [], "bankrader": [{"id": rad["id"]}], "z_rapporter": [],
                       "regel": {"id": bankavgiften.kopplingar["regel"]["id"],
                                 "regelbokens_kontrollsumma": korning.regelbok.kontrollsumma,
                                 "kontoplanens_kontrollsumma": korning.kontoplan.kontrollsumma,
                                 "momsfilens_kontrollsumma": mot["momssatser"],
                                 "matchningsformatets_kontrollsumma": mot["matchningsformat"]}},
        "motivering": "Byggt för hand i testet för P1.",
    }
    assert skapa(korning, forslag, momssatser=None, underlagsperiod=None).kontroller == {"K2": "ok", "ursprung": "ok"}


def test_p1_en_annan_momsfil_an_regelbokens_stoppas(korning, tmp_path):
    fil = tmp_path / "momssatser.json"
    fil.write_bytes((TESTBUTIKEN / "momssatser.json").read_bytes() + b" ")
    stoppas(korning, forslag_for_hand(korning, "SYNT-U-2025-003"), "K2",
            "momsfilen är inte den som regelboken kontrollerades mot", momssatser=las_momssatser(fil))


@pytest.mark.parametrize("varde, text", [({}, "momsfilen ska komma från las_momssatser, inte vara dict"),
                                         ("tom", "momsfilen är tom eller trasig")])
def test_p1_en_momsfil_som_inte_kommer_fran_inlasningen_stoppas(korning, varde, text):
    from las_momssatser import Momssatser

    momssatser = object.__new__(Momssatser) if varde == "tom" else varde
    stoppas(korning, forslag_for_hand(korning, "SYNT-U-2025-003"), "indata", text, momssatser=momssatser)


def test_p1_kontrollera_underlag_ger_samma_svar_som_flodena(korning):
    # Den gemensamma kontrollen som både flödena och skapa_konteringsforslag använder. Importeras här, så att
    # resten av filen går att köra mot koden före rättelsen (rött före).
    from konteringsforslag import kontrollera_underlag

    def kontroll(id_):
        underlag, = [post for post in korning.underlagsperiod.underlag if post["id"] == id_]
        regel = korning.regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
        return kontrollera_underlag(underlag, regel, korning.regelbok, korning.momssatser)

    godkant = kontroll("SYNT-U-2025-003")
    assert godkant.konton == {12: "4010"} and godkant.fynd == ()
    k5 = kontroll("SYNT-U-2025-019")
    assert k5.konton is None and [(fynd.kontroll, fynd.typ) for fynd in k5.fynd] == [("K5", "fel momssats")]
    k8 = kontroll("SYNT-U-2025-028")
    assert k8.konton is None and [(fynd.kontroll, fynd.typ) for fynd in k8.fynd] == [("K8", "avdragsbegränsat")]
    # Flödenas ärenden har samma kontroll, typ och text.
    arende, = korning.arenden_for("SYNT-U-2025-019")
    assert (arende["kontroll"], arende["typ"], arende["text"]) == (k5.fynd[0].kontroll, k5.fynd[0].typ, k5.fynd[0].text)
    arende, = korning.arenden_for("SYNT-U-2025-028")
    assert (arende["kontroll"], arende["typ"], arende["text"]) == (k8.fynd[0].kontroll, k8.fynd[0].typ, k8.fynd[0].text)


# --- P2: K4 ger inget förslag, och K4-ärendet följer med ---

def underlagsmapp_med_kopia(tmp_path, original, nytt_id, andring):
    """En kopia av testdatans underlag, plus en kopia av underlaget original med nytt id och andring gjord."""
    mapp = tmp_path / "underlag"
    shutil.copytree(DATAMAPP / "underlag", mapp)
    data = json.loads((mapp / (original + ".json")).read_text(encoding="utf-8"))
    data["id"] = nytt_id
    andring(data)
    (mapp / (nytt_id + ".json")).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return mapp


def annat_nummer(data):
    data["fakturanummer"] = data["fakturanummer"] + "-B"


def annat_datum(data):
    data["datum"] = "2025-01-08"


def annat_belopp(data):
    # 100 kr mindre utan moms och momsen räknad om med 12 %, så att underlaget går ihop (K13).
    data["moms"][0].update(underlag_ore=1483800, moms_ore=178056)
    data["belopp_ore"] = 1661856


KOPIAN = "SYNT-U-2025-903"


@pytest.mark.parametrize("andring, kontroll, typ", [
    (annat_nummer, "K4c", "möjlig dublett av SYNT-U-2025-003"),
    (annat_datum, "K4b", "samma fakturanummer, olika datum"),
    (annat_belopp, "K4a", "samma fakturanummer, olika belopp"),
], ids=["k4c", "k4b", "k4a"])
def test_p2_ett_underlag_som_k4_flaggar_far_inget_forslag_och_arendet_foljer_med(tmp_path, andring, kontroll, typ):
    mapp = underlagsmapp_med_kopia(tmp_path, "SYNT-U-2025-003", KOPIAN, andring)
    korning = Korning(underlag=mapp)
    # Underlagsperioden behåller båda och har K4-ärendet (som förut).
    assert KOPIAN in [post["id"] for post in korning.underlagsperiod.underlag]
    assert [(post["kontroll"], post["text"]) for post in korning.underlagsperiod.arenden if post["id"] == KOPIAN] == [
        (kontroll, typ)]
    # Nytt: kopian får inget förslag, och K4-ärendet står i resultatet från kontera_period.
    assert korning.forslag_for(KOPIAN) == []
    arende, = korning.arenden_for(KOPIAN)
    assert (arende["kontroll"], arende["typ"], arende["underlag"], arende["regel"]) == (kontroll, typ, KOPIAN, "R-LEV-TE")
    assert "SYNT-U-2025-003" in arende["text"] and "Inget förslag" in arende["text"]
    # Nivån sätts i nivåsteget (DESIGN 5 säger C), och märkningen är inte den för nivå D.
    assert arende["niva"] is None and arende["kraver_mansklig_bedomning"] is False
    assert tuple(arende) == ARENDE_NYCKLAR
    # Originalet får sitt förslag för fakturan. (Betalningen beror på om matchningen blir tvetydig.)
    assert [forslag.forslag_id for forslag in korning.forslag_for("SYNT-U-2025-003")][0] == "F-FAKTURA-SYNT-U-2025-003"


def test_p2_dubbletten_004_har_sitt_k4_arende_i_resultatet(korning):
    # SYNT-U-2025-004 är en dublett av 003 (K4) och tas bort redan i underlagsperioden. Förut försvann ärendet
    # ur resultatet från kontera_period.
    assert "SYNT-U-2025-004" not in [post["id"] for post in korning.underlagsperiod.underlag]
    arende, = korning.arenden_for("SYNT-U-2025-004")
    assert (arende["kontroll"], arende["typ"]) == ("K4", "dublett av SYNT-U-2025-003")
    assert arende["bankrader"] == () and arende["regel"] is None and arende["niva"] is None
    assert korning.forslag_for("SYNT-U-2025-004") == []


def test_p2_alla_k4_arenden_i_perioden_foljer_med(korning):
    i_perioden = [(post["kontroll"], post["id"]) for post in korning.underlagsperiod.arenden]
    assert i_perioden  # skydd: testdatan har minst ett K4-ärende (004)
    i_resultatet = [(arende["kontroll"], arende["underlag"]) for arende in korning.resultat.arenden
                    if arende["kontroll"].startswith("K4")]
    assert i_resultatet == i_perioden


def test_p2_ett_k4_flaggat_underlag_far_bara_k4_arendet(tmp_path):
    # Kopian är en möjlig dublett OCH har fel moms. Bara K4-ärendet görs: svaret på det går sedan genom samma
    # kontroller som ett nytt förslag (SPEC 4).
    def bada(data):
        annat_nummer(data)
        data["moms"][0].update(underlag_ore=1493795, moms_ore=179261)
    korning = Korning(underlag=underlagsmapp_med_kopia(tmp_path, "SYNT-U-2025-003", KOPIAN, bada))
    assert [arende["kontroll"] for arende in korning.arenden_for(KOPIAN)] == ["K4c"]
    assert korning.forslag_for(KOPIAN) == []


# --- Öppet 27: reserverade ord stoppar alla namn i konfigurationen, bara vid exakt träff ---

def regelbok_dar(tmp_path, andring):
    regelbok = las_json("regelbok.json")
    andring(regelbok)
    return skriv(tmp_path, "regelbok.json", regelbok)


def regel(regelbok, regel_id):
    return [post for post in regelbok["regler"] if post["id"] == regel_id][0]


@pytest.mark.parametrize("namn", [RESERVERAT, "Bankavgift", "BANKAVGIFT", "bank avgift"])
def test_o27_en_motpart_med_ett_reserverat_ord_stoppar_regelboken(tmp_path, namn):
    def andring(regelbok):
        regel(regelbok, "R-LEV-TE")["galler"]["motpart"] = namn
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'"):
        Korning(regelbok=regelbok_dar(tmp_path, andring))


def test_o27_ett_kassaregister_i_regelboken_med_ett_reserverat_ord_stoppar_regelboken(tmp_path):
    def andring(regelbok):
        regel(regelbok, "R-Z-TB-KASSA-1")["galler"]["kassaregister"] = "BANKAVGIFT"
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'"):
        Korning(regelbok=regelbok_dar(tmp_path, andring))


def test_o27_en_agare_med_ett_reserverat_ord_stoppar_regelboken(tmp_path):
    def andring(regelbok):
        regelbok["agare_och_narstaende"].append("Bank avgift")
    with pytest.raises(RegelbokFel, match="det reserverade ordet 'bankavgift'"):
        Korning(regelbok=regelbok_dar(tmp_path, andring))


def kassaformat_dar(tmp_path, andring):
    data = las_json("kassaformat.json")
    andring(data)
    return skriv(tmp_path, "kassaformat.json", data)


def satt_kassaregister(data):
    data["kassaregister"] = [RESERVERAT]


def satt_betalsatt(data):
    data["poster"]["betalsatt"][0] = "BANKAVGIFT"


def satt_kolumn(data):
    data["kolumner"]["postnamn"] = "Bankavgift"


def satt_postnamn(data):
    data["poster"]["totalsumma"] = "bank avgift"


@pytest.mark.parametrize("andring", [satt_kassaregister, satt_betalsatt, satt_kolumn, satt_postnamn],
                         ids=["kassaregister", "betalsatt", "kolumn", "postnamn"])
def test_o27_ett_namn_i_kassaformatet_med_ett_reserverat_ord_stoppar_formatet(tmp_path, andring):
    with pytest.raises(KassafilFel, match="det reserverade ordet 'bankavgift'"):
        ladda_kassaformat(kassaformat_dar(tmp_path, andring))


def test_o27_ett_kolumnnamn_i_bankformatet_med_ett_reserverat_ord_stoppar_formatet(tmp_path):
    data = las_json("bankformat.json")
    data["kolumner"]["referens"] = "Bankavgift"
    with pytest.raises(BankfilFel, match="det reserverade ordet 'bankavgift'"):
        ladda_bankformat(skriv(tmp_path, "bankformat.json", data))


def test_o27_ett_kontonamn_med_ett_reserverat_ord_stoppar_kontoplanen(tmp_path):
    data = las_json("kontoplan.json")
    [konto for konto in data["konton"] if konto["nummer"] == "6570"][0]["namn"] = "Bankavgift"
    with pytest.raises(KontoplanFel, match="det reserverade ordet 'bankavgift'"):
        las_kontoplan(skriv(tmp_path, "kontoplan.json", data))


def test_o27_en_varugrupp_med_ett_reserverat_ord_stoppar_momsfilen(tmp_path):
    data = las_json("momssatser.json")
    data["varugrupper"][RESERVERAT] = data["varugrupper"]["livsmedel"]
    with pytest.raises(MomssatsFel, match="det reserverade ordet 'bankavgift'"):
        las_momssatser(skriv(tmp_path, "momssatser.json", data))


def test_o27_bara_exakt_traff_stoppas_inte_delstrang(tmp_path):
    # Namn som bara innehåller eller liknar ordet godtas överallt: "Bankavgift AB", "bankavgifter", "bank-avgift".
    def i_regelboken(regelbok):
        regel(regelbok, "R-LEV-TE")["galler"]["motpart"] = "Bankavgift AB"
        regel(regelbok, "R-Z-TB-KASSA-1")["galler"]["kassaregister"] = "bank-avgift"
        regelbok["agare_och_narstaende"].append("bankavgift-1")
    assert Korning(regelbok=regelbok_dar(tmp_path, i_regelboken)).resultat.forslag

    def i_kassaformatet(data):
        data["kassaregister"] = ["bank-avgift"]
        data["poster"]["betalsatt"][0] = "bankavgifter"
        data["kolumner"]["postnamn"] = "Bankavgift AB"
    assert ladda_kassaformat(kassaformat_dar(tmp_path, i_kassaformatet))["kassaregister"] == ["bank-avgift"]

    bankformat = las_json("bankformat.json")
    bankformat["kolumner"]["referens"] = "Bankavgiften"
    assert ladda_bankformat(skriv(tmp_path, "bankformat.json", bankformat))["kolumner"]["referens"] == "Bankavgiften"

    kontoplan = las_json("kontoplan.json")
    [konto for konto in kontoplan["konton"] if konto["nummer"] == "6570"][0]["namn"] = "Bankavgifter"
    assert las_kontoplan(skriv(tmp_path, "kontoplan.json", kontoplan)).kontots_namn("6570", "2025-01-01") == (
        "Bankavgifter")

    momsfil = las_json("momssatser.json")
    momsfil["varugrupper"]["bankavgifter"] = momsfil["varugrupper"]["livsmedel"]
    assert "bankavgifter" in las_momssatser(skriv(tmp_path, "momssatser.json", momsfil)).varugrupper


def test_o27_de_reserverade_orden_star_pa_ett_stalle():
    # Listan ligger i reserverade_namn.py, som alla inläsningsmoduler använder. Ingen modul har en egen lista.
    import las_regelbok
    import reserverade_namn

    assert reserverade_namn.RESERVERADE_NAMN == (RESERVERAT,)
    assert set(las_regelbok.FLODEN) <= set(reserverade_namn.RESERVERADE_NAMN)
    assert reserverade_namn.reserverat_namn("Bank avgift") == RESERVERAT
    assert reserverade_namn.reserverat_namn("Bankavgift AB") is None
    for modul in ("las_bank", "las_kassa", "las_kontoplan", "las_momssatser", "las_matchningsformat", "las_regelbok"):
        kod = (AGENT / "scripts" / (modul + ".py")).read_text(encoding="utf-8")
        assert "from reserverade_namn import inget_reserverat_namn" in kod, modul
        assert "RESERVERADE_NAMN = " not in kod, modul


def test_o27_readme_sager_vilka_namn_som_provas():
    readme = (AGENT / "foretag" / "README.md").read_text(encoding="utf-8")
    avsnitt = readme.split("### Reserverade namn", 1)[1].split("\n## ", 1)[0]
    for ord_ in ("`" + RESERVERAT + "`", "kontonamn", "varugrupp", "kassaregister", "betalsätt", "kolumnnamn",
                 "motpart", "ägare", "exakt", "Öppet 27"):
        assert ord_ in avsnitt, ord_


# --- Öppet 28: 'flode' stoppas på en regel för pengar in ---

def test_o28_flode_pa_en_regel_for_pengar_in_stoppar_regelboken(tmp_path):
    # R-BANK-SWISH pekar på regeln 'swish' i matchningsformatet, som gäller pengar in (P7 i granskning 22).
    def andring(regelbok):
        swish = regel(regelbok, "R-BANK-SWISH")
        swish["flode"] = "bankavgift"
        swish["kontering"] = {"kostnad": "6570"}
    with pytest.raises(RegelbokFel, match="pengar in") as fel:
        Korning(regelbok=regelbok_dar(tmp_path, andring))
    assert "'flode'" in str(fel.value) and "R-BANK-SWISH" in str(fel.value) and "'swish'" in str(fel.value)


def test_o28_flode_pa_en_regel_for_pengar_ut_godtas_som_forut(korning):
    assert korning.regelbok.regel_for_bankrad("bankens-avgifter", "2025-01-31")["flode"] == "bankavgift"
