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
import las_underlag  # noqa: E402

# Ord som är både kärnans egen nyckel (i bankformat.json eller kassaformat.json) och ett
# kolumnnamn i ett kassaformat. Testdatans kassafil har kolumnen "belopp", och kärnan använder
# samma ord för uppgiften belopp. Därför kan ordet inte sökas efter som text. Att kärnan ändå
# inte har kassans kolumnnamn inbyggt bevisas av test_annat_kassaformat_laser_samma_data i
# test_las_kassa.py, som läser samma Z-rapport med helt andra namn.
KARNANS_EGNA_ORD = {"belopp"}


def namn_i_kassaformaten():
    """Alla kolumnnamn, postnamn och kassaregister från alla företags kassaformat.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/kassaformat.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update(data["kolumner"].values())
        for postnamn in data["poster"].values():
            namn.update(postnamn if isinstance(postnamn, list) else [postnamn])
        namn.update(data["kassaregister"])
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


def kassanamn_i_filer(filer, namnlista, egna_ord=KARNANS_EGNA_ORD):
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
            if text.strip() in namnlista and text.strip() not in egna_ord:
                fynd.append(fil.name + ":" + str(radnummer) + " har textsträngen " + repr(text))
        for radnummer, rad in enumerate(kalla.splitlines(), start=1):
            for namn in kodlika:
                if re.search(r"(?<!\w)" + re.escape(namn) + r"(?!\w)", rad):
                    fynd.append(fil.name + ":" + str(radnummer) + " innehåller " + repr(namn))
    return fynd


def test_kassaformaten_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några kassaformat alls.
    namn = namn_i_kassaformaten()
    assert {"z_nummer", "summa_brutto", "forsaljning", "moms", "betalsatt_kort", "post", "TB-KASSA-1"} <= set(namn)


def test_karnans_egna_ord_ar_verkligen_karnans_nycklar():
    # Skydd mot att undantaget ovan växer med ord som inte är kärnans egna nycklar.
    assert KARNANS_EGNA_ORD <= set(las_bank.KOLUMN_NYCKLAR) | set(las_kassa.KOLUMN_NYCKLAR)


# Underlagets nycklar är kärnans egen form för underlag (las_underlag.py), gemensam för alla
# företag. Några av dem ("datum", "moms", "momssats") råkar också vara namn i testbutikens
# kassaformat. De godtas som textsträngar bara i las_underlag.py, där formen beskrivs. Alla andra
# kärnfiler prövas som förut.
UNDERLAGSMODULEN = SCRIPTS / "las_underlag.py"
UNDERLAGETS_EGNA_ORD = set(las_underlag.NYCKLAR) | set(las_underlag.MOMSRAD_NYCKLAR)


def test_karnan_innehaller_inga_namn_fran_kassaformaten():
    """Kassaformatet hör till företagets konfiguration, inte till kärnan."""
    namn = namn_i_kassaformaten()
    fynd = kassanamn_i_filer([fil for fil in karnans_filer() if fil != UNDERLAGSMODULEN], namn)
    fynd += kassanamn_i_filer([UNDERLAGSMODULEN], namn, KARNANS_EGNA_ORD | UNDERLAGETS_EGNA_ORD)
    assert not fynd, "Kolumnnamn, postnamn eller kassaregister från kassaformatet i kärnan:\n" + "\n".join(fynd)


def test_underlagets_undantag_galler_bara_underlagets_nycklar(tmp_path):
    # Skydd: undantaget släpper bara igenom underlagets egna nycklar, inte andra namn ur kassaformatet.
    assert UNDERLAGSMODULEN in karnans_filer()
    assert {"datum", "moms", "momssats"} <= UNDERLAGETS_EGNA_ORD
    fil = tmp_path / "x.py"
    fil.write_text('a = "moms"\nb = "forsaljning"\nc = "summa_brutto"\n', encoding="utf-8")
    assert kassanamn_i_filer([fil], namn_i_kassaformaten()) == [
        "x.py:1 har textsträngen 'moms'", "x.py:2 har textsträngen 'forsaljning'",
        "x.py:3 har textsträngen 'summa_brutto'", "x.py:3 innehåller 'summa_brutto'"]
    assert kassanamn_i_filer([fil], namn_i_kassaformaten(), KARNANS_EGNA_ORD | UNDERLAGETS_EGNA_ORD) == [
        "x.py:2 har textsträngen 'forsaljning'", "x.py:3 har textsträngen 'summa_brutto'",
        "x.py:3 innehåller 'summa_brutto'"]


# --- Testdatans underlag ---

def namn_i_testdatans_underlag():
    """Alla id, motparter och fakturanummer i testdatans underlag, för alla testföretag och perioder."""
    namn = set()
    for fil in sorted((SCRIPTS.parent / "testdata").glob("*/*/underlag/*.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update([data["id"], data["motpart"], data["fakturanummer"]])
    return sorted(namn)


def namn_ur_testdatan_i_filer(filer, namnlista):
    """Var testdatans namn står i filerna, som hela ord, även i kommentarer och förklarande text."""
    monster = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, namnlista)) + r")(?![\w-])")
    fynd = []
    for fil in filer:
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            fynd += [fil.name + ":" + str(radnummer) + " innehåller " + repr(traff.group(1))
                     for traff in monster.finditer(rad)]
    return fynd


def test_testdatans_underlag_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några underlag alls.
    namn = namn_i_testdatans_underlag()
    assert len(namn) > 60
    assert {"LEV-TE", "BUTIK-STAD", "SYNT-U-2025-004", "SYNT-TE-761"} <= set(namn)


def test_karnan_innehaller_inga_namn_fran_testdatans_underlag():
    """Motparter, fakturanummer och id hör till underlagen, inte till kärnan (gäller även las_underlag.py)."""
    assert UNDERLAGSMODULEN in karnans_filer()
    fynd = namn_ur_testdatan_i_filer(karnans_filer(), namn_i_testdatans_underlag())
    assert not fynd, "Namn från testdatans underlag i kärnan:\n" + "\n".join(fynd)


def test_testdatanamn_kontrollen_hittar_inbyggda_namn(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text('# dublett av SYNT-U-2025-003\nif motpart == "LEV-TE":\n    pass\nx = "LEV-TELE-2"\n',
                   encoding="utf-8")
    assert namn_ur_testdatan_i_filer([fil], namn_i_testdatans_underlag()) == [
        "x.py:1 innehåller 'SYNT-U-2025-003'", "x.py:2 innehåller 'LEV-TE'"]


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


# --- De gemensamma skydden i inlasning_skydd.py ---

def test_karnan_soker_aven_i_inlasning_skydd():
    # Skydd: alla sökningar ovan (företagsnamn, organisationsnummer, bankformatens kolumnnamn och
    # kassaformatens namn) går igenom karnans_filer(). Den gemensamma modulen ska vara en av dem.
    assert SCRIPTS / "inlasning_skydd.py" in karnans_filer()


def test_inlasning_skydd_namner_ingen_sorts_fil():
    """De gemensamma skydden vet inte vilken sorts fil de läser.

    Allt som skiljer bankfilen och Z-filen åt, som felklass och vad filen kallas, kommer in som en
    _Filsort från las_bank.py och las_kassa.py. Själva modulen får inte nämna bank, kassa eller
    Z-rapport någonstans, inte ens i kommentarer.
    """
    text = (SCRIPTS / "inlasning_skydd.py").read_text(encoding="utf-8").casefold()
    fynd = [ord for ord in ("bank", "kassa", "z-rapport", "z-fil") if ord in text]
    assert not fynd, "inlasning_skydd.py nämner " + ", ".join(map(repr, fynd))
