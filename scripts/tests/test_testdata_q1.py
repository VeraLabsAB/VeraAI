"""Tester för den SYNTETISKA testdatan för Syntet Testbutik AB, 2025-Q1.

Testerna visar att generatorn är deterministisk, att bankfilernas saldokedja och Z-rapporterna
går ihop, och att exakt de planterade felen i facit.json finns i filerna och inga andra.
"""

import csv
import datetime as dt
import json
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
DATAMAPP = AGENT / "testdata" / "syntet-testbutik" / "2025-Q1"

sys.path.insert(0, str(AGENT / "scripts"))
sys.path.insert(0, str(AGENT / "testdata" / "generator"))

from belopp import tolka_belopp
import generera_syntet_testbutik_q1 as generator

MANADER = ["2025-01", "2025-02", "2025-03"]
MOMSSATS_PER_KVITTOMOTPART = {"BUTIK-FORBRUKNING": 25, "BUTIK-STAD": 25, "RESTAURANG-1": 12}


# --- Inläsning ---

def facit():
    return json.loads((DATAMAPP / "facit.json").read_text(encoding="utf-8"))


def las_csv(sokvag):
    with open(sokvag, encoding="utf-8", newline="") as fil:
        return list(csv.DictReader(fil))


def bankrader(manad):
    rader = las_csv(DATAMAPP / ("bank_" + manad + ".csv"))
    for rad in rader:
        rad["belopp_ore"] = tolka_belopp(rad["Belopp"])
        rad["saldo_ore"] = tolka_belopp(rad["Bokfört saldo"])
    return rader


def kassafiler():
    return sorted((DATAMAPP / "kassa").glob("kassa_*.csv"))


def underlag():
    return [json.loads(fil.read_text(encoding="utf-8")) for fil in sorted((DATAMAPP / "underlag").glob("*.json"))]


def planterat(typ):
    traffar = [fel for fel in facit()["planterade_fel"] if fel["typ"] == typ]
    assert len(traffar) == 1, typ
    return traffar[0]


def alla_filer(mapp):
    return {str(fil.relative_to(mapp)): fil.read_bytes() for fil in sorted(mapp.rglob("*")) if fil.is_file()}


# --- (a) Samma körning ger samma filer ---

def test_generatorn_ger_identiska_filer_vid_tva_korningar(tmp_path):
    generator.generera(tmp_path / "forsta")
    generator.generera(tmp_path / "andra")
    forsta = alla_filer(tmp_path / "forsta")
    assert len(forsta) > 0
    assert forsta == alla_filer(tmp_path / "andra")


def test_incheckade_filer_ar_exakt_generatorns_utdata(tmp_path):
    generator.generera(tmp_path / "ny")
    assert alla_filer(DATAMAPP) == alla_filer(tmp_path / "ny")


# --- (b) Saldokedjan ---

def test_saldokedjan_gar_ihop_utom_pa_den_planterade_raden_i_mars():
    fel = planterat("brott_i_saldokedjan")
    avvikelser = []
    for manad in MANADER:
        rader = bankrader(manad)
        saldo = facit()["bank"][manad]["ingaende_saldo_ore"]
        for rad in rader:
            saldo += rad["belopp_ore"]
            if rad["saldo_ore"] != saldo:
                avvikelser.append(("bank_" + manad + ".csv", int(rad["Radnummer"]), rad["saldo_ore"] - saldo))
        assert saldo == facit()["bank"][manad]["utgaende_saldo_ore"]

    assert avvikelser == [(fel["filnamn"], fel["rad"], fel["visat_saldo_ore"] - fel["ratt_saldo_ore"])]


def test_ingaende_saldo_ar_foregaende_manads_utgaende():
    bank = facit()["bank"]
    assert bank["2025-01"]["ingaende_saldo_ore"] == generator.INGAENDE_SALDO_ORE
    for foregaende, manad in zip(MANADER, MANADER[1:]):
        assert bank[manad]["ingaende_saldo_ore"] == bank[foregaende]["utgaende_saldo_ore"]
        # Samma sak sett i filerna: första radens saldo minus belopp är förra filens sista saldo.
        forsta = bankrader(manad)[0]
        assert forsta["saldo_ore"] - forsta["belopp_ore"] == bankrader(foregaende)[-1]["saldo_ore"]


