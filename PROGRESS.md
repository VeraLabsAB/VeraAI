# PROGRESS – Veras bokföringsagent

Uppdaterad 2026-10-28. Specifikation: `SPEC.md`. Byggordning: `DESIGN-regelbok.md` avsnitt 7.
Granskningarna och rättelserna efter dem: `GRANSKNING.md`.

Projektet är i **fas 0** (SPEC avsnitt 9): ett testföretag, Syntet Testbutik AB, hela vägen från
underlag till godkänd rapport. Inget i koden kan i dag bokföra något.

Testsviten: **3 350 passed**, 0 misslyckade (körd 2026-10-28 i projektet med `.venv/bin/python`, i
byggsessionen efter Hugos beslut om granskning 13).

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

**Öppet beslut (P4):** appen och appens Claude Code ägs av Hugo, inte av systemet. Förbuden stoppar agentens
fil-verktyg, men inte program som Hugo själv kör eller den kända luckan (en egen testfil). Ska ägandet
ändras, eller räcker förbuden? Inget ägande är ändrat.

**Beslut som behövs:**

1. **P4:** se det öppna beslutet ovan.
2. **P3 b, tolkning:** `cd ~/VERA` står kvar före `~/.local/bin/claude` (bara `claude` är utbytt mot hela
   sökvägen). Bekräftas?
3. **`~/Library/Application Support/Claude`** har också skrivbordsappens egna inställningar. Bara mappen
   `claude-code` är förbjuden nu. Ska hela mappen förbjudas? Inte kontrollerat vad mer som ligger där.
4. **Ny oberoende granskning** av den nya versionen, med kontrollsummor, före installationen. P5 (omvägarna
   i en kopia) görs i en egen session före uppgift 5 (Öppet, punkt 6).

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
  `Project settings` och `Project local settings` är väntade. Raden läses i Terminal (`cd ~/VERA`, `claude`,
  `/status`). Nytt sista steg i kontrollen efter installationen: agenten ombeds köra `date` i
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
   byggda** efter Hugos beslut 2026-10-28 (5cb9080, 08a3370, c066188). **PATH-regeln, förprovet för
   `onFailure` och P7 är byggda** efter Hugos beslut 2026-10-28 (`GRANSKNING.md`, "Beslut 2026-10-28:
   PATH-regel, förprov för onFailure, P7"). Kvar: P1 (omvägarna), att lägsta version för
   `disableSkillShellExecution` och `disableAutoMode` inte är bekräftad i dokumentationen, och **beslutet om
   testsviten**: PATH-regeln stoppar båda pytest-kommandona efter installationen, eftersom
   `.venv/bin/python` ligger i projektet.
   Kontrollsummorna i granskning 12 gäller inte längre, eftersom vakten och inställningarna är ändrade.
   Provet med en vakt som fallerar visar att en **saknad** vakt stoppar (Python ger kod 2), men prövar inte
   `onFailure` i sig (INSTALLERA.md, steg 8).
6. **Granskning 13, P5: omvägarna förbi vakten med kommandotexter i en kopia.** Hugos beslut 2026-10-28 (P5
   a): görs i **en egen session före uppgift 5**. Granskning 12 och 13 kunde inte göra det provet, eftersom
   ett säkerhetsfilter i Claude Code stoppade svaret. Det som inte är uteslutet är framför allt sätt som zsh
   läser ett ord på som skiljer sig från vaktens uppdelning. **Öppen, inte gjord.**

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
- **Hugos beslut i chatten 2026-10-27:** listan över ägare och närstående ligger kvar i
  `foretag/<namn>/regelbok.json` tills spärrsteget, eftersom SPEC inte säger var den skyddade mappen ska
  ligga. Testet att listan ligger utanför alla mappar agenten får skriva i skrivs då.
- **Hugos beslut 2026-10-21 (enligt den förra versionen av den här filen):** testantagandena i grupp b
  (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9 och Ö-T24) godkändes som de stod, för testföretaget. De gäller inte för
  riktiga företag. Frågorna står nu i `testforetag/FIKTIVT_FORETAG.md` avsnitt 9, där de inte är markerade
  som besvarade.
