from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import sys

# --- HACK NA ŚCIEŻKĘ: dodajemy src/ żeby działał import am_nasa ---
ROOT = Path(__file__).resolve().parents[1]   # .../AM-NASA-v6/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Importy z Twojego silnika AM-NASA (już po dodaniu src do sys.path)
from am_nasa.konwersja_wielosystemowa import konwertuj
from am_nasa.am_core import am_from_jd


# Stała korekta epoki AM względem MASTER_AM:
# z walidacji wyszło, że kodowy AM = MASTER_AM - 3.5 d
AM_OFFSET = 3.5


# ---------- MODELE DANYCH ----------

@dataclass
class MasterRow:
    key: str
    label: str
    calendar: Optional[str]
    civil_date: Optional[str]
    TT_time: Optional[str]
    UT_time: Optional[str]
    delta_t_s: Optional[float]
    JD_TT: Optional[float]
    JD_UT: Optional[float]
    AM_day_float: Optional[float]
    AM_full: Optional[str]
    notes: Optional[str]


@dataclass
class RowValidationResult:
    key: str
    label: str

    jd_ut: Optional[float]

    # walidacja JD względem civil_date + UT_time
    jd_from_calendar: Optional[float]
    delta_jd: Optional[float]
    status_jd: str

    # walidacja AM względem JD_UT
    am_from_code: Optional[float]   # już po korekcie AM_OFFSET
    am_expected: Optional[float]
    delta_am: Optional[float]
    status_am: str


# ---------- UTILITIES ----------

def _is_blank(value: Optional[str]) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def _parse_float(value: str | float | None) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_minus(s: str) -> str:
    # zamiana ewentualnego znaku U+2212 na zwykły '-'
    return s.replace("\u2212", "-")


def parse_calendar_date(date_str: str) -> Tuple[int, int, int]:
    """
    Parsuje string w stylu:
      '2025-10-09'
      '-0239-07-01'  (rok ujemny, astronomiczny)
    do (year, month, day).
    """
    if date_str is None:
        raise ValueError("Brak daty (None)")

    s = _normalize_minus(str(date_str).strip())
    if not s:
        raise ValueError("Pusta data")

    # Obsługa roku z minusem: '-0239-07-01'
    if s[0] in "+-":
        sign = -1 if s[0] == "-" else 1
        s_body = s[1:]
    else:
        sign = 1
        s_body = s

    parts = s_body.split("-")
    if len(parts) != 3:
        raise ValueError(f"Niepoprawny format daty: {date_str!r}")

    year = sign * int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    return year, month, day


def parse_ut_time_to_day_fraction(time_str: Optional[str]) -> float:
    """
    Zamienia 'HH:MM:SS.sss' na ułamek dnia (0–1).
    Jeśli brak czasu -> 0.0 (czyli 00:00 UT).
    """
    if _is_blank(time_str):
        return 0.0

    s = str(time_str).strip()
    parts = s.split(":")
    if len(parts) != 3:
        raise ValueError(f"Niepoprawny format czasu UT: {time_str!r}")
    h = int(parts[0])
    m = int(parts[1])
    sec = float(parts[2])
    total_seconds = h * 3600 + m * 60 + sec
    return total_seconds / 86400.0


