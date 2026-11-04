# Förslag: BYGGPLAN.md avstämd mot Kassio-specen

**Besluten är fattade 2026-11-04.** De står ordagrant i `GRANSKNING.md`, "Hugos beslut 2026-11-04 om planen (PLAN-KASSIO-FORSLAG.md)". Kravkällan är `KASSIO-KRAV.md`, och planen som gäller är `BYGGPLAN.md`. Den här filen är underlaget för besluten, kompletterad med kravlistan.

Skrivet 2026-11-04 i planeringssessionen (Hugos beslut 2026-11-04 om granskning 33, beslut 6). Kompletterat samma dag med `KASSIO-KRAV.md`: avsnitt B, storlekarna i C, och E. Datumen i D är inte ändrade.

## Läs det här först

1. **Kassio-specen i uppdraget var avklippt** mitt i en mening, efter "Kassasystem: direkt". Resten finns nu i `KASSIO-KRAV.md`, och B, C och E är kompletterade.
2. **Säkerhet: inget i förslaget lättar på regeln att inget bokförs utan godkännande.** Men två Kassio-krav krockar med de spärrar som precis har byggts: att kunden får ändra ett förslag mot en varning, och att ett saknat kvitto ändå ger ett förslag. De måste designas innan de byggs, så att de inte blir en väg runt godkännandet (fråga 4 och 5 i avsnitt F).
3. **Riktiga kunduppgifter är förbjudna i dag** (CLAUDE.md, "Aldrig"). En pilot med en riktig kund kräver ett uttryckligt beslut om var uppgifterna får ligga, och att juristfrågorna i steg 53 är besvarade. Det gäller alla tre alternativen i avsnitt D.
4. **Det viktigaste jag hittade:** koden har i dag ingen koppling till Fortnox, BankID eller en språkmodell. Den kan inte heller läsa ett riktigt kvitto, utan bara färdiga JSON-filer (en strukturerad textfil). BYGGPLAN.md har inget eget steg för att göra ett foto eller en PDF till sådan data, och ingen plats där kundens uppgifter ska ligga (SPEC Ö1).

**Min rekommendation:** alternativ C och sedan B i avsnitt D. Det ger riktig data i januari, utan att något skrivs i Fortnox. Det kräver Hugos beslut att ändra specen, som i dag kräver alla funktioner.

---

## A. Takten hittills

Alla siffror är räknade ur git och ur BYGGPLAN.md. Datumen i D bygger på dem, men också på bedömningar, som är märkta där.

**Kommandon:**

```
git log --since=2026-10-21 --date=short --format='%ad %h %s'
git log --since='2026-10-30 00:00:00' --until='2026-11-04 23:59:59' --date=short --format='%ad %h %s'
git show -s --date=short --format='%h %ad' d9a0ce3 3fd797e b36ba6c a2d1540 60fbaa3 c46142f 5e1af42 3368f9e 1c1bdc5 16000a8 567692b 7d8cae9 175db51 3bbcbe4 6aba32d 277ca90 c479915 7801a64 109fdcf 0708667 4b3f379 d8a5edc 95afce1 40b1ec1
git diff --shortstat 7d8cae9 33efbe4 -- scripts/tests
git diff --stat 7d8cae9 33efbe4 -- scripts/konteringsforslag.py scripts/konteringsfloden.py scripts/las_regelbok.py scripts/reserverade_namn.py
git diff --shortstat 7d8cae9 33efbe4 -- GRANSKNING.md PROGRESS.md BYGGPLAN.md SPEC.md CLAUDE.md
```

Antalen är räknade med ett litet Python-skript i den tillfälliga mappen. Det är inte en del av projektet.

### Klara steg per vecka

Första commiten är från 2026-10-24, så inget hände 21–23 oktober. Datumet är dagen då stegets sista byggcommit gjordes. Steg 22 räknas på dagen det förklarades klart (277ca90). Steg 10 räknas på 16000a8, min tolkning eftersom raden bara hänvisar till PROGRESS.md.

| Vecka | Datum | Klara steg | Vilka |
|---|---|---|---|
| 43 | 19–25 okt | 6 | 1–6 |
| 44 | 26 okt–1 nov | 13 | 7–13, 20, 21, 22, 91, 93, 94 |
| 45, hittills | 2–4 nov | 5 | 95, 97, 98, 99, 100 |
| **Summa** | 12 kalenderdagar | **24** | 2,0 per dag, eller 14 per vecka |

