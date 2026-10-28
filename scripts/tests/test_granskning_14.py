"""Granskning 14 (oberoende granskning 2026-10-28), punkt 4: P2 med längre kedjor, och länkar som pekar på
sig själva eller i en ring.

Proven görs med vaktens egna funktioner, i en tillfällig mapp som pytest skapar. Inget program körs via
länkarna: vakten bara läser länkarna och mapparnas ägare och rättigheter.

Ett test kan inte skapa en mapp som root äger, så fixturen rotagd (från test_kommandosparr.py) låtsas att
de sökvägar testet anger gör det. Allt annat prövas som vanligt.
"""

import os
import subprocess
import time

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    FORE_PROGRAMMET,
    PLATS,
    SYSTEMETS_SOKVAG,
    _bedom,
    _lagg_program,
    mappar,
    rotagd,
    vakt,
)

LANK_PA_VAGEN = "en länk på vägen dit"


def _kedja_av_filer(tmp_path, rotagd, antal, osaker=None):
    """d1/git -> d2/git -> ... -> dN/git -> mal/bin/git, med N = antal länkar.

    Varje mapp d1 ... dN låtsas ägas av root, utom d<osaker> (räknat från 1), som ägs av användaren.
    Returnerar d1, som är mappen som står först i PATH."""
    mal_fil = _lagg_program(str(tmp_path / "mal" / "bin"), "git")
    rotagd(mal_fil)
    mappar_ = [tmp_path / f"d{nummer}" for nummer in range(1, antal + 1)]
    for mapp in mappar_:
        mapp.mkdir()
    for nummer, mapp in enumerate(mappar_):
        mal = mappar_[nummer + 1] / "git" if nummer + 1 < antal else mal_fil
        os.symlink(mal, mapp / "git")
    for nummer, mapp in enumerate(mappar_, start=1):
        if nummer != osaker:
            rotagd(mapp / "git")
    return mappar_[0]


@pytest.mark.parametrize("antal", [3, 4, 5, 8])
def test_lang_kedja_dar_varje_lank_ligger_i_en_rotmapp_slapps_igenom(vakt, mappar, tmp_path, rotagd, antal):
    forsta = _kedja_av_filer(tmp_path, rotagd, antal)
    assert vakt._saker_kedja(str(forsta / "git"))
    assert _bedom(vakt, mappar, "git status", sokvag=f"{forsta}:{SYSTEMETS_SOKVAG}") is None


@pytest.mark.parametrize(
    "antal,osaker",
    [(3, 2), (3, 3), (4, 2), (4, 3), (4, 4), (5, 3), (8, 5), (8, 8)],
)
def test_lang_kedja_med_en_lank_i_en_anvandarmapp_stoppas(vakt, mappar, tmp_path, rotagd, antal, osaker):
    # Den osäkra länken ligger i mitten eller sist i kedjan. Det första och sista steget (sökvägen som den
    # står och slutmålet) är säkra, så bara provet av varje länk kan stoppa.
    forsta = _kedja_av_filer(tmp_path, rotagd, antal, osaker=osaker)
    assert not vakt._sakert_agd(str(tmp_path / f"d{osaker}")), "förutsättning: mappen ägs av användaren"
    assert not vakt._saker_kedja(str(forsta / "git"))
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{forsta}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and LANK_PA_VAGEN in fel, fel


def test_kedja_av_mappar_i_path_med_en_lank_i_en_anvandarmapp_stoppas(vakt, mappar, tmp_path, rotagd):
    # En mapp i PATH före programmet: a/bin -> b/bin -> c/bin -> mal/bin. b ägs av användaren.
    mal = tmp_path / "mal" / "bin"
    mal.mkdir(parents=True)
    rotagd(mal)
    for namn, nasta in (("c", mal), ("b", tmp_path / "c" / "bin"), ("a", tmp_path / "b" / "bin")):
        (tmp_path / namn).mkdir()
        os.symlink(nasta, tmp_path / namn / "bin")
    rotagd(tmp_path / "a" / "bin")
    rotagd(tmp_path / "c" / "bin")
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{tmp_path / 'a' / 'bin'}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel and LANK_PA_VAGEN in fel, fel


