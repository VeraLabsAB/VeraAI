# Fiktivt testföretag: Syntet Testbutik AB

Allt i den här filen är påhittat. Företaget, personerna, motparterna, numren och kontona finns inte.
Filen beskriver företaget som ska användas för att bygga och testa hela systemet. Den innehåller
ingen testdata. Testdata genereras i senare sessioner, ett kvartal i taget, utifrån den här beskrivningen.

Mappen `testforetag/` är skrivskyddad för agenten (förberedande och bokförande körning). Ändringar görs
av en människa.

Skrivsätt:

- **SYNTETISK** betyder att värdet är påhittat och aldrig får användas mot en riktig myndighet,
  bank eller motpart.
- Där en bokföringsfråga inte är avgjord står det "se Ö-T" och numret på frågan i avsnitt 9. Ingen
  sådan fråga är besvarad i den här filen.

---

## 1. Grunduppgifter

| Uppgift | Värde |
|---|---|
| Namn | Syntet Testbutik AB |
| Bolagsform | Aktiebolag |
| Organisationsnummer | 559900-0001 **SYNTETISK** (kontrollsiffran är avsiktligt fel, så numret kan inte tillhöra ett riktigt bolag) |
| Verksamhetsform | En fysisk butik och en webbshop |
| Räkenskapsår | 2025-01-01 – 2025-12-31 (kalenderår, första och enda teståret) |
| Momsredovisning | Per kvartal |
| Bokföringsprogram | Fortnox |
| Företagskonto (bank) | Clearing 9999, konto 000 000 001-0 **SYNTETISK**, bokförs på 1940 |
| Lånekonto (från Q3) | Clearing 9999, konto 000 000 002-0 **SYNTETISK** |
| Bankgiro | 000-0001 **SYNTETISK** |
| Swish-nummer för butiken | 000 000 00 01 **SYNTETISK** (ogiltigt, riktiga Swish-nummer för företag börjar på 123) |
| Momsregistreringsnummer | SE559900000101 **SYNTETISK** |
| Säte | En påhittad svensk ort. Ingen adress anges |

Kontoplanen antas vara BAS. Vilka konton som ska användas för varje händelse bestäms i testföretagets
egen regelbok, som inte finns än (se Ö-T1).

---

## 2. Verksamhet

**Vad företaget säljer**

- Te och kaffe i lösvikt och förpackat (livsmedel).
- Tillbehör: koppar, kannor, filter, teslevar och presentförpackningar (inte livsmedel).
- Presentkort, som säljs både i butiken och i webbshopen (se Ö-T14).

Försäljningen sker alltså med minst två momssatser. Vilken sats som gäller för varje varugrupp under
2025 ska bestämmas i testföretagets momssatser och verifieras av människa (se Ö-T2).

**Kunder**: i butiken nästan bara privatpersoner. I webbshopen privatpersoner i Sverige. Ett fåtal
företagskunder köper på faktura (presentförpackningar till personal).

**Ägare**: en fysisk person, här kallad **Ägare 1** (påhittad). Äger 100 % av aktierna, är VD och
ensam styrelseledamot. Ägare 1 arbetar i butiken men tar ingen lön under 2025 (se Ö-T15).

**Anställda under året**

| Period | Antal anställda | Kommentar |
|---|---|---|
| 2025-01-01 – 2025-07-31 | 0 | Ägare 1 sköter allt |
| 2025-08-01 – 2025-12-31 | 1 | **Anställd 1** (påhittad), deltid i butiken, månadslön |

Antal anställda som någon gång varit anställda under året: 1. Medelantalet anställda för
årsredovisningen räknas inte här (se Ö-T16).

---

## 3. System

Bara format som kärnan redan stödjer används. Där kärnan inte stödjer underlaget står det uttryckligen,
och underlaget kommer in som JSON enligt kärnans schema eller inte alls.

