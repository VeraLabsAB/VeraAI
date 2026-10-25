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

## Åtgärder efter granskning

Rättat 2026-10-25 i en egen session, en commit per fynd. Alla tester ligger i `scripts/tests/test_las_bank.py`. Varje test nedan har körts mot den gamla koden (commit b36ba6c) och misslyckats där, och lyckas på den nya. Den gamla koden fick bara ta emot det nya argumentet för utgående saldo (utan att använda det), så att testerna kunde anropa den.

| Nr | Åtgärdad | Test |
|---|---|---|
| F1 | Ja. Ett fält med radbrytning (\n, \r, U+2028, U+2029) stoppar filen | `test_f1_citattecken_som_slar_ihop_rader_stoppas` (granskarens fall 4g), `test_f1_radbrytning_inuti_falt_stoppas` |
| F2 | Ja. `las_bankfil` och `kontrollera_k1` kräver utgående saldo, och sista radens saldo måste vara lika med det | `test_f2_avklippt_fil_stoppas` |
| F3 | Ja. NUL-tecken, UTF-16 och för långa fält ger `BankfilFel`. Övriga fel från csv-läsaren översätts också | `test_f3_nul_tecken_stoppas_med_bankfilfel`, `test_f3_nul_tecken_fore_rubrikraden_stoppas_med_bankfilfel`, `test_f3_utf16_stoppas_med_bankfilfel`, `test_f3_for_langt_falt_stoppas_med_bankfilfel` |
| F4 | Ja. Radnumren måste vara 1, 2, 3 … i tur och ordning | `test_f4_radnummer_maste_vara_1_2_3_i_tur_och_ordning` (dubbla, osorterade, saknade) |
| F5 | Ja (egen uppgift). Kolumnnamn och avgränsare ligger i `foretag/<namn>/bankformat.json` och läses med `ladda_bankformat`. `las_bankfil` tar bankformatet som argument. `test_karnan_ar_generell.py` stoppar nu också "Swedbank" och bankformatens kolumnnamn i kärnan | `test_karnan_innehaller_inga_kolumnnamn_fran_bankformaten`, `test_karnan_innehaller_inget_foretagsspecifikt` ("Swedbank"), `test_f5_annat_bankformat_laser_samma_data`, `test_f5_trasigt_bankformat_ger_bankfilfel`, `test_f5_saknat_bankformat_ger_bankfilfel` |
| F6 | Ja, genom rättelsen av F4: två identiska rader har samma radnummer och stoppas | `test_f6_identiska_rader_stoppas` |
| F7 | Ja. Saknad fil, mapp och oläsbar fil ger `BankfilFel` | `test_f7_saknad_fil_ger_bankfilfel`, `test_f7_mapp_ger_bankfilfel`, `test_f7_fil_som_inte_gar_att_lasa_ger_bankfilfel` |
| F8 | Ja. Meddelandet nämner teckenkodningen om filen inte är giltig UTF-8 | `test_f8_trasig_utf8_namner_teckenkodningen` (skyddstest som ska vara grönt även på gamla koden: `test_f8_giltig_utf8_utan_rubrikrad_namner_inte_teckenkodningen`) |
| F9 | Ja. Csv-läsaren körs i strikt läge | `test_f9_skrap_efter_citerat_falt_stoppas` |
| F10 | Ja. Den gamla andra delen av K1 är ersatt av jämförelsen med utgående saldo (F2) | `test_f2_avklippt_fil_stoppas` |
| F11 | Ja (egen uppgift). Ett test stoppar annan kod i `scripts/` (utom `tests/` och `las_bank.py`) från att använda `_tolka_rader` | `test_f11_ingen_annan_karnfil_anvander_tolka_rader` (skyddstest: `test_f11_kontrollen_hittar_en_fil_som_anvander_tolka_rader`) |

Testsviten efter rättelserna: 128 passed, 0 misslyckade.

## Granskning 2 av bankinläsningen

| | |
|---|---|
| Datum | 2026-10-25 |
| Granskad version | commit 8015dea ("GRANSKNING: F5 och F11 åtgärdade") |
| Granskare | Oberoende session som inte sett rättelserna eller konfigurationen byggas. Ingen kod eller befintlig fil har ändrats, bara det här avsnittet har lagts till |
| Underlag | CLAUDE.md, SPEC.md (avsnitt 2, 6, 7), foretag/README.md, foretag/syntet-testbutik/bankformat.json, scripts/belopp.py, scripts/las_bank.py, scripts/tests/test_las_bank.py, scripts/tests/test_karnan_ar_generell.py, tidigare granskning ovan |

### Så gick granskningen till

Egna provskript i en temporär mapp utanför projektet (inte i `testdata/`) skapade små bankfiler och bankformat, körde `ladda_bankformat` och `las_bankfil` och skrev ut utfallet: **STOPPAD** (tydligt `BankfilFel`/`K1Fel`), **GODKÄND** (raderna släpptes igenom) eller **KRASCH** (annat fel). För att pröva om testerna är starka nog gjordes också ett så kallat mutationstest: i en kopia av projektet (också i den temporära mappen) togs en rättelse i taget bort, och testsviten kördes mot kopian. Om sviten fortfarande är grön utan rättelsen är testet för svagt. Den temporära mappen är borttagen efteråt.

Allvar: **hög** = kan ge fel bokföring, **medel** = onödig krasch eller otydligt fel, **låg** = kosmetiskt.

### Uppgift A: är de tidigare fynden rättade?

Ja. Alla ursprungliga felfall stoppas nu med ett tydligt fel.

| Fynd | Vad jag körde | Utfall nu |
|---|---|---|
| F1 | Fall 4g (citattecken slår ihop tre rader), samma med CRLF-radslut, med citattecknet i referensen i stället, och med sammanslagning av de två sista raderna | STOPPAD: "rad 2 i filen har en radbrytning inuti fält nummer 5 …" |
| F2 | Avklippt fil (en av två rader kvar) | STOPPAD av K1: "sista radens saldo … men utgående saldo ska vara … Filen kan sakna rader" |
| F3 | NUL i beskrivning, NUL före rubrikraden, UTF-16 med och utan BOM, fält på 200 000 tecken, ostängt citattecken på sista raden | STOPPAD med svenska meddelanden. Inga `csv.Error` läcker ut |
| F4 | Radnummer 1,1 / 3,1,2 / 1,5 / börjar på 0 | STOPPAD: "har radnummer X, men nästa radnummer ska vara Y" |
| F6 | Två identiska rader på 0 kr | STOPPAD (radnummerkontrollen) |
| F7 | Saknad fil, mapp i stället för fil | STOPPAD med `BankfilFel` |
| F8 | UTF-8-fil med en trasig byte | STOPPAD, meddelandet nämner teckenkodningen |
| F9 | `"REF"X`, samt skräp efter citerat belopp | STOPPAD: "citattecken i fel läge" |
| F10 | Rätt kedja men fel utgående saldo | STOPPAD av K1 |

**Är testerna starka nog?** Mutationstestet visar att testsviten slår larm när någon av rättelserna för F1, F2, F3 (NUL, UTF-16, översättning av csv-fel), F4, F7, F8 och F9 tas bort, liksom när kontrollen av fältantal, av bankformatet i `las_bankfil`, av dubbla kolumnnamn i formatet, av avgränsare i kolumnnamn, av `anteckning` och av dubbla JSON-nycklar tas bort. De testerna är alltså inte gröna utan rättelsen. Fyra kontroller saknar test, se G8 nedan.

### Sammanfattning av nya fynd

Inga fynd med allvar hög. Ingen av proverna fick en felaktig fil att godkännas med verkliga radslut.

| Nr | Fynd | Allvar |
|---|---|---|
| G1 | Vissa ovanliga styrtecken räknas som radslut av Python men inte av F1-skyddet | Låg |
| G2 | Bankformatet godtar avgränsare och kolumnnamn som aldrig kan fungera | Låg |
| G3 | Saldo av fel typ ger `TypeError`, inte `BankfilFel`, och kontrolleras först efter att filen lästs | Låg |
| G4 | Djupt nästlad JSON i bankformat.json ger krasch (`RecursionError`) | Medel |
| G5 | Kolumnnamn med "ö" skrivet på två olika sätt (Unicode-normalisering) ger otydligt fel | Låg |
| G6 | En rad före rubriken som innehåller alla kolumnnamn väljs som rubrikrad och ger missvisande fel | Låg |
| G7 | Ingen storleksgräns: en miljon rader tar en halv minut och cirka 1 GB minne | Låg |
| G8 | Testluckor: fyra kontroller utan test, och två regeltester som går att lura | Låg (testlucka, koden är rätt idag) |
| G9 | Ett ändrat bankformat kan flytta datum utan att K1 märker det. Bankformatet och saldona ligger inte skyddat | Observation inför spärrsteget |

### Fynd i detalj

#### G1. Styrtecken som radslut. Allvar: låg

**Vad jag körde:** granskarens F1-fall 4g, men med tecknet "form feed" (`\x0c`, ett gammalt sidbrytningstecken) mellan raderna i stället för vanlig radbrytning. Även fält som innehåller `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e` eller `\x85`, med och utan citattecken.

**Vad som hände:** F1-fallet GODKÄNDES med **en** rad i stället för tre (beloppet 75 kr med datum och referens från rad 1), precis som det ursprungliga F1-felet. Ett citerat fält med något av tecknen godkändes. Ett ociterat fält stoppades med ett missvisande meddelande ("har 5 fält").

**Varför:** filen delas i rader med Pythons `splitlines`, som räknar de sex tecknen ovan som radslut. Kontrollen mot radbrytning inuti fält (`_RADBRYTNINGAR`) känner bara till `\n`, `\r`, U+2028 och U+2029.

**Varför allvaret är lågt:** det kräver en fil där raderna skiljs åt av sådana tecken. Riktiga bankexporter använder `\n` eller `\r\n`, och en Swish-text med tecknet inuti en enda transaktion ger rätt belopp och datum. Konsekvensen om det ändå hände vore däremot hög (sammanslagna transaktioner).

**Vad som borde hända:** samma uppsättning tecken i radkontrollen som i radindelningen. Förslag (inte genomfört): lägg till de sex tecknen i `_RADBRYTNINGAR`, eller dela filen bara på `\n` och `\r`.

#### G2. Avgränsare och kolumnnamn som aldrig kan fungera. Allvar: låg

**Vad jag körde:** bankformat med avgränsarna tom lista, två tecken, `"`, `\n`, `\r`, mellanslag, tom text, tal, `None`, text i stället för lista, samt `'`, tabb, hårt mellanslag, `\x0c`, `\x1e`, `\x85`, NUL, punkt, minus, siffran 0, bokstaven x, bakåtsnedstreck och en emoji. Kolumnnamn med komma, semikolon, citattecken, apostrof, tabb, `\x0c`, `\x85`, NUL, U+2028, osynligt mellanslag (U+200B), bara hårt mellanslag, tal och lista.

**Vad som hände:** de uppenbart felaktiga stoppades med tydligt fel. Men `ladda_bankformat` godkände `\x0c`, `\x1e`, `\x85`, NUL, punkt, minus, siffror, bokstäver och emoji som avgränsare, och `\x0c`, `\x85`, NUL och osynligt mellanslag i kolumnnamn. Ett format med `\x0c` som avgränsare kan aldrig hitta rubrikraden (se G1). Med punkt eller minus som avgränsare stoppades filerna i mina prov av kontrollen av antal fält, så ingen felaktig rad gick igenom.

**Vad som borde hända:** formatet bör stoppas redan när det läses in. Förslag: tillåt bara en kort lista med avgränsare (till exempel komma, semikolon, tabb och lodstreck) och inga styrtecken eller osynliga tecken i kolumnnamn.

#### G3. Saldo av fel typ ger `TypeError`. Allvar: låg

**Vad jag körde:** `las_bankfil` med ingående eller utgående saldo som flyttal (1.0, 100.0), text ("100"), `True`, `False`, `None`, `Decimal` och `Fraction`.

**Vad som hände:** alla stoppades, men med `TypeError` ("Utgående saldo måste vara ett heltal i öre, inte float."), inte `BankfilFel`. Kontrollen görs först efter att hela filen lästs och tolkats, så en trasig fil ger `BankfilFel` och döljer att saldot har fel typ. Ett felaktigt bankformat ger däremot `BankfilFel` direkt. Ett heltal av en underklass (`IntEnum`) godkändes, vilket är ofarligt.

**Vad som borde hända:** inget felaktigt släpps igenom, och meddelandet är tydligt, så det här är ett medvetet val (testet `test_k1_vagrar_float` kräver `TypeError`). Två förbättringar att överväga: kontrollera saldonas typ innan filen läses, och bestäm om anropande kod ska behöva fånga både `TypeError` och `BankfilFel`.

#### G4. Djupt nästlad JSON i bankformatet kraschar. Allvar: medel

**Vad jag körde:** en bankformat.json med 100 000 nästlade hakparenteser (`[[[[…]]]]`).

**Vad som hände:** KRASCH med `RecursionError` i stället för `BankfilFel`.

**Vad som borde hända:** `BankfilFel` med ett tydligt meddelande. Det är en onödig krasch och därmed medel enligt skalan, men den kan bara uppstå om konfigurationen är trasig eller manipulerad. Inget läses in fel.

#### G5. Två sätt att skriva "ö". Allvar: låg

**Vad jag körde:** en bankfil vars rubrikrad är sparad i så kallad NFD-form (där "ö" lagras som "o" plus två prickar, vilket vissa Mac-program gör), och omvänt ett bankformat i NFD med en vanlig fil.

**Vad som hände:** STOPPAD med "hittar ingen rubrikrad med kolumnerna … Bokföringsdag … Bokfört saldo". Namnen i meddelandet ser exakt ut som i filen, så felet är svårt att förstå.

**Vad som borde hända:** antingen jämföra namnen efter normalisering, eller nämna i felmeddelandet att tecken kan vara lagrade på olika sätt.

#### G6. Missvisande rubrikrad. Allvar: låg

**Vad jag körde:** en fil med raden `Info,Radnummer,Bokföringsdag,…` före den riktiga rubrikraden.

**Vad som hände:** förraden valdes som rubrikrad, och filen STOPPADES med "rad 2 i filen har 7 fält, men rubrikraden har 8". Ingen rad gick igenom, men meddelandet pekar inte på orsaken.

#### G7. Stora filer. Allvar: låg

**Vad jag körde:** korrekta filer med 100 000 rader (7,8 MB) och 1 000 000 rader (82 MB), samma filer med fel på sista raden, 20 000 rader med 1 000 fält utan rubrikrad, samt ett belopp med 100 000 siffror.

**Vad som hände:**

| Fall | Utfall | Tid | Minne |
|---|---|---|---|
| 100 000 rader | GODKÄND | 2,6 s | cirka 100 MB |
| 100 000 rader, fel på sista raden | STOPPAD av K1 på radnummer 100 000 | 1,0 s | |
| 1 000 000 rader | GODKÄND | 29 s | cirka 1 GB |
| 1 000 000 rader, fel på sista raden | STOPPAD av K1 på radnummer 1 000 000 | 9,7 s | |
| 20 000 rader × 1 000 fält, ingen rubrik | STOPPAD | 1,4 s | |
| Belopp med 100 000 siffror | GODKÄND som exakt heltal. Felmeddelanden skriver ut hela talet | 0,4 s | |

Det fungerar och går i rimlig tid för 100 000 rader, vilket är långt mer än ett småföretag har på en månad. Det finns ingen övre gräns för filstorlek eller belopp. Beloppsgränsen hör till K9 (ovanliga belopp). En gräns för filstorlek kan övervägas.

#### G8. Testluckor. Allvar: låg (koden är rätt idag)

Mutationstestet hittade fyra kontroller som kan tas bort utan att någon test blir röd:

1. **Kolumnen står flera gånger på rubrikraden** ("rubrikraden … har kolumnen 'Belopp' flera gånger"). Kontrollen fungerar (provat), men saknar test. Utan den skulle den första av två kolumner med samma namn användas utan varning.
2. **Mellanslag som avgränsare** är förbjudet i koden, men inget test kräver det.
3. **`True`/`False` som saldo** stoppas i koden, men inget test kräver det. `False` är lika med 0 i Python och skulle annars godkännas som ingående saldo 0.
4. **Tomma rader hoppas över** är inte testat (det är ett beteende, inte en rättelse).

Två regeltester går att lura. Provat i en kopia, där sviten var grön (159 passed) trots ändringarna:

5. **F11-testet** söker bara efter texten `_tolka_rader` i andra filer. Ett alias i `las_bank.py` (`TOLKA = _tolka_rader`) eller `getattr(las_bank, "_tolka_" + "rader")` i en annan fil passerar.
6. **`test_karnan_ar_generell.py`** letar efter företagsnamn, organisationsnummer, "Swedbank" och bankformatens kolumnnamn. Konstanterna `BANK = "Nordea"`, `KONTO = 1930`, `MOMS = 25` och `TILLATNA_AVGRANSARE = [",", ";"]` i `las_bank.py` passerade. SPEC avsnitt 2 säger att konto, momssats och belopp ska kontrolleras med ett test. Idag finns inga sådana i kärnan (se uppgift C), men testet behöver byggas ut när kontoplan och momssatser kommer.

#### G9. Bankformatet och saldona ligger inte skyddat. Observation inför spärrsteget

**Vad jag körde:** testbutikens riktiga januarifil med en kopia av bankformatet där `bokforingsdag` och `transaktionsdag` bytt plats.

**Vad som hände:** GODKÄND, 118 rader, varav 18 med annan bokföringsdag (till exempel radnummer 12: 2025-01-04 i stället för 2025-01-07). K1 räknar bara belopp och saldo, så den kan inte märka det.

**Varför det spelar roll:** SPEC avsnitt 7 säger att en spärr aldrig får läsa från en mapp som agenten kan skriva i. `ladda_bankformat` tar emot vilken sökväg som helst, och `foretag/` är inte skrivskyddad. Ingående och utgående saldo kommer från den som anropar, och i testerna från `testdata/…/facit.json`. Varifrån de ska komma i drift är inte bestämt. Det bryter inte mot reglerna idag, eftersom spärrarna inte är byggda än, men det måste lösas i spärrsteget. Fel datum skulle annars kunna ge bokföring i fel period (K6).

### Uppgift B: övrigt som provades och fungerade

| Prov | Utfall |
|---|---|
| Bankformat som skickas direkt som `None`, lista, tal, text, sökväg, tom ordlista, `kolumner=None`, avgränsare som tuple, `anteckning=None`, okänd nyckel | STOPPAD med `BankfilFel` och tydligt meddelande |
| Kolumnnamn som krockar efter borttagna blanksteg (`" Belopp "` och `"Belopp"`) | STOPPAD |
| Kolumnnamn som bara skiljer i stor/liten bokstav (`"Belopp"` och `"belopp"`) | Godkänt i formatet. Jämförelsen är exakt, så båda kolumnerna hittas rätt i filen. Rubrik med `belopp` när formatet säger `Belopp` stoppas |
| Kolumnnamn med internt dubbelt mellanslag | Godkänt som eget namn (exakt jämförelse) |
| Omkastade saldon (570 kr in, 500 kr ut i stället för tvärtom) | STOPPAD av K1 på radnummer 1. Meddelandet antyder inte att saldona kan vara omkastade (kosmetiskt). Om månadens netto är 0 är omkastade saldon lika med rätt saldon, och filen godkänns, vilket är rätt |
| Bara rubrikrad, med och utan radslut, med tomma rader, med rader med bara komman eller blanksteg | STOPPAD: "filen har en rubrikrad men inga transaktionsrader" |
| Tom fil, fil med bara BOM | STOPPAD: "hittar ingen rubrikrad" |
| `anteckning` på 1 MB, `anteckning` med en "instruktion" | Godkänt. Kärnan returnerar inte anteckningen och använder den inte |
| `anteckning` som `null` eller lista, okända nycklar (`Kolumner`, `_kommentar`), dubbla nycklar | STOPPAD |
| Bankformat med BOM / UTF-16 / `NaN` / tomt / bara en text | Godkänt / STOPPAD / STOPPAD / STOPPAD / STOPPAD (rätt) |
| Två månader ihopklistrade i en fil | STOPPAD: andra rubrikraden har ogiltigt radnummer |
| Rubrik med semikolon men data med komma | STOPPAD |
| Komma inuti fält i en semikolonfil | GODKÄND, texten rätt |
| Mellanslag före citattecken (`, "A,B"`) | STOPPAD (fel antal fält) |
| Windows-1252-fil med "…" (byte 0x85) | GODKÄND, "…" läses rätt (inget radslut) |
| Belopp `1 000,50` med vanligt och hårt mellanslag, `1,5` i semikolonfil | GODKÄND som 100050 och 150 öre (rätt) |
| Belopp `1.234` och `1,234.56` | STOPPAD (rätt: kan vara engelsk tusentalsavgränsare) |
| Datum med blanksteg runt, radnummer `" 1 "` | GODKÄND (blanksteg tas bort, rätt) |
| Datum med fullbreddssiffror (２０２５) | STOPPAD |
| Tom referens och beskrivning | GODKÄND (bara text) |
| Avgränsarna tabb, hårt mellanslag och lodstreck i ett riktigt format | GODKÄND, rätt rader |

### Uppgift C: kontroll mot reglerna

| Kontroll | Resultat |
|---|---|
| Företags- eller bankspecifika uppgifter i `scripts/` (utom `tests/`) | Inga. Inga företagsnamn, banknamn, kolumnnamn, konton, momssatser eller belopp. Talen som finns är 100 (öre per krona), 16 (längd på id) och exempel i kommentarer |
| Flyttal | Inga. Ordet "float" förekommer bara i en kommentar som förbjuder det |
| Nätverksanrop | Inga (ingen `socket`, `urllib`, `http`, `requests`) |
| Körning av kommandon | Ingen (ingen `subprocess`, `os.system`, `eval`, `exec`) |
| Filåtkomst | Bara läsning (`open(sokvag, "rb")`) av den sökväg anroparen anger, i `ladda_bankformat` och `las_bankfil`. Inget skrivs. Ingen kontroll av att sökvägen ligger i en skyddad mapp, se G9 |
| `git diff 7823bd8 -- SPEC.md` | Tom. SPEC.md är oförändrad sedan commit 7823bd8. CLAUDE.md är också oförändrad. `foretag/README.md` har fått 14 nya rader (avsnittet om bankformat.json), vilket stämmer med F5 |
| Fast lista med kommandon (SPEC avsnitt 7) | Finns fortfarande inte i SPEC.md |

### Testsviten

Kommando: `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests`

Resultat: **159 passed**, 0 misslyckade, både före och efter granskningen. `git status` visade bara den här filen som ändrad.

Kommandon som kördes i granskningen: Python i projektets `.venv` (provskript och pytest), `git log`, `git diff`, `git status`, `git rev-parse`, samt `ls`, `cat`, `grep`, `sed`, `cut`, `od`, `rsync`, `cp`, `mkdir` och `rm` (de tre sista bara i den temporära mappen).

### Beslut som behövs från Hugo

1. **G9:** var ska bankformatet och ingående/utgående saldo ligga så att agenten inte kan ändra dem, och varifrån kommer saldona i drift (kontoutdrag, föregående månad)? Hör till spärrsteget.
2. **G1, G2, G4:** ska de rättas nu (små ändringar i `las_bank.py` med test) eller samlas till nästa byggsteg? Rekommendation: rätta G1 nu, eftersom det gäller samma skydd som F1.
3. **G8:** ska testerna för kärnans generalitet och F11 byggas ut nu, eller när kontoplan och momssatser läggs till?

## Åtgärder efter granskning 2

Rättat 2026-10-25 i en egen session, i commit c6f84bf. Alla tester ligger i `scripts/tests/test_las_bank.py`.

**Så bevisades testerna.** De nya testerna kördes i en kopia av projektet utanför projektmappen, där `las_bank.py` var den gamla versionen (commit 1d2c03f, samma kod som granskades i 8015dea). Där blev 23 nya tester röda av rätt skäl: 20 släpptes igenom (`DID NOT RAISE`), 2 kraschade med `RecursionError` och 1 gav granskarens missvisande meddelande "har 5 fält". Dessutom gjordes ett mutationstest på den nya koden: en kontroll i taget togs bort i en kopia, och hela sviten kördes.

| Borttagen kontroll (i en kopia) | Röda tester |
|---|---|
| G1: kontrollen av styrtecken i bankfilen | 7 (`test_g1_…`) |
| G2: fasta listan med avgränsare | 12 (`test_g2_avgransare_…`, `test_g8_mellanslag_…`, två fall i `test_f5_trasigt_bankformat_…`) |
| G2: styrtecken och osynliga tecken i kolumnnamn | 5 (`test_g2_styrtecken_och_osynliga_…`) |
| G4: fångsten av `RecursionError` | 2 (`test_g4_…`) |
| G8 punkt 1: dubbla kolumner på rubrikraden | 1 (`test_g8_kolumn_flera_ganger_…`) |
| G8 punkt 3: `True`/`False` som saldo | 4 (`test_g8_true_och_false_…`) |
| G8 punkt 2, i den gamla koden: mellanslag bland förbjudna avgränsare | 1 (`test_g8_mellanslag_…`) |

G8 punkt 1, 2 och 3 fungerade redan i den gamla koden, så de testerna är gröna även där. Det gäller också punkt 2 (mellanslag), som förbjöds redan innan.

| Nr | Åtgärdad | Test |
|---|---|---|
| G1 | Ja. En bankfil som innehåller ett styrtecken (Unicode-kategori Cc) utom tabb, `\n` och `\r`, eller U+2028/U+2029, stoppas med `BankfilFel`, var tecknet än står: inuti eller mellan fält, med eller utan citattecken, även före rubrikraden | `test_g1_citattecken_som_slar_ihop_rader_med_styrtecken_stoppas` (fall 4g med `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e`, `\x85`), `test_g1_styrtecken_i_vanligt_falt_stoppas` (skyddstest: `test_g1_tabb_och_vanliga_radslut_ar_tillatna`) |
| G2 | Ja. Bara komma, semikolon, tabb och lodstreck godtas som avgränsare. Kolumnnamn med styrtecken (Cc, även tabb) eller osynliga tecken (Cf) förkastas | `test_g2_avgransare_utanfor_fasta_listan_forkastas` (`\x0c`, `\x1e`, `\x85`, NUL, punkt, minus, siffra, bokstav, emoji), `test_g2_styrtecken_och_osynliga_tecken_i_kolumnnamn_forkastas` (`\x0c`, `\x85`, NUL, U+200B, tabb) (skyddstest: `test_g2_avgransarna_i_fasta_listan_godtas`) |
| G3 | Nej, medvetet | Se nedan |
| G4 | Ja. Djupt nästlad JSON i bankformat.json ger `BankfilFel` med tydligt meddelande | `test_g4_djupt_nastlat_bankformat_ger_bankfilfel` (100 000 hakparenteser, 100 000 klammerparenteser) |
| G5 | Nej, medvetet | Se nedan |
| G6 | Nej, medvetet | Se nedan |
| G7 | Nej, medvetet | Se nedan |
| G8 punkt 1 | Ja (test tillagt, koden var redan rätt) | `test_g8_kolumn_flera_ganger_pa_rubrikraden_stoppas` |
| G8 punkt 2 | Ja (test tillagt, koden var redan rätt) | `test_g8_mellanslag_som_avgransare_forkastas` |
| G8 punkt 3 | Ja (test tillagt, koden var redan rätt) | `test_g8_true_och_false_som_saldo_stoppas` (ingående och utgående, `True` och `False`) |
| G8 punkt 4–6 | Nej, medvetet | Se nedan |
| G9 | Nej, medvetet | Se nedan |

**Varför resten inte är åtgärdat nu.** Uppgiften var att rätta G1, G2, G4 och G8 punkt 1–3. Övriga fynd släpper inte igenom någon felaktig rad idag, och flera kräver ett beslut först:

