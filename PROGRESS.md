# PROGRESS – bokföringsagent för många företag (version 1)

Specifikation: `SPEC.md`. Uppdaterad 2026-10-21.

## Status

| Steg | Innehåll (SPEC 14) | Status |
|---|---|---|
| 0 | Omstart: arkiv av v0, lärdomar, ny SPEC, PROGRESS, GRANSKNING och CLAUDE.md | Klart på grenen `omstart-v1`. Väntar på oberoende granskning innan sammanslagning med `main` |
| 1 | Skal: mappstruktur, Python-miljö, kontroll av företagskonfiguration, testföretagets konfiguration | Ej påbörjad |
| 2 | Säkerhetsgrund: fast kommandolista, skrivskydd, isoleringsspärr, logg med kedja, spärrar som stänger vid fel | Ej påbörjad |
| 3 | Testdatagenerator för testföretaget, Q1 med planterade fel | Ej påbörjad. Grinden är klar: Hugo godkände testantagandena i grupp b 2026-10-21 |
| 4 | Inläsning: bank, kassa, underlag, arkiv | Ej påbörjad |
| 5 | Matchning, kontering och kontrollerna K1–K17 på Q1 | Ej påbörjad |
| 6 | Granskare, ärenden, rapportsida och Excel | Ej påbörjad |
| 7 | Godkännandeflöde och bokförande körning mot simulerad mottagare | Ej påbörjad |
| 8 | Q2–Q4, momsrapport per kvartal och månadsavstämning | Ej påbörjad |
| 9 | Företag nummer två (Shop and Go) utan ändring i kärnan, test mot juni 2024 | Ej påbörjad |
| 10 | Fortnox-koppling, bara läsning | Ej påbörjad |

## Det gamla bygget (v0)

- Hela det gamla bygget (steg 1–4 för ett enda företag, 407 tester) finns i taggen `v0-shop-and-go`.
  Läs en fil med `git show v0-shop-and-go:<fil>`.
- Gamla specen, progress och granskningarna ligger i `dokument/v0/`. Lärdomarna och reglerna R1–R33
  står i `dokument/LARDOMAR.md`.

## Beslut

- 2026-10-21: Hugo godkände testantagandena i grupp b (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9, Ö-T24 i
  SPEC avsnitt 16) som de står, för testföretaget. De gäller inte för riktiga företag.

## Nästa steg

Oberoende granskning av grenen `omstart-v1` (SPEC.md, LARDOMAR.md, CLAUDE.md) i en ny session.
