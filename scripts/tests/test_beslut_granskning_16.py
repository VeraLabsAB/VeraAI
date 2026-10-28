"""Hugos beslut 2026-10-28 efter granskning 16 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 16)").

- G3: -R är borttaget ur grep-tilläggen i vakten och i SPEC 7.1. ugrep -R följer alla länkar inne i mappar, också
  länkar som leder ut ur projektet. -r står kvar.
- G7: agenten får inte skapa eller ändra en fil som heter .ugrep (ugreps inställningsfil, som kan köra andra
  program), i någon mapp. Vakten stoppar kommandon som skulle skriva en sådan fil, och de låsta inställningarna
  förbjuder fil-verktygen att skriva den.
- G2: INSTALLERA.md steg 4 h säger att allt som inte är exakt de elva raderna betyder "stoppa och fråga".
- G6: SPEC 7.1 säger att Claude Codes grep hoppar över filer i .gitignore och binära filer.
- G4: det riktiga, oförändrade kontrollskriptet skriver OK i ett rent fall. Testet startar zsh som Terminal gör
  (TERM_PROGRAM=Apple_Terminal, med en tillfällig hemmapp), läser in systemets /etc/zshrc, som läser in Apples
  /etc/zshrc_Apple_Terminal, och sedan skriptet. Det läser systemfiler utanför projektet men skriver bara i
  testets tillfälliga mapp (Hugos val i chatten 2026-10-28). På en dator utan Apples fil hoppas testet över.
  Testet visade att Terminals fil läser in zsh:s funktion add-zsh-hook, som skriptet inte godtog. Hugos beslut i
  chatten 2026-10-28: skriptet godtar den bara från zsh:s egen mapp, och filen ska ägas av root.
"""

import os

import pytest

from test_beslut_granskning_15 import (
    AGARE_RAD,
    NVM_RADER,
    SKRIPTET,
    STEG_4_RADER,
    _avvikelser,
    _kor,
    _steg_4_h,
    _zsh,
    inget_zsh,
)
from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    INSTALLERA,
    _bedom,
    _en_rad,
    _installningar,
    _spec_7_1,
    _steg,
    mappar,
    vakt,
)

GREP_SOKER = "grep får bara söka"


def _grep_regeln():
    # Regeln "`grep` får bara söka" i SPEC 7.1, fram till nästa punkt i listan.
    return _spec_7_1().split("**`grep` får bara söka**", 1)[1].split(" - **", 1)[0]


# ---------------------------------------------------------------------------------------------
# G3: -R borttaget.


@pytest.mark.parametrize(
    "kommando",
    [
        "grep -R x scripts",
        "grep -nR x scripts",
        "grep -Rn x scripts",
        "grep -rR x scripts",
        "grep -iRe x scripts",
        "grep -n -R x scripts",
        "grep -R -- x scripts",
        "grep --dereference-recursive x scripts",
        "grep --dereference x scripts",
        "grep --deref x scripts",
        "grep --dereference-recursive=x x scripts",
    ],
)
def test_g3_grep_med_R_stoppas_i_varje_form(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and GREP_SOKER in fel, fel


@pytest.mark.parametrize(
    "kommando", ["grep -r x scripts", "grep -rn x scripts", "grep -nr x scripts", "grep --recursive x scripts"]
)
def test_g3_grep_med_r_gar_igenom_som_forut(vakt, mappar, kommando):
    assert _bedom(vakt, mappar, kommando) is None


def test_g3_R_star_inte_pa_listan_i_vakten_eller_spec(vakt):
    assert "R" not in vakt.GREP_KORTA + vakt.GREP_KORTA_VARDE
    assert "-R" not in vakt.GREP_TILLATNA.replace(",", " ").split()
    assert "dereference-recursive" not in vakt.GREP_LANGA
    grep_regel = _grep_regeln()
    lista = grep_regel.split("namnen jämförs exakt:", 1)[1].split("Allt annat stoppas", 1)[0]
    assert "`-R`" not in lista and "`-r`" in lista
    assert "granskning 16, G3" in grep_regel


# ---------------------------------------------------------------------------------------------
# G7: .ugrep förbjuden.

UGREP = ".ugrep"

# Varje kommando på listan som skriver en fil eller mapp, med .ugrep som mål. macOS skiljer i regel inte på
# stora och små bokstäver i filnamn, så .UGREP är samma fil.
UGREP_KOMMANDON = [
    ("mkdir", "mkdir <T>/.ugrep"),
    ("mkdir-p-djupt", "mkdir -p <T>/a/.ugrep/b"),
    ("mkdir-stora", "mkdir <T>/.UGREP"),
    ("cp-mal", "cp -R SPEC.md <T>/.ugrep"),
    ("cp-mal-i-mapp", "cp -R SPEC.md <T>/kopia/.ugrep"),
    ("cp-kalla", "cp -R <T>/.ugrep <T>/kopia"),
    ("cp-kalla-blandade", "cp -R <T>/.Ugrep <T>/kopia"),
    ("tar-c-arkiv", "tar -cf <T>/.ugrep scripts"),
    ("tar-x-mapp", "tar -xf <T>/kopia.tar -C <T>/.ugrep"),
    ("git-archive-o", "git archive -o <T>/.ugrep HEAD"),
    ("git-archive-o-hopskrivet", "git archive -o<T>/.ugrep HEAD"),
    ("git-archive-output", "git archive --output=<T>/.ugrep HEAD"),
]


@pytest.mark.parametrize("kommando", [k for _, k in UGREP_KOMMANDON], ids=[i for i, _ in UGREP_KOMMANDON])
def test_g7_kommandon_som_skriver_ugrep_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando)
    assert fel is not None and UGREP in fel and "granskning 16, G7" in fel, fel


