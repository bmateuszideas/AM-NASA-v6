from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

# Root repo i katalog danych
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "amjd"


def load_csv(path: Path) -> List[Dict[str, Any]]:
    """Bezpieczne wczytanie CSV -> list[dict]. Jak pliku nie ma, zwracamy [] i logujemy."""
    if not path.exists():
        print(f"[WARN] Brak pliku: {path}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def str_or_none(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def bool_from_str(v: Any) -> Optional[bool]:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y", "t"):
        return True
    if s in ("false", "0", "no", "n", "f"):
        return False
    return None


def get_or_create_event(events: Dict[str, Dict[str, Any]], key: str) -> Dict[str, Any]:
    if key not in events:
        events[key] = {
            "key": key,
            "label": None,
            "kind": None,
            "calendar": None,
            "civil_date": None,       # np. -0003-03-13
            "julian_date": None,      # jak ktoś to trzyma osobno
            "jd_ut": None,
            "jd_ut_source": None,     # skąd ten JD (master/gsfc/volcano/etc.)
            "status_jd": None,

            "am_from_code_adjusted": None,
            "delta_am_days": None,
            "status_am": None,

            "volcano_name": None,
            "volcano_vei": None,
            "volcano_date_mode": None,

            "raw_present": False,
            "raw_source_group": None,

            "topo_solar_sites": 0,
            "topo_solar_visible": 0,
            "topo_lunar_sites": 0,
            "topo_lunar_visible": 0,
        }
    return events[key]


def try_set_once(record: Dict[str, Any], field: str, value: Any):
    """Ustawia pole tylko jeśli jest None i value nie jest None."""
    if value is None:
        return
    if record.get(field) is None:
        record[field] = value


# ===================== 1) AMJD_VALIDACJA_MASTER_AM_validated =====================

def integrate_master_validated(events: Dict[str, Dict[str, Any]]):
    path = DATA_DIR / "AMJD_VALIDACJA_MASTER_AM_validated.csv"
    rows = load_csv(path)
    if not rows:
        return

    print(f"[INFO] Integruję MASTER_VALIDATED: {len(rows)} rekordów")

    for row in rows:
        key = str_or_none(row.get("key"))
        if not key:
            continue

        ev = get_or_create_event(events, key)

        label = str_or_none(row.get("label"))
        calendar = str_or_none(row.get("calendar"))
        civil_date = str_or_none(row.get("civil_date"))
        julian_date = str_or_none(row.get("julian_date"))
        jd_ut = str_or_none(row.get("JD_UT"))
        status_jd = str_or_none(row.get("status_JD"))
        am_adj = str_or_none(row.get("AM_from_code_adjusted"))
        delta_am = str_or_none(row.get("delta_AM_days"))
        status_am = str_or_none(row.get("status_AM"))

        try_set_once(ev, "label", label)
        try_set_once(ev, "calendar", calendar)
        try_set_once(ev, "civil_date", civil_date)
        try_set_once(ev, "julian_date", julian_date)

        # JD z walidacji traktujemy jako bardzo dobrego kandydata na canonical
        if jd_ut is not None:
            try_set_once(ev, "jd_ut", jd_ut)
            try_set_once(ev, "jd_ut_source", "master_validated")
        try_set_once(ev, "status_jd", status_jd)

        try_set_once(ev, "am_from_code_adjusted", am_adj)
        try_set_once(ev, "delta_am_days", delta_am)
        try_set_once(ev, "status_am", status_am)


# ===================== 2) AMJD_MASTER_GSFC_BATCH6 =====================

def integrate_master_gsfc(events: Dict[str, Dict[str, Any]]):
    path = DATA_DIR / "AMJD_MASTER_GSFC_BATCH6.csv"
    rows = load_csv(path)
    if not rows:
        return

    print(f"[INFO] Integruję MASTER_GSFC_BATCH6: {len(rows)} rekordów")

    for row in rows:
        # Najczęściej kolumna nazywa się 'key'; jak nie ma, próbujemy 'tag' / 'id'
        key = (
            str_or_none(row.get("key"))
            or str_or_none(row.get("tag"))
            or str_or_none(row.get("id"))
        )
        if not key:
            continue

        ev = get_or_create_event(events, key)

        label = str_or_none(row.get("label"))
        calendar = str_or_none(row.get("calendar"))
        civil_date = str_or_none(row.get("civil_date"))
        julian_date = str_or_none(row.get("julian_date"))
        jd_ut = str_or_none(row.get("JD_UT") or row.get("JD_ut") or row.get("jd_ut"))
        kind = str_or_none(row.get("kind") or row.get("type"))

        try_set_once(ev, "label", label)
        try_set_once(ev, "calendar", calendar)
        try_set_once(ev, "civil_date", civil_date)
        try_set_once(ev, "julian_date", julian_date)
        try_set_once(ev, "kind", kind)

        # Jeśli nie ma jeszcze jd_ut, możemy użyć z GSFC
        if jd_ut is not None and ev.get("jd_ut") is None:
            ev["jd_ut"] = jd_ut
            ev["jd_ut_source"] = "gsfc_master"


# ===================== 3) AMJD_VALIDACJA_GSFC_v1 =====================

