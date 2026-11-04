"""Konteringsförslaget: en verifikation som ännu inte är bokförd, med kontrollerna K2 och ursprunget.

Ett konteringsförslag är en verifikation som Vera föreslår, plus det som en människa behöver för att
förstå och godkänna den (DESIGN-regelbok.md avsnitt 3). Förslaget är aldrig en bokföring. Det har
inget fält för att vara bokfört eller godkänt, och inget här skriver till kundens bokföringsprogram
eller till en SIE-fil. Det sker först efter godkännande (SPEC avsnitt 4, steg 9).

skapa_konteringsforslag är den enda offentliga funktionen som skapar ett förslag. Den tar emot
förslaget som ett objekt (se nedan), regelboken från las_regelbok, kontoplanen från las_kontoplan,
momsfilen från las_momssatser och perioderna från las_underlagsperiod, las_bankfil (eller
sla_ihop_bankperioder) och las_kassaperiod, och kör alltid alla kontroller. En period som förslaget
inte behöver får vara None, och momsfilen får vara None bara när förslaget inte bygger på något
underlag. Bara om allt stämmer returneras ett Konteringsforslag, som inte går att ändra och bara kan
skapas där. Annars stoppas förslaget med ett KonteringsforslagFel, och inget förslag skapas. Det är
ett fel i kärnan, inte ett ärende: det betyder att koden som räknade fram förslaget har räknat fel,
eller har byggt ett förslag där det skulle ha blivit ett ärende.

Ingen siffra i förslaget får komma från modellen. Därför bär varje rad sitt ursprung, och kontrollen
räknar själv om varje belopp ur källorna. Alla belopp är heltal i öre. Ingen avrundning görs någonstans:
de tre sätten att räkna (lika, summa och skillnad) är bara addition och subtraktion av heltal, så
beloppen går alltid jämnt ut.

K5, K7 och K8 för underlag (Hugos beslut 2026-10-30, granskning 22, P1) ligger också här, i
kontrollera_underlag, så att ingen kod kan få ett förslag för ett underlag utan att de har körts:
skapa_konteringsforslag kör dem på varje underlag i kopplingarna, efter K2 och ursprungskontrollen.
Flödena (konteringsfloden.py) anropar kontrollera_underlag före förslaget, för att göra ett ärende i
stället för ett förslag, och förslaget kontrollerar sedan samma sak igen. Ett förslag som stoppas av
K5, K7 eller K8 är alltså ett fel i kärnan: koden borde ha gjort ett ärende. Se "K5, K7 och K8" nedan.

Förslaget som objekt har exakt nycklarna i FORSLAG_NYCKLAR:

  forslag_id    förslagets id, text
  verifikation  exakt nycklarna i VERIFIKATION_NYCKLAR:
                  datum  verifikationens datum, ÅÅÅÅ-MM-DD
                  text   verifikationens text
                  rader  en lista med rader. En rad har exakt nycklarna i RAD_NYCKLAR:
                           konto       kontonumret som text
                           debet_ore   heltal i öre, 0 eller mer
                           kredit_ore  heltal i öre, 0 eller mer
                           ursprung    exakt nycklarna i URSPRUNG_NYCKLAR: berakning (en av
                                       BERAKNINGAR) och fran (en lista med källor)
  kopplingar    exakt nycklarna i KOPPLINGAR_NYCKLAR: underlag och bankrader (listor med objekt med
                nyckeln id), z_rapporter (en lista med objekt med nycklarna kassaregister och
                znummer) och regel (ett objekt med exakt nycklarna i REGELNS_NYCKLAR: id, regelns id
                i regelboken, och kontrollsummorna för regelboken, kontoplanen, momsfilen och
                matchningsformatet som förslaget är byggt mot)
  motivering    varför förslaget ser ut som det gör, text för godkännaren

Allt i förslaget ska vara objekt (dict), listor, text och heltal. En text får inte vara tom, inte ha
blanksteg först eller sist och inte ha något dolt tecken (samma tecken som normalisering.py tar bort,
utom vanligt mellanslag).

En källa i fran pekar på ett värde i en av perioderna (KALLOR):

  underlag   id och falt. falt är belopp_ore (att betala), eller underlag_ore eller moms_ore i en
             momsrad. För en momsrad krävs också momssats, som säger vilken momsrad det är
  bankrad    id (bankradens id från las_bankfil) och falt, som är belopp_ore
  z_rapport  kassaregister (namnet som i kassaformatets lista), znummer och postnamn, och sats för
             en post med momssats

Värdet är källans belopp i öre. En bankrad med pengar ut har ett negativt belopp, som räknas som
positivt: det är sidan raden står på som visar riktningen. Ett negativt värde i en Z-rapport stoppar
förslaget, eftersom det inte är bestämt hur returer ska bokföras.

Sätten att räkna (berakning):

  lika      beloppet är värdet i exakt en källa
  summa     beloppet är summan av två eller fler källor
  skillnad  beloppet är den första källan minus de andra, med minst två källor

K2 (debet = kredit), i Python:

  1. förslaget är byggt mot just de filer som det kontrolleras mot: kontoplanen är den som regelboken
     kontrollerades mot (samma kontrollsumma), och förslagets fyra kontrollsummor i 'regel' är de som
     regelboken, kontoplanen, och momsfilen och matchningsformatet som regelboken kontrollerades mot,
     faktiskt har. Summorna jämförs bara med de inlästa objekten, inte med något sparat godkänt värde
     (det hör till spärrsteget),
  2. verifikationen har minst två rader,
  3. varje belopp är ett heltal (inte True eller False, som annars räknas som 1 och 0 i Python), inte
     negativt och har högst HELTAL_HOGST_SIFFROR siffror,
  4. på varje rad är exakt ett av debet_ore och kredit_ore större än 0,
  5. summan av all debet är lika med summan av all kredit,
  6. varje konto finns i kontoplanen och gäller på verifikationens datum.

Ursprunget, direkt efter K2:

  1. varje rad har ett ursprung med ett känt sätt att räkna och rätt antal källor, och ingen källa står
     två gånger på samma rad,
  2. varje källa finns i perioderna,
  3. beloppet som kontrollen själv räknar fram ur källorna är exakt radens belopp,
  4. varje underlag, bankrad och Z-rapport som en rad använder står i kopplingar, var och en en gång,
     och varje som står i kopplingar används av minst en rad. Regeln finns i regelboken,
  5. en rad på ett momskonto har bara momsbelopp som källor, och rätt sorts moms. På kontot för
     ingående moms (rollen ingaende_moms i kontoplanen) är källan moms_ore i en momsrad i ett underlag.
     På ett konto för utgående moms (rollen utgaende_moms_per_sats) är källan en momspost i en
     Z-rapport, med en av kontots satser. Sidan (debet eller kredit) prövas inte, eftersom det inte är
     bestämt hur kreditnotor ska bokföras,
  6. en rad på bankkontot (rollen bank i kontoplanen) har bara bankrader som källor, räknade med lika
     eller summa, och står på rätt sida: pengar in i debet och pengar ut i kredit,
  7. täckningen: raderna tillsammans använder varje värde i källorna högst en gång per sida, så att
     inget räknas två gånger (se nedan),
  8. regeln passar förslaget (granskning 7, M3): verifikationens datum ligger inom regelns giltighet,
     förslaget har minst en källa av det slag regeln gäller (underlag, Z-rapport eller bankrad), och
     varje sådan källa i kopplingar har just den här regeln i regelboken på verifikationens datum.
     För ett underlag avgör typen och motparten, för en Z-rapport kassaregistret och för en bankrad
     regeln i matchningsformatet som raden passar. Varje konto på raderna står i regelns kontering
     eller har en roll i kontoplanen (bankkontot, leverantörsskulderna och momskontona).

Täckningen. Varje källa består av delar:

  underlag   en del per momsrad och fält: underlag_ore och moms_ore. belopp_ore består av alla
             underlagets delar (summan av momsraderna, K13)
  bankrad    en del, bankradens belopp
  z_rapport  försäljningen med en sats består av två delar: försäljningen utan moms och momsen med
             samma sats. Momsposten är bara momsdelen, och totalsumman består av alla
             försäljningens delar. Ett betalsätt är en egen del

För debet och för kredit räknas hur många gånger varje del används, med tecken: på en rad som räknas
med skillnad dras källorna efter den första ifrån (minus en gång), annars läggs de till (plus en
gång). Regeln:

  a. varje del används 0 eller 1 gång i debet, och 0 eller 1 gång i kredit,
  b. på varje sida är det som kommer från ett underlag antingen 0 eller hela belopp_ore: underlaget
     används helt eller inte alls på en sida.

a stoppar samma värde två gånger på en sida (dubbel moms, samma bankrad två gånger, moms både i
bruttot och för sig) och en skillnad som drar ifrån något som sidan inte tar med (ett belopp ur två
orelaterade underlag). b stoppar ett underlag där en del saknas, till exempel momsen. Kortavgiften
(DESIGN 4d: kortförsäljningen minus bankraden) godtas: bankraden läggs till och dras ifrån i debet och
används där 0 gånger. Samma del får stå en gång i debet och en gång i kredit (till exempel bankraden
på både bankkontot och kostnaden i 4e).

K5, K7 och K8, efter ursprunget, för varje underlag som förslaget bygger på (kontrollera_underlag):

  K7: ett underlag från en ägare eller närstående (Regelbok.ar_agare_eller_narstaende) blir alltid
      ett ärende (SPEC K7), aldrig ett förslag. Prövas först: då prövas inte K5 och K8.
  K5 (DESIGN avsnitt 6), för varje momsrad i underlaget:
      1. satsen finns: minst en varugrupp i momsfilen har satsen på underlagets datum,
      2. satsen passar regeln: satsen är satsen för minst en av varugrupperna i regelns kontering på
         datumet, och alla sådana varugrupper har samma konto. Annars vet kärnan inte vilket konto
         raden ska till,
      3. momsen stämmer med satsen: abs(moms_ore × 100 − underlag_ore × sats) är högst momsfilens
         tolerans × 100. Bara heltal.
      Annars ett fynd, "fel momssats" (1 och 2) eller "moms stämmer inte med satsen" (3), med satsen
      i underlaget och satserna som momsfilen och regeln väntar sig.
  K8 (DESIGN avsnitt 6): regelns villkor säger avdragsbegransad. Då ett fynd, "avdragsbegränsat", som
      bara säger vilken regel det gäller, aldrig hur stor del som får dras av.

  Regeln är varje underlags egen regel: den regelboken ger underlaget på underlagets datum
  (Regelbok.regel_for_underlag), som i flödena. Inte förslagets regel i 'kopplingar' (granskning 23,
  P1, Hugos beslut 2026-10-30): förslagets regel kan gälla bankrader eller Z-rapporter och ändå ha ett
  underlag bland raderna, eftersom ursprungskontrollen punkt 8 bara prövar källorna av det slag regeln
  gäller. Då skulle K5 prövas mot bankregelns kontering och K8 mot bankregelns villkor. Ett underlag
  som inte har någon regel på sitt datum stoppar förslaget: det ska vara ärendet "ny motpart".
  Momsfilen ska vara den som regelboken kontrollerades mot (samma kontrollsumma, prövas i K2 punkt 1).
  Ett förslag med underlag men utan momsfil stoppas, eftersom K5 då inte kan köras.

  Underlagets egen regel ska dessutom vara förslagets regel i 'kopplingar' (Öppet 31, granskning 24,
  P5, Hugos beslut 2026-10-30). Prövas efter K5, K7 och K8, för varje underlag. Annars prövar
  ursprungskontrollen punkt 8 kontona mot förslagets regel, och underlagets kostnad kan hamna på
  den regelns konto fast K5 godtog satsen mot underlagets egen regel (granskarens prov: ett underlag
  under en regel för bankrader, med kostnaden på bankregelns konto). Flödena bygger alltid med
  underlagets egen regel, så de berörs inte. Ett förslag med underlag som har olika regler kräver
  ett nytt beslut.

  Kostnadsraden står på det konto K5 ger (Öppet 32, granskning 25, P7, Hugos beslut 2026-10-30).
  Prövas efter Öppet 31, för varje underlag: varje rad som har underlagets 'underlag_ore' för en
  momssats som källa ska stå på det konto kontrollera_underlag räknar fram för satsen ('konton').
  Annat konto stoppar förslaget, också ett annat konto i regeln och ett konto med en roll i
  kontoplanen (till exempel leverantörsskulderna). Annars godtar ursprungskontrollen punkt 8 varje
  konto som står i regeln eller har en roll, och kostnaden kan hamna på fel konto fast K5 och
  Öppet 31 godtog förslaget (granskarens prov: en regel med två konton och kontona bytta, och
  kostnaden på leverantörsskulderna). Flödena bygger kostnadsraderna ur samma 'konton', så de
  berörs inte.

  Beloppet och sätten att räkna (Öppet 34, granskning 26, M1, Hugos beslut 2026-10-30 om
  granskning 26). Prövas efter Öppet 32, för varje underlag: en rad som har underlagets
  'belopp_ore' som källa räknas bara med 'lika' och står bara på leverantörsskulderna (rollen
  leverantorsskulder i kontoplanen), och underlagets 'belopp_ore' står på högst en rad i
  förslaget, så att hela beloppet bokförs en gång, som fakturan (kredit) eller betalningen
  (debet). 'underlag_ore' och 'moms_ore' räknas bara med 'lika' eller 'summa', aldrig med
  'skillnad'. Annars kan kostnaden räknas som 'belopp_ore' minus momsen och hamna på vilket konto
  som helst utan att Öppet 32 ser den, eftersom raden då inte har 'underlag_ore' som källa
  (granskarens prov: kostnaden på leverantörsskulderna, kontona bytta inom regeln, hela beloppet
  med moms på kostnadskontot utan momsrad, och hela beloppet på leverantörsskulderna på båda
  sidorna, alla godtagna med alla kontroller gröna). Flödena bygger fakturan med 'belopp_ore' en
  gång i kredit på leverantörsskulderna och betalningen med 'belopp_ore' en gång i debet, alltid
  med 'lika', så de berörs inte. Prövas före Öppet 33, så att en rad som räknas fel får felet om
  beräkningen, inte om kontot.

  Momsraden står på kontot för ingående moms (Öppet 33, granskning 25, P7, Hugos beslut
  2026-10-30 om byggsessionen för Öppet 32, a). Prövas efter Öppet 34, för varje underlag: varje rad
  som har underlagets 'moms_ore' som källa ska stå på kontot för ingående moms (rollen ingaende_moms i
  kontoplanen). Annat konto stoppar förslaget. Punkt 5 säger bara vad en rad på ett momskonto får
  ha som källa, inte att momsen från ett underlag måste stå på ett momskonto, så utan den här
  kontrollen godtogs momsen på kostnadskontot (granskning 26, H7). Flödena bygger momsraden ur
  kontoplanens roll, så de berörs inte.

  Sidan för beloppet (Öppet 35, granskning 27, M1, Hugos beslut 2026-10-31). Prövas sist, för varje
  underlag: en rad med underlagets 'belopp_ore' som källa står i debet bara när förslaget har minst
  en bankrad i kopplingarna (betalningen), och i kredit bara när ingen rad har underlagets
  'underlag_ore' eller 'moms_ore' som källa i kredit (fakturan). Annars godtogs fakturan spegelvänd
  (beloppet i debet, kostnaden och momsen i kredit) och två lika stora fakturor kvittade mot varandra
  på leverantörsskulderna, båda utan bankrad (granskarens prov h1 och h2): Öppet 34 räknar raderna
  per underlag och prövar inte sidan, och punkt 5 prövar inte sidan eftersom kreditnotor inte är
  bestämda (Ö8). En kreditnota kan inte läsas in i dag (typen finns inte och negativa belopp stoppas
  i las_underlag), så regeln stoppar ingen. När Ö8 byggs måste regeln prövas igen. Halvan om kredit
  stoppas i dag redan av täckningen eller Öppet 34. Flödena bygger betalningen med bankraden och
  fakturan med kostnaden och momsen i debet, så de berörs inte.

  Bankraden för beloppet i debet (Öppet 36, granskning 28, M1, Hugos beslut 2026-11-04, granskarens
  (a)). Prövas i samma kontroll som Öppet 35, för varje underlag: för varje rad med underlagets
  'belopp_ore' i debet ska förslaget ha en egen rad på bankkontot (rollen bank i kontoplanen) i
  kredit, med samma belopp och med bankrader som källor, och varje rad på bankkontot räknas bara en
  gång (två rader med 'belopp_ore' i debet och samma belopp får inte dela en rad på bankkontot).
  Annars räckte det att förslaget hade någon bankrad alls, var som helst och med vilket belopp som
  helst: fakturan spegelvänd gick igenom ihop med en annan fakturas betalning, och beloppet i debet
  gick igenom mot en bankrad på kostnadskontot (granskarens prov b1 och b3). Det är så flöde a bygger
  betalningen (beloppet i debet, bankraden på bankkontot i kredit med samma belopp), så flödena berörs
  inte. När Ö8 (kreditnotor) byggs måste regeln prövas igen, som Öppet 35.

Kopplingarna i förslaget får kontrollsummorna för regelboken, kontoplanen, momsfilen och
matchningsformatet, och kontrollsumman för varje fil förslaget bygger på (underlaget, bankfilen och
Z-filen). Summorna kommer från inläsningen, aldrig från indata: de som står i indata jämförs bara (K2).
Förslagets 'kontroller' säger vilka kontroller det har klarat: K2 och ursprunget för alla förslag, och
K5, K7 och K8 för förslag som bygger på underlag.
"""

