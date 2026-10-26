"""I1: ingen kärnfil får använda en genväg förbi inläsningens kontroller.

En genväg är en funktion som läser en fil men hoppar över en kontroll:

- las_bank._tolka_rader hoppar över K1 (saldokedjan), och las_bank._PERIODNYCKEL skapar en Bankperiod
  med vilka rader som helst. Bankperiodens inre (_rader, _ingaende_saldo_ore, _utgaende_saldo_ore) är
  raderna och saldona som matchningen får,
- las_kassa._tolka_kassarader hoppar över Z-kontroll a–e,
- byggstenarna i inlasning_skydd.py (_las_fil, _avkoda, _csv_rader, _rubrikens_falt m.fl.) gör en sak
  var och måste anropas i rätt ordning. Ensamma hoppar de över de andra skydden. Alla deras namn
  börjar med understreck, så att de inte är en del av något offentligt gränssnitt,
- las_kassa._PERIODNYCKEL skapar en Kassaperiod med vilka rader som helst, utan Z-kontroll a–e och
  seriekontrollen, och Kassaperiodens inre (_rapporter m.fl.) är raderna som summeras,
- las_underlag._las_underlagsfil hoppar över kontrollen av dubbla id och K4 (dubbletter), och
  las_underlag._PERIODNYCKEL skapar en Underlagsperiod med vilka underlag som helst. Periodens inre
  (_underlag, _arenden) är underlagen och ärendena,
- las_kontoplan och las_momssatser: _kontrollera_konto, _kontrollera_period och de andra
  delkontrollerna gör var sin del av kontrollerna och hoppar över resten (till exempel överlapp och
  glapp mellan perioder). _KONTOPLANSNYCKEL och _MOMSNYCKEL skapar en Kontoplan eller Momssatser
  med vilket innehåll som helst, och deras inre (_konton, _roller, _varugrupper m.fl.) är det som
  uppslagen läser,
- las_regelbok: _kontrollera_regelboksregel, _kontrollera_villkor och de andra delkontrollerna gör
  var sin del av kontrollerna och hoppar över resten (till exempel tvetydiga regler och regler som
  höjer företagets gränser). _REGELBOKSNYCKEL skapar en Regelbok med vilket innehåll och vilken
  kontrollsumma som helst, och dess inre (_regelboken, _kontrollsumma) är det som uppslagen läser,
- konteringsforslag: alla namn i modulen som börjar med understreck är byggstenar. _kontrollera_k2,
  _kontrollera_ursprung och de andra delkontrollerna gör var sin del av kontrollerna och hoppar över
  resten. _FORSLAGSNYCKEL skapar ett Konteringsforslag med vilket innehåll som helst, och _FORSLAGEN
  är innehållet i alla förslag.

All annan kod ska läsa filer med las_bankfil, las_kassafil, las_kassaperiod,
las_underlagsperiod, las_kontoplan, las_momssatser och las_regelbok, som alltid kör alla kontroller, summera med summa_per_momssats, som bara
tar emot en Kassaperiod, matcha med matcha_period, som bara tar emot en Bankperiod, och skapa förslag med
skapa_konteringsforslag, som alltid kör K2 och ursprungskontrollen. Bara inläsningsmodulerna själva (UNDANTAGNA) och testerna får använda
genvägarna. En ny inläsningsmodul måste läggas till i UNDANTAGNA med flit. las_matchningsformat.py,
las_kontoplan.py, las_momssatser.py och las_regelbok.py läser JSON-format med de gemensamma skydden och är därför
inläsningsmoduler. matcha_bank.py och konteringsforslag.py
läser inga filer och är inte undantagna: förbudet gäller dem som alla andra kärnfiler.
konteringsforslag.py använder sina egna byggstenar bara som vanliga namn, aldrig som attribut eller
text, och klarar sig därför utan undantag.

Kontrollen läser koden med Pythons ast-modul, alltså som Python själv ser den, och inte som text.
Den klarar därför alias (import ... as, x = las_bank) och kod som bygger ihop namn medan
programmet kör (getattr med hopsatt text, G8 punkt 5). Den kan inte bevisa att ingen genväg
finns: den som medvetet skriver kod för att lura den kan alltid lyckas i Python. Den stoppar
misstag och de enkla sätten att lura den.
"""

import ast
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

# Filer i scripts/ som får använda genvägarna: inläsningsmodulerna själva.
UNDANTAGNA = ("las_bank.py", "las_kassa.py", "las_underlag.py", "las_matchningsformat.py", "las_kontoplan.py",
              "las_momssatser.py", "las_regelbok.py", "inlasning_skydd.py")
SKYDDSMODUL = "inlasning_skydd"
INLASNINGSMODULER = ("las_bank", "las_kassa", "las_underlag", "las_matchningsformat", "las_kontoplan", "las_momssatser",
                     "las_regelbok")
# Kärnmoduler som inte läser filer men har egna byggstenar: alla deras namn som börjar med understreck.
FORSLAGSMODUL = "konteringsforslag"
MODULER_MED_BYGGSTENAR = INLASNINGSMODULER + (FORSLAGSMODUL,)
GENVAGAR = ("_tolka_rader", "_tolka_kassarader", "_las_underlagsfil",
            # Kontoplanens och momsfilens delkontroller, och kontrollerna som ger ett ofryst resultat
            "_kontrollera_kontoplan", "_kontrollera_konton", "_kontrollera_konto", "_kontrollera_roller",
            "_kontrollera_momssatser", "_kontrollera_perioder", "_kontrollera_period",
            # Regelbokens delkontroller, och kontrollen som ger ett ofryst resultat
            "_kontrollera_regelbok", "_kontrollera_regelbokens_regler", "_kontrollera_regelboksregel",
            "_kontrollera_galler", "_kontrollera_villkor", "_kontrollera_kontering", "_kontrollera_bankradsregel",
            "_kontrollera_varugrupp", "_kontrollera_granser", "_kontrollera_k9", "_kontrollera_oppettider",
            "_kontrollera_godkand", "_konfigurationen", "_konto_per_varugrupp", "_kontrollera_agare_och_narstaende",
            "_kontrollera_agarregel")
