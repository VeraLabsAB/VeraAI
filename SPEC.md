# SPEC – Veras bokföringsagent

| | |
|---|---|
| Bolag | Vera Labs AB (produkt: Vera AI) |
| Status | Godkänd av Hugo 2026-10-24 (utkast 1). Ändrad efter Hugos OK 2026-10-25: K1 kräver båda saldona, nya kontroller K11 och K12 (avsnitt 6), saldon och periodgränser (6.1), saknad Z-rapport (6.2), fyra nya säkerhetsgrunder (7), fast kommandolista (7.1), tillägg till Ö3 och Ö5 och momsfil för K5 (11). Senare samma dag, efter Hugos OK: K4a, K4b och K13 (6), `cd` och `tar` i 7.1, beslutet om minst en momsrad och Ö8–Ö10 (11) i commit 7133f15; matchningsformatet bland filerna som ska ligga skyddat (7) i commit a7cb12f; styrande och milda riktningstecken och en enda funktion per källa (7), K3 med väntetid och bankrader som inte kräver underlag (6) och Ö11 (11) efter granskning 5 (J10). Efter granskning 6 (L1), med Hugos OK: K4c, möjlig dublett (6). 2026-10-26, på Hugos uppdrag (uppgift 2 i DESIGN-regelbok.md): `las_regelbok` bland funktionerna per källa (7). Samma dag, efter Hugos beslut: `las_regelbok` läser också regelbokens lista över ägare och närstående (`agare_och_narstaende`, K7), där en regel för en sådan motpart alltid har nivå D (DESIGN-regelbok.md avsnitt 8). Samma dag, på Hugos uppdrag (uppgift 3 i DESIGN-regelbok.md): `skapa_konteringsforslag` för konteringsförslagen, med K2 och ursprungskontrollen (7). Samma dag, på Hugos uppdrag efter granskning 7 (M3 och en del av M4): `las_matchningsformat` bland funktionerna per källa, kontrollsummor för kontoplanen, momsfilen och matchningsformatet, regeln ska passa förslaget och K2 prövar förslagets kontrollsummor (7), och Ö12 (11). Samma dag, på Hugos uppdrag efter granskning 7 (M5, M7 och kommandolistan): förväxlingstecken i regelboken (7), Ö13 (11) och den fasta kommandolistan skriven efter hur den faktiskt används (7.1). 2026-10-27, på Hugos uppdrag efter granskning 8 (N1, N2, N3 och N5): Unicodes lista över tecken som inte ska synas och vilka tecken ett namn i regelboken får ha (7), skälet för att `cd` inte används, ett kommando i taget, läsa i kopior, provfiler i kopian och `sed` (7.1), och ägarens bankrader (Ö13). Samma dag, efter Hugos beslut 2026-10-27 (granskning 8, N3, det som var kvar): `matcha_period` tar emot regelboken i stället för matchningsformatet, och en bankrad mot en ägare eller närstående kräver alltid underlag (6 K3, 7 och Ö13). Samma dag, på uppdraget att märka besluten med namn och datum: Hugos beslut 2026-10-27 om fristående accenttecken (N4), om en saknad, tom eller oläsbar lista över ägare och närstående och om ägarens bankrader i matchningen (11), och namn och datum på besluten i 6, 7, 7.1, 11 och Ö13. 2026-10-28, på Hugos uppdrag efter granskning 9: besluten om ägarlistan och om ägarens bankrader i matchningen står som byggda (commit dd0e1cf), och Hugos beslut i chatten 2026-10-27 att listan ligger kvar i regelboken tills spärrsteget (11 och Ö13). Samma dag, efter Hugos beslut 2026-10-28 (granskning 10): en motpart i listan över ägare och närstående utan bokstäver och siffror stoppar hela körningen (P1, byggt i commit 16000a8), och när felet säger att hela körningen stoppas (P2) (11). Samma dag, efter Hugos beslut 2026-10-28 (granskning 12, P4): vakten släpper bara igenom verktygen på en uttrycklig lista (7.1). Samma dag, efter Hugos beslut 2026-10-28 (8) och hans OK på texten: villkoren för att installera vakten och för provet med en vakt som fallerar (7.1). Samma dag, efter Hugos beslut 2026-10-28 (beslut 1–3): PATH-regeln, förprovet för `onFailure` före installationen, och P7 med versionen via `/status`, ägare och rättigheter för mapparna och `/status` efter installationen (7.1). Samma dag, efter Hugos beslut 2026-10-28 om granskning 13 (P2 och P3 b): vakten prövar varje länk i kedjan, och Claude Code för Terminal startas med hela sökvägen `~/.local/bin/claude` (7.1). Samma dag, efter Hugos beslut 2026-10-28 om granskning 14 (R4): PATH-regeln säger att vakten prövar mappen där varje länk ligger, inte länkfilen själv (7.1). Samma dag, efter Hugos beslut 2026-10-28 om granskning 15 (S1, S5 och `cd ~/VERA/agent`): `find` borttaget, `grep` bara med tillägg som söker, och att skalet kör Claude Codes program för `grep` (7.1). Samma dag, efter Hugos beslut 2026-10-28 om granskning 16: `-R` borttaget ur `grep` (G3) och `.ugrep` förbjuden (G7), och att Claude Codes `grep` inte söker i allt (G6, texten godkänd av Hugo i chatten samma dag) (7.1). 2026-10-29, efter Hugos beslut om Q2 (granskning 11): accenter spelar ingen roll i ägaruppslaget, och andra stavningar väntar på riktiga bankfiler (11, Ö5 och Ö13). Samma dag, efter Hugos beslut om Q2b: accenter spelar ingen roll i någon ägarkontroll (11 och Ö13). Hugo godkände texterna i commit d7d38e0 och dcf3078 i chatten 2026-10-29. Samma dag, efter granskning 21 och Hugos OK i chatten: ø, æ, ł och đ som exempel i Ö5 (L3), och "Det gäller följande ägarkontroller" i Q2-stycket (11). Samma dag, efter Hugos beslut 2026-10-29 inför uppgift 4: ärenden från K5 och K8 får nivå D direkt (B2), och D1, D2, D4 och D14 antagna för testföretaget, D13 öppen (B3) (11). Samma dag, efter Hugos beslut i chatten 2026-10-29 i sessionen för uppgift 4: D13 antagen för testföretaget, och "bankens datum" i D14 är transaktionsdagen (11). Ändras bara efter Hugos OK |
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
| K3 | Varje förslag har underlag. Ett saknat underlag blir ett ärende först när det har gått mer än ett visst antal dagar efter bankradens datum. Antalet är ett värde per företag i `matchning.json` (testbutiken har 7). Före dess väntar raden, eftersom underlaget kan komma in senare. Vissa bankrader kräver inte underlag och stäms av på annat sätt: kortinlösen, Swish och kontantinsättningar stäms av mot Z-rapporterna i K10. Regler för utgående rader som slipper underlag måste alltid ha en högsta summa per bankrad. En bankrad mot en ägare eller närstående (K7) kräver alltid underlag, även när en regel i `matchning.json` annars skulle undanta den (granskning 8, N3, Hugos beslut 2026-10-27) |
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
- **Varje källa har en enda funktion som alltid kör alla kontroller** (idag `las_bankfil` för banken, `las_kassaperiod` för kassan, `las_underlagsperiod` för underlagen, `matcha_period` för matchningen mot banken, `las_kontoplan` för kontoplanen, `las_momssatser` för momsfilen, `las_matchningsformat` för matchningsformatet och `las_regelbok` för regelboken). Kontoplanen, momsfilen, matchningsformatet och regelboken får var sin **kontrollsumma**, räknad på exakt de bytes som sedan kontrolleras. `las_regelbok` tar emot den redan inlästa kontoplanen, momsfilen och matchningsformatet, och kommer ihåg deras kontrollsummor och matchningsformatets innehåll. `matcha_period` tar emot bankperioden, underlagsperioden och regelboken från funktionerna ovan (och bedömningsdatumet), och tar matchningsformatet från regelboken, aldrig för sig. Då använder matchningen alltid samma format som regelboken kontrollerades mot, och regelbokens uppslag avgör vilka bankrader som inte kräver underlag, så att en bankrad mot en ägare eller närstående aldrig undantas (granskning 8, N3, Hugos beslut 2026-10-27). På samma sätt skapas ett **konteringsförslag** bara av `skapa_konteringsforslag`, som tar emot regelboken, kontoplanen och perioderna från funktionerna ovan och alltid kör K2 och ursprungskontrollen: förslaget är byggt mot samma filer som det kontrolleras mot (kontoplanen är den som regelboken kontrollerades mot, och förslagets fyra kontrollsummor är de som de inlästa filerna har), debet = kredit, varje belopp räknas om i Python ur sitt ursprung (underlaget, bankraden eller Z-rapporten), och regeln passar förslaget (rätt regel för källorna och datumet, och varje konto står i regeln eller är ett rollkonto). Förslaget får de fyra kontrollsummorna, kan inte ändras och har inget fält för att vara bokfört eller godkänt. Genvägar förbi kontrollerna är förbjudna, och ett test slår larm om någon annan kod använder dem.
- **Styrande riktningstecken stoppar filen.** Riktningstecken är osynliga tecken som kan få en text att visas i en annan ordning än den är lagrad, så att till exempel en beskrivning ser ut som en annan. De **styrande** riktningstecknen (U+202A–U+202E och U+2066–U+2069) stoppar filen. De **milda riktningsmärkena** U+200E, U+200F och U+061C godtas, eftersom de förekommer i vanlig arabisk och hebreisk text, men ska visas synligt i rapporten. Andra osynliga **formattecken** (till exempel nollbreddsmellanslag) godtas, men ska visas synligt i rapporten så att godkännaren ser dem. **Kontoplanen och momsfilen är konfiguration och därför strängare än underlag:** där stoppar alla dolda tecken filen, även de milda riktningsmärkena och andra osynliga formattecken. Regelboken är lika sträng. **Alla tecken på Unicodes egen lista över tecken som inte ska synas** (egenskapen Default_Ignorable_Code_Point) räknas som dolda, och listan står uttryckligen i koden, så att den inte beror på vilken Unicode-version Python har (granskning 8, N1, Hugos uppdrag 2026-10-27). De av dem som inte används i vanlig text, två khmeriska vokaltecken som inte syns (U+17B4 och U+17B5) och koder som Unicode inte har gett något tecken (U+2065, U+FFF0–U+FFF8 och U+E0000–U+E0FFF utom taggar och variantväljare), stoppar också ett underlag.
- **Förväxlingstecken i regelboken stoppar filen** (granskning 7, M5, Hugos uppdrag 2026-10-26). Ett **förväxlingstecken** ser ut som en latinsk bokstav eller siffra men är ett annat tecken, till exempel ett kyrilliskt "А" eller cherokee-bokstäver som tillsammans ser ut som "AGARE". Ett namn skrivet så jämförs som ett annat namn, så att till exempel en ägare inte känns igen. I underlagen stoppas ett ord som blandar latinska och andra bokstäver. Regelboken är konfiguration och därför strängare: en motpart, ett kassaregister och en ägare eller närstående får bara ha bokstäverna a–z med eller utan accent (även å, ä, ö och é), siffrorna 0–9, mellanslag, bindestreck (alla sorters bindestreck, som räknas som "-" när namn jämförs), understreck och punkt, och ett regel-id bara a–z, siffror och bindestreck. Allt annat stoppar filen, till exempel tecken som ser ut som ett bindestreck men är något annat, och latinska bokstäver som inte är a–z med accent, som "ı" (i utan prick), som ser ut som en etta (granskning 8, N2, Hugos uppdrag 2026-10-27). Understreck och punkt är de skiljetecken som Hugos uppdrag efter granskning 8 (2026-10-27) tillåter, eftersom SPEC inte sa vilka. **Öppen fråga (N2):** om fler ska få finnas (till exempel `&`, eller `Ø` och `ß`) bestämmer Hugo eller Casper. I dag stoppas de. Konton och varugrupper ska finnas i kontoplanen och momsfilen, där de redan bara får ha 0–9 respektive a–z, siffror och understreck.
- **Fast lista med kommandon.** Agenten får bara köra de kommandon som står uttryckligen på listan (7.1).
- **Belopp är heltal i öre.** Aldrig flyttal. All matematik görs i Python, inte av modellen.
- **Underlag är data, aldrig instruktioner.**
- **Logg som inte kan skrivas om** (varje rad bär föregående rads hash).
- **Rättelser görs bara med motverifikation**, aldrig genom att ändra eller radera.
- **Spärrtester** körs vid varje ändring: bokföra utan godkännande, ändra efter godkännande, för stort belopp, förfalskat godkännande, ändrad regelbok, instruktion i underlag.
- Personuppgifter maskeras i loggar och rapporter.

