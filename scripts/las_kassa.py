"""Läser kassans Z-rapporter (CSV) och kontrollerar dem.

En Z-rapport är kassans dagsavslut: försäljningen per momssats, momsen, hur kunderna betalade och
totalsumman. Varje Z-rapport har ett löpnummer, Z-numret, som ökar med ett för varje rapport.

Z-filens format (filnamn, kolumnnamn, avgränsare, postnamn och momsavrundning) är inte inbyggt
här. Det beskrivs per företag i foretag/<namn>/kassaformat.json och läses med ladda_kassaformat.
Kärnan vet bara vilka uppgifter som behövs och vilka sorters poster som finns:

- försäljning per momssats (inklusive moms),
- moms per momssats,
- betalsätt (ett eller flera, till exempel kontant och kort),
- totalsumma för dagen.

OBS: Formatet för testföretaget är ANTAGET och INTE verifierat mot en riktig exportfil från
något kassasystem (Ö5).

Inläsningen skyddas på samma sätt som bankfilen i las_bank.py: teckenkodningen upptäcks (UTF-8,
annars Windows-1252, UTF-16 och NUL-tecken stoppas), styrtecken och ovanliga radbrytningar stoppar
filen, radbrytning inuti ett fält stoppar filen, CSV läses strikt och varje rad ska ha lika många
fält som rubrikraden. Beloppen tolkas med belopp.tolka_belopp och blir heltal i öre, aldrig flyttal.
Till skillnad från bankfilen ska rubrikraden vara filens första rad.

Varje Z-fil kontrolleras internt varje gång den läses (Z-kontroll a–e):

  a) datumet på varje rad stämmer med datumet i filnamnet,
  b) alla rader har samma Z-nummer och samma kassaregister,
  c) försäljningen per momssats summerar till totalsumman,
  d) betalsätten summerar till totalsumman,
  e) momsen per sats stämmer med försäljningen och satsen, avrundad enligt kassaformatet.

kontrollera_z_serien kontrollerar flera Z-rapporter över en period: Z-numren för varje
kassaregister ska följa på varandra utan luckor och utan dubbletter, och datumen får inte gå
bakåt när Z-numret ökar.

Vid minsta fel stoppas hela filen: inga rader returneras, och ett KassafilFel kastas.
"""

import csv
import datetime as dt
import hashlib
import json
import re
import unicodedata

from belopp import tolka_belopp
from las_bank import (
    TILLATNA_AVGRANSARE, BankfilFel, _DATUM, _HELTAL, _OTILLATNA_TECKEN, _RADBRYTNINGAR, _RADSLUT,
    _inga_dubbla_nycklar, kronor,
)

# Uppgifterna som kärnan behöver ur varje rad. Kassaformatet anger vad kolumnen för varje
# uppgift heter i Z-filen.
KOLUMN_NYCKLAR = ("rapportdatum", "znummer", "kassaregister", "postnamn", "sats", "belopp")

# Sorterna av poster. Kassaformatet anger vad posterna heter i Z-filen. Försäljning och moms har
# en rad per momssats. Betalsätten är en lista med ett postnamn per betalsätt.
POSTTYPER = ("forsaljning_per_sats", "moms_per_sats", "betalsatt", "totalsumma")
POSTTYPER_MED_SATS = ("forsaljning_per_sats", "moms_per_sats")

# Nycklar i kassaformat.json. "anteckning" är fri text för människor och används inte i koden.
KASSAFORMAT_NYCKLAR = ("filnamn", "kolumner", "avgransare", "poster", "momsavrundning")
KASSAFORMAT_VALFRIA_NYCKLAR = ("anteckning",)

# Platsen för datumet i filnamnsmönstret, till exempel "z_ÅÅÅÅ-MM-DD.csv".
DATUMPLATS = "ÅÅÅÅ-MM-DD"

# Sätt att avrunda momsen som kärnan känner till. "narmaste_ore": momsen är försäljningen ×
# sats / (100 + sats), avrundad till närmaste öre. Ligger det exakta värdet precis mitt emellan
# två ören godtas båda, eftersom testdatan inte visar vilket håll kassan avrundar åt då.
MOMSAVRUNDNINGAR = ("narmaste_ore",)


class KassafilFel(Exception):
    """Z-filen kunde inte läsas in. Hela filen är stoppad."""


class ZKontrollFel(KassafilFel):
    """En av Z-rapportens interna kontroller (a–e) slog larm. Hela filen är stoppad."""

    def __init__(self, meddelande, kontroll):
        super().__init__(meddelande)
        self.kontroll = kontroll


