"""Vakten för den fasta kommandolistan i SPEC 7.1 (granskning 11, Q1).

Claude Code kör vakten före varje verktyg som agenten använder (en hook av typen PreToolUse i de låsta
inställningarna, se managed-settings.json och INSTALLERA.md i samma mapp). Claude Code skickar en
beskrivning av verktyget som JSON på standard in. Vakten svarar på två sätt:

- kod 0 och ingen utskrift: vakten har inget att invända, och Claude Code frågar som vanligt,
- kod 2 och ett fel på svenska på standard fel: verktyget stoppas, och agenten ser felet.

Vakten godkänner aldrig något själv. Den kan bara stoppa.

Reglerna, i den ordning de prövas (planen i GRANSKNING.md, "Granskning 11 – plan för Q1"):

1. sudo och su stoppas alltid (Hugos beslut 2026-10-28, 5 och 7).
2. Andra verktyg som kör kommandon än Bash stoppas helt. Fil-verktygen (läsa, skriva, redigera)
   släpps igenom, eftersom 7.1 bara gäller kommandon.
3. Ingen mapp undantas (Hugos beslut 8). Kommandot ska köras i mappen där sessionen startade
   (CLAUDE_PROJECT_DIR), och den mappen får inte vara hemmappen eller en mapp ovanför den.
4. Inga ihopkopplade kommandon: inget ;, &, |, <, >, $, bakåtfnutt, omvänt snedstreck eller
   radbrytning, inte heller inom citattecken. Inga osynliga eller styrande tecken. Inga tecken som
   skalet byter ut mot något annat (jokertecken, ~ och liknande) utanför citattecken.
5. Första ordet ska stå på listan i SPEC 7.1.
6. Reglerna under listan: mål bara i den tillfälliga mappen, find bara för att söka, pytest bara i de
   två formerna, inga git-tillägg som skriver filer eller kör program, och läsande kommandon bara i
   projektet och i den tillfälliga mappen.

Allt som vakten inte känner igen stoppas. Om vakten själv kraschar stoppas kommandot också, både här
(kod 2) och av Claude Code (inställningen "onFailure": "block").

Vakten körs med datorns egen Python (/usr/bin/python3 -I) och använder bara Pythons egna delar. -I gör
att Python inte läser in filer från vaktens mapp, arbetsmappen eller inställningar i miljön.
"""

from __future__ import annotations

import json
import os
import pwd
import sys
import unicodedata

FORSTA = "Stoppat av vakten: "

SUDO_OCH_SU = ("sudo", "su")

# Regel 2: verktyg som kör kommandon. Bash prövas mot listan. Övriga stoppas helt.
KOMMANDOVERKTYG = ("PowerShell", "Monitor")
KOMMANDOORD = (
    "bash",
    "shell",
    "terminal",
    "command",
    "exec",
    "run_",
    "preview_start",
    "simulator__build",
    "sync_with_base_branch",
)

# Regel 4: tecken som kopplar ihop kommandon eller styr om utskriften, var de än står.
IHOPKOPPLING = {
    ";": "semikolon (;)",
    "&": "&",
    "|": "lodstreck (|)",
    "<": "<",
    ">": ">",
    "$": "dollartecken ($)",
    "`": "bakåtfnutt (`)",
    "\\": "omvänt snedstreck (\\)",
    "\n": "radbrytning",
    "\r": "vagnretur",
}
# Tecken som skalet (bash eller zsh) byter ut mot något annat utanför citattecken: jokertecken,
# hemmappen (~), uttryck med parenteser och zsh:s utökade jokertecken (^ och #). = i början av ett
# ord byts i zsh mot sökvägen till ett program.
UTBYTESTECKEN = "*?[{()~^#"
OSYNLIGA_KATEGORIER = ("Cc", "Cf", "Cn", "Co", "Cs", "Zl", "Zp", "Zs")

