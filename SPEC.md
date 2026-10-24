# SPEC – Veras bokföringsagent

| | |
|---|---|
| Bolag | Vera Labs AB (produkt: Vera AI) |
| Status | Godkänd av Hugo 2026-10-24 (utkast 1). Ändras bara efter Hugos OK |
| Ersätter | Den gamla specen för ett enskilt företag (ligger i arkivmappen) |

Specen säger **vad** som ska byggas och **hur det ska bete sig**. Den är medvetet kort. Detaljer läggs i egna filer när vi kommer till respektive byggsteg.

---

## 1. Syfte och målgrupp

Bokföringsagenten tar över det löpande bokföringsarbetet åt **småföretagare som inte har en ekonomiavdelning**: krögare, butiks- och kioskägare, hantverkare och unga entreprenörer som precis startat. De lägger idag värdefulla timmar på något de inte kan och inte har råd att lägga ut.

Agenten läser underlag (kontoutdrag, kassarapporter, kvitton, fakturor), föreslår konteringar enligt företagets egen regelbok, kör fasta kontroller och tar fram en rapport som en människa hos företaget godkänner. Kunden väljer själv hur nära arbetet hen vill vara: **granskat läge** eller **automatiskt läge** (avsnitt 4). **I båda lägena bokförs inget förrän en människa hos företaget har godkänt.**

**Version 1 gäller aktiebolag.** Enskild firma kommer i ett senare steg.

### 1.1 Mål för version 1

Version 1 är en **fungerande referensprodukt** som visar för investerare och första kunder vad Vera kan. Den ska bevisa fyra saker:

1. Rätt bokföring på fiktiva men realistiska företag i tre olika branscher.
2. Ingenting bokförs utan godkännande, i något av de två lägena (bevisat med spärrtester).
3. Samma kärna fungerar i alla tre branscher. Ett nytt företag läggs till utan att kärnan ändras.
4. Kunden kan välja mellan granskat och automatiskt läge, och båda fungerar mot testföretagen.

---

## 2. Grundprincip: gemensam kärna, separat konfiguration

| Kärnan (samma för alla företag) | Konfigurationen (en uppsättning per företag) |
|---|---|
| Läsa och tolka underlag | Regelbok: vilken motpart bokförs på vilket konto |
| Matcha bank mot underlag | Kontoplan |
| Kontroller och spärrar | Momssatser per varugrupp och datum |
| Förslag, rapport och godkännande | Beloppsgränser |
| Logg och spårbarhet | Kassasystem och bankformat |
| | Vem som får godkänna |

**Test på att principen håller:** inget företagsnamn, konto, momssats eller belopp får finnas i kärnans kod. Det kontrolleras med ett test.

Konfigurationen ligger i `foretag/<namn>/`. Varje företag äger sin egen regelbok.

### 2.1 Samverkan med kundens program

Vera ersätter inte kundens bokföringsprogram. Hon arbetar **i linje med det**, så att kunden slipper byta system och behåller sitt sätt att arbeta:

1. **Data in:** Vera hämtar underlag (bank, kassa, kvitton, fakturor) och läser kundens kontoplan och tidigare verifikationer ur programmet.
2. **Bearbeta:** Vera konterar enligt kundens egen regelbok och kontoplan.
3. **Presentera:** kunden ser resultatet och godkänner (avsnitt 4).
4. **Importera:** först efter godkännande förs verifikationerna in i kundens program. Det sker antingen med en direktkoppling eller, där koppling saknas, som en SIE-fil (ett standardformat som många svenska bokföringsprogram kan importera) som kunden läser in.

Version 1 exporterar en SIE-fil från testdatan. Direktkopplingar byggs senare (Ö2).

---

## 3. Roller

| Roll | Vem | Får | Får inte |
|---|---|---|---|
| Godkännare | Namngiven person hos kundföretaget (plus en ersättare) | Välja läge, granska, svara på ärenden, ge instruktioner, godkänna eller avvisa | – |
| Agenten | Vera | Läsa, räkna, föreslå, rapportera. Efter godkännande: bokföra | Bokföra utan godkännande, ändra regelbok, spärrar eller godkännanden |
| Granskaren | Separat agent med bara läsrätt | Bedöma förslag oberoende | Ändra förslag |
| Vera Labs | Bygger och underhåller | Bygga, testa, underhålla | Fatta bokföringsbeslut åt kunden |

