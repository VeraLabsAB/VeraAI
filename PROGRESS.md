# PROGRESS – Veras bokföringsagent

Uppdaterad 2026-10-28. Specifikation: `SPEC.md`. Byggordning: `DESIGN-regelbok.md` avsnitt 7.
Granskningarna och rättelserna efter dem: `GRANSKNING.md`.

Projektet är i **fas 0** (SPEC avsnitt 9): ett testföretag, Syntet Testbutik AB, hela vägen från
underlag till godkänd rapport. Inget i koden kan i dag bokföra något.

Testsviten: **3 198 passed**, 0 misslyckade (körd 2026-10-28 i projektet, i byggsessionen som härdade
vakten efter granskning 12).

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

## Öppet

1. **Granskning 10 (av dd0e1cf)** står sist i `GRANSKNING.md`. P1 är rättat i 16000a8 (Hugos beslut
   2026-10-28), P2 i texten i SPEC avsnitt 11 och P5–P6 i dokumentationen. Kvar från granskningen: P3
   (en ägarrad med ett skiljetecken intill namnet matchas aldrig mot sitt underlag, säker riktning) och P4
   (nivåsteget ska använda märkningen, uppgift 6). Listan över ägare och närstående ligger där agenten kan
   skriva, till spärrsteget (Hugos beslut i chatten 2026-10-27). 16000a8 och 10bfe0f är oberoende granskade
   i granskning 11 (P1 stängd, fynd Q1–Q8). Öppna därifrån: Q2–Q4 och Q7.
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
   hela körningen på riktiga underlag om den kommer först**.
5. **Granskning 12 av vakten (2026-10-28)** står sist i `GRANSKNING.md`. Testsviten: 3 148 passed.
   Frågorna från bygget är besvarade, och kontrollsummorna står där. **Inte komplett:** punkt 3 (omvägar
   förbi vakten) gjordes inte, eftersom ett säkerhetsfilter stoppade den (P1, stoppar installationen).
   Övriga fynd: P2 (provet där vakten fallerar togs bort ur kontrollen efter installationen), P3 (skills
   som kör skalkommandon), P4 (kommandoverktyg känns igen på namnet), P5 (`.git` som fil), P6 (läget
   "auto") och P7 (rättigheterna på `/Library/Application Support`). **P2–P6 och beslut (a) och (b) är
   byggda** efter Hugos beslut 2026-10-28 (5cb9080, 08a3370, c066188). Kvar: P1 (omvägarna), P7 (inget
   beslut), vilka mappar i Hugos `PATH` som ska förbjudas (förbuden mot `~/bin`, `~/.local/bin` och
   `/opt/homebrew` är granskarens förslag, inte kontrollerade mot Hugos `PATH`), och att lägsta version
   för `disableSkillShellExecution` och `disableAutoMode` inte är bekräftad i dokumentationen.
   Kontrollsummorna i granskning 12 gäller inte längre, eftersom vakten och inställningarna är ändrade.
   Provet med en vakt som fallerar visar att en **saknad** vakt stoppar (Python ger kod 2), men prövar inte
   `onFailure` i sig (INSTALLERA.md, steg 8).

## Nästa steg i byggordningen

1. **Vakten för kommandolistan (granskning 11, Q1).** Byggsessionen är klar (f21a3a1, 773e919 och
   6686166), och fynden i granskning 12 är byggda (5cb9080, 08a3370, c066188). Kvar: **en ny oberoende
   granskning av den nya versionen, med punkt 3 (omvägarna)** och nya kontrollsummor, sedan kontrollerar
   Hugo versionen och installerar enligt `sparr/INSTALLERA.md`, och
   därefter kontrollen efter installationen i en ny session (sist i `sparr/INSTALLERA.md`). Caspers dator
   får samma installation och samma kontroll. Före
   uppgift 4 (Hugos beslut 2026-10-28).
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
- **Hugos beslut i chatten 2026-10-27:** listan över ägare och närstående ligger kvar i
  `foretag/<namn>/regelbok.json` tills spärrsteget, eftersom SPEC inte säger var den skyddade mappen ska
  ligga. Testet att listan ligger utanför alla mappar agenten får skriva i skrivs då.
- **Hugos beslut 2026-10-21 (enligt den förra versionen av den här filen):** testantagandena i grupp b
  (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9 och Ö-T24) godkändes som de stod, för testföretaget. De gäller inte för
  riktiga företag. Frågorna står nu i `testforetag/FIKTIVT_FORETAG.md` avsnitt 9, där de inte är markerade
  som besvarade.
