from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List
import sys

# --- HACK NA ŚCIEŻKĘ: dodajemy src/ żeby działał import am_nasa ---
ROOT = Path(__file__).resolve().parents[1]   # .../AM-NASA-v6/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from am_nasa.konwersja_wielosystemowa import konwertuj


# ===== MODELE / UTIL =====

@dataclass
class VolcanoRaw:
    event_id: str
    name: str
    gvp_volcano_number: Optional[str]
    location: Optional[str]
    vei: Optional[str]
    date_kind: Optional[str]
    year: Optional[int]
    era: Optional[str]
    month: Optional[int]
    day: Optional[int]
    time_utc: Optional[str]
    calendar_used: str
    jd_ut_src: Optional[float]
    jd_min: Optional[float]
    jd_max: Optional[float]
    time_quality: Optional[str]
    notes: Optional[str]
    sources: Optional[str]


def _is_blank(v: Optional[object]) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    return str(v).strip() == ""


def _parse_int(v: Optional[object]) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_float(v: Optional[object]) -> Optional[float]:
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


def astro_year(year: int, era: Optional[str]) -> int:
    """
    Konwersja (year, era) -> rok astronomiczny:
    - BCE/BC -> 1 - year
    - CE/AD/None -> year
    """
    e = (era or "").strip().upper()
    if e in ("BCE", "BC"):
        return 1 - year
    return year


def parse_time_utc_to_day_fraction(time_utc: Optional[str]) -> float:
    """
    'HH:MM[:SS]' -> ułamek dnia. Brak -> 0.0
    """
    if _is_blank(time_utc):
        return 0.0
    s = str(time_utc).strip()
    parts = s.split(":")
    if len(parts) == 2:
        h, m = int(parts[0]), int(parts[1])
        sec = 0.0
    elif len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        sec = float(parts[2])
    else:
        raise ValueError(f"Niepoprawny czas UTC: {time_utc!r}")
    return (h * 3600 + m * 60 + sec) / 86400.0


