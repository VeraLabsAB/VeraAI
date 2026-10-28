"""Q1 (granskning 11): vakten som spärrar den fasta kommandolistan i SPEC 7.1.

Vakten ligger i sparr/kommandosparr.py. Claude Code kör den före varje verktyg som agenten använder,
med datorns egen Python (/usr/bin/python3 -I). Den släpper bara igenom det som SPEC 7.1 tillåter och
stoppar allt annat med ett fel på svenska. Planen och Hugos beslut står i GRANSKNING.md under
"Granskning 11 – plan för Q1".

Testerna visar
- att varje kommando i SPEC 7.1 går igenom (TILLATNA),
- att varje regel och varje omväg i planen stoppas, med rätt skäl (STOPPAS och testerna under den),
- att programmet fungerar som Claude Code väntar sig: kod 0 och ingen utskrift när kommandot släpps
  igenom, kod 2 och ett fel på svenska när det stoppas, och kod 2 också när indata är trasig,
- att vakten bara använder Pythons egna delar och går med datorns egen Python,
- att förslaget till låsta inställningar (sparr/managed-settings.json) och installationsbeskrivningen
  (sparr/INSTALLERA.md) stämmer med planen.

I kommandona står <P> för projektmappen och <T> för den tillfälliga mappen (scratchpad-mappen). Båda
skapas på nytt för varje test, så att inget test rör det riktiga projektet.
"""

import ast
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJEKTET = Path(__file__).resolve().parents[2]
SPARR = PROJEKTET / "sparr"
VAKTEN = SPARR / "kommandosparr.py"
INSTALLNINGAR = SPARR / "managed-settings.json"
INSTALLERA = SPARR / "INSTALLERA.md"
SYSTEMETS_PYTHON = "/usr/bin/python3"
INSTALLERAD_VAKT = "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
INSTALLERADE_INSTALLNINGAR = "/Library/Application Support/ClaudeCode/managed-settings.json"

# Hugos beslut 2026-10-28 om vakten, beslut 1 (alternativ c): projektets Python med pytest flyttas till en
# mapp som root äger, bredvid vakten. Hugo skapar den själv (INSTALLERA.md). Pytest-kommandona i SPEC 7.1
# pekar dit, och sökvägen står inom citattecken eftersom "Application Support" har ett mellanslag.
NY_VENV = "/Library/Application Support/ClaudeCode/vera/venv"
NY_PYTHON = f"{NY_VENV}/bin/python"
PYTEST_FAST = "-B -m pytest -p no:cacheprovider"
PYTEST = f"'{NY_PYTHON}' {PYTEST_FAST}"
GAMLA_PYTEST = f".venv/bin/python {PYTEST_FAST}"

# PATH-regeln (Hugos beslut 2026-10-28, beslut 1): vakten letar upp programmet i PATH och kontrollerar
# var det ligger. Testerna använder datorns egna mappar för program, som ägs av systemet (root).
SYSTEMETS_SOKVAG = "/usr/bin:/bin"


@pytest.fixture(scope="module")
def vakt():
    if not VAKTEN.exists():
        pytest.fail(f"Vakten finns inte: {VAKTEN}")
    spec = importlib.util.spec_from_file_location("kommandosparr", VAKTEN)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture
def mappar(tmp_path):
    hem = tmp_path / "hem"
    projekt = hem / "projekt"
    tillfallig = tmp_path / "tillfallig"
    (projekt / "scripts" / "tests").mkdir(parents=True)
    tillfallig.mkdir()
    return {"hem": str(hem), "projekt": str(projekt), "tillfallig": str(tillfallig)}


def _fyll_i(kommando, mappar):
    return kommando.replace("<P>", mappar["projekt"]).replace("<T>", mappar["tillfallig"])


def _indata(mappar, kommando, verktyg="Bash"):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": verktyg,
        "tool_input": {"command": _fyll_i(kommando, mappar), "description": "prov"},
        "cwd": mappar["projekt"],
        "scratchpad_dir": mappar["tillfallig"],
    }


def _bedom(vakt, mappar, kommando, verktyg="Bash", sokvag=SYSTEMETS_SOKVAG):
    return vakt.bedom(_indata(mappar, kommando, verktyg), mappar["projekt"], mappar["hem"], sokvag)


# ---------------------------------------------------------------------------------------------
# Det som SPEC 7.1 tillåter går igenom. En rad per rad i tabellen i 7.1, och de regler under den
# som tillåter något (läsa i kopior, provfiler i kopian, tillägg till pytest).

# Rad 1 och 2: testsviten i projektet och mot en kopia, med Python på den nya platsen. Ingen mapp som
# root äger kan skapas i ett test, så formerna prövas med en Python i en mapp som testet låtsas att root
# äger (se fixturen rotagd och testerna under "Hugos beslut 2026-10-28 om vakten").
TILLATNA_PYTEST = [
    # Rad 1: testsviten i projektet.
    ("pytest-projektet", f"{PYTEST} -q scripts/tests"),
    # Rad 2: testsviten mot en kopia, hela mappen eller en testfil i kopian.
    ("pytest-kopia", f"{PYTEST} <T>/kopia/scripts/tests"),
    ("pytest-kopia-testfil", f"{PYTEST} <T>/kopia/scripts/tests/test_prov.py"),
    # Tillägg som bara ändrar vad som visas.
    ("pytest-tillagg", f"{PYTEST} -qq --tb=short -rA -p no:randomly -k regelbok scripts/tests"),
    ("pytest-tillagg-separata", f"{PYTEST} -q --tb line -r fE -k 'not langsam' scripts/tests"),
    ("pytest-k-hopskrivet", f"{PYTEST} -kbelopp <T>/kopia/scripts/tests"),
]

TILLATNA = [
    # git status, log, diff, add, commit, show och archive.
    ("git-status", "git status"),
    ("git-log", "git log"),
    ("git-log-tillagg", "git log --oneline -5"),
    ("git-diff", "git diff"),
    ("git-diff-stat", "git diff --stat"),
    ("git-diff-text", "git diff --text SPEC.md"),
    ("git-add", "git add scripts/belopp.py"),
    ("git-commit-m", "git commit -m 'Rubrik' -m 'Brödtext'"),
    ("git-commit-fil", "git commit -F <T>/meddelande.txt"),
    ("git-show", "git show 'HEAD~1:SPEC.md'"),
    ("git-show-stat", "git show --stat HEAD"),
    ("git-archive-o", "git archive -o <T>/kopia.tar HEAD"),
    ("git-archive-output", "git archive --format=tar --output=<T>/kopia.tar HEAD"),
    # ls, cat, head, tail, grep, diff, find, wc och sort, i projektet och i kopior.
    ("ls", "ls"),
    ("ls-tillagg", "ls -la scripts"),
    ("ls-tillfallig", "ls <T>"),
    ("cat", "cat SPEC.md"),
    ("cat-kopia", "cat <T>/kopia/SPEC.md"),
    ("head", "head -n 20 SPEC.md"),
    ("tail", "tail -5 PROGRESS.md"),
    ("grep", "grep -n 'Q1' GRANSKNING.md"),
    ("grep-include", "grep -rn --include='*.py' 'def ' scripts"),
    ("diff", "diff SPEC.md <T>/kopia/SPEC.md"),
    ("diff-mappar", "diff -r scripts <T>/kopia/scripts"),
    ("find-namn", "find . -name '*.py'"),
    ("find-typ", "find scripts -type f"),
    ("wc", "wc -l SPEC.md"),
    ("sort", "sort <T>/lista.txt"),
    # mkdir, cp -R, tar och git archive med mål i den tillfälliga mappen.
    ("mkdir", "mkdir <T>/kopia"),
    ("mkdir-p", "mkdir -p <T>/a/b"),
    ("cp-R", "cp -R scripts <T>/kopia"),
    ("cp-R-flera", "cp -R SPEC.md scripts <T>/kopia"),
    ("tar-packa-upp", "tar -xf <T>/kopia.tar -C <T>/kopia"),
    ("tar-packa-upp-z", "tar -xzvf <T>/k.tar.gz -C <T>/k"),
    ("tar-packa-ihop", "tar -cf <T>/paket.tar scripts"),
    ("tar-lista", "tar -tf <T>/paket.tar"),
]


@pytest.mark.parametrize("kommando", [k for _, k in TILLATNA], ids=[i for i, _ in TILLATNA])
def test_kommandon_pa_listan_gar_igenom(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


# Granskning 12, P4 (Hugos beslut 2026-10-28): vakten släpper bara igenom verktyg som står på en
# uttrycklig lista, och listan står i SPEC 7.1 ("Tillåtna verktyg"). Hugo valde i chatten 2026-10-28
# grunden (Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion och WebFetch) och dessutom ToolSearch,
# appens planlista och slutruta, Skill och Agent.
VERKTYGSLISTAN = [
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "AskUserQuestion",
    "WebFetch",
    "ToolSearch",
    "Skill",
    "Agent",
    "mcp__ccd_turn__update_plan",
    "mcp__ccd_turn__wrap_up",
]
SPEC = PROJEKTET / "SPEC.md"
SPEC_VERKTYG_RUBRIK = "**Tillåtna verktyg**"


def _verktygen_i_spec():
    rader = [r for r in SPEC.read_text(encoding="utf-8").splitlines() if SPEC_VERKTYG_RUBRIK in r]
    assert len(rader) == 1, f"SPEC 7.1 ska ha exakt en rad med {SPEC_VERKTYG_RUBRIK}"
    return re.findall(r"`([^`]+)`", rader[0])


def test_verktygslistan_i_spec_ar_hugos_beslut():
    assert _verktygen_i_spec() == VERKTYGSLISTAN


def test_vakten_har_samma_verktygslista_som_spec(vakt):
    # Säger texten och vakten olika gäller den strängaste, och skillnaden rättas (SPEC 7.1). Testet
    # gör att de inte kan bli olika utan att någon märker det.
    assert list(vakt.TILLATNA_VERKTYG) == _verktygen_i_spec()


@pytest.mark.parametrize("verktyg", VERKTYGSLISTAN)
def test_alla_verktyg_pa_listan_slapps_igenom(vakt, mappar, verktyg):
    # Bash prövas mot kommandolistan, så det får ett kommando som står där.
    assert _bedom(vakt, mappar, "git status", verktyg) is None


OKANDA_VERKTYG = [
    "mcp__x__nytt_verktyg",  # granskarens förslag: ett påhittat namn
    "NotebookEdit",
    "WebSearch",
    "CronCreate",
    "RemoteTrigger",
    "EnterWorktree",
    "mcp__Claude_Code_iOS_Simulator__control",
    "mcp__ccd_session_mgmt__set_session_permission_mode",
    "mcp__scheduled-tasks__create_scheduled_task",
    "mcp__abc__COMPOSIO_REMOTE_WORKBENCH",
    "mcp__ccd_turn__update_plan_x",
    "bash",
    "read",
    "Read ",
    "",
]


@pytest.mark.parametrize("verktyg", OKANDA_VERKTYG)
def test_verktyg_som_inte_star_pa_listan_stoppas(vakt, mappar, verktyg):
    fel = _bedom(vakt, mappar, "git status", verktyg)
    assert fel is not None and VERKTYG in fel, fel


@pytest.mark.parametrize("verktyg", ["Read", "Write", "Edit", "Glob", "Grep", "WebFetch"])
def test_vanliga_filverktyg_slapps_igenom(vakt, mappar, verktyg):
    # SPEC 7.1 gäller bara kommandon (planen, regel 2). Fil-verktygen släpps igenom.
    indata = _indata(mappar, "", verktyg)
    indata["tool_input"] = {"file_path": mappar["projekt"] + "/SPEC.md"}
    assert vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG) is None