- Alla fem stegen i vecka 45 kom samma dag. Det kom inga commitar alls 1–3 november. **Takten styrs av när Hugo eller Casper kan arbeta och besluta, inte av hur fort koden skrivs.**
- 24 av 102 steg är klara, och 78 är kvar.
- **Planen växer fortare än den krymper.** Sedan 2026-10-30 har 9 steg blivit klara, men 12 nya har lagts till (91–102). Planen hade 90 steg när den skrevs (b91dd02).
- Att räkna steg säger lite om vad som återstår. Stegen hittills är små kontroller, medan de kvarvarande ofta är nya system.

### Commitarna sedan 2026-10-30

34 commitar, d5b2fba till 33efbe4. Dagens commit med besluten (01aa499) är inte med. Uppdelningen är min, gjord efter varje commits titel.

| Sort | Antal | Andel |
|---|---|---|
| Härdning i koden (fler stopp, inga nya funktioner) | 12 | 35,3 % |
| Oberoende granskningar | 11 | 32,4 % |
| Dokumentation och beslut om dem | 11 | 32,4 % |
| **Nya funktioner** | **0** | **0 %** |

- Fyra av de tolv härdningscommitarna hör till steg 22 och inte till steg 91–100 (d5b2fba, 13126d2, 35afa8b, bbb183a). Det ändrar inte slutsatsen.
- Senaste nya funktionen är uppgift 4, flöde a, b och e, byggd 2026-10-29. **En dags bygge följdes av 12 granskningar (22–33).** Det är det bästa mått vi har på vad en ny funktion kostar med dagens arbetssätt.
- Av de 11 granskningarna sedan 2026-10-30 blev 8 gula och 3 gröna (24, 25, 32).
- En **omgång** (bygge, dokumentation och oberoende granskning) går i dag snabbt: 11 omgångar på 6 kalenderdagar, ungefär 12,8 per vecka.
- Sedan 7d8cae9 har kärnkoden fått 1 055 nya rader och förlorat 136, testerna 3 897 nya och förlorat 55, och dokumenten 4 345 nya och förlorat 20.

**Att läsa det här rättvist:** härdningen var inte bortkastad. Den gjorde att ett förslag bara kan se ut som flödena bygger det, vilket är ett starkt skydd. Men nästan alla hålen krävde kod som går förbi flödena, och förslaget behöver fortfarande en människas godkännande. Det viktiga undantaget är Öppet 46, där flödena själva kan betala samma faktura två gånger över olika körningar, och det är därför steg 101 (registret) ska byggas. Frågan om hur långt det ska drivas före piloten är fråga 10 i avsnitt F.

---

## B. Kassio-specen mot BYGGPLAN.md

"Krockar" betyder att BYGGPLAN.md, SPEC.md eller DESIGN-regelbok.md säger något annat än specen. Tabellen visar läget i de filerna före besluten 2026-11-04, och rader som "krockar" kan alltså vara avgjorda av besluten. Raderna som förut hette "inte läst" är bedömda mot `KASSIO-KRAV.md`, och kraven efter klippet är tillagda sist. Steg från 103 och uppåt är de nya stegen i `BYGGPLAN.md`.

### Från specen till byggplanen

