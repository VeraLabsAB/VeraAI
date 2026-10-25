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
- Riktningstecknen U+202A–U+202E och U+2066–U+2069 stoppar filen var de än står (I3). De är
  osynliga och kan få en beskrivning att visas som en annan text än den är.
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

Resultatet är en Bankperiod, som inte går att ändra: raderna och periodens ingående och utgående
saldo. Den kan bara skapas av las_bankfil och sla_ihop_bankperioder (en nyckel som bara de har),
och raderna ges som nya kopior varje gång de läses. Annars skulle annan kod kunna ta bort en rad
efter inläsningen, och raden skulle aldrig bli ett ärende i matchningen. sla_ihop_bankperioder
sätter ihop flera månader till en Bankperiod, och kontrollerar då att varje månads ingående saldo
är förra månadens utgående och att ingen bankrad finns två gånger.
"""

import hashlib
from types import MappingProxyType

from belopp import formatera_ore
from inlasning_skydd import (
    _HELTAL, _Filsort, _avkoda, _csv_rader, _filrad_for, _inga_dubbla_kolumnnamn, _inga_otillatna_tecken,
    _kontrollera_anteckning, _kontrollera_avgransare, _kontrollera_namn, _kontrollera_nycklar, _ladda_json, _las_fil,
    _nul_fel, _rubrikens_falt, _tolka_datum, _tolka_ore,
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
# Avgränsarna (_TILLATNA_AVGRANSARE) och styrtecknen som stoppar filen ligger också där.
BANKFIL = _Filsort(
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
    _kontrollera_nycklar(data, BANKFORMAT_NYCKLAR, BANKFORMAT_VALFRIA_NYCKLAR, var, BANKFIL)
    _kontrollera_anteckning(data, var, BANKFIL)

    _kontrollera_nycklar(data["kolumner"], KOLUMN_NYCKLAR, (), var + ", 'kolumner',", BANKFIL)
    kolumner = {
        nyckel: _kontrollera_namn(data["kolumner"][nyckel], "kolumnnamnet för " + repr(nyckel), var, BANKFIL,
                                 "ett kolumnnamn")
        for nyckel in KOLUMN_NYCKLAR
    }
    _inga_dubbla_kolumnnamn(kolumner, var, BANKFIL)
    avgransare = _kontrollera_avgransare(data["avgransare"], kolumner, var, BANKFIL)

    return {"kolumner": kolumner, "avgransare": avgransare}


def ladda_bankformat(sokvag):
    """Läser och kontrollerar ett företags bankformat.json. Fel ger BankfilFel.

    Returnerar {"kolumner": {nyckel: kolumnnamn}, "avgransare": [tecken, ...]}.
    """
    innehall, var = _ladda_json(sokvag, BANKFIL)
    return _kontrollera_bankformat(innehall, var)


# --- Inläsning ---

def _hitta_rubrikrad(rader, giltig_utf8, bankformat):
    """Returnerar (index för rubrikraden, avgränsare, kolumnernas plats, antal kolumner)."""
    kolumner = bankformat["kolumner"]
    for index, rad in enumerate(rader):
        rubrik = _rubrikens_falt(rad, bankformat["avgransare"], kolumner)
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
    text, giltig_utf8 = _avkoda(data, BANKFIL)
    # Radnumret räknas som i en textredigerare (_filrad_for), på samma sätt som för Z-filen. Andra
    # tecken som Python räknar som radslut, till exempel \x0c, stoppas strax efter.
    if "\x00" in text:
        raise _nul_fel(_filrad_for(text, text.index("\x00")), BANKFIL)
    _inga_otillatna_tecken(text, BANKFIL)
    textrader = text.splitlines(keepends=True)
    rubrik_index, avgransare, plats, antal_kolumner = _hitta_rubrikrad(textrader, giltig_utf8, bankformat)

    resultat = []
    for _, var, falt in _csv_rader(textrader[rubrik_index + 1:], rubrik_index + 2, avgransare, antal_kolumner,
                                  BANKFIL):
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
            "bokforingsdag": _tolka_datum(varde["bokforingsdag"], kolumner["bokforingsdag"], var, BANKFIL),
            "transaktionsdag": _tolka_datum(varde["transaktionsdag"], kolumner["transaktionsdag"], var, BANKFIL),
            "referens": varde["referens"],
            "beskrivning": varde["beskrivning"],
            "belopp_ore": _tolka_ore(varde["belopp"], kolumner["belopp"], var, BANKFIL),
            "saldo_efter_ore": _tolka_ore(varde["saldo"], kolumner["saldo"], var, BANKFIL),
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


# --- Bankperiod ---

# Nyckeln som bara las_bankfil och sla_ihop_bankperioder har. Utan den går det inte att skapa en
# Bankperiod med rader som inte har gått igenom K1. Ett test (test_inga_genvagar.py) stoppar annan
# kärnkod från att använda den.
_PERIODNYCKEL = object()


class Bankperiod:
    """Bankraderna för en period, från las_bankfil. Kan bara skapas där och kan inte ändras.

    rader är raderna i filens ordning, i den form som beskrivs överst i filen. Varje gång de läses
    ges nya kopior, så att en ändring i dem aldrig når perioden. ingaende_saldo_ore och
    utgaende_saldo_ore är saldot när perioden börjar och slutar, heltal i öre.
    """

    __slots__ = ("_rader", "_ingaende_saldo_ore", "_utgaende_saldo_ore")

    def __init__(self, nyckel, rader, ingaende_saldo_ore, utgaende_saldo_ore):
        if nyckel is not _PERIODNYCKEL:
            raise BankfilFel(
                "En Bankperiod kan bara skapas av las_bankfil eller sla_ihop_bankperioder, som kör alla kontroller"
                " först."
            )
        # Raderna sparas som oföränderliga kopior. object.__setattr__ behövs eftersom vanlig
        # tilldelning är spärrad nedan.
        object.__setattr__(self, "_rader", tuple(MappingProxyType(dict(rad)) for rad in rader))
        object.__setattr__(self, "_ingaende_saldo_ore", ingaende_saldo_ore)
        object.__setattr__(self, "_utgaende_saldo_ore", utgaende_saldo_ore)

    def __setattr__(self, namn, varde):
        raise AttributeError("En Bankperiod kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("En Bankperiod kan inte ändras.")

    @property
    def rader(self):
        return [dict(rad) for rad in self._rader]

    @property
    def ingaende_saldo_ore(self):
        return self._ingaende_saldo_ore

    @property
    def utgaende_saldo_ore(self):
        return self._utgaende_saldo_ore

    def __repr__(self):
        return ("Bankperiod(" + str(len(self._rader)) + " rader, ingående saldo " + kronor(self._ingaende_saldo_ore)
                + ", utgående saldo " + kronor(self._utgaende_saldo_ore) + ")")


def las_bankfil(sokvag, bankformat, ingaende_saldo_ore, utgaende_saldo_ore):
    """Läser en bankfil och kör K1. Returnerar en Bankperiod bara om allt stämmer, annars BankfilFel.

    Bankformatet kommer från ladda_bankformat och kontrolleras igen här, så att ett trasigt
    format aldrig används. Ingående och utgående saldo är heltal i öre, till exempel från
    kontoutdraget.
    """
    bankformat = _kontrollera_bankformat(bankformat, "Bankformatet")
    data = _las_fil(sokvag, BANKFIL)
    rader = _tolka_rader(data, bankformat)
    kontrollera_k1(rader, ingaende_saldo_ore, utgaende_saldo_ore)
    return Bankperiod(_PERIODNYCKEL, rader, ingaende_saldo_ore, utgaende_saldo_ore)


def sla_ihop_bankperioder(perioder):
    """Sätter ihop flera Bankperioder, till exempel tre månader, till en. Annat ger BankfilFel.

    perioder är en lista eller tupel med Bankperioder i tidsordning, minst en. Varje periods
    ingående saldo ska vara lika med förra periodens utgående, så att inga rader saknas mellan
    dem, och ingen bankrad får finnas två gånger, till exempel om samma bankfil har lästs in två
    gånger. Den nya perioden har den första periodens ingående saldo och den sistas utgående.
    """
    if not isinstance(perioder, (list, tuple)):
        raise BankfilFel(
            "Bankperioderna ska vara en lista med Bankperioder från las_bankfil, inte " + type(perioder).__name__ + "."
        )
    if not perioder:
        raise BankfilFel("Det finns inga Bankperioder att sätta ihop.")
    for nummer, period in enumerate(perioder, start=1):
        # type() i stället för isinstance(), så att en underklass med andra regler inte godtas.
        if type(period) is not Bankperiod:
            raise BankfilFel(
                "Bankperiod nummer " + str(nummer) + " ska vara en Bankperiod från las_bankfil, inte "
                + type(period).__name__ + "."
            )
    for nummer in range(1, len(perioder)):
        forra, nasta = perioder[nummer - 1], perioder[nummer]
        if nasta.ingaende_saldo_ore != forra.utgaende_saldo_ore:
            raise BankfilFel(
                "Bankperioderna hänger inte ihop: Bankperiod nummer " + str(nummer + 1) + " har ingående saldo "
                + kronor(nasta.ingaende_saldo_ore) + ", men Bankperiod nummer " + str(nummer) + " har utgående saldo "
                + kronor(forra.utgaende_saldo_ore) + ", skillnad "
                + kronor(nasta.ingaende_saldo_ore - forra.utgaende_saldo_ore)
                + ". Det kan saknas rader mellan dem, eller så är de i fel ordning."
            )
    rader = [rad for period in perioder for rad in period.rader]
    sedda = set()
    for rad in rader:
        if rad["id"] in sedda:
            raise BankfilFel(
                "Bankraden med id " + repr(rad["id"]) + " (radnummer " + str(rad["radnr"]) + ") finns i flera"
                " Bankperioder. Samma bankfil kan vara inläst två gånger. Varje bankrad ska finnas en gång."
            )
        sedda.add(rad["id"])
    return Bankperiod(_PERIODNYCKEL, rader, perioder[0].ingaende_saldo_ore, perioder[-1].utgaende_saldo_ore)
