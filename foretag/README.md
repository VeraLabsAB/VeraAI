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

## regelbok.json

Företagets **regelbok**: för varje känd motpart, kassa eller sorts bankrad, vilka konton det ska konteras på och på vilken nivå (A–D, SPEC 5). Formatet är Hugos beslut D17 (DESIGN-regelbok.md avsnitt 1). Läses och kontrolleras av `las_regelbok` i `scripts/las_regelbok.py`, som också tar emot den redan inlästa kontoplanen (`las_kontoplan`), momsfilen (`las_momssatser`) och matchningsformatet (`ladda_matchningsformat`), så att varje konto, varugrupp och regel i matchningen som regelboken nämner kan kontrolleras. Resultatet går inte att ändra efteråt. **Hela filen stoppas vid minsta fel**, på samma sätt som för kontoplanen och momsfilen ovan (okänd eller saknad nyckel, fel typ, tomt värde, dolt tecken var som helst, trasig JSON).

**Agenten får aldrig ändra regelboken** (SPEC 3). En ny motpart blir ett ärende, och svaret blir ett regelförslag som en människa själv lägger in.

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `foretag` | Ja | Företagets namn. Visas för människor och i loggen |
| `version` | Ja | Regelbokens version, ett heltal från 1 |
| `godkand` | Ja | Vem som godkände regelboken och när: `{"av": "...", "datum": "ÅÅÅÅ-MM-DD"}`. Det som skyddar är kontrollsumman, inte det här fältet |
| `granser` | Ja | Företagets gränser i **öre**: `a_hogst_ore` (högsta belopp för nivå A) och `b_hogst_ore` (för nivå B). Heltal större än 0. A-gränsen får inte vara högre än B-gränsen |
| `k9` | Ja | Värdena för K9 (ovanliga belopp): `minst_historik` (heltal från 1), `hogst_procent_av_median` (från 100) och `lagst_procent_av_median` (0–100). `minst_historik` är också hur många gånger en regel ska ha godkänts innan den kan ge nivå A (DESIGN avsnitt 5) |
| `oppettider` | Ja | Företagets stängda dagar, för varningssignalen i K8 (Hugos beslut D21): `stangda_veckodagar` (en lista med `mandag`, `tisdag`, `onsdag`, `torsdag`, `fredag`, `lordag`, `sondag`) och `stangda_datum` (en lista med hela datum, `ÅÅÅÅ-MM-DD`). Det finns ingen återkommande dag utan år (Hugos beslut 2026-10-26), så en helgdag skrivs in för varje år. Varje dag får stå en gång. En lista får vara tom, om företaget inte har sådana stängda dagar. Läses och kontrolleras, men används inte än |
| `agare_och_narstaende` | Nej | Lista med motparter som är **ägare eller närstående** (K7, Hugos beslut 2026-10-26), till exempel `["AGARE-1"]`. Saknas nyckeln är listan tom, och en tom lista godtas. Varje motpart är text och får stå en gång. Motparterna jämförs efter samma normalisering som i K4 (stora och små bokstäver, bindestreck och osynliga tecken räknas inte), så `AGARE-1` och `agare-1` räknas som samma och stoppar filen. Uppslaget `ar_agare_eller_narstaende` säger om en motpart står i listan, och ska användas av nivåsteget |
| `regler` | Ja | Lista med minst en regel, se nedan |
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

En regel:

| Nyckel | Krävs | Innehåll |
|---|---|---|
| `id` | Ja | Regelns fasta id, till exempel `R-LEV-TE`. Står i varje förslag. Två id som blir lika efter normalisering (stora och små bokstäver, bindestreck och osynliga tecken räknas inte) stoppar filen |
| `galler` | Ja | Vad regeln gäller. `kalla` är `underlag`, `z_rapport` eller `bankrad`. För `underlag` krävs också `typ` (`leverantorsfaktura` eller `kvitto`) och `motpart`. För `z_rapport` krävs `kassaregister`. För `bankrad` krävs `matchningsregel`: namnet på en regel i `matchning.json` |
| `kontering` | Ja | Kontona. För `underlag`: ett konto per varugrupp, till exempel `{"livsmedel": "4010"}`. För `z_rapport`: `forsaljning` (ett konto per varugrupp) och `betalsatt` (ett konto per betalsätt, med postnamnet i kassaformatet). För `bankrad`: en eller flera av `motkonto`, `avgift` och `kostnad` |
| `villkor` | Ja | `giltig_fran` (krävs), och valfritt `giltig_till` (eller `null`, tills vidare), `hogst_belopp_ore` (regelns egen gräns i öre) och `avdragsbegransad` (`true` eller `false`, K8) |
| `niva` | Ja | Den lägsta nivån ett förslag med regeln kan få: `A`, `B`, `C` eller `D` |
| `anteckning` | Nej | Fri text för människor |

Dessutom stoppas filen om:

- **två regler kan passa samma sak**: samma källa och samma värden i `galler` (motpart och kassaregister jämförs efter samma normalisering som i K4), och datum som överlappar med minst en dag. Högst en regel får passa,
- ett konto inte finns i kontoplanen, eller inte gäller under hela tiden regeln gäller,
- en varugrupp saknar sats i momsfilen för någon dag regeln gäller,
- en regel för `bankrad` pekar på en regel som inte finns i `matchning.json`,
- en regel för bankrader med **pengar ut** saknar `hogst_belopp_ore`, eller har en högre gräns än regeln i `matchning.json`,
- en regels `hogst_belopp_ore` är högre än företagets `b_hogst_ore`. **En regel kan bara skärpa företagets gränser, aldrig höja dem** (Hugos beslut D20),
- en regel för `bankrad` har nivå `A`. Bankrader utan underlag blir aldrig nivå A (D20),
- en regel för `underlag` vars motpart står i `agare_och_narstaende` (efter normaliseringen) har en annan nivå än `D`. **En regel för ägare och närstående har alltid nivå D** (K7, Hugos beslut 2026-10-26),
- samma motpart står två gånger i `agare_och_narstaende`, eller en motpart där är tom eller inte text.