| Krav | Steg | Läge | Kommentar |
|---|---|---|---|
| Heter Kassio Finance, bolaget Kassio Labs AB, agenten har inget eget namn | – | krockar | SPEC, BYGGPLAN och CLAUDE.md säger Vera och Vera Labs. Ordet "Vera" står också på sex rader i de fyra kärnfiler jag sökte i. Repot heter också något annat |
| Ekonomikollega ovanpå kundens program, ersätter byrån | SPEC 2.1, målet i BYGGPLAN | täckt | |
| Bara Fortnox vid lansering | 55, 56, och 34 | krockar | SPEC 2.1 och steg 34 säger SIE-fil (ett filformat för import) i version 1. Bokio är steg 57 |
| Bara aktiebolag i version 1 | SPEC 1, steg 81 senare | täckt | |
| Målgrupp: nystartade små aktiebolag | 39, 40, 65 | krockar | SPEC 1 och 8 säger butik, krog och hantverkare. Steg 65 bygger regler ur förra årets bokföring, som ett nystartat bolag kanske inte har |
| Pris 999 kr/mån | – | saknas | Behövs inte före en gratis pilot |
| Pilotkundens ekonomiansvarige godkänner, en riktig kund | SPEC 3, 53, 68 | krockar | CLAUDE.md förbjuder riktiga kunders uppgifter, och SPEC 1.1 talar om en referensprodukt |
| Piloten startar med alla funktioner i en enkel webbapp | 68 | krockar | Appen ligger i fas G, efter fas F, "Före första kund". Fakturor och bokslut ligger också i fas G |
| Tre frågor som slår på funktioner | – | saknas | Steg 65 har en intervju, men inga funktioner att slå på och av |
| Organisationsnummer med uppslag | – | saknas | |
| Bokföringsmetod | 65 | delvis | Bara faktureringsmetoden finns. Kontantmetoden är inte byggd (`foretag/README.md`), fråga 11 |
| Räkenskapsår | 46, 27 | delvis | Finns inte i konfigurationen i dag |
| Momsperiod | 44 | täckt | |
| Koppling till Fortnox | 55 | täckt | |
| Rundtur: koppla mejl och bank, frågor som blir regelboken | 65, 58, 59, 84 | delvis | Rundturen finns inte som steg |
| Något nytt: Kassio stannar, frågar, frågar om svaret ska bli en regel | 32, 49 | krockar | Steg 49 stämmer, men DESIGN säger att en människa själv lägger in regeln. Steg 49 ligger också sent |
| Granskat läge: varje post godkänns, en i taget | 33 | täckt | |
| Automatiskt läge: bara veckans slututkast | 24, 33, 41 | krockar | SPEC 5 och steg 33 låter nivåerna styra visningen (samlat, stickprov, rad för rad), fråga 6 |
| I båda lägena skrivs inget i Fortnox före veckans slututkast | 33, 56 | krockar | SPEC 4 bokför löpande i granskat läge: på söndagen "återstår inget" |
| Godkännande i webbapp och mobilapp | 33, 68 | delvis | Steg 33 säger mobilvänlig sida. Specen säger enkel webbapp för piloten men också mobilapp, fråga 9 |
| Kortet: underlag, förslag, varför, varningar | 26, 33, Öppet 45 och 49 | delvis | Kortet är inget eget steg. Kraven på det står under Öppet |
| Kunden ber Kassio göra om förslaget | 32, SPEC 4 | täckt | |
| Kunden redigerar själv, Kassio varnar, kunden bestämmer | – | krockar | Spärrarna stoppar allt som inte har flödenas form (steg 97, 100). Inget steg beskriver ett kundändrat förslag, fråga 4 |
| Veckoutkast: sammanfattning, flaggat överst, hela listan | 33 | täckt | |
| Påminnelser trappas upp: app, mejl, sms | 32, 68 | delvis | Sms saknas |
| Inget bokförs utan godkännande | Regel 1, 19, 33, 56 | täckt | |
| Aldrig skriva i Fortnox utan godkännande | 56 | täckt | |
| Aldrig flytta pengar | Regel 2 | täckt | |
| Aldrig radera i bokföringen | SPEC 7, 27 | täckt | |
| Aldrig ändra regelboken utan ja | 30, 49 | täckt | |
| Aldrig kontakta Skatteverket, banken eller kundens kunder utan godkännande | Regel 1, 70 | krockar | Steg 70 säger att kunden godkänner varje utskick "i början" |
| Aldrig hjälpa till med något olagligt | 53 | saknas | Steg 53 är en juristfråga. Inget steg säger hur Kassio ska säga nej |
| Kvitton hämtas från mejlen | 59 | krockar | Steg 59 låter kunden vidarebefordra till en egen adress, fråga 8 |
| Papperskvitton fotas i appen | – | saknas | Koden läser bara färdig JSON, och ingen modell är inkopplad |
| Saknat kvitto: förslag ändå, märkt "kvitto saknas" | 47 | krockar | K3 gör ett ärende, och steg 100 stoppar allt utan underlag utom bankavgiften, fråga 5 |
| Utlägg via appen | – | saknas | Eget flöde, och utlägg från en ägare berör K7 |
| Bank: läskoppling med BankID | 58 | krockar | Steg 58 läser via Fortnox, fråga 8 |
| Bank: uppladdning av kontoutdrag | 3 | delvis | Ett antaget CSV-format (SPEC Ö5). Ingen uppladdning i någon app |
| Kassan: direkt koppling som hämtar dagsavsluten | 23, 43, 64, 85, nytt 111 | delvis | Z-rapporter läses bara som filer i dag. Ingen koppling finns. **Öppen fråga:** går pilotkundens kassasystem att koppla? |
| Lön: räkna ut lönen, lönespecar, förbereda utbetalning, semester, frånvaro, utbetalning den 25:e | 63, 79, nytt 133 | krockar | Byggplanen kontrollerar bara lön ovanpå Fortnox Lön, och SPEC 10 lägger löneberäkning utanför version 1. Kassio flyttar aldrig pengar |
| Kundfakturor: formulär, snygg faktura som laddas ner eller mejlas | 70, nytt 134 | krockar | Steg 70 går via Fortnox och Bokio, och SPEC 10 lägger fakturering utanför version 1 |
| Följa fakturan till betalning, påminnelsefakturor | 70, nytt 135 | delvis | Tidslinjen saknas |
| Leverantörsfakturor: fusk och dubbletter, påminnelser, attest, förbereda betalning, företaget betalar själv | 60 | täckt | |
| Lager och tillgångar: inventarier, avskrivningar, varulager, lager per artikel, periodisering | 72, 73, 76, nytt 136 | delvis | Lager saknas som eget steg |
| Årets slut: bokslut, skatt och skatteförslag, K2, INK2 | 73, 76, 77, 78 | täckt | |
| Årsstämmoprotokoll | nytt 137 | saknas | |
| Inkasso | nytt 135 | saknas | **Öppen fråga till jurist:** inkasso åt andra kräver som regel tillstånd enligt kravlistan. Troligen förbereder Kassio och lämnar över |
| Deklarationer: först förbereder Kassio och kunden lämnar in. Målet är inlämning efter kundens BankID-signering | 61, 79, 82, nytt 145 | delvis | Stämmer med regel 3 så länge kunden signerar. Automatisk inlämning saknas |
| Alla kontroller: bank mot bokföring, skattekontot, kassa mot bank, dubbletter, luckor i nummerserien | 36, 43, 45, K4, K12 | delvis | K12 gäller bara Z-numren |
| Vid en skillnad letar Kassio själv förklaringen, annars stoppas utkastet | 36 | delvis | Steg 36 stämmer av men säger inget om att leta förklaring |
| Köp från utlandet och valutor, fullt ut från start | nytt 138 | saknas | Reglerna ska komma från lagregistret, och inget får gissas |
| Fel i det som förts över till Fortnox: ny verifikation efter godkännande, inget raderas | 27, nytt 131, SPEC 7 | delvis | Steg 27 gäller bara stängda månader |
| Ägarens privata köp: flagga, förklara, föreslå, kunden bestämmer | K7, 24 | delvis | K7 ger ärende och nivå D. Förklaring och förslag saknas |
| Aldrig kontakta kundens kunder utan godkännande | Regel 1, nytt 135 | täckt | |
| Chatt kopplad till alla funktioner, bifoga filer, föreslagna frågor | 75 | delvis | Steg 75 är bara frågor om böckerna |
| Chattens gränser: om företagets ekonomi, hänvisar tunga frågor till revisor eller jurist | nytt 141 | saknas | |
| Startsidan: att göra, tidslinje, vad Kassio gjort, nyckeltal som kunden anpassar | 68, nytt 140 | delvis | Tidslinje och nyckeltal saknas |
| Rapporter: månadens resultat, likviditet, skatt att betala, resultat- och balansräkning | 62, 74 | täckt | |
| Roller: ägare/admin, godkännare, anställd, bara läsa | 68, 69 | delvis | Steg 68 säger bara "roller och ersättare" |
| Flera bolag: bolagsväljare, lägga till, hantera | nytt 146 | saknas | |
| Ton och utseende | nytt 140 | saknas | Inget steg säger något om dem |
| Så mycket som möjligt krypterat, bara kunden och agenten läser, inte personalen | nytt 114, 139 | saknas | **Öppen fråga:** hur Anthropic hanterar datan måste kontrolleras innan löftet formuleras |
| När kunden slutar: exportera, radera eller betala för att Kassio sparar | 66 | delvis | Bara export finns som steg |
| Ansvar: formellt kundens efter godkännande | SPEC 3, 53 | täckt | |
| Målen: 90 % godkänns utan ändring efter en månad, 75 % mindre tid | 50 | delvis | Steg 50 räknar godkännanden. Att fråga kunden om tiden saknas |
| Valfri import av tidigare bokföring | 65 | delvis | **Öppen fråga:** behövs den när Kassio kan läsa historiken i Fortnox? |
| Köp på hemsidan, återbetalning första månaden, 30 dagars uppsägning | nytt 147 | saknas | Behövs inte före en gratis pilot |

