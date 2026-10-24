# testdata/

**Allt här är SYNTETISKT.** Företaget, motparterna, numren och beloppen är påhittade och får aldrig
användas mot en riktig myndighet, bank eller motpart. Testföretaget beskrivs i
`testforetag/FIKTIVT_FORETAG.md`.

## Vad som finns

```
testdata/
  generator/generera_syntet_testbutik_q1.py   generatorn
  syntet-testbutik/2025-Q1/                   genererade filer för januari–mars 2025
    bank_2025-01.csv, bank_2025-02.csv, bank_2025-03.csv
    kassa/kassa_ÅÅÅÅ-MM-DD.csv                en Z-rapport per öppen dag
    underlag/SYNT-U-2025-NNN.json             ett dokument per leverantörsfaktura och kvitto
    facit.json                                rätt svar och listan över planterade fel
```

Filerna i `syntet-testbutik/` ska inte ändras för hand. Ändra generatorn och kör om den.

## Så kör man generatorn

Från mappen `agent/`:

```bash
.venv/bin/python testdata/generator/generera_syntet_testbutik_q1.py
```

Generatorn använder ett fast slumpfrö, så samma körning ger exakt samma filer varje gång. Den tar
först bort filer som den själv har skrivit tidigare i målmappen och skriver sedan allt på nytt.
Med `--ut <mapp>` skrivs filerna någon annanstans.

Testerna i `scripts/tests/test_testdata_q1.py` kontrollerar att de incheckade filerna är exakt
generatorns utdata.

## SYNTETISKA antaganden (inte verifierade)

Det här är antaganden för att kunna generera data. De är **inte** kontrollerade mot Skatteverket
eller en redovisningskonsult och får inte läggas i någon regelbok som de är (se Ö3 i SPEC.md och
Ö-T2 i FIKTIVT_FORETAG.md).

| Antagande | Värde |
|---|---|
| Moms på livsmedel (te, kaffe, restaurangkvittot) | 12 % **SYNTETISK, inte verifierad** |
| Moms på övrigt (tillbehör, el, tele, hyra, förbrukning, städ) | 25 % **SYNTETISK, inte verifierad** |
| Hyran | 25 % moms, eftersom avtalet anger frivillig skattskyldighet (Ö-T8) |
| Försäkringens helårspremie | Fakturan har ingen moms. **Öppen fråga**: hur försäkringspremien ska behandlas momsmässigt ska verifieras med Skatteverket eller en redovisningskonsult |
| Kortinlösarens avgift | 1,2 % av dagens kortförsäljning, dras vid avräkningen (Ö-T5) |
| Bankens månadsavgifter | 125,00 kr för kontot och 199,00 kr för kortinlösen, sista bankdagen i månaden |
| Öppettider | Måndag–lördag. Stängt söndagar, 1 januari och 6 januari |
| Bankdagar | Måndag–fredag utom 1 januari och 6 januari |
| Ingående saldo 1 januari 2025 | 85 000,00 kr |
| Första Z-numret 2025 | 1001 |

Kvittomotparterna `BUTIK-FORBRUKNING`, `BUTIK-STAD` och `RESTAURANG-1` finns inte i
FIKTIVT_FORETAG.md. De är påhittade kortnamn för mindre inköp i butik.

## Vad som händer under kvartalet

- **Kassa**: en Z-rapport per öppen dag med två momssatser och betalsätten kontant, kort och Swish.
  Försäljningen är i hela kronor.
- **Kortinlösen**: BET-KORT sätter in dagens kortförsäljning minus avgift nästa bankdag.
- **Swish**: varje Swish-betalning är en egen bankrad. Lördagens betalningar bokförs på måndagen.
- **Kontantinsättning**: första bankdagen varje vecka sätts kontanterna från dagarna före in på banken.
  Kontanterna från 31 mars ligger kvar i kassan.
- **Leverantörsfakturor**: LEV-TE och LEV-KAFFE två gånger i månaden, LEV-TILLBEHOR, LEV-EL och
  LEV-TELE en gång i månaden, LEV-FORSAKRING (helårspremie) i januari. Betalas 30 dagar efter
  fakturadatum, nästa bankdag om det är helg. Fakturor som förfaller efter 31 mars är obetalda.
  En faktura från LEV-KAFFE i februari har två momssatser.
- **Hyra**: hyresavin för andra kvartalet kommer 3 mars och betalas 31 mars.
- **Kvitton**: förbrukningsmaterial och städartiklar, betalda med företagets kort.
- **Bankavgifter**: två avgifter sista bankdagen varje månad.

## Format

Alla belopp är heltal i öre i JSON. I CSV-filerna skrivs de med punkt som decimaltecken och utan
tusentalsavgränsare, t.ex. `-1234.50`. Kärnans `tolka_belopp` läser det formatet. Filerna är UTF-8
med kommatecken som avgränsare.

### Bank (`bank_ÅÅÅÅ-MM.csv`)

Swedbank-CSV, kolumnlayouten är antagen och inte verifierad mot en riktig fil.

