"""Hugos beslut 2026-10-28 om fynden i granskning 13 (GRANSKNING.md, "Granskning 11 – plan för Q1").

- P1 a: Hugo kontrollerar alias och funktioner i Terminal före och efter installationen (INSTALLERA.md).
- P1 b: agentens fil-verktyg får inte skriva i filerna som zsh läser vid start, eller i filerna som de läser
  in (sparr/managed-settings.json). INSTALLERA.md säger vad Hugo gör om han senare lägger till en rad med
  source i ~/.zshrc.
- P2 a: vakten prövar varje länk i en kedja av länkar, inte bara den första och slutmålet
  (sparr/kommandosparr.py). Granskarens test i test_granskning_13.py är nu grönt.
- P3 b: PATH ändras inte. INSTALLERA.md använder hela sökvägen ~/.local/bin/claude och varnar för
  installerarens förslag.
- P4 a: agentens fil-verktyg får inte skriva i Claude Code för Terminal, skrivbordsappens Claude Code eller
  appen.
- Fråga 2: INSTALLERA.md visar att Claude Code för Terminal omfattas av samma låsta inställningar som appen.

Fixturerna (vakt, mappar, rotagd) och hjälpfunktionerna hämtas från test_kommandosparr.py, så att proven
görs på samma sätt som i de andra testerna.
"""

import os

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    FORE_PROGRAMMET,
    INSTALLERA,
    PLATS,
    SKRIPT_KORNING,
    SKRIPT_SUMMA,
    SYSTEMETS_SOKVAG,
    TERMINAL_CLAUDE,
    _bedom,
    _en_rad,
    _forsta_sudo,
    _installationskommandon,
    _installningar,
    _kontrollen,
    _lagg_program,
    _spec_7_1,
    _steg,
    mappar,
    rotagd,
    vakt,
)

# ---------------------------------------------------------------------------------------------
# P2 a: varje länk i kedjan prövas.


def _kedja(tmp_path, rotagd, mitten_ags_av_root, relativ=False):
    """rot/bin/git -> mitten/git -> mal/bin/git. rot och mal låtsas ägas av root (rotagd). mitten gör det
    bara om mitten_ags_av_root. Med relativ pekar länken i rot på mitten med en relativ sökväg."""
    mal_fil = _lagg_program(str(tmp_path / "mal" / "bin"), "git")
    rotagd(mal_fil)
    mitten = tmp_path / "mitten"
    mitten.mkdir()
    os.symlink(mal_fil, mitten / "git")
    if mitten_ags_av_root:
        rotagd(mitten)
    rot = tmp_path / "rot" / "bin"
    rot.mkdir(parents=True)
    os.symlink(os.path.join("..", "..", "mitten", "git") if relativ else mitten / "git", rot / "git")
    rotagd(rot)
    rotagd(rot / "git")
    return rot


def test_p2_kedja_dar_varje_lank_ags_av_root_slapps_igenom(vakt, mappar, tmp_path, rotagd):
    # Vakten stoppar inte mer än beslutet säger: ligger varje länk i en mapp som root äger går det igenom.
    rot = _kedja(tmp_path, rotagd, mitten_ags_av_root=True)
    assert _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}") is None


def test_p2_relativ_lank_i_mitten_i_anvandarens_mapp_stoppas(vakt, mappar, tmp_path, rotagd):
    # Samma kedja som i granskarens test, men länken i rot är relativ (../../mitten/git).
    rot = _kedja(tmp_path, rotagd, mitten_ags_av_root=False, relativ=True)
    assert not vakt._sakert_agd(str(tmp_path / "mitten")), "förutsättning: mitten ägs av användaren"
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and PLATS in fel and "en länk på vägen dit" in fel, fel


def test_p2_mapp_i_path_som_leder_via_en_lank_i_anvandarens_mapp_stoppas(vakt, mappar, tmp_path, rotagd):
    # En mapp i PATH före programmet: rot/bin -> mitten/bin -> mal/bin. Den gamla vakten prövade bara
    # rot/bin (som leder till mal/bin) och mal/bin, som båda låtsas ägas av root.
    mal = tmp_path / "mal" / "bin"
    mal.mkdir(parents=True)
    rotagd(mal)
    mitten = tmp_path / "mitten"
    mitten.mkdir()
    os.symlink(mal, mitten / "bin")
    rot = tmp_path / "rot"
    rot.mkdir()
    os.symlink(mitten / "bin", rot / "bin")
    rotagd(rot / "bin")
    fel = _bedom(vakt, mappar, "git status", sokvag=f"{rot / 'bin'}:{SYSTEMETS_SOKVAG}")
    assert fel is not None and FORE_PROGRAMMET in fel and "en länk på vägen dit" in fel, fel


