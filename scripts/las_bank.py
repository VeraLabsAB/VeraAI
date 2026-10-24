"""Läser en bankfil (CSV) och kör kontroll K1, saldokedjan.

Bankfilens format (kolumnnamn och tillåtna avgränsare) är inte inbyggt här. Det beskrivs per
företag i foretag/<namn>/bankformat.json och läses med ladda_bankformat. Kärnan vet bara vilka
uppgifter som behövs: radnummer, bokföringsdag, transaktionsdag, referens, beskrivning, belopp och
saldo efter transaktionen. Bankformatet säger vad kolumnerna heter i just det företagets bankfil.

OBS: Formatet för testföretaget är ANTAGET och INTE verifierat mot en riktig exportfil från
banken (Ö5). Det måste jämföras med en riktig export innan modulen används på riktiga underlag.

Det här gör modulen:

- Teckenkodningen upptäcks automatiskt: först UTF-8 (med eller utan BOM), annars Windows-1252.
  En fil som bara innehåller vanliga engelska tecken är giltig i båda och läses då som UTF-8.
  En fil sparad som UTF-16 (börjar med BOM FF FE eller FE FF) stoppas med tydligt fel, liksom
  en fil som innehåller NUL-tecken (tecken nummer 0).
- Rader före rubrikraden hoppas över. Rubrikraden är den första raden som innehåller alla
  kolumnerna i bankformatet, i valfri ordning.
- Avgränsaren upptäcks automatiskt på rubrikraden, bland dem som bankformatet tillåter.
- Ett fält får inte innehålla radbrytning. CSV tillåter det inuti citattecken, men i en
  bankfil betyder det nästan alltid att ett citattecken i fel läge har slagit ihop flera
  transaktioner till en. Då stoppas filen.
- Radnumren ska vara 1, 2, 3 … i tur och ordning. Dubbla, osorterade eller saknade
  radnummer betyder att filen är trasig, och då stoppas den.
- Beloppen tolkas med belopp.tolka_belopp och blir heltal i öre, aldrig flyttal.
- Varje rad får: id, bokforingsdag, transaktionsdag, referens, beskrivning, belopp_ore,
  saldo_efter_ore, kalla_fil (SHA-256 av hela filen) och radnr (värdet i radnummerkolumnen).

K1 (saldokedjan): varje rads saldo ska vara föregående saldo plus radens belopp, där första
raden räknas från ingående saldo. Sista radens saldo ska dessutom vara lika med utgående saldo
(saldot vid periodens slut), som anroparen måste ange. Utan den kontrollen skulle en fil där de
sista raderna saknas kunna godkännas, eftersom kedjan stämmer för de rader som finns kvar.

Vid minsta fel stoppas hela filen: inga rader returneras, och ett BankfilFel kastas.
"""

import csv
import datetime as dt
import hashlib
import json
import re

from belopp import formatera_ore, tolka_belopp

# Uppgifterna som kärnan behöver ur varje rad. Bankformatet anger vad kolumnen för varje
# uppgift heter i bankfilen.
KOLUMN_NYCKLAR = (
    "radnr", "bokforingsdag", "transaktionsdag", "referens", "beskrivning", "belopp", "saldo",
)

# Nycklar i bankformat.json. "anteckning" är fri text för människor och används inte i koden.
BANKFORMAT_NYCKLAR = ("kolumner", "avgransare")
BANKFORMAT_VALFRIA_NYCKLAR = ("anteckning",)

_DATUM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
_HELTAL = re.compile(r"\d+", re.ASCII)

# Radbrytningar som inte får finnas inuti ett fält: \n, \r, U+2028 och U+2029.
_RADBRYTNINGAR = "\n\r\u2028\u2029"


class BankfilFel(Exception):
    """Bankfilen kunde inte läsas in. Hela filen är stoppad."""


class K1Fel(BankfilFel):
    """Saldokedjan stämmer inte. Hela filen är stoppad."""

    def __init__(self, meddelande, radnr, forvantat_ore, faktiskt_ore):
        super().__init__(meddelande)
        self.radnr = radnr
        self.forvantat_ore = forvantat_ore
        self.faktiskt_ore = faktiskt_ore
        self.skillnad_ore = faktiskt_ore - forvantat_ore


