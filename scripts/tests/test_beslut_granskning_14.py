"""Hugos beslut 2026-10-28 om fynden i granskning 14 (GRANSKNING.md, "Hugos svar 2026-10-28 efter granskning 14").

- Bash-vägen (CLAUDE_CODE_SHELL=/bin/bash) byggdes inte: dokumentationen bekräftar inte att variabeln gäller i
  skrivbordsappen (PROGRESS.md). Granskarens väg för R1 är byggd.
- R1: förbud för ~/.zcompdump, och en kontroll av zsh:s mappar för funktioner (fpath) i INSTALLERA.md steg 4 i.
- R2: INSTALLERA.md steg 4 h visar vilka filer zsh läser in, på båda datorerna.
- R3: kontrollen av alias och funktioner är vänd. Allt som inte står i listan över väntade namn stoppar.
- R4: SPEC 7.1 säger att vakten prövar mappen där varje länk ligger, inte länkfilen själv.
- R5: INSTALLERA.md säger vad som syns när steg 6–11 går bra, och steg 4 d på en dator utan nvm.

Proven med zsh körs med zsh -f, som inte läser några av Hugos filer, med en tillfällig hemmapp och bara
systemets mappar i PATH. Kommandona hämtas ur INSTALLERA.md, så att det är just de som prövas.
"""

import os
import subprocess

import pytest

from test_kommandosparr import (
    ALIAS_KOMMANDON,
    FPATH_KOMMANDON,
    FUNKTIONER_KOMMANDO,
    INSTALLERA,
    KROK_KOMMANDO,
    KROK_VANTAT,
    KROKLISTOR,
    ZSH_FILER_KOMMANDO,
    _en_rad,
    _forsta_sudo,
    _installationskommandon,
    _installningar,
    _kontrollen,
    _spec_7_1,
    _steg,
)

ZSH = "/bin/zsh"
inget_zsh = pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")

# Det som nvm:s fil bash_completion kör i zsh (granskning 14, R1), och bashcompinit, som den kör sedan.
NVM_COMPINIT = "autoload -U +X compinit && compinit\nautoload -U +X bashcompinit && bashcompinit\n"


def _zsh(tmp_path, skript):
    miljo = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "LANG": "C"}
    return subprocess.run(
        [ZSH, "-f", "-c", skript], capture_output=True, text=True, env=miljo, cwd=tmp_path, timeout=30
    )


def _steg_4():
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    return steget


def _caspers():
    return _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Caspers dator", 1)[1].split("\n## ", 1)[0])


# ---------------------------------------------------------------------------------------------
# Bash-vägen byggdes inte.


def test_bash_vagen_byggdes_inte_och_bash_filerna_har_kvar_sina_forbud():
    # CLAUDE_CODE_SHELL sätts inte i den låsta inställningsfilen: att den gäller i skrivbordsappen är inte
    # bekräftat (appens startmiljö går före inställningsfilernas env). Förbuden för bash-filerna står kvar.
    installningar = _installningar()
    assert "CLAUDE_CODE_SHELL" not in installningar.get("env", {})
    for regel in ("Edit(~/.bashrc)", "Edit(~/.bash_profile)", "Edit(~/.profile)"):
        assert regel in installningar["permissions"]["deny"], regel


# ---------------------------------------------------------------------------------------------
# R1: ~/.zcompdump och zsh:s mappar för funktioner.


@pytest.mark.parametrize("regel", ["Edit(~/.zcompdump)", "Edit(~/.zcompdump*)"])
def test_r1_installningarna_nekar_att_skriva_i_zcompdump(regel):
    # ~/.zcompdump* täcker också namnen som oh-my-zsh använder (.zcompdump-<dator>-<version>) och
    # compinits kompilerade fil (.zcompdump.zwc).
    assert regel in _installningar()["permissions"]["deny"]


def test_r1_installera_namner_forbudet_for_zcompdump():
    vad = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[0])
    assert "`~/.zcompdump`" in vad and "granskning 14, R1" in vad


