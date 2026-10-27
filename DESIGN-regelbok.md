# DESIGN – regelbok och kontering

| | |
|---|---|
| Status | **Godkänt av Hugo 2026-10-26 (design). D1–D16 är öppna och väntar på redovisningskonsult**. Uppgift 1 (läsa kontoplan och momsfil), uppgift 2 (läsa regelboken, med tillägget för ägare och närstående) och uppgift 3 (konteringsförslaget med K2 och ursprungskontrollen) i avsnitt 7 är byggda, och granskning 7:s M1 och M2 är rättade (täckningen och ingående och utgående moms, avsnitt 3), liksom M3 och en del av M4 (regeln ska passa förslaget, och kontrollsummor för regelbok, kontoplan, momsfil och matchningsformat, avsnitt 3), och M5–M8 och M10–M12 (förväxlingstecken och ägarens bankrader i avsnitt 1, en roll per konto i avsnitt 2, och bankradernas nyckelnamn i avsnitt 3). M9 hör till uppgift 5. Efter granskning 8 är N1–N4 och N7 rättade (dolda tecken enligt Unicodes lista, vilka tecken ett namn får ha och ägarens bankrader, avsnitt 1), och exemplet i avsnitt 3 har kodens nyckelnamn för bankrader (M11, Hugos OK 2026-10-27). Hugos beslut efter uppgift 2 och 3 och efter granskning 7 och 8 står i avsnitt 8. Ändrar inget i SPEC.md |
| Gäller | Steg 4 i arbetsflödet (SPEC avsnitt 4): kontera enligt företagets regelbok, och kontrollerna K2, K5, K8 och K9 |
| Exempel | Bara Syntet Testbutik AB och testdatan för 2025-Q1. **Allt är SYNTETISKT** |

Det här dokumentet föreslår hur Vera ska gå från "bankrad och underlag hör ihop" (det som matchningen
redan gör) till "så här ska det bokföras" (ett **konteringsförslag**). Det svarar på åtta frågor, en per
avsnitt.

---

## Viktigt först: säkerhet

Två saker rör säkerheten och ska vara kända innan något byggs.

1. **Regelboken styr vad som bokförs, och agenten kan i dag skriva i mappen där den ska ligga.**
   Enligt SPEC avsnitt 3 får agenten aldrig ändra regelboken. Men `foretag/<namn>/` är skrivbar för
   agenten, precis som bankformatet och matchningsformatet (SPEC 7). Förslaget nedan har därför tre skydd
   tills spärrsteget flyttar regelboken till en skyddad mapp:
   - regelboken har en **kontrollsumma** (hash, ett "fingeravtryck" av filen som ändras om ett enda tecken
     ändras), och den godkända kontrollsumman står i varje förslag,
   - spärrtestet "ändrad regelbok" (SPEC 7) ska prövas mot just den här filen,
   - agenten kan aldrig skapa eller ändra en regel. En ny motpart blir ett ärende, och svaret blir ett
     **regelförslag** som en människa själv lägger in.
2. **Ett konteringsförslag är aldrig en bokföring.** Förslaget är en datastruktur som visas för
   godkännaren. Inget i det här steget skriver till kundens bokföringsprogram eller till SIE-filen. Det
   sker först efter godkännande (SPEC avsnitt 4, steg 9).

---

## Ord som används

| Ord | Betydelse |
|---|---|
| **Kontering** | Att bestämma på vilka konton en händelse ska bokföras och med vilka belopp |
| **Konto** | En "låda" i bokföringen med ett nummer, till exempel bankkontot eller kontot för hyra |
| **Kontoplan** | Listan över företagets konton. De flesta svenska företag utgår från **BAS**, en standardlista med kontonummer |
| **Verifikation** | En bokförd händelse: ett datum, en text och minst två rader med konton och belopp. Varje verifikation ska kunna kopplas till sitt underlag |
| **Debet och kredit** | De två sidorna i en verifikation. Det är bara namn på sidorna. Summan i debet ska alltid vara lika med summan i kredit. Pengar **in** på banken står i debet på bankkontot, pengar **ut** står i kredit |
| **Ingående moms** | Moms som företaget har betalat på sina inköp och normalt får tillbaka (dras av) |
| **Utgående moms** | Moms som företaget har tagit ut av sina kunder och ska betala in till Skatteverket |
| **Varugrupp** | En grupp varor eller tjänster med samma momssats, till exempel "livsmedel" |
| **Avräkningskonto** | Ett konto som pengar "står på" en kort tid, mellan två händelser. Till exempel kortförsäljningen mellan kassans dagsavslut och dagen då kortinlösaren sätter in pengarna. När allt stämmer går kontot jämnt ut, alltså blir noll |
| **Periodisering** | Att fördela en kostnad över den tid den gäller, till exempel en helårsförsäkring över tolv månader |
| **Faktureringsmetoden** | En faktura bokförs när den kommer, och betalningen bokförs senare för sig |
| **Kontantmetoden** | En faktura bokförs först när den betalas. Vid räkenskapsårets slut bokförs obetalda fakturor ändå |
| **Representation** | Till exempel mat och dryck med kunder eller personal. Där får företaget ofta bara dra av en del av kostnaden och momsen. Kallas **avdragsbegränsat** |
| **Median** | Det mittersta värdet när beloppen ställs i ordning. Påverkas inte av ett enda extremt belopp, som ett medelvärde gör |

---

## 1. Regelbokens form

### Vad en regel är

En regel säger: **"när det här kommer in, föreslå den här konteringen, på den här nivån"**. En regel har
fyra delar:

| Del | Innehåll |
|---|---|
| **Vad regeln gäller** (`galler`) | Vilken källa (underlag, bankrad eller Z-rapport), vilken typ (kvitto eller leverantörsfaktura) och vilken motpart. För bankrader utan underlag: namnet på regeln i `matchning.json` (till exempel `bankavgift`) |
| **Konteringen** (`kontering`) | Vilket konto kostnaden eller intäkten ska på, per **varugrupp**. Momsens konto bestäms inte här utan av momssatsen (avsnitt 2) |
| **Villkor** (`villkor`) | Från och till vilket datum regeln gäller, högsta belopp, och om posten är avdragsbegränsad (K8) |
| **Nivå** (`niva`) | Den lägsta nivån förslaget kan få: A, B, C eller D. Kontrollerna kan bara höja nivån, aldrig sänka den (avsnitt 5) |

Varje regel har ett fast **regel-id** (till exempel `R-LEV-TE`). Id:t står i varje förslag, så att
godkännaren ser vilken regel som användes (SPEC avsnitt 4, steg 4).

### Regler för regelboken som helhet

- Motparten jämförs efter samma **normalisering** som i K4 och matchningen (`normalisering.py`): stora
  och små bokstäver, blanksteg och osynliga tecken räknas inte.
- **Förväxlingstecken stoppar regelboken** (granskning 7, M5, och granskning 8, N2). En motpart, ett
  kassaregister och en ägare eller närstående får bara ha bokstäverna a–z med eller utan accent (även å, ä,
  ö och é), siffrorna 0–9, mellanslag, bindestreck (alla sorter, som räknas som "-"), understreck och
  punkt. Ett regel-id får bara ha a–z, siffror och bindestreck, efter normaliseringen (som fakturanumret i
  underlagen). Annars stoppas hela filen. Underlagen stoppar bara ord som blandar latinska och andra
  bokstäver, men regelboken är konfiguration och stoppar också ett helt ord i ett annat skriftsystem, till
  exempel cherokee-bokstäver som ser ut som `AGARE`, och alla andra tecken: skiljetecken och symboler som
  ser ut som ett bindestreck (till exempel U+02D7 och U+2043), kombinerande tecken som står för sig, och
  latinska bokstäver som inte är a–z med accent (till exempel U+0131, i utan prick, som ser ut som en etta,
  U+01C0, ett lodrätt streck, och U+1D00, ett litet versalt A). Också `&`, `/`, `,`, `'`, parenteser, `Ø`,
  `Æ` och `ß` stoppas, tills Hugo har bestämt om de ska få finnas (avsnitt 8). Konton och varugrupper ska
  finnas i kontoplanen och momsfilen, där de redan bara får ha 0–9 respektive a–z, siffror och understreck.
  Kvar är förväxlingar inom a–z, till exempel litet L i stället för en etta. De kräver en lista över tecken
  som liknar varandra (granskning 7, M5) och är inte byggda.