import datetime as dt
import re
import unicodedata
import weakref
from types import MappingProxyType
from typing import NamedTuple

from las_bank import Bankperiod, kronor
from las_kassa import Kassaperiod
from las_kontoplan import Kontoplan, KontoplanFel
from las_momssatser import Momssatser, MomssatsFel
from las_regelbok import Regelbok
from las_underlag import HELTAL_HOGST_SIFFROR, Underlagsperiod
from normalisering import normalisera_for_jamforelse

FORSLAG_NYCKLAR = ("forslag_id", "verifikation", "kopplingar", "motivering")
# "datum" är samma ord som underlagets egen nyckel för datumet (las_underlag.NYCKLAR).
VERIFIKATION_NYCKLAR = ("datum", "text", "rader")
RAD_NYCKLAR = ("konto", "debet_ore", "kredit_ore", "ursprung")
URSPRUNG_NYCKLAR = ("berakning", "fran")
BERAKNINGAR = ("lika", "summa", "skillnad")
KOPPLINGAR_NYCKLAR = ("underlag", "bankrader", "z_rapporter", "regel")
# Nycklarna i varje post i kopplingarnas listor.
KOPPLINGARNAS_NYCKLAR = {"underlag": ("id",), "bankrader": ("id",), "z_rapporter": ("kassaregister", "znummer")}
# Nycklarna i 'regel' i kopplingarna: regelns id och kontrollsummorna för filerna förslaget är byggt mot.
REGELNS_NYCKLAR = ("id", "regelbokens_kontrollsumma", "kontoplanens_kontrollsumma", "momsfilens_kontrollsumma",
                   "matchningsformatets_kontrollsumma")
# Källan som en regel gäller (las_regelbok.KALLOR), och var källorna står i kopplingarna.
_REGELNS_KALLOR = {"underlag": ("underlag", "underlag"), "z_rapport": ("z_rapporter", "Z-rapporter"),
                   "bankrad": ("bankrader", "bankrader")}
# Källorna en rad kan räknas ur: nycklarna utöver "kalla", och de valfria nycklarna.
KALLOR = {
    "underlag": (("id", "falt"), ("momssats",)),
    "bankrad": (("id", "falt"), ()),
    "z_rapport": (("kassaregister", "znummer", "postnamn"), ("sats",)),
}
# Fälten som en källa kan peka på. Namnen är underlagets och bankradens egna (las_underlag, las_bank).
UNDERLAGETS_FALT = ("belopp_ore",)
MOMSRADENS_FALT = ("underlag_ore", "moms_ore")
BANKRADENS_FALT = ("belopp_ore",)

# Det största beloppet på en rad, som för talen i underlagen.
_HOGSTA_BELOPP = 10 ** HELTAL_HOGST_SIFFROR - 1

# Kontrollernas namn i felen och i fynden.
_INDATA = "indata"
_K2 = "K2"
_URSPRUNG = "ursprung"
_K5 = "K5"
_K7 = "K7"
_K8 = "K8"
# Typerna i fynden från kontrollera_underlag. Flödena använder dem som ärendets typ.
_FEL_SATS = "fel momssats"
_FEL_MOMS = "moms stämmer inte med satsen"
_KRAVER_BEDOMNING = "kräver mänsklig bedömning"
_AVDRAGSBEGRANSAT = "avdragsbegränsat"

# Rollerna i kontoplanen som kontrollerna känner igen (las_kontoplan.ROLLER), och kassans post för moms
# (las_kassa.POSTTYPER).
_BANK = "bank"
_INGAENDE_MOMS = "ingaende_moms"
_UTGAENDE_MOMS = "utgaende_moms_per_sats"
_MOMSPOST = "moms_per_sats"
_FORSALJNINGSPOST = "forsaljning_per_sats"
_TOTALSUMMA = "totalsumma"
# Fälten i en momsrad: beloppet utan moms och momsen. Och underlagets belopp att betala.
_UNDERLAGSFALT = "underlag_ore"
_MOMSFALT = "moms_ore"
_BELOPPSFALT = "belopp_ore"
_LEVERANTORSSKULDER = "leverantorsskulder"
# Sidorna i täckningen.
_SIDOR = ("debet", "kredit")
_DELARNA = ("Ett underlags 'belopp_ore' räknas som alla dess momsraders '" + _UNDERLAGSFALT + "' och '" + _MOMSFALT
            + "', och en Z-rapports försäljning med en sats som försäljningen utan moms plus momsen med samma sats.")

_DATUMFORM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)


class KonteringsforslagFel(Exception):
    """Förslaget skapades inte. kontroll är "indata", "K2" eller "ursprung", efter vad som slog larm."""

    def __init__(self, meddelande, kontroll):
        super().__init__(meddelande)
        self.kontroll = kontroll


def _fel(kontroll, text):
    return KonteringsforslagFel("Konteringsförslaget skapas inte (" + kontroll + "): " + text, kontroll)


_SORTER = {str: "text", int: "ett heltal", float: "ett decimaltal", bool: "True eller False", type(None): "None",
           list: "en lista", tuple: "en tupel", dict: "ett objekt"}


def _sort(varde):
    """Vad ett värde är, för ett felmeddelande, till exempel "ett decimaltal"."""
    return _SORTER.get(type(varde), type(varde).__name__)


# --- Formen ---

def _ren_kopia(varde, plats):
    """En kopia av förslaget med bara objekt, listor, text, tal, True, False och None. Annat stoppas.

    Kopian görs innan något kontrolleras, så att förslaget inte kan ändras under kontrollerna, och så
    att ett objekt som bara liknar en dict eller lista aldrig kommer in. type() i stället för
    isinstance(), så att en underklass med egna regler inte släpps igenom.
    """
    if type(varde) is dict:
        kopia = {}
        for nyckel, del_ in varde.items():
            if type(nyckel) is not str:
                raise _fel(_INDATA, plats + " har nyckeln " + repr(nyckel) + ", som inte är text.")
            kopia[nyckel] = _ren_kopia(del_, plats + ", " + repr(nyckel))
        return kopia
    if type(varde) is list:
        return [_ren_kopia(del_, plats + ", nummer " + str(nummer)) for nummer, del_ in enumerate(varde, start=1)]
    if varde is None or type(varde) in (str, int, float, bool):
        return varde
    raise _fel(_INDATA, plats + " är " + _sort(varde) + ". Förslaget får bara innehålla objekt (dict), listor,"
                        " text, tal, True, False och None.")