- **G3** (saldo av fel typ ger `TypeError`): ett medvetet val som ett befintligt test (`test_k1_vagrar_float`) kräver. Om det ska bli `BankfilFel`, och om typen ska kontrolleras innan filen läses, är ett beslut om hur anropande kod ska fånga fel. Felaktiga saldon stoppas redan.
- **G5** (två sätt att skriva "ö"): att normalisera namnen ändrar vad som räknas som samma kolumnnamn, och det bör bestämmas medvetet. Filen stoppas redan, bara meddelandet är otydligt.
- **G6** (missvisande rubrikrad): filen stoppas redan. En bättre lösning kräver ändrad logik för hur rubrikraden väljs.
- **G7** (ingen storleksgräns): en gräns är ett beslut om hur stor en bankfil får vara, och kanske per företag. 100 000 rader går på under 3 sekunder.
- **G8 punkt 4** (tomma rader hoppas över): ett beteende, inte en rättelse, och ingick inte i uppgiften.
- **G8 punkt 5–6** (regeltesterna för F11 och kärnans generalitet går att lura): granskningens beslut 3. Hör ihop med när kontoplan och momssatser läggs till. Obs: kärnan har nu konstanten `TILLATNA_AVGRANSARE` med komma, semikolon, tabb och lodstreck. Den är en allmän CSV-regel som gäller alla företag (företagets egna avgränsare står fortfarande i bankformat.json), men den är just en sådan konstant som granskaren visade att generalitetstestet inte skulle upptäcka.
- **G9** (bankformat och saldon ligger inte skyddat): hör till spärrsteget och kräver beslut om var bankformatet och saldona ska ligga och varifrån saldona kommer i drift (granskningens beslut 1).

**Övrigt som ändrats.** Ett befintligt testfall (`avgransare_i_kolumnnamn` i `test_f5_trasigt_bankformat_ger_bankfilfel`) hade tabb inuti ett kolumnnamn. Det stoppas nu av G2-kontrollen i stället, så testfallet använder lodstreck och prövar fortfarande samma sak. `foretag/README.md` och beskrivningen överst i `las_bank.py` har uppdaterats med de nya reglerna. SPEC.md är inte ändrad.

Testsviten efter rättelserna: 190 passed, 0 misslyckade.

## Granskning 3: rättelser efter granskning 2 och kassainläsningen

| | |
|---|---|
| Datum | 2026-10-25 |
| Granskad version | commit a2d1540 ("Kassans Z-rapporter: inläsning, Z-kontroll a–e och kontroll av Z-serien") |
| Granskare | Oberoende session som inte sett rättelserna efter granskning 2 eller kassainläsningen byggas. Ingen kod eller befintlig fil har ändrats, bara det här avsnittet har lagts till |
| Underlag | CLAUDE.md, SPEC.md (avsnitt 2, 5, 6, 7, 8), foretag/README.md, foretag/syntet-testbutik/bankformat.json och kassaformat.json, scripts/belopp.py, scripts/las_bank.py, scripts/las_kassa.py, alla filer i scripts/tests/, testdata/README.md, facit.json, Z-filerna för 2025-01-02 och 2025-03-31, tidigare granskningar ovan |

### Så gick granskningen till

Egna provskript i en temporär mapp utanför projektet (inte i `testdata/`) skapade små bankfiler, Z-filer och kassaformat, körde `las_bankfil`, `ladda_bankformat`, `las_kassafil` och `kontrollera_z_serien` och skrev ut utfallet: **STOPPAD** (tydligt `BankfilFel`/`KassafilFel` eller underklass), **GODKÄND** (raderna släpptes igenom) eller **KRASCH** (annat, oförklarat fel). Mutationstesterna gjordes i en kopia av projektet i samma temporära mapp. Den temporära mappen är borttagen efteråt.

Ord som används nedan: en **Z-rapport** är kassans dagsavslut. **Z-numret** är rapportens löpnummer. **Kassaregistret** är id för den kassa rapporten kommer från. En **mutation** är en avsiktligt borttagen kontroll i en kopia, för att se om testerna märker det.

Allvar: **hög** = kan ge fel bokföring, **medel** = onödig krasch eller otydligt fel, **låg** = kosmetiskt.

### Uppgift A: är G1, G2, G4 och G8 punkt 1–3 rättade?

Ja. Alla ursprungliga felfall stoppas nu med ett tydligt fel.

| Fynd | Vad jag körde | Utfall nu |
|---|---|---|
| G1 | Granskarens F1-fall 4g (citattecken slår ihop tre rader) med `\x0b`, `\x0c`, `\x1c`, `\x1d`, `\x1e` och `\x85` som radslut. Samma tecken inuti ett citerat fält och på en rad före rubrikraden | STOPPAD i alla 18 fall: "rad N i filen innehåller tecknet U+000C, som är ett styrtecken eller en ovanlig radbrytning …". Skydd: tabb i ett fält och CRLF-radslut GODKÄNDES som förut |
| G2 | Bankformat med avgränsarna `\x0c`, `\x1e`, `\x85`, NUL, punkt, minus, `0`, `x`, emoji, mellanslag, bakåtsnedstreck, apostrof, citattecken, `\n`, tom text och två tecken. Kolumnnamn med `\x0c`, `\x85`, NUL, U+200B, tabb, U+FEFF och U+202E | STOPPAD i alla fall, med "avgränsaren … är ogiltig. Tillåtna avgränsare är komma, semikolon, tabb och lodstreck" respektive "innehåller tecknet U+…" |
| G4 | bankformat.json med 100 000 hakparenteser, 100 000 klammerparenteser och 1 000 000 hakparenteser | STOPPAD: "för många hakparenteser eller klammerparenteser inuti varandra" |
| G8 punkt 1 | Rubrikrad med kolumnen `Belopp` två gånger | STOPPAD: "rubrikraden (rad 1 i filen) har kolumnen 'Belopp' flera gånger" |
| G8 punkt 2 | Mellanslag som avgränsare | STOPPAD (se G2) |
| G8 punkt 3 | `True` och `False` som ingående och utgående saldo | STOPPAD med `TypeError` ("… måste vara ett heltal i öre, inte bool"). `TypeError` i stället för `BankfilFel` är det medvetna valet från G3 |

Kassainläsningen har samma skydd: styrtecken, U+2028, NUL, avgränsare utanför fasta listan och djup JSON i kassaformat.json stoppas (provat och testat i `test_las_kassa.py`).

### Sammanfattning av nya fynd

Inga fynd med allvar hög. Ingen av proverna fick en Z-fil med fel siffror att godkännas: Z-kontroll a–e stoppade alla filer där försäljning, betalsätt, moms eller datum inte gick ihop.

| Nr | Fynd | Allvar |
|---|---|---|
| H1 | Ett mycket stort Z-nummer får seriekontrollen att krascha eller ta slut på minne | Medel |
| H2 | Samma Z-rapport räknas två gånger om kassaregistrets namn skiljer sig lite (stor bokstav, osynligt tecken) | Medel |
| H3 | En UTF-8-fil med ett enda felkodat tecken läses som Windows-1252 utan varning, och kassaregistrets namn blir förvanskat | Låg |
| H4 | Z-nummer som börjar om (till exempel vid årsskifte) ger ett missvisande meddelande. Om det är tillåtet är en öppen fråga | Låg (plus Öppen fråga) |
| H5 | Filnamnsmönstret har bara datum, så två kassaregister eller två Z-rapporter samma dag kan inte ligga i samma mapp | Låg (observation, hör till Ö5) |
| H6 | Seriekontrollen godkänner en tom lista | Låg |
| H7 | Z-kontrollerna godtar vilken momssats som helst och en fil med bara totalsumman 0 | Observation inför K5 och K10 |
| H8 | Små brister i hjälpfunktioner som bara anropas inifrån kärnan | Låg |
| H9 | Långsam kontroll av kassaformat med tiotusentals betalsätt, och obegränsat långa felmeddelanden | Låg |
| H10 | Generalitetstestet går fortfarande att lura (G8 punkt 5–6 är inte åtgärdat, medvetet). Undantaget "belopp" är däremot smalt | Låg (testlucka) |
| H11 | kassaformat.json ligger lika oskyddat som bankformatet (fortsättning på G9) | Observation inför spärrsteget |

### Fynd i detalj

#### H1. Mycket stort Z-nummer kraschar seriekontrollen. Allvar: medel

**Vad jag körde:** två giltiga Z-filer för samma kassaregister med Z-nummer 1 och 10 000 000, 1 och 10¹² (en etta med tolv nollor), 1 och 10²⁰, samt 1 och ett tal med 5 000 siffror. Inläsningen godkänner alla dessa Z-nummer (även 5 000 siffror), eftersom ett Z-nummer bara måste bestå av siffror.

**Vad som hände:** med 10 000 000 STOPPADES serien rätt ("Z-rapport 2–9999999 (9999998 st) saknas"), men programmet byggde en lista med tio miljoner tal. Med 10¹² försökte det bygga en lista med en biljon tal: minnet tog slut och processen dödades av operativsystemet (avslutskod 137). Med 10²⁰ och 5 000 siffror blev det KRASCH med `OverflowError`.

**Varför:** `kontrollera_z_serien` sparar varje saknat Z-nummer i en lista (`saknade = list(range(z_fore + 1, z_efter))`), oavsett hur många de är.

**Vad som borde hända:** `ZSerieFel` av typen "lucka" med ett tydligt meddelande, utan krasch. Förslag (inte genomfört): spara bara första och sista saknade numret och antalet när luckan är stor, och/eller sätt en övre gräns för hur många siffror ett Z-nummer får ha. Inget släpps igenom, men en trasig fil kan stoppa hela körningen.

#### H2. Samma Z-rapport kan räknas två gånger. Allvar: medel

**Vad jag körde:** två Z-filer i olika mappar, med samma datum, samma Z-nummer (1001) och samma belopp, där kassaregistret heter `TB-1` i den ena och `tb-1`, `TB-1` + osynligt mellanslag (U+200B) respektive `TB-1 X` i den andra. Sedan `kontrollera_z_serien` och `summa_per_momssats` på båda.

**Vad som hände:** båda filerna GODKÄNDES, seriekontrollen GODKÄNDE, och försäljningen med 12 % blev 224,00 kr i stället för 112,00 kr. Samma sak med två helt identiska filer där registret skiljer sig stoppas däremot som dubblett.

**Varför:** seriekontrollen letar dubbletter bara inom samma kassaregister, och registrets namn jämförs exakt. Ett namn med osynliga tecken (Unicode-kategori Cf, till exempel U+200B och U+202E som vänder text) släpps igenom i Z-filens data, eftersom skyddet mot ovanliga tecken bara gäller styrtecken (Cc). Det finns ingen lista över vilka kassaregister företaget har.

**Varför allvaret är medel och inte hög:** det kräver en fil där registrets namn har ändrats för hand eller av ett fel, och samma Z-rapport finns kvar i originalskick. Ett kassasystem byter inte namn på sin kassa mellan två exporter. Konsekvensen om det ändå händer är däremot hög (dubbel försäljning), och seriekontrollen är idag det enda skyddet mot dubbla Z-rapporter (K4 och K10 är inte byggda).

**Vad som borde hända:** filen stoppas. Förslag (inte genomfört): lägg en lista över företagets kassaregister i kassaformat.json (det är företagsspecifikt) och stoppa Z-filer från okända register, och stoppa osynliga tecken (Cf) i Z-filens fält på samma sätt som styrtecken.

#### H3. Förvanskat kassaregister vid blandad teckenkodning. Allvar: låg

**Vad jag körde:** (a) en UTF-8-fil med kassaregistret `KASSA-Ö` och en extra kolumn där ett enda tecken var sparat som Windows-1252 (`café`). (b) En UTF-8-fil med BOM (ett osynligt märke först i filen som säger att den är UTF-8) och en trasig byte på sista raden.

**Vad som hände:** (a) GODKÄND, men kassaregistret blev `KASSA-Ã–`. Det räknas då som ett annat register än `KASSA-Ö` i seriekontrollen, så Z-numret saknas i rätt registers serie (missvisande lucka, eller ingen varning alls om filen är periodens första eller sista). (b) STOPPAD med "första raden i filen ska vara en rubrikrad med kolumnerna …", utan att teckenkodningen nämns.

**Varför:** filen läses som UTF-8 om det går, annars som Windows-1252, och ett enda felaktigt tecken räcker för att hela filen läses på det andra sättet. I `las_bank.py` nämner felmeddelandet teckenkodningen i det läget (F8). Det tillägget finns inte i `las_kassa.py`.

**Vad som borde hända:** samma hjälpande meddelande som i bankinläsningen. Överväg också att stoppa en fil som börjar med UTF-8-BOM men inte är giltig UTF-8.

#### H4. Z-nummer som börjar om ger missvisande meddelande. Allvar: låg. Öppen fråga

**Vad jag körde:** serierna 1001, 1002, 1, 2 (nollställd mitt i), 1300 (2025-12-31) följd av 1 (2026-01-02), och 1300 följd av 1301 över årsskiftet.

**Vad som hände:** 1300 → 1301 GODKÄNDES (rätt). De nollställda serierna STOPPADES, men med till exempel "Z-rapport 2–1299 (1298 st) saknas mellan Z-rapport 1 (2026-01-02) och Z-rapport 1300 (2025-12-31). Den saknade rapporten är från 2026-01-02 eller 2025-12-31". Datumen står i omvänd ordning och antalet saknade rapporter är fel.

**Öppen fråga:** om ett kassaregisters Z-nummer får börja om (vid årsskifte, vid byte av kassa, eller när räknaren slår runt) har jag inte kontrollerat. Det ska verifieras med Skatteverket eller en redovisningskonsult innan kontrollen ändras. Om det är tillåtet måste kärnan kunna ta emot en ny serie, annars stoppas varje januari.

**Vad som borde hända oavsett svar:** när Z-numret går ner medan datumet går fram bör meddelandet säga att serien verkar ha börjat om, inte att över tusen rapporter saknas.

#### H5. Filnamnet rymmer bara datum. Allvar: låg (observation)

Filnamnsmönstret (`kassa_ÅÅÅÅ-MM-DD.csv`) har bara datumet. Två kassaregister, eller två Z-rapporter från samma kassa samma dag, får då samma filnamn och kan inte ligga i samma mapp. Kontrollen klarar fallet om filerna ligger i olika mappar (provat: två register samma dag med samma Z-nummer, och två Z-rapporter samma dag, GODKÄNDES rätt). Ett företag med flera kassor kommer ändå att behöva ett mönster med kassans id. Hör till Ö5 (vilka kassasystem som ska stödjas).

#### H6. Tom lista godkänns av seriekontrollen. Allvar: låg

`kontrollera_z_serien([])` GODKÄNDES utan meddelande. En period helt utan Z-rapporter ser alltså likadan ut som en felfri period. Det stämmer med beskrivningen i koden (bara luckor mellan rapporterna som finns syns), men bör fångas: antingen här (stoppa en tom lista) eller i K10 (kassan mot banken), som också måste upptäcka att periodens första eller sista Z-rapport saknas.

#### H7. Z-kontrollerna godtar vilken momssats som helst. Observation inför K5 och K10

**Vad jag körde:** Z-filer med momssats 0, 99 och 200 000 påhittade satser (en rad per sats, 1,4 sekunder), en fil med bara totalsumman 0, en fil med +1 000 kr i en sats och −1 000 kr i en annan, och en fil med bara en moms-rad på 0.

**Vad som hände:** alla GODKÄNDES, eftersom siffrorna går ihop inbördes. Z-kontroll a–e prövar bara att filen är konsekvent med sig själv, inte att satsen finns för datumet. En fil med bara totalsumman 0 och rätt Z-nummer fyller också en lucka i serien.

**Varför det spelar roll:** det är rätt för en inläsningskontroll, men K5 ("satsen finns för datumet", mot företagets momssatser i konfigurationen) och K10 (kassan mot banken) måste byggas innan försäljningen bokförs. Negativa belopp (returer) och noll i alla poster GODKÄNDES också, vilket är rätt beteende.

#### H8. Hjälpfunktioner. Allvar: låg

- `momsen_i_brutto` är en publik funktion utan typkontroll: satsen 12,5 (flyttal) ger flyttalet `11.0`, `True` räknas som 1, och satsen −100 ger `ZeroDivisionError`. Kärnan själv anropar den bara med heltal från filen, så inget fel når bokföringen idag.
- `kontrollera_z_serien` kraschar med `TypeError` om anroparen har ändrat ett Z-nummer till text i raderna. Raderna ska komma från `las_kassafil`, så det kräver ett programmeringsfel.
- En fil som heter `x\kassa_2025-01-02.csv` (bakåtsnedstreck är tillåtet i filnamn på Mac och Linux) läses som `kassa_2025-01-02.csv`. Datumkontrollen fungerar ändå.

#### H9. Stora kassaformat och långa meddelanden. Allvar: låg

Ett kassaformat med 20 000 betalsätt tog 2,6 sekunder att kontrollera, eftersom dubblettkontrollen jämför alla namn med alla. 200 000 skulle ta flera minuter. Det kräver en trasig eller manipulerad konfiguration. Ett belopp med 100 000 siffror gav ett felmeddelande på 200 179 tecken (samma som G7). Övrigt om storlek fungerade: fält över 131 072 tecken STOPPADES, ett kassaregister på 130 000 tecken GODKÄNDES, och 5 000 000 tomma rader efter posterna gick på en sekund.

#### H10. Generalitetstestet går att lura. Allvar: låg (testlucka)

**Vad jag körde:** i en kopia lade jag till rader i `las_kassa.py` och körde `test_karnan_ar_generell.py`.

| Tillägg i kärnan | Utfall |
|---|---|
| `MOMSSATSER = (12, 25)`, `KONTO_KASSA = 1910`, `GRANS_ORE = 500000` | Grönt (lurat) |
| `"forsalj" + "ning"`, `"FORSALJNING".lower()`, `"summa_" + "brutto"` | Grönt (lurat) |
| `"syntet testbutik ab"` (små bokstäver), organisationsnummer utan bindestreck, `"Nordea"` | Grönt (lurat) |
| Postnamnen i en fil `scripts/namn.json` (testet söker bara i `.py`-filer) | Grönt (lurat) |
| Kontrollfall: `POST = "forsaljning"` | Rött (rätt) |

Det mesta är G8 punkt 5–6, som medvetet inte åtgärdats (beslut 3 i granskning 2). SPEC avsnitt 2 säger att konto, momssats och belopp ska kontrolleras med ett test, och det gör testet fortfarande inte. Idag finns inga sådana tal i kärnan: de enda talen i `las_kassa.py` är 0, 1, 2, 16 (längd på id) och 100 (procent i momsformeln).

**Undantaget "belopp" är smalt.** Det gäller bara textsträngar som är exakt `belopp`, och ett test (`test_karnans_egna_ord_ar_verkligen_karnans_nycklar`) kräver att ordet är en av kärnans egna nycklar. Jag provade att missbruka det: i en kopia byggde jag in kolumnnamnet `"belopp"` i rubrikläsningen. Då blev `test_annat_kassaformat_laser_samma_data` och `test_annat_kassaformat_kor_samma_kontroller` röda, eftersom det andra formatet kallar kolumnen `Summa`. Undantaget kan alltså inte dölja att kassans kolumnnamn byggs in på riktigt.

#### H11. kassaformat.json ligger oskyddat. Observation inför spärrsteget

Samma som G9: `ladda_kassaformat` läser vilken sökväg som helst, och `foretag/` går att skriva i. Kassaformatet styr vilka poster som räknas som betalsätt, vilken post som är totalsumman och hur momsen avrundas. Jag provade omkastade kolumn- och postnamn: alla omkastningar som ger fel siffror STOPPADES (datum ↔ Z-nummer, sats ↔ belopp, kassaregister ↔ post, sats ↔ Z-nummer, försäljning ↔ moms, totalsumma ↔ kort). Kärnan vet däremot inte vilket betalsätt som är kontant, kort eller Swish, bara att de är betalsätt. Den kopplingen måste komma från skyddad konfiguration när matchningen mot banken byggs.

### Uppgift B: övrigt som provades och fungerade

| Prov | Utfall |
|---|---|
| Retur: alla belopp negativa. Allt noll. Moms med fel tecken | GODKÄND / GODKÄND / STOPPAD (e) |
| Negativ momssats, negativt Z-nummer, Z-nummer som text eller med fullbreddssiffror | STOPPAD: "ogiltigt heltal" |
| Z-nummer med inledande nollor (`0001001`), med blanksteg runt, och 0 | GODKÄND som 1001 / 1001 / 0. Två filer med `1001` och `01001` blir dubbletter i serien |
| Två kassaregister med blandade Z-nummer i oordning, samma Z-nummer i två register | GODKÄND (rätt, serien kontrolleras per register) |
| Samma fil två gånger, samma innehåll i två mappar, samma innehåll med CRLF | STOPPAD som dubblett ("samma fil är inläst två gånger" / "två olika filer har samma Z-nummer") |
| Filnamn med 2025-02-29, månad 00, stora bokstäver, blanksteg sist, utan `.csv`, med prefix, med fullbreddssiffror | STOPPAD (ogiltigt datum eller Z-kontroll a). 2024-02-29 (skottår) GODKÄND |
| Datum i filen skiljer sig från filnamnet | STOPPAD (Z-kontroll a) |
| Momssats `12`, `012`, ` 12`, `12` + hårt mellanslag | GODKÄND som 12. `12,0`, `12.00`, tom, `12 %`, `+12`, `1e1` STOPPAD. `12` och `012` för samma post blir dubblett |
| Momssats på betalsätt (`0`) / bara mellanslag | STOPPAD / GODKÄND (blanksteg tas bort) |
| Avrundning: 100,38 kr med 12 % ger exakt 10,755 kr. 10,75 och 10,76 godtas, 10,74 och 10,77 stoppas. Samma med minustecken. 4 242,00 kr ger exakt 454,50 kr: 454,49 och 454,51 stoppas | Rätt. Med 25 % kan momsen aldrig hamna på exakt ett halvt öre |
| Kassaformat: betalsätt som heter som försäljningen, krockar efter blanksteg, osynligt tecken, okänd nyckel, okänd posttyp, tuple i stället för lista, momsavrundning som lista, `ÅÅÅÅ` skrivet i NFD-form, punkt först | STOPPAD med tydligt fel |
| Postnamn som heter som en kolumn, postnamn med komma i (citerat i filen) | GODKÄND, läses rätt |
| Postnamn som bara skiljer i stor bokstav | Formatet godtas, filen stoppas ("okänd post") eftersom jämförelsen är exakt |
| Rubrikrad med citattecken eller blanksteg runt namnen | GODKÄND (rätt) |
| Rad med färre fält, datum med klockslag, fil med bara BOM, bara rubrikrad | STOPPAD |
| Kassaregister med en "instruktion" i texten | GODKÄND som vanlig text. Kärnan tolkar den inte |

### Uppgift C: kontroll mot reglerna

| Kontroll | Resultat |
|---|---|
| Företagsspecifika uppgifter i `scripts/` (utom `tests/`) | Inga företagsnamn, kassaregister, kolumnnamn, postnamn, konton, momssatser eller belopp. Talen är 0, 1, 2, 16, 100 (och 256 i `las_bank.py`, gränsen för tecken som prövas som styrtecken) |
| Flyttal | Inga. `momsen_i_brutto` räknar med heltal (`divmod`), se H8 om vad som händer om någon skickar in ett flyttal |
| Nätverksanrop | Inga (ingen `socket`, `urllib`, `http`, `requests`) |
| Körning av kommandon | Ingen (ingen `subprocess`, `os.system`, `eval`, `exec`) |
| Filåtkomst | Bara läsning (`open(sokvag, "rb")`) av sökvägar som anroparen anger. Inget skrivs. `kassaformat.json` läses från `foretag/`, som agenten kan skriva i (H11, G9) |
| Har SPEC.md ändrats sedan 7823bd8? | Nej. `git diff 7823bd8 HEAD -- SPEC.md CLAUDE.md` är tom |
| Slutrapportens påståenden för kassabygget | Stämmer. Commit a2d1540 ändrar bara `foretag/README.md`, `kassaformat.json`, `las_kassa.py`, `test_karnan_ar_generell.py` och `test_las_kassa.py`. `git diff f8d39ee a2d1540 -- scripts/las_bank.py SPEC.md testdata` är tom. Testdatan är oförändrad sedan commit f150652, före bankinläsningen |
| Undantaget "belopp" | Smalt, se H10 |
| Fast lista med kommandon (SPEC avsnitt 7) | Finns fortfarande inte i SPEC.md |

### Uppgift D: stickprov på mutationstesterna

I en kopia av projektet i den temporära mappen togs en kontroll i taget bort ur `las_kassa.py`, och hela testsviten kördes. Uppgiften bad om fem. Jag gjorde arton, eftersom varje körning tar under en sekund.

| Borttagen kontroll | Röda tester |
|---|---|
| Z-kontroll b: jämförelsen av kassaregister | `test_b_olika_kassaregister_i_samma_fil` |
| Serien: dubblettkontrollen | 2 (`test_serien_samma_fil_…`, `test_serien_tva_filer_…`) |
| Serien: datum som går bakåt | `test_serien_datum_som_gar_bakat_stoppas` |
| Serien: sorteringen | `test_serien_samma_fil_inlast_tva_ganger_ar_en_dubblett` |
| Momssats på betalsätt eller totalsumma | `test_trasig_z_fil_stoppas[sats_pa_betalsatt]` |
| Samma post två gånger | 2 (`dubbel_post`, `dubbel_totalsumma`) |
| Tomt kassaregister | `test_trasig_z_fil_stoppas` |
| Z-kontroll e: moms för en sats utan försäljning | `test_e_moms_for_en_sats_utan_forsaljning` |
| Z-kontroll a: radernas datum | 2 (`test_a_…`) |
| `las_kassafil` kontrollerar formatet igen | `test_las_kassafil_kontrollerar_kassaformatet_igen` |
| Dubbla postnamn i formatet | 3 (`test_trasigt_kassaformat_…`) |
| Styrtecken i Z-filen | `test_trasig_z_fil_stoppas` (styrtecken-fallen) |
| Serien: rader från olika filer i samma rapport | `test_serien_med_rader_fran_olika_filer_…` |
| Momsen: minustecknet | `test_momsen_i_brutto` |
| Z-kontroll c | 2 (`test_c_…`, `test_annat_kassaformat_kor_samma_kontroller`) |
| Kontrollen att totalsumman finns | `test_trasig_z_fil_stoppas` |
| Halvt öre: bara nedåt | `test_momsen_i_brutto` |
| Z-kontroll d jämför med försäljningen i stället för totalsumman | Inga röda. Det är rätt: Z-kontroll c har redan krävt att försäljningen är lika med totalsumman, så ändringen gör ingen skillnad (en så kallad likvärdig mutation, ingen testlucka) |

Alla verkliga borttagningar gav minst ett rött test. Ingen testlucka hittades i stickprovet.

### Testsviten

Kommando: `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests`

Resultat: **313 passed**, 0 misslyckade, både före och efter granskningen. `git status` visade bara den här filen som ändrad.

Kommandon som kördes i granskningen: Python i projektets `.venv` (provskript och pytest), `git log`, `git show`, `git diff`, `git status`, samt `ls`, `cat`, `head`, `tail`, `grep`, `sed`, `cut`, `wc`, `od`, `md5`, `mkdir`, `rm` och `/usr/bin/time` (de två sista bara i den temporära mappen). Provskripten skrev bara i den temporära mappen.

### Beslut som behövs från Hugo

1. **H1 och H2:** ska de rättas nu, innan nästa byggsteg? Rekommendation: ja. H1 är en liten ändring. H2 kräver ett beslut om att kassaformat.json ska innehålla en lista över företagets kassaregister.
2. **H4 (Öppen fråga):** får ett kassaregisters Z-nummer börja om, till exempel vid årsskifte? Ska verifieras med Skatteverket eller en redovisningskonsult.
3. **H10 / G8 punkt 5–6:** när ska generalitetstestet byggas ut så att det också fångar konton, momssatser och belopp? Senast när kontoplan och momssatser läggs till.
4. **H11 / G9:** var ska bankformat och kassaformat ligga så att agenten inte kan ändra dem? Hör till spärrsteget.

## Åtgärder efter granskning 3

Rättat 2026-10-25 i en egen session. Granskarens text ovan är inte ändrad. GRANSKNING.md med granskning 3 var redan committad (commit 419c849) när sessionen började, så det steget behövdes inte. Ett halvfärdigt, ocommittat försök från en tidigare session låg kvar i `las_kassa.py` och `kassaformat.json`. Det jämförde kassaregistrets namn exakt i stället för att normalisera det, så det togs bort och rättelserna gjordes om från commit 419c849. Alla tester ligger i `scripts/tests/test_las_kassa.py` (namn som börjar med `test_h1_`, `test_h2_`, `test_h4_`, `test_h6_`, och fallen `h2_…` i `test_trasigt_kassaformat_ger_kassafilfel`).

**Ord som används nedan.** Att **normalisera** ett namn betyder att skriva om det till en fast form innan det jämförs, så att två namn som ser likadana ut för en människa också räknas som samma av programmet.

