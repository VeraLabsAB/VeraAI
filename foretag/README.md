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
