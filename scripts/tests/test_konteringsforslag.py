"""Tester för konteringsförslaget (konteringsforslag.py): K2, ursprungskontrollen och att förslaget inte kan ändras.

Förslagen byggs för hand här, med kontona och reglerna i testbutikens SYNTETISKA konfiguration och
källorna ur testdatan för 2025-Q1. Flödena som räknar fram förslagen byggs i nästa steg (DESIGN avsnitt
7, uppgift 4). Exemplen är DESIGN-regelbok.md avsnitt 4a (SYNT-U-2025-003 och dess betalning), 4c
(Z 1001), 4d (kortinlösen) och 4e (bankavgift).
"""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
TESTBUTIKEN = AGENT / "foretag" / "syntet-testbutik"
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"

sys.path.insert(0, str(AGENT / "scripts"))

from las_bank import ladda_bankformat, las_bankfil, sla_ihop_bankperioder  # noqa: E402
from las_kassa import ladda_kassaformat, las_kassaperiod  # noqa: E402
from las_kontoplan import las_kontoplan  # noqa: E402
from las_matchningsformat import las_matchningsformat  # noqa: E402
from las_momssatser import las_momssatser  # noqa: E402
from las_regelbok import las_regelbok  # noqa: E402
from las_underlag import las_underlagsperiod  # noqa: E402
from konteringsforslag import (  # noqa: E402
    FORSLAG_NYCKLAR, Konteringsforslag, KonteringsforslagFel, skapa_konteringsforslag,
)

KASSAREGISTER = "TB-KASSA-1"


# --- Testbutikens konfiguration och perioder ---

class Kallor:
    """Allt som ett förslag kontrolleras mot, läst med de vanliga inläsningsfunktionerna."""

    def __init__(self):
        bank = json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))["bank"]
        self.kontoplan = las_kontoplan(TESTBUTIKEN / "kontoplan.json")
        self.momssatser = las_momssatser(TESTBUTIKEN / "momssatser.json")
        self.matchning = las_matchningsformat(TESTBUTIKEN / "matchning.json")
        self.regelbok = las_regelbok(TESTBUTIKEN / "regelbok.json", self.kontoplan, self.momssatser, self.matchning)
        bankformat = ladda_bankformat(TESTBUTIKEN / "bankformat.json")
        self.januari = las_bankfil(DATAMAPP / "bank_2025-01.csv", bankformat, bank["2025-01"]["ingaende_saldo_ore"],
                                   bank["2025-01"]["utgaende_saldo_ore"])
        self.februari = las_bankfil(DATAMAPP / "bank_2025-02.csv", bankformat, self.januari.utgaende_saldo_ore,
                                    bank["2025-02"]["utgaende_saldo_ore"])
        self.bankperiod = sla_ihop_bankperioder([self.januari, self.februari])
        self.underlagsperiod = las_underlagsperiod(DATAMAPP / "underlag", "2025-01-01", "2025-03-31")
        # Z 1011 (2025-01-15) saknas i testdatan, så kassaperioden slutar dagen före.
        self.kassaformat = ladda_kassaformat(TESTBUTIKEN / "kassaformat.json")
        self.kassaperiod = las_kassaperiod(DATAMAPP / "kassa", self.kassaformat, "2025-01-01", "2025-01-14")

    def bankrad(self, period, radnr):
        """Bankradens id i bankfilen (januari eller februari) med radnumret."""
        rad = period.rader[radnr - 1]
        assert rad["radnr"] == radnr
        return rad["id"]

    def perioder(self):
        return {"underlagsperiod": self.underlagsperiod, "bankperiod": self.bankperiod,
                "kassaperiod": self.kassaperiod}


@pytest.fixture(scope="module")
def kallor():
    return Kallor()


def skapa(kallor, forslag, **perioder):
    """skapa_konteringsforslag med testbutikens regelbok och kontoplan och alla tre perioderna, om inget annat anges."""
    allt = {**kallor.perioder(), **perioder}
    return skapa_konteringsforslag(forslag, kallor.regelbok, kallor.kontoplan, **allt)


# --- Förslag byggda för hand ---

def sha256(fil):
    return hashlib.sha256(fil.read_bytes()).hexdigest()


def kontrollsummor(regelbok=TESTBUTIKEN / "regelbok.json", kontoplan=TESTBUTIKEN / "kontoplan.json"):
    """Kontrollsummorna i 'regel' i kopplingarna: filerna som förslaget är byggt mot (granskning 7, M4)."""
    return {"regelbokens_kontrollsumma": sha256(regelbok), "kontoplanens_kontrollsumma": sha256(kontoplan),
            "momsfilens_kontrollsumma": sha256(TESTBUTIKEN / "momssatser.json"),
            "matchningsformatets_kontrollsumma": sha256(TESTBUTIKEN / "matchning.json")}


def underlag(id_, falt, momssats=None):
    kalla = {"kalla": "underlag", "id": id_, "falt": falt}
    if momssats is not None:
        kalla["momssats"] = momssats
    return kalla


def bankrad(id_):
    return {"kalla": "bankrad", "id": id_, "falt": "belopp_ore"}


def z(postnamn, sats=None, znummer=1001):
    kalla = {"kalla": "z_rapport", "kassaregister": KASSAREGISTER, "znummer": znummer, "postnamn": postnamn}
    if sats is not None:
        kalla["sats"] = sats
    return kalla


def rad(konto, debet=0, kredit=0, berakning="lika", *fran):
    return {"konto": konto, "debet_ore": debet, "kredit_ore": kredit, "ursprung": {"berakning": berakning,
                                                                                   "fran": list(fran)}}


def forslag(datum, text, rader, regel, underlag_=(), bankrader=(), z_rapporter=(), forslag_id="F-TEST-0001"):
    return {
        "forslag_id": forslag_id,
        "verifikation": {"datum": datum, "text": text, "rader": rader},
        "kopplingar": {"underlag": [{"id": id_} for id_ in underlag_],
                       "bankrader": [{"id": id_} for id_ in bankrader],
                       "z_rapporter": [{"kassaregister": KASSAREGISTER, "znummer": nummer} for nummer in z_rapporter],
                       "regel": {"id": regel, **kontrollsummor()}},
        "motivering": "Byggt för hand i ett test.",
    }


U3 = "SYNT-U-2025-003"


def fakturan():
    """4a, verifikation 1: fakturan SYNT-U-2025-003 bokförs (faktureringsmetoden)."""
    return forslag("2025-01-07", "Faktura LEV-TE, SYNT-TE-761", [
        rad("4010", 1493800, 0, "lika", underlag(U3, "underlag_ore", 12)),
        rad("2641", 179256, 0, "lika", underlag(U3, "moms_ore", 12)),
        rad("2440", 0, 1673056, "lika", underlag(U3, "belopp_ore")),
    ], "R-LEV-TE", underlag_=[U3])


def betalningen(kallor):
    """4a, verifikation 2: betalningen 2025-02-06, bank_2025-02.csv radnummer 26."""
    bank = kallor.bankrad(kallor.februari, 26)
    return forslag("2025-02-06", "Betalning LEV-TE, faktura SYNT-TE-761", [
        rad("2440", 1673056, 0, "lika", underlag(U3, "belopp_ore")),
        rad("1940", 0, 1673056, "lika", bankrad(bank)),
    ], "R-LEV-TE", underlag_=[U3], bankrader=[bank])


def z_1001():
    """4c: Z-rapport 1001 från 2025-01-02, med avräkningskonton för betalsätten."""
    return forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 95600, 0, "lika", z("betalsatt_kontant")),
        rad("1580", 411500, 0, "lika", z("betalsatt_kort")),
        rad("1581", 89400, 0, "lika", z("betalsatt_swish")),
        rad("3002", 0, 378750, "skillnad", z("forsaljning", 12), z("moms", 12)),
        rad("2621", 0, 45450, "lika", z("moms", 12)),
        rad("3001", 0, 137840, "skillnad", z("forsaljning", 25), z("moms", 25)),
        rad("2611", 0, 34460, "lika", z("moms", 25)),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])


def kortinlosen(kallor):
    """4d: kortinlösens insättning 2025-01-03 (bank_2025-01.csv radnummer 3) för Z 1001, med avgiften som skillnad."""
    bank = kallor.bankrad(kallor.januari, 3)
    return forslag("2025-01-03", "Kortinlösen för 2025-01-02", [
        rad("1940", 406562, 0, "lika", bankrad(bank)),
        rad("6570", 4938, 0, "skillnad", z("betalsatt_kort"), bankrad(bank)),
        rad("1580", 0, 411500, "lika", z("betalsatt_kort")),
    ], "R-BANK-KORTINLOSEN", bankrader=[bank], z_rapporter=[1001])


def bankavgiften(kallor):
    """4e: bankavgiften 2025-01-31, bank_2025-01.csv radnummer 117 (125,00 kr)."""
    bank = kallor.bankrad(kallor.januari, 117)
    return forslag("2025-01-31", "Bankavgift företagskonto", [
        rad("6570", 12500, 0, "lika", bankrad(bank)),
        rad("1940", 0, 12500, "lika", bankrad(bank)),
    ], "R-BANK-AVGIFT", bankrader=[bank])


# --- Exemplen i DESIGN avsnitt 4 ---

def test_4a_fakturan(kallor):
    resultat = skapa(kallor, fakturan())
    assert type(resultat) is Konteringsforslag
    verifikation = resultat.verifikation
    assert verifikation["datum"] == "2025-01-07"
    assert [(r["konto"], r["debet_ore"], r["kredit_ore"]) for r in verifikation["rader"]] == [
        ("4010", 1493800, 0), ("2641", 179256, 0), ("2440", 0, 1673056)]
    assert resultat.kopplingar == {
        "underlag": [{"id": U3, "kontrollsumma": sha256(DATAMAPP / "underlag" / (U3 + ".json"))}],
        "bankrader": [], "z_rapporter": [],
        "regel": {"id": "R-LEV-TE", "regelbokens_kontrollsumma": sha256(TESTBUTIKEN / "regelbok.json"),
                  "kontoplanens_kontrollsumma": sha256(TESTBUTIKEN / "kontoplan.json"),
                  "momsfilens_kontrollsumma": sha256(TESTBUTIKEN / "momssatser.json"),
                  "matchningsformatets_kontrollsumma": sha256(TESTBUTIKEN / "matchning.json")},
    }
    assert resultat.kontroller == {"K2": "ok", "ursprung": "ok"}
    assert resultat.forslag_id == "F-TEST-0001" and resultat.motivering == "Byggt för hand i ett test."


def test_4a_betalningen(kallor):
    resultat = skapa(kallor, betalningen(kallor))
    assert [(r["konto"], r["debet_ore"], r["kredit_ore"]) for r in resultat.verifikation["rader"]] == [
        ("2440", 1673056, 0), ("1940", 0, 1673056)]
    bank = kallor.bankrad(kallor.februari, 26)
    assert resultat.kopplingar["bankrader"] == [
        {"id": bank, "radnr": 26, "filens_kontrollsumma": sha256(DATAMAPP / "bank_2025-02.csv")}]
    assert resultat.kopplingar["regel"]["regelbokens_kontrollsumma"] == kallor.regelbok.kontrollsumma


