"""Hugos beslut 2026-10-29 om Q2 (GRANSKNING.md, "Hugos beslut 2026-10-29 om Q2–Q4").

Ägaren ska kännas igen även när banken skriver namnet utan accenter, till exempel "ASA OBERG" för
"Åsa Öberg", och omvänt. Det gäller bara ägaruppslaget: regelbokens uppslag för bankrader
(Regelbok.ar_bankrad_mot_agare_eller_narstaende), som matchningen och konteringsförslagen använder,
och kontrollen att ingen regel i matchningsformatet nämner en ägare. Den gemensamma jämförelsen
(normalisera_for_jamforelse), dublettkontrollen K4 och matchningen mot motparter ändras inte.

Testen för Q2 var röda före rättelsen. Skyddstesten var gröna både före och efter. Allt skrivs i
testets tillfälliga mapp.

Q2b (samma avsnitt i GRANSKNING.md): accenter spelar heller ingen roll i de andra två ägarkontrollerna,
Regelbok.ar_agare_eller_narstaende (en motpart i ett underlag) och kontrollen att en regel för ägarens
underlag har nivå D. Dublettkontrollen i ägarlistan och kontrollen av tvetydiga regler ändras inte.
"""

import hashlib
import itertools
import json
import sys
from pathlib import Path

import pytest

from test_las_regelbok import (  # noqa: F401 (konfiguration är en fixture)
    bok, konfiguration, las, med_agare, regel, stoppas, underlag as galler_for_underlag,
)
from test_matcha_bank import (  # noqa: F401 (kvartalet är en fixture)
    FORMAT, REGELBOK, bankrader, kvartalet, matcha, period, regelbok_for, sammanfattning, tomt, underlag,
)

AGENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AGENT / "scripts"))

import normalisering  # noqa: E402
from las_regelbok import RegelbokFel  # noqa: E402
from matcha_bank import matcha_period  # noqa: E402

# Accenter som egna tecken byggs med chr(), så att det syns vilket tecken som används.
RING = chr(0x030A)        # kombinerande ring, som i Å
TREMA = chr(0x0308)       # kombinerande trema, som i Ä och Ö
AKUT = chr(0x0301)        # kombinerande akut accent, som i É
FRISTAENDE_TREMA = chr(0x00A8)  # ¨ som eget tecken, inte kombinerande


def pekas_ut(mapp, konfiguration, agare, beskrivning, referens=""):  # noqa: F811
    """True om regelbokens uppslag pekar ut bankraden som en rad mot en ägare eller närstående i agare."""
    regelbok = las(mapp, bok(agare_och_narstaende=list(agare)), konfiguration)
    return regelbok.ar_bankrad_mot_agare_eller_narstaende({"beskrivning": beskrivning, "referens": referens})


# --- Q2: ägaren känns igen utan accenter (röda före rättelsen) ---

@pytest.mark.parametrize("agare, beskrivning, referens", [
    # Accenter i ägarlistan, inga i banken.
    ("Åsa Öberg", "UTTAG ASA OBERG", ""),
    ("Åsa Öberg", "", "ASA OBERG"),
    ("Åsa Öberg", "UTTAG ASA OBERG/LAN", ""),
    ("René", "UTTAG RENE", ""),
    ("Ärlig Ägare", "LON ARLIG AGARE", ""),
    # Omvänt: inga accenter i listan, accenter i banken.
    ("Asa Oberg", "UTTAG ÅSA ÖBERG", ""),
    ("Rene", "UTTAG RENÉ", ""),
    # Accenter som egna tecken: en bokstav och sedan ett separat accenttecken.
    ("Asa Oberg", "UTTAG A" + RING + "SA O" + TREMA + "BERG", ""),
    ("Rene", "UTTAG RENE" + AKUT, ""),
    ("Rene" + AKUT, "UTTAG RENE", ""),
    ("A" + RING + "sa O" + TREMA + "berg", "UTTAG ASA OBERG", ""),
    # Ett fristående accenttecken efter bokstaven (N4).
    ("Asa Oberg", "UTTAG ASA O" + FRISTAENDE_TREMA + "BERG", ""),
])
def test_q2_agaren_kanns_igen_utan_accenter(tmp_path, konfiguration, agare, beskrivning, referens):  # noqa: F811
    assert pekas_ut(tmp_path, konfiguration, [agare], beskrivning, referens), (agare, beskrivning, referens)


