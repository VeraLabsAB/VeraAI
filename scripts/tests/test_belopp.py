import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from belopp import formatera_ore, tolka_belopp


# --- tolka_belopp: giltiga belopp ---

@pytest.mark.parametrize(
    "text, ore",
    [
        ("1 234,56", 123456),  # komma som decimaltecken, mellanslag som tusental
        ("1234.56", 123456),   # punkt som decimaltecken
        ("1234,56", 123456),
        ("0,01", 1),
        ("0.10", 10),
        ("12,5", 1250),        # en decimal
        ("12", 1200),          # inga decimaler
        ("0", 0),
        ("  1234,56  ", 123456),  # mellanslag runt om tas bort
    ],
)
def test_tolka_giltiga_belopp(text, ore):
    assert tolka_belopp(text) == ore


@pytest.mark.parametrize(
    "text, ore",
    [
        ("-1 234,56", -123456),
        ("-1234.56", -123456),
        ("-0,01", -1),
        ("-12", -1200),
    ],
)
def test_tolka_negativa_belopp(text, ore):
    assert tolka_belopp(text) == ore


@pytest.mark.parametrize(
    "text, ore",
    [
        ("1 234 567,89", 123456789),
        ("1\u00a0234,56", 123456),       # hårt mellanslag
        ("1\u202f234,56", 123456),       # smalt hårt mellanslag
        ("12 345 678", 1234567800),
        ("999 999 999 999,99", 99999999999999),  # stora belopp blir exakta
    ],
)
def test_tolka_tusentalsavgransare(text, ore):
    assert tolka_belopp(text) == ore


# --- tolka_belopp: ogiltiga belopp ---

@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "abc",
        "12a",
        "12,34,56",
        "1.234,56",    # både punkt och komma
        "1,234.56",
        "12 34,56",    # tusentalsgrupp med fel antal siffror
        "1 2345,00",
        "1  234,00",   # två mellanslag
        "1234,",       # decimaltecken utan decimaler
        ",50",         # kronor saknas
        "--5",
        "- 5",
        "5-",
        "+5",
        "1e3",
        "12 kr",
        "١٢",  # siffror från ett annat skriftsystem
    ],
)
def test_tolka_ogiltig_text_ger_fel(text):
    with pytest.raises(ValueError, match="Ogiltigt belopp"):
        tolka_belopp(text)


@pytest.mark.parametrize("text", ["1,234", "1.234", "0,001", "-12,345", "1 234,567"])
def test_tolka_fler_an_tva_decimaler_ger_fel(text):
    with pytest.raises(ValueError, match="fler än två decimaler"):
        tolka_belopp(text)


@pytest.mark.parametrize("varde", [1234.56, 123456, None, b"12,00"])
def test_tolka_kraver_text(varde):
    with pytest.raises(TypeError):
        tolka_belopp(varde)


# --- formatera_ore ---

@pytest.mark.parametrize(
    "ore, text",
    [
        (123456, "1234,56"),
        (1, "0,01"),
        (10, "0,10"),
        (100, "1,00"),
        (0, "0,00"),
        (-1, "-0,01"),
        (-123456, "-1234,56"),
        (99999999999999, "999999999999,99"),
    ],
)
def test_formatera_ore(ore, text):
    assert formatera_ore(ore) == text


@pytest.mark.parametrize("varde", [12.5, "123", None, True])
def test_formatera_kraver_heltal(varde):
    with pytest.raises(TypeError):
        formatera_ore(varde)


@pytest.mark.parametrize("ore", [0, 1, -1, 99, 100, 123456, -123456, 99999999999999])
def test_formatera_och_tolka_tillbaka_ger_samma_belopp(ore):
    assert tolka_belopp(formatera_ore(ore)) == ore