def test_p2_for_lang_kedja_stoppas(vakt, mappar, tmp_path, rotagd):
    # Allt i kedjan låtsas ägas av root. Med MAX_LANKAR länkar går det igenom, med en till stoppas det.
    mapp = tmp_path / "kedja"
    mal_fil = _lagg_program(str(mapp), "git-mal")
    rotagd(mapp)
    rotagd(mal_fil)
    forra = mal_fil
    for nummer in range(vakt.MAX_LANKAR + 1):
        lank = mapp / f"lank-{nummer}"
        os.symlink(os.path.basename(forra), lank)
        rotagd(lank)
        forra = str(lank)
    # Kedjan prövas för sig, så att macOS egen gräns för länkar (som stat använder) inte avgör provet.
    langst_tillaten = str(mapp / f"lank-{vakt.MAX_LANKAR - 1}")
    for_lang = str(mapp / f"lank-{vakt.MAX_LANKAR}")
    assert vakt._saker_kedja(langst_tillaten)
    assert not vakt._saker_kedja(for_lang)


def test_p2_systemets_program_slapps_fortfarande_igenom(vakt):
    # På den här datorn: programmen på listan i /usr/bin och /bin klarar den nya kontrollen.
    for fil in ("/usr/bin/git", "/usr/bin/tar", "/bin/ls"):
        if os.path.exists(fil) and os.stat("/usr/bin").st_uid == 0:
            assert vakt._saker_plats(fil), fil


def test_p2_granskarens_test_ar_inte_langre_markerat_vantat_rott():
    text = (INSTALLERA.parents[1] / "scripts" / "tests" / "test_granskning_13.py").read_text(encoding="utf-8")
    assert "def test_lank_via_en_lank_i_en_mapp_som_anvandaren_ager_stoppas" in text
    assert "@pytest.mark.xfail" not in text


# ---------------------------------------------------------------------------------------------
# P1 b: förbud för filerna som zsh läser vid start och de filer som de läser in. Kartlagt 2026-10-28 på
# Hugos dator (PROGRESS.md): ~/.zshrc läser in ~/.nvm/nvm.sh och ~/.nvm/bash_completion, /etc/zshrc läser
# in ~/.zkbd/<terminal>, och /etc/zshrc_Apple_Terminal läser in ~/.zsh_sessions/<session>.session.
# ~/.zshenv, ~/.zprofile och ~/.zlogin finns inte, men zsh läser dem om de skapas.

ZSH_FORBUD = [
    "Edit(~/.zshenv)",
    "Edit(~/.zprofile)",
    "Edit(~/.zshrc)",
    "Edit(~/.zlogin)",
    "Edit(~/.zlogout)",
    "Edit(//etc/zshenv)",
    "Edit(//etc/zprofile)",
    "Edit(//etc/zshrc)",
    "Edit(//etc/zshrc_*)",
    "Edit(//etc/zlogin)",
    "Edit(//etc/zlogout)",
    "Edit(~/.nvm/**)",
    "Edit(~/.zkbd/**)",
    "Edit(~/.zsh_sessions/**)",
]


@pytest.mark.parametrize("regel", ZSH_FORBUD)
def test_p1b_installningarna_nekar_att_skriva_i_zsh_filer_och_filer_de_laser_in(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_p1b_installera_sager_vad_hugo_gor_med_en_ny_source_rad():
    efterat = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Efteråt", 1)[1].split("\n## ", 1)[0])
    assert "Om du senare lägger till en ny rad med `source` i `~/.zshrc`" in efterat
    assert "Lägg inte till raden än" in efterat and "ny version av inställningsfilen" in efterat
    assert "Hugos beslut 2026-10-28, granskning 13, P1 b" in efterat


# ---------------------------------------------------------------------------------------------
# P4 a: förbud för Claude Code för Terminal, skrivbordsappens Claude Code och appen. Platserna lästes med
# ls -l 2026-10-28 (PROGRESS.md).

P4_FORBUD = [
    "Edit(~/.local/bin/claude)",
    "Edit(~/.local/share/claude/**)",
    "Edit(~/Library/Application Support/Claude/claude-code/**)",
    "Edit(//Applications/Claude.app/**)",
]


@pytest.mark.parametrize("regel", P4_FORBUD)
def test_p4_installningarna_nekar_att_skriva_i_claude_code(regel):
    assert regel in _installningar()["permissions"]["deny"]


def test_hugos_svar_3_hela_appens_mapp_ar_forbjuden():
    # Hugos svar 2026-10-28 efter granskning 13, punkt 3: hela ~/Library/Application Support/Claude förbjuds för agentens
    # fil-verktyg, inte bara mappen claude-code. Där ligger också skrivbordsappens egna inställningar.
    # ** gäller allt under mappen, på varje djup (code.claude.com/docs/en/permissions).
    neka = _installningar()["permissions"]["deny"]
    assert "Edit(~/Library/Application Support/Claude/**)" in neka
    vad = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[0])
    assert "hela `~/Library/Application Support/Claude`" in vad
    assert "Hugos svar 2026-10-28 efter granskning 13, punkt 3" in vad


# ---------------------------------------------------------------------------------------------
# P1 a: alias och funktioner kontrolleras i Terminal före och efter installationen.

# find står inte längre på listan (granskning 15, S1, Hugos beslut 2026-10-28).
LISTANS_NAMN = ("git", "ls", "cat", "head", "tail", "grep", "diff", "wc", "sort", "mkdir", "cp", "tar")