| Underlag | Format | Kärnans stöd i dag |
|---|---|---|
| Bank (1940 och lånekontot) | Swedbank-CSV med kolumnerna Radnummer, Bokföringsdag, Transaktionsdag, Referens, Beskrivning, Belopp, Bokfört saldo, och saldo på varje rad | `scripts/las_bank.py`. Kolumnlayouten är antagen och inte verifierad mot en riktig fil |
| Kassasystem (Z-rapporter) | Kärnans generiska CSV, en fil per dag, kolumnerna `datum,z_nummer,kassaregister_id,post,momssats,belopp` | Adaptern `scripts/kassa_adaptrar/generisk_csv.py` (platshållaren). Ett kassaregister, id `TB-KASSA-1` **SYNTETISK** |
| Kvitton och leverantörsfakturor | JSON i standardformatet för kvitton och leverantörsfakturor (SPEC 4.4), ett dokument per underlag | `scripts/las_underlag.py`. Kvittobilder tolkas inte än, så underlagen skapas direkt som JSON. Schemat i `scripts/schemas/` finns inte än |
| Webbshopens utbetalningsrapport | Ingen parser finns | **Stöds inte.** Se Ö-T6 |
| Kortinlösarens avräkning | Ingen parser finns. Matchning sker mot summerade Z-rapporter minus avgifter | Delvis (matchningen i `matcha.py`) |
| Skattekontoutdrag | Ingen parser finns (`las_skattekonto.py` är ett skal) | **Stöds inte.** Se Ö-T12 |
| Lönebesked och lönespecifikation | Lönen hanteras av en påhittad lönebyrå. Agenten skapar aldrig löneverifikationer | Bara avstämning mot bank, och den är inte byggd för testföretaget |

Kassasystemet är ett påhittat certifierat kassaregister. Bankformatet är Swedbank-CSV eftersom det är
det enda bankformat kärnan läser.

---

## 4. Motparter

Alla motparter är påhittade. Här står bara vilken typ av motpart det är och ett internt kortnamn som
testdatan använder. Inget kortnamn får vara ett riktigt företagsnamn.

| Kortnamn | Typ av motpart | Land | Från |
|---|---|---|---|
| KUND-PRIVAT | Privatpersoner i butiken (anonyma, syns bara i Z-rapporten) | Sverige | Q1 |
| KUND-WEBB | Privatpersoner som handlar i webbshopen | Sverige | Q2 |
| KUND-FTG-1 | Företagskund som köper presentförpackningar på faktura | Sverige | Q2 |
| LEV-TE | Grossist för te i lösvikt | Sverige | Q1 |
| LEV-KAFFE | Kafferosteri | Sverige | Q1 |
| LEV-TILLBEHOR | Grossist för porslin och tillbehör | Sverige | Q1 |
| LEV-EU-VAROR | Leverantör av tekannor och koppar | Ett annat EU-land | Q2 |
| LEV-FRAKT | Fraktbolag för webbshopens paket | Sverige | Q2 |
| LEV-EL | Elleverantör | Sverige | Q1 |
| LEV-TELE | Telefoni och bredband | Sverige | Q1 |
| LEV-FORSAKRING | Försäkringsbolag | Sverige | Q1 |
| HYRESVARD | Fastighetsbolag som hyr ut butikslokalen | Sverige | Q1 |
| BANK | Företagets bank (konto, avgifter, lån) | Sverige | Q1 |
| BET-KORT | Kortinlösare för butikens kortterminal | Sverige | Q1 |
| BET-SWISH | Swish via banken | Sverige | Q1 |
| BET-WEBB | Betaltjänst för webbshopen som betalar ut netto efter avgifter och returer | Ett annat EU-land | Q2 |
| PLATTFORM-WEBB | Plattform som webbshopen körs på (månadsabonnemang) | Ett annat EU-land | Q2 |
| ANNONS-EU | Annonsplattform som säljer annonser i sociala medier | Ett annat EU-land | Q2 |
| LONEBYRA | Byrå som räknar och bokför lönen | Sverige | Q3 |
| INVENTARIE-LEV | Leverantör av butiksinredning (en kyl- och visningsdisk) | Sverige | Q3 |
| SKATTEVERKET | Skattekontot | Sverige | Q4 som underlag, se Ö-T12 |
| AGARE-1 | Ägare 1 (påhittad person), för utlägg och eventuella mellanhavanden | Sverige | Q2 |