def classify_delta_days(delta: Optional[float]) -> str:
    """
    Klasyfikacja ΔJD wg konwencji z AMJD_ERRATA_I_KANON:
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


def classify_delta_am(delta: Optional[float]) -> str:
    """
    Klasyfikacja ΔAM-day:
    - OK    |ΔAM| ≤ 1e-6 d (~0.086 s)
    - WARN  1e-6 < |ΔAM| ≤ 1e-3 d (~86 s)
    - FAIL  > 1e-3 d
    """
    if delta is None or math.isnan(delta):
        return "NA"
    ad = abs(delta)
    if ad <= 1e-6:
        return "OK"
    elif ad <= 1e-3:
        return "WARN"
    else:
        return "FAIL"


def parse_am_year_from_full(am_full: str) -> Optional[int]:
    """
    Z AM_full typu '1181 AM, May 28 00:00:00.000' wyciąga rok AM (np. 1181).
    """
    if _is_blank(am_full):
        return None
    s = str(am_full).strip()
    if "AM" not in s:
        return None
    head = s.split("AM", 1)[0].strip()
    head = head.replace(",", "").strip()
    head = _normalize_minus(head)
    try:
        return int(head.split()[0])
    except Exception:
        return None


# ---------- IO: wczytanie CSV ----------

def load_master_csv(path: Path) -> List[MasterRow]:
    rows: List[MasterRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            rows.append(
                MasterRow(
                    key=(raw.get("key") or "").strip(),
                    label=(raw.get("label") or "").strip(),
                    calendar=raw.get("calendar") or None,
                    civil_date=raw.get("civil_date") or None,
                    TT_time=raw.get("TT_time") or None,
                    UT_time=raw.get("UT_time") or None,
                    delta_t_s=_parse_float(
                        raw.get("ΔT_s") or raw.get("dT_s")
                    ),
                    JD_TT=_parse_float(raw.get("JD_TT")),
                    JD_UT=_parse_float(raw.get("JD_UT")),
                    AM_day_float=_parse_float(raw.get("AM_day_float")),
                    AM_full=raw.get("AM_full") or None,
                    notes=raw.get("notes") or None,
                )
            )
    return rows


# ---------- GŁÓWNA LOGIKA WALIDACJI ----------

def validate_row(row: MasterRow) -> RowValidationResult:
    # --- 1) Walidacja JD względem daty kalendarzowej ---
    jd_from_calendar: Optional[float] = None
    delta_jd: Optional[float] = None
    status_jd: str = "NA"

    if row.calendar and not _is_blank(row.civil_date) and row.JD_UT is not None:
        try:
            year, month, day = parse_calendar_date(row.civil_date)
            day_frac = parse_ut_time_to_day_fraction(row.UT_time)

            system = row.calendar.lower().strip()  # 'julian' / 'gregorian'
            payload: Dict[str, object] = {
                "system": system,
                "year": year,
                "month": month,
                "day": day + day_frac,
            }

            conv = konwertuj(payload)
            # zakładamy, że w wyniku jest pole 'JD' (JD_UT zgodnie z kanonem)
            jd_from_calendar = float(conv["JD"])
            delta_jd = jd_from_calendar - row.JD_UT
            status_jd = classify_delta_days(delta_jd)
        except Exception as e:
            status_jd = f"ERROR: {e}"

    # --- 2) Walidacja AM względem JD_UT ---
    am_from_code: Optional[float] = None
    delta_am: Optional[float] = None
    status_am: str = "NA"
    am_expected = row.AM_day_float

    if row.JD_UT is not None and am_expected is not None and not _is_blank(row.AM_full):
        am_year = parse_am_year_from_full(row.AM_full)
        if am_year is not None:
            try:
                raw_am = float(am_from_jd(row.JD_UT, am_year))  # AM z kodu bez korekty
                adjusted_am = raw_am + AM_OFFSET                # dostosowany do MASTER_AM

                am_from_code = adjusted_am
                delta_am = am_from_code - am_expected
                status_am = classify_delta_am(delta_am)
            except Exception as e:
                status_am = f"ERROR: {e}"
        else:
            status_am = "NA (no AM year)"

    return RowValidationResult(
        key=row.key,
        label=row.label,
        jd_ut=row.JD_UT,
        jd_from_calendar=jd_from_calendar,
        delta_jd=delta_jd,
        status_jd=status_jd,
        am_from_code=am_from_code,
        am_expected=am_expected,
        delta_am=delta_am,
        status_am=status_am,
    )


def validate_master(master_path: Path) -> List[RowValidationResult]:
    rows = load_master_csv(master_path)
    results: List[RowValidationResult] = []
    for row in rows:
        results.append(validate_row(row))
    return results


# ---------- OUTPUT / CLI ----------

def print_results(results: List[RowValidationResult]) -> None:
    jd_counts: Dict[str, int] = {}
    am_counts: Dict[str, int] = {}

    for r in results:
        jd_counts[r.status_jd] = jd_counts.get(r.status_jd, 0) + 1
        am_counts[r.status_am] = am_counts.get(r.status_am, 0) + 1

    print("=== AMJD MASTER VALIDATION ===")
    print("JD status counts:", jd_counts)
    print("AM status counts:", am_counts)
    print()

    print(f"{'KEY':<25} {'JD_status':<12} {'ΔJD[d]':>12}   {'AM_status':<12} {'ΔAM[d]':>14}")
    print("-" * 90)
    for r in results:
        dj = f"{r.delta_jd:.6f}" if r.delta_jd is not None else "-"
        da = f"{r.delta_am:.8f}" if r.delta_am is not None else "-"
        print(
            f"{r.key:<25} {r.status_jd:<12} {dj:>12}   {r.status_am:<12} {da:>14}"
        )


def write_results_csv(master_path: Path, results: List[RowValidationResult]) -> Path:
    out_path = master_path.with_name(master_path.stem + "_validated.csv")
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "key",
                "label",
                "JD_UT",
                "JD_from_calendar",
                "delta_JD_days",
                "status_JD",
                "AM_expected",
                "AM_from_code_adjusted",
                "delta_AM_days",
                "status_AM",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.key,
                    r.label,
                    r.jd_ut,
                    r.jd_from_calendar,
                    r.delta_jd,
                    r.status_jd,
                    r.am_expected,
                    r.am_from_code,
                    r.delta_am,
                    r.status_am,
                ]
            )
    return out_path


def main() -> None:
    # root = .../AM-NASA-v6/
    root = ROOT
    master_path = root / "data" / "amjd" / "AMJD_VALIDACJA_MASTER_AM.csv"

    if not master_path.exists():
        raise SystemExit(f"Nie znaleziono pliku: {master_path}")

    results = validate_master(master_path)
    print_results(results)
    out_path = write_results_csv(master_path, results)
    print()
    print(f"Wynik zapisany do: {out_path}")


if __name__ == "__main__":
    main()