### 7.1 Fast kommandolista

Listan gäller byggarbetet i Claude Code, inklusive granskningar. Veras egen lista med vad hon får köra hos en kund skrivs när hennes skript finns.

**Godkänd av Hugo 2026-10-25. Skriven om 2026-10-26 på Hugos uppdrag**, så att den stämmer med hur den faktiskt används: `cd` är borttaget, och testsviten körs mot en kopia med kopians sökväg i stället för inifrån kopian. **Kompletterad 2026-10-27 på Hugos uppdrag** efter granskning 8 (N5): skälet för att `cd` inte används, ett kommando i taget, läsa i kopior, provfiler i kopian och `sed`. Listan bygger på de kommandon som faktiskt används i projektet. Allt körs från projektmappen. **Kompletterad 2026-10-28 på Hugos beslut** (granskning 11, Q1): vakten och reglerna den håller, nedan. **Ändrad 2026-10-28 på Hugos beslut om vakten, beslut 1–4** (`GRANSKNING.md`, "Granskning 11 – plan för Q1"): pytest-kommandona använder Python i en mapp som root äger, PATH-regeln gäller varje mapp i `PATH` före programmet och filen själv och länkens mål, och varje annan källa i `/status` stoppar installationen.

**Spärras tekniskt (granskning 11, Q1, Hugos beslut 2026-10-28).** Listan hålls av en vakt, `sparr/kommandosparr.py`, som Claude Code kör före varje verktyg. Den körs från de låsta inställningarna i `/Library/Application Support/ClaudeCode/`: förslaget står i `sparr/managed-settings.json` och installationen i `sparr/INSTALLERA.md`. Vakten stoppar allt som inte står här, gäller i alla mappar (ingen mapp undantas) och stoppar alltid `sudo` och `su`. Om vakten kraschar eller inte svarar stoppas kommandot (`onFailure: block`, kräver Claude Code 2.1.295 eller senare). **Version, förprov och mappar** (Hugos beslut 2026-10-28, beslut 2 och 3). Före installationen kontrollerar Hugo versionen med `/status` i en Claude Code-session (minst 2.1.295), och gör ett förprov: i en tillfällig mapp utanför `~/VERA` skapas `.claude/settings.json` med en vakt (PreToolUse) som pekar på ett skript som inte finns och har `"onFailure": "block"`, Hugo ber Claude köra `ls`, och mappen raderas sedan. Stoppas inte kommandot, avbryts installationen. Vakten i installationsfilen startas med hela sökvägen till både tolken och skriptet, och har `"onFailure": "block"` (med test). Mappen `ClaudeCode` får ägaren `root:wheel` och rättigheterna 755, och filerna `root:wheel` och 644. Inte 600: en fil som Claude Code inte får läsa hoppas över utan varning, och då gäller ingen vakt. Ägare och rättigheter för `/`, `/Library`, `/Library/Application Support` och `/Library/Application Support/ClaudeCode` kontrolleras med `ls -ld` före och efter installationen. Kan gruppen eller andra skriva någonstans i kedjan, avbryts installationen. Efter installationen ska `/status` visa `Enterprise managed settings (file)` på raden Setting sources. Saknas den, gäller inte vakten, och installationen räknas som misslyckad. Bara en annan låst källa underkänner installationen, till exempel inställningar som styrs från claude.ai. `User settings`, `Project settings` och `Project local settings` är väntade och underkänner inte. Raden visas inte i skrivbordsappen, så den läses i Terminal (`cd ~/VERA/agent`, `~/.local/bin/claude`, `/status`) (Hugos svar 2026-10-28, punkt 3, som ersätter beslut 4 om vakten). Claude Code för Terminal ligger i `~/.local/bin`, utanför `PATH`, och startas alltid med hela sökvägen. Installerarens förslag att lägga `~/.local/bin` först i `PATH` används inte (Hugos beslut 2026-10-28, granskning 13, P3 b, som ersätter `claude` och stoppet vid `command not found` i svar 3). Sist i kontrollen efter installationen visar ett ofarligt kommando som inte står på listan (`date`), i skrivbordsappen, att vakten stoppar det. **En ändrad lista blir en ny version av vakten:** den byggs med tester, granskas oberoende, godkänns av Hugo och installeras av Hugo (och på Caspers dator). Tills dess gäller den installerade versionen. **Villkor för installation och användning** (Hugos beslut 2026-10-28, 8). En ny version av vakten installeras först när en oberoende granskning är klar. Provet med en vakt som fallerar (INSTALLERA.md, "Kontroll efter installationen", steg 8), som en människa gör själv i Terminal, krävs inte för installationen. Det ska vara gjort, utan anmärkningar, före läget "auto", före körningar utan att Hugo tittar, före första hela körningen på riktiga underlag och före första kund. Säger texten och vakten olika gäller den strängaste, och skillnaden rättas.