# Regel 5 och 6: listan i SPEC 7.1.
PYTHON = ".venv/bin/python"
PYTEST_FAST = ["-B", "-m", "pytest", "-p", "no:cacheprovider"]
PYTEST_PROJEKTET = os.path.join("scripts", "tests")
PYTEST_TB = ("auto", "long", "short", "line", "native", "no")

LASANDE = ("ls", "cat", "head", "tail", "grep", "diff", "find", "wc", "sort")
LASANDE_FORBJUDNA_KORTA = {"sort": "oT", "grep": "f"}
LASANDE_FORBJUDNA_LANGA = {
    "sort": ("output", "compress-program", "temporary-directory"),
    "grep": ("file",),
}
FIND_FORBJUDNA = ("exec", "execdir", "ok", "okdir", "delete", "fprint", "fprint0", "fprintf", "fls")

GIT_UNDERKOMMANDON = ("status", "log", "diff", "add", "commit", "show", "archive")
# git godtar förkortade långa tillägg (--out för --output), så ett tillägg stoppas om dess namn är
# början på ett förbjudet namn. GIT_SAKRA är hela namn som är början på ett förbjudet namn men som
# git läser som sig själva (--text är inte --textconv).
GIT_FORBJUDNA_LANGA = (
    "output",
    "exec-path",
    "exec",
    "ext-diff",
    "textconv",
    "no-index",
    "git-dir",
    "work-tree",
    "remote",
    "config-env",
    "upload-pack",
    "receive-pack",
    "add-file",
    "add-virtual-file",
)
GIT_SAKRA = ("text",)
# Per underkommando: (förbjudna korta tillägg, förbjudna långa tillägg, korta tillägg som tar ett värde,
# långa tillägg som tar ett värde i nästa ord). -c, -e, -p, -i och -t öppnar ett fönster för att
# skriva eller frågar om varje ändring, -O läser en fil.
GIT_REGLER = {
    "status": ("", (), "", ()),
    "add": ("pie", ("interactive", "patch", "edit", "pathspec-from-file"), "", ()),
    "commit": (
        "cept",
        ("interactive", "patch", "edit", "reedit-message", "template", "pathspec-from-file"),
        "mFCct",
        ("message", "file", "author", "date", "reuse-message", "fixup", "squash", "trailer", "cleanup"),
    ),
    "diff": ("cO", (), "SGOUnLl", ()),
    "log": ("cO", (), "SGOUnLl", ()),
    "show": ("cO", (), "SGOUnLl", ()),
}

TILLATNA_KOMMANDON = (
    ".venv/bin/python (bara pytest), git, ls, cat, head, tail, grep, diff, find, wc, sort, mkdir, "
    "cp -R och tar"
)


class _Stopp(Exception):
    pass


class _Lage:
    def __init__(self, projekt, tillfallig):
        self.projekt = projekt
        self.tillfallig = tillfallig


def bedom(indata, projektmapp, hemmapp):
    """Bedömer ett verktyg. Returnerar None om vakten inte invänder, annars felet på svenska."""
    try:
        _bedom(indata, projektmapp, hemmapp)
    except _Stopp as stopp:
        return FORSTA + str(stopp)
    return None