# Nycklarna som skapar en Kontoplan, Momssatser eller en Regelbok, och det som ligger i dem.
KONFIGURATIONENS_INRE = ("_KONTOPLANSNYCKEL", "_MOMSNYCKEL", "_REGELBOKSNYCKEL", "_status", "_konton", "_roller",
                         "_varugrupper", "_tolerans_ore_per_rad", "_kontrollsumma", "_regelboken")
# Det inre i en Kassaperiod, en Underlagsperiod och en Bankperiod: nyckeln som skapar en (den heter
# _PERIODNYCKEL i alla tre modulerna), och det som ligger i den.
PERIODENS_INRE = ("_PERIODNYCKEL", "_rapporter", "_fran_datum", "_till_datum", "_underlag", "_arenden", "_rader",
                  "_ingaende_saldo_ore", "_utgaende_saldo_ore")

# Sätt att nå ett namn som byggs ihop medan programmet kör. Ett sådant namn går inte att granska i
# koden, så det får inte användas i kärnan alls. Först fristående namn och moduler, sedan
# attribut (till exempel sys.modules och las_bank.__dict__).
DYNAMISKA_NAMN = ("__import__", "eval", "exec", "compile", "globals", "locals", "vars", "importlib",
                  "builtins", "__builtins__")
DYNAMISKA_ATTRIBUT = ("__dict__", "__getattribute__", "__setattr__", "__delattr__", "modules", "import_module",
                      "__import__")
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

    Till exempel ger "from inlasning_skydd import _csv_rader as rader" namnet rader, och
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
    forbjudna = (set(GENVAGAR) | set(PERIODENS_INRE) | set(KONFIGURATIONENS_INRE) | {SKYDDSMODUL}
                 | toppnamn(mapp / (SKYDDSMODUL + ".py"))
                 | {namn for namn in toppnamn(mapp / (FORSLAGSMODUL + ".py")) if namn.startswith("_")})
    for modul in MODULER_MED_BYGGSTENAR:
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
                elif moduldelar[-1] in MODULER_MED_BYGGSTENAR and alias.name == "*":
                    fynd.append((rad, "importerar allt från " + nod.module + ", även byggstenarna"))
                elif moduldelar[-1] in MODULER_MED_BYGGSTENAR and alias.name in forbjudna:
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
    for namn in ["_tolka_rader", "_tolka_kassarader", "inlasning_skydd", "_las_fil", "_avkoda", "_csv_rader",
                 "_rubrikens_falt", "_inga_otillatna_tecken", "_nul_fel", "_csv_fel", "_ladda_json",
                 "_kontrollera_namn", "_tolka_datum", "_tolka_ore", "_Filsort", "_OTILLATNA_TECKEN",
                 "_TILLATNA_AVGRANSARE", "_HELTAL", "_RADBRYTNINGAR", "_RIKTNINGSTECKEN", "_ar_sokvag", "_DATUM",
                 "_sokvagens_typ", "_PERIODNYCKEL", "_rapporter", "_las_underlagsfil", "_underlag", "_arenden",
                 "_DubbelNyckel", "_inga_dubbla_nycklar", "_UNDERLAGSFIL", "_rader", "_ingaende_saldo_ore",
                 "_utgaende_saldo_ore", "_inga_dolda_tecken_i_json", "_text_i_json", "_heltal_i_json", "_datumtext",
                 "_ar_dolt_tecken", "_json_typ", "_KONTOPLANSNYCKEL", "_MOMSNYCKEL", "_konton", "_roller",
                 "_varugrupper", "_status", "_tolerans_ore_per_rad", "_kontrollera_konto", "_kontrollera_period",
                 "_kontrollera_perioder", "_KONTOPLAN", "_MOMSSATSER", "_REGELBOKSNYCKEL", "_regelboken",
                 "_kontrollsumma", "_REGELBOK", "_las_jsonfil", "_tolka_json", "_kontrollera_regelbok",
                 "_kontrollera_regelboksregel", "_konfigurationen", "_FORSLAGSNYCKEL", "_FORSLAGEN", "_kontrollera_k2",
                 "_kontrollera_ursprung", "_kontrollera_formen", "_sla_upp", "_innehallet"]:
        assert namn in forbjudna, namn
    # Det som annan kod ska använda är inte förbjudet.
    for namn in ["las_bankfil", "las_kassafil", "las_kassaperiod", "Kassaperiod", "ladda_bankformat",
                 "ladda_kassaformat", "kontrollera_k1", "kontrollera_z_serien", "summa_per_momssats", "kronor",
                 "BankfilFel", "KassafilFel", "rapporter", "fran_datum", "till_datum", "las_underlagsperiod",
                 "Underlagsperiod", "UnderlagFilFel", "underlag", "arenden", "ladda_matchningsformat",
                 "kontrollera_matchningsformat", "MatchningsformatFel", "matcha_period", "MatchningFel",
                 "Bankperiod", "sla_ihop_bankperioder", "rader", "ingaende_saldo_ore", "utgaende_saldo_ore",
                 "las_kontoplan", "Kontoplan", "KontoplanFel", "kontots_namn", "rollens_konto", "utgaende_moms_konto",
                 "konton", "status", "las_momssatser", "Momssatser", "MomssatsFel", "sats", "period", "varugrupper",
                 "tolerans_ore_per_rad", "ROLLER", "HOGSTA_SATS", "las_regelbok", "Regelbok", "RegelbokFel",
                 "regel_for_underlag", "regel_for_z_rapport", "regel_for_bankrad", "kontrollsumma", "regler",
                 "granser", "oppettider", "REGELBOK_NYCKLAR", "KALLOR", "NIVAER", "agare_och_narstaende",
                 "ar_agare_eller_narstaende", "kontots_roller", "skapa_konteringsforslag", "Konteringsforslag",
                 "KonteringsforslagFel", "verifikation", "kopplingar", "motivering", "kontroller", "forslag_id",
                 "FORSLAG_NYCKLAR", "BERAKNINGAR"]:
        assert namn not in forbjudna, namn


