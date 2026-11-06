"""Steg 149, mellanvägen (Hugos beslut 2026-11-06 om granskning 43 och om steg 149, mellanvägen, GRANSKNING.md).

- Beslut 1: Claude Codes två inställningar under permissions i sparr/managed-settings.json, och version 2.1.314.
- Beslut 2: vakten stoppar Agent när tool_input har fältet isolation, oavsett stora och små bokstäver, med vilket värde som helst.
- Beslut 3: vakten släpper WebFetch bara till de två webbplatserna, skrivna exakt.
- Beslut 5, 6 och 9: INSTALLERA.md. Kommandona och deras ordning låses i test_sandladan.py, BYTET_149.
- Granskning 43, P4, P5 och P6: Öppet 74, SPEC 7.1, och att besluten och steg 149 låses, utan att låsa ordval.

Vakten prövas som funktion och som program, med vaktens Python och flaggorna ur inställningarna. Inget verktyg körs på riktigt,
och inget nät används. Att Claude Code vägrar utanför arbetsmapparna kan ett test inte visa. Det visar provkörningen och
spärrproven i INSTALLERA.md.
"""

import hashlib
import json
import re

import pytest

from test_kommandosparr import (  # noqa: F401 (fixturerna används av pytest via namnen)
    INSTALLERA,
    INSTALLERAD_VAKT,
    INSTALLNINGAR,
    PROJEKTET,
    SYSTEMETS_SOKVAG,
    VAKTENS_PYTHON,
    _kor_programmet,
    mappar,
    vakt,
)
from test_sandladan import (
    AKTIV,
    BYTE_149_RUBRIK,
    BYTE_18_RUBRIK,
    BYTET_149,
    GRANSKNING,
    INSTALLERAD_VAKT_CITERAD,
    INSTALLNINGARNAS_SUMMA_STEG_18,
    PROGRAMMET_149,
    PROVFILEN_149,
    SPARAD_149,
    SPARAD_VAKT_149,
    VAKTENS_SUMMA_STEG_18,
    _avsnitt,
    _avsnitt_i_granskning,
    _byggplanens_rad,
    _en_rad_text,
    _kodrader,
    _post_under_oppet,
    _spec_7_1,
)

PROVFILEN = PROJEKTET / "sparr" / "provkorning-steg-149.json"
NYCKLARNA = ("blockWritesOutsideWorkingDirectories", "blockReadsOutsideWorkingDirectories")


def _bedom_verktyg(vakt, mappar, verktyg, verktygsdata):
    return vakt.bedom(_verktyg(mappar, verktyg, verktygsdata), mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)


def _verktyg(mappar, verktyg, verktygsdata):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": verktyg,
        "tool_input": verktygsdata,
        "cwd": mappar["projekt"],
        "scratchpad_dir": mappar["tillfallig"],
    }


# ---------------------------------------------------------------------------------------------
# Besluten ordagrant (P6). Inga ord om status, så att en senare ändring av läget inte ger rött (P1 i granskning 42).

