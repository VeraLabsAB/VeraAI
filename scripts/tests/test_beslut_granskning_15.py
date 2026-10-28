"""Hugos beslut 2026-10-28 om fynden i granskning 15 (GRANSKNING.md, "Hugos svar 2026-10-28 efter granskning 15").

- S1: find är borttaget ur listan i SPEC 7.1 och ur vakten. grep står kvar, eftersom verktyget Grep inte finns i
  skrivbordsappen, men får bara ha tillägg som söker. rg har aldrig stått på listan.
- S2: förbud för den kompilerade versionen (.zwc) av varje zsh-startfil som redan är förbjuden, och av
  ~/.zcompdump.
- S3: INSTALLERA.md steg 4 h: agenten kör en fast, läsande kontroll i sitt eget skal före installationen.
- S4: godtas. trap, hash och en funktion som heter builtin står i PROGRESS.md under "Öppet", för sandlådan.
- S5: SPEC 7.1 säger hur grep, find och rg hanteras.
- S6: steg 5 och 12 i INSTALLERA.md kontrollerar också requirements.txt.
- 8 d: i Terminal är exakt update_terminal_cwd och shell_session_update godkända i kroklistorna, med ursprung
  och ägare.
- Förenklingen: historiken i INSTALLERA.md är flyttad till GRANSKNING.md, och kontrollerna i steg 4 ligger i
  sparr/kontrollera-skalet.zsh, som bara läser och skriver OK eller vad som avviker, och sist SLUT.
- cd ~/VERA/agent i stället för cd ~/VERA.
- PROGRESS.md: sandlådan direkt efter installationen, stoppregeln och läget Manual.

Proven med zsh körs med zsh -f, med en tillfällig hemmapp och bara systemets mappar i PATH. Inga av Hugos filer
läses. Skriptet körs i en kopia där Terminals fil och /etc-filerna är provfiler i den tillfälliga mappen, och där
provfilernas ägare (den som kör testet) räknas som root. Det som prövas om ägaren görs i en egen kopia där bara
root godtas.
"""

import hashlib
import os
import pwd
import re
import subprocess

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    AGENT_KOMMANDO,
    INSTALLERA,
    KROKLISTOR,
    PROJEKTET,
    SKRIPT_KORNING,
    SKRIPT_SUMMA,
    SPARR,
    _bedom,
    _en_rad,
    _forsta_sudo,
    _installationskommandon,
    _installningar,
    _kontrollen,
    _spec_7_1,
    _steg,
    mappar,
    vakt,
)

ZSH = "/bin/zsh"
inget_zsh = pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")

SKRIPTET = SPARR / "kontrollera-skalet.zsh"
GRANSKNING = PROJEKTET / "GRANSKNING.md"
PROGRESS = PROJEKTET / "PROGRESS.md"

# Raderna i skriptet som byts ut i proven (se docstringen överst).
TERMINALFIL_RAD = "local terminalfil=/etc/zshrc_Apple_Terminal"
ETCFILER_RAD = "local -a etcfiler=(/etc/zshrc /etc/zshrc_Apple_Terminal)"
AGARE_RAD = "local -a agare=(root)"
# macOS sätter uppgiften com.apple.provenance (syns som @ i ls -l) på filer som skapas i testets tillfälliga mapp.
# Skriptet godtar den, och bara den (Hugos beslut 2026-10-28 efter granskning 17, H1), så kopian har kvar
# skriptets egen kontroll. Den prövas i test_beslut_granskning_17.py.

NVM_RADER = (
    'export NVM_DIR="$HOME/.nvm"\n'
    '[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"  # This loads nvm\n'
    '[ -s "$NVM_DIR/bash_completion" ] && \\. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion\n'
)
STEG_4_RADER = (
    '[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )\n'
    "path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )\n"
)
NVM_COMPINIT = "autoload -U +X compinit && compinit\nautoload -U +X bashcompinit && bashcompinit\n"
# Funktioner som Hugos Terminal har utöver compinit: nvm:s och Terminals egna (Terminals två läggs i provfilen).
NVM_FUNKTIONER = "nvm() { }\nnvm_ls() { }\n__nvm() { }\nshell_session_save() { }\n"
TERMINAL_INNEHALL = (
    "update_terminal_cwd() { : }\n"
    "shell_session_update() { : }\n"
    "precmd_functions+=(update_terminal_cwd)\n"
    "zshexit_functions+=(shell_session_update)\n"
)