- **Dolda tecken** stoppar regelboken var de än står, som i kontoplanen och momsfilen. Dit hör alla tecken
  på Unicodes egen lista över tecken som inte ska synas, som står uttryckligen i koden (granskning 8, N1).
- **Högst en regel får passa.** Två regler som kan passa samma underlag (samma källa, typ, motpart och
  överlappande datum) stoppar regelboken redan när den läses in, som i `matchning.json`. Om ett underlag
  ändå passar flera regler (till exempel för att motparten står två gånger i en bankrad) blir det ett
  ärende, "flera regler". Det är det planterade felet i september.
- **Ingen regel passar** betyder ny eller okänd motpart. Då gissar Vera inte ett konto. Det blir ett ärende
  (avsnitt 5).
- Varje konto i regelboken måste finnas i kontoplanen, och varje varugrupp i momsfilen. Annars stoppas
  regelboken.
- En regels beloppsgräns får bara vara **lägre** än företagets gräns, aldrig högre. En regel kan alltså
  skärpa men inte lätta på.
- Okända nycklar, saknade nycklar och flyttal stoppar filen med ett tydligt fel, som i de andra
  formatfilerna.

### Filformat: `foretag/<namn>/regelbok.json`

Exemplet visar Syntet Testbutik med motparter ur testdatan. **Kontonumren är SYNTETISKA och inte
verifierade** (avsnitt 2). Nivåerna och gränserna är exempel som Hugo bestämmer.

```json
{
  "anteckning": "SYNTETISK regelbok för Syntet Testbutik AB. Konton, varugrupper och gränser är antagna och INTE verifierade av en redovisningskonsult.",
  "foretag": "syntet-testbutik",
  "version": 1,
  "godkand": {"av": "Godkännare 1 (påhittad)", "datum": "2026-10-25"},
  "granser": {
    "a_hogst_ore": 2000000,
    "b_hogst_ore": 4000000
  },
  "k9": {"minst_historik": 3, "hogst_procent_av_median": 300, "lagst_procent_av_median": 33},
  "regler": [
    {
      "id": "R-LEV-TE",
      "galler": {"kalla": "underlag", "typ": "leverantorsfaktura", "motpart": "LEV-TE"},
      "kontering": {"livsmedel": "4010"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "A",
      "anteckning": "Inköp av te för vidareförsäljning."
    },
    {
      "id": "R-LEV-KAFFE",
      "galler": {"kalla": "underlag", "typ": "leverantorsfaktura", "motpart": "LEV-KAFFE"},
      "kontering": {"livsmedel": "4010", "ovrigt": "4010"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "A",
      "anteckning": "Kaffe, och ibland tillbehör på samma faktura (SYNT-U-2025-020 har två momssatser)."
    },
    {
      "id": "R-BUTIK-STAD",
      "galler": {"kalla": "underlag", "typ": "kvitto", "motpart": "BUTIK-STAD"},
      "kontering": {"ovrigt": "5460"},
      "villkor": {"giltig_fran": "2025-01-01", "hogst_belopp_ore": 100000},
      "niva": "B"
    },
    {
      "id": "R-LEV-FORSAKRING",
      "galler": {"kalla": "underlag", "typ": "leverantorsfaktura", "motpart": "LEV-FORSAKRING"},
      "kontering": {"momsfritt": "6310"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "D",
      "anteckning": "Nivå D tills konsulten har svarat på periodisering och moms (avsnitt 8)."
    },
    {
      "id": "R-RESTAURANG-1",
      "galler": {"kalla": "underlag", "typ": "kvitto", "motpart": "RESTAURANG-1"},
      "kontering": {"livsmedel": "6071"},
      "villkor": {"giltig_fran": "2025-01-01", "avdragsbegransad": true},
      "niva": "D"
    },
    {
      "id": "R-Z-TB-KASSA-1",
      "galler": {"kalla": "z_rapport", "kassaregister": "TB-KASSA-1"},
      "kontering": {
        "forsaljning": {"livsmedel": "3002", "ovrigt": "3001"},
        "betalsatt": {"betalsatt_kontant": "1910", "betalsatt_kort": "1580", "betalsatt_swish": "1581"}
      },
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "B"
    },
    {
      "id": "R-BANK-KORTINLOSEN",
      "galler": {"kalla": "bankrad", "matchningsregel": "kortinlosen"},
      "kontering": {"motkonto": "1580", "avgift": "6570"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "C",
      "anteckning": "Nivå C tills kortinlösarens avgiftsspecifikation finns som underlag (avsnitt 4d)."
    },
    {
      "id": "R-BANK-SWISH",
      "galler": {"kalla": "bankrad", "matchningsregel": "swish"},
      "kontering": {"motkonto": "1581"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "B"
    },
    {
      "id": "R-BANK-KONTANT",
      "galler": {"kalla": "bankrad", "matchningsregel": "kontantinsattning"},
      "kontering": {"motkonto": "1910"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "B"
    },
    {
      "id": "R-BANK-AVGIFT",
      "galler": {"kalla": "bankrad", "matchningsregel": "bankavgift"},
      "kontering": {"kostnad": "6570"},
      "villkor": {"giltig_fran": "2025-01-01"},
      "niva": "B",
      "anteckning": "Inget underlag finns än (Ö11). Därför aldrig nivå A."
    }
  ]
}
```

Några saker att lägga märke till:

- **Kontering per varugrupp, inte per momssats.** Underlaget säger bara momssatsen, till exempel 12 %.
  Regeln säger vilka varugrupper motparten säljer. Kärnan slår upp vilken sats varugruppen har på
  underlagets datum (avsnitt 2) och kontrollerar att de stämmer (K5, avsnitt 6). Det är så det planterade
  felet SYNT-U-2025-019 (städartiklar med 12 %) fångas: BUTIK-STAD har bara varugruppen `ovrigt`.
- **Regler för bankrader utan underlag** pekar på regelns namn i `matchning.json`. De två filerna hänger
  alltså ihop: matchningen säger *att* raden inte kräver underlag, regelboken säger *hur* den bokförs.
- `godkand` och `version` är till för människor och för loggen. Det som skyddar är kontrollsumman.
- Ägartransaktioner (K7) har ingen regel som kan ge annat än D. En regel med motparten `AGARE-1` får bara
  ha nivå D, annars stoppas regelboken. Vilka motparter som är ägare eller närstående står i den valfria
  nyckeln `agare_och_narstaende`, en lista med motparter (för testbutiken `["AGARE-1"]`). Motparterna
  jämförs efter samma normalisering som ovan (Hugos beslut 2026-10-26, avsnitt 8).
- **Bankrader mot en ägare eller närstående** ska aldrig få lägre nivå än D, inte heller när en regel i
  `matchning.json` undantar raden från underlag (granskning 7, M7). Uppslaget
  `ar_bankrad_mot_agare_eller_narstaende` pekar ut en bankrad där en motpart i `agare_och_narstaende`
  står som hela ord i beskrivningen eller referensen, efter normaliseringen. Orden delas vid allt som inte
  är en bokstav, en siffra eller ett kombinerande tecken, så att `UTTAG AGARE-1/LAN` och `TILL:AGARE-1`
  pekas ut (granskning 8, N3). En sådan rad passar aldrig en regel i `matchning.json`
  (`matchningsregel_for_bankrad`), så ett förslag för den med en regel för bankrader stoppas, och en regel
  i `matchning.json` vars text nämner en ägare stoppar regelboken. Matchningen (`matcha_period`) får
  regelboken och tar matchningsformatet från den (`Regelbok.matchningsformat`), så den använder samma
  uppslag: raden hamnar aldrig bland dem som inte kräver underlag och blir aldrig "över gräns", utan kräver
  underlag som andra rader (K3, avsnitt 8). Själva nivån sätts i uppgift 6 (avsnitt 5 och 7, SPEC Ö13).

---

## 2. Kontoplan och momssatser

### `foretag/<namn>/kontoplan.json`

Kontoplanen gör två saker: den listar kontona, och den säger vilka konton som har en **roll** som
kärnan behöver känna till (till exempel "bankkontot" eller "utgående moms för en viss sats"). Rollerna
behövs eftersom kärnan aldrig får ha ett kontonummer i sin kod (SPEC 2).

