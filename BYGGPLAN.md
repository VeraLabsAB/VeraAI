# BYGGPLAN – Kassio, från referensprodukt till en hel byrå

Skapad 2026-10-29. Utgår från `PROGRESS.md` (2026-10-28, 4 076 gröna tester), `SPEC.md`, `DESIGN-regelbok.md`
avsnitt 7 och två researchrapporter från 2026-10-29: "Så kan Vera bli en bättre agent" och "Byråtjänster Vera saknar".

**Rättad 2026-10-29 efter PROGRESS.md:** status för steg 12–21 och beroendet för steg 22 (Hugos beslut 2026-10-29,
B1, `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4").

**Omskriven 2026-11-04 efter Hugos beslut om planen** (`GRANSKNING.md`, "Hugos beslut 2026-11-04 om planen
(PLAN-KASSIO-FORSLAG.md)"). Kravkällan är `KASSIO-KRAV.md` (beslut 1), och underlaget är `PLAN-KASSIO-FORSLAG.md`.
Namnbytet från Vera till Kassio är gjort i steg 104 (beslut 12, och Hugos beslut 2026-11-04 om steg 104).

**Målet på lång sikt:** Kassio ska kunna göra i princip allt som Jolene, Fortnox, Bokio, Spiris, Wint och Lennart redan gör åt
ett litet aktiebolag, plus några saker som ingen av dem gör. Det enda Kassio aldrig gör är att betala, skriva under
eller lämna in något utan att en människa hos kunden har godkänt och signerat.

**De två målen närmast (beslut 2). Datumen är uppskattningar, inte löften:**

1. **Skuggpiloten** (förslag: 2027-01-11). En skuggpilot betyder att Kassio arbetar vid sidan av: Kassio tar fram
   veckoutkast på pilotkundens riktiga data, men inget skrivs i Fortnox. Pilotkundens ekonomiansvarige bokför som vanligt och jämför.
2. **Piloten med Fortnox** (förslag: 2027-03-01). Bokföring, moms och veckoutkast skrivs i Fortnox efter godkännande.

Lön, fakturor, bokslut och resten byggs under piloten, i den ordning piloten visar.

**Så är planen ordnad:**

| Del | Vad | Rubrikerna |
|---|---|---|
| Klart | Allt som är klart, med historiken kvar | Fas A, B och C |
| Mål 1: Skuggpiloten | Det som krävs för veckoutkast på riktig data | Fas Skugg 0–12 |
| Mål 2: Piloten med Fortnox | Det som krävs för att skriva i Fortnox efter godkännande | Fas Pilot 2–12 |
| Under piloten | Lön, fakturor, bokslut och resten | Fas Under 9–12 |
| Efter piloten | Det som väntar, med skälet på varje rad | Fas Efter 1–5, och Fas Väntar |

Numret i rubriken är gruppens nummer i `PLAN-KASSIO-FORSLAG.md` avsnitt C, så samma nummer kan stå under flera mål.
Inga stegnummer är ändrade, och inget steg är borttaget. Stegen från de gamla faserna D–H står nu under de nya rubrikerna.
Alla rubriker med steg börjar med "Fas", eftersom testet `scripts/tests/test_byggplan_progress.py` läser tabellerna under sådana rubriker.

**Så används planen:**

- Ett steg är en Claude Code-session. Stora steg delas upp i flera sessioner, och då står det i steget.
- Varje steg avslutas med full testsvit och slutrapportrutan (STATUS, KAN JAG GÅ VIDARE, beslut, nästa steg).
- Kolumnen "Granskas" säger om steget granskas oberoende för sig eller med sin grupp (regel 10). En granskning görs i en ny session.
- Ett steg får inte börja förrän stegen det beror på är klara. Säkerhetsstegen i Fas Skugg 1 går före kärnan. Steg 15 ska vara klar före steg 23.
- Där det står **Beslut** måste Hugo eller Casper (eller en redovisningskonsult) svara innan steget byggs.
- Statusen uppdateras här och i `PROGRESS.md` när ett steg blir klart.

Status: ✅ klart · 🔶 pågår · ⬜ inte påbörjat

## Läge nu

- **Uppdaterad:** 2026-11-05
- **Pågående steg:** 15 – Sandlådan (byggd igen i 795f848 efter granskning 34 och Hugos beslut 2026-11-05, P6 gjord och Hugos beslut efter P6 införda, granskad i granskning 35, gult, spärrprovet grönt i Hugos provkörning 2026-11-05 i Terminal och appen, del E grön, Hugos beslut om granskning 35 byggda i ed6b847 och 2572b0f, granskade i granskning 36, gult, inget blockerar, Hugos beslut om granskning 36 byggda 2026-11-05 i abded14 och 420a57d, granskade i granskning 37, rött tills ett test är rättat, 9 röda tester, ett fynd blockerar och fyra bör rättas, Hugos beslut om granskning 37 byggda 2026-11-05 i 8bd6fe5 och 6065501, 0 röda tester, granskade i granskning 38, gult, inget blockerar, ett fynd bör rättas, Hugos beslut om granskning 38 byggda 2026-11-05 i f52e6ef och c0b54e6, 0 röda tester, granskade i granskning 39, gult, inget blockerar, tre fynd bör rättas, inte installerad). Nästa att börja: 53 – Juristen, 54 – Redovisningskonsulten, 105 – Frågorna till pilotkunden och 106 – Fortnox-avtalet
- **Senast avslutade steg:** 104 – Namnbytet till Kassio (klart 2026-11-04 i c764101: Vera blir Kassio i text i kod, tester och dokument, bara text. Sökningen i `scripts/`, `testforetag/`, `testdata/README.md`, `DESIGN-regelbok.md`, `OVERLAMNING.md` och `foretag/` ger bara vaktens sökväg, mappnamnet `~/VERA` och vakttesterna. Den här filens gällande text bytte namn efter Hugos beslut 2026-11-04 om steg 104, och `PLAN-KASSIO-FORSLAG.md` är historik och ändras inte. Granskas per grupp). Före det: 52 – SPEC och CLAUDE.md skrivs om (klart 2026-11-04: varje krock i listan i `PROGRESS.md` är rättad, avsnitt 7.1 är oförändrat, och förbudet mot riktiga kunduppgifter står kvar. Riktig data får bara finnas i driftmiljön när alla villkor i steg 118 är uppfyllda. Ingen kod). Före det: 103 – Planen skrivs om (klart 2026-11-04: BYGGPLAN.md omskriven efter Hugos beslut 2026-11-04 om planen, utan kod). Före det: 100 – Öppet 44 (klart 2026-11-04: ett förslag utan underlag ska ha flöde e:s form, bankavgiften, annars stoppas förslaget. Byggt efter Hugos beslut 2026-11-04 om granskning 30, beslut 2, committat i 40b1ec1. n1 och n4–n8 stoppas, och Z-rapporter, Swish in och kortinlösen tills deras flöden finns. Flödena är inte ändrade. Granskat i granskning 33, gult: byggt som beslutet säger, formen stämmer med flödet, flödenas utfall identiskt före och efter steget; ett fynd på nivån medel, verifikationens datum väljer regeln, så ett handbyggt förslag kan välja gräns, konto och flöde, Öppet 41, nu steg 102. Granskat och klart enligt Hugos beslut 2026-11-04 om granskning 33, beslut 5). Före det: 99 – Öppet 43 (klart 2026-11-04: ett underlag som K4 har flaggat stoppas också i `skapa_konteringsforslag`, med samma regler som flödena. Byggt efter Hugos beslut 2026-11-04 om granskning 30, beslut 1, committat i 95afce1. g11 stoppas, och flödena har bara fått konstantens import. Granskat i granskning 32, grönt: byggt som beslutet säger, ingen väg runt under samma perioder, flödenas utfall identiskt före och efter steget; låga fynd om märkningen, Öppet 49. Granskat och klart enligt Hugos beslut 2026-11-04 om granskning 32, beslut 3). Före det: 98 – Öppet 40 (klart 2026-11-04: ett förslag med både underlag och bankrad ska vara ett par bland matchningarna från `matcha_period`, annars stoppas förslaget. Byggt efter Hugos beslut 2026-11-04 om granskning 29, beslut 2, och om granskning 30, beslut 3, committat i d8a5edc. r5, g9 och g10 stoppas, och flödena är inte ändrade. Granskat i granskning 31, gult: byggt som beslutet säger, ingen väg runt under samma perioder, datumet ändrar inga par; ett fynd på nivån medel utanför steget, paren beror på hur perioden skärs, också i flödena, Öppet 46, steg 101. Granskat och klart enligt Hugos beslut 2026-11-04 om granskning 31, beslut 4). Före det: 97 – Flödenas former (klart 2026-11-04: ett förslag med underlag har exakt en av flödenas tre former, fakturan, betalningen eller kvittot, annars stoppas förslaget. Byggt efter Hugos beslut 2026-11-04 om granskning 29, beslut 1 och 3, committat i 4b3f379. Stänger Öppet 39, P3 och P4. Granskat i granskning 30, gult: formerna stämmer fält för fält med flödena och inget nytt hål i familjen. Granskat och klart enligt Hugos beslut 2026-11-04 om granskning 30, beslut 6). Före det: 95 – Öppet 36 (klart 2026-11-04: varje rad med ett underlags `belopp_ore` i debet har en egen rad på bankkontot i kredit med samma belopp ur en bankrad, och varje bankkontorad räknas bara en gång; annars stoppas förslaget. Byggt efter Hugos beslut 2026-11-04 om granskning 28, beslut 1, granskarens (a), committat 2026-11-04 i 0708667. Granskarens b1 och b3 stoppas; b2 godtas, eftersom konteringen är identisk med flöde a:s två förslag i samma förslag, Hugos beslut 2026-11-04 i chatten, Öppet 38 för redovisningskonsulten. Granskad i granskning 29, gult: byggd som beslutet säger, utom att flera bankrader godtas där beslutet säger en, P3; ett nytt hål i familjen, en bankrad som källa på kostnadskontot, Öppet 39, stängd i steg 97. Granskat och klart enligt Hugos beslut 2026-11-04 om granskning 29, beslut 5; beslutet att godta b2 ersatt av beslut 1, beslut 6). Före det: 94 – Öppet 35 (klart 2026-10-31, granskat och klart enligt Hugos beslut 2026-11-04 om granskning 28, beslut 3: i ett förslag med underlag står underlagets `belopp_ore` i debet bara när förslaget har en bankrad, och i kredit bara när underlagets `underlag_ore` och `moms_ore` inte står i kredit; annars stoppas förslaget. Byggt efter Hugos beslut 2026-10-31 om granskning 27, committat 2026-10-31 i 109fdcf och granskat i granskning 28, gult: byggt som beslutet säger ordagrant, h1 och h2 stoppas; kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en bankrad som inte hör till underlaget, Öppet 36, byggd som steg 95; ett underlag med belopp 0 stannar hela körningen, Öppet 37, steg 96). Före det: 93 – Öppet 33 och Öppet 34 (klart 2026-10-30: momsraden i ett förslag med underlag står på kontot för ingående moms, beloppet att betala räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad, och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`; annars stoppas förslaget. Byggt efter Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg", committat 2026-10-30 i 7801a64 och granskat i granskning 27, gult: byggt som beslutet säger, alla prov från granskning 26 stoppas, två hål kvar i en ny familj, Öppet 35, väntar på beslut; regeln om högst en rad beslutad av Hugo 2026-10-31). Före det: 91 – Öppet 32 (klart 2026-10-30: kostnadsraden i ett förslag med underlag står på det konto K5 ger för momssatsen, annars stoppas förslaget; byggd efter Hugos beslut 2026-10-30 om granskning 25, beslut 1, committad 2026-10-30 i c479915 och granskad i granskning 26, gult: byggd som beslutet säger, ett hål kvar i samma familj som Öppet 34, väntar på beslut). Öppet 32 och Öppet 26 fick egna stegnummer, 91 och 92, de nästa lediga (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b, `GRANSKNING.md`). Före det: 22 – Uppgift 4, flöde a, b och e (klart 2026-10-30 efter granskning 24, Hugos beslut 2026-10-30 om granskning 24, beslut 3). Granskad i granskning 22, 23 och 24. Öppet 31 (P5 i granskning 24) rättad i bbb183a, granskad i granskning 25 (grönt) och klar (Hugos beslut 2026-10-30 om granskning 25, beslut 2)
- **Nästa steg:** Steg 15: granskning 39 är klar och inget blockerar (Hugos beslut 2026-11-05 om granskning 38). Hugo kör provkörningen igen (`49 skipped`), installerar och kör spärrprovet i kopian direkt, med H1-proven i appen (steg d). Hugo eller Casper tar ställning till P1, P2 och P3 i granskning 39, helst före första commiten efter installationen. Den här veckan, parallellt: steg 53 och 54 (Hugo eller Casper kontaktar jurist och redovisningskonsult, beslut 14), steg 105 (frågorna till pilotkunden) och steg 106 (Fortnox-avtalet). Sedan säkerheten i Fas Skugg 1: steg 15, 16, 17, 18, 19 och 30. Sedan kärnan i Fas Skugg 2: steg 96, 102, 107, 108, 101, 23, 24, 26, 28 och 25. Steg 14 väntar på en ny dator (beslut 13). Öppet 38 går till redovisningskonsulten
- **Opushat:** ja: steg 100 (40b1ec1), dokumentationen efter det (ab17064), granskning 33 (33efbe4), besluten om granskning 33 (01aa499), `PLAN-KASSIO-FORSLAG.md` (a6feeb1), besluten om planen (78f146f), kompletteringen av förslaget (3e1651e), omskrivningen av planen (933d809), SPEC.md (136a2ed), CLAUDE.md (43d8c0f), namnbytet (c764101), statusraderna för steg 104 (7ca8ebd), namnbytet i den här filen (ddfe43d), steg 15 (b6ce680, 19010e8 och 011ed92), granskning 34 (b08098b), bygget efter granskning 34 (795f848), besluten om granskning 34 och statusraderna (fa47738), Hugos beslut efter P6 (b423dd4), granskning 35 (28fab6d), provkörningen och punkt 5–7 i granskning 35 (54d6acb), testerna och INSTALLERA.md efter Hugos beslut om granskning 35 (ed6b847), samma beslut i CLAUDE.md, SPEC.md och statusraderna (2572b0f), granskning 36 (4f40869), testerna, `.gitignore` och INSTALLERA.md efter Hugos beslut om granskning 36 (abded14), samma beslut i CLAUDE.md, GRANSKNING.md och statusraderna (420a57d), granskning 37 (ba353a6), testerna, `.gitignore` och INSTALLERA.md efter Hugos beslut om granskning 37 (8bd6fe5) samma beslut i CLAUDE.md, GRANSKNING.md och statusraderna (6065501), granskning 38 (103eb55), testerna, CLAUDE.md, SPEC.md och INSTALLERA.md efter Hugos beslut om granskning 38 (f52e6ef), samma beslut i GRANSKNING.md och statusraderna (c0b54e6) och den här commiten (2026-11-05, granskning 39). `origin/main` står på feba3ad enligt `git status`, den lokala uppgiften om GitHub, inte kontrollerad mot GitHub. Sessionerna efter steg 100 pushade inte. Pushen 2026-11-04 15:58 gjordes av Hugo från hans dator (Hugos beslut 2026-11-04 om granskning 30, beslut 7)

---

## Regler som gäller i hela planen

1. **Godkännande före allt.** Inget bokförs, skickas eller lämnas in innan en människa hos kunden har godkänt
   just det innehållet. Godkännandet är låst till förslagets kontrollsumma (hash).
2. **Kassio betalar aldrig.** Betalningar görs alltid av kunden i banken med BankID.
3. **Kassio signerar aldrig.** Deklarationer och årsredovisning förbereds av Kassio och signeras av kunden.
4. **Koden räknar, modellen förklarar.** Alla belopp, summor, moms och avstämningar räknas i Python. Modellen
   tolkar underlag, väljer regel och skriver förklaringar.
5. **Kärnan är gemensam.** Allt företagsspecifikt ligger i `foretag/<namn>/`. Testet att kärnan är generell
   utökas i varje steg som lägger till något.
6. **Ny datakälla = ny läsare i karantän.** Allt som kommer utifrån (mejl, PDF, bankdata, API-svar) läses av
   en del som inte kan skriva eller nå nätverket. K17 körs på allt.
7. **Spärrarna läser aldrig från en mapp agenten kan skriva i.**
8. **Inga riktiga kunduppgifter i repot.** Allt i repot byggs på syntetiska testföretag. Pilotkundens riktiga uppgifter får bara
   ligga i driftmiljön (steg 114), skild från repot, och pilotkundens namn skrivs inte i någon fil i repot (Hugos uppdrag 2026-11-04).
9. **Varje nytt flöde byggs med sin form i samma steg** (Hugos beslut 2026-11-04 om granskning 30, beslut 2). Det som
   flödena inte bygger stoppas och läggs till uttryckligen om det behövs.
10. **Granskning** (Hugos beslut 2026-11-04 om planen, beslut 3). En oberoende granskning per steg bara för det som rör godkännande,
    spärrar, skrivning i Fortnox eller pengar. Annat granskas per grupp, i en ny session när gruppens sista steg är klart och innan
    nästa grupp börjar. Fynd som kräver handbyggd kod förbi flödena och ändå en människas godkännande går till Öppet, inte till nya steg
    före piloten, utom när de rör godkännandet. **Hugos svar 2026-11-04 efter steg 103 (`GRANSKNING.md`), punkt 1:** "pengar" betyder betalningar, utbetalningar och belopp kunden
    ska betala, inte varje belopp i bokföringen. Läsaren i karantän och driftmiljön räknas som spärrar och granskas per steg.
11. **Inget skrivs i Fortnox förrän veckans utkast är godkänt, i båda lägena**, och underlag hämtas på samma sätt i båda lägena (samma beslut, 7).
12. **Nivåerna A–D sorterar och flaggar.** De styr inte vem som godkänner. Nivå D är alltid en människas beslut (samma beslut, 6).

---

# Klart

## Fas A – Grunden (klart)

| # | Steg | Status | Commit |
|---|---|---|---|
| 1 | Projektets grund: mappstruktur, `.gitignore`, belopp i öre, test att kärnan är generell | ✅ | 649b258, d9a0ce3 |
| 2 | Syntetisk testdata för Syntet Testbutik AB, 2025 Q1 | ✅ | 3fd797e |
| 3 | Inläsning av bankfil med K1 (saldokedjan) | ✅ | b36ba6c |
| 4 | Inläsning av Z-rapporter med K11 och K12 | ✅ | a2d1540 |
| 5 | Inläsning av underlag med K4, K4a, K4b, K4c och K13 | ✅ | c4dd436, ca6867d, 60fbaa3 |
| 6 | Matchning mot banken (`matcha_period`) med K3 | ✅ | 2817f42, e3a618c, c46142f |
| 7 | Uppgift 1: kontoplan och momsfil | ✅ | 5e1af42 |
| 8 | Uppgift 2: regelboken, med ägare och närstående | ✅ | 82b5e87, 3368f9e |
| 9 | Uppgift 3: konteringsförslaget med K2 och ursprungskontrollen | ✅ | 1c1bdc5 |
| 10 | Rättelserna efter granskning 1–10 (bland annat ägarlistan som stoppar, märkningen "kräver mänsklig bedömning") | ✅ | se PROGRESS.md |
| 11 | Vakten för kommandolistan: byggd, granskad (11–20), steg 4 h provkört | ✅ | f21a3a1 till 567692b |

---

## Fas B – Säkerhetsgrunden, det som är klart (resten står i Fas Skugg 1 och Fas Väntar)

| # | Steg | Status | Klart när | Beror på |
|---|---|---|---|---|
| 12 | **Hugo installerar vakten** enligt `sparr/INSTALLERA.md` | ✅ 2026-10-29 | Den nya filen utan `disableAutoMode` (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen") är installerad med steg 10–13, och kontrollen steg 1, 2, 3 och 9 är gjord igen, med läget "auto" valbart i steg 1 (INSTALLERA.md, "Byte av inställningsfil"). Gjort och grönt på Hugos dator 2026-10-29 (`GRANSKNING.md`, "Kontroll efter bytet av inställningsfil, 2026-10-29"). Första installationen: `/status` visar `Enterprise managed settings (file)` och vakten stoppar `date` i skrivbordsappen. Gjort på Hugos dator 2026-10-28 (`GRANSKNING.md`, "Installation på Hugos dator 2026-10-28"). Caspers dator är steg 14 | 11 |
| 13 | Kontrollen efter installationen, i en ny session (sist i INSTALLERA.md), inklusive provet med en vakt som fallerar | ✅ 2026-10-29 | Alla steg i kontrollen visar väntat svar. Steg 1–7 och 9 gjorda vid installationen, och spärrtestet 2026-10-29 är grönt. Steg 8 (provet med en vakt som fallerar) och steg 9 igen efter det är gjorda och gröna 2026-10-29, med samma kontrollsummor (`GRANSKNING.md`, "Steg 8, provet med en vakt som fallerar, 2026-10-29", PROGRESS.md, Öppet 16 stängd) | 12 |
| 20 | Q3 + Q4 + Q2: gemensam ordindelning, kommentaren i `las_regelbok.py`, ägarnamn utan accenter | ✅ | Tester gröna. Q2, Q2b, Q3 och Q4 klara (3e3c18c, d7d38e0, 1dcf769, bd851ba, 2bc9762) och granskade i granskning 21 (3bbcbe4, grön). Byggt före steg 19 | 19 |
| 21 | Q7: pusha som det är (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd"). Historiken skrivs inte om, och ingen tagg byts eller pushas (taggen `v0-shop-and-go` finns inte i repot) | ✅ | Repot på GitHub är privat (kontrollerat av Hugo 2026-10-29). Repot får inte göras publikt utan en ny genomgång av hela historiken först. Q7 stängd och pushat 2026-10-29 (`main` i fas med GitHub vid 6aba32d) | 20 |

---

## Fas C – Kärnan, det som är klart (resten står i Fas Skugg 2 och Fas Pilot 2)

| # | Steg | Status | Klart när | Lånat från | Beror på |
|---|---|---|---|---|---|
| 22 | **Uppgift 4:** flöde a, b och e (leverantörsfakturor, kvitton, bankavgifter) med K5 och K8. Byggs på syntetisk data, med vakten installerad och Claude Code i det läge som frågar (inte Auto) tills provet med en fallerande vakt (Öppet 16) är gjort. Förutsättningar: B2 och B3 i `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4". **Beslut:** D13 (moms på bankavgifter, bankraden som underlag) och vad "bankens datum" i D14 betyder är beslutade för testföretaget (Hugos beslut i chatten 2026-10-29, `GRANSKNING.md`, "D13 och D14 beslutade") | ✅ 2026-10-30. Byggd 2026-10-29 och granskad i granskning 22 (e4d8cd7, gult), 23 (269d641, gult) och 24 (6dfcdcd, grönt). P1 och P2 rättade 2026-10-30 (d5b2fba), P1 och P3 från granskning 23 rättade och Öppet 29 stängd (13126d2, 35afa8b). Klart efter granskning 24 (Hugos beslut 2026-10-30 om granskning 24, beslut 3). Öppet 31 från granskning 24 rättad i bbb183a, granskad i granskning 25 (grönt) och klar (Hugos beslut 2026-10-30 om granskning 25, beslut 2). Öppet 32 (granskning 25, P7) är steg 91 och Öppet 26 steg 92 (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b) | Testerna i DESIGN 7, rad 4, är gröna | – | 12, 20, 21. Beror inte på steg 15 (Hugos beslut 2026-10-29, B1) |
| 91 | **Öppet 32** (granskning 25, P7): kostnadsraden i ett förslag med underlag står på det konto K5 räknar fram för underlagets momssats, annars stoppas förslaget i `skapa_konteringsforslag` (`_kontrollera_underlagen`). Också ett annat konto i regeln och ett rollkonto som leverantörsskulderna stoppar. Eget steg före steg 23, med nästa lediga nummer (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b, `GRANSKNING.md`). Momsraden (`moms_ore`) ingår inte: den är Öppet 33, ett eget steg efter det här (samma beslut, a) | ✅ 2026-10-30. Byggd efter Hugos beslut 2026-10-30 om granskning 25 (beslut 1), testerna i `scripts/tests/test_beslut_granskning_25.py` röda före (5 av 14 mot 7c1f148). Committad 2026-10-30 i c479915 (PROGRESS.md, "Läge 2026-10-30, Öppet 32 rättad"). Granskad i granskning 26 (gult: byggd som beslutet säger, granskarens två prov stoppas; ett hål kvar i samma familj, Öppet 34, eget beslut) | Granskarens två prov från P7 stoppas, och flöde a, b och e går igenom med varje kostnadsrad på kontot K5 ger | – | 22 |
| 93 | **Öppet 33 och Öppet 34** i samma steg (Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg", `GRANSKNING.md`). Öppet 33: varje rad i ett förslag med ett underlags `moms_ore` som källa står på kontot för ingående moms (rollen i kontoplanen), annars stoppas förslaget (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a). Öppet 34 (granskning 26, M1): en rad med ett underlags `belopp_ore` som källa räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad i förslaget (det sista är byggsessionens tillägg, för granskarens fjärde prov), och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`. Båda i `skapa_konteringsforslag` (`_kontrollera_underlagen`), efter Öppet 32. Docstringen om momsraden rättad (granskning 26, L1) | ✅ 2026-10-30. Byggd i 7801a64 (PROGRESS.md, "Läge 2026-10-30, Öppet 33 och 34 byggda"), testerna i `scripts/tests/test_beslut_granskning_26.py` röda före (12 av 22 mot `git archive` av 5b4aa83). Granskad i granskning 27 (gult: byggd som beslutet säger, H7 och de fyra LUCKA-proven stoppas; två hål i en ny familj, beloppet i debet utan bankrad, Öppet 35, eget beslut). Regeln om högst en rad beslutad av Hugo 2026-10-31 | Granskarens prov H7 och de fyra LUCKA-proven från granskning 26 stoppas, och flöde a, b och e går igenom | – | 91 |
| 94 | **Öppet 35** (granskning 27, M1, Hugos beslut 2026-10-31 om granskning 27: "Beloppet i debet ska kräva en bankrad. belopp_ore får bara stå i kredit när delarna inte gör det."). I ett förslag med underlag står underlagets `belopp_ore` i debet bara när förslaget har minst en bankrad, och i kredit bara när underlagets `underlag_ore` och `moms_ore` inte står i kredit. I `skapa_konteringsforslag` (`_kontrollera_underlagen`, ny delkontroll `_kontrollera_beloppssidan`), sist efter Öppet 33 | ✅ 2026-10-31. Byggd i 109fdcf (PROGRESS.md, "Läge 2026-10-31, Öppet 35 byggd"), testerna i `scripts/tests/test_beslut_granskning_27.py` röda före (5 av 13 mot koden i b7d9fac). Granskad i granskning 28 (gult: byggd som beslutet säger ordagrant, h1 och h2 stoppas, "rött före" upprepat mot `git archive` av b7d9fac; kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en bankrad som inte hör till underlaget, Öppet 36, eget beslut; ett underlag med belopp 0 stannar hela körningen, Öppet 37, utanför steget). Granskat och klart (Hugos beslut 2026-11-04 om granskning 28, beslut 3). Öppet 36 är steg 95 och Öppet 37 steg 96 | Granskarens prov h1 och h2 från granskning 27 stoppas, och flöde a, b och e går igenom | – | 93 |
| 95 | **Öppet 36** (granskning 28, M1, Hugos beslut 2026-11-04 om granskning 28, beslut 1, granskarens (a)): för varje rad med ett underlags `belopp_ore` i debet ska förslaget ha en egen rad på bankkontot (rollen `bank` i kontoplanen) i kredit, med samma belopp och med en bankrad som källa, och varje bankkontorad räknas bara en gång. I `skapa_konteringsforslag` (`_kontrollera_beloppssidan`, grenen för debet, efter Öppet 35:s krav på någon bankrad alls). Hittar nästa granskning ett nytt hål i familjen Öppet 31–36 går vi över till (b), flödenas former rakt av | ✅ 2026-11-04. Byggd i 0708667 (PROGRESS.md, "Läge 2026-11-04, Öppet 36 byggd"), testerna i `scripts/tests/test_beslut_granskning_28.py` röda före (4 av 9 mot koden i 3f36f6b). Granskarens b1 och b3 stoppas. b2 godtas: konteringen är identisk med flöde a:s två förslag i samma förslag (Hugos beslut 2026-11-04 i chatten, inte ett nytt hål; Öppet 38 för redovisningskonsulten). Granskad i granskning 29 (gult: byggd som beslutet säger, utom att flera bankrader godtas där beslutet säger en, P3; rött före 4 av 9 upprepat mot `git archive` av 3f36f6b; parningen ger samma utfall i alla radordningar; ett nytt hål i familjen, en bankrad som källa på kostnadskontot, Öppet 39, stängd i steg 97). Granskat och klart (Hugos beslut 2026-11-04 om granskning 29, beslut 5). Beslutet att godta b2 ersatt (beslut 6) | Granskarens prov b1 och b3 från granskning 28 stoppas, två belopp i debet delar inte en bankkontorad, och flöde a, b och e går igenom | – | 94 |
| 97 | **Flödenas former** (Öppet 39, granskning 29, P1, Hugos beslut 2026-11-04 om granskning 29, beslut 1 och 3, granskarens (b) rakt av): ett förslag med underlag har exakt en av flödenas tre former, fakturan, betalningen eller kvittot. Allt annat stoppas, också b2, två betalningar i samma förslag och en betalning ur flera bankrader. Det som flödena inte bygger läggs till uttryckligen om det behövs. I `skapa_konteringsforslag` (`_kontrollera_flodets_form`, allra sist i `_kontrollera_underlagen`, efter Öppet 36). Stänger Öppet 39, P3 och P4. Byggt före steg 96 på Hugos uppdrag | ✅ 2026-11-04. Byggd i 4b3f379 (PROGRESS.md, "Läge 2026-11-04, steg 97 byggt"), testerna röda före (22 mot `git archive` av c9a6cee: 19 av 25 i `scripts/tests/test_beslut_granskning_29.py` och 3 omgjorda skydd). Mutationsprov: nio ändringar, alla ger rött. Granskad i granskning 30 (gult: formerna stämmer fält för fält med flödena, rött före 22 upprepat mot `git archive` av c9a6cee, sviten 4 468, inget nytt hål i familjen; tre hål på nivån medel utanför formerna, Öppet 43 och 44 och en bredare Öppet 40, beslutade). Granskat och klart (Hugos beslut 2026-11-04 om granskning 30, beslut 6) | Granskarens r3, r6–r9, r11 och r16 stoppas, b2 och två betalningar stoppas, och varje förslag med underlag i hela körningen har exakt en av de tre formerna | – | 95 |
| 98 | **Öppet 40** (granskning 29, P2, Hugos beslut 2026-11-04 om granskning 29, beslut 2, och granskning 30, P3, Hugos beslut 2026-11-04 om granskning 30, beslut 3): bankraden ska kontrolleras mot underlaget med samma matchning som flödena använder. Ett förslag med både underlag och bankrad ska vara ett par bland matchningarna från `matcha_period`. I `skapa_konteringsforslag` (`_kontrollera_bankradens_par`, allra sist, efter formerna), som kör `matcha_period` själv och inte tar emot något matchningsresultat. Testet som dokumenterade r5 är omskrivet till ett stopp-test (`test_oppet_40_r5_en_annan_leverantors_bankrad_stoppas`) | ✅ 2026-11-04. Byggd i d8a5edc (PROGRESS.md, "Läge 2026-11-04, steg 98 byggt"), testerna röda före (16 mot `git archive` av 2a57517: 15 av 24 i `scripts/tests/test_beslut_granskning_30.py` och r5 omgjort). Mutationsprov: sex ändringar, alla ger rött, efter ett test som lades till när en överlevde. Sviten 4 492. Flödena är inte ändrade. Granskad i granskning 31 (gult: byggd som beslutet säger, rött före 16 upprepat mot `git archive` av 2a57517, sviten 4 492, alla 9 förslag med underlag och bankrad har sitt par, ingen väg runt under samma perioder; Öppet 46 är större än byggsessionen säger, steg 101). Granskat och klart (Hugos beslut 2026-11-04 om granskning 31, beslut 4) | r5, g9 och g10 stoppas, ett saknat eller handbyggt matchningsresultat ger inget förslag, och flöde a, b och e går igenom | – | 97 |
| 99 | **Öppet 43** (granskning 30, P1, Hugos beslut 2026-11-04 om granskning 30, beslut 1): `skapa_konteringsforslag` ska stoppa ett underlag som K4 har flaggat, i linje med beslutet 2026-10-30 om granskning 22, punkt 3 ("inget förslag alls"), med samma regler som flödena (Öppet 29). I `skapa_konteringsforslag` (`_kontrollera_k4`, allra sist, efter Öppet 40). K4a, K4b och "K4a och K4b": båda underlagen stoppas. K4c: det flaggade stoppas, och originalet godtas bara med märkningen. K4 (dublett): kan inte nås. Eget steg, före uppgift 5 | ✅ 2026-11-04. Byggd i 95afce1 (PROGRESS.md, "Läge 2026-11-04, steg 99 byggt"), testerna i `scripts/tests/test_beslut_granskning_31.py` röda före (46 av 60 mot `git archive` av 344a8d2: 41 "DID NOT RAISE" och 5 kodtest). Mutationsprov: tio ändringar, alla ger rött. Sviten 4 552. Flödena har bara fått konstantens import. Granskad i granskning 32 (grönt: byggd som beslutet säger, rött före 46 av 60 upprepat mot `git archive` av 344a8d2, sviten 4 552, flödenas utfall identiskt före och efter steget i 67 uppställningar, ingen väg runt under samma perioder, inget nytt hål i familjen; låga fynd, Öppet 49). Granskat och klart (Hugos beslut 2026-11-04 om granskning 32, beslut 3) | Fakturan i flödets form för ett underlag som K4 har flaggat stoppas (granskarens g11), och flöde a, b och e går igenom | – | 98 |
| 100 | **Öppet 44** (granskning 30, P2, Hugos beslut 2026-11-04 om granskning 30, beslut 2): förslag utan underlag ska ha fasta former, samma princip som (b). Formen för flöde e byggs här, som eget steg, före uppgift 5. Formerna för flöde c och d byggs i samma steg som flödena (regel 9). I `skapa_konteringsforslag` (`_kontrollera_forslag_utan_underlag`, allra sist, efter K4). Allt annat utan underlag stoppas tills dess flöde finns | ✅ 2026-11-04. Byggd i 40b1ec1 (PROGRESS.md, "Läge 2026-11-04, steg 100 byggt"), testerna röda före (34 mot `git archive` av feba3ad: 25 av 39 i `scripts/tests/test_beslut_granskning_32.py` och 9 omgjorda). Mutationsprov: 15 ändringar, 13 gav rött direkt, två överlevde och ledde till ett enklare villkor i koden. Sviten 4 592. Flödena är inte ändrade. Granskad i granskning 33 (gult: byggd som beslutet säger, rött före 34 upprepat mot `git archive` av feba3ad, sviten 4 592, flödenas utfall identiskt före och efter steget, inget äldre stopp borta ur testerna; datumet väljer regeln, så ett handbyggt förslag kan välja gräns, konto och flöde, Öppet 41, nivå medel, väntar på besked). Granskat och klart (Hugos beslut 2026-11-04 om granskning 33, beslut 5). Öppet 41 är steg 102 (samma beslut, 1) | Granskarens n1 stoppas, och de andra proven i granskning 30, P2, stoppas eller är avgjorda för uppgift 5. Bankavgiften i flöde e går igenom | – | 98 |

---

# Mål 1: Skuggpiloten

**Förslag: 2027-01-11 (uppskattning).** Kassio tar fram veckoutkast på pilotkundens riktiga data, och inget skrivs i Fortnox.

**Säkerhet:** riktig data får inte användas förrän steg 118:s villkor är uppfyllda. Det som hindrar i dag: CLAUDE.md och SPEC 8 förbjuder riktiga kunders uppgifter tills villkoren är uppfyllda (omskrivna i steg 52, och förbudet gäller fullt ut), juristens svar saknas (steg 53), driftmiljön saknas (steg 114) och sandlådan saknas (steg 15).

## Fas Skugg 0 – Beslut och omskrivning (grupp 0)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 103 | **Planen skrivs om** efter Hugos beslut 2026-11-04 om planen. Ingen kod | ✅ 2026-11-04. Se PROGRESS.md, "Läge 2026-11-04, Hugos beslut om planen" | Alla steg finns kvar med sina nummer, klara steg har sin historik, och byggplanstestet är grönt | per grupp | – | – |
| 52 | **Beslut (ingen kod):** Hugo ändrar SPEC avsnitt 10 så att fakturering, lönekontroll, momsdeklaration, bokslut och årsredovisning blir planerade steg. Betalningar och egen signering stannar utanför för alltid. Efter Hugos beslut 2026-11-04 om planen (beslut 2 och 4–11) ingår också de andra krockarna i SPEC och CLAUDE.md, listade i PROGRESS.md | ✅ 2026-11-04. SPEC.md i 136a2ed, med tabellen "Ändrat 2026-11-04" överst. Avsnitt 7.1 är oförändrat. Se PROGRESS.md, "Läge 2026-11-04, SPEC.md och CLAUDE.md omskrivna" | Beslutet skrivet i SPEC med namn och datum, och varje krock i listan är rättad eller har ett eget beslut | per grupp | – | 103 |
| 104 | **Namnbytet till Kassio** i dokument och kod (beslut 12). `sparr/` och sökvägen `/Library/Application Support/ClaudeCode/vera` ändras inte här: de ändras bara som en ny version av vakten (SPEC 7.1). Repot byter namn senare, steg 148 | ✅ | En sökning efter "Vera" i dokument och kod ger bara historik eller vaktens sökväg, och testsviten är grön | per grupp | – | 52 |
| 53 | **Beslut (ingen kod):** jurist om penningtvättslagen (säljs Kassio som tjänst eller program?), kundavtal, ansvarsbegränsning, personuppgiftsbiträdesavtal, överföring till USA (Anthropic har ingen EU-region). Också riktig data i skuggpiloten, bankkoppling, inkasso, och pilotkundens två roller och skriftliga godkännande. Hugo eller Casper kontaktar juristen den här veckan (beslut 14) | ⬜ | Skriftligt svar från jurist | per grupp | Jolenes villkor | – |
| 54 | **Beslut (ingen kod):** redovisningskonsult svarar på DESIGN D1–D16 för riktiga företag. Också Ö3, Ö4, Öppet 38, momsen när kvitto saknas (beslut 5), utlägg och bokföringsmetoderna. Hugo eller Casper kontaktar konsulten den här veckan (beslut 14) | ⬜ | Svaren skrivna i DESIGN 8 | per grupp | – | – |
| 105 | **Frågorna till pilotkunden (ingen kod):** pilotavtal, vem som godkänner, tillgång till Fortnox, om kunden vill vara med i en skuggpilot, vilken bokföringsmetod som används (beslut 10), vilket kassasystem, och skriftligt godkännande för siffror i marknadsföring | ⬜ | Svaren är skrivna. I repot står bara det som inte pekar ut kunden, aldrig namnet | per grupp | – | – |
| 106 | **Fortnox-avtalet (ingen kod):** registrera som utvecklare, App Partner-avtalet, och svar från Fortnox: gäller hela granskningen också en enda gratis pilotkund, och finns en testdatabas? | ⬜ | Utvecklarkontot finns, och Fortnox svar på de två frågorna är skrivna | per grupp | – | – |

## Fas Skugg 1 – Säkerhet (grupp 1)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 15 | **Sandlådan** (Öppet 4 och 8): skrivning bara i tillåtna mappar, förbud för appen, appens Claude Code och `~/.local/share/claude`, täcker `trap`, `hash` och `builtin`. Ska vara klar före steg 23 (uppgift 5), eller före första körningen på riktiga underlag om den kommer först (Hugos beslut 2026-10-28 och 2026-10-29, B1) | 🔶 | Spärrtest: en egen testfil som försöker skriva utanför projektet stoppas | per steg | – | 13 |
| 16 | Bash-vägen prövas i skrivbordsappen (Öppet 7) | ⬜ | Beslut skrivet: bash eller zsh | per steg | – | 15 |
| 17 | Omvägarna förbi vakten med kommandotexter i en kopia (granskning 13, P5) | ⬜ | Inga omvägar hittade, eller rättade | per steg | – | 15 |
| 18 | Nästa version av vakten: `-I -S` (K1) och tom `cwd` (K3) från granskning 20 | ⬜ | Tester gröna, ny granskning | per steg | – | 17 |
| 19 | Spärrtest i en ny session | ⬜ | Alla spärrtester blockeras och syns i loggen. (Ett första spärrtest efter installationen gjordes 2026-10-29 och är grönt, men det här steget är spärrtestet efter steg 15–18) | per steg | – | 15, 16, 17, 18 |
| 30 | **Godkända kontrollsummor** (Ö12): regelbok, kontoplan och momsfil jämförs mot godkänd summa i skyddad mapp | ⬜ | Spärrtest "ändrad regelbok" stoppas | per steg | – | 19 |

## Fas Skugg 2 – Kärnan, det skuggpiloten behöver (grupp 2)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 96 | **Öppet 37** (granskning 28, M2, Hugos beslut 2026-11-04 om granskning 28, beslut 2): ett underlag med `belopp_ore` 0 ska bli ett ärende för just det underlaget, och resten av perioden ska fortsätta. I dag läses underlaget in utan anmärkning, flöde a bygger en faktura med en rad, K2 stoppar och felet går upp genom `kontera_period`, så hela körningen stannar utan ärende. Eget steg, inte en del av steg 95. **Steget omfattar också:** Öppet 48 (Hugos beslut 2026-11-04 om granskning 31, beslut 2), Öppet 49 P4, testet och hjälpfunktionen (Hugos beslut 2026-11-04 om granskning 32, beslut 2), de två missvisande testen i Öppet 50 a (Hugos beslut 2026-11-04 om granskning 33, beslut 2), och att SPEC 7 i stegets dokumentation beskriver de nya kontrollerna, Öppet 36, 40, 43, formerna och Öppet 44 (Hugos beslut 2026-11-04 om granskning 32, beslut 4, och om granskning 33, beslut 4, Öppet 47 b) | ⬜ | Ett underlag med belopp 0 i en kopia av testdatan ger ett ärende för det underlaget, och de andra underlagen i perioden får förslag som förut. SPEC 7 beskriver kontrollerna, och Öppet 48, Öppet 49 P4 och Öppet 50 a är rättade | per grupp | – | 94 |
| 102 | **Öppet 41** (granskning 29, P5, och granskning 33, P1, Hugos beslut 2026-11-04 om granskning 33, beslut 1): verifikationens datum prövas mot det datum flödet skulle ha valt, för förslag både med och utan underlag. Datumet räknas som en del av formen, samma princip som (b). Eget steg med nästa lediga nummer, före steg 23 (uppgift 5). Ersätter "senare, låg prioritet" i beslut 4 om granskning 29. Flödena tar datumet ur regelbokens `bokforing`. Granskning 33 provade det bara för förslag utan underlag, så förslag med underlag är inte provade | ⬜ | Granskarens c1–c4 och d1 från granskning 33 stoppas, betalningen med ett datum före både fakturan och bankraden (granskning 29, P5) stoppas, och flöde a, b och e går igenom med samma utfall som förut | per steg | – | 100 |
| 107 | **Syntet nystartat AB:** testföretag och testdata för ett nystartat aktiebolag utan historik. Ersätter Krog och Bygg före piloten (beslut 11) | ⬜ | Kärnan oförändrad, rapporten stämmer med facit på kronan, och allt är märkt som syntetiskt | per grupp | – | 22 |
| 108 | **Bokföringsmetoden:** bara den metod pilotkundens ekonomiansvarige svarar byggs (beslut 10). Faktureringsmetoden finns i dag. Vad som gäller för vem är en **Öppen fråga** till konsulten | ⬜ | Svaret är skrivet. Är det faktureringsmetoden stängs steget utan kod. Är det kontantmetoden stämmer testdata för metoden med facit på kronan | per grupp | – | 54, 105 |
| 101 | **Registret över vad som är bokfört** (designsteg före piloten, Hugos beslut 2026-11-04 om granskning 31, beslut 1 och 3, ihop med beslut 5 om granskning 30, Öppet 45, 46 och 47 a): ett register över vad som redan är bokfört, som varje körning läser. Inget underlag och ingen bankrad får bokföras två gånger, varken i samma körning eller över körningar. När flera fakturor passar samma betalning blir det ett ärende där kunden väljer. Designen tar också med tiden (Öppet 47 a, uppmätt). Designen avgör också om en enkel variant behövs redan i skuggpiloten, eftersom en körning per vecka annars kan visa samma betalning två gånger (Öppet 46). Registret byggs i steg 119 | ⬜ | Designen är skriven och godkänd av Hugo eller Casper. Hur den byggs bestäms i designen | per steg | – | 98 |
| 23 | **Uppgift 5:** flöde c och d (Z-rapporter, kortinlösen, Swish, kontantinsättningar) och M9, med sina former i samma steg (regel 9). Radnumret läggs tillbaka när flöde d byggs (Hugos beslut 2026-11-04 om granskning 33, beslut 2, Öppet 50 b). Behöver pilotkunden inte kassan i skuggpiloten (steg 105) kan Hugo eller Casper flytta steget | ⬜ | Försäljning per sats och månad stämmer på öret med `facit.json` | per steg | Jolene (Z-nummerserien, bokför aldrig dagskassa utan kontroll) | 15, 22, 99, 100, 102 |
| 24 | **Uppgift 6:** nivåerna A–D och K9, nivå D för ägarens bankrader. Nivåerna sorterar och flaggar (beslut 6) | ⬜ | Varje skäl ger rätt nivå. Högsta nivån vinner | per steg | – | 23 |
| 26 | **Ursprungsmärkning och "varför":** varje förslag märks *regel*, *exakt matchning*, *tidigare godkänd* eller *modellens förslag*, plus en rad "varför" som namnger regel-id | ⬜ | Varje förslag i testdatan har märkning och förklaring | per grupp | Xero (Match/Rule/Memory/Prediction), Ramp | 24 |
| 28 | **K17 instruktioner i underlag** (Ö10) | ⬜ | Spärrtest: kvitto med "ignorera reglerna" blir ärende, inget förslag | per steg | OWASP, Willison | 24 |
| 25 | Oberoende granskning av uppgift 4–6 och av den här gruppen | ⬜ | Inga allvarliga eller medelfynd kvar | är gruppens granskning | – | 26, 28 |

## Fas Skugg 4 – Fortnox, bara läsning (grupp 4)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 112 | **Tunn hel kedja, utan skrivning:** en faktura hämtas ur Fortnox testdatabas, blir ett förslag och visas i en enkel webbsida där den godkänns. Visar de största okända sakerna tidigt. Skrivningen in i testdatabasen görs i steg 56. Finns ingen testdatabas bestäms vägen i steg 106 | ⬜ | Fakturan går hela vägen på syntetisk data, och inget skrivs i Fortnox | per grupp | – | 22, 106 |
| 55 | **Fortnox-koppling, läsning:** kontoplan, verifikationer, leverantörsreskontra, bankens transaktioner och skattekonto (om API:et tillåter) via Fortnox testdatabas | ⬜ | Läsningen stämmer med testdatabasen. Okända API-delar dokumenterade | per grupp | Fortnox API | 106, 112 |
| 113 | **Skuggspärren:** i skuggläget kan inget skrivas i Fortnox, vad som än händer (beslut 2). Spärren ligger i kod, eftersom en Fortnox-nyckel kan ha skrivrätt (steg 56) | ⬜ | Spärrtest: ett försök att skriva från skuggläget mot testdatabasen stoppas, och testdatabasen är oförändrad efteråt | per steg | – | 19, 55 |

## Fas Skugg 5 – Veckoutkastet (grupp 5)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 32 | **Ärenden:** mall, prioritet, påminnelse, svar som blir nytt förslag. Granskarens invändningar kommer in när steg 31 är byggt | ⬜ | Ett svar ger nytt förslag med hänvisning | per steg | – | 26 |
| 33 | **Veckorapporten och godkännandet** i båda lägena (granskat och automatiskt), låst med hash, mobilvänlig sida. Sammanfattning, osäkra eller ovanliga poster överst, och hela listan finns. Nivåerna sorterar och flaggar (beslut 6). Kortet visar underlag, förslag, varför och varningar, med text som räknas fram ur raderna (Öppet 45 och 49). I skuggpiloten händer inget i Fortnox efter godkännandet. Post för post i granskat läge är steg 125 | ⬜ | Spärrtest: ändrad rad efter godkännande stoppas | per steg | GitHub (Accept all/Decline), Pleo (OK/Behöver åtgärd), Ramp | 32 |

## Fas Skugg 6 – Underlag in (grupp 6)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 109 | **Läsare för foto och PDF:** gör ett foto eller en PDF till data, i karantän (regel 6), med K17 på allt. Språkmodellen kommer in här, med riktig data först efter juristens svar. Hur en modell går ihop med regel 6, "kan inte nå nätverket", bestäms i steget | ⬜ | Syntetiska foton och PDF:er ger samma data som facit, ett underlag med dolda instruktioner blir ärende, och en osäker läsning blir ärende, inte ett förslag | per steg | – | 15, 28 |
| 59 | **E-postinkorg:** kunden vidarebefordrar kvitton och fakturor till en egen adress (beslut 8). Läsaren i karantän, K17 på allt | ⬜ | Spärrtest: mejl med dolda instruktioner blir ärende | per steg | Jolene, Bokio kvittoinkorg | 28 |
| 110 | **Kontoutdrag som fil** (beslut 8): en fil i pilotkundens bankformat läses i karantän, med K1. Formatet jämförs mot en riktig exportfil (SPEC Ö5). Uppladdningen i appen är steg 68 | ⬜ | Ett kontoutdrag med syntetiskt innehåll i det riktiga formatet läses, och ett ändrat saldo stoppar filen | per steg | – | 28 |
| 111 | **Kassan in:** dagsavslut från pilotkundens kassasystem. **Öppen fråga:** går systemet att koppla direkt, eller ger det en fil? Direkt koppling är kravet (`KASSIO-KRAV.md`) | ⬜ | Frågan är besvarad, och dagsavslut med syntetiskt innehåll i systemets riktiga format läses med K11 och K12 | per steg | – | 23, 28, 105 |

## Fas Skugg 7 – Appen och driften (grupp 7)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 114 | **Driftmiljön** (SPEC Ö1): var agenten körs och var kundens uppgifter ligger, skilt från repot. Vem som kan läsa uppgifterna, säkerhetskopior och vad som händer när något går sönder. Krypteringslöftet formuleras i steg 139 | ⬜ | Beslutet är skrivet med namn och datum, en säkerhetskopia är återläst en gång, och kontrollerat att uppgifter i driftmiljön inte hamnar i repot | per steg | – | 19, 53 |
| 115 | **Kassios egen kommandolista** (SPEC 7.1 säger att den ska skrivas): vad agenten får köra hos en kund. Vakten skyddar bygget här, inte en körning hos en kund | ⬜ | Listan är skriven, och spärrtest: ett kommando utanför listan i driftmiljön stoppas | per steg | – | 114 |
| 116 | **Pilotkundens konfiguration utanför repot:** regelbok, kontoplan, momsfil, bank- och kassaformat ligger i driftmiljön (regel 8). Kärnan ändras inte | ⬜ | Kärnan kör på konfigurationen i driftmiljön, och inget ur den finns i repot | per steg | – | 105, 108, 114 |
| 68 | **Webbappen, version 1** (hette Egen app): fungerar i mobilen (beslut 9). Inloggning med tvåstegsverifiering, att-göra-lista, veckoutkastet och godkännandet, uppladdning av kontoutdrag, notiser (mejl, kunden väljer veckodag), roller och ersättare. Chatten är steg 75, foto steg 130 och mobilappen steg 142 | ⬜ | En testkund godkänner en vecka helt i mobilen | per steg | Jolene, Wint (att-göra), Spendesk, Ramp | 33, 110, 114 |

## Fas Skugg 12 – Genrep och start (grupp 12)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 117 | **Genrep för skuggpiloten:** en hel vecka på det syntetiska nystartade bolaget i driftmiljön, från underlag till veckoutkast och godkännande | ⬜ | Veckoutkastet stämmer med facit på kronan, spärrtesterna i steg 19 och 113 är gröna i driftmiljön, och gruppernas granskningar har inga allvarliga eller medelfynd kvar | per steg | – | 19, 30, 59, 68, 107, 109, 111, 113, 115 |
| 118 | **Skuggpiloten startar** (förslag: 2027-01-11, uppskattning): Kassio tar fram veckoutkast på pilotkundens riktiga data, inget skrivs i Fortnox, och ekonomiansvarige bokför som vanligt och jämför (beslut 2) | ⬜ | Första veckoutkastet på riktig data är visat, och Fortnox är oförändrat av Kassio | per steg | – | 52, 53, 54, 105, 116, 117 |

---

# Mål 2: Piloten med Fortnox

**Förslag: 2027-03-01 (uppskattning).** Bokföring, moms och veckoutkast skrivs i Fortnox efter godkännande. I båda lägena skrivs inget förrän veckans utkast är godkänt (regel 11).

## Fas Pilot 2 – Kärnan klar (grupp 2)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 92 | **Öppet 26:** kontona 5010 Lokalhyra, 5020 El för belysning och 6210 Telekommunikation i testbutikens kontoplan, med en ny titt på B3:s D2, och sedan regler för HYRESVARD (nivå D), LEV-EL och LEV-TELE (PROGRESS.md, Öppet 26, Hugos besked i chatten 2026-10-29). Eget steg med nästa lediga nummer (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b). **Beslut:** D10 och D11 är öppna | ⬜ | Underlagen från de tre motparterna får förslag i stället för ärendet "ny motpart", och kärnan är oförändrad | per grupp | – | 22 |
| 29 | **K4 mot arkivet** (Ö9), **bankens avgiftsspecifikation** (Ö11), **kreditnotor** (Ö8) | ⬜ | Tester gröna | per grupp | – | 24 |
| 27 | **K6 rätt period** och **låsta perioder:** en stängd månad kan bara ändras med motverifikation och nytt godkännande | ⬜ | Spärrtest: förslag i stängd period stoppas | per steg | Digits Locked Periods | 24 |
| 35 | **Logg och spårbarhet:** append-only logg med kedjad hash, och ett kommando som visar hela kedjan underlag → förslag → godkännande → verifikation | ⬜ | Manipulerad logg upptäcks | per steg | Digits Activity Log | 33 |
| 36 | **K10 månadsavstämning:** bank, kassa, skattekonto, leverantörsskulder, moms, försäljning mot kassa. Vid en skillnad letar Kassio förklaringen själv. Hittas den föreslås bokföring med förklaring, annars stoppas utkastet och kunden får frågan (`KASSIO-KRAV.md`) | ⬜ | Testbutikens månader stämmer med facit | per grupp | – | 33 |
| 37 | **Facit-svit ("golden ledger"):** hela kvartalet körs mot facit vid varje ändring och modellbyte | ⬜ | Rapporten stämmer med facit på kronan (SPEC fas 0 klar) | per grupp | Anthropic om evals | 36 |
| 119 | **Registret byggs** efter designen i steg 101: varje körning läser vad som redan är bokfört, inget underlag och ingen bankrad bokförs två gånger, och flera fakturor som passar samma betalning blir ett ärende där kunden väljer | ⬜ | Granskarens s2 och s3 från granskning 31 ger inte två betalningar, och samma körning två gånger ger inga nya förslag | per steg | – | 35, 101 |
| 38 | Oberoende granskning av kärnan (hette fas C) | ⬜ | Inga allvarliga eller medelfynd kvar | är gruppens granskning | – | 29, 37, 92, 119 |

## Fas Pilot 3 – Kassios krav i kärnan (grupp 3)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 120 | **Kvitto saknas:** ett förslag ändå, med egen form och märkningen "kvitto saknas" (beslut 5), i stället för K3:s ärende. Kassio påminner, och kunden kan godkänna med egen förklaring. **Öppen fråga:** momsen i det fallet går till redovisningskonsulten | ⬜ | Ett förslag utan kvitto har formen och märkningen och visas märkt på kortet, allt annat utan underlag stoppas som förut (steg 100), och momsen följer konsultens svar | per steg | – | 33, 54 |
| 121 | **Kunden ändrar ett förslag, designen** (beslut 4): vad kunden får ändra, hur Kassio varnar och hur formen ser ut. Förslaget ska alltid gå ihop (K2), en stängd period förblir stängd, och inget skrivs före godkännandet | ⬜ | Designen är skriven, oberoende granskad som säkerhet och godkänd av Hugo eller Casper | per steg | – | 27, 33 |
| 122 | **Kunden ändrar ett förslag, bygget** efter designen i steg 121, med sin form i samma steg | ⬜ | Spärrtest: ett ändrat förslag som inte går ihop stoppas, en ändring i en stängd period stoppas, en ändring efter godkännandet kräver nytt godkännande, och inget skrivs före godkännandet | per steg | – | 121 |
| 130 | **Foto i webbappen** (beslut 9): kunden fotar ett kvitto i mobilen | ⬜ | Ett foto av ett syntetiskt kvitto blir ett underlag via läsaren i steg 109 | per grupp | – | 68, 109 |
| 123 | **Utlägg:** den anställde fotar kvittot och markerar utlägg, Kassio bokför skulden till den anställde, ägaren godkänner, och Kassio förbereder återbetalningen. Kassio flyttar aldrig pengar. Eget flöde med sin form (regel 9) | ⬜ | Testfall: utlägget ger skuld till rätt person efter godkännande, återbetalningen är förberedd men inte gjord, och ett utlägg från en ägare blir nivå D | per steg | – | 54, 120, 130 |
| 124 | **Samlingsbetalningar** (Öppet 42, Hugos beslut 2026-11-04 om granskning 29, beslut 7): en bankrad som betalar flera fakturor, som egen form. Stoppas av flödenas former tills dess | ⬜ | En bankrad som betalar flera fakturor får ett förslag i formen, summan stämmer på öret, och delbetalningar stoppas fortfarande | per steg | – | 97, 119 |
| 49 | **Regelförslag från rättelser:** när kunden ändrar en kontering föreslår Kassio en ny regel. Den börjar gälla först när kunden godkänt den. När något nytt dyker upp frågar Kassio "Ska jag göra så här varje gång?" (`KASSIO-KRAV.md`) | ⬜ | En rättelse i testdatan ger ett regelförslag som inte gäller förrän det godkänts | per steg | Puzzle, Ramp, QuickBooks | 33 |

## Fas Pilot 4 – Fortnox, skrivning (grupp 4)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 56 | **Fortnox-koppling, skrivning:** skapa verifikation och ladda upp underlag, bara efter godkännande av veckans utkast (regel 11), med efterkontroll och skydd mot dubbelbokning (samma förslag kan inte skrivas två gånger). Fortnox-nyckeln kan alltid skriva, så spärren ligger i Kassios kod | ⬜ | Spärrtest 1–10 klarade mot testdatabasen, och kedjan i steg 112 går hela vägen in i testdatabasen | per steg | Fortnox API, SPEC 9.4 i den gamla specen (arkivmappen) | 19, 33, 55, 119 |
| 131 | **Rättelse efter överföring:** fel i något som redan förts över till Fortnox. Kassio föreslår en ny verifikation med förklaring, kunden godkänner, och inget raderas | ⬜ | Spärrtest: en rättelse utan godkännande skrivs inte, och originalet finns kvar oförändrat i testdatabasen | per steg | – | 27, 56 |

## Fas Pilot 5 – Godkännandet (grupp 5)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 31 | **Granskaren:** separat agent med bara läsrätt, ser bara underlag, regelbok och förslag. Oenighet = ärende | ⬜ | Testfall där granskaren invänder blir ärende | per steg | SPEC 4 steg 6 | 26 |
| 125 | **Granskat läge, post för post:** kunden godkänner varje post, en i taget, och sedan veckans slututkast. Inget skrivs förrän slututkastet är godkänt (beslut 7) | ⬜ | Testfall: nästa post visas först när den förra är godkänd, och Fortnox är oförändrat tills slututkastet är godkänt | per steg | – | 33, 56 |
| 47 | **Dokumentjakt:** lista över bankrader utan underlag med en färdig fråga till ägaren | ⬜ | Saknade underlag i testdatan listas med fråga | per grupp | Pennylane Autopilot, Fortnox "Begär underlag" | 33 |
| 126 | **Påminnelser som trappas upp:** app, mejl och sms närmare deadline. Inget bokförs utan godkännande, även om deadline missas | ⬜ | Testfall: en missad deadline ger påminnelser i rätt ordning, och inget bokförs | per grupp | – | 68 |

## Fas Pilot 7 – Starten för kunden (grupp 7)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 65 | **Onboarding:** intervju i chatt, import av förra årets SIE-fil, regelförslag från historiken, och en skuggvecka där Kassio föreslår men inget bokförs | ⬜ | Ett nytt testföretag kommer igång utan att kärnan ändras | per grupp | Digits, Ramp, Jolene (8 frågor) | 49, 55 |
| 127 | **De tre frågorna** som slår på funktioner: fakturor, lön, lager eller tillgångar. Kunden kan ändra allt senare | ⬜ | Svaren slår på och av funktioner, och ett testföretag utan lön ser ingen lön | per grupp | – | 65 |
| 128 | **Uppslag på organisationsnummer:** namn, bolagsform, adress, momsregistrering och F-skatt, som kunden bekräftar eller ändrar. Källan är en **Öppen fråga** | ⬜ | Ett organisationsnummer ger uppgifterna från den valda källan, och inget sparas utan kundens bekräftelse | per grupp | – | 65 |
| 129 | **Rundturen,** som går att hoppa över. Frågor som "Hur brukar ni sköta den här delen idag?" blir en del av regelboken, och kunden kan läsa hur allt fungerar | ⬜ | En testkund går igenom eller hoppar över rundturen, och ett svar blir en regel först efter kundens ja | per grupp | – | 49, 127 |
| 66 | **Dataexport vid uppsägning:** allt kunden äger (underlag, logg, regelbok, SIE) kan exporteras | ⬜ | Export av ett testföretag går att läsa in igen | per grupp | Jolene GDPR-export, lärdom från Bench | 35 |

## Fas Pilot 8 – Moms och månaden (grupp 8)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 43 | **Kassaavstämning:** kort- och Swishbelopp i Z-rapporten mot utbetalningar från Zettle, SumUp, Nets och Swish. Avgift bokförs separat, kassadifferens visas, försäljning delas på 6/12/25 % | ⬜ | Testbutiken stämmer på öret. Syntet Krog läggs till när steg 39 är byggt | per grupp | Jolene Z-läsare | 23, 36, 111 |
| 44 | **Momsutkast med förkontroll:** summa per ruta i momsdeklarationen, kontrollerad mot momskontona, varje avvikelse förklarad. Redovisningsperiod (år/kvartal/månad) i konfigurationen | ⬜ | Utkastet för testföretagen stämmer med facit | per steg | Intuit Sales Tax AI, Lundify momskontroll, Jolene | 36 |
| 45 | **Skattekontoavstämning:** skattekontots händelser mot konto 1630. Flaggar ränta, oväntade debiteringar och sena betalningar | ⬜ | Testfall med ränta och sen betalning blir ärenden | per grupp | Talenom, Jolene, Bokio | 36 |
| 46 | **Deadlinekalender per företag:** moms, AGI, INK2, kontrolluppgifter, årsredovisning. Datumen i en datafil med källa, aldrig i koden | ⬜ | Veckorapporten visar nästa tre deadlines för varje testföretag | per grupp | Inkle, Sage | 44 |
| 48 | **Checklista för månadsbokslut** med status "klar för månadsbokslut" | ⬜ | Checklistan granskad en gång av en redovisningskonsult | per grupp | Digits Checklist, Kick | 36, 45 |
| 61 | **Momsdeklaration klar att signera:** Kassio fyller i momsen i Fortnox, kunden granskar förkontrollen och signerar själv med BankID | ⬜ | Testdatabasen visar en ifylld deklaration som inte är inskickad | per steg | Fortnox moms-API, Jolene | 44, 56 |
| 62 | **Månadsrapport med kommentarer:** resultat, balans, nyckeltal och ett kort brev på vanlig svenska om vad som ändrats och varför. Siffrorna från koden | ⬜ | Rapport för testföretagen granskad mot facit | per grupp | Inverso, Intuit Finance Agent, Zeni | 36 |
| 51 | Oberoende granskning av gruppen Moms och månaden (hette fas E) | ⬜ | Inga allvarliga eller medelfynd kvar | är gruppens granskning | – | 43, 46, 48, 61, 62 |

## Fas Pilot 12 – Genrep och start (grupp 12)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 67 | Oberoende granskning av Mål 2 (hette fas F) och spärrtest mot riktiga testdatabaser | ⬜ | Inga allvarliga eller medelfynd kvar | per steg | – | 31, 38, 47, 51, 66, 120, 122, 123, 124, 125, 126, 128, 129, 131 |
| 132 | **Piloten med Fortnox startar** (förslag: 2027-03-01, uppskattning): bokföring, moms och veckoutkast skrivs i pilotkundens Fortnox efter godkännande (beslut 2) | ⬜ | Första veckans godkända utkast är skrivet i pilotkundens Fortnox, och efterkontrollen stämmer med det godkända | per steg | – | 67, 118 |

---

# Under piloten

Byggs i den ordning piloten visar (beslut 2). Ordningen mellan grupperna här är inte bestämd.

## Fas Under 9 – Lön (grupp 9)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 63 | **Lönekontroll ovanpå Fortnox Lön/Bokio Lön:** AGI mot bokföringen, ungdomsrabatten (född 2003–2007, tak 25 000 kr, till 2027-09-30), semesterlöneskuld | ⬜ | Testfall med fel arbetsgivaravgift blir ärende | per steg | Talenom, Skatteverket | 55 |
| 133 | **Lönekörningen:** Kassio räknar ut lönen, skickar lönespecar, förbereder utbetalningen, hanterar semester och frånvaro. Utbetalning den 25:e, eller närmaste vardag före om den 25:e är en helgdag. Kassio flyttar aldrig pengar. **Öppen fråga:** ska lönedagen kunna ändras per företag? | ⬜ | Testlöner stämmer med facit på öret, utbetalningen är förberedd men inte gjord, och reglerna är kontrollerade av en redovisningskonsult | per steg | – | 54, 56, 127 |
| 79 | **AGI-utkast** i Fortnox/Bokio Lön, kunden signerar med BankID | ⬜ | Utkast stämmer med lönekontrollen i steg 63 | per steg | Fortnox, Intuit Workforce | 63 |

## Fas Under 10 – Fakturor (grupp 10)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 60 | **Kontroll av leverantörsfakturor:** tolkning, attestförslag, bedrägerikoll (ändrat bankgiro, dubbletter, ny leverantör, ovanligt belopp). Kassio betalar aldrig | ⬜ | Testfall med ändrat bankgiro blir ärende med hög prioritet | per steg | Xero Bill Protection, Fortnox dubblettfilter | 56 |
| 70 | **Kundfakturor och påminnelser** via Fortnox/Bokio, med OCR och Swish-QR. Kunden godkänner varje utskick i början | ⬜ | Faktura skapad i testdatabasen efter godkännande | per steg | Intuit Payments Agent, Xero Payment Follow Ups | 56 |
| 134 | **Fakturaformuläret:** alla fält i `KASSIO-KRAV.md`, en obruten nummerserie per räkenskapsår, och en snygg faktura som kunden laddar ner eller som Kassio mejlar efter godkännande | ⬜ | En testfaktura har alla fält, numren är en obruten serie, momsen räknas i koden, och inget skickas utan godkännande | per grupp | – | 70 |
| 135 | **Följa fakturan:** tidslinje till betalning, påminnelsefakturor, och inkasso som förbereds och lämnas över. **Öppen fråga till jurist:** inkasso åt andra kräver som regel tillstånd enligt kravlistan | ⬜ | En testfaktura visas som betald, försenad eller klar för inkasso, en påminnelse skickas bara efter godkännande, och inkasso följer juristens svar | per steg | – | 53, 134 |

## Fas Under 11 – Bokslut (grupp 11)

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 72 | **Anläggningsregister och avskrivningsplaner** | ⬜ | Planerna föreslås och bokförs månadsvis efter ett godkännande | per steg | Digits Schedules, Fortnox | 56 |
| 73 | **Periodiseringar:** förutbetalda kostnader och upplupna kostnader som vänds nästa månad | ⬜ | Testfallen med hyra och försäkring (D10) stämmer | per grupp | Ramp, Digits | 54, 72 |
| 136 | **Varulager och lager per artikel** | ⬜ | Lagret i testdatan stämmer med facit, och reglerna är kontrollerade av en redovisningskonsult | per grupp | – | 54, 72 |
| 76 | **Förgranskning av bokslutet:** checklista, periodiseringar, avskrivningar, lagervärde, semesterlöneskuld, skatteberäkning. Allt nivå D | ⬜ | En redovisningskonsult har granskat reglerna | per grupp | Pennylane Autopilot, Kick | 54, 73, 136 |
| 77 | **K2-årsredovisning, utkast** med noter, förvaltningsberättelse och alla avstämningar bifogade. Inlämning via Fortnox/Spiris, styrelsen signerar | ⬜ | Utkast för ett testföretag granskat av en revisor | per grupp | Fortnox Bokslut & Skatt, Spiris | 76 |
| 137 | **Årsstämmoprotokoll:** Kassio förbereder, kunden godkänner och skriver under | ⬜ | Utkast för ett testföretag granskat av en redovisningskonsult eller jurist | per grupp | – | 77 |
| 78 | **INK2 och K10** enligt 3:12-reglerna från 2026. INK2:s e-tjänst stängs 2026-12-29, så det går via API eller SRU-fil | ⬜ | Utkast för ett testföretag granskat av en redovisningskonsult | per grupp | Jolene, Spiris | 77 |

## Fas Under 12 – Resten av kraven

| # | Steg | Status | Klart när | Granskas | Lånat från | Beror på |
|---|---|---|---|---|---|---|
| 138 | **Köp från utlandet och valutor:** utländska leverantörer, omräkning till kronor och rätt moms. Reglerna kontrolleras av en redovisningskonsult, och inget gissas | ⬜ | Testfall i utländsk valuta stämmer med facit på öret | per grupp | – | 54 |
| 64 | **Kassaregistrets XML-export** (krav från 2027-01-01) som källa vid sidan av Z-rapporten | ⬜ | En XML-fil i testdatan läses och stämmer med Z-rapporten | per grupp | SKVFS 2021:17 | 23 |
| 69 | **Revisor- eller konsultåtkomst** med bara läsrätt och tidsgräns | ⬜ | Revisorn ser allt men kan inte godkänna | per steg | Spiris, Bokio Byrå | 68 |
| 74 | **Likviditetsprognos och skattereserv:** pengar om 4–13 veckor, och vad som ska läggas undan till moms och skatt. Osäkerheten visas | ⬜ | Prognos för testföretagen med förklaring | per grupp | Xero Cash Flow Actions, Pilot, Accountable | 110 |
| 75 | **Chatt "fråga dina böcker":** svaren räknas i koden, och uträkningen visas. Bifogade filer och föreslagna frågor enligt `KASSIO-KRAV.md`. Ingen mikrofon i första versionen | ⬜ | 20 testfrågor besvaras rätt mot facit | per grupp | Jolene "Fråga Jolene", Zeni, Xero JAX | 68 |
| 141 | **Kassio säger nej:** till något olagligt, till exempel att dölja intäkter. Tunga skatte- och juridikfrågor förklaras, och kunden hänvisas till revisor eller jurist | ⬜ | Testfrågor om att dölja intäkter ger ett nej med förklaring och inget förslag | per grupp | – | 53, 75 |
| 140 | **Startsidan:** att-göra-lista, tidslinje med deadlines, vad Kassio gjort och nyckeltal som kunden anpassar. Ton och utseende enligt `KASSIO-KRAV.md` | ⬜ | En testkund ser alla delarna och väljer nyckeltal, och siffrorna räknas i koden | per grupp | – | 46, 68 |
| 50 | **Automatiseringsgrad per motpart:** andel godkända utan ändring visas, och en motpart kan flyttas till nivå A först efter X veckor utan rättelser. Mäter också målet 90 % i `KASSIO-KRAV.md` | ⬜ | Värdet räknas från loggen, inte gissas | per grupp | Ramp, Vic.ai (stegvis autonomi) | 35, 49 |
| 139 | **Kryptering och arkivet:** så mycket som möjligt krypteras, bara kunden och agenten kan läsa kundens dokument, och kunden väljer vid avslut: exportera, radera eller spara mot en avgift. **Öppen fråga:** hur Anthropic hanterar datan måste kontrolleras innan löftet formuleras | ⬜ | Hur Anthropic hanterar datan är kontrollerat och skrivet, löftet är godkänt av jurist, och ett prov visar att personalen inte kan läsa ett dokument | per steg | – | 53, 66, 114 |
| 83 | Oberoende granskning av det som byggs under piloten (hette fas G) | ⬜ | Inga allvarliga eller medelfynd kvar | är gruppens granskning | – | 50, 64, 69, 74, 78, 79, 133, 135, 137, 138, 139, 140, 141 |

---

# Efter piloten

Allt här väntar till efter piloten, och skälet står på varje rad. Inget steg är borttaget.

## Fas Väntar – Caspers dator

| # | Steg | Status | Klart när | Granskas | Varför det väntar | Beror på |
|---|---|---|---|---|---|---|
| 14 | Samma installation och kontroll på Caspers dator (`/Library/Python` kontrolleras för hand först, K1 granskning 20) | ⬜ väntar på en ny dator | Samma resultat som steg 13. Tidigare planerad till helgen vecka 44 (PROGRESS.md, Öppet 15). Casper installerar den nya inställningsfilen utan `disableAutoMode` (Hugos beslut 2026-10-29, "Beslut 2026-10-29 – Auto tillåts igen"), med summan i INSTALLERA.md steg 5. Läget "auto" används på Caspers dator först när steg 8 i kontrollen är gjort där | per steg | Väntar på en ny dator, inte på piloten. Casper behöver bara webbappen i piloten (Hugos beslut 2026-11-04 om planen, beslut 13). Han kör inga sessioner i projektet före installationen (Öppet 15) | 13 |

## Fas Efter 1 – Fler testföretag och demo (gamla fas D)

| # | Steg | Status | Klart när | Granskas | Varför det väntar | Beror på |
|---|---|---|---|---|---|---|
| 39 | **Syntet Krog AB:** testföretag och testdata (mat 6/12 %, alkohol 25 %, personal, dricks) | ⬜ | Kärnan oförändrad, rapport stämmer med facit | per grupp | Beslut 11: ersätts före piloten av ett syntetiskt nystartat aktiebolag | 38 |
| 40 | **Syntet Bygg AB:** testföretag och testdata (omvänd byggmoms, material, underentreprenörer, ROT) | ⬜ | Kärnan oförändrad, rapport stämmer med facit | per grupp | Samma som steg 39 | 39 |
| 41 | **Automatiskt läge simulerat:** inkorg som fylls som om bank och mejl vore kopplade | ⬜ | Båda lägena går hela vägen på alla tre företag | per grupp | Riktiga kopplingar och riktig data testar mer | 40 |
| 42 | Oberoende granskning av fas D, sedan demo (SPEC fas 4) | ⬜ | Demo visad för minst en investerare eller kund | är gruppens granskning | Ingen demo krävs för piloten | 41 |

## Fas Efter 2 – Fler kopplingar

| # | Steg | Status | Klart när | Granskas | Varför det väntar | Lånat från | Beror på |
|---|---|---|---|---|---|---|---|
| 34 | **Bokföringssteget v1: SIE-export** av godkända verifikationer, med efterkontroll av filen | ⬜ | SIE-filen importeras i Fortnox testdatabas och stämmer med det godkända | per steg | Fortnox skrivs direkt. Kan bli en reserv om kopplingen dröjer | SPEC 2.1 | 33 |
| 57 | **Bokio-koppling,** samma som 55–56 | ⬜ | Samma spärrtester mot Bokios testmiljö | per steg | Bara Fortnox vid lansering | Bokio API | 56 |
| 80 | **Spiris-koppling** (tredje programmet) | ⬜ | Samma spärrtester som 56 | per steg | Bara Fortnox vid lansering | Spiris API, MCP | 57 |
| 58 | **Bank via Fortnox/Bokio** i automatiskt läge: läs de transaktioner som programmet redan hämtat. Bara läsning | ⬜ | Automatiskt läge körs utan uppladdad bankfil | per grupp | Beslut 8: kontoutdrag laddas upp i piloten | Fortnox bankkoppling, Jolene | 55 |
| 143 | **Mejlkopplingen:** digitala kvitton hämtas automatiskt från företagsmejlen, bara med läsrätt och i karantän | ⬜ | Spärrtest: ett mejl med dolda instruktioner blir ärende, och Kassio kan inte skicka eller ändra mejl | per steg | Beslut 8: vidarebefordran räcker i piloten | – | 59 |
| 144 | **Bankkoppling med BankID** som bara kan läsa: de stora svenska bankerna, flera konton per företag. **Öppen fråga till jurist:** kan kräva tillstånd eller en leverantör som har det | ⬜ | Transaktioner från en testbank stämmer med kontoutdraget, och kopplingen kan inte flytta pengar | per steg | Beslut 8: BankID-koppling kommer senare | – | 53, 110 |
| 145 | **Inlämning till Skatteverket** efter att kunden signerat med BankID | ⬜ | Spärrtest: inget lämnas in utan kundens signering | per steg | I början förbereder Kassio och kunden lämnar in själv | – | 53, 61 |
| 82 | **Eget Skatteverket-avtal som ombud** för moms och AGI, så att Kassio inte behöver gå via Fortnox. Kräver att Kassio Labs har F-skatt, moms- och arbetsgivarregistrering och inga skatteskulder | ⬜ | Avtal tecknat, spärrtest klarat | per steg | Går via Fortnox så länge det räcker | Jolene (ombud + BankID) | 53, 61, 79 |

## Fas Efter 3 – Andra kunder

| # | Steg | Status | Klart när | Granskas | Varför det väntar | Lånat från | Beror på |
|---|---|---|---|---|---|---|---|
| 71 | **ROT/RUT** för hantverkare (Syntet Bygg AB) | ⬜ | ROT-faktura och begäran förberedd, kunden signerar | per grupp | Hantverkare är inte målgruppen i piloten | Fortnox, Bokio | 40, 70 |
| 81 | **Enskild firma** som ny konfiguration (NE-bilaga) | ⬜ | Kärnan oförändrad | per grupp | Bara aktiebolag i version 1 | Jolene, Bokio | 78 |

## Fas Efter 4 – Appen, försäljningen och repot

| # | Steg | Status | Klart när | Granskas | Varför det väntar | Beror på |
|---|---|---|---|---|---|---|
| 142 | **Mobilappen.** När den byggs är en öppen fråga i `KASSIO-KRAV.md` | ⬜ | En testkund godkänner en vecka i mobilappen, och spärrtesterna är gröna | per steg | Beslut 9: webbappen räcker i piloten | 68 |
| 146 | **Flera bolag:** bolagsväljare, "Lägg till företag" i tre steg, och "Hantera företag" | ⬜ | En testkund byter bolag, lägger till ett bolag och ser aldrig ett annat bolags uppgifter | per steg | Piloten har ett bolag | 68 |
| 147 | **Köp på hemsidan:** 999 kr/mån eller 2 997 kr/kvartal, första månaden återbetalas om kunden avslutar under den, sedan 30 dagars uppsägning. **Öppen fråga:** inklusive eller exklusive moms | ⬜ | Ett testköp går igenom, återbetalningen fungerar, och momsfrågan är beslutad | per grupp | Piloten är gratis | 53 |
| 148 | **Repot byter namn** (beslut 12) | ⬜ | Repot har det nya namnet, och vakten och testsviten fungerar efteråt | per grupp | Beslut 12: inte bråttom | 104 |

## Fas Efter 5 – Lite till: det ingen konkurrent gör i dag (gamla fas H)

| # | Steg | Status | Varför det är unikt | Granskas | Varför det väntar | Beror på |
|---|---|---|---|---|---|---|
| 84 | **Regelboken på vanlig svenska:** kunden skriver "Snabbgross är varuinköp, ofta två momssatser", Kassio gör om det till en regel och ett test som kunden godkänner | ⬜ | Ingen svensk aktör låter kunden äga en läsbar regelbok. Digits gör det bara för kontroller | per steg | Efter piloten: rundturens frågor räcker till dess | 49 |
| 85 | **Kassabutikspaketet:** Z-rapport, kortinlösen, Swish, kassadifferens, tre momssatser och XML-export i ett flöde | ⬜ | De billigaste byråerna tar inte kunder med kontanthantering, och ingen programvara gör hela kedjan | per grupp | Efter piloten: delarna finns i steg 23, 43 och 64 | 43, 64 |
| 86 | **Årsredovisning som styrelsen förstår:** varje post i utkastet har en förklaring på vanlig svenska och en länk till underlagen | ⬜ | Ingen i världen automatiserar årsredovisningen helt, och ingen förklarar den | per grupp | Kräver steg 77 och ett riktigt bokslut | 77 |
| 87 | **Revisorspaketet:** ett klick ger hela spårbarhetskedjan, alla kontroller och alla godkännanden för ett år | ⬜ | Gör revisionen billigare för kunden, och är ett säljargument mot byrån | per grupp | Kräver ett helt år | 35, 77 |
| 88 | **Branschnyckeltal:** jämför kundens marginal, personalkostnad och svinn med andra i samma bransch (anonymt, först när det finns tillräckligt många kunder) | ⬜ | Byråer gör det sällan för små företag | per grupp | Kräver många kunder | 62, 68 |
| 89 | **Nya branscher som konfiguration:** e-handel, frisör, konsult, skapare | ⬜ | Samma kärna, nya regelböcker | per grupp | Målgruppen är nystartade aktiebolag | 81 |
| 90 | **Fler agenter på samma kärna:** strategikonsulten, trendövervakaren, leverantörsagenten | ⬜ | Del av Kassio Labs plan, efter bokföringsagenten | per grupp | Efter bokföringsagenten | 83 |

---

## Datum att bevaka

| Datum | Vad | Steg |
|---|---|---|
| 2026-12-29 | Skatteverkets e-tjänst för INK2 stängs | 78 |
| 2027-01-01 | Kassaregister måste kunna exportera journalminnet som XML | 64 |
| 2027-01-11 | Skuggpiloten, förslag (uppskattning) | 118 |
| 2027-03-01 | Piloten med Fortnox, förslag (uppskattning) | 132 |
| 2027-09-30 | Sänkta arbetsgivaravgifter för unga upphör | 63 |
| 2027-12-31 | Sänkt matmoms (6 %) upphör | 43, 44 |
| 2027 | Första K10 enligt de nya 3:12-reglerna | 78 |
