"""Kärnan i scripts/ får inte innehålla något företagsspecifikt (SPEC avsnitt 2)."""

import json
import re
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
