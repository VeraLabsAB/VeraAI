"""Hugos beslut 2026-10-28 efter granskning 18 (GRANSKNING.md, "Hugos beslut 2026-10-28 (efter granskning 18)").

- I1: vakten stoppar varje sökväg vars första del direkt under roten börjar med punkt (till exempel /.vol,
  /.nofollow och /.resolve), oavsett stora och små bokstäver och extra snedstreck, före och efter att sökvägen har
  räknats om. Det gäller verktygen som skriver eller ändrar filer och sökvägar i kommandon.

Testen här prövar bara text med vaktens bedom: ingen fil skrivs via /.vol eller /.nofollow, och inga länkar görs
(H3). Vakten letar upp dit länkarna leder med os.path.realpath, som tittar på disken. I testen tittar den bara i
testets tillfälliga mapp: en sökväg utanför den räknas bara som text (fixturen bara_text_utanfor_testet), så att
testen inte rör /.vol, /System eller andra systemets mappar. Fallet där en länk leder till /.vol prövas med en
låtsad länk på samma sätt, eftersom en riktig sådan länk skulle peka ut ur testets tillfälliga mapp. Kommandona
prövas med en tom PATH, som i test_beslut_granskning_17.py, så att vakten inte tittar på systemets program.
"""

import os

import pytest

from test_beslut_granskning_17 import PATH_SAKNAS, _skriv
from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    PYTEST,
    _bedom,
    _spec_7_1,
    mappar,
    vakt,
)

I1 = "granskning 18, I1"
# Många ../ når roten och stannar där.
UPP = "../" * 40


