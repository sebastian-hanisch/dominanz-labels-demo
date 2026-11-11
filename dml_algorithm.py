"""Kern der Demo: Label-Setting mit wählbarer Dominanzregel (reines Python, Standardbibliothek).

Aufgabe: den Weg mit den kleinsten **reduzierten Kosten** finden (Weglänge minus Dualpreise der besuchten Kunden), mit Last-, Zeitfenster- und
Horizontgrenze. Ein **Label** hält einen Teilweg fest: Zeit, Kosten, Last, Gedächtnis (welche Kunden nicht noch einmal besucht werden dürfen).

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b): `dominates` (die Dominanzregel), `conditions`
(die vier Einzelbedingungen für die Anzeige), `extend` (Zulässigkeit einer Fortsetzung), `ng_masks` (Gedächtnis), `price` (nur die Schleife
in Zeitreihenfolge). `enumerate_routes` ist der Vergleichsweg ohne Labels (Tiefensuche über alle Routen). Kein versteckter Zustand,
kein Zufall im Kern: Instanzen und Dualpreise kommen fertig herein.

Die Messgröße der Demo ist die Zahl der erzeugten Labels (jedes erzeugte Label, auch ein sofort verworfenes, plus das Start-Label), nicht die Zeit."""

import heapq
from typing import NamedTuple

from dml_scenario import Instance

EPS = 1e-9            # Toleranz für Vergleiche von Kosten und Zeiten (Gleitkomma)
IMPROVING = -1e-7     # eine Route zählt als verbessernd, wenn ihre reduzierten Kosten darunter liegen

# Zusätzliche Bedingungen der Dominanz; die Kosten werden bei jeder Regel verglichen.
TIME, LOAD, MEMORY = "Z", "Q", "M"
RULES = {
    "keine": None,                                   # nichts wird gestrichen
    "kosten": frozenset(),                           # nur Kosten
    "kosten_zeit": frozenset({TIME}),
    "kosten_last": frozenset({LOAD}),
    "kosten_gedaechtnis": frozenset({MEMORY}),
    "kosten_zeit_last": frozenset({TIME, LOAD}),
    "kosten_zeit_gedaechtnis": frozenset({TIME, MEMORY}),
    "kosten_last_gedaechtnis": frozenset({LOAD, MEMORY}),
    "voll": frozenset({TIME, LOAD, MEMORY}),         # die vier Bedingungen zusammen
}
CONDITION_NAMES = ("Kosten", "Zeit", "Last", "Gedächtnis")


class Label(NamedTuple):
    time: float     # Beginn der Bedienung am Knoten (nach Warten)
    cost: float     # reduzierte Kosten des Teilwegs
    load: int       # verbrauchte Last
    mem: int        # Bitmaske: Kunden, die nicht noch einmal besucht werden dürfen
    node: int       # letzter Kunde (0 = Start im Depot)
    parent: int     # Nummer des Vorgänger-Labels, -1 beim Start


class Event(NamedTuple):
    """Eine Entscheidung der Dominanzprüfung.

    kind "bleibt":     das neue Label `label` bleibt (partner = -1);
    kind "verworfen":  das neue Label `label` wird vom älteren Label `partner` dominiert;
    kind "verdraengt": das ältere Label `label` entfällt, weil das neue Label `partner` es dominiert."""

    kind: str
    label: int
    partner: int


class PriceResult(NamedTuple):
    value: float                  # kleinster reduzierter Kostenwert aller gefundenen Routen; 0, wenn keine Route unter IMPROVING liegt
    route: tuple[int, ...]        # zugehörige Route (ohne Depot); () bei value == 0
    generated: int                # erzeugte Labels inklusive Start-Label
    dominated: int                # davon durch Dominanz verloren (neue Labels, die gar nicht erst blieben, und verdrängte ältere)
    labels: tuple[Label, ...]     # alle erzeugten Labels in der Reihenfolge der Erzeugung (Nummer = Index)
    dead: tuple[bool, ...]        # Label am Ende gestrichen?
    ended: tuple[tuple[float, int], ...]   # (reduzierte Kosten einschließlich Rückfahrt, Nummer des letzten Labels) je Route, die ins Depot zurückkehren kann
    events: tuple[Event, ...]     # Entscheidungen in der Reihenfolge der Erzeugung (nur mit trace=True)
    aborted: bool                 # Abbruch bei max_labels

    @property
    def alive(self) -> int:
        return self.generated - self.dominated