**Summering, 67 krav efter `KASSIO-KRAV.md`:** 17 täckta, 21 delvis, 14 saknas och 15 krockar. Inget krav är kvar som "inte läst". Antalen är räknade ur tabellen med en provfil i den tillfälliga mappen. Förut var det 45 krav, varav 7 "inte lästa".

### Det specen förutsätter men inte räknar upp

Inget av det här har ett eget steg, och utan det går ingen pilot:

- **Plats att köra på** (SPEC Ö1): var agenten körs och var kundens uppgifter ligger, skilda från det här repot.
- **Att läsa riktiga underlag:** en del som gör foto och PDF till data, i karantän (regel 6). Steg 60 nämner tolkning, men bara för leverantörsfakturor.
- **Veras egen kommandolista** (SPEC 7.1 säger att den ska skrivas): vakten skyddar bygget här, inte en körning hos en kund.
- **Riktig drift:** säkerhetskopior och vad som händer när något går sönder.

### Från byggplanen till specen: behövs inte före piloten

Bedömning utifrån kravtexten. Efter `KASSIO-KRAV.md` flyttar tillbaka: 74 och 75 (rapporter och chatt, byggs under piloten) och kassan 43 och 64 (pilotkunden har troligen ett kassasystem). 85 väntar fortfarande.

