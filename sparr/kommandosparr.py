"""Vakten för den fasta kommandolistan i SPEC 7.1 (granskning 11, Q1).

Claude Code kör vakten före varje verktyg som agenten använder (en hook av typen PreToolUse i de låsta
inställningarna, se managed-settings.json och INSTALLERA.md i samma mapp). Claude Code skickar en
beskrivning av verktyget som JSON på standard in. Vakten svarar på två sätt:

- kod 0 och ingen utskrift: vakten har inget att invända, och Claude Code frågar som vanligt,
- kod 2 och ett fel på svenska på standard fel: verktyget stoppas, och agenten ser felet.

Vakten godkänner aldrig något själv. Den kan bara stoppa.

Reglerna, i den ordning de prövas (planen i GRANSKNING.md, "Granskning 11 – plan för Q1"):

1. sudo och su stoppas alltid (Hugos beslut 2026-10-28, 5 och 7).
2. Bara verktygen på listan i SPEC 7.1 ("Tillåtna verktyg") släpps igenom. Allt annat stoppas, också
   verktyg som vakten inte känner till (granskning 12, P4, Hugos beslut 2026-10-28). Bash prövas
   vidare mot reglerna nedan. De andra verktygen på listan kör inga kommandon.
2 b. Verktygen som skriver eller ändrar filer (Write och Edit, och MultiEdit och NotebookEdit om de skulle stå på
   listan) får inte skriva där förbuden i managed-settings.json säger, och sökvägen jämförs utan hänsyn till stora
   och små bokstäver (granskning 17, H6, Hugos beslut 2026-10-28). Sökvägen prövas som den står, med ~ som
   hemmappen, efter ../ och dit länkarna leder, och med macOS andra namn för samma mapp (till exempel
   /private/etc för /etc). En sökväg vars första del direkt under roten börjar med punkt (till exempel /.vol och
   /.nofollow) stoppas alltid, också i kommandon (granskning 18, I1, Hugos beslut 2026-10-28).
3. Ingen mapp undantas (Hugos beslut 8). Kommandot ska köras i mappen där sessionen startade
   (CLAUDE_PROJECT_DIR), och den mappen får inte vara hemmappen eller en mapp ovanför den. Där vakten stoppar
   jämförs sökvägar utan hänsyn till stora och små bokstäver, och där den släpper igenom jämförs de exakt
   (granskning 17, H6).
4. Inga ihopkopplade kommandon: inget ;, &, |, <, >, $, bakåtfnutt, omvänt snedstreck eller
   radbrytning, inte heller inom citattecken. Inga osynliga eller styrande tecken. Inga tecken som
   skalet byter ut mot något annat (jokertecken, ~ och liknande) utanför citattecken.
5. Första ordet ska stå på listan i SPEC 7.1.
6. Reglerna under listan: mål bara i den tillfälliga mappen, ingen fil eller mapp som heter .ugrep
   (granskning 16, G7, Hugos beslut 2026-10-28), inga mål eller källor till cp -R som förbuden för
   fil-verktygen gäller (regel 2 b), grep bara med tillägg som söker, pytest bara
   i de två formerna, inga git-tillägg som skriver filer eller kör program, och läsande kommandon bara i
   projektet och i den tillfälliga mappen. find står inte på listan (granskning 15, S1, Hugos beslut
   2026-10-28): i agentens skal är find Claude Codes bfs, som raderar med -rm.
7. PATH-regeln (Hugos beslut 2026-10-28, beslut 1). Kommandon som ändrar PATH stoppas (prövas före
   regel 5). Programmet som kommandot pekar på letas upp som skalet gör, i PATH från vaktens miljö, och
   filen och varje mapp ovanför den ska ägas av systemet (root) och inte gå att skriva i för gruppen
   eller andra. Det gäller både sökvägen som den står och dit länkarna leder (Hugos beslut 2026-10-28
   om vakten, beslut 3), och varje länk i kedjan däremellan, med mappen den ligger i (granskning 13, P2,
   Hugos beslut 2026-10-28). Samma krav gäller varje mapp i PATH före programmet, och en sådan mapp som
   inte finns stoppar också (beslut 2). Kan vakten inte säkert avgöra vilken fil som körs, stoppas
   kommandot. Regeln prövas sist.

Allt som vakten inte känner igen stoppas. Om vakten själv kraschar stoppas kommandot också, både här
(kod 2) och av Claude Code (inställningen "onFailure": "block").

Vakten körs med Python i Apples utvecklarverktyg, med hela sökvägen
(/Library/Developer/CommandLineTools/usr/bin/python3 -I, granskning 19, J1, Hugos beslut 2026-10-28), och
använder bara Pythons egna delar. Den ska fungera med Python 3.9. -I gör att Python inte läser in filer från
vaktens mapp, arbetsmappen eller inställningar i miljön.
"""