---

## 5. Avtal

| Avtal | Motpart | Villkor (påhittade) | Första händelse |
|---|---|---|---|
| Hyra av butikslokal | HYRESVARD | Hyra per kvartal i förskott, förfaller sista vardagen före kvartalets början. Lokalen hyrs med frivillig skattskyldighet för moms enligt avtalet (se Ö-T8). Indexuppräkning vid årsskiftet | Hyran för Q1 2025 betalas i slutet av december 2024 (före räkenskapsåret, se Ö-T9). Första hyresbetalningen i testdatan: hyran för Q2, i mars 2025 |
| Försäkring | LEV-FORSAKRING | Företagsförsäkring (egendom och ansvar), helårspremie för 2025, faktureras i januari som leverantörsfaktura | Januari 2025 |
| Banklån | BANK | Lån för inventarieköpet, utbetalas i juli 2025. Rak amortering varje månad och rörlig ränta, båda dras från företagskontot. Löptid och ränta sätts när testdatan genereras och står i underlaget (lånebeskedet) | Juli 2025 (Q3) |
| Kortinlösen | BET-KORT | Avgift per transaktion, avräkning dagligen netto efter avgift (se Ö-T5) | Januari 2025 |
| Webbshopens betaltjänst | BET-WEBB | Utbetalning varje vecka, netto efter avgifter, returer och eventuella återbetalningar | April 2025 (Q2) |
| Webbshopsplattform | PLATTFORM-WEBB | Månadsabonnemang, faktureras från annat EU-land utan svensk moms | April 2025 (Q2) |
| Lönebyrå | LONEBYRA | Fast avgift per månad och lönespecifikation per lönekörning | Augusti 2025 (Q3) |

---

## 6. Underlagstyper

Alla underlagstyper företaget får under året, med det kvartal de dyker upp första gången.

| Underlagstyp | Format i testdatan | Första kvartal |
|---|---|---|
| Kontoutdrag för företagskontot | Swedbank-CSV | Q1 |
| Z-rapport per dag | Generisk kassa-CSV | Q1 |
| Kortinlösarens avräkning (insättning netto efter avgift) | Bankrad. Avgiften framgår av underlag i JSON (se Ö-T5) | Q1 |
| Swish-insättningar | Bankrad | Q1 |
| Leverantörsfaktura, svensk med moms | JSON (underlag) | Q1 |
| Kvitto, inköp i butik med kort eller kontant | JSON (underlag) | Q1 |
| Hyresavi | JSON (underlag) | Q1 |
| Försäkringsfaktura | JSON (underlag) | Q1 |
| Bankavgift | Bankrad. Specifikation från banken i JSON | Q1 |
| Utbetalningsrapport från webbshopens betaltjänst | Saknar format (se Ö-T6) | Q2 |
| Faktura från EU-leverantör av varor (omvänd moms) | JSON (underlag) | Q2 |
| Faktura från annonsplattform i annat EU-land (tjänst, omvänd moms) | JSON (underlag) | Q2 |
| Faktura från webbshopsplattform i annat EU-land (tjänst) | JSON (underlag) | Q2 |
| Fraktfaktura | JSON (underlag) | Q2 |
| Utlägg: kvitto som Ägare 1 betalat privat, med utläggsredovisning | JSON (underlag) | Q2 |
| Kundfaktura till företagskund | JSON (underlag) | Q2 |
| Kreditfaktura från leverantör | JSON (underlag) | Q2 |
| Återbetalning till kund (retur i butik och i webbshop) | Z-rapportens returer, bankrad och returkvitto i JSON | Q2 |
| Momsdeklaration (kvittens eller kopia) | Saknar format (se Ö-T11) | Q2 (för Q1) |
| Lönespecifikation och lönesammanställning från lönebyrån | JSON (underlag), bara för avstämning | Q3 |
| Faktura från lönebyrån | JSON (underlag) | Q3 |
| Faktura för inventarie | JSON (underlag) | Q3 |
| Lånebesked och lånekontoutdrag | Lånebesked i JSON. Lånekontot i Swedbank-CSV | Q3 |
| Räntebesked (ränta och amortering) | JSON (underlag) | Q3 |
| Hyresavi för förskottsbetald hyra över årsskiftet | JSON (underlag) | Q4 |
| Inventeringslista per 2025-12-31 | Saknar format (se Ö-T19) | Q4 |
| Skattekontoutdrag | Saknar parser (se Ö-T12) | Q4 |
| Underlag för bokslutsposter (avskrivningsplan, periodiseringar, skatteberäkning) | Tas fram av människa (se Ö-T20) | Q4 |