def test_q2_matchningen_marker_raden_och_undantaget_galler_inte(tmp_path):
    # Regeln "uttag" i matchningsformatet undantar alla uttag från underlag. Raden mot ägaren "Åsa Öberg",
    # som banken skriver utan accenter, ska inte undantas: den kräver underlag och märks "kräver mänsklig
    # bedömning". Rad 2 är mot någon annan, så regeln prövas verkligen.
    format_ = {**FORMAT, "kraver_inte_underlag": FORMAT["kraver_inte_underlag"] + [
        {"namn": "uttag", "riktning": "ut", "beskrivning_borjar_med": "UTTAG", "hogst_belopp_ore": 100000}]}
    rader = bankrader(tmp_path, ("X-1", "UTTAG ASA OBERG", -50000, "2025-04-01"),
                      ("X-2", "UTTAG ANNAN PERSON", -50000, "2025-04-01"))
    regelbok = regelbok_for(format_, agare=("Åsa Öberg",))
    assert regelbok.matchningsregel_for_bankrad(rader.rader[0]) is None
    resultat = matcha(rader, period(tmp_path), "2025-04-30", format_=format_, agare=("Åsa Öberg",))
    assert sammanfattning(resultat) == tomt(arenden=[(1, "saknat underlag", ())], kraver_inte=[(2, "uttag")])
    assert resultat.arenden[0]["kraver_mansklig_bedomning"] is True
    assert resultat.kraver_inte_underlag[0]["kraver_mansklig_bedomning"] is False
    # Med exakt ett underlag blir raden ett ärende "kräver mänsklig bedömning", aldrig en matchning.
    underlagen = period(tmp_path, underlag(motpart="ASA OBERG", fakturanummer="X-1", belopp_ore=50000,
                                           datum="2025-04-01"))
    resultat = matcha(rader, underlagen, "2025-04-30", format_=format_, agare=("Åsa Öberg",))
    assert sammanfattning(resultat) == tomt(arenden=[(1, "kräver mänsklig bedömning", ("U-1",))],
                                            oavstamda=["U-1"], kraver_inte=[(2, "uttag")])
    assert resultat.arenden[0]["kraver_mansklig_bedomning"] is True


@pytest.mark.parametrize("agare, text", [
    ("Åsa Öberg", "UTTAG ASA OBERG"),
    ("Asa Oberg", "UTTAG ÅSA ÖBERG"),
    ("René", "UTTAG RENE"),
    ("Rene", "UTTAG RENE" + AKUT),
])
def test_q2_en_matchningsregel_som_namner_agaren_utan_accenter_stoppar_regelboken(agare, text):
    # Kontrollen i las_regelbok._ingen_matchningsregel_for_agare: regeln skulle annars undanta ägarens
    # bankrader från underlag.
    format_ = {**FORMAT, "kraver_inte_underlag": FORMAT["kraver_inte_underlag"] + [
        {"namn": "agaruttag", "riktning": "ut", "beskrivning_borjar_med": text, "hogst_belopp_ore": 100000}]}
    with pytest.raises(RegelbokFel, match="får aldrig undanta en bankrad mot en ägare"):
        regelbok_for(format_, agare=(agare,))
    # Skydd: med en annan ägare godtas samma regel.
    assert regelbok_for(format_, agare=("AGARE-9",)) is not None


# --- Q2b: ägaren känns igen utan accenter också i underlagen (röda före rättelsen) ---

# (namn i ägarlistan, motpart i underlaget eller i regeln). Båda riktningarna, och accenter som egna tecken.
UTAN_ACCENTER = [
    ("Åsa Öberg", "Asa Oberg"),
    ("Åsa Öberg", "ASA OBERG"),
    ("Asa Oberg", "Åsa Öberg"),
    ("Asa Oberg", "ÅSA ÖBERG"),
    ("René", "Rene"),
    ("Rene", "René"),
    ("Ärlig Ägare", "arlig agare"),
    ("Asa Oberg", "A" + RING + "sa O" + TREMA + "berg"),
    ("A" + RING + "sa O" + TREMA + "berg", "Asa Oberg"),
    ("Rene", "Rene" + AKUT),
    ("Rene" + AKUT, "Rene"),
    ("Åsa Öberg", "A" + RING + "sa Oberg"),
]


