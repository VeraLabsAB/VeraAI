"""BYGGPLAN.md och PROGRESS.md visar samma läge (uppdraget 2026-10-29 om "Läge nu").

Testet läser bara projektets egna filer och skriver ingenting.

Formatet som testet läser:

- BYGGPLAN.md har avsnittet "## Läge nu" med raderna "- **Uppdaterad:** ÅÅÅÅ-MM-DD" och
  "- **Pågående steg:** 22 – namn; 13 – namn". Ett stegnummer är ett tal som följs av " – ".
- Tabellerna under "## Fas ..." i BYGGPLAN.md har stegets nummer i första kolumnen och status (✅, 🔶 eller ⬜)
  i tredje.
- Det första "## Läge"-avsnittet i PROGRESS.md börjar med raden "Steg i byggplanen: 22 (pågår) och 13 (pågår)".
- Varje granskning i GRANSKNING.md har en rubrik "## Granskning N" med ett eget nummer.
"""

import re
from pathlib import Path

PROJEKT = Path(__file__).resolve().parents[2]
BYGGPLAN = PROJEKT / "BYGGPLAN.md"
PROGRESS = PROJEKT / "PROGRESS.md"
GRANSKNING = PROJEKT / "GRANSKNING.md"

STATUSAR = ("✅", "🔶", "⬜")
DATUM = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)
STEGNUMMER = re.compile(r"(?<!\d)(\d+) – ", re.ASCII)
TABELLRAD = re.compile(r"^\| (\d+) \|", re.ASCII)
GRANSKNINGSRUBRIK = re.compile(r"^## Granskning (\d+)(?!\d)", re.ASCII)

# "Granskning 11 – plan för Q1" är en plan som granskaren skrev i samma session som granskning 11,
# inte en egen granskning (GRANSKNING.md, första stycket under rubriken, och Hugos beslut i chatten
# 2026-10-29). Bara exakt den här rubriken undantas, så en ny granskning med numret 11 gör ändå testet rött.
DELAR_AV_EN_GRANSKNING = {"## Granskning 11 – plan för Q1 (2026-10-28)"}


def rader(fil):
    return fil.read_text(encoding="utf-8").splitlines()


def avsnitt(alla_rader, rubrik_borjar_med):
    """Raderna under den första rubriken på nivå 2 som börjar med texten, fram till nästa sådan rubrik."""
    for start, rad in enumerate(alla_rader):
        if rad.startswith(rubrik_borjar_med):
            slut = start + 1
            while slut < len(alla_rader) and not alla_rader[slut].startswith("## "):
                slut += 1
            return alla_rader[start + 1:slut]
    return None


def lage_nu():
    innehall = avsnitt(rader(BYGGPLAN), "## Läge nu")
    assert innehall is not None, "BYGGPLAN.md saknar avsnittet \"## Läge nu\""
    return innehall


def rad_med(innehall, etikett, var):
    traffar = [rad for rad in innehall if rad.startswith("- **" + etikett + ":**")]
    assert len(traffar) == 1, (
        var + " ska ha exakt en rad \"- **" + etikett + ":**\", hittade " + str(len(traffar))
    )
    return traffar[0][len("- **" + etikett + ":**"):]


def stegens_status():
    """Stegnummer → statuscell, för tabellerna under rubrikerna "## Fas" i BYGGPLAN.md."""
    status = {}
    i_en_fas = False
    for rad in rader(BYGGPLAN):
        if rad.startswith("## "):
            i_en_fas = rad.startswith("## Fas ")
        if not i_en_fas or not TABELLRAD.match(rad):
            continue
        celler = [cell.strip() for cell in rad.strip().strip("|").split("|")]
        nummer = int(celler[0])
        assert nummer not in status, "Steg " + str(nummer) + " står två gånger i BYGGPLAN.md"
        status[nummer] = celler[2]
    return status


def pagaende_steg():
    text = rad_med(lage_nu(), "Pågående steg", "\"Läge nu\" i BYGGPLAN.md")
    nummer = [int(tal) for tal in STEGNUMMER.findall(text)]
    assert nummer, (
        "Ingen stegnummer under Pågående steg i BYGGPLAN.md. Skriv till exempel "
        "\"22 – Uppgift 4; 13 – Kontrollen efter installationen\""
    )
    return nummer


def forsta_lage_i_progress():
    innehall = avsnitt(rader(PROGRESS), "## Läge")
    assert innehall is not None, "PROGRESS.md saknar ett avsnitt \"## Läge ...\""
    return innehall


def steg_i_progress():
    forsta_raden = next((rad for rad in forsta_lage_i_progress() if rad.strip()), "")
    assert forsta_raden.startswith("Steg i byggplanen:"), (
        "Första \"## Läge\"-avsnittet i PROGRESS.md ska börja med raden \"Steg i byggplanen: N\" "
        "(CLAUDE.md), men börjar med " + repr(forsta_raden)
    )
    return forsta_raden[len("Steg i byggplanen:"):]


