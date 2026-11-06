"""Steg 15: sandlådan (Hugos beslut 2026-11-04 om sandlådan, Hugos beslut 2026-11-05 om granskning 34 och Hugos beslut
2026-11-05 efter P6, GRANSKNING.md).

Tre delar:

- Testerna som läser sparr/managed-settings.json och visar besluten. De körs alltid.
- Testerna av INSTALLERA.md. De godtar bara kända kommandon, i rätt ordning, och stoppar allt annat (granskning 34, P5).
- Spärrtestet, som prövar att sandlådan faktiskt stoppar. Det hoppas över med ett tydligt meddelande när sandlådan inte är
  installerad, eller när pytest inte körs av Claude Code i sandlådan. Då stoppar inget, så provet säger inget.

Spärrtestet skriver i testets tillfälliga mapp, och i tre fall utanför den:

- Proven att skrivning utanför projektet stoppas försöker skapa en ny fil med ett slumpat namn, och tar bort den direkt om
  det ändå gick. Provet för ~/.ssh visar aldrig vad som ligger där. Hugos beslut 2026-11-04 säger att det ska prövas.
- test_sparr_hard_lank_till_ssh_stoppas försöker göra en hård länk till testfilen ~/.ssh/prov, ett uttalat undantag från
  länkregeln i CLAUDE.md, bara här (Hugos beslut 2026-11-05 om granskning 37, P3).
- Proven test_sparr_kopian_ gäller kopian ~/VERA/sparrprov, som Hugo förbereder utanför sandlådan (Hugos beslut 2026-11-05,
  beslut 4, ett undantag från regeln "Prov och test", bara för spärrtestet). De körs bara i en session startad i kopian,
  vägrar om kopian är projektet, och rör aldrig projektets riktiga .git.
"""

import ast
import builtins
import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturen används av pytest via namnet)
    AGENT_KOMMANDO,
    INSTALLERA,
    INSTALLERADE_INSTALLNINGAR,
    INSTALLNINGAR,
    PROJEKTET,
    VAKTEN,
    _bedom,
    gor_mapp_eller_hoppa_over,
    installera_utan_sandlada,
    mappar,
    vakt,
)

CLAUDE_MD = PROJEKTET / "CLAUDE.md"
GRANSKNING = PROJEKTET / "GRANSKNING.md"
SPEC = PROJEKTET / "SPEC.md"
PROGRESS = PROJEKTET / "PROGRESS.md"
GITIGNORE = PROJEKTET / ".gitignore"
# Vaktens kontrollsumma, oförändrad sedan 2026-10-28 (INSTALLERA.md, steg 5). Beslut 5: vakten ändras inte.
VAKTENS_SUMMA = "314df00b4239877d21e0fef7d8f11c844a75d07276ad0af32baa94db8e92d10d"
# Filen som är installerad i dag, före steg 15.
FORE_STEG_15 = "149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2"
GIT = "/usr/bin/git"
HEM = Path.home()
SPARRPROV = HEM / "VERA" / "sparrprov"
RIKTIGA_PROJEKTET = HEM / "VERA" / "agent"
PROVKORNING_RUBRIK = "## Provkörning med sandlådan, före bytet (steg 15)"
BYTE_RUBRIK = "## Byte till versionen med sandlåda (steg 15)"
SPARRPROV_RUBRIK = "## Spärrprovet i kopian (steg 15)"
UTANFOR_RUBRIK = "## Prov utanför sandlådan (steg 15)"


def _installningar():
    return json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))


def _avsnitt(rubrik):
    text = INSTALLERA.read_text(encoding="utf-8")
    assert rubrik in text
    return text.split(rubrik, 1)[1].split("\n## ", 1)[0]


def _byte_avsnittet():
    return _avsnitt(BYTE_RUBRIK)


# ---------------------------------------------------------------------------------------------
# Beslut 1-7 om sandlådan (2026-11-04), med ändringarna i Hugos beslut 2026-11-05 om granskning 34.


def test_beslut_1_sandladan_ligger_i_de_lasta_installningarna_och_installeras_med_losenord():
    assert "sandbox" in _installningar()
    assert (
        'sudo cp ~/VERA/agent/sparr/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"'
        in _byte_avsnittet()
    )
    assert not (PROJEKTET / ".claude" / "settings.json").exists(), "sandlådan ska inte ligga i projektets inställningar"


def test_beslut_2_sandladan_ar_obligatorisk_och_utan_undantag():
    sandbox = _installningar()["sandbox"]
    assert sandbox["enabled"] is True
    assert sandbox["allowUnsandboxedCommands"] is False
    assert sandbox["failIfUnavailable"] is True
    assert sandbox["excludedCommands"] == []


def test_beslut_3_sandladan_andrar_inte_vilka_kommandon_som_kors_utan_att_fraga():
    assert _installningar()["sandbox"]["autoAllowBashIfSandboxed"] is False


def test_beslut_4_inga_nya_mappar_att_skriva_i_och_forbud_for_appen_och_claude_code():
    installningar = _installningar()
    filesystem = installningar["sandbox"]["filesystem"]
    # Ingen allowWrite: bara det som sandlådan tillåter från början, projektmappen och den tillfälliga mappen.
    assert set(filesystem) == {"denyWrite", "denyRead"}
    assert filesystem["denyWrite"] == [
        "/Applications/Claude.app",
        "~/Library/Application Support/Claude/claude-code",
        "~/.local/share/claude",
    ]
    assert "allow" not in installningar["permissions"]
    assert "additionalDirectories" not in installningar["permissions"]


def test_beslut_5_vakten_ar_oforandrad_och_kors_som_forut():
    assert hashlib.sha256(VAKTEN.read_bytes()).hexdigest() == VAKTENS_SUMMA
    vakter = _installningar()["hooks"]["PreToolUse"]
    assert len(vakter) == 1 and vakter[0]["matcher"] == "*" and vakter[0]["hooks"][0]["onFailure"] == "block"


def test_beslut_7_sandladan_och_read_forbjuder_lasning_av_ssh():
    # Hugos svar i chatten 2026-11-04: Read(~/.ssh/**) läggs till, eftersom denyRead inte stoppar fil-verktyget Read.
    installningar = _installningar()
    assert installningar["sandbox"]["filesystem"]["denyRead"] == ["~/.ssh"]
    assert "Read(~/.ssh/**)" in installningar["permissions"]["deny"]


