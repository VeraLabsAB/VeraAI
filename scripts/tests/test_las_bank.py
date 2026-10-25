"""Tester för inläsning av bankfiler och kontroll K1 (saldokedjan).

Testdatan är SYNTETISK (Syntet Testbutik AB, 2025-Q1). Rätt svar står i facit.json.
"""

import csv
import io
import json
import os
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"

sys.path.insert(0, str(AGENT / "scripts"))

import las_bank
from las_bank import (
    Bankperiod, BankfilFel, K1Fel, _tolka_rader, kontrollera_k1, ladda_bankformat, las_bankfil, sla_ihop_bankperioder,
)

BANKFORMAT_FIL = AGENT / "foretag" / "syntet-testbutik" / "bankformat.json"
BANKFORMAT = ladda_bankformat(BANKFORMAT_FIL)

MANADER = ["2025-01", "2025-02", "2025-03"]
FALT = ["id", "bokforingsdag", "transaktionsdag", "referens", "beskrivning",
        "belopp_ore", "saldo_efter_ore", "kalla_fil", "radnr"]


def facit():
    return json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))


def bankfil(manad):
    return DATAMAPP / facit()["bank"][manad]["fil"]


def saldon(manad):
    """(ingående saldo, utgående saldo) i öre för månaden, enligt facit."""
    fakta = facit()["bank"][manad]
    return fakta["ingaende_saldo_ore"], fakta["utgaende_saldo_ore"]


def utan_kalla_fil(rader):
    return [{k: v for k, v in rad.items() if k != "kalla_fil"} for rad in rader]


# --- (a) Januari och februari klarar K1 ---

def test_januari_och_februari_klarar_k1():
    bank = facit()["bank"]
    januari = las_bankfil(bankfil("2025-01"), BANKFORMAT, *saldon("2025-01")).rader
    assert januari[-1]["saldo_efter_ore"] == bank["2025-01"]["utgaende_saldo_ore"]

    # Februaris ingående saldo är januaris utgående, både i facit och i filen.
    assert bank["2025-02"]["ingaende_saldo_ore"] == bank["2025-01"]["utgaende_saldo_ore"]
    februari = las_bankfil(bankfil("2025-02"), BANKFORMAT, januari[-1]["saldo_efter_ore"],
                           bank["2025-02"]["utgaende_saldo_ore"]).rader
    assert februari[-1]["saldo_efter_ore"] == bank["2025-02"]["utgaende_saldo_ore"]


def test_raderna_har_ratt_falt():
    rader = las_bankfil(bankfil("2025-01"), BANKFORMAT, *saldon("2025-01")).rader
    assert all(list(rad) == FALT for rad in rader)
    assert rader[0]["radnr"] == 1
    assert rader[0]["bokforingsdag"] == "2025-01-02"
    assert rader[0]["referens"] == "SWISH-20250102-1"
    assert rader[0]["belopp_ore"] == 32300
    assert rader[0]["saldo_efter_ore"] == 8532300
    assert len({rad["id"] for rad in rader}) == len(rader)  # unika id
    assert len({rad["kalla_fil"] for rad in rader}) == 1
    assert len(rader[0]["kalla_fil"]) == 64  # SHA-256 i hex


def test_fel_ingaende_saldo_stoppar_januari():
    with pytest.raises(K1Fel) as fel:
        ingaende, utgaende = saldon("2025-01")
        las_bankfil(bankfil("2025-01"), BANKFORMAT, ingaende + 1, utgaende)
    assert fel.value.radnr == 1
    assert fel.value.skillnad_ore == -1


# --- (b) Mars stoppas av K1 på radnummer 74 ---

def test_mars_stoppas_av_k1_pa_raden_som_facit_anger():
    planterat = [f for f in facit()["planterade_fel"] if f["typ"] == "brott_i_saldokedjan"][0]
    resultat = None
    with pytest.raises(K1Fel) as fel:
        resultat = las_bankfil(bankfil("2025-03"), BANKFORMAT, *saldon("2025-03"))
    assert resultat is None  # ingen rad returneras

    assert fel.value.radnr == planterat["rad"] == 74
    assert fel.value.forvantat_ore == planterat["ratt_saldo_ore"]
    assert fel.value.faktiskt_ore == planterat["visat_saldo_ore"]
    assert fel.value.skillnad_ore == 10000

    meddelande = str(fel.value)
    assert "radnummer 74" in meddelande
    assert "förväntat saldo 289911,38 kr" in meddelande.lower()
    assert "faktiskt saldo 290011,38 kr" in meddelande
    assert "skillnad 100,00 kr" in meddelande
    print("\nFelmeddelandet för mars:\n" + meddelande)


def test_k1_godkanner_korrekt_kedja_och_stoppar_pa_forsta_felet():
    rader = [
        {"radnr": 1, "belopp_ore": 100, "saldo_efter_ore": 100},
        {"radnr": 2, "belopp_ore": 50, "saldo_efter_ore": 150},
        {"radnr": 3, "belopp_ore": -20, "saldo_efter_ore": 130},
    ]
    kontrollera_k1(rader, 0, 130)

    rader[1]["saldo_efter_ore"] = 160  # rad 2 fel, och därmed även rad 3 räknat från rad 2
    with pytest.raises(K1Fel) as fel:
        kontrollera_k1(rader, 0, 130)
    assert fel.value.radnr == 2
    assert fel.value.skillnad_ore == 10


# --- (c) Antal rader och summan av beloppen stämmer med facit ---

