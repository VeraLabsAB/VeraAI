"""Tester för inläsning av kassans Z-rapporter, Z-kontroll a–e och kontrollen av Z-serien.

Testdatan är SYNTETISK (Syntet Testbutik AB, 2025-Q1). Rätt svar står i facit.json.
"""

import csv
import io
import json
import os
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"
KASSAMAPP = DATAMAPP / "kassa"

sys.path.insert(0, str(AGENT / "scripts"))

import las_kassa  # noqa: E402  (nya namn efter granskning 3 hämtas härifrån, inne i testerna)
from las_kassa import (
    KassafilFel, ZKontrollFel, ZSerieFel, kontrollera_z_rapport, kontrollera_z_serien, ladda_kassaformat,
    las_kassafil, momsen_i_brutto, summa_per_momssats,
)

KASSAFORMAT_FIL = AGENT / "foretag" / "syntet-testbutik" / "kassaformat.json"
TESTBUTIKENS_KASSAFORMAT = ladda_kassaformat(KASSAFORMAT_FIL)
# De små Z-filerna nedan har egna, påhittade kassaregister. De läggs till i listan här, så att
# testbutikens kassaformat.json bara behöver innehålla testbutikens egen kassa. Testdatan läses
# alltid med testbutikens oförändrade format (las_alla).
SMA_FILERNAS_KASSAREGISTER = ["K-1", "K-2", "K-A", "K-B", "KASSA-Ö"]
KASSAFORMAT = {**TESTBUTIKENS_KASSAFORMAT,
               "kassaregister": TESTBUTIKENS_KASSAFORMAT["kassaregister"] + SMA_FILERNAS_KASSAREGISTER}

FALT = ["id", "rapportdatum", "znummer", "kassaregister", "postnamn", "posttyp", "sats",
        "belopp_ore", "kalla_fil", "filrad"]


def facit():
    return json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))


def kassafiler():
    return sorted(KASSAMAPP.glob("*.csv"))


def las_alla():
    return [las_kassafil(fil, TESTBUTIKENS_KASSAFORMAT) for fil in kassafiler()]


def utan(nycklar, rad):
    return {k: v for k, v in rad.items() if k not in nycklar}


# --- Små Z-filer för testerna ---

RUBRIK = "datum,z_nummer,kassaregister_id,post,momssats,belopp"


def z_rader(datum="2025-01-02", z=1001, register="K-1", forsaljning12="112.00", forsaljning25="50.00",
            moms12="12.00", moms25="10.00", kontant="100.00", kort="62.00", total="162.00"):
    """En felfri Z-rapport: 112,00 kr med 12 % (moms 12,00) och 50,00 kr med 25 % (moms 10,00)."""
    def rad(post, sats, belopp):
        return ",".join([datum, str(z), register, post, sats, belopp])
    return [
        rad("forsaljning", "12", forsaljning12),
        rad("forsaljning", "25", forsaljning25),
        rad("moms", "12", moms12),
        rad("moms", "25", moms25),
        rad("betalsatt_kontant", "", kontant),
        rad("betalsatt_kort", "", kort),
        rad("summa_brutto", "", total),
    ]


def z_fil(mapp, rader=None, namn="kassa_2025-01-02.csv", rubrik=RUBRIK, kodning="utf-8"):
    fil = mapp / namn
    text = "\n".join([rubrik] + (z_rader() if rader is None else rader)) + "\n"
    fil.write_bytes(text.encode(kodning) if isinstance(text, str) else text)
    return fil


def z_rapport(mapp, datum, z, register="K-1"):
    """Skriver och läser en felfri Z-rapport för datumet."""
    return las_kassafil(z_fil(mapp, z_rader(datum=datum, z=z, register=register), "kassa_" + datum + ".csv"),
                        KASSAFORMAT)


def test_den_lilla_felfria_filen_godkanns(tmp_path):
    # Skydd: testerna nedan ändrar en sak i den här filen. Utan ändringen ska den godkännas.
    rader = las_kassafil(z_fil(tmp_path), KASSAFORMAT)
    assert len(rader) == 7


# --- Testdatan: alla felfria dagar ---

def test_alla_felfria_dagar_klarar_de_interna_kontrollerna():
    rapporter = las_alla()
    antal = sum(manad["antal_z_rapporter"] for manad in facit()["forsaljning"].values())
    assert len(rapporter) == len(kassafiler()) == antal == 74
    for rader in rapporter:
        assert len({rad["znummer"] for rad in rader}) == 1
        assert len({rad["kalla_fil"] for rad in rader}) == 1


def test_raderna_har_ratt_falt():
    rader = las_kassafil(KASSAMAPP / "kassa_2025-01-02.csv", KASSAFORMAT)
    assert all(list(rad) == FALT for rad in rader)
    forsta = rader[0]
    assert forsta["rapportdatum"] == "2025-01-02"
    assert forsta["znummer"] == 1001
    assert forsta["kassaregister"] == "TB-KASSA-1"
    assert forsta["postnamn"] == "forsaljning"
    assert forsta["posttyp"] == "forsaljning_per_sats"
    assert forsta["sats"] == 12
    assert forsta["belopp_ore"] == 424200
    assert forsta["filrad"] == 2
    assert len(forsta["kalla_fil"]) == 64  # SHA-256 i hex
    assert rader[-1]["posttyp"] == "totalsumma" and rader[-1]["sats"] is None
    assert rader[-1]["belopp_ore"] == 596500


def test_id_ar_unika_och_stabila(tmp_path):
    rapporter = las_alla()
    alla_id = [rad["id"] for rader in rapporter for rad in rader]
    assert len(set(alla_id)) == len(alla_id)
    # Samma innehåll med Windows-1252 och CRLF ger samma id, men annan kalla_fil.
    original = KASSAMAPP / "kassa_2025-01-02.csv"
    kopia = tmp_path / original.name
    kopia.write_bytes(original.read_bytes().replace(b"\n", b"\r\n"))
    fran_original = las_kassafil(original, KASSAFORMAT)
    fran_kopia = las_kassafil(kopia, KASSAFORMAT)
    assert [r["id"] for r in fran_kopia] == [r["id"] for r in fran_original]
    assert fran_kopia[0]["kalla_fil"] != fran_original[0]["kalla_fil"]


def test_beloppen_ar_heltal_aldrig_float():
    for rader in las_alla():
        for rad in rader:
            assert type(rad["belopp_ore"]) is int
            assert rad["sats"] is None or type(rad["sats"]) is int


# --- Facit: summorna per momssats ---

def lagg_ihop(*summor_per_sats):
    """Lägger ihop flera svar från summa_per_momssats."""
    totalt = {}
    for summor in summor_per_sats:
        for sats, belopp in summor.items():
            for nyckel, ore in belopp.items():
                totalt.setdefault(sats, {}).setdefault(nyckel, 0)
                totalt[sats][nyckel] += ore
    return dict(sorted(totalt.items()))


def delar_runt_luckan(rapporter):
    """Delar rapporterna i två hela serier: före och efter den planterade luckan (Z-rapport 1011)."""
    lucka = [f for f in facit()["planterade_fel"] if f["typ"] == "lucka_i_z_serien"][0]["z_nummer"]
    fore = [rader for rader in rapporter if rader[0]["znummer"] < lucka]
    efter = [rader for rader in rapporter if rader[0]["znummer"] > lucka]
    assert fore and efter and len(fore) + len(efter) == len(rapporter)
    return fore, efter


