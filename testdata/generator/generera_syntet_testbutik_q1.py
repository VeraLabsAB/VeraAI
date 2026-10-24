"""Generator för SYNTETISK testdata: Syntet Testbutik AB, första kvartalet 2025.

Allt som skrivs är påhittat. Företaget, motparterna, numren och beloppen finns inte.
Momssatserna (12 % på livsmedel, 25 % på övrigt) är SYNTETISKA antaganden och inte verifierade.

Körs så här, från mappen agent/:

    .venv/bin/python testdata/generator/generera_syntet_testbutik_q1.py

Samma körning ger exakt samma filer varje gång, eftersom slumpen har ett fast frö.
Filerna skrivs till testdata/syntet-testbutik/2025-Q1/ om inget annat anges med --ut.

Alla belopp är heltal i öre. I filerna skrivs de med punkt som decimaltecken, t.ex. 1234.50.
"""

import argparse
import copy
import csv
import datetime as dt
import json
from pathlib import Path
import random

SLUMPFRO = 20250101
AR = 2025
MANADER = [1, 2, 3]
FORSTA_DAG = dt.date(AR, 1, 1)
SISTA_DAG = dt.date(AR, 3, 31)
STANDARDMAPP = Path(__file__).resolve().parents[1] / "syntet-testbutik" / "2025-Q1"

KASSAREGISTER_ID = "TB-KASSA-1"
FORSTA_Z_NUMMER = 1001
INGAENDE_SALDO_ORE = 8500000  # 85 000,00 kr den 1 januari

# SYNTETISKA antaganden, inte verifierade (se testdata/README.md).
MOMS_LIVSMEDEL = 12
MOMS_OVRIGT = 25
KORTAVGIFT_PROMILLE = 12  # 1,2 % av kortförsäljningen dras vid avräkningen
BANKAVGIFT_KONTO_ORE = 12500
BANKAVGIFT_KORTINLOSEN_ORE = 19900
HYRA_PER_KVARTAL_ORE = 3600000  # exklusive moms
FORSAKRING_HELAR_ORE = 960000
BETALNINGSVILLKOR_DAGAR = 30

# Röda dagar i Sverige under januari–mars 2025. Butiken är stängd och banken bokför inte.
HELGDAGAR = {dt.date(2025, 1, 1), dt.date(2025, 1, 6)}

# Leverantörer som fakturerar varje månad:
# (motpart, prefix i fakturanumret, fakturadagar, momssats, lägsta och högsta belopp i kronor exkl. moms)
LEVERANTORER = [
    ("LEV-TELE", "TELE", [1], MOMS_OVRIGT, 599, 599),
    ("LEV-EL", "EL", [3], MOMS_OVRIGT, 1200, 2600),
    ("LEV-TE", "TE", [5, 19], MOMS_LIVSMEDEL, 7000, 16000),
    ("LEV-KAFFE", "KAFFE", [10, 24], MOMS_LIVSMEDEL, 6000, 14000),
    ("LEV-TILLBEHOR", "TILLB", [14], MOMS_OVRIGT, 3000, 11000),
]

# Kvitton för mindre inköp i butik, betalda med företagets kort:
# (datum, motpart, momssats, lägsta och högsta belopp i kronor inkl. moms)
KVITTON = [
    (dt.date(2025, 1, 9), "BUTIK-FORBRUKNING", MOMS_OVRIGT, 150, 650),
    (dt.date(2025, 1, 22), "BUTIK-STAD", MOMS_OVRIGT, 120, 480),
    (dt.date(2025, 2, 10), "BUTIK-FORBRUKNING", MOMS_OVRIGT, 150, 650),
    (dt.date(2025, 2, 21), "BUTIK-STAD", MOMS_OVRIGT, 120, 480),
    (dt.date(2025, 3, 11), "BUTIK-FORBRUKNING", MOMS_OVRIGT, 150, 650),
    (dt.date(2025, 3, 24), "BUTIK-STAD", MOMS_OVRIGT, 120, 480),
]

# --- Planterade fel (testforetag/FIKTIVT_FORETAG.md, avsnitt 8) ---

