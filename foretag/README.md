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
