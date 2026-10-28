"""Hugos beslut 2026-10-28 efter granskning 17 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 17)").

- H3: regeln om prov och test står i CLAUDE.md och SPEC 7.1. Det är en regel i text. Den tekniska spärren är
  sandlådan, som ska vara klar före uppgift 5.
- H1 och H2, alternativ 1: kontrollskriptet godtar exakt en extra uppgift, och bara om den heter exakt
  com.apple.provenance. Andra namn, flera uppgifter och alla extra rättigheter (+) avviker som förut.
- Steg 2 och 13 i INSTALLERA.md: samma regel som H1 (Hugos beslut 2026-10-28 kväll).
- H6: vakten prövar sökvägen för verktygen som skriver eller ändrar filer mot förbuden i managed-settings.json,
  utan hänsyn till stora och små bokstäver, och så att ../, ~ och andra sätt att skriva samma namn inte hjälper.
  Kommandon prövas på samma sätt. Sökvägar till systemets filer (till exempel /etc) prövas bara som text med
  vaktens funktioner för förbuden, och kommandon prövas med en tom PATH, så att vakten inte tittar på systemets
  program.

Testen här läser bara filer i projektet och skriver bara i testets tillfälliga mapp (H3). De gör inga länkar.
macOS sätter själv com.apple.provenance på filer som skapas där (granskning 17, H1), så det riktiga fallet prövas
med en sådan fil. Andra uppgifter läggs till med /usr/bin/xattr och extra rättigheter med /bin/chmod, bara på
filer i testets tillfälliga mapp. Fall som inte går att skapa på riktigt (till exempel en fil med bara
com.apple.quarantine, eftersom com.apple.provenance inte går att ta bort) prövas med ett eget ls i testets
tillfälliga mapp, som skriver en påhittad rad för just den filen. Skriptet körs med zsh -f, utan compinit och med
en tom fpath, som i test_beslut_granskning_15.py. Det kör /bin/ls på /usr/local och /usr/local/share, som
skriptet alltid gör, men läser inte innehållet i någon systemfil.
"""

import os
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
from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    INSTALLERA,
    PROJEKTET,
    _bedom,
    _en_rad,
    _fyll_i,
    _indata,
    _installningar,
    _spec_7_1,
    _steg,
    mappar,
    vakt,
)

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


# ---------------------------------------------------------------------------------------------
# Steg 2 och 13 i INSTALLERA.md: samma regel som H1 (Hugos beslut 2026-10-28 kväll). Stegen läses av Hugo, inte av
# skriptet, så texten ska säga regeln i enkla ord, och ls ska visa namnet på varje uppgift.


def _steget(nummer):
    (steget,) = [
        t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith(f"## Steg {nummer}:")
    ]
    return steget


@pytest.mark.parametrize("nummer", [2, 13])
def test_steg_2_och_13_visar_namnet_pa_varje_uppgift(nummer):
    ls_rader = [r for r in _steget(nummer).splitlines() if r.startswith("ls ")]
    assert ls_rader and all(r.startswith("ls -lde@ ") for r in ls_rader), ls_rader


def test_steg_2_sager_regeln_i_enkla_ord():
    text = _en_rad(_steget(2))
    assert "(Hugos beslut 2026-10-28 kväll, samma regel som H1)" in text
    assert f"**exakt en** indragen rad som börjar med `{PROVENANCE}`" in text
    assert "`+` efter de tio tecknen" in text and "alltid" in text
    assert "`com.apple.quarantine`" in text and "`com.apple.provenance2`" in text
    assert "mer än en indragen rad" in text and "**Allt annat: stoppa och fråga.**" in text
    # Det gamla, att varje @ stoppar, står inte kvar.
    assert "Står det `+` eller `@` direkt efter de tio tecknen" not in text


def test_steg_13_hanvisar_till_regeln_i_steg_2():
    text = _en_rad(_steget(13))
    assert "eller står det `+` eller `@` efter de tio tecknen" not in text
    assert f"`{PROVENANCE}`" in text and "regeln i steg 2" in text and "`+` stoppar alltid" in text
    assert "installationen räknas som misslyckad. Stoppa och fråga." in text


