# Kassio Finance – kraven ur Hugos intervju 2026-10-31

Utdrag gjort 2026-11-04. Källan är Hugos intervju (projektdokumentet claude/intervju-kassio.md i Claude-projektet, inte i repot). Personliga uppgifter om ekonomi och finansiering är borttagna. Pilotkunden nämns inte vid namn. Där intervjun har ändrats står "ändrat".

## Produkten
- Kassio Finance, bolaget Kassio Labs AB (inte registrerat än). Agenten har inget eget namn.
- En digital ekonomikollega som ligger ovanpå kundens bokföringsprogram och ersätter redovisningsbyrån, inte programmet. Använder företagets redan valda program.
- Bara Fortnox vid lansering. Kunder utan program får Fortnox rekommenderat och betalar det själva.
- Målgrupp: nystartade företag. Bara aktiebolag i version 1 (enskild firma behövs inte i startformuläret).
- Pris 999 kr/mån eller 2 997 kr/kvartal. Om priset är inklusive eller exklusive moms är öppet.
- Köp alltid via hemsidan. Första månaden betalas och återbetalas om kunden avslutar under den. Sedan 30 dagars uppsägning.

## Piloten
- Pilotkunden är första riktiga kund, gratis pilot. Pilotkundens ekonomiansvarige godkänner Kassios förslag. Han är också med och bygger Kassio (öppen fråga: två roller).
- Bara siffror på resultatet får användas i marknadsföring, inte namn eller citat. Skriftligt godkännande från pilotkunden behövs.
- Ändrat 2026-11-04 (Hugos beslut efter PLAN-KASSIO-FORSLAG.md, alternativ C och sedan B): piloten startar som en skuggpilot (förslag: från 2027-01-11). Kassio tar fram veckoutkast på pilotkundens riktiga data men skriver inget i Fortnox, och pilotkundens ekonomiansvarige bokför som vanligt och jämför. Sedan (förslag: från 2027-03-01) bokföring, moms och veckoutkast som skrivs i Fortnox efter godkännande. Lön, fakturor, bokslut och resten byggs under piloten, i den ordning piloten visar. Datumen är uppskattningar, inte löften.
- Tidigare (ersatt 2026-11-04): piloten startar först när pilotagenten har alla funktioner, i en enkel webbapp.
- I piloten: en webbapp som fungerar i mobilen (också för att fota kvitton), kvitton och fakturor vidarebefordras till en egen adress, kontoutdrag laddas upp. Mobilapp, mejlkoppling och BankID-koppling kommer senare.
- Öppen fråga: vad räknas som färdigt för funktioner som kräver avtal eller extern hjälp (till exempel att Kassio förbereder och kunden lämnar in)?

## Från köp till start
1. Köp på hemsidan.
2. Tre frågor som slår på funktioner ("du kan ändra allt senare"): skickar eller tar du emot fakturor? Betalar företaget ut lön (även till dig själv)? Har du lager eller tillgångar (inventarier, maskiner, varulager)?
3. Organisationsnummer. Kassio hämtar namn, bolagsform, adress, momsregistrering och F-skatt. Kunden bekräftar eller ändrar. Företagets e-post.
4. Bokföringsmetod: faktureringsmetoden eller kontantmetoden.
5. Räkenskapsår: när det slutar, startdag (från bolagsregistret, kan ändras), om första året var vanligt eller förlängt.
6. Moms: hur ofta (månad, kvartal, år) och från vilket datum.
7. Bokföringsprogram (lista). Kunden loggar in, till exempel i Fortnox, så att det kopplas.
8. Valfri import av tidigare bokföring (öppen fråga: behövs den när Kassio kan läsa historiken i Fortnox?).
- Sedan öppnas appen med en rundtur som går att hoppa över. Kunden kopplar företagsmejlen (där fakturor hamnar) och banken. Frågor som "Hur brukar ni sköta den här delen idag?" blir en del av regelboken. Kunden kan läsa hur allt fungerar.
- När något nytt dyker upp som regelboken inte täcker stannar Kassio och frågar. Sedan frågar Kassio "Ska jag göra så här varje gång?" och kunden väljer om svaret blir en regel eller bara gäller den gången.