def _bedom(indata, projektmapp, hemmapp):
    if not isinstance(indata, dict):
        _indatafel("det är inte ett JSON-objekt")
    verktyg = indata.get("tool_name")
    if not isinstance(verktyg, str):
        _indatafel("verktygets namn saknas")
    verktygsdata = indata.get("tool_input")

    # Regel 1.
    if isinstance(verktygsdata, dict) and isinstance(verktygsdata.get("command"), str):
        _sudo_och_su(verktygsdata["command"])

    if verktyg != "Bash":
        # Regel 2.
        if verktyg in KOMMANDOVERKTYG or any(ord_ in verktyg.lower() for ord_ in KOMMANDOORD):
            raise _Stopp(
                f"verktyget {verktyg} kör kommandon och är stoppat. Bara Bash får köra kommandon, och "
                "bara de som står i SPEC 7.1."
            )
        return

    if not isinstance(verktygsdata, dict):
        _indatafel("tool_input saknas")
    kommando = verktygsdata.get("command")
    if not isinstance(kommando, str):
        _indatafel("kommandot saknas eller är inte text")
    cwd = indata.get("cwd")
    if not isinstance(cwd, str):
        _indatafel("mappen där kommandot körs (cwd) saknas")

    # Regel 3.
    lage = _sessionen(projektmapp, hemmapp, cwd, indata.get("scratchpad_dir"))

    # Regel 4.
    if not kommando.strip():
        raise _Stopp("kommandot är tomt.")
    for tecken in kommando:
        if tecken in IHOPKOPPLING:
            raise _Stopp(
                f"tecknet {IHOPKOPPLING[tecken]} är inte tillåtet, inte heller inom citattecken. "
                "Kommandon kopplas inte ihop och utskriften styrs inte om: ett kommando i taget "
                "(SPEC 7.1)."
            )
    for tecken in kommando:
        if tecken != " " and unicodedata.category(tecken) in OSYNLIGA_KATEGORIER:
            raise _Stopp(
                f"kommandot innehåller ett osynligt eller styrande tecken (U+{ord(tecken):04X}). Det ska "
                "synas exakt vad som körs (SPEC 7.1)."
            )
    ordlista = _dela_upp(kommando)
    _sudo_och_su(ordlista[0])

    # Regel 5 och 6.
    forsta = ordlista[0]
    if forsta == PYTHON:
        _pytest(ordlista, lage)
    elif forsta == "git":
        _git(ordlista, lage)
    elif forsta in LASANDE:
        _lasande(ordlista, lage)
    elif forsta == "mkdir":
        _mkdir(ordlista, lage)
    elif forsta == "cp":
        _cp(ordlista, lage)
    elif forsta == "tar":
        _tar(ordlista, lage)
    else:
        raise _Stopp(
            f"'{forsta}' står inte på listan i SPEC 7.1. Tillåtna kommandon: {TILLATNA_KOMMANDON}."
        )


def _indatafel(detalj):
    raise _Stopp(
        f"vakten fick indata som den inte kan läsa ({detalj}). Kommandot stoppas för säkerhets skull."
    )


def _sudo_och_su(kommando):
    delar = kommando.split()
    if not delar:
        return
    forsta = delar[0].strip("'\"\\").rsplit("/", 1)[-1].lower()
    if forsta in SUDO_OCH_SU:
        raise _Stopp("sudo och su stoppas alltid, i alla mappar (Hugos beslut 2026-10-28).")


def _sessionen(projektmapp, hemmapp, cwd, tillfallig):
    if not projektmapp:
        raise _Stopp(
            "Claude Code har inte angett projektmappen (CLAUDE_PROJECT_DIR), så vakten vet inte var "
            "kommandon får köras. Kommandot stoppas för säkerhets skull."
        )
    projekt = os.path.realpath(projektmapp)
    hem = os.path.realpath(hemmapp)
    if _inom(hem, projekt):
        raise _Stopp(
            f"sessionen är startad i hemmappen eller i en mapp ovanför den ({projekt}). Då skulle "
            "läsande kommandon nå allt i hemmappen. Starta sessionen i projektmappen."
        )
    if os.path.realpath(cwd) != projekt:
        raise _Stopp(
            f"kommandot skulle köras i en annan mapp ({cwd}) än projektmappen ({projekt}). Allt körs "
            "från projektmappen, och cd används inte (SPEC 7.1)."
        )
    godkand = None
    if isinstance(tillfallig, str) and tillfallig:
        mapp = os.path.realpath(tillfallig)
        if not (_inom(mapp, projekt) or _inom(projekt, mapp) or _inom(hem, mapp)):
            godkand = mapp
    return _Lage(projekt, godkand)