| Steg | Varför det kan vänta |
|---|---|
| 34 SIE-export | Fortnox skrivs direkt. Kan vara en reserv om kopplingen dröjer |
| 39, 40 Krog och Bygg | Målgruppen är en annan. Ett syntetiskt nystartat bolag ger mer, fråga 12 |
| 41 Simulerat automatiskt läge | Ersätts av riktiga kopplingar |
| 42 Demo | Ingen demo krävs för piloten |
| 50 Automatiseringsgrad | Behöver historik |
| 57 Bokio, 80 Spiris | Bara Fortnox vid lansering |
| 71 ROT/RUT | Hantverkare är inte målgruppen |
| 74 Likviditetsprognos, 75 Chatt | Inte nämnda i texten jag har |
| 81 Enskild firma | Bara aktiebolag |
| 82 Eget ombudsavtal | Går via Fortnox så länge det räcker |
| 84–90 Fas H | Efter piloten |
| 43, 64, 85 Kassa | Beror på den klippta texten och på pilotkunden |

**Bör stå kvar fast specen inte nämner dem:** steg 14–19 och 30 (spärrarna), 31 (granskaren, SPEC 4), 35 (loggen), 53 och 54 (jurist och konsult) och 101 (registret, Hugos beslut).

---

## C. Ordning fram till piloten

**Storlekar:** S är 1–3 omgångar, M är 4–10 och L är fler än 10. Antalen är **mina bedömningar**, inte mätningar. Tumregeln kommer från avsnitt A: något nytt kostar ett bygge och flera granskningar, men regel 9 (formen byggs med flödet) bör minska jakten på hål.

**Det största förslaget i ordningen:** bygg en **tunn hel kedja tidigt**. Följ en faktura från Fortnox, via förslag och godkännande i en enkel webbsida, tillbaka in i en testdatabas i Fortnox, innan fler flöden härdas. I dag ligger Fortnox och appen sist, så de största okända sakerna upptäcks sist.

| # | Grupp | Steg (N = nytt steg) | Storlek | Omgångar | Motivering | Måste vara klart före |
|---|---|---|---|---|---|---|
| 0 | Beslut och omskrivning | Svar på F, BYGGPLAN, SPEC 1, 4, 5 och 10 (steg 52), namnet | S | 2–3 | Bara text, men många beslut | – |
| 1 | Säkerhet | 14, 15, 16, 17, 18, 19, 30 | M | 6–10 | Vakten tog 10 granskningar förra gången. Steg 15 ska vara klar före steg 23 och före riktiga underlag | 0 |
| 2 | Kärnan klar | 96, 102, 92, 101, 23, 24, 25, 26, 27, 28, 29, 35, 36, 37, 38 | L | 20–35 | 15 steg. Flöde c och d och registret är nya | 1 (steg 23 kräver 15) |
| 3 | Kassios krav i kärnan | N: kvitto saknas. N: kundändrat förslag med varning. N: utlägg. 49. Öppet 42. N: kontantmetoden om den ska finnas | M–L | 8–16 | Krockar med spärrarna, så design först | 0, och delar av 2 |
| 4 | Fortnox | 55, 56, tunn kedja först | L | 8–14 | Okänd omvärld, och skrivning till ett riktigt system kräver spärrtest | 0, 1. Extern väntan, se E |
| 5 | Godkännandet | 31, 32, 33, 47 | M | 5–9 | Hjärtat i säkerheten | 2 (delar), 4 |
| 6 | Underlag in | N: läsare för foto och PDF. 59 eller N: mejlkoppling. 58 eller N: bankkoppling. Uppladdning. Kassasystem | L | 10–18 | Modellen kommer in här, med K17. **Kassan, efter `KASSIO-KRAV.md`:** bedömning 2–6 av omgångarna om pilotkundens kassasystem går att koppla eller ger en fil. Går det inte är storleken okänd (öppen fråga) | 28, 1 |
| 7 | Appen och driften | N: driftmiljö (Ö1). 68. N: sms. 65. N: tre frågor, uppslag, rundtur. 66, 69 | L | 15–25 | Helt nytt, och människor måste prova det | 5, och jurist för riktig data |
| 8 | Moms och månaden | 44, 45, 46, 48, 61, 62 | M | 6–10 | Bygger på avstämningen i 36 | 36, 4 |
| 9 | Lön | 63, 79, N: lönekörning | L | 10–18 | Ändrat efter `KASSIO-KRAV.md` (förut M, 4–8): kravet är hela lönekörningen med lönespecar, semester och frånvaro, inte bara en kontroll ovanpå Fortnox Lön | 4, 7 |
| 10 | Fakturor | 60, 70, N: fakturaformulär, N: tidslinje, påminnelser och inkasso som lämnas över | M–L | 8–14 | Ändrat efter `KASSIO-KRAV.md` (förut M, 4–8): formulär, egen faktura och tidslinje är nya. Inkasso beror på juristens svar | 4, 5 |
| 11 | Bokslut | 72, 73, 76, 77, 78, N: lager, N: årsstämmoprotokoll | L | 12–22 | Ändrat efter `KASSIO-KRAV.md` (förut 10–18): årsstämmoprotokoll och lager per artikel. Kräver konsult. Kan inte provas på riktigt före ett årsskifte | 8, steg 54 |
| 12 | Genrep | 67, skuggvecka | S | 3–5 | Sista spärrtestet | Allt |

