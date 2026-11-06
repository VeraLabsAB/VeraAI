"""Hugos beslut 2026-11-06 om granskning 44 och installationen av steg 149 (GRANSKNING.md).

Testerna låser besluten ordagrant, att Öppet 74 är stängd, att steg 149 är klart, att steg 150 finns och står i texten för
steg 118, och meningen i beslut 6. De låser inga ord som ändras vid nästa statusändring (P1 i granskning 42): raden "Nästa steg"
prövas bara på det som inte får stå kvar, och status för steg 150 prövas inte. Att installationen och proven faktiskt gjordes kan
ett test inte visa. Det är Hugos uppgift i beslut 1 och 2.
"""

import re

import pytest

from test_sandladan import (
    BYTE_149_RUBRIK,
    GRANSKNING,
    PROJEKTET,
    _avsnitt,
    _avsnitt_i_granskning,
    _byggplanens_rad,
    _en_rad_text,
    _post_under_oppet,
    _raden_i_lage_nu,
)

RUBRIK = "## Hugos beslut 2026-11-06 om granskning 44 och installationen av steg 149"
BESLUT = [
    '1. Installationen är gjord och provad av Hugo 2026-11-06 enligt INSTALLERA.md, "Byte till nästa version av vakten (steg 149)". '
    "Version: appen 2.1.317, Terminal 2.1.319. Provkörningen med --settings: Write och Read till /System vägrades av "
    "blockWritesOutsideWorkingDirectories och blockReadsOutsideWorkingDirectories, Write och Read i scratchpad gick igenom, sviten i "
    "Terminal gav 0 failed, 5843 passed, 77 skipped. Summorna före stämde, kopiorna .fore-steg-149 är exakta, och efter bytet är "
    "summorna d99ff000… och a903190eb4… med -rw-r--r-- root wheel. /status visade Enterprise managed settings (file). Vakten som "
    "program: isolation och Isolation med tomt värde gav stopp och kod 2, Agent utan isolation kod 0.",
    "2. Spärrproven i appen: Write till /System, Write med relativ sökväg och Read av /etc/hosts vägrades av de två inställningarna. "
    "Edit stoppades av att filen måste läsas först, och läsningen är spärrad, så skrivspärren för Edit är inte prövad direkt. Grep "
    "och Glob finns inte i skrivbordsappen och är inte prövade. En underagent fick Write till /System vägrat av "
    "blockWritesOutsideWorkingDirectories (sett i underagentens ruta). WebFetch till .invalid och Write till .git i scratchpad "
    "stoppades av vakten. Write och Read i scratchpad, WebFetch till code.claude.com och git status gick igenom. Sviten i appen: 0 "
    "failed, 5849 passed, 71 skipped. Prov utanför sandlådan på 885c8aa6607ec7974e53defca25b4e3428e9471c: 39 passed, ingen rad GRUPP "
    "D HOPPAS ÖVER. Kopian är borttagen.",
    "3. Öppet 74 stängs: hålet från prov 17 är stängt av steg 149.",
    "4. Öppet 77 har sin förklaring: vakten stoppar SubagentHandback, verktyget som underagenter lämnar sin rapport med. Om det ska "
    "släppas igenom är ett eget beslut senare. Öppet 77 står kvar öppen.",
    "5. P1 i granskning 44 blir ett nytt steg 150 i BYGGPLAN.md: sandlådan stänger nätet och läsning utanför projektet och scratchpad "
    "för Bash och testfiler. Steg 150 ska vara klart före första körningen på riktiga underlag. Kravet skrivs i texten för steg 118, "
    "inte i kolumnen Beror på.",
    "6. P2: bara ett fel som nämner arbetsmapparna (working directories) räknas som en vägran. Står det read-only, EROFS, Operation "
    "not permitted eller Permission denied: stanna och fråga. En mening om det läggs i avsnittet för steg 149 i INSTALLERA.md.",
    "7. P3: Hugos kontroll 2026-11-06, grep -n -e additionalDirectories -e OutsideWorkingDirectories ~/.claude/settings.json, gav "
    "ingen rad.",
    "8. P4–P10 står kvar under Öppet 80.",
    "9. /add-dir används aldrig i projektet. Det lägger till en mapp där agenten får läsa och skriva, och vakten ser det inte.",
    "10. Steg 149 är klart. Nästa steg är steg 30. Den här sessionen granskas tillsammans med steg 30.",
    "11. Försiktighetsreglerna i Hugos beslut 2026-11-06 om granskning 43, beslut 2: regel 1 (ingen session utan att Hugo tittar) och "
    "regel 2 (ingen underagent med isolation, som vakten nu stoppar) upphör. Regel 3 (inget innehåll utifrån i en session som kan "
    "skriva, och svaren från steg 105 och 106 tas inte in i en Code-session) gäller tills steg 150 är klart.",
]