# Januari: den första fakturan från den här leverantören läses in två gånger.
DUBBLETT_MOTPART = "LEV-TE"
# Januari: Z-rapporten för den här dagen saknas. Butiken hade öppet och Z-numret förbrukades.
SAKNAD_Z_DAG = dt.date(2025, 1, 15)
# Februari: kvittot för städartiklar har livsmedelssatsen i stället för satsen för övrigt.
FEL_MOMS_KVITTO = (dt.date(2025, 2, 21), "BUTIK-STAD")
# Februari: ett kortköp syns på banken men inget kvitto finns.
KORTKOP_UTAN_KVITTO = (dt.date(2025, 2, 18), "BUTIK-FORBRUKNING", 150, 650)
# Mars: en rad i bankfilen visar fel saldo, så här mycket för högt.
SALDOFEL_MANAD = 3
SALDOFEL_ORE = 10000
# Mars: restaurangkvitto en söndag då butiken är stängd.
RESTAURANGKVITTO = (dt.date(2025, 3, 16), "RESTAURANG-1", MOMS_LIVSMEDEL, 1400, 2200)

# Ordning för bankrader som bokförs samma dag.
KATEGORIER = ["kortavrakning", "swish", "kontantinsattning", "leverantorsbetalning", "kortkop", "bankavgift"]

BANKKOLUMNER = ["Radnummer", "Bokföringsdag", "Transaktionsdag", "Referens", "Beskrivning", "Belopp", "Bokfört saldo"]
KASSAKOLUMNER = ["datum", "z_nummer", "kassaregister_id", "post", "momssats", "belopp"]


# --- Hjälpfunktioner ---

def belopp_text(ore):
    """Heltal i öre som text med punkt som decimaltecken, t.ex. -123450 -> "-1234.50"."""
    tecken = "-" if ore < 0 else ""
    kronor, rest = divmod(abs(ore), 100)
    return tecken + str(kronor) + "." + str(rest).zfill(2)


def moms_ur_brutto(brutto_ore, momssats):
    """Momsen i ett belopp som innehåller moms, avrundad till närmaste öre (hälften uppåt)."""
    return (brutto_ore * momssats * 2 + 100 + momssats) // (2 * (100 + momssats))


def moms_pa_netto(netto_ore, momssats):
    """Momsen på ett belopp utan moms, avrundad till närmaste öre (hälften uppåt)."""
    return (netto_ore * momssats * 2 + 100) // 200


def ar_bankdag(dag):
    return dag.weekday() < 5 and dag not in HELGDAGAR


def nasta_bankdag(dag):
    """Första bankdagen på eller efter dagen."""
    while not ar_bankdag(dag):
        dag += dt.timedelta(days=1)
    return dag


def oppna_dagar():
    """Butiken har öppet måndag–lördag utom röda dagar."""
    dag = FORSTA_DAG
    while dag <= SISTA_DAG:
        if dag.weekday() < 6 and dag not in HELGDAGAR:
            yield dag
        dag += dt.timedelta(days=1)