@pytest.mark.parametrize("regel", ["Edit(//**/.git/**)", "Edit(//**/.git)", "Edit(//**/.venv/**)"])
def test_2026_11_05_beslut_1_forbuden_for_git_och_venv_ar_som_fore_steg_15(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_2026_11_05_beslut_1_samma_forbud_som_vakten_i_samma_ordning(vakt):
    edit = [r[len("Edit("):-1] for r in _installningar()["permissions"]["deny"] if r.startswith("Edit(")]
    assert edit == list(vakt.SKRIVFORBUD)


@pytest.mark.parametrize(
    "regel",
    [
        # Avsmalningen från steg 15, som återkallas.
        "Edit(~/VERA/agent/.venv/**)",
        # Granskarens 14 nya förbud, som inte byggs, eftersom de bara täcker kända vägar.
        "Edit(//**/.git/commondir)",
        "Edit(//**/.git/config.worktree)",
        "Edit(//**/.git/modules/**)",
        "Edit(//**/.git/modules)",
        "Edit(//**/.git/worktrees/*/commondir)",
        "Edit(//**/.git/worktrees/*/gitdir)",
        "Edit(//**/.git/worktrees/*/config.worktree)",
        "Edit(//**/.git/rebase-merge/**)",
        "Edit(//**/.git/rebase-merge)",
        "Edit(//**/.git/rebase-apply/**)",
        "Edit(//**/.git/rebase-apply)",
        "Edit(//**/.git/sequencer/**)",
        "Edit(//**/.git/sequencer)",
        "Edit(~/VERA/agent/*/**/.git)",
    ],
)
def test_2026_11_05_beslut_1_varken_avsmalningen_eller_granskarens_forbud_finns(regel):
    assert regel not in _installningar()["permissions"]["deny"]


def test_2026_11_05_beslut_1_filen_ar_den_installerade_plus_sandladan_och_ssh():
    # Tar man bort sandbox-blocket och Read(~/.ssh/**) och sätter tillbaka den gamla versionen (Hugos beslut 2026-11-05
    # efter P6, beslut 2), ska det bli exakt filen som är installerad i dag, byte för byte.
    rader = INSTALLNINGAR.read_text(encoding="utf-8").splitlines(keepends=True)
    start = rader.index('  "sandbox": {\n')
    slut = rader.index("  },\n", start)
    kvar = rader[:start] + rader[slut + 1:]
    kvar.remove('      "Read(~/.ssh/**)",\n')
    kvar[kvar.index('  "requiredMinimumVersion": "2.1.305",\n')] = '  "requiredMinimumVersion": "2.1.295",\n'
    assert hashlib.sha256("".join(kvar).encode("utf-8")).hexdigest() == FORE_STEG_15


@pytest.mark.parametrize(
    "stig",
    [
        ("enableWeakerNestedSandbox",),
        ("enableWeakerNetworkIsolation",),
        ("allowAppleEvents",),
        ("allowNestedUserNamespaces",),
        ("network", "allowAllUnixSockets"),
        ("network", "allowLocalBinding"),
    ],
    ids=lambda stig: stig[-1],
)
def test_2026_11_05_beslut_6_de_sex_nycklarna_ar_avstangda(stig):
    # Var nycklarna står: code.claude.com/docs/en/settings-reference.md. Standardvärdet är false för alla sex.
    varde = _installningar()["sandbox"]
    for nyckel in stig:
        varde = varde[nyckel]
    assert varde is False


def test_inget_annat_i_filen_ar_andrat():
    installningar = _installningar()
    assert set(installningar) == {
        "requiredMinimumVersion",
        "allowManagedHooksOnly",
        "allowManagedPermissionRulesOnly",
        "disableSkillShellExecution",
        "permissions",
        "sandbox",
        "hooks",
    }
    assert installningar["requiredMinimumVersion"] == "2.1.305"
    assert set(installningar["permissions"]) == {"disableBypassPermissionsMode", "deny"}
    andra = [r for r in installningar["permissions"]["deny"] if not r.startswith("Edit(")]
    assert andra == ["Bash(sudo *)", "Bash(su *)", "Bash(su)", "Read(~/.ssh/**)"]
    assert set(installningar["sandbox"]) == {
        "enabled",
        "failIfUnavailable",
        "allowUnsandboxedCommands",
        "autoAllowBashIfSandboxed",
        "excludedCommands",
        "enableWeakerNestedSandbox",
        "enableWeakerNetworkIsolation",
        "allowAppleEvents",
        "allowNestedUserNamespaces",
        "network",
        "filesystem",
    }
    assert set(installningar["sandbox"]["network"]) == {"allowAllUnixSockets", "allowLocalBinding"}


@pytest.mark.parametrize(
    "text",
    [
        "committar agenten inte",
        "git add",
        "git commit -F COMMIT_MSG.txt",
        "från installationen av steg 15",
        "Prov som inte kan köras i sandlådan (grupp D)",
        "H1-proven hoppas över i Terminal och körs i appen",
        "inne i sandlådan",
        "behövs ett nytt beslut",
        "Hugos beslut 2026-11-05",
    ],
)
def test_2026_11_05_beslut_2_och_3_star_i_claude_md(text):
    assert text in CLAUDE_MD.read_text(encoding="utf-8")


def test_efter_p6_beslut_1_claude_md_sager_inte_att_h1_proven_kors_utanfor_sandladan():
    assert "grupp D och H1-proven" not in CLAUDE_MD.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# INSTALLERA.md: bara kända kommandon, i rätt ordning (granskning 34, P5).

PYTHON = "'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider"
MAPP = '"/Library/Application Support/ClaudeCode'
AKTIV = f'{MAPP}/managed-settings.json"'
SPARAD = f'{MAPP}/managed-settings.fore-sandladan.json"'
INSTALLERAD_PYTHON = f"{MAPP}/vera/venv"
INSTALLERAD_VAKT_CITERAD = f'{MAPP}/vera/kommandosparr.py"'
SUMMA = "shasum -a 256"

PROVKORNINGENS_NYCKLAR = (
    '{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false,'
    '"autoAllowBashIfSandboxed":false,"excludedCommands":[],"enableWeakerNestedSandbox":false,'
    '"enableWeakerNetworkIsolation":false,"allowAppleEvents":false,"allowNestedUserNamespaces":false,'
    '"network":{"allowAllUnixSockets":false,"allowLocalBinding":false},'
    '"filesystem":{"denyWrite":["/Applications/Claude.app","~/Library/Application Support/Claude/claude-code",'
    '"~/.local/share/claude"],"denyRead":["~/.ssh"]}}}'
)

PROVKORNINGEN = [
    "cd ~/VERA/agent",
    "~/.local/bin/claude --version",
    f"~/.local/bin/claude --settings '{PROVKORNINGENS_NYCKLAR}'",
    f"{PYTHON} -q --tb=line -rfs scripts/tests",
]

# Ordningen är granskning 34, P5: version, summor, spara, kopiera, kontrollera, kontrollen efter bytet, backa. Först
# git-inställningen (Hugos beslut 2026-11-05 om granskning 35, beslut 2).
SAFE_BARE = "git config --global --get safe.bareRepository"
HUGOS_FASTA_KOMMANDON = [
    "git status --short --ignored -uall",
    "git add -A",
    "ls -l COMMIT_MSG.txt",
    # Hugos beslut 2026-11-05 om granskning 39, beslut 3.
    "cat COMMIT_MSG.txt",
    "git commit -F COMMIT_MSG.txt",
]
TITTEN_EFTER_COMMITEN = "git show --stat HEAD"
BYTET = [
    SAFE_BARE,
    "~/.local/bin/claude --version",
    f"{SUMMA} ~/VERA/agent/sparr/managed-settings.json ~/VERA/agent/sparr/kommandosparr.py",
    f"{SUMMA} {AKTIV} {INSTALLERAD_VAKT_CITERAD}",
    f"sudo cp -i {AKTIV} {SPARAD}",
    f"sudo chown root:wheel {SPARAD}",
    f"sudo chmod 644 {SPARAD}",
    f"sudo cp ~/VERA/agent/sparr/managed-settings.json {AKTIV}",
    f"sudo chown root:wheel {AKTIV}",
    f"sudo chmod 644 {AKTIV}",
    f"{SUMMA} {AKTIV} {SPARAD}",
    f"ls -lde@ {AKTIV} {SPARAD}",
    "cd ~/VERA/agent",
    "~/.local/bin/claude",
    "grep -n -e sandbox -e additionalDirectories ~/.claude/settings.json",
    "grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.json",
    "grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.local.json",
    "git status",
    f"{PYTHON} -q --tb=short -rfs scripts/tests",
    # Hugos beslut 2026-11-05 om granskning 35, beslut 6: de fasta kommandona, som Hugo alltid skriver själv.
    *HUGOS_FASTA_KOMMANDON,
    # Hugos beslut 2026-11-05 om granskning 37, P3: efter commiten och före en push.
    TITTEN_EFTER_COMMITEN,
    f"sudo cp {SPARAD} {AKTIV}",
    f"{SUMMA} {AKTIV}",
]

SPARRPROVET = [
    "ls -ld ~/VERA/sparrprov",
    "git clone --no-hardlinks ~/VERA/agent ~/VERA/sparrprov",
    "cd ~/VERA/sparrprov",
    "git log -1 --format=%H",
    # Hugos beslut 2026-11-05 om granskning 36, P6: en ~/.ssh med en testfil, bara för provet.
    "ls -ld ~/.ssh",
    "mkdir -m 700 ~/.ssh",
    "echo kassio-prov > ~/.ssh/prov",
    "~/.local/bin/claude",
    f"{PYTHON} -q --tb=short -rfs -k test_sparr_ scripts/tests",
    # Hugos beslut 2026-11-05 efter P6, beslut 1: H1-proven i appen, med kommandot från Hugos körning.
    f"{PYTHON} -q --tb=line -rs -k test_h1_ scripts/tests",
    "cat ~/.ssh/prov",
    "cd ~/VERA/agent",
    "rm ~/.ssh/prov",
    "rmdir ~/.ssh",
    "ls -ld ~/.ssh",
    "rm -rf ~/VERA/sparrprov",
    "ls -ld ~/VERA/sparrprov",
]

# Bara grupp D (Hugos beslut 2026-11-05 efter P6, beslut 1, och om granskning 39, beslut 1).
UTANFOR_K = (
    "test_h6_en_lank_till_git_stoppas or test_beslut_1_gamla_venv_i_projektet_stoppas"
    " or test_granskning_37_p4_uall_visar_varje_fil_for_sig or test_granskning_37_p4_utan_uall_doljs_filerna"
    " or test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott"
    " or test_granskning_38_det_vantade_laget_ger_inget_stopp"
    " or test_granskning_38_p1_en_ny_fil_i_en_mapp_i_det_vantade_laget_stoppar"
    " or test_granskning_38_p3_gitattributes_i_en_ny_mapp_stoppar_i_varje_stavning"
    " or test_granskning_38_sessionens_uppraknade_filer_ar_vantade_och_inget_annat"
    " or test_granskning_39_riktiga_rader_stoppar_ocksa_om_de_ar_uppraknade"
)
UTANFOR = [
    "ls -ld ~/VERA/provkopia",
    "git clone --no-hardlinks ~/VERA/agent ~/VERA/provkopia",
    "cd ~/VERA/provkopia",
    "git log -1 --format=%H",
    f"{PYTHON} -q --tb=short -rfs -k '{UTANFOR_K}' scripts/tests",
    "cd ~/VERA/agent",
    "rm -rf ~/VERA/provkopia",
]

# Resten av filen: den vanliga installationen, kontrollen efter den och väntade utskrifter. Alla rader i alla rutor,
# i ordning. En ny rad eller en ändrad rad gör testet rött, så att den måste läggas in här med avsikt.
RESTEN = [
    "~/.local/bin/claude --version",
    "~/.local/bin/claude update",
    "cd ~/VERA/agent",
    "~/.local/bin/claude",
    'ls -lde@ / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"',
    "/Library/Developer/CommandLineTools/usr/bin/python3 --version",
    "f=/Library/Developer/CommandLineTools/usr/bin/python3; for p in $f ${f:A}; do while true; do ls -lde@ $p; "
    "[[ $p == / ]] && break; p=${p:h}; done; done",
    "ls -ld ~/vera-forprov",
    "mkdir -p ~/vera-forprov/.claude",
    """echo '{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[{"type":"command","command":"/finns-inte/vera-forprov.sh","""
    """"onFailure":"block"}]}]}}' > ~/vera-forprov/.claude/settings.json""",
    "cat ~/vera-forprov/.claude/settings.json",
    "ls",
    "rm ~/vera-forprov/.claude/settings.json",
    "rmdir ~/vera-forprov/.claude",
    "rmdir ~/vera-forprov",
    "cp -i ~/.zshrc ~/.zshrc.fore-vera",
    """echo '[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )' >> ~/.zshrc""",
    "echo 'path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )' >> ~/.zshrc",
    "tail -n 3 ~/.zshrc",
    "echo $PATH",
    "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:",
    "/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:",
    "/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:",
    "/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:",
    "/pkg/env/global/bin:/Library/Apple/usr/bin:/Users/hugolindholmer/.nvm/versions/node/v24.18.0/bin:",
    "/System/Cryptexes/App/usr/bin",
    "shasum -a 256 ~/VERA/agent/sparr/kontrollera-skalet.zsh",
    "source ~/VERA/agent/sparr/kontrollera-skalet.zsh",
    AGENT_KOMMANDO,
    "preexec_functions=()",
    "precmd_functions=()",
    "chpwd_functions=()",
    "periodic_functions=()",
    "zshaddhistory_functions=()",
    "zshexit_functions=()",
    "find",
    "grep",
    "pkill",
    "rg",
    "SLUT",
    "cp ~/.zshrc.fore-vera ~/.zshrc",
    "shasum -a 256 ~/VERA/agent/sparr/kommandosparr.py ~/VERA/agent/sparr/managed-settings.json "
    "~/VERA/agent/requirements.txt",
    f"sudo mkdir {MAPP}\"",
    f'sudo mkdir {MAPP}/vera"',
    f'sudo chown root:wheel {MAPP}" {MAPP}/vera"',
    f'sudo chmod 755 {MAPP}" {MAPP}/vera"',
    f"sudo ditto ~/VERA/agent/sparr/kommandosparr.py {INSTALLERAD_VAKT_CITERAD}",
    f"sudo chown root:wheel {INSTALLERAD_VAKT_CITERAD}",
    f"sudo chmod 644 {INSTALLERAD_VAKT_CITERAD}",
    f'sudo /usr/bin/python3 -m venv {INSTALLERAD_PYTHON}"',
    f"sudo {INSTALLERAD_PYTHON}/bin/python\" -m pip install --only-binary ':all:' --no-cache-dir "
    "-r ~/VERA/agent/requirements.txt",
    f'sudo chown -R root:wheel {INSTALLERAD_PYTHON}"',
    f'sudo chmod -R go-w {INSTALLERAD_PYTHON}"',
    f"sudo cp -i ~/VERA/agent/sparr/managed-settings.json {AKTIV}",
    f"sudo chown root:wheel {AKTIV}",
    f"sudo chmod 644 {AKTIV}",
    f"{SUMMA} {INSTALLERAD_VAKT_CITERAD} {AKTIV} ~/VERA/agent/requirements.txt",
    'ls -lde@ / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"',
    f'ls -lde@ {MAPP}/vera" {INSTALLERAD_VAKT_CITERAD} {AKTIV}',
    f'ls -lde@ {INSTALLERAD_PYTHON}" {INSTALLERAD_PYTHON}/bin" {INSTALLERAD_PYTHON}/bin/python"',
    "shasum -a 256 ~/VERA/agent/sparr/kontrollera-skalet.zsh",
    "source ~/VERA/agent/sparr/kontrollera-skalet.zsh",
    "ls; ls",
    "git status",
    f"{PYTHON} -q scripts/tests",
    "sudo ls",
    f'sudo mv {INSTALLERAD_VAKT_CITERAD} {MAPP}/vera/kommandosparr.py.av"',
    f'sudo mv {MAPP}/vera/kommandosparr.py.av" {INSTALLERAD_VAKT_CITERAD}',
    f"{SUMMA} {INSTALLERAD_VAKT_CITERAD} {AKTIV}",
    "date",
]


def _kodrader(text):
    """Alla rader i alla kodrutor, i ordning, med eller utan språk efter ```."""
    rader = []
    i_ruta = False
    for rad in text.splitlines():
        if rad.strip().startswith("```"):
            i_ruta = not i_ruta
        elif i_ruta and rad.strip():
            rader.append(rad.strip())
    assert not i_ruta, "en kodruta stängs inte"
    return rader


def _lopande_text(text):
    """Alla rader utanför kodrutorna."""
    rader = []
    i_ruta = False
    for rad in text.splitlines():
        if rad.strip().startswith("```"):
            i_ruta = not i_ruta
        elif not i_ruta:
            rader.append(rad)
    return rader


@pytest.mark.parametrize(
    "rubrik,forvantade",
    [
        (PROVKORNING_RUBRIK, PROVKORNINGEN),
        (BYTE_RUBRIK, BYTET),
        (SPARRPROV_RUBRIK, SPARRPROVET),
        (UTANFOR_RUBRIK, UTANFOR),
    ],
    ids=["provkorningen", "bytet", "sparrprovet", "utanfor"],
)
def test_avsnitten_for_steg_15_har_exakt_de_har_kommandona_i_den_har_ordningen(rubrik, forvantade):
    assert _kodrader(_avsnitt(rubrik)) == forvantade


def test_resten_av_filen_har_exakt_de_har_raderna_i_den_har_ordningen():
    assert _kodrader(installera_utan_sandlada()) == RESTEN


def test_filen_har_de_avsnitten_i_ordning_och_inga_andra_rutor():
    text = INSTALLERA.read_text(encoding="utf-8")
    platser = [text.index(r) for r in (PROVKORNING_RUBRIK, BYTE_RUBRIK, SPARRPROV_RUBRIK, UTANFOR_RUBRIK, "## Caspers dator")]
    assert platser == sorted(platser)
    # Allt mellan rubrikerna räknas, så ett nytt avsnitt med kommandon kan inte smita förbi.
    assert len(_kodrader(text)) == len(RESTEN) + len(PROVKORNINGEN) + len(BYTET) + len(SPARRPROVET) + len(UTANFOR)


@pytest.mark.parametrize(
    "text",
    [
        "2.1.305",
        "managed-settings.fore-sandladan.json",
        "scripts/tests/test_sandladan.py",
        "Backa till förra versionen",
        FORE_STEG_15,
        "Avsluta alla öppna sessioner",
        "också i sessioner som redan är öppna",
        "Git kan inte göra en commit i sandlådan, och det är rätt",
        "Sandbox settings are overridden by a higher-priority configuration",
    ],
)
def test_installera_har_version_kopia_kontroll_och_backning(text):
    assert text in _byte_avsnittet()


def test_byte_avsnittet_har_inte_kvar_det_som_aterkallats():
    avsnitt = _byte_avsnittet()
    for text in ("avsmalnade", "fliken Config", "Denied within allowed", "`git add` och `git commit` på riktigt"):
        assert text not in avsnitt
    assert "~/VERA/agent/.venv/**" not in INSTALLERA.read_text(encoding="utf-8")


def test_avsluta_sessioner_star_fore_kopieringen():
    # Granskning 34, P8: nya inställningar når också sessioner som redan är öppna.
    avsnitt = _byte_avsnittet()
    assert avsnitt.index("Avsluta alla öppna sessioner") < avsnitt.index("**4. Kopiera den nya versionen.**")


def test_summan_i_bytet_ar_den_nya_filens_summa():
    summa = hashlib.sha256(INSTALLNINGAR.read_bytes()).hexdigest()
    assert _byte_avsnittet().count(summa) == 2


def test_provkorningen_har_samma_nycklar_som_filen_ocksa_filesystem():
    # Hette ..._utom_filesystem före Hugos beslut 2026-11-05 om granskning 39, beslut 2.
    assert json.loads(PROVKORNINGENS_NYCKLAR) == {"sandbox": _installningar()["sandbox"]}


@pytest.mark.parametrize(
    "text",
    [
        "GRUPP D HOPPAS ÖVER",
        "varje gång vakten eller de låsta inställningarna ändras",
        "i en kopia av en granskad commit",
        "Hugos beslut 2026-11-05 efter P6, beslut 1 och 3",
    ],
)
def test_prov_utanfor_sandladan_sager_vad_som_galler(text):
    assert text in _avsnitt(UTANFOR_RUBRIK)


def test_efter_p6_beslut_1_prov_utanfor_sandladan_galler_bara_grupp_d():
    avsnitt = _avsnitt(UTANFOR_RUBRIK)
    assert "bara grupp D" in avsnitt
    assert "test_h1_" not in avsnitt and "H1-PROVET HOPPAS ÖVER" not in avsnitt
    assert "inte avgjort" not in avsnitt


@pytest.mark.parametrize(
    "text",
    [
        "**d. Kör H1-proven i skrivbordsappen",
        "`31 passed`",
        "H1-PROVET HOPPAS ÖVER",
        "backa inte",
        "sandlådan fungerar då ändå",
        "nytt beslut",
        "Hugos beslut 2026-11-05 efter P6, beslut 1",
    ],
)
def test_efter_p6_beslut_1_sparrprovet_kor_h1_proven_i_appen(text):
    assert text in _avsnitt(SPARRPROV_RUBRIK)


def test_efter_p6_beslut_1_h1_proven_kommer_efter_provet_i_appen_och_fore_kopian_tas_bort():
    avsnitt = _avsnitt(SPARRPROV_RUBRIK)
    platser = [
        avsnitt.index(text)
        for text in (
            "**c. Kör samma prov i skrivbordsappen.**",
            "**Är något rött i b eller c:",
            "**d. Kör H1-proven i skrivbordsappen",
            "Arkivera sessionen efteråt.",
            "**e. Ta bort kopian, i Terminal.**",
        )
    ]
    assert platser == sorted(platser)


def test_efter_p6_beslut_1_provkorningen_och_bytet_sager_var_h1_proven_kors():
    assert "Orsaken är inte fastställd" not in _avsnitt(PROVKORNING_RUBRIK)
    assert 'De körs i appen, se "Spärrprovet i kopian", punkt d.' in _avsnitt(PROVKORNING_RUBRIK)
    assert "`H1-PROVET HOPPAS ÖVER` kan stå" not in _byte_avsnittet()
    assert "Står `H1-PROVET HOPPAS ÖVER` där: backa inte" in _byte_avsnittet()


def test_efter_p6_beslut_2_installera_sager_samma_version_som_filen():
    text = INSTALLERA.read_text(encoding="utf-8")
    assert '`"requiredMinimumVersion": "2.1.305"`' in text
    assert "En Claude Code som är äldre än 2.1.305 startar inte alls." in text
    # 2.1.295 står bara kvar som dokumentationens krav för onFailure, inte som det filen kräver.
    kvar = [rad for rad in text.splitlines() if "2.1.295" in rad]
    assert len(kvar) == 2
    assert kvar[0].startswith("**Claude Code version 2.1.295 eller senare**")
    assert "Requires Claude Code v2.1.295 or later" in kvar[1]


def test_efter_p6_besluten_star_ordagrant_i_granskning():
    avsnitt = GRANSKNING.read_text(encoding="utf-8").split("## Hugos beslut 2026-11-05 efter P6", 1)[1]
    for text in (
        "1. H1-proven hoppas över i Terminal, inte på grund av sandlådan. Beslut 3 om granskning 34 ändras för dem: "
        "H1-proven körs i appen, som är där märkningen sätts och där vakten används. Spärrprovet efter installationen "
        "kontrollerar i appen, inne i sandlådan, att H1-proven går igenom och inte hoppas över. Hoppas de över där behövs "
        "ett nytt beslut. Grupp D körs fortfarande utanför sandlådan i Terminal.",
        "2. requiredMinimumVersion höjs till 2.1.305.",
        "3. Proven utanför sandlådan körs i en kopia av en granskad commit, inte i projektmappen, eftersom de körs med "
        "Hugos fulla rättigheter.",
    ):
        assert text in avsnitt, text


@pytest.mark.parametrize(
    "text",
    [
        "backar du direkt",
        "SPÄRRPROVET I KOPIAN HOPPAS ÖVER",
        "SPÄRRTESTET HOPPAS ÖVER",
        "`.git/commondir`",
        "byta namn på `.git`",
        "projektets riktiga `.git`",
    ],
)
def test_sparrprovet_sager_vad_som_galler(text):
    assert text in _avsnitt(SPARRPROV_RUBRIK)


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05 om granskning 35.

GRANSKNING_35_BESLUT = [
    "1. P1: testet test_sparr_kopian_arbetsmappen_gar_inte_att_flytta (från provkörningen) läggs in i "
    "scripts/tests/test_sandladan.py.",
    "2. P2: Hugo har satt git config --global safe.bareRepository explicit (2026-11-05). INSTALLERA.md kontrollerar att "
    "den är satt före installationen.",
    "3. P3: varje session börjar och slutar med git status --short --ignored.",
    "4. P4: inga sessioner i worktrees tills det finns ett prov för det. Hugo har städat den gamla arbetskopian 2026-11-05 "
    "(mappen till papperskorgen, git worktree prune, grenen borttagen med git branch -d).",
    "5. P11: är ett H1-prov rött i appen: backa inte, men stanna. Kör inga sessioner tills det är avgjort. Det avgörs av "
    "en session som bara läser, som Hugo startar, och som bara tittar på det provet.",
    "6. P12: när sandlådan är installerad skriver Hugo alltid själv samma fasta kommandon: git status --short --ignored, "
    "git add -A och git commit -F COMMIT_MSG.txt. Sessionen skriver bara commit-meddelandet i filen COMMIT_MSG.txt i "
    'projektmappen, och skriver aldrig ett kommando som Hugo ska klistra in. Det ersätter delen om "färdiga kommandon" i '
    "beslut 2 om granskning 34. COMMIT_MSG.txt står i .gitignore.",
    "7. P13: CLAUDE.md ska säga att grupp D körs utanför sandlådan i en kopia av en granskad commit.",
    "8. P9: INSTALLERA.md får bara ha kommandon i vanliga kodrutor (```). Testerna stoppar ~~~-rutor, indragna kodrader "
    "och kodrutor i citat.",
    "9. P14 och Öppet 62 (Git LFS) står kvar under Öppet. Git LFS låts vara tills Hugo vet om något annat repo använder det.",
    "10. SPEC 7.1: 2.1.295 blir 2.1.305, och de två meningarna i Öppet 58 rättas, som en del av den här versionen.",
    "11. Provkörningen 2026-11-05, del E (Terminal, Claude Code 2.1.318, ~/VERA/agent, hela sandlådan med --settings): "
    "4683 passed, 47 skipped, 0 failed. De överhoppade: 30 spärrprov i kopian, 9 spärrtestet (sandlådan inte installerad), "
    "6 H1-prov (Terminal), 2 grupp D.",
]


@pytest.mark.parametrize("beslut", GRANSKNING_35_BESLUT, ids=[str(n) for n in range(1, 12)])
def test_granskning_35_besluten_star_ordagrant_i_granskning(beslut):
    avsnitt = GRANSKNING.read_text(encoding="utf-8").split("## Hugos beslut 2026-11-05 om granskning 35", 1)[1]
    assert beslut in avsnitt


def _del_e_star_under_steg_15(progress):
    """Sant om ett avsnitt "## Läge", var som helst i filen, hör till steg 15 och har raden om del E (granskning 36, P5)."""
    del_e = GRANSKNING_35_BESLUT[10].split(" ", 1)[1]
    avsnitt = (del_.split("\n## ", 1)[0] for del_ in progress.split("\n## Läge")[1:])
    return any("Steg i byggplanen: 15" in text and del_e in text for text in avsnitt)


def test_granskning_35_del_e_star_i_progress_under_steg_15():
    assert _del_e_star_under_steg_15(PROGRESS.read_text(encoding="utf-8"))


# P1: testet ligger i filen, och antalen i INSTALLERA.md stämmer med testerna (granskning 35, P6).


def _insamlade_sparrprov():
    """Namnen på spärrproven i den här filen, som pytest samlar in dem. Kör inga tester och skriver inget."""
    svar = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q", "-k", "test_sparr_", __file__],
        cwd=PROJEKTET,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert svar.returncode == 0, svar.stdout + svar.stderr
    return [rad for rad in svar.stdout.splitlines() if "::test_sparr_" in rad]


def test_granskning_35_p1_antalen_i_installera_stammer_med_testerna():
    prov = _insamlade_sparrprov()
    assert any("::test_sparr_kopian_arbetsmappen_gar_inte_att_flytta" in rad for rad in prov)
    i_kopian = [rad for rad in prov if "::test_sparr_kopian_" in rad]
    assert (len(prov), len(i_kopian), len(prov) - len(i_kopian)) == (41, 31, 10)


@pytest.mark.parametrize(
    "rubrik,text",
    [
        # 41 spärrprov och två texttest. Hugos beslut 2026-11-06, beslut 5, och testet som räknar alla filtret väljer nedan.
        (SPARRPROV_RUBRIK, "`43 passed`"),
        (SPARRPROV_RUBRIK, "flytta hela arbetsmappen"),
        (SPARRPROV_RUBRIK, "`31 passed`"),
        (PROVKORNING_RUBRIK, "`85 skipped`"),
        (PROVKORNING_RUBRIK, "`GRUPP D HOPPAS ÖVER`: **38** prov"),
        (PROVKORNING_RUBRIK, "`SPÄRRTESTET HOPPAS ÖVER`: **10** prov"),
        (PROVKORNING_RUBRIK, "`SPÄRRPROVET I KOPIAN HOPPAS ÖVER`: **31** prov"),
        (PROVKORNING_RUBRIK, "2.1.318"),
        (BYTE_RUBRIK, "**69** överhoppade"),
        (BYTE_RUBRIK, "**71** om `~/.ssh` inte finns"),
        (BYTE_RUBRIK, "`GRUPP D HOPPAS ÖVER` (38 prov)"),
    ],
)
def test_granskning_35_p1_installera_har_vantade_antal(rubrik, text):
    assert text in _avsnitt(rubrik)


def test_granskning_35_p1_installera_namner_inte_den_gamla_provkorningens_version():
    assert "2.1.314" not in INSTALLERA.read_text(encoding="utf-8")


# P2: INSTALLERA.md kontrollerar git-inställningen före installationen.


def test_granskning_35_p2_bytet_kontrollerar_git_installningen_forst():
    avsnitt = _byte_avsnittet()
    assert avsnitt.index(f"```bash\n{SAFE_BARE}\n```") < avsnitt.index("**1. Version.**")
    assert "Väntat: exakt `explicit`" in avsnitt
    assert "stoppa och fråga" in avsnitt.split(SAFE_BARE, 1)[1].split("**1. Version.**", 1)[0]
    assert "granskning 35, beslut 2" in avsnitt


def test_granskning_35_p2_caspers_dator_gor_samma_kontroll():
    avsnitt = _avsnitt("## Caspers dator")
    assert "`safe.bareRepository`" in avsnitt and "`explicit`" in avsnitt


# P4: inga sessioner i worktrees. Kontrollen efter installationen startar annars en.


def test_granskning_35_p4_kontrollen_startar_ingen_session_i_en_worktree():
    avsnitt = _avsnitt("## Kontroll efter installationen")
    assert "Hoppa över det här steget tills det finns ett prov för worktrees" in avsnitt
    assert avsnitt.index("Hoppa över det här steget") < avsnitt.index("Starta en ny session i en worktree")


# P11: ett rött H1-prov.


def test_granskning_35_p11_installera_sager_vad_ett_rott_h1_prov_betyder():
    avsnitt = _avsnitt(SPARRPROV_RUBRIK)
    assert "**Är ett H1-prov rött: backa inte, men stanna. Kör inga sessioner tills det är avgjort.**" in avsnitt
    assert "Det avgörs av en session som bara läser, som du startar, och som bara tittar på det provet" in avsnitt
    assert "granskning 35, beslut 5" in avsnitt
    assert "backa inte heller, men stanna och fråga" not in avsnitt


# P12: Hugo skriver de fasta kommandona själv, och sessionen skriver bara meddelandet.


def test_granskning_35_p12_installera_har_de_fasta_kommandona():
    avsnitt = _byte_avsnittet()
    assert "skriver aldrig ett kommando som du ska klistra in" in avsnitt
    assert "`COMMIT_MSG.txt`" in avsnitt
    assert "färdiga kommandon" not in avsnitt


def test_granskning_35_p12_commit_msg_star_i_gitignore():
    assert "COMMIT_MSG.txt" in GITIGNORE.read_text(encoding="utf-8").splitlines()


# P3, P4, P11, P12 och P13 i CLAUDE.md.


@pytest.mark.parametrize(
    "text",
    [
        "Varje session börjar och slutar med `git status --short --ignored -uall`",
        "Inga sessioner i worktrees tills det finns ett prov för det",
        "Är ett H1-prov rött i appen: backa inte, men stanna. Kör inga sessioner tills det är avgjort.",
        "Det avgörs av en session som bara läser, som Hugo startar, och som bara tittar på det provet",
        "Sessionen skriver bara commit-meddelandet i filen `COMMIT_MSG.txt` i projektmappen",
        "skriver aldrig ett kommando som Hugo ska klistra in",
        "`git status --short --ignored -uall`, `git add -A`, `ls -l COMMIT_MSG.txt`, `cat COMMIT_MSG.txt` och "
        "`git commit -F COMMIT_MSG.txt`",
        "Hugo kör dem utanför sandlådan, i Terminal, i en kopia av en granskad commit",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 3",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 4",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 5",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 6",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 7",
    ],
)
def test_granskning_35_star_i_claude_md(text):
    assert text in CLAUDE_MD.read_text(encoding="utf-8")


@pytest.mark.parametrize("text", ["färdiga kommandon", "git commit -m", "med namngivna filer"])
def test_granskning_35_p12_claude_md_har_inte_kvar_det_som_ersatts(text):
    assert text not in CLAUDE_MD.read_text(encoding="utf-8")


# Beslut 10: SPEC 7.1.


def _spec_7_1():
    return SPEC.read_text(encoding="utf-8").split("### 7.1 Fast kommandolista", 1)[1].split("\n---\n", 1)[0]


def test_granskning_35_beslut_10_spec_7_1_sager_den_nya_versionen():
    avsnitt = _spec_7_1()
    assert "2.1.295" not in avsnitt
    assert "(minst 2.1.305)" in avsnitt
    assert "Filen kräver Claude Code 2.1.305 eller senare" in avsnitt


def test_granskning_35_beslut_10_spec_7_1_har_de_tva_ratta_meningarna():
    avsnitt = _spec_7_1()
    assert "ett test kontrollerar att de är samma, i samma ordning, som i inställningarna" in avsnitt
    assert "sandlådan stoppar en egen testfil bara utanför projektet" in avsnitt
    # Med -uall sedan Hugos beslut 2026-11-05 om granskning 38, SPEC 7.1.
    assert "`git status --short --ignored -uall`" in avsnitt


# P9: INSTALLERA.md har bara kommandon i vanliga kodrutor.

LISTPUNKT = re.compile(r"(?:[-*+]|\d+[.)]) +")
CITAT = re.compile(r"(?: {0,3}> ?)+")
ANDRA_RUTOR = ("~~~", "<pre", "<code")


def _otillatna_rutor(text):
    """Rader som visas som en grå ruta utan att vara en vanlig kodruta, och som kontrollen av kommandon annars inte ser.

    Det är ~~~-rutor, indragna kodrader och kodrutor i citat (Hugos beslut 2026-11-05 om granskning 35, beslut 8), och
    <pre> och <code>, som visas på samma sätt. En vanlig ruta får vara indragen under en listpunkt. En indragen rad räknas
    som kodrad om den inte fortsätter ett stycke och inte står exakt där texten i en öppen listpunkt börjar."""
    fel = []
    i_ruta = False
    i_stycke = False
    listor = []
    for rad in text.splitlines():
        ren = rad.strip()
        if ren.startswith("```"):
            i_ruta = not i_ruta
            i_stycke = False
            continue
        if i_ruta:
            continue
        if not ren:
            i_stycke = False
            continue
        innehall = rad.lstrip(" ")
        indrag = len(rad) - len(innehall)
        citat = CITAT.match(rad)
        if citat:
            inuti = rad[citat.end():]
            if inuti.strip().startswith(("```", *ANDRA_RUTOR)) or inuti.startswith(("    ", "\t")):
                fel.append(rad)
            i_stycke = True
            continue
        if innehall.startswith("\t") or innehall.lower().startswith(ANDRA_RUTOR):
            fel.append(rad)
        listpunkt = LISTPUNKT.match(innehall)
        if not i_stycke or listpunkt:
            while listor and indrag < listor[-1]:
                listor.pop()
        if not i_stycke and indrag >= 4 and indrag not in listor:
            fel.append(rad)
        if listpunkt:
            listor.append(indrag + listpunkt.end())
        i_stycke = not innehall.startswith(("#", "|"))
    return fel


def test_granskning_35_p9_filen_har_bara_vanliga_kodrutor():
    assert _otillatna_rutor(INSTALLERA.read_text(encoding="utf-8")) == []


def test_granskning_35_p9_filen_har_bara_varningen_som_citat():
    text = INSTALLERA.read_text(encoding="utf-8")
    citat = [rad for rad in _lopande_text(text) if CITAT.match(rad)]
    assert citat[0] == "> **Varning: kör inte installerarens förslag.** När Claude Code installerades föreslog installeraren"
    assert len(citat) == 15


def test_granskning_35_p9_indragna_listor_och_rutor_i_listor_ar_tillatna():
    text = (
        "1. Punkt\n\n   Fortsätter\n\n   ```bash\n   kommando\n   ```\n\n"
        "10. Punkt\n    fortsätter\n\n    Fortsätter\n\n    - Under\n\n      Fortsätter\n"
    )
    assert _otillatna_rutor(text) == []


P9_FORMER = {
    "tilde": "~~~\n{k}\n~~~",
    "tilde_bash": "~~~bash\n{k}\n~~~",
    "tilde_i_lista": "- Punkt\n\n  ~~~\n  {k}\n  ~~~",
    "indragen": "    {k}",
    "indragen_tabb": "\t{k}",
    "indragen_i_lista": "- Punkt\n\n      {k}",
    "citat": "> ```\n> {k}\n> ```",
    "citat_bash": "> ```bash\n> {k}\n> ```",
    "citat_tilde": "> ~~~\n> {k}\n> ~~~",
    "citat_indragen": ">     {k}",
    "pre": "<pre>{k}</pre>",
}
P9_PLATSER = [
    PROVKORNING_RUBRIK,
    BYTE_RUBRIK,
    SPARRPROV_RUBRIK,
    UTANFOR_RUBRIK,
    "## Steg 7: kopiera vakten",
    "## Caspers dator",
]


@pytest.mark.parametrize("sida", ["fore", "efter"])
@pytest.mark.parametrize("plats", P9_PLATSER, ids=["provkorningen", "bytet", "sparrprovet", "utanfor", "steg_7", "casper"])
@pytest.mark.parametrize("form", P9_FORMER)
@pytest.mark.parametrize("kommando", ["okant-kommando --flagga", "rm ~/VERA/agent/SPEC.md"], ids=["okant", "rm"])
def test_granskning_35_p9_kommando_utanfor_vanlig_ruta_ger_rott(kommando, form, plats, sida):
    # Mutationen i minnet. Provet med den riktiga filen i en kopia står i PROGRESS.md.
    text = INSTALLERA.read_text(encoding="utf-8")
    assert plats in text
    tillagg = "\n\n" + P9_FORMER[form].format(k=kommando) + "\n\n"
    ny = text.replace(plats, tillagg + plats if sida == "fore" else plats + tillagg, 1)
    assert _otillatna_rutor(ny)


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05 om granskning 36.

GRANSKNING_36_BESLUT = [
    '- P1: Ja. Ett fjärde fast kommando före commit: ls -l COMMIT_MSG.txt. Raden ska börja med "-". Börjar den med "l" '
    "(länk) eller något annat: committa inte, stanna.",
    "- P2: Ja. .gitignore görs snävare så att den inte tar kodfiler, plus ett test som larmar om en kodfil ignoreras.",
    '- P3: Ja. CLAUDE.md får ett väntat läge för git status --short --ignored och en stoppregel. Löftet "kan inte gömma '
    'sig" tas bort eller skrivs om så att det stämmer.',
    "- P4: Kontrollerat av Hugo 2026-11-05 med git config --global --name-only --list. Namnen: user.name, user.email, "
    "filter.lfs.clean, filter.lfs.smudge, filter.lfs.process, filter.lfs.required, safe.barerepository. Ingen "
    "core.hooksPath. Stängd utan fynd.",
    "- P5: Rättas.",
    "- P6 och öppen fråga 3: Ja. Spärrprovet skapar ~/.ssh med en testfil, prövar läsförbudet och tar bort mappen efteråt.",
    "- Öppen fråga 1: Ja. Kommandon i löpande text i INSTALLERA.md flyttas till kodrutor.",
    "- Öppen fråga 2: git add och git commit står kvar i vaktens lista till nästa version av vakten. Läggs under Öppet.",
    "- Rättelserna görs före installationen.",
]


@pytest.mark.parametrize("beslut", GRANSKNING_36_BESLUT, ids=[str(n) for n in range(1, 10)])
def test_granskning_36_besluten_star_ordagrant_under_granskning_36(beslut):
    # Hugos beslut 2026-11-05 om granskning 37, P1: en ny rubrik efter granskning 36 är väntad.
    avsnitt = GRANSKNING.read_text(encoding="utf-8").split("## Granskning 36 (av ed6b847 och 2572b0f)", 1)[1].split("\n## ", 1)[0]
    assert beslut in avsnitt.split("### Hugos beslut 2026-11-05 om granskning 36", 1)[1]


# P1: ls -l COMMIT_MSG.txt före commiten, på varje plats som listar de fasta kommandona.

# Historik, där de gamla kommandona får stå kvar som de stod när de skrevs. Också BYGGPLAN.md, där varje session skriver om
# sitt läge (Hugos beslut 2026-11-05 om granskning 37, A).
HISTORIK = {"GRANSKNING.md", "PROGRESS.md", "BYGGPLAN.md"}
COMMITEN = "git commit -F COMMIT_MSG.txt"
LS_KOMMANDOT = "ls -l COMMIT_MSG.txt"


def _platser_med_de_fasta_kommandona():
    filer = [*PROJEKTET.glob("*.md"), *(PROJEKTET / "sparr").glob("*.md")]
    return {f.name: f.read_text(encoding="utf-8") for f in filer if f.name not in HISTORIK and COMMITEN in f.read_text(encoding="utf-8")}


def test_granskning_36_p1_platserna_ar_de_vantade():
    assert set(_platser_med_de_fasta_kommandona()) == {"CLAUDE.md", "INSTALLERA.md"}


@pytest.mark.parametrize("plats", ["CLAUDE.md", "INSTALLERA.md"])
def test_granskning_36_p1_ls_star_fore_commiten_med_regeln(plats):
    text = _platser_med_de_fasta_kommandona()[plats]
    assert LS_KOMMANDOT in text
    assert text.index(LS_KOMMANDOT) < text.index(COMMITEN)
    assert "ska börja med `-`" in text
    assert "Börjar den med `l` (en länk) eller något annat: committa inte, stanna" in text


def test_granskning_36_p1_i_installera_star_regeln_vid_rutan_och_fyra_kommandon_i_ordning():
    # Fem kommandon sedan Hugos beslut 2026-11-05 om granskning 39, beslut 3.
    avsnitt = _byte_avsnittet()
    assert "samma fem kommandon" in avsnitt and "samma fyra kommandon" not in avsnitt
    rader = _kodrader(avsnitt)
    start = rader.index(HUGOS_FASTA_KOMMANDON[0])
    assert rader[start:start + 5] == HUGOS_FASTA_KOMMANDON
    efter_ls = avsnitt.split(f"```bash\n   {LS_KOMMANDOT}\n   ```", 1)[1].split("```bash", 1)[0]
    assert "committa inte, stanna" in efter_ls


# P2: .gitignore tar inga kodfiler, och reglerna för riktiga underlag och hemligheter är lika starka som förut.

KODFILER = (".py", ".md", ".json")
# Reglerna som fanns före granskning 36. Ingen av dem får försvinna.
REGLER_FORE_GRANSKNING_36 = """
inkorg/ arkiv/ forslag/ godkant/ arenden/ rapporter/ logg/
.env .env.* *.env *.pem *.key *.p12 *.pfx secrets/ hemligheter/ *secret* *credentials* *losenord* *lösenord* *token*
*api_key* *apikey*
*kontoutdrag* *kvitto* *kvitton* *z-rapport* *Z-rapport* *shop*and*go* *Shop*and*Go* *shopandgo* *ShopAndGo*
*.pdf *.jpg *.jpeg *.png *.heic *.se *.si *.sie
!testdata/**/*.pdf !testdata/**/*.jpg !testdata/**/*.jpeg !testdata/**/*.png !testdata/**/*.heic
.venv/ __pycache__/ *.pyc .pytest_cache/ .claude/settings.local.json COMMIT_MSG.txt .DS_Store
""".split()
# Allt som ska ignoreras också efter P2, också när det ligger i en mapp med kod.
SKA_IGNORERAS = [
    # Riktiga underlag med andra filändelser än .py, i projektroten och i mapparna med kod.
    "kontoutdrag.pdf",
    "kontoutdrag_2026.csv",
    "scripts/kontoutdrag.csv",
    "sparr/kontoutdrag.xlsx",
    "kontoutdrag.md",
    "kontoutdrag.json",
    "kontoutdrag.py",
    "kvitto.jpg",
    "kvitto.txt",
    "scripts/kvitto.csv",
    "scripts/kvitto.json",
    "scripts/tests/kvitto.md",
    "sparr/kvitto.md",
    "kvitton.xlsx",
    "scripts/kvitton/kvitto.py",
    "z-rapport-1.pdf",
    "Z-rapport.txt",
    "scripts/z-rapport.csv",
    "scripts/z-rapport.json",
    # Allt från gamla Shop and Go-projektet, också kod: inget företagsnamn får stå i kärnans kod.
    "shop and go.xlsx",
    "shop_and_go.md",
    "Shop-and-Go.txt",
    "shopandgo.csv",
    "ShopAndGo.json",
    "scripts/shop_and_go_import.py",
    "scripts/shopandgo.py",
    "sparr/ShopAndGo.py",
    # Mappar med utdata och underlag, också med .py i.
    "inkorg/kvitto.py",
    "scripts/inkorg/kvitto.py",
    "arkiv/x.py",
    "rapporter/x.md",
    "scripts/logg/x.py",
    # Hemligheter, också i .py: en nyckel i kod ska larma, inte följa med.
    ".env",
    "scripts/.env",
    "nyckel.pem",
    "credentials.json",
    "token.json",
    "scripts/credentials.py",
    "scripts/token.py",
    "scripts/secret_nyckel.py",
    "sparr/api_key.py",
    "scripts/losenord.py",
    # Inskannat och exporterat.
    "bokforing.se",
    "scripts/bokforing.sie",
    "faktura.pdf",
    # Verktyg.
    "scripts/__pycache__/x.pyc",
    "scripts/__pycache__/x.py",
    "COMMIT_MSG.txt",
    # En mapp med .py i namnet och ett ord om underlag är ingen kodfil (Hugos beslut 2026-11-05 om granskning 37, P2).
    "scripts/kontoutdrag.py/utdrag_2026.csv",
    "scripts/kontoutdrag.py/x.py",
    "sparr/kontoutdrag.py/utdrag.csv",
    "scripts/kvitto.py/kvitto.csv",
    "sparr/kvitto.py/kvitto.csv",
    "sparr/kvitto.py/x.py",
    "scripts/tests/kvitton.py/k.csv",
    "scripts/z-rapport.py/z.csv",
    "sparr/Z-rapport.py/z.csv",
    "scripts/shop and go.py/s.csv",
    "sparr/shopandgo.py/x.py",
]
SKA_FOLJA_MED = [
    "scripts/kvitto_flode.py",
    "scripts/tests/test_kvitto_saknas.py",
    "scripts/kontoutdrag_las.py",
    "scripts/z_rapport.py",
    "scripts/z-rapport.py",
    "sparr/kvitto_prov.py",
    "scripts/tests/delmapp/test_kvitton.py",
]


def _gitmiljo(tmp_path):
    """git i testets tillfälliga mapp, utan någon av Hugos inställningar. Mappen heter inte .git, eftersom sandlådan stoppar
    det namnet. Projektets .git används aldrig."""
    return {
        **os.environ,
        "GIT_DIR": str(tmp_path / "prov-repo"),
        "GIT_WORK_TREE": str(tmp_path / "arbetsmapp"),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
    }


def _provrepo(tmp_path, gitignore=None):
    """Ett repo i testets tillfälliga mapp, med projektets .gitignore. Ger arbetsmappen och miljön för git."""
    arbetsmapp = tmp_path / "arbetsmapp"
    arbetsmapp.mkdir(exist_ok=True)
    (arbetsmapp / ".gitignore").write_text(
        GITIGNORE.read_text(encoding="utf-8") if gitignore is None else gitignore, encoding="utf-8"
    )
    miljo = _gitmiljo(tmp_path)
    start = subprocess.run(
        [GIT, "init", "-q", "--template="], cwd=arbetsmapp, env=miljo, capture_output=True, text=True, timeout=60, check=False
    )
    assert start.returncode == 0, start.stderr
    return arbetsmapp, miljo


def _ignorerade(tmp_path, vagar, gitignore=None):
    """Vilka av sökvägarna som .gitignore tar enligt git check-ignore. Filerna behöver inte finnas."""
    arbetsmapp, miljo = _provrepo(tmp_path, gitignore)
    svar = subprocess.run(
        [GIT, "check-ignore", "--no-index", "-z", "--stdin"],
        cwd=arbetsmapp,
        env=miljo,
        input="\0".join(vagar) + "\0",
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    # 0: någon är ignorerad. 1: ingen är det. Annat: git gick inte att köra, och då säger provet ingenting.
    assert svar.returncode in (0, 1), svar.stderr
    return {v for v in svar.stdout.split("\0") if v}


def _kodfiler_i(rot):
    """Spårade och nya .py-, .md- och .json-filer i projektroten och under scripts/ och sparr/. Läser bara namnen."""
    filer = [p.name for p in Path(rot).iterdir() if p.is_file() and p.suffix in KODFILER]
    for mapp in ("scripts", "sparr"):
        for plats, mappar_, namn in os.walk(Path(rot) / mapp):
            mappar_[:] = [m for m in mappar_ if m != "__pycache__"]
            filer.extend(
                (Path(plats) / n).relative_to(rot).as_posix() for n in namn if Path(n).suffix in KODFILER
            )
    return filer


def test_granskning_36_p2_ingen_kodfil_i_projektet_ignoreras(tmp_path):
    # Larmet (P2): en ny fil med ett namn som .gitignore tar följer annars inte med git add -A, och inget sägs. Blir det här
    # testet rött: byt namn på filen. Är filen ett riktigt underlag ska den inte ligga här alls.
    filer = _kodfiler_i(PROJEKTET)
    assert "scripts/tests/test_sandladan.py" in filer and "CLAUDE.md" in filer and "sparr/managed-settings.json" in filer
    assert _ignorerade(tmp_path, filer) == set()


def test_granskning_36_p2_larmet_ser_en_ny_fil(tmp_path):
    # Larmet prövat i en liten kopia av mappstrukturen: det hittar filen, och git säger att den ignoreras.
    rot = tmp_path / "projekt"
    for fil in ("scripts/kvitto_schema.json", "sparr/token_prov.py", "scripts/tests/credentials.md", "kvitto_noter.md", "SPEC.md"):
        (rot / fil).parent.mkdir(parents=True, exist_ok=True)
        (rot / fil).write_text("", encoding="utf-8")
    filer = _kodfiler_i(rot)
    assert _ignorerade(tmp_path, filer) == {
        "scripts/kvitto_schema.json",
        "sparr/token_prov.py",
        "scripts/tests/credentials.md",
        "kvitto_noter.md",
    }


@pytest.mark.parametrize("vag", SKA_FOLJA_MED)
def test_granskning_36_p2_kod_med_ord_ur_underlagsreglerna_foljer_med(tmp_path, vag):
    assert _ignorerade(tmp_path, [vag]) == set()


@pytest.mark.parametrize("vag", SKA_IGNORERAS)
def test_granskning_36_p2_underlag_och_hemligheter_ignoreras_som_forut(tmp_path, vag):
    assert _ignorerade(tmp_path, [vag]) == {vag}


def test_granskning_36_p2_ingen_gammal_regel_ar_borta():
    rader = GITIGNORE.read_text(encoding="utf-8").splitlines()
    for regel in REGLER_FORE_GRANSKNING_36:
        assert regel in rader, regel


def test_granskning_36_p2_undantaget_ar_bara_for_py_under_scripts_och_sparr():
    rader = [r for r in GITIGNORE.read_text(encoding="utf-8").splitlines() if r.startswith("!")]
    assert [r for r in rader if not r.startswith("!testdata/")] == ["!/scripts/**/*.py", "!/sparr/**/*.py"]


# P3: väntat läge och stoppregel, och inget löfte som inte håller.

# Räknat med kommandot i projektmappen 2026-11-05: 11 rader (Hugos beslut 2026-11-05 om granskning 37, P4).
VANTADE_IGNORERADE = [
    ".DS_Store",
    ".claude/.DS_Store",
    ".claude/worktrees/.DS_Store",
    ".pytest_cache/.gitignore",
    ".pytest_cache/CACHEDIR.TAG",
    ".pytest_cache/README.md",
    ".pytest_cache/v/cache/lastfailed",
    ".pytest_cache/v/cache/nodeids",
    "foretag/.DS_Store",
    "scripts/.DS_Store",
    "testdata/.DS_Store",
]
STOPPFILER = [".gitattributes", ".gitignore", ".lfsconfig", ".gitmodules"]


def _claude_md_stycket_om_git_status():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    return next(r for r in rader if r.startswith("- Varje session börjar och slutar med `git status --short --ignored -uall`"))


def _installera_stycket_om_git_status():
    return _byte_avsnittet().split("```bash\n   git status --short --ignored -uall\n   ```", 1)[1].split("```bash", 1)[0]


def test_granskning_36_p3_claude_md_har_inte_kvar_loftet():
    assert "gömma sig" not in CLAUDE_MD.read_text(encoding="utf-8")


def test_granskning_36_p3_claude_md_sager_vad_kommandot_visar_och_inte_visar():
    # Med -uall (Hugos beslut 2026-11-05 om granskning 37, P4) syns också det som kommandot förut inte visade.
    stycket = _claude_md_stycket_om_git_status()
    assert "Den visar varje fil för sig" in stycket
    assert "en ny fil i en mapp som redan är ignorerad syns inte" not in stycket
    assert "Tomma mappar syns inte" in stycket
    assert "Hugos beslut 2026-11-05 om granskning 36, P3" in stycket
    assert "Hugos beslut 2026-11-05 om granskning 37, P4" in stycket


@pytest.mark.parametrize("namn", [*VANTADE_IGNORERADE, "COMMIT_MSG.txt", *STOPPFILER])
def test_granskning_36_p3_claude_md_har_vantat_lage_och_stoppregel(namn):
    stycket = _claude_md_stycket_om_git_status()
    assert f"`{namn}`" in stycket
    assert "stanna och fråga" in stycket


@pytest.mark.parametrize("namn", [*VANTADE_IGNORERADE, "COMMIT_MSG.txt", *STOPPFILER])
def test_granskning_36_p3_installera_har_samma_vantade_lage(namn):
    stycket = _installera_stycket_om_git_status()
    assert f"`{namn}`" in stycket
    assert "stoppa och fråga" in stycket


def test_granskning_36_p3_installera_lovar_inte_att_allt_syns():
    assert "så att du ser vad som följer med" not in _byte_avsnittet()


# P5: testet av del E tål nya poster.


def test_granskning_36_p5_en_ny_post_overst_ger_inte_rott():
    text = PROGRESS.read_text(encoding="utf-8")
    ny = text.replace("\n## Läge", "\n## Läge 2099-01-01, påhittad post\n\nSteg i byggplanen: 99\n\n- Inget.\n\n## Läge", 1)
    assert ny != text
    assert _del_e_star_under_steg_15(ny)


def test_granskning_36_p5_raden_maste_finnas_och_hora_till_steg_15():
    text = PROGRESS.read_text(encoding="utf-8")
    del_e = GRANSKNING_35_BESLUT[10].split(" ", 1)[1]
    assert not _del_e_star_under_steg_15(text.replace(del_e, "Något annat."))
    assert not _del_e_star_under_steg_15(f"\n## Läge A\n\nSteg i byggplanen: 16\n\n- {del_e}\n")


# P6: läsförbudet för ~/.ssh, ur den riktiga inställningsfilen, och provet med en mapp för stunden.


def _ssh_mappen():
    """Mappen som läsförbudet gäller, läst ur sparr/managed-settings.json, inte en kopia här."""
    forbud = json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))["sandbox"]["filesystem"]["denyRead"]
    assert len(forbud) == 1 and forbud[0].startswith("~/"), forbud
    return HEM / forbud[0][2:]