def test_bankfilerna_har_ratt_kolumner_radnummer_och_manad():
    for manad in MANADER:
        rader = bankrader(manad)
        assert list(rader[0])[:7] == generator.BANKKOLUMNER
        assert [int(rad["Radnummer"]) for rad in rader] == list(range(1, len(rader) + 1))
        assert len(rader) == facit()["bank"][manad]["antal_rader"]
        assert all(rad["Bokföringsdag"].startswith(manad) for rad in rader)
        assert all(rad["Transaktionsdag"] <= rad["Bokföringsdag"] for rad in rader)


# --- (c) Z-rapporterna ---

def test_varje_z_fil_ar_intern_konsekvent():
    for fil in kassafiler():
        rader = las_csv(fil)
        assert list(rader[0]) == generator.KASSAKOLUMNER
        datum = fil.stem.replace("kassa_", "")
        assert {rad["datum"] for rad in rader} == {datum}, fil.name
        assert len({rad["z_nummer"] for rad in rader}) == 1, fil.name
        assert {rad["kassaregister_id"] for rad in rader} == {"TB-KASSA-1"}, fil.name

        def summa(post):
            return sum(tolka_belopp(rad["belopp"]) for rad in rader if rad["post"] == post)

        forsaljning = {int(rad["momssats"]): tolka_belopp(rad["belopp"]) for rad in rader if rad["post"] == "forsaljning"}
        moms = {int(rad["momssats"]): tolka_belopp(rad["belopp"]) for rad in rader if rad["post"] == "moms"}
        brutto = summa("summa_brutto")

        assert set(forsaljning) == {12, 25}, fil.name
        assert set(moms) == set(forsaljning), fil.name
        assert sum(forsaljning.values()) == brutto, fil.name
        assert summa("betalsatt_kontant") + summa("betalsatt_kort") + summa("betalsatt_swish") == brutto, fil.name
        for sats, belopp in forsaljning.items():
            assert moms[sats] == generator.moms_ur_brutto(belopp, sats), fil.name


def test_luckan_i_z_serien_finns_dar_facit_sager():
    fel = planterat("lucka_i_z_serien")
    serie = [(int(las_csv(fil)[0]["z_nummer"]), fil.stem.replace("kassa_", "")) for fil in kassafiler()]
    luckor = [(z_fore, z_efter, datum_fore, datum_efter)
              for (z_fore, datum_fore), (z_efter, datum_efter) in zip(serie, serie[1:])
              if z_efter != z_fore + 1]

    assert len(luckor) == 1
    z_fore, z_efter, datum_fore, datum_efter = luckor[0]
    assert z_efter == z_fore + 2
    assert fel["z_nummer"] == z_fore + 1
    assert datum_fore < fel["datum"] < datum_efter
    assert not (DATAMAPP / fel["filnamn"]).exists()
    assert dt.date.fromisoformat(fel["datum"]).weekday() < 6  # en vanlig öppen dag, inte söndag


def test_facit_for_forsaljning_stammer_med_kassafilerna():
    for manad in MANADER:
        filer = [fil for fil in kassafiler() if fil.stem.startswith("kassa_" + manad)]
        forvantat = facit()["forsaljning"][manad]
        assert forvantat["antal_z_rapporter"] == len(filer)
        for sats, summor in forvantat["per_momssats"].items():
            rader = [rad for fil in filer for rad in las_csv(fil) if rad["momssats"] == sats]
            brutto = sum(tolka_belopp(r["belopp"]) for r in rader if r["post"] == "forsaljning")
            moms = sum(tolka_belopp(r["belopp"]) for r in rader if r["post"] == "moms")
            assert summor == {"brutto_ore": brutto, "moms_ore": moms, "netto_ore": brutto - moms}


