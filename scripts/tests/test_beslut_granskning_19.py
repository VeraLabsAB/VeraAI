"""Hugos beslut 2026-10-28 efter granskning 19 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 19)").

- J1: vakten körs med /Library/Developer/CommandLineTools/usr/bin/python3 -I, och stoppar allt om den inte kan köras.

Rökprovet kör vakten som Claude Code gör, med den Pythonen (version 3.9 på Hugos dator) och -I, i ett eget
program för varje anrop. Testen hoppar över sig själva om den Pythonen inte finns på datorn. Allt skapas i testets
tillfälliga mapp, och inga länkar görs (H3). Två saker tittar ändå på disken utanför testets mapp, bara läsande:
PATH-regeln tittar på var systemets program ligger (/usr/bin och /bin), som i test_kommandosparr.py, och vakten
tittar på hemmappen. Sökvägar under /.vol och /.nofollow prövas inte här, eftersom vakten då skulle titta på
disken där. De prövas som text i test_beslut_granskning_18.py, och rökprovet i scratchpad prövade dem en gång med
Python 3.9 (GRANSKNING.md).
"""

import json
import os
import subprocess

import pytest

from test_kommandosparr import (
    INSTALLERA,
    INSTALLERAD_VAKT,
    INSTALLNINGAR,
    VAKTEN,
    VAKTENS_PYTHON,
    VAKTENS_PYTHON_KEDJAN,
    VAKTENS_PYTHON_VERSION,
    _en_rad,
    _forsta_sudo,
    _installationskommandon,
    _steg,
)

SOKVAG = "/usr/bin:/bin"
FORSTA = "Stoppat av vakten: "

finns_inte = pytest.mark.skipif(
    not os.path.isfile(VAKTENS_PYTHON), reason=f"{VAKTENS_PYTHON} finns inte på den här datorn"
)


def _bash(kommando):
    return ("Bash", {"command": kommando, "description": "prov"})


def _skriv(sokvag):
    return ("Write", {"file_path": sokvag, "content": "x"})


def _andra(sokvag):
    return ("Edit", {"file_path": sokvag, "old_string": "a", "new_string": "b"})


# (namn, verktyg och indata, väntat: "ok" eller ett ord som felet ska innehålla). <P> är projektmappen och <T> den
# tillfälliga mappen.
FALL = [
    # Tillåtna kommandon och verktyg.
    ("git-status", _bash("git status"), "ok"),
    ("git-log", _bash("git log --stat"), "ok"),
    ("git-diff", _bash("git diff"), "ok"),
    ("git-add", _bash("git add GRANSKNING.md"), "ok"),
    ("git-commit-F", _bash("git commit -F <T>/meddelande.txt"), "ok"),
    ("ls", _bash("ls"), "ok"),
    ("ls-R", _bash("ls -R scripts"), "ok"),
    ("cat", _bash("cat SPEC.md"), "ok"),
    ("head", _bash("head -n 5 SPEC.md"), "ok"),
    ("grep", _bash("grep -rn vakten scripts"), "ok"),
    ("wc", _bash("wc -l SPEC.md"), "ok"),
    ("mkdir-i-T", _bash("mkdir -p <T>/kopia"), "ok"),
    ("cp-R-till-T", _bash("cp -R scripts <T>/kopia"), "ok"),
    ("Read", ("Read", {"file_path": "<P>/SPEC.md"}), "ok"),
    ("Glob", ("Glob", {"pattern": "**/*.py"}), "ok"),
    ("update_plan", ("mcp__ccd_turn__update_plan", {"advance": True}), "ok"),
    # Skrivning i projektet.
    ("Write-i-projektet", _skriv("<P>/ny.txt"), "ok"),
    ("Edit-i-projektet", _andra("<P>/GRANSKNING.md"), "ok"),
    ("Write-relativ", _skriv("scripts/tests/test_ny.py"), "ok"),
    # Förbjudna kommandon.
    ("sudo", _bash("sudo ls"), "sudo och su stoppas alltid"),
    ("su", _bash("su"), "sudo och su stoppas alltid"),
    ("rm", _bash("rm -rf scripts"), "står inte på listan"),
    ("semikolon", _bash("ls; rm x"), "ett kommando i taget"),
    ("lodstreck", _bash("cat SPEC.md | sh"), "ett kommando i taget"),
    ("omdirigering", _bash("ls > fil"), "ett kommando i taget"),
    ("dollar", _bash("cat $HOME"), "ett kommando i taget"),
    ("find", _bash("find . -name x"), "står inte på listan"),
    ("python", _bash("python3 -c 1"), "står inte på listan"),
    ("curl", _bash("curl https://example.com"), "står inte på listan"),
    ("git-C", _bash("git -C /tmp status"), "står inte på listan"),
    ("git-push", _bash("git push"), "står inte på listan"),
    ("jokertecken", _bash("ls *"), "citattecken"),
    ("lasa-utanfor", _bash("cat ../utanfor.txt"), "utanför projektet"),
    ("mkdir-i-projektet", _bash("mkdir -p <P>/ny"), "tillfällig mapp"),
    ("cp-R-till-projektet", _bash("cp -R scripts <P>/kopia"), "tillfällig mapp"),
    ("grep-f", _bash("grep -f x SPEC.md"), "grep får bara söka"),
    ("PATH-andras", _bash("PATH='/tmp' git status"), "ändrar PATH"),
    ("okant-verktyg", ("Monitor", {"command": "ls"}), "står inte på listan över tillåtna verktyg"),
    # Skrivning till .git och .claude.
    ("Write-git-hooks", _skriv("<P>/.git/hooks/pre-commit"), "förbjuden för fil-verktygen"),
    ("Write-GIT", _skriv("<P>/.GIT/config"), "förbjuden för fil-verktygen"),
    ("Edit-git", _andra("<P>/.git"), "förbjuden för fil-verktygen"),
    ("Write-claude", _skriv("<P>/.claude/settings.json"), "förbjuden för fil-verktygen"),
    ("Write-via-punktpunkt-till-git", _skriv("scripts/../.git/config"), "förbjuden för fil-verktygen"),
    # Tom eller ofullständig indata.
    ("tomt-kommando", _bash(""), "kommandot är tomt"),
    ("bara-mellanslag", _bash("   "), "kommandot är tomt"),
    ("Bash-utan-kommando", ("Bash", {}), "indata"),
    ("Write-utan-sokvag", ("Write", {"content": "x"}), "indata"),
    ("Write-med-NUL", _skriv("<P>/a\x00b"), "indata"),
]

