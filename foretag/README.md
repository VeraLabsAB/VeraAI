# foretag/

All företagsspecifik konfiguration ligger här, med en mapp per företag: `foretag/<namn>/`.

Hit hör till exempel regelbok, kontoplan, momssatser, beloppsgränser, kassasystem, bankformat och vem som får godkänna.

Sådant får aldrig skrivas i `scripts/`. Kärnan i `scripts/` är gemensam för alla företag och läser konfigurationen härifrån.