def _lasning_stoppas(mapp, fil):
    """Listar mappen, läser filen och kör cat på den. Sant om allt stoppas. Visar aldrig vad som står i filen. None om mappen
    inte finns, och då säger provet ingenting."""
    try:
        os.listdir(mapp)
        return False
    except FileNotFoundError:
        return None
    except PermissionError:
        pass
    try:
        with open(fil, "rb"):
            return False
    except (FileNotFoundError, PermissionError):
        pass
    cat = subprocess.run(["/bin/cat", str(fil)], capture_output=True, timeout=30, check=False)
    return cat.returncode != 0 and cat.stdout == b""


def test_granskning_36_p6_forbudet_las_ur_installningsfilen(monkeypatch, tmp_path):
    assert _ssh_mappen() == HEM / ".ssh"
    assert "Read(~/.ssh/**)" in _installningar()["permissions"]["deny"]
    # Står något annat i filen ändras svaret, så det finns ingen kopia av förbudet i testet.
    annan = tmp_path / "installningar.json"
    annan.write_text(json.dumps({"sandbox": {"filesystem": {"denyRead": ["~/.annan"]}}}), encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "INSTALLNINGAR", annan)
    assert _ssh_mappen() == HEM / ".annan"


def test_granskning_36_p6_hjalpfunktionen_nar_inget_stoppar_eller_nar_allt_saknas(tmp_path):
    fil = tmp_path / "prov"
    fil.write_text("kassio-prov", encoding="utf-8")
    assert _lasning_stoppas(tmp_path, fil) is False
    assert _lasning_stoppas(tmp_path / "finns-inte", tmp_path / "finns-inte" / "prov") is None


