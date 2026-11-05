# Installera vakten för kommandolistan

Vilka beslut som har ändrat filen, och när, står i `GRANSKNING.md` under "Hugos svar 2026-10-28 efter
granskning 15", "Historiken i INSTALLERA.md".

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
| `sparr/managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` | **De låsta inställningarna.** De säger åt Claude Code att köra vakten, att stoppa kommandot om vakten kraschar eller inte svarar, och att bara vakter och regler härifrån gäller. En Claude Code som är äldre än 2.1.305 startar inte alls. Agenten får inte skriva i `.git` (varken mappen eller filen, på varje djup), i skalets och gits startfiler, i `~/.claude`, i `~/Library/LaunchAgents`, i `~/.ssh`, i `.mcp.json`, i någon mapp `.claude` (också projektets), i `~/.claude.json`, i `~/bin`, `~/.local/bin` och `/opt/homebrew`, eller i någon mapp `.venv`. Inte heller i filerna som zsh läser när det startar och de filer som de läser in: nvm-mappen `~/.nvm`, `~/.zkbd`, `~/.zsh_sessions`, `~/.zlogout` och systemets zsh-filer i `/etc` (granskning 13, P1 b), och `~/.zcompdump`,
som zsh:s `compinit` läser in vid start (granskning 14, R1), eller i den kompilerade versionen (`.zwc`) av någon av zsh:s startfiler eller av `~/.zcompdump`, som zsh läser i stället för filen (granskning 15, S2). Inte heller i Claude Code för Terminal (`~/.local/bin/claude` och `~/.local/share/claude`), i skrivbordsappens egen Claude Code (`~/Library/Application Support/Claude/claude-code`) eller i appen (`/Applications/Claude.app`) (granskning 13, P4 a). Inte heller någonstans i hela `~/Library/Application Support/Claude`, där också skrivbordsappens egna inställningar ligger (Hugos svar 2026-10-28 efter granskning 13, punkt 3). Inte heller i en fil som heter `.ugrep`, i någon mapp, som är inställningsfilen för det program som `grep` kör i agentens skal (granskning 16, G7). Läget "auto" går att använda, och skills kan inte köra skalkommandon. |
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
vakten, beslut 1).

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
2.1.305 eller senare. Först appen, med `/status` (Hugos beslut 2026-10-28, beslut 3):

1. Öppna Claude-appen, gå till fliken **Code** och starta en ny session, till exempel i `~/VERA/agent`.
2. Skriv `/status` i rutan där du skriver till Claude och tryck Retur. `/status` är ett kommando till
   Claude Code, inte till Terminal. Det visar bland annat versionen och var inställningarna kommer ifrån,
   och ändrar ingenting.