TRASIG = [
    ("tom-indata", b""),
    ("inte-json", b"inte json"),
    ("json-lista", b"[]"),
    ("tomt-objekt", b"{}"),
    ("inte-utf8", b"\xff\xfe"),
    ("utan-tool-input", b'{"tool_name": "Bash"}'),
    ("kommandot-ett-tal", b'{"tool_name": "Bash", "tool_input": {"command": 1}}'),
    ("verktyget-ett-tal", b'{"tool_name": 7}'),
    ("avbruten-json", b'{"tool_name": "Bash", "tool_input": {"comm'),
]


@pytest.fixture
def mappar(tmp_path):
    projekt = tmp_path / "projekt"
    tillfallig = tmp_path / "tillfallig"
    (projekt / "scripts" / "tests").mkdir(parents=True)
    tillfallig.mkdir()
    return {"projekt": str(projekt), "tillfallig": str(tillfallig)}


def _fyll_i(varde, mappar):
    if isinstance(varde, str):
        return varde.replace("<P>", mappar["projekt"]).replace("<T>", mappar["tillfallig"])
    if isinstance(varde, dict):
        return {nyckel: _fyll_i(v, mappar) for nyckel, v in varde.items()}
    return varde


def _indata(verktyg, verktygsdata, mappar, cwd=True):
    data = {
        "hook_event_name": "PreToolUse",
        "tool_name": verktyg,
        "tool_input": _fyll_i(verktygsdata, mappar),
        "scratchpad_dir": mappar["tillfallig"],
    }
    if cwd:
        data["cwd"] = mappar["projekt"]
    return json.dumps(data).encode("utf-8")


def _kor(mappar, data, miljo=None, argument=(str(VAKTEN),)):
    if miljo is None:
        miljo = {"PATH": SOKVAG, "CLAUDE_PROJECT_DIR": mappar["projekt"]}
    return subprocess.run(
        [VAKTENS_PYTHON, "-I", *argument],
        input=data,
        capture_output=True,
        env=miljo,
        cwd=mappar["projekt"],
        timeout=10,
    )


def _slapps_igenom(svar):
    assert (svar.returncode, svar.stdout, svar.stderr.decode("utf-8", "replace")) == (0, b"", "")


def _stoppas(svar, ord_=None):
    fel = svar.stderr.decode("utf-8", "replace")
    assert svar.returncode == 2 and svar.stdout == b"", (svar.returncode, fel)
    if ord_ is not None:
        assert fel.startswith(FORSTA) and ord_ in fel, fel


