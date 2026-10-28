"""Granskning 15 (oberoende granskning 2026-10-28): den vända kontrollen i steg 4 g, fler filer som zsh läser
vid start, och skalet som agenten faktiskt kör i (GRANSKNING.md, "Granskning 15").

Proven med zsh körs med zsh -f (eller zsh -d, som inte läser systemets filer i /etc utom /etc/zshenv), med
en tillfällig hemmapp och bara systemets mappar i PATH. Inga av Hugos filer läses. Kommandona i steg 4 g
hämtas från test_kommandosparr.py, som hämtar dem ur INSTALLERA.md.

Tester som visar en lucka som inte är rättad är markerade xfail(strict=True): de är väntat röda i dag. När
luckan rättas blir de gröna, och då stoppar pytest testsviten tills markeringen tas bort.
"""

import os
import subprocess

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    FUNKTIONER_KOMMANDO,
    KROK_KOMMANDO,
    KROK_VANTAT,
    _bedom,
    _installningar,
    mappar,
    vakt,
)

ZSH = "/bin/zsh"
inget_zsh = pytest.mark.skipif(not os.path.isfile(ZSH), reason="zsh finns inte på den här datorn")
ALIAS_VANTAT = {"run-help=man", "which-command=whence"}


def _miljo(tmp_path, **extra):
    return {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "LANG": "C", **extra}


def _zsh(tmp_path, skript, flagga="-f", **extra):
    return subprocess.run(
        [ZSH, flagga, "-c", skript],
        capture_output=True,
        text=True,
        env=_miljo(tmp_path, **extra),
        cwd=tmp_path,
        timeout=30,
    )


def _kontrollen_ser_ren_ut(tmp_path, forberedelse):
    """Kör kontrollerna i steg 4 g efter forberedelse, en i taget i samma skal, och returnerar utskrifterna."""
    avdelare = "-----GRANSKNING15-----"
    skript = forberedelse + "\n" + f"\nprint -r -- '{avdelare}'\n".join(
        ["alias", "alias -s", FUNKTIONER_KOMMANDO, KROK_KOMMANDO]
    )
    resultat = _zsh(tmp_path, skript)
    delar = resultat.stdout.split(avdelare + "\n")
    assert len(delar) == 4, resultat
    return delar


def _ren(delar):
    alias_, alias_s, funktioner, krokar = delar
    return (
        set(alias_.splitlines()) == ALIAS_VANTAT
        and alias_s == ""
        and funktioner == "SLUT\n"
        and krokar == KROK_VANTAT
    )


# ---------------------------------------------------------------------------------------------
# Punkt 2: kan något farligt ta sig igenom den vända kontrollen?


@inget_zsh
def test_forutsattning_kontrollen_ar_ren_i_ett_tomt_skal(tmp_path):
    assert _ren(_kontrollen_ser_ren_ut(tmp_path, ":"))


@inget_zsh
def test_en_funktion_med_ett_vantat_namn_i_en_kroklista_syns(tmp_path):
    # Namnet börjar med _ och döljs därför av filtret för funktioner, men kroklistan visar det.
    delar = _kontrollen_ser_ren_ut(tmp_path, "_vera_ond() { : }\nprecmd_functions+=(_vera_ond)")
    assert "precmd_functions=(_vera_ond)\n" in delar[3]
    assert not _ren(delar)


@inget_zsh
def test_en_falla_satt_med_trap_kors_fore_varje_kommando_men_syns_inte_i_kontrollen(tmp_path):
    # trap '…' DEBUG skapar ingen funktion som heter TRAPDEBUG, så filtret och kroklistorna visar ingenting.
    # Fällan körs ändå före varje kommando, också i ett skal som inte är interaktivt.
    spar = tmp_path / "spar"
    delar = _kontrollen_ser_ren_ut(tmp_path, f"trap 'print -r -- KORD >> {spar}' DEBUG")
    assert _ren(delar), delar
    assert spar.read_text().count("KORD") >= 4


