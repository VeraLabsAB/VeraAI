# foretag/

All företagsspecifik konfiguration ligger här, med en mapp per företag: `foretag/<namn>/`.

Hit hör till exempel regelbok, kontoplan, momssatser, beloppsgränser, kassasystem, bankformat och vem som får godkänna.

Sådant får aldrig skrivas i `scripts/`. Kärnan i `scripts/` är gemensam för alla företag och läser konfigurationen härifrån.

## bankformat.json

Beskriver hur företagets bankfil (CSV) ser ut, så att kärnan kan läsa den utan att känna till banken. Läses och kontrolleras av `ladda_bankformat` i `scripts/las_bank.py`.

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `kolumner` | Ja | Vad kolumnerna heter i bankfilens rubrikrad. Exakt dessa sju nycklar: `radnr`, `bokforingsdag`, `transaktionsdag`, `referens`, `beskrivning`, `belopp`, `saldo` (saldot efter transaktionen). Inga tomma eller dubbla namn, och inga styrtecken (till exempel tabb) eller osynliga tecken (till exempel U+200B, osynligt mellanslag) |
| `avgransare` | Ja | Lista med tecknen som får skilja kolumnerna åt, till exempel `[",", ";"]`. Bara komma, semikolon, tabb (`"\t"`) och lodstreck (`"\|"`) är tillåtna. Det som står på rubrikraden används |
| `anteckning` | Nej | Fri text för människor, till exempel vilken bank formatet gäller. Används inte av koden |

Saknas en nyckel, finns en okänd nyckel, är något namn tomt eller dubbelt, eller är en avgränsare inte tillåten, stoppas inläsningen med ett tydligt fel.

Formatet i `syntet-testbutik/` är **antaget** och inte jämfört med en riktig exportfil från banken (Ö5).

## kassaformat.json

Beskriver hur företagets Z-rapporter från kassan (en CSV-fil per rapport) ser ut, så att kärnan kan läsa dem utan att känna till kassasystemet. Läses och kontrolleras av `ladda_kassaformat` i `scripts/las_kassa.py`.

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `filnamn` | Ja | Filnamnsmönstret, med `ÅÅÅÅ-MM-DD` exakt en gång där datumet står, till exempel `"kassa_ÅÅÅÅ-MM-DD.csv"`. Utan mapp och utan punkt först |
| `kolumner` | Ja | Vad kolumnerna heter i Z-filens rubrikrad. Exakt dessa sex nycklar: `rapportdatum`, `znummer` (Z-rapportens löpnummer), `kassaregister`, `postnamn` (vilken post raden gäller), `sats` (momssatsen i procent) och `belopp`. Samma regler för namnen som i bankformatet |
| `avgransare` | Ja | Lista med tecknen som får skilja kolumnerna åt. Samma tillåtna tecken som i bankformatet |
| `poster` | Ja | Vad posterna heter i Z-filen. Exakt dessa fyra nycklar: `forsaljning_per_sats` (försäljning inklusive moms, en rad per momssats), `moms_per_sats` (momsen, en rad per momssats), `betalsatt` (en lista med ett postnamn per betalsätt) och `totalsumma`. Varje postnamn får bara användas en gång |
| `momsavrundning` | Ja | Hur kassan avrundar momsen. Kärnan känner bara till `"narmaste_ore"`: försäljningen × sats / (100 + sats), avrundad till närmaste öre |
| `kassaregister` | Ja | Lista med företagets kassaregister (id för varje kassa som skriver Z-rapporter), till exempel `["TB-KASSA-1"]`. Minst ett. Samma regler för namnen som för kolumnnamnen. Se avsnittet om kassalistan nedan |
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

Saknas en nyckel, finns en okänd nyckel, är något namn tomt eller dubbelt, eller är en avgränsare eller momsavrundning inte tillåten, stoppas inläsningen med ett tydligt fel.

### Kassalistan (`kassaregister`)

Listan säger vilka kassor företaget har. Den finns för att samma Z-rapport inte ska kunna räknas två gånger bara för att kassans namn är skrivet lite olika i två filer (granskning 3, H2).

- En Z-fil från en kassa som inte står i listan stoppas. Har företaget fått en ny kassa ska den läggas till här, av en människa.
- Namnen jämförs efter **normalisering**, det vill säga de skrivs om till en fast form innan de jämförs: Unicode-normalisering (NFKC, så att till exempel fullbreddstecken och två sätt att skriva "Ö" blir samma), blanksteg och osynliga tecken (till exempel U+200B, osynligt mellanslag) tas bort, och stora och små bokstäver räknas som samma. `TB-KASSA-1`, `tb-kassa-1` och `TB-KASSA-1` med ett osynligt mellanslag är alltså samma kassa. `TB-KASSA-1 X` är en annan kassa och stoppas.
- Två namn i listan som blir samma efter normalisering, till exempel `"K-1"` och `"k-1"`, stoppas med ett tydligt fel.
- Raderna som läses in får kassans namn som det står i listan, inte som det står i filen. Två filer med samma datum, Z-nummer och kassa efter normalisering stoppas därför som dubblett av kontrollen av Z-serien.