**Parallellt från första dagen:** jurist (steg 53), redovisningskonsult (steg 54), Fortnox-avtalet och samtalet med pilotkunden. De kostar få omgångar men har längst väntan.

**Krav utan grupp i tabellen, storleken inte bedömd:** utländska köp och valutor, chatten, startsidan, flera bolag, kryptering och arkivet. De står under "Under piloten" och "Efter piloten" i `BYGGPLAN.md`.

---

## D. Alternativ för piloten

**Specen kräver i dag alla funktioner före piloten. Bara alternativ A följer den. B och C kräver Hugos beslut att ändra det.**

**Så är datumen räknade:** start 2026-11-09, och tre takter:

- **Tidigast:** färst omgångar, i 12 per vecka (nära det uppmätta 12,8).
- **Troligt:** mitten, i 9 per vecka.
- **Sent:** flest omgångar, i 6 per vecka.

Till det läggs 2 veckor för julen, om datumet passerar den, och 2 veckors skuggkörning för A och B. **Takten är uppmätt på små kontroller. API och app går troligen långsammare, så lita mer på "troligt" och "sent".** Extern väntan (avsnitt E) är inte medräknad, och datumen är avrundade framåt till en måndag.

| | A: Allt enligt specen | B: Bokföring, moms, veckoutkast | C: Skuggpilot |
|---|---|---|---|
| **Vad kunden får** | Alla funktioner | Bokföring skrivs i Fortnox efter godkännande, moms, veckoutkast, webbapp som fungerar i mobilen | Veckoutkast på riktig data, och **inget skrivs i Fortnox**. Kunden bokför som förut och jämför |
| **Kommer senare** | – | Lön, fakturor, bokslut, egen mobilapp, bankkoppling (kontoutdrag laddas upp) | Allt som skriver, flöde c och d om kunden inte behöver dem, foto, utlägg |
| **Grupper** | 0–12 | 0–8 och 12, mindre 6, 7 och 8 | 0, 1 och 12, och små delar av 2–8 |
| **Omgångar** | 101–179 | 72–125 | 40–68 |
| **Tidigast** | 2027-02-08 | 2027-01-18 | 2026-12-07 |
| **Troligt** | 2027-03-29 | 2027-02-22 | 2026-12-21 |
| **Sent** | 2027-07-05 | 2027-05-03 | 2027-02-15 |
| **Mitt förslag till datum** | **2027-04-05** | **2027-03-01** | **2027-01-11** |
| **Bra** | Följer specen, en enda stor start | Kunden får värde tidigt, och piloten styr resten | Lägst risk, eftersom Fortnox inte kan få fel. Riktiga format tidigt (SPEC Ö5) |
| **Risk** | Allt byggs utan riktig data, och fel upptäcks sent | Kunden behöver byrå eller annan lösning för resten under tiden | Kunden har dubbelarbete eller bara nytta av att jämföra, och behöver vilja det |
| **Kräver beslut** | Inget nytt | Ändrad spec | Ändrad spec |

