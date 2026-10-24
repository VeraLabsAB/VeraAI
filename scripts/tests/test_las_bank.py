"""Tester för inläsning av bankfiler och kontroll K1 (saldokedjan).

Testdatan är SYNTETISK (Syntet Testbutik AB, 2025-Q1). Rätt svar står i facit.json.
"""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"

sys.path.insert(0, str(AGENT / "scripts"))

from las_bank import BankfilFel, K1Fel, _tolka_rader, kontrollera_k1, las_bankfil

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
    januari = las_bankfil(bankfil("2025-01"), *saldon("2025-01"))
    assert januari[-1]["saldo_efter_ore"] == bank["2025-01"]["utgaende_saldo_ore"]

    # Februaris ingående saldo är januaris utgående, både i facit och i filen.
    assert bank["2025-02"]["ingaende_saldo_ore"] == bank["2025-01"]["utgaende_saldo_ore"]
    februari = las_bankfil(bankfil("2025-02"), januari[-1]["saldo_efter_ore"],
                           bank["2025-02"]["utgaende_saldo_ore"])
    assert februari[-1]["saldo_efter_ore"] == bank["2025-02"]["utgaende_saldo_ore"]


def test_raderna_har_ratt_falt():
    rader = las_bankfil(bankfil("2025-01"), *saldon("2025-01"))
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
        las_bankfil(bankfil("2025-01"), ingaende + 1, utgaende)
    assert fel.value.radnr == 1
    assert fel.value.skillnad_ore == -1


# --- (b) Mars stoppas av K1 på radnummer 74 ---

def test_mars_stoppas_av_k1_pa_raden_som_facit_anger():
    planterat = [f for f in facit()["planterade_fel"] if f["typ"] == "brott_i_saldokedjan"][0]
    resultat = None
    with pytest.raises(K1Fel) as fel:
        resultat = las_bankfil(bankfil("2025-03"), *saldon("2025-03"))
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
    rader = _tolka_rader(bankfil(manad).read_bytes())
    assert len(rader) == fakta["antal_rader"]
    assert sum(rad["belopp_ore"] for rad in rader) == fakta["utgaende_saldo_ore"] - fakta["ingaende_saldo_ore"]


# --- (d) Kodning, avgränsare och rader före rubriken ---

def test_windows_1252_ger_samma_resultat(tmp_path):
    original = bankfil("2025-01")
    kopia = tmp_path / "bank_cp1252.csv"
    kopia.write_bytes(original.read_text(encoding="utf-8").encode("cp1252"))
    assert kopia.read_bytes() != original.read_bytes()

    fran_original = las_bankfil(original, *saldon("2025-01"))
    fran_kopia = las_bankfil(kopia, *saldon("2025-01"))
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

    fran_original = las_bankfil(original, *saldon("2025-01"))
    fran_kopia = las_bankfil(kopia, *saldon("2025-01"))
    assert utan_kalla_fil(fran_kopia) == utan_kalla_fil(fran_original)
    assert fran_kopia[0]["kalla_fil"] != fran_original[0]["kalla_fil"]


# --- (e) Beloppen är heltal ---

def test_beloppen_ar_heltal_aldrig_float():
    rader = las_bankfil(bankfil("2025-01"), *saldon("2025-01"))
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
        las_bankfil(fil, 0, 11230)
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
        las_bankfil(skriv(tmp_path, RUBRIK + rad), 0, 10000)


def test_fil_utan_rubrikrad_stoppas(tmp_path):
    with pytest.raises(BankfilFel, match="ingen rubrikrad"):
        las_bankfil(skriv(tmp_path, "1,2025-01-02,2025-01-02,REF-1,MOTPART-A,100.00,100.00\n"), 0, 10000)


def test_fil_utan_transaktioner_stoppas(tmp_path):
    with pytest.raises(BankfilFel, match="inga transaktionsrader"):
        las_bankfil(skriv(tmp_path, RUBRIK), 0, 0)


