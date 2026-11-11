"""Szenario: Instanzen für das Label-Verfahren (ein Depot, Kunden mit Last, Zeitfenster und Dualpreis).

Zwei Arten von Instanzen:
- das **Handbeispiel** (6 Kunden auf einem Gitter, Manhattan-Abstand, ganze Zahlen; von Hand nachrechenbar),
- **Zufallsinstanzen** im Stil der Solomon-Instanzen (Quadrat 100 x 100, Fahrzeit = Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300;
  nicht die Originalinstanzen). `make_instance` zieht die Zahlen in derselben Reihenfolge wie die Messreihen der Planung, damit
  die festen Zufalls-Seeds dieselben Instanzen ergeben."""

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Instance:
    """Knoten 0 ist das Depot, die Kunden sind 1..n. Alle Tupel haben die Länge n + 1."""

    n: int
    points: tuple[tuple[float, float], ...]
    d: tuple[tuple[float, ...], ...]   # Entfernung = Fahrzeit
    demand: tuple[int, ...]
    ready: tuple[float, ...]           # frühester Beginn der Bedienung (früher ankommen heißt warten, kostenlos)
    due: tuple[float, ...]             # spätester Beginn der Bedienung
    service: float                     # Bedienzeit je Kunde
    horizon: float                     # spätestmögliche Rückkehr ins Depot
    capacity: int


def make_instance(n: int, seed: int, width: float, horizon: float = 300.0, capacity: int = 70, service: float = 10.0) -> Instance:
    """Zufallsinstanz aus (n, seed, Fensterbreite): gleiche Eingabe, gleiche Instanz (Zufallsgenerator `random.Random(seed)`)."""
    rng = random.Random(seed)
    customers = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    points = [(50.0, 50.0)] + customers
    d = tuple(tuple(math.dist(a, b) for b in points) for a in points)
    demand = [0] + [rng.randint(5, 25) for _ in range(n)]
    ready = [0.0] * (n + 1)
    due = [horizon] * (n + 1)
    for i in range(1, n + 1):
        lo = d[0][i]
        hi = horizon - service - d[0][i]
        center = rng.uniform(lo, hi)
        ready[i] = max(lo, center - width / 2)
        due[i] = min(hi, center + width / 2)
    return Instance(n, tuple(points), d, tuple(demand), tuple(ready), tuple(due), service, horizon, capacity)


def random_duals(n: int, seed: int) -> tuple[float, ...]:
    """Dualpreise der Kunden: gleichverteilt zwischen 20 und 70, Zufallsgenerator `random.Random(1000 + seed)`; Index 0 (Depot) ist 0."""
    rng = random.Random(1000 + seed)
    return (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n))


def make_general_instance(seed: int, n: int = 6, window: float = 30.0, horizon: float = 300.0) -> tuple[Instance, tuple]:
    """Gegenprobe: Zufallsinstanz mit beliebiger Fahrzeit-Matrix (zufällig zwischen 5 und 60, nicht symmetrisch, **Dreiecksungleichung nicht erzwungen**; sie ist in allen Instanzen der Gegenprobe verletzt, siehe `tests/test_claims.py`),
    schmalen Fenstern (Mitte zufällig zwischen 20 und 200, jedes Fenster genau `window` breit, nicht beschnitten), Bedienzeit 10, Kapazität 70; dazu zufällige Dualpreise zwischen 20 und 70.
    Rückgabe: (Instanz, Dualpreise). Die Demo benutzt sie nur für die Gegenprobe in Experiment 3."""
    rng = random.Random(seed)
    points = tuple((rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n + 1))   # nur zur Anzeige; die Fahrzeiten sind unabhängig davon
    d = tuple(tuple(0.0 if i == j else rng.uniform(5, 60) for j in range(n + 1)) for i in range(n + 1))
    demand = (0,) + tuple(rng.randint(5, 25) for _ in range(n))
    ready, due = [0.0] * (n + 1), [horizon] * (n + 1)
    for i in range(1, n + 1):
        center = rng.uniform(20, 200)
        ready[i], due[i] = max(0.0, center - window / 2), center + window / 2
    pi = (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n))
    return Instance(n, points, d, demand, tuple(ready), tuple(due), 10.0, horizon, 70), pi


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

HAND_POINTS = ((5, 5), (7, 3), (1, 9), (1, 10), (6, 7), (5, 10), (1, 7))   # Depot, dann Kunde 1 bis 6
HAND_DEMAND = (0, 2, 3, 3, 6, 2, 2)
HAND_READY = (0, 6, 8, 9, 17, 16, 10)
HAND_DUE = (36, 16, 16, 18, 27, 26, 20)
HAND_DUALS = (0, 8, 12, 12, 9, 9, 7)
HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY = 2, 36, 12


def hand_instance() -> Instance:
    """Das Handbeispiel: Manhattan-Abstand auf einem Gitter, alle Zahlen ganz (die Zufallsinstanzen rechnen euklidisch)."""
    d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in HAND_POINTS) for a in HAND_POINTS)
    return Instance(6, HAND_POINTS, d, HAND_DEMAND, HAND_READY, HAND_DUE, HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY)
