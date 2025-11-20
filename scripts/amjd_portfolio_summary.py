from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import math
import sys

# Root repo
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "amjd"


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


@dataclass
class DatasetSummary:
    dataset: str
    metrics: Dict[str, Any]


# ================= MASTER VALIDATED =================

def summarize_master_validated(path: Path) -> DatasetSummary:
    """
    AMJD_VALIDACJA_MASTER_AM_validated.csv
    Kolumny (wg naszego skryptu):
      key,label,JD_UT,JD_from_calendar,delta_JD_days,status_JD,
      AM_expected,AM_from_code_adjusted,delta_AM_days,status_AM,...
    """
    metrics: Dict[str, Any] = {
        "rows": 0,
        "status_JD": Counter(),
        "status_AM": Counter(),
        "max_abs_delta_JD_days": None,
        "max_abs_delta_AM_days": None,
    }

    if not path.exists():
        metrics["missing"] = True
        return DatasetSummary("AMJD_VALIDACJA_MASTER_AM_validated", metrics)

    max_djd = 0.0
    max_dam = 0.0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics["rows"] += 1
            sj = row.get("status_JD") or "NA"
            sa = row.get("status_AM") or "NA"
            metrics["status_JD"][sj] += 1
            metrics["status_AM"][sa] += 1

            djd = _parse_float(row.get("delta_JD_days"))
            if djd is not None:
                max_djd = max(max_djd, abs(djd))

            dam = _parse_float(row.get("delta_AM_days"))
            if dam is not None:
                max_dam = max(max_dam, abs(dam))

    metrics["max_abs_delta_JD_days"] = max_djd if metrics["rows"] else None
    metrics["max_abs_delta_AM_days"] = max_dam if metrics["rows"] else None

    return DatasetSummary("AMJD_VALIDACJA_MASTER_AM_validated", metrics)


# ================= RAW DATA =================

def summarize_raw_masterlike(path: Path) -> DatasetSummary:
    """
    AMJD_RAW_DATA_MASTERLIKE.csv
    Kolumny (ważne):
      key,label,calendar,Y,M,D,UT_time,
      JD_UT_src,JD_UT_calc,delta_JD_days,status_JD,error,...
    """
    metrics: Dict[str, Any] = {
        "rows": 0,
        "status_JD": Counter(),
        "error_count": 0,
        "max_abs_delta_JD_days": None,
    }

    if not path.exists():
        metrics["missing"] = True
        return DatasetSummary("AMJD_RAW_DATA_MASTERLIKE", metrics)

    max_djd = 0.0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics["rows"] += 1
            sj = row.get("status_JD") or "NA"
            metrics["status_JD"][sj] += 1
            if row.get("error"):
                metrics["error_count"] += 1

            djd = _parse_float(row.get("delta_JD_days"))
            if djd is not None:
                max_djd = max(max_djd, abs(djd))

    metrics["max_abs_delta_JD_days"] = max_djd if metrics["rows"] else None

    return DatasetSummary("AMJD_RAW_DATA_MASTERLIKE", metrics)


# ================= VOLCANO =================

def summarize_volcano(path: Path) -> DatasetSummary:
    """
    AMJD_VOLCANO_PROCESSED.csv
    Z naszego skryptu:
      event_id,name,...,jd_ut_calc,jd_ut_final,delta_jd_calc,delta_status,
      civil_date_astro,approx_date,date_mode,error,...
    """
    metrics: Dict[str, Any] = {
        "rows": 0,
        "delta_status": Counter(),
        "date_mode": Counter(),
        "approx_date_true": 0,
        "error_count": 0,
        "max_abs_delta_JD_days": None,
    }

    if not path.exists():
        metrics["missing"] = True
        return DatasetSummary("AMJD_VOLCANO_PROCESSED", metrics)

    max_djd = 0.0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics["rows"] += 1
            ds = row.get("delta_status") or "NA"
            metrics["delta_status"][ds] += 1

            dm = row.get("date_mode") or "none"
            metrics["date_mode"][dm] += 1

            approx = (row.get("approx_date") or "").strip().lower()
            if approx in ("1", "true", "yes"):
                metrics["approx_date_true"] += 1

            if row.get("error"):
                metrics["error_count"] += 1

            djd = _parse_float(row.get("delta_jd_calc"))
            if djd is not None:
                max_djd = max(max_djd, abs(djd))

    metrics["max_abs_delta_JD_days"] = max_djd if metrics["rows"] else None

    return DatasetSummary("AMJD_VOLCANO_PROCESSED", metrics)


# ================= TOPO VISIBILITY =================