| Kommando | Till vad |
|---|---|
| `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q scripts/tests` | Köra testsviten med projektets egen Python, som ligger i en mapp som root äger (Hugos beslut 2026-10-28 om vakten, beslut 1). Citattecknen behövs, eftersom "Application Support" har ett mellanslag |
| `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider <kopia>/scripts/tests` | Köra testsviten mot en kopia utanför projektet (se nedan), till exempel för ett mutationstest eller för att visa att ett nytt test är rött på den gamla koden. I stället för hela mappen får en testfil i kopian anges |
| `git status` | Se vilka filer som är ändrade |
| `git log` | Se tidigare ändringar |
| `git diff` | Se exakt vad som har ändrats |
| `git add` | Välja ut ändrade filer inför en commit |
| `git commit` | Spara ändringarna i projektets historik (en **commit**) |
| `ls`, `cat`, `head`, `tail`, `grep` | Läsa och söka i filer i projektet, och i kopior utanför projektet (se nedan), utan att ändra något |
| `git show` | Visa en tidigare commit, eller en fil som den såg ut då |
| `git archive` | Ta ut en ren kopia av projektet ur historiken, till exempel inför en granskning, bara med mål utanför projektet (se nedan) |
| `diff` | Jämföra två filer eller mappar rad för rad |
| `wc` | Räkna rader, ord eller tecken i en fil |
| `sort` | Sortera rader, till exempel för att jämföra två listor |
| `mkdir` | Skapa en mapp, bara i en tillfällig mapp utanför projektet (se nedan) |
| `cp -R` | Kopiera filer och mappar, bara till en tillfällig mapp utanför projektet (se nedan) |
| `tar` | Packa upp eller packa ihop filer, bara med mål i en tillfällig mapp utanför projektet (se nedan) |