@inget_zsh
def test_trap_utan_argument_visar_fallan(tmp_path):
    # Förslaget i granskning 15: kommandot trap (utan något efter) visar fällorna. Väntat: ingenting.
    resultat = _zsh(tmp_path, "trap 'print -r -- KORD' DEBUG\ntrap")
    assert "DEBUG" in resultat.stdout
    assert _zsh(tmp_path, "trap").stdout == ""


@inget_zsh
def test_ett_namn_i_skalets_tabell_over_program_byter_program_men_syns_inte_i_kontrollen(tmp_path):
    # hash git=… gör att git kör en annan fil, oavsett PATH. Det är varken ett alias eller en funktion.
    ond = tmp_path / "ond"
    ond.mkdir()
    (ond / "git").write_text("#!/bin/sh\necho ONDGIT\n")
    os.chmod(ond / "git", 0o755)
    forberedelse = f"hash git={ond / 'git'}"
    assert _ren(_kontrollen_ser_ren_ut(tmp_path, forberedelse))
    assert _zsh(tmp_path, forberedelse + "\ngit status").stdout == "ONDGIT\n"
    # Förslaget i granskning 15: whence -v visar vad varje namn på listan faktiskt kör.
    assert str(ond / "git") in _zsh(tmp_path, forberedelse + "\nwhence -v git").stdout


@inget_zsh
def test_en_funktion_som_heter_builtin_kan_harma_kontrollen_och_skriva_slut(tmp_path):
    # INSTALLERA.md steg 4 g: "Saknas SLUT … har något dolt utskriften, till exempel en funktion som heter
    # builtin". Det gäller en funktion som döljer. En funktion som härmar skriver de väntade raderna själv.
    vantat = KROK_VANTAT.replace("\n", "\\n")
    forberedelse = (
        "TRAPDEBUG() { : }\n"
        "builtin() {\n"
        f"  if [[ $* == *preexec_functions* ]]; then printf '{vantat}'; else printf 'SLUT\\n'; fi\n"
        "}"
    )
    delar = _kontrollen_ser_ren_ut(tmp_path, forberedelse)
    assert _ren(delar), delar


@inget_zsh
def test_functions_source_visar_filen_dar_en_funktion_skrevs(tmp_path):
    # Underlag för förslaget om Terminals två namn: zsh 5.9 visar i functions_source vilken fil som
    # skrev en funktion sist.
    fil = tmp_path / "defs.zsh"
    fil.write_text("update_terminal_cwd() { : }\n")
    resultat = _zsh(tmp_path, f"source {fil}\nprint -r -- ${{functions_source[update_terminal_cwd]}}")
    assert resultat.stdout == f"{fil}\n"
    # Skrivs funktionen om senare, i en annan fil, visar functions_source den filen.
    annan = tmp_path / "annan.zsh"
    annan.write_text("update_terminal_cwd() { echo ond }\n")
    resultat = _zsh(
        tmp_path, f"source {fil}\nsource {annan}\nprint -r -- ${{functions_source[update_terminal_cwd]}}"
    )
    assert resultat.stdout == f"{annan}\n"
    # whence -v säger samma sak i klartext, som Hugo kan läsa i Terminal.
    resultat = _zsh(tmp_path, f"source {fil}\nwhence -v update_terminal_cwd")
    assert resultat.stdout == f"update_terminal_cwd is a shell function from {fil}\n"


# ---------------------------------------------------------------------------------------------
# Punkt 3: kompilerade startfiler (.zwc).


def _kompilera(tmp_path, namn, innehall):
    """Kompilerar en fil som heter namn (i en egen mapp) med zcompile och returnerar .zwc-filen."""
    kalla = tmp_path / "kalla"
    kalla.mkdir(exist_ok=True)
    (kalla / namn).write_text(innehall)
    resultat = _zsh(tmp_path, f"zcompile {kalla / namn}")
    assert resultat.returncode == 0, resultat
    return kalla / f"{namn}.zwc"