```json
{
  "anteckning": "SYNTETISK kontoplan för Syntet Testbutik AB. Numren liknar BAS men är INTE verifierade. Ska kontrolleras av en redovisningskonsult och mot kundens bokföringsprogram.",
  "status": "SYNTETISK",
  "konton": [
    {"nummer": "1580", "namn": "Avräkning kortinlösen"},
    {"nummer": "1581", "namn": "Avräkning Swish"},
    {"nummer": "1910", "namn": "Kassa"},
    {"nummer": "1940", "namn": "Företagskonto"},
    {"nummer": "2440", "namn": "Leverantörsskulder"},
    {"nummer": "2611", "namn": "Utgående moms, sats 25"},
    {"nummer": "2621", "namn": "Utgående moms, sats 12"},
    {"nummer": "2641", "namn": "Ingående moms"},
    {"nummer": "3001", "namn": "Försäljning, övrigt"},
    {"nummer": "3002", "namn": "Försäljning, livsmedel"},
    {"nummer": "4010", "namn": "Inköp av varor"},
    {"nummer": "5460", "namn": "Förbrukningsmaterial"},
    {"nummer": "6071", "namn": "Representation"},
    {"nummer": "6310", "namn": "Företagsförsäkringar"},
    {"nummer": "6570", "namn": "Bank- och kortavgifter"}
  ],
  "roller": {
    "bank": "1940",
    "leverantorsskulder": "2440",
    "ingaende_moms": "2641",
    "utgaende_moms_per_sats": {"25": "2611", "12": "2621"}
  }
}
```

- Ett konto är text, inte ett tal, så att ett konto som börjar med noll inte förlorar nollan.
- Varje konto i `roller` och i regelboken måste finnas i `konton`. Annars stoppas filen.
- Ett konto får bara ha en roll (granskning 7, M12). Bankkontot får till exempel inte också vara kontot
  för ingående moms. Samma konto får däremot vara kontot för utgående moms med flera satser, eftersom det
  är samma roll.
- I version 1 läses kontoplanen ur filen. Enligt SPEC 2.1 ska den senare läsas ur kundens program, och
  då ska de två jämföras.
- Vilket konto som ska användas för vad är ett **bokföringsmässigt val**. Hugo kan bestämma formatet, men
  inte numren för en riktig kund (avsnitt 8).

### `foretag/<namn>/momssatser.json`

Momsfilen finns redan som beslut i SPEC 11 (för K5). Förslag på form:

```json
{
  "anteckning": "SYNTETISKA momssatser för Syntet Testbutik AB, utlästa ur testdata/README.md. INTE verifierade mot Skatteverket eller en redovisningskonsult (Ö3, Ö-T2).",
  "status": "SYNTETISK",
  "varugrupper": {
    "livsmedel": [
      {"fran": "2025-01-01", "till": null, "sats": 12, "kalla": "SYNTETISK, testdata/README.md"}
    ],
    "ovrigt": [
      {"fran": "2025-01-01", "till": null, "sats": 25, "kalla": "SYNTETISK, testdata/README.md"}
    ],
    "momsfritt": [
      {"fran": "2025-01-01", "till": null, "sats": 0, "kalla": "SYNTETISK. Öppen fråga: moms på försäkring"}
    ]
  },
  "moms_tolerans_ore_per_rad": 1
}
```

- **Satser per datum.** En varugrupp har en lista med perioder. När en sats ändras läggs en ny period
  till, och den gamla får ett slutdatum. Gamla rader ändras aldrig, så att en gammal faktura kontrolleras
  mot satsen som gällde då.
- Perioderna för en varugrupp får inte överlappa och inte ha glapp. Annars stoppas filen.
- Satsen är ett heltal i procent, eftersom underlagets `momssats` redan är det. Behövs en sats som inte är
  ett helt tal måste formatet ändras.
- **Ingen sats i filen är en skatteregel.** Varje sats har fältet `kalla`, och för testföretaget står det
  SYNTETISK. För en riktig kund ska `kalla` peka på ett beslut från en redovisningskonsult.
- `moms_tolerans_ore_per_rad` är hur många öre momsen på en momsrad får skilja från sats × belopp.
  Värdet 1 är ett antagande, se avsnitt 6 och 8.

---

## 3. Konteringsförslag

### Datastrukturen

Ett **konteringsförslag** är en verifikation som ännu inte är bokförd, plus allt som behövs för att en
människa ska kunna förstå och godkänna den. Exempel: betalningen av leverantörsfakturan SYNT-U-2025-003.

```json
{
  "forslag_id": "F-2025-02-0007",
  "verifikation": {
    "datum": "2025-02-06",
    "text": "Betalning LEV-TE, faktura SYNT-TE-761",
    "rader": [
      {
        "konto": "2440",
        "debet_ore": 1673056,
        "kredit_ore": 0,
        "ursprung": {"berakning": "lika", "fran": [
          {"kalla": "underlag", "id": "SYNT-U-2025-003", "falt": "belopp_ore"}
        ]}
      },
      {
        "konto": "1940",
        "debet_ore": 0,
        "kredit_ore": 1673056,
        "ursprung": {"berakning": "lika", "fran": [
          {"kalla": "bankrad", "id": "BANK-…", "falt": "belopp_ore"}
        ]}
      }
    ]
  },
  "kopplingar": {
    "underlag": [{"id": "SYNT-U-2025-003", "kontrollsumma": "…"}],
    "bankrader": [{"id": "BANK-…", "radnr": 26, "filens_kontrollsumma": "…"}],
    "z_rapporter": [],
    "regel": {"id": "R-LEV-TE", "regelbokens_kontrollsumma": "…", "kontoplanens_kontrollsumma": "…",
              "momsfilens_kontrollsumma": "…", "matchningsformatets_kontrollsumma": "…"}
  },
  "motivering": "Bankraden matchar fakturan SYNT-TE-761 (samma belopp, motpart LEV-TE, inom 40 dagar). Regeln R-LEV-TE.",
  "kontroller": {"K2": "ok", "K3": "ok", "K5": "ej aktuell", "K8": "ok", "K9": "ok"},
  "niva": "A",
  "nivans_skal": ["regel R-LEV-TE har nivå A"],
  "arenden": []
}
```

**Nyckelnamn för bankrader i DESIGN-exemplet och i koden** (granskning 7, M11). Exemplet ovan pekade
förut ut en bankrad med filen och radnumret. Koden pekar i stället ut den med bankradens `id`, som
`las_bankfil` ger varje rad (`BANK-` och 16 tecken av radens kontrollsumma), eftersom ett radnummer bara är
unikt inom en fil. Exemplet visar nu kodens nyckelnamn, och namnen i koden är inte ändrade. Avvikelsen från
exemplet som D17 godkände är godkänd av Hugo 2026-10-27 (uppdraget efter granskning 8). De andra
nyckelnamnen i exemplen gäller som de står (D17).

| Var | Förut i DESIGN-exemplet | I koden (och nu i exemplet) |
|---|---|---|
| En källa i `ursprung` | `{"kalla": "bankrad", "fil": …, "radnr": …, "falt": "belopp_ore"}` | `{"kalla": "bankrad", "id": …, "falt": "belopp_ore"}` |
| `bankrader` i `kopplingar`, i förslaget som byggs | `{"fil": …, "radnr": …, "filens_kontrollsumma": …}` | `{"id": …}` |
| `bankrader` i `kopplingar`, i det färdiga förslaget | `{"fil": …, "radnr": …, "filens_kontrollsumma": …}` | `{"id": …, "radnr": …, "filens_kontrollsumma": …}`, där radnumret och kontrollsumman kommer från inläsningen |

- **Belopp är heltal i öre**, aldrig flyttal (SPEC 7). En rad har antingen debet eller kredit större än
  noll, aldrig båda, och inget belopp är negativt. Minus visas genom att beloppet står på andra sidan.
