"""Steg 18: nästa version av vakten (Hugos beslut 2026-11-06 om Öppet 72 och steg 18, beslut 4).

- K1 (a): vakten startas med -I -S. -S gör att Python inte läser tilläggsmapparna (site-packages), där en .pth-fil annars kan
  köra kod varje gång Python startar, också med -I (granskning 20, K1).
- K3 (b): en cwd som är tom eller inte börjar med / stoppas (granskning 20, K3).
- O1 (c): ! stoppas var det än står, eftersom zsh kan läsa det som en hämtning ur historiken (steg 17, O1).
- O2 (d): = stoppas när ordet hittills är tomt, så att också ''=y och ""=y stoppas (steg 17, O2).
- O4 (e): ett ord som bara är } utanför citattecken stoppas (steg 17, O4).

Vakten prövas både som funktion och som program, med vaktens Python och flaggorna ur sparr/managed-settings.json. Allt skapas i
testets tillfälliga mapp. Ingen text körs i zsh. Hur zsh läser texterna är bedömt i steg 17, inte kört.
"""

import json
import os
import subprocess

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    INSTALLERAD_VAKT,
    INSTALLNINGAR,
    SYSTEMETS_SOKVAG,
    VAKTENS_PYTHON,
    _bedom,
    _indata,
    _kor_programmet,
    mappar,
    vakt,
    vaktens_flaggor,
)

finns_inte = pytest.mark.skipif(
    not os.path.isfile(VAKTENS_PYTHON), reason=f"{VAKTENS_PYTHON} finns inte på den här datorn"
)


# ---------------------------------------------------------------------------------------------
# (a) K1: -I -S


def test_steg_18_a_installningen_har_exakt_flaggorna_och_vaktens_sokvag():
    (grupp,) = json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    (vakt_,) = grupp["hooks"]
    assert vakt_["args"] == ["-I", "-S", INSTALLERAD_VAKT]


@finns_inte
def test_steg_18_a_vaktens_python_med_flaggorna_laser_inte_tillaggsmapparna():
    svar = subprocess.run(
        [
            VAKTENS_PYTHON,
            *vaktens_flaggor(),
            "-c",
            "import sys; print(sys.flags.no_site, sys.flags.isolated, 'site' in sys.modules, "
            "any('site-packages' in mapp for mapp in sys.path))",
        ],
        capture_output=True,
        env={"PATH": SYSTEMETS_SOKVAG},
        timeout=10,
    )
    assert (svar.returncode, svar.stderr) == (0, b"")
    assert svar.stdout.split() == [b"1", b"1", b"False", b"False"]


@finns_inte
@pytest.mark.parametrize(
    "kommando,kod",
    [("git status", 0), ("ls", 0), ("ls; rm x", 2), ("rm x", 2), ("sudo ls", 2)],
    ids=["git-status", "ls", "semikolon", "rm", "sudo"],
)
def test_steg_18_a_vakten_fungerar_i_samma_lage_som_installeras(mappar, kommando, kod):
    # Vakten använder bara Pythons egna delar, så -S ska inte ändra något den behöver.
    assert vaktens_flaggor() == ["-I", "-S"]
    svar = _kor_programmet(mappar, _indata(mappar, kommando))
    assert svar.returncode == kod, svar.stderr
    assert svar.stdout == b""
    assert (svar.stderr == b"") == (kod == 0), svar.stderr


# ---------------------------------------------------------------------------------------------
# (b) K3: cwd


def _med_cwd(mappar, cwd):
    data = _indata(mappar, "ls")
    data["cwd"] = cwd
    return data