def test_konfigurationens_inre_finns_i_modulerna_och_ar_forbjudet():
    # Skydd: nycklarna, det inre och delkontrollerna ska verkligen heta så i las_kontoplan.py,
    # las_momssatser.py och las_regelbok.py. Annars förbjuder testerna namn som ingen använder, medan
    # det verkliga heter något annat.
    import las_kontoplan
    import las_momssatser
    import las_regelbok

    toppnamn_i_modulerna = (toppnamn(SCRIPTS / "las_kontoplan.py") | toppnamn(SCRIPTS / "las_momssatser.py")
                            | toppnamn(SCRIPTS / "las_regelbok.py"))
    assert {"_KONTOPLANSNYCKEL", "_MOMSNYCKEL", "_REGELBOKSNYCKEL"} <= toppnamn_i_modulerna
    assert set(GENVAGAR[3:]) <= toppnamn_i_modulerna
    inre = (set(las_kontoplan.Kontoplan.__slots__) | set(las_momssatser.Momssatser.__slots__)
            | set(las_regelbok.Regelbok.__slots__))
    assert inre | {"_KONTOPLANSNYCKEL", "_MOMSNYCKEL", "_REGELBOKSNYCKEL"} == set(KONFIGURATIONENS_INRE)
    assert set(KONFIGURATIONENS_INRE) <= forbjudna_namn()


def test_regelbokens_alla_delkontroller_ar_forbjudna():
    # Skydd: varje funktion i las_regelbok.py som kontrollerar en del av filen (namnet börjar med
    # _kontrollera_) står bland genvägarna. En ny delkontroll måste alltså läggas till med flit.
    delkontroller = {namn for namn in toppnamn(SCRIPTS / "las_regelbok.py") if namn.startswith("_kontrollera_")}
    assert len(delkontroller) > 10
    assert delkontroller <= set(GENVAGAR)


def test_i1_underlagets_genvagar_finns_i_modulen():
    # Skydd: de förbjudna namnen för underlaget ska verkligen finnas i las_underlag.py. Annars
    # förbjuder testerna nedan namn som ingen använder, medan den verkliga genvägen heter något annat.
    import las_underlag

    assert {"_las_underlagsfil", "_PERIODNYCKEL"} <= toppnamn(SCRIPTS / "las_underlag.py")
    assert {"_underlag", "_arenden", "_fran_datum", "_till_datum"} == set(las_underlag.Underlagsperiod.__slots__)


def test_i1_bankperiodens_inre_finns_i_modulen_och_ar_forbjudet():
    # Skydd: nyckeln och Bankperiodens inre ska verkligen heta så i las_bank.py, och alla ska vara
    # förbjudna. Annars förbjuder testerna namn som ingen använder, medan det verkliga inre heter något annat.
    import las_bank

    assert "_PERIODNYCKEL" in toppnamn(SCRIPTS / "las_bank.py")
    assert set(las_bank.Bankperiod.__slots__) == {"_rader", "_ingaende_saldo_ore", "_utgaende_saldo_ore"}
    assert {"_PERIODNYCKEL", *las_bank.Bankperiod.__slots__} <= set(PERIODENS_INRE) & forbjudna_namn()


# --- Byggstenarna är interna ---

def offentliga_byggstenar(mapp):
    """Ställen där en byggsten får ett namn utan understreck, som text för felmeddelandet.

    Det gäller namn som inlasning_skydd.py binder på översta nivån, namn som las_bank.py och
    las_kassa.py importerar från inlasning_skydd (även modulen själv), och offentliga alias i
    dem för en byggsten eller genväg, som csv_rader = _csv_rader eller TOLKA = _tolka_rader.
    """
    fynd = [SKYDDSMODUL + ".py binder " + namn for namn in sorted(toppnamn(mapp / (SKYDDSMODUL + ".py")))
            if not namn.startswith("_")]
    forbjudna = forbjudna_namn(mapp)
    for modul in MODULER_MED_BYGGSTENAR:
        trad = ast.parse((mapp / (modul + ".py")).read_text(encoding="utf-8"))
        for nod in ast.walk(trad):
            if isinstance(nod, ast.ImportFrom) and (nod.module or "").split(".")[-1] == SKYDDSMODUL:
                fynd += [modul + ".py importerar " + (alias.asname or alias.name) for alias in nod.names
                         if not (alias.asname or alias.name).startswith("_")]
            elif isinstance(nod, ast.Import):
                fynd += [modul + ".py importerar " + (alias.asname or alias.name) for alias in nod.names
                         if SKYDDSMODUL in alias.name.split(".") and not (alias.asname or alias.name).startswith("_")]
        for nod in trad.body:
            if (isinstance(nod, ast.Assign) and isinstance(nod.value, (ast.Name, ast.Attribute))
                    and (getattr(nod.value, "id", None) in forbjudna or getattr(nod.value, "attr", None) in forbjudna)):
                fynd += [modul + ".py gör " + mal.id + " till ett alias" for mal in nod.targets
                         if isinstance(mal, ast.Name) and not mal.id.startswith("_")]
    return fynd


def test_byggstenarna_har_bara_interna_namn():
    # Alla namn i inlasning_skydd.py börjar med understreck, och las_bank och las_kassa gör inget av
    # dem offentligt. En ny byggsten blir därför intern från början, och testet slår larm om någon
    # glömmer det.
    assert {"_las_fil", "_avkoda", "_csv_rader", "_Filsort"} <= toppnamn(SCRIPTS / (SKYDDSMODUL + ".py"))
    fynd = offentliga_byggstenar(SCRIPTS)
    assert not fynd, "Byggstenar med offentligt namn:\n" + "\n".join(fynd)


def offentliga_namn_for_byggstenar(moduler):
    """[(modul, namn), ...] för varje offentligt namn i modulerna som pekar på en byggsten, när programmet kör."""
    import inlasning_skydd

    byggstenar = {id(getattr(inlasning_skydd, namn)) for namn in toppnamn(SCRIPTS / (SKYDDSMODUL + ".py"))}
    assert len(byggstenar) > 20  # skydd mot att inga byggstenar hittas
    return [(modul.__name__, namn) for modul in moduler for namn in dir(modul)
            if not namn.startswith("_") and id(getattr(modul, namn)) in byggstenar]