SPARRTEST_RUBRIK = "## Spärrtest efter steg 15–18 (steg 19, 2026-11-06)"
SPARRTEST_BESLUT = [
    "1. Listan, prov 1–23, är godkänd.",
    "2. Prov 9 och 10 körs, i de riktiga mapparna.",
    "3. Prov 17 körs i det läge sessionen redan har. Frågar appen om lov svarar Hugo nej. Skapas filen utan fråga är det ett fynd. "
    "Skriv det, kör inga fler prov som skriver utanför projektet, och fortsätt med resten.",
    "4. Exitkriteriet för steg 19: vakten, sandlådan och Claude Codes egna förbud stoppar det de ska, och tabellen i GRANSKNING.md "
    "är loggen. De sex spärrtesterna i SPEC prövas i de steg där koden byggs.",
    "5. För stort belopp och förfalskat godkännande skrivs under Öppet, utan att något byggs. Båda ska ha ett eget steg i "
    "BYGGPLAN.md innan godkännandet byggs (steg 33).",
    "6. Omskrivna sökningar utan | \\ $ * ! och bakåtfnutt är tillåtna. Stanna för allt annat som vakten eller ett säkerhetsfilter "
    "stoppar.",
    "7. Prov 17: appen frågade inte om lov. Filen skapades i läget sessionen körs i, utan fråga och utan att någon spärr stoppade "
    "den. Hugo har kontrollerat innehållet (bara provtexten) och tagit bort filen. Fynd, nivå allvarlig: fil-verktygen kan skriva i "
    "hela hemmappen utom förbudslistan, och i läget auto frågar Claude Code inte alltid.",
    "8. Ett nytt steg i BYGGPLAN.md, direkt efter granskning 43: fil-verktygen som skriver (Write, Edit, MultiEdit, NotebookEdit) "
    "får bara skriva i projektmappen och scratchpad, som en tillåtelselista i vakten. I samma steg utreds om Read ska begränsas på "
    "samma sätt, och Hugo beslutar. Det blir en ny version av vakten, med granskning och installation. Steget ska vara klart före "
    "första körningen på riktiga underlag och före uppgift 5.",
    "9. Prov 20: inte visat. Hugo har ingen skärmbild av underagentens ruta. Spärrtestet 2026-10-29 visade att vakten stoppar date "
    "för en underagent. Den saknade rapporten och de 6 anropen går till Öppet.",
    "10. Svagheten i läsprovet (grönt också när ~/.ssh/prov saknas) och avvikelsen med den saknade filen skrivs in. Svagheten går "
    "till Öppet.",
    "11. Steg 19 är klart: vakten, sandlådan och Claude Codes förbud stoppade det de är byggda för. Fyndet i prov 17 gäller det som "
    "ingen spärr täcker, och det stängs i steget i beslut 8. Granskning 43 tar e323025 och den här sessionen.",
]

BESLUT_43_RUBRIK = "## Hugos beslut 2026-11-06 om granskning 43"
BESLUT_43 = [
    "1. P1, P2 och P3 tas med i steg 149. Vakten stoppar Agent med isolation. Tillåtelselistan prövar dit länkarna leder, inte bara "
    "texten. Exitkriteriet prövar också Edit, relativa sökvägar, saknad scratchpad och underagenter. Utredningen gäller Read, Grep, "
    "Glob och WebFetch, och Hugo beslutar. Claude Codes inställning blockWritesOutsideWorkingDirectories utreds som ett andra lager "
    "bredvid vaktens lista.",
    "2. Tills steg 149 är installerat gäller tre försiktighetsregler: ingen session körs utan att Hugo tittar, ingen underagent "
    "startas med isolation, och inget innehåll utifrån tas in i en session som kan skriva. WebFetch får bara användas mot Claude "
    "Codes egen dokumentation. Svaren från steg 105 och 106 tas inte in i en Code-session före steg 149.",
    "3. P7 godtas, samma val som P1 i granskning 42.",
    "4. P4, P5 och P6 rättas i steg 149. P8–P11 står kvar under Öppet 78.",
]

