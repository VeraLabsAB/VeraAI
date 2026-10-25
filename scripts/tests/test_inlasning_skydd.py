"""Tester som prövar de gemensamma skydden i inlasning_skydd.py direkt.

Varje skydd prövas med både bankfilens och kassafilens Filsort (BANKFIL och KASSAFIL). Felet ska
vara filsortens egen felklass, och meddelandet ska börja med filsortens egna ord. Att meddelandena
är exakt desamma som innan skydden flyttades hit bevisas av test_las_bank.py och test_las_kassa.py,
som inte ändrades vid flytten.
"""

import csv
import json
import os
import sys
import types
import unicodedata
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AGENT / "scripts"))

import inlasning_skydd as skydd  # noqa: E402
from las_bank import BANKFIL, BankfilFel  # noqa: E402
from las_kassa import KASSAFIL, KassafilFel  # noqa: E402

FILSORTER = pytest.mark.parametrize("filsort", [BANKFIL, KASSAFIL], ids=["bank", "kassa"])
KOLUMNER = {"datum": "Datum", "belopp": "Belopp"}


def stoppas(filsort, funktion, *args):
    """Kör funktionen, kräver filsortens felklass och returnerar meddelandet."""
    with pytest.raises(filsort.fel) as fel:
        funktion(*args)
    assert type(fel.value) is filsort.fel
    return str(fel.value)


def test_filsorterna_har_egna_felklasser_och_ord():
    assert BANKFIL.fel is BankfilFel and KASSAFIL.fel is KassafilFel
    assert (BANKFIL.filen, KASSAFIL.filen) == ("Bankfilen", "Kassafilen")
    assert (BANKFIL.formatet, KASSAFIL.formatet) == ("Bankformatet", "Kassaformatet")
    for falt in skydd.Filsort._fields:
        assert getattr(BANKFIL, falt) != getattr(KASSAFIL, falt), falt


# --- JSON-formatet ---

@FILSORTER
def test_ladda_json_godtar_giltig_json_med_och_utan_bom(tmp_path, filsort):
    fil = tmp_path / "format.json"
    for data in (b'{"a": [1, {"b": "\xc3\xb6"}]}', b'\xef\xbb\xbf{"a": [1, {"b": "\xc3\xb6"}]}'):
        fil.write_bytes(data)
        assert skydd.ladda_json(fil, filsort) == ({"a": [1, {"b": "ö"}]}, filsort.formatet + " i " + str(fil))


@FILSORTER
def test_ladda_json_saknad_fil_och_mapp(tmp_path, filsort):
    assert stoppas(filsort, skydd.ladda_json, tmp_path / "x.json", filsort) == (
        filsort.formatet + " saknas: filen finns inte: " + str(tmp_path / "x.json") + ".")
    assert stoppas(filsort, skydd.ladda_json, tmp_path, filsort) == (
        filsort.formatet + " saknas: " + str(tmp_path) + " är en mapp, inte en fil.")


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="behöver filrättigheter som vanlig användare")
@FILSORTER
def test_ladda_json_olasbar_fil(tmp_path, filsort):
    fil = tmp_path / "format.json"
    fil.write_text("{}", encoding="utf-8")
    fil.chmod(0)
    try:
        meddelande = stoppas(filsort, skydd.ladda_json, fil, filsort)
    finally:
        fil.chmod(0o600)
    assert meddelande.startswith(filsort.formatet + " går inte att läsa: " + str(fil) + " (")


@pytest.mark.parametrize("data, slut", [
    (b'{"a": "\xf6"}', " är inte sparat som UTF-8."),
    (b'{"a": 1,}', " är inte giltig JSON (rad 1, tecken 9)."),
    (b'{"a": 1, "a": 2}', ": nyckeln 'a' står flera gånger."),
    (b'{"a": {"b": 1, "b": 2}}', ": nyckeln 'b' står flera gånger."),
], ids=["inte_utf8", "trasig_json", "dubbel_nyckel", "dubbel_nyckel_inuti"])
@FILSORTER
def test_ladda_json_trasig_fil(tmp_path, filsort, data, slut):
    fil = tmp_path / "format.json"
    fil.write_bytes(data)
    assert stoppas(filsort, skydd.ladda_json, fil, filsort) == filsort.formatet + " i " + str(fil) + slut