def classify_delta_jd(delta: Optional[float]) -> str:
    """
    Na wzór kanonu:
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


# ===== JD -> KALENDARZ (do zakresów) =====

def jd_to_gregorian(jd: float):
    j = jd + 0.5
    Z = int(j)
    F = j - Z
    alpha = int((Z - 1867216.25) / 36524.25)
    A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    return year, month, day


def jd_to_julian(jd: float):
    j = jd + 0.5
    Z = int(j)
    F = j - Z
    A = Z
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    if E < 14:
        month = E - 1
    else:
        month = E - 13
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715
    return year, month, day


def split_day(day_float: float):
    d_int = int(day_float)
    frac = day_float - d_int
    total_seconds = frac * 86400.0
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = total_seconds - h * 3600 - m * 60
    s_rounded = int(round(s))
    if s_rounded == 60:
        s_rounded = 0
        m += 1
        if m == 60:
            m = 0
            h += 1
            if h == 24:
                h = 0
                d_int += 1
    return d_int, h, m, s_rounded


def jd_to_calendar(jd: float, system: str):
    """
    JD -> (year_astro, month, day_int, time_utc_str)
    system: 'gregorian' albo 'julian'
    """
    if system == "gregorian":
        y, m, d = jd_to_gregorian(jd)
    else:
        y, m, d = jd_to_julian(jd)
    day_int, h, mm, ss = split_day(d)
    time_str = f"{h:02d}:{mm:02d}:{ss:02d}"
    return int(y), int(m), day_int, time_str


# ===== IO =====

def load_volcano_raw(path: Path) -> List[VolcanoRaw]:
    if not path.exists():
        raise SystemExit(f"Nie znaleziono pliku VOLCANO_RAW: {path}")

    rows: List[VolcanoRaw] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []

        expected = [
            "event_id",
            "name",
            "gvp_volcano_number",
            "location",
            "vei",
            "date_kind",
            "year",
            "era",
            "month",
            "day",
            "time_utc",
            "calendar_used",
            "jd_ut",
            "jd_min",
            "jd_max",
            "time_quality",
            "notes",
            "sources",
        ]
        missing = [c for c in expected if c not in fields]
        if missing:
            raise SystemExit(
                f"W {path} brakuje oczekiwanych kolumn: {missing}. "
                f"Znaleziono: {fields}"
            )

        for raw in reader:
            rows.append(
                VolcanoRaw(
                    event_id=(raw["event_id"] or "").strip(),
                    name=(raw.get("name") or "").strip(),
                    gvp_volcano_number=raw.get("gvp_volcano_number"),
                    location=raw.get("location"),
                    vei=raw.get("vei"),
                    date_kind=raw.get("date_kind"),
                    year=_parse_int(raw.get("year")),
                    era=(raw.get("era") or "").strip() or None,
                    month=_parse_int(raw.get("month")),
                    day=_parse_int(raw.get("day")),
                    time_utc=raw.get("time_utc"),
                    calendar_used=(raw.get("calendar_used") or "").strip(),
                    jd_ut_src=_parse_float(raw.get("jd_ut")),
                    jd_min=_parse_float(raw.get("jd_min")),
                    jd_max=_parse_float(raw.get("jd_max")),
                    time_quality=raw.get("time_quality"),
                    notes=raw.get("notes"),
                    sources=raw.get("sources"),
                )
            )
    return rows


# ===== GŁÓWNA LOGIKA =====

def process_volcano_rows(rows: List[VolcanoRaw]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []

    for r in rows:
        cal_raw = (r.calendar_used or "").strip().lower()
        if "julian" in cal_raw:
            system = "julian"
        elif "gregorian" in cal_raw:
            system = "gregorian"
        else:
            system = None

        year_astro: Optional[int] = None
        civil_date_astro: Optional[str] = None
        approx_date = False
        jd_calc: Optional[float] = None
        jd_final: Optional[float] = None
        delta_jd: Optional[float] = None
        status = "NA"
        error: Optional[str] = None
        time_mid_utc: Optional[str] = None
        date_mode: str = "none"  # 'exact' / 'range_midpoint' / 'none'

        # --- CASE 1: normalna data (year znany) ---
        if r.year is not None:
            year_astro = astro_year(r.year, r.era)
            month = r.month if r.month is not None else 1
            day = r.day if r.day is not None else 1
            approx_date = (r.month is None) or (r.day is None)
            civil_date_astro = f"{year_astro:+05d}-{month:02d}-{day:02d}"
            date_mode = "exact" if not approx_date else "exact_approx"

            if system is not None:
                try:
                    day_frac = parse_time_utc_to_day_fraction(r.time_utc)
                    payload = {
                        "system": system,
                        "year": year_astro,
                        "month": month,
                        "day": day + day_frac,
                    }
                    conv = konwertuj(payload)
                    jd_calc = float(conv["JD"])
                    if r.jd_ut_src is not None:
                        delta_jd = jd_calc - r.jd_ut_src
                        status = classify_delta_jd(delta_jd)
                    jd_final = r.jd_ut_src if r.jd_ut_src is not None else jd_calc
                except Exception as exc:
                    error = str(exc)
            else:
                error = f"Nieznany calendar_used: {r.calendar_used!r}"

        # --- CASE 2: brak year, ale jest zakres JD (range / year_range) ---
        elif r.jd_min is not None or r.jd_max is not None:
            if r.jd_min is not None and r.jd_max is not None:
                jd_center = 0.5 * (r.jd_min + r.jd_max)
            else:
                jd_center = r.jd_min if r.jd_min is not None else r.jd_max

            if system is not None:
                try:
                    y_c, m_c, d_c, t_c = jd_to_calendar(jd_center, system)
                    year_astro = y_c
                    civil_date_astro = f"{y_c:+05d}-{m_c:02d}-{d_c:02d}"
                    time_mid_utc = t_c
                    approx_date = True
                    date_mode = "range_midpoint"
                    jd_calc = jd_center
                    jd_final = jd_center
                    status = "RANGE"
                except Exception as exc:
                    error = str(exc)
            else:
                error = f"Nieznany calendar_used (range): {r.calendar_used!r}"

        # --- CASE 3: totalny brak info ---
        else:
            error = "Brak year oraz jd_min/jd_max"

        out.append(
            {
                "event_id": r.event_id,
                "name": r.name,
                "gvp_volcano_number": r.gvp_volcano_number,
                "location": r.location,
                "vei": r.vei,
                "date_kind": r.date_kind,
                "time_quality": r.time_quality,
                "year": r.year,
                "era": r.era,
                "year_astro": year_astro,
                "month": r.month,
                "day": r.day,
                "time_utc": r.time_utc,
                "calendar_used": r.calendar_used,
                "system_for_konwersja": system,
                "jd_ut_src": r.jd_ut_src,
                "jd_min": r.jd_min,
                "jd_max": r.jd_max,
                "jd_ut_calc": jd_calc,
                "jd_ut_final": jd_final,
                "delta_jd_calc": delta_jd,
                "delta_status": status,
                "civil_date_astro": civil_date_astro,
                "approx_date": approx_date,
                "date_mode": date_mode,
                "time_mid_utc_from_range": time_mid_utc,
                "notes": r.notes,
                "sources": r.sources,
                "error": error,
                # miejsce na ewentualne AM w kolejnym kroku:
                "AM_day_float": None,
                "AM_full": None,
            }
        )

    return out


def write_volcano_processed(path_in: Path, rows: List[Dict[str, object]]) -> Path:
    out_path = path_in.with_name("AMJD_VOLCANO_PROCESSED.csv")

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
    data_dir = ROOT / "data" / "amjd"
    volcano_raw_path = data_dir / "AMJD_VOLCANO_RAW.csv"

    rows = load_volcano_raw(volcano_raw_path)
    print(f"[INFO] Załadowano {len(rows)} rekordów z {volcano_raw_path}")

    processed = process_volcano_rows(rows)
    out_path = write_volcano_processed(volcano_raw_path, processed)

    errors = [r for r in processed if r.get("error")]
    print(f"[DONE] Zapisano: {out_path}")
    print(f"[INFO] Rekordy z błędami konwersji: {len(errors)}")


if __name__ == "__main__":
    main()
