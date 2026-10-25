"""Rättelser efter granskning 4 som gäller både bankfilen och Z-filen.

- NUL-tecken: radnumret i meddelandet är radens verkliga nummer i filen, för både bank och kassa.
- I3: riktningstecken (U+202A–U+202E och U+2066–U+2069) stoppar filen. Andra osynliga
  formattecken, till exempel U+200D i emoji, godtas fortfarande.
- I4: en sökväg som inte är text eller Path stoppas innan något öppnas.

Varje test körs på både las_bankfil och las_kassafil. Bankfilen och Z-filen nedan är felfria så
när som på det som testet lägger till.
"""

import builtins
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parents[2]
SCRIPTS = AGENT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from las_bank import BankfilFel, ladda_bankformat, las_bankfil  # noqa: E402
from las_kassa import KassafilFel, ladda_kassaformat, las_kassafil  # noqa: E402

BANKFORMAT_FIL = AGENT / "foretag" / "syntet-testbutik" / "bankformat.json"
KASSAFORMAT_FIL = AGENT / "foretag" / "syntet-testbutik" / "kassaformat.json"
BANKFORMAT = ladda_bankformat(BANKFORMAT_FIL)
KASSAFORMAT = ladda_kassaformat(KASSAFORMAT_FIL)

# En felfri bankfil: rubrikrad och två transaktioner, från 0 kr till 3 kr. Rad 2 och 3 i filen.
BANK_RUBRIK = "Radnummer,Bokföringsdag,Transaktionsdag,Referens,Beskrivning,Belopp,Bokfört saldo"
BANK_RADER = ["1,2025-01-02,2025-01-02,REF-1,Kund A,1.00,1.00",
              "2,2025-01-03,2025-01-03,REF-2,Kund B,2.00,3.00"]

# En felfri Z-fil med en extra kolumn för fri text (extra kolumner godtas). Rad 2–8 i filen.
KASSA_RUBRIK = "datum,z_nummer,kassaregister_id,post,momssats,belopp,anteckning"
KASSA_RADER = [
    "2025-01-02,1001,TB-KASSA-1,forsaljning,12,112.00,x",
    "2025-01-02,1001,TB-KASSA-1,forsaljning,25,50.00,x",
    "2025-01-02,1001,TB-KASSA-1,moms,12,12.00,x",
    "2025-01-02,1001,TB-KASSA-1,moms,25,10.00,x",
    "2025-01-02,1001,TB-KASSA-1,betalsatt_kontant,,100.00,x",
    "2025-01-02,1001,TB-KASSA-1,betalsatt_kort,,62.00,x",
    "2025-01-02,1001,TB-KASSA-1,summa_brutto,,162.00,x",
]


def las_bank(mapp, rader):
    fil = mapp / "bank.csv"
    fil.write_bytes(("\n".join(rader) + "\n").encode("utf-8"))
    return las_bankfil(fil, BANKFORMAT, 0, 300)


def las_kassa(mapp, rader):
    fil = mapp / "kassa_2025-01-02.csv"
    fil.write_bytes(("\n".join(rader) + "\n").encode("utf-8"))
    return las_kassafil(fil, KASSAFORMAT)


# Varje sort: (funktion som läser raderna, rubrik, dataraderna, felklass, fältet med fri text
# som byts ut, och raden i filen där det fältet står först).
SORTER = {
    "bank": (las_bank, BANK_RUBRIK, BANK_RADER, BankfilFel, "Kund A", 2),
    "kassa": (las_kassa, KASSA_RUBRIK, KASSA_RADER, KassafilFel, ",x", 2),
}
SORT = pytest.mark.parametrize("sort", SORTER.values(), ids=SORTER.keys())


def ersatt_i_rad(rader, index, gammalt, nytt):
    rader = list(rader)
    assert gammalt in rader[index]
    rader[index] = rader[index].replace(gammalt, nytt, 1)
    return rader