def test_summorna_per_momssats_stammer_med_facit_per_manad_och_for_hela_perioden():
    # summa_per_momssats kör seriekontrollen först (I2). Januari har en planterad lucka (Z-rapport
    # 1011 saknas), så januari och hela kvartalet summeras i två hela delar: före och efter luckan.
    forsaljning = facit()["forsaljning"]
    rapporter = las_alla()
    per_manad = {}
    for rader in rapporter:
        per_manad.setdefault(rader[0]["rapportdatum"][:7], []).append(rader)
    assert sorted(per_manad) == sorted(forsaljning)

    kvartal = {}
    for manad, fakta in forsaljning.items():
        assert len(per_manad[manad]) == fakta["antal_z_rapporter"]
        ratt = {int(sats): summor for sats, summor in fakta["per_momssats"].items()}
        if manad == "2025-01":
            assert lagg_ihop(*(summa_per_momssats(del_) for del_ in delar_runt_luckan(per_manad[manad]))) == ratt
        else:
            assert summa_per_momssats(per_manad[manad]) == ratt
        kvartal = lagg_ihop(kvartal, ratt)

    assert lagg_ihop(*(summa_per_momssats(del_) for del_ in delar_runt_luckan(rapporter))) == kvartal
    assert kvartal[12]["brutto_ore"] == 27583500


# --- I2: summeringen kör seriekontrollen först ---

def test_i2_testdatans_januari_och_kvartal_stoppas_av_den_planterade_luckan():
    rapporter = las_alla()
    januari = [rader for rader in rapporter if rader[0]["rapportdatum"].startswith("2025-01")]
    for period in (januari, rapporter):
        with pytest.raises(ZSerieFel) as fel:
            summa_per_momssats(period)
        assert fel.value.typ == "lucka"
        assert fel.value.saknas_fran == fel.value.saknas_till == 1011


def test_i2_samma_z_rapport_inlast_tva_ganger_summeras_inte(tmp_path):
    # Granskarens fall: samma Z-rapport (112 kr med 12 %) i två mappar, den ena med kassan skriven
    # tb-kassa-1. Var för sig är filerna felfria. Den gamla koden gav 224 kr i stället för 112 kr.
    fran_a = z_rapport(tmp_path / "a", "2025-01-02", 1001, "TB-KASSA-1")
    fran_b = z_rapport(tmp_path / "b", "2025-01-02", 1001, "tb-kassa-1")
    assert summa_per_momssats([fran_a])[12]["brutto_ore"] == 11200  # skydd: en rapport ensam går bra
    with pytest.raises(ZSerieFel) as fel:
        summa_per_momssats([fran_a, fran_b])
    assert fel.value.typ == "dubblett"
    assert fel.value.kassaregister == "TB-KASSA-1"
    assert "Z-rapport 1001 finns två gånger" in str(fel.value)


def test_i2_samma_fil_tva_ganger_summeras_inte(tmp_path):
    rapport = z_rapport(tmp_path, "2025-01-02", 1001)
    with pytest.raises(ZSerieFel, match="samma fil är inläst två gånger") as fel:
        summa_per_momssats([rapport, rapport])
    assert fel.value.typ == "dubblett"


def test_i2_lucka_summeras_inte(tmp_path):
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-04", 1003)]
    with pytest.raises(ZSerieFel) as fel:
        summa_per_momssats(rapporter)
    assert fel.value.typ == "lucka"
    assert fel.value.saknas_fran == fel.value.saknas_till == 1002
    # Skydd: utan luckan summeras serien.
    hel = rapporter[:1] + [z_rapport(tmp_path, "2025-01-03", 1002)] + rapporter[1:]
    assert summa_per_momssats(hel) == {12: {"brutto_ore": 33600, "moms_ore": 3600, "netto_ore": 30000},
                                       25: {"brutto_ore": 15000, "moms_ore": 3000, "netto_ore": 12000}}


def test_i2_z_nummer_som_gar_bakat_summeras_inte(tmp_path):
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1002), z_rapport(tmp_path, "2025-01-03", 1001)]
    with pytest.raises(ZSerieFel) as fel:
        summa_per_momssats(rapporter)
    assert fel.value.typ == "ordning"


def test_i2_tom_lista_summeras_inte():
    with pytest.raises(KassafilFel, match="det finns inga Z-rapporter att kontrollera"):
        summa_per_momssats([])


# --- Det planterade felet: lucka i Z-serien ---

def test_planterat_fel_lucka_i_z_serien_upptacks_och_pekar_ut_z_nummer_och_datum():
    planterat = [f for f in facit()["planterade_fel"] if f["typ"] == "lucka_i_z_serien"][0]
    assert planterat["z_nummer"] == 1011 and planterat["datum"] == "2025-01-15"
    assert not (DATAMAPP / planterat["filnamn"]).exists()

    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(las_alla())
    assert fel.value.typ == "lucka"
    assert fel.value.kassaregister == "TB-KASSA-1"
    assert fel.value.saknas_fran == fel.value.saknas_till == planterat["z_nummer"]
    assert fel.value.antal_saknade == 1
    assert fel.value.dagar_fran == fel.value.dagar_till == planterat["datum"]
    assert fel.value.antal_dagar == 1
    assert fel.value.znummer == [1010, 1012]

    meddelande = str(fel.value)
    assert "Z-rapport 1011 saknas" in meddelande
    assert "Z-rapport 1010 (2025-01-14)" in meddelande
    assert "Z-rapport 1012 (2025-01-16)" in meddelande
    assert "Dag däremellan utan Z-rapport: 2025-01-15." in meddelande
    print("\nFelmeddelandet för Z-serien:\n" + meddelande)


def test_serien_utan_luckan_godkanns():
    # Skydd: luckan vid 1011 är det enda felet i serien. Rapporterna efter den följer på varandra.
    efter_luckan = [rader for rader in las_alla() if rader[0]["znummer"] >= 1012]
    assert len(efter_luckan) == 74 - 10
    kontrollera_z_serien(efter_luckan)


# --- Z-kontroll a–e, med en liten trasig fil i taget ---

def z_kontroll(fil, kontroll):
    with pytest.raises(ZKontrollFel) as fel:
        las_kassafil(fil, KASSAFORMAT)
    assert fel.value.kontroll == kontroll
    assert str(fel.value).startswith("Z-kontroll " + kontroll + ":")
    return str(fel.value)


def test_a_datum_i_filen_skiljer_sig_fran_filnamnet(tmp_path):
    rader = z_rader()
    rader[3] = rader[3].replace("2025-01-02", "2025-01-03")
    meddelande = z_kontroll(z_fil(tmp_path, rader), "a")
    assert "rad 5 i filen har datumet 2025-01-03" in meddelande
    assert "säger 2025-01-02" in meddelande


def test_a_hela_filen_har_ett_annat_datum_an_filnamnet(tmp_path):
    z_kontroll(z_fil(tmp_path, z_rader(datum="2025-01-03")), "a")


@pytest.mark.parametrize("namn", ["z_2025-01-02.csv", "kassa_2025-01-02.txt", "kassa_2025-1-2.csv",
                                  "kassa_2025-02-30.csv", "kassa_2025-01-02.csv.bak"])
def test_a_filnamn_som_inte_foljer_monstret_stoppas(tmp_path, namn):
    meddelande = z_kontroll(z_fil(tmp_path, namn=namn), "a")
    assert "följer inte mönstret 'kassa_ÅÅÅÅ-MM-DD.csv'" in meddelande