@FILSORTER
def test_ladda_json_for_djup_nastling(tmp_path, filsort):
    fil = tmp_path / "format.json"
    fil.write_bytes(b"[" * 100000)
    meddelande = stoppas(filsort, skydd.ladda_json, fil, filsort)
    assert "för många hakparenteser eller klammerparenteser inuti varandra. " + filsort.nivaer in meddelande


@FILSORTER
def test_kontrollera_nycklar(filsort):
    skydd.kontrollera_nycklar({"a": 1, "c": 2}, ("a",), ("c",), "X", filsort)
    skydd.kontrollera_nycklar({"a": 1}, ("a",), ("c",), "X", filsort)
    assert stoppas(filsort, skydd.kontrollera_nycklar, [1], ("a",), (), "X", filsort) == (
        "X ska vara ett objekt med nycklar, inte list.")
    assert stoppas(filsort, skydd.kontrollera_nycklar, {"c": 1}, ("a", "b"), ("c",), "X", filsort) == (
        "X saknar nyckeln 'a', 'b'.")
    assert stoppas(filsort, skydd.kontrollera_nycklar, {"a": 1, "z": 2, "y": 3}, ("a",), ("c",), "X", filsort) == (
        "X har en okänd nyckel: 'y', 'z'. Tillåtna nycklar är 'a', 'c'.")


@FILSORTER
def test_kontrollera_anteckning(filsort):
    skydd.kontrollera_anteckning({}, "X", filsort)
    skydd.kontrollera_anteckning({"anteckning": "fri text"}, "X", filsort)
    assert stoppas(filsort, skydd.kontrollera_anteckning, {"anteckning": 5}, "X", filsort) == (
        "X: 'anteckning' ska vara text.")


@FILSORTER
def test_kontrollera_namn_godtar_och_tar_bort_mellanslag(filsort):
    assert skydd.kontrollera_namn("  Bokföringsdag  ", "namnet", "X", filsort) == "Bokföringsdag"


@pytest.mark.parametrize("namn, slut", [
    ("", " får inte vara tomt."),
    ("  ", " får inte vara tomt."),
    (5, " får inte vara tomt."),
    (None, " får inte vara tomt."),
    ("a\nb", " får inte innehålla radbrytning eller citattecken."),
    ("a\rb", " får inte innehålla radbrytning eller citattecken."),
    ("a\u2028b", " får inte innehålla radbrytning eller citattecken."),
    ("a\u2029b", " får inte innehålla radbrytning eller citattecken."),
    ('a"b', " får inte innehålla radbrytning eller citattecken."),
    ("a\u200bb", " innehåller tecknet U+200B, som är ett styrtecken eller ett osynligt tecken."),
    ("a\x0cb", " innehåller tecknet U+000C, som är ett styrtecken eller ett osynligt tecken."),
    ("a\tb", " innehåller tecknet U+0009, som är ett styrtecken eller ett osynligt tecken."),
    ("\ufeffa", " innehåller tecknet U+FEFF, som är ett styrtecken eller ett osynligt tecken."),
], ids=["tomt", "blanksteg", "tal", "none", "radbrytning", "vagnretur", "u2028", "u2029", "citattecken",
        "osynligt_mellanslag", "sidbrytning", "tabb", "bom"])
@FILSORTER
def test_kontrollera_namn_stoppar_trasiga_namn(filsort, namn, slut):
    assert stoppas(filsort, skydd.kontrollera_namn, namn, "namnet", "X", filsort).startswith("X: namnet" + slut)