def test_agenten_kan_fraga_och_skriva_filer_i_vera(vakt, mappar):
    # Kontrollen efter installationen (INSTALLERA.md): agenten ska fortfarande kunna fråga Hugo och
    # skriva filer i ~/VERA. Vakten ska alltså släppa igenom båda, också utanför projektmappen.
    fraga = _indata(mappar, "", "AskUserQuestion")
    fraga["tool_input"] = {"questions": [{"question": "Prov?", "header": "Prov", "options": []}]}
    assert vakt.bedom(fraga, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG) is None
    skriv = _indata(mappar, "", "Write")
    skriv["tool_input"] = {"file_path": os.path.join(mappar["hem"], "VERA", "prov.txt"), "content": "x"}
    assert vakt.bedom(skriv, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG) is None


KONTROLL_RUBRIK = "## Kontroll efter installationen"


def _kontrollen():
    text = INSTALLERA.read_text(encoding="utf-8")
    assert KONTROLL_RUBRIK in text, "avsnittet saknas"
    return text.split(KONTROLL_RUBRIK, 1)[1]


def test_kontrollen_efter_installationen_ar_sista_avsnittet():
    # Hugos beslut 2026-10-28: kontrollerna står i ett eget avsnitt sist i INSTALLERA.md.
    assert "\n## " not in _kontrollen()


def test_kontrollen_gors_i_en_ny_session():
    assert "ny session" in _kontrollen()


@pytest.mark.parametrize(
    "steg",
    [
        "Enterprise managed settings (file)",  # /status, code.claude.com/docs/en/managed-settings
        "`ls; ls`",
        "`git status`",
        "`sudo ls`",
        "kan fortfarande fråga dig",
        "kan fortfarande skriva filer i `~/VERA`",
        "worktree",
    ],
)
def test_kontrollen_efter_installationen_har_hugos_steg(steg):
    # Hugos beslut 2026-10-28: /status, ls; ls stoppas, git status går igenom, sudo stoppas, agenten kan
    # fråga och skriva i ~/VERA, och en worktree-session fungerar eller stoppas på ett säkert sätt.
    assert steg in _kontrollen()


# Hugos beslut 2026-10-28, 7 (granskning 12, P2 och beslut a): provet där vakten fallerar står i
# kontrollen efter installationen. Hugo flyttar vakten tillfälligt med sudo mv, ser att ett vanligt
# kommando stoppas, flyttar tillbaka och jämför kontrollsummorna.
FLYTTA_UNDAN = f'sudo mv "{INSTALLERAD_VAKT}" "{INSTALLERAD_VAKT}.av"'
FLYTTA_TILLBAKA = f'sudo mv "{INSTALLERAD_VAKT}.av" "{INSTALLERAD_VAKT}"'


def _kommandon_i_kontrollen():
    block = re.findall(r"```bash\n(.*?)```", _kontrollen(), flags=re.S)
    return [rad.strip() for b in block for rad in b.splitlines() if rad.strip()]


def test_kontrollen_provar_en_vakt_som_fallerar():
    assert "en vakt som fallerar" in _kontrollen()
    rader = _kommandon_i_kontrollen()
    assert FLYTTA_UNDAN in rader and FLYTTA_TILLBAKA in rader
    summa = [
        i
        for i, r in enumerate(rader)
        if r.startswith("shasum -a 256 ") and INSTALLERAD_VAKT in r and INSTALLERADE_INSTALLNINGAR in r
    ]
    # Ordningen: flytta undan, flytta tillbaka, jämför summorna.
    assert summa and rader.index(FLYTTA_UNDAN) < rader.index(FLYTTA_TILLBAKA) < min(summa)


def test_bara_kontrollen_flyttar_vakten_och_bara_fram_och_tillbaka():
    _, rader = _installationskommandon()
    flyttar = [r for r in rader if r.startswith("sudo mv")]
    assert flyttar == [FLYTTA_UNDAN, FLYTTA_TILLBAKA]
    installationen = INSTALLERA.read_text(encoding="utf-8").split(KONTROLL_RUBRIK, 1)[0]
    assert "sudo mv" not in installationen


# Hugos beslut 2026-10-28, 8 (texten godkänd av Hugo i chatten samma dag): installationen kräver en
# oberoende granskning men inte provet gjort av en människa (steg 8). Provet krävs före de fyra
# tillfällena nedan, och det ska stå både i SPEC 7.1 och i INSTALLERA.md.
FORE_PROVET = [
    'före läget "auto"',
    "före körningar utan att Hugo tittar",
    "före första hela körningen på riktiga underlag",
    "före första kund",
]


def _en_rad(text):
    # Radbrytningarna i Markdown-filerna räknas som mellanslag, så att en mening kan brytas var som helst.
    return " ".join(text.split())


def _spec_7_1():
    text = SPEC.read_text(encoding="utf-8")
    return _en_rad(text.split("### 7.1 Fast kommandolista", 1)[1].split("\n## ", 1)[0])


@pytest.mark.parametrize("tillfalle", FORE_PROVET)
def test_provet_kravs_fore_auto_obevakat_riktiga_underlag_och_kund(tillfalle):
    assert tillfalle in _spec_7_1()
    assert tillfalle in _en_rad(_kontrollen())


def test_installationen_kraver_granskning_men_inte_provet():
    spec = _spec_7_1()
    assert "Hugos beslut 2026-10-28, 8" in spec
    assert "installeras först när en oberoende granskning är klar" in spec
    assert "krävs inte för installationen" in spec
    fore = INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[1].split("\n## ", 1)[0]
    assert "behövs inte före installationen" in _en_rad(fore)
    kontrollen = _en_rad(_kontrollen())
    assert "Steg 1–7 ska vara klara innan uppgift 4 körs" in kontrollen
    assert "Kör inte uppgift 4 förrän alla steg är klara" not in kontrollen


def test_systemets_python_stoppar_med_kod_2_nar_vakten_saknas(tmp_path):
    # Det är därför provet stoppar: när vakten är bortflyttad kan /usr/bin/python3 inte öppna filen och
    # avslutar med kod 2, som Claude Code läser som "stoppa". Provet visar alltså att en saknad vakt
    # stoppar, men prövar inte onFailure (som gäller andra koder än 0 och 2). Se INSTALLERA.md.
    svar = subprocess.run(
        [SYSTEMETS_PYTHON, "-I", str(tmp_path / "kommandosparr.py")],
        input=b"{}",
        capture_output=True,
        env={"PATH": "/usr/bin:/bin"},
        timeout=10,
    )
    assert svar.returncode == 2


def test_installationen_jamfor_kontrollsummor_fore_och_efter_kopieringen():
    # Hugos beslut 2026-10-28, punkt 4: Hugo jämför summorna med dem som granskningen skriver upp
    # innan han kopierar, och kontrollerar efteråt att det är samma filer som ligger på plats.
    _, rader = _installationskommandon()
    summor = [i for i, r in enumerate(rader) if r.startswith("shasum -a 256 ")]
    forsta_kopian = min(i for i, r in enumerate(rader) if r.startswith(("sudo ditto", "sudo cp")))
    sista_kopian = max(i for i, r in enumerate(rader) if r.startswith(("sudo ditto", "sudo cp")))
    fore = [i for i in summor if i < forsta_kopian]
    efter = [i for i in summor if i > sista_kopian]
    assert fore and efter
    for i in fore:
        assert "sparr/kommandosparr.py" in rader[i] and "sparr/managed-settings.json" in rader[i]
    for i in efter:
        assert INSTALLERAD_VAKT in rader[i] and INSTALLERADE_INSTALLNINGAR in rader[i]


# ---------------------------------------------------------------------------------------------
# Det som stoppas. Varje rad har ett ord som felet ska innehålla, så att testet visar att rätt
# regel stoppade kommandot och inte en annan.

SUDO = "sudo och su stoppas alltid"
IHOP = "ett kommando i taget"
CITAT = "citattecken"
OSYNLIGT = "osynligt eller styrande tecken"
LISTAN = "står inte på listan"
GIT_TILLAGG = "git-tillägget"
UTANFOR = "utanför projektet"
TILLFALLIG = "tillfällig mapp"
FIND = "find får bara söka"
PYTEST_FORM = "pytest"
TILLAGG = "tillägget"
TAR = "tar"
VERKTYG = "står inte på listan över tillåtna verktyg"
PLATS = "ägs inte av systemet (root) eller går att skriva i"
OSAKER = "kan inte säkert avgöra vilken fil"
FORE_PROGRAMMET = "före programmet i PATH"
ANDRAR_PATH = "ändrar PATH"