def _zsh(hem, skript, **extra):
    miljo = {"PATH": "/usr/bin:/bin", "HOME": str(hem), "LANG": "C", **extra}
    return subprocess.run([ZSH, "-f", "-c", skript], capture_output=True, text=True, env=miljo, cwd=hem, timeout=60)


def _anvandaren():
    return pwd.getpwuid(os.getuid()).pw_name


def _kopia(tmp_path, root_bara=False, etcfiler=None):
    """En kopia av skriptet där Terminals fil och /etc-filerna är provfiler, och returnerar (kopia, terminalfil)."""
    terminal = tmp_path / "zshrc_Apple_Terminal"
    terminal.write_text(TERMINAL_INNEHALL, encoding="utf-8")
    etc = tmp_path / "zshrc"
    etc.write_text("# provfil\n", encoding="utf-8")
    text = SKRIPTET.read_text(encoding="utf-8")
    for rad in (TERMINALFIL_RAD, ETCFILER_RAD, AGARE_RAD):
        assert text.count(rad) == 1, rad
    text = text.replace(TERMINALFIL_RAD, f"local terminalfil={terminal}")
    filer = " ".join(str(f) for f in (etcfiler if etcfiler is not None else [etc, terminal]))
    text = text.replace(ETCFILER_RAD, f"local -a etcfiler=({filer})")
    if not root_bara:
        text = text.replace(AGARE_RAD, f"local -a agare=(root {_anvandaren()})")
    kopia = tmp_path / "kontrollera-skalet.zsh"
    kopia.write_text(text, encoding="utf-8")
    return kopia, terminal


def _hem(tmp_path, zshrc=NVM_RADER + STEG_4_RADER):
    hem = tmp_path / "hem"
    hem.mkdir()
    (hem / ".zshrc").write_text(zshrc, encoding="utf-8")
    return hem


def _kor(tmp_path, fore="", efter="", root_bara=False, etcfiler=None, hem=None, compinit=True, **extra):
    kopia, terminal = _kopia(tmp_path, root_bara, etcfiler)
    hem = hem or _hem(tmp_path)
    start = (NVM_COMPINIT if compinit else "") + NVM_FUNKTIONER + f"source {terminal}\n"
    return _zsh(hem, start + fore + f"\nsource {kopia}\n" + efter, **extra)


def _avvikelser(resultat):
    return [r for r in resultat.stdout.splitlines() if r.startswith("AVVIKER: ")]


# ---------------------------------------------------------------------------------------------
# S1: find borttaget, grep bara med tillägg som söker, rg inte på listan.


def test_s1_find_star_inte_pa_listan_i_vakten_eller_spec(vakt):
    assert "find" not in vakt.LASANDE
    assert not hasattr(vakt, "FIND_FORBJUDNA")
    assert "find" not in vakt.TILLATNA_KOMMANDON
    spec = _spec_7_1()
    assert "| `find` |" not in spec
    assert "`find` används bara för att söka" not in spec
    assert "**`find` står inte på listan**" in spec and "granskning 15, S1, Hugos beslut 2026-10-28" in spec


@pytest.mark.parametrize(
    "tillagg", ["-rm", "-delete", "-exec rm '{}' +", "-execdir rm '{}' +", "-ok rm '{}' +", "-okdir rm '{}' +",
                "-fprint x", "-fls x", "-name x", "-type f", "-print"],
)
def test_s1_find_stoppas_med_varje_tillagg(vakt, mappar, tillagg):
    # Hugos beslut: bland annat -rm, -delete, -exec, -execdir, -ok, -okdir, -fprint och -fls ska stoppas. Med
    # find borttaget stoppas alla former, också de som bara söker.
    fel = _bedom(vakt, mappar, f"find . {tillagg}")
    assert fel is not None and "står inte på listan" in fel, fel


@pytest.mark.parametrize("kommando", ["rg x", "rg -n x scripts", "/opt/homebrew/bin/rg x"])
def test_s1_rg_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and "står inte på listan" in fel, fel