@finns_inte
def test_j1_vaktens_python_ar_minst_3_9():
    svar = subprocess.run(
        [VAKTENS_PYTHON, "-I", "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
        capture_output=True,
        env={"PATH": SOKVAG},
        timeout=10,
    )
    assert svar.returncode == 0
    assert tuple(int(t) for t in svar.stdout.split()) >= (3, 9)


@finns_inte
def test_j1_vakten_gar_att_oversatta_med_vaktens_python():
    # Som py_compile, men utan att skriva någon fil i projektet (__pycache__).
    svar = subprocess.run(
        [VAKTENS_PYTHON, "-I", "-c", "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec')", str(VAKTEN)],
        capture_output=True,
        env={"PATH": SOKVAG},
        timeout=10,
    )
    assert (svar.returncode, svar.stderr) == (0, b"")


@finns_inte
@pytest.mark.parametrize("verktyg_och_data,vantat", [f[1:] for f in FALL], ids=[f[0] for f in FALL])
def test_j1_rokprov(mappar, verktyg_och_data, vantat):
    svar = _kor(mappar, _indata(*verktyg_och_data, mappar))
    if vantat == "ok":
        _slapps_igenom(svar)
    else:
        _stoppas(svar, vantat)


@finns_inte
@pytest.mark.parametrize("data", [t[1] for t in TRASIG], ids=[t[0] for t in TRASIG])
def test_j1_trasig_indata_stoppas(mappar, data):
    _stoppas(_kor(mappar, data), "indata")


@finns_inte
def test_j1_bash_utan_cwd_stoppas(mappar):
    _stoppas(_kor(mappar, _indata(*_bash("ls"), mappar, cwd=False)), "cwd")


@finns_inte
def test_j1_utan_projektmapp_stoppas(mappar):
    _stoppas(_kor(mappar, _indata(*_bash("git status"), mappar), {"PATH": SOKVAG}), "CLAUDE_PROJECT_DIR")


@finns_inte
def test_j1_utan_path_stoppas(mappar):
    miljo = {"CLAUDE_PROJECT_DIR": mappar["projekt"]}
    _stoppas(_kor(mappar, _indata(*_bash("git status"), mappar), miljo), "kan inte säkert avgöra")


@finns_inte
def test_j1_nul_i_cwd_stoppas(mappar):
    data = json.loads(_indata(*_bash("ls"), mappar))
    data["cwd"] = "a\x00b"
    _stoppas(_kor(mappar, json.dumps(data).encode("utf-8")), "annan mapp")


@finns_inte
def test_j1_krasch_nar_felet_skrivs_stoppar(mappar):
    # Ett ensamt surrogattecken i en förbjuden sökväg kommer med i felet, som då inte kan skrivas som UTF-8. Vakten
    # kraschar efter bedömningen, och ska ändå stoppa med kod 2.
    _stoppas(_kor(mappar, _indata(*_skriv("<P>/.git/a\ud800"), mappar)))


@finns_inte
def test_j1_krasch_vid_inlasningen_stoppar(mappar):
    # JSON som är kapslad för djupt får Python att krascha (RecursionError) redan vid inläsningen.
    _stoppas(_kor(mappar, b"[" * 100000))


KRASCH_I_BEDOM = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('kommandosparr', sys.argv[1])\n"
    "modul = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(modul)\n"
    "def kraschar(*_):\n"
    "    raise RuntimeError('prov')\n"
    "modul.bedom = kraschar\n"
    "sys.exit(modul.main())\n"
)


@finns_inte
def test_j1_krasch_inne_i_bedomningen_stoppar(mappar):
    # Bedömningen byts mot en som kraschar, i vaktens Python. Kommandot ska stoppas med kod 2.
    svar = _kor(mappar, _indata(*_bash("ls"), mappar), argument=("-c", KRASCH_I_BEDOM, str(VAKTEN)))
    _stoppas(svar, "oväntat fel")


@finns_inte
def test_j1_saknad_vakt_stoppar(mappar):
    # Finns inte vakten kan Python inte öppna filen, och avslutar med kod 2, som Claude Code läser som "stoppa".
    svar = _kor(mappar, b"{}", argument=(os.path.join(mappar["tillfallig"], "kommandosparr.py"),))
    assert svar.returncode == 2


def test_j1_rokprovet_har_minst_30_anrop():
    assert len(FALL) + len(TRASIG) >= 30


# ---------------------------------------------------------------------------------------------
# Inställningen för vakten (sparr/managed-settings.json).

def _vakter():
    installningar = json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))
    return [vakt_ for grupper in installningar["hooks"].values() for grupp in grupper for vakt_ in grupp["hooks"]]


