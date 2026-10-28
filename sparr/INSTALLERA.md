# Installera vakten för kommandolistan

Skriven 2026-10-28 i byggsessionen för granskning 11, Q1. Planen och Hugos beslut står i `GRANSKNING.md`
under "Granskning 11 – plan för Q1". Ändrad samma dag efter Hugos beslut 2026-10-28 om PATH-regeln,
förprovet för `onFailure` och P7 (`GRANSKNING.md`, "Beslut 2026-10-28: PATH-regel, förprov för onFailure,
P7"). Ändrad igen samma dag efter Hugos beslut 2026-10-28 om vakten, beslut 1–4 (`GRANSKNING.md`,
"Granskning 11 – plan för Q1"): projektets Python flyttas till en mapp som systemet äger (steg 9), och
nvm-mappen flyttas sist i `PATH` (steg 4). Ändrad igen samma dag efter Hugos svar 2026-10-28, punkt 1–3:
också Cryptexes-mappen flyttas sist (steg 4), den gamla `.venv` tas bort efter installationen, raden Setting
sources läses i Terminal och bara en annan låst källa underkänner installationen, och ett sista steg i
skrivbordsappen visar att vakten stoppar ett kommando som inte står på listan. Ändrad igen samma dag efter
Hugos beslut 2026-10-28 om granskning 13 (`GRANSKNING.md`, "Granskning 11 – plan för Q1"): kontroll av alias
och funktioner före och efter installationen (P1 a, steg 4 g och kontrollen efter installationen, steg 1),
förbud för filerna som zsh läser vid start och de filer de läser in (P1 b), Claude Code för Terminal med
hela sökvägen `~/.local/bin/claude` och en varning för installerarens förslag (P3 b, steg 1), och förbud för
Claude Code för Terminal, skrivbordsappens Claude Code och appen (P4 a). Ändrad igen samma dag efter Hugos
beslut 2026-10-28 om granskning 14 (`GRANSKNING.md`, "Hugos svar 2026-10-28 efter granskning 14"): förbud
för `~/.zcompdump` och en kontroll av zsh:s mappar för funktioner (R1, steg 4 i), en kontroll av vilka filer
zsh läser in (R2, steg 4 h), en vänd kontroll av alias och funktioner där allt som inte är väntat stoppar
(R3, steg 4 g), och vad du ska se när ett steg går bra, och steg 4 d på en dator utan nvm (R5).

Den här beskrivningen är till **Hugo** (och sedan **Casper**, på sin dator). Agenten kör inga av
kommandona. Du kör dem själv i programmet **Terminal**, ett i taget, och skriver ditt
administratörslösenord när datorn frågar efter det. Kopiera ett kommando i taget från en grå ruta,
klistra in det i Terminal och tryck Retur.

## Vad som installeras

Två filer kopieras till mappen `/Library/Application Support/ClaudeCode/`, och projektets Python
skapas där. Den mappen ägs av systemet, så det krävs ett administratörslösenord för att ändra där.
Agenten kan därför inte ändra filerna.

| Fil i projektet | Kopieras till | Vad den gör |
|---|---|---|
| `sparr/kommandosparr.py` | `/Library/Application Support/ClaudeCode/vera/kommandosparr.py` | **Vakten.** Ett litet program som Claude Code kör före varje verktyg. Det stoppar allt som inte står på listan i SPEC 7.1. Det stoppar också ett kommando vars program ligger i en mapp som du kan ändra utan lösenord, och kommandon som ändrar `PATH` (PATH-regeln, se nedan). |
| `sparr/managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` | **De låsta inställningarna.** De säger åt Claude Code att köra vakten, att stoppa kommandot om vakten kraschar eller inte svarar, och att bara vakter och regler härifrån gäller. En Claude Code som är äldre än 2.1.295 startar inte alls. Agenten får inte skriva i `.git` (varken mappen eller filen, på varje djup), i skalets och gits startfiler, i `~/.claude`, i `~/Library/LaunchAgents`, i `~/.ssh`, i `.mcp.json`, i någon mapp `.claude` (också projektets), i `~/.claude.json`, i `~/bin`, `~/.local/bin` och `/opt/homebrew`, eller i någon mapp `.venv`. Inte heller i filerna som zsh läser när det startar och de filer som de läser in: nvm-mappen `~/.nvm`, `~/.zkbd`, `~/.zsh_sessions`, `~/.zlogout` och systemets zsh-filer i `/etc` (granskning 13, P1 b), och `~/.zcompdump`,
som zsh:s `compinit` läser in vid start (granskning 14, R1). Inte heller i Claude Code för Terminal (`~/.local/bin/claude` och `~/.local/share/claude`), i skrivbordsappens egen Claude Code (`~/Library/Application Support/Claude/claude-code`) eller i appen (`/Applications/Claude.app`) (granskning 13, P4 a). Inte heller någonstans i hela `~/Library/Application Support/Claude`, där också skrivbordsappens egna inställningar ligger (Hugos svar 2026-10-28 efter granskning 13, punkt 3). Läget "auto" går inte att använda, och skills kan inte köra skalkommandon. |
| `requirements.txt` (listan över paket) | `/Library/Application Support/ClaudeCode/vera/venv` (skapas, kopieras inte) | **Projektets Python med pytest**, som testsviten körs med. Den låg förut i mappen `.venv` i projektet, som du äger, och då stoppade PATH-regeln testsviten. Nu ligger den där bara systemet kan ändra den (Hugos beslut 2026-10-28 om vakten, beslut 1). |

Inställningarna börjar gälla så fort filen finns, i terminalen och i skrivbordsappen. Därför kopieras
vakten först, sedan skapas projektets Python, och inställningarna kopieras sist.

**Claude Code för Terminal omfattas av samma låsta inställningar som appen** (Hugos beslut 2026-10-28,
granskning 13, fråga 2). Claude Code för Terminal, `~/.local/bin/claude`, behålls, men utanför `PATH` (steg
1). Den läser samma fil som skrivbordsappen: dokumentationen säger att terminalen och skrivbordsappens flik
Code läser samma källor (code.claude.com/docs/en/managed-settings, "Surfaces"). Vakten, förbuden och
`"onFailure": "block"` gäller alltså där också, och agenten får inte skriva i den (förbudet i tabellen
ovan). Att den faktiskt läser filen syns efter installationen: raden **Setting sources** i `/status` i
Terminal ska visa `Enterprise managed settings (file)` ("Efteråt", punkt 2).

**PATH-regeln** (Hugos beslut 2026-10-28, beslut 1). `PATH` är listan över mappar där datorn letar efter
ett program när du skriver dess namn, till exempel `git`. Ligger ett program med samma namn i en mapp
som du själv kan ändra, kan det bytas ut utan lösenord. Vakten släpper därför bara igenom ett kommando om
programmet, och varje mapp ovanför det, ägs av systemet (`root`) och inte går att ändra för någon annan.
Samma krav gäller själva filen och, om filen är en **länk** (en hänvisning till en fil någon annanstans),
filen dit länken leder (Hugos beslut 2026-10-28 om vakten, beslut 3). Det gäller också **varje mapp i
`PATH` före programmet** (beslut 2): en sådan mapp som du äger stoppar kommandot, också när programmet inte
ligger i den. Därför flyttas nvm-mappen sist i din `PATH` i steg 4.

**Testsviten.** Pytest-kommandona i SPEC 7.1 körs med Python i
`/Library/Application Support/ClaudeCode/vera/venv`, som du skapar i steg 9 (Hugos beslut 2026-10-28 om
vakten, beslut 1). Den gamla mappen `.venv` i projektet används inte längre när vakten är installerad.

## Innan du börjar

1. **Den oberoende granskningen ska vara klar** (planens steg 2), och du ska kopiera filerna från den
   commit som granskades. Ändras filerna i projektet efter granskningen, kopiera inte. Fråga först.
   Provet med en vakt som fallerar (steg 8 i kontrollen efter installationen) behövs inte före
   installationen (Hugos beslut 2026-10-28, 8). Förprovet i steg 3 nedan behövs däremot.
2. **Titta efter om mappen redan finns.** Öppna Finder, välj **Gå > Gå till mapp…** och skriv
   `/Library/Application Support/ClaudeCode`. Om Finder säger att mappen inte finns: bra, gå vidare.
   Om mappen finns och har filer i sig: **stoppa och fråga**, så att inget som redan ligger där skrivs
   över.
