"""Hugos beslut 2026-10-28 efter granskning 17 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 17)").

- H3: regeln om prov och test står i CLAUDE.md och SPEC 7.1. Det är en regel i text. Den tekniska spärren är
  sandlådan, som ska vara klar före uppgift 5.
- H1 och H2, alternativ 1: kontrollskriptet godtar exakt en extra uppgift, och bara om den heter exakt
  com.apple.provenance. Andra namn, flera uppgifter och alla extra rättigheter (+) avviker som förut.

Testen här läser bara filer i projektet och skriver bara i testets tillfälliga mapp (H3). De gör inga länkar.
macOS sätter själv com.apple.provenance på filer som skapas där (granskning 17, H1), så det riktiga fallet prövas
med en sådan fil. Andra uppgifter läggs till med /usr/bin/xattr och extra rättigheter med /bin/chmod, bara på
filer i testets tillfälliga mapp. Fall som inte går att skapa på riktigt (till exempel en fil med bara
com.apple.quarantine, eftersom com.apple.provenance inte går att ta bort) prövas med ett eget ls i testets
tillfälliga mapp, som skriver en påhittad rad för just den filen. Skriptet körs med zsh -f, utan compinit och med
en tom fpath, som i test_beslut_granskning_15.py. Det kör /bin/ls på /usr/local och /usr/local/share, som
skriptet alltid gör, men läser inte innehållet i någon systemfil.
"""

import subprocess

import pytest

from test_beslut_granskning_15 import (
    AGARE_RAD,
    ETCFILER_RAD,
    NVM_FUNKTIONER,
    SKRIPTET,
    TERMINAL_INNEHALL,
    TERMINALFIL_RAD,
    _anvandaren,
    _avvikelser,
    _hem,
    _zsh,
    inget_zsh,
)
from test_kommandosparr import INSTALLERA, PROJEKTET, _en_rad, _spec_7_1, _steg

CLAUDE_MD = PROJEKTET / "CLAUDE.md"
LS = "/bin/ls"
XATTR = "/usr/bin/xattr"
CHMOD = "/bin/chmod"
PROVENANCE = "com.apple.provenance"
EXTRA = "har extra rättigheter eller uppgifter (+ eller @)"


# ---------------------------------------------------------------------------------------------
# H3: regeln om prov och test.

H3_REGELN = [
    "Prov och test får bara skapa, ändra eller länka filer i scratchpad",
    "eller i testets tillfälliga mapp",
    "Aldrig länkar (hårda eller mjuka) till något utanför de mapparna",
    "Nya test får inte läsa eller röra riktiga systemfiler",
    "regel i text",
    "sandlådan",
    "före uppgift 5",
    "granskning 17, H3",
]


@pytest.mark.parametrize("del_", H3_REGELN)
@pytest.mark.parametrize("fil", ["CLAUDE.md", "SPEC 7.1"])
def test_h3_regeln_om_prov_och_test_star_i_claude_md_och_spec(fil, del_):
    text = _en_rad(CLAUDE_MD.read_text(encoding="utf-8") if fil == "CLAUDE.md" else _spec_7_1())
    assert del_ in text, f"{fil} saknar: {del_}"


# ---------------------------------------------------------------------------------------------
# H1 och H2: bara exakt com.apple.provenance godtas.


def _kor_skriptet(tmp_path, fil, ls=None):
    """Kör en kopia av det riktiga skriptet där fil är den enda /etc-filen som prövas med ls.

    Som _kopia i test_beslut_granskning_15.py: Terminals fil är en provfil, och den som kör testet räknas som
    root. Men kontrollen av extra uppgifter är orörd. Med ls körs ett eget ls i stället för /bin/ls."""
    terminal = tmp_path / "zshrc_Apple_Terminal"
    terminal.write_text(TERMINAL_INNEHALL, encoding="utf-8")
    text = SKRIPTET.read_text(encoding="utf-8")
    for rad in (TERMINALFIL_RAD, ETCFILER_RAD, AGARE_RAD):
        assert text.count(rad) == 1, rad
    text = text.replace(TERMINALFIL_RAD, f"local terminalfil={terminal}")
    text = text.replace(ETCFILER_RAD, f"local -a etcfiler=({fil})")
    text = text.replace(AGARE_RAD, f"local -a agare=(root {_anvandaren()})")
    if ls:
        assert text.count(f"{LS} ") == 1
        text = text.replace(f"{LS} ", f"{ls} ")
    kopia = tmp_path / "kontrollera-skalet.zsh"
    kopia.write_text(text, encoding="utf-8")
    start = f"fpath=()\n{NVM_FUNKTIONER}source {terminal}\nsource {kopia}\n"
    return _zsh(_hem(tmp_path), start)


def _ls(fil):
    return subprocess.run([LS, "-lde@", "--", str(fil)], capture_output=True, text=True, timeout=30).stdout


@pytest.fixture
def provfil(tmp_path):
    """En fil i testets tillfälliga mapp med exakt en extra uppgift, com.apple.provenance."""
    fil = tmp_path / "provfil"
    fil.write_text("x\n", encoding="utf-8")
    rader = _ls(fil).splitlines()
    if not (len(rader) == 2 and rader[0].split()[0].endswith("@") and rader[1].split() == [PROVENANCE, "11"]):
        pytest.skip(f"filer i testets tillfälliga mapp har inte exakt {PROVENANCE} på den här datorn: {rader}")
    return fil