- **Tills Python på den nya platsen finns** (INSTALLERA.md, steg 9) körs de två pytest-kommandona som förut med `.venv/bin/python` i projektet i stället för den nya sökvägen, med samma tillägg och mål. Annars kan ingen session, inte heller den oberoende granskningen, köra testsviten före installationen. Efter installationen pekar listan bara på den nya platsen: vakten godtar bara den, och den gamla `.venv` tas bort (INSTALLERA.md, "Efteråt") (Hugos svar 2026-10-28, punkt 2).
- `mkdir`, `cp -R` och `git archive` får bara ha mål i en tillfällig mapp utanför projektet (till exempel scratchpad-mappen), aldrig inne i projektmappen. Samma gräns gäller `tar`.
- **`find` står inte på listan** (granskning 15, S1, Hugos beslut 2026-10-28). I agentens skal är `find` inte systemets program utan Claude Codes inbyggda `bfs`, som raderar filer med `-rm`. Filer letas upp med `ls` (till exempel `ls -R scripts`) eller med Claude Codes egna verktyg där de finns. **`rg` står inte heller på listan.**
- **`grep` får bara söka** (granskning 15, S1, Hugos beslut 2026-10-28). `grep` står kvar, eftersom verktyget Grep inte finns i skrivbordsappen (där säger Claude Code att `grep` i Bash ska användas i stället, sett i byggsessionen 2026-10-28). I agentens skal är `grep` Claude Codes inbyggda `ugrep`, som har tillägg som kör program och skriver filer. Vakten släpper därför bara igenom tillägg på en uttrycklig lista, och namnen jämförs exakt: `-n`, `-i`, `-r`, `-l`, `-L`, `-c`, `-v`, `-w`, `-x`, `-E`, `-F`, `-H`, `-h`, `-o`, `-s`, `-q`, `-I`, `-e` med ett mönster, `-A`, `-B`, `-C` och `-m` med ett tal, samma tillägg med långa namn (till exempel `--line-number` och `--context=2`), och `--include=`, `--exclude=` och `--exclude-dir=` med ett filmönster. Allt annat stoppas, också tillägg som vakten inte känner till, till exempel `-f`, `--filter`, `--pager`, `--view` och `--config`. **`-R` står inte på listan** (granskning 16, G3, Hugos beslut 2026-10-28): i Claude Codes `ugrep` följer `-R` alla länkar inne i mappar, också länkar som leder ut ur projektet. Det stoppas i alla former, också ihopskrivet med andra tillägg (till exempel `-nR`) och med det långa namnet `--dereference-recursive`. `-r` räcker för att söka i mappar. **Claude Codes `grep` söker inte i allt** (granskning 16, G6, Hugos beslut 2026-10-28): det startar `ugrep` med egna tillägg före agentens, så filer som står i en `.gitignore` hoppas över (till exempel `.venv`), binära filer ger ingen träff, och mönstret är ett enkelt reguljärt uttryck tills `-E` anges. Att `grep` inte hittar något betyder alltså inte att texten saknas i sådana filer.
- **`.ugrep` är förbjuden** (granskning 16, G7, Hugos beslut 2026-10-28). `.ugrep` är `ugrep`s inställningsfil, som kan sätta tillägg som kör andra program, och vakten ser den inte. I dag läser Claude Codes `grep` ingen sådan fil av sig själv, men det kan ändras när Claude Code uppdateras. Agenten får därför inte skapa eller ändra en fil eller mapp som heter `.ugrep`, i någon mapp: vakten stoppar kommandon som skulle skriva en (som mål, som källa till `cp -R`, eller via en länk, och oavsett stora och små bokstäver), och de låsta inställningarna förbjuder fil-verktygen att skriva den (`Edit(//**/.ugrep)` och `Edit(~/.ugrep)`). `grep`-tillägg som pekar ut en egen inställningsfil (`--config`, `---` och `--save-config`) står inte på listan och stoppas.
- **`cd` används inte.** Arbetsmappen finns kvar mellan kommandona, så ett `cd` gäller också alla kommandon efter det, och då kan ett kommando köras i fel mapp utan att det syns (granskning 7 såg det, och granskning 8, N5, rättade skälet här). Allt körs därför från projektmappen, med hela sökvägar till kopior utanför projektet.
- **Ett kommando i taget.** Kommandon kopplas inte ihop: inget `;`, `|` eller `&&`, och utskriften styrs inte om med `>`, `2>&1` eller `2>/dev/null`. Inte heller `echo`, `for`-slingor eller `$(...)`. Varje kommando på listan körs för sig, så att det syns exakt vad som körs (granskning 8, N5).
- **Läsa i kopior.** `ls`, `cat`, `head`, `tail`, `grep`, `diff`, `wc` och `sort` får också läsa kopior, provfiler och utfallsfiler i en tillfällig mapp utanför projektet, till exempel scratchpad-mappen (granskning 8, N5).
- **Provfiler i kopian.** I en kopia utanför projektet får en egen testfil skrivas med fil-verktygen och köras med pytest-kommandot, till exempel för en granskares prov. Det är det enda sättet att köra egen Python (granskning 8, N5).
- **Prov och test** (granskning 17, H3, Hugos beslut 2026-10-28). Prov och test får bara skapa, ändra eller länka filer i scratchpad eller i testets tillfälliga mapp (mappen som pytest ger varje test). Aldrig länkar (hårda eller mjuka) till något utanför de mapparna. Nya test får inte läsa eller röra riktiga systemfiler. Det är en regel i text: vakten kan inte hålla den, eftersom ett test kör egen Python. Den tekniska spärren är sandlådan, som ska vara klar före uppgift 5 (se "Det vakten inte stoppar" nedan). Skälet: i granskning 17 gjorde en provfil hårda länkar till `/etc/zshrc`, och då satte macOS en extra uppgift på filen (H1). De gamla testen som gör mjuka länkar till `/usr/bin/git` i testets tillfälliga mapp körs ändå (Hugos svar 2026-10-28).
- **`sed` används inte**, inte heller för att läsa. Ett stycke av en fil läses med fil-verktyget Read (granskning 8, N5).
- **Testsviten mot en kopia.** Pytest-kommandot får köras mot en kopia utanför projektet (gjord med `git archive`, `tar` och `cp -R`), med kopians sökväg som argument i stället för `scripts/tests`. Kommandot körs från projektmappen, med projektets Python på den nya platsen. `-B` och `-p no:cacheprovider` gör att inget skrivs.
- **Tillägg till pytest som bara ändrar vad som visas** får läggas till i båda pytest-kommandona: `--tb` (hur mycket av ett fel som visas), `-q` och `-qq` (kortare utskrift), `-r` (en sammanfattning av till exempel röda tester), `-k` (bara tester vars namn passar ett mönster) och `-p no:randomly` (testerna i fast ordning). Andra tillägg får inte användas.
- Nya filer i projektet skapas med Claudes fil-verktyg (Write och Edit), inte med skalkommandon (kommandon i terminalen). Ändringar i en kopia utanför projektet, till exempel ett mutationstest, görs också med fil-verktygen.
- **Bara verktygen på listan släpps igenom** (granskning 12, P4, Hugos beslut 2026-10-28). Vakten stoppar alla andra verktyg, också nya verktyg som den inte känner till, och namnen jämförs exakt. Bash prövas mot kommandona ovan, och de andra verktygen på listan kör inga kommandon. Andra verktyg som kör kommandon, till exempel terminalverktyget i appen, PowerShell, Monitor, fjärrkommandon via kopplingar och verktyg som startar en server eller bygger en app, är alltså stoppade. Listan valdes av Hugo i chatten 2026-10-28.
- **Tillåtna verktyg**: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `AskUserQuestion`, `WebFetch`, `ToolSearch`, `Skill`, `Agent`, `mcp__ccd_turn__update_plan`, `mcp__ccd_turn__wrap_up`
- **Fil-verktygen och förbuden** (granskning 17, H6, Hugos beslut 2026-10-28). Vakten prövar också sökvägen för verktygen som skriver eller ändrar filer (`Write` och `Edit`, och `MultiEdit` och `NotebookEdit` om de skulle stå på listan) mot förbuden för fil-verktygen i de låsta inställningarna (`Edit(...)` i `sparr/managed-settings.json`), utan hänsyn till stora och små bokstäver. Macen skiljer inte på dem, så `.GIT/hooks` är samma mapp som `.git/hooks`. Sökvägen prövas som den står, med `~` som hemmappen, efter `../`, dit länkarna leder, och med macOS andra namn för samma mapp (`/private/etc` för `/etc`, och `/System/Volumes/Data` för hela datavolymen). **En sökväg vars första del direkt under roten börjar med punkt stoppas alltid** (granskning 18, I1, Hugos beslut 2026-10-28), till exempel `/.vol`, `/.nofollow` och `/.resolve`, oavsett stora och små bokstäver och extra snedstreck (`//.vol`), före och efter att sökvägen har räknats om, både för fil-verktygen och för sökvägar i kommandon. Sådana namn leder till samma fil som en vanlig sökväg utan att synas som länkar. Samma förbud gäller mål för `mkdir`, `cp -R`, `tar` och `git archive` och källor till `cp -R`. Förbuden står också i vakten, och ett test kontrollerar att de är samma som i inställningarna. Där vakten stoppar jämförs sökvägar utan hänsyn till stora och små bokstäver, och där den släpper igenom (till exempel att en sökväg ligger i projektet) jämförs de exakt. Om Claude Codes egna förbud gör samma sak är inte bekräftat. Det prövas i spärrtestet efter installationen.
- **PATH-regeln** (Hugos beslut 2026-10-28, beslut 1). `PATH` är listan över mappar där skalet letar efter ett program. Vakten släpper bara igenom ett kommando om programmet det pekar på ligger i en mapp som ägs av systemet (root) och som varken gruppen eller andra kan skriva i, och samma krav gäller alla mappar ovanför. Samma krav gäller filen själv och sökvägen dit länkarna leder (Hugos beslut 2026-10-28 om vakten, beslut 3), och mappen där varje länk i kedjan däremellan ligger (granskning 13, P2, Hugos beslut 2026-10-28). Länkfilen själv prövas inte: en länk kan inte ändras, bara bytas ut, och det kräver skrivrätt i mappen där den ligger (granskning 14, R4, Hugos beslut 2026-10-28). Samma krav gäller också **varje mapp i `PATH` före programmet**, och en sådan mapp som inte finns stoppar också (beslut 2). Programmet letas upp som skalet gör: ett namn med `/` som det står (i förhållande till projektmappen om det inte börjar med `/`), annars första körbara filen med namnet i `PATH` från vaktens miljö. Kan vakten inte säkert avgöra vilken fil som körs stoppas kommandot: när `PATH` saknas, när en tom eller relativ mapp står före träffen, och när programmet inte finns. Kommandon som ändrar `PATH` stoppas: `PATH=...` (och zsh:s `path=...`) först i kommandot, och `export`, `env`, `typeset`, `declare`, `readonly`, `local` och `unset` med `PATH`. **Följd för testsviten:** projektets Python ligger i `/Library/Application Support/ClaudeCode/vera/venv`, som Hugo skapar med sitt lösenord (beslut 1, INSTALLERA.md steg 9). **Följd för Hugos dator:** nvm-mappen, som Hugo äger, står först i `PATH`, och `/System/Cryptexes/App/usr/bin` leder till en mapp med rättigheterna 777. Hugo flyttar båda sist i `PATH` med två rader i `~/.zshrc` innan vakten installeras, på sin och Caspers dator (INSTALLERA.md steg 4). Vakten har inget undantag för dem (Hugos svar 2026-10-28, punkt 1). Annars stoppas alla kommandon.
- **Projektmappen.** Allt körs i mappen där sessionen startade. En session som startar i hemmappen eller ovanför den får inte köra några kommandon.
- **Citattecken** (Hugos beslut 2026-10-28). Tecken som skalet byter ut mot något annat får bara stå inom citattecken: `*`, `?`, `[`, `{`, `(`, `)`, `~`, `^`, `#`, och `=` först i ett ord. Till exempel `grep -rn --include='*.py' x scripts` och `git show 'HEAD~1:SPEC.md'`. Osynliga och styrande tecken stoppas, också tabb och hårt mellanslag.
- **Tillägg** (Hugos beslut 2026-10-28 om `mkdir -p`):
  - `mkdir` bara med `-p` och `-v`.
  - `cp` bara med `-R`, `-p` och `-v`.
  - `tar` bara med `-c`, `-x`, `-t`, `-f`, `-C`, `-v`, `-z` och `--exclude`, skrivna med bindestreck. `tar -x` måste ha `-C` med en tillfällig mapp, och `tar -c` skriver arkivet bara i en tillfällig mapp.
  - `git archive` bara med `--format`, `--prefix`, `-o`/`--output` och `-v`.
