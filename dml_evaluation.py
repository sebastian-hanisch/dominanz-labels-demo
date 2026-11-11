"""Kennzahlen, Verdikte (reine Funktionen) und Messreihen der Demo.

Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft
Schwellen und jede Zahl im Text an handgesetzten Werten. Die festen Messreihen (data/*.json) laden `load_*`; jede Zeile nennt ihre Quelle."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import dml_algorithm as A
import dml_constants as C
from dml_scenario import HAND_DUALS, Instance, hand_instance, make_general_instance, make_instance, random_duals

DATA_DIR = Path(__file__).resolve().parent / "data"


# --- Zahlen und Mengen als Text -------------------------------------------------------------------------------------------------------------

def fmt_num(x, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und echtem Minuszeichen; ganze Zahlen ohne Nachkommastellen."""
    if float(x).is_integer():
        text = f"{int(x)}"
    else:
        text = f"{x:.{digits}f}".replace(".", ",")
    return text.replace("-", "−")


def fmt_dec(x: float, digits: int = 2) -> str:
    """Dezimalzahl mit immer gleich vielen Nachkommastellen und deutschem Komma (1,00 statt 1)."""
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(n: int) -> str:
    """Ganze Zahl mit geschütztem Leerzeichen als Tausendertrenner (4 424 statt 4424)."""
    return f"{n:,}".replace(",", " ")


def fmt_pct(x: float, digits: int = 1) -> str:
    """Prozentwert mit deutschem Dezimalkomma (x ist schon in Prozent)."""
    return f"{x:.{digits}f}".replace(".", ",") + " %"


def fmt_set(mem: int, n: int) -> str:
    """Menge der Kunden (Bitmaske) als {1,3,5}."""
    return "{" + ",".join(str(i) for i in range(1, n + 1) if (mem >> i) & 1) + "}"


def fmt_route(route) -> str:
    return "-".join(str(i) for i in route) if route else "keine"


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class HandAnalysis:
    inst: Instance
    pi: tuple
    rule: str                       # Schlüssel in A.RULES
    result: A.PriceResult           # mit Protokoll der Entscheidungen
    routes: tuple                   # alle zulässigen elementaren Routen (Kosten, Route, Rückkehrzeit), sortiert
    best_value: float
    best_route: tuple
    unique: bool                    # ist der beste Weg eindeutig?
    correct: bool                   # findet die Regel genau den besten Weg (Wert und Route)?


def analyse_hand(rule: str) -> HandAnalysis:
    """Handbeispiel mit der gewählten Regel (Gedächtnis k = n, also elementar) und die Aufzählung aller Routen als Vergleich."""
    inst = hand_instance()
    routes = tuple(A.enumerate_routes(inst, HAND_DUALS))
    best_value, best_route, _ = routes[0]
    unique = len(routes) < 2 or routes[1][0] > best_value
    result = A.price(inst, HAND_DUALS, inst.n, A.RULES[rule], trace=True)
    correct = result.value == best_value and result.route == best_route
    return HandAnalysis(inst, tuple(HAND_DUALS), rule, result, routes, best_value, best_route, unique, correct)


def compare_rules(rules=C.LIVE_RULES) -> list[dict]:
    """Zeile je Regel für das Handbeispiel: bester Wert, Route, erzeugte, gestrichene und lebende Labels, richtig oder falsch."""
    rows = []
    for rule in rules:
        a = analyse_hand(rule)
        rows.append({"rule": rule, "value": a.result.value, "route": a.result.route, "generated": a.result.generated,
                     "dominated": a.result.dominated, "alive": a.result.alive, "correct": a.correct})
    return rows


def label_text(inst: Instance, result: A.PriceResult, index: int) -> str:
    """L8 (Weg 1-5, Zeit 17, Kosten −4, Last 4, besucht {1,5})."""
    label = result.labels[index]
    route = fmt_route(A.route_of(result.labels, index))
    return (f"L{index} (Weg {route}, Zeit {fmt_num(label.time)}, Kosten {fmt_num(label.cost)}, Last {label.load}, "
            f"besucht {fmt_set(label.mem, inst.n)})")


