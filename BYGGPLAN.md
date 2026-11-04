# BYGGPLAN – Vera, från referensprodukt till en hel byrå

Skapad 2026-10-29. Utgår från `PROGRESS.md` (2026-10-28, 4 076 gröna tester), `SPEC.md`, `DESIGN-regelbok.md`
avsnitt 7 och två researchrapporter från 2026-10-29: "Så kan Vera bli en bättre agent" och "Byråtjänster Vera saknar".

**Rättad 2026-10-29 efter PROGRESS.md:** status för steg 12–21 och beroendet för steg 22 (Hugos beslut 2026-10-29,
B1, `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4").

**Målet:** Vera ska kunna göra i princip allt som Jolene, Fortnox, Bokio, Spiris, Wint och Lennart redan gör åt
ett litet aktiebolag, plus några saker som ingen av dem gör. Det enda Vera aldrig gör är att betala, skriva under
eller lämna in något utan att en människa hos kunden har godkänt och signerat.

**Så används planen:**

- Ett steg är en Claude Code-session. Stora steg delas upp i flera sessioner, och då står det i steget.
- Varje steg avslutas med full testsvit och slutrapportrutan (STATUS, KAN JAG GÅ VIDARE, beslut, nästa steg).
- Efter varje fas görs en oberoende granskning i en ny session innan nästa fas börjar.
- Ett steg får inte börja förrän stegen det beror på är klara. Säkerhetsstegen i fas B går alltid före, med ett
  undantag: steg 22 (uppgift 4) får byggas före steg 15–19 (Hugos beslut 2026-10-29, B1, se fas C).
- Där det står **Beslut** måste Hugo (eller en redovisningskonsult) svara innan steget byggs.
- Statusen uppdateras här och i `PROGRESS.md` när ett steg blir klart.

Status: ✅ klart · 🔶 pågår · ⬜ inte påbörjat

## Läge nu

- **Uppdaterad:** 2026-11-04
- **Pågående steg:** inget steg pågår just nu. Nästa att börja: 96 – Öppet 37 (beslutad 2026-11-04, inte påbörjad), 15 – Sandlådan (inte påbörjad, ska vara klar före steg 23), och 14 – Caspers dator (planerad helgen vecka 44)
- **Senast avslutade steg:** 95 – Öppet 36 (klart 2026-11-04: varje rad med ett underlags `belopp_ore` i debet har en egen rad på bankkontot i kredit med samma belopp ur en bankrad, och varje bankkontorad räknas bara en gång; annars stoppas förslaget. Byggt efter Hugos beslut 2026-11-04 om granskning 28, beslut 1, granskarens (a), committat 2026-11-04 i 0708667. Granskarens b1 och b3 stoppas; b2 godtas, eftersom konteringen är identisk med flöde a:s två förslag i samma förslag, Hugos beslut 2026-11-04 i chatten, Öppet 38 för redovisningskonsulten. Granskad i granskning 29, gult: byggd som beslutet säger, utom att flera bankrader godtas där beslutet säger en, P3; ett nytt hål i familjen, en bankrad som källa på kostnadskontot, Öppet 39, så att (b) ska byggas enligt Hugos beslut; väntar på besked). Före det: 94 – Öppet 35 (klart 2026-10-31, granskat och klart enligt Hugos beslut 2026-11-04 om granskning 28, beslut 3: i ett förslag med underlag står underlagets `belopp_ore` i debet bara när förslaget har en bankrad, och i kredit bara när underlagets `underlag_ore` och `moms_ore` inte står i kredit; annars stoppas förslaget. Byggt efter Hugos beslut 2026-10-31 om granskning 27, committat 2026-10-31 i 109fdcf och granskat i granskning 28, gult: byggt som beslutet säger ordagrant, h1 och h2 stoppas; kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en bankrad som inte hör till underlaget, Öppet 36, byggd som steg 95; ett underlag med belopp 0 stannar hela körningen, Öppet 37, steg 96). Före det: 93 – Öppet 33 och Öppet 34 (klart 2026-10-30: momsraden i ett förslag med underlag står på kontot för ingående moms, beloppet att betala räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad, och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`; annars stoppas förslaget. Byggt efter Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg", committat 2026-10-30 i 7801a64 och granskat i granskning 27, gult: byggt som beslutet säger, alla prov från granskning 26 stoppas, två hål kvar i en ny familj, Öppet 35, väntar på beslut; regeln om högst en rad beslutad av Hugo 2026-10-31). Före det: 91 – Öppet 32 (klart 2026-10-30: kostnadsraden i ett förslag med underlag står på det konto K5 ger för momssatsen, annars stoppas förslaget; byggd efter Hugos beslut 2026-10-30 om granskning 25, beslut 1, committad 2026-10-30 i c479915 och granskad i granskning 26, gult: byggd som beslutet säger, ett hål kvar i samma familj som Öppet 34, väntar på beslut). Öppet 32 och Öppet 26 fick egna stegnummer, 91 och 92, de nästa lediga (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b, `GRANSKNING.md`). Före det: 22 – Uppgift 4, flöde a, b och e (klart 2026-10-30 efter granskning 24, Hugos beslut 2026-10-30 om granskning 24, beslut 3). Granskad i granskning 22, 23 och 24. Öppet 31 (P5 i granskning 24) rättad i bbb183a, granskad i granskning 25 (grönt) och klar (Hugos beslut 2026-10-30 om granskning 25, beslut 2)
- **Nästa steg:** Hugos eller Caspers besked om granskning 29, "Beslut som behövs" (framför allt hur (b) ska byggas och vad som då gäller b2; Öppet 39 ska vara stängd före steg 23). Steg 96 (Öppet 37, underlag med belopp 0 blir ett ärende, resten av perioden fortsätter; Hugos beslut 2026-11-04 om granskning 28, beslut 2). Steg 92 (Öppet 26, konton för hyra, el och telefon). Öppet 38 (faktura och annan fakturas betalning i samma förslag) till en redovisningskonsult. Steg 15 (sandlådan) ska vara klar före steg 23 (uppgift 5). Steg 14 (Caspers dator) i helgen vecka 44
- **Opushat:** ja: d5b2fba (P1 och P2 efter granskning 22), 269d641 (granskning 23), 13126d2 och 35afa8b (rättelserna efter granskning 23), aecccdf (dokumentationen), 6dfcdcd (granskning 24), bbb183a (Öppet 31), 277ca90 (dokumentationen), 7c1f148 (granskning 25), c479915 (Öppet 32: kod, test och SPEC), d1ab489 (dokumentationen), 994bcdf (granskning 26), 5b4aa83 (Hugos beslut om granskning 26), 7801a64 (steg 93, Öppet 33 och 34: kod, test och SPEC), 68e86bb (dokumentationen), granskning 27 (2026-10-31), 109fdcf (steg 94, Öppet 35: kod och test), f10c65b (dokumentationen), granskning 28 (2026-11-04), 0708667 (steg 95, Öppet 36: kod och test), 2418288 (dokumentationen) och granskning 29 (2026-11-04). `main` på GitHub står på 7d8cae9

---

## Regler som gäller i hela planen

1. **Godkännande före allt.** Inget bokförs, skickas eller lämnas in innan en människa hos kunden har godkänt
   just det innehållet. Godkännandet är låst till förslagets kontrollsumma (hash).
2. **Vera betalar aldrig.** Betalningar görs alltid av kunden i banken med BankID.
3. **Vera signerar aldrig.** Deklarationer och årsredovisning förbereds av Vera och signeras av kunden.
4. **Koden räknar, modellen förklarar.** Alla belopp, summor, moms och avstämningar räknas i Python. Modellen
   tolkar underlag, väljer regel och skriver förklaringar.
5. **Kärnan är gemensam.** Allt företagsspecifikt ligger i `foretag/<namn>/`. Testet att kärnan är generell
   utökas i varje steg som lägger till något.
6. **Ny datakälla = ny läsare i karantän.** Allt som kommer utifrån (mejl, PDF, bankdata, API-svar) läses av
   en del som inte kan skriva eller nå nätverket. K17 körs på allt.
7. **Spärrarna läser aldrig från en mapp agenten kan skriva i.**
8. **Inga riktiga kunduppgifter i repot.** Allt byggs på syntetiska testföretag.

---

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

## Fas B – Säkerhetsgrunden (pågår, går före allt annat utom steg 22, se B1)

| # | Steg | Status | Klart när | Beror på |
|---|---|---|---|---|
| 12 | **Hugo installerar vakten** enligt `sparr/INSTALLERA.md` | ✅ 2026-10-29 | Den nya filen utan `disableAutoMode` (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen") är installerad med steg 10–13, och kontrollen steg 1, 2, 3 och 9 är gjord igen, med läget "auto" valbart i steg 1 (INSTALLERA.md, "Byte av inställningsfil"). Gjort och grönt på Hugos dator 2026-10-29 (`GRANSKNING.md`, "Kontroll efter bytet av inställningsfil, 2026-10-29"). Första installationen: `/status` visar `Enterprise managed settings (file)` och vakten stoppar `date` i skrivbordsappen. Gjort på Hugos dator 2026-10-28 (`GRANSKNING.md`, "Installation på Hugos dator 2026-10-28"). Caspers dator är steg 14 | 11 |
| 13 | Kontrollen efter installationen, i en ny session (sist i INSTALLERA.md), inklusive provet med en vakt som fallerar | ✅ 2026-10-29 | Alla steg i kontrollen visar väntat svar. Steg 1–7 och 9 gjorda vid installationen, och spärrtestet 2026-10-29 är grönt. Steg 8 (provet med en vakt som fallerar) och steg 9 igen efter det är gjorda och gröna 2026-10-29, med samma kontrollsummor (`GRANSKNING.md`, "Steg 8, provet med en vakt som fallerar, 2026-10-29", PROGRESS.md, Öppet 16 stängd) | 12 |
| 14 | Samma installation och kontroll på Caspers dator (`/Library/Python` kontrolleras för hand först, K1 granskning 20) | ⬜ | Samma resultat som steg 13. Planerad till helgen vecka 44 (PROGRESS.md, Öppet 15). Casper installerar den nya inställningsfilen utan `disableAutoMode` (Hugos beslut 2026-10-29, "Beslut 2026-10-29 – Auto tillåts igen"), med summan i INSTALLERA.md steg 5. Läget "auto" används på Caspers dator först när steg 8 i kontrollen är gjort där | 13 |
| 15 | **Sandlådan** (Öppet 4 och 8): skrivning bara i tillåtna mappar, förbud för appen, appens Claude Code och `~/.local/share/claude`, täcker `trap`, `hash` och `builtin`. Ska vara klar före steg 23 (uppgift 5), eller före första körningen på riktiga underlag om den kommer först (Hugos beslut 2026-10-28 och 2026-10-29, B1) | ⬜ | Spärrtest: en egen testfil som försöker skriva utanför projektet stoppas | 13 |
| 16 | Bash-vägen prövas i skrivbordsappen (Öppet 7) | ⬜ | Beslut skrivet: bash eller zsh | 15 |
| 17 | Omvägarna förbi vakten med kommandotexter i en kopia (granskning 13, P5) | ⬜ | Inga omvägar hittade, eller rättade | 15 |
| 18 | Nästa version av vakten: `-I -S` (K1) och tom `cwd` (K3) från granskning 20 | ⬜ | Tester gröna, ny granskning | 17 |
| 19 | Spärrtest i en ny session | ⬜ | Alla spärrtester blockeras och syns i loggen. (Ett första spärrtest efter installationen gjordes 2026-10-29 och är grönt, men det här steget är spärrtestet efter steg 15–18) | 15–18 |
| 20 | Q3 + Q4 + Q2: gemensam ordindelning, kommentaren i `las_regelbok.py`, ägarnamn utan accenter | ✅ | Tester gröna. Q2, Q2b, Q3 och Q4 klara (3e3c18c, d7d38e0, 1dcf769, bd851ba, 2bc9762) och granskade i granskning 21 (3bbcbe4, grön). Byggt före steg 19 | 19 |
| 21 | Q7: pusha som det är (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd"). Historiken skrivs inte om, och ingen tagg byts eller pushas (taggen `v0-shop-and-go` finns inte i repot) | ✅ | Repot på GitHub är privat (kontrollerat av Hugo 2026-10-29). Repot får inte göras publikt utan en ny genomgång av hela historiken först. Q7 stängd och pushat 2026-10-29 (`main` i fas med GitHub vid 6aba32d) | 20 |

---

## Fas C – Version 1 av kärnan, ett testföretag hela vägen (SPEC fas 0)

| # | Steg | Status | Klart när | Lånat från | Beror på |
|---|---|---|---|---|---|
| 22 | **Uppgift 4:** flöde a, b och e (leverantörsfakturor, kvitton, bankavgifter) med K5 och K8. Byggs på syntetisk data, med vakten installerad och Claude Code i det läge som frågar (inte Auto) tills provet med en fallerande vakt (Öppet 16) är gjort. Förutsättningar: B2 och B3 i `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4". **Beslut:** D13 (moms på bankavgifter, bankraden som underlag) och vad "bankens datum" i D14 betyder är beslutade för testföretaget (Hugos beslut i chatten 2026-10-29, `GRANSKNING.md`, "D13 och D14 beslutade") | ✅ 2026-10-30. Byggd 2026-10-29 och granskad i granskning 22 (e4d8cd7, gult), 23 (269d641, gult) och 24 (6dfcdcd, grönt). P1 och P2 rättade 2026-10-30 (d5b2fba), P1 och P3 från granskning 23 rättade och Öppet 29 stängd (13126d2, 35afa8b). Klart efter granskning 24 (Hugos beslut 2026-10-30 om granskning 24, beslut 3). Öppet 31 från granskning 24 rättad i bbb183a, granskad i granskning 25 (grönt) och klar (Hugos beslut 2026-10-30 om granskning 25, beslut 2). Öppet 32 (granskning 25, P7) är steg 91 och Öppet 26 steg 92 (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b) | Testerna i DESIGN 7, rad 4, är gröna | – | 12, 20, 21. Beror inte på steg 15 (Hugos beslut 2026-10-29, B1) |
| 91 | **Öppet 32** (granskning 25, P7): kostnadsraden i ett förslag med underlag står på det konto K5 räknar fram för underlagets momssats, annars stoppas förslaget i `skapa_konteringsforslag` (`_kontrollera_underlagen`). Också ett annat konto i regeln och ett rollkonto som leverantörsskulderna stoppar. Eget steg före steg 23, med nästa lediga nummer (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b, `GRANSKNING.md`). Momsraden (`moms_ore`) ingår inte: den är Öppet 33, ett eget steg efter det här (samma beslut, a) | ✅ 2026-10-30. Byggd efter Hugos beslut 2026-10-30 om granskning 25 (beslut 1), testerna i `scripts/tests/test_beslut_granskning_25.py` röda före (5 av 14 mot 7c1f148). Committad 2026-10-30 i c479915 (PROGRESS.md, "Läge 2026-10-30, Öppet 32 rättad"). Granskad i granskning 26 (gult: byggd som beslutet säger, granskarens två prov stoppas; ett hål kvar i samma familj, Öppet 34, eget beslut) | Granskarens två prov från P7 stoppas, och flöde a, b och e går igenom med varje kostnadsrad på kontot K5 ger | – | 22 |
| 92 | **Öppet 26:** kontona 5010 Lokalhyra, 5020 El för belysning och 6210 Telekommunikation i testbutikens kontoplan, med en ny titt på B3:s D2, och sedan regler för HYRESVARD (nivå D), LEV-EL och LEV-TELE (PROGRESS.md, Öppet 26, Hugos besked i chatten 2026-10-29). Eget steg med nästa lediga nummer (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, b). **Beslut:** D10 och D11 är öppna | ⬜ | Underlagen från de tre motparterna får förslag i stället för ärendet "ny motpart", och kärnan är oförändrad | – | 22 |
| 93 | **Öppet 33 och Öppet 34** i samma steg (Hugos beslut 2026-10-30 om granskning 26, "Ja, i samma steg", `GRANSKNING.md`). Öppet 33: varje rad i ett förslag med ett underlags `moms_ore` som källa står på kontot för ingående moms (rollen i kontoplanen), annars stoppas förslaget (Hugos beslut 2026-10-30 om byggsessionen för Öppet 32, a). Öppet 34 (granskning 26, M1): en rad med ett underlags `belopp_ore` som källa räknas bara med `lika`, står bara på leverantörsskulderna och på högst en rad i förslaget (det sista är byggsessionens tillägg, för granskarens fjärde prov), och `underlag_ore` och `moms_ore` räknas aldrig med `skillnad`. Båda i `skapa_konteringsforslag` (`_kontrollera_underlagen`), efter Öppet 32. Docstringen om momsraden rättad (granskning 26, L1) | ✅ 2026-10-30. Byggd i 7801a64 (PROGRESS.md, "Läge 2026-10-30, Öppet 33 och 34 byggda"), testerna i `scripts/tests/test_beslut_granskning_26.py` röda före (12 av 22 mot `git archive` av 5b4aa83). Granskad i granskning 27 (gult: byggd som beslutet säger, H7 och de fyra LUCKA-proven stoppas; två hål i en ny familj, beloppet i debet utan bankrad, Öppet 35, eget beslut). Regeln om högst en rad beslutad av Hugo 2026-10-31 | Granskarens prov H7 och de fyra LUCKA-proven från granskning 26 stoppas, och flöde a, b och e går igenom | – | 91 |
| 94 | **Öppet 35** (granskning 27, M1, Hugos beslut 2026-10-31 om granskning 27: "Beloppet i debet ska kräva en bankrad. belopp_ore får bara stå i kredit när delarna inte gör det."). I ett förslag med underlag står underlagets `belopp_ore` i debet bara när förslaget har minst en bankrad, och i kredit bara när underlagets `underlag_ore` och `moms_ore` inte står i kredit. I `skapa_konteringsforslag` (`_kontrollera_underlagen`, ny delkontroll `_kontrollera_beloppssidan`), sist efter Öppet 33 | ✅ 2026-10-31. Byggd i 109fdcf (PROGRESS.md, "Läge 2026-10-31, Öppet 35 byggd"), testerna i `scripts/tests/test_beslut_granskning_27.py` röda före (5 av 13 mot koden i b7d9fac). Granskad i granskning 28 (gult: byggd som beslutet säger ordagrant, h1 och h2 stoppas, "rött före" upprepat mot `git archive` av b7d9fac; kravet på bankrad gäller per förslag, inte per underlag, så h1 och h2 går igenom ihop med en bankrad som inte hör till underlaget, Öppet 36, eget beslut; ett underlag med belopp 0 stannar hela körningen, Öppet 37, utanför steget). Granskat och klart (Hugos beslut 2026-11-04 om granskning 28, beslut 3). Öppet 36 är steg 95 och Öppet 37 steg 96 | Granskarens prov h1 och h2 från granskning 27 stoppas, och flöde a, b och e går igenom | – | 93 |
| 95 | **Öppet 36** (granskning 28, M1, Hugos beslut 2026-11-04 om granskning 28, beslut 1, granskarens (a)): för varje rad med ett underlags `belopp_ore` i debet ska förslaget ha en egen rad på bankkontot (rollen `bank` i kontoplanen) i kredit, med samma belopp och med en bankrad som källa, och varje bankkontorad räknas bara en gång. I `skapa_konteringsforslag` (`_kontrollera_beloppssidan`, grenen för debet, efter Öppet 35:s krav på någon bankrad alls). Hittar nästa granskning ett nytt hål i familjen Öppet 31–36 går vi över till (b), flödenas former rakt av | ✅ 2026-11-04. Byggd i 0708667 (PROGRESS.md, "Läge 2026-11-04, Öppet 36 byggd"), testerna i `scripts/tests/test_beslut_granskning_28.py` röda före (4 av 9 mot koden i 3f36f6b). Granskarens b1 och b3 stoppas. b2 godtas: konteringen är identisk med flöde a:s två förslag i samma förslag (Hugos beslut 2026-11-04 i chatten, inte ett nytt hål; Öppet 38 för redovisningskonsulten). Granskad i granskning 29 (gult: byggd som beslutet säger, utom att flera bankrader godtas där beslutet säger en, P3; rött före 4 av 9 upprepat mot `git archive` av 3f36f6b; parningen ger samma utfall i alla radordningar; ett nytt hål i familjen, en bankrad som källa på kostnadskontot, Öppet 39, så att (b) ska byggas enligt Hugos beslut, väntar på besked) | Granskarens prov b1 och b3 från granskning 28 stoppas, två belopp i debet delar inte en bankkontorad, och flöde a, b och e går igenom | – | 94 |
| 96 | **Öppet 37** (granskning 28, M2, Hugos beslut 2026-11-04 om granskning 28, beslut 2): ett underlag med `belopp_ore` 0 ska bli ett ärende för just det underlaget, och resten av perioden ska fortsätta. I dag läses underlaget in utan anmärkning, flöde a bygger en faktura med en rad, K2 stoppar och felet går upp genom `kontera_period`, så hela körningen stannar utan ärende. Eget steg, inte en del av steg 95 | ⬜ | Ett underlag med belopp 0 i en kopia av testdatan ger ett ärende för det underlaget, och de andra underlagen i perioden får förslag som förut | – | 94 |
| 23 | **Uppgift 5:** flöde c och d (Z-rapporter, kortinlösen, Swish, kontantinsättningar) och M9 | ⬜ | Försäljning per sats och månad stämmer på öret med `facit.json` | Jolene (Z-nummerserien, bokför aldrig dagskassa utan kontroll) | 15, 22 |
| 24 | **Uppgift 6:** nivåerna A–D och K9, nivå D för ägarens bankrader | ⬜ | Varje skäl ger rätt nivå. Högsta nivån vinner | – | 23 |
| 25 | Oberoende granskning av uppgift 4–6 | ⬜ | Inga allvarliga eller medelfynd kvar | – | 24 |
| 26 | **Ursprungsmärkning och "varför":** varje förslag märks *regel*, *exakt matchning*, *tidigare godkänd* eller *modellens förslag*, plus en rad "varför" som namnger regel-id | ⬜ | Varje förslag i testdatan har märkning och förklaring | Xero (Match/Rule/Memory/Prediction), Ramp | 24 |
| 27 | **K6 rätt period** och **låsta perioder:** en stängd månad kan bara ändras med motverifikation och nytt godkännande | ⬜ | Spärrtest: förslag i stängd period stoppas | Digits Locked Periods | 24 |
| 28 | **K17 instruktioner i underlag** (Ö10) | ⬜ | Spärrtest: kvitto med "ignorera reglerna" blir ärende, inget förslag | OWASP, Willison | 24 |
| 29 | **K4 mot arkivet** (Ö9), **bankens avgiftsspecifikation** (Ö11), **kreditnotor** (Ö8) | ⬜ | Tester gröna | – | 24 |
| 30 | **Godkända kontrollsummor** (Ö12): regelbok, kontoplan och momsfil jämförs mot godkänd summa i skyddad mapp | ⬜ | Spärrtest "ändrad regelbok" stoppas | – | 19 |
| 31 | **Granskaren:** separat agent med bara läsrätt, ser bara underlag, regelbok och förslag. Oenighet = ärende | ⬜ | Testfall där granskaren invänder blir ärende | SPEC 4 steg 6 | 26 |
| 32 | **Ärenden:** mall, prioritet, påminnelse, svar som blir nytt förslag | ⬜ | Ett svar ger nytt förslag med hänvisning | – | 31 |
| 33 | **Veckorapporten och godkännandet** i båda lägena (granskat och automatiskt), låst med hash, mobilvänlig sida. Undantagen först, A-poster samlat med stickprov | ⬜ | Spärrtest: ändrad rad efter godkännande stoppas | GitHub (Accept all/Decline), Pleo (OK/Behöver åtgärd), Ramp | 32 |
| 34 | **Bokföringssteget v1: SIE-export** av godkända verifikationer, med efterkontroll av filen | ⬜ | SIE-filen importeras i Fortnox testdatabas och stämmer med det godkända | SPEC 2.1 | 33 |
| 35 | **Logg och spårbarhet:** append-only logg med kedjad hash, och ett kommando som visar hela kedjan underlag → förslag → godkännande → verifikation | ⬜ | Manipulerad logg upptäcks | Digits Activity Log | 34 |
| 36 | **K10 månadsavstämning:** bank, kassa, skattekonto, leverantörsskulder, moms, försäljning mot kassa | ⬜ | Testbutikens månader stämmer med facit | – | 34 |
| 37 | **Facit-svit ("golden ledger"):** hela kvartalet körs mot facit vid varje ändring och modellbyte | ⬜ | Rapporten stämmer med facit på kronan (SPEC fas 0 klar) | Anthropic om evals | 36 |
| 38 | Oberoende granskning av fas C | ⬜ | Inga allvarliga eller medelfynd kvar | – | 37 |

---

## Fas D – Fler branscher och automatiskt läge (SPEC fas 1–3)

| # | Steg | Status | Klart när | Beror på |
|---|---|---|---|---|
| 39 | **Syntet Krog AB:** testföretag och testdata (mat 6/12 %, alkohol 25 %, personal, dricks) | ⬜ | Kärnan oförändrad, rapport stämmer med facit | 38 |
| 40 | **Syntet Bygg AB:** testföretag och testdata (omvänd byggmoms, material, underentreprenörer, ROT) | ⬜ | Kärnan oförändrad, rapport stämmer med facit | 39 |
| 41 | **Automatiskt läge simulerat:** inkorg som fylls som om bank och mejl vore kopplade | ⬜ | Båda lägena går hela vägen på alla tre företag | 40 |
| 42 | Oberoende granskning av fas D, sedan demo (SPEC fas 4) | ⬜ | Demo visad för minst en investerare eller kund | 41 |

---

## Fas E – Byråpaket 1: det byrån gör varje månad (bygger på det som finns, inga nya myndighetskopplingar)

| # | Steg | Status | Klart när | Lånat från | Beror på |
|---|---|---|---|---|---|
| 43 | **Kassaavstämning:** kort- och Swishbelopp i Z-rapporten mot utbetalningar från Zettle, SumUp, Nets och Swish. Avgift bokförs separat, kassadifferens visas, försäljning delas på 6/12/25 % | ⬜ | Testbutiken och Syntet Krog stämmer på öret | Jolene Z-läsare | 23, 39 |
| 44 | **Momsutkast med förkontroll:** summa per ruta i momsdeklarationen, kontrollerad mot momskontona, varje avvikelse förklarad. Redovisningsperiod (år/kvartal/månad) i konfigurationen | ⬜ | Utkastet för testföretagen stämmer med facit | Intuit Sales Tax AI, Lundify momskontroll, Jolene | 36 |
| 45 | **Skattekontoavstämning:** skattekontots händelser mot konto 1630. Flaggar ränta, oväntade debiteringar och sena betalningar | ⬜ | Testfall med ränta och sen betalning blir ärenden | Talenom, Jolene, Bokio | 36 |
| 46 | **Deadlinekalender per företag:** moms, AGI, INK2, kontrolluppgifter, årsredovisning. Datumen i en datafil med källa, aldrig i koden | ⬜ | Veckorapporten visar nästa tre deadlines för varje testföretag | Inkle, Sage | 44 |
| 47 | **Dokumentjakt:** lista över bankrader utan underlag med en färdig fråga till ägaren | ⬜ | Saknade underlag i testdatan listas med fråga | Pennylane Autopilot, Fortnox "Begär underlag" | 33 |
| 48 | **Checklista för månadsbokslut** med status "klar för månadsbokslut" | ⬜ | Checklistan granskad en gång av en redovisningskonsult | Digits Checklist, Kick | 36, 45 |
| 49 | **Regelförslag från rättelser:** när kunden ändrar en kontering föreslår Vera en ny regel. Den börjar gälla först när kunden godkänt den | ⬜ | En rättelse i testdatan ger ett regelförslag som inte gäller förrän det godkänts | Puzzle, Ramp, QuickBooks | 33 |
| 50 | **Automatiseringsgrad per motpart:** andel godkända utan ändring visas, och en motpart kan flyttas till nivå A först efter X veckor utan rättelser | ⬜ | Värdet räknas från loggen, inte gissas | Ramp, Vic.ai (stegvis autonomi) | 35, 49 |
| 51 | Oberoende granskning av fas E | ⬜ | – | – | 50 |

---

## Fas F – Före första kund

| # | Steg | Status | Klart när | Lånat från | Beror på |
|---|---|---|---|---|---|
| 52 | **Beslut (ingen kod):** Hugo ändrar SPEC avsnitt 10 så att fakturering, lönekontroll, momsdeklaration, bokslut och årsredovisning blir planerade steg. Betalningar och egen signering stannar utanför för alltid | ⬜ | Beslutet skrivet i SPEC med namn och datum | – | 51 |
| 53 | **Beslut (ingen kod):** jurist om penningtvättslagen (säljs Vera som tjänst eller program?), kundavtal, ansvarsbegränsning, personuppgiftsbiträdesavtal, överföring till USA (Anthropic har ingen EU-region) | ⬜ | Skriftligt svar från jurist | Jolenes villkor | 52 |
| 54 | **Beslut (ingen kod):** redovisningskonsult svarar på DESIGN D1–D16 för riktiga företag | ⬜ | Svaren skrivna i DESIGN 8 | – | 52 |
| 55 | **Fortnox-koppling, läsning:** kontoplan, verifikationer, leverantörsreskontra, bankens transaktioner och skattekonto (om API:et tillåter) via Fortnox testdatabas | ⬜ | Läsningen stämmer med testdatabasen. Okända API-delar dokumenterade | Fortnox API | 38 |
| 56 | **Fortnox-koppling, skrivning:** skapa verifikation och ladda upp underlag, bara efter godkännande, med efterkontroll och skydd mot dubbelbokning (samma förslag kan inte skrivas två gånger). Fortnox-nyckeln kan alltid skriva, så spärren ligger i Veras kod | ⬜ | Spärrtest 1–10 klarade mot testdatabasen | Fortnox API, SPEC 9.4 i Shop and Go-specen | 55, 19 |
| 57 | **Bokio-koppling,** samma som 55–56 | ⬜ | Samma spärrtester mot Bokios testmiljö | Bokio API | 56 |
| 58 | **Bank via Fortnox/Bokio** i automatiskt läge: läs de transaktioner som programmet redan hämtat. Bara läsning | ⬜ | Automatiskt läge körs utan uppladdad bankfil | Fortnox bankkoppling, Jolene | 55 |
| 59 | **E-postinkorg:** kunden vidarebefordrar kvitton och fakturor till en egen adress. Läsaren i karantän, K17 på allt | ⬜ | Spärrtest: mejl med dolda instruktioner blir ärende | Jolene, Bokio kvittoinkorg | 28 |
| 60 | **Kontroll av leverantörsfakturor:** tolkning, attestförslag, bedrägerikoll (ändrat bankgiro, dubbletter, ny leverantör, ovanligt belopp). Vera betalar aldrig | ⬜ | Testfall med ändrat bankgiro blir ärende med hög prioritet | Xero Bill Protection, Fortnox dubblettfilter | 56 |
| 61 | **Momsdeklaration klar att signera:** Vera fyller i momsen i Fortnox, kunden granskar förkontrollen och signerar själv med BankID | ⬜ | Testdatabasen visar en ifylld deklaration som inte är inskickad | Fortnox moms-API, Jolene | 44, 56 |
| 62 | **Månadsrapport med kommentarer:** resultat, balans, nyckeltal och ett kort brev på vanlig svenska om vad som ändrats och varför. Siffrorna från koden | ⬜ | Rapport för testföretagen granskad mot facit | Inverso, Intuit Finance Agent, Zeni | 36 |
| 63 | **Lönekontroll ovanpå Fortnox Lön/Bokio Lön:** AGI mot bokföringen, ungdomsrabatten (född 2003–2007, tak 25 000 kr, till 2027-09-30), semesterlöneskuld | ⬜ | Testfall med fel arbetsgivaravgift blir ärende | Talenom, Skatteverket | 55 |
| 64 | **Kassaregistrets XML-export** (krav från 2027-01-01) som källa vid sidan av Z-rapporten | ⬜ | En XML-fil i testdatan läses och stämmer med Z-rapporten | SKVFS 2021:17 | 23 |
| 65 | **Onboarding:** intervju i chatt, import av förra årets SIE-fil, regelförslag från historiken, och en skuggvecka där Vera föreslår men inget bokförs | ⬜ | Ett nytt testföretag kommer igång utan att kärnan ändras | Digits, Ramp, Jolene (8 frågor) | 49, 55 |
| 66 | **Dataexport vid uppsägning:** allt kunden äger (underlag, logg, regelbok, SIE) kan exporteras | ⬜ | Export av ett testföretag går att läsa in igen | Jolene GDPR-export, lärdom från Bench | 35 |
| 67 | Oberoende granskning av fas F och spärrtest mot riktiga testdatabaser | ⬜ | Inga allvarliga eller medelfynd kvar | – | 66 |

---

## Fas G – Det konkurrenterna redan har (paritet)

| # | Steg | Status | Klart när | Lånat från | Beror på |
|---|---|---|---|---|---|
| 68 | **Egen app, version 1:** inloggning med tvåstegsverifiering, chatt-start, att-göra-lista, godkänn på mobilen, notiser (push och mejl, kunden väljer veckodag), roller och ersättare | ⬜ | En testkund godkänner en vecka helt i mobilen | Jolene, Wint (att-göra), Spendesk, Ramp | 67, Ö1 |
| 69 | **Revisor- eller konsultåtkomst** med bara läsrätt och tidsgräns | ⬜ | Revisorn ser allt men kan inte godkänna | Spiris, Bokio Byrå | 68 |
| 70 | **Kundfakturor och påminnelser** via Fortnox/Bokio, med OCR och Swish-QR. Kunden godkänner varje utskick i början | ⬜ | Faktura skapad i testdatabasen efter godkännande | Intuit Payments Agent, Xero Payment Follow Ups | 56 |
| 71 | **ROT/RUT** för hantverkare (Syntet Bygg AB) | ⬜ | ROT-faktura och begäran förberedd, kunden signerar | Fortnox, Bokio | 70, 40 |
| 72 | **Anläggningsregister och avskrivningsplaner** | ⬜ | Planerna föreslås och bokförs månadsvis efter ett godkännande | Digits Schedules, Fortnox | 56 |
| 73 | **Periodiseringar:** förutbetalda kostnader och upplupna kostnader som vänds nästa månad | ⬜ | Testfallen med hyra och försäkring (D10) stämmer | Ramp, Digits | 72, 54 |
| 74 | **Likviditetsprognos och skattereserv:** pengar om 4–13 veckor, och vad som ska läggas undan till moms och skatt. Osäkerheten visas | ⬜ | Prognos för testföretagen med förklaring | Xero Cash Flow Actions, Pilot, Accountable | 58 |
| 75 | **Chatt "fråga dina böcker":** svaren räknas i koden, och uträkningen visas | ⬜ | 20 testfrågor besvaras rätt mot facit | Jolene "Fråga Jolene", Zeni, Xero JAX | 68 |
| 76 | **Förgranskning av bokslutet:** checklista, periodiseringar, avskrivningar, lagervärde, semesterlöneskuld, skatteberäkning. Allt nivå D | ⬜ | En redovisningskonsult har granskat reglerna | Pennylane Autopilot, Kick | 73, 54 |
| 77 | **K2-årsredovisning, utkast** med noter, förvaltningsberättelse och alla avstämningar bifogade. Inlämning via Fortnox/Spiris, styrelsen signerar | ⬜ | Utkast för ett testföretag granskat av en revisor | Fortnox Bokslut & Skatt, Spiris | 76 |
| 78 | **INK2 och K10** enligt 3:12-reglerna från 2026. INK2:s e-tjänst stängs 2026-12-29, så det går via API eller SRU-fil | ⬜ | Utkast för ett testföretag granskat av en redovisningskonsult | Jolene, Spiris | 77 |
| 79 | **AGI-utkast** i Fortnox/Bokio Lön, kunden signerar med BankID | ⬜ | Utkast stämmer med lönekontrollen i steg 63 | Fortnox, Intuit Workforce | 63 |
| 80 | **Spiris-koppling** (tredje programmet) | ⬜ | Samma spärrtester som 56 | Spiris API, MCP | 57 |
| 81 | **Enskild firma** som ny konfiguration (NE-bilaga) | ⬜ | Kärnan oförändrad | Jolene, Bokio | 78 |
| 82 | **Eget Skatteverket-avtal som ombud** för moms och AGI, så att Vera inte behöver gå via Fortnox. Kräver att Vera Labs har F-skatt, moms- och arbetsgivarregistrering och inga skatteskulder | ⬜ | Avtal tecknat, spärrtest klarat | Jolene (ombud + BankID) | 61, 79, 53 |
| 83 | Oberoende granskning av fas G | ⬜ | – | – | 82 |

---

## Fas H – Lite till: det ingen konkurrent gör i dag

| # | Steg | Status | Varför det är unikt | Beror på |
|---|---|---|---|---|
| 84 | **Regelboken på vanlig svenska:** kunden skriver "Snabbgross är varuinköp, ofta två momssatser", Vera gör om det till en regel och ett test som kunden godkänner | ⬜ | Ingen svensk aktör låter kunden äga en läsbar regelbok. Digits gör det bara för kontroller | 49 |
| 85 | **Kassabutikspaketet:** Z-rapport, kortinlösen, Swish, kassadifferens, tre momssatser och XML-export i ett flöde | ⬜ | De billigaste byråerna tar inte kunder med kontanthantering, och ingen programvara gör hela kedjan | 43, 64 |
| 86 | **Årsredovisning som styrelsen förstår:** varje post i utkastet har en förklaring på vanlig svenska och en länk till underlagen | ⬜ | Ingen i världen automatiserar årsredovisningen helt, och ingen förklarar den | 77 |
| 87 | **Revisorspaketet:** ett klick ger hela spårbarhetskedjan, alla kontroller och alla godkännanden för ett år | ⬜ | Gör revisionen billigare för kunden, och är ett säljargument mot byrån | 35, 77 |
| 88 | **Branschnyckeltal:** jämför kundens marginal, personalkostnad och svinn med andra i samma bransch (anonymt, först när det finns tillräckligt många kunder) | ⬜ | Byråer gör det sällan för små företag | 62, 68 |
| 89 | **Nya branscher som konfiguration:** e-handel, frisör, konsult, skapare | ⬜ | Samma kärna, nya regelböcker | 81 |
| 90 | **Fler agenter på samma kärna:** strategikonsulten, trendövervakaren, leverantörsagenten | ⬜ | Del av Vera Labs plan, efter bokföringsagenten | 83 |

---

## Datum att bevaka

| Datum | Vad | Steg |
|---|---|---|
| 2026-12-29 | Skatteverkets e-tjänst för INK2 stängs | 78 |
| 2027-01-01 | Kassaregister måste kunna exportera journalminnet som XML | 64 |
| 2027-09-30 | Sänkta arbetsgivaravgifter för unga upphör | 63 |
| 2027-12-31 | Sänkt matmoms (6 %) upphör | 43, 44 |
| 2027 | Första K10 enligt de nya 3:12-reglerna | 78 |