def test_granskning_36_p6_hjalpfunktionen_nar_datorn_nekar(monkeypatch, tmp_path):
    def nekar(*_a, **_k):
        raise PermissionError(1, "Operation not permitted")

    with monkeypatch.context() as byte:
        byte.setattr(os, "listdir", nekar)
        byte.setattr(builtins, "open", nekar)
        byte.setattr(
            subprocess,
            "run",
            lambda *_a, **_k: subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr=b""),
        )
        svar = _lasning_stoppas(tmp_path, tmp_path / "prov")
    assert svar is True


def test_granskning_36_p6_hjalpfunktionen_sager_nej_nar_cat_far_lasa(monkeypatch, tmp_path):
    def nekar(*_a, **_k):
        raise PermissionError(1, "Operation not permitted")

    with monkeypatch.context() as byte:
        byte.setattr(os, "listdir", nekar)
        byte.setattr(builtins, "open", nekar)
        byte.setattr(
            subprocess,
            "run",
            lambda *_a, **_k: subprocess.CompletedProcess(args=[], returncode=0, stdout=b"kassio-prov", stderr=b""),
        )
        svar = _lasning_stoppas(tmp_path, tmp_path / "prov")
    assert svar is False


def test_granskning_36_p6_vakten_stoppar_cat_av_testfilen(vakt, mappar):
    # INSTALLERA.md säger att vakten stoppar agentens cat. Sandlådans eget förbud prövas därför av spärrtestet, inne i sandlådan.
    assert _bedom(vakt, mappar, "cat ~/.ssh/prov")


def test_granskning_36_p6_sparrtestet_kor_lasningen_ur_installningsfilen():
    kod = Path(__file__).read_text(encoding="utf-8").rsplit("def test_sparr_lasning_av_ssh_stoppas():", 1)[1]
    assert "_ssh_mappen()" in kod and "_lasning_stoppas(" in kod
    assert 'HEM / ".ssh"' not in kod


def test_granskning_36_p6_installera_skapar_provar_och_tar_bort():
    avsnitt = _avsnitt(SPARRPROV_RUBRIK)
    platser = [
        avsnitt.index(text)
        for text in (
            "```bash\nls -ld ~/.ssh\n```",
            "```bash\nmkdir -m 700 ~/.ssh\n```",
            "```bash\necho kassio-prov > ~/.ssh/prov\n```",
            "**b. Kör provet i Terminal:**",
            "**Pröva läsförbudet, i samma session",
            "`~/.ssh/prov` med verktyget Read",
            "```\ncat ~/.ssh/prov\n```",
            "**e. Ta bort kopian, i Terminal.**",
            "```bash\nrm ~/.ssh/prov\n```",
            "```bash\nrmdir ~/.ssh\n```",
        )
    ]
    assert platser == sorted(platser)


@pytest.mark.parametrize(
    "text",
    [
        "**Finns mappen: stoppa och fråga**",
        "**Väntat: båda stoppas, och texten `kassio-prov` visas inte.**",
        "**Visas `kassio-prov`: läsförbudet gäller inte.**",
        "`test_sparr_lasning_av_ssh_stoppas`",
        "Säger den `Directory not empty`: stoppa och fråga",
        "Hugos beslut 2026-11-05 om granskning 36, P6",
    ],
)
def test_granskning_36_p6_installera_sager_vad_som_galler(text):
    assert text in _avsnitt(SPARRPROV_RUBRIK)


def test_granskning_36_p6_sparrprovet_har_inte_kvar_provet_utan_mapp():
    avsnitt = _avsnitt(SPARRPROV_RUBRIK)
    assert "`39 passed, 1 skipped`" not in avsnitt and "läsförbudet är inte prövat" not in avsnitt


# Öppen fråga 1: kända kommandon står i kodrutor, inte i löpande text.

# Namn på ett kommando får stå i en förklaring ("`cp` kopierar en fil"). Ett kommando med något efter namnet får inte det.
KANDA_KOMMANDON = {"sudo", "rm", "cp", "mv", "chmod", "curl", "wget", "git", "ls", "cd", "echo", "~/.local/bin/claude"}
# Utanför bakåtfnuttar står också vanliga svenska meningar, så för git räknas bara git:s egna ord.
GIT_ORD = (
    "add|commit|status|log|diff|show|push|pull|fetch|merge|checkout|clone|config|archive|init|reset|rebase|stash|rm|mv|"
    "restore|switch|branch|tag|remote|worktree|gc|fsck|lfs|submodule|check-ignore|ls-files|rev-parse|-[^ ]*"
)
KOMMANDO_I_TEXT = re.compile(rf"\b(?:(?:sudo|rm|cp|mv|chmod|curl|wget|ls)\s+\S+|git\s+(?:{GIT_ORD})(?=[\s,.:;)]|$))")
# Vanliga ord efter sudo, i kontrollens steg 4, utan något kommando. Allt annat som börjar med ett av orden ger rött.
TILLATET_UTANFOR_FNUTTAR = {"sudo stoppas.**", "sudo och"}


def _stycken(rader):
    """Rader utanför kodrutorna, ihopsatta till stycken, eftersom ett avsnitt inom bakåtfnuttar kan löpa över två rader."""
    stycken = []
    aktuellt = []
    for rad in rader:
        if rad.strip():
            aktuellt.append(rad.strip())
        elif aktuellt:
            stycken.append(" ".join(aktuellt))
            aktuellt = []
    if aktuellt:
        stycken.append(" ".join(aktuellt))
    return stycken


def _kommandon_i_lopande_text(text):
    """Kommandon som står utanför kodrutorna, inom eller utom bakåtfnuttar."""
    traffar = []
    for stycke in _stycken(_lopande_text(text)):
        for avsnitt in re.findall(r"`([^`]+)`", stycke):
            delar = [d for d in re.split(r"[\s;]+", avsnitt) if d]
            if len(delar) >= 2 and delar[0] in KANDA_KOMMANDON or "-m pytest" in avsnitt:
                traffar.append(avsnitt)
        utan_fnuttar = re.sub(r"`[^`]*`", " ", stycke)
        traffar.extend(t.group(0) for t in KOMMANDO_I_TEXT.finditer(utan_fnuttar) if t.group(0) not in TILLATET_UTANFOR_FNUTTAR)
    return traffar


def test_granskning_36_oppen_fraga_1_inga_kanda_kommandon_i_lopande_text():
    assert _kommandon_i_lopande_text(INSTALLERA.read_text(encoding="utf-8")) == []


def test_granskning_36_oppen_fraga_1_namn_i_en_forklaring_ar_tillatna():
    text = "- `cp` kopierar en fil, `rm` raderar den och `git` visar läget. Den gör att git inte kör kod.\n"
    assert _kommandon_i_lopande_text(text) == []


OPPEN_FRAGA_1_RADER = [
    'sudo cp ~/x "/Library/Application Support/ClaudeCode/x"',
    "`sudo cp ~/x /Library/x`",
    "Kör `sudo cp` här.",
    "sudo mv a b",
    "sudo chmod -R 777 ~/VERA",
    "rm ~/VERA/agent/SPEC.md",
    "`rm -rf ~/VERA`",
    "cp ~/.zshrc.fore-vera ~/.zshrc",
    "`cp ~/.zshrc.fore-vera ~/.zshrc`",
    "mv a b",
    "chmod 777 x",
    "`chmod 777 x`",
    "curl https://example.invalid",
    "wget https://example.invalid",
    "git add x",
    "`git status`",
    "git config --global core.hooksPath .x",
    "`git config --global core.hooksPath .x`",
    "ls -l x",
    "`ls; ls`",
    "`~/.local/bin/claude --version`",
    "`cd ~/VERA/agent`",
    "`'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest scripts/tests`",
]


@pytest.mark.parametrize("rad", OPPEN_FRAGA_1_RADER)
@pytest.mark.parametrize(
    "plats", [PROVKORNING_RUBRIK, BYTE_RUBRIK, SPARRPROV_RUBRIK, UTANFOR_RUBRIK, "## Steg 7: kopiera vakten", "## Caspers dator"],
    ids=["provkorningen", "bytet", "sparrprovet", "utanfor", "steg_7", "casper"],
)
def test_granskning_36_oppen_fraga_1_kommando_i_lopande_text_ger_rott(rad, plats):
    # Mutationen i minnet. Provet med den riktiga filen i en kopia står i PROGRESS.md.
    text = INSTALLERA.read_text(encoding="utf-8")
    assert plats in text
    ny = text.replace(plats, f"{plats}\n\n{rad}\n", 1)
    assert _kommandon_i_lopande_text(ny)


# Öppen fråga 2 och de andra besluten i PROGRESS.md.


def test_granskning_36_oppen_fraga_2_star_under_oppet():
    oppet = PROGRESS.read_text(encoding="utf-8").split("\n## Öppet\n", 1)[1].split("\n## ", 1)[0]
    rad = next(r for r in oppet.splitlines() if r.startswith("64. "))
    assert "`git add` och `git commit`" in rad and "nästa version av vakten" in rad and "**Öppen.**" in rad


def test_granskning_36_vakten_och_installningarna_ar_oforandrade():
    # Rättelserna görs utan att ändra de låsta filerna. Kommandolistan i SPEC 7.1 står kvar med git add och git commit.
    assert hashlib.sha256(VAKTEN.read_bytes()).hexdigest() == VAKTENS_SUMMA
    assert hashlib.sha256(INSTALLNINGAR.read_bytes()).hexdigest() == "1ba7457615356ff634956cf3f665787d2e74900986aa96001feeaa8ce31a39da"
    for rad in ("| `git add` | Välja ut ändrade filer inför en commit |", "| `git commit` | Spara ändringarna i projektets historik (en **commit**) |"):
        assert rad in _spec_7_1()


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05 om granskning 37.

GRANSKNING_37_BESLUT = [
    "- P1: Rättas. Testet för granskning 36 får inte kräva att inget står efter rubriken.",
    "- P2: Ja till öppningen för .py-filer under scripts/ och sparr/. Ja till regler som bara gäller mappar, så att en mapp "
    "med .py i namnet och orden kontoutdrag, kvitto, kvitton, z-rapport eller Shop and Go ignoreras som förut.",
    '- P3: Ja. Raden från ls -l COMMIT_MSG.txt ska börja med "-" och antalet länkar (siffran efter rättigheterna) ska vara 1. '
    "Efter commiten och före push kör Hugo git show --stat HEAD och läser meddelandet och fillistan. Ser något fel ut: pusha "
    "inte, fråga. Spärrprovet prövar att sandlådan inte kan skapa en hård länk till testfilen i ~/.ssh, som ett uttalat "
    "undantag från länkregeln i CLAUDE.md, bara i spärrprovet.",
    "- P4: Ja. Kommandot blir git status --short --ignored -uall, med ett nytt väntat läge.",
    '- P5: Ja. Ett test skyddar orden "en annan rad med !!" i stoppregeln.',
    "- A: Inga tester får bero på vad som står sist i GRANSKNING.md, PROGRESS.md eller BYGGPLAN.md.",
    "- B: Granskning 38 prövar bara rättelserna från granskning 37. Nya fynd som inte blockerar installationen går till Öppet.",
]


