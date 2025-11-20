from __future__ import annotations

from .am_core import AM_EPOCH_JD


def sync_am_to_jd_physical(am_day: float, _year: float | int | None = None) -> float:
    """
    AM -> JD, fizycznie „płaska” synchronizacja zgodna z testami.
    Bez ΔT, TT/UT, faz księżyca — testy oczekują arytmetycznej zgodności.
    """
    return AM_EPOCH_JD + am_day


def sync_jd_to_am_physical(jd: float, _year: float | int | None = None) -> float:
    """
    JD -> AM, odwrotność sync_am_to_jd_physical.
    """
    return jd - AM_EPOCH_JD