@pytest.mark.parametrize("agare, motpart", UTAN_ACCENTER)
def test_q2b_ar_agare_eller_narstaende_bortser_fran_accenter(tmp_path, konfiguration, agare, motpart):  # noqa: F811
    regelbok = las(tmp_path, bok(agare_och_narstaende=[agare]), konfiguration)
    assert regelbok.ar_agare_eller_narstaende(motpart), (agare, motpart)


@pytest.mark.parametrize("agare, motpart", UTAN_ACCENTER)
def test_q2b_galler_aven_narstaende_langre_ned_i_listan(tmp_path, konfiguration, agare, motpart):  # noqa: F811
    # Ägare och närstående står i samma lista. Den närstående står här efter en annan ägare.
    regelbok = las(tmp_path, bok(agare_och_narstaende=["AGARE-X", agare]), konfiguration)
    assert regelbok.ar_agare_eller_narstaende(motpart), (agare, motpart)


def test_q2b_ett_fristaende_accenttecken_i_underlaget(tmp_path, konfiguration):  # noqa: F811
    # Motparten i ett underlag kan ha vilka tecken som helst, också ett fristående "¨" efter bokstaven (N4).
    regelbok = las(tmp_path, bok(agare_och_narstaende=["Asa Oberg"]), konfiguration)
    assert regelbok.ar_agare_eller_narstaende("Asa O" + FRISTAENDE_TREMA + "berg")
    regelbok = las(tmp_path, bok(agare_och_narstaende=["Åsa Öberg"]), konfiguration)
    assert regelbok.ar_agare_eller_narstaende("Asa O" + FRISTAENDE_TREMA + "berg")


@pytest.mark.parametrize("niva", ["A", "B", "C"])
@pytest.mark.parametrize("agare, motpart", UTAN_ACCENTER)
def test_q2b_regel_for_agaren_utan_accenter_ska_ha_niva_d(tmp_path, konfiguration, agare, motpart, niva):  # noqa: F811
    data = med_agare([agare], regel("R-6", galler_for_underlag(motpart=motpart), {"grupp_a": "9001"}, niva=niva))
    stoppas(tmp_path, data, konfiguration, "regel nummer 6 (R-6) gäller motparten " + repr(motpart),
            "som står i 'agare_och_narstaende' (som " + repr(agare) + ")", "har nivå " + repr(niva),
            "ska alltid ha nivå D")


@pytest.mark.parametrize("agare, motpart", UTAN_ACCENTER)
def test_q2b_regel_for_narstaende_utan_accenter_ska_ha_niva_d(tmp_path, konfiguration, agare, motpart):  # noqa: F811
    data = med_agare(["AGARE-X", agare], regel("R-6", galler_for_underlag("kvitto", motpart), {"grupp_a": "9001"}))
    stoppas(tmp_path, data, konfiguration, "gäller motparten " + repr(motpart), "(som " + repr(agare) + ")",
            "ska alltid ha nivå D")


# --- Skyddstest (gröna både före och efter rättelsen) ---

@pytest.mark.parametrize("agare, motpart", UTAN_ACCENTER)
def test_skydd_regel_for_agaren_utan_accenter_med_niva_d_godtas(tmp_path, konfiguration, agare, motpart):  # noqa: F811
    data = med_agare([agare], regel("R-6", galler_for_underlag(motpart=motpart), {"grupp_a": "9001"}, niva="D"))
    assert las(tmp_path, data, konfiguration).regler[-1]["niva"] == "D"


def test_skydd_andra_motparter_ar_inte_agare(tmp_path, konfiguration):  # noqa: F811
    regelbok = las(tmp_path, bok(agare_och_narstaende=["Åsa Öberg", "AGARE-1"]), konfiguration)
    for motpart in ("Asa Obergsson", "Asa", "Oberg", "Åsa Öberg AB", "AGARE-10", "AGARE-1X", "AGARE 2", "MOTPART-A"):
        assert not regelbok.ar_agare_eller_narstaende(motpart), motpart
    # En regel för en sådan motpart får ha vilken nivå som helst.
    data = med_agare(["Åsa Öberg"], regel("R-6", galler_for_underlag(motpart="Asa Obergsson"), {"grupp_a": "9001"},
                                          niva="A"))
    assert las(tmp_path, data, konfiguration).regler[-1]["niva"] == "A"