@pytest.mark.parametrize("cwd", ["", "projekt", "./projekt", "~/projekt", " /x"], ids=["tom", "relativ", "punkt", "tilde", "mellanslag"])
def test_steg_18_b_cwd_som_inte_ar_en_hel_sokvag_stoppas(vakt, mappar, cwd):
    fel = vakt.bedom(_med_cwd(mappar, cwd), mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "hel sökväg" in fel, fel


def test_steg_18_b_tom_cwd_stoppas_av_programmet(mappar):
    # K3 som granskning 20 såg det: en tom text räknades som vaktens egen arbetsmapp, här projektmappen.
    svar = _kor_programmet(mappar, _med_cwd(mappar, ""))
    assert svar.returncode == 2 and "hel sökväg" in svar.stderr.decode("utf-8"), svar.stderr


def test_steg_18_b_relativ_cwd_stoppas_av_programmet(mappar):
    # Relativt vaktens arbetsmapp leder "projekt" rätt, så här släpptes kommandot igenom förut.
    svar = _kor_programmet(mappar, _med_cwd(mappar, "projekt"), cwd=mappar["hem"])
    assert svar.returncode == 2 and "hel sökväg" in svar.stderr.decode("utf-8"), svar.stderr


def test_steg_18_b_en_riktig_projektmapp_slapps_som_forut(vakt, mappar):
    for cwd in (mappar["projekt"], mappar["projekt"] + "/"):
        assert vakt.bedom(_med_cwd(mappar, cwd), mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG) is None
    svar = _kor_programmet(mappar, _med_cwd(mappar, mappar["projekt"]))
    assert (svar.returncode, svar.stdout, svar.stderr) == (0, b"", b"")


def test_steg_18_b_en_annan_hel_sokvag_stoppas_som_forut(vakt, mappar):
    fel = vakt.bedom(_med_cwd(mappar, mappar["hem"]), mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "annan mapp" in fel, fel


# ---------------------------------------------------------------------------------------------
# (c) O1: !


@pytest.mark.parametrize(
    "kommando",
    ["ls !x", "ls '!x'", 'ls "!x"', "ls !", "ls x!y", "ls x!", "! ls", "ls -l !x", "grep -n '!' SPEC.md", "git log --grep='!x'"],
)
def test_steg_18_c_utropstecken_stoppas_var_det_an_star(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and fel.startswith("Stoppat av vakten") and "tecknet !" in fel, fel


def test_steg_18_c_programmet_stoppar_utropstecken(mappar):
    for kommando in ("ls !x", "ls '!x'", 'ls "!x"', "ls !"):
        svar = _kor_programmet(mappar, _indata(mappar, kommando))
        assert svar.returncode == 2 and "tecknet !" in svar.stderr.decode("utf-8"), kommando


# ---------------------------------------------------------------------------------------------
# (d) O2: = när ordet hittills är tomt


@pytest.mark.parametrize("kommando", ["ls ''=y", 'ls ""=y', "ls ''\"\"=y", "ls =y", "ls x ''=y"])
def test_steg_18_d_likhetstecken_nar_ordet_hittills_ar_tomt_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and "tecknet =" in fel and "citattecken" in fel, fel


@pytest.mark.parametrize("kommando", ["ls x=y", "ls x==y", "ls 'x'=y", "ls '=y'", 'ls "=y"', "ls x='y'"])
def test_steg_18_d_likhetstecken_annars_slapps_som_forut(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


# ---------------------------------------------------------------------------------------------
# (e) O4: ett ord som bara är }


@pytest.mark.parametrize("kommando", ["ls }", "ls x }", "ls } x", "}", "ls ''}", 'ls }""'])
def test_steg_18_e_ett_ord_som_bara_ar_klammer_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and "tecknet }" in fel and "citattecken" in fel, fel


@pytest.mark.parametrize("kommando", ["ls '}'", 'ls "}"', "ls x}y", "ls x}", "ls }y", "ls 'a}'"])
def test_steg_18_e_klammer_annars_slapps_som_forut(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


def test_steg_18_e_programmet_stoppar_klammer_men_inte_inom_citat(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "ls }"))
    assert svar.returncode == 2 and "tecknet }" in svar.stderr.decode("utf-8"), svar.stderr
    svar = _kor_programmet(mappar, _indata(mappar, "ls '}'"))
    assert (svar.returncode, svar.stdout, svar.stderr) == (0, b"", b"")
