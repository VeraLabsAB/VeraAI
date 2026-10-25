"""I1: ingen kärnfil får använda en genväg förbi inläsningens kontroller.

En genväg är en funktion som läser en fil men hoppar över en kontroll:

- las_bank._tolka_rader hoppar över K1 (saldokedjan),
- las_kassa._tolka_kassarader hoppar över Z-kontroll a–e,
- byggstenarna i inlasning_skydd.py (las_fil, avkoda, csv_rader, rubrikens_falt m.fl.) gör en sak
  var och måste anropas i rätt ordning. Ensamma hoppar de över de andra skydden.

All annan kod ska läsa filer med las_bankfil och las_kassafil, som alltid kör alla kontroller.
Bara inläsningsmodulerna själva (UNDANTAGNA) och testerna får använda genvägarna. En ny
inläsningsmodul (till exempel för kvitton) måste läggas till i UNDANTAGNA med flit.

Kontrollen läser koden med Pythons ast-modul, alltså som Python själv ser den, och inte som text.
Den klarar därför alias (import ... as, x = las_bank) och kod som bygger ihop namn medan
programmet kör (getattr med hopsatt text, G8 punkt 5). Den kan inte bevisa att ingen genväg
finns: den som medvetet skriver kod för att lura den kan alltid lyckas i Python. Den stoppar
misstag och de enkla sätten att lura den.
"""

import ast
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]

# Filer i scripts/ som får använda genvägarna: inläsningsmodulerna själva.
UNDANTAGNA = ("las_bank.py", "las_kassa.py", "inlasning_skydd.py")
SKYDDSMODUL = "inlasning_skydd"
INLASNINGSMODULER = ("las_bank", "las_kassa")
GENVAGAR = ("_tolka_rader", "_tolka_kassarader")

# Sätt att nå ett namn som byggs ihop medan programmet kör. Ett sådant namn går inte att granska i
# koden, så det får inte användas i kärnan alls. Först fristående namn och moduler, sedan
# attribut (till exempel sys.modules och las_bank.__dict__).
DYNAMISKA_NAMN = ("__import__", "eval", "exec", "compile", "globals", "locals", "vars", "importlib",
                  "builtins", "__builtins__")
DYNAMISKA_ATTRIBUT = ("__dict__", "__getattribute__", "modules", "import_module", "__import__")
# Funktioner som slår upp ett namn ur en text. Texten måste vara skriven rakt ut, så att den
# kan jämföras med de förbjudna namnen.
NAMNUPPSLAG = ("getattr", "hasattr", "setattr", "delattr", "attrgetter", "methodcaller")