def test_4c_z_1001(kallor):
    resultat = skapa(kallor, z_1001())
    rader = resultat.verifikation["rader"]
    assert sum(r["debet_ore"] for r in rader) == sum(r["kredit_ore"] for r in rader) == 596500
    assert [(r["konto"], r["debet_ore"] or r["kredit_ore"]) for r in rader] == [
        ("1910", 95600), ("1580", 411500), ("1581", 89400), ("3002", 378750), ("2621", 45450), ("3001", 137840),
        ("2611", 34460)]
    assert resultat.kopplingar["z_rapporter"] == [
        {"kassaregister": KASSAREGISTER, "znummer": 1001, "rapportdatum": "2025-01-02",
         "filens_kontrollsumma": sha256(DATAMAPP / "kassa" / "kassa_2025-01-02.csv")}]


def test_4d_kortinlosen_med_avgiften_som_skillnad(kallor):
    resultat = skapa(kallor, kortinlosen(kallor))
    assert [(r["konto"], r["debet_ore"], r["kredit_ore"]) for r in resultat.verifikation["rader"]] == [
        ("1940", 406562, 0), ("6570", 4938, 0), ("1580", 0, 411500)]
    assert [k["znummer"] for k in resultat.kopplingar["z_rapporter"]] == [1001]


def test_4e_bankavgiften(kallor):
    resultat = skapa(kallor, bankavgiften(kallor))
    assert resultat.kopplingar["bankrader"][0]["radnr"] == 117


def test_summa_av_flera_bankrader(kallor):
    # 4d: två Swish-rader (bank_2025-01.csv radnummer 1 och 2) är tillsammans Swish i Z 1001.
    forsta, andra = kallor.bankrad(kallor.januari, 1), kallor.bankrad(kallor.januari, 2)
    data = forslag("2025-01-02", "Swish 2025-01-02", [
        rad("1940", 89400, 0, "summa", bankrad(forsta), bankrad(andra)),
        rad("1581", 0, 89400, "lika", z("betalsatt_swish")),
    ], "R-BANK-SWISH", bankrader=[forsta, andra], z_rapporter=[1001])
    assert skapa(kallor, data).kopplingar["bankrader"][1]["radnr"] == 2


def test_period_som_inte_anvands_far_vara_none(kallor):
    assert skapa(kallor, fakturan(), bankperiod=None, kassaperiod=None).kontroller == {"K2": "ok", "ursprung": "ok"}
    assert skapa(kallor, z_1001(), underlagsperiod=None, bankperiod=None)
    assert skapa(kallor, bankavgiften(kallor), underlagsperiod=None, kassaperiod=None)


def test_en_bankperiod_for_en_manad_godtas(kallor):
    assert skapa(kallor, bankavgiften(kallor), bankperiod=kallor.januari)


def test_en_andrad_regelbok_ger_en_annan_kontrollsumma_i_forslaget(kallor, tmp_path):
    # Förberedelse för spärrtestet "ändrad regelbok" (SPEC 7): samma regler, ett mellanslag till i filen.
    fil = tmp_path / "regelbok.json"
    fil.write_bytes((TESTBUTIKEN / "regelbok.json").read_bytes() + b" ")
    andrad = las_regelbok(fil, kallor.kontoplan, kallor.momssatser, kallor.matchning)
    data = fakturan()
    data["kopplingar"]["regel"]["regelbokens_kontrollsumma"] = sha256(fil)
    resultat = skapa_konteringsforslag(data, andrad, kallor.kontoplan, **kallor.perioder())
    summa = resultat.kopplingar["regel"]["regelbokens_kontrollsumma"]
    assert summa == sha256(fil) != skapa(kallor, fakturan()).kopplingar["regel"]["regelbokens_kontrollsumma"]


# --- Förslaget kan inte ändras, och är aldrig bokfört eller godkänt ---

def test_forslaget_kan_inte_andras(kallor):
    resultat = skapa(kallor, fakturan())
    for namn in ("verifikation", "forslag_id", "godkand", "bokford", "x"):
        with pytest.raises(AttributeError, match="Ett Konteringsforslag kan inte ändras"):
            setattr(resultat, namn, None)
        with pytest.raises(AttributeError, match="Ett Konteringsforslag kan inte ändras"):
            delattr(resultat, namn)
    kopia = resultat.verifikation
    kopia["rader"][0]["debet_ore"] = 1
    kopia["rader"].clear()
    kopplingar = resultat.kopplingar
    kopplingar["regel"]["regelbokens_kontrollsumma"] = "0" * 64
    resultat.kontroller["K2"] = "ändrat"
    assert resultat.verifikation["rader"][0]["debet_ore"] == 1493800
    assert resultat.kopplingar["regel"]["regelbokens_kontrollsumma"] == kallor.regelbok.kontrollsumma
    assert resultat.kontroller == {"K2": "ok", "ursprung": "ok"}


def test_ett_forslag_kan_inte_fyllas_med_nytt_innehall(kallor):
    # Även med nyckeln, som bara modulen själv har (testerna får använda den), går ett skapat förslag
    # inte att fylla med nytt innehåll.
    import konteringsforslag

    resultat = skapa(kallor, fakturan())
    with pytest.raises(KonteringsforslagFel, match="Ett Konteringsforslag kan inte ändras"):
        resultat.__init__(konteringsforslag._FORSLAGSNYCKEL, {"forslag_id": "F-ANNAT"})
    assert resultat.forslag_id == "F-TEST-0001"


def test_indata_som_andras_efterat_andrar_inte_forslaget(kallor):
    data = fakturan()
    fore = copy.deepcopy(data)
    resultat = skapa(kallor, data)
    assert data == fore  # funktionen ändrar inte indata
    data["verifikation"]["rader"][0]["debet_ore"] = 1
    data["verifikation"]["rader"][0]["ursprung"]["fran"][0]["id"] = "annat"
    data["kopplingar"]["regel"]["id"] = "annat"
    assert resultat.verifikation == fore["verifikation"]
    assert resultat.kopplingar["regel"]["id"] == "R-LEV-TE"


def test_forslaget_har_inget_falt_for_bokfort_eller_godkant(kallor):
    resultat = skapa(kallor, betalningen(kallor))
    offentliga = [namn for namn in dir(resultat) if not namn.startswith("_")]
    assert offentliga == ["forslag_id", "kontroller", "kopplingar", "motivering", "verifikation"]
    assert set(FORSLAG_NYCKLAR) == {"forslag_id", "verifikation", "kopplingar", "motivering"}
    for text in (json.dumps(resultat.verifikation), json.dumps(resultat.kopplingar), json.dumps(resultat.kontroller)):
        assert "godk" not in text and "bokf" not in text


def test_forslaget_kan_bara_skapas_av_skapa_konteringsforslag():
    with pytest.raises(KonteringsforslagFel, match="kan bara skapas av skapa_konteringsforslag"):
        Konteringsforslag(object(), {"forslag_id": "F-1"})
    with pytest.raises(KonteringsforslagFel, match="kan bara skapas av skapa_konteringsforslag"):
        Konteringsforslag(None, {})


def test_ett_forslag_skapat_forbi_funktionen_gar_inte_att_lasa():
    falskt = object.__new__(Konteringsforslag)
    for las in (lambda: falskt.verifikation, lambda: falskt.kopplingar, lambda: falskt.forslag_id,
                lambda: falskt.kontroller, lambda: falskt.motivering, lambda: repr(falskt)):
        with pytest.raises(KonteringsforslagFel, match="har inte skapats av skapa_konteringsforslag"):
            las()


def test_repr(kallor):
    assert repr(skapa(kallor, fakturan())) == (
        "Konteringsforslag('F-TEST-0001', 2025-01-07, 3 rader, debet = kredit = 16730,56 kr)")


# --- Stoppregler ---

def stoppas(kallor, data, kontroll, *texter, **perioder):
    """Kräver KonteringsforslagFel med kontrollen och texterna i meddelandet."""
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa(kallor, data, **perioder)
    meddelande = str(fel.value)
    assert fel.value.kontroll == kontroll, meddelande
    assert meddelande.startswith("Konteringsförslaget skapas inte (" + kontroll + "): "), meddelande
    for text in texter:
        assert text in meddelande, meddelande
    return meddelande


def andrat(bygg, andring):
    """Ett förslag från bygg, med andring(förslaget) gjord. bygg tar kallor om den behöver det."""
    def gor(kallor):
        data = bygg(kallor) if bygg in (betalningen, kortinlosen, bankavgiften) else bygg()
        andring(data)
        return data
    return gor


def rader(data):
    return data["verifikation"]["rader"]


def satt(*vag, varde):
    """En ändring som sätter värdet på platsen vag i förslaget."""
    def andring(data):
        del_ = data
        for nyckel in vag[:-1]:
            del_ = del_[nyckel]
        del_[vag[-1]] = varde
    return andring


def ta_bort(*vag):
    def andring(data):
        del_ = data
        for nyckel in vag[:-1]:
            del_ = del_[nyckel]
        del del_[vag[-1]]
    return andring


def bada(*andringar):
    def andring(data):
        for en in andringar:
            en(data)
    return andring


def ny_rad(konto, debet, kredit, berakning, *fran):
    def andring(data):
        rader(data).append(rad(konto, debet, kredit, berakning, *fran))
    return andring


class Konstig(dict):
    """En dict med egna regler. Ska stoppas, så att inget som bara liknar en dict kommer in."""


