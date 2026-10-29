"""Kärnan i scripts/ får inte innehålla något företagsspecifikt (SPEC avsnitt 2)."""

import ast
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
TESTER = SCRIPTS / "tests"
FORETAG = SCRIPTS.parent / "foretag"

FORBJUDNA_ORD = ["Syntet", "Testbutik", "Krog", "Bygg", "Swedbank"]
ORGANISATIONSNUMMER = re.compile(r"(?<!\d)\d{6}-\d{4}(?!\d)", re.ASCII)


def karnans_filer():
    return sorted(
        fil for fil in SCRIPTS.rglob("*.py")
        if TESTER not in fil.parents
    )


def test_karnan_har_filer_att_soka_i():
    # Skydd mot att testet blir grönt för att det inte hittar några filer alls.
    assert SCRIPTS / "belopp.py" in karnans_filer()


def test_karnan_innehaller_inget_foretagsspecifikt():
    fynd = []
    for fil in karnans_filer():
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            plats = str(fil.relative_to(SCRIPTS.parent)) + ":" + str(radnummer)
            for ord in FORBJUDNA_ORD:
                if ord in rad:
                    fynd.append(plats + " innehåller " + repr(ord))
            for nummer in ORGANISATIONSNUMMER.findall(rad):
                fynd.append(plats + " innehåller organisationsnummer " + repr(nummer))

    assert not fynd, "Företagsspecifikt innehåll i kärnan:\n" + "\n".join(fynd)


def kolumnnamn_i_bankformaten():
    """Alla kolumnnamn från alla företags bankformat.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/bankformat.json")):
        namn.update(json.loads(fil.read_text(encoding="utf-8"))["kolumner"].values())
    return sorted(namn)


def test_bankformaten_har_kolumnnamn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några bankformat alls.
    assert "Bokfört saldo" in kolumnnamn_i_bankformaten()


def test_karnan_innehaller_inga_kolumnnamn_fran_bankformaten():
    """Bankformatet hör till företagets konfiguration (F5), inte till kärnan.

    Kolumnnamnen söks som hela ord och med skiftläge, alltså stor och liten bokstav som i
    konfigurationen. "Belopp" ger träff, men inte "Beloppet" eller fältnamnet "belopp_ore".
    """
    monster = {namn: re.compile(r"(?<!\w)" + re.escape(namn) + r"(?!\w)") for namn in kolumnnamn_i_bankformaten()}
    fynd = []
    for fil in karnans_filer():
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            plats = str(fil.relative_to(SCRIPTS.parent)) + ":" + str(radnummer)
            for namn, regex in monster.items():
                if regex.search(rad):
                    fynd.append(plats + " innehåller kolumnnamnet " + repr(namn))

    assert not fynd, "Kolumnnamn från bankformatet i kärnan:\n" + "\n".join(fynd)


# --- Kassaformatet (F5 för kassan) ---

sys.path.insert(0, str(SCRIPTS))

import las_bank  # noqa: E402
import las_kassa  # noqa: E402
import las_underlag  # noqa: E402

# Ord som är både kärnans egen nyckel (i bankformat.json eller kassaformat.json) och ett
# kolumnnamn i ett kassaformat. Testdatans kassafil har kolumnen "belopp", och kärnan använder
# samma ord för uppgiften belopp. Därför kan ordet inte sökas efter som text. Att kärnan ändå
# inte har kassans kolumnnamn inbyggt bevisas av test_annat_kassaformat_laser_samma_data i
# test_las_kassa.py, som läser samma Z-rapport med helt andra namn.
KARNANS_EGNA_ORD = {"belopp"}


def namn_i_kassaformaten():
    """Alla kolumnnamn, postnamn och kassaregister från alla företags kassaformat.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/kassaformat.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update(data["kolumner"].values())
        for postnamn in data["poster"].values():
            namn.update(postnamn if isinstance(postnamn, list) else [postnamn])
        namn.update(data["kassaregister"])
    return sorted(namn)