def test_g7_en_lank_som_leder_till_ugrep_stoppas(vakt, mappar):
    # Målet ser ut som en annan fil, men länken leder till .ugrep.
    lank = f"{mappar['tillfallig']}/ser-oskyldig-ut"
    os.symlink(f"{mappar['tillfallig']}/.ugrep", lank)
    fel = _bedom(vakt, mappar, f"cp -R SPEC.md {lank}")
    assert fel is not None and UGREP in fel, fel


@pytest.mark.parametrize(
    "kommando",
    ["mkdir <T>/ugrep", "mkdir <T>/.ugrep2", "cp -R SPEC.md <T>/x.ugrep", "grep -n '.ugrep' SPEC.md",
     "cat <T>/kopia/SPEC.md"],
)
def test_g7_andra_namn_och_lasning_gar_igenom(vakt, mappar, kommando):
    # Bara en fil eller mapp som heter exakt .ugrep stoppas. Att söka efter ordet går igenom.
    assert _bedom(vakt, mappar, kommando) is None


@pytest.mark.parametrize("regel", ["Edit(//**/.ugrep)", "Edit(~/.ugrep)"])
def test_g7_filverktygen_far_inte_skriva_ugrep(regel):
    # Samma form som förbudet för filen .git (//**/.git gäller en fil med namnet på varje djup).
    assert regel in _installningar()["permissions"]["deny"]


@pytest.mark.parametrize(
    "tillagg", ["--config", "--config=.ugrep", "---", "---.ugrep", "--save-config", "--save-config=.ugrep", "-@"]
)
def test_g7_grep_tillagg_som_pekar_ut_en_installningsfil_stoppas(vakt, mappar, tillagg):
    fel = _bedom(vakt, mappar, f"grep {tillagg} x SPEC.md")
    assert fel is not None and GREP_SOKER in fel, fel


def test_g7_star_i_spec():
    spec = _spec_7_1()
    assert "**`.ugrep` är förbjuden**" in spec and "granskning 16, G7, Hugos beslut 2026-10-28" in spec


# ---------------------------------------------------------------------------------------------
# G2 och G6: meningarna i INSTALLERA.md steg 4 h och SPEC 7.1.


def test_g2_steg_4_h_sager_stoppa_for_allt_som_inte_ar_exakt_de_elva_raderna():
    steget = _en_rad(_steg_4_h())
    assert (
        "**Visar verktygsrutan något annat än exakt de elva raderna, i den ordningen: stoppa och fråga, och "
        "installera inte** (granskning 16, G2, Hugos beslut 2026-10-28)" in steget
    )
    assert "inte bara fallen som räknas upp här" in steget
    assert "en annan ordning" in steget and "en rad för mycket" in steget and "avkortad" in steget
    # Meningen står först i punkt 5, före de uppräknade fallen.
    punkt_5 = steget.split(" 5. ", 1)[1]
    assert punkt_5.startswith("**Visar verktygsrutan något annat än exakt de elva raderna")


def test_g6_spec_sager_att_claude_codes_grep_inte_soker_i_allt():
    grep_regel = _grep_regeln()
    assert "**Claude Codes `grep` söker inte i allt** (granskning 16, G6, Hugos beslut 2026-10-28)" in grep_regel
    assert "`.gitignore`" in grep_regel and "binära filer" in grep_regel and "`-E`" in grep_regel


# ---------------------------------------------------------------------------------------------
# G4: det riktiga skriptet skriver OK i ett rent fall.

SYSTEMETS_ZSHRC = "/etc/zshrc"
APPLES_TERMINALFIL = "/etc/zshrc_Apple_Terminal"
inte_mac = pytest.mark.skipif(
    not (os.path.isfile(SYSTEMETS_ZSHRC) and os.path.isfile(APPLES_TERMINALFIL)),
    reason="Apples filer för zsh och Terminal finns inte på den här datorn",
)