def _nycklar(varde, nycklar, valfria, vad, kontroll=_INDATA):
    """varde ska vara ett objekt med alla nycklarna och inga andra än de valfria. Returnerar det."""
    if type(varde) is not dict:
        raise _fel(kontroll, vad + " ska vara ett objekt (dict), inte " + _sort(varde) + ".")
    saknas = [nyckel for nyckel in nycklar if nyckel not in varde]
    if saknas:
        raise _fel(kontroll, vad + " saknar nyckeln " + ", ".join(map(repr, saknas)) + ".")
    okanda = sorted(nyckel for nyckel in varde if nyckel not in nycklar + valfria)
    if okanda:
        raise _fel(kontroll, vad + " har en okänd nyckel: " + ", ".join(map(repr, okanda)) + ". Tillåtna nycklar är "
                   + ", ".join(map(repr, nycklar + valfria)) + ".")
    return varde


def _lista(varde, vad):
    if type(varde) is not list:
        raise _fel(_INDATA, vad + " ska vara en lista, inte " + _sort(varde) + ".")
    return varde


def _ar_dolt(tecken):
    """True för ett tecken som inte syns, utom vanligt mellanslag: det som normaliseringen tar bort.

    Dessutom halva tecken (kategori Cs), som inte är giltig Unicode.
    """
    if tecken == " ":
        return False
    return unicodedata.category(tecken) == "Cs" or not normalisera_for_jamforelse(tecken)


def _text(varde, vad, kontroll=_INDATA):
    """En text som inte är tom, inte har blanksteg först eller sist och inte har något dolt tecken."""
    if type(varde) is not str:
        raise _fel(kontroll, vad + " ska vara text, inte " + _sort(varde) + ".")
    if not varde.strip():
        raise _fel(kontroll, vad + " får inte vara tom.")
    if varde != varde.strip():
        raise _fel(kontroll, vad + " får inte ha blanksteg först eller sist.")
    dolda = [tecken for tecken in varde if _ar_dolt(tecken)]
    if dolda:
        raise _fel(kontroll, vad + " innehåller tecknet U+" + format(ord(dolda[0]), "04X") + ", som inte syns (ett"
                   " styrtecken, ett osynligt tecken eller ett ovanligt blanksteg). Sådana tecken kan dölja eller"
                   " ändra text för godkännaren.")
    return varde


def _heltal(varde, vad, kontroll):
    """Ett heltal som inte är negativt. True och False räknas inte som heltal."""
    if type(varde) is not int:
        raise _fel(kontroll, vad + " ska vara ett heltal, inte " + _sort(varde) + ".")
    if varde < 0:
        raise _fel(kontroll, vad + " är negativt (" + str(varde) + ").")
    return varde


def _datum(varde, vad):
    """Ett giltigt datum som text, ÅÅÅÅ-MM-DD."""
    if type(varde) is str and _DATUMFORM.fullmatch(varde):
        try:
            dt.date.fromisoformat(varde)
            return varde
        except ValueError:
            pass
    raise _fel(_INDATA, vad + " ska vara ett giltigt datum som text, ÅÅÅÅ-MM-DD, inte "
               + (repr(varde) if type(varde) is str else _sort(varde)) + ".")


def _kontrollera_formen(forslag):
    """Kopierar förslaget och kontrollerar formen: nycklar, listor, texter och datum. Returnerar kopian."""
    try:
        forslag = _ren_kopia(forslag, "förslaget")
    except RecursionError:
        raise _fel(_INDATA, "förslaget har för många objekt och listor inuti varandra.") from None
    _nycklar(forslag, FORSLAG_NYCKLAR, (), "förslaget")
    _text(forslag["forslag_id"], "'forslag_id'")
    _text(forslag["motivering"], "'motivering'")
    verifikation = _nycklar(forslag["verifikation"], VERIFIKATION_NYCKLAR, (), "'verifikation'")
    _datum(verifikation["datum"], "'datum' i 'verifikation'")
    _text(verifikation["text"], "'text' i 'verifikation'")
    for nummer, rad in enumerate(_lista(verifikation["rader"], "'rader' i 'verifikation'"), start=1):
        vad = "rad " + str(nummer)
        _nycklar(rad, RAD_NYCKLAR, (), vad)
        _nycklar(rad["ursprung"], URSPRUNG_NYCKLAR, (), "'ursprung' på " + vad)
        _lista(rad["ursprung"]["fran"], "'fran' i 'ursprung' på " + vad)
    kopplingar = _nycklar(forslag["kopplingar"], KOPPLINGAR_NYCKLAR, (), "'kopplingar'")
    for typ, nycklar in KOPPLINGARNAS_NYCKLAR.items():
        for nummer, post in enumerate(_lista(kopplingar[typ], repr(typ) + " i 'kopplingar'"), start=1):
            vad = "post nummer " + str(nummer) + " i " + repr(typ) + " i 'kopplingar'"
            _nycklar(post, nycklar, (), vad)
            for nyckel in nycklar:
                if nyckel == "znummer":
                    _heltal(post[nyckel], repr(nyckel) + " i " + vad, _INDATA)
                else:
                    _text(post[nyckel], repr(nyckel) + " i " + vad)
    regel = _nycklar(kopplingar["regel"], REGELNS_NYCKLAR, (), "'regel' i 'kopplingar'")
    for nyckel in REGELNS_NYCKLAR:
        _text(regel[nyckel], repr(nyckel) + " i 'regel' i 'kopplingar'")
    return forslag


def _kontrollera_indatans_typer(regelbok, kontoplan, momssatser, underlagsperiod, bankperiod, kassaperiod):
    """Regelboken, kontoplanen, momsfilen och perioderna ska komma från de enda tillåtna inläsningsfunktionerna."""
    # type() i stället för isinstance(), så att en underklass med egna regler inte släpps igenom.
    if type(regelbok) is not Regelbok:
        raise _fel(_INDATA, "regelboken ska komma från las_regelbok, inte vara " + type(regelbok).__name__ + ".")
    if type(kontoplan) is not Kontoplan:
        raise _fel(_INDATA, "kontoplanen ska komma från las_kontoplan, inte vara " + type(kontoplan).__name__ + ".")
    if momssatser is not None and type(momssatser) is not Momssatser:
        raise _fel(_INDATA, "momsfilen ska komma från las_momssatser, inte vara " + type(momssatser).__name__
                   + " (den får vara None bara när förslaget inte bygger på något underlag).")
    for period, klass, vad, funktion in (
            (underlagsperiod, Underlagsperiod, "underlagsperioden", "las_underlagsperiod"),
            (bankperiod, Bankperiod, "bankperioden", "las_bankfil eller sla_ihop_bankperioder"),
            (kassaperiod, Kassaperiod, "kassaperioden", "las_kassaperiod")):
        if period is not None and type(period) is not klass:
            raise _fel(_INDATA, vad + " ska komma från " + funktion + " (eller vara None), inte vara "
                       + type(period).__name__ + ".")
    # Ett objekt av rätt typ som har skapats förbi sin inläsningsfunktion, till exempel med __new__,
    # saknar sitt innehåll, och då ger Python ett AttributeError i stället för ett fel som förklarar
    # något (M12, granskning 7).
    for hamta, vad, funktion in (
            (lambda: regelbok.kontrollsumma, "regelboken", "las_regelbok"),
            (lambda: kontoplan.kontrollsumma, "kontoplanen", "las_kontoplan"),
            (lambda: momssatser is None or momssatser.kontrollsumma, "momsfilen", "las_momssatser"),
            (lambda: underlagsperiod is None or underlagsperiod.underlag, "underlagsperioden", "las_underlagsperiod"),
            (lambda: bankperiod is None or bankperiod.rader, "bankperioden", "las_bankfil eller sla_ihop_bankperioder"),
            (lambda: kassaperiod is None or kassaperiod.rapporter, "kassaperioden", "las_kassaperiod")):
        try:
            hamta()
        except AttributeError:
            raise _fel(_INDATA, vad + " är tom eller trasig: den har inte skapats av " + funktion + ".") from None


# --- K2 ---

def _radens_belopp(rad):
    return rad["debet_ore"] or rad["kredit_ore"]


# Så många tecken av en kontrollsumma visas i ett felmeddelande.
_VISADE_TECKEN = 16


def _kort(summa):
    """En kontrollsumma i ett felmeddelande: de första _VISADE_TECKEN tecknen."""
    return repr(summa[:_VISADE_TECKEN] + ("…" if len(summa) > _VISADE_TECKEN else ""))


def _kontrollera_kontrollsummor(regel, regelbok, kontoplan, momssatser):
    """K2 punkt 1: förslaget är byggt mot just de filer som det kontrolleras mot (granskning 7, M4).

    regel är 'regel' i förslagets kopplingar. Summorna jämförs bara med de inlästa objekten. Momsfilen
    (None om förslaget inte fick någon) ska vara den som regelboken kontrollerades mot, så att K5 prövar
    samma satser som regelboken kontrollerades mot (P1, granskning 22).
    """
    mot = regelbok.kontrollerad_mot
    if kontoplan.kontrollsumma != mot["kontoplan"]:
        raise _fel(_K2, "kontoplanen är inte den som regelboken kontrollerades mot. Kontoplanens kontrollsumma är "
                   + _kort(kontoplan.kontrollsumma) + ", men regelboken kontrollerades mot en kontoplan med "
                   + _kort(mot["kontoplan"]) + ". Regelboken och förslaget ska kontrolleras mot samma kontoplan.")
    if momssatser is not None and momssatser.kontrollsumma != mot["momssatser"]:
        raise _fel(_K2, "momsfilen är inte den som regelboken kontrollerades mot. Momsfilens kontrollsumma är "
                   + _kort(momssatser.kontrollsumma) + ", men regelboken kontrollerades mot en momsfil med "
                   + _kort(mot["momssatser"]) + ". Regelboken och förslaget ska kontrolleras mot samma momsfil.")
    for nyckel, vad, faktisk in (
            ("regelbokens_kontrollsumma", "regelboken", regelbok.kontrollsumma),
            ("kontoplanens_kontrollsumma", "kontoplanen", kontoplan.kontrollsumma),
            ("momsfilens_kontrollsumma", "momsfilen som regelboken kontrollerades mot", mot["momssatser"]),
            ("matchningsformatets_kontrollsumma", "matchningsformatet som regelboken kontrollerades mot",
             mot["matchningsformat"])):
        if regel[nyckel] != faktisk:
            raise _fel(_K2, "förslaget är byggt mot en annan fil: " + repr(nyckel) + " i 'regel' i 'kopplingar' är "
                       + _kort(regel[nyckel]) + ", men " + vad + " har kontrollsumman " + _kort(faktisk) + ".")