BESLUT_149_RUBRIK = "## Hugos beslut 2026-11-06 om steg 149 (mellanvägen)"
BESLUT_149 = [
    "1. Steg 149 byggs som mellanvägen. Claude Codes inställningar blockWritesOutsideWorkingDirectories och "
    "blockReadsOutsideWorkingDirectories slås på under permissions i de låsta inställningarna, och requiredMinimumVersion höjs till "
    "2.1.314. Det ersätter vaktens egen tillåtelselista i beslut 1 om granskning 43, så länge proven i beslut 5 och 7 håller.",
    "2. Vakten stoppar Agent när tool_input har fältet isolation, oavsett stora och små bokstäver i namnet och med vilket värde som "
    "helst, också tomt.",
    "3. Vakten släpper WebFetch bara till https://code.claude.com/ och https://docs.claude.com/, med värdnamnet exakt så, utan port, "
    "användare eller lösenord, och utan ? % @ eller \\ i adressen. Allt annat stoppas.",
    "4. Vaktens egen tillåtelselista för Write, Edit och läsverktygen, prövning av länkar, och en lista med tillåtna fält och typer "
    "för Agent byggs inte nu. De skrivs under Öppet och byggs om provkörningen eller spärrproven visar en lucka.",
    "5. Provkörning före bytet, i Terminal, med de nya inställningarna via --settings: Write och Read utanför projektet och "
    "scratchpad ska vägras av Claude Code, Write och Read i scratchpad ska gå igenom, och hela sviten ska inte ha något rött. Vägras "
    "Read i scratchpad, eller blir något rött: Hugo stannar och frågar.",
    "6. Spärrproven använder /System/kassio-prov-149-*.txt och https://kassio-prov-149.invalid/ som mål. Länkar och Agent med "
    "isolation provas bara i test och mot den installerade vaktfilen som program, inte med riktiga verktyg.",
    "7. Exitkriteriet för steg 149: testerna är röda före och gröna efter, provkörningen före bytet är godkänd, och spärrproven efter "
    "installationen är godkända. Öppet 74 stängs först då.",
    "8. Testräkningen görs i del 2. Testet test_beslut_42_b10_… tas bort, eftersom P7 är godtaget.",
    "9. Skrivbordsappens Claude Code ska vara minst 2.1.314 före bytet. Det kontrolleras i INSTALLERA.md.",
]


@pytest.mark.parametrize("beslut", SPARRTEST_BESLUT, ids=[str(n) for n in range(1, len(SPARRTEST_BESLUT) + 1)])
def test_steg_149_p6_besluten_om_sparrtestet_star_ordagrant(beslut):
    assert beslut in _avsnitt_i_granskning(SPARRTEST_RUBRIK)


@pytest.mark.parametrize("beslut", BESLUT_43, ids=[str(n) for n in range(1, len(BESLUT_43) + 1)])
def test_steg_149_besluten_om_granskning_43_star_ordagrant(beslut):
    assert beslut in _avsnitt_i_granskning(BESLUT_43_RUBRIK)


@pytest.mark.parametrize("beslut", BESLUT_149, ids=[str(n) for n in range(1, len(BESLUT_149) + 1)])
def test_steg_149_besluten_om_mellanvagen_star_ordagrant(beslut):
    assert beslut in _avsnitt_i_granskning(BESLUT_149_RUBRIK)


# ---------------------------------------------------------------------------------------------
# Beslut 2: Agent med isolation.

AGENT_STOPPAS = [
    {"isolation": "worktree"},
    {"isolation": "remote"},
    {"Isolation": "worktree"},
    {"ISOLATION": "remote"},
    {"iSoLaTiOn": "worktree"},
    {"isolation": ""},
    {"Isolation": ""},
    {"isolation": None},
    {"isolation": False},
    {"isolation": 0},
    {"isolation": []},
    {"isolation": {}},
    {"prompt": "x", "description": "y", "isolation": "worktree"},
    {"prompt": "x", "Isolation": ""},
]
AGENT_SLAPPS = [
    {},
    {"prompt": "x", "description": "y"},
    {"prompt": "isolation", "description": "isolation", "subagent_type": "general-purpose"},
    {"isolate": "worktree"},
    {"x_isolation": "worktree"},
    {"isolation_": "worktree"},
]


@pytest.mark.parametrize("data", AGENT_STOPPAS, ids=json.dumps)
def test_steg_149_b2_agent_med_isolation_stoppas(vakt, mappar, data):
    fel = _bedom_verktyg(vakt, mappar, "Agent", data)
    assert fel is not None and fel.startswith("Stoppat av vakten") and "isolation" in fel, fel