def toppnamn(fil):
    """Namn som filen själv binder på översta nivån: funktioner, klasser och tilldelningar."""
    namn = set()
    for nod in ast.parse(fil.read_text(encoding="utf-8")).body:
        if isinstance(nod, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            namn.add(nod.name)
        elif isinstance(nod, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            mal = nod.targets if isinstance(nod, ast.Assign) else [nod.target]
            namn.update(n.id for m in mal for n in ast.walk(m) if isinstance(n, ast.Name))
    return namn


def namn_som_leder_till_genvagar(inlasningsmodul, forbjudna):
    """Namn i en inläsningsmodul som pekar på en genväg: importerade byggstenar och alias.

    Till exempel ger "from inlasning_skydd import csv_rader as rader" namnet rader, och
    "TOLKA = _tolka_rader" namnet TOLKA (G8 punkt 5). Upprepas tills inga nya namn tillkommer.
    """
    trad = ast.parse(inlasningsmodul.read_text(encoding="utf-8"))
    nya = set()
    for nod in ast.walk(trad):
        if isinstance(nod, ast.ImportFrom) and nod.module and nod.module.split(".")[-1] == SKYDDSMODUL:
            nya.update(alias.asname or alias.name for alias in nod.names)
        elif isinstance(nod, ast.Import):
            nya.update(alias.asname or alias.name.split(".")[0] for alias in nod.names
                       if SKYDDSMODUL in alias.name.split("."))
    while True:
        alla = forbjudna | nya
        for nod in trad.body:
            if isinstance(nod, ast.Assign) and any(
                    isinstance(n, (ast.Name, ast.Attribute)) and (getattr(n, "id", None) in alla
                                                                  or getattr(n, "attr", None) in alla)
                    for n in ast.walk(nod.value)):
                nya.update(m.id for m in nod.targets if isinstance(m, ast.Name))
        if forbjudna | nya == alla:
            return nya


def forbjudna_namn(mapp=SCRIPTS):
    """Alla namn som leder till en genväg: genvägarna, byggstenarna och deras alias."""
    forbjudna = set(GENVAGAR) | {SKYDDSMODUL} | toppnamn(mapp / (SKYDDSMODUL + ".py"))
    for modul in INLASNINGSMODULER:
        forbjudna |= namn_som_leder_till_genvagar(mapp / (modul + ".py"), forbjudna)
    return forbjudna


def karnfiler(mapp):
    """Alla .py-filer under mapp utom tests/ och de undantagna inläsningsmodulerna."""
    return sorted(
        fil for fil in mapp.rglob("*.py")
        if mapp / "tests" not in fil.parents and fil not in [mapp / namn for namn in UNDANTAGNA]
    )


def ar_text(nod):
    return isinstance(nod, ast.Constant) and isinstance(nod.value, str)


def genvagar_i_fil(fil, forbjudna):
    """Lista med (radnummer, varför) för varje ställe i filen som använder en genväg."""
    try:
        trad = ast.parse(fil.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError, UnicodeDecodeError) as fel:
        return [(0, "filen går inte att läsa som Python och kan därför inte kontrolleras (" + str(fel) + ")")]

    anropade = {id(nod.func) for nod in ast.walk(trad) if isinstance(nod, ast.Call)}
    fynd = []
    for nod in ast.walk(trad):
        rad = getattr(nod, "lineno", 0)
        if isinstance(nod, ast.Import):
            for alias in nod.names:
                if SKYDDSMODUL in alias.name.split("."):
                    fynd.append((rad, "importerar " + SKYDDSMODUL))
                if alias.name.split(".")[0] in DYNAMISKA_NAMN:
                    fynd.append((rad, "importerar " + alias.name + ", som kan nå vilka namn som helst"))
        elif isinstance(nod, ast.ImportFrom):
            moduldelar = (nod.module or "").split(".")
            if SKYDDSMODUL in moduldelar:
                fynd.append((rad, "importerar från " + SKYDDSMODUL))
            if moduldelar[0] in DYNAMISKA_NAMN:
                fynd.append((rad, "importerar från " + nod.module + ", som kan nå vilka namn som helst"))
            for alias in nod.names:
                if alias.name in NAMNUPPSLAG:
                    fynd.append((rad, "importerar " + alias.name + ", så namnet den slår upp kan inte granskas"))
                if alias.name == SKYDDSMODUL:
                    fynd.append((rad, "importerar " + SKYDDSMODUL))
                elif moduldelar[-1] in INLASNINGSMODULER and alias.name == "*":
                    fynd.append((rad, "importerar allt från " + nod.module + ", även byggstenarna"))
                elif moduldelar[-1] in INLASNINGSMODULER and alias.name in forbjudna:
                    fynd.append((rad, "hämtar " + alias.name + " från " + nod.module))
        elif isinstance(nod, ast.Attribute):
            if nod.attr in forbjudna:
                fynd.append((rad, "använder ." + nod.attr))
            elif nod.attr in DYNAMISKA_ATTRIBUT:
                fynd.append((rad, "använder ." + nod.attr + ", som kan nå vilka namn som helst"))
            elif nod.attr in NAMNUPPSLAG and id(nod) not in anropade:
                fynd.append((rad, "använder ." + nod.attr + " utan att anropa den, så namnet kan inte granskas"))
        elif isinstance(nod, ast.Name):
            if nod.id in DYNAMISKA_NAMN:
                fynd.append((rad, "använder " + nod.id + ", som kan nå vilka namn som helst"))
            elif nod.id in NAMNUPPSLAG and id(nod) not in anropade:
                fynd.append((rad, "använder " + nod.id + " utan att anropa den, så namnet kan inte granskas"))
        elif ar_text(nod) and nod.value in forbjudna:
            fynd.append((rad, "har texten " + repr(nod.value) + ", som kan användas för att nå genvägen"))

        if isinstance(nod, ast.Call):
            funktion = nod.func.id if isinstance(nod.func, ast.Name) else getattr(nod.func, "attr", None)
            if funktion in NAMNUPPSLAG:
                namnet = nod.args[1:2] if funktion in ("getattr", "hasattr", "setattr", "delattr") else nod.args
                if not namnet or not all(ar_text(arg) for arg in namnet) or nod.keywords:
                    fynd.append((rad, funktion + " med ett namn som inte är skrivet rakt ut som text"))
    return sorted(set(fynd))


def genvagar_i(mapp, forbjudna=None):
    """Alla ställen i kärnans filer under mapp som använder en genväg, som text för felmeddelandet."""
    forbjudna = forbjudna_namn() if forbjudna is None else forbjudna
    return [
        str(fil.relative_to(mapp)) + ":" + str(rad) + " " + varfor
        for fil in karnfiler(mapp) for rad, varfor in genvagar_i_fil(fil, forbjudna)
    ]


# --- Kärnan i dag ---

def test_i1_ingen_karnfil_anvander_en_genvag():
    assert SCRIPTS / "belopp.py" in karnfiler(SCRIPTS)  # skydd mot att testet inte hittar några filer alls
    fynd = genvagar_i(SCRIPTS)
    assert not fynd, ("Kärnfiler som går förbi inläsningens kontroller (läs filer med las_bankfil och "
                      "las_kassafil i stället):\n" + "\n".join(fynd))


def test_i1_de_undantagna_filerna_finns():
    # Skydd: byter en inläsningsmodul namn ska undantaget inte ligga kvar och släppa igenom en ny fil.
    for namn in UNDANTAGNA:
        assert (SCRIPTS / namn).exists(), namn


def test_i1_de_forbjudna_namnen_hittas():
    # Skydd: listan med förbjudna namn byggs från koden. Den ska verkligen innehålla genvägarna,
    # byggstenarna och kassans importerade konstanter.
    forbjudna = forbjudna_namn()
    for namn in ["_tolka_rader", "_tolka_kassarader", "inlasning_skydd", "las_fil", "avkoda", "csv_rader",
                 "rubrikens_falt", "inga_otillatna_tecken", "nul_fel", "csv_fel", "ladda_json",
                 "kontrollera_namn", "tolka_datum", "tolka_ore", "Filsort", "OTILLATNA_TECKEN",
                 "TILLATNA_AVGRANSARE", "HELTAL", "RADBRYTNINGAR"]:
        assert namn in forbjudna, namn
    # Det som annan kod ska använda är inte förbjudet.
    for namn in ["las_bankfil", "las_kassafil", "ladda_bankformat", "ladda_kassaformat", "kontrollera_k1",
                 "kontrollera_z_serien", "summa_per_momssats", "kronor", "BankfilFel", "KassafilFel"]:
        assert namn not in forbjudna, namn


# --- Skydd: kontrollen slår verkligen larm ---

@pytest.fixture
def projekt(tmp_path):
    """En påhittad scripts-mapp där genvägarna finns i de undantagna filerna och i testerna."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "import inlasning_skydd\nfrom las_bank import _tolka_rader, csv_rader\n"
        "from las_kassa import _tolka_kassarader\n", encoding="utf-8")
    (tmp_path / "las_bank.py").write_text(
        "from inlasning_skydd import avkoda, csv_rader\ndef _tolka_rader(data, bankformat): ...\n", encoding="utf-8")
    (tmp_path / "las_kassa.py").write_text(
        "from inlasning_skydd import las_fil\ndef _tolka_kassarader(data, kassaformat): ...\n", encoding="utf-8")
    (tmp_path / "inlasning_skydd.py").write_text("def las_fil(sokvag, filsort): ...\n", encoding="utf-8")
    (tmp_path / "belopp.py").write_text("def tolka_belopp(text): ...\n", encoding="utf-8")
    return tmp_path


def test_i1_undantagen_och_testerna_far_anvanda_genvagarna(projekt):
    assert genvagar_i(projekt) == []


GENVAGSKOD = {
    # Kassans genväg (hoppar över Z-kontroll a–e)
    "kassans_genvag": "from las_kassa import _tolka_kassarader\n",
    "kassans_genvag_alias": "from las_kassa import _tolka_kassarader as tolka\n",
    "kassans_genvag_attribut": "import las_kassa\nrader = las_kassa._tolka_kassarader(b'', {})\n",
    "kassans_genvag_modulalias": "import las_kassa as k\nrader = k._tolka_kassarader(b'', {})\n",
    "kassans_genvag_tilldelad_modul": "import las_kassa\nk = las_kassa\nrader = k._tolka_kassarader(b'', {})\n",
    "kassans_genvag_getattr_text": "import las_kassa\nf = getattr(las_kassa, '_tolka_kassarader')\n",
    "kassans_genvag_getattr_hopsatt": "import las_kassa\nf = getattr(las_kassa, '_tolka_' + 'kassarader')\n",
    "kassans_genvag_getattr_variabel": "import las_kassa\nn = '_tolka_' 'kassarader'\nf = getattr(las_kassa, n)\n",
    "kassans_genvag_paketnamn": "from scripts.las_kassa import _tolka_kassarader\n",
    "kassans_genvag_relativ": "from .las_kassa import _tolka_kassarader\n",
    # Bankens genväg (hoppar över K1)
    "bankens_genvag": "from las_bank import _tolka_rader\n",
    "bankens_genvag_attribut": "import las_bank\nrader = las_bank._tolka_rader(b'', {})\n",
    "bankens_genvag_getattr_hopsatt": "import las_bank\nf = getattr(las_bank, '_tolka_' + 'rader')\n",
    "bankens_genvag_getattr_fstrang": "import las_bank\ndel_ = 'rader'\nf = getattr(las_bank, f'_tolka_{del_}')\n",
    "bankens_genvag_getattr_join": "import las_bank\nf = getattr(las_bank, ''.join(['_tolka', '_rader']))\n",
    "bankens_genvag_getattr_nyckelord": "import las_bank\nf = getattr(las_bank, *['_tolka_rader'])\n",
    "bankens_genvag_hasattr": "import las_bank\nhasattr(las_bank, '_tolka' + '_rader')\n",
    "bankens_genvag_attrgetter": "import operator, las_bank\nf = operator.attrgetter('_tolka' + '_rader')(las_bank)\n",
    "bankens_genvag_vars": "import las_bank\nf = vars(las_bank)['_tolka' + '_rader']\n",
    "bankens_genvag_dict": "import las_bank\nf = las_bank.__dict__['_tolka' + '_rader']\n",
    # Byggstenarna direkt ur inlasning_skydd
    "skyddsmodulen_import": "import inlasning_skydd\n",
    "skyddsmodulen_import_alias": "import inlasning_skydd as s\n",
    "skyddsmodulen_from": "from inlasning_skydd import las_fil, avkoda, csv_rader\n",
    "skyddsmodulen_from_ett_namn": "from inlasning_skydd import rubrikens_falt\n",
    "skyddsmodulen_paketnamn": "import scripts.inlasning_skydd\n",
    "skyddsmodulen_relativ": "from . import inlasning_skydd\n",
    "skyddsmodulen_relativ_from": "from .inlasning_skydd import csv_rader\n",
    "skyddsmodulen_i_funktion": "def f():\n    from inlasning_skydd import avkoda\n    return avkoda\n",
    # Byggstenarna via las_bank och las_kassa
    "byggsten_via_bank": "from las_bank import csv_rader, las_fil, avkoda\n",
    "byggsten_via_kassa": "from las_kassa import rubrikens_falt\n",
    "byggsten_via_kassa_konstant": "from las_kassa import HELTAL\n",
    "byggsten_via_bank_attribut": "import las_bank\nrader = las_bank.csv_rader([], 1, ',', 1, None)\n",
    "byggsten_via_kassa_alias": "import las_kassa as k\ntext = k.avkoda(b'', None)\n",
    "byggsten_via_bank_stjarna": "from las_bank import *\n",
    "skyddsmodulen_via_bank": "import las_bank\ns = las_bank.inlasning_skydd\n",
    "byggsten_getattr_text": "import las_bank\nf = getattr(las_bank, 'csv_rader')\n",
    "byggsten_getattr_hopsatt": "import las_kassa\nf = getattr(las_kassa, 'csv_' + 'rader')\n",
    # Dynamisk import, som kan nå vilken modul som helst med hopsatt text
    "dunder_import": "s = __import__('inlasning' + '_skydd')\n",
    "importlib": "import importlib\ns = importlib.import_module('inlasning' + '_skydd')\n",
    "importlib_from": "from importlib import import_module\ns = import_module('inlasning' + '_skydd')\n",
    "sys_modules": "import sys\ns = sys.modules['inlasning' + '_skydd']\n",
    "eval": "f = eval('las_bank.' + '_tolka_rader')\n",
    "exec": "exec('from las_bank import ' + '_tolka_rader')\n",
    "globals": "f = globals()['_tolka' + '_rader']\n",
    "builtins": "import builtins\nf = builtins.getattr\n",
    "builtins_alias": "import builtins as b, las_bank\nf = b.vars(las_bank)['_tolka' + '_rader']\n",
    "importlib_alias": "import importlib.util as u\nspec = u.find_spec('inlasning' + '_skydd')\n",
    "getattr_som_varde": "import las_bank\ng = getattr\nf = g(las_bank, '_tolka' + '_rader')\n",
    "attrgetter_som_varde": "import las_bank\nfrom operator import attrgetter as a\nf = [a][0]('_tolka' + '_rader')\n",
    "trasig_fil": "def f(:\n",
}


@pytest.mark.parametrize("kod", GENVAGSKOD.values(), ids=GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_en_fil_som_anvander_en_genvag(projekt, kod):
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


def test_i1_kontrollen_hittar_en_genvag_i_en_undermapp(projekt):
    (projekt / "matchning").mkdir()
    (projekt / "matchning" / "las_bank.py").write_text("from las_kassa import _tolka_kassarader\n", encoding="utf-8")
    assert genvagar_i(projekt) == ["matchning/las_bank.py:1 hämtar _tolka_kassarader från las_kassa"]


def test_i1_kontrollen_hittar_alias_i_en_inlasningsmodul(projekt):
    # G8 punkt 5: ett alias i las_bank.py (TOLKA = _tolka_rader) som en annan fil sedan använder.
    (projekt / "las_bank.py").write_text(
        "from inlasning_skydd import csv_rader as rader\ndef _tolka_rader(data, bankformat): ...\n"
        "TOLKA = _tolka_rader\nOCKSA = TOLKA\nRADER = rader\n", encoding="utf-8")
    forbjudna = forbjudna_namn(projekt)
    assert {"TOLKA", "OCKSA", "rader", "RADER"} <= forbjudna
    for kod in ["from las_bank import TOLKA\n", "import las_bank\nf = las_bank.OCKSA\n",
                "from las_bank import RADER\n", "import las_bank\nf = las_bank.rader\n"]:
        (projekt / "rapport.py").write_text(kod, encoding="utf-8")
        assert genvagar_i(projekt, forbjudna), kod


VANLIG_KOD = {
    "las_bankfil": "from las_bank import las_bankfil, ladda_bankformat, kronor, BankfilFel\n",
    "las_kassafil": "import las_kassa\nrader = las_kassa.las_kassafil('x.csv', {})\n"
                    "summor = las_kassa.summa_per_momssats([rader])\n",
    "modulalias": "import las_kassa as k\nk.kontrollera_z_serien([])\n",
    "getattr_med_vanlig_text": "f = getattr(object(), 'namn', None)\n",
    "beskrivning": '"""Läser bankfilen med las_bankfil, som använder inlasning_skydd och kör K1."""\n',
    "egen_funktion": "def tolka(rader):\n    return [rad for rad in rader]\n",
    "re_compile": "import re\nMONSTER = re.compile('x')\n",
}


@pytest.mark.parametrize("kod", VANLIG_KOD.values(), ids=VANLIG_KOD.keys())
def test_i1_vanlig_kod_slaps_igenom(projekt, kod):
    # Skydd: kontrollen får inte stoppa kod som läser filer på rätt sätt.
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    assert genvagar_i(projekt) == []