def dela_i_kronor(rng, total_ore, antal):
    """Delar ett belopp i hela kronor i ett antal delar som tillsammans blir exakt beloppet."""
    kronor = total_ore // 100
    vikter = [rng.randint(20, 100) for _ in range(antal)]
    delar = [kronor * vikt // sum(vikter) for vikt in vikter]
    delar[-1] += kronor - sum(delar)
    assert all(del_ > 0 for del_ in delar)
    return [del_ * 100 for del_ in delar]


# --- Kassa ---

def skapa_zrapporter(rng):
    rapporter = []
    z_nummer = FORSTA_Z_NUMMER
    for dag in oppna_dagar():
        faktor = 14 if dag.weekday() == 5 else 10  # lördagar säljer mer
        livsmedel = rng.randint(1800, 5200) * faktor // 10 * 100
        ovrigt = rng.randint(400, 2200) * faktor // 10 * 100
        brutto = livsmedel + ovrigt
        kort = brutto * rng.randint(50, 70) // 10000 * 100
        swish = brutto * rng.randint(10, 20) // 10000 * 100
        kontant = brutto - kort - swish
        swishdelar = dela_i_kronor(rng, swish, rng.randint(2, 6))
        rapporter.append({
            "datum": dag,
            "z_nummer": z_nummer,
            "forsaljning": {MOMS_LIVSMEDEL: livsmedel, MOMS_OVRIGT: ovrigt},
            "brutto": brutto,
            "kontant": kontant,
            "kort": kort,
            "swish": swish,
            "swishdelar": swishdelar,
            "saknas": dag == SAKNAD_Z_DAG,
        })
        z_nummer += 1
    return rapporter


def kassarader(rapport):
    def rad(post, momssats, belopp):
        return [rapport["datum"].isoformat(), str(rapport["z_nummer"]), KASSAREGISTER_ID,
                post, momssats, belopp_text(belopp)]

    satser = sorted(rapport["forsaljning"])
    rader = [rad("forsaljning", str(sats), rapport["forsaljning"][sats]) for sats in satser]
    rader += [rad("moms", str(sats), moms_ur_brutto(rapport["forsaljning"][sats], sats)) for sats in satser]
    rader.append(rad("betalsatt_kontant", "", rapport["kontant"]))
    rader.append(rad("betalsatt_kort", "", rapport["kort"]))
    rader.append(rad("betalsatt_swish", "", rapport["swish"]))
    rader.append(rad("summa_brutto", "", rapport["brutto"]))
    return rader


# --- Underlag ---

def nytt_underlag(typ, datum, motpart, fakturanummer, momsrader, belopp_ore=None):
    """momsrader: lista med (momssats, underlag_ore, moms_ore)."""
    moms = [{"momssats": sats, "underlag_ore": underlag, "moms_ore": momsbelopp}
            for sats, underlag, momsbelopp in momsrader]
    if belopp_ore is None:
        belopp_ore = sum(rad["underlag_ore"] + rad["moms_ore"] for rad in moms)
    return {
        "id": None,
        "typ": typ,
        "datum": datum.isoformat(),
        "motpart": motpart,
        "fakturanummer": fakturanummer,
        "belopp_ore": belopp_ore,
        "moms": moms,
        "flaggor": [],
    }


def skapa_leverantorsfakturor(rng):
    fakturor = []
    for motpart, prefix, dagar, sats, lagst, hogst in LEVERANTORER:
        lopnummer = rng.randint(100, 899)
        for manad in MANADER:
            for i, dag in enumerate(dagar):
                datum = nasta_bankdag(dt.date(AR, manad, dag))
                netto = rng.randint(lagst, hogst) * 100
                momsrader = [(sats, netto, moms_pa_netto(netto, sats))]
                if motpart == "LEV-KAFFE" and manad == 2 and i == 1:
                    # Kaffe och filterpapper på samma faktura: två momssatser.
                    filter_netto = rng.randint(800, 1500) * 100
                    momsrader.append((MOMS_OVRIGT, filter_netto, moms_pa_netto(filter_netto, MOMS_OVRIGT)))
                dok = nytt_underlag("leverantorsfaktura", datum, motpart,
                                    "SYNT-" + prefix + "-" + str(lopnummer), momsrader)
                forfallodag = datum + dt.timedelta(days=BETALNINGSVILLKOR_DAGAR)
                fakturor.append({"dok": dok, "betaldag": nasta_bankdag(forfallodag), "markering": None})
                lopnummer += 1

    # Försäkringens helårspremie. Fakturan har ingen moms (antagande, se README: Öppen fråga).
    datum = dt.date(2025, 1, 8)
    dok = nytt_underlag("leverantorsfaktura", datum, "LEV-FORSAKRING", "SYNT-FORS-" + str(rng.randint(1000, 9999)),
                        [], belopp_ore=FORSAKRING_HELAR_ORE)
    fakturor.append({"dok": dok, "betaldag": nasta_bankdag(datum + dt.timedelta(days=BETALNINGSVILLKOR_DAGAR)),
                     "markering": None})

    # Hyresavi för andra kvartalet, betalas i förskott sista vardagen före kvartalets början.
    datum = dt.date(2025, 3, 3)
    momsrader = [(MOMS_OVRIGT, HYRA_PER_KVARTAL_ORE, moms_pa_netto(HYRA_PER_KVARTAL_ORE, MOMS_OVRIGT))]
    dok = nytt_underlag("leverantorsfaktura", datum, "HYRESVARD", "SYNT-HYRA-2025-Q2", momsrader)
    fakturor.append({"dok": dok, "betaldag": dt.date(2025, 3, 31), "markering": None})

    # Planterat fel: samma faktura läses in en gång till. Den betalas bara en gång.
    original = next(f for f in fakturor
                    if f["dok"]["motpart"] == DUBBLETT_MOTPART and f["dok"]["datum"].startswith("2025-01"))
    original["markering"] = "dubblett_original"
    fakturor.append({"dok": copy.deepcopy(original["dok"]), "betaldag": None, "markering": "dubblett_kopia"})
    return fakturor


def kvitto(rng, datum, motpart, sats, lagst, hogst, markering=None):
    brutto = rng.randint(lagst, hogst) * 100
    moms = moms_ur_brutto(brutto, sats)
    dok = nytt_underlag("kvitto", datum, motpart, "SYNT-KV-" + str(rng.randint(10000, 99999)),
                        [(sats, brutto - moms, moms)])
    return {"dok": dok, "kortkop": datum, "markering": markering}


def skapa_kvitton(rng):
    kvitton = []
    for datum, motpart, sats, lagst, hogst in KVITTON:
        markering = None
        if (datum, motpart) == FEL_MOMS_KVITTO:
            sats = MOMS_LIVSMEDEL  # planterat fel
            markering = "fel_momssats"
        kvitton.append(kvitto(rng, datum, motpart, sats, lagst, hogst, markering))
    datum, motpart, sats, lagst, hogst = RESTAURANGKVITTO
    kvitton.append(kvitto(rng, datum, motpart, sats, lagst, hogst, "restaurang_privat"))
    return kvitton


def numrera_underlag(fakturor, kvitton):
    alla = fakturor + kvitton
    alla.sort(key=lambda u: (u["dok"]["datum"], u["dok"]["motpart"], u["dok"]["fakturanummer"],
                             u["markering"] == "dubblett_kopia"))
    for nummer, underlag in enumerate(alla, start=1):
        underlag["dok"]["id"] = "SYNT-U-2025-" + str(nummer).zfill(3)
    return alla


# --- Bank ---

def skapa_bankrader(rng, rapporter, fakturor, kvitton):
    rader = []

    def lagg_till(bokforingsdag, transaktionsdag, kategori, referens, beskrivning, belopp, markering=None):
        rader.append({
            "bokforingsdag": bokforingsdag,
            "transaktionsdag": transaktionsdag,
            "kategori": kategori,
            "lopnummer": len(rader),
            "referens": referens,
            "beskrivning": beskrivning,
            "belopp": belopp,
            "markering": markering,
        })

    for rapport in rapporter:
        dag = rapport["datum"]
        avrakningsdag = nasta_bankdag(dag + dt.timedelta(days=1))
        if avrakningsdag <= SISTA_DAG:
            avgift = (rapport["kort"] * KORTAVGIFT_PROMILLE + 500) // 1000
            lagg_till(avrakningsdag, avrakningsdag, "kortavrakning", "AVR-" + dag.strftime("%Y%m%d"),
                      "BET-KORT AVRAKNING " + dag.isoformat(), rapport["kort"] - avgift)
        for i, belopp in enumerate(rapport["swishdelar"], start=1):
            lagg_till(nasta_bankdag(dag), dag, "swish", "SWISH-" + dag.strftime("%Y%m%d") + "-" + str(i),
                      "BET-SWISH INBETALNING", belopp)

    # Kontantinsättning första bankdagen varje vecka, för kontanterna från dagarna före.
    ej_insatt = list(rapporter)
    dag = FORSTA_DAG
    while dag <= SISTA_DAG:
        forsta_i_veckan = ar_bankdag(dag) and all(
            not ar_bankdag(dag - dt.timedelta(days=n)) for n in range(1, dag.weekday() + 1))
        if forsta_i_veckan:
            insatt = [r for r in ej_insatt if r["datum"] < dag]
            if insatt:
                lagg_till(dag, dag, "kontantinsattning", "INS-" + dag.strftime("%Y%m%d"),
                          "KONTANTINSATTNING", sum(r["kontant"] for r in insatt))
                ej_insatt = [r for r in ej_insatt if r["datum"] >= dag]
        dag += dt.timedelta(days=1)

    for faktura in fakturor:
        if faktura["betaldag"] is not None and faktura["betaldag"] <= SISTA_DAG:
            dok = faktura["dok"]
            lagg_till(faktura["betaldag"], faktura["betaldag"], "leverantorsbetalning", dok["fakturanummer"],
                      dok["motpart"], -dok["belopp_ore"])

    for underlag in kvitton:
        dok = underlag["dok"]
        dag = underlag["kortkop"]
        lagg_till(nasta_bankdag(dag + dt.timedelta(days=1)), dag, "kortkop", "KORTKOP-" + dag.strftime("%Y%m%d"),
                  "KORTKOP " + dok["motpart"], -dok["belopp_ore"])

    # Planterat fel: kortköp utan kvitto.
    dag, motpart, lagst, hogst = KORTKOP_UTAN_KVITTO
    lagg_till(nasta_bankdag(dag + dt.timedelta(days=1)), dag, "kortkop", "KORTKOP-" + dag.strftime("%Y%m%d"),
              "KORTKOP " + motpart, -rng.randint(lagst, hogst) * 100, "kortkop_utan_kvitto")

    for manad in MANADER:
        sista_bankdag = max(d for d in (dt.date(AR, manad, 1) + dt.timedelta(days=n) for n in range(31))
                            if d.month == manad and ar_bankdag(d))
        manadstext = "2025-" + str(manad).zfill(2)
        lagg_till(sista_bankdag, sista_bankdag, "bankavgift", "AVG-" + manadstext,
                  "BANK AVGIFT FORETAGSKONTO", -BANKAVGIFT_KONTO_ORE)
        lagg_till(sista_bankdag, sista_bankdag, "bankavgift", "AVG-" + manadstext,
                  "BANK AVGIFT KORTINLOSEN", -BANKAVGIFT_KORTINLOSEN_ORE)

    rader.sort(key=lambda r: (r["bokforingsdag"], KATEGORIER.index(r["kategori"]), r["lopnummer"]))
    return rader


def bankfiler(rader):
    """Delar raderna per månad, numrerar dem och räknar saldot. Ett saldo i mars görs avsiktligt fel."""
    saldo = INGAENDE_SALDO_ORE
    filer = {}
    for manad in MANADER:
        manadsrader = [r for r in rader if r["bokforingsdag"].month == manad]
        ingaende = saldo
        for radnummer, rad in enumerate(manadsrader, start=1):
            saldo += rad["belopp"]
            rad["radnummer"] = radnummer
            rad["saldo"] = saldo
            rad["visat_saldo"] = saldo
        if manad == SALDOFEL_MANAD:
            felrad = manadsrader[len(manadsrader) // 2]
            felrad["visat_saldo"] = felrad["saldo"] + SALDOFEL_ORE
            felrad["markering"] = "saldofel"
        filer[manad] = {"rader": manadsrader, "ingaende": ingaende, "utgaende": saldo}
    return filer


# --- Skriva filer ---

def skriv_csv(sokvag, kolumner, rader):
    sokvag.parent.mkdir(parents=True, exist_ok=True)
    with open(sokvag, "w", encoding="utf-8", newline="") as fil:
        skrivare = csv.writer(fil, lineterminator="\n")
        skrivare.writerow(kolumner)
        skrivare.writerows(rader)


def skriv_json(sokvag, data):
    sokvag.parent.mkdir(parents=True, exist_ok=True)
    with open(sokvag, "w", encoding="utf-8", newline="") as fil:
        fil.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def rensa(utmapp):
    """Tar bort filer som generatorn själv har skrivit tidigare, och inget annat."""
    for monster in ["bank_*.csv", "facit.json", "kassa/kassa_*.csv", "underlag/*.json"]:
        for fil in utmapp.glob(monster):
            fil.unlink()


def manadsnamn(manad):
    return "2025-" + str(manad).zfill(2)


def skapa_facit(filer, rapporter, underlag):
    facit = {
        "beskrivning": "SYNTETISKT facit för Syntet Testbutik AB, 2025-Q1. Allt är påhittat.",
        "bank": {},
        "forsaljning": {},
        "planterade_fel": [],
    }
    for manad, fil in filer.items():
        facit["bank"][manadsnamn(manad)] = {
            "fil": "bank_" + manadsnamn(manad) + ".csv",
            "antal_rader": len(fil["rader"]),
            "ingaende_saldo_ore": fil["ingaende"],
            "utgaende_saldo_ore": fil["utgaende"],
        }

    for manad in MANADER:
        manadens = [r for r in rapporter if r["datum"].month == manad and not r["saknas"]]
        per_sats = {}
        for sats in [MOMS_LIVSMEDEL, MOMS_OVRIGT]:
            brutto = sum(r["forsaljning"][sats] for r in manadens)
            moms = sum(moms_ur_brutto(r["forsaljning"][sats], sats) for r in manadens)
            per_sats[str(sats)] = {"brutto_ore": brutto, "moms_ore": moms, "netto_ore": brutto - moms}
        facit["forsaljning"][manadsnamn(manad)] = {
            "antal_z_rapporter": len(manadens),
            "per_momssats": per_sats,
        }

    fel = facit["planterade_fel"]

    def underlag_med(markering):
        return next(u["dok"] for u in underlag if u["markering"] == markering)

    def bankrad_med(markering):
        for manad, fil in filer.items():
            for rad in fil["rader"]:
                if rad["markering"] == markering:
                    return manad, rad
        raise LookupError(markering)

    original = underlag_med("dubblett_original")
    kopia = underlag_med("dubblett_kopia")
    fel.append({
        "typ": "dubblett_leverantorsfaktura",
        "manad": "2025-01",
        "kontroll": "K4",
        "filnamn": "underlag/" + kopia["id"] + ".json",
        "id": kopia["id"],
        "original_id": original["id"],
        "original_filnamn": "underlag/" + original["id"] + ".json",
        "beskrivning": "Samma leverantörsfaktura (" + original["motpart"] + ", " + original["fakturanummer"]
                       + ") finns två gånger med olika id. Den betalas bara en gång på banken.",
    })

    saknad = next(r for r in rapporter if r["saknas"])
    fel.append({
        "typ": "lucka_i_z_serien",
        "manad": "2025-01",
        "kontroll": "inläsningskontroll",
        "filnamn": "kassa/kassa_" + saknad["datum"].isoformat() + ".csv",
        "z_nummer": saknad["z_nummer"],
        "datum": saknad["datum"].isoformat(),
        "saknad_forsaljning_brutto_ore": {str(s): b for s, b in sorted(saknad["forsaljning"].items())},
        "beskrivning": "Z-rapport " + str(saknad["z_nummer"]) + " saknas. Butiken hade öppet, och dagens "
                       "kortavräkning, Swish och kontanter syns ändå på banken. Filen finns inte och dagens "
                       "försäljning ingår inte i summan under \"forsaljning\".",
    })

    felmoms = underlag_med("fel_momssats")
    fel.append({
        "typ": "fel_momssats_kvitto",
        "manad": "2025-02",
        "kontroll": "K5",
        "filnamn": "underlag/" + felmoms["id"] + ".json",
        "id": felmoms["id"],
        "momssats_i_underlaget": MOMS_LIVSMEDEL,
        "forvantad_momssats": MOMS_OVRIGT,
        "beskrivning": "Kvitto för städartiklar (" + felmoms["motpart"] + ") med livsmedelssatsen "
                       + str(MOMS_LIVSMEDEL) + " % i stället för " + str(MOMS_OVRIGT) + " %.",
    })

    manad, rad = bankrad_med("kortkop_utan_kvitto")
    fel.append({
        "typ": "bankrad_utan_underlag",
        "manad": manadsnamn(manad),
        "kontroll": "K3",
        "filnamn": "bank_" + manadsnamn(manad) + ".csv",
        "rad": rad["radnummer"],
        "belopp_ore": rad["belopp"],
        "beskrivning": "Kortköp (" + rad["beskrivning"] + ") utan kvitto. Ska bli \"Saknat underlag\" "
                       "efter 7 dagar.",
    })

    manad, rad = bankrad_med("saldofel")
    fel.append({
        "typ": "brott_i_saldokedjan",
        "manad": manadsnamn(manad),
        "kontroll": "K1",
        "filnamn": "bank_" + manadsnamn(manad) + ".csv",
        "rad": rad["radnummer"],
        "visat_saldo_ore": rad["visat_saldo"],
        "ratt_saldo_ore": rad["saldo"],
        "beskrivning": "Bokfört saldo på raden är " + belopp_text(SALDOFEL_ORE).replace(".", ",")
                       + " kr för högt. Alla andra "
                       "rader stämmer med ingående saldo plus beloppen. Jämförs varje rad med raden före syns "
                       "felet även på nästa rad, eftersom den räknas från det felaktiga saldot.",
    })

    restaurang = underlag_med("restaurang_privat")
    fel.append({
        "typ": "restaurangkvitto_privat_karaktar",
        "manad": "2025-03",
        "kontroll": "K8",
        "filnamn": "underlag/" + restaurang["id"] + ".json",
        "id": restaurang["id"],
        "beskrivning": "Restaurangkvitto (" + restaurang["motpart"] + ") en söndag då butiken är stängd, "
                       "betalt med företagets kort. Avdragsbegränsat eller privat, alltid ärende.",
    })
    return facit


def generera(utmapp=STANDARDMAPP):
    """Skriver all testdata för 2025-Q1 till utmapp och returnerar facit."""
    utmapp = Path(utmapp)
    utmapp.mkdir(parents=True, exist_ok=True)
    rensa(utmapp)
    rng = random.Random(SLUMPFRO)

    rapporter = skapa_zrapporter(rng)
    fakturor = skapa_leverantorsfakturor(rng)
    kvitton = skapa_kvitton(rng)
    underlag = numrera_underlag(fakturor, kvitton)
    filer = bankfiler(skapa_bankrader(rng, rapporter, fakturor, kvitton))

    for manad, fil in filer.items():
        skriv_csv(utmapp / ("bank_" + manadsnamn(manad) + ".csv"), BANKKOLUMNER, [
            [str(r["radnummer"]), r["bokforingsdag"].isoformat(), r["transaktionsdag"].isoformat(),
             r["referens"], r["beskrivning"], belopp_text(r["belopp"]), belopp_text(r["visat_saldo"])]
            for r in fil["rader"]
        ])

    for rapport in rapporter:
        if not rapport["saknas"]:
            skriv_csv(utmapp / "kassa" / ("kassa_" + rapport["datum"].isoformat() + ".csv"),
                      KASSAKOLUMNER, kassarader(rapport))

    for u in underlag:
        skriv_json(utmapp / "underlag" / (u["dok"]["id"] + ".json"), u["dok"])

    facit = skapa_facit(filer, rapporter, underlag)
    skriv_json(utmapp / "facit.json", facit)
    return facit


def main():
    tolkare = argparse.ArgumentParser(description="Genererar SYNTETISK testdata för 2025-Q1.")
    tolkare.add_argument("--ut", type=Path, default=STANDARDMAPP, help="Mapp att skriva till.")
    argument = tolkare.parse_args()
    facit = generera(argument.ut)
    print("Testdata skriven till " + str(argument.ut))
    for fel in facit["planterade_fel"]:
        plats = fel.get("rad", fel.get("id", fel.get("z_nummer")))
        print("  " + fel["manad"] + "  " + fel["typ"] + "  " + fel["filnamn"] + "  " + str(plats))


if __name__ == "__main__":
    main()