def _avsnitt_i_granskning(rubrik):
    """Texten under rubriken i GRANSKNING.md, fram till nästa rubrik på samma nivå. Beror inte på vad som står efter (beslut A)."""
    return GRANSKNING.read_text(encoding="utf-8").split(rubrik, 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize("beslut", GRANSKNING_37_BESLUT, ids=["P1", "P2", "P3", "P4", "P5", "A", "B"])
def test_granskning_37_besluten_star_ordagrant_under_granskning_37(beslut):
    avsnitt = _avsnitt_i_granskning("## Granskning 37 (av abded14 och 420a57d)")
    assert beslut in avsnitt.split("### Hugos beslut 2026-11-05 om granskning 37", 1)[1]


# P2: reglerna som bara gäller mappar. Hålet var en mapp som slutar på .py, som undantaget för .py öppnade.

MAPPREGLER = ["*kontoutdrag*/", "*kvitto*/", "*kvitton*/", "*z-rapport*/", "*Z-rapport*/"]


def test_granskning_37_p2_reglerna_for_mappar_star_direkt_efter_undantaget():
    # Ordningen spelar roll: den sista regeln som passar gäller. Före undantaget skulle mappen släppas igenom igen.
    rader = GITIGNORE.read_text(encoding="utf-8").splitlines()
    plats = rader.index("!/sparr/**/*.py")
    assert rader[plats - 1] == "!/scripts/**/*.py"
    assert rader[plats + 1:plats + 1 + len(MAPPREGLER)] == MAPPREGLER


def test_granskning_37_p2_git_add_tar_inte_med_en_mapp_med_py_i_namnet(tmp_path):
    # Riktiga filer och riktig git add -A i testets tillfälliga mapp, aldrig i projektets .git.
    arbetsmapp, miljo = _provrepo(tmp_path)
    borta = [
        "scripts/kontoutdrag.py/utdrag_2026.csv",
        "scripts/kontoutdrag.py/x.py",
        "sparr/kvitto.py/kvitto.csv",
        "sparr/kvitto.py/x.py",
        "scripts/z-rapport.py/z.csv",
        "scripts/shop and go.py/s.csv",
    ]
    for fil in [*borta, "scripts/kvitto_flode.py"]:
        (arbetsmapp / fil).parent.mkdir(parents=True, exist_ok=True)
        (arbetsmapp / fil).write_text("x\n", encoding="utf-8")
    lagg_till = subprocess.run([GIT, "add", "-A"], cwd=arbetsmapp, env=miljo, capture_output=True, text=True, timeout=60, check=False)
    assert lagg_till.returncode == 0, lagg_till.stderr
    filer = subprocess.run([GIT, "ls-files", "-z"], cwd=arbetsmapp, env=miljo, capture_output=True, text=True, timeout=60, check=False)
    assert set(filer.stdout.split("\0")) - {""} == {".gitignore", "scripts/kvitto_flode.py"}


def test_granskning_37_p2_larmet_ser_en_kodfil_i_en_sadan_mapp(tmp_path):
    rot = tmp_path / "projekt"
    (rot / "scripts" / "kvitto.py").mkdir(parents=True)
    (rot / "scripts" / "kvitto.py" / "x.py").write_text("", encoding="utf-8")
    assert _ignorerade(tmp_path, _kodfiler_i(rot)) == {"scripts/kvitto.py/x.py"}


# P3: siffran 1, titten efter commiten och spärrprovet med en hård länk.

REGELN_OM_SIFFRAN = "antalet länkar (siffran efter rättigheterna) ska vara 1"
HARD_LANK_TEST = "test_sparr_hard_lank_till_ssh_stoppas"


@pytest.mark.parametrize("plats", ["CLAUDE.md", "INSTALLERA.md"])
def test_granskning_37_p3_varje_plats_har_regeln_om_siffran(plats):
    text = _platser_med_de_fasta_kommandona()[plats]
    assert REGELN_OM_SIFFRAN in text
    assert "ska börja med `-`" in text
    assert "Är siffran en annan än 1: committa inte, stanna" in text


@pytest.mark.parametrize("plats", ["CLAUDE.md", "INSTALLERA.md"])
def test_granskning_37_p3_varje_plats_har_titten_efter_commiten_och_fore_push(plats):
    text = _platser_med_de_fasta_kommandona()[plats]
    assert text.index(COMMITEN) < text.index(TITTEN_EFTER_COMMITEN)
    efter = text.split(COMMITEN, 1)[1]
    assert "före en push" in efter and "meddelandet och fillistan" in efter and "pusha inte, fråga" in efter
    assert "Hugos beslut 2026-11-05 om granskning 37, P3" in text


def test_granskning_37_p3_i_installera_star_titten_i_en_egen_ruta_efter_commiten():
    avsnitt = _byte_avsnittet()
    rader = _kodrader(avsnitt)
    start = rader.index(HUGOS_FASTA_KOMMANDON[0])
    assert rader[start:start + 6] == [*HUGOS_FASTA_KOMMANDON, TITTEN_EFTER_COMMITEN]
    efter = avsnitt.split(f"```bash\n   {TITTEN_EFTER_COMMITEN}\n   ```", 1)[1].split("```bash", 1)[0]
    assert "pusha inte, fråga" in efter


@pytest.mark.parametrize(
    "text",
    [
        "hård länk",
        f"`{HARD_LANK_TEST}`",
        "uttalat undantag från länkregeln i CLAUDE.md, bara i spärrprovet",
        "Hugos beslut 2026-11-05 om granskning 37, P3",
    ],
)
def test_granskning_37_p3_installera_har_sparrprovet_med_hard_lank(text):
    assert text in _avsnitt(SPARRPROV_RUBRIK)


def test_granskning_37_p3_claude_md_har_undantaget_bara_for_sparrprovet():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    stycket = next(r for r in rader if r.startswith("- Prov och test får bara skapa, ändra eller länka filer"))
    # Regeln står kvar, och undantaget gäller bara det testet.
    assert "Aldrig länkar (hårda eller mjuka) till något utanför de mapparna." in stycket
    assert "Uttalat undantag, bara i spärrprovet" in stycket
    assert f"`{HARD_LANK_TEST}`" in stycket and "`~/.ssh/prov`" in stycket
    assert "Hugos beslut 2026-11-05 om granskning 37, P3" in stycket


def test_granskning_37_p3_sparrtestet_provar_bara_testfilen_och_kraver_stopp():
    kod = Path(__file__).read_text(encoding="utf-8").rsplit(f"def {HARD_LANK_TEST}(tmp_path):", 1)[1]
    assert '_hard_lank_stoppas(_ssh_mappen() / "prov", tmp_path / "lank")' in kod
    assert "assert svar," in kod


def test_granskning_37_p3_hjalpfunktionen_nar_filen_saknas(tmp_path):
    assert _hard_lank_stoppas(tmp_path / "finns-inte" / "prov", tmp_path / "lank") is None


def test_granskning_37_p3_hjalpfunktionen_sager_nej_och_stadar_nar_inget_stoppar(tmp_path):
    fil = tmp_path / "prov"
    fil.write_text("kassio-prov", encoding="utf-8")
    assert _hard_lank_stoppas(fil, tmp_path / "lank") is False
    assert not (tmp_path / "lank").exists()
    assert fil.read_text(encoding="utf-8") == "kassio-prov"


def test_granskning_37_p3_hjalpfunktionen_sager_ja_nar_datorn_nekar(monkeypatch, tmp_path):
    def nekar(*_a, **_k):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(os, "link", nekar)
    assert _hard_lank_stoppas(tmp_path / "prov", tmp_path / "lank") is True


@pytest.mark.parametrize("kommando", [HUGOS_FASTA_KOMMANDON[0], TITTEN_EFTER_COMMITEN, LS_KOMMANDOT, "cat COMMIT_MSG.txt"])
def test_granskning_37_vakten_slapper_igenom_lasande_kommandon(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


# P4: -uall, på varje plats, och vad kommandot faktiskt visar.

NYTT_STATUS = HUGOS_FASTA_KOMMANDON[0]
GAMMALT_STATUS = re.compile(r"git status --short --ignored(?! -uall)")


def _gallande_dokument():
    filer = [*PROJEKTET.glob("*.md"), *(PROJEKTET / "sparr").glob("*.md")]
    return {f.name: f.read_text(encoding="utf-8") for f in filer if f.name not in HISTORIK}


def test_granskning_37_p4_varje_plats_har_uall():
    gamla = {namn: len(GAMMALT_STATUS.findall(text)) for namn, text in _gallande_dokument().items() if GAMMALT_STATUS.search(text)}
    # SPEC 7.1 är rättad (Hugos beslut 2026-11-05 om granskning 38). Ingen gammal form är kvar, och varje ny ger rött.
    assert gamla == {}
    assert {namn for namn, text in _gallande_dokument().items() if NYTT_STATUS in text} == {"CLAUDE.md", "INSTALLERA.md", "SPEC.md"}


# Hugos beslut 2026-11-05 om granskning 39, beslut 1: grupp D. Bara Operation not permitted hoppar över, från datorn eller i
# git:s felmeddelande. Allt annat ger rött, också Permission denied. Utanför sandlådan händer det inte, och kommandot i
# "Prov utanför sandlådan" visar det: där ska texten nedan inte stå.

OPERATION_NOT_PERMITTED = "Operation not permitted"


def _hoppa_over_grupp_d(orsak):
    pytest.skip(
        f"GRUPP D HOPPAS ÖVER: {orsak}, troligen sandlådan. Provet körs utanför sandlådan, se INSTALLERA.md, "
        '"Prov utanför sandlådan".'
    )


@contextlib.contextmanager
def _grupp_d_om_datorn_nekar():
    try:
        yield
    except PermissionError as fel:
        if fel.errno != errno.EPERM:
            raise
        _hoppa_over_grupp_d(f"datorn nekade: {fel}")


def _kontrollera_git(svar):
    """Git gick bra, eller nekades med Operation not permitted. Ett annat fel från git ger rött."""
    if svar.returncode != 0 and OPERATION_NOT_PERMITTED in svar.stderr:
        _hoppa_over_grupp_d(f"git nekades: {svar.stderr.strip()}")
    assert svar.returncode == 0, svar.stderr


def _status(tmp_path, *tillagg):
    with _grupp_d_om_datorn_nekar():
        arbetsmapp, miljo = _provrepo(tmp_path)
        for fil in (".pytest_cache/ny.py", ".venv/x.py", "ny/.gitattributes", "ny/.lfsconfig"):
            (arbetsmapp / fil).parent.mkdir(parents=True, exist_ok=True)
            (arbetsmapp / fil).write_text("x\n", encoding="utf-8")
        (arbetsmapp / "tom").mkdir()
    svar = subprocess.run(
        [GIT, "status", "--short", "--ignored", *tillagg], cwd=arbetsmapp, env=miljo, capture_output=True, text=True, timeout=60, check=False
    )
    _kontrollera_git(svar)
    return svar.stdout.splitlines()


def test_granskning_37_p4_uall_visar_varje_fil_for_sig(tmp_path):
    rader = _status(tmp_path, "-uall")
    for rad in ("!! .pytest_cache/ny.py", "!! .venv/x.py", "?? ny/.gitattributes", "?? ny/.lfsconfig"):
        assert rad in rader
    assert not any("tom" in rad for rad in rader), "CLAUDE.md säger att tomma mappar inte syns"


def test_granskning_37_p4_utan_uall_doljs_filerna(tmp_path):
    # Skälet till beslutet, granskning 37, P4: stoppregeln ser varken .gitattributes i en ny mapp eller nya filer i en ignorerad mapp.
    rader = _status(tmp_path)
    assert "?? ny/" in rader and "!! .pytest_cache/" in rader
    assert not any(".gitattributes" in rad or "ny.py" in rad for rad in rader)


# P5: orden i stoppregeln.


@pytest.mark.parametrize("stycket", [_claude_md_stycket_om_git_status, _installera_stycket_om_git_status], ids=["claude", "installera"])
@pytest.mark.parametrize("text", ["en annan rad med `!!`", "också när sessionen själv har ändrat filen", "i vilken mapp som helst"])
def test_granskning_37_p5_stoppregeln_har_orden(stycket, text):
    assert text in stycket()


# A: nya rubriker och poster i de tre filerna ger inte rött.

LASER_HISTORIKEN = {"test_byggplan_progress.py", "test_sandladan.py", "test_beslut_granskning_15.py", "test_beslut_granskning_23.py"}
LASNING_AV_HISTORIKEN = re.compile(r'"(?:GRANSKNING|PROGRESS|BYGGPLAN)[.]md"')
PAHITTAD_TEXT = "`git commit -F COMMIT_MSG.txt`, `git status --short --ignored` och rubriken `## Öppet`"


def test_granskning_37_a_listan_over_tester_som_laser_filerna_ar_hel():
    # Ett nytt test som läser filerna måste med i provet nedan.
    hittade = {
        f.name for f in Path(__file__).parent.glob("test_*.py") if LASNING_AV_HISTORIKEN.search(f.read_text(encoding="utf-8"))
    }
    assert hittade == LASER_HISTORIKEN


def _lagg_in(fil, plats, mitt_i, sist):
    text = fil.read_text(encoding="utf-8")
    assert plats in text
    fil.write_text(text.replace(plats, mitt_i + plats, 1) + sist, encoding="utf-8")


def test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path):
    # En kopia i testets tillfälliga mapp, med nya poster mitt i och sist i varje fil. Testerna som läser filerna körs där.
    # Hoppar över bara om datorn nekar själva kopian (Hugos beslut 2026-11-05 om granskning 39, beslut 1). Ett rött test i
    # kopian ger alltid rött här. De tester i kopian som sandlådan nekar hoppar över sig själva.
    rot = tmp_path / "kopia"
    with _grupp_d_om_datorn_nekar():
        rot.mkdir()
        for mapp in ("scripts", "sparr", "foretag", "testdata", "testforetag"):
            shutil.copytree(PROJEKTET / mapp, rot / mapp, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        for fil in (*PROJEKTET.glob("*.md"), GITIGNORE, PROJEKTET / "requirements.txt"):
            shutil.copy(fil, rot / fil.name)
        _lagg_in(
            rot / "GRANSKNING.md",
            "\n## Granskning 37 (av abded14",
            # Så höga nummer att de inte krockar med en verklig granskning, eftersom två med samma nummer ska ge rött.
            f"\n## Granskning 99998 (påhittad) (2099-01-01)\n\n{PAHITTAD_TEXT}\n",
            f"\n## Granskning 99999 (påhittad) (2099-01-01)\n\n{PAHITTAD_TEXT}\n",
        )
        # Ett steg som verkligen pågår. Det var ett fast 15, som blev fel när steg 15 blev klart (Hugos beslut 2026-11-06, beslut 6).
        pagaende = next(r for r in (rot / "BYGGPLAN.md").read_text(encoding="utf-8").splitlines() if r.startswith("- **Pågående steg:**"))
        pagar = re.search(r"(?<!\d)(\d+) – ", pagaende, re.ASCII).group(1)
        _lagg_in(
            rot / "PROGRESS.md",
            "\n## Läge",
            f"\n## Läge 2099-01-01, påhittad post\n\nSteg i byggplanen: {pagar} (pågår)\n\n- {PAHITTAD_TEXT}\n",
            f"\n## Påhittad rubrik sist\n\n- {PAHITTAD_TEXT}\n",
        )
        _lagg_in(
            rot / "BYGGPLAN.md",
            "\n## Regler som gäller i hela planen",
            f"\n## Påhittad post\n\n- {PAHITTAD_TEXT}\n",
            f"\n## Påhittad rubrik sist\n\n- {PAHITTAD_TEXT}\n",
        )
    svar = subprocess.run(
        [
            sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=line", "-rs",
            "-k", "not test_sparr_ and not test_granskning_37_a_",
            *[f"scripts/tests/{namn}" for namn in sorted(LASER_HISTORIKEN)],
        ],
        cwd=rot,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert svar.returncode == 0, svar.stdout[-6000:] + svar.stderr[-2000:]
    # Pytest ger returkod 0 också när alla test hoppar över sig (Hugos beslut 2026-11-06, beslut 1, granskning 40, P1).
    assert re.search(r"[1-9][0-9]* passed", svar.stdout), svar.stdout[-2000:]
    annat = [r for r in svar.stdout.splitlines() if r.startswith("SKIPPED") and "GRUPP D HOPPAS ÖVER" not in r]
    assert not annat, annat


# B: nästa granskning.


def test_granskning_37_b_star_i_claude_md():
    assert (
        "Granskning 38 prövar bara rättelserna från granskning 37. Nya fynd som inte blockerar installationen går till Öppet"
        in CLAUDE_MD.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05 om granskning 38.

GRANSKNING_38_RUBRIK = "## Granskning 38 (av 8bd6fe5 och 6065501)"
GRANSKNING_38_BESLUT = [
    "- P1: Rättas före installationen. En ny fil i .claude/ ska få stoppregeln att slå till.",
    "- P3: Rättas före installationen. Stoppregeln gäller .gitattributes med alla sorters stora och små bokstäver.",
    "- SPEC 7.1: Texten rättas nu så att den säger samma sak som CLAUDE.md och INSTALLERA.md (Öppet 66 och P4 i granskning 38). "
    "Kommandolistan ändras inte. git add och git commit står kvar i den, enligt Öppet 64.",
    "- Stoppkriterium: Granskning 39 prövar bara P1, P3 och SPEC 7.1. Blockerar inget där, installerar Hugo. Allt annat som "
    "hittas går till Öppet.",
    "- P2, P5, P6 och P7 i granskning 38: under Öppet.",
]


@pytest.mark.parametrize("beslut", GRANSKNING_38_BESLUT, ids=["P1", "P3", "SPEC", "stopp", "oppet"])
def test_granskning_38_besluten_star_ordagrant_under_granskning_38(beslut):
    avsnitt = _avsnitt_i_granskning(GRANSKNING_38_RUBRIK)
    assert beslut in avsnitt.split("### Hugos beslut 2026-11-05 om granskning 38", 1)[1]


def test_granskning_38_svaret_om_vantat_lage_star_under_besluten():
    # Frågan i byggsessionen: ska sessionens egna filer få räknas som väntade? Hugos svar i chatten.
    avsnitt = _avsnitt_i_granskning(GRANSKNING_38_RUBRIK).split("### Hugos beslut 2026-11-05 om granskning 38", 1)[1]
    assert "Bara uppräknade" in avsnitt


# Stoppregeln som kod, efter orden i texten. Ändras orden ändras utfallet, så ett prov här är ett prov av texten.

FNUTTAT = re.compile(r"`([^`]+)`")
ALLTID_STOPP = "någon annan rad med"
ALLA_ANDRA_STOPPAR = "varje rad som inte står exakt i det väntade läget stoppar"
ALLA_BOKSTAVER = "oavsett stora och små bokstäver"
CITATTECKEN_STOPPAR = 'varje rad som innehåller ett citattecken (`"`)'
STYCKENA = {"claude": _claude_md_stycket_om_git_status, "installera": _installera_stycket_om_git_status}


def _vantat_och_regel(stycket):
    fore, regel = stycket.split("toppregel", 1)
    return set(FNUTTAT.findall(fore.split("Väntat", 1)[1])) - {"!!"}, regel


def _stoppar(stycket, rad, uppraknade=()):
    """Slår stoppregeln till på raden från git status? uppraknade är filerna som sessionen räknar upp i COMMIT_MSG.txt."""
    vantat, regel = _vantat_och_regel(stycket)
    kod, sokvag = rad[:2], rad[3:]
    if CITATTECKEN_STOPPAR in regel and '"' in rad:
        return True
    if kod == "!!" and sokvag in vantat:
        return False
    if kod == "!!" and "en annan rad med `!!`" in regel:
        return True
    namn = [n.rstrip("/") for n in FNUTTAT.findall(regel) if n not in ("!!", '"')]
    delar = sokvag.split("/")
    if ALLA_BOKSTAVER in regel:
        namn, delar = [n.lower() for n in namn], [d.lower() for d in delar]
    if ALLTID_STOPP in regel and set(namn) & set(delar):
        return True
    if ALLA_ANDRA_STOPPAR in regel:
        return sokvag not in uppraknade
    return False


def _git_i_kopian(arbetsmapp, miljo, *argument):
    svar = subprocess.run(
        [GIT, *argument],
        cwd=arbetsmapp,
        env={**miljo, "GIT_AUTHOR_NAME": "prov", "GIT_AUTHOR_EMAIL": "prov@example.test", "GIT_COMMITTER_NAME": "prov", "GIT_COMMITTER_EMAIL": "prov@example.test"},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    _kontrollera_git(svar)
    return svar.stdout


def _statusrader(arbetsmapp, miljo):
    return set(_git_i_kopian(arbetsmapp, miljo, *NYTT_STATUS.split()[1:]).splitlines())


def _kopia_med_vantat_lage(tmp_path):
    """En kopia i testets tillfälliga mapp, med projektets .gitignore och det väntade läget. Aldrig projektets .git."""
    with _grupp_d_om_datorn_nekar():
        arbetsmapp, miljo = _provrepo(tmp_path)
        (arbetsmapp / "SPEC.md").write_text("x\n", encoding="utf-8")
        _git_i_kopian(arbetsmapp, miljo, "add", ".gitignore", "SPEC.md")
        _git_i_kopian(arbetsmapp, miljo, "commit", "-q", "-m", "prov")
        for fil in VANTADE_IGNORERADE:
            (arbetsmapp / fil).parent.mkdir(parents=True, exist_ok=True)
            (arbetsmapp / fil).write_text("", encoding="utf-8")
    return arbetsmapp, miljo


def _rad_for_ny_fil(tmp_path, fil, sokvag_i_raden=None):
    """Lägger en ny fil i kopian. Ger den enda nya raden från git status, som den ser ut på riktigt. sokvag_i_raden är
    namnet som git skriver det, när det inte är filens namn rakt av (inom citattecken)."""
    arbetsmapp, miljo = _kopia_med_vantat_lage(tmp_path)
    fore = _statusrader(arbetsmapp, miljo)
    with _grupp_d_om_datorn_nekar():
        (arbetsmapp / fil).parent.mkdir(parents=True, exist_ok=True)
        (arbetsmapp / fil).write_text("x\n", encoding="utf-8")
    nya = _statusrader(arbetsmapp, miljo) - fore
    assert len(nya) == 1, nya
    rad = nya.pop()
    assert rad[3:] == (sokvag_i_raden or fil), rad
    return rad


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
def test_granskning_38_det_vantade_laget_ger_inget_stopp(tmp_path, stycket):
    arbetsmapp, miljo = _kopia_med_vantat_lage(tmp_path)
    (arbetsmapp / "COMMIT_MSG.txt").write_text("x\n", encoding="utf-8")
    rader = _statusrader(arbetsmapp, miljo)
    assert rader == {f"!! {namn}" for namn in [*VANTADE_IGNORERADE, "COMMIT_MSG.txt"]}
    assert not [rad for rad in rader if _stoppar(STYCKENA[stycket](), rad)]


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize(
    "fil",
    [".claude/ny.py", ".claude/worktrees/ny.py", ".pytest_cache/ny.py", "foretag/ny.txt", "scripts/ny.py", "testdata/ny.txt"],
)
def test_granskning_38_p1_en_ny_fil_i_en_mapp_i_det_vantade_laget_stoppar(tmp_path, stycket, fil):
    # .claude/ är P1. Resten är de andra mapparna som står i det väntade läget.
    assert _stoppar(STYCKENA[stycket](), _rad_for_ny_fil(tmp_path, fil))


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize("fil", [".claude/ny.py", ".claude/worktrees/ny.py", ".CLAUDE/ny.py"])
def test_granskning_38_p1_en_fil_i_claude_stoppar_ocksa_om_sessionen_har_raknat_upp_den(stycket, fil):
    assert _stoppar(STYCKENA[stycket](), f"?? {fil}", uppraknade=[fil])


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize("namn", [".GITATTRIBUTES", ".GitAttributes", ".gitattributes"])
def test_granskning_38_p3_gitattributes_i_en_ny_mapp_stoppar_i_varje_stavning(tmp_path, stycket, namn):
    fil = f"ny/{namn}"
    rad = _rad_for_ny_fil(tmp_path, fil)
    assert rad == f"?? {fil}"
    # Också om sessionen har räknat upp filen, så att regeln inte bara är "allt annat stoppar".
    assert _stoppar(STYCKENA[stycket](), rad, uppraknade=[fil])


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize("namn", [".GITATTRIBUTES", ".GitIgnore", ".LFSCONFIG", ".GitModules", ".gitmodules"])
def test_granskning_38_p3_de_fyra_namnen_stoppar_i_varje_stavning_i_vilken_mapp_som_helst(stycket, namn):
    for fil in (namn, f"scripts/{namn}", f"ny/under/{namn}"):
        assert _stoppar(STYCKENA[stycket](), f"?? {fil}", uppraknade=[fil])
        assert _stoppar(STYCKENA[stycket](), f" M {fil}", uppraknade=[fil])


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
def test_granskning_38_sessionens_uppraknade_filer_ar_vantade_och_inget_annat(tmp_path, stycket):
    # Hugos svar i chatten: bara uppräknade. Riktiga rader från git status, en ändrad fil och en ny fil.
    arbetsmapp, miljo = _kopia_med_vantat_lage(tmp_path)
    (arbetsmapp / "SPEC.md").write_text("ändrad\n", encoding="utf-8")
    (arbetsmapp / "scripts" / "ny.py").write_text("x\n", encoding="utf-8")
    rader = _statusrader(arbetsmapp, miljo)
    assert {" M SPEC.md", "?? scripts/ny.py"} <= rader
    text = STYCKENA[stycket]()
    assert not [rad for rad in rader if _stoppar(text, rad, uppraknade=["SPEC.md", "scripts/ny.py"])]
    assert [rad for rad in rader if _stoppar(text, rad, uppraknade=["SPEC.md"])] == ["?? scripts/ny.py"]
    assert [rad for rad in rader if _stoppar(text, rad, uppraknade=["scripts/ny.py"])] == [" M SPEC.md"]


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
def test_granskning_38_en_ignorerad_fil_gar_inte_att_rakna_upp(stycket):
    assert "men aldrig en rad med `!!`" in STYCKENA[stycket]()
    assert _stoppar(STYCKENA[stycket](), "!! scripts/kvitto.csv", uppraknade=["scripts/kvitto.csv"])


def test_granskning_38_samma_vantade_lage_pa_bada_platserna():
    assert _vantat_och_regel(_claude_md_stycket_om_git_status())[0] == _vantat_och_regel(_installera_stycket_om_git_status())[0]


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
def test_granskning_38_stoppregeln_har_orden(stycket):
    regel = _vantat_och_regel(STYCKENA[stycket]())[1]
    for text in (ALLA_ANDRA_STOPPAR, ALLA_BOKSTAVER, ALLTID_STOPP, "`.claude/`", "även om sessionen har räknat upp filen"):
        assert text in regel


@pytest.mark.parametrize("plats", ["CLAUDE.md", "INSTALLERA.md"])
def test_granskning_38_meddelandet_raknar_upp_filerna(plats):
    assert "Meddelandet räknar upp varje fil som sessionen har ändrat, skapat eller tagit bort." in _platser_med_de_fasta_kommandona()[plats]


def test_granskning_38_stoppkriteriet_star_efter_regeln_om_granskning_38():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    plats = next(i for i, rad in enumerate(rader) if rad.startswith("- Granskning 38 prövar bara rättelserna"))
    assert rader[plats + 1] == (
        "- Granskning 39 prövar bara P1, P3 och SPEC 7.1 från granskning 38. Blockerar inget där, installerar Hugo. Allt annat "
        "som hittas går till Öppet (Hugos beslut 2026-11-05 om granskning 38)."
    )


# SPEC 7.1 mot CLAUDE.md och INSTALLERA.md. Ställena: "Det vakten inte stoppar" (status-kommandot), "Prov och test" (länkregeln,
# undantaget för spärrprovet och undantaget för kopian) och "git commit -F" under git: (vem som committar före och efter).

KOPIAN_UNDANTAG = 'Kopian är ett undantag från regeln "Prov och test", bara för spärrtestet'


def _spec_punkt(borjan):
    return next(rad for rad in _spec_7_1().splitlines() if rad.lstrip().startswith(borjan))


def test_granskning_38_spec_status_kommandot_ar_samma_som_i_claude_md():
    i_claude = re.findall(r"`(git status --short[^`]*)`", _claude_md_stycket_om_git_status())
    assert i_claude == [NYTT_STATUS]
    assert re.findall(r"`(git status --short[^`]*)`", _spec_7_1()) == i_claude
    assert not GAMMALT_STATUS.search(_spec_7_1())


def test_granskning_38_spec_lankregeln_har_samma_undantag_som_claude_md():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    i_claude = next(r for r in rader if r.startswith("- Prov och test får bara skapa, ändra eller länka filer"))
    undantaget = re.search(rf"testet `{HARD_LANK_TEST}` [^.]*[.]ssh/prov`, och ska stoppas", i_claude)
    assert undantaget, "undantaget hittas inte i CLAUDE.md"
    i_spec = _spec_punkt("- **Prov och test**")
    assert undantaget.group(0) in i_spec
    assert "Aldrig länkar (hårda eller mjuka) till något utanför de mapparna." in i_spec
    assert "bara i spärrprovet" in i_spec
    assert "Hugos beslut 2026-11-05 om granskning 37, P3" in i_spec


def test_granskning_38_spec_lankregeln_har_undantaget_for_kopian_som_installera():
    assert KOPIAN_UNDANTAG in _avsnitt(SPARRPROV_RUBRIK)
    i_spec = _spec_punkt("- **Prov och test**")
    assert KOPIAN_UNDANTAG in i_spec
    assert "`~/VERA/sparrprov`" in i_spec


def test_granskning_38_spec_sager_vem_som_committar_fore_och_efter_installationen():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    i_claude = next(r for r in rader if r.startswith("- När sandlådan är installerad committar agenten inte"))
    i_spec = _spec_punkt("- `git commit -F`")
    for text in (
        "När sandlådan är installerad committar agenten inte",
        "Sessionen skriver bara commit-meddelandet i filen `COMMIT_MSG.txt` i projektmappen",
        "Hugos beslut 2026-11-05 om granskning 34, beslut 2",
        "Det gäller från installationen av steg 15",
        "Hugos beslut 2026-11-05 om granskning 35, beslut 6",
    ):
        assert text in i_claude and text in i_spec
    # Det gamla, att meddelandet skrivs i den tillfälliga mappen, gäller bara före installationen.
    assert i_spec.index("Före installationen") < i_spec.index("skrivs med fil-verktygen i den tillfälliga mappen")
    assert i_spec.index("skrivs med fil-verktygen i den tillfälliga mappen") < i_spec.index("När sandlådan är installerad")


def test_granskning_38_spec_sager_att_git_add_och_git_commit_star_kvar_enligt_oppet_64():
    i_spec = _spec_punkt("- `git commit -F`")
    assert "`git add` och `git commit` står kvar i listan" in i_spec
    assert "Öppet 64" in i_spec


# Kommandolistan, inställningarna och vakten är oförändrade mot 103eb55, commiten före rättelsen (räknat i en kopia av den).

LISTANS_SUMMA = "7c3ab251713a93073f5d9d10804f35af8d48497daca8f77140ff3c6e321783e7"
INSTALLNINGARNAS_SUMMA = "1ba7457615356ff634956cf3f665787d2e74900986aa96001feeaa8ce31a39da"


def _kommandolistan():
    rader = _spec_7_1().splitlines(keepends=True)
    start = rader.index("| Kommando | Till vad |\n")
    slut = start
    while rader[slut].startswith("|"):
        slut += 1
    return "".join(rader[start:slut])


def test_granskning_38_kommandolistan_i_spec_7_1_ar_oforandrad():
    assert hashlib.sha256(_kommandolistan().encode("utf-8")).hexdigest() == LISTANS_SUMMA
    assert "| `git add` |" in _kommandolistan() and "| `git commit` |" in _kommandolistan()


def test_granskning_38_installningarna_ar_oforandrade():
    assert hashlib.sha256(INSTALLNINGAR.read_bytes()).hexdigest() == INSTALLNINGARNAS_SUMMA


def test_granskning_38_vakten_ar_oforandrad():
    assert hashlib.sha256(VAKTEN.read_bytes()).hexdigest() == VAKTENS_SUMMA


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05 om granskning 39.

GRANSKNING_39_RUBRIK = "## Granskning 39 (av f52e6ef och c0b54e6)"
GRANSKNING_39_BESLUT = [
    '1. De 25 testerna blir grupp D. I sandlådan hoppar de över sig själva med "GRUPP D HOPPAS ÖVER", men bara när datorn '
    "nekar med Operation not permitted (PermissionError, eller git som avslutas med det i sitt felmeddelande). Alla andra "
    'fel ger rött. Utanför sandlådan körs de som vanligt och hoppas aldrig över. De körs i "Prov utanför sandlådan" i '
    "INSTALLERA.md.",
    '2. Kommandot i "Provkörning med sandlådan" får exakt samma sandbox-nyckel som sparr/managed-settings.json, också '
    "filesystem. Ett test jämför dem.",
    "3. Granskning 39, P1: Hugo läser listan i COMMIT_MSG.txt innan han committar. Kommandot cat COMMIT_MSG.txt läggs till "
    "bland de fasta kommandona, efter ls -l COMMIT_MSG.txt och före git commit -F COMMIT_MSG.txt.",
    '4. Granskning 39, P2: en rad i git status som innehåller ett citattecken (") stoppar alltid.',
    "5. Granskning 39, P3: .github/ och .mcp.json läggs till i listan som alltid stoppar, i vilken mapp som helst och oavsett "
    "stora och små bokstäver.",
    "6. Stoppkriterium: Granskning 40 prövar bara punkt 1–5. Blockerar inget där, kör Hugo provkörningen igen och installerar. "
    "Allt annat som hittas går till Öppet.",
]


@pytest.mark.parametrize("beslut", GRANSKNING_39_BESLUT, ids=[str(n) for n in range(1, 7)])
def test_granskning_39_besluten_star_ordagrant_under_granskning_39(beslut):
    avsnitt = _avsnitt_i_granskning(GRANSKNING_39_RUBRIK)
    assert beslut in avsnitt.split("### Hugos beslut 2026-11-05 om granskning 39", 1)[1]


def test_granskning_39_stoppkriteriet_star_efter_regeln_om_granskning_39():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    plats = next(i for i, rad in enumerate(rader) if rad.startswith("- Granskning 39 prövar bara"))
    assert rader[plats + 1] == (
        "- Granskning 40 prövar bara punkt 1–5 i Hugos beslut 2026-11-05 om granskning 39. Blockerar inget där, kör Hugo "
        "provkörningen igen och installerar. Allt annat som hittas går till Öppet (Hugos beslut 2026-11-05 om granskning 39, "
        "beslut 6)."
    )


# Beslut 1: grupp D. Vad sandlådan nekar, enligt koden: test_granskning_37_p4_ skapar mappen .venv, och test_granskning_38_
# och de riktiga raderna nedan skapar mappen .claude (_kopia_med_vantat_lage). Båda namnen står i Edit-förbuden i
# sparr/managed-settings.json. test_granskning_37_a_ skapar inget sådant namn: den är röd i sandlådan eftersom den kör de andra
# i en kopia, och blir grön när de hoppar över sig (PROGRESS.md).

NEKAT = PermissionError(errno.EPERM, "Operation not permitted")
ANDRA_FEL = {
    "disken_full": OSError(errno.ENOSPC, "No space left on device"),
    "ratten_saknas": PermissionError(errno.EACCES, "Permission denied"),
}
GIT_NEKAT = "fatal: cannot mkdir x: Operation not permitted\n"


def _neka_mapp(byte, namn, fel):
    """Bara mappen med namnet nekas. Allt annat i testet körs på riktigt, så det här går att köra också i sandlådan."""
    riktig = Path.mkdir

    def mkdir(self, *argument, **tillagg):
        if self.name == namn:
            raise fel
        return riktig(self, *argument, **tillagg)

    byte.setattr(Path, "mkdir", mkdir)


GRUPP_D_PROV = {
    "37_p4_uall": (".venv", lambda t: test_granskning_37_p4_uall_visar_varje_fil_for_sig(t)),
    "37_p4_utan": (".venv", lambda t: test_granskning_37_p4_utan_uall_doljs_filerna(t)),
    "38_vantat": (".claude", lambda t: test_granskning_38_det_vantade_laget_ger_inget_stopp(t, "claude")),
    "38_p1": (".claude", lambda t: test_granskning_38_p1_en_ny_fil_i_en_mapp_i_det_vantade_laget_stoppar(t, "claude", "scripts/ny.py")),
    "38_p3": (".claude", lambda t: test_granskning_38_p3_gitattributes_i_en_ny_mapp_stoppar_i_varje_stavning(t, "claude", ".gitattributes")),
    "38_uppraknade": (".claude", lambda t: test_granskning_38_sessionens_uppraknade_filer_ar_vantade_och_inget_annat(t, "claude")),
    "39_rader": (".claude", lambda t: test_granskning_39_riktiga_rader_stoppar_ocksa_om_de_ar_uppraknade(t, "claude", "ny/a b.py", '"ny/a b.py"')),
}


def _ska_ge_rott(vantat_fel, kor):
    """Felet ska komma, och provet får inte hoppa över sig. Ett hopp inne i pytest.raises skulle annars räknas som överhoppat,
    inte som rött, så att provet av att andra fel ger rött inte larmar när regeln är borta (mutation i byggsessionen)."""
    try:
        with pytest.raises(vantat_fel) as fangat:
            kor()
    except pytest.skip.Exception as hopp:
        pytest.fail(f"provet hoppade över sig, men skulle ge rött: {hopp}")
    return fangat.value


@pytest.mark.parametrize("prov", GRUPP_D_PROV)
def test_granskning_39_b1_operation_not_permitted_hoppar_over(monkeypatch, tmp_path, prov):
    mapp, kor = GRUPP_D_PROV[prov]
    _neka_mapp(monkeypatch, mapp, NEKAT)
    with pytest.raises(pytest.skip.Exception, match="GRUPP D HOPPAS ÖVER"):
        kor(tmp_path)


@pytest.mark.parametrize("fel", ANDRA_FEL, ids=list(ANDRA_FEL))
@pytest.mark.parametrize("prov", GRUPP_D_PROV)
def test_granskning_39_b1_andra_fel_ger_rott(monkeypatch, tmp_path, prov, fel):
    mapp, kor = GRUPP_D_PROV[prov]
    _neka_mapp(monkeypatch, mapp, ANDRA_FEL[fel])
    fangat = _ska_ge_rott(type(ANDRA_FEL[fel]), lambda: kor(tmp_path))
    assert fangat.errno == ANDRA_FEL[fel].errno


def _git_som_svarar(monkeypatch, returkod, felmeddelande, bara_for=None):
    riktig = subprocess.run

    def run(argument, *resten, **tillagg):
        if bara_for is not None and bara_for not in argument:
            return riktig(argument, *resten, **tillagg)
        return subprocess.CompletedProcess(args=argument, returncode=returkod, stdout="", stderr=felmeddelande)

    monkeypatch.setattr(subprocess, "run", run)


def test_granskning_39_b1_git_som_nekas_hoppar_over(monkeypatch, tmp_path):
    _git_som_svarar(monkeypatch, 128, GIT_NEKAT)
    with pytest.raises(pytest.skip.Exception, match="GRUPP D HOPPAS ÖVER"):
        _git_i_kopian(tmp_path, {}, "status")


@pytest.mark.parametrize("felmeddelande", ["fatal: not a git repository\n", "fatal: Permission denied\n", ""])
def test_granskning_39_b1_annat_git_fel_ger_rott(monkeypatch, tmp_path, felmeddelande):
    _git_som_svarar(monkeypatch, 128, felmeddelande)
    _ska_ge_rott(AssertionError, lambda: _git_i_kopian(tmp_path, {}, "status"))


def test_granskning_39_b1_orden_utan_att_git_misslyckas_hoppar_inte_over(monkeypatch, tmp_path):
    _git_som_svarar(monkeypatch, 0, "warning: Operation not permitted\n")
    try:
        assert _git_i_kopian(tmp_path, {}, "status") == ""
    except pytest.skip.Exception as hopp:
        pytest.fail(f"git gick bra, men provet hoppade över sig: {hopp}")


def _inget_skapas_i_venv(byte):
    """Mappen .venv skapas inte på riktigt. I sandlådan skulle provet annars hoppa över sig där, före git (modellprovet)."""
    riktig_mkdir = Path.mkdir
    riktig_skriv = Path.write_text

    def mkdir(self, *argument, **tillagg):
        return None if self.name == ".venv" else riktig_mkdir(self, *argument, **tillagg)

    def skriv(self, *argument, **tillagg):
        return 0 if self.parent.name == ".venv" else riktig_skriv(self, *argument, **tillagg)

    byte.setattr(Path, "mkdir", mkdir)
    byte.setattr(Path, "write_text", skriv)


def test_granskning_39_b1_git_status_i_p4_som_nekas_hoppar_over(monkeypatch, tmp_path):
    _inget_skapas_i_venv(monkeypatch)
    _git_som_svarar(monkeypatch, 128, GIT_NEKAT, bara_for="status")
    with pytest.raises(pytest.skip.Exception, match="git nekades"):
        test_granskning_37_p4_uall_visar_varje_fil_for_sig(tmp_path)


def test_granskning_39_b1_annat_fel_fran_git_status_i_p4_ger_rott(monkeypatch, tmp_path):
    _inget_skapas_i_venv(monkeypatch)
    _git_som_svarar(monkeypatch, 128, "fatal: not a git repository\n", bara_for="status")
    _ska_ge_rott(AssertionError, lambda: test_granskning_37_p4_uall_visar_varje_fil_for_sig(tmp_path))


def _neka_kopiering(byte, fel):
    def copytree(*_a, **_k):
        raise fel

    byte.setattr(shutil, "copytree", copytree)


def test_granskning_39_b1_prov_a_hoppar_over_bara_om_kopieringen_nekas(monkeypatch, tmp_path):
    _neka_kopiering(monkeypatch, NEKAT)
    with pytest.raises(pytest.skip.Exception, match="GRUPP D HOPPAS ÖVER"):
        test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path)


def test_granskning_39_b1_prov_a_annat_fel_vid_kopieringen_ger_rott(monkeypatch, tmp_path):
    _neka_kopiering(monkeypatch, ANDRA_FEL["disken_full"])
    _ska_ge_rott(OSError, lambda: test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path))


def test_granskning_39_b1_prov_a_rott_i_kopian_ger_rott_ocksa_med_orden_i_utskriften(monkeypatch, tmp_path):
    # Ett rött test i kopian får aldrig bli ett överhoppat prov, oavsett vad utskriften säger.
    monkeypatch.setattr(shutil, "copytree", lambda *_a, **_k: None)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argument, *_r, **_k: subprocess.CompletedProcess(
            args=argument, returncode=1, stdout="PermissionError: Operation not permitted", stderr=""
        ),
    )
    _ska_ge_rott(AssertionError, lambda: test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path))


def _prov_som_bygger_provrepo():
    trad = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    hjalp = {"_kopia_med_vantat_lage", "_rad_for_ny_fil", "_status"}
    return {
        del_.name
        for del_ in trad.body
        if isinstance(del_, ast.FunctionDef)
        and del_.name.startswith("test_")
        and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in hjalp for n in ast.walk(del_))
    }