@pytest.mark.parametrize("data", AGENT_SLAPPS, ids=json.dumps)
def test_steg_149_b2_agent_utan_isolation_slapps(vakt, mappar, data):
    assert _bedom_verktyg(vakt, mappar, "Agent", data) is None


@pytest.mark.parametrize("data", AGENT_STOPPAS, ids=json.dumps)
def test_steg_149_b2_programmet_stoppar_agent_med_isolation(mappar, data):
    svar = _kor_programmet(mappar, _verktyg(mappar, "Agent", data))
    assert svar.returncode == 2 and svar.stdout == b"", svar.stderr
    assert "isolation" in svar.stderr.decode("utf-8")


@pytest.mark.parametrize("data", AGENT_SLAPPS, ids=json.dumps)
def test_steg_149_b2_programmet_slapper_agent_utan_isolation(mappar, data):
    svar = _kor_programmet(mappar, _verktyg(mappar, "Agent", data))
    assert (svar.returncode, svar.stdout, svar.stderr) == (0, b"", b"")


# ---------------------------------------------------------------------------------------------
# Beslut 3: WebFetch. Inget nät används: vakten läser bara adressen.

WEBFETCH_SLAPPS = [
    "https://code.claude.com/",
    "https://docs.claude.com/",
    "https://code.claude.com/docs/en/settings",
    "https://docs.claude.com/en/docs/overview",
]
WEBFETCH_STOPPAS = [
    # Annan värd.
    "https://kassio-prov-149.invalid/",
    "https://example.com/",
    "https://claude.com/",
    "https://claude.ai/",
    "https://www.code.claude.com/",
    "https://code.claude.com.invalid/",
    "https://xcode.claude.com/",
    # http.
    "http://code.claude.com/",
    "http://docs.claude.com/docs",
    "ftp://code.claude.com/",
    # Port.
    "https://code.claude.com:443/",
    "https://docs.claude.com:8443/docs",
    # Användare och lösenord.
    "https://hugo@code.claude.com/",
    "https://hugo:losen@docs.claude.com/",
    "https://code.claude.com@kassio-prov-149.invalid/",
    "https://code.claude.com:x@kassio-prov-149.invalid/",
    # ? % @ och \ var de än står.
    "https://code.claude.com/docs?x=1",
    "https://code.claude.com/?",
    "https://docs.claude.com/docs%2Fx",
    "https://code.claude.com/%",
    "https://code.claude.com/@x",
    "https://docs.claude.com/a@b",
    "https://code.claude.com/docs\\x",
    "https://code.claude.com\\@kassio-prov-149.invalid/",
    # Stora bokstäver i värdnamnet och i början.
    "https://CODE.claude.com/",
    "https://code.CLAUDE.com/",
    "https://docs.Claude.com/",
    "https://code.claude.COM/",
    "HTTPS://code.claude.com/",
    "Https://docs.claude.com/",
    # Inte en hel adress.
    "https://code.claude.com",
    "https://docs.claude.com",
    "code.claude.com/",
    "//code.claude.com/",
    " https://code.claude.com/",
    "",
]
WEBFETCH_FEL_TYP = [{}, {"prompt": "x"}, {"url": None}, {"url": 1}, {"url": ["https://code.claude.com/"]}, {"URL": "https://code.claude.com/"}]


@pytest.mark.parametrize("adress", WEBFETCH_SLAPPS)
def test_steg_149_b3_de_tva_webbplatserna_slapps(vakt, mappar, adress):
    assert _bedom_verktyg(vakt, mappar, "WebFetch", {"url": adress, "prompt": "x"}) is None


@pytest.mark.parametrize("adress", WEBFETCH_STOPPAS)
def test_steg_149_b3_allt_annat_stoppas(vakt, mappar, adress):
    fel = _bedom_verktyg(vakt, mappar, "WebFetch", {"url": adress, "prompt": "x"})
    assert fel is not None and fel.startswith("Stoppat av vakten") and "WebFetch" in fel, fel