## Lägen och godkännande
- I båda lägena för Kassio över till Fortnox först efter att kunden godkänt veckans slututkast.
- Granskat läge: kunden godkänner varje enskild post under veckan, en i taget (nästa visas först när den förra är godkänd), plus slututkastet.
- Automatiskt läge: bara slututkastet i slutet av veckan.
- Godkännande i webbappen och en mobilapp (öppen fråga: när mobilappen byggs).
- Kortet visar underlaget, förslaget, varför och varningar. Förklaring och varning bara där det behövs.
- När kunden inte håller med frågar Kassio vad som är fel. Kunden svarar så att Kassio gör om förslaget, eller redigerar posten direkt.
- Om kundens egen ändring troligen bryter mot reglerna varnar och förklarar Kassio, men kunden bestämmer.
- Veckoutkastet i automatiskt läge: sammanfattning, osäkra eller ovanliga poster lyfts fram, hela listan finns.
- Inget godkännande i tid: påminnelserna trappas upp (app, mejl, sms) närmare deadline. Inget bokförs utan godkännande, även om deadline missas.

## Underlag in
- Digitala kvitton hämtas automatiskt från mejlen. Fysiska kvitton fotas i appen.
- Saknat kvitto: Kassio föreslår bokföring ändå, markerar "kvitto saknas" och påminner. Kunden kan godkänna med egen förklaring om kvittot är borta.
- Utlägg: den anställde fotar kvittot i appen och markerar utlägg. Kassio bokför skulden till den anställde, ägaren godkänner, Kassio förbereder återbetalningen (med nästa lön eller som egen betalning).
- Bank: både koppling med BankID som bara kan läsa (de stora svenska bankerna, flera konton per företag) och uppladdning av kontoutdrag som fil.
- Kassan: direkt koppling till kassasystemet som hämtar dagsavsluten. Pilotkunden använder troligen DinKassa (öppen fråga: går det att koppla, och vilka kassasystem är vanligast?).

## Kontroller och regler
- Alla kontroller som behövs för att säkerställa att inget blivit fel (till exempel bank mot bokföring, skattekontot, kassa mot bank, dubbletter, luckor i nummerserien).
- Vid en skillnad letar Kassio förklaringen själv (till exempel kortavgifter). Hittas den föreslås bokföring med förklaring, annars stoppas utkastet och kunden får frågan.
- Köp från utlandet och valutor hanteras fullt ut: utländska leverantörer, omräkning till kronor, rätt moms, med reglerna i lagregistret från start.
- Fel i något som redan förts över till Fortnox: Kassio föreslår en rättelse (ny verifikation) med förklaring. Kunden godkänner. Inget raderas.
- I första versionen: inventarier och avskrivningar, varulager, lager per artikel, periodisering.
- Ägarens privata köp och insättningar: Kassio flaggar, förklarar varför det spelar roll och föreslår hantering. Kunden bestämmer.
- Aldrig: skriva i Fortnox utan godkännande, flytta pengar, radera i bokföringen, ändra regelboken utan att kunden sagt ja, kontakta Skatteverket, banken eller kundens kunder utan godkännande, hjälpa till med något olagligt (till exempel dölja intäkter). Fler punkter tas fram när varje del kodas.