STOPPAS = [
    # Regel 1: sudo och su stoppas alltid (Hugos beslut 5 och 7).
    ("sudo", "sudo ls", SUDO),
    ("sudo-anvandare", "sudo -u root ls", SUDO),
    ("sudo-hel-sokvag", "/usr/bin/sudo ls", SUDO),
    ("sudo-versaler", "SUDO ls", SUDO),
    ("sudo-citat", '"sudo" ls', SUDO),
    ("sudo-mellanslag-fore", "   sudo git status", SUDO),
    ("sudo-och-mer", "sudo ls; ls", SUDO),
    ("su", "su", SUDO),
    ("su-root", "su root", SUDO),
    ("su-streck", "su -", SUDO),
    ("su-citat", "'su' -", SUDO),
    # Regel 4: inga ihopkopplade kommandon, ingen omdirigering, inget $(...).
    ("semikolon", "ls; rm x", IHOP),
    ("och-och", "ls && rm x", IHOP),
    ("eller-eller", "ls || rm x", IHOP),
    ("bakgrund", "ls & rm x", IHOP),
    ("ror", "ls | head", IHOP),
    ("till-fil", "ls > x", IHOP),
    ("lagg-till-fil", "ls >> x", IHOP),
    ("fel-till-utskrift", "ls 2>&1", IHOP),
    ("fel-bort", "ls 2>/dev/null", IHOP),
    ("fran-fil", "cat < x", IHOP),
    ("kommando-i-kommando", "cat $(rm x)", IHOP),
    ("variabel", "cat $HOME", IHOP),
    ("bakatfnuttar", "cat `rm x`", IHOP),
    ("tva-rader", "ls\nrm x", IHOP),
    ("vagnretur", "ls\r\nrm x", IHOP),
    ("omvant-snedstreck", "ls \\; rm x", IHOP),
    ("semikolon-i-citat", "grep 'a;b' SPEC.md", IHOP),
    ("kommando-i-meddelande", 'git commit -m "$(cat x)"', IHOP),
    ("find-exec-semikolon", "find . -name x -exec rm {} \\;", IHOP),
    # Tecken som skalet byter ut mot något annat än det som står (jokertecken, ~, = och liknande).
    ("stjarna", "cat *", CITAT),
    ("stjarna-i-sokvag", "ls scripts/*.py", CITAT),
    ("fragetecken", "cat ?.md", CITAT),
    ("hakparentes", "cat [ab].md", CITAT),
    ("klammer", "cat {a,b}", CITAT),
    ("tilde", "cat ~/x", CITAT),
    ("tilde-ensam", "ls ~", CITAT),
    ("tilde-i-git", "git show HEAD~1", CITAT),
    ("cirkumflex", "git show HEAD^", CITAT),
    ("brädgård", "ls #x", CITAT),
    ("parentes", "(ls)", CITAT),
    ("likhetstecken-forst", "cat =python3", CITAT),
    ("citat-ej-stangt", 'cat "x', CITAT),
    ("enkelcitat-ej-stangt", "cat 'x", CITAT),
    # Osynliga och styrande tecken: det ska synas exakt vad som körs.
    ("tabb", "ls\tscripts", OSYNLIGT),
    ("riktningstecken", "ls " + chr(0x202E) + "scripts", OSYNLIGT),
    ("hart-mellanslag", "ls" + chr(0x00A0) + "scripts", OSYNLIGT),
    ("nollbredd", "ls scr" + chr(0x200B) + "ipts", OSYNLIGT),
    ("nolltecken", "ls\x00", OSYNLIGT),
    # Tomt kommando.
    ("tomt", "", "tomt"),
    ("bara-mellanslag", "   ", "tomt"),
    # Regel 5: första ordet ska stå på listan.
    ("cd", "cd ..", LISTAN),
    ("cd-tillfallig", "cd <T>", LISTAN),
    ("sed", "sed -n 1p SPEC.md", LISTAN),
    ("echo", "echo x", LISTAN),
    ("printf", "printf x", LISTAN),
    ("rm", "rm x", LISTAN),
    ("rm-rf", "rm -rf scripts", LISTAN),
    ("mv", "mv a b", LISTAN),
    ("chmod", "chmod 777 x", LISTAN),
    ("ln", "ln -s x y", LISTAN),
    ("touch", "touch x", LISTAN),
    ("for", "for", LISTAN),
    ("env", "env ls", LISTAN),
    ("bash", "bash -c ls", LISTAN),
    ("sh", "sh x", LISTAN),
    ("zsh", "zsh", LISTAN),
    ("python3", "python3 x.py", LISTAN),
    ("xargs", "xargs rm", LISTAN),
    ("perl", "perl -e 1", LISTAN),
    ("awk", "awk 1 x", LISTAN),
    ("curl", "curl https://exempel.se", LISTAN),
    ("open", "open .", LISTAN),
    ("eget-skript", "./skript.sh", LISTAN),
    ("variabel-fore", "X=1 ls", LISTAN),
    ("command", "command ls", LISTAN),
    ("exec", "exec ls", LISTAN),
    ("nohup", "nohup ls", LISTAN),
    ("time", "time ls", LISTAN),
    ("true", "true", LISTAN),
    ("ls-hel-sokvag", "/bin/ls", LISTAN),
    ("ls-versaler", "LS", LISTAN),
    # git: bara status, log, diff, add, commit, show och archive som andra ord.
    ("git-ensamt", "git", LISTAN),
    ("git-C", "git -C .. status", LISTAN),
    ("git-c-forst", "git -c core.pager=x log", LISTAN),
    ("git-no-pager", "git --no-pager log", LISTAN),
    ("git-push", "git push", LISTAN),
    ("git-checkout", "git checkout x", LISTAN),
    ("git-reset", "git reset --hard", LISTAN),
    ("git-config", "git config core.pager x", LISTAN),
    ("git-rebase", "git rebase main", LISTAN),
    ("git-stash", "git stash", LISTAN),
    ("git-clean", "git clean -fd", LISTAN),
    ("git-rm", "git rm x", LISTAN),
    ("git-restore", "git restore x", LISTAN),
    ("git-merge", "git merge x", LISTAN),
    ("git-apply", "git apply x", LISTAN),
    ("git-grep", "git grep x", LISTAN),
    ("git-rev-parse", "git rev-parse HEAD", LISTAN),
    ("git-tag", "git tag", LISTAN),
    # Regel 6: git-tillägg som skriver filer, kör program eller öppnar ett fönster för att skriva.
    ("git-diff-output", "git diff --output=x", GIT_TILLAGG),
    ("git-diff-output-separat", "git diff --output x", GIT_TILLAGG),
    ("git-diff-output-forkortat", "git diff --out=x", GIT_TILLAGG),
    ("git-log-output", "git log --output=x", GIT_TILLAGG),
    ("git-show-output", "git show --output=x", GIT_TILLAGG),
    ("git-diff-c", "git diff -c", GIT_TILLAGG),
    ("git-log-c", "git log -c", GIT_TILLAGG),
    ("git-commit-c", "git commit -c HEAD", GIT_TILLAGG),
    ("git-diff-ext-diff", "git diff --ext-diff", GIT_TILLAGG),
    ("git-diff-ext-forkortat", "git diff --ext", GIT_TILLAGG),
    ("git-diff-textconv", "git diff --textconv", GIT_TILLAGG),
    ("git-log-exec-path", "git log --exec-path", GIT_TILLAGG),
    ("git-diff-no-index", "git diff --no-index a b", GIT_TILLAGG),
    ("git-diff-orderfile", "git diff -Oordning", GIT_TILLAGG),
    ("git-diff-git-dir", "git diff --git-dir=x", GIT_TILLAGG),
    ("git-status-work-tree", "git status --work-tree=x", GIT_TILLAGG),
    ("git-commit-e", "git commit -e", GIT_TILLAGG),
    ("git-commit-edit", "git commit --edit", GIT_TILLAGG),
    ("git-commit-ve", "git commit -ve", GIT_TILLAGG),
    ("git-commit-m-och-e", "git commit -m x -e", GIT_TILLAGG),
    ("git-commit-interactive", "git commit --interactive", GIT_TILLAGG),
    ("git-commit-p", "git commit -p", GIT_TILLAGG),
    ("git-commit-template", "git commit --template=x", GIT_TILLAGG),
    ("git-add-p", "git add -p", GIT_TILLAGG),
    ("git-add-i", "git add -i", GIT_TILLAGG),
    ("git-add-e", "git add -e", GIT_TILLAGG),
    ("git-add-interactive", "git add --interactive", GIT_TILLAGG),
    ("git-add-patch", "git add --patch", GIT_TILLAGG),
    ("git-archive-remote", "git archive --remote=x HEAD", GIT_TILLAGG),
    ("git-archive-exec", "git archive --exec=x HEAD", GIT_TILLAGG),
    ("git-archive-add-file", "git archive --add-file=x HEAD", GIT_TILLAGG),
    ("git-archive-output-forkortat", "git archive --out=<T>/x.tar HEAD", GIT_TILLAGG),
    # git archive och git commit -F: målet och filen.
    ("git-archive-o-projektet", "git archive -o kopia.tar HEAD", TILLFALLIG),
    ("git-archive-output-projektet", "git archive --output=kopia.tar HEAD", TILLFALLIG),
    ("git-archive-o-projektet-hel", "git archive -o <P>/kopia.tar HEAD", TILLFALLIG),
    ("git-archive-o-ut-ur-tillfallig", "git archive -o <T>/../x.tar HEAD", TILLFALLIG),
    ("git-commit-F-utanfor", "git commit -F /etc/passwd", UTANFOR),
    ("git-commit-file-utanfor", "git commit --file=../x", UTANFOR),
    # find bara för att söka.
    ("find-exec", "find . -exec rm '{}' +", FIND),
    ("find-execdir", "find . -execdir rm '{}' +", FIND),
    ("find-ok", "find . -ok rm '{}' +", FIND),
    ("find-okdir", "find . -okdir rm '{}' +", FIND),
    ("find-delete", "find . -delete", FIND),
    ("find-namn-delete", "find . -name x -delete", FIND),
    ("find-fprint", "find . -fprint x", FIND),
    ("find-fprint0", "find . -fprint0 x", FIND),
    ("find-fprintf", "find . -fprintf x '%p'", FIND),
    ("find-fls", "find . -fls x", FIND),
    ("find-roten", "find / -name x", UTANFOR),
    ("find-ovanfor", "find .. -name x", UTANFOR),
    ("find-ovanfor-tillfallig", "find <T>/.. -name x", UTANFOR),
    # mkdir bara i den tillfälliga mappen.
    ("mkdir-projektet", "mkdir ny", TILLFALLIG),
    ("mkdir-projektet-hel", "mkdir <P>/ny", TILLFALLIG),
    ("mkdir-p-projektet", "mkdir -p scripts/ny", TILLFALLIG),
    ("mkdir-ut-ur-tillfallig", "mkdir <T>/../ny", TILLFALLIG),
    ("mkdir-m", "mkdir -m 777 <T>/x", TILLAGG),
    # cp -R bara till den tillfälliga mappen, och bara från projektet eller den tillfälliga mappen.
    ("cp-projektet", "cp -R scripts ny", TILLFALLIG),
    ("cp-projektet-hel", "cp -R scripts <P>/ny", TILLFALLIG),
    ("cp-tillbaka", "cp -R <T>/kopia scripts", TILLFALLIG),
    ("cp-fran-etc", "cp -R /etc <T>/etc", UTANFOR),
    ("cp-fran-ovanfor", "cp -R .. <T>/x", UTANFOR),
    ("cp-utan-R", "cp SPEC.md <T>/x", "cp -R"),
    ("cp-L", "cp -RL scripts <T>/x", TILLAGG),
    # tar bara med mål i den tillfälliga mappen.
    ("tar-x-utan-C", "tar -xf <T>/x.tar", TAR),
    ("tar-x-C-projektet", "tar -xf <T>/x.tar -C .", TAR),
    ("tar-x-C-scripts", "tar -xf <T>/x.tar -C scripts", TAR),
    ("tar-c-projektet", "tar -cf x.tar scripts", TAR),
    ("tar-c-projektet-hel", "tar -cf <P>/x.tar scripts", TAR),
    ("tar-utan-streck", "tar xf <T>/x.tar -C <T>", TAR),
    ("tar-P", "tar -xPf <T>/x.tar -C <T>", TAR),
    ("tar-s", "tar -xf <T>/x.tar -C <T> -s ',a,b,'", TAR),
    ("tar-compress-program", "tar --use-compress-program=sh -xf <T>/x.tar -C <T>", TAR),
    ("tar-t-utanfor", "tar -tf /etc/x.tar", TAR),
    ("tar-utan-f", "tar -x -C <T>", TAR),
    ("tar-f-streck", "tar -xf - -C <T>", TAR),
    ("tar-c-fran-etc", "tar -cf <T>/x.tar /etc", TAR),
    ("tar-c-C-roten", "tar -cf <T>/x.tar -C / etc", TAR),
    # pytest bara i de två formerna i 7.1, med de tillägg som 7.1 tillåter.
    ("python-skript", f"'{NY_PYTHON}' x.py", PYTEST_FORM),
    ("python-c", f"'{NY_PYTHON}' -c 'print(1)'", PYTEST_FORM),
    ("pytest-utan-B", f"'{NY_PYTHON}' -m pytest -p no:cacheprovider scripts/tests", PYTEST_FORM),
    ("pytest-utan-cache", f"'{NY_PYTHON}' -B -m pytest scripts/tests", PYTEST_FORM),
    ("pip", f"'{NY_PYTHON}' -B -m pip install x", PYTEST_FORM),
    # Hugos beslut 2026-10-28 om vakten, beslut 1: projektets gamla .venv står inte längre på listan.
    ("gamla-venv", f"{GAMLA_PYTEST} -q scripts/tests", LISTAN),
    ("gamla-venv-kopia", f"{GAMLA_PYTEST} <T>/kopia/scripts/tests", LISTAN),
    ("pytest-x", f"{PYTEST} -x scripts/tests", PYTEST_FORM),
    ("pytest-s", f"{PYTEST} -s scripts/tests", PYTEST_FORM),
    ("pytest-lf", f"{PYTEST} --lf scripts/tests", PYTEST_FORM),
    ("pytest-cache-clear", f"{PYTEST} --cache-clear scripts/tests", PYTEST_FORM),
    ("pytest-p-annat", f"{PYTEST} -p xdist scripts/tests", PYTEST_FORM),
    ("pytest-p-efter-randomly", f"{PYTEST} -p no:randomly -p annat scripts/tests", PYTEST_FORM),
    ("pytest-rootdir", f"{PYTEST} --rootdir=<T> scripts/tests", PYTEST_FORM),
    ("pytest-c", f"{PYTEST} -c <T>/pytest.ini scripts/tests", PYTEST_FORM),
    ("pytest-o", f"{PYTEST} -o addopts=x scripts/tests", PYTEST_FORM),
    ("pytest-basetemp", f"{PYTEST} --basetemp=scripts scripts/tests", PYTEST_FORM),
    ("pytest-junitxml", f"{PYTEST} --junitxml=x.xml scripts/tests", PYTEST_FORM),
    ("pytest-tb-okand", f"{PYTEST} --tb=ond scripts/tests", PYTEST_FORM),
    ("pytest-mal-scripts", f"{PYTEST} scripts", PYTEST_FORM),
    ("pytest-mal-testfil-i-projektet", f"{PYTEST} scripts/tests/test_belopp.py", PYTEST_FORM),
    ("pytest-mal-etc", f"{PYTEST} /etc", PYTEST_FORM),
    ("pytest-mal-ut-ur-tillfallig", f"{PYTEST} <T>/../x", PYTEST_FORM),
    ("pytest-tva-mal", f"{PYTEST} scripts/tests <T>/kopia/scripts/tests", PYTEST_FORM),
    ("pytest-inget-mal", PYTEST, PYTEST_FORM),
    # Läsande kommandon bara i projektet och i den tillfälliga mappen.
    ("cat-etc", "cat /etc/passwd", UTANFOR),
    ("cat-ovanfor", "cat ../annat/x", UTANFOR),
    ("ls-users", "ls /Users", UTANFOR),
    ("ls-ovanfor", "ls ..", UTANFOR),
    ("grep-roten", "grep -r x /", UTANFOR),
    ("grep-efter-streck", "grep -e x -- /etc/hosts", UTANFOR),
    ("grep-include-ovanfor", "grep --include=../x y .", UTANFOR),
    ("head-ut-ur-tillfallig", "head <T>/../x", UTANFOR),
    ("tail-logg", "tail -n 5 /var/log/system.log", UTANFOR),
    ("diff-etc", "diff SPEC.md /etc/hosts", UTANFOR),
    ("wc-etc", "wc /etc/hosts", UTANFOR),
    ("sort-etc", "sort -- /etc/hosts", UTANFOR),
    # Tillägg till läsande kommandon som skriver filer, kör program eller läser andra filer.
    ("sort-o", "sort -o x SPEC.md", TILLAGG),
    ("sort-o-ihop", "sort -ro x SPEC.md", TILLAGG),
    ("sort-output", "sort --output=x SPEC.md", TILLAGG),
    ("sort-output-forkortat", "sort --out=x SPEC.md", TILLAGG),
    ("sort-compress-program", "sort --compress-program=sh SPEC.md", TILLAGG),
    ("sort-T", "sort -T <T> SPEC.md", TILLAGG),
    ("grep-f", "grep -f monster.txt SPEC.md", TILLAGG),
    ("grep-file", "grep --file=x SPEC.md", TILLAGG),
    ("sokvag-i-tillagg", "ls -/etc", TILLAGG),
]