def strangar_i_koden(kalla):
    """(radnummer, text) för varje textsträng i Python-koden, utom docstrings (förklarande text)."""
    trad = ast.parse(kalla)
    docstrings = set()
    for nod in ast.walk(trad):
        if isinstance(nod, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and nod.body:
            forsta = nod.body[0]
            if isinstance(forsta, ast.Expr) and isinstance(forsta.value, ast.Constant):
                docstrings.add(id(forsta.value))
    return [
        (getattr(nod, "lineno", 0), nod.value) for nod in ast.walk(trad)
        if isinstance(nod, ast.Constant) and isinstance(nod.value, str) and id(nod) not in docstrings
    ]


def kassanamn_i_filer(filer, namnlista, egna_ord=KARNANS_EGNA_ORD):
    """Var kassaformatens namn står i filerna.

    - En textsträng i koden som är exakt ett namn ger träff, till exempel "forsaljning".
    - Ett namn med understreck eller siffra, till exempel summa_brutto, ser ut som en kod och
      aldrig som svensk text. Det ger träff var det än står som helt ord, även i kommentarer.
    Vanliga ord som "moms" får alltså förekomma i förklarande text och i felmeddelanden.
    """
    fynd = []
    kodlika = [namn for namn in namnlista if re.search(r"[_\d]", namn)]
    for fil in filer:
        kalla = fil.read_text(encoding="utf-8")
        for radnummer, text in strangar_i_koden(kalla):
            if text.strip() in namnlista and text.strip() not in egna_ord:
                fynd.append(fil.name + ":" + str(radnummer) + " har textsträngen " + repr(text))
        for radnummer, rad in enumerate(kalla.splitlines(), start=1):
            for namn in kodlika:
                if re.search(r"(?<!\w)" + re.escape(namn) + r"(?!\w)", rad):
                    fynd.append(fil.name + ":" + str(radnummer) + " innehåller " + repr(namn))
    return fynd


def test_kassaformaten_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några kassaformat alls.
    namn = namn_i_kassaformaten()
    assert {"z_nummer", "summa_brutto", "forsaljning", "moms", "betalsatt_kort", "post", "TB-KASSA-1"} <= set(namn)


def test_karnans_egna_ord_ar_verkligen_karnans_nycklar():
    # Skydd mot att undantaget ovan växer med ord som inte är kärnans egna nycklar.
    assert KARNANS_EGNA_ORD <= set(las_bank.KOLUMN_NYCKLAR) | set(las_kassa.KOLUMN_NYCKLAR)


# Underlagets nycklar är kärnans egen form för underlag (las_underlag.py), gemensam för alla
# företag. Några av dem ("datum", "moms", "momssats") råkar också vara namn i testbutikens
# kassaformat. De godtas som textsträngar bara i las_underlag.py, där formen beskrivs, i
# matcha_bank.py, som läser underlagens uppgifter (till exempel "datum"), i
# konteringsforslag.py, som läser underlagens momsrader ("moms" och "momssats") och har samma ord
# "datum" för verifikationens datum, och i konteringsfloden.py, som läser underlagens datum och
# momsrader och bygger förslagen. Alla andra kärnfiler prövas som förut.
UNDERLAGSMODULEN = SCRIPTS / "las_underlag.py"
MATCHNINGSMODULEN = SCRIPTS / "matcha_bank.py"
FORSLAGSMODULEN = SCRIPTS / "konteringsforslag.py"
FLODESMODULEN = SCRIPTS / "konteringsfloden.py"
UNDERLAGETS_ANVANDARE = (UNDERLAGSMODULEN, MATCHNINGSMODULEN, FORSLAGSMODULEN, FLODESMODULEN)
UNDERLAGETS_EGNA_ORD = set(las_underlag.NYCKLAR) | set(las_underlag.MOMSRAD_NYCKLAR)

# Regelbokens nycklar är kärnans egen form för regelboken (las_regelbok.py), gemensam för alla
# företag. Två av dem råkar också vara namn i testbutikens kassaformat: "datum" (när regelboken
# godkändes) och "forsaljning" (konteringen av en Z-rapports försäljning). De godtas som
# textsträngar bara i las_regelbok.py. Vilka ord det är räknas fram ur modulens egna nycklar.
REGELBOKSMODULEN = SCRIPTS / "las_regelbok.py"


def regelbokens_egna_ord():
    import las_regelbok

    nycklar = set(las_regelbok.GODKAND_NYCKLAR) | set(las_regelbok.KONTERING_Z_NYCKLAR)
    return nycklar & set(namn_i_kassaformaten())


def test_karnan_innehaller_inga_namn_fran_kassaformaten():
    """Kassaformatet hör till företagets konfiguration, inte till kärnan."""
    namn = namn_i_kassaformaten()
    sarskilda = UNDERLAGETS_ANVANDARE + (REGELBOKSMODULEN,)
    fynd = kassanamn_i_filer([fil for fil in karnans_filer() if fil not in sarskilda], namn)
    fynd += kassanamn_i_filer(list(UNDERLAGETS_ANVANDARE), namn, KARNANS_EGNA_ORD | UNDERLAGETS_EGNA_ORD)
    fynd += kassanamn_i_filer([REGELBOKSMODULEN], namn, KARNANS_EGNA_ORD | regelbokens_egna_ord())
    assert not fynd, "Kolumnnamn, postnamn eller kassaregister från kassaformatet i kärnan:\n" + "\n".join(fynd)


def test_regelbokens_undantag_galler_bara_tva_nycklar():
    # Skydd: undantaget för las_regelbok.py är exakt de två nycklarna, och inget annat namn ur kassaformatet.
    assert REGELBOKSMODULEN in karnans_filer()
    assert regelbokens_egna_ord() == {"datum", "forsaljning"}
    assert kassanamn_i_filer([REGELBOKSMODULEN], namn_i_kassaformaten(), KARNANS_EGNA_ORD) != []


def test_underlagets_undantag_galler_bara_underlagets_nycklar(tmp_path):
    # Skydd: undantaget släpper bara igenom underlagets egna nycklar, inte andra namn ur kassaformatet.
    assert UNDERLAGSMODULEN in karnans_filer()
    assert {"datum", "moms", "momssats"} <= UNDERLAGETS_EGNA_ORD
    fil = tmp_path / "x.py"
    fil.write_text('a = "moms"\nb = "forsaljning"\nc = "summa_brutto"\n', encoding="utf-8")
    assert kassanamn_i_filer([fil], namn_i_kassaformaten()) == [
        "x.py:1 har textsträngen 'moms'", "x.py:2 har textsträngen 'forsaljning'",
        "x.py:3 har textsträngen 'summa_brutto'", "x.py:3 innehåller 'summa_brutto'"]
    assert kassanamn_i_filer([fil], namn_i_kassaformaten(), KARNANS_EGNA_ORD | UNDERLAGETS_EGNA_ORD) == [
        "x.py:2 har textsträngen 'forsaljning'", "x.py:3 har textsträngen 'summa_brutto'",
        "x.py:3 innehåller 'summa_brutto'"]


# --- Testdatans underlag ---

def namn_i_testdatans_underlag():
    """Alla id, motparter och fakturanummer i testdatans underlag, för alla testföretag och perioder."""
    namn = set()
    for fil in sorted((SCRIPTS.parent / "testdata").glob("*/*/underlag/*.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update([data["id"], data["motpart"], data["fakturanummer"]])
    return sorted(namn)


def namn_ur_testdatan_i_filer(filer, namnlista):
    """Var testdatans namn står i filerna, som hela ord, även i kommentarer och förklarande text."""
    monster = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, namnlista)) + r")(?![\w-])")
    fynd = []
    for fil in filer:
        for radnummer, rad in enumerate(fil.read_text(encoding="utf-8").splitlines(), start=1):
            fynd += [fil.name + ":" + str(radnummer) + " innehåller " + repr(traff.group(1))
                     for traff in monster.finditer(rad)]
    return fynd