def test_s1_grep_har_en_uttrycklig_lista_och_spec_namner_varje_tillagg(vakt):
    spec = _en_rad(_spec_7_1())
    assert "**`grep` får bara söka**" in spec
    for bokstav in vakt.GREP_KORTA + vakt.GREP_KORTA_VARDE:
        assert f"`-{bokstav}`" in spec, bokstav
    for namn in vakt.GREP_LANGA_MONSTER:
        assert f"`--{namn}=`" in spec, namn
    # Inga tillägg som läser filer med mönster, kör program eller skriver filer.
    for bokstav in "fQPzOdD":
        assert bokstav not in vakt.GREP_KORTA + vakt.GREP_KORTA_VARDE, bokstav
    for namn in ("file", "filter", "pager", "view", "config", "save-config", "devices", "directories"):
        assert namn not in vakt.GREP_LANGA + vakt.GREP_LANGA_TAL + vakt.GREP_LANGA_MONSTER, namn


@pytest.mark.parametrize(
    "tillagg",
    ["--filter=sh", "--pager", "--view", "--config", "--save-config", "---", "-f x", "--file=x", "-Q", "-P",
     "-z", "-U", "-%", "-+", "--index", "--color=always", "--hyperlink", "--format=x", "--replace=x",
     "--tree", "--no-ignore-files", "--ignore-files=x", "--label=x", "-O x", "-d skip", "-D skip"],
)
def test_s1_grep_med_ett_annat_tillagg_stoppas(vakt, mappar, tillagg):
    fel = _bedom(vakt, mappar, f"grep {tillagg} x SPEC.md")
    assert fel is not None and "grep får bara söka" in fel, fel


def test_s1_skalet_for_att_grep_star_kvar_star_i_spec():
    # Verktyget Grep finns inte i skrivbordsappen. Det sågs i byggsessionen 2026-10-28.
    spec = _en_rad(_spec_7_1())
    assert "verktyget Grep inte finns i skrivbordsappen" in spec
    assert "`ls -R scripts`" in spec


# ---------------------------------------------------------------------------------------------
# S2: kompilerade startfiler.

S2_FORBUD = [
    "Edit(~/.zshrc.zwc)",
    "Edit(~/.zshenv.zwc)",
    "Edit(~/.zprofile.zwc)",
    "Edit(~/.zlogin.zwc)",
    "Edit(~/.zlogout.zwc)",
    "Edit(//etc/zshenv.zwc)",
    "Edit(//etc/zprofile.zwc)",
    "Edit(//etc/zshrc.zwc)",
    "Edit(//etc/zlogin.zwc)",
    "Edit(//etc/zlogout.zwc)",
    "Edit(~/.zcompdump.zwc)",
]


@pytest.mark.parametrize("regel", S2_FORBUD)
def test_s2_den_kompilerade_versionen_av_varje_forbjuden_startfil_har_ett_forbud(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_s2_varje_forbjuden_startfil_har_ett_forbud_for_sin_zwc():
    # Varje zsh-startfil med ett eget förbud (utan * eller **) har också ett för sin .zwc. //etc/zshrc_* täcker
    # redan sin .zwc.
    neka = _installningar()["permissions"]["deny"]
    startfiler = [r for r in neka if re.fullmatch(r"Edit\((~/\.z[a-z]+|//etc/z[a-z]+)\)", r)]
    assert len(startfiler) >= 11, startfiler
    for regel in startfiler:
        assert regel[:-1] + ".zwc)" in neka, regel


def test_s2_installera_namner_forbudet():
    vad = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[0])
    assert "`.zwc`" in vad and "granskning 15, S2" in vad


# ---------------------------------------------------------------------------------------------
# S3: agentens eget skal, steg 4 h.

CLAUDE_CODES_FUNKTIONER = ("find", "grep", "pkill", "rg")
AGENT_VANTAT = "".join(f"{lista}=()\n" for lista in KROKLISTOR) + "".join(
    f"{namn}\n" for namn in CLAUDE_CODES_FUNKTIONER
) + "SLUT\n"
# Som Claude Codes fil i ~/.claude/shell-snapshots: fyra funktioner (granskning 15, typeset -f i agentens skal).
CLAUDE_CODES_SKAL = "".join(f"{namn}() {{ : }}\n" for namn in CLAUDE_CODES_FUNKTIONER)


def _steg_4_h():
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    return steget.split("**h. Kontrollera agentens eget skal", 1)[1].split("Ångra steget:", 1)[0]


