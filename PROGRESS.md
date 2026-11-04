# PROGRESS – Veras bokföringsagent

Uppdaterad 2026-11-04. Specifikation: `SPEC.md`. Byggordning: `DESIGN-regelbok.md` avsnitt 7.
Byggplan för hela produkten: `BYGGPLAN.md` (Hugos beslut 2026-10-29, rättad 2026-10-29 efter den här filen). Steg 12: vakten installerades på Hugos dator 2026-10-28. Steg 12 är klart igen 2026-10-29: den nya versionen av inställningsfilen, där läget Auto tillåts igen (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen"), är installerad och kontrollerad (`GRANSKNING.md`, "Kontroll efter bytet av inställningsfil, 2026-10-29"). Auto får användas på Hugos dator, med villkoren tills steg 15 är klart. Caspers dator är steg 14. Spärrtestet är klart och grönt (2026-10-29). **Steg 13 är klart**: provet med en vakt som fallerar (steg 8 i kontrollen) är gjort och grönt 2026-10-29. **Q2, Q2b, Q3 och Q4 är klara och granskade** (Q2: 3e3c18c och d7d38e0, Q2b: 1dcf769, Q3: bd851ba, Q4: 2bc9762, Hugos beslut 2026-10-29 om Q2–Q4). **Granskning 21 (3bbcbe4) är gjord och grön**: inget allvarligt och inget på nivån medel, tre låga fynd (L1–L3) som är rättade i dokumentationen 2026-10-29 (L3 som exempel i SPEC Ö5). **Q7 är stängd**: pusha som det är, historiken skrivs inte om, och repot på GitHub förblir privat (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd"). Pushat 2026-10-29. **Besluten inför uppgift 4 (B1–B3)** står i `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4", och **D13 och D14** under "D13 och D14 beslutade" (baec52b). **Uppgift 4 är byggd** 2026-10-29 (4269f76, f6ed99e och e4cc538): flöde a, b och e med K5 och K8 i `scripts/konteringsfloden.py`, och den nya nyckeln `bokforing` i regelboken (Hugos OK i chatten 2026-10-29). Granskad i granskning 22 (e4d8cd7), gult: P1 och P2 kvar, 7 frågor väntar på Hugo. Pushad (`main` på GitHub står vid d127c3e). **Hugos beslut efter uppgift 4 (a–f)** står i `GRANSKNING.md`, "Beslut efter uppgift 4 (2026-10-29)" (48e7ed3), och är byggda 2026-10-29 i ded669d (c: nyckeln `flode`, reserverade namn och regeln `bankens-avgifter`) och 5753890 (f och e). Pushade 2026-10-29 (`main` på GitHub står på 7d8cae9). **Hugos beslut 2026-10-30 om granskning 22** (`GRANSKNING.md`, "Hugos beslut 2026-10-30 om granskning 22") är byggda 2026-10-30: K5, K7 och K8 ligger i `skapa_konteringsforslag` (P1), ett underlag som K4 flaggar får inget förslag och K4-ärendet följer med (P2), reserverade ord stoppar alla namn i konfigurationen vid exakt träff (Öppet 27, stängd) och `flode` stoppas på regler för pengar in (Öppet 28, stängd). **Granskade i granskning 23** (269d641, gult): P1 hade en lucka (K5 och K8 prövades mot förslagets regel, inte underlagets), P3 två namn som inte prövades. **Hugos beslut 2026-10-30 om granskning 23** (`GRANSKNING.md`, "Hugos beslut 2026-10-30 om granskning 23") är byggda 2026-10-30 i 13126d2 (P1) och 35afa8b (P3 och Öppet 29, stängd), och **granskade i granskning 24** (6dfcdcd, grönt): byggda som besluten säger, inget blockerande. **Steg 22 är klart** 2026-10-30: granskat i granskning 23 och 24 (Hugos beslut 2026-10-30 om granskning 24, beslut 3). **Öppet 31 är rättad** 2026-10-30 i bbb183a (förslagets regel ska vara underlagets egen regel, beslut 1) och **granskad i granskning 25** (grönt: byggd som beslutet säger, inget blockerande; en lucka inom regeln kvar som Öppet 32, väntar på beslut), och **Öppet 30 är stängd** (beslut 2). **Öppet 32 är rättad** 2026-10-30 (kostnadsraden i ett förslag med underlag står på det konto K5 ger för momssatsen, annars stoppas förslaget, Hugos beslut 2026-10-30 om granskning 25, beslut 1; committad 2026-10-30 som steg 91 i BYGGPLAN.md) och **granskad i granskning 26** (gult: byggd som beslutet säger, inget blockerande; ett hål kvar i samma familj, kostnaden räknad ur `belopp_ore` i stället för `underlag_ore`, som Öppet 34, väntar på beslut), och **Öppet 31 räknas som granskad och klar** (beslut 2). **Hugos beslut 2026-10-30 om byggsessionen för Öppet 32** (`GRANSKNING.md`): momsraden är Öppet 33, ett eget steg efter Öppet 32 (a), och Öppet 32 och Öppet 26 är steg 91 och 92 (b). **Öppet 33 och Öppet 34 är byggda** 2026-10-30 som steg 93 i BYGGPLAN.md (Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg"; commit 7801a64: momsraden står på kontot för ingående moms, beloppet att betala räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad, och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`), och **granskade i granskning 27** (gult: byggda som beslutet säger, H7 och de fyra LUCKA-proven stoppas; två hål kvar i en ny familj, beloppet i debet på leverantörsskulderna utan bankrad, som Öppet 35, väntar på beslut). **Regeln om högst en rad är beslutad av Hugo 2026-10-31** (uppdraget till granskning 27, `GRANSKNING.md`). **Öppet 35 är rättad** 2026-10-31 som steg 94 i BYGGPLAN.md (Hugos beslut 2026-10-31 om granskning 27; commit 109fdcf: ett underlags `belopp_ore` står i debet bara när förslaget har en bankrad, och i kredit bara när underlagets delar inte står i kredit), och **granskad i granskning 28** (2026-11-04, gult: byggd som beslutet säger, h1 och h2 stoppas; kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en annan fakturas betalning eller en bankrad på fel konto, Öppet 36, väntar på beslut; ett underlag med belopp 0 stannar hela körningen, Öppet 37, utanför steget). **Steg 94 är granskat och klart** (Hugos beslut 2026-11-04 om granskning 28, beslut 3). **Öppet 36 är rättad** 2026-11-04 som steg 95 i BYGGPLAN.md (Hugos beslut 2026-11-04 om granskning 28, beslut 1, granskarens (a); commit 0708667: varje rad med ett underlags `belopp_ore` i debet har en egen rad på bankkontot i kredit med samma belopp ur en bankrad, och varje bankkontorad räknas bara en gång). Granskarens b1 och b3 stoppas. b2 godtas: konteringen är identisk med flöde a:s två förslag i samma förslag (Hugos beslut 2026-11-04, 1); att en faktura och en annan fakturas betalning står i samma förslag ska kontrolleras med en redovisningskonsult (Öppet 38). **Öppet 37 är steg 96** (beslut 2), inte byggd. Nästa steg: se "Nästa steg i byggordningen". Caspers dator installeras i helgen (vecka 44, Öppet, punkt 15).

Granskningarna och rättelserna efter dem: `GRANSKNING.md`.

Projektet är i **fas 0** (SPEC avsnitt 9): ett testföretag, Syntet Testbutik AB, hela vägen från
underlag till godkänd rapport. Inget i koden kan i dag bokföra något.

Testsviten: **4 443 passed**, 0 misslyckade (körd senast 2026-11-04 i steg 95, i projektmappen med kommandot i
SPEC 7.1: 4 434 från förut och 9 från steg 95 i `scripts/tests/test_beslut_granskning_28.py`). Sedan installationen
2026-10-28 körs den med `'/Library/Application Support/ClaudeCode/vera/venv/bin/python'`. Projektets `.venv` är
borttagen.

**Regler tills vakten är installerad** (Hugos beslut 2026-10-28 efter granskning 15, ändrade 2026-10-28 kväll):

- ~~Varje session körs i läget **Manual** tills vakten är installerad.~~ Granskning 15 kördes av misstag i läget
  auto. **Sessionerna får köras i auto redan
  före vakten** (Hugos beslut 2026-10-28 kväll). Villkor: Shop and Gos riktiga underlag ligger utanför `~/VERA`,
  varje session börjar och slutar med `git status`, och granskning 18 kontrollerar att inget utanför projektet
  har ändrats.
- **Sandlådan görs direkt efter installationen** (Öppet, punkt 4).
- **Stoppregel:** vakten installeras när en oberoende granskning inte hittar något allvarligt fynd, eller fynd
  på nivån medel, som inte är rättat. Låga fynd går till "Öppet".

## Läge 2026-11-04, Öppet 36 byggd

Steg i byggplanen: 95 (klart)

- **Vilket steg:** Öppet 36 (granskning 28, M1), eget steg med nästa lediga nummer, 95, efter steg 94. **Hugos beslut
  2026-11-04 om granskning 28**, skrivna i chatten i uppdraget till den här sessionen, står ordagrant i
  `GRANSKNING.md` under "Hugos beslut 2026-11-04 om granskning 28": (1) Öppet 36 enligt granskarens (a), med
  tillägget att varje bankkontorad räknas bara en gång; hittar nästa granskning ett nytt hål i familjen Öppet 31–36
  går vi över till (b); (2) Öppet 37 blir ett ärende för just det underlaget, byggs som steg 96, inte här; (3) steg 94
  är granskat och klart. Byggt i 0708667 (kod och test) och dokumentationscommiten efter den.
- **Byggt** i `_kontrollera_beloppssidan`, i grenen för debet, efter Öppet 35:s krav på någon bankrad alls: varje
  rad med ett underlags `belopp_ore` i debet paras i radordning med den första lediga raden på bankkontot (rollen
  `bank`) i kredit som har exakt samma belopp och bara bankrader som källor, och varje bankkontorad paras högst en
  gång. En rad utan partner stoppar förslaget. Bara stopp tillagda, returvärdet oförändrat, inget företagsspecifikt.
  Felet namnger raden, kontot, underlaget, beloppet, raderna på bankkontot (och vilken rad som redan tagit dem) och
  Öppet 36. Granskarens b1 (fakturan spegelvänd ihop med 009:s betalning) och b3 (bankraden på kostnadskontot)
  stoppas, och två belopp i debet får inte dela en bankkontorad. Docstringarna säger att regeln måste prövas igen
  när Ö8 (kreditnotor) byggs.
- **Nytt argument:** `_kontrollera_beloppssidan` tar kontoplanen (för rollen `bank`). De två testerna i
  `test_beslut_granskning_27.py` som anropar den direkt skickar nu `korning.kontoplan` (Hugos OK 2026-11-04, 2).
- **Sessionen stannade och frågade (uppdragets punkt 3):** b2 går igenom med regeln enligt beslut 1. Bankrad 26 är
  003:s betalning och står på bankkontot i kredit mot 003:s belopp i debet, så (a) är uppfylld; 009:s belopp står i
  kredit med delarna i debet. Konteringen är identisk med flöde a:s två förslag (009:s faktura och 003:s betalning)
  i samma förslag. **Hugos beslut 2026-11-04 (i chatten, ordagrant i `GRANSKNING.md`):** b2 godtas under (a), inte
  felaktig bokföring, inte ett nytt hål i familjen; b2-testet är ett skydd som visar att formen godtas och att
  konteringen per konto är samma som flöde a:s två förslag; att en faktura och en annan fakturas betalning står i
  samma förslag ska kontrolleras med en redovisningskonsult och tas upp när godkännandekortet i appen byggs (Öppet
  38).
- **Skyddstestet** `test_skydd_varje_belopp_i_debet_i_flodena_har_en_bankrad` (granskning 28, L1) prövar nu
  granskarens f4: exakt en rad på bankkontot i kredit med samma belopp och bara bankrader som källor.
- **Tester:** 9 nya i `scripts/tests/test_beslut_granskning_28.py`: b1, b3, den delade bankkontoraden, ordningen
  (Öppet 35 före 36), b2 som skydd, två skydd till (fakturan och betalningen för hand, två betalningar med var sin
  bankkontorad), flöde a, b och e, och texten i koden. **Röda före:** 4 av 9 mot koden i 3f36f6b (b1, b3 och den
  delade raden "DID NOT RAISE", texttestet), körda i projektmappen innan `konteringsforslag.py` ändrades. Då var b2
  skrivet som ett stopp: 5 röda före, och efter kodändringen 1 röd (b2), vilket var frågan till Hugo.
- **Kommandon** (från projektmappen, ett i taget):
  1. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line
     -rA -k granskning_28 scripts/tests` före kodändringen (**5 failed, 4 passed**, rött före, med b2 som stopp).
  2. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short
     -rA -k "granskning_28 or granskning_27" scripts/tests` efter kodändringen (först 2 failed, 20 passed: b1:s test
     väntade sig tusentalsavstånd i beloppet, rättat till `kronor`; sedan **1 failed, 21 passed**, b2).
  3. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
     scripts/tests`: **1 failed, 4 442 passed** (b2), före frågan till Hugo.
  4. Samma som 1 med `--tb=short` efter att b2 skrivits om till skydd: **9 passed**. Samma som 3: **4 443 passed**.
  5. `git add scripts/konteringsforslag.py scripts/tests/test_beslut_granskning_27.py
     scripts/tests/test_beslut_granskning_28.py` och `git commit -F` med meddelandet i scratchpad (0708667).
  6. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q -k
     byggplan_progress scripts/tests` efter dokumentationen.
- **Dokumentation** (den här commiten): `GRANSKNING.md` ("Hugos beslut 2026-11-04 om granskning 28", med alla sex
  besluten ordagrant), BYGGPLAN.md (steg 95 och 96, steg 94 granskat och klart, "Läge nu") och den här filen (Öppet
  36 stängd, Öppet 37 som steg 96, Öppet 38 ny). SPEC 7.1 är inte rörd. SPEC 7 (stycket "Sidan för beloppet") är
  inte uppdaterad med Öppet 36 i den här sessionen, eftersom uppdraget sa att inget utanför de nämnda filerna rörs.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf, 5b4aa83, 7801a64, 68e86bb, granskning 27, 109fdcf, f10c65b, granskning 28, 0708667 och den här commiten.
  `main` på GitHub står på 7d8cae9.

## Läge 2026-11-04, granskning 28 av Öppet 35

Steg i byggplanen: 94 (klart)

- **Granskning 28** (av 109fdcf och f10c65b, i en ny session som inte sett byggsessionen, `GRANSKNING.md`,
  "Granskning 28"): **gult**. Öppet 35 är byggd som Hugos beslut 2026-10-31 säger, ordagrant: diffen lägger bara till
  en delkontroll och ett anrop sist efter Öppet 33, tar inte bort något och ändrar inte returvärdet; inget
  företagsspecifikt i kärnan; granskarens h1 och h2 från granskning 27, byggda om oberoende, stoppas med rätt fel;
  "rött före" upprepat mot `git archive` av b7d9fac (5 röda, 8 gröna av 13) och sviten 4 434 gröna; flöde a, b och e
  går igenom; 109fdcf och f10c65b rör bara koden, testfilen och dokumentationen. Halvan om kredit prövad med tre
  hela förslag: alla stoppas av täckningen innan Öppet 35 nås, som byggsessionen bedömde. **Tre egna prov går igenom
  (M1, nivå medel, fanns före 109fdcf, Öppet 36):** kravet på bankrad gäller per förslag, inte per underlag, så
  fakturan spegelvänd och två fakturor kvittade mot varandra godtas så fort förslaget också har någon bankrad: en
  annan fakturas betalning (b1, b2) eller en bankrad på kostnadskontot i stället för bankkontot (b3). **Utanför
  steget (M2, nivå medel, Öppet 37):** ett underlag med `belopp_ore` 0 läses in, flöde a bygger en faktura med en
  rad, K2 stoppar, och felet går upp genom `kontera_period`, så hela körningen stannar utan ärende. Ett lågt fynd:
  L1 (byggsessionens skyddstest prövar samma svaga villkor som regeln). Granskarens förslag till regel för Öppet 36
  står i `GRANSKNING.md`.
- **Statusraderna** här (statusraden, testsviten, tabellen Klart, Öppet 35, Öppet 36 och 37 nya, "Nästa steg" punkt
  3) och i BYGGPLAN.md ("Läge nu" och steg 94) uppdaterade i samma commit som granskningen (CLAUDE.md, Hugos beslut
  2026-10-30 om granskning 24, P10). Inget annat ändrat. Kommandona står i `GRANSKNING.md`, "Granskning 28".
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf, 5b4aa83, 7801a64, 68e86bb, granskning 27, 109fdcf, f10c65b och granskning 28. `main` på GitHub står på
  7d8cae9.

## Läge 2026-10-31, Öppet 35 byggd

Steg i byggplanen: 94 (klart)

- **Vilket steg:** Öppet 35 (granskning 27, M1), eget steg med nästa lediga nummer, 94, efter steg 93. **Hugos beslut
  2026-10-31**, skrivet i chatten i uppdraget till den här sessionen: "Beloppet i debet ska kräva en bankrad.
  belopp_ore får bara stå i kredit när delarna inte gör det." Byggt i 109fdcf (kod och test) och
  dokumentationscommiten efter den.
- **Kreditnotor först (steg 1 i uppdraget), före kodändringen:** en riktig kreditnota (leverantören ger tillbaka
  pengar, sidorna medvetet omvända) kan inte läsas in i dag. `las_underlag.TYPER` har bara `leverantorsfaktura` och
  `kvitto`, och negativa belopp stoppas "tills det är bestämt hur kreditnotor ska behandlas" (SPEC 11, Ö8). Ingen
  testdata och inget i SPEC har en kreditnota. Två nya tester visar det (typen `kreditnota` och negativa belopp stoppas
  redan när underlaget läses). Den nya regeln stoppar alltså ingen kreditnota, och sessionen stannade inte. När Ö8
  byggs måste regeln prövas igen, eftersom en kreditnota bokförd med beloppet i debet utan bankrad ser ut som h1.
- **Byggt** i `_kontrollera_underlagen`, sist efter Öppet 33 (ny delkontroll `_kontrollera_beloppssidan`): en rad med
  ett underlags `belopp_ore` som källa står i debet bara när förslaget har minst en bankrad i kopplingarna, och i
  kredit bara när ingen rad har underlagets `underlag_ore` eller `moms_ore` som källa i kredit. Bara ett nytt stopp:
  ingen kontroll borttagen, returvärdet oförändrat, inget företagsspecifikt i kärnan, inget som kan bokföra eller
  godkänna. Felen namnger raden, kontot, underlaget, sidan och Öppet 35. Granskarens prov h1 (003 spegelvänd) och h2
  (003 och 009 med samma belopp mot varandra på 2440) stoppas.
- **Granskarens förslag hade en del till** ("i debet bara ... utan underlagets delar alls"). Den står inte i Hugos
  beslut och är inte byggd.
- **Halvan om kredit** stoppas i dag redan av täckningen (punkt 7), eftersom `belopp_ore` räknar med alla delarna på
  sin sida, eller av Öppet 34 om en del dras ifrån med `skillnad`. Det är byggsessionens bedömning efter att ha läst
  koden, inte provat med ett helt förslag. Därför prövas den halvan med två tester direkt på den nya delkontrollen.