def test_skydd_ar_agare_eller_narstaende_hittar_aldrig_farre_an_forut(tmp_path, konfiguration):  # noqa: F811
    # Varje ägarnamn och varje motpart av tecknen nedan: där den gamla jämförelsen (normalisera_for_jamforelse på
    # båda sidor) säger ja, säger uppslaget också ja. Namn som regelboken stoppar hoppas över.
    tecken = ["a", "Å", "é", "0", "-", " ", "e" + AKUT, "A" + RING, FRISTAENDE_TREMA, chr(0x200B)]
    namn = ["".join(delar) for langd in (1, 2) for delar in itertools.product(tecken, repeat=langd)]
    motparter = ["".join(delar) for langd in (1, 2, 3) for delar in itertools.product(tecken, repeat=langd)]
    provade, lika = 0, 0
    for nummer, ett in enumerate(namn):
        mapp = tmp_path / str(nummer)
        mapp.mkdir()
        try:
            regelbok = las(mapp, bok(agare_och_narstaende=[ett]), konfiguration)
        except RegelbokFel:
            continue
        provade += 1
        for motpart in motparter:
            if normalisering.normalisera_for_jamforelse(motpart) == normalisering.normalisera_for_jamforelse(ett):
                lika += 1
                assert regelbok.ar_agare_eller_narstaende(motpart), (ett, motpart)
    assert provade > 20 and lika > 100, (provade, lika)


def test_skydd_dubbletter_i_agarlistan_som_forut(tmp_path, konfiguration):  # noqa: F811
    # Dublettkontrollen i ägarlistan bryr sig fortfarande om accenter: "Åsa Öberg" och "Asa Oberg" får stå
    # bredvid varandra, men inte "Åsa Öberg" och "ÅSA ÖBERG".
    regelbok = las(tmp_path, bok(agare_och_narstaende=["Åsa Öberg", "Asa Oberg"]), konfiguration)
    assert regelbok.agare_och_narstaende == ["Åsa Öberg", "Asa Oberg"]
    for andra in ("ÅSA ÖBERG", "åsa öberg", "A" + RING + "sa O" + TREMA + "berg"):
        stoppas(tmp_path, bok(agare_och_narstaende=["Åsa Öberg", andra]), konfiguration,
                repr(andra) + " står flera gånger i 'agare_och_narstaende' (som 'Åsa Öberg')")


def test_skydd_tvetydiga_regler_som_forut(tmp_path, konfiguration):  # noqa: F811
    # Två regler för "Café AB" och "Cafe AB" är olika regler, som förut. Uppslaget för den ena hittar inte den andra.
    data = bok(regler=bok()["regler"] + [
        regel("R-6", galler_for_underlag(motpart="Café AB"), {"grupp_a": "9001"}),
        regel("R-7", galler_for_underlag(motpart="Cafe AB"), {"grupp_a": "9002"}),
    ])
    regelbok = las(tmp_path, data, konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "CAFÉ AB", "2025-01-01")["id"] == "R-6"
    assert regelbok.regel_for_underlag("leverantorsfaktura", "CAFE AB", "2025-01-01")["id"] == "R-7"
    regelbok = las(tmp_path, bok(regler=bok()["regler"] + [regel("R-6", galler_for_underlag(motpart="Café AB"),
                                                                 {"grupp_a": "9001"})]), konfiguration)
    assert regelbok.regel_for_underlag("leverantorsfaktura", "Cafe AB", "2025-01-01") is None
    # Samma stavning med andra stora och små bokstäver är tvetydig, som förut.
    data = bok(regler=bok()["regler"] + [
        regel("R-6", galler_for_underlag(motpart="Café AB"), {"grupp_a": "9001"}),
        regel("R-7", galler_for_underlag(motpart="CAFÉ AB"), {"grupp_a": "9002"}),
    ])
    stoppas(tmp_path, data, konfiguration, "reglerna 'R-6' och 'R-7' kan båda passa samma sak")

