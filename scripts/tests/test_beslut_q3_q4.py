"""Hugos beslut 2026-10-29 om Q2–Q4 (GRANSKNING.md, "Hugos beslut 2026-10-29 om Q2–Q4").

- Q3: sökformen för ett namn (namnet delat i ord, ihopsatt och normaliserat) finns i en offentlig funktion,
  normalisering.sokform_for_namn, som både star_som_hela_ord och regelboken använder. Regelboken använder inte
  längre den interna funktionen _ord_i. Skyddstestet binder ihop "godtas" och "hittas": varje ägarnamn som
  regelboken godtar hittas också i en bankrad.
- Q4: kommentaren överst i las_regelbok.py säger samma sak som SPEC 11 om undantagen.

Ingen av rättelserna ändrar hur något fungerar. Allt skrivs i testets tillfälliga mapp.
"""

import ast
import itertools
import re
import sys
from pathlib import Path

from test_las_regelbok import bok, konfiguration, las  # noqa: F401 (konfiguration är en fixture)

AGENT = Path(__file__).resolve().parents[2]
SKRIPT = AGENT / "scripts"
sys.path.insert(0, str(SKRIPT))

import normalisering  # noqa: E402
from las_regelbok import RegelbokFel  # noqa: E402

NORMALISERING_FIL = SKRIPT / "normalisering.py"
REGELBOK_KOD = SKRIPT / "las_regelbok.py"


def _tradet(fil):
    return ast.parse(fil.read_text(encoding="utf-8"))


def _funktion(trad, namn):
    """Funktionen med namnet, på översta nivån i filen."""
    for del_ in trad.body:
        if isinstance(del_, ast.FunctionDef) and del_.name == namn:
            return del_
    raise AssertionError("funktionen " + namn + " finns inte")


def _anropar(trad, namn):
    """True om trädet anropar en funktion med namnet."""
    return any(isinstance(del_, ast.Call) and isinstance(del_.func, ast.Name) and del_.func.id == namn
               for del_ in ast.walk(trad))


def _namn_i(trad):
    """Alla namn som trädet använder eller importerar."""
    namn = set()
    for del_ in ast.walk(trad):
        if isinstance(del_, ast.Name):
            namn.add(del_.id)
        elif isinstance(del_, ast.Attribute):
            namn.add(del_.attr)
        elif isinstance(del_, ast.alias):
            namn.add(del_.name)
    return namn


# --- Q3: en gemensam, offentlig sokform_for_namn ---

def test_q3_las_regelbok_anvander_inte_ord_i():
    # _ord_i börjar med _ och är bara för normalisering.py.
    assert "_ord_i" not in _namn_i(_tradet(REGELBOK_KOD))


def test_q3_star_som_hela_ord_och_las_regelbok_anvander_samma_sokform_for_namn():
    # Funktionen finns, är offentlig och används på båda ställena.
    assert callable(getattr(normalisering, "sokform_for_namn", None))
    assert _anropar(_funktion(_tradet(NORMALISERING_FIL), "star_som_hela_ord"), "sokform_for_namn")
    regelboken = _tradet(REGELBOK_KOD)
    importerat = {alias.name for del_ in regelboken.body if isinstance(del_, ast.ImportFrom)
                  and del_.module == "normalisering" for alias in del_.names}
    assert "sokform_for_namn" in importerat
    assert _anropar(_funktion(regelboken, "_kontrollera_agare_och_narstaende"), "sokform_for_namn")
    # Samma sökform som förut, så att inget ändras i hur det fungerar.
    for namn in ["Åsa Öberg", "É. Larsson AB", "PAHITTAD-AGARE", "-", "_ .", "A" + chr(0x00A8), "e" + chr(0x0301)]:
        assert normalisering.sokform_for_namn(namn) == normalisering.normalisera_for_jamforelse(
            "".join(normalisering._ord_i(namn))), namn


# Tecknen som granskaren i granskning 11 prövade: bokstäver med och utan accent, en siffra, de tre
# skiljetecknen som får finnas i ett namn, mellanslag, ett tankstreck och "e" med en kombinerande accent.
TECKEN = ["a", "Å", "é", "0", "-", ".", "_", " ", chr(0x2013), "e" + chr(0x0301)]
P1_FELET = "som saknar bokstäver och siffror"


def test_q3_varje_agarnamn_som_regelboken_godtar_hittas_i_en_bankrad(tmp_path, konfiguration):  # noqa: F811
    # Skydd för Q3 (och P1, granskning 10): alla namn av 1–3 av tecknen ovan. Varje namn som regelboken
    # godtar ska hittas i en bankrad med namnet. Ett namn som stoppas för att det saknar bokstäver och siffror
    # ska aldrig kunna hittas.
    godtagna, utan_bokstaver = 0, 0
    for langd in (1, 2, 3):
        for delar in itertools.product(TECKEN, repeat=langd):
            namn = "".join(delar)
            try:
                regelbok = las(tmp_path, bok(agare_och_narstaende=[namn]), konfiguration)
            except RegelbokFel as fel:
                if P1_FELET in str(fel):
                    utan_bokstaver += 1
                    assert not normalisering.star_som_hela_ord(namn, "UTTAG " + namn), repr(namn)
                continue
            godtagna += 1
            for text in ("UTTAG " + namn, "UTTAG " + namn + "/LAN", "UTTAG (" + namn + ")"):
                assert regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": text, "referens": ""}), (
                    repr(namn), text)
    # Provet prövar något åt båda hållen.
    assert godtagna > 500 and utan_bokstaver > 50, (godtagna, utan_bokstaver)


# --- Q4: kommentaren överst i las_regelbok.py stämmer med SPEC 11 ---

def test_q4_kommentaren_om_agarlistan_namner_undantagen_i_spec_11():
    beskrivning = " ".join(ast.get_docstring(_tradet(REGELBOK_KOD)).split())
    # Stycket om agare_och_narstaende, fram till beskrivningen av en regel.
    stycket = beskrivning.split("agare_och_narstaende lista med motparter", 1)[1].split("En regel har exakt", 1)[0]
    for text in ("dolt tecken", "trasig JSON", "före listan", "egen text"):
        assert text in stycket, text
    # SPEC 11 säger samma sak.
    spec = " ".join((AGENT / "SPEC.md").read_text(encoding="utf-8").split())
    assert re.search(r"Ett dolt tecken eller trasig JSON någonstans i filen, och ett annat fel i filen som hittas"
                     r" före listan, stoppar också regelboken", spec)