INDATA = {
    # Formen
    "alla_nycklar_saknas": (fakturan, lambda d: d.clear() or d.update({"x": 1}),
                            "förslaget saknar nyckeln 'forslag_id', 'verifikation', 'kopplingar', 'motivering'"),
    "saknad_nyckel": (fakturan, ta_bort("motivering"), "förslaget saknar nyckeln 'motivering'"),
    "okand_nyckel_bokford": (fakturan, satt("bokford", varde=True), "förslaget har en okänd nyckel: 'bokford'"),
    "okand_nyckel_godkand": (fakturan, satt("godkand", varde={"av": "x"}), "okänd nyckel: 'godkand'"),
    "okand_nyckel_niva": (fakturan, satt("niva", varde="A"), "okänd nyckel: 'niva'"),
    "verifikation_saknar_datum": (fakturan, ta_bort("verifikation", "datum"), "'verifikation' saknar nyckeln 'datum'"),
    "verifikation_okand_nyckel": (fakturan, satt("verifikation", "nummer", varde=7),
                                  "'verifikation' har en okänd nyckel: 'nummer'"),
    "verifikation_inte_objekt": (fakturan, satt("verifikation", varde=[]),
                                 "'verifikation' ska vara ett objekt (dict), inte en lista"),
    "rader_inte_lista": (fakturan, satt("verifikation", "rader", varde={}),
                         "'rader' i 'verifikation' ska vara en lista, inte ett objekt"),
    "rad_inte_objekt": (fakturan, lambda d: rader(d).append("4010"), "rad 4 ska vara ett objekt (dict), inte text"),
    "rad_okand_nyckel": (fakturan, satt("verifikation", "rader", 0, "moms", varde=0),
                         "rad 1 har en okänd nyckel: 'moms'"),
    "rad_saknar_ursprung": (fakturan, ta_bort("verifikation", "rader", 2, "ursprung"),
                            "rad 3 saknar nyckeln 'ursprung'"),
    "ursprung_okand_nyckel": (fakturan, satt("verifikation", "rader", 0, "ursprung", "modell", varde="x"),
                              "'ursprung' på rad 1 har en okänd nyckel: 'modell'"),
    "fran_inte_lista": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", varde={}),
                        "'fran' i 'ursprung' på rad 1 ska vara en lista, inte ett objekt"),
    "kopplingar_saknar_regel": (fakturan, ta_bort("kopplingar", "regel"), "'kopplingar' saknar nyckeln 'regel'"),
    "kopplingar_okand_nyckel": (fakturan, satt("kopplingar", "godkannare", varde=[]),
                                "'kopplingar' har en okänd nyckel: 'godkannare'"),
    "koppling_inte_lista": (fakturan, satt("kopplingar", "underlag", varde=U3),
                            "'underlag' i 'kopplingar' ska vara en lista, inte text"),
    "koppling_okand_nyckel": (fakturan, satt("kopplingar", "underlag", 0, "kontrollsumma", varde="0" * 64),
                              "post nummer 1 i 'underlag' i 'kopplingar' har en okänd nyckel: 'kontrollsumma'"),
    "koppling_id_inte_text": (fakturan, satt("kopplingar", "underlag", 0, "id", varde=3),
                              "'id' i post nummer 1 i 'underlag' i 'kopplingar' ska vara text, inte ett heltal"),
    "koppling_znummer_text": (z_1001, satt("kopplingar", "z_rapporter", 0, "znummer", varde="1001"),
                              "'znummer' i post nummer 1 i 'z_rapporter' i 'kopplingar' ska vara ett heltal, inte text"),
    "koppling_znummer_true": (z_1001, satt("kopplingar", "z_rapporter", 0, "znummer", varde=True),
                              "ska vara ett heltal, inte True eller False"),
    "koppling_znummer_negativt": (z_1001, satt("kopplingar", "z_rapporter", 0, "znummer", varde=-1001),
                                  "'znummer' i post nummer 1 i 'z_rapporter' i 'kopplingar' är negativt"),
    "regel_utan_id": (fakturan, satt("kopplingar", "regel", varde={}), "'regel' i 'kopplingar' saknar nyckeln 'id'"),
    "regel_id_tomt": (fakturan, satt("kopplingar", "regel", "id", varde=" "),
                      "'id' i 'regel' i 'kopplingar' får inte vara tom"),
    # Sorterna av värden
    "tupel_i_stallet_for_lista": (fakturan, satt("verifikation", "rader", varde=()),
                                  "förslaget, 'verifikation', 'rader' är en tupel"),
    "dict_med_egna_regler": (fakturan, lambda d: rader(d).__setitem__(0, Konstig(rader(d)[0])),
                             "förslaget, 'verifikation', 'rader', nummer 1 är Konstig"),
    "nyckel_som_inte_ar_text": (fakturan, satt(1, varde="x"), "förslaget har nyckeln 1, som inte är text"),
    "objekt_inuti_sig_sjalvt": (fakturan, lambda d: d["verifikation"]["rader"].append(d["verifikation"]["rader"]),
                                "för många objekt och listor inuti varandra"),
    # Texterna och datumet
    "id_inte_text": (fakturan, satt("forslag_id", varde=1), "'forslag_id' ska vara text, inte ett heltal"),
    "id_tomt": (fakturan, satt("forslag_id", varde=""), "'forslag_id' får inte vara tom"),
    "id_med_blanksteg": (fakturan, satt("forslag_id", varde="F-1 "), "'forslag_id' får inte ha blanksteg först"),
    "id_med_dolt_tecken": (fakturan, satt("forslag_id", varde="F-" + chr(0x200B) + "1"),
                           "'forslag_id' innehåller tecknet U+200B"),
    "text_med_riktningstecken": (fakturan, satt("verifikation", "text", varde="Faktura " + chr(0x202E) + "ETT"),
                                 "'text' i 'verifikation' innehåller tecknet U+202E"),
    "text_med_milt_riktningsmarke": (fakturan, satt("verifikation", "text", varde="Faktura " + chr(0x200F)),
                                     "'text' i 'verifikation' innehåller tecknet U+200F"),
    "text_med_radbrytning": (fakturan, satt("verifikation", "text", varde="Faktura\nrad 2"),
                             "'text' i 'verifikation' innehåller tecknet U+000A"),
    "text_med_halvt_tecken": (fakturan, satt("verifikation", "text", varde="Faktura " + chr(0xD800)), "tecknet U+D800"),
    "text_none": (fakturan, satt("verifikation", "text", varde=None), "'text' i 'verifikation' ska vara text, inte None"),
    "motivering_med_hart_mellanslag": (fakturan, satt("motivering", varde="Regeln" + chr(0x00A0) + "R-LEV-TE"),
                                       "'motivering' innehåller tecknet U+00A0"),
    "datum_som_inte_finns": (fakturan, satt("verifikation", "datum", varde="2025-02-30"),
                             "'datum' i 'verifikation' ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte '2025-02-30'"),
    "datum_som_tal": (fakturan, satt("verifikation", "datum", varde=20250107), "inte ett heltal"),
    "datum_med_annan_form": (fakturan, satt("verifikation", "datum", varde="2025-1-07"), "inte '2025-1-07'"),
}

K2 = {
    "en_rad": (fakturan, lambda d: rader(d).__delitem__(slice(1, None)),
               "verifikationen har 1 rad, men en verifikation ska ha minst två rader"),
    "inga_rader": (fakturan, lambda d: rader(d).clear(), "verifikationen har 0 rader"),
    "decimaltal": (fakturan, satt("verifikation", "rader", 0, "debet_ore", varde=1493800.0),
                   "'debet_ore' på rad 1 ska vara ett heltal i öre, inte ett decimaltal"),
    "true": (fakturan, satt("verifikation", "rader", 1, "kredit_ore", varde=True),
             "'kredit_ore' på rad 2 ska vara ett heltal i öre, inte True eller False"),
    "false": (fakturan, satt("verifikation", "rader", 0, "kredit_ore", varde=False),
              "'kredit_ore' på rad 1 ska vara ett heltal i öre, inte True eller False"),
    "text": (fakturan, satt("verifikation", "rader", 2, "kredit_ore", varde="1673056"), "inte text"),
    "none": (fakturan, satt("verifikation", "rader", 2, "debet_ore", varde=None), "inte None"),
    "negativt": (fakturan, bada(satt("verifikation", "rader", 2, "kredit_ore", varde=0),
                                satt("verifikation", "rader", 2, "debet_ore", varde=-1673056)),
                 "'debet_ore' på rad 3 är negativt (-16730,56 kr)"),
    "for_stort": (fakturan, satt("verifikation", "rader", 0, "debet_ore", varde=10 ** 15),
                  "'debet_ore' på rad 1 har fler än 15 siffror"),
    "bade_debet_och_kredit": (fakturan, satt("verifikation", "rader", 1, "kredit_ore", varde=179256),
                              "rad 2 har både debet och kredit"),
    "varken_debet_eller_kredit": (fakturan, satt("verifikation", "rader", 1, "debet_ore", varde=0),
                                  "rad 2 har varken debet eller kredit"),
    "obalans_ett_ore": (fakturan, satt("verifikation", "rader", 0, "debet_ore", varde=1493801),
                        "summan av debet är 16730,57 kr, men summan av kredit är 16730,56 kr, skillnad 0,01 kr"),
    "obalans_rad_saknas": (fakturan, lambda d: rader(d).pop(1), "summan av debet är 14938,00 kr"),
    "konto_som_tal": (fakturan, satt("verifikation", "rader", 0, "konto", varde=4010),
                      "'konto' på rad 1 ska vara text, till exempel \"1234\", inte ett heltal"),
    "konto_som_inte_finns": (fakturan, satt("verifikation", "rader", 0, "konto", varde="4011"),
                             "rad 1: Kontoplanen har inget konto '4011'"),
    "konto_med_blanksteg": (fakturan, satt("verifikation", "rader", 0, "konto", varde="4010 "),
                            "rad 1: Kontoplanen har inget konto '4010 '"),
}