Kassalistan ligger i samma fil som resten av kassaformatet och är lika oskyddad (granskning 3, H11). Den hör till spärrsteget.

Formatet i `syntet-testbutik/` är **antaget** och inte jämfört med en riktig exportfil från något kassasystem (Ö5). Momsavrundningen är utläst ur testdatan och inte kontrollerad mot Skatteverket eller en redovisningskonsult.

## matchning.json

Beskriver hur företagets bankrader **matchas** (paras ihop) med underlagen, till exempel en betalning med fakturan den betalar. Läses och kontrolleras av `ladda_matchningsformat` i `scripts/las_matchningsformat.py`, och används av `matcha_period` i `scripts/matcha_bank.py` (kontroll K3, varje förslag har underlag).

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `kraver_inte_underlag` | Ja | Lista med regler för bankrader som inte ska ha ett underlag, till exempel kortinlösarens insättning av kortförsäljningen. Se reglerna nedan. Listan får vara tom |
| `tidsfonster_dagar` | Ja | För varje underlagstyp (`leverantorsfaktura` och `kvitto`): hur många dagar efter underlagets datum betalningen får ligga på banken. Heltal från 0 till och med 366 |
| `saknat_underlag_efter_dagar` | Ja | Hur många dagar efter bankradens transaktionsdag en bankrad utan underlag får vänta innan den blir ett ärende. Heltal från 0 till och med 366 |
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

### Reglerna i `kraver_inte_underlag`

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `namn` | Ja | Regelns namn. Visas i resultatet och i ärenden. Varje namn får bara finnas en gång |
| `riktning` | Ja | `"in"` (pengar in, positivt belopp) eller `"ut"` (pengar ut, negativt belopp) |
| `referens_borjar_med` | Minst en av de två | Text som bankradens referens ska börja med |
| `beskrivning_borjar_med` | Minst en av de två | Text som bankradens beskrivning ska börja med |
| `hogst_belopp_ore` | Ja för `"ut"`, får inte finnas för `"in"` | Den högsta summan per bankrad, i **öre** (100 öre är 1 krona), som regeln gäller för. Beloppet räknas som positivt, så gränsen 25000 gäller en utgående rad på −250,00 kr. Ett heltal större än 0, med högst 15 siffror. Se nedan |
| `anteckning` | Nej | Fri text för människor, till exempel varför raden inte kräver underlag |

Finns båda textmönstren ska båda stämma. Texten jämförs exakt, med stora och små bokstäver och utan att osynliga tecken tas bort, så att en rad med en annan stavning aldrig undantas av misstag. Två regler med samma riktning som kan passa samma bankrad stoppas, så att varje bankrad hör till högst en regel.

### Gränsen för pengar ut (`hogst_belopp_ore`)

En regel för pengar ut får aldrig gälla obegränsat (Hugos beslut 2026-10-25). Annars kunde en stor betalning slippa underlag bara för att texten börjar som till exempel en bankavgift.

- En utgående rad som passar regeln och ligger **på eller under** gränsen kräver inget underlag.
- En utgående rad som passar regeln men ligger **över** gränsen blir direkt ett ärende av typen `"över gräns"` (K3), med regelns namn och gränsen. Den matchas inte mot underlag och räknas inte som en rad utan krav på underlag. En människa avgör vad den är.
- Saknas gränsen i en regel för pengar ut, eller är den inte ett heltal större än 0 med högst 15 siffror, stoppas formatet.
- En regel för pengar in får inte ha en gräns. Den skulle inte användas, och en gräns som inte gör något ska inte se ut som ett skydd. Om insättningar också ska ha en gräns är inte bestämt.

För Syntet Testbutik har regeln `bankavgift` gränsen 25000 öre (250 kr), som Hugo har bestämt. Avgifterna i testdatan är 125 och 199 kr.

Saknas en nyckel, finns en okänd nyckel eller är ett värde fel, stoppas inläsningen med ett tydligt fel (`MatchningsformatFel`).

Formatet i `syntet-testbutik/` är **antaget** utifrån testdatan och inte jämfört med en riktig bankfil (Ö5). Det ligger där agenten kan skriva, som bank- och kassaformatet. Flytten till en skyddad mapp hör till spärrsteget (SPEC 7).

## Gemensamt för kontoplan.json och momssatser.json

Formaten är Hugos beslut D17 (DESIGN-regelbok.md avsnitt 2 och 8). Båda filerna läses av en enda funktion var, som alltid kör alla kontroller, och resultatet går inte att ändra efteråt. **Hela filen stoppas vid minsta fel**:

