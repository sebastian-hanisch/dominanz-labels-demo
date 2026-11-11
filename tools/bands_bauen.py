"""Erzeugt die festen Messreihen (data/*.json) aus den Rohausgaben der Messungen.

Aufruf (im Ordner der Demo):  python tools/bands_bauen.py <Ordner mit run_p02.log und out_v1_n30.txt> [--ohne-nachrechnung]

Quellen (jede Zeile der JSON-Dateien nennt ihre Quelle):
- run_p02.log            Teil A (180 Fälle, elementar), Teil A2 (dieselben Fälle, Gedächtnis k = 3), Teil B (Wachstum der Labels), Teil C (Spaltenerzeugung)
- run_p02_v0.log         Orakelvergleich der 180 Fälle (Zählung); steht in der Tabelle als Zusammenfassung
- out_v1_n30.txt         30 Kunden, ganze Spaltenerzeugung, Gedächtnis k = 1, 3, 5: Anteil der verworfenen Labels (Mittel über 6 Instanzen)

Die Spalten „Mittel“ und „Minimum“ des Faktors in Teil B stehen nicht in den Rohausgaben. Sie werden mit dem Kern der Demo nachgerechnet;
dabei muss der Median des Faktors und das Maximum mit run_p02.log übereinstimmen (sonst Abbruch), das ist zugleich die Prüfung, dass die
Kopie des Kerns dieselben Zahlen liefert wie die Messung. Mit --ohne-nachrechnung bleiben diese Felder leer (null)."""

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import dml_algorithm as A  # noqa: E402
from dml_scenario import make_instance, random_duals  # noqa: E402

RULE_KEYS = {
    "keine Dominanz": "keine",
    "nur Kosten": "kosten",
    "Kosten + Zeit": "kosten_zeit",
    "Kosten + Last": "kosten_last",
    "Kosten + Gedächtnis": "kosten_gedaechtnis",
    "Kosten + Zeit + Last": "kosten_zeit_last",
    "Kosten + Zeit + Gedächtnis": "kosten_zeit_gedaechtnis",
    "Kosten + Last + Gedächtnis": "kosten_last_gedaechtnis",
    "voll (Kosten, Zeit, Last, Gedächtnis)": "voll",
}
NUM = r"(-?\d+(?:\.\d+)?)"


def _de(text):
    return text.replace(",", ".")


def teil_a(lines):
    rows = []
    for line in lines:
        m = re.match(r"^(.+?)\s{2,}(\d+)\s+" + NUM + r"%\s+(\d+)\s+" + NUM + r"\s+(\d+)\s*$", line)
        if m and m.group(1) in RULE_KEYS:
            rows.append({"regel": RULE_KEYS[m.group(1)], "verfehlt": int(m.group(2)), "labels_median": int(m.group(4)), "labels_mittel": float(m.group(5)),
                         "labels_max": int(m.group(6)), "quelle": f"run_p02.log, Teil A, Zeile „{m.group(1)}“"})
    return rows


def teil_a2(lines):
    rows = []
    for line in lines:
        m = re.match(r"^(.+?)\s{2,}(\d+)\s+" + NUM + r"%\s+(\d+)\s+" + NUM + r"\s*$", line)
        if m and m.group(1) in RULE_KEYS:
            rows.append({"regel": RULE_KEYS[m.group(1)], "weicht_ab": int(m.group(2)), "labels_median": int(m.group(4)), "labels_mittel": float(m.group(5)),
                         "quelle": f"run_p02.log, Teil A2, Zeile „{m.group(1)}“"})
    return rows