@pytest.mark.parametrize("manad", MANADER)
def test_antal_rader_och_summa_stammer_med_facit(manad):
    fakta = facit()["bank"][manad]
    # _tolka_rader kör inte K1, så även mars kan räknas här.
    rader = _tolka_rader(bankfil(manad).read_bytes(), BANKFORMAT)
    assert len(rader) == fakta["antal_rader"]
    assert sum(rad["belopp_ore"] for rad in rader) == fakta["utgaende_saldo_ore"] - fakta["ingaende_saldo_ore"]


# --- (d) Kodning, avgränsare och rader före rubriken ---

def test_windows_1252_ger_samma_resultat(tmp_path):
    original = bankfil("2025-01")
    kopia = tmp_path / "bank_cp1252.csv"
    kopia.write_bytes(original.read_text(encoding="utf-8").encode("cp1252"))
    assert kopia.read_bytes() != original.read_bytes()

    fran_original = las_bankfil(original, BANKFORMAT, *saldon("2025-01")).rader
    fran_kopia = las_bankfil(kopia, BANKFORMAT, *saldon("2025-01")).rader
    # Allt är lika utom kontrollsumman av filen, eftersom filerna har olika bytes.
    assert utan_kalla_fil(fran_kopia) == utan_kalla_fil(fran_original)
    assert fran_kopia[0]["kalla_fil"] != fran_original[0]["kalla_fil"]


def test_semikolon_och_rader_fore_rubriken_ger_samma_resultat(tmp_path):
    original = bankfil("2025-01")
    with open(original, encoding="utf-8", newline="") as fil:
        rader = list(csv.reader(fil))
    text = io.StringIO()
    text.write("* Transaktionsrapport\r\n")
    text.write("Period;2025-01-01;2025-01-31\r\n")
    csv.writer(text, delimiter=";").writerows(rader)
    kopia = tmp_path / "bank_semikolon.csv"
    kopia.write_bytes(text.getvalue().encode("utf-8"))
    assert kopia.read_text(encoding="utf-8").splitlines()[2].startswith("Radnummer;")

    fran_original = las_bankfil(original, BANKFORMAT, *saldon("2025-01")).rader
    fran_kopia = las_bankfil(kopia, BANKFORMAT, *saldon("2025-01")).rader
    assert utan_kalla_fil(fran_kopia) == utan_kalla_fil(fran_original)
    assert fran_kopia[0]["kalla_fil"] != fran_original[0]["kalla_fil"]


# --- (e) Beloppen är heltal ---

def test_beloppen_ar_heltal_aldrig_float():
    rader = las_bankfil(bankfil("2025-01"), BANKFORMAT, *saldon("2025-01")).rader
    for rad in rader:
        for falt in ("belopp_ore", "saldo_efter_ore", "radnr"):
            assert type(rad[falt]) is int, (rad["radnr"], falt)


def test_k1_vagrar_float():
    with pytest.raises(TypeError):
        kontrollera_k1([{"radnr": 1, "belopp_ore": 1.0, "saldo_efter_ore": 1}], 0, 1)
    with pytest.raises(TypeError):
        kontrollera_k1([{"radnr": 1, "belopp_ore": 1, "saldo_efter_ore": 1}], 0.0, 1)
    with pytest.raises(TypeError):
        kontrollera_k1([{"radnr": 1, "belopp_ore": 1, "saldo_efter_ore": 1}], 0, 1.0)


# --- (f) Ogiltiga filer stoppas med tydligt fel ---

RUBRIK = "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo\n"


def skriv(tmp_path, innehall):
    fil = tmp_path / "bank.csv"
    fil.write_text(innehall, encoding="utf-8")
    return fil