def test_steg_2_och_13_har_samma_regel_som_skriptet():
    # Skriptet godtar samma sak som stegen: exakt en uppgift, com.apple.provenance, och aldrig +.
    skriptet = SKRIPTET.read_text(encoding="utf-8")
    assert f"$'\\t'{PROVENANCE}$'\\t'" in skriptet and "${#rader} == 2" in skriptet


# ---------------------------------------------------------------------------------------------
# H6: verktygen som skriver filer, och sökvägar i kommandon, utan hänsyn till stora och små bokstäver.

FORBJUDEN = "är förbjuden för fil-verktygen"
# Kommandona prövas med en tom PATH, så att vakten inte tittar på systemets program (H3). Ett kommando som klarar
# alla andra regler stoppas då först av PATH-regeln, som prövas sist.
PATH_SAKNAS = "(PATH saknas)"


def _skriv(vakt, mappar, sokvag, verktyg="Write"):
    """Vaktens svar när verktyget skriver till sokvag. <P> är projektet, <T> den tillfälliga mappen och <H>
    hemmappen, alla i testets tillfälliga mapp."""
    indata = _indata(mappar, "", verktyg)
    sokvag = _fyll_i(sokvag, mappar).replace("<H>", mappar["hem"])
    falt = "notebook_path" if verktyg == "NotebookEdit" else "file_path"
    indata["tool_input"] = {falt: sokvag, "content": "x", "old_string": "a", "new_string": "b"}
    return vakt.bedom(indata, mappar["projekt"], mappar["hem"], "")


GIT_SKRIVNINGAR = [
    "<P>/.GIT/hooks/pre-commit",
    "<P>/.Git/HOOKS/x",
    "<P>/.git/hooks/x",
    "<P>/scripts/../.git/hooks/x",
    "<P>/scripts/../.GIT/hooks/pre-commit",
    "<P>/scripts/tests/../../.Git/HOOKS/x",
    "scripts/../.GIT/hooks/pre-commit",
    ".git/hooks/x",
    ".GIT/hooks/pre-commit",
    "<P>//.GIT//hooks/x",
    "<P>/./.GIT/./hooks/x",
    "<P>/.GIT/hooks/",
    "<P>/.GIT",
    "<P>/.Git/config",
    "<T>/kopia/.GIT/hooks/x",
    "<T>/../hem/projekt/.git/hooks/x",
]


@pytest.mark.parametrize("sokvag", GIT_SKRIVNINGAR)
@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_h6_skrivverktyg_till_git_stoppas(vakt, mappar, verktyg, sokvag):
    fel = _skriv(vakt, mappar, sokvag, verktyg)
    assert fel is not None and FORBJUDEN in fel and "granskning 17, H6" in fel, fel


@pytest.mark.parametrize("sokvag", ["<P>/.GIT/hooks/x.ipynb", "<P>/scripts/x.ipynb"])
def test_h6_notebookedit_stoppas(vakt, mappar, sokvag):
    # NotebookEdit står inte på listan i SPEC 7.1 och stoppas alltid. Sökvägen prövas också.
    assert _skriv(vakt, mappar, sokvag, "NotebookEdit") is not None


ANDRA_FORBUD = [
    "<H>/.ZSHRC",
    "<H>/.Zshenv",
    "~/.zshrc",
    "~/.ZPROFILE",
    "<H>/.zshrc.ZWC",
    "<H>/.ZCOMPDUMP-abc",
    "<H>/.NVM/nvm.sh",
    "<H>/LIBRARY/LaunchAgents/x.plist",
    "<H>/Library/launchagents/x.plist",
    "<H>/.CLAUDE/settings.json",
    "~/.Claude/settings.json",
    "<H>/.Claude.json",
    "<H>/.local/BIN/claude",
    "<H>/.LOCAL/share/claude/x",
    "<H>/library/application support/claude/x",
    "<H>/.SSH/config",
    "<H>/.GITCONFIG",
    "<H>/.config/GIT/config",
    "<H>/BIN/x",
    "<H>/.UGREP",
    "<P>/.CLAUDE/settings.json",
    "<P>/.MCP.json",
    "<P>/.VENV/bin/python",
    "<P>/scripts/.Ugrep",
    "<P>/../.ZSHRC",
    "<P>/../../hem/.zshrc",
]


