# Installera vakten för kommandolistan

Skriven 2026-10-28 i byggsessionen för granskning 11, Q1. Planen och Hugos beslut står i `GRANSKNING.md`
under "Granskning 11 – plan för Q1".

Den här beskrivningen är till **Hugo** (och sedan **Casper**, på sin dator). Agenten kör inga av
kommandona. Du kör dem själv i programmet **Terminal**, ett i taget, och skriver ditt
administratörslösenord när datorn frågar efter det.

## Vad som installeras

Två filer kopieras till mappen `/Library/Application Support/ClaudeCode/`. Den mappen ägs av
systemet, så det krävs ett administratörslösenord för att ändra där. Agenten kan därför inte ändra
filerna.

| Fil i projektet | Kopieras till | Vad den gör |
|---|---|---|
| `sparr/kommandosparr.py` | `/Library/Application Support/ClaudeCode/vera/kommandosparr.py` | **Vakten.** Ett litet program som Claude Code kör före varje verktyg. Det stoppar allt som inte står på listan i SPEC 7.1. |
| `sparr/managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` | **De låsta inställningarna.** De säger åt Claude Code att köra vakten, att stoppa kommandot om vakten kraschar eller inte svarar, och att bara vakter och regler härifrån gäller. En Claude Code som är äldre än 2.1.295 startar inte alls. Agenten får inte skriva i `.git` (varken mappen eller filen, på varje djup), i skalets och gits startfiler, i `~/.claude`, i `~/Library/LaunchAgents`, i `~/.ssh`, i `.mcp.json`, i någon mapp `.claude` (också projektets), i `~/.claude.json`, i `~/bin`, `~/.local/bin` och `/opt/homebrew`, eller i någon mapp `.venv`. Läget "auto" går inte att använda, och skills kan inte köra skalkommandon. |

Inställningarna börjar gälla så fort filen finns, i terminalen och i skrivbordsappen. Därför kopieras
vakten först och inställningarna sist.

## Innan du börjar

1. **Den oberoende granskningen ska vara klar** (planens steg 2), och du ska kopiera filerna från den
   commit som granskades. Ändras filerna i projektet efter granskningen, kopiera inte. Fråga först.
   Provet med en vakt som fallerar (steg 8 i kontrollen efter installationen) behövs inte före
   installationen (Hugos beslut 2026-10-28, 8).
2. **Titta efter om mappen redan finns.** Öppna Finder, välj **Gå > Gå till mapp…** och skriv
   `/Library/Application Support/ClaudeCode`. Om Finder säger att mappen inte finns: bra, gå vidare.
   Om mappen finns och har filer i sig: **stoppa och fråga**, så att inget som redan ligger där skrivs
   över.

## Steg 1: kontrollera Claude Codes version (före allt annat)

Inställningen som stoppar kommandot när vakten kraschar eller inte svarar heter `onFailure`. Den kräver
**Claude Code version 2.1.295 eller senare**. På en äldre version körs kommandot ändå om vakten
kraschar. Kravet står i Claude Codes dokumentation på sidan **code.claude.com/docs/en/hooks**, i
tabellen över fälten för en vakt av typen `command` ("Requires Claude Code v2.1.295 or later") och i
avsnittet "Block the action when a hook fails". Kontrollerat 2026-10-28.

Terminalen och skrivbordsappen har **var sin** Claude Code med var sitt versionsnummer, och att
uppdatera den ena uppdaterar inte den andra (sidan **code.claude.com/docs/en/desktop**, avsnittet
"Claude Code version in the Code tab"). Båda ska därför kontrolleras.

**I Terminal:** kör

```bash
claude --version
```

Det visar Claude Codes version, till exempel `2.1.300`. Det läser bara, och ändrar ingenting.

**I skrivbordsappen:** öppna en ny session i fliken **Code** på den här datorn, skriv `/status` i
rutan där du skriver till Claude, och läs raden **Claude Code**. Den visar versionen.

Läs i samma ruta raden **Setting sources** (var inställningarna kommer från). Om den nämner inställningar
från claude.ai (server-managed settings) går de före filen som installeras här, och då används inte
filen. Stoppa i så fall och fråga.