## Moms, lön, fakturor, bokslut
- Deklarationer och årsredovisning: i början förbereder Kassio och kunden lämnar in själv. Målet är att Kassio lämnar in automatiskt till Skatteverket efter att kunden signerat med BankID.
- Lön: Kassio räknar ut lönen, skickar lönespecar, förbereder utbetalningen, hanterar semester och frånvaro. Utbetalning den 25:e, eller närmaste vardag före om den 25:e är en helgdag. Kassio flyttar aldrig pengar själv. (Öppen fråga: ska lönedagen kunna ändras per företag?)
- Kundfakturor: ett formulär där kunden fyller i fakturadatum, fakturanummer (obruten serie per räkenskapsår, till exempel 2026-001), säljarens uppgifter (namn, adress, momsregistreringsnummer), köparens uppgifter, varor eller tjänster (mängd, omfattning, art), leveransdatum, pris exklusive moms, momssats (25, 12, 6 % eller momsfritt) och momsbelopp, totalbelopp, F-skatt, bolagets officiella namn, organisationsnummer, säteskommun, betalningsvillkor och förfallodatum, bankgiro eller plusgiro, dröjsmålsränta, er/vår referens och eventuellt order- eller offertnummer. Kassio gör en snygg och professionell faktura som kunden laddar ner eller som Kassio mejlar.
- Efter utskick följer Kassio fakturan till betalning i en tidslinje, noterar förfallodatum och meddelar när den är betald, försenad eller måste till inkasso. Kassio kan skapa påminnelsefakturor och ha hand om inkassoärenden. (Öppen fråga: inkasso åt andra kräver som regel tillstånd; troligen förbereder Kassio och lämnar över till ett inkassobolag.)
- Leverantörsfakturor: varna för fusk och dubbletter, påminna om förfallodag, attest och bokföring, förbereda betalning. Kassio meddelar att en faktura kommit. Företaget betalar själv och meddelar Kassio, som bokför.
- Årets slut: bokslutsarbetet, skatt och skatteförslag, årsredovisning K2, årsstämmoprotokoll, inkomstdeklaration INK2. Kassio förbereder, kunden godkänner och skriver under.

## Appen
- Chatt kopplad till alla funktioner: uppdrag, frågor om ekonomin, råd och förklaringar. Bifoga filer, förslag på frågor efter vad som är aktuellt. Ingen mikrofon i första versionen.
- Chattens gränser: Kassio svarar om företagets ekonomi. Vid tunga skatte- eller juridikfrågor förklarar Kassio reglerna men säger att kunden bör fråga en revisor eller jurist.
- Startsidan: att göra-lista, tidslinje med deadlines, vad Kassio gjort, många nyckeltal som kunden kan anpassa.
- Rapporter: månadens resultat, likviditet och pengar framåt, skatt att betala, resultat- och balansräkning.
- Roller: ägare/admin (den som köper, bjuder in och bestämmer roller), godkännare, anställd (kvitton), bara läsa.
- Flera bolag: bolagsväljare uppe till vänster (namn och organisationsnummer), "Lägg till företag" (tre steg, börjar med organisationsnumret) och "Hantera företag".
- Ton: kunnig kollega som säger "du". Utseende: chatt först, att göra-lista och dashboard, egen layout, Light Steel-färger och glassmorphism.

## Data och ansvar
- Så mycket data som möjligt krypteras (inspirerat av Mullvad). Kassio sparar alla händelser och dokument som ett digitalt bibliotek, som pärmar med kvitton.
- Bara kunden och agenten kan läsa kundens dokument. Inte Kassio Labs personal, inte ens vid support.
- När en kund slutar väljer kunden: exportera arkivet, radera det, eller betala en liten avgift för att Kassio sparar det.
- Öppen fråga: agenten skickar text till Claude (Anthropic) när den arbetar. Hur Anthropic hanterar datan måste kontrolleras innan krypteringslöftet formuleras.
- Ansvar: formellt kundens efter godkännande, men Kassio Labs ska vara rättvist och hjälpa kunden så gott det går.

## Mål
- Minst 90 % av förslagen godkänns utan ändring efter första månaden hos en kund.
- Kassio levererar resultat som hade kunnat skickas till Fortnox direkt.
- Kunden lägger 75 % mindre tid än innan (mäts genom att fråga kunden vid start och efter en månad).