class ZSerieFel(KassafilFel):
    """Z-serien har en lucka, en dubblett eller datum i fel ordning.

    typ är "lucka", "dubblett" eller "ordning". saknade_znummer och dagar_utan_rapport är
    ifyllda vid lucka: vilka Z-nummer som saknas och vilka dagar mellan rapporterna före och
    efter luckan som saknar Z-rapport.
    """

    def __init__(self, meddelande, typ, kassaregister, znummer, saknade_znummer=(), dagar_utan_rapport=()):
        super().__init__(meddelande)
        self.typ = typ
        self.kassaregister = kassaregister
        self.znummer = list(znummer)
        self.saknade_znummer = list(saknade_znummer)
        self.dagar_utan_rapport = list(dagar_utan_rapport)


# --- Kassaformat ---

def _kontrollera_nycklar(data, obligatoriska, valfria, var):
    if not isinstance(data, dict):
        raise KassafilFel(var + " ska vara ett objekt med nycklar, inte " + type(data).__name__ + ".")
    saknas = [nyckel for nyckel in obligatoriska if nyckel not in data]
    if saknas:
        raise KassafilFel(var + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in data if nyckel not in obligatoriska + valfria)
    if okanda:
        raise KassafilFel(
            var + " har en okänd nyckel: " + ", ".join(map(repr, okanda)) + ". Tillåtna nycklar är "
            + ", ".join(map(repr, obligatoriska + valfria)) + "."
        )


def _kontrollera_namn(namn, vad, var):
    """Kontrollerar ett kolumnnamn eller postnamn och returnerar det utan mellanslag runt om."""
    if not isinstance(namn, str) or not namn.strip():
        raise KassafilFel(var + ": " + vad + " får inte vara tomt.")
    if any(tecken in namn for tecken in _RADBRYTNINGAR + '"'):
        raise KassafilFel(var + ": " + vad + " får inte innehålla radbrytning eller citattecken.")
    osynliga = [tecken for tecken in namn if unicodedata.category(tecken) in ("Cc", "Cf")]
    if osynliga:
        raise KassafilFel(
            var + ": " + vad + " innehåller tecknet U+" + format(ord(osynliga[0]), "04X")
            + ", som är ett styrtecken eller ett osynligt tecken. Sådana tecken får inte finnas i ett namn."
        )
    return namn.strip()


def _kontrollera_filnamn(monster, var):
    if not isinstance(monster, str):
        raise KassafilFel(var + ": 'filnamn' ska vara text, till exempel \"z_" + DATUMPLATS + ".csv\".")
    if monster.count(DATUMPLATS) != 1:
        raise KassafilFel(
            var + ": 'filnamn' ska innehålla " + repr(DATUMPLATS) + " exakt en gång, där datumet står i filnamnet."
        )
    if any(tecken in monster for tecken in "/\\") or monster.startswith("."):
        raise KassafilFel(var + ": 'filnamn' ska vara ett filnamn, utan mapp och utan punkt först.")
    if any(unicodedata.category(tecken) in ("Cc", "Cf") or tecken in _RADBRYTNINGAR for tecken in monster):
        raise KassafilFel(var + ": 'filnamn' innehåller ett styrtecken eller ett osynligt tecken.")
    return monster


