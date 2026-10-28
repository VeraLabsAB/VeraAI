"""Hugos beslut 2026-10-28 efter granskning 16 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 16)").

- G3: -R är borttaget ur grep-tilläggen i vakten och i SPEC 7.1. ugrep -R följer alla länkar inne i mappar, också
  länkar som leder ut ur projektet. -r står kvar.
"""

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    _bedom,
    _en_rad,
    _spec_7_1,
    mappar,
    vakt,
)

GREP_SOKER = "grep får bara söka"


def _grep_regeln():
    # Regeln "`grep` får bara söka" i SPEC 7.1, fram till nästa punkt i listan.
    return _spec_7_1().split("**`grep` får bara söka**", 1)[1].split(" - **", 1)[0]


# ---------------------------------------------------------------------------------------------
# G3: -R borttaget.


@pytest.mark.parametrize(
    "kommando",
    [
        "grep -R x scripts",
        "grep -nR x scripts",
        "grep -Rn x scripts",
        "grep -rR x scripts",
        "grep -iRe x scripts",
        "grep -n -R x scripts",
        "grep -R -- x scripts",
        "grep --dereference-recursive x scripts",
        "grep --dereference x scripts",
        "grep --deref x scripts",
        "grep --dereference-recursive=x x scripts",
    ],
)
def test_g3_grep_med_R_stoppas_i_varje_form(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and GREP_SOKER in fel, fel


@pytest.mark.parametrize(
    "kommando", ["grep -r x scripts", "grep -rn x scripts", "grep -nr x scripts", "grep --recursive x scripts"]
)
def test_g3_grep_med_r_gar_igenom_som_forut(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


def test_g3_R_star_inte_pa_listan_i_vakten_eller_spec(vakt):
    assert "R" not in vakt.GREP_KORTA + vakt.GREP_KORTA_VARDE
    assert "-R" not in vakt.GREP_TILLATNA.replace(",", " ").split()
    assert "dereference-recursive" not in vakt.GREP_LANGA
    grep_regel = _grep_regeln()
    lista = grep_regel.split("namnen jämförs exakt:", 1)[1].split("Allt annat stoppas", 1)[0]
    assert "`-R`" not in lista and "`-r`" in lista
    assert "granskning 16, G3" in grep_regel