URSPRUNG = {
    # Punkt 1: sätt att räkna och antal källor
    "okand_berakning": (fakturan, satt("verifikation", "rader", 0, "ursprung", "berakning", varde="medel"),
                        "'berakning' på rad 1 (konto 4010) ska vara en av 'lika', 'summa', 'skillnad', inte 'medel'"),
    "berakning_inte_text": (fakturan, satt("verifikation", "rader", 0, "ursprung", "berakning", varde=None),
                            "inte None"),
    "utan_kallor": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", varde=[]),
                    "rad 1 (konto 4010) räknas med 'lika' och ska ha exakt en källa i 'fran', men har 0"),
    "lika_med_tva_kallor": (fakturan, lambda d: rader(d)[2]["ursprung"]["fran"].append(underlag(U3, "moms_ore", 12)),
                            "rad 3 (konto 2440) räknas med 'lika' och ska ha exakt en källa i 'fran', men har 2"),
    "summa_med_en_kalla": (fakturan, satt("verifikation", "rader", 2, "ursprung", "berakning", varde="summa"),
                           "rad 3 (konto 2440) räknas med 'summa' och ska ha minst två källor i 'fran', men har 1"),
    "skillnad_med_en_kalla": (fakturan, satt("verifikation", "rader", 2, "ursprung", "berakning", varde="skillnad"),
                              "räknas med 'skillnad' och ska ha minst två källor"),
    "samma_kalla_tva_ganger": (z_1001, bada(
        satt("verifikation", "rader", 0, "debet_ore", varde=191200),
        satt("verifikation", "rader", 0, "ursprung", varde={"berakning": "summa", "fran": [
            z("betalsatt_kontant"), z("betalsatt_kontant")]}),
        ny_rad("1910", 0, 95600, "lika", z("betalsatt_kontant"))),
        "rad 1 (konto 1910) har Z-rapport 1001 (TB-KASSA-1), posten 'betalsatt_kontant' flera gånger i 'fran'"),
    # Punkt 2: källan finns
    "kalla_inte_objekt": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", 0, varde=U3),
                          "källa nummer 1 på rad 1 (konto 4010) ska vara ett objekt (dict), inte text"),
    "okand_kalla": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "kalla", varde="modellen"),
                    "'kalla' i källa nummer 1 på rad 1 (konto 4010) ska vara en av 'underlag', 'bankrad', 'z_rapport',"
                    " inte 'modellen'"),
    "kalla_saknas": (fakturan, ta_bort("verifikation", "rader", 0, "ursprung", "fran", 0, "kalla"),
                     "'kalla' i källa nummer 1 på rad 1 (konto 4010) ska vara en av"),
    "kalla_som_lista": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "kalla", varde=[]),
                        "inte en lista"),
    "kalla_okand_nyckel": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "belopp_ore",
                                          varde=1493800),
                           "källa nummer 1 på rad 1 (konto 4010) har en okänd nyckel: 'belopp_ore'"),
    "kalla_saknar_falt": (fakturan, ta_bort("verifikation", "rader", 2, "ursprung", "fran", 0, "falt"),
                          "källa nummer 1 på rad 3 (konto 2440) saknar nyckeln 'falt'"),
    "underlag_finns_inte": (fakturan, bada(*[satt("verifikation", "rader", n, "ursprung", "fran", 0, "id",
                                                  varde="SYNT-U-2025-099") for n in range(3)],
                                           satt("kopplingar", "underlag", 0, "id", varde="SYNT-U-2025-099")),
                            "pekar på underlaget 'SYNT-U-2025-099', som inte finns i underlagsperioden"),
    "underlag_som_ar_dublett": (fakturan, bada(*[satt("verifikation", "rader", n, "ursprung", "fran", 0, "id",
                                                      varde="SYNT-U-2025-004") for n in range(3)],
                                               satt("kopplingar", "underlag", 0, "id", varde="SYNT-U-2025-004")),
                                "'SYNT-U-2025-004', som inte finns i underlagsperioden",
                                "dublett som K4 har tagit bort"),
    "underlag_id_inte_text": (fakturan, satt("verifikation", "rader", 2, "ursprung", "fran", 0, "id", varde=3),
                              "'id' i källa nummer 1 på rad 3 (konto 2440) ska vara text, inte ett heltal"),
    "underlag_okant_falt": (fakturan, satt("verifikation", "rader", 2, "ursprung", "fran", 0, "falt",
                                           varde="fakturanummer"),
                            "'falt' i källa nummer 1 på rad 3 (konto 2440) ska vara en av 'belopp_ore', "
                            "'underlag_ore', 'moms_ore', inte 'fakturanummer'"),
    "underlag_falt_inte_text": (fakturan, satt("verifikation", "rader", 2, "ursprung", "fran", 0, "falt", varde=None),
                                "inte None"),
    "momssats_pa_beloppet": (fakturan, satt("verifikation", "rader", 2, "ursprung", "fran", 0, "momssats", varde=12),
                             "har 'momssats', men 'belopp_ore' står inte i en momsrad"),
    "momsrad_utan_momssats": (fakturan, ta_bort("verifikation", "rader", 1, "ursprung", "fran", 0, "momssats"),
                              "pekar på 'moms_ore' i en momsrad men saknar 'momssats'"),
    "momsrad_som_inte_finns": (fakturan, satt("verifikation", "rader", 1, "ursprung", "fran", 0, "momssats", varde=25),
                               "underlaget 'SYNT-U-2025-003' har ingen momsrad med satsen 25 %. Satserna i underlaget"
                               " är 12 %"),
    "momssats_true": (fakturan, satt("verifikation", "rader", 1, "ursprung", "fran", 0, "momssats", varde=True),
                      "'momssats' i källa nummer 1 på rad 2 (konto 2641) ska vara ett heltal, inte True eller False"),
    "momssats_text": (fakturan, satt("verifikation", "rader", 1, "ursprung", "fran", 0, "momssats", varde="12"),
                      "ska vara ett heltal, inte text"),
    "bankrad_finns_inte": (betalningen, bada(satt("verifikation", "rader", 1, "ursprung", "fran", 0, "id",
                                                  varde="BANK-0000000000000000"),
                                             satt("kopplingar", "bankrader", 0, "id", varde="BANK-0000000000000000")),
                           "pekar på bankraden 'BANK-0000000000000000', som inte finns i bankperioden"),
    "bankradens_saldo": (betalningen, satt("verifikation", "rader", 1, "ursprung", "fran", 0, "falt",
                                           varde="saldo_efter_ore"),
                         "ska vara en av 'belopp_ore', inte 'saldo_efter_ore'"),
    "bankrad_med_momssats": (betalningen, satt("verifikation", "rader", 1, "ursprung", "fran", 0, "momssats", varde=0),
                             "källa nummer 1 på rad 2 (konto 1940) har en okänd nyckel: 'momssats'"),
    "z_rapport_finns_inte": (z_1001, bada(satt("verifikation", "rader", 0, "ursprung", "fran", 0, "znummer",
                                               varde=1011),
                                          satt("kopplingar", "z_rapporter", varde=[
                                              {"kassaregister": KASSAREGISTER, "znummer": 1001},
                                              {"kassaregister": KASSAREGISTER, "znummer": 1011}])),
                             "pekar på Z-rapport 1011 från kassaregistret 'TB-KASSA-1', som inte finns i kassaperioden"),
    "z_kassaregister_annan_stavning": (z_1001, satt("verifikation", "rader", 0, "ursprung", "fran", 0,
                                                    "kassaregister", varde="tb-kassa-1"),
                                       "pekar på Z-rapport 1001 från kassaregistret 'tb-kassa-1', som inte finns"),
    "z_post_finns_inte": (z_1001, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "postnamn",
                                       varde="betalsatt_check"),
                          "Z-rapport 1001 (TB-KASSA-1), posten 'betalsatt_check' finns inte. Posterna i rapporten är"
                          " 'forsaljning' med satsen 12 %"),
    "z_moms_utan_sats": (z_1001, ta_bort("verifikation", "rader", 4, "ursprung", "fran", 0, "sats"),
                         "posten 'moms' finns inte"),
    "z_betalsatt_med_sats": (z_1001, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "sats", varde=12),
                             "posten 'betalsatt_kontant' med satsen 12 % finns inte"),
    "z_znummer_text": (z_1001, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "znummer", varde="1001"),
                       "'znummer' i källa nummer 1 på rad 1 (konto 1910) ska vara ett heltal, inte text"),
    "z_sats_decimaltal": (z_1001, satt("verifikation", "rader", 4, "ursprung", "fran", 0, "sats", varde=12.0),
                          "'sats' i källa nummer 1 på rad 5 (konto 2621) ska vara ett heltal, inte ett decimaltal"),
    "z_med_falt": (z_1001, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "falt", varde="belopp_ore"),
                   "har en okänd nyckel: 'falt'"),
    # Punkt 3: beloppet räknas om
    "belopp_ett_ore_fel": (fakturan, bada(satt("verifikation", "rader", 0, "debet_ore", varde=1493801),
                                          satt("verifikation", "rader", 2, "kredit_ore", varde=1673057)),
                           "rad 1 (konto 4010) har beloppet 14938,01 kr, men 'lika' av källorna (underlaget"
                           " 'SYNT-U-2025-003', momsraden med satsen 12 %, 'underlag_ore': 14938,00 kr) blir"
                           " 14938,00 kr, skillnad 0,01 kr"),
    "fel_falt_i_kallan": (fakturan, satt("verifikation", "rader", 0, "ursprung", "fran", 0, "falt", varde="moms_ore"),
                          "rad 1 (konto 4010) har beloppet 14938,00 kr, men 'lika' av källorna"),
    "skillnad_at_fel_hall": (z_1001, satt("verifikation", "rader", 3, "ursprung", "fran", varde=[
        z("moms", 12), z("forsaljning", 12)]), "rad 4 (konto 3002) har beloppet 3787,50 kr", "blir -3787,50 kr"),
    "summa_i_stallet_for_skillnad": (z_1001, satt("verifikation", "rader", 3, "ursprung", "berakning", varde="summa"),
                                     "'summa' av källorna", "blir 4696,50 kr"),
    # Punkt 4: kopplingarna
    "underlag_saknas_i_kopplingar": (fakturan, satt("kopplingar", "underlag", varde=[]),
                                     "underlaget 'SYNT-U-2025-003' används av en rad, men står inte i 'underlag' i"
                                     " 'kopplingar'"),
    "underlag_i_kopplingar_som_inte_anvands": (betalningen, bada(
        satt("kopplingar", "underlag", varde=[{"id": U3}, {"id": "SYNT-U-2025-005"}])),
        "underlaget 'SYNT-U-2025-005' står i 'underlag' i 'kopplingar', men ingen rad använder det"),
    "underlag_tva_ganger_i_kopplingar": (fakturan, satt("kopplingar", "underlag", varde=[{"id": U3}, {"id": U3}]),
                                         "underlaget 'SYNT-U-2025-003' står flera gånger i 'underlag' i 'kopplingar'"),
    "bankrad_saknas_i_kopplingar": (betalningen, satt("kopplingar", "bankrader", varde=[]),
                                    "används av en rad, men står inte i 'bankrader' i 'kopplingar'"),
    "z_saknas_i_kopplingar": (z_1001, satt("kopplingar", "z_rapporter", varde=[]),
                              "Z-rapport 1001 (TB-KASSA-1) används av en rad, men står inte i 'z_rapporter'"),
    "z_i_kopplingar_som_inte_anvands": (fakturan, satt("kopplingar", "z_rapporter", varde=[
        {"kassaregister": KASSAREGISTER, "znummer": 1001}]),
        "Z-rapport 1001 (TB-KASSA-1) står i 'z_rapporter' i 'kopplingar', men ingen rad använder det"),
    "regel_som_inte_finns": (fakturan, satt("kopplingar", "regel", "id", varde="R-LEV-TEX"),
                             "regeln 'R-LEV-TEX' i 'kopplingar' finns inte i regelboken"),
    "regel_med_annan_stavning": (fakturan, satt("kopplingar", "regel", "id", varde="r-lev-te"),
                                 "regeln 'r-lev-te' i 'kopplingar' finns inte i regelboken"),
    # Punkt 5: momskontona
    "momskonto_utan_momsbelopp": (fakturan, bada(
        satt("verifikation", "rader", 0, "debet_ore", varde=179256),
        satt("verifikation", "rader", 0, "ursprung", "fran", 0, "falt", varde="moms_ore"),
        satt("verifikation", "rader", 1, "debet_ore", varde=1493800),
        satt("verifikation", "rader", 1, "ursprung", "fran", 0, "falt", varde="underlag_ore")),
        "rad 2 (konto 2641) är ett momskonto, men källan underlaget 'SYNT-U-2025-003', momsraden med satsen 12 %,"
        " 'underlag_ore' är inte ett momsbelopp"),
    "utgaende_moms_med_fel_sats": (z_1001, bada(
        satt("verifikation", "rader", 4, "kredit_ore", varde=34460),
        satt("verifikation", "rader", 4, "ursprung", "fran", 0, "sats", varde=25),
        satt("verifikation", "rader", 6, "kredit_ore", varde=45450),
        satt("verifikation", "rader", 6, "ursprung", "fran", 0, "sats", varde=12)),
        "rad 5 (konto 2621) är kontot för utgående moms med satsen 12 %, men källan Z-rapport 1001 (TB-KASSA-1),"
        " posten 'moms' med satsen 25 % har satsen 25 %"),
    # Hela försäljningen med satsen på kontot för utgående moms, och ingen rad på försäljningskontot.
    "utgaende_moms_fran_forsaljningen": (z_1001, bada(
        lambda d: rader(d).pop(3),
        satt("verifikation", "rader", 3, "kredit_ore", varde=424200),
        satt("verifikation", "rader", 3, "ursprung", "fran", 0, "postnamn", varde="forsaljning")),
        "rad 4 (konto 2621) är ett momskonto, men källan Z-rapport 1001 (TB-KASSA-1), posten 'forsaljning' med"
        " satsen 12 % är inte ett momsbelopp"),
    # Punkt 6: bankkontot (fler fall i egna tester nedan)
    "pengar_ut_i_debet": (betalningen, bada(
        satt("verifikation", "rader", 0, "debet_ore", varde=0),
        satt("verifikation", "rader", 0, "kredit_ore", varde=1673056),
        satt("verifikation", "rader", 1, "debet_ore", varde=1673056),
        satt("verifikation", "rader", 1, "kredit_ore", varde=0)),
        "rad 2 (konto 1940) är bankkontot och står i debet, men bankraden",
        "är pengar ut. Pengar in står i debet på bankkontot och pengar ut i kredit"),
}


