# Granskningar

## Granskning av las_bank.py

| | |
|---|---|
| Datum | 2026-10-25 |
| Granskad version | commit b36ba6c ("Inläsning av bankfiler (Swedbank-CSV) och kontroll K1, saldokedjan") |
| Granskare | Oberoende session som inte sett bygget. Ingen kod eller befintlig fil har ändrats |
| Underlag | CLAUDE.md, SPEC.md (avsnitt 6 och 7), scripts/belopp.py, scripts/las_bank.py, scripts/tests/test_las_bank.py |

Obs: GRANSKNING.md fanns inte sedan tidigare, så filen skapades med det här avsnittet.

### Så gick granskningen till

Ett eget provskript skapade ett sextiotal små bankfiler i en temporär mapp utanför projektet (inte i `testdata/`), körde `las_bankfil` på var och en och skrev ut vad som hände. Den temporära mappen är borttagen efteråt. Varje fall gav ett av tre utfall:

- **STOPPAD**: modulen stoppade filen med ett tydligt `BankfilFel` (eller `K1Fel`). Det är rätt beteende för en trasig fil.
- **GODKÄND**: modulen släppte igenom raderna.
- **KRASCH**: modulen stoppade med ett annat, oförklarat fel.

Allvar: **hög** = kan ge fel bokföring, **medel** = onödig krasch eller otydligt fel, **låg** = kosmetiskt.

### Sammanfattning av fynden

| Nr | Fynd | Allvar |
|---|---|---|
| F1 | Ett citattecken i fel läge kan slå ihop flera transaktioner till en. Rader försvinner och kvarvarande rad får fel datum och referens, men K1 godkänner filen | **Hög** |
| F2 | En fil där de sista raderna saknas godkänns, eftersom inget utgående saldo kontrolleras | **Hög** |
| F3 | Vissa trasiga filer ger en krasch (`csv.Error`) i stället för `BankfilFel` | Medel |
| F4 | Radnummer kontrolleras inte: dubbla, osorterade och saknade radnummer godkänns | Medel |
| F5 | Swedbanks kolumnlayout ligger i kärnans kod, trots att bankformat enligt reglerna hör hemma i `foretag/<namn>/` | Medel |
| F6 | Två helt identiska rader får samma id | Låg |
| F7 | Saknad fil eller mapp ger systemfel i stället för `BankfilFel` | Låg |
| F8 | Trasig teckenkodning ger ett missvisande felmeddelande | Låg |
| F9 | Skräp direkt efter ett citerat fält godtas tyst | Låg |
| F10 | Den andra delen av K1 (ingående saldo plus summan) kan aldrig slå larm | Låg |
| F11 | `_tolka_rader` kan anropas direkt och hoppar då över K1 | Låg |

### Fynd i detalj

#### F1. Citattecken i fel läge slår ihop rader. K1 släpper igenom. Allvar: hög

**Vad jag körde** (fall 4g): en fil med tre transaktioner där beskrivningen på första raden börjar med ett citattecken som aldrig stängs på samma rad:

```
1,2025-01-03,2025-01-03,REF-1,"A,200.00,200.00
2,2025-01-04,2025-01-04,REF-2,B,-200.00,0.00
3,2025-01-28,2025-01-28,REF-3,C",75.00,75.00
```

**Vad som hände:** filen GODKÄNDES med **en** rad i stället för tre: radnummer 1, datum 2025-01-03, referens REF-1, belopp 75,00 kr och saldo 75,00 kr. Beskrivningen innehåller resten av rad 1 och hela rad 2 som text. Transaktionerna +200 och −200 har försvunnit, och beloppet 75 kr från 28 januari har fått datum och referens från 3 januari.

**Varför:** CSV-formatet (kommaseparerad text) tillåter radbrytningar inuti citerade fält. Läsaren tolkar därför allt från det första citattecknet fram till nästa citattecken som en enda text. K1 märker inget om de uppslukade raderna tillsammans blir noll kronor, till exempel en betalning och dess återbetalning.

**Varför det är realistiskt:** beskrivningen på en Swish-betalning är fritext som betalaren själv skriver. Ett meddelande som börjar med `"` räcker.

**Vad som borde hända:** filen ska stoppas. Förslag till byggaren (inte genomfört): stoppa filen om ett fält innehåller radbrytning, och/eller kräv att radnumren löper 1, 2, 3 … utan luckor (se F4). Den senare kontrollen fångar sammanslagningar mitt i filen, men inte i slutet, så radbrytningskontrollen behövs också.

Relaterat: fall 4f (där de uppslukade raderna inte blev noll) stoppades korrekt av K1, och fall 4h (ostängt citat på sista raden) stoppades korrekt.

#### F2. Avklippt fil godkänns. Allvar: hög

