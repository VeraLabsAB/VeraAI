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

Inläsningen skyddas på samma sätt som bankfilen i las_bank.py, med de gemensamma skydden i
inlasning_skydd.py och kassafilens egna felmeddelanden (KASSAFIL): teckenkodningen upptäcks (UTF-8,
annars Windows-1252, UTF-16 och NUL-tecken stoppas), styrtecken och ovanliga radbrytningar stoppar
filen, radbrytning inuti ett fält stoppar filen, CSV läses strikt och varje rad ska ha lika många
fält som rubrikraden. Beloppen tolkas med belopp.tolka_belopp och blir heltal i öre, aldrig flyttal.
Ett Z-nummer får ha högst ZNUMMER_HOGST_SIFFROR siffror (H1). Kassaregistret måste finnas i
kassaformatets lista "kassaregister". Namnen jämförs efter normalisera_kassaregister, så stora och
små bokstäver, blanksteg och osynliga tecken räknas inte (H2).
Till skillnad från bankfilen ska rubrikraden vara filens första rad.

Varje Z-fil kontrolleras internt varje gång den läses (Z-kontroll a–e):

  a) datumet på varje rad stämmer med datumet i filnamnet,
  b) alla rader har samma Z-nummer och samma kassaregister,
  c) försäljningen per momssats summerar till totalsumman,
  d) betalsätten summerar till totalsumman,
  e) momsen per sats stämmer med försäljningen och satsen, avrundad enligt kassaformatet.

kontrollera_z_serien kontrollerar flera Z-rapporter över en period: Z-numren för varje
kassaregister ska följa på varandra utan luckor och utan dubbletter, och datumen får inte gå
bakåt när Z-numret ökar. Luckor beskrivs som ett intervall, både de saknade Z-numren och dagarna
utan rapport, och ett Z-nummer som verkar ha börjat om ger ett eget meddelande (öppen fråga H4).

summa_per_momssats summerar försäljningen per momssats för flera Z-rapporter. Den kör alltid
kontrollera_z_serien först, så en dubblett, en lucka eller en tom lista stoppar summeringen (I2).
Rapporterna som summeras måste alltså vara en hel serie utan luckor.

Vid minsta fel stoppas hela filen: inga rader returneras, och ett KassafilFel kastas.
"""

import datetime as dt
import hashlib
import re
import unicodedata

from inlasning_skydd import (
    HELTAL, RADBRYTNINGAR, Filsort, avkoda, csv_rader, filrad_for, inga_dubbla_kolumnnamn, inga_otillatna_tecken,
    kontrollera_anteckning, kontrollera_avgransare, kontrollera_namn, kontrollera_nycklar, ladda_json, las_fil,
    nul_fel, rubrikens_falt, tolka_datum, tolka_ore,
)
from las_bank import kronor

# Uppgifterna som kärnan behöver ur varje rad. Kassaformatet anger vad kolumnen för varje
# uppgift heter i Z-filen.
KOLUMN_NYCKLAR = ("rapportdatum", "znummer", "kassaregister", "postnamn", "sats", "belopp")

# Sorterna av poster. Kassaformatet anger vad posterna heter i Z-filen. Försäljning och moms har
# en rad per momssats. Betalsätten är en lista med ett postnamn per betalsätt.
POSTTYPER = ("forsaljning_per_sats", "moms_per_sats", "betalsatt", "totalsumma")
POSTTYPER_MED_SATS = ("forsaljning_per_sats", "moms_per_sats")

# Nycklar i kassaformat.json. "anteckning" är fri text för människor och används inte i koden.
KASSAFORMAT_NYCKLAR = ("filnamn", "kolumner", "avgransare", "poster", "momsavrundning", "kassaregister")
KASSAFORMAT_VALFRIA_NYCKLAR = ("anteckning",)

# Högsta antal siffror i ett Z-nummer, utan inledande nollor (H1). Z-numret ökar med ett för
# varje dagsavslut. Även en kassa med tio Z-rapporter om dagen i tusen år kommer bara upp i
# ungefär 3,7 miljoner (7 siffror). Nio siffror (upp till 999 999 999) ger god marginal, och ett
# längre Z-nummer betyder att filen är trasig. Gränsen gäller alla företag och ligger därför här.
ZNUMMER_HOGST_SIFFROR = 9

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

    typ är "lucka", "dubblett" eller "ordning". Vid lucka är saknas_fran och saknas_till det
    första och sista saknade Z-numret och antal_saknade hur många de är. dagar_fran och
    dagar_till är första och sista dagen mellan rapporterna före och efter luckan, som text, och
    antal_dagar hur många dagar det är (None, None och 0 om det inte finns någon dag däremellan).
    Varken de saknade Z-numren eller dagarna räknas upp en och en, eftersom luckan kan vara
    mycket stor (H1) och datumen kan ligga långt isär.
    """

    def __init__(self, meddelande, typ, kassaregister, znummer, saknas_fran=None, saknas_till=None,
                 dagar_fran=None, dagar_till=None):
        super().__init__(meddelande)
        self.typ = typ
        self.kassaregister = kassaregister
        self.znummer = list(znummer)
        self.saknas_fran = saknas_fran
        self.saknas_till = saknas_till
        self.antal_saknade = 0 if saknas_fran is None else saknas_till - saknas_fran + 1
        self.dagar_fran = dagar_fran
        self.dagar_till = dagar_till
        self.antal_dagar = 0 if dagar_fran is None else (
            dt.date.fromisoformat(dagar_till) - dt.date.fromisoformat(dagar_fran)).days + 1