def bygg_fall(fall):
    bygg, andring, *texter = fall
    return andrat(bygg, andring), texter


@pytest.mark.parametrize("fall", INDATA.values(), ids=INDATA.keys())
def test_stoppregel_indata(kallor, fall):
    bygg, texter = bygg_fall(fall)
    stoppas(kallor, bygg(kallor), "indata", *texter)


@pytest.mark.parametrize("fall", K2.values(), ids=K2.keys())
def test_stoppregel_k2(kallor, fall):
    bygg, texter = bygg_fall(fall)
    stoppas(kallor, bygg(kallor), "K2", *texter)


@pytest.mark.parametrize("fall", URSPRUNG.values(), ids=URSPRUNG.keys())
def test_stoppregel_ursprung(kallor, fall):
    bygg, texter = bygg_fall(fall)
    stoppas(kallor, bygg(kallor), "ursprung", *texter)


def test_summa_dar_det_ska_vara_skillnad_stoppas(kallor):
    # 4d: avgiften räknad som summa i stället för skillnad blir för stor och går inte ihop.
    data = kortinlosen(kallor)
    rader(data)[1]["ursprung"]["berakning"] = "summa"
    stoppas(kallor, data, "ursprung", "rad 2 (konto 6570) har beloppet 49,38 kr, men 'summa' av källorna",
            "blir 8180,62 kr")


def test_bankkonto_fran_underlaget_stoppas(kallor):
    # Betalningen med kontona bytta: beloppen och balansen stämmer, men bankkontot har underlaget som
    # ursprung i stället för bankraden. Pengar på banken ska alltid komma från en bankrad.
    bank = kallor.bankrad(kallor.februari, 26)
    data = forslag("2025-02-06", "Betalning", [
        rad("2440", 1673056, 0, "lika", bankrad(bank)),
        rad("1940", 0, 1673056, "lika", underlag(U3, "belopp_ore")),
    ], "R-LEV-TE", underlag_=[U3], bankrader=[bank])
    stoppas(kallor, data, "ursprung", "rad 2 (konto 1940) är bankkontot, men källan underlaget 'SYNT-U-2025-003',"
                                      " 'belopp_ore' är inte en bankrad")


def test_bankkonto_fran_z_rapporten_stoppas(kallor):
    data = forslag("2025-01-02", "Kortförsäljning direkt mot banken", [
        rad("1940", 411500, 0, "lika", z("betalsatt_kort")),
        rad("1580", 0, 411500, "lika", z("betalsatt_kort")),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])
    stoppas(kallor, data, "ursprung", "rad 1 (konto 1940) är bankkontot, men källan Z-rapport 1001 (TB-KASSA-1),"
                                      " posten 'betalsatt_kort' är inte en bankrad")


def test_bankkonto_med_skillnad_stoppas(kallor):
    # Två bankrader som skillnad på bankkontot: radnummer 3 (kortinlösen) minus radnummer 1 (Swish).
    kort, swish = kallor.bankrad(kallor.januari, 3), kallor.bankrad(kallor.januari, 1)
    data = forslag("2025-01-03", "Felaktig skillnad", [
        rad("1940", 406562 - 32300, 0, "skillnad", bankrad(kort), bankrad(swish)),
        rad("1580", 0, 406562 - 32300, "skillnad", bankrad(kort), bankrad(swish)),
    ], "R-BANK-KORTINLOSEN", bankrader=[kort, swish])
    stoppas(kallor, data, "ursprung", "rad 1 (konto 1940) är bankkontot och räknas med 'skillnad'. En rad på"
                                      " bankkontot ska vara en eller flera bankrader, räknade med 'lika' eller 'summa'")


def test_pengar_in_i_kredit_pa_bankkontot_stoppas(kallor):
    # Kortinlösens insättning med bankkontot i kredit och avräkningskontot i debet: beloppen och
    # balansen stämmer, men pengar in ska stå i debet på bankkontot.
    bank = kallor.bankrad(kallor.januari, 3)
    data = forslag("2025-01-03", "Kortinlösen för 2025-01-02", [
        rad("1580", 406562, 0, "lika", bankrad(bank)),
        rad("1940", 0, 406562, "lika", bankrad(bank)),
    ], "R-BANK-KORTINLOSEN", bankrader=[bank])
    stoppas(kallor, data, "ursprung", "rad 2 (konto 1940) är bankkontot och står i kredit, men bankraden",
            "är pengar in")


def test_bankkonto_med_summa_av_pengar_in_och_ut_stoppas(kallor):
    # Swish in (radnummer 1) och bankavgift ut (radnummer 117) på samma rad i debet: raden 117 går åt fel håll.
    swish, avgift = kallor.bankrad(kallor.januari, 1), kallor.bankrad(kallor.januari, 117)
    data = forslag("2025-01-31", "Felaktig summa", [
        rad("1940", 32300 + 12500, 0, "summa", bankrad(swish), bankrad(avgift)),
        rad("6570", 0, 32300 + 12500, "summa", bankrad(swish), bankrad(avgift)),
    ], "R-BANK-AVGIFT", bankrader=[swish, avgift])
    stoppas(kallor, data, "ursprung", "(radnummer 117) är pengar ut")


def test_konto_som_inte_galler_pa_datumet_stoppas(kallor, tmp_path):
    data = json.loads((TESTBUTIKEN / "kontoplan.json").read_text(encoding="utf-8"))
    for konto in data["konton"]:
        if konto["nummer"] == "1940":
            konto["till"] = "2025-01-31"
    fil = tmp_path / "kontoplan.json"
    fil.write_text(json.dumps(data), encoding="utf-8")
    kontoplan = las_kontoplan(fil)
    # Regelboken läses med samma kontoplan som förslaget (K2 punkt 1, granskning 7 M4).
    regelbok = las_regelbok(TESTBUTIKEN / "regelbok.json", kontoplan, kallor.momssatser, kallor.matchning)
    avgiften, betalningen_ = bankavgiften(kallor), betalningen(kallor)
    for data in (avgiften, betalningen_):
        data["kopplingar"]["regel"]["kontoplanens_kontrollsumma"] = sha256(fil)
    assert skapa_konteringsforslag(avgiften, regelbok, kontoplan, **kallor.perioder())
    with pytest.raises(KonteringsforslagFel, match="rad 2: Kontot 1940 gäller inte på 2025-02-06") as fel:
        skapa_konteringsforslag(betalningen_, regelbok, kontoplan, **kallor.perioder())
    assert fel.value.kontroll == "K2"


@pytest.mark.parametrize("period, saknas", [
    ("underlagsperiod", "pekar på ett underlag, men förslaget fick ingen underlagsperiod"),
    ("bankperiod", "pekar på en bankrad, men förslaget fick ingen bankperiod"),
    ("kassaperiod", "pekar på en Z-rapport, men förslaget fick ingen kassaperiod"),
])
def test_kalla_utan_period_stoppas(kallor, period, saknas):
    stoppas(kallor, kortinlosen(kallor) if period != "underlagsperiod" else fakturan(), "ursprung", saknas,
            **{period: None})


def test_bankrad_utanfor_bankperioden_stoppas(kallor):
    stoppas(kallor, betalningen(kallor), "ursprung", "som inte finns i bankperioden", bankperiod=kallor.januari)


def test_negativ_post_i_z_rapporten_stoppas(kallor, tmp_path):
    # En påhittad Z-rapport med negativa kontanter (mer tillbaka än in), där summorna ändå stämmer (K11).
    mapp = tmp_path / "kassa"
    mapp.mkdir()
    text = (DATAMAPP / "kassa" / "kassa_2025-01-02.csv").read_text(encoding="utf-8")
    text = text.replace("betalsatt_kontant,,956.00", "betalsatt_kontant,,-100.00")
    text = text.replace("betalsatt_kort,,4115.00", "betalsatt_kort,,5171.00")
    (mapp / "kassa_2025-01-02.csv").write_text(text, encoding="utf-8")
    kassaperiod = las_kassaperiod(mapp, kallor.kassaformat, "2025-01-02", "2025-01-02")
    data = forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 0, 10000, "lika", z("betalsatt_kontant")),
        rad("1580", 10000, 0, "lika", z("betalsatt_kontant")),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])
    stoppas(kallor, data, "ursprung", "posten 'betalsatt_kontant' är negativ (-100,00 kr)", "returer",
            kassaperiod=kassaperiod)


@pytest.mark.parametrize("namn, varde, text", [
    ("regelbok", None, "regelboken ska komma från las_regelbok, inte vara NoneType"),
    ("regelbok", {}, "regelboken ska komma från las_regelbok, inte vara dict"),
    ("kontoplan", "kontoplan.json", "kontoplanen ska komma från las_kontoplan, inte vara str"),
    ("underlagsperiod", [], "underlagsperioden ska komma från las_underlagsperiod (eller vara None), inte vara list"),
    ("bankperiod", "bank", "bankperioden ska komma från las_bankfil eller sla_ihop_bankperioder"),
    ("kassaperiod", {}, "kassaperioden ska komma från las_kassaperiod (eller vara None), inte vara dict"),
])
def test_indata_som_inte_kommer_fran_inlasningen_stoppas(kallor, namn, varde, text):
    argument = {"regelbok": kallor.regelbok, "kontoplan": kallor.kontoplan, **kallor.perioder(), namn: varde}
    with pytest.raises(KonteringsforslagFel, match=re.escape(text)) as fel:
        skapa_konteringsforslag(fakturan(), **argument)
    assert fel.value.kontroll == "indata"


