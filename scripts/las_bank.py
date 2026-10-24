"""Läser en bankfil (Swedbank-CSV) och kör kontroll K1, saldokedjan.

OBS: Kolumnlayouten nedan är ANTAGEN och INTE verifierad mot en riktig fil från Swedbank.
Den måste jämföras med en riktig export innan modulen används på riktiga underlag.

Antagna kolumner (rubrikraden måste innehålla alla, i valfri ordning):

    Radnummer, Bokföringsdag, Transaktionsdag, Referens, Beskrivning, Belopp, Bokfört saldo

Det här gör modulen:

- Teckenkodningen upptäcks automatiskt: först UTF-8 (med eller utan BOM), annars Windows-1252.
  En fil som bara innehåller vanliga engelska tecken är giltig i båda och läses då som UTF-8.
  En fil sparad som UTF-16 (börjar med BOM FF FE eller FE FF) stoppas med tydligt fel, liksom
  en fil som innehåller NUL-tecken (tecken nummer 0).
- Rader före rubrikraden hoppas över. Rubrikraden är den första raden som innehåller alla
  kolumnerna ovan.
- Avgränsaren (komma eller semikolon) upptäcks automatiskt på rubrikraden.
- Ett fält får inte innehålla radbrytning. CSV tillåter det inuti citattecken, men i en
  bankfil betyder det nästan alltid att ett citattecken i fel läge har slagit ihop flera
  transaktioner till en. Då stoppas filen.
- Radnumren ska vara 1, 2, 3 … i tur och ordning. Dubbla, osorterade eller saknade
  radnummer betyder att filen är trasig, och då stoppas den.
- Belopp tolkas med belopp.tolka_belopp och blir heltal i öre, aldrig flyttal.
- Varje rad får: id, bokforingsdag, transaktionsdag, referens, beskrivning, belopp_ore,
  saldo_efter_ore, kalla_fil (SHA-256 av hela filen) och radnr (värdet i kolumnen Radnummer).

K1 (saldokedjan): varje rads saldo ska vara föregående saldo plus radens belopp, där första
raden räknas från ingående saldo. Sista radens saldo ska dessutom vara lika med utgående saldo
(saldot vid periodens slut), som anroparen måste ange. Utan den kontrollen skulle en fil där de
sista raderna saknas kunna godkännas, eftersom kedjan stämmer för de rader som finns kvar.

Vid minsta fel stoppas hela filen: inga rader returneras, och ett BankfilFel kastas.
"""

import csv
import datetime as dt
import hashlib
import re

from belopp import formatera_ore, tolka_belopp

KOLUMNER = {
    "radnr": "Radnummer",
    "bokforingsdag": "Bokföringsdag",
    "transaktionsdag": "Transaktionsdag",
    "referens": "Referens",
    "beskrivning": "Beskrivning",
    "belopp": "Belopp",
    "saldo": "Bokfört saldo",
}

AVGRANSARE = [",", ";"]

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


# --- Inläsning ---

def _avkoda(data):
    """Returnerar filens text. Provar UTF-8 först och Windows-1252 sedan."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise BankfilFel(
            "Bankfilen stoppas: filen är sparad som UTF-16 (\"Unicode-text\"), som inte stöds."
            " Exportera filen från banken igen, eller spara den som UTF-8 eller CSV."
        )
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        raise BankfilFel(
            "Bankfilen stoppas: teckenkodningen är varken UTF-8 eller Windows-1252."
        ) from None


def _hitta_rubrikrad(rader):
    """Returnerar (index för rubrikraden, avgränsare, kolumnernas plats, antal kolumner)."""
    for index, rad in enumerate(rader):
        for avgransare in AVGRANSARE:
            try:
                falt = [f.strip() for f in next(csv.reader([rad], delimiter=avgransare), [])]
            except csv.Error:
                continue  # raden går inte att tolka, så den är ingen rubrikrad
            if all(namn in falt for namn in KOLUMNER.values()):
                dubbletter = [namn for namn in KOLUMNER.values() if falt.count(namn) > 1]
                if dubbletter:
                    raise BankfilFel(
                        "Bankfilen stoppas: rubrikraden (rad " + str(index + 1)
                        + " i filen) har kolumnen " + repr(dubbletter[0]) + " flera gånger."
                    )
                plats = {nyckel: falt.index(namn) for nyckel, namn in KOLUMNER.items()}
                return index, avgransare, plats, len(falt)
    raise BankfilFel(
        "Bankfilen stoppas: hittar ingen rubrikrad med kolumnerna "
        + ", ".join(KOLUMNER.values()) + "."
    )


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


def _tolka_rader(data):
    """Tolkar bankfilens innehåll (bytes) till rader. Kör INTE K1.

    Använd las_bankfil, som alltid kör K1. Den här funktionen finns separat bara för att
    testerna ska kunna räkna rader i en fil som K1 stoppar.
    """
    kalla_fil = hashlib.sha256(data).hexdigest()
    textrader = _avkoda(data).splitlines(keepends=True)
    for index, rad in enumerate(textrader):
        if "\x00" in rad:
            raise BankfilFel(
                "Bankfilen stoppas: rad " + str(index + 1) + " i filen innehåller ett NUL-tecken"
                " (tecken nummer 0). Filen är troligen trasig eller sparad i fel format."
            )
    rubrik_index, avgransare, plats, antal_kolumner = _hitta_rubrikrad(textrader)

    resultat = []
    lasare = csv.reader(textrader[rubrik_index + 1:], delimiter=avgransare)
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
            "bokforingsdag": _tolka_datum(varde["bokforingsdag"], KOLUMNER["bokforingsdag"], var),
            "transaktionsdag": _tolka_datum(varde["transaktionsdag"], KOLUMNER["transaktionsdag"], var),
            "referens": varde["referens"],
            "beskrivning": varde["beskrivning"],
            "belopp_ore": _tolka_ore(varde["belopp"], KOLUMNER["belopp"], var),
            "saldo_efter_ore": _tolka_ore(varde["saldo"], KOLUMNER["saldo"], var),
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


def las_bankfil(sokvag, ingaende_saldo_ore, utgaende_saldo_ore):
    """Läser en bankfil och kör K1. Returnerar raderna bara om allt stämmer, annars BankfilFel.

    Ingående och utgående saldo är heltal i öre, till exempel från kontoutdraget.
    """
    with open(sokvag, "rb") as fil:
        data = fil.read()
    rader = _tolka_rader(data)
    kontrollera_k1(rader, ingaende_saldo_ore, utgaende_saldo_ore)
    return rader