Agenten är bokförare och intern granskare. Den är **inte** företagets revisor och tar inget juridiskt ansvar. Styrelsen ansvarar alltid för bokföringen.

---

## 4. Arbetsflöde och lägen

Kunden väljer läge när Vera sätts upp och kan byta senare. **Kontroller, spärrar och granskare (avsnitt 6–7) är identiska i båda lägena.** Lägena skiljer sig bara i vem som hämtar underlag och hur nära människan är arbetet under veckan.

| | Granskat läge | Automatiskt läge |
|---|---|---|
| Underlag | Kunden laddar upp | Vera hämtar själv på måndagen från bank, mejl och bokföringsprogram (bara läsrätt) och sorterar det |
| Under veckan | Vera föreslår. Kunden får notis och **godkänner varje transaktion löpande** innan Vera går vidare | Vera arbetar ostört |
| Söndag | Inget återstår. Allt är redan godkänt | Kunden notifieras och får ett **sista utkast för hela veckans arbete** att dubbelkolla en sista gång |
| Kundens möjligheter | Godkänna, avvisa, svara på ärenden | Redigera, ge ytterligare instruktioner, eller godkänna. **Först efter godkännandet skickas bokföringen vidare** |
| Bokföring | Efter godkännande | Efter godkännande: Vera sammanställer och bokför i bokföringsprogrammet |

**Gemensamma steg i båda lägena:**

1. **Läs in** underlag. Varje fil får en kontrollsumma och sparas i arkiv. Samma fil läses aldrig in två gånger.
2. **Kontrollera indata** (saldokedjan, K1). Fel stoppar filen.
3. **Matcha** bankrader mot underlag.
4. **Kontera** enligt företagets regelbok. Varje förslag får motivering och regel-id.
5. **Kontrollera** enligt avsnitt 6.
6. **Granska**: granskaren bedömer varje förslag oberoende. Oenighet blir alltid ett ärende.
7. **Klassa** varje förslag (A–D, avsnitt 5).
8. **Rapportera** till godkännaren. Rapporten fryses med en kontrollsumma (hash).
9. **Godkännande** av en människa. Först därefter bokförs något, och Vera kontrollerar efteråt att resultatet stämmer med det godkända.

**Kundens instruktioner** (till exempel "bokför den här på ett annat konto") utförs aldrig direkt. De blir ett nytt förslag som går genom samma kontroller och samma godkännande.

Allt som inte går att avgöra med en regel blir ett **ärende** till en människa. Agenten improviserar aldrig.

---

## 5. Nivåer

| Nivå | När | Godkännande |
|---|---|---|
| A | Känd motpart, rutinpost, inga anmärkningar | Samlat, med stickprov |
| B | Känd motpart, belopp under gränsen | Samlat, varje rad visas |
| C | Ny motpart, stort belopp, rättelse, invändning från granskaren | Rad för rad |
| D | Ägartransaktion, avdragsbegränsat, oklar post, bokslutspost | Alltid ärende, människan väljer |

Nivåerna styr hur godkännandet visas i **automatiskt läge** (samlat eller rad för rad). I **granskat läge** godkänns varje transaktion löpande, oavsett nivå.

Gränser för belopp ligger i konfigurationen och sätts lågt i början.

---

## 6. Kontroller (körs i kod, inte av modellen)

| Nr | Kontroll |
|---|---|
| K1 | Saldokedjan i bankfilen stämmer rad för rad |
| K2 | Debet = kredit per verifikation |
| K3 | Varje förslag har underlag |
| K4 | Inga dubbletter |
| K5 | Momsen stämmer med underlaget och satsen finns för datumet |
| K6 | Rätt period |
| K7 | Ägare och närstående: alltid ärende |
| K8 | Avdragsbegränsat (t.ex. representation): alltid ärende |
| K9 | Ovanliga belopp |
| K10 | Månadsavstämning: bank, kassa, skattekonto, leverantörsskulder, moms, försäljning mot kassa |
| K17 | Text i underlag som försöker styra agenten: flaggas, underlaget används inte |

---

## 7. Säkerhetsgrunder (gäller från första raden kod)