3. **Visar ett kommando något annat än det som står vid steget: stoppa och fråga** (granskning 14, R5,
   Hugos beslut 2026-10-28). Det gäller varje steg, också när det inte står uttryckligen. Kör inte nästa
   kommando förrän du har fått svar. Många kommandon visar **ingenting alls** när det går bra: du får bara
   en ny rad att skriva på. Det står vid varje sådant steg.

## Steg 1: kontrollera Claude Codes version (före allt annat)

Inställningen som stoppar kommandot när vakten kraschar eller inte svarar heter `onFailure`. Den kräver
**Claude Code version 2.1.295 eller senare**. På en äldre version körs kommandot ändå om vakten
kraschar. Kravet står i Claude Codes dokumentation på sidan **code.claude.com/docs/en/hooks**, i
tabellen över fälten för en vakt av typen `command` ("Requires Claude Code v2.1.295 or later") och i
avsnittet "Block the action when a hook fails". Kontrollerat 2026-10-28.

Du har två Claude Code: den i **Claude-appen** och **Claude Code för Terminal**. Båda ska ha version
2.1.295 eller senare. Först appen, med `/status` (Hugos beslut 2026-10-28, beslut 3):

1. Öppna Claude-appen, gå till fliken **Code** och starta en ny session, till exempel i `~/VERA/agent`.
2. Skriv `/status` i rutan där du skriver till Claude och tryck Retur. `/status` är ett kommando till
   Claude Code, inte till Terminal. Det visar bland annat versionen och var inställningarna kommer ifrån,
   och ändrar ingenting.
3. Läs raden **Claude Code**. Den visar versionen, till exempel `2.1.300`. Jämför siffergrupperna mellan
   punkterna en i taget, från vänster: `2.1.300` och `2.2.0` är senare än `2.1.295`, men `2.1.29` är
   äldre (29 är mindre än 295).
4. Raden **Setting sources** (var inställningarna kommer från) visas inte i skrivbordsappen. Den läses i
   Terminal, se nedan.

**Claude Code för Terminal, alltid med hela sökvägen** (Hugos beslut 2026-10-28, granskning 13, P3 b).
Claude Code för Terminal är installerad med den officiella metoden, och programmet ligger i
`~/.local/bin/claude` (version 2.1.312 enligt dig 2026-10-28). Mappen `~/.local/bin` står inte i `PATH`, och
den ska inte läggas dit. Därför skriver du alltid hela sökvägen, `~/.local/bin/claude`, och aldrig bara
`claude`. Skriver du bara `claude` säger Terminal `command not found: claude`. Det är väntat och inget fel.

> **Varning: kör inte installerarens förslag.** När Claude Code installerades föreslog installeraren
> raden `export PATH="$HOME/.local/bin:$PATH"`. **Kör den inte, och lägg inte in den i `~/.zshrc`,
> `~/.zprofile` eller någon annan fil.** Skälen:
>
> - Raden lägger `~/.local/bin` **först** i `PATH`, före systemets mappar. Mappen ägs av dig, så vakten
>   stoppar då **alla** kommandon, också `git status` (PATH-regeln, Hugos beslut 2026-10-28 om vakten,
>   beslut 2).
> - Ett program som läggs i den mappen med samma namn som ett program på listan, till exempel `git`, skulle
>   köras i stället för systemets program. Det kräver inget lösenord. Det är just det PATH-regeln skyddar
>   mot.
> - Skrivbordsappen läser `PATH` från skalet när den startar, så raden skulle gälla agentens kommandon
>   också, inte bara Terminal.
>
> Har raden redan kommit in i någon av filerna: stoppa och fråga. (Steg 4 e visar om `~/.local/bin` står i
> `PATH`.)

Kontrollera versionen i Terminal. Öppna Terminal och kör:

```bash
~/.local/bin/claude --version
```

- Visar versionen av Claude Code för Terminal, till exempel `2.1.312 (Claude Code)`, och ändrar ingenting.
  Versionen ska vara 2.1.295 eller senare (jämför som i punkt 3 ovan).
- Säger Terminal `no such file or directory`: Claude Code för Terminal ligger inte där. Stoppa och fråga.

**Om versionen i Terminal är äldre än 2.1.295**, uppdatera:

```bash
~/.local/bin/claude update
```

- Hämtar och installerar den senaste versionen av Claude Code för Terminal (det kräver internet). Det ska
  stå `Successfully updated from … to version …` eller `Claude Code is up to date (…)`. Kör sedan
  `~/.local/bin/claude --version` igen. Är versionen fortfarande äldre än 2.1.295: stoppa och fråga.
  (Kommandona står på code.claude.com/docs/en/setup, "Verify your installation" och "Update manually".)

**Raden Setting sources, i Terminal** (Hugos svar 2026-10-28, punkt 3, och Hugos beslut 2026-10-28,
granskning 13, P3 b, som ersätter `claude` med hela sökvägen). Kör ett kommando i taget:

```bash
cd ~/VERA
```

```bash
~/.local/bin/claude
```

- `cd ~/VERA` gör `~/VERA` till mappen du står i. `~/.local/bin/claude` startar Claude Code för Terminal, i
  den mappen. Frågar Claude Code om du litar på mappen: svara ja.
- Säger Terminal `no such file or directory`: stoppa och fråga.

Skriv sedan `/status` i Claude Code i Terminal och tryck Retur. Leta upp raden som börjar med
**Setting sources**. Den räknar upp källorna efter kolon, åtskilda med kommatecken.

- **Väntade källor**, som inte underkänner något: `User settings` (dina egna inställningar),
  `Project settings` (projektets) och `Project local settings` (projektets, bara på din dator).
- **Före installationen** ska raden inte nämna någon låst källa, till exempel inställningar som styrs från
  claude.ai (orden `managed`, `policy` eller `claude.ai`). En sådan går före filen som installeras här, och
  då används inte filen. Stoppa i så fall och fråga.
- **Efter installationen** ska raden också visa `Enterprise managed settings (file)`, alltså filen du
  installerade. Bara en annan låst källa underkänner installationen (Hugos svar 2026-10-28, punkt 3).
- Står det något annat på raden som inte är nämnt här: stoppa och fråga.
- Avsluta Claude Code i Terminal med `/exit`.

**Om appens version är äldre än 2.1.295: stoppa och uppdatera först.**

1. Klicka på **Claude** i menyraden överst på skärmen (när Claude-appen är aktiv) och välj **Check for
   Updates…**. Installera uppdateringen om det finns en.
2. Avsluta appen helt (**Claude > Quit Claude**, eller Cmd+Q) och öppna den igen.
3. Starta en ny session och gör `/status` igen.
4. Gå vidare först när versionen är minst 2.1.295. Säger appen att den redan är senaste versionen, men
   versionen fortfarande är äldre än 2.1.295: stoppa och fråga.

