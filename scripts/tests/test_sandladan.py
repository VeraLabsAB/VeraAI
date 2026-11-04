"""Steg 15: sandlådan (Hugos beslut 2026-11-04 om sandlådan, GRANSKNING.md).

Två delar:

- Testerna som läser sparr/managed-settings.json och visar varje beslut 1-7. De körs alltid.
- Spärrtestet, som prövar att sandlådan faktiskt stoppar. Det hoppas över med ett tydligt meddelande när sandlådan
  inte är installerad, eller när pytest inte körs av Claude Code i sandlådan. Då stoppar inget, så provet säger inget.

Spärrtestet skriver bara i testets tillfälliga mapp, utom proven att skrivning utanför stoppas. Där försöker det skapa
en ny fil med ett slumpat namn, och tar bort den direkt om det ändå gick. Provet för ~/.ssh visar aldrig vad som ligger
där. Hugos beslut 2026-11-04 (uppdraget för steg 15) säger att spärrtestet ska pröva just det.
"""

import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturen används av pytest via namnet)
    AVSMALNADE_FORBUD,
    INSTALLERA,
    INSTALLERADE_INSTALLNINGAR,
    INSTALLNINGAR,
    PROJEKTET,
    VAKTEN,
    vakt,
)

# Vaktens kontrollsumma, oförändrad sedan 2026-10-28 (INSTALLERA.md, steg 5). Beslut 5: vakten ändras inte.
VAKTENS_SUMMA = "314df00b4239877d21e0fef7d8f11c844a75d07276ad0af32baa94db8e92d10d"
GIT = "/usr/bin/git"
HEM = Path.home()
BYTE_RUBRIK = "## Byte till versionen med sandlåda (steg 15)"


def _installningar():
    return json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))


def _byte_avsnittet():
    text = INSTALLERA.read_text(encoding="utf-8")
    assert BYTE_RUBRIK in text
    return text.split(BYTE_RUBRIK, 1)[1].split("\n## ", 1)[0]


# ---------------------------------------------------------------------------------------------
# Beslut 1-7, som de står i filen.


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


def test_beslut_6_forbuden_ar_avsmalnade_och_alla_andra_ar_kvar_i_samma_ordning(vakt):
    # Vakten är oförändrad, så dess lista är den gamla listan i inställningarna.
    forvantade = []
    for regel in vakt.SKRIVFORBUD:
        forvantade += AVSMALNADE_FORBUD.get(regel, [regel])
    edit = [r[len("Edit("):-1] for r in _installningar()["permissions"]["deny"] if r.startswith("Edit(")]
    assert edit == forvantade
    for regel in ("//**/.git/**", "//**/.git", "//**/.venv/**"):
        assert regel not in edit


def test_beslut_6_vakten_stoppar_fortfarande_fil_verktygen_i_hela_git_och_venv(vakt):
    # Vakten ändras inte (beslut 5), så för fil-verktygen lättar spärren inte i praktiken: vakten stoppar först.
    for sokvag, regel in (
        ("/x/projekt/.git/index", "//**/.git/**"),
        ("/x/projekt/.git", "//**/.git"),
        ("/x/annan/.venv/bin/python", "//**/.venv/**"),
    ):
        assert vakt._forbud_som_passar(vakt._andra_namn(sokvag), ["/Users/vera"]) == regel


def test_beslut_7_sandladan_och_read_forbjuder_lasning_av_ssh():
    # Hugos svar i chatten 2026-11-04: Read(~/.ssh/**) läggs till, eftersom denyRead inte stoppar fil-verktyget Read.
    installningar = _installningar()
    assert installningar["sandbox"]["filesystem"]["denyRead"] == ["~/.ssh"]
    assert "Read(~/.ssh/**)" in installningar["permissions"]["deny"]


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
        "filesystem",
    }


@pytest.mark.parametrize(
    "text",
    [
        "--version",
        "shasum -a 256",
        "managed-settings.fore-sandladan.json",
        "scripts/tests/test_sandladan.py",
        "Backa till förra versionen",
        "149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2",
    ],
)
def test_installera_har_version_kopia_kontrollsumma_kontroll_och_backning(text):
    assert text in _byte_avsnittet()


def test_bytet_har_exakt_de_har_kommandona_med_sudo():
    mapp = '"/Library/Application Support/ClaudeCode'
    aktiv = f'{mapp}/managed-settings.json"'
    sparad = f'{mapp}/managed-settings.fore-sandladan.json"'
    rader = [rad.strip() for rad in _byte_avsnittet().splitlines() if rad.strip().startswith("sudo ")]
    assert rader == [
        f"sudo cp -i {aktiv} {sparad}",
        f"sudo chown root:wheel {sparad}",
        f"sudo chmod 644 {sparad}",
        f"sudo cp ~/VERA/agent/sparr/managed-settings.json {aktiv}",
        f"sudo chown root:wheel {aktiv}",
        f"sudo chmod 644 {aktiv}",
        f"sudo cp {sparad} {aktiv}",
    ]