- **git:**
  - Inga tillägg före underkommandot, till exempel `git -C` och `git -c`.
  - Inga tillägg som skriver filer, kör andra program, läser filer utanför git eller öppnar ett fönster. Det gäller bland annat `--output`, `-c`, `--exec-path`, `--ext-diff`, `--textconv`, `--no-index` och `-O`, och för `add` och `commit` också `-p`, `-i`, `-e` och `--template`. Förkortningar stoppas också, till exempel `--out`.
  - `git commit -F` får bara läsa en fil i projektet eller i den tillfälliga mappen. Ett meddelande med `<`, `>` eller flera stycken skrivs med fil-verktygen i den tillfälliga mappen och tas med `-F` (Hugos beslut 2026-10-28).
- **Läsande kommandon** får bara ha sökvägar i projektet och i den tillfälliga mappen, också inne i tillägg. Ett sökmönster till `grep` prövas som en sökväg, så ett mönster som börjar med `/` stoppas (Hugos beslut 2026-10-28). `sort -o`, `--output`, `--compress-program` och `-T` stoppas, och för `grep` gäller listan ovan.
- **pytest:** målet är `scripts/tests`, eller en kopia eller en testfil i en kopia i den tillfälliga mappen. `-p` får bara användas som `-p no:randomly`.
- **Den tillfälliga mappen** är den som Claude Code anger för sessionen (scratchpad-mappen). En mapp i projektet, eller en mapp som rymmer hemmappen, räknas inte.
- **Det vakten inte stoppar:** en egen testfil i en kopia, fil-verktygen utanför förbuden (ovan) och andra datorer. Det stoppas först av sandlådan och spärrsteget, före uppgift 5, eller före första hela körningen på riktiga underlag om den kommer först. **Det PATH-regeln inte ser:** vakten prövar `PATH` i sin egen miljö, som Claude Code ger den. Kontrollerat på Hugos dator 2026-10-28: Bash-verktygets `PATH` och den `PATH` som Claude Code själv startades med (och ger vakten) är exakt lika (PROGRESS.md). Om de ändå skiljer sig, eller skalet har alias eller funktioner, kan skalet köra en annan fil än den vakten prövade. Beslut 2 gör det svårare: före programmet får bara stå mappar som root äger. `/usr/bin/git` är ett litet program från Apple som startar git i utvecklarverktygen, och vakten prövar bara det första programmet. **För `grep` kör skalet ett annat program än det vakten prövar** (granskning 15, S5, Hugos beslut 2026-10-28). I agentens skal är `grep` en funktion som Claude Code själv lägger in, och den kör Claude Codes inbyggda `ugrep`, som Hugo äger. Vakten prövar `/usr/bin/grep`. Skyddet för Claude Codes program är förbuden i de låsta inställningarna (`~/Library/Application Support/Claude/**`, `~/.local/bin/claude` och `~/.local/share/claude/**`), inte att root äger det, och att `grep` bara får ha tillägg som söker (ovan). Samma sak gällde `find` (Claude Codes `bfs`), som därför är borttaget. Att skalet inte har andra funktioner än Claude Codes egna kontrolleras före installationen (INSTALLERA.md, steg 4 h).

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