---

## 7. Händelsekalender per kvartal

Varje kvartal innehåller allt från kvartalen före och lägger till nya händelser.

### Q1 (januari–mars)

- **Kassa**: en Z-rapport per öppen dag, ett kassaregister, löpande Z-nummer. Försäljning med två
  momssatser. Betalsätt kontant, kort och Swish.
- **Kortinlösen**: insättning från BET-KORT dagen efter, netto efter avgift.
- **Swish**: insättningar från BET-SWISH.
- **Leverantörsfakturor**: LEV-TE, LEV-KAFFE, LEV-TILLBEHOR, LEV-EL, LEV-TELE och LEV-FORSAKRING
  (helårspremie i januari). Betalas från företagskontot.
- **Kvitton**: mindre inköp i butik (förbrukningsmaterial, städartiklar).
- **Hyra**: hyran för Q2 betalas i mars (förskott enligt avtalet).
- **Bankavgifter**: månadsavgift för konto och kortinlösen.
- **Kontantinsättning**: kassan töms och sätts in på banken (se Ö-T4).

### Q2 (april–juni)

Allt från Q1, och dessutom:

- **Webbshop med nettoutbetalningar**: webbshopen öppnar i april. BET-WEBB betalar ut varje vecka netto
  efter avgifter och returer. PLATTFORM-WEBB fakturerar månadsabonnemanget. LEV-FRAKT fakturerar frakt.
- **EU-inköp med omvänd moms**: varuinköp från LEV-EU-VAROR och annonser från ANNONS-EU.
- **Utlägg**: Ägare 1 betalar ett inköp privat och får tillbaka pengarna från företagskontot.
- **Kreditfaktura**: en leverantör krediterar en tidigare faktura (felleverans).
- **Återbetalning till kund**: en retur i butiken (via kassan) och en retur i webbshopen (dras från
  BET-WEBBs utbetalning).
- **Kundfaktura**: första fakturan till KUND-FTG-1, betalas in på bankgirot.
- **Momsdeklaration för Q1** lämnas och betalas (se Ö-T10, Ö-T11).

### Q3 (juli–september)

Allt från Q2, och dessutom:

- **Banklån**: lånet betalas ut i juli. Från augusti dras amortering och ränta varje månad.
- **Köp av inventarie**: en kyl- och visningsdisk från INVENTARIE-LEV i juli, betald med lånet.
- **Första anställd och lön**: Anställd 1 börjar 2025-08-01. Första lönen betalas ut i slutet av augusti.
  LONEBYRA skickar lönespecifikation och faktura. Personalskatt och arbetsgivaravgifter betalas till
  skattekontot månaden efter.

### Q4 (oktober–december)

Allt från Q3, och dessutom:

- **Förskottsbetald hyra**: hyran för Q1 2026 betalas i december 2025.
- **Skattekonto**: skattekontoutdraget kommer som underlag från oktober (se Ö-T12).
- **Inventering**: varulagret inventeras per 2025-12-31 av Ägare 1 och Anställd 1.
- **Bokslutsposter**: avskrivning av inventarien, periodisering av förskottsbetald hyra och upplupna
  kostnader, lagerförändring, upplupen ränta, semesterlöneskuld och skatt på årets resultat. Alla är
  nivå D och bedöms av människa.