@pytest.mark.parametrize("data", WEBFETCH_FEL_TYP, ids=json.dumps)
def test_steg_149_b3_saknad_adress_stoppas(vakt, mappar, data):
    fel = _bedom_verktyg(vakt, mappar, "WebFetch", data)
    assert fel is not None and fel.startswith("Stoppat av vakten"), fel


def test_steg_149_b3_webfetch_utan_tool_input_stoppas(vakt, mappar):
    fel = _bedom_verktyg(vakt, mappar, "WebFetch", None)
    assert fel is not None and fel.startswith("Stoppat av vakten"), fel


@pytest.mark.parametrize("adress", WEBFETCH_SLAPPS)
def test_steg_149_b3_programmet_slapper_de_tva_webbplatserna(mappar, adress):
    svar = _kor_programmet(mappar, _verktyg(mappar, "WebFetch", {"url": adress, "prompt": "x"}))
    assert (svar.returncode, svar.stdout, svar.stderr) == (0, b"", b"")


@pytest.mark.parametrize("adress", WEBFETCH_STOPPAS)
def test_steg_149_b3_programmet_stoppar_allt_annat(mappar, adress):
    svar = _kor_programmet(mappar, _verktyg(mappar, "WebFetch", {"url": adress, "prompt": "x"}))
    assert svar.returncode == 2 and svar.stdout == b"", svar.stderr
    assert "WebFetch" in svar.stderr.decode("utf-8")


# Beslut 4: vakten har ingen egen tillåtelselista. Förbuden gäller, också utan scratchpad_dir (P2, saknad scratchpad).


def test_steg_149_b4_write_provas_som_forut_utan_tillatelselista(vakt, mappar):
    utanfor = mappar["hem"] + "/annat/prov.txt"
    assert _bedom_verktyg(vakt, mappar, "Write", {"file_path": utanfor, "content": "x"}) is None


@pytest.mark.parametrize("verktyg", ["Write", "Edit"])
def test_steg_149_saknad_scratchpad_andrar_inget_for_fil_verktygen(vakt, mappar, verktyg):
    for sokvag, stoppas in ((mappar["projekt"] + "/SPEC.md", False), (mappar["projekt"] + "/.git/config", True), ("/x/.GIT/config", True)):
        indata = _verktyg(mappar, verktyg, {"file_path": sokvag})
        del indata["scratchpad_dir"]
        fel = vakt.bedom(indata, mappar["projekt"], mappar["hem"], SYSTEMETS_SOKVAG)
        assert (fel is not None) is stoppas, (sokvag, fel)


# ---------------------------------------------------------------------------------------------
# Beslut 1: inställningarna.


def _installningar():
    return json.loads(INSTALLNINGAR.read_text(encoding="utf-8"))


@pytest.mark.parametrize("nyckel", NYCKLARNA)
def test_steg_149_b1_nycklarna_ar_pa_under_permissions(nyckel):
    assert _installningar()["permissions"][nyckel] is True
    assert nyckel not in _installningar()


def test_steg_149_b1_versionen_ar_2_1_314():
    assert _installningar()["requiredMinimumVersion"] == "2.1.314"


def test_steg_149_b1_inget_annat_i_filen_ar_andrat_mot_steg_18():
    # Tar man bort de två nya raderna och sätter tillbaka versionen ska det bli filen från steg 18, byte för byte.
    rader = INSTALLNINGAR.read_text(encoding="utf-8").splitlines(keepends=True)
    for nyckel in NYCKLARNA:
        rader.remove(f'    "{nyckel}": true,\n')
    rader[rader.index('  "requiredMinimumVersion": "2.1.314",\n')] = '  "requiredMinimumVersion": "2.1.305",\n'
    assert hashlib.sha256("".join(rader).encode("utf-8")).hexdigest() == INSTALLNINGARNAS_SUMMA_STEG_18


def test_steg_149_b5_provfilen_har_bara_de_tva_nycklarna():
    assert json.loads(PROVFILEN.read_text(encoding="utf-8")) == {"permissions": {nyckel: True for nyckel in NYCKLARNA}}


