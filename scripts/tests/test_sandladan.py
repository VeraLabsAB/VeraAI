"""Steg 15: sandlådan (Hugos beslut 2026-11-04 om sandlådan och Hugos beslut 2026-11-05 om granskning 34, GRANSKNING.md).

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
    # Tar man bort sandbox-blocket och Read(~/.ssh/**) ska det bli exakt filen som är installerad i dag, byte för byte.
    rader = INSTALLNINGAR.read_text(encoding="utf-8").splitlines(keepends=True)
    start = rader.index('  "sandbox": {\n')
    slut = rader.index("  },\n", start)
    kvar = rader[:start] + rader[slut + 1:]
    kvar.remove('      "Read(~/.ssh/**)",\n')
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
    assert installningar["requiredMinimumVersion"] == "2.1.295"
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
        "git commit -m",
        "från installationen av steg 15",
        "Prov som inte kan köras i sandlådan",
        "grupp D och H1-proven",
        "Hugos beslut 2026-11-05",
    ],
)
def test_2026_11_05_beslut_2_och_3_star_i_claude_md(text):
    assert text in CLAUDE_MD.read_text(encoding="utf-8")


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

# Ordningen är granskning 34, P5: version, summor, spara, kopiera, kontrollera, kontrollen efter bytet, backa.
BYTET = [
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
    "cd ~/VERA/agent",
    "rm -rf ~/VERA/sparrprov",
    "ls -ld ~/VERA/sparrprov",
]

UTANFOR_K = "test_h6_en_lank_till_git_stoppas or test_beslut_1_gamla_venv_i_projektet_stoppas or test_h1_"
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
        "H1-PROVET HOPPAS ÖVER",
        "varje gång vakten eller de låsta inställningarna ändras",
        "granskad",
        "P6",
    ],
)
def test_prov_utanfor_sandladan_sager_vad_som_galler(text):
    assert text in _avsnitt(UTANFOR_RUBRIK)


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