def short_label(result: A.PriceResult, index: int) -> str:
    """L8 (Weg 1-5): Nummer und Weg, für die Spalten der Ereignistabelle (alle Zahlen stehen in den Vergleichen daneben)."""
    return f"L{index} (Weg {fmt_route(A.route_of(result.labels, index))})"


def condition_text(name: str, o: A.Label, new: A.Label, n: int) -> tuple[bool, str]:
    """(erfüllt, Text) für eine der vier Bedingungen: `o` soll `new` dominieren, Text als Vergleich `o ≤ new` bzw. `o > new`."""
    if name == "Kosten":
        ok, a, b = A.conditions(o, new)["Kosten"], fmt_num(o.cost), fmt_num(new.cost)
    elif name == "Zeit":
        ok, a, b = A.conditions(o, new)["Zeit"], fmt_num(o.time), fmt_num(new.time)
    elif name == "Last":
        ok, a, b = A.conditions(o, new)["Last"], str(o.load), str(new.load)
    else:
        ok = A.conditions(o, new)["Gedächtnis"]
        return ok, f"{fmt_set(o.mem, n)} {'⊆' if ok else '⊄'} {fmt_set(new.mem, n)}"
    return ok, f"{a} {'≤' if ok else '>'} {b}"


def checked_conditions(rule: str) -> tuple[str, ...]:
    """Die Bedingungen, die die Regel tatsächlich prüft (Kosten immer), in der Reihenfolge CONDITION_NAMES."""
    letters = A.RULES[rule]
    if letters is None:
        return ()
    names = ["Kosten"]
    if A.TIME in letters:
        names.append("Zeit")
    if A.LOAD in letters:
        names.append("Last")
    if A.MEMORY in letters:
        names.append("Gedächtnis")
    return tuple(names)


def event_rows(a: HandAnalysis, show_all: bool = False) -> list[dict]:
    """Eine Zeile je Entscheidung der Dominanzprüfung (Label gestrichen oder verdrängt); mit show_all auch je Label, das bleibt.
    Die vier Vergleiche stehen für das dominierende Label gegenüber dem gestrichenen Label (erfüllt: ✓, verletzt: ✗)."""
    inst, res = a.inst, a.result
    rows = []
    for e in res.events:
        if e.kind == "bleibt":
            if show_all:
                rows.append({"Ereignis": "bleibt", "Gestrichenes Label": short_label(res, e.label) + " (bleibt)", "Dominierendes Label": "", "ok": None,
                             **{name: "" for name in A.CONDITION_NAMES}, "Zu großzügig": ""})
            continue
        dom, lost = res.labels[e.partner], res.labels[e.label]
        row = {"Ereignis": "neues Label verworfen" if e.kind == "verworfen" else "älteres entfällt", "Gestrichenes Label": short_label(res, e.label),
               "Dominierendes Label": short_label(res, e.partner) + (" (neu)" if e.kind == "verdraengt" else "")}
        ok_all = True
        for name in A.CONDITION_NAMES:
            ok, text = condition_text(name, dom, lost, inst.n)
            row[name] = f"{text} {'✓' if ok else '✗'}"
            ok_all &= ok
        row["ok"] = ok_all
        row["Zu großzügig"] = "nein" if ok_all else "ja"
        rows.append(row)
    return rows


class Loss(NamedTuple):
    prefix: tuple[int, ...]       # Vorstufe des besten Weges, die verloren geht
    lost: int                     # Nummer des gestrichenen Labels
    dominator: int                # Nummer des Labels, das es nach der Regel dominiert
    violated: tuple[str, ...]     # Bedingungen der vollen Regel, die das dominierende Label verletzt (Text je Bedingung)


