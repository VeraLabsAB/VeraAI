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

PYTEST = ".venv/bin/python -B -m pytest -p no:cacheprovider"


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


def _bedom(vakt, mappar, kommando, verktyg="Bash"):
    return vakt.bedom(_indata(mappar, kommando, verktyg), mappar["projekt"], mappar["hem"])


# ---------------------------------------------------------------------------------------------
# Det som SPEC 7.1 tillåter går igenom. En rad per rad i tabellen i 7.1, och de regler under den
# som tillåter något (läsa i kopior, provfiler i kopian, tillägg till pytest).

TILLATNA = [
    # Rad 1: testsviten i projektet.
    ("pytest-projektet", f"{PYTEST} -q scripts/tests"),
    # Rad 2: testsviten mot en kopia, hela mappen eller en testfil i kopian.
    ("pytest-kopia", f"{PYTEST} <T>/kopia/scripts/tests"),
    ("pytest-kopia-testfil", f"{PYTEST} <T>/kopia/scripts/tests/test_prov.py"),
    # Tillägg som bara ändrar vad som visas.
    ("pytest-tillagg", f"{PYTEST} -qq --tb=short -rA -p no:randomly -k regelbok scripts/tests"),
    ("pytest-tillagg-separata", f"{PYTEST} -q --tb line -r fE -k 'not langsam' scripts/tests"),
    ("pytest-k-hopskrivet", f"{PYTEST} -kbelopp <T>/kopia/scripts/tests"),
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


@pytest.mark.parametrize("verktyg", ["Read", "Write", "Edit", "Glob", "Grep", "WebFetch"])
def test_vanliga_filverktyg_slapps_igenom(vakt, mappar, verktyg):
    # SPEC 7.1 gäller bara kommandon (planen, regel 2). Fil-verktygen släpps igenom.
    indata = _indata(mappar, "", verktyg)
    indata["tool_input"] = {"file_path": mappar["projekt"] + "/SPEC.md"}
    assert vakt.bedom(indata, mappar["projekt"], mappar["hem"]) is None


def test_agenten_kan_fraga_och_skriva_filer_i_vera(vakt, mappar):
    # Kontrollen efter installationen (INSTALLERA.md): agenten ska fortfarande kunna fråga Hugo och
    # skriva filer i ~/VERA. Vakten ska alltså släppa igenom båda, också utanför projektmappen.
    fraga = _indata(mappar, "", "AskUserQuestion")
    fraga["tool_input"] = {"questions": [{"question": "Prov?", "header": "Prov", "options": []}]}
    assert vakt.bedom(fraga, mappar["projekt"], mappar["hem"]) is None
    skriv = _indata(mappar, "", "Write")
    skriv["tool_input"] = {"file_path": os.path.join(mappar["hem"], "VERA", "prov.txt"), "content": "x"}
    assert vakt.bedom(skriv, mappar["projekt"], mappar["hem"]) is None


def test_installationen_kontrollerar_att_agenten_kan_fraga_och_skriva():
    text = INSTALLERA.read_text(encoding="utf-8")
    efterat = text.split("## Efteråt", 1)[1].split("\n## ", 1)[0]
    assert "kan fråga dig" in efterat
    assert "kan skriva filer i `~/VERA`" in efterat


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
VERKTYG = "kör kommandon"

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
    ("python-skript", ".venv/bin/python x.py", PYTEST_FORM),
    ("python-c", ".venv/bin/python -c 'print(1)'", PYTEST_FORM),
    ("pytest-utan-B", ".venv/bin/python -m pytest -p no:cacheprovider scripts/tests", PYTEST_FORM),
    ("pytest-utan-cache", ".venv/bin/python -B -m pytest scripts/tests", PYTEST_FORM),
    ("pip", ".venv/bin/python -B -m pip install x", PYTEST_FORM),
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
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"])
    assert fel is not None and "annan mapp" in fel


def test_kommando_utan_mapp_stoppas(vakt, mappar):
    indata = _indata(mappar, "git status")
    del indata["cwd"]
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"])
    assert fel is not None and "indata" in fel


def test_utan_projektmapp_stoppas_allt(vakt, mappar):
    fel = vakt.bedom(_indata(mappar, "git status"), None, mappar["hem"])
    assert fel is not None and "CLAUDE_PROJECT_DIR" in fel


@pytest.mark.parametrize("vilken", ["hem", "ovanfor-hem"])
def test_session_i_hemmappen_eller_ovanfor_stoppas(vakt, mappar, vilken):
    # Då skulle "projektet" vara hela hemmappen, och läsande kommandon nå allt i den.
    mapp = mappar["hem"] if vilken == "hem" else os.path.dirname(mappar["hem"])
    indata = _indata(mappar, "ls")
    indata["cwd"] = mapp
    fel = vakt.bedom(indata, mapp, mappar["hem"])
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
    fel = vakt.bedom(indata, annan, mappar["hem"])
    assert fel is not None and nyckel in fel


def test_utan_tillfallig_mapp_stoppas_mkdir_men_inte_cat(vakt, mappar):
    indata = _indata(mappar, "mkdir <T>/kopia")
    del indata["scratchpad_dir"]
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"])
    assert fel is not None and TILLFALLIG in fel
    indata = _indata(mappar, "cat SPEC.md")
    del indata["scratchpad_dir"]
    assert vakt.bedom(indata, mappar["projekt"], mappar["hem"]) is None


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
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"])
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
    fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"])
    assert fel is not None and "indata" in fel


# ---------------------------------------------------------------------------------------------
# Programmet: så som Claude Code kör det, med datorns egen Python och -I.

def _kor_programmet(mappar, indata, fil=VAKTEN, projektmapp=True, cwd=None):
    miljo = {"PATH": "/usr/bin:/bin"}
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


def test_installningarna_nekar_sudo_su_och_att_skriva_i_git():
    neka = _installningar()["permissions"]["deny"]
    for regel in ["Bash(sudo *)", "Bash(su *)", "Bash(su)", "Edit(//**/.git/**)"]:
        assert regel in neka


def test_git_regeln_galler_varje_git_mapp_pa_datorn():
    # Regeln ska gälla .git var den än ligger, så att samma fil fungerar på Caspers dator. I Claude Codes
    # regler betyder // datorns rot och ** valfritt antal mappar (code.claude.com/docs/en/permissions,
    # "How path patterns match", exemplet Read(//**/.env)). Ingen regel får ha ett användarnamn eller
    # en hemmapp i sig.
    neka = _installningar()["permissions"]["deny"]
    git_regler = [regel for regel in neka if ".git" in regel]
    assert git_regler == ["Edit(//**/.git/**)"]
    text = INSTALLNINGAR.read_text(encoding="utf-8")
    assert "/Users/" not in text and "hugolindholmer" not in text and "~/" not in text


def _installationskommandon():
    text = INSTALLERA.read_text(encoding="utf-8")
    block = re.findall(r"```bash\n(.*?)```", text, flags=re.S)
    return text, [rad for b in block for rad in b.splitlines() if rad.strip()]


def test_installationen_bara_kopierar_och_satter_agare_och_rattigheter():
    _, rader = _installationskommandon()
    tillatna = ("claude --version", "sudo ditto ", "sudo cp -i ", "sudo chown ", "sudo chmod ")
    assert rader
    for rad in rader:
        assert rad.startswith(tillatna), rad


def test_installationen_kontrollerar_versionen_forst():
    text, rader = _installationskommandon()
    assert rader[0] == "claude --version"
    assert "2.1.295" in text and "/status" in text
    assert "code.claude.com/docs/en/hooks" in text


def test_installationen_kopierar_vakten_fore_installningarna():
    # Inställningarna gäller så fort filen finns. Vakten ska därför vara på plats, och ägas av
    # systemet så att agenten inte kan ändra den, innan inställningarna kopieras.
    _, rader = _installationskommandon()
    vakten = next(i for i, r in enumerate(rader) if r.startswith("sudo ditto") and INSTALLERAD_VAKT in r)
    installningarna = next(
        i for i, r in enumerate(rader) if r.startswith("sudo cp -i") and INSTALLERADE_INSTALLNINGAR in r
    )
    agare = [i for i, r in enumerate(rader[:installningarna]) if r.startswith("sudo chown")]
    rattigheter = [
        i for i, r in enumerate(rader[:installningarna]) if r.startswith("sudo chmod") and INSTALLERAD_VAKT in r
    ]
    assert agare and rattigheter
    assert vakten < min(agare) and vakten < min(rattigheter)