def _kontrollera_k2(verifikation, kontoplan):
    """K2 punkt 2–6: minst två rader, rätta belopp, en sida per rad, debet = kredit och konton som finns på datumet."""
    rader = verifikation["rader"]
    if len(rader) < 2:
        raise _fel(_K2, "verifikationen har " + str(len(rader)) + " rad" + ("" if len(rader) == 1 else "er")
                   + ", men en verifikation ska ha minst två rader.")
    for nummer, rad in enumerate(rader, start=1):
        for falt in ("debet_ore", "kredit_ore"):
            belopp, vad = rad[falt], repr(falt) + " på rad " + str(nummer)
            # type() i stället för isinstance(), eftersom True och False räknas som heltal i Python.
            if type(belopp) is not int:
                raise _fel(_K2, vad + " ska vara ett heltal i öre, inte " + _sort(belopp) + ".")
            if belopp < 0:
                raise _fel(_K2, vad + " är negativt (" + kronor(belopp) + "). Inget belopp får vara negativt."
                           " Minus visas genom att beloppet står på andra sidan.")
            if belopp > _HOGSTA_BELOPP:
                raise _fel(_K2, vad + " har fler än " + str(HELTAL_HOGST_SIFFROR) + " siffror. Beloppet är"
                           " troligen fel räknat.")
        if (rad["debet_ore"] > 0) == (rad["kredit_ore"] > 0):
            raise _fel(_K2, "rad " + str(nummer) + " har " + ("både debet och kredit" if rad["debet_ore"] > 0 else
                                                              "varken debet eller kredit")
                       + ". På varje rad ska exakt ett av 'debet_ore' och 'kredit_ore' vara större än 0.")
    debet = sum(rad["debet_ore"] for rad in rader)
    kredit = sum(rad["kredit_ore"] for rad in rader)
    if debet != kredit:
        raise _fel(_K2, "summan av debet är " + kronor(debet) + ", men summan av kredit är " + kronor(kredit)
                   + ", skillnad " + kronor(debet - kredit) + ". Debet och kredit ska alltid vara lika.")
    for nummer, rad in enumerate(rader, start=1):
        if type(rad["konto"]) is not str:
            raise _fel(_K2, "'konto' på rad " + str(nummer) + " ska vara text, till exempel \"1234\", inte "
                       + _sort(rad["konto"]) + ".")
        try:
            kontoplan.kontots_namn(rad["konto"], verifikation["datum"])
        except KontoplanFel as fel:
            raise _fel(_K2, "rad " + str(nummer) + ": " + str(fel)) from None


# --- Ursprunget ---

class _Del(NamedTuple):
    """En del av en källa, som täckningen räknar (punkt 7 överst i filen)."""

    nyckel: tuple  # vilken del det är
    visas: str     # delen i ett felmeddelande
    belopp: int    # delens värde i öre


class _Varde(NamedTuple):
    """Ett värde ur en källa, som kontrollen själv har slagit upp i perioderna."""

    nyckel: tuple          # vilket värde det är, för att hitta en källa som står två gånger
    visas: str             # källan i ett felmeddelande
    belopp: int            # värdet i öre, aldrig negativt
    moms: object           # vilken sorts moms värdet är: "underlag" (moms_ore i en momsrad i ett underlag),
                           # "z_rapport" (en momspost i en Z-rapport), eller None om det inte är moms
    sats: object           # momssatsen, eller None om källan inte har någon
    koppling: tuple        # (typen i kopplingar, vad som står där): ("underlag", id) och så vidare
    bankens_belopp: object  # bankradens belopp med tecken (in är positivt, ut negativt), annars None
    delar: tuple           # delarna som värdet består av (_Del), för täckningen


class _Kallorna(NamedTuple):
    """Det som källorna slås upp i. None om förslaget inte fick perioden."""

    underlag: object     # {id: underlaget}
    bankrader: object    # {id: bankraden}
    z_rapporter: object  # {(kassaregister, znummer): raderna i Z-rapporten}


def _kallorna(underlagsperiod, bankperiod, kassaperiod):
    return _Kallorna(
        None if underlagsperiod is None else {underlag["id"]: underlag for underlag in underlagsperiod.underlag},
        None if bankperiod is None else {rad["id"]: rad for rad in bankperiod.rader},
        None if kassaperiod is None else {(rader[0]["kassaregister"], rader[0]["znummer"]): rader
                                          for rader in kassaperiod.rapporter},
    )


def _falt(kalla, tillatna, vad):
    falt = kalla["falt"]
    if type(falt) is not str or falt not in tillatna:
        raise _fel(_URSPRUNG, "'falt' i " + vad + " ska vara en av " + ", ".join(map(repr, tillatna)) + ", inte "
                   + (repr(falt) if type(falt) is str else _sort(falt)) + ".")
    return falt


def _underlagets_varde(kalla, vad, underlagen):
    if underlagen is None:
        raise _fel(_URSPRUNG, vad + " pekar på ett underlag, men förslaget fick ingen underlagsperiod.")
    id_ = _text(kalla["id"], "'id' i " + vad, _URSPRUNG)
    falt = _falt(kalla, UNDERLAGETS_FALT + MOMSRADENS_FALT, vad)
    if id_ not in underlagen:
        raise _fel(_URSPRUNG, vad + " pekar på underlaget " + repr(id_) + ", som inte finns i underlagsperioden. Det"
                   " kan ha ett datum utanför perioden, eller vara en dublett som K4 har tagit bort.")
    underlag = underlagen[id_]
    if falt in UNDERLAGETS_FALT:
        if "momssats" in kalla:
            raise _fel(_URSPRUNG, vad + " har 'momssats', men " + repr(falt) + " står inte i en momsrad. 'momssats'"
                       " hör bara till fälten " + ", ".join(map(repr, MOMSRADENS_FALT)) + ".")
        # belopp_ore är summan av momsraderna (K13), så det består av alla underlagets delar.
        return _Varde(("underlag", id_, None, falt), "underlaget " + repr(id_) + ", " + repr(falt), underlag[falt],
                      None, None, ("underlag", id_), None, _underlagets_delar(id_, underlag))
    if "momssats" not in kalla:
        raise _fel(_URSPRUNG, vad + " pekar på " + repr(falt) + " i en momsrad men saknar 'momssats', som säger"
                   " vilken momsrad det är.")
    sats = _heltal(kalla["momssats"], "'momssats' i " + vad, _URSPRUNG)
    momsrader = [rad for rad in underlag["moms"] if rad["momssats"] == sats]
    if not momsrader:
        raise _fel(_URSPRUNG, vad + ": underlaget " + repr(id_) + " har ingen momsrad med satsen " + str(sats) + " %."
                   " Satserna i underlaget är " + ", ".join(str(rad["momssats"]) + " %" for rad in underlag["moms"])
                   + ".")
    del_ = _momsradens_del(id_, momsrader[0], falt)
    return _Varde(del_.nyckel, del_.visas, del_.belopp, "underlag" if falt == _MOMSFALT else None, sats,
                  ("underlag", id_), None, (del_,))


def _momsradens_del(id_, momsrad, falt):
    """Fältet falt i en momsrad i underlaget id_, som en del för täckningen."""
    return _Del(("underlag", id_, momsrad["momssats"], falt), "underlaget " + repr(id_) + ", momsraden med satsen "
                + str(momsrad["momssats"]) + " %, " + repr(falt), momsrad[falt])


def _underlagets_delar(id_, underlag):
    """Alla delar i underlaget: underlag_ore och moms_ore i varje momsrad."""
    return tuple(_momsradens_del(id_, momsrad, falt) for momsrad in underlag["moms"] for falt in MOMSRADENS_FALT)


def _bankradens_varde(kalla, vad, bankrader):
    if bankrader is None:
        raise _fel(_URSPRUNG, vad + " pekar på en bankrad, men förslaget fick ingen bankperiod.")
    id_ = _text(kalla["id"], "'id' i " + vad, _URSPRUNG)
    falt = _falt(kalla, BANKRADENS_FALT, vad)
    if id_ not in bankrader:
        raise _fel(_URSPRUNG, vad + " pekar på bankraden " + repr(id_) + ", som inte finns i bankperioden.")
    belopp = bankrader[id_][falt]
    # Pengar ut har ett negativt belopp. På vilken sida raden står visar riktningen.
    del_ = _Del(("bankrad", id_, falt), "bankraden " + repr(id_) + " (radnummer " + str(bankrader[id_]["radnr"]) + ")",
                abs(belopp))
    return _Varde(del_.nyckel, del_.visas, del_.belopp, None, None, ("bankrader", id_), belopp, (del_,))


def _z_postens_varde(kalla, vad, rapporterna):
    if rapporterna is None:
        raise _fel(_URSPRUNG, vad + " pekar på en Z-rapport, men förslaget fick ingen kassaperiod.")
    kassaregister = _text(kalla["kassaregister"], "'kassaregister' i " + vad, _URSPRUNG)
    znummer = _heltal(kalla["znummer"], "'znummer' i " + vad, _URSPRUNG)
    postnamn = _text(kalla["postnamn"], "'postnamn' i " + vad, _URSPRUNG)
    sats = _heltal(kalla["sats"], "'sats' i " + vad, _URSPRUNG) if "sats" in kalla else None
    rapport = rapporterna.get((kassaregister, znummer))
    if rapport is None:
        raise _fel(_URSPRUNG, vad + " pekar på Z-rapport " + str(znummer) + " från kassaregistret "
                   + repr(kassaregister) + ", som inte finns i kassaperioden.")
    visas = "Z-rapport " + str(znummer) + " (" + kassaregister + "), posten " + repr(postnamn) + (
        "" if sats is None else " med satsen " + str(sats) + " %")
    poster = [rad for rad in rapport if rad["postnamn"] == postnamn and rad["sats"] == sats]
    if not poster:
        raise _fel(_URSPRUNG, vad + ": " + visas + " finns inte. Posterna i rapporten är " + ", ".join(
            repr(rad["postnamn"]) + ("" if rad["sats"] is None else " med satsen " + str(rad["sats"]) + " %")
            for rad in rapport) + ".")
    post = poster[0]
    if post["belopp_ore"] < 0:
        raise _fel(_URSPRUNG, vad + ": " + visas + " är negativ (" + kronor(post["belopp_ore"]) + "). Hur returer"
                   " och andra negativa poster i kassan ska bokföras är inte bestämt.")
    return _Varde(("z_rapport", kassaregister, znummer, postnamn, sats), visas, post["belopp_ore"],
                  "z_rapport" if post["posttyp"] == _MOMSPOST else None, post["sats"],
                  ("z_rapporter", (kassaregister, znummer)), None, _z_postens_delar(post, rapport))


def _z_postens_delar(post, rapport):
    """Delarna i en post i Z-rapporten (rapport är alla dess rader), för täckningen.

    Försäljningen med en sats är försäljningen utan moms plus momsen med samma sats (Z-kontroll e).
    Totalsumman är all försäljning (Z-kontroll c). En annan post är en egen del.
    """
    rapporten = "Z-rapport " + str(post["znummer"]) + " (" + post["kassaregister"] + "), "
    borjan = ("z_rapport", post["kassaregister"], post["znummer"])
    if post["posttyp"] == _TOTALSUMMA:
        return tuple(del_ for rad in rapport if rad["posttyp"] == _FORSALJNINGSPOST
                     for del_ in _z_postens_delar(rad, rapport))
    if post["posttyp"] not in (_FORSALJNINGSPOST, _MOMSPOST):
        return (_Del(borjan + (post["posttyp"], post["postnamn"]), rapporten + "posten " + repr(post["postnamn"]),
                     post["belopp_ore"]),)
    sats = post["sats"]
    # En sats utan momspost har momsen 0 (Z-kontroll e).
    moms = sum(rad["belopp_ore"] for rad in rapport if rad["posttyp"] == _MOMSPOST and rad["sats"] == sats)
    momsdelen = _Del(borjan + (_MOMSPOST, sats), rapporten + "momsen med satsen " + str(sats) + " %", moms)
    if post["posttyp"] == _MOMSPOST:
        return (momsdelen,)
    return (_Del(borjan + (_FORSALJNINGSPOST, sats), rapporten + "försäljningen utan moms med satsen " + str(sats)
                 + " %", post["belopp_ore"] - moms), momsdelen)


def _sla_upp(kalla, vad, kallorna):
    """Slår upp en källa i perioderna. Returnerar ett _Varde. En källa som inte finns stoppar förslaget."""
    if type(kalla) is not dict:
        raise _fel(_URSPRUNG, vad + " ska vara ett objekt (dict), inte " + _sort(kalla) + ".")
    sort = kalla.get("kalla")
    if type(sort) is not str or sort not in KALLOR:
        raise _fel(_URSPRUNG, "'kalla' i " + vad + " ska vara en av " + ", ".join(map(repr, KALLOR)) + ", inte "
                   + (repr(sort) if type(sort) is str else _sort(sort)) + ".")
    nycklar, valfria = KALLOR[sort]
    _nycklar(kalla, ("kalla",) + nycklar, valfria, vad, _URSPRUNG)
    if sort == "underlag":
        return _underlagets_varde(kalla, vad, kallorna.underlag)
    if sort == "bankrad":
        return _bankradens_varde(kalla, vad, kallorna.bankrader)
    return _z_postens_varde(kalla, vad, kallorna.z_rapporter)