def test_r1_fpath_kontrolleras_fore_installationen():
    _, rader = _installationskommandon()
    for kommando in FPATH_KOMMANDON:
        assert rader.count(kommando) == 1, kommando
        assert rader.index(kommando) < _forsta_sudo(rader), kommando
    steget = _en_rad(_steg_4().split("**i. Kontrollera zsh:s mappar för funktioner**", 1)[1])
    assert "granskning 14, R1, Hugos beslut 2026-10-28" in steget
    assert "`~/.zcompdump`" in steget and "`compinit`" in steget
    assert "ägaren är `root`" in steget and "stoppa och fråga" in steget.lower()


@inget_zsh
def test_r1_fpath_pa_den_har_datorn_ar_den_som_installera_vantar_sig(tmp_path):
    # Mapparna i fpath med zsh -f, före och efter compinit, ska vara de som steg 4 i godtar.
    (visa,) = [k for k in FPATH_KOMMANDON if k.startswith("print")]
    for skript in (visa, NVM_COMPINIT + visa):
        rader = _zsh(tmp_path, skript).stdout.splitlines()
        assert rader, skript
        for mapp in rader:
            assert mapp.startswith("/usr/share/zsh/") or mapp == "/usr/local/share/zsh/site-functions", mapp


# ---------------------------------------------------------------------------------------------
# R2: vilka filer zsh läser in.

NVM_RADER = (
    'export NVM_DIR="$HOME/.nvm"\n'
    '[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"  # This loads nvm\n'
    '[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion\n'
)
# Raderna från steg 4 b och c.
STEG_4_RADER = (
    '[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )\n'
    "path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )\n"
)


def test_r2_steget_finns_fore_installationen_och_for_casper():
    _, rader = _installationskommandon()
    assert rader.count(ZSH_FILER_KOMMANDO) == 1
    assert rader.index(ZSH_FILER_KOMMANDO) < _forsta_sudo(rader)
    steget = _en_rad(_steg_4().split("**h. Kontrollera vilka filer zsh läser in**", 1)[1])
    assert "granskning 14, R2, Hugos beslut 2026-10-28" in steget and "**båda** datorerna" in steget
    assert "Står någon annan rad där: stoppa och fråga." in steget
    caspers = _caspers()
    assert "Steg 4 h, vilka filer Caspers zsh läser in" in caspers and "stoppa och fråga" in caspers


@inget_zsh
def test_r2_pa_en_dator_med_nvm_visas_bara_nvm_raderna(tmp_path):
    (tmp_path / ".zshrc").write_text(NVM_RADER + STEG_4_RADER, encoding="utf-8")
    ut = _zsh(tmp_path, ZSH_FILER_KOMMANDO)
    rader = ut.stdout.splitlines()
    assert len(rader) == 2, ut.stdout
    assert rader[0].endswith('.zshrc:2:[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"  # This loads nvm')
    assert "bash_completion" in rader[1] and rader[1].split(":")[1] == "3"
    # Filerna som inte finns nämns, som steget säger.
    for fil in (".zshenv", ".zprofile", ".zlogin"):
        assert f"{fil}: No such file or directory" in ut.stderr, ut.stderr


@inget_zsh
def test_r2_pa_en_dator_utan_nvm_visas_inga_rader(tmp_path):
    (tmp_path / ".zshrc").write_text(STEG_4_RADER, encoding="utf-8")
    assert _zsh(tmp_path, ZSH_FILER_KOMMANDO).stdout == ""


@pytest.mark.parametrize(
    "fil,rad",
    [
        (".zshrc", 'source "$ZSH/oh-my-zsh.sh"'),
        (".zprofile", 'eval "$(/opt/homebrew/bin/brew shellenv)"'),
        (".zshrc", 'eval "$(conda shell.zsh hook)"'),
        (".zshrc", 'test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"'),
        (".zshrc", ". ~/.annan_fil"),
        (".zshenv", "autoload -Uz compinit && compinit"),
        (".zlogin", "fpath=(~/.zfunc $fpath)"),
        (".zshenv", 'export ZDOTDIR="$HOME/.config/zsh"'),
    ],
)
@inget_zsh
def test_r2_andra_rader_som_laser_in_filer_visas(tmp_path, fil, rad):
    (tmp_path / ".zshrc").write_text(NVM_RADER + STEG_4_RADER, encoding="utf-8")
    with open(tmp_path / fil, "a", encoding="utf-8") as ut:
        ut.write(rad + "\n")
    rader = _zsh(tmp_path, ZSH_FILER_KOMMANDO).stdout.splitlines()
    assert any(r.endswith(rad) and f"{fil}:" in r for r in rader), rader
    assert len(rader) == 3, rader