- **`kopplingar`** säger vilka underlag, bankrader, Z-rapporter och vilken regel förslaget bygger på, med
  kontrollsumman för varje fil. Ändras en fil efteråt syns det. `regel` har också kontrollsummorna för de
  fyra filerna som förslaget är byggt mot: regelboken, kontoplanen, momsfilen och matchningsformatet
  (granskning 7, M4). Koden som bygger förslaget skriver dem, K2 jämför dem med de inlästa filerna, och
  förslaget får summorna från de inlästa filerna. Att jämföra dem med en godkänd summa hör till
  spärrsteget (SPEC Ö12).
- **`ursprung`** finns på **varje rad**. Det säger vilka värden i källorna beloppet kommer ifrån och hur det
  räknas fram. Bara tre sätt finns:
  - `lika`: beloppet är exakt ett värde ur en källa,
  - `summa`: beloppet är summan av flera värden,
  - `skillnad`: det första värdet minus resten (till exempel kortavgiften: kortförsäljningen minus
    insättningen, avsnitt 4d).
  Ett negativt värde i källan (pengar ut på banken) räknas som positivt.
- Verifikationsnumret sätts inte här. Det sätts först när verifikationen bokförs efter godkännande, i
  kundens program eller i SIE-filen.
- Förslaget kan inte ändras när det väl är skapat (som matchningens resultat). En kundinstruktion blir ett
  **nytt** förslag (SPEC 4).

### Kontrollen K2 (debet = kredit)

K2 körs i Python på varje förslag, och ett förslag som inte klarar den skapas aldrig (det blir ett fel i
kärnan, inte ett ärende, eftersom det betyder att koden räknat fel):

1. Förslaget är byggt mot samma filer som det kontrolleras mot. Kontoplanen är den som regelboken
   kontrollerades mot (samma kontrollsumma), eftersom regelbokens konton och roller bara betyder något
   med den kontoplanen. Förslagets fyra kontrollsummor i `regel` är de som regelboken, kontoplanen, och
   momsfilen och matchningsformatet som regelboken kontrollerades mot, faktiskt har. Kontrollsummorna
   räknas när filerna läses (`las_regelbok`, `las_kontoplan`, `las_momssatser`, `las_matchningsformat`),
   på exakt de bytes som sedan kontrolleras (granskning 7, M4).
2. Verifikationen har minst två rader.
3. Varje belopp är ett heltal, inte ett sanningsvärde (True eller False räknas annars som 1 och 0 i
   Python), inte negativt och har högst 15 siffror.
4. På varje rad är exakt ett av `debet_ore` och `kredit_ore` större än noll.
5. Summan av all debet är lika med summan av all kredit.
6. Varje konto finns i kontoplanen och gäller på verifikationens datum.

### Kontrollen av ursprunget

Körs direkt efter K2, också i Python:

1. Varje rad har ett `ursprung` med minst ett värde i `fran` (exakt ett för `lika`, minst två för `summa`
   och `skillnad`), och samma värde står inte två gånger på samma rad.
2. Varje värde pekar på något som verkligen finns i den här körningen: ett underlag i
   underlagsperioden, en bankrad i bankperioden, en post i en Z-rapport i kassaperioden. Funktionen tar
   bara emot perioderna från de enda tillåtna inläsningsfunktionerna (SPEC 7), så att ingen källa kan ha
   ändrats eller lagts till efter kontrollerna. Ett objekt som har skapats förbi sin inläsningsfunktion
   (till exempel med `__new__`) stoppas med ett tydligt fel (granskning 7, M12).
3. Kontrollen räknar själv om beloppet från källorna med `berakning`, och det ska bli exakt radens belopp.
4. Varje källa i `ursprung` står också i `kopplingar`, och tvärtom används varje underlag, bankrad och
   Z-rapport i `kopplingar` av minst en rad. Regeln i `kopplingar` finns i regelboken.
5. En rad på ett **momskonto** har bara momsbelopp som ursprung, och rätt sorts moms. På kontot för
   **ingående moms** (rollen `ingaende_moms`) är det `moms_ore` i en momsrad i ett underlag. På ett konto
   för **utgående moms** (rollen `utgaende_moms_per_sats`) är det en momspost i en Z-rapport, med kontots
   egen sats. Sidan (debet eller kredit) prövas inte, eftersom kreditnotor inte är bestämda (D16).
6. En rad på **bankkontot** (rollen `bank`) har bara bankrader som ursprung, räknade med `lika` eller
   `summa`, och står på rätt sida: pengar in i debet, pengar ut i kredit.
7. **Täckningen:** raderna tillsammans använder varje värde i källorna högst en gång per sida, så att inget
   räknas två gånger (se nedan).
8. **Regeln passar förslaget** (granskning 7, M3). Verifikationens datum ligger inom regelns giltighet
   (`giltig_fran` till `giltig_till`). Förslaget har minst en källa av det slag regeln gäller (underlag,
   Z-rapport eller bankrad), och varje sådan källa har just den här regeln i regelboken på verifikationens
   datum: för ett underlag avgör typen och motparten, för en Z-rapport kassaregistret och för en bankrad
   regeln i `matchning.json` som raden passar. Varje konto på raderna står i regelns kontering eller är ett
   **rollkonto** (ett konto som kontoplanen pekar ut för en roll: bankkontot, leverantörsskulderna och
   momskontona). Punkt 8 körs efter täckningen, så att ett värde som räknas två gånger visas först.

Rollerna slås upp i kontoplanen med `kontots_roller`, så att kärnan inte har något kontonummer i sin kod.

**Täckningen.** Varje källa består av **delar**:

- ett **underlag**: en del per momsrad och fält, `underlag_ore` och `moms_ore`. `belopp_ore` består av
  alla underlagets delar, eftersom det är summan av momsraderna (K13),
- en **bankrad**: en del, bankradens belopp,
- en **Z-rapport**: försäljningen med en sats består av två delar, försäljningen utan moms och momsen med
  samma sats. Momsposten är bara momsdelen, och totalsumman består av alla försäljningens delar. Ett
  betalsätt är en egen del.

För debet och för kredit räknas hur många gånger varje del används, med tecken: på en rad som räknas med
`skillnad` dras källorna efter den första ifrån (minus en gång), annars läggs de till (plus en gång).
Regeln:

- **a.** Varje del används 0 eller 1 gång i debet, och 0 eller 1 gång i kredit.
- **b.** På varje sida är det som kommer från ett underlag antingen 0 eller hela `belopp_ore`: underlaget
  används helt eller inte alls på en sida.

Så här blir det med exemplen och granskning 7:s prov (SYNT-U-2025-003: 14 938,00 kr plus moms 12 %
1 792,56 kr, att betala 16 730,56 kr):

| Förslag | Debet | Kredit | Utfall |
|---|---|---|---|
| 4a fakturan | utan moms 1, moms 1 (= hela underlaget) | `belopp_ore`: utan moms 1, moms 1 | godtas |
| 4a betalningen | underlaget helt | bankraden 1 | godtas |
| 4c Z 1001 | kontant 1, kort 1, Swish 1 | försäljning utan moms 1 per sats (skillnad: momsen +1 −1 = 0), moms 1 per sats | godtas |
| 4d kortinlösen | bankraden +1 −1 = 0, kort 1 | kort 1 | godtas |
| 4e bankavgiften | bankraden 1 | bankraden 1 | godtas |
| Swish, summa av två bankrader | bankrad 1: 1, bankrad 2: 1 | Swish 1 | godtas |
| P01, momsen två gånger | moms **2** | | stoppas (a) |
| P02, momsen i bruttot och för sig | `belopp_ore` och momsen: moms **2** | | stoppas (a) |
| P03, samma bankrad två gånger | bankraden **2** | | stoppas (a) |
| P10, skillnad mellan två underlag | SYNT-U-2025-005 **−1** | | stoppas (a) |
| Underlaget utan momsen | 14 938,00 av 16 730,56 kr | | stoppas (b) |

Täckningen säger inget om vilka konton som används, bara att varje värde räknas en gång (kontona prövas i
punkt 8). Om en del i en
Z-rapport saknas (till exempel kortförsäljningen, som bokförs mot banken senare i flöde 4d) är det
tillåtet: en Z-rapport kan delas på flera verifikationer, ett underlag kan det inte.

Ett förslag som inte klarar ursprungskontrollen skapas inte heller. På så sätt bär varje rad sitt
ursprung, ingen siffra i en verifikation kan komma från modellen, och inget värde räknas två gånger.

---

## 4. Flödena