def test_granskning_39_b1_varje_prov_som_kan_hoppa_over_kors_utanfor_sandladan():
    # Ett nytt prov med samma hjälpfunktioner måste med i kommandot i "Prov utanför sandlådan", annars körs det aldrig.
    utanfor = set(UTANFOR_K.split(" or "))
    assert utanfor == _prov_som_bygger_provrepo() | {
        "test_h6_en_lank_till_git_stoppas",
        "test_beslut_1_gamla_venv_i_projektet_stoppas",
        "test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott",
    }


def _insamlade_utanfor():
    svar = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q", "-k", UTANFOR_K, str(Path(__file__).parent)],
        cwd=PROJEKTET,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert svar.returncode == 0, svar.stdout + svar.stderr
    return [rad for rad in svar.stdout.splitlines() if "::test_" in rad]


def test_granskning_39_b1_antalen_i_installera_stammer_med_testerna():
    prov = _insamlade_utanfor()
    # Alla utom test_granskning_37_a_, som inte skapar något som sandlådan nekar.
    hoppar = [rad for rad in prov if "::test_granskning_37_a_" not in rad]
    assert (len(prov), len(hoppar)) == (39, 38)
    sparrtestet, i_kopian, h1 = 10, 31, 6
    assert f"`{len(hoppar) + sparrtestet + i_kopian + h1} skipped`" in _avsnitt(PROVKORNING_RUBRIK)
    assert f"**{len(hoppar) + i_kopian}** överhoppade" in _byte_avsnittet()
    assert f"**{len(hoppar) + i_kopian + 2}** om `~/.ssh` inte finns" in _byte_avsnittet()
    assert f"`{len(prov)} passed`" in _avsnitt(UTANFOR_RUBRIK)