def test_perioderna_kan_inte_byta_plats(kallor):
    with pytest.raises(KonteringsforslagFel, match="underlagsperioden ska komma från las_underlagsperiod"):
        skapa_konteringsforslag(fakturan(), kallor.regelbok, kallor.kontoplan, kallor.bankperiod,
                                kallor.underlagsperiod, kallor.kassaperiod)
    with pytest.raises(KonteringsforslagFel, match="regelboken ska komma från las_regelbok, inte vara Kontoplan"):
        skapa_konteringsforslag(fakturan(), kallor.kontoplan, kallor.regelbok)


def test_underklass_till_perioden_stoppas(kallor):
    from las_bank import Bankperiod

    class EgenPeriod(Bankperiod):
        __slots__ = ()

    with pytest.raises(KonteringsforslagFel, match="inte vara EgenPeriod"):
        skapa(kallor, bankavgiften(kallor), bankperiod=object.__new__(EgenPeriod))


def test_forslag_som_inte_ar_ett_objekt_stoppas(kallor):
    for varde, sort in [(None, "None"), ([], "en lista"), ("F-1", "text"), (Konstig(fakturan()), "Konstig")]:
        with pytest.raises(KonteringsforslagFel, match="förslaget") as fel:
            skapa(kallor, varde)
        assert fel.value.kontroll == "indata" and sort in str(fel.value)


# --- Täckningen (punkt 7, granskning 7 M1) ---
# Förslag där varje rad för sig kan räknas fram ur riktiga värden och debet = kredit, men där ett värde
# räknas två gånger eller ett belopp inte finns i någon källa. P01–P03 och P10 är granskarens prov.

U5 = "SYNT-U-2025-005"


def p01_dubbel_ingaende_moms():
    return forslag("2025-01-07", "Faktura LEV-TE, SYNT-TE-761", [
        rad("4010", 1493800, 0, "lika", underlag(U3, "underlag_ore", 12)),
        rad("2641", 179256, 0, "lika", underlag(U3, "moms_ore", 12)),
        rad("2641", 179256, 0, "lika", underlag(U3, "moms_ore", 12)),
        rad("2440", 0, 1852312, "summa", underlag(U3, "belopp_ore"), underlag(U3, "moms_ore", 12)),
    ], "R-LEV-TE", underlag_=[U3])


def p02_moms_bade_som_kostnad_och_avdrag():
    return forslag("2025-01-07", "Faktura LEV-TE, SYNT-TE-761", [
        rad("4010", 1673056, 0, "lika", underlag(U3, "belopp_ore")),
        rad("2641", 179256, 0, "lika", underlag(U3, "moms_ore", 12)),
        rad("2440", 0, 1852312, "summa", underlag(U3, "belopp_ore"), underlag(U3, "moms_ore", 12)),
    ], "R-LEV-TE", underlag_=[U3])


def p03_samma_bankrad_tva_ganger(kallor):
    bank = kallor.bankrad(kallor.januari, 3)
    return forslag("2025-01-03", "Kortinlösen för 2025-01-02", [
        rad("1940", 406562, 0, "lika", bankrad(bank)),
        rad("1940", 406562, 0, "lika", bankrad(bank)),
        rad("1580", 0, 406562, "lika", bankrad(bank)),
        rad("1581", 0, 406562, "lika", bankrad(bank)),
    ], "R-BANK-KORTINLOSEN", bankrader=[bank])


def p10_skillnad_mellan_tva_underlag():
    # 16 730,56 kr (SYNT-U-2025-003) minus 9 600,00 kr (SYNT-U-2025-005): ett belopp som inte finns i något underlag.
    return forslag("2025-01-07", "Skillnad mellan två fakturor", [
        rad("4010", 713056, 0, "skillnad", underlag(U3, "belopp_ore"), underlag(U5, "belopp_ore")),
        rad("2440", 0, 713056, "skillnad", underlag(U3, "belopp_ore"), underlag(U5, "belopp_ore")),
    ], "R-LEV-TE", underlag_=[U3, U5])


def underlaget_utan_momsen():
    # Fakturan utan momsraden: leverantörsskulden blir beloppet utan moms. Varje del används högst en
    # gång, men underlaget används inte helt.
    return forslag("2025-01-07", "Faktura LEV-TE, SYNT-TE-761", [
        rad("4010", 1493800, 0, "lika", underlag(U3, "underlag_ore", 12)),
        rad("2440", 0, 1493800, "lika", underlag(U3, "underlag_ore", 12)),
    ], "R-LEV-TE", underlag_=[U3])


def z_forsaljningen_med_moms_och_momsen():
    # Z 1001 med försäljningen 12 % inklusive moms på 3002 och momsen dessutom på 2621: momsen i kredit två
    # gånger. Debet har momsen på kassan för att summorna ska gå ihop.
    return forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 95600, 0, "lika", z("betalsatt_kontant")),
        rad("1580", 411500, 0, "lika", z("betalsatt_kort")),
        rad("1581", 89400, 0, "lika", z("betalsatt_swish")),
        rad("1910", 45450, 0, "lika", z("moms", 12)),
        rad("3002", 0, 424200, "lika", z("forsaljning", 12)),
        rad("2621", 0, 45450, "lika", z("moms", 12)),
        rad("3001", 0, 137840, "skillnad", z("forsaljning", 25), z("moms", 25)),
        rad("2611", 0, 34460, "lika", z("moms", 25)),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])


def z_totalsumman_och_forsaljningen():
    # Z 1001 med totalsumman i kredit och dessutom försäljningen per sats: försäljningen två gånger.
    return forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 95600, 0, "lika", z("betalsatt_kontant")),
        rad("1580", 411500, 0, "lika", z("betalsatt_kort")),
        rad("1581", 89400, 0, "lika", z("betalsatt_swish")),
        rad("1910", 596500, 0, "lika", z("summa_brutto")),
        rad("3002", 0, 596500, "lika", z("summa_brutto")),
        rad("3002", 0, 378750, "skillnad", z("forsaljning", 12), z("moms", 12)),
        rad("2621", 0, 45450, "lika", z("moms", 12)),
        rad("3001", 0, 137840, "skillnad", z("forsaljning", 25), z("moms", 25)),
        rad("2611", 0, 34460, "lika", z("moms", 25)),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])


TACKNING = {
    "p01_dubbel_ingaende_moms": (
        lambda kallor: p01_dubbel_ingaende_moms(),
        "i debet används underlaget 'SYNT-U-2025-003', momsraden med satsen 12 %, 'moms_ore' 2 gånger (rad 2 och 3)",
        "högst en gång i debet och en gång i kredit"),
    "p02_moms_bade_som_kostnad_och_avdrag": (
        lambda kallor: p02_moms_bade_som_kostnad_och_avdrag(),
        "i debet används underlaget 'SYNT-U-2025-003', momsraden med satsen 12 %, 'moms_ore' 2 gånger (rad 1 och 2)",
        "Ett underlags 'belopp_ore' räknas som alla dess momsraders 'underlag_ore' och 'moms_ore'"),
    "p03_samma_bankrad_tva_ganger": (
        p03_samma_bankrad_tva_ganger, "i debet används bankraden", "(radnummer 3) 2 gånger (rad 1 och 2)"),
    "p10_skillnad_mellan_tva_underlag": (
        lambda kallor: p10_skillnad_mellan_tva_underlag(),
        "i debet dras underlaget 'SYNT-U-2025-005', momsraden med satsen 0 %, 'underlag_ore' ifrån 1 gång mer än den"
        " läggs till (rad 1)", "En skillnad får bara dra ifrån något som samma sida också tar med"),
    "underlaget_utan_momsen": (
        lambda kallor: underlaget_utan_momsen(),
        "i debet används 14938,00 kr av underlaget 'SYNT-U-2025-003', men ett underlag ska användas helt eller inte"
        " alls på varje sida: 0 kr eller hela 'belopp_ore', 16730,56 kr. Det som saknas är underlaget"
        " 'SYNT-U-2025-003', momsraden med satsen 12 %, 'moms_ore': 1792,56 kr."),
    "z_forsaljningen_med_moms_och_momsen": (
        lambda kallor: z_forsaljningen_med_moms_och_momsen(),
        "i kredit används Z-rapport 1001 (TB-KASSA-1), momsen med satsen 12 % 2 gånger (rad 5 och 6)"),
    "z_totalsumman_och_forsaljningen": (
        lambda kallor: z_totalsumman_och_forsaljningen(),
        "i kredit används Z-rapport 1001 (TB-KASSA-1), försäljningen utan moms med satsen 12 % 2 gånger (rad 5"
        " och 6)"),
}


@pytest.mark.parametrize("fall", TACKNING.values(), ids=TACKNING.keys())
def test_tackningen_stoppar(kallor, fall):
    bygg, *texter = fall
    stoppas(kallor, bygg(kallor), "ursprung", *texter)


def test_tackningen_godtar_samma_del_i_debet_och_kredit(kallor):
    # 4e: bankraden står både på kostnaden (debet) och på bankkontot (kredit), en gång på varje sida.
    # 4d: bankraden läggs till och dras ifrån i debet (0 gånger), och kortförsäljningen står en gång per sida.
    assert skapa(kallor, bankavgiften(kallor))
    assert skapa(kallor, kortinlosen(kallor))


def test_tackningen_godtar_underlaget_som_skillnad_mellan_beloppet_och_momsen(kallor):
    # Kostnaden räknad som 'belopp_ore' minus momsen: underlaget används ändå helt, en gång per sida.
    data = fakturan()
    rader(data)[0]["ursprung"] = {"berakning": "skillnad",
                                  "fran": [underlag(U3, "belopp_ore"), underlag(U3, "moms_ore", 12)]}
    assert skapa(kallor, data)


def test_tackningen_godtar_totalsumman_mot_betalsatten(kallor):
    # Totalsumman i kredit och betalsätten i debet: varje del en gång per sida.
    data = forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 95600, 0, "lika", z("betalsatt_kontant")),
        rad("1580", 411500, 0, "lika", z("betalsatt_kort")),
        rad("1581", 89400, 0, "lika", z("betalsatt_swish")),
        rad("3002", 0, 596500, "lika", z("summa_brutto")),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])
    assert skapa(kallor, data)


# --- Momskontona (punkt 5, granskning 7 M2) ---

def p04_kassans_moms_pa_ingaende_moms():
    data = z_1001()
    rader(data)[4]["konto"] = "2641"
    rader(data)[6]["konto"] = "2641"
    return data


def p05_fakturans_moms_pa_utgaende_moms():
    data = fakturan()
    rader(data)[1]["konto"] = "2621"
    return data


