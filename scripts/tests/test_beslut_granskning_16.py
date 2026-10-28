"""Hugos beslut 2026-10-28 efter granskning 16 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 16)").

- G3: -R är borttaget ur grep-tilläggen i vakten och i SPEC 7.1. ugrep -R följer alla länkar inne i mappar, också
  länkar som leder ut ur projektet. -r står kvar.
- G7: agenten får inte skapa eller ändra en fil som heter .ugrep (ugreps inställningsfil, som kan köra andra
  program), i någon mapp. Vakten stoppar kommandon som skulle skriva en sådan fil, och de låsta inställningarna
  förbjuder fil-verktygen att skriva den.
"""

import os

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    _bedom,
    _installningar,
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


# ---------------------------------------------------------------------------------------------
# G7: .ugrep förbjuden.

UGREP = ".ugrep"

# Varje kommando på listan som skriver en fil eller mapp, med .ugrep som mål. macOS skiljer i regel inte på
# stora och små bokstäver i filnamn, så .UGREP är samma fil.
UGREP_KOMMANDON = [
    ("mkdir", "mkdir <T>/.ugrep"),
    ("mkdir-p-djupt", "mkdir -p <T>/a/.ugrep/b"),
    ("mkdir-stora", "mkdir <T>/.UGREP"),
    ("cp-mal", "cp -R SPEC.md <T>/.ugrep"),
    ("cp-mal-i-mapp", "cp -R SPEC.md <T>/kopia/.ugrep"),
    ("cp-kalla", "cp -R <T>/.ugrep <T>/kopia"),
    ("cp-kalla-blandade", "cp -R <T>/.Ugrep <T>/kopia"),
    ("tar-c-arkiv", "tar -cf <T>/.ugrep scripts"),
    ("tar-x-mapp", "tar -xf <T>/kopia.tar -C <T>/.ugrep"),
    ("git-archive-o", "git archive -o <T>/.ugrep HEAD"),
    ("git-archive-o-hopskrivet", "git archive -o<T>/.ugrep HEAD"),
    ("git-archive-output", "git archive --output=<T>/.ugrep HEAD"),
]


@pytest.mark.parametrize("kommando", [k for _, k in UGREP_KOMMANDON], ids=[i for i, _ in UGREP_KOMMANDON])
def test_g7_kommandon_som_skriver_ugrep_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and UGREP in fel and "granskning 16, G7" in fel, fel


def test_g7_en_lank_som_leder_till_ugrep_stoppas(vakt, mappar):
    # Målet ser ut som en annan fil, men länken leder till .ugrep.
    lank = f"{mappar['tillfallig']}/ser-oskyldig-ut"
    os.symlink(f"{mappar['tillfallig']}/.ugrep", lank)
    fel = _bedom(vakt, mappar, f"cp -R SPEC.md {lank}")
    assert fel is not None and UGREP in fel, fel


@pytest.mark.parametrize(
    "kommando",
    ["mkdir <T>/ugrep", "mkdir <T>/.ugrep2", "cp -R SPEC.md <T>/x.ugrep", "grep -n '.ugrep' SPEC.md",
     "cat <T>/kopia/SPEC.md"],
)
def test_g7_andra_namn_och_lasning_gar_igenom(vakt, mappar, kommando):
    # Bara en fil eller mapp som heter exakt .ugrep stoppas. Att söka efter ordet går igenom.
    assert _bedom(vakt, mappar, kommando) is None


@pytest.mark.parametrize("regel", ["Edit(//**/.ugrep)", "Edit(~/.ugrep)"])
def test_g7_filverktygen_far_inte_skriva_ugrep(regel):
    # Samma form som förbudet för filen .git (//**/.git gäller en fil med namnet på varje djup).
    assert regel in _installningar()["permissions"]["deny"]


@pytest.mark.parametrize(
    "tillagg", ["--config", "--config=.ugrep", "---", "---.ugrep", "--save-config", "--save-config=.ugrep", "-@"]
)
def test_g7_grep_tillagg_som_pekar_ut_en_installningsfil_stoppas(vakt, mappar, tillagg):
    fel = _bedom(vakt, mappar, f"grep {tillagg} x SPEC.md")
    assert fel is not None and GREP_SOKER in fel, fel


def test_g7_star_i_spec():
    spec = _spec_7_1()
    assert "**`.ugrep` är förbjuden**" in spec and "granskning 16, G7, Hugos beslut 2026-10-28" in spec