---

## 8. Planterade fel

För varje månad står vilka typer av fel som ska planteras när testdatan genereras. Bara typ och månad
står här. Själva datan tas fram senare. Inom parentes står den kontroll som förväntas fånga felet, där
det finns en. "Ingen kontroll" betyder att kärnan i dag inte fångar felet. Det är i sig ett fynd.

| Månad | Planterade feltyper |
|---|---|
| Januari | Leverantörsfaktura importerad två gånger (K4). Lucka i Z-serien, en Z-rapport saknas (inläsningskontroll) |
| Februari | Kvitto med fel momssats för varugruppen (K5). Bankrad utan underlag, ett kortköp utan kvitto (K3, "Saknat underlag" efter 7 dagar) |
| Mars | Brott i saldokedjan i bankfilen, en rad med fel saldo (K1). Kvitto från restaurang med privat karaktär (K8) |
| April | Nettoutbetalning från webbshopens betaltjänst där avgifterna inte går att stämma av mot specifikationen (ingen kontroll, se Ö-T6). Z-rapport där summan av betalsätten inte är lika med bruttot (inläsningskontroll) |
| Maj | Faktura från EU-leverantör där omvänd moms saknas eller är svensk moms (K5). Kvitto med instruktionsliknande text riktad till agenten (K17) |
| Juni | Kreditfaktura som ser ut som en ny debetfaktura, belopp med fel tecken (K4 eller ingen kontroll). Utlägg utan kvitto (K3) och utlägg betalt till Ägare 1 två gånger (K7, K4) |
| Juli | Inventarie som ser ut att vara en förbrukningskostnad (ingen kontroll, nivå D enligt regelbok). Belopp långt över snittet för en känd motpart (K9) |
| Augusti | Löneutbetalning utan löneverifikation efter 7 dagar (lönekontrollen i SPEC 4.6). Amortering och ränta i en och samma bankrad utan uppdelning (ingen kontroll, nivå D) |
| September | Samma bankfil inläst två gånger med nytt filnamn (dubblettimport). Bankrad som matchar två motparter i regelboken (ärende vid flera träffar) |
| Oktober | Underlag daterat i en månad som redan är stängd (K6). Beräkningsfel i kvittot, underlag plus moms är inte lika med totalen (beräkningskontrollen i SPEC 4.4) |
| November | Insättning från Ägare 1 utan förklaring (K7). Moms som är mer än 20 % av bruttot (K5) |
| December | Förskottsbetald hyra bokförd som kostnad i december utan periodisering (ingen kontroll, bokslut nivå D). Dag utan Z-rapport två dagar i rad (Z-kontrollen, hög prioritet) |

---

## 9. Öppna frågor

Bokföringsfrågor som inte är besvarade. Ska granskas av en redovisningskonsult. Inga svar är påhittade
här, och testdatan för en händelse ska inte genereras med en gissad bokföring innan frågan är avgjord.
Där det står ett belopp, en tidsgräns eller en regel i frågan är det något som ska **verifieras**, inte ett svar.