def first_loss(a: HandAnalysis) -> Loss | None:
    """Die erste Vorstufe des besten Weges, die die Regel streicht, und die Bedingungen der vollen Regel, die dabei verletzt sind; None, wenn keine verloren geht."""
    res, inst = a.result, a.inst
    by_route: dict[tuple[int, ...], A.Event] = {}
    for e in res.events:
        if e.kind in ("verworfen", "verdraengt"):
            by_route.setdefault(A.route_of(res.labels, e.label), e)
    for k in range(1, len(a.best_route) + 1):
        prefix = a.best_route[:k]
        e = by_route.get(prefix)
        if e is not None:
            dom, lost = res.labels[e.partner], res.labels[e.label]
            violated = tuple(f"{name}: {text}" for name in A.CONDITION_NAMES
                             for ok, text in [condition_text(name, dom, lost, inst.n)] if not ok)
            return Loss(prefix, e.label, e.partner, violated)
    return None


# --- Größenversuch (live) -------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class RunStats:
    rule: str
    generated: int                 # erzeugte Labels inklusive Start-Label
    dominated: int
    value: float
    route: tuple
    aborted: bool
    alive_per_customer: tuple      # Labels je Kunde 1..n, die am Ende leben (ohne Start-Label)
    dominated_per_customer: tuple  # Labels je Kunde 1..n, die gestrichen sind


@dataclass(frozen=True)
class SizeResult:
    n: int
    width: int
    seed: int
    runs: dict                     # {"keine": RunStats, "voll": RunStats}

    @property
    def aborted(self) -> bool:
        return any(r.aborted for r in self.runs.values())

    @property
    def factor(self) -> float | None:
        """Labels ohne Dominanz durch Labels mit voller Dominanz; None bei Abbruch."""
        return None if self.aborted else self.runs["keine"].generated / self.runs["voll"].generated

    @property
    def same_value(self) -> bool | None:
        return None if self.aborted else abs(self.runs["keine"].value - self.runs["voll"].value) < 1e-6


def run_stats(rule: str, inst: Instance, pi, max_labels: int | None = C.MAX_LABELS) -> RunStats:
    res = A.price(inst, pi, inst.n, A.RULES[rule], max_labels=max_labels)
    alive = [0] * inst.n
    dead = [0] * inst.n
    for index in range(1, res.generated):
        (dead if res.dead[index] else alive)[res.labels[index].node - 1] += 1
    return RunStats(rule, res.generated, res.dominated, res.value, res.route, res.aborted, tuple(alive), tuple(dead))


def size_experiment(n: int, width: int, seed: int, max_labels: int | None = C.MAX_LABELS) -> SizeResult:
    """Dieselbe Zufallsinstanz (n Kunden, Fensterbreite, Zufalls-Seed) mit den zufällig gezogenen Dualpreisen ohne und mit voller Dominanz, elementar."""
    inst = make_instance(n, seed, width)
    pi = random_duals(n, seed)
    return SizeResult(n, width, seed, {rule: run_stats(rule, inst, pi, max_labels) for rule in C.RUN_RULES})


# --- Gegenprobe mit zufälligen Fahrzeiten (Dreiecksungleichung nicht erzwungen) ----------------------------------------------------------------------------------------------------

COUNTER_RULES = ("kosten", "kosten_zeit", "kosten_last", "kosten_gedaechtnis", "kosten_zeit_last", "voll")
COUNTER_INSTANCES = 3000


def counter_sweep(count: int = COUNTER_INSTANCES, rules=COUNTER_RULES) -> dict[str, list[int]]:
    """Gegenprobe: Zufalls-Seeds 0 bis count - 1 der Instanzen aus `make_general_instance` (6 Kunden, beliebige Fahrzeiten, schmale Fenster).
    Je Regel die Zufalls-Seeds, bei denen sie den besten Weg (Aufzählung aller Routen) verfehlt."""
    missed: dict[str, list[int]] = {rule: [] for rule in rules}
    for seed in range(count):
        inst, pi = make_general_instance(seed)
        best = A.best_by_enumeration(inst, pi)[0]
        for rule in rules:
            if abs(A.price(inst, pi, inst.n, A.RULES[rule]).value - best) > 1e-6:
                missed[rule].append(seed)
    return missed