**Så bevisades testerna.** De nya testerna kördes i en kopia av projektet utanför projektmappen, där `las_kassa.py` var den gamla versionen (commit 419c849, samma kod som granskades i a2d1540). Den gamla koden stoppar den nya nyckeln `kassaregister` i kassaformat.json som okänd, så ingen test alls kunde köras. För att se att varje test blir rött av rätt skäl fick den gamla koden i kopian två extra rader som släpper igenom nyckeln utan att kontrollera den. Inget annat ändrades. Resultat: 42 röda och 312 gröna.

- 39 nya tester blev röda av rätt skäl: 33 släpptes igenom (`DID NOT RAISE`: för långa Z-nummer, okända kassaregister, varianter av samma kassaregister, trasig kassalista, tom lista), 1 kraschade med `OverflowError` (lucka upp till 10²⁰), 2 gav granskarens missvisande luckmeddelande i stället för omstart, 1 saknade omstartstipset vid dubblett, och 2 hittade inte den nya konstanten eller funktionen (`ZNUMMER_HOGST_SIFFROR`, `normalisera_kassaregister`).
- 3 befintliga tester blev röda eftersom de nu frågar efter de nya fälten för luckan (`saknas_fran`, `saknas_till`) i stället för den gamla listan `saknade_znummer`.
- 2 nya skyddstester var gröna även i den gamla koden, som de ska: `test_h1_z_nummer_med_hogst_nio_siffror_godtas` och `test_h4_serien_som_fortsatter_over_arsskiftet_godkanns`.
- 1 nytt test kördes inte mot den gamla koden: `test_h1_storsta_tillatna_lucka_gar_fort` (lucka från 1 till 999 999 999). Den gamla koden skulle bygga en lista med nästan en miljard tal och fylla datorns minne, vilket är just felet. Att den gamla koden inte klarar stora luckor bevisas i stället av testet med 10²⁰.

Dessutom gjordes ett mutationstest på den nya koden: en ny kontroll i taget togs bort i en kopia, och hela sviten kördes. Alla gav minst ett rött test.

| Borttagen kontroll (i en kopia) | Röda tester |
|---|---|
| H1: gränsen för antal siffror i Z-numret | 4 |
| H2: kontrollen mot kassalistan | 15 |
| H2: hela normaliseringen | 14 |
| H2: normaliseringen utom stora och små bokstäver | 11 |
| H2: Unicode-normaliseringen (NFKC) | 4 |
| H2: seriekontrollens egen normalisering | 1 |
| H2: kontrollen av dubbla namn i kassalistan | 4 |
| H2: kravet att kassalistan är en lista med minst ett namn | 2 |
| H6: stoppet för tom lista | 1 |
| H4: kontrollen i datumordning (omstart) | 3 |
| H4: omstartstipset vid dubblett | 1 |

**Gränsen för Z-numret (H1).** Ett Z-nummer får ha högst 9 siffror, inledande nollor oräknade (konstanten `ZNUMMER_HOGST_SIFFROR` i `las_kassa.py`). Motivering: Z-numret ökar med ett per dagsavslut. Även en kassa med tio Z-rapporter om dagen i tusen år kommer bara upp i ungefär 3,7 miljoner (7 siffror), så 9 siffror (upp till 999 999 999) ger god marginal. Gränsen ligger i kärnan och inte i kassaformat.json, eftersom den gäller alla företag och bara fångar trasiga filer. Den är inget belopp, konto eller momssats.

| Nr | Åtgärdad | Test |
|---|---|---|
| H1 | Ja. Ett Z-nummer med fler än 9 siffror stoppas vid inläsningen med ett kort meddelande som säger hur många siffror det har. Seriekontrollen beskriver en lucka som ett intervall ("Z-rapporter saknas från nummer X till Y (N st)") och sparar bara första och sista saknade numret och antalet (`saknas_fran`, `saknas_till`, `antal_saknade`), aldrig en lista med alla saknade nummer | `test_h1_z_nummer_med_for_manga_siffror_stoppas` (10 siffror, 10¹², 10²⁰, 5 000 siffror), `test_h1_stor_lucka_beskrivs_som_intervall_med_kort_meddelande` (lucka till 10²⁰), `test_h1_storsta_tillatna_lucka_gar_fort`, `test_h1_granssen_for_z_numret_ar_nio_siffror` (skyddstest: `test_h1_z_nummer_med_hogst_nio_siffror_godtas`) |
| H2 | Ja. kassaformat.json har en obligatorisk lista `kassaregister`. En Z-fil från ett register som inte står i listan stoppas. Namnen jämförs efter normalisering (Unicode-normalisering NFKC, blanksteg och osynliga tecken bort, stora och små bokstäver räknas som samma). Raderna får registrets namn som det står i listan, och seriekontrollen jämför också normaliserade namn, så samma datum, Z-nummer och kassa i två filer stoppas som dubblett. Två namn i listan som blir samma efter normalisering stoppas | `test_h2_samma_z_rapport_med_annat_skrivsatt_kassaregister_ar_en_dubblett` (granskarens varianter: `tb-1`, osynligt mellanslag U+200B sist och inuti, U+202E som vänder text, samt mellanslag, hårt mellanslag, fullbreddstecken och "Ö" skrivet på två sätt), `test_h2_kassaregister_som_inte_finns_i_listan_stoppas` (granskarens `TB-1 X`, samt okänt register, extra bokstav, extra siffra, annan kassa), `test_h2_testbutikens_format_godtar_bara_testbutikens_kassa`, `test_h2_seriekontrollen_jamfor_normaliserade_namn`, `test_h2_normalisering_av_kassaregister`, 12 fall `h2_…` i `test_trasigt_kassaformat_ger_kassafilfel` |
| H3 | Nej (delvis som bieffekt) | Se nedan |
| H4 | Meddelandet: ja. Den öppna frågan: nej | Seriekontrollen prövar nu, före luckorna, att Z-numret aldrig går ner när datumet går fram. Gör det det står det att Z-numret går ner från X till Y, att det kan vara ett omstartat Z-nummer, och att det är en öppen fråga (H4) som ska kontrolleras med Skatteverket eller en redovisningskonsult. Serien stoppas fortfarande. Börjar numret om och upprepar ett Z-nummer som redan finns, med ett annat datum, får dubblettmeddelandet samma tips. Test: `test_h4_z_nummer_som_borjar_om_vid_arsskifte_ger_tydligt_meddelande`, `test_h4_z_nummer_som_borjar_om_mitt_i_ger_tydligt_meddelande`, `test_h4_z_nummer_som_borjar_om_och_upprepas_ger_tydligt_meddelande` (skyddstest: `test_h4_serien_som_fortsatter_over_arsskiftet_godkanns`) |
| H5 | Nej, medvetet | Se nedan |
| H6 | Ja. `kontrollera_z_serien([])` stoppas med `KassafilFel`: "det finns inga Z-rapporter att kontrollera" | `test_h6_tom_lista_stoppas` |
| H7 | Nej, medvetet | Se nedan |
| H8 | Nej, medvetet | Se nedan |
| H9 | Nej, medvetet | Se nedan |
| H10 | Nej, medvetet | Se nedan |
| H11 | Nej, medvetet | Se nedan |

**Varför resten inte är åtgärdat nu.** Uppgiften var att rätta H1, H2 och de låga fynden i samma kod (H4:s meddelande och H6). Övriga fynd kräver mer än en rättelse i den här koden, eller ett beslut först:

- **H2, granskarens andra förslag** (stoppa osynliga tecken i Z-filens fält): inte gjort. Uppgiften valde normalisering i stället. Kassaregistret var det enda fältet med fri text: postnamnen måste stämma exakt med kassaformatet, och datum, Z-nummer, momssats och belopp har fasta mönster. Ett osynligt tecken i registrets namn tas nu bort vid jämförelsen.
- **H3** (blandad teckenkodning): ett felkodat kassaregister som `KASSA-Ã–` finns inte i kassalistan och stoppas därför nu (provat för hand, inget eget test). Meddelandet nämner däremot inte teckenkodningen, och en fil med UTF-8-BOM som inte är giltig UTF-8 stoppas fortfarande med fel förklaring. Det kräver samma ändring som F8 i `las_bank.py` och ingick inte i uppgiften.
- **H4, den öppna frågan**: om ett Z-nummer får börja om ska verifieras med Skatteverket eller en redovisningskonsult. Om det är tillåtet måste kärnan kunna ta emot en ny serie, vilket är en större ändring.
- **H5** (filnamnet rymmer bara datum): kräver att filnamnsmönstret också kan innehålla kassaregistret, och hör till Ö5 (vilka kassasystem som ska stödjas).
- **H7** (vilken momssats som helst godtas): hör till K5 och K10, som inte är byggda.
- **H8** (hjälpfunktioner): `momsen_i_brutto` utan typkontroll och Z-nummer som text i rader som inte kommer från `las_kassafil` kräver programmeringsfel. Ingick inte i uppgiften.
- **H9** (stora kassaformat och långa meddelanden): samma beslut om storleksgränser som G7.
- **H10** (generalitetstestet går att lura): granskning 2:s beslut 3. Generalitetstestet letar nu däremot också efter kassaregistrens namn från kassaformat.json i kärnan, eftersom de är nya företagsuppgifter (`test_karnan_innehaller_inga_namn_fran_kassaformaten`).
- **H11** (kassaformat.json ligger oskyddat): hör till spärrsteget. Kassalistan ligger i samma oskyddade fil.

**Nya iakttagelser under arbetet (inte rättade).**

- **Datum långt isär ger ett jättelångt meddelande.** Två Z-rapporter från samma kassa med datumen 0001-01-01 och 9999-12-31 och Z-nummer 1 och 3 ger en lucka där alla 3,65 miljoner dagar däremellan räknas upp. Meddelandet blev 43,8 miljoner tecken och kontrollen tog 1,6 sekunder (provat för hand). Inget släpps igenom och minnet tar inte slut, eftersom antalet dagar begränsas av kalendern, men meddelandet går inte att läsa. Det kräver en trasig fil. Förslag: beskriv dagarna som ett intervall när de är många, på samma sätt som Z-numren.
- **En kassa i listan utan Z-rapporter syns inte.** Seriekontrollen får inte kassaformatet, så den vet inte vilka kassor som borde ha rapporter. En kassa som står i listan men saknar alla rapporter för perioden upptäcks inte. Hör ihop med H6 och K10.

**Övrigt som ändrats.** Testerna för de små Z-filerna använder påhittade kassaregister (`K-1`, `K-2`, `K-A`, `K-B`, `KASSA-Ö`). De läggs till i en kopia av testbutikens kassaformat inne i testfilen, så att testbutikens `kassaformat.json` bara innehåller testbutikens egen kassa (`TB-KASSA-1`). Testdatan läses alltid med testbutikens oförändrade format. Tre befintliga tester frågar nu efter `saknas_fran` och `saknas_till` i stället för `saknade_znummer`, och ett befintligt test har fått det nya luckmeddelandet. `foretag/README.md` och beskrivningen överst i `las_kassa.py` beskriver kassalistan och de nya reglerna. SPEC.md och `las_bank.py` är inte ändrade.

Testsviten efter rättelserna: 355 passed, 0 misslyckade.

**Senare samma dag (två commits):** (A) seriekontrollen beskriver dagarna utan Z-rapport som ett intervall ("från DATUM till DATUM (N dagar)"), så datum långt isär ger ett kort meddelande (`test_datum_langt_isar_ger_kort_meddelande`, rött på gamla koden med ett meddelande på 43 824 888 tecken); (B) inläsningskoden som bank och kassa delade ligger nu i `scripts/inlasning_skydd.py`, med samma felmeddelanden och felklasser som förut (`test_inlasning_skydd.py`).

## Granskning 4: inläsningslagret (bank, kassa och gemensamma skydd)

| | |
|---|---|
| Datum | 2026-10-25 |
| Granskad version | commit 61a5946 ("Gemensamma inläsningsskydd i inlasning_skydd.py") |
| Granskare | Oberoende session som inte sett inläsningslagret byggas. Ingen kod eller befintlig fil har ändrats, bara det här avsnittet har lagts till |
| Underlag | CLAUDE.md, SPEC.md (avsnitt 2, 5, 6, 7, 8), foretag/README.md, foretag/syntet-testbutik/bankformat.json och kassaformat.json, scripts/belopp.py, scripts/inlasning_skydd.py, scripts/las_bank.py, scripts/las_kassa.py, alla filer i scripts/tests/, testdata/README.md, facit.json, tidigare granskningar och åtgärdstabeller ovan |

### Så gick granskningen till

Allt provande gjordes i en temporär mapp utanför projektet. Där lades tre kopior av koden: commit f3ecc76 (före flytten, som uppgiften angav), commit 6adbf24 (direkt före flytten) och commit 61a5946 (nu). Egna provskript skapade filer och format, körde dem mot kopiorna och skrev ut utfallet: **STOPPAD** (tydligt `BankfilFel`/`KassafilFel` eller underklass), **GODKÄND** (raderna släpptes igenom) eller **KRASCH** (annat, oförklarat fel). Mutationstesterna gjordes i ytterligare en kopia. Den temporära mappen är borttagen efteråt.

Ord som används nedan: en **genväg** är en funktion som läser en fil men hoppar över en kontroll. En **byggsten** är en liten funktion i `inlasning_skydd.py` som gör en sak, till exempel avkodar text eller läser CSV-rader. **Riktningstecken** (bidi) är osynliga tecken som får text att visas baklänges eller i annan ordning än den är lagrad.

Allvar: **hög** = kan ge fel bokföring, **medel** = onödig krasch eller otydligt fel, **låg** = kosmetiskt.

Obs: mellan f3ecc76 och flytten ligger commit 6adbf24, som medvetet ändrade seriekontrollens meddelande om dagar utan Z-rapport. För att inte blanda ihop den avsiktliga ändringen med flytten jämfördes nya koden mot båda.

### Uppgift A: har flytten ändrat beteendet?

Nej. Flytten har inte ändrat något beteende som jag kunde hitta.

**Vad jag körde:** 6 181 provfall, körda mot alla tre kopiorna. För varje fall jämfördes felklassen (med modulnamn), hela felmeddelandet och felets extra uppgifter (till exempel `radnr`, `kontroll`, `typ`, `saknas_fran`). När filen godkändes jämfördes i stället hela resultatet (alla rader och alla fält).

| Sorts fall | Antal | Hur de skapades |
|---|---|---|
| Bankfiler (`las_bankfil`) | 2 228 | Giltiga filer med 1–8 rader, komma, semikolon, tabb eller lodstreck, med och utan förrader och extra kolumn. 80 % fick 1–3 slumpade skador: styrtecken, NUL, U+2028, U+FEFF, U+200B, U+202E, U+2066, citattecken, avgränsare, radslut av olika slag (CR, CRLF, `\x0c`, `\x85`), borttagna, dubblerade och omkastade rader, avklippt fil, ändrade siffror, fält på 200 000 tecken, UTF-16, Windows-1252, trasiga byte. Ibland fel saldo, eller saldo av fel typ (flyttal, `True`, `None`, text). Ibland ett skadat bankformat som skickas direkt. Dessutom saknad fil, mapp, oläsbar fil (rättigheter 000), tom fil, bara BOM och bara rubrikrad |
| Z-filer (`las_kassafil`) | 2 131 | Giltiga Z-rapporter med rätt moms, betalsätt och totalsumma, omkastade kolumner och rader, olika skrivsätt för kassan. Samma slumpade skador som bankfilerna. Dessutom handgjorda fall: bara rubrikrad, tomt kassaregister, Z-nummer med 10, 13 och 5 000 siffror, dubbel post, dubbel kolumn, fält med radbrytning, fullbreddstecken och fel datum i filnamnet |
| Bankformat (`ladda_bankformat`) | 600 | Skadade värden och nycklar, dubbla nycklar, 1 000–100 000 nästlade parenteser, avklippt JSON, `NaN`, NFD-form ("ö" som "o" plus prickar), fel teckenkodning |
| Kassaformat (`ladda_kassaformat`) | 572 | Samma sorts skador, samt krockande kassaregister (`K-1`/`k-1`, osynligt tecken, fullbredd), filnamnsmönster med mapp, punkt först och osynligt tecken |
| Z-serier (`kontrollera_z_serien`) | 650 | 0–5 giltiga Z-filer med luckor, dubbletter, omstarter, samma fil två gånger och datum från år 1 till år 9999 |

**Vad som hände:**

| Jämförelse | Fall med skillnad | Förklaring |
|---|---|---|
| 6adbf24 (direkt före flytten) mot nu | **0 av 6 181** | Felklass, meddelande, extra uppgifter och godkända rader är identiska i alla fall |
| f3ecc76 mot nu | 385 av 6 181, alla i seriekontrollen | Alla kommer från 6adbf24, inte från flytten: 330 fall har bara nya namn på felets uppgifter (`dagar_fran`, `dagar_till`, `antal_dagar` i stället för listan `dagar_utan_rapport`), 48 fall har det nya meddelandet om dagar som intervall, och 7 fall gav `OverflowError` i f3ecc76 men `ZSerieFel` nu (två rapporter samma dag år 9999) |

Proverna träffade 255 olika sorters felmeddelanden, bland dem alla meddelanden som flyttades till `inlasning_skydd.py`. Även de sällsynta grenarna provades med handgjorda fall: för långt fält, oläsbar fil, mapp i stället för fil, NUL före rubrikraden, radbrytning inuti fält och dubbel kolumn på rubrikraden.

**Det enda som har ändrats utöver beteendet** är var namnen finns. Hjälpfunktionerna som förut hette till exempel `las_bank._avkoda` och `las_kassa._csv_fel` finns nu bara i `inlasning_skydd.py` (utan understreck), och konstanten `TILLATNA_AVGRANSARE` kan inte längre hämtas som `las_bank.TILLATNA_AVGRANSARE`. Ingen fil i projektet använde de gamla namnen, så inget har gått sönder. Se I1 om vad det betyder att byggstenarna nu är offentliga.

### Sammanfattning av nya fynd

Inga fynd med allvar hög. Ingen skadad fil eller skadat format släpptes igenom av `las_bankfil` eller `las_kassafil` med fel siffror.

| Nr | Fynd | Allvar |
|---|---|---|
| I1 | Kassans genväg `_tolka_kassarader` (hoppar över Z-kontroll a–e) och de offentliga byggstenarna i `inlasning_skydd.py` saknar skyddstest. En ny kärnfil kan använda dem utan att något test slår larm | Medel (risk inför nästa byggsteg) |
| I2 | Seriekontrollen körs bara om anroparen kommer ihåg det. `summa_per_momssats` räknar samma Z-rapport två gånger utan varning | Medel (risk inför nästa byggsteg) |
| I3 | Osynliga tecken, bland annat riktningstecken, släpps igenom i bank- och Z-filernas textfält | Låg (observation inför rapportsteget och K17) |
| I4 | En sökväg av fel typ ger Python-fel i stället för `BankfilFel`/`KassafilFel`. Ett heltal eller `True` som sökväg stänger programmets utdata | Låg (kräver programmeringsfel, fanns före flytten) |
| I5 | Byggstenarna anropade direkt med ovanliga indata ger Python-fel eller konstiga svar | Låg (kräver programmeringsfel) |
| I6 | Luckmeddelandet kan säga "Den saknade rapporten är från 9999-12-31 eller 9999-12-31" och "rapporten" i ental när flera saknas | Låg (kosmetiskt, fanns före flytten) |
| I7 | Slutrapportens "355 tester före" gäller f3ecc76. Direkt före flytten var det 358 | Låg (kosmetiskt) |

### Fynd i detalj

#### I1. Genvägar förbi kontrollerna utan skyddstest. Allvar: medel

**Vad jag körde:** (a) en bankfil där saldot efter rad 1 är fel, och en Z-fil där försäljningen (112 kr) inte summerar till totalsumman (1 kr). Varje fil lästes både på vanligt sätt och via genvägarna. (b) I en kopia av projektet lade jag till en ny kärnfil, `scripts/rapport.py`, med en enda rad i taget, och körde hela testsviten.

**Vad som hände (a):**

| Anrop | Bankfilen | Z-filen |
|---|---|---|
| `las_bankfil` / `las_kassafil` | STOPPAD (`K1Fel`) | STOPPAD (`ZKontrollFel`, kontroll c) |
| `las_bank._tolka_rader` | GODKÄND, saldo 999,00 kr | – |
| `las_kassa._tolka_kassarader` | – | GODKÄND, 4 rader, och `summa_per_momssats` ger 112 kr i försäljning |
| `las_fil` + `avkoda` + `csv_rader` ur `inlasning_skydd` | GODKÄND som råa fält | GODKÄND som råa fält |

**Vad som hände (b):**

| Rad i den nya filen `scripts/rapport.py` | Testsviten |
|---|---|
| `from las_bank import _tolka_rader` | 1 röd (F11-testet, rätt) |
| `from las_kassa import _tolka_kassarader` | **496 gröna** |
| `from inlasning_skydd import las_fil, avkoda, csv_rader` | **496 gröna** |
| `from las_bank import csv_rader, las_fil, avkoda` (byggstenarna går också att hämta via `las_bank` och `las_kassa`) | **496 gröna** |

**Varför:** F11-testet söker bara efter texten `_tolka_rader`. `_tolka_kassarader` innehåller inte den texten, och det finns inget motsvarande test för kassan. Byggstenarna är gjorda för att anropas i rätt ordning (`las_fil`, `avkoda`, NUL-kontroll, `inga_otillatna_tecken`, rubrikrad, `csv_rader`), men ingenting tvingar fram ordningen. `csv_rader` ensam godtar till exempel tecknet `\x0c` (sidbrytning) inuti ett fält, vilket är just G1-felet, eftersom styrteckenkontrollen ligger i en annan byggsten.

**Varför allvaret är medel och inte hög:** ingen kod i projektet använder genvägarna i dag, och ingen bokföring byggs ännu. Men konsekvensen om nästa byggsteg (matchning, kontering, rapport) råkar använda dem vore hög: Z-rapporter som inte går ihop, eller en bankfil utan K1, skulle gå vidare. Granskningen ser ingen sådan kod i dag.

**Vad som borde hända:** ett test som stoppar alla filer i `scripts/` utom `las_bank.py`, `las_kassa.py` och `tests/` från att använda `_tolka_kassarader` och från att importera `inlasning_skydd`. Testet bör också klara alias och `getattr` (G8 punkt 5). Ett alternativ är att samla byggstenarna i en enda funktion som alltid kör alla skydd i rätt ordning.

#### I2. Seriekontrollen tvingas inte fram. Allvar: medel

**Vad jag körde:** samma giltiga Z-rapport (112 kr i försäljning) i två mappar, den ena med kassan skriven `tb-kassa-1`. Båda lästes med `las_kassafil`, och sedan anropades `summa_per_momssats` direkt.

**Vad som hände:** båda filerna GODKÄNDES (rätt, var för sig är de felfria). `summa_per_momssats` gav **224 kr** i försäljning och 24 kr i moms, utan varning. `kontrollera_z_serien` på samma två rapporter STOPPADE dem som dubblett (rätt), men den körs bara om anroparen kommer ihåg det.

**Varför det spelar roll:** seriekontrollen är i dag det enda skyddet mot att samma Z-rapport räknas två gånger (H2). `summa_per_momssats` tar emot vilka rader som helst, även rader från `_tolka_kassarader` som inte gått igenom Z-kontroll a–e (se I1). Allvaret är medel av samma skäl som I1: inget anropar funktionen i dag, men konsekvensen vore dubbel försäljning.

**Vad som borde hända:** att summera försäljningen ska bara gå att göra efter en godkänd seriekontroll, till exempel genom att `summa_per_momssats` kör `kontrollera_z_serien` själv, eller genom en enda funktion som läser en hel period. Bör bestämmas innan K10 och rapporten byggs.

#### I3. Osynliga tecken och riktningstecken i textfälten. Allvar: låg (observation)

**Vad jag körde:** en bankfil med beskrivningen U+202E + `ET-VEL` och referensen `R` + U+200B + `1`. Även `inga_otillatna_tecken` direkt med U+FEFF mitt i texten, U+200B, U+202E, U+2066 och U+00AD (mjukt bindestreck).

**Vad som hände:** GODKÄND. Beskrivningen lagras som U+202E + `ET-VEL`, men visas för en människa som `LEV-TE`. Skyddet mot ovanliga tecken stoppar bara styrtecken (kategori Cc) och U+2028/U+2029, inte osynliga formattecken (kategori Cf).

**Varför det spelar roll:** när rapporten byggs ser godkännaren beskrivningen och referensen. En text som visas som en känd motpart men är lagrad som något annat kan vilseleda. Det lindras av att regelboken troligen jämför exakt, så att texten blir "ny motpart" (nivå C, rad för rad). Granskarens förslag i H2 (stoppa Cf i Z-filens fält) gjordes medvetet inte, och för bankfilen har frågan inte tagits upp tidigare. Hör ihop med K17 (text i underlag som försöker styra agenten).

**Vad som borde hända:** bestäm före rapportsteget om Cf-tecken ska stoppa filen, tas bort, eller visas synligt (till exempel som `<U+202E>`) i rapporten.

#### I4. Sökväg av fel typ. Allvar: låg

**Vad jag körde:** `las_fil`, `ladda_json` och `las_bankfil` med sökvägen `None`, en lista, ett flyttal, en text med NUL-tecken, en bytes-sökväg, `pathlib.Path`, tom text, 5 000 tecken och `True`.

**Vad som hände:** `None`, lista och flyttal gav `TypeError`, och NUL i sökvägen gav `ValueError`, i stället för `BankfilFel`/`KassafilFel`. Bytes, `Path`, tom text och lång sökväg fungerade eller stoppades rätt. **`True` (eller ett heltal) tolkas av Python som ett filnummer:** `las_bankfil(True, …)` försökte läsa från programmets egen utdata (filnummer 1), stoppades med "filen True går inte att läsa (Bad file descriptor)", och **stängde sedan programmets utdata**. Allt programmet skrev efteråt gick förlorat och processen avslutades med fel.

**Varför allvaret är lågt:** det kräver ett programmeringsfel, eftersom sökvägar från en mapp alltid är text. Beteendet är detsamma som före flytten. **Förslag:** kontrollera att sökvägen är text eller `Path` innan filen öppnas.

#### I5. Byggstenarna med ovanliga indata. Allvar: låg

Funktionerna i `inlasning_skydd.py` anropades direkt. Inget av detta kan nås från en bank- eller Z-fil eller ett JSON-format, bara från kod.

| Anrop | Utfall |
|---|---|
| `avkoda` med text, `None`, `memoryview`, heltal | KRASCH (`TypeError`/`AttributeError`). `bytearray`, tom fil, bara BOM och 10 MB fungerade |
| `inga_otillatna_tecken` med bytes, `None`, lista | KRASCH (`TypeError`). 50 MB ren text gick bra |
| `csv_rader` med avgränsaren tom, `None` eller två tecken | KRASCH (`TypeError` från csv-läsaren) |
| `csv_rader` med `textrader` som en text i stället för en lista, och 1 kolumn | GODKÄND, varje **tecken** blir en egen rad |
| `csv_rader` med `filsort=None` eller en felklass som inte är ett fel | KRASCH (`AttributeError`/`TypeError`). Med `StopIteration` som felklass blir det `RuntimeError`, alltså ingen tyst hoppad kontroll |
| `rubrikens_falt` med tom kolumnlista | Godtar vilken rad som helst som rubrikrad |
| `kontrollera_nycklar` med en nyckel som är ett tal | KRASCH (`TypeError` när okända nycklar sorteras) |
| `kontrollera_namn` med bytes | STOPPAD, men med det missvisande "får inte vara tomt" |
| `kontrollera_namn` med U+2800 (blank blindskrift) eller U+115F (osynlig koreansk utfyllnad) | Godtas som namn. Ofarligt, eftersom namnet måste stå exakt så i filen |
| `kontrollera_avgransare` med en text-underklass som säger sig vara lika med allt | Godtar `x` som avgränsare |
| `tolka_datum`/`tolka_ore` med `None`, tal eller bytes | KRASCH (`TypeError`) |
| `nul_fel("x", …)` | Meddelandet "rad x i filen" |
| bankformat.json och kassaformat.json med en avgränsare eller momsavrundning nästlad 900–999 nivåer (för att se om felmeddelandet kraschar när det skriver ut värdet) | STOPPAD i alla fall, ingen krasch |

**Vad som borde hända:** inget av detta släpper igenom en felaktig rad från en fil. Om byggstenarna ska användas av fler inläsningsmoduler (kvitton, fakturor) bör de antingen kontrollera typerna eller göras interna, se I1.

#### I6. Luckmeddelande med samma datum två gånger. Allvar: låg (kosmetiskt)