def kronor(ore):
    """123456 -> "1234,56 kr"."""
    return formatera_ore(ore) + " kr"


# --- Bankformat ---

def _kontrollera_nycklar(data, obligatoriska, valfria, var):
    if not isinstance(data, dict):
        raise BankfilFel(var + " ska vara ett objekt med nycklar, inte " + type(data).__name__ + ".")
    saknas = [nyckel for nyckel in obligatoriska if nyckel not in data]
    if saknas:
        raise BankfilFel(var + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in data if nyckel not in obligatoriska + valfria)
    if okanda:
        raise BankfilFel(
            var + " har en okänd nyckel: " + ", ".join(map(repr, okanda)) + ". Tillåtna nycklar är "
            + ", ".join(map(repr, obligatoriska + valfria)) + "."
        )


def _kontrollera_bankformat(data, var):
    """Kontrollerar ett bankformat och returnerar det i den form kärnan använder."""
    _kontrollera_nycklar(data, BANKFORMAT_NYCKLAR, BANKFORMAT_VALFRIA_NYCKLAR, var)
    if "anteckning" in data and not isinstance(data["anteckning"], str):
        raise BankfilFel(var + ": 'anteckning' ska vara text.")

    _kontrollera_nycklar(data["kolumner"], KOLUMN_NYCKLAR, (), var + ", 'kolumner',")
    kolumner = {}
    for nyckel in KOLUMN_NYCKLAR:
        namn = data["kolumner"][nyckel]
        if not isinstance(namn, str) or not namn.strip():
            raise BankfilFel(var + ": kolumnnamnet för " + repr(nyckel) + " får inte vara tomt.")
        if any(tecken in namn for tecken in _RADBRYTNINGAR + '"'):
            raise BankfilFel(
                var + ": kolumnnamnet för " + repr(nyckel) + " får inte innehålla radbrytning eller citattecken."
            )
        kolumner[nyckel] = namn.strip()
    for nyckel, namn in kolumner.items():
        andra = [annan for annan, annat_namn in kolumner.items() if annat_namn == namn and annan != nyckel]
        if andra:
            raise BankfilFel(
                var + ": kolumnnamnet " + repr(namn) + " används för både " + repr(nyckel)
                + " och " + repr(andra[0]) + ". Varje kolumn måste ha ett eget namn."
            )

    avgransare = data["avgransare"]
    if not isinstance(avgransare, list) or not avgransare:
        raise BankfilFel(var + ": 'avgransare' ska vara en lista med minst en avgränsare.")
    for tecken in avgransare:
        if not isinstance(tecken, str) or len(tecken) != 1 or tecken in _RADBRYTNINGAR + '" ':
            raise BankfilFel(
                var + ": avgränsaren " + repr(tecken) + " är ogiltig. Varje avgränsare ska vara ett"
                " enda tecken, och inte mellanslag, citattecken eller radbrytning."
            )
    if len(set(avgransare)) != len(avgransare):
        raise BankfilFel(var + ": samma avgränsare står flera gånger i 'avgransare'.")
    if any(tecken in namn for tecken in avgransare for namn in kolumner.values()):
        raise BankfilFel(var + ": ett kolumnnamn innehåller en av avgränsarna.")

    return {"kolumner": kolumner, "avgransare": list(avgransare)}


def _inga_dubbla_nycklar(par):
    objekt = {}
    for nyckel, varde in par:
        if nyckel in objekt:
            raise BankfilFel("nyckeln " + repr(nyckel) + " står flera gånger")
        objekt[nyckel] = varde
    return objekt