def test_testdatans_underlag_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några underlag alls.
    namn = namn_i_testdatans_underlag()
    assert len(namn) > 60
    assert {"LEV-TE", "BUTIK-STAD", "SYNT-U-2025-004", "SYNT-TE-761"} <= set(namn)


def test_karnan_innehaller_inga_namn_fran_testdatans_underlag():
    """Motparter, fakturanummer och id hör till underlagen, inte till kärnan (gäller även las_underlag.py)."""
    assert UNDERLAGSMODULEN in karnans_filer()
    fynd = namn_ur_testdatan_i_filer(karnans_filer(), namn_i_testdatans_underlag())
    assert not fynd, "Namn från testdatans underlag i kärnan:\n" + "\n".join(fynd)


def test_testdatanamn_kontrollen_hittar_inbyggda_namn(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text('# dublett av SYNT-U-2025-003\nif motpart == "LEV-TE":\n    pass\nx = "LEV-TELE-2"\n',
                   encoding="utf-8")
    assert namn_ur_testdatan_i_filer([fil], namn_i_testdatans_underlag()) == [
        "x.py:1 innehåller 'SYNT-U-2025-003'", "x.py:2 innehåller 'LEV-TE'"]


def test_kassanamn_kontrollen_hittar_inbyggda_namn(tmp_path):
    """Skydd: kontrollen ovan ska verkligen slå larm när ett namn är inbyggt i koden."""
    fil = tmp_path / "x.py"
    fil.write_text(
        '"""Förklaring om moms och post."""\n'
        'def f(rad):\n'
        '    """Docstring om forsaljning."""\n'
        '    fel = "momsen stämmer inte"\n'
        '    if rad["post"] == "forsaljning":\n'
        '        return rad[f"{1}"]\n'
        '    # summa_brutto står i en kommentar\n',
        encoding="utf-8",
    )
    assert sorted(kassanamn_i_filer([fil], namn_i_kassaformaten())) == [
        "x.py:5 har textsträngen 'forsaljning'",
        "x.py:5 har textsträngen 'post'",
        "x.py:7 innehåller 'summa_brutto'",
    ]


# --- De gemensamma skydden i inlasning_skydd.py ---

def test_karnan_soker_aven_i_inlasning_skydd():
    # Skydd: alla sökningar ovan (företagsnamn, organisationsnummer, bankformatens kolumnnamn och
    # kassaformatens namn) går igenom karnans_filer(). Den gemensamma modulen ska vara en av dem.
    assert SCRIPTS / "inlasning_skydd.py" in karnans_filer()


def test_inlasning_skydd_namner_ingen_sorts_fil():
    """De gemensamma skydden vet inte vilken sorts fil de läser.

    Allt som skiljer bankfilen och Z-filen åt, som felklass och vad filen kallas, kommer in som en
    _Filsort från las_bank.py och las_kassa.py. Själva modulen får inte nämna bank, kassa eller
    Z-rapport någonstans, inte ens i kommentarer.
    """
    text = (SCRIPTS / "inlasning_skydd.py").read_text(encoding="utf-8").casefold()
    fynd = [ord for ord in ("bank", "kassa", "z-rapport", "z-fil") if ord in text]
    assert not fynd, "inlasning_skydd.py nämner " + ", ".join(map(repr, fynd))


# --- Matchningen mot banken ---

def namn_i_matchningsformaten():
    """Regelnamn och mönster ur alla företags matchning.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/matchning.json")):
        for regel in json.loads(fil.read_text(encoding="utf-8"))["kraver_inte_underlag"]:
            namn.add(regel["namn"])
            namn.update(regel[nyckel] for nyckel in ("referens_borjar_med", "beskrivning_borjar_med") if nyckel in regel)
    return sorted(namn)


def texter_i_testdatans_bankfiler():
    """Beskrivningar och referenser ur testdatans bankfiler, utan siffrorna sist (AVR-20250102 blir AVR).

    Kolumnernas namn hämtas ur företagets bankformat.json, så att testet inte heller har dem inbyggda.
    """
    import csv

    texter = set()
    for fil in sorted((SCRIPTS.parent / "testdata").glob("*/*/bank_*.csv")):
        kolumner = json.loads((FORETAG / fil.parent.parent.name / "bankformat.json").read_text(
            encoding="utf-8"))["kolumner"]
        with open(fil, encoding="utf-8", newline="") as csvfil:
            for rad in csv.DictReader(csvfil):
                for nyckel in ("referens", "beskrivning"):
                    text = re.sub(r"[\d\s-]+$", "", rad[kolumner[nyckel]])
                    if text:
                        texter.add(text)
    return sorted(texter)


def test_matchningen_och_bankfilerna_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några namn alls.
    assert {"kortinlosen", "bankavgift", "AVR-", "BET-SWISH INBETALNING", "BANK AVGIFT"} <= set(
        namn_i_matchningsformaten())
    assert {"AVR", "SWISH", "INS", "KORTKOP", "BET-KORT AVRAKNING", "KONTANTINSATTNING", "LEV-TELE", "SYNT-TE",
            "KORTKOP BUTIK-FORBRUKNING"} <= set(texter_i_testdatans_bankfiler())
    assert SCRIPTS / "matcha_bank.py" in karnans_filer() and SCRIPTS / "las_matchningsformat.py" in karnans_filer()


def test_karnan_innehaller_inga_bankradstexter_eller_regler_ur_matchningen():
    """Vilka bankrader som inte kräver underlag, och hur bankradernas texter ser ut, hör till företaget.

    Gäller hela kärnan, även matcha_bank.py och las_matchningsformat.py, och även kommentarer.
    """
    fynd = namn_ur_testdatan_i_filer(karnans_filer(), namn_i_matchningsformaten() + texter_i_testdatans_bankfiler())
    assert not fynd, "Regler ur matchning.json eller texter ur testdatans bankfiler i kärnan:\n" + "\n".join(fynd)


# --- Kontoplanen och momsfilen ---

def namn_i_kontoplanerna_och_momsfilerna():
    """Kontonummer och kontonamn ur alla företags kontoplan.json, och varugrupper ur alla momssatser.json."""
    namn = set()
    for fil in sorted(FORETAG.glob("*/kontoplan.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        for konto in data["konton"]:
            namn.update([konto["nummer"], konto["namn"]])
    for fil in sorted(FORETAG.glob("*/momssatser.json")):
        namn.update(json.loads(fil.read_text(encoding="utf-8"))["varugrupper"])
    return sorted(namn)


def satser_i_momsfilerna():
    """Alla momssatser större än 0 ur alla företags momssatser.json och kontoplanernas utgående moms."""
    satser = set()
    for fil in sorted(FORETAG.glob("*/momssatser.json")):
        for perioder in json.loads(fil.read_text(encoding="utf-8"))["varugrupper"].values():
            satser.update(period["sats"] for period in perioder)
    for fil in sorted(FORETAG.glob("*/kontoplan.json")):
        satser.update(map(int, json.loads(fil.read_text(encoding="utf-8"))["roller"]["utgaende_moms_per_sats"]))
    return sorted(satser - {0})


def satser_i_filer(filer, satser):
    """Var momssatserna står i filerna.

    - Ett tal i koden som är lika med en sats ger träff, till exempel sats = 25. Ett tal som är en
      gräns i en del av en text eller lista (text[:12]) är en längd, inte en momssats, och godtas.
    - En textsträng i koden som är exakt en sats ger träff, till exempel "12".
    - En sats med procenttecken efter ger träff var den än står, även i kommentarer, till exempel "12 %".
    """
    procent = re.compile(r"(?<![\d.,])(" + "|".join(map(str, satser)) + r")\s?%")
    fynd = []
    for fil in filer:
        kalla = fil.read_text(encoding="utf-8")
        trad = ast.parse(kalla)
        i_granser = {id(nod) for del_ in ast.walk(trad) if isinstance(del_, ast.Slice) for nod in ast.walk(del_)}
        for nod in ast.walk(trad):
            if not isinstance(nod, ast.Constant) or id(nod) in i_granser:
                continue
            if type(nod.value) in (int, float) and nod.value in satser:
                fynd.append(fil.name + ":" + str(nod.lineno) + " har talet " + repr(nod.value))
            elif isinstance(nod.value, str) and nod.value.strip() in map(str, satser):
                fynd.append(fil.name + ":" + str(nod.lineno) + " har textsträngen " + repr(nod.value))
        for radnummer, rad in enumerate(kalla.splitlines(), start=1):
            fynd += [fil.name + ":" + str(radnummer) + " innehåller " + repr(traff.group())
                     for traff in procent.finditer(rad)]
    return fynd


def test_kontoplanerna_och_momsfilerna_har_namn_och_satser_att_soka_efter():
    # Skydd mot att testerna nedan blir gröna för att de inte hittar några namn eller satser alls.
    assert {"1940", "2611", "Företagskonto", "Kassa", "livsmedel", "ovrigt", "momsfritt"} <= set(
        namn_i_kontoplanerna_och_momsfilerna())
    assert satser_i_momsfilerna() == [12, 25]
    assert {SCRIPTS / "las_kontoplan.py", SCRIPTS / "las_momssatser.py"} <= set(karnans_filer())


def test_karnan_innehaller_inga_konton_eller_varugrupper():
    """Kontonummer, kontonamn och varugrupper hör till företagets konfiguration (SPEC 2), inte till kärnan.

    Ett kontonummer har siffror och ger träff var det än står, även i kommentarer. Kontonamn och
    varugrupper ger träff som textsträngar i koden (som kassaformatens namn ovan), så att vanliga ord
    som "kassa" får stå i förklarande text.
    """
    fynd = kassanamn_i_filer(karnans_filer(), namn_i_kontoplanerna_och_momsfilerna(), set())
    assert not fynd, "Konton eller varugrupper från kontoplanen eller momsfilen i kärnan:\n" + "\n".join(fynd)


def test_karnan_innehaller_inga_momssatser():
    """Momssatserna hör till företagets momsfil (SPEC 2 och 11), inte till kärnan."""
    fynd = satser_i_filer(karnans_filer(), satser_i_momsfilerna())
    assert not fynd, "Momssatser i kärnan:\n" + "\n".join(fynd)


def test_konto_och_satskontrollerna_hittar_inbyggda_varden(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text(
        '"""Förklaring om kassa och livsmedel."""\n'
        'KONTO = "1940"\n'
        '# bokförs på 2611\n'
        'x = text[:12]\n'
        'sats = 25\n'
        'y = "moms 12 %"\n'
        'z = "Kassa"\n'
        'grupp = "livsmedel"\n'
        'w = 12.0\n'
        'v = "25"\n'
        'u = 1250\n',
        encoding="utf-8",
    )
    assert kassanamn_i_filer([fil], namn_i_kontoplanerna_och_momsfilerna(), set()) == [
        "x.py:2 har textsträngen '1940'", "x.py:7 har textsträngen 'Kassa'", "x.py:8 har textsträngen 'livsmedel'",
        "x.py:2 innehåller '1940'", "x.py:3 innehåller '2611'"]
    assert sorted(satser_i_filer([fil], satser_i_momsfilerna())) == [
        "x.py:10 har textsträngen '25'", "x.py:5 har talet 25", "x.py:6 innehåller '12 %'", "x.py:9 har talet 12.0"]


# --- Regelboken ---

def namn_i_regelbockerna():
    """Regel-id, motparter, kassaregister, regler i matchning.json, betalsätt, konton och ägare och närstående
    ur alla företags regelbok.json.

    Varugrupperna ur konteringen finns redan i kontrollen av momsfilerna. Källorna och typerna
    (till exempel "underlag" och "kvitto") och konteringens egna nycklar (till exempel "motkonto")
    är kärnans ord och tas inte med.
    """
    namn = set()
    for fil in sorted(FORETAG.glob("*/regelbok.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update(data.get("agare_och_narstaende", []))
        for regel in data["regler"]:
            namn.add(regel["id"])
            namn.update(varde for nyckel, varde in regel["galler"].items() if nyckel not in ("kalla", "typ"))
            kontering = regel["kontering"]
            if regel["galler"]["kalla"] == "z_rapport":
                namn.update(kontering["betalsatt"])
                namn.update(kontering["betalsatt"].values())
                namn.update(kontering["forsaljning"].values())
            else:
                namn.update(kontering.values())
    return sorted(namn)


def test_regelbockerna_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några namn alls.
    namn = set(namn_i_regelbockerna())
    assert {"R-LEV-TE", "R-Z-TB-KASSA-1", "R-BANK-AVGIFT", "LEV-TE", "RESTAURANG-1", "TB-KASSA-1", "bankavgift",
            "betalsatt_swish", "4010", "6570", "AGARE-1"} <= namn
    assert not namn & {"underlag", "kvitto", "leverantorsfaktura", "motkonto", "kostnad", "livsmedel"}
    assert REGELBOKSMODULEN in karnans_filer()


def test_karnan_innehaller_inga_namn_ur_regelbockerna():
    """Regler, motparter och konton hör till företagets regelbok (SPEC 2), inte till kärnan.

    Namnen söks som hela ord var de än står, även i kommentarer och förklarande text.
    """
    fynd = namn_ur_testdatan_i_filer(karnans_filer(), namn_i_regelbockerna())
    assert not fynd, "Namn ur regelboken i kärnan:\n" + "\n".join(fynd)


def test_regelbokskontrollen_hittar_inbyggda_namn(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text('# regeln R-BUTIK-STAD\nif regel["id"] == "R-LEV-KAFFE":\n    pass\nx = "R-LEV-TEX"\n'
                   'konto = "6071"\n', encoding="utf-8")
    assert namn_ur_testdatan_i_filer([fil], namn_i_regelbockerna()) == [
        "x.py:1 innehåller 'R-BUTIK-STAD'", "x.py:2 innehåller 'R-LEV-KAFFE'", "x.py:5 innehåller '6071'"]


def test_bankradstext_kontrollen_hittar_inbyggda_texter(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text('# kortinlosen kräver inget underlag\nif rad["referens"].startswith("AVR-"):\n    pass\n'
                   'x = "KONTANTINSATTNING"\ny = "BET-KORT AVRAKNING 2025-01-02"\nz = "AVRUNDA"\n', encoding="utf-8")
    namn = namn_i_matchningsformaten() + texter_i_testdatans_bankfiler()
    assert namn_ur_testdatan_i_filer([fil], namn) == [
        "x.py:1 innehåller 'kortinlosen'", "x.py:2 innehåller 'AVR-'", "x.py:4 innehåller 'KONTANTINSATTNING'",
        "x.py:5 innehåller 'BET-KORT AVRAKNING'"]


# --- Konteringsförslaget ---

def test_forslagsmodulen_provas_av_alla_kontroller():
    # Skydd: konteringsforslag.py är en kärnfil, så att alla sökningar i filen (företagsnamn, konton,
    # momssatser, kassaformatens, regelbökernas och testdatans namn) gäller den. Undantaget för
    # underlagets nycklar släpper bara igenom de nycklarna, och förslagets egna nycklar som också är
    # namn i kassaformaten är bara underlagets ord "datum".
    import konteringsforslag

    assert FORSLAGSMODULEN in karnans_filer() and FORSLAGSMODULEN in UNDERLAGETS_ANVANDARE
    egna = (set(konteringsforslag.FORSLAG_NYCKLAR) | set(konteringsforslag.VERIFIKATION_NYCKLAR)
            | set(konteringsforslag.RAD_NYCKLAR) | set(konteringsforslag.KOPPLINGAR_NYCKLAR)
            | {nyckel for nycklar, valfria in konteringsforslag.KALLOR.values() for nyckel in nycklar + valfria})
    assert egna & set(namn_i_kassaformaten()) == {"datum", "momssats"} <= UNDERLAGETS_EGNA_ORD
    assert kassanamn_i_filer([FORSLAGSMODULEN], namn_i_kassaformaten()) != []


# --- Flödena a, b och e (uppgift 4) ---

def test_flodena_provas_av_alla_kontroller():
    # Skydd: konteringsfloden.py är en kärnfil, så att alla sökningar ovan (företagsnamn, konton,
    # momssatser, kassaformatens, regelbökernas och testdatans namn och bankfilernas texter) gäller den.
    # Undantaget för underlagets nycklar släpper bara igenom underlagets egna ord, och utan undantaget
    # slår kontrollen larm på filen.
    assert FLODESMODULEN in karnans_filer() and FLODESMODULEN in UNDERLAGETS_ANVANDARE
    fynd = kassanamn_i_filer([FLODESMODULEN], namn_i_kassaformaten())
    assert fynd and all(fynd_.split(" har textsträngen ")[-1].strip("'") in UNDERLAGETS_EGNA_ORD for fynd_ in fynd)


def namn_i_regelbockernas_val():
    """Värdena i alla företags regelbok.json som hör till företaget och inte är kärnans egna ord.

    Stängda datum ur 'oppettider' och anteckningar. Valen i 'bokforing' (metod och datum) är kärnans
    ord (las_regelbok.METODER och VERIFIKATIONSDATUM) och tas inte med.
    """
    namn = set()
    for fil in sorted(FORETAG.glob("*/regelbok.json")):
        data = json.loads(fil.read_text(encoding="utf-8"))
        namn.update(data["oppettider"]["stangda_datum"])
        namn.update([data["foretag"], data["godkand"]["av"]])
    return sorted(namn)


def test_regelbockernas_val_har_namn_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar något alls.
    assert {"2025-01-06", "syntet-testbutik"} <= set(namn_i_regelbockernas_val())


def test_karnan_innehaller_inga_stangda_dagar_eller_foretagets_namn_ur_regelbockerna():
    """Vilka dagar företaget har stängt och vad det heter står i regelboken, aldrig i kärnan (K8:s varningssignal)."""
    fynd = namn_ur_testdatan_i_filer(karnans_filer(), namn_i_regelbockernas_val())
    assert not fynd, "Värden ur regelbökerna i kärnan:\n" + "\n".join(fynd)


def test_regelbockernas_val_ar_karnans_ord():
    # Valen i 'bokforing' är de som kärnan har byggda, inte företagets egna namn. Ett nytt värde i en
    # regelbok stoppas av las_regelbok, så kärnan kan aldrig behöva ett företags eget ord här.
    import las_regelbok

    for fil in sorted(FORETAG.glob("*/regelbok.json")):
        bokforing = json.loads(fil.read_text(encoding="utf-8"))["bokforing"]
        assert bokforing["metod"] in las_regelbok.METODER
        for nyckel, varde in bokforing["verifikationsdatum"].items():
            assert varde in las_regelbok.VERIFIKATIONSDATUM[nyckel]


def znummer_i_testdatans_kassafiler():
    """Alla Z-nummer i testdatans Z-filer, som heltal. Kolumnens namn hämtas ur företagets kassaformat.json."""
    import csv

    nummer = set()
    for fil in sorted((SCRIPTS.parent / "testdata").glob("*/*/kassa/*.csv")):
        kolumn = json.loads((FORETAG / fil.parents[2].name / "kassaformat.json").read_text(
            encoding="utf-8"))["kolumner"]["znummer"]
        with open(fil, encoding="utf-8", newline="") as csvfil:
            nummer.update(int(rad[kolumn]) for rad in csv.DictReader(csvfil))
    return sorted(nummer)


def referenser_i_testdatans_bankfiler():
    """Hela referenserna ur testdatans bankfiler, med siffrorna, till exempel AVR-20250102."""
    import csv

    referenser = set()
    for fil in sorted((SCRIPTS.parent / "testdata").glob("*/*/bank_*.csv")):
        kolumn = json.loads((FORETAG / fil.parents[1].name / "bankformat.json").read_text(
            encoding="utf-8"))["kolumner"]["referens"]
        with open(fil, encoding="utf-8", newline="") as csvfil:
            referenser.update(rad[kolumn] for rad in csv.DictReader(csvfil) if rad[kolumn])
    return sorted(referenser)


def test_testdatans_znummer_och_bankreferenser_finns_att_soka_efter():
    # Skydd mot att testet nedan blir grönt för att det inte hittar några Z-nummer eller referenser alls.
    znummer = znummer_i_testdatans_kassafiler()
    assert {1001, 1010, 1012} <= set(znummer) and 1011 not in znummer
    assert {"AVR-20250102", "INS-20250107", "AVG-2025-01", "SWISH-20250102-1", "SYNT-TE-761"} <= set(
        referenser_i_testdatans_bankfiler())


def test_karnan_innehaller_inga_znummer_eller_bankreferenser_ur_testdatan():
    """Ett förslag pekar på en Z-rapport eller en bankrad i perioderna, aldrig på en som är inbyggd i koden.

    Z-numren söks som tal och som textsträngar i koden, som momssatserna. Referenserna söks som hela
    ord var de än står, även i kommentarer och förklarande text.
    """
    fynd = satser_i_filer(karnans_filer(), znummer_i_testdatans_kassafiler())
    fynd += namn_ur_testdatan_i_filer(karnans_filer(), referenser_i_testdatans_bankfiler())
    assert not fynd, "Z-nummer eller bankreferenser ur testdatan i kärnan:\n" + "\n".join(fynd)


def test_znummer_och_referenskontrollen_hittar_inbyggda_varden(tmp_path):
    fil = tmp_path / "x.py"
    fil.write_text('Z = 1001\nx = "1012"\n# bankraden AVR-20250102\ny = text[:1010]\nz = "AVR-2025"\n',
                   encoding="utf-8")
    assert sorted(satser_i_filer([fil], znummer_i_testdatans_kassafiler())) == [
        "x.py:1 har talet 1001", "x.py:2 har textsträngen '1012'"]
    assert namn_ur_testdatan_i_filer([fil], referenser_i_testdatans_bankfiler()) == [
        "x.py:3 innehåller 'AVR-20250102'"]