@FILSORTER
def test_kontrollera_namn_sager_vad_namnet_kallas(filsort):
    assert stoppas(filsort, skydd.kontrollera_namn, "a\u200b", "namnet", "X", filsort).endswith(
        "Sådana tecken får inte finnas i ett namn.")
    assert stoppas(filsort, skydd.kontrollera_namn, "a\u200b", "namnet", "X", filsort, "ett kolumnnamn").endswith(
        "Sådana tecken får inte finnas i ett kolumnnamn.")


@FILSORTER
def test_inga_dubbla_kolumnnamn(filsort):
    skydd.inga_dubbla_kolumnnamn({"a": "A", "b": "B"}, "X", filsort)
    assert stoppas(filsort, skydd.inga_dubbla_kolumnnamn, {"a": "A", "b": "B", "c": "A"}, "X", filsort) == (
        "X: kolumnnamnet 'A' används för både 'a' och 'c'. Varje kolumn måste ha ett eget namn.")


@FILSORTER
def test_kontrollera_avgransare_godtar_tillatna(filsort):
    lista = [",", ";", "\t", "|"]
    resultat = skydd.kontrollera_avgransare(lista, KOLUMNER, "X", filsort)
    assert resultat == lista and resultat is not lista  # en ny lista, inte formatets egen
    assert skydd.TILLATNA_AVGRANSARE == (",", ";", "\t", "|")


@pytest.mark.parametrize("avgransare, slut", [
    ([], ": 'avgransare' ska vara en lista med minst en avgränsare."),
    (",", ": 'avgransare' ska vara en lista med minst en avgränsare."),
    ((",",), ": 'avgransare' ska vara en lista med minst en avgränsare."),
    (["."], ": avgränsaren '.' är ogiltig."),
    ([" "], ": avgränsaren ' ' är ogiltig."),
    (["\x0c"], ": avgränsaren '\\x0c' är ogiltig."),
    ([",;"], ": avgränsaren ',;' är ogiltig."),
    ([5], ": avgränsaren 5 är ogiltig."),
    ([",", ","], ": samma avgränsare står flera gånger i 'avgransare'."),
], ids=["tom", "text", "tuple", "punkt", "mellanslag", "sidbrytning", "tva_tecken", "tal", "dubbel"])
@FILSORTER
def test_kontrollera_avgransare_stoppar(filsort, avgransare, slut):
    assert stoppas(filsort, skydd.kontrollera_avgransare, avgransare, KOLUMNER, "X", filsort).startswith("X" + slut)


@FILSORTER
def test_kontrollera_avgransare_kolumnnamn_med_avgransare(filsort):
    kolumner = {"datum": "Datum", "belopp": "Belopp; kr"}
    skydd.kontrollera_avgransare([","], kolumner, "X", filsort)
    assert stoppas(filsort, skydd.kontrollera_avgransare, [",", ";"], kolumner, "X", filsort) == (
        "X: ett kolumnnamn innehåller en av avgränsarna.")


# --- Filen: teckenkodning och styrtecken ---

@FILSORTER
def test_las_fil(tmp_path, filsort):
    fil = tmp_path / "fil.csv"
    fil.write_bytes(b"a,b\r\n")
    assert skydd.las_fil(fil, filsort) == b"a,b\r\n"
    assert stoppas(filsort, skydd.las_fil, tmp_path / "x.csv", filsort) == (
        filsort.filen + " stoppas: filen finns inte: " + str(tmp_path / "x.csv") + ".")
    assert stoppas(filsort, skydd.las_fil, tmp_path, filsort) == (
        filsort.filen + " stoppas: " + str(tmp_path) + " är en mapp, inte en fil.")


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="behöver filrättigheter som vanlig användare")
@FILSORTER
def test_las_fil_olasbar(tmp_path, filsort):
    fil = tmp_path / "fil.csv"
    fil.write_bytes(b"a")
    fil.chmod(0)
    try:
        meddelande = stoppas(filsort, skydd.las_fil, fil, filsort)
    finally:
        fil.chmod(0o600)
    assert meddelande.startswith(filsort.filen + " stoppas: filen " + str(fil) + " går inte att läsa (")