Exemplen visar hur verifikationerna skulle se ut **om** de val som står under "får inte gissas" görs på
ett visst sätt. De valen är inte gjorda. Kontona är de SYNTETISKA ur avsnitt 2. Beloppen står i kronor
för att vara lättare att läsa, men lagras i öre.

### (a) Leverantörsfaktura och dess betalning

**Exempel:** SYNT-U-2025-003, LEV-TE, faktura SYNT-TE-761, daterad 2025-01-07, att betala 16 730,56 kr
(14 938,00 kr plus moms 12 % 1 792,56 kr). Betald 2025-02-06, `bank_2025-02.csv` radnummer 26.

**Om faktureringsmetoden används** blir det två verifikationer:

| Verifikation | Datum | Konto | Debet | Kredit | Ursprung |
|---|---|---|---|---|---|
| 1. Fakturan | 2025-01-07 | 4010 Inköp av varor | 14 938,00 | | momsraden, `underlag_ore` |
| | | 2641 Ingående moms | 1 792,56 | | momsraden, `moms_ore` |
| | | 2440 Leverantörsskulder | | 16 730,56 | `belopp_ore` |
| 2. Betalningen | 2025-02-06 | 2440 Leverantörsskulder | 16 730,56 | | `belopp_ore` |
| | | 1940 Företagskonto | | 16 730,56 | bankraden |

**Om kontantmetoden används** blir det en verifikation på betaldagen: 4010 och 2641 i debet, 1940 i
kredit. Fakturor som är obetalda när räkenskapsåret slutar bokförs då som i verifikation 1.

**Fler exempel ur testdatan:**

- **SYNT-U-2025-020**, LEV-KAFFE, två momssatser: en kostnadsrad och en momsrad per momsrad i underlaget
  (12 % och 25 %). Regeln har båda varugrupperna.
- **SYNT-U-2025-004** är en dublett av 003 (K4). Inget förslag skapas för den. Den finns redan som ärende.
- **Fakturor som är obetalda 31 mars**: med faktureringsmetoden har de verifikation 1 men ingen betalning.
  De är "oavstämda underlag" i matchningen och ska synas i K10 (leverantörsskulder).
- **SYNT-U-2025-005**, LEV-FORSAKRING, helårspremie 9 600,00 kr utan moms, betald 2025-02-07: ska den
  kostnadsföras direkt eller fördelas över året? Därför nivå D i exemplet.
- **SYNT-U-2025-021**, HYRESVARD, hyra för **andra** kvartalet, avi 2025-03-03 och betald 2025-03-31:
  samma fråga. Hyran gäller april–juni men betalas i mars.

**Får inte gissas:** faktureringsmetod eller kontantmetod. Vilket konto varje motpart ska på. Om och hur
försäkring och förskottsbetald hyra ska fördelas. Vilket datum verifikationen ska ha. Om momsen på hyran
får dras av (Ö-T8) och om försäkringen har moms.

### (b) Kvitto betalat med kort

**Exempel:** SYNT-U-2025-015, BUTIK-FORBRUKNING, kvitto daterat 2025-02-10, 247,00 kr (197,60 kr plus moms
25 % 49,40 kr). Företagets kort dras direkt från företagskontot: `bank_2025-02.csv` radnummer 50,
`KORTKOP-20250210`, transaktionsdag 2025-02-10, bokföringsdag 2025-02-11.

En verifikation:

| Datum | Konto | Debet | Kredit | Ursprung |
|---|---|---|---|---|
| 2025-02-10 | 5460 Förbrukningsmaterial | 197,60 | | momsraden, `underlag_ore` |
| | 2641 Ingående moms | 49,40 | | momsraden, `moms_ore` |
| | 1940 Företagskonto | | 247,00 | bankraden |

**Planterade fel som stoppar eller höjer förslaget:**

- **SYNT-U-2025-019**, BUTIK-STAD med 12 %: regeln har bara varugruppen `ovrigt` (25 %). K5 ger ett
  ärende, nivå D (avsnitt 6).
- **SYNT-U-2025-028**, RESTAURANG-1, 2 146,00 kr en söndag: regeln är avdragsbegränsad. K8 ger ett ärende,
  nivå D. Vera föreslår ingen fördelning mellan avdragsgill och icke avdragsgill del.
- **`bank_2025-02.csv` radnummer 85**, kortköp 351,00 kr utan kvitto: inget förslag. Matchningen gör det
  till "saknat underlag" efter 7 dagar (K3).

**Får inte gissas:** vilket datum som gäller (kvittots datum, transaktionsdagen eller bankens
bokföringsdag). Vilket konto. Hur ett restaurangkvitto eller ett privat köp ska bokföras. Om företagets kort
skulle vara ett kreditkort med egen faktura ser flödet annorlunda ut, och det är inte med här.

### (c) Kassans dagsavslut (Z-rapport)

**Exempel:** `kassa_2025-01-02.csv`, Z-nummer 1001, kassa TB-KASSA-1:

| Post | Sats | Belopp |
|---|---|---|
| Försäljning | 12 % | 4 242,00 (varav moms 454,50) |
| Försäljning | 25 % | 1 723,00 (varav moms 344,60) |
| Kontant | | 956,00 |
| Kort | | 4 115,00 |
| Swish | | 894,00 |
| Totalsumma | | 5 965,00 |

En verifikation per Z-rapport, där betalsätten går till avräkningskonton:

| Datum | Konto | Debet | Kredit | Ursprung |
|---|---|---|---|---|
| 2025-01-02 | 1910 Kassa | 956,00 | | `betalsatt_kontant` |
| | 1580 Avräkning kortinlösen | 4 115,00 | | `betalsatt_kort` |
| | 1581 Avräkning Swish | 894,00 | | `betalsatt_swish` |
| | 3002 Försäljning, livsmedel | | 3 787,50 | skillnad: försäljning 12 % minus moms 12 % |
| | 2621 Utgående moms, sats 12 | | 454,50 | `moms`, 12 % |
| | 3001 Försäljning, övrigt | | 1 378,40 | skillnad: försäljning 25 % minus moms 25 % |
| | 2611 Utgående moms, sats 25 | | 344,60 | `moms`, 25 % |
| | **Summa** | **5 965,00** | **5 965,00** | |

Förslaget skapas bara från en `Kassaperiod` från `las_kassaperiod`, så att Z-kontrollerna (K11) och
Z-serien (K12) redan har körts. Vilken försäljningsrad som går till vilket konto avgörs av satsen: satsen
12 % slås upp i momsfilen och ska höra till exakt en av regelns varugrupper på datumet (K5 för kassan).
Passar satsen två varugrupper med olika konton blir det ett ärende.

**Varför avräkningskonton:** kortförsäljningen kommer till banken först nästa bankdag, Swish kommer som
många små bankrader och kontanterna sätts in en gång i veckan. Med avräkningskonton får varje bankrad en
egen verifikation (flöde d), och kontona ska gå jämnt ut. Ett konto som inte blir noll är en signal som
K10 kan visa. Det är ett förslag, inte ett bokföringsbeslut.

**Saknad Z-rapport:** Z 1011, 2025-01-15, saknas. Inget förslag skapas för dagen. Det är ett ärende på nivå
D (SPEC 6.2). Bankraderna för den dagen (till exempel `AVR-20250115` och tre Swish-rader) har ingen
försäljning att stämmas av mot och blir också ärenden.

**Får inte gissas:** om kassan ska bokföras per dag eller samlat per vecka (Ö4, Ö-T24). Vilka konton.
Avräkningskonton eller direkt mot banken. Hur skillnad mellan räknad kassa och Z-rapporten ska bokföras
(Ö-T4). Presentkort och returer (från Q2, Ö-T14 och Ö-T22).

### (d) Kortinlösens insättning, Swish och kontantinsättning

De här bankraderna kräver inget underlag (`matchning.json`). De stäms i stället av mot Z-rapporterna.

**Kortinlösen.** `bank_2025-01.csv` radnummer 3, 2025-01-03, `AVR-20250102`, 4 065,62 kr. Datumet i
referensen pekar på Z-rapporten för 2025-01-02, där kortförsäljningen var 4 115,00 kr. Skillnaden 49,38 kr
är kortinlösarens avgift (testdatan antar 1,2 %, SYNTETISKT).