def ng_masks(inst: Instance, k: int) -> list[int]:
    """Gedächtnis NG(j): die k nächsten Kunden von j (j selbst eingeschlossen). k = n heißt: jeder besuchte Kunde bleibt im Gedächtnis (elementar)."""
    k = max(1, min(k, inst.n))
    masks = [0] * (inst.n + 1)
    for j in range(1, inst.n + 1):
        order = sorted(range(1, inst.n + 1), key=lambda i: inst.d[j][i])
        m = 0
        for i in order[:k]:
            m |= 1 << i
        masks[j] = m | (1 << j)
    return masks


def dominates(o: Label, new: Label, rule: frozenset) -> bool:
    """Dominiert Label `o` das Label `new` (am selben Knoten)? Kosten immer, dazu Zeit, Last, Gedächtnis je nach Regel.
    Gedächtnis heißt: die besuchten Kunden von `o` sind eine Teilmenge der von `new`."""
    if o.cost > new.cost + EPS:
        return False
    if TIME in rule and o.time > new.time + EPS:
        return False
    if LOAD in rule and o.load > new.load:
        return False
    if MEMORY in rule and (o.mem & ~new.mem) != 0:
        return False
    return True


def conditions(o: Label, new: Label) -> dict[str, bool]:
    """Die vier Einzelbedingungen der vollen Regel für `o` gegenüber `new` (True = erfüllt), in der Reihenfolge CONDITION_NAMES."""
    return {
        "Kosten": o.cost <= new.cost + EPS,
        "Zeit": o.time <= new.time + EPS,
        "Last": o.load <= new.load,
        "Gedächtnis": (o.mem & ~new.mem) == 0,
    }


def extend(inst: Instance, pi, ng: list[int], label: Label, parent: int, j: int) -> Label | None:
    """Fortsetzung von `label` (Nummer `parent`) zum Kunden j, oder None, wenn sie unzulässig ist (Kunde im Gedächtnis, Last, Zeitfenster).
    Ankunft vor dem Fenster heißt warten (kostenlos). Die Rückkehr ins Depot prüft `price` beim Abschluss."""
    i = label.node
    if j == i or (label.mem >> j) & 1:
        return None
    load = label.load + inst.demand[j]
    if load > inst.capacity:
        return None
    arrival = label.time + (inst.service if i != 0 else 0) + inst.d[i][j]
    if arrival > inst.due[j] + EPS:
        return None
    return Label(max(arrival, inst.ready[j]), label.cost + inst.d[i][j] - pi[j], load, (label.mem & ng[j]) | (1 << j), j, parent)


def route_of(labels, index: int) -> tuple[int, ...]:
    """Route (ohne Depot) des Labels mit der Nummer `index`."""
    route = []
    while index != -1:
        route.append(labels[index].node)
        index = labels[index].parent
    return tuple(reversed(route))[1:]