def test_inlasningsmodulerna_har_inga_byggstenar_under_offentligt_namn():
    # Samma sak när programmet kör: inget offentligt namn i las_bank eller las_kassa pekar på en
    # byggsten. Det fångar även namn som läggs till på något annat sätt än i koden ovan.
    import las_bank
    import las_kassa
    import las_underlag

    import las_kontoplan
    import las_matchningsformat
    import las_momssatser
    import las_regelbok
    import matcha_bank

    import konteringsforslag

    assert offentliga_namn_for_byggstenar([las_bank, las_kassa, las_underlag, las_matchningsformat, matcha_bank,
                                           las_kontoplan, las_momssatser, las_regelbok, konteringsforslag]) == []


def test_kontrollen_hittar_byggstenar_under_offentligt_namn_nar_programmet_kor():
    import types

    import inlasning_skydd

    modul = types.ModuleType("rapport")
    modul.avkoda, modul._internt, modul.kronor = inlasning_skydd._avkoda, inlasning_skydd._las_fil, len
    modul.MONSTER = inlasning_skydd._HELTAL
    assert offentliga_namn_for_byggstenar([modul]) == [("rapport", "MONSTER"), ("rapport", "avkoda")]


OFFENTLIGA = {
    "offentlig_funktion": ("inlasning_skydd.py", "def avkoda(data, filsort): ...\n", "inlasning_skydd.py binder avkoda"),
    "offentlig_konstant": ("inlasning_skydd.py", "HELTAL = 1\n", "inlasning_skydd.py binder HELTAL"),
    "offentlig_klass": ("inlasning_skydd.py", "class Filsort: ...\n", "inlasning_skydd.py binder Filsort"),
    "import_under_offentligt_namn": ("las_bank.py", "from inlasning_skydd import _avkoda as avkoda\n",
                                     "las_bank.py importerar avkoda"),
    "import_med_paketnamn": ("las_kassa.py", "from scripts.inlasning_skydd import _las_fil as las_fil\n",
                             "las_kassa.py importerar las_fil"),
    "import_av_modulen": ("las_bank.py", "import inlasning_skydd\n", "las_bank.py importerar inlasning_skydd"),
    "alias_for_byggsten": ("las_bank.py", "csv_rader = _csv_rader\n", "las_bank.py gör csv_rader till ett alias"),
    "alias_for_genvag": ("las_kassa.py", "TOLKA = _tolka_kassarader\n", "las_kassa.py gör TOLKA till ett alias"),
}


@pytest.mark.parametrize("fil, kod, fynd", OFFENTLIGA.values(), ids=OFFENTLIGA.keys())
def test_kontrollen_hittar_offentliga_byggstenar(projekt, fil, kod, fynd):
    assert offentliga_byggstenar(projekt) == []  # skydd: det påhittade projektet är rent
    with open(projekt / fil, "a", encoding="utf-8") as ut:
        ut.write(kod)
    assert offentliga_byggstenar(projekt) == [fynd]


def test_kontrollen_slapper_igenom_interna_namn_och_vanliga_offentliga_namn(projekt):
    (projekt / "las_bank.py").write_text(
        "from inlasning_skydd import _avkoda, _csv_rader as _rader\nimport inlasning_skydd as _skydd\n"
        "BANKFIL = _Filsort('x')\n_RADER = _csv_rader\ndef las_bankfil(sokvag): ...\n", encoding="utf-8")
    assert offentliga_byggstenar(projekt) == []


# --- Skydd: kontrollen slår verkligen larm ---

