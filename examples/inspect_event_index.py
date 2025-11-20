"""
Przykład użycia danych AMJD_EVENT_INDEX.csv

- wczytuje index eventów
- liczy ile jest jakich typów (kind)
- wypisuje kilka przykładowych eventów o statusie AM == OK
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "amjd"
INDEX_PATH = DATA_DIR / "AMJD_EVENT_INDEX.csv"


def load_event_index():
    if not INDEX_PATH.exists():
        raise SystemExit(f"Brak pliku indexu: {INDEX_PATH}")

    with INDEX_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    rows = load_event_index()
    print(f"[INFO] Załadowano {len(rows)} eventów z AMJD_EVENT_INDEX.csv")

    # Statystyka po 'kind'
    kind_counter = Counter()
    for r in rows:
        kind = (r.get("kind") or "unknown").strip() or "unknown"
        kind_counter[kind] += 1

    print("\n== Liczba eventów wg kind ==")
    for kind, cnt in kind_counter.most_common():
        print(f"  {kind:15s}  {cnt:4d}")

    # Przykładowe eventy z dobrze zwalidowanym AM
    ok_events = [
        r for r in rows
        if (r.get("status_am") or r.get("status_AM") or "").upper() == "OK"
    ]

    print("\n== Przykładowe eventy ze statusem AM=OK ==")
    for r in ok_events[:10]:
        key = r.get("key")
        label = r.get("label")
        civil_date = r.get("civil_date")
        jd_ut = r.get("jd_ut")
        delta_am = r.get("delta_am_days")
        print(f"- {key:25s}  {civil_date:15s}  JD_UT={jd_ut}  ΔAM={delta_am}")

    if not ok_events:
        print("\n[WARN] Brak eventów ze statusem AM=OK – sprawdź pipeline walidacji.")


if __name__ == "__main__":
    main()
