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