def test_b_olika_z_nummer_i_samma_fil(tmp_path):
    rader = z_rader()
    rader[6] = rader[6].replace(",1001,", ",1002,")
    meddelande = z_kontroll(z_fil(tmp_path, rader), "b")
    assert "rad 8 i filen har Z-nummer 1002, men rad 2 har Z-nummer 1001" in meddelande


def test_b_olika_kassaregister_i_samma_fil(tmp_path):
    rader = z_rader()
    rader[2] = rader[2].replace(",K-1,", ",K-2,")
    meddelande = z_kontroll(z_fil(tmp_path, rader), "b")
    assert "rad 4 i filen har kassaregistret 'K-2'" in meddelande


def test_c_forsaljningen_summerar_inte_till_totalsumman(tmp_path):
    # Totalsumman och betalsätten är 1,00 kr högre än försäljningen. Momsen stämmer.
    fil = z_fil(tmp_path, z_rader(kontant="101.00", total="163.00"))
    meddelande = z_kontroll(fil, "c")
    assert "summerar till 162,00 kr, men totalsumman" in meddelande
    assert "är 163,00 kr, skillnad -1,00 kr" in meddelande


def test_d_betalsatten_summerar_inte_till_totalsumman(tmp_path):
    meddelande = z_kontroll(z_fil(tmp_path, z_rader(kort="62.01")), "d")
    assert "summerar till 162,01 kr, men totalsumman" in meddelande
    assert "skillnad 0,01 kr" in meddelande


def test_d_saknat_betalsatt_med_pengar_slar_larm(tmp_path):
    rader = [rad for rad in z_rader() if "betalsatt_kort" not in rad]
    z_kontroll(z_fil(tmp_path, rader), "d")


def test_d_saknat_betalsatt_utan_pengar_godkanns(tmp_path):
    rader = [rad for rad in z_rader(kontant="162.00", kort="0") if "betalsatt_kort" not in rad]
    las_kassafil(z_fil(tmp_path, rader), KASSAFORMAT)


def test_e_momsen_ar_ett_ore_fel(tmp_path):
    meddelande = z_kontroll(z_fil(tmp_path, z_rader(moms25="10.01")), "e")
    assert "momsen för momssatsen 25 %" in meddelande
    assert "är 10,01 kr, men försäljningen 50,00 kr ger 10,00 kr" in meddelande
    assert "skillnad 0,01 kr" in meddelande


def test_e_avrundning_till_narmaste_ore(tmp_path):
    # 23,79 kr med 12 %: exakt moms 2,5489… kr. Närmaste öre är 2,55 kr; 2,54 och 2,56 är fel.
    def fil(moms):
        return z_fil(tmp_path, z_rader(forsaljning12="23.79", moms12=moms, kontant="11.79", total="73.79"))
    las_kassafil(fil("2.55"), KASSAFORMAT)
    assert "ger 2,55 kr" in z_kontroll(fil("2.54"), "e")
    z_kontroll(fil("2.56"), "e")


def test_e_moms_saknas_for_en_sats_med_forsaljning(tmp_path):
    rader = [rad for rad in z_rader() if ",moms,25," not in rad]
    assert "är 0,00 kr, men försäljningen 50,00 kr ger 10,00 kr" in z_kontroll(z_fil(tmp_path, rader), "e")


def test_e_moms_for_en_sats_utan_forsaljning(tmp_path):
    rader = z_rader() + ["2025-01-02,1001,K-1,moms,6,1.00"]
    z_kontroll(z_fil(tmp_path, rader), "e")


def test_momsen_i_brutto():
    assert momsen_i_brutto(11200, 12, "narmaste_ore") == [1200]
    assert momsen_i_brutto(-11200, 12, "narmaste_ore") == [-1200]
    assert momsen_i_brutto(2379, 12, "narmaste_ore") == [255]
    assert momsen_i_brutto(5000, 25, "narmaste_ore") == [1000]
    assert momsen_i_brutto(0, 12, "narmaste_ore") == [0]
    # 0,14 kr med 12 % ger exakt 1,5 öre. Testdatan visar inte åt vilket håll kassan avrundar
    # då, så båda godtas (se BESLUT SOM BEHÖVS).
    assert momsen_i_brutto(14, 12, "narmaste_ore") == [1, 2]
    with pytest.raises(KassafilFel, match="Okänd momsavrundning"):
        momsen_i_brutto(100, 12, "nedat")


# --- Z-serien ---

def test_serie_som_foljer_pa_varandra_godkanns(tmp_path):
    kontrollera_z_serien([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1002),
                          z_rapport(tmp_path, "2025-01-04", 1003)])


def test_serien_samma_fil_inlast_tva_ganger_ar_en_dubblett(tmp_path):
    forsta = z_rapport(tmp_path, "2025-01-02", 1001)
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([forsta, z_rapport(tmp_path, "2025-01-03", 1002), forsta])
    assert fel.value.typ == "dubblett"
    assert fel.value.znummer == [1001]
    assert "Z-rapport 1001 finns två gånger" in str(fel.value)
    assert "samma fil är inläst två gånger" in str(fel.value)


def test_serien_tva_filer_med_samma_z_nummer_ar_en_dubblett(tmp_path):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1001)])
    assert fel.value.typ == "dubblett"
    assert "daterad 2025-01-02 och 2025-01-03 (två olika filer har samma Z-nummer)" in str(fel.value)


def test_serien_lucka_med_flera_saknade_rapporter(tmp_path):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1002),
                              z_rapport(tmp_path, "2025-01-07", 1005)])
    assert fel.value.typ == "lucka"
    assert (fel.value.saknas_fran, fel.value.saknas_till, fel.value.antal_saknade) == (1003, 1004, 2)
    assert (fel.value.dagar_fran, fel.value.dagar_till, fel.value.antal_dagar) == ("2025-01-04", "2025-01-06", 3)
    assert ("Z-rapporter saknas från nummer 1003 till 1004 (2 st) mellan Z-rapport 1002 (2025-01-03)"
            in str(fel.value))
    assert "Dagar däremellan utan Z-rapport: från 2025-01-04 till 2025-01-06 (3 dagar)." in str(fel.value)


def test_serien_lucka_utan_dag_emellan(tmp_path):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1003)])
    assert (fel.value.dagar_fran, fel.value.dagar_till, fel.value.antal_dagar) == (None, None, 0)
    assert "Den saknade rapporten är från 2025-01-02 eller 2025-01-03." in str(fel.value)


def test_serien_kontrolleras_per_kassaregister(tmp_path):
    rapporter = [z_rapport(tmp_path / "a", "2025-01-02", 1, "K-A"), z_rapport(tmp_path / "b", "2025-01-02", 501, "K-B"),
                 z_rapport(tmp_path / "a", "2025-01-03", 2, "K-A"), z_rapport(tmp_path / "b", "2025-01-03", 502, "K-B")]
    kontrollera_z_serien(rapporter)
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter + [z_rapport(tmp_path / "b", "2025-01-04", 504, "K-B")])
    assert fel.value.kassaregister == "K-B"
    assert fel.value.saknas_fran == fel.value.saknas_till == 503