def test_de_felfria_filerna_godkanns(tmp_path):
    # Skydd: testerna nedan ändrar en sak i de här filerna. Utan ändringen ska de godkännas.
    assert len(las_bank(tmp_path, [BANK_RUBRIK] + BANK_RADER)) == 2
    assert len(las_kassa(tmp_path, [KASSA_RUBRIK] + KASSA_RADER)) == 7


# --- NUL-tecken: radens verkliga radnummer i filen ---

# Tecken som Python räknar som radslut när texten delas i rader (str.splitlines), men som en
# textredigerare inte räknar. De stoppar filen, men först efter NUL-kontrollen.
DOLDA_RADSLUT = {"vt": "\x0b", "ff": "\x0c", "fs": "\x1c", "gs": "\x1d", "rs": "\x1e", "nel": "\x85",
                 "u2028": "\u2028", "u2029": "\u2029"}


@pytest.mark.parametrize("radslut", DOLDA_RADSLUT.values(), ids=DOLDA_RADSLUT.keys())
@SORT
def test_nul_tecken_far_radens_verkliga_radnummer(tmp_path, sort, radslut):
    # Fil: rubrikrad (rad 1), en rad med ett dolt radslut inuti ett fält (rad 2) och en rad med NUL
    # (rad 3). Den gamla bankkoden räknade det dolda radslutet som en ny rad och sa "rad 4".
    las, rubrik, rader, fel, falt, _ = sort
    rader = ersatt_i_rad(rader, 0, falt, falt + radslut + "y")
    rader[1] += "\x00"
    with pytest.raises(fel) as stopp:
        las(tmp_path, [rubrik] + rader)
    assert "rad 3 i filen innehåller ett NUL-tecken" in str(stopp.value), str(stopp.value)


@SORT
def test_nul_tecken_efter_dolda_radslut_fore_rubrikraden(tmp_path, sort):
    # Bankfilen får ha rader före rubrikraden. Fyra dolda radslut på rad 1 och NUL på rad 2.
    las, rubrik, rader, fel, _, _ = sort
    with pytest.raises(fel) as stopp:
        las(tmp_path, ["a\x0cb\x1cc\x85d\u2028e", "X\x00Y", rubrik] + rader)
    assert "rad 2 i filen innehåller ett NUL-tecken" in str(stopp.value), str(stopp.value)


@SORT
def test_nul_tecken_med_windows_radslut(tmp_path, sort):
    # Skydd: \r\n är ett radslut, inte två.
    las, rubrik, rader, fel, _, _ = sort
    rader = rader[:1] + [rader[1] + "\x00"] + rader[2:]
    fil = tmp_path / ("bank.csv" if las is las_bank else "kassa_2025-01-02.csv")
    fil.write_bytes(("\r\n".join([rubrik] + rader) + "\r\n").encode("utf-8"))
    with pytest.raises(fel, match="rad 3 i filen innehåller ett NUL-tecken"):
        las_bankfil(fil, BANKFORMAT, 0, 300) if las is las_bank else las_kassafil(fil, KASSAFORMAT)


# --- I3: riktningstecken stoppar filen ---

RIKTNINGSTECKEN = [chr(nummer) for nummer in [*range(0x202A, 0x202F), *range(0x2066, 0x206A)]]


def test_i3_riktningstecknen_ar_nio():
    assert ["U+" + format(ord(t), "04X") for t in RIKTNINGSTECKEN] == [
        "U+202A", "U+202B", "U+202C", "U+202D", "U+202E", "U+2066", "U+2067", "U+2068", "U+2069"]


@pytest.mark.parametrize("tecken", RIKTNINGSTECKEN, ids=[format(ord(t), "04X") for t in RIKTNINGSTECKEN])
@SORT
def test_i3_riktningstecken_i_ett_textfalt_stoppar_filen(tmp_path, sort, tecken):
    # Granskarens fall: beskrivningen U+202E + "ET-VEL", som visas som "LEV-TE".
    las, rubrik, rader, fel, falt, filrad = sort
    resultat = None
    with pytest.raises(fel) as stopp:
        resultat = las(tmp_path, [rubrik] + ersatt_i_rad(rader, 0, falt, falt + tecken + "ET-VEL"))
    assert resultat is None
    assert ("rad " + str(filrad) + " i filen innehåller tecknet U+" + format(ord(tecken), "04X")
            + ", som är ett riktningstecken") in str(stopp.value), str(stopp.value)