Två Z-rapporter med Z-nummer 37 och 100 039, båda daterade 9999-12-31, gav: "Z-rapporter saknas från nummer 38 till 100038 (100001 st) … Den saknade rapporten är från 9999-12-31 eller 9999-12-31." Samma sak med två rapporter samma dag och vilka nummer som helst. Meddelandet skriver samma datum två gånger och "rapporten" i ental fast flera saknas. Serien stoppas rätt. Fanns före flytten.

#### I7. Antalet tester före flytten. Allvar: låg (kosmetiskt)

Se uppgift D. Påståendet "355 före, 496 efter" stämmer om det gäller båda commitarna tillsammans (6adbf24 och 61a5946). Direkt före flytten var det 358.

### Uppgift B: finns det en väg förbi kontrollerna?

Ja, men bara genom att anropa funktioner direkt från kod. Ingen fil eller konfiguration kan få `las_bankfil` eller `las_kassafil` att hoppa över en kontroll.

| Kontroll | Hoppas över av | Skyddstest som slår larm |
|---|---|---|
| K1 (saldokedjan och utgående saldo) | `las_bank._tolka_rader` (känd, F11). Byggstenarna i `inlasning_skydd` | Bara för `_tolka_rader`, och det går att lura (G8 punkt 5) |
| Z-kontroll a–e | `las_kassa._tolka_kassarader`. Byggstenarna | **Inget** (I1) |
| Seriekontrollen | Allt som läser Z-filer, inklusive `las_kassafil`. `summa_per_momssats` kräver den inte | **Inget** (I2) |
| Styrtecken och NUL | `csv_rader` och `rubrikens_falt` direkt | Inget (I1) |

Övrigt som provades och fungerade:

- En felklass (`fel`) i en `Filsort` kan inte få en kontroll att tyst hoppas över. `raise` kastar alltid något, och `StopIteration` inuti `csv_rader` blir `RuntimeError`.
- `BANKFIL` och `KASSAFIL` är oföränderliga (`NamedTuple`). Konstanterna i `inlasning_skydd.py` (till exempel `OTILLATNA_TECKEN`) går däremot att byta ut från annan kod i samma körning, och ett enda byte slår då ut skyddet för både bank och kassa. Det kräver medvetet skriven kod och går inte att stänga helt i Python. Samma sak gäller `csv.field_size_limit`, som gäller hela programmet.
- Djupt nästlad JSON nästan upp till Pythons gräns (900–999 nivåer) där JSON-läsaren klarar sig men felmeddelandet skriver ut värdet: ingen krasch.

### Uppgift C: dolda tecken i hela projektet

**Vad jag körde:** ett skript som läste alla 138 filer under `agent/` utom `.git/` och `.venv/` (kod, tester, konfiguration, testdata, dokument, GRANSKNING.md, `.gitignore`, `.pytest_cache`), filnamnen och alla commitmeddelanden. Det letade efter styrtecken (kategori Cc utom tabb och radslut), formattecken (Cf, bland dem nollbreddstecken, riktningstecken U+202A–U+202E och U+2066–U+2069, U+FEFF och mjukt bindestreck), U+2028, U+2029, privata och otilldelade tecken, andra blanksteg än vanligt mellanslag, utfyllnadstecken (U+115F, U+1160, U+3164, U+FFA0, U+2800), variantväljare och CR (Windows-radslut). Dessutom bokstäver från andra skriftsystem än latin i `.py`-filer.

**Vad som hände:**

| Fil och rad | Tecken | Avsiktligt? |
|---|---|---|
| scripts/belopp.py:14 | U+00A0 (hårt mellanslag) och U+202F (smalt hårt mellanslag) | Ja. Tillåtna tusentalsavgränsare, förklarade i kommentaren ovanför |
| scripts/tests/test_belopp.py:48 | U+00A0 | Ja. Teststräng `"1 234,56"`, kommentaren säger "hårt mellanslag" |
| scripts/tests/test_belopp.py:49 | U+202F | Ja. Teststräng, kommentaren säger "smalt hårt mellanslag" |
| scripts/tests/test_las_kassa.py:416 | U+2028 (ovanlig radbrytning) | Ja. Teststräng `"K` + U+2028 + `-1"`, testet kräver meddelandet "innehåller tecknet U+2028" |
| scripts/tests/test_las_kassa.py:623 | U+200B (osynligt mellanslag) | Ja. Kolumnnamnet `"Moms` + U+200B + `"`, testet kräver "innehåller tecknet U+200B" |
| scripts/tests/test_las_kassa.py:645 | U+200B | Ja. Filnamnsmönster med osynligt tecken, testet kräver "styrtecken eller ett osynligt tecken" |
| scripts/tests/test_las_kassa.py:615 | Fullbreddsbokstäver (`ＴＢ－ＫＡＳＳＡ－１`) | Ja. H2-testet för kassaregister i fullbredd. Synliga, inte dolda |

Inga riktningstecken, ingen U+FEFF (inte ens i början av en fil), ingen U+2029, inga styrtecken utom tabb och `\n`, inga CR-radslut och inga dolda tecken i filnamn eller commitmeddelanden. De enda filerna som inte är UTF-8 är tre `.DS_Store` (macOS egna mappinställningar), som inte är incheckade (`.gitignore`).

**Kosmetiskt:** de tre osynliga tecknen i test_las_kassa.py är inskrivna som själva tecknet, medan testerna annars skriver sådana tecken som `\u200b` och `\u2028` (21 ställen). Om en textredigerare skulle ta bort tecknen blir testerna röda (de kräver tecknets kod i meddelandet), så felet skulle märkas. Förslag: skriv dem som `\u2028` och `\u200b` så att de syns.

### Uppgift D: kontroll mot reglerna

| Kontroll | Resultat |
|---|---|
| Företagsspecifika uppgifter i `scripts/` (utom `tests/`) | Inga företagsnamn, banknamn, kassaregister, kolumnnamn, postnamn, konton, momssatser eller belopp. `inlasning_skydd.py` nämner varken bank, kassa, Z-rapport, kvitto eller faktura. Talen i koden är 0, 1, 2, 8 (UTF-8), 16 (UTF-16 och längd på id), 100 (procent), 0x100, 1252 (Windows-1252), 2028/2029 (tecknens koder), 9 (`ZNUMMER_HOGST_SIFFROR`) och exempel i kommentarer |
| Flyttal | Inga. Ingen division med `/` i koden (bara `divmod`), inga decimaltal. "float" står bara i en kommentar som förbjuder det |
| Nätverksanrop | Inga (ingen `socket`, `urllib`, `http`, `requests`). Importerna är bara `csv`, `datetime`, `hashlib`, `json`, `re`, `unicodedata`, `typing` och projektets egna moduler |
| Körning av kommandon | Ingen (ingen `subprocess`, `os.system`, `popen`, `eval`, `exec`, `__import__`, `importlib`, `pickle`) |
| Läsning från mappar agenten kan skriva i | Bara läsning (`open(sokvag, "rb")` på två ställen, båda i `inlasning_skydd.py`) av sökvägar som anroparen anger. Inget skrivs. Flytten har inte lagt till någon ny läsning. Bank- och kassaformatet läses fortfarande från `foretag/`, som agenten kan skriva i (G9, H11, spärrsteget) |
| Har SPEC.md ändrats sedan 7823bd8? | Nej. `git diff 7823bd8 HEAD -- SPEC.md CLAUDE.md` är tom |
| 355 tester före, 496 efter | Egen körning i kopiorna: **355** vid f3ecc76, **358** vid 6adbf24 (direkt före flytten, 3 nya tester för dagar som intervall) och **496** nu. Ökningen vid flytten är 138: 136 i den nya `test_inlasning_skydd.py` och 2 i `test_karnan_ar_generell.py` (från 8 till 10) |
| Oförändrade bank- och kassatester | Stämmer för flytten: `git diff 6adbf24 61a5946 -- scripts/tests/test_las_bank.py scripts/tests/test_las_kassa.py` är tom, och antalet tester i dem är 104 och 164 både före och efter. `test_las_kassa.py` ändrades i 6adbf24, vilket hör till den commiten |
| Flyttcommitens påstående om 20 040 filer med samma felklass och meddelande | Inte omkört (filerna finns inte kvar), men min egen jämförelse med 6 181 fall ger samma slutsats |
| Fast lista med kommandon (SPEC avsnitt 7) | Finns fortfarande inte i SPEC.md |

### Uppgift E: stickprov på mutationstesterna

I en kopia av projektet togs en kontroll i taget bort, och hela testsviten kördes. Uppgiften bad om tio. Jag gjorde tjugoen, eftersom varje körning tar en sekund.

| Fil | Borttagen kontroll | Röda tester (exempel) |
|---|---|---|
| inlasning_skydd.py | UTF-16 stoppas | 10 (`test_avkoda_stoppar_utf16`) |
| inlasning_skydd.py | Styrtecken i filen (G1) | 28 (`test_inga_otillatna_tecken_stoppar`) |
| inlasning_skydd.py | Radbrytning inuti fält (F1) | 8 (`test_csv_rader_radbrytning_inuti_falt`, `test_f1_…`) |
| inlasning_skydd.py | Antal fält mot rubrikraden | 6 (`test_csv_rader_fel_antal_falt`) |
| inlasning_skydd.py | Strikt csv-läsning (F9) | 4 (`test_csv_rader_lases_strikt`, `test_f9_…`) |
| inlasning_skydd.py | Styrtecken och osynliga tecken i namn (G2) | 19 (`test_kontrollera_namn_stoppar_trasiga_namn`) |
| inlasning_skydd.py | Dubbla JSON-nycklar | 6 (`test_ladda_json_trasig_fil`) |
| inlasning_skydd.py | Datum som inte finns (2025-02-30) | 5 (`test_tolka_datum`) |
| inlasning_skydd.py | Fasta listan med avgränsare | 21 (`test_kontrollera_avgransare_stoppar`) |
| inlasning_skydd.py | Översättningen av "för långt fält" | 6 (`test_csv_fel`, `test_csv_rader_for_langt_falt`) |
| las_bank.py | K1: utgående saldo (F2) | 1 (`test_f2_avklippt_fil_stoppas`) |
| las_bank.py | K1: saldokedjan rad för rad | 3 (`test_k1_godkanner_korrekt_kedja_…`) |
| las_bank.py | Radnummer 1, 2, 3 (F4) | 5 (`test_f4_…`) |
| las_bank.py | `las_bankfil` kontrollerar formatet igen | 1 (`test_f5_las_bankfil_kontrollerar_bankformatet_igen`) |
| las_bank.py | NUL-kontrollen | 2 (`test_f3_nul_tecken_…`) |
| las_kassa.py | Z-kontroll d | 3 (`test_d_…`) |
| las_kassa.py | Z-kontroll e | 5 (`test_e_…`) |
| las_kassa.py | Okänt kassaregister (H2) | 6 (`test_h2_kassaregister_som_inte_finns_i_listan_stoppas`) |
| las_kassa.py | Seriekontrollen: luckor | 9 (`test_serien_lucka_…`) |
| las_kassa.py | Gränsen för Z-numrets siffror (H1) | 4 (`test_h1_…`) |
| las_kassa.py | NUL-kontrollen | 1 (`test_trasig_z_fil_stoppas[nul_tecken]`) |

Alla borttagningar gav minst ett rött test. Ingen testlucka hittades i stickprovet. Testluckorna i I1 och I2 gäller inte borttagna kontroller, utan att det saknas test som stoppar ny kod från att gå förbi dem.

### Testsviten

Kommando: `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests`

Resultat: **496 passed**, 0 misslyckade, både före och efter granskningen. `git status` visade bara den här filen som ändrad.

Kommandon som kördes i granskningen: Python i projektets `.venv` (provskript och pytest), `git log`, `git show`, `git diff`, `git status`, `git archive`, `git ls-files`, `tar`, samt `ls`, `cat`, `head`, `tail`, `grep`, `sed`, `diff`, `od`, `awk`, `cut`, `sort`, `uniq`, `wc`, `printf`, `cp`, `mkdir` och `rm` (de tre sista bara i den temporära mappen). Provskripten skrev bara i den temporära mappen.

### Beslut som behövs från Hugo

1. **I1 och I2:** ska skyddstesterna byggas ut nu, så att ingen ny kärnfil kan använda `_tolka_kassarader` eller byggstenarna i `inlasning_skydd.py`, och ska summering av försäljning bara gå efter en godkänd seriekontroll? Rekommendation: ja, innan nästa byggsteg (matchning eller rapport) börjar använda inläsningen.
2. **I3:** hur ska osynliga tecken och riktningstecken i bank- och Z-filernas text hanteras (stoppa, ta bort eller visa synligt i rapporten)? Behöver bestämmas senast när rapporten byggs. Hör ihop med K17.
3. **I4–I7:** små rättelser (typkontroll av sökvägen, luckmeddelandet, teststrängar som `\u`-koder). Kan samlas till ett senare tillfälle.

## Åtgärder efter granskning 4

Rättat 2026-10-25 i en egen session. Granskarens text ovan är inte ändrad. GRANSKNING.md med granskning 4 committades först, som den var (commit 106a7ba). Hugo sa ja till att rätta I1 och I2. I3–I7 rättas inte nu.

**Ord som används nedan.** **ast** är Pythons eget verktyg för att läsa kod som Python själv ser den (vilka namn som importeras, vilka funktioner som anropas), i stället för att söka efter text. Ett **alias** är ett annat namn för samma sak, till exempel `import las_bank as b`.

| Nr | Åtgärdad | Test |
|---|---|---|
| I1 | Ja. Ett nytt skyddstest läser alla `.py`-filer i `scripts/` (även undermappar) utom `tests/`, `las_bank.py`, `las_kassa.py` och `inlasning_skydd.py` med ast. Det slår larm om en fil importerar `inlasning_skydd` på något sätt (även `from . import`, paketnamn och inuti en funktion), hämtar `_tolka_rader`, `_tolka_kassarader` eller en byggsten från `las_bank`/`las_kassa` (som import, som `las_bank.csv_rader`, via alias eller med `import *`), har ett förbjudet namn skrivet som text, eller slår upp ett namn som byggs ihop medan programmet kör (`getattr`, `hasattr`, `attrgetter` m.fl. med ett namn som inte är skrivet rakt ut, eller `eval`, `exec`, `__import__`, `importlib`, `vars`, `globals`, `sys.modules`, `__dict__`, `builtins`). Listan med förbjudna namn byggs från koden: allt som `inlasning_skydd.py` definierar, plus namn i `las_bank.py`/`las_kassa.py` som pekar på en genväg (importerade byggstenar under eget namn och alias som `TOLKA = _tolka_rader`, G8 punkt 5). En ny byggsten blir därför förbjuden utan att testet ändras. En ny inläsningsmodul (till exempel för kvitton) måste läggas till i listan över undantag med flit | `scripts/tests/test_inga_genvagar.py`: `test_i1_ingen_karnfil_anvander_en_genvag`, 50 fall i `test_i1_kontrollen_hittar_en_fil_som_anvander_en_genvag` (påhittad fil i `tmp_path`, bland dem granskarens tre rader och `getattr` med hopsatt text), `test_i1_kontrollen_hittar_alias_i_en_inlasningsmodul`, `test_i1_kontrollen_hittar_en_genvag_i_en_undermapp`, skyddstester: `test_i1_undantagen_och_testerna_far_anvanda_genvagarna`, `test_i1_de_undantagna_filerna_finns`, `test_i1_de_forbjudna_namnen_hittas`, 7 fall i `test_i1_vanlig_kod_slaps_igenom` |
| I2 | Ja. `summa_per_momssats` kör `kontrollera_z_serien` först. En dubblett, lucka, ett Z-nummer som går bakåt eller en tom lista stoppas med samma fel som seriekontrollen ger, och ingen summa returneras. Beskrivningen överst i `las_kassa.py` säger det | `test_i2_samma_z_rapport_inlast_tva_ganger_summeras_inte` (granskarens fall: två mappar, `TB-KASSA-1` och `tb-kassa-1`), `test_i2_samma_fil_tva_ganger_summeras_inte`, `test_i2_lucka_summeras_inte`, `test_i2_z_nummer_som_gar_bakat_summeras_inte`, `test_i2_tom_lista_summeras_inte`, `test_i2_testdatans_januari_och_kvartal_stoppas_av_den_planterade_luckan` |
| I3 | Nej, medvetet | Kräver Hugos beslut (beslut 2 i granskning 4): stoppa, ta bort eller visa osynliga tecken. Hör ihop med rapportsteget och K17 |
| I4 | Nej, medvetet | Kräver ett programmeringsfel och fanns före flytten. Samlas med andra små rättelser (beslut 3) |
| I5 | Nej, medvetet | Kräver ett programmeringsfel. Efter I1 kan ingen annan kärnfil än inläsningsmodulerna anropa byggstenarna, så det spelar mindre roll nu. Se förslaget nedan |
| I6 | Nej, medvetet | Kosmetiskt, serien stoppas rätt. Samlas med andra små rättelser (beslut 3) |
| I7 | Nej, medvetet | Gäller en siffra i en tidigare slutrapport, inte koden |

**Testdatans planterade lucka och facit (I2).** Januari i testdatan har en planterad lucka: Z-rapport 1011 (2025-01-15) saknas. Efter I2 vägrar `summa_per_momssats` därför att summera januari och hela kvartalet i ett stycke, vilket är rätt. Det befintliga facittestet (`test_summorna_per_momssats_stammer_med_facit_per_manad_och_for_hela_perioden`) var det enda befintliga testet som anropade `summa_per_momssats` (kontrollerat med grep). Det summerar nu januari och kvartalet i två hela delar, före och efter luckan, och lägger ihop dem. Februari och mars summeras som förut. Facit stämmer fortfarande för alla tre månaderna och kvartalet. Det nya testet `test_i2_testdatans_januari_och_kvartal_stoppas_av_den_planterade_luckan` kräver att januari och kvartalet i ett stycke stoppas vid Z-rapport 1011. Facit och testdatan är inte ändrade.

**Så bevisades testerna.** De nya testerna kördes i en kopia av projektet utanför projektmappen, med koden från commit 61a5946 (den granskade versionen).

- I2: 6 nya tester blev röda av rätt skäl (`DID NOT RAISE`). Gamla koden gav 224 kr i stället för 112 kr för granskarens fall, och en tom summa (`{}`) för en tom lista. Alla andra 559 tester var gröna, även det ändrade facittestet.
- I1: på gamla koden är det nya testet grönt, eftersom ingen kärnfil använder en genväg i dag. Granskarens försök (b) gjordes därför om: en ny fil `scripts/rapport.py` med en rad i taget lades till i kopian.

| Rad i den nya filen `scripts/rapport.py` | Gamla testsviten (496) | Nya testet säger |
|---|---|---|
| `from las_bank import _tolka_rader` | 1 röd (F11) | röd: "hämtar _tolka_rader från las_bank" |
| `from las_kassa import _tolka_kassarader` | **496 gröna** | röd: "hämtar _tolka_kassarader från las_kassa" |
| `from inlasning_skydd import las_fil, avkoda, csv_rader` | **496 gröna** | röd: "importerar från inlasning_skydd" |
| `from las_bank import csv_rader, las_fil, avkoda` | **496 gröna** | röd: "hämtar avkoda/csv_rader/las_fil från las_bank" |
| `import las_bank as b; f = getattr(b, '_tolka_' + 'rader')` (G8 punkt 5) | **496 gröna** | röd: "getattr med ett namn som inte är skrivet rakt ut som text" |
| `TOLKA = _tolka_rader` sist i `las_bank.py`, och `las_bank.TOLKA` i `rapport.py` (G8 punkt 5) | **496 gröna** | röd: "använder .TOLKA" |

Dessutom gjordes ett mutationstest på den nya koden: en ny kontroll i taget togs bort i en kopia, och hela sviten kördes. Alla gav minst ett rött test. En regel (genvägarnas namn som fristående namn i koden) gav först inget rött test. Den visade sig fånga bara sådant som de andra reglerna redan fångar, och togs bort. Regeln mot `import builtins`/`importlib` gav först inget rött test och fick två egna testfall (`import builtins as b; b.vars(...)` och `import importlib.util as u`).

| Borttagen kontroll (i en kopia) | Röda tester |
|---|---|
| I2: seriekontrollen i `summa_per_momssats` | 6 |
| I1: `import inlasning_skydd` | 3 |
| I1: `from inlasning_skydd import …` | 4 |
| I1: `from . import inlasning_skydd` | 1 |
| I1: `from las_bank import *` | 1 |
| I1: förbjudet namn hämtat från `las_bank`/`las_kassa` | 10 |
| I1: förbjudet namn som attribut (`las_bank.csv_rader`) | 8 |
| I1: förbjudet namn skrivet som text | 2 |
| I1: `getattr` m.fl. med hopsatt namn | 7 |
| I1: `getattr` m.fl. använd som värde (`g = getattr`) | 1 |
| I1: `getattr` m.fl. importerad under eget namn | 1 |
| I1: `eval`, `vars`, `__import__`, `globals` m.fl. | 3 |
| I1: `sys.modules` och `__dict__` | 2 |
| I1: `import builtins`/`importlib` | 2 |
| I1: `from importlib import …` | 1 |
| I1: fil som inte går att läsa som Python | 1 |
| I1: alias i inläsningsmodulerna (`TOLKA = _tolka_rader`) | 1 |
| I1: byggstenar importerade under eget namn i inläsningsmodulerna | 1 |
| I1: byggstenarna läses från `inlasning_skydd.py` | 1 |
| I1: undermappar genomsöks | 1 |

**Vad I1-testet inte klarar.** Det kan inte bevisa att ingen genväg finns. Den som medvetet skriver kod för att lura det kan lyckas i Python, till exempel genom att lägga modulen i en lista och läsa ut den med ett påhittat namn via en funktion som inte står i listan. Det kan inte heller se en ny genväg som skrivs inne i `las_bank.py` eller `las_kassa.py` (till exempel en ny funktion som anropar `_tolka_rader`), eftersom de filerna är undantagna. Testet stoppar misstag och de enkla sätten att lura det, och en ändring i de undantagna filerna syns i granskningen. Det förbjuder också `getattr` med hopsatt namn, `eval`, `exec` och dynamisk import i hela kärnan, vilket ingen kärnfil använder i dag (granskning 4, uppgift D).

**Förslag (inte gjort).** Två sätt att göra skyddet starkare än ett test, att ta ställning till innan nästa inläsningsmodul byggs:

1. Gör byggstenarna interna (`_las_fil`, `_avkoda` …) och låt `las_bank` och `las_kassa` sluta exportera dem. Det ändrar inget beteende men gör det tydligt i koden att de inte är till för annan kod.
2. Samla byggstenarna i en enda funktion i `inlasning_skydd.py`, till exempel `las_csv(sokvag, filsort, …)`, som alltid kör alla skydd i rätt ordning (läsning, avkodning, NUL, styrtecken, rubrikrad, CSV-rader). Då kan en ny inläsningsmodul inte glömma ett steg, och I5 blir mindre viktigt. Detsamma för kassan: en funktion som läser en hel period (alla Z-filer, Z-kontroll a–e, seriekontrollen och summan) i stället för att anroparen sätter ihop stegen.

**Ny iakttagelse under arbetet (inte rättad).** Efter I2 går en månad med en saknad Z-rapport inte att summera alls förrän den saknade rapporten är hämtad. Det är rätt för en inläsning, men testdatan säger att Z-rapport 1011 *inte finns* (butiken hade öppet, och dagens betalningar syns på banken). Hur en sådan månad ska hanteras i drift (ärende till människa, eller summering med ett godkänt undantag) behöver bestämmas när K10 och rapporten byggs.

Testsviten efter rättelserna: 565 passed, 0 misslyckade (496 före, 63 nya i `test_inga_genvagar.py` och 6 nya i `test_las_kassa.py`).

### Senare samma dag: I3, I4, I6, NUL-radnumret, dolda tecken och säkrare form (två commits)

Rättat 2026-10-25 i en egen session, i två commits: **del A** (commit da1be60, små rättelser) och **del B** (säkrare form, samma commit som det här avsnittet). Granskarens text ovan är inte ändrad, och inte heller tabellen ovan. Där stod I3, I4 och I6 som "Nej, medvetet", vilket stämde när den skrevs. Tabellen nedan gäller nu för dem.

**Ord som används nedan.** Ett **internt** namn börjar med understreck (till exempel `_avkoda`). I Python betyder det "inte till för annan kod", och det är inte en del av modulens offentliga gränssnitt. **Escape-kod** är ett sätt att skriva ett tecken som synlig text i koden, till exempel ` ` för ett hårt mellanslag. Python läser koden som exakt samma tecken. En **Kassaperiod** är det `las_kassaperiod` returnerar: raderna för alla Z-filer i en period, som bara kan skapas efter att alla kontroller har gått igenom.

| Nr | Åtgärdad | Test |
|---|---|---|
| NUL-radnumret | Ja (del A). Bank och kassa räknade radnumret olika när en fil hade ett NUL-tecken. Bankfilen räknade som Python (`str.splitlines`), som också räknar tecken som `\x0c`, `\x85` och U+2028 som radslut. Z-filen räknade som en textredigerare (bara `\n`, `\r` och `\r\n`). Nu räknar båda som Z-filen, eftersom det ger radens verkliga nummer i filen. De andra radsluten stoppar filen ändå, men först efter NUL-kontrollen | `scripts/tests/test_bank_och_kassa.py`: `test_nul_tecken_far_radens_verkliga_radnummer` (8 sorters dolda radslut, för bank och kassa), `test_nul_tecken_efter_dolda_radslut_fore_rubrikraden` (skydd: `test_nul_tecken_med_windows_radslut`) |
| Dolda tecken i källkoden (granskning 4, uppgift C) | Ja (del A). De sju avsiktliga osynliga tecknen i `scripts/` (U+00A0 och U+202F i `belopp.py` och `test_belopp.py`, U+2028 och två U+200B i `test_las_kassa.py`) är skrivna som escape-koder. Python ser exakt samma kod (kontrollerat med Pythons ast för `belopp.py` och `test_belopp.py`, och strängarna jämförda en och en i `test_las_kassa.py`), så testerna prövar samma sak som förut. Ett nytt permanent test läser alla `.py`-filer i `scripts/`, även `tests/`, och slår larm för råa styrtecken (även tabb och `\r`, bara `\n` får finnas), osynliga formattecken (kategori Cf, bland dem riktningstecknen och nollbreddstecknen), andra blanksteg än vanligt mellanslag (Zs, Zl, Zp), utfyllnadstecken, blank blindskrift och variantväljare | `scripts/tests/test_inga_dolda_tecken.py`: `test_ingen_pythonfil_innehaller_dolda_tecken`, 38 fall i `test_kontrollen_hittar_dolda_tecken` (skydd: `test_det_finns_filer_att_soka_i`, `test_kontrollen_slapper_igenom_vanlig_kod`) |
| I3 | Ja (del A). En bank- eller Z-fil med något av riktningstecknen U+202A–U+202E eller U+2066–U+2069, var som helst i filen, stoppas med "rad N i filen innehåller tecknet U+…, som är ett riktningstecken …". Andra osynliga formattecken, till exempel U+200D i emoji, U+200B och mjukt bindestreck, godtas som förut. En fil som också har ett styrtecken före riktningstecknet stoppas för styrtecknet, med samma meddelande som förut | `test_bank_och_kassa.py`: `test_i3_riktningstecken_i_ett_textfalt_stoppar_filen` (alla 9 tecken, granskarens `ET-VEL`, bank och kassa), `test_i3_riktningstecken_i_bankens_referens_och_fore_rubrikraden`, `test_i3_riktningstecken_i_kassaregistret_stoppar_filen`, `test_i3_riktningstecknen_ar_nio`, skydd: `test_i3_andra_osynliga_formattecken_godtas` (5 sorter, bank och kassa), `test_i3_styrtecken_fore_riktningstecken_ger_samma_meddelande_som_forut` |
| I4 | Ja (del A). En sökväg som inte är text eller `Path` stoppas med `BankfilFel`/`KassafilFel` ("sökvägen ska vara text eller en Path, inte …") innan någon fil öppnas, i `las_bankfil`, `las_kassafil`, `ladda_bankformat` och `ladda_kassaformat`. `True`, `False` och heltal stänger alltså inte längre programmets in- eller utdata. Obs: även en sökväg som bytes stoppas nu (den fungerade förut för bankfilen, men inte för Z-filen) | `test_bank_och_kassa.py`: `test_i4_sokvag_av_fel_typ_stoppas_innan_nagot_oppnas` (None, flyttal, lista, ordbok, bytes och objekt i alla fyra funktionerna, med en spärr som slår larm om en fil öppnas), `test_i4_heltal_och_sanningsvarden_stanger_inte_programmets_utdata` (True, False, 0, 1 och 2 i ett eget program, som ska kunna skriva efteråt), skydd: `test_i4_text_och_path_godtas` |
| I5 | Nej, medvetet | Blir ointressant när byggstenarna är interna (del B nedan). Ingen kärnfil utom inläsningsmodulerna får använda dem (I1-testet), och de är inte längre en del av något offentligt gränssnitt |
| I6 | Ja (del A). När det inte finns någon dag mellan rapporterna före och efter luckan skrivs samma datum bara en gång ("Den saknade rapporten är från 9999-12-31."), och flera saknade rapporter får plural ("De saknade rapporterna är från …", och vid två olika datum "… från A, från B eller från båda dagarna."). En enda dag mellan rapporterna heter nu "Dag däremellan utan Z-rapport", inte "Dagar" | `test_las_kassa.py`: `test_i6_en_saknad_rapport_samma_dag`, `test_i6_flera_saknade_rapporter_samma_dag` (granskarens fall 37 och 100 039), `test_i6_flera_saknade_rapporter_dagar_i_rad`, `test_i6_en_dag_daremellan_ar_ental`, skydd: `test_i6_en_saknad_rapport_dagar_i_rad_ar_som_forut` |
| I7 | Nej, medvetet | Gäller en siffra i en tidigare slutrapport, inte koden |
| Förslag 1 ovan: interna byggstenar | Ja (del B). Alla namn i `inlasning_skydd.py` börjar med understreck (`_las_fil`, `_avkoda`, `_csv_rader`, `_Filsort` …). `las_bank.py` och `las_kassa.py` importerar dem under samma interna namn och gör inget av dem offentligt. Inget beteende har ändrats | `test_inga_genvagar.py`: `test_byggstenarna_har_bara_interna_namn`, `test_inlasningsmodulerna_har_inga_byggstenar_under_offentligt_namn` (samma sak när programmet kör), skydd: 8 fall i `test_kontrollen_hittar_offentliga_byggstenar`, `test_kontrollen_hittar_byggstenar_under_offentligt_namn_nar_programmet_kor`, `test_kontrollen_slapper_igenom_interna_namn_och_vanliga_offentliga_namn`. I1-testet bevisar fortfarande skyddet med de nya namnen |
| Förslag 2 ovan: läsa en hel kassaperiod | Ja, för kassan (del B). `las_kassaperiod(mapp, kassaformat, fran_datum, till_datum)` läser alla Z-filer i mappen med datum i perioden, gränserna medräknade (datumet tas ur filnamnet enligt kassaformatet), kör `las_kassafil` på varje fil och `kontrollera_z_serien` på alla, och returnerar först då raderna, som en `Kassaperiod`. `summa_per_momssats` tar bara emot en `Kassaperiod`, inte listor med rader. En `Kassaperiod` kan bara skapas av `las_kassaperiod` (en nyckel som bara den har) och kan inte ändras: raderna sparas som oföränderliga kopior, och `rapporter` ger nya kopior varje gång. I1-testet förbjuder annan kärnkod att använda nyckeln och periodens inre. Andra filer i mappen hoppas över, undermappar gås inte igenom, och en fil som följer mönstret men har ett datum som inte finns stoppar perioden | `test_las_kassa.py`: facittestet `test_summorna_per_momssats_stammer_med_facit_per_manad_och_for_hela_perioden` (januari som 2025-01-01–2025-01-14 och 2025-01-16–2025-01-31, kvartalet som 2025-01-01–2025-01-14 och 2025-01-16–2025-03-31, stämmer mot facit), `test_i2_testdatans_januari_och_kvartal_stoppas_av_den_planterade_luckan` (januari i ett stycke stoppas vid Z-rapport 1011), `test_i2_summa_tar_inte_emot_godtyckliga_rader` (granskarens fall), 4 fler `test_i2_…` och 13 testfunktioner `test_period_…` (20 tester). I `test_inga_genvagar.py` 6 nya fall i `test_i1_kontrollen_hittar_en_fil_som_anvander_en_genvag` |