def test_ogiltigt_belopp_stoppar_filen(tmp_path):
    fil = skriv(tmp_path, RUBRIK
                + "1,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n"
                + "2,2025-01-02,2025-01-02,REF-2,MOTPART-B,12.3x,112.30\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 11230)
    meddelande = str(fel.value)
    assert "rad 3 i filen" in meddelande
    assert "ogiltigt belopp" in meddelande
    assert "'Belopp'" in meddelande
    assert "'12.3x'" in meddelande


@pytest.mark.parametrize(
    "rad, text",
    [
        ("1,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00,100.005\n", "ogiltigt belopp"),
        ("1,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00\n", "fält"),
        ("1,2025-02-30,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n", "ogiltigt datum"),
        ("1,20250102,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n", "ogiltigt datum"),
        ("x,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n", "ogiltigt radnummer"),
    ],
)
def test_andra_ogiltiga_rader_stoppar_filen(tmp_path, rad, text):
    with pytest.raises(BankfilFel, match=text):
        las_bankfil(skriv(tmp_path, RUBRIK + rad), BANKFORMAT, 0, 10000)


def test_fil_utan_rubrikrad_stoppas(tmp_path):
    with pytest.raises(BankfilFel, match="ingen rubrikrad"):
        las_bankfil(skriv(tmp_path, "1,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n"), BANKFORMAT, 0, 10000)


def test_fil_utan_transaktioner_stoppas(tmp_path):
    with pytest.raises(BankfilFel, match="inga transaktionsrader"):
        las_bankfil(skriv(tmp_path, RUBRIK), BANKFORMAT, 0, 0)


def test_okand_teckenkodning_stoppas(tmp_path):
    fil = tmp_path / "bank.csv"
    fil.write_bytes(RUBRIK.encode("utf-8") + b"1,2025-01-02,2025-01-02,REF-\x81,M,1.00,1.00\n")
    with pytest.raises(BankfilFel, match="teckenkodningen"):
        las_bankfil(fil, BANKFORMAT, 0, 100)


# --- Rättelser efter granskningen (GRANSKNING.md) ---

def test_f2_avklippt_fil_stoppas(tmp_path):
    """F2 och F10: en fil där sista raden saknas stoppas av jämförelsen med utgående saldo."""
    rader = bankfil("2025-01").read_bytes().splitlines(keepends=True)
    kopia = tmp_path / "bank_avklippt.csv"
    kopia.write_bytes(b"".join(rader[:-1]))

    ingaende, utgaende = saldon("2025-01")
    resultat = None
    with pytest.raises(K1Fel) as fel:
        resultat = las_bankfil(kopia, BANKFORMAT, ingaende, utgaende)
    assert resultat is None
    assert fel.value.radnr == 117  # sista raden som finns kvar
    assert fel.value.forvantat_ore == utgaende
    assert fel.value.skillnad_ore == 19900  # den bortklippta bankavgiften, 199,00 kr
    assert "kan sakna rader" in str(fel.value)
    assert "utgående saldo" in str(fel.value)


def test_f1_citattecken_som_slar_ihop_rader_stoppas(tmp_path):
    """F1: granskarens fall 4g. Tre transaktioner som läses som en ska stoppas."""
    fil = skriv(tmp_path, RUBRIK
                + '1,2025-01-03,2025-01-03,REF-1,"A,200.00,200.00\n'
                + "2,2025-01-04,2025-01-04,REF-2,B,-200.00,0.00\n"
                + '3,2025-01-28,2025-01-28,REF-3,C",75.00,75.00\n')
    resultat = None
    with pytest.raises(BankfilFel) as fel:
        resultat = las_bankfil(fil, BANKFORMAT, 0, 7500)  # rätt ingående och utgående saldo
    assert resultat is None
    assert "rad 2 i filen" in str(fel.value)
    assert "radbrytning" in str(fel.value)


@pytest.mark.parametrize("radbrytning", ["\n", "\r", "\r\n", "\u2028", "\u2029"])
def test_f1_radbrytning_inuti_falt_stoppas(tmp_path, radbrytning):
    fil = skriv(tmp_path, RUBRIK
                + '1,2025-01-02,2025-01-02,REF-1,"RAD ETT' + radbrytning + 'RAD TVA",100.00,100.00\n')
    with pytest.raises(BankfilFel, match="radbrytning"):
        las_bankfil(fil, BANKFORMAT, 0, 10000)


@pytest.mark.parametrize(
    "radnummer, felrad, text",
    [
        ([1, 1, 2], 3, "radnummer 1, men nästa radnummer ska vara 2"),  # dubbla
        ([1, 3, 2], 3, "radnummer 3, men nästa radnummer ska vara 2"),  # osorterade
        ([2, 1, 3], 2, "radnummer 2, men nästa radnummer ska vara 1"),  # osorterade
        ([1, 5, 6], 3, "radnummer 5, men nästa radnummer ska vara 2"),  # saknade
    ],
    ids=["dubbla", "osorterade", "osorterade_forsta", "saknade"],
)
def test_f4_radnummer_maste_vara_1_2_3_i_tur_och_ordning(tmp_path, radnummer, felrad, text):
    """F4: saldokedjan stämmer i filens ordning, men radnumren är fel."""
    rader = "".join(
        str(nr) + ",2025-01-02,2025-01-02,REF-" + str(i) + ",M," + "1.00," + str(i + 1) + ".00\n"
        for i, nr in enumerate(radnummer)
    )
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(skriv(tmp_path, RUBRIK + rader), BANKFORMAT, 0, 300)
    assert "rad " + str(felrad) + " i filen" in str(fel.value)
    assert text in str(fel.value)


def test_f6_identiska_rader_stoppas(tmp_path):
    """F6: två helt identiska rader på 0 kr skulle få samma id. Nu stoppas filen."""
    rad = "1,2025-01-02,2025-01-02,REF-1,M,0.00,0.00\n"
    with pytest.raises(BankfilFel, match="radnummer 1, men nästa radnummer ska vara 2"):
        las_bankfil(skriv(tmp_path, RUBRIK + rad + rad), BANKFORMAT, 0, 0)


def test_f3_nul_tecken_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9a: NUL-tecken i en beskrivning gav csv.Error."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M\x00X,1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "rad 2 i filen" in str(fel.value)
    assert "NUL-tecken" in str(fel.value)


def test_f3_nul_tecken_fore_rubrikraden_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9b."""
    fil = skriv(tmp_path, "X\x00Y\n" + RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n")
    with pytest.raises(BankfilFel, match="rad 1 i filen innehåller ett NUL-tecken"):
        las_bankfil(fil, BANKFORMAT, 0, 100)


@pytest.mark.parametrize("kodning, bom", [("utf-16-le", b"\xff\xfe"), ("utf-16-be", b"\xfe\xff")])
def test_f3_utf16_stoppas_med_bankfilfel(tmp_path, kodning, bom):
    """F3, fall 9c: en fil sparad som UTF-16 gav csv.Error."""
    fil = tmp_path / "bank.csv"
    fil.write_bytes(bom + (RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n").encode(kodning))
    with pytest.raises(BankfilFel, match="UTF-16"):
        las_bankfil(fil, BANKFORMAT, 0, 100)


def test_f3_for_langt_falt_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9d: en beskrivning på 200 000 tecken gav csv.Error."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1," + "M" * 200_000 + ",1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "rad 2 i filen" in str(fel.value)
    assert "längre än" in str(fel.value)


def test_f9_skrap_efter_citerat_falt_stoppas(tmp_path):
    """F9, fall 4i: fältet "REF"X lästes tyst som REFX."""
    fil = skriv(tmp_path, RUBRIK + '1,2025-01-02,2025-01-02,"REF"X,M,1.00,1.00\n')
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "rad 2 i filen" in str(fel.value)
    assert "citattecken i fel läge" in str(fel.value)


def test_f7_saknad_fil_ger_bankfilfel(tmp_path):
    """F7, fall 9m: gav FileNotFoundError."""
    with pytest.raises(BankfilFel, match="filen finns inte"):
        las_bankfil(tmp_path / "finns_inte.csv", BANKFORMAT, 0, 0)


def test_f7_mapp_ger_bankfilfel(tmp_path):
    """F7, fall 9n: gav IsADirectoryError."""
    with pytest.raises(BankfilFel, match="är en mapp"):
        las_bankfil(tmp_path, BANKFORMAT, 0, 0)


def test_f7_fil_som_inte_gar_att_lasa_ger_bankfilfel(tmp_path):
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n")
    fil.chmod(0)
    try:
        if os.access(fil, os.R_OK):
            pytest.skip("Filen går ändå att läsa (till exempel som administratör).")
        with pytest.raises(BankfilFel, match="går inte att läsa"):
            las_bankfil(fil, BANKFORMAT, 0, 100)
    finally:
        fil.chmod(0o600)


def test_f8_trasig_utf8_namner_teckenkodningen(tmp_path):
    """F8, fall 9e: en UTF-8-fil med en trasig byte. Rubrikraden känns inte igen, och
    meddelandet ska då nämna att teckenkodningen kan vara orsaken."""
    fil = tmp_path / "bank.csv"
    fil.write_bytes(RUBRIK.encode("utf-8") + b"1,2025-01-02,2025-01-02,REF-1,CAF\xe9,1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "ingen rubrikrad" in str(fel.value)
    assert "Teckenkodningen kan vara orsaken" in str(fel.value)


def test_f8_giltig_utf8_utan_rubrikrad_namner_inte_teckenkodningen(tmp_path):
    fil = skriv(tmp_path, "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "teckenkodning" not in str(fel.value).lower()


def filer_som_namner_tolka_rader(mapp):
    """Alla .py-filer under mapp, utom tests/ och las_bank.py, som nämner _tolka_rader."""
    return sorted(
        fil for fil in mapp.rglob("*.py")
        if mapp / "tests" not in fil.parents and fil != mapp / "las_bank.py"
        and "_tolka_rader" in fil.read_text(encoding="utf-8")
    )


def test_f11_ingen_annan_karnfil_anvander_tolka_rader():
    """F11: _tolka_rader hoppar över K1. Bara las_bank.py själv och testerna får använda den.
    All annan kod ska gå via las_bankfil, som alltid kör K1."""
    scripts = AGENT / "scripts"
    assert (scripts / "belopp.py").exists()  # skydd mot att testet inte hittar några filer alls
    fynd = filer_som_namner_tolka_rader(scripts)
    assert not fynd, "Använder _tolka_rader och hoppar då över K1: " + ", ".join(map(str, fynd))


def test_f11_kontrollen_hittar_en_fil_som_anvander_tolka_rader(tmp_path):
    """Skydd: kontrollen ovan ska verkligen slå larm när en annan fil använder _tolka_rader."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("from las_bank import _tolka_rader\n", encoding="utf-8")
    (tmp_path / "las_bank.py").write_text("def _tolka_rader(data, bankformat): ...\n", encoding="utf-8")
    (tmp_path / "rapport.py").write_text("from las_bank import _tolka_rader\n", encoding="utf-8")
    (tmp_path / "belopp.py").write_text("def tolka_belopp(text): ...\n", encoding="utf-8")
    assert filer_som_namner_tolka_rader(tmp_path) == [tmp_path / "rapport.py"]


# --- F5: bankformatet kommer från företagets konfiguration ---

ENGELSKT_FORMAT = {
    "anteckning": "Påhittat format för test: engelska kolumnnamn och tabb som avgränsare.",
    "kolumner": {
        "radnr": "Row",
        "bokforingsdag": "Booking date",
        "transaktionsdag": "Transaction date",
        "referens": "Reference",
        "beskrivning": "Description",
        "belopp": "Amount",
        "saldo": "Balance",
    },
    "avgransare": ["\t"],
}


def skriv_bankformat(tmp_path, innehall):
    fil = tmp_path / "bankformat.json"
    fil.write_text(innehall if isinstance(innehall, str) else json.dumps(innehall), encoding="utf-8")
    return fil


def test_f5_annat_bankformat_laser_samma_data(tmp_path):
    """Samma transaktioner med engelska kolumnnamn, tabb som avgränsare och kolumnerna i omvänd
    ordning läses lika bra, bara genom att bankformatet byts. Kärnan ändras inte."""
    with open(bankfil("2025-01"), encoding="utf-8", newline="") as fil:
        rader = list(csv.reader(fil))
    rubrik = rader[0]
    svenska = BANKFORMAT["kolumner"]
    engelska = {svenska[nyckel]: ENGELSKT_FORMAT["kolumner"][nyckel] for nyckel in svenska}
    assert sorted(rubrik) == sorted(engelska)  # januarifilen har precis bankformatets kolumner
    text = io.StringIO()
    csv.writer(text, delimiter="\t").writerows(
        [[engelska[namn] for namn in reversed(rubrik)]] + [list(reversed(rad)) for rad in rader[1:]]
    )
    kopia = tmp_path / "bank_engelsk.csv"
    kopia.write_bytes(text.getvalue().encode("utf-8"))
    assert kopia.read_text(encoding="utf-8").startswith("Balance\tAmount\t")

    engelskt = ladda_bankformat(skriv_bankformat(tmp_path, ENGELSKT_FORMAT))
    fran_original = las_bankfil(bankfil("2025-01"), BANKFORMAT, *saldon("2025-01")).rader
    fran_kopia = las_bankfil(kopia, engelskt, *saldon("2025-01")).rader
    assert utan_kalla_fil(fran_kopia) == utan_kalla_fil(fran_original)

    # Formatet styr verkligen: fel format för filen hittar ingen rubrikrad, åt båda hållen.
    with pytest.raises(BankfilFel, match="ingen rubrikrad med kolumnerna Row, Booking date"):
        las_bankfil(bankfil("2025-01"), engelskt, *saldon("2025-01"))
    with pytest.raises(BankfilFel, match="ingen rubrikrad med kolumnerna Radnummer"):
        las_bankfil(kopia, BANKFORMAT, *saldon("2025-01"))


def test_f5_testbutikens_bankformat_laddas():
    assert BANKFORMAT["kolumner"]["saldo"] == "Bokfört saldo"
    assert BANKFORMAT["avgransare"] == [",", ";"]
    assert "anteckning" not in BANKFORMAT  # fri text för människor, används inte i koden


def utan(nyckel, data):
    return {k: v for k, v in data.items() if k != nyckel}


def med_kolumner(**andrat):
    return {**ENGELSKT_FORMAT, "kolumner": {**ENGELSKT_FORMAT["kolumner"], **andrat}}


@pytest.mark.parametrize(
    "innehall, text",
    [
        (utan("kolumner", ENGELSKT_FORMAT), "saknar nyckeln 'kolumner'"),
        (utan("avgransare", ENGELSKT_FORMAT), "saknar nyckeln 'avgransare'"),
        ({**ENGELSKT_FORMAT, "kolumner": utan("saldo", ENGELSKT_FORMAT["kolumner"])}, "saknar nyckeln 'saldo'"),
        ({**ENGELSKT_FORMAT, "bank": "X"}, "okänd nyckel: 'bank'"),
        (med_kolumner(valuta="Currency"), "okänd nyckel: 'valuta'"),
        (med_kolumner(saldo="Amount"), "kolumnnamnet 'Amount' används för både 'belopp' och 'saldo'"),
        (med_kolumner(saldo=" Amount "), "kolumnnamnet 'Amount' används för både"),
        (med_kolumner(referens=""), "kolumnnamnet för 'referens' får inte vara tomt"),
        (med_kolumner(referens="   "), "kolumnnamnet för 'referens' får inte vara tomt"),
        (med_kolumner(referens=None), "kolumnnamnet för 'referens' får inte vara tomt"),
        (med_kolumner(referens='Ref"'), "får inte innehålla radbrytning eller citattecken"),
        ({**med_kolumner(referens="Ref|nr"), "avgransare": ["\t", "|"]}, "ett kolumnnamn innehåller en av avgränsarna"),
        ({**ENGELSKT_FORMAT, "kolumner": ["Row"]}, "'kolumner', ska vara ett objekt"),
        ({**ENGELSKT_FORMAT, "avgransare": []}, "minst en avgränsare"),
        ({**ENGELSKT_FORMAT, "avgransare": ","}, "ska vara en lista"),
        ({**ENGELSKT_FORMAT, "avgransare": [",;"]}, "avgränsaren ',;' är ogiltig"),
        ({**ENGELSKT_FORMAT, "avgransare": ['"']}, "är ogiltig"),
        ({**ENGELSKT_FORMAT, "avgransare": [",", ","]}, "samma avgränsare står flera gånger"),
        ({**ENGELSKT_FORMAT, "anteckning": 1}, "'anteckning' ska vara text"),
        ([], "ska vara ett objekt"),
        ("{", "inte giltig JSON"),
        ('{"kolumner": {}, "kolumner": {}}', "nyckeln 'kolumner' står flera gånger"),
    ],
    ids=[
        "saknar_kolumner", "saknar_avgransare", "saknar_kolumn", "okand_nyckel", "okand_kolumn",
        "dubbla_kolumnnamn", "dubbla_kolumnnamn_med_mellanslag", "tomt_kolumnnamn",
        "kolumnnamn_bara_mellanslag", "kolumnnamn_saknar_text", "citattecken_i_kolumnnamn",
        "avgransare_i_kolumnnamn", "kolumner_ar_lista", "inga_avgransare", "avgransare_ar_text",
        "avgransare_tva_tecken", "avgransare_citattecken", "dubbla_avgransare",
        "anteckning_ar_tal", "inte_objekt", "trasig_json", "dubbla_nycklar_i_json",
    ],
)
def test_f5_trasigt_bankformat_ger_bankfilfel(tmp_path, innehall, text):
    with pytest.raises(BankfilFel) as fel:
        ladda_bankformat(skriv_bankformat(tmp_path, innehall))
    assert text in str(fel.value)
    assert str(tmp_path / "bankformat.json") in str(fel.value)  # meddelandet säger vilken fil


def test_f5_saknat_bankformat_ger_bankfilfel(tmp_path):
    with pytest.raises(BankfilFel, match="Bankformatet saknas: filen finns inte"):
        ladda_bankformat(tmp_path / "bankformat.json")
    with pytest.raises(BankfilFel, match="är en mapp"):
        ladda_bankformat(tmp_path)


def test_f5_bankformat_som_inte_ar_utf8_ger_bankfilfel(tmp_path):
    fil = tmp_path / "bankformat.json"
    fil.write_bytes(json.dumps(ENGELSKT_FORMAT, ensure_ascii=False).replace("Row", "Radö").encode("cp1252"))
    with pytest.raises(BankfilFel, match="inte sparat som UTF-8"):
        ladda_bankformat(fil)


def test_f5_las_bankfil_kontrollerar_bankformatet_igen():
    """Ett bankformat som inte gått via ladda_bankformat kontrolleras ändå innan det används."""
    with pytest.raises(BankfilFel, match="saknar nyckeln 'saldo'"):
        las_bankfil(bankfil("2025-01"), {**BANKFORMAT, "kolumner": utan("saldo", BANKFORMAT["kolumner"])},
                    *saldon("2025-01"))


# --- Rättelser efter granskning 2 (GRANSKNING.md) ---

# Styrtecken som Pythons splitlines räknar som radslut, men som F1-skyddet inte kände till.
G1_STYRTECKEN = ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85"]


@pytest.mark.parametrize("tecken", G1_STYRTECKEN, ids=lambda t: "U+" + format(ord(t), "04X"))
def test_g1_citattecken_som_slar_ihop_rader_med_styrtecken_stoppas(tmp_path, tecken):
    """G1: granskarens fall 4g, men med ett styrtecken mellan raderna i stället för \\n.
    Före rättelsen godkändes filen med en enda rad i stället för tre."""
    fil = skriv(tmp_path, RUBRIK
                + '1,2025-01-03,2025-01-03,REF-1,"A,200.00,200.00' + tecken
                + "2,2025-01-04,2025-01-04,REF-2,B,-200.00,0.00" + tecken
                + '3,2025-01-28,2025-01-28,REF-3,C",75.00,75.00\n')
    resultat = None
    with pytest.raises(BankfilFel) as fel:
        resultat = las_bankfil(fil, BANKFORMAT, 0, 7500)  # rätt ingående och utgående saldo
    assert resultat is None
    assert "rad 2 i filen" in str(fel.value)
    assert "U+" + format(ord(tecken), "04X") in str(fel.value)
    assert "styrtecken" in str(fel.value)


def test_g1_styrtecken_i_vanligt_falt_stoppas(tmp_path):
    """G1: ett ociterat fält med \\x0c inuti. Före rättelsen stoppades filen med det missvisande
    meddelandet "har 5 fält"."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1,MOT\x0cPART,1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, BANKFORMAT, 0, 100)
    assert "rad 2 i filen innehåller tecknet U+000C" in str(fel.value)


def test_g1_tabb_och_vanliga_radslut_ar_tillatna(tmp_path):
    """Skydd: tabb, \\n och \\r\\n är fortfarande tillåtna."""
    fil = skriv(tmp_path, RUBRIK.replace("\n", "\r\n") + "1,2025-01-02,2025-01-02,REF-1,M\tX,1.00,1.00\r\n")
    assert las_bankfil(fil, BANKFORMAT, 0, 100).rader[0]["beskrivning"] == "M\tX"


@pytest.mark.parametrize(
    "avgransare",
    ["\x0c", "\x1e", "\x85", "\x00", ".", "-", "0", "x", "\U0001F600"],
    ids=["U+000C", "U+001E", "U+0085", "NUL", "punkt", "minus", "siffra", "bokstav", "emoji"],
)
def test_g2_avgransare_utanfor_fasta_listan_forkastas(tmp_path, avgransare):
    """G2: bara komma, semikolon, tabb och lodstreck får vara avgränsare."""
    with pytest.raises(BankfilFel) as fel:
        ladda_bankformat(skriv_bankformat(tmp_path, {**ENGELSKT_FORMAT, "avgransare": [avgransare]}))
    assert "avgränsaren " + repr(avgransare) + " är ogiltig" in str(fel.value)
    assert "Tillåtna avgränsare är komma, semikolon, tabb och lodstreck" in str(fel.value)


def test_g2_avgransarna_i_fasta_listan_godtas(tmp_path):
    for avgransare in [",", ";", "\t", "|"]:
        format_ = ladda_bankformat(skriv_bankformat(tmp_path, {**ENGELSKT_FORMAT, "avgransare": [avgransare]}))
        assert format_["avgransare"] == [avgransare]


@pytest.mark.parametrize(
    "tecken",
    ["\x0c", "\x85", "\x00", "\u200b", "\t"],
    ids=["U+000C", "U+0085", "NUL", "U+200B", "tabb"],
)
def test_g2_styrtecken_och_osynliga_tecken_i_kolumnnamn_forkastas(tmp_path, tecken):
    """G2: kolumnnamn med styrtecken (Cc) eller osynliga tecken (Cf) kan aldrig hittas i en
    bankfil. U+200B är ett osynligt mellanslag. Tabb är också ett styrtecken. Avgränsaren är komma,
    så att tabben inte stoppas av kontrollen av avgränsare i kolumnnamn i stället."""
    format_ = {**med_kolumner(referens="Ref" + tecken + "nr"), "avgransare": [","]}
    with pytest.raises(BankfilFel) as fel:
        ladda_bankformat(skriv_bankformat(tmp_path, format_))
    assert "kolumnnamnet för 'referens' innehåller tecknet U+" + format(ord(tecken), "04X") in str(fel.value)
    assert "styrtecken eller ett osynligt tecken" in str(fel.value)


@pytest.mark.parametrize(
    "innehall",
    ["[" * 100_000 + "]" * 100_000, '{"a":' * 100_000 + "1" + "}" * 100_000],
    ids=["hakparenteser", "klammerparenteser"],
)
def test_g4_djupt_nastlat_bankformat_ger_bankfilfel(tmp_path, innehall):
    """G4: 100 000 nivåer inuti varandra gav RecursionError i stället för BankfilFel."""
    with pytest.raises(BankfilFel) as fel:
        ladda_bankformat(skriv_bankformat(tmp_path, innehall))
    assert "för många hakparenteser eller klammerparenteser inuti varandra" in str(fel.value)
    assert str(tmp_path / "bankformat.json") in str(fel.value)


def test_g8_kolumn_flera_ganger_pa_rubrikraden_stoppas(tmp_path):
    """G8 punkt 1: utan kontrollen skulle den första av två kolumner med samma namn användas
    utan varning. Raden nedan klarar K1 om den första kolumnen 'Belopp' används."""
    fil = skriv(tmp_path, RUBRIK.replace("\n", ",Belopp\n") + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00,99.00\n")
    resultat = None
    with pytest.raises(BankfilFel) as fel:
        resultat = las_bankfil(fil, BANKFORMAT, 0, 100)
    assert resultat is None
    assert "rubrikraden (rad 1 i filen) har kolumnen 'Belopp' flera gånger" in str(fel.value)


def test_g8_mellanslag_som_avgransare_forkastas(tmp_path):
    """G8 punkt 2. Kolumnnamnen saknar mellanslag, så att det är avgränsarkontrollen som prövas
    och inte kontrollen av avgränsare i kolumnnamn."""
    format_ = {
        "kolumner": {
            "radnr": "Row", "bokforingsdag": "Booked", "transaktionsdag": "Date", "referens": "Reference",
            "beskrivning": "Description", "belopp": "Amount", "saldo": "Balance",
        },
        "avgransare": [" "],
    }
    with pytest.raises(BankfilFel, match="avgränsaren ' ' är ogiltig"):
        ladda_bankformat(skriv_bankformat(tmp_path, format_))


@pytest.mark.parametrize(
    "belopp, saldo, ingaende, utgaende",
    [
        ("0.01", "0.01", False, 1),  # False är lika med 0 i Python
        ("0.01", "0.02", True, 2),  # True är lika med 1
        ("0.01", "0.01", 0, True),
        ("-0.01", "0.00", 1, False),
    ],
    ids=["ingaende_false", "ingaende_true", "utgaende_true", "utgaende_false"],
)
def test_g8_true_och_false_som_saldo_stoppas(tmp_path, belopp, saldo, ingaende, utgaende):
    """G8 punkt 3: kedjan stämmer om True räknas som 1 och False som 0, men ett sanningsvärde är
    inget saldo. Felet är TypeError (se G3, som inte är ändrat)."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M," + belopp + "," + saldo + "\n")
    with pytest.raises(TypeError, match="heltal i öre, inte bool"):
        las_bankfil(fil, BANKFORMAT, ingaende, utgaende)