def ladda_bankformat(sokvag):
    """Läser och kontrollerar ett företags bankformat.json. Fel ger BankfilFel.

    Returnerar {"kolumner": {nyckel: kolumnnamn}, "avgransare": [tecken, ...]}.
    """
    var = "Bankformatet i " + str(sokvag)
    try:
        with open(sokvag, "rb") as fil:
            data = fil.read()
    except FileNotFoundError:
        raise BankfilFel("Bankformatet saknas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise BankfilFel("Bankformatet saknas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise BankfilFel(
            "Bankformatet går inte att läsa: " + str(sokvag) + " (" + (fel.strerror or str(fel)) + ")."
        ) from None
    try:
        innehall = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_inga_dubbla_nycklar)
    except UnicodeDecodeError:
        raise BankfilFel(var + " är inte sparat som UTF-8.") from None
    except json.JSONDecodeError as fel:
        raise BankfilFel(
            var + " är inte giltig JSON (rad " + str(fel.lineno) + ", tecken " + str(fel.colno) + ")."
        ) from None
    except BankfilFel as fel:
        raise BankfilFel(var + ": " + str(fel) + ".") from None
    return _kontrollera_bankformat(innehall, var)


# --- Inläsning ---

def _avkoda(data):
    """Returnerar (filens text, True om den var giltig UTF-8). Provar UTF-8 först och Windows-1252 sedan."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise BankfilFel(
            "Bankfilen stoppas: filen är sparad som UTF-16 (\"Unicode-text\"), som inte stöds."
            " Exportera filen från banken igen, eller spara den som UTF-8 eller CSV."
        )
    try:
        return data.decode("utf-8-sig"), True
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252"), False
    except UnicodeDecodeError:
        raise BankfilFel(
            "Bankfilen stoppas: teckenkodningen är varken UTF-8 eller Windows-1252."
        ) from None


def _hitta_rubrikrad(rader, giltig_utf8, bankformat):
    """Returnerar (index för rubrikraden, avgränsare, kolumnernas plats, antal kolumner)."""
    kolumner = bankformat["kolumner"]
    for index, rad in enumerate(rader):
        for avgransare in bankformat["avgransare"]:
            try:
                falt = [f.strip() for f in next(csv.reader([rad], delimiter=avgransare), [])]
            except csv.Error:
                continue  # raden går inte att tolka, så den är ingen rubrikrad
            if all(namn in falt for namn in kolumner.values()):
                dubbletter = [namn for namn in kolumner.values() if falt.count(namn) > 1]
                if dubbletter:
                    raise BankfilFel(
                        "Bankfilen stoppas: rubrikraden (rad " + str(index + 1)
                        + " i filen) har kolumnen " + repr(dubbletter[0]) + " flera gånger."
                    )
                plats = {nyckel: falt.index(namn) for nyckel, namn in kolumner.items()}
                return index, avgransare, plats, len(falt)
    meddelande = (
        "Bankfilen stoppas: hittar ingen rubrikrad med kolumnerna "
        + ", ".join(kolumner.values()) + "."
    )
    if not giltig_utf8:
        meddelande += (
            " Filen är inte giltig UTF-8 och lästes därför som Windows-1252. Teckenkodningen kan"
            " vara orsaken, till exempel en UTF-8-fil med en trasig byte, så att \"ö\" i"
            " kolumnnamnen inte känns igen."
        )
    raise BankfilFel(meddelande)


def _tolka_datum(text, kolumn, plats):
    if not _DATUM.fullmatch(text):
        raise BankfilFel(plats + " har ett ogiltigt datum i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")
    try:
        dt.date.fromisoformat(text)
    except ValueError:
        raise BankfilFel(plats + " har ett ogiltigt datum i kolumnen " + repr(kolumn) + ": " + repr(text) + ".") from None
    return text


def _tolka_ore(text, kolumn, plats):
    try:
        return tolka_belopp(text)
    except ValueError:
        raise BankfilFel(plats + " har ett ogiltigt belopp i kolumnen " + repr(kolumn) + ": " + repr(text) + ".") from None


def _csv_fel(fel, var):
    """Översätter ett fel från csv-läsaren till ett BankfilFel med svenskt meddelande."""
    if "field larger than field limit" in str(fel):
        return BankfilFel(
            var + " har ett fält som är längre än " + str(csv.field_size_limit())
            + " tecken. Filen är troligen trasig."
        )
    return BankfilFel(
        var + " kan inte tolkas som CSV, till exempel på grund av ett citattecken i fel läge."
        + " Teknisk detalj: " + str(fel) + "."
    )


def _rad_id(rad):
    """Stabilt id som bara beror på radens innehåll, inte på filens kodning eller avgränsare."""
    delar = [
        str(rad["radnr"]), rad["bokforingsdag"], rad["transaktionsdag"], rad["referens"],
        rad["beskrivning"], str(rad["belopp_ore"]), str(rad["saldo_efter_ore"]),
    ]
    return "BANK-" + hashlib.sha256("\x1f".join(delar).encode("utf-8")).hexdigest()[:16]


def _tolka_rader(data, bankformat):
    """Tolkar bankfilens innehåll (bytes) till rader enligt ett kontrollerat bankformat. Kör INTE K1.

    Använd las_bankfil, som alltid kör K1. Den här funktionen finns separat bara för att
    testerna ska kunna räkna rader i en fil som K1 stoppar. Ett test (F11) stoppar annan kod i
    scripts/ från att använda den.
    """
    kolumner = bankformat["kolumner"]
    kalla_fil = hashlib.sha256(data).hexdigest()
    text, giltig_utf8 = _avkoda(data)
    textrader = text.splitlines(keepends=True)
    for index, rad in enumerate(textrader):
        if "\x00" in rad:
            raise BankfilFel(
                "Bankfilen stoppas: rad " + str(index + 1) + " i filen innehåller ett NUL-tecken"
                " (tecken nummer 0). Filen är troligen trasig eller sparad i fel format."
            )
    rubrik_index, avgransare, plats, antal_kolumner = _hitta_rubrikrad(textrader, giltig_utf8, bankformat)

    resultat = []
    # strict=True: text direkt efter ett citerat fält, som "REF"X, stoppar filen i stället för
    # att tyst läsas som REFX.
    lasare = csv.reader(textrader[rubrik_index + 1:], delimiter=avgransare, strict=True)
    lasta_rader = 0  # antal textrader efter rubriken som läsaren har gått igenom
    while True:
        filrad = rubrik_index + 2 + lasta_rader  # raden i filen där posten börjar
        var = "Bankfilen stoppas: rad " + str(filrad) + " i filen"
        try:
            falt = next(lasare)
        except StopIteration:
            break
        except csv.Error as fel:
            raise _csv_fel(fel, var) from None
        lasta_rader = lasare.line_num
        if not falt or all(not f.strip() for f in falt):
            continue  # tom rad
        for index, text in enumerate(falt):
            if any(tecken in text for tecken in _RADBRYTNINGAR):
                raise BankfilFel(
                    var + " har en radbrytning inuti fält nummer " + str(index + 1)
                    + ". Det beror troligen på ett citattecken i fel läge, som kan slå ihop"
                    + " flera transaktioner till en."
                )
        if len(falt) != antal_kolumner:
            raise BankfilFel(
                var + " har " + str(len(falt)) + " fält, men rubrikraden har " + str(antal_kolumner) + "."
            )
        varde = {nyckel: falt[index].strip() for nyckel, index in plats.items()}

        if not _HELTAL.fullmatch(varde["radnr"]):
            raise BankfilFel(var + " har ett ogiltigt radnummer: " + repr(varde["radnr"]) + ".")
        forvantat_radnr = len(resultat) + 1
        if int(varde["radnr"]) != forvantat_radnr:
            raise BankfilFel(
                var + " har radnummer " + str(int(varde["radnr"])) + ", men nästa radnummer ska vara "
                + str(forvantat_radnr) + ". Radnumren ska vara 1, 2, 3 … i tur och ordning, utan"
                + " dubbletter eller luckor."
            )

        rad = {
            "radnr": int(varde["radnr"]),
            "bokforingsdag": _tolka_datum(varde["bokforingsdag"], kolumner["bokforingsdag"], var),
            "transaktionsdag": _tolka_datum(varde["transaktionsdag"], kolumner["transaktionsdag"], var),
            "referens": varde["referens"],
            "beskrivning": varde["beskrivning"],
            "belopp_ore": _tolka_ore(varde["belopp"], kolumner["belopp"], var),
            "saldo_efter_ore": _tolka_ore(varde["saldo"], kolumner["saldo"], var),
            "kalla_fil": kalla_fil,
        }
        rad["id"] = _rad_id(rad)
        resultat.append({nyckel: rad[nyckel] for nyckel in (
            "id", "bokforingsdag", "transaktionsdag", "referens", "beskrivning",
            "belopp_ore", "saldo_efter_ore", "kalla_fil", "radnr",
        )})

    if not resultat:
        raise BankfilFel("Bankfilen stoppas: filen har en rubrikrad men inga transaktionsrader.")
    return resultat


# --- K1, saldokedjan ---

def _kontrollera_heltal(varde, namn):
    if isinstance(varde, bool) or not isinstance(varde, int):
        raise TypeError(namn + " måste vara ett heltal i öre, inte " + type(varde).__name__ + ".")


def kontrollera_k1(rader, ingaende_saldo_ore, utgaende_saldo_ore):
    """Kontroll K1. Kastar K1Fel vid första felet. Returnerar inget om allt stämmer."""
    _kontrollera_heltal(ingaende_saldo_ore, "Ingående saldo")
    _kontrollera_heltal(utgaende_saldo_ore, "Utgående saldo")
    if not rader:
        raise BankfilFel("Bankfilen stoppas: det finns inga rader att kontrollera.")

    saldo = ingaende_saldo_ore
    for rad in rader:
        _kontrollera_heltal(rad["belopp_ore"], "Beloppet på radnummer " + str(rad["radnr"]))
        _kontrollera_heltal(rad["saldo_efter_ore"], "Saldot på radnummer " + str(rad["radnr"]))
        forvantat = saldo + rad["belopp_ore"]
        faktiskt = rad["saldo_efter_ore"]
        if faktiskt != forvantat:
            raise K1Fel(
                "K1 saldokedjan: fel på radnummer " + str(rad["radnr"])
                + ". Förväntat saldo " + kronor(forvantat)
                + ", faktiskt saldo " + kronor(faktiskt)
                + ", skillnad " + kronor(faktiskt - forvantat)
                + ". Hela filen är stoppad och ingen rad har lästs in.",
                rad["radnr"], forvantat, faktiskt,
            )
        saldo = faktiskt

    # Kedjan ovan stämmer även om de sista raderna saknas. Därför jämförs sista radens saldo
    # med det utgående saldot som anroparen har angett.
    sista = rader[-1]
    if sista["saldo_efter_ore"] != utgaende_saldo_ore:
        raise K1Fel(
            "K1 saldokedjan: sista radens saldo (radnummer " + str(sista["radnr"]) + ") är "
            + kronor(sista["saldo_efter_ore"]) + ", men utgående saldo ska vara "
            + kronor(utgaende_saldo_ore) + ", skillnad "
            + kronor(sista["saldo_efter_ore"] - utgaende_saldo_ore)
            + ". Filen kan sakna rader, eller så är det angivna utgående saldot fel."
            + " Hela filen är stoppad och ingen rad har lästs in.",
            sista["radnr"], utgaende_saldo_ore, sista["saldo_efter_ore"],
        )


def las_bankfil(sokvag, bankformat, ingaende_saldo_ore, utgaende_saldo_ore):
    """Läser en bankfil och kör K1. Returnerar raderna bara om allt stämmer, annars BankfilFel.

    Bankformatet kommer från ladda_bankformat och kontrolleras igen här, så att ett trasigt
    format aldrig används. Ingående och utgående saldo är heltal i öre, till exempel från
    kontoutdraget.
    """
    bankformat = _kontrollera_bankformat(bankformat, "Bankformatet")
    try:
        with open(sokvag, "rb") as fil:
            data = fil.read()
    except FileNotFoundError:
        raise BankfilFel("Bankfilen stoppas: filen finns inte: " + str(sokvag) + ".") from None
    except IsADirectoryError:
        raise BankfilFel("Bankfilen stoppas: " + str(sokvag) + " är en mapp, inte en fil.") from None
    except OSError as fel:
        raise BankfilFel(
            "Bankfilen stoppas: filen " + str(sokvag) + " går inte att läsa (" + (fel.strerror or str(fel)) + ")."
        ) from None
    rader = _tolka_rader(data, bankformat)
    kontrollera_k1(rader, ingaende_saldo_ore, utgaende_saldo_ore)
    return rader