**Vad jag körde** (fall 8c): en fil där bara första raden av två finns kvar, med rätt ingående saldo.

**Vad som hände:** filen GODKÄNDES. Saldokedjan stämmer ju för de rader som finns kvar.

**Vad som borde hända:** en fil som saknar transaktioner i slutet ska inte kunna godkännas. Det går bara att upptäcka om modulen också får veta vad **utgående saldo** (saldot vid periodens slut) ska vara, till exempel från kontoutdraget eller nästa månads ingående saldo. Idag tar `las_bankfil` bara emot ingående saldo.

Det här strider inte mot K1 som den står i SPEC ("saldokedjan stämmer rad för rad"), men lämnar en lucka som kan ge ofullständig bokföring. K10 (månadsavstämning) kan fånga det senare, men den finns inte än. **Beslut behövs** (se nedan).

#### F3. Krasch med `csv.Error` i stället för `BankfilFel`. Allvar: medel

| Fall | Vad jag körde | Vad som hände |
|---|---|---|
| 9a | Ett NUL-tecken (tecken nummer 0) i en beskrivning | KRASCH: `csv.Error: line contains NUL` |
| 9b | Ett NUL-tecken på en rad före rubrikraden | KRASCH: samma |
| 9c | Hela filen sparad som UTF-16 (vanligt när man sparar "Unicode-text" från Excel) | KRASCH: samma |
| 9d | En beskrivning på 200 000 tecken | KRASCH: `csv.Error: field larger than field limit (131072)` |

**Vad som borde hända:** ett tydligt `BankfilFel` som säger vad som är fel. Filen stoppas visserligen, så ingen felaktig rad går igenom, men felet är oförklarat och fångas inte av kod som bara lyssnar efter `BankfilFel`.

#### F4. Radnummer kontrolleras inte. Allvar: medel

| Fall | Vad jag körde | Vad som hände |
|---|---|---|
| 2a | Radnummer 1, 1 (kedjan stämmer) | GODKÄND |
| 2b | Radnummer 3, 1, 2 (kedjan stämmer i filens ordning) | GODKÄND |
| 2c | Radnummer 1, 5 (lucka, kedjan stämmer) | GODKÄND |
| 2d | Nyaste raden först, radnummer 2, 1 | STOPPAD av K1 (rätt) |

Saldokedjan räknas i den ordning raderna står i filen, och radnumret används bara som etikett. Inget av fallen ger fel belopp i sig, men en lucka eller ett dubblerat radnummer är ett tecken på att filen är trasig (se F1). Förslag: kräv att radnumren är 1, 2, 3 … i tur och ordning.

#### F5. Bankformatet ligger i kärnan. Allvar: medel (strider mot reglerna)

`scripts/las_bank.py` innehåller Swedbanks kolumnnamn (`KOLUMNER`) och tillåtna avgränsare. Enligt CLAUDE.md ("Allt företagsspecifikt (… kassasystem, bankformat) ligger i `foretag/<namn>/`"), SPEC avsnitt 2 och `foretag/README.md` ("Sådant får aldrig skrivas i `scripts/`") hör bankformat till konfigurationen. Testet `test_karnan_ar_generell.py` fångar inte detta, eftersom det bara letar efter företagsnamn och organisationsnummer. Modulen säger själv att layouten är antagen och ska verifieras mot en riktig Swedbank-fil (Ö5). **Beslut behövs:** ska bankformat beskrivas per bank i konfigurationen, och var?

#### F6. Identiska rader får samma id. Allvar: låg

Fall 3b: två exakt likadana rader på 0,00 kr (samma radnummer och allt annat) GODKÄNDES och fick **samma** id. En senare dubblettkontroll (K4) eller lagring som använder id:t som nyckel kan då tappa en av dem. Med belopp 0 kr påverkas inte bokföringen. Med ett riktigt belopp stoppar K1 dubbletten (fall 3a, rätt). Fångas också av förslaget i F4.

Fall 3c (två köp med samma referens och belopp men olika radnummer) GODKÄNDES med olika id. Det är rätt: två likadana köp samma dag kan vara riktiga.

#### F7. Saknad fil eller mapp. Allvar: låg

Fall 9m och 9n gav `FileNotFoundError` respektive `IsADirectoryError` i stället för `BankfilFel`. Meddelandet går att förstå, men anropande kod som bara fångar `BankfilFel` kraschar.

#### F8. Missvisande meddelande vid trasig teckenkodning. Allvar: låg

Fall 9e: en UTF-8-fil med en enda trasig byte. Modulen faller då tillbaka på Windows-1252, "ö" blir "Ã¶", och rubrikraden känns inte igen. Filen STOPPADES (rätt), men meddelandet säger "hittar ingen rubrikrad" i stället för att peka på teckenkodningen.