# --- Bankperiod: resultatet går inte att ändra (Hugos beslut 2026-10-25) ---

def liten_period(mapp, namn, ingaende, *belopp):
    """Skriver en liten bankfil med beloppen (i öre) och läser den med las_bankfil."""
    saldo, rader = ingaende, []
    for nummer, ore in enumerate(belopp, start=1):
        saldo += ore
        rader.append(str(nummer) + ",2025-01-02,2025-01-02,REF-" + str(nummer) + ",M," + formatera(ore) + ","
                     + formatera(saldo) + "\n")
    fil = mapp / namn
    fil.write_text(RUBRIK + "".join(rader), encoding="utf-8")
    return las_bankfil(fil, BANKFORMAT, ingaende, saldo)


def formatera(ore):
    return ("-" if ore < 0 else "") + str(abs(ore) // 100) + "." + str(abs(ore) % 100).zfill(2)


def test_bankperiod_bar_raderna_och_saldona():
    ingaende, utgaende = saldon("2025-01")
    period = las_bankfil(bankfil("2025-01"), BANKFORMAT, ingaende, utgaende)
    assert type(period) is Bankperiod
    assert period.rader == _tolka_rader(bankfil("2025-01").read_bytes(), BANKFORMAT)
    assert (period.ingaende_saldo_ore, period.utgaende_saldo_ore) == (ingaende, utgaende)
    assert all(type(rad) is dict for rad in period.rader)
    assert (len(period.rader), ingaende, utgaende) == (118, 8500000, 19276493)  # enligt facit
    assert repr(period) == "Bankperiod(118 rader, ingående saldo 85000,00 kr, utgående saldo 192764,93 kr)"


def test_bankperiod_kan_inte_andras_utifran(tmp_path):
    period = liten_period(tmp_path, "bank.csv", 0, 100, -40)
    fore = period.rader
    # Raderna som läses ut är kopior. Att ta bort eller ändra en rad i dem når inte perioden.
    utlast = period.rader
    del utlast[0]
    utlast[0]["belopp_ore"] = 99999900
    utlast.append(dict(utlast[0]))
    period.rader.clear()
    assert period.rader == fore and len(fore) == 2
    assert period.rader is not period.rader and period.rader[0] is not period.rader[0]
    # Perioden själv går inte att ändra.
    for namn in ("_rader", "_ingaende_saldo_ore", "_utgaende_saldo_ore", "rader", "ingaende_saldo_ore", "ny"):
        with pytest.raises(AttributeError):
            setattr(period, namn, [])
        with pytest.raises(AttributeError):
            delattr(period, namn)
    with pytest.raises(TypeError):
        period._rader[0]["belopp_ore"] = 1
    with pytest.raises(AttributeError):
        period._rader.append({})
    assert period.rader == fore


def test_bankperiod_kan_bara_skapas_av_las_bankfil(tmp_path):
    rader = liten_period(tmp_path, "bank.csv", 0, 100).rader
    for nyckel in (None, object(), "nyckel", Bankperiod):
        with pytest.raises(BankfilFel, match="En Bankperiod kan bara skapas av las_bankfil eller sla_ihop_bankperioder"):
            Bankperiod(nyckel, rader, 0, 100)
    with pytest.raises(TypeError):
        Bankperiod(rader, 0, 100)
    # Skydd: med nyckeln går det (bara las_bank.py själv och testerna får använda den, test_inga_genvagar.py).
    assert Bankperiod(las_bank._PERIODNYCKEL, rader, 0, 100).rader == rader


def test_sla_ihop_januari_och_februari():
    bank = facit()["bank"]
    januari = las_bankfil(bankfil("2025-01"), BANKFORMAT, *saldon("2025-01"))
    februari = las_bankfil(bankfil("2025-02"), BANKFORMAT, januari.utgaende_saldo_ore,
                           bank["2025-02"]["utgaende_saldo_ore"])
    ihop = sla_ihop_bankperioder([januari, februari])
    assert type(ihop) is Bankperiod
    assert ihop.rader == januari.rader + februari.rader
    assert len(ihop.rader) == bank["2025-01"]["antal_rader"] + bank["2025-02"]["antal_rader"]
    assert (ihop.ingaende_saldo_ore, ihop.utgaende_saldo_ore) == (
        bank["2025-01"]["ingaende_saldo_ore"], bank["2025-02"]["utgaende_saldo_ore"])
    assert sla_ihop_bankperioder((januari,)).rader == januari.rader  # en tupel med en period går också


def test_sla_ihop_stoppar_perioder_som_inte_hanger_ihop(tmp_path):
    forsta = liten_period(tmp_path, "a.csv", 0, 100)          # 0,00 kr till 1,00 kr
    andra = liten_period(tmp_path, "b.csv", 100, 50)          # 1,00 kr till 1,50 kr
    tredje = liten_period(tmp_path, "c.csv", 150, -25)        # 1,50 kr till 1,25 kr
    assert sla_ihop_bankperioder([forsta, andra, tredje]).utgaende_saldo_ore == 125  # skydd: de hänger ihop
    with pytest.raises(BankfilFel) as fel:
        sla_ihop_bankperioder([forsta, tredje])                 # andra saknas
    assert str(fel.value) == (
        "Bankperioderna hänger inte ihop: Bankperiod nummer 2 har ingående saldo 1,50 kr, men Bankperiod nummer 1"
        " har utgående saldo 1,00 kr, skillnad 0,50 kr. Det kan saknas rader mellan dem, eller så är de i fel"
        " ordning.")
    with pytest.raises(BankfilFel, match="^Bankperioderna hänger inte ihop: Bankperiod nummer 3 har ingående saldo"
                                         " 1,00 kr, men Bankperiod nummer 2 har utgående saldo 1,25 kr"):
        sla_ihop_bankperioder([andra, tredje, andra])          # andra två gånger, och inte i ordning
    with pytest.raises(BankfilFel, match="^Bankperioderna hänger inte ihop: Bankperiod nummer 2"):
        sla_ihop_bankperioder([andra, forsta])                  # fel ordning


def test_sla_ihop_stoppar_samma_bankrad_tva_ganger(tmp_path):
    # En bankfil där pengarna in och ut tar ut varandra hänger ihop med sig själv. Samma fil två
    # gånger stoppas ändå, eftersom raderna finns två gånger.
    noll = liten_period(tmp_path, "noll.csv", 0, 100, -100)
    with pytest.raises(BankfilFel) as fel:
        sla_ihop_bankperioder([noll, noll])
    rad = noll.rader[0]
    assert str(fel.value) == (
        "Bankraden med id " + repr(rad["id"]) + " (radnummer 1) finns i flera Bankperioder. Samma bankfil kan vara"
        " inläst två gånger. Varje bankrad ska finnas en gång.")
    # Samma rad i två olika filer, till exempel en export som överlappar en annan.
    kopia = liten_period(tmp_path, "kopia.csv", 0, 100, -100)
    assert kopia.rader[0]["kalla_fil"] == noll.rader[0]["kalla_fil"]  # filerna har samma innehåll
    with pytest.raises(BankfilFel, match="finns i flera Bankperioder"):
        sla_ihop_bankperioder([noll, kopia])
    # Skydd: två olika filer som båda börjar och slutar på 0 kr går att sätta ihop.
    annan = liten_period(tmp_path, "annan.csv", 0, 200, -200)
    assert len(sla_ihop_bankperioder([noll, annan]).rader) == 4


def test_sla_ihop_tar_bara_emot_bankperioder(tmp_path):
    period = liten_period(tmp_path, "bank.csv", 0, 100)

    class Underklass(Bankperiod):
        __slots__ = ()

    for varde, text in [(None, "NoneType"), (period, "Bankperiod"), (iter([period]), "list_iterator"),
                        ({1: period}, "dict"), (period.rader, None)]:
        if text is None:  # en lista med rader i stället för perioder
            with pytest.raises(BankfilFel, match="^Bankperiod nummer 1 ska vara en Bankperiod från las_bankfil,"
                                                 " inte dict"):
                sla_ihop_bankperioder(varde)
            continue
        with pytest.raises(BankfilFel, match="^Bankperioderna ska vara en lista med Bankperioder från las_bankfil,"
                                             " inte " + text + r"\."):
            sla_ihop_bankperioder(varde)
    for tomt in ([], ()):
        with pytest.raises(BankfilFel, match="^Det finns inga Bankperioder att sätta ihop"):
            sla_ihop_bankperioder(tomt)
    for annat, text in [(period.rader, "list"), (None, "NoneType"), (Underklass.__new__(Underklass), "Underklass")]:
        with pytest.raises(BankfilFel, match="^Bankperiod nummer 2 ska vara en Bankperiod från las_bankfil, inte "
                                             + text + r"\."):
            sla_ihop_bankperioder([period, annat])


def test_sla_ihop_ger_en_ny_period_som_inte_delar_nagot_med_de_gamla(tmp_path):
    forsta = liten_period(tmp_path, "a.csv", 0, 100)
    andra = liten_period(tmp_path, "b.csv", 100, 50)
    ihop = sla_ihop_bankperioder([forsta, andra])
    ihop.rader[0]["belopp_ore"] = 1
    assert forsta.rader[0]["belopp_ore"] == 100 and ihop.rader[0]["belopp_ore"] == 100
    with pytest.raises(AttributeError):
        ihop.ingaende_saldo_ore = 0