def test_s3_steget_finns_fore_installationen_med_kommandot_och_det_vantade():
    _, rader = _installationskommandon()
    assert rader.count(AGENT_KOMMANDO) == 1
    assert rader.index(AGENT_KOMMANDO) < _forsta_sudo(rader)
    steget = _steg_4_h()
    assert "\n".join(f"   {rad}" for rad in AGENT_VANTAT.splitlines()) in steget, "de elva väntade raderna"
    en_rad = _en_rad(steget)
    assert "Hugos beslut 2026-10-28 efter granskning 15, S3" in en_rad
    assert "**verktygsrutan**" in en_rad and "inte agentens sammanfattning" in en_rad
    assert "**Manual**" in en_rad and "**före** installationen" in en_rad
    assert "**Stoppa och fråga**" in en_rad and "`SLUT` saknas" in en_rad and "**Inte bekräftat:**" in en_rad


@inget_zsh
def test_s3_i_ett_skal_som_agentens_visas_de_elva_raderna(tmp_path):
    ut = _zsh(tmp_path, NVM_COMPINIT + NVM_FUNKTIONER + CLAUDE_CODES_SKAL + AGENT_KOMMANDO)
    assert ut.stdout == AGENT_VANTAT, ut


@pytest.mark.parametrize("namn", ["git", "TRAPDEBUG", "preexec", "command_not_found_handler", "pkillx", "print"])
@inget_zsh
def test_s3_en_annan_funktion_syns(tmp_path, namn):
    ut = _zsh(tmp_path, NVM_COMPINIT + CLAUDE_CODES_SKAL + f"{namn}() {{ }}\n" + AGENT_KOMMANDO).stdout
    assert namn in ut.splitlines() and ut != AGENT_VANTAT, ut


@pytest.mark.parametrize("lista", KROKLISTOR)
@inget_zsh
def test_s3_en_kroklista_som_inte_ar_tom_syns(tmp_path, lista):
    ut = _zsh(tmp_path, CLAUDE_CODES_SKAL + f"{lista}+=(_nagot)\n" + AGENT_KOMMANDO).stdout
    assert f"{lista}=(_nagot)\n" in ut and ut != AGENT_VANTAT, ut


@inget_zsh
def test_s3_saknas_en_av_claude_codes_funktioner_syns_det(tmp_path):
    ut = _zsh(tmp_path, "find() { }\ngrep() { }\nrg() { }\n" + AGENT_KOMMANDO).stdout
    assert ut != AGENT_VANTAT and "pkill" not in ut


@inget_zsh
def test_s3_en_funktion_som_heter_builtin_syns_pa_att_slut_saknas(tmp_path):
    assert _zsh(tmp_path, CLAUDE_CODES_SKAL + "builtin() { }\n" + AGENT_KOMMANDO).stdout == ""


# ---------------------------------------------------------------------------------------------
# S4 och PROGRESS.md.


def _oppet():
    return _en_rad(PROGRESS.read_text(encoding="utf-8").split("## Öppet", 1)[1].split("\n## ", 1)[0])


def test_s4_trap_hash_och_builtin_star_under_oppet_for_sandladan():
    oppet = _oppet()
    assert "granskning 15, S4" in oppet and "Hugos beslut 2026-10-28" in oppet
    for ord_ in ("`trap`", "`hash`", "`builtin`", "sandlådan"):
        assert ord_ in oppet, ord_


def test_progress_sandladan_stoppregeln_och_manual():
    text = _en_rad(PROGRESS.read_text(encoding="utf-8"))
    assert "Sandlådan görs direkt efter installationen" in text
    assert "**Stoppregel:**" in text and "Låga fynd går till \"Öppet\"" in text
    assert "läget **Manual** tills vakten är installerad" in text
    assert "Granskning 15 kördes av misstag i läget auto" in text


# ---------------------------------------------------------------------------------------------
# S5: SPEC 7.1.


def test_s5_spec_sager_att_skalet_kor_claude_codes_program_for_grep():
    spec = _en_rad(_spec_7_1())
    assert "**För `grep` kör skalet ett annat program än det vakten prövar**" in spec
    assert "granskning 15, S5, Hugos beslut 2026-10-28" in spec
    assert "`ugrep`" in spec and "`bfs`" in spec and "**`rg` står inte heller på listan.**" in spec
    assert "`grep -f`/`--file` stoppas" not in spec


# ---------------------------------------------------------------------------------------------
# S6: requirements.txt i steg 5 och 12.