- **Ordningen:** ett förslag som bryter mot både Öppet 33 och Öppet 35 får Öppet 33:s fel (test).
- **Tester:** 13 nya i `scripts/tests/test_beslut_granskning_27.py`: två om kreditnotor, h1 och h2, ordningen, två
  direkt på delkontrollen, fem skydd (fakturan och betalningen för hand, flöde a och b, och att varje belopp i debet i
  flödena har en bankrad) och ett om texten i koden. **Röda före:** 5 av 13 mot koden i b7d9fac (h1 och h2 "DID NOT
  RAISE", de två direkta testerna och texttestet för att delkontrollen inte fanns), körda i projektmappen innan
  `konteringsforslag.py` ändrades. Den första körningen hade ett fel i testet (h2 krävde att testdatan saknar
  K4-ärenden, men testdatan har planterade dubbletter); påståendet ändrades till att kopian inte får nya ärenden.
- **Kommandon** (från projektmappen, ett i taget):
  1. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line
     -rA -k granskning_27 scripts/tests` före kodändringen, två gånger (först 5 failed, 8 passed med testets eget fel
     i h2; sedan **5 failed, 8 passed**, rött före).
  2. Samma med `--tb=short` efter kodändringen (12 passed, 1 failed: felet om kredit namngav inte kontot, rättat i
     koden), sedan **13 passed**.
  3. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
     scripts/tests`: **4 434 passed**, tre gånger (efter kodändringen, efter radbrytningar i koden och efter
     dokumentationen, före commit 2).
  4. `git add scripts/konteringsforslag.py scripts/tests/test_beslut_granskning_27.py` och `git commit -F` med
     meddelandet i scratchpad (109fdcf).
- **Dokumentation** (den här commiten): SPEC 7 (sidan för beloppet, Öppet 33 prövas inte längre sist), SPEC 11
  (meningen om att regeln om högst en rad är bekräftad av Hugo 2026-10-31, beslutet om Öppet 35, och en hänvisning i
  Ö8), `GRANSKNING.md` ("Hugos beslut 2026-10-31 om granskning 27"), BYGGPLAN.md (steg 94 och "Läge nu") och den här
  filen. SPEC 11 hade inte orden "för Hugo eller Casper att bekräfta" om regeln om högst en rad (de stod i PROGRESS.md,
  och rättades där i granskning 27), så där fanns inget att ta bort. SPEC 7.1 är inte rörd.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf, 5b4aa83, 7801a64, 68e86bb, granskning 27, 109fdcf och den här commiten. `main` på GitHub står på 7d8cae9.

## Läge 2026-10-31, granskning 27 av Öppet 33 och 34

Steg i byggplanen: 93 (klart)

- **Granskning 27** (av 7801a64 och 68e86bb, i en ny session som inte sett byggsessionen, `GRANSKNING.md`,
  "Granskning 27"): **gult**. Öppet 33 och Öppet 34 är byggda som Hugos beslut om granskning 26 och SPEC 7 säger:
  diffen lägger bara till stopp, tar inte bort något och ändrar inte returvärdet; ordningen K5, K8, Öppet 31, 32, 34
  och sist 33 stämmer; granskarens prov H7 och de fyra LUCKA-proven från granskning 26, byggda om oberoende, stoppas
  med rätt fel; det ändrade gamla testet i `test_konteringsforslag.py` är rimligt och rött mot 5b4aa83; inget
  företagsspecifikt i kärnan och inget fält för bokfört eller godkänt; "rött före" upprepat (12 röda, 10 gröna av 22
  mot `git archive` av 5b4aa83) och sviten 4 421 gröna. Nio egna prov: sju stoppas där de ska (brutto som `summa` tas
  av Öppet 33, kreditsidan som delarna av Öppet 32, moms på utgående momskontot av punkt 5, `belopp_ore` i en
  `skillnad` och två fakturor summerade av Öppet 34, avrundning av punkt 3, negativt belopp av K2). **Två går igenom
  (M1, nivå medel, fanns före 7801a64, Öppet 35):** fakturan spegelvänd (beloppet i debet på 2440, kostnaden och
  momsen i kredit) och två lika stora fakturor under samma regel mot varandra (den enas belopp i debet, den andras i
  kredit på 2440), båda med alla fem kontrollerna "ok". Sidan prövas inte, och inget kräver en bankrad när beloppet
  står i debet. Granskarens förslag till regel står i `GRANSKNING.md`. Två låga fynd: L1 (ett överflödigt påstående
  i det ändrade testet) och L2 (SPEC 11 säger "för Hugo eller Casper att bekräfta" om regeln om högst en rad).
- **Hugos beslut 2026-10-31 om regeln om högst en rad** (i uppdraget till granskning 27, ordagrant i
  `GRANSKNING.md`): regeln "ett underlags `belopp_ore` står på högst en rad i förslaget" behålls. Byggsessionens
  tillägg är därmed bekräftat.
- **Statusraderna** här (statusraden, testsviten, tabellen Klart, Öppet 33 och 34, Öppet 35 ny, "Nästa steg" punkt 3)
  och i BYGGPLAN.md ("Läge nu" och steg 93) uppdaterade i samma commit som granskningen (CLAUDE.md, Hugos beslut
  2026-10-30 om granskning 24, P10). Inget annat ändrat. Kommandona står i `GRANSKNING.md`, "Granskning 27".
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf, 5b4aa83, 7801a64, 68e86bb och granskning 27. `main` på GitHub står på 7d8cae9.

## Läge 2026-10-30, Öppet 33 och 34 byggda

Steg i byggplanen: 93 (klart)

- **Vilket steg:** Öppet 33 och Öppet 34 byggs i ett steg före uppgift 5 (Hugos beslut 2026-10-30 om granskning 26,
  "Ja, i samma steg", `GRANSKNING.md`). Steget fick nästa lediga nummer, 93, i fas C efter steg 92 (Hugos beslut
  2026-10-30 om byggsessionen för Öppet 32, b). Byggt 2026-10-30 i 7801a64 (kod, test och SPEC) och
  dokumentationscommiten efter den. Den här sessionen har inte sett granskning 26 annat än som text i
  `GRANSKNING.md`.
- **Öppet 34 (granskning 26, M1), byggt i `_kontrollera_underlagen` efter Öppet 32** (ny delkontroll
  `_kontrollera_beloppsraderna`), med granskarens förslag till regel: en rad som har ett underlags `belopp_ore` som
  källa räknas bara med `lika` och står bara på leverantörsskulderna (rollen `leverantorsskulder` i kontoplanen), och
  `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`. **Byggsessionens tillägg, bekräftat av Hugo 2026-10-31
  (uppdraget till granskning 27, `GRANSKNING.md`):** underlagets `belopp_ore` står på högst en rad i förslaget. Utan det går granskarens fjärde prov (hela
  beloppet på leverantörsskulderna på båda sidorna, ingen kostnad och ingen moms bokförs) igenom, eftersom båda
  raderna räknas med `lika` på leverantörsskulderna. Flödena bygger fakturan med `belopp_ore` en gång i kredit och
  betalningen med `belopp_ore` en gång i debet, så de berörs inte. Granskarens fyra LUCKA-prov stoppas: kostnaden
  som `skillnad` av `belopp_ore` och momsen på 2440 (och på 4010), kontona bytta inom regeln byggda så (020 med
  granskarens regelbok), hela beloppet på 4010 utan momsrad, och hela beloppet på 2440 på båda sidorna. Ett eget
  prov: kostnaden på 4010 räknad som `underlag_ore` minus momsen, med momsen två gånger på 2641, godtogs också
  förut (täckningen går ihop, och Öppet 32 godtar kontot) och stoppas nu av regeln om `skillnad`.
- **Öppet 33 (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a), byggt sist i `_kontrollera_underlagen`**
  (ny delkontroll `_kontrollera_momsraderna`): varje rad som har ett underlags `moms_ore` som källa står på kontot
  för ingående moms (rollen `ingaende_moms` i kontoplanen), annars stoppas förslaget. Granskarens prov H7 (003 med
  momsen på 4010) och momsen på leverantörsskulderna stoppas. Prövas efter Öppet 34, så att en rad som räknas fel
  får felet om beräkningen, inte om kontot.
- **Felen** namnger raden, underlaget, momssatsen där den finns, kontot raden står på, kontot med rollen och vad som
  gäller, med hänvisning till Öppet 33 respektive 34. K5, K7, K8, Öppet 31 och Öppet 32 stoppar före de nya
  kontrollerna med samma texter som förut (tester för ordningen).
- **Docstringen** i `scripts/konteringsforslag.py` om momsraden ("inte beslutat") är rättad (granskning 26, L1), och
  SPEC 7 och 11 säger vad som gäller. Inget annat i kärnan är ändrat: diffen i `konteringsforslag.py` lägger till två
  delkontroller med var sitt `raise`, två små hjälpfunktioner, kontoplanen och verifikationen som argument till
  `_kontrollera_underlagen`, och dokumentationstext. Inget företagsspecifikt i `scripts/` utanför `scripts/tests/`
  (`grep` efter `4010`, `5460`, `2440`, `2641`, `syntet` och `SYNT` i `konteringsforslag.py` ger inget). CLAUDE.md
  är inte ändrad.
- **Avsteg:** ett gammalt test i `scripts/tests/test_konteringsforslag.py`,
  `test_tackningen_godtar_underlaget_som_skillnad_mellan_beloppet_och_momsen`, visade att täckningen godtar kostnaden
  räknad som `belopp_ore` minus momsen, exakt luckan i Öppet 34. Det är ändrat till
  `test_tackningen_godtar_men_oppet_34_stoppar_underlaget_som_skillnad_mellan_beloppet_och_momsen`, som säger att
  förslaget stoppas av Öppet 34 (inte av täckningen). Rött mot kopian av 5b4aa83 (kommando 10 nedan). Antalet tester
  är oförändrat av den ändringen.
- **Rött före** (`scripts/tests/test_beslut_granskning_26.py` mot `git archive` av 5b4aa83, koden före rättelsen):
  **12 röda och 10 gröna av 22**. Röda: H7 med båda momsfilerna, momsen på leverantörsskulderna, LUCKA 1 med båda
  momsfilerna och på 4010, LUCKA 2, 3 och 4, det egna provet med `underlag_ore` som `skillnad` (alla "DID NOT
  RAISE"), ordningsprovet Öppet 34 före 33, och dokumentationstestet (SPEC saknade Öppet 33 och 34). De tio gröna är
  skydd som ska vara gröna före: prov B stoppas av K5 och K8 först, granskarens prov från granskning 24 av Öppet
  31 först, prov (b) från granskning 25 av Öppet 32 först, ett förslag med rätt form godtas med båda momsfilerna,
  momsen summerad över två satser godtas (`summa` är tillåtet), 020 med två konton i regeln godtas med rätt konton,
  flöde a (003 med fakturan och betalningen), flöde b (kvittot 015) och flöde e (bankrad 117 utan underlag) går
  igenom, och varje rad från ett underlag i hela körningen har rätt form.
- **Testsviten:** 4 421 passed (före: 4 399, 22 nya), 0 röda, i projektmappen med kommandot i SPEC 7.1 (i
  bakgrunden, 81 sekunder). Byggplanstestet grönt efter dokumentationen (kommando 12).
- **Kommandon i den här sessionen** (P7). `<scratch>` är sessionens scratchpad-mapp,
  `/private/tmp/claude-501/-Users-hugolindholmer-VERA-agent/50302ee1-89f6-40cf-a08b-cde4259aa5cc/scratchpad`. Allt
  kördes från projektmappen, ett kommando i taget, i förgrunden utom kommando 7:
  1. `ls`, `git status` och `git log --oneline -3` (rent, 5b4aa83 överst).
  2. `cat`, `grep -n` med `-e`, `-r` och `-c`, `wc -l`, `git diff` och `git diff --stat` för att läsa. Stycken av
     filer lästes med fil-verktyget Read och ändrades med fil-verktygen Edit och Write.
  3. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short
     -rf -k beslut_granskning_26 scripts/tests` (de nya testerna i projektet: först **2 failed, 20 passed**, ett fel i
     testet självt, se nedan; efter rättelsen **22 passed**).
  4. `mkdir -p <scratch>/kopia-5b4aa83` och `mkdir -p <scratch>/kopia-5b4aa83-kf`.
  5. `git archive -o <scratch>/5b4aa83.tar 5b4aa83`.
  6. `tar -xf <scratch>/5b4aa83.tar -C <scratch>/kopia-5b4aa83` och samma till `<scratch>/kopia-5b4aa83-kf`.
  7. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q scripts/tests`
     (hela sviten i projektmappen, kommandot i SPEC 7.1, i bakgrunden: **4 421 passed**, 0 röda, 81 sekunder).
  8. `cp -R scripts/tests/test_beslut_granskning_26.py <scratch>/kopia-5b4aa83/scripts/tests/test_beslut_granskning_26.py`.
  9. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-5b4aa83/scripts/tests/test_beslut_granskning_26.py` (rött före: **12 failed, 10 passed**).
  10. `cp -R scripts/tests/test_konteringsforslag.py <scratch>/kopia-5b4aa83-kf/scripts/tests/test_konteringsforslag.py`
      och `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
      --tb=line -rf -k oppet_34 <scratch>/kopia-5b4aa83-kf/scripts/tests/test_konteringsforslag.py` (det ändrade
      gamla testet mot kopian: **1 failed**, "DID NOT RAISE").
  11. `git add` och `git commit -F <scratch>/commit-1.txt` (kod, test och SPEC: 7801a64).
  12. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q -k
      byggplan_progress scripts/tests` efter dokumentationen (byggplanstestet).
  13. `git add` och `git commit -F <scratch>/commit-2.txt` (dokumentationen), sedan `git status` och `git log`.
  Vakten stoppade: `sed` två gånger (står inte på listan) och `grep` två gånger med `\|` i mönstret (omvänt
  snedstreck); de ersattes med fil-verktyget Read och `grep -e`. Felet i testet självt (kommando 3): H7-testet krävde
  att "Öppet 32" inte stod i felet, men felet för Öppet 33 hänvisar till "Hugos beslut om byggsessionen för Öppet 32,
  a"; testet kräver nu att "(Öppet 32," inte står där. Inget i projektet ändrades utom de sju filerna i de två
  commitarna, och inget utanför projektet utom scratchpad.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf, 5b4aa83, 7801a64 (steg 93: kod, test och SPEC) och dokumentationscommiten efter den. `main` på GitHub står
  på 7d8cae9.

## Läge 2026-10-30, granskning 26 av Öppet 32

Steg i byggplanen: 91 (klart)

- **Granskning 26** (av c479915 och d1ab489, skriven i den här commiten) är gjord i en ny session som inte sett
  byggsessionen eller commit-sessionen: **gult**. Inget kan bokföras och ingen spärr har blivit svagare (P4). Öppet 32
  är byggd som Hugos beslut 1 säger, och granskarens två prov från granskning 25 stoppas med båda momsfilerna (P1).
  K5, K7, K8 och Öppet 31 stoppar före den nya kontrollen med samma texter, och felet för Öppet 32 namnger raden,
  underlaget, satsen, kontot K5 ger, regeln, datumet och kontot raden står på (P3). "Rött före" stämmer: 5 röda och 9
  gröna, upprepat mot `git archive` av 7c1f148, och sviten 4 399 gröna (P5). Dokumenten säger samma sak, stegnumren 91
  och 92 stämmer med beslut b, och Öppet 33 är inte byggd (P6). **Ett hål kvar, i samma familj (M1, nivå medel, ny punkt
  Öppet 34):** den nya kontrollen prövar bara rader med `underlag_ore` som källa, så en kostnadsrad räknad som
  `skillnad` ur underlagets `belopp_ore` (minus momsen) prövas aldrig. Granskarens prov (a) och (b) från granskning 25
  byggda så, och en bruttobokföring utan momsrad, godtas med alla kontrollerna "ok". Luckan fanns före c479915, rör
  inte flödena och förslaget kräver godkännande, så den är inte blockerande, men den bör rättas före uppgift 5 efter
  Hugos eller Caspers beslut, gärna tillsammans med Öppet 33. Ett lågt fynd (L1): docstringen i
  `konteringsforslag.py` säger att momsradens konto "inte är beslutat", men beslut a säger Öppet 33. Steg 91 är klart
  och granskat.
- **Statusraderna** (den här filen: statusraden, tabellen Klart, Öppet 32, ny punkt Öppet 34 och "Nästa steg" punkt 3;
  BYGGPLAN.md "Läge nu" och steg 91) säger nu att Öppet 32 är granskad, enligt CLAUDE.md (Hugos beslut 2026-10-30 om
  granskning 24, P10). Ingen kod ändrad, inget i CLAUDE.md ändrat.
- **Kommandon i den här sessionen** (P7): står i `GRANSKNING.md`, "Granskning 26", "Kommandon i den här granskningen".
  Rött före för byggsessionens testfil: kommandona 3–8 där (**5 failed, 9 passed**). Granskarens egen provfil
  `test_granskare_prov26.py` (bara i scratchpad): **25 passed** mot kopian av d1ab489 och **8 failed, 16 passed** mot
  kopian av 7c1f148 (24 tester där), med de fyra LUCKA-proven gröna i båda.
- **Testsviten:** 4 399 passed, 0 röda, med kommandot i SPEC 7.1 (i bakgrunden, 73 sekunder).
- **Hugos beslut 2026-10-30 om granskning 26** (i chatten, efter commiten 994bcdf, ordagrant i `GRANSKNING.md`):
  "Ja, i samma steg": Öppet 33 och Öppet 34 byggs i ett steg före uppgift 5. Inskrivet i den här filen (Öppet 33, 34
  och "Nästa steg" punkt 3), BYGGPLAN.md ("Läge nu") och `GRANSKNING.md` i en egen commit. Inte byggt; bygget är en
  egen session (CLAUDE.md, en uppgift per session).
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148, c479915, d1ab489,
  994bcdf (granskning 26) och beslutscommiten efter den. `main` på GitHub står på 7d8cae9.

## Läge 2026-10-30, Öppet 32 rättad

Steg i byggplanen: 91 (klart)

- **Vilket steg:** Öppet 32 är enligt granskning 25 inte en del av steg 22 utan ett eget steg före uppgift 5, och
  BYGGPLAN.md gav först varken Öppet 32 eller Öppet 26 något stegnummer (granskning 25, P6). **Hugos beslut 2026-10-30
  om byggsessionen för Öppet 32** (skrivna i uppdraget till commit-sessionen, ordagrant i `GRANSKNING.md`, "Hugos
  beslut 2026-10-30 om byggsessionen för Öppet 32"): (a) momsraden (`moms_ore`) låses till kontot för ingående moms
  som eget steg, Öppet 33, efter Öppet 32, inte i den här commiten; (b) Öppet 32 och Öppet 26 får egna stegnummer i
  BYGGPLAN.md; (c) SPEC 11-stycket får följa med i commit 1. Gjort i commit-sessionen 2026-10-30: Öppet 32 är steg 91
  (✅) och Öppet 26 steg 92 (⬜), de nästa lediga numren efter 90, i fas C efter steg 22; Öppet 33 står under Öppet
  nedan, utan stegnummer än; SPEC 7 och 11 säger att momsraden är Öppet 33.
- **Commit-sessionen 2026-10-30** (byggsessionen kunde inte köra `git`, se "Avsteg" nedan) kontrollerade före
  commitarna att `git status` visade exakt de fem ändrade filerna och den nya testfilen, att koddiffen i
  `scripts/konteringsforslag.py` bara lägger till stoppet i `_kontrollera_underlagen` (hjälpfunktionen
  `_kontrollera_kostnadsraderna`, verifikationens rader som nytt argument, och dokumentationstext; inget annat), körde
  hela sviten med kommandot i SPEC 7.1 i projektmappen (**4 399 passed**, 0 röda) och upprepade "rött före" mot en
  kopia tagen med `git archive` av 7c1f148 (**5 röda, 9 gröna**, samma som byggsessionen). Kommandona står under
  "Kommandon i commit-sessionen" nedan.
- **Hugos beslut 2026-10-30 om granskning 25**, skrivna i uppdraget till den här sessionen och ordagrant i
  `GRANSKNING.md`, "Hugos beslut 2026-10-30 om granskning 25": (1) Öppet 32 byggs före uppgift 5: kostnadsraden i ett
  förslag med underlag ska stå på det konto som K5 räknar fram för underlagets momssats, och annat konto stoppar
  förslaget. (2) Öppet 31 räknas som granskad och klar.
- **1 (Öppet 32), byggt i commit 1 ("Öppet 32: kostnadsraden står på det konto K5 ger"):** `_kontrollera_underlagen` i
  `scripts/konteringsforslag.py` får verifikationens rader och prövar, efter K5, K7, K8 och kontrollen från Öppet 31
  och för varje underlag, att varje rad som har underlagets `underlag_ore` för en momssats som källa står på det konto
  `kontrollera_underlag` räknar fram för satsen (`konton`, ny delkontroll `_kontrollera_kostnadsraderna`). Annars
  stoppas förslaget med kontrollen `ursprung`, och felet namnger raden, underlaget, satsen, kontot K5 ger, underlagets
  regel och datum, och kontot raden står på. Granskarens två prov från P7 stoppas: `R-LEV-KAFFE` med två konton
  (livsmedel på 4010, ovrigt på 5460) och kontona bytta för SYNT-U-2025-020, och SYNT-U-2025-003 under sin egen regel
  med kostnaden på leverantörsskulderna 2440, båda med testbutikens momsfil och med prov B:s momsfil från granskning
  23. Flödena a, b och e bygger kostnadsraderna ur samma `konton` (`konteringsfloden._kostnad_och_moms`), så de berörs
  inte, och ett test visar att varje kostnadsrad i hela körningen står på kontot K5 ger. Momsraden (`moms_ore`) är
  inte byggd: den är Öppet 33, ett eget steg efter Öppet 32 (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32,
  a). Inget annat i kärnan är ändrat, och inget företagsspecifikt finns i `scripts/`. SPEC 7 säger vad som gäller.
  Öppet 32 stängd.
- **2 (Öppet 31):** står som granskad och klar under Öppet och i BYGGPLAN.md. Ingen kod.
- **Rött före** (`scripts/tests/test_beslut_granskning_25.py` mot en kopia av koden före rättelsen, HEAD 7c1f148):
  **5 röda och 9 gröna av 14**. Röda: granskarens prov (a) och (b) med båda momsfilerna, alla fyra med "DID NOT RAISE"
  (kopian skapade förslaget), och dokumentationstestet (SPEC saknade Öppet 32). De nio gröna är skydd som ska vara
  gröna före: flödet bokför 020 rätt med två konton i regeln och samma förslag för hand med rätt konton godtas (båda
  momsfilerna), ett förslag med rätt konto godtas, prov B stoppas av K5 och K8 först, granskarens prov från granskning
  24 stoppas av Öppet 31 först, flöde a (003 med fakturan och betalningen), flöde b (kvittot 015) och flöde e (bankrad
  117 utan underlag) går igenom, och varje kostnadsrad i körningen står på kontot K5 ger.
- **Avsteg (för Hugo att känna till):** sessionen startades i `~/VERA`, mappen ovanför projektet, inte i
  `~/VERA/agent`. Vakten kräver att allt körs i mappen där sessionen startade, och stoppade därför `git` (ingen
  git-mapp där), `cd`, `git -C` och appens eget verktyg för att byta mapp, och pytest mot `scripts/tests` hade inget
  mål. Allt kördes i stället mot kopior i scratchpad, som SPEC 7.1 tillåter: "rött före" mot en kopia av den orörda
  arbetsmappen tagen med `cp -R` (HEAD var 7c1f148 enligt `.git/refs/heads/main`, och sviten där gav samma 4 385 som
  PROGRESS.md), inte med `git archive`, och hela sviten efter rättelsen mot en kopia av det ändrade projektet.
  Commitarna (kod, test och SPEC; sedan dokumentationen) gjordes 2026-10-30 i en ny session startad i projektmappen
  (commit-sessionen), som körde sviten med kommandot i SPEC 7.1 och "rött före" med `git archive` mot 7c1f148, se
  ovan.
- **Kommandon i den här sessionen** (P7). `<scratch>` är sessionens scratchpad-mapp,
  `/private/tmp/claude-501/-Users-hugolindholmer-VERA/a568ef37-2cd8-4cf6-ac98-58fd22d7bc64/scratchpad`, och
  `<agent>` är `/Users/hugolindholmer/VERA/agent`. Allt kördes från `~/VERA`, i förgrunden, och vakten släppte igenom
  allt nedan:
  1. `mkdir -p <scratch>/kopia-7c1f148`
  2. `cp -R <agent>/ <scratch>/kopia-7c1f148` (den orörda arbetsmappen före alla ändringar)
  3. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
     <scratch>/kopia-7c1f148/scripts/tests` (hela sviten mot den orörda kopian: **4 385 passed**, antalet före)
  4. `cp -R <agent>/scripts/tests/test_beslut_granskning_25.py <scratch>/kopia-7c1f148/scripts/tests/test_beslut_granskning_25.py`
  5. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-7c1f148/scripts/tests/test_beslut_granskning_25.py` (**5 failed, 9 passed**, rött före)
  6. `cp -R <agent>/ <scratch>/kopia-arbete` efter kodändringen och SPEC 7, sedan `cp -R
     <agent>/scripts/konteringsforslag.py <scratch>/kopia-arbete/scripts/konteringsforslag.py` och `diff` mellan dem
     (lika)
  7. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rA
     <scratch>/kopia-arbete/scripts/tests/test_beslut_granskning_25.py` (den nya testfilen efter rättelsen: **14 passed**)
  8. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rf
     <scratch>/kopia-arbete/scripts/tests` (hela sviten efter rättelsen: **4 399 passed**)
  9. Efter dokumentationen: `cp -R` av de fyra dokumentfilerna till `<scratch>/kopia-arbete/` och kommando 8 igen (se
     "Testsviten" nedan)
  10. `ls`, `cat`, `grep`, `wc` och `diff` för att läsa. Stycken av filer lästes med fil-verktyget Read.
  Vakten stoppade: `cd` och `git -C` (står inte på listan), fem kommandon med `;` eller `\` (ihopkopplade, eller
  `grep` med `\` i mönstret), och verktyget som byter sessionens mapp (står inte på listan över tillåtna verktyg).
  `git log`, `git status` och `git show` gav "not a git repository" från `~/VERA`. Inget i projektet ändrades utom
  de sex filerna i de två commitarna, och inget utanför projektet utom scratchpad.
- **Kommandon i commit-sessionen** (P7), 2026-10-30, startad i `~/VERA/agent`. `<scratch>` är den sessionens
  scratchpad-mapp, `/private/tmp/claude-501/-Users-hugolindholmer-VERA-agent/fe3a6544-42b9-4c18-a0f5-d8275a1477ea/scratchpad`.
  Ett kommando i taget, och vakten släppte igenom allt nedan:
  1. `ls` och `git status` (exakt fem ändrade filer och en ny).
  2. `cat CLAUDE.md`, `git diff scripts/konteringsforslag.py`, `git diff SPEC.md`, `git diff BYGGPLAN.md GRANSKNING.md`,
     `head -n 120 PROGRESS.md`, `cat BYGGPLAN.md`, `cat scripts/tests/test_beslut_granskning_25.py` och `grep -n` med
     `-e` för att läsa. Stycken av filer lästes med fil-verktyget Read och ändrades med fil-verktyget Edit.
  3. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q scripts/tests`
     (hela sviten i projektmappen, kommandot i SPEC 7.1, i bakgrunden: **4 399 passed**, 0 röda, 82 sekunder).
  4. `mkdir -p <scratch>/kopia-7c1f148`
  5. `git archive -o <scratch>/kopia-7c1f148.tar 7c1f148`
  6. `tar -xf <scratch>/kopia-7c1f148.tar -C <scratch>/kopia-7c1f148`
  7. `cp -R scripts/tests/test_beslut_granskning_25.py <scratch>/kopia-7c1f148/scripts/tests/test_beslut_granskning_25.py`
  8. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-7c1f148/scripts/tests/test_beslut_granskning_25.py` (rött före mot den rena kopian av 7c1f148:
     **5 failed, 9 passed**. Röda: granskarens prov (a) och (b) med båda momsfilerna, "DID NOT RAISE", och
     dokumentationstestet. Gröna: de nio skydden. Samma som byggsessionens kommando 5.)
  9. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q -k
     byggplan_progress scripts/tests` efter dokumentationen (byggplanstestet: **8 passed**).
  10. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q -k
      beslut_granskning_25 scripts/tests` efter tillägget om Öppet 33 i SPEC (de 14 nya testerna: **14 passed**).
  11. `git add` och `git commit -F <scratch>/commit-1.txt` respektive `<scratch>/commit-2.txt` (meddelandena skrivna
      med fil-verktyget Write), sedan `git status` och `git log`.
  Vakten stoppade: `sed` två gånger (står inte på listan), `grep` två gånger med `\|` i mönstret (omvänt snedstreck),
  `tail` på bakgrundskörningens utskriftsfil utanför scratchpad (lästes med fil-verktyget Read i stället), och pytest
  med en enskild testfil i projektet som mål (bara `scripts/tests` eller en kopia tillåts, därför `-k` i kommando 10).
  Inget i projektet ändrades utom de sex filerna i de två commitarna, och inget utanför projektet utom scratchpad.
- **Testsviten:** 4 399 passed (före: 4 385), 0 röda, i byggsessionen mot kopian av det ändrade projektet (kommando 8
  och 9) och i commit-sessionen i projektmappen med kommandot i SPEC 7.1 (kommando 3). Byggplanstestet grönt efter
  stegnumren (kommando 9).
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90, 7c1f148 (granskning 25),
  c479915 (Öppet 32: kod, test och SPEC) och dokumentationscommiten efter den. `main` på GitHub står på 7d8cae9.

## Läge 2026-10-30, granskning 25 av Öppet 31

Steg i byggplanen: 22 (klart)

- **Granskning 25** (av bbb183a och 277ca90, skriven i den här commiten) är gjord i en ny session som inte sett
  rättelsesessionen: **grönt**. Inget kan bokföras och ingen spärr har blivit svagare (P4). Öppet 31 är byggd som
  Hugos beslut 1 säger och granskarens prov från granskning 24 stoppas (P1). Granskarens sex hålprov (underlag utan
  datum, underlag utan regel, två underlag med olika egna regler med båda momsfilerna, tomt förslag, regel-id med
  annat skiftläge, två regler med samma id) stoppas alla (P2). K5, K7 och K8 stoppar prov B före den nya kontrollen
  med samma text som förut (P3). "Rött före" stämmer: 4 röda och 6 gröna, upprepat mot en ny kopia av 6dfcdcd (P5).
  Dokumenten säger samma sak om Öppet 30, Öppet 31 och steg 22 (P6). **Ett fynd bör rättas** efter Hugos eller
  Caspers beslut (P7, ny punkt Öppet 32): kostnaden kan stå på fel konto inom regeln, eller på ett rollkonto, för
  ett förslag byggt förbi flödena, eftersom `_kontrollera_underlagen` inte prövar raderna mot de konton K5 ger per
  sats. Luckan finns före och efter bbb183a och rör inte flödena. Steg 22 förblir klart.
- **Statusraderna** (den här filen: statusraden, tabellen Klart, Öppet 31 och "Nästa steg" punkt 3; BYGGPLAN.md "Läge
  nu" och steg 22) säger nu att Öppet 31 är granskad, enligt CLAUDE.md (Hugos beslut 2026-10-30 om granskning 24,
  P10). Ingen kod ändrad.
- **Kommandon i den här sessionen** (P7 i granskning 23): står i `GRANSKNING.md`, "Granskning 25", "Kommandon i den
  här granskningen". Rött före för rättelsesessionens testfil: kommandona 3–7 där (**4 failed, 6 passed**).
  Granskarens egen provfil `test_granskare_prov25.py` (bara i scratchpad): **16 passed** mot kopian av 277ca90 och
  **2 failed, 14 passed** mot kopian av 6dfcdcd.
- **Testsviten:** 4 385 passed, 0 röda, med kommandot i SPEC 7.1.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a, 277ca90 och den här commiten. `main` på
  GitHub står på 7d8cae9.

## Läge 2026-10-30, Öppet 31 rättad och steg 22 klart

Steg i byggplanen: 22 (klart)

- **Granskning 24** (av aecccdf, skriven i 6dfcdcd) är gjord i en ny session som inte sett rättelsesessionen: **grönt**.
  Inget kan bokföras och ingen spärr har blivit svagare (P9). P1 och P3 från granskning 23 och Öppet 29 är byggda som
  besluten säger, med prov B bekräftat i en kopia (P1). Granskaren bedömde att Öppet 31 bör rättas före uppgift 5
  (P5), att märkningen vid K4c som text räcker till uppgift 6 (P6), att steg 22 får räknas som klart, och frågade
  vilken regel som gäller när ett uppdrag säger "ändra ingen annan fil" (P10).
- **Hugos beslut 2026-10-30 om granskning 24**, skrivna i chatten i den här sessionen och ordagrant i `GRANSKNING.md`,
  "Hugos beslut 2026-10-30 om granskning 24": (1) Öppet 31: `skapa_konteringsforslag` stoppar ett förslag när
  förslagets regel inte är underlagets egen regel, uppslagen på underlagets datum, och granskarens prov ska stoppas.
  (2) Öppet 30: märkningen vid K4c som text i motiveringen räcker till uppgift 6, stängd. (3) Steg 22 är klart efter
  granskning 24. (4) Ny regel i CLAUDE.md: en granskningssession uppdaterar statusraderna i PROGRESS.md och
  BYGGPLAN.md i samma commit som granskningen, också när uppdraget säger "ändra ingen annan fil".
- **1 (Öppet 31), byggt i bbb183a:** `_kontrollera_underlagen` i `scripts/konteringsforslag.py` prövar, efter K5, K7 och
  K8 och för varje underlag i förslaget, att underlagets egen regel (`Regelbok.regel_for_underlag` på underlagets
  datum) har samma id som förslagets regel i `kopplingar`. Annars stoppas förslaget med kontrollen `ursprung`, och
  felet namnger underlaget, dess datum, båda reglerna och Öppet 31. Granskarens prov (SYNT-U-2025-003 under
  `R-BANK-AVGIFT` med kostnaden på 6570 och bankrad 117 i januari som avgift) godtogs förut med alla fem kontrollerna
  "ok" och stoppas nu, både med testbutikens momsfil och med prov B:s momsfil från granskning 23. Prov B (019 och
  028) stoppas som förut av K5 respektive K8, eftersom den nya kontrollen prövas efter dem, så testerna i
  `test_beslut_granskning_23.py` gäller oförändrade. Flödena a, b och e bygger alltid med underlagets egen regel
  (flöde e har inget underlag), och ett test visar att varje förslag med underlag i hela körningen har underlagets
  egen regel. Inget annat i kärnan är ändrat, och inget företagsspecifikt finns i `scripts/`. SPEC 7 säger vad som
  gäller. Öppet 31 stängd.
- **2 (Öppet 30):** stängd under Öppet med texten "avgjort, eget fält byggs i uppgift 6". Ingen kod.
- **3 (steg 22):** ✅ i BYGGPLAN.md, "Läge nu" uppdaterad (inget steg pågår, nästa att börja är steg 15 och 14), och
  raden "Steg i byggplanen" ovan säger klart. Steg 22 är granskat i granskning 22, 23 och 24 och klart.
- **4 (CLAUDE.md):** regeln står under "Så arbetar vi", efter regeln från 2026-10-29 om PROGRESS.md och BYGGPLAN.md.
- **Rött före** (`scripts/tests/test_beslut_granskning_24.py` mot en kopia av 6dfcdcd): **4 röda och 6 gröna av 10**.
  Röda: granskarens prov med testbutikens momsfil och med prov B:s momsfil, och testet av feltexten, alla tre med
  "DID NOT RAISE" (kopian skapade förslaget), och dokumentationstestet (SPEC saknade Öppet 31). De sex gröna är skydd
  som ska vara gröna före: prov B stoppas av K5 och K8 först, ett förslag för hand under underlagets egen regel
  godtas, flöde a (003 med fakturan och betalningen), flöde b (kvittot 015) och flöde e (bankrad 117 utan underlag)
  går igenom, och varje förslag med underlag i körningen har underlagets egen regel.
- **Kommandon i den här sessionen** (P7). `<scratch>` är sessionens scratchpad-mapp,
  `/private/tmp/claude-501/-Users-hugolindholmer-VERA-agent/b343bd08-da78-4176-8910-94df7bc7c349/scratchpad`.
  Allt kördes från projektmappen, i förgrunden, och vakten släppte igenom allt nedan:
  1. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
     scripts/tests` (hela sviten i projektet före alla ändringar: **4 375 passed**, antalet före)
  2. `mkdir -p <scratch>/kopia-6dfcdcd`
  3. `git archive --format=tar -o <scratch>/6dfcdcd.tar 6dfcdcd`
  4. `tar -x -f <scratch>/6dfcdcd.tar -C <scratch>/kopia-6dfcdcd`
  5. `cp -R scripts/tests/test_beslut_granskning_24.py <scratch>/kopia-6dfcdcd/scripts/tests/test_beslut_granskning_24.py`
  6. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-6dfcdcd/scripts/tests/test_beslut_granskning_24.py` (**4 failed, 6 passed**, rött före)
  7. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rf
     -k beslut_granskning_24 scripts/tests` (den nya testfilen i projektet efter rättelsen: **10 passed**)
  8. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rf
     scripts/tests` (hela sviten efter rättelsen: **4 385 passed**)
  9. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rf
     scripts/tests` igen efter dokumentationen (se nedan)
  10. `git status`, `git log`, `git diff --stat`, `git add` och `git commit -F <scratch>/commit-….txt` (meddelandena
      skrivna med fil-verktyget i scratchpad), och `ls`, `cat`, `tail`, `grep` och `wc` för att läsa. Stycken av filer
      lästes med fil-verktyget Read.
  Vakten stoppade fyra kommandon som skrevs i strid med SPEC 7.1, alla bara läsande (ett `&&`, ett `grep` med `\` i
  mönstret, två `sed` och ett `git -C`); de gjordes om eller ersattes med fil-verktyget Read.
- **Testsviten:** 4 385 passed (före: 4 375), 0 röda, med kommandot i SPEC 7.1.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b, aecccdf, 6dfcdcd, bbb183a och den här commiten. `main` på GitHub
  står på 7d8cae9.

## Läge 2026-10-30, rättelserna efter granskning 23

Steg i byggplanen: 22 (pågår)

- **Granskning 23** (av d5b2fba, skriven i 269d641) är gjord i en ny session som inte sett rättelsesessionen: **gult**.
  Inget kan bokföras och ingen spärr har blivit svagare (P8). P1 och P2 från granskning 22 är i stort sett rättade,
  men P1 hade en lucka: K5 och K8 prövades mot förslagets regel, inte underlagets egen (P1). Öppet 27 saknade två
  namn (P3). Granskaren bedömde avsteget i rättelsesessionen som inom SPEC 7.1, men kommandona var inte nedskrivna
  (P7). Granskningen uppdaterade inte PROGRESS.md och BYGGPLAN.md, eftersom uppdraget sa "Ändra ingen annan fil"
  (P9); det görs här.
- **Hugos beslut 2026-10-30 om granskning 23**, skrivna i chatten i den här sessionen och ordagrant i `GRANSKNING.md`,
  "Hugos beslut 2026-10-30 om granskning 23": (1) P1: K5, K7 och K8 prövas mot varje underlags egen regel, och ett
  underlag utan egen regel stoppar förslaget. (2) P3: betalsätten i kassareglerna och företagets namn prövas mot de
  reserverade orden, bara exakt träff. (3) Öppet 29: vid K4a och K4b stoppas båda underlagen i paret, vid K4c bara
  det flaggade, och originalets förslag märks med K4-ärendets id. (4) P7: ny regel i CLAUDE.md om att körningar mot
  en kopia och av enskilda testfiler skrivs i PROGRESS.md med exakt kommando. (5) P9: steg 22 räknas som klart först
  efter en kort oberoende granskning av den här rättelsen.
- **P1, byggt i 13126d2:** `_kontrollera_underlagen` i `scripts/konteringsforslag.py` slår upp varje underlags egen
  regel med `Regelbok.regel_for_underlag` på underlagets datum (som flödena) och kör K5, K7 och K8 mot den. Ett
  underlag utan regel på sitt datum stoppar förslaget med kontrollen "ursprung" och texten att det ska vara ärendet
  "ny motpart". Granskarens prov B (momsfilen får varugruppen `kostnad` med 12 %, och ett förslag byggs för hand med
  `R-BANK-AVGIFT` för SYNT-U-2025-028 och SYNT-U-2025-019 med bankrad 117 i januari som avgift) stoppas nu av K8
  respektive K5, med underlagets egen regel i felet. Granskning 23, P2 (`KeyError` i samma prov med testbutikens
  momsfil) försvinner i `skapa_konteringsforslag`. `kontrollera_underlag` tar fortfarande emot regeln från anroparen,
  och ger fortfarande `KeyError` om någon anropar den direkt med en regel för bankrader och en momsfil utan
  varugruppen: det är inte rättat, eftersom bara `skapa_konteringsforslag` skulle rättas, och flödena anropar den
  bara med underlagets egen regel. **Inte byggt (för Hugo att avgöra):** ett underlag under en bankregel där
  underlagets kostnad står på bankregelns konto (till exempel 003 med 12 % på 6570 under `R-BANK-AVGIFT`) godtas
  fortfarande när underlagets egen regel godtar satsen: K5 prövar satsen, inte vilket konto raden står på, och
  ursprungskontrollen punkt 8 godtar kontot eftersom det står i förslagets regel. Flödena bygger inte så.
- **P3, byggt i 35afa8b:** `las_regelbok` prövar betalsätten i en Z-regels `kontering` och företagets namn
  (`foretag`) med `inget_reserverat_namn`, samma exakta träff som de andra namnen. `Bankavgift AB` och
  `bankavgifter` godtas. SPEC 7, `foretag/README.md`, `reserverade_namn.py` och `las_regelbok.py` räknar upp de två.
- **Öppet 29, stängd, byggt i 35afa8b:** i `kontera_period` stoppas vid K4a, K4b och "K4a och K4b" också originalet
  (underlaget flaggan jämför med), som får ett eget ärende med samma kontroll och typ, texten att båda stoppas, och
  sin bankrad och regel. Vid K4c stoppas bara det flaggade, och originalets förslag får i motiveringen texten
  "Märkning K4c: underlaget '<id>' är flaggat ... som möjlig dublett ..." (`konteringsfloden.MARKNING_K4C`). Ett
  ärende har inget eget id, så märkningen använder det som pekar ut ärendet: kontrollen K4c och det flaggade
  underlagets id. Märkningen ligger i motiveringen eftersom förslaget inte har något annat fält för text till
  godkännaren; nivåsteget (uppgift 6) kan använda den. **Val i sessionen, för Hugo att bekräfta:** att märkningen
  är text i motiveringen och inte ett eget fält i förslaget.
- **Följd för ett gammalt test:** `test_konteringsfloden.py::test_k5_moms_inom_toleransen_godtas` ändrade bara 003,
  och då blev 004 (dubletten) K4a mot 003, så att båda stoppades enligt Öppet 29. Testet ändrar nu 004 likadant, så
  att 004 förblir en dublett (K4). P2-testet i `test_beslut_granskning_22.py` följer Öppet 29 (originalet får
  förslag bara vid K4c).
- **P7:** regeln står i CLAUDE.md ("Så arbetar vi"), och kommandona i den här sessionen står nedan.
- **P9:** steg 22 räknas som klart först efter en kort oberoende granskning av 13126d2 och 35afa8b (BYGGPLAN.md,
  "Läge nu").
- **Rött före** (`scripts/tests/test_beslut_granskning_23.py` mot en kopia av d5b2fba): **19 röda och 3 gröna av 22**
  i den slutliga versionen. De tre gröna är skydd som ska vara gröna före: ett underlag under sin egen regel godtas,
  längre namn än det reserverade ordet godtas, och `kontrollera_underlag` svarar inte K8 med bankregeln (det är
  luckan testet beskriver). Prov B var rött med "DID NOT RAISE" för både 019 och 028, som granskaren såg, och med
  testbutikens momsfil med `KeyError: 'kostnad'` (granskning 23, P2). En första version av filen gav 20 röda och 2
  gröna: testet för `kontrollera_underlag` var då rött med `KeyError`, för att det anropade kontrollen med bankregeln
  mot testbutikens momsfil, alltså rött för P2:s krasch och inte för det som testet skulle visa. Det skrevs om till
  prov B:s momsfil och är grönt före. Det ändrade P2-testet i `test_beslut_granskning_22.py` mot samma kopia: 2 röda
  (k4a och k4b, originalet fick förslag) och 32 gröna.
- **Kommandon i den här sessionen** (P7). `<scratch>` är sessionens scratchpad-mapp,
  `/private/tmp/claude-501/-Users-hugolindholmer-VERA-agent/ed6565a5-1c77-43a3-8f42-a2bb02aedafa/scratchpad`.
  Allt kördes från projektmappen, och vakten släppte igenom allt nedan:
  1. `mkdir -p <scratch>/kopia-d5b2fba`
  2. `git archive --format=tar -o <scratch>/d5b2fba.tar d5b2fba`
  3. `tar -x -f <scratch>/d5b2fba.tar -C <scratch>/kopia-d5b2fba`
  4. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q
     <scratch>/kopia-d5b2fba/scripts/tests` (hela sviten mot den orörda kopian: **4 353 passed**, antalet före)
  5. `cp -R scripts/tests/test_beslut_granskning_23.py <scratch>/kopia-d5b2fba/scripts/tests/test_beslut_granskning_23.py`
  6. `cp -R scripts/tests/test_beslut_granskning_22.py <scratch>/kopia-d5b2fba/scripts/tests/test_beslut_granskning_22.py`
  7. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-d5b2fba/scripts/tests/test_beslut_granskning_23.py` (20 röda, 2 gröna; efter omskrivningen av
     ett test och kommando 5 igen: 19 röda, 3 gröna)
  8. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rA
     <scratch>/kopia-d5b2fba/scripts/tests/test_beslut_granskning_22.py` (2 röda, 32 gröna)
  9. `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rf
     scripts/tests` (hela sviten i projektet, två gånger: 2 röda efter kodändringarna, se "Följd för ett gammalt
     test", och sedan **4 375 passed**)
  10. `git status`, `git diff --stat`, `git add` och `git commit -F <scratch>/commit-….txt` (meddelandena skrivna med
      fil-verktyget i scratchpad), och `ls`, `cat`, `grep` och `wc` för att läsa.
  Dessutom startades hela sviten en gång i bakgrunden i projektet före alla ändringar; utskriften lades av Claude Code
  utanför scratchpad, där vakten inte låter den läsas, så antalet före togs i stället från kommando 4. Vakten
  stoppade åtta kommandon som skrevs i strid med SPEC 7.1, alla bara läsande (ett `&&`, fyra `sed`, ett `git -C`,
  ett `grep` med `\` i mönstret och ett `tail` mot filen utanför scratchpad); de gjordes om eller ersattes med
  fil-verktyget Read.
- **Testsviten:** 4 375 passed (före: 4 353), 0 röda, med kommandot i SPEC 7.1.
- **Opushat:** d5b2fba, 269d641, 13126d2, 35afa8b och den här commiten. `main` på GitHub står på 7d8cae9.

## Läge 2026-10-30, rättelserna av P1 och P2 efter granskning 22

Steg i byggplanen: 22 (pågår)

- **Hugos beslut 2026-10-30 om granskning 22** står ordagrant i `GRANSKNING.md`, "Hugos beslut 2026-10-30 om
  granskning 22", och är byggda i den här sessionen. Inget är granskat oberoende än.
- **P1, K5, K7 och K8 i `skapa_konteringsforslag`:** kontrollerna ligger nu i `scripts/konteringsforslag.py`
  (`kontrollera_underlag`), och `skapa_konteringsforslag` kör dem på varje underlag i förslaget, efter K2 och
  ursprungskontrollen. Funktionen tar därför emot momsfilen (`momssatser`, från `las_momssatser`, den som regelboken
  kontrollerades mot), och ett förslag med underlag utan momsfil stoppas. Flödena i `konteringsfloden.py` anropar
  inte längre K5, K7 och K8 för sig: de frågar `kontrollera_underlag` för att göra ärenden, och förslaget
  kontrollerar sedan samma sak igen. Förslagets `kontroller` visar K5, K7 och K8 som "ok" för förslag med underlag.
  Granskarens prov (ett förslag för SYNT-U-2025-019 byggt direkt, utan flödena) stoppas nu med kontrollen K5, och
  samma för SYNT-U-2025-028 (K8) och ett underlag från ägaren (K7). Genvägstestet `test_inga_genvagar.py` är kvar
  och kompletterat: det kontrollerar genom att läsa koden att `skapa_konteringsforslag` anropar kontrollen för
  underlag, och dess text säger vad det täcker och inte (SPEC 7).
- **P2, K4 i flödena:** ett underlag som underlagsperiodens K4 har flaggat (K4, K4a, K4b eller K4c) får inget
  förslag alls och inga andra ärenden, och varje K4-ärende följer med i `Konteringsresultat.arenden` med
  underlagsperiodens kontroll, dess text som typ, och underlagets bankrad och regel om de finns. Nivån är None och
  märkningen "kräver mänsklig bedömning" False: nivån sätts i nivåsteget (DESIGN 5 säger C). Underlaget som flaggan
  jämför med (lägst id) rörs inte och får sitt förslag, som när K4 behåller originalet. **Val i sessionen, för
  Hugo att bekräfta:** att bara det flaggade underlaget stoppas, inte båda i paret.
- **Öppet 27, stängd:** reserverade ord (`scripts/reserverade_namn.py`, ny modul, i dag bara `bankavgift`) stoppar
  alla namn i konfigurationen vid exakt träff efter normaliseringen: bankformatets kolumnnamn, kassaformatets
  kolumnnamn, postnamn, betalsätt och kassaregister, kontoplanens kontonamn, momsfilens varugrupper,
  matchningsformatets regelnamn, och regelbokens regel-id, motparter, kassaregister och ägare. "Bankavgift AB" och
  "bankavgifter" godtas. Listan flyttad från `las_matchningsformat.py` till den nya modulen.
- **Öppet 28, stängd:** de tre valen bekräftade, och `las_regelbok` stoppar `flode` på en regel för bankrader vars
  regel i `matchning.json` gäller pengar in (granskning 22, P7).
- **P3:** Q2-avtrycket i `test_beslut_q2.py` räknas med det gamla regelnamnet `bankavgift`, se raden för ded669d
  under Klart.
- **BYGGPLAN.md:** raden "Opushat" under "Läge nu" rättad: GitHub stod på 7d8cae9, i fas med lokalt, före den här
  sessionens commit.
- **Rött före:** `scripts/tests/test_beslut_granskning_22.py` kördes mot en kopia av 7d8cae9 i scratchpad: 32 röda och
  2 gröna av 34. De två gröna är skydd som ska vara gröna före (namn som bara liknar ett reserverat ord godtas, och
  `flode` på en regel för pengar ut godtas). Granskarens prov var rött för att ett förslag skapades ("DID NOT
  RAISE"), P2-testerna för att kopian fick ett förslag och 004:s ärende saknades, Öppet 27 och 28 för att filerna
  godtogs. Testerna för K5, K7 och K8 direkt mot `skapa_konteringsforslag` var röda för att parametern `momssatser`
  inte fanns.
- **Testsviten:** 4 353 passed, 0 röda, med kommandot i SPEC 7.1.
- **Opushat:** den här commiten. Allt före den är pushat (7d8cae9).

## Läge 2026-10-29, ny inställningsfil installerad och kontrollerad

Steg i byggplanen: 12 (klart)

- **Den nya inställningsfilen är installerad på Hugos dator** (7deaadb, summan
  `149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2`), och kontrollen efter bytet är **grön**
  (`GRANSKNING.md`, "Kontroll efter bytet av inställningsfil, 2026-10-29"). Steg 1, 5 och 10–13 gjorde Hugo själv
  (Hugos besked i chatten 2026-10-29). Steg 2, 3 och 9 gjordes i den här sessionen: `ls; ls` och `date` stoppades med
  "Stoppat av vakten", `git status` gick igenom efter Hugos ja, och testsviten var grön.
- **Läget Auto får nu användas på Hugos dator** (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto
  tillåts igen"). Villkor tills steg 15 (sandlådan) är klart:
  1. Shop and Gos riktiga underlag ligger utanför `~/VERA`.
  2. Varje session börjar och slutar med `git status`.
  3. Nästa oberoende granskning kontrollerar att inget utanför projektet har ändrats.
- **Caspers dator:** Auto används där först när steg 14 och steg 8 i kontrollen är gjorda där.
- **Steg 12 i byggplanen är klart.** Pågående steg är nu bara 22 (uppgift 4, P1 och P2 kvar).
- **Inte rapporterat:** kontrollskriptet för skalet i kontrollen steg 1. Bytet av inställningsfilen ändrar inte skalet.
- **Testsviten:** 4 312 passed, 0 röda (oförändrat), med kommandot i SPEC 7.1.
- **Opushat:** e4d8cd7 och commitarna efter den, och den här.

## Läge 2026-10-29, ny version av inställningsfilen (Auto tillåts igen)

Steg i byggplanen: 12 (ny version av inställningsfilen, pågår tills Hugo har installerat om)

- **Hugos beslut 2026-10-29: läget Auto tillåts igen** (vänder P6 från granskning 12). Beslutet står ordagrant i
  `GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen". Grund: steg 8 i kontrollen efter installationen är gjort
  (175db51), vakten körs före behörighetsfrågan i alla lägen, och förbudslistan gäller oförändrat.
- **Villkor tills steg 15 (sandlådan) är klart:**
  1. Shop and Gos riktiga underlag ligger utanför `~/VERA`.
  2. Varje session börjar och slutar med `git status`.
  3. Nästa oberoende granskning kontrollerar att inget utanför projektet har ändrats.
- **Byggt:** raden `"disableAutoMode": "disable",` är borttagen ur `sparr/managed-settings.json`, inget annat i filen
  är ändrat. Testet `test_installningarna_tillater_laget_auto_men_inte_att_hoppa_over_behorigheter` kräver att nyckeln
  saknas och att `disableBypassPermissionsMode` fortfarande är `"disable"` (rött före, grönt efter). Ny summa för
  inställningsfilen i INSTALLERA.md steg 5: `149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2` (förut
  `ab34081665b9052c1ff7c35a1b3a983107fc6a763f1f1aab6476523109cb80b0`). Summan räknades med Python i testet, eftersom
  `shasum` inte står på kommandolistan i SPEC 7.1. INSTALLERA.md har fått avsnittet "Byte av inställningsfil" och
  hänvisar till beslutet där den sa att Auto inte går att välja. SPEC.md är inte ändrad (den säger inte att Auto är
  avstängt).
- **Gäller först efter ominstallationen.** Inget installerades i den här sessionen. Tills Hugo har gjort om steg 10–13
  och kontrollen steg 1, 2, 3 och 9 gäller den installerade filen, där Auto är avstängt. Casper installerar den nya
  filen i steg 14.
- **Ingen ny granskning före bytet** (Hugos beslut 2026-10-29 i chatten, "Installera direkt"): filen i 7deaadb
  installeras utan en ny oberoende granskning. Undantaget gäller bara den filen. Nästa oberoende granskning tittar på
  ändringen i efterhand (`GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen").
- **Testsviten:** 4 312 passed, 0 röda (ett test ersatt av ett annat), med kommandot i SPEC 7.1.
- **Opushat:** e4d8cd7 och commitarna efter den, och den här.

## Läge 2026-10-29, efter steg 8 i kontrollen

Steg i byggplanen: 13 (klart)

- **Steg 8 i kontrollen efter installationen**, provet med en vakt som fallerar, är gjort på Hugos dator och
  **grönt** (`GRANSKNING.md`, "Steg 8, provet med en vakt som fallerar, 2026-10-29"). Hugo gjorde a–d själv i
  Terminal (Hugos besked i chatten 2026-10-29): med vakten undanflyttad stoppades `git status`, och också anropet för
  slutrapportrutan, med Claude Codes fel `can't open file … No such file or directory`. Vakten flyttades tillbaka, och
  kontrollsummorna stämde med INSTALLERA.md steg 5. Steg e gjordes i en ny session: `ls; ls` stoppades med "Stoppat av
  vakten", `git status` gick igenom. Steg 9 igen efter e (`date`) stoppades med "Stoppat av vakten" (Hugos svar i
  chatten 2026-10-29: "Kör date nu").
- **Steg 13 i byggplanen är klart.** Öppet 16 är stängd.
- **Vad det ändrar:** provet var ett av villkoren i B1 (Claude Code i det läge som frågar tills provet är gjort) och i
  Öppet 16 (före läget auto, före första hela körningen på riktiga underlag och före första kund). Det villkoret är
  nu uppfyllt. Inget annat ändras av det: läget auto är fortfarande avstängt i de låsta inställningarna, och sandlådan
  (steg 15) ska fortfarande vara klar före uppgift 5 och före första körningen på riktiga underlag.
- **Pågående steg** är nu bara 22 (uppgift 4, P1 och P2 kvar).
- **Testsviten:** 4 312 passed, 0 röda (oförändrat), med kommandot i SPEC 7.1. Testet
  `scripts/tests/test_byggplan_progress.py` ingår och är grönt. Vakten tillåter bara hela `scripts/tests` som mål,
  inte en enskild fil.
- **Opushat:** e4d8cd7 och commitarna efter den, och den här.

## Läge 2026-10-29, efter granskning 22 av uppgift 4

Steg i byggplanen: 22 (pågår) och 13 (pågår)

- **Granskning 22** (av d127c3e, skriven i e4d8cd7) är gjord i en ny session som inte sett bygget: **gult**. Inget
  kan bokföras och ingen spärr har blivit svagare. **P1 och P2** bör rättas eller beslutas före uppgift 5 (steg
  23). 7 frågor väntar på Hugo eller Casper (`GRANSKNING.md`, "Granskning 22 (av d127c3e)", "Beslut som behövs").
- **Namnet:** granskningen hette "Granskning 12" i e4d8cd7, men granskning 12 fanns redan (vakten, Q1). Rubriken är
  rättad till 22 enligt uppdraget i chatten 2026-10-29, som P8 föreslog.
- **BYGGPLAN.md och PROGRESS.md är ihopkopplade:** avsnittet "Läge nu" överst i BYGGPLAN.md, en Status-kolumn i
  tabellerna för fas C–H, tre nya regler i CLAUDE.md ("Så arbetar vi") och raden STEG I BYGGPLANEN i
  slutrapportrutan. Testet `scripts/tests/test_byggplan_progress.py` kräver att "Läge nu" och det här avsnittet
  stämmer, och att inga två granskningar har samma nummer. Testet undantar exakt rubriken "Granskning 11 – plan för
  Q1", som är en plan skriven i samma session som granskning 11, inte en egen granskning (Hugos beslut i chatten
  2026-10-29: rubriken räknas som en del av granskning 11, och undantaget står kvar).
- **Testsviten:** 4 312 passed (före: 4 304). Det nya testet är rött mot en kopia av e4d8cd7 i scratchpad (7 av 8;
  det åttonde är skyddet att undantaget för planen finns kvar, som ska vara grönt före) och grönt efter.
- **Opushat:** e4d8cd7 och commitarna efter den. Uppgift 4 och besluten efter den är pushade (d127c3e).

## Läge 2026-10-28, efter rättelsen av J1 (granskning 19)

**Rättat, inte granskat, inte installerat.** Besluten står i `GRANSKNING.md`, "Hugos beslut 2026-10-28 (efter
granskning 19)": meningen om I1 i SPEC 7.1 är godkänd, att I1 gäller fler sökvägar i kommandon är godkänt, J1
rättas före installationen, J2 under Öppet (punkt 12) och J3 prövas i spärrtestet efter installationen.
Sessionen kördes i läget auto (tillåtet enligt Hugos beslut 2026-10-28 kväll), och började och slutade med
`git status`. Inga sudo-kommandon körda, inget i `/etc` eller `/Library` ändrat, inget pushat, inga `git stash`.

- **J1** (ab305c7, 4bcbabe, ad85b8e): vakten startas med `/Library/Developer/CommandLineTools/usr/bin/python3`
  (Python 3.9.6 på Hugos dator), `-I` och `"onFailure": "block"`, i formen med `args`. Vakten fungerar med 3.9
  utan kodändring. Rökprovet (`test_beslut_granskning_19.py`) kör vakten med den Pythonen och hoppar över sig
  självt om den saknas. INSTALLERA.md har ett nytt steg 2 b där Hugo ser versionen och ägare och rättigheter för
  Pythonen, filen den leder till och alla mappar ovanför. Ingen rad med `sudo` är ändrad (21 rader).
- **Kontrollsummor (sha256)**, räknade med Pythons `hashlib` i en provfil i scratchpad:
  `sparr/kommandosparr.py` `314df00b4239877d21e0fef7d8f11c844a75d07276ad0af32baa94db8e92d10d` (ny),
  `sparr/managed-settings.json` `ab34081665b9052c1ff7c35a1b3a983107fc6a763f1f1aab6476523109cb80b0` (ny),
  `sparr/kontrollera-skalet.zsh` `10388d474a555e6d337a9468c5a1f5e2fd0ca04608e36024f73011dc5186d51f` och
  `requirements.txt` `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a` (oförändrade).
- **Testsviten:** 4 076 passed (före: 3 987 passed).
- **Nästa steg:** (1) **oberoende granskning 20** i en ny session, som bara gäller J1-ändringen (b9b49cc till och
  med den här commiten), med kontrollsummor, (2) en session provkör steg 4 h med Hugos OK (G1), (3) Hugo
  installerar enligt `sparr/INSTALLERA.md`.

## Läge 2026-10-28, efter rättelsen av I1 (granskning 18)

**Rättat, inte granskat, inte installerat.** Besluten står i `GRANSKNING.md`, "Hugos beslut 2026-10-28 (efter
granskning 18)". Sessionen kördes i läget auto (tillåtet enligt Hugos beslut 2026-10-28 kväll), och började och
slutade med `git status`. Inga sudo-kommandon körda, inget i `/etc` eller `/Library` rört, inget pushat, inga
`git stash`.

- **I1** (0c7cdcb): vakten stoppar varje sökväg vars första del direkt under roten börjar med punkt (`/.vol`,
  `/.nofollow`, `/.resolve` och liknande), oavsett stora och små bokstäver och extra snedstreck, före och efter
  att sökvägen har räknats om. Det gäller Write och Edit och sökvägar i kommandon. En mening i SPEC 7.1.
  93 nya tester (`test_beslut_granskning_18.py`). 64 är röda mot versionen före (f363b92), visat i en kopia i
  scratchpad: skrivverktygen släpptes igenom där, kommandona stoppades redan av andra regler men utan I1-skälet.
- **Kontrollsummor (sha256)** (43e2371), räknade med Pythons `hashlib` i en provfil i en ren kopia:
  `sparr/kommandosparr.py` `4b271e0aeb1a662133603f3c674ff98d37367ea6ea5786add9937e73e48a62cf` (ny),
  `sparr/managed-settings.json` `e1222e168de38f819ebf861319e9a9b2fc134ce52b3729ec23ceacb57682d463`,
  `sparr/kontrollera-skalet.zsh` `10388d474a555e6d337a9468c5a1f5e2fd0ca04608e36024f73011dc5186d51f` och
  `requirements.txt` `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a` (oförändrade).
- **I2–I8** står under Öppet, punkt 11.
- **Testsviten:** 3 987 passed (före: 3 894 passed).
- **Nästa steg:** (1) **oberoende granskning 19** i en ny session, som bara gäller I1-ändringen (f363b92 till och
  med den här commiten), med kontrollsummor, (2) en session provkör steg 4 h med Hugos OK (G1), (3) Hugo
  installerar enligt `sparr/INSTALLERA.md`.

## Läge 2026-10-28 kväll, efter rättelserna efter granskning 17

**Rättat, inte granskat, inte installerat.** Besluten står i `GRANSKNING.md`, "Hugos beslut 2026-10-28 (efter
granskning 17)" och "Hugos beslut 2026-10-28 kväll". Inga sudo-kommandon körda, inget i `/etc` eller `/Library`
rört, inget pushat.

- **H3** (653f0a4): regeln om prov och test står i CLAUDE.md och SPEC 7.1. En regel i text. Spärren är sandlådan.
- **H1 och H2** (3072393): kontrollskriptet läser med `ls -lde@` och godtar exakt en extra uppgift, och bara om
  den heter exakt `com.apple.provenance`. Andra namn, flera uppgifter och alla `+` avviker. G4-testet är grönt.
- **Steg 2 och 13 i INSTALLERA.md** (c7ba2b9): samma regel, i enkla ord för Hugo, och kommandona är `ls -lde@`.
  Projektets filer har `com.apple.provenance`, och `ditto` och `cp` tar med den till de installerade filerna.
- **H6** (6a488fd): vakten prövar Write och Edit (och MultiEdit och NotebookEdit om de kommer på listan) mot
  förbuden för fil-verktygen, utan hänsyn till stora och små bokstäver, med `~`, `../`, länkar och macOS andra
  namn för samma mapp. Samma förbud gäller mål och källor i kommandon. Där vakten stoppar jämförs sökvägar utan
  hänsyn till bokstäver. Om Claude Codes egna förbud gör samma sak prövas i spärrtestet efter installationen.
- **Kontrollsummor (sha256)** (235eab6), räknade med Pythons `hashlib` i testerna:
  `sparr/kommandosparr.py` `273e37f00faede9d3402c70fd7fdd585a97e064e21fbdd732018af273e5c2ad3`,
  `sparr/managed-settings.json` `e1222e168de38f819ebf861319e9a9b2fc134ce52b3729ec23ceacb57682d463` (oförändrad),
  `sparr/kontrollera-skalet.zsh` `10388d474a555e6d337a9468c5a1f5e2fd0ca04608e36024f73011dc5186d51f` och
  `requirements.txt` `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a` (oförändrad).
- **Läget:** första byggsessionen startade i Manual och bytte till auto mitt i H6. Den halvfärdiga H6-rättelsen
  lades undan med `git stash` och gjordes om från början. Två stashar med samma meddelande finns kvar (Öppet,
  punkt 10).
- **Testsviten:** 3 894 passed (före: 3 723 passed, 1 failed). Varje rättelse prövad mot en kopia av versionen
  före den.
- **Nästa steg:** (1) oberoende granskning 18 i en ny session, med kontrollsummor och med kontrollen att inget
  utanför projektet har ändrats, (2) en session provkör steg 4 h med Hugos OK (G1), (3) Hugo installerar enligt
  `sparr/INSTALLERA.md`.

## Läge 2026-10-28, efter rättelserna efter granskning 16

**Rättat, inte granskat, inte installerat.** Byggsession i läget Manual (`permissionMode: default`). Inga
sudo-kommandon körda, inget i `/Library` rört, inga filer i hemmappen ändrade, inget pushat. Besluten står i
`GRANSKNING.md`, "Hugos beslut 2026-10-28 (efter granskning 16)".

- **G3** (1dbedb1): `-R` borttaget ur `grep` i vakten och SPEC 7.1, i alla former (`-nR`, `-Rn`,
  `--dereference-recursive` och förkortningar). `-r` står kvar.
- **G7** (8cfba7c): `.ugrep` förbjuden. Vakten stoppar kommandon som skulle skriva en fil eller mapp med det
  namnet (som mål, som källa till `cp -R`, via en länk, oavsett stora och små bokstäver), och
  `managed-settings.json` har `Edit(//**/.ugrep)` och `Edit(~/.ugrep)`. `grep`-tillägg för en egen
  inställningsfil stod aldrig på listan.
- **G2 och G6** (43ea3b5): meningen i INSTALLERA.md steg 4 h (allt som inte är exakt de elva raderna: stoppa och
  fråga) och meningen i SPEC 7.1 om att Claude Codes `grep` inte söker i allt (texten godkänd av Hugo i chatten).
- **G4** (77dce23): ett test kör det riktiga kontrollskriptet så som Terminal startar, och kräver `OK`. **Fynd:**
  med det gamla skriptet skrev testet `AVVIKER: funktion: add-zsh-hook`, eftersom Apples Terminal-fil läser in
  zsh:s egen `add-zsh-hook`. Det hade troligen stoppat installationen i steg 4 g. Hugos beslut i chatten: skriptet
  godtar den bara från `/usr/share/zsh/<version>/functions`, med root som ägare. Skriptet har därför en ny
  kontrollsumma.
- **Kontrollsummor (sha256)** (58daf69), räknade med Pythons `hashlib` i en ren kopia:
  `sparr/kommandosparr.py` `b730b27fff418430983f7c06ca2f58b04c890d3ff3bc7c9bf1d832e64bbad481`,
  `sparr/managed-settings.json` `e1222e168de38f819ebf861319e9a9b2fc134ce52b3729ec23ceacb57682d463`,
  `sparr/kontrollera-skalet.zsh` `8ae712451b55f75dda5ecf429161ccbb34f1e98d90b53d03e5293319965e1583` och
  `requirements.txt` `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a` (oförändrad). Står i
  INSTALLERA.md steg 4 g och 5. Summorna efter granskning 16 (nedan) gäller inte längre, utom för
  `requirements.txt`.
- **Testsviten:** 3 724 passed, 0 misslyckade (före: 3 669). 57 nya tester i
  `scripts/tests/test_beslut_granskning_16.py`, och två fall borttagna (`grep -R` som tillåtet, och
  `add-zsh-hook` i listan över funktioner som avviker, som nu prövas i de nya testen). Varje rättelse prövad mot en
  kopia av versionen före den.
- **Nästa steg:** (1) en oberoende granskning (granskning 17) i en ny session, med kontrollsummor, (2) en session
  provkör steg 4 h med Hugos OK i chatten (G1), (3) Hugo installerar enligt `sparr/INSTALLERA.md`.

## Läge 2026-10-28, efter granskning 16 (av abd0745)

**Granskat, inte installerat.** Oberoende granskning 16 står sist i `GRANSKNING.md`, gjord i läget Manual.
Inga sudo-kommandon körda, inget i `/Library` rört, inga filer i hemmappen ändrade.

- **Hugos beslut 2026-10-28 (B1–B3):** `grep` med bara sökande tillägg och `find` borttaget (B1), skriptet
  strängare än 8 d (B2), och `.zwc` eller satt `ZDOTDIR` avviker (B3) är godkända. Regel: skriver skriptet
  `AVVIKER` vid installationen, stoppar Hugo och frågar. Kontrollen lättas aldrig på plats.
- **Fynd:** inget allvarligt och inget på nivån medel. Sju låga (G1–G7), under "Öppet", punkt 9. Enligt
  stoppregeln kan vakten installeras.
- **`grep` i agentens skal** är bekräftat: Claude Codes funktion, som kör Claude Codes program med namnet
  `ugrep` (läser ingen `.ugrep` av sig själv). Inget sätt att ta sig förbi vaktens lista hittades.
- **Kontrollsummor (sha256)** för installationen, steg 5: `sparr/kommandosparr.py`
  `3d65477403d324c692d54fd676460ac506382173f430d190a6b5a24197cca5e3`, `sparr/managed-settings.json`
  `7d44e7c3123f4a2cdc95459c810e07149ddc492cc5b689053a5851ee4b15ac9c`, `requirements.txt`
  `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a`. Kontrollskriptet
  `4038b5eb32fadc7621ce69aa0fa5f4a511c0bc0ff70f5ee3f25a2260b016eb3d` stämmer med steg 4 g.
- **Före installationsdagen** (förslag i granskningen): Hugo kör fyra läsande kommandon i Terminal för att se
  om filerna som skriptet prövar har `@` eller `+` (G4, `GRANSKNING.md`, granskning 16, punkt 2), och en
  session provkör kommandot i steg 4 h med Hugos OK (G1).
- **Testsviten:** 3 669 passed, 0 misslyckade (körd i granskning 16 med `.venv/bin/python`).

## Läge 2026-10-28, efter Hugos beslut om granskning 15

**Byggt** (inte installerat, inte granskat, inga `sudo`-kommandon körda, inget i `/Library` rört, inga filer
i hemmappen ändrade, inga kontrollsummor för filerna som ska installeras). Besluten och detaljerna står i
`GRANSKNING.md`, "Hugos svar 2026-10-28 efter granskning 15".

- **S1:** `find` är borttaget ur listan i SPEC 7.1 och ur vakten. `grep` står kvar, men bara med tillägg som
  söker, eftersom verktyget Grep inte finns i skrivbordsappen (sett i byggsessionen). `rg` har aldrig stått
  på listan. Granskarens väntade tester för S1 är gröna.
- **S2:** förbud för den kompilerade versionen (`.zwc`) av varje förbjuden zsh-startfil och av
  `~/.zcompdump`. Granskarens väntade test för S2 är grönt.
- **S3:** INSTALLERA.md steg 4 h: agenten kör en fast, läsande kontroll i sitt eget skal före installationen.
- **S5:** SPEC 7.1 säger hur `grep`, `find` och `rg` hanteras. **S6:** steg 5 och 12 kontrollerar
  `requirements.txt`. **8 d:** Terminals två namn i kroklistorna, med ursprung och ägare, i skriptet.
- **Förenklingen:** historiken är flyttad ur INSTALLERA.md, och kontrollerna i steg 4 ligger i
  `sparr/kontrollera-skalet.zsh`, som Hugo kör i Terminal efter att ha kontrollerat dess kontrollsumma.
- **`cd ~/VERA/agent`** i stället för `cd ~/VERA` i INSTALLERA.md, SPEC 7.1 och PROGRESS.md.
- **Testsviten:** 3 669 passed, 0 misslyckade och inga väntat röda (före: 3 469 passed och 7 xfailed).
- **Beslut som behövs:** se `GRANSKNING.md`, "Hugos svar 2026-10-28 efter granskning 15". Därefter en ny
  oberoende granskning, med kontrollsummor, före installationen.

## Läge 2026-10-28, efter Hugos beslut om granskning 14

**Byggt** (inte installerat, inte granskat, inga `sudo`-kommandon körda, inget i `/Library` rört, inga filer
i hemmappen ändrade, inga kontrollsummor). Besluten och detaljerna står i `GRANSKNING.md`, "Hugos svar
2026-10-28 efter granskning 14".

**Steg 1: kan Bash-verktyget köras i `/bin/bash` i stället för zsh?** Läst i Claude Codes dokumentation
2026-10-28.

- **(a) Kan `CLAUDE_CODE_SHELL` sättas i `env` i den låsta inställningsfilen, och gäller den då i
  skrivbordsappen?**
  - Variabeln finns: "Set the shell Claude Code uses to run Bash tool commands. Accepts a path to a `bash` or
    `zsh` binary … If the value is not a working `bash` or `zsh` path, Claude Code ignores it and falls back
    to auto-detection" ([env-vars](https://code.claude.com/docs/en/env-vars), tabellen "Variables").
  - `env` får stå i den låsta filen ("Managed settings | Everyone in your organization",
    [env-vars, "Set variables in settings files"](https://code.claude.com/docs/en/env-vars)), och
    `CLAUDE_CODE_SHELL` står inte bland variablerna som Claude Code bortser från i `env`
    ([settings-reference, "Variables Claude Code ignores in env"](https://code.claude.com/docs/en/settings-reference#env)).
    Ett värde där "overwrites the same variable exported in your shell" (samma ställe, "How env values
    interact with your shell"). **I Terminal: bekräftat.**
  - **I skrivbordsappen: inte bekräftat.** "When the Claude Desktop app … starts the session, the launch
    environment it builds takes precedence instead: Claude Code ignores an `env` value from any settings
    file for a variable the launch environment already sets" (samma ställe). Appen tar med det som
    inloggningsskalet exporterar ("When Desktop starts, it reads what your login shell exports",
    [desktop](https://code.claude.com/docs/en/desktop)). Dokumentationen säger inte om startmiljön har
    `CLAUDE_CODE_SHELL`. Inte heller bekräftat: att skalet väljs efter att `env` från inställningarna har
    lagts in.
- **(b) Vilka filer läser Claude Code in när skalet är bash?** "At session start, Claude Code sources
  `~/.zshrc`, `~/.bashrc`, or `~/.profile` depending on your shell, captures the resulting aliases,
  functions, and shell options, and applies them to every Bash command"
  ([tools-reference, "What persists between commands"](https://code.claude.com/docs/en/tools-reference)).
  Alltså `~/.bashrc` eller `~/.profile`. När det är `~/.profile`: **inte bekräftat**. `~/.bash_profile`,
  `BASH_ENV` och systemets filer (`/etc/profile`, `/etc/bashrc`): **inte bekräftat** (nämns inte).
- **(c) Kan User-, Project- eller Local-inställningar skriva över den?** Nej: "Between settings files, `env`
  values follow settings precedence, so a managed settings entry overrides the same variable in user or
  project settings" ([env-vars, "Precedence"](https://code.claude.com/docs/en/env-vars)), och "Nothing in
  your own settings files or `--settings` overrides a managed key"
  ([settings, "Settings precedence"](https://code.claude.com/docs/en/settings)). **Bekräftat.** Men appens
  startmiljö går före alla inställningsfiler, också den låsta (a).

**Slutsats: zsh-vägen byggdes, inte bash-vägen**, eftersom (a) inte är bekräftat för skrivbordsappen, där
agenten körs. `CLAUDE_CODE_SHELL` är inte satt. Förbuden för `~/.bashrc`, `~/.bash_profile` och `~/.profile`
fanns redan och står kvar.

- **R1:** förbud för `~/.zcompdump` och `~/.zcompdump*`, och INSTALLERA.md steg 4 i: Hugo kontrollerar
  mapparna i zsh:s `fpath` med `print -rl -- $fpath` och `ls -ld`. Granskarens väntade test är grönt.
- **R2:** INSTALLERA.md steg 4 h, på båda datorerna: `grep` visar raderna i zsh:s fyra startfiler som läser
  in filer eller kör kod. Väntat: bara nvm:s två rader. Avsnittet "Caspers dator" pekar på steget.
- **R3:** kontrollen av alias och funktioner är vänd: `alias` (väntat exakt två rader), `alias -s` (väntat
  ingenting) och ett kommando som bara visar oväntade funktioner och sist `SLUT` (väntat bara `SLUT`).
  `typeset -f +` används inte längre: efter nvm:s `compinit` visar det 976 namn.
- **R4:** SPEC 7.1 säger att vakten prövar mappen där varje länk ligger, inte länkfilen själv. Koden är inte
  ändrad.
- **R5:** INSTALLERA.md säger vad som syns när steg 4 a och 6–11 går bra (ingenting), vilka fel som stoppar,
  steg 4 d och 4 e utan nvm, och att Caspers installation inte går att kontrollera utan Claude Code för
  Terminal. En allmän regel i "Innan du börjar": visar ett kommando något annat, stoppa och fråga.
- **Tester:** 56 nya i `scripts/tests/test_beslut_granskning_14.py`, `ALIAS_KOMMANDON` och listan över
  kommandon i INSTALLERA.md ändrade i `test_kommandosparr.py`, markeringen `xfail` borttagen i
  `test_granskning_14.py`. Hela testsviten: **3 434 passed**, 0 misslyckade.

**Hugos svar 2026-10-28 efter granskning 14, fortsättning:** (1) ja till listan över väntade funktioner,
med tillägget att steg 4 g också visar att zsh:s kroklistor är tomma och att de särskilda funktionerna
(`preexec`, `precmd`, `chpwd`, `periodic`, `zshexit`, `command_not_found_handler` och `TRAP…`) inte finns.
Byggt, med 21 tester, före och efter installationen. (2) Steg 4 h gäller båda datorerna. (3) Bash-vägen
prövas inte nu (Öppet, punkt 7). Testsviten: se överst.

**Inte bekräftat:** om Terminal själv lägger in sina funktioner i en kroklista. Gör det det, stoppar Hugo i
steg 4 g, och då behövs ett beslut om just de namnen.

**Beslut som behövs:** en ny oberoende granskning av den nya versionen, med kontrollsummor, före
installationen.

## Läge 2026-10-28, efter Hugos beslut om granskning 13

**Byggt** (inte installerat, inte granskat, inga `sudo`-kommandon körda, inget i `/Library` rört, `~/.zshrc`
och andra filer i hemmappen inte ändrade, inga kontrollsummor). Besluten och detaljerna står i
`GRANSKNING.md`, "Granskning 11 – plan för Q1", "Hugos beslut 2026-10-28 om fynden i granskning 13".

- **P1 a:** INSTALLERA.md steg 4 g och kontrollen efter installationen, steg 1: Hugo kör `alias` och
  `typeset -f +` i Terminal och stoppar om ett namn på listan i SPEC 7.1 (eller ett namn med `/`) finns där.
- **P1 b:** förbud i `sparr/managed-settings.json` för filerna som zsh läser vid start och filerna de läser
  in: `~/.nvm/**`, `~/.zkbd/**`, `~/.zsh_sessions/**`, `~/.zlogout` och zsh-filerna i `/etc` (de fyra i
  hemmappen var redan förbjudna). På Hugos dator läser `~/.zshrc` in `~/.nvm/nvm.sh` och
  `~/.nvm/bash_completion`. INSTALLERA.md "Efteråt", punkt 10: vad Hugo gör med en ny `source`-rad.
- **P2 a:** vakten prövar varje länk i kedjan (`_saker_kedja`). Granskarens väntade test är grönt.
- **P3 b:** INSTALLERA.md använder `~/.local/bin/claude --version`, `~/.local/bin/claude update` och
  `~/.local/bin/claude`, och varnar för installerarens förslag. `PATH` ändras inte. SPEC 7.1 är ändrad till
  samma sak (med beslutet angivet).
- **P4 a:** förbud för `~/.local/bin/claude`, `~/.local/share/claude/**`, skrivbordsappens Claude Code och
  appen (se nedan).
- **Fråga 2:** INSTALLERA.md säger att Claude Code för Terminal omfattas av samma låsta inställningar.
- **Tester:** 31 nya i `scripts/tests/test_beslut_granskning_13.py`, tre ändrade i `test_kommandosparr.py`.
  Hela testsviten: **3 350 passed**, 0 misslyckade.

**Vad som hittades om Claude Code och appen (P4 a, läst med `ls -l` 2026-10-28):**

- Claude Code för Terminal: `~/.local/bin/claude` → `~/.local/share/claude/versions/2.1.312`, allt ägt av Hugo.
- **Skrivbordsappens egen Claude Code** ligger i
  `~/Library/Application Support/Claude/claude-code/<version>/<kod>/claude.app/Contents/MacOS/claude`
  (versionerna 2.1.308 och 2.1.309 finns). Ägs av Hugo (`hugolindholmer staff`).
- **`/Applications/Claude.app` ägs av Hugo** (`hugolindholmer staff`), liksom mapparna i den.
  `/Applications` ägs av root med gruppen `admin` och kan skrivas i av gruppen (`drwxrwxr-x`).

**Hugos svar 2026-10-28 efter granskning 13, punkt 1–4** (besvarar besluten som behövdes efter bygget):

1. **P4:** förbuden räcker, ägandet ändras inte. Sandlådan ska förbjuda skrivning i appen, appens Claude
   Code och `~/.local/share/claude` (Öppet, punkt 4).
2. **P3 b:** `cd` står kvar först, före `~/.local/bin/claude`. Mappen är `~/VERA/agent` (rättat efter Hugos
   beslut 2026-10-28 efter granskning 15).
3. **Hela `~/Library/Application Support/Claude`** förbjuds för agentens fil-verktyg. Byggt, med test.
4. **Ändringen i SPEC 7.1** (P2 och P3 b) godkänns.

**Beslut som behövs:** en ny oberoende granskning av den nya versionen, med kontrollsummor, före
installationen. P5 (omvägarna i en kopia) görs i en egen session före uppgift 5 (Öppet, punkt 6).

## Läge 2026-10-28, efter Hugos svar 1–3

(Läget nedan gällde före Hugos beslut om granskning 13. Att `claude` inte hittas i Terminal gäller inte
längre: Claude Code för Terminal ligger i `~/.local/bin/claude` och startas med hela sökvägen.)

**Byggt** (inte installerat, inga `sudo`-kommandon körda, inget i `/Library` rört, `~/.zshrc` inte rörd).
Besluten och detaljerna står i `GRANSKNING.md`, "Granskning 11 – plan för Q1", "Hugos svar 2026-10-28 på de
öppna frågorna 1–3".

- **Svar 1, Cryptexes-mappen:** INSTALLERA.md steg 4 har raden som Hugo själv lägger sist i `~/.zshrc`, på
  sin och Caspers dator, och hur han kontrollerar `PATH` efteråt. Inget undantag i vakten. Nytt test: med
  Cryptexes-mappen först stoppas `git status`, med den sist går det igenom (både med en kopia av
  uppbyggnaden och med den riktiga mappen på den här datorn).
- **Svar 2, gamla `.venv`:** testsviten körs med `.venv/bin/python` tills den nya platsen finns. Efter
  installationen tas den gamla `.venv` bort (INSTALLERA.md, "Efteråt"), och listan i SPEC 7.1 pekar bara på
  den nya platsen.
- **Svar 3, Setting sources:** bara en annan låst källa underkänner installationen. `User settings`,
  `Project settings` och `Project local settings` är väntade. Raden läses i Terminal (`cd ~/VERA/agent`, `claude`,
  `/status`; mappen rättad efter granskning 15). Nytt sista steg i kontrollen efter installationen: agenten ombeds köra `date` i
  skrivbordsappen, och vakten ska stoppa det. Ersätter beslut 4 om vakten.
- **OVERLAMNING.md** nämner inte längre den gamla `.venv`.
- **Tester:** 8 nya, 508 för vakten. Hela testsviten: **3 312 passed**, 0 misslyckade.

**Att veta före installationen:** kommandot `claude` hittades inte i Terminal på Hugos dator 2026-10-28.
Svar 3 kräver det. Säger Terminal `command not found: claude`, stoppar Hugo och frågar (INSTALLERA.md steg
1). Claude Code för Terminal har ett eget versionsnummer, som också ska vara minst 2.1.295.

**Beslut som behövs:** en ny oberoende granskning av den nya versionen, med omvägarna (P1 från granskning
12) och PATH-regeln, och nya kontrollsummor. Därefter installerar Hugo enligt `sparr/INSTALLERA.md`.

## Läge 2026-10-28, efter Hugos beslut 1–4 om vakten

(Beslut som behövs 1–3 nedan är besvarade, se avsnittet ovan.)

**Byggt** (inte installerat, inga `sudo`-kommandon körda, inget i `/Library` rört). Besluten och detaljerna
står i `GRANSKNING.md`, "Granskning 11 – plan för Q1", "Hugos beslut 2026-10-28 om vakten, beslut 1–4".

- **Beslut 1:** projektets Python flyttas till `/Library/Application Support/ClaudeCode/vera/venv`. Vakten och
  SPEC 7.1:s pytest-rader pekar dit. Hugo skapar mappen och installerar pytest själv (INSTALLERA.md steg 9).
- **Beslut 2:** varje mapp i `PATH` före programmet ska ägas av root. Vakten byggd, och INSTALLERA.md steg 4
  beskriver hur Hugo själv flyttar nvm-mappen sist i `PATH`. Agenten har inte ändrat Hugos skalfiler.
- **Beslut 3:** filen själv och länkens mål ska ägas av root. Vakten gjorde redan så, nu med egna tester.
- **Beslut 4:** varje annan källa på raden Setting sources i `/status` stoppar installationen.
- **Tester:** 37 nya i `scripts/tests/test_kommandosparr.py` (500 för vakten). Hela testsviten: **3 304
  passed**, 0 misslyckade.

**Bash-verktygets PATH och vaktens PATH** (beslut 2, kontrollerat 2026-10-28 med en provfil i
scratchpad-mappen). Vaktens `PATH` är den som Claude Code själv startades med (Claude-appens `claude`,
version 2.1.309), och den får en vakt som Claude Code startar. **Svaret: de är exakt lika.** Båda är:

```
/Users/hugolindholmer/.nvm/versions/node/v24.18.0/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:
/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:
/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:
/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/pkg/env/global/bin:
/Library/Apple/usr/bin
```

(radbrutet här, i verkligheten en rad). nvm-mappen står först och ägs av Hugo, så **nvm-mappen behöver
flyttas bakåt** (INSTALLERA.md steg 4). Alla 13 program på listan ligger i `/usr/bin` eller `/bin`.

**Fynd som stoppar installationen tills vidare:** `/System/Cryptexes/App/usr/bin` står också före
`/usr/bin`. Den leder till `/System/Volumes/Preboot/Cryptexes`, som har rättigheterna 777, så vakten stoppar
alla kommandon också med nvm-mappen sist. Med både nvm-mappen och den mappen sist går alla 13 igenom (prövat
med den nya vakten mot Hugos riktiga `PATH`). Öppen fråga till Hugo eller Casper.

**Beslut som behövs:**

1. **Cryptexes-mappen:** (a) flytta också `/System/Cryptexes/App/usr/bin` sist med raden i `~/.zshrc`
   (rekommenderas, mappen har bara `safaridriver`), eller (b) ett undantag i vakten (rekommenderas inte).
2. **Övergången:** tills Python på den nya platsen finns körs testsviten med `.venv/bin/python` som förut
   (byggsessionens val, står i SPEC 7.1). Bekräftas?
3. **Följd av beslut 4:** finns `User settings` eller `Project settings` på raden Setting sources i dag,
   räknas installationen som misslyckad. Hugo läser raden i INSTALLERA.md steg 1, före installationen.
4. **Ny oberoende granskning** av den nya versionen, med omvägarna (P1 från granskning 12) och PATH-regeln,
   och nya kontrollsummor (beslut 5 från förra slutrapporten, inte besvarat).

`OVERLAMNING.md` nämner fortfarande `.venv/bin/python` för testsviten. Den är inte ändrad (uppdraget gällde
bara vakten, INSTALLERA.md, GRANSKNING.md och PROGRESS.md).

**Nästa steg:** Hugo eller Casper svarar på 1–3, sedan en byggsession för svaret på 1, sedan en oberoende
granskning.

## Läge 2026-10-28 kväll

**Byggt** (commit 1427105, efter Hugos beslut 2026-10-28 om PATH-regeln, förprovet för `onFailure` och P7):

- **Vakten** (`sparr/kommandosparr.py`): kommandolistan i SPEC 7.1, listan över tillåtna verktyg, och
  PATH-regeln (regel 7). Ett kommando släpps bara igenom om programmet, och varje mapp ovanför det, ägs av
  root och inte går att skriva i för gruppen eller andra. Kommandon som ändrar `PATH` stoppas.
- **Testerna** (`scripts/tests/test_kommandosparr.py`): 463 tester för vakten, de låsta inställningarna och
  INSTALLERA.md. Hela testsviten: **3 267 passed**, 0 misslyckade (körd 2026-10-28 kväll, före
  installationen).
- **INSTALLERA.md** (`sparr/INSTALLERA.md`): versionen med `/status`, mapparna ovanför med `ls -ld`,
  förprovet för `onFailure`, kontrollsummor, kopiering med `root:wheel` och 755 respektive 644, `ls -ld`
  igen efteråt, `/status` efter installationen och kontrollen efter installationen.

**Inget är installerat än.** Inget i `/Library/Application Support/` är ändrat.

**Beslut som behövs** (ordagrant från slutrapporten 2026-10-28):

1. Testsviten efter installationen. .venv/bin/python ligger i projektet, som Hugo äger, så båda
   pytest-kommandona stoppas. Vägar: (a) Hugo kör testsviten själv i Terminal, (b) pytest körs med en
   Python i en mapp som root äger, (c) .venv flyttas till en mapp som root äger. Påverkar "Varje rättelse
   får ett test".
2. Vakten prövar PATH i sin egen miljö. Har Bash-verktygets skal en annan PATH kan en annan fil köras
   (inte bekräftat). Ska varje mapp i PATH före programmet också ägas av root? Då måste nvm-mappen flyttas
   bakåt i Hugos PATH, annars stoppas allt.
3. Vakten kräver mer än beslutet: också filen själv och målet för en länk ska ägas av root. OK?
4. "En annan källa" i /status: bara låsta källor (t.ex. från claude.ai), eller varje källa på raden?
   INSTALLERA.md följer i dag ordalydelsen, det strängaste.
5. Ny oberoende granskning, med omvägarna (P1) och PATH-regeln, och nya kontrollsummor.

**Nästa steg:** Hugo fattar beslut 1–4, sedan en byggsession, sedan en oberoende granskning. (Beslut 1–4 är
fattade och byggda, se avsnittet ovan.)

## Klart

| Vad | Commit |
|---|---|
| Projektets grund: mappstruktur, `.gitignore`, belopp i öre och test att kärnan är generell | 649b258, d9a0ce3 |
| Syntetisk testdata för testbutiken, 2025 Q1 | 3fd797e |
| Inläsning av bankfil med K1 (saldokedjan) | b36ba6c |
| Rättelserna efter granskning 1 (F1–F11) och 2 (G1, G2, G4, G8) | 8ab3d15 till e9cfd6a, c6f84bf |
| Inläsning av Z-rapporter med K11 och K12 | a2d1540 |
| Rättelserna efter granskning 3 (H1, H2, H4, H6) och 4 (I1–I6) | f3ecc76, 6adbf24, 61a5946, 14c6bf0, da1be60, 0b2d41b |
| Inläsning av underlag med K4 (dubbletter), K4a, K4b och K13 | c4dd436, ca6867d |
| Matchning mot banken (`matcha_period`) med K3 | 2817f42, e3a618c, c46142f |
| Rättelserna efter granskning 5 och 6, bland annat K4c (möjlig dublett) | 60fbaa3, 5712b60 |
| Uppgift 1: kontoplan och momsfil (`las_kontoplan`, `las_momssatser`) | 5e1af42 |
| Uppgift 2: regelboken (`las_regelbok`), med ägare och närstående | 82b5e87, 3368f9e |
| Uppgift 3: konteringsförslaget (`skapa_konteringsforslag`) med K2 och ursprungskontrollen | 1c1bdc5 |
| Rättelserna efter granskning 7 (M1–M8 och M10–M12). M9 hör till uppgift 5 | 2a323d3, d04303a, 9e0462e |
| Rättelserna efter granskning 8 (N1–N4 och N7), och dokumentationen (N5 och N6) | ca2df6a, c2a8f2d |
| Granskning 8, N3, det som var kvar: `matcha_period` får regelboken, och ägarens bankrad kräver alltid underlag | ea51c97, de14da7 |
| Efter granskning 9: en saknad, tom eller oläsbar ägarlista stoppar körningen (a), och ägarens bankrad märks "kräver mänsklig bedömning" i matchningen och blir aldrig en vanlig matchning (b) | dd0e1cf |
| Efter granskning 10 (P1): en motpart i ägarlistan utan bokstäver och siffror, till exempel `-`, stoppar körningen | 16000a8 |
| Granskning 11, Q1: vakten för kommandolistan (`sparr/kommandosparr.py`), förslaget till låsta inställningar, INSTALLERA.md och SPEC 7.1 | f21a3a1, 773e919, 6686166 |
| Efter granskning 12 (Hugos beslut 2026-10-28): lista över tillåtna verktyg i vakten och SPEC 7.1 (P4), skills utan skalkommandon (P3), förbud för filen `.git` (P5), läget "auto" avstängt (P6), nya skrivförbud (beslut b), provet med en vakt som fallerar i INSTALLERA.md (P2, beslut a). **Inte granskad och inte installerad** | 5cb9080, 08a3370, c066188 |
| Granskning 11, Q3 och Q4 (Hugos beslut 2026-10-29): `sokform_for_namn` i `normalisering.py` för både sökningen och regelboken, och kommentaren överst i `las_regelbok.py` som SPEC 11. Granskad i granskning 21 | bd851ba, 2bc9762 |
| Granskning 11, Q2 (Hugos beslut 2026-10-29): ägaren känns igen utan accenter, bara i ägaruppslaget. Ny funktion `star_som_hela_ord_utan_accenter` i `normalisering.py`, som bara regelbokens ägaruppslag använder (bankraderna och kontrollen av `matchning.json`). `normalisera_for_jamforelse`, `sokform_for_namn` och `star_som_hela_ord` är oförändrade. SPEC 11, Ö5 och Ö13 uppdaterade. Granskad i granskning 21 | 3e3c18c, d7d38e0 |
| Granskning 11, Q2b (Hugos beslut 2026-10-29): accenter spelar ingen roll i någon ägarkontroll. `ar_agare_eller_narstaende` och kontrollen att en regel för ägarens underlag har nivå D använder den nya funktionen `normalisera_utan_accenter` i `normalisering.py`, som tar bort accenterna på samma sätt som `star_som_hela_ord_utan_accenter`. Dublettkontrollen i ägarlistan och kontrollen av tvetydiga regler är oförändrade. SPEC 11 och Ö13 uppdaterade. Granskad i granskning 21 | 1dcf769 |
| Granskning 21 av Q2, Q2b, Q3 och Q4 (3a2d4f6 till dcf3078): grön, inget allvarligt och inget medel. Tre låga fynd: L1 (DESIGN-regelbok.md och `foretag/README.md` om accenter) och L2 (matchningens egen kopia av `star_som_hela_ord` heter nu Q9) rättade i dokumentationen, L3 (ø, æ, ł och đ) som exempel i SPEC Ö5. Hugo godkände SPEC-texterna i d7d38e0 och dcf3078 i chatten 2026-10-29 | 3bbcbe4, och dokumentationen efter den |
| D13 och D14 beslutade för testföretaget (Hugos beslut i chatten 2026-10-29): bankavgifter utan moms med bankraden som underlag tills Ö11, allt annat från banken kräver faktura, och "bankens datum" är transaktionsdagen. Bara dokumentation | baec52b |
| Uppgift 4, del 1: flöde a (leverantörsfakturor) med K5, K7 och K8 i `scripts/konteringsfloden.py` (`kontera_period`), och nyckeln `bokforing` i regelboken (metod, verifikationsdatum och "antaget", Hugos OK i chatten 2026-10-29). Ärenden från K5 och K8 har nivå D och "kräver mänsklig bedömning" direkt (B2) | 4269f76 |
| Uppgift 4, del 2: flöde b (kvitton). SYNT-U-2025-028 blir K8, nivå D, SYNT-U-2025-004 får inget förslag | f6ed99e |
| Uppgift 4, del 3: flöde e (bankavgifter) enligt D13. En avgift över gränsen blir ett ärende med nivå D | e4cc538 |
| Hugos beslut efter uppgift 4 (a–f) inskrivna i `GRANSKNING.md`, och Öppet 21, 22, 24 och 25 stängda | 48e7ed3 |
| Beslut c: flöde e väljs bara med regelbokens nyckel `flode` (`"bankavgift"`). En regel för pengar ut utan nyckeln blir ett ärende, "regeln saknar flöde", nivå D. Reserverade namn: en regel i `matchning.json` eller ett regel-id får inte heta `bankavgift`, och testbutikens regel heter nu `bankens-avgifter`. 22 av 26 nya tester röda mot 48e7ed3. **Q2-avtrycket räknas med det gamla namnet** (granskning 22, P3, Hugos beslut 2026-10-30): `test_beslut_q2.py` byter `bankens-avgifter` tillbaka till `bankavgift` innan avtrycket räknas, så att avtrycket från före Q2 (f61eb4e) fortfarande visar att inget har ändrats. Avtrycket räknas inte om | ded669d |
| Hugos beslut 2026-10-30 om granskning 22: K5, K7 och K8 i `skapa_konteringsforslag` (P1), K4-flaggade underlag utan förslag och K4-ärendet i resultatet (P2), reserverade ord för alla namn i konfigurationen (Öppet 27) och `flode` stoppat på pengar in (Öppet 28). Ny modul `scripts/reserverade_namn.py`. 32 av 34 nya tester röda mot 7d8cae9. Granskat i granskning 23 (269d641, gult: P1 hade en lucka, rättad nedan) | d5b2fba |
| Hugos beslut 2026-10-30 om granskning 23: K5, K7 och K8 mot varje underlags egen regel, och ett underlag utan egen regel stoppar förslaget (P1); betalsätten i Z-reglerna och företagets namn prövas mot de reserverade orden (P3); K4a och K4b stoppar båda underlagen i paret, K4c bara det flaggade med märkning i originalets motivering (Öppet 29, stängd); regeln om kommandon i PROGRESS.md i CLAUDE.md (P7). 19 av 22 nya tester röda mot d5b2fba. Granskat i granskning 24 (6dfcdcd, grönt) | 13126d2, 35afa8b, aecccdf |
| Granskning 24 (av aecccdf): rättelserna efter granskning 23 är byggda som besluten säger, grönt. **Steg 22 klart** (Hugos beslut 2026-10-30 om granskning 24) | 6dfcdcd |
| Hugos beslut 2026-10-30 om granskning 24: förslagets regel ska vara underlagets egen regel, annars stoppas förslaget i `skapa_konteringsforslag` (Öppet 31, stängd); Öppet 30 stängd; ny regel i CLAUDE.md om granskningssessioner. 4 av 10 nya tester röda mot 6dfcdcd. Granskat i granskning 25 (grönt) | bbb183a, 277ca90 |
| Granskning 25 (av bbb183a och 277ca90): Öppet 31 är byggd som beslutet säger, inget hål i den nya kontrollen, grönt. P7: kostnaden kan stå på fel konto inom regeln för ett förslag förbi flödena (Öppet 32). Bara dokumentation | commiten "Granskning 25" |
| Hugos beslut 2026-10-30 om granskning 25: kostnadsraden i ett förslag med underlag står på det konto K5 ger för momssatsen, annars stoppas förslaget i `skapa_konteringsforslag` (Öppet 32, stängd, steg 91); Öppet 31 granskad och klar. 5 av 14 nya tester röda mot en kopia av 7c1f148, upprepat mot `git archive` av 7c1f148 i commit-sessionen. Hugos beslut 2026-10-30 om byggsessionen för Öppet 32: momsraden är Öppet 33, Öppet 32 och 26 är steg 91 och 92. Granskat i granskning 26 (gult: byggd som beslutet säger, ett hål kvar som Öppet 34) | c479915, d1ab489 |
| Granskning 26 (av c479915 och d1ab489): Öppet 32 är byggd som beslutet säger, granskarens två prov stoppas, gult. M1: kostnaden räknad som `skillnad` ur `belopp_ore` går förbi den nya kontrollen, för ett förslag förbi flödena (Öppet 34, väntar på beslut). Bara dokumentation | 994bcdf |
| Hugos beslut 2026-10-30 om granskning 26 ("Ja, i samma steg"): Öppet 33 och Öppet 34 byggda i ett steg, steg 93. Momsraden (`moms_ore`) står på kontot för ingående moms (Öppet 33, stängd); beloppet (`belopp_ore`) räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad (det sista byggsessionens tillägg), och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad` (Öppet 34, stängd). Docstringen om momsraden rättad (L1). 12 av 22 nya tester röda mot `git archive` av 5b4aa83. Granskat i granskning 27 (gult: byggt som beslutet säger, alla prov från granskning 26 stoppas; två hål kvar i en ny familj, Öppet 35) | 7801a64, 68e86bb |
| Granskning 27 (av 7801a64 och 68e86bb): Öppet 33 och 34 är byggda som beslutet säger, H7 och de fyra LUCKA-proven stoppas, gult. M1: beloppet i debet på leverantörsskulderna utan bankrad (fakturan spegelvänd, eller två lika stora fakturor mot varandra) godtas, för ett förslag förbi flödena (Öppet 35, väntar på beslut). Hugos beslut 2026-10-31: regeln om högst en rad behålls. Bara dokumentation | commiten "Granskning 27" |
| Hugos beslut 2026-10-31 om granskning 27: Öppet 35 byggd som steg 94. Ett underlags `belopp_ore` står i debet bara när förslaget har en bankrad, och i kredit bara när underlagets `underlag_ore` och `moms_ore` inte står i kredit (`_kontrollera_beloppssidan`, sist efter Öppet 33). Granskarens prov h1 och h2 stoppas. Kreditnotor kan inte läsas in i dag, så regeln stoppar ingen (test). 5 av 13 nya tester röda mot koden i b7d9fac. Granskat i granskning 28 (gult: byggt som beslutet säger, h1 och h2 stoppas; kravet på bankrad gäller per förslag, Öppet 36) | 109fdcf, f10c65b |
| Granskning 28 (av 109fdcf och f10c65b): Öppet 35 är byggd som beslutet säger ordagrant, h1 och h2 stoppas, "rött före" och sviten stämmer, gult. M1: kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 godtas ihop med en annan fakturas betalning eller en bankrad på fel konto, för ett förslag förbi flödena (Öppet 36, väntar på beslut). M2, utanför steget: ett underlag med belopp 0 stannar hela körningen (Öppet 37, väntar på beslut). Bara dokumentation | commiten "Granskning 28" |
| Hugos beslut 2026-11-04 om granskning 28: Öppet 36 byggd som steg 95 enligt granskarens (a). Varje rad med ett underlags `belopp_ore` i debet har en egen rad på bankkontot i kredit med samma belopp ur en bankrad, och varje bankkontorad räknas bara en gång (`_kontrollera_beloppssidan`, som fick kontoplanen som argument). Granskarens b1 och b3 stoppas; b2 godtas (konteringen är identisk med flöde a:s två förslag i samma förslag, Hugos beslut 2026-11-04 i chatten, Öppet 38 för redovisningskonsulten). Skyddstestet från steg 94 skärpt till f4 (L1). 4 av 9 nya tester röda mot koden i 3f36f6b. Steg 94 granskat och klart (beslut 3). Öppet 37 är steg 96 (beslut 2), inte byggd | 0708667, och dokumentationen efter den |
| Beslut f och e: `R-BUTIK-FORBRUKNING` (5460) och `R-LEV-TILLBEHOR` (4010), nivå B, i testbutikens regelbok, och testregeln för DESIGN 4b borttagen. SPEC 7 nämner `kontera_period` | 5753890 |
| Granskning 11, Q7 (Hugos beslut 2026-10-29): pusha som det är. Historiken skrivs inte om, och ingen tagg byts eller pushas. Repot på GitHub är privat och får inte göras publikt utan en ny genomgång av hela historiken först. `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd". Bara dokumentation | commiten "Q7 stängd: pusha som det är, repot förblir privat" |

## Öppet

1. **Granskning 10 (av dd0e1cf)** står sist i `GRANSKNING.md`. P1 är rättat i 16000a8 (Hugos beslut
   2026-10-28), P2 i texten i SPEC avsnitt 11 och P5–P6 i dokumentationen. Kvar från granskningen: P3
   (en ägarrad med ett skiljetecken intill namnet matchas aldrig mot sitt underlag, säker riktning) och P4
   (nivåsteget ska använda märkningen, uppgift 6). Listan över ägare och närstående ligger där agenten kan
   skriva, till spärrsteget (Hugos beslut i chatten 2026-10-27). 16000a8 och 10bfe0f är oberoende granskade
   i granskning 11 (P1 stängd, åtta fynd från Q1, det sista om namnet "Anna Nilsson" i ett test). Q7 är stängd
   (Hugos beslut 2026-10-29, se Klart). Q2, Q2b, Q3 och Q4 är byggda (Q2: 3e3c18c och d7d38e0, Q2b: 1dcf769, Q3: bd851ba, Q4: 2bc9762, Hugos beslut
   2026-10-29 om Q2–Q4) och granskade i granskning 21 (3bbcbe4, grön).
2. **N2, vilka tecken ett namn i regelboken får ha.** I dag får ett namn bara ha a–z med eller utan accent,
   0–9, mellanslag, bindestreck, understreck och punkt. Öppen fråga till Hugo eller Casper: ska fler tecken
   få finnas, till exempel `&` (som i "Café Ölund & Söner AB"), `/`, `,`, `'` och parenteser, och bokstäver
   som `Ø`, `Æ` och `ß`? I dag stoppas de (SPEC 7, DESIGN-regelbok.md avsnitt 8).
3. **Fyra val från rättelserna efter granskning 7 väntar på bekräftelse** (DESIGN-regelbok.md avsnitt 8,
   granskning 8:s punkt 6): regelbokens namn bara latinska, regel-id bara a–z, siffror och bindestreck, en
   roll per konto, och ägarens bankrader som hela ord. Valen gjordes i en byggsession, inte av en människa.
   BESLUTSFATTARE SAKNAS.
4. **Sandlådan (granskning 11, Q1).** Kommandolistan i SPEC 7.1 spärras av en vakt i Claude Codes låsta
   inställningar (planen står i `GRANSKNING.md` under "Granskning 11 – plan för Q1", bygget under "Bygget av
   vakten för Q1"). Vakten kan inte stoppa
   en egen testfil som körs med pytest och raderar eller skriver i projektet. Det stoppas av en **sandlåda**
   (ett skydd i macOS som gör att kommandon bara kan skriva i vissa mappar). **Öppen, inte byggd.** Hugos
   beslut 2026-10-28: sandlådan byggs i spärrsteget, men ska vara klar **före uppgift 5, eller före första
   hela körningen på riktiga underlag om den kommer först**. Hugos beslut 2026-10-28 efter granskning 15:
   **sandlådan görs direkt efter installationen**, och ska också täcka det som står i punkt 8. **Sandlådan ska förbjuda skrivning i appen
   (`/Applications/Claude.app`), appens Claude Code (`~/Library/Application Support/Claude/claude-code`) och
   `~/.local/share/claude`** (Hugos svar 2026-10-28 efter granskning 13, punkt 1). De ägs av Hugo, och
   förbuden i de låsta inställningarna stoppar bara agentens fil-verktyg, inte en egen testfil.
5. **Granskning 12 av vakten (2026-10-28)** står sist i `GRANSKNING.md`. Testsviten: 3 148 passed.
   Frågorna från bygget är besvarade, och kontrollsummorna står där. **Inte komplett:** punkt 3 (omvägar
   förbi vakten) gjordes inte, eftersom ett säkerhetsfilter stoppade den (P1, stoppar installationen).
   Övriga fynd: P2 (provet där vakten fallerar togs bort ur kontrollen efter installationen), P3 (skills
   som kör skalkommandon), P4 (kommandoverktyg känns igen på namnet), P5 (`.git` som fil), P6 (läget
   "auto") och P7 (rättigheterna på `/Library/Application Support`). **P2–P6 och beslut (a) och (b) är
   byggda** efter Hugos beslut 2026-10-28 (5cb9080, 08a3370, c066188). **PATH-regeln, förprovet för
   `onFailure` och P7 är byggda** efter Hugos beslut 2026-10-28 (`GRANSKNING.md`, "Beslut 2026-10-28:
   PATH-regel, förprov för onFailure, P7"). Kvar: P1 (omvägarna), att lägsta version för
   `disableSkillShellExecution` och `disableAutoMode` inte är bekräftad i dokumentationen, och ~~**beslutet om
   testsviten**: PATH-regeln stoppar båda pytest-kommandona efter installationen, eftersom
   `.venv/bin/python` ligger i projektet~~ (stängt: testsviten går med Python på den nya platsen, 4 076 gröna i
   spärrtestet 2026-10-29).
   Kontrollsummorna i granskning 12 gäller inte längre, eftersom vakten och inställningarna är ändrade.
   Provet med en vakt som fallerar visar att en **saknad** vakt stoppar (Python ger kod 2), men prövar inte
   `onFailure` i sig (INSTALLERA.md, steg 8).
6. **Granskning 13, P5: omvägarna förbi vakten med kommandotexter i en kopia.** Hugos beslut 2026-10-28 (P5
   a): görs i **en egen session före uppgift 5**. Granskning 12 och 13 kunde inte göra det provet, eftersom
   ett säkerhetsfilter i Claude Code stoppade svaret. Det som inte är uteslutet är framför allt sätt som zsh
   läser ett ord på som skiljer sig från vaktens uppdelning. **Öppen, inte gjord.** Dit hör också skalets
   inställningar (`setopt`), som Claude Code tar med från `~/.zshrc` till agentens kommandon och som
   kontrollen i INSTALLERA.md steg 4 g inte prövar (granskning 14, bygget efter Hugos svar 2026-10-28).
7. **Bash-vägen: Bash-verktyget i `/bin/bash` i stället för zsh** (`CLAUDE_CODE_SHELL=/bin/bash` i `env` i
   den låsta inställningsfilen). Hugos svar 2026-10-28 efter granskning 14, punkt 3: **prövas inte nu.**
   Den prövas **efter installationen, i samma veva som sandlådan** (punkt 4), med ett prov i
   skrivbordsappen. Skälet: dokumentationen bekräftar att variabeln gäller i Terminal och att User-,
   Project- och Local-inställningar inte kan skriva över den, men inte att den gäller i skrivbordsappen,
   eftersom appens startmiljö går före `env` i alla inställningsfiler (svaren med länkar: "Läge 2026-10-28,
   efter Hugos beslut om granskning 14", steg 1). Vilka filer bash läser in (`~/.bash_profile`, `BASH_ENV`)
   är inte heller bekräftat. **Öppen, inte gjord.**
8. **Det kontrollskriptet inte ser** (granskning 15, S4, godtagen av Hugos beslut 2026-10-28). Fällor satta
   med kommandot `trap` (till exempel `trap '…' DEBUG`, som körs före varje kommando), skalets tabell över
   program (`hash`, till exempel `hash git=…`, som får `git` att köra en annan fil oavsett `PATH`), och en funktion som heter
   `builtin` och härmar kontrollens svar. Alla tre kräver en rad i en startfil, som har förbud. De ska täckas
   av **sandlådan** (punkt 4). **Öppen, inte byggd.**
9. **De låga fynden i granskning 16** (av abd0745, `GRANSKNING.md`). Stoppregeln: de stoppar inte
   installationen. G1: de elva raderna i INSTALLERA.md steg 4 h är aldrig provkörda i agentens riktiga skal.
   G2: steg 4 h saknar meningen "inte exakt de elva raderna: stoppa och fråga". G3: `grep -R` följer länkar ut
   ur projektet (förslag: ta bort `-R`). G4: kontrollskriptet skriver aldrig OK om en prövad fil eller mapp har
   `@` eller `+`, och testet för OK prövar en ändrad kopia. G5: minst 40 av de nya och ändrade testerna är
   gröna redan före abd0745. G6: Claude Codes `grep` hoppar över filer i `.gitignore` och binära filer, vilket
   inte står i SPEC 7.1. G7: inget förbud för `.ugrep`, och skyddet bygger på hur Claude Codes funktion ser ut
   i dag. **Hugos beslut 2026-10-28: G2, G3, G4, G6 och G7 är rättade** (se "Läge 2026-10-28, efter rättelserna
   efter granskning 16"). **G1 och H6 räknas som stängda** (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Hugos
   beslut 2026-10-29 (efter spärrtestet)"). **Kvar:** G5 (bara en anmärkning om gamla tester), och två saker från
   rättelserna: (b) vakten ser bara namnen i kommandot, inte innehållet i en mapp som kopieras eller ett arkiv som
   packas upp, men det hamnar bara i den tillfälliga mappen, där `ugrep` inte letar, och (c) granskningens förslag
   att visa `typeset -f grep` i steg 4 h ingick inte i beslutet och är inte gjort.
10. **De låga fynden i granskning 17 som inte är rättade** (Hugos beslut 2026-10-28, efter granskning 17).
    **H4:** G4-testet (`test_g4_det_riktiga_skriptet_skriver_ok_i_ett_rent_fall`) läser riktiga systemfiler och
    blir rött av datorns läge, inte av koden. Förslag: ett felmeddelande som säger det, och en egen markering
    skild från testerna av koden. **H5:** kontrollskriptet prövar ursprung och ägare för `add-zsh-hook`, men inte
    innehållet och inte mappen filen ligger i. Förslag (frivilligt): jämför innehållet med filen. **Också:**
    `git stash` har två poster med meddelandet "H6 halvfärdig, delvis gjord i auto 2026-10-28" från
    byggsessionerna. De kan tas bort när Hugo säger till (`git stash` står inte på listan).
11. **De låga fynden i granskning 18** (Hugos beslut 2026-10-28 efter granskning 18: under Öppet, så att vakten
    kan installeras snart). En rad var:
    - **I2:** kontrollskriptet godtar en uppgift som heter `com.apple.provenance` plus en tabb, som om den hette exakt `com.apple.provenance`.
    - **I3:** H6 byggdes på den undanlagda versionen, inte om från början, och den andra stash-posten (kl. 20.18) saknar ett nedskrivet OK (historiken står i `GRANSKNING.md`).
    - **I4:** vakten ser inte hårda länkar: Write till en fil i projektet som är ett andra namn på `~/.zshrc` släpps igenom (till sandlådan).
    - **I5:** Agent-verktyget med `isolation: "worktree"` får Claude Code att skriva i `.git` utan att vakten tittar (inte prövad i spärrtestet 2026-10-29, Hugos besked i chatten: står kvar under Öppet).
    - **I6:** INSTALLERA.md steg 2 säger "den fjärde raden" om `No such file or directory`, men `ls` skriver den raden först.
    - **I7:** INSTALLERA.md steg 13: `ditto` och `cp` tar med alla uppgifter, inte bara `com.apple.provenance`, så installationen kan stoppa i onödan.
    - **I8:** regeln om prov och test: SPEC 7.1 har ett undantag som CLAUDE.md saknar, och "läsa riktiga systemfiler" är otydligt.
12. **J2, gits egna sökvägar** (Hugos beslut 2026-10-28 efter granskning 19: under Öppet). SPEC 7.1 säger att I1
    gäller sökvägar i kommandon, men sökvägar som git själv tar emot (efter `--` eller sist, till exempel
    `git log -- /.vol/…`) prövas inte av vakten. git vägrar troligen sökvägar utanför projektet, men det är inte
    prövat. Förslag: SPEC säger exakt vilka kommandon I1 gäller, eller vakten prövar också gits sökvägar.
13. **Steg 9 använder /usr/bin/python3 med sudo. Kan bytas till den fasta sökvägen senare** (Hugos beslut
    2026-10-28 efter granskning 19, bekräftat och inskrivet i Hugos beslut 2026-10-28 efter granskning 20, K4).
    INSTALLERA.md steg 9 skapar projektets Python med `sudo /usr/bin/python3 -m venv`, och lämnas som det är.
14. **De låga fynden i granskning 20** (Hugos beslut 2026-10-28 efter granskning 20: under Öppet). En rad var:
    - **K1:** steg 2 b visar inte mapparna där vaktens Python läser in kod när den startar, bland annat
      `/Library/Python/3.9/site-packages`, där en `.pth`-fil kör kod också med `-I`. **Rättas med `-I -S` nästa
      gång vakten ändras.** `/Library/Python` kontrolleras för hand på Caspers dator före hans installation.
    - **K2:** kan vakten inte skriva sitt fel (felkanalen stängd eller inte skrivbar) avslutar Python med kod 120,
      inte 2. Stoppas ändå av `onFailure: block`.
    - **K3:** en tom `cwd` (`""`) släpps igenom, eftersom vakten räknar den som sin egen arbetsmapp. **Rättas i
      nästa version av vakten.**
    - **K5:** steg 2 b säger inte var andra omgången börjar, och första raden visar en relativ sökväg som kan
      förväxlas med regeln för andra omgången.
15. Caspers dator: installation i helgen (vecka 44). Han har inte projektet. De fem filerna (kommandosparr.py,
    managed-settings.json, kontrollera-skalet.zsh, requirements.txt, INSTALLERA.md) skickas med AirDrop, och han
    kontrollerar kontrollsummorna i INSTALLERA.md innan han skriver sitt lösenord. Projektet får han från GitHub
    efter pushen (Q7 stängd 2026-10-29). Han kör inga sessioner i projektet före installationen. Lärdom 2026-10-29: om ~/.local/bin läggs i
    PATH ska den stå sist, annars stoppar vakten git. Efter en ändring i ~/.zshrc måste Claude-appen avslutas helt
    med Cmd+Q, annars behåller den den gamla PATH.
16. ~~**Kontrollen efter installationen, steg 8 (provet med en vakt som fallerar), är inte gjord** på Hugos dator
    (Hugos besked i chatten 2026-10-29, `GRANSKNING.md`, "Spärrtest 2026-10-29"). Krävs före läget auto, före
    första hela körningen på riktiga underlag och före första kund.~~ **Stängd** 2026-10-29: provet är gjort och
    grönt, med samma kontrollsummor (se "Läge 2026-10-29, efter steg 8 i kontrollen" och `GRANSKNING.md`, "Steg 8,
    provet med en vakt som fallerar, 2026-10-29").
17. **Q9: matchningen mot motparter har en egen kopia av `star_som_hela_ord`** (`_star_som_hela_ord` i
    `scripts/matcha_bank.py`). Hugos beslut 2026-10-29 (`GRANSKNING.md`, "Hugos beslut 2026-10-29 om Q2–Q4"):
    den ska samlas på ett ställe, som i Q3, senare. Ägarkontrollerna rörs inte. Döpt om efter granskning 21 (L2),
    eftersom det första namnet redan betydde något annat i granskning 11 (`GRANSKNING.md`, beslutet 2026-10-29). **Öppen, inte byggd.**
18. **Matchningen mot motparter behandlar inte "Ölund" och "O¨LUND" som lika** (granskning 21, punkt 7), fast
    Hugos beslut om fristående accenttecken (N4) säger att de ska jämföras lika. "O¨LUND" är ett O följt av ett
    separat accenttecken. Så var det också före Q2. Tas med när Q9 byggs. **Öppen, inte byggd.**
19. **`Regelbok.ar_agare_eller_narstaende` anropas inte av någon kärnkod än** (granskning 21, punkt 6), bara av
    testerna. Den är till för nivåsteget (uppgift 6). Q2b gäller alltså i drift i dag bara kontrollen att en
    regel för en ägare har nivå D. **Ändrat i uppgift 4:** `kontera_period` använder den nu (K7 för underlag,
    se punkt 22).
20. **D13:s "allt annat från banken" täcks i dag av K3** (Hugos beslut i chatten 2026-10-29). En bankrad som passar
    en regel för bankrader utan underlag och är över gränsen (250 kr för testbutiken, i `matchning.json` och i
    regelbokens `R-BANK-AVGIFT`) blir ett ärende med nivå D. Andra bankrader från banken utan underlag
    (terminalhyra, bankfack med mera) blir som förut matchningens K3-ärende "saknat underlag", utan nivå. **De ska
    få nivå D i uppgift 6.** Kärnan kan inte se att en sådan rad kommer från banken utan en ny nyckel.
21. ~~**`bokforing` i regelboken är inte beskriven i `foretag/README.md`** (uppgift 4).~~ **Stängd** (Hugos beslut
    2026-10-29, `GRANSKNING.md`, "Beslut efter uppgift 4 (2026-10-29)"): Hugos OK gäller nu också `foretag/`, och
    README beskriver `bokforing` och `flode`.
22. ~~**Val i uppgift 4 som väntar på bekräftelse** (a–d).~~ **Stängd** (Hugos beslut 2026-10-29, samma ställe): (a)
    ja, ett underlag från en ägare blir alltid ett K7-ärende utan förslag. (b) ja, "ny motpart" får ingen nivå nu.
    (c) **ändrad**: flöde e väljs bara när regeln har nyckeln `flode` med ett värde ur kärnans fasta lista, aldrig för
    att regeln bara har kontot `kostnad`. En regel för pengar ut utan nyckeln blir ett ärende. Regeln `bankavgift` i
    testbutikens `matchning.json` byter namn, och ett reserverat ord stoppar en regel som heter så (Hugos beslut i
    chatten samma dag). (d) ja, "över gräns" ger nivå D för alla regler för pengar ut.
23. **K17 är inte byggd** (Ö10). Ett underlag med text som försöker styra agenten får i dag ett förslag som andra
    underlag. Texten används bara som data, och förslaget kräver alltid godkännande. Byggs i rapportsteget.
24. ~~**SPEC 7 nämner inte `kontera_period`.**~~ **Stängd** (Hugos beslut 2026-10-29, beslut e): SPEC 7 får nämna
    `kontera_period`.
25. ~~**Exemplet i DESIGN 4b (SYNT-U-2025-015, BUTIK-FORBRUKNING) blir en ny motpart.**~~ **Stängd** (Hugos beslut
    2026-10-29, beslut f): testbutikens regelbok får regler för BUTIK-FORBRUKNING, HYRESVARD, LEV-TELE, LEV-TILLBEHOR
    och LEV-EL, och regeln som bara fanns i testet tas bort. Byggt för BUTIK-FORBRUKNING och LEV-TILLBEHOR (5753890).
    Resten står i punkt 26.
26. **Konton för hyra, el och telefon i testbutikens kontoplan** (Hugos besked i chatten 2026-10-29, `GRANSKNING.md`,
    "Beslut efter uppgift 4"): kontona 5010 Lokalhyra, 5020 El för belysning och 6210 Telekommunikation ska läggas
    till i testbutikens kontoplan i ett eget steg, med en ny titt på B3:s D2 ("de BAS-konton som redan finns i
    kontoplanen"). Därefter får HYRESVARD, LEV-EL och LEV-TELE regler, och HYRESVARD ska ha nivå D (D10 och D11 är
    öppna). Till dess blir deras underlag "ny motpart". **Öppen, inte byggd.**
27. ~~**Reserverade ord gäller bara regelnamn och regel-id** (Hugos beslut i chatten 2026-10-29). Spärren i
    `test_karnan_ar_generell.py` söker också efter motparter, kassaregister, ägare, betalsätt och konton ur
    regelboken. En motpart som heter exakt `bankavgift` skulle alltså fortfarande krocka med kärnans ord, och då
    blir testet rött (inte tyst). Om reserverade ord ska stoppa fler namn bestämmer Hugo eller Casper.~~ **Stängd**
    (Hugos beslut 2026-10-30 om granskning 22, punkt 4): reserverade ord stoppar alla namn i konfigurationen, men bara
    vid exakt träff (inte delsträng). Byggt 2026-10-30 i `scripts/reserverade_namn.py` och inläsningsmodulerna, se
    "Läge 2026-10-30".
28. ~~**Värdet D i ärendet "regeln saknar flöde"** valdes i byggsessionen 2026-10-29 (som "allt annat från banken" i
    D13, den säkra riktningen), liksom att `flode` bara får stå i en regel för bankrader och att `bankavgift` kräver
    exakt kontot `kostnad`. BESLUTSFATTARE SAKNAS för bekräftelse.~~ **Stängd** (Hugos beslut 2026-10-30 om
    granskning 22, punkt 5): de tre valen är bekräftade, och `flode` stoppas dessutom på en regel för pengar in
    (granskning 22, P7). Byggt 2026-10-30 i `las_regelbok.py`.
29. ~~**Val i rättelsen av P2, för Hugo att bekräfta** (byggsessionen 2026-10-30): när K4a, K4b eller K4c flaggar ett
    par underlag får bara det flaggade underlaget (det med högre id, som bär ärendet) inget förslag. Underlaget det
    jämförs med får sitt förslag, som när K4 behåller originalet. Alternativet är att båda stoppas tills en människa
    har svarat. Säkra riktningen är det senare, men det skulle också stoppa riktiga fakturor som bara råkar likna en
    annan. BESLUTSFATTARE SAKNAS för bekräftelse.~~ **Stängd** (Hugos beslut 2026-10-30 om granskning 23, beslut 3,
    efter granskarens bedömning i punkt 7): vid K4a och K4b stoppas båda underlagen i paret, och originalet får ett
    eget ärende. Vid K4c stoppas bara det flaggade, och originalets förslag märks i motiveringen med K4c-ärendet
    (det flaggade underlagets id). Byggt 2026-10-30 i 35afa8b, se "Läge 2026-10-30, rättelserna efter granskning 23".
30. ~~**Märkningen vid K4c är text i motiveringen, inte ett eget fält i förslaget** (valt i byggsessionen 2026-10-30
    för Öppet 29, eftersom förslaget inte har något annat fält för text till godkännaren och ett ärende inget eget
    id). Nivåsteget (uppgift 6) kan läsa den. Om Hugo eller Casper vill ha ett eget fält byggs det då.
    BESLUTSFATTARE SAKNAS för bekräftelse.~~ **Stängd: avgjort, eget fält byggs i uppgift 6** (Hugos beslut
    2026-10-30 om granskning 24, beslut 2, efter granskarens bedömning i P6). Märkningen som text i motiveringen
    räcker till uppgift 6.
31. ~~**Ett underlag under en bankregel godtas när dess egen regel godtar satsen** (granskning 23, P1, det som inte
    byggdes): K5 prövar satsen mot underlagets egen regel, men inte att underlagets kostnad står på den regelns konto,
    och ursprungskontrollen punkt 8 godtar kontot eftersom det står i förslagets regel. Bara kod som bygger förslag
    förbi flödena kan göra så. Granskarens alternativ i granskning 23 var att stoppa ett förslag med underlag vars
    regel inte gäller underlag. BESLUTSFATTARE SAKNAS.~~ **Stängd** (Hugos beslut 2026-10-30 om granskning 24, beslut
    1, efter granskarens bedömning i P5): `skapa_konteringsforslag` stoppar ett förslag när förslagets regel inte är
    underlagets egen regel, uppslagen på underlagets datum. Byggt 2026-10-30 i bbb183a, se "Läge 2026-10-30, Öppet 31
    rättad och steg 22 klart". Granskad i granskning 25 (grönt), och **räknas som granskad och klar** (Hugos beslut
    2026-10-30 om granskning 25, beslut 2).
32. ~~**Kostnaden kan stå på fel konto inom regeln, eller på ett rollkonto, för ett förslag byggt förbi flödena**
    (granskning 25, P7). `kontrollera_underlag` räknar fram kontot per momssats (`konton`), men
    `_kontrollera_underlagen` prövar inte att raden med `underlag_ore` står på det kontot, och ursprungskontrollen
    punkt 8 godtar varje konto som står i regeln eller har en roll. Granskarens prov: `R-LEV-KAFFE` med två konton
    och kontona bytta godtas, och 003 med kostnaden på 2440 godtas, med alla kontroller "ok". Flödena bygger ur
    `konton` och bokför rätt. Granskarens förslag: kräv i `_kontrollera_underlagen` att varje `underlag_ore`-rad står
    på `konton[sats]` och varje `moms_ore`-rad på kontot för ingående moms, före uppgift 5. BESLUTSFATTARE SAKNAS.~~
    **Stängd** (Hugos beslut 2026-10-30 om granskning 25, beslut 1): kostnadsraden i ett förslag med underlag ska stå
    på det konto som K5 räknar fram för underlagets momssats, och annat konto stoppar förslaget. Byggt 2026-10-30, se
    "Läge 2026-10-30, Öppet 32 rättad", committad 2026-10-30 som steg 91 i BYGGPLAN.md (Hugos beslut 2026-10-30 om
    byggsessionen för Öppet 32, b). **Granskad i granskning 26** (gult: byggd som beslutet säger, granskarens två prov
    stoppas med båda momsfilerna; ett hål kvar i samma familj, Öppet 34). Momsraden (`moms_ore`) ingick inte i
    beslutet och är inte byggd: den är Öppet 33 (samma beslut, a).
33. ~~**Momsraden (`moms_ore`) i ett förslag med underlag låses till kontot för ingående moms** (granskarens andra
    förslag i granskning 25, P7). I dag prövar `_kontrollera_underlagen` bara kostnadsraderna (Öppet 32), så en momsrad
    kan stå på ett annat konto som står i regeln eller har en roll i kontoplanen, för ett förslag byggt förbi
    flödena. Flödena bygger momsraden ur kontoplanens roll `ingaende_moms`, så de berörs inte. **Byggs som eget steg
    efter Öppet 32, inte i commiten för Öppet 32** (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a,
    `GRANSKNING.md`). Inget stegnummer i BYGGPLAN.md än. Granskning 26 (H7) bekräftar att
    momsen på kostnadskontot godtas i dag. **Byggs i samma steg som Öppet 34** (Hugos beslut 2026-10-30 om granskning
    26, `GRANSKNING.md`, "Hugos beslut 2026-10-30 om granskning 26").~~ **Stängd:** byggd 2026-10-30 som steg 93 i
    BYGGPLAN.md, i 7801a64 (`_kontrollera_momsraderna` i `_kontrollera_underlagen`, sist efter Öppet 34), se "Läge
    2026-10-30, Öppet 33 och 34 byggda". Granskarens prov H7 stoppas. **Granskad i granskning 27** (byggd som
    beslutet säger; H7 och momsen på leverantörsskulderna stoppas, bruttot som `summa` på kostnadskontot stoppas).
34. ~~**Kostnaden räknad ur `belopp_ore` i stället för `underlag_ore` går förbi Öppet 32, för ett förslag byggt förbi
    flödena** (granskning 26, M1, nivå medel). `_kontrollera_kostnadsraderna` prövar bara rader som har underlagets
    `underlag_ore` som källa. En kostnadsrad räknad som `skillnad` av underlagets `belopp_ore` och `moms_ore` har samma
    belopp men aldrig `underlag_ore` som källa, så dess konto prövas inte, och täckningen går ihop. Granskarens prov:
    003 med kostnaden på 2440 byggd så godtas med alla kontrollerna "ok" (samma verifikation som prov (b) i granskning
    25), 020 med kontona bytta byggd så godtas (prov (a)), och en bruttobokföring (hela `belopp_ore` på 4010 utan
    momsrad, eller på 2440 på båda sidorna) godtas. Flödena bygger alltid med `lika` ur `underlag_ore`, så de berörs
    inte, och luckan fanns före c479915. Granskarens förslag: en rad med ett underlags `belopp_ore` som källa får bara
    räknas med `lika` och bara stå på leverantörsskulderna, och `underlag_ore` och `moms_ore` får inte räknas med
    `skillnad`; alternativt kräv flödenas form rakt av (stänger också Öppet 33). Bör byggas före uppgift 5, gärna i
    samma steg som Öppet 33. Docstringen i `konteringsforslag.py` om momsraden ("inte beslutat") rättas samtidigt
    (granskning 26, L1). **Avgjort** (Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg", `GRANSKNING.md`):
    byggs i samma steg som Öppet 33, före uppgift 5, med granskarens förslag till regel om inget annat sägs i
    uppdraget.~~ **Stängd:** byggd 2026-10-30 som steg 93 i BYGGPLAN.md, i 7801a64 (`_kontrollera_beloppsraderna` i
    `_kontrollera_underlagen`, efter Öppet 32), med granskarens förslag till regel och byggsessionens tillägg att
    underlagets `belopp_ore` står på högst en rad i förslaget (annars går det fjärde provet igenom; bekräftat av
    Hugo 2026-10-31 i uppdraget till granskning 27), se "Läge 2026-10-30, Öppet 33 och 34 byggda". Alla fyra
    LUCKA-proven stoppas. **Granskad i granskning 27** (gult: byggd som beslutet säger, alla fyra LUCKA-proven och
    fem egna prov stoppas; två hål kvar i en ny familj, Öppet 35).
35. ~~**Beloppet i debet på leverantörsskulderna utan bankrad går förbi alla kontroller, för ett förslag byggt förbi
    flödena** (granskning 27, M1, nivå medel). Ingen kontroll prövar sidan (punkt 5 säger uttryckligen att den inte
    prövas, eftersom kreditnotor inte är bestämda, Ö8), och ingen kräver en bankrad när `belopp_ore` står i debet.
    Granskarens prov: (h1) 003 spegelvänd, 2440 debet `belopp_ore`, 4010 kredit `underlag_ore`, 2641 kredit
    `moms_ore`, godtas med alla fem kontrollerna "ok" (en faktura bokförd som en kreditnota utan kreditnota); (h2)
    två fakturor under samma regel med exakt samma belopp, den enas `belopp_ore` i debet och den andras i kredit på
    2440, godtas också (inget bokförs, som i det fjärde provet i granskning 26, men varje underlag står på exakt en
    rad, så regeln om högst en rad ser det inte). Båda fanns före 7801a64, flödena bygger aldrig så, och förslaget
    kräver godkännande. Granskarens förslag: `belopp_ore` i kredit bara utan underlagets delar i kredit, och i debet
    bara med minst en bankrad i förslaget och utan underlagets delar alls; alternativt flödenas två former rakt av.
    Hänger ihop med Ö8. Bör byggas före uppgift 5, som eget steg. **Öppen, inte byggd. Väntar på Hugos eller
    Caspers beslut** (granskning 27, "Beslut som behövs", 1).~~ **Stängd:** Hugos beslut 2026-10-31 ("Beloppet i
    debet ska kräva en bankrad. belopp_ore får bara stå i kredit när delarna inte gör det."), byggt 2026-10-31 som
    steg 94 i BYGGPLAN.md, i 109fdcf (`_kontrollera_beloppssidan`, sist i `_kontrollera_underlagen`), se "Läge
    2026-10-31, Öppet 35 byggd". h1 och h2 stoppas. Granskarens tillägg "i debet ... utan underlagets delar alls" står
    inte i beslutet och är inte byggt. Kreditnotor kan inte läsas in i dag; när Ö8 byggs måste regeln prövas igen.
    **Granskad i granskning 28** (gult: byggd som beslutet säger ordagrant, h1 och h2 stoppas; kravet på bankrad
    gäller per förslag, inte per underlag, Öppet 36).
36. ~~**Kravet på bankrad i Öppet 35 gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en
    bankrad som inte hör till underlaget, för ett förslag byggt förbi flödena** (granskning 28, M1, nivå medel).
    `_kontrollera_beloppssidan` frågar bara om förslaget har någon använd bankrad alls, var som helst och med vilket
    belopp som helst. Granskarens prov: (b1) 003 spegelvänd (beloppet i debet, delarna i kredit) i samma förslag som
    009:s riktiga betalning (beloppet i debet, bankrad 84 på bankkontot i kredit), godtas med alla fem kontrollerna
    "ok"; (b2) 003 och 009 med samma belopp kvittade mot varandra på 2440, plus 009 som delar i debet mot bankrad 26
    (003:s betalning) i kredit, godtas; (b3) 003:s belopp i debet mot bankrad 26 som källa på 4010, utan rad på
    bankkontot, godtas. Alla tre fanns före 109fdcf, flödena bygger aldrig så (varje betalning i flödena har exakt
    en rad på bankkontot i kredit med samma belopp), och förslaget kräver godkännande. Granskarens möjliga sätt, för
    Hugo eller Casper att välja: (a) för varje rad med ett underlags `belopp_ore` i debet ska förslaget ha en rad på
    bankkontot i kredit med samma belopp, räknad ur en bankrad; (b) flödenas två former rakt av; (c) lämna till
    uppgift 5. Hänger ihop med Ö8 som Öppet 35. Bör avgöras före uppgift 5, som eget steg. **Öppen, inte byggd.
    Väntar på Hugos eller Caspers beslut** (granskning 28, "Beslut som behövs", 1).~~ **Stängd:** Hugos beslut
    2026-11-04 om granskning 28, beslut 1 (granskarens (a), med uppdragets tillägg att varje bankkontorad räknas bara
    en gång), byggt 2026-11-04 som steg 95 i BYGGPLAN.md, i 0708667 (`_kontrollera_beloppssidan`, grenen för debet,
    med kontoplanen som nytt argument), se "Läge 2026-11-04, Öppet 36 byggd". b1 och b3 stoppas. **b2 godtas** (Hugos
    beslut 2026-11-04 i chatten): bankrad 26 är 003:s betalning och står mot 003:s belopp, så (a) är uppfylld, och
    konteringen är identisk med flöde a:s två förslag (009:s faktura och 003:s betalning) i samma förslag. Räknas
    inte som ett nytt hål i familjen; frågan om samma förslag är Öppet 38. Kreditnotor: när Ö8 byggs måste regeln
    prövas igen. **Inte granskad oberoende än.**
37. **Ett underlag med `belopp_ore` 0 stannar hela körningen** (granskning 28, M2, nivå medel, utanför steg 94).
    `las_underlag` stoppar negativa tal men inte 0, och K13 går ihop (0 + 0 = 0). Flöde a hoppar över momsrader med 0
    och bygger en faktura med en enda rad (leverantörsskulderna med 0 i kredit), som K2 stoppar, och
    `kontera_period` fångar inte felet, så inget förslag görs för någon i perioden och felet säger inte vilket
    underlag det gäller. Säker riktning, men körningen stannar. Fanns före 109fdcf. Beslut som behövs: stoppa ett
    sådant underlag när det läses (som negativa tal), eller göra ett ärende. Eget steg, inte en del av Öppet 36.
    **Öppen. Väntar på Hugos eller Caspers beslut** (granskning 28, "Beslut som behövs", 2). **Avgjort** (Hugos
    beslut 2026-11-04 om granskning 28, beslut 2, `GRANSKNING.md`): ett underlag med `belopp_ore` 0 ska bli ett
    ärende för just det underlaget, och resten av perioden ska fortsätta. Byggs som eget steg 96 i BYGGPLAN.md, inte
    i sessionen för steg 95. **Öppen, inte byggd.**
38. **En faktura och en annan fakturas betalning i samma förslag** (Hugos beslut 2026-11-04 i chatten, i sessionen
    för steg 95, `GRANSKNING.md`, "Hugos beslut 2026-11-04 om granskning 28"). Granskarens b2 från granskning 28
    (009:s faktura och 003:s betalning i en verifikation) godtas av Öppet 36 enligt (a), eftersom konteringen är
    identisk med flöde a:s två förslag. Hugos beslut 3, ordagrant: "Att en faktura och en annan fakturas betalning
    står i samma förslag ska kontrolleras med en redovisningskonsult (en verifikation per affärshändelse?), och tas
    upp igen när godkännandekortet i appen byggs." Flödena bygger aldrig så; bara kod förbi flödena kan. **Öppen.
    Väntar på en redovisningskonsult, och på steg 33 (godkännandet) i BYGGPLAN.md.**

## Nästa steg i byggordningen

1. **Q3 + Q4 + Q2 (granskning 11).** Vakten för kommandolistan (granskning 11, Q1) är klar på Hugos dator.
   Byggd i f21a3a1, 773e919 och 6686166, fynden i granskning 12 i 5cb9080, 08a3370 och c066188, rättelserna
   efter granskning 16 i 1dbedb1 till 58daf69, efter granskning 17 i 653f0a4 till 235eab6, I1 efter
   granskning 18 i 0c7cdcb och 43e2371 och J1 efter granskning 19 i ab305c7, 4bcbabe och ad85b8e.
   **Klart:** granskning 20 (a9ad2ab, beslut i 2da1172), provkörningen av steg 4 h (40df48e och 567692b),
   installationen på Hugos dator och spärrtestet (818f87d, beslut i 61a6d5d). Caspers dator: se Öppet,
   punkt 15. **Q2, Q2b, Q3 och Q4 är byggda** (Q2: 3e3c18c och d7d38e0, Q2b: 1dcf769, Q3: bd851ba, Q4:
   2bc9762, `GRANSKNING.md`, "Hugos beslut 2026-10-29 om Q2–Q4"). Q3 och Q4 ändrar inte hur något fungerar. Q2
   gör att ägaren känns igen när banken skriver namnet utan accenter, och Q2b gör samma sak i underlagen och i
   kontrollen att en regel för ägaren har nivå D. **Granskade** i granskning 21 (3bbcbe4, grön), och
   dokumentationen rättad efter den.
2. **Push till GitHub.** Klar 2026-10-29: `main` är i fas med GitHub vid 6aba32d. Q7 är stängd (Hugos beslut
   2026-10-29): pusha som det är.
3. **Uppgift 4 är byggd** (4269f76, f6ed99e och e4cc538, 2026-10-29): flöde a, b och e med K5 och K8, och
   testerna i DESIGN 7 rad 4 är gröna. Hugos beslut efter uppgift 4 (a–f) är byggda (48e7ed3, ded669d och
   5753890). Granskad i granskning 22 (gult): **P1 och P2 rättade 2026-10-30** efter Hugos beslut om granskning 22,
   och Öppet 27 och 28 stängda. **Granskade i granskning 23** (gult): P1 hade en lucka och P3 två namn, **rättade
   2026-10-30** i 13126d2 och 35afa8b efter Hugos beslut om granskning 23, och Öppet 29 stängd. **Granskade i
   granskning 24** (6dfcdcd, grönt). **Steg 22 är klart 2026-10-30** (Hugos beslut 2026-10-30 om granskning 24,
   beslut 3). Öppet 31 från granskning 24 rättad i bbb183a, granskad i granskning 25 (grönt) och klar (Hugos beslut
   2026-10-30 om granskning 25, beslut 2). **Öppet 32 (granskning 25, P7) rättad 2026-10-30** efter Hugos beslut om
   granskning 25 (beslut 1) och committad som steg 91 i BYGGPLAN.md, **granskad i granskning 26** (gult: byggd som
   beslutet säger, ett hål kvar i samma familj som Öppet 34). **Öppet 33 och Öppet 34 byggda 2026-10-30 i samma
   steg, steg 93** (Hugos beslut 2026-10-30 om granskning 26; 7801a64), **granskade i granskning 27** (gult: byggda
   som beslutet säger, två hål kvar i en ny familj, Öppet 35; regeln om högst en rad beslutad av Hugo 2026-10-31).
   **Öppet 35 byggd 2026-10-31 som steg 94** (Hugos beslut 2026-10-31 om granskning 27; 109fdcf), **granskad i
   granskning 28** (gult: byggd som beslutet säger ordagrant, h1 och h2 stoppas; kravet på bankrad gäller per
   förslag, inte per underlag, Öppet 36; ett underlag med belopp 0 stannar hela körningen, Öppet 37, utanför
   steget). **Steg 94 granskat och klart** (Hugos beslut 2026-11-04 om granskning 28, beslut 3). **Öppet 36 byggd
   2026-11-04 som steg 95** (beslut 1, granskarens (a); 0708667): b1 och b3 stoppas, b2 godtas (Hugos beslut
   2026-11-04 i chatten, Öppet 38 för redovisningskonsulten). Inte granskad oberoende än. Kvar: Öppet 37 som steg 96
   (beslut 2, inte byggd), Öppet 38 (redovisningskonsult), och steg 92, Öppet 26 (konton för hyra, el och telefon)
   (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b). Pushad till 7d8cae9. DESIGN 7 säger oberoende granskning efter uppgift 3 och 6, inte efter 4. Det som var förutsättningarna:
   flöde a, b och e (leverantörsfakturor, kvitton och bankavgifter)
   med K5 och K8 (BYGGPLAN steg 22). Förutsättningar, Hugos beslut 2026-10-29 (`GRANSKNING.md`, "Beslut
   2026-10-29 – inför uppgift 4"):
   - **B1:** uppgift 4 byggs nu, på syntetisk data, med vakten installerad och Claude Code i det läge som frågar
     (inte Auto) tills provet med en fallerande vakt (Öppet 16) är gjort. Det går före Hugos beslut 2026-10-28
     kväll om auto (överst i filen) för den här uppgiften. Sandlådan (Öppet 4) ska vara klar före uppgift 5,
     eller före första körningen på riktiga underlag om den kommer först.
   - **B2:** ärenden från K5 och K8 skapas med märkningen "kräver mänsklig bedömning" (samma som P4) och nivå D
     direkt. Nivåsteget i uppgift 6 får aldrig sänka en sådan nivå, bara höja.
   - **B3:** påhittade val för Syntet Testbutik AB, märkta "antaget" i testföretagets konfiguration (nya nycklar
     där är OK): D1 faktureringsmetoden, D2 de BAS-konton som redan finns i kontoplanen, D4 momsen i öre exakt
     som på underlaget utan avrundning per verifikation, och D14 leverantörsfaktura på fakturadatum och
     betalningen på bankens datum, kvitto på kvittodatum, bankavgift på bankens datum (Hugos besked i chatten
     2026-10-29). Valen gäller bara testföretaget. Strider ett val mot DESIGN stannar byggsessionen och frågar.
   - ~~**Öppet före start:** D13 (moms på bankavgifter, och om bankraden räcker som underlag) är inte beslutad.
     Om "bankens datum" är transaktionsdagen eller bankens bokföringsdag är inte sagt.~~ Beslutat i chatten
     2026-10-29 (baec52b): D13 antagen för testföretaget, och "bankens datum" är transaktionsdagen.
4. Uppgift 5: Z-rapporter, kortinlösen, Swish och kontantinsättningar (och M9 från granskning 7). Kräver
   sandlådan (BYGGPLAN steg 15).
5. Uppgift 6: nivåerna A–D och K9, med nivå D för ägarens bankrader. Därefter en oberoende granskning.

Uppgift 4 och 5 kräver bokföringsbeslut (DESIGN D1–D16) som väntar på en redovisningskonsult. Till dess
byggs de bara med syntetiska val som tydligt står i konfigurationen.

## Beslut

Här står besluten som rör läget ovan. Alla andra beslut står i SPEC.md avsnitt 11 och DESIGN-regelbok.md
avsnitt 8, med namn och datum.

- **Hugos beslut 2026-10-27 (granskning 8, N3):** `matcha_period` får regelboken, och en bankrad mot en
  ägare eller närstående kräver alltid underlag (K3), även när en regel i `matchning.json` annars skulle
  undanta den. Byggt i ea51c97.
- **Hugos beslut 2026-10-27 (granskning 8, N4):** ett fristående accenttecken efter en bokstav jämförs som
  bokstaven med accent ("A¨" som "Ä"). Byggt i ca2df6a och låst med ett test.
- **Hugos beslut 2026-10-27:** en saknad, tom eller oläsbar lista över ägare och närstående stoppar
  agenten. Byggt i dd0e1cf.
- **Hugos beslut 2026-10-27:** en bankrad mot en ägare eller närstående märks "kräver mänsklig bedömning"
  redan i matchningen, och får dessutom nivå D i uppgift 6. Märkningen är byggd i dd0e1cf. Nivå D är inte
  byggd.
- **Hugos beslut 2026-10-28 (granskning 10, P1):** en motpart i listan över ägare och närstående som
  inte har någon bokstav eller siffra räknas som tom och stoppar hela körningen. Det gäller alla företag.
  Byggt i 16000a8.
- **Hugos beslut 2026-10-28 (granskning 10, P2 och P5–P6):** felet för P1 ska säga fil, värde, var det
  står och hur det rättas, i en mening. De tre andra stoppen där felet inte säger "Hela körningen stoppas"
  rättas bara i texten i SPEC avsnitt 11, inte i koden. Dokumentationen (`DESIGN-regelbok.md`,
  `foretag/README.md` och PROGRESS.md) rättas i en egen commit.
- **Hugos beslut 2026-10-28 (granskning 11, Q1):** kommandolistan i SPEC 7.1 spärras tekniskt nu, före
  uppgift 4, i en fil utanför projektet. Vakten gäller strikt överallt, och ingen mapp undantas. `sudo` och
  `su` stoppas alltid. Claude Code uppdateras först till en version som kan stoppa kommandot när vakten
  fallerar (minst 2.1.295). Hugo godtar att superpowers vakter slutar fungera. Sandlådan byggs i
  spärrsteget, men är klar före uppgift 5, eller före första hela körningen på riktiga underlag om den kommer
  först. Hela planen och besluten: `GRANSKNING.md`, "Granskning 11 – plan för Q1".
- **Hugos beslut 2026-10-28 (granskning 11, Q1, tredje omgången):** SPEC 7.1 skrivs om med vakten ("godkänns
  av Hugo", sandlådan före uppgift 5 eller före första hela körningen på riktiga underlag om den kommer först).
  Ja till `mkdir -p`, citatregeln, stopp för `grep`-mönster som börjar med `/` och commit-meddelanden via
  fil. Ja till `requiredMinimumVersion` 2.1.295 och till kontrollsummor (`shasum -a 256`) i INSTALLERA.md,
  som Hugo jämför med granskningens innan han kopierar. Förbud mot att skriva i skalets och gits startfiler,
  `~/.claude/**` och `~/Library/LaunchAgents/**`. Skills och worktree-sessioner blir frågor till
  granskningen. Byggt, inte installerat. Detaljer: `GRANSKNING.md`, "Bygget av vakten för Q1".
- **Hugos beslut 2026-10-28 (granskning 12):** `disableSkillShellExecution: true` (P3). Vakten släpper bara
  igenom verktygen på listan i SPEC 7.1 (P4), och Hugo valde listan i chatten samma dag. Förbud mot att
  skriva i filen `.git` på varje djup (P5). `permissions.disableAutoMode: "disable"` (P6). Förbud mot att
  skriva i `~/.ssh/**`, `.mcp.json`, projektets `.claude/**`, `~/.claude.json`, mappar i `PATH` som Hugo
  äger och `.venv/**`, men inget förbud för CLAUDE.md. Varje ändring i CLAUDE.md nämns i slutrapporten.
  Provet med en vakt som fallerar i kontrollen efter installationen, gjort av Hugo i Terminal. Lägsta
  version för P3 och P6 är inte bekräftad, och Hugo beslöt i chatten att de byggs in ändå. Byggt i
  5cb9080, 08a3370 och c066188.
- **Hugos beslut 2026-10-28 (8), texten godkänd av Hugo i chatten samma dag:** installationen av vakten
  kräver en oberoende granskning, men inte provet med en vakt som fallerar. Provet krävs före läget
  "auto", före körningar utan att Hugo tittar, före första hela körningen på riktiga underlag och före
  första kund. Står i SPEC 7.1 och INSTALLERA.md, med test.
- **Hugos beslut 2026-10-28 (PATH-regel, förprov för onFailure, P7):** vakten släpper bara igenom ett
  kommando vars program, och varje mapp ovanför det, ägs av root och inte går att skriva i för gruppen
  eller andra, och kommandon som ändrar `PATH` stoppas. Listan ändras inte. Ett förprov i INSTALLERA.md
  visar att Claude Code stoppar ett kommando när en vakt inte går att starta, före installationen.
  Versionen kontrolleras med `/status`, `ClaudeCode` får `root:wheel` och 755 och filerna 644, mapparna
  kontrolleras med `ls -ld` före och efter, och `/status` ska visa `Enterprise managed settings (file)`
  efteråt. Byggt, inte installerat. Detaljer: `GRANSKNING.md`.
- **Hugos beslut 2026-10-28 om vakten, beslut 1–4:** (1) `.venv` flyttas till en mapp som root äger, och
  pytest-kommandona pekar dit, (2) varje mapp i `PATH` före programmet ska ägas av root, (3) också filen själv
  och länkens mål ska ägas av root, (4) varje annan källa i `/status` stoppar installationen. Byggt, inte
  installerat. Detaljer: `GRANSKNING.md`, "Granskning 11 – plan för Q1".
- **Hugos svar 2026-10-28, punkt 1–3:** (1) Cryptexes-mappen flyttas sist i `PATH` med en rad i `~/.zshrc`
  som Hugo lägger in själv, inget undantag i vakten, (2) testsviten körs med den gamla `.venv` tills den nya
  platsen finns, och den gamla tas bort efter installationen, (3) bara en annan låst källa på raden Setting
  sources underkänner installationen (ersätter beslut 4 ovan), raden läses i Terminal, och ett sista steg i
  skrivbordsappen visar att vakten stoppar `date`. Byggt, inte installerat.
- **Hugos beslut 2026-10-28 om granskning 13:** P1 a och b (kontroll av alias och funktioner, förbud för
  zsh:s filer och filerna de läser in), P2 a (vakten prövar varje länk i kedjan), P3 b (`PATH` ändras inte,
  hela sökvägen `~/.local/bin/claude`, varning för installerarens förslag), P4 a (förbud för Claude Code för
  Terminal, appens Claude Code och appen), P5 a (omvägarna i en egen session före uppgift 5) och fråga 2
  (Claude Code för Terminal behålls, utanför `PATH`). Byggt, inte installerat. Detaljer: `GRANSKNING.md`.
- **Hugos svar 2026-10-28 efter granskning 13, punkt 1–4:** förbuden räcker för appen och ägandet ändras
  inte, och sandlådan ska förbjuda skrivning i appen, appens Claude Code och `~/.local/share/claude` (1),
  `cd` till projektmappen står kvar först (2, mappen rättad till `~/VERA/agent` efter granskning 15), hela `~/Library/Application Support/Claude` förbjuds för agentens
  fil-verktyg (3), och ändringen i SPEC 7.1 godkänns (4). Byggt, inte installerat.
- **Hugos beslut 2026-10-29 (granskning 11, Q7):** de opushade commitarna pushas som de är, med `d8efa3a` kvar
  i historiken. Historiken skrivs inte om. Villkoret är att repot på GitHub är privat (kontrollerat av Hugo
  2026-10-29). **Repot får inte göras publikt utan en ny genomgång av hela historiken först.** Skälen:
  `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd".
- **Hugos beslut 2026-10-30 om granskning 23** (ordagrant i `GRANSKNING.md`, "Hugos beslut 2026-10-30 om
  granskning 23"): (1) K5, K7 och K8 mot varje underlags egen regel, och ett underlag utan egen regel stoppar
  förslaget (P1), (2) betalsätten i kassareglerna och företagets namn prövas mot de reserverade orden, bara exakt
  träff (P3), (3) K4a och K4b stoppar båda underlagen i paret, K4c bara det flaggade med märkning av originalets
  förslag (Öppet 29, stängd), (4) körningar mot en kopia och av enskilda testfiler skrivs i PROGRESS.md med exakt
  kommando (P7, regel i CLAUDE.md), (5) steg 22 räknas som klart först efter en kort oberoende granskning av
  rättelsen (P9). Byggt i 13126d2 och 35afa8b, inte granskat.
- **Hugos beslut i chatten 2026-10-27:** listan över ägare och närstående ligger kvar i
  `foretag/<namn>/regelbok.json` tills spärrsteget, eftersom SPEC inte säger var den skyddade mappen ska
  ligga. Testet att listan ligger utanför alla mappar agenten får skriva i skrivs då.
- **Hugos beslut 2026-10-21 (enligt den förra versionen av den här filen):** testantagandena i grupp b
  (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9 och Ö-T24) godkändes som de stod, för testföretaget. De gäller inte för
  riktiga företag. Frågorna står nu i `testforetag/FIKTIVT_FORETAG.md` avsnitt 9, där de inte är markerade
  som besvarade.