def test_j1_installningen_startar_vakten_med_utvecklarverktygens_python():
    # Formen med "args": command är bara programmet, och varje argument står för sig, så att inget skal tolkar
    # raden. -I står före vaktens sökväg, och onFailure block stoppar allt om vakten inte kan köras.
    assert _vakter() == [
        {
            "type": "command",
            "command": "/Library/Developer/CommandLineTools/usr/bin/python3",
            "args": ["-I", INSTALLERAD_VAKT],
            "timeout": 10,
            "onFailure": "block",
        }
    ]
    assert VAKTENS_PYTHON == "/Library/Developer/CommandLineTools/usr/bin/python3"


def test_j1_installningen_kor_inte_vakten_via_usr_bin_python3():
    # /usr/bin/python3 väljer utvecklarverktyg efter xcode-select eller DEVELOPER_DIR (granskning 19, J1).
    for vakt_ in _vakter():
        assert vakt_["command"] != "/usr/bin/python3" and "/usr/bin/python3" not in vakt_["args"], vakt_


# ---------------------------------------------------------------------------------------------
# INSTALLERA.md, steg 2 b: Hugo kontrollerar vaktens Python före installationen.

def _steg_2_b():
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 2 b:")]
    return steget


def test_j1_steg_2_b_finns_fore_forprovet_och_installationen():
    text, rader = _installationskommandon()
    rubriker = [r for r, _ in _steg(text)]
    plats = [i for i, r in enumerate(rubriker) if r.startswith("## Steg 2 b:")]
    assert plats and rubriker[plats[0] - 1].startswith("## Steg 2:") and rubriker[plats[0] + 1].startswith("## Steg 3:")
    assert rader.index(VAKTENS_PYTHON_VERSION) < rader.index(VAKTENS_PYTHON_KEDJAN) < _forsta_sudo(rader)


def test_j1_steg_2_b_har_bara_kommandon_som_visar():
    steget = _steg_2_b()
    kommandon = [rad.strip() for b in steget.split("```bash\n")[1:] for rad in b.split("```", 1)[0].splitlines()]
    assert [k for k in kommandon if k] == [VAKTENS_PYTHON_VERSION, VAKTENS_PYTHON_KEDJAN]
    for ord_ in ("sudo", "rm ", "mv ", "chmod", "chown", ">", "cp "):
        assert ord_ not in VAKTENS_PYTHON_KEDJAN and ord_ not in VAKTENS_PYTHON_VERSION, ord_
    assert "bara visar" in _en_rad(steget)


def test_j1_kedjan_visar_filen_dit_lankarna_leder_och_alla_mappar_upp_till_roten():
    # ${f:A} är sökvägen efter alla länkar, ${p:h} mappen ovanför, och slingan slutar först när / är visad.
    assert VAKTENS_PYTHON_KEDJAN.startswith(f"f={VAKTENS_PYTHON}; for p in $f ${{f:A}}; ")
    assert "ls -lde@ $p; [[ $p == / ]] && break; p=${p:h};" in VAKTENS_PYTHON_KEDJAN


@pytest.mark.parametrize(
    "text",
    [
        "3.9 eller nyare",
        "9 eller större",
        "ägaren är `root`",
        "inget `w`** på plats 6 (gruppen) eller plats 9 (alla andra)",
        "samma regel som i steg 2",
        "`com.apple.provenance`",
        "`+` efter de tio tecknen",
        "ska börja med `/Library/Developer/CommandLineTools/`",
        "`No such file or directory`",
        "Stoppa och fråga",
        "installera inte, och fråga",
        "granskning 19, J1, Hugos beslut 2026-10-28",
        '"onFailure": "block"',
    ],
)
def test_j1_steg_2_b_sager_vad_som_ar_ratt_och_fel(text):
    assert text.lower() in _en_rad(_steg_2_b()).lower()


def test_j1_caspers_dator_gor_steg_2_b():
    text = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Caspers dator", 1)[1].split("\n## ", 1)[0])
    assert "steg 2 b" in text


def test_j1_installera_kraver_en_version_med_onfailure():
    forsta = _en_rad(_steg(INSTALLERA.read_text(encoding="utf-8"))[0][1])
    assert "onFailure" in forsta and "2.1.295 eller senare" in forsta


def test_j1_installera_namner_inte_usr_bin_python3_for_vakten():
    # /usr/bin/python3 står kvar bara i steg 9, där projektets Python skapas (en rad med sudo).
    text = INSTALLERA.read_text(encoding="utf-8")
    rader = [rad for rad in text.splitlines() if "/usr/bin/python3" in rad and "CommandLineTools" not in rad]
    assert rader == [
        'sudo /usr/bin/python3 -m venv "/Library/Application Support/ClaudeCode/vera/venv"',
        "- `/usr/bin/python3 -m venv` skapar en **venv**: en egen mapp med Python och plats för paket, som inte",
    ]