@pytest.mark.parametrize("nummer", [5, 12])
def test_s6_steg_5_och_12_kontrollerar_requirements(nummer):
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith(f"## Steg {nummer}:")]
    (rad,) = [r for r in steget.splitlines() if r.startswith("shasum -a 256 ")]
    assert rad.endswith(" ~/VERA/agent/requirements.txt"), rad
    assert "granskning" in _en_rad(steget) and "S6" in _en_rad(steget)


# ---------------------------------------------------------------------------------------------
# Skriptet: kontrollsumman, var det körs, och att det bara läser.


def test_skriptets_kontrollsumma_star_i_installera():
    summa = hashlib.sha256(SKRIPTET.read_bytes()).hexdigest()
    text = INSTALLERA.read_text(encoding="utf-8")
    assert f"`{summa}`" in text, f"kontrollsumman i INSTALLERA.md ska vara {summa}"


def test_skriptet_kors_fore_och_efter_installationen_med_kontrollsumman_forst():
    _, rader = _installationskommandon()
    korningar = [i for i, r in enumerate(rader) if r == SKRIPT_KORNING]
    summor = [i for i, r in enumerate(rader) if r == SKRIPT_SUMMA]
    assert len(korningar) == 2 and len(summor) == 2
    sista_chmod = max(i for i, r in enumerate(rader) if r.startswith("sudo chmod"))
    assert summor[0] + 1 == korningar[0] < _forsta_sudo(rader)
    assert sista_chmod < summor[1] and summor[1] + 1 == korningar[1]
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    g = _en_rad(steget.split("**g. Kontrollera skalet i Terminal med kontrollskriptet**", 1)[1].split("**h. ", 1)[0])
    assert "**Väntat: exakt två rader**, `OK` och sedan `SLUT`" in g
    assert "`AVVIKER`: stoppa och fråga" in g and "**Saknas `SLUT`" in g
    assert "**Är summan en annan: stoppa och fråga.**" in g
    efter = _en_rad(_kontrollen().split("\n2. ", 1)[0])
    assert "`AVVIKER`" in efter and "stoppa och fråga" in efter


def test_skriptet_skriver_inga_filer_och_kor_bara_lasande_program():
    kod = [r.split("#", 1)[0] for r in SKRIPTET.read_text(encoding="utf-8").splitlines()]
    kod = "\n".join(r for r in kod if r.strip())
    # Den enda omdirigeringen är att fel från ls inte visas.
    assert re.findall(r"\d?>+\S*", kod.replace("2>/dev/null", "")) == []
    for ord_ in ("rm ", "mv ", "cp ", "touch ", "mkdir ", "chmod ", "chown ", "eval ", "zcompile", "export "):
        assert ord_ not in kod, ord_
    assert re.findall(r"/(?:usr/)?bin/\w+", kod) == ["/bin/ls", "/usr/bin/grep"]


@inget_zsh
def test_skriptet_skriver_ok_och_slut_nar_allt_ar_vantat(tmp_path):
    resultat = _kor(tmp_path)
    assert resultat.stdout == "OK\nSLUT\n", resultat


@inget_zsh
def test_skriptet_skriver_ok_ocksa_utan_compinit(tmp_path):
    assert _kor(tmp_path, compinit=False).stdout == "OK\nSLUT\n"


@inget_zsh
def test_skriptet_lamnar_inget_efter_sig(tmp_path):
    # Samma inställningar och samma funktioner före och efter, och inga variabler kvar.
    visa = "builtin print -r -- ${(kv)options} ${(ok)functions}"
    variabler = "builtin print -r -- ${+avvikelser} ${+terminalfil} ${+etcfiler} ${+agare} ${+rad} ${+namn}"
    resultat = _kor(tmp_path, fore=visa, efter=visa + "\n" + variabler)
    rader = resultat.stdout.splitlines()
    assert rader[1:3] == ["OK", "SLUT"], resultat
    assert rader[0] == rader[3]
    assert rader[4] == "0 0 0 0 0 0"


@pytest.mark.parametrize("installning", ["KSH_ARRAYS", "NO_EXTENDED_GLOB", "EXTENDED_GLOB", "RC_EXPAND_PARAM"])
@inget_zsh
def test_skriptet_fungerar_med_andra_installningar_i_skalet(tmp_path, installning):
    # emulate -L zsh: skalets egna inställningar ändrar inte kontrollen när den körs.
    assert _kor(tmp_path, fore=f"setopt {installning}").stdout == "OK\nSLUT\n"