# ---------------------------------------------------------------------------------------------
# R3: allt som inte står i listan över väntade namn stoppar.

# Funktioner som Hugos Terminal har utöver compinit: nvm:s och Terminals egna.
VANTADE = "nvm() { }\nnvm_ls() { }\n__nvm() { }\nshell_session_save() { }\nupdate_terminal_cwd() { }\n"
VANTADE_ALIAS = {"run-help=man", "which-command=whence"}


def test_r3_installera_har_den_vanda_kontrollen_fore_och_efter():
    # Före och efter installationen (räknat i test_beslut_granskning_13.py, P1 a), och typeset -f +
    # används inte längre: efter nvm:s compinit visar det fler än 900 namn.
    _, rader = _installationskommandon()
    assert rader.count(FUNKTIONER_KOMMANDO) == 2
    assert "typeset -f +" not in rader
    assert ALIAS_KOMMANDON == ("alias", "alias -s", FUNKTIONER_KOMMANDO, KROK_KOMMANDO)
    fore = _en_rad(_steg_4().split("**g. Kontrollera alias och funktioner**", 1)[1].split("**h. ", 1)[0])
    efter = _en_rad(_kontrollen().split("**Alias och funktioner, igen efter installationen**", 1)[1].split("\n2. ", 1)[0])
    for steget in (fore, efter):
        assert "granskning 14, R3, Hugos beslut 2026-10-28" in steget
        assert "exakt två rader" in steget and "`run-help=man`" in steget and "`which-command=whence`" in steget
        assert "en enda rad, `SLUT`" in steget
        assert "TRAPDEBUG" in steget
    assert "**globalt alias**" in fore
    assert "Leta efter namnen på kommandona" not in fore
    assert "Leta efter samma namn" not in efter


@inget_zsh
def test_r3_med_bara_vantade_namn_visas_tva_alias_och_slut(tmp_path):
    ut = _zsh(tmp_path, NVM_COMPINIT + VANTADE + "alias\nprint -r -- ---\n" + FUNKTIONER_KOMMANDO)
    alias_, funktioner = ut.stdout.split("---\n")
    assert set(alias_.splitlines()) == VANTADE_ALIAS and len(alias_.splitlines()) == 2, ut.stdout
    assert funktioner == "SLUT\n", ut.stdout


@inget_zsh
def test_r3_utan_nvm_visas_ocksa_bara_slut(tmp_path):
    assert _zsh(tmp_path, FUNKTIONER_KOMMANDO).stdout == "SLUT\n"


@pytest.mark.parametrize(
    "namn",
    [
        "TRAPDEBUG",
        "TRAPEXIT",
        "TRAPZERR",
        "preexec",
        "precmd",
        "chpwd",
        "periodic",
        "zshexit",
        "zshaddhistory",
        "zsh_directory_name",
        "command_not_found_handler",
        "git",
        "ls",
        "/usr/bin/git",
        "status",
        "nmv",
        "print",
        "alias",
    ],
)
@inget_zsh
def test_r3_en_funktion_som_inte_ar_vantad_visas_fore_slut(tmp_path, namn):
    ut = _zsh(tmp_path, NVM_COMPINIT + VANTADE + f"{namn}() {{ }}\n" + FUNKTIONER_KOMMANDO)
    assert ut.stdout.splitlines() == [namn, "SLUT"], ut.stdout


@inget_zsh
def test_r3_en_funktion_som_heter_builtin_doljer_utskriften_och_syns_pa_att_slut_saknas(tmp_path):
    # Bara en funktion som heter builtin kan dölja utskriften. En som heter print syns (listan ovan).
    ut = _zsh(tmp_path, NVM_COMPINIT + VANTADE + "builtin() { }\n" + FUNKTIONER_KOMMANDO)
    assert ut.stdout == "", ut.stdout