@pytest.mark.parametrize(
    "kommando,nyckel", [(k, n) for _, k, n in STOPPAS], ids=[i for i, _, _ in STOPPAS]
)
def test_omvagar_stoppas(vakt, mappar, kommando, nyckel):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None, f"släpptes igenom: {kommando!r}"
    assert nyckel in fel, f"fel skäl för {kommando!r}: {fel}"


ANDRA_VERKTYG = [
    "PowerShell",
    "Monitor",
    "mcp__terminal__run_in_terminal",
    "mcp__abc__COMPOSIO_REMOTE_BASH_TOOL",
    "mcp__abc__exec",
    "mcp__Claude_Browser__preview_start",
    "mcp__Claude_Code_iOS_Simulator__build",
    "mcp__ccd_host__sync_with_base_branch",
]


@pytest.mark.parametrize("verktyg", ANDRA_VERKTYG)
def test_andra_verktyg_som_kor_kommandon_stoppas(vakt, mappar, verktyg):
    # Regel 2: bara Bash får köra kommandon, också när kommandot står på listan.
    fel = _bedom(vakt, mappar, "git status", verktyg)
    assert fel is not None and VERKTYG in fel


def test_sudo_stoppas_ocksa_i_andra_verktyg(vakt, mappar):
    fel = _bedom(vakt, mappar, "sudo ls", "Monitor")
    assert fel is not None and SUDO in fel


def test_symbolisk_lank_ut_ur_projektet_stoppas(vakt, mappar):
    # En länk i projektet som pekar ut ur det: vakten följer länken och ser vart den går.
    os.symlink(mappar["hem"], os.path.join(mappar["projekt"], "lank"))
    fel = _bedom(vakt, mappar, "cat lank/hemligt.txt")
    assert fel is not None and UTANFOR in fel


# ---------------------------------------------------------------------------------------------
# Mappen där kommandot körs, och regel 3: ingen mapp undantas (Hugos beslut 8).

def test_kommando_i_annan_mapp_an_projektet_stoppas(vakt, mappar):
    indata = _indata(mappar, "git status")
    indata["cwd"] = mappar["projekt"] + "/scripts"
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "annan mapp" in fel


def test_kommando_utan_mapp_stoppas(vakt, mappar):
    indata = _indata(mappar, "git status")
    del indata["cwd"]
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "indata" in fel


