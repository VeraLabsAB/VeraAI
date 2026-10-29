# PROGRESS – Veras bokföringsagent

Uppdaterad 2026-10-29. Specifikation: `SPEC.md`. Byggordning: `DESIGN-regelbok.md` avsnitt 7.
Byggplan för hela produkten: `BYGGPLAN.md` (Hugos beslut 2026-10-29, rättad 2026-10-29 efter den här filen). Steg 12: vakten installerades på Hugos dator 2026-10-28. Steg 12 är klart igen 2026-10-29: den nya versionen av inställningsfilen, där läget Auto tillåts igen (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto tillåts igen"), är installerad och kontrollerad (`GRANSKNING.md`, "Kontroll efter bytet av inställningsfil, 2026-10-29"). Auto får användas på Hugos dator, med villkoren tills steg 15 är klart. Caspers dator är steg 14. Spärrtestet är klart och grönt (2026-10-29). **Steg 13 är klart**: provet med en vakt som fallerar (steg 8 i kontrollen) är gjort och grönt 2026-10-29. **Q2, Q2b, Q3 och Q4 är klara och granskade** (Q2: 3e3c18c och d7d38e0, Q2b: 1dcf769, Q3: bd851ba, Q4: 2bc9762, Hugos beslut 2026-10-29 om Q2–Q4). **Granskning 21 (3bbcbe4) är gjord och grön**: inget allvarligt och inget på nivån medel, tre låga fynd (L1–L3) som är rättade i dokumentationen 2026-10-29 (L3 som exempel i SPEC Ö5). **Q7 är stängd**: pusha som det är, historiken skrivs inte om, och repot på GitHub förblir privat (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Q7 stängd"). Pushat 2026-10-29. **Besluten inför uppgift 4 (B1–B3)** står i `GRANSKNING.md`, "Beslut 2026-10-29 – inför uppgift 4", och **D13 och D14** under "D13 och D14 beslutade" (baec52b). **Uppgift 4 är byggd** 2026-10-29 (4269f76, f6ed99e och e4cc538): flöde a, b och e med K5 och K8 i `scripts/konteringsfloden.py`, och den nya nyckeln `bokforing` i regelboken (Hugos OK i chatten 2026-10-29). Granskad i granskning 22 (e4d8cd7), gult: P1 och P2 kvar, 7 frågor väntar på Hugo. Pushad (`main` på GitHub står vid d127c3e). **Hugos beslut efter uppgift 4 (a–f)** står i `GRANSKNING.md`, "Beslut efter uppgift 4 (2026-10-29)" (48e7ed3), och är byggda 2026-10-29 i ded669d (c: nyckeln `flode`, reserverade namn och regeln `bankens-avgifter`) och 5753890 (f och e). Inte pushade. Nästa steg: se "Nästa steg i byggordningen". Caspers dator installeras i helgen (vecka 44, Öppet, punkt 15).

Granskningarna och rättelserna efter dem: `GRANSKNING.md`.

Projektet är i **fas 0** (SPEC avsnitt 9): ett testföretag, Syntet Testbutik AB, hela vägen från
underlag till godkänd rapport. Inget i koden kan i dag bokföra något.

Testsviten: **4 304 passed**, 0 misslyckade (körd senast 2026-10-29 efter besluten efter uppgift 4: 4 273 från förut
och 31 nya, de flesta i `scripts/tests/test_beslut_efter_uppgift_4.py`). Sedan installationen
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
| Beslut c: flöde e väljs bara med regelbokens nyckel `flode` (`"bankavgift"`). En regel för pengar ut utan nyckeln blir ett ärende, "regeln saknar flöde", nivå D. Reserverade namn: en regel i `matchning.json` eller ett regel-id får inte heta `bankavgift`, och testbutikens regel heter nu `bankens-avgifter`. 22 av 26 nya tester röda mot 48e7ed3 | ded669d |
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
27. **Reserverade ord gäller bara regelnamn och regel-id** (Hugos beslut i chatten 2026-10-29). Spärren i
    `test_karnan_ar_generell.py` söker också efter motparter, kassaregister, ägare, betalsätt och konton ur
    regelboken. En motpart som heter exakt `bankavgift` skulle alltså fortfarande krocka med kärnans ord, och då
    blir testet rött (inte tyst). Om reserverade ord ska stoppa fler namn bestämmer Hugo eller Casper.
28. **Värdet D i ärendet "regeln saknar flöde"** valdes i byggsessionen 2026-10-29 (som "allt annat från banken" i
    D13, den säkra riktningen), liksom att `flode` bara får stå i en regel för bankrader och att `bankavgift` kräver
    exakt kontot `kostnad`. BESLUTSFATTARE SAKNAS för bekräftelse.

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
   5753890). Kvar: Öppet 26 (konton för hyra, el och telefon), 27 och 28. Inte pushad. DESIGN 7 säger oberoende granskning efter uppgift 3 och 6, inte efter 4. Det som var förutsättningarna:
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
- **Hugos beslut i chatten 2026-10-27:** listan över ägare och närstående ligger kvar i
  `foretag/<namn>/regelbok.json` tills spärrsteget, eftersom SPEC inte säger var den skyddade mappen ska
  ligga. Testet att listan ligger utanför alla mappar agenten får skriva i skrivs då.
- **Hugos beslut 2026-10-21 (enligt den förra versionen av den här filen):** testantagandena i grupp b
  (Ö-T2, Ö-T4, Ö-T5, Ö-T8, Ö-T9 och Ö-T24) godkändes som de stod, för testföretaget. De gäller inte för
  riktiga företag. Frågorna står nu i `testforetag/FIKTIVT_FORETAG.md` avsnitt 9, där de inte är markerade
  som besvarade.