# --- (d) Varje planterat fel finns i filerna ---

def test_facit_listar_exakt_de_planterade_felen_for_q1():
    typer = sorted((fel["manad"], fel["typ"]) for fel in facit()["planterade_fel"])
    assert typer == [
        ("2025-01", "dubblett_leverantorsfaktura"),
        ("2025-01", "lucka_i_z_serien"),
        ("2025-02", "bankrad_utan_underlag"),
        ("2025-02", "fel_momssats_kvitto"),
        ("2025-03", "brott_i_saldokedjan"),
        ("2025-03", "restaurangkvitto_privat_karaktar"),
    ]


def test_dubbletten_finns_och_ar_samma_faktura_som_originalet():
    fel = planterat("dubblett_leverantorsfaktura")
    kopia = json.loads((DATAMAPP / fel["filnamn"]).read_text(encoding="utf-8"))
    original = json.loads((DATAMAPP / fel["original_filnamn"]).read_text(encoding="utf-8"))
    assert kopia["id"] == fel["id"] and original["id"] == fel["original_id"]
    assert kopia["typ"] == "leverantorsfaktura"
    assert {k: v for k, v in kopia.items() if k != "id"} == {k: v for k, v in original.items() if k != "id"}
    assert fel["manad"] == kopia["datum"][:7]

    # Inga andra dubbletter: varje (motpart, fakturanummer) finns bara en gång utöver den planterade.
    nycklar = [(u["motpart"], u["fakturanummer"]) for u in underlag()]
    dubbletter = {n for n in nycklar if nycklar.count(n) > 1}
    assert dubbletter == {(original["motpart"], original["fakturanummer"])}

    # Fakturan betalas bara en gång.
    betalningar = [rad for manad in MANADER for rad in bankrader(manad) if rad["Referens"] == original["fakturanummer"]]
    assert len(betalningar) == 1
    assert betalningar[0]["belopp_ore"] == -original["belopp_ore"]


def test_kvittot_med_fel_momssats_finns():
    fel = planterat("fel_momssats_kvitto")
    dok = json.loads((DATAMAPP / fel["filnamn"]).read_text(encoding="utf-8"))
    assert dok["id"] == fel["id"] and dok["typ"] == "kvitto"
    assert [rad["momssats"] for rad in dok["moms"]] == [fel["momssats_i_underlaget"]]
    assert MOMSSATS_PER_KVITTOMOTPART[dok["motpart"]] == fel["forvantad_momssats"] != fel["momssats_i_underlaget"]

    # Alla andra kvitton har den sats som gäller för motpartens varugrupp.
    for annat in underlag():
        if annat["typ"] == "kvitto" and annat["id"] != fel["id"]:
            assert [r["momssats"] for r in annat["moms"]] == [MOMSSATS_PER_KVITTOMOTPART[annat["motpart"]]]


def test_bankraden_utan_underlag_finns_och_ar_den_enda():
    fel = planterat("bankrad_utan_underlag")
    manad = fel["filnamn"].replace("bank_", "").replace(".csv", "")
    rad = bankrader(manad)[fel["rad"] - 1]
    assert int(rad["Radnummer"]) == fel["rad"]
    assert rad["belopp_ore"] == fel["belopp_ore"]
    assert rad["Beskrivning"].startswith("KORTKOP ")

    kvitton = [u for u in underlag() if u["typ"] == "kvitto"]
    utan_kvitto = []
    for m in MANADER:
        for kortkop in (r for r in bankrader(m) if r["Beskrivning"].startswith("KORTKOP ")):
            motpart = kortkop["Beskrivning"].replace("KORTKOP ", "")
            if not any(k["motpart"] == motpart and k["datum"] == kortkop["Transaktionsdag"]
                       and k["belopp_ore"] == -kortkop["belopp_ore"] for k in kvitton):
                utan_kvitto.append(("bank_" + m + ".csv", int(kortkop["Radnummer"])))
    assert utan_kvitto == [(fel["filnamn"], fel["rad"])]


