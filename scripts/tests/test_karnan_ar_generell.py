"""Kärnan i scripts/ får inte innehålla något företagsspecifikt (SPEC avsnitt 2)."""

import ast
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
TESTER = SCRIPTS / "tests"
FORETAG = SCRIPTS.parent / "foretag"

FORBJUDNA_ORD = ["Syntet", "Testbutik", "Krog", "Bygg", "Swedbank"]
ORGANISATIONSNUMMER = re.compile(r"(?<!\d)\d{6}-\d{4}(?!\d)", re.ASCII)


def karnans_filer():
    return sorted(
        fil for fil in SCRIPTS.rglob("*.py")
        if TESTER not in fil.parents
    )


def test_karnan_har_filer_att_soka_i():
    # Skydd mot att testet blir grönt för att det inte hittar några filer alls.
    assert SCRIPTS / "belopp.py" in karnans_filer()


def test_karnan_innehaller_inget_foretagsspecifikt():
    fynd = []
    for fil in karnans_filer():
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            plats = str(fil.relative_to(SCRIPTS.parent)) + ":" + str(radnummer)
            for ord in FORBJUDNA_ORD:
                if ord in rad:
                    fynd.append(plats + " innehåller " + repr(ord))
            for nummer in ORGANISATIONSNUMMER.findall(rad):
                fynd.append(plats + " innehåller organisationsnummer " + repr(nummer))

    assert not fynd, "Företagsspecifikt innehåll i kärnan:\n" + "\n".join(fynd)


def kolumnnamn_i_bankformaten():
    """Alla kolumnnamn från alla företags bankformat.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/bankformat.json")):
        namn.update(json.loads(fil.read_text(encoding="utf-8"))["kolumner"].values())
    return sorted(namn)


def test_bankformaten_har_kolumnnamn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några bankformat alls.
    assert "Bokfört saldo" in kolumnnamn_i_bankformaten()


def test_karnan_innehaller_inga_kolumnnamn_fran_bankformaten():
    """Bankformatet hör till företagets konfiguration (F5), inte till kärnan.

    Kolumnnamnen söks som hela ord och med skiftläge, alltså stor och liten bokstav som i
    konfigurationen. "Belopp" ger träff, men inte "Beloppet" eller fältnamnet "belopp_ore".
    """
    monster = {namn: re.compile(r"(?<!\w)" + re.escape(namn) + r"(?!\w)") for namn in kolumnnamn_i_bankformaten()}
    fynd = []
    for fil in karnans_filer():
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            plats = str(fil.relative_to(SCRIPTS.parent)) + ":" + str(radnummer)
            for namn, regex in monster.items():
                if regex.search(rad):
                    fynd.append(plats + " innehåller kolumnnamnet " + repr(namn))

    assert not fynd, "Kolumnnamn från bankformatet i kärnan:\n" + "\n".join(fynd)


# --- Kassaformatet (F5 för kassan) ---

sys.path.insert(0, str(SCRIPTS))

import las_bank  # noqa: E402
import las_kassa  # noqa: E402

# Ord som är både kärnans egen nyckel (i bankformat.json eller kassaformat.json) och ett
# kolumnnamn i ett kassaformat. Testdatans kassafil har kolumnen "belopp", och kärnan använder
# samma ord för uppgiften belopp. Därför kan ordet inte sökas efter som text. Att kärnan ändå
# inte har kassans kolumnnamn inbyggt bevisas av test_annat_kassaformat_laser_samma_data i
# test_las_kassa.py, som läser samma Z-rapport med helt andra namn.
KARNANS_EGNA_ORD = {"belopp"}


def namn_i_kassaformaten():
    """Alla kolumnnamn och postnamn från alla företags kassaformat.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/kassaformat.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update(data["kolumner"].values())
        for postnamn in data["poster"].values():
            namn.update(postnamn if isinstance(postnamn, list) else [postnamn])
    return sorted(namn)


def strangar_i_koden(kalla):
    """(radnummer, text) för varje textsträng i Python-koden, utom docstrings (förklarande text)."""
    trad = ast.parse(kalla)
    docstrings = set()
    for nod in ast.walk(trad):
        if isinstance(nod, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and nod.body:
            forsta = nod.body[0]
            if isinstance(forsta, ast.Expr) and isinstance(forsta.value, ast.Constant):
                docstrings.add(id(forsta.value))
    return [
        (getattr(nod, "lineno", 0), nod.value) for nod in ast.walk(trad)
        if isinstance(nod, ast.Constant) and isinstance(nod.value, str) and id(nod) not in docstrings
    ]


def kassanamn_i_filer(filer, namnlista):
    """Var kassaformatens namn står i filerna.

    - En textsträng i koden som är exakt ett namn ger träff, till exempel "forsaljning".
    - Ett namn med understreck eller siffra, till exempel summa_brutto, ser ut som en kod och
      aldrig som svensk text. Det ger träff var det än står som helt ord, även i kommentarer.
    Vanliga ord som "moms" får alltså förekomma i förklarande text och i felmeddelanden.
    """
    fynd = []
    kodlika = [namn for namn in namnlista if re.search(r"[_\d]", namn)]
    for fil in filer:
        kalla = fil.read_text(encoding="utf-8")
        for radnummer, text in strangar_i_koden(kalla):
            if text.strip() in namnlista and text.strip() not in KARNANS_EGNA_ORD:
                fynd.append(fil.name + ":" + str(radnummer) + " har textsträngen " + repr(text))
        for radnummer, rad in enumerate(kalla.splitlines(), start=1):
            for namn in kodlika:
                if re.search(r"(?<!\w)" + re.escape(namn) + r"(?!\w)", rad):
                    fynd.append(fil.name + ":" + str(radnummer) + " innehåller " + repr(namn))
    return fynd


def test_kassaformaten_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några kassaformat alls.
    namn = namn_i_kassaformaten()
    assert {"z_nummer", "summa_brutto", "forsaljning", "moms", "betalsatt_kort", "post"} <= set(namn)


def test_karnans_egna_ord_ar_verkligen_karnans_nycklar():
    # Skydd mot att undantaget ovan växer med ord som inte är kärnans egna nycklar.
    assert KARNANS_EGNA_ORD <= set(las_bank.KOLUMN_NYCKLAR) | set(las_kassa.KOLUMN_NYCKLAR)


def test_karnan_innehaller_inga_namn_fran_kassaformaten():
    """Kassaformatet hör till företagets konfiguration, inte till kärnan."""
    fynd = kassanamn_i_filer(karnans_filer(), namn_i_kassaformaten())
    assert not fynd, "Kolumnnamn eller postnamn från kassaformatet i kärnan:\n" + "\n".join(fynd)


def test_kassanamn_kontrollen_hittar_inbyggda_namn(tmp_path):
    """Skydd: kontrollen ovan ska verkligen slå larm när ett namn är inbyggt i koden."""
    fil = tmp_path / "x.py"
    fil.write_text(
        '"""Förklaring om moms och post."""\n'
        'def f(rad):\n'
        '    """Docstring om forsaljning."""\n'
        '    fel = "momsen stämmer inte"\n'
        '    if rad["post"] == "forsaljning":\n'
        '        return rad[f"{1}"]\n'
        '    # summa_brutto står i en kommentar\n',
        encoding="utf-8",
    )
    assert sorted(kassanamn_i_filer([fil], namn_i_kassaformaten())) == [
        "x.py:5 har textsträngen 'forsaljning'",
        "x.py:5 har textsträngen 'post'",
        "x.py:7 innehåller 'summa_brutto'",
    ]