def _avviker(resultat, fil):
    (rad,) = _avvikelser(resultat)
    assert rad.startswith(f"AVVIKER: ls -l: {fil} {EXTRA}"), resultat
    assert resultat.stdout.endswith("SLUT\n") and "OK\n" not in resultat.stdout, resultat


@inget_zsh
def test_h1_en_fil_med_bara_com_apple_provenance_godtas(tmp_path, provfil):
    resultat = _kor_skriptet(tmp_path, provfil)
    assert resultat.stdout == "OK\nSLUT\n", resultat


@pytest.mark.parametrize(
    "namn", ["com.apple.quarantine", "com.apple.provenance2", "xcom.apple.provenance", "com.apple.provenanc"]
)
@inget_zsh
def test_h1_en_uppgift_till_avviker(tmp_path, provfil, namn):
    # com.apple.provenance går inte att ta bort, så filen får två uppgifter.
    subprocess.run([XATTR, "-w", namn, "prov", str(provfil)], check=True, capture_output=True, timeout=30)
    assert len(_ls(provfil).splitlines()) == 3
    _avviker(_kor_skriptet(tmp_path, provfil), provfil)


@inget_zsh
def test_h1_extra_rattigheter_avviker_ocksa_med_com_apple_provenance(tmp_path, provfil):
    # ls visar bara @ när filen har både uppgifter och extra rättigheter. ls -e visar rättigheterna på en egen rad.
    subprocess.run([CHMOD, "+a", "everyone deny delete", str(provfil)], check=True, capture_output=True, timeout=30)
    rader = _ls(provfil).splitlines()
    assert len(rader) == 3 and rader[0].split()[0].endswith("@") and "deny delete" in rader[2], rader
    _avviker(_kor_skriptet(tmp_path, provfil), provfil)


# Fall som inte går att skapa på riktigt: ett eget ls skriver en påhittad rad för just den här filen, och kör
# /bin/ls för allt annat. {fil} byts mot filens sökväg.
FORSTA_RADEN = "-rw-r--r--{tecken} 1 root  wheel  5 Oct 28 19:25 {fil}\n"
TAB = "\t"
PAHITTADE = [
    ("bara-provenance", "@", f"{TAB}{PROVENANCE}{TAB}   11 \n", True),
    ("bara-provenance-utan-mellanslag", "@", f"{TAB}{PROVENANCE}{TAB}11\n", True),
    ("bara-quarantine", "@", f"{TAB}com.apple.quarantine{TAB}   57 \n", False),
    ("bara-provenance2", "@", f"{TAB}com.apple.provenance2{TAB}   11 \n", False),
    ("provenance-med-stora-bokstaver", "@", f"{TAB}com.apple.PROVENANCE{TAB}   11 \n", False),
    ("provenance-och-quarantine", "@", f"{TAB}{PROVENANCE}{TAB}   11 \n{TAB}com.apple.quarantine{TAB}   57 \n", False),
    ("quarantine-och-provenance", "@", f"{TAB}com.apple.quarantine{TAB}   57 \n{TAB}{PROVENANCE}{TAB}   11 \n", False),
    ("provenance-och-rattigheter", "@", f"{TAB}{PROVENANCE}{TAB}   11 \n 0: group:everyone deny delete\n", False),
    ("snabel-a-utan-uppgift", "@", "", False),
    ("plus", "+", " 0: group:everyone allow write\n", False),
    ("plus-utan-rad", "+", "", False),
    ("plus-med-provenance", "+", f"{TAB}{PROVENANCE}{TAB}   11 \n", False),
    ("tio-tecken-med-en-rad-till", "", f"{TAB}{PROVENANCE}{TAB}   11 \n", False),
    ("provenance-med-text-efter", "@", f"{TAB}{PROVENANCE}{TAB}   11 x\n", False),
    ("provenance-utan-storlek", "@", f"{TAB}{PROVENANCE}{TAB}\n", False),
    ("mellanslag-fore-namnet", "@", f"{TAB} {PROVENANCE}{TAB}   11 \n", False),
]


@pytest.mark.parametrize("tecken,rader,godtas", [p[1:] for p in PAHITTADE], ids=[p[0] for p in PAHITTADE])
@inget_zsh
def test_h1_paahittade_rader_fran_ls(tmp_path, tecken, rader, godtas):
    fil = tmp_path / "provfil"
    fil.write_text("x\n", encoding="utf-8")
    utdata = tmp_path / "ls-utdata"
    utdata.write_text(FORSTA_RADEN.format(tecken=tecken, fil=fil) + rader, encoding="utf-8")
    ls = tmp_path / "eget-ls"
    ls.write_text(f'#!/bin/sh\nif [ "$3" = "{fil}" ]; then /bin/cat {utdata}; else exec {LS} "$@"; fi\n',
                  encoding="utf-8")
    ls.chmod(0o755)
    resultat = _kor_skriptet(tmp_path, fil, ls=ls)
    if godtas:
        assert resultat.stdout == "OK\nSLUT\n", resultat
    else:
        _avviker(resultat, fil)


def test_h1_skriptet_och_steg_4_g_namner_com_apple_provenance():
    text = SKRIPTET.read_text(encoding="utf-8")
    assert f"{LS} -lde@ -- " in text and PROVENANCE in text and "granskning 17, H1" in text
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    g = _en_rad(steget.split("**g. ", 1)[1].split("**h. ", 1)[0])
    assert f"`{PROVENANCE}`" in g and "granskning 17, H1" in g and "`+`" in g