def test_utan_projektmapp_stoppas_allt(vakt, mappar):
    fel = vakt.bedom(_indata(mappar, "git status"), None, mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "CLAUDE_PROJECT_DIR" in fel


@pytest.mark.parametrize("vilken", ["hem", "ovanfor-hem"])
def test_session_i_hemmappen_eller_ovanfor_stoppas(vakt, mappar, vilken):
    # Då skulle "projektet" vara hela hemmappen, och läsande kommandon nå allt i den.
    mapp = mappar["hem"] if vilken == "hem" else os.path.dirname(mappar["hem"])
    indata = _indata(mappar, "ls")
    indata["cwd"] = mapp
    fel = vakt.bedom(indata, mapp, mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "hemmappen" in fel


@pytest.mark.parametrize(
    "kommando,nyckel",
    [("ls; rm x", IHOP), ("rm x", LISTAN), ("sudo ls", SUDO), ("cat <P>/SPEC.md", UTANFOR)],
)
def test_samma_regler_i_en_annan_mapp(vakt, mappar, kommando, nyckel):
    # En session i en annan mapp under ~/VERA får samma lista, och når inte Veras projekt.
    annan = os.path.join(mappar["hem"], "varumarke")
    os.mkdir(annan)
    indata = _indata(mappar, kommando)
    indata["cwd"] = annan
    fel = vakt.bedom(indata, annan, mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and nyckel in fel


def test_utan_tillfallig_mapp_stoppas_mkdir_men_inte_cat(vakt, mappar):
    indata = _indata(mappar, "mkdir <T>/kopia")
    del indata["scratchpad_dir"]
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and TILLFALLIG in fel
    indata = _indata(mappar, "cat SPEC.md")
    del indata["scratchpad_dir"]
    assert vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG) is None


@pytest.mark.parametrize("vilken", ["i-projektet", "hemmappen", "roten"])
def test_tillfallig_mapp_som_inte_ar_tillfallig_godtas_inte(vakt, mappar, vilken):
    # En "tillfällig mapp" inne i projektet, eller som rymmer hemmappen, skulle öppna allt.
    mapp = {
        "i-projektet": os.path.join(mappar["projekt"], "tmp"),
        "hemmappen": mappar["hem"],
        "roten": "/",
    }[vilken]
    indata = _indata(mappar, "mkdir " + os.path.join(mapp, "x"))
    indata["scratchpad_dir"] = mapp
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and TILLFALLIG in fel


TRASIG_INDATA = [
    ("inte-ett-objekt", ["lista"]),
    ("utan-verktyg", {"tool_input": {"command": "ls"}, "cwd": "x"}),
    ("verktyg-inte-text", {"tool_name": 5, "tool_input": {}, "cwd": "x"}),
    ("utan-tool-input", {"tool_name": "Bash", "cwd": "x"}),
    ("tool-input-inte-objekt", {"tool_name": "Bash", "tool_input": "ls", "cwd": "x"}),
    ("utan-command", {"tool_name": "Bash", "tool_input": {}, "cwd": "x"}),
    ("command-inte-text", {"tool_name": "Bash", "tool_input": {"command": ["ls"]}, "cwd": "x"}),
]


@pytest.mark.parametrize("indata", [i for _, i in TRASIG_INDATA], ids=[n for n, _ in TRASIG_INDATA])
def test_trasig_indata_stoppas(vakt, mappar, indata):
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
    assert fel is not None and "indata" in fel


# ---------------------------------------------------------------------------------------------
# PATH-regeln (Hugos beslut 2026-10-28, beslut 1). Vakten tillåter ett kommando bara om programmet det
# pekar på ligger i en mapp som ägs av systemet (root) och som varken gruppen eller andra kan skriva i.
# Samma krav gäller alla mappar ovanför, och filen själv. Kan vakten inte säkert avgöra vilken fil som
# körs, stoppas kommandot. Kommandon som ändrar PATH stoppas.

def _lagg_program(mapp, namn):
    """Lägger ett litet program med namnet namn i mappen, som användaren (inte systemet) äger."""
    os.makedirs(mapp, exist_ok=True)
    fil = os.path.join(mapp, namn)
    with open(fil, "w", encoding="utf-8") as ut:
        ut.write("#!/bin/sh\nexit 0\n")
    os.chmod(fil, 0o755)
    return fil


# Ett kommando per namn på listan i SPEC 7.1 (utom .venv/bin/python, som har en egen sökväg).
LISTANS_PROGRAM = [
    ("git", "git status"),
    ("ls", "ls"),
    ("cat", "cat SPEC.md"),
    ("head", "head SPEC.md"),
    ("tail", "tail SPEC.md"),
    ("grep", "grep -n x SPEC.md"),
    ("diff", "diff SPEC.md SPEC.md"),
    ("find", "find scripts -type f"),
    ("wc", "wc -l SPEC.md"),
    ("sort", "sort SPEC.md"),
    ("mkdir", "mkdir <T>/kopia"),
    ("cp", "cp -R scripts <T>/kopia"),
    ("tar", "tar -tf <T>/paket.tar"),
]


def test_systemets_program_ags_av_systemet():
    # Förutsättning för testerna nedan: programmen i SYSTEMETS_SOKVAG ägs av root och går inte att
    # skriva i för gruppen eller andra.
    for namn, _ in LISTANS_PROGRAM:
        fil = next(os.path.join(m, namn) for m in SYSTEMETS_SOKVAG.split(":") if os.path.isfile(os.path.join(m, namn)))
        info = os.stat(fil)
        assert info.st_uid == 0 and not info.st_mode & 0o022, fil


@pytest.mark.parametrize("kommando", [k for _, k in LISTANS_PROGRAM], ids=[n for n, _ in LISTANS_PROGRAM])
def test_program_i_en_rotmapp_gar_igenom(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando, sokvag=SYSTEMETS_SOKVAG) is None


@pytest.mark.parametrize("namn,kommando", LISTANS_PROGRAM, ids=[n for n, _ in LISTANS_PROGRAM])
def test_program_med_tillatet_namn_i_en_mapp_som_anvandaren_ager_stoppas(vakt, mappar, tmp_path, namn, kommando):
    # Som node, npm och npx i Hugos nvm-mapp: mappen står först i PATH och ägs av Hugo.
    egen = str(tmp_path / "egen-bin")
    fil = _lagg_program(egen, namn)
    fel = _bedom(vakt, mappar, kommando, sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and fil in fel, fel


def test_lank_i_en_mapp_som_anvandaren_ager_stoppas_aven_om_den_leder_till_systemet(vakt, mappar, tmp_path):
    # Länken pekar på systemets git, men själva länken kan bytas ut av användaren.
    egen = tmp_path / "egen-bin"
    egen.mkdir()
    os.symlink("/usr/bin/git", egen / "git")
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel, fel


def test_forsta_traffen_i_path_avgor(vakt, mappar, tmp_path):
    # Skalet kör det första programmet med namnet i PATH. Ligger systemets git först går det igenom,
    # ligger användarens git först stoppas det.
    egen = str(tmp_path / "egen-bin")
    _lagg_program(egen, "git")
    assert _bedom(vakt, mappar, "git status", sokvag=f"{SYSTEMETS_SOKVAG}:{egen}") is None
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel


def test_fil_som_inte_far_koras_hoppas_over_som_skalet_gor(vakt, mappar, tmp_path, rotagd):
    # En fil med namnet som inte är körbar hoppar skalet över, och letar vidare i PATH. Mappen före
    # programmet ska ägas av root (beslut 2), så testet låtsas att den gör det.
    egen = tmp_path / "egen-bin"
    egen.mkdir()
    (egen / "git").write_text("inte ett program\n", encoding="utf-8")
    os.chmod(egen / "git", 0o644)
    rotagd(egen)
    assert _bedom(vakt, mappar, "git status", sokvag=f"{egen}:{SYSTEMETS_SOKVAG}") is None


@pytest.mark.parametrize(
    "sokvag",
    ["/finns-inte/bin", "/finns-inte/bin:/finns-inte/heller"],
    ids=["en-mapp", "tva-mappar"],
)
def test_program_i_en_mapp_som_inte_finns_stoppas(vakt, mappar, sokvag):
    fel = _bedom(vakt, mappar, "git status", sokvag=sokvag)
    assert fel is not None and OSAKER in fel, fel


def test_python_som_inte_finns_stoppas(vakt, mappar, monkeypatch, tmp_path):
    # Python på den nya platsen finns inte (till exempel före installationen).
    saknas = str(tmp_path / "finns-inte" / "bin" / "python")
    monkeypatch.setattr(vakt, "PYTHON", saknas)
    fel = _bedom(vakt, mappar, f"{PYTEST.replace(NY_PYTHON, saknas)} -q scripts/tests")
    assert fel is not None and OSAKER in fel, fel


@pytest.mark.parametrize(
    "sokvag",
    [None, "", ":/usr/bin:/bin", ".:/usr/bin:/bin", "bin:/usr/bin:/bin", "~/bin:/usr/bin:/bin"],
    ids=["saknas", "tom", "tom-mapp-forst", "punkt", "relativ", "tilde"],
)
def test_path_som_inte_gar_att_lita_pa_stoppas(vakt, mappar, sokvag):
    # En tom eller relativ mapp i PATH före programmet betyder arbetsmappen eller en mapp i förhållande
    # till den. Då kan vakten inte säkert avgöra vilken fil som körs.
    fel = _bedom(vakt, mappar, "git status", sokvag=sokvag)
    assert fel is not None and OSAKER in fel, fel


ANDRAR_PATH_KOMMANDON = [
    ("tilldelning", "PATH=/tmp git status"),
    ("tilldelning-citat", "PATH='/tmp' git status"),
    ("tilldelning-tom", "PATH= git status"),
    ("tilldelning-ensam", "PATH=/tmp"),
    ("tilldelning-lagg-till", "PATH+=/tmp git status"),
    ("tilldelning-zsh-path", "path=/tmp git status"),
    ("tilldelning-efter-annan", "X=1 PATH=/tmp git status"),
    ("export", "export PATH=/tmp"),
    ("export-namn", "export PATH"),
    ("export-citat", "export 'PATH=/tmp'"),
    ("env", "env PATH=/tmp git status"),
    ("env-i", "env -i PATH=/tmp git status"),
    ("typeset", "typeset PATH=/tmp"),
    ("declare", "declare -x PATH=/tmp"),
    ("readonly", "readonly PATH"),
    ("local", "local PATH=/tmp"),
    ("unset", "unset PATH"),
]


@pytest.mark.parametrize(
    "kommando", [k for _, k in ANDRAR_PATH_KOMMANDON], ids=[i for i, _ in ANDRAR_PATH_KOMMANDON]
)
def test_kommandon_som_andrar_path_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and ANDRAR_PATH in fel, fel


@pytest.mark.parametrize("kommando", ["grep -n PATH SPEC.md", "grep -n 'PATH=' SPEC.md", "git log --grep=PATH"])
def test_att_soka_efter_ordet_path_gar_igenom(vakt, mappar, kommando):
    # Bara kommandon som ändrar PATH stoppas, inte en sökning efter ordet.
    assert _bedom(vakt, mappar, kommando) is None


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-10-28 om vakten, beslut 1–4 (GRANSKNING.md, "Granskning 11 – plan för Q1").
#
# Ett test kan inte skapa en mapp eller fil som ägs av root. Fixturen rotagd låtsas därför att de
# sökvägar som testet anger ägs säkert av root, genom att byta ut vaktens _sakert_agd. Allt annat prövas
# som vanligt, så en fil eller mapp som testet inte anger är fortfarande användarens.

@pytest.fixture
def rotagd(vakt, monkeypatch):
    sakra = set()
    vanlig = vakt._sakert_agd
    monkeypatch.setattr(vakt, "_sakert_agd", lambda sokvag: sokvag in sakra or vanlig(sokvag))

    def lagg_till(sokvag, mapparna_ovanfor=True):
        for form in {os.path.normpath(str(sokvag)), os.path.realpath(str(sokvag))}:
            sakra.add(form)
            while mapparna_ovanfor and form != os.path.dirname(form):
                form = os.path.dirname(form)
                sakra.add(form)

    return lagg_till


@pytest.fixture
def ny_python(vakt, monkeypatch, tmp_path):
    """En Python i en mapp i testet, i stället för den nya platsen i /Library (som testet inte kan skapa)."""
    fil = _lagg_program(str(tmp_path / "rot" / "vera" / "venv" / "bin"), "python")
    monkeypatch.setattr(vakt, "PYTHON", fil)
    return fil


def test_rotagd_galler_bara_det_testet_anger(vakt, tmp_path, rotagd):
    # Förutsättning för testerna nedan: utan rotagd är en mapp i testet användarens.
    mapp = tmp_path / "rot"
    mapp.mkdir()
    assert not vakt._saker_plats(str(mapp))
    rotagd(mapp)
    assert vakt._saker_plats(str(mapp))
    assert not vakt._saker_plats(str(_lagg_program(str(mapp), "git")))


# Beslut 1 (alternativ c): .venv flyttas till en mapp som root äger. Pytest-kommandona i listan pekar dit.

def _spec_tabellen():
    text = SPEC.read_text(encoding="utf-8").split("### 7.1 Fast kommandolista", 1)[1].split("\n## ", 1)[0]
    return [rad for rad in text.splitlines() if rad.startswith("| `")]


def test_beslut_1_listan_och_vakten_pekar_pa_python_i_en_mapp_som_root_ager(vakt):
    assert vakt.PYTHON == NY_PYTHON
    assert NY_PYTHON.startswith("/Library/Application Support/ClaudeCode/")
    pytest_rader = [rad for rad in _spec_tabellen() if "pytest" in rad]
    assert len(pytest_rader) == 2
    for rad in pytest_rader:
        assert rad.startswith(f"| `{PYTEST} "), rad
    assert not any(".venv/bin/python" in rad for rad in _spec_tabellen())


@pytest.mark.parametrize("kommando", [k for _, k in TILLATNA_PYTEST], ids=[i for i, _ in TILLATNA_PYTEST])
def test_beslut_1_pytest_formerna_gar_igenom_med_python_i_en_mapp_som_root_ager(
    vakt, mappar, ny_python, rotagd, kommando
):
    rotagd(ny_python)
    assert _bedom(vakt, mappar, kommando.replace(NY_PYTHON, ny_python)) is None


@pytest.mark.parametrize("kommando", [k for _, k in TILLATNA_PYTEST], ids=[i for i, _ in TILLATNA_PYTEST])
def test_beslut_1_pytest_formerna_stoppas_med_python_i_en_mapp_som_anvandaren_ager(
    vakt, mappar, ny_python, kommando
):
    # PATH-regeln prövas sist. Att felet kommer från den visar att reglerna 1–6 godtar formen.
    fel = _bedom(vakt, mappar, kommando.replace(NY_PYTHON, ny_python))
    assert fel is not None and PLATS in fel and ny_python in fel, fel


def test_beslut_1_gamla_venv_i_projektet_stoppas(vakt, mappar):
    # Också om den finns: den står inte längre på listan.
    _lagg_program(os.path.join(mappar["projekt"], ".venv", "bin"), "python")
    fel = _bedom(vakt, mappar, f"{GAMLA_PYTEST} -q scripts/tests")
    assert fel is not None and LISTAN in fel, fel


VENV_SKAPA = f'sudo /usr/bin/python3 -m venv "{NY_VENV}"'
VENV_PIP = (
    f'sudo "{NY_PYTHON}" -m pip install --only-binary \':all:\' --no-cache-dir '
    "-r ~/VERA/agent/requirements.txt"
)
VENV_AGARE = f'sudo chown -R root:wheel "{NY_VENV}"'
VENV_RATTIGHETER = f'sudo chmod -R go-w "{NY_VENV}"'
VENV_LS = f'ls -ld "{NY_VENV}" "{NY_VENV}/bin" "{NY_PYTHON}"'


def test_beslut_1_installera_skapar_python_pa_den_nya_platsen():
    # Hugo skapar mappen och installerar paketen själv, med sitt lösenord. Mappen och allt i den ska ägas
    # av root:wheel och inte gå att skriva i för gruppen eller andra. Paketen installeras bara färdigbyggda
    # (--only-binary), så att inget installationsskript körs som administratör, och utan cache, så att pip
    # inte lämnar filer som root äger i Hugos hemmapp.
    text, rader = _installationskommandon()
    plats = {k: rader.index(k) for k in (VENV_SKAPA, VENV_PIP, VENV_AGARE, VENV_RATTIGHETER, VENV_LS)}
    assert plats[VENV_SKAPA] < plats[VENV_PIP] < plats[VENV_AGARE] < plats[VENV_RATTIGHETER] < plats[VENV_LS]
    # Efter att vakten är på plats och låst, före inställningarna, och kontrolleras med ls -ld efteråt.
    vakten_last = max(i for i, r in enumerate(rader) if r.startswith("sudo chmod 644") and INSTALLERAD_VAKT in r)
    installningarna = next(i for i, r in enumerate(rader) if r.startswith("sudo cp -i"))
    assert vakten_last < plats[VENV_SKAPA] and plats[VENV_RATTIGHETER] < installningarna
    assert plats[VENV_LS] > max(i for i, r in enumerate(rader) if r == KEDJAN)
    # Testsviten med den nya platsen prövas i kontrollen efter installationen.
    assert PYTEST in _kontrollen()


# Beslut 2: varje mapp i PATH före programmet ska ägas av root.

def test_beslut_2_mapp_som_anvandaren_ager_fore_programmet_stoppas(vakt, mappar, tmp_path):
    # Mappen är tom, och git hittas i /usr/bin. Men ett git som läggs i mappen senare skulle köras i
    # stället, och om skalet och vakten har olika PATH kan skalet hitta något där som vakten inte såg.
    egen = tmp_path / "egen-bin"
    egen.mkdir()
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel and str(egen) in fel, fel


def test_beslut_2_mapp_som_inte_finns_fore_programmet_stoppas(vakt, mappar):
    fel = _bedom(vakt, mappar, "git status", sokvag=f"/finns-inte/bin:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel, fel


def test_beslut_2_mapp_under_en_mapp_som_anvandaren_ager_fore_programmet_stoppas(vakt, mappar, tmp_path, rotagd):
    # Mappen själv låtsas ägas av root, men inte mappen ovanför den: då kan mappen bytas ut.
    egen = tmp_path / "egen" / "bin"
    egen.mkdir(parents=True)
    rotagd(egen, mapparna_ovanfor=False)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel, fel


def test_beslut_2_rotmappar_fore_programmet_gar_igenom(vakt, mappar):
    # /usr/sbin ägs av root och står före /usr/bin, där git ligger.
    assert _bedom(vakt, mappar, "git status", sokvag="/usr/sbin:/usr/bin:/bin") is None


def test_beslut_2_hugos_path_med_nvm_forst_stoppas_och_med_nvm_sist_gar_igenom(vakt, mappar, tmp_path):
    # Som Hugos PATH 2026-10-28: nvm-mappen (som Hugo äger, med node, npm och npx) står först. Flyttas den
    # efter systemets mappar går kommandona igenom (INSTALLERA.md beskriver hur).
    nvm = str(tmp_path / ".nvm" / "versions" / "node" / "v24.18.0" / "bin")
    for namn in ("node", "npm", "npx"):
        _lagg_program(nvm, namn)
    for _, kommando in LISTANS_PROGRAM:
        fel = _bedom(vakt, mappar, kommando, sokvag=f"{nvm}:{SYSTEMETS_SOKVAG}")
        assert fel is not None and FORE_PROGRAMMET in fel and nvm in fel, (kommando, fel)
        assert _bedom(vakt, mappar, kommando, sokvag=f"{SYSTEMETS_SOKVAG}:{nvm}") is None, kommando


def test_beslut_2_programmet_stoppar_nar_en_mapp_fore_programmet_ags_av_anvandaren(mappar, tmp_path):
    # Samma sak som Claude Code kör det, med PATH från vaktens miljö.
    egen = tmp_path / "egen-bin"
    egen.mkdir()
    svar = _kor_programmet(mappar, _indata(mappar, "git status"), sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert svar.returncode == 2 and FORE_PROGRAMMET in svar.stderr.decode("utf-8")


@pytest.mark.parametrize("namn,kommando", LISTANS_PROGRAM, ids=[n for n, _ in LISTANS_PROGRAM])
def test_program_i_en_mapp_som_hugo_ager_stoppas_nar_mappen_ligger_tidigare_i_path(
    vakt, mappar, tmp_path, namn, kommando
):
    # Uppdragets extra test: programmet finns både i systemets mapp och i en mapp som användaren äger, och
    # användarens mapp står tidigare i PATH. Skalet skulle köra användarens program, och det stoppas.
    egen = str(tmp_path / "egen-bin")
    fil = _lagg_program(egen, namn)
    assert _bedom(vakt, mappar, kommando, sokvag=f"{SYSTEMETS_SOKVAG}:{egen}") is None
    fel = _bedom(vakt, mappar, kommando, sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and fil in fel, fel


# Beslut 3: också filen själv och målet för en länk ska ägas av root.

def test_beslut_3_fil_som_anvandaren_ager_i_en_rotmapp_stoppas(vakt, mappar, tmp_path, rotagd):
    rot = tmp_path / "rot-bin"
    fil = _lagg_program(str(rot), "git")
    rotagd(rot)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and fil in fel, fel


def test_beslut_3_fil_som_root_ager_i_en_rotmapp_gar_igenom(vakt, mappar, tmp_path, rotagd):
    # Motprov till testet ovan: när också filen ägs av root går kommandot igenom.
    rot = tmp_path / "rot-bin"
    fil = _lagg_program(str(rot), "git")
    rotagd(fil)
    assert _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}") is None


def test_beslut_3_lank_i_en_rotmapp_till_en_fil_som_anvandaren_ager_stoppas(vakt, mappar, tmp_path, rotagd):
    egen = _lagg_program(str(tmp_path / "egen-bin"), "git")
    rot = tmp_path / "rot-bin"
    rot.mkdir()
    os.symlink(egen, rot / "git")
    rotagd(rot)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and f"länken leder till {egen}" in fel, fel


def test_beslut_3_lank_i_en_rotmapp_till_en_fil_i_en_mapp_som_anvandaren_ager_stoppas(
    vakt, mappar, tmp_path, rotagd
):
    # Filen dit länken leder låtsas ägas av root, men inte mappen den ligger i.
    egen = _lagg_program(str(tmp_path / "egen-bin"), "git")
    rotagd(egen, mapparna_ovanfor=False)
    rot = tmp_path / "rot-bin"
    rot.mkdir()
    os.symlink(egen, rot / "git")
    rotagd(rot)
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel, fel


def test_beslut_3_lank_i_en_rotmapp_till_systemets_program_gar_igenom(vakt, mappar, tmp_path, rotagd):
    rot = tmp_path / "rot-bin"
    rot.mkdir()
    os.symlink("/usr/bin/git", rot / "git")
    rotagd(rot)
    assert _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}") is None


# Beslut 4: den strängaste tolkningen. Varje källa på raden Setting sources i /status som inte är den
# låsta filen stoppar installationen.

ANNAN_KALLA = "Varje annan källa på raden stoppar installationen"


def test_beslut_4_varje_annan_kalla_i_status_stoppar_installationen():
    text = INSTALLERA.read_text(encoding="utf-8")
    forsta_steget = _en_rad(_steg(text)[0][1])
    efterat = _en_rad(text.split("## Efteråt", 1)[1].split("\n## ", 1)[0])
    kontroll_1 = _en_rad(_kontrollen().split("\n2. ", 1)[0])
    for stalle in (forsta_steget, efterat, kontroll_1, _spec_7_1()):
        assert "Enterprise managed settings (file)" in stalle
        assert ANNAN_KALLA in stalle
        assert "Hugos beslut 2026-10-28 om vakten, beslut 4" in stalle
    # Också Hugos och projektets egna inställningar räknas, inte bara låsta källor från claude.ai.
    for stalle in (efterat, kontroll_1):
        assert "User settings" in stalle and "Project settings" in stalle


# ---------------------------------------------------------------------------------------------
# Programmet: så som Claude Code kör det, med datorns egen Python och -I.

def _kor_programmet(mappar, indata, fil=VAKTEN, projektmapp=True, cwd=None, sokvag=SYSTEMETS_SOKVAG):
    miljo = {} if sokvag is None else {"PATH": sokvag}
    if projektmapp:
        miljo["CLAUDE_PROJECT_DIR"] = mappar["projekt"]
    if not isinstance(indata, bytes):
        indata = json.dumps(indata).encode("utf-8")
    return subprocess.run(
        [SYSTEMETS_PYTHON, "-I", str(fil)],
        input=indata,
        capture_output=True,
        env=miljo,
        cwd=cwd or mappar["projekt"],
        timeout=10,
    )


def test_programmet_slapper_igenom_med_kod_0_och_ingen_utskrift(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "git status"))
    assert (svar.returncode, svar.stdout, svar.stderr) == (0, b"", b"")


def test_programmet_stoppar_med_kod_2_och_fel_pa_svenska(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "ls; rm x"))
    assert svar.returncode == 2
    assert svar.stdout == b""
    fel = svar.stderr.decode("utf-8")
    assert fel.startswith("Stoppat av vakten")
    assert "ett kommando i taget" in fel and "SPEC 7.1" in fel


def test_programmet_stoppar_sudo(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "sudo ls"))
    assert svar.returncode == 2 and SUDO in svar.stderr.decode("utf-8")


@pytest.mark.parametrize(
    "indata",
    [b"", b"inte json", b"[]", b"\xff\xfe", b'{"tool_name": "Bash"}', b'{"tool_name": "Bash", "tool_input": {"command": 1}}'],
    ids=["tomt", "inte-json", "lista", "inte-utf8", "utan-tool-input", "command-tal"],
)
def test_programmet_stoppar_trasig_indata(mappar, indata):
    svar = _kor_programmet(mappar, indata)
    assert svar.returncode == 2 and "indata" in svar.stderr.decode("utf-8")


def test_programmet_stoppar_nar_vakten_kraschar_mitt_i_bedomningen(vakt, mappar, monkeypatch):
    # Bedömningen byts mot en som kraschar. Kommandot ska då stoppas med kod 2, inte släppas igenom
    # (mutationstest d, 2026-10-28: utan det här testet var inget test rött när kraschen släppte igenom).
    def kraschar(*_):
        raise RuntimeError("prov")

    monkeypatch.setattr(vakt, "bedom", kraschar)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(json.dumps(_indata(mappar, "ls")).encode())))
    fel = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    monkeypatch.setattr(sys, "stderr", fel)
    assert vakt.main() == 2
    fel.flush()
    assert "oväntat fel" in fel.buffer.getvalue().decode("utf-8")