def test_skydd_agare_1_hittas_inte_i_agare_10(tmp_path, konfiguration):  # noqa: F811
    for beskrivning in ("UTTAG AGARE-10", "UTTAG AGARE-1X", "UTTAGAGARE-1", "KOP AGARE-12 AB"):
        assert not pekas_ut(tmp_path, konfiguration, ["AGARE-1"], beskrivning), beskrivning
    assert pekas_ut(tmp_path, konfiguration, ["AGARE-1"], "UTTAG AGARE-1")
    # Samma sak utan accenter: "Åsa Öberg" står inte i "ASA OBERGSSON" eller "ASA OBERG2". ("ASAOBERG" pekas
    # däremot ut, som "Anna Nilsson" i "ANNANILSSON" förut: orden i följd sätts ihop.)
    for beskrivning in ("UTTAG ASA OBERGSSON", "UTTAG ASA OBERG2", "UTTAG ASA OBER"):
        assert not pekas_ut(tmp_path, konfiguration, ["Åsa Öberg"], beskrivning), beskrivning


def test_q2_uppslaget_utan_accenter_hittar_aldrig_farre_an_forut(tmp_path, konfiguration):  # noqa: F811
    # Varje namn med en bokstav eller siffra, och varje text, av tecknen nedan: där den gamla sökningen hittar
    # namnet hittas det också utan accenter. Ett namn utan bokstäver och siffror (till exempel bara "¨", som
    # utan accenter blir tomt) kan aldrig stå i ägarlistan: regelboken stoppar det. Funktionen finns först
    # efter rättelsen.
    tecken = ["a", "Å", "é", "0", "-", ".", " ", "e" + AKUT, FRISTAENDE_TREMA]
    namn = ["".join(delar) for langd in (1, 2) for delar in itertools.product(tecken, repeat=langd)]
    texter = ["X " + "".join(delar) for langd in (1, 2, 3) for delar in itertools.product(tecken, repeat=langd)]
    hittade, stoppade = 0, 0
    for ett in namn:
        if not any(del_.isalnum() for del_ in ett):
            with pytest.raises(RegelbokFel):
                las(tmp_path, bok(agare_och_narstaende=[ett]), konfiguration)
            stoppade += 1
            continue
        for text in texter:
            if normalisering.star_som_hela_ord(ett, text):
                hittade += 1
                assert normalisering.star_som_hela_ord_utan_accenter(ett, text), (ett, text)
    assert hittade > 100 and stoppade > 10, (hittade, stoppade)


def test_skydd_normalisera_for_jamforelse_ar_oforandrad():
    # Exakt samma svar som före Q2: accenterna står kvar.
    forvantat = {"Åsa Öberg": "åsaöberg", "ÅSA ÖBERG": "åsaöberg", "Asa Oberg": "asaoberg", "René": "rené",
                 "Ärlig Ägare": "ärligägare", "Café Ölund-AB": "caféölund-ab", "e" + AKUT: "é",
                 "A" + RING: "å", "O" + FRISTAENDE_TREMA: "ö"}
    for text, svar in forvantat.items():
        assert normalisering.normalisera_for_jamforelse(text) == svar, text
    assert normalisering.sokform_for_namn("Åsa Öberg") == "åsaöberg"
    # Den gemensamma sökningen efter hela ord bryr sig fortfarande om accenter.
    assert not normalisering.star_som_hela_ord("Åsa Öberg", "UTTAG ASA OBERG")
    assert not normalisering.star_som_hela_ord("CAFÉ", "KOP CAFE")