@FILSORTER
def test_avkoda(filsort):
    assert skydd.avkoda("Bokföringsdag".encode("utf-8"), filsort) == ("Bokföringsdag", True)
    assert skydd.avkoda("Bokföringsdag".encode("utf-8-sig"), filsort) == ("Bokföringsdag", True)
    assert skydd.avkoda("Bokföringsdag".encode("cp1252"), filsort) == ("Bokföringsdag", False)
    assert skydd.avkoda(b"", filsort) == ("", True)


@pytest.mark.parametrize("kodning", ["utf-16", "utf-16-le", "utf-16-be"])
@FILSORTER
def test_avkoda_stoppar_utf16(filsort, kodning):
    data = "\ufeffDatum,Belopp".encode(kodning) if kodning != "utf-16" else "Datum,Belopp".encode(kodning)
    assert stoppas(filsort, skydd.avkoda, data, filsort) == (
        filsort.filen + " stoppas: filen är sparad som UTF-16 (\"Unicode-text\"), som inte stöds. "
        + filsort.exportera_igen + ", eller spara den som UTF-8 eller CSV.")


@FILSORTER
def test_avkoda_stoppar_okand_teckenkodning(filsort):
    # Byten 0x81 finns inte i Windows-1252, och ensam är den inte giltig UTF-8.
    assert stoppas(filsort, skydd.avkoda, b"Datum\x81", filsort) == (
        filsort.filen + " stoppas: teckenkodningen är varken UTF-8 eller Windows-1252.")


def test_filrad_for_raknar_bara_vanliga_radslut():
    text = "a\nb\r\nc\rd\x0ce\u2028f"
    assert skydd.filrad_for(text, 0) == 1
    assert skydd.filrad_for(text, text.index("b")) == 2
    assert skydd.filrad_for(text, text.index("c")) == 3  # \r\n räknas som ett radslut
    assert skydd.filrad_for(text, text.index("d")) == 4
    assert skydd.filrad_for(text, text.index("f")) == 4  # \x0c och U+2028 räknas inte


@FILSORTER
def test_nul_fel(filsort):
    fel = skydd.nul_fel(7, filsort)
    assert type(fel) is filsort.fel
    assert str(fel) == (filsort.filen + " stoppas: rad 7 i filen innehåller ett NUL-tecken (tecken nummer 0)."
                        " Filen är troligen trasig eller sparad i fel format.")


def test_otillatna_tecken_ar_alla_styrtecken_utom_tabb_och_radslut():
    otillatna = {chr(nummer) for nummer in range(0x110000) if skydd.OTILLATNA_TECKEN.fullmatch(chr(nummer))}
    ratt = {chr(nummer) for nummer in range(0x110000) if unicodedata.category(chr(nummer)) == "Cc"}
    assert otillatna == (ratt - {"\t", "\n", "\r"}) | {"\u2028", "\u2029"}


@pytest.mark.parametrize("tecken", ["\x00", "\x0b", "\x0c", "\x1c", "\x1e", "\x7f", "\x85", "\u2028", "\u2029"])
@FILSORTER
def test_inga_otillatna_tecken_stoppar(filsort, tecken):
    text = "Datum,Belopp\r\n2025-01-02,1\r\nx" + tecken + "y\n"
    assert stoppas(filsort, skydd.inga_otillatna_tecken, text, filsort) == (
        filsort.filen + " stoppas: rad 3 i filen innehåller tecknet U+" + format(ord(tecken), "04X")
        + ", som är ett styrtecken eller en ovanlig radbrytning. " + filsort.om_styrtecken)


@FILSORTER
def test_inga_otillatna_tecken_godtar_tabb_och_radslut(filsort):
    skydd.inga_otillatna_tecken("Datum\tBelopp\r\n2025-01-02\t1\n\r\u00a0ö\u200b", filsort)


# --- CSV-läsningen ---