def test_p04_kassans_moms_pa_kontot_for_ingaende_moms_stoppas(kallor):
    stoppas(kallor, p04_kassans_moms_pa_ingaende_moms(), "ursprung",
            "rad 5 (konto 2641) är kontot för ingående moms, men källan Z-rapport 1001 (TB-KASSA-1), posten 'moms' med"
            " satsen 12 % är momsen i en Z-rapport. Ingående moms ska komma från momsen i en momsrad i ett underlag"
            " ('moms_ore')")


def test_p05_fakturans_moms_pa_kontot_for_utgaende_moms_stoppas(kallor):
    stoppas(kallor, p05_fakturans_moms_pa_utgaende_moms(), "ursprung",
            "rad 2 (konto 2621) är kontot för utgående moms med satsen 12 %, men källan underlaget 'SYNT-U-2025-003',"
            " momsraden med satsen 12 %, 'moms_ore' är momsen i ett underlag. Utgående moms ska komma från en momspost"
            " i en Z-rapport")


def test_k2_kors_fore_ursprunget(kallor):
    # En rad utan källor och med obalans: K2 stoppar först, som i DESIGN avsnitt 3.
    data = fakturan()
    rader(data)[0]["debet_ore"] += 1
    rader(data)[0]["ursprung"]["fran"] = []
    stoppas(kallor, data, "K2", "summan av debet")


# --- Regeln passar förslaget (punkt 8, granskning 7 M3) ---
# P06a, P06b och P07 är granskarens prov. Varje förslag har riktiga källor, och debet = kredit.

REGELN = {
    # P06a: LEV-TE-fakturan med en regel för bankrader.
    "p06a_regel_for_bankrader_pa_fakturan": (fakturan, satt("kopplingar", "regel", "id", varde="R-BANK-AVGIFT"),
                                             "regeln 'R-BANK-AVGIFT' gäller bankrader, men förslaget har inga"
                                             " bankrader i 'bankrader' i 'kopplingar'. Regeln passar inte förslaget"),
    # P06b: kostnaden på 6071 Representation, men regeln R-LEV-TE säger 4010.
    "p06b_konto_som_regeln_inte_har": (fakturan, satt("verifikation", "rader", 0, "konto", varde="6071"),
                                       "rad 1 (konto 6071): kontot står inte i regeln 'R-LEV-TE' och har ingen roll i"
                                       " kontoplanen. Regelns konton är 4010."),
    # P07: verifikationen före regelns första dag (fakturan är daterad 2025-01-07).
    "p07_datum_fore_regelns_forsta_dag": (fakturan, satt("verifikation", "datum", varde="2024-06-01"),
                                          "regeln 'R-LEV-TE' gäller från 2025-01-01 till tills vidare, men"
                                          " verifikationens datum är 2024-06-01."),
    "underlag_med_en_annan_motparts_regel": (fakturan, satt("kopplingar", "regel", "id", varde="R-LEV-FORSAKRING"),
                                             "regeln i 'kopplingar' är 'R-LEV-FORSAKRING', men underlaget"
                                             " 'SYNT-U-2025-003' (leverantorsfaktura från 'LEV-TE') har regeln"
                                             " 'R-LEV-TE' på 2025-01-07"),
    "z_rapport_med_en_regel_for_underlag": (z_1001, satt("kopplingar", "regel", "id", varde="R-LEV-TE"),
                                            "regeln 'R-LEV-TE' gäller underlag, men förslaget har inga underlag i"
                                            " 'underlag' i 'kopplingar'"),
    "z_rapport_med_en_regel_for_bankrader": (z_1001, satt("kopplingar", "regel", "id", varde="R-BANK-SWISH"),
                                             "regeln 'R-BANK-SWISH' gäller bankrader, men förslaget har inga"
                                             " bankrader"),
    "bankrad_med_en_annan_regel": (bankavgiften, satt("kopplingar", "regel", "id", varde="R-BANK-SWISH"),
                                   "regeln i 'kopplingar' är 'R-BANK-SWISH', men bankraden",
                                   "(radnummer 117) (regeln 'bankens-avgifter' i matchningsformatet) har regeln"
                                   " 'R-BANK-AVGIFT' på 2025-01-31"),
    "bankrad_som_inte_passar_matchningsformatet": (betalningen, satt("kopplingar", "regel", "id",
                                                                     varde="R-BANK-AVGIFT"),
                                                   "(radnummer 26), som inte passar någon regel för bankrader utan"
                                                   " underlag i matchningsformatet, har ingen regel i regelboken på"
                                                   " 2025-02-06"),
    "bankrad_med_konto_som_regeln_inte_har": (bankavgiften, satt("verifikation", "rader", 0, "konto", varde="4010"),
                                              "rad 1 (konto 4010): kontot står inte i regeln 'R-BANK-AVGIFT' och har"
                                              " ingen roll i kontoplanen. Regelns konton är 6570."),
    "z_rapport_med_konto_som_regeln_inte_har": (z_1001, satt("verifikation", "rader", 3, "konto", varde="6570"),
                                                "rad 4 (konto 6570): kontot står inte i regeln 'R-Z-TB-KASSA-1' och har"
                                                " ingen roll i kontoplanen. Regelns konton är 1580, 1581, 1910, 3001,"
                                                " 3002."),
}


@pytest.mark.parametrize("fall", REGELN.values(), ids=REGELN.keys())
def test_stoppregel_regeln(kallor, fall):
    bygg, texter = bygg_fall(fall)
    stoppas(kallor, bygg(kallor), "ursprung", *texter)


def regelbok_med(kallor, tmp_path, andring):
    """Testbutikens regelbok med andring(regelboken) gjord, och dess kontrollsumma."""
    data = json.loads((TESTBUTIKEN / "regelbok.json").read_text(encoding="utf-8"))
    andring(data)
    fil = tmp_path / "regelbok.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return las_regelbok(fil, kallor.kontoplan, kallor.momssatser, kallor.matchning), sha256(fil)


def skapa_med_regelboken(kallor, data, regelbok, summa):
    data["kopplingar"]["regel"]["regelbokens_kontrollsumma"] = summa
    return skapa_konteringsforslag(data, regelbok, kallor.kontoplan, **kallor.perioder())


def regeln(data, regelns_id):
    return [regel for regel in data["regler"] if regel["id"] == regelns_id][0]


def test_datum_efter_regelns_sista_dag_stoppas(kallor, tmp_path):
    # R-LEV-TE slutar 2025-01-31: fakturan (2025-01-07) godtas, betalningen (2025-02-06) stoppas.
    regelbok, summa = regelbok_med(kallor, tmp_path,
                                   lambda d: regeln(d, "R-LEV-TE")["villkor"].update(giltig_till="2025-01-31"))
    assert skapa_med_regelboken(kallor, fakturan(), regelbok, summa)
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_med_regelboken(kallor, betalningen(kallor), regelbok, summa)
    assert fel.value.kontroll == "ursprung"
    assert ("regeln 'R-LEV-TE' gäller från 2025-01-01 till 2025-01-31, men verifikationens datum är 2025-02-06."
            in str(fel.value))


def test_z_rapport_med_ett_annat_kassaregisters_regel_stoppas(kallor, tmp_path):
    # En regel till för ett annat kassaregister, med samma kontering. Z 1001 kommer från TB-KASSA-1.
    def ny_regel(data):
        ny = copy.deepcopy(regeln(data, "R-Z-TB-KASSA-1"))
        ny.update(id="R-Z-ANNAN-KASSA", galler={"kalla": "z_rapport", "kassaregister": "ANNAN-KASSA"})
        data["regler"].append(ny)

    regelbok, summa = regelbok_med(kallor, tmp_path, ny_regel)
    assert skapa_med_regelboken(kallor, z_1001(), regelbok, summa)
    data = z_1001()
    data["kopplingar"]["regel"]["id"] = "R-Z-ANNAN-KASSA"
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_med_regelboken(kallor, data, regelbok, summa)
    assert fel.value.kontroll == "ursprung"
    assert ("regeln i 'kopplingar' är 'R-Z-ANNAN-KASSA', men Z-rapport 1001 (TB-KASSA-1) har regeln 'R-Z-TB-KASSA-1'"
            " på 2025-01-02" in str(fel.value))


def test_regeln_godtar_rollkontona_och_regelns_egna_konton(kallor):
    # Skydd: exemplen i DESIGN 4 använder både regelns konton och rollkontona (bank, leverantörsskulder,
    # ingående och utgående moms), och alla godtas.
    for data in (fakturan(), betalningen(kallor), z_1001(), kortinlosen(kallor), bankavgiften(kallor)):
        assert skapa(kallor, data)


# --- Kontrollsummorna (K2 punkt 1, granskning 7 M4) ---

def kontoplan_med(tmp_path, andring):
    """Testbutikens kontoplan med andring(kontoplanen) gjord, läst med las_kontoplan, och filen."""
    data = json.loads((TESTBUTIKEN / "kontoplan.json").read_text(encoding="utf-8"))
    andring(data)
    fil = tmp_path / "kontoplan.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return las_kontoplan(fil), fil


def bankkontot_fran_fakturan():
    """P08: 1940 i debet ur fakturans belopp_ore, och leverantörsskulden i kredit."""
    return forslag("2025-01-07", "Faktura LEV-TE, SYNT-TE-761", [
        rad("1940", 1673056, 0, "lika", underlag(U3, "belopp_ore")),
        rad("2440", 0, 1673056, "lika", underlag(U3, "belopp_ore")),
    ], "R-LEV-TE", underlag_=[U3])


def test_p08b_en_annan_kontoplan_an_regelbokens_stoppas(kallor, tmp_path):
    # P08: med testbutikens kontoplan stoppas förslaget, eftersom 1940 är bankkontot och ska ha en bankrad.
    stoppas(kallor, bankkontot_fran_fakturan(), "ursprung", "rad 1 (konto 1940) är bankkontot")
    # P08b: med en kontoplan där rollen bank är 1910 godtog den gamla koden samma förslag, med
    # testbutikens regelbok. Kontoplanen är inte den som regelboken kontrollerades mot.
    annan, fil = kontoplan_med(tmp_path, lambda d: d["roller"].update(bank="1910"))
    data = bankkontot_fran_fakturan()
    data["kopplingar"]["regel"]["kontoplanens_kontrollsumma"] = sha256(fil)
    with pytest.raises(KonteringsforslagFel) as fel:
        skapa_konteringsforslag(data, kallor.regelbok, annan, **kallor.perioder())
    assert fel.value.kontroll == "K2"
    assert str(fel.value).startswith("Konteringsförslaget skapas inte (K2): kontoplanen är inte den som regelboken"
                                     " kontrollerades mot. Kontoplanens kontrollsumma är '" + sha256(fil)[:16] + "…'")