@pytest.fixture(autouse=True)
def _mappar(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()


def test_serien_datum_som_gar_bakat_stoppas(tmp_path):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([z_rapport(tmp_path, "2025-01-03", 1001), z_rapport(tmp_path, "2025-01-02", 1002)])
    assert fel.value.typ == "ordning"
    assert "Z-rapport 1002 är daterad 2025-01-02, men Z-rapport 1001 före den är daterad 2025-01-03" in str(fel.value)


# --- Trasiga Z-filer ---

def stoppas(fil, text):
    resultat = None
    with pytest.raises(KassafilFel) as fel:
        resultat = las_kassafil(fil, KASSAFORMAT)
    assert resultat is None
    assert not isinstance(fel.value, ZKontrollFel)  # stoppas redan vid inläsningen
    assert text in str(fel.value), str(fel.value)


def ersatt(rad_index, gammalt, nytt):
    rader = z_rader()
    assert gammalt in rader[rad_index]
    rader[rad_index] = rader[rad_index].replace(gammalt, nytt, 1)
    return rader


@pytest.mark.parametrize(
    "rader, text",
    [
        (ersatt(0, "2025-01-02", "2025-13-02"), "rad 2 i filen har ett ogiltigt datum i kolumnen 'datum'"),
        (ersatt(0, "2025-01-02", "2025-02-30"), "ogiltigt datum"),
        (ersatt(0, "2025-01-02", "20250102"), "ogiltigt datum"),
        (ersatt(1, "50.00", "50,5,0"), "har 8 fält, men rubrikraden har 6"),
        (ersatt(1, "50.00", "50.001"), "ogiltigt belopp i kolumnen 'belopp': '50.001'"),
        (ersatt(1, "50.00", "1e3"), "ogiltigt belopp"),
        (ersatt(1, "50.00", ""), "ogiltigt belopp"),
        (ersatt(1, ",1001,", ",10O1,"), "ogiltigt heltal i kolumnen 'z_nummer'"),
        (ersatt(1, ",25,", ",25.0,"), "ogiltigt heltal i kolumnen 'momssats'"),
        (ersatt(1, ",25,", ",,"), "ogiltigt heltal i kolumnen 'momssats'"),
        (ersatt(4, ",,", ",12,"), "posten 'betalsatt_kontant' ska inte ha någon momssats"),
        (ersatt(4, "betalsatt_kontant", "betalsatt_check"), "okänd post i kolumnen 'post': 'betalsatt_check'"),
        (ersatt(4, ",K-1,", ",,"), "saknar kassaregister"),
        (z_rader() + [z_rader()[2]], "rad 9 i filen: posten 'moms' för momssatsen 12 % står redan på rad 4"),
        (z_rader() + [z_rader()[6]], "posten 'summa_brutto' står redan på rad 8"),
        (z_rader()[:6], "posten 'summa_brutto' (totalsumman) saknas"),
        ([], "har en rubrikrad men inga poster"),
        (ersatt(1, "50.00", '"50.00"X'), "kan inte tolkas som CSV"),
        (ersatt(1, "K-1", '"K\n-1"'), "rad 3 i filen har en radbrytning inuti fält nummer 3"),
        (ersatt(1, "K-1", '"K\r-1"'), "radbrytning inuti fält"),
        (ersatt(1, "K-1", "K\x0b-1"), "innehåller tecknet U+000B"),
        (ersatt(1, "K-1", "K\x85-1"), "innehåller tecknet U+0085"),
        (ersatt(1, "K-1", "K\u2028-1"), "innehåller tecknet U+2028"),
        (ersatt(1, "K-1", "K\x00-1"), "rad 3 i filen innehåller ett NUL-tecken"),
    ],
    ids=[
        "manad_13", "30_februari", "datum_utan_streck", "for_manga_falt", "tre_decimaler",
        "belopp_med_exponent", "tomt_belopp", "bokstav_i_z_nummer", "sats_med_decimal", "sats_saknas",
        "sats_pa_betalsatt", "okand_post", "kassaregister_saknas", "dubbel_post", "dubbel_totalsumma",
        "totalsumma_saknas", "bara_rubrik", "skrap_efter_citerat_falt", "radbrytning_i_falt",
        "vagnretur_i_falt", "styrtecken_vt", "styrtecken_nel", "radavgransare_u2028", "nul_tecken",
    ],
)
def test_trasig_z_fil_stoppas(tmp_path, rader, text):
    stoppas(z_fil(tmp_path, rader), text)


def test_rubrikraden_maste_vara_forsta_raden(tmp_path):
    stoppas(z_fil(tmp_path, rubrik="Z-rapport\n" + RUBRIK), "första raden i filen ska vara en rubrikrad")
    stoppas(z_fil(tmp_path, rubrik="datum;z_nummer;kassaregister_id;post;momssats;belopp"),
            "ska vara en rubrikrad med kolumnerna datum, z_nummer")
    stoppas(z_fil(tmp_path, rubrik=RUBRIK + ",post"), "har kolumnen 'post' flera gånger")


def test_tom_fil_stoppas(tmp_path):
    fil = tmp_path / "kassa_2025-01-02.csv"
    fil.write_bytes(b"")
    stoppas(fil, "filen är tom")


def test_extra_kolumn_och_kolumner_i_annan_ordning_godtas(tmp_path):
    rubrik = "belopp,momssats,post,kassaregister_id,z_nummer,datum,kommentar"
    rader = [",".join(list(reversed(rad.split(","))) + ["x"]) for rad in z_rader()]
    assert utan({"kalla_fil"}, las_kassafil(z_fil(tmp_path, rader, rubrik=rubrik), KASSAFORMAT)[0]) == \
        utan({"kalla_fil"}, las_kassafil(z_fil(tmp_path / "a"), KASSAFORMAT)[0])


def test_windows_1252_ger_samma_resultat(tmp_path):
    rader = z_rader(register="KASSA-Ö")
    utf8 = las_kassafil(z_fil(tmp_path / "a", rader), KASSAFORMAT)
    cp1252 = las_kassafil(z_fil(tmp_path / "b", rader, kodning="cp1252"), KASSAFORMAT)
    assert (tmp_path / "a" / "kassa_2025-01-02.csv").read_bytes() != (tmp_path / "b" / "kassa_2025-01-02.csv").read_bytes()
    assert [utan({"kalla_fil"}, r) for r in utf8] == [utan({"kalla_fil"}, r) for r in cp1252]
    assert utf8[0]["kassaregister"] == "KASSA-Ö"


@pytest.mark.parametrize("bom", [b"\xff\xfe", b"\xfe\xff"], ids=["utf16le", "utf16be"])
def test_utf16_stoppas(tmp_path, bom):
    fil = tmp_path / "kassa_2025-01-02.csv"
    fil.write_bytes(bom + (RUBRIK + "\n").encode("utf-16-le"))
    stoppas(fil, "sparad som UTF-16")


def test_for_langt_falt_stoppas(tmp_path):
    stoppas(z_fil(tmp_path, ersatt(1, "K-1", '"' + "x" * (csv.field_size_limit() + 1) + '"')),
            "har ett fält som är längre än")


def test_saknad_fil_och_mapp_stoppas(tmp_path):
    stoppas(tmp_path / "kassa_2025-01-02.csv", "filen finns inte")
    stoppas(tmp_path, "är en mapp, inte en fil")


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="behöver filrättigheter som vanlig användare")
def test_fil_som_inte_gar_att_lasa_stoppas(tmp_path):
    fil = z_fil(tmp_path)
    fil.chmod(0)
    try:
        stoppas(fil, "går inte att läsa")
    finally:
        fil.chmod(0o600)


# --- Kassaformatet kommer från företagets konfiguration ---