def test_programmet_stoppar_nar_vakten_kraschar_vid_inlasningen(mappar):
    # JSON som är kapslad för djupt får Python att krascha (RecursionError) redan vid inläsningen,
    # utanför vaktens vanliga felhantering. Kommandot ska ändå stoppas.
    svar = _kor_programmet(mappar, b"[" * 100000)
    assert svar.returncode == 2


def test_programmet_tar_path_fran_sin_miljo(mappar, tmp_path):
    # Claude Code ger vakten sin PATH i miljön. Ett git i en mapp som användaren äger stoppas.
    egen = str(tmp_path / "egen-bin")
    _lagg_program(egen, "git")
    svar = _kor_programmet(mappar, _indata(mappar, "git status"), sokvag=f"{egen}:{SYSTEMETS_SOKVAG}")
    assert svar.returncode == 2 and PLATS in svar.stderr.decode("utf-8")


def test_programmet_stoppar_utan_path(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "git status"), sokvag=None)
    assert svar.returncode == 2 and OSAKER in svar.stderr.decode("utf-8")


def test_programmet_stoppar_utan_projektmapp(mappar):
    svar = _kor_programmet(mappar, _indata(mappar, "git status"), projektmapp=False)
    assert svar.returncode == 2 and "CLAUDE_PROJECT_DIR" in svar.stderr.decode("utf-8")