| # | Fråga |
|---|---|
| Ö-T1 | Ska testföretaget ha en egen regelbok (motparter, momssatser, gränser) i en egen mapp, och vem godkänner den? Kärnan läser i dag bara `regelbok/` |
| Ö-T2 | Vilka momssatser gäller 2025 för te och kaffe, för tillbehör och för presentförpackningar som blandar livsmedel och andra varor? |
| Ö-T3 | Kärnan och K14 är byggda för helårsmoms. Hur ska kvartalsmoms hanteras: perioder, avstämning per kvartal, och när `/arsmoms` ska ersättas av en kvartalsrapport? |
| Ö-T4 | Hur bokförs kontantinsättning från kassan till banken, och hur hanteras skillnad mellan räknad kassa och Z-rapportens kontantbelopp? |
| Ö-T5 | Kortinlösen betalas ut netto efter avgift. Ska avgiften bokföras brutto (försäljning och avgift var för sig) och vilket underlag krävs för avgiften? Är avgiften momsfri? |
| Ö-T6 | Webbshopens nettoutbetalningar: hur bokförs försäljning, avgifter, returer och återbetalningar när betaltjänsten finns i ett annat EU-land? Vilket underlag behövs, och ska kärnan få en parser för utbetalningsrapporten? |
| Ö-T7 | Hur redovisas omvänd moms på varuinköp från ett annat EU-land respektive på tjänster (annonser, webbshopsplattform) från ett annat EU-land? Vilka rutor i momsdeklarationen påverkas? |
| Ö-T8 | Om hyresvärden tar ut moms på hyran: vad krävs av underlaget för att avdrag ska få göras? |
| Ö-T9 | Hyran för Q1 2025 betalades i december 2024, före första räkenskapsåret i testet. Hur ska ingående balans för förutbetald hyra se ut? Behövs en ingående balansräkning för testföretaget? |
| Ö-T10 | När ska momsdeklarationen för varje kvartal lämnas och betalas 2025 (datum ska verifieras), och hur bokförs betalningen via skattekontot? |
| Ö-T11 | Vilket underlag för momsdeklarationen ska finnas i testdatan, och i vilket format? |
| Ö-T12 | Skattekontot syns som underlag först i Q4 enligt kalendern, men F-skatt och moms betalas till skattekontot redan från Q1. Ska testdatan ha skattekontohändelser från Q1, och i så fall i vilket format när kärnan inte kan läsa utdraget? |
| Ö-T13 | Hur bokförs ränta och amortering på banklånet, och hur ska upplupen ränta vid årsskiftet räknas? |
| Ö-T14 | Hur bokförs sålda presentkort (inlösta och ej inlösta), och vilken moms gäller när presentkortet säljs respektive löses in? |
| Ö-T15 | Ägare 1 tar ingen lön 2025. Finns det skattemässiga eller bokföringsmässiga konsekvenser som testet bör täcka (till exempel utlägg, eget uttag, aktieägartillskott)? |
| Ö-T16 | Hur räknas medelantalet anställda i årsredovisningen när en person är anställd på deltid från augusti? |
| Ö-T17 | Utlägg: vilket underlag krävs (kvitto plus utläggsredovisning), och hur hanteras utlägg med moms som ägaren betalat privat? |
| Ö-T18 | Kyl- och visningsdisken: är den inventarie eller förbrukning, ska den skrivas av enligt plan eller direktavdras, och vilken avskrivningstid gäller? Beloppsgränsen för direktavdrag ska verifieras för 2025 |
| Ö-T19 | Inventering: vilken värderingsprincip gäller för lagret (lägsta värdets princip, inkuransavdrag), och i vilket format ska inventeringslistan finnas? |
| Ö-T20 | Vilka bokslutsposter ska testas enligt K2 (BFNAR 2016:10), och vem tar fram underlagen för dem: periodiseringar, avskrivning, semesterlöneskuld, skatt? |
| Ö-T21 | Kreditfaktura från leverantör: ska den kvittas mot nästa betalning eller återbetalas, och hur ska den kopplas till originalfakturan i testdatan? |
| Ö-T22 | Återbetalning till kund i butiken: räcker Z-rapportens returer som underlag, eller krävs ett returkvitto per återbetalning? |
| Ö-T23 | Kundfaktura till företagskund: kundreskontra ligger utanför version 1 (inbetalningar som inte är kassa, kort eller Swish blir ärenden). Ska testföretaget ha kundfakturor alls? |
| Ö-T24 | Får dagskassan bokföras samlat per vecka (senareläggning enligt BFNAR 2013:2 med certifierat kassaregister) även för testföretaget? |
| Ö-T25 | Lön: agenten stämmer bara av. Vilka löneverifikationer ska lönebyrån "ha bokfört" i testets Fortnox, och hur ska de se ut för att avstämningen ska kunna testas? |