# Det som skiljer kassafilens felmeddelanden från andra filers, för skydden i inlasning_skydd.py.
KASSAFIL = Filsort(
    fel=KassafilFel,
    filen="Kassafilen",
    formatet="Kassaformatet",
    exportera_igen="Exportera Z-rapporten från kassan igen",
    om_styrtecken="Sådana tecken finns inte i en vanlig Z-rapport, och de kan få raderna att delas fel.",
    ihopslaget="flera rader",
    nivaer="Ett kassaformat har bara tre nivåer.",
)


def normalisera_kassaregister(namn):
    """Kassaregistrets namn i den form som jämförs (H2).

    Unicode-normaliseras (NFKC, så att till exempel fullbreddstecken och två sätt att skriva "Ö"
    blir samma), blanksteg och osynliga tecken (Unicode-kategori Cc och Cf, till exempel U+200B)
    tas bort, och stora och små bokstäver räknas som samma. "TB-1", "tb-1" och "TB-1" med ett
    osynligt mellanslag blir alltså samma kassaregister.
    """
    namn = unicodedata.normalize("NFKC", namn)
    namn = "".join(tecken for tecken in namn
                   if not tecken.isspace() and unicodedata.category(tecken) not in ("Cc", "Cf"))
    return namn.casefold()


# --- Kassaformat ---

def _kontrollera_filnamn(monster, var):
    if not isinstance(monster, str):
        raise KassafilFel(var + ": 'filnamn' ska vara text, till exempel \"z_" + DATUMPLATS + ".csv\".")
    if monster.count(DATUMPLATS) != 1:
        raise KassafilFel(
            var + ": 'filnamn' ska innehålla " + repr(DATUMPLATS) + " exakt en gång, där datumet står i filnamnet."
        )
    if any(tecken in monster for tecken in "/\\") or monster.startswith("."):
        raise KassafilFel(var + ": 'filnamn' ska vara ett filnamn, utan mapp och utan punkt först.")
    if any(unicodedata.category(tecken) in ("Cc", "Cf") or tecken in RADBRYTNINGAR for tecken in monster):
        raise KassafilFel(var + ": 'filnamn' innehåller ett styrtecken eller ett osynligt tecken.")
    return monster


