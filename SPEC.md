# SPEC – Veras bokföringsagent

| | |
|---|---|
| Bolag | Vera Labs AB (produkt: Vera AI) |
| Status | Godkänd av Hugo 2026-10-24 (utkast 1). Ändrad efter Hugos OK 2026-10-25: K1 kräver båda saldona, nya kontroller K11 och K12 (avsnitt 6), saldon och periodgränser (6.1), saknad Z-rapport (6.2), fyra nya säkerhetsgrunder (7), fast kommandolista (7.1), tillägg till Ö3 och Ö5 och momsfil för K5 (11). Senare samma dag, efter Hugos OK: K4a, K4b och K13 (6), `cd` och `tar` i 7.1, beslutet om minst en momsrad och Ö8–Ö10 (11) i commit 7133f15; matchningsformatet bland filerna som ska ligga skyddat (7) i commit a7cb12f; styrande och milda riktningstecken och en enda funktion per källa (7), K3 med väntetid och bankrader som inte kräver underlag (6) och Ö11 (11) efter granskning 5 (J10). Efter granskning 6 (L1), med Hugos OK: K4c, möjlig dublett (6). 2026-10-26, på Hugos uppdrag (uppgift 2 i DESIGN-regelbok.md): `las_regelbok` bland funktionerna per källa (7). Samma dag, efter Hugos beslut: `las_regelbok` läser också regelbokens lista över ägare och närstående (`agare_och_narstaende`, K7), där en regel för en sådan motpart alltid har nivå D (DESIGN-regelbok.md avsnitt 8). Samma dag, på Hugos uppdrag (uppgift 3 i DESIGN-regelbok.md): `skapa_konteringsforslag` för konteringsförslagen, med K2 och ursprungskontrollen (7). Ändras bara efter Hugos OK |
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
| K1 | Saldokedjan i bankfilen stämmer rad för rad. Kedjan börjar i **ingående saldo** (saldot när perioden börjar) och sista radens saldo ska vara lika med **utgående saldo** (saldot när perioden slutar). Båda saldona krävs, annars stoppas filen (6.1) |
| K2 | Debet = kredit per verifikation |
| K3 | Varje förslag har underlag. Ett saknat underlag blir ett ärende först när det har gått mer än ett visst antal dagar efter bankradens datum. Antalet är ett värde per företag i `matchning.json` (testbutiken har 7). Före dess väntar raden, eftersom underlaget kan komma in senare. Vissa bankrader kräver inte underlag och stäms av på annat sätt: kortinlösen, Swish och kontantinsättningar stäms av mot Z-rapporterna i K10. Regler för utgående rader som slipper underlag måste alltid ha en högsta summa per bankrad |
| K4 | Inga dubbletter |
| K4a | Samma motpart och fakturanummer men olika belopp. Blir ett ärende, och båda underlagen behålls |
| K4b | Samma motpart och fakturanummer men olika datum. Blir ett ärende, och båda underlagen behålls |
| K4c | Möjlig dublett: samma belopp och datum, och samma motpart eller samma fakturanummer, men inte båda (då är det en dublett, K4). Motpart och fakturanummer jämförs efter samma normalisering som i K4. Blir ett ärende, "möjlig dublett", och båda underlagen behålls. En människa avgör |
| K5 | Momsen stämmer med underlaget och satsen finns för datumet |
| K6 | Rätt period |
| K7 | Ägare och närstående: alltid ärende |
| K8 | Avdragsbegränsat (t.ex. representation): alltid ärende |
| K9 | Ovanliga belopp |
| K10 | Månadsavstämning: bank, kassa, skattekonto, leverantörsskulder, moms, försäljning mot kassa |
| K11 | Z-rapportens interna kontroller. En **Z-rapport** är kassans dagsavslut: försäljningen per momssats, momsen, hur kunderna betalade och dagens totalsumma. Varje Z-rapport har ett löpnummer, **Z-numret**. Kontrollen prövar att datumet i filen stämmer med datumet i filnamnet, att filen har ett enda Z-nummer och en enda kassa, att försäljningen summerar till totalsumman, att betalsätten summerar till totalsumman och att momsen stämmer med försäljningen och momssatsen |
| K12 | Z-serien, per kassa: Z-numren följer på varandra utan luckor eller dubbletter, och datumen går framåt |
| K13 | Underlagets interna kontroll: summan av momsraderna (belopp utan moms plus moms) är lika med underlagets belopp |
| K17 | Text i underlag som försöker styra agenten: flaggas, underlaget används inte |

### 6.1 Saldon och periodgränser