@pytest.mark.parametrize("installning", ["SH_GLOB", "KSH_GLOB SH_GLOB"])
@inget_zsh
def test_skriptet_med_sh_glob_skriver_inte_ok_och_inte_slut(tmp_path, installning):
    # Med SH_GLOB kan zsh inte läsa skriptet. Då saknas SLUT, och Hugo stoppar: det säkra hållet.
    resultat = _kor(tmp_path, fore=f"setopt {installning}")
    assert "OK" not in resultat.stdout and "SLUT" not in resultat.stdout, resultat
    assert resultat.stderr, resultat


# Alias.


@pytest.mark.parametrize(
    "rad,vantat",
    [
        ("alias -g status=log", "AVVIKER: globalt alias: status=log"),
        ("alias ls='ls -G'", "AVVIKER: alias: ls=ls -G"),
        ("alias /usr/bin/git=true", "AVVIKER: alias: /usr/bin/git=true"),
        ("alias -s txt=cat", "AVVIKER: alias för filändelse: txt=cat"),
        ("unalias run-help", "AVVIKER: alias saknas: run-help"),
        ("alias run-help=less", "AVVIKER: alias: run-help=less"),
    ],
)
@inget_zsh
def test_skriptet_visar_varje_annat_alias(tmp_path, rad, vantat):
    resultat = _kor(tmp_path, fore=rad)
    assert _avvikelser(resultat) == [vantat], resultat
    assert resultat.stdout.endswith("SLUT\n") and "OK\n" not in resultat.stdout


# Funktioner.


@pytest.mark.parametrize(
    "namn",
    ["TRAPDEBUG", "TRAPEXIT", "preexec", "precmd", "chpwd", "periodic", "zshexit", "zshaddhistory",
     "zsh_directory_name", "command_not_found_handler", "git", "ls", "grep", "find", "/usr/bin/git", "status",
     "print", "alias", "whence", "emulate"],
)
@inget_zsh
def test_skriptet_visar_varje_funktion_som_inte_ar_vantad(tmp_path, namn):
    resultat = _kor(tmp_path, fore=f"function {namn} {{ }}")
    assert f"AVVIKER: funktion: {namn}" in _avvikelser(resultat), resultat
    assert resultat.stdout.endswith("SLUT\n")


@inget_zsh
def test_skriptet_en_funktion_som_heter_builtin_syns_pa_att_slut_saknas(tmp_path):
    resultat = _kor(tmp_path, fore="builtin() { }")
    assert "SLUT" not in resultat.stdout and "OK" not in resultat.stdout, resultat


# Kroklistor och Terminals funktioner (8 d).


@pytest.mark.parametrize("lista", KROKLISTOR)
@inget_zsh
def test_8d_en_annan_funktion_i_en_kroklista_avviker(tmp_path, lista):
    # Också ett namn som börjar med _, som filtret för funktioner godtar.
    resultat = _kor(tmp_path, fore=f"_vera_ond() {{ }}\n{lista}+=(_vera_ond)")
    (rad,) = _avvikelser(resultat)
    assert rad.startswith(f"AVVIKER: {lista}=(") and "_vera_ond)" in rad, resultat


@inget_zsh
def test_8d_tomma_kroklistor_avviker_i_terminal(tmp_path):
    # Hugos beslut: exakt de två namnen i Terminal. Allt annat stoppar, också tomma listor.
    resultat = _kor(tmp_path, fore="precmd_functions=()\nzshexit_functions=()")
    assert _avvikelser(resultat) == ["AVVIKER: precmd_functions=()", "AVVIKER: zshexit_functions=()"], resultat


@inget_zsh
def test_8d_add_zsh_hook_syns(tmp_path):
    resultat = _kor(tmp_path, fore="autoload -Uz add-zsh-hook\nadd-zsh-hook preexec _nagot")
    assert "AVVIKER: preexec_functions=(_nagot)" in _avvikelser(resultat), resultat


@pytest.mark.parametrize("namn", ["update_terminal_cwd", "shell_session_update"])
@inget_zsh
def test_8d_en_terminalfunktion_fran_en_annan_fil_avviker(tmp_path, namn):
    annan = tmp_path / "annan.zsh"
    annan.write_text(f"{namn}() {{ echo ond }}\n", encoding="utf-8")
    resultat = _kor(tmp_path, fore=f"source {annan}")
    assert _avvikelser(resultat) == [f"AVVIKER: whence -v: {namn} is a shell function from {annan}"], resultat