def integrate_validacja_gsfc(events: Dict[str, Dict[str, Any]]):
    path = DATA_DIR / "AMJD_VALIDACJA_GSFC_v1.csv"
    rows = load_csv(path)
    if not rows:
        return

    print(f"[INFO] Integruję VALIDACJA_GSFC_v1: {len(rows)} rekordów")

    for row in rows:
        key = (
            str_or_none(row.get("key"))
            or str_or_none(row.get("id"))
        )
        if not key:
            continue

        ev = get_or_create_event(events, key)

        label = str_or_none(row.get("label") or row.get("event"))
        calendar = str_or_none(row.get("calendar"))
        julian_date = str_or_none(row.get("julian_date"))
        jd_ut = str_or_none(row.get("JD_UT") or row.get("JD_ut") or row.get("jd_ut"))

        try_set_once(ev, "label", label)
        try_set_once(ev, "calendar", calendar)
        try_set_once(ev, "julian_date", julian_date)

        if jd_ut is not None and ev.get("jd_ut") is None:
            ev["jd_ut"] = jd_ut
            ev["jd_ut_source"] = "gsfc_validacja"


# ===================== 4) AMJD_VOLCANO_PROCESSED =====================

def integrate_volcano(events: Dict[str, Dict[str, Any]]):
    path = DATA_DIR / "AMJD_VOLCANO_PROCESSED.csv"
    rows = load_csv(path)
    if not rows:
        return

    print(f"[INFO] Integruję VOLCANO_PROCESSED: {len(rows)} rekordów")

    for row in rows:
        key = str_or_none(row.get("event_id"))
        if not key:
            continue

        ev = get_or_create_event(events, key)

        name = str_or_none(row.get("name"))
        vei = str_or_none(row.get("vei"))
        calendar_used = str_or_none(row.get("calendar_used"))
        civil_date_astro = str_or_none(row.get("civil_date_astro"))
        date_mode = str_or_none(row.get("date_mode"))
        jd_final = str_or_none(row.get("jd_ut_final") or row.get("jd_ut_calc"))

        try_set_once(ev, "kind", "volcano")
        try_set_once(ev, "label", name)
        try_set_once(ev, "calendar", calendar_used)
        try_set_once(ev, "civil_date", civil_date_astro)

        try_set_once(ev, "volcano_name", name)
        try_set_once(ev, "volcano_vei", vei)
        try_set_once(ev, "volcano_date_mode", date_mode)

        if jd_final is not None and ev.get("jd_ut") is None:
            ev["jd_ut"] = jd_final
            ev["jd_ut_source"] = "volcano"


# ===================== 5) AMJD_RAW_DATA_MASTERLIKE =====================

def integrate_raw_masterlike(events: Dict[str, Dict[str, Any]]):
    path = DATA_DIR / "AMJD_RAW_DATA_MASTERLIKE.csv"
    rows = load_csv(path)
    if not rows:
        return

    print(f"[INFO] Integruję RAW_DATA_MASTERLIKE: {len(rows)} rekordów")

    for row in rows:
        key = str_or_none(row.get("key"))
        if not key:
            continue

        ev = get_or_create_event(events, key)
        ev["raw_present"] = True

        source_group = str_or_none(row.get("source_group"))
        try_set_once(ev, "raw_source_group", source_group)


# ===================== 6) AMJD_TOPO_VISIBILITY_SOLAR/LUNAR =====================

def integrate_topo_visibility(events: Dict[str, Dict[str, Any]]):
    solar_path = DATA_DIR / "AMJD_TOPO_VISIBILITY_SOLAR.csv"
    lunar_path = DATA_DIR / "AMJD_TOPO_VISIBILITY_LUNAR.csv"

    solar_rows = load_csv(solar_path)
    lunar_rows = load_csv(lunar_path)

    print(f"[INFO] Integruję TOPO_VISIBILITY_SOLAR: {len(solar_rows)} rekordów")
    print(f"[INFO] Integruję TOPO_VISIBILITY_LUNAR: {len(lunar_rows)} rekordów")

    # SOLAR
    for row in solar_rows:
        key = str_or_none(row.get("key"))
        if not key:
            continue
        ev = get_or_create_event(events, key)

        ev["topo_solar_sites"] += 1
        vis = bool_from_str(row.get("visible"))
        if vis is True:
            ev["topo_solar_visible"] += 1

    # LUNAR
    for row in lunar_rows:
        key = str_or_none(row.get("key"))
        if not key:
            continue
        ev = get_or_create_event(events, key)

        ev["topo_lunar_sites"] += 1
        vis = bool_from_str(row.get("visible"))
        if vis is True:
            ev["topo_lunar_visible"] += 1


# ===================== ZAPIS INDEXU =====================

def write_event_index(events: Dict[str, Dict[str, Any]], out_path: Path):
    # zbierz wszystkie pola jakie wystąpiły
    all_fields = set()
    for ev in events.values():
        all_fields.update(ev.keys())
    fieldnames = sorted(all_fields)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(events.keys()):
            writer.writerow(events[key])

    print(f"[OK] Zapisano AMJD_EVENT_INDEX: {out_path} (eventów: {len(events)})")


def main():
    events: Dict[str, Dict[str, Any]] = {}

    integrate_master_validated(events)
    integrate_master_gsfc(events)
    integrate_validacja_gsfc(events)
    integrate_volcano(events)
    integrate_raw_masterlike(events)
    integrate_topo_visibility(events)

    out_path = DATA_DIR / "AMJD_EVENT_INDEX.csv"
    write_event_index(events, out_path)


if __name__ == "__main__":
    main()
