"""Kärnans reserverade ord: namn som inget i ett företags konfiguration får ha.

Några ord är kärnans egna namn, till exempel på ett flöde (las_regelbok.FLODEN), och står därför i
kärnans kod. Kärnan får aldrig innehålla ett företags egna namn (SPEC 2, test_karnan_ar_generell.py),
så ett företag får inte använda de orden (Hugos beslut 2026-10-29, efter uppgift 4). Från början gällde
det bara en regels namn i matchning.json och ett regel-id i regelbok.json. Hugos beslut 2026-10-30
(granskning 22, Öppet 27): orden stoppar alla namn i konfigurationen, men bara vid exakt träff, inte
som en del av ett längre namn. Namnen som prövas:

- bankformat.json: kolumnnamnen,
- kassaformat.json: kolumnnamnen, postnamnen (även betalsätten) och kassaregistren,
- kontoplan.json: kontonamnen,
- momssatser.json: varugrupperna,
- matchning.json: reglernas namn,
- regelbok.json: regel-id, motparter, kassaregister, ägare och närstående, betalsätten i en Z-regels
  kontering och företagets namn (foretag). De två sista efter Hugos beslut 2026-10-30 om granskning 23
  (P3).

Namnet jämförs efter normaliseringen för jämförelser (normalisering.normalisera_for_jamforelse):
stora och små bokstäver, blanksteg och vilken sorts bindestreck det är räknas inte. "Bankavgift",
"BANKAVGIFT" och "bank avgift" är alltså det reserverade ordet "bankavgift" och stoppas, medan
"Bankavgift AB", "bankavgifter" och "bank-avgift" inte är det och godtas. Listan står också i
foretag/README.md, och ett test kontrollerar att de har samma ord.
"""

from normalisering import normalisera_for_jamforelse

RESERVERADE_NAMN = ("bankavgift",)


def reserverat_namn(namn):
    """Det reserverade ordet som namnet är lika med efter normaliseringen, eller None (RESERVERADE_NAMN)."""
    for reserverat in RESERVERADE_NAMN:
        if normalisera_for_jamforelse(namn) == normalisera_for_jamforelse(reserverat):
            return reserverat
    return None


def inget_reserverat_namn(namn, vad, var, fel):
    """Stoppar med felklassen fel om namnet är ett reserverat ord. Returnerar namnet oförändrat.

    vad säger vilket namn det gäller, till exempel "'namn' i regel nummer 2", och var vilken fil.
    """
    reserverat = reserverat_namn(namn)
    if reserverat is not None:
        raise fel(
            var + ": " + vad + " är " + repr(namn) + ", som är det reserverade ordet " + repr(reserverat) + ". Det är"
            " kärnans eget namn på ett flöde, och inget namn i konfigurationen får vara det ordet (Hugos beslut"
            " 2026-10-30, Öppet 27). Ge det ett annat namn."
        )
    return namn