def _rakna(berakning, belopp):
    """Beloppet räknat ur källornas värden, i öre."""
    if berakning == "lika":
        return belopp[0]
    if berakning == "summa":
        return sum(belopp)
    return belopp[0] - sum(belopp[1:])


def _kontrollera_momskonto(roller, varden, vad):
    """En rad på ett momskonto har bara momsbelopp som källor, av rätt sort och med rätt sats.

    Ingående moms kommer bara från moms_ore i en momsrad i ett underlag, och utgående moms bara från
    en momspost i en Z-rapport med en av kontots satser. Sidan prövas inte (kreditnotor är inte bestämda).
    """
    ingaende = (_INGAENDE_MOMS, None) in roller
    satser = [sats for roll, sats in roller if roll == _UTGAENDE_MOMS]
    if not ingaende and not satser:
        return
    utgaende = "kontot för utgående moms med satsen " + " och ".join(str(sats) + " %" for sats in satser)
    for varde in varden:
        if varde.moms is None:
            raise _fel(_URSPRUNG, vad + " är ett momskonto, men källan " + varde.visas + " är inte ett momsbelopp. En"
                       " rad på ett momskonto ska ha momsen i en momsrad ('" + _MOMSFALT + "') eller en momspost i en"
                       " Z-rapport som ursprung.")
        if varde.moms == "underlag" and ingaende:
            continue
        if varde.moms == "z_rapport" and varde.sats in satser:
            continue
        if varde.moms == "underlag":
            raise _fel(_URSPRUNG, vad + " är " + utgaende + ", men källan " + varde.visas + " är momsen i ett"
                       " underlag. Utgående moms ska komma från en momspost i en Z-rapport.")
        if not satser:
            raise _fel(_URSPRUNG, vad + " är kontot för ingående moms, men källan " + varde.visas + " är momsen i en"
                       " Z-rapport. Ingående moms ska komma från momsen i en momsrad i ett underlag ('" + _MOMSFALT
                       + "').")
        raise _fel(_URSPRUNG, vad + " är " + utgaende + ", men källan " + varde.visas + " har satsen "
                   + str(varde.sats) + " %.")


def _kontrollera_bankkonto(rad, roller, berakning, varden, vad):
    """En rad på bankkontot har bara bankrader som källor, räknade med lika eller summa, och rätt riktning."""
    if (_BANK, None) not in roller:
        return
    if berakning not in ("lika", "summa"):
        raise _fel(_URSPRUNG, vad + " är bankkontot och räknas med " + repr(berakning) + ". En rad på bankkontot ska"
                   " vara en eller flera bankrader, räknade med 'lika' eller 'summa'.")
    for varde in varden:
        if varde.bankens_belopp is None:
            raise _fel(_URSPRUNG, vad + " är bankkontot, men källan " + varde.visas + " är inte en bankrad. Pengar på"
                       " banken ska alltid komma från en bankrad.")
        if (varde.bankens_belopp > 0) != (rad["debet_ore"] > 0):
            raise _fel(_URSPRUNG, vad + " är bankkontot och står i " + ("debet" if rad["debet_ore"] > 0 else "kredit")
                       + ", men " + varde.visas + " är pengar " + ("in" if varde.bankens_belopp > 0 else "ut") + ". Pengar"
                       " in står i debet på bankkontot och pengar ut i kredit.")


def _kopplingens_uppgifter(typ, vad, kallorna):
    """En post i kopplingarna, med kontrollsumman från inläsningen."""
    if typ == "underlag":
        return {"id": vad, "kontrollsumma": kallorna.underlag[vad]["kalla_fil"]}
    if typ == "bankrader":
        rad = kallorna.bankrader[vad]
        return {"id": vad, "radnr": rad["radnr"], "filens_kontrollsumma": rad["kalla_fil"]}
    rader = kallorna.z_rapporter[vad]
    return {"kassaregister": vad[0], "znummer": vad[1], "rapportdatum": rader[0]["rapportdatum"],
            "filens_kontrollsumma": rader[0]["kalla_fil"]}


def _visa_koppling(typ, vad):
    if typ == "z_rapporter":
        return "Z-rapport " + str(vad[1]) + " (" + vad[0] + ")"
    return ("underlaget " if typ == "underlag" else "bankraden ") + repr(vad)


def _kontrollera_kopplingar(kopplingar, anvanda, regelbok, kontoplan, kallorna):
    """Kopplingarna och raderna använder samma källor, och regeln finns. Returnerar de nya kopplingarna."""
    nya = {}
    for typ, nycklar in KOPPLINGARNAS_NYCKLAR.items():
        angivna = [post[nycklar[0]] if len(nycklar) == 1 else tuple(post[nyckel] for nyckel in nycklar)
                   for post in kopplingar[typ]]
        for nummer, vad in enumerate(angivna):
            if vad in angivna[:nummer]:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " står flera gånger i " + repr(typ)
                           + " i 'kopplingar'.")
        for vad in anvanda[typ]:
            if vad not in angivna:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " används av en rad, men står inte i " + repr(typ)
                           + " i 'kopplingar'.")
        for vad in angivna:
            if vad not in anvanda[typ]:
                raise _fel(_URSPRUNG, _visa_koppling(typ, vad) + " står i " + repr(typ) + " i 'kopplingar', men"
                           " ingen rad använder det.")
        nya[typ] = [_kopplingens_uppgifter(typ, vad, kallorna) for vad in angivna]
    regelns_id = kopplingar["regel"]["id"]
    if not any(regel["id"] == regelns_id for regel in regelbok.regler):
        raise _fel(_URSPRUNG, "regeln " + repr(regelns_id) + " i 'kopplingar' finns inte i regelboken.")
    # Summorna tas från de inlästa objekten. Att de är samma som i förslaget har K2 redan prövat.
    mot = regelbok.kontrollerad_mot
    nya["regel"] = {"id": regelns_id, "regelbokens_kontrollsumma": regelbok.kontrollsumma,
                    "kontoplanens_kontrollsumma": kontoplan.kontrollsumma,
                    "momsfilens_kontrollsumma": mot["momssatser"],
                    "matchningsformatets_kontrollsumma": mot["matchningsformat"]}
    return nya


def _regelns_konton(kontering):
    """Alla konton i en regels kontering. Formen beror på källan (las_regelbok), med ett eller två steg."""
    konton = set()
    for varde in kontering.values():
        konton |= _regelns_konton(varde) if type(varde) is dict else {varde}
    return konton


def _kallans_regel(typ, vad, regelbok, kallorna, datum):
    """(regeln som regelboken ger källan på datumet, eller None; källan i ett felmeddelande)."""
    if typ == "underlag":
        underlag = kallorna.underlag[vad]
        return (regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], datum),
                "underlaget " + repr(vad) + " (" + underlag["typ"] + " från " + repr(underlag["motpart"]) + ")")
    if typ == "z_rapporter":
        return regelbok.regel_for_z_rapport(vad[0], datum), _visa_koppling(typ, vad)
    rad = kallorna.bankrader[vad]
    visas = "bankraden " + repr(vad) + " (radnummer " + str(rad["radnr"]) + ")"
    namn = regelbok.matchningsregel_for_bankrad(rad)
    if namn is None and regelbok.ar_bankrad_mot_agare_eller_narstaende(rad):
        # En regel i matchningsformatet undantar aldrig en bankrad mot en ägare eller närstående (K7, N3).
        return None, (visas + ", som är mot en ägare eller närstående och därför aldrig undantas från underlag av en"
                      " regel i matchningsformatet,")
    if namn is None:
        return None, visas + ", som inte passar någon regel för bankrader utan underlag i matchningsformatet,"
    return regelbok.regel_for_bankrad(namn, datum), visas + " (regeln " + repr(namn) + " i matchningsformatet)"


def _kontrollera_regeln(forslag, anvanda, regelbok, kontoplan, kallorna):
    """Ursprunget punkt 8: regeln passar förslagets datum, källor och konton (granskning 7, M3)."""
    regelns_id = forslag["kopplingar"]["regel"]["id"]
    # Att regeln finns har _kontrollera_kopplingar redan prövat.
    regel = [en for en in regelbok.regler if en["id"] == regelns_id][0]
    datum, villkor = forslag["verifikation"]["datum"], regel["villkor"]
    if datum < villkor["giltig_fran"] or (villkor["giltig_till"] is not None and datum > villkor["giltig_till"]):
        raise _fel(_URSPRUNG, "regeln " + repr(regelns_id) + " gäller från " + villkor["giltig_fran"] + " till "
                   + (villkor["giltig_till"] or "tills vidare") + ", men verifikationens datum är " + datum + ".")
    typ, sorten = _REGELNS_KALLOR[regel["galler"]["kalla"]]
    if not anvanda[typ]:
        raise _fel(_URSPRUNG, "regeln " + repr(regelns_id) + " gäller " + sorten + ", men förslaget har inga "
                   + sorten + " i " + repr(typ) + " i 'kopplingar'. Regeln passar inte förslaget.")
    for vad in anvanda[typ]:
        kallans, visas = _kallans_regel(typ, vad, regelbok, kallorna, datum)
        if kallans is None or kallans["id"] != regelns_id:
            raise _fel(_URSPRUNG, "regeln i 'kopplingar' är " + repr(regelns_id) + ", men " + visas + " har "
                       + ("ingen regel i regelboken" if kallans is None else "regeln " + repr(kallans["id"]))
                       + " på " + datum + ". Regeln ska vara den som regelboken ger källan.")
    konton = _regelns_konton(regel["kontering"])
    for nummer, rad in enumerate(forslag["verifikation"]["rader"], start=1):
        if rad["konto"] not in konton and not kontoplan.kontots_roller(rad["konto"]):
            raise _fel(_URSPRUNG, "rad " + str(nummer) + " (konto " + rad["konto"] + "): kontot står inte i regeln "
                       + repr(regelns_id) + " och har ingen roll i kontoplanen. Regelns konton är "
                       + ", ".join(sorted(konton)) + ".")


def _visa_rader(nummer):
    """Radnumren i ett felmeddelande, till exempel "rad 2" eller "rad 1, 2 och 4"."""
    nummer = [str(tal) for tal in sorted(set(nummer))]
    return "rad " + (nummer[0] if len(nummer) == 1 else ", ".join(nummer[:-1]) + " och " + nummer[-1])