from __future__ import annotations

import json
import os
import pwd
import sys
import unicodedata

FORSTA = "Stoppat av vakten: "

SUDO_OCH_SU = ("sudo", "su")

# Regel 2: listan i SPEC 7.1, "Tillåtna verktyg", i samma ordning. Namnen jämförs exakt.
TILLATNA_VERKTYG = (
    "Bash",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "AskUserQuestion",
    "WebFetch",
    "ToolSearch",
    "Skill",
    "Agent",
    "mcp__ccd_turn__update_plan",
    "mcp__ccd_turn__wrap_up",
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

# Regel 5 och 6: listan i SPEC 7.1. Projektets Python med pytest ligger i en mapp som root äger, bredvid
# vakten (Hugos beslut 2026-10-28 om vakten, beslut 1). I kommandot står sökvägen inom citattecken.
PYTHON = "/Library/Application Support/ClaudeCode/vera/venv/bin/python"
PYTEST_FAST = ["-B", "-m", "pytest", "-p", "no:cacheprovider"]
PYTEST_PROJEKTET = os.path.join("scripts", "tests")
PYTEST_TB = ("auto", "long", "short", "line", "native", "no")

LASANDE = ("ls", "cat", "head", "tail", "grep", "diff", "wc", "sort")
LASANDE_FORBJUDNA_KORTA = {"sort": "oT"}
LASANDE_FORBJUDNA_LANGA = {
    "sort": ("output", "compress-program", "temporary-directory"),
}
# grep (granskning 15, S1, Hugos beslut 2026-10-28): i agentens skal är grep Claude Codes ugrep, som har
# tillägg som kör program och skriver filer. Bara tillägg som söker släpps igenom, och namnen jämförs exakt.
# Korta tillägg utan värde, korta tillägg som tar ett värde, långa tillägg utan värde, långa tillägg som tar
# ett tal efter =, och långa tillägg som tar ett filmönster efter = (prövas som en sökväg). -R står inte med
# (granskning 16, G3, Hugos beslut 2026-10-28): i ugrep följer det alla länkar inne i mappar, också ut ur
# projektet. Den långa formen (--dereference-recursive) står inte heller med.
GREP_KORTA = "nirlLcvwxEFHhosqI"
GREP_KORTA_VARDE = "eABCm"
GREP_KORTA_TAL = "ABCm"
GREP_LANGA = (
    "line-number",
    "ignore-case",
    "recursive",
    "files-with-matches",
    "files-without-match",
    "count",
    "invert-match",
    "word-regexp",
    "line-regexp",
    "extended-regexp",
    "fixed-strings",
    "with-filename",
    "no-filename",
    "only-matching",
    "no-messages",
    "quiet",
    "silent",
)
GREP_LANGA_TAL = ("after-context", "before-context", "context", "max-count")
GREP_LANGA_MONSTER = ("include", "exclude", "exclude-dir")
GREP_TILLATNA = (
    "-n, -i, -r, -l, -L, -c, -v, -w, -x, -E, -F, -H, -h, -o, -s, -q, -I, -e med ett mönster, -A, -B, -C "
    "och -m med ett tal, motsvarande långa namn, och --include=, --exclude= och --exclude-dir="
)

# ugreps inställningsfil (granskning 16, G7, Hugos beslut 2026-10-28). Den kan sätta tillägg som kör andra
# program, och vakten ser den inte. Inget kommando får skriva en fil eller mapp med det namnet, i någon mapp.
# Namnet jämförs utan hänsyn till stora och små bokstäver, eftersom macOS i regel inte skiljer på dem.
UGREP_FIL = ".ugrep"

# Regel 2 b (granskning 17, H6, Hugos beslut 2026-10-28). Verktygen som skriver eller ändrar filer, och fältet där
# sökvägen står. MultiEdit och NotebookEdit står inte på listan i SPEC 7.1 och stoppas av regel 2, men står här
# också, om listan ändras.
SKRIVVERKTYG = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
# Förbuden för fil-verktygen i managed-settings.json (Edit(...)), i samma ordning. Ett test jämför dem. // är datorns
# rot och ~/ hemmappen. ** står för valfritt antal mappar (sist i ett förbud minst en), och * för vad som helst inom
# ett namn.
SKRIVFORBUD = (
    "//**/.git/**",
    "//**/.git",
    "//**/.ugrep",
    "~/.ugrep",
    "~/.zshrc",
    "~/.zshenv",
    "~/.zprofile",
    "~/.zlogin",
    "~/.zlogout",
    "//etc/zshenv",
    "//etc/zprofile",
    "//etc/zshrc",
    "//etc/zshrc_*",
    "//etc/zlogin",
    "//etc/zlogout",
    "~/.zshrc.zwc",
    "~/.zshenv.zwc",
    "~/.zprofile.zwc",
    "~/.zlogin.zwc",
    "~/.zlogout.zwc",
    "//etc/zshenv.zwc",
    "//etc/zprofile.zwc",
    "//etc/zshrc.zwc",
    "//etc/zlogin.zwc",
    "//etc/zlogout.zwc",
    "~/.nvm/**",
    "~/.zkbd/**",
    "~/.zsh_sessions/**",
    "~/.zcompdump",
    "~/.zcompdump*",
    "~/.zcompdump.zwc",
    "~/.bashrc",
    "~/.bash_profile",
    "~/.profile",
    "~/.gitconfig",
    "~/.config/git/**",
    "~/.claude/**",
    "~/Library/LaunchAgents/**",
    "~/.ssh/**",
    "//**/.mcp.json",
    "//**/.claude/**",
    "~/.claude.json",
    "~/bin/**",
    "~/.local/bin/**",
    "~/.local/bin/claude",
    "~/.local/share/claude/**",
    "~/Library/Application Support/Claude/claude-code/**",
    "~/Library/Application Support/Claude/**",
    "//Applications/Claude.app/**",
    "//opt/homebrew/**",
    "//**/.venv/**",
)
# macOS har flera namn för samma mapp: /etc, /tmp och /var är länkar till mappar i /private, och hela datavolymen
# (där bland annat hemmappen ligger) syns också under /System/Volumes/Data. Sökvägen prövas med varje namn, bara
# som text.
MACOS_ANDRA_NAMN = (
    ("/System/Volumes/Data", ""),
    ("/private/etc", "/etc"),
    ("/private/tmp", "/tmp"),
    ("/private/var", "/var"),
)
# macOS har också namn direkt under roten som börjar med punkt, till exempel /.vol/<enhet>/<inode>/… och
# /.nofollow/<sökväg>, som leder till samma fil som den vanliga sökvägen utan att synas som länkar. Vakten kan inte
# räkna om dem, så varje sökväg vars första del under roten börjar med punkt stoppas (granskning 18, I1, Hugos
# beslut 2026-10-28).
PUNKT = "."

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

# Regel 7: PATH heter också path i zsh. Kommandon i skalet som sätter eller tar bort en variabel.
PATH_NAMN = ("PATH", "path")
SATTER_VARIABLER = ("export", "env", "typeset", "declare", "readonly", "local", "unset")
SKRIVBAR_FOR_GRUPP_ELLER_ANDRA = 0o022
# Granskning 13, P2: så många länkar följs som mest i en kedja, som i macOS (MAXSYMLINKS). En längre kedja
# stoppas.
MAX_LANKAR = 32

TILLATNA_KOMMANDON = (
    f"'{PYTHON}' (bara pytest), git, ls, cat, head, tail, grep, diff, wc, sort, mkdir, cp -R och tar"
)


class _Stopp(Exception):
    pass


class _Lage:
    def __init__(self, projekt, tillfallig, hem):
        self.projekt = projekt
        self.tillfallig = tillfallig
        self.hem = hem


def bedom(indata, projektmapp, hemmapp, sokvag):
    """Bedömer ett verktyg. Returnerar None om vakten inte invänder, annars felet på svenska.

    sokvag är PATH, som avgör vilket program ett kommando utan / pekar på (regel 7).
    """
    try:
        _bedom(indata, projektmapp, hemmapp, sokvag)
    except _Stopp as stopp:
        return FORSTA + str(stopp)
    return None


def _bedom(indata, projektmapp, hemmapp, sokvag):
    if not isinstance(indata, dict):
        _indatafel("det är inte ett JSON-objekt")
    verktyg = indata.get("tool_name")
    if not isinstance(verktyg, str):
        _indatafel("verktygets namn saknas")
    verktygsdata = indata.get("tool_input")

    # Regel 1.
    if isinstance(verktygsdata, dict) and isinstance(verktygsdata.get("command"), str):
        _sudo_och_su(verktygsdata["command"])

    # Regel 2.
    if verktyg not in TILLATNA_VERKTYG:
        raise _Stopp(
            f"verktyget '{verktyg}' står inte på listan över tillåtna verktyg i SPEC 7.1 och är stoppat. "
            "Bara Bash får köra kommandon, och bara de som står i SPEC 7.1."
        )

    # Regel 2 b.
    if verktyg in SKRIVVERKTYG:
        _skrivverktyg(verktyg, verktygsdata, indata.get("cwd"), projektmapp, hemmapp)
    if verktyg != "Bash":
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

    # Regel 7, första delen: kommandon som ändrar PATH.
    _andrar_path(ordlista)

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

    # Regel 7, andra delen: var programmet ligger. Prövas sist.
    _programmet(forsta, lage, sokvag)


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
    if _inom_oavsett_bokstaver(hem, projekt):
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
        if not (
            _inom_oavsett_bokstaver(mapp, projekt)
            or _inom_oavsett_bokstaver(projekt, mapp)
            or _inom_oavsett_bokstaver(hem, mapp)
        ):
            godkand = mapp
    return _Lage(projekt, godkand, hemmapp)


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


def _jamforbar(text):
    """Texten som macOS jämför namn: utan hänsyn till stora och små bokstäver, och med é skrivet som ett tecken
    eller som e med accent lika (granskning 17, H6)."""
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", text).casefold())


def _inom_oavsett_bokstaver(sokvag, rot):
    """Som _inom, men utan hänsyn till stora och små bokstäver. Används bara där vakten stoppar."""
    return _inom(_jamforbar(sokvag), _jamforbar(rot))


# ---------------------------------------------------------------------------------------------
# Regel 2 b: förbuden för fil-verktygen (granskning 17, H6, Hugos beslut 2026-10-28)

def _delar(sokvag):
    return [_jamforbar(del_) for del_ in sokvag.split("/") if del_ and del_ != "."]


def _passar_namn(namn, monster):
    """Sant om namnet passar mönstret, där * står för vad som helst (också ingenting) inom ett namn."""
    bitar = monster.split("*")
    if len(bitar) == 1:
        return namn == monster
    forst, sist = bitar[0], bitar[-1]
    if len(namn) < len(forst) + len(sist) or not (namn.startswith(forst) and namn.endswith(sist)):
        return False
    plats, slut = len(forst), len(namn) - len(sist)
    for bit in bitar[1:-1]:
        hittad = namn.find(bit, plats, slut)
        if hittad < 0:
            return False
        plats = hittad + len(bit)
    return True


def _passar(delar, monster):
    """Sant om sökvägens delar passar förbudets delar. ** står för valfritt antal mappar, och sist i förbudet för
    minst en (allt i mappen, men inte mappen själv)."""
    if not monster:
        return not delar
    if monster[0] == "**":
        minst = 1 if len(monster) == 1 else 0
        return any(_passar(delar[i:], monster[1:]) for i in range(minst, len(delar) + 1))
    return bool(delar) and _passar_namn(delar[0], monster[0]) and _passar(delar[1:], monster[1:])


def _andra_namn(sokvag):
    """Sökvägen efter ../ och ./ (bara som text), och med macOS andra namn för samma mapp."""
    former = [os.path.normpath(sokvag)]
    for form in former:
        for langt, kort in MACOS_ANDRA_NAMN:
            if _jamforbar(form).startswith(_jamforbar(langt) + "/"):
                ny = kort + form[len(langt):]
                if ny not in former:
                    former.append(ny)
    return former


def _forbud_som_passar(former, hemmar):
    """Det första förbudet som någon av sökvägens former passar, annars None. Bara text: ingen fil läses."""
    for regel in SKRIVFORBUD:
        if regel.startswith("//"):
            baser = ["/"]
        elif regel.startswith("~/"):
            baser = hemmar
        else:
            return regel
        for bas in baser:
            monster = _delar(bas) + _delar(regel[2:])
            if any(_passar(_delar(form), monster) for form in former):
                return regel
    return None


def _former(sokvag, baser, hem):
    """Sökvägens former: som den står och med ~ som hemmappen, i förhållande till varje mapp i baser om den inte
    börjar med /, och både som text och dit länkarna leder."""
    tolkningar = [sokvag]
    if sokvag == "~" or sokvag.startswith("~/"):
        tolkningar.append(hem + sokvag[1:])
    former = []
    for tolkning in tolkningar:
        hela = [tolkning] if os.path.isabs(tolkning) else [os.path.join(bas, tolkning) for bas in baser]
        for sok in hela:
            former += _andra_namn(sok) + _andra_namn(os.path.realpath(sok))
    return former


def _forbud_for(sokvag, baser, hem):
    """Förbudet som någon av sökvägens former passar, eller None."""
    return _forbud_som_passar(_former(sokvag, baser, hem), [hem, os.path.realpath(hem)])


def _punkt_under_roten(sokvag, etikett, baser, hem):
    """Stoppar sökvägen om första delen direkt under roten börjar med punkt i någon av sökvägens former, före och
    efter att den har räknats om (granskning 18, I1, Hugos beslut 2026-10-28)."""
    for form in _former(sokvag, baser, hem):
        delar = [del_ for del_ in form.split("/") if del_ and del_ != "."]
        if os.path.isabs(form) and delar and delar[0].startswith(PUNKT):
            raise _Stopp(
                f"{etikett}: '{sokvag}' leder till '/{delar[0]}', en mapp direkt under roten vars namn börjar med "
                "punkt. macOS har sådana namn (till exempel /.vol och /.nofollow) som leder till samma fil som en "
                "vanlig sökväg utan att synas som en länk, så sökvägen stoppas (granskning 18, I1, Hugos beslut "
                "2026-10-28)."
            )


def _forbjuden_text(sokvag, regel):
    return (
        f"'{sokvag}' är förbjuden för fil-verktygen (Edit({regel}) i de låsta inställningarna), också skriven med "
        "andra stora och små bokstäver, med ../, ~ eller via en länk (granskning 17, H6, Hugos beslut 2026-10-28)."
    )


def _skrivverktyg(verktyg, verktygsdata, cwd, projektmapp, hemmapp):
    falt = SKRIVVERKTYG[verktyg]
    if not isinstance(verktygsdata, dict):
        _indatafel("tool_input saknas")
    sokvag = verktygsdata.get(falt)
    if not isinstance(sokvag, str) or not sokvag or "\x00" in sokvag:
        _indatafel(f"sökvägen ({falt}) saknas, är inte text eller har ett NUL-tecken")
    baser = [bas for bas in (cwd, projektmapp) if isinstance(bas, str) and bas]
    if not baser and not os.path.isabs(sokvag):
        _indatafel("sökvägen är inte hel, och mappen den gäller (cwd) saknas")
    regel = _forbud_for(sokvag, baser, hemmapp)
    if regel:
        raise _Stopp(f"{verktyg}: {_forbjuden_text(sokvag, regel)}")
    _punkt_under_roten(sokvag, verktyg, baser, hemmapp)


def _skrivforbud_kommando(sokvag, etikett, lage):
    regel = _forbud_for(sokvag, [lage.projekt], lage.hem)
    if regel:
        raise _Stopp(f"{etikett}: {_forbjuden_text(sokvag, regel)}")
    _punkt_under_roten(sokvag, etikett, [lage.projekt], lage.hem)


def _verklig(sokvag, bas):
    if not os.path.isabs(sokvag):
        sokvag = os.path.join(bas, sokvag)
    return os.path.realpath(sokvag)


def _las(sokvag, etikett, lage, bas=None):
    _punkt_under_roten(sokvag, etikett, [bas or lage.projekt], lage.hem)
    verklig = _verklig(sokvag, bas or lage.projekt)
    if _inom(verklig, lage.projekt) or (lage.tillfallig and _inom(verklig, lage.tillfallig)):
        return
    raise _Stopp(
        f"{etikett}: sökvägen '{sokvag}' ligger utanför projektet och den tillfälliga mappen. Bara filer "
        "i projektet och kopior i den tillfälliga mappen får läsas (SPEC 7.1 och CLAUDE.md)."
    )


def _ugrep(sokvag, etikett, lage):
    """Stoppar en sökväg där någon del heter .ugrep, både som den står och dit länkarna leder."""
    for sok in (sokvag, _verklig(sokvag, lage.projekt)):
        if any(del_.casefold() == UGREP_FIL for del_ in sok.split("/")):
            raise _Stopp(
                f"{etikett}: '{sokvag}' skulle skriva en fil eller mapp som heter {UGREP_FIL}. Det är ugreps "
                "inställningsfil, som kan köra andra program, och den får inte skapas eller ändras i någon mapp "
                "(granskning 16, G7, Hugos beslut 2026-10-28)."
            )


def _mal(sokvag, etikett, lage):
    if sokvag:
        _ugrep(sokvag, etikett, lage)
        _skrivforbud_kommando(sokvag, etikett, lage)
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
# Regel 7: PATH-regeln (Hugos beslut 2026-10-28, beslut 1)

def _path_namn(ord_):
    """Namnet på variabeln i PATH=..., PATH+=... eller PATH, annars None."""
    namn = ord_.split("=", 1)[0]
    if namn.endswith("+"):
        namn = namn[:-1]
    return namn if namn.isidentifier() else None


def _andrar_path(ordlista):
    andrar = False
    # Ord först i kommandot som ser ut som NAMN=värde sätter en variabel för kommandot.
    for ord_ in ordlista:
        if "=" not in ord_ or _path_namn(ord_) is None:
            break
        if _path_namn(ord_) in PATH_NAMN:
            andrar = True
    if ordlista[0] in SATTER_VARIABLER and any(_path_namn(o) in PATH_NAMN for o in ordlista[1:]):
        andrar = True
    if andrar:
        raise _Stopp(
            "kommandon som ändrar PATH stoppas, eftersom PATH avgör vilket program ett kommando kör "
            "(PATH-regeln, Hugos beslut 2026-10-28)."
        )


def _osaker(namn, detalj):
    raise _Stopp(
        f"vakten kan inte säkert avgöra vilken fil som körs för '{namn}' ({detalj}). Kommandot stoppas för "
        "säkerhets skull (PATH-regeln, Hugos beslut 2026-10-28)."
    )


def _kan_koras(fil):
    return os.path.isfile(fil) and os.access(fil, os.X_OK)


def _hitta_programmet(namn, lage, sokvag):
    """Filen som skalet kör för namn: som det står om namnet har ett /, annars första träffen i PATH."""
    if "/" in namn:
        fil = namn if os.path.isabs(namn) else os.path.join(lage.projekt, namn)
        if not _kan_koras(fil):
            _osaker(namn, f"{fil} finns inte eller går inte att köra")
        return fil
    if not isinstance(sokvag, str) or not sokvag:
        _osaker(namn, "PATH saknas")
    mappar = sokvag.split(":")
    for plats, mapp in enumerate(mappar):
        if not os.path.isabs(mapp):
            _osaker(namn, f"PATH har en mapp som inte är en hel sökväg, '{mapp}', före programmet")
        fil = os.path.join(mapp, namn)
        if _kan_koras(fil):
            _mapparna_fore(namn, mappar[:plats])
            return fil
    _osaker(namn, "programmet finns inte i någon mapp i PATH")


def _mapparna_fore(namn, mappar):
    """Varje mapp i PATH före programmet ska ägas säkert av systemet (Hugos beslut 2026-10-28 om vakten,
    beslut 2). Annars kan ett program med samma namn läggas där utan administratörslösenord, och om
    skalet har en annan PATH än vakten kan skalet hitta en annan fil än vakten prövade."""
    for mapp in mappar:
        if not _saker_plats(mapp):
            raise _Stopp(
                f"mappen {mapp} står före programmet i PATH för '{namn}', och den mappen, en länk på vägen "
                "dit eller en mapp ovanför dem finns inte, ägs inte av systemet (root) eller går att skriva i "
                "för någon annan än systemet. Ett program med samma namn kan läggas där utan administratörslösenord, så "
                "kommandot stoppas (PATH-regeln, Hugos beslut 2026-10-28 om vakten, beslut 2)."
            )


def _sakert_agd(sokvag):
    """Sant om sökvägen ägs av systemet (root) och varken gruppen, andra eller den som kör vakten kan
    skriva i den. os.access räknar också med extra rättigheter (ACL) för den som kör vakten."""
    try:
        info = os.stat(sokvag)
    except OSError:
        return False
    return (
        info.st_uid == 0
        and not info.st_mode & SKRIVBAR_FOR_GRUPP_ELLER_ANDRA
        and not os.access(sokvag, os.W_OK)
    )


def _saker_plats(fil):
    """Sant om filen (eller mappen) och varje mapp ovanför den ägs säkert av systemet, både för sökvägen
    som den står och för sökvägen dit länkarna leder (Hugos beslut 2026-10-28 om vakten, beslut 3), och
    för varje länk i kedjan däremellan (granskning 13, P2, Hugos beslut 2026-10-28)."""
    for sokvag in (os.path.normpath(fil), os.path.realpath(fil)):
        if not _sakert_agd(sokvag):
            return False
        mapp = os.path.dirname(sokvag)
        while True:
            if not _sakert_agd(mapp):
                return False
            if mapp == os.path.dirname(mapp):
                break
            mapp = os.path.dirname(mapp)
    return _saker_kedja(fil)


def _saker_kedja(fil):
    """Sant om varje mapp som datorn går igenom för att nå filen ägs säkert av systemet, och filen själv.

    Sökvägen följs en del i taget från /, som datorn själv gör. Varje länk på vägen (också en mapp som
    är en länk) följs för sig, så att varje länk i en kedja prövas, också en länk i mitten (granskning 13,
    P2, Hugos beslut 2026-10-28). En länk kan bara bytas ut av den som får skriva i mappen där länken
    ligger, och den mappen prövas. En kedja med fler än MAX_LANKAR länkar stoppas, liksom en länk som
    inte går att läsa."""
    delar = [del_ for del_ in fil.split("/") if del_]
    if not os.path.isabs(fil):
        delar = [del_ for del_ in os.getcwd().split("/") if del_] + delar
    mapp = "/"
    lankar = 0
    while delar:
        if not _sakert_agd(mapp):
            return False
        del_ = delar.pop(0)
        if del_ == ".":
            continue
        if del_ == "..":
            mapp = os.path.dirname(mapp)
            continue
        nasta = os.path.join(mapp, del_)
        if os.path.islink(nasta):
            lankar += 1
            if lankar > MAX_LANKAR:
                return False
            try:
                mal = os.readlink(nasta)
            except OSError:
                return False
            if os.path.isabs(mal):
                mapp = "/"
            delar[:0] = [d for d in mal.split("/") if d]
            continue
        mapp = nasta
    return _sakert_agd(mapp)


def _programmet(namn, lage, sokvag):
    fil = _hitta_programmet(namn, lage, sokvag)
    if _saker_plats(fil):
        return
    verklig = os.path.realpath(fil)
    lank = f" (länken leder till {verklig})" if verklig != os.path.normpath(fil) else ""
    raise _Stopp(
        f"programmet '{namn}' är {fil}{lank}, och filen, en länk på vägen dit eller en mapp ovanför dem ägs "
        "inte av systemet (root) eller går att skriva i för någon annan än systemet. Ett program där kan bytas ut utan "
        "administratörslösenord, så kommandot stoppas (PATH-regeln, Hugos beslut 2026-10-28)."
    )


# ---------------------------------------------------------------------------------------------
# Kommandona på listan

def _pytest(ordlista, lage):
    if ordlista[1:6] != PYTEST_FAST:
        raise _Stopp(
            f"pytest: Python får bara köras som \"'{PYTHON}' -B -m pytest -p no:cacheprovider\", följt "
            "av tillåtna tillägg och ett mål (SPEC 7.1)."
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
    _punkt_under_roten(mal[0], "pytest", [lage.projekt], lage.hem)
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
    if namn == "grep":
        _grep(ordlista, lage)
        return
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


def _grep_tillagg(tillagg):
    raise _Stopp(
        f"grep: tillägget '{tillagg}' är inte tillåtet. grep får bara söka (granskning 15, S1, Hugos beslut "
        f"2026-10-28). Tillåtna: {GREP_TILLATNA} (SPEC 7.1)."
    )


def _grep_tal(tillagg, varde):
    if not (varde.isascii() and varde.isdigit()):
        raise _Stopp(f"grep: tillägget '{tillagg}' ska följas av ett tal, inte '{varde}'.")


def _grep(ordlista, lage):
    """grep med bara de tillägg som söker. Allt annat stoppas, också tillägg som vakten inte känner till.
    Mönstret prövas som en sökväg, som förut (Hugos beslut 2026-10-28)."""
    argument = ordlista[1:]
    efter_streck = False
    i = 0
    while i < len(argument):
        ord_ = argument[i]
        if efter_streck or not ord_.startswith("-") or ord_ == "-":
            if ord_ != "-":
                _las(ord_, "grep", lage)
        elif ord_ == "--":
            efter_streck = True
        elif ord_.startswith("--"):
            tillagg, lika, varde = ord_[2:].partition("=")
            if tillagg in GREP_LANGA and not lika:
                pass
            elif tillagg in GREP_LANGA_TAL and lika:
                _grep_tal(ord_, varde)
            elif tillagg in GREP_LANGA_MONSTER and lika:
                _las(varde, "grep", lage)
            elif tillagg == "regexp" and lika:
                _las(varde, "grep", lage)
            else:
                _grep_tillagg(ord_)
        else:
            for j in range(1, len(ord_)):
                bokstav = ord_[j]
                if bokstav in GREP_KORTA:
                    continue
                if bokstav not in GREP_KORTA_VARDE:
                    _grep_tillagg(ord_)
                varde = ord_[j + 1:]
                if not varde:
                    i += 1
                    if i >= len(argument):
                        raise _Stopp(f"grep: tillägget '{ord_}' saknar ett värde.")
                    varde = argument[i]
                if bokstav in GREP_KORTA_TAL:
                    _grep_tal(ord_, varde)
                else:
                    _las(varde, "grep", lage)
                break
        i += 1


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
        # Kopian får samma namn som källan (granskning 16, G7, och granskning 17, H6).
        _ugrep(operand, "cp -R", lage)
        _skrivforbud_kommando(operand, "cp -R", lage)
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
            fel = bedom(
                indata,
                os.environ.get("CLAUDE_PROJECT_DIR"),
                pwd.getpwuid(os.getuid()).pw_dir,
                os.environ.get("PATH"),
            )
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