def _kontrollera_kassaformat(data, var):
    """Kontrollerar ett kassaformat och returnerar det i den form kärnan använder."""
    kontrollera_nycklar(data, KASSAFORMAT_NYCKLAR, KASSAFORMAT_VALFRIA_NYCKLAR, var, KASSAFIL)
    kontrollera_anteckning(data, var, KASSAFIL)

    filnamn = _kontrollera_filnamn(data["filnamn"], var)

    kontrollera_nycklar(data["kolumner"], KOLUMN_NYCKLAR, (), var + ", 'kolumner',", KASSAFIL)
    kolumner = {
        nyckel: kontrollera_namn(data["kolumner"][nyckel], "kolumnnamnet för " + repr(nyckel), var, KASSAFIL)
        for nyckel in KOLUMN_NYCKLAR
    }
    inga_dubbla_kolumnnamn(kolumner, var, KASSAFIL)
    avgransare = kontrollera_avgransare(data["avgransare"], kolumner, var, KASSAFIL)

    kontrollera_nycklar(data["poster"], POSTTYPER, (), var + ", 'poster',", KASSAFIL)
    poster = {}
    for posttyp in POSTTYPER:
        if posttyp == "betalsatt":
            lista = data["poster"][posttyp]
            if not isinstance(lista, list) or not lista:
                raise KassafilFel(var + ": 'betalsatt' under 'poster' ska vara en lista med minst ett postnamn.")
            poster[posttyp] = [
                kontrollera_namn(namn, "postnamnet för betalsätt nummer " + str(nummer), var, KASSAFIL)
                for nummer, namn in enumerate(lista, start=1)
            ]
        else:
            poster[posttyp] = kontrollera_namn(data["poster"][posttyp], "postnamnet för " + repr(posttyp), var,
                                               KASSAFIL)
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

    # Företagets kassaregister (H2). Z-filer från ett register som inte står här stoppas.
    lista = data["kassaregister"]
    if not isinstance(lista, list) or not lista:
        raise KassafilFel(var + ": 'kassaregister' ska vara en lista med minst ett kassaregister.")
    kassaregister = [
        kontrollera_namn(namn, "kassaregister nummer " + str(nummer), var, KASSAFIL)
        for nummer, namn in enumerate(lista, start=1)
    ]
    sedda = {}  # normaliserat namn -> namnet
    for namn in kassaregister:
        normaliserat = normalisera_kassaregister(namn)
        if normaliserat in sedda:
            raise KassafilFel(
                var + ": kassaregistren " + repr(sedda[normaliserat]) + " och " + repr(namn)
                + " under 'kassaregister' räknas som samma kassaregister (stora och små bokstäver och"
                + " blanksteg räknas inte). Varje kassaregister måste ha ett eget namn."
            )
        sedda[normaliserat] = namn

    return {
        "filnamn": filnamn,
        "kolumner": kolumner,
        "avgransare": avgransare,
        "poster": poster,
        "momsavrundning": data["momsavrundning"],
        "kassaregister": kassaregister,
    }


def ladda_kassaformat(sokvag):
    """Läser och kontrollerar ett företags kassaformat.json. Fel ger KassafilFel.

    Returnerar {"filnamn": mönster, "kolumner": {nyckel: kolumnnamn}, "avgransare": [tecken, ...],
    "poster": {posttyp: postnamn, "betalsatt": [postnamn, ...]}, "momsavrundning": sätt,
    "kassaregister": [namn, ...]}.
    """
    innehall, var = ladda_json(sokvag, KASSAFIL)
    return _kontrollera_kassaformat(innehall, var)


# --- Inläsning ---

def _las_rubrikrad(rad, kassaformat):
    """Returnerar (avgränsare, kolumnernas plats, antal kolumner) för filens första rad."""
    kolumner = kassaformat["kolumner"]
    rubrik = rubrikens_falt(rad, kassaformat["avgransare"], kolumner)
    if rubrik:
        avgransare, falt = rubrik
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


def _tolka_heltal(text, kolumn, var):
    if not HELTAL.fullmatch(text):
        raise KassafilFel(var + " har ett ogiltigt heltal i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")
    return int(text)


def _tolka_znummer(text, kolumn, var):
    """Z-numret som heltal. Fler än ZNUMMER_HOGST_SIFFROR siffror stoppar filen (H1)."""
    if not HELTAL.fullmatch(text):
        raise KassafilFel(var + " har ett ogiltigt heltal i kolumnen " + repr(kolumn) + ": " + repr(text) + ".")
    siffror = text.lstrip("0") or "0"
    if len(siffror) > ZNUMMER_HOGST_SIFFROR:
        raise KassafilFel(
            var + " har ett Z-nummer med " + str(len(siffror)) + " siffror i kolumnen " + repr(kolumn)
            + " (det börjar med " + siffror[:12] + "…), men ett Z-nummer får ha högst "
            + str(ZNUMMER_HOGST_SIFFROR) + " siffror. Z-numret ökar med ett per Z-rapport, så ett så"
            + " stort tal betyder att filen är trasig. Exportera Z-rapporten från kassan igen."
        )
    return int(siffror)