- Mina datum ligger efter "troligt" av två skäl: 2027-03-29 är annandag påsk, och 2026-12-21 är rakt in i julen. 2027-03-01 ger B en liten marginal.
- Bokslut i A kan bara provas på syntetisk data, eftersom kundens första bokslut kommer först vid räkenskapsårets slut.
- **Efter `KASSIO-KRAV.md` är datumen inte ändrade.** Med de nya storlekarna i C blir A i stället 113–199 omgångar (uppskattning), men A är inte valt, så datumen för A är inte räknade om. B och C innehåller inte lön, fakturor och bokslut, så de berörs inte. Kassan ligger kvar inom grupp 6. Går pilotkundens kassasystem inte att koppla eller ge en fil kan det flytta datumen för B och C.

**Min rekommendation: C från 2027-01-11, och sedan B från 2027-03-01.** Resten byggs under piloten, vilket stämmer med specens "byggs vidare utifrån vad piloten visar". Det som mest kan stoppa C i januari är juristen, eftersom riktig data kräver svaren i steg 53, och Fortnox-avtalet.

---

## E. Extern hjälp och avtal

**Bara Fortnox är kontrollerat.** Jag läste `fortnox.se/developer` 2026-11-04. De andra sidorna gick inte att nå eller var tomma, så resten är frågor att ställa, inte fakta. Datumen i D räknar inte med väntan här.

| Vem | Vad som behövs | Kontrollerat? | Påverkan på datumen |
|---|---|---|---|
| **Jurist** (steg 53) | Penningtvättslagen, kundavtal, ansvar, personuppgiftsavtal, överföring till USA (BYGGPLAN steg 53). Efter `KASSIO-KRAV.md` också: riktig data i skuggpiloten, pilotkundens skriftliga godkännande för siffror i marknadsföring, ekonomiansvariges två roller, och om krypteringslöftet håller | Inte kontrollerat | **Stoppar alla tre alternativen.** Hugo eller Casper kontaktar juristen den här veckan (beslut 14) |
| **Fortnox** | Registrera sig som utvecklare och acceptera App Partner-avtalet. Fortnox granskar programmet, kopplingen, landningssidan, kontaktuppgifter, pris och användaravtal innan kunder kan aktivera det | Ja, men sidan säger inget om tider, kostnad eller testmiljö | **Stoppar grupp 4.** Öppen fråga till Fortnox: gäller hela granskningen också en enda gratis pilotkund? Steg 55 räknar med en testdatabas, som inte är bekräftad |
| **Redovisningskonsult** (steg 54) | D1–D16, Ö3, Ö4, Öppet 38, moms när kvitto saknas, utlägg, bokslut och INK2. Efter `KASSIO-KRAV.md` också: utländska köp och valutor, lön och semester, varulager, och årsstämmoprotokollet. Hugo eller Casper kontaktar konsulten den här veckan (beslut 14) | Inte kontrollerat | Behövs för pilotkundens egna val redan i C, och för alla bokföringsbeslut i B. Stoppar grupp 11 |
| **BankID** | Inloggning i appen. Vilket avtal det kräver är en öppen fråga | Inte kontrollerat | Stoppar inte om appen startar med annan inloggning, som steg 68:s tvåstegsverifiering |
| **Bankkoppling** | Att läsa kundens konton är en reglerad verksamhet som kan kräva tillstånd eller en leverantör som har det. **Öppen fråga till jurist** | Inte kontrollerat | Kan bli lång väntan. Piloten använder uppladdade kontoutdrag, och BankID-kopplingen kommer senare (beslut 8) |
| **Skatteverket** | Steg 61 går via Fortnox, och steg 82 är ett eget ombudsavtal. Enligt `KASSIO-KRAV.md` förbereder Kassio först och kunden lämnar in, och målet är inlämning efter kundens BankID-signering. **Öppen fråga** om moms via Fortnox räcker | Inte kontrollerat | Stoppar inte i piloten, där kunden lämnar in själv. Steg 78 har ett datum: e-tjänsten för INK2 stängs 2026-12-29 (BYGGPLAN) |
| **Inkasso** | Kravlistan säger att inkasso åt andra som regel kräver tillstånd, och att Kassio troligen förbereder och lämnar över till ett inkassobolag. **Öppen fråga till jurist** | Inte kontrollerat | Byggs under piloten: påminnelser först, inkasso först efter juristens svar |
| **Språkmodell** | Villkor för kunddata. Kravlistan säger att hur Anthropic hanterar datan måste kontrolleras innan krypteringslöftet formuleras. Steg 53 noterar att Anthropic inte har någon EU-region, vilket bör prövas igen | Inte kontrollerat | Ingår i juristens svar. **Stoppar skuggpiloten**, som skickar riktig data till modellen när underlag läses |
| **Pilotkunden** | Pilotavtal, en person som godkänner, tillgång till Fortnox, vilja att vara med i en skuggpilot, bokföringsmetod (beslut 10), kassasystem, och skriftligt godkännande för siffror i marknadsföring | – | Måste frågas nu. Bestämmer också om kassasystem behövs |
| **Kassasystemet** | Om pilotkundens kassasystem går att koppla, och vilka kassasystem som är vanligast (öppen fråga i `KASSIO-KRAV.md`) | Inte kontrollerat | Kan stoppa kassadelen i piloten om varken koppling eller fil finns |
| **Bolagsuppgifter** | Var namn, bolagsform, adress, momsregistrering och F-skatt hämtas när kunden skriver organisationsnumret | Inte kontrollerat | Stoppar inte piloten, där uppgifterna kan fyllas i för hand |
| **Mejl, sms, driftmiljö** | Leverantörer väljs i grupp 6 och 7 | Inte kontrollerat | Bedömning: korta väntetider |