@inget_zsh
def test_en_kompilerad_zshrc_zwc_laser_in_i_stallet_for_zshrc(tmp_path):
    # zsh-manualen, "Startup/Shutdown Files": en kompilerad fil med .zwc sist, som är nyare än filen, används
    # i stället. Här med source, som Claude Code använder för ~/.zshrc.
    zwc = _kompilera(tmp_path, ".zshrc", "alias git=true\n")
    (tmp_path / ".zshrc").write_text("# vanlig fil utan alias\n")
    os.utime(tmp_path / ".zshrc", (946684800, 946684800))
    (tmp_path / ".zshrc.zwc").write_bytes(zwc.read_bytes())
    resultat = _zsh(tmp_path, f"source {tmp_path / '.zshrc'}\nalias")
    assert "git=true" in resultat.stdout.splitlines()


@inget_zsh
def test_en_kompilerad_zshenv_zwc_laser_in_vid_start(tmp_path):
    # Samma sak när zsh startar och läser $ZDOTDIR/.zshenv själv (zsh -d läser inte /etc/zprofile,
    # /etc/zshrc eller /etc/zlogin).
    zwc = _kompilera(tmp_path, ".zshenv", "alias git=true\n")
    hem = tmp_path / "hem"
    hem.mkdir()
    (hem / ".zshenv").write_text("# vanlig fil utan alias\n")
    os.utime(hem / ".zshenv", (946684800, 946684800))
    (hem / ".zshenv.zwc").write_bytes(zwc.read_bytes())
    resultat = subprocess.run(
        [ZSH, "-d", "-c", "alias"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(hem), "ZDOTDIR": str(hem), "LANG": "C"},
        cwd=hem,
        timeout=30,
    )
    assert "git=true" in resultat.stdout.splitlines(), resultat


def _nekas(regel_sokvag):
    """Sant om någon Edit-regel i den låsta filen gäller sökvägen ~/<namn> (ett namn, utan /)."""
    import fnmatch

    for regel in _installningar()["permissions"]["deny"]:
        if regel.startswith("Edit(~/") and regel.endswith(")"):
            monster = regel[len("Edit(~/") : -1]
            if "/" not in monster and fnmatch.fnmatchcase(regel_sokvag, monster):
                return True
    return False


@pytest.mark.parametrize("namn", [".zshrc.zwc", ".zshenv.zwc", ".zprofile.zwc", ".zlogin.zwc", ".zlogout.zwc"])
def test_kompilerade_startfiler_har_ett_forbud(namn):
    assert _nekas(namn), namn


@pytest.mark.parametrize("namn", [".zcompdump", ".zcompdump.zwc", ".zcompdump-dator-5.9"])
def test_zcompdump_och_dess_kompilerade_fil_har_ett_forbud(namn):
    assert _nekas(namn), namn


# ---------------------------------------------------------------------------------------------
# Skalet som agenten kör i: find är Claude Codes inbyggda bfs, som har -rm.


@pytest.mark.parametrize("kommando", ["find <P> -name prov.txt -rm", "find <P> -rm"])
def test_find_med_rm_stoppas(vakt, mappar, kommando):
    # I agentens skal är find en funktion som Claude Code lägger in, och den kör bfs (tools-reference,
    # "Glob tool behavior"). bfs raderar med -rm, som -delete. Vakten känner bara till -delete.
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None, "vakten släpper igenom find -rm"


def test_systemets_find_godtar_inte_rm(tmp_path):
    # Vaktens regler för find bygger på systemets find, där -rm inte finns. Filen finns kvar.
    fil = tmp_path / "prov.txt"
    fil.write_text("prov\n")
    resultat = subprocess.run(
        ["/usr/bin/find", str(tmp_path), "-name", "prov.txt", "-rm"], capture_output=True, text=True, timeout=30
    )
    assert resultat.returncode != 0
    assert fil.exists()
