"""Hantering av belopp som heltal i öre.

Alla belopp i kärnan är heltal i öre, aldrig flyttal (float).
Här finns två funktioner:

- tolka_belopp("1 234,56") -> 123456
- formatera_ore(123456)    -> "1234,56"
"""

import re

# Mellanslag som får användas som tusentalsavgränsare:
# vanligt mellanslag, hårt mellanslag och smalt hårt mellanslag.
_TUSENTAL = " \u00a0\u202f"

# Heltalsdelen är antingen bara siffror ("1234"),
# eller grupper om tre siffror med mellanslag emellan ("1 234 567").
_MONSTER = re.compile(
    r"(?P<tecken>-?)"
    r"(?P<kronor>\d+|\d{1,3}(?:[" + _TUSENTAL + r"]\d{3})+)"
    r"(?:[.,](?P<decimaler>\d+))?",
    re.ASCII,  # bara siffrorna 0-9, inga andra skriftsystems siffror
)


def tolka_belopp(text):
    """Tolkar ett belopp i text och returnerar det som heltal i öre.

    Decimaltecken får vara komma eller punkt. Tusentalsavgränsare får vara mellanslag.
    Högst två decimaler. Allt annat ger ValueError.
    """
    if not isinstance(text, str):
        raise TypeError(
            "Beloppet måste vara text, inte " + type(text).__name__ + "."
        )

    rensad = text.strip()
    traff = _MONSTER.fullmatch(rensad)
    if traff is None:
        raise ValueError("Ogiltigt belopp: " + repr(text) + ".")

    decimaler = traff.group("decimaler") or ""
    if len(decimaler) > 2:
        raise ValueError(
            "Ogiltigt belopp: " + repr(text) + " har fler än två decimaler."
        )

    kronor = traff.group("kronor")
    for tecken in _TUSENTAL:
        kronor = kronor.replace(tecken, "")

    ore = int(kronor) * 100 + int(decimaler.ljust(2, "0"))
    if traff.group("tecken") == "-":
        ore = -ore
    return ore


def formatera_ore(ore):
    """Formaterar ett heltal i öre som text med exakt två decimaler, t.ex. 123456 -> "1234,56"."""
    if isinstance(ore, bool) or not isinstance(ore, int):
        raise TypeError(
            "Beloppet måste vara ett heltal i öre, inte " + type(ore).__name__ + "."
        )

    tecken = "-" if ore < 0 else ""
    kronor, rest = divmod(abs(ore), 100)
    return tecken + str(kronor) + "," + str(rest).zfill(2)