De låsta inställningarna innehåller också `"requiredMinimumVersion": "2.1.295"`, så att en äldre Claude
Code inte startar alls efter installationen (Hugos beslut 2026-10-28). Kontrollen här behövs ändå,
eftersom inställningarna inte gäller förrän de är installerade.

Två inställningar har ingen lägsta version i dokumentationen: `disableSkillShellExecution` (skills kör
inga skalkommandon) och `disableAutoMode` (läget "auto" går inte att använda). Sidorna
**code.claude.com/docs/en/settings-reference**, **/skills** och **/permissions** nämner ingen version för
dem, kontrollerat 2026-10-28. Lägsta version är alltså **inte bekräftat** (Hugos beslut 2026-10-28: byggs
in ändå). Kontrollen efter installationen, steg 1, visar att läget "auto" saknas.

**Båda versionerna ska vara 2.1.295 eller senare.** Om någon är äldre: **stoppa**, uppdatera den först
(skrivbordsappen med **Claude > Check for Updates…**, och terminalens Claude Code enligt
dokumentationen), kontrollera igen, och gå vidare först när båda är minst 2.1.295.

## Steg 2: kontrollera att filerna är de som granskades

```bash
shasum -a 256 ~/VERA/agent/sparr/kommandosparr.py ~/VERA/agent/sparr/managed-settings.json
```

- `shasum -a 256` räknar ut en **kontrollsumma** för varje fil: ett "fingeravtryck" på 64 tecken.
  Minsta ändring i en fil ger en helt annan summa. Kommandot bara läser, och ändrar ingenting.
- Jämför de två summorna, tecken för tecken, med dem som den oberoende granskningen har skrivit upp
  (Hugos beslut 2026-10-28). **Är någon summa olika: stoppa och fråga.** Kopiera ingenting.

## Steg 3: kopiera vakten

```bash
sudo ditto ~/VERA/agent/sparr/kommandosparr.py "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

- `sudo` gör att kommandot körs som administratör. Datorn frågar efter ditt lösenord. Det syns inte
  när du skriver, det är normalt.
- `ditto` kopierar en fil. Om mapparna `ClaudeCode` och `vera` inte finns, skapar `ditto` dem som en
  del av kopieringen.
- `~/VERA/agent/sparr/kommandosparr.py` är vakten i projektet (`~` betyder din hemmapp).
- Den sista sökvägen är dit vakten kopieras. Citattecknen behövs, eftersom "Application Support"
  har ett mellanslag.

## Steg 4: låt systemet äga mappen och vakten

```bash
sudo chown -R root:wheel "/Library/Application Support/ClaudeCode"
```

- `chown` byter ägare. `root:wheel` är systemets administratör och dess grupp.
- `-R` gör att det gäller mappen och allt i den, alltså också `vera` och vakten.
- Efter det kan bara en administratör ändra i mappen, och agenten, som arbetar som ditt vanliga
  konto, kan inte göra det.

## Steg 5: sätt rättigheterna på mapparna och vakten

```bash
sudo chmod 755 "/Library/Application Support/ClaudeCode" "/Library/Application Support/ClaudeCode/vera"
```

- `chmod` sätter vem som får läsa, skriva och öppna. `755` på en mapp betyder: ägaren (systemet) får
  ändra, alla andra får bara titta in. Claude Code behöver kunna titta in för att hitta filerna.

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

- `644` på en fil betyder: ägaren (systemet) får ändra, alla andra får bara läsa. Claude Code behöver
  kunna läsa vakten för att köra den med `/usr/bin/python3`.

## Steg 6: kopiera de låsta inställningarna (sist, nu börjar de gälla)

```bash
sudo cp -i ~/VERA/agent/sparr/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- `cp` kopierar en fil. `-i` gör att datorn frågar innan den skriver över en fil som redan finns. Om
  den frågar: svara `n` (nej) och stoppa, eftersom filen då inte borde finnas (se "Innan du börjar").

## Steg 7: låt systemet äga inställningarna och sätt rättigheterna

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Samma som i steg 4 och 5, för inställningsfilen: systemet äger den, alla får läsa den, bara en
  administratör får ändra den.

## Steg 8: kontrollera att det är samma filer som ligger på plats