ANNAT_FORMAT = {
    "anteckning": "Påhittat format för test: andra kolumnnamn, andra postnamn och semikolon.",
    "filnamn": "Z-rapport ÅÅÅÅ-MM-DD.txt",
    "kolumner": {
        "rapportdatum": "Dag",
        "znummer": "Z-nr",
        "kassaregister": "Kassa",
        "postnamn": "Typ",
        "sats": "Moms %",
        "belopp": "Summa",
    },
    "avgransare": [";", "\t"],
    "poster": {
        "forsaljning_per_sats": "SALG",
        "moms_per_sats": "MVA",
        "betalsatt": ["KONTANT", "KORT", "MOBIL"],
        "totalsumma": "TOTAL",
    },
    "momsavrundning": "narmaste_ore",
    "kassaregister": ["TB-KASSA-1", "K"],
}


def skriv_kassaformat(mapp, innehall):
    fil = mapp / "kassaformat.json"
    fil.write_text(innehall if isinstance(innehall, str) else json.dumps(innehall), encoding="utf-8")
    return fil


def test_annat_kassaformat_laser_samma_data(tmp_path):
    """Samma Z-rapport med andra kolumnnamn, andra postnamn, annat filnamn, semikolon och kolumnerna
    i omvänd ordning läses lika bra, bara genom att kassaformatet byts. Kärnan ändras inte."""
    original = KASSAMAPP / "kassa_2025-01-14.csv"
    with open(original, encoding="utf-8", newline="") as fil:
        rader = list(csv.reader(fil))
    egna = KASSAFORMAT["kolumner"]
    kolumnbyte = {egna[nyckel]: ANNAT_FORMAT["kolumner"][nyckel] for nyckel in egna}
    egna_poster, andra_poster = KASSAFORMAT["poster"], ANNAT_FORMAT["poster"]
    postbyte = dict(zip(egna_poster["betalsatt"], andra_poster["betalsatt"]))
    postbyte.update({egna_poster[typ]: andra_poster[typ] for typ in egna_poster if typ != "betalsatt"})
    postkolumn = rader[0].index(egna["postnamn"])
    for rad in rader[1:]:
        rad[postkolumn] = postbyte[rad[postkolumn]]
    text = io.StringIO()
    csv.writer(text, delimiter=";").writerows(
        [[kolumnbyte[namn] for namn in reversed(rader[0])]] + [list(reversed(rad)) for rad in rader[1:]]
    )
    kopia = tmp_path / "Z-rapport 2025-01-14.txt"
    kopia.write_bytes(text.getvalue().encode("utf-8"))
    assert kopia.read_text(encoding="utf-8").startswith("Summa;Moms %;Typ;")

    annat = ladda_kassaformat(skriv_kassaformat(tmp_path, ANNAT_FORMAT))
    fran_original = las_kassafil(original, KASSAFORMAT)
    fran_kopia = las_kassafil(kopia, annat)
    assert len(fran_kopia) == len(fran_original) == 8
    for rad_kopia, rad_original in zip(fran_kopia, fran_original):
        assert rad_kopia["postnamn"] == postbyte[rad_original["postnamn"]]
        assert utan({"id", "kalla_fil", "postnamn"}, rad_kopia) == utan({"id", "kalla_fil", "postnamn"}, rad_original)

    # Formatet styr verkligen, åt båda hållen.
    with pytest.raises(KassafilFel, match="rubrikrad med kolumnerna Dag, Z-nr"):
        las_kassafil(original, annat)
    with pytest.raises(KassafilFel, match="rubrikrad med kolumnerna datum, z_nummer"):
        las_kassafil(kopia, KASSAFORMAT)


def test_annat_kassaformat_kor_samma_kontroller(tmp_path):
    """Kontrollerna a–e använder kassaformatets postnamn, inte inbyggda namn."""
    annat = ladda_kassaformat(skriv_kassaformat(tmp_path, ANNAT_FORMAT))
    rader = ["2025-01-02;7;K;SALG;12;112.00", "2025-01-02;7;K;MVA;12;12.00", "2025-01-02;7;K;KORT;;112.00",
             "2025-01-02;7;K;TOTAL;;112.00"]
    rubrik = "Dag;Z-nr;Kassa;Typ;Moms %;Summa"
    assert len(las_kassafil(z_fil(tmp_path, rader, "Z-rapport 2025-01-02.txt", rubrik), annat)) == 4
    for index, gammalt, nytt, kontroll in [(0, "112.00", "113.00", "c"), (2, "112.00", "111.00", "d"),
                                           (1, "12.00", "12.01", "e"), (3, "112.00", "112.01", "c")]:
        andrade = list(rader)
        andrade[index] = andrade[index].replace(gammalt, nytt)
        with pytest.raises(ZKontrollFel) as fel:
            las_kassafil(z_fil(tmp_path, andrade, "Z-rapport 2025-01-02.txt", rubrik), annat)
        assert fel.value.kontroll == kontroll


def test_testbutikens_kassaformat_laddas():
    assert KASSAFORMAT["kolumner"]["znummer"] == "z_nummer"
    assert KASSAFORMAT["poster"]["totalsumma"] == "summa_brutto"
    assert KASSAFORMAT["filnamn"] == "kassa_ÅÅÅÅ-MM-DD.csv"
    assert KASSAFORMAT["momsavrundning"] == "narmaste_ore"
    assert TESTBUTIKENS_KASSAFORMAT["kassaregister"] == ["TB-KASSA-1"]
    assert "anteckning" not in KASSAFORMAT  # fri text för människor, används inte i koden


def med(**andrat):
    return {**ANNAT_FORMAT, **andrat}


def med_kolumner(**andrat):
    return med(kolumner={**ANNAT_FORMAT["kolumner"], **andrat})


def med_poster(**andrat):
    return med(poster={**ANNAT_FORMAT["poster"], **andrat})


def utan_nyckel(nyckel, data):
    return {k: v for k, v in data.items() if k != nyckel}