3. Läs raden **Claude Code**. Den visar versionen, till exempel `2.1.310`. Jämför siffergrupperna mellan
   punkterna en i taget, från vänster: `2.1.310` och `2.2.0` är senare än `2.1.305`, men `2.1.30` är
   äldre (30 är mindre än 305).
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
>   stoppar då **alla** kommandon (PATH-regeln, Hugos beslut 2026-10-28 om vakten,
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
  Versionen ska vara 2.1.305 eller senare (jämför som i punkt 3 ovan).
- Säger Terminal `no such file or directory`: Claude Code för Terminal ligger inte där. Stoppa och fråga.

**Om versionen i Terminal är äldre än 2.1.305**, uppdatera:

```bash
~/.local/bin/claude update
```

- Hämtar och installerar den senaste versionen av Claude Code för Terminal (det kräver internet). Det ska
  stå `Successfully updated from … to version …` eller `Claude Code is up to date (…)`. Kör sedan
  versionskommandot ovan igen. Är versionen fortfarande äldre än 2.1.305: stoppa och fråga.

**Raden Setting sources, i Terminal** (Hugos svar 2026-10-28, punkt 3, och Hugos beslut 2026-10-28,
granskning 13, P3 b, som ersätter `claude` med hela sökvägen). Kör ett kommando i taget:

```bash
cd ~/VERA/agent
```

```bash
~/.local/bin/claude
```

- Det första gör projektets mapp, `~/VERA/agent`, till mappen du står i. Det andra startar Claude Code för Terminal, i
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

**Om appens version är äldre än 2.1.305: stoppa och uppdatera först.**

1. Klicka på **Claude** i menyraden överst på skärmen (när Claude-appen är aktiv) och välj **Check for
   Updates…**. Installera uppdateringen om det finns en.
2. Avsluta appen helt (**Claude > Quit Claude**, eller Cmd+Q) och öppna den igen.
3. Starta en ny session och gör `/status` igen.
4. Gå vidare först när versionen är minst 2.1.305. Säger appen att den redan är senaste versionen, men
   versionen fortfarande är äldre än 2.1.305: stoppa och fråga.

Terminalen och skrivbordsappen har **var sin** Claude Code med var sitt versionsnummer, och att uppdatera
den ena uppdaterar inte den andra. Kontrollera därför versionen i båda: i appen med `/status` och i Terminal med
versionskommandot ovan, innan du installerar vakten.

De låsta inställningarna innehåller också `"requiredMinimumVersion": "2.1.305"`, så att en äldre Claude
Code inte startar alls efter installationen (Hugos beslut 2026-11-05 efter P6). Kontrollen här behövs ändå,
eftersom inställningarna inte gäller förrän de är installerade.

En inställning har ingen lägsta version i dokumentationen: `disableSkillShellExecution` (skills kör inga
skalkommandon). Sidorna **code.claude.com/docs/en/settings-reference**, **/skills** och **/permissions** nämner
ingen version för den, kontrollerat 2026-10-28. Lägsta version är alltså **inte bekräftat** (Hugos beslut
2026-10-28: byggs in ändå). `disableAutoMode` är borttagen (Hugos beslut 2026-10-29).

## Steg 2: kontrollera mapparna ovanför (före installationen)

Vakten och inställningarna skyddas av att bara systemet kan ändra mappen `ClaudeCode`. Det skyddet gäller
bara om ingen annan heller kan ändra mapparna ovanför, eftersom den som kan ändra en mapp kan flytta undan
allt som ligger i den (granskning 12, P7, Hugos beslut 2026-10-28, beslut 3).

```bash
ls -lde@ / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"
```

- `ls` visar en rad per mapp: vem som äger mappen och vem som får ändra i den. `e@` gör att varje
  extra uppgift och varje extra rättighet visas på en egen, indragen rad direkt under. Det bara läser, och
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
- **Extra uppgifter och rättigheter** (Hugos beslut 2026-10-28 kväll, samma regel som H1). Titta på tecknet
  direkt efter de tio tecknen, och på de indragna raderna under:
  - Står det **inget** där, och ingen indragen rad under: rätt.
  - Står det `@` (till exempel `drwxr-xr-x@`), och under står **exakt en** indragen rad som börjar med
    `com.apple.provenance` och sedan bara en siffra (till exempel `com.apple.provenance   11`): rätt. Den
    uppgiften sätter macOS själv, och den ger inga rättigheter.
  - **Allt annat: stoppa och fråga.** Till exempel `+` efter de tio tecknen (det betyder alltid extra
    rättigheter), ett annat namn på den indragna raden (till exempel `com.apple.quarantine` eller
    `com.apple.provenance2`), mer än en indragen rad, eller en indragen rad som börjar med en siffra och kolon
    (till exempel `0: group:everyone deny delete`, som är en extra rättighet).

**Kan gruppen eller andra skriva någonstans i kedjan, är ägaren inte `root`, eller finns `ClaudeCode`
redan: avbryt installationen och fråga.**

## Steg 2 b: kontrollera Python som vakten körs med (före installationen)

De låsta inställningarna startar vakten med Python i Apples **utvecklarverktyg** (Command Line Tools, program
för den som programmerar), med hela sökvägen och `-I` (granskning 19, J1, Hugos beslut 2026-10-28). Kan någon
byta ut den Pythonen utan lösenord, kan vakten ändras utan att den märker det. Går den inte att starta, stoppar
Claude Code allt (`"onFailure": "block"`, steg 1). Kommandona **bara visar**, ändrar ingenting och kräver inget
lösenord. Gör steget på varje dator där vakten installeras.

**a. Versionen:**

```bash
/Library/Developer/CommandLineTools/usr/bin/python3 --version
```

- **Rätt:** en enda rad, `Python 3.`, ett tal som är **9 eller större**, en punkt och ett tal, till exempel
  `Python 3.9.6` (din dator 2026-10-28) eller `Python 3.12.1`. Alltså 3.9 eller nyare: `3.10` är nyare än `3.9`.
- **Fel: stoppa och fråga.** Till exempel `no such file or directory` (utvecklarverktygen saknas), en version
  äldre än `3.9` (som `Python 3.8.9`), en ruta som vill installera något (svara inte ja), eller annan text.

**b. Ägare och rättigheter för filen, filen den leder till och alla mappar ovanför** (en enda lång rad):

```bash
f=/Library/Developer/CommandLineTools/usr/bin/python3; for p in $f ${f:A}; do while true; do ls -lde@ $p; [[ $p == / ]] && break; p=${p:h}; done; done
```

- `${f:A}` är sökvägen dit filen till sist leder, efter alla **länkar** (hänvisningar till en fil någon
  annanstans). Kommandot visar (som i steg 2) filen och varje mapp ovanför den upp till `/`, och
  sedan samma sak för filen dit länkarna leder. Två omgångar alltså. Börjar första raden med `l` är filen en
  länk (raden slutar med `->` och vart den pekar). Börjar den med `-` är omgångarna likadana. Båda är rätt.
- **Varje rad**, i båda omgångarna, ska följa samma regel som i steg 2: ägaren är `root`, det står **inget `w`**
  på plats 6 (gruppen) eller plats 9 (alla andra), till exempel `drwxr-xr-x` eller `lrwxr-xr-x`, och extra
  uppgifter följer regeln där (bara `@` med exakt en indragen rad `com.apple.provenance` och en siffra är rätt,
  och `+` efter de tio tecknen stoppar alltid). Gruppen får vara `wheel` eller `admin`.
- **Första raden i andra omgången** är filen dit länkarna leder. Dess sökväg (sist på raden) ska börja med
  `/Library/Developer/CommandLineTools/`, inte till exempel `/Applications/Xcode.app` eller din hemmapp.
- **Fel: stoppa och fråga.** Ägaren är inte `root`, `w` på plats 6 eller 9, `No such file or directory`, ett fel
  från Terminal, eller något annat än det som står här.

**Visar a eller b något annat än det som står här: installera inte, och fråga.**

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

- `echo` skriver ut texten mellan de enkla citattecknen, och `>` gör att texten hamnar i filen
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
Claude köra:

```
ls
```

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
- Kör sedan kommandot från a igen. Det ska stå `No such file or directory`.

**Stoppades `ls` inte i e: avbryt installationen.** Gå vidare till steg 4 bara om `ls` stoppades.

## Steg 4: flytta nvm-mappen och Cryptexes-mappen sist i PATH, och kontrollera skalet: alias, funktioner och zsh:s filer (före installationen)

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
**alla** kommandon. Med båda mapparna sist går alla program på listan igenom
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

- `echo` skriver ut texten mellan de enkla citattecknen, och `>>` (två större än-tecken) lägger
  texten **sist** i filen. Med bara ett `>` skulle hela filen ersättas, så kopiera kommandot exakt. Har
  det ändå blivit fel: ångra (rutan sist i steg 4), och fråga.
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
- Står något annat där, eller står en rad två gånger: ångra (rutan sist i steg 4), och fråga.

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
3, ska kommandot gå igenom.

**g. Kontrollera skalet i Terminal med kontrollskriptet** (Hugos beslut 2026-10-28 efter granskning 15).
Claude Code läser in `~/.zshrc` när en session startar, och tar med sig **alias** (ett kortnamn som skalet
byter ut mot ett annat kommando) och **funktioner** (små program som skrivs direkt i skalet) till varje
kommando som agenten kör. Vakten ser dem inte. zsh kör också vissa funktioner av sig själv, till exempel de i
**kroklistorna** (listor med funktioner som körs före varje kommando eller när skalet avslutas), och läser
in andra filer från sina **startfiler**. Allt det kontrolleras av ett skript i projektet,
`sparr/kontrollera-skalet.zsh`. Skriptet bara läser, och ändrar ingenting. Det kontrollerar att det bara
finns väntade alias, funktioner och kroklistor (granskning 13, P1 a, granskning 14, R3, och Hugos svar
2026-10-28 efter granskning 14, punkt 1), att zsh:s mappar för funktioner (`fpath`) bara är zsh:s egna och
ägs av systemet (granskning 14, R1), att startfilerna bara läser in nvm:s två filer (granskning 14, R2), och
att det inte finns någon kompilerad startfil (`.zwc`, granskning 15, S2). Kontrollen är **vänd**: allt som
inte är väntat avviker, också sådant som verkar ofarligt.

**Terminals egna funktioner** (Hugos beslut 2026-10-28 efter granskning 15, 8 d). I Terminal är exakt två
namn godkända i kroklistorna: `update_terminal_cwd` i `precmd_functions` (talar om för Terminal vilken mapp
skalet står i) och `shell_session_update` i `zshexit_functions` (sparar fönstret när det stängs). Skriptet
kontrollerar med `whence -v` att båda kommer från Apples fil `/etc/zshrc_Apple_Terminal`, och med `ls`
att `/etc/zshrc` och `/etc/zshrc_Apple_Terminal` ägs av `root` och att varken gruppen eller andra kan
skriva i dem. Terminals fil läser också in zsh:s egen funktion `add-zsh-hook`. Den godtas bara om `whence -v`
visar att den kommer från zsh:s egen mapp, `/usr/share/zsh/<version>/functions/add-zsh-hook`, och filen ägs av
`root` utan skrivrätt för gruppen eller andra (Hugos beslut 2026-10-28 efter granskning 16, G4). Allt annat
avviker. Varje fil och mapp som skriptet prövar med `ls` får inte ha extra rättigheter (`+`). Den får ha en
enda extra uppgift (`@`), och bara om den heter exakt `com.apple.provenance`. Den uppgiften sätter macOS själv,
till exempel när någon gör ett andra namn på filen (Hugos beslut 2026-10-28 efter granskning 17, H1). Alla
andra uppgifter, och flera uppgifter samtidigt, avviker.

Gör det här i samma nya Terminal-fönster som i e, ett kommando i taget. Kontrollera först skriptets
kontrollsumma:

```bash
shasum -a 256 ~/VERA/agent/sparr/kontrollera-skalet.zsh
```

- Summan ska vara exakt (Hugos beslut 2026-10-28 efter granskning 15, ny summa efter Hugos beslut 2026-10-28
  efter granskning 17, H1, oförändrad efter granskning 18, I1, och granskning 19, J1):
  `10388d474a555e6d337a9468c5a1f5e2fd0ca04608e36024f73011dc5186d51f`
  Den oberoende granskningen bekräftar samma summa. **Är summan en annan: stoppa och fråga.** Kör inte
  skriptet.

Kör sedan skriptet:

```bash
source ~/VERA/agent/sparr/kontrollera-skalet.zsh
```

- `source` kör skriptet i det skal du står i, så att det ser just det skalets alias och funktioner.
- **Väntat: exakt två rader**, `OK` och sedan `SLUT`.
- **Står det en rad som börjar med `AVVIKER`: stoppa och fråga.** Installera inte. Raden säger vad som
  avviker, till exempel `AVVIKER: funktion: git` eller `AVVIKER: startfil: …`. Skicka raderna till den som
  hjälper dig.
- **Saknas `SLUT`, eller skriver Terminal ett fel: stoppa och fråga.** Då kan något ha dolt utskriften.

**h. Kontrollera agentens eget skal, i skrivbordsappen** (Hugos beslut 2026-10-28 efter granskning 15, S3).
Agenten kör sina kommandon i ett annat skal än Terminal. Där lägger Claude Code själv in fyra funktioner:
`find`, `grep`, `rg` och `pkill` (granskning 15). Kontrollen i g ser inte det skalet, så agenten kör en
fast kontroll i sitt eget skal. Det går bara **före** installationen: efter den stoppar vakten kommandot.

1. Starta en ny session i fliken **Code** i skrivbordsappen, i `~/VERA/agent`, i läget **Manual**.
2. Be agenten: "Kör exakt det här kommandot med Bash-verktyget, och ändra ingenting i det:" och klistra in
   kommandot nedan (en enda lång rad).

   ```bash
   builtin print -rl -- "preexec_functions=(${preexec_functions[*]})" "precmd_functions=(${precmd_functions[*]})" "chpwd_functions=(${chpwd_functions[*]})" "periodic_functions=(${periodic_functions[*]})" "zshaddhistory_functions=(${zshaddhistory_functions[*]})" "zshexit_functions=(${zshexit_functions[*]})" ${(ko)functions:#(_*|nvm*|shell_session*|update_terminal_cwd|compinit|compdef|compdump|compaudit|compinstall|bashcompinit|compgen|complete|getent)} SLUT
   ```

3. Claude Code frågar om lov. Jämför först kommandot i frågan med kommandot ovan, tecken för tecken. Är det
   samma: svara ja. Annars: svara nej, och stoppa och fråga.
4. Läs utskriften i **verktygsrutan** (rutan med kommandot och svaret), inte agentens sammanfattning. Det
   bara visar, och ändrar ingenting. **Väntat: exakt de här elva raderna**, i den här ordningen:

   ```
   preexec_functions=()
   precmd_functions=()
   chpwd_functions=()
   periodic_functions=()
   zshaddhistory_functions=()
   zshexit_functions=()
   find
   grep
   pkill
   rg
   SLUT
   ```

   De sex första raderna är kroklistorna, som ska vara tomma. Sedan kommer varje funktion som inte är
   väntad, och där ska bara Claude Codes fyra stå. En särskild funktion som zsh kör av sig själv, till
   exempel `TRAPDEBUG` eller `preexec`, skulle synas där.
5. **Visar verktygsrutan något annat än exakt de elva raderna, i den ordningen: stoppa och fråga, och
   installera inte** (granskning 16, G2, Hugos beslut 2026-10-28). Det gäller allt som inte är exakt de elva
   raderna, inte bara fallen som räknas upp här: till exempel raderna i en annan ordning, en rad för mycket
   (som samma namn två gånger) eller för lite, eller ett annat namn i en kroklista. Ser verktygsrutan ut att
   vara avkortad, öppna hela utskriften innan du jämför. **Stoppa och fråga** alltså bland annat om det står
   något mellan parenteserna, om det står något annat namn än `find`, `grep`, `pkill` och `rg`, om något av
   dem saknas, om `SLUT` saknas, om Claude Code vägrar köra kommandot, eller om verktygsrutan visar ett fel.
   **Inte bekräftat:** att Claude Code släpper igenom
   kommandot (granskning 15 såg att en inbyggd kontroll i Claude Code stoppade ett annat `print`-kommando),
   och att namnen är desamma i en annan version av Claude Code.

**Ångra steget** (hämtar tillbaka säkerhetskopian), och starta om Terminal och Claude-appen. Då stoppar vakten
alla kommandon igen.

```bash
cp ~/.zshrc.fore-vera ~/.zshrc
```

## Steg 5: kontrollera att filerna är de som granskades

```bash
shasum -a 256 ~/VERA/agent/sparr/kommandosparr.py ~/VERA/agent/sparr/managed-settings.json ~/VERA/agent/requirements.txt
```

- `shasum -a 256` räknar ut en **kontrollsumma** för varje fil: ett "fingeravtryck" på 64 tecken.
  Minsta ändring i en fil ger en helt annan summa. Kommandot bara läser, och ändrar ingenting.
- Jämför de tre summorna, tecken för tecken, med dem som den oberoende granskningen har skrivit upp
  (Hugos beslut 2026-10-28). `requirements.txt` är listan över paket som installeras i steg 9 (granskning
  15, S6, Hugos beslut 2026-10-28). **Är någon summa olika: stoppa och fråga.** Kopiera ingenting.
- Summorna ska vara exakt de här (2026-10-28 efter granskning 19, och 2026-11-05 för inställningarna). Den
  oberoende granskningen ska skriva upp samma summor. Skiljer granskningens summor från dessa: stoppa och fråga.
  - `sparr/kommandosparr.py`: `314df00b4239877d21e0fef7d8f11c844a75d07276ad0af32baa94db8e92d10d`
  - `sparr/managed-settings.json`: `1ba7457615356ff634956cf3f665787d2e74900986aa96001feeaa8ce31a39da`
  - `requirements.txt`: `bf4dc0555928a3facf67b3370001388d4b65e69a071c339f8b201310bde4486a`

## Steg 6: skapa mapparna och låt systemet äga dem

**Så ser det ut när det går bra, i steg 6–11** (granskning 14, R5, Hugos beslut 2026-10-28). Kommandona
med `mkdir`, `chown`, `chmod`, `ditto` och `cp` visar **ingenting** när de går
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
  bara läsa. Claude Code behöver kunna läsa vakten för att köra den med
  `/Library/Developer/CommandLineTools/usr/bin/python3` (steg 2 b).
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

- `-R` gör att kommandot gäller mappen och allt i den. `chown` gör systemet till ägare av
  allt, och `chmod` tar bort rätten att ändra för gruppen (`g`) och alla andra (`o`). Ingenting
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
shasum -a 256 "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json" ~/VERA/agent/requirements.txt
```

- Samma kontroll som i steg 5, nu för filerna där de installerades, och för `requirements.txt`, som steg 9
  installerade paketen från (granskning 15, S6). Summorna ska vara exakt samma som i steg 5. **Är någon
  olika: stoppa och fråga.**

## Steg 13: kontrollera ägare och rättigheter igen (efter installationen)

```bash
ls -lde@ / /Library "/Library/Application Support" "/Library/Application Support/ClaudeCode"
```

- Samma kommando som i steg 2, och de tre första raderna ska se ut som där. Nu ska också den fjärde raden
  finnas: `drwxr-xr-x`, ägaren `root` och gruppen `wheel`, för `/Library/Application Support/ClaudeCode`.

```bash
ls -lde@ "/Library/Application Support/ClaudeCode/vera" "/Library/Application Support/ClaudeCode/vera/kommandosparr.py" "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Visar mappen `vera` och de två filerna. `vera` ska vara `drwxr-xr-x`. Filerna ska vara `-rw-r--r--`
  (det första tecknet, `-`, betyder att det är en fil, och `644` skrivs så). Ägaren ska vara `root` och
  gruppen `wheel` på alla tre.

```bash
ls -lde@ "/Library/Application Support/ClaudeCode/vera/venv" "/Library/Application Support/ClaudeCode/vera/venv/bin" "/Library/Application Support/ClaudeCode/vera/venv/bin/python"
```

- Visar projektets Python från steg 9: mappen `venv`, mappen `bin` i den och `python`. Mapparna ska vara
  `drwxr-xr-x`. `python` är en **länk** till Python i utvecklarverktygen: raden börjar med `l` och slutar
  med `-> python3` eller liknande. Det är rätt. Ägaren ska vara `root` och gruppen `wheel` på alla tre.

- Filerna i projektet har uppgiften `com.apple.provenance`, och `ditto` och `cp` tar med den. Det är väntat
  att vakten och inställningarna har den här också.

**Kan gruppen eller andra skriva någonstans (ett `w` på plats 6 eller 9), är ägaren inte `root`, är
gruppen inte `wheel` för `ClaudeCode`, `vera`, `venv` och filerna, eller visar någon rad en extra uppgift
eller rättighet som inte är rätt enligt regeln i steg 2 (bara `@` med exakt en indragen rad
`com.apple.provenance` och en siffra är rätt, och `+` stoppar alltid): installationen räknas som misslyckad.
Stoppa och fråga.**

## Efteråt

1. **Starta nya sessioner** i skrivbordsappen (och i terminalen, om du har Claude Code där). Sessioner som
   redan är öppna kan ha läst inställningarna innan filen fanns.
2. **Kontrollera att de låsta inställningarna gäller** (Hugos beslut 2026-10-28, beslut 3). Raden visas
   inte i skrivbordsappen, så den läses i Terminal (Hugos svar 2026-10-28, punkt 3): kör de två rutorna under
   "Raden Setting sources" i steg 1 (hela sökvägen, Hugos beslut 2026-10-28, granskning 13, P3 b),
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
7. **Läget "auto" går att välja** (Hugos beslut 2026-10-29, `GRANSKNING.md`, "Beslut 2026-10-29 – Auto
   tillåts igen", med villkoren). Vakten körs ändå före varje verktyg.
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
    - Samma sak gäller `~/.zshenv`, `~/.zprofile` och `~/.zlogin`, en rad som lägger till ett alias eller
      en funktion, och en rad med `eval`, `compinit`, `autoload`, `fpath` eller `ZDOTDIR` (granskning 14, R1
      och R2, Hugos beslut 2026-10-28). Gör efteråt kontrollen med skriptet i steg 4 g igen.

## Byte av inställningsfil

Ny granskad `managed-settings.json`: kör steg 5 och 10–13 (svara `y` när steg 10 frågar), sedan kontrollen
steg 1, 2, 3, 9.

## Provkörning med sandlådan, före bytet (steg 15)

Den här provkörningen ska visa att testsviten är grön i sandlådan, med exakt samma `sandbox`-nyckel som `sparr/managed-settings.json`, också `filesystem` (Hugos beslut 2026-11-05 om granskning 39, beslut 2). Ett test jämför dem. Ingenting
installeras, inget kräver lösenord, och de låsta inställningarna är oförändrade. Sandlådan gäller bara den här sessionen.
Kör i programmet **Terminal**, ett kommando i taget:

```bash
cd ~/VERA/agent
```

```bash
~/.local/bin/claude --version
```

- Skriv upp versionen. Den behövs vid bytet nedan. Provkörningen 2026-11-05, del E, gjordes med 2.1.318 (`PROGRESS.md`).

```bash
~/.local/bin/claude --settings '{"sandbox":{"enabled":true,"failIfUnavailable":true,"allowUnsandboxedCommands":false,"autoAllowBashIfSandboxed":false,"excludedCommands":[],"enableWeakerNestedSandbox":false,"enableWeakerNetworkIsolation":false,"allowAppleEvents":false,"allowNestedUserNamespaces":false,"network":{"allowAllUnixSockets":false,"allowLocalBinding":false},"filesystem":{"denyWrite":["/Applications/Claude.app","~/Library/Application Support/Claude/claude-code","~/.local/share/claude"],"denyRead":["~/.ssh"]}}}'
```

Be sedan Claude: "Kör exakt det här kommandot med Bash-verktyget, och ändra ingenting i det:" och klistra in:

```
'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rfs scripts/tests
```

**Väntat på sista raden: inget `failed`, alltså inga röda, och `85 skipped`.** Skicka hela slutet av utskriften till sessionen som hjälper dig. **Är något test rött, eller är antalet ett annat: stoppa och fråga.**

Utskriften (`-rfs`) visar vilka som hoppas över, och varför:

- `GRUPP D HOPPAS ÖVER`: **38** prov (Hugos beslut 2026-11-05 om granskning 39, beslut 1). De skapar en mapp `.git`, `.venv` eller `.claude` i testets tillfälliga mapp, och det ska sandlådan stoppa. De hoppar över sig bara när datorn nekar med `Operation not permitted`. Alla andra fel ger rött. De körs i "Prov utanför sandlådan" nedan. `test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott` hör till gruppen men ska gå igenom här: den nekas inget själv, utan kör de andra i en kopia. Därför är det 38 och inte 39.
- `SPÄRRTESTET HOPPAS ÖVER`: **10** prov, och `SPÄRRPROVET I KOPIAN HOPPAS ÖVER`: **31** prov: väntat före bytet, eftersom sandlådan ännu inte står i de låsta inställningarna.
- `H1-PROVET HOPPAS ÖVER`: **6** prov. Väntat i Terminal: de hoppas över där också utan sandlåda (Hugos körning 2026-11-05, P6). De körs i appen, se "Spärrprovet i kopian", punkt d.

Avsluta med `/exit`.

## Byte till versionen med sandlåda (steg 15)

Hugos beslut 2026-11-04 om sandlådan och Hugos beslut 2026-11-05 om granskning 34 (`GRANSKNING.md`). Alla kommandon körs i en sandlåda. Förbuden för `.git` och `.venv` är desamma som i filen som är installerad nu, så inget kommando i sandlådan kan skriva i `.git`. Vakten är oförändrad. **Agenten kör inga av kommandona.** Du kör dem själv i Terminal,
ett i taget, och skriver ditt administratörslösenord när datorn frågar. **Visar ett kommando något annat än det som står:
stoppa och fråga**, och kör inte nästa kommando. Kommandona med `sudo` i punkt 3 och 4 visar ingenting när de går bra.

**Innan du börjar:** den oberoende granskningen ska vara klar, provkörningen ovan ska vara gjord, och filen ska vara den som
granskades. Sessionen där bytet görs ska inte vara en session med agenten: kör allt i ett vanligt Terminal-fönster. **Avsluta alla öppna sessioner** i skrivbordsappen och i Terminal innan du börjar. Dokumentationen säger att nya låsta inställningar läses in också i en session som körs ([settings.md](https://code.claude.com/docs/en/settings.md), "When edits take effect").

**Kontrollera git-inställningen** (Hugos beslut 2026-11-05 om granskning 35, beslut 2). Den gör att git inte kör kod från en mapp som bara ser ut som ett repo (granskning 35, P2). Kommandot bara visar:

```bash
git config --global --get safe.bareRepository
```

- **Väntat: exakt `explicit`.** Visas något annat, eller ingenting: stoppa och fråga.

**1. Version.** Läs av båda, eftersom Claude Code uppdaterar sig själv:

```bash
~/.local/bin/claude --version
```

Läs också raden **Claude Code** i `/status` i skrivbordsappen. Båda ska vara minst **2.1.305**. Filen kräver 2.1.305 (Hugos beslut 2026-11-05 efter P6, beslut 2), och det gör också nyckeln `allowNestedUserNamespaces` enligt dokumentationen ([settings-reference.md](https://code.claude.com/docs/en/settings-reference.md)). Är Terminalens
version en annan än i provkörningen: gör provkörningen igen med den versionen. För de andra nycklarna i `sandbox` anger dokumentationen ingen lägsta version.
Den nämner bara 2.1.224 (avslutande snedstreck) och 2.1.285 (`allowUnsandboxedCommands`), och båda är
äldre än 2.1.305. Att sandlådan körs i skrivbordsappen står inte på sidorna som är lästa (se "Inte bekräftat" i
`GRANSKNING.md`), så det prövas i punkt 6.

**2. Kontrollsummor, före bytet:**

```bash
shasum -a 256 ~/VERA/agent/sparr/managed-settings.json ~/VERA/agent/sparr/kommandosparr.py
```

```bash
shasum -a 256 "/Library/Application Support/ClaudeCode/managed-settings.json" "/Library/Application Support/ClaudeCode/vera/kommandosparr.py"
```

- Den nya filen i projektet: `1ba7457615356ff634956cf3f665787d2e74900986aa96001feeaa8ce31a39da`. Den oberoende granskningen ska ha skrivit upp samma summa.
- Filen som är installerad nu: `149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2`.
- Vakten, båda ställena (beslut 5, den ändras inte): `314df00b4239877d21e0fef7d8f11c844a75d07276ad0af32baa94db8e92d10d`.

**3. Spara förra versionen**, bredvid den, så att du kan backa utan agenten:

```bash
sudo cp -i "/Library/Application Support/ClaudeCode/managed-settings.json" "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json"
```

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json"
```

- `-i` gör att datorn frågar innan den skriver över. Frågar den: svara `n`, stoppa och fråga.

**4. Kopiera den nya versionen.** Inställningarna börjar gälla direkt, också i sessioner som redan är öppna.

```bash
sudo cp ~/VERA/agent/sparr/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/managed-settings.json"
```

**5. Kontrollera efter bytet:**

```bash
shasum -a 256 "/Library/Application Support/ClaudeCode/managed-settings.json" "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json"
```

- Första raden ska vara `1ba7457615356ff634956cf3f665787d2e74900986aa96001feeaa8ce31a39da` och andra `149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2`.

```bash
ls -lde@ "/Library/Application Support/ClaudeCode/managed-settings.json" "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json"
```

- Båda ska vara `-rw-r--r--`, med ägaren `root` och gruppen `wheel`. Extra uppgifter följer regeln i steg 2.

**6. Kontrollen efter bytet.** Avsluta skrivbordsappen helt (Cmd+Q) och öppna den igen.

1. **Terminal:** kör, ett kommando i taget:

   ```bash
   cd ~/VERA/agent
   ```

   ```bash
   ~/.local/bin/claude
   ```

   Skriv `/status`. Raden **Setting sources** ska visa `Enterprise managed settings (file)`. Avsluta med `/exit`.
2. **Inga egna undantag, kontrollerat i Terminal.** `/sandbox` går inte att använda för det här. Enligt [dokumentationen](https://code.claude.com/docs/en/sandboxing.md) skriver det ett fel i stället för att öppna sin panel när låsta inställningar sätter sandlådans nycklar: `Sandbox settings are overridden by a higher-priority configuration`. Det felet är väntat och inget skäl att backa. Kör i stället, ett kommando i taget:

   ```bash
   grep -n -e sandbox -e additionalDirectories ~/.claude/settings.json
   ```

   ```bash
   grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.json
   ```

   ```bash
   grep -n -e sandbox -e additionalDirectories ~/VERA/agent/.claude/settings.local.json
   ```

   **Väntat för varje kommando: ingenting visas, eller `No such file or directory`.** Visas en rad: stoppa och fråga. En tom lista i de låsta inställningarna kan inte hålla undantag borta (Hugos svar 2026-11-04), så du lägger aldrig till `excludedCommands`, `allowWrite` eller `--add-dir` själv.
3. **Ny session i fliken Code i skrivbordsappen, startad i `~/VERA/agent`.** Be agenten köra rutan. Claude Code frågar som vanligt (beslut 3). Säg ja. Kommandot ska visa läget i projektet.

   ```
   git status
   ```

4. **Hela sviten, inne i sandlådan.** Be agenten köra:

   ```
   '/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rfs scripts/tests
   ```

   **Väntat: inget `failed`, alltså inga röda.** Väntat antal: **69** överhoppade, eller **71** om `~/.ssh` inte finns. Det ska inte stå `SPÄRRTESTET HOPPAS ÖVER`. Det ska stå `GRUPP D HOPPAS ÖVER` (38 prov) och `SPÄRRPROVET I KOPIAN HOPPAS ÖVER` (31 prov), som körs i punkt 8. Finns inte `~/.ssh` hoppas också de två proven av den mappen över, med texten "finns inte på den här datorn". Det ska inte heller stå `H1-PROVET HOPPAS ÖVER`. Står `H1-PROVET HOPPAS ÖVER` där: backa inte, utan fortsätt till "Spärrprovet i kopian", punkt d, som säger vad du gör. Spärrtestet i `scripts/tests/test_sandladan.py` prövar här att git kan visa läget och att läsning i projektet fungerar, att en fil eller mapp med namnet `.git` stoppas i testets tillfälliga mapp, att skrivning utanför projektet, i `~/.local/share/claude`, i appen och i appens Claude Code stoppas, och att läsning av `~/.ssh` stoppas. **Står `SPÄRRTESTET HOPPAS ÖVER` där, eller är något rött: stoppa och fråga.**
5. **Git kan inte göra en commit i sandlådan, och det är rätt.** Från den här installationen committar agenten inte (Hugos beslut 2026-11-05 om granskning 34, beslut 2). Sessionen skriver bara commit-meddelandet i filen `COMMIT_MSG.txt` i projektmappen, och skriver aldrig ett kommando som du ska klistra in. Meddelandet räknar upp varje fil som sessionen har ändrat, skapat eller tagit bort. Du skriver alltid själv samma fem kommandon, ett i taget, med `!` i sessionen eller i Terminal (Hugos beslut 2026-11-05 om granskning 35, beslut 6, om granskning 36, P1, och om granskning 39, beslut 3). Gör det vid nästa ändring i projektet. Det första visar läget, varje fil för sig, också filer som `.gitignore` döljer (Hugos beslut 2026-11-05 om granskning 36, P3, och om granskning 37, P4):

   ```bash
   git status --short --ignored -uall
   ```

   Väntat, raderna som börjar med `!!`: `.DS_Store`, `.claude/.DS_Store`, `.claude/worktrees/.DS_Store`, `.pytest_cache/.gitignore`, `.pytest_cache/CACHEDIR.TAG`, `.pytest_cache/README.md`, `.pytest_cache/v/cache/lastfailed`, `.pytest_cache/v/cache/nodeids`, `foretag/.DS_Store`, `scripts/.DS_Store` och `testdata/.DS_Store`, och `COMMIT_MSG.txt`. Väntat är också en rad för varje fil som sessionen har räknat upp i `COMMIT_MSG.txt`, men aldrig en rad med `!!` (Hugos beslut 2026-11-05 om granskning 38, P1 och P3, och Hugos svar i chatten samma dag). **Stoppregel: varje rad som inte står exakt i det väntade läget stoppar, också en annan rad med `!!`. Det gör också alltid, i vilken mapp som helst och oavsett stora och små bokstäver, någon annan rad med `.claude/`, `.github/`, `.mcp.json`, `.gitattributes`, `.gitignore`, `.lfsconfig` eller `.gitmodules`, och varje rad som innehåller ett citattecken (`"`), även om sessionen har räknat upp filen (Hugos beslut 2026-11-05 om granskning 39, beslut 4 och 5). När en rad stoppar: stoppa och fråga, också när sessionen själv har ändrat filen.**

   ```bash
   git add -A
   ```

   ```bash
   ls -l COMMIT_MSG.txt
   ```

   **Raden ska börja med `-` (en vanlig fil), och antalet länkar (siffran efter rättigheterna) ska vara 1. Börjar den med `l` (en länk) eller något annat: committa inte, stanna. Är siffran en annan än 1: committa inte, stanna.** En länk kan annars få en fil som sandlådan förbjuder att hamna i commit-meddelandet (granskning 36, P1). En **hård länk** är ett andra namn på samma fil. Raden börjar då med `-`, men siffran är 2 eller högre (Hugos beslut 2026-11-05 om granskning 37, P3).

   **Läs listan i `COMMIT_MSG.txt` före commiten.** Kör det här bara när raden ovan stämmer, annars kan det visa en annan fil (Hugos beslut 2026-11-05 om granskning 39, beslut 3). Det ändrar ingenting. Jämför listan med raderna från det första kommandot.

   ```bash
   cat COMMIT_MSG.txt
   ```

   ```bash
   git commit -F COMMIT_MSG.txt
   ```

   **Efter commiten och före en push:** kör det här, och läs meddelandet och fillistan (Hugos beslut 2026-11-05 om granskning 37, P3). Det ändrar ingenting. Står `(END)` eller ett kolon längst ner: tryck `q` när du har läst klart.

   ```bash
   git show --stat HEAD
   ```

   Överst står meddelandet, och längst ner står vilka filer som följde med. **Ser något fel ut, till exempel ett långt eller konstigt meddelande eller en fil du inte väntade dig: pusha inte, fråga.**

6. **Sista kontrollen:** steg 2, 4 och 9 i "Kontroll efter installationen" nedan. Be också agenten skapa en mapp i scratchpad med `mkdir -p`, eftersom kopior och provfiler ligger där. Det ska gå igenom.
7. **Skalet:** kontrollskriptet i steg 4 g gäller oförändrat.
8. **Spärrprovet i kopian, direkt och före annat arbete.** Gör avsnittet "Spärrprovet i kopian" nedan.

**Det här gäller från nu:**

- Kommandon som hämtar från eller skickar till GitHub över en SSH-adress går inte i sandlådan på macOS, enligt dokumentationen. De står inte heller på listan i SPEC 7.1. Du kör dem själv i Terminal.
- Kommandon som skriver i `.git`, till exempel de som gör en commit eller slår ihop eller byter gren, stoppas i sandlådan. Du kör dem själv i Terminal.
- Ett kommando du själv skriver efter `!` körs utanför sandlådan, enligt [dokumentationen](https://code.claude.com/docs/en/sandboxing.md).

**Backa till förra versionen.** Vägrar Claude Code eller skrivbordsappen starta, stoppas allt med `Sandbox is required`, eller blir något i kontrollen fel. Kör i Terminal, som inte behöver agenten:

```bash
sudo cp "/Library/Application Support/ClaudeCode/managed-settings.fore-sandladan.json" "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
shasum -a 256 "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Summan ska vara `149b603bf44438c1643a213dfcf52325ed3f7c8ff9aa402bee97c6328ef92ea2`. Avsluta sedan appen helt och öppna den igen. Vakten är kvar, oförändrad. Skriv upp vad som hände, och fråga.

## Spärrprovet i kopian (steg 15)

Hugos beslut 2026-11-05 om granskning 34, beslut 4. Provet visar att inget i sandlådan kan skriva i `.git`, skapa en fil eller mapp med namnet `.git`, skriva `.git/commondir`, byta namn på `.git` eller flytta hela arbetsmappen (granskning 35, P1). Det prövar också att git kan visa läget och historiken, men inte lägga till filer, göra en commit eller ändra den senaste commiten. Det prövar läsförbudet för `~/.ssh` med en mapp som finns bara under provet. Testet `test_sparr_hard_lank_till_ssh_stoppas` prövar att sandlådan inte kan skapa en hård länk (ett andra namn på samma fil) till testfilen där, ett uttalat undantag från länkregeln i CLAUDE.md, bara i spärrprovet (Hugos beslut 2026-11-05 om granskning 37, P3). Det görs direkt efter bytet.

Provet körs i en kopia, `~/VERA/sparrprov`, som du förbereder själv, utanför sandlådan. Kopian är ett undantag från regeln "Prov och test", bara för spärrtestet. Provet rör aldrig projektets riktiga `.git`, och testerna vägrar köra om kopian är projektet.

**a. Förbered kopian, i Terminal.** Kontrollera först att mappen inte finns. Det ska stå `No such file or directory`. Finns den: stoppa och fråga.

```bash
ls -ld ~/VERA/sparrprov
```

```bash
git clone --no-hardlinks ~/VERA/agent ~/VERA/sparrprov
```

- Det gör en egen kopia av projektet med hela historiken. `--no-hardlinks` gör att kopian inte delar några filer med projektet.

```bash
cd ~/VERA/sparrprov
```

```bash
git log -1 --format=%H
```

- Visar den senaste commiten i kopian. Den ska vara den som granskades. Är den en annan: stoppa och fråga.

**Skapa en `~/.ssh` för provet** (Hugos beslut 2026-11-05 om granskning 36, P6). Kontrollera först att mappen inte finns. Det ska stå `No such file or directory`. **Finns mappen: stoppa och fråga**, och ändra inget i den.

```bash
ls -ld ~/.ssh
```

```bash
mkdir -m 700 ~/.ssh
```

```bash
echo kassio-prov > ~/.ssh/prov
```

- Det andra skapar mappen, som bara du kan öppna. Det tredje skriver en testfil med texten `kassio-prov`, inget hemligt. Båda visar ingenting när de går bra.

**b. Kör provet i Terminal:**

```bash
~/.local/bin/claude
```

Frågar Claude Code om du litar på mappen: svara ja. Be Claude: "Kör exakt det här kommandot med Bash-verktyget, och ändra ingenting i det:" och klistra in:

```
'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rfs -k test_sparr_ scripts/tests
```

**Väntat: `41 passed`, inget `failed`, och varken `SPÄRRTESTET HOPPAS ÖVER` eller `SPÄRRPROVET I KOPIAN HOPPAS ÖVER`.** Ett av proven kör `cat` på testfilen inne i sandlådan, och ett försöker göra den hårda länken. Avsluta med `/exit`.

**c. Kör samma prov i skrivbordsappen.** Starta en ny session i fliken **Code**, i mappen `sparrprov` i `~/VERA`, inte i en worktree, och be Claude köra samma kommando. Samma väntade resultat. Det här är också provet av att sandlådan körs i skrivbordsappen. Låt sessionen vara kvar till d.

**Är något rött i b eller c: lyckades ett försök, så backar du direkt** med "Backa till förra versionen" ovan, gör e och frågar. **Står någon av texterna `HOPPAS ÖVER` ovan där, körs provet inte i sandlådan:** backa också och fråga.

**d. Kör H1-proven i skrivbordsappen, i samma session som i c** (Hugos beslut 2026-11-05 efter P6, beslut 1). I Terminal hoppas de över, också utan sandlåda (Hugos körning 2026-11-05, P6). Appen är där märkningen `com.apple.provenance` sätts och där vakten används. Be Claude: "Kör exakt det här kommandot med Bash-verktyget, och ändra ingenting i det:" och klistra in:

```
'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=line -rs -k test_h1_ scripts/tests
```

- **Väntat: `31 passed`, inget `skipped`, inget `failed`, och inte texten `H1-PROVET HOPPAS ÖVER`.** Inga överhoppade H1-prov, alltså.
- **Hoppas de över, så backa inte.** Stanna och fråga, utan att göra något mer i projektet. Spärrproven i b och c har redan gått igenom, så sandlådan fungerar då ändå. Det är H1-proven som inte går att köra där, och då behövs ett nytt beslut.
- **Är ett H1-prov rött: backa inte, men stanna. Kör inga sessioner tills det är avgjort.** Det avgörs av en session som bara läser, som du startar, och som bara tittar på det provet (Hugos beslut 2026-11-05 om granskning 35, beslut 5). Skicka hela utskriften dit.

**Pröva läsförbudet, i samma session** (Hugos beslut 2026-11-05 om granskning 36, P6). Förbudet står i `sparr/managed-settings.json`: `denyRead` för sandlådan och `Read(~/.ssh/**)` för fil-verktyget. Be Claude: "Läs filen `~/.ssh/prov` med verktyget Read." Be sedan Claude köra det här med Bash-verktyget:

```
cat ~/.ssh/prov
```

- **Väntat: båda stoppas, och texten `kassio-prov` visas inte.** Det senare stoppas redan av vakten. Sandlådans eget förbud prövas därför av testet `test_sparr_lasning_av_ssh_stoppas` i b och c, inne i sandlådan.
- **Visas `kassio-prov`: läsförbudet gäller inte.** Backa med "Backa till förra versionen", gör e och fråga.

Arkivera sessionen efteråt.

**e. Ta bort kopian, i Terminal.** Ta först bort testfilen och mappen `~/.ssh`. Kopiera kommandona exakt.

```bash
cd ~/VERA/agent
```

```bash
rm ~/.ssh/prov
```

```bash
rmdir ~/.ssh
```

```bash
ls -ld ~/.ssh
```

- `rmdir` tar bara bort en tom mapp, så inget annat kan försvinna. Säger den `Directory not empty`: stoppa och fråga. Det sista ska säga `No such file or directory`.

Ta sedan bort kopian. Det första raderar hela mappen, utan papperskorg.

```bash
rm -rf ~/VERA/sparrprov
```

```bash
ls -ld ~/VERA/sparrprov
```

- Det sista kommandot ska säga `No such file or directory`.

## Prov utanför sandlådan (steg 15)

Hugos beslut 2026-11-05 om granskning 34, beslut 3, Hugos beslut 2026-11-05 efter P6, beslut 1 och 3, och Hugos beslut 2026-11-05 om granskning 39, beslut 1. Det här avsnittet gäller bara grupp D (39 prov). De kan inte köras i sandlådan. Där hoppas 38 av dem över, med texten `GRUPP D HOPPAS ÖVER`, och bara när datorn nekar med `Operation not permitted`. Den sista går igenom där, eftersom den bara kör de andra i en kopia. Du kör dem själv i Terminal, varje gång vakten eller de låsta inställningarna ändras. H1-proven körs inte här, utan i appen, se "Spärrprovet i kopian", punkt d.

Du kör dem i en kopia av en granskad commit, inte i projektmappen, eftersom de körs med dina fulla rättigheter. I projektmappen kan en testfil ha lagts av agenten, och här körs den utan sandlåda. En sådan kopia har bara det som är committat.

**a. Gör kopian.** Det första kommandot ska säga `No such file or directory`. Finns mappen: stoppa och fråga.

```bash
ls -ld ~/VERA/provkopia
```

```bash
git clone --no-hardlinks ~/VERA/agent ~/VERA/provkopia
```

```bash
cd ~/VERA/provkopia
```

```bash
git log -1 --format=%H
```

- Det ska vara den commit som granskades. Är det en annan: kör inte provet, stoppa och fråga.

**b. Kör proven:**

```bash
'/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q --tb=short -rfs -k 'test_h6_en_lank_till_git_stoppas or test_beslut_1_gamla_venv_i_projektet_stoppas or test_granskning_37_p4_uall_visar_varje_fil_for_sig or test_granskning_37_p4_utan_uall_doljs_filerna or test_granskning_37_a_pahittade_poster_i_de_tre_filerna_ger_inte_rott or test_granskning_38_det_vantade_laget_ger_inget_stopp or test_granskning_38_p1_en_ny_fil_i_en_mapp_i_det_vantade_laget_stoppar or test_granskning_38_p3_gitattributes_i_en_ny_mapp_stoppar_i_varje_stavning or test_granskning_38_sessionens_uppraknade_filer_ar_vantade_och_inget_annat or test_granskning_39_riktiga_rader_stoppar_ocksa_om_de_ar_uppraknade' scripts/tests
```

- **Väntat: `39 passed`, inget `failed`, och inte `GRUPP D HOPPAS ÖVER`.** Är något rött, står den texten där, eller är antalet ett annat: stoppa och fråga.

**c. Ta bort kopian.** Kopiera kommandona exakt. Det andra raderar hela mappen, utan papperskorg.

```bash
cd ~/VERA/agent
```

```bash
rm -rf ~/VERA/provkopia
```

## Caspers dator

Samma steg, i samma ordning, och samma versionskontroll i steg 1 (minst 2.1.305, med `/status` i
skrivbordsappen och med versionskommandot i Terminal om Claude Code för Terminal finns där,
med hela sökvägen och samma varning för installerarens förslag). Samma kontrollskript i steg 4 g och i
kontrollen efter installationen, steg 1, och samma kontroll av agentens skal i steg 4 h. Samma förprov i
steg 3 och samma kontroll av mapparna i steg 2 och 13. Samma kontroll av vaktens Python i steg 2 b: på
Caspers dator är den inte kontrollerad, så den kan visa en annan version eller att utvecklarverktygen saknas.
Då gäller samma sak: stoppa och fråga. Samma `managed-settings.json` fungerar: regeln som hindrar agenten att skriva i
`.git` (`Edit(//**/.git/**)`) gäller varje `.git`-mapp på datorn och har inget användarnamn i sig.
Skillnader:

- Sökvägen till projektet kan vara en annan. Byt `~/VERA/agent` i steg 1, 4 g, 5, 7, 9, 10 och 12 mot där
  projektet ligger på Caspers dator.
- Steg 4: kör kommandot från steg 4 e först. Raden för Cryptexes-mappen (steg 4 c) läggs in också
  på Caspers dator (Hugos svar 2026-10-28, punkt 1). Raden för nvm-mappen (steg 4 b) behövs bara om nvm
  finns där. Utan nvm ska bara den sista raden i steg 4 d vara Cryptexes-raden (se steg 4 d). Står någon
  annan mapp än systemets före `/usr/bin`, till exempel Homebrew (`/opt/homebrew/bin`): stoppa och fråga,
  eftersom vakten då stoppar alla kommandon.
- **Steg 4 g, vilka filer Caspers zsh läser in** (granskning 14, R2, Hugos beslut 2026-10-28). Förbuden i
  de låsta inställningarna bygger på vad zsh läser in på Hugos dator. Casper kör därför skriptet i steg 4 g
  på sin dator före installationen. Visar det en rad `AVVIKER: startfil: …`, till exempel för oh-my-zsh,
  Homebrews `brew shellenv`, conda eller iTerm2: stoppa och fråga. Installera inte förrän en ny version av
  inställningsfilen har förbud för de filerna.
- **Claude Code för Terminal behövs på Caspers dator** (granskning 14, R5, Hugos beslut 2026-10-28). Raden
  Setting sources syns bara i Terminal (steg 1, "Efteråt" punkt 2 och kontrollen efter installationen,
  steg 1). Utan Claude Code för Terminal i `~/.local/bin/claude` går det inte att se att de låsta
  inställningarna gäller, och då **går installationen inte att kontrollera**. Säger
  versionskommandot `no such file or directory`: stoppa och fråga innan installationen.
- **Före installationen:** samma kontroll av `safe.bareRepository` som i bytet. Inte `explicit`: stoppa och fråga.

Kontrollen nedan görs också på Caspers dator.

## Kontroll efter installationen

Planens steg 5 (Hugos beslut 2026-10-28). Gör stegen i ordning, i **en ny session** i fliken **Code** i
skrivbordsappen, startad i `~/VERA/agent`. Du skriver till agenten som vanligt. Agenten gör inte den här
kontrollen utan att du säger till.

Om något steg inte blir som det står: **stoppa, skriv upp vad som hände, och fråga** innan något annat
görs. Steg 1–7 ska vara klara innan uppgift 4 körs. Steg 9 görs direkt efter steg 7 och ska också vara
klart innan uppgift 4 körs (Hugos svar 2026-10-28, punkt 3). Steg 8 krävs inte för installationen eller för
uppgift 4, men ska vara gjort före läget "auto", före körningar utan att Hugo tittar, före första hela
körningen på riktiga underlag och före första kund (Hugos beslut 2026-10-28, 8). Steg 8 är gjort på Hugos
dator (175db51), ännu inte på Caspers.

1. **De låsta inställningarna gäller.** Raden **Setting sources** visas inte i skrivbordsappen, så den läses i Terminal (Hugos svar 2026-10-28, punkt 3): kör de två rutorna under "Raden Setting sources" i installationens steg 1 (hela sökvägen, Hugos beslut 2026-10-28, granskning 13, P3 b), och skriv `/status`. Säger Terminal `no such file or directory`: stoppa och fråga. Raden ska visa `Enterprise managed settings (file)`, alltså inställningarna från filen du installerade (code.claude.com/docs/en/managed-settings). `User settings`, `Project settings` och `Project local settings` är väntade och underkänner inte. Bara en annan låst källa underkänner installationen, till exempel inställningar som styrs från claude.ai: stoppa och fråga (Hugos svar 2026-10-28, punkt 3). Avsluta med `/exit`. Läs också i skrivbordsappens `/status` raden **Claude Code**: versionen ska vara 2.1.305 eller senare. Läget "auto" ska gå att välja (Hugos beslut 2026-10-29): i terminalens Claude Code, tryck Shift+Tab några gånger, och "auto" ska komma upp.

   **Skalet, igen efter installationen** (Hugos beslut 2026-10-28, granskning 13, P1 a, och efter
   granskning 15). Öppna ett nytt Terminal-fönster (Cmd+N) och kör, ett i taget, samma två kommandon som i
   installationens steg 4 g:

   ```bash
   shasum -a 256 ~/VERA/agent/sparr/kontrollera-skalet.zsh
   ```

   ```bash
   source ~/VERA/agent/sparr/kontrollera-skalet.zsh
   ```

   Summan ska vara samma som i steg 4 g, och skriptet ska skriva exakt `OK` och `SLUT`. **Är summan en
   annan, står det en rad som börjar med `AVVIKER`, eller saknas `SLUT`: stoppa och fråga**, och kör inte
   uppgift 4. Kontrollen av agentens skal i steg 4 h går inte att göra efter installationen, eftersom vakten
   stoppar kommandot.
2. **Ihopkopplade kommandon stoppas.** Be agenten köra rutan. Det ska stoppas med ett fel som börjar "Stoppat av vakten" och säger att kommandon inte kopplas ihop.

   ```
   ls; ls
   ```

3. **Ett kommando på listan går igenom.** Be agenten köra rutan. Claude Code frågar dig som vanligt om det får köras. Säg ja. Kommandot ska köras och visa läget i projektet. (`git` ligger i `/usr/bin`, som ägs av systemet, så PATH-regeln släpper igenom det. Stoppas det med "PATH-regeln": skriv upp felet och fråga. Nämner felet en mapp med `.nvm` i namnet eller `/System/Cryptexes/App/usr/bin`, har installationens steg 4 inte fått effekt i appen.)

   ```
   git status
   ```

   Be sedan agenten köra testsviten med kommandot i SPEC 7.1 (Hugos beslut 2026-10-28 om vakten, beslut 1). Det ska gå igenom, och sista raden ska säga hur många tester som är gröna (`passed`) och att inga är röda.

   ```
   '/Library/Application Support/ClaudeCode/vera/venv/bin/python' -B -m pytest -p no:cacheprovider -q scripts/tests
   ```

4. **sudo stoppas.** Be agenten köra rutan. Det ska stoppas, antingen av vakten ("sudo och su stoppas alltid") eller av förbudsregeln i inställningarna. Datorn ska **inte** fråga efter ditt lösenord. Gör den det: skriv inte lösenordet, avbryt med Ctrl+C, och stoppa.

   ```
   sudo ls
   ```


5. **Agenten kan fortfarande fråga dig.** Be agenten ställa en fråga till dig med svarsknappar. Frågan
   ska visas, och ditt svar ska komma fram.
6. **Agenten kan fortfarande skriva filer i `~/VERA`.** Be agenten skapa en liten provfil,
   `~/VERA/agent/provfil.txt`, med fil-verktyget Write. Claude Code frågar dig först. Säg ja. Filen ska
   finnas efteråt. Ta sedan bort den själv i Finder.
7. **Hoppa över det här steget tills det finns ett prov för worktrees** (granskning 35, beslut 4). **En session i en worktree fungerar, eller stoppas på ett säkert sätt** (Hugos beslut 2026-10-28,
   punkt 6). En **worktree** är en egen kopia av projektet på en egen gren, som skrivbordsappen kan skapa
   för en session. Starta en ny session i en worktree i skrivbordsappen och be agenten köra kommandot i steg 3.
   Det finns två godtagbara utfall:
   - kommandot går igenom (som i steg 3), eller
   - vakten stoppar det med "annan mapp". Då stoppar vakten alla kommandon i worktree-sessioner. Det är
     säkert, men skriv upp det och fråga, eftersom worktree-sessioner då inte går att använda.

   Om kommandot i stället körs utan att vakten har prövat det, till exempel om kommandot i steg 2 går igenom i
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
   det första kommandot i steg 3. **Det ska stoppas.** Felet kommer från Claude Code och inte från vakten (vakten ligger ju
   inte på plats), så det börjar inte med "Stoppat av vakten". Det säger att vakten (en hook,
   `PreToolUse`) inte gick att köra, och nämner troligen `can't open file` och `No such file or
   directory`. Eftersom vakten gäller alla verktyg stoppas allt i sessionen, också när agenten vill läsa
   en fil. Det är den säkra riktningen.

   **Om kommandot går igenom och visar läget i projektet: gör c direkt, och stoppa och fråga.**

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

   **e. Starta en ny session** och gör steg 2 och 3 igen: kommandot i steg 2 ska stoppas med "Stoppat av vakten",
   och det första kommandot i steg 3 ska gå igenom. Då är vakten tillbaka och fungerar.

   **Vad provet visar.** När vakten saknas kan vaktens Python (`/Library/Developer/CommandLineTools/usr/bin/python3`, steg 2 b) inte öppna filen och avslutar med kod 2, och kod 2 betyder för Claude Code "stoppa". Provet visar alltså att en **saknad** vakt stoppar allt. Det prövar inte inställningen `onFailure: "block"` i sig, som gäller när vakten fallerar på andra sätt (en annan kod än 0 och 2, tidsgränsen, eller att programmet inte går att starta). Att Python ger kod 2 visas av testet `test_systemets_python_stoppar_med_kod_2_nar_vakten_saknas`. Det är förprovet i steg 3 i installationen som prövar `onFailure: "block"`: där går vakten inte att starta alls.

   Gör steg 9 igen efter e.
9. **Sista kontrollen, i skrivbordsappen: vakten stoppar ett kommando som inte står på listan** (Hugos svar
   2026-10-28, punkt 3). Görs direkt efter steg 7, och igen efter steg 8 om du gör det. Starta en ny session
   i fliken **Code** i skrivbordsappen, startad i `~/VERA/agent`, och be agenten köra:

   ```
   date
   ```

   - `date` visar bara dagens datum och klockslag. Det läser och ändrar ingenting, så det är ofarligt även
     om vakten skulle saknas. Det står inte på listan i SPEC 7.1.
   - **Förväntat:** kommandot stoppas innan Claude Code frågar dig om lov, med ett fel som börjar
     "Stoppat av vakten" och säger att `'date' står inte på listan i SPEC 7.1`. Inget datum visas.
   - **Om Claude Code frågar om lov att köra `date`:** svara nej. Vakten har då inte stoppat kommandot.
     Stoppa och fråga.
   - **Om datumet visas:** kommandot kördes utan att vakten stoppade det. Det är ofarligt, men vakten
     fungerar inte. Stoppa och fråga, och kör inte uppgift 4.