def test_p1a_listans_namn_ar_kommandona_pa_listan(vakt):
    assert set(vakt.LASANDE) | {"git", "mkdir", "cp", "tar"} == set(LISTANS_NAMN)


def _alias_steget_fore():
    text = INSTALLERA.read_text(encoding="utf-8")
    (steget,) = [t for r, t in _steg(text) if "alias" in r.lower()]
    return steget.split("**g. Kontrollera skalet i Terminal med kontrollskriptet**", 1)[1].split("**h. ", 1)[0]


def _alias_steget_efter():
    return _kontrollen().split("\n2. ", 1)[0].split("**Skalet, igen efter installationen**", 1)[1]


def test_p1a_alias_och_funktioner_kontrolleras_fore_och_efter_installationen():
    # Hugos beslut 2026-10-28 efter granskning 15: kontrollen ligger i sparr/kontrollera-skalet.zsh, som Hugo
    # kör före och efter installationen (prövat i test_beslut_granskning_15.py).
    _, rader = _installationskommandon()
    for kommando in (SKRIPT_SUMMA, SKRIPT_KORNING):
        platser = [i for i, r in enumerate(rader) if r == kommando]
        assert len(platser) == 2, kommando
        assert platser[0] < _forsta_sudo(rader), "en gång före installationen"
        assert platser[1] > max(i for i, r in enumerate(rader) if r.startswith("sudo chmod")), "en gång efter"
    for steget in (_alias_steget_fore(), _alias_steget_efter()):
        # Kodblocken i kontrollen efter installationen är indragna under sin listpunkt.
        utan_indrag = "\n".join(rad.strip() for rad in steget.splitlines())
        for kommando in (SKRIPT_SUMMA, SKRIPT_KORNING):
            assert f"```bash\n{kommando}\n```" in utan_indrag, kommando
        en_rad = _en_rad(steget)
        assert "stoppa och fråga" in en_rad.lower() and "`AVVIKER`" in en_rad
        assert "granskning 13, P1 a" in en_rad
    skriptet = (INSTALLERA.parent / "kontrollera-skalet.zsh").read_text(encoding="utf-8")
    assert "${(kv)aliases}" in skriptet and "${(kv)galiases}" in skriptet and "${(kv)saliases}" in skriptet


# ---------------------------------------------------------------------------------------------
# P3 b: PATH ändras inte. Hela sökvägen i Terminal, och en varning för installerarens förslag.

INSTALLERARENS_FORSLAG = 'export PATH="$HOME/.local/bin:$PATH"'


def test_p3b_installera_lagger_aldrig_lokala_bin_i_path():
    _, rader = _installationskommandon()
    for rad in rader:
        assert not (".local/bin" in rad and (">>" in rad or "PATH" in rad or "path=" in rad)), rad
    assert INSTALLERARENS_FORSLAG not in rader


def test_p3b_installera_varnar_for_installerarens_forslag_och_forklarar_varfor():
    text = INSTALLERA.read_text(encoding="utf-8")
    forsta = _en_rad(_steg(text)[0][1].replace("\n>", "\n"))
    assert "Varning: kör inte installerarens förslag." in forsta
    assert f"`{INSTALLERARENS_FORSLAG}`" in forsta
    assert "Kör den inte" in forsta
    # Varför: mappen hamnar först, Hugo äger den, vakten stoppar allt, och ett program där körs i stället.
    assert "**först** i `PATH`" in forsta and "ägs av dig" in forsta and "**alla** kommandon" in forsta
    assert "i stället för systemets program" in forsta
    (steg_4,) = [_en_rad(t) for r, t in _steg(text) if "nvm" in r.lower()]
    assert "ska **inte** stå någonstans i raden" in steg_4


def test_p3b_terminal_anvander_hela_sokvagen_i_installera_och_spec():
    text, rader = _installationskommandon()
    assert TERMINAL_CLAUDE == "~/.local/bin/claude"
    terminal = [r for r in rader if "claude" in r.split()[0]]
    assert terminal and all(r.split()[0] == TERMINAL_CLAUDE for r in terminal), terminal
    spec = _spec_7_1()
    assert "`~/.local/bin/claude`" in spec and "granskning 13, P3 b" in spec
    assert "Hittas inte `claude`" not in spec


# ---------------------------------------------------------------------------------------------
# Fråga 2: Claude Code för Terminal behålls, utanför PATH, och omfattas av samma låsta inställningar.


def test_fraga_2_terminal_omfattas_av_samma_lasta_installningar_som_appen():
    vad = _en_rad(INSTALLERA.read_text(encoding="utf-8").split("## Innan du börjar", 1)[0])
    assert "Claude Code för Terminal omfattas av samma låsta inställningar som appen" in vad
    assert "code.claude.com/docs/en/managed-settings" in vad and "utanför `PATH`" in vad
    assert "`Enterprise managed settings (file)`" in vad
    assert "granskning 13, fråga 2" in vad
