#!/usr/bin/env python3
"""Exact deterministic counterexamples; a math proof-of-limitation, not physical testing."""
from dataclasses import dataclass

@dataclass(frozen=True)
class World:
    sensor: int
    reference: int
    protected: int

    def two_arm(self):
        return self.sensor - self.reference

    def tri_arm(self):
        return (self.sensor - self.reference, self.reference - self.protected)


def main():
    clean_sensor = World(sensor=2, reference=0, protected=0)
    reference_fouled = World(sensor=10, reference=8, protected=0)
    both_reference_and_guard_fouled = World(sensor=10, reference=8, protected=8)
    common_environmental_shift = World(sensor=7, reference=5, protected=5)
    # Two-arm cannot identify a 4x larger sensor fouling signal if reference also fouls.
    assert clean_sensor.two_arm() == reference_fouled.two_arm() == 2
    # Protected third arm distinguishes only when independently clean.
    assert clean_sensor.tri_arm() == (2, 0)
    assert reference_fouled.tri_arm() == (2, 8)
    # An equally fouled third arm recreates the original ambiguity exactly.
    assert both_reference_and_guard_fouled.tri_arm() == clean_sensor.tri_arm()
    # Unknown common environmental shift also cannot be disentangled just by 3 arms.
    assert common_environmental_shift.tri_arm() == clean_sensor.tri_arm()
    print('PASS: analytical identifiability counterexamples — 2 arms insufficient; 3 arms conditional')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