**Så bevisades testerna i del A.** Dagens tester kördes i en kopia av projektet utanför projektmappen med koden från commit 14c6bf0 (före rättelserna). Resultat: 63 röda och 628 gröna. Alla 63 röda är nya eller ändrade tester och blev röda av rätt skäl: NUL-testerna för banken fick "rad 4" i stället för "rad 3" (9, kassans fall var redan gröna, som de ska), riktningstecknen släpptes igenom eller stoppades av något annat (21), sökvägarna av fel typ öppnades eller kraschade med `TypeError` (24), programmet med `True` som sökväg förlorade sin utdata och avslutades med fel (1), luckmeddelandena hade det gamla, dubbla datumet eller "Dagar" (7), och dolda-tecken-testet hittade hårt mellanslag och smalt hårt mellanslag i den gamla `belopp.py` (1). Körd mot hela den gamla `scripts/` (även de gamla testfilerna) hittade dolda-tecken-testet exakt granskarens sju tecken.

**Ändrade befintliga tester.** Tre i del A: två luckmeddelanden som krävde den gamla, felaktiga meningen (I6), och en variant i H2-testet (`vand_text`, U+202E i kassaregistret) som nu stoppas redan vid inläsningen och därför prövas i I3-testet i stället. I del B: facittestet och fem `test_i2_…` skrivs om till `las_kassaperiod`, eftersom `summa_per_momssats` inte längre tar listor, och `test_inlasning_skydd.py` och `test_inga_genvagar.py` använder byggstenarnas nya namn. Körde man del A:s tester oförändrade mot del B:s kod blev 150 röda, alla av just de skälen (gamla namn som inte finns, eller listor till `summa_per_momssats`). Alla andra, bland dem hela `test_las_bank.py` och resten av `test_las_kassa.py`, var gröna.

**Har `las_bankfil` och `las_kassafil` ändrat beteende?** Samma sätt som granskare 4: 3 034 provfall (1 517 bankfiler och 1 517 Z-filer, slumpade men samma vid varje körning) kördes mot tre kopior av koden: före rättelserna (14c6bf0), efter del A (da1be60) och efter del B. Fallen var giltiga filer med 1–8 rader, olika avgränsare, förrader, extra och omkastade kolumner och olika skrivsätt för kassan. 80 % fick 1–3 skador: styrtecken, NUL, riktningstecken, dolda radslut följda av NUL, U+FEFF, U+200B, U+200D, citattecken, avgränsare, borttagna, dubblerade och omkastade rader, avklippta rader och filer, ändrade siffror, fält på upp till 200 000 tecken, Windows-1252, UTF-16, BOM och trasiga byte. Dessutom tom fil, bara BOM, saknad fil, mapp, oläsbar fil och sökvägar av fel typ (None, flyttal, lista, ordbok, bytes, `Path`, och `True`, `False`, 0, 1, 2 i ett eget program per fall). För varje fall jämfördes felklassen, hela meddelandet och felets extra uppgifter, eller alla godkända rader och fält.

| Jämförelse | Fall med skillnad | Förklaring |
|---|---|---|
| Efter del A mot efter del B | **0 av 3 034** | Del B har inte ändrat något beteende i `las_bankfil` eller `las_kassafil` |
| Före rättelserna mot efter del B | 378 av 3 034, alla förklarade | 249 riktningstecken (I3: 14 filer som förut godkändes stoppas nu, och 235 som förut stoppades av något annat stoppas nu för riktningstecknet), 109 bankfiler med NUL efter ett dolt radslut (bara radnumret i meddelandet), 20 sökvägar av fel typ (I4: 8 krascher och 4 program som förlorade sin utdata blir `BankfilFel`/`KassafilFel`, och 8 bytes eller None som förut stoppades av något annat). Ingen oförklarad skillnad |

Efter del B godkändes 579 fall (331 bank, 248 kassa) och 2 455 stoppades. Inget fall kraschade.

**Mutationstest.** I en kopia av projektet utanför projektmappen togs en ny kontroll i taget bort (eller ett dolt tecken lades tillbaka), och hela sviten kördes. Alla 59 gav minst ett rött test. Två försök i del B gav först inget rött test och ledde till ändringar: testet för interna namn saknade egna skyddsfall, så det fick fall med påhittade filer (`test_kontrollen_hittar_offentliga_byggstenar` m.fl.), och kontrollen av kassaformatet i `las_kassaperiod` prövades bara med ett fel som `las_kassafil` också hittar, så testet prövar nu ett trasigt filnamnsmönster och en tom mapp. Ett tredje försök (att låta summeringen ta emot listor efter typkontrollen) ändrade inget, eftersom typkontrollen före stoppar listor. Det är ingen borttagen kontroll och togs bort ur listan.

| Del | Borttagen kontroll eller tillagt tecken (i en kopia) | Röda tester |
|---|---|---|
| A | NUL: bankens gamla radräkning | 9 |
| A | Dolda tecken: hårt mellanslag tillbaka i `belopp.py` | 1 |
| A | Dolda tecken: U+2028 tillbaka i `test_las_kassa.py` | 1 |
| A | Dolda tecken: U+202E i en kommentar i `las_bank.py` | 1 |
| A | Dolda tecken: tabb i `inlasning_skydd.py` | 1 |
| A | Dolda tecken: U+200D i en teststräng | 2 |
| A | Dolda tecken: CR (Windows-radslut) i `las_kassa.py` | 1 |
| A | Dolda-tecken-testet: kategori Cf borttagen | 19 |
| A | Dolda-tecken-testet: kategori Cc borttagen | 8 |
| A | Dolda-tecken-testet: Zl och Zp borttagna | 2 |
| A | Dolda-tecken-testet: andra blanksteg (Zs) borttagna | 4 |
| A | Dolda-tecken-testet: utfyllnadstecken borttagna | 5 |
| A | Dolda-tecken-testet: `tests/` genomsöks inte | 1 |
| A | I3: kontrollen av riktningstecken borttagen | 21 |
| A | I3: bara U+202A–U+202E | 9 |
| A | I3: bara U+2066–U+2069 | 12 |
| A | I3: alla Cf-tecken stoppas (för mycket) | 14 |
| A | I4: kontrollen i `_las_fil` borttagen | 13 |
| A | I4: kontrollen i `_ladda_json` borttagen | 13 |
| A | I4: heltal och sanningsvärden godtas | 2 |
| A | I4: bytes godtas | 5 |
| A | I6: samma datum två gånger igen | 4 |
| A | I6: ental vid flera saknade samma dag | 1 |
| A | I6: ental vid flera saknade dagar i rad | 1 |
| A | I6: "Dagar" för en dag | 2 |
| B | Ett offentligt namn i `inlasning_skydd.py` | 1 |
| B | En offentlig funktion i `inlasning_skydd.py` | 1 |
| B | `las_bank` gör en byggsten offentlig (`csv_rader = _csv_rader`) | 2 |
| B | `las_kassa` importerar en byggsten under offentligt namn | 2 |
| B | Perioden: nedre gränsen borttagen | 2 |
| B | Perioden: övre gränsen borttagen | 4 |
| B | Perioden: gränserna inte medräknade | 5 |
| B | Perioden: seriekontrollen borttagen | 4 |
| B | Perioden: Z-kontroll a–e borttagen (genvägen i stället för `las_kassafil`) | 2 |
| B | Perioden: stoppet för period utan Z-filer borttaget | 1 |
| B | Perioden: kontrollen att fran_datum inte ligger efter till_datum borttagen | 1 |
| B | Perioden: datumens form kontrolleras inte | 3 |
| B | Perioden: datum som inte finns godtas | 1 |
| B | Perioden: mappens typ kontrolleras inte | 1 |
| B | Perioden: saknad mapp översätts inte | 1 |
| B | Perioden: fil i stället för mapp översätts inte | 1 |
| B | Perioden: oläsbar mapp översätts inte | 1 |
| B | Perioden: ogiltigt datum i filnamn hoppas över | 1 |
| B | Perioden: filerna sorteras inte | 1 |
| B | Perioden: kassaformatet kontrolleras inte | 1 |
| B | Kassaperiod: nyckeln kontrolleras inte | 1 |
| B | Kassaperiod: raderna sparas inte som oföränderliga kopior | 1 |
| B | Kassaperiod: `rapporter` ger inte kopior | 1 |
| B | Kassaperiod: tilldelning inte spärrad | 1 |
| B | Kassaperiod: borttagning inte spärrad | 1 |
| B | `summa_per_momssats`: typkontrollen borttagen | 1 |
| B | `summa_per_momssats`: typkontrollen tar emot listor | 1 |
| B | I1-testet: periodens inre inte förbjudet | 4 |
| B | I1-testet: `__setattr__`/`__delattr__` inte förbjudna | 2 |
| B | Testet för interna namn: offentliga namn i `inlasning_skydd.py` kontrolleras inte | 3 |
| B | Testet för interna namn: import under offentligt namn kontrolleras inte | 2 |
| B | Testet för interna namn: import av modulen kontrolleras inte | 1 |
| B | Testet för interna namn: offentliga alias kontrolleras inte | 2 |
| B | Testet för interna namn: kontrollen när programmet kör borttagen | 1 |

**Nya iakttagelser under arbetet (inte rättade).**

- **Andra riktningsmärken godtas.** U+200E och U+200F (vänster- och högermärke) och U+061C (arabiskt märke) påverkar också textens riktning, men ligger utanför intervallen i uppgiften. De godtas därför fortfarande. Ska de stoppas behöver det beslutas.
- **NUL-tecken i sökvägen.** En sökväg som är text men innehåller ett NUL-tecken ger fortfarande `ValueError` från Python i stället för `BankfilFel`/`KassafilFel` (en del av granskarens I4, men utanför uppgiften "inte text eller Path").
- **En period ser inte luckor i kanterna.** Precis som seriekontrollen ser `las_kassaperiod` bara luckor mellan rapporterna som finns i perioden. En period som börjar dagen efter en saknad rapport (som 2025-01-16 i facittestet) godkänns. Det är så facittestet ska fungera, men i drift måste K10 eller rapporten se till att perioderna tillsammans täcker hela månaden.
- **Felstavade Z-filer hoppas över.** En fil som inte följer filnamnsmönstret exakt (till exempel `Kassa_2025-01-07.csv` med stort K) hoppas över utan varning. Mitt i en period syns det som en lucka i Z-serien, men i periodens början eller slut syns det inte.
- **Skyddet kan kringgås med flit.** En `Kassaperiod` går att förfalska med kod som medvetet går förbi Python-reglerna. I1-testet stoppar de enkla sätten (nyckeln, periodens inre, `object.__setattr__`), men kan inte bevisa att inget annat sätt finns, på samma sätt som för I1.

Testsviten: **730 passed**, 0 misslyckade (565 före, 691 efter del A, 730 efter del B). SPEC.md, CLAUDE.md, `foretag/`, testdatan och facit är inte ändrade.

## Åtgärder 2026-10-25: små rättelser och matchning mot banken

Gjort i en egen session, i tre commits: SPEC.md (del A, commit 7133f15, med Hugos godkända text: `cd` och `tar` i 7.1, K4a, K4b och K13 i avsnitt 6, beslutet om minst en momsrad, och Ö8–Ö10), små rättelser (del B) och matchning mot banken (del C). Ingen granskares text ovan är ändrad. SPEC.md är inte ändrad i del B och C.

### Del B: små rättelser

| Nr | Rättelse | Test |
|---|---|---|
| 5 | Ett jättelångt heltal i `bankformat.json` eller `kassaformat.json` stoppas med `BankfilFel`/`KassafilFel`: "… innehåller ett heltal med N siffror, men ett tal i formatet får ha högst 15 siffror." Längden prövas i `_ladda_json` (i `inlasning_skydd.py`) innan talet räknas ut, med samma gräns som i underlagen. Förut räknade Python 3.9 (projektets Python) ut talet, vilket tog 2,7–3,1 sekunder för 900 000 siffror, och sedan stoppades formatet av ett annat fel. Python 3.11 och senare ger i stället ett `ValueError` på engelska för tal med fler än 4300 siffror. Gränsen står i funktionen och inte som ett eget namn, eftersom skyddstestet för offentliga byggstenar (som jämför värden när programmet kör) annars tog talet 15 för en byggsten när underlagets gräns också är 15 | `test_bank_och_kassa.py`: `test_jattelangt_tal_i_formatet_stoppas_utan_att_raknas_ut` (16, 4301 och 900 000 siffror, bank och kassa, hela meddelandet och högst 2 sekunder), `test_jattelangt_tal_stoppas_aven_med_nyare_pythons_grans` (efterliknar gränsen i Python 3.11 med en egen `int`), skydd: `test_tal_med_femton_siffror_lases_och_stoppas_av_den_vanliga_kontrollen` |
| 6 | Varje underlag ska ha minst en momsrad (beslut i SPEC 11). En tom lista stoppas: "'moms' har inga momsrader. Varje underlag ska ha minst en momsrad, så att beloppet kan kontrolleras (K13). Ett momsfritt underlag har en rad med momssats 0 och moms 0." K13 (summan av momsraderna är lika med beloppet) görs därför alltid. Förut hoppades den över för ett underlag utan momsrader | `test_las_underlag.py`: `test_underlag_utan_momsrader_stoppas` (ersätter `test_underlag_utan_moms_godtas`, som krävde det gamla beteendet), skydd: `test_momsfritt_underlag_med_sats_0_godtas_och_kontrolleras`. Fuzzens kontroll av inlästa underlag kräver nu minst en momsrad. `test_testdata_q1.py`: `test_momsfria_underlag_har_en_rad_med_sats_0_och_moms_0`, och `test_underlagen_har_ratt_falt_och_gar_ihop` kräver minst en momsrad |

**Vad som ändrades i testdatan.** Generatorn ger försäkringsfakturan (LEV-FORSAKRING, `SYNT-U-2025-005`) en momsrad med sats 0, belopp utan moms 9 600,00 kr och moms 0, i stället för en tom lista (ny konstant `MOMSFRI = 0`). Beloppet är detsamma, 9 600,00 kr. Det var det enda momsfria underlaget. Generatorn kördes om: bara `underlag/SYNT-U-2025-005.json` ändrades. Inga andra filer, och inte facit, eftersom facit inte innehåller underlagens momsrader och slumpen drar samma tal som förut. `test_testdata_q1.py` är grönt. Raden om `moms` i `testdata/README.md` säger nu "Minst en rad" i stället för "Tom lista om dokumentet saknar moms".

**Så bevisades testerna.** De nya och ändrade testfilerna kördes mot koden och testdatan från commit 7133f15 (före rättelserna) i en kopia utanför projektet: 12 röda, alla av rätt skäl (8 för talen: annat meddelande eller mer än 2 sekunder; 4 för momsraderna: tomma listan godtogs, eller försäkringsfakturan hade en tom lista), och 1 025 gröna.

**Mutationstest.** En ny kontroll i taget togs bort i en kopia, och hela sviten kördes.

| Borttagen kontroll (i en kopia) | Röda tester |
|---|---|
| `parse_int` borttagen i `_ladda_json` | 8 |
| Längdkontrollen i `_heltal_ur_json` | 8 |
| Översättningen till `BankfilFel`/`KassafilFel` (ett internt fel kommer igenom i stället) | 8 |
| Kontrollen av minst en momsrad | 1 |
| Generatorn ger försäkringsfakturan en tom lista igen | 1 |

Testsviten efter del B: **1 037 passed**, 0 misslyckade (1 025 före).

### Del C: matchning mot banken

**Ord som används nedan.** Att **matcha** är att para ihop en bankrad med underlaget som förklarar den, till exempel en betalning med fakturan. En **kandidat** är ett underlag som kan höra till en bankrad. Ett **tidsfönster** är hur många dagar efter underlagets datum betalningen får ligga. Ett **oavstämt** underlag är ett som ingen bankrad har matchats mot än, till exempel en obetald faktura.

**Nya filer.**

- `scripts/matcha_bank.py` med en enda offentlig funktion, `matcha_period(bankrader, underlagsperiod, matchningsformat, bedomningsdatum)`, och klasserna `MatchningFel` och `Matchningsresultat`.
- `scripts/las_matchningsformat.py` med `ladda_matchningsformat` (läser filen) och `kontrollera_matchningsformat` (kontrollerar innehållet, används också av `matcha_period`). Den ligger i en egen modul eftersom `matcha_bank.py` bara ska ha en offentlig funktion, och eftersom filen läses med de gemensamma skydden i `inlasning_skydd.py`, som bara inläsningsmodulerna får använda.
- `foretag/syntet-testbutik/matchning.json`: fyra regler för bankrader som inte kräver underlag (kortinlösen, Swish, kontantinsättning, bankens avgifter), tidsfönster 40 dagar för leverantörsfakturor och 3 dagar för kvitton, och 7 dagar innan en bankrad utan underlag blir ett ärende. Allt är antaget utifrån testdatan och står som SYNTETISKT i filen.
- Tester: `scripts/tests/test_matcha_bank.py` och `scripts/tests/test_las_matchningsformat.py`.

**Reglerna, som de är byggda.**

| Regel | Test |
|---|---|
| Indatan kontrolleras först: bankraderna ska vara en lista (eller tupel) med rader som har exakt uppgifterna från `las_bankfil`, med rätt typ (text, giltiga datum, heltal och inte True/False), ett id som inte är tomt och inga dubbla id. Underlagen ska vara en `Underlagsperiod` (inte en underklass). Formatet kontrolleras igen. Bedömningsdatumet ska vara ett giltigt datum som text. Fel ger `MatchningFel` | `test_bankrader_av_fel_typ_stoppas` (6 fall), `test_trasiga_bankrader_stoppas` (15), `test_samma_bankrad_tva_ganger_stoppas`, `test_underlagen_ska_vara_en_underlagsperiod`, `test_bedomningsdatum_ska_vara_ett_giltigt_datum` (9), `test_trasigt_format_stoppas_aven_nar_det_skickas_direkt` (5) |
| En bankrad som passar en regel i `kraver_inte_underlag` hamnar i gruppen `kraver_inte_underlag`, med regelns namn. Riktningen (in eller ut) ska stämma, och referensen och beskrivningen ska börja exakt med regelns text, utan normalisering | 11 fall i `test_bankrader_som_inte_kraver_underlag`, `test_rad_som_inte_kraver_underlag_matchas_inte_mot_ett_underlag` |
| Ett underlag är en kandidat om beloppet är exakt bankradens med omvänt tecken, motparten står i bankradens beskrivning eller referens som hela ord (efter samma normalisering som kassans namn), och bankradens transaktionsdag ligger från underlagets datum till och med tidsfönstret för underlagets typ | `test_samma_belopp_motpart_och_datum_matchas`, `test_annat_belopp_eller_fel_tecken_matchas_inte` (4), `test_motparten_i_bankradens_text_matchas` (8), `test_motpart_som_inte_star_som_hela_ord_matchas_inte` (5), `test_tidsfonstret_per_underlagstyp` (6), `test_tidsfonstret_galler_transaktionsdagen_inte_bokforingsdagen` |
| Flera kandidater, och fakturanumret för exakt en av dem står i bankradens text: den är den enda kandidaten | `test_fakturanumret_avgor_nar_flera_underlag_passar` (5 referenser), `test_fakturanumret_ensamt_racker_inte` |
| Exakt en kandidat som inte passar någon annan bankrad: matchad. Ett underlag och en bankrad matchas högst en gång | `test_varje_underlag_och_varje_bankrad_matchas_hogst_en_gang`, `test_tvetydigt_ett_underlag_och_tva_bankrader`, `test_tvetydigt_nar_en_kandidat_ocksa_passar_en_annan_bankrad` |
| Flera kandidater, eller en kandidat som också passar en annan bankrad: ärende "tvetydig" (K3) med kandidaternas id | `test_tvetydigt_tva_lika_underlag_och_en_bankrad` och de två ovan |
| Ingen kandidat: ärende "saknat underlag" (K3) först när bedömningsdatumet ligger mer än `saknat_underlag_efter_dagar` dagar efter transaktionsdagen. Annars hamnar raden i gruppen `vantande`, med dagen då den blir ett ärende | `test_saknat_underlag_blir_arende_forst_efter_antalet_dagar_i_formatet`, `test_saknat_underlag_text_namner_dagarna_men_inga_texter_ur_bankraden`, `test_sista_dagen_som_finns_ger_inget_fel` |
| Underlag som inte matchas är oavstämda | `test_obetalt_underlag_ar_oavstamt`, `test_kvartalets_matchningar_ar_ratt` |
| Varje bankrad finns i exakt en grupp, och varje underlag i perioden i exakt en matchning eller bland de oavstämda | `kontrollera_grupperna` körs i alla små fall och i fuzzen, och `test_varje_bankrad_i_testdatan_finns_i_exakt_en_grupp` (alla 395 bankrader i kvartalet, fem bedömningsdatum) |
| Indatan ändras aldrig, och resultatet går inte att ändra: grupperna är tupler och posterna `MappingProxyType` | `test_indatan_andras_aldrig`, `test_resultatet_gar_inte_att_andra`, och fuzzen jämför indatan före och efter |
| `matcha_period` är den enda offentliga funktionen | `test_det_finns_bara_en_offentlig_funktion` |

**Testdatan.** Hela kvartalet läses med `las_bankfil` i samma kedja som i `test_las_bank.py` (varje månads ingående saldo är förra månadens utgående, och saldona kommer från facit). Mars stoppas av K1 på den planterade raden 74, så den raden rättas i en kopia i en tillfällig mapp: saldot byts mot det rätta enligt facit, och inget annat ändras. Underlagen läses med `las_underlagsperiod` för 2025-01-01–2025-03-31.

- `test_kvartalet_ger_exakt_det_planterade_felet_som_saknat_underlag`: med bedömningsdatum 2025-04-30 blir det exakt ett ärende, "saknat underlag" för februarifilens bankrad 85 (−351,00 kr, KORTKOP BUTIK-FORBRUKNING), och inga andra ärenden och inga väntande rader.
- `test_kvartalet_fore_sju_dagar_ger_inget_arende_bara_att_raden_vantar`: 2025-02-18, 2025-02-20 och 2025-02-25 ger inget ärende, bara att raden väntar till 2025-02-25. 2025-02-26 ger ärendet.
- `test_dubbletten_kommer_fran_k4_och_inte_fran_matchningen`: `SYNT-U-2025-004` är ett K4-ärende i underlagsperioden och finns inte någonstans i matchningens resultat. Originalet `SYNT-U-2025-003` matchas med den enda betalningen.
- `test_kvartalets_matchningar_ar_ratt`: 23 matchningar (16 leverantörsbetalningar, var och en mot fakturan med samma fakturanummer, och 7 kortköp mot sitt kvitto), 371 rader som inte kräver underlag (74 kortinlösen, 278 Swish, 13 kontantinsättningar och 6 avgifter), och de oavstämda är bara fakturor som förfaller efter 31 mars.
- `test_en_manad_i_taget_ger_samma_planterade_fel` och skyddet `test_utan_underlagen_fran_januari_blir_februaris_betalningar_arenden`.

**Fuzz.** `test_fuzz_skadade_indata_ger_ratt_resultat_eller_matchningfel`: 600 körningar, hälften på testdatans kvartal och hälften på små påhittade fall där även underlagen skadas och läses in igen. Skadorna: värden av fel typ eller med farligt innehåll i bankraderna, borttagna och nya nycklar, dubbla rader, rader som inte är rader, hela listan utbytt, ändrade belopp, datum, motparter och referenser, omkastade och borttagna rader, trasiga och krockande regler, tidsfönster och antal dagar utanför gränserna, och ogiltiga bedömningsdatum. Varje körning ger antingen ett resultat som följer alla regler ovan, eller `MatchningFel` (eller `UnderlagFilFel` när ett skadat underlag läses in), och indatan är oförändrad. Inget annat Python-fel. `test_fuzz_skadad_matchningsfil_laddas_ratt_eller_stoppas`: 300 skadade `matchning.json`, som ger ett kontrollerat format eller `MatchningsformatFel`.

**Skydden mot genvägar och företagsspecifikt i kärnan.** `las_matchningsformat.py` är en inläsningsmodul och lagd till i undantagen i `test_inga_genvagar.py`, med flit, eftersom den använder de gemensamma skydden. `matcha_bank.py` är inte undantagen, så förbuden gäller den: `test_matchningen_omfattas_av_skyddet` och 6 fall i `test_i1_kontrollen_hittar_genvagar_i_matchningen`. I `test_karnan_ar_generell.py` får `matcha_bank.py` använda underlagets egna nycklar som text (till exempel `"datum"`, som också är ett kolumnnamn i testbutikens kassaformat), precis som `las_underlag.py`. Det nya testet `test_karnan_innehaller_inga_bankradstexter_eller_regler_ur_matchningen` söker i hela kärnan, även i kommentarer, efter regelnamn och mönster ur alla `matchning.json` och efter beskrivningar och referenser ur testdatans bankfiler (utan siffrorna sist). Det hittade mina egna exempel `LEV-TE` och `LEV-TELE` i en kommentar i `matcha_bank.py` medan jag byggde, och de är utbytta mot påhittade namn.