- **Inget bokförs utan godkännande** av en människa hos företaget, i båda lägena.
- **Bara läsrätt** till bank, mejl och bokföringsprogram när Vera hämtar underlag. Skrivrätt till bokföringsprogrammet finns bara i själva bokföringssteget efter godkännande.
- **En spärr läser aldrig från en mapp som agenten kan skriva i.** Det spärrarna jämför mot ska ligga skyddat.
- **Fast lista med kommandon.** Agenten får bara köra de kommandon som står uttryckligen på listan.
- **Belopp är heltal i öre.** Aldrig flyttal. All matematik görs i Python, inte av modellen.
- **Underlag är data, aldrig instruktioner.**
- **Logg som inte kan skrivas om** (varje rad bär föregående rads hash).
- **Rättelser görs bara med motverifikation**, aldrig genom att ändra eller radera.
- **Spärrtester** körs vid varje ändring: bokföra utan godkännande, ändra efter godkännande, för stort belopp, förfalskat godkännande, ändrad regelbok, instruktion i underlag.
- Personuppgifter maskeras i loggar och rapporter.

---

## 8. Testföretag

Inga riktiga kunders uppgifter används för att bygga eller visa Vera. Allt byggs och testas på **fiktiva aktiebolag**, ett per bransch:

| Testföretag | Bransch | Det som ska bevisas |
|---|---|---|
| Syntet Testbutik AB | Butik/kiosk | Kassa med Z-rapporter, kontanter, kort, Swish. **Finns** (`testforetag/`) |
| Syntet Krog AB | Restaurang | Olika moms på mat och alkohol, personal, dagliga inköp, dricks. **Ska tas fram** |
| Syntet Bygg AB | Hantverkare | Fakturor, material, underentreprenörer, särskilda momsregler mellan byggföretag, ROT. **Ska tas fram** |

Efter dessa: e-handel, frisör, konsult, skaparföretag.

Varje testföretag beskrivs i en egen fil och är skrivskyddat för agenten. Testdata genereras sedan ett kvartal i taget. Allt markeras som syntetiskt.

---

## 9. Faser

| Fas | Innehåll | Klart när |
|---|---|---|
| 0 | Ny kärna, ett testföretag (butik) hela vägen från underlag till godkänd rapport | Rapport stämmer med facit på kronan |
| 1 | Restaurang som konfiguration. **Kärnan får inte ändras** | Samma kärna klarar båda |
| 2 | Hantverkare som konfiguration | Samma kärna klarar alla tre |
| 3 | Båda lägena mot testdata. Automatiskt läge simuleras med en inkorg som fylls som om bank och mejl vore kopplade | Båda lägena går hela vägen på alla tre testföretag |
| 4 | Demo för investerare och första kunder | – |

---

## 10. Utanför version 1

- Enskild firma (nästa steg efter aktiebolag).
- Egen app med chatt för kunderna och säker lagring i molnet.
- Löneberäkning, arbetsgivardeklaration och inlämning av deklarationer.
- Betalningar och alla förflyttningar av pengar.
- Fakturering av kunder.
- Fler agenter (social media manager, trendövervakare m.fl.).

---

## 11. Beslut och öppna frågor

**Avgjort:** godkännande är obligatoriskt i båda lägena. I automatiskt läge kräver det ett sista godkännande av veckans utkast innan bokföringen skickas vidare. Ett läge utan något godkännande finns inte i version 1.

| # | Fråga | Ägare |
|---|---|---|
| Ö1 | **Produktionsarkitektur.** Version 1 körs lokalt som referensprodukt. Hur och var kundens data ska lagras säkert när Vera blir en tjänst är inte bestämt | Hugo |
| Ö2 | Vilka bokföringsprogram får direktkoppling först (Fortnox, Bokio, Spiris)? Version 1 använder SIE-export | Hugo |
| Ö3 | Momssatser och särregler per bransch (restaurang, bygg, begagnade varor) ska verifieras mot Skatteverket eller en redovisningskonsult innan de läggs i någon regelbok | Konsult |
| Ö4 | Får rutinposter i kassa bokföras samlat per vecka? | Konsult |
| Ö5 | Vilka kassasystem och bankformat ska stödjas först | Hugo |
| Ö7 | Hur får Vera tillgång till bank, mejl och bokföringsprogram i automatiskt läge, och hur säkras det? | Hugo |