#### F9. Skräp efter citerat fält godtas. Allvar: låg

Fall 4i: fältet `"REF"X` lästes tyst som `REFX`. Läsaren är förlåtande mot felaktiga citattecken. Det påverkar bara text, inte belopp eller datum.

#### F10. Andra delen av K1 kan aldrig slå larm. Allvar: låg

`kontrollera_k1` kontrollerar först varje rad och sedan att ingående saldo plus summan av beloppen är lika med sista radens saldo. Om varje rad stämmer är den andra kontrollen alltid sann, så den lägger inte till något skydd. Det kan ge intrycket att filens fullständighet kontrolleras, vilket den inte gör (se F2).

#### F11. `_tolka_rader` hoppar över K1. Allvar: låg

Funktionen kan importeras och anropas direkt och returnerar då rader utan att K1 har körts. Understrecket och kommentaren säger att den bara är till för tester, men inget hindrar annan kod från att använda den. SPEC avsnitt 6 säger att kontrollerna körs i kod. Värt att hålla koll på när fler steg byggs.

### Det som fungerade som det ska

| Fall | Vad jag körde | Utfall |
|---|---|---|
| 1a | Belopp med riktigt minustecken (−, U+2212) | STOPPAD, tydligt: ogiltigt belopp '−50.00' |
| 1b–1d, 1f | Tankstreck (–), minus efter beloppet, plustecken, saldo med U+2212 | STOPPAD, tydligt |
| 1e | −0,00 | GODKÄND som 0 öre (rätt) |
| 3a | Samma rad med belopp två gånger | STOPPAD av K1 |
| 4a–4d | Citerade fält med radbrytning, semikolon, komma och U+2028 (en ovanlig radbrytning) | GODKÄND, texten lästes rätt |
| 4e | U+2028 utan citattecken | STOPPAD, tydligt |
| 5a, 5b, 5d | Summarad, fritext och en ny rubrikrad efter sista transaktionen | STOPPAD, tydligt |
| 5c | Tomma rader och rader med bara kommatecken på slutet | GODKÄND, de tomma raderna hoppades över (rätt) |
| 6a | Belopp 0,00 | GODKÄND (rätt) |
| 6b, 6c | 99 999 999 999 999 999 999,99 kr och ett belopp med 5 000 siffror | GODKÄND som exakta heltal. Ingen övre gräns i inläsningen; det är K9:s sak (ovanliga belopp) |
| 6d, 6e | "100.5" och "1 234,56" i semikolonfil | GODKÄND som 10050 och 123456 öre (rätt) |
| 7a, 7b, 7c, 7g | 2025-02-30, 25-01-01, 0000-01-01, 01/02/2025 | STOPPAD, tydligt |
| 7d | 2024-02-29 (skottdag) | GODKÄND (rätt) |
| 7e, 7f | År 1900, datum som går bakåt i filen | GODKÄND. Rätt period är K6:s sak |
| 8a | Kedjan stämmer rad för rad men fel ingående saldo | STOPPAD av K1 på radnummer 1 |
| 8b | Samma fil med rätt ingående saldo | GODKÄND (rätt) |
| 9f, 9k | Extra kolumn, extra mellanslag runt kolumnnamn | GODKÄND (rätt) |
| 9g | Ostängt citattecken före rubrikraden | GODKÄND (rätt, raden före rubriken hoppas över) |
| 9h | Gamla Mac-radslut (bara CR) | GODKÄND (rätt) |
| 9i | Svenska decimalkomman utan citattecken i en kommafil | STOPPAD, fel antal fält |
| 9j | Citerat "1 000,50" i en kommafil | GODKÄND som 100050 öre (rätt) |
| 9l | Radnummer 007 | GODKÄND som 7 |

Belopp är heltal i öre hela vägen, och inga flyttal förekommer. Datum kontrolleras både till form och till att dagen finns.

### Testsviten

Kommando: `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests`

Resultat: **105 passed** (alla gröna), 0 misslyckade. `git status` var tom efter körningen, det vill säga ingen befintlig fil ändrades.

Obs: SPEC avsnitt 7 kräver en fast lista med kommandon, men listan finns inte i SPEC.md än. De kommandon som kördes i granskningen var Python (projektets `.venv`), pytest, git status och ls/cat/grep för att läsa filer.

### Beslut som behövs från Hugo

1. **F2:** ska `las_bankfil` också få utgående saldo och stoppa filen om det inte stämmer? Var kommer det värdet ifrån?
2. **F1/F4:** ska en fil stoppas om ett fält innehåller radbrytning, och om radnumren inte löper 1, 2, 3 …? (Rekommenderas.)
3. **F5:** ska bankformatet flyttas till konfigurationen, och i så fall hur?