**Skillnader mot uppgiften och mot SPEC K3.** Det här är byggt annorlunda än uppgiften säger, eller står inte i SPEC:

1. **Fem grupper, inte fyra.** En bankrad utan underlag som ännu inte är ett ärende (före 7 dagar) måste finnas i en grupp, eftersom varje bankrad ska finnas i exakt en. Den ligger i en femte grupp, `vantande`.
2. **Fakturanumret avgör mellan flera kandidater.** Med bara belopp, motpart och tidsfönster gav testdatan två extra ärenden "tvetydig": telefonfakturorna (LEV-TELE) har samma belopp varje månad, och betalningen av januarifakturan den 3 februari ligger också i februarifakturans tidsfönster (februarifakturan är daterad samma dag). Därför väljs den kandidat vars fakturanummer står i bankradens text, om det är exakt en. Fakturanumret ensamt räcker aldrig: belopp, motpart och tidsfönster krävs ändå.
3. **Motparten ska stå som hela ord.** "Förekommer i texten" tolkat som delsträng skulle göra LEV-TE till kandidat för bankrader från LEV-TELE. Hela ord krävs därför, efter samma normalisering som kassans namn.
4. **Regler för rader utan underlag har riktning och exakt text.** En regel gäller bara pengar in eller pengar ut, och texten jämförs exakt (inga osynliga tecken, samma stora och små bokstäver). Annars kunde en utgående betalning med en referens som börjar som en Swish-betalning slippa underlag. Två regler som kan passa samma rad stoppar formatet.
5. **Bankradens datum är transaktionsdagen**, både för tidsfönstret och för de 7 dagarna. För ett kortköp är transaktionsdagen köpdagen, som kvittot har, medan bokföringsdagen kan vara några dagar senare.
6. **SPEC K3** säger bara "Varje förslag har underlag". Att en bankrad utan underlag blir ett ärende efter 7 dagar står inte i SPEC, bara i facit och i `testforetag/FIKTIVT_FORETAG.md` (avsnitt 8). Inte heller att vissa bankrader (kortinlösen, Swish, kontanter, bankens avgifter) inte kräver underlag. SPEC är inte ändrad i del C.
7. **testdata/README.md** säger att bankens specifikation av avgifterna och kortinlösarens avgiftsspecifikation läggs till "när matchningen byggs" (beslut av Hugo). Enligt uppgiften hör bankens avgifter i stället till `kraver_inte_underlag` tills vidare, och det står i `matchning.json` och i `matcha_bank.py`.

**Säkerhet (inte rättat, behöver beslut).**

- **En borttagen bankrad syns inte.** `las_bankfil` returnerar en vanlig lista. Tar annan kod bort en rad efter inläsningen kan matchningen inte se det, och raden blir aldrig ett ärende. Förslag: en skyddad typ för bankrader, som `Underlagsperiod` och `Kassaperiod`.
- **Bankens avgifter slipper underlag oavsett belopp.** Regeln `bankavgift` undantar varje utgående rad som börjar med `AVG-` och `BANK AVGIFT`, även en stor betalning. Förslag: en beloppsgräns per regel, eller att avgiftsspecifikationen läggs till som underlag snart.
- **`matchning.json` ligger där agenten kan skriva**, som bank- och kassaformatet. Den hör till spärrsteget.
- **Ett `Matchningsresultat` kan skapas av annan kod.** Det är en `NamedTuple` utan nyckel (koden i `matcha_bank.py` får inte använda `object.__setattr__`, som nyckelmönstret i `las_underlag.py` behöver, eftersom I1-testet förbjuder det utanför inläsningsmodulerna). Rapportsteget bör därför köra `matcha_period` självt, inte ta emot ett färdigt resultat.

**Kommandon utanför den fasta listan.** Under del A och B redigerade jag några filer med ett litet Python-skript i terminalen i stället för med fil-verktygen, och läste filer med `sed`, `cut` och `uniq`. Det står inte på listan i SPEC 7.1. I del C användes listans kommandon och fil-verktygen, plus `echo` och `printf` (som bara skriver ut text) i en slinga som körde testsviten i varje mutationskopia. Generatorn kördes med kommandot i `testdata/README.md`, eftersom uppgiften sa att den skulle köras om. Inget av det ändrade något utanför projektet utom kopiorna i den tillfälliga mappen.

**Mutationstest.** I 63 kopior utanför projektet togs en ny kontroll bort (eller gjordes svagare) i var och en, och hela sviten kördes. 60 gav direkt minst ett rött test. Tre gav först inget rött test:

- **Datumets form (m14).** Python 3.9 stoppar själv allt som inte är ÅÅÅÅ-MM-DD, så kontrollen syntes inte. Python 3.11 och senare godtar fler skrivsätt (till exempel `20251231`). Nytt test: `test_datumets_form_kontrolleras_aven_med_nyare_python`, som efterliknar nyare Python. Nu rött.
- **Fakturanumret, "exakt en" (m31).** Prövades bara med två kandidater. Nytt test: `test_fakturanumret_avgor_bara_nar_det_pekar_ut_exakt_ett_underlag`, med tre kandidater där två fakturanummer står i texten. Nu rött.
- **Kopian av varje bankrad (m38).** Ger fortfarande inget rött test, och kan inte göra det: koden ändrar aldrig raderna, och resultatet fryses ändå som en ny kopia. Kopian ligger kvar som ett extra skydd, eftersom uppgiften säger att indatan ska kopieras. Det är ingen kontroll som kan tas bort, så den räknas inte som en kontroll utan test.

| Nr | Borttagen eller svagare kontroll (i en kopia) | Röda tester |
|---|---|---|
| m01 | Bankraderna ska vara en lista | 5 |
| m02 | Varje rad ska vara ett objekt | 3 |
| m03 | Raden har exakt uppgifterna från `las_bankfil` | 4 |
| m04 | Textfälten är text | 5 |
| m05 | Id får inte vara tomt | 1 |
| m06 | Radens datum kontrolleras | 3 |
| m07 | Talen är heltal | 5 |
| m08 | Talen: True/False godtas | 1 |
| m09 | Dubbla id | 1 |
| m10 | Underlagen ska vara en `Underlagsperiod` | 1 |
| m11 | Underklass av `Underlagsperiod` godtas | 1 |
| m12 | Formatet kontrolleras inte igen i `matcha_period` | 6 |
| m13 | Formatets fel blir inte `MatchningFel` | 6 |
| m14 | Datumets form (ÅÅÅÅ-MM-DD) | 0, efter nytt test 1 |
| m15 | Datumet behöver inte vara text | 5 |
| m16 | Regelns riktning | 3 |
| m17 | Regelns referens | 8 |
| m18 | Regelns beskrivning | 38 |
| m19 | 0 kr räknas som pengar in | 1 |
| m20 | Beloppets tecken | 1 |
| m21 | Beloppet | 5 |
| m22 | Motparten | 7 |
| m23 | Motparten söks bara i beskrivningen | 7 |
| m24 | Motparten som delsträng i stället för hela ord | 4 |
| m25 | Ingen normalisering av motparten | 6 |
| m26 | Tidsfönstrets början (underlagets datum) | 3 |
| m27 | Tidsfönstrets slut | 4 |
| m28 | Tidsfönstret räknas från bokföringsdagen | 2 |
| m29 | Samma tidsfönster för alla underlagstyper | 3 |
| m30 | Fakturanumret avgör inte | 6 |
| m31 | Fakturanumret avgör när det pekar ut minst ett (i stället för exakt ett) | 0, efter nytt test 1 |
| m32 | Ett underlag kan matchas mot flera bankrader | 2 |
| m33 | Ärende redan på dag 7 (i stället för efter) | 2 |
| m34 | Ärende direkt, ingen väntan | 5 |
| m35 | Väntan efter 9999-12-31 kraschar | 2 |
| m36 | De 7 dagarna räknas från bokföringsdagen | 1 |
| m37 | Resultatet fryses inte | 29 |
| m38 | Raderna kopieras inte | 0 (ändrar inget beteende, se ovan) |
| m39 | Matchade underlag räknas också som oavstämda | 21 |
| m40 | Flera kandidater blir "saknat underlag" i stället för "tvetydig" | 4 |
| m41 | Formatet: nycklar som inte är text | 2 |
| m42 | Formatet: True/False som antal dagar | 2 |
| m43 | Formatet: antal dagar utan gränser | 4 |
| m44 | Formatet: ingen övre gräns för antal dagar | 2 |
| m45 | Formatet: regelns riktning | 3 |
| m46 | Formatet: minst ett mönster per regel | 1 |
| m47 | Formatet: mönstren kontrolleras inte | 5 |
| m48 | Formatet: regelns namn kontrolleras inte | 2 |
| m49 | Formatet: samma regelnamn två gånger | 1 |
| m50 | Formatet: regler som kan passa samma rad | 6 |
| m51 | Formatet: krock oavsett riktning | 79 |
| m52 | Formatet: krock bara åt ena hållet | 2 |
| m53 | Formatet: krock om något mönster passar (i stället för alla) | 65 |
| m54 | Formatet: tidsfönstrens nycklar | 6 |
| m55 | Formatet: anteckning överst | 1 |
| m56 | Formatet: anteckning i en regel | 1 |
| m57 | Formatet: regelns nycklar | 6 |
| m58 | Formatet: reglerna ska vara en lista | 2 |
| m59 | Formatet: nycklarna överst | 10 |
| m60 | Genvägstestet: `las_matchningsformat` inte bland inläsningsmodulerna | 2 |
| m61 | Generalitetstestet: mönstret `AVR-` i en kommentar i `matcha_bank.py` | 1 |
| m62 | Genvägstestet: `matcha_bank.py` importerar `_las_underlagsfil` | 2 |
| m63 | Generalitetstestet: bankradstexten `KORTKOP` i en kommentar i `matcha_bank.py` | 1 |

Testsviten efter del C: **1 203 passed**, 0 misslyckade (1 037 efter del B, alltså 166 nya tester i `test_matcha_bank.py`, `test_las_matchningsformat.py`, `test_inga_genvagar.py` och `test_karnan_ar_generell.py`). SPEC.md är inte ändrad i del B och C.

### Hugos beslut om säkerhetsfrågorna i del C

Beslutade 2026-10-25, efter del C. Ingen kod är ändrad av besluten än.

| Fråga | Beslut | Görs |
|---|---|---|
| En borttagen bankrad syns inte | `las_bankfil` ska lämna ett resultat som inte går att ändra, som kassan och underlagen redan gör. Annars kan en bankrad tas bort efter inläsningen och aldrig bli ett ärende | Egen uppgift, **innan granskningen** av del B och C |
| Bankens avgifter slipper underlag oavsett belopp | Nytt krav i konfigurationen: varje regel i `kraver_inte_underlag` för utgående rader måste ha en högsta summa per bankrad. En rad som passar regeln men ligger över summan blir ett ärende direkt, med en egen typ (till exempel "över gräns för regeln bankavgift"), och matchas inte först mot underlag. För Syntet Testbutik är gränsen för `bankavgift` 250 kr (avgifterna i testdatan är 125 och 199 kr) | Egen uppgift, nu. Bankens avgiftsspecifikation som riktigt underlag kommer senare: den kräver en ny dokumenttyp i SPEC (förslag till ny öppen fråga) |
| `matchning.json` ligger där agenten kan skriva | Matchningsformatet skrivs in i SPEC avsnitt 7 bland filerna som ska ligga där agenten inte kan skriva | Gjort i SPEC.md (samma commit som det här avsnittet). Själva flytten görs i spärrsteget, som för bank- och kassaformatet |
| Ett `Matchningsresultat` kan skapas av annan kod | **Krav på rapportsteget:** rapporten kör `matcha_period` själv och tar aldrig emot ett färdigt `Matchningsresultat`. När rapportsteget byggs får resultatet samma nyckelskydd som `Underlagsperiod`, och genvägstestet får ett undantag för det, med flit | Regeln gäller nu. Skyddet byggs i rapportsteget |

## Åtgärd 2026-10-25: bankfilens resultat går inte att ändra (Bankperiod)

Gjort i en egen session, efter Hugos beslut ovan ("En borttagen bankrad syns inte"), före granskningen av del B och C. Ingen granskares text ovan är ändrad. SPEC.md, testdatan, facit och `foretag/` är inte ändrade.

**Ord som används nedan.** En **Bankperiod** är det `las_bankfil` nu returnerar: bankraderna plus periodens ingående och utgående saldo, i ett objekt som inte går att ändra. En **nyckel** är ett hemligt värde som bara inläsningsmodulen har. Utan den går det inte att skapa en Bankperiod, så den kan bara komma från en funktion som har kört alla kontroller.

**Felet som rättas.** `las_bankfil` returnerade en vanlig lista. Annan kod kunde ta bort en rad ur listan efter inläsningen, och `matcha_period` kunde inte se det: raden blev aldrig ett ärende. Det bevisades i en kopia av den gamla koden (commit a7cb12f): en bankfil med två rader, där rad 2 saknar underlag, gav ärendet för rad 2. Efter `del rader[1]` gav samma matchning inget ärende alls (`assert [] == ['X-1']`).

**Vad som är byggt.**

| Ändring | Test |
|---|---|
| `las_bankfil` returnerar en `Bankperiod` i stället för en lista. Den bär `rader` (i filens ordning, samma form som förut), `ingaende_saldo_ore` och `utgaende_saldo_ore`. Raderna sparas som oföränderliga kopior (`MappingProxyType`, en sorts objekt som bara går att läsa) och `rader` ger nya vanliga kopior varje gång, så att en ändring i dem aldrig når perioden. Tilldelning och borttagning är spärrade. Mönstret är detsamma som `Kassaperiod` och `Underlagsperiod` | `test_las_bank.py`: `test_bankperiod_bar_raderna_och_saldona`, `test_bankperiod_kan_inte_andras_utifran` |
| En `Bankperiod` kan bara skapas med nyckeln `_PERIODNYCKEL` i `las_bank.py`, som bara `las_bankfil` och `sla_ihop_bankperioder` använder. Utan den: "En Bankperiod kan bara skapas av las_bankfil eller sla_ihop_bankperioder, som kör alla kontroller först." | `test_bankperiod_kan_bara_skapas_av_las_bankfil` |
| Ny funktion `sla_ihop_bankperioder(perioder)` sätter ihop flera Bankperioder (till exempel januari, februari och mars) till en. Den tar bara en lista eller tupel med minst en Bankperiod (inte en underklass). Varje periods ingående saldo ska vara lika med förra periodens utgående ("Bankperioderna hänger inte ihop: …"), och ingen bankrad (samma id) får finnas två gånger ("… finns i flera Bankperioder. Samma bankfil kan vara inläst två gånger."). Den nya perioden har den första periodens ingående saldo och den sistas utgående | `test_sla_ihop_januari_och_februari`, `test_sla_ihop_stoppar_perioder_som_inte_hanger_ihop` (en saknad period, fel ordning, samma period två gånger), `test_sla_ihop_stoppar_samma_bankrad_tva_ganger` (samma fil två gånger, en kopia av filen, och skyddet att två olika filer på 0 kr går ihop), `test_sla_ihop_tar_bara_emot_bankperioder`, `test_sla_ihop_ger_en_ny_period_som_inte_delar_nagot_med_de_gamla` |
| `matcha_period(bankperiod, …)` tar bara emot en `Bankperiod` (kontrollen är `type(...) is Bankperiod`, som för `Underlagsperiod`), aldrig en lista eller tupel, inte heller raderna ur en riktig Bankperiod. Annat ger `MatchningFel`: "Bankraderna ska vara en Bankperiod från las_bankfil eller sla_ihop_bankperioder, inte …" | `test_matcha_bank.py`: `test_bankraderna_ska_vara_en_bankperiod` (12 sorters fel värde, även en underklass), `test_en_bankrad_som_tas_bort_efter_inlasningen_blir_anda_ett_arende` (Hugos fall: en rad som tas bort ur de utlästa raderna blir ändå ett ärende), `test_samma_bankfil_tva_ganger_stoppas_redan_nar_perioderna_satts_ihop` |
| Genvägstestet förbjuder Bankperiodens inre (`_rader`, `_ingaende_saldo_ore`, `_utgaende_saldo_ore`) i all annan kärnkod. Nyckeln heter `_PERIODNYCKEL` som i kassan och underlagen och var därför redan förbjuden | `test_inga_genvagar.py`: `test_i1_bankperiodens_inre_finns_i_modulen_och_ar_forbjudet` (skydd: namnen finns verkligen i `las_bank.py`), 13 fall i `test_i1_kontrollen_hittar_genvagar_forbi_bankperiodens_skydd`, 2 nya fall i `test_i1_kontrollen_hittar_genvagar_i_matchningen`, 1 nytt fall i `test_i1_vanlig_kod_slaps_igenom` |

**Kontroller som togs bort ur `matcha_bank.py`.** Kontrollen av varje bankrad (att raden är ett objekt med exakt uppgifterna från `las_bankfil`, med rätt typer, ett id som inte är tomt och inga dubbla id) är borttagen. Den kan inte längre nås: raderna kommer bara ur en Bankperiod, och de har redan gått igenom inläsningen och K1. Dubbla id stoppas nu i `sla_ihop_bankperioder` i stället. Kvar i matchningen hade de varit kontroller som inget test kan bevisa, eftersom mutationstestet inte kan göra dem röda. Det gäller m01–m09 i del C:s tabell ovan, som därmed inte längre finns i koden.

**Ändrade befintliga tester.** Alla rör att resultatet nu är en Bankperiod och inte en lista:

- `test_las_bank.py` och `test_bank_och_kassa.py`: raderna läses med `.rader` där testerna använder dem. Inget annat i testerna är ändrat.
- `test_matcha_bank.py`: kvartalet sätts ihop med `sla_ihop_bankperioder` (förut med `+` mellan listorna), och varje månads ingående saldo tas från förra Bankperiodens `utgaende_saldo_ore`. Hjälpfunktionen `bankrader` ger en Bankperiod och kan börja på ett annat saldo. `test_bankrader_av_fel_typ_stoppas` (6 fall), `test_trasiga_bankrader_stoppas` (15 fall) och `test_samma_bankrad_tva_ganger_stoppas` är ersatta av de tre nya testerna i tabellen, eftersom trasiga rader inte längre kan skickas in. `test_flera_bankfiler_och_tom_lista` heter nu `test_flera_bankfiler`: en tom lista eller en tupel kan inte längre skickas in, och en Bankperiod kan inte vara tom (`las_bankfil` stoppar en fil utan rader). I `test_datumets_form_kontrolleras_aven_med_nyare_python` är delen som ändrade en bankrads transaktionsdag borttagen, av samma skäl; delen om bedömningsdatumet är kvar. `test_indatan_andras_aldrig` jämför Bankperiodens rader före och efter.
- Fuzzen (`test_fuzz_skadade_indata_ger_ratt_resultat_eller_matchningfel`): skadorna med värden av fel typ i bankraderna, borttagna nycklar och rader som inte är rader är borttagna, eftersom de inte längre kan nå matchningen. I stället ändras den lilla bankfilens rader (belopp, datum, motpart, referens, dubblerade, omkastade och borttagna rader), filen skrivs och läses med `las_bankfil`, och ibland byts Bankperioden mot något annat (bland annat dess egna rader som lista), vilket alltid ska ge `MatchningFel`. För testdatans del väljs hela kvartalet eller februari.

**Så bevisades testerna.** I en kopia utanför projektet med koden från commit a7cb12f och de nya testfilerna gick `test_las_bank.py` och `test_matcha_bank.py` inte att läsa in ("cannot import name 'Bankperiod' from 'las_bank'"), alltså av rätt skäl: typen och funktionen finns inte i den gamla koden. Med bara de nya `test_inga_genvagar.py` och `test_bank_och_kassa.py` blev 8 röda: `test_i1_bankperiodens_inre_finns_i_modulen_och_ar_forbjudet` (nyckeln och typen finns inte) och 7 i `test_bank_och_kassa.py` som läser `.rader` (den gamla listan har inget sådant). Felet självt visades med ett eget test i kopian (se "Felet som rättas" ovan).

**Mutationstest.** I 22 kopior utanför projektet togs en ny kontroll bort eller gjordes svagare, och hela sviten kördes. Alla 22 gav minst ett rött test.

| Nr | Borttagen eller svagare kontroll (i en kopia) | Röda tester |
|---|---|---|
| b01 | Bankperiod: nyckeln kontrolleras inte | 1 |
| b02 | Bankperiod: raderna sparas inte som oföränderliga | 1 |
| b03 | Bankperiod: `rader` ger inte nya kopior | 6 |
| b04 | Bankperiod: tilldelning inte spärrad | 1 |
| b05 | Bankperiod: borttagning inte spärrad | 1 |
| b06 | `las_bankfil` returnerar listan som förut | 92 och 8 fel |
| b07 | Ihopsättning: perioderna behöver inte vara en lista eller tupel | 1 |
| b08 | Ihopsättning: tom lista stoppas inte | 1 |
| b09 | Ihopsättning: typkontrollen borttagen | 1 |
| b10 | Ihopsättning: underklass godtas (`isinstance`) | 1 |
| b11 | Ihopsättning: saldokedjan mellan perioderna kontrolleras inte | 1 |
| b12 | Ihopsättning: samma bankrad två gånger stoppas inte | 2 |
| b13 | Ihopsättning: fel ingående och utgående saldo i den nya perioden | 2 |
| b14 | Matchningen: typkontrollen borttagen | 3 |
| b15 | Matchningen: underklass godtas (`isinstance`) | 1 |
| b16 | Matchningen: listor och tupler godtas igen | 3 |
| b17 | Genvägstestet: `_rader` inte förbjudet | 5 |
| b18 | Genvägstestet: `_ingaende_saldo_ore` inte förbjudet | 3 |
| b19 | Genvägstestet: `_utgaende_saldo_ore` inte förbjudet | 4 |
| b20 | `matcha_bank.py` läser `bankperiod._rader` | 2 |
| b21 | `matcha_bank.py` importerar `_PERIODNYCKEL` | 2 |
| b22 | Bankperiod: raderna varken frysta eller kopierade (samma lista som `las_bankfil` gjorde) | 3, bland dem Hugos fall |

**Att tänka på.**

- `las_bank.py` har nu två offentliga funktioner som ger bankrader: `las_bankfil` och `sla_ihop_bankperioder`. Den andra läser ingen fil och tar bara emot Bankperioder, så den är ingen väg förbi K1. SPEC 7 nämner bara `las_bankfil`, och SPEC är inte ändrad.
- `sla_ihop_bankperioder` kontrollerar inte att perioderna ligger i datumordning, bara att saldona hänger ihop. Saldokedjan räcker för att se en saknad eller omkastad månad i testdatan, men två månader med samma ingående och utgående saldo kan byta plats utan att det märks.
- Skyddet kan kringgås med flit, som för `Kassaperiod` och `Underlagsperiod`: genvägstestet stoppar de enkla sätten men kan inte bevisa att inget annat sätt finns.

**Kommandon utanför den fasta listan.** Jag läste några filer med `sed -n` och mätte `.venv` med `du -sh` (båda bara läser). De står inte på listan i SPEC 7.1. Kopiorna gjordes med `git archive` och `tar` (för den gamla koden) och `cp -R` (för mutationerna), alla i den tillfälliga mappen, och ändringarna i kopiorna gjordes med fil-verktygen.

Testsviten: **1 209 passed**, 0 misslyckade (1 203 före).

## Åtgärd 2026-10-25: gräns för regler för pengar ut (bankens avgifter)

Gjort i en egen session, efter Hugos beslut ovan ("Bankens avgifter slipper underlag oavsett belopp"), och efter Bankperiod-åtgärden (commit e3a618c), som den bygger på. Ingen granskares text ovan är ändrad. SPEC.md, testdatan och facit är inte ändrade.

**Ord som används nedan.** En **regel för pengar ut** är en regel i `kraver_inte_underlag` med `"riktning": "ut"`, till exempel `bankavgift`. En **gräns** är den högsta summan per bankrad som regeln gäller för. **Öre** är hundradels kronor: 25000 öre är 250 kr.

**Felet som rättas.** Regeln `bankavgift` undantog varje utgående bankrad som började med `AVG-` och `BANK AVGIFT` från underlag, oavsett belopp. En betalning på 50 000 kr med en sådan text hade alltså slunkit igenom utan underlag och utan ärende.

**Vad som är byggt.**

| Ändring | Test |
|---|---|
| Ny nyckel `hogst_belopp_ore` i reglerna i `matchning.json`, kontrollerad i `las_matchningsformat.py` (`_kontrollera_grans`). Den **krävs** för en regel för pengar ut. Saknas den: "… saknar 'hogst_belopp_ore'. En regel för pengar ut ska ha en högsta summa i öre per bankrad, så att den aldrig gäller obegränsat." | `test_las_matchningsformat.py`: `test_regel_for_pengar_ut_utan_grans_stoppas`, `test_testforetagets_regel_utan_grans_stoppas` |
| Gränsen ska vara ett heltal i öre, större än 0 och med högst 15 siffror (samma gräns som talen i underlagen, `HELTAL_HOGST_SIFFROR` i `las_underlag.py`). true/false, decimaltal, text, null, listor och objekt stoppas: "… 'hogst_belopp_ore' ska vara ett heltal i öre, större än 0 och med högst 15 siffror, inte …". Ett tal med fler än 15 siffror skrivs inte ut i meddelandet (det tar lång tid för mycket långa tal), utan visas som "ett heltal med fler än 15 siffror". I filen stoppas ett så långt tal redan när JSON läses, av skyddet från del B | `test_gransen_av_fel_typ_stoppas` (8 fall), `test_gransen_0_eller_negativ_stoppas` (4), `test_gransen_med_fler_an_15_siffror_stoppas_nar_formatet_kommer_direkt` (5, även 10^5000), `test_gransen_med_fler_an_15_siffror_stoppas_i_filen`, skydd: `test_gransvarden_for_gransen_godtas` (1, 25000 och 999 999 999 999 999) |
| **Beslut i den här uppgiften:** en regel för pengar in får **inte** ha en gräns. Den skulle inte användas av matchningen, och en gräns som inte gör något ska inte se ut som ett skydd: "… har 'hogst_belopp_ore', men gäller pengar in. En gräns gäller bara regler med riktning 'ut', …". Om insättningar också ska ha en gräns är inte bestämt (se Beslut nedan) | `test_regel_for_pengar_in_far_inte_ha_en_grans` (3 värden, och skyddet att samma regel utan gräns godtas) |
| `matcha_bank.py`: en utgående rad som passar en regel men vars belopp, räknat som positivt, är **större** än gränsen blir direkt ett ärende (K3) av typen `"över gräns"`. Ärendet har, utöver de vanliga uppgifterna, `"regel"` (regelns namn) och `"hogst_belopp_ore"` (gränsen), och texten "Bankraden passar regeln 'avgift' för rader som inte kräver underlag, men beloppet är större än regelns gräns, 2,00 kr per bankrad. En människa behöver avgöra vad raden är och vilket underlag den ska ha." Texten har inga texter ur bankraden. Raden väntar inte 7 dagar, matchas inte mot underlag och hamnar inte i `kraver_inte_underlag`. **Exakt på gränsen räknas som inom.** Varje rad prövas för sig. Beskrivningen överst i filen och i `Matchningsresultat` är uppdaterad | `test_matcha_bank.py`: `test_utgaende_rad_under_pa_och_over_gransen` (6 belopp: 1 och 199 öre under, 200 på, 201, 12 500 och 10^12 över), `test_over_gransen_ger_ett_arende_med_regeln_och_gransen`, `test_over_gransen_matchas_inte_mot_underlag` (med skyddet att samma rad matchas utan regeln), `test_inkommande_rad_paverkas_inte_av_gransen`, `test_gransen_galler_varje_bankrad_for_sig`, 3 nya fall i `test_trasigt_format_stoppas_aven_nar_det_skickas_direkt` |
| `foretag/syntet-testbutik/matchning.json`: `bankavgift` har `"hogst_belopp_ore": 25000` (250 kr, Hugos beslut). Anteckningen säger varför, och den gamla varningen "oavsett belopp" är borttagen | `test_testforetagets_format_laddas`, `test_varfor_bankens_avgifter_har_gransen_250_kr_star_i_formatet` |
| `foretag/README.md`: nytt avsnitt om `matchning.json`, med alla nycklar och gränsen | – |

