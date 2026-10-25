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
- Andra styrtecken än tabb och vanliga radslut (\\n, \\r), samt de ovanliga radbrytningarna
  U+2028 och U+2029, stoppar filen var de än står. Flera av dem kan annars få raderna att delas
  fel så att flera transaktioner slås ihop till en.
- Rader före rubrikraden hoppas över. Rubrikraden är den första raden som innehåller alla
  kolumnerna i bankformatet, i valfri ordning.
- Avgränsaren upptäcks automatiskt på rubrikraden, bland dem som bankformatet tillåter.
  Bankformatet får bara använda komma, semikolon, tabb och lodstreck.
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

Skydden för teckenkodning, styrtecken, CSV-läsning och bankformat.json är gemensamma med andra
filer och ligger i inlasning_skydd.py. Felmeddelandena är bankfilens egna (BANKFIL).

Vid minsta fel stoppas hela filen: inga rader returneras, och ett BankfilFel kastas.
"""

import hashlib

from belopp import formatera_ore
from inlasning_skydd import (
    HELTAL, Filsort, avkoda, csv_rader, inga_dubbla_kolumnnamn, inga_otillatna_tecken,
    kontrollera_anteckning, kontrollera_avgransare, kontrollera_namn, kontrollera_nycklar, ladda_json, las_fil,
    nul_fel, rubrikens_falt, tolka_datum, tolka_ore,
)

# Uppgifterna som kärnan behöver ur varje rad. Bankformatet anger vad kolumnen för varje
# uppgift heter i bankfilen.
KOLUMN_NYCKLAR = (
    "radnr", "bokforingsdag", "transaktionsdag", "referens", "beskrivning", "belopp", "saldo",
)

# Nycklar i bankformat.json. "anteckning" är fri text för människor och används inte i koden.
BANKFORMAT_NYCKLAR = ("kolumner", "avgransare")
BANKFORMAT_VALFRIA_NYCKLAR = ("anteckning",)


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


# Det som skiljer bankfilens felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
# Avgränsarna (TILLATNA_AVGRANSARE) och styrtecknen som stoppar filen ligger också där.
BANKFIL = Filsort(
    fel=BankfilFel,
    filen="Bankfilen",
    formatet="Bankformatet",
    exportera_igen="Exportera filen från banken igen",
    om_styrtecken="Sådana tecken finns inte i en vanlig bankfil, och de kan få raderna att delas fel"
                  " så att flera transaktioner slås ihop till en.",
    ihopslaget="flera transaktioner",
    nivaer="Ett bankformat har bara två nivåer.",
)


def kronor(ore):
    """123456 -> "1234,56 kr"."""
    return formatera_ore(ore) + " kr"


# --- Bankformat ---

def _kontrollera_bankformat(data, var):
    """Kontrollerar ett bankformat och returnerar det i den form kärnan använder."""
    kontrollera_nycklar(data, BANKFORMAT_NYCKLAR, BANKFORMAT_VALFRIA_NYCKLAR, var, BANKFIL)
    kontrollera_anteckning(data, var, BANKFIL)

    kontrollera_nycklar(data["kolumner"], KOLUMN_NYCKLAR, (), var + ", 'kolumner',", BANKFIL)
    kolumner = {
        nyckel: kontrollera_namn(data["kolumner"][nyckel], "kolumnnamnet för " + repr(nyckel), var, BANKFIL,
                                 "ett kolumnnamn")
        for nyckel in KOLUMN_NYCKLAR
    }
    inga_dubbla_kolumnnamn(kolumner, var, BANKFIL)
    avgransare = kontrollera_avgransare(data["avgransare"], kolumner, var, BANKFIL)

    return {"kolumner": kolumner, "avgransare": avgransare}


def ladda_bankformat(sokvag):
    """Läser och kontrollerar ett företags bankformat.json. Fel ger BankfilFel.

    Returnerar {"kolumner": {nyckel: kolumnnamn}, "avgransare": [tecken, ...]}.
    """
    innehall, var = ladda_json(sokvag, BANKFIL)
    return _kontrollera_bankformat(innehall, var)


# --- Inläsning ---

def _hitta_rubrikrad(rader, giltig_utf8, bankformat):
    """Returnerar (index för rubrikraden, avgränsare, kolumnernas plats, antal kolumner)."""
    kolumner = bankformat["kolumner"]
    for index, rad in enumerate(rader):
        rubrik = rubrikens_falt(rad, bankformat["avgransare"], kolumner)
        if rubrik:
            avgransare, falt = rubrik
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
    text, giltig_utf8 = avkoda(data, BANKFIL)
    textrader = text.splitlines(keepends=True)
    for index, rad in enumerate(textrader):
        if "\x00" in rad:
            raise nul_fel(index + 1, BANKFIL)
    inga_otillatna_tecken(text, BANKFIL)
    rubrik_index, avgransare, plats, antal_kolumner = _hitta_rubrikrad(textrader, giltig_utf8, bankformat)

    resultat = []
    for _, var, falt in csv_rader(textrader[rubrik_index + 1:], rubrik_index + 2, avgransare, antal_kolumner,
                                  BANKFIL):
        varde = {nyckel: falt[index].strip() for nyckel, index in plats.items()}

        if not HELTAL.fullmatch(varde["radnr"]):
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
            "bokforingsdag": tolka_datum(varde["bokforingsdag"], kolumner["bokforingsdag"], var, BANKFIL),
            "transaktionsdag": tolka_datum(varde["transaktionsdag"], kolumner["transaktionsdag"], var, BANKFIL),
            "referens": varde["referens"],
            "beskrivning": varde["beskrivning"],
            "belopp_ore": tolka_ore(varde["belopp"], kolumner["belopp"], var, BANKFIL),
            "saldo_efter_ore": tolka_ore(varde["saldo"], kolumner["saldo"], var, BANKFIL),
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
    data = las_fil(sokvag, BANKFIL)
    rader = _tolka_rader(data, bankformat)
    kontrollera_k1(rader, ingaende_saldo_ore, utgaende_saldo_ore)
    return rader