def summarize_topo_visibility(path: Path, label: str) -> DatasetSummary:
    """
    AMJD_TOPO_VISIBILITY_SOLAR/LUNAR.csv
    Kolumny:
      key,label,eclipse_type,JD_UT,site_name,...,visible,classification,error,...
    """
    metrics: Dict[str, Any] = {
        "rows": 0,
        "visible_true": 0,
        "visible_false": 0,
        "classification": Counter(),
        "error_count": 0,
    }

    if not path.exists():
        metrics["missing"] = True
        return DatasetSummary(label, metrics)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics["rows"] += 1
            vis = str(row.get("visible")).strip().lower()
            if vis in ("true", "1", "yes"):
                metrics["visible_true"] += 1
            elif vis in ("false", "0", "no"):
                metrics["visible_false"] += 1

            cls = row.get("classification") or "NA"
            metrics["classification"][cls] += 1

            if row.get("error"):
                metrics["error_count"] += 1

    return DatasetSummary(label, metrics)


# ================= GSFC CSV =================

def summarize_simple_rows(path: Path, label: str) -> DatasetSummary:
    """
    Proste podliczenie wierszy dla plików typu:
      AMJD_MASTER_GSFC_BATCH6.csv
      AMJD_VALIDACJA_GSFC_v1.csv
    """
    metrics: Dict[str, Any] = {
        "rows": 0,
    }

    if not path.exists():
        metrics["missing"] = True
        return DatasetSummary(label, metrics)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for _ in reader:
            metrics["rows"] += 1

    return DatasetSummary(label, metrics)


# ================= ZAPIS PODSUMOWANIA =================

def flatten_summary(ds: DatasetSummary) -> List[Dict[str, Any]]:
    """
    Konwertuje DatasetSummary -> listę wierszy:
      dataset, metric, value
    """
    rows: List[Dict[str, Any]] = []

    def add(prefix: str, value: Any):
        rows.append(
            {
                "dataset": ds.dataset,
                "metric": prefix,
                "value": value,
            }
        )

    for k, v in ds.metrics.items():
        if isinstance(v, Counter):
            for subk, cnt in v.items():
                add(f"{k}.{subk}", cnt)
        else:
            add(k, v)

    return rows


def main() -> None:
    summaries: List[DatasetSummary] = []

    # 1) Walidacja MASTER AM
    summaries.append(
        summarize_master_validated(
            DATA_DIR / "AMJD_VALIDACJA_MASTER_AM_validated.csv"
        )
    )

    # 2) RAW
    summaries.append(
        summarize_raw_masterlike(
            DATA_DIR / "AMJD_RAW_DATA_MASTERLIKE.csv"
        )
    )

    # 3) Volcano
    summaries.append(
        summarize_volcano(
            DATA_DIR / "AMJD_VOLCANO_PROCESSED.csv"
        )
    )

    # 4) Topo visibility
    summaries.append(
        summarize_topo_visibility(
            DATA_DIR / "AMJD_TOPO_VISIBILITY_SOLAR.csv",
            "AMJD_TOPO_VISIBILITY_SOLAR",
        )
    )
    summaries.append(
        summarize_topo_visibility(
            DATA_DIR / "AMJD_TOPO_VISIBILITY_LUNAR.csv",
            "AMJD_TOPO_VISIBILITY_LUNAR",
        )
    )

    # 5) GSFC surowe
    summaries.append(
        summarize_simple_rows(
            DATA_DIR / "AMJD_MASTER_GSFC_BATCH6.csv",
            "AMJD_MASTER_GSFC_BATCH6",
        )
    )
    summaries.append(
        summarize_simple_rows(
            DATA_DIR / "AMJD_VALIDACJA_GSFC_v1.csv",
            "AMJD_VALIDACJA_GSFC_v1",
        )
    )

    # Zapis do CSV
    out_rows: List[Dict[str, Any]] = []
    for ds in summaries:
        out_rows.extend(flatten_summary(ds))

    out_path = DATA_DIR / "AMJD_PORTFOLIO_SUMMARY.csv"
    if out_rows:
        fieldnames = ["dataset", "metric", "value"]
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in out_rows:
                writer.writerow(r)

    # Print ładnego loga
    print("=== AMJD PORTFOLIO SUMMARY ===")
    for ds in summaries:
        print(f"\n[{ds.dataset}]")
        for k, v in ds.metrics.items():
            if isinstance(v, Counter):
                sub = ", ".join(f"{kk}={vv}" for kk, vv in v.items())
                print(f"  {k}: {sub}")
            else:
                print(f"  {k}: {v}")
    print(f"\n[OK] Zapisano zbiorczy plik: {out_path}")


if __name__ == "__main__":
    main()