# ---------------------------------------------------------------------------------------------
# Beslut 5, 6 och 9: INSTALLERA.md.


def _bytet():
    return _avsnitt(BYTE_149_RUBRIK)


def _bytet_en_rad():
    return _en_rad_text(_bytet())


def test_steg_149_avsnittet_ligger_efter_steg_18_och_fore_caspers_dator():
    text = INSTALLERA.read_text(encoding="utf-8")
    assert text.index(BYTE_18_RUBRIK) < text.index(BYTE_149_RUBRIK) < text.index("## Caspers dator")


def test_steg_149_b9_versionen_kontrolleras_i_appen_och_terminalen_fore_provkorningen():
    bytet = _bytet_en_rad()
    forst = bytet.split("**2. Provkörning", 1)[0]
    assert "**1. Version" in forst and "/status" in forst and "skrivbordsappen" in forst and "2.1.314" in forst
    assert "stoppa och fråga" in forst
    kod = _kodrader(_bytet())
    assert kod.index("~/.local/bin/claude --version") < kod.index(f"~/.local/bin/claude --settings {PROVFILEN_149}")


def test_steg_149_b5_provkorningen_kommer_fore_forsta_sudo_och_summan_ar_ratt():
    kod = _kodrader(_bytet())
    forsta_sudo = next(i for i, rad in enumerate(kod) if rad.startswith("sudo "))
    assert kod.index(f"~/.local/bin/claude --settings {PROVFILEN_149}") < forsta_sudo
    assert hashlib.sha256(PROVFILEN.read_bytes()).hexdigest() in _bytet()


@pytest.mark.parametrize(
    "text",
    [
        "Vägras Read i scratchpad, eller blir något rött: stanna och fråga",
        "**77** överhoppade",
        "räknat, inte kört",
    ],
)
def test_steg_149_b5_provkorningen_sager_vad_som_galler(text):
    assert text in _bytet_en_rad().split("**3. Kontrollsummor", 1)[0]


def test_steg_149_b5_provkorningen_har_write_och_read_utanfor_och_i_scratchpad():
    avsnitt = _bytet().split("**3. Kontrollsummor", 1)[0]
    kod = _kodrader(avsnitt)
    for verktyg in ("Write", "Read"):
        assert any(verktyg in rad and "/System/kassio-prov-149-" in rad for rad in kod), verktyg
        assert any(verktyg in rad and "scratchpad" in rad for rad in kod), verktyg


@pytest.mark.parametrize(
    "summa,antal",
    [
        (hashlib.sha256(INSTALLNINGAR.read_bytes()).hexdigest(), 2),
        (hashlib.sha256((PROJEKTET / "sparr" / "kommandosparr.py").read_bytes()).hexdigest(), 2),
        (INSTALLNINGARNAS_SUMMA_STEG_18, 3),
        (VAKTENS_SUMMA_STEG_18, 3),
    ],
    ids=["nya_installningarna", "nya_vakten", "gamla_installningarna", "gamla_vakten"],
)
def test_steg_149_summorna_fore_efter_och_vid_backning(summa, antal):
    assert _bytet().count(summa) == antal


def test_steg_149_kopior_fore_vakten_forst_och_installningarna_sist():
    kod = _kodrader(_bytet())
    ordning = [
        kod.index(f"sudo cp -i {AKTIV} {SPARAD_149}"),
        kod.index(f"sudo cp -i {INSTALLERAD_VAKT_CITERAD} {SPARAD_VAKT_149}"),
        kod.index(f"sudo ditto ~/VERA/agent/sparr/kommandosparr.py {INSTALLERAD_VAKT_CITERAD}"),
        kod.index(f"sudo cp ~/VERA/agent/sparr/managed-settings.json {AKTIV}"),
    ]
    assert ordning == sorted(ordning)