def _dela_upp(kommando):
    """Delar kommandot i ord som skalet gör, och stoppar tecken som skalet skulle byta ut."""
    ordlista = []
    nu = []
    borjat = False
    citat = None
    for tecken in kommando:
        if citat:
            if tecken == citat:
                citat = None
            else:
                nu.append(tecken)
            continue
        if tecken == " ":
            if borjat:
                ordlista.append("".join(nu))
                nu = []
                borjat = False
            continue
        if tecken in "'\"":
            citat = tecken
            borjat = True
            continue
        if tecken in UTBYTESTECKEN or (tecken == "=" and not borjat):
            raise _Stopp(
                f"tecknet {tecken} utanför citattecken är inte tillåtet: skalet byter ut det mot något "
                "annat än det som står (till exempel filnamn eller hemmappen). Sätt texten inom "
                "enkla citattecken."
            )
        nu.append(tecken)
        borjat = True
    if citat:
        raise _Stopp("ett citattecken är inte stängt.")
    if borjat:
        ordlista.append("".join(nu))
    return ordlista


# ---------------------------------------------------------------------------------------------
# Sökvägar

def _inom(sokvag, rot):
    return sokvag == rot or sokvag.startswith(rot.rstrip(os.sep) + os.sep)


def _verklig(sokvag, bas):
    if not os.path.isabs(sokvag):
        sokvag = os.path.join(bas, sokvag)
    return os.path.realpath(sokvag)


def _las(sokvag, etikett, lage, bas=None):
    verklig = _verklig(sokvag, bas or lage.projekt)
    if _inom(verklig, lage.projekt) or (lage.tillfallig and _inom(verklig, lage.tillfallig)):
        return
    raise _Stopp(
        f"{etikett}: sökvägen '{sokvag}' ligger utanför projektet och den tillfälliga mappen. Bara filer "
        "i projektet och kopior i den tillfälliga mappen får läsas (SPEC 7.1 och CLAUDE.md)."
    )


def _mal(sokvag, etikett, lage):
    if not lage.tillfallig:
        raise _Stopp(
            f"{etikett}: får bara ha mål i en tillfällig mapp (scratchpad-mappen), och sessionen har "
            "ingen godkänd tillfällig mapp (SPEC 7.1)."
        )
    if sokvag and _inom(_verklig(sokvag, lage.projekt), lage.tillfallig):
        return
    raise _Stopp(
        f"{etikett}: får bara ha mål i en tillfällig mapp ({lage.tillfallig}), aldrig i projektet "
        f"(SPEC 7.1). '{sokvag}' ligger inte där."
    )


# ---------------------------------------------------------------------------------------------
# Kommandona på listan

def _pytest(ordlista, lage):
    if ordlista[1:6] != PYTEST_FAST:
        raise _Stopp(
            f"pytest: {PYTHON} får bara köras som '{PYTHON} -B -m pytest -p no:cacheprovider', följt av "
            "tillåtna tillägg och ett mål (SPEC 7.1)."
        )
    mal = []
    i = 6
    while i < len(ordlista):
        ord_ = ordlista[i]
        if ord_ in ("-q", "-qq"):
            pass
        elif ord_ == "--tb" or ord_.startswith("--tb="):
            if ord_ == "--tb":
                i += 1
                varde = ordlista[i] if i < len(ordlista) else ""
            else:
                varde = ord_[len("--tb="):]
            if varde not in PYTEST_TB:
                raise _Stopp(f"pytest: --tb får bara vara {', '.join(PYTEST_TB)}.")
        elif ord_ == "-r" or (ord_.startswith("-r") and not ord_.startswith("--")):
            if ord_ == "-r":
                i += 1
                varde = ordlista[i] if i < len(ordlista) else ""
            else:
                varde = ord_[2:]
            if not (varde.isascii() and varde.isalpha()):
                raise _Stopp("pytest: -r får bara följas av bokstäver, till exempel -rA.")
        elif ord_ == "-k":
            i += 1
            if i >= len(ordlista):
                raise _Stopp("pytest: -k saknar ett mönster.")
        elif ord_.startswith("-k") and not ord_.startswith("--"):
            pass
        elif ord_ == "-p" or (ord_.startswith("-p") and not ord_.startswith("--")):
            if ord_ == "-p":
                i += 1
                varde = ordlista[i] if i < len(ordlista) else ""
            else:
                varde = ord_[2:]
            if varde != "no:randomly":
                raise _Stopp("pytest: -p får bara användas som -p no:randomly (SPEC 7.1).")
        elif ord_.startswith("-"):
            raise _Stopp(
                f"pytest: tillägget '{ord_}' är inte tillåtet. Tillåtna: --tb, -q, -qq, -r, -k och "
                "-p no:randomly (SPEC 7.1)."
            )
        else:
            mal.append(ord_)
        i += 1
    if len(mal) != 1:
        raise _Stopp("pytest: ange exakt ett mål, scripts/tests eller en kopia i den tillfälliga mappen.")
    if os.path.normpath(mal[0]) == PYTEST_PROJEKTET:
        return
    if lage.tillfallig and _inom(_verklig(mal[0], lage.projekt), lage.tillfallig):
        return
    raise _Stopp(
        f"pytest: målet '{mal[0]}' är inte tillåtet. Målet ska vara scripts/tests, eller en kopia (eller en "
        "testfil i en kopia) i den tillfälliga mappen (SPEC 7.1)."
    )