@inget_zsh
def test_r3_med_ett_annat_satt_att_lasa_monster_visas_for_mycket_inte_for_lite(tmp_path):
    # Med SH_GLOB läser zsh inte parentesen som ett mönster. Då visas alla namn: det säkra hållet.
    ut = _zsh(tmp_path, NVM_COMPINIT + VANTADE + "setopt SH_GLOB\n" + FUNKTIONER_KOMMANDO)
    assert len(ut.stdout.splitlines()) > 100, ut.stdout


@pytest.mark.parametrize(
    "rad",
    ["alias -g status=log", "alias ls='ls -G'", "alias /usr/bin/git=true", "alias -g X='| true'"],
)
@inget_zsh
def test_r3_varje_annat_alias_syns_i_alias(tmp_path, rad):
    # Också globala alias visas av alias, utan märkning.
    rader = _zsh(tmp_path, f"{rad}\nalias").stdout.splitlines()
    assert len(rader) == 3 and set(rader) > VANTADE_ALIAS, rader


@inget_zsh
def test_r3_alias_for_filandelser_syns_bara_i_alias_s(tmp_path):
    # alias visar inte alias för filändelser (prövat), därför finns alias -s i kontrollen, med väntat
    # resultat ingenting.
    assert _zsh(tmp_path, "alias -s").stdout == ""
    ut = _zsh(tmp_path, "alias -s txt=cat\nalias\nprint -r -- ---\nalias -s").stdout
    alias_, suffix = ut.split("---\n")
    assert set(alias_.splitlines()) == VANTADE_ALIAS
    assert suffix == "txt=cat\n", ut


@inget_zsh
def test_r3_en_funktion_som_heter_alias_syns_pa_att_raderna_saknas(tmp_path):
    rader = _zsh(tmp_path, "alias() { }\nalias").stdout.splitlines()
    assert set(rader) != VANTADE_ALIAS


# ---------------------------------------------------------------------------------------------
# Hugos svar 2026-10-28 efter granskning 14, punkt 1: kroklistorna är tomma, och de särskilda funktionerna
# finns inte.

KROK_BESLUT = "Hugos svar 2026-10-28 efter granskning 14, punkt 1"


def test_svar_1_kroklistorna_kontrolleras_fore_och_efter_installationen():
    _, rader = _installationskommandon()
    platser = [i for i, r in enumerate(rader) if r == KROK_KOMMANDO]
    assert len(platser) == 2
    assert platser[0] < _forsta_sudo(rader) < platser[1]
    # Kommandot nämner varje kroklista och varje särskild funktion som beslutet räknar upp.
    for namn in KROKLISTOR + ("TRAP*", "preexec", "precmd", "chpwd", "periodic", "zshexit", "command_not_found_handler"):
        assert namn in KROK_KOMMANDO, namn
    fore = _steg_4().split("**g. Kontrollera alias och funktioner**", 1)[1].split("**h. ", 1)[0]
    assert "\n".join(f"  {rad}" for rad in KROK_VANTAT.splitlines()) in fore, "de sju väntade raderna"
    fore = _en_rad(fore)
    assert KROK_BESLUT in fore and "**Stoppa och fråga**" in fore
    assert "det står något mellan parenteserna" in fore and "`SLUT` saknas" in fore
    assert "**Inte bekräftat:**" in fore and "`update_terminal_cwd`" in fore
    efter = _en_rad(_kontrollen().split("**Alias och funktioner, igen efter installationen**", 1)[1].split("\n2. ", 1)[0])
    assert KROK_BESLUT in efter and "sju raderna i steg 4 g" in efter


@inget_zsh
def test_svar_1_med_tomma_kroklistor_och_utan_sarskilda_funktioner_visas_de_sju_raderna(tmp_path):
    for start in ("", NVM_COMPINIT + VANTADE):
        assert _zsh(tmp_path, start + KROK_KOMMANDO).stdout == KROK_VANTAT


@pytest.mark.parametrize("lista", KROKLISTOR)
@inget_zsh
def test_svar_1_en_kroklista_som_inte_ar_tom_syns(tmp_path, lista):
    ut = _zsh(tmp_path, f"{lista}+=(nagot)\n" + KROK_KOMMANDO).stdout
    assert f"{lista}=(nagot)\n" in ut and ut != KROK_VANTAT, ut


