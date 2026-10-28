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
| `sparr/managed-settings.json` | `/Library/Application Support/ClaudeCode/managed-settings.json` | **De låsta inställningarna.** De säger åt Claude Code att köra vakten, att stoppa kommandot om vakten kraschar eller inte svarar, och att bara vakter och regler härifrån gäller. |

Inställningarna börjar gälla så fort filen finns, i terminalen och i skrivbordsappen. Därför kopieras
vakten först och inställningarna sist.

## Innan du börjar

1. **Den oberoende granskningen ska vara klar** (planens steg 2), och du ska kopiera filerna från den
   commit som granskades. Ändras filerna i projektet efter granskningen, kopiera inte. Fråga först.
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

**Båda versionerna ska vara 2.1.295 eller senare.** Om någon är äldre: **stoppa**, uppdatera den först
(skrivbordsappen med **Claude > Check for Updates…**, och terminalens Claude Code enligt
dokumentationen), kontrollera igen, och gå vidare först när båda är minst 2.1.295.

## Steg 2: kopiera vakten

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

## Steg 3: låt systemet äga mappen och vakten

```bash
sudo chown -R root:wheel "/Library/Application Support/ClaudeCode"
```

- `chown` byter ägare. `root:wheel` är systemets administratör och dess grupp.
- `-R` gör att det gäller mappen och allt i den, alltså också `vera` och vakten.
- Efter det kan bara en administratör ändra i mappen, och agenten, som arbetar som ditt vanliga
  konto, kan inte göra det.

## Steg 4: sätt rättigheterna på mapparna och vakten

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

## Steg 5: kopiera de låsta inställningarna (sist, nu börjar de gälla)

```bash
sudo cp -i ~/VERA/agent/sparr/managed-settings.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- `cp` kopierar en fil. `-i` gör att datorn frågar innan den skriver över en fil som redan finns. Om
  den frågar: svara `n` (nej) och stoppa, eftersom filen då inte borde finnas (se "Innan du börjar").

## Steg 6: låt systemet äga inställningarna och sätt rättigheterna

```bash
sudo chown root:wheel "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo chmod 644 "/Library/Application Support/ClaudeCode/managed-settings.json"
```

- Samma som i steg 3 och 4, för inställningsfilen: systemet äger den, alla får läsa den, bara en
  administratör får ändra den.

## Efteråt

1. **Starta nya sessioner** i terminalen och i skrivbordsappen. Sessioner som redan är öppna kan ha
   läst inställningarna innan filen fanns.
2. **Kontrollen efter installationen görs i en ny session** (planens steg 5): under `/status` ska de
   låsta inställningarna synas som källa, `git status` ska gå igenom, och `ls; ls`, `cd ..`,
   `sudo ls`, `su` och `echo x` ska stoppas med ett fel på svenska. Agenten gör inte det steget utan
   att du säger till.
3. **Vakterna i tillägget superpowers slutar fungera** (Hugos beslut 2026-10-28, 2), eftersom bara
   vakter från de låsta inställningarna får köras.

## Caspers dator

Samma steg, i samma ordning, och samma versionskontroll i steg 1 (både terminalen och
skrivbordsappen, minst 2.1.295). Två skillnader:

- Sökvägen till projektet kan vara en annan. Byt `~/VERA/agent` i steg 2 och 5 mot där projektet
  ligger på Caspers dator.
- Regeln i `managed-settings.json` som hindrar agenten att skriva i `.git` har Hugos sökväg
  (`/Users/hugolindholmer/VERA/agent/.git`). Casper behöver en version av filen med sin egen sökväg,
  som granskas på samma sätt innan den installeras.