def _git_tillagg(tillagg, underkommando):
    raise _Stopp(
        f"git-tillägget '{tillagg}' är inte tillåtet för git {underkommando}: det skriver filer, kör andra "
        "program, läser filer utanför git eller öppnar ett fönster för att skriva (SPEC 7.1)."
    )


def _forbjudet_langt(namn, forbjudna, sakra=()):
    if not namn or namn in sakra:
        return False
    return any(forbjudet.startswith(namn) for forbjudet in forbjudna)


def _git(ordlista, lage):
    if len(ordlista) < 2 or ordlista[1] not in GIT_UNDERKOMMANDON:
        raise _Stopp(
            f"'{' '.join(ordlista[:2])}' står inte på listan i SPEC 7.1. Tillåtna: git status, git log, "
            "git diff, git add, git commit, git show och git archive, utan tillägg före det andra ordet "
            "(till exempel -C eller -c)."
        )
    underkommando = ordlista[1]
    argument = ordlista[2:]
    if underkommando == "archive":
        _git_archive(argument, lage)
        return
    korta_forbjudna, langa_forbjudna, korta_varde, langa_varde = GIT_REGLER[underkommando]
    i = 0
    while i < len(argument):
        ord_ = argument[i]
        if ord_ == "--":
            return
        if ord_.startswith("--"):
            namn, lika, varde = ord_[2:].partition("=")
            if _forbjudet_langt(namn, GIT_FORBJUDNA_LANGA + langa_forbjudna, GIT_SAKRA):
                _git_tillagg(ord_, underkommando)
            if not lika and namn in langa_varde:
                i += 1
                varde = argument[i] if i < len(argument) else ""
            if underkommando == "commit" and namn == "file":
                _commit_fil(varde, lage)
        elif ord_.startswith("-") and ord_ != "-":
            for j in range(1, len(ord_)):
                bokstav = ord_[j]
                if bokstav in korta_forbjudna:
                    _git_tillagg(ord_, underkommando)
                if bokstav in korta_varde:
                    varde = ord_[j + 1:]
                    if not varde:
                        i += 1
                        varde = argument[i] if i < len(argument) else ""
                    if underkommando == "commit" and bokstav == "F":
                        _commit_fil(varde, lage)
                    break
        i += 1


def _commit_fil(sokvag, lage):
    if sokvag == "-":
        return
    if not sokvag:
        raise _Stopp("git commit: -F saknar en fil.")
    _las(sokvag, "git commit", lage)