@inget_zsh
def test_svar_1_add_zsh_hook_syns_i_kroklistan(tmp_path):
    # Program lägger oftast in sig med add-zsh-hook, som skriver i kroklistan.
    ut = _zsh(tmp_path, "autoload -Uz add-zsh-hook\nadd-zsh-hook preexec nagot\n" + KROK_KOMMANDO).stdout
    assert "preexec_functions=(nagot)\n" in ut, ut


@pytest.mark.parametrize(
    "namn",
    ["preexec", "precmd", "chpwd", "periodic", "zshexit", "command_not_found_handler", "TRAPDEBUG", "TRAPEXIT", "TRAPZERR", "TRAPINT"],
)
@inget_zsh
def test_svar_1_en_sarskild_funktion_syns_fore_slut(tmp_path, namn):
    ut = _zsh(tmp_path, NVM_COMPINIT + VANTADE + f"{namn}() {{ }}\n" + KROK_KOMMANDO).stdout
    assert ut.splitlines()[-2:] == [namn, "SLUT"], ut


@inget_zsh
def test_svar_1_en_funktion_som_heter_builtin_syns_pa_att_raderna_saknas(tmp_path):
    assert _zsh(tmp_path, "builtin() { }\n" + KROK_KOMMANDO).stdout == ""


@inget_zsh
def test_svar_1_en_funktion_som_heter_print_doljer_inget(tmp_path):
    # builtin går förbi funktioner, så en funktion som heter print ändrar inte utskriften. Den syns i
    # stället i kontrollen av funktioner (R3), eftersom den inte står bland de väntade.
    assert _zsh(tmp_path, "print() { }\n" + KROK_KOMMANDO).stdout == KROK_VANTAT
    assert _zsh(tmp_path, "print() { }\n" + FUNKTIONER_KOMMANDO).stdout.splitlines() == ["print", "SLUT"]


# ---------------------------------------------------------------------------------------------
# R4: SPEC 7.1 beskriver vad vakten prövar.


def test_r4_spec_sager_mappen_dar_varje_lank_ligger_och_inte_lanken_sjalv():
    spec = _spec_7_1()
    assert "varje länk i kedjan däremellan, med mappen den ligger i" not in spec
    assert "mappen där varje länk i kedjan däremellan ligger" in spec
    assert "Länkfilen själv prövas inte" in spec and "granskning 14, R4, Hugos beslut 2026-10-28" in spec


# ---------------------------------------------------------------------------------------------
# R5: vad Hugo ska se när ett steg går bra, och steg 4 d utan nvm.


@pytest.mark.parametrize("nummer", [6, 7, 8, 9, 10, 11])
def test_r5_varje_steg_med_sudo_sager_vad_som_syns_nar_det_gar_bra(nummer):
    (steget,) = [_en_rad(t) for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith(f"## Steg {nummer}:")]
    assert "Går det bra visa" in steget, nummer
    assert "ingenting" in steget and "stoppa och fråga" in steget.lower(), nummer


def test_r5_steg_6_forklarar_vad_som_syns_och_nar_hugo_stoppar():
    (steget,) = [_en_rad(t) for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 6:")]
    assert "granskning 14, R5, Hugos beslut 2026-10-28" in steget
    for fel in ("Operation not permitted", "Permission denied", "No such file or directory"):
        assert f"`{fel}`" in steget, fel


def test_r5_allman_regel_att_stoppa_och_fraga_fore_installationen():
    fore = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[1].split("\n## ", 1)[0])
    assert "Visar ett kommando något annat än det som står vid steget: stoppa och fråga" in fore
    assert "granskning 14, R5" in fore


def test_r5_steg_4_d_pa_en_dator_utan_nvm():
    d = _en_rad(_steg_4().split("**d. Kontrollera filen:**", 1)[1].split("**e. ", 1)[0])
    assert "**På en dator utan nvm**" in d and "bara den **sista** raden" in d
    assert "Utan nvm ska bara den sista raden i steg 4 d vara Cryptexes-raden" in _caspers()


def test_r5_casper_behover_claude_code_for_terminal():
    caspers = _caspers()
    assert "Claude Code för Terminal behövs på Caspers dator" in caspers
    assert "**går installationen inte att kontrollera**" in caspers
