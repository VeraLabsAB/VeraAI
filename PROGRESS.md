# PROGRESS – Veras bokföringsagent

Uppdaterad 2026-10-28. Specifikation: `SPEC.md`. Byggordning: `DESIGN-regelbok.md` avsnitt 7.
Granskningarna och rättelserna efter dem: `GRANSKNING.md`.

Projektet är i **fas 0** (SPEC avsnitt 9): ett testföretag, Syntet Testbutik AB, hela vägen från
underlag till godkänd rapport. Inget i koden kan i dag bokföra något.

Testsviten: **2 794 passed**, 0 misslyckade (körd 2026-10-28 på commit dd0e1cf, både i projektet och i en
ren kopia av commiten tagen med `git archive`).

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

## Öppet

1. **Granskning 9 (av ea51c97)** står sist i `GRANSKNING.md`. Bara sammanfattningen finns kvar. Beslut (a)
   och (b) är byggda i dd0e1cf. Kvar: listan över ägare och närstående ligger där agenten kan skriva, till
   spärrsteget (Hugos beslut 2026-10-27), och granskningens punkt 4 är okänd. dd0e1cf är inte oberoende
   granskad.
2. **N2, vilka tecken ett namn i regelboken får ha.** I dag får ett namn bara ha a–z med eller utan accent,
   0–9, mellanslag, bindestreck, understreck och punkt. Öppen fråga till Hugo eller Casper: ska fler tecken
   få finnas, till exempel `&` (som i "Café Ölund & Söner AB"), `/`, `,`, `'` och parenteser, och bokstäver
   som `Ø`, `Æ` och `ß`? I dag stoppas de (SPEC 7, DESIGN-regelbok.md avsnitt 8).
3. **Fyra val från rättelserna efter granskning 7 väntar på bekräftelse** (DESIGN-regelbok.md avsnitt 8,
   granskning 8:s punkt 6): regelbokens namn bara latinska, regel-id bara a–z, siffror och bindestreck, en
   roll per konto, och ägarens bankrader som hela ord. Valen gjordes i en byggsession, inte av en människa.
   BESLUTSFATTARE SAKNAS.
4. **`foretag/README.md` säger fortfarande att ägarlistan är valfri** och att en tom lista godtas. Det
   stämmer inte efter dd0e1cf. Filen fick inte ändras i uppgiften (bara ägarspärren, matchningen, deras
   tester, SPEC.md och PROGRESS.md).

## Nästa steg i byggordningen

1. En oberoende granskning av dd0e1cf i en ny session.
2. **Uppgift 4**: flöde a, b och e (leverantörsfakturor, kvitton och bankavgifter) med K5 och K8.
3. Uppgift 5: Z-rapporter, kortinlösen, Swish och kontantinsättningar (och M9 från granskning 7).
4. Uppgift 6: nivåerna A–D och K9, med nivå D för ägarens bankrader. Därefter en oberoende granskning.

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
- **Hugos beslut i chatten 2026-10-27:** listan över ägare och närstående ligger kvar i
  `foretag/<namn>/regelbok.json` tills spärrsteget, eftersom SPEC inte säger var den skyddade mappen ska
  ligga. Testet att listan ligger utanför alla mappar agenten får skriva i skrivs då.
- **Hugos beslut 2026-10-21 (enligt den förra versionen av den här filen):** testantagandena i grupp b
  (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9 och Ö-T24) godkändes som de stod, för testföretaget. De gäller inte för
  riktiga företag. Frågorna står nu i `testforetag/FIKTIVT_FORETAG.md` avsnitt 9, där de inte är markerade
  som besvarade.
