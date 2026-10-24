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
| `anteckning` | Nej | Fri text för människor. Används inte av koden |

Saknas en nyckel, finns en okänd nyckel, är något namn tomt eller dubbelt, eller är en avgränsare eller momsavrundning inte tillåten, stoppas inläsningen med ett tydligt fel.

Formatet i `syntet-testbutik/` är **antaget** och inte jämfört med en riktig exportfil från något kassasystem (Ö5). Momsavrundningen är utläst ur testdatan och inte kontrollerad mot Skatteverket eller en redovisningskonsult.