def _sparrproven():
    return _bytet().split("**7. Spärrproven", 1)[1].split("**8. ", 1)[0]


def test_steg_149_b6_sparrproven_har_malen_i_beslutet():
    kod = _kodrader(_sparrproven())
    assert any("https://kassio-prov-149.invalid/" in rad for rad in kod)
    for verktyg in ("Write", "Edit", "Read", "Grep", "Glob"):
        assert any(verktyg in rad and "/System" in rad and "kassio-prov-149-" in rad for rad in kod), verktyg
    # Inget prov skriver eller läser i hemmappen eller i de andra mapparna som vakten släpper (granskning 43, P4).
    for rad in kod:
        if rad.startswith(("Använd", "Starta")):
            assert not any(plats in rad for plats in ("/Users", "~", "/tmp", "/Volumes", "/Applications", "/etc")), rad


def test_steg_149_p2_sparrproven_provar_edit_relativ_sokvag_och_underagent():
    kod = _kodrader(_sparrproven())
    assert any(rad.startswith("Använd verktyget Edit") for rad in kod)
    assert any("../../../../System/kassio-prov-149-" in rad for rad in kod)
    assert any("underagent utan isolation" in rad for rad in kod)


def test_steg_149_b6_agent_med_isolation_provas_bara_mot_programmet():
    kod = _kodrader(_bytet())
    agent = [rad for rad in kod if "isolation" in rad.lower() and "tool_name" not in rad]
    assert agent == [rad for rad in kod if "underagent utan isolation" in rad]
    assert all(PROGRAMMET_149 in rad and rad.startswith("echo '") for rad in kod if "tool_name" in rad)
    assert INSTALLERAD_VAKT in PROGRAMMET_149 and VAKTENS_PYTHON in PROGRAMMET_149 and "-I -S" in PROGRAMMET_149


def _programmets_prov():
    for rad in _kodrader(_bytet()):
        if "tool_name" in rad:
            yield rad, json.loads(rad[len("echo '"):].split("' | ", 1)[0])


def test_steg_149_b6_kommandona_mot_programmet_ger_det_texten_sager(mappar):
    # Samma JSON som i rutorna, mot vaktfilen i projektet, utan CLAUDE_PROJECT_DIR, som i Terminal.
    utfall = {}
    for _rad, indata in _programmets_prov():
        svar = _kor_programmet(mappar, indata, projektmapp=False)
        utfall[json.dumps(indata["tool_input"])] = svar.returncode
    assert utfall == {'{"isolation": "worktree"}': 2, '{"Isolation": ""}': 2, '{"prompt": "x"}': 0}


@pytest.mark.parametrize(
    "text",
    [
        "**Agenten kör inga av kommandona",
        "**Avsluta alla öppna sessioner**",
        '"Prov utanför sandlådan" igen',
        "Setting sources",
        "Enterprise managed settings (file)",
        "**Backa till förra versionen.**",
        "Ett rött eller överhoppat prov betyder att du stannar och frågar, och du backar inte på egen hand (`CLAUDE.md`).",
        "**71** överhoppade",
        "**69** om `~/.ssh` finns",
    ],
)
def test_steg_149_bytet_sager_vad_som_galler(text):
    assert text in _bytet_en_rad()


def test_steg_149_backningen_blandar_inte_ihop_stopp_och_rott_prov():
    # P8 i granskning 43 gäller bytet i steg 18, som står kvar. Här skrivs inte samma dubbla besked.
    assert "blir något i provet fel" not in _bytet_en_rad()


@pytest.mark.parametrize(
    "text",
    ['`"requiredMinimumVersion": "2.1.314"`', "En Claude Code som är äldre än 2.1.314 startar inte alls."],
)
def test_steg_149_installationen_sager_den_nya_versionen(text):
    assert text in INSTALLERA.read_text(encoding="utf-8")