def test_skydd_motparter_som_bara_skiljer_sig_i_accenter_matchas_inte(tmp_path):
    # Matchningen mot motparter: underlaget från "LEV-Ä" passar inte bankraden "KOP LEV-A", och omvänt.
    for nummer, (motpart, beskrivning) in enumerate((("LEV-Ä", "LEV-A"), ("LEV-A", "LEV-Ä"), ("Café AB", "CAFE AB"))):
        mapp = tmp_path / str(nummer)
        mapp.mkdir()
        rader = bankrader(mapp, ("F-1", beskrivning, -12500, "2025-01-20"))
        resultat = matcha(rader, period(mapp, underlag(motpart=motpart)), "2025-01-21")
        assert sammanfattning(resultat) == tomt(oavstamda=["U-1"], vantande=[(1, "2025-01-27")]), motpart
    # Skydd: med samma stavning matchas de.
    rader = bankrader(tmp_path, ("F-1", "LEV-Ä", -12500, "2025-01-20"))
    assert sammanfattning(matcha(rader, period(tmp_path, underlag(motpart="LEV-Ä")))) == tomt(matchningar=[(1, "U-1")])


def test_skydd_k4_motparter_som_bara_skiljer_sig_i_accenter_ar_olika(tmp_path):
    # Samma fakturanummer, belopp och datum, men motparten "Café AB" och "Cafe AB". Det är inte en dublett
    # (K4), utan en möjlig dublett (K4c), och båda underlagen behålls.
    underlagen = period(tmp_path, underlag(id="U-1", motpart="Café AB"), underlag(id="U-2", motpart="Cafe AB"))
    assert [post["id"] for post in underlagen.underlag] == ["U-1", "U-2"]
    assert [(arende["kontroll"], arende["id"], arende["jamfort_med"]) for arende in underlagen.arenden] == [
        ("K4c", "U-2", "U-1")]
    # Skydd: med samma stavning är det en dublett.
    mapp = tmp_path / "samma"
    mapp.mkdir()
    lika = period(mapp, underlag(id="U-1", motpart="Café AB"), underlag(id="U-2", motpart="CAFÉ AB"))
    assert [post["id"] for post in lika.underlag] == ["U-1"]
    assert [(arende["kontroll"], arende["id"]) for arende in lika.arenden] == [("K4", "U-2")]


def _fingeravtryck(resultat, regelbok, bankperiod):
    """SHA-256 av hela matchningens resultat och regelbokens uppslag för varje bankrad, som JSON."""
    data = {
        "matchningar": [(m["bankrad"]["id"], m["underlag"]["id"], m["kraver_mansklig_bedomning"])
                        for m in resultat.matchningar],
        "arenden": [(a["bankrad"]["id"], a["kontroll"], a["typ"], list(a["kandidater"]), a["kraver_mansklig_bedomning"])
                    for a in resultat.arenden],
        "oavstamda": [post["id"] for post in resultat.oavstamda_underlag],
        "kraver_inte": [(post["bankrad"]["id"], post["regel"], post["kraver_mansklig_bedomning"])
                        for post in resultat.kraver_inte_underlag],
        "vantande": [(post["bankrad"]["id"], post["arende_efter"], post["kraver_mansklig_bedomning"])
                     for post in resultat.vantande],
        "uppslag": [(rad["id"], regelbok.ar_bankrad_mot_agare_eller_narstaende(rad),
                     regelbok.matchningsregel_for_bankrad(rad)) for rad in bankperiod.rader],
    }
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


# Räknat med koden före Q2 (f61eb4e), för bedömningsdagarna nedan. Båda dagarna ger samma resultat: den
# planterade raden utan underlag (18 februari) är redan ett ärende den 31 mars.
TESTBUTIKENS_FINGERAVTRYCK = {
    "2025-03-31": "5e77f8abb81158b04cef80541c9d890a9b5b804d085d1cf726ff67bfe9d54efd",
    "2025-04-30": "5e77f8abb81158b04cef80541c9d890a9b5b804d085d1cf726ff67bfe9d54efd",
}


def test_skydd_testbutikens_korning_ger_samma_resultat_som_fore_q2(kvartalet):  # noqa: F811
    for dag, forvantat in TESTBUTIKENS_FINGERAVTRYCK.items():
        resultat = matcha_period(kvartalet["bankperiod"], kvartalet["period"], REGELBOK, dag)
        avtryck = _fingeravtryck(resultat, REGELBOK, kvartalet["bankperiod"])
        assert avtryck == forvantat, (dag, avtryck)
    # Ingen av testbutikens bankrader är mot ägaren, varken före eller efter.
    assert not any(REGELBOK.ar_bankrad_mot_agare_eller_narstaende(rad) for rad in kvartalet["rader"])