@pytest.mark.parametrize(
    "innehall, text",
    [
        (utan_nyckel("kolumner", ANNAT_FORMAT), "saknar nyckeln 'kolumner'"),
        (utan_nyckel("avgransare", ANNAT_FORMAT), "saknar nyckeln 'avgransare'"),
        (utan_nyckel("poster", ANNAT_FORMAT), "saknar nyckeln 'poster'"),
        (utan_nyckel("filnamn", ANNAT_FORMAT), "saknar nyckeln 'filnamn'"),
        (utan_nyckel("momsavrundning", ANNAT_FORMAT), "saknar nyckeln 'momsavrundning'"),
        (utan_nyckel("kassaregister", ANNAT_FORMAT), "saknar nyckeln 'kassaregister'"),
        (med(kassaregister=[]), "'kassaregister' ska vara en lista med minst ett kassaregister"),
        (med(kassaregister="K"), "'kassaregister' ska vara en lista"),
        (med(kassaregister=["K", ""]), "kassaregister nummer 2 får inte vara tomt"),
        (med(kassaregister=["K", None]), "kassaregister nummer 2 får inte vara tomt"),
        (med(kassaregister=["K\u200b"]), "innehåller tecknet U+200B"),
        (med(kassaregister=["\u202eK"]), "innehåller tecknet U+202E"),
        (med(kassaregister=["K\x0c"]), "innehåller tecknet U+000C"),
        (med(kassaregister=["K", "K"]), "kassaregistren 'K' och 'K' under 'kassaregister' räknas som samma"),
        (med(kassaregister=["TB-1", "tb-1"]), "kassaregistren 'TB-1' och 'tb-1' under 'kassaregister' räknas som samma"),
        (med(kassaregister=["TB-1", "TB -1"]), "räknas som samma kassaregister"),
        (med(kassaregister=["TB-1", "ＴＢ－１"]), "räknas som samma kassaregister"),
        (med(bank="X"), "okänd nyckel: 'bank'"),
        (med(kolumner=utan_nyckel("sats", ANNAT_FORMAT["kolumner"])), "saknar nyckeln 'sats'"),
        (med_kolumner(valuta="Valuta"), "okänd nyckel: 'valuta'"),
        (med_kolumner(sats="Summa"), "kolumnnamnet 'Summa' används för både 'sats' och 'belopp'"),
        (med_kolumner(sats=""), "kolumnnamnet för 'sats' får inte vara tomt"),
        (med_kolumner(sats=None), "kolumnnamnet för 'sats' får inte vara tomt"),
        (med_kolumner(sats='Moms"'), "får inte innehålla radbrytning eller citattecken"),
        (med_kolumner(sats="Moms\u200b"), "innehåller tecknet U+200B"),
        (med_kolumner(sats="Moms;%"), "ett kolumnnamn innehåller en av avgränsarna"),
        (med(kolumner=["Dag"]), "'kolumner', ska vara ett objekt"),
        (med(avgransare=[]), "minst en avgränsare"),
        (med(avgransare=";"), "ska vara en lista"),
        (med(avgransare=[" "]), "avgränsaren ' ' är ogiltig"),
        (med(avgransare=[";", ";"]), "samma avgränsare står flera gånger"),
        (med(poster=utan_nyckel("totalsumma", ANNAT_FORMAT["poster"])), "saknar nyckeln 'totalsumma'"),
        (med_poster(rabatt="RABATT"), "okänd nyckel: 'rabatt'"),
        (med_poster(totalsumma=""), "postnamnet för 'totalsumma' får inte vara tomt"),
        (med_poster(totalsumma="TOT\nAL"), "får inte innehålla radbrytning"),
        (med_poster(totalsumma="SALG"), "postnamnet 'SALG' står flera gånger"),
        (med_poster(betalsatt=["KORT", "KORT"]), "postnamnet 'KORT' står flera gånger"),
        (med_poster(betalsatt=["MVA"]), "postnamnet 'MVA' står flera gånger"),
        (med_poster(betalsatt=[]), "'betalsatt' under 'poster' ska vara en lista med minst ett postnamn"),
        (med_poster(betalsatt="KORT"), "ska vara en lista"),
        (med_poster(betalsatt=["KORT", None]), "postnamnet för betalsätt nummer 2 får inte vara tomt"),
        (med(poster=["SALG"]), "'poster', ska vara ett objekt"),
        (med(filnamn="Z.txt"), "ska innehålla 'ÅÅÅÅ-MM-DD' exakt en gång"),
        (med(filnamn="ÅÅÅÅ-MM-DD_ÅÅÅÅ-MM-DD.txt"), "exakt en gång"),
        (med(filnamn="z/ÅÅÅÅ-MM-DD.txt"), "utan mapp"),
        (med(filnamn=".ÅÅÅÅ-MM-DD.txt"), "utan punkt först"),
        (med(filnamn="ÅÅÅÅ-MM-DD\u200b.txt"), "styrtecken eller ett osynligt tecken"),
        (med(filnamn=1), "'filnamn' ska vara text"),
        (med(momsavrundning="nedat"), "'momsavrundning' är 'nedat', men kärnan känner bara till 'narmaste_ore'"),
        (med(anteckning=1), "'anteckning' ska vara text"),
        ([], "ska vara ett objekt"),
        ("{", "inte giltig JSON"),
        ('{"poster": {}, "poster": {}}', "nyckeln 'poster' står flera gånger"),
        ("[" * 100000 + "]" * 100000, "för många hakparenteser"),
    ],
    ids=[
        "saknar_kolumner", "saknar_avgransare", "saknar_poster", "saknar_filnamn", "saknar_momsavrundning",
        "h2_saknar_kassaregister", "h2_inga_kassaregister", "h2_kassaregister_ar_text", "h2_tomt_kassaregister",
        "h2_kassaregister_saknar_text", "h2_osynligt_mellanslag_i_kassaregister", "h2_vand_text_i_kassaregister",
        "h2_styrtecken_i_kassaregister", "h2_samma_kassaregister_tva_ganger", "h2_kassaregister_stor_och_liten_bokstav",
        "h2_kassaregister_blanksteg", "h2_kassaregister_fullbredd",
        "okand_nyckel", "saknar_kolumn", "okand_kolumn", "dubbla_kolumnnamn", "tomt_kolumnnamn",
        "kolumnnamn_saknar_text", "citattecken_i_kolumnnamn", "osynligt_tecken_i_kolumnnamn",
        "avgransare_i_kolumnnamn", "kolumner_ar_lista", "inga_avgransare", "avgransare_ar_text",
        "mellanslag_som_avgransare", "dubbla_avgransare", "saknar_totalsumma", "okand_posttyp",
        "tomt_postnamn", "radbrytning_i_postnamn", "samma_postnamn_tva_typer", "samma_betalsatt_tva_ganger",
        "betalsatt_med_annan_posts_namn", "inga_betalsatt", "betalsatt_ar_text", "betalsatt_saknar_text",
        "poster_ar_lista", "filnamn_utan_datum", "filnamn_med_tva_datum", "filnamn_med_mapp",
        "filnamn_dold_fil", "filnamn_osynligt_tecken", "filnamn_ar_tal", "okand_momsavrundning",
        "anteckning_ar_tal", "inte_objekt", "trasig_json", "dubbla_nycklar_i_json", "djupt_nastlad_json",
    ],
)
def test_trasigt_kassaformat_ger_kassafilfel(tmp_path, innehall, text):
    with pytest.raises(KassafilFel) as fel:
        ladda_kassaformat(skriv_kassaformat(tmp_path, innehall))
    assert text in str(fel.value)
    assert str(tmp_path / "kassaformat.json") in str(fel.value)  # meddelandet säger vilken fil


def test_saknat_kassaformat_ger_kassafilfel(tmp_path):
    with pytest.raises(KassafilFel, match="Kassaformatet saknas: filen finns inte"):
        ladda_kassaformat(tmp_path / "kassaformat.json")
    with pytest.raises(KassafilFel, match="är en mapp"):
        ladda_kassaformat(tmp_path)


def test_kassaformat_som_inte_ar_utf8_ger_kassafilfel(tmp_path):
    fil = tmp_path / "kassaformat.json"
    fil.write_bytes(json.dumps(ANNAT_FORMAT, ensure_ascii=False).replace("Dag", "Dagö").encode("cp1252"))
    with pytest.raises(KassafilFel, match="inte sparat som UTF-8"):
        ladda_kassaformat(fil)


def test_las_kassafil_kontrollerar_kassaformatet_igen(tmp_path):
    """Ett kassaformat som inte gått via ladda_kassaformat kontrolleras ändå innan det används."""
    trasigt = {**KASSAFORMAT, "poster": utan_nyckel("totalsumma", KASSAFORMAT["poster"])}
    with pytest.raises(KassafilFel, match="saknar nyckeln 'totalsumma'"):
        las_kassafil(z_fil(tmp_path), trasigt)


# --- Fall som mutationskörningen visade saknade test ---

def test_okand_teckenkodning_stoppas(tmp_path):
    # 0x81 är inte giltig UTF-8 och finns inte heller i Windows-1252.
    fil = tmp_path / "kassa_2025-01-02.csv"
    fil.write_bytes((RUBRIK + "\n").encode("utf-8") + b"\x81\n")
    stoppas(fil, "teckenkodningen är varken UTF-8 eller Windows-1252")


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="behöver filrättigheter som vanlig användare")
def test_kassaformat_som_inte_gar_att_lasa_ger_kassafilfel(tmp_path):
    fil = skriv_kassaformat(tmp_path, ANNAT_FORMAT)
    fil.chmod(0)
    try:
        with pytest.raises(KassafilFel, match="Kassaformatet går inte att läsa"):
            ladda_kassaformat(fil)
    finally:
        fil.chmod(0o600)