def test_programmet_laser_inte_in_filer_bredvid_sig(mappar, tmp_path):
    # -I gör att Python inte läser in en planterad json.py från vaktens mapp eller arbetsmappen.
    mapp = tmp_path / "planterad"
    mapp.mkdir()
    shutil.copy(VAKTEN, mapp / "kommandosparr.py")
    (mapp / "json.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    svar = _kor_programmet(mappar, _indata(mappar, "rm x"), fil=mapp / "kommandosparr.py", cwd=str(mapp))
    assert svar.returncode == 2 and LISTAN in svar.stderr.decode("utf-8")


def test_vakten_anvander_bara_pythons_egna_delar():
    # Vakten körs med /usr/bin/python3, utan projektets .venv, och får därför bara använda
    # Pythons standardbibliotek.
    tillatna = {"__future__", "json", "os", "pwd", "sys", "unicodedata"}
    trad = ast.parse(VAKTEN.read_text(encoding="utf-8"))
    moduler = set()
    for nod in ast.walk(trad):
        if isinstance(nod, ast.Import):
            moduler |= {alias.name.split(".")[0] for alias in nod.names}
        elif isinstance(nod, ast.ImportFrom):
            assert nod.level == 0, "vakten får inte läsa in filer bredvid sig"
            moduler.add(nod.module.split(".")[0])
    assert moduler <= tillatna, moduler - tillatna


# ---------------------------------------------------------------------------------------------
# Förslaget till låsta inställningar och installationsbeskrivningen.

def _installningar():
    return json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))