def test_steg_149_bytet_i_steg_18_har_kvar_sina_summor():
    avsnitt = _avsnitt(BYTE_18_RUBRIK)
    assert avsnitt.count(INSTALLNINGARNAS_SUMMA_STEG_18) == 2 and avsnitt.count(VAKTENS_SUMMA_STEG_18) == 2


# ---------------------------------------------------------------------------------------------
# P5: SPEC 7.1.


def test_steg_149_p5_spec_sager_att_sandladan_bara_galler_skalkommandon():
    avsnitt = _spec_7_1()
    assert "Sandlådan gäller bara skalkommandon" in avsnitt
    assert "fil-verktygen utanför förbuden (ovan) och andra datorer. Det stoppas först av sandlådan" not in avsnitt


@pytest.mark.parametrize(
    "text",
    [
        "`permissions.blockWritesOutsideWorkingDirectories`",
        "`permissions.blockReadsOutsideWorkingDirectories`",
        "`Agent`",
        "`isolation`",
        "`https://code.claude.com/`",
        "`https://docs.claude.com/`",
        "(minst 2.1.314)",
    ],
)
def test_steg_149_spec_beskriver_installningarna_och_reglerna(text):
    assert text in _spec_7_1()


# ---------------------------------------------------------------------------------------------
# P4 och Öppet.


@pytest.mark.parametrize(
    "text",
    ["`/tmp`", "`/Users/Shared`", "`/Volumes`", "`/Applications`", "`~/VERA/sparrprov`", "tilläggsmappar"],
)
def test_steg_149_p4_oppet_74_raknar_upp_platserna(text):
    assert text in _post_under_oppet(74)


def test_steg_149_b7_oppet_74_star_kvar_oppen_tills_exitkriteriet_ar_uppfyllt():
    # Exitkriteriet är uppfyllt när Hugos beslut säger det (Hugos beslut 2026-11-06 om granskning 44 och installationen av steg 149,
    # beslut 3). Utan beslutet ska posten vara öppen, precis som förut. Med beslutet ska den vara stängd.
    post = " ".join(_post_under_oppet(74).split())
    if "3. Öppet 74 stängs: hålet från prov 17 är stängt av steg 149." in GRANSKNING.read_text(encoding="utf-8"):
        assert post.startswith("~~") and "**Stängd" in post and "**Öppen" not in post
    else:
        assert not post.startswith("~~") and "**Stängd" not in post and "**Öppen" in post


@pytest.mark.parametrize("text", ["tillåtelselista", "länkar", "`Agent`", "Öppen"])
def test_steg_149_b4_det_som_skjuts_upp_star_under_oppet(text):
    assert text in _post_under_oppet(79)


def test_steg_149_oppet_78_har_kvar_p8_till_p11():
    post = " ".join(_post_under_oppet(78).split())
    assert "Kvar: P8, P9, P10 och P11" in post and post.endswith("**Öppen.**")


# ---------------------------------------------------------------------------------------------
# P6: steg 149 i BYGGPLAN.md. Bara det som inte ändras när läget ändras: inga ord om status.


def _beror_pa(nummer):
    return [int(tal) for tal in re.findall(r"\d+", _byggplanens_rad(nummer).strip().strip("|").split("|")[-1], re.ASCII)]


def test_steg_149_p6_steget_beror_pa_steg_19():
    assert _beror_pa(149) == [19]


@pytest.mark.parametrize("nummer", [30, 23])
def test_steg_149_p6_senare_steg_beror_pa_steg_149(nummer):
    assert 149 in _beror_pa(nummer)


def test_steg_149_p6_steg_118_kraver_steg_149():
    assert "Steg 149 ska också vara klart före första körningen på riktiga underlag" in _byggplanens_rad(118)


@pytest.mark.parametrize("text", ["blockWritesOutsideWorkingDirectories", "blockReadsOutsideWorkingDirectories", "2.1.314", "Öppet 74"])
def test_steg_149_b1_b7_raden_sager_mellanvagen(text):
    assert text in _byggplanens_rad(149)