@inget_zsh
def test_8d_en_terminalfunktion_som_saknas_avviker(tmp_path):
    resultat = _kor(tmp_path, fore="unfunction shell_session_update")
    assert "AVVIKER: whence -v: shell_session_update not found" in _avvikelser(resultat), resultat


@inget_zsh
def test_8d_etcfiler_som_inte_ags_av_root_avviker(tmp_path):
    resultat = _kor(tmp_path, root_bara=True)
    rader = _avvikelser(resultat)
    assert len(rader) == 2 and all(r.startswith("AVVIKER: ls -l: ") and "ägs inte av root" in r for r in rader), resultat


@pytest.mark.parametrize("rattigheter", [0o664, 0o646, 0o666])
@inget_zsh
def test_8d_etcfiler_som_gruppen_eller_andra_kan_skriva_i_avviker(tmp_path, rattigheter):
    fil = tmp_path / "skrivbar"
    fil.write_text("x\n", encoding="utf-8")
    os.chmod(fil, rattigheter)
    resultat = _kor(tmp_path, etcfiler=[fil])
    (rad,) = _avvikelser(resultat)
    assert "gruppen eller andra kan skriva i" in rad, resultat


@inget_zsh
def test_skriptet_stoppar_for_extra_uppgifter(tmp_path):
    # Det riktiga skriptet godtar inget + och ingen annan uppgift än exakt com.apple.provenance (granskning 17, H1).
    # Fler fall står i test_beslut_granskning_17.py.
    fil = tmp_path / "med_uppgifter"
    fil.write_text("x\n", encoding="utf-8")
    subprocess.run(["/usr/bin/xattr", "-w", "com.apple.quarantine", "prov", str(fil)], check=True, timeout=30)
    resultat = _kor(tmp_path, etcfiler=[fil])
    (rad,) = _avvikelser(resultat)
    assert "extra rättigheter eller uppgifter (+ eller @)" in rad, resultat


@inget_zsh
def test_8d_en_etcfil_som_ar_en_lank_eller_saknas_avviker(tmp_path):
    lank = tmp_path / "lank"
    lank.symlink_to(tmp_path / "hem")
    resultat = _kor(tmp_path, etcfiler=[lank, tmp_path / "finns-inte"])
    rader = _avvikelser(resultat)
    assert any("är en länk" in r for r in rader) and any("finns inte" in r for r in rader), resultat


def test_8d_installera_namner_namnen_ursprunget_och_agaren():
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    g = _en_rad(steget.split("**g. ", 1)[1].split("**h. ", 1)[0])
    assert "Hugos beslut 2026-10-28 efter granskning 15, 8 d" in g
    assert "`update_terminal_cwd` i `precmd_functions`" in g and "`shell_session_update` i `zshexit_functions`" in g
    assert "`whence -v`" in g and "`/etc/zshrc_Apple_Terminal`" in g and "`ls -l`" in g and "`root`" in g
    assert "Allt annat avviker." in g
    text = SKRIPTET.read_text(encoding="utf-8")
    assert "precmd_functions} == update_terminal_cwd ]]" in text
    assert "zshexit_functions} == shell_session_update ]]" in text


# fpath och startfiler.


@inget_zsh
def test_skriptet_visar_en_annan_mapp_i_fpath(tmp_path):
    egen = tmp_path / "funktioner"
    egen.mkdir()
    resultat = _kor(tmp_path, fore=f"fpath=({egen} $fpath)")
    assert f"AVVIKER: fpath: {egen}" in _avvikelser(resultat), resultat