Terminalen och skrivbordsappen har **var sin** Claude Code med var sitt versionsnummer, och att uppdatera
den ena uppdaterar inte den andra (sidan **code.claude.com/docs/en/desktop**, avsnittet "Claude Code
version in the Code tab"). Kontrollera därför versionen i båda: i appen med `/status` och i Terminal med
`~/.local/bin/claude --version` (ovan), innan du installerar vakten.

De låsta inställningarna innehåller också `"requiredMinimumVersion": "2.1.295"`, så att en äldre Claude
Code inte startar alls efter installationen (Hugos beslut 2026-10-28). Kontrollen här behövs ändå,
eftersom inställningarna inte gäller förrän de är installerade.

Två inställningar har ingen lägsta version i dokumentationen: `disableSkillShellExecution` (skills kör
inga skalkommandon) och `disableAutoMode` (läget "auto" går inte att använda). Sidorna
**code.claude.com/docs/en/settings-reference**, **/skills** och **/permissions** nämner ingen version för
dem, kontrollerat 2026-10-28. Lägsta version är alltså **inte bekräftat** (Hugos beslut 2026-10-28: byggs
in ändå). Kontrollen efter installationen, steg 1, visar att läget "auto" saknas.

## Steg 2: kontrollera mapparna ovanför (före installationen)

Vakten och inställningarna skyddas av att bara systemet kan ändra mappen `ClaudeCode`. Det skyddet gäller
bara om ingen annan heller kan ändra mapparna ovanför, eftersom den som kan ändra en mapp kan flytta undan
allt som ligger i den (granskning 12, P7, Hugos beslut 2026-10-28, beslut 3).

```bash
ls -ld / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"
```

- `ls -ld` visar en rad per mapp: vem som äger mappen och vem som får ändra i den. Det bara läser, och
  ändrar ingenting. Citattecknen behövs, eftersom "Application Support" har ett mellanslag.
- En rad ser ut ungefär så här: `drwxr-xr-x  67 root  wheel  2144 Oct 28 10:00 /Library`. Så läser du den:
  - Det första tecknet, `d`, betyder att det är en mapp.
  - Sedan kommer tre grupper om tre tecken: vad **ägaren** får (`rwx`), vad **gruppen** får (`r-x`) och
    vad **alla andra** får (`r-x`). `r` betyder läsa, `w` betyder skriva (ändra), `x` betyder öppna
    mappen, och `-` betyder att det inte är tillåtet.
  - Efter siffran kommer **ägaren** (`root`, systemets administratör) och sedan **gruppen** (till
    exempel `wheel` eller `admin`).
- **Så ska de tre första raderna** (`/`, `/Library` och `/Library/Application Support`) se ut:
  - ägaren är `root`, och
  - det står **inget `w`** på plats 6 (gruppen) eller plats 9 (alla andra), räknat från vänster.
    Rätt: `drwxr-xr-x`. Fel: till exempel `drwxrwxr-x` (gruppen får ändra) eller `drwxr-xrwx` (alla får
    ändra).
  - `/Library/Application Support` har gruppen `admin` på din dator. Det är bra så länge det inte står
    `w` på plats 6.
- **Den fjärde raden** ska säga `No such file or directory`, eftersom mappen `ClaudeCode` inte finns än.
- Står det `+` eller `@` direkt efter de tio tecknen (till exempel `drwxr-xr-x+`), har mappen extra
  uppgifter som raden inte visar, och de kan ge fler rättigheter. Stoppa och fråga.

**Kan gruppen eller andra skriva någonstans i kedjan, är ägaren inte `root`, eller finns `ClaudeCode`
redan: avbryt installationen och fråga.**

## Steg 3: förprov – stoppar Claude Code ett kommando när en vakt fallerar?

`"onFailure": "block"` ska göra att ett kommando stoppas när vakten inte går att köra. Förprovet visar att
din Claude Code faktiskt gör så, **innan** något installeras (Hugos beslut 2026-10-28, beslut 2). Det görs
i en tillfällig mapp, `~/vera-forprov`, utanför `~/VERA`, med en vakt som pekar på ett skript som inte
finns. Ingenting i `~/VERA` eller i `/Library` ändras, och inget kräver lösenord.

**a. Kontrollera att mappen inte finns:**

```bash
ls -ld ~/vera-forprov
```

- Visar mappen `vera-forprov` i din hemmapp (`~` betyder din hemmapp), om den finns. Det ska stå
  `No such file or directory`. Finns mappen redan: stoppa och fråga.

**b. Skapa mappen:**

```bash
mkdir -p ~/vera-forprov/.claude
```

- `mkdir` skapar en mapp. `-p` gör att mappen ovanför, `vera-forprov`, skapas i samma steg. `.claude` är
  mappen där Claude Code läser inställningar för en mapp.

**c. Skriv inställningsfilen** (kommandot är en enda lång rad, kopiera hela):

```bash
echo '{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[{"type":"command","command":"/finns-inte/vera-forprov.sh","onFailure":"block"}]}]}}' > ~/vera-forprov/.claude/settings.json
```

- `echo '…'` skriver ut texten mellan de enkla citattecknen, och `>` gör att texten hamnar i filen
  `settings.json` i stället för på skärmen. Kommandot skapar bara den filen.
- Texten är inställningar för Claude Code: före varje verktyg (`PreToolUse`, och `"matcher": "*"` betyder
  alla verktyg) ska programmet `/finns-inte/vera-forprov.sh` köras. Det programmet finns inte, och mappen
  `/finns-inte` kan inte skapas utan administratörslösenord. Claude Code kan alltså inte starta vakten.
  `"onFailure": "block"` säger: går vakten inte att köra, stoppa kommandot.

**d. Kontrollera filen:**

```bash
cat ~/vera-forprov/.claude/settings.json
```

- `cat` visar vad som står i filen, och ändrar ingenting. Det ska vara exakt texten mellan citattecknen i
  c.

**e. Pröva.** Öppna Claude-appen, gå till fliken **Code** och starta en ny session i mappen
`vera-forprov` i din hemmapp. Frågar appen om du litar på mappen: svara ja (den har bara filen ovan). Be
Claude: "Kör kommandot `ls`."

- **Förväntat: kommandot stoppas.** Claude Code säger att en vakt (en hook, `PreToolUse`) inte gick att
  köra, eller att verktyget stoppades. Eftersom vakten gäller alla verktyg kan Claude inte heller läsa
  filer i den sessionen. Det är rätt.
- **Om `ls` körs och visar filerna i mappen: förprovet har misslyckats.** Det betyder att Claude Code inte
  stoppar ett kommando när en vakt fallerar, och då skyddar vakten inte. Gör f, avbryt installationen och
  fråga.
- Avsluta sessionen när du har sett resultatet (arkivera den i appen).

**f. Radera den tillfälliga mappen** (i båda fallen). Ett kommando i taget:

```bash
rm ~/vera-forprov/.claude/settings.json
```

```bash
rmdir ~/vera-forprov/.claude
```

```bash
rmdir ~/vera-forprov
```

- `rm` raderar en fil, här bara inställningsfilen från c.
- `rmdir` raderar en mapp, men bara om den är tom, så inget annat kan försvinna av misstag. Först
  `.claude`, sedan `vera-forprov`.
- Säger `rmdir` `Directory not empty` har något mer hamnat i mappen. Radera inte på något annat sätt:
  stoppa och fråga.
- Kör sedan `ls -ld ~/vera-forprov` från a igen. Det ska stå `No such file or directory`.

**Stoppades `ls` inte i e: avbryt installationen.** Gå vidare till steg 4 bara om `ls` stoppades.

## Steg 4: flytta nvm-mappen och Cryptexes-mappen sist i PATH, och kontrollera alias, funktioner och zsh:s filer (före installationen)

Vakten kräver att varje mapp i `PATH` före programmet ägs av systemet och inte går att ändra för någon
annan (Hugos beslut 2026-10-28 om vakten, beslut 2). På din dator står två mappar före `/usr/bin` och
`/bin`, där programmen på listan ligger, som inte klarar det:

- **nvm-mappen**, `/Users/hugolindholmer/.nvm/versions/node/v24.18.0/bin`, står först. **nvm** (Node Version
  Manager) är ett program som installerar Node, och mappen ägs av dig.
- **Cryptexes-mappen**, `/System/Cryptexes/App/usr/bin`. Den ägs av systemet, men leder till
  `/System/Volumes/Preboot/Cryptexes`, som har rättigheterna 777 (alla får ändra, enligt mappens egna
  uppgifter). Mappen innehåller bara programmet `safaridriver` (för att styra Safari från program), som
  inte står på listan.

Båda står så både i den `PATH` som Claude Code själv har (och som vakten får) och i den `PATH` som
agentens kommandon körs med (kontrollerat 2026-10-28, se `PROGRESS.md`). Utan det här steget stoppar vakten
**alla** kommandon, också `git status`. Med båda mapparna sist går alla 13 program på listan igenom
(prövat med vakten mot din `PATH` 2026-10-28). Vakten har inget undantag för någon av mapparna (Hugos svar
2026-10-28, punkt 1).

nvm lägger in sin mapp från filen `~/.zshrc`, som skalet zsh (programmet som tolkar kommandona i Terminal)
läser varje gång det startar. Här lägger du till två rader sist i den filen: en som flyttar nvm-mappen sist
i `PATH`, och en som sedan flyttar Cryptexes-mappen sist. Agenten ändrar inte dina skalfiler, du gör det
själv, på din och på Caspers dator (Hugos beslut 2026-10-28 om vakten, beslut 2, och Hugos svar
2026-10-28, punkt 1; de låsta inställningarna förbjuder också agenten att skriva i `~/.zshrc`). `node`,
`npm`, `npx` och `safaridriver` fungerar som förut.

**a. Gör en säkerhetskopia av filen:**

```bash
cp -i ~/.zshrc ~/.zshrc.fore-vera
```

- `cp` kopierar filen `~/.zshrc` till `~/.zshrc.fore-vera`. `-i` gör att datorn frågar innan den skriver
  över en fil som redan finns. Om den frågar: svara `n` (nej), och stoppa och fråga.
- Går det bra visas ingenting.
- Säger kommandot `No such file or directory` finns ingen `~/.zshrc`. Det är vanligt på en ny dator och
  inget fel, men då läggs nvm (om det finns) in från en annan fil, och raderna nedan kan hamna i fel fil.
  Stoppa och fråga, så att rätt fil ändras.

**b. Lägg till raden för nvm-mappen sist i filen** (kommandot är en enda rad, kopiera hela):

```bash
echo '[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )' >> ~/.zshrc
```

- `echo '…'` skriver ut texten mellan de enkla citattecknen, och `>>` (två större än-tecken) lägger
  texten **sist** i filen. Med bara ett `>` skulle hela filen ersättas, så kopiera kommandot exakt. Har
  det ändå blivit fel: hämta tillbaka säkerhetskopian med `cp ~/.zshrc.fore-vera ~/.zshrc`, och fråga.
- Raden som hamnar i filen gör så här: `$NVM_BIN` är nvm-mappen. `path` är zsh:s namn på `PATH` som en
  lista. `${path:#$NVM_BIN}` är listan utan nvm-mappen, och nvm-mappen läggs sedan sist. `[ -n "$NVM_BIN" ]
  &&` betyder "bara om nvm har angett sin mapp", så att ingen tom mapp läggs till.

**c. Lägg till raden för Cryptexes-mappen sist i filen**, efter raden från b (en enda rad, kopiera hela):

```bash
echo 'path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )' >> ~/.zshrc
```

- Samma sätt som i b, med `>>`. Raden som hamnar i filen är:
  `path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )`. Den tar bort
  `/System/Cryptexes/App/usr/bin` ur listan och lägger den sist, efter nvm-mappen.
- Fanns mappen inte i `PATH` förut (till exempel på en dator med en äldre macOS), läggs den till sist. Det
  är ofarligt: vakten prövar bara mapparna före programmet.

**d. Kontrollera filen:**

```bash
tail -n 3 ~/.zshrc
```

- `tail -n 3` visar de tre sista raderna i filen, och ändrar ingenting. De **två sista** raderna ska vara
  exakt de två raderna från b och c, i den ordningen:
  - `[ -n "$NVM_BIN" ] && path=( ${path:#$NVM_BIN} $NVM_BIN )`
  - `path=( ${path:#/System/Cryptexes/App/usr/bin} /System/Cryptexes/App/usr/bin )`
- **På en dator utan nvm** (till exempel Caspers, om nvm inte finns där) har du bara lagt in raden från c,
  inte den från b. Då ska bara den **sista** raden vara Cryptexes-raden ovan, och raden för nvm ska inte
  stå bland de tre (granskning 14, R5, Hugos beslut 2026-10-28).
- Står något annat där, eller står en rad två gånger: hämta tillbaka säkerhetskopian med
  `cp ~/.zshrc.fore-vera ~/.zshrc`, och fråga.

**e. Kontrollera `PATH`.** Öppna ett **nytt** Terminal-fönster (Cmd+N), så att skalet läser filen på
nytt, och kör:

```bash
echo $PATH
```

- Visar `PATH`: mapparna i ordning, åtskilda med `:`, på en enda lång rad. Så ska den se ut:
  - Den **första** mappen ska vara en av systemets, till exempel `/usr/local/bin`, och `/usr/bin` och `/bin`
    ska komma tidigt.
  - nvm-mappen (den med `.nvm` i namnet) ska stå **näst sist**.
  - `/System/Cryptexes/App/usr/bin` ska stå sist, efter nvm-mappen. Raden slutar alltså med
    `:/Users/hugolindholmer/.nvm/versions/node/v24.18.0/bin:/System/Cryptexes/App/usr/bin`.
  - På din dator 2026-10-28 ska hela raden bli (radbruten här, i Terminal en rad):

    ```
    /usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:
    /var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:
    /var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:
    /var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:
    /pkg/env/global/bin:/Library/Apple/usr/bin:/Users/hugolindholmer/.nvm/versions/node/v24.18.0/bin:
    /System/Cryptexes/App/usr/bin
    ```

    Har nvm bytt version sedan dess kan siffrorna efter `node/v` vara andra.
  - På en dator utan nvm finns ingen nvm-mapp i raden, och `/System/Cryptexes/App/usr/bin` står sist.
- Står nvm-mappen eller `/System/Cryptexes/App/usr/bin` före `/usr/bin`: stoppa och fråga. Då läggs de
  troligen in från en annan fil, till exempel `~/.zprofile` eller `~/.zlogin`, efter `~/.zshrc`.
- `~/.local/bin` (på din dator `/Users/hugolindholmer/.local/bin`) ska **inte** stå någonstans i raden
  (Hugos beslut 2026-10-28, granskning 13, P3 b). Står den där har installerarens förslag kommit in i en
  fil (se varningen i steg 1): stoppa och fråga.

**f. Starta om Claude-appen** helt (**Claude > Quit Claude**, eller Cmd+Q), och öppna den igen. Claude
Code läser `PATH` när appen startar, så sessioner som redan är öppna har kvar den gamla ordningen. Att
appen har fått den nya ordningen syns först efter installationen: i kontrollen efter installationen, steg
3, ska `git status` gå igenom.

**g. Kontrollera alias och funktioner** (Hugos beslut 2026-10-28, granskning 13, P1 a). Claude Code läser
in `~/.zshrc` när en session startar, och tar med sig **alias** (ett kortnamn som skalet byter ut mot ett
annat kommando) och **funktioner** (små program som skrivs direkt i skalet) till varje kommando som agenten
kör. Vakten ser dem inte. Heter ett alias eller en funktion som ett kommando på listan, till exempel `git`,
kör skalet aliaset eller funktionen i stället för programmet som vakten prövade. Gör det här i samma nya
Terminal-fönster som i e, ett kommando i taget:

**Kontrollen är vänd** (granskning 14, R3, Hugos beslut 2026-10-28): du letar inte efter farliga namn,
utan kontrollerar att **bara väntade namn** finns. Allt annat stoppar, också namn som verkar ofarliga.
Skälet: ett farligt alias eller en farlig funktion behöver inte heta som ett kommando på listan. Ett
**globalt alias** (`alias -g`) byts ut var det än står i ett kommando, så ett alias som heter `status`
gör om `git status` till något annat. Och funktioner med vissa särskilda namn körs av zsh av sig själv,
till exempel `TRAPDEBUG` (före varje kommando) och andra namn som börjar med `TRAP`, `preexec`, `precmd`,
`chpwd`, `periodic`, `zshexit`, `zshaddhistory`, `zsh_directory_name` och `command_not_found_handler`.

```bash
alias
```

- `alias` visar alla alias, också globala alias, ett per rad, som `namn=vad det byts ut mot`. Det bara
  visar, och ändrar ingenting.
- **Väntat: exakt två rader**, `run-help=man` och `which-command=whence` (i valfri ordning). zsh har dem
  alltid.
- **Står någon annan rad där, eller visas ingenting alls: stoppa och fråga.** Installera inte. (Visas
  ingenting kan något ha dolt utskriften.)

```bash
alias -s
```

- `alias -s` visar alias för filändelser (till exempel att en fil som slutar på `.txt` öppnas med ett
  visst program). `alias` ovan visar inte dem. Det bara visar, och ändrar ingenting.
- **Väntat: ingenting.** Visas någon rad: stoppa och fråga. Installera inte.

```bash
builtin print -rl -- ${(ko)functions:#(_*|nvm*|shell_session*|update_terminal_cwd|compinit|compdef|compdump|compaudit|compinstall|bashcompinit|compgen|complete|getent)} SLUT
```

- Kommandot är en enda lång rad, kopiera hela. Det visar namnen på alla funktioner **utom de väntade**,
  ett per rad, och sist ordet `SLUT`. Det bara visar, och ändrar ingenting.
- **Väntade funktioner**, som kommandot inte visar: namn som börjar med `_` (zsh:s hjälp för att fylla i
  kommandon med tabb, ofta flera hundra), med `nvm` (nvm) eller med `shell_session` (Terminal), och
  `update_terminal_cwd` (Terminal). Dessutom de nio som zsh:s `compinit` och `bashcompinit` lägger in när
  nvm läses in: `compinit`, `compdef`, `compdump`, `compaudit`, `compinstall`, `bashcompinit`, `compgen`,
  `complete` och `getent` (prövat med zsh 5.9 på Hugos dator 2026-10-28, i ett test utan Hugos filer).
- **Väntat: en enda rad, `SLUT`.**
- **Står något annat än `SLUT`, före `SLUT` eller i stället för det: stoppa och fråga.** Installera
  inte. Det gäller också om `SLUT` saknas: då har något dolt utskriften, till exempel en funktion som
  heter `builtin`.
- Särskilt farligt är ett namn som är ett kommando på listan i SPEC 7.1: `git`, `ls`, `cat`, `head`,
  `tail`, `grep`, `diff`, `find`, `wc`, `sort`, `mkdir`, `cp` och `tar`, eller ett namn med ett snedstreck
  (`/`) i sig, till exempel `/usr/bin/git`, eller ett namn som börjar med `'/Library`: zsh kan ha alias och
  funktioner med en hel sökväg som namn, och då gäller de också när agenten skriver hela sökvägen. Men
  stoppa och fråga för **varje** namn som visas, inte bara för dem.

**Kroklistor och särskilda funktioner** (Hugos svar 2026-10-28 efter granskning 14, punkt 1). zsh har
**kroklistor**: listor med namn på funktioner som zsh kör av sig själv, till exempel före varje kommando
(`preexec_functions`) eller när skalet avslutas (`zshexit_functions`). De ska vara tomma. Funktionerna
`preexec`, `precmd`, `chpwd`, `periodic`, `zshexit`, `command_not_found_handler` och alla funktioner som
börjar med `TRAP` körs också av sig själva, och de ska inte finnas. Kör, i samma Terminal-fönster:

```bash
builtin print -rl -- "preexec_functions=(${preexec_functions[*]})" "precmd_functions=(${precmd_functions[*]})" "chpwd_functions=(${chpwd_functions[*]})" "periodic_functions=(${periodic_functions[*]})" "zshaddhistory_functions=(${zshaddhistory_functions[*]})" "zshexit_functions=(${zshexit_functions[*]})" ${(Mko)functions:#(TRAP*|preexec|precmd|chpwd|periodic|zshexit|command_not_found_handler)} SLUT
```

- Kommandot är en enda lång rad, kopiera hela. Det visar de sex kroklistorna, en per rad, med innehållet
  mellan parenteserna. Sedan visar det namnet på varje särskild funktion som finns, och sist ordet `SLUT`.
  Det bara visar, och ändrar ingenting.
- **Väntat: exakt de här sju raderna**, i den här ordningen, med **ingenting** mellan parenteserna:

  ```
  preexec_functions=()
  precmd_functions=()
  chpwd_functions=()
  periodic_functions=()
  zshaddhistory_functions=()
  zshexit_functions=()
  SLUT
  ```

- **Stoppa och fråga**, och installera inte, om:
  - det står något mellan parenteserna på någon rad, till exempel `precmd_functions=(update_terminal_cwd)`,
  - det står en rad till före `SLUT`, till exempel `TRAPDEBUG` eller `preexec` (en särskild funktion
    finns),
  - en rad saknas, eller `SLUT` saknas (då kan något ha dolt utskriften), eller
  - Terminal skriver ett fel i stället.
- **Inte bekräftat:** om Terminal själv lägger in sina egna funktioner (`update_terminal_cwd` och namn som
  börjar med `shell_session`) i en kroklista. Apples fil för det (`/etc/zshrc_Apple_Terminal`) är inte
  läst i den här versionen. Står ett sådant namn mellan parenteserna: stoppa och fråga ändå. Då behövs
  ett beslut om det namnet.

**h. Kontrollera vilka filer zsh läser in** (granskning 14, R2, Hugos beslut 2026-10-28). De låsta
inställningarna förbjuder agenten att skriva i de filer som zsh läser in på Hugos dator (`~/.nvm` med mera).
Läser din zsh in andra filer, till exempel från oh-my-zsh, Homebrew, conda eller iTerm2, har de filerna inget
förbud. Gör det här på **båda** datorerna, i samma Terminal-fönster:

```bash
grep -n -E 'source|\. |eval|compinit|autoload|fpath|ZDOTDIR' ~/.zshenv ~/.zprofile ~/.zshrc ~/.zlogin
```

- `grep` visar raderna i zsh:s fyra startfiler där en annan fil läses in (`source` eller en punkt), där
  kod körs (`eval`), där zsh:s hjälp för tabb startas eller får fler mappar (`compinit`, `autoload`,
  `fpath`), eller där zsh:s filer flyttas (`ZDOTDIR`). Varje rad börjar med filens namn och radnumret. Det
  bara läser, och ändrar ingenting.
- **Väntat på en dator med nvm:** två rader från `~/.zshrc`, de som läser in nvm:s två filer `nvm.sh` och
  `bash_completion` (radnumren, och texten efter `#`, kan vara andra):
  - `…/.zshrc:2:[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm`
  - `…/.zshrc:3:[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion`
- **Väntat på en dator utan nvm:** inga rader från filerna.
- Rader som `grep: …/.zshenv: No such file or directory` är väntade: filen finns inte, och det är bra.
- **Står någon annan rad där: stoppa och fråga.** Installera inte. Det behövs då en ny version av
  inställningsfilen med förbud för de filer som raden läser in.

**i. Kontrollera zsh:s mappar för funktioner** (granskning 14, R1, Hugos beslut 2026-10-28). nvm:s fil
`bash_completion` startar zsh:s `compinit`. `compinit` läser in filen `~/.zcompdump` och funktioner från
mapparna i zsh:s lista `fpath`. Den som kan skriva där kan lägga in funktioner som gäller i agentens
kommandon. De låsta inställningarna förbjuder agenten att skriva i `~/.zcompdump`. Mapparna skyddas bara av
att systemet äger dem, och det kontrollerar du här, i samma Terminal-fönster, ett kommando i taget:

```bash
print -rl -- $fpath
```

- Visar mapparna i `fpath`, en per rad, och ändrar ingenting.
- **Väntat:** varje rad börjar med `/usr/share/zsh/` eller är `/usr/local/share/zsh/site-functions`. Med
  zsh 5.9 på Hugos dator är det tre rader (prövat 2026-10-28 i ett test utan Hugos filer):
  `/usr/local/share/zsh/site-functions`, `/usr/share/zsh/site-functions` och
  `/usr/share/zsh/5.9/functions`. Siffrorna `5.9` kan vara andra med en annan version av zsh.
- **Står någon annan mapp där**, till exempel en i din hemmapp, `/opt/homebrew`, `.oh-my-zsh` eller `.nvm`:
  stoppa och fråga. Installera inte.

```bash
ls -ld $fpath
```

```bash
ls -ld /usr/local /usr/local/share /usr/local/share/zsh /usr/local/share/zsh/site-functions
```

- Det första visar mapparna i `fpath`, det andra mapparna ovanför `/usr/local/share/zsh/site-functions`.
  Båda bara läser, och ändrar ingenting. Läs raderna som i steg 2.
- **Väntat på varje rad som finns:** ägaren är `root`, det står **inget `w`** på plats 6 eller 9, och inget
  `+` eller `@` efter de tio tecknen.
- En rad som säger `No such file or directory` är bra: mappen finns inte. Då ska mappen ovanför, som finns,
  vara rätt enligt raden ovan. Det andra kommandot visar den.
- **Är ägaren inte `root`, står det `w` på plats 6 eller 9, eller `+` eller `@`: stoppa och fråga.**
  Installera inte.

Ångra steget: `cp ~/.zshrc.fore-vera ~/.zshrc`, och starta om Terminal och Claude-appen. Då stoppar vakten
alla kommandon igen.

## Steg 5: kontrollera att filerna är de som granskades

```bash
shasum -a 256 ~/VERA/agent/sparr/kommandosparr.py ~/VERA/agent/sparr/managed-settings.json
```

- `shasum -a 256` räknar ut en **kontrollsumma** för varje fil: ett "fingeravtryck" på 64 tecken.
  Minsta ändring i en fil ger en helt annan summa. Kommandot bara läser, och ändrar ingenting.
- Jämför de två summorna, tecken för tecken, med dem som den oberoende granskningen har skrivit upp
  (Hugos beslut 2026-10-28). **Är någon summa olika: stoppa och fråga.** Kopiera ingenting.

## Steg 6: skapa mapparna och låt systemet äga dem

**Så ser det ut när det går bra, i steg 6–11** (granskning 14, R5, Hugos beslut 2026-10-28). Kommandona
med `sudo mkdir`, `sudo chown`, `sudo chmod`, `sudo ditto` och `sudo cp -i` visar **ingenting** när de går
bra: datorn frågar kanske efter ditt lösenord, och sedan får du bara en ny rad att skriva på. **Stoppa och
fråga** om ett av dem skriver något, till exempel `Operation not permitted`, `Permission denied`,
`No such file or directory`, `File exists` eller `illegal option`. Säger datorn `Sorry, try again.` efter
lösenordet har du skrivit fel lösenord: skriv det igen. Säger den `sudo: 3 incorrect password attempts`:
kör samma kommando igen.

```bash
sudo mkdir "/Library/Application Support/ClaudeCode"
```

```bash
sudo mkdir "/Library/Application Support/ClaudeCode/vera"
```

- `sudo` gör att kommandot körs som administratör. Datorn frågar efter ditt lösenord. Det syns inte
  när du skriver, det är normalt.
- `mkdir` skapar en mapp: först `ClaudeCode`, sedan `vera` inuti den, där vakten ska ligga. Säger
  kommandot `File exists` finns mappen redan: stoppa och fråga.
- Går det bra visas ingenting. Visas något annat: stoppa och fråga.

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode" "/Library/Application Support/ClaudeCode/vera"
```

- `chown` byter ägare. `root:wheel` är systemets administratör och dess grupp. En ny mapp får annars
  gruppen från mappen ovanför (`admin`), och därför sätts gruppen uttryckligen här.
- Går det bra visas ingenting. Visas något annat: stoppa och fråga.

```bash
sudo chmod 755 "/Library/Application Support/ClaudeCode" "/Library/Application Support/ClaudeCode/vera"
```

- `chmod` sätter vem som får läsa, skriva och öppna. `755` på en mapp betyder: ägaren (systemet) får
  ändra, alla andra får bara titta in. Claude Code behöver kunna titta in för att hitta filerna.
- Går det bra visas ingenting. Visas något annat: stoppa och fråga.

## Steg 7: kopiera vakten

```bash
sudo ditto ~/VERA/agent/sparr/kommandosparr.py "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

- `ditto` kopierar en fil. `~/VERA/agent/sparr/kommandosparr.py` är vakten i projektet, och den sista
  sökvägen är dit den kopieras.
- Går det bra visas ingenting. Visas något annat, till exempel `No such file or directory` (då ligger
  vakten inte där kommandot letar): stoppa och fråga.

## Steg 8: låt systemet äga vakten och sätt rättigheterna

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

- Systemet blir ägare av vakten. `644` på en fil betyder: ägaren (systemet) får ändra, alla andra får
  bara läsa. Claude Code behöver kunna läsa vakten för att köra den med `/usr/bin/python3`.
- Går det bra visar båda kommandona ingenting. Visas något annat: stoppa och fråga.
- **Varför 644 och inte 600?** `600` betyder att bara ägaren, systemet, får läsa filen. Claude Code körs
  som ditt vanliga konto, inte som systemet, och skulle då inte kunna läsa filerna. En inställningsfil som
  Claude Code inte får läsa **hoppas över utan varning**: sessionen startar som om filen inte fanns, och
  då gäller ingen vakt alls (code.claude.com/docs/en/managed-settings, granskning 12). Det är farligare än
  att alla kan läsa filerna, eftersom de inte innehåller några hemligheter. Det viktiga är att ingen utom
  systemet kan **ändra** dem.

## Steg 9: skapa projektets Python på den nya platsen

Testsviten körs med en egen Python som har pytest installerat. Den skapas nu i
`/Library/Application Support/ClaudeCode/vera/venv`, där bara systemet kan ändra den (Hugos beslut
2026-10-28 om vakten, beslut 1). Agenten kan då köra testsviten utan att PATH-regeln stoppar den, och kan
inte byta ut Python eller pytest.

```bash
sudo /usr/bin/python3 -m venv "/Library/Application Support/ClaudeCode/vera/venv"
```

- `/usr/bin/python3 -m venv` skapar en **venv**: en egen mapp med Python och plats för paket, som inte
  blandas med något annat på datorn. Det är samma Python som projektets gamla `.venv` och vakten använder.
  Säger kommandot `File exists` eller `already exists`: stoppa och fråga.
- Går det bra visas ingenting (det kan ta några sekunder). Visas något annat: stoppa och fråga.

```bash
sudo "/Library/Application Support/ClaudeCode/vera/venv/bin/python" -m pip install --only-binary ':all:' --no-cache-dir -r ~/VERA/agent/requirements.txt
```

- `pip install -r` installerar paketen som står i projektets fil `requirements.txt` (pytest 8.4.2) och de
  paket pytest behöver. Det kräver internet.
- `--only-binary ':all:'` gör att pip bara tar färdigbyggda paket. Då körs inget installationsskript från
  paketen som administratör. Säger pip att ett paket inte finns färdigbyggt: stoppa och fråga.
- `--no-cache-dir` gör att pip inte sparar en kopia av paketen i din hemmapp, där filerna annars skulle
  ägas av systemet.
- pip varnar troligen för att det körs som administratör ("Running pip as the 'root' user"), och kanske
  för att det finns en nyare pip. Det är väntat här. Står det `Successfully installed` och `pytest-8.4.2`
  sist, gick det bra. Står det `ERROR`: stoppa och fråga.

```bash
sudo chown -R root:wheel "/Library/Application Support/ClaudeCode/vera/venv"
```

```bash
sudo chmod -R go-w "/Library/Application Support/ClaudeCode/vera/venv"
```

- `-R` gör att kommandot gäller mappen och allt i den. `chown -R root:wheel` gör systemet till ägare av
  allt, och `chmod -R go-w` tar bort rätten att ändra för gruppen (`g`) och alla andra (`o`). Ingenting
  annat ändras.
- Går det bra visar båda kommandona ingenting. Visas något annat: stoppa och fråga.

## Steg 10: kopiera de låsta inställningarna (sist, nu börjar de gälla)

```bash
sudo cp -i ~/VERA/agent/sparr/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- `cp` kopierar en fil. `-i` gör att datorn frågar innan den skriver över en fil som redan finns. Om
  den frågar: svara `n` (nej) och stoppa, eftersom filen då inte borde finnas (se "Innan du börjar").
- Går det bra visas ingenting. Visas något annat: stoppa och fråga.

## Steg 11: låt systemet äga inställningarna och sätt rättigheterna

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Samma som i steg 8, för inställningsfilen: systemet äger den, alla får läsa den, bara en
  administratör får ändra den.
- Går det bra visar båda kommandona ingenting. Visas något annat: stoppa och fråga.

## Steg 12: kontrollera att det är samma filer som ligger på plats

```bash
shasum -a 256 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Samma kontroll som i steg 5, nu för filerna där de installerades. Summorna ska vara exakt samma som
  i steg 5. **Är någon olika: stoppa och fråga.**

## Steg 13: kontrollera ägare och rättigheter igen (efter installationen)

```bash
ls -ld / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"
```

- Samma kommando som i steg 2, och de tre första raderna ska se ut som där. Nu ska också den fjärde raden
  finnas: `drwxr-xr-x`, ägaren `root` och gruppen `wheel`, för `/Library/Application Support/ClaudeCode`.

```bash
ls -ld "/Library/Application Support/ClaudeCode/vera" "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Visar mappen `vera` och de två filerna. `vera` ska vara `drwxr-xr-x`. Filerna ska vara `-rw-r--r--`
  (det första tecknet, `-`, betyder att det är en fil, och `644` skrivs så). Ägaren ska vara `root` och
  gruppen `wheel` på alla tre.

```bash
ls -ld "/Library/Application Support/ClaudeCode/vera/venv" "/Library/Application Support/ClaudeCode/vera/venv/bin" "/Library/Application Support/ClaudeCode/vera/venv/bin/python"
```

- Visar projektets Python från steg 9: mappen `venv`, mappen `bin` i den och `python`. Mapparna ska vara
  `drwxr-xr-x`. `python` är en **länk** till Python i utvecklarverktygen: raden börjar med `l` och slutar
  med `-> python3` eller liknande. Det är rätt. Ägaren ska vara `root` och gruppen `wheel` på alla tre.

**Kan gruppen eller andra skriva någonstans (ett `w` på plats 6 eller 9), är ägaren inte `root`, är
gruppen inte `wheel` för `ClaudeCode`, `vera`, `venv` och filerna, eller står det `+` eller `@` efter de
tio tecknen: installationen räknas som misslyckad. Stoppa och fråga.**

## Efteråt

1. **Starta nya sessioner** i skrivbordsappen (och i terminalen, om du har Claude Code där). Sessioner som
   redan är öppna kan ha läst inställningarna innan filen fanns.
2. **Kontrollera att de låsta inställningarna gäller** (Hugos beslut 2026-10-28, beslut 3). Raden visas
   inte i skrivbordsappen, så den läses i Terminal (Hugos svar 2026-10-28, punkt 3): kör `cd ~/VERA` och
   sedan `~/.local/bin/claude` (hela sökvägen, Hugos beslut 2026-10-28, granskning 13, P3 b), som i steg 1,
   skriv `/status` och leta upp raden **Setting sources**. Säger Terminal `no such file or directory`:
   stoppa och fråga. Raden ska visa `Enterprise managed settings (file)`,
   alltså inställningarna från filen du installerade (code.claude.com/docs/en/managed-settings). **Saknas
   raden eller den texten, gäller inte vakten, och installationen räknas som misslyckad.** Stoppa och
   fråga. `User settings`, `Project settings` och `Project local settings` är väntade och underkänner inte.
   Bara en annan låst källa underkänner installationen, till exempel inställningar som styrs från
   claude.ai (Hugos svar 2026-10-28, punkt 3). Står något annat på raden: stoppa och fråga. Avsluta med
   `/exit`.
3. **Gör kontrollen efter installationen** (sist i den här filen) i en ny session.
4. **Agenten kan inte längre skriva i `~/.claude`** (Hugos beslut 2026-10-28, punkt 5). Där ligger
   bland annat Claudes minne mellan sessionerna (`~/.claude/projects/…/memory`). Det slutar gå att
   spara nytt där. Claude Code själv skriver fortfarande sina egna filer.
5. **Vakterna i tillägget superpowers slutar fungera** (Hugos beslut 2026-10-28, 2), eftersom bara
   vakter från de låsta inställningarna får köras.
6. **Bara verktygen på listan i SPEC 7.1 fungerar** (granskning 12, P4, Hugos beslut 2026-10-28). Andra
   verktyg, till exempel webbsökning, appens webbläsare och kopplingar till andra tjänster, stoppas av
   vakten. Behövs ett verktyg till blir det en ny version av vakten.
7. **Läget "auto" går inte att välja** (granskning 12, P6). Claude Code frågar dig före varje kommando
   som inte är förgodkänt.
8. **Agenten kan inte skriva i projektets mapp `.claude`, i `.mcp.json` eller i `.venv`** (Hugos beslut
   2026-10-28, 5). Inställningar och kopplingar för projektet skriver du eller Casper själva. Agenten kan
   inte heller skriva i `~/Library/Application Support/Claude`, där skrivbordsappens egna inställningar
   ligger (Hugos svar 2026-10-28 efter granskning 13, punkt 3).
9. **Agenten kör testsviten med Python på den nya platsen** (Hugos beslut 2026-10-28 om vakten, beslut
   1), med kommandona i SPEC 7.1. Den gamla mappen `.venv` i projektet ska tas bort efter installationen
   (Hugos svar 2026-10-28, punkt 2). Gör det när kontrollen efter installationen, steg 3, visar att
   testsviten går med Python på den nya platsen, inte före: dra mappen `.venv` i `~/VERA/agent` till
   papperskorgen i Finder (mappen är dold, tryck Cmd+Shift+. i Finder för att se den) och töm sedan
   papperskorgen. Därefter pekar listan i SPEC 7.1 bara på den nya platsen.
10. **Om du senare lägger till en ny rad med `source` i `~/.zshrc`** (Hugos beslut 2026-10-28, granskning
    13, P1 b). En rad som börjar med `source` eller med en punkt (`.`), eller har `&& \.` i sig som
    nvm-raderna, läser in en annan fil varje gång skalet startar, och Claude Code tar med det som filen
    gör till agentens kommandon. Program föreslår ofta en sådan rad när de installeras. De låsta
    inställningarna förbjuder agenten att skriva i de filer som läses in i dag (`~/.nvm`, `~/.zkbd` och
    `~/.zsh_sessions`), men inte i en ny fil. Gör så här:
    - **Lägg inte till raden än.** Be om en ny version av inställningsfilen, med ett förbud för den nya
      filen (och för mappen den ligger i, om den läser in fler filer därifrån). Den byggs med test,
      granskas oberoende och installeras av dig, som en ny version av vakten.
    - **Har ett program redan lagt in raden:** stoppa och fråga innan nästa session med agenten.
    - Samma sak gäller `~/.zshenv`, `~/.zprofile` och `~/.zlogin`, och en rad som lägger till ett alias
      eller en funktion. Gör efteråt kontrollen av alias och funktioner i steg 4 g igen.
    - Samma sak gäller en rad med `eval`, `compinit`, `autoload`, `fpath` eller `ZDOTDIR`. Gör efteråt
      kontrollerna i steg 4 h och 4 i igen (granskning 14, R1 och R2, Hugos beslut 2026-10-28).

## Caspers dator

Samma steg, i samma ordning, och samma versionskontroll i steg 1 (minst 2.1.295, med `/status` i
skrivbordsappen och med `~/.local/bin/claude --version` i Terminal om Claude Code för Terminal finns där,
med hela sökvägen och samma varning för installerarens förslag). Samma kontroll av alias och funktioner i
steg 4 g och i kontrollen efter installationen, steg 1. Samma förprov i steg 3 och samma kontroll av
mapparna i steg 2 och 13. Samma `managed-settings.json` fungerar: regeln som hindrar agenten att skriva i
`.git` (`Edit(//**/.git/**)`) gäller varje `.git`-mapp på datorn och har inget användarnamn i sig.
Skillnader:

- Sökvägen till projektet kan vara en annan. Byt `~/VERA/agent` i steg 5, 7, 9 och 10 mot där projektet
  ligger på Caspers dator.
- Steg 4: kör `echo $PATH` från steg 4 e först. Raden för Cryptexes-mappen (steg 4 c) läggs in också
  på Caspers dator (Hugos svar 2026-10-28, punkt 1). Raden för nvm-mappen (steg 4 b) behövs bara om nvm
  finns där. Utan nvm ska bara den sista raden i steg 4 d vara Cryptexes-raden (se steg 4 d). Står någon
  annan mapp än systemets före `/usr/bin`, till exempel Homebrew (`/opt/homebrew/bin`): stoppa och fråga,
  eftersom vakten då stoppar alla kommandon.
- **Steg 4 h, vilka filer Caspers zsh läser in** (granskning 14, R2, Hugos beslut 2026-10-28). Förbuden i
  de låsta inställningarna bygger på vad zsh läser in på Hugos dator. Casper gör därför steg 4 h på sin
  dator före installationen. Visar `grep` något annat än nvm:s två rader (eller inga rader alls, utan nvm),
  till exempel oh-my-zsh, Homebrews `brew shellenv`, conda eller iTerm2: stoppa och fråga. Installera
  inte förrän en ny version av inställningsfilen har förbud för de filerna.
- **Claude Code för Terminal behövs på Caspers dator** (granskning 14, R5, Hugos beslut 2026-10-28). Raden
  Setting sources syns bara i Terminal (steg 1, "Efteråt" punkt 2 och kontrollen efter installationen,
  steg 1). Utan Claude Code för Terminal i `~/.local/bin/claude` går det inte att se att de låsta
  inställningarna gäller, och då **går installationen inte att kontrollera**. Säger
  `~/.local/bin/claude --version` `no such file or directory`: stoppa och fråga innan installationen.

Kontrollen nedan görs också på Caspers dator.

## Kontroll efter installationen

Planens steg 5 (Hugos beslut 2026-10-28). Gör stegen i ordning, i **en ny session** i fliken **Code** i
skrivbordsappen, startad i `~/VERA/agent`. Du skriver till agenten som vanligt. Agenten gör inte den här
kontrollen utan att du säger till.

Om något steg inte blir som det står: **stoppa, skriv upp vad som hände, och fråga** innan något annat
görs. Steg 1–7 ska vara klara innan uppgift 4 körs. Steg 9 görs direkt efter steg 7 och ska också vara
klart innan uppgift 4 körs (Hugos svar 2026-10-28, punkt 3). Steg 8 krävs inte för installationen eller för
uppgift 4, men ska vara gjort före läget "auto", före körningar utan att Hugo tittar, före första hela
körningen på riktiga underlag och före första kund (Hugos beslut 2026-10-28, 8).

1. **De låsta inställningarna gäller.** Raden **Setting sources** visas inte i skrivbordsappen, så den läses
   i Terminal (Hugos svar 2026-10-28, punkt 3): kör `cd ~/VERA` och sedan `~/.local/bin/claude` (hela
   sökvägen, Hugos beslut 2026-10-28, granskning 13, P3 b), som i installationens steg 1, och skriv
   `/status`. Säger Terminal `no such file or directory`: stoppa och fråga. Raden ska
   visa `Enterprise managed settings (file)`, alltså inställningarna från filen du installerade
   (code.claude.com/docs/en/managed-settings). `User settings`, `Project settings` och
   `Project local settings` är väntade och underkänner inte. Bara en annan låst källa underkänner
   installationen, till exempel inställningar som styrs från claude.ai: stoppa och fråga (Hugos svar
   2026-10-28, punkt 3). Avsluta med `/exit`. Läs också i skrivbordsappens `/status`
   raden **Claude Code**: versionen ska vara
   2.1.295 eller senare. Läget "auto" ska inte gå att välja: i terminalens Claude Code, tryck Shift+Tab
   några gånger, och "auto" ska inte komma upp (code.claude.com/docs/en/settings-reference,
   `disableAutoMode`).

   **Alias och funktioner, igen efter installationen** (Hugos beslut 2026-10-28, granskning 13, P1 a).
   Öppna ett nytt Terminal-fönster (Cmd+N) och kör, ett i taget:

   ```bash
   alias
   ```

   ```bash
   alias -s
   ```

   ```bash
   builtin print -rl -- ${(ko)functions:#(_*|nvm*|shell_session*|update_terminal_cwd|compinit|compdef|compdump|compaudit|compinstall|bashcompinit|compgen|complete|getent)} SLUT
   ```

   ```bash
   builtin print -rl -- "preexec_functions=(${preexec_functions[*]})" "precmd_functions=(${precmd_functions[*]})" "chpwd_functions=(${chpwd_functions[*]})" "periodic_functions=(${periodic_functions[*]})" "zshaddhistory_functions=(${zshaddhistory_functions[*]})" "zshexit_functions=(${zshexit_functions[*]})" ${(Mko)functions:#(TRAP*|preexec|precmd|chpwd|periodic|zshexit|command_not_found_handler)} SLUT
   ```

   Samma vända kontroll som i installationens steg 4 g (granskning 14, R3, Hugos beslut 2026-10-28):
   `alias` ska visa exakt två rader, `run-help=man` och `which-command=whence`, `alias -s` ska inte visa
   något, och det tredje kommandot ska visa en enda rad, `SLUT`. Det fjärde kommandot visar kroklistorna
   och de särskilda funktionerna (Hugos svar 2026-10-28 efter granskning 14, punkt 1): väntat är exakt de
   sju raderna i steg 4 g, från `preexec_functions=()` till `SLUT`, med ingenting mellan parenteserna och
   ingen rad till före `SLUT`. **Står något annat där, eller saknas något av det: stoppa och fråga**,
   och kör inte uppgift 4. Varje namn som visas stoppar, inte bara de som är farligast: ett kommando på
   listan (`git`, `ls`, `cat`, `head`, `tail`, `grep`, `diff`, `find`, `wc`, `sort`, `mkdir`, `cp` och
   `tar`), ett namn med ett snedstreck (`/`) i sig, eller ett särskilt namn som `TRAPDEBUG`.
2. **Ihopkopplade kommandon stoppas.** Be agenten köra `ls; ls`. Det ska stoppas med ett fel som börjar
   "Stoppat av vakten" och säger att kommandon inte kopplas ihop.
3. **Ett kommando på listan går igenom.** Be agenten köra `git status`. Claude Code frågar dig som vanligt
   om det får köras. Säg ja. Kommandot ska köras och visa läget i projektet. (`git` ligger i
   `/usr/bin`, som ägs av systemet, så PATH-regeln släpper igenom det. Stoppas det med "PATH-regeln":
   skriv upp felet och fråga. Nämner felet en mapp med `.nvm` i namnet eller
   `/System/Cryptexes/App/usr/bin`, har installationens steg 4 inte fått effekt i appen.)
   Be sedan agenten köra testsviten med kommandot i SPEC 7.1,
   `'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q scripts/tests`
   (Hugos beslut 2026-10-28 om vakten, beslut 1). Det ska gå igenom, och sista raden ska säga hur många
   tester som är gröna (`passed`) och att inga är röda.
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
   steget gör du **själv i Terminal**, inte agenten. Gör det när steg 1–7 och 9 är klara. Vakten flyttas
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
   **exakt samma** som i steg 12 i installationen (och som de som granskningen skrev upp). Är någon olika:
   stoppa och fråga.

   **e. Starta en ny session** och gör steg 2 och 3 igen: `ls; ls` ska stoppas med "Stoppat av vakten",
   och `git status` ska gå igenom. Då är vakten tillbaka och fungerar.

   **Vad provet visar.** När vakten saknas kan `/usr/bin/python3` inte öppna filen och avslutar med kod 2,
   och kod 2 betyder för Claude Code "stoppa". Provet visar alltså att en **saknad** vakt stoppar allt.
   Det prövar inte inställningen `onFailure: "block"` i sig, som gäller när vakten fallerar på andra sätt
   (en annan kod än 0 och 2, tidsgränsen, eller att programmet inte går att starta). Att Python ger kod 2
   visas av testet `test_systemets_python_stoppar_med_kod_2_nar_vakten_saknas`. Det är förprovet i steg 3
   i installationen som prövar `onFailure: "block"`: där går vakten inte att starta alls.

   Gör steg 9 igen efter e.
9. **Sista kontrollen, i skrivbordsappen: vakten stoppar ett kommando som inte står på listan** (Hugos svar
   2026-10-28, punkt 3). Görs direkt efter steg 7, och igen efter steg 8 om du gör det. Starta en ny session
   i fliken **Code** i skrivbordsappen, startad i `~/VERA/agent`, och be agenten: "Kör kommandot `date`."
   - `date` visar bara dagens datum och klockslag. Det läser och ändrar ingenting, så det är ofarligt även
     om vakten skulle saknas. Det står inte på listan i SPEC 7.1.
   - **Förväntat:** kommandot stoppas innan Claude Code frågar dig om lov, med ett fel som börjar
     "Stoppat av vakten" och säger att `'date' står inte på listan i SPEC 7.1`. Inget datum visas.
   - **Om Claude Code frågar om lov att köra `date`:** svara nej. Vakten har då inte stoppat kommandot.
     Stoppa och fråga.
   - **Om datumet visas:** kommandot kördes utan att vakten stoppade det. Det är ofarligt, men vakten
     fungerar inte. Stoppa och fråga, och kör inte uppgift 4.