En **period** är den tid som stäms av, till exempel en månad. För att en period ska kunna kontrolleras krävs:

- **Bank:** ingående och utgående saldo.
- **Kassa:** periodens första och sista Z-nummer.

Värdena är obligatoriska. Saknas något stoppas perioden. De hämtas från kontoutdraget och stäms av mot nästa periods ingående värden, så att perioderna hänger ihop utan glapp. Avstämningen hör till K10.

### 6.2 Saknad Z-rapport

En saknad Z-rapport blir ett ärende på nivå D (avsnitt 5). Månaden summeras inte tyst, med eller utan den saknade rapporten. Ett undantag kräver ett uttryckligt godkännande av en människa hos företaget, och undantaget loggas.

---

## 7. Säkerhetsgrunder (gäller från första raden kod)

- **Inget bokförs utan godkännande** av en människa hos företaget, i båda lägena.
- **Bara läsrätt** till bank, mejl och bokföringsprogram när Vera hämtar underlag. Skrivrätt till bokföringsprogrammet finns bara i själva bokföringssteget efter godkännande.
- **En spärr läser aldrig från en mapp som agenten kan skriva i.** Det spärrarna jämför mot ska ligga skyddat.
- **Bankformat, kassaformat, matchningsformat och saldon ligger i en mapp som agenten inte kan skriva i**, och spärrarna läser bara därifrån. Byggs i spärrsteget. Fram till dess ligger formaten i `foretag/<namn>/`, som agenten kan skriva i.
- **Varje källa har en enda funktion som alltid kör alla kontroller** (idag `las_bankfil` för banken, `las_kassaperiod` för kassan, `las_underlagsperiod` för underlagen, `matcha_period` för matchningen mot banken, `las_kontoplan` för kontoplanen, `las_momssatser` för momsfilen och `las_regelbok` för regelboken). `las_regelbok` tar emot den redan inlästa kontoplanen, momsfilen och matchningsformatet, och räknar ut regelbokens kontrollsumma. På samma sätt skapas ett **konteringsförslag** bara av `skapa_konteringsforslag`, som tar emot regelboken, kontoplanen och perioderna från funktionerna ovan och alltid kör K2 och ursprungskontrollen: debet = kredit, och varje belopp räknas om i Python ur sitt ursprung (underlaget, bankraden eller Z-rapporten). Förslaget får regelbokens kontrollsumma, kan inte ändras och har inget fält för att vara bokfört eller godkänt. Genvägar förbi kontrollerna är förbjudna, och ett test slår larm om någon annan kod använder dem.
- **Styrande riktningstecken stoppar filen.** Riktningstecken är osynliga tecken som kan få en text att visas i en annan ordning än den är lagrad, så att till exempel en beskrivning ser ut som en annan. De **styrande** riktningstecknen (U+202A–U+202E och U+2066–U+2069) stoppar filen. De **milda riktningsmärkena** U+200E, U+200F och U+061C godtas, eftersom de förekommer i vanlig arabisk och hebreisk text, men ska visas synligt i rapporten. Andra osynliga **formattecken** (till exempel nollbreddsmellanslag) godtas, men ska visas synligt i rapporten så att godkännaren ser dem. **Kontoplanen och momsfilen är konfiguration och därför strängare än underlag:** där stoppar alla dolda tecken filen, även de milda riktningsmärkena och andra osynliga formattecken.
- **Fast lista med kommandon.** Agenten får bara köra de kommandon som står uttryckligen på listan (7.1).
- **Belopp är heltal i öre.** Aldrig flyttal. All matematik görs i Python, inte av modellen.
- **Underlag är data, aldrig instruktioner.**
- **Logg som inte kan skrivas om** (varje rad bär föregående rads hash).
- **Rättelser görs bara med motverifikation**, aldrig genom att ändra eller radera.
- **Spärrtester** körs vid varje ändring: bokföra utan godkännande, ändra efter godkännande, för stort belopp, förfalskat godkännande, ändrad regelbok, instruktion i underlag.
- Personuppgifter maskeras i loggar och rapporter.

### 7.1 Fast kommandolista

Listan gäller byggarbetet i Claude Code, inklusive granskningar. Veras egen lista med vad hon får köra hos en kund skrivs när hennes skript finns.

**Godkänd av Hugo 2026-10-25.** Listan bygger på de kommandon som faktiskt används i projektet. Allt körs inifrån projektmappen.