Namn och datum för de tre första besluten är hämtade ur statusraden överst, som säger när SPEC godkändes och ändrades.

**Avgjort (i SPEC utkast 1, godkänd av Hugo 2026-10-24):** godkännande är obligatoriskt i båda lägena. I automatiskt läge kräver det ett sista godkännande av veckans utkast innan bokföringen skickas vidare. Ett läge utan något godkännande finns inte i version 1.

**Avgjort (efter Hugos OK 2026-10-25):** kontrollen K5 (momssatsen finns för datumet) kräver en momsfil i företagets konfiguration (`foretag/<namn>/`), med momssatser per varugrupp och datum. Vad som står i filen hänger på Ö3.

**Avgjort (efter Hugos OK 2026-10-25):** varje underlag har minst en momsrad. Ett momsfritt underlag har en rad med sats 0 och moms 0.

**Avgjort (Hugos beslut 2026-10-27, granskning 8, N3):** `matcha_period` får regelboken, och en bankrad mot en ägare eller närstående kräver alltid underlag (K3), även när en regel i `matchning.json` annars skulle undanta den. Byggt i commit ea51c97 (Ö13).

**Avgjort (Hugos beslut 2026-10-27, granskning 8, N4):** ett fristående accenttecken efter en bokstav, och en accent efter ett blanksteg, jämförs som bokstaven med accent, så att "A¨" jämförs som "Ä". Det är den säkra riktningen: fler ägare känns igen, och fler möjliga dubbletter blir ärenden. Byggt i commit ca2df6a och låst med testet `test_n4_fristaende_accent_jamfors_som_bokstaven_med_accent`.