def test_summan_i_bytet_ar_den_nya_filens_summa():
    summa = hashlib.sha256(INSTALLNINGAR.read_bytes()).hexdigest()
    assert _byte_avsnittet().count(summa) == 2


def test_provkorningen_har_samma_fem_nycklar_som_filen():
    text = INSTALLERA.read_text(encoding="utf-8")
    avsnitt = text.split("## Provkörning med sandlådan, före bytet (steg 15)", 1)[1].split("\n## ", 1)[0]
    rad = next(r for r in avsnitt.splitlines() if r.startswith("~/.local/bin/claude --settings "))
    data = json.loads(rad.split("'", 2)[1])
    sandbox = dict(_installningar()["sandbox"])
    del sandbox["filesystem"]
    assert data == {"sandbox": sandbox}
    assert "-rfs scripts/tests" in avsnitt


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


kraver_sandladan = pytest.mark.skipif(
    not (_sandladan_ar_installerad() and _kors_i_sandladan()),
    reason=(
        "SPÄRRTESTET HOPPAS ÖVER: sandlådan är inte installerad i de låsta inställningarna, eller pytest körs inte av "
        "Claude Code i sandlådan. Efter installationen ska inget av de här proven hoppas över (INSTALLERA.md)."
    ),
)


def _git(mapp, *argument):
    return subprocess.run(
        [GIT, *argument], cwd=mapp, capture_output=True, text=True, timeout=120, check=False
    )


def _kopia_av_repot(tmp_path):
    """En kopia av repot med en riktig mapp .git. Förbuden gäller .git/hooks och .git/config var de än ligger, så
    git-mappen byggs under ett annat namn och flyttas sedan till .git."""
    arbete = tmp_path / "kopia"
    data = tmp_path / "git-data"
    klon = _git(tmp_path, "clone", "--quiet", "--no-hardlinks", f"--separate-git-dir={data}", str(PROJEKTET), str(arbete))
    assert klon.returncode == 0, klon.stderr
    (arbete / ".git").unlink()
    os.rename(data, arbete / ".git")
    assert _git(arbete, "status", "--porcelain").returncode == 0
    return arbete


def _skrivning_stoppas(fil):
    """Försöker skapa en ny fil. Sant om sandlådan stoppar. Går det ändå tas filen bort direkt."""
    try:
        fd = os.open(fil, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except PermissionError:
        return True
    os.close(fd)
    os.unlink(fil)
    return False


def _tillagg_stoppas(fil):
    """Försöker lägga till text i en fil som finns. Sant om sandlådan stoppar. Skriver inget om den stoppar."""
    try:
        with open(fil, "a", encoding="utf-8"):
            pass
    except PermissionError:
        return True
    return False


def _slumpat_namn():
    return f".kassio-sparrtest-{uuid.uuid4().hex}"


@kraver_sandladan
def test_sparr_git_add_och_commit_fungerar_i_en_kopia_av_repot(tmp_path):
    arbete = _kopia_av_repot(tmp_path)
    fore = _git(arbete, "rev-parse", "HEAD").stdout.strip()
    (arbete / "prov.txt").write_text("prov\n", encoding="utf-8")
    tillagd = _git(arbete, "add", "prov.txt")
    assert tillagd.returncode == 0, tillagd.stderr
    sparad = _git(
        arbete, "-c", "user.name=Prov", "-c", "user.email=prov@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "-q", "-m", "prov",
    )
    assert sparad.returncode == 0, sparad.stderr
    assert _git(arbete, "rev-parse", "HEAD").stdout.strip() != fore


@kraver_sandladan
@pytest.mark.parametrize(
    "namn",
    # macOS skiljer inte på stora och små bokstäver, så .GIT/hooks är samma mapp (granskning 17, H6).
    [".git/hooks/prov", ".git/info/prov", ".GIT/hooks/prov"],
    ids=["hooks", "info", "stora-bokstaver"],
)
def test_sparr_ny_fil_i_git_hooks_och_git_info_stoppas(tmp_path, namn):
    assert _skrivning_stoppas(_kopia_av_repot(tmp_path) / namn)


@kraver_sandladan
def test_sparr_git_config_gar_inte_att_andra(tmp_path):
    arbete = _kopia_av_repot(tmp_path)
    fore = (arbete / ".git" / "config").read_bytes()
    assert _tillagg_stoppas(arbete / ".git" / "config")
    assert (arbete / ".git" / "config").read_bytes() == fore


@kraver_sandladan
def test_sparr_mappen_hooks_gar_inte_att_flytta_undan(tmp_path):
    arbete = _kopia_av_repot(tmp_path)
    with pytest.raises(PermissionError):
        os.rename(arbete / ".git" / "hooks", arbete / ".git" / "hooks-undan")


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