@pytest.mark.parametrize("tecken", ["\u202e", "\u2066"], ids=["202E", "2066"])
def test_i3_riktningstecken_i_bankens_referens_och_fore_rubrikraden(tmp_path, tecken):
    for rader, filrad in [
        ([BANK_RUBRIK] + ersatt_i_rad(BANK_RADER, 1, "REF-2", "R" + tecken + "EF-2"), 3),
        (["Kontoutdrag " + tecken + "x", BANK_RUBRIK] + BANK_RADER, 1),
    ]:
        with pytest.raises(BankfilFel, match="rad " + str(filrad) + " i filen innehåller tecknet U+"):
            las_bank(tmp_path, rader)


def test_i3_riktningstecken_i_kassaregistret_stoppar_filen(tmp_path):
    # Kassaregistrets namn jämförs efter normalisering, som tar bort osynliga tecken (H2). Utan
    # I3 godtogs därför "TB-KASSA-1" med ett riktningstecken.
    rader = [rad.replace("TB-KASSA-1", "TB-KASSA-1\u202e") for rad in KASSA_RADER]
    with pytest.raises(KassafilFel, match="rad 2 i filen innehåller tecknet U\\+202E, som är ett riktningstecken"):
        las_kassa(tmp_path, [KASSA_RUBRIK] + rader)


@SORT
def test_i3_styrtecken_fore_riktningstecken_ger_samma_meddelande_som_forut(tmp_path, sort):
    # Skydd: en fil med både ett styrtecken och ett riktningstecken stoppas för styrtecknet, som förut.
    las, rubrik, rader, fel, falt, _ = sort
    rader = ersatt_i_rad(rader, 0, falt, falt + "\x0c\u202e")
    with pytest.raises(fel, match="innehåller tecknet U\\+000C, som är ett styrtecken"):
        las(tmp_path, [rubrik] + rader)


ANDRA_OSYNLIGA = {
    "emoji_med_u200d": "\U0001F468\u200d\U0001F469\u200d\U0001F467",
    "u200b": "a\u200bb",
    "mjukt_bindestreck": "a\u00adb",
    "u2060": "a\u2060b",
    "u200c": "a\u200cb",
}


@pytest.mark.parametrize("text", ANDRA_OSYNLIGA.values(), ids=ANDRA_OSYNLIGA.keys())
@SORT
def test_i3_andra_osynliga_formattecken_godtas(tmp_path, sort, text):
    las, rubrik, rader, _, falt, _ = sort
    resultat = las(tmp_path, [rubrik] + ersatt_i_rad(rader, 0, falt, falt + text))
    assert len(resultat) == len(rader)
    if las is las_bank:
        assert resultat[0]["beskrivning"] == "Kund A" + text  # texten är oförändrad


# --- I4: sökväg av fel typ ---

FEL_TYP = {"none": None, "flyttal": 1.5, "lista": ["bank.csv"], "ordbok": {}, "bytes": b"bank.csv",
           "objekt": object()}

INLASNINGAR = {
    "las_bankfil": (lambda sokvag: las_bankfil(sokvag, BANKFORMAT, 0, 300), BankfilFel,
                    "Bankfilen stoppas: sökvägen ska vara text eller en Path, inte "),
    "las_kassafil": (lambda sokvag: las_kassafil(sokvag, KASSAFORMAT), KassafilFel,
                     "Kassafilen stoppas: sökvägen ska vara text eller en Path, inte "),
    "ladda_bankformat": (ladda_bankformat, BankfilFel,
                         "Bankformatet går inte att läsa: sökvägen ska vara text eller en Path, inte "),
    "ladda_kassaformat": (ladda_kassaformat, KassafilFel,
                          "Kassaformatet går inte att läsa: sökvägen ska vara text eller en Path, inte "),
}