def _kontrollera_tackning(raderna, underlagen, kallorna):
    """Täckningen, punkt 7 överst i filen.

    raderna är (radnummer, sida, berakning, värdena) för varje rad, och underlagen är id för
    underlagen som raderna använder.
    """
    for sida in _SIDOR:
        antal = {}  # delens nyckel: [delen, antal gånger med tecken, radnumren]
        for nummer, radens_sida, berakning, varden in raderna:
            if radens_sida != sida:
                continue
            for plats, varde in enumerate(varden):
                tecken = -1 if berakning == "skillnad" and plats > 0 else 1
                for del_ in varde.delar:
                    rakning = antal.setdefault(del_.nyckel, [del_, 0, []])
                    rakning[1] += tecken
                    rakning[2].append(nummer)
        for del_, ganger, nummer in antal.values():
            if ganger > 1:
                raise _fel(_URSPRUNG, "i " + sida + " används " + del_.visas + " " + str(ganger) + " gånger ("
                           + _visa_rader(nummer) + "). Varje del av en källa får användas högst en gång i debet och"
                           " en gång i kredit, så att inget värde räknas två gånger. " + _DELARNA)
            if ganger < 0:
                raise _fel(_URSPRUNG, "i " + sida + " dras " + del_.visas + " ifrån " + str(-ganger) + " gång"
                           + ("" if ganger == -1 else "er") + " mer än den läggs till (" + _visa_rader(nummer) + "). En"
                           " skillnad får bara dra ifrån något som samma sida också tar med. " + _DELARNA)
        for id_ in underlagen:
            underlag = kallorna.underlag[id_]
            delar = _underlagets_delar(id_, underlag)
            anvanda = [del_ for del_ in delar if del_.nyckel in antal and antal[del_.nyckel][1] == 1]
            anvant = sum(del_.belopp for del_ in anvanda)
            if anvant not in (0, underlag["belopp_ore"]):
                saknas = [del_ for del_ in delar if del_ not in anvanda and del_.belopp]
                raise _fel(_URSPRUNG, "i " + sida + " används " + kronor(anvant) + " av underlaget " + repr(id_)
                           + ", men ett underlag ska användas helt eller inte alls på varje sida: 0 kr eller hela"
                           " 'belopp_ore', " + kronor(underlag["belopp_ore"]) + ". Det som saknas är " + "; ".join(
                               del_.visas + ": " + kronor(del_.belopp) for del_ in saknas) + ".")


def _kontrollera_ursprung(forslag, regelbok, kontoplan, kallorna):
    """Ursprungskontrollen, punkt 1–8 överst i filen. Returnerar kopplingarna med kontrollsummorna."""
    anvanda = {typ: [] for typ in KOPPLINGARNAS_NYCKLAR}
    raderna = []
    for nummer, rad in enumerate(forslag["verifikation"]["rader"], start=1):
        vad = "rad " + str(nummer) + " (konto " + rad["konto"] + ")"
        berakning, fran = rad["ursprung"]["berakning"], rad["ursprung"]["fran"]
        if type(berakning) is not str or berakning not in BERAKNINGAR:
            raise _fel(_URSPRUNG, "'berakning' på " + vad + " ska vara en av " + ", ".join(map(repr, BERAKNINGAR))
                       + ", inte " + (repr(berakning) if type(berakning) is str else _sort(berakning)) + ".")
        if berakning == "lika" and len(fran) != 1:
            raise _fel(_URSPRUNG, vad + " räknas med 'lika' och ska ha exakt en källa i 'fran', men har "
                       + str(len(fran)) + ".")
        if berakning != "lika" and len(fran) < 2:
            raise _fel(_URSPRUNG, vad + " räknas med " + repr(berakning) + " och ska ha minst två källor i 'fran', men"
                       " har " + str(len(fran)) + ".")
        varden = []
        for kallans_nummer, kalla in enumerate(fran, start=1):
            varde = _sla_upp(kalla, "källa nummer " + str(kallans_nummer) + " på " + vad, kallorna)
            if any(annat.nyckel == varde.nyckel for annat in varden):
                raise _fel(_URSPRUNG, vad + " har " + varde.visas + " flera gånger i 'fran'. Varje källa får stå en"
                           " gång på en rad, så att inget värde räknas två gånger.")
            varden.append(varde)
            typ, vad_i_kopplingar = varde.koppling
            if vad_i_kopplingar not in anvanda[typ]:
                anvanda[typ].append(vad_i_kopplingar)
        raknat = _rakna(berakning, [varde.belopp for varde in varden])
        if raknat != _radens_belopp(rad):
            raise _fel(_URSPRUNG, vad + " har beloppet " + kronor(_radens_belopp(rad)) + ", men " + repr(berakning)
                       + " av källorna (" + "; ".join(varde.visas + ": " + kronor(varde.belopp) for varde in varden)
                       + ") blir " + kronor(raknat) + ", skillnad " + kronor(_radens_belopp(rad) - raknat) + ".")
        roller = kontoplan.kontots_roller(rad["konto"])
        _kontrollera_momskonto(roller, varden, vad)
        _kontrollera_bankkonto(rad, roller, berakning, varden, vad)
        raderna.append((nummer, _SIDOR[0] if rad["debet_ore"] > 0 else _SIDOR[1], berakning, varden))
    kopplingar = _kontrollera_kopplingar(forslag["kopplingar"], anvanda, regelbok, kontoplan, kallorna)
    _kontrollera_tackning(raderna, anvanda["underlag"], kallorna)
    # Efter täckningen, så att ett förslag med ett värde som räknas två gånger visar det felet först.
    _kontrollera_regeln(forslag, anvanda, regelbok, kontoplan, kallorna)
    return kopplingar


# --- K5, K7 och K8 för underlag (P1, granskning 22, Hugos beslut 2026-10-30) ---

class Underlagsfynd(NamedTuple):
    """Ett fynd från kontrollera_underlag: en kontroll som säger att underlaget ska bli ett ärende."""

    kontroll: str  # "K5", "K7" eller "K8"
    typ: str       # vad fyndet gäller, till exempel "fel momssats"
    text: str      # förklaringen för människan, med "Inget förslag görs"


class Underlagskontroll(NamedTuple):
    """Svaret från kontrollera_underlag."""

    konton: object  # {momssats: konto} för underlagets momsrader när alla tre kontrollerna godtar det, annars None
    fynd: tuple     # Underlagsfynd, tomt när underlaget godtas


def _satser_pa_datumet(momssatser, datum):
    """{varugrupp: sats} för varugrupperna i momsfilen som har en sats på datumet."""
    satser = {}
    for grupp in momssatser.varugrupper:
        try:
            satser[grupp] = momssatser.sats(grupp, datum)
        except MomssatsFel:
            pass
    return satser


def _visa_grupper(grupper, satser):
    """Varugrupperna med sina satser i ett fynd, till exempel "'grupp' (6 %)"."""
    return ", ".join(repr(grupp) + " (" + str(satser[grupp]) + " %)" for grupp in grupper)