**Testdatan.** Avgifterna i kvartalet är tre på 125 kr och tre på 199 kr, alla under 250 kr. Testdatan ger därför fortfarande exakt det planterade ärendet (februari, bankrad 85, "saknat underlag"), och de befintliga testerna för kvartalet är oförändrade och gröna. Det nya testet `test_testdatans_avgifter_ligger_inom_gransen` visar att gränsen verkligen prövas på testdatans rader: med gränsen 198,99 kr blir de tre avgifterna på 199 kr ärenden "över gräns", och med exakt 199,00 kr blir det inga nya ärenden.

**Fuzz.** `test_fuzz_skadade_indata_ger_ratt_resultat_eller_matchningfel` skadar nu också gränsen: tar bort den, byter den mot gränser kring testdatans och de små fallens avgifter, mot för stora, 0, negativa och värden av fel typ, och lägger till nya regler med och utan gräns. Varje resultat kontrolleras mot de nya reglerna: ett ärende "över gräns" gäller en utgående rad som passar regeln och är större än gränsen, och varje rad i `kraver_inte_underlag` för en regel för pengar ut ligger på eller under gränsen. Antalet körningar är höjt från 600 till 800, eftersom de nya skadorna stoppar fler format och testets skydd kräver minst 100 resultat. Skyddet kräver också minst 10 ärenden "över gräns", så att fuzzen verkligen prövar dem.

**Så bevisades testerna.** I en kopia utanför projektet med koden och `matchning.json` från commit e3a618c (före ändringen) och de nya testfilerna blev 123 tester röda och 1 125 gröna. Felen beror på att den gamla koden inte känner till nyckeln ("har en okänd nyckel: 'hogst_belopp_ore'"), att den inte har något ärende "över gräns" och att testföretagets format saknar gränsen, alltså av rätt skäl.

**Mutationstest.** I 19 kopior utanför projektet togs en ny kontroll bort eller gjordes svagare, och hela sviten kördes. Alla 19 gav minst ett rött test.

| Nr | Borttagen eller svagare kontroll (i en kopia) | Röda tester |
|---|---|---|
| g01 | Formatet: regel för pengar ut utan gräns godtas | 4 |
| g02 | Formatet: true/false godtas som gräns (`isinstance`) | 1 |
| g03 | Formatet: decimaltal godtas som gräns | 2 |
| g04 | Formatet: 0 godtas | 2 |
| g05 | Formatet: negativ gräns godtas | 4 |
| g06 | Formatet: ingen övre gräns (15 siffror) | 4 |
| g07 | Formatet: övre gränsen ett för hög (16 siffror godtas) | 1 |
| g08 | Formatet: regel för pengar in med gräns godtas | 2 |
| g09 | Formatet: gränsen följer inte med i det kontrollerade formatet | 20 |
| g10 | Formatet: ett mycket långt tal skrivs ut i meddelandet | 5 |
| g11 | Matchningen: gränsen prövas inte | 8 |
| g12 | Matchningen: exakt på gränsen blir ett ärende (`>=`) | 4 |
| g13 | Matchningen: beloppets tecken vänds inte (pengar ut är aldrig över gränsen) | 8 |
| g14 | Matchningen: en rad över gränsen matchas mot underlag i stället | 8 |
| g15 | Matchningen: ärendet saknar regelns namn och gränsen | 3 |
| g16 | Matchningen: ärendets text saknar gränsen | 1 |
| g17 | `matchning.json`: gränsen 300 kr i stället för 250 kr | 3 |
| g18 | `matchning.json`: anteckningen säger inte varför | 1 |
| g19 | `matchning.json`: gränsen borttagen | hela `test_matcha_bank.py` går inte att läsa in (formatet stoppas), 1 fel |

**Att tänka på.**

- Ärendena "över gräns" står först bland ärendena, i bankfilernas ordning. Efter dem kommer "tvetydig" och "saknat underlag", också i bankfilernas ordning, som förut.
- Gränsen gäller varje bankrad för sig. Många små avgifter under gränsen ger inget ärende, hur många de än är. Det fångas först i månadsavstämningen (K10) eller av en kontroll av ovanliga belopp (K9), som inte är byggda.
- `matchning.json` ligger fortfarande där agenten kan skriva. Gränsen skyddar mot en stor rad med avgiftstext, inte mot att någon höjer gränsen i filen. Det hör till spärrsteget.
- Bankens avgiftsspecifikation som riktigt underlag ingår inte. Den kräver en ny dokumenttyp i SPEC och tas senare, som Hugo har bestämt.

**Beslut som behövs från Hugo.**

- Ska regler för pengar in (kortinlösen, Swish, kontantinsättningar) också ha en gräns? Idag stoppas en sådan gräns, eftersom den inte skulle användas.
- Den föreslagna öppna frågan om bankens avgiftsspecifikation som ny dokumenttyp är inte inskriven i SPEC 11 (SPEC ändras inte i den här uppgiften).

**Kommandon utanför den fasta listan.** Kopiorna för mutationstestet skapades och testsviten kördes i dem med en `for`-slinga, med `printf` för att skriva ut kopians namn, och en gång med `echo`. Testsvitens tid mättes en gång med `time`. Inget av det står på listan i SPEC 7.1, och inget ändrade något i projektet. Kopiorna gjordes med `cp -R`, `git archive` och `tar` i den tillfälliga mappen, och ändringarna i kopiorna gjordes med fil-verktygen.

Testsviten: **1 248 passed**, 0 misslyckade (1 209 före, alltså 39 nya tester i `test_las_matchningsformat.py` och `test_matcha_bank.py`).

## Granskning 5: underlag och matchning mot banken

| | |
|---|---|
| Datum | 2026-10-25 |
| Granskad version | commit c46142f ("Gräns för regler för pengar ut …") |
| Granskare | Oberoende session som inte sett steg 5 (underlag) och steg 6 (matchning) byggas. Ingen kod eller befintlig fil har ändrats, bara det här avsnittet har lagts till |
| Underlag | CLAUDE.md, SPEC.md (hela), foretag/README.md, foretag/syntet-testbutik/matchning.json, bankformat.json och kassaformat.json, scripts/las_underlag.py, las_bank.py, matcha_bank.py, las_matchningsformat.py, inlasning_skydd.py, testerna i scripts/tests/, testdata/README.md, facit.json, tidigare granskningar och åtgärdsavsnitt ovan |

### Så gick granskningen till

Allt provande gjordes i en tillfällig mapp utanför projektet. Där lades en ren kopia av commit c46142f (med `git archive` och `tar`) och projektets `.venv` (med `cp -R`). Provskripten skrevs med fil-verktyget som egna testfiler i en andra kopia som bara hade kärnans filer, testdatan och `foretag/`, och kördes med testsvitens kommando inifrån kopian. Varje prov skrev sitt utfall till en textfil: **STOPPAD** (tydligt `UnderlagFilFel`, `MatchningFel`, `MatchningsformatFel` eller `BankfilFel`), **GODKÄND** (resultatet släpptes igenom, med vad som hände) eller **KRASCH** (annat Python-fel). Mutationstesterna gjordes i den rena kopian, en ändring i taget, som återställdes efteråt (`diff -r` mot projektets `scripts/` visar inga skillnader).

**Ord som används nedan.** En **dubblett** är samma underlag inläst två gånger. **Matcha** är att para ihop en bankrad med underlaget som förklarar den. En **kandidat** är ett underlag som kan höra till en bankrad. **Oavstämt** är ett underlag som ingen bankrad har matchats mot, till exempel en obetald faktura. Ett **förväxlingstecken** är ett tecken som ser ut som ett annat men är ett annat tecken i datorn, till exempel ett annat sorts bindestreck (‐ i stället för -) eller ett litet L i stället för en etta. Ett **riktningstecken** är ett osynligt tecken som kan få text att visas i en annan ordning än den är lagrad.

Allvar: **hög** = kan ge fel bokföring, **medel** = onödig krasch eller otydligt fel (eller fel som kräver ovanliga omständigheter), **låg** = kosmetiskt eller kräver avsiktligt skriven kod.

### Sammanfattning av nya fynd

| Nr | Fynd | Allvar |
|---|---|---|
| J1 | En dubblett där fakturanumret eller motparten bara *ser* likadan ut (förväxlingstecken, annat bindestreck, mellanslag) fångas inte av K4. Fakturanummerregeln i matchningen matchar sedan originalet, och dubbletten blir ett oavstämt underlag, som en obetald faktura. **Inget ärende någonstans** | **Hög** |
| J2 | Fakturanummerregeln kan avgöra på ett ord som bara råkar stå i bankradens text (ett kort fakturanummer, ett fakturanummer som är motpartens namn, ett nummer som är en del av ett annat). En verklig tvetydighet blir då en matchning utan ärende | Medel |
| J3 | Tre riktningstecken släpps igenom: U+200E, U+200F och U+061C. SPEC 7 säger att riktningstecken stoppar filen | Medel |
| J4 | Ett kort motpartsnamn passar en annan, längre motparts bankrad ("ICA" passar "KORTKOP ICA MAXI"), och en motpart som heter som ett vanligt ord i banktexten passar alla sådana rader | Låg |
| J5 | Matchningen är kvadratisk: 100 000 bankrader mot 100 000 underlag tar ungefär en kvart, och med samma belopp på alla flera timmar. En momsrad-lista på knappt 1 MB tar 6,6 sekunder | Låg |
| J6 | Filer i underlagsmappen som inte heter exakt `.json` (till exempel `U-2.JSON`) och undermappar hoppas över utan att det sägs. En namngiven rörledning (FIFO) får inläsningen att stanna för alltid. Symboliska länkar till filer utanför mappen följs | Låg |
| J7 | En tom `Bankperiod` eller `Underlagsperiod` skapad med `__new__` ger `AttributeError` i stället för `MatchningFel`. Två nya sätt att förfalska eller ändra en Bankperiod (via `inspect` och `gc`) går förbi genvägstestet | Låg (kräver avsiktligt skriven kod) |
| J8 | Testlucka: att fakturanumret också söks i bankradens *beskrivning* (inte bara referensen) prövas inte av något test (mutation D8) | Låg |
| J9 | Små brister i meddelanden och regler: K4 nämner bara "olika belopp" när både belopp och datum skiljer; "lägst id" är bokstavsordning (`U-10` före `U-9`); ett bedömningsdatum före bankradens datum godtas; NFC/NFD-filnamn ger ett meddelande med två namn som ser likadana ut; formatet godtar en osynlig utfyllnad (U+3164) som mönster och regelnamnen `swish` och `Swish` samtidigt | Låg |
| J10 | SPEC: statusraden överst nämner inte ändringarna i 7133f15 och a7cb12f, och SPEC 7 nämner fortfarande bara `las_bankfil` och `las_kassaperiod` som "enda funktion" per källa | Låg (kosmetiskt) |

### Fynd i detalj

#### J1. Dubblett med förväxlingstecken passerar både K4 och matchningen. Allvar: hög

**Vad jag körde (A):** två underlag, `U-1` och `U-2`, med samma motpart (`LEV-A`), samma belopp (125,00 kr) och samma datum. Bara fakturanumret (eller motparten) skilde, på sätt som ser likadant ut eller nästan likadant ut för en människa. Lästes med `las_underlagsperiod`.

| Fakturanummer i U-2 (U-1 har `F-1`) | Utfall |
|---|---|
| `f-1`, `F-1 ` (mellanslag sist), `F-1` med U+200B eller mjukt bindestreck, `Ｆ－１` (fullbredd) | Dubblett, ärende "dublett av U-1" (rätt) |
| `F‐1` (U+2010 bindestreck), `F–1` (U+2013 tankstreck), `F−1` (U+2212 minustecken) | **Båda behålls, inget ärende** |
| `Ғ-1` (kyrilliskt tecken som liknar F), `F-l` (litet L i stället för 1) | **Båda behålls, inget ärende** |
| `F 1`, `F1`, `F-01` | **Båda behålls, inget ärende** |
| Motpart `LEV A`, `LEV-А` (kyrilliskt А), `LEV-A AB` i stället för `LEV-A` | **Båda behålls, inget ärende** |

**Vad jag körde (B):** samma par (`F-1` och `F‐1`, och `F-1` och `F-l`) och en bankrad på −125,00 kr från `LEV-A`.

| Bankradens referens | Utfall |
|---|---|
| `F-1` | `U-1` matchad. `U-2` **oavstämd, inget ärende** |
| `OCR 5555` (inget fakturanummer) | Ärende "tvetydig" med båda (rätt: en människa ser dubbletten) |

**Varför det spelar roll:** K4 finns för att samma faktura inte ska bokföras två gånger. Här säger varken K4 eller matchningen något. Dubbletten ser ut som en obetald faktura från samma leverantör med samma belopp, och kan föreslås bokförd som en andra leverantörsskuld (dubbel kostnad). Fakturanummerregeln gör det värre: utan den hade bankraden blivit "tvetydig" och en människa hade sett de två fakturorna bredvid varandra. Förväxlingar som `1`/`l` och `0`/`O` är vanliga när text läses ur en bild (OCR), och olika bindestreck är vanliga när text kopieras från en PDF.

**Vad som borde hända (förslag, beslut behövs):** K4 bör ge ett ärende, till exempel "möjlig dublett", när två underlag har samma motpart (normaliserad), samma belopp och samma datum, även om fakturanumret skiljer. Båda underlagen behålls, som i K4a och K4b, och en människa avgör. Ett komplement är att normaliseringen av fakturanummer också tar bort skiljetecken och bindestreck av alla slag, men det löser inte `1`/`l`. Det rör inga skatteregler, bara hur strikt dubblettkontrollen ska vara.

#### J2. Fakturanummerregeln kan avgöra på ett ord som råkar stå i texten. Allvar: medel

**Vad jag körde:** två fakturor från samma motpart med samma belopp, båda i tidsfönstret, och en bankrad som betalar en av dem.

| Fakturanummer | Bankradens text | Utfall |
|---|---|---|
| `10` och `11` | referens `OCR`, beskrivning `LEV-A 10 ST` | `U-1` (nr 10) matchad, `U-2` oavstämd. Inget ärende |
| `LEV-A` (fakturanumret är motpartens namn) och `F-2` | referens `OCR 5555`, beskrivning `LEV-A` | `U-1` matchad, utan att bankraden säger något om vilken faktura |
| `761` och `SYNT-TE-761` | referens `SYNT TE 761` (mellanslag i stället för bindestreck) | `U-1` (nr 761) matchad, fast referensen pekar på den andra |
| `761` och `SYNT-TE-761` | referens `SYNT-TE-761` | `U-2` matchad (rätt) |
| `F-1` och `F-10` | referens `F-10` | `U-2` matchad (rätt) |

Regeln väljer rätt i alla fall jag provade där fakturanumret verkligen är bankradens referens, och den gör aldrig två matchningar mot samma underlag eller samma bankrad (se uppgift B). Felet är att ett fakturanummer som bara råkar stå som ett eget ord någonstans i texten räcker. Då blir en verklig tvetydighet (två lika troliga fakturor) en matchning utan ärende, och fel faktura kan markeras som betald. Beloppen är lika, så kassan och banken stämmer ändå, men leverantörsreskontran (listan över vilka fakturor som är betalda) blir fel.

**Vad som borde hända (förslag):** låt fakturanumret avgöra bara när bankradens referens, normaliserad, är exakt fakturanumret, så som i testdatan. Annars "tvetydig".

#### J3. Tre riktningstecken släpps igenom. Allvar: medel

**Vad jag körde:** ett underlag vars motpart innehåller U+200F (höger-till-vänster-märke), U+200E (vänster-till-höger-märke) eller U+061C (arabiskt bokstavsmärke).

**Vad som hände:** GODKÄND i alla tre fallen. U+202A–U+202E och U+2066–U+2069 stoppas (rätt). Unicode räknar tolv tecken som styr textriktningen (egenskapen Bidi_Control): de nio som stoppas plus de tre ovan. Testet `test_riktningstecknen_ar_nio` låser listan vid nio. Bankfilen använder samma lista (`_RIKTNINGSTECKEN` i `inlasning_skydd.py`), så enligt koden gäller samma sak bankradernas beskrivning och referens (inte provkört). Matchningsformatet stoppar dem redan, eftersom alla osynliga tecken stoppas där.

**Varför det spelar roll:** U+200F räknas som en höger-till-vänster-bokstav. Enligt Unicodes regler för textriktning visas till exempel U+200F följt av `123 456` som `456 123` i en vanlig vänster-till-höger-text. Ett fakturanummer eller en beskrivning kan alltså se ut som en annan än den är, vilket är precis det SPEC 7 säger ska stoppas ("kan få en text att visas i en annan ordning än den är lagrad").

**Vad som borde hända:** U+200E, U+200F och U+061C läggs till bland riktningstecknen som stoppar filen, och testet räknar tolv.

#### J4. Kort motpartsnamn passar en annan motparts bankrad. Allvar: låg

**Vad jag körde:** ett underlag på 125,00 kr och en bankrad med samma belopp och datum, men en annan text.

| Underlagets motpart | Bankradens beskrivning | Utfall |
|---|---|---|
| `ICA` | `KORTKOP ICA MAXI` | Matchad |
| `LEV` | `KORTKOP LEV A` | Matchad |
| `KORTKOP` | `KORTKOP BUTIK-X` | Matchad |
| `TE` | `LEV T E` | Matchad (orden slås ihop) |
| `ICA MAXI` | `KORTKOP ICA` | Saknat underlag (rätt) |
| `LEV-A` | `LEV A`, `LEVA`, `LEV–A`, `KORTKOP*LEV-A`, `LEV-A/STHLM`, `KORTKOP` + U+200B + `LEV-A` | Saknat underlag (säker riktning: blir ett ärende) |
| `LEV-A` | `lev-a`, `LEV` + U+200B + `-A`, `KORTKOP` + hårt mellanslag + `LEV-A` | Matchad (rätt) |

"Hela ord" stoppar `LEV-TE` mot `LEV-TELE`, som avsett, men inte ett kortare namn som är ett eget ord i ett längre. En fel matchning kräver att beloppet är exakt detsamma på öret och att rätt bankrad för underlaget saknas (finns den blir båda "tvetydig"), så risken är liten. Det är ändå en matchning utan ärende. Förslag: när regelboken finns, jämför motparten mot regelbokens kända motparter, så att en bankrad som också passar en längre motpart blir ett ärende.

#### J5. Kvadratisk tid. Allvar: låg

| Antal bankrader och underlag | Inläsning bank | Inläsning underlag | Matchning |
|---|---|---|---|
| 1 000, olika belopp | 0,01 s | 0,07 s | 0,09 s |
| 4 000, olika belopp | 0,04 s | 0,25 s | 1,23 s |
| 8 000, olika belopp | 0,08 s | 0,85 s | 5,56 s |
| 1 000, samma belopp | 0,01 s | 0,08 s | 5,71 s |
| 2 000, samma belopp | 0,02 s | 0,14 s | 20,26 s |
| 100 000, olika belopp | 1,0 s | 11,7 s | 1 000 rader mot alla underlag: 9,4 s, alltså ungefär **940 s (16 minuter)** för alla |

Tiden fyrdubblas när antalet fördubblas: `_kandidater` går igenom alla underlag för varje bankrad, och normaliserar bankradens text på nytt för varje underlag med samma belopp. Med samma belopp på alla blir 100 000 ungefär 14 timmar (räknat från 2 000). Ett litet företag har några hundra rader i kvartalet, så det spelar ingen roll i dag. I `las_underlag.py` är kontrollen av dubbla momssatser också kvadratisk: 2 000 momsrader 0,07 s, 10 000 rader 1,75 s, 19 000 rader (920 kB, under gränsen 1 MB) 6,6 s för en enda fil. Förslag: sortera underlagen efter belopp en gång (en ordbok från belopp till underlag), och använd en mängd för momssatserna.

#### J6. Filer som hoppas över, rörledning och länkar. Allvar: låg

| Prov | Utfall |
|---|---|
| Mappen har `U-1.json`, `U-2.JSON`, `U-3.json.txt`, `U-4.txt` och `undermapp/U-5.json` | Bara `U-1` läses. **Ingen varning** om de andra |
| AppleDouble-fil `._U-1.json` (macOS skapar sådana på USB-minnen och nätverksdiskar) | Hela perioden STOPPAD (NUL-tecken), med tydligt meddelande |
| `U-1.json` är en namngiven rörledning (FIFO) | **Inläsningen stannar** och väntar för alltid på att något skrivs i den |
| Symbolisk länk till en fil utanför mappen | Filen läses (GODKÄND) |
| Länk till `/dev/zero`, två länkar som pekar på varandra, trasig länk, mapp som heter `U-1.json`, tom fil, bara BOM, 1 000 001 byte, 50 MB | STOPPAD med tydligt meddelande (rätt) |

Ett underlag som hoppas över blir inte fel bokfört: bankraden blir "saknat underlag" efter 7 dagar. Men den som lade dit `U-2.JSON` får aldrig veta varför. Förslag: lista filer som inte läses (som en varning eller ett ärende), stoppa eller hoppa över allt som inte är en vanlig fil innan den öppnas, och bestäm om länkar ska följas.

#### J7. Tomma eller förfalskade perioder. Allvar: låg

| Prov | Utfall |
|---|---|
| `copy.copy`, `copy.deepcopy`, `pickle.dumps` av en Bankperiod | Stoppas (`AttributeError`/`TypeError`) |
| `__dict__`, `bp._rader = ()`, ändra `bp._rader[0]`, konstruktören utan nyckel, underklass till `matcha_period` | Stoppas, med tydligt fel |
| `Bankperiod.__new__(Bankperiod)` till `matcha_period` | **KRASCH** `AttributeError: _rader` i stället för `MatchningFel` |
| `Underlagsperiod.__new__(Underlagsperiod)` till `matcha_period` | **KRASCH** `AttributeError: _underlag` |
| `object.__setattr__` på en tom Bankperiod, med bara en av två rader och fel saldo | GICK: matchningen tog emot den (känt sedan Bankperiod-åtgärden, och stoppas av genvägstestet i kärnkod) |
| `inspect.getmembers(Bankperiod)` och `__set__`, utan texten `_rader` och utan `__setattr__` | GICK: en tom Bankperiod gav ett resultat utan rader och utan ärenden |
| `gc.get_referents` når ordboken bakom en rad i en riktig Bankperiod | GICK: rad 2 ändrades från "saknat underlag" till en insättning, utan att K1 kördes igen |
| `gc.get_referents` på en post i ett `Matchningsresultat` | GICK: ärendets typ ändrades |

I en kopia lades en ny kärnfil `scripts/rapport.py` med `inspect`- och `gc`-sätten: **alla 1 248 tester gröna**. Genvägstestet hittar dem inte, eftersom inga förbjudna namn eller texter används. Åtgärdsavsnittet säger redan att skyddet "kan kringgås med flit", och båda sätten är tydligt avsiktliga. Förslag: förbjud `gc` och `inspect` i kärnan i genvägstestet, och låt `matcha_period` stoppa en period vars inre saknas med `MatchningFel`.

#### J8. Testlucka för fakturanumret i beskrivningen. Allvar: låg

Se uppgift D, mutation D8. Beskrivningen överst i `matcha_bank.py` säger att fakturanumret söks i "beskrivning eller referens". När sökningen i beskrivningen togs bort var alla 1 248 tester gröna. Om J2 rättas som föreslaget (bara referensen) försvinner luckan. Annars behövs ett test.

#### J9. Små brister. Allvar: låg

- **K4 nämner bara ett fel.** Samma fakturanummer med både annat belopp och annat datum ger bara "samma fakturanummer, olika belopp". Med tre underlag A (125 kr, dag 1), B (5 kr, dag 1) och C (5 kr, dag 2) jämförs C bara med A ("olika belopp"), inte med B, som C skiljer sig från bara i datum. Båda underlagen behålls och ärendet finns, så inget går förlorat.
- **"Lägst id" är bokstavsordning.** `U-10` behålls och `U-9` blir "dublett av U-10". Testdatans id har nollor först (`SYNT-U-2025-003`), så det märks inte där.
- **Bedömningsdatum före bankraden.** Bedömningsdatum 2025-02-01 för en bankrad från 2025-03-01 godtas, och raden väntar. Ett bedömningsdatum före bankradens datum är troligen fel och kunde stoppas.
- **NFC och NFD.** "Ö" kan lagras som ett tecken (NFC) eller som "O" plus två prickar (NFD). Ett underlag med id i NFD i en fil vars namn är i NFC gav: "Underlaget 'Ö-1.json' stoppas: filen ska heta … alltså 'Ö-1.json'." De två namnen ser likadana ut. Gamla Mac-diskar (HFS+) sparar filnamn i NFD.
- **Matchningsformatet** godtar U+3164 (en osynlig utfyllnad, som inte räknas som osynligt tecken) som mönster, regelnamnen `swish` och `Swish` i samma fil, och tar tyst bort mellanslag sist i ett mönster (`"BANK AVGIFT "` blir `"BANK AVGIFT"`, alltså en något bredare regel). En `anteckning` med riktningstecken eller NUL skrivet som kod godtas, men används inte. Filen har ingen storleksgräns (2 000 regler lästes utan problem).
- **Momssats över 100 %** godtas (101, 250 och 10^14). Omkastade belopp utan moms och moms (2 500 och 10 000 i stället för 10 000 och 2 500) godtas, eftersom summan stämmer. Båda hör till K5, som inte är byggd.
- **Helt osynliga motparter** (bara U+3164, U+115F eller U+2800) godtas som icke-tomma. Ofarligt för matchningen (de passar ingen vanlig bankrad), men godkännaren ser en tom motpart.

#### J10. SPEC. Allvar: låg (kosmetiskt)

`git diff 7133f15 HEAD -- SPEC.md` visar en enda ändring: "matchningsformat" i SPEC 7, i commit a7cb12f, som stämmer med åtgärdsavsnittet ("Gjort i SPEC.md (samma commit som det här avsnittet)"). Statusraden överst i SPEC listar ändringarna från tidigare samma dag, men inte K4a, K4b, K13, Ö8–Ö10 (7133f15) eller matchningsformatet (a7cb12f). SPEC 7 säger att varje källa har en enda funktion, "idag `las_bankfil` för banken och `las_kassaperiod` för kassan". `las_underlagsperiod` och `sla_ihop_bankperioder` nämns inte (det senare står redan under "Att tänka på" i Bankperiod-åtgärden).

### Kända luckor (inte nya fynd, kommentarer)

- **SPEC K3** saknar 7 dagar och rader som inte kräver underlag. Bekräftat: koden och `matchning.json` har båda, SPEC inget.
- **K4a och K4b heter K4 i koden.** Bekräftat: ärendena har `"kontroll": "K4"`. Vid rättningen bör J9 (bara ett av två fel nämns) tas med, eftersom ett underlag kan vara både K4a och K4b.
- **Bankens avgiftsspecifikation** som öppen fråga saknas i SPEC 11. Bekräftat.
- **Kreditnotor stoppas.** Bekräftat: alla negativa tal stoppas, även `-1` i momssatsen. `-0` läses som 0 och godtas, vilket är ofarligt.
- **K4 ser bara perioden.** Bekräftat: ett underlag daterat 2024-12-31 som är en exakt kopia av ett i januari 2025 ger inget ärende när perioden är januari. Gäller också J1: förslaget om "möjlig dublett" bör jämföra mot arkivet när Ö9 byggs.
- **K17 flaggar inte än.** Bekräftat: texterna lämnas oförändrade och ärendenas texter innehåller inga texter ur bankraderna (`test_saknat_underlag_text_namner_dagarna_men_inga_texter_ur_bankraden` och ärendet "över gräns").

### Uppgift A: övrigt som provades och fungerade

- **Tal:** `1e3`, `1E3`, `1.0`, `12500.00`, `-0.0`, `1e400` (blir oändligt i Python) stoppas som decimaltal. `true`, `"12500"`, `null` och `[12500]` stoppas med sin sort. 15 siffror godtas, 16 stoppas innan talet räknas ut. `0x10`, `+12500` och `012500` är inte giltig JSON och stoppas.
- **Datum:** periodens första och sista dag räknas med, dagen före och efter gör det inte. 0001-01-01 och 9999-12-31 fungerar. 0000-01-01, 2025-02-29 och fel form stoppas. 2024-02-29 godtas. Period baklänges, `None` och fullbreddssiffror stoppas.
- **Id och filnamn:** fel stora och små bokstäver i filnamnet stoppas. Två id som bara skiljer i osynligt tecken eller fullbredd stoppar perioden. Id med snedstreck stoppas. Id `.` i filen `..json` godtas (ofarligt).
- **K4:** tre likadana ger två ärenden "dublett av U-1". Dublett av ett underlag som behölls av K4a fungerar. Typ och momsrader spelar ingen roll för dubbletten (som avsett).
- **moms:** tom lista stoppas, dubbla satser stoppas, momsrad som lista och `moms` som objekt stoppas.
- **Texter:** U+202E skrivet som kod stoppas. Andra formattecken (U+2060, U+FFF9, taggtecken U+E0041) godtas, som SPEC 7 säger, och ska visas synligt i rapporten.