@pytest.mark.parametrize(
    "rubrik,text",
    [
        (UTANFOR_RUBRIK, "Hugos beslut 2026-11-05 om granskning 39, beslut 1"),
        (UTANFOR_RUBRIK, "`Operation not permitted`"),
        (PROVKORNING_RUBRIK, "`Operation not permitted`"),
        (PROVKORNING_RUBRIK, "Alla andra fel ger rött"),
        (PROVKORNING_RUBRIK, "`test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott`"),
    ],
    # Egna namn, eftersom -k också söker i namnet på en variant, och provnamnet ovan annars väljs i "Prov utanför sandlådan".
    ids=["utanfor_beslutet", "utanfor_nekar", "provkorning_nekar", "provkorning_andra_fel", "provkorning_prov_a"],
)
def test_granskning_39_b1_installera_sager_vad_som_galler(rubrik, text):
    assert text in _avsnitt(rubrik)


def test_granskning_39_b1_claude_md_sager_nar_grupp_d_hoppas_over():
    rader = CLAUDE_MD.read_text(encoding="utf-8").splitlines()
    stycket = next(r for r in rader if r.startswith("- Prov som inte kan köras i sandlådan (grupp D)"))
    assert "bara när datorn nekar med `Operation not permitted`" in stycket
    assert "Hugos beslut 2026-11-05 om granskning 39, beslut 1" in stycket


# Beslut 2: kommandot i rutan mot filen, nyckel för nyckel.

PROVKORNING_START = "~/.local/bin/claude --settings '"


def _provkorningens_installningar(text):
    rad = next(r for r in _kodrader(text) if r.startswith(PROVKORNING_START))
    assert rad.endswith("'")
    return json.loads(rad[len(PROVKORNING_START):-1])


def _skillnader_mot_filen(i_rutan):
    i_filen = _installningar()["sandbox"]
    assert set(i_rutan) == {"sandbox"}
    nycklar = set(i_filen) | set(i_rutan["sandbox"])
    return sorted(n for n in nycklar if i_rutan["sandbox"].get(n, "saknas") != i_filen.get(n, "saknas"))


def test_granskning_39_b2_rutan_har_exakt_samma_sandbox_nyckel_som_filen():
    i_rutan = _provkorningens_installningar(_avsnitt(PROVKORNING_RUBRIK))
    assert _skillnader_mot_filen(i_rutan) == []
    assert i_rutan["sandbox"]["filesystem"] == _installningar()["sandbox"]["filesystem"]


@pytest.mark.parametrize("nyckel", ["filesystem", "enabled", "network"])
def test_granskning_39_b2_jamforelsen_ser_en_saknad_nyckel(nyckel):
    i_rutan = json.loads(PROVKORNINGENS_NYCKLAR)
    del i_rutan["sandbox"][nyckel]
    assert _skillnader_mot_filen(i_rutan) == [nyckel]


def test_granskning_39_b2_texten_sager_att_det_ar_samma_nyckel():
    avsnitt = _avsnitt(PROVKORNING_RUBRIK)
    assert "exakt samma `sandbox`-nyckel som `sparr/managed-settings.json`, också `filesystem`" in avsnitt
    assert "Hugos beslut 2026-11-05 om granskning 39, beslut 2" in avsnitt


# Beslut 3: cat COMMIT_MSG.txt, på varje plats som listar de fasta kommandona.

CAT_KOMMANDOT = "cat COMMIT_MSG.txt"


@pytest.mark.parametrize("plats", ["CLAUDE.md", "INSTALLERA.md"])
def test_granskning_39_b3_cat_star_efter_ls_och_fore_commiten(plats):
    text = _platser_med_de_fasta_kommandona()[plats]
    assert text.index(LS_KOMMANDOT) < text.index(CAT_KOMMANDOT) < text.index(COMMITEN)
    assert "Hugos beslut 2026-11-05 om granskning 39, beslut 3" in text


@pytest.mark.parametrize(
    "plats,mening,villkor",
    [
        ("CLAUDE.md", "Med `cat` läser Hugo listan i `COMMIT_MSG.txt` före commiten", "bara när raden från `ls -l` stämmer"),
        ("INSTALLERA.md", "**Läs listan i `COMMIT_MSG.txt` före commiten.**", "bara när raden ovan stämmer"),
    ],
)
def test_granskning_39_b3_varje_plats_sager_att_listan_lases_fore_commiten(plats, mening, villkor):
    text = _platser_med_de_fasta_kommandona()[plats]
    assert mening in text and villkor in text


def test_granskning_39_b3_i_installera_star_cat_i_en_egen_ruta_i_ordning():
    rader = _kodrader(_byte_avsnittet())
    start = rader.index(LS_KOMMANDOT)
    assert rader[start:start + 3] == [LS_KOMMANDOT, CAT_KOMMANDOT, COMMITEN]


def test_granskning_39_b3_spec_7_1_namner_cat_och_kommandolistan_ar_oforandrad():
    assert f"`{CAT_KOMMANDOT}`" in _spec_punkt("- `git commit -F`")
    assert hashlib.sha256(_kommandolistan().encode("utf-8")).hexdigest() == LISTANS_SUMMA


# Beslut 4 och 5: citattecken, .github/ och .mcp.json.


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
def test_granskning_39_b4_b5_stoppregeln_har_orden(stycket):
    regel = _vantat_och_regel(STYCKENA[stycket]())[1]
    for text in (CITATTECKEN_STOPPAR, "`.github/`", "`.mcp.json`", ALLA_BOKSTAVER, "i vilken mapp som helst"):
        assert text in regel
    assert "Hugos beslut 2026-11-05 om granskning 39, beslut 4 och 5" in regel


def test_granskning_39_b4_b5_spec_7_1_sager_samma_sak():
    punkt = _spec_punkt("- **Det vakten inte stoppar:**")
    for text in ("citattecken", "`.github/`", "`.mcp.json`", "Hugos beslut 2026-11-05 om granskning 39, beslut 4 och 5"):
        assert text in punkt


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize(
    "rad",
    [
        '?? "ny/a b.py"',
        '?? "ny/.gitattribute\\305\\277"',
        ' M "scripts/\\303\\245.py"',
        'D  "a b.txt"',
        'R  "a b.txt" -> c.txt',
        '!! "ny/a b.py"',
    ],
)
def test_granskning_39_b4_en_rad_med_citattecken_stoppar_alltid(stycket, rad):
    sokvag = rad[3:]
    assert _stoppar(STYCKENA[stycket](), rad, uppraknade=[sokvag])


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize(
    "fil",
    [
        ".github/workflows/x.yml",
        "ny/.github/workflows/x.yml",
        ".GITHUB/x.yml",
        "scripts/.GitHub/x",
        ".mcp.json",
        "ny/under/.mcp.json",
        ".MCP.json",
        "scripts/.Mcp.Json",
    ],
)
def test_granskning_39_b5_github_och_mcp_stoppar_i_varje_stavning_och_mapp(stycket, fil):
    for kod in ("??", " M", "D ", "A "):
        assert _stoppar(STYCKENA[stycket](), f"{kod} {fil}", uppraknade=[fil])


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize("fil", ["github/x.yml", "scripts/mcp.json", "scripts/ny.py"])
def test_granskning_39_b5_andra_namn_stoppar_bara_om_de_inte_ar_uppraknade(stycket, fil):
    assert not _stoppar(STYCKENA[stycket](), f"?? {fil}", uppraknade=[fil])
    assert _stoppar(STYCKENA[stycket](), f"?? {fil}")


@pytest.mark.parametrize("stycket", STYCKENA, ids=list(STYCKENA))
@pytest.mark.parametrize(
    "fil,i_raden",
    [
        (".github/workflows/x.yml", None),
        (".GITHUB/x.yml", None),
        (".MCP.json", None),
        ("ny/.mcp.json", None),
        ("ny/.gitattributeſ", '"ny/.gitattribute\\305\\277"'),
        ("ny/a b.py", '"ny/a b.py"'),
    ],
    ids=["github", "GITHUB", "MCP", "mcp_i_mapp", "langt_s", "mellanslag"],
)
def test_granskning_39_riktiga_rader_stoppar_ocksa_om_de_ar_uppraknade(tmp_path, stycket, fil, i_raden):
    # Riktiga rader från git status i testets tillfälliga mapp, med projektets .gitignore. Långt s är granskning 39, P2: Macen
    # räknar det som s, git läser filen, och raden innehåller inte namnet. Citattecknet stoppar den ändå.
    rad = _rad_for_ny_fil(tmp_path, fil, i_raden)
    assert rad == f"?? {i_raden or fil}"
    assert _stoppar(STYCKENA[stycket](), rad, uppraknade=[fil, rad[3:]])


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-05, beslut 3: grupp D hoppas över bara när datorn nekar.


def test_grupp_d_hoppas_over_med_tydligt_meddelande_nar_datorn_nekar(monkeypatch):
    def nekar(_sokvag):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr(os, "makedirs", nekar)
    with pytest.raises(pytest.skip.Exception, match="GRUPP D HOPPAS ÖVER"):
        gor_mapp_eller_hoppa_over("/x/.git")


def test_grupp_d_hoppas_inte_over_vid_andra_fel(monkeypatch):
    def annat_fel(_sokvag):
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(os, "makedirs", annat_fel)
    with pytest.raises(FileNotFoundError):
        gor_mapp_eller_hoppa_over("/x/.git")


def test_grupp_d_skapar_mappen_nar_datorn_inte_nekar(tmp_path):
    gor_mapp_eller_hoppa_over(str(tmp_path / "prov" / "mapp"))
    assert (tmp_path / "prov" / "mapp").is_dir()


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-06 om Öppet 69 och spärrprovet. Namnen på testen här får inte innehålla filtren i INSTALLERA.md, eftersom
# -k också söker i namnet på en variant. Därför har varianterna egna namn.

BESLUT_06_RUBRIK = "## Hugos beslut 2026-11-06 om Öppet 69 och spärrprovet"
BESLUT_06 = [
    '1. P1 (granskning 40) rättas som granskningen föreslår: "-rs" läggs till i kommandot i '
    "test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott, och efter raden med returncode kontrolleras att "
    "minst ett test gick igenom och att inget test hoppades över med en annan text än GRUPP D HOPPAS ÖVER. Rött före: visa att "
    "testet i dag blir grönt när alla test i kopian hoppar över sig av en annan anledning.",
    "2. P2 (granskning 40) rättas: gor_mapp_eller_hoppa_over hoppar bara över vid Operation not permitted (errno 1), samma "
    "kontroll av felkoden som de andra i grupp D. Alla andra fel, också Permission denied (errno 13), ger rött. Nytt test för "
    "errno 13. Rött före.",
    "3. P3 är klar: Hugo körde git config --get core.quotepath 2026-11-05, standardläge.",
    "4. P4 och P5 står kvar under Öppet 69.",
    '5. Det väntade antalet i "Spärrprovet i kopian" i sparr/INSTALLERA.md blir 43 passed i stället för 41. Filtret -k '
    "test_sparr_ väljer 41 spärrprov och två texttest vars namn innehåller spärrprovens namn: "
    "test_granskning_36_p6_installera_sager_vad_som_galler[`test_sparr_lasning_av_ssh_stoppas`] och "
    "test_granskning_37_p3_installera_har_sparrprovet_med_hard_lank[`test_sparr_hard_lank_till_ssh_stoppas`]. Lås antalet med "
    "ett test som räknar alla test filtret väljer (inte bara de som heter test_sparr_), så att det inte kan glida isär igen. "
    'Gör likadant för H1-proven (31) och "Prov utanför sandlådan" (39), om de inte redan är låsta så.',
    "6. Steg 15 är installerat och provat. Hugos körningar 2026-11-06, commit c49ebf1:",
    "a. Spärrprovet i kopian i Terminal (Claude Code 2.1.318): 43 passed, inget failed, ingen rad med HOPPAS ÖVER.",
    "b. Samma i skrivbordsappen: 43 passed, inget failed, ingen rad med HOPPAS ÖVER.",
    "c. H1-proven i appen: 31 passed, inget skipped, inget failed.",
    'd. Läsförbudet: Read av ~/.ssh/prov nekades ("File is in a directory that is denied by your permission settings"). cat '
    "~/.ssh/prov stoppades av vakten (tecknet ~ utanför citattecken). kassio-prov visades inte.",
    "e. ~/.ssh/prov, ~/.ssh och ~/VERA/sparrprov är borttagna (ls: No such file or directory).",
    "f. Prov utanför sandlådan i ~/VERA/provkopia: 39 passed, inget failed, ingen rad med GRUPP D HOPPAS ÖVER. Kopian är "
    "borttagen.",
    "g. Installationen och kontrollen efter bytet, 6.1–6.7, godkändes 2026-11-05.",
    '7. Raden "Nästa steg" i BYGGPLAN.md och steg 53 och 54 följer Kassio-beslutet 2026-11-05: rådgivare, jurister och '
    "konsulter kontaktas längre fram, eftersom vi inte har råd nu. Det som krävs innan riktig data används (steg 109 och 118) "
    "är en öppen fråga. Skriv den som öppen fråga och hitta inte på något svar.",
    "8. Ingen egen granskning för den här sessionen. Den granskas tillsammans med steg 16.",
]


@pytest.mark.parametrize("beslut", BESLUT_06, ids=[str(n) for n in range(1, len(BESLUT_06) + 1)])
def test_beslut_2026_11_06_star_ordagrant_i_granskning(beslut):
    assert beslut in _avsnitt_i_granskning(BESLUT_06_RUBRIK)


# Beslut 1: P1. Kopieringen och pytest i kopian byts ut, så att bara det som kontrolleras efter körningen prövas.

GRUPP_D_RAD = 'SKIPPED [36] scripts/tests/test_sandladan.py:1697: GRUPP D HOPPAS ÖVER: datorn nekade, troligen sandlådan.\n'
ANNAN_RAD = "SKIPPED [{}] scripts/tests/test_byggplan_progress.py:1: annan anledning\n"


def _kopian_svarar(monkeypatch, returkod, utskrift):
    kommandon = []

    def run(argument, *_r, **_k):
        kommandon.append(argument)
        return subprocess.CompletedProcess(args=argument, returncode=returkod, stdout=utskrift, stderr="")

    monkeypatch.setattr(shutil, "copytree", lambda *_a, **_k: None)
    monkeypatch.setattr(subprocess, "run", run)
    return kommandon


@pytest.mark.parametrize(
    "utskrift",
    [
        ANNAN_RAD.format(1074) + "1074 skipped in 1.30s\n",
        ANNAN_RAD.format(10) + "1064 passed, 10 skipped in 45.00s\n",
        ANNAN_RAD.format(10) + GRUPP_D_RAD + "1028 passed, 46 skipped in 45.00s\n",
        GRUPP_D_RAD + "36 skipped in 1.30s\n",
    ],
    ids=["alla_hoppar_av_en_annan_anledning", "en_fil_hoppar_av_en_annan_anledning", "bada_sorterna", "alla_hoppar_som_grupp_d"],
)
def test_beslut_2026_11_06_p1_kopian_utan_prov_eller_med_annat_hopp_ger_rott(monkeypatch, tmp_path, utskrift):
    _kopian_svarar(monkeypatch, 0, utskrift)
    _ska_ge_rott(AssertionError, lambda: test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path))


@pytest.mark.parametrize(
    "utskrift",
    ["1074 passed in 45.00s\n", GRUPP_D_RAD + "1038 passed, 36 skipped in 45.00s\n"],
    ids=["utan_sandlada", "i_sandladan"],
)
def test_beslut_2026_11_06_p1_kopian_som_provar_nagot_ger_gront(monkeypatch, tmp_path, utskrift):
    _kopian_svarar(monkeypatch, 0, utskrift)
    test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path)


def test_beslut_2026_11_06_p1_kommandot_visar_vad_som_hoppades_over(monkeypatch, tmp_path):
    # Utan -rs står inga rader med SKIPPED i utskriften, och då har kontrollen ingenting att läsa.
    kommandon = _kopian_svarar(monkeypatch, 0, "1074 passed in 45.00s\n")
    test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott(tmp_path)
    assert len(kommandon) == 1 and "-rs" in kommandon[0]


# Beslut 2: P2. Samma kontroll av felkoden som de andra i grupp D.


def test_beslut_2026_11_06_p2_errno_13_ger_rott(monkeypatch):
    def nekar(_sokvag):
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(os, "makedirs", nekar)
    assert _ska_ge_rott(PermissionError, lambda: gor_mapp_eller_hoppa_over("/x/.git")).errno == errno.EACCES


def test_beslut_2026_11_06_p2_riktigt_permission_denied_ger_rott(tmp_path):
    # Vanliga rättigheter, i testets tillfälliga mapp: en mapp utan skrivrätt ger errno 13.
    mapp = tmp_path / "utan_skrivratt"
    mapp.mkdir()
    mapp.chmod(0o555)
    try:
        fel = _ska_ge_rott(PermissionError, lambda: gor_mapp_eller_hoppa_over(str(mapp / "ny")))
    finally:
        mapp.chmod(0o755)
    assert fel.errno == errno.EACCES


# Beslut 5: antalen. Alla test som filtret väljer räknas, som i kommandot i INSTALLERA.md, oavsett vad testen heter. "Prov utanför
# sandlådan" (39) är redan låst så, i test_granskning_39_b1_antalen_i_installera_stammer_med_testerna.


def _alla_som_filtret_valjer(filtret):
    svar = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q", "-k", filtret, str(Path(__file__).parent)],
        cwd=PROJEKTET,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert svar.returncode == 0, svar.stdout + svar.stderr
    return [rad for rad in svar.stdout.splitlines() if "::" in rad]


@pytest.mark.parametrize("filtret,antal", [("test_sparr_", 43), ("test_h1_", 31)], ids=["sparrprovet", "h1_proven"])
def test_beslut_2026_11_06_b5_antalet_i_installera_ar_alla_test_filtret_valjer(filtret, antal):
    prov = _alla_som_filtret_valjer(filtret)
    avsnitt = _avsnitt(SPARRPROV_RUBRIK)
    assert len(prov) == antal, prov
    assert f" -k {filtret} scripts/tests" in avsnitt
    assert f"`{len(prov)} passed`" in avsnitt


def test_beslut_2026_11_06_b5_de_tva_texttesten_ar_de_som_skiljer():
    # Spärrproven är 41, och de två extra är exakt de två i beslutet. Ett nytt test med filtret i namnet ger rött här.
    extra = [rad.split("::", 1)[1] for rad in _alla_som_filtret_valjer("test_sparr_") if "::test_sparr_" not in rad]
    assert sorted(extra) == [
        "test_granskning_36_p6_installera_sager_vad_som_galler[`test_sparr_lasning_av_ssh_stoppas`]",
        "test_granskning_37_p3_installera_har_sparrprovet_med_hard_lank[`test_sparr_hard_lank_till_ssh_stoppas`]",
    ]


def test_beslut_2026_11_06_b5_det_gamla_antalet_ar_borta():
    assert "`41 passed`" not in _avsnitt(SPARRPROV_RUBRIK)


# Beslut 6 och 7: raderna i BYGGPLAN.md.


def _byggplanens_rad(nummer):
    rader = (PROJEKTET / "BYGGPLAN.md").read_text(encoding="utf-8").splitlines()
    return next(rad for rad in rader if rad.startswith(f"| {nummer} |"))


def test_beslut_2026_11_06_b6_steg_15_ar_klart():
    assert "| ✅ 2026-11-06" in _byggplanens_rad(15)


@pytest.mark.parametrize("nummer", [53, 54])
def test_beslut_2026_11_06_b7_radgivarna_kontaktas_langre_fram(nummer):
    rad = _byggplanens_rad(nummer)
    assert "längre fram" in rad and "Kassio-beslutet 2026-11-05" in rad
    assert "den här veckan" not in rad


@pytest.mark.parametrize(
    "nummer,villkoret_star_kvar",
    [(109, "riktig data först efter juristens svar"), (118, "| 52, 53, 54, 105, 116, 117 |")],
)
def test_beslut_2026_11_06_b7_riktig_data_ar_en_oppen_fraga_och_villkoren_star_kvar(nummer, villkoret_star_kvar):
    rad = _byggplanens_rad(nummer)
    assert "**Öppen fråga" in rad and "Hugos beslut 2026-11-06, beslut 7" in rad
    assert villkoret_star_kvar in rad