**Avgjort (Hugos beslut 2026-10-27): en saknad, tom eller oläsbar lista över ägare och närstående stoppar agenten** (regelbokens `agare_och_narstaende`, K7). **Byggt i commit dd0e1cf** (granskning 9): `las_regelbok` stoppas, och utan en Regelbok kan varken matchningen eller konteringsförslagen köras. När felet ligger i själva listan (den saknas, är tom, är inte en lista, eller en motpart i den är fel) säger felet att hela körningen stoppas. Ett dolt tecken eller trasig JSON någonstans i filen, och ett annat fel i filen som hittas före listan, stoppar också regelboken och därmed hela körningen, men med det felets egen text (granskning 10, P2: Hugos beslut 2026-10-28 är att bara den här texten rättas, inte koden).

**Avgjort (Hugos beslut 2026-10-28, granskning 10, P1): en motpart i listan över ägare och närstående som inte har någon bokstav eller siffra räknas som tom och stoppar hela körningen.** Ett sådant namn, till exempel `-`, `.`, `_ .` eller ett tankstreck, blir tomt när det delas i ord som i uppslaget för bankrader, och kan aldrig kännas igen i en bankrad. Det gäller alla företag, inte bara testföretaget. **Byggt i commit 16000a8**: felet säger vilken fil, vilken motpart och vilket värde, varför det är fel och hur det rättas, och sedan att hela körningen stoppas.

**Avgjort (Hugos beslut 2026-10-27): en bankrad mot en ägare eller närstående märks "kräver mänsklig bedömning" redan i matchningen** (`matcha_period`), och får dessutom nivå D i nivåsteget (DESIGN-regelbok.md, uppgift 6). **Märkningen är byggd i commit dd0e1cf** (granskning 9): varje bankrad i matchningens resultat har `kraver_mansklig_bedomning`, som är sann för en sådan rad. Raden blir aldrig en vanlig matchning: med exakt ett underlag blir den ett ärende "kräver mänsklig bedömning" (kontroll K7). Den kräver fortfarande alltid underlag (K3, ea51c97). **Nivån D är inte byggd**: nivåerna sätts i nivåsteget (Ö13).

**Avgjort (Hugos beslut 2026-10-29, granskning 11, Q2): accenter spelar ingen roll i ägaruppslaget.** En ägare eller närstående känns igen i en bankrad även när banken skriver namnet utan accenter, och omvänt: "Åsa Öberg" i listan pekas ut i "UTTAG ASA OBERG", och "Asa Oberg" i "UTTAG ÅSA ÖBERG". Det gäller också accenter som är egna tecken (en bokstav och sedan ett separat accenttecken). Det gäller följande ägarkontroller: regelbokens uppslag för bankrader, som matchningen och konteringsförslagen använder, och kontrollen att ingen regel i `matchning.json` nämner en ägare eller närstående. Den gemensamma jämförelsen (`normalisera_for_jamforelse`), dublettkontrollen K4 och matchningen mot motparter bryr sig fortfarande om accenter. **Andra stavningar**, till exempel "AA" för "Å" eller "OE" för "Ö", känns inte igen. De tas när riktiga bankfiler finns (Ö5). **Byggt i commit 3e3c18c.**

**Avgjort (Hugos beslut 2026-10-29, granskning 11, Q2b): accenter spelar ingen roll i någon ägarkontroll.** Utöver uppslaget för bankrader och kontrollen av `matchning.json` (Q2) gäller det också uppslaget för en motpart i ett underlag (`Regelbok.ar_agare_eller_narstaende`) och kontrollen att en regel för en ägares eller närståendes underlag har nivå D: en regel för "Asa Oberg" med en annan nivå än D stoppar regelboken när "Åsa Öberg" står i listan, och omvänt. Samma jämförelse som förut, bara utan accenter på båda sidor. Två saker som inte är ägarkontroller bryr sig fortfarande om accenter: dublettkontrollen i listan över ägare och närstående ("Åsa Öberg" och "Asa Oberg" får båda stå där) och kontrollen av tvetydiga regler. `normalisera_for_jamforelse`, `sokform_for_namn` och `star_som_hela_ord` är oförändrade. **Byggt i commit 1dcf769.**

**Avgjort (Hugos beslut i chatten 2026-10-27): listan över ägare och närstående ligger kvar i `foretag/<namn>/regelbok.json`, där agenten kan skriva, tills spärrsteget.** Avsnitt 7 säger att en spärr inte ska läsa från en mapp som agenten kan skriva i, men inte var den skyddade mappen ska ligga. Den platsen, och testet att listan ligger utanför alla mappar agenten får skriva i, byggs i spärrsteget (granskning 9).

**Avgjort (Hugos beslut 2026-10-29, B2): ärenden från K5 och K8 får nivå D direkt, före nivåsteget.** De skapas med märkningen "kräver mänsklig bedömning" (samma märkning som för ägarens bankrader, granskning 10, P4) och nivå D. Nivåsteget i uppgift 6 får aldrig sänka en sådan nivå, bara höja. `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4".

**Antaget för testföretaget (Hugos beslut 2026-10-29), bokföringsfrågorna D1, D2, D4, D13 och D14** (DESIGN-regelbok.md avsnitt 8). Valen är påhittade, gäller bara Syntet Testbutik AB och märks "antaget" i testföretagets konfiguration. För en riktig kund är de kundens, och frågorna är fortfarande öppna för riktiga företag. Strider ett val mot DESIGN-regelbok.md ska byggsessionen stanna och fråga. Källa: `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4" (B3, tillägget om D13 och D14, och "D13 och D14 beslutade").

- **D1, antaget för testföretaget (Hugos beslut 2026-10-29):** faktureringsmetoden.
- **D2, antaget för testföretaget (Hugos beslut 2026-10-29):** de BAS-konton som redan finns i kontoplanen.
- **D4, antaget för testföretaget (Hugos beslut 2026-10-29):** momsen i öre exakt som på underlaget, ingen avrundning per verifikation.
- **D14, antaget för testföretaget (Hugos beslut 2026-10-29):** leverantörsfaktura på fakturadatum och betalningen på bankens datum, kvitto på kvittodatum, bankavgift på bankens datum. **Förtydligande (Hugos beslut i chatten 2026-10-29):** "bankens datum" betyder transaktionsdagen, inte bankens bokföringsdag.
- **D13, antaget för testföretaget (Hugos beslut i chatten 2026-10-29):** bankrader som regelboken pekar ut som rena bankavgifter konteras utan moms, med bankraden som underlag tills Ö11. Allt annat från banken (terminalhyra, bankfack med mera) kräver faktura. Saknas den blir det ett ärende med nivå D, inget förslag.