### Uppgift B: övrigt som provades och fungerade

- **Fakturanummerregeln** gjorde aldrig två matchningar mot samma underlag. När ett utpekat underlag också passade en annan bankrad blev båda "tvetydig". Två bankrader med samma fakturanummer (dubbelbetalning) blev båda "tvetydig". Två fakturanummer i samma text gav "tvetydig". K4b-paret (samma fakturanummer, samma belopp, olika datum) blev "tvetydig".
- **Tidsfönster** (testbutikens format): faktura dag 0 och dag 40 matchas, dag 41 och dagen före inte. Kvitto dag 3 matchas, dag 4 inte. **Sju dagar:** dag 7 väntar, dag 8 blir ärende.
- **Flera med samma belopp:** två underlag och en rad, en rad och två underlag, och korsvis passande par blev alla "tvetydig".
- **Regler:** en utgående rad med Swish-text och en inkommande rad med avgiftstext kräver underlag. Avgift exakt 250,00 kr kräver inget underlag, 250,01 kr blir "över gräns". 0 kr passar ingen regel. Bara referensen eller dubbla mellanslag i beskrivningen räcker inte. Mellanslag först i bankfilen tas bort av `las_bankfil`, så `" SWISH-1"` räknas som Swish (rätt). En Swish-insättning på 1 000 000 kr kräver inget underlag (ingen gräns för pengar in, öppen fråga för Hugo sedan förra åtgärden).
- **Invarianter och ordning:** kvartalets 395 bankrader kastades om slumpvis **240 gånger** (skrevs som en ny bankfil med nya radnummer och saldon och lästes med `las_bankfil`), med fyra bedömningsdatum. **Alla 240 gav exakt samma resultat** som originalordningen (jämfört utan radnummer, id och saldo). Dessutom 200 små påhittade fall med många lika belopp, fakturanummer och motparter, var och ett omkastat 10 gånger: **0 skillnader**. I alla körningar fanns varje bankrad i exakt en grupp, varje underlag i högst en matchning, och matchade plus oavstämda var precis periodens underlag.
- **Matchningsformatet** (48 prov på filen, varav 12 godtogs; av dem är `-0` som antal dagar (blir 0) ofarligt och resten nämns här eller i J9): dubbla nycklar överst och i en regel, nästling 990–200 000, tal med 16 och 100 000 siffror, `1e5`, `NaN` och `Infinity` som gräns och tidsfönster, osynliga tecken och kyrilliska bokstäver i nycklar, U+200B, U+202E, U+200F och NUL i mönster, okända nycklar, utgående regel utan gräns, inkommande regel med gräns, gräns som text och `true`, riktning `UT` och `ut `, tomt mönster och bara mellanslag, krockande regler, en tredje underlagstyp, UTF-16, Windows-1252, NUL-byte och styrtecken: alla STOPPADE med tydligt meddelande. Testbutikens fil, UTF-8 med BOM, tom regellista och gränsen 999 999 999 999 999 godtas (rätt).

### Uppgift C: kontroll mot reglerna

| Kontroll | Resultat |
|---|---|
| Företags- och motpartsnamn i `scripts/` (utom `tests/`) | Inga. Sökt efter testbutikens namn, motparter, kassaregister, banknamn och alla mönster i `matchning.json` (`AVR-`, `SWISH-`, `INS-`, `AVG-`, `BET-KORT`, `KORTKOP`, `BANK AVGIFT`). Bara de allmänna orden "kontant" och "Swish-betalningar" i kommentarer. Tal i de nya filerna: 200, 15, 366 (gränser), 40 (hur mycket text som visas i ett fel), 10 (i `10 ** 15`), och exempel i kommentarer. Inga momssatser, konton, belopp eller antal dagar ur `matchning.json` |
| Flyttal | Inga. "float" och "decimaltal" står bara i tabeller över sorter som stoppas. Ingen division i de nya filerna |
| Nätverksanrop och körning av kommandon | Inga. Importerna i hela kärnan är `csv`, `datetime`, `hashlib`, `json`, `re`, `unicodedata`, `pathlib`, `types`, `typing` och projektets egna moduler. `open` bara på två ställen i `inlasning_skydd.py`, för läsning |
| Dolda tecken | Inga i `scripts/` utom `tests/`. I testerna bara synliga fullbreddsbokstäver (med flit, för normaliseringen). I hela kopian (140 filer) inga riktningstecken, ingen BOM, inga CR-radslut. Ett hårt mellanslag (U+00A0) i GRANSKNING.md rad 1025, i en åtgärdstext, ofarligt |
| SPEC sedan 7133f15 | Bara "matchningsformat" i SPEC 7 (a7cb12f). Stämmer med åtgärdsavsnittet. Se J10 om statusraden |
| Antal tester enligt slutrapporterna | Egen körning i kopior av varje commit: **1 025** (7133f15), **1 037** (ca6867d, del B), **1 203** (2817f42, del C), **1 209** (e3a618c, Bankperiod), **1 248** (c46142f, gränsen). Alla stämmer med åtgärdsavsnitten, liksom "166 nya" och "39 nya" |
| Commits | Del A, B och C är 7133f15, ca6867d och 2817f42, som avsnittet säger. Filerna i e3a618c och c46142f stämmer med vad avsnitten säger är ändrat och inte ändrat (SPEC, testdatan och facit orörda i båda) |

### Uppgift D: stickprov på mutationstesterna

I den rena kopian togs en kontroll i taget bort eller gjordes svagare, hela sviten kördes, och ändringen togs tillbaka. Fjorton mutationer, de flesta andra än byggarens egna.

| Nr | Fil | Borttagen eller svagare kontroll | Röda tester |
|---|---|---|---|
| D1 | las_underlag.py | Negativa tal godtas | 4 (`test_negativa_tal_stoppas`) |
| D2 | las_underlag.py | Dubbla id jämförs utan normalisering | 1 (`test_samma_id_i_tva_filer_stoppar_perioden`) |
| D3 | las_underlag.py | K4 jämför fakturanumret utan normalisering | 5 (`test_k4_jamfor_motpart_och_fakturanummer_efter_normalisering`) |
| D4 | las_underlag.py | K13 borttagen | 7 (bland dem `test_summan_av_momsraderna_ska_vara_beloppet` och fuzzen) |
| D5 | las_underlag.py | Samma momssats på flera rader godtas | 1 (`test_trasiga_momsrader_stoppas[samma_sats_tva_ganger]`) |
| D6 | las_underlag.py | Periodens sista dag räknas inte med | 1 (`test_perioden_raknar_med_forsta_och_sista_dagen`) |
| D7 | las_underlag.py | K4a och K4b ger inga ärenden | 3 |
| **D8** | matcha_bank.py | Fakturanumret söks bara i referensen, inte i beskrivningen | **0** (se J8) |
| D9 | matcha_bank.py | Fakturanumret avgör bara vid tre kandidater eller fler | 7 (bland dem kvartalets tester) |
| D10 | matcha_bank.py | Tidsfönstrets sista dag räknas inte med | 3 (`test_tidsfonstret_per_underlagstyp`) |
| D11 | las_matchningsformat.py | Krockkontrollen ser bara på referensen | 1 (`test_regler_som_aldrig_passar_samma_bankrad_godtas`) |
| D12 | las_matchningsformat.py | 0 dagar godtas inte | 2 |
| D13 | matcha_bank.py | Motparten får bara vara ett ord | 2 (`test_motparten_i_bankradens_text_matchas`) |
| D14 | matcha_bank.py | Regelns referens får stå var som helst, inte bara först | 2 (bland dem fuzzen) |

13 av 14 gav minst ett rött test. D8 är en testlucka (J8). Flera kontroller fångas av bara ett test (D2, D5, D6, D11), men det räcker för att en borttagning ska märkas.

### Testsviten

Kommando: `.venv/bin/python -B -m pytest -p no:cacheprovider -q scripts/tests`

Resultat: **1 248 passed**, 0 misslyckade, i projektet och i den rena kopian, före och efter mutationstesterna. `git status` visade inga ändrade filer innan det här avsnittet skrevs.

**Kommandon.** Jag använde listans kommandon och fil-verktygen. Kopior, provskript och mutationer låg bara i den tillfälliga mappen, och Python kördes bara genom testsvitens kommando, inifrån kopiorna. Utanför listan i SPEC 7.1, av misstag och bara för att läsa: `.venv/bin/python --version` en gång, `sed -n` och `cut` för att visa några rader, `uniq -c` efter `sort` för att räkna importer, `echo` för rubriker i en sökning, och `|| true`. `cd` användes också till projektmappen (listan tillåter `cd` bara till en tillfällig mapp), alltid för att köra listans kommandon där. Inget av det ändrade något.

### Beslut som behövs från Hugo

1. **J1 (hög):** ska K4 ge ett ärende "möjlig dublett" när motpart, belopp och datum är samma men fakturanumret skiljer? Rekommendation: ja, innan konteringen byggs, och samtidigt med K4a/K4b-namnen och Ö9 (arkivet).
2. **J2:** ska fakturanumret bara avgöra när bankradens referens är exakt fakturanumret? Rekommendation: ja. Då försvinner också testluckan J8.
3. **J3:** ska U+200E, U+200F och U+061C stoppa filen, som de nio andra riktningstecknen? Rekommendation: ja, det är vad SPEC 7 redan säger.
4. **J4–J10:** små rättelser som kan samlas: varning för filer som inte läses och stopp för sådant som inte är vanliga filer (J6), `MatchningFel` för tomma perioder och `gc`/`inspect` i genvägstestet (J7), snabbare kandidatsökning (J5), statusraden och SPEC 7 (J10). Ingen av dem är bråttom.

## Åtgärder efter granskning 5

Gjort i en egen session, i två commits: SPEC.md (del A, commit d667ab3) och koden (del B). Uppgiften kom från Hugo, som därmed också godkände texten i SPEC. Ingen granskares text ovan är ändrad. Testdatan, facit och `foretag/` är inte ändrade.

**Ord som används nedan.** En **dubblett** är samma underlag inläst två gånger. Ett **förväxlingstecken** ser ut som ett annat tecken men är ett annat tecken i datorn, till exempel ett tankstreck (–) i stället för ett bindestreck (-), eller ett kyrilliskt А i stället för ett latinskt A. Ett **skriftsystem** är en sorts bokstäver: latinska (som svenska), kyrilliska (som ryska), grekiska och så vidare. **Normalisering** är att göra om en text till en fast form innan den jämförs, så att texter som ser likadana ut blir lika. En **symbolisk länk** är en genväg i en mapp som pekar på en annan fil. En **rörledning** (FIFO) ser ut som en fil, men den som läser den väntar tills något skrivs i den. Ett **mutationstest** är att ta bort en kontroll i en kopia av koden och se att minst ett test slår larm.

### Del A: SPEC.md (commit d667ab3)

| Punkt | Ändring |
|---|---|
| J3 | SPEC 7: de **styrande** riktningstecknen (U+202A–U+202E och U+2066–U+2069) stoppar filen. De **milda riktningsmärkena** U+200E, U+200F och U+061C godtas, eftersom de förekommer i vanlig arabisk och hebreisk text, men ska visas synligt i rapporten. Koden gjorde redan så, så den är inte ändrad, och testet `test_riktningstecknen_ar_nio` stämmer nu med SPEC |
| J10 | SPEC 7: "en enda funktion per källa" nämner nu `las_bankfil`, `las_kassaperiod`, `las_underlagsperiod` och `matcha_period`. Statusraden överst nämner ändringarna i 7133f15, a7cb12f och den här uppdateringen |
| K3 | Ett saknat underlag blir ett ärende först när det har gått mer än ett antal dagar efter bankradens datum (ett värde per företag i `matchning.json`, testbutiken har 7). Vissa bankrader kräver inte underlag och stäms av på annat sätt (kortinlösen, Swish och kontantinsättningar mot Z-rapporterna i K10). Regler för utgående rader som slipper underlag måste ha en högsta summa per bankrad |
| Ö11 | Ny öppen fråga: bankens avgiftsspecifikation ska bli ett riktigt underlag med en egen dokumenttyp. Ö11 och inte Ö6, eftersom Ö6 inte används och ett återanvänt nummer kan förväxlas med en gammal fråga |

Testsviten efter del A: **1 248 passed**, 0 misslyckade.

### Del B: koden

| Fynd | Rättelse | Test |
|---|---|---|
| J1 | Ny kärnfil `scripts/normalisering.py` med `normalisera_for_jamforelse`: Unicode-normalisering (NFKC), alla bindestreck och tankstreck (Unicode-kategori Pd) och minustecknet U+2212 blir "-", blanksteg och osynliga tecken (kategori Cc och Cf) tas bort, och stora och små bokstäver räknas som samma. K4 (`las_underlag.py`) jämför motpart och fakturanummer med den, och fakturanummerregeln i matchningen jämför bankradens ord och fakturanumret med den. Texten i underlaget ändras aldrig | `test_las_underlag.py`: `test_k4_dublett_med_annat_bindestreck_blanksteg_eller_osynligt_tecken` (14 fall: sex sorters streck, extra blanksteg och osynligt tecken i fakturanumret, och streck, blanksteg, osynligt tecken och fullbredd i motparten). `test_matcha_bank.py`: tankstreck och minustecken i `test_fakturanumret_avgor_bara_som_ett_helt_ord` |
| J1 | Ett ord i motpart eller fakturanummer som blandar latinska bokstäver med bokstäver från ett annat skriftsystem stoppar underlaget: "… 'motpart' har ordet 'LEV-А', som blandar latinska bokstäver med bokstaven U+0410 (CYRILLIC CAPITAL LETTER A) från ett annat skriftsystem. …". Ett ord är det som står mellan blanksteg. Texten normaliseras (NFKC) först, så att fullbreddsbokstäver räknas som latinska. Skriftsystemet tas ur bokstavens namn i Unicode (första ordet, till exempel LATIN eller CYRILLIC), eftersom Python inte har något eget sätt att slå upp det | `test_ord_som_blandar_latinska_och_andra_bokstaver_stoppas` (4 fall), skydd: `test_ord_med_ett_enda_skriftsystem_godtas` (8 fall, bland dem "Москва Трейдинг", "Café Москва" och "ΟΜΕΓΑ ΑΕ") |
| J1 | Ett fakturanummer får efter normaliseringen bara innehålla a–z, siffror, bindestreck, snedstreck, punkt och understreck. Annat stoppar underlaget, och meddelandet visar tecknet som det står i filen, med kod och namn | `test_fakturanummer_med_annat_an_ascii_stoppas` (9 fall, bland dem é, Å, kyrilliskt Ғ, #, :, + och bråkstreck), skydd: `test_fakturanummer_med_tillatna_tecken_godtas_som_de_star` (10 fall) |
| J1 | En dubblett med förväxlingstecken hamnar aldrig som ett oavstämt underlag utan ärende: antingen blir den ett K4-ärende, eller så stoppas underlaget med tydligt fel | `test_matcha_bank.py`: `test_dublett_med_forvaxlingstecken_blir_aldrig_oavstamd_utan_arende` (9 fall, med en bankrad som betalar originalet) |
| J2 | Fakturanumret får bara avgöra mellan flera kandidater när det (efter normaliseringen) står som ett helt ord i bankradens referens eller beskrivning, har minst 5 tecken (`_FAKTURANUMMER_MINST_TECKEN`), inte är lika med eller en del av underlagets motpart och inte är en del av en annan kandidats fakturanummer. Står flera kandidaters nummer i texten blir det "tvetydig", som förut | `test_fakturanumret_avgor_bara_som_ett_helt_ord` (12 fall), `test_kort_fakturanummer_avgor_inte` (granskarens 10 och 11), `test_fakturanumret_ska_ha_minst_fem_tecken` (3), `test_fakturanummer_som_ar_motpartens_namn_avgor_inte` (4, med granskarens fall), `test_fakturanummer_som_ar_en_del_av_ett_annat_avgor_inte` (4, med granskarens 761-fall som 4711), `test_samma_fakturanummer_pa_tva_kandidater_avgor_inte` |
| J5 | `matcha_period` stoppar med `MatchningFel` om det finns fler än 20 000 bankrader eller underlag (`_HOGST_ANTAL`). En kommentar i koden säger att gränsen ska tas bort när matchningen har gjorts snabbare | `test_fler_an_20_000_bankrader_stoppas` (20 001 stoppas, 20 000 godtas), `test_fler_underlag_an_gransen_stoppas` (med en lägre gräns, så att testet går fort) |
| J6 | `las_underlagsperiod` stoppar perioden om mappen innehåller något annat än vanliga filer som slutar på exakt `.json`: undermappar, symboliska länkar, rörledningar, `U-2.JSON`, `.txt`, dolda filer. Bara `.DS_Store` hoppas över (`IGNORERADE_FILER`). Varje sak undersöks med `lstat`, som inte följer länkar och inte öppnar något | `test_mappen_far_bara_innehalla_underlag` (7 fall, ersätter `test_undermappar_och_andra_filer_lases_inte`, som krävde det gamla beteendet), `test_ds_store_ignoreras`, `test_symboliska_lankar_foljs_aldrig` (4), `test_rorledning_far_inte_inlasningen_att_stanna` (läser i en egen tråd och ger upp efter 5 sekunder) |
| J7 | En `Bankperiod` eller `Underlagsperiod` som skapats med `__new__`, utan inläsningsfunktionen, ger `MatchningFel` ("… är tom eller trasig …") i stället för `AttributeError` | `test_tom_bankperiod_eller_underlagsperiod_ger_matchningfel` |
| J8 | Fakturanumret i bankradens beskrivning prövas nu | `test_fakturanumret_i_beskrivningen_avgor`, och ett fall i `test_fakturanumret_avgor_bara_som_ett_helt_ord` |
| J9 | K4-ärendena har kontrollerna K4 (dublett), K4a (olika belopp) och K4b (olika datum). Skiljer både belopp och datum heter kontrollen "K4a och K4b" och texten "samma fakturanummer, olika belopp och datum" | `test_k4_namner_bade_belopp_och_datum_nar_bada_skiljer`, `test_k4_dublett_heter_fortfarande_k4`, och K4a/K4b i de två befintliga testerna och i `test_k4_dublett_av_det_andra_underlaget_med_samma_fakturanummer` |
| J9 | Ett bedömningsdatum före någon bankrads transaktionsdag stoppar matchningen: "Bedömningsdatumet 2025-02-28 ligger före transaktionsdagen 2025-03-01 för bankraden med radnummer 2. …". Inga texter ur bankraden visas. Samma dag godtas | `test_bedomningsdatum_fore_en_bankrad_stoppas` |

**Beslut som togs i uppgiften (bör bekräftas av Hugo).**

1. **Kyrilliskt А i en dubblett stoppas i stället för att bli ett K4-ärende.** Uppgiften sa både att ett blandat ord ska stoppas och att dubbletten med kyrillisk a ska bli ett K4-ärende. Det går inte att göra båda: "LEV-А" är ett blandat ord. Det stoppas, vilket också uppfyller kravet att dubbletten aldrig blir ett oavstämt underlag utan ärende. Att se att två olika bokstäver *ser* lika ut skulle kräva en tabell över förväxlingsbara tecken, som inte ingick.
2. **"K4a och K4b"** när både belopp och datum skiljer, i stället för två ärenden för samma underlag.
3. **Bankradens datum är transaktionsdagen** i kontrollen av bedömningsdatumet, som i resten av matchningen.
4. **En ny kärnfil**, `normalisering.py`, eftersom både `las_underlag.py` och `matcha_bank.py` behöver normaliseringen och `las_underlag.py` bara ska ha en offentlig funktion.
5. **"Ett helt ord" är ett ord mellan blanksteg.** Ett skiljetecken intill numret (till exempel "F-1001.") gör att det inte är ett helt ord, och raden blir "tvetydig". Det är den säkra riktningen.
6. **Ett nummer som inte får avgöra räknas ändå** när det avgörs om flera kandidaters nummer står i texten. Står både "F-1001" och ett kort "10" i texten blir det "tvetydig".

**Ändrade befintliga tester.** Alla ändringar beror på rättelserna:

- `test_las_underlag.py`: `test_undermappar_och_andra_filer_lases_inte` är ersatt (J6). I `test_k17_instruktion_i_underlaget_ar_vanlig_text` står instruktionen i fakturanumret nu utan Ö (`INSTRUKTION_ASCII`), eftersom Ö inte är tillåtet i ett fakturanummer (J1). Motparten har kvar texten med Ö.
- `test_matcha_bank.py`: testerna för fakturanummerregeln använder nummer med minst 5 tecken (`F-1001` i stället för `F-1`), annars avgör inte numret (J2). Bedömningsdatum före en bankrad är borttagna eller utbytta (J9): `test_saknat_underlag_blir_arende_forst_efter_antalet_dagar_i_formatet` provar inte längre 2025-02-01, `test_varje_bankrad_i_testdatan_finns_i_exakt_en_grupp` använder datum från 2025-03-31, och fuzzen har fler sena datum och kontrollerar att inget resultat har en bankrad efter bedömningsdatumet. `test_kvartalet_fore_sju_dagar_ger_inget_arende_bara_att_raden_vantar` använder nu februarifilen fram till och med rad 85 (läst med `las_bankfil`, utgående saldo efter rad 85), eftersom hela kvartalet med bedömningsdatum i februari nu stoppas. Testet visar också att det stoppas.

**Medvetet inte rättat (punkt 12 i uppgiften).** Dessa väntar med flit:

- **J4** (ett kort motpartsnamn passar en annan motparts bankrad). Det kräver regelbokens lista över kända motparter, som inte är byggd. En fel matchning kräver dessutom exakt samma belopp och att rätt bankrad saknas.
- **J9, matchningsformatet:** formatet godtar en osynlig utfyllnad (U+3164) som mönster och regelnamnen `swish` och `Swish` i samma fil. Formatet skrivs av Vera Labs och ska flyttas till en skyddad mapp i spärrsteget, så risken är liten, och en utfyllnad i ett mönster gör bara att regeln aldrig passar (raden kräver då underlag, den säkra riktningen).
- **J9, NFC/NFD-filnamn:** "Ö" kan sparas på två sätt, så meddelandet kan visa två namn som ser likadana ut. Filen stoppas ändå, så inget blir fel bokfört. Bara meddelandet är otydligt.
- Inte heller med i uppgiften och därför inte rättat: "lägst id" som bokstavsordning, momssats över 100 % och helt osynliga motparter (J9), `gc` och `inspect` i genvägstestet (J7), och en snabbare matchning (J5, bara gränsen är byggd).

**Kvar att tänka på.**

- **J1 är inte helt stängt.** Kvar är förväxlingar inom samma skriftsystem: `F-1` och `F-l` (litet L), `F-1` och `F1` eller `F-01`, och `LEV-A` och `LEV-A AB`. Granskarens förslag, ett ärende "möjlig dublett" när motpart, belopp och datum är samma men fakturanumret skiljer, är fortfarande ett beslut för Hugo.
- **Ett kyrilliskt ord för sig själv** godtas, eftersom bara ord som blandar stoppas. Motparten "LEV А" (med mellanslag och kyrilliskt А) blir därför inte stoppad, och efter normaliseringen är den inte samma som "LEV A". En sådan dubblett kan alltså fortfarande bli oavstämd utan ärende. Ett fakturanummer kan inte ha det problemet, eftersom det bara får ha a–z.
- Mappen undersöks med `lstat` innan filerna öppnas. Byts en fil mot en länk eller en rörledning precis mellan undersökningen och läsningen märks det inte. Det kräver att någon gör det med flit, i rätt ögonblick.

**Så bevisades testerna.** De nya testfilerna kördes mot koden från commit d667ab3 (före rättelserna) i en kopia utanför projektet: **64 röda och 1 282 gröna**, alla röda av rätt skäl. Det gamla K4 gav "K4" i stället för "K4a"/"K4b" och behöll dubbletterna med streck och förväxlingstecken utan ärende. Mappens filer hoppades över utan fel, länkarna följdes och inläsningen stannade vid rörledningen. Fakturanummerregeln avgjorde på korta nummer, på motpartens namn, på en del av ett annat nummer och på ett nummer uppdelat på flera ord. Matchningen godtog ett tidigt bedömningsdatum och fler än gränsen, och gav `AttributeError` för tomma perioder. Under bygget rättades två fel i testerna, inte i koden: ett fall med kommatecken i referensen (det förstörde själva bankfilen) togs bort, och J5-testerna gjordes om så att de slår larm på beteendet och inte på att namnet `_HOGST_ANTAL` saknas.

**Mutationstest.** I 40 kopior utanför projektet togs en ny kontroll bort eller gjordes svagare, och hela sviten kördes. Alla 40 gav minst ett rött test.

| Nr | Borttagen eller svagare kontroll (i en kopia) | Röda tester |
|---|---|---|
| n01 | Normaliseringen: bindestreck och tankstreck (Pd) blir inte "-" | 12 |
| n02 | Normaliseringen: minustecknet blir inte "-" | 5 |
| n03 | Normaliseringen: blanksteg tas inte bort | 8 |
| n04 | Normaliseringen: osynliga tecken tas inte bort | 7 |
| n05 | Normaliseringen: ingen NFKC | 3 |
| n06 | Normaliseringen: stora och små bokstäver skiljs | 188 och 9 fel |
| n07 | K4 jämför fakturanumret med kassans gamla normalisering | 9 |
| n08 | K4 jämför motparten med kassans gamla normalisering | 4 |
| n09 | Fakturanumrets tecken (a–z m.m.) kontrolleras inte | 10 |
| n10 | Fakturanumrets tecken prövas utan normaliseringen | 28 |
| n11 | Blandade ord i motparten stoppas inte | 4 |
| n12 | Blandade ord i fakturanumret stoppas inte | 1 |
| n13 | Blandade ord prövas utan NFKC | 2 |
| n14 | Alla icke-latinska bokstäver stoppas, även ord helt på ett annat språk | 4 |
| n15 | Mappen: bara ändelsen prövas, inte att det är en vanlig fil | 5 |
| n16 | Mappen: `.JSON` godtas | 2 |
| n17 | Mappen: `stat` i stället för `lstat` (länkar följs) | 4 |
| n18 | Mappen: `.DS_Store` hoppas inte över | 1 |
| n19 | Mappen: annat hoppas över tyst, som förut | 14 |
| n20 | Fakturanumret får stå som en del av ett ord | 7 |
| n21 | Ingen minsta längd | 3 |
| n22 | Minsta längd 6 i stället för 5 | 1 |
| n23 | Fakturanummer som är motpartens namn får avgöra | 3 |
| n24 | Bara exakt motpartens namn stoppas, inte en del av det | 1 |
| n25 | En del av en annan kandidats nummer får avgöra | 1 |
| n26 | Fakturanumret söks inte i beskrivningen (J8) | 2 |
| n27 | Fakturanumret söks inte i referensen | 15 |
| n28 | Bankradens ord normaliseras med kassans gamla normalisering | 2 |
| n29 | Första av flera nummer i texten avgör | 1 |
| n30 | Ingen gräns för bankrader | 2 |
| n31 | Ingen gräns för underlag | 1 |
| n32 | Exakt på gränsen stoppas (`>=`) | 2 |
| n33 | Gränsen 20 001 i stället för 20 000 | 1 |
| n34 | Tom Bankperiod ger `AttributeError` | 1 |
| n35 | Tom Underlagsperiod ger `AttributeError` | 1 |
| n36 | Bedömningsdatum före en bankrad godtas | 3 |
| n37 | Bedömningsdatum samma dag som bankraden stoppas (`>=`) | 7 |
| n38 | K4a heter K4 | 1 |
| n39 | K4b heter K4 | 3 |
| n40 | Både belopp och datum: bara K4a nämns | 1 |

**Kommandon utanför den fasta listan.** Av misstag, och bara för att läsa: `sed -n` och `head -c` en gång var (båda på en tom fil, utan verkan), `uniq -c` efter `sort` för att räkna testdatans fakturanummer och `cut -c` för att korta felrader. I mutationstestet kördes listans kommandon efter varandra med `;` i ett kommando, med en variabel för kopiornas mapp. Kopiorna gjordes med `git archive`, `tar` och `cp -R` i den tillfälliga mappen, och ändringarna i kopiorna gjordes med fil-verktygen. Inget av det ändrade något i projektet.

Testsviten efter del B: **1 346 passed**, 0 misslyckade (1 248 före, alltså 98 fler).