# --- Feste Messreihen -----------------------------------------------------------------------------------------------------------------------

def _load(name: str) -> dict:
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def load_rule_table() -> dict:
    return _load("regeltabelle")


def load_growth() -> dict:
    return _load("wachstum")


def load_colgen() -> dict:
    return _load("spaltenerzeugung")


def rule_rows(table: dict, key: str = "elementar") -> list[dict]:
    """Zeilen der Regel-Tabelle in der Reihenfolge C.TABLE_RULES; `key` ist "elementar" (k = n) oder "ng3" (Gedächtnis k = 3)."""
    by_rule = {r["regel"]: r for r in table[key]}
    return [by_rule[rule] for rule in C.TABLE_RULES]


def colgen_summary(rows: list[dict]) -> dict:
    """Zahl der Instanzen, in denen „nur Kosten“ bei einer höheren Zahl endet als die volle Regel, und Mittel und Maximum des Unterschieds in Prozent
    (Unterschied = Schranke „nur Kosten“ minus Schranke der vollen Regel, geteilt durch die Schranke der vollen Regel; Mittel über alle Instanzen der Messreihe, auch die mit Unterschied 0)."""
    diffs = [r["unterschied_prozent"] for r in rows]
    return {"instanzen": len(rows), "hoeher": sum(1 for d in diffs if d > 1e-9), "mittel": sum(diffs) / len(diffs), "maximum": max(diffs)}


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def equal_value_routes(a: HandAnalysis) -> tuple:
    """Die anderen Routen der Aufzählung, die genau den Wert haben, den die Regel findet; leer, wenn die Regel den besten Wert findet oder keine Route fand."""
    if a.result.value == a.best_value or not a.result.route:
        return ()
    return tuple(r for v, r, _ in a.routes if v == a.result.value and r != a.result.route)


def verdict_hand(rule_label: str, value, route, best_value, best_route, n_routes: int, generated: int, dominated: int, equal_routes: tuple = ()) -> tuple[str, str]:
    """Findet die gewählte Regel den besten Weg des Handbeispiels? Vergleich mit der Aufzählung aller zulässigen Routen.
    `equal_routes`: weitere Routen der Aufzählung mit demselben (schlechteren) Wert wie der gefundene; sie werden im Fehlertext genannt."""
    if value == best_value and route == best_route:
        return "success", (f"Die Regel „{rule_label}“ findet den besten Weg {fmt_route(route)} mit reduzierten Kosten {fmt_num(value)}, wie die Aufzählung aller "
                           f"{n_routes} zulässigen Routen. Sie erzeugt {generated} Labels, {dominated} davon werden gestrichen.")
    equal = ""
    if equal_routes:
        named = " und ".join(fmt_route(r) for r in equal_routes)
        equal = f" Mit demselben Wert {fmt_num(value)} kennt die Aufzählung auch {'die Route' if len(equal_routes) == 1 else 'die Routen'} {named}; die Regel gibt {fmt_route(route)} aus."
    return "error", (f"Die Regel „{rule_label}“ verfehlt den besten Weg: Sie findet {fmt_route(route)} mit {fmt_num(value)}, die Aufzählung aller {n_routes} "
                     f"zulässigen Routen findet {fmt_route(best_route)} mit {fmt_num(best_value)}.{equal} Sie erzeugt {generated} Labels und streicht {dominated}.")


