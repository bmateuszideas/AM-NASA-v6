from __future__ import annotations

import math
from typing import Iterable, List

from .am_core import jd_from_am, am_from_jd


def validate_am_jd(am_values: Iterable[float], nasa_jd_values: Iterable[float]) -> dict:
    """Porównuje dane AM ↔ JD z wartościami NASA i zwraca statystyki różnic."""
    am_list: List[float] = list(am_values)
    jd_list: List[float] = list(nasa_jd_values)

    if len(am_list) != len(jd_list):
        raise ValueError("Listy am_values i nasa_jd_values muszą mieć tę samą długość.")

    diffs = []
    for am, jd_nasa in zip(am_list, jd_list):
        jd_am = jd_from_am(am)
        delta = jd_am - jd_nasa
        diffs.append(delta)

    if not diffs:
        return {"count": 0, "mean": 0.0, "max": 0.0, "rms": 0.0, "diffs": []}

    mean_diff = sum(diffs) / len(diffs)
    max_diff = max(abs(d) for d in diffs)
    rms_diff = math.sqrt(sum(d * d for d in diffs) / len(diffs))

    return {
        "count": len(diffs),
        "mean": mean_diff,
        "max": max_diff,
        "rms": rms_diff,
        "diffs": diffs,
    }


def print_validation_summary(result: dict):
    """Wyświetla czytelne podsumowanie walidacji w konsoli."""
    print("=== WALIDACJA JD ↔ AM ===")
    print(f"Liczba porównań: {result['count']}")
    print(f"Średnia różnica [dni]: {result['mean']:.6f}")
    print(f"Maksymalna różnica [dni]: {result['max']:.6f}")
    print(f"RMS różnica [dni]: {result['rms']:.6f}")
    print("Przykładowe różnice:")
    for i, d in enumerate(result["diffs"][:5]):
        print(f"  #{i+1}: {d:+.6f} dni")