MENINGEN_I_BESLUT_6 = (
    "Bara ett fel som nämner arbetsmapparna (working directories) räknas som en vägran, och står det read-only, `EROFS`, "
    "`Operation not permitted` eller `Permission denied`: stanna och fråga."
)


def _post(nummer):
    return " ".join(_post_under_oppet(nummer).split())


def _beror_pa(nummer):
    return [int(tal) for tal in re.findall(r"\d+", _byggplanens_rad(nummer).strip().strip("|").split("|")[-1], re.ASCII)]


@pytest.mark.parametrize("beslut", BESLUT, ids=[str(n) for n in range(1, len(BESLUT) + 1)])
def test_granskning_44_besluten_star_ordagrant(beslut):
    assert beslut in _avsnitt_i_granskning(RUBRIK)


def test_granskning_44_besluten_star_efter_granskningen():
    text = GRANSKNING.read_text(encoding="utf-8")
    assert text.index("## Granskning 44 (av 2b295f6)") < text.index(RUBRIK)


def test_granskning_44_b3_oppet_74_ar_stangd():
    post = _post(74)
    assert post.startswith("~~") and "**Stängd" in post and "**Öppen" not in post
    assert "Hugos beslut 2026-11-06 om granskning 44 och installationen av steg 149, beslut 3" in post


def test_granskning_44_b4_oppet_77_har_forklaringen_och_star_kvar_oppen():
    post = _post(77)
    assert not post.startswith("~~") and "**Stängd" not in post
    assert "`SubagentHandback`" in post and "eget beslut senare" in post
    assert post.endswith("**Öppen.**")


@pytest.mark.parametrize("fynd", ["P4", "P5", "P6", "P7", "P8", "P9", "P10"])
def test_granskning_44_b8_oppet_80_har_kvar_de_laga_fynden(fynd):
    assert f"**{fynd}, låg:**" in _post(80)


def test_granskning_44_oppet_80_sager_vad_som_ar_beslutat_och_star_kvar_oppen():
    post = _post(80)
    assert "Kvar: P4–P10" in post and "steg 150" in post and "gav ingen rad" in post
    assert post.endswith("**Öppen.**")


def test_granskning_44_b10_steg_149_ar_klart():
    rad = _byggplanens_rad(149)
    assert "| ✅ 2026-11-06" in rad and "🔶" not in rad and "Inte installerad" not in rad
    assert "Hugos beslut 2026-11-06 om granskning 44 och installationen av steg 149" in rad
    assert not re.search(r"(?<!\d)149 – ", _raden_i_lage_nu("Pågående steg"))
    assert re.search(r"(?<!\d)149 – ", _raden_i_lage_nu("Senast avslutade steg"))


@pytest.mark.parametrize(
    "text",
    ["provkörningen och bytet enligt", "Hugos beslut om granskning 44", "de tre försiktighetsreglerna"],
)
def test_granskning_44_nasta_steg_har_inte_kvar_laget_fore_installationen(text):
    assert text not in _raden_i_lage_nu("Nästa steg")


@pytest.mark.parametrize("text", ["Sandlådan", "nätet", "läsning utanför projektet och scratchpad", "Bash", "testfiler", "Öppet 80"])
def test_granskning_44_b5_steg_150_finns_och_sager_vad_det_ar(text):
    assert text in _byggplanens_rad(150).split(" | ")[1]


def test_granskning_44_b5_steg_150_ska_vara_klart_fore_riktiga_underlag():
    assert "före första körningen på riktiga underlag" in _byggplanens_rad(150)


def test_granskning_44_b5_steg_150_star_bara_i_texten_for_steg_118():
    rad = _byggplanens_rad(118)
    assert "Steg 150 ska också vara klart före första körningen på riktiga underlag" in rad
    assert 150 not in _beror_pa(118)


def test_granskning_44_b6_meningen_star_i_avsnittet_for_steg_149():
    assert MENINGEN_I_BESLUT_6 in _en_rad_text(_avsnitt(BYTE_149_RUBRIK))


def test_granskning_44_b6_meningen_star_bara_en_gang_i_filen():
    text = _en_rad_text((PROJEKTET / "sparr" / "INSTALLERA.md").read_text(encoding="utf-8"))
    assert text.count(MENINGEN_I_BESLUT_6) == 1


def test_granskning_44_progress_har_en_post_for_installationen():
    text = (PROJEKTET / "PROGRESS.md").read_text(encoding="utf-8")
    assert "\n## Läge 2026-11-06, steg 149 klart, installerat och provat\n\nSteg i byggplanen: 149" in text
