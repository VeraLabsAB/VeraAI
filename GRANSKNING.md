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
