from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List
import sys
import math

# --- HACK NA ŚCIEŻKĘ: dodajemy src/ żeby działał import am_nasa ---
ROOT = Path(__file__).resolve().parents[1]   # .../AM-NASA-v6/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from am_nasa.konwersja_wielosystemowa import konwertuj


# ===== MODELE / UTIL =====

@dataclass
class RawRow:
    key: str
    label: str
    calendar: str
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    ut_time: Optional[str]
    jd_ut_src: Optional[float]
    extra: Dict[str, str]


def _is_blank(v: Optional[str]) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return str(v).strip() == ""


def _parse_int(v: Optional[str]) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_float(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_ut_to_day_fraction(time_str: Optional[str]) -> float:
    """
    'HH:MM:SS' -> ułamek dnia. Brak -> 0.0
    """
    if _is_blank(time_str):
        return 0.0
    s = str(time_str).strip()
    parts = s.split(":")
    if len(parts) != 3:
        raise ValueError(f"Niepoprawny czas UT: {time_str!r}")
    h = int(parts[0])
    m = int(parts[1])
    sec = float(parts[2])
    return (h * 3600 + m * 60 + sec) / 86400.0


def classify_delta_jd(delta: Optional[float]) -> str:
    """
    Klasyfikacja ΔJD w stylu kanonu:
    - OK    |ΔJD| ≤ 0.5 d
    - WARN  0.5 < |ΔJD| ≤ 5 d
    - FAIL  |ΔJD| > 5 d
    """
    if delta is None or math.isnan(delta):
        return "NA"
    ad = abs(delta)
    if ad <= 0.5:
        return "OK"
    elif ad <= 5.0:
        return "WARN"
    else:
        return "FAIL"


# ===== IO =====

def load_raw(path: Path) -> List[RawRow]:
    if not path.exists():
        raise SystemExit(f"Nie znaleziono pliku RAW: {path}")

    rows: List[RawRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        expected = [
            "key",
            "label",
            "calendar",
            "Y",
            "M",
            "D",
            "UT_time",
            "JD_UT",
        ]
        missing = [c for c in expected if c not in fieldnames]
        if missing:
            raise SystemExit(
                f"W {path} brakuje oczekiwanych kolumn: {missing}. "
                f"Znaleziono: {fieldnames}"
            )

        for raw in reader:
            key = (raw.get("key") or "").strip()
            label = (raw.get("label") or "").strip() or key
            calendar = (raw.get("calendar") or "").strip()

            year = _parse_int(raw.get("Y"))
            month = _parse_int(raw.get("M"))
            day = _parse_int(raw.get("D"))
            ut_time = raw.get("UT_time")

            jd_ut_src = _parse_float(raw.get("JD_UT"))

            # zbierz resztę kolumn jako extra
            extra: Dict[str, str] = {}
            for col in fieldnames:
                if col in (
                    "key",
                    "label",
                    "calendar",
                    "Y",
                    "M",
                    "D",
                    "UT_time",
                    "JD_UT",
                ):
                    continue
                extra[col] = raw.get(col, "")

            rows.append(
                RawRow(
                    key=key,
                    label=label,
                    calendar=calendar,
                    year=year,
                    month=month,
                    day=day,
                    ut_time=ut_time,
                    jd_ut_src=jd_ut_src,
                    extra=extra,
                )
            )

    return rows


# ===== GŁÓWNA LOGIKA =====

def process_raw(rows: List[RawRow]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []

    for r in rows:
        system = r.calendar.lower().strip()
        jd_calc = None
        delta = None
        status = "NA"
        error = None

        # jeśli nie ma pełnej daty – nie liczymy JD, tylko flagujemy
        if r.year is None or r.month is None or r.day is None:
            error = "Brak daty (Y/M/D) – nie można policzyć JD"
        else:
            try:
                day_frac = parse_ut_to_day_fraction(r.ut_time)
                payload = {
                    "system": system,
                    "year": r.year,
                    "month": r.month,
                    "day": r.day + day_frac,
                }
                conv = konwertuj(payload)
                jd_calc = float(conv["JD"])
                if r.jd_ut_src is not None:
                    delta = jd_calc - r.jd_ut_src
                    status = classify_delta_jd(delta)
            except Exception as exc:
                error = str(exc)

        row_out: Dict[str, object] = {
            "key": r.key,
            "label": r.label,
            "calendar": r.calendar,
            "Y": r.year,
            "M": r.month,
            "D": r.day,
            "UT_time": r.ut_time,
            "JD_UT_src": r.jd_ut_src,
            "JD_UT_calc": jd_calc,
            "delta_JD_days": delta,
            "status_JD": status,
            "error": error,
        }
        # dołóż wszystkie extra kolumny (DeltaT_s, JD_TT, AM_day_float, itd.)
        row_out.update(r.extra)

        out.append(row_out)

    return out


def write_raw_masterlike(path_in: Path, rows: List[Dict[str, object]]) -> Path:
    out_path = path_in.with_name("AMJD_RAW_DATA_MASTERLIKE.csv")

    # zbieramy kompletną listę kolumn
    all_keys: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in all_keys:
                all_keys.append(k)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return out_path


def main() -> None:
    raw_path = ROOT / "data" / "amjd" / "AMJD_RAW_DATA.csv"
    rows = load_raw(raw_path)
    print(f"[INFO] Załadowano {len(rows)} rekordów z {raw_path}")

    processed = process_raw(rows)
    out_path = write_raw_masterlike(raw_path, processed)

    errors = [r for r in processed if r.get("error")]
    print(f"[DONE] Zapisano: {out_path}")
    print(f"[INFO] Rekordy z błędami konwersji: {len(errors)}")


if __name__ == "__main__":
    main()