def _k5(underlag, regel, momssatser):
    """K5 för underlagets momsrader. Returnerar ({sats: konto}, []) eller (None, [(typ, text), ...])."""
    datum = underlag["datum"]
    satser = _satser_pa_datumet(momssatser, datum)
    tolerans = momssatser.tolerans_ore_per_rad
    konton, fel = {}, []
    for momsrad in underlag["moms"]:
        sats = momsrad["momssats"]
        rad = "Momsraden med satsen " + str(sats) + " %"
        regelns = {grupp: konto for grupp, konto in regel["kontering"].items() if satser.get(grupp) == sats}
        if sats not in satser.values():
            fel.append((_FEL_SATS, rad + ": ingen varugrupp i momsfilen har satsen på " + datum + ". Satserna där på"
                        " datumet är " + _visa_grupper(satser, satser) + "."))
        elif not regelns:
            fel.append((_FEL_SATS, rad + ": regeln " + regel["id"] + " har varugrupperna " + _visa_grupper(
                regel["kontering"], satser) + " på " + datum + ", och ingen av dem har satsen i underlaget."))
        elif len(set(regelns.values())) > 1:
            fel.append((_FEL_SATS, rad + ": satsen passar flera varugrupper i regeln " + regel["id"] + " med olika"
                        " konton (" + _visa_grupper(regelns, satser) + "). Kärnan vet inte vilket konto raden ska"
                        " till."))
        elif abs(momsrad[_MOMSFALT] * 100 - momsrad[_UNDERLAGSFALT] * sats) > tolerans * 100:
            fel.append((_FEL_MOMS, rad + ": momsen är " + str(momsrad[_MOMSFALT]) + " öre på " + str(
                momsrad[_UNDERLAGSFALT]) + " öre utan moms, men satsen ger " + str(
                momsrad[_UNDERLAGSFALT] * sats // 100) + " öre, och momsfilen godtar högst " + str(tolerans)
                        + " öre i skillnad per rad."))
        else:
            konton[sats] = sorted(set(regelns.values()))[0]
    return (None, fel) if fel else (konton, [])


def kontrollera_underlag(underlag, regel, regelbok, momssatser):
    """K5, K7 och K8 för ett underlag med regeln regel. Returnerar en Underlagskontroll, annars KonteringsforslagFel.

    underlag är ett underlag från las_underlagsperiod, regel regeln som regelboken ger det
    (Regelbok.regel_for_underlag, inte None), regelbok från las_regelbok och momssatser från
    las_momssatser. Samma funktion används av skapa_konteringsforslag, som stoppar förslaget vid ett
    fynd, och av flödena, som gör ett ärende av varje fynd i stället för ett förslag. K7 prövas först
    och ensam. Annars prövas K5 och K8, och båda kan ge fynd. Utan fynd är konton kontot per momssats
    som underlagets kostnad ska bokföras på enligt regeln.
    """
    if type(regelbok) is not Regelbok:
        raise _fel(_INDATA, "regelboken ska komma från las_regelbok, inte vara " + type(regelbok).__name__ + ".")
    if type(momssatser) is not Momssatser:
        raise _fel(_INDATA, "momsfilen ska komma från las_momssatser, inte vara " + type(momssatser).__name__
                   + ". Utan momsfilen kan K5 inte köras.")
    if type(regel) not in (dict, MappingProxyType) or not {"id", "kontering", "villkor"} <= set(regel):
        raise _fel(_INDATA, "regeln ska vara en regel ur regelboken (Regelbok.regel_for_underlag), inte "
                   + _sort(regel) + ".")
    if regelbok.ar_agare_eller_narstaende(underlag["motpart"]):
        return Underlagskontroll(None, (Underlagsfynd(
            _K7, _KRAVER_BEDOMNING, "Underlaget är från en ägare eller närstående (K7). Det blir alltid ett ärende,"
            " och en människa avgör hur det ska bokföras."),))
    konton, fel = _k5(underlag, regel, momssatser)
    fynd = []
    if fel:
        typ = _FEL_SATS if any(typ == _FEL_SATS for typ, _ in fel) else _FEL_MOMS
        fynd.append(Underlagsfynd(_K5, typ, " ".join(text for _, text in fel) + " Inget förslag görs. En människa"
                                  " avgör vilken moms som gäller."))
    if regel["villkor"].get("avdragsbegransad") is True:
        fynd.append(Underlagsfynd(
            _K8, _AVDRAGSBEGRANSAT, "Regeln " + regel["id"] + " är avdragsbegränsad (K8). Inget förslag görs, och Vera"
            " föreslår inte hur stor del av kostnaden eller momsen som får dras av. En människa avgör det, med stöd"
            " av en redovisningskonsult."))
    return Underlagskontroll(None if fynd else konton, tuple(fynd))


def _kontrollera_kostnadsraderna(id_, underlag, regel, konton, rader):
    """Öppet 32: varje rad med underlagets 'underlag_ore' som källa står på det konto K5 ger för momssatsen.

    konton är {momssats: konto} från kontrollera_underlag, det konto regeln ger varugruppen med satsen.
    Ursprungskontrollen punkt 8 godtar varje konto som står i regeln eller har en roll i kontoplanen,
    så utan den här kontrollen kunde kostnaden stå på fel konto inom regeln eller på ett rollkonto
    (granskning 25, P7, Hugos beslut 2026-10-30). Källorna är redan uppslagna av ursprungskontrollen,
    så varje 'momssats' på en sådan rad finns i underlaget.
    """
    for nummer, rad in enumerate(rader, start=1):
        for kalla in rad["ursprung"]["fran"]:
            if kalla["kalla"] != "underlag" or kalla["id"] != id_ or kalla["falt"] != _UNDERLAGSFALT:
                continue
            sats = kalla["momssats"]
            vantat = konton.get(sats)
            if rad["konto"] == vantat:
                continue
            raise _fel(_URSPRUNG, "rad " + str(nummer) + " (konto " + rad["konto"] + ") är kostnaden från underlaget "
                       + repr(id_) + " för momssatsen " + str(sats) + " % ('" + _UNDERLAGSFALT + "'), men K5 ger kontot "
                       + (str(vantat) if vantat is not None else "inget konto") + " för den satsen enligt underlagets"
                       " regel " + repr(regel["id"]) + " på " + underlag["datum"] + ", och raden står på kontot "
                       + rad["konto"] + ". Kostnaden från ett underlag bokförs alltid på det konto K5 räknar fram för"
                       " momssatsen, också när ett annat konto står i regeln eller har en roll i kontoplanen (Öppet 32,"
                       " granskning 25, P7, Hugos beslut 2026-10-30).")


def _rollens_konto(kontoplan, roll, datum):
    """Kontot med rollen i ett felmeddelande, eller bara rollen om inget konto gäller på datumet."""
    try:
        return "kontot " + kontoplan.rollens_konto(roll, datum) + " (rollen " + repr(roll) + " i kontoplanen)"
    except KontoplanFel:
        return "kontot med rollen " + repr(roll) + " i kontoplanen"


def _underlagets_kallor(id_, rader):
    """(radnummer, raden, källan) för varje källa på raderna som pekar på underlaget id_."""
    return [(nummer, rad, kalla) for nummer, rad in enumerate(rader, start=1) for kalla in rad["ursprung"]["fran"]
            if kalla["kalla"] == "underlag" and kalla["id"] == id_]


def _kontrollera_beloppsraderna(id_, kontoplan, verifikation):
    """Öppet 34: underlagets 'belopp_ore' bara med 'lika', bara på leverantörsskulderna och på högst en rad, och
    'underlag_ore' och 'moms_ore' aldrig med 'skillnad'.

    Annars kan kostnaden räknas som 'belopp_ore' minus momsen, utan 'underlag_ore' som källa, och då ser
    Öppet 32 den inte (granskning 26, M1, Hugos beslut 2026-10-30 om granskning 26). Flödena bygger
    fakturan och betalningen med 'belopp_ore' en gång, med 'lika', på leverantörsskulderna.
    """
    datum, rader = verifikation["datum"], verifikation["rader"]
    beloppsrader = []
    for nummer, rad, kalla in _underlagets_kallor(id_, rader):
        vad = "rad " + str(nummer) + " (konto " + rad["konto"] + ")"
        berakning, falt = rad["ursprung"]["berakning"], kalla["falt"]
        if falt != _BELOPPSFALT:
            if berakning == "skillnad":
                raise _fel(_URSPRUNG, vad + " räknas med 'skillnad' och har underlaget " + repr(id_) + ", momsraden med"
                           " satsen " + str(kalla["momssats"]) + " %, " + repr(falt) + " som källa. Beloppet utan moms"
                           " ('" + _UNDERLAGSFALT + "') och momsen ('" + _MOMSFALT + "') i ett underlag räknas bara med"
                           " 'lika' eller 'summa', aldrig med 'skillnad': en rad som räknas som en skillnad ur ett"
                           " underlag kan bokföra något annat än det underlaget säger (Öppet 34, granskning 26, M1,"
                           " Hugos beslut 2026-10-30 om granskning 26).")
            continue
        if berakning != "lika":
            raise _fel(_URSPRUNG, vad + " räknas med " + repr(berakning) + " och har underlaget " + repr(id_) + ", '"
                       + _BELOPPSFALT + "' som källa. Hela beloppet att betala i ett underlag räknas bara med 'lika',"
                       " på en egen rad: annars kan kostnaden räknas som beloppet minus momsen och hamna på vilket"
                       " konto som helst utan att kontrollen av kostnadsraden ser den (Öppet 34, granskning 26, M1,"
                       " Hugos beslut 2026-10-30 om granskning 26).")
        if (_LEVERANTORSSKULDER, None) not in kontoplan.kontots_roller(rad["konto"]):
            raise _fel(_URSPRUNG, vad + " har underlaget " + repr(id_) + ", '" + _BELOPPSFALT + "' som källa, men står"
                       " på kontot " + rad["konto"] + ", som inte är leverantörsskulderna. Hela beloppet att betala i"
                       " ett underlag står bara på " + _rollens_konto(kontoplan, _LEVERANTORSSKULDER, datum)
                       + ": kostnaden bokförs ur momsradernas '" + _UNDERLAGSFALT + "' på det konto K5 ger och momsen ur"
                       " '" + _MOMSFALT + "' på kontot för ingående moms (Öppet 34, granskning 26, M1, Hugos beslut"
                       " 2026-10-30 om granskning 26).")
        beloppsrader.append(nummer)
    if len(beloppsrader) > 1:
        raise _fel(_URSPRUNG, _visa_rader(beloppsrader) + " har alla underlaget " + repr(id_) + ", '" + _BELOPPSFALT
                   + "' som källa. Hela beloppet att betala i ett underlag står på högst en rad i ett förslag, så att"
                   " det bokförs en gång: som fakturan (i kredit på leverantörsskulderna) eller som betalningen (i"
                   " debet), aldrig på båda sidorna i samma verifikation (Öppet 34, granskning 26, M1, Hugos beslut"
                   " 2026-10-30 om granskning 26).")


def _kontrollera_momsraderna(id_, kontoplan, verifikation):
    """Öppet 33: varje rad med underlagets 'moms_ore' som källa står på kontot för ingående moms.

    Punkt 5 i ursprungskontrollen säger bara vad en rad på ett momskonto får ha som källa, inte att
    momsen från ett underlag måste stå på ett momskonto, så utan den här kontrollen godtogs momsen
    på kostnadskontot (granskning 26, H7, Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a).
    Flödena bygger momsraden ur kontoplanens roll, så de berörs inte.
    """
    datum, rader = verifikation["datum"], verifikation["rader"]
    for nummer, rad, kalla in _underlagets_kallor(id_, rader):
        if kalla["falt"] != _MOMSFALT or (_INGAENDE_MOMS, None) in kontoplan.kontots_roller(rad["konto"]):
            continue
        raise _fel(_URSPRUNG, "rad " + str(nummer) + " (konto " + rad["konto"] + ") har momsen från underlaget "
                   + repr(id_) + " för momssatsen " + str(kalla["momssats"]) + " % ('" + _MOMSFALT + "') som källa,"
                   " men står på kontot " + rad["konto"] + ", som inte är kontot för ingående moms. Momsen från ett"
                   " underlag bokförs alltid på " + _rollens_konto(kontoplan, _INGAENDE_MOMS, datum) + ", också när"
                   " ett annat konto står i regeln eller har en roll i kontoplanen (Öppet 33, granskning 25, P7, Hugos"
                   " beslut 2026-10-30 om byggsessionen för Öppet 32, a).")


def _bankkontorader_i_kredit(kontoplan, rader):
    """(radnummer, raden) för varje rad på bankkontot (rollen bank) i kredit med bara bankrader som källor.

    Punkt 6 har redan stoppat en rad på bankkontot med någon annan källa, så villkoret om källorna är
    bara ett skydd om ordningen ändras.
    """
    return [(nummer, rad) for nummer, rad in enumerate(rader, start=1)
            if rad["kredit_ore"] > 0 and (_BANK, None) in kontoplan.kontots_roller(rad["konto"])
            and all(kalla["kalla"] == "bankrad" for kalla in rad["ursprung"]["fran"])]


def _para_beloppen_med_bankkontot(kontoplan, rader):
    """{radnummer: radnummer på bankkontot} för raderna med ett underlags 'belopp_ore' i debet (Öppet 36).

    Varje sådan rad paras, i radordning, med den första lediga raden på bankkontot i kredit som har
    exakt samma belopp, och en rad på bankkontot paras högst en gång. Rader med samma belopp är
    utbytbara, så ordningen spelar ingen roll för om alla får en partner. En rad utan partner saknas
    i svaret.
    """
    lediga = _bankkontorader_i_kredit(kontoplan, rader)
    par = {}
    for nummer, rad in enumerate(rader, start=1):
        if rad["debet_ore"] <= 0 or not any(kalla["kalla"] == "underlag" and kalla["falt"] == _BELOPPSFALT
                                             for kalla in rad["ursprung"]["fran"]):
            continue
        for plats, (bankens_nummer, bankens_rad) in enumerate(lediga):
            if bankens_rad["kredit_ore"] == rad["debet_ore"]:
                par[nummer] = bankens_nummer
                del lediga[plats]
                break
    return par


def _visa_bankkontoraderna(kontoplan, rader, par):
    """Raderna på bankkontot i kredit i ett felmeddelande, med vilken betalning var och en redan hör till."""
    bankens = _bankkontorader_i_kredit(kontoplan, rader)
    if not bankens:
        return "Förslaget har ingen rad på bankkontot i kredit."
    tagna = {bankens_nummer: nummer for nummer, bankens_nummer in par.items()}
    return "Raderna på bankkontot i kredit är " + "; ".join(
        "rad " + str(nummer) + " (konto " + rad["konto"] + "), " + kronor(rad["kredit_ore"])
        + (", redan betalningen för rad " + str(tagna[nummer]) + " (konto " + rader[tagna[nummer] - 1]["konto"] + ")"
           if nummer in tagna else "")
        for nummer, rad in bankens) + "."


def _kontrollera_beloppssidan(id_, kontoplan, kopplingar, verifikation):
    """Öppet 35 och 36: underlagets 'belopp_ore' i debet bara med en egen rad på bankkontot, och i kredit bara när
    delarna inte står i kredit.

    Flödena har 'belopp_ore' i debet bara i betalningen, tillsammans med bankraden, och i kredit bara i
    fakturan, med kostnaden och momsen i debet. Utan den här kontrollen godtogs fakturan spegelvänd
    (beloppet i debet, kostnaden och momsen i kredit, en faktura bokförd som en kreditnota, fast
    kreditnotor inte finns, Ö8) och två lika stora fakturor kvittade mot varandra på leverantörsskulderna,
    båda utan bankrad och med alla kontroller gröna (granskning 27, M1, Hugos beslut 2026-10-31). Öppet 34
    räknar raderna per underlag och prövar inte sidan. Halvan om kredit stoppas i dag redan av täckningen
    (punkt 7), eftersom 'belopp_ore' räknar med alla delarna på sin sida, eller av Öppet 34 om en del
    dras ifrån med 'skillnad', men ligger här så att beslutet står på ett ställe. Prövas sist, efter
    Öppet 33.

    Öppet 36 (granskning 28, M1, Hugos beslut 2026-11-04, granskarens (a)): kravet på bankrad gällde
    per förslag, så fakturan spegelvänd gick igenom ihop med en annan fakturas betalning (b1), och
    beloppet i debet gick igenom mot en bankrad på kostnadskontot (b3). Nu ska varje rad med
    underlagets 'belopp_ore' i debet ha en egen rad på bankkontot (rollen bank i kontoplanen) i
    kredit, med samma belopp och med bankrader som källor, och varje rad på bankkontot räknas bara
    en gång. Felet för Öppet 35 (ingen bankrad alls) kommer först, så att h1 och h2 får samma fel som
    förut. Kreditnotor (Ö8) finns inte än, så regeln stoppar ingen kreditnota i dag: när Ö8 byggs
    måste regeln prövas igen, eftersom en kreditnota med beloppet i debet inte har någon betalning.
    """
    datum, rader = verifikation["datum"], verifikation["rader"]
    kallor = _underlagets_kallor(id_, rader)
    par = _para_beloppen_med_bankkontot(kontoplan, rader)
    for nummer, rad, kalla in kallor:
        if kalla["falt"] != _BELOPPSFALT:
            continue
        vad = "rad " + str(nummer) + " (konto " + rad["konto"] + ")"
        if rad["debet_ore"] > 0:
            if not kopplingar["bankrader"]:
                raise _fel(_URSPRUNG, vad + " har underlaget " + repr(id_) + ", '" + _BELOPPSFALT + "' som källa i"
                           " debet, men förslaget har ingen bankrad. Hela beloppet att betala står i debet bara i"
                           " betalningen, tillsammans med bankraden: utan bankrad bokför raden fakturan baklänges, som"
                           " en kreditnota (en egen dokumenttyp som inte finns än, Ö8), eller kvittar den mot en annan"
                           " faktura (Öppet 35, granskning 27, M1, Hugos beslut 2026-10-31).")
            if nummer in par:
                continue
            raise _fel(_URSPRUNG, vad + " har underlaget " + repr(id_) + ", '" + _BELOPPSFALT + "' som källa i debet, "
                       + kronor(rad["debet_ore"]) + ", men förslaget har ingen egen rad på bankkontot i kredit med"
                       " samma belopp räknad ur en bankrad. " + _visa_bankkontoraderna(kontoplan, rader, par)
                       + " Betalningen av ett underlag är hela beloppet i debet på leverantörsskulderna mot samma"
                       " belopp i kredit på " + _rollens_konto(kontoplan, _BANK, datum) + ", ur bankraden: en bankrad"
                       " med ett annat belopp, på ett annat konto eller som redan är en annan rads betalning räcker"
                       " inte (Öppet 36, granskning 28, M1, Hugos beslut 2026-11-04).")
        delarna = sorted({(annan, annan_rad["konto"]) for annan, annan_rad, annan_kalla in kallor
                          if annan_kalla["falt"] != _BELOPPSFALT and annan_rad["kredit_ore"] > 0})
        if delarna:
            raise _fel(_URSPRUNG, vad + " har underlaget " + repr(id_) + ", '" + _BELOPPSFALT + "' som källa i kredit,"
                       " och " + ", ".join("rad " + str(annan) + " (konto " + konto + ")" for annan, konto in delarna)
                       + " har underlagets '" + _UNDERLAGSFALT + "' eller '" + _MOMSFALT + "' som källa också i"
                       " kredit. Hela beloppet att betala står i kredit bara i fakturan, där kostnaden och momsen står"
                       " i debet (Öppet 35, granskning 27, M1, Hugos beslut 2026-10-31).")


def _kontrollera_underlagen(kopplingar, verifikation, regelbok, kontoplan, momssatser, kallorna):
    """K5, K7 och K8 på varje underlag i de kontrollerade kopplingarna, mot underlagets egen regel.

    Returnerar kontrollerna som klarats. Körs efter ursprungskontrollen, som har visat att varje
    underlag finns. Regeln är den regelboken ger underlaget på underlagets datum, som i flödena, inte
    förslagets regel: den kan gälla bankrader eller Z-rapporter när ett underlag står bland raderna
    (granskning 23, P1, Hugos beslut 2026-10-30). Ett underlag utan regel stoppar förslaget. Sedan
    ska underlagets egen regel vara förslagets regel i kopplingarna, annars stoppas förslaget
    (Öppet 31, granskning 24, P5, Hugos beslut 2026-10-30): kontona prövades mot förslagets regel.
    Sedan ska varje kostnadsrad från underlaget i verifikationens rader stå på det konto K5 ger för
    momssatsen, annars stoppas förslaget (Öppet 32, granskning 25, P7, Hugos beslut 2026-10-30):
    punkt 8 godtar varje konto i regeln eller med en roll. Sedan räknas underlagets 'belopp_ore'
    bara med 'lika', bara på leverantörsskulderna och bara på en rad, och 'underlag_ore' och
    'moms_ore' aldrig med 'skillnad' (Öppet 34, granskning 26, M1, Hugos beslut 2026-10-30 om
    granskning 26). Sedan står varje momsrad från underlaget på kontot för ingående moms (Öppet 33,
    Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a). Sist står underlagets 'belopp_ore' i
    debet bara med en bankrad i förslaget, och i kredit bara när delarna inte står i kredit (Öppet 35,
    granskning 27, M1, Hugos beslut 2026-10-31), och beloppet i debet har en egen rad på bankkontot i
    kredit med samma belopp ur en bankrad, där varje rad på bankkontot räknas bara en gång (Öppet 36,
    granskning 28, M1, Hugos beslut 2026-11-04).
    """
    underlagen = [post["id"] for post in kopplingar["underlag"]]
    if not underlagen:
        return {}
    if momssatser is None:
        raise _fel(_INDATA, "förslaget bygger på ett underlag, men fick ingen momsfil. K5 kan inte köras utan"
                   " momsfilen från las_momssatser, så förslaget skapas inte.")
    rader = verifikation["rader"]
    for id_ in underlagen:
        underlag = kallorna.underlag[id_]
        regel = regelbok.regel_for_underlag(underlag["typ"], underlag["motpart"], underlag["datum"])
        if regel is None:
            raise _fel(_URSPRUNG, "underlaget " + repr(id_) + " (" + underlag["typ"] + " från "
                       + repr(underlag["motpart"]) + ") har ingen regel i regelboken på sitt datum " + underlag["datum"]
                       + ", så K5 och K8 kan inte prövas mot underlagets egen regel. Det ska vara ett ärende (ny"
                       " motpart), inte ett förslag.")
        kontroll = kontrollera_underlag(underlag, regel, regelbok, momssatser)
        if kontroll.fynd:
            fynd = kontroll.fynd[0]
            raise _fel(fynd.kontroll, "underlaget " + repr(id_) + ", " + fynd.typ + ": " + fynd.text + " Det ska vara"
                       " ett ärende, inte ett förslag.")
        if regel["id"] != kopplingar["regel"]["id"]:
            raise _fel(_URSPRUNG, "underlaget " + repr(id_) + " (" + underlag["typ"] + " från "
                       + repr(underlag["motpart"]) + ") har regeln " + repr(regel["id"]) + " i regelboken på sitt datum "
                       + underlag["datum"] + ", men förslagets regel i 'kopplingar' är " + repr(kopplingar["regel"]["id"])
                       + ". Ett förslag med underlag byggs bara med underlagets egen regel: annars prövas kontona mot en"
                       " annan regel, och underlagets kostnad kan hamna på fel konto (Öppet 31, Hugos beslut"
                       " 2026-10-30).")
        _kontrollera_kostnadsraderna(id_, underlag, regel, kontroll.konton, rader)
        _kontrollera_beloppsraderna(id_, kontoplan, verifikation)
        _kontrollera_momsraderna(id_, kontoplan, verifikation)
        _kontrollera_beloppssidan(id_, kontoplan, kopplingar, verifikation)
    return {_K5: "ok", _K7: "ok", _K8: "ok"}


# --- Förslaget ---

def _frys(varde):
    """En oföränderlig kopia: objekt blir MappingProxyType och listor blir tupler."""
    if isinstance(varde, dict):
        return MappingProxyType({nyckel: _frys(del_) for nyckel, del_ in varde.items()})
    if isinstance(varde, list):
        return tuple(_frys(del_) for del_ in varde)
    return varde


def _kopia(varde):
    """En vanlig kopia av ett fryst värde, som anroparen får ändra utan att förslaget ändras."""
    if isinstance(varde, MappingProxyType):
        return {nyckel: _kopia(del_) for nyckel, del_ in varde.items()}
    if isinstance(varde, tuple):
        return [_kopia(del_) for del_ in varde]
    return varde


# Nyckeln som bara skapa_konteringsforslag har. Utan den går det inte att skapa ett Konteringsforslag
# som inte har gått igenom K2 och ursprungskontrollen.
_FORSLAGSNYCKEL = object()

# Innehållet i varje förslag. Det ligger här och inte i förslaget självt, så att ett förslag inte har
# något som går att ändra, och så att ett förslag som har skapats förbi skapa_konteringsforslag (till
# exempel med object.__new__) är tomt och inte går att läsa. Ett test (test_inga_genvagar.py) stoppar
# annan kärnkod från att använda nyckeln och innehållet.
_FORSLAGEN = weakref.WeakKeyDictionary()


def _innehallet(forslag):
    try:
        return _FORSLAGEN[forslag]
    except KeyError:
        raise KonteringsforslagFel("Förslaget har inte skapats av skapa_konteringsforslag och kan inte läsas.",
                                   _INDATA) from None


class Konteringsforslag:
    """Ett konteringsförslag från skapa_konteringsforslag. Kan bara skapas där och kan inte ändras.

    Förslaget är aldrig bokfört eller godkänt och har inget fält för det. Varje gång en del läses ges
    en ny kopia, så att en ändring i den aldrig når förslaget.
    """

    __slots__ = ("__weakref__",)

    def __init__(self, nyckel, innehall):
        if nyckel is not _FORSLAGSNYCKEL:
            raise KonteringsforslagFel("Ett Konteringsforslag kan bara skapas av skapa_konteringsforslag, som kör K2"
                                       " och ursprungskontrollen först.", _INDATA)
        if self in _FORSLAGEN:
            raise KonteringsforslagFel("Ett Konteringsforslag kan inte ändras.", _INDATA)
        _FORSLAGEN[self] = _frys(innehall)

    def __setattr__(self, namn, varde):
        raise AttributeError("Ett Konteringsforslag kan inte ändras.")

    def __delattr__(self, namn):
        raise AttributeError("Ett Konteringsforslag kan inte ändras.")

    @property
    def forslag_id(self):
        return _innehallet(self)["forslag_id"]

    @property
    def verifikation(self):
        """Datum, text och rader, som en ny kopia. Varje rad har konto, debet_ore, kredit_ore och ursprung."""
        return _kopia(_innehallet(self)["verifikation"])

    @property
    def kopplingar(self):
        """Underlagen, bankraderna, Z-rapporterna och regeln, med kontrollsummorna, som en ny kopia."""
        return _kopia(_innehallet(self)["kopplingar"])

    @property
    def motivering(self):
        return _innehallet(self)["motivering"]

    @property
    def kontroller(self):
        """Kontrollerna som förslaget har klarat, som en ny kopia."""
        return _kopia(_innehallet(self)["kontroller"])

    def __repr__(self):
        innehall = _innehallet(self)
        verifikation = innehall["verifikation"]
        return ("Konteringsforslag(" + repr(innehall["forslag_id"]) + ", " + verifikation["datum"] + ", "
                + str(len(verifikation["rader"])) + " rader, debet = kredit = "
                + kronor(sum(rad["debet_ore"] for rad in verifikation["rader"])) + ")")


def skapa_konteringsforslag(forslag, regelbok, kontoplan, momssatser=None, underlagsperiod=None, bankperiod=None,
                            kassaperiod=None):
    """Kontrollerar förslaget med K2, ursprungskontrollen och K5, K7 och K8. Returnerar ett Konteringsforslag, annars fel.

    forslag är förslaget som objekt (se överst i filen). regelbok ska komma från las_regelbok,
    kontoplan från las_kontoplan, momssatser från las_momssatser, underlagsperiod från
    las_underlagsperiod, bankperiod från las_bankfil eller sla_ihop_bankperioder och kassaperiod från
    las_kassaperiod. En period som förslaget inte använder får vara None, och momsfilen får vara None
    bara när förslaget inte bygger på något underlag (K5, K7 och K8 gäller underlag). Allt som inte går
    ihop stoppar förslaget med ett KonteringsforslagFel.
    """
    _kontrollera_indatans_typer(regelbok, kontoplan, momssatser, underlagsperiod, bankperiod, kassaperiod)
    nytt = _kontrollera_formen(forslag)
    _kontrollera_kontrollsummor(nytt["kopplingar"]["regel"], regelbok, kontoplan, momssatser)
    _kontrollera_k2(nytt["verifikation"], kontoplan)
    kallorna = _kallorna(underlagsperiod, bankperiod, kassaperiod)
    kopplingar = _kontrollera_ursprung(nytt, regelbok, kontoplan, kallorna)
    kontroller = {_K2: "ok", _URSPRUNG: "ok"}
    kontroller.update(_kontrollera_underlagen(kopplingar, nytt["verifikation"], regelbok, kontoplan, momssatser,
                                              kallorna))
    return Konteringsforslag(_FORSLAGSNYCKEL, {
        "forslag_id": nytt["forslag_id"],
        "verifikation": nytt["verifikation"],
        "kopplingar": kopplingar,
        "motivering": nytt["motivering"],
        "kontroller": kontroller,
    })