def split_parts(text):
    parts = re.split(r"^== (Teil [A-Z0-9]+)", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        out[parts[i]] = parts[i + 1].splitlines()
    return out


def nachrechnen_faktor(n, width):
    factors = []
    for seed in range(10):
        inst = make_instance(n, seed, width)
        pi = random_duals(n, seed)
        a = A.price(inst, pi, n, None).generated
        b = A.price(inst, pi, n, A.RULES["voll"]).generated
        factors.append(a / b)
    return factors


def teil_b(lines, rechnen):
    rows = []
    for line in lines:
        m = re.match(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s*$", line)
        if not m:
            continue
        n, width = int(m.group(1)), int(m.group(2))
        row = {"breite": width, "n": n, "labels_ohne_median": int(m.group(3)), "labels_voll_median": int(m.group(4)), "faktor_median": float(m.group(5)),
               "faktor_max": float(m.group(6)), "faktor_mittel": None, "faktor_min": None, "instanzen": 10,
               "quelle": "run_p02.log, Teil B (Median, Maximum); Mittel und Minimum: Nachrechnung mit dem Kern der Demo (tools/bands_bauen.py)"}
        if rechnen:
            f = nachrechnen_faktor(n, width)
            assert round(statistics.median(f), 2) == row["faktor_median"], (n, width, statistics.median(f), row["faktor_median"])
            assert round(max(f), 2) == row["faktor_max"], (n, width, max(f), row["faktor_max"])
            row["faktor_mittel"] = round(statistics.mean(f), 2)
            row["faktor_min"] = round(min(f), 2)
        rows.append(row)
    return rows


def teil_c(lines):
    rows = []
    for line in lines:
        m = re.match(r"^\s*(\d+)\s+" + NUM + r"\s+" + NUM + r"\s+" + NUM + r"\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$", line)
        if m:
            rows.append({"seed": int(m.group(1)), "schranke_voll": float(m.group(2)), "schranke_kosten": float(m.group(3)), "unterschied_prozent": float(m.group(4)),
                         "labels_voll": int(m.group(5)), "labels_kosten": int(m.group(6)), "iterationen_voll": int(m.group(7)), "iterationen_kosten": int(m.group(8)),
                         "quelle": "run_p02.log, Teil C"})
    return rows


def v1(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        p = line.split()
        if len(p) >= 11:
            rows.append({"n": int(p[0]), "breite": int(p[1]), "seed": int(p[2]), "k": int(p[3]), "labels": int(p[8]), "dom": float(p[9]), "abgebrochen": int(p[10])})
    out = []
    for width in (40, 100, 200):
        for k in (1, 3, 5):
            sel = [r for r in rows if r["breite"] == width and r["k"] == k and not r["abgebrochen"]]
            out.append({"n": 30, "breite": width, "k": k, "laeufe": len(sel), "anteil_verworfen_prozent": round(100 * sum(r["dom"] for r in sel) / len(sel), 1),
                        "labels_median": round(statistics.median(r["labels"] for r in sel)), "quelle": "out_v1_n30.txt (Mittel der Anteile je Lauf über die Läufe ohne Abbruch)"})
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rechnen = "--ohne-nachrechnung" not in sys.argv
    src = Path(args[0])
    parts = split_parts((src / "run_p02.log").read_text(encoding="utf-8"))
    a_lines, a2_lines, b_lines, c_lines = parts["Teil A"], parts["Teil A2"], parts["Teil B"], parts["Teil C"]
    ratio_keine_voll = re.search(r"ohne Dominanz / mit voller Dominanz je Fall: Median " + NUM + ", Minimum " + NUM + ", Maximum " + NUM, "\n".join(a_lines))
    ratio_kosten = re.search(r"nur Kosten / voll je Fall: Median " + NUM + ", Minimum " + NUM + ", Maximum " + NUM, "\n".join(a_lines))
    miss = re.search(r"verfehlt: (\d+) Fälle; .*?Median " + NUM + ", Minimum " + NUM + ", Maximum " + NUM + r"; davon ohne jede verbessernde Route gefunden \(Wert 0\): (\d+)", "\n".join(a_lines))
    regeltabelle = {
        "quelle": "run_p02.log (Teil A, A2) und run_p02_v0.log",
        "faelle": 180, "instanzen": 60, "kunden": 7, "breiten": [30, 80, 200],
        "elementar": teil_a(a_lines), "ng3": teil_a2(a2_lines),
        "verhaeltnis_keine_zu_voll": {"median": float(ratio_keine_voll.group(1)), "min": float(ratio_keine_voll.group(2)), "max": float(ratio_keine_voll.group(3))},
        "verhaeltnis_kosten_zu_voll": {"median": float(ratio_kosten.group(1)), "min": float(ratio_kosten.group(2)), "max": float(ratio_kosten.group(3))},
        "verfehlung_nur_kosten": {"faelle": int(miss.group(1)), "wert_median": float(miss.group(2)), "wert_min": float(miss.group(3)), "wert_max": float(miss.group(4)),
                                  "ohne_verbessernde_route": int(miss.group(5))},
    }
    wachstum = {"quelle": "run_p02.log (Teil B) und out_v1_n30.txt", "teil_b": teil_b(b_lines, rechnen), "v1": v1(src / "out_v1_n30.txt")}
    spalten = {"quelle": "run_p02.log (Teil C)", "kunden": 10, "breite": 80, "instanzen": 10, "zeilen": teil_c(c_lines)}
    assert len(regeltabelle["elementar"]) == 9 and len(regeltabelle["ng3"]) == 9 and len(wachstum["teil_b"]) == 16 and len(spalten["zeilen"]) == 10
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    for name, obj in (("regeltabelle", regeltabelle), ("wachstum", wachstum), ("spaltenerzeugung", spalten)):
        (out / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("geschrieben:", out / f"{name}.json")


if __name__ == "__main__":
    main()