def _kontrollera_kassaformat(data, var):
    """Kontrollerar ett kassaformat och returnerar det i den form kärnan använder."""
    _kontrollera_nycklar(data, KASSAFORMAT_NYCKLAR, KASSAFORMAT_VALFRIA_NYCKLAR, var)
    if "anteckning" in data and not isinstance(data["anteckning"], str):
        raise KassafilFel(var + ": 'anteckning' ska vara text.")

    filnamn = _kontrollera_filnamn(data["filnamn"], var)

    _kontrollera_nycklar(data["kolumner"], KOLUMN_NYCKLAR, (), var + ", 'kolumner',")
    kolumner = {
        nyckel: _kontrollera_namn(data["kolumner"][nyckel], "kolumnnamnet för " + repr(nyckel), var)
        for nyckel in KOLUMN_NYCKLAR
    }
    for nyckel, namn in kolumner.items():
        andra = [annan for annan, annat_namn in kolumner.items() if annat_namn == namn and annan != nyckel]
        if andra:
            raise KassafilFel(
                var + ": kolumnnamnet " + repr(namn) + " används för både " + repr(nyckel)
                + " och " + repr(andra[0]) + ". Varje kolumn måste ha ett eget namn."
            )

    avgransare = data["avgransare"]
    if not isinstance(avgransare, list) or not avgransare:
        raise KassafilFel(var + ": 'avgransare' ska vara en lista med minst en avgränsare.")
    for tecken in avgransare:
        if not isinstance(tecken, str) or tecken not in TILLATNA_AVGRANSARE:
            raise KassafilFel(
                var + ": avgränsaren " + repr(tecken) + " är ogiltig. Tillåtna avgränsare är komma,"
                " semikolon, tabb och lodstreck (" + ", ".join(map(repr, TILLATNA_AVGRANSARE)) + ")."
            )
    if len(set(avgransare)) != len(avgransare):
        raise KassafilFel(var + ": samma avgränsare står flera gånger i 'avgransare'.")
    if any(tecken in namn for tecken in avgransare for namn in kolumner.values()):
        raise KassafilFel(var + ": ett kolumnnamn innehåller en av avgränsarna.")

    _kontrollera_nycklar(data["poster"], POSTTYPER, (), var + ", 'poster',")
    poster = {}
    for posttyp in POSTTYPER:
        if posttyp == "betalsatt":
            lista = data["poster"][posttyp]
            if not isinstance(lista, list) or not lista:
                raise KassafilFel(var + ": 'betalsatt' under 'poster' ska vara en lista med minst ett postnamn.")
            poster[posttyp] = [
                _kontrollera_namn(namn, "postnamnet för betalsätt nummer " + str(nummer), var)
                for nummer, namn in enumerate(lista, start=1)
            ]
        else:
            poster[posttyp] = _kontrollera_namn(data["poster"][posttyp], "postnamnet för " + repr(posttyp), var)
    alla_postnamn = [poster[posttyp] for posttyp in POSTTYPER if posttyp != "betalsatt"] + poster["betalsatt"]
    for namn in alla_postnamn:
        if alla_postnamn.count(namn) > 1:
            raise KassafilFel(
                var + ": postnamnet " + repr(namn) + " står flera gånger under 'poster'. Varje post måste ha ett eget namn."
            )

    if data["momsavrundning"] not in MOMSAVRUNDNINGAR:
        raise KassafilFel(
            var + ": 'momsavrundning' är " + repr(data["momsavrundning"]) + ", men kärnan känner bara till "
            + ", ".join(map(repr, MOMSAVRUNDNINGAR)) + "."
        )

    return {
        "filnamn": filnamn,
        "kolumner": kolumner,
        "avgransare": list(avgransare),
        "poster": poster,
        "momsavrundning": data["momsavrundning"],
    }


def ladda_kassaformat(sokvag):
    """Läser och kontrollerar ett företags kassaformat.json. Fel ger KassafilFel.

    Returnerar {"filnamn": mönster, "kolumner": {nyckel: kolumnnamn}, "avgransare": [tecken, ...],
    "poster": {posttyp: postnamn, "betalsatt": [postnamn, ...]}, "momsavrundning": sätt}.
    """
    var = "Kassaformatet i " + str(sokvag)
    try:
        with open(sokvag, "rb") as fil:
            data = fil.read()
    except FileNotFoundError:
        raise KassafilFel("Kassaformatet saknas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise KassafilFel("Kassaformatet saknas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise KassafilFel(
            "Kassaformatet går inte att läsa: " + str(sokvag) + " (" + (fel.strerror or str(fel)) + ")."
        ) from None
    try:
        innehall = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_inga_dubbla_nycklar)
    except UnicodeDecodeError:
        raise KassafilFel(var + " är inte sparat som UTF-8.") from None
    except json.JSONDecodeError as fel:
        raise KassafilFel(
            var + " är inte giltig JSON (rad " + str(fel.lineno) + ", tecken " + str(fel.colno) + ")."
        ) from None
    except BankfilFel as fel:  # dubbla nycklar, från _inga_dubbla_nycklar
        raise KassafilFel(var + ": " + str(fel) + ".") from None
    except RecursionError:
        raise KassafilFel(
            var + " är inte giltigt: för många hakparenteser eller klammerparenteser inuti varandra."
            " Ett kassaformat har bara tre nivåer. Filen är troligen trasig."
        ) from None
    return _kontrollera_kassaformat(innehall, var)


# --- Inläsning ---