def test_kedja_med_relativa_lankar_och_tva_punkter(vakt, mappar, tmp_path, rotagd):
    # d1/git -> ../d2/git -> ../d3/./git -> mal. d2 ägs av användaren. Samma kedja med d2 säker går igenom.
    mal_fil = _lagg_program(str(tmp_path / "mal" / "bin"), "git")
    rotagd(mal_fil)
    for namn in ("d1", "d2", "d3"):
        (tmp_path / namn).mkdir()
    os.symlink(mal_fil, tmp_path / "d3" / "git")
    os.symlink(os.path.join("..", "d3", ".", "git"), tmp_path / "d2" / "git")
    os.symlink(os.path.join("..", "d2", "git"), tmp_path / "d1" / "git")
    rotagd(tmp_path / "d1" / "git")
    rotagd(tmp_path / "d3" / "git")
    assert not vakt._saker_kedja(str(tmp_path / "d1" / "git"))
    rotagd(tmp_path / "d2")
    assert vakt._saker_kedja(str(tmp_path / "d1" / "git"))


# ---------------------------------------------------------------------------------------------
# Länkar som pekar på sig själva eller i en ring. Vakten ska stoppa (eller inte välja filen) och inte
# fastna. Allt låtsas ägas av root, så att det bara är ringen som prövas.


def _sjalvlank(tmp_path, rotagd):
    mapp = tmp_path / "sjalv"
    mapp.mkdir()
    os.symlink("git", mapp / "git")  # git -> git
    rotagd(mapp)
    return mapp


def _ring(tmp_path, rotagd, langd):
    """r1/git -> r2/git -> ... -> r<langd>/git -> r1/git."""
    mappar_ = [tmp_path / f"r{nummer}" for nummer in range(1, langd + 1)]
    for mapp in mappar_:
        mapp.mkdir()
    for nummer, mapp in enumerate(mappar_):
        os.symlink(mappar_[(nummer + 1) % langd] / "git", mapp / "git")
        rotagd(mapp)
    return mappar_[0]


@pytest.mark.parametrize("langd", [1, 2, 3, 7])
def test_ring_av_lankar_ger_falskt_och_fastnar_inte(vakt, tmp_path, rotagd, langd):
    forsta = _sjalvlank(tmp_path, rotagd) if langd == 1 else _ring(tmp_path, rotagd, langd)
    start = time.monotonic()
    assert not vakt._saker_kedja(str(forsta / "git"))
    assert not vakt._saker_plats(str(forsta / "git"))
    assert time.monotonic() - start < 5


@pytest.mark.parametrize("langd", [1, 3])
def test_ring_i_en_mapp_i_path_fore_programmet_stoppas(vakt, mappar, tmp_path, rotagd, langd):
    # Mappen i PATH är själv en ring av länkar: p1 -> p2 -> ... -> p1.
    mappar_ = [tmp_path / f"p{nummer}" for nummer in range(1, langd + 1)]
    for nummer, mapp in enumerate(mappar_):
        os.symlink(mappar_[(nummer + 1) % langd], mapp)
    rotagd(tmp_path)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{mappar_[0]}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel, fel


def test_ring_som_programmet_i_en_saker_mapp_valjs_inte(vakt, mappar, tmp_path, rotagd):
    # En trasig länk (git -> git) i en säker mapp före /usr/bin går inte att köra, så skalet hittar
    # /usr/bin/git. Vakten gör likadant: den prövar /usr/bin/git och mappen före, som är säker.
    mapp = _sjalvlank(tmp_path, rotagd)
    if not vakt._saker_plats("/usr/bin/git"):
        pytest.skip("/usr/bin/git ägs inte säkert av root på den här datorn")
    assert _bedom(vakt, mappar, "git status", sokvag=f"{mapp}:{SYSTEMETS_SOKVAG}") is None


def test_ring_som_python_med_hel_sokvag_stoppas(vakt, mappar, tmp_path, rotagd, monkeypatch):
    # Python med hel sökväg (testsvitens kommando) som är en ring: vakten kan inte avgöra filen och stoppar.
    forsta = _ring(tmp_path, rotagd, 3)
    python = str(forsta / "git")
    monkeypatch.setattr(vakt, "PYTHON", python)
    fel = _bedom(vakt, mappar, f"'{python}' -B -m pytest -p no:cacheprovider -q scripts/tests")
    assert fel is not None and "kan inte säkert avgöra vilken fil" in fel, fel


def test_ring_genom_en_mapplank_pa_vagen_ger_falskt(vakt, tmp_path, rotagd):
    # a/x -> b, b/y -> ../a/x/y: att nå a/x/y kräver att a/x/y följs, som leder tillbaka till sig själv.
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    os.symlink(tmp_path / "b", tmp_path / "a" / "x")
    os.symlink(os.path.join("..", "a", "x", "y"), tmp_path / "b" / "y")
    rotagd(tmp_path / "a")
    rotagd(tmp_path / "b")
    start = time.monotonic()
    assert not vakt._saker_kedja(str(tmp_path / "a" / "x" / "y"))
    assert time.monotonic() - start < 5