def verdict_decisions(rule_label: str, decisions: int, too_generous: int) -> tuple[str, str]:
    """Wie viele der Streichungen verletzen mindestens eine der vier Bedingungen der vollen Regel?"""
    if decisions == 0:
        return "info", f"Mit der Regel „{rule_label}“ wird nichts gestrichen: Es gibt keine Entscheidung zu prüfen."
    if too_generous == 0:
        return "success", f"Alle {decisions} Streichungen erfüllen alle vier Bedingungen: Kein gestrichenes Label war der Anfang eines Weges, den ein anderes Label nicht mindestens ebenso gut fortsetzen kann."
    return "warning", (f"{too_generous} von {decisions} Streichungen verletzen mindestens eine der vier Bedingungen (rote Zellen): Dort streicht die Regel „{rule_label}“ "
                       f"ein Label, das ein anderes Label in Zeit, Last oder besuchten Kunden nicht ersetzt.")


def verdict_loss(rule_label: str, best_route, loss: Loss | None) -> tuple[str, str]:
    if loss is None:
        return "success", f"Bei der Regel „{rule_label}“ geht keine Vorstufe des besten Weges {fmt_route(best_route)} verloren."
    return "error", (f"Bei der Regel „{rule_label}“ geht der beste Weg {fmt_route(best_route)} schon an der Vorstufe {fmt_route(loss.prefix)} verloren: "
                     f"Das Label L{loss.lost} wird von L{loss.dominator} gestrichen, das {len(loss.violated)} der vier Bedingungen verletzt.")


def verdict_losses(n_wrong: int, n_rules: int) -> tuple[str, str]:
    """Experiment 2 insgesamt: bei wie vielen der wählbaren Regeln geht der beste Weg verloren?"""
    if n_wrong == 0:
        return "success", f"Bei keiner der {n_rules} wählbaren Regeln geht der beste Weg des Handbeispiels verloren."
    each = "in diesem Fall" if n_wrong == 1 else "in beiden Fällen" if n_wrong == 2 else f"in allen {n_wrong} Fällen"
    return "info", (f"Im Handbeispiel geht der beste Weg bei {n_wrong} der {n_rules} wählbaren Regeln verloren; {each} erfüllt ein dominierendes Label "
                    f"nicht alle vier Bedingungen der vollen Regel.")


def verdict_rule_table(rows_el: list[dict], rows_ng: list[dict], cases: int) -> tuple[str, str]:
    """Experiment 3: Zählungen aus der Messreihe (180 Fälle mit 7 Kunden)."""
    el = {r["regel"]: r for r in rows_el}
    ng = {r["regel"]: r for r in rows_ng}
    return "info", (f"Bei {cases} Fällen mit 7 Kunden verfehlt „nur Kosten“ den besten Weg in {el['kosten']['verfehlt']} Fällen "
                    f"({fmt_pct(100 * el['kosten']['verfehlt'] / cases)}), die volle Regel in {el['voll']['verfehlt']}. Bei Wegen ohne Wiederholung (elementar) "
                    f"verfehlt „Kosten + Gedächtnis“ ihn in {el['kosten_gedaechtnis']['verfehlt']} Fällen. Mit dem lockereren Gedächtnis k = 3 weicht diese Regel in "
                    f"{ng['kosten_gedaechtnis']['weicht_ab']} Fällen vom Ergebnis ohne Dominanz ab; dort weicht erst die volle Regel in keinem Fall ab ({ng['voll']['weicht_ab']} Fälle).")