### Kontrollsumman

`las_regelbok` räknar ut en **kontrollsumma** (SHA-256, ett "fingeravtryck" på 64 tecken) av filens innehåll, byte för byte, och den följer med i resultatet. Den ska senare visas i varje förslag, så att godkännaren ser vilken regelbok som användes, och användas i spärrtestet "ändrad regelbok" (SPEC 7). Samma fil ger alltid samma summa. Minsta ändring, även ett mellanslag eller en radbrytning, ger en annan. Summan räknas på exakt de bytes som sedan tolkas, så filen kan inte bytas mellan summan och kontrollerna.

### Testbutikens regelbok

`syntet-testbutik/regelbok.json` är **SYNTETISK**. Den är exemplet i DESIGN-regelbok.md avsnitt 1 med tre tillägg, alla med redan bestämda värden och godkända av Hugo 2026-10-26 (ett test kontrollerar det):

- `oppettider`, med testbutikens stängda dagar ur `testdata/README.md` (söndagar, 1 januari och 6 januari 2025),
- `hogst_belopp_ore` 25000 (250 kr) i `R-BANK-AVGIFT`. Bankavgiften är pengar ut och måste därför ha en gräns. Värdet är gränsen i `matchning.json` som Hugo bestämde 2026-10-25,
- `agare_och_narstaende` med `AGARE-1`, det syntetiska värdet ur DESIGN-regelbok.md avsnitt 1 och `testforetag/FIKTIVT_FORETAG.md` (Ägare 1, en påhittad person). Testbutiken har ingen regel för ägaren än.

Gränserna är Hugos beslut D18 och D19: A-gräns 20 000 kr (`2000000` öre), B-gräns 40 000 kr (`4000000` öre), 3 godkännanden innan nivå A, och K9 med 3 / 300 % / 33 %. Konton och varugrupper är SYNTETISKA och inte verifierade av en redovisningskonsult (D1–D16).

Regelboken ligger där agenten kan skriva. Tills spärrsteget flyttar den till en skyddad mapp är det kontrollsumman som visar om den har ändrats (DESIGN-regelbok.md, säkerhetsavsnittet).

## Konteringsförslaget och konfigurationen

Ett **konteringsförslag** är en verifikation som Vera föreslår men som ännu inte är bokförd (DESIGN-regelbok.md avsnitt 3). Det är ingen fil här, utan skapas av kärnan med `skapa_konteringsforslag` i `scripts/konteringsforslag.py`. Funktionen läser ingen fil själv. Den tar emot regelboken (`las_regelbok`), kontoplanen (`las_kontoplan`) och perioderna med underlag, bankrader och Z-rapporter, och kör alltid två kontroller. Allt som inte går ihop stoppar förslaget med ett tydligt fel, och inget förslag skapas.

- **K2 (debet = kredit):** minst två rader, varje belopp ett heltal i öre (aldrig decimaltal, `True` eller `False`, och aldrig negativt), exakt ett av debet och kredit på varje rad, summan av debet lika med summan av kredit, och varje konto finns i kontoplanen och gäller på verifikationens datum.
- **Ursprunget:** varje rad säger var beloppet kommer ifrån (ett värde i ett underlag, en bankrad eller en post i en Z-rapport) och hur det räknas (`lika`, `summa` eller `skillnad`). Kärnan räknar själv om beloppet ur källorna, och det ska bli exakt radens belopp. Så kan ingen siffra komma från modellen. Ingen avrundning görs: det är bara addition och subtraktion av heltal.

Det här i konfigurationen används av förslaget:

| Fil | Vad förslaget använder |
|---|---|
| `kontoplan.json` | Att kontot finns och gäller på datumet. Rollerna `ingaende_moms` och `utgaende_moms_per_sats`: en rad på ett **momskonto** får bara ha momsen ur en momsrad eller en momspost i en Z-rapport som ursprung, och på ett konto för utgående moms ska momsen ha kontots sats. Rollen `bank`: en rad på **bankkontot** får bara komma från bankrader, och pengar in står i debet, pengar ut i kredit. Rollerna slås upp med `kontots_roller`, så att kärnan aldrig har ett kontonummer i sin kod |
| `regelbok.json` | Regeln som förslaget bygger på ska finnas i regelboken, och **regelbokens kontrollsumma** står i varje förslag. Ändras regelboken med ett enda tecken får nya förslag en annan summa (förberedelse för spärrtestet "ändrad regelbok", SPEC 7) |

Förslaget får också kontrollsumman för varje fil det bygger på: underlagets, bankfilens och Z-filens. Summorna kommer från inläsningen, aldrig från den som skapar förslaget. Förslaget går inte att ändra efteråt och har **inget fält för att vara bokfört eller godkänt**. Det bokförs aldrig i det här steget.

Vilka konton ett flöde ska använda (till exempel leverantörsfakturan eller Z-rapporten) bestäms inte här. Det byggs i nästa steg, och kräver Hugos eller konsultens val (DESIGN-regelbok.md avsnitt 4 och 8).