def test_installningarna_lasar_vakter_och_regler():
    installningar = _installningar()
    assert installningar["allowManagedHooksOnly"] is True
    assert installningar["allowManagedPermissionRulesOnly"] is True
    assert installningar["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert "allow" not in installningar["permissions"], "inget ska godkännas i förväg"


def test_installningarna_kor_vakten_fore_varje_verktyg_och_stoppar_om_den_fallerar():
    vakter = _installningar()["hooks"]["PreToolUse"]
    assert len(vakter) == 1 and vakter[0]["matcher"] == "*"
    assert vakter[0]["hooks"] == [
        {
            "type": "command",
            "command": SYSTEMETS_PYTHON,
            "args": ["-I", INSTALLERAD_VAKT],
            "timeout": 10,
            "onFailure": "block",
        }
    ]


def test_installationsfilen_startar_vakten_med_hela_sokvagar_och_stoppar_om_den_fallerar():
    # Hugos beslut 2026-10-28, beslut 2: varje vakt i installationsfilen startas med fullständig sökväg
    # till både tolken (Python) och skriptet, och har "onFailure": "block". Testet läser filen och
    # prövar alla vakter i den, inte bara den första.
    alla = [
        vakt_
        for grupper in _installningar()["hooks"].values()
        for grupp in grupper
        for vakt_ in grupp["hooks"]
    ]
    assert alla, "installationsfilen har ingen vakt"
    for vakt_ in alla:
        assert vakt_["onFailure"] == "block", vakt_
        tolken = vakt_["command"]
        assert os.path.isabs(tolken) and " " not in tolken and tolken == SYSTEMETS_PYTHON, tolken
        skript = [a for a in vakt_["args"] if not a.startswith("-")]
        assert skript == [INSTALLERAD_VAKT] and os.path.isabs(skript[0]), vakt_["args"]
        assert skript[0].startswith("/Library/Application Support/ClaudeCode/")


def test_installningarna_nekar_sudo_su_och_att_skriva_i_git():
    neka = _installningar()["permissions"]["deny"]
    for regel in ["Bash(sudo *)", "Bash(su *)", "Bash(su)", "Edit(//**/.git/**)"]:
        assert regel in neka


def test_installningarna_nekar_bade_mappen_git_och_filen_git():
    # Granskning 12, P5 (Hugos beslut 2026-10-28): i en worktree är .git en fil, inte en mapp. Båda ska
    # vara förbjudna, på varje djup. //**/.git utan /** på slutet gäller en fil med det namnet var den än
    # ligger, som Read(//**/.env) i code.claude.com/docs/en/permissions ("How deep a pattern matches").
    neka = _installningar()["permissions"]["deny"]
    assert "Edit(//**/.git/**)" in neka
    assert "Edit(//**/.git)" in neka


def test_installningarna_stanger_av_skalkommandon_i_skills():
    # Granskning 12, P3 (Hugos beslut 2026-10-28, 1). Nyckeln ligger överst i filen och tar true
    # (code.claude.com/docs/en/settings-reference, "disableSkillShellExecution").
    assert _installningar()["disableSkillShellExecution"] is True


def test_installningarna_stanger_av_laget_auto():
    # Granskning 12, P6 (Hugos beslut 2026-10-28, 4). Under permissions, värdet "disable"
    # (code.claude.com/docs/en/settings-reference, "disableAutoMode / permissions.disableAutoMode").
    assert _installningar()["permissions"]["disableAutoMode"] == "disable"


# Hugos beslut 2026-10-28, 5 (granskning 12, beslut b). Mapparna i PATH är granskarens förslag för de
# mappar Hugo äger. Vilka som faktiskt finns i Hugos PATH är inte kontrollerat (öppen fråga).
NYA_FORBUD = [
    "Edit(~/.ssh/**)",
    "Edit(//**/.mcp.json)",
    "Edit(//**/.claude/**)",
    "Edit(~/.claude.json)",
    "Edit(~/bin/**)",
    "Edit(~/.local/bin/**)",
    "Edit(//opt/homebrew/**)",
    "Edit(//**/.venv/**)",
]


@pytest.mark.parametrize("regel", NYA_FORBUD)
def test_installningarna_nekar_hugos_nya_forbud(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_claude_md_ar_inte_forbjuden():
    # Hugos beslut 2026-10-28, 5: inget förbud för CLAUDE.md. Hugo och Casper ber ibland agenten ändra den.
    for regel in _installningar()["permissions"]["deny"]:
        assert "CLAUDE.md" not in regel, regel


def test_git_regeln_galler_varje_git_mapp_pa_datorn():
    # Regeln ska gälla .git var den än ligger, så att samma fil fungerar på Caspers dator. I Claude Codes
    # regler betyder // datorns rot och ** valfritt antal mappar (code.claude.com/docs/en/permissions,
    # "How path patterns match", exemplet Read(//**/.env)). Ingen regel får ha ett användarnamn eller
    # en hemmapp i sig.
    neka = _installningar()["permissions"]["deny"]
    git_regler = [regel for regel in neka if "/.git/" in regel]
    assert git_regler == ["Edit(//**/.git/**)"]
    text = INSTALLNINGAR.read_text(encoding="utf-8")
    assert "/Users/" not in text and "hugolindholmer" not in text


# Filer som körs eller läses in av skalet, git, Claude Code eller macOS och som kan få ett tillåtet
# kommando att göra något annat (Hugos beslut 2026-10-28, punkt 5). ~/ är hemmappen för den som kör
# Claude Code (code.claude.com/docs/en/permissions, "How path patterns match", Read(~/.zshrc)).
STARTFILER = [
    "Edit(~/.zshrc)",
    "Edit(~/.zshenv)",
    "Edit(~/.zprofile)",
    "Edit(~/.zlogin)",
    "Edit(~/.bashrc)",
    "Edit(~/.bash_profile)",
    "Edit(~/.profile)",
    "Edit(~/.gitconfig)",
    "Edit(~/.config/git/**)",
    "Edit(~/.claude/**)",
    "Edit(~/Library/LaunchAgents/**)",
]


@pytest.mark.parametrize("regel", STARTFILER)
def test_installningarna_nekar_att_skriva_i_startfiler(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_filregler_har_en_form_som_galler_pa_varje_dator():
    # Varje Edit-regel börjar med // (datorns rot) eller ~/ (hemmappen). En regel med en ensam / eller
    # utan början gäller i förhållande till inställningsfilen eller arbetsmappen, inte där det är tänkt.
    for regel in _installningar()["permissions"]["deny"]:
        if regel.startswith("Edit("):
            assert regel.endswith(")")
            assert regel[len("Edit("):].startswith(("//", "~/")), regel


def test_installningarna_kraver_lagst_den_version_som_kan_stoppa_vid_krasch():
    # onFailure kräver Claude Code 2.1.295 (code.claude.com/docs/en/hooks). En äldre version ska inte
    # starta alls (Hugos beslut 2026-10-28, punkt 3).
    assert _installningar()["requiredMinimumVersion"] == "2.1.295"


def _installationskommandon():
    text = INSTALLERA.read_text(encoding="utf-8")
    # Kodblocken i kontrollen efter installationen är indragna under sin listpunkt.
    block = re.findall(r"```bash\n(.*?)```", text, flags=re.S)
    return text, [rad.strip() for b in block for rad in b.splitlines() if rad.strip()]


FORPROV_MAPP = "~/vera-forprov"
FORPROV_FIL = f"{FORPROV_MAPP}/.claude/settings.json"
FORPROV_ECHO = "echo '{"
FORPROV_KOMMANDON = (
    f"ls -ld {FORPROV_MAPP}",
    f"mkdir -p {FORPROV_MAPP}/.claude",
    FORPROV_ECHO,
    f"cat {FORPROV_FIL}",
    f"rm {FORPROV_FIL}",
    f"rmdir {FORPROV_MAPP}/.claude",
    f"rmdir {FORPROV_MAPP}",
)
KEDJAN = 'ls -ld / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"'

# Hugos beslut 2026-10-28 om vakten, beslut 2: INSTALLERA.md beskriver hur Hugo själv flyttar nvm-mappen
# sist i PATH. Agenten ändrar inte Hugos skalfiler.
NVM_KOPIA = "cp -i ~/.zshrc ~/.zshrc.fore-vera"
NVM_RAD = '[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )'
NVM_LAGG_TILL = f"echo '{NVM_RAD}' >> ~/.zshrc"
NVM_KOMMANDON = (NVM_KOPIA, NVM_LAGG_TILL, "tail -n 3 ~/.zshrc", "echo $PATH")


def test_installationen_bara_kopierar_och_satter_agare_och_rattigheter():
    # Utöver kopieringen: förprovet i en egen mapp, nvm-mappen sist i PATH, projektets Python på den nya
    # platsen, och ls -ld för att läsa ägare och rättigheter.
    _, rader = _installationskommandon()
    tillatna = (
        "shasum -a 256 ",
        "sudo mkdir ",
        "sudo ditto ",
        "sudo cp -i ",
        "sudo chown ",
        "sudo chmod ",
        'ls -ld "/Library/Application Support/ClaudeCode',
        KEDJAN,
        FLYTTA_UNDAN,
        FLYTTA_TILLBAKA,
        VENV_SKAPA,
        VENV_PIP,
    ) + FORPROV_KOMMANDON
    assert rader
    for rad in rader:
        assert rad.startswith(tillatna) or rad in NVM_KOMMANDON, rad


def test_beslut_2_installera_beskriver_hur_nvm_mappen_flyttas_sist_i_path():
    text, rader = _installationskommandon()
    plats = {k: rader.index(k) for k in NVM_KOMMANDON}
    # Säkerhetskopian först, sedan raden, sedan kontrollen. Allt före installationen.
    assert plats[NVM_KOPIA] < plats[NVM_LAGG_TILL] < plats["tail -n 3 ~/.zshrc"] < plats["echo $PATH"]
    assert max(plats.values()) < _forsta_sudo(rader)
    # Raden tar bort nvm-mappen ur listan och lägger den sist, och bara om nvm har angett mappen (annars
    # skulle en tom mapp, alltså arbetsmappen, hamna sist i PATH).
    assert NVM_RAD.startswith('[ -n "$NVM_BIN" ] && ')
    (steget,) = [_en_rad(t) for r, t in _steg(text) if "nvm" in r.lower()]
    assert "Quit Claude" in steget, "appen ska startas om så att den läser PATH på nytt"
    assert "agenten ändrar inte" in steget.lower()


def _steg(text):
    """Avsnitten i INSTALLERA.md med rubriken "## Steg ...", i ordning, som (rubrik, text)."""
    delar = re.split(r"\n(## .*)\n", "\n" + text.split(KONTROLL_RUBRIK, 1)[0])
    return [(delar[i], delar[i + 1]) for i in range(1, len(delar), 2) if delar[i].startswith("## Steg")]


def test_installationen_kontrollerar_versionen_forst():
    # Hugos beslut 2026-10-28, beslut 3: versionen kontrolleras med /status i en Claude Code-session och
    # ska vara 2.1.295 eller senare. Kommandot claude finns inte i Terminal på Hugos dator.
    text, rader = _installationskommandon()
    rubrik, forsta = _steg(text)[0]
    forsta = _en_rad(forsta)
    assert "version" in rubrik.lower()
    assert "/status" in forsta and "2.1.295" in forsta
    assert "Check for Updates" in forsta, "hur Hugo uppdaterar ska stå med"
    assert "claude --version" not in rader
    assert "code.claude.com/docs/en/hooks" in text


def _forsta_sudo(rader):
    return min(i for i, r in enumerate(rader) if r.startswith("sudo "))


def test_forprovet_gors_fore_installationen_och_stadas_bort():
    # Hugos beslut 2026-10-28, beslut 2: förprovet görs före installationen, och den tillfälliga mappen
    # raderas efteråt. Mappen ligger utanför ~/VERA.
    text, rader = _installationskommandon()
    # Hela kommandon jämförs exakt, så att "rmdir ~/vera-forprov" inte räknas som ".../.claude".
    plats = {
        k: next(i for i, r in enumerate(rader) if (r.startswith(k) if k == FORPROV_ECHO else r == k))
        for k in FORPROV_KOMMANDON
    }
    assert max(plats.values()) < _forsta_sudo(rader)
    assert plats[f"ls -ld {FORPROV_MAPP}"] < plats[f"mkdir -p {FORPROV_MAPP}/.claude"] < plats[FORPROV_ECHO]
    assert plats[FORPROV_ECHO] < plats[f"rm {FORPROV_FIL}"] < plats[f"rmdir {FORPROV_MAPP}/.claude"]
    assert plats[f"rmdir {FORPROV_MAPP}/.claude"] < plats[f"rmdir {FORPROV_MAPP}"]
    assert not FORPROV_MAPP.lower().startswith("~/vera/")
    (forprovet,) = [_en_rad(t) for r, t in _steg(text) if "förprov" in r.lower()]
    assert "`ls`" in forprovet and "avbryt installationen" in forprovet


def test_forprovets_vakt_pekar_pa_ett_skript_som_inte_finns_och_har_onfailure_block():
    _, rader = _installationskommandon()
    rad = next(r for r in rader if r.startswith(FORPROV_ECHO))
    innehall, _, mal = rad[len("echo '"):].rpartition("' > ")
    assert mal == FORPROV_FIL
    installningar = json.loads(innehall)
    assert list(installningar) == ["hooks"] and list(installningar["hooks"]) == ["PreToolUse"]
    (grupp,) = installningar["hooks"]["PreToolUse"]
    assert grupp["matcher"] == "*"
    (vakt_,) = grupp["hooks"]
    assert vakt_["type"] == "command" and vakt_["onFailure"] == "block"
    # Ett skript som inte finns, med hel sökväg och utan tolk framför: då går vakten inte att starta, och
    # det är onFailure som avgör (inte kod 2 från en Python som inte hittar sin fil).
    assert os.path.isabs(vakt_["command"]) and not os.path.exists(vakt_["command"])
    assert " " not in vakt_["command"] and "python" not in vakt_["command"]


def test_agare_och_rattigheter_kontrolleras_fore_och_efter_installationen():
    # Hugos beslut 2026-10-28, beslut 3 (P7): ls -ld för hela kedjan före och efter installationen.
    _, rader = _installationskommandon()
    kedjan = [i for i, r in enumerate(rader) if r == KEDJAN]
    sista_chmod = max(i for i, r in enumerate(rader) if r.startswith("sudo chmod"))
    assert any(i < _forsta_sudo(rader) for i in kedjan)
    assert any(i > sista_chmod for i in kedjan)


def test_mappen_och_filerna_far_ratt_agare_och_rattigheter():
    # Mappen ClaudeCode (och vera) root:wheel och 755, filerna root:wheel och 644.
    _, rader = _installationskommandon()
    mapp = '"/Library/Application Support/ClaudeCode"'
    assert f"sudo mkdir {mapp}" in rader
    assert any(r.startswith("sudo chown root:wheel ") and mapp in r for r in rader)
    assert any(r.startswith("sudo chmod 755 ") and mapp in r for r in rader)
    for fil in (INSTALLERAD_VAKT, INSTALLERADE_INSTALLNINGAR):
        assert any(r.startswith("sudo chown root:wheel ") and f'"{fil}"' in r for r in rader), fil
        assert any(r.startswith("sudo chmod 644 ") and f'"{fil}"' in r for r in rader), fil
    assert not any(r.startswith("sudo chmod 600") for r in rader)


def test_installera_forklarar_varfor_644_och_inte_600():
    text = _en_rad(INSTALLERA.read_text(encoding="utf-8"))
    assert "600" in text and "hoppas över utan varning" in text


def test_status_efter_installationen_avgor_om_den_lyckades():
    # Beslut 3: /status ska visa "Enterprise managed settings (file)" på raden Setting sources. Annars
    # gäller inte vakten, och installationen räknas som misslyckad.
    efterat = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Efteråt", 1)[1].split("\n## ", 1)[0])
    assert "Setting sources" in efterat and "Enterprise managed settings (file)" in efterat
    assert "misslyckad" in efterat


def test_installationen_kopierar_vakten_fore_installningarna():
    # Inställningarna gäller så fort filen finns. Vakten ska därför vara på plats, och ägas av
    # systemet så att agenten inte kan ändra den, innan inställningarna kopieras.
    _, rader = _installationskommandon()
    vakten = next(i for i, r in enumerate(rader) if r.startswith("sudo ditto") and INSTALLERAD_VAKT in r)
    installningarna = next(
        i for i, r in enumerate(rader) if r.startswith("sudo cp -i") and INSTALLERADE_INSTALLNINGAR in r
    )
    agare = [
        i for i, r in enumerate(rader[:installningarna]) if r.startswith("sudo chown") and INSTALLERAD_VAKT in r
    ]
    rattigheter = [
        i for i, r in enumerate(rader[:installningarna]) if r.startswith("sudo chmod") and INSTALLERAD_VAKT in r
    ]
    assert agare and rattigheter
    assert vakten < min(agare) and vakten < min(rattigheter)