def test_alla_leverantorsbetalningar_har_en_faktura():
    fakturor = {u["fakturanummer"]: u for u in underlag() if u["typ"] == "leverantorsfaktura"}
    for manad in MANADER:
        for rad in bankrader(manad):
            if rad["Referens"].startswith("SYNT-"):
                faktura = fakturor[rad["Referens"]]
                assert rad["Beskrivning"] == faktura["motpart"]
                assert rad["belopp_ore"] == -faktura["belopp_ore"]


def test_raden_med_fel_saldo_finns():
    fel = planterat("brott_i_saldokedjan")
    manad = fel["filnamn"].replace("bank_", "").replace(".csv", "")
    rader = bankrader(manad)
    rad = rader[fel["rad"] - 1]
    assert int(rad["Radnummer"]) == fel["rad"]
    assert rad["saldo_ore"] == fel["visat_saldo_ore"] != fel["ratt_saldo_ore"]
    # Rätt saldo är raden före plus beloppet. Raden före och raden efter är korrekta.
    assert rader[fel["rad"] - 2]["saldo_ore"] + rad["belopp_ore"] == fel["ratt_saldo_ore"]
    assert fel["ratt_saldo_ore"] + rader[fel["rad"]]["belopp_ore"] == rader[fel["rad"]]["saldo_ore"]


def test_restaurangkvittot_finns():
    fel = planterat("restaurangkvitto_privat_karaktar")
    dok = json.loads((DATAMAPP / fel["filnamn"]).read_text(encoding="utf-8"))
    assert dok["id"] == fel["id"] and dok["typ"] == "kvitto"
    assert dok["motpart"] == "RESTAURANG-1"
    assert dok["datum"][:7] == fel["manad"]
    assert dt.date.fromisoformat(dok["datum"]).weekday() == 6  # söndag, butiken är stängd
    kortkop = [r for m in MANADER for r in bankrader(m)
               if r["Beskrivning"] == "KORTKOP RESTAURANG-1" and r["belopp_ore"] == -dok["belopp_ore"]]
    assert len(kortkop) == 1


# --- Underlagens format ---

def test_underlagen_har_ratt_falt_och_gar_ihop():
    falt = ["id", "typ", "datum", "motpart", "fakturanummer", "belopp_ore", "moms", "flaggor"]
    for fil in sorted((DATAMAPP / "underlag").glob("*.json")):
        dok = json.loads(fil.read_text(encoding="utf-8"))
        assert list(dok) == falt, fil.name
        assert fil.stem == dok["id"]
        assert dok["typ"] in ("kvitto", "leverantorsfaktura")
        assert dok["flaggor"] == []
        assert isinstance(dok["belopp_ore"], int) and not isinstance(dok["belopp_ore"], bool)
        for rad in dok["moms"]:
            assert list(rad) == ["momssats", "underlag_ore", "moms_ore"]
            assert all(isinstance(v, int) for v in rad.values())
        assert dok["moms"], fil.name  # minst en momsrad (beslut i SPEC 11)
        assert dok["belopp_ore"] == sum(r["underlag_ore"] + r["moms_ore"] for r in dok["moms"]), fil.name


def test_momsfria_underlag_har_en_rad_med_sats_0_och_moms_0():
    # Försäkringsfakturan har ingen moms. Den har en momsrad med sats 0 och moms 0, inte en tom lista.
    momsfria = [dok for dok in underlag() if any(rad["momssats"] == 0 for rad in dok["moms"])]
    assert [(dok["motpart"], dok["moms"]) for dok in momsfria] == [
        ("LEV-FORSAKRING", [{"momssats": 0, "underlag_ore": generator.FORSAKRING_HELAR_ORE, "moms_ore": 0}])]
    assert all(rad["moms_ore"] == 0 for dok in momsfria for rad in dok["moms"] if rad["momssats"] == 0)