def test_rubrikens_falt():
    assert skydd.rubrikens_falt(' Belopp ;"Datum";x\r\n', [",", ";"], KOLUMNER) == (";", ["Belopp", "Datum", "x"])
    assert skydd.rubrikens_falt("Datum,Belopp,Datum\n", [","], KOLUMNER) == (",", ["Datum", "Belopp", "Datum"])
    assert skydd.rubrikens_falt("Datum;Summa\n", [",", ";"], KOLUMNER) is None
    assert skydd.rubrikens_falt("Datum;Belopp\n", [","], KOLUMNER) is None
    assert skydd.rubrikens_falt("", [","], KOLUMNER) is None


def test_rubrikens_falt_hoppar_over_rad_som_inte_gar_att_tolka():
    # Med komma som avgränsare blir hela raden ett enda fält, längre än csv-läsarens gräns. Det ger
    # csv.Error, och då prövas nästa avgränsare.
    rad = "Datum;Belopp;" + ";".join(["x" * 1000] * (csv.field_size_limit() // 1000 + 1)) + "\n"
    assert skydd.rubrikens_falt(rad, [",", ";"], KOLUMNER)[0] == ";"
    assert skydd.rubrikens_falt(rad, [","], KOLUMNER) is None


@FILSORTER
def test_csv_fel(filsort):
    fel = skydd.csv_fel(csv.Error("field larger than field limit (131072)"), "X", filsort)
    assert type(fel) is filsort.fel
    assert str(fel) == "X har ett fält som är längre än " + str(csv.field_size_limit()) + " tecken. Filen är troligen trasig."
    fel = skydd.csv_fel(csv.Error("',' expected after '\"'"), "X", filsort)
    assert type(fel) is filsort.fel
    assert str(fel) == ("X kan inte tolkas som CSV, till exempel på grund av ett citattecken i fel läge."
                        " Teknisk detalj: ',' expected after '\"'.")


def csv_lista(textrader, filsort, forsta_filrad=2, avgransare=",", antal_kolumner=2):
    return list(skydd.csv_rader(textrader, forsta_filrad, avgransare, antal_kolumner, filsort))


@FILSORTER
def test_csv_rader_ger_filrad_var_och_falt(filsort):
    textrader = ["a,1\r\n", "\r\n", " , \n", '"b, c",2\n', "d,3"]
    assert csv_lista(textrader, filsort, forsta_filrad=5) == [
        (5, filsort.filen + " stoppas: rad 5 i filen", ["a", "1"]),
        (8, filsort.filen + " stoppas: rad 8 i filen", ["b, c", "2"]),
        (9, filsort.filen + " stoppas: rad 9 i filen", ["d", "3"]),
    ]
    assert csv_lista(["a;1\n"], filsort, avgransare=";") == [(2, filsort.filen + " stoppas: rad 2 i filen", ["a", "1"])]
    assert csv_lista([], filsort) == []


@FILSORTER
def test_csv_rader_raknar_rader_efter_en_post_over_flera_rader(filsort):
    # Posten på rad 2–3 är ett citerat fält med bara en radbrytning, alltså en tom rad som hoppas
    # över. Nästa post börjar på rad 4, inte rad 3: radnumret följer csv-läsarens egen räkning.
    assert csv_lista(['"\n', '",\n', "a,1\n"], filsort) == [(4, filsort.filen + " stoppas: rad 4 i filen", ["a", "1"])]
    assert stoppas(filsort, csv_lista, ['"\n', '",\n', "a,1\n", "b,2,3\n"], filsort).startswith(
        filsort.filen + " stoppas: rad 5 i filen har 3 fält")


@FILSORTER
def test_tolka_datum_kraver_monstret_aven_om_python_godtar_mer(filsort, monkeypatch):
    # I Python 3.9 (projektets .venv) stoppar dt.date.fromisoformat samma texter som mönstret
    # ÅÅÅÅ-MM-DD. Från Python 3.11 godtar den mer, till exempel "20250102". Här låtsas testet att
    # fromisoformat godtar allt, för att visa att mönstret ensamt stoppar sådana datum.
    class AllaDatum:
        @staticmethod
        def fromisoformat(text):
            return text

    monkeypatch.setattr(skydd, "dt", types.SimpleNamespace(date=AllaDatum))
    for text in ("20250102", "2025-W01-1", "2025-01-02T00:00", "\uff12025-01-02"):
        assert stoppas(filsort, skydd.tolka_datum, text, "Datum", "X", filsort) == (
            "X har ett ogiltigt datum i kolumnen 'Datum': " + repr(text) + ".")
@FILSORTER
def test_csv_rader_radbrytning_inuti_falt(filsort):
    # Ett citattecken i fel läge slår ihop raderna 3 och 4 till ett fält. Felet pekar på rad 3.
    assert stoppas(filsort, csv_lista, ["a,1\n", '"b,2\n', 'c",3\n'], filsort) == (
        filsort.filen + " stoppas: rad 3 i filen har en radbrytning inuti fält nummer 1. Det beror troligen"
        " på ett citattecken i fel läge, som kan slå ihop " + filsort.ihopslaget + " till en.")
    for tecken in ("\u2028", "\u2029", "\r"):
        assert "radbrytning inuti fält nummer 2" in stoppas(filsort, csv_lista, ['a,"x' + tecken + 'y"\n'], filsort)


@FILSORTER
def test_csv_rader_fel_antal_falt(filsort):
    assert stoppas(filsort, csv_lista, ["a,1\n", "b,2,3\n"], filsort) == (
        filsort.filen + " stoppas: rad 3 i filen har 3 fält, men rubrikraden har 2.")
    assert stoppas(filsort, csv_lista, ["a\n"], filsort) == (
        filsort.filen + " stoppas: rad 2 i filen har 1 fält, men rubrikraden har 2.")


@FILSORTER
def test_csv_rader_lases_strikt(filsort):
    meddelande = stoppas(filsort, csv_lista, ["a,1\n", '"b"x,2\n'], filsort)
    assert meddelande.startswith(filsort.filen + " stoppas: rad 3 i filen kan inte tolkas som CSV")


@FILSORTER
def test_csv_rader_for_langt_falt(filsort):
    assert stoppas(filsort, csv_lista, ["a," + "x" * (csv.field_size_limit() + 1) + "\n"], filsort) == (
        filsort.filen + " stoppas: rad 2 i filen har ett fält som är längre än " + str(csv.field_size_limit())
        + " tecken. Filen är troligen trasig.")


@FILSORTER
def test_tolka_datum(filsort):
    assert skydd.tolka_datum("2024-02-29", "Datum", "X", filsort) == "2024-02-29"
    for text in ("2025-02-29", "2025-13-01", "2025-1-02", "2025-01-02 ", "20250102", "\uff12025-01-02", ""):
        assert stoppas(filsort, skydd.tolka_datum, text, "Datum", "X", filsort) == (
            "X har ett ogiltigt datum i kolumnen 'Datum': " + repr(text) + ".")


@FILSORTER
def test_tolka_ore(filsort):
    assert skydd.tolka_ore("-1234.50", "Belopp", "X", filsort) == -123450
    for text in ("12,5.0", "1e3", "", "abc"):
        assert stoppas(filsort, skydd.tolka_ore, text, "Belopp", "X", filsort) == (
            "X har ett ogiltigt belopp i kolumnen 'Belopp': " + repr(text) + ".")


def test_heltal_och_datum_godtar_bara_vanliga_siffror():
    assert skydd.HELTAL.fullmatch("0123")
    assert not skydd.HELTAL.fullmatch("\uff11")  # fullbreddssiffra
    assert not skydd.HELTAL.fullmatch("-1")
    assert not skydd.DATUM.fullmatch("\uff12\uff10\uff12\uff15-01-02")
    assert skydd.RADBRYTNINGAR == "\n\r\u2028\u2029"
    assert json.dumps(skydd.TILLATNA_STYRTECKEN) == '"\\t\\n\\r"'