```bash
shasum -a 256 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Samma kontroll som i steg 2, nu för filerna där de installerades. Summorna ska vara exakt samma som
  i steg 2. **Är någon olika: stoppa och fråga.**

## Efteråt

1. **Starta nya sessioner** i terminalen och i skrivbordsappen. Sessioner som redan är öppna kan ha
   läst inställningarna innan filen fanns.
2. **Gör kontrollen efter installationen** (sist i den här filen) i en ny session.
3. **Agenten kan inte längre skriva i `~/.claude`** (Hugos beslut 2026-10-28, punkt 5). Där ligger
   bland annat Claudes minne mellan sessionerna (`~/.claude/projects/…/memory`). Det slutar gå att
   spara nytt där. Claude Code själv skriver fortfarande sina egna filer.
4. **Vakterna i tillägget superpowers slutar fungera** (Hugos beslut 2026-10-28, 2), eftersom bara
   vakter från de låsta inställningarna får köras.
5. **Bara verktygen på listan i SPEC 7.1 fungerar** (granskning 12, P4, Hugos beslut 2026-10-28). Andra
   verktyg, till exempel webbsökning, appens webbläsare och kopplingar till andra tjänster, stoppas av
   vakten. Behövs ett verktyg till blir det en ny version av vakten.
6. **Läget "auto" går inte att välja** (granskning 12, P6). Claude Code frågar dig före varje kommando
   som inte är förgodkänt.
7. **Agenten kan inte skriva i projektets mapp `.claude`, i `.mcp.json` eller i `.venv`** (Hugos beslut
   2026-10-28, 5). Inställningar och kopplingar för projektet skriver du eller Casper själva.

## Caspers dator

Samma steg, i samma ordning, och samma versionskontroll i steg 1 (både terminalen och
skrivbordsappen, minst 2.1.295). Samma `managed-settings.json` fungerar: regeln som hindrar agenten att
skriva i `.git` (`Edit(//**/.git/**)`) gäller varje `.git`-mapp på datorn och har inget användarnamn i
sig. En skillnad:

- Sökvägen till projektet kan vara en annan. Byt `~/VERA/agent` i steg 2, 3 och 6 mot där projektet
  ligger på Caspers dator.

Kontrollen nedan görs också på Caspers dator.

## Kontroll efter installationen

Planens steg 5 (Hugos beslut 2026-10-28). Gör stegen i ordning, i **en ny session** i fliken **Code** i
skrivbordsappen, startad i `~/VERA/agent`. Du skriver till agenten som vanligt. Agenten gör inte den här
kontrollen utan att du säger till.

Om något steg inte blir som det står: **stoppa, skriv upp vad som hände, och fråga** innan något annat
görs. Steg 1–7 ska vara klara innan uppgift 4 körs. Steg 8 krävs inte för installationen eller för
uppgift 4, men ska vara gjort före läget "auto", före körningar utan att Hugo tittar, före första hela
körningen på riktiga underlag och före första kund (Hugos beslut 2026-10-28, 8).

1. **De låsta inställningarna gäller.** Skriv `/status` och läs raden **Setting sources**. Den ska visa
   `Enterprise managed settings (file)`, alltså inställningarna från filen du installerade
   (code.claude.com/docs/en/managed-settings). Läs också raden **Claude Code**: versionen ska vara
   2.1.295 eller senare. Läget "auto" ska inte gå att välja: i terminalens Claude Code, tryck Shift+Tab
   några gånger, och "auto" ska inte komma upp (code.claude.com/docs/en/settings-reference,
   `disableAutoMode`).
2. **Ihopkopplade kommandon stoppas.** Be agenten köra `ls; ls`. Det ska stoppas med ett fel som börjar
   "Stoppat av vakten" och säger att kommandon inte kopplas ihop.
3. **Ett kommando på listan går igenom.** Be agenten köra `git status`. Claude Code frågar dig som vanligt
   om det får köras. Säg ja. Kommandot ska köras och visa läget i projektet.
4. **sudo stoppas.** Be agenten köra `sudo ls`. Det ska stoppas, antingen av vakten ("sudo och su stoppas
   alltid") eller av förbudsregeln i inställningarna. Datorn ska **inte** fråga efter ditt lösenord. Gör
   den det: skriv inte lösenordet, avbryt med Ctrl+C, och stoppa.
5. **Agenten kan fortfarande fråga dig.** Be agenten ställa en fråga till dig med svarsknappar. Frågan
   ska visas, och ditt svar ska komma fram.
6. **Agenten kan fortfarande skriva filer i `~/VERA`.** Be agenten skapa en liten provfil,
   `~/VERA/agent/provfil.txt`, med fil-verktyget Write. Claude Code frågar dig först. Säg ja. Filen ska
   finnas efteråt. Ta sedan bort den själv i Finder.
7. **En session i en worktree fungerar, eller stoppas på ett säkert sätt** (Hugos beslut 2026-10-28,
   punkt 6). En **worktree** är en egen kopia av projektet på en egen gren, som skrivbordsappen kan skapa
   för en session. Starta en ny session i en worktree i skrivbordsappen och be agenten köra `git status`.
   Det finns två godtagbara utfall:
   - kommandot går igenom (som i steg 3), eller
   - vakten stoppar det med "annan mapp". Då stoppar vakten alla kommandon i worktree-sessioner. Det är
     säkert, men skriv upp det och fråga, eftersom worktree-sessioner då inte går att använda.

   Om kommandot i stället körs utan att vakten har prövat det, till exempel om `ls; ls` går igenom i
   worktree-sessionen: stoppa och fråga.
8. **Provet med en vakt som fallerar:** ett vanligt kommando ska stoppas när vakten inte går att köra
   (Hugos beslut 2026-10-28, 7, granskning 12 P2). Det här
   steget gör du **själv i Terminal**, inte agenten. Gör det sist, när steg 1–7 är klara. Vakten flyttas
   undan en kort stund, och flyttas sedan tillbaka. Inställningsfilen ändras inte.

   **a. Flytta undan vakten.** Kommandot byter bara namn på filen, i samma mapp (`.av` på slutet):

   ```bash
   sudo mv "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/vera/kommandosparr.py.av"
   ```

   - `mv` flyttar eller byter namn på en fil. `sudo` gör att det körs som administratör, och datorn
     frågar efter ditt lösenord. När det är klart visas ingenting.

   **b. Pröva.** Starta en ny session i fliken **Code**, startad i `~/VERA/agent`, och be agenten köra
   `git status`. **Det ska stoppas.** Felet kommer från Claude Code och inte från vakten (vakten ligger ju
   inte på plats), så det börjar inte med "Stoppat av vakten". Det säger att vakten (en hook,
   `PreToolUse`) inte gick att köra, och nämner troligen `can't open file` och `No such file or
   directory`. Eftersom vakten gäller alla verktyg stoppas allt i sessionen, också när agenten vill läsa
   en fil. Det är den säkra riktningen.

   **Om `git status` går igenom och visar läget i projektet: gör c direkt, och stoppa och fråga.**

   **c. Flytta tillbaka vakten:**

   ```bash
   sudo mv "/Library/Application Support/ClaudeCode/vera/kommandosparr.py.av" "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
   ```

   **d. Jämför kontrollsummorna:**

   ```bash
   shasum -a 256 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json"
   ```

   Du ser två rader, var och en med en summa på 64 tecken och sökvägen till filen. Summorna ska vara
   **exakt samma** som i steg 8 i installationen (och som de som granskningen skrev upp). Är någon olika:
   stoppa och fråga.

   **e. Starta en ny session** och gör steg 2 och 3 igen: `ls; ls` ska stoppas med "Stoppat av vakten",
   och `git status` ska gå igenom. Då är vakten tillbaka och fungerar.

   **Vad provet visar.** När vakten saknas kan `/usr/bin/python3` inte öppna filen och avslutar med kod 2,
   och kod 2 betyder för Claude Code "stoppa". Provet visar alltså att en **saknad** vakt stoppar allt.
   Det prövar inte inställningen `onFailure: "block"` i sig, som gäller när vakten fallerar på andra sätt
   (en annan kod än 0 och 2, tidsgränsen, eller att programmet inte går att starta). Att Python ger kod 2
   visas av testet `test_systemets_python_stoppar_med_kod_2_nar_vakten_saknas`.