# Före varje prompt kör zsh funktionerna i precmd_functions. Terminals shell_session_history_check tar bort sig
# själv där, så i Terminal finns den inte kvar när Hugo kör skriptet (prövat i byggsessionen 2026-10-28). Utskriften
# från update_terminal_cwd (en kod till Terminal) visas inte.
FORSTA_PROMPTEN = "for f in $precmd_functions; do $f >/dev/null 2>&1; done\n"
TERMINAL_MILJO = {"TERM_PROGRAM": "Apple_Terminal", "TERM_SESSION_ID": "vera-prov", "TERM": "xterm-256color"}


def _som_terminal(tmp_path, skriptet=SKRIPTET, efter_start=""):
    hem = tmp_path / "hem"
    hem.mkdir()
    # Som Hugos ~/.zshrc efter steg 4: nvm:s rader och de två raderna som flyttar mappar sist i PATH.
    (hem / ".zshrc").write_text(NVM_RADER + STEG_4_RADER, encoding="utf-8")
    start = f"source {SYSTEMETS_ZSHRC}\nsource {hem / '.zshrc'}\n{FORSTA_PROMPTEN}{efter_start}\nsource {skriptet}\n"
    return _zsh(hem, start, **TERMINAL_MILJO)


@inte_mac
@inget_zsh
def test_g4_det_riktiga_skriptet_skriver_ok_i_ett_rent_fall(tmp_path):
    resultat = _som_terminal(tmp_path)
    assert resultat.stdout == "OK\nSLUT\n", resultat


@inte_mac
@inget_zsh
def test_g4_terminal_laser_in_add_zsh_hook_fran_zsh_egen_mapp(tmp_path):
    # Skälet till ändringen i skriptet: Terminals fil läser in add-zsh-hook, och den finns kvar.
    resultat = _zsh(tmp_path, f"source {SYSTEMETS_ZSHRC}\nwhence -v -- add-zsh-hook\n", **TERMINAL_MILJO)
    rad = resultat.stdout.splitlines()[0]
    assert rad.startswith("add-zsh-hook is a shell function from /usr/share/zsh/"), resultat
    assert rad.endswith("/functions/add-zsh-hook"), resultat


@pytest.mark.parametrize(
    "fore,vantat",
    [
        # En egen funktion med samma namn, från en annan fil.
        ("source {annan}", "AVVIKER: whence -v: add-zsh-hook is a shell function from {annan}"),
        # Skriven direkt i skalet.
        ("add-zsh-hook() {{ }}", "AVVIKER: whence -v: add-zsh-hook is a shell function from zsh"),
        # Bara anmäld, inte inläst: whence -v visar inte varifrån den kommer.
        ("autoload -Uz add-zsh-hook", "AVVIKER: whence -v: add-zsh-hook is an autoload shell function"),
    ],
)
@inget_zsh
def test_g4_add_zsh_hook_fran_en_annan_plats_avviker(tmp_path, fore, vantat):
    annan = tmp_path / "annan.zsh"
    annan.write_text("add-zsh-hook() { : }\n", encoding="utf-8")
    resultat = _kor(tmp_path, fore=fore.format(annan=annan))
    assert _avvikelser(resultat) == [vantat.format(annan=annan)], resultat
    assert resultat.stdout.endswith("SLUT\n") and "OK\n" not in resultat.stdout


@inget_zsh
def test_g4_add_zsh_hook_fran_zsh_egen_mapp_godtas(tmp_path):
    resultat = _kor(tmp_path, fore="autoload -Uz +X add-zsh-hook")
    assert resultat.stdout == "OK\nSLUT\n", resultat


@inget_zsh
def test_g4_add_zsh_hook_som_inte_ags_av_root_avviker(tmp_path):
    # Ingen fil i /usr/share/zsh kan få en annan ägare i ett test. I en kopia där bara en påhittad användare
    # godtas som ägare avviker därför filen för add-zsh-hook, som alla andra filer och mappar som prövas.
    text = SKRIPTET.read_text(encoding="utf-8")
    assert text.count(AGARE_RAD) == 1
    kopia = tmp_path / "kopia.zsh"
    kopia.write_text(text.replace(AGARE_RAD, "local -a agare=(vera_ingen)"), encoding="utf-8")
    resultat = _zsh(tmp_path, f"autoload -Uz +X add-zsh-hook\nsource {kopia}\n")
    rader = [r for r in _avvikelser(resultat) if "/functions/add-zsh-hook" in r]
    assert len(rader) == 1 and rader[0].startswith("AVVIKER: ls -l: ") and "ägs inte av root" in rader[0], resultat


def test_g4_installera_namner_add_zsh_hook():
    (steget,) = [t for r, t in _steg(INSTALLERA.read_text(encoding="utf-8")) if r.startswith("## Steg 4:")]
    g = _en_rad(steget.split("**g. ", 1)[1].split("**h. ", 1)[0])
    assert "`add-zsh-hook`" in g and "granskning 16, G4" in g and "`/usr/share/zsh/" in g