@pytest.mark.parametrize("sokvag", ANDRA_FORBUD)
def test_h6_andra_forbud_galler_oavsett_bokstaver(vakt, mappar, sokvag):
    fel = _skriv(vakt, mappar, sokvag, "Edit")
    assert fel is not None and FORBJUDEN in fel, fel


def test_h6_en_lank_till_git_stoppas(vakt, mappar):
    # Länken och målet ligger båda i testets tillfälliga mapp.
    os.mkdir(os.path.join(mappar["projekt"], ".git"))
    os.symlink(os.path.join(mappar["projekt"], ".git"), os.path.join(mappar["projekt"], "ser-oskyldig-ut"))
    fel = _skriv(vakt, mappar, "<P>/ser-oskyldig-ut/hooks/pre-commit")
    assert fel is not None and FORBJUDEN in fel, fel


@pytest.mark.parametrize(
    "sokvag",
    ["<P>/SPEC.md", "<P>/scripts/ny.py", "scripts/ny.py", "<P>/.gitignore", "<P>/git/hooks/x", "<P>/.github/x",
     "<P>/x.git", "<T>/kopia/SPEC.md", "<H>/VERA/prov.txt", "<H>/.zshrc.fore-vera", "<P>/.claudex"],
)
@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_h6_vanliga_filer_gar_att_skriva(vakt, mappar, verktyg, sokvag):
    assert _skriv(vakt, mappar, sokvag, verktyg) is None


@pytest.mark.parametrize(
    "tool_input",
    [{}, {"file_path": ""}, {"file_path": None}, {"file_path": 3}, {"file_path": "<P>/x\x00"}],
)
def test_h6_skrivverktyg_utan_en_sokvag_stoppas(vakt, mappar, tool_input):
    indata = _indata(mappar, "", "Write")
    indata["tool_input"] = {k: (_fyll_i(v, mappar) if isinstance(v, str) else v) for k, v in tool_input.items()}
    assert vakt.bedom(indata, mappar["projekt"], mappar["hem"], "") is not None


@pytest.mark.parametrize(
    "sokvag,regel",
    [
        ("/ETC/zshrc", "//etc/zshrc"),
        ("/private/etc/zshrc", "//etc/zshrc"),
        ("/PRIVATE/ETC/ZSHRC_Apple_Terminal", "//etc/zshrc_*"),
        ("/System/Volumes/Data/private/etc/zshenv", "//etc/zshenv"),
        ("/system/volumes/data/Users/vera/.zshrc", "~/.zshrc"),
        ("/System/Volumes/Data/Users/vera/projekt/.GIT/hooks/x", "//**/.git/**"),
        ("/applications/CLAUDE.app/Contents/x", "//Applications/Claude.app/**"),
        ("/OPT/Homebrew/bin/git", "//opt/homebrew/**"),
        ("/Users/VERA/Library/Application Support/Claude/claude-code/x",
         "~/Library/Application Support/Claude/claude-code/**"),
        ("/Users/vera/.zcompdump-dator-5.9", "~/.zcompdump*"),
        ("/users/vera/./x/../.zshrc", "~/.zshrc"),
        ("/Users/vera/.git", "//**/.git"),
        ("/Users/vera/.cláude/x", None),
        ("/Users/vera/VERA/agent/SPEC.md", None),
    ],
)
def test_h6_forbuden_som_text(vakt, sokvag, regel):
    # Bara text: ingen fil läses. Hemmappen är /Users/vera.
    assert vakt._forbud_som_passar(vakt._andra_namn(sokvag), ["/Users/vera"]) == regel