# (a) "Läge nu" finns, och varje pågående steg finns i tabellerna utan status ✅


def test_varje_steg_i_byggplanen_har_en_status():
    status = stegens_status()
    assert 22 in status and 90 in status, "Testet hittar inte tabellerna i BYGGPLAN.md"
    fel = [str(nummer) + ": " + repr(cell) for nummer, cell in sorted(status.items())
           if not cell.startswith(STATUSAR)]
    assert not fel, "Steg utan status (✅, 🔶 eller ⬜) i BYGGPLAN.md:\n" + "\n".join(fel)


def test_lage_nu_har_de_fem_raderna():
    innehall = lage_nu()
    for etikett in ("Uppdaterad", "Pågående steg", "Senast avslutade steg", "Nästa steg", "Opushat"):
        rad_med(innehall, etikett, "\"Läge nu\" i BYGGPLAN.md")


def test_pagaende_steg_finns_och_ar_inte_klara():
    status = stegens_status()
    fel = []
    for nummer in pagaende_steg():
        if nummer not in status:
            fel.append("steg " + str(nummer) + " finns inte i tabellerna")
        elif status[nummer].startswith("✅"):
            fel.append("steg " + str(nummer) + " har status ✅ men står som pågående")
    assert not fel, "Pågående steg i \"Läge nu\" stämmer inte:\n" + "\n".join(fel)


# (b) Första "## Läge"-avsnittet i PROGRESS.md säger vilket steg det hör till


def test_progress_sager_vilket_steg_och_stegen_finns():
    nummer = [int(tal) for tal in re.findall(r"\d+", steg_i_progress(), re.ASCII)]
    assert nummer, "Raden \"Steg i byggplanen:\" i PROGRESS.md har inget stegnummer"
    status = stegens_status()
    saknas = [str(tal) for tal in nummer if tal not in status]
    assert not saknas, "Steg i PROGRESS.md som inte finns i BYGGPLAN.md: " + ", ".join(saknas)


def test_steg_som_pagar_i_progress_pagar_i_byggplanen():
    pagar_i_progress = [int(tal) for tal in re.findall(r"(\d+) \(pågår\)", steg_i_progress(), re.ASCII)]
    saknas = [str(tal) for tal in pagar_i_progress if tal not in pagaende_steg()]
    assert not saknas, (
        "Steg som pågår enligt PROGRESS.md men inte står under Pågående steg i BYGGPLAN.md: "
        + ", ".join(saknas)
    )


# (c) Samma datum i "Läge nu" och överst i PROGRESS.md


def test_lage_nu_har_samma_datum_som_progress():
    i_byggplanen = DATUM.findall(rad_med(lage_nu(), "Uppdaterad", "\"Läge nu\" i BYGGPLAN.md"))
    assert len(i_byggplanen) == 1, "Raden Uppdaterad i \"Läge nu\" ska ha exakt ett datum"
    overst = [rad for rad in rader(PROGRESS) if rad.startswith("Uppdaterad ")]
    assert overst, "PROGRESS.md saknar raden \"Uppdaterad ÅÅÅÅ-MM-DD\" överst"
    i_progress = DATUM.findall(overst[0])
    assert i_progress, "Raden Uppdaterad överst i PROGRESS.md har inget datum"
    assert i_byggplanen[0] == i_progress[0], (
        "\"Läge nu\" i BYGGPLAN.md är uppdaterad " + i_byggplanen[0]
        + " men PROGRESS.md " + i_progress[0]
    )


# (d) Inga två granskningar med samma nummer


def test_inga_tva_granskningar_har_samma_nummer():
    sedda = {}
    dubbletter = []
    for rad in rader(GRANSKNING):
        traff = GRANSKNINGSRUBRIK.match(rad)
        if not traff or rad in DELAR_AV_EN_GRANSKNING:
            continue
        nummer = int(traff.group(1))
        if nummer in sedda:
            dubbletter.append(str(nummer) + ": " + repr(sedda[nummer]) + " och " + repr(rad))
        sedda[nummer] = rad
    assert len(sedda) >= 20, "Testet hittar inte granskningarna i GRANSKNING.md"
    assert not dubbletter, "Granskningar med samma nummer i GRANSKNING.md:\n" + "\n".join(dubbletter)


def test_undantaget_for_planen_finns_kvar():
    # Skydd mot att undantaget blir kvar och tyst släpper igenom något annat om rubriken ändras.
    alla = set(rader(GRANSKNING))
    assert DELAR_AV_EN_GRANSKNING <= alla