def verdict_counter(missed: dict[str, list[int]], count: int) -> tuple[str, str]:
    """Gegenprobe zu Experiment 3: Instanzen mit zufälligen Fahrzeiten (Dreiecksungleichung nicht erzwungen). Zählt die Instanzen, in denen „Kosten + Gedächtnis“ und die volle Regel den besten Weg verfehlen."""
    mem, full = len(missed["kosten_gedaechtnis"]), len(missed["voll"])
    if mem == 0:
        return "info", (f"Auch bei {fmt_int(count)} Instanzen mit zufälligen, nicht symmetrischen Fahrzeiten (Dreiecksungleichung nicht erzwungen) verfehlt „Kosten + Gedächtnis“ den besten Weg nie; die volle Regel ebenfalls nicht "
                        f"({full} Fälle).")
    seeds = ", ".join(str(s) for s in missed["kosten_gedaechtnis"][:3])
    return "warning", (f"Bei {fmt_int(count)} Instanzen mit zufälligen, nicht symmetrischen Fahrzeiten (Dreiecksungleichung nicht erzwungen) verfehlt „Kosten + Gedächtnis“ den besten Weg in {mem} {"Fall" if mem == 1 else "Fällen"} (Zufalls-Seed {seeds}"
                       f"{', …' if mem > 3 else ''}), die volle Regel in {full}. Dass „Kosten + Gedächtnis“ in der Tabelle keinen Fall verfehlt, ist eine Beobachtung an diesen Instanzen "
                       f"(Fahrzeit gleich Entfernung), kein Satz. Die Gegenprobe ändert zugleich Fahrzeiten, Kundenzahl (6 statt 7) und Fensterbreite; "
                       f"ob die Dreiecksungleichung die Ursache ist, ist nicht untersucht.")


def verdict_size(n: int, width: int, labels_none: int, labels_full: int, dominated_full: int, aborted: bool, limit: int = C.MAX_LABELS) -> tuple[str, str]:
    """Experiment 4: spart die Dominanz bei dieser Instanz Labels? Faktor = Labels ohne durch Labels mit voller Dominanz; unter C.EQUAL_FACTOR gilt „gleichauf“."""
    if aborted:
        return "warning", (f"Abbruch bei {fmt_int(limit)} erzeugten Labels: Bei n = {n} Kunden und Fensterbreite {width} ist dieser Lauf für die Live-Rechnung zu groß. "
                           f"Die festen Messreihen darunter gelten weiter.")
    factor = labels_none / labels_full
    if factor < C.EQUAL_FACTOR:
        return "info", (f"Bei n = {n} Kunden und Fensterbreite {width} sparen die Streichregeln bei dieser Instanz kaum etwas: {fmt_int(labels_none)} Labels ohne, "
                        f"{fmt_int(labels_full)} mit voller Dominanz (Faktor {fmt_num(factor)}; unter {fmt_num(C.EQUAL_FACTOR, 1)} gilt hier als gleichauf).")
    return "info", (f"Bei n = {n} Kunden und Fensterbreite {width} erzeugt die Rechnung ohne Dominanz {fmt_int(labels_none)} Labels, mit voller Dominanz "
                    f"{fmt_int(labels_full)}: das {fmt_num(factor)}-Fache. Mit voller Dominanz werden {fmt_pct(100 * dominated_full / labels_full)} der erzeugten Labels gestrichen.")


def verdict_colgen(summary: dict) -> tuple[str, str]:
    """Experiment 5: endet die Spaltenerzeugung mit „nur Kosten“ bei einer höheren Zahl als mit der vollen Regel?"""
    if summary["hoeher"] == 0:
        return "success", f"In allen {summary['instanzen']} Instanzen endet die Spaltenerzeugung mit „nur Kosten“ bei derselben Zahl wie mit der vollen Regel."
    return "warning", (f"Mit „nur Kosten“ endet die Spaltenerzeugung in {summary['hoeher']} von {summary['instanzen']} Instanzen bei einer höheren Zahl als mit der "
                       f"vollen Regel (Abstand zur Schranke der vollen Regel, bezogen auf diese: Mittel {fmt_pct(summary['mittel'], 3)}, Maximum {fmt_pct(summary['maximum'], 3)}; "
                       f"das Mittel läuft über alle {summary['instanzen']} Instanzen, auch über die {summary['instanzen'] - summary['hoeher']} ohne Unterschied). "
                       f"Diese Zahl ist dann keine gültige Untergrenze mehr, weil Spalten fehlen.")