# ---------------------------------------------------------------------------------------------
# Hugos beslut 2026-11-06 om steg 16: bash-vägen byggs inte, Öppet 7 stängs, Öppet 8 står kvar. Att CLAUDE_CODE_SHELL inte står i
# env i sparr/managed-settings.json prövas redan i test_beslut_granskning_14.py (test_bash_vagen_byggdes_inte_och_bash_filerna_har_kvar_sina_forbud).

BESLUT_16_RUBRIK = "## Hugos beslut 2026-11-06 om steg 16"
BESLUT_16 = [
    "1. Bash-vägen byggs inte. Bash-verktyget fortsätter i zsh. CLAUDE_CODE_SHELL sätts inte i de låsta inställningarna.",
    "2. Skäl: dokumentationen bekräftar fortfarande inte att CLAUDE_CODE_SHELL i env i den låsta inställningsfilen gäller i "
    "skrivbordsappen (kontrollerat 2026-11-06 på code.claude.com/docs/en/settings, code.claude.com/docs/en/env-vars och "
    "claude.com/docs/third-party/claude-desktop/code). zsh-vägen är byggd, installerad och provad i steg 15 (förbud för "
    "startfilerna, kontrollskriptet och sandlådan). Bash-vägen skulle kräva en ny version av de låsta inställningarna, ett nytt "
    "kontrollskript, förbud för bashs startfiler, ny granskning, ny installation och nya spärrprov, för en vinst som inte är visad.",
    "3. Öppet 7 stängs med det här beslutet. Öppet 8 (en rad som redan står i en startfil syns inte för sandlådan) står kvar "
    "öppen. Den gäller oavsett skal.",
    "4. Steg 16 är klart: beslutet är zsh.",
    "5. Nästa steg är en oberoende granskning av commit dbe85a9 (Öppet 69 och spärrprovet) och commiten från den här sessionen, "
    "enligt Hugos beslut 2026-11-06, beslut 8. Sedan steg 17.",
]


def _post_under_oppet(nummer):
    """Posten med numret under "## Öppet" i PROGRESS.md, fram till nästa post. Rubriken söks som en egen rad."""
    oppet = (PROJEKTET / "PROGRESS.md").read_text(encoding="utf-8").split("\n## Öppet\n", 1)[1].split("\n## ", 1)[0]
    return oppet.split(f"\n{nummer}. ", 1)[1].split(f"\n{nummer + 1}. ", 1)[0]


def _raden_i_lage_nu(etikett):
    rader = (PROJEKTET / "BYGGPLAN.md").read_text(encoding="utf-8").splitlines()
    (rad,) = [r for r in rader if r.startswith(f"- **{etikett}:**")]
    return rad[len(f"- **{etikett}:**"):].strip()


@pytest.mark.parametrize("beslut", BESLUT_16, ids=[str(n) for n in range(1, len(BESLUT_16) + 1)])
def test_beslut_steg_16_star_ordagrant_i_granskning(beslut):
    assert beslut in _avsnitt_i_granskning(BESLUT_16_RUBRIK)


def test_beslut_steg_16_rubriken_star_efter_besluten_om_oppet_69():
    text = GRANSKNING.read_text(encoding="utf-8")
    assert text.count(f"\n{BESLUT_16_RUBRIK}\n") == 1
    assert text.index(f"\n{BESLUT_16_RUBRIK}\n") > text.index(f"\n{BESLUT_06_RUBRIK}\n")


def test_beslut_steg_16_oppet_7_ar_stangd_med_hanvisning_till_beslutet():
    # Det som inte är överstruket är det som gäller. Den gamla texten står kvar överstruken, som i de andra stängda posterna.
    post = _post_under_oppet(7)
    assert post.startswith("~~**Bash-vägen")
    galler = re.sub(r"~~.*?~~", "", post, flags=re.DOTALL)
    assert "**Stängd**" in galler and "Hugos beslut 2026-11-06 om steg 16" in galler
    assert "Öppen" not in galler and "prövas" not in galler


def test_beslut_steg_16_oppet_8_ar_fortfarande_oppen():
    post = _post_under_oppet(8)
    assert post.startswith("**Det kontrollskriptet inte ser**")
    assert "~~" not in post and "Stängd" not in post
    assert "Öppen för det." in post


def test_beslut_steg_16_steget_ar_klart_i_byggplanen():
    rad = _byggplanens_rad(16)
    assert "| ✅ 2026-11-06" in rad
    assert "Beslutet är zsh" in rad and "Hugos beslut 2026-11-06 om steg 16" in rad


def test_beslut_steg_16_lage_nu_foljer_beslut_5():
    assert _raden_i_lage_nu("Senast avslutade steg").startswith("16 – ")
    assert "16 – " not in _raden_i_lage_nu("Pågående steg")
    nasta = _raden_i_lage_nu("Nästa steg")
    assert nasta.startswith("En oberoende granskning av commit dbe85a9 (Öppet 69 och spärrprovet) och commiten från sessionen för steg 16")
    assert "Hugos beslut 2026-11-06, beslut 8" in nasta and "Sedan steg 17" in nasta
    assert "Bash-vägen prövas" not in nasta


def test_beslut_steg_16_progress_har_en_post_for_sessionen():
    text = (PROJEKTET / "PROGRESS.md").read_text(encoding="utf-8")
    post = text.split("\n## Läge 2026-11-06, steg 16 klart", 1)[1].split("\n## ", 1)[0]
    assert "\nSteg i byggplanen: 16 (klart)\n" in post


# ---------------------------------------------------------------------------------------------
# Spärrtestets hjälpfunktioner. De avgör om ett försök räknas som stoppat och städar om det gick.


def _skrivning_stoppas(fil):
    """Försöker skapa en ny fil. Sant om sandlådan stoppar. Går det ändå tas filen bort direkt."""
    try:
        fd = os.open(fil, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except PermissionError:
        return True
    os.close(fd)
    os.unlink(fil)
    return False


def _mapp_stoppas(mapp):
    """Försöker skapa en ny mapp. Sant om sandlådan stoppar. Går det ändå tas mappen bort direkt."""
    try:
        os.mkdir(mapp)
    except PermissionError:
        return True
    os.rmdir(mapp)
    return False


def _tillagg_stoppas(fil, ocksa_borta=False):
    """Försöker öppna en fil för att lägga till text. Sant om sandlådan stoppar. Skriver aldrig något."""
    stoppande = (PermissionError, FileNotFoundError) if ocksa_borta else PermissionError
    try:
        with open(fil, "a", encoding="utf-8"):
            pass
    except stoppande:
        return True
    return False


def _namnbyte_stoppas(fran, till):
    """Försöker byta namn. Sant om sandlådan stoppar. Går det ändå byts namnet tillbaka direkt."""
    try:
        os.rename(fran, till)
    except PermissionError:
        return True
    os.rename(till, fran)
    return False


def _lank_stoppas(skapa, lank):
    """Försöker skapa en länk. Sant om sandlådan stoppar. Går det ändå tas länken bort direkt."""
    try:
        skapa(lank)
    except PermissionError:
        return True
    os.unlink(lank)
    return False


def _hard_lank_stoppas(fil, lank):
    """Försöker skapa en hård länk till filen. Sant om sandlådan stoppar. Går det ändå tas länken bort direkt, och filen är
    orörd. None om filen inte finns, och då säger provet ingenting."""
    try:
        os.link(fil, lank)
    except FileNotFoundError:
        return None
    except PermissionError:
        return True
    os.unlink(lank)
    return False


def test_hjalpfunktionerna_sager_nej_och_stadar_nar_inget_stoppar(tmp_path):
    fil = tmp_path / "fil"
    assert _skrivning_stoppas(fil) is False and not fil.exists()
    mapp = tmp_path / "mapp"
    assert _mapp_stoppas(mapp) is False and not mapp.exists()
    fil.write_text("x", encoding="utf-8")
    assert _tillagg_stoppas(fil) is False and fil.read_text(encoding="utf-8") == "x"
    assert _namnbyte_stoppas(fil, tmp_path / "annan") is False and fil.exists() and not (tmp_path / "annan").exists()
    lank = tmp_path / "lank"
    assert _lank_stoppas(lambda namn: os.symlink(fil, namn), lank) is False and not os.path.lexists(lank)


@pytest.mark.parametrize(
    "funktion,argument",
    [
        (_skrivning_stoppas, ("x",)),
        (_mapp_stoppas, ("x",)),
        (_tillagg_stoppas, ("x",)),
        (_namnbyte_stoppas, ("x", "y")),
    ],
    ids=["skrivning", "mapp", "tillagg", "namnbyte"],
)
def test_hjalpfunktionerna_sager_ja_nar_datorn_nekar(monkeypatch, funktion, argument):
    def nekar(*_a, **_k):
        raise PermissionError(1, "Operation not permitted")

    with monkeypatch.context() as byte:
        byte.setattr(os, "open", nekar)
        byte.setattr(os, "mkdir", nekar)
        byte.setattr(os, "rename", nekar)
        byte.setattr(builtins, "open", nekar)
        svar = funktion(*argument)
    assert svar is True


# ---------------------------------------------------------------------------------------------
# Spärrtestet. Gäller först när sandlådan är installerad och pytest körs av Claude Code i den.


def _sandladan_ar_installerad():
    try:
        data = json.loads(Path(INSTALLERADE_INSTALLNINGAR).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and isinstance(data.get("sandbox"), dict) and data["sandbox"].get("enabled") is True


def _kors_i_sandladan():
    # I sandlådan sätter Claude Code den tillfälliga mappen till sin egen mapp (provkörningen 2026-11-04:
    # /private/tmp/claude-501/).
    return os.path.realpath(tempfile.gettempdir()).startswith("/private/tmp/claude-")


def _ar_i_kopian(arbetsmapp, projektet):
    """Sant bara om sessionen står i ~/VERA/sparrprov, och testfilen också ligger där."""
    return os.path.realpath(arbetsmapp) == os.path.realpath(SPARRPROV) == os.path.realpath(projektet)


def test_sparrprovet_i_kopian_kors_inte_fran_projektet():
    assert not _ar_i_kopian(RIKTIGA_PROJEKTET, RIKTIGA_PROJEKTET)
    assert not _ar_i_kopian(SPARRPROV, RIKTIGA_PROJEKTET)
    assert not _ar_i_kopian(RIKTIGA_PROJEKTET, SPARRPROV)


def test_sparrprovet_i_kopian_kors_bara_i_kopian():
    assert _ar_i_kopian(SPARRPROV, SPARRPROV)


kraver_sandladan = pytest.mark.skipif(
    not (_sandladan_ar_installerad() and _kors_i_sandladan()),
    reason=(
        "SPÄRRTESTET HOPPAS ÖVER: sandlådan är inte installerad i de låsta inställningarna, eller pytest körs inte av "
        "Claude Code i sandlådan. Efter installationen ska inget av de här proven hoppas över (INSTALLERA.md)."
    ),
)

kraver_kopian = pytest.mark.skipif(
    not (_sandladan_ar_installerad() and _kors_i_sandladan() and _ar_i_kopian(os.getcwd(), PROJEKTET)),
    reason=(
        "SPÄRRPROVET I KOPIAN HOPPAS ÖVER: det körs bara i sandlådan, i en session startad i ~/VERA/sparrprov "
        '(INSTALLERA.md, "Spärrprovet i kopian"). Det rör aldrig projektets riktiga .git.'
    ),
)


def _git(mapp, *argument):
    return subprocess.run(
        [GIT, *argument], cwd=mapp, capture_output=True, text=True, timeout=120, check=False
    )


def _slumpat_namn():
    return f".kassio-sparrtest-{uuid.uuid4().hex}"


@pytest.fixture
def kopian():
    """Kopian ~/VERA/sparrprov. Vägrar köra om den på något sätt är projektet."""
    assert not SPARRPROV.is_symlink(), "kopian är en länk"
    assert (SPARRPROV / ".git").is_dir() and not (SPARRPROV / ".git").is_symlink(), "kopian har ingen egen mapp .git"
    if RIKTIGA_PROJEKTET.exists():
        assert not os.path.samefile(SPARRPROV, RIKTIGA_PROJEKTET), "kopian är projektet"
        assert not os.path.samefile(SPARRPROV / ".git", RIKTIGA_PROJEKTET / ".git"), "kopian delar .git med projektet"
    return SPARRPROV


@pytest.fixture
def undermapp(kopian):
    """En ny mapp i kopian, som tas bort efter testet. Den är inte i .git, så den får skapas."""
    mapp = kopian / _slumpat_namn()
    mapp.mkdir()
    yield mapp
    shutil.rmtree(mapp)


# Inget i sandlådan kan skriva i .git, skapa en fil eller mapp med namnet .git, skriva .git/commondir eller byta namn på .git.
# Lyckas något av det backar Hugo direkt (Hugos beslut 2026-11-05, beslut 4).


@kraver_kopian
@pytest.mark.parametrize(
    "namn",
    [
        ".git/commondir",
        ".git/COMMONDIR",
        ".git/config.worktree",
        ".git/hooks/prov",
        ".GIT/HOOKS/prov",
        ".git/info/prov",
        ".git/prov",
        ".git/objects/prov",
        ".git/refs/heads/prov",
        ".git/logs/prov",
    ],
)
def test_sparr_kopian_ny_fil_i_git_stoppas(kopian, namn):
    assert _skrivning_stoppas(kopian / namn)


@kraver_kopian
@pytest.mark.parametrize("namn", [".git/modules", ".git/rebase-merge", ".git/rebase-apply", ".git/sequencer", ".git/worktrees"])
def test_sparr_kopian_ny_mapp_i_git_stoppas(kopian, namn):
    assert _mapp_stoppas(kopian / namn)


@kraver_kopian
@pytest.mark.parametrize("namn", [".git/config", ".git/index", ".git/HEAD", ".git/info/exclude", ".GIT/CONFIG"])
def test_sparr_kopian_fil_i_git_gar_inte_att_andra(kopian, namn):
    fore = (kopian / namn).read_bytes()
    assert _tillagg_stoppas(kopian / namn)
    assert (kopian / namn).read_bytes() == fore


@kraver_kopian
def test_sparr_kopian_git_config_gar_inte_att_andra_genom_lankar(kopian, undermapp):
    config = kopian / ".git" / "config"
    fore = config.read_bytes()
    # Antingen stoppas länken, eller så stoppas skrivningen genom den.
    for lank, skapa in ((undermapp / "hard", os.link), (undermapp / "mjuk", os.symlink)):
        try:
            skapa(config, lank)
        except PermissionError:
            continue
        assert _tillagg_stoppas(lank)
    info = os.stat(config)
    assert _tillagg_stoppas(f"/.vol/{info.st_dev}/{info.st_ino}", ocksa_borta=True)
    assert config.read_bytes() == fore


@kraver_kopian
@pytest.mark.parametrize(
    "fran,till",
    [(".git", ".git-flyttad"), (".git", ".kassio-git"), (".git/hooks", ".git/hooks-undan"), (".git/hooks", ".hooks-undan")],
)
def test_sparr_kopian_git_gar_inte_att_byta_namn_pa(kopian, fran, till):
    assert _namnbyte_stoppas(kopian / fran, kopian / till)
    assert (kopian / fran).is_dir()


@kraver_kopian
def test_sparr_kopian_arbetsmappen_gar_inte_att_flytta(kopian, tmp_path):
    # Granskning 35, P1. Hugos beslut 2026-11-05 om granskning 35, beslut 1.
    assert _namnbyte_stoppas(kopian, tmp_path / "flyttad")
    assert (kopian / ".git").is_dir()


@kraver_kopian
@pytest.mark.parametrize("namn", [".git", ".GIT"])
def test_sparr_kopian_fil_eller_mapp_med_namnet_git_stoppas(undermapp, namn):
    assert _skrivning_stoppas(undermapp / namn)
    assert _mapp_stoppas(undermapp / namn)


@kraver_kopian
def test_sparr_kopian_mapp_gar_inte_att_byta_namn_till_git(undermapp):
    (undermapp / "vanlig").mkdir()
    assert _namnbyte_stoppas(undermapp / "vanlig", undermapp / ".git")


@kraver_kopian
def test_sparr_kopian_lank_med_namnet_git_stoppas(undermapp):
    assert _lank_stoppas(lambda namn: os.symlink("vanlig", namn), undermapp / ".git")


@kraver_kopian
def test_sparr_kopian_git_status_och_log_fungerar_men_inte_add_och_commit(kopian, undermapp):
    # Beslut 2 och 5: agenten committar inte, och ingenting i sandlådan kan ändra git-historiken.
    identitet = ("-c", "user.name=Prov", "-c", "user.email=prov@example.invalid", "-c", "commit.gpgsign=false")
    fore = _git(kopian, "rev-parse", "HEAD").stdout.strip()
    assert fore
    status = _git(kopian, "status", "--porcelain")
    assert status.returncode == 0, status.stderr
    assert _git(kopian, "log", "-1").returncode == 0
    (undermapp / "prov.txt").write_text("prov\n", encoding="utf-8")
    assert _git(kopian, "add", str(undermapp / "prov.txt")).returncode != 0
    assert _git(kopian, *identitet, "commit", "--allow-empty", "-q", "-m", "prov").returncode != 0
    assert _git(kopian, *identitet, "commit", "--amend", "--no-edit", "--no-verify", "-q").returncode != 0
    assert _git(kopian, "rev-parse", "HEAD").stdout.strip() == fore


# Det här gäller i alla sessioner i sandlådan, också i projektet.


@kraver_sandladan
def test_sparr_git_status_och_lasning_fungerar_i_projektet():
    # Hugos beslut 2026-11-05: förbuden får inte stoppa det som ska fungera.
    status = _git(PROJEKTET, "status")
    assert status.returncode == 0, status.stderr
    assert (PROJEKTET / "SPEC.md").read_text(encoding="utf-8")


@kraver_sandladan
@pytest.mark.parametrize("namn", [".git", ".GIT"])
def test_sparr_fil_eller_mapp_med_namnet_git_stoppas_i_tillfalliga_mappen(tmp_path, namn):
    assert _skrivning_stoppas(tmp_path / namn)
    assert _mapp_stoppas(tmp_path / namn)


@kraver_sandladan
def test_sparr_mapp_i_venv_stoppas_i_tillfalliga_mappen(tmp_path):
    with pytest.raises(PermissionError):
        os.makedirs(tmp_path / ".venv" / "bin")


@kraver_sandladan
def test_sparr_skrivning_utanfor_projektet_stoppas():
    assert _skrivning_stoppas(HEM / _slumpat_namn())


@kraver_sandladan
@pytest.mark.parametrize(
    "mapp",
    [
        HEM / ".local" / "share" / "claude",
        HEM / "Library" / "Application Support" / "Claude" / "claude-code",
        Path("/Applications/Claude.app"),
    ],
    ids=["local-share-claude", "appens-claude-code", "appen"],
)
def test_sparr_skrivning_i_appen_och_claude_code_stoppas(mapp):
    if not mapp.is_dir():
        pytest.skip(f"{mapp} finns inte på den här datorn")
    assert _skrivning_stoppas(mapp / _slumpat_namn())


@kraver_sandladan
def test_sparr_lasning_av_ssh_stoppas():
    # Mappen och testfilen skapas av Hugo i "Spärrprovet i kopian" (Hugos beslut 2026-11-05 om granskning 36, P6). Här, i
    # hela sviten före det provet, finns mappen inte, och då hoppas provet över.
    mapp = _ssh_mappen()
    svar = _lasning_stoppas(mapp, mapp / "prov")
    if svar is None:
        pytest.skip("~/.ssh finns inte på den här datorn")
    assert svar, "~/.ssh gick att läsa: sandlådan stoppar inte läsning där"


@kraver_sandladan
def test_sparr_hard_lank_till_ssh_stoppas(tmp_path):
    # Ett uttalat undantag från länkregeln i CLAUDE.md, bara här (Hugos beslut 2026-11-05 om granskning 37, P3). Bara testfilen
    # från "Spärrprovet i kopian" prövas, aldrig en annan fil i mappen, och testet körs bara i sandlådan. En hård länk är ett
    # andra namn på samma fil. Gick den att skapa skulle Hugos git, som körs utanför sandlådan, kunna läsa filen genom den.
    svar = _hard_lank_stoppas(_ssh_mappen() / "prov", tmp_path / "lank")
    if svar is None:
        pytest.skip("~/.ssh/prov finns inte på den här datorn")
    assert svar, "en hård länk till ~/.ssh/prov gick att skapa: sandlådan stoppar den inte"