@pytest.mark.parametrize(
    "fil,rad",
    [
        (".zshrc", 'source "$ZSH/oh-my-zsh.sh"'),
        (".zprofile", 'eval "$(/opt/homebrew/bin/brew shellenv)"'),
        (".zshrc", 'eval "$(conda shell.zsh hook)"'),
        (".zshrc", ". ~/.annan_fil"),
        (".zshenv", "autoload -Uz compinit && compinit"),
        (".zlogin", "fpath=(~/.zfunc $fpath)"),
        (".zshenv", 'export ZDOTDIR="$HOME/.config/zsh"'),
        (".zshrc", '[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/annan.sh"  # This loads nvm'),
    ],
)
@inget_zsh
def test_skriptet_visar_andra_rader_som_laser_in_filer(tmp_path, fil, rad):
    hem = _hem(tmp_path)
    with open(hem / fil, "a", encoding="utf-8") as ut:
        ut.write(rad + "\n")
    resultat = _kor(tmp_path, hem=hem)
    (avvikelse,) = _avvikelser(resultat)
    assert avvikelse.startswith(f"AVVIKER: startfil: {hem / fil}:") and avvikelse.endswith(rad), resultat


@inget_zsh
def test_skriptet_godtar_nvm_raderna_med_en_annan_kommentar_och_utan_nvm(tmp_path):
    andrad = NVM_RADER.replace("# This loads nvm bash_completion", "# annan text")
    assert _kor(tmp_path, hem=_hem(tmp_path, andrad + STEG_4_RADER)).stdout == "OK\nSLUT\n"
    utan = tmp_path / "utan"
    utan.mkdir()
    assert _kor(utan, hem=_hem(utan, STEG_4_RADER), compinit=False).stdout == "OK\nSLUT\n"


@pytest.mark.parametrize("namn", [".zshrc.zwc", ".zshenv.zwc", ".zprofile.zwc", ".zlogin.zwc", ".zlogout.zwc"])
@inget_zsh
def test_skriptet_visar_en_kompilerad_startfil(tmp_path, namn):
    hem = _hem(tmp_path)
    (hem / namn).write_bytes(b"\x00prov")
    resultat = _kor(tmp_path, hem=hem)
    assert _avvikelser(resultat) == [f"AVVIKER: kompilerad startfil: {hem / namn}"], resultat


@inget_zsh
def test_skriptet_visar_zdotdir(tmp_path):
    resultat = _kor(tmp_path, ZDOTDIR=str(tmp_path))
    assert f"AVVIKER: ZDOTDIR={tmp_path}" in _avvikelser(resultat), resultat


# ---------------------------------------------------------------------------------------------
# cd ~/VERA/agent, historiken och att INSTALLERA.md är kortare.


@pytest.mark.parametrize("fil", ["sparr/INSTALLERA.md", "SPEC.md"])
def test_cd_till_projektmappen_ar_vera_agent(fil):
    text = (PROJEKTET / fil).read_text(encoding="utf-8")
    assert re.findall(r"cd ~/VERA(?!/agent\b)", text) == [], fil


def test_installera_sager_cd_vera_agent_fore_claude_i_terminal():
    _, rader = _installationskommandon()
    assert "cd ~/VERA" not in rader
    assert rader.index("cd ~/VERA/agent") + 1 == rader.index("~/.local/bin/claude")


def test_historiken_ar_flyttad_till_granskning():
    borjan = INSTALLERA.read_text(encoding="utf-8").split("## Vad som installeras", 1)[0]
    assert "Ändrad igen samma dag" not in borjan and "Skriven 2026-10-28 i byggsessionen" not in borjan
    assert "Historiken i INSTALLERA.md" in borjan
    granskning = GRANSKNING.read_text(encoding="utf-8")
    historiken = granskning.split("#### Historiken i INSTALLERA.md", 1)[1]
    assert "Skriven 2026-10-28 i byggsessionen för granskning 11, Q1" in historiken
    assert "(R3, steg 4 g), och vad du ska se när ett steg går bra" in historiken


def test_installera_ar_kortare_an_fore_granskning_15():
    # Före: 989 rader, 9 043 ord, 51 kommandorutor och 16 sudo-kommandon (räknat 2026-10-28 i byggsessionen).
    text = INSTALLERA.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 989
    assert len(text.split()) < 9043
    assert len(re.findall(r"^ *```bash", text, flags=re.M)) < 51
    assert len(re.findall(r"^ *sudo ", text, flags=re.M)) == 16


def test_besluten_star_i_granskning():
    granskning = _en_rad(GRANSKNING.read_text(encoding="utf-8").split("### Hugos svar 2026-10-28 efter granskning 15", 1)[1])
    for nyckel in ("S1", "S2", "S3", "S4", "S5", "S6", "8 d", "Förenklingen", "`cd ~/VERA/agent`"):
        assert f"**{nyckel}" in granskning, nyckel