def _avkoda(data):
    """Returnerar filens text. Provar UTF-8 först och Windows-1252 sedan."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise KassafilFel(
            "Kassafilen stoppas: filen är sparad som UTF-16 (\"Unicode-text\"), som inte stöds."
            " Exportera Z-rapporten från kassan igen, eller spara den som UTF-8 eller CSV."
        )
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        raise KassafilFel("Kassafilen stoppas: teckenkodningen är varken UTF-8 eller Windows-1252.") from None


def _inga_otillatna_tecken(text):
    """Stoppar filen om den innehåller NUL, ett annat styrtecken än tabb, \\n och \\r, eller U+2028/U+2029."""
    if "\x00" in text:
        filrad = len(_RADSLUT.findall(text, 0, text.index("\x00"))) + 1
        raise KassafilFel(
            "Kassafilen stoppas: rad " + str(filrad) + " i filen innehåller ett NUL-tecken"
            " (tecken nummer 0). Filen är troligen trasig eller sparad i fel format."
        )
    fynd = _OTILLATNA_TECKEN.search(text)
    if fynd:
        filrad = len(_RADSLUT.findall(text, 0, fynd.start())) + 1
        raise KassafilFel(
            "Kassafilen stoppas: rad " + str(filrad) + " i filen innehåller tecknet U+"
            + format(ord(fynd.group()), "04X") + ", som är ett styrtecken eller en ovanlig radbrytning."
            + " Sådana tecken finns inte i en vanlig Z-rapport, och de kan få raderna att delas fel."
        )


def _las_rubrikrad(rad, kassaformat):
    """Returnerar (avgränsare, kolumnernas plats, antal kolumner) för filens första rad."""
    kolumner = kassaformat["kolumner"]
    for avgransare in kassaformat["avgransare"]:
        try:
            falt = [f.strip() for f in next(csv.reader([rad], delimiter=avgransare), [])]
        except csv.Error:
            continue
        if all(namn in falt for namn in kolumner.values()):
            dubbletter = [namn for namn in kolumner.values() if falt.count(namn) > 1]
            if dubbletter:
                raise KassafilFel(
                    "Kassafilen stoppas: rubrikraden har kolumnen " + repr(dubbletter[0]) + " flera gånger."
                )
            return avgransare, {nyckel: falt.index(namn) for nyckel, namn in kolumner.items()}, len(falt)
    raise KassafilFel(
        "Kassafilen stoppas: första raden i filen ska vara en rubrikrad med kolumnerna "
        + ", ".join(kolumner.values()) + "."
    )


def _tolka_datum(text, kolumn, var):
    if _DATUM.fullmatch(text):
        try:
            dt.date.fromisoformat(text)
            return text
        except ValueError:
            pass
    raise KassafilFel(var + " har ett ogiltigt datum i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")


def _tolka_ore(text, kolumn, var):
    try:
        return tolka_belopp(text)
    except ValueError:
        raise KassafilFel(var + " har ett ogiltigt belopp i kolumnen " + repr(kolumn) + ": " + repr(text) + ".") from None


def _tolka_heltal(text, kolumn, var):
    if not _HELTAL.fullmatch(text):
        raise KassafilFel(var + " har ett ogiltigt heltal i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")
    return int(text)


def _csv_fel(fel, var):
    """Översätter ett fel från csv-läsaren till ett KassafilFel med svenskt meddelande."""
    if "field larger than field limit" in str(fel):
        return KassafilFel(
            var + " har ett fält som är längre än " + str(csv.field_size_limit()) + " tecken. Filen är troligen trasig."
        )
    return KassafilFel(
        var + " kan inte tolkas som CSV, till exempel på grund av ett citattecken i fel läge."
        + " Teknisk detalj: " + str(fel) + "."
    )


def _rad_id(rad):
    """Stabilt id som bara beror på radens innehåll, inte på filens kodning eller avgränsare."""
    delar = [
        rad["kassaregister"], str(rad["znummer"]), rad["rapportdatum"], rad["postnamn"],
        "" if rad["sats"] is None else str(rad["sats"]), str(rad["belopp_ore"]),
    ]
    return "KASSA-" + hashlib.sha256("\x1f".join(delar).encode("utf-8")).hexdigest()[:16]


def _posttyper(kassaformat):
    """{postnamn: posttyp} enligt kassaformatet."""
    poster = kassaformat["poster"]
    typer = {poster[posttyp]: posttyp for posttyp in POSTTYPER if posttyp != "betalsatt"}
    typer.update({namn: "betalsatt" for namn in poster["betalsatt"]})
    return typer


def _tolka_kassarader(data, kassaformat):
    """Tolkar Z-filens innehåll (bytes) till rader. Kör INTE Z-kontrollerna a–e; det gör las_kassafil."""
    kolumner = kassaformat["kolumner"]
    posttyper = _posttyper(kassaformat)
    kalla_fil = hashlib.sha256(data).hexdigest()
    text = _avkoda(data)
    _inga_otillatna_tecken(text)
    textrader = text.splitlines(keepends=True)
    if not textrader:
        raise KassafilFel("Kassafilen stoppas: filen är tom.")
    avgransare, plats, antal_kolumner = _las_rubrikrad(textrader[0], kassaformat)

    resultat = []
    sedda = {}  # (postnamn, sats) -> filrad, för att hitta poster som står två gånger
    # strict=True: text direkt efter ett citerat fält, som "X"Y, stoppar filen.
    lasare = csv.reader(textrader[1:], delimiter=avgransare, strict=True)
    lasta_rader = 0
    while True:
        filrad = 2 + lasta_rader  # raden i filen där posten börjar
        var = "Kassafilen stoppas: rad " + str(filrad) + " i filen"
        try:
            falt = next(lasare)
        except StopIteration:
            break
        except csv.Error as fel:
            raise _csv_fel(fel, var) from None
        lasta_rader = lasare.line_num
        if not falt or all(not f.strip() for f in falt):
            continue  # tom rad
        for index, faltet in enumerate(falt):
            if any(tecken in faltet for tecken in _RADBRYTNINGAR):
                raise KassafilFel(
                    var + " har en radbrytning inuti fält nummer " + str(index + 1)
                    + ". Det beror troligen på ett citattecken i fel läge, som kan slå ihop flera rader till en."
                )
        if len(falt) != antal_kolumner:
            raise KassafilFel(var + " har " + str(len(falt)) + " fält, men rubrikraden har " + str(antal_kolumner) + ".")
        varde = {nyckel: falt[index].strip() for nyckel, index in plats.items()}

        postnamn = varde["postnamn"]
        if postnamn not in posttyper:
            raise KassafilFel(
                var + " har en okänd post i kolumnen " + repr(kolumner["postnamn"]) + ": " + repr(postnamn)
                + ". Kända poster enligt kassaformatet är " + ", ".join(map(repr, posttyper)) + "."
            )
        posttyp = posttyper[postnamn]
        if posttyp in POSTTYPER_MED_SATS:
            sats = _tolka_heltal(varde["sats"], kolumner["sats"], var)
        elif varde["sats"]:
            raise KassafilFel(
                var + ": posten " + repr(postnamn) + " ska inte ha någon momssats, men kolumnen "
                + repr(kolumner["sats"]) + " innehåller " + repr(varde["sats"]) + "."
            )
        else:
            sats = None
        if not varde["kassaregister"]:
            raise KassafilFel(var + " saknar kassaregister i kolumnen " + repr(kolumner["kassaregister"]) + ".")
        nyckel = (postnamn, sats)
        if nyckel in sedda:
            raise KassafilFel(
                var + ": posten " + repr(postnamn) + ("" if sats is None else " för momssatsen " + str(sats) + " %")
                + " står redan på rad " + str(sedda[nyckel]) + ". Varje post får bara finnas en gång."
            )
        sedda[nyckel] = filrad

        rad = {
            "rapportdatum": _tolka_datum(varde["rapportdatum"], kolumner["rapportdatum"], var),
            "znummer": _tolka_heltal(varde["znummer"], kolumner["znummer"], var),
            "kassaregister": varde["kassaregister"],
            "postnamn": postnamn,
            "posttyp": posttyp,
            "sats": sats,
            "belopp_ore": _tolka_ore(varde["belopp"], kolumner["belopp"], var),
            "kalla_fil": kalla_fil,
            "filrad": filrad,
        }
        rad["id"] = _rad_id(rad)
        resultat.append({nyckel: rad[nyckel] for nyckel in (
            "id", "rapportdatum", "znummer", "kassaregister", "postnamn", "posttyp", "sats",
            "belopp_ore", "kalla_fil", "filrad",
        )})

    if not resultat:
        raise KassafilFel("Kassafilen stoppas: filen har en rubrikrad men inga poster.")
    totaler = [rad for rad in resultat if rad["posttyp"] == "totalsumma"]
    if not totaler:
        raise KassafilFel(
            "Kassafilen stoppas: posten " + repr(kassaformat["poster"]["totalsumma"]) + " (totalsumman) saknas."
        )
    return resultat


# --- Z-kontroll a–e ---

def _summa(rader, posttyp):
    return sum(rad["belopp_ore"] for rad in rader if rad["posttyp"] == posttyp)


def _per_sats(rader, posttyp):
    return {rad["sats"]: rad["belopp_ore"] for rad in rader if rad["posttyp"] == posttyp}


def _totalsumma(rader):
    return [rad["belopp_ore"] for rad in rader if rad["posttyp"] == "totalsumma"][0]


def _datum_i_filnamnet(filnamn, kassaformat):
    """Läser ut datumet ur filnamnet enligt kassaformatets mönster. Fel ger ZKontrollFel (a)."""
    fore, efter = kassaformat["filnamn"].split(DATUMPLATS)
    traff = re.fullmatch(re.escape(fore) + r"(\d{4}-\d{2}-\d{2})" + re.escape(efter), filnamn, re.ASCII)
    if traff:
        try:
            dt.date.fromisoformat(traff.group(1))
            return traff.group(1)
        except ValueError:
            pass
    raise ZKontrollFel(
        "Z-kontroll a: filnamnet " + repr(filnamn) + " följer inte mönstret " + repr(kassaformat["filnamn"])
        + " med ett giltigt datum, så datumet i filen kan inte jämföras med filnamnet. Hela filen är stoppad.",
        "a",
    )


def _kontroll_a_datum(rader, filnamn, kassaformat):
    """a) Datumet på varje rad stämmer med datumet i filnamnet."""
    datum = _datum_i_filnamnet(filnamn, kassaformat)
    for rad in rader:
        if rad["rapportdatum"] != datum:
            raise ZKontrollFel(
                "Z-kontroll a: rad " + str(rad["filrad"]) + " i filen har datumet " + rad["rapportdatum"]
                + ", men filnamnet " + repr(filnamn) + " säger " + datum + ". Hela filen är stoppad.",
                "a",
            )


def _kontroll_b_samma_rapport(rader):
    """b) Alla rader har samma Z-nummer och samma kassaregister."""
    forsta = rader[0]
    for rad in rader[1:]:
        if rad["znummer"] != forsta["znummer"]:
            raise ZKontrollFel(
                "Z-kontroll b: rad " + str(rad["filrad"]) + " i filen har Z-nummer " + str(rad["znummer"])
                + ", men rad " + str(forsta["filrad"]) + " har Z-nummer " + str(forsta["znummer"])
                + ". En Z-fil ska innehålla exakt en Z-rapport. Hela filen är stoppad.",
                "b",
            )
        if rad["kassaregister"] != forsta["kassaregister"]:
            raise ZKontrollFel(
                "Z-kontroll b: rad " + str(rad["filrad"]) + " i filen har kassaregistret " + repr(rad["kassaregister"])
                + ", men rad " + str(forsta["filrad"]) + " har " + repr(forsta["kassaregister"])
                + ". En Z-fil ska innehålla exakt en Z-rapport. Hela filen är stoppad.",
                "b",
            )


def _kontroll_c_forsaljning(rader, kassaformat):
    """c) Försäljningen per momssats summerar till totalsumman."""
    forsaljning = _summa(rader, "forsaljning_per_sats")
    total = _totalsumma(rader)
    if forsaljning != total:
        raise ZKontrollFel(
            "Z-kontroll c: försäljningen per momssats (posten " + repr(kassaformat["poster"]["forsaljning_per_sats"])
            + ") summerar till " + kronor(forsaljning) + ", men totalsumman (posten "
            + repr(kassaformat["poster"]["totalsumma"]) + ") är " + kronor(total) + ", skillnad "
            + kronor(forsaljning - total) + ". Hela filen är stoppad.",
            "c",
        )


def _kontroll_d_betalsatt(rader, kassaformat):
    """d) Betalsätten summerar till totalsumman. Ett betalsätt som saknas i filen räknas som 0."""
    betalt = _summa(rader, "betalsatt")
    total = _totalsumma(rader)
    if betalt != total:
        raise ZKontrollFel(
            "Z-kontroll d: betalsätten (" + ", ".join(map(repr, kassaformat["poster"]["betalsatt"]))
            + ") summerar till " + kronor(betalt) + ", men totalsumman (posten "
            + repr(kassaformat["poster"]["totalsumma"]) + ") är " + kronor(total) + ", skillnad "
            + kronor(betalt - total) + ". Hela filen är stoppad.",
            "d",
        )


def momsen_i_brutto(brutto_ore, sats, momsavrundning):
    """De momsbelopp i öre som är rätt för försäljningen brutto_ore (inklusive moms) och satsen.

    Den exakta momsen är brutto × sats / (100 + sats). Med "narmaste_ore" avrundas den till
    närmaste öre. Ligger den exakt mitt emellan två ören returneras båda.
    """
    if momsavrundning not in MOMSAVRUNDNINGAR:
        raise KassafilFel("Okänd momsavrundning: " + repr(momsavrundning) + ".")
    tecken = -1 if brutto_ore < 0 else 1
    hela, rest = divmod(abs(brutto_ore) * sats, 100 + sats)
    if rest * 2 < 100 + sats:
        kandidater = [hela]
    elif rest * 2 > 100 + sats:
        kandidater = [hela + 1]
    else:
        kandidater = [hela, hela + 1]
    return [tecken * ore for ore in kandidater]


def _kontroll_e_moms(rader, kassaformat):
    """e) Momsen per sats stämmer med försäljningen och satsen. En sats som saknas räknas som 0."""
    forsaljning = _per_sats(rader, "forsaljning_per_sats")
    moms = _per_sats(rader, "moms_per_sats")
    for sats in sorted(set(forsaljning) | set(moms)):
        brutto = forsaljning.get(sats, 0)
        faktisk = moms.get(sats, 0)
        ratt = momsen_i_brutto(brutto, sats, kassaformat["momsavrundning"])
        if faktisk not in ratt:
            raise ZKontrollFel(
                "Z-kontroll e: momsen för momssatsen " + str(sats) + " % (posten "
                + repr(kassaformat["poster"]["moms_per_sats"]) + ") är " + kronor(faktisk)
                + ", men försäljningen " + kronor(brutto) + " ger " + " eller ".join(map(kronor, ratt))
                + " (" + str(sats) + "/" + str(100 + sats) + " av försäljningen, avrundat till närmaste öre)"
                + ", skillnad " + kronor(faktisk - ratt[0]) + ". Hela filen är stoppad.",
                "e",
            )


def kontrollera_z_rapport(rader, filnamn, kassaformat):
    """Z-kontroll a–e för raderna i en Z-fil. Kastar ZKontrollFel vid första felet."""
    if not rader:
        raise KassafilFel("Kassafilen stoppas: det finns inga rader att kontrollera.")
    _kontroll_a_datum(rader, filnamn, kassaformat)
    _kontroll_b_samma_rapport(rader)
    _kontroll_c_forsaljning(rader, kassaformat)
    _kontroll_d_betalsatt(rader, kassaformat)
    _kontroll_e_moms(rader, kassaformat)


def las_kassafil(sokvag, kassaformat):
    """Läser EN Z-fil och kör Z-kontroll a–e. Returnerar raderna bara om allt stämmer.

    Kassaformatet kommer från ladda_kassaformat och kontrolleras igen här, så att ett trasigt
    format aldrig används. Varje rad har: id, rapportdatum, znummer, kassaregister, postnamn
    (som i filen), posttyp (en av POSTTYPER), sats (heltal i procent, eller None), belopp_ore,
    kalla_fil (SHA-256 av hela filen) och filrad (raden i filen).
    """
    kassaformat = _kontrollera_kassaformat(kassaformat, "Kassaformatet")
    try:
        with open(sokvag, "rb") as fil:
            data = fil.read()
    except FileNotFoundError:
        raise KassafilFel("Kassafilen stoppas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise KassafilFel("Kassafilen stoppas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise KassafilFel(
            "Kassafilen stoppas: filen " + str(sokvag) + " går inte att läsa (" + (fel.strerror or str(fel)) + ")."
        ) from None
    rader = _tolka_kassarader(data, kassaformat)
    filnamn = str(sokvag).replace("\\", "/").rsplit("/", 1)[-1]
    kontrollera_z_rapport(rader, filnamn, kassaformat)
    return rader


# --- Z-serien över en period ---

def _rapportens_huvud(rader):
    """(kassaregister, znummer, rapportdatum, kalla_fil) för en Z-rapport från las_kassafil."""
    if not rader:
        raise KassafilFel("Z-serien: en av Z-rapporterna har inga rader.")
    forsta = rader[0]
    huvud = (forsta["kassaregister"], forsta["znummer"], forsta["rapportdatum"], forsta["kalla_fil"])
    if any((rad["kassaregister"], rad["znummer"], rad["rapportdatum"], rad["kalla_fil"]) != huvud for rad in rader):
        raise KassafilFel(
            "Z-serien: raderna för Z-rapport " + str(forsta["znummer"]) + " kommer inte från en och samma Z-fil."
        )
    return huvud


def _dagar_mellan(fran, till):
    """Datumen efter fran och före till, som text."""
    dag = dt.date.fromisoformat(fran) + dt.timedelta(days=1)
    slut = dt.date.fromisoformat(till)
    dagar = []
    while dag < slut:
        dagar.append(dag.isoformat())
        dag += dt.timedelta(days=1)
    return dagar


def kontrollera_z_serien(rapporter):
    """Kontrollerar Z-serien över en period. rapporter är en lista med raderna från las_kassafil, en per Z-fil.

    För varje kassaregister ska Z-numren följa på varandra utan luckor och utan dubbletter, och
    datumet får inte gå bakåt när Z-numret ökar. Kastar ZSerieFel vid första felet.

    OBS: Kontrollen ser bara luckor mellan rapporterna som finns. Saknas periodens första eller
    sista Z-rapport syns det inte här.
    """
    per_register = {}
    for rader in rapporter:
        kassaregister, znummer, datum, kalla_fil = _rapportens_huvud(rader)
        per_register.setdefault(kassaregister, []).append((znummer, datum, kalla_fil))

    for kassaregister in sorted(per_register):
        serie = sorted(per_register[kassaregister])
        datum_med_rapport = {datum for _, datum, _ in serie}
        for (z_fore, datum_fore, fil_fore), (z_efter, datum_efter, fil_efter) in zip(serie, serie[1:]):
            if z_efter == z_fore:
                orsak = ("samma fil är inläst två gånger" if fil_fore == fil_efter
                         else "två olika filer har samma Z-nummer")
                raise ZSerieFel(
                    "Z-serien för kassaregistret " + repr(kassaregister) + " har en dubblett: Z-rapport "
                    + str(z_fore) + " finns två gånger, daterad " + datum_fore + " och " + datum_efter
                    + " (" + orsak + ").",
                    "dubblett", kassaregister, [z_fore],
                )
            if z_efter > z_fore + 1:
                saknade = list(range(z_fore + 1, z_efter))
                dagar = [dag for dag in _dagar_mellan(datum_fore, datum_efter) if dag not in datum_med_rapport]
                if len(saknade) == 1:
                    vad = "Z-rapport " + str(saknade[0]) + " saknas"
                else:
                    vad = "Z-rapport " + str(saknade[0]) + "–" + str(saknade[-1]) + " (" + str(len(saknade)) + " st) saknas"
                raise ZSerieFel(
                    "Z-serien för kassaregistret " + repr(kassaregister) + " har en lucka: " + vad
                    + " mellan Z-rapport " + str(z_fore) + " (" + datum_fore + ") och Z-rapport "
                    + str(z_efter) + " (" + datum_efter + "). "
                    + ("Dagar däremellan utan Z-rapport: " + ", ".join(dagar) + "." if dagar else
                       "Den saknade rapporten är från " + datum_fore + " eller " + datum_efter + ".")
                    + " Hämta den saknade Z-rapporten från kassan.",
                    "lucka", kassaregister, [z_fore, z_efter], saknade, dagar,
                )
            if datum_efter < datum_fore:
                raise ZSerieFel(
                    "Z-serien för kassaregistret " + repr(kassaregister) + " går bakåt i tiden: Z-rapport "
                    + str(z_efter) + " är daterad " + datum_efter + ", men Z-rapport " + str(z_fore)
                    + " före den är daterad " + datum_fore + ".",
                    "ordning", kassaregister, [z_fore, z_efter],
                )


def summa_per_momssats(rapporter):
    """Försäljning per momssats för flera Z-rapporter: {sats: {"brutto_ore", "moms_ore", "netto_ore"}}."""
    summor = {}
    for rader in rapporter:
        for rad in rader:
            if rad["posttyp"] == "forsaljning_per_sats":
                summor.setdefault(rad["sats"], {"brutto_ore": 0, "moms_ore": 0})["brutto_ore"] += rad["belopp_ore"]
            elif rad["posttyp"] == "moms_per_sats":
                summor.setdefault(rad["sats"], {"brutto_ore": 0, "moms_ore": 0})["moms_ore"] += rad["belopp_ore"]
    return {
        sats: {**summor[sats], "netto_ore": summor[sats]["brutto_ore"] - summor[sats]["moms_ore"]}
        for sats in sorted(summor)
    }