@pytest.mark.parametrize("nyckel, vad, filnamn", [
    ("regelbokens_kontrollsumma", "regelboken", "regelbok.json"),
    ("kontoplanens_kontrollsumma", "kontoplanen", "kontoplan.json"),
    ("momsfilens_kontrollsumma", "momsfilen som regelboken kontrollerades mot", "momssatser.json"),
    ("matchningsformatets_kontrollsumma", "matchningsformatet som regelboken kontrollerades mot", "matchning.json"),
])
def test_en_kontrollsumma_som_inte_ar_den_inlasta_filens_stoppas(kallor, nyckel, vad, filnamn):
    fil = TESTBUTIKEN / filnamn
    stoppas(kallor, andrat(fakturan, satt("kopplingar", "regel", nyckel, varde="0" * 64))(kallor), "K2",
            "förslaget är byggt mot en annan fil: '" + nyckel + "' i 'regel' i 'kopplingar' är '" + "0" * 16 + "…', men "
            + vad + " har kontrollsumman '" + sha256(fil)[:16] + "…'.")


def test_kontrollsummorna_i_forslaget_kommer_fran_de_inlasta_filerna(kallor):
    regel = skapa(kallor, fakturan()).kopplingar["regel"]
    assert regel == {"id": "R-LEV-TE", **kontrollsummor()}
    assert regel["kontoplanens_kontrollsumma"] == kallor.kontoplan.kontrollsumma
    assert regel["momsfilens_kontrollsumma"] == kallor.momssatser.kontrollsumma
    assert regel["matchningsformatets_kontrollsumma"] == kallor.matchning.kontrollsumma


def test_p15_en_andrad_kontoplan_ger_en_annan_kontrollsumma_i_forslaget(kallor, tmp_path):
    # P15: samma regelbok, men en kontoplan där 4010 heter "Eget uttag". Regelboken godtar den, men
    # kontrollsumman i regelboken och i förslaget är en annan.
    def nytt_namn(data):
        [konto for konto in data["konton"] if konto["nummer"] == "4010"][0]["namn"] = "Eget uttag"

    andrad, fil = kontoplan_med(tmp_path, nytt_namn)
    regelbok = las_regelbok(TESTBUTIKEN / "regelbok.json", andrad, kallor.momssatser, kallor.matchning)
    assert regelbok.kontrollsumma == kallor.regelbok.kontrollsumma
    assert regelbok.kontrollerad_mot["kontoplan"] == sha256(fil) != kallor.regelbok.kontrollerad_mot["kontoplan"]
    data = fakturan()
    data["kopplingar"]["regel"]["kontoplanens_kontrollsumma"] = sha256(fil)
    resultat = skapa_konteringsforslag(data, regelbok, andrad, **kallor.perioder())
    assert resultat.kopplingar["regel"]["kontoplanens_kontrollsumma"] == sha256(fil) != sha256(
        TESTBUTIKEN / "kontoplan.json")
    # Den ändrade kontoplanen med testbutikens regelbok stoppas.
    with pytest.raises(KonteringsforslagFel, match="kontoplanen är inte den som regelboken kontrollerades mot"):
        skapa_konteringsforslag(data, kallor.regelbok, andrad, **kallor.perioder())


@pytest.mark.parametrize("nyckel", ["regelbokens_kontrollsumma", "kontoplanens_kontrollsumma",
                                    "momsfilens_kontrollsumma", "matchningsformatets_kontrollsumma"])
def test_en_kontrollsumma_som_saknas_eller_inte_ar_text_stoppas(kallor, nyckel):
    stoppas(kallor, andrat(fakturan, ta_bort("kopplingar", "regel", nyckel))(kallor), "indata",
            "'regel' i 'kopplingar' saknar nyckeln '" + nyckel + "'")
    stoppas(kallor, andrat(fakturan, satt("kopplingar", "regel", nyckel, varde=None))(kallor), "indata",
            "'" + nyckel + "' i 'regel' i 'kopplingar' ska vara text, inte None")


# --- Granskning 7, M6: en egen variant av regelboken eller kontoplanen ---
# Varianterna är underklasser skapade med object.__new__. De svarar som testbutikens regelbok och
# kontoplan, utom på en punkt som släpper igenom ett fel förslag. Med isinstance() i stället för type()
# (Mut5 och Mut6) skapades förslaget.

def fakturan_pa_representation():
    """P06b: fakturan SYNT-U-2025-003 med kostnaden på 6071, som regeln R-LEV-TE inte har."""
    data = fakturan()
    data["verifikation"]["rader"][0]["konto"] = "6071"
    return data


def test_m6_egen_variant_av_regelboken_stoppas(kallor):
    from las_regelbok import Regelbok

    riktig = kallor.regelbok

    class EgenRegelbok(Regelbok):
        """Testbutikens regelbok, men R-LEV-TE bokför på 6071."""

        __slots__ = ()

        def __getattribute__(self, namn):
            if namn == "regler":
                regler = riktig.regler
                for regel in regler:
                    if regel["id"] == "R-LEV-TE":
                        regel["kontering"] = {"livsmedel": "6071"}
                return regler
            return getattr(riktig, namn)

    stoppas(kallor, fakturan_pa_representation(), "ursprung", "kontot står inte i regeln 'R-LEV-TE'")
    with pytest.raises(KonteringsforslagFel, match="regelboken ska komma från las_regelbok, inte vara EgenRegelbok"):
        skapa_konteringsforslag(fakturan_pa_representation(), object.__new__(EgenRegelbok), kallor.kontoplan,
                                **kallor.perioder())


def test_m6_egen_variant_av_kontoplanen_stoppas(kallor):
    from las_kontoplan import Kontoplan

    riktig = kallor.kontoplan

    class EgenKontoplan(Kontoplan):
        """Testbutikens kontoplan, men bankkontot 1940 har rollen för leverantörsskulder i stället för bank."""

        __slots__ = ()

        def __getattribute__(self, namn):
            if namn == "kontots_roller":
                return lambda nummer: [("leverantorsskulder", None)] if nummer == "1940" else riktig.kontots_roller(nummer)
            return getattr(riktig, namn)

    # P08: bankkontot ur fakturans belopp_ore stoppas med den riktiga kontoplanen.
    stoppas(kallor, bankkontot_fran_fakturan(), "ursprung", "rad 1 (konto 1940) är bankkontot")
    with pytest.raises(KonteringsforslagFel, match="kontoplanen ska komma från las_kontoplan, inte vara EgenKontoplan"):
        skapa_konteringsforslag(bankkontot_fran_fakturan(), kallor.regelbok, object.__new__(EgenKontoplan),
                                **kallor.perioder())


# --- Granskning 7, M12: regelbok, kontoplan och perioder skapade med __new__ ---

@pytest.mark.parametrize("namn, text", [
    ("regelbok", "regelboken är tom eller trasig: den har inte skapats av las_regelbok."),
    ("kontoplan", "kontoplanen är tom eller trasig: den har inte skapats av las_kontoplan."),
    ("underlagsperiod", "underlagsperioden är tom eller trasig: den har inte skapats av las_underlagsperiod."),
    ("bankperiod", "bankperioden är tom eller trasig: den har inte skapats av las_bankfil eller sla_ihop_bankperioder."),
    ("kassaperiod", "kassaperioden är tom eller trasig: den har inte skapats av las_kassaperiod."),
])
def test_m12_tomt_objekt_ger_ett_tydligt_fel(kallor, namn, text):
    # P09: förut gav en Kontoplan skapad med __new__ ett AttributeError, som inte förklarar något.
    argument = {"regelbok": kallor.regelbok, "kontoplan": kallor.kontoplan, **kallor.perioder()}
    argument[namn] = object.__new__(type(argument[namn]))
    with pytest.raises(KonteringsforslagFel, match=re.escape(text)) as fel:
        skapa_konteringsforslag(fakturan(), **argument)
    assert fel.value.kontroll == "indata"


# --- Granskning 7, M10: den minsta negativa posten i en Z-rapport ---

def test_m10_negativ_post_pa_ett_ore_i_z_rapporten_stoppas(kallor, tmp_path):
    # Mut4: bara -0,02 kr och lägre stoppades. Samma påhittade Z-rapport som i
    # test_negativ_post_i_z_rapporten_stoppas, men kontanterna är -0,01 kr.
    mapp = tmp_path / "kassa"
    mapp.mkdir()
    text = (DATAMAPP / "kassa" / "kassa_2025-01-02.csv").read_text(encoding="utf-8")
    text = text.replace("betalsatt_kontant,,956.00", "betalsatt_kontant,,-0.01")
    text = text.replace("betalsatt_kort,,4115.00", "betalsatt_kort,,5071.01")
    (mapp / "kassa_2025-01-02.csv").write_text(text, encoding="utf-8")
    kassaperiod = las_kassaperiod(mapp, kallor.kassaformat, "2025-01-02", "2025-01-02")
    data = forslag("2025-01-02", "Kassa Z 1001", [
        rad("1910", 0, 1, "lika", z("betalsatt_kontant")),
        rad("1580", 1, 0, "lika", z("betalsatt_kontant")),
    ], "R-Z-TB-KASSA-1", z_rapporter=[1001])
    stoppas(kallor, data, "ursprung", "posten 'betalsatt_kontant' är negativ (-0,01 kr)", "returer",
            kassaperiod=kassaperiod)


# --- Granskning 8, N3: en bankrad mot ägaren undantas aldrig av en regel i matchningsformatet ---

def test_n3_bankavgift_mot_agaren_stoppas(kallor, tmp_path):
    # Båda raderna passar regeln bankavgift i matchningsformatet, men i rad 1 står ägaren AGARE-1 med ett
    # snedstreck intill. Förut godtogs förslaget med R-BANK-AVGIFT för rad 1, så att ägarens rad slapp
    # underlag. Rad 2 är skyddet: samma förslag utan ägaren godtas.
    fil = tmp_path / "bank.csv"
    fil.write_text("\n".join([
        "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo",
        "1,2025-04-01,2025-04-01,AVG-1,BANK AVGIFT AGARE-1/APRIL,-100.00,9900.00",
        "2,2025-04-02,2025-04-02,AVG-2,BANK AVGIFT APRIL,-100.00,9800.00",
    ]) + "\n", encoding="utf-8")
    bankperiod = las_bankfil(fil, ladda_bankformat(TESTBUTIKEN / "bankformat.json"), 1000000, 980000)

    def avgiften(bankraden):
        return forslag(bankraden["transaktionsdag"], "Bankavgift", [
            rad("6570", 10000, 0, "lika", bankrad(bankraden["id"])),
            rad("1940", 0, 10000, "lika", bankrad(bankraden["id"])),
        ], "R-BANK-AVGIFT", bankrader=[bankraden["id"]])

    agarens, vanlig = bankperiod.rader
    assert skapa(kallor, avgiften(vanlig), bankperiod=bankperiod).kopplingar["bankrader"][0]["radnr"] == 2
    stoppas(kallor, avgiften(agarens), "ursprung", "(radnummer 1), som är mot en ägare eller närstående",
            "har ingen regel i regelboken", bankperiod=bankperiod)