| Datum | Konto | Debet | Kredit | Ursprung |
|---|---|---|---|---|
| 2025-01-03 | 1940 Företagskonto | 4 065,62 | | bankraden |
| | 6570 Bank- och kortavgifter | 49,38 | | skillnad: Z-rapportens kort minus bankraden |
| | 1580 Avräkning kortinlösen | | 4 115,00 | Z-rapportens `betalsatt_kort` |

Avgiften har i dag **inget eget underlag**: kortinlösarens specifikation finns inte i testdatan. Därför är
regeln nivå C, och avgiften visas tydligt som "räknad som skillnad, utan specifikation". Är skillnaden
negativ (mer in än kortförsäljningen) eller saknas Z-rapporten för datumet blir det ett ärende.

**Swish.** `bank_2025-01.csv` radnummer 1 och 2, 323,00 och 571,00 kr. Varje rad blir en verifikation:
1940 i debet, 1581 Avräkning Swish i kredit. Tillsammans är de 894,00 kr, lika med Swish i Z 1001.
Lördagens Swish bokförs av banken på måndagen, så raderna kopplas till Z-rapporten via transaktionsdagen
och referensen, inte via bokföringsdagen.

**Kontantinsättning.** `bank_2025-01.csv` radnummer 20, 2025-01-07, `INS-20250107`, 3 719,00 kr: 1940 i
debet, 1910 Kassa i kredit. Beloppet är kontanterna från 2 januari (956,00), 3 januari (1 832,00) och 4
januari (931,00). Att insättningen stämmer mot Z-rapporterna sedan förra insättningen hör till K10.
Kontanterna från 31 mars ligger kvar i kassan, så kassakontot har ett saldo vid kvartalets slut.

**Får inte gissas:** om kortavgiften ska bokföras för sig (brutto) och om den har moms (Ö-T5). Om en
avgift som räknats fram som skillnad räcker som underlag. Om Swish ska bokföras per bankrad eller per dag,
och om Swish har avgifter. Hur kontantinsättningen och kassadifferenser bokförs (Ö-T4).

### (e) Bankavgifter

**Exempel:** `bank_2025-01.csv` radnummer 117 (`AVG-2025-01`, BANK AVGIFT FORETAGSKONTO, 125,00 kr) och
radnummer 118 (BANK AVGIFT KORTINLOSEN, 199,00 kr). En verifikation per rad:

| Datum | Konto | Debet | Kredit | Ursprung |
|---|---|---|---|---|
| 2025-01-31 | 6570 Bank- och kortavgifter | 125,00 | | bankraden |
| | 1940 Företagskonto | | 125,00 | bankraden |

Ingen momsrad, eftersom det inte finns något underlag som visar moms. Raderna ligger under gränsen 250 kr
i `matchning.json`. En avgiftsrad över gränsen är redan ett ärende, "över gräns", och får inget förslag.
När bankens specifikation blir ett riktigt underlag (Ö11) flyttas avgifterna till flöde (b), med underlag.

**Får inte gissas:** om bankavgifterna har moms. Vilket konto. Om en avgift utan specifikation räcker
som underlag.

---

## 5. Nivåerna A–D

Nivån räknas fram i Python, i två steg:

1. **Regelns nivå** är startpunkten.
2. **Varje skäl till en högre nivå** höjer den. Den **högsta** nivån vinner. Ingenting kan sänka nivån.

Alla skäl skrivs in i `nivans_skal`, så att godkännaren ser varför en post hamnade där.

| Nivå | Förslag som hamnar här | Exempel ur testdatan |
|---|---|---|
| **A** | Regeln har nivå A, beloppet ligger under `a_hogst_ore`, regeln har godkänts minst `minst_historik` gånger förut, och alla kontroller är utan anmärkning. Bankrader utan underlag blir aldrig A | LEV-TE efter de första fakturorna |
| **B** | Regeln har nivå B, eller ett A-förslag som inte klarar villkoren ovan. Beloppet ligger under `b_hogst_ore` och under regelns egen gräns | BUTIK-STAD, Swish, bankavgifter, Z-rapporter |
| **C** | Belopp över `b_hogst_ore` eller över regelns gräns. Första gången en regel används. Ovanligt belopp (K9). Rättelse (motverifikation). Invändning från granskaren. Möjlig dublett eller samma fakturanummer med olika belopp eller datum (K4a, K4b, K4c). Bankrad med flera möjliga underlag ("tvetydig"). Avgift utan underlag (kortinlösen) | Hyran 45 000 kr ligger över B-gränsen 40 000 kr i exemplet. Kortavgiften |
| **D** | Ägare och närstående (K7). Avdragsbegränsat (K8). Fel momssats eller sats som saknas för datumet (K5). Saknad Z-rapport (6.2). Fel period (K6). Bokslutspost och periodisering. Text som försöker styra agenten (K17). Oklar post | SYNT-U-2025-019 (K5), SYNT-U-2025-028 (K8), Z 1011 som saknas, försäkringen |

**Ny motpart** (ingen regel passar): Vera har inget konto att föreslå och får inte gissa. Därför blir det
inget förslag utan ett ärende på nivå C, där människan väljer konto. Svaret används för just den posten,
och blir ett regelförslag som en människa kan lägga in i regelboken. Agenten lägger aldrig in det själv.

Det som **stoppar** (K1 saldokedjan, K11 och K12 i kassan, K13 i underlaget, trasiga filer) ger inget
förslag och ingen nivå alls. Hela filen eller perioden stoppas, som i dag.

Nivån styr bara hur godkännandet visas i automatiskt läge. I granskat läge godkänns allt löpande ändå
(SPEC 5).

---

## 6. Kontrollerna K5, K8 och K9

### K5: momsen stämmer med underlaget och satsen finns för datumet

**Definition.** För varje momsrad i ett underlag:

1. **Satsen finns.** Det finns minst en varugrupp i momsfilen med just den satsen på underlagets datum.
2. **Satsen passar regeln.** Satsen är satsen för en av varugrupperna i regelns `kontering` på datumet,
   och för exakt en av dem (eller flera med samma konto). Annars kan kärnan inte veta vilket konto raden ska
   till.
3. **Momsen stämmer med satsen.** `moms_ore` skiljer högst `moms_tolerans_ore_per_rad` från
   `underlag_ore × sats / 100`. Beräkningen görs med heltal: `abs(moms_ore × 100 − underlag_ore × sats)`
   ska vara högst `tolerans × 100`.

För en Z-rapport: punkt 1 och 2 gäller varje försäljningsrad, med regeln för kassan. Punkt 3 är redan
Z-kontroll e i K11.

**Resultat.** Ett ärende, "fel momssats" eller "moms stämmer inte med satsen", nivå D, med satsen i
underlaget och satsen som momsfilen och regeln väntar sig. Fångar SYNT-U-2025-019 (12 % i stället för
25 %) och det planterade felet i november ("moms mer än 20 % av bruttot", vilket betyder en sats över 25 %
eller fel räknad moms).

**Behöver i konfigurationen:** `momssatser.json` (varugrupper och satser per datum, toleransen) och
regelbokens `kontering` per varugrupp.

**Inte med:** omvänd moms vid EU-köp (från Q2, Ö-T7). Det kräver en egen sorts momsrad och är en
expertfråga.

### K8: avdragsbegränsat

**Definition.** Ett förslag är avdragsbegränsat om regeln som används har `"avdragsbegransad": true`. Då
blir det alltid ett ärende på nivå D, och Vera föreslår bara vilket underlag och vilken bankrad det gäller,
aldrig hur stor del som får dras av.

Dessutom en **varningssignal**, som inte själv avgör: ett kvitto daterat en dag då företaget har stängt
får flaggan "köpt en dag då företaget har stängt" och visas i ärendet. Det är så SYNT-U-2025-028 (en
söndag) blir extra tydligt. Signalen höjer bara till D om regeln också är avdragsbegränsad. Ett köp på en
stängd dag kan ju vara helt i sin ordning.

**Behöver i konfigurationen:** `avdragsbegransad` i regelboken, och en lista över företagets stängda
dagar (veckodagar och datum), till exempel i en ny nyckel `oppettider` i regelboken. Vilka motparter och
kostnader som är avdragsbegränsade bestäms av en människa, med stöd av en konsult.