def _kassaregister_i_listan(text, kassaformat, kolumn, var):
    """Kassaregistrets namn som det står i kassaformatets lista. Okänt register stoppar filen (H2)."""
    normaliserat = normalisera_kassaregister(text)
    for namn in kassaformat["kassaregister"]:
        if normalisera_kassaregister(namn) == normaliserat:
            return namn
    raise KassafilFel(
        var + " har kassaregistret " + repr(text) + " i kolumnen " + repr(kolumn) + ", som inte"
        + " finns bland företagets kassaregister i kassaformatet ("
        + ", ".join(map(repr, kassaformat["kassaregister"])) + "). Kontrollera att filen kommer från"
        + " företagets egen kassa. Har företaget fått en ny kassa ska den läggas till i kassaformat.json."
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
    text, _ = avkoda(data, KASSAFIL)
    if "\x00" in text:
        raise nul_fel(filrad_for(text, text.index("\x00")), KASSAFIL)
    inga_otillatna_tecken(text, KASSAFIL)
    textrader = text.splitlines(keepends=True)
    if not textrader:
        raise KassafilFel("Kassafilen stoppas: filen är tom.")
    avgransare, plats, antal_kolumner = _las_rubrikrad(textrader[0], kassaformat)

    resultat = []
    sedda = {}  # (postnamn, sats) -> filrad, för att hitta poster som står två gånger
    for filrad, var, falt in csv_rader(textrader[1:], 2, avgransare, antal_kolumner, KASSAFIL):
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
        kassaregister = _kassaregister_i_listan(varde["kassaregister"], kassaformat, kolumner["kassaregister"], var)
        nyckel = (postnamn, sats)
        if nyckel in sedda:
            raise KassafilFel(
                var + ": posten " + repr(postnamn) + ("" if sats is None else " för momssatsen " + str(sats) + " %")
                + " står redan på rad " + str(sedda[nyckel]) + ". Varje post får bara finnas en gång."
            )
        sedda[nyckel] = filrad

        rad = {
            "rapportdatum": tolka_datum(varde["rapportdatum"], kolumner["rapportdatum"], var, KASSAFIL),
            "znummer": _tolka_znummer(varde["znummer"], kolumner["znummer"], var),
            "kassaregister": kassaregister,
            "postnamn": postnamn,
            "posttyp": posttyp,
            "sats": sats,
            "belopp_ore": tolka_ore(varde["belopp"], kolumner["belopp"], var, KASSAFIL),
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
    format aldrig används. Varje rad har: id, rapportdatum, znummer, kassaregister (namnet som
    det står i kassaformatets lista, inte som i filen), postnamn (som i filen), posttyp (en av
    POSTTYPER), sats (heltal i procent, eller None), belopp_ore, kalla_fil (SHA-256 av hela filen)
    och filrad (raden i filen).
    """
    kassaformat = _kontrollera_kassaformat(kassaformat, "Kassaformatet")
    data = las_fil(sokvag, KASSAFIL)
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
    """(första, sista) dagen efter fran och före till, som text, eller (None, None) om det inte finns någon.

    Dagarna räknas aldrig upp en och en, eftersom datumen kan ligga tusentals år isär.
    """
    # Dagnummer i stället för datum, så att det inte blir fel vid år 1 och år 9999, där det inte
    # finns någon dag före eller efter.
    forsta = dt.date.fromisoformat(fran).toordinal() + 1
    sista = dt.date.fromisoformat(till).toordinal() - 1
    if forsta > sista:
        return None, None
    return dt.date.fromordinal(forsta).isoformat(), dt.date.fromordinal(sista).isoformat()


_OMSTART_OPPEN_FRAGA = (
    " Det kan vara ett omstartat Z-nummer (till exempel vid årsskifte eller byte av kassa)."
    " Om ett kassaregisters Z-nummer får börja om är en öppen fråga (H4) som ska kontrolleras med"
    " Skatteverket eller en redovisningskonsult. Till dess stoppas serien."
)


def kontrollera_z_serien(rapporter):
    """Kontrollerar Z-serien över en period. rapporter är en lista med raderna från las_kassafil, en per Z-fil.

    För varje kassaregister ska Z-numren följa på varandra utan luckor och utan dubbletter, och
    datumet får inte gå bakåt när Z-numret ökar. Kassaregistren jämförs efter
    normalisera_kassaregister, så "TB-1" och "tb-1" är samma register (H2). En tom lista stoppas
    (H6). Kastar ZSerieFel vid första felet, och KassafilFel om det inte finns något att kontrollera.

    OBS: Kontrollen ser bara luckor mellan rapporterna som finns. Saknas periodens första eller
    sista Z-rapport syns det inte här.
    """
    if not rapporter:
        raise KassafilFel(
            "Z-serien: det finns inga Z-rapporter att kontrollera. En period helt utan Z-rapporter kan"
            " inte godkännas. Kontrollera att kassans filer för perioden är inlästa."
        )
    per_register = {}  # normaliserat namn -> (namnet, [(znummer, datum, kalla_fil), ...])
    for rader in rapporter:
        kassaregister, znummer, datum, kalla_fil = _rapportens_huvud(rader)
        per_register.setdefault(normalisera_kassaregister(kassaregister), (kassaregister, []))[1].append(
            (znummer, datum, kalla_fil))

    for normaliserat in sorted(per_register):
        kassaregister, rapporter_i_registret = per_register[normaliserat]
        serie = sorted(rapporter_i_registret)
        borjan = "Z-serien för kassaregistret " + repr(kassaregister)

        for (z_fore, datum_fore, fil_fore), (z_efter, datum_efter, fil_efter) in zip(serie, serie[1:]):
            if z_efter == z_fore:
                orsak = ("samma fil är inläst två gånger" if fil_fore == fil_efter
                         else "två olika filer har samma Z-nummer")
                raise ZSerieFel(
                    borjan + " har en dubblett: Z-rapport " + str(z_fore) + " finns två gånger, daterad "
                    + datum_fore + " och " + datum_efter + " (" + orsak + ")."
                    + (_OMSTART_OPPEN_FRAGA if datum_fore != datum_efter else ""),
                    "dubblett", kassaregister, [z_fore],
                )

        # Datumet får inte gå bakåt när Z-numret ökar. I datumordning får Z-numret alltså aldrig gå
        # ner. Det prövas före luckorna, så att ett Z-nummer som börjat om inte beskrivs som en
        # stor lucka (H4).
        i_datumordning = sorted(serie, key=lambda rapport: (rapport[1], rapport[0]))
        for (z_fore, datum_fore, _), (z_efter, datum_efter, _) in zip(i_datumordning, i_datumordning[1:]):
            if z_efter < z_fore:
                raise ZSerieFel(
                    borjan + " går bakåt i tiden: Z-rapport " + str(z_fore) + " är daterad " + datum_fore
                    + ", men Z-rapport " + str(z_efter) + " före den är daterad " + datum_efter + "."
                    + " Z-numret går alltså ner från " + str(z_fore) + " till " + str(z_efter)
                    + " när datumet går fram." + _OMSTART_OPPEN_FRAGA
                    + " Det kan också vara ett fel datum eller Z-nummer i en av filerna.",
                    "ordning", kassaregister, [z_efter, z_fore],
                )

        for (z_fore, datum_fore, _), (z_efter, datum_efter, _) in zip(serie, serie[1:]):
            if z_efter > z_fore + 1:
                # Luckan beskrivs som ett intervall, både Z-numren och dagarna. Inget räknas upp ett
                # och ett, eftersom luckan kan vara hur stor som helst (H1) och datumen kan ligga
                # tusentals år isär. Ingen annan rapport kan ha ett datum mellan datum_fore och
                # datum_efter: den skulle vara en dubblett eller gå bakåt i tiden, och det har
                # stoppats ovan.
                fran, till = z_fore + 1, z_efter - 1
                if fran == till:
                    vad = "Z-rapport " + str(fran) + " saknas"
                else:
                    vad = ("Z-rapporter saknas från nummer " + str(fran) + " till " + str(till)
                           + " (" + str(till - fran + 1) + " st)")
                dag_fran, dag_till = _dagar_mellan(datum_fore, datum_efter)
                if dag_fran is None:
                    dagar = "Den saknade rapporten är från " + datum_fore + " eller " + datum_efter + "."
                elif dag_fran == dag_till:
                    dagar = "Dagar däremellan utan Z-rapport: " + dag_fran + "."
                else:
                    antal = (dt.date.fromisoformat(dag_till) - dt.date.fromisoformat(dag_fran)).days + 1
                    dagar = ("Dagar däremellan utan Z-rapport: från " + dag_fran + " till " + dag_till
                             + " (" + str(antal) + " dagar).")
                raise ZSerieFel(
                    borjan + " har en lucka: " + vad + " mellan Z-rapport " + str(z_fore) + " ("
                    + datum_fore + ") och Z-rapport " + str(z_efter) + " (" + datum_efter + "). "
                    + dagar + " Hämta den saknade Z-rapporten från kassan.",
                    "lucka", kassaregister, [z_fore, z_efter], fran, till, dag_fran, dag_till,
                )


def summa_per_momssats(rapporter):
    """Försäljning per momssats för flera Z-rapporter: {sats: {"brutto_ore", "moms_ore", "netto_ore"}}.

    Kör kontrollera_z_serien först, så att samma Z-rapport aldrig räknas två gånger och en period
    med en lucka i Z-serien inte summeras (I2). En dubblett, lucka eller tom lista stoppas med samma
    fel som seriekontrollen ger, och ingen summa returneras.
    """
    kontrollera_z_serien(rapporter)
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