| # | Fråga | Ägare |
|---|---|---|
| Ö1 | **Produktionsarkitektur.** Version 1 körs lokalt som referensprodukt. Hur och var kundens data ska lagras säkert när Vera blir en tjänst är inte bestämt | Hugo |
| Ö2 | Vilka bokföringsprogram får direktkoppling först (Fortnox, Bokio, Spiris)? Version 1 använder SIE-export | Hugo |
| Ö3 | Momssatser och särregler per bransch (restaurang, bygg, begagnade varor) ska verifieras mot Skatteverket eller en redovisningskonsult innan de läggs i någon regelbok. Hit hör också **momsavrundning**: testdatan visar att kassan avrundar momsen till närmaste öre, men inte vad som gäller när momsen hamnar på exakt ett halvt öre. Och **Z-nummer som börjar om**, till exempel vid årsskifte: kanske tillåtet, och ska kontrolleras med kassaleverantören eller en redovisningskonsult. Tills dess stoppas en Z-serie som börjar om (K12) | Konsult |
| Ö4 | Får rutinposter i kassa bokföras samlat per vecka? | Konsult |
| Ö5 | Vilka kassasystem och bankformat ska stödjas först. Bankformatet, kassaformatet och att bankfilens rader numreras 1, 2, 3 … är **antaget** för testföretaget och ska jämföras mot riktiga exportfiler innan de används på riktiga underlag. Hit hör också hur banken skriver ägarens namn: ägaruppslaget bortser från accenter (Q2, Hugos beslut 2026-10-29), men andra stavningar, till exempel "AA" för "Å" eller "OE" för "Ö", tas när riktiga bankfiler finns (Ö13). Samma sak gäller bokstäver som inte känns igen utan accent, eftersom Unicode inte delar upp dem i en bokstav och en accent, till exempel ø, æ, ł och đ: "Soren Lokke" i listan pekas inte ut i "UTTAG SØREN LØKKE" (granskning 21, L3) | Hugo |
| Ö7 | Hur får Vera tillgång till bank, mejl och bokföringsprogram i automatiskt läge, och hur säkras det? | Hugo |
| Ö8 | **Kreditnotor:** en egen dokumenttyp där alla belopp är negativa. Ingen annan typ får vara negativ | Hugo |
| Ö9 | K4 (dubbletter) ska också jämföra mot underlag från tidigare perioder (arkivet), inte bara inom perioden | Hugo |
| Ö10 | K17: att känna igen instruktionsliknande text i underlag och flagga den byggs i rapportsteget | Hugo |
| Ö11 | **Bankens avgiftsspecifikation** ska bli ett riktigt underlag med en egen dokumenttyp, så att bankens avgifter matchas som andra utgifter. Tills dess slipper avgifterna underlag genom en regel i `matchning.json`, med en högsta summa per bankrad | Hugo |
| Ö12 | **Godkända kontrollsummor.** Förslagets kontrollsummor för regelboken, kontoplanen, momsfilen och matchningsformatet jämförs i dag bara med filerna som lästes in i samma körning, inte med ett godkänt värde. En ändrad fil syns därför bara om någon jämför summan med en summa som är godkänd. Den godkända summan ska sparas i en mapp som agenten inte kan skriva i, och jämförelsen göras där. Byggs i spärrsteget (spärrtestet "ändrad regelbok") | Hugo |
| Ö13 | **Ägarens bankrader** (K7, granskning 7 M7). En bankrad där en ägare eller närstående (regelbokens `agare_och_narstaende`) står i beskrivningen eller referensen ska aldrig få lägre nivå än D, inte heller om en regel i `matchning.json` undantar raden från underlag. Uppslaget som pekar ut raderna finns (`Regelbok.ar_bankrad_mot_agare_eller_narstaende`), men nivåerna sätts först i nivåsteget (DESIGN-regelbok.md, uppgift 6). Tills dess är det inte byggt. Uppslaget kräver att namnet står som hela ord. Orden delas vid allt som inte är en bokstav, en siffra eller ett kombinerande tecken (granskning 8, N3, Hugos uppdrag 2026-10-27), så "UTTAG AGARE-1", "UTTAG AGARE-1/LAN", "TILL:AGARE-1" och "UTTAG AGARE 1" pekas ut, men inte "UTTAGAGARE-1" eller "UTTAG AGARE-10". **Accenter spelar ingen roll i uppslaget** (granskning 11, Q2, Hugos beslut 2026-10-29, byggt i commit 3e3c18c): "Åsa Öberg" pekas ut i "UTTAG ASA OBERG" och "Asa Oberg" i "UTTAG ÅSA ÖBERG", och samma sak gäller kontrollen av reglerna i `matchning.json` nedan. **Accenter spelar heller ingen roll i de andra ägarkontrollerna** (Q2b, Hugos beslut 2026-10-29, byggt i commit 1dcf769): `Regelbok.ar_agare_eller_narstaende` och kontrollen att en regel för ägarens underlag har nivå D. Andra stavningar, till exempel "AA" för "Å" eller "OE" för "Ö", känns inte igen förrän riktiga bankfiler finns (Ö5). Om det ska räcka att namnet står någonstans i texten avgörs i uppgift 6. **En regel i `matchning.json` undantar aldrig en sådan rad** (granskning 8, N3, Hugos uppdrag 2026-10-27): regelboken ger ingen regel i matchningsformatet för raden (`Regelbok.matchningsregel_for_bankrad`), så ett konteringsförslag för den med en regel för bankrader stoppas, och en regel i matchningsformatet vars text nämner en ägare eller närstående stoppar regelboken. **Matchningen** (`matcha_period`) får regelboken och använder dess uppslag, enligt Hugos beslut 2026-10-27: en sådan rad hamnar aldrig bland raderna som inte kräver underlag och blir aldrig "över gräns", utan kräver underlag som andra rader (K3). Den väntar på underlag eller blir ett ärende "saknat underlag", "tvetydig" eller, med exakt ett underlag, "kräver mänsklig bedömning" (K7), och märks alltid "kräver mänsklig bedömning" (Hugos beslut 2026-10-27, byggt i commit dd0e1cf). Kvar är nivån D, som sätts i nivåsteget (Hugos beslut 2026-10-27, se ovan) | Hugo |