---

## F. Frågor till Hugo innan BYGGPLAN.md skrivs om

**Besvarade 2026-11-04:** Hugos beslut 15 säger att alla svar är enligt rekommendationerna nedan, med de andra besluten som svar där de säger något annat.

Min rekommendation står efter varje fråga.

1. **Resten av specen:** kan du klistra in den? *Behövs för B–E. Allt efter "Kassasystem: direkt" är oläst.* Besvarad: `KASSIO-KRAV.md`.
2. **Omfång och datum:** A, B eller C? *C från 2027-01-11, sedan B från 2027-03-01.*
3. **Vem är pilotkunden?** Namnet skrivs inte i någon fil (Hugos uppdrag 2026-11-04). *Viktigt för kassa, samlingsbetalningar och regeln om arkivmappen. Var ska en riktig kunds uppgifter ligga? Aldrig i det här repot.*
4. **Kunden ändrar ett förslag:** vad får kunden bestämma över? *Kunden får välja konto och text mot en varning, men ett förslag ska alltid gå ihop (K2), en stängd period ska förbli stängd, och inget skrivs före godkännandet. Designas först, med en egen form, och granskas som säkerhet.*
5. **Saknat kvitto:** ska det bli ett förslag ändå, i stället för ett ärende (K3)? *Ja, som specen säger, med en egen form och märkning. Hur moms ska hanteras då är en **Öppen fråga** till redovisningskonsult eller Skatteverket.*
6. **Nivåerna A–D:** ska de finnas kvar när kunden bara ser två lägen? *Ja, men bara för att sortera och flagga. SPEC 5 skrivs om, och nivå D förblir "alltid människan".*
7. **Granskat läge:** skrivs allt först efter veckans utkast, och hämtar Kassio underlag själv också där? *Ja på båda. SPEC 4 skrivs om.*
8. **Mejl och bank:** riktig koppling till företagsmejlen eller vidarebefordran? BankID-koppling eller via Fortnox? *Specen säger riktig koppling. För piloten: börja med vidarebefordran och uppladdning, eftersom de går fortare och kräver mindre behörighet. Det kräver ditt beslut.*
9. **Mobilapp:** räcker en webbapp som fungerar i mobilen under piloten, också för foto? *Ja. Specen säger både "enkel webbapp" och "mobilapp".*
10. **Hur mycket ska granskas?** BYGGPLAN säger efter varje fas. I praktiken har varje steg granskats. *Behåll en oberoende granskning per steg för det som rör godkännande, spärrar eller skrivning i Fortnox. För annat: per grupp. Fynd som kräver kod förbi flödena och fortfarande en människas godkännande går till Öppet, inte till ett nytt steg före piloten, utom när de rör godkännandet. Det här är det beslut som flyttar datumen mest, så det är ditt att väga mot risken.*
11. **Kontantmetoden:** ska onboardingen erbjuda den i piloten? *Avgörs av pilotkunden. Bygg den bara om den behövs. Vad som gäller för vem är en **Öppen fråga** till konsulten.*
12. **Testföretagen:** behålla Krog och Bygg före piloten? *Nej. Ersätt med ett syntetiskt nystartat aktiebolag.*
13. **Namnet:** när byter vi till Kassio, i dokument, kod och repo? *Dokument och kod i grupp 0. Repot när det passar, det är inte bråttom.*
14. **Steg 14, Caspers dator:** den var planerad till helgen vecka 44, som är förbi (i dag är det vecka 45), och står som inte klar. Är den gjord? *Behöver ett nytt datum annars.*
15. **Jurist och konsult:** vem kontaktar dem, och vilken budget finns? *Hugo eller Casper, den här veckan. Jag kan förbereda frågorna.*

**Efter svaren:** BYGGPLAN.md skrivs om i samma session som den här kompletteringen. SPEC.md, CLAUDE.md och namnbytet görs i nästa session.