### K9: ovanliga belopp

**Definition.** För ett förslag med en regel som har använts förut:

1. Hämta beloppen i de tidigare **godkända** förslagen med samma regel.
2. Finns färre än `minst_historik` stycken gör K9 inget. (Första gångerna blir ändå nivå C, avsnitt 5.)
3. Räkna ut **medianen**.
4. Beloppet är ovanligt om `belopp × 100 > median × hogst_procent_av_median` eller
   `belopp × 100 < median × lagst_procent_av_median`. Bara heltal.

**Resultat.** Ett ärende, "ovanligt belopp", nivå C, med beloppet, medianen och antalet tidigare
belopp. Fångar det planterade felet i juli (belopp långt över snittet för en känd motpart).

**Behöver i konfigurationen:** `k9` i regelboken (företagets värden) och, om det behövs, egna värden per
regel. Värdena i exemplet (3, 300 %, 33 %) är påhittade och bestäms av Hugo.

**Viktigt:** historiken får bara läsas från den skyddade loggen över godkända och bokförda poster, aldrig
från en mapp agenten kan skriva i (SPEC 7). Annars skulle agenten kunna flytta medianen. Tills loggen
finns kan K9 inte byggas fullt ut (avsnitt 7).

---

## 7. Byggordning

Sex små uppgifter, en per session. De tre första kräver inga bokföringsbeslut. Uppgift 4 och 5 kräver
att Hugo har bestämt hur testföretaget ska bokföras (avsnitt 8), eller att uppgiften byggs med ett
SYNTETISKT val som tydligt står i konfigurationen och kan bytas utan att kärnan ändras.

Innan uppgift 1: Hugo ska godkänna det här förslaget, och de nya filerna i `foretag/syntet-testbutik/`.
Regelboken räknas som något agenten inte får ändra utan Hugos ord (CLAUDE.md).

| # | Uppgift | Ska bevisa |
|---|---|---|
| 1 | **Läsa kontoplan och momsfil** (`kontoplan.json`, `momssatser.json`) med samma stränga kontroller som de andra formatfilerna, och en funktion som slår upp satsen för en varugrupp på ett datum | Trasiga filer stoppas (okänd nyckel, flyttal, konto som saknas, perioder som överlappar eller har glapp). Satsen på ett datum före och efter en ändring blir rätt. Inget kontonummer eller momssats finns i kärnan (testet i `test_karnan_ar_generell.py` utökas) |
| 2 | **Läsa regelboken** och slå upp regeln för ett underlag, en bankrad eller en Z-rapport | Två regler som kan passa samma sak stoppar filen. Konto eller varugrupp som saknas stoppar filen. En regel kan inte ha högre gräns än företaget. En regel för `AGARE-1` som inte är D stoppas. En ändrad regelbok får en ny kontrollsumma (förberedelse för spärrtestet) |
| 3 | **Konteringsförslaget som datastruktur**, med K2 och ursprungskontrollen, utan några flöden | Obalans stoppas. En rad med både debet och kredit, ett negativt belopp, ett flyttal eller True stoppas. En rad utan ursprung, eller vars belopp inte går att räkna fram ur ursprunget, stoppas. Förslaget går inte att ändra |
| 4 | **Flöde a, b och e**: leverantörsfakturor, kvitton och bankavgifter, med K5 och K8 | Mot testdatan Q1: SYNT-U-2025-003 och dess betalning ger exakt verifikationerna i avsnitt 4a. SYNT-U-2025-019 blir K5, nivå D. SYNT-U-2025-028 blir K8, nivå D. SYNT-U-2025-004 får inget förslag. Summan av ingående moms stämmer med summan av underlagens moms |
| 5 | **Flöde c och d**: Z-rapporter, kortinlösen, Swish och kontantinsättningar | Försäljningen per sats och månad stämmer på öret med `facit.json`. Avräkningskontona går jämnt ut för varje hel dag. Z 1011 som saknas ger ett D-ärende, och dagens bankrader blir ärenden. Kortavgiften är skillnaden och visas som "utan specifikation" |
| 6 | **Nivåerna A–D och K9** | Varje skäl i avsnitt 5 ger rätt nivå. Den högsta nivån vinner, och inget sänker den. K9 läser bara historik från den skyddade platsen och gör inget med för lite historik. Kräver att loggen över godkända poster finns. Annars byggs nivåerna utan K9, och K9 skjuts upp och sägs till |

Varje uppgift avslutas med full testsvit och slutrapportrutan. Oberoende granskning i en ny session efter
uppgift 3 och efter uppgift 6.

---

## 8. Öppna frågor

D17–D21 är besvarade av Hugo (se beslutet under tabellen). D1–D16 är öppna. Där det står ett värde i exemplen ovan är det ett antagande som
ska **verifieras**, inte ett svar. Numren D1–D21 är nya. Där en fråga redan finns i SPEC (Ö) eller i
FIKTIVT_FORETAG.md (Ö-T) står det.

### Kräver en redovisningskonsult eller Skatteverket

| # | Fråga |
|---|---|
| D1 | **Faktureringsmetoden eller kontantmetoden?** Får testföretaget och första kunderna använda kontantmetoden, och vad krävs för det? Avgör om flöde (a) ger en eller två verifikationer |
| D2 | **Kontoplan.** Vilka BAS-konton ska användas för varje händelse i flödena? Alla nummer i avsnitt 2 är SYNTETISKA |
| D3 | **Momssatser 2025** för te och kaffe, tillbehör och blandade presentförpackningar, och hur en satsändring under året ska hanteras (Ö3, Ö-T2) |
| D4 | **Momsavrundning på leverantörsfakturor och kvitton.** Hur många öre får momsen på en rad skilja från sats × belopp? Räknar leverantörer momsen per rad eller på totalen? (Toleransen 1 öre är ett antagande. Ö3 för kassan) |
| D5 | **Kassans dag.** Ska Z-rapporten bokföras per dag eller samlat per vecka (Ö4, Ö-T24)? På vilket datum? Avräkningskonton eller direkt mot banken? |
| D6 | **Kassadifferens och kontantinsättning:** hur bokförs skillnad mellan räknad kassa och Z-rapporten, och insättningen till banken (Ö-T4)? |
| D7 | **Kortinlösen:** brutto eller netto, har avgiften moms, och räcker en avgift räknad som skillnad som underlag, eller krävs kortinlösarens specifikation (Ö-T5)? |
| D8 | **Swish:** en verifikation per bankrad eller per dag? Har Swish avgifter som ska bokföras för sig? |
| D9 | **Moms på försäkring.** Fakturan i testdatan har ingen moms. Hur ska försäkringspremien behandlas momsmässigt? |
| D10 | **Periodisering av försäkring och hyra.** Ska helårspremien (SYNT-U-2025-005) och hyran för Q2 som betalas i mars (SYNT-U-2025-021) fördelas över tiden de gäller, eller kostnadsföras direkt? Finns en beloppsgräns där det inte behövs? (Ö-T9, Ö-T20) |
| D11 | **Moms på hyran** med frivillig skattskyldighet: vad krävs av hyresavin för avdrag (Ö-T8)? |
| D12 | **Restaurangkvitto och representation:** hur stor del av kostnaden och momsen får dras av, vilket underlag krävs (till exempel vilka som deltog och syftet), och hur bokförs ett köp av privat karaktär (som fordran på ägaren eller på annat sätt, K7)? |
| D13 | **Bankavgifter:** har de moms, och räcker bankraden som underlag tills specifikationen finns (Ö11)? |
| D14 | **Datum på verifikationen:** fakturadatum, kvittodatum, transaktionsdag eller bankens bokföringsdag, för varje flöde |
| D15 | **Vad en verifikation måste innehålla** enligt bokföringslagen, och om Veras förslag plus underlaget och bankraden räcker, när den importeras som SIE-fil till kundens program |
| D16 | **Kreditnotor** (Ö8, Ö-T21): hur bokförs de och kopplas till originalfakturan? Formatet för dem bestämmer Hugo, bokföringen kräver en expert |

### Hugo kan bestämma själv

De här är produkt- och riskval, inte skatteregler. Hugo bestämmer, och svaren skrivs i SPEC eller i
konfigurationen.