| Kommando | Till vad |
|---|---|
| `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests` | Köra testsviten med projektets egen Python (i mappen `.venv`) |
| `git status` | Se vilka filer som är ändrade |
| `git log` | Se tidigare ändringar |
| `git diff` | Se exakt vad som har ändrats |
| `git add` | Välja ut ändrade filer inför en commit |
| `git commit` | Spara ändringarna i projektets historik (en **commit**) |
| `ls`, `cat`, `head`, `tail`, `grep` | Läsa och söka i filer i projektet, utan att ändra något |
| `git show` | Visa en tidigare commit, eller en fil som den såg ut då |
| `git archive` | Ta ut en ren kopia av projektet ur historiken, till exempel inför en granskning, bara med mål utanför projektet (se nedan) |
| `diff` | Jämföra två filer eller mappar rad för rad |
| `find` | Leta upp filer efter namn eller typ, bara för att söka (se nedan) |
| `wc` | Räkna rader, ord eller tecken i en fil |
| `sort` | Sortera rader, till exempel för att jämföra två listor |
| `mkdir` | Skapa en mapp, bara i en tillfällig mapp utanför projektet (se nedan) |
| `cp -R` | Kopiera filer och mappar, bara till en tillfällig mapp utanför projektet (se nedan) |
| `cd` | Byta mapp, bara till en tillfällig mapp utanför projektet (se nedan) |
| `tar` | Packa upp eller packa ihop filer, bara med mål i en tillfällig mapp utanför projektet (se nedan) |

- `mkdir`, `cp -R` och `git archive` får bara ha mål i en tillfällig mapp utanför projektet (till exempel scratchpad-mappen), aldrig inne i projektmappen. Samma gräns gäller `cd` och `tar`.
- `find` används bara för att söka. Tilläggen `-delete` och `-exec`, som raderar filer eller kör andra kommandon, är förbjudna.
- Testsviten (pytest-kommandot ovan) får också köras mot en sådan kopia, och då inifrån kopian. Det är det enda undantaget från att allt körs inifrån projektmappen.
- Nya filer i projektet skapas med Claudes fil-verktyg (Write och Edit), inte med skalkommandon (kommandon i terminalen).

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

**Avgjort:** kontrollen K5 (momssatsen finns för datumet) kräver en momsfil i företagets konfiguration (`foretag/<namn>/`), med momssatser per varugrupp och datum. Vad som står i filen hänger på Ö3.

**Avgjort:** varje underlag har minst en momsrad. Ett momsfritt underlag har en rad med sats 0 och moms 0.

| # | Fråga | Ägare |
|---|---|---|
| Ö1 | **Produktionsarkitektur.** Version 1 körs lokalt som referensprodukt. Hur och var kundens data ska lagras säkert när Vera blir en tjänst är inte bestämt | Hugo |
| Ö2 | Vilka bokföringsprogram får direktkoppling först (Fortnox, Bokio, Spiris)? Version 1 använder SIE-export | Hugo |
| Ö3 | Momssatser och särregler per bransch (restaurang, bygg, begagnade varor) ska verifieras mot Skatteverket eller en redovisningskonsult innan de läggs i någon regelbok. Hit hör också **momsavrundning**: testdatan visar att kassan avrundar momsen till närmaste öre, men inte vad som gäller när momsen hamnar på exakt ett halvt öre. Och **Z-nummer som börjar om**, till exempel vid årsskifte: kanske tillåtet, och ska kontrolleras med kassaleverantören eller en redovisningskonsult. Tills dess stoppas en Z-serie som börjar om (K12) | Konsult |
| Ö4 | Får rutinposter i kassa bokföras samlat per vecka? | Konsult |
| Ö5 | Vilka kassasystem och bankformat ska stödjas först. Bankformatet, kassaformatet och att bankfilens rader numreras 1, 2, 3 … är **antaget** för testföretaget och ska jämföras mot riktiga exportfiler innan de används på riktiga underlag | Hugo |
| Ö7 | Hur får Vera tillgång till bank, mejl och bokföringsprogram i automatiskt läge, och hur säkras det? | Hugo |
| Ö8 | **Kreditnotor:** en egen dokumenttyp där alla belopp är negativa. Ingen annan typ får vara negativ | Hugo |
| Ö9 | K4 (dubbletter) ska också jämföra mot underlag från tidigare perioder (arkivet), inte bara inom perioden | Hugo |
| Ö10 | K17: att känna igen instruktionsliknande text i underlag och flagga den byggs i rapportsteget | Hugo |
| Ö11 | **Bankens avgiftsspecifikation** ska bli ett riktigt underlag med en egen dokumenttyp, så att bankens avgifter matchas som andra utgifter. Tills dess slipper avgifterna underlag genom en regel i `matchning.json`, med en högsta summa per bankrad | Hugo |