# ---------------------------------------------------------------------------------------------
# Punkt 1 (P1 a): kontrollen av alias och funktioner i INSTALLERA.md, steg 4 g och kontrollen efter
# installationen, steg 1. Proven körs med zsh -f, som inte läser några av Hugos filer, med en tillfällig
# hemmapp och bara systemets mappar i PATH. Inget av kommandona körs: zsh bara skriver ut texten.

ZSH = "/bin/zsh"


def _zsh(tmp_path, skript):
    miljo = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "LANG": "C"}
    return subprocess.run(
        [ZSH, "-f", "-c", skript], capture_output=True, text=True, env=miljo, cwd=tmp_path, timeout=20
    ).stdout


@pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")
def test_ett_globalt_alias_med_ett_namn_som_inte_ar_pa_listan_andrar_ett_kommando_pa_listan(tmp_path):
    # Ett globalt alias (alias -g) byts ut var det än står i kommandot, inte bara först. Här heter det
    # "status", som inte är ett av de 13 namnen som steg 4 g säger åt Hugo att leta efter, men det gör
    # om "git status" till "git log".
    # zsh -c läser hela texten på en gång, så aliaset gäller först i text som läses efteråt (eval), som
    # när Claude Code först läser in aliasen och sedan kör agentens kommando.
    ut = _zsh(tmp_path, "alias -g status=log\neval 'print -r -- git status'\nalias")
    rader = ut.splitlines()
    assert rader[0] == "git log", ut
    # alias utan tillägg visar det, men med namnet "status", som Hugo inte är ombedd att leta efter.
    assert "status=log" in rader[1:], ut


@pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")
def test_en_funktion_med_ett_namn_som_inte_ar_pa_listan_kors_fore_varje_kommando(tmp_path):
    # En funktion med det särskilda namnet TRAPDEBUG körs före varje kommando, också i ett skal som inte
    # är interaktivt. Namnet är inte ett av de 13 som steg 4 g säger åt Hugo att leta efter.
    ut = _zsh(tmp_path, "TRAPDEBUG() { print -r -- FORE }\nprint -r -- git status\ntypeset -f +")
    assert "FORE" in ut.splitlines() and "git status" in ut.splitlines(), ut
    assert "TRAPDEBUG" in ut.splitlines(), ut


# ---------------------------------------------------------------------------------------------
# Punkt 3 (P1 b): nvm:s fil bash_completion kör zsh:s compinit när den läses in i zsh (nvm:s källkod,
# github.com/nvm-sh/nvm, filen bash_completion: "compinit" om compinit inte redan finns). compinit läser
# in filen ~/.zcompdump med punkt (.) som zsh-kod. Den filen har inget förbud i sparr/managed-settings.json.

# Samma rader som nvm:s bash_completion kör i zsh (förkortat: utan ZSH_DISABLE_COMPFIX).
NVM_COMPINIT = "autoload -U +X compinit && compinit"


@pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")
def test_compinit_laser_in_zcompdump_i_hemmappen_som_zsh_kod(tmp_path):
    # Första gången skapar compinit ~/.zcompdump i (den tillfälliga) hemmappen.
    _zsh(tmp_path, NVM_COMPINIT)
    dump = tmp_path / ".zcompdump"
    assert dump.is_file()
    # En rad sist i filen, och sedan samma start igen: raden körs, och ett alias därifrån gäller.
    with open(dump, "a", encoding="utf-8") as ut:
        ut.write("print -r -- FRAN_ZCOMPDUMP\nalias git=true\n")
    ut = _zsh(tmp_path, NVM_COMPINIT + "\nalias")
    assert "FRAN_ZCOMPDUMP" in ut.splitlines(), ut
    assert "git=true" in ut.splitlines(), ut


def test_zcompdump_har_ett_forbud_i_installningarna():
    # Var väntat rött (R1). Granskningens förslag: ett förbud för ~/.zcompdump och ~/.zcompdump-*
    # (namnet som till exempel oh-my-zsh använder). Förbudet är byggt efter Hugos beslut 2026-10-28
    # (granskning 14, R1), och markeringen xfail är borttagen i byggsessionen.
    import json

    fil = os.path.join(os.path.dirname(__file__), "..", "..", "sparr", "managed-settings.json")
    with open(fil, encoding="utf-8") as in_:
        neka = json.load(in_)["permissions"]["deny"]
    assert [regel for regel in neka if "zcompdump" in regel]