@pytest.fixture
def projekt(tmp_path):
    """En påhittad scripts-mapp där genvägarna finns i de undantagna filerna och i testerna."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "import inlasning_skydd\nfrom las_bank import _tolka_rader, _csv_rader\n"
        "from las_kassa import _tolka_kassarader\nfrom las_underlag import _las_underlagsfil, _PERIODNYCKEL\n",
        encoding="utf-8")
    (tmp_path / "las_bank.py").write_text(
        "from inlasning_skydd import _avkoda, _csv_rader\ndef _tolka_rader(data, bankformat): ...\n", encoding="utf-8")
    (tmp_path / "las_kassa.py").write_text(
        "from inlasning_skydd import _las_fil\ndef _tolka_kassarader(data, kassaformat): ...\n", encoding="utf-8")
    (tmp_path / "las_underlag.py").write_text(
        "from inlasning_skydd import _las_fil, _nul_fel\nfrom las_kassa import normalisera_kassaregister as _n\n"
        "def _las_underlagsfil(sokvag): ...\n_PERIODNYCKEL = object()\n", encoding="utf-8")
    (tmp_path / "las_matchningsformat.py").write_text(
        "from inlasning_skydd import _ladda_json\ndef ladda_matchningsformat(sokvag): ...\n", encoding="utf-8")
    (tmp_path / "las_kontoplan.py").write_text(
        "from inlasning_skydd import _ladda_json\n_KONTOPLANSNYCKEL = object()\ndef las_kontoplan(sokvag): ...\n",
        encoding="utf-8")
    (tmp_path / "las_momssatser.py").write_text(
        "from inlasning_skydd import _ladda_json\n_MOMSNYCKEL = object()\ndef las_momssatser(sokvag): ...\n",
        encoding="utf-8")
    (tmp_path / "las_regelbok.py").write_text(
        "from inlasning_skydd import _las_jsonfil, _tolka_json\n_REGELBOKSNYCKEL = object()\n"
        "def las_regelbok(sokvag, kontoplan, momssatser, matchningsformat): ...\n", encoding="utf-8")
    (tmp_path / "konteringsforslag.py").write_text(
        "_FORSLAGSNYCKEL = object()\n_FORSLAGEN = {}\ndef _kontrollera_k2(verifikation, kontoplan): ...\n"
        "def skapa_konteringsforslag(forslag, regelbok, kontoplan): ...\n", encoding="utf-8")
    (tmp_path / "inlasning_skydd.py").write_text("def _las_fil(sokvag, filsort): ...\n", encoding="utf-8")
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
    "skyddsmodulen_from": "from inlasning_skydd import _las_fil, _avkoda, _csv_rader\n",
    "skyddsmodulen_from_ett_namn": "from inlasning_skydd import _rubrikens_falt\n",
    "skyddsmodulen_paketnamn": "import scripts.inlasning_skydd\n",
    "skyddsmodulen_relativ": "from . import inlasning_skydd\n",
    "skyddsmodulen_relativ_from": "from .inlasning_skydd import _csv_rader\n",
    "skyddsmodulen_i_funktion": "def f():\n    from inlasning_skydd import _avkoda\n    return _avkoda\n",
    # Byggstenarna via las_bank och las_kassa
    "byggsten_via_bank": "from las_bank import _csv_rader, _las_fil, _avkoda\n",
    "byggsten_via_kassa": "from las_kassa import _rubrikens_falt\n",
    "byggsten_via_kassa_konstant": "from las_kassa import _HELTAL\n",
    "byggsten_via_bank_attribut": "import las_bank\nrader = las_bank._csv_rader([], 1, ',', 1, None)\n",
    "byggsten_via_kassa_alias": "import las_kassa as k\ntext = k._avkoda(b'', None)\n",
    "byggsten_via_bank_stjarna": "from las_bank import *\n",
    "skyddsmodulen_via_bank": "import las_bank\ns = las_bank.inlasning_skydd\n",
    "byggsten_getattr_text": "import las_bank\nf = getattr(las_bank, '_csv_rader')\n",
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
    # Kassaperiodens inre: nyckeln som skapar en period med vilka rader som helst, och raderna
    "periodnyckel": "from las_kassa import _PERIODNYCKEL\n",
    "periodnyckel_attribut": "import las_kassa\np = las_kassa.Kassaperiod(las_kassa._PERIODNYCKEL, [], 'a', 'b')\n",
    "periodens_rader": "def f(period):\n    return period._rapporter\n",
    "periodens_rader_setattr": "def f(period):\n    object.__setattr__(period, '_rapporter', ())\n",
    "periodens_rader_setattr_hopsatt": "def f(period, n):\n    object.__setattr__(period, n, ())\n",
    "periodens_datum_delattr": "def f(period, n):\n    object.__delattr__(period, n)\n",
}


@pytest.mark.parametrize("kod", GENVAGSKOD.values(), ids=GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_en_fil_som_anvander_en_genvag(projekt, kod):
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


# Genvägar förbi underlagets kontroller. las_underlag.py är undantagen, men förbudet gäller alla andra kärnfiler.
UNDERLAGETS_GENVAGSKOD = {
    "underlagets_genvag": "from las_underlag import _las_underlagsfil\n",
    "underlagets_genvag_alias": "from las_underlag import _las_underlagsfil as las\n",
    "underlagets_genvag_attribut": "import las_underlag\nu = las_underlag._las_underlagsfil('U-1.json')\n",
    "underlagets_genvag_modulalias": "import las_underlag as u\nx = u._las_underlagsfil('U-1.json')\n",
    "underlagets_genvag_getattr_hopsatt": "import las_underlag\nf = getattr(las_underlag, '_las_' + 'underlagsfil')\n",
    "underlagets_genvag_paketnamn": "from scripts.las_underlag import _las_underlagsfil\n",
    "underlagets_periodnyckel": "from las_underlag import _PERIODNYCKEL\n",
    "underlagets_periodnyckel_attribut": ("import las_underlag\np = las_underlag.Underlagsperiod("
                                          "las_underlag._PERIODNYCKEL, [], [], 'a', 'b')\n"),
    "underlagsperiodens_underlag": "def f(period):\n    return period._underlag\n",
    "underlagsperiodens_arenden": "def f(period):\n    return period._arenden\n",
    "underlagsperiodens_setattr": "def f(period):\n    object.__setattr__(period, '_arenden', ())\n",
    "byggsten_via_underlag": "from las_underlag import _las_fil, _nul_fel\n",
    "byggsten_via_underlag_attribut": "import las_underlag\nd = las_underlag._las_fil('x', None)\n",
    "byggsten_via_underlag_stjarna": "from las_underlag import *\n",
}


@pytest.mark.parametrize("kod", UNDERLAGETS_GENVAGSKOD.values(), ids=UNDERLAGETS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_forbi_underlagets_kontroller(projekt, kod):
    # Skydd: namnen finns verkligen i den riktiga modulen, så att förbudet gäller den verkliga genvägen.
    assert {"_las_underlagsfil", "_PERIODNYCKEL", "_las_fil", "_nul_fel"} <= (
        toppnamn(SCRIPTS / "las_underlag.py") | namn_som_leder_till_genvagar(SCRIPTS / "las_underlag.py", set()))
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


# Genvägar förbi bankperiodens skydd: nyckeln som skapar en Bankperiod med vilka rader som helst, och
# periodens inre. las_bank.py är undantagen, men förbudet gäller alla andra kärnfiler.
BANKPERIODENS_GENVAGSKOD = {
    "bankens_periodnyckel": "from las_bank import _PERIODNYCKEL\n",
    "bankens_periodnyckel_alias": "from las_bank import _PERIODNYCKEL as nyckel\n",
    "bankens_periodnyckel_attribut": "import las_bank\np = las_bank.Bankperiod(las_bank._PERIODNYCKEL, [], 0, 0)\n",
    "bankens_periodnyckel_modulalias": "import las_bank as b\np = b.Bankperiod(b._PERIODNYCKEL, [], 0, 0)\n",
    "bankens_periodnyckel_getattr": "import las_bank\nn = getattr(las_bank, '_PERIOD' + 'NYCKEL')\n",
    "bankens_periodnyckel_paketnamn": "from scripts.las_bank import _PERIODNYCKEL\n",
    "bankperiodens_rader": "def f(period):\n    return period._rader\n",
    "bankperiodens_ingaende_saldo": "def f(period):\n    return period._ingaende_saldo_ore\n",
    "bankperiodens_utgaende_saldo": "def f(period):\n    return period._utgaende_saldo_ore\n",
    "bankperiodens_rader_getattr_text": "def f(period):\n    return getattr(period, '_rader')\n",
    "bankperiodens_rader_setattr": "def f(period):\n    object.__setattr__(period, '_rader', ())\n",
    "bankperiodens_saldo_setattr_text": "def f(period):\n    setattr(period, '_utgaende_saldo_ore', 0)\n",
    "bankperiodens_rader_delattr": "def f(period):\n    object.__delattr__(period, '_rader')\n",
}


@pytest.mark.parametrize("kod", BANKPERIODENS_GENVAGSKOD.values(), ids=BANKPERIODENS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_forbi_bankperiodens_skydd(projekt, kod):
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


# Genvägar förbi kontoplanens och momsfilens kontroller. las_kontoplan.py och las_momssatser.py är
# undantagna, men förbudet gäller alla andra kärnfiler.
KONFIGURATIONENS_GENVAGSKOD = {
    "kontoplanens_nyckel": "from las_kontoplan import _KONTOPLANSNYCKEL\n",
    "kontoplanens_nyckel_attribut": ("import las_kontoplan as k\n"
                                     "p = k.Kontoplan(k._KONTOPLANSNYCKEL, 'x', {}, {})\n"),
    "kontoplanens_nyckel_getattr": "import las_kontoplan\nn = getattr(las_kontoplan, '_KONTOPLANS' + 'NYCKEL')\n",
    "kontoplanens_konton": "def f(plan):\n    return plan._konton\n",
    "kontoplanens_roller_setattr": "def f(plan):\n    object.__setattr__(plan, '_roller', {})\n",
    "kontoplanens_delkontroll": "from las_kontoplan import _kontrollera_konto\n",
    "kontoplanens_delkontroll_attribut": "import las_kontoplan\nk = las_kontoplan._kontrollera_roller({}, {}, 'x')\n",
    "kontoplanens_kontroll_utan_frysning": "from las_kontoplan import _kontrollera_kontoplan\n",
    "kontoplanens_byggsten": "from las_kontoplan import _ladda_json\n",
    "kontoplanens_stjarna": "from las_kontoplan import *\n",
    "momsfilens_nyckel": "from las_momssatser import _MOMSNYCKEL\n",
    "momsfilens_nyckel_attribut": "import las_momssatser as m\ns = m.Momssatser(m._MOMSNYCKEL, 'x', {}, 0)\n",
    "momsfilens_varugrupper": "def f(satser):\n    return satser._varugrupper\n",
    "momsfilens_tolerans_getattr": "def f(satser):\n    return getattr(satser, '_tolerans_ore_per_rad')\n",
    "momsfilens_status": "def f(satser):\n    return satser._status\n",
    "momsfilens_delkontroll": "from las_momssatser import _kontrollera_period\n",
    "momsfilens_perioder_utan_overlappskontroll": "import las_momssatser\np = las_momssatser._kontrollera_period({}, 'x', 'y')\n",
    "momsfilens_kontroll_utan_frysning": "from las_momssatser import _kontrollera_momssatser\n",
    "momsfilens_byggsten": "from las_momssatser import _datumtext\n",
    "momsfilens_stjarna": "from las_momssatser import *\n",
    "nya_byggstenar_direkt": "from inlasning_skydd import _inga_dolda_tecken_i_json\n",
}


@pytest.mark.parametrize("kod", KONFIGURATIONENS_GENVAGSKOD.values(), ids=KONFIGURATIONENS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_forbi_kontoplanens_och_momsfilens_kontroller(projekt, kod):
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


# Genvägar förbi regelbokens kontroller. las_regelbok.py är undantagen, men förbudet gäller alla andra kärnfiler.
REGELBOKENS_GENVAGSKOD = {
    "regelbokens_nyckel": "from las_regelbok import _REGELBOKSNYCKEL\n",
    "regelbokens_nyckel_attribut": "import las_regelbok as r\nb = r.Regelbok(r._REGELBOKSNYCKEL, '0' * 64, {})\n",
    "regelbokens_nyckel_getattr": "import las_regelbok\nn = getattr(las_regelbok, '_REGELBOKS' + 'NYCKEL')\n",
    "regelbokens_inre": "def f(bok):\n    return bok._regelboken\n",
    "regelbokens_inre_getattr_text": "def f(bok):\n    return getattr(bok, '_regelboken')\n",
    "regelbokens_kontrollsumma_setattr": "def f(bok):\n    object.__setattr__(bok, '_kontrollsumma', '0' * 64)\n",
    "regelbokens_kontrollsumma_attribut": "def f(bok):\n    return bok._kontrollsumma\n",
    "regelbokens_kontroll_utan_frysning": "from las_regelbok import _kontrollera_regelbok\n",
    "regelbokens_delkontroll": "from las_regelbok import _kontrollera_regelboksregel\n",
    "regelbokens_delkontroll_attribut": "import las_regelbok\nv = las_regelbok._kontrollera_villkor({}, 'x', {}, 'y')\n",
    "regelbokens_tvetydighet_hoppas_over": "from las_regelbok import _kontrollera_regelbokens_regler as k\n",
    "regelbokens_indata_hoppas_over": "import las_regelbok as r\nk = r._konfigurationen(None, None, None)\n",
    "regelbokens_byggsten": "from las_regelbok import _las_jsonfil\n",
    "regelbokens_byggsten_tolka": "import las_regelbok\nd = las_regelbok._tolka_json(b'{}', 'x', None)\n",
    "regelbokens_stjarna": "from las_regelbok import *\n",
    "nya_byggstenar_for_json_direkt": "from inlasning_skydd import _las_jsonfil, _tolka_json\n",
}


@pytest.mark.parametrize("kod", REGELBOKENS_GENVAGSKOD.values(), ids=REGELBOKENS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_forbi_regelbokens_kontroller(projekt, kod):
    # Skydd: namnen finns verkligen i den riktiga modulen, så att förbudet gäller den verkliga genvägen.
    assert {"_REGELBOKSNYCKEL", "_kontrollera_regelbok", "_kontrollera_villkor", "_konfigurationen"} <= toppnamn(
        SCRIPTS / "las_regelbok.py")
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


# Genvägar förbi konteringsförslagets kontroller. konteringsforslag.py är inte undantagen, så förbudet
# gäller alla andra kärnfiler.
FORSLAGETS_GENVAGSKOD = {
    "forslagets_nyckel": "from konteringsforslag import _FORSLAGSNYCKEL\n",
    "forslagets_nyckel_alias": "from konteringsforslag import _FORSLAGSNYCKEL as nyckel\n",
    "forslagets_nyckel_attribut": ("import konteringsforslag as k\n"
                                   "f = k.Konteringsforslag(k._FORSLAGSNYCKEL, {'forslag_id': 'F-1'})\n"),
    "forslagets_nyckel_getattr": "import konteringsforslag\nn = getattr(konteringsforslag, '_FORSLAGS' + 'NYCKEL')\n",
    "forslagets_nyckel_getattr_text": "import konteringsforslag\nn = getattr(konteringsforslag, '_FORSLAGSNYCKEL')\n",
    "forslagets_nyckel_paketnamn": "from scripts.konteringsforslag import _FORSLAGSNYCKEL\n",
    "forslagens_innehall": "from konteringsforslag import _FORSLAGEN\n",
    "forslagens_innehall_attribut": "import konteringsforslag\nkonteringsforslag._FORSLAGEN.clear()\n",
    "forslagens_innehall_andras": "import konteringsforslag as k\ndef f(forslag, nytt):\n    k._FORSLAGEN[forslag] = nytt\n",
    "forslagets_innehall_las": "import konteringsforslag\ni = konteringsforslag._innehallet(None)\n",
    "k2_hoppas_over": "from konteringsforslag import _kontrollera_ursprung\n",
    "ursprunget_hoppas_over": "from konteringsforslag import _kontrollera_k2\n",
    "ursprunget_hoppas_over_attribut": "import konteringsforslag\nk = konteringsforslag._kontrollera_k2({}, None)\n",
    "formen_hoppas_over": "from konteringsforslag import _kontrollera_formen\n",
    "kallan_slas_upp_utan_kontroll": "from konteringsforslag import _sla_upp, _Kallorna\n",
    "forslagets_stjarna": "from konteringsforslag import *\n",
    "forslagets_text": "def f(forslag):\n    return '_FORSLAGEN'\n",
}


@pytest.mark.parametrize("kod", FORSLAGETS_GENVAGSKOD.values(), ids=FORSLAGETS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_forbi_konteringsforslagets_kontroller(projekt, kod):
    # Skydd: namnen finns verkligen i den riktiga modulen, så att förbudet gäller den verkliga genvägen.
    assert {"_FORSLAGSNYCKEL", "_FORSLAGEN", "_kontrollera_k2", "_kontrollera_ursprung", "_kontrollera_formen",
            "_sla_upp", "_Kallorna", "_innehallet"} <= toppnamn(SCRIPTS / "konteringsforslag.py")
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("rapport.py:") for rad in fynd), fynd


def test_konteringsforslagets_alla_byggstenar_ar_forbjudna():
    # Skydd: varje namn i konteringsforslag.py som börjar med understreck är förbjudet för annan kärnkod.
    # En ny byggsten blir alltså förbjuden från början.
    privata = {namn for namn in toppnamn(SCRIPTS / "konteringsforslag.py") if namn.startswith("_")}
    assert len(privata) > 20
    assert {namn for namn in privata if namn.startswith("_kontrollera_")} >= {
        "_kontrollera_k2", "_kontrollera_ursprung", "_kontrollera_formen", "_kontrollera_kopplingar",
        "_kontrollera_momskonto", "_kontrollera_bankkonto", "_kontrollera_indatans_typer"}
    assert privata <= forbjudna_namn()


def test_konteringsforslaget_omfattas_av_skyddet():
    # konteringsforslag.py är en vanlig kärnfil: den är inte undantagen, så alla förbud gäller den, och den
    # använder ingen genväg. Perioderna, kontoplanen och regelboken får den bara som färdiga objekt.
    modul = SCRIPTS / "konteringsforslag.py"
    assert modul in karnfiler(SCRIPTS) and modul.name not in UNDANTAGNA
    assert genvagar_i_fil(modul, forbjudna_namn()) == []


def test_kontrollen_hittar_alias_for_konteringsforslagets_byggstenar(projekt):
    (projekt / "konteringsforslag.py").write_text(
        "_FORSLAGSNYCKEL = object()\nNYCKEL = _FORSLAGSNYCKEL\ndef _kontrollera_k2(v, k): ...\nK2 = _kontrollera_k2\n",
        encoding="utf-8")
    forbjudna = forbjudna_namn(projekt)
    assert {"NYCKEL", "K2"} <= forbjudna
    assert offentliga_byggstenar(projekt) == ["konteringsforslag.py gör NYCKEL till ett alias",
                                              "konteringsforslag.py gör K2 till ett alias"]
    (projekt / "rapport.py").write_text("from konteringsforslag import NYCKEL\n", encoding="utf-8")
    assert genvagar_i(projekt, forbjudna) == ["rapport.py:1 hämtar NYCKEL från konteringsforslag"]


@pytest.mark.parametrize("kod", [
    "from las_kontoplan import las_kontoplan, Kontoplan, KontoplanFel, ROLLER\n"
    "plan = las_kontoplan('k.json')\nkonto = plan.rollens_konto('bank', '2025-01-01')\nx = plan.konton\n",
    "from las_momssatser import las_momssatser, MomssatsFel\nsatser = las_momssatser('m.json')\n"
    "sats = satser.sats('grupp', '2025-01-01')\nstatus = satser.status\n",
    "from las_regelbok import las_regelbok, Regelbok, RegelbokFel, KALLOR\n"
    "bok = las_regelbok('r.json', None, None, None)\nregel = bok.regel_for_underlag('kvitto', 'x', '2025-01-01')\n"
    "summa = bok.kontrollsumma\ngranser = (bok.granser, bok.k9, bok.oppettider, bok.regler)\n",
    "from konteringsforslag import skapa_konteringsforslag, Konteringsforslag, KonteringsforslagFel, KALLOR\n"
    "f = skapa_konteringsforslag({}, None, None, None, None, None)\nv = (f.verifikation, f.kopplingar, f.kontroller)\n"
    "ok = type(f) is Konteringsforslag\nroller = None.kontots_roller('1')\n",
], ids=["kontoplan", "momssatser", "regelbok", "konteringsforslag"])
def test_i1_kontoplanen_och_momsfilen_las_pa_ratt_satt_slapps_igenom(projekt, kod):
    (projekt / "rapport.py").write_text(kod, encoding="utf-8")
    assert genvagar_i(projekt) == []


def test_matchningen_omfattas_av_skyddet():
    # matcha_bank.py är en vanlig kärnfil: den är inte undantagen, så alla förbud gäller den, och den
    # använder ingen genväg. Bankrader och underlag får den bara från las_bankfil och las_underlagsperiod.
    matchning = SCRIPTS / "matcha_bank.py"
    assert matchning in karnfiler(SCRIPTS) and matchning.name not in UNDANTAGNA
    assert genvagar_i_fil(matchning, forbjudna_namn()) == []


MATCHNINGENS_GENVAGSKOD = {
    "byggsten_via_matchningsformat": "from las_matchningsformat import _ladda_json\n",
    "byggsten_via_matchningsformat_attribut": "import las_matchningsformat as m\nd = m._kontrollera_namn('x')\n",
    "byggsten_via_matchningsformat_stjarna": "from las_matchningsformat import *\n",
    "matchningen_importerar_skyddet": "import inlasning_skydd\n",
    "matchningen_anvander_underlagets_genvag": "import las_underlag\nu = las_underlag._las_underlagsfil('U-1.json')\n",
    "matchningen_skapar_en_underlagsperiod": ("import las_underlag\np = las_underlag.Underlagsperiod("
                                              "las_underlag._PERIODNYCKEL, [], [], 'a', 'b')\n"),
    "matchningen_skapar_en_bankperiod": ("from las_bank import Bankperiod, _PERIODNYCKEL\n"
                                         "p = Bankperiod(_PERIODNYCKEL, [], 0, 0)\n"),
    "matchningen_laser_bankperiodens_inre": "def matcha_period(bankperiod):\n    return bankperiod._rader\n",
}


@pytest.mark.parametrize("kod", MATCHNINGENS_GENVAGSKOD.values(), ids=MATCHNINGENS_GENVAGSKOD.keys())
def test_i1_kontrollen_hittar_genvagar_i_matchningen(projekt, kod):
    # En påhittad matcha_bank.py i det påhittade projektet. Den är inte undantagen, så genvägarna hittas.
    (projekt / "matcha_bank.py").write_text(kod, encoding="utf-8")
    fynd = genvagar_i(projekt)
    assert fynd and all(rad.startswith("matcha_bank.py:") for rad in fynd), fynd


def test_i1_kontrollen_hittar_en_genvag_i_en_undermapp(projekt):
    (projekt / "matchning").mkdir()
    (projekt / "matchning" / "las_bank.py").write_text("from las_kassa import _tolka_kassarader\n", encoding="utf-8")
    assert genvagar_i(projekt) == ["matchning/las_bank.py:1 hämtar _tolka_kassarader från las_kassa"]


def test_i1_kontrollen_hittar_alias_i_en_inlasningsmodul(projekt):
    # G8 punkt 5: ett alias i las_bank.py (TOLKA = _tolka_rader) som en annan fil sedan använder.
    (projekt / "las_bank.py").write_text(
        "from inlasning_skydd import _csv_rader as rader\ndef _tolka_rader(data, bankformat): ...\n"
        "TOLKA = _tolka_rader\nOCKSA = TOLKA\nRADER = rader\n", encoding="utf-8")
    forbjudna = forbjudna_namn(projekt)
    assert {"TOLKA", "OCKSA", "rader", "RADER"} <= forbjudna
    for kod in ["from las_bank import TOLKA\n", "import las_bank\nf = las_bank.OCKSA\n",
                "from las_bank import RADER\n", "import las_bank\nf = las_bank.rader\n"]:
        (projekt / "rapport.py").write_text(kod, encoding="utf-8")
        assert genvagar_i(projekt, forbjudna), kod


VANLIG_KOD = {
    "las_bankfil": "from las_bank import las_bankfil, ladda_bankformat, kronor, BankfilFel\n",
    "las_kassafil": "import las_kassa\nrader = las_kassa.las_kassafil('x.csv', {})\n",
    "las_kassaperiod": "from las_kassa import las_kassaperiod, summa_per_momssats\n"
                       "period = las_kassaperiod('kassa', {}, '2025-01-01', '2025-01-31')\n"
                       "summor = summa_per_momssats(period)\nrader = period.rapporter\n",
    "modulalias": "import las_kassa as k\nk.kontrollera_z_serien([])\n",
    "las_underlagsperiod": "from las_underlag import las_underlagsperiod, UnderlagFilFel\n"
                           "period = las_underlagsperiod('underlag', '2025-01-01', '2025-01-31')\n"
                           "poster = period.underlag + period.arenden\n",
    "matcha_period": "from las_matchningsformat import ladda_matchningsformat\nfrom matcha_bank import matcha_period\n"
                     "resultat = matcha_period(None, None, ladda_matchningsformat('m.json'), '2025-01-31')\n",
    "bankperiod": "from las_bank import Bankperiod, las_bankfil, sla_ihop_bankperioder\n"
                  "januari = las_bankfil('bank.csv', {}, 0, 100)\nkvartal = sla_ihop_bankperioder([januari])\n"
                  "rader = kvartal.rader\nsaldon = (kvartal.ingaende_saldo_ore, kvartal.utgaende_saldo_ore)\n"
                  "ok = type(kvartal) is Bankperiod\n",
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