def price(inst: Instance, pi, k: int, rule: frozenset | None, trace: bool = False, max_labels: int | None = None) -> PriceResult:
    """Label-Setting in Zeitreihenfolge. `rule`: None (keine Dominanz) oder eine Menge aus {TIME, LOAD, MEMORY} (Kosten immer dabei).

    Ein neues Label wird verworfen, wenn ein lebendes Label am selben Kunden es dominiert (bei Gleichstand bleibt das ältere);
    sonst verdrängt es alle lebenden Labels, die es dominiert. `k` ist die Größe des Gedächtnisses (k = n: elementar)."""
    ng = ng_masks(inst, k)
    labels = [Label(0, 0, 0, 0, 0, -1)]
    dead = [False]
    at_node: list[list[int]] = [[] for _ in range(inst.n + 1)]
    heap = [(0, 0)]
    dominated = 0
    ended: list[tuple[float, int]] = []
    events: list[Event] = []
    aborted = False
    while heap:
        _, li = heapq.heappop(heap)
        if dead[li]:
            continue
        label = labels[li]
        i = label.node
        if i != 0 and label.time + inst.service + inst.d[i][0] <= inst.horizon:
            ended.append((label.cost + inst.d[i][0], li))
        for j in range(1, inst.n + 1):
            new = extend(inst, pi, ng, label, li, j)
            if new is None:
                continue
            nid = len(labels)
            labels.append(new)
            dead.append(False)
            if rule is not None:
                lost_to = next((o for o in at_node[j] if dominates(labels[o], new, rule)), None)
                if lost_to is not None:
                    dead[nid] = True
                    dominated += 1
                    if trace:
                        events.append(Event("verworfen", nid, lost_to))
                    continue
                survivors = []
                for o in at_node[j]:
                    if dominates(new, labels[o], rule):
                        dead[o] = True
                        dominated += 1
                        if trace:
                            events.append(Event("verdraengt", o, nid))
                    else:
                        survivors.append(o)
                at_node[j] = survivors
            at_node[j].append(nid)
            heapq.heappush(heap, (new.time, nid))
            if trace:
                events.append(Event("bleibt", nid, -1))
            if max_labels is not None and len(labels) >= max_labels:
                aborted = True
                break
        if aborted:
            break
    best_value, best_route = 0, ()
    candidates = sorted((rc, route_of(labels, li)) for rc, li in ended if rc < IMPROVING)
    if candidates:
        best_value, best_route = candidates[0]
    return PriceResult(best_value, best_route, len(labels), dominated, tuple(labels), tuple(dead), tuple(ended), tuple(events), aborted)


def routes_of(result: PriceResult, limit: int = 15) -> list[tuple[float, tuple[int, ...]]]:
    """Die besten verschiedenen verbessernden Routen eines Laufs (reduzierte Kosten, Route), aufsteigend; Grundlage für neue Spalten."""
    found: dict[tuple[int, ...], float] = {}
    for rc, li in result.ended:
        if rc < IMPROVING:
            found.setdefault(route_of(result.labels, li), rc)
    return sorted((rc, route) for route, rc in found.items())[:limit]


def enumerate_routes(inst: Instance, pi) -> list[tuple[float, tuple[int, ...], float]]:
    """Vergleichsweg ohne Labels: alle zulässigen elementaren Routen (Tiefensuche), sortiert nach reduzierten Kosten, als (Kosten, Route, Rückkehrzeit)."""
    routes: list[tuple[float, tuple[int, ...], float]] = []

    def visit(i: int, time: float, load: int, visited: int, cost: float, path: tuple[int, ...]) -> None:
        if i != 0 and time + inst.service + inst.d[i][0] <= inst.horizon:
            routes.append((cost + inst.d[i][0], path, time + inst.service + inst.d[i][0]))
        for j in range(1, inst.n + 1):
            if (visited >> j) & 1 or load + inst.demand[j] > inst.capacity:
                continue
            arrival = time + (inst.service if i != 0 else 0) + inst.d[i][j]
            if arrival > inst.due[j] + EPS:
                continue
            visit(j, max(arrival, inst.ready[j]), load + inst.demand[j], visited | (1 << j), cost + inst.d[i][j] - pi[j], path + (j,))

    visit(0, 0, 0, 0, 0, ())
    return sorted(routes)


def best_by_enumeration(inst: Instance, pi) -> tuple[float, tuple[int, ...]]:
    """Bester Wert und Route aller zulässigen elementaren Routen; (0, ()) , wenn keine verbessernd ist."""
    routes = enumerate_routes(inst, pi)
    if routes and routes[0][0] < IMPROVING:
        return routes[0][0], routes[0][1]
    return 0, ()


def route_value(inst: Instance, pi, route) -> float | None:
    """Unabhängiger Prüfer: reduzierte Kosten einer Route, oder None, wenn sie unzulässig ist (Kunde doppelt, Last, Zeitfenster, Horizont)."""
    route = tuple(route)
    if len(set(route)) != len(route) or any(not 1 <= j <= inst.n for j in route):
        return None
    time, load, cost, prev = 0, 0, 0, 0
    for j in route:
        arrival = time + (inst.service if prev != 0 else 0) + inst.d[prev][j]
        load += inst.demand[j]
        if arrival > inst.due[j] + EPS or load > inst.capacity:
            return None
        time = max(arrival, inst.ready[j])
        cost += inst.d[prev][j] - pi[j]
        prev = j
    if route:
        if time + inst.service + inst.d[prev][0] > inst.horizon:
            return None
        cost += inst.d[prev][0]
    return cost