| Kolumn | Innehåll |
|---|---|
| Radnummer | Löpande från 1 i varje fil. Raden i filen är radnumret plus 1 (rubrikraden) |
| Bokföringsdag | Bankdagen då raden bokförs. Bestämmer vilken månadsfil raden hamnar i |
| Transaktionsdag | Dagen då köpet eller betalningen gjordes |
| Referens | `AVR-ÅÅÅÅMMDD` kortavräkning för försäljningsdagen, `SWISH-ÅÅÅÅMMDD-n`, `INS-ÅÅÅÅMMDD` kontantinsättning, fakturanumret vid leverantörsbetalning, `KORTKOP-ÅÅÅÅMMDD`, `AVG-ÅÅÅÅ-MM` bankavgift |
| Beskrivning | Motpartens kortnamn, t.ex. `LEV-TE`, `BET-KORT AVRAKNING 2025-01-02`, `KORTKOP BUTIK-STAD` |
| Belopp | Positivt in, negativt ut |
| Bokfört saldo | Föregående rads saldo plus radens belopp. Månadens ingående saldo är förra månadens utgående |

### Kassa (`kassa/kassa_ÅÅÅÅ-MM-DD.csv`)

Kärnans generiska CSV med kolumnerna `datum,z_nummer,kassaregister_id,post,momssats,belopp`.
Kassaregistret heter `TB-KASSA-1`. En fil innehåller en Z-rapport med de här posterna:

| post | momssats | belopp |
|---|---|---|
| `forsaljning` | 12 eller 25 | Försäljning inklusive moms för satsen |
| `moms` | 12 eller 25 | Momsen i försäljningen: brutto × sats / (100 + sats), avrundat till närmaste öre |
| `betalsatt_kontant`, `betalsatt_kort`, `betalsatt_swish` | tom | Betalt med respektive betalsätt |
| `summa_brutto` | tom | Hela dagens försäljning. Lika med summan av försäljningen och lika med summan av betalsätten |

### Underlag (`underlag/SYNT-U-2025-NNN.json`)

Ett JSON-dokument per leverantörsfaktura och kvitto. Filnamnet är dokumentets id.

```json
{
  "id": "SYNT-U-2025-003",
  "typ": "leverantorsfaktura",
  "datum": "2025-01-07",
  "motpart": "LEV-TE",
  "fakturanummer": "SYNT-TE-761",
  "belopp_ore": 1673056,
  "moms": [
    {"momssats": 12, "underlag_ore": 1493800, "moms_ore": 179256}
  ],
  "flaggor": []
}
```

| Fält | Innehåll |
|---|---|
| `id` | Unikt id för dokumentet |
| `typ` | `kvitto` eller `leverantorsfaktura` |
| `datum` | Fakturadatum eller kvittodatum, ÅÅÅÅ-MM-DD |
| `motpart` | Motpartens kortnamn |
| `fakturanummer` | Faktura- eller kvittonummer. Står som referens på bankraden när fakturan betalas |
| `belopp_ore` | Att betala, inklusive moms, heltal i öre |
| `moms` | En rad per momssats: sats i procent, belopp utan moms och moms, heltal i öre. Tom lista om dokumentet saknar moms |
| `flaggor` | Tom lista. Fylls av kärnan senare |

Hyresavin är lagd som `leverantorsfaktura`.

Det här finns **inte** som underlag i Q1: specifikation av kortinlösarens avgift och bankens
specifikation av avgifterna (FIKTIVT_FORETAG.md avsnitt 6 nämner dem i JSON, men uppgiften gällde
bara leverantörsfakturor och kvitton).

### Facit (`facit.json`)

| Nyckel | Innehåll |
|---|---|
| `bank` | Per månad: filnamn, antal rader, ingående och utgående saldo i öre |
| `forsaljning` | Per månad: antal Z-rapporter och, per momssats, brutto, moms och netto i öre. Räknat på de Z-filer som finns, alltså utan dagen med den saknade Z-rapporten |
| `planterade_fel` | Ett objekt per planterat fel: `typ`, `manad`, `kontroll` som förväntas fånga felet, `filnamn`, och `rad` (värdet i Radnummer) eller `id` eller `z_nummer`, plus en beskrivning |

## Planterade fel i Q1

Enligt FIKTIVT_FORETAG.md avsnitt 8. Exakt dessa och inga andra.

| Månad | Typ | Fil | Rad, id eller Z-nummer | Kontroll |
|---|---|---|---|---|
| Januari | Leverantörsfaktura inläst två gånger | `underlag/SYNT-U-2025-004.json` (kopia av `SYNT-U-2025-003`) | SYNT-U-2025-004 | K4 |
| Januari | Lucka i Z-serien | `kassa/kassa_2025-01-15.csv` saknas | Z 1011 | Inläsningskontroll |
| Februari | Kvitto med fel momssats (städartiklar med 12 %) | `underlag/SYNT-U-2025-019.json` | SYNT-U-2025-019 | K5 |
| Februari | Kortköp utan kvitto | `bank_2025-02.csv` | Radnummer 85 | K3 |
| Mars | Fel saldo på en rad (100,00 kr för högt) | `bank_2025-03.csv` | Radnummer 74 | K1 |
| Mars | Restaurangkvitto en söndag | `underlag/SYNT-U-2025-028.json` | SYNT-U-2025-028 | K8 |