- en okänd eller saknad nyckel,
- fel typ, till exempel ett decimaltal, en text eller `true` där det ska vara ett heltal, eller ett tal där det ska vara text,
- ett tomt värde (en tom text, en tom lista eller ett tomt objekt), eller en text med blanksteg först eller sist,
- ett **dolt tecken** var som helst i filen, även i nycklar och anteckningar: styrtecken (till exempel tabb och radbrytning), osynliga tecken (till exempel U+200B, osynligt mellanslag), riktningstecken, ovanliga blanksteg (till exempel hårt mellanslag) och tecken som ser tomma ut. Det gäller också tecken som skrivits som kod i JSON, till exempel `"​"`. Vanligt mellanslag är tillåtet,
- en fil som inte är UTF-8, inte är giltig JSON eller har en nyckel två gånger.

Ett **uppslag** (till exempel "vilken sats har livsmedel den 10 februari?") görs alltid för ett datum. Finns inget svar för datumet stoppas uppslaget med ett fel. Vera gissar aldrig ett konto eller en sats.

## kontoplan.json

Företagets konton, och vilka konton som har en **roll** som kärnan behöver känna till. Rollerna behövs eftersom kärnan aldrig får ha ett kontonummer i sin kod (SPEC 2). Läses och kontrolleras av `las_kontoplan` i `scripts/las_kontoplan.py`.

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `status` | Ja | Vad filen är, till exempel `"SYNTETISK"`. Visas för människor |
| `konton` | Ja | Lista med minst ett konto, se nedan |
| `roller` | Ja | Exakt rollerna `bank`, `leverantorsskulder`, `ingaende_moms` och `utgaende_moms_per_sats`. De tre första pekar på ett konto. `utgaende_moms_per_sats` är ett objekt med minst en momssats och kontot för utgående moms med den satsen, till exempel `{"25": "2611"}`. Satsen skrivs som ett heltal i text, från `"0"` till `"100"`, utan nollor först |
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

Ett konto:

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `nummer` | Ja | Kontonumret som **text**, bara siffrorna 0–9 (högst 15), till exempel `"1940"`. Text och inte ett tal, så att ett konto som börjar med noll behåller nollan |
| `namn` | Ja | Kontots namn |
| `fran` | Nej | Första dagen kontot får användas, `ÅÅÅÅ-MM-DD`. Saknas den gäller kontot från början |
| `till` | Nej | Sista dagen kontot får användas, `ÅÅÅÅ-MM-DD`, eller `null`. Saknas den gäller kontot tills vidare |

Dessutom stoppas filen om samma kontonummer står två gånger, om ett konto slutar före sitt första datum, eller om en roll pekar på ett konto som inte finns i `konton`. Ett uppslag på ett konto som inte finns, eller som inte gäller på datumet, stoppas.

`fran` och `till` för konton finns inte i exemplet i DESIGN-regelbok.md. De är valfria och lades till för att konton ska gälla per datum, som för momssatserna. Testbutikens fil använder dem inte.

## momssatser.json

Vilken momssats varje **varugrupp** (en grupp varor med samma sats, till exempel livsmedel) har, och från och till vilket datum. Läses och kontrolleras av `las_momssatser` i `scripts/las_momssatser.py`. Behövs för kontroll K5 (SPEC 11).

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `status` | Ja | Vad filen är, till exempel `"SYNTETISK"`. Visas för människor |
| `varugrupper` | Ja | Objekt med minst en varugrupp. Namnet får bara ha små bokstäverna a–z, siffror och understreck, och ska börja med en bokstav (så att två namn som ser likadana ut aldrig är olika). Varje varugrupp har en lista med minst en period, se nedan |
| `moms_tolerans_ore_per_rad` | Ja | Hur många öre momsen på en momsrad får skilja från sats × belopp (K5). Heltal från 0 |
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

En period:

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `fran` | Ja | Första dagen satsen gäller, `ÅÅÅÅ-MM-DD` |
| `till` | Ja | Sista dagen satsen gäller, `ÅÅÅÅ-MM-DD`, eller `null` om den gäller tills vidare. Bara den sista perioden får ha `null` |
| `sats` | Ja | Momssatsen i procent, ett **heltal** från 0 till och med 100. Aldrig ett decimaltal |
| `kalla` | Ja | Varifrån satsen kommer. För en riktig kund ska den peka på ett beslut av en redovisningskonsult |

Perioderna står i tidsordning och ska följa direkt på varandra: nästa period börjar dagen efter att den förra slutar. **Överlapp** (två satser samma dag) och **glapp** (en dag utan sats) stoppar filen. När en sats ändras läggs en ny period till och den gamla får ett slutdatum, så att ett gammalt underlag kontrolleras mot satsen som gällde då.

**Ingen sats i filen är en skatteregel.** Satserna i `syntet-testbutik/` är SYNTETISKA, utlästa ur `testdata/README.md`, och inte verifierade mot Skatteverket eller en redovisningskonsult (Ö3). Kontonumren i `syntet-testbutik/kontoplan.json` liknar BAS men är SYNTETISKA och inte verifierade (D2). Båda filerna är exakt exemplen i DESIGN-regelbok.md avsnitt 2, och ett test kontrollerar det.

Båda filerna ligger där agenten kan skriva, som de andra formatfilerna. Flytten till en skyddad mapp hör till spärrsteget (SPEC 7).