def test_kontrollera_z_rapport_utan_rader_stoppas():
    with pytest.raises(KassafilFel, match="det finns inga rader att kontrollera"):
        kontrollera_z_rapport([], "kassa_2025-01-02.csv", KASSAFORMAT)


def test_serien_med_tom_rapport_stoppas(tmp_path):
    with pytest.raises(KassafilFel, match="en av Z-rapporterna har inga rader"):
        kontrollera_z_serien([z_rapport(tmp_path, "2025-01-02", 1001), []])


def test_serien_med_rader_fran_olika_filer_i_samma_rapport_stoppas(tmp_path):
    blandad = z_rapport(tmp_path / "a", "2025-01-02", 1001)[:3] + z_rapport(tmp_path / "b", "2025-01-03", 1002)[3:]
    with pytest.raises(KassafilFel, match="kommer inte från en och samma Z-fil"):
        kontrollera_z_serien([blandad])


# --- Rättelser efter granskning 3 (H1, H2, H4, H6) ---

def med_znummer(rader, znummer):
    """Raderna med ett annat Z-nummer, som om de kom från las_kassafil. För tal som las_kassafil stoppar."""
    return [{**rad, "znummer": znummer} for rad in rader]


def test_h1_granssen_for_z_numret_ar_nio_siffror():
    assert las_kassa.ZNUMMER_HOGST_SIFFROR == 9


@pytest.mark.parametrize("znummer", ["1" + "0" * 9, "1" + "0" * 12, "1" + "0" * 20, "9" * 5000],
                         ids=["10_siffror", "10_upphojt_till_12", "10_upphojt_till_20", "5000_siffror"])
def test_h1_z_nummer_med_for_manga_siffror_stoppas(tmp_path, znummer):
    resultat = None
    with pytest.raises(KassafilFel) as fel:
        resultat = las_kassafil(z_fil(tmp_path, z_rader(z=znummer)), KASSAFORMAT)
    assert resultat is None
    meddelande = str(fel.value)
    assert "har ett Z-nummer med " + str(len(znummer)) + " siffror i kolumnen 'z_nummer'" in meddelande
    assert "får ha högst 9 siffror" in meddelande
    assert len(meddelande) < 500  # hela talet skrivs inte ut


def test_h1_z_nummer_med_hogst_nio_siffror_godtas(tmp_path):
    # Skydd: gränsen stoppar inte vanliga Z-nummer. Inledande nollor räknas inte som siffror.
    assert las_kassafil(z_fil(tmp_path, z_rader(z="9" * 9)), KASSAFORMAT)[0]["znummer"] == 999999999
    assert las_kassafil(z_fil(tmp_path, z_rader(z="0" * 10 + "1001")), KASSAFORMAT)[0]["znummer"] == 1001
    assert las_kassafil(z_fil(tmp_path, z_rader(z="0")), KASSAFORMAT)[0]["znummer"] == 0


def test_h1_stor_lucka_beskrivs_som_intervall_med_kort_meddelande(tmp_path):
    # 10^20 kan inte läsas in (gränsen ovan), men seriekontrollen ska ändå klara det utan att
    # räkna upp de saknade Z-numren. Den gamla koden kraschade här med OverflowError.
    stort = 10 ** 20
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1), med_znummer(z_rapport(tmp_path, "2025-01-03", 2), stort)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.typ == "lucka"
    assert (fel.value.saknas_fran, fel.value.saknas_till) == (2, stort - 1)
    assert fel.value.antal_saknade == stort - 2
    assert not hasattr(fel.value, "saknade_znummer")  # ingen lista med alla saknade nummer
    meddelande = str(fel.value)
    assert "Z-rapporter saknas från nummer 2 till " + str(stort - 1) + " (" + str(stort - 2) + " st)" in meddelande
    assert len(meddelande) < 400


def test_h1_storsta_tillatna_lucka_gar_fort(tmp_path):
    # Kördes INTE mot den gamla koden: där bygger den en lista med nästan en miljard tal och fyller
    # minnet, vilket är just felet. Den gamla koden bevisas röd av testet med 10^20 ovan.
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1), z_rapport(tmp_path, "2025-01-03", 999999999)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.antal_saknade == 999999997
    assert "Z-rapporter saknas från nummer 2 till 999999998 (999999997 st)" in str(fel.value)
    assert len(str(fel.value)) < 400


@pytest.mark.parametrize("register", ["K-9", "K-1 X", "K-1X", "K-11", "TB-KASSA-2"],
                         ids=["okant", "extra_ord", "extra_bokstav", "extra_siffra", "annan_kassa"])
def test_h2_kassaregister_som_inte_finns_i_listan_stoppas(tmp_path, register):
    stoppas(z_fil(tmp_path, z_rader(register=register)), "som inte finns bland företagets kassaregister")


def test_h2_testbutikens_format_godtar_bara_testbutikens_kassa(tmp_path):
    with pytest.raises(KassafilFel, match="'K-1' i kolumnen 'kassaregister_id', som inte finns bland"):
        las_kassafil(z_fil(tmp_path), TESTBUTIKENS_KASSAFORMAT)
    assert las_kassafil(z_fil(tmp_path, z_rader(register="TB-KASSA-1")), TESTBUTIKENS_KASSAFORMAT)


# Samma kassaregister skrivet på olika sätt. Granskarens varianter: stora och små bokstäver och
# osynligt mellanslag (U+200B). Dessutom blanksteg, hårt mellanslag, fullbreddstecken och två sätt
# att skriva "Ö" (NFC och NFD). Granskarens tredje variant, tecknet U+202E som vänder textens
# riktning, stoppas efter I3 redan vid inläsningen (test_i3_riktningstecken_i_kassaregistret_stoppar_filen
# i test_bank_och_kassa.py).
VARIANTER = {
    "sma_bokstaver": ("K-1", "k-1"),
    "osynligt_mellanslag_sist": ("K-1", "K-1\u200b"),
    "osynligt_mellanslag_inuti": ("K-1", "K\u200b-1"),
    "mellanslag_inuti": ("K-1", "K -1"),
    "hart_mellanslag_inuti": ("K-1", "K\u00a0-1"),
    "fullbredd": ("K-1", "\uff2b\uff0d\uff11"),
    "o_med_prickar_nfd": ("KASSA-Ö", "KASSA-O\u0308"),
    "o_med_prickar_sma_bokstaver": ("KASSA-Ö", "kassa-ö"),
}


@pytest.mark.parametrize("original, variant", list(VARIANTER.values()), ids=list(VARIANTER))
def test_h2_samma_z_rapport_med_annat_skrivsatt_kassaregister_ar_en_dubblett(tmp_path, original, variant):
    fran_original = z_rapport(tmp_path / "a", "2025-01-02", 1001, original)
    fran_variant = z_rapport(tmp_path / "b", "2025-01-02", 1001, variant)
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([fran_original, fran_variant])
    assert fel.value.typ == "dubblett"
    assert fel.value.kassaregister == original
    assert "Z-rapport 1001 finns två gånger" in str(fel.value)
    # Raderna får kassaregistrets namn som det står i listan, så att varianten inte blir en egen kassa.
    assert {rad["kassaregister"] for rad in fran_variant} == {original}


