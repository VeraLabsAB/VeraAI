"""Steg 15: sandlådan (Hugos beslut 2026-11-04 om sandlådan, Hugos beslut 2026-11-05 om granskning 34 och Hugos beslut
2026-11-05 efter P6, GRANSKNING.md).

Tre delar:

- Testerna som läser sparr/managed-settings.json och visar besluten. De körs alltid.
- Testerna av INSTALLERA.md. De godtar bara kända kommandon, i rätt ordning, och stoppar allt annat (granskning 34, P5).
- Spärrtestet, som prövar att sandlådan faktiskt stoppar. Det hoppas över med ett tydligt meddelande när sandlådan inte är
  installerad, eller när pytest inte körs av Claude Code i sandlådan. Då stoppar inget, så provet säger inget.

Spärrtestet skriver i testets tillfälliga mapp, och i två fall utanför den:

- Proven att skrivning utanför projektet stoppas försöker skapa en ny fil med ett slumpat namn, och tar bort den direkt om
  det ändå gick. Provet för ~/.ssh visar aldrig vad som ligger där. Hugos beslut 2026-11-04 säger att det ska prövas.
- Proven test_sparr_kopian_ gäller kopian ~/VERA/sparrprov, som Hugo förbereder utanför sandlådan (Hugos beslut 2026-11-05,
  beslut 4, ett undantag från regeln "Prov och test", bara för spärrtestet). De körs bara i en session startad i kopian,
  vägrar om kopian är projektet, och rör aldrig projektets riktiga .git.
"""

import builtins
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
    gor_mapp_eller_hoppa_over,
    installera_utan_sandlada,
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
    '"network":{"allowAllUnixSockets":false,"allowLocalBinding":false}}}'
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
HUGOS_FASTA_KOMMANDON = ["git status --short --ignored", "git add -A", "git commit -F COMMIT_MSG.txt"]
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
    "grep -n -e sandbox -e additionalDirectories ~/.claude/settings.json",
    "grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.json",
    "grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.local.json",
    f"{PYTHON} -q --tb=short -rfs scripts/tests",
    # Hugos beslut 2026-11-05 om granskning 35, beslut 6: de fasta kommandona, som Hugo alltid skriver själv.
    *HUGOS_FASTA_KOMMANDON,
    f"sudo cp {SPARAD} {AKTIV}",
    f"{SUMMA} {AKTIV}",
]

SPARRPROVET = [
    "ls -ld ~/VERA/sparrprov",
    "git clone --no-hardlinks ~/VERA/agent ~/VERA/sparrprov",
    "cd ~/VERA/sparrprov",
    "git log -1 --format=%H",
    "~/.local/bin/claude",
    f"{PYTHON} -q --tb=short -rfs -k test_sparr_ scripts/tests",
    # Hugos beslut 2026-11-05 efter P6, beslut 1: H1-proven i appen, med kommandot från Hugos körning.
    f"{PYTHON} -q --tb=line -rs -k test_h1_ scripts/tests",
    "cd ~/VERA/agent",
    "rm -rf ~/VERA/sparrprov",
    "ls -ld ~/VERA/sparrprov",
]

# Bara grupp D (Hugos beslut 2026-11-05 efter P6, beslut 1).
UTANFOR_K = "test_h6_en_lank_till_git_stoppas or test_beslut_1_gamla_venv_i_projektet_stoppas"
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
    f'sudo mv {INSTALLERAD_VAKT_CITERAD} {MAPP}/vera/kommandosparr.py.av"',
    f'sudo mv {MAPP}/vera/kommandosparr.py.av" {INSTALLERAD_VAKT_CITERAD}',
    f"{SUMMA} {INSTALLERAD_VAKT_CITERAD} {AKTIV}",
]

# Ord som får stå efter sudo i löpande text, där de beskriver kommandon i rutorna eller ett prov som ska stoppas.
SUDO_I_TEXT = {"mkdir", "chown", "chmod", "ditto", "cp", "mv", "ls", "och", "stoppas.**"}


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


def test_lopande_text_namner_inget_okant_kommando():
    # Också utanför rutorna, eftersom Hugo kopierar det som står. sudo bara med kända ord, och aldrig rm, curl eller wget
    # med tillägg.
    for rad in _lopande_text(INSTALLERA.read_text(encoding="utf-8")):
        for ord_ in re.findall(r"\bsudo\s+([^\s`]+)", rad):
            assert ord_ in SUDO_I_TEXT, rad
        assert not re.search(r"\brm\s+-", rad), rad
        assert not re.search(r"\b(curl|wget)\s", rad), rad


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
        "`git add` och `git commit` stoppas",
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


def test_provkorningen_har_samma_nycklar_som_filen_utom_filesystem():
    sandbox = dict(_installningar()["sandbox"])
    del sandbox["filesystem"]
    assert json.loads(PROVKORNINGENS_NYCKLAR) == {"sandbox": sandbox}


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
def test_granskning_35_besluten_star_ordagrant_sist_i_granskning(beslut):
    avsnitt = GRANSKNING.read_text(encoding="utf-8").split("## Hugos beslut 2026-11-05 om granskning 35", 1)[1]
    assert beslut in avsnitt


def test_granskning_35_del_e_star_i_progress_under_steg_15():
    forsta_laget = PROGRESS.read_text(encoding="utf-8").split("\n## Läge", 1)[1].split("\n## ", 1)[0]
    assert "Steg i byggplanen: 15" in forsta_laget
    assert GRANSKNING_35_BESLUT[10].split(" ", 1)[1] in forsta_laget


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
    assert (len(prov), len(i_kopian), len(prov) - len(i_kopian)) == (40, 31, 9)


@pytest.mark.parametrize(
    "rubrik,text",
    [
        (SPARRPROV_RUBRIK, "`40 passed`"),
        (SPARRPROV_RUBRIK, "`39 passed, 1 skipped`"),
        (SPARRPROV_RUBRIK, "flytta hela arbetsmappen"),
        (SPARRPROV_RUBRIK, "`31 passed`"),
        (PROVKORNING_RUBRIK, "`48 skipped`"),
        (PROVKORNING_RUBRIK, "`SPÄRRTESTET HOPPAS ÖVER`: **9** prov"),
        (PROVKORNING_RUBRIK, "`SPÄRRPROVET I KOPIAN HOPPAS ÖVER`: **31** prov"),
        (PROVKORNING_RUBRIK, "2.1.318"),
        (BYTE_RUBRIK, "**33** överhoppade"),
        (BYTE_RUBRIK, "**34** om `~/.ssh` inte finns"),
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
        "Varje session börjar och slutar med `git status --short --ignored`",
        "Inga sessioner i worktrees tills det finns ett prov för det",
        "Är ett H1-prov rött i appen: backa inte, men stanna. Kör inga sessioner tills det är avgjort.",
        "Det avgörs av en session som bara läser, som Hugo startar, och som bara tittar på det provet",
        "Sessionen skriver bara commit-meddelandet i filen `COMMIT_MSG.txt` i projektmappen",
        "skriver aldrig ett kommando som Hugo ska klistra in",
        "`git status --short --ignored`, `git add -A` och `git commit -F COMMIT_MSG.txt`",
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
    assert "`git status --short --ignored`" in avsnitt


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
    mapp = HEM / ".ssh"
    try:
        os.listdir(mapp)
    except PermissionError:
        return
    except FileNotFoundError:
        pytest.skip("~/.ssh finns inte på den här datorn")
    pytest.fail("~/.ssh gick att lista: sandlådan stoppar inte läsning där")