| # | Fråga | Förslag |
|---|---|---|
| D17 | Filformaten i avsnitt 1–3: nycklarnas namn, regel-id, förslagens id | Som i exemplen |
| D18 | Beloppsgränserna för nivå A och B (`a_hogst_ore`, `b_hogst_ore`), och hur många godkända gånger en regel behöver innan den kan ge A | Lågt i början (SPEC 5), till exempel 20 000 kr, 40 000 kr och 3 gånger |
| D19 | Värdena för K9 (`minst_historik`, procentgränserna) | 3, 300 %, 33 % |
| D20 | Att en ny motpart alltid blir ett ärende, att en regel bara kan skärpa företagets gränser, och att bankrader utan underlag aldrig blir nivå A | Ja på alla tre |
| D21 | Om listan över stängda dagar ska finnas för K8:s varningssignal, och var den ligger | I regelboken, nyckeln `oppettider` |

**Hugos beslut 2026-10-26:**

- **D17:** filformaten och nyckelnamnen i exemplen gäller.
- **D18:** A-gräns 20 000 kr, B-gräns 40 000 kr, 3 godkännanden innan nivå A.
- **D19:** K9 med värdena 3 / 300 % / 33 %.
- **D20:** ny motpart är alltid ett ärende; en regel kan bara skärpa företagets gränser; bankrader utan underlag
  blir aldrig nivå A.
- **D21:** lista över stängda dagar för K8 ligger i regelboken under nyckeln `oppettider`.

**Hugos beslut 2026-10-26, efter uppgift 2:**

1. **Ägare och närstående (K7).** Regelboken får en ny, valfri nyckel `agare_och_narstaende`: en lista med
   motparter. En regel som gäller en motpart i listan måste ha nivå D, annars stoppas hela filen. Saknas
   nyckeln är listan tom. Dubbletter, tomma värden och dolda tecken i listan stoppar filen. Motparterna
   jämförs efter samma normalisering som i K4 och i resten av regelboken (avsnitt 1), så `AGARE-1` och
   `agare-1` är samma motpart. Uppslaget `ar_agare_eller_narstaende` säger om en motpart är ägare eller
   närstående, så att nivåsteget (uppgift 6) kan använda det. Byggt som ett tillägg till uppgift 2.
2. **Öppettider.** `oppettider` har `stangda_veckodagar` och `stangda_datum`. Datumen är hela datum
   (ÅÅÅÅ-MM-DD). Det finns ingen återkommande dag utan år, så en helgdag skrivs in för varje år.
3. **Testbutikens regelbok.** De två tilläggen till exemplet i avsnitt 1 är godkända: `oppettider` och
   gränsen 25000 öre i `R-BANK-AVGIFT`. Dessutom har den `agare_och_narstaende` med det syntetiska värdet
   `AGARE-1` ur exemplen ovan.

**Hugos beslut 2026-10-26, efter uppgift 3:** tre kontroller i ursprungskontrollen (avsnitt 3), utöver
punkt 1–5 där, är godkända:

1. **Bankkontot.** En rad på bankkontot (rollen `bank` i kontoplanen) får bara ha bankrader som ursprung,
   räknade med `lika` eller `summa`, och ska stå på rätt sida: pengar in i debet, pengar ut i kredit.
2. **Utgående moms.** En rad på ett konto för utgående moms ska ha momsen med kontots egen sats som
   ursprung.
3. **Negativa poster i kassan.** En negativ post i en Z-rapport (till exempel en retur) stoppar förslaget.
   Regeln i avsnitt 3 att ett negativt värde räknas som positivt gäller bara bankrader. Hur returer ska
   bokföras är inte bestämt (Ö-T22).

**Hugos beslut 2026-10-26, efter granskning 7 (M1 och M2):** "Ja, M1 och M2 ska rättas innan uppgift 4.
Börja i en ny session med en täckningskontroll och separata regler för ingående och utgående moms."
Byggt i ursprungskontrollen (avsnitt 3, punkt 5 och 7):

1. **Täckningen** (punkt 7): varje del av en källa används 0 eller 1 gång per sida, räknat med tecken,
   och ett underlag används helt eller inte alls på varje sida. Den exakta regeln formulerades i
   uppgiften och är bekräftad av Hugo 2026-10-26, med de fem besluten i GRANSKNING.md ("Åtgärder efter
   granskning 7").
2. **Ingående och utgående moms** (punkt 5): kontot för ingående moms tar bara moms ur underlag, och
   kontona för utgående moms bara moms ur Z-rapporter. Sidan prövas inte förrän kreditnotorna är bestämda
   (D16).

**På Hugos uppdrag 2026-10-26, efter granskning 7 (M5–M8 och M10–M12):** rättat enligt uppdraget och
granskningens förslag (avsnitt 1, 2 och 3, och GRANSKNING.md, tabellen "Rättelserna"). Fyra val gjordes i
uppgiften och bör bekräftas av Hugo:

1. Regelbokens namn (motpart, kassaregister, ägare och närstående) får bara ha latinska bokstäver och
   siffrorna 0–9. Det är strängare än underlagen. En leverantör med ett namn i till exempel grekisk skrift
   behöver en latinsk stavning i regelboken, och ett underlag med det grekiska namnet blir då en ny motpart
   (ett ärende), vilket är den säkra riktningen.
2. Ett regel-id får bara ha a–z, siffror och bindestreck, alltså inte understreck eller punkt.
3. Ett konto får bara ha en roll, utom utgående moms med flera satser på samma konto.
4. Ägarens bankrader pekas ut när namnet står som hela ord (som när matchningen letar efter en motpart),
   inte när det står inuti ett längre ord (SPEC Ö13).

**På Hugos uppdrag 2026-10-27, efter granskning 8 (N1–N7 och M11):** rättat enligt uppdraget (GRANSKNING.md,
tabellen "Rättelserna efter granskning 8"). Val 1 och 4 ovan är ändrade av N2 och N3:

1. **Dolda tecken (N1).** Alla tecken på Unicodes lista över tecken som inte ska synas räknas som dolda i
   regelboken, kontoplanen och momsfilen, och de som inte används i vanlig text stoppar också ett underlag.
   Listan står uttryckligen i koden.
2. **Tecknen i ett namn (N2).** Ett namn i regelboken får ha a–z med eller utan accent, 0–9, mellanslag,
   bindestreck (alla sorter), understreck och punkt. SPEC sa inte vilka skiljetecken som godtas, så
   uppdragets regel gäller: bara bindestreck, understreck och punkt. **Öppen fråga till Hugo:** ska fler
   tecken få finnas, till exempel `&` (som i "Café Ölund & Söner AB"), `/`, `,`, `'` och parenteser, och
   latinska bokstäver som inte är a–z med accent, till exempel `Ø`, `Æ` och `ß`? I dag stoppas de.
3. **Ägarens bankrader (N3).** Orden delas vid skiljetecken. En regel i `matchning.json` undantar aldrig en
   rad mot en ägare eller närstående i regelboken och i konteringsförslaget, och en regel vars text nämner
   en ägare stoppar regelboken. Frågan om matchningen är **besvarad i chatten 2026-10-27**: "matcha_period
   ska få regelbokens ägarlista så att ägarens bankrad kräver underlag". Det är gjort: `matcha_period` tar
   emot regelboken (ett obligatoriskt argument) i stället för matchningsformatet, tar formatet från
   regelboken och använder regelbokens uppslag. Ägarens rad kräver underlag som andra rader (K3) och blir
   aldrig "över gräns". Formatet skickas inte längre in för sig, så att matchningen aldrig kan använda ett
   annat format än regelboken kontrollerades mot. Nivån D sätts fortfarande i uppgift 6.
4. **Fristående accenttecken (N4).** "A¨" jämförs som "Ä", som granskningen rekommenderade (den säkra
   riktningen). Valet står i `normalisering.py` och är låst med ett test.
5. **Nyckelnamnen för bankrader (M11).** Exemplet i avsnitt 3 visar kodens nyckelnamn (`id`). Namnen i
   koden är inte ändrade. Hugo har godkänt avvikelsen från exemplet som D17 godkände.

Det som Hugo bestämmer gäller bara testföretaget och produktens beteende. För en riktig kund ska varje
konto, sats och metod komma från kunden och dess redovisningskonsult, och stå som källa i konfigurationen.