def test_h6_samma_namn_skrivet_pa_olika_satt_jamfors_lika(vakt):
    # é som ett tecken och som e med accent, och stora och små bokstäver (macOS skiljer inte på dem).
    assert vakt._jamforbar("café") == vakt._jamforbar("café") == vakt._jamforbar("CAFÉ")


def test_h6_vakten_har_samma_forbud_som_installningarna(vakt):
    edit = [r[len("Edit("):-1] for r in _installningar()["permissions"]["deny"] if r.startswith("Edit(")]
    assert list(vakt.SKRIVFORBUD) == edit


def test_h6_vakten_provar_alla_skrivverktyg(vakt):
    assert vakt.SKRIVVERKTYG == {
        "Write": "file_path",
        "Edit": "file_path",
        "MultiEdit": "file_path",
        "NotebookEdit": "notebook_path",
    }


# Kommandon: mål i den tillfälliga mappen som är förbjudna för fil-verktygen stoppas också, och mål i projektet
# stoppas som förut (de ligger inte i den tillfälliga mappen).
KOMMANDON_TILL_GIT = [
    "cp -R SPEC.md .GIT/hooks/pre-commit",
    "cp -R SPEC.md <P>/.Git/HOOKS/x",
    "cp -R SPEC.md scripts/../.git/hooks/x",
    "mkdir -p .git/hooks/x",
    "mkdir -p <T>/.GIT/hooks",
    "mkdir <T>/kopia/.Git",
    "cp -R SPEC.md <T>/kopia/.Git/HOOKS/pre-commit",
    "cp -R SPEC.md <T>/../tillfallig/.GIT/hooks/x",
    "cp -R SPEC.md <T>/../hem/projekt/.git/hooks/x",
    "tar -x -f <T>/kopia.tar -C <T>/.GIT",
    "git archive -o <T>/.Git/x.tar HEAD",
    "cp -R .GIT <T>/kopia",
    "mkdir -p <T>/.CLAUDE/x",
    "mkdir -p <T>/x/.VENV/bin",
    "cp -R SPEC.md <T>/.MCP.json",
]


@pytest.mark.parametrize("kommando", KOMMANDON_TILL_GIT)
def test_h6_kommandon_till_git_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando, sokvag="")
    assert fel is not None and PATH_SAKNAS not in fel, fel


@pytest.mark.parametrize(
    "kommando", ["mkdir -p <T>/kopia/scripts", "cp -R SPEC.md <T>/kopia/.gitignore", "cp -R scripts <T>/kopia"]
)
def test_h6_vanliga_kommandon_klarar_reglerna_fore_path_regeln(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando, sokvag="")
    assert fel is not None and PATH_SAKNAS in fel, fel


def test_h6_session_i_hemmappen_skriven_med_andra_bokstaver_stoppas(vakt, mappar):
    # Projektmappen är hemmappen, men hemmappen anges med stora bokstäver.
    hem = mappar["hem"]
    indata = _indata(mappar, "git status")
    indata["cwd"] = hem
    fel = vakt.bedom(indata, hem, os.path.join(os.path.dirname(hem), "HEM"), "")
    assert fel is not None and "hemmappen" in fel, fel


def test_h6_tillfallig_mapp_i_projektet_skriven_med_andra_bokstaver_godtas_inte(vakt, mappar):
    # Den tillfälliga mappen ligger i projektet, men anges med stora bokstäver. Den godtas inte, så mkdir stoppas.
    projekt = mappar["projekt"]
    tillfallig = os.path.join(os.path.dirname(projekt), "PROJEKT", "kopia")
    indata = _indata(mappar, f"mkdir -p {tillfallig}/x")
    indata["scratchpad_dir"] = tillfallig
    fel = vakt.bedom(indata, projekt, mappar["hem"], "")
    assert fel is not None and "tillfällig mapp" in fel, fel


def test_h6_star_i_spec():
    spec = _spec_7_1()
    assert "**Fil-verktygen och förbuden** (granskning 17, H6, Hugos beslut 2026-10-28)" in spec
    assert "utan hänsyn till stora och små bokstäver" in spec and "`Write`" in spec and "`Edit`" in spec