def _git_archive(argument, lage):
    i = 0
    while i < len(argument):
        ord_ = argument[i]
        if ord_ == "--":
            return
        if ord_.startswith("--"):
            namn, lika, varde = ord_[2:].partition("=")
            if namn == "output":
                if not lika:
                    i += 1
                    varde = argument[i] if i < len(argument) else ""
                _mal(varde, "git archive", lage)
            elif namn in ("format", "prefix"):
                if not lika:
                    i += 1
            elif namn in ("verbose", "worktree-attributes") and not lika:
                pass
            else:
                _git_tillagg(ord_, "archive")
        elif ord_.startswith("-") and ord_ != "-":
            if ord_ == "-o":
                i += 1
                _mal(argument[i] if i < len(argument) else "", "git archive", lage)
            elif ord_.startswith("-o"):
                _mal(ord_[2:], "git archive", lage)
            elif not (ord_ == "-v" or (len(ord_) == 2 and ord_[1].isdigit())):
                _git_tillagg(ord_, "archive")
        i += 1


def _lasande(ordlista, lage):
    namn = ordlista[0]
    korta = LASANDE_FORBJUDNA_KORTA.get(namn, "")
    langa = LASANDE_FORBJUDNA_LANGA.get(namn, ())
    efter_streck = False
    for ord_ in ordlista[1:]:
        if efter_streck or not ord_.startswith("-"):
            _las(ord_, namn, lage)
        elif ord_ == "-":
            pass
        elif ord_ == "--":
            efter_streck = True
        elif namn == "find":
            if ord_[1:] in FIND_FORBJUDNA:
                raise _Stopp(
                    f"find får bara söka. Tillägget '{ord_}' raderar filer, kör andra kommandon eller "
                    "skriver filer (SPEC 7.1)."
                )
        elif ord_.startswith("--"):
            tillagg, lika, varde = ord_[2:].partition("=")
            if _forbjudet_langt(tillagg, langa):
                _forbjudet_tillagg(namn, ord_)
            if lika:
                _las(varde, namn, lage)
        else:
            if "/" in ord_:
                raise _Stopp(
                    f"{namn}: tillägget '{ord_}' innehåller en sökväg. Skriv sökvägen som ett eget ord, så "
                    "att vakten kan pröva den."
                )
            if any(bokstav in korta for bokstav in ord_[1:]):
                _forbjudet_tillagg(namn, ord_)


def _forbjudet_tillagg(namn, tillagg):
    raise _Stopp(
        f"{namn}: tillägget '{tillagg}' är inte tillåtet: det skriver filer, kör andra program eller läser "
        "en fil med mönster (SPEC 7.1)."
    )


def _tillagg_och_operander(ordlista, tillatna, namn):
    tillagg = set()
    operander = []
    efter_streck = False
    for ord_ in ordlista[1:]:
        if not efter_streck and ord_ == "--":
            efter_streck = True
        elif not efter_streck and ord_.startswith("-") and ord_ != "-":
            if ord_.startswith("--") or not set(ord_[1:]) <= set(tillatna):
                raise _Stopp(
                    f"{namn}: tillägget '{ord_}' är inte tillåtet. Bara "
                    f"{', '.join('-' + t for t in tillatna)} får användas."
                )
            tillagg |= set(ord_[1:])
        else:
            operander.append(ord_)
    return tillagg, operander


def _mkdir(ordlista, lage):
    _, operander = _tillagg_och_operander(ordlista, "pv", "mkdir")
    if not operander:
        raise _Stopp("mkdir: ange vilken mapp som ska skapas.")
    for operand in operander:
        _mal(operand, "mkdir", lage)


def _cp(ordlista, lage):
    tillagg, operander = _tillagg_och_operander(ordlista, "Rpv", "cp")
    if "R" not in tillagg:
        raise _Stopp("cp får bara köras som cp -R (SPEC 7.1).")
    if len(operander) < 2:
        raise _Stopp("cp -R: ange vad som ska kopieras och vart.")
    for operand in operander[:-1]:
        _las(operand, "cp -R", lage)
    _mal(operander[-1], "cp -R", lage)


