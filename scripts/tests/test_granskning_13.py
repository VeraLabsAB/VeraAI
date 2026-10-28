"""Granskning 13 (2026-10-28): tester som den oberoende granskaren lade till för vakten.

Vakten och de andra testerna ligger i sparr/kommandosparr.py och scripts/tests/test_kommandosparr.py.
Fixturerna (vakt, mappar, rotagd) och hjälpfunktionerna hämtas därifrån, så att proven görs på samma sätt.
Fynden står i GRANSKNING.md under "Granskning 13".

1. ~/.local/bin, där Claude Code för Terminal ligger på Hugos dator (version 2.1.312, uppdragets punkt 9):
   vakten stoppar allt när mappen står före /usr/bin, och släpper igenom när den står sist.
2. Raderna i ~/.zshrc: med zsh, utan Hugos egna filer (-f), visas att nvm-raden, den föreslagna raden för
   ~/.local/bin och Cryptexes-raden, i den ordningen, ger den PATH som INSTALLERA.md väntar sig, också om
   installerarens förslag (~/.local/bin först) redan har körts.
3. P2 i granskning 13: en länk som leder via en annan länk i en mapp som användaren äger. Vakten prövar i
   dag bara länken och slutmålet, inte länken i mitten. Testet är markerat xfail (väntat rött) tills vakten
   rättas i en ny version. Det är strikt: när vakten rättas blir testet grönt, och då måste markeringen tas
   bort.
"""

import os
import subprocess

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    FORE_PROGRAMMET,
    KRYPTEX,
    KRYPTEX_RAD,
    NVM_RAD,
    PLATS,
    SYSTEMETS_SOKVAG,
    _bedom,
    _kryptex_i_testet,
    _lagg_program,
    mappar,
    rotagd,
    vakt,
)

# Granskarens förslag till raden i ~/.zshrc (GRANSKNING.md, granskning 13, P3). Den läggs efter nvm-raden
# och före Cryptexes-raden, så att Cryptexes-mappen fortfarande står sist.
LOKAL_BIN_RAD = "path=( ${path:#$HOME/.local/bin} $HOME/.local/bin )"
# Installerarens förslag, som Hugo inte har kört: det lägger mappen först.
INSTALLERARENS_RAD = 'export PATH="$HOME/.local/bin:$PATH"'


def _lokal_bin(tmp_path):
    """~/.local/bin som på Hugos dator: en mapp som användaren äger, med programmet claude."""
    mapp = str(tmp_path / "hem" / ".local" / "bin")
    _lagg_program(mapp, "claude")
    return mapp


def test_lokala_bin_mappen_forst_stoppar_allt_och_sist_slapps_igenom(vakt, mappar, tmp_path):
    lokal = _lokal_bin(tmp_path)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{lokal}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel and lokal in fel, fel
    assert _bedom(vakt, mappar, "git status", sokvag=f"{SYSTEMETS_SOKVAG}:{lokal}") is None


def test_claude_i_lokala_bin_star_inte_pa_listan(vakt, mappar, tmp_path):
    # Agenten får inte starta Claude Code själv, inte heller med hela sökvägen.
    lokal = _lokal_bin(tmp_path)
    for kommando in ("claude --version", f"{lokal}/claude --version"):
        fel = _bedom(vakt, mappar, kommando, sokvag=f"{SYSTEMETS_SOKVAG}:{lokal}")
        assert fel is not None and "står inte på listan" in fel, (kommando, fel)


def test_hugos_path_efter_de_tre_raderna_slapps_igenom(vakt, mappar, tmp_path, rotagd):
    # Ordningen som INSTALLERA.md ska ge: systemets mappar, sedan nvm-mappen, ~/.local/bin och sist
    # Cryptexes-mappen (som i testet är en kopia av uppbyggnaden på Hugos dator).
    nvm = str(tmp_path / "nvm" / "bin")
    _lagg_program(nvm, "node")
    lokal = _lokal_bin(tmp_path)
    kryptex = _kryptex_i_testet(tmp_path, rotagd)
    assert _bedom(vakt, mappar, "git status", sokvag=f"{SYSTEMETS_SOKVAG}:{nvm}:{lokal}:{kryptex}") is None
    # Installerarens förslag lägger ~/.local/bin först: då stoppas allt.
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{lokal}:{SYSTEMETS_SOKVAG}:{nvm}:{kryptex}")
    assert fel is not None and FORE_PROGRAMMET in fel and lokal in fel, fel


ZSH = "/bin/zsh"


@pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")
@pytest.mark.parametrize(
    "fore",
    ["efter-installerarens-forslag", "utan-forslaget"],
)
def test_raderna_i_zshrc_ger_den_vantade_ordningen(tmp_path, fore):
    # zsh -f läser inga av Hugos filer. Raderna körs i samma ordning som de ska stå sist i ~/.zshrc.
    hem = str(tmp_path / "hem")
    nvm = str(tmp_path / "nvm" / "bin")
    lokal = f"{hem}/.local/bin"
    if fore == "efter-installerarens-forslag":
        # Som om installerarens rad redan hade körts: ~/.local/bin först.
        start = f"{lokal}:{nvm}:/usr/bin:/bin:{KRYPTEX}"
    else:
        # Som på Hugos dator i dag: ~/.local/bin finns inte i PATH.
        start = f"{nvm}:/usr/bin:{KRYPTEX}:/bin"
    skript = "\n".join([NVM_RAD, LOKAL_BIN_RAD, KRYPTEX_RAD, "print -r -- $PATH"])
    svar = subprocess.run(
        [ZSH, "-f", "-c", skript],
        capture_output=True,
        env={"PATH": start, "HOME": hem, "NVM_BIN": nvm},
        timeout=10,
        text=True,
    )
    assert svar.returncode == 0, svar.stderr
    mappar_ = svar.stdout.strip().split(":")
    # De tre sista: nvm-mappen, ~/.local/bin och Cryptexes-mappen. Före dem bara systemets mappar.
    assert mappar_[-3:] == [nvm, lokal, KRYPTEX], mappar_
    assert set(mappar_[:-3]) == {"/usr/bin", "/bin"}, mappar_
    assert len(mappar_) == len(set(mappar_)), "en mapp står två gånger"


def test_installerarens_forslag_lagger_mappen_forst():
    # Därför ska INSTALLERA.md varna för det: $HOME/.local/bin står före $PATH.
    assert INSTALLERARENS_RAD.split('"')[1].startswith("$HOME/.local/bin:")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Granskning 13, P2: vakten prövar inte en länk i mitten av en kedja av länkar (inte rättat)",
)
def test_lank_via_en_lank_i_en_mapp_som_anvandaren_ager_stoppas(vakt, mappar, tmp_path, rotagd):
    # rot/bin/git -> mitten/git -> mal/bin/git. rot och mal låtsas ägas av root (rotagd), men mitten
    # ägs av användaren, som kan byta ut mitten/git mot en länk till ett annat program.
    mal = tmp_path / "mal" / "bin"
    mal_fil = _lagg_program(str(mal), "git")
    mitten = tmp_path / "mitten"
    mitten.mkdir()
    os.symlink(mal_fil, mitten / "git")
    rot = tmp_path / "rot" / "bin"
    rot.mkdir(parents=True)
    os.symlink(mitten / "git", rot / "git")
    rotagd(rot / "git")
    assert not vakt._sakert_agd(str(mitten)), "förutsättning: mitten ägs av användaren"
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel, fel