def test_okand_teckenkodning_stoppas(tmp_path):
    fil = tmp_path / "bank.csv"
    fil.write_bytes(RUBRIK.encode("utf-8") + b"1,2025-01-02,2025-01-02,REF-\x81,M,1.00,1.00\n")
    with pytest.raises(BankfilFel, match="teckenkodningen"):
        las_bankfil(fil, 0, 100)


# --- Rättelser efter granskningen (GRANSKNING.md) ---

def test_f2_avklippt_fil_stoppas(tmp_path):
    """F2 och F10: en fil där sista raden saknas stoppas av jämförelsen med utgående saldo."""
    rader = bankfil("2025-01").read_bytes().splitlines(keepends=True)
    kopia = tmp_path / "bank_avklippt.csv"
    kopia.write_bytes(b"".join(rader[:-1]))

    ingaende, utgaende = saldon("2025-01")
    resultat = None
    with pytest.raises(K1Fel) as fel:
        resultat = las_bankfil(kopia, ingaende, utgaende)
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
        resultat = las_bankfil(fil, 0, 7500)  # rätt ingående och utgående saldo
    assert resultat is None
    assert "rad 2 i filen" in str(fel.value)
    assert "radbrytning" in str(fel.value)


@pytest.mark.parametrize("radbrytning", ["\n", "\r", "\r\n", "\u2028", "\u2029"])
def test_f1_radbrytning_inuti_falt_stoppas(tmp_path, radbrytning):
    fil = skriv(tmp_path, RUBRIK
                + '1,2025-01-02,2025-01-02,REF-1,"RAD ETT' + radbrytning + 'RAD TVA",100.00,100.00\n')
    with pytest.raises(BankfilFel, match="radbrytning"):
        las_bankfil(fil, 0, 10000)


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
        las_bankfil(skriv(tmp_path, RUBRIK + rader), 0, 300)
    assert "rad " + str(felrad) + " i filen" in str(fel.value)
    assert text in str(fel.value)


def test_f6_identiska_rader_stoppas(tmp_path):
    """F6: två helt identiska rader på 0 kr skulle få samma id. Nu stoppas filen."""
    rad = "1,2025-01-02,2025-01-02,REF-1,M,0.00,0.00\n"
    with pytest.raises(BankfilFel, match="radnummer 1, men nästa radnummer ska vara 2"):
        las_bankfil(skriv(tmp_path, RUBRIK + rad + rad), 0, 0)


def test_f3_nul_tecken_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9a: NUL-tecken i en beskrivning gav csv.Error."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M\x00X,1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, 0, 100)
    assert "rad 2 i filen" in str(fel.value)
    assert "NUL-tecken" in str(fel.value)


def test_f3_nul_tecken_fore_rubrikraden_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9b."""
    fil = skriv(tmp_path, "X\x00Y\n" + RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n")
    with pytest.raises(BankfilFel, match="rad 1 i filen innehåller ett NUL-tecken"):
        las_bankfil(fil, 0, 100)


@pytest.mark.parametrize("kodning, bom", [("utf-16-le", b"\xff\xfe"), ("utf-16-be", b"\xfe\xff")])
def test_f3_utf16_stoppas_med_bankfilfel(tmp_path, kodning, bom):
    """F3, fall 9c: en fil sparad som UTF-16 gav csv.Error."""
    fil = tmp_path / "bank.csv"
    fil.write_bytes(bom + (RUBRIK + "1,2025-01-02,2025-01-02,REF-1,M,1.00,1.00\n").encode(kodning))
    with pytest.raises(BankfilFel, match="UTF-16"):
        las_bankfil(fil, 0, 100)


def test_f3_for_langt_falt_stoppas_med_bankfilfel(tmp_path):
    """F3, fall 9d: en beskrivning på 200 000 tecken gav csv.Error."""
    fil = skriv(tmp_path, RUBRIK + "1,2025-01-02,2025-01-02,REF-1," + "M" * 200_000 + ",1.00,1.00\n")
    with pytest.raises(BankfilFel) as fel:
        las_bankfil(fil, 0, 100)
    assert "rad 2 i filen" in str(fel.value)
    assert "längre än" in str(fel.value)