@pytest.mark.parametrize("sokvag", FEL_TYP.values(), ids=FEL_TYP.keys())
@pytest.mark.parametrize("inlasning", INLASNINGAR.values(), ids=INLASNINGAR.keys())
def test_i4_sokvag_av_fel_typ_stoppas_innan_nagot_oppnas(monkeypatch, inlasning, sokvag):
    funktion, fel, meddelande = inlasning

    def ingen_fil_far_oppnas(*args, **kwargs):
        raise AssertionError("en fil öppnades: " + repr(args))

    monkeypatch.setattr(builtins, "open", ingen_fil_far_oppnas)
    with pytest.raises(fel) as stopp:
        funktion(sokvag)
    monkeypatch.undo()
    assert type(stopp.value) is fel
    assert str(stopp.value) == meddelande + type(sokvag).__name__ + "."


def test_i4_text_och_path_godtas(tmp_path):
    # Skydd: text, Path och en text som är en underklass till str fungerar som förut.
    class Text(str):
        pass

    fil = tmp_path / "bank.csv"
    fil.write_text("\n".join([BANK_RUBRIK] + BANK_RADER) + "\n", encoding="utf-8")
    for sokvag in (fil, str(fil), Text(str(fil))):
        assert len(las_bankfil(sokvag, BANKFORMAT, 0, 300)) == 2
    for sokvag in (BANKFORMAT_FIL, str(BANKFORMAT_FIL)):
        assert ladda_bankformat(sokvag) == BANKFORMAT
    for sokvag in (KASSAFORMAT_FIL, str(KASSAFORMAT_FIL)):
        assert ladda_kassaformat(sokvag) == KASSAFORMAT


def test_i4_heltal_och_sanningsvarden_stanger_inte_programmets_utdata():
    # Ett heltal, True eller False tolkades av Python som ett filnummer: 0 är programmets indata, 1
    # dess utdata och 2 dess felutskrifter. Den gamla koden läste från filnumret och stängde det
    # sedan, så att allt programmet skrev efteråt gick förlorat. Det prövas i ett eget program, så
    # att testsviten själv inte förlorar sin utdata om felet kommer tillbaka.
    program = textwrap.dedent("""
        import sys
        sys.path.insert(0, sys.argv[1])
        from las_bank import BankfilFel, ladda_bankformat, las_bankfil
        from las_kassa import KassafilFel, ladda_kassaformat, las_kassafil
        bankformat = ladda_bankformat(sys.argv[2])
        kassaformat = ladda_kassaformat(sys.argv[3])
        for sokvag in (True, False, 0, 1, 2):
            for namn, las, fel in [("bank", lambda s: las_bankfil(s, bankformat, 0, 0), BankfilFel),
                                   ("kassa", lambda s: las_kassafil(s, kassaformat), KassafilFel),
                                   ("bankformat", ladda_bankformat, BankfilFel),
                                   ("kassaformat", ladda_kassaformat, KassafilFel)]:
                try:
                    las(sokvag)
                    print("GODKÄND", namn, repr(sokvag), flush=True)
                except fel as stopp:
                    print("STOPPAD", namn, repr(sokvag), str(stopp), flush=True)
        print("UTDATA LEVER", flush=True)
        print("FELUTSKRIFT LEVER", file=sys.stderr, flush=True)
    """)
    korning = subprocess.run(
        [sys.executable, "-I", "-c", program, str(SCRIPTS), str(BANKFORMAT_FIL), str(KASSAFORMAT_FIL)],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=60,
    )
    utdata = korning.stdout.decode("utf-8", "replace")
    assert korning.returncode == 0, (utdata, korning.stderr)
    assert "UTDATA LEVER" in utdata
    assert "FELUTSKRIFT LEVER" in korning.stderr.decode("utf-8", "replace")
    rader = [rad for rad in utdata.splitlines() if rad.startswith(("STOPPAD", "GODKÄND"))]
    assert len(rader) == 5 * 4
    for rad in rader:
        typ = "bool" if rad.split()[2] in ("True", "False") else "int"
        assert rad.startswith("STOPPAD") and rad.endswith(
            "sökvägen ska vara text eller en Path, inte " + typ + "."), rad