def _tar(ordlista, lage):
    argument = ordlista[1:]
    if not argument or not argument[0].startswith("-"):
        raise _Stopp("tar: skriv tilläggen med bindestreck, till exempel tar -xf, så att de läses som det står.")
    lage_tar = None
    arkiv = None
    mappar = []
    operander = []
    i = 0
    while i < len(argument):
        ord_ = argument[i]
        if ord_ == "--":
            operander.extend(argument[i + 1:])
            break
        if ord_.startswith("--"):
            namn, lika, _ = ord_[2:].partition("=")
            if namn != "exclude":
                raise _Stopp(
                    f"tar: tillägget '{ord_}' är inte tillåtet. Bara -c, -x, -t, -f, -C, -v, -z och "
                    "--exclude får användas."
                )
            if not lika:
                i += 1
        elif ord_.startswith("-") and len(ord_) > 1:
            for j in range(1, len(ord_)):
                bokstav = ord_[j]
                if bokstav in "cxt":
                    if lage_tar and lage_tar != bokstav:
                        raise _Stopp("tar: bara ett av -c, -x och -t får användas.")
                    lage_tar = bokstav
                elif bokstav in "fC":
                    varde = ord_[j + 1:]
                    if not varde:
                        i += 1
                        varde = argument[i] if i < len(argument) else ""
                    if not varde:
                        raise _Stopp(f"tar: -{bokstav} saknar ett värde.")
                    if bokstav == "f":
                        if arkiv is not None:
                            raise _Stopp("tar: -f får bara anges en gång.")
                        arkiv = varde
                    else:
                        mappar.append(varde)
                    break
                elif bokstav not in "vz":
                    raise _Stopp(
                        f"tar: tillägget '-{bokstav}' är inte tillåtet. Bara -c, -x, -t, -f, -C, -v, -z "
                        "och --exclude får användas."
                    )
        else:
            operander.append(ord_)
        i += 1
    if lage_tar is None:
        raise _Stopp("tar: ange -c (packa ihop), -x (packa upp) eller -t (lista).")
    if arkiv is None or arkiv == "-":
        raise _Stopp("tar: ange arkivet med -f och ett filnamn (inte -).")
    if len(mappar) > 1:
        raise _Stopp("tar: -C får bara anges en gång.")
    if lage_tar == "c":
        _mal(arkiv, "tar", lage)
        bas = lage.projekt
        if mappar:
            _las(mappar[0], "tar", lage)
            bas = _verklig(mappar[0], lage.projekt)
        if not operander:
            raise _Stopp("tar -c: ange vad som ska packas ihop.")
        for operand in operander:
            _las(operand, "tar", lage, bas)
    elif lage_tar == "x":
        _las(arkiv, "tar", lage)
        if not mappar:
            raise _Stopp(
                "tar -x måste ha -C med en tillfällig mapp, annars packas filerna upp i projektet (SPEC 7.1)."
            )
        _mal(mappar[0], "tar", lage)
    else:
        _las(arkiv, "tar", lage)


# ---------------------------------------------------------------------------------------------
# Programmet

def main():
    try:
        indata = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        fel = FORSTA + (
            "vakten fick indata som den inte kan läsa (det är inte JSON i UTF-8). Kommandot stoppas för "
            "säkerhets skull."
        )
    else:
        try:
            fel = bedom(indata, os.environ.get("CLAUDE_PROJECT_DIR"), pwd.getpwuid(os.getuid()).pw_dir)
        except Exception as undantag:
            fel = FORSTA + (
                f"vakten råkade ut för ett oväntat fel ({type(undantag).__name__}). Kommandot stoppas för "
                "säkerhets skull."
            )
    if fel is None:
        return 0
    sys.stderr.buffer.write((fel + "\n").encode("utf-8"))
    sys.stderr.buffer.flush()
    return 2


if __name__ == "__main__":
    try:
        kod = main()
    except BaseException:
        kod = 2
    sys.exit(kod)