def test_h2_seriekontrollen_jamfor_normaliserade_namn(tmp_path):
    # Även rader som inte gått via las_kassafil jämförs efter normalisering.
    fran_original = z_rapport(tmp_path, "2025-01-02", 1001, "K-1")
    andra = [{**rad, "kassaregister": "k-1\u200b", "kalla_fil": "x"} for rad in fran_original]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([fran_original, andra])
    assert fel.value.typ == "dubblett"


def test_h2_normalisering_av_kassaregister():
    normalisera = las_kassa.normalisera_kassaregister
    assert len({normalisera(namn) for namn in ["TB-1", "tb-1", "TB-1\u200b", "\u202eTB-1", " TB - 1 ",
                                                "\uff34\uff22\uff0d\uff11"]}) == 1
    assert normalisera("KASSA-Ö") == normalisera("KASSA-O\u0308") == normalisera("kassa-ö")
    assert normalisera("TB-1 X") != normalisera("TB-1")
    assert normalisera("TB-1") != normalisera("TB-2")


def test_h4_z_nummer_som_borjar_om_vid_arsskifte_ger_tydligt_meddelande(tmp_path):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien([z_rapport(tmp_path, "2025-12-31", 1300), z_rapport(tmp_path, "2026-01-02", 1)])
    meddelande = str(fel.value)
    assert fel.value.typ == "ordning"
    assert "Z-numret går alltså ner från 1300 till 1 när datumet går fram." in meddelande
    assert "Det kan vara ett omstartat Z-nummer" in meddelande
    assert "öppen fråga (H4)" in meddelande
    assert "saknas" not in meddelande  # inte "Z-rapport 2–1299 (1298 st) saknas"


def test_h4_z_nummer_som_borjar_om_mitt_i_ger_tydligt_meddelande(tmp_path):
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1002),
                 z_rapport(tmp_path, "2025-01-04", 1), z_rapport(tmp_path, "2025-01-05", 2)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.typ == "ordning"
    assert "Z-numret går alltså ner från 1002 till 1 när datumet går fram." in str(fel.value)
    assert "omstartat Z-nummer" in str(fel.value)
    assert "saknas" not in str(fel.value)


def test_h4_z_nummer_som_borjar_om_och_upprepas_ger_tydligt_meddelande(tmp_path):
    # Börjar numret om från 1 och 1 redan finns blir det en dubblett. Meddelandet nämner omstart.
    rapporter = [z_rapport(tmp_path, "2025-01-02", 1), z_rapport(tmp_path, "2025-01-03", 2),
                 z_rapport(tmp_path, "2026-01-02", 1)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.typ == "dubblett"
    assert "daterad 2025-01-02 och 2026-01-02" in str(fel.value)
    assert "Det kan vara ett omstartat Z-nummer" in str(fel.value)


def test_h4_serien_som_fortsatter_over_arsskiftet_godkanns(tmp_path):
    # Skydd: ett Z-nummer som fortsätter över årsskiftet är rätt.
    kontrollera_z_serien([z_rapport(tmp_path, "2025-12-31", 1300), z_rapport(tmp_path, "2026-01-02", 1301)])


def test_h6_tom_lista_stoppas():
    with pytest.raises(KassafilFel, match="det finns inga Z-rapporter att kontrollera"):
        kontrollera_z_serien([])


# --- Datum långt isär i seriekontrollen (iakttagelse efter granskning 3) ---

def test_datum_langt_isar_ger_kort_meddelande(tmp_path):
    # Den gamla koden räknade upp alla 3,65 miljoner dagar mellan år 1 och år 9999 och gav ett
    # meddelande på 43,8 miljoner tecken. Nu beskrivs dagarna som ett intervall.
    rapporter = [z_rapport(tmp_path, "0001-01-01", 1), z_rapport(tmp_path, "9999-12-31", 3)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    meddelande = str(fel.value)
    assert len(meddelande) < 500
    assert fel.value.typ == "lucka"
    assert (fel.value.dagar_fran, fel.value.dagar_till, fel.value.antal_dagar) == ("0001-01-02", "9999-12-30", 3652057)
    assert "Z-rapport 2 saknas mellan Z-rapport 1 (0001-01-01) och Z-rapport 3 (9999-12-31)." in meddelande
    assert "Dagar däremellan utan Z-rapport: från 0001-01-02 till 9999-12-30 (3652057 dagar)." in meddelande


@pytest.mark.parametrize("datum", ["0001-01-01", "9999-12-31"], ids=["ar_1", "ar_9999"])
def test_lucka_samma_dag_vid_kalenderns_kant(tmp_path, datum):
    # Två rapporter samma dag vid kalenderns början eller slut. Det finns ingen dag före år 1 eller
    # efter år 9999, så uträkningen av dagarna däremellan får inte gå utanför kalendern.
    rapporter = [z_rapport(tmp_path / "a", datum, 1), z_rapport(tmp_path / "b", datum, 3)]
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.typ == "lucka"
    assert (fel.value.dagar_fran, fel.value.dagar_till, fel.value.antal_dagar) == (None, None, 0)
    assert "Den saknade rapporten är från " + datum + "." in str(fel.value)
    assert str(fel.value).count(datum) == 3  # I6: två gånger vid Z-rapporterna och en gång i sista meningen


# --- I6: luckmeddelandet säger inte samma datum två gånger och har rätt ental och plural ---

def lucka(rapporter):
    with pytest.raises(ZSerieFel) as fel:
        kontrollera_z_serien(rapporter)
    assert fel.value.typ == "lucka"
    return str(fel.value)


def test_i6_en_saknad_rapport_samma_dag(tmp_path):
    meddelande = lucka([z_rapport(tmp_path / "a", "2025-01-02", 1001), z_rapport(tmp_path / "b", "2025-01-02", 1003)])
    assert meddelande.endswith("Den saknade rapporten är från 2025-01-02. Hämta den saknade Z-rapporten från kassan.")
    assert "eller" not in meddelande


def test_i6_flera_saknade_rapporter_samma_dag(tmp_path):
    # Granskarens fall: Z-nummer 37 och 100 039, båda daterade 9999-12-31.
    meddelande = lucka([z_rapport(tmp_path / "a", "9999-12-31", 37), z_rapport(tmp_path / "b", "9999-12-31", 100039)])
    assert "Z-rapporter saknas från nummer 38 till 100038 (100001 st)" in meddelande
    assert "De saknade rapporterna är från 9999-12-31." in meddelande
    assert "Den saknade rapporten" not in meddelande
    assert "9999-12-31 eller 9999-12-31" not in meddelande


def test_i6_flera_saknade_rapporter_dagar_i_rad(tmp_path):
    meddelande = lucka([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1004)])
    assert "Z-rapporter saknas från nummer 1002 till 1003 (2 st)" in meddelande
    assert "De saknade rapporterna är från 2025-01-02, från 2025-01-03 eller från båda dagarna." in meddelande
    assert "Den saknade rapporten" not in meddelande


def test_i6_en_dag_daremellan_ar_ental(tmp_path):
    meddelande = lucka([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-04", 1003)])
    assert "Dag däremellan utan Z-rapport: 2025-01-03." in meddelande
    assert "Dagar" not in meddelande


def test_i6_en_saknad_rapport_dagar_i_rad_ar_som_forut(tmp_path):
    # Skydd: två olika datum och en saknad rapport ger samma mening som förut.
    meddelande = lucka([z_rapport(tmp_path, "2025-01-02", 1001), z_rapport(tmp_path, "2025-01-03", 1003)])
    assert "Den saknade rapporten är från 2025-01-02 eller 2025-01-03." in meddelande
