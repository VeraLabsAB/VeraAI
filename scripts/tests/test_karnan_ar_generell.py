"""Kärnan i scripts/ får inte innehålla något företagsspecifikt (SPEC avsnitt 2)."""

import re
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
TESTER = SCRIPTS / "tests"

FORBJUDNA_ORD = ["Syntet", "Testbutik", "Krog", "Bygg"]
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
