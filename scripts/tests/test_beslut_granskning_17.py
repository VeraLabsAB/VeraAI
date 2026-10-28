"""Hugos beslut 2026-10-28 efter granskning 17 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 17)").

- H3: regeln om prov och test står i CLAUDE.md och SPEC 7.1. Det är en regel i text. Den tekniska spärren är
  sandlådan, som ska vara klar före uppgift 5.

Testen här läser bara filer i projektet och skriver bara i testets tillfälliga mapp (H3). De gör inga länkar.
"""

import pytest

from test_kommandosparr import PROJEKTET, _en_rad, _spec_7_1

CLAUDE_MD = PROJEKTET / "CLAUDE.md"


# ---------------------------------------------------------------------------------------------
# H3: regeln om prov och test.

H3_REGELN = [
    "Prov och test får bara skapa, ändra eller länka filer i scratchpad",
    "eller i testets tillfälliga mapp",
    "Aldrig länkar (hårda eller mjuka) till något utanför de mapparna",
    "Nya test får inte läsa eller röra riktiga systemfiler",
    "regel i text",
    "sandlådan",
    "före uppgift 5",
    "granskning 17, H3",
]


@pytest.mark.parametrize("del_", H3_REGELN)
@pytest.mark.parametrize("fil", ["CLAUDE.md", "SPEC 7.1"])
def test_h3_regeln_om_prov_och_test_star_i_claude_md_och_spec(fil, del_):
    text = _en_rad(CLAUDE_MD.read_text(encoding="utf-8") if fil == "CLAUDE.md" else _spec_7_1())
    assert del_ in text, f"{fil} saknar: {del_}"
