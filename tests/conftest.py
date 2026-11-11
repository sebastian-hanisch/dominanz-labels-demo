"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Die Mini-Instanz ist das Handbeispiel: Depot bei (5, 5) und sechs Kunden auf einem Gitter, Entfernung = Fahrzeit = Manhattan-Abstand, Bedienzeit 2,
Horizont 36, Kapazität 12, Zeitfenster [früh, spät], ganzzahlige Dualpreise. Die Zahlen stehen hier **noch einmal von Hand** (nicht aus dml_scenario),
`test_algorithm.py` vergleicht beide Fassungen. Die Handrechnung steht als Rechnung in den Tests, nicht als abgeschriebenes Ergebnis."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from dml_scenario import Instance  # noqa: E402

# Kunde: (Punkt, Last, früh, spät, Dualpreis); Index 0 ist das Depot
HAND_TABLE = {
    0: ((5, 5), 0, 0, 36, 0),
    1: ((7, 3), 2, 6, 16, 8),
    2: ((1, 9), 3, 8, 16, 12),
    3: ((1, 10), 3, 9, 18, 12),
    4: ((6, 7), 6, 17, 27, 9),
    5: ((5, 10), 2, 16, 26, 9),
    6: ((1, 7), 2, 10, 20, 7),
}
SERVICE, HORIZON, CAPACITY = 2, 36, 12


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@pytest.fixture
def hand():
    """(Instanz, Dualpreise) des Handbeispiels aus der Tabelle oben."""
    pts = tuple(HAND_TABLE[i][0] for i in range(7))
    d = tuple(tuple(manhattan(a, b) for b in pts) for a in pts)
    inst = Instance(6, pts, d, tuple(HAND_TABLE[i][1] for i in range(7)), tuple(HAND_TABLE[i][2] for i in range(7)),
                    tuple(HAND_TABLE[i][3] for i in range(7)), SERVICE, HORIZON, CAPACITY)
    return inst, tuple(HAND_TABLE[i][4] for i in range(7))