@pytest.fixture(autouse=True)
def bara_text_utanfor_testet(tmp_path, monkeypatch):
    """os.path.realpath tittar bara på disken för sökvägar i testets tillfälliga mapp. Andra hela sökvägar räknas om
    bara som text (../ och extra snedstreck), som om de inte hade några länkar (H3)."""
    riktig = os.path.realpath
    rotter = {str(tmp_path), riktig(str(tmp_path))}

    def realpath(sokvag, *args, **kwargs):
        if isinstance(sokvag, str) and os.path.isabs(sokvag):
            text = os.path.normpath(sokvag)
            if not any(text == rot or text.startswith(rot + "/") for rot in rotter):
                return text
        return riktig(sokvag, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", realpath)

SKRIVNINGAR_UNDER_PUNKT = [
    "/.vol/16777220/12345/pre-commit",
    "/.vol/16777220/12345/.zshrc",
    "/.nofollow<H>/.zshrc",
    "/.nofollow<P>/scripts/ny.py",
    "/.VOL/16777220/12345/pre-commit",
    "/.Nofollow<H>/.zshrc",
    "//.vol/16777220/12345/pre-commit",
    "///.vol/16777220/12345/pre-commit",
    "/./.vol/16777220/12345/pre-commit",
    "/.resolve/16777220/12345/pre-commit",
    "/.RESOLVE/16777220/12345/x",
    # Efter att sökvägen har räknats om: ../, ~ och macOS andra namn för datavolymen.
    "/x/../.vol/16777220/12345/pre-commit",
    "/../.vol/16777220/12345/pre-commit",
    f"<P>/{UPP}.vol/16777220/12345/pre-commit",
    f"{UPP}.nofollow<H>/.zshrc",
    f"~/{UPP}.vol/16777220/12345/x",
    "/System/Volumes/Data/.vol/16777220/12345/x",
]


@pytest.mark.parametrize("sokvag", SKRIVNINGAR_UNDER_PUNKT)
@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_i1_skrivverktyg_under_punkt_vid_roten_stoppas(vakt, mappar, verktyg, sokvag):
    fel = _skriv(vakt, mappar, sokvag, verktyg)
    assert fel is not None and I1 in fel, fel


KOMMANDON_UNDER_PUNKT = [
    "mkdir -p /.vol/16777220/12345/x",
    "mkdir -p /.VOL/16777220/12345/x",
    "mkdir -p //.vol/16777220/12345/x",
    "mkdir -p /.nofollow<T>/x",
    "mkdir -p /.resolve/16777220/12345/x",
    f"mkdir -p <T>/{UPP}.nofollow<T>/x",
    "cp -R SPEC.md /.vol/16777220/12345/pre-commit",
    "cp -R SPEC.md /.nofollow<T>/x",
    "cp -R /.vol/16777220/12345 <T>/kopia",
    "tar -x -f <T>/kopia.tar -C /.vol/16777220/12345",
    "tar -c -f /.nofollow<T>/kopia.tar SPEC.md",
    "git archive -o /.vol/16777220/12345/x.tar HEAD",
    "git archive --output=//.vol/16777220/12345/x.tar HEAD",
    "git commit -F /.vol/16777220/12345/meddelande",
    "cat /.vol/16777220/12345/x",
    "cat /.nofollow<P>/SPEC.md",
    "ls /.VOL/16777220/12345",
    f"ls {UPP}.vol/16777220/12345",
    "grep -n x //.vol/16777220/12345/x",
    "grep -rn x /.resolve/16777220/12345",
    "diff SPEC.md /.nofollow<P>/SPEC.md",
    f"{PYTEST} /.vol/16777220/12345/kopia/scripts/tests",
]


@pytest.mark.parametrize("kommando", KOMMANDON_UNDER_PUNKT)
def test_i1_kommandon_under_punkt_vid_roten_stoppas(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando, sokvag="")
    assert fel is not None and I1 in fel, fel


@pytest.fixture
def lank_till_vol(vakt, mappar, monkeypatch):
    """Låtsas att <P>/lank och <T>/lank är länkar till /.vol/16777220/12345. Bara os.path.realpath byts ut, och bara
    för de två sökvägarna. Ingen länk görs (H3)."""
    lankar = [os.path.join(mappar["projekt"], "lank"), os.path.join(mappar["tillfallig"], "lank")]
    riktig = os.path.realpath

    def realpath(sokvag, *args, **kwargs):
        for lank in lankar:
            if sokvag == lank or sokvag.startswith(lank + "/"):
                return "/.vol/16777220/12345" + sokvag[len(lank):]
        return riktig(sokvag, *args, **kwargs)

    monkeypatch.setattr(vakt.os.path, "realpath", realpath)


@pytest.mark.parametrize("sokvag", ["<P>/lank/pre-commit", "lank/.zshrc"])
@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_i1_skrivverktyg_via_en_lank_till_punkt_vid_roten_stoppas(vakt, mappar, lank_till_vol, verktyg, sokvag):
    fel = _skriv(vakt, mappar, sokvag, verktyg)
    assert fel is not None and I1 in fel, fel


@pytest.mark.parametrize("kommando", ["mkdir -p <T>/lank/x", "cp -R SPEC.md <T>/lank/x", "cat lank/x"])
def test_i1_kommandon_via_en_lank_till_punkt_vid_roten_stoppas(vakt, mappar, lank_till_vol, kommando):
    fel = _bedom(vakt, mappar, kommando, sokvag="")
    assert fel is not None and I1 in fel, fel


@pytest.mark.parametrize(
    "sokvag",
    ["<P>/SPEC.md", "<P>/scripts/ny.py", "scripts/ny.py", "<P>/.gitignore", "<P>/.vol/x", "<P>/scripts/.nofollow",
     "<T>/kopia/SPEC.md", "<T>/.vol/x", "<T>/kopia/.nofollow/x", "<H>/VERA/prov.txt"],
)
@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_i1_vanliga_filer_gar_att_skriva(vakt, mappar, verktyg, sokvag):
    # En mapp som börjar med punkt längre ner än direkt under roten stoppas inte av I1.
    assert _skriv(vakt, mappar, sokvag, verktyg) is None


@pytest.mark.parametrize(
    "kommando",
    ["mkdir -p <T>/kopia/.vol", "cp -R SPEC.md <T>/kopia/x", "cp -R scripts <T>/.nofollow", "cat SPEC.md",
     "cat <T>/.vol", "ls scripts", "grep -rn x scripts", "tar -x -f <T>/kopia.tar -C <T>/kopia",
     "git archive -o <T>/x.tar HEAD"],
)
def test_i1_vanliga_kommandon_klarar_reglerna_fore_path_regeln(vakt, mappar, kommando):
    fel = _bedom(vakt, mappar, kommando, sokvag="")
    assert fel is not None and PATH_SAKNAS in fel, fel


def test_i1_star_i_spec():
    spec = _spec_7_1()
    assert "**En sökväg vars första del direkt under roten börjar med punkt stoppas alltid** (granskning 18, I1, Hugos beslut 2026-10-28)" in spec
    assert "`/.vol`" in spec and "`/.nofollow`" in spec and "`/.resolve`" in spec and "`//.vol`" in spec
